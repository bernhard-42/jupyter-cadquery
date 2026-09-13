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


import os

os.environ["JUPYTER_CADQUERY"] = "1"

import warnings

from cad_viewer_widget import AnimationTrack as _AnimationTrack
from cad_viewer_widget import (
    close_sidecar as close_viewer,
    close_sidecars as close_viewers,
    get_sidecar as get_viewer,
    get_sidecars as get_viewers,
    get_default_sidecar as get_default_viewer,
    set_default_sidecar as set_default_viewer,
    get_viewer_by_id,
    get_viewers_by_id,
)

from ocp_viewer_core.tessellator import (
    ImageFace,
    disable_native_tessellator,
    enable_native_tessellator,
    init_native_tessellator,
    is_native_tessellator_enabled,
)
from ocp_viewer_core.colors import *
from ocp_viewer_core.selectors import (
    select_edge,
    select_edges,
    select_face,
    select_faces,
    select_vertex,
    select_vertices,
)
from .config import (
    AnalysisTool,
    Camera,
    Collapse,
    Render,
    StudioBackground,
    StudioEnvironment,
    StudioTextureMapping,
    StudioToneMapping,
    UiTab,
    combined_config,
    get_changed_config,
    set_viewer_config,
    get_default,
    get_defaults,
    reset_defaults,
    set_defaults,
    status,
    workspace_config,
)

class AnimationTrack(_AnimationTrack):
    """The pre-5.1 way of animating: a track built by hand and handed to the
    viewer with `cv.add_track(...)`, then `cv.animate(speed)`.

    Deprecated in favour of the `Animation` every viewer shares:

        animation = Animation()
        animation.add_track(path, action, times, values)
        animation.animate(speed)

    It still works - the viewer methods it feeds are the transport the shared
    Animation uses too - and the warning is on construction, because building
    a track by hand is the one step the old way has and the new way has not.
    The transport builds its tracks from cad_viewer_widget's class directly and
    never sees this one.
    """

    _warned = False

    def __init__(self, *args, **kwargs):
        # Once per session, not once per track: an animation is many tracks,
        # and the second warning says nothing the first did not.
        if not AnimationTrack._warned:
            AnimationTrack._warned = True
            warnings.warn(
                "AnimationTrack and cv.add_track(...) are deprecated: use "
                "`animation = Animation(); animation.add_track(path, action, "
                "times, values); animation.animate(speed)` instead - see "
                "https://bernhard-42.github.io/ocp_viewer_docs/animation/",
                DeprecationWarning,
                stacklevel=2,
            )
        super().__init__(*args, **kwargs)


# Inject Collapse enum. Import in cad_viewer_widget would lead to circular import
from cad_viewer_widget.widget import _set_collapse

_set_collapse(
    {"R": Collapse.ROOT, "C": Collapse.ALL, "E": Collapse.NONE, "1": Collapse.LEAVES}
)
del _set_collapse

from .show import show_all, reset_show, show_clear


from .app import JupyterCadqueryBackend
from .settings import get_user_defaults, save_user_defaults
from ._version import __version__
from .tools import auto_show, get_pick
from .show import *

# The public surface, so the star import is chosen rather than accidental -
# `os`, the submodules and IPython's `get_ipython` stay out. The tessellator
# toggles below are deliberately absent: their import is conditional, and a
# name in __all__ that may not exist breaks every star import when it does not.
__all__ = [
    "AnalysisTool",
    "Animation",
    "AnimationTrack",
    "auto_show",
    "BaseColorMap",
    "Camera",
    "close_viewer",
    "close_viewers",
    "Collapse",
    "Color",
    "ColorMap",
    "combined_config",
    "cvw_version",
    "disable_native_tessellator",
    "enable_native_tessellator",
    "get_changed_config",
    "get_colormap",
    "get_default",
    "get_default_viewer",
    "get_defaults",
    "get_last_paths",
    "get_pick",
    "get_user_defaults",
    "get_viewer",
    "get_viewer_by_id",
    "get_viewers",
    "get_viewers_by_id",
    "GoldenRatioColormap",
    "hex_to_rgb",
    "hsv_mapper",
    "ignore_camera_warnings",
    "ImageFace",
    "init_native_tessellator",
    "is_native_tessellator_enabled",
    "JupyterCadqueryBackend",
    "ListedColorMap",
    "matplotlib_mapper",
    "none_filter",
    "occt_version",
    "open_viewer",
    "push_object",
    "random_rgb_mapper",
    "remove_object",
    "Render",
    "reset_defaults",
    "reset_show",
    "export_html",
    "save_screenshot",
    "save_user_defaults",
    "SeededColormap",
    "SegmentedColorMap",
    "select_edge",
    "select_edges",
    "select_face",
    "select_faces",
    "select_vertex",
    "select_vertices",
    "set_colormap",
    "set_default_viewer",
    "set_defaults",
    "set_viewer_config",
    "show",
    "show_all",
    "show_clear",
    "show_object",
    "show_objects",
    "status",
    "StudioBackground",
    "StudioEnvironment",
    "StudioTextureMapping",
    "StudioToneMapping",
    "UiTab",
    "unset_colormap",
    "versions",
    "web_to_rgb",
    "workspace_config",
]

if init_native_tessellator():
    print(
        "Found and enabled native tessellator.\n"
        "To disable, call `disable_native_tessellator()`\n"
        "To enable, call `enable_native_tessellator()`\n"
    )

from cad_viewer_widget._version import __version__ as cvw_version
from ocp_tessellate.ocp_utils import Color, occt_version


def versions():
    # do not add to global namesapce
    from ._version import __version__ as jcq_version
    from ._version import __version_info__ as jcq_version_info

    print()
    print("Versions:")
    print("- jupyter_cadquery ", jcq_version)
    print("- cad_viewer_widget", cvw_version)
    print("- open cascade     ", occt_version())
    print()


def _jupyter_server_extension_points():
    return [{"module": "jupyter_cadquery.app", "app": JupyterCadqueryBackend}]


def _load_jupyter_server_extension(server_app):
    JupyterCadqueryBackend.load_jupyter_server_extension(server_app)


try:
    from IPython import get_ipython

    shell_name = get_ipython().__class__.__name__
    if shell_name == "ZMQInteractiveShell":
        auto_show()
except Exception as ex:
    ...

get_user_defaults()
