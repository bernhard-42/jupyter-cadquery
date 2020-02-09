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

from jupyter_cadquery.cad_objects import _Assembly, _Part, _show


class Part(_Part):

    def __init__(self, shape, name="part", color=None, show_faces=True, show_edges=True):
        super().__init__([shape], name, color, show_faces, show_edges)

    def to_assembly(self):
        return Assembly([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class Assembly(_Assembly):

    def to_assembly(self):
        return self

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


def show(cad_obj,**kwargs):
    """Show CAD objects in Jupyter

    Valid keywords:
    - height:        Height of the CAD view (default=600)
    - tree_width:    Width of navigation tree part of the view (default=250)
    - cad_width:     Width of CAD view part of the view (default=800)
    - quality:       Mesh quality for tesselation (default=0.5)
    - edge_accuracy: Presicion of edge discretizaion (default=0.5)
    - axes:          Show axes (default=False)
    - axes0:         Show axes at (0,0,0) (default=False)
    - grid:          Show grid (default=False)
    - ortho:         Use orthographic projections (default=True)
    - transparent:   Show objects transparent (default=False)
    - position:      Relative camera position that will be scaled (default=(1, 1, 1))
    - rotation:      z, y and y rotation angles of position (default=(0, 0, 0))
    - zoom:          Zoom factor of view (default=2.5)
    - mac_scrollbar: Prettify scrollbasrs on Macs (default=True)
    - sidecar:       Use provided sidecar (default=None)
    - timeit:        Show rendering times (default=False)
    """
    assembly = None
    if isinstance(cad_obj, (Assembly, Part)):
        assembly = cad_obj.to_assembly()

    if assembly is None:
        raise ValueError("%s cannot be viewed" % type(cad_obj))
    return _show(assembly, **kwargs)
