"""Configuration of the viewer.

The semantics live in `ocp_viewer_core.config`. What is this host's is the two
lists that tell the core what it can do, and the names bound off the Config
built from them - the same file, the same lists and the same functions as
ocp_vscode's and ocp_viewer's.
"""

#
# Copyright 2026 Bernhard Walter
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

from ocp_viewer_core.comms import Session
from ocp_viewer_core.config import (
    AnalysisTool,
    Camera,
    Collapse,
    Config,
    Render,
    StudioBackground,
    StudioEnvironment,
    StudioTextureMapping,
    StudioToneMapping,
    UiTab,
)

from .comms import JupyterComms

__all__ = [
    "AnalysisTool",
    "Camera",
    "Collapse",
    "Render",
    "StudioBackground",
    "StudioEnvironment",
    "StudioTextureMapping",
    "StudioToneMapping",
    "UiTab",
    "combined_config",
    "get_changed_config",
    "get_default",
    "get_defaults",
    "reset_defaults",
    "set_defaults",
    "set_viewer_config",
    "status",
    "workspace_config",
]

# The one keyword that belongs to another host. A port names a viewer to
# address among several, which is real where viewers are servers and has no
# meaning in a notebook - a sidecar is named, not dialled.
#
# Nothing else is excluded: `cad_width`, `height`, `viewer`, `anchor` and
# `pinning` are all this host's to be told, where a panel or a browser window
# decides its own and refuses them. That the list runs the other way here is
# the clearest case for it being per host at all.
EXCLUDE_KEYS = ("port",)

comms = JupyterComms()
session = Session(comms)
config = Config(session, EXCLUDE_KEYS)

set_defaults = config.set_defaults
set_viewer_config = config.set_viewer_config
check_deprecated = config.check_deprecated
validate_tool_args = config.validate_tool_args


# The small entry points keep the host keywords they have always taken and open
# the core's scope around the call, so the transport knows which sidecar.


def status(viewer=None, debug=False):
    """Get viewer status"""
    session.begin({"viewer": viewer})
    try:
        return config.status(debug=debug)
    finally:
        session.clear()


def workspace_config(viewer=None):
    """Get viewer workspace config"""
    session.begin({"viewer": viewer})
    try:
        return config.workspace_config()
    finally:
        session.clear()


def combined_config(viewer=None):
    """Get combined config from workspace and status"""
    session.begin({"viewer": viewer})
    try:
        return config.combined_config()
    finally:
        session.clear()


def get_changed_config(key=None, viewer=None):
    """Get changed config from workspace and status"""
    session.begin({"viewer": viewer})
    try:
        return config.get_changed_config(key=key)
    finally:
        session.clear()


def get_defaults(viewer=None):
    """Get all defaults"""
    session.begin({"viewer": viewer})
    try:
        return config.get_defaults()
    finally:
        session.clear()


def get_default(key, viewer=None):
    """Get default value for key"""
    session.begin({"viewer": viewer})
    try:
        return config.get_default(key)
    finally:
        session.clear()


def reset_defaults(viewer=None):
    """Reset defaults not given in workspace config"""
    session.begin({"viewer": viewer})
    try:
        return config.reset_defaults()
    finally:
        session.clear()
