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

from jupyter_cadquery.cad_objects import _PartGroup, _Part, _show


class Part(_Part):
    def __init__(self, shape, name="part", color=None, show_faces=True, show_edges=True):
        super().__init__([shape], name, color, show_faces, show_edges)

    def to_assembly(self):
        return PartGroup([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class PartGroup(_PartGroup):
    def to_assembly(self):
        return self

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class Assembly(PartGroup):
    def __init__(self, *args, **kwargs):
        import warnings

        super().__init__(*args, **kwargs)
        warnings.warn(
            "Class 'Assembly' is deprecated (too many assemblies ...). Please use class 'PartGroup' instead",
            RuntimeWarning,
        )


def show(cad_obj, **kwargs):
    """Show CAD objects in Jupyter

    Valid keywords:
    - height:            Height of the CAD view (default=600)
    - tree_width:        Width of navigation tree part of the view (default=250)
    - cad_width:         Width of CAD view part of the view (default=800)
    - render_shapes:     Render shapes  (default=True)
    - render_edges:      Render edges  (default=True)
    - quality:           Tolerance for tessellation (default=0.1)
    - angular_tolerance: Angular tolerance for building the mesh for tessellation (default=0.1)
    - edge_accuracy:     Presicion of edge discretizaion (default=0.01)
    - optimal_bb:        Use optimal bounding box (default=True)
    - axes:              Show axes (default=False)
    - axes0:             Show axes at (0,0,0) (default=False)
    - grid:              Show grid (default=False)
    - ortho:             Use orthographic projections (default=True)
    - transparent:       Show objects transparent (default=False)
    - position:          Relative camera position that will be scaled (default=(1, 1, 1))
    - rotation:          z, y and y rotation angles to apply to position vector (default=(0, 0, 0))
    - zoom:              Zoom factor of view (default=2.5)
    - mac_scrollbar:     Prettify scrollbasrs on Macs (default=True)
    - display:           Select display: "sidecar", "cell", "html"
    - tools:             Show the viewer tools like the object tree
    - timeit:            Show rendering times (default=False)

    For example isometric projection can be achieved in two ways:
    - position = (1, 1, 1)
    - position = (0, 0, 1) and rotation = (45, 35.264389682, 0)
    """
    assembly = None
    if isinstance(cad_obj, (PartGroup, Part)):
        assembly = cad_obj.to_assembly()

    if assembly is None:
        raise ValueError("%s cannot be viewed" % type(cad_obj))
    return _show(assembly, **kwargs)
