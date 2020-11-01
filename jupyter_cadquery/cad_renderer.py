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
    )
import time

import numpy as np

from .cad_helpers import CustomMaterial
from .utils import (
    is_vertex,
    is_edge,
    discretize_edge,
    get_edges,
    get_point,
    tessellate,
    explode,
    flatten,
    Color,
)


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


class CadqueryRenderer(object):
    def __init__(
        self,
        quality=0.1,
        angular_tolerance=0.1,
        render_edges=True,
        render_shapes=True,
        edge_accuracy=0.01,
        default_mesh_color=None,
        default_edge_color=None,
        timeit=False,
    ):
        self.quality = quality
        self.angular_tolerance = angular_tolerance
        self.edge_accuracy = edge_accuracy
        self.render_edges = render_edges
        self.render_shapes = render_shapes

        self.default_mesh_color = Color(default_mesh_color or (166, 166, 166))
        self.default_edge_color = Color(default_edge_color or (128, 128, 128))

        self.timeit = timeit

    def _start_timer(self):
        return time.time() if self.timeit else None

    def _stop_timer(self, msg, start):
        if self.timeit:
            print("%20s: %7.2f sec" % (msg, time.time() - start))

    def render_shape(
        self,
        shape_index,
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

        index_str = ".".join([str(x) for x in shape_index])

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
            shp_material = material(
                mesh_color.web_color, transparent=transparent, opacity=opacity
            )

            shape_mesh = Mesh(
                geometry=shape_geometry,
                material=shp_material,
                name="mesh_" + index_str,
            )

            if render_edges:
                edges = get_edges(shape)

            # unset shape_mesh again
            if not render_shapes:
                shape_mesh = None

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
                edge_lines = [LineSegments2(lines, mat, name="edges_" + index_str)]
            else:
                lines = LineSegmentsGeometry(positions=edge_list)
                mat = LineMaterial(linewidth=edge_width, color=edge_color.web_color)
                edge_lines = [LineSegments2(lines, mat, name="edges_" + index_str)]

        self._stop_timer("shape render time", start_render_time)

        return shape_mesh, edge_lines, points

    def _render(self, shapes, current):
        results = {}
        # Render all shapes
        for i, shape in enumerate(shapes):
            index = (*current, i)  # use hashable tuple
            if len(shape) == 0:
                continue
            elif not isinstance(shape, (list, tuple)):
                # Assume that all are edges when first element is an edge
                if is_edge(shape["shape"][0]):
                    shape_mesh, edge_lines, points = self.render_shape(
                        index,
                        edges=shape["shape"],
                        render_edges=True,
                        edge_color=shape["color"],
                        edge_width=3,
                    )
                elif is_vertex(shape["shape"][0]):
                    shape_mesh, edge_lines, points = self.render_shape(
                        index,
                        vertices=shape["shape"],
                        render_edges=False,
                        vertex_color=shape["color"],
                        vertex_width=6,
                    )
                else:
                    # shape has only 1 object
                    shape_mesh, edge_lines, points = self.render_shape(
                        index,
                        shape=shape["shape"][0],
                        render_shapes=self.render_shapes,
                        render_edges=self.render_edges,
                        mesh_color=shape["color"],
                    )
                results[index] = (shape_mesh, edge_lines, points)
            else:
                results[index] = self._render(shape, index)

        return results

    def render(self, shapes):
        start_render_time = self._start_timer()
        results = self._render(shapes, ())
        self._stop_timer("overall render time", start_render_time)
        return results
