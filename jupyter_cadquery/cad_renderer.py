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
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from pythreejs import (
        BufferAttribute,
        BufferGeometry,
        Mesh,
        LineSegmentsGeometry,
        LineMaterial,
        LineSegments2,
        Points,
        PointsMaterial,
        Group,
    )

from .cad_helpers import CustomMaterial
from .tessellator import Tessellator
from .ocp_utils import (
    is_vertex,
    is_edge,
    discretize_edge,
    get_edges,
    get_point,
    tq,
)
from .utils import (
    Color,
    tree_find_single_selector,
    Timer,
)

from cadquery.occ_impl.shapes import Compound
from .ocp_utils import BoundingBox


class RenderCache:
    def __init__(self):
        self.objects = {}
        self.use_cache = True

    def reset_cache(self):
        self.objects = {}

    def toggle_cache(self):
        self.use_cache = not self.use_cache
        print(f"Render cache turned {'ON' if self.use_cache else 'OFF'}")

    def tessellate(
        self, compound, quality=None, angular_tolerance=None, render_shapes=True, render_edges=True, debug=False
    ):

        hash = id(compound)  # use python id instead of compound.HashCode(HASH_CODE_MAX)
        if self.objects.get(hash) is None:
            tess = Tessellator()
            tess.compute(
                compound,
                quality=quality,
                angular_tolerance=angular_tolerance,
                tessellate=render_shapes,
                compute_edges=render_edges,
                debug=debug,
            )
            np_vertices = tess.get_vertices()
            np_triangles = tess.get_triangles()
            np_normals = tess.get_normals()
            np_edges = tess.get_edges() if render_edges else None

            if np_normals.shape != np_vertices.shape:
                raise AssertionError("Wrong number of normals/shapes")

            shape_geometry = BufferGeometry(
                attributes={
                    "position": BufferAttribute(np_vertices),
                    "index": BufferAttribute(np_triangles),
                    "normal": BufferAttribute(np_normals),
                }
            )
            if debug:
                print(f"| | | (Caching {hash})")
            self.objects[hash] = (shape_geometry, np_edges)
        else:
            if debug:
                print(f"| | | (Taking {hash} from cache)")
        return self.objects[hash]


RENDER_CACHE = RenderCache()
reset_cache = RENDER_CACHE.reset_cache
toggle_cache = RENDER_CACHE.toggle_cache


def material(color, transparent=False, opacity=1.0):
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


class IndexedGroup(Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ind = None

    def dump(self, ind=""):
        print(ind, self.name, self.ind)
        for c in self.children:
            if isinstance(c, IndexedGroup):
                c.dump(ind + "    ")
            else:
                print(ind + "  ", c)

    def find_group(self, query):
        return tree_find_single_selector(self, query)


class IndexedMesh(Mesh):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ind = None

    def __repr__(self):
        return (
            f"IndexedMesh(name='{self.name}', ind={self.ind}, position={self.position}, quaternion={self.quaternion})"
        )


class IndexedPoints(Points):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ind = None

    def __repr__(self):
        return f"IndexedPoints(name='{self.name}', ind={self.ind}, position={self.position}, quaternion={self.quaternion})"


class IndexedLineSegments2(LineSegments2):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ind = None

    def __repr__(self):
        return f"IndexedLineSegments2(name='{self.name}', ind={self.ind}, position={self.position}, quaternion={self.quaternion})"


class CadqueryRenderer(object):
    def __init__(
        self,
        quality=None,
        deviation=0.5,
        angular_tolerance=0.3,
        render_edges=True,
        render_shapes=True,
        edge_accuracy=None,
        default_mesh_color=None,
        default_edge_color=None,
        timeit=False,
    ):
        self.quality = quality
        self.angular_tolerance = angular_tolerance
        self.edge_accuracy = edge_accuracy
        self.render_edges = render_edges
        self.render_shapes = render_shapes
        self.deviation = deviation
        self.default_mesh_color = Color(default_mesh_color or (166, 166, 166))
        self.default_edge_color = Color(default_edge_color or (128, 128, 128))

        self.timeit = timeit

    def compute_quality(self, shape):
        # based on non-optimal bounding box without mesh
        bb = BoundingBox([[shape]], optimal=False)
        return (bb.xsize + bb.ysize + bb.zsize) / 300 * self.deviation

    def render_shape(
        self,
        shape=None,
        edges=None,
        vertices=None,
        mesh_color=None,
        edge_color=None,
        vertex_color=None,
        render_edges=True,
        render_shapes=True,
        edge_width=1,
        vertex_width=5,
        transparent=False,
        opacity=1.0,
    ):

        edge_list = None
        edge_lines = None
        points = None
        shape_mesh = None

        edge_accuracy = None

        render_timer = Timer(self.timeit, "| | shape render time")
        if shape is not None:
            quality = self.quality if self.quality is not None else self.compute_quality(shape)
            edge_accuracy = self.edge_accuracy if self.edge_accuracy is not None else (quality * 0.02 * self.deviation)
            if self.timeit:
                print(f"| | | (quality: {quality:8.6f}, angular_tolerance: {self.angular_tolerance:8.6f})")

            # Compute the tesselation and build mesh
            tesselation_timer = Timer(self.timeit, "| | | build mesh time")
            shape_geometry, edge_list = RENDER_CACHE.tessellate(
                shape,
                quality=quality,
                angular_tolerance=self.angular_tolerance,
                render_shapes=render_shapes,
                render_edges=render_edges,
                debug=self.timeit,
            )
            shape_mesh = None
            if render_shapes:
                if mesh_color is None:
                    mesh_color = self.default_mesh_color
                shp_material = material(mesh_color.web_color, transparent=transparent, opacity=opacity)
                # Do not cache building the mesh. Might lead to unpredictable results
                shape_mesh = IndexedMesh(geometry=shape_geometry, material=shp_material)

            tesselation_timer.stop()

        if vertices is not None:
            if vertex_color is None:
                vertex_color = self.default_edge_color  # same as edge_color

            vertices_list = []
            for vertex in vertices:
                vertices_list.append(get_point(vertex))
            vertices_list = np.array(vertices_list, dtype=np.float32)

            attributes = {"position": BufferAttribute(vertices_list, normalized=False)}

            mat = PointsMaterial(color=vertex_color.web_color, sizeAttenuation=False, size=vertex_width)
            geom = BufferGeometry(attributes=attributes)
            points = IndexedPoints(geometry=geom, material=mat)

        if edges is not None:
            if edge_accuracy is None:  # take over from shape meshing
                edge_accuracy = self.edge_accuracy if self.edge_accuracy is not None else 0.01 * self.deviation

            discretize_timer = Timer(self.timeit, "| | | discretize time")
            edge_list = []
            for edge in edges:
                edge_list += discretize_edge(edge, edge_accuracy)
            edge_list = np.asarray(edge_list, dtype="float32")
            discretize_timer.stop()
            if self.timeit:
                print(f"| | | (edge_accuracy: {edge_accuracy:8.6f})")

        if edge_list is not None:
            if edge_color is None:
                edge_color = self.default_edge_color

            if isinstance(edge_color, (list, tuple)):
                if len(edge_list) != len(edge_color):
                    print("warning: color list and edge list have different length, using first color for all edges")
                    edge_color = edge_color[0]

            if isinstance(edge_color, (list, tuple)):
                lines = LineSegmentsGeometry(
                    positions=edge_list,
                    colors=[[color.percentage] * 2 for color in edge_color],
                )
                mat = LineMaterial(linewidth=edge_width, vertexColors="VertexColors")
                edge_lines = [IndexedLineSegments2(lines, mat)]
            else:
                lines = LineSegmentsGeometry(positions=edge_list)
                mat = LineMaterial(linewidth=edge_width, color=edge_color.web_color)
                edge_lines = [IndexedLineSegments2(lines, mat)]

        render_timer.stop()

        return shape_mesh, edge_lines, points

    def _render(self, shapes, current, prefix=""):

        group = IndexedGroup()
        # we need to ensure unique names to enable Threejs animation later which currently doesn't
        # support directory names
        _, _, name = shapes["name"].rpartition("/")
        group.name = name if prefix == "" else f"{prefix}\\{name}"
        group.ind = current

        if self.timeit:
            print(f"| | Object: {name}")

        if shapes["loc"] is not None:
            group.position, group.quaternion = tq(shapes["loc"])

        # Render all shapes
        for shape in shapes["parts"]:
            if shape.get("parts") is None:
                self._mapping[shape["ind"]] = {"mesh": None, "edges": None}

                # Assume that all are edges when first element is an edge
                if is_edge(shape["shape"][0]):
                    options = dict(
                        edges=shape["shape"],
                        edge_color=shape["color"],
                        edge_width=3,
                        render_edges=True,
                    )
                elif is_vertex(shape["shape"][0]):
                    options = dict(
                        vertices=shape["shape"],
                        vertex_color=shape["color"],
                        vertex_width=6,
                        render_edges=False,
                    )
                else:
                    # Creatge a Compound out of all shapes
                    options = dict(
                        shape=Compound._makeCompound(shape["shape"]) if len(shape["shape"]) > 1 else shape["shape"][0],
                        mesh_color=shape["color"],
                        render_shapes=self.render_shapes,
                        render_edges=self.render_edges,
                    )

                shape_mesh, edge_lines, points = self.render_shape(**options)

                ind = len(group.children)
                if shape_mesh is not None:
                    shape_mesh.name = shape["name"]
                    shape_mesh.ind = {"group": (*current, ind), "shape": shape["ind"]}
                    shape_mesh.visible = False
                    group.add(shape_mesh)
                    self._mapping[shape["ind"]]["mesh"] = (*current, ind)
                    ind += 1

                if edge_lines is not None:
                    edge_group = IndexedGroup()
                    edge_group.name = "edges"
                    edge_group.ind = (*current, ind)
                    for j, edge in enumerate(edge_lines):
                        edge.name = shape["name"]
                        edge.ind = {"group": (*current, ind, j), "shape": shape["ind"]}
                        edge_group.add(edge)
                    group.add(edge_group)
                    edge_group.visible = False
                    self._mapping[shape["ind"]]["edges"] = (*current, ind)
                    ind += 1

                if points is not None:
                    points.name = shape["name"]
                    points.ind = {"group": (*current, ind), "shape": shape["ind"]}
                    group.add(points)
                    self._mapping[shape["ind"]]["mesh"] = (*current, ind)
                    ind += 1

                self.progress.update()
            else:
                ind = len(group.children)
                group.add(self._render(shape, (*current, ind), group.name))

        return group

    def render(self, shapes, progress):
        # Since ids are only unique during lifetime of the objects reset the cache for
        # each call. The cache will only speed up assemblies with multiple same parts
        RENDER_CACHE.reset_cache()
        self.progress = progress
        self._mapping = {}
        rendered_objects = self._render(shapes, (), "")
        return rendered_objects, self._mapping
