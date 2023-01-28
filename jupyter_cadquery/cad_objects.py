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


from ocp_tessellate.cad_objects import Edges as OCP_Edges
from ocp_tessellate.cad_objects import Faces as OCP_Faces
from ocp_tessellate.cad_objects import Part as OCP_Part
from ocp_tessellate.cad_objects import PartGroup as OCP_PartGroup
from ocp_tessellate.cad_objects import Vertices as OCP_Vertices
from ocp_tessellate.convert import to_assembly
from ocp_tessellate.defaults import preset
from ocp_tessellate.utils import warn
from ocp_tessellate.ocp_utils import is_cadquery

from .base import _show

OBJECTS = {"objs": [], "names": [], "colors": [], "alphas": []}


class Part(OCP_Part):
    def __init__(self, shape, name="Part", color=None, show_faces=True, show_edges=True):
        if is_cadquery(shape):
            super().__init__(
                [o.wrapped for o in shape.objects],
                name=name,
                color=color,
                show_faces=show_faces,
                show_edges=show_edges,
            )
        elif hasattr(shape, "wrapped"):
            super().__init__(
                shape.wrapped,
                name=name,
                color=color,
                show_faces=show_faces,
                show_edges=show_edges,
            )
        else:
            raise TypeError(f"Type {type(shape)} not support by Part")


class Faces(OCP_Faces):
    def __init__(self, faces, name="Faces", color=None, show_faces=True, show_edges=True):
        super().__init__(
            [face.wrapped for face in faces.objects],
            name=name,
            color=color,
            show_faces=show_faces,
            show_edges=show_edges,
        )


class Edges(OCP_Edges):
    def __init__(self, edges, name="Edges", color=None, width=1):
        super().__init__(
            [edge.wrapped for edge in edges.objects],
            name=name,
            color=color,
            width=width,
        )


class Vertices(OCP_Vertices):
    def __init__(self, vertices, name="Vertices", color=None, size=1):
        super().__init__([vertex.wrapped for vertex in vertices.objects], name=name, size=size)


class PartGroup(OCP_PartGroup):
    def __init__(self, objects, name="Group", loc=None):
        if loc is not None:
            loc = loc.wrapped
        super().__init__(objects, name=name, loc=loc)


def show(*cad_objs, names=None, colors=None, alphas=None, **kwargs):
    """Show CAD objects in Jupyter

    Valid keywords:

    DISPLAY OPTIONS
    - viewer:             Name of the sidecar viewer (default=""):
                          "" uses the default sidecar (if exists) and None forces to use notebook cell
    - anchor:             How to open sidecar: "right", "split-right", "split-bottom", ... (default="right")
    - cad_width:          Width of CAD view part of the view (default=800)
    - tree_width:         Width of navigation tree part of the view (default=250)
    - height:             Height of the CAD view (default=600)
    - theme:              Theme "light" or "dark" (default="light")
    - pinning:            Allow replacing the CAD View by a canvas screenshot (default=True in cells, else False)

    TESSELLATION OPTIONS
    - angular_tolerance:  Shapes: Angular deflection in radians for tessellation (default=0.2)
    - deviation:          Shapes: Deviation from linear deflection value (default=0.1)
    - edge_accuracy:      Edges: Precision of edge discretization (default=None, i.e. mesh quality / 100)
    - default_color:      Default face color (default=(232, 176, 36))
    - default_edge_color: Default edge color (default="#707070")
    - optimal_bb:         Use optimal bounding box (default=False)
    - render_normals:     Render vertex normals(default=False)
    - render_edges:       Render edges  (default=True)
    - render_mates:       Render mates (for MAssemblies, default=False)
    - mate_scale:         Scale of rendered mates (for MAssemblies, default=1)

    VIEWER OPTIONS
    - control:            Use trackball controls ('trackball') or orbit controls ('orbit') (default='trackball')
    - up:                 Use z-axis ('Z') or y-axis ('Y') as up direction for the camera (or 'L' for legacy z-axis up mode)
    - axes:               Show axes (default=False)
    - axes0:              Show axes at (0,0,0) (default=False)
    - grid:               Show grid (default=[False, False, False])
    - ticks:              Hint for the number of ticks in both directions (default=10)
    - ortho:              Use orthographic projections (default=True)
    - transparent:        Show objects transparent (default=False)
    - black_edges:        Show edges in black (default=False)
    - position:           Absolute camera position that will be scaled (default=None)
    - quaternion:         Camera rotation as quaternion (x, y, z, w) (default=None)
    - target:             Camera target to look at (default=None)
    - zoom:               Zoom factor of view (default=2.5)
    - reset_camera:       Reset camera position, rotation and zoom to default (default=True)
    - zoom_speed:         Mouse zoom speed (default=1.0)
    - pan_speed:          Mouse pan speed (default=1.0)
    - rotate_speed:       Mouse rotate speed (default=1.0)
    - ambient_intensity   Intensity of ambient light (default=0.75)
    - direct_intensity    Intensity of direct lights (default=0.15)
    - show_parent:        Show the parent for edges, faces and vertices objects
    - show_bbox:          Show bounding box (default=False)
    - collapse:           Collapse CAD tree (1: collapse nodes with single leaf, 2: collapse all nodes)
    - cad_width:          Width of CAD view part of the view (default=800)
    - tree_width:         Width of navigation tree part of the view (default=250)
    - height:             Height of the CAD view (default=600)
    - tools:              Show the viewer tools like the object tree (default=True)
    - glass:              Show the viewer in glass mode, i.e (CAD navigation as transparent overlay (default=False)
    - timeit:             Show rendering times, levels = False, 0,1,2,3,4,5 (default=False)
    - parallel:           (Linux only) Whether to use multiprocessing for parallel tessellation
    - js_debug:           Enable debug output in browser console (default=False)

    NOT SUPPORTED ANY MORE:
    - mac_scrollbar       The default now
    - bb_factor:          Removed
    - display             Use 'viewer="<viewer title>"' (for sidecar display) or 'viewer=None' (for cell display)
    - quality             Use 'deviation'to control smoothness of rendered edges
    """

    render_mates = preset("render_mates", kwargs.get("render_mates"))
    mate_scale = preset("mate_scale", kwargs.get("mate_scale"))
    default_color = preset("default_color", kwargs.get("default_color"))
    show_parent = preset("show_parent", kwargs.get("show_parent"))

    if isinstance(kwargs.get("grid"), bool):
        warn(
            "Using bool for grid is deprecated, please use (xy-grid, xz-grid. yz-grid)",
            DeprecationWarning,
            "once",
        )
        kwargs["grid"] = (kwargs["grid"], False, False)

    if cad_objs:

        assembly = to_assembly(
            *cad_objs,
            names=names,
            colors=colors,
            alphas=alphas,
            render_mates=render_mates,
            mate_scale=mate_scale,
            default_color=default_color,
            show_parent=show_parent,
        )

        if assembly is None:
            raise ValueError("%s cannot be viewed" % cad_objs)

        if len(assembly.objects) == 1 and isinstance(assembly.objects[0], PartGroup):
            # omit leading "PartGroup" group
            return _show(assembly.objects[0], **kwargs)
        else:
            return _show(assembly, **kwargs)

    else:

        return _show(None, **kwargs)


def reset():
    global OBJECTS

    OBJECTS = {"objs": [], "names": [], "colors": [], "alphas": []}


def show_object(obj, name=None, options=None, clear=False, **kwargs):
    global OBJECTS

    if clear:
        reset()

    if options is None:
        color = None
        alpha = 1.0
    else:
        color = options.get("color")
        alpha = options.get("alpha", 1.0)

    OBJECTS["objs"].append(obj)
    OBJECTS["names"].append(name)
    OBJECTS["colors"].append(color)
    OBJECTS["alphas"].append(alpha)

    show(
        *OBJECTS["objs"],
        names=OBJECTS["names"],
        colors=OBJECTS["colors"],
        alphas=OBJECTS["alphas"],
        **kwargs,
    )
