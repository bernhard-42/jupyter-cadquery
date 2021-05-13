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
        - default_color:     Default mesh color (default=(232, 176, 36))
        - default_edgecolor: Default mesh color (default=(128, 128, 128))
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
        - ticks:             Hint for the number of ticks in both directions (default=10)
        - ortho:             Use orthographic projections (default=True)
        - transparent:       Show objects transparent (default=False)
        - ambient_intensity  Intensity of ambient ligth (default=1.0)
        - direct_intensity   Intensity of direct lights (default=0.12)
        - position:          Relative camera position that will be scaled (default=(1, 1, 1))
        - rotation:          z, y and y rotation angles to apply to position vector (default=(0, 0, 0))
        - zoom:              Zoom factor of view (default=2.5)
        - reset_camera:      Reset camera position, rotation and zoom to default (default=True)
        - mac_scrollbar:     Prettify scrollbars (default=True)
        - display:           Select display: "sidecar", "cell", "html"
        - theme:             Theme "light" or "dark" (default="light")
        - tools:             Show the viewer tools like the object tree
        - timeit:            Show rendering times, levels = False, 0,1,2,3,4,5 (default=False)

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
            "default_color": (232, 176, 36),
            "default_edgecolor": (128, 128, 128),
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
            "ticks": 10,
            "ortho": True,
            "transparent": False,
            "black_edges": False,
            "ambient_intensity": 1.0,
            "direct_intensity": 0.12,
            "position": (1, 1, 1),
            "rotation": (0, 0, 0),
            "zoom": 2.5,
            "reset_camera": True,
            "mac_scrollbar": True,
            "display": "cell",
            "theme": "light",
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


def split_args(config):
    create_args = {
        k: v
        for k, v in config.items()
        if k
        in [
            "height",
            "bb_factor",
            "tree_width",
            "cad_width",
            "axes",
            "axes0",
            "grid",
            "ortho",
            "transparent",
            "mac_scrollbar",
            "display",
            "tools",
            "timeit",
        ]
    }
    add_shape_args = {
        k: v
        for k, v in config.items()
        if k
        in [
            "bb_factor",
            "ticks",
            "default_edgecolor",
            "ambient_intensity",
            "direct_intensity",
            "position",
            "rotation",
            "zoom",
            "reset_camera",
        ]
    }
    return create_args, add_shape_args


DEFAULTS = Defaults()