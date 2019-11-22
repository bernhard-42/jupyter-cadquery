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
from .cad_objects import _Assembly, _Part
from OCC.Extend.DataExchange import write_stl_file
from OCC.Core.TopoDS import TopoDS_Compound


def exportSTL(cadObj, filename, linear_deflection=0.01, angular_deflection=0.5):
    compound = None
    if isinstance(cadObj, (_Assembly, _Part)):
        compound = cadObj.compound()
    elif isinstance(cadObj, TopoDS_Compound):
        compound = cadObj
    elif isinstance(cadObj, (cq.Shape, cq.Workplane)):
        compound = Part(cadObj).compound()
    else:
        print("Unsupported CAD object %s, convert to Assembly or Part" % type(cadObj))

    if compound is not None:
        write_stl_file(compound, filename, linear_deflection=linear_deflection, angular_deflection=angular_deflection)
