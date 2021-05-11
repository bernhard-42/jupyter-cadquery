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
from jupyter_cadquery.defaults import split_args
from jupyter_cadquery.logo import LOGO_DATA

CAD_DISPLAY = None
LOG_OUTPUT = None
INTERACTIVE = None
ZMQ_SERVER = None
ZMQ_PORT = 5555
ROOT_GROUP = None


def _log(typ, *msg):
    ts = datetime(*localtime()[:6]).isoformat()
    prefix = f"{ts} ({typ}) "
    if LOG_OUTPUT is not None:
        if isinstance(msg, (tuple, list)):
            LOG_OUTPUT.append_stdout(prefix + " ".join([str(m) for m in msg]) + "\n")
        else:
            LOG_OUTPUT.append_stdout(prefix + str(msg) + "\n")
    else:
        print(prefix, *msg)


def info(*msg):
    _log("I", *msg)


def warn(*msg):
    _log("W", *msg)


def error(*msg):
    _log("E", *msg)


def stop_viewer():
    global ZMQ_SERVER

    if ZMQ_SERVER is not None:
        try:
            ZMQ_SERVER.close()
            info("zmq stopped")
            if CAD_DISPLAY is not None and CAD_DISPLAY.info is not None:
                CAD_DISPLAY.info.add_html("<b>HTTP zmq stopped</b>")
            ZMQ_SERVER = None
            time.sleep(0.5)
        except Exception as ex:
            error("Exception %s" % ex)


def _display(data):
    global ROOT_GROUP

    mesh_data = data["data"]
    config = data["config"]
    info(mesh_data["bb"])

    # Force reset of camera to inhereit splash settings for first object
    if CAD_DISPLAY.splash:
        config["reset_camera"] = True
        CAD_DISPLAY.splash = False

    CAD_DISPLAY.init_progress(data.get("count", 1))
    create_args, add_shape_args = split_args(config)
    CAD_DISPLAY._update_settings(**create_args)
    CAD_DISPLAY.add_shapes(**mesh_data, **add_shape_args)
    info(create_args, add_shape_args)
    CAD_DISPLAY.info.ready_msg(CAD_DISPLAY.cq_view.grid.step)
    ROOT_GROUP = CAD_DISPLAY.root_group


def start_viewer():
    global CAD_DISPLAY, LOG_OUTPUT, ZMQ_SERVER, ZMQ_PORT

    CAD_DISPLAY = CadqueryDisplay()
    cad_view = CAD_DISPLAY.create()
    width = CAD_DISPLAY.cad_width + CAD_DISPLAY.tree_width + 6
    LOG_OUTPUT = widgets.Output(layout=widgets.Layout(height="400px", overflow="scroll"))
    INTERACTIVE = widgets.Output(layout=widgets.Layout(height="100px"))

    clear_output()
    log_view = widgets.Accordion(children=[INTERACTIVE, LOG_OUTPUT], layout=widgets.Layout(width=f"{width}px"))
    log_view.set_title(0, "Interactive")
    log_view.set_title(1, "Log")
    log_view.selected_index = None
    display(widgets.VBox([cad_view, log_view]))

    logo = pickle.loads(base64.b64decode(LOGO_DATA))
    _display(logo)
    CAD_DISPLAY.splash = True

    stop_viewer()

    if os.environ.get("ZMQ_PORT") != None:
        ZMQ_PORT = os.environ.get("ZMQ_PORT")
        info(f"Using port {ZMQ_PORT}")

    for i in range(5):
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REP)
            socket.bind(f"tcp://*:{ZMQ_PORT}")
            break
        except Exception as ex:
            print(f"{ex}: retrying ... ")
            time.sleep(1)

    ZMQ_SERVER = socket
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

            INTERACTIVE.outputs = ()

            if data.get("type") == "data":
                try:
                    t = time.time()
                    _display(data)
                    return_success(t)

                except Exception as ex:
                    error_msg = f"{type(ex).__name__}: {ex}"
                    return_error(error_msg)

            elif data.get("type") == "animation":
                try:
                    t = time.time()
                    animation = Animation(ROOT_GROUP)
                    for track in data["tracks"]:
                        animation.add_track(*track)
                    widget = animation.animate(data["speed"], data["autoplay"])

                    with INTERACTIVE:
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
                        INTERACTIVE.outputs = (mime_data,)

                    return_success(t)

                except Exception as ex:
                    error_msg = f"{type(ex).__name__}: {ex}"
                    return_error(error_msg)
            else:
                return_error(f"Wrong message type {data.get('type')}")

    thread = threading.Thread(target=msg_handler)
    thread.setDaemon(True)
    thread.start()
    CAD_DISPLAY.info.add_html("<b>zmq server started</b>")
