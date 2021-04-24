from enum import Enum

import cadquery as cq
import vtk
import pyvista as pv
import numpy as np

import OCP
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
from OCP.IVtkOCC import IVtkOCC_Shape, IVtkOCC_ShapeMesher
from OCP.IVtkVTK import IVtkVTK_ShapeData


class MeshType(Enum):
    # Order of cell blocks from OCP vtk:
    # - Vertices:   1/FreeVertex, 2/Shared_Vertex (will be mixed)
    # - Edges:      0/IsoLine (only when requested), 3/FreeEdge, 4/BoundaryEdge, 5/SharedEdge, 8/SeamEdge (will be mixed)
    # - WireFrames: 0/IsoLine
    # - Faces:      7/ShadedFace

    IsoLine = 0  # Isoline
    FreeVertex = 1  # Free vertex
    SharedVertex = 2  # Shared vertex
    FreeEdge = 3  # Free edge
    BoundaryEdge = 4  # Boundary edge (related to a single face)
    SharedEdge = 5  # Shared edge (related to several faces)
    WireFrameFace = 6  # Wireframe face
    ShadedFace = 7  # Shaded face
    SeamEdge = 8  # Seam edge between faces


class Tessellator:
    def __init__(self):
        self._poly_data = None
        self._points = None

        self._vertices = None
        self._triangle_points = None
        self._triangle_point_normals = None
        self._segments = None
        self._mesh_types = None
        self._subshape_ids = None

        self.num_vertices = self.vertices_offset = None
        self.num_segments = self.segments_offset = None
        self.num_triangles = self.triangles_offset = None

    def _multi_shape(self, shape):
        """
        Check whether a shape or compound has multiple subshapes

        :param shape: An OCP.TopoDS.TopoDS_Compound or OCP.TopoDS.TopoDS_Solid
        :returns: True for multiple subshapes, False else
        """

        count = 0
        e = TopExp_Explorer(shape, TopAbs_SOLID)
        while e.More() and count <= 1:
            count += 1
            e.Next()
        return count > 1

    def compute(
        self,
        shape,
        deviation=0,
        deviation_angle=12 * 3.141593 / 180,
        iso_lines=0,
        parallel=None,
        info=False,
    ):
        """
        Tessellate the shape
        :param shape: An OCP.TopoDS.TopoDS_Compound or OCP.TopoDS.TopoDS_Solid
        :param deviation: Multiplier for the internally calculated deflection value (default=0.0001)
        :param deviation_angle: Angle in degree for the angular deflection (default=12)
        :param iso_lines: Number of iso lines to compute
        :param parallel: Overwrite the default behaviour (parallel computation for 2 subshapes and more)
        """

        if parallel is None:
            parallel = self._multi_shape(shape)

        BRepMesh_IncrementalMesh.SetParallelDefault_s(parallel)

        vtk_shape = IVtkOCC_Shape(shape)
        vtk_data = IVtkVTK_ShapeData()
        vtk_mesher = IVtkOCC_ShapeMesher(
            theDevCoeff=deviation,
            theDevAngle=deviation_angle,
            theNbUIsos=iso_lines,
            theNbVIsos=iso_lines,
        )
        vtk_mesher.Build(vtk_shape, vtk_data)

        if info:
            print(
                f"| | | (deflection ={vtk_mesher.GetDeflection():8.5f}, "
                + f"angular deflection ={vtk_mesher.GetDeviationAngle():8.5f}, parallel = {parallel})"
            )

        alg = vtk.vtkTriangleFilter()
        alg.SetInputData(pv.PolyData(vtk_data.getVtkPolyData()))
        alg.Update()
        self._poly_data = pv.PolyData(alg.GetOutput())

        # Extract only once for all later methods
        self._points = self._poly_data.points

        self.vertex_offset = 0
        self.line_offset = self.num_vertices

        # Transform the triangles and get the minimum point offset
        triangles = self._poly_data.faces.reshape(-1, 4)[:, 1:].ravel().astype("uint32")
        self.triangle_offset = 0  # triangles.min()

        # Ensure triangle index starts with 0
        self.triangles = triangles - self.triangle_offset

        self.num_vertices = self._poly_data.verts.size // 2
        self.num_segments = self._poly_data.lines.size // 3
        self.num_triangles = self._poly_data.faces.size // 4

    @property
    def subshape_ids(self):
        """
        Property returning all subshape ids of the VTK tessellation

        :returns: A 1-dim numpy array containing the subshape id for each point, line, wire and face
        """

        if self._subshape_ids is None:
            self._subshape_ids = self._poly_data.get_array("SUBSHAPE_IDS")
        return self._subshape_ids

    @property
    def mesh_types(self):
        """
        Property returning the mesh types of all points, lines, faces and wires of the VTK tessellation

        All supported mesh types can be seen in class MeshType

        :returns: A 1-dim numpy array containing the mesh type id for each point, line, wire and face
        """

        if self._mesh_types is None:
            self._mesh_types = self._poly_data.get_array("MESH_TYPES")
        return self._mesh_types

    @property
    def vertices(self):
        """
        Property returning all vertices of the VTK tessellation

        Vertices are the points at the beginning of self.points with vertex mesh types "FreeVertex" or "SharedVertex"

        :returns: A (-1,3) shaped numpy float32 array of all vertices
        """

        if self._vertices is None:
            self._vertices = self._points[self._poly_data.verts.reshape(-1, 2)[:, 1]]
        return self._vertices

    @property
    def segments(self):
        """
        Property returning all edges of the VTK tessellation as segments

        This is the preferred format to feed into pythreejs from a performance perspective

        Example:
            { <MeshType.SharedEdge: 5>: array([
                [[-0.5       , -0.47      , -0.47      ],
                 [-0.5       , -0.47      ,  0.47      ]],

                [[-0.5       , -0.47      , -0.47      ],
                 [-0.5       ,  0.47      , -0.47      ]],

                ...,

              ], dtype=float32),
              <MeshType.SeamEdge: 8>: ... }

        :returns: A dict of mesh types with (-1,3,2) shaped numpy float32 arrays of all segments per mesh type
        """

        if self._segments is None:
            segments = self._poly_data.lines.reshape(-1, 3)[:, 1:]
            line_types = self.mesh_types[self.num_vertices : self.num_vertices + self.num_segments]
            typed_segments = np.column_stack((line_types, segments))

            self._segments = {}
            for key in [
                MeshType.FreeEdge,
                MeshType.SharedEdge,
                MeshType.IsoLine,
                MeshType.BoundaryEdge,
                MeshType.SeamEdge,
            ]:
                self._segments[key] = self._points[
                    typed_segments[np.in1d(typed_segments[:, 0], np.asarray([key.value]))][:, 1:]
                ]

        return self._segments

    @property
    def combined_segments(self):
        """
        Property returning all segments of the VTK tessellation as a combined numpy array

        :returns: A (-1,3,2) shaped numpy float32 array of all segments for all line mesh types
        """

        return np.vstack(
            [
                self.segments[mt]
                for mt in [
                    MeshType.FreeEdge,
                    MeshType.SharedEdge,
                    MeshType.IsoLine,
                    MeshType.BoundaryEdge,
                    MeshType.SeamEdge,
                ]
                if self.segments[mt].shape[0] > 0
            ]
        )

    @property
    def triangle_vertices(self):
        """
        Property returning all triangle points of the VTK tessellation

        :returns: A (-1,3) shaped numpy float32 array of all normals
        """

        if self._triangle_points is None:
            # Extract relevant points and point_normals
            self._triangle_points = np.asarray(self._points[self.triangle_offset :], dtype=np.float32)
        return self._triangle_points

    @property
    def triangle_vertex_normals(self):
        """
        Property returning all normals of the VTK tessellation

        :returns: A (-1,3) shaped numpy float32 array of all normals
        """

        if self._triangle_point_normals is None:
            # Note: threejs uses point_normals:
            #       https://threejsfundamentals.org/threejs/lessons/threejs-custom-buffergeometry.html

            # Extract relevant point_normals
            self._triangle_point_normals = np.asarray(
                self._poly_data.point_normals[self.triangle_offset :], dtype=np.float32
            )
        return self._triangle_point_normals
