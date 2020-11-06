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

import math
import itertools
from cadquery.occ_impl.shapes import Vertex, Shape
import numpy as np

import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from pythreejs import (
        CombinedCamera,
        Plane,
        Mesh,
        LineSegments2,
        AmbientLight,
        DirectionalLight,
        Scene,
        OrbitControls,
        Renderer,
        Picker,
        Group,
    )


from .widgets import state_diff
from .cad_helpers import Grid, Axes
from .ocp_utils import BoundingBox
from .utils import rotate, Color
from .cad_renderer import CadqueryRenderer


def tq(loc):
    T = loc.wrapped.Transformation()
    t = T.Transforms()
    q = T.GetRotation()
    return (t, (q.X(), q.Y(), q.Z(), q.W()))


class CadqueryView(object):
    def __init__(
        self,
        shapes,
        width=600,
        height=400,
        quality=0.1,
        angular_tolerance=0.1,
        edge_accuracy=0.01,
        render_edges=True,
        render_shapes=True,
        info=None,
        timeit=False,
    ):

        self.shapes = shapes
        self.width = width
        self.height = height
        self.quality = quality
        self.angular_tolerance = angular_tolerance
        self.edge_accuracy = edge_accuracy
        self.render_edges = render_edges
        self.render_shapes = render_shapes
        self.info = info
        self.timeit = timeit

        self.pick_color = Color("LightGreen")
        self.default_mesh_color = Color((232, 176, 36))
        self.default_edge_color = Color((128, 128, 128))

        self.camera_distance_factor = 6
        self.camera_initial_zoom = 2.5

        self.features = ["mesh", "edges"]

        self.bb = None

        self.pickable_objects = None
        self.pick_last_mesh = None
        self.pick_last_mesh_color = None
        self.pick_mapping = {}

        self.camera = None
        self.axes = None
        self.grid = None
        self.scene = None
        self.controller = None
        self.renderer = None

        self.savestate = None

    def get_transparent(self):
        # if one object is transparent, all are
        return self.pickable_objects.children[0].material.transparent

    def _scale(self, vec):
        r = self.bb.max_dist_from_center() * self.camera_distance_factor
        n = np.linalg.norm(vec)
        new_vec = [v / n * r for v in vec]
        return new_vec

    def _add(self, vec1, vec2):
        return list(v1 + v2 for v1, v2 in zip(vec1, vec2))

    def _sub(self, vec1, vec2):
        return list(v1 - v2 for v1, v2 in zip(vec1, vec2))

    def _norm(self, vec):
        n = np.linalg.norm(vec)
        return [v / n for v in vec]

    def _minus(self, vec):
        return [-v for v in vec]

    def direction(self):
        return self._norm(self._sub(self.camera.position, self.bb.center))

    def set_plane(self, i):
        plane = self.renderer.clippingPlanes[i]
        plane.normal = self._minus(self.direction())

    def _update(self):
        self.controller.exec_three_obj_method("update")
        pass

    def _reset(self):
        self.camera.rotation, self.controller.target = self.savestate
        self.camera.position = self._add(self.bb.center, self._scale((1, 1, 1)))
        self.camera.zoom = self.camera_initial_zoom
        self._update()

    # UI Handler

    def change_view(self, typ, directions):
        def reset(b):
            self._reset()

        def refit(b):
            self.camera.zoom = self.camera_initial_zoom
            self._update()

        def change(b):
            self.camera.position = self._add(
                self.bb.center, self._scale(directions[typ])
            )
            self._update()

        if typ == "fit":
            return refit
        elif typ == "reset":
            return reset
        else:
            return change

    def bool_or_new(self, val):
        return val if isinstance(val, bool) else val["new"]

    def toggle_axes(self, change):
        self.axes.set_visibility(self.bool_or_new(change))

    def toggle_grid(self, change):
        self.grid.set_visibility(self.bool_or_new(change))

    def toggle_center(self, change):
        self.grid.set_center(self.bool_or_new(change))
        self.axes.set_center(self.bool_or_new(change))

    def toggle_ortho(self, change):
        self.camera.mode = "orthographic" if self.bool_or_new(change) else "perspective"

    def toggle_transparent(self, change):
        def toggle(group, value):
            for obj in group.children:
                if isinstance(obj, Group):
                    toggle(obj, value)
                else:
                    if isinstance(obj, Mesh):
                        obj.material.transparent = value

        value = self.bool_or_new(change)
        toggle(self.pickable_objects, value)

    def toggle_black_edges(self, change):
        def toggle(group, value):
            for obj in group.children:
                if isinstance(obj, Group):
                    toggle(obj, value)
                else:
                    if isinstance(obj, LineSegments2):
                        if obj.material.linewidth == 1:
                            obj.material.color = (
                                "#000" if value else self.default_edge_color.web_color
                            )

        value = self.bool_or_new(change)
        toggle(self.pickable_objects, value)

    def _get_group(self, group_index):
        try:
            group = self.pickable_objects
            for j in group_index:
                group = group.children[j]
            return group
        except:
            return None

    def set_visibility(self, ind, i, state):
        feature = self.features[i]
        group_index = self.pick_mapping[ind][feature]
        group = self._get_group(group_index)
        if group is not None:
            group.visible = state == 1

    def change_visibility(self, paths):
        def f(states):
            diffs = state_diff(states.get("old"), states.get("new"))
            for diff in diffs:
                [[obj, val]] = diff.items()
                self.set_visibility(paths[obj], val["icon"], val["new"])

        return f

    def _get_shape(self, shape_index):
        shape = self.shapes
        try:
            for j in shape_index:
                shape = shape["parts"][j]
        except:
            return None
        return shape

    def pick(self, value):
        if self.pick_last_mesh != value.owner.object:
            # Reset
            if value.owner.object is None or self.pick_last_mesh is not None:
                self.pick_last_mesh.material.color = self.pick_last_mesh_color
                self.pick_last_mesh = None
                self.pick_last_mesh_color = None

            # Change highlighted mesh
            if isinstance(value.owner.object, Mesh):
                self.pick_last_mesh = value.owner.object
                shape = self._get_shape(value.owner.object.ind["shape"])
                bbox = BoundingBox([shape["shape"]])

                self.info.bb_info(
                    shape["name"],
                    (
                        (bbox.xmin, bbox.xmax),
                        (bbox.ymin, bbox.ymax),
                        (bbox.zmin, bbox.zmax),
                        bbox.center,
                    ),
                )
                self.pick_last_mesh_color = self.pick_last_mesh.material.color
                self.pick_last_mesh.material.color = self.pick_color.web_color

    def clip(self, index):
        def f(change):
            self.renderer.clippingPlanes[index].constant = change["new"]

        return f

    # public methods to render the view

    def is_ortho(self):
        return self.camera.mode == "orthographic"

    def is_transparent(self):
        return self.pickable_objects.children[0].material.transparent

    def render(self, position=None, rotation=None, zoom=2.5):
        def all_shapes(shapes, loc=None):
            loc = shapes["loc"] if loc is None else loc * shapes["loc"]
            result = []
            for shape in shapes["parts"]:
                if shape.get("parts") is None:
                    if loc is None:
                        result.append(shape["shape"])
                    else:
                        reloc_shape = [
                            Shape(s).located(loc).wrapped for s in shape["shape"]
                        ]
                        result.append(reloc_shape)
                else:
                    result += all_shapes(shape, loc)
            return result

        position = position or (1, 1, 1)
        rotation = rotation or (0, 0, 0)

        self.camera_initial_zoom = zoom

        cq_renderer = CadqueryRenderer(
            quality=self.quality,
            angular_tolerance=self.angular_tolerance,
            edge_accuracy=self.edge_accuracy,
            render_edges=self.render_edges,
            render_shapes=self.render_shapes,
            default_mesh_color=self.default_mesh_color,
            default_edge_color=self.default_edge_color,
            timeit=self.timeit,
        )
        self.pickable_objects, self.pick_mapping = cq_renderer.render(self.shapes)

        # Get the overall bounding box

        self.bb = BoundingBox(all_shapes(self.shapes))
        if self.bb.is_empty():
            # add origin to increase bounding box to also show origin
            self.bb = BoundingBox(
                [[Vertex.makeVertex(0, 0, 0).wrapped]]
                + [shape["shape"] for shape in self.shapes]
            )
            if self.bb.is_empty():
                # looks like only one vertex in origin is to be shown
                self.bb = BoundingBox(
                    [[Vertex.makeVertex(0.1, 0.1, 0.1).wrapped]]
                    + [shape["shape"] for shape in self.shapes]
                )

        bb_max = self.bb.max
        orbit_radius = 2 * self.bb.max_dist_from_center()

        # Set up camera
        camera_target = self.bb.center
        camera_up = (0.0, 0.0, 1.0)

        if rotation != (0, 0, 0):
            position = rotate(position, *rotation)

        camera_position = self._add(
            self.bb.center,
            self._scale([1, 1, 1] if position is None else self._scale(position)),
        )

        self.camera = CombinedCamera(
            position=camera_position,
            width=self.width,
            height=self.height,
            far=10 * orbit_radius,
            orthoFar=10 * orbit_radius,
        )
        self.camera.up = camera_up

        self.camera.mode = "orthographic"
        self.camera.position = camera_position

        # Set up lights in every of the 8 corners of the global bounding box
        positions = list(itertools.product(*[(-orbit_radius, orbit_radius)] * 3))
        key_lights = [
            DirectionalLight(color="white", position=position, intensity=0.12)
            for position in positions
        ]
        ambient_light = AmbientLight(intensity=1.0)

        # Set up Helpers
        self.axes = Axes(bb_center=self.bb.center, length=bb_max * 1.1)
        self.grid = Grid(
            bb_center=self.bb.center,
            maximum=bb_max,
            colorCenterLine="#aaa",
            colorGrid="#ddd",
        )

        # Set up scene
        environment = (
            self.axes.axes + key_lights + [ambient_light, self.grid.grid, self.camera]
        )
        self.scene = Scene(children=environment + [self.pickable_objects])

        # Set up Controllers
        self.controller = OrbitControls(
            controlling=self.camera, target=camera_target, target0=camera_target
        )

        # Update controller to instantiate camera position
        self.camera.zoom = zoom
        self._update()

        self.picker = Picker(controlling=self.pickable_objects, event="dblclick")
        self.picker.observe(self.pick)

        # Create Renderer instance
        self.renderer = Renderer(
            scene=self.scene,
            camera=self.camera,
            controls=[self.controller, self.picker],
            antialias=True,
            width=self.width,
            height=self.height,
        )

        self.renderer.localClippingEnabled = True
        self.renderer.clippingPlanes = [
            Plane((1, 0, 0), self.grid.size / 2),
            Plane((0, 1, 0), self.grid.size / 2),
            Plane((0, 0, 1), self.grid.size / 2),
        ]

        # needs to be done after setup of camera
        self.grid.set_rotation((math.pi / 2.0, 0, 0, "XYZ"))
        self.grid.set_position((0, 0, 0))

        self.savestate = (self.camera.rotation, self.controller.target)

        return self.renderer

    def find_group(self, selector):
        return self.pickable_objects.find_group(selector)