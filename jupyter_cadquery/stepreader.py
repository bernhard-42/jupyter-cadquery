import os
import pickle
import time
import unicodedata

from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDF import TDF_LabelSequence, TDF_Label, TDF_ChildIterator
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf, XCAFDoc_ColorGen, XCAFDoc_ColorCurv
from OCP.TDataStd import TDataStd_Name
from OCP.TCollection import TCollection_AsciiString
from OCP.Quantity import Quantity_ColorRGBA
from OCP.TopoDS import TopoDS_Shape, TopoDS_Compound, TopoDS_Iterator
from OCP.TopLoc import TopLoc_Location
from OCP.TopAbs import TopAbs_SOLID, TopAbs_COMPOUND, TopAbs_SHELL, TopAbs_FACE
from OCP.TopExp import TopExp_Explorer

from .ocp_utils import serialize, deserialize, loc_to_tq, tq_to_loc
from .utils import warn

import cadquery as cq

MISSING_COLOR = (0.8, 0.8, 0.8, 1)
DEFAULT_COLOR = (0.5906188488006592, 0.637596845626831, 0.8549926280975342)


def clean_string(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C").replace(" ", "_")


def is_default_color(col):
    return all([abs(col[i] - DEFAULT_COLOR[i]) < 1e-6 for i in range(3)])


class StepReader:
    def __init__(self):
        self.shape_tool = None
        self.color_tool = None
        self.assembly = None
        self.name = "Assembly"

    def _create_shape(self, name, loc=None, color=None, shape=None, children=None):
        return {
            "name": name,
            "loc": loc,
            "color": color,
            "shape": shape,
            "shapes": children,
        }

    def get_name(self, label):
        t = TDataStd_Name()
        if label.FindAttribute(TDataStd_Name.GetID_s(), t):
            name = TCollection_AsciiString(t.Get()).ToCString()
            return clean_string(name)
        else:
            return "Component"

    def get_color(self, shape, name, use_faces=True):
        to_list = lambda c: (c.GetRGB().Red(), c.GetRGB().Green(), c.GetRGB().Blue(), c.Alpha())

        missing_color = False
        col = Quantity_ColorRGBA()
        if self.color_tool.GetColor(shape, XCAFDoc_ColorGen, col) or self.color_tool.GetColor(
            shape, XCAFDoc_ColorSurf, col
        ):
            color = to_list(col)
            if is_default_color(color):
                color = MISSING_COLOR
                missing_color = True
        else:
            color = MISSING_COLOR
            missing_color = True

        # If we get the default color or the color is missing, iterate over faces
        if missing_color:
            colors = []
            exp = TopExp_Explorer(shape, TopAbs_FACE)
            while exp.More():
                face = exp.Current()
                col = Quantity_ColorRGBA()
                if self.color_tool.GetColor(face, XCAFDoc_ColorGen, col) or self.color_tool.GetColor(
                    face, XCAFDoc_ColorSurf, col
                ):
                    colors.append(to_list(col))
                exp.Next()

            # If all faces have the same color, use this as shape color
            colors = set(colors)
            if len(colors) == 1:
                return list(colors)[0]

        return color

    def get_location(self, label):
        return self.shape_tool.GetLocation_s(label)

    def get_shape(self, label):
        return self.shape_tool.GetShape_s(label)

    def get_shape_details(self, label, name, loc):
        it = TDF_ChildIterator()
        it.Initialize(label)
        i = 0
        shapes = []
        while it.More():
            name = f"{name}_{i+1}"
            shape = self.get_shape(it.Value())

            if shape.ShapeType() == TopAbs_SOLID:
                color = self.get_color(shape, name)
                sub_shape = self._create_shape(name, loc, color, shape)
                shapes.append(sub_shape)
                i += 1

            elif shape.ShapeType == TopAbs_COMPOUND:
                warn(f"Nested compounds not supported yet: {name}")

            elif shape.ShapeType == TopAbs_SHELL:
                warn(f"Shells nested in compounds not supported yet: {name}")

            it.Next()

        return shapes

    def get_subshapes(self, label, loc=None):
        label_comps = TDF_LabelSequence()
        self.shape_tool.GetComponents_s(label, label_comps)

        result = []

        for i in range(label_comps.Length()):
            label_comp = label_comps.Value(i + 1)

            if self.shape_tool.IsReference_s(label_comp):
                label_ref = TDF_Label()
                self.shape_tool.GetReferredShape_s(label_comp, label_ref)
            else:
                label_ref = label_comp

            is_assembly = self.shape_tool.IsAssembly_s(label_ref)

            name = self.get_name(label_ref)
            loc = self.get_location(label_comp)
            shape = self.get_shape(label_ref)

            sub_shape = self._create_shape(name, loc)

            if is_assembly:
                sub_shape["shapes"] = self.get_subshapes(label_ref)

            elif shape.ShapeType() == TopAbs_COMPOUND and label_ref.HasChild():
                sub_shape["shapes"] = self.get_shape_details(label_ref, name, TopLoc_Location())

            else:
                sub_shape["shape"] = shape
                sub_shape["color"] = self.get_color(shape, name, True)

            result.append(sub_shape)

        return result

    def load(self, filename):
        if not os.path.exists(filename):
            raise FileNotFoundError(filename)

        print("Reading STEP file ... ", flush=True, end="")
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

        print("parsing Assembly ... ", flush=True, end="")
        time.sleep(0.01)  # ensure output is shown

        root_labels = TDF_LabelSequence()
        self.shape_tool.GetFreeShapes(root_labels)

        result = []
        for i in range(root_labels.Length()):
            root_label = root_labels.Value(i + 1)

            name = self.get_name(root_label)
            loc = self.get_location(root_label)

            sub_shape = self._create_shape(name, loc)

            if self.shape_tool.IsAssembly_s(root_label):
                sub_shape["shapes"] = self.get_subshapes(root_label, TopLoc_Location())
            elif self.shape_tool.IsShape_s(root_label) and root_label.HasChild():
                sub_shape["shapes"] = self.get_shape_details(root_label, name, TopLoc_Location())
            else:
                warn("Only Assemblies and Shapes are supported on a top-level - ignored")

            result.append(sub_shape)

        self.assembly = result

        print("done")

    def to_cadquery(self):
        def to_workplane(obj):
            return cq.Workplane(obj=cq.Shape(obj))

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
                    to_workplane(obj["shape"]) if obj["shapes"] is None else walk(obj["shapes"]),
                    name=name,
                    color=None if obj["color"] is None else cq.Color(*obj["color"]),
                    loc=cq.Location(obj.get("loc")),
                )

            return a

        if len(self.assembly) == 1:
            if len(self.assembly[0]["shapes"]) == 0:
                raise ValueError("Empty assembly list")
            result = walk(self.assembly[0]["shapes"])
            result.name = self.assembly[0]["name"]
            result.loc = cq.Location(self.assembly[0]["loc"])
        else:
            raise RuntimeError("multiple root labels")

        if len(result.children) == 1:
            return result.children[0]
        else:
            return result

    def save_assembly(self, filename):
        def _save_assembly(assembly):
            if assembly is None:
                return None

            result = []
            for assembly in assembly:
                obj = {
                    "name": assembly["name"],
                    "shape": serialize(assembly["shape"]),
                    "shapes": _save_assembly(assembly["shapes"]),
                    "color": assembly["color"],
                    "loc": loc_to_tq(assembly["loc"]),
                }
                result.append(obj)
            return result

        objs = _save_assembly(self.assembly)
        with open(filename, "wb") as fd:
            pickle.dump(objs, fd)

    def load_assembly(self, filename):
        def _load_assembly(objs):
            if objs is None:
                return None

            result = []
            for obj in objs:
                assembly = {
                    "name": obj["name"],
                    "shape": deserialize(obj["shape"]),
                    "shapes": _load_assembly(obj["shapes"]),
                    "color": obj["color"],
                    "loc": tq_to_loc(*obj["loc"]),
                }
                result.append(assembly)
            return result

        with open(filename, "rb") as fd:
            self.assembly = _load_assembly(pickle.load(fd))
