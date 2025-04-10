#
# Copyright 2025 Bernhard Walter
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

# from ocp_tessellate.cad_objects import Edges, Faces, Part, PartGroup, Vertices
from ocp_tessellate.convert import tessellate_group, to_assembly
from ocp_tessellate.ocp_utils import is_build123d_assembly, is_cadquery_assembly
from ocp_tessellate.utils import numpy_to_json
from ocp_vscode import show

try:
    import cadquery as cq

    HAS_CADQUERY = True
except ImportError:
    HAS_CADQUERY = False

try:
    import build123d as bd

    HAS_BUILD123D = True
except ImportError:
    HAS_BUILD123D = False


# pylint: disable=protected-access
# pylint: disable=unnecessary-lambda
def auto_show():
    if HAS_CADQUERY:
        try:
            del cq.Workplane._repr_html_  # pylint: disable=no-member
            del cq.Shape._repr_html_  # pylint: disable=no-member
        except:  # pylint: disable=bare-except
            pass
        cq.Workplane._ipython_display_ = lambda cad_obj: show(cad_obj)
        cq.Shape._ipython_display_ = lambda cad_obj: show(cad_obj)
        cq.Assembly._ipython_display_ = lambda cad_obj: show(cad_obj)
        cq.Sketch._ipython_display_ = lambda cad_obj: show(cad_obj)
        print("Overwriting auto display for cadquery Workplane and Shape")

    if HAS_BUILD123D:
        bd.BuildPart._ipython_display_ = lambda cad_obj: show(cad_obj)
        bd.BuildSketch._ipython_display_ = lambda cad_obj: show(cad_obj)
        bd.BuildLine._ipython_display_ = lambda cad_obj: show(cad_obj)
        bd.ShapeList._ipython_display_ = lambda cad_obj: show(cad_obj)
        bd.Shape._ipython_display_ = lambda cad_obj: show(cad_obj)
        try:
            del bd.Shape._repr_javascript_
        except:
            pass
        print(
            "Overwriting auto display for build123d BuildPart, BuildSketch, BuildLine, ShapeList"
        )


def get_pick(assembly, pick):
    if pick == {}:
        print("First double click on an object in the CAD viewer")
        return None

    path = pick["path"]
    name = pick["name"]
    id_ = "/".join([path, name])

    if is_cadquery_assembly(assembly):
        short_path = "/".join(id_.split("/")[2:])
        if assembly.objects.get(short_path) is not None:
            return assembly.objects[short_path]
        else:
            short_path = "/".join(id_.split("/")[2:-1])
            if assembly.objects.get(short_path) is not None:
                return assembly.objects[short_path]
    else:
        print("Currently only CadQuery is supported")
