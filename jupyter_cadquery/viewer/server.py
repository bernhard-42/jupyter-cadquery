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
from jupyter_cadquery.cad_display import CadqueryDisplay, DISPLAY
from jupyter_cadquery.defaults import split_args
from jupyter_cadquery.logo import LOGO_DATA

CAD_DISPLAY = None
LOG_OUTPUT = None
ZMQ_SERVER = None
ZMQ_PORT = 5555


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
    mesh_data = data["data"]
    config = data["config"]

    CAD_DISPLAY.init_progress(data.get("count", 1))
    create_args, add_shape_args = split_args(config)
    CAD_DISPLAY._update_settings(**create_args)
    CAD_DISPLAY.add_shapes(**mesh_data, **add_shape_args)
    info(create_args, add_shape_args)


def start_viewer():
    global CAD_DISPLAY, LOG_OUTPUT, ZMQ_SERVER, ZMQ_PORT

    CAD_DISPLAY = CadqueryDisplay()
    cad_view = CAD_DISPLAY.create()
    width = CAD_DISPLAY.cad_width + CAD_DISPLAY.tree_width + 6
    LOG_OUTPUT = widgets.Output(layout=widgets.Layout(height="400px", overflow="scroll"))

    clear_output()
    log_view = widgets.Accordion(children=[LOG_OUTPUT], layout=widgets.Layout(width=f"{width}px"))
    log_view.set_title(0, "Log")
    log_view.selected_index = None
    display(widgets.VBox([cad_view, log_view]))

    logo = pickle.loads(base64.b64decode(LOGO_DATA))
    _display(logo)

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

            if data.get("type") == "data":
                try:
                    t = time.time()
                    _display(data)
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
