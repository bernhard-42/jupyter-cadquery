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

from ._version import __version_info__, __version__
from .cad_display import (
    set_sidecar,
    get_default,
    get_defaults,
    set_defaults,
    reset_defaults,
)

from .cad_renderer import reset_cache
from .export import exportSTL
from .ocp_utils import tq
from cadquery import Location


def __location__repr__(self):
    t, r = tq(self)
    return f"Location(t={t}, q=({r[0]}, {r[1]}, {r[2]}, {r[3]}))"


Location.__repr__ = __location__repr__  # type: ignore
