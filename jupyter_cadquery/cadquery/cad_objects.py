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

from cadquery.occ_impl.shapes import Face, Edge
from cadquery import Workplane, Shape

from jupyter_cadquery.cad_objects import _Assembly, _Part, _Edges, _Faces, _show


class Part(_Part):

    def __init__(self, shape, name="part", color=None, show_faces=True, show_edges=True):
        super().__init__(_to_occ(shape), name, color, show_faces, show_edges)

    def to_assembly(self):
        return Assembly([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class Faces(_Faces):

    def __init__(self, faces, name="faces", color=None, show_faces=True, show_edges=True):
        super().__init__(_to_occ(faces.combine()), name, color, show_faces, show_edges)

    def to_assembly(self):
        return Assembly([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class Edges(_Edges):

    def __init__(self, edges, name="edges", color=None):
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


def _to_occ(cad_obj):
    if isinstance(cad_obj, Workplane):
        return [obj.wrapped for obj in cad_obj.objects]
    elif isinstance(cad_obj, Shape):
        return [cad_obj.wrapped]
    else:
        raise NotImplementedError(type(cad_obj))

def _edge_list_to_assembly(cad_obj):
    return Assembly(
        [Part(cad_obj.parent, show_edges=False, show_faces=False),
         Edges(cad_obj, "edges", color=(1, 0, 1))])


def _face_list_to_assembly(cad_obj):
    return Assembly(
        [Part(cad_obj.parent, show_edges=False, show_faces=False),
         Faces(cad_obj, "faces", color=(1, 0, 1))])

def _workplane_to_assembly(cad_obj):
    return Assembly([Part(cad_obj, "part")])


def _is_face_list(cad_obj):
    return all([isinstance(obj, Face) for obj in cad_obj.objects])


def _is_edge_list(cad_obj):
    return all([isinstance(obj, Edge) for obj in cad_obj.objects])


def show(cad_obj,
         height=600,
         tree_width=250,
         cad_width=800,
         quality=0.5,
         axes=False,
         axes0=True,
         grid=False,
         ortho=True,
         transparent=False,
         mac_scrollbar=True):

    assembly = None
    if isinstance(cad_obj, (Assembly, Part, Faces, Edges)):
        assembly = cad_obj.to_assembly()
    elif _is_edge_list(cad_obj):
        assembly = _edge_list_to_assembly(cad_obj)
    elif _is_face_list(cad_obj):
        assembly = _face_list_to_assembly(cad_obj)
    elif isinstance(cad_obj, Workplane):
        assembly = _workplane_to_assembly(cad_obj)

    if assembly is None:
        raise ValueError("%s cannot be viewed" % type(cad_obj))
    return _show(assembly, height, tree_width, cad_width, quality, axes, axes0, grid, ortho, transparent, mac_scrollbar)
