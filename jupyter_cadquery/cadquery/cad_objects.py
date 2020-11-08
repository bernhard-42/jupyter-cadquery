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

from cadquery.occ_impl.shapes import Face, Edge, Wire
from cadquery import Workplane, Shape, Vector, Vertex, Location, Assembly as CqAssembly

from jupyter_cadquery.cad_objects import (
    _Assembly,
    _Part,
    _Edges,
    _Faces,
    _Vertices,
    _show,
)

from .cqparts import is_cqparts, convert_cqparts
from ..utils import Color


class Part(_Part):
    def __init__(self, shape, name="Part", color=None, show_faces=True, show_edges=True):
        super().__init__(_to_occ(shape), name, color, show_faces, show_edges)

    def to_assembly(self):
        return Assembly([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class Faces(_Faces):
    def __init__(self, faces, name="Faces", color=None, show_faces=True, show_edges=True):
        super().__init__(_to_occ(faces.combine()), name, color, show_faces, show_edges)

    def to_assembly(self):
        return Assembly([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class Edges(_Edges):
    def __init__(self, edges, name="Edges", color=None):
        super().__init__(_to_occ(edges), name, color)

    def to_assembly(self):
        return Assembly([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class Vertices(_Vertices):
    def __init__(self, vertices, name="Vertices", color=None):
        super().__init__(_to_occ(vertices), name, color)

    def to_assembly(self):
        return Assembly([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class Assembly(_Assembly):
    def to_assembly(self):
        return self

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)

    def add(self, cad_obj):
        self.objects.append(cad_obj)

    def add_list(self, cad_objs):
        self.objects += cad_objs


def _to_occ(cad_obj):
    # special case Wire, must be handled before Workplane
    if _is_wirelist(cad_obj):
        all_edges = []
        for edges in cad_obj.objects:
            all_edges += edges.Edges()
        return [edge.wrapped for edge in all_edges]

    elif isinstance(cad_obj, Workplane):
        return [obj.wrapped for obj in cad_obj.objects]

    elif isinstance(cad_obj, Shape):
        return [cad_obj.wrapped]

    else:
        raise NotImplementedError(type(cad_obj))


def _parent(cad_obj, obj_id):
    if cad_obj.parent is not None:
        if isinstance(cad_obj.parent.val(), Vector):
            return _from_vectorlist(
                cad_obj.parent,
                obj_id,
                name="Parent",
                color=Color((0.8, 0.8, 0.8)),
                show_parents=False,
            )
        elif isinstance(cad_obj.parent.val(), Vertex):
            return _from_vertexlist(
                cad_obj.parent,
                obj_id,
                name="Parent",
                color=Color((0.8, 0.8, 0.8)),
                show_parents=False,
            )
        elif isinstance(cad_obj.parent.val(), Edge):
            return _from_edgelist(
                cad_obj.parent,
                obj_id,
                name="Parent",
                color=Color((0.8, 0.8, 0.8)),
                show_parents=False,
            )
        elif isinstance(cad_obj.parent.val(), Wire):
            return [
                _from_wirelist(cad_obj.parent, obj_id, name="Parent", color=Color((0.8, 0.8, 0.8)))
            ]
        else:
            return [Part(cad_obj.parent, "Parent_%d" % obj_id, show_edges=True, show_faces=False,)]
    else:
        return []


def _from_facelist(cad_obj, obj_id, name="Faces", show_parents=True):
    result = [Faces(cad_obj, "%s_%d" % (name, obj_id), color=Color((0.8, 0.0, 0.8)))]
    if show_parents:
        result = _parent(cad_obj, obj_id) + result
    return result


def _from_edgelist(cad_obj, obj_id, name="Edges", color=None, show_parents=True):
    result = [Edges(cad_obj, "%s_%d" % (name, obj_id), color=Color(color or (1.0, 0.0, 1.0)))]
    if show_parents:
        result = _parent(cad_obj, obj_id) + result
    return result


def _from_vectorlist(cad_obj, obj_id, name="Vertices", color=None, show_parents=True):
    obj = cad_obj.newObject([Vertex.makeVertex(v.x, v.y, v.z) for v in cad_obj.vals()])
    result = [Vertices(obj, "%s_%d" % (name, obj_id), color=Color(color or (1.0, 0.0, 1.0)))]
    if show_parents:
        result = _parent(cad_obj, obj_id) + result
    return result


def _from_vertexlist(cad_obj, obj_id, name="Vertices", color=None, show_parents=True):
    result = [Vertices(cad_obj, "%s_%d" % (name, obj_id), color=Color(color or (1.0, 0.0, 1.0)))]
    if show_parents:
        result = _parent(cad_obj, obj_id) + result
    return result


def _from_wirelist(cad_obj, obj_id, name="Edges", color=None):
    return Edges(cad_obj, "%s_%d" % (name, obj_id), color=Color(color or (1.0, 0.0, 1.0)))


def to_edge(mate, loc=None, scale=4) -> Workplane:
    w = Workplane()
    for d in (mate.x_dir, mate.y_dir, mate.z_dir):
        edge = Edge.makeLine(mate.pnt, mate.pnt + d * scale)
        w.objects.append(edge if loc is None else edge.moved(loc))

    return w


def from_assembly(cad_obj, top, loc=None, render_mates=False):
    loc = Location()
    render_loc = cad_obj.loc

    color = Color(cad_obj.web_color)

    parent = [
        Part(Workplane(shape), "%s_%d" % (cad_obj.name, i), color=color,)
        for i, shape in enumerate(cad_obj.shapes)
    ]

    if render_mates:
        if cad_obj.matelist:
            parent.append(
                Assembly(
                    [
                        Part(
                            to_edge(top.mates[mate]["mate"]),
                            name=mate,
                            color=(Color((255, 0, 0)), Color((0, 128, 0)), Color((0, 0, 255)),),
                        )
                        for mate in cad_obj.matelist
                    ],
                    name="mates",
                    loc=Location(),  # mates inherit the parent location, so actually add a no-op
                )
            )

    children = [from_assembly(c, top, loc, render_mates) for c in cad_obj.children]
    return Assembly(parent + children, cad_obj.name, loc=render_loc)


def _from_workplane(cad_obj, obj_id, name="Part"):
    return Part(cad_obj, "%s_%d" % (name, obj_id))


def _is_facelist(cad_obj):
    return all([isinstance(obj, Face) for obj in cad_obj.objects])


def _is_vertexlist(cad_obj):
    return all([isinstance(obj, Vertex) for obj in cad_obj.objects])


def _is_edgelist(cad_obj):
    return all([isinstance(obj, Edge) for obj in cad_obj.objects])


def _is_wirelist(cad_obj):
    return all([isinstance(obj, Wire) for obj in cad_obj.objects])


def show(*cad_objs, render_mates=False, **kwargs):
    """Show CAD objects in Jupyter

    Valid keywords:
    - height:            Height of the CAD view (default=600)
    - tree_width:        Width of navigation tree part of the view (default=250)
    - cad_width:         Width of CAD view part of the view (default=800)
    - render_shapes:     Render shapes  (default=True)
    - render_edges:      Render edges  (default=True)
    - render_mates:      Render mates in case of an assembly
    - quality:           Tolerance for tessellation (default=0.1)
    - angular_tolerance: Angular tolerance for building the mesh for tessellation (default=0.1)
    - edge_accuracy:     Presicion of edge discretizaion (default=0.01)
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
    assembly = Assembly([], "Assembly")
    obj_id = 0
    for cad_obj in cad_objs:
        if isinstance(cad_obj, (Assembly, Part, Faces, Edges, Vertices)):
            assembly.add(cad_obj)

        elif isinstance(cad_obj, CqAssembly):
            assembly.add(from_assembly(cad_obj, cad_obj, render_mates=render_mates,))

        elif isinstance(cad_obj, Edge):
            assembly.add_list(_from_edgelist(Workplane(cad_obj), obj_id))

        elif isinstance(cad_obj, Face):
            assembly.add_list(_from_facelist(Workplane(cad_obj), obj_id))

        elif isinstance(cad_obj, Wire):
            assembly.add(_from_wirelist(Workplane(cad_obj), obj_id))

        elif isinstance(cad_obj, Vertex):
            assembly.add_list(_from_vertexlist(Workplane(cad_obj), obj_id))

        elif is_cqparts(cad_obj):
            assembly = convert_cqparts(cad_obj)

        elif _is_facelist(cad_obj):
            assembly.add_list(_from_facelist(cad_obj, obj_id))

        elif _is_edgelist(cad_obj):
            assembly.add_list(_from_edgelist(cad_obj, obj_id))

        elif _is_wirelist(cad_obj):
            assembly.add(_from_wirelist(cad_obj, obj_id))

        elif _is_vertexlist(cad_obj):
            assembly.add_list(_from_vertexlist(cad_obj, obj_id))

        elif isinstance(cad_obj.val(), Vector):
            assembly.add_list(_from_vectorlist(cad_obj, obj_id))

        elif isinstance(cad_obj, Workplane):
            assembly.add(_from_workplane(cad_obj, obj_id))

        else:
            raise NotImplementedError("Type:", cad_obj)

        obj_id += 1

    if assembly is None:
        raise ValueError("%s cannot be viewed" % cad_objs)

    if len(assembly.objects) == 1:
        # omit leading "Assembly" group
        return _show(assembly.objects[0], **kwargs)
    else:
        return _show(assembly, **kwargs)


def auto_show():
    Assembly._ipython_display_ = lambda self: self.show()
    Part._ipython_display_ = lambda self: self.show()
    Faces._ipython_display_ = lambda self: self.show(grid=False, axes=False)
    Edges._ipython_display_ = lambda self: self.show(grid=False, axes=False)
    Vertices._ipython_display_ = lambda self: self.show(grid=False, axes=False)

    print("Overwriting auto display for cadquery Workplane and Shape")

    import cadquery as cq

    try:
        del cq.Workplane._repr_html_
        del cq.Shape._repr_html_
    except:
        pass
    cq.Workplane._ipython_display_ = lambda cad_obj: show(cad_obj)
    cq.Shape._ipython_display_ = lambda cad_obj: show(cad_obj)
