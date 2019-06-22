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
from .cad_objects import Assembly, Part


def exportSTL(cadObj, filename, precision=0.001):
    compound = None
    if isinstance(cadObj, cq.Shape):
        compound = cq.Compound.makeCompound(cadObj.objects)
    elif isinstance(cadObj, cq.Workplane):
        compound = cq.Compound.makeCompound(cadObj.objects)
    elif isinstance(cadObj, Assembly):
        compound = cadObj.compound()
    elif isinstance(cadObj, Part):
        compound = cadObj.compound()
    else:
        print("Unknown CAD object", type(cadObj))

    if compound is not None:
        compound.exportStl(filename, precision=precision)
