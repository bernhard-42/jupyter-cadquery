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
from ..utils import warn

warn(
    "jupyter_cadquery.cadquery is deprecated, please use jupyter_cadquery directly for import "
    + "and jupyter_cadquery.replay for replay functions",
    DeprecationWarning,
    "once",
)

from ..cad_objects import (
    Assembly,
    PartGroup,
    Part,
    Faces,
    Edges,
    Vertices,
    show,
    web_color,
)
from ..tools import auto_show, show_accuracy, show_constraints

from ..replay import replay, enable_replay, disable_replay, reset_replay
