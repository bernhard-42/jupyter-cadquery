import pickle

import cadquery as cq

from jupyter_cadquery.ocp_utils import loc_to_tq, tq_to_loc, serialize, deserialize
from jupyter_cadquery.base import _tessellate_group, _combined_bb
from jupyter_cadquery.cad_objects import to_assembly
from jupyter_cadquery.utils import numpy_to_json

try:
    from cadquery_massembly import MAssembly, Mate
    from cadquery_massembly.massembly import MateDef

    HAS_MASSEMBLY = True
except ImportError:
    HAS_MASSEMBLY = False


def save_binary(assembly, filename, metadata=None):
    def to_tuple(vec):
        return vec.toTuple() if isinstance(vec, cq.Vector) else vec

    def _create_assembly_object(name, loc=None, color=None, shape=None, children=None):
        return {
            "name": name,
            "loc": loc,
            "color": color,
            "shape": shape,
            "children": [] if children is None else children,
        }

    def _save_binary(assembly):
        if assembly is None:
            return None

        result = _create_assembly_object(
            assembly.name,
            None if assembly.loc is None else loc_to_tq(assembly.loc.wrapped),
            None if assembly.color is None else assembly.color.toTuple(),
            None if assembly.obj is None else serialize(assembly.obj.val().wrapped),
            [_save_binary(child) for child in assembly.children],
        )

        return result

    typ = type(assembly).__name__
    mates = {}
    if typ == "MAssembly":
        mates = {
            name: {
                "mate": {
                    "origin": to_tuple(mate_def.mate.origin),
                    "x_dir": to_tuple(mate_def.mate.x_dir),
                    "y_dir": to_tuple(mate_def.mate.y_dir),
                    "z_dir": to_tuple(mate_def.mate.z_dir),
                },
                "assembly": mate_def.assembly.name,
                "origin": mate_def.origin,
            }
            for name, mate_def in assembly.mates.items()
        }

    objs = {
        "type": typ,
        "obj": _save_binary(assembly),
        "mates": mates,
        "metadata": metadata,
    }
    with open(filename, "wb") as fd:
        pickle.dump(objs, fd)


def load_binary(filename, assembly_name=None):
    def to_workplane(obj):
        return cq.Workplane(obj=cq.Solid(obj))

    def _load_binary(obj, klass):
        if obj is None:
            return None

        assembly = klass(
            None if obj["shape"] is None else to_workplane(deserialize(obj["shape"])),
            name=obj["name"],
            loc=None if obj["loc"] is None else cq.Location(tq_to_loc(*obj["loc"])),
            color=None if obj["color"] is None else cq.Color(*obj["color"]),
        )
        for child in obj["children"]:
            assembly.add(_load_binary(child, klass))

        return assembly

    with open(filename, "rb") as fd:
        buffer = pickle.load(fd)

    is_ma = buffer["type"] == "MAssembly"

    klass = MAssembly if is_ma else cq.Assembly
    assembly = _load_binary(buffer["obj"], klass)

    if is_ma:
        mates = {}
        for name, mate_obj in buffer["mates"].items():
            mate = Mate()
            mate.origin = cq.Vector(*mate_obj["mate"]["origin"])
            mate.x_dir = cq.Vector(*mate_obj["mate"]["x_dir"])
            mate.y_dir = cq.Vector(*mate_obj["mate"]["y_dir"])
            mate.z_dir = cq.Vector(*mate_obj["mate"]["z_dir"])
            mates[name] = MateDef(mate, assembly.objects[mate_obj["assembly"]], mate_obj["origin"])
        assembly.mates = mates

    if assembly_name is not None:
        assembly.name = assembly_name

    return assembly, buffer["metadata"]


def exportJson(cad_obj, filename):
    shapes, states = _tessellate_group(to_assembly(cad_obj))
    bb = _combined_bb(shapes).to_dict()
    # add global bounding box
    shapes["bb"] = bb

    with open(filename, "w", encoding="utf-8") as fd:
        fd.write(numpy_to_json((shapes, states)))
