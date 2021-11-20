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
    get_viewer,
    get_viewers,
    set_viewer as _set_viewer,
    close_viewer,
    close_viewers,
    AnimationTrack,
)
from .cadquery.cad_objects import show

from ._version import __version_info__, __version__

from .defaults import (
    get_default,
    get_defaults,
    set_defaults,
    reset_defaults,
)

from .utils import warn


def set_viewer(
    name,
    height=None,
    tree_width=None,
    cad_width=None,
    tools=None,
    anchor="split-right",
    init=False,
):

    if init:
        preset = lambda key, value: get_default(key) if value is None else value
        show(
            sidecar=name,
            anchor=anchor,
            height=preset("height", height),
            tree_width=preset("tree_width", tree_width),
            cad_width=preset("cad_width", cad_width),
            tools=preset("tools", tools),
        )

    _set_viewer(name, anchor=anchor)


def set_sidecar(title, init=False):
    warn(
        "set_sidecar(title, init=False) is deprecated, please use set_viewer(title, init=False)",
        DeprecationWarning,
        "once",
    )
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("ignore", DeprecationWarning)
        set_viewer(title, init=init)


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
