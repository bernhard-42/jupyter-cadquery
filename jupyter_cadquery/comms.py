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


def init_session(url):
    global SESSION
    session = requests.Session()
    session.get(url)
    SESSION = session


def send_data(data, port=None, timeit=False):
    """
    Send data to the viewer

    Called by ocp_vscode.show.show() to send model and config to viewer
    """

    collapse_mapping = ["E", "1", "C", "R"]  # show needs the string

    config = data["config"]
    type_ = data["type"]
    if type_ != "data":
        raise TypeError(f"Wrong data type {type_}")
    # count = data["count"]
    data = data["data"]

    if config.get("collapse") is not None:
        if isinstance(config["collapse"], Enum):
            config["collapse"] = collapse_mapping[config["collapse"].value]
        else:
            config["collapse"] = collapse_mapping[config["collapse"]]

    if config.get("reset_camera") is not None:
        if isinstance(config["reset_camera"], Enum):
            config["reset_camera"] = config["reset_camera"].value

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
    return viewer


def send_command(data, port=None, title=None, timeit=False):
    """
    Send command to the viewer.

    With data == "config" called by called by ocp_vscode.config.workspace_config()
    With data == "status" called by called by ocp_vscode.config.status()
    """
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
        return {} if viewer is None else viewer.status()

    else:
        raise ValueError("Unknown data for send_data")


def send_backend(data, port=None, jcv_id=None, timeit=False):
    """
    Send data to the viewer

    Called by ocp_vscode.show.show() to send model to backend
    """
    port = os.environ.get("JUPYTER_PORT", "8888")
    url = f"http://localhost:{port}"

    if SESSION is None:
        init_session(url)

    message = {
        "_xsrf": SESSION.cookies.get("_xsrf"),
        "apikey": os.environ.get("JUPYTER_CADQUERY_API_KEY"),
        "viewer": jcv_id,
        "data": orjson.dumps(data, default=json_default).decode("utf-8"),
    }
    response = SESSION.post(f"{url}/objects", data=message)
    return response.status_code


def send_measure_request(jcv_id, shape_ids):
    """
    Retrieve the measurement for a given viewer and shape ids from the backend

    Called as callbacks by cad_viewer_widget.widget.CadViewerWidget.active_tool and
    cad_viewer_widget.widget.CadViewerWidget.selected_shape_ids to retrieve measurements
    """
    port = os.environ.get("JUPYTER_PORT", "8888")
    url = f"http://localhost:{port}"

    if SESSION is None:
        init_session(url)

    message = {
        "_xsrf": SESSION.cookies.get("_xsrf"),
        "apikey": os.environ.get("JUPYTER_CADQUERY_API_KEY"),
        "viewer": jcv_id,
        "data": orjson.dumps(shape_ids).decode("utf-8"),
    }
    response = SESSION.post(f"{url}/measure", data=message)
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
                setattr(cv, k, v)
