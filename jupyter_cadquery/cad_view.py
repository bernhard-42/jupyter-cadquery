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
import numpy as np

import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from pythreejs import (
        CombinedCamera,
        BufferAttribute,
        BufferGeometry,
        Plane,
        Mesh,
        LineSegmentsGeometry,
        LineMaterial,
        LineSegments2,
        AmbientLight,
        DirectionalLight,
        Scene,
        OrbitControls,
        Renderer,
        Picker,
        Group,
        Points,
        PointsMaterial,
    )
import time

import numpy as np

from .widgets import state_diff
from .cad_helpers import Grid, Axes, CustomMaterial
from .utils import (
    is_vertex,
    is_edge,
    is_compound,
    discretize_edge,
    get_edges,
    get_point,
    tessellate,
    explode,
    flatten,
    rotate,
    BoundingBox,
    Color,
)


class CadqueryView(object):
    def __init__(
        self,
        width=600,
        height=400,
        quality=0.1,
        angular_tolerance=0.1,
        edge_accuracy=0.01,
        render_edges=True,
        default_mesh_color=None,
        default_edge_color=None,
        info=None,
        timeit=False,
    ):

        self.width = width
        self.height = height
        self.quality = quality
        self.angular_tolerance = angular_tolerance
        self.edge_accuracy = edge_accuracy
        self.render_edges = render_edges
        self.info = info
        self.timeit = timeit

        self.camera_distance_factor = 6
        self.camera_initial_zoom = 2.5

        self.features = ["mesh", "edges"]

        self.bb = None

        self.default_mesh_color = Color(default_mesh_color or (166, 166, 166))
        self.default_edge_color = Color(default_edge_color or (128, 128, 128))
        self.pick_color = Color((232, 176, 36))

        self.shapes = []
        self.pickable_objects = Group()
        self.pick_last_mesh = None
        self.pick_last_mesh_color = None
        self.pick_mapping = []

        self.camera = None
        self.axes = None
        self.grid = None
        self.scene = None
        self.controller = None
        self.renderer = None

        self.savestate = None
        self.tesselated_shapes = {}

    def _start_timer(self):
        return time.time() if self.timeit else None

    def _stop_timer(self, msg, start):
        if self.timeit:
            print("%20s: %7.2f sec" % (msg, time.time() - start))

    def _material(self, color, transparent=False, opacity=1.0):
        material = CustomMaterial("standard")
        material.color = color
        material.clipping = True
        material.side = "DoubleSide"
        material.alpha = 0.7
        material.polygonOffset = True
        material.polygonOffsetFactor = 1
        material.polygonOffsetUnits = 1
        material.transparent = transparent
        material.opacity = opacity
        material.update("metalness", 0.3)
        material.update("roughness", 0.8)
        return material

    def _render_shape(
        self,
        shape_index,
        shape=None,
        edges=None,
        vertices=None,
        mesh_color=None,
        edge_color=None,
        vertex_color=None,
        render_edges=False,
        edge_width=1,
        vertex_width=5,
        transparent=False,
        opacity=1.0,
    ):

        edge_list = None
        edge_lines = None
        points = None
        shape_mesh = None

        start_render_time = self._start_timer()
        if shape is not None:
            if mesh_color is None:
                mesh_color = self.default_mesh_color
            if edge_color is None:
                edge_color = self.default_edge_color
            if vertex_color is None:
                vertex_color = self.default_edge_color  # same as edge_color

            # Compute the tesselation
            start_tesselation_time = self._start_timer()

            np_vertices, np_triangles, np_normals = tessellate(
                shape, self.quality, self.angular_tolerance
            )

            if np_normals.shape != np_vertices.shape:
                raise AssertionError("Wrong number of normals/shapes")

            self._stop_timer("tesselation time", start_tesselation_time)

            # build a BufferGeometry instance
            shape_geometry = BufferGeometry(
                attributes={
                    "position": BufferAttribute(np_vertices),
                    "index": BufferAttribute(np_triangles.ravel()),
                    "normal": BufferAttribute(np_normals),
                }
            )
            shp_material = self._material(
                mesh_color.web_color, transparent=transparent, opacity=opacity
            )

            shape_mesh = Mesh(
                geometry=shape_geometry,
                material=shp_material,
                name="mesh_%d" % shape_index,
            )

            if render_edges:
                edges = get_edges(shape)

        if vertices is not None:
            vertices_list = []
            for vertex in vertices:
                vertices_list.append(get_point(vertex))
            vertices_list = np.array(vertices_list, dtype=np.float32)

            attributes = {"position": BufferAttribute(vertices_list, normalized=False)}

            mat = PointsMaterial(
                color=vertex_color.web_color, sizeAttenuation=False, size=vertex_width
            )
            geom = BufferGeometry(attributes=attributes)
            points = Points(geometry=geom, material=mat)

        if edges is not None:
            start_discretize_time = self._start_timer()
            edge_list = [discretize_edge(edge, self.edge_accuracy) for edge in edges]
            self._stop_timer("discretize time", start_discretize_time)

        if edge_list is not None:
            edge_list = flatten(list(map(explode, edge_list)))
            if isinstance(edge_color, (list, tuple)):
                if len(edge_list) != len(edge_color):
                    print(
                        "warning: color list and edge list have different length, using first color for all edges"
                    )
                    edge_color = edge_color[0]

            if isinstance(edge_color, (list, tuple)):

                lines = LineSegmentsGeometry(
                    positions=edge_list,
                    colors=[[color.percentage] * 2 for color in edge_color],
                )
                mat = LineMaterial(linewidth=edge_width, vertexColors="VertexColors")
                edge_lines = [LineSegments2(lines, mat, name="edges_%d" % shape_index)]
            else:
                lines = LineSegmentsGeometry(positions=edge_list)
                mat = LineMaterial(linewidth=edge_width, color=edge_color.web_color)
                edge_lines = [LineSegments2(lines, mat, name="edges_%d" % shape_index)]

        self._stop_timer("shape render time", start_render_time)

        return shape_mesh, edge_lines, points

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
        value = self.bool_or_new(change)
        for obj in self.pickable_objects.children:
            if isinstance(obj, Mesh):
                obj.material.transparent = value

    def toggle_black_edges(self, change):
        value = self.bool_or_new(change)
        for obj in self.pickable_objects.children:
            if isinstance(obj, LineSegments2):
                _, ind = obj.name.split("_")
                ind = int(ind)
                if is_compound(self.shapes[ind]["shape"][0]):
                    obj.material.color = (
                        "#000" if value else self.default_edge_color.web_color
                    )

    def set_visibility(self, ind, i, state):
        feature = self.features[i]
        group_index = self.pick_mapping[ind][feature]
        if group_index is not None:
            self.pickable_objects.children[group_index].visible = state == 1

    def change_visibility(self, mapping):
        def f(states):
            diffs = state_diff(states.get("old"), states.get("new"))
            for diff in diffs:
                [[obj, val]] = diff.items()
                self.set_visibility(mapping[obj], val["icon"], val["new"])

        return f

    def pick(self, value):
        if self.pick_last_mesh != value.owner.object:
            # Reset
            if value.owner.object is None or self.pick_last_mesh is not None:
                self.pick_last_mesh.material.color = self.pick_last_mesh_color.web_color
                self.pick_last_mesh = None
                self.pick_last_mesh_color = None

            # Change highlighted mesh
            if isinstance(value.owner.object, Mesh):
                _, ind = value.owner.object.name.split("_")
                shape = self.shapes[int(ind)]
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
                self.pick_last_mesh = value.owner.object
                self.pick_last_mesh_color = self.pick_last_mesh.material.color.web_color
                self.pick_last_mesh.material.color = self.pick_color.web_color

    def clip(self, index):
        def f(change):
            self.renderer.clippingPlanes[index].constant = change["new"]

        return f

    # public methods to add shapes and render the view

    def add_shape(self, name, shape, color):
        self.shapes.append({"name": name, "shape": shape, "color": color})

    def is_ortho(self):
        return self.camera.mode == "orthographic"

    def is_transparent(self):
        return self.pickable_objects.children[0].material.transparent

    def render(self, position=None, rotation=None, zoom=2.5):
        def _render(i, shape):
            # Assume that all are edges when first element is an edge
            if is_edge(shape["shape"][0]):
                shape_mesh, edge_lines, points = self._render_shape(
                    i,
                    edges=shape["shape"],
                    render_edges=True,
                    edge_color=shape["color"],
                    edge_width=3,
                )
            elif is_vertex(shape["shape"][0]):
                shape_mesh, edge_lines, points = self._render_shape(
                    i,
                    vertices=shape["shape"],
                    render_edges=False,
                    vertex_color=shape["color"],
                    vertex_width=6,
                )
            else:
                # shape has only 1 object, hence first=True
                shape_mesh, edge_lines, points = self._render_shape(
                    i,
                    shape=shape["shape"][0],
                    render_edges=True,
                    mesh_color=shape["color"],
                )
            results[i] = (shape_mesh, edge_lines, points)

        self.camera_initial_zoom = zoom
        results = {}

        start_render_time = self._start_timer()
        # Render all shapes
        for i, shape in enumerate(self.shapes):
            _render(i, shape)

        for i, objects in results.items():
            (shape_mesh, edge_lines, points) = objects
            if shape_mesh is not None or edge_lines is not None or points is not None:
                index_mapping = {"mesh": None, "edges": None, "shape": i}
                if shape_mesh is not None:
                    ind = len(self.pickable_objects.children)
                    self.pickable_objects.add(shape_mesh)
                    index_mapping["mesh"] = ind
                if edge_lines is not None:
                    ind = len(self.pickable_objects.children)
                    self.pickable_objects.add(edge_lines)
                    index_mapping["edges"] = ind
                if points is not None:
                    ind = len(self.pickable_objects.children)
                    self.pickable_objects.add(points)
                    index_mapping["mesh"] = ind
                self.pick_mapping.append(index_mapping)

        # Get the overall bounding box
        self.bb = BoundingBox([shape["shape"] for shape in self.shapes])

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

        self._stop_timer("overall render time", start_render_time)

        return self.renderer
