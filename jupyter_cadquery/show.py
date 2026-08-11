"""The show family, bound to this host's viewer, and opening a sidecar.

The pipeline is `ocp_viewer_core.show.Viewer`; what is here is the one Viewer
this process shows through, the names bound off it, and `open_viewer`, which is
this host's alone - the other clients have a panel or a browser window already
open, and this one makes a sidecar.

`Viewer[CadViewer]` is the handle: `show()` returns the widget it drew into, so
a user can go on to call methods on it. The same definition gives the hosts
with nothing to hand back None.

The same file, the same names and the same reasoning as ocp_vscode's show.py.
"""

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

import orjson
from cad_viewer_widget import CadViewer
from cad_viewer_widget import open_viewer as _open_viewer
from cad_viewer_widget.utils import viewer_args
from ocp_viewer_core.logo import logo as b_logo
from ocp_viewer_core.show import Viewer as CoreViewer
from ocp_viewer_core.show import ignore_camera_warnings, none_filter

from .comms import send_backend, send_measure_request
from .config import config
from .logo import logo

__all__ = [
    "get_colormap",
    "get_last_paths",
    "ignore_camera_warnings",
    "none_filter",
    "open_viewer",
    "push_object",
    "remove_object",
    "reset_show",
    "save_screenshot",
    "set_colormap",
    "show",
    "show_all",
    "show_clear",
    "show_object",
    "show_objects",
    "unset_colormap",
]


def open_viewer(
    title=None,
    anchor="right",
    cad_width=800,
    tree_width=250,
    height=600,
    aspect_ratio=None,
    theme="browser",
    glass=True,
    tools=True,
    pinning=True,
    default=True,
):
    viewer = _open_viewer(
        title=title,
        anchor=anchor,
        cad_width=cad_width,
        tree_width=tree_width,
        aspect_ratio=aspect_ratio,
        height=height,
        theme=theme,
        glass=glass,
        tools=tools,
        pinning=pinning,
        default=default,
    )
    l = orjson.loads(logo)
    l["config"]["collapse"] = "R"
    viewer.add_shapes(l["data"], **viewer_args(l["config"]), _is_logo=True)

    send_backend({"model": b_logo}, jcv_id=viewer.widget.id)
    viewer.widget.measure_callback = send_measure_request

    return viewer


# The widget this host hands back, carried in the type so that a user who does
# `v = show(part)` gets completion on `v`.
viewer = CoreViewer[CadViewer](config)

show = viewer.show
show_object = viewer.show_object
show_objects = viewer.show_objects
show_all = viewer.show_all
show_clear = viewer.show_clear
push_object = viewer.push_object
remove_object = viewer.remove_object
reset_show = viewer.reset_show
save_screenshot = viewer.save_screenshot

get_colormap = viewer.get_colormap
set_colormap = viewer.set_colormap
unset_colormap = viewer.unset_colormap
get_last_paths = viewer.get_last_paths
