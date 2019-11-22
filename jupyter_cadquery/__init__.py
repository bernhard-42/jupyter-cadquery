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

from ._version import __version_info__, __version__
from .cad_display import set_sidecar
from .export import exportSTL


def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'jupyter_cadquery',
        'require': 'jupyter_cadquery/extension'
    }]

def patch_cq():
    print("Patch")
    import cadquery
    print("  - cadquery.Workplane.lineTo: guard against line length 0")

    def lineTo(self, x, y, forConstruction=False):
        """
        Make a line from the current point to the provided point

        :param float x: the x point, in workplane plane coordinates
        :param float y: the y point, in workplane plane coordinates
        :return: the Workplane object with the current point at the end of the new line

        see :py:meth:`line` if you want to use relative dimensions to make a line instead.
        """
        startPoint = self._findFromPoint(False)

        endPoint = self.plane.toWorldCoords((x, y))

        if startPoint.sub(endPoint).Length > self.ctx.tolerance:
            p = cadquery.Edge.makeLine(startPoint, endPoint)

            if not forConstruction:
                self._addPendingEdge(p)

            return self.newObject([p])
        else:
            return self

    cadquery.Workplane.lineTo = lineTo

