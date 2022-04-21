#
# Copyright 2019 Bernhard Walter
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

import warnings

from cad_viewer_widget import (
    open_viewer as cvw_open_viewer,
    AnimationTrack,
)

from cad_viewer_widget.sidecar import (
    get_sidecar as get_viewer,
    get_sidecars as get_viewers,
    close_sidecar as close_viewer,
    close_sidecars as close_viewers,
    set_default as set_default_viewer,
)

from cad_viewer_widget._version import __version__ as cvw_version
from ._version import __version_info__ as jcq_version_info, __version__ as jcq_version
from .ocp_utils import ocp_version

from .cad_objects import (
    Assembly,
    PartGroup,
    Part,
    Faces,
    Edges,
    Vertices,
    show,
    web_color,
    get_pick,
)

from .defaults import (
    get_default,
    get_defaults,
    set_defaults,
    reset_defaults,
)

from .utils import warn
from .tools import auto_show

def versions():
    print("jupyter_cadquery ", jcq_version)
    print("cad_viewer_widget", cvw_version)
    print("OCP              ", ocp_version())


def open_viewer(viewer=None, default=True, **kwargs):
    cv = cvw_open_viewer(title=viewer, **kwargs)
    set_defaults(reset_camera=True)

    if kwargs.get("cad_width") is not None:
        set_defaults(cad_width=kwargs["cad_width"])
    if kwargs.get("tree_width") is not None:
        set_defaults(tree_width=kwargs["tree_width"])
    if kwargs.get("height") is not None:
        set_defaults(height=kwargs["height"])
    if kwargs.get("theme") is not None:
        set_defaults(theme=kwargs["theme"])

    if default:
        set_default_viewer(viewer)

    show(viewer=viewer, **kwargs)
    return cv


def set_sidecar(title, anchor="right", init=False):
    warn(
        "set_sidecar(title, init=False) is deprecated, please use: open_viewer(title='CadQuery', **kwargs)",
        DeprecationWarning,
        "once",
    )
    if init:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("ignore", DeprecationWarning)
            open_viewer(viewer=title, default=True, anchor=anchor)


def close_sidecar(title):
    warn(
        "close_sidecar(title) is deprecated, please use close_viewer(title)",
        DeprecationWarning,
        "once",
    )

    close_viewer(title)


def close_sidecars():
    warn(
        "close_sidecars() is deprecated, please use close_viewers()",
        DeprecationWarning,
        "once",
    )

    close_viewers()


try:
    from IPython import get_ipython

    shell_name = get_ipython().__class__.__name__
    if shell_name == "ZMQInteractiveShell":
        auto_show()
except Exception as ex:
    ...
