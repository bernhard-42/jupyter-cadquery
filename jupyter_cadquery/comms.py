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
from cad_viewer_widget import get_default_sidecar, get_sidecar, show
from cad_viewer_widget.utils import display_args, viewer_args
from ocp_vscode.comms import default as json_default

from .config import get_user_defaults

__all__ = [
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

# Translations between ocp_vscode's Collapse enum (whose values are
# three-cad-viewer CollapseState numbers since ocp_vscode 4) and the
# cad-viewer-widget trait strings "1"/"R"/"C"/"E". Mapped by enum name where
# possible, since the enum values changed between ocp_vscode versions.
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

    Called by ocp_vscode.show.show() to send model and config to viewer
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
            # preset view afterwards, like ocp_vscode's viewer does
            preset_view = config["reset_camera"]
            config["reset_camera"] = "reset"

    if config.get("orbit_control") is not None:
        config["control"] = "orbit" if config["orbit_control"] else "trackball"

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
        # activate the analysis tool after rendering, like ocp_vscode's viewer
        viewer.execute("viewer.display.setTool", [config["analysis_tool"], True])
    return viewer


def send_command(data, port=None, title=None, timeit=False):
    """
    Send command to the viewer.

    With data == "config" called by called by ocp_vscode.config.workspace_config()
    With data == "status" called by called by ocp_vscode.config.status()
    With data == {"type": "screenshot", ...} called by ocp_vscode.show.save_screenshot()
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
        # ocp_vscode expects the CollapseState number, not the widget letter
        if status.get("collapse") is not None:
            status["collapse"] = COLLAPSE_NUMBERS[status["collapse"]]
        return status

    else:
        raise ValueError(f"Unknown data for send_command: {data}")


def send_backend(data, port=None, jcv_id=None, timeit=False):
    """
    Send data to the viewer

    Called by ocp_vscode.show.show() to send model to backend
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


def send_config(config, port=None, title=None, timeit=False):
    """
    Send config to the viewer

    Called by ocp_vscode.config.set_viewer_config() to set attributes in the viewer
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
                if k == "collapse":
                    # arrives as CollapseState number from set_viewer_config
                    v = _collapse_to_letter(v)
                elif isinstance(v, Enum):
                    # the websocket path serializes enums to their values,
                    # do the same before setting the widget property
                    v = v.value
                setattr(cv, k, v)
