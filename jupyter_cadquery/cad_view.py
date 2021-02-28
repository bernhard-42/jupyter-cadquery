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


from jupyter_cadquery_widgets.widgets import state_diff
from .cad_helpers import Grid, Axes
from .ocp_utils import BoundingBox, is_compound, is_shape, is_solid
from .utils import rotate, Color, Timer
from .cad_renderer import CadqueryRenderer


class CadqueryView(object):
    def __init__(
        self,
        width=600,
        height=400,
        bb_factor=1.01,
        quality=0.1,
        angular_tolerance=0.1,
        edge_accuracy=0.01,
        optimal_bb=True,
        render_edges=True,
        render_shapes=True,
        info=None,
        position=None,
        rotation=None,
        zoom=None,
        timeit=False,
    ):

        self.width = width
        self.height = height
        self.quality = quality
        self.bb_factor = bb_factor
        self.angular_tolerance = angular_tolerance
        self.edge_accuracy = edge_accuracy
        self.optimal_bb = optimal_bb
        self.render_edges = render_edges
        self.render_shapes = render_shapes
        self.info = info
        self.position = position
        self.rotation = rotation
        self.zoom = zoom
        self.timeit = timeit

        self.all_shapes = None

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

        self.camera_position = None
        self.zoom = None

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
        plane = self.clippingPlanes[i]
        plane.normal = self._minus(self.direction())

    def _update(self):
        self.controller.exec_three_obj_method("update")
        pass

    def _fix_camera(self):
        zoom = self.camera.zoom
        # force the camera to zoom correctly. Seems to be a bug.
        self.camera.zoom = zoom + 1e-6
        self.camera.zoom = zoom

    def _reset(self):
        self.camera.rotation, self.controller.target = self.savestate
        self.camera.position = self._add(self.bb.center, self._scale((1, 1, 1)))
        self.camera.zoom = self.camera_initial_zoom
        self._update()

    def _get_group(self, group_index):
        try:
            group = self.pickable_objects
            for j in group_index:
                group = group.children[j]
            return group
        except:
            return None

    def set_axes_visibility(self, value):
        self.axes.set_visibility(value)

    def set_grid_visibility(self, value):
        self.grid.set_visibility(value)

    def set_axes_center(self, value):
        self.grid.set_center(value)
        self.axes.set_center(value)

    def toggle_ortho(self, value):
        self.camera.mode = "orthographic" if value else "perspective"

    def set_transparent(self, value):
        def toggle(group, value):
            for obj in group.children:
                if isinstance(obj, Group):
                    toggle(obj, value)
                else:
                    if isinstance(obj, Mesh):
                        obj.material.transparent = value

        toggle(self.pickable_objects, value)

    def set_black_edges(self, value):
        def toggle(group, value):
            for obj in group.children:
                if isinstance(obj, Group):
                    toggle(obj, value)
                else:
                    if isinstance(obj, LineSegments2):
                        if obj.material.linewidth == 1:
                            obj.material.color = "#000" if value else self.default_edge_color.web_color

        toggle(self.pickable_objects, value)

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

    def set_clipping(self, tab):
        if tab == 0:
            self.renderer.clippingPlanes = []
        else:
            self.renderer.clippingPlanes = self.clippingPlanes

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
            self.clippingPlanes[index].constant = change["new"]

        return f

    # public methods to render the view

    def is_ortho(self):
        return self.camera.mode == "orthographic"

    def is_transparent(self):
        return self.pickable_objects.children[0].material.transparent

    def create(self):
        self.cq_renderer = CadqueryRenderer(
            quality=self.quality,
            angular_tolerance=self.angular_tolerance,
            edge_accuracy=self.edge_accuracy,
            render_edges=self.render_edges,
            render_shapes=self.render_shapes,
            default_mesh_color=self.default_mesh_color,
            default_edge_color=self.default_edge_color,
            timeit=self.timeit,
        )

        # Set up camera
        self.camera = CombinedCamera(
            position=(1.0, 1.0, 1.0),
            width=self.width,
            height=self.height,
            far=100,
            orthoFar=100,
            up=(0.0, 0.0, 1.0),
        )
        # needs to be an extra step to take effect
        self.toggle_ortho(True)

        # Set up scene
        self.scene = Scene(children=[self.camera, AmbientLight(intensity=1.0)])

        # Set up Controllers
        camera_target = (0.0, 0.0, 0.0)
        self.controller = OrbitControls(controlling=self.camera, target=camera_target, target0=camera_target)

        # Create Renderer instance
        self.renderer = Renderer(
            scene=self.scene,
            camera=self.camera,
            controls=[self.controller],
            antialias=True,
            width=self.width,
            height=self.height,
        )
        return self.renderer

    def add_shapes(self, shapes, progress, position=None, rotation=None, zoom=2.5, reset=True):
        def all_shapes(shapes, loc=None):
            loc = shapes["loc"] if loc is None else loc * shapes["loc"]
            result = []
            for shape in shapes["parts"]:
                if shape.get("parts") is None:
                    compounds = [c for c in shape["shape"] if is_compound(c) or is_solid(c) or is_shape(c)]
                    if compounds:
                        if loc is None:
                            result.append(shape["shape"])
                        else:
                            reloc_shape = [Shape(s).moved(loc).wrapped for s in compounds]
                            result.append(reloc_shape)
                else:
                    result += all_shapes(shape, loc)
            return result

        self.shapes = shapes
        self.all_shapes = all_shapes(shapes)

        # Render Shapes
        render_timer = Timer(self.timeit, "| overall render time")
        self.pickable_objects, self.pick_mapping = self.cq_renderer.render(self.shapes, progress)
        render_timer.stop()
        progress.update()

        bb_timer = Timer(self.timeit, "| create bounding box")
        # Get bounding box
        self.bb = self.get_bounding_box(self.all_shapes)
        bb_timer.stop()
        progress.update()

        configure_timer = Timer(self.timeit, "| configure view")
        bb_max = self.bb.max_dist_from_center()
        orbit_radius = 4 * self.bb_factor * bb_max

        # Calculate camera postion
        if position is None and rotation is None:  # no new defaults
            if reset or self.camera_position is None:  # no existing position
                self.camera_position = self._add(self.bb.center, self._scale((1, 1, 1)))
        else:
            position = rotate(position or (1, 1, 1), *(rotation or (0, 0, 0)))
            self.camera_position = self._add(self.bb.center, self._scale(position))

        if reset or self.zoom is None:
            self.zoom = zoom

        # Set up Helpers relative to bounding box
        xy_max = max(abs(self.bb.xmin), abs(self.bb.xmax), abs(self.bb.ymin), abs(self.bb.ymax)) * 1.2
        self.grid = Grid(
            bb_center=self.bb.center,
            maximum=xy_max,
            colorCenterLine="#aaa",
            colorGrid="#ddd",
        )
        self.grid.set_visibility(False)

        self.axes = Axes(bb_center=self.bb.center, length=self.grid.grid.size / 2)
        self.axes.set_visibility(False)

        # Set up the controller relative to bounding box
        self.controller.target = self.bb.center
        self.controller.target0 = self.bb.center

        # Set up lights in every of the 8 corners of the global bounding box
        positions = list(itertools.product(*[(-orbit_radius, orbit_radius)] * 3))
        self.key_lights = [
            DirectionalLight(color="white", position=position, intensity=0.12) for position in positions
        ]

        # Set up Picker
        self.picker = Picker(controlling=self.pickable_objects, event="dblclick")
        self.picker.observe(self.pick)
        self.renderer.controls = self.renderer.controls + [self.picker]

        # Set up camera
        self.update_camera(self.camera_position, self.zoom, orbit_radius)

        # Add objects to scene
        self._fix_camera()
        self.add_to_scene()

        # needs to be done after setup of camera
        self.grid.set_rotation((math.pi / 2.0, 0, 0, "XYZ"))
        self.grid.set_position((0, 0, 0))

        self.renderer.localClippingEnabled = True
        self.renderer.clippingPlanes = []  # turn off when not in clipping view
        self.clippingPlanes = [
            Plane((-1, 0, 0), 0.02 if abs(self.bb.xmax) < 1e-4 else self.bb.xmax * self.bb_factor),
            Plane((0, -1, 0), 0.02 if abs(self.bb.ymax) < 1e-4 else self.bb.ymax * self.bb_factor),
            Plane((0, 0, -1), 0.02 if abs(self.bb.zmax) < 1e-4 else self.bb.zmax * self.bb_factor),
        ]

        self.savestate = (self.camera.rotation, self.controller.target)
        configure_timer.stop()
        progress.update()

        return self.renderer

    def get_bounding_box(self, shapes):
        bb = BoundingBox(shapes, optimal=self.optimal_bb)
        if bb.is_empty():
            # add origin to increase bounding box to also show origin
            bb = BoundingBox([[Vertex.makeVertex(0, 0, 0).wrapped]] + [shape["shape"] for shape in self.shapes])
            if bb.is_empty():
                # looks like only one vertex in origin is to be shown
                bb = BoundingBox(
                    [[Vertex.makeVertex(0.1, 0.1, 0.1).wrapped]] + [shape["shape"] for shape in self.shapes]
                )
        return bb

    def update_camera(self, position, zoom, orbit_radius):
        self.camera.position = position
        self.camera.zoom = zoom
        self.camera.far = 10 * orbit_radius
        self.camera.orthoFar = 10 * orbit_radius
        self._update()

    def add_to_scene(self):
        self.scene.add(self.key_lights)
        self.scene.add(self.axes.axes)
        self.scene.add(self.grid.grid)
        self.scene.add(self.pickable_objects)

    def clear(self):
        # save camera position and zoom in case we want to keep it for the object
        self.zoom = self.camera.zoom
        self.camera_position = self.camera.position

        self.scene.remove(self.key_lights)
        self.scene.remove(self.axes.axes)
        self.scene.remove(self.grid.grid)
        self.scene.remove(self.pickable_objects)

    @property
    def root_group(self):
        return self.pickable_objects
