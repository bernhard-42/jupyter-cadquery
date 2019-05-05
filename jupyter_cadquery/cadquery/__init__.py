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

from .cad_objects import Assembly, Part, Faces, Edges, Wires, show

print("Overwriting auto display for cadquery Workplane and Shape")

def _cadquery_display_(cad_obj):
    # from IPython.display import display as idisplay
    # idisplay(display(obj))
    return cad_obj


from cadquery import Workplane, Shape
try:
    del Workplane._repr_html_
    del Shape._repr_html_
except:
    pass

Workplane._ipython_display_ = _cadquery_display_
Shape._ipython_display_ = _cadquery_display_
