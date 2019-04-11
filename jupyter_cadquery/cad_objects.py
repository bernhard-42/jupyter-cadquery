import os
import json

import cadquery as cq
from cadquery import Shape, Compound, CQ

from .tree_view import UNSELECTED, SELECTED, EMPTY

part_id = 0

#
# Create simple Part and Assembly classes
#

class CADObject(object):

    def __init__(self):
        self.color = (0.9, 0.9, 0.9)

    def next_id(self):
        global part_id
        part_id += 1
        return part_id

    def to_nav_dict(self):
        raise NotImplementedError("not implemented yet")

    def to_state(self):
        raise NotImplementedError("not implemented yet")

    def web_color(self):
        return "rgba(%d, %d, %d, 0.6)" % tuple([c * 255 for c in self.color])

    # def _repr_html_(self):
    #     display(self)


class Part(CADObject):

    def __init__(self, shape, name="part", color=None, show_faces=True, show_edges=True):
        super().__init__()
        self.name = name
        self.id = self.next_id()
        if color is not None:
            self.color = color
        self.shape = shape
        self.state_faces = SELECTED if show_faces else UNSELECTED
        self.state_edges = SELECTED if show_edges else UNSELECTED

    def to_nav_dict(self):
        return {
            "type": "leaf",
            "name": self.name,
            "id": self.id,
            "color": self.web_color()
        }

    def to_state(self):
        return {str(self.id): [self.state_faces, self.state_edges]}


class Faces(Part):

    def __init__(self, shape, name="faces", color=None, show_faces=True, show_edges=True):
        super().__init__(shape.combine(), name, color, show_faces, show_edges)


class Edges(CADObject):

    def __init__(self, edges, name="edges", color=None):
        super().__init__()
        self.shape = edges
        self.name = name
        self.id = self.next_id()
        if color is not None:
            self.color = color

    def to_nav_dict(self):
        return {
            "type": "leaf",
            "name": self.name,
            "id": self.id,
            "color": self.web_color()
        }

    def to_state(self):
        return {str(self.id): [EMPTY, 1]}



class Assembly(CADObject):

    def __init__(self, objects, name="assembly"):
        super().__init__()
        self.name = name
        self.id = self.next_id()
        self.objects = objects

    def to_nav_dict(self):
        return {
            "type": "node",
            "name": self.name,
            "id": self.id,
            "children": [obj.to_nav_dict() for obj in self.objects]
        }

    def to_state(self):
        result = {}
        for obj in self.objects:
            result.update(obj.to_state())
        return result

    def obj_mapping(self):
        return  {v:k for k,v in enumerate(self.to_state().keys())}

    @classmethod
    def reset_id(cls):
        global part_id
        part_id = 0


def is_edges(cadObj):
    return all([isinstance(obj, cq.occ_impl.shapes.Edge) for obj in cadObj.objects])


def is_faces(cadObj):
    return all([isinstance(obj, cq.occ_impl.shapes.Face) for obj in cadObj.objects])


def convert(cadObj):
    if isinstance(cadObj, (Assembly, Part, Faces, Edges)):
        return cadObj
    elif is_edges(cadObj):
        return Edges(cadObj, color=(1, 0, 0))
    elif is_faces(cadObj):
        return Faces(cadObj, color=(0, 1, 0))
    else:
        return Part(cadObj, color=(0.9, 0.9, 0.9), show_edges=False)


# def repr_html(obj):
#     """
#     Jupyter 3D representation support
#     """
#     if is_edges(obj):
#         cadObj = Edges(obj, name="edges", color=(1, 0, 0))
#     elif is_faces(obj):
#         cadObj = Faces(obj, name="faces", color=(0, 1, 0))
#     else:
#         cadObj = obj

#     return display(cadObj)
