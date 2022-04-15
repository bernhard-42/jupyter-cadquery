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

import numpy as np

from cadquery import Compound, __version__

from cad_viewer_widget import show as viewer_show

from jupyter_cadquery.progress import Progress
from jupyter_cadquery.utils import Color, Timer, warn
from jupyter_cadquery.ocp_utils import bounding_box, get_point, loc_to_tq, BoundingBox, wrapped_or_None
from jupyter_cadquery.tessellator import discretize_edge, tessellate, compute_quality, bbox_edges
from jupyter_cadquery.mp_tessellator import (
    is_apply_result,
    mp_tessellate,
    get_mp_result,
    keymap,
    init_pool,
    close_pool,
)
from jupyter_cadquery.defaults import (
    get_default,
    apply_defaults,
    create_args,
    add_shape_args,
    tessellation_args,
    show_args,
    preset,
)


UNSELECTED = 0
SELECTED = 1
EMPTY = 3

#
# Simple Part and PartGroup classes
#


class _CADObject(object):
    def __init__(self):
        self.color = Color(get_default("default_color"))

    def to_state(self):
        raise NotImplementedError("not implemented yet")

    def collect_shapes(
        self,
        path,
        loc,
        deviation,
        angular_tolerance,
        edge_accuracy,
        render_edges,
        parallel,
        progress,
        timeit,
    ):
        raise NotImplementedError("not implemented yet")


class _Part(_CADObject):
    def __init__(self, shape, name="Part", color=None, show_faces=True, show_edges=True):
        super().__init__()
        self.name = name
        self.id = None
        self.color = Color(get_default("default_color") if color is None else color)

        self.shape = shape
        self.set_states(show_faces, show_edges)
        self.renderback = False

    def set_states(self, show_faces, show_edges):
        self.state_faces = SELECTED if show_faces else UNSELECTED
        self.state_edges = SELECTED if show_edges else UNSELECTED

    def to_state(self):
        return [self.state_faces, self.state_edges]

    def collect_shapes(
        self,
        path,
        loc,
        deviation,
        angular_tolerance,
        edge_accuracy,
        render_edges,
        parallel=False,
        progress=None,
        timeit=False,
    ):
        self.id = f"{path}/{self.name}"

        # A first rough estimate of the bounding box.
        # Will be too large, but is sufficient for computing the quality
        with Timer(timeit, self.name, "compute quality:", 2) as t:
            bb = bounding_box(self.shape, loc=wrapped_or_None(loc), optimal=False)
            quality = compute_quality(bb, deviation=deviation)
            t.info = str(bb)

        with Timer(timeit, self.name, "tessellate:     ", 2) as t:
            func = mp_tessellate if parallel else tessellate
            result = func(
                self.shape,
                loc_to_tq(wrapped_or_None(loc)),
                deviation=deviation,
                quality=quality,
                angular_tolerance=angular_tolerance,
                debug=timeit,
                compute_edges=render_edges,
            )

            t.info = f"{{quality:{quality:.4f}, angular_tolerance:{angular_tolerance:.2f}}}"

            if parallel and is_apply_result(result):
                mesh = result
                bb = {}
            else:
                mesh, bb = result

        if progress is not None:
            progress.update()

        if isinstance(self.color, tuple):
            color = [c.web_color for c in self.color]  # pylint: disable=not-an-iterable
        else:
            color = self.color.web_color

        return {
            "id": self.id,
            "type": "shapes",
            "name": self.name,
            "shape": mesh,
            "color": color,
            "renderback": self.renderback,
            "accuracy": quality,
            "bb": bb,
        }

    def compound(self):
        return Compound._makeCompound(self.shape)

    def compounds(self):
        return [self.compound()]


class _Faces(_Part):
    def __init__(self, faces, name="Faces", color=None, show_faces=True, show_edges=True):
        super().__init__(faces, name, color, show_faces, show_edges)
        self.color = Color(color or (238, 130, 238))
        self.renderback = True


class _Edges(_CADObject):
    def __init__(self, edges, name="Edges", color=None, width=1):
        super().__init__()
        self.shape = edges
        self.name = name
        self.id = None

        if color is not None:
            if isinstance(color, (list, tuple)) and isinstance(color[0], Color):
                self.color = color
            elif isinstance(color, Color):
                self.color = color
            else:
                self.color = Color(color)
        self.width = width

    def to_state(self):
        return [EMPTY, SELECTED]

    def collect_shapes(
        self,
        path,
        loc,
        deviation,
        angular_tolerance,
        edge_accuracy,
        render_edges,
        parallel=False,
        progress=None,
        timeit=False,
    ):
        self.id = f"{path}/{self.name}"

        with Timer(timeit, self.name, "bounding box:", 2) as t:
            bb = bounding_box(self.shape, loc=wrapped_or_None(loc))
            quality = compute_quality(bb, deviation=deviation)
            deflection = quality / 100 if edge_accuracy is None else edge_accuracy
            t.info = str(bb)

        with Timer(timeit, self.name, "discretize:  ", 2):
            edges = []
            for edge in self.shape:
                edges.extend(discretize_edge(edge, deflection))
            edges = np.asarray(edges)

        if progress:
            progress.update()

        color = [c.web_color for c in self.color] if isinstance(self.color, tuple) else self.color.web_color

        return {
            "id": self.id,
            "type": "edges",
            "name": self.name,
            "shape": edges,
            "color": color,
            "width": self.width,
            "bb": bb.to_dict(),
        }


class _Vertices(_CADObject):
    def __init__(self, vertices, name="Vertices", color=None, size=1):
        super().__init__()
        self.shape = vertices
        self.name = name
        self.id = None
        self.color = Color(color or (148, 0, 211))
        self.size = size

    def to_state(self):
        return [EMPTY, SELECTED]

    def collect_shapes(
        self,
        path,
        loc,
        deviation,
        angular_tolerance,
        edge_accuracy,
        render_edges,
        parallel=False,
        progress=None,
        timeit=False,
    ):
        self.id = f"{path}/{self.name}"

        bb = bounding_box(self.shape, loc=wrapped_or_None(loc))

        if progress is not None:
            progress.update()

        return {
            "id": self.id,
            "type": "vertices",
            "name": self.name,
            "shape": [get_point(vertex) for vertex in self.shape],
            "color": self.color.web_color,
            "size": self.size,
            "bb": bb.to_dict(),
        }


class _PartGroup(_CADObject):
    def __init__(self, objects, name="Group", loc=None):
        super().__init__()
        self.objects = objects
        self.name = name
        self.loc = loc
        self.id = None

    def to_nav_dict(self):
        return {
            "type": "node",
            "name": self.name,
            "id": self.id,
            "children": [obj.to_nav_dict() for obj in self.objects],
        }

    def collect_shapes(
        self,
        path,
        loc,
        deviation,
        angular_tolerance,
        edge_accuracy,
        render_edges,
        parallel=False,
        progress=None,
        timeit=False,
    ):

        self.id = f"{path}/{self.name}"

        if loc is None and self.loc is None:
            combined_loc = None
        elif loc is None:
            combined_loc = self.loc
        else:
            combined_loc = loc * self.loc

        result = {
            "parts": [],
            "loc": None if self.loc is None else loc_to_tq(wrapped_or_None(self.loc)),
            "name": self.name,
        }
        for obj in self.objects:
            result["parts"].append(
                obj.collect_shapes(
                    self.id,
                    combined_loc,
                    deviation,
                    angular_tolerance,
                    edge_accuracy,
                    render_edges,
                    parallel,
                    progress,
                    timeit,
                )
            )
        return result

    def to_state(self, parents=None):  # pylint: disable=arguments-differ
        parents = parents or ()
        result = {}
        for i, obj in enumerate(self.objects):
            if isinstance(obj, _PartGroup):
                for k, v in obj.to_state((*parents, i)).items():
                    result[k] = v
            else:
                result[str(obj.id)] = obj.to_state()
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

    def compounds(self):
        result = []
        for obj in self.objects:
            result += obj.compounds()
        return result

    def compound(self):
        return Compound._makeCompound(self.compounds())  # pylint: disable=protected-access


def _tessellate_group(group, kwargs=None, progress=None, timeit=False):
    if kwargs is None:
        kwargs = {}

    shapes = group.collect_shapes(
        "",
        None,
        deviation=preset("deviation", kwargs.get("deviation")),
        angular_tolerance=preset("angular_tolerance", kwargs.get("angular_tolerance")),
        edge_accuracy=preset("edge_accuracy", kwargs.get("edge_accuracy")),
        render_edges=preset("render_edges", kwargs.get("render_edges")),
        parallel=kwargs.get("parallel"),
        progress=progress,
        timeit=timeit,
    )
    states = group.to_state()

    return shapes, states


def _combined_bb(shapes):
    def c_bb(shapes, bb):
        for shape in shapes["parts"]:
            if shape.get("parts") is None:
                if bb is None:
                    if shape["bb"] is None:
                        bb = BoundingBox()
                    else:
                        bb = BoundingBox(shape["bb"])
                else:
                    if shape["bb"] is not None:
                        bb.update(shape["bb"])

                # after updating the global bounding box, remove the local
                del shape["bb"]
            else:
                bb = c_bb(shape, bb)
        return bb

    bb = c_bb(shapes, None)
    return bb


def mp_get_results(shapes, progress):
    def walk(shapes):
        for shape in shapes["parts"]:
            if shape.get("parts") is None:
                if shape.get("type") == "shapes":
                    if is_apply_result(shape["shape"]):
                        mesh, bb = get_mp_result(shape["shape"])
                        shape["shape"] = mesh
                        shape["bb"] = bb

                    if progress is not None:
                        progress.update()
            else:
                walk(shape)

    walk(shapes)
    return shapes


def get_accuracies(shapes):
    def _get_accuracies(shapes, lengths):
        if shapes.get("parts"):
            for shape in shapes["parts"]:
                _get_accuracies(shape, lengths)
        elif shapes.get("type") == "shapes":
            accuracies[shapes["id"]] = shapes["accuracy"]

    accuracies = {}
    _get_accuracies(shapes, accuracies)
    return accuracies


def get_normal_len(render_normals, shapes, deviation):
    if render_normals:
        accuracies = get_accuracies(shapes)
        normal_len = max(accuracies.values()) / deviation * 4
    else:
        normal_len = 0

    return normal_len


def insert_bbox(bbox, shapes, states):
    # derive the top level states path part
    prefix = list(states)[0].split("/")[1]

    bbox = {
        "id": f"/{prefix}/BoundingBox",
        "type": "edges",
        "name": "BoundingBox",
        "shape": bbox_edges(bbox),
        "color": "#FF00FF",
        "width": 1,
        "bb": bbox,
    }
    # inject bounding box into shapes
    shapes["parts"].insert(0, bbox)
    # and states
    states[f"/{prefix}/BoundingBox"] = [3, 1]


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

    if kwargs.get("quality") is not None:
        warn("quality is ignored. Use deviation to control smoothness of edges")
        del kwargs["quality"]

    # if kwargs.get("parallel") is not None:
    #     if kwargs["parallel"] and platform.system() != "Linux":
    #         warn("parallel=True only works on Linux. Setting parallel=False")
    #         kwargs["parallel"] = False

    timeit = preset("timeit", kwargs.get("timeit"))

    with Timer(timeit, "", "overall"):

        if part_group is None:

            import base64  # pylint:disable=import-outside-toplevel
            import pickle  # pylint:disable=import-outside-toplevel
            from jupyter_cadquery.logo import LOGO_DATA  # pylint:disable=import-outside-toplevel

            logo = pickle.loads(base64.b64decode(LOGO_DATA))

            config = add_shape_args(logo["config"])
            for k, v in create_args(kwargs).items():
                config[k] = v

            shapes = logo["data"]["shapes"]
            states = logo["data"]["states"]
            bb = _combined_bb(shapes).to_dict()
            # add global bounding box
            shapes["bb"] = bb

        else:

            config = apply_defaults(**kwargs)
            if config.get("reset_camera") is False:  #  could be None
                if config.get("zoom") is not None:
                    del config["zoom"]
                if config.get("position") is not None:
                    del config["position"]
                if config.get("quaternion") is not None:
                    del config["quaternion"]

            parallel = preset("parallel", config.get("parallel"))
            with Timer(timeit, "", "tessellate", 1):
                num_shapes = part_group.count_shapes()
                progress_len = 2 * num_shapes if parallel else num_shapes
                progress = None if num_shapes < 2 else Progress(progress_len)

                if parallel:
                    init_pool()
                    keymap.reset()

                shapes, states = _tessellate_group(part_group, tessellation_args(config), progress, timeit)

                if parallel:
                    mp_get_results(shapes, progress)
                    close_pool()

                bb = _combined_bb(shapes).to_dict()
                # add global bounding box
                shapes["bb"] = bb

                if progress is not None:
                    progress.done()

            # Calculate normal length

            config["normal_len"] = get_normal_len(
                preset("render_normals", config.get("render_normals")),
                shapes,
                preset("deviation", config.get("deviation")),
            )

            show_bbox = preset("show_bbox", kwargs.get("show_bbox"))
            if show_bbox:
                insert_bbox(show_bbox, shapes, states)

        with Timer(timeit, "", "show shapes", 1):
            cv = viewer_show(shapes, states, **show_args(config))

    return cv
