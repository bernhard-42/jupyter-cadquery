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

import html

try:
    from cadquery_massembly import MAssembly

    HAS_MASSEMBLY = True
except:
    HAS_MASSEMBLY = False
import numpy as np
from cadquery.occ_impl.shapes import Face, Edge, Wire
from cadquery import Workplane, Shape, Vector, Vertex, Location, Assembly as CqAssembly

from jupyter_cadquery.cad_objects import (
    _PartGroup,
    _Part,
    _Edges,
    _Faces,
    _Vertices,
    _show,
)

from jupyter_cadquery.cad_display import get_default
from .cqparts import is_cqparts, convert_cqparts
from ..utils import Color
from ..ocp_utils import get_rgb


class Part(_Part):
    def __init__(self, shape, name="Part", color=None, show_faces=True, show_edges=True):
        super().__init__(_to_occ(shape), name, color, show_faces, show_edges)

    def to_assembly(self):
        return PartGroup([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class Faces(_Faces):
    def __init__(self, faces, name="Faces", color=None, show_faces=True, show_edges=True):
        super().__init__(_to_occ(faces.combine()), name, color, show_faces, show_edges)

    def to_assembly(self):
        return PartGroup([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class Edges(_Edges):
    def __init__(self, edges, name="Edges", color=None):
        super().__init__(_to_occ(edges), name, color)

    def to_assembly(self):
        return PartGroup([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class Vertices(_Vertices):
    def __init__(self, vertices, name="Vertices", color=None):
        super().__init__(_to_occ(vertices), name, color)

    def to_assembly(self):
        return PartGroup([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class PartGroup(_PartGroup):
    def to_assembly(self):
        return self

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)

    def add(self, cad_obj):
        self.objects.append(cad_obj)

    def add_list(self, cad_objs):
        self.objects += cad_objs


class Assembly(PartGroup):
    def __init__(self, *args, **kwargs):
        import warnings

        super().__init__(*args, **kwargs)
        warnings.warn(
            "Class 'Assembly' is deprecated (too many assemblies ...). Please use class 'PartGroup' instead",
            RuntimeWarning,
        )


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
                cad_obj.parent, obj_id, name="Parent", color=Color((0.8, 0.8, 0.8)), show_parents=False,
            )
        elif isinstance(cad_obj.parent.val(), Vertex):
            return _from_vertexlist(
                cad_obj.parent, obj_id, name="Parent", color=Color((0.8, 0.8, 0.8)), show_parents=False,
            )
        elif isinstance(cad_obj.parent.val(), Edge):
            return _from_edgelist(
                cad_obj.parent, obj_id, name="Parent", color=Color((0.8, 0.8, 0.8)), show_parents=False,
            )
        elif isinstance(cad_obj.parent.val(), Wire):
            return [_from_wirelist(cad_obj.parent, obj_id, name="Parent", color=Color((0.8, 0.8, 0.8)))]
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


def _from_vector(vec, obj_id, name="Vector"):
    tmp = Workplane()
    obj = tmp.newObject([vec])
    return _from_vectorlist(obj, obj_id, name)


def _from_vectorlist(cad_obj, obj_id, name="Vertices", color=None, show_parents=True):
    if cad_obj.vals():
        vectors = cad_obj.vals()
    else:
        vectors = [cad_obj.val()]
    obj = cad_obj.newObject([Vertex.makeVertex(v.x, v.y, v.z) for v in vectors])
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


def to_edge(mate, loc=None, scale=1) -> Workplane:
    w = Workplane()
    for d in (mate.x_dir, mate.y_dir, mate.z_dir):
        edge = Edge.makeLine(mate.origin, mate.origin + d * scale)
        w.objects.append(edge if loc is None else edge.moved(loc))

    return w


def from_assembly(cad_obj, top, loc=None, render_mates=False, mate_scale=1):
    loc = Location()
    render_loc = cad_obj.loc

    color = Color(get_rgb(cad_obj.color))

    parent = [
        Part(Workplane(shape), "%s_%d" % (cad_obj.name, i), color=color,) for i, shape in enumerate(cad_obj.shapes)
    ]

    if render_mates and cad_obj.mates is not None:
        RGB = (Color((255, 0, 0)), Color((0, 128, 0)), Color((0, 0, 255)))
        parent.append(
            PartGroup(
                [
                    Part(to_edge(mate_def.mate, scale=mate_scale), name=name, color=RGB)
                    for name, mate_def in top.mates.items()
                    if mate_def.assembly == cad_obj
                ],
                name="mates",
                loc=Location(),  # mates inherit the parent location, so actually add a no-op
            )
        )

    children = [from_assembly(c, top, loc, render_mates, mate_scale) for c in cad_obj.children]
    return PartGroup(parent + children, cad_obj.name, loc=render_loc)


def _from_workplane(cad_obj, obj_id, name="Part"):
    return Part(cad_obj, "%s_%d" % (name, obj_id))


def _is_facelist(cad_obj):
    return (
        hasattr(cad_obj, "objects")
        and cad_obj.objects != []
        and all([isinstance(obj, Face) for obj in cad_obj.objects])
    )


def _is_vertexlist(cad_obj):
    return (
        hasattr(cad_obj, "objects")
        and cad_obj.objects != []
        and all([isinstance(obj, Vertex) for obj in cad_obj.objects])
    )


def _is_edgelist(cad_obj):
    return (
        hasattr(cad_obj, "objects")
        and cad_obj.objects != []
        and all([isinstance(obj, Edge) for obj in cad_obj.objects])
    )


def _is_wirelist(cad_obj):
    return (
        hasattr(cad_obj, "objects")
        and cad_obj.objects != []
        and all([isinstance(obj, Wire) for obj in cad_obj.objects])
    )


def to_assembly(*cad_objs, render_mates=None, mate_scale=None):
    assembly = PartGroup([], "Group")
    obj_id = 0
    for cad_obj in cad_objs:
        if isinstance(cad_obj, (PartGroup, Part, Faces, Edges, Vertices)):
            assembly.add(cad_obj)

        elif HAS_MASSEMBLY and isinstance(cad_obj, MAssembly):
            assembly.add(from_assembly(cad_obj, cad_obj, render_mates=render_mates, mate_scale=mate_scale))

        elif isinstance(cad_obj, CqAssembly):
            assembly.add(from_assembly(cad_obj, cad_obj))

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

        elif isinstance(cad_obj, Vector):
            assembly.add_list(_from_vector(cad_obj, obj_id))

        elif isinstance(cad_obj.val(), Vector):
            assembly.add_list(_from_vectorlist(cad_obj, obj_id))

        elif isinstance(cad_obj, Workplane):
            assembly.add(_from_workplane(cad_obj, obj_id))

        else:
            raise NotImplementedError("Type:", cad_obj)

        obj_id += 1
    return assembly


def show(*cad_objs, render_mates=None, mate_scale=None, **kwargs):
    """Show CAD objects in Jupyter

    Valid keywords:
    - height:            Height of the CAD view (default=600)
    - tree_width:        Width of navigation tree part of the view (default=250)
    - cad_width:         Width of CAD view part of the view (default=800)
    - bb_factor:         Scale bounding box to ensure compete rendering (default=1.0)
    - render_shapes:     Render shapes  (default=True)
    - render_edges:      Render edges  (default=True)
    - render_mates:      For MAssemblies, whether to rander the mates (default=True)
    - mate_scale:        For MAssemblies, scale of rendered mates (default=1)
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
    render_mates = render_mates or get_default("render_mates")
    mate_scale = mate_scale or get_default("mate_scale")

    assembly = to_assembly(*cad_objs, render_mates=render_mates, mate_scale=mate_scale)

    if assembly is None:
        raise ValueError("%s cannot be viewed" % cad_objs)

    if len(assembly.objects) == 1 and isinstance(assembly.objects[0], PartGroup):
        # omit leading "PartGroup" group
        return _show(assembly.objects[0], **kwargs)
    else:
        return _show(assembly, **kwargs)


def auto_show():
    PartGroup._ipython_display_ = lambda self: self.show()
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


# Some further cq.Assembly methods


def show_constraints(assy, qs):
    colors = [
        "#e41a1c",
        "#377eb8",
        "#4daf4a",
        "#984ea3",
        "#ff7f00",
        "#ffff33",
        "#a65628",
        "#f781bf",
        "#999999",
        "#8dd3c7",
        "#ffffb3",
        "#bebada",
        "#fb8072",
        "#80b1d3",
        "#fdb462",
        "#b3de69",
        "#fccde5",
        "#d9d9d9",
    ]

    constraints = []
    objects = []
    cache = {}

    for i, q1q2 in enumerate(qs):
        parts = []

        kind = q1q2[-1]

        if len(q1q2) == 3:
            q1q2 = ((q1q2[0].split("@")[0], q1q2[0]), (q1q2[1].split("@")[0], q1q2[1]))
        else:
            q1q2 = (q1q2[0:2], q1q2[2:4])

        for q in q1q2:
            name, shape = q
            if name in cache:
                obj = cache[name]["obj"]
                loc = cache[name]["loc"]
            else:
                obj = assy.objects[name].obj
                loc = assy.objects[name].loc

                parent = assy.objects[name].parent
                while parent is not None:
                    loc = parent.loc * loc
                    parent = parent.parent

                cache[name] = {"obj": obj, "loc": loc, "shape": shape}

                objects.append(Part(Workplane(obj.val().located(loc)), name=name, show_faces=False))

            label = str(shape)
            if isinstance(shape, str):
                shape = assy._query(shape)[1]

            parts.append(
                Faces(
                    Workplane(Workplane(shape).val().located(loc)),
                    name=html.escape(label),
                    color=colors[i % len(colors)],
                )
            )
        constraints.append(PartGroup(parts, "%s_%d" % (kind, i)))

    show(PartGroup([PartGroup(objects, "objects")] + constraints), axes=True, axes0=True)


def show_accuracy(assy, cs):
    def relocate(name, shape):
        a = assy.objects[name]
        loc = a.loc

        parent = a.parent
        while parent is not None:
            loc = parent.loc * loc
            parent = parent.parent

        if isinstance(shape, str):
            shape = assy._query(shape)[1]
        return Workplane(Workplane(shape).val().located(loc))

    def center(face):
        c = face.Center()
        return np.array((c.x, c.y, c.z))

    def normal(face):
        n = face.normalAt()
        return np.array((n.x, n.y, n.z))

    def print_metric(results):
        l = max([len(r[1]) for r in results])
        h = ("Constraint", "Normal-Dist", "Normal-Angle", "Point-Dist")
        print(f"{h[0]:{l+7}s} {h[1]:12s}  {h[2]:12s}  {h[3]:12s}")
        print("-" * (l + 46))
        for kind, label, nrm_dist, nrm_angle, pnt_dist in results:
            metric = f"{kind:5s} {label:{l}s} "
            metric += " " * 27 if nrm_dist is None else f"{nrm_dist:12.9f}  {nrm_angle:12.8}°"
            metric += " " * 13 if pnt_dist is None else f"{pnt_dist:12.9f}"
            print(metric)

    results = []
    for q1q2 in cs:
        kind = q1q2[-1]

        if len(q1q2) == 3:
            n_q1q2 = ((q1q2[0].split("@")[0], q1q2[0]), (q1q2[1].split("@")[0], q1q2[1]))
            label = "%s - %s" % q1q2[:2]
        else:
            n_q1q2 = (q1q2[0:2], q1q2[2:4])
            label = "%s<%s> - %s<%s>" % (q1q2[0], q1q2[1].__class__.__name__, q1q2[2], q1q2[3].__class__.__name__)

        shape1 = relocate(*n_q1q2[0])
        shape2 = relocate(*n_q1q2[1])

        pnt_dist = None
        nrm_dist = None
        nrm_angle = None

        if kind in ["Point", "Plane"]:
            c1, c2 = center(shape1.val()), center(shape2.val())
            pnt_dist = np.linalg.norm(c1 - c2)
        if kind in ["Axis", "Plane"]:
            n1, n2 = normal(shape1.val()), normal(shape2.val())
            nrm_dist = np.linalg.norm(n1 + n2)  # distance between n1 and -n2 since n1 and n2 point opposite
            c = np.dot(n1, -n2) / np.linalg.norm(n1) / np.linalg.norm(n2)
            nrm_angle = np.arccos(np.clip(c, -1, 1)) / np.pi * 180

        results.append((kind, label, nrm_dist, nrm_angle, pnt_dist))

    print_metric(results)
