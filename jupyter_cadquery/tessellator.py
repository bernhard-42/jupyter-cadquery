from array import array

import numpy as np

from OCP.gp import gp_Vec, gp_Pnt, gp_Trsf
from OCP.BRep import BRep_Tool
from OCP.BRepTools import BRepTools
from OCP.BRepGProp import BRepGProp_Face
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopLoc import TopLoc_Location
from OCP.TopAbs import TopAbs_Orientation
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape, TopTools_IndexedMapOfShape
from OCP.TopExp import TopExp
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCP.TopoDS import TopoDS

from jupyter_cadquery.utils import Timer
from jupyter_cadquery.ocp_utils import get_faces


class Tessellator:
    def __init__(self):
        self.vertices = np.empty((0, 3), dtype="float32")
        self.triangles = np.empty((0,), dtype="uint32")
        self.normals = np.empty((0, 3), dtype="float32")
        self.normals = np.empty((0, 2, 3), dtype="float32")
        self.shape = None

    def compute(
        self, shape, quality: float, angular_tolerance: float = 0.3, tessellate=True, compute_edges=True, debug=False
    ):
        self.shape = shape

        timer_mesh = Timer(debug, "| | | | Incremental mesh")
        # Remove previous mesh data
        BRepTools.Clean_s(shape)
        BRepMesh_IncrementalMesh(shape, quality, False, angular_tolerance, True)
        timer_mesh.stop()

        if tessellate:
            timer_values = Timer(debug, "| | | | nodes, normals")
            self.tessellate()
            timer_values.stop()

        if compute_edges:
            timer_edges = Timer(debug, "| | | | edges")
            self.compute_edges()
            timer_edges.stop()

        # Remove mesh data again
        # BRepTools.Clean_s(shape)

    def tessellate(self):
        self.vertices = array("f")
        self.triangles = array("f")
        self.normals = array("f")

        # global buffers
        p_buf = gp_Pnt()
        n_buf = gp_Vec()
        loc_buf = TopLoc_Location()

        offset = -1

        # every line below is selected for performance. Do not introduce functions to "beautify" the code

        for face in get_faces(self.shape):
            if face.Orientation() == TopAbs_Orientation.TopAbs_REVERSED:
                i1, i2 = 2, 1
            else:
                i1, i2 = 1, 2

            internal = face.Orientation() == TopAbs_Orientation.TopAbs_INTERNAL

            poly = BRep_Tool.Triangulation_s(face, loc_buf)
            if poly is not None:
                Trsf = loc_buf.Transformation()

                # add vertices
                # [node.Transformed(Trsf).Coord() for node in poly.Nodes()] is 5-8 times slower!
                items = poly.Nodes()
                coords = [items.Value(i).Transformed(Trsf).Coord() for i in range(items.Lower(), items.Upper() + 1)]
                flat = []
                for coord in coords:
                    flat += coord
                self.vertices.extend(flat)

                # add triangles
                items = poly.Triangles()
                coords = [items.Value(i).Get() for i in range(items.Lower(), items.Upper() + 1)]
                flat = []
                for coord in coords:
                    flat += (coord[0] + offset, coord[i1] + offset, coord[i2] + offset)
                self.triangles.extend(flat)

                # add normals
                if poly.HasUVNodes():
                    prop = BRepGProp_Face(face)
                    items = poly.UVNodes()

                    def extract(uv0, uv1):
                        prop.Normal(uv0, uv1, p_buf, n_buf)
                        return n_buf.Reverse().Coord() if internal else n_buf.Coord()

                    uvs = [items.Value(i).Coord() for i in range(items.Lower(), items.Upper() + 1)]
                    flat = []
                    for uv1, uv2 in uvs:
                        flat += extract(uv1, uv2)
                    self.normals.extend(flat)

                offset += poly.NbNodes()

    def compute_edges(self):
        self.edges = []

        edge_map = TopTools_IndexedMapOfShape()
        face_map = TopTools_IndexedDataMapOfShapeListOfShape()

        TopExp.MapShapes_s(self.shape, TopAbs_EDGE, edge_map)
        TopExp.MapShapesAndAncestors_s(self.shape, TopAbs_EDGE, TopAbs_FACE, face_map)

        for i in range(1, edge_map.Extent() + 1):
            edge = TopoDS.Edge_s(edge_map.FindKey(i))

            face_list = face_map.FindFromKey(edge)
            if face_list.Extent() == 0:
                print("no faces")
                continue

            loc = TopLoc_Location()
            poly = BRep_Tool.Polygon3D_s(edge, loc)

            if poly is not None:
                print("Polygon3D successful")
                nodes = poly.Nodes()
                transf = loc.Transformation()
                v1 = None
                for j in range(1, poly.NbNodes() + 1):
                    v2 = nodes.Value(j)
                    v2.Transform(transf)
                    v2 = v2.Coord()
                    if v1 is not None:
                        self.edges.append((v1, v2))
                    v1 = v2
            else:
                face = TopoDS.Face_s(face_list.First())
                triang = BRep_Tool.Triangulation_s(face, loc)
                poly = BRep_Tool.PolygonOnTriangulation_s(edge, triang, loc)
                if poly is None:
                    continue

                indices = poly.Nodes()
                nodes = triang.Nodes()
                transf = loc.Transformation()
                v1 = None
                for j in range(indices.Lower(), indices.Upper() + 1):
                    v2 = nodes.Value(indices.Value(j))
                    v2.Transform(transf)
                    v2 = v2.Coord()
                    if v1 is not None:
                        self.edges.append((v1, v2))
                    v1 = v2

    def get_vertices(self):
        return np.asarray(self.vertices, dtype=np.float32).reshape(-1, 3)

    def get_triangles(self):
        return np.asarray(self.triangles, dtype=np.uint32)

    def get_normals(self):
        return np.asarray(self.normals, dtype=np.float32).reshape(-1, 3)

    def get_edges(self):
        return np.asarray(self.edges, dtype=np.float32)