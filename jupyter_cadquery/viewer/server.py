import base64
import base64
from datetime import datetime
from time import localtime
import os
import pickle
import threading
import time
import zmq

from IPython.display import display, clear_output
import ipywidgets as widgets
from jupyter_cadquery import show
from jupyter_cadquery import AnimationTrack
from jupyter_cadquery.defaults import get_default, create_args, add_shape_args, set_defaults
from jupyter_cadquery.logo import LOGO_DATA
from jupyter_cadquery.utils import px

VIEWER = None


def _log(typ, *msg):
    ts = datetime(*localtime()[:6]).isoformat()
    prefix = f"{ts} ({typ}) "
    if VIEWER is not None:
        if isinstance(msg, (tuple, list)):
            VIEWER.log_output.append_stdout(prefix + " ".join([str(m) for m in msg]) + "\n")
        else:
            VIEWER.log_output.append_stdout(prefix + str(msg) + "\n")
    else:
        print(prefix, *msg)


def info(*msg):
    _log("I", *msg)


def warn(*msg):
    _log("W", *msg)


def error(*msg):
    _log("E", *msg)


def debug(*msg):
    _log("D", *msg)


class Viewer:
    def __init__(self, zmq_port):
        self.zmq_port = zmq_port
        self.viewer = None
        self.interactive = None
        self.zmq_server = None
        self.log_output = widgets.Output(layout=widgets.Layout(height="400px", overflow="scroll"))
        self.splash = None
        self.log_view = None

    def _display(self, data, logo=False):
        mesh_data = data["data"]
        config = data["config"]

        if logo or config.get("cad_width") is None:
            config["cad_width"] = get_default("cad_width")
        else:
            if config.get("cad_width") < 640:
                warn("cad_width has to be >= 640, setting to 640")
                config["cad_width"] = 640

        if logo or config.get("height") is None:
            config["height"] = get_default("height")
        else:
            if config.get("height") < 400:
                warn("height has to be >= 400, setting to 400")
                config["height"] = 400

        if logo or config.get("tree_width") is not None:
            config["tree_width"] = get_default("tree_width")
        else:
            if config.get("tree_width") < 200:
                warn("tree_width has to be >= 200, setting to 200")
                config["tree_width"] = 200

        width = config["cad_width"] + config["tree_width"] + 6

        if self.interactive is not None:
            self.interactive.layout.width = px(width - 30)
        if self.log_output is not None:
            self.log_output.layout.width = px(width - 30)
        self.log_view.layout.width = px(width)

        # Force reset of camera to not inhereit splash settings for first object
        if self.splash:
            config["reset_camera"] = True
            self.splash = False

        kwargs = add_shape_args(config)

        self.viewer.clear_tracks()
        self.viewer.add_shapes(**mesh_data, **kwargs)
        info(create_args(config))
        info(add_shape_args(config))

    def start_viewer(self, cad_width, cad_height, theme):
        info(f"zmq_port:   {self.zmq_port}")
        info(f"theme:      {theme}")
        info(f"cad_width:  {cad_width}")
        info(f"cad_height: {cad_height}")

        set_defaults(theme=theme, cad_width=cad_width, height=cad_height)

        # remove jupyter cadquery start message
        clear_output()

        self.viewer = show(theme=theme, cad_width=cad_width, height=cad_height, pinning=False)
        self.splash = True

        self.log_view = widgets.Accordion(children=[self.log_output])
        self.log_view.set_title(0, "Log")
        self.log_view.selected_index = None
        display(self.log_view)

        stop_viewer()

        context = zmq.Context()
        socket = context.socket(zmq.REP)
        for i in range(5):
            try:
                socket.bind(f"tcp://*:{self.zmq_port}")
                break
            except Exception as ex:
                print(f"{ex}: retrying ... ")
                time.sleep(1)

        self.zmq_server = socket
        info("zmq started\n")

        def return_error(error_msg):
            error(error_msg)
            socket.send_json({"result": "error", "msg": error_msg})

        def return_success(t):
            info(f"duration: {time.time() - t:7.2f}")
            socket.send_json({"result": "success"})

        def msg_handler():
            while True:
                msg = socket.recv()
                try:
                    data = pickle.loads(msg)
                except Exception as ex:
                    return_error(str(ex))
                    continue

                if data.get("type") == "data":
                    try:
                        t = time.time()
                        self._display(data)
                        return_success(t)

                    except Exception as ex:
                        error_msg = f"{type(ex).__name__}: {ex}"
                        return_error(error_msg)

                elif data.get("type") == "animation":
                    try:
                        t = time.time()
                        for track in data["data"]:
                            self.viewer.add_track(AnimationTrack(*track))

                        self.viewer.animate(data["config"]["speed"])
                        return_success(t)

                    except Exception as ex:
                        error_msg = f"{type(ex).__name__}: {ex}"
                        return_error(error_msg)

                else:
                    return_error(f"Wrong message type {data.get('type')}")

        thread = threading.Thread(target=msg_handler)
        thread.setDaemon(True)
        thread.start()

    #        self.viewer.info.add_html("<b>zmq server started</b>")

    def stop_viewer(self):
        if self.zmq_server is not None:
            try:
                self.zmq_server.close()
                info("zmq stopped")
                if self.viewer is not None and self.viewer.info is not None:
                    self.viewer.info.add_html("<b>HTTP zmq stopped</b>")
                self.zmq_server = None
                time.sleep(0.5)
            except Exception as ex:
                error("Exception %s" % ex)


def start_viewer():
    global VIEWER

    zmq_port = 5555 if os.environ.get("ZMQ_PORT") is None else os.environ["ZMQ_PORT"]
    cad_width = get_default("cad_width") if os.environ.get("CAD_WIDTH") is None else int(os.environ["CAD_WIDTH"])
    cad_height = get_default("height") if os.environ.get("CAD_HEIGHT") is None else int(os.environ["CAD_HEIGHT"])
    theme = get_default("theme") if os.environ.get("THEME") is None else os.environ["THEME"]

    VIEWER = Viewer(zmq_port)
    VIEWER.start_viewer(cad_width, cad_height, theme)


def stop_viewer():
    VIEWER.stop_viewer()
