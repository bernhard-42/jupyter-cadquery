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

from jupyter_cadquery.cad_objects import _Assembly, _Part, _show


class Part(_Part):

    def __init__(self, shape, name="part", color=None, show_faces=True, show_edges=True):
        super().__init__([shape], name, color, show_faces, show_edges)

    def to_assembly(self):
        return Assembly([self])

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


class Assembly(_Assembly):

    def to_assembly(self):
        return self

    def show(self, grid=False, axes=False):
        return show(self, grid=grid, axes=axes)


def show(cad_obj,
         height=600,
         tree_width=250,
         cad_width=600,
         quality=0.5,
         axes=False,
         axes0=True,
         grid=False,
         ortho=True,
         transparent=False,
         mac_scrollbar=True,
         sidecar=None,
         show_parents=True,
         position=None,
         rotation=None,
         zoom=None):

    assembly = None
    if isinstance(cad_obj, (Assembly, Part)):
        assembly = cad_obj.to_assembly()

    if assembly is None:
        raise ValueError("%s cannot be viewed" % type(cad_obj))
    return _show(assembly, height, tree_width, cad_width, quality, axes, axes0, grid, ortho, transparent, position,
                 rotation, zoom, mac_scrollbar, sidecar)
