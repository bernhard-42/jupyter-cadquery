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

import itertools
import math
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
from .utils import rotate, Color, Timer
from .cad_renderer import CadqueryRenderer, IndexedMesh
from .defaults import get_default


class CadqueryView(object):
    def __init__(
        self,
        width=600,
        height=400,
        info=None,
        timeit=False,
    ):

        self.width = width
        self.height = height
        self.info = info
        self.timeit = timeit

        self.all_shapes = None

        self.pick_color = Color("LightGreen")
        self.default_mesh_color = Color(get_default("default_color"))
        self.default_edge_color = Color(get_default("default_edgecolor"))

        self.camera_distance_factor = 6
        self.camera_initial_zoom = get_default("zoom")

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

        self.position = None
        self.rotation = None
        self.zoom = None

        self.initial_rotation = None
        self.initial_position = None
        self.initial_zoom = None

        self.savestate = ((0, 0, 0, "XYZ"), (0, 0, 0))

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

    def _fix_camera(self):
        zoom = self.camera.zoom
        # force the camera to zoom correctly. Seems to be a bug.
        self.camera.zoom = zoom + 1e-6
        self.camera.zoom = zoom

    def _reset_camera(self):
        self.camera.rotation, self.controller.target = self.savestate
        self.position = self.camera.position = self.initial_position
        self.zoom = self.camera.zoom = self.initial_zoom
        self._update()
        self._fix_camera()

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
                    if type(obj) is IndexedMesh:
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
                            obj.material.color = "#000" if value else self.edge_color

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

    def _filter_shapes(self, shapes):
        return {
            "parts": [
                (
                    {"id": shape["id"], "name": shape["name"], "bb": shape["bb"]}
                    if shape.get("parts") is None
                    else self._filter_shapes(shape)
                )
                for shape in shapes["parts"]
            ]
        }

    def _get_bb(self, shape_index):
        shape = self.bbs
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
                shape = self._get_bb(value.owner.object.ind["shape"])
                bbox = shape["bb"]

                self.info.bb_info(
                    shape["name"],
                    (
                        (bbox["xmin"], bbox["xmax"]),
                        (bbox["ymin"], bbox["ymax"]),
                        (bbox["zmin"], bbox["zmax"]),
                        (
                            (bbox["xmax"] + bbox["xmin"]) / 2,
                            (bbox["ymax"] + bbox["ymin"]) / 2,
                            (bbox["zmax"] + bbox["zmin"]) / 2,
                        ),
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
        self.scene = Scene(
            children=[
                self.camera,
            ]
        )
        if get_default("theme") == "dark":
            self.scene.background = "#212121"

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

    def add_shapes(
        self,
        shapes,
        bb,
        ticks,
        progress,
        bb_factor=None,
        ambient_intensity=None,
        direct_intensity=None,
        default_edgecolor=None,
        position=None,
        rotation=None,
        zoom=None,
        reset_camera=True,
    ):

        preset = lambda key, value: get_default(key) if value is None else value

        bb_factor = preset("bb_factor", bb_factor)
        ticks = preset("ticks", ticks)
        ambient_intensity = preset("ambient_intensity", ambient_intensity)
        direct_intensity = preset("direct_intensity", direct_intensity)
        self.edge_color = Color(preset("default_edgecolor", default_edgecolor)).web_color
        self.cq_renderer.default_edge_color = self.edge_color

        self.bbs = self._filter_shapes(shapes)
        self.bb = bb

        # Render Shapes
        with Timer(self.timeit, "", "overall render", 3):
            self.pickable_objects, self.pick_mapping = self.cq_renderer.render(shapes, progress)

        with Timer(self.timeit, "", "configure view", 3):
            bb_max = self.bb.max_dist_from_center()
            orbit_radius = 4 * bb_factor * bb_max

            if reset_camera:
                self.initial_rotation = self.rotation = preset("rotation", rotation)
                self.initial_position = self.position = self._add(
                    self.bb.center, self._scale(rotate(preset("position", position), *self.rotation))
                )
                self.initial_zoom = self.zoom = preset("zoom", zoom)
            else:
                if rotation is not None:
                    self.rotation = rotation
                if self.rotation is None:
                    self.rotation = get_default("rotation")
                if self.initial_rotation is None:
                    self.initial_rotation = self.rotation

                if position is not None:
                    self.position = position
                if self.position is None:
                    self.position = self._add(
                        self.bb.center, self._scale(rotate(preset("position", position), *self.rotation))
                    )
                if self.initial_position is None:
                    self.initial_position = self.position

                if zoom is not None:
                    self.zoom = zoom
                if self.zoom is None:
                    self.zoom = get_default("zoom")
                if self.initial_zoom is None:
                    self.initial_zoom = self.zoom

            # Set up Helpers relative to bounding box
            xy_max = max(abs(self.bb.xmin), abs(self.bb.xmax), abs(self.bb.ymin), abs(self.bb.ymax)) * 1.2
            self.grid = Grid(
                bb_center=self.bb.center, maximum=xy_max, colorCenterLine="#aaa", colorGrid="#ddd", ticks=ticks
            )
            self.grid.set_visibility(False)

            self.axes = Axes(bb_center=self.bb.center, length=self.grid.grid.size / 2)
            self.axes.set_visibility(False)

            # Set up the controller relative to bounding box
            self.controller.target = self.bb.center
            self.controller.target0 = self.bb.center
            self.controller.panSpeed = (self.bb.xsize + self.bb.ysize + self.bb.zsize) / 300

            # Set up lights in every of the 8 corners of the global bounding box
            positions = list(itertools.product(*[(-orbit_radius, orbit_radius)] * 3))

            self.amb_light = AmbientLight(intensity=ambient_intensity)
            self.key_lights = [
                DirectionalLight(color="white", position=position, intensity=direct_intensity)
                for position in positions
            ]

            # Set up Picker
            self.picker = Picker(controlling=self.pickable_objects, event="dblclick")
            self.picker.observe(self.pick)
            self.renderer.controls = self.renderer.controls + [self.picker]

            # Set up camera
            self.update_camera(self.position, self.zoom, orbit_radius)

            # Add objects to scene
            self._fix_camera()
            self.add_to_scene()

            # needs to be done after setup of camera
            self.grid.set_rotation((math.pi / 2.0, 0, 0, "XYZ"))
            self.grid.set_position((0, 0, 0))

            self.renderer.localClippingEnabled = True
            self.renderer.clippingPlanes = []  # turn off when not in clipping view
            self.clippingPlanes = [
                Plane((-1, 0, 0), 0.02 if abs(self.bb.xmax) < 1e-4 else self.bb.xmax * bb_factor),
                Plane((0, -1, 0), 0.02 if abs(self.bb.ymax) < 1e-4 else self.bb.ymax * bb_factor),
                Plane((0, 0, -1), 0.02 if abs(self.bb.zmax) < 1e-4 else self.bb.zmax * bb_factor),
            ]

            self.savestate = (self.camera.rotation, self.controller.target)

        return self.renderer

    def update_camera(self, position, zoom, orbit_radius):
        self.camera.position = position
        self.camera.zoom = zoom
        self.camera.far = 10 * orbit_radius
        self.camera.orthoFar = 10 * orbit_radius
        self._update()

    def add_to_scene(self):
        self.scene.add(self.amb_light)
        self.scene.add(self.key_lights)
        self.scene.add(self.axes.axes)
        self.scene.add(self.grid.grid)
        self.scene.add(self.pickable_objects)

    def clear(self):
        # save camera position and zoom in case we want to keep it for the object
        self.zoom = self.camera.zoom
        self.position = self.camera.position

        self.scene.remove(self.amb_light)
        self.scene.remove(self.key_lights)
        self.scene.remove(self.axes.axes)
        self.scene.remove(self.grid.grid)
        self.scene.remove(self.pickable_objects)

    @property
    def root_group(self):
        return self.pickable_objects
