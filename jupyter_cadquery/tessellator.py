from enum import Enum

import numpy as np

import vtk
from vtk.util.numpy_support import vtk_to_numpy

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
        self._vtk_mesher = None
        self._dataset = None
        self._points = None
        self._vertices = None
        self._typed_segments = None

        self.segments = None
        self.triangles = None
        self.vertices = None
        self.normals = None

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
        deviation=0.0001,
        deviation_angle=12 * 3.141593 / 180,
        iso_lines=0,
        parallel=None,
    ):
        """
        Tessellate the shape
        :param shape: An OCP.TopoDS.TopoDS_Compound or OCP.TopoDS.TopoDS_Solid
        :param deviation: Multiplier for the internally calculated deflection value (default=0.0001)
        :param deviation_angle: Angle in degree for the angular deflection (default=12)
        :param iso_lines: Number of iso lines to compute
        :param parallel: Overwrite the default behaviour (parallel computation for 2 subshapes and more)
        """
        self.parallel = parallel or self._multi_shape(shape)
        BRepMesh_IncrementalMesh.SetParallelDefault_s(self.parallel)

        vtk_shape = IVtkOCC_Shape(shape)
        vtk_data = IVtkVTK_ShapeData()
        self._vtk_mesher = IVtkOCC_ShapeMesher(
            theDevCoeff=deviation, theDevAngle=deviation_angle, theNbUIsos=iso_lines, theNbVIsos=iso_lines
        )
        self._vtk_mesher.Build(vtk_shape, vtk_data)
        dataset = vtk_data.getVtkPolyData()

        # Split lines into segments
        t_filter = vtk.vtkTriangleFilter()
        t_filter.SetInputData(dataset)
        t_filter.Update()
        dataset = t_filter.GetOutput()

        # Calculate point normals
        n_filter = vtk.vtkPolyDataNormals()
        n_filter.SetInputData(dataset)
        n_filter.Update()
        dataset = self._dataset = n_filter.GetOutput()

        self._points = vtk_to_numpy(dataset.GetPoints().GetData())

        self.triangles = vtk_to_numpy(dataset.GetPolys().GetData()).reshape(-1, 4)[:, 1:].ravel().astype("uint32")
        triangle_offset = np.min(self.triangles)
        self.triangles = self.triangles - triangle_offset  # Ensure triangles start with 0

        self.vertices = np.asarray(self._points[triangle_offset:], dtype=np.float32)

        self.normals = np.asarray(
            vtk_to_numpy(dataset.GetPointData().GetAbstractArray("Normals"))[triangle_offset:], dtype=np.float32
        )

        self.segments = self._points[vtk_to_numpy(dataset.GetLines().GetData()).reshape(-1, 3)[:, 1:]]

    @property
    def deflection(self):
        return self._vtk_mesher.GetDeflection()

    @property
    def deviation_angle(self):
        return self._vtk_mesher.GetDeviationAngle()

    @property
    def typed_segments(self):
        """
        Property returning all edges of the VTK tessellation as segments

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

        if self._typed_segments is None:
            mesh_types = vtk_to_numpy(self._dataset.GetCellData().GetAbstractArray("MESH_TYPES"))
            line_types = mesh_types[self._vertices.shape[0] : self._vertices.shape[0] + self.segments.shape[0]]
            typed_segments = np.column_stack((line_types, self.segments))

            self._segments = {}
            for key in [
                MeshType.FreeEdge,
                MeshType.SharedEdge,
                MeshType.IsoLine,
                MeshType.BoundaryEdge,
                MeshType.SeamEdge,
            ]:
                self.segments[key] = self._points[
                    typed_segments[np.in1d(typed_segments[:, 0], np.asarray([key.value]))][:, 1:]
                ]

        return self._typed_segments
