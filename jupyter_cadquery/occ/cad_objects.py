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
    - bb_factor:         Scale bounding box to ensure compete rendering (default=1.5)
    - default_color:     Default mesh color (default=(232, 176, 36))
    - default_edgecolor: Default mesh color (default=(128, 128, 128))
    - render_edges:      Render edges  (default=True)
    - render_normals:    Render normals (default=False)
    - render_mates:      Render mates (for MAssemblies)
    - mate_scale:        Scale of rendered mates (for MAssemblies)
    - quality:           Linear deflection for tessellation (default=None)
                         If None, uses bounding box as in (xlen + ylen + zlen) / 300 * deviation)
    - deviation:         Deviation from default for linear deflection value ((default=0.1)
    - angular_tolerance: Angular deflection in radians for tessellation (default=0.2)
    - edge_accuracy:     Presicion of edge discretizaion (default=None)
                         If None, uses: quality / 100
    - optimal_bb:        Use optimal bounding box (default=False)
    - axes:              Show axes (default=False)
    - axes0:             Show axes at (0,0,0) (default=False)
    - grid:              Show grid (default=False)
    - ticks:             Hint for the number of ticks in both directions (default=10)
    - ortho:             Use orthographic projections (default=True)
    - ambient_intensity  Intensity of ambient ligth (default=1.0)
    - direct_intensity   Intensity of direct lights (default=0.12)
    - transparent:       Show objects transparent (default=False)
    - position:          Relative camera position that will be scaled (default=(1, 1, 1))
    - rotation:          z, y and y rotation angles to apply to position vector (default=(0, 0, 0))
    - zoom:              Zoom factor of view (default=2.5)
    - reset_camera:      Reset camera position, rotation and zoom to default (default=True)
    - mac_scrollbar:     Prettify scrollbars (default=True)
    - display:           Select display: "sidecar", "cell", "html"
    - tools:             Show the viewer tools like the object tree
    - timeit:            Show rendering times, levels = False, 0,1,2,3,4,5 (default=False)

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
