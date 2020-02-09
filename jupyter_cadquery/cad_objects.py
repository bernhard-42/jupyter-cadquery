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

import os
import json

from IPython.display import display

from cadquery import Compound

from jupyter_cadquery.cad_display import CadqueryDisplay
from jupyter_cadquery.widgets import UNSELECTED, SELECTED, EMPTY

PART_ID = 0

#
# Simple Part and Assembly classes
#


class _CADObject(object):

    def __init__(self):
        self.color = (232, 176, 36)

    def next_id(self):
        global PART_ID
        PART_ID += 1
        return PART_ID

    def to_nav_dict(self):
        raise NotImplementedError("not implemented yet")

    def to_state(self):
        raise NotImplementedError("not implemented yet")

    def collect_shapes(self):
        raise NotImplementedError("not implemented yet")

    def to_assembly(self):
        raise NotImplementedError("not implemented yet")

    def show(self, grid=False, axes=False):
        raise NotImplementedError("not implemented yet")

    def web_color(self):
        if isinstance(self.color, str):
            if self.color[0] == "#":
                return self.color
        else:
            # Note: (1,1,1) will be interpreted as (1,1,1). Use (255,255,255) if needed
            if any((c < 1) for c in self.color):
                return "rgb(%d, %d, %d)" % tuple([c * 255 for c in self.color])
            else:
                return "rgb(%d, %d, %d)" % self.color


class _Part(_CADObject):

    def __init__(self, shape, name="Part", color=None, show_faces=True, show_edges=True):
        super().__init__()
        self.name = name
        self.id = self.next_id()
        if color is not None:
            self.color = color
        self.shape = shape
        self.set_states(show_faces, show_edges)

    def set_states(self, show_faces, show_edges):
        self.state_faces = SELECTED if show_faces else UNSELECTED
        self.state_edges = SELECTED if show_edges else UNSELECTED

    def to_nav_dict(self):
        return {"type": "leaf", "name": self.name, "id": self.id, "color": self.web_color()}

    def to_state(self):
        return {str(self.id): [self.state_faces, self.state_edges]}

    def collect_shapes(self):
        return [{"name": self.name, "shape": self.shape, "color": self.web_color()}]

    def compound(self):
        return self.shape[0]

    def compounds(self):
        return [self.compound()]


class _Faces(_Part):

    def __init__(self, faces, name="Faces", color=None, show_faces=True, show_edges=True):
        super().__init__(faces, name, color, show_faces, show_edges)
        self.color = (1, 0, 1) if color is None else color


class _Edges(_CADObject):

    def __init__(self, edges, name="Edges", color=None):
        super().__init__()
        self.shape = edges
        self.name = name
        self.id = self.next_id()
        self.color = (1, 0, 1) if color is None else color

    def to_nav_dict(self):
        return {"type": "leaf", "name": self.name, "id": self.id, "color": self.web_color()}

    def to_state(self):
        return {str(self.id): [EMPTY, SELECTED]}

    def collect_shapes(self):
        return [{"name": self.name, "shape": [edge for edge in self.shape], "color": self.web_color()}]


class _Vertices(_CADObject):

    def __init__(self, vertices, name="Vertices", color=None):
        super().__init__()
        self.shape = vertices
        self.name = name
        self.id = self.next_id()
        self.color = (1, 0, 1) if color is None else color

    def to_nav_dict(self):
        return {"type": "leaf", "name": self.name, "id": self.id, "color": self.web_color()}

    def to_state(self):
        return {str(self.id): [SELECTED, EMPTY]}

    def collect_shapes(self):
        return [{"name": self.name, "shape": [edge for edge in self.shape], "color": self.web_color()}]


class _Assembly(_CADObject):

    def __init__(self, objects, name="Assembly"):
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

    def collect_shapes(self):
        result = []
        for obj in self.objects:
            result += obj.collect_shapes()
        return result

    def obj_mapping(self):
        return {v: k for k, v in enumerate(self.to_state().keys())}

    @classmethod
    def reset_id(cls):
        global PART_ID
        PART_ID = 0

    def compounds(self):
        result = []
        for obj in self.objects:
            result += obj.compounds()
        return result

    def compound(self):
        return Compound._makeCompound(self.compounds())


def set_defaults(height=600,
                 tree_width=250,
                 cad_width=800,
                 quality=0.5,
                 edge_accuracy=0.5,
                 axes=False,
                 axes0=False,
                 grid=False,
                 ortho=True,
                 transparent=False,
                 position=(1, 1, 1),
                 rotation=(0, 0, 0),
                 zoom=2.5,
                 mac_scrollbar=True,
                 sidecar=None,
                 timeit=False):
    """Set defaults for CAD viewer

    Valid keywords:
    - height:        Height of the CAD view
    - tree_width:    Width of navigation tree part of the view
    - cad_width:     Width of CAD view part of the view
    - quality:       Mesh quality for tesselation
    - edge_accuracy: Presicion of edge discretizaion
    - axes:          Show axes
    - axes0:         Show axes at (0,0,0)
    - grid:          Show grid
    - ortho:         Use orthographic projections
    - transparent:   Show objects transparent
    - position:      Relative camera position that will be scaled
    - rotation:      z, y and y rotation angles of position
    - zoom:          Zoom factor of view
    - mac_scrollbar: Prettify scrollbasrs on Macs
    - sidecar:       Use provided sidecar
    - timeit:        Show rendering times

    For example isometric projection can be achieved in two ways:
    - position = (1, 1, 1)
    - position = (0, 0, 1) and rotation = (45, 35.264389682, 0) 
    """
    CadqueryDisplay.defaults["height"] = height
    CadqueryDisplay.defaults["tree_width"] = tree_width
    CadqueryDisplay.defaults["cad_width"] = cad_width
    CadqueryDisplay.defaults["quality"] = quality
    CadqueryDisplay.defaults["edge_accuracy"] = edge_accuracy
    CadqueryDisplay.defaults["axes"] = axes
    CadqueryDisplay.defaults["axes0"] = axes0
    CadqueryDisplay.defaults["grid"] = grid
    CadqueryDisplay.defaults["ortho"] = ortho
    CadqueryDisplay.defaults["transparent"] = transparent
    CadqueryDisplay.defaults["position"] = position
    CadqueryDisplay.defaults["rotation"] = rotation
    # for zoom == 1 viewing has a bug, so slightly increase it
    if zoom == 1:
        zoom = 1 + 1e-6
    CadqueryDisplay.defaults["zoom"] = zoom
    CadqueryDisplay.defaults["mac_scrollbar"] = mac_scrollbar
    CadqueryDisplay.defaults["sidecar"] = sidecar
    CadqueryDisplay.defaults["timeit"] = timeit


def get_defaults():
    return CadqueryDisplay.defaults


def reset_defaults():
    CadqueryDisplay.defaults = {
        "height": 600,
        "tree_width": 250,
        "cad_width": 800,
        "quality": 0.5,
        "edge_accuracy": 0.5,
        "axes": False,
        "axes0": False,
        "grid": False,
        "ortho": True,
        "transparent": False,
        "position": (1, 1, 1),
        "rotation": (0, 0, 0),
        "zoom": 2.5,
        "mac_scrollbar": True,
        "sidecar": None,
        "timeit": False
    }


def _show(assembly, **kwargs):

    d = CadqueryDisplay()
    params = d.defaults.copy()
    for k,v in kwargs.items():
        if params.get(k, None) is None:
            raise KeyError("Paramater %s is not a valid argument for show()" % k)
        else:
            params[k] = v

    widget = d.create(
        states=assembly.to_state(),
        shapes=assembly.collect_shapes(),
        mapping=assembly.obj_mapping(),
        tree=assembly.to_nav_dict(),
        height=params["height"],
        tree_width=params["tree_width"],
        cad_width=params["cad_width"],
        quality=params["quality"],
        edge_accuracy=params["edge_accuracy"],
        axes=params["axes"],
        axes0=params["axes0"],
        grid=params["grid"],
        ortho=params["ortho"],
        transparent=params["transparent"],
        position=params["position"],
        rotation=params["rotation"],
        zoom=params["zoom"],
        mac_scrollbar=params["mac_scrollbar"],
        timeit=params["timeit"])

    d.info.ready_msg(d.cq_view.grid.step)

    d.display(widget, params["sidecar"])

    return d
