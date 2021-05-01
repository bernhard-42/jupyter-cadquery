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

from .utils import (
    Color,
    tree_find_single_selector,
    Timer,
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
        default_mesh_color=None,
        default_edge_color=None,
        timeit=False,
    ):
        self.default_mesh_color = Color(default_mesh_color or (166, 166, 166))
        self.default_edge_color = Color(default_edge_color or (128, 128, 128))

        self.timeit = timeit

    def _render_shape(
        self,
        shape=None,
        edges=None,
        vertices=None,
        mesh_color=None,
        edge_color=None,
        vertex_color=None,
        edge_width=1,
        vertex_width=5,
        transparent=False,
        opacity=1.0,
    ):

        edge_list = []
        normals_list = []
        edge_lines = []
        normal_lines = []
        points = None
        shape_mesh = None

        # edge_accuracy = None

        if shape is not None:
            # Compute the tesselation and build mesh
            with Timer(self.timeit, "", "build mesh:", 5):
                edge_list, normals_list = shape["edges"]
                shape_geometry = BufferGeometry(
                    attributes={
                        "position": BufferAttribute(shape["vertices"]),
                        "index": BufferAttribute(shape["triangles"]),
                        "normal": BufferAttribute(shape["normals"]),
                    }
                )

                if mesh_color is None:
                    mesh_color = self.default_mesh_color
                shp_material = material(mesh_color, transparent=transparent, opacity=opacity)
                shape_mesh = IndexedMesh(geometry=shape_geometry, material=shp_material)

        if vertices is not None:
            if vertex_color is None:
                vertex_color = self.default_edge_color  # same as edge_color

            vertices_list = vertices
            attributes = {"position": BufferAttribute(vertices_list, normalized=False)}

            mat = PointsMaterial(color=vertex_color, sizeAttenuation=False, size=vertex_width)
            geom = BufferGeometry(attributes=attributes)
            points = IndexedPoints(geometry=geom, material=mat)

        if edges is not None:
            edge_list = edges

        if len(edge_list) > 0:
            if edge_color is None:
                edge_color = self.default_edge_color

            if isinstance(edge_color, (list, tuple)):
                if len(edge_list) != len(edge_color):
                    print("warning: color list and edge list have different length, using first color for all edges")
                    edge_color = edge_color[0]

            if isinstance(edge_color, (list, tuple)):
                lines = LineSegmentsGeometry(
                    positions=edge_list,
                    colors=[[Color(color).percentage] * 2 for color in edge_color],
                )
                mat = LineMaterial(linewidth=edge_width, vertexColors="VertexColors")
                edge_lines = [IndexedLineSegments2(lines, mat)]
            else:
                lines = LineSegmentsGeometry(positions=edge_list)
                mat = LineMaterial(
                    linewidth=edge_width, color=edge_color.web_color if isinstance(edge_color, Color) else edge_color
                )
                edge_lines = [IndexedLineSegments2(lines, mat)]

        if len(normals_list) > 0:
            lines = LineSegmentsGeometry(positions=normals_list)
            mat = LineMaterial(linewidth=2, color="#9400d3")
            normal_lines = [IndexedLineSegments2(lines, mat)]

        return shape_mesh, edge_lines, normal_lines, points

    def _render(self, shapes, current, prefix=""):

        group = IndexedGroup()
        # we need to ensure unique names to enable Threejs animation later which currently doesn't
        # support directory names
        _, _, name = shapes["name"].rpartition("/")
        group.name = name if prefix == "" else f"{prefix}\\{name}"
        group.ind = current

        if shapes["loc"] is not None:
            group.position, group.quaternion = shapes["loc"]

        # Render all shapes
        for shape in shapes["parts"]:
            if shape.get("parts") is None:
                self._mapping[shape["ind"]] = {"mesh": None, "edges": None}

                if shape["type"] == "edges":
                    options = dict(
                        edges=shape["shape"],
                        edge_color=shape["color"],
                        edge_width=3,
                    )
                elif shape["type"] == "vertices":
                    options = dict(
                        vertices=shape["shape"],
                        vertex_color=shape["color"],
                        vertex_width=6,
                    )
                else:
                    options = dict(
                        shape=shape["shape"],
                        mesh_color=shape["color"],
                    )

                with Timer(self.timeit, shape["name"], "render shape:", 4):
                    shape_mesh, edge_lines, normal_lines, points = self._render_shape(**options)

                ind = len(group.children)
                if shape_mesh is not None:
                    shape_mesh.name = shape["name"]
                    shape_mesh.ind = {"group": (*current, ind), "shape": shape["ind"]}
                    shape_mesh.visible = False
                    group.add(shape_mesh)
                    self._mapping[shape["ind"]]["mesh"] = (*current, ind)
                    ind += 1

                if edge_lines or normal_lines:
                    edge_group = IndexedGroup()
                    edge_group.name = "edges"
                    edge_group.ind = (*current, ind)
                    for j, edge in enumerate(edge_lines + normal_lines):
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
        self.progress = progress
        self._mapping = {}
        rendered_objects = self._render(shapes, (), "")
        return rendered_objects, self._mapping
