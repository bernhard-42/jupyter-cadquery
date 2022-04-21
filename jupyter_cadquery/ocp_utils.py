from glob import glob
import io
import itertools
import os
import pickle
import platform
import sys
import tempfile
import time
import unicodedata

from cachetools import LRUCache, cached

import numpy as np
from quaternion import rotate_vectors

import cadquery as cq

from cadquery import Compound, Location
from cadquery.occ_impl.shapes import downcast
from .utils import distance

from OCP.TopAbs import (
    TopAbs_EDGE,
    TopAbs_FACE,
)
from OCP.TopoDS import TopoDS_Compound, TopoDS_Shape
from OCP.TopExp import TopExp_Explorer

from OCP.StlAPI import StlAPI_Writer

from OCP.gp import gp_Trsf, gp_Quaternion, gp_Vec
from OCP.TopLoc import TopLoc_Location


# Bounding Box
from OCP.TopoDS import TopoDS_Shape
from OCP.BinTools import BinTools
from OCP.Bnd import Bnd_Box
from OCP.BRep import BRep_Tool
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepTools import BRepTools
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

# Step reader
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf
from OCP.TDataStd import TDataStd_Name
from OCP.TCollection import TCollection_AsciiString
from OCP.Quantity import Quantity_ColorRGBA
from OCP.TopoDS import TopoDS_Shape, TopoDS_Compound
from OCP.TopLoc import TopLoc_Location
from OCP.TopAbs import TopAbs_SOLID, TopAbs_COMPOUND


MAX_HASH_KEY = 2147483647

#
# Caching helpers
#

def make_key(objs, loc=None, optimal=False):  # pylint: disable=unused-argument
    # optimal is not used and as such ignored
    if not isinstance(objs, (tuple, list)):
        objs = [objs]

    key = (tuple((s.HashCode(MAX_HASH_KEY) for s in objs)), loc_to_tq(loc))
    return key


def get_size(obj):
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        size += sum([get_size(v) + len(k) for k, v in obj.items()])
    elif isinstance(obj, (tuple, list)):
        size += sum([get_size(i) for i in obj])
    return size


cache = LRUCache(maxsize=16 * 1024 * 1024, getsizeof=get_size)

#
# Version
#

def ocp_version():
    lib = glob(f"{os.environ['CONDA_PREFIX']}/lib/libTKBRep.*.*.*")[0]
    return lib.split(".so.")[-1]

#
# Bounding Box
#

class BoundingBox(object):
    def __init__(self, obj=None, optimal=False):
        self.optimal = optimal
        if obj is None:
            self.xmin = self.xmax = self.ymin = self.ymax = self.zmin = self.zmax = 0
        elif isinstance(obj, BoundingBox):
            self.xmin = obj.xmin
            self.xmax = obj.xmax
            self.ymin = obj.ymin
            self.ymax = obj.ymax
            self.zmin = obj.zmin
            self.zmax = obj.zmax
        elif isinstance(obj, dict):
            self.xmin = obj["xmin"]
            self.xmax = obj["xmax"]
            self.ymin = obj["ymin"]
            self.ymax = obj["ymax"]
            self.zmin = obj["zmin"]
            self.zmax = obj["zmax"]
        else:
            bbox = self._bounding_box(obj)
            self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax = bbox

        self._calc()

    def _center_of_mass(self, obj):
        Properties = GProp_GProps()
        BRepGProp.VolumeProperties_s(obj, Properties)
        com = Properties.CentreOfMass()
        return (com.X(), com.Y(), com.Z())

    def _bounding_box(self, obj, tol=1e-6):
        bbox = Bnd_Box()
        if self.optimal:
            BRepTools.Clean_s(obj)
            BRepBndLib.AddOptimal_s(obj, bbox)
        else:
            BRepBndLib.Add_s(obj, bbox)
        if not bbox.IsVoid():
            values = bbox.Get()
            return (values[0], values[3], values[1], values[4], values[2], values[5])
        else:
            c = self._center_of_mass(obj)
            bb = (c[0] - tol, c[0] + tol, c[1] - tol, c[1] + tol, c[2] - tol, c[2] + tol)
            print("\nVoid Bounding Box", bb)
            return bb

    def _calc(self):
        self.xsize = self.xmax - self.xmin
        self.ysize = self.ymax - self.ymin
        self.zsize = self.zmax - self.zmin
        self.center = (
            self.xmin + self.xsize / 2.0,
            self.ymin + self.ysize / 2.0,
            self.zmin + self.zsize / 2.0,
        )
        self.max = max([abs(x) for x in (self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax)])

    def is_empty(self):
        return (
            (abs(self.xmax - self.xmin) < 0.01)
            and (abs(self.ymax - self.ymin) < 0.01)
            and (abs(self.zmax - self.zmin) < 0.01)
        )

    def max_dist_from_center(self):
        return max(
            [
                distance(self.center, v)
                for v in itertools.product((self.xmin, self.xmax), (self.ymin, self.ymax), (self.zmin, self.zmax))
            ]
        )

    def max_dist_from_origin(self):
        return max(
            [
                np.linalg.norm(v)
                for v in itertools.product((self.xmin, self.xmax), (self.ymin, self.ymax), (self.zmin, self.zmax))
            ]
        )

    def update(self, bb, minimize=False):
        lower, upper = (max, min) if minimize else (min, max)

        if isinstance(bb, BoundingBox):
            self.xmin = lower(bb.xmin, self.xmin)
            self.xmax = upper(bb.xmax, self.xmax)
            self.ymin = lower(bb.ymin, self.ymin)
            self.ymax = upper(bb.ymax, self.ymax)
            self.zmin = lower(bb.zmin, self.zmin)
            self.zmax = upper(bb.zmax, self.zmax)
        elif isinstance(bb, dict):
            self.xmin = lower(bb["xmin"], self.xmin)
            self.xmax = upper(bb["xmax"], self.xmax)
            self.ymin = lower(bb["ymin"], self.ymin)
            self.ymax = upper(bb["ymax"], self.ymax)
            self.zmin = lower(bb["zmin"], self.zmin)
            self.zmax = upper(bb["zmax"], self.zmax)
        else:
            raise "Wrong bounding box param"

        self._calc()

    def to_dict(self):
        return {
            "xmin": self.xmin,
            "xmax": self.xmax,
            "ymin": self.ymin,
            "ymax": self.ymax,
            "zmin": self.zmin,
            "zmax": self.zmax,
        }

    def __repr__(self):
        return "{xmin:%.2f, xmax:%.2f, ymin:%.2f, ymax:%.2f, zmin:%.2f, zmax:%.2f}" % (
            self.xmin,
            self.xmax,
            self.ymin,
            self.ymax,
            self.zmin,
            self.zmax,
        )


@cached(cache, key=make_key)
def bounding_box(objs, loc=None, optimal=False):
    if isinstance(objs, (list, tuple)):
        compound = Compound._makeCompound(objs)  # pylint: disable=protected-access
    else:
        compound = objs

    return BoundingBox(compound if loc is None else compound.Moved(loc), optimal=optimal)


def np_bbox(p, t, q):
    if p.size == 0:
        return None

    n_p = p.reshape(-1, 3)
    if t is None and q is None:
        v = n_p
    else:
        n_t = np.asarray(t)
        n_q = np.quaternion(q[-1], *q[:-1])
        v = rotate_vectors([n_q], n_p)[0] + n_t

    bbmin = np.min(v, axis=0)
    bbmax = np.max(v, axis=0)
    return {"xmin": bbmin[0], "xmax": bbmax[0], "ymin": bbmin[1], "ymax": bbmax[1], "zmin": bbmin[2], "zmax": bbmax[2]}

#
# StepReader
#

def clean_string(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C").replace(" ", "_")


class StepReader:
    def __init__(self):
        self.shape_tool = None
        self.color_tool = None
        self.assembly = None

    def get_name(self, label):
        t = TDataStd_Name()
        if label.FindAttribute(TDataStd_Name.GetID_s(), t):
            name = TCollection_AsciiString(t.Get()).ToCString()
            return clean_string(name)
        else:
            return "Component"

    def get_color(self, label):
        col = Quantity_ColorRGBA()
        if self.color_tool.GetColor(label, XCAFDoc_ColorSurf, col):
            return (col.GetRGB().Red(), col.GetRGB().Green(), col.GetRGB().Blue(), col.Alpha())
        else:
            return (0.5, 0.5, 0.5, 1.0)

    def get_shape(self, label):
        return self.shape_tool.GetShape_s(label)

    def get_location(self, label):
        return self.shape_tool.GetLocation_s(label)

    def load(self, filename):
        print("Reading STEP file ...", flush=True, end="")
        time.sleep(0.01)  # ensure output is shown

        fmt = TCollection_ExtendedString("CadQuery-XCAF")
        doc = TDocStd_Document(fmt)

        self.shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
        self.color_tool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())

        reader = STEPCAFControl_Reader()
        reader.SetNameMode(True)
        reader.SetColorMode(True)
        reader.SetLayerMode(True)

        reader.ReadFile(filename)
        reader.Transfer(doc)
        print(" done")
        time.sleep(0.01)  # ensure output is shown

        root_labels = TDF_LabelSequence()
        self.shape_tool.GetFreeShapes(root_labels)

        result = []
        for i in range(root_labels.Length()):
            label = root_labels.Value(i + 1)
            if self.shape_tool.IsAssembly_s(label):
                result.append(
                    {
                        "name": self.get_name(label),
                        "shape": self.get_shape(label),
                        "shapes": self.get_subshapes(label),
                        "color": self.get_color(label),
                        "loc": self.get_location(label),
                    }
                )
            else:
                raise RuntimeError("ERROR: Shapes are not supported")

        self.assembly = result

    def get_subshapes(self, label, loc=None):
        label_comps = TDF_LabelSequence()
        is_assembly = self.shape_tool.GetComponents_s(label, label_comps)

        if not is_assembly and self.get_shape(label).ShapeType() == TopAbs_COMPOUND:
            is_assembly = self.shape_tool.GetSubShapes_s(label, label_comps)

        result = []

        for i in range(label_comps.Length()):
            label_comp = label_comps.Value(i + 1)

            sub_shape = None
            if self.shape_tool.IsReference_s(label_comp):
                label_ref = TDF_Label()
                self.shape_tool.GetReferredShape_s(label_comp, label_ref)
                sub_shape = {
                    "name": self.get_name(label_ref),
                    "color": self.get_color(label_ref),
                    "shape": self.get_shape(label_ref),
                    "shapes": self.get_subshapes(label_ref),
                    # one has to use the location of the component, not of the reference
                    "loc": self.get_location(label_comp),
                }
            else:
                shape = self.get_shape(label_comp)
                if shape.ShapeType() in (TopAbs_SOLID, TopAbs_COMPOUND):
                    if shape.ShapeType() == TopAbs_COMPOUND:
                        print(f"{self.get_name(label)}_{i+1}", "yet another compound")
                    sub_shape = {
                        # self.get_name(label_comp) crashes
                        "name": f"{self.get_name(label)}_{i+1}",
                        "color": self.get_color(label_comp),
                        "shape": shape,
                        "shapes": [],
                        "loc": self.get_location(label_comp),
                    }

            if sub_shape is not None:
                result.append(sub_shape)

        return result

    def to_cadquery(self):
        def to_workplane(obj):
            return cq.Workplane(obj=cq.Shape(obj))

        def to_location(obj):
            return cq.Location(obj)

        def to_color(rgba):
            return cq.Color(*rgba)

        def walk(objs):
            a = cq.Assembly()
            names = {}
            for obj in objs:
                name = obj["name"]

                # Create a unique name by postfixing the enumerator index if needed
                if names.get(name) is None:
                    names[name] = 1
                else:
                    names[name] += 1
                    name = f"{obj['name']}_{names[name]}"

                a.add(
                    walk(obj["shapes"]) if len(obj["shapes"]) > 0 else to_workplane(obj["shape"]),
                    name=name,
                    color=to_color(obj["color"]),
                    loc=to_location(obj.get("loc")),
                )
            return a

        result = walk(self.assembly)

        if len(result.children) == 1:
            return result.children[0]
        else:
            return result

    def save_assembly(self, filename):
        def _save_assembly(assembly):
            result = []
            for assembly in assembly:
                obj = {
                    "name": assembly["name"],
                    "shape": serialize(assembly["shape"]),
                    "shapes": [],
                    "color": assembly["color"],
                    "loc": loc_to_tq(assembly["loc"]),
                }
                if assembly["shapes"]:
                    obj["shapes"] = _save_assembly(assembly["shapes"])
                result.append(obj)
            return result

        objs = _save_assembly(self.assembly)
        with open(filename, "wb") as fd:
            pickle.dump(objs, fd)

    def load_assembly(self, filename):
        def _load_assembly(objs):
            result = []
            for obj in objs:
                assembly = {
                    "name": obj["name"],
                    "shape": deserialize(obj["shape"]),
                    "shapes": [],
                    "color": obj["color"],
                    "loc": tq_to_loc(*obj["loc"]),
                }
                if obj["shapes"]:
                    assembly["shapes"] = _load_assembly(obj["shapes"])
                result.append(assembly)
            return result

        with open(filename, "rb") as fd:
            self.assembly = _load_assembly(pickle.load(fd))


# Export STL


def write_stl_file(compound, filename, tolerance=None, angular_tolerance=None):

    # Remove previous mesh data
    BRepTools.Clean_s(compound)

    mesh = BRepMesh_IncrementalMesh(compound, tolerance, True, angular_tolerance)
    mesh.Perform()

    writer = StlAPI_Writer()

    result = writer.Write(compound, filename)

    # Remove the mesh data again
    BRepTools.Clean_s(compound)
    return result


# OCP serialisation


def serialize(shape):
    if platform.system() == "Darwin":
        with tempfile.NamedTemporaryFile() as tf:
            BinTools.Write_s(shape, tf.name)
            with open(tf.name, "rb") as fd:
                buffer = fd.read()
    else:
        bio = io.BytesIO()
        BinTools.Write_s(shape, bio)
        buffer = bio.getvalue()
    return buffer


def deserialize(buffer):
    shape = TopoDS_Shape()
    if platform.system() == "Darwin":
        with tempfile.NamedTemporaryFile() as tf:
            with open(tf.name, "wb") as fd:
                fd.write(buffer)
            BinTools.Read_s(shape, tf.name)
    else:
        bio = io.BytesIO(buffer)
        BinTools.Read_s(shape, bio)
    return shape


# OCP types and accessors


def is_compound(topods_shape):
    return isinstance(topods_shape, TopoDS_Compound)


def is_shape(topods_shape):
    return isinstance(topods_shape, TopoDS_Shape)


def _get_topo(shape, topo):
    explorer = TopExp_Explorer(shape, topo)
    hashes = {}
    while explorer.More():
        item = explorer.Current()
        hash_value = item.HashCode(MAX_HASH_KEY)
        if hashes.get(hash_value) is None:
            hashes[hash_value] = True
            yield downcast(item)
        explorer.Next()


def get_faces(shape):
    return _get_topo(shape, TopAbs_FACE)


def get_edges(shape):
    return _get_topo(shape, TopAbs_EDGE)


def get_point(vertex):
    p = BRep_Tool.Pnt_s(vertex)
    return (p.X(), p.Y(), p.Z())


def get_rgb(color):
    if color is None:
        return (176, 176, 176)
    rgb = color.wrapped.GetRGB()
    return (int(255 * rgb.Red()), int(255 * rgb.Green()), int(255 * rgb.Blue()))


def tq_to_loc(t, q):
    T = gp_Trsf()
    Q = gp_Quaternion(*q)
    V = gp_Vec(*t)
    T.SetTransformation(Q, V)
    return TopLoc_Location(T)


def loc_to_tq(loc):
    if loc is None:
        return (None, None)
        
    T = loc.Transformation()
    t = T.TranslationPart()
    q = T.GetRotation()
    return ((t.X(), t.Y(), t.Z()), (q.X(), q.Y(), q.Z(), q.W()))

def wrapped_or_None(obj):
    return None if obj is None else obj.wrapped

def __location__repr__(self):
    t, r = loc_to_tq(self.wrapped)
    return f"Location: t=({t[0]}, {t[1]}, {t[2]}), q=({r[0]}, {r[1]}, {r[2]}, {r[3]})"


Location.__repr__ = __location__repr__  # type: ignore
