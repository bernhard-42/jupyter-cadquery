# Copyright 2019 Bernhard Walter

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from pythreejs import CombinedCamera, BufferAttribute, BufferGeometry, \
                          Plane, ShaderMaterial, ShaderLib, \
                          Mesh, LineSegmentsGeometry,  LineMaterial,  LineSegments2, \
                          AmbientLight, Scene, OrbitControls, Renderer, Picker, Group, DirectionalLight
import numpy as np

from OCC.Core.Visualization import Tesselator
from OCC.Extend.TopologyUtils import TopologyExplorer, is_edge, discretize_edge

from .tree_view import state_diff
from .cad_helpers import Grid, Axes, BoundingBox


def _decomp(a):
    [item] = a.items()
    return item


def _explode(edge_list):
    return [[edge_list[i], edge_list[i + 1]] for i in range(len(edge_list) - 1)]


def _flatten(nested_list):
    return [y for x in nested_list for y in x]


class CustomMaterial(ShaderMaterial):

    def __init__(self, typ):
        self.types = {'diffuse': 'c', 'uvTransform': 'm3', 'normalScale': 'v2', 'fogColor': 'c', 'emissive': 'c'}

        shader = ShaderLib[typ]

        fragmentShader = """
        uniform float alpha;
        """
        frag_from = "gl_FragColor = vec4( outgoingLight, diffuseColor.a );"
        frag_to = """
            if ( gl_FrontFacing ) {
                gl_FragColor = vec4( outgoingLight, alpha * diffuseColor.a );
            } else {
                gl_FragColor = diffuseColor;
            }"""
        fragmentShader += shader["fragmentShader"].replace(frag_from, frag_to)

        vertexShader = shader["vertexShader"]
        uniforms = shader["uniforms"]
        uniforms["alpha"] = dict(value=0.7)

        super().__init__(uniforms=uniforms, vertexShader=vertexShader, fragmentShader=fragmentShader)
        self.lights = True

    @property
    def color(self):
        return self.uniforms["diffuse"]["value"]

    @color.setter
    def color(self, value):
        self.update("diffuse", value)

    @property
    def alpha(self):
        return self.uniforms["alpha"]["value"]

    @alpha.setter
    def alpha(self, value):
        self.update("alpha", value)

    def update(self, key, value):
        uniforms = dict(**self.uniforms)
        if self.types.get(key) is None:
            uniforms[key] = {'value': value}
        else:
            uniforms[key] = {'type': self.types.get(key), 'value': value}
        self.uniforms = uniforms
        self.needsUpdate = True


class CadqueryView(object):

    def __init__(self,
                 width=600,
                 height=400,
                 render_edges=True,
                 default_mesh_color=None,
                 default_edge_color=None,
                 debug=None):
        self.width = width
        self.height = height
        self.render_edges = render_edges
        self._debug = debug

        self.features = ["mesh", "edges"]

        self.bb = None

        self.default_mesh_color = default_mesh_color or self._format_color(166, 166, 166)
        self.default_edge_color = default_edge_color or self._format_color(128, 128, 128)
        self.pick_color = self._format_color(232, 176, 36)

        self.shapes = []
        self.pickable_objects = Group()
        self.pick_last_mesh = None
        self.pick_last_mesh_color = None
        self.mash_edges_mapping = []

        self.camera = None
        self.axes = None
        self.grid = None
        self.scene = None
        self.controller = None
        self.renderer = None

        self.savestate = None

    def _format_color(self, r, g, b):
        return '#%02x%02x%02x' % (r, g, b)

    def _material(self, color, transparent=False, opacity=1.0):
        material = CustomMaterial("standard")
        material.color = color
        material.clipping = True
        material.side = "DoubleSide"
        material.alpha = 0.7
        material.polygonOffset = False
        material.polygonOffsetFactor = 1
        material.polygonOffsetUnits = 1
        material.transparent=transparent
        material.opacity = opacity
        material.update("metalness", 0.3)
        material.update("roughness", 0.8)
        return material
        # return MeshStandardMaterial(color=color, transparent=transparent, opacity=opacity, side='FrontSide',
        #     polygonOffset = True, polygonOffsetFactor = 1, polygonOffsetUnits = 1)

    def _render_shape(self,
                      shape_index,
                      shape=None,
                      edges=None,
                      mesh_color=None,
                      edge_color=None,
                      render_edges=False,
                      edge_width=1,
                      deflection=0.05,
                      quality=1.0,
                      transparent=False,
                      opacity=1.0):

        edge_list = None
        edge_lines = None

        if shape is not None:
            if mesh_color is None:
                mesh_color = self.default_mesh_color
            if edge_color is None:
                edge_color = self.default_edge_color

            # first, compute the tesselation
            tess = Tesselator(shape)
            tess.Compute(uv_coords=False, compute_edges=render_edges, mesh_quality=quality, parallel=True)

            # get vertices and normals
            vertices_position = tess.GetVerticesPositionAsTuple()

            number_of_triangles = tess.ObjGetTriangleCount()
            number_of_vertices = len(vertices_position)

            # number of vertices should be a multiple of 3
            if number_of_vertices % 3 != 0:
                raise AssertionError("Wrong number of vertices")
            if number_of_triangles * 9 != number_of_vertices:
                raise AssertionError("Wrong number of triangles")

            # then we build the vertex and faces collections as numpy ndarrays
            np_vertices = np.array(vertices_position, dtype='float32')\
                            .reshape(int(number_of_vertices / 3), 3)
            # Note: np_faces is just [0, 1, 2, 3, 4, 5, ...], thus arange is used
            np_faces = np.arange(np_vertices.shape[0], dtype='uint32')

            # compute normals
            np_normals = np.array(tess.GetNormalsAsTuple(), dtype='float32').reshape(-1, 3)
            if np_normals.shape != np_vertices.shape:
                raise AssertionError("Wrong number of normals/shapes")

            # build a BufferGeometry instance
            shape_geometry = BufferGeometry(
                attributes={
                    'position': BufferAttribute(np_vertices),
                    'index': BufferAttribute(np_faces),
                    'normal': BufferAttribute(np_normals)
                })

            shp_material = self._material(mesh_color, transparent=True, opacity=opacity)

            shape_mesh = Mesh(geometry=shape_geometry, material=shp_material, name="mesh_%d" % shape_index)

            if render_edges:
                edge_list = list(
                    map(
                        lambda i_edge:
                        [tess.GetEdgeVertex(i_edge, i_vert) for i_vert in range(tess.ObjEdgeGetVertexCount(i_edge))],
                        range(tess.ObjGetEdgeCount())))

        if edges is not None:
            shape_mesh = None
            edge_list = [discretize_edge(edge, deflection) for edge in edges]

        if edge_list is not None:
            edge_list = _flatten(list(map(_explode, edge_list)))
            lines = LineSegmentsGeometry(positions=edge_list)
            mat = LineMaterial(linewidth=edge_width, color=edge_color)
            edge_lines = LineSegments2(lines, mat, name="edges_%d" % shape_index)

        if shape_mesh is not None or edge_lines is not None:
            index_mapping = {"mesh": None, "edges": None, "shape": shape_index}
            if shape_mesh is not None:
                ind = len(self.pickable_objects.children)
                self.pickable_objects.add(shape_mesh)
                index_mapping["mesh"] = ind
            if edge_lines is not None:
                ind = len(self.pickable_objects.children)
                self.pickable_objects.add(edge_lines)
                index_mapping["edges"] = ind
            self.mash_edges_mapping.append(index_mapping)

    def _scale(self, vec):
        r = self.bb.max * 2.5
        n = np.linalg.norm(vec)
        new_vec = (vec / n * r) + self.bb.center
        return new_vec.tolist()

    def _sub(self, vec1, vec2):
        return list(v1-v2 for v1,v2 in zip(vec1, vec2))

    def _norm(self, vec):
        n = np.linalg.norm(vec)
        return [v/n for v in vec]

    def _minus(self, vec):
        return [-v for v in vec]

    def direction(self):
        return self._norm(self._sub(self.camera.position, self.bb.center))

    def set_plane(self, i):
        plane = self.renderer.clippingPlanes[i]
        plane.normal = self._minus(self.direction())

    def _update(self):
        self.controller.exec_three_obj_method('update')
        pass

    def _reset(self):
        self.camera.rotation, self.controller.target = self.savestate
        self.camera.position = self._scale((1, 1, 1))
        self.camera.zoom = 1.0
        self._update()

    # UI Handler

    def change_view(self, typ, directions):

        def reset(b):
            self._reset()

        def refit(b):
            self.camera.zoom = 1.0
            self._update()

        def change(b):
            self.camera.position = self._scale(directions[typ])
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
        self.camera.mode = 'orthographic' if self.bool_or_new(change) else 'perspective'

    def toggle_transparent(self, change):
        value = self.bool_or_new(change)
        for i in range(0, len(self.pickable_objects.children), 2):
            self.pickable_objects.children[i].material.transparent = value

    def toggle_black_edges(self, change):
        value = self.bool_or_new(change)
        for i in range(1, len(self.pickable_objects.children), 2):
            if value:
                self.pickable_objects.children[i].material.color = "#000"
            else:
                self.pickable_objects.children[i].material.color = self.default_edge_color

    def set_visibility(self, ind, i, state):
        feature = self.features[i]
        group_index = self.mash_edges_mapping[ind][feature]
        if group_index is not None:
            self.pickable_objects.children[group_index].visible = (state == 1)

    def change_visibility(self, mapping):

        def f(states):
            diffs = state_diff(states.get("old"), states.get("new"))
            for diff in diffs:
                obj, val = _decomp(diff)
                self.set_visibility(mapping[obj], val["icon"], val["new"])

        return f

    def pick(self, value):
        if self.pick_last_mesh != value.owner.object:
            # Reset
            if value.owner.object is None or self.pick_last_mesh is not None:
                self.pick_last_mesh.material.color = self.pick_last_mesh_color
                self.pick_last_mesh = None
                self.pick_last_mesh_color = None

            # Change highlighted mesh
            if isinstance(value.owner.object, Mesh):
                _, ind = value.owner.object.name.split("_")
                shape = self.shapes[int(ind)]
                bbox = BoundingBox([shape["shape"]])
                self._debug("\n%s:" % shape["name"])
                self._debug(" x~[%5.2f,%5.2f] ~ %5.2f" % (bbox.xmin, bbox.xmax, bbox.xsize))
                self._debug(" y~[%5.2f,%5.2f] ~ %5.2f" % (bbox.ymin, bbox.ymax, bbox.ysize))
                self._debug(" z~[%5.2f,%5.2f] ~ %5.2f" % (bbox.zmin, bbox.zmax, bbox.zsize))
                self.pick_last_mesh = value.owner.object
                self.pick_last_mesh_color = self.pick_last_mesh.material.color
                self.pick_last_mesh.material.color = self.pick_color

    def clip(self, index):

        def f(change):
            self.renderer.clippingPlanes[index].constant = change["new"]

        return f

    # public methods to add shapes and render the view

    def add_shape(self, name, shape, color="#ff0000"):
        self.shapes.append({"name": name, "shape": shape, "color": color})

    def render(self):
        # Render all shapes
        for i, shape in enumerate(self.shapes):
            if is_edge(shape["shape"].toOCC()):
                # TODO Check it is safe to omit these edges
                # The edges with one vertex are CurveOnSurface
                # curve_adaptator = BRepAdaptor_Curve(edge)
                # curve_adaptator.IsCurveOnSurface() == True
                edges = [
                    edge.wrapped
                    for edge in shape["shape"].objects
                    if TopologyExplorer(edge.wrapped).number_of_vertices() >= 2
                ]
                self._render_shape(i, edges=edges, render_edges=True, edge_color=shape["color"], edge_width=3)
            else:
                self._render_shape(i, shape=shape["shape"].toOCC(), render_edges=True, mesh_color=shape["color"])

        # Get the overall bounding box
        self.bb = BoundingBox([shape["shape"] for shape in self.shapes])
        bb_max = max((abs(self.bb.xmin), abs(self.bb.xmax), abs(self.bb.ymin), abs(self.bb.ymax), abs(self.bb.zmin),
                      abs(self.bb.zmax)))

        # Set up camera
        camera_target = self.bb.center
        camera_position = self._scale([1, 1, 1])

        self.camera = CombinedCamera(
            position=camera_position, width=self.width, height=self.height, far=10 * bb_max, orthoFar=10 * bb_max)
        self.camera.up = (0.0, 0.0, 1.0)
        self.camera.lookAt(camera_target)
        self.camera.mode = 'orthographic'
        self.camera.position = camera_position

        # Set up lights
        key_lights = [
            DirectionalLight(color='white', position=position, intensity=0.12) for position in [
                (bb_max, bb_max, bb_max),
                (-bb_max, bb_max, bb_max),
                (bb_max, -bb_max, bb_max),
                (bb_max, bb_max, -bb_max),
                (-bb_max, -bb_max, bb_max),
                (-bb_max, bb_max, -bb_max),
                (bb_max, -bb_max, -bb_max),
                (-bb_max, -bb_max, bb_max),
            ]
        ]
        ambient_light = AmbientLight(intensity=1.0)

        # Set up Helpers
        self.axes = Axes(bb_center=self.bb.center, length=bb_max)
        self.grid = Grid(bb_center=self.bb.center, maximum=bb_max, colorCenterLine='#aaa', colorGrid='#ddd')

        # Set up scene
        environment = self.axes.axes + key_lights + [ambient_light, self.grid.grid, self.camera]
        self.scene = Scene(children=environment + [self.pickable_objects])

        # Set up Controllers
        self.controller = OrbitControls(controlling=self.camera, target=camera_target)

        self.picker = Picker(controlling=self.pickable_objects, event='dblclick')
        self.picker.observe(self.pick)

        # Create Renderer instance
        self.renderer = Renderer(
            scene=self.scene,
            camera=self.camera,
            controls=[self.controller, self.picker],
            antialias=True,
            width=self.width,
            height=self.height)

        self.renderer.localClippingEnabled = True
        self.renderer.clippingPlanes = [
            Plane((1, 0, 0), self.grid.size / 2),
            Plane((0, 1, 0), self.grid.size / 2),
            Plane((0, 0, 1), self.grid.size / 2)
        ]

        # needs to be done after setup of camera
        self.grid.set_rotation((math.pi / 2.0, 0, 0, "XYZ"))
        self.grid.set_position((0, 0, 0))

        self.savestate = (self.camera.rotation, self.controller.target)

        # Workaround: Zoom forth and back to update frame. Sometimes necessary :(
        self.camera.zoom = 1.01
        self._update()
        self.camera.zoom = 1.0
        self._update()

        return self.renderer
