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
from jupyter_cadquery.cad_display import CadqueryDisplay
from jupyter_cadquery.cad_animation import Animation
from jupyter_cadquery.defaults import get_default, get_defaults, split_args, set_defaults
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
        self.cad_display = None
        self.interactive = None
        self.zmq_server = None
        self.root_group = None
        self.log_output = widgets.Output(layout=widgets.Layout(height="400px", overflow="scroll"))
        self.log_output.add_class("mac-scrollbar")

    def _display(self, data, logo=False):
        mesh_data = data["data"]
        config = data["config"]
        info(mesh_data["bb"])

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
        if self.cad_display.splash:
            config["reset_camera"] = True
            self.cad_display.splash = False

        self.cad_display.set_size(config.get("tree_width"), config.get("cad_width"), config.get("height"))
        self.cad_display.init_progress(data.get("count", 1))
        create_args, add_shape_args = split_args(config)
        self.cad_display._update_settings(**create_args)
        self.cad_display.add_shapes(**mesh_data, **add_shape_args)
        info(create_args, add_shape_args)
        self.cad_display.info.ready_msg(self.cad_display.cq_view.grid.step)
        self.root_group = self.cad_display.root_group

    def start_viewer(self, cad_width, cad_height, theme):
        info(f"zmq_port:   {self.zmq_port}")
        info(f"theme:      {theme}")
        info(f"cad_width:  {cad_width}")
        info(f"cad_height: {cad_height}")

        set_defaults(theme=theme, cad_width=cad_width, height=cad_height)

        self.interactive = widgets.Output(layout=widgets.Layout(height="0px"))

        self.cad_display = CadqueryDisplay()
        cad_view = self.cad_display.create()

        # remove jupyter cadquery start message
        clear_output()

        self.log_view = widgets.Accordion(children=[self.log_output])
        self.log_view.set_title(0, "Log")
        self.log_view.selected_index = None
        display(widgets.VBox([cad_view, self.interactive, self.log_view]))

        logo = pickle.loads(base64.b64decode(LOGO_DATA))
        self._display(logo, True)
        self.cad_display.splash = True

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

                self.interactive.outputs = ()
                self.interactive.layout.height = f"0px"

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
                        animation = Animation(self.root_group)
                        for track in data["tracks"]:
                            animation.add_track(*track)
                        widget = animation.animate(data["speed"], data["autoplay"])

                        # With INTERACTIVE: display(widget) does not work, see
                        # https://ipywidgets.readthedocs.io/en/7.6.3/examples/Output%20Widget.html#Interacting-with-output-widgets-from-background-threads
                        #
                        # INTERACTIVE.addpend_display_data(widget) doesn't work either, see https://github.com/jupyter-widgets/ipywidgets/issues/1811
                        # Should be solved, however isn't
                        #
                        mime_data = {
                            "output_type": "display_data",
                            "data": {
                                "text/plain": "AnimationAction",
                                "application/vnd.jupyter.widget-view+json": {
                                    "version_major": 2,
                                    "version_minor": 0,
                                    "model_id": widget.model_id,
                                },
                            },
                            "metadata": {},
                        }
                        self.interactive.outputs = (mime_data,)
                        self.interactive.layout.height = f"40px"
                        return_success(t)

                    except Exception as ex:
                        error_msg = f"{type(ex).__name__}: {ex}"
                        return_error(error_msg)
                else:
                    return_error(f"Wrong message type {data.get('type')}")

        thread = threading.Thread(target=msg_handler)
        thread.setDaemon(True)
        thread.start()
        self.cad_display.info.add_html("<b>zmq server started</b>")

    def stop_viewer(self):
        if self.zmq_server is not None:
            try:
                self.zmq_server.close()
                info("zmq stopped")
                if self.cad_display is not None and self.cad_display.info is not None:
                    self.cad_display.info.add_html("<b>HTTP zmq stopped</b>")
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