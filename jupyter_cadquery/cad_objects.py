import os
import json

from IPython.display import display as idisplay

import cadquery as cq
from cadquery import Shape, Compound, Workplane
from OCC.Display.WebGl.jupyter_renderer import bounding_box

from .tree_view import UNSELECTED, SELECTED, EMPTY
from .cad_display import CadqueryDisplay

part_id = 0

#
# Create simple Part and Assembly classes
#


class CADObject(object):

    def __init__(self):
        self.color = (0.1, 0.1, 0.1)

    def next_id(self):
        global part_id
        part_id += 1
        return part_id

    def to_nav_dict(self):
        raise NotImplementedError("not implemented yet")

    def to_state(self):
        raise NotImplementedError("not implemented yet")

    def web_color(self):
        return "rgb(%d, %d, %d)" % tuple([c * 255 for c in self.color])

    def _ipython_display_(self):
        idisplay(display(self))


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
        return {"type": "leaf", "name": self.name, "id": self.id, "color": self.web_color()}

    def to_state(self):
        return {str(self.id): [self.state_faces, self.state_edges]}


class Faces(Part):

    def __init__(self, shape, name="faces", color=None, show_faces=True, show_edges=True):
        super().__init__(shape.combine(), name, color, show_faces, show_edges)
        self.color = (1, 0, 1) if color is None else color

    def _ipython_display_(self):
        idisplay(display(self, grid=False, axes=False))


class Edges(CADObject):

    def __init__(self, edges, name="edges", color=None):
        super().__init__()
        self.shape = edges
        self.name = name
        self.id = self.next_id()
        self.color = (1, 0, 1) if color is None else color

    def to_nav_dict(self):
        return {"type": "leaf", "name": self.name, "id": self.id, "color": self.web_color()}

    def to_state(self):
        return {str(self.id): [EMPTY, SELECTED]}

    def _ipython_display_(self):
        idisplay(display(self, grid=False, axes=False))


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
        return {v: k for k, v in enumerate(self.to_state().keys())}

    @classmethod
    def reset_id(cls):
        global part_id
        part_id = 0


def is_edges(cadObj):
    return all([isinstance(obj, cq.occ_impl.shapes.Edge) for obj in cadObj.objects])


def is_faces(cadObj):
    return all([isinstance(obj, cq.occ_impl.shapes.Face) for obj in cadObj.objects])


def convert(cadObj, show_edges=True, show_faces=True):
    if isinstance(cadObj, (Assembly, Part, Faces, Edges)):
        return cadObj
    elif is_edges(cadObj):
        return Edges(cadObj, "edges", color=(1, 0, 1))
    elif is_faces(cadObj):
        return Faces(cadObj, "faces", color=(1, 0, 1), show_edges=show_edges, show_faces=show_faces)
    else:
        return Part(cadObj, "part", color=(0.1, 0.1, 0.1), show_edges=show_edges, show_faces=show_faces)


def display(cad_obj,
            height=600,
            tree_width=250,
            cad_width=800,
            axes=False,
            axes0=True,
            grid=False,
            ortho=True,
            transparent=False,
            mac_scrollbar=True):

    assembly = None
    if isinstance(cad_obj, Assembly):
        assembly = cad_obj
    elif isinstance(cad_obj, Part):
        assembly = Assembly([convert(cad_obj)])
    elif is_edges(cad_obj):
        assembly = Assembly([convert(cad_obj.parent, False, False), convert(cad_obj)])
    elif is_faces(cad_obj):
        assembly = Assembly([convert(cad_obj.parent, False, False), convert(cad_obj)])
    elif isinstance(cad_obj, Workplane):
        assembly = Assembly([convert(cad_obj)])

    if assembly is not None:
        d = CadqueryDisplay()
        v = d.display(
            assembly=assembly,
            height=height,
            tree_width=tree_width,
            cad_width=cad_width,
            axes=axes,
            axes0=axes0,
            grid=grid,
            ortho=ortho,
            transparent=transparent,
            mac_scrollbar=mac_scrollbar)
        d._debug("Rendering done")
        d._debug("Grid: %5.1f mm" % d.cq_view.grid.step)
        return v