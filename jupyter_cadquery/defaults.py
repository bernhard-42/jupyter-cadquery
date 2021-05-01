#
# Copyright 2021 Bernhard Walter
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


class Defaults:
    def __init__(self):
        self.reset_defaults()

    def get_defaults(self):
        return self.defaults

    def get_default(self, key, default_value=None):
        return self.defaults.get(key, default_value)

    def set_defaults(self, **kwargs):
        """Set defaults for CAD viewer

        Valid keywords:
        - height:            Height of the CAD view (default=600)
        - tree_width:        Width of navigation tree part of the view (default=250)
        - cad_width:         Width of CAD view part of the view (default=800)
        - bb_factor:         Scale bounding box to ensure compete rendering (default=1.5)
        - render_shapes:     Render shapes  (default=True)
        - render_edges:      Render edges  (default=True)
        - render_normals:    Render normals (default=False)
        - render_mates:      Render mates (for MAssemblies)
        - mate_scale:        Scale of rendered mates (for MAssemblies)
        - quality:           Linear deflection for tessellation (default=None)
                             If None, uses: (xlen + ylen + zlen) / 300 * deviation)
        - deviation:         Deviation from default for linear deflection value ((default=0.1)
        - angular_tolerance: Angular deflection in radians for tessellation (default=0.2)
        - edge_accuracy:     Presicion of edge discretizaion (default=None)
                             If None, uses: quality / 100
        - optimal_bb:        Use optimal bounding box (default=False)
        - axes:              Show axes (default=False)
        - axes0:             Show axes at (0,0,0) (default=False)
        - grid:              Show grid (default=False)
        - ortho:             Use orthographic projections (default=True)
        - transparent:       Show objects transparent (default=False)
        - ambient_intensity  Intensity of ambient ligth (default=1.0)
        - direct_intensity   Intensity of direct lights (default=0.12)
        - position:          Relative camera position that will be scaled (default=(1, 1, 1))
        - rotation:          z, y and y rotation angles to apply to position vector (default=(0, 0, 0))
        - zoom:              Zoom factor of view (default=2.5)
        - mac_scrollbar:     Prettify scrollbasrs on Macs (default=True)
        - display:           Select display: "sidecar", "cell", "html"
        - tools:             Show the viewer tools like the object tree
        - timeit:            Show rendering times (default=False)

        For example isometric projection can be achieved in two ways:
        - position = (1, 1, 1)
        - position = (0, 0, 1) and rotation = (45, 35.264389682, 0)
        """

        for k, v in kwargs.items():
            if self.get_default(k, "") == "":
                print("Paramater %s is not a valid argument for show()" % k)
            else:
                if k == "zoom" and v == 1.0:
                    # for zoom == 1 viewing has a bug, so slightly increase it
                    v = 1 + 1e-6
                self.defaults[k] = v

    def reset_defaults(self):
        self.defaults = {
            "height": 600,
            "tree_width": 250,
            "cad_width": 800,
            "bb_factor": 1.0,
            "render_shapes": True,
            "render_edges": True,
            "render_normals": False,
            "render_mates": False,
            "mate_scale": 1,
            "quality": None,
            "deviation": 0.1,
            "angular_tolerance": 0.2,
            "edge_accuracy": None,
            "optimal_bb": False,
            "axes": False,
            "axes0": False,
            "grid": False,
            "ortho": True,
            "transparent": False,
            "black_edges": False,
            "ambient_intensity": 1.0,
            "direct_intensity": 0.12,
            "position": (1, 1, 1),
            "rotation": (0, 0, 0),
            "zoom": 2.5,
            "mac_scrollbar": True,
            "display": "cell",
            "tools": True,
            "timeit": False,
        }


def get_defaults():
    return DEFAULTS.get_defaults()


def get_default(key, default_value=None):
    return DEFAULTS.get_default(key, default_value)


def set_defaults(**kwargs):
    DEFAULTS.set_defaults(**kwargs)


def reset_defaults():
    DEFAULTS.reset_defaults()


DEFAULTS = Defaults()