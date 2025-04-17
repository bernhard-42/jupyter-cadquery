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

from cad_viewer_widget import (
    AnimationTrack,
    close_sidecar as close_viewer,
    close_sidecars as close_viewers,
    get_sidecar as get_viewer,
    get_sidecars as get_viewers,
    get_default_sidecar as get_default_viewer,
    set_default_sidecar as set_default_viewer,
    get_viewer_by_id,
    get_viewers_by_id,
)

from ocp_vscode.colors import *
from ocp_vscode.config import (
    Camera,
    Collapse,
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

# Inject Collapse enum. Import in cad_viewer_widget would lead to circular import
from cad_viewer_widget.widget import _set_collapse

_set_collapse(
    {"R": Collapse.ROOT, "C": Collapse.ALL, "E": Collapse.NONE, "1": Collapse.LEAVES}
)
del _set_collapse

from ocp_vscode.show import show_all, reset_show, show_clear


from .app import JupyterCadqueryBackend
from .config import get_user_defaults, save_user_defaults
from ._version import __version__
from .tools import auto_show, get_pick
from .show import *

try:
    from ocp_tessellate.tessellator import (
        disable_native_tessellator,
        enable_native_tessellator,
        is_native_tessellator_enabled,
    )

    if os.environ.get("NATIVE_TESSELLATOR") == "0":
        disable_native_tessellator()
    else:
        enable_native_tessellator()

    print(
        "Found and enabled native tessellator.\n"
        "To disable, call `disable_native_tessellator()`\n"
        "To enable, call `enable_native_tessellator()`\n"
    )
except:
    pass

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
