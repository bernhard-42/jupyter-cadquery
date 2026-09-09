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
from cad_viewer_widget import (
    AnimationTrack,
    CadViewer,
    get_default_sidecar,
    get_sidecar,
    show,
)
from cad_viewer_widget.utils import display_args, viewer_args
from ocp_viewer_core.codec import default as json_default
from ocp_viewer_core.comms import Comms

from .settings import get_user_defaults

__all__ = [
    "JupyterComms",
    "set_jupyter_port",
    "get_jupyter_port",
    "init_session",
    "send_data",
    "send_command",
    "send_backend",
    "status",
    "workspace_config",
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
        # Passed by name: `viewer_args` and `display_args` both filter it out,
        # and cad-viewer-widget's `show` applies it as the trait with the
        # `keymap` route - without this line, `~/.jcq_config`'s modifier keys
        # reach nothing.
        modifier_keys=config.get("modifier_keys"),
        **all_args,
    )
    viewer.widget.measure_callback = send_measure_request
    if preset_view is not None:
        viewer.set_camera(preset_view)
    return viewer


def send_command(data, port=None, title=None, timeit=False):
    """
    Send a command to the viewer.

    Only things done *to* a viewer arrive here - a screenshot is the one this
    host has. The two questions a show asks are `workspace_config` and `status`
    below: they used to be the strings `"config"` and `"status"` handled in this
    function, which is why it once had three jobs and a `ValueError` for a
    fourth.
    """
    if isinstance(data, dict):
        if data.get("type") == "screenshot":
            viewer = get_sidecar(title)
            if viewer is None:
                print("No viewer found to take a screenshot from")
            else:
                viewer.export_png(data["filename"])
            return {}

        if data.get("type") == "set_relative_time":
            # The core's Animation scrubbing the timeline: three-cad-viewer's
            # own setRelativeTime over the method RPC - the same call the page
            # hosts' `set_relative_time` branch makes.
            viewer = get_sidecar(title)
            if viewer is None:
                print("No viewer found to set the animation time on")
            else:
                viewer.execute("viewer.setRelativeTime", [float(data["value"])])
            return {}

        print(f"Ignoring unsupported viewer command {data.get('type')}")
        return {}

    # Unchanged from when this function also answered "config" and "status":
    # anything else is a command this host does not have, and saying so is the
    # point - a silent empty answer is the failure mode this whole layer is
    # careful about.
    raise ValueError(f"Unknown data for send_command: {data}")


def workspace_config(title=None):
    """
    The settings this host persists, from `~/.jcq_config`.

    Read in process - there is no wire between a notebook's Python and its
    widget - which is the whole of this host's transport for the question.
    `_splash` comes from the sidecar rather than the file: it is not a setting
    but the viewer saying whether what is on screen is still the logo.
    """
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


def status(title=None):
    """
    The viewer's live state, asked of the widget itself.

    An empty dict when the named sidecar does not exist: nothing has been
    changed at a toolbar that is not on screen.
    """
    viewer = get_sidecar(title)
    if viewer is None:
        return {}
    result = viewer.status()
    # The core's Collapse is a CollapseState number, not a widget letter
    if result.get("collapse") is not None:
        result["collapse"] = COLLAPSE_NUMBERS[result["collapse"]]
    return result


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

    Settable means: a `CadViewer` property with a setter. Everything the
    viewer can change is one, so a name that is no attribute at all is not
    settable - it used to answer True for those, and `setattr` planted it on
    the CadViewer as a junk attribute (`reset_camera` on every
    `reset_defaults()`, and `viewer` before the exclusion below).

    Asked of the property rather than discovered by catching AttributeError,
    so that a genuine failure inside a setter still surfaces.
    """
    attribute = getattr(CadViewer, name, None)
    return isinstance(attribute, property) and attribute.fset is not None


def send_config(config, port=None, title=None, timeit=False):
    """
    Send config to the viewer

    Called through `JupyterComms.send_config` to set attributes on the widget.
    """
    # The caller's sidecar, if it named one. This read `config["config"].get(
    # "title")` and so overwrote the argument it had just been passed with a key
    # nothing produces: `set_viewer_config` puts the host keyword in as
    # `viewer`. Configuring a named sidecar therefore configured the default
    # one, and the named one did nothing.
    if title is None:
        title = config["config"].get("viewer")

    if title is None:
        title = get_default_sidecar()
        if title is None:
            return

    cv = get_sidecar(title)
    if cv is None:
        return

    for k, v in config["config"].items():
        if v is not None:
            # `port`, `title` and `viewer` are host keywords consumed above,
            # not viewer attributes - `viewer` names the sidecar being
            # configured. `_is_settable` refuses them too now, but they are
            # excluded by name because skipping them is intent, not a
            # capability the viewer happens to lack.
            if not k in ["port", "title", "viewer"]:
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
        if data.get("type") == "clear":
            # `show_clear()`: empty the scene of the viewer this call is
            # addressed to. A widget has no message channel into the shared
            # page, so this calls three-cad-viewer's own clear() over the
            # method RPC - the same call the page hosts' `clear` branch makes.
            # No viewer, nothing to clear: the page hosts ignore it too.
            viewer = get_sidecar(self.title)
            if viewer is not None:
                viewer.execute("viewer.clear")
            return None
        if data.get("type") == "animation":
            # The core's Animation: the tracks ride the widget's own traits -
            # `add_tracks` syncs them, `animate` sets the speed trait, and the
            # widget's JavaScript plays them through the same shared `animate`
            # the page hosts use. No viewer, nothing to animate.
            viewer = get_sidecar(self.title)
            if viewer is not None:
                viewer.add_tracks([AnimationTrack(*track) for track in data["data"]])
                viewer.animate(data["config"]["speed"])
            return None
        viewer = send_data(data, timeit=timeit)
        self.last_widget = viewer
        return viewer

    def send_config(self, config, timeit=False):
        send_config(config, title=self.title, timeit=timeit)

    def send_command(self, data, timeit=False):
        return send_command(data, title=self.title, timeit=timeit)

    def status(self):
        return status(title=self.title)

    def workspace_config(self):
        return workspace_config(title=self.title)

    def send_backend(self, data, timeit=False):
        jcv_id = None if self.last_widget is None else self.last_widget.widget.id
        send_backend(data, jcv_id=jcv_id, timeit=timeit)

    def is_handle(self, obj):
        """Whether `obj` is one of this host's viewers.

        `show_all` walks the user's namespace, and in a notebook that namespace
        contains the sidecar itself - which must not be drawn into itself.
        """
        return isinstance(obj, CadViewer)
