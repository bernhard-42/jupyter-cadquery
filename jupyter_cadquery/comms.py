"""Communication with the viewer"""

#
# Copyright 2025 Bernhard Walter
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from enum import Enum
import os

import orjson
import requests
from cad_viewer_widget import CadViewer, get_default_sidecar, get_sidecar, show
from cad_viewer_widget.utils import display_args, viewer_args
from ocp_viewer_core.comms import Comms
from ocp_viewer_core.websocket import default as json_default

from .settings import get_user_defaults

__all__ = [
    "JupyterComms",
    "set_jupyter_port",
    "get_jupyter_port",
    "init_session",
    "send_data",
    "send_command",
    "send_backend",
    "send_measure_request",
    "send_config",
]

SESSION = None

# Between the core's Collapse enum, whose values are three-cad-viewer's
# CollapseState numbers, and the widget's trait strings "1"/"R"/"C"/"E".
# Mapped by enum name where possible, so a change of value cannot silently
# reinterpret one.
COLLAPSE_NAMES = {"NONE": "E", "LEAVES": "1", "ALL": "C", "ROOT": "R"}
COLLAPSE_VALUES = {2: "E", -1: "1", 0: "C", 1: "R"}
COLLAPSE_NUMBERS = {letter: number for number, letter in COLLAPSE_VALUES.items()}

# Camera enum values that are position presets, not reset modes
CAMERA_PRESET_VIEWS = ["iso", "top", "bottom", "left", "right", "front", "rear"]

# (connect, read) timeouts for the HTTP requests to the Jupyter server so a
# stuck server extension cannot hang the kernel indefinitely
OBJECTS_TIMEOUT = (5, 120)
MEASURE_TIMEOUT = (5, 60)


def _collapse_to_letter(collapse):
    """Translate a Collapse enum or CollapseState number to the widget letter"""
    if isinstance(collapse, Enum):
        return COLLAPSE_NAMES[collapse.name]
    if isinstance(collapse, int):
        return COLLAPSE_VALUES[collapse]
    return collapse  # already one of the "1"/"R"/"C"/"E" strings

def init_session(url):
    global SESSION
    session = requests.Session()
    session.get(url, timeout=(5, 30))
    SESSION = session


def send_data(data, port=None, timeit=False):
    """
    Send data to the viewer

    Called through `JupyterComms.send_data` to build the sidecar and draw.
    """

    config = data["config"]
    type_ = data["type"]
    if type_ != "data":
        raise TypeError(f"Wrong data type {type_}")
    # count = data["count"]
    data = data["data"]

    if config.get("collapse") is not None:
        config["collapse"] = _collapse_to_letter(config["collapse"])

    preset_view = None
    if config.get("reset_camera") is not None:
        if isinstance(config["reset_camera"], Enum):
            config["reset_camera"] = config["reset_camera"].value
        if config["reset_camera"] in CAMERA_PRESET_VIEWS:
            # Camera position presets (Camera.ISO, Camera.TOP, ...) are not
            # reset modes of the widget; render with "reset" and apply the
            # preset view afterwards, as the other clients' viewers do
            preset_view = config["reset_camera"]
            config["reset_camera"] = "reset"

    all_args = viewer_args(config)
    all_args.update(display_args(config))
    viewer = show(
        data,
        title=config.get("viewer"),
        anchor=config.get("anchor"),
        **all_args,
    )
    viewer.widget.measure_callback = send_measure_request
    if preset_view is not None:
        viewer.set_camera(preset_view)
    if config.get("analysis_tool") in ("distance", "properties", "select"):
        # activate the analysis tool after rendering, as the others do
        viewer.execute("viewer.display.setTool", [config["analysis_tool"], True])
    return viewer


def send_command(data, port=None, title=None, timeit=False):
    """
    Send command to the viewer.

    `"config"` answers `Config.workspace_config`, `"status"` answers
    `Config.status`, and a screenshot command answers `save_screenshot`.
    """
    if isinstance(data, dict):
        if data.get("type") == "screenshot":
            viewer = get_sidecar(title)
            if viewer is None:
                print("No viewer found to take a screenshot from")
            else:
                viewer.export_png(data["filename"])
            return {}

        print(f"Ignoring unsupported viewer command {data.get('type')}")
        return {}

    if data == "config":
        config = get_user_defaults()
        viewer = None
        if title is None:
            title = get_default_sidecar()
            if title is not None:
                viewer = get_sidecar(title)
        else:
            viewer = get_sidecar(title)

        if viewer is not None:
            config["_splash"] = viewer._splash
        return config

    elif data == "status":
        viewer = get_sidecar(title)
        if viewer is None:
            return {}
        status = viewer.status()
        # The core's Collapse is a CollapseState number, not a widget letter
        if status.get("collapse") is not None:
            status["collapse"] = COLLAPSE_NUMBERS[status["collapse"]]
        return status

    else:
        raise ValueError(f"Unknown data for send_command: {data}")


def send_backend(data, port=None, jcv_id=None, timeit=False):
    """
    Send data to the viewer

    Called through `JupyterComms.send_backend` to give the measurement
    backend the model that was just drawn.
    """
    port = os.environ.get("JUPYTER_PORT", "8888")
    url = f"http://localhost:{port}"

    try:
        if SESSION is None:
            init_session(url)

        message = {
            "_xsrf": SESSION.cookies.get("_xsrf"),
            "apikey": os.environ.get("JUPYTER_CADQUERY_API_KEY"),
            "viewer": jcv_id,
            "data": orjson.dumps(data, default=json_default).decode("utf-8"),
        }
        response = SESSION.post(f"{url}/objects", data=message, timeout=OBJECTS_TIMEOUT)
    except requests.exceptions.RequestException as ex:
        print(
            f"Warning: could not send the model to the measurement backend ({ex}); "
            "measurements will not work for this viewer"
        )
        return None
    return response.status_code


def send_measure_request(jcv_id, shape_ids):
    """
    Retrieve the measurement for a given viewer and shape ids from the backend

    Called as callbacks by cad_viewer_widget.widget.CadViewerWidget.active_tool and
    cad_viewer_widget.widget.CadViewerWidget.selected_shape_ids to retrieve measurements
    """
    port = os.environ.get("JUPYTER_PORT", "8888")
    url = f"http://localhost:{port}"

    try:
        if SESSION is None:
            init_session(url)

        message = {
            "_xsrf": SESSION.cookies.get("_xsrf"),
            "apikey": os.environ.get("JUPYTER_CADQUERY_API_KEY"),
            "viewer": jcv_id,
            "data": orjson.dumps(shape_ids).decode("utf-8"),
        }
        response = SESSION.post(f"{url}/measure", data=message, timeout=MEASURE_TIMEOUT)
    except requests.exceptions.RequestException as ex:
        return 500, f"Measurement request failed: {ex}"
    return response.status_code, response.text


def _is_settable(name):
    """Whether a viewer attribute can be changed after the sidecar is open.

    Asked of the property rather than discovered by catching AttributeError,
    so that a genuine failure inside a setter still surfaces.
    """
    attribute = getattr(CadViewer, name, None)
    return not isinstance(attribute, property) or attribute.fset is not None


def send_config(config, port=None, title=None, timeit=False):
    """
    Send config to the viewer

    Called through `JupyterComms.send_config` to set attributes on the widget.
    """
    title = config["config"].get("title")

    if title is None:
        title = get_default_sidecar()
        if title is None:
            return

    cv = get_sidecar(title)
    if cv is None:
        return

    for k, v in config["config"].items():
        if v is not None:
            if not k in ["port", "title"]:
                if not _is_settable(k):
                    # Chosen when the sidecar is opened rather than afterwards:
                    # `up` and `control` have no setter, and a config that
                    # names them - `reset_defaults` re-applies everything the
                    # workspace config holds - would otherwise raise on one the
                    # viewer simply cannot change now.
                    continue
                if k == "collapse":
                    # arrives as CollapseState number from set_viewer_config
                    v = _collapse_to_letter(v)
                elif isinstance(v, Enum):
                    # the websocket path serializes enums to their values,
                    # do the same before setting the widget property
                    v = v.value
                setattr(cv, k, v)


class JupyterComms(Comms):
    """Jupyter CadQuery's transport: a sidecar in the notebook, in this process.

    The host that is least like the others, and the reason the core takes a
    transport rather than a socket. There is no wire: `send_data` builds the
    widget and hands it back, so `show()` returns something the user can go on
    to call methods on. That handle is what `H` is for - `Viewer[CadViewer]`
    gives its users the right type from the same definition that gives the
    other hosts None.

    Which sidecar a call is addressed to arrives in the keywords of the call in
    flight, the way a port does for the hosts that have one.
    """

    def __init__(self):
        super().__init__()
        # The widget the last model went to. The measurement backend is
        # addressed by viewer id, and the id is the handle `send_data` has just
        # produced - so nothing above needs to pass one down.
        self.last_widget = None

    @property
    def title(self):
        """The sidecar this call is addressed to, or None for the default."""
        return self.keywords.get("viewer")

    def encode_config(self, config):
        """No renaming: a traitlet has one name in both languages.

        The widget's Python attribute and its JavaScript trait are the same
        string, so what Python sends is what the JavaScript half reads. The
        rule is unchanged - the sender translates to the receiver's paradigm -
        and here the two paradigms are one.
        """
        return config

    def send_data(self, data, timeit=False):
        viewer = send_data(data, timeit=timeit)
        self.last_widget = viewer
        return viewer

    def send_config(self, config, timeit=False):
        send_config(config, title=self.title, timeit=timeit)

    def send_command(self, data, timeit=False):
        return send_command(data, title=self.title, timeit=timeit)

    def send_backend(self, data, timeit=False):
        jcv_id = None if self.last_widget is None else self.last_widget.widget.id
        send_backend(data, jcv_id=jcv_id, timeit=timeit)

    def send_response(self, data, timeit=False):
        """Nothing to send: this host's backend answers in the same process.

        `ViewerBackend.handle_properties` and `handle_distance` both return
        their response and call this; a host with a socket puts it on the wire,
        and here the caller reads the return value.
        """

    def is_handle(self, obj):
        """Whether `obj` is one of this host's viewers.

        `show_all` walks the user's namespace, and in a notebook that namespace
        contains the sidecar itself - which must not be drawn into itself.
        """
        return isinstance(obj, CadViewer)
