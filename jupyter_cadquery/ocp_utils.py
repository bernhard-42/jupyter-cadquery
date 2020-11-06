import itertools
from functools import reduce
import numpy as np

from OCP.gp import gp_Vec, gp_Pnt

from OCP.Bnd import Bnd_Box
from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp_Face
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepTools import BRepTools

from OCP.GCPnts import (
    GCPnts_QuasiUniformDeflection,
    GCPnts_UniformAbscissa,
    GCPnts_UniformDeflection,
)

from OCP.TopAbs import (
    TopAbs_ShapeEnum,
    TopAbs_Orientation,
    TopAbs_VERTEX,
    TopAbs_EDGE,
    TopAbs_FACE,
)
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS, TopoDS_Shape, TopoDS_Compound
from OCP.TopAbs import TopAbs_FACE

from OCP.TopExp import TopExp_Explorer

from OCP.TopLoc import TopLoc_Location

from OCP.StlAPI import StlAPI_Writer

from cadquery.occ_impl.shapes import downcast
from .utils import distance

# Nested bounding box


class BoundingBox(object):
    def __init__(self, objects, tol=1e-5):
        self.tol = tol
        bbox = reduce(self._opt, [self.bbox(obj) for obj in objects])
        self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax = bbox
        self.xsize = self.xmax - self.xmin
        self.ysize = self.ymax - self.ymin
        self.zsize = self.zmax - self.zmin
        self.center = (
            self.xmin + self.xsize / 2.0,
            self.ymin + self.ysize / 2.0,
            self.zmin + self.zsize / 2.0,
        )
        self.max = reduce(lambda a, b: max(abs(a), abs(b)), bbox)

    def max_dist_from_center(self):
        return max(
            [
                distance(self.center, v)
                for v in itertools.product(
                    (self.xmin, self.xmax),
                    (self.ymin, self.ymax),
                    (self.zmin, self.zmax),
                )
            ]
        )

    def max_dist_from_origin(self):
        return max(
            [
                np.linalg.norm(v)
                for v in itertools.product(
                    (self.xmin, self.xmax),
                    (self.ymin, self.ymax),
                    (self.zmin, self.zmax),
                )
            ]
        )

    def _opt(self, b1, b2):
        return (
            min(b1[0], b2[0]),
            max(b1[1], b2[1]),
            min(b1[2], b2[2]),
            max(b1[3], b2[3]),
            min(b1[4], b2[4]),
            max(b1[5], b2[5]),
        )

    def _bounding_box(self, obj, tol=1e-5):
        bbox = Bnd_Box()
        BRepBndLib.AddOptimal_s(obj, bbox)
        values = bbox.Get()
        return (values[0], values[3], values[1], values[4], values[2], values[5])

    def bbox(self, objects):
        bb = reduce(self._opt, [self._bounding_box(obj) for obj in objects])
        return bb

    def is_empty(self, eps=0.01):
        return (
            (abs(self.xmax - self.xmin) < 0.01)
            and (abs(self.ymax - self.ymin) < 0.01)
            and (abs(self.zmax - self.zmin) < 0.01)
        )

    def __repr__(self):
        return "[x(%f .. %f), y(%f .. %f), z(%f .. %f)]" % (
            self.xmin,
            self.xmax,
            self.ymin,
            self.ymax,
            self.zmin,
            self.zmax,
        )


# Tessellate and discretize functions


def tessellate(shape, tolerance: float, angularTolerance: float = 0.1):

    # Remove previous mesh data
    BRepTools.Clean_s(shape)

    triangulated = BRepTools.Triangulation_s(shape, tolerance)
    if not triangulated:
        # this will add mesh data to the shape and prevent calculating an exact bounding box after this call
        BRepMesh_IncrementalMesh(shape, tolerance, True, angularTolerance)

    vertices = []
    triangles = []
    normals = []

    offset = 0

    for face in get_faces(shape):
        loc = TopLoc_Location()
        poly = BRep_Tool.Triangulation_s(face, loc)
        Trsf = loc.Transformation()

        reverse = face.Orientation() == TopAbs_Orientation.TopAbs_REVERSED
        internal = face.Orientation() == TopAbs_Orientation.TopAbs_INTERNAL

        # add vertices
        vertices += [
            (v.X(), v.Y(), v.Z()) for v in (v.Transformed(Trsf) for v in poly.Nodes())
        ]

        # add triangles
        triangles += [
            (
                t.Value(1) + offset - 1,
                t.Value(3 if reverse else 2) + offset - 1,
                t.Value(2 if reverse else 3) + offset - 1,
            )
            for t in poly.Triangles()
        ]

        # add normals
        if poly.HasUVNodes():
            prop = BRepGProp_Face(face)
            uvnodes = poly.UVNodes()
            for uvnode in uvnodes:
                p = gp_Pnt()
                n = gp_Vec()
                prop.Normal(uvnode.X(), uvnode.Y(), p, n)

                if n.SquareMagnitude() > 0:
                    n.Normalize()
                if internal:
                    n.Reverse()

                normals.append((n.X(), n.Y(), n.Z()))

        offset += poly.NbNodes()

    if not triangulated:
        # Remove the mesh data again
        BRepTools.Clean_s(shape)

    return (
        np.asarray(vertices, dtype=np.float32),
        np.asarray(triangles, dtype=np.uint32),
        np.asarray(normals, dtype=np.float32),
    )


# Source pythonocc-core: Extend/TopologyUtils.py
def discretize_edge(a_topods_edge, deflection=0.1, algorithm="QuasiUniformDeflection"):
    """Take a TopoDS_Edge and returns a list of points
    The more deflection is small, the more the discretization is precise,
    i.e. the more points you get in the returned points
    algorithm: to choose in ["UniformAbscissa", "QuasiUniformDeflection"]
    """
    if not is_edge(a_topods_edge):
        raise AssertionError(
            "You must provide a TopoDS_Edge to the discretize_edge function."
        )
    if a_topods_edge.IsNull():
        print(
            "Warning : TopoDS_Edge is null. discretize_edge will return an empty list of points."
        )
        return []
    curve_adaptator = BRepAdaptor_Curve(a_topods_edge)
    first = curve_adaptator.FirstParameter()
    last = curve_adaptator.LastParameter()

    if algorithm == "QuasiUniformDeflection":
        discretizer = GCPnts_QuasiUniformDeflection()
    elif algorithm == "UniformAbscissa":
        discretizer = GCPnts_UniformAbscissa()
    elif algorithm == "UniformDeflection":
        discretizer = GCPnts_UniformDeflection()
    else:
        raise AssertionError("Unknown algorithm")
    discretizer.Initialize(curve_adaptator, deflection, first, last)

    if not discretizer.IsDone():
        raise AssertionError("Discretizer not done.")
    if not discretizer.NbPoints() > 0:
        raise AssertionError("Discretizer nb points not > 0.")

    points = []
    for i in range(1, discretizer.NbPoints() + 1):
        p = curve_adaptator.Value(discretizer.Parameter(i))
        points.append(p.Coord())
    return points


# Export STL


def write_stl_file(compound, filename, tolerance=1e-3, angular_tolerance=1e-1):

    # Remove previous mesh data
    BRepTools.Clean_s(compound)

    mesh = BRepMesh_IncrementalMesh(compound, tolerance, True, angular_tolerance)
    mesh.Perform()

    writer = StlAPI_Writer()

    result = writer.Write(compound, filename)

    # Remove the mesh data again
    BRepTools.Clean_s(compound)
    return result


# OCP types and accessors

# Source pythonocc-core: Extend/TopologyUtils.py
def is_vertex(topods_shape):
    if not hasattr(topods_shape, "ShapeType"):
        return False
    return topods_shape.ShapeType() == TopAbs_VERTEX


# Source pythonocc-core: Extend/TopologyUtils.py
def is_edge(topods_shape):
    if not hasattr(topods_shape, "ShapeType"):
        return False
    return topods_shape.ShapeType() == TopAbs_EDGE


def is_compound(topods_shape):
    return isinstance(topods_shape, TopoDS_Compound)


def _objects(shape, shape_type):
    HASH_CODE_MAX = 2147483647
    out = {}  # using dict to prevent duplicates

    explorer = TopExp_Explorer(shape, shape_type)

    while explorer.More():
        item = explorer.Current()
        out[item.HashCode(HASH_CODE_MAX)] = downcast(item)
        explorer.Next()

    return list(out.values())


def get_faces(shape):
    return _objects(shape, TopAbs_FACE)


def get_edges(shape):
    return _objects(shape, TopAbs_EDGE)


def get_point(vertex):
    p = BRep_Tool.Pnt_s(vertex)
    return (p.X(), p.Y(), p.Z())
