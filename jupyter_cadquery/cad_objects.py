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

from cadquery import Compound, __version__

from jupyter_cadquery.cad_display import (
    get_default,
    get_or_create_display,
    has_sidecar,
)
from jupyter_cadquery_widgets.widgets import UNSELECTED, SELECTED, EMPTY
from jupyter_cadquery.utils import Color, flatten, Timer, warn
from jupyter_cadquery.ocp_utils import bounding_box, get_point, BoundingBox, loc_to_tq
from jupyter_cadquery.tessellator import discretize_edge, tessellate, compute_quality
from jupyter_cadquery.defaults import get_default, split_args

PART_ID = 0


#
# Simple Part and PartGroup classes
#


class _CADObject(object):
    def __init__(self):
        self.color = Color(get_default("default_color"))

    def next_id(self):
        global PART_ID
        PART_ID += 1
        return PART_ID

    def to_nav_dict(self):
        raise NotImplementedError("not implemented yet")

    def to_state(self):
        raise NotImplementedError("not implemented yet")

    def collect_shapes(self, loc, quality, deviation, angular_tolerance, edge_accuracy):
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
        self.color = Color(get_default("default_color") if color is None else color)

        self.shape = shape
        self.set_states(show_faces, show_edges)

    def set_states(self, show_faces, show_edges):
        self.state_faces = SELECTED if show_faces else UNSELECTED
        self.state_edges = SELECTED if show_edges else UNSELECTED

    def to_nav_dict(self):
        return {
            "type": "leaf",
            "name": self.name,
            "id": self.id,
            "color": self.color.web_color,
        }

    def to_state(self):
        return [self.state_faces, self.state_edges]

    def collect_shapes(
        self,
        loc,
        quality,
        deviation,
        angular_tolerance,
        edge_accuracy,
        render_edges,
        render_normals,
        progress=None,
        timeit=False,
    ):

        # A first rough estimate of the bounding box.
        # Will be too large, but is sufficient for computing the quality
        with Timer(timeit, self.name, "compute quality:", 2) as t:
            bb = bounding_box(self.shape, loc=loc, optimal=False)
            quality = compute_quality(bb, deviation=deviation)
            t.info = str(bb)

        normals_len = 0 if render_normals is False else quality / deviation * 5

        with Timer(timeit, self.name, "tessellate:     ", 2) as t:
            mesh = tessellate(
                self.shape,
                quality=quality,
                angular_tolerance=angular_tolerance,
                normals_len=normals_len,
                debug=timeit,
                compute_edges=render_edges,
            )
            t.info = f"{{quality:{quality:.4f}, angular_tolerance:{angular_tolerance:.2f}}}"

        # After meshing the non optimal bounding box is much more exact
        with Timer(timeit, self.name, "bounding box:   ", 2) as t:
            bb2 = bounding_box(self.shape, loc=loc, optimal=False)
            bb2.update(bb, minimize=True)
            t.info = str(bb2)

        if progress:
            progress.update()

        color = [c.web_color for c in self.color] if isinstance(self.color, tuple) else self.color.web_color

        return {
            "id": self.id,
            "type": "shapes",
            "name": self.name,
            "shape": mesh,
            "color": color,
            "bb": bb2.to_dict(),
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

        if color is not None:
            if isinstance(color, (list, tuple)) and isinstance(color[0], Color):
                self.color = color
            elif isinstance(color, Color):
                self.color = color
            else:
                self.color = Color(color)

    def to_nav_dict(self):
        if isinstance(self.color, (tuple, list)):
            color = [c.web_color for c in self.color]
        else:
            color = self.color.web_color
        return {
            "type": "leaf",
            "name": self.name,
            "id": self.id,
            "color": color,
        }

    def to_state(self):
        return [EMPTY, SELECTED]

    def collect_shapes(
        self,
        loc,
        quality,
        deviation,
        angular_tolerance,
        edge_accuracy,
        render_edges,
        render_normals,
        progress=None,
        timeit=False,
    ):
        with Timer(timeit, self.name, "bounding box:", 2) as t:
            bb = bounding_box(self.shape, loc=loc)
            quality = compute_quality(bb, deviation=deviation)
            deflection = quality / 100 if edge_accuracy is None else edge_accuracy
            t.info = str(bb)

        with Timer(timeit, self.name, "discretize:  ", 2):
            edges = flatten([discretize_edge(edge, deflection) for edge in self.shape])

        if progress:
            progress.update()

        color = [c.web_color for c in self.color] if isinstance(self.color, tuple) else self.color.web_color

        return {
            "id": self.id,
            "type": "edges",
            "name": self.name,
            "shape": edges,
            "color": color,
            "bb": bb,
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

    def collect_shapes(
        self,
        loc,
        quality,
        deviation,
        angular_tolerance,
        edge_accuracy,
        render_edges,
        render_normals,
        progress=None,
        timeit=False,
    ):
        bb = bounding_box(self.shape, loc=loc)

        if progress:
            progress.update()

        return {
            "id": self.id,
            "type": "vertices",
            "name": self.name,
            "shape": [get_point(vertex) for vertex in self.shape],
            "color": self.color.web_color,
            "bb": bb,
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

    def collect_shapes(
        self,
        loc,
        quality,
        deviation,
        angular_tolerance,
        edge_accuracy,
        render_edges,
        render_normals,
        progress=None,
        timeit=False,
    ):
        if loc is None and self.loc is None:
            combined_loc = None
        elif loc is None:
            combined_loc = self.loc
        else:
            combined_loc = loc * self.loc

        result = {"parts": [], "loc": None if self.loc is None else loc_to_tq(self.loc), "name": self.name}
        for obj in self.objects:
            result["parts"].append(
                obj.collect_shapes(
                    combined_loc,
                    quality,
                    deviation,
                    angular_tolerance,
                    edge_accuracy,
                    render_edges,
                    render_normals,
                    progress,
                    timeit,
                )
            )
        return result

    def collect_mapped_shapes(
        self,
        mapping,
        quality,
        deviation,
        angular_tolerance,
        edge_accuracy,
        render_edges,
        render_normals,
        progress=None,
        timeit=False,
    ):
        def set_paths(shapes, mapping):
            for obj in shapes["parts"]:
                if obj.get("parts") is None:
                    obj["ind"] = mapping[str(obj["id"])]["path"]
                else:
                    set_paths(obj, mapping)

        shapes = self.collect_shapes(
            loc=None,
            quality=quality,
            deviation=deviation,
            angular_tolerance=angular_tolerance,
            edge_accuracy=edge_accuracy,
            render_edges=render_edges,
            render_normals=render_normals,
            progress=progress,
            timeit=timeit,
        )
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

    def count_shapes(self):
        def c(pg):
            count = 0
            for p in pg.objects:
                if isinstance(p, _PartGroup):
                    count += c(p)
                else:
                    count += 1
            return count

        return c(self)

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


def _combined_bb(shapes):
    def c_bb(shapes, bb):
        for shape in shapes["parts"]:
            if shape.get("parts") is None:
                bb.update(shape["bb"])
            else:
                c_bb(shape, bb)

    bb = BoundingBox()
    c_bb(shapes, bb)
    return bb


def _show(part_group, **kwargs):
    for k in kwargs:
        if get_default(k, "n/a") == "n/a":
            raise KeyError(f"Paramater {k} is not a valid argument for show()")

    if kwargs.get("cad_width") is not None and kwargs.get("cad_width") < 640:
        warn("cad_width has to be >= 640, setting to 640")
        kwargs["cad_width"] = 640

    if kwargs.get("height") is not None and kwargs.get("height") < 400:
        warn("height has to be >= 400, setting to 400")
        kwargs["height"] = 400

    if kwargs.get("tree_width") is not None and kwargs.get("tree_width") < 250:
        warn("tree_width has to be >= 250, setting to 250")
        kwargs["tree_width"] = 250

    # remove all tessellation and view parameters
    create_args, add_shape_args = split_args(kwargs)

    preset = lambda key, value: get_default(key) if value is None else value

    timeit = preset("timeit", kwargs.get("timeit"))

    with Timer(timeit, "", "overall"):

        with Timer(timeit, "", "setup display", 1):
            num_shapes = part_group.count_shapes()
            d = get_or_create_display(**create_args)
            d.init_progress(2 * num_shapes)

        with Timer(timeit, "", "tessellate", 1):

            mapping = part_group.to_state()
            shapes = part_group.collect_mapped_shapes(
                mapping,
                quality=preset("quality", kwargs.get("quality")),
                deviation=preset("deviation", kwargs.get("deviation")),
                angular_tolerance=preset("angular_tolerance", kwargs.get("angular_tolerance")),
                edge_accuracy=preset("edge_accuracy", kwargs.get("edge_accuracy")),
                render_edges=preset("render_edges", kwargs.get("render_edges")),
                render_normals=preset("render_normals", kwargs.get("render_normals")),
                progress=d.progress,
                timeit=timeit,
            )
            tree = part_group.to_nav_dict()

        with Timer(timeit, "", "show shapes", 1):
            d.add_shapes(shapes=shapes, mapping=mapping, tree=tree, bb=_combined_bb(shapes), **add_shape_args)

    d.info.version_msg(__version__)
    d.info.ready_msg(d.cq_view.grid.step)

    sidecar = has_sidecar()
    if sidecar is not None:
        print(f"Done, using side car '{sidecar.title()}'")

    return d
