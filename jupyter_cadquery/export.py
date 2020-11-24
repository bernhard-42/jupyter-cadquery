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

import cadquery as cq
from .cad_objects import _PartGroup, _Part
from .ocp_utils import write_stl_file, is_compound


def exportSTL(cadObj, filename, tolerance=1e-3, angular_tolerance=0.1):
    compound = None
    if isinstance(cadObj, (_PartGroup, _Part)):
        compound = cadObj.compound()
    elif is_compound(cadObj):
        compound = cadObj
    elif isinstance(cadObj, (cq.Shape, cq.Workplane)):
        compound = _Part(cadObj).compound()
    else:
        print("Unsupported CAD object %s, convert to PartGroup or Part" % type(cadObj))

    if compound is not None:
        write_stl_file(
            compound,
            filename,
            tolerance=tolerance,
            angular_tolerance=angular_tolerance,
        )
