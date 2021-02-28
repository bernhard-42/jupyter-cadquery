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

from cadquery import Compound

from jupyter_cadquery.cad_display import CadqueryDisplay, get_default
from jupyter_cadquery_widgets.widgets import UNSELECTED, SELECTED, EMPTY
from jupyter_cadquery.utils import Color

PART_ID = 0


#
# Simple Part and PartGroup classes
#


class _CADObject(object):
    def __init__(self):
        self.color = Color((232, 176, 36))

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


class _Part(_CADObject):
    def __init__(self, shape, name="Part", color=None, show_faces=True, show_edges=True):
        super().__init__()
        self.name = name
        self.id = self.next_id()

        if color is not None:
            if isinstance(color, (list, tuple)) and isinstance(color[0], Color):
                self.color = color
            elif isinstance(color, Color):
                self.color = color
            else:
                self.color = Color(color)
        self.shape = shape
        self.set_states(show_faces, show_edges)

    def set_states(self, show_faces, show_edges):
        self.state_faces = SELECTED if show_faces else UNSELECTED
        self.state_edges = SELECTED if show_edges else UNSELECTED

    def to_nav_dict(self):
        if isinstance(self.color, (tuple, list)):
            color = (c.web_color for c in self.color)
        else:
            color = self.color.web_color
        return {
            "type": "leaf",
            "name": self.name,
            "id": self.id,
            "color": color,
        }

    def to_state(self):
        return [self.state_faces, self.state_edges]

    def collect_shapes(self):
        return {
            "id": self.id,
            "name": self.name,
            "shape": self.shape,
            "color": self.color,
        }

    def compound(self):
        return self.shape[0]

    def compounds(self):
        return [self.compound()]


class _Faces(_Part):
    def __init__(self, faces, name="Faces", color=None, show_faces=True, show_edges=True):
        super().__init__(faces, name, color, show_faces, show_edges)
        self.color = Color(color or (255, 0, 255))


class _Edges(_CADObject):
    def __init__(self, edges, name="Edges", color=None):
        super().__init__()
        self.shape = edges
        self.name = name
        self.id = self.next_id()
        self.color = Color(color or (255, 0, 255))

    def to_nav_dict(self):
        return {
            "type": "leaf",
            "name": self.name,
            "id": self.id,
            "color": self.color.web_color,
        }

    def to_state(self):
        return [EMPTY, SELECTED]

    def collect_shapes(self):
        return {
            "id": self.id,
            "name": self.name,
            "shape": [edge for edge in self.shape],
            "color": self.color,
        }


class _Vertices(_CADObject):
    def __init__(self, vertices, name="Vertices", color=None):
        super().__init__()
        self.shape = vertices
        self.name = name
        self.id = self.next_id()
        self.color = Color(color or (255, 0, 255))

    def to_nav_dict(self):
        return {
            "type": "leaf",
            "name": self.name,
            "id": self.id,
            "color": self.color.web_color,
        }

    def to_state(self):
        return [SELECTED, EMPTY]

    def collect_shapes(self):
        return {
            "id": self.id,
            "name": self.name,
            "shape": [edge for edge in self.shape],
            "color": self.color,
        }


class _PartGroup(_CADObject):
    def __init__(self, objects, name="Group", loc=None):
        super().__init__()
        self.objects = objects
        self.name = name
        self.loc = loc
        self.id = self.next_id()

    def to_nav_dict(self):
        return {
            "type": "node",
            "name": self.name,
            "id": self.id,
            "children": [obj.to_nav_dict() for obj in self.objects],
        }

    def collect_shapes(self):
        result = {"parts": [], "loc": None}
        for obj in self.objects:
            result["parts"].append(obj.collect_shapes())
        result["loc"] = self.loc
        result["name"] = self.name
        return result

    def collect_mapped_shapes(self, mapping):
        def set_paths(shapes, mapping):
            for obj in shapes["parts"]:
                if obj.get("parts") is None:
                    obj["ind"] = mapping[str(obj["id"])]["path"]
                else:
                    set_paths(obj, mapping)

        shapes = self.collect_shapes()
        set_paths(shapes, mapping)
        return shapes

    def to_state(self, parents=None):
        parents = parents or ()
        result = {}
        for i, obj in enumerate(self.objects):
            if isinstance(obj, _PartGroup):
                for k, v in obj.to_state((*parents, i)).items():
                    result[k] = v
            else:
                result[str(obj.id)] = {"path": (*parents, i), "state": obj.to_state()}
        return result

    @staticmethod
    def reset_id():
        global PART_ID
        PART_ID = 0

    def compounds(self):
        result = []
        for obj in self.objects:
            result += obj.compounds()
        return result

    def compound(self):
        return Compound._makeCompound(self.compounds())


def _show(assembly, **kwargs):
    for k in kwargs:
        if get_default(k) is None:
            raise KeyError("Paramater %s is not a valid argument for show()" % k)

    mapping = assembly.to_state()
    shapes = assembly.collect_mapped_shapes(mapping)
    tree = tree = assembly.to_nav_dict()

    d = CadqueryDisplay()
    widget = d.create(**kwargs)
    d.display(widget)
    d.add_shapes(shapes=shapes, mapping=mapping, tree=tree)

    d.info.ready_msg(d.cq_view.grid.step)

    return d
