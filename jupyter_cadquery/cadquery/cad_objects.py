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
from cadquery import Workplane, Shape, Vector

from jupyter_cadquery.cad_objects import _Assembly, _Part, _Edges, _Faces, _show


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
    # special cas Wire, must be handled before Workplane
    if _is_wire_list(cad_obj):
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


def _edge_list_to_objs(cad_obj, obj_id):
    if isinstance(cad_obj.parent.val(), Vector):
        return [Edges(cad_obj, "Edges_%d" % obj_id, color=(1, 0, 1))]
    else:
        return [
            Part(cad_obj.parent, "Part_%d" % obj_id, show_edges=True, show_faces=False),
            Edges(cad_obj, "Edges_%d" % obj_id, color=(1, 0, 1))
        ]


def _wire_list_to_obj(cad_obj, obj_id):
    return Edges(cad_obj, "Edges_%d" % obj_id, color=(1, 0, 1))


def _face_list_to_objs(cad_obj, obj_id):
    return [
        Part(cad_obj.parent, "Part_%d" % obj_id, show_edges=True, show_faces=False),
        Faces(cad_obj, "Faces_%d" % obj_id, color=(1, 0, 1))
    ]


def _workplane_to_obj(cad_obj, obj_id):
    return Part(cad_obj, "Part_%d" % obj_id)


def _is_face_list(cad_obj):
    return all([isinstance(obj, Face) for obj in cad_obj.objects])


def _is_edge_list(cad_obj):
    return all([isinstance(obj, Edge) for obj in cad_obj.objects])


def _is_wire_list(cad_obj):
    return all([isinstance(obj, Wire) for obj in cad_obj.objects])


def show(*cad_objs,
         height=600,
         tree_width=250,
         cad_width=800,
         quality=0.5,
         axes=False,
         axes0=True,
         grid=False,
         ortho=True,
         transparent=False,
         mac_scrollbar=True,
         sidecar=None):

    assembly = Assembly([], "Assembly")
    obj_id = 0
    for cad_obj in cad_objs:
        if isinstance(cad_obj, (Assembly, Part, Faces, Edges)):
            assembly.add(cad_obj)

        elif _is_face_list(cad_obj):
            assembly.add_list(_face_list_to_objs(cad_obj, obj_id))

        elif _is_edge_list(cad_obj):
            assembly.add_list(_edge_list_to_objs(cad_obj, obj_id))

        elif _is_wire_list(cad_obj):
            assembly.add_list([_wire_list_to_obj(cad_obj, obj_id)])

        elif isinstance(cad_obj, Workplane):
            assembly.add(_workplane_to_obj(cad_obj, obj_id))

        obj_id += 1

    if assembly is None:
        raise ValueError("%s cannot be viewed" % type(cad_obj))
    return _show(assembly, height, tree_width, cad_width, quality, axes, axes0, grid, ortho, transparent, mac_scrollbar,
                 sidecar)
