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

from .utils import warn


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
        - show_parent:       Show the parent for edges, faces and vertices objects
        - show_bbox:         Show bounding box (default=False)
        - viewer:            Name of the sidecar viewer
        - anchor:            How to open sidecar: "right", "split-right", "split-bottom", ...
        - theme:             Theme "light" or "dark" (default="light")
        - tools:             Show the viewer tools like the object tree
        - timeit:            Show rendering times, levels = False, 0,1,2,3,4,5 (default=False)

        NOT SUPPORTED ANY MORE:
        - mac_scrollbar      The default now
        - bb_factor:         Removed
        - display            Use 'viewer="<viewer title>"' (for sidecar display) or 'viewer=None' (for cell display)
        """

        for k, v in kwargs.items():
            if self.get_default(k, "") == "":
                print(f"Paramater {k} is not a valid argument for show()")
            else:
                # if k == "zoom" and v == 1.0:
                #     # for zoom == 1 viewing has a bug, so slightly increase it
                #     v = 1 + 1e-6
                self.defaults[k] = v

        # if kwargs.get("display") == "html":
        #     self.defaults["tools"] = False
        #     from IPython.display import HTML, display
        #     from ipywidgets.embed import DEFAULT_EMBED_REQUIREJS_URL

        #     display(HTML(f"""<script src="{DEFAULT_EMBED_REQUIREJS_URL}" crossorigin="anonymous"></script>"""))

    def reset_defaults(self):
        self.defaults = {
            #
            # display options
            "viewer": None,
            "anchor": "right",
            "cad_width": 800,
            "tree_width": 250,
            "height": 600,
            "theme": "light",
            #
            # render options
            "default_color": (232, 176, 36),
            "default_edge_color": "#707070",
            "ambient_intensity": 0.75,
            "direct_intensity": 0.15,
            "render_normals": False,
            "render_edges": True,
            "render_mates": False,
            "mate_scale": 1,
            "quality": None,
            "deviation": 0.1,
            "angular_tolerance": 0.2,
            "edge_accuracy": None,
            "optimal_bb": False,
            #
            # viewer options
            "tools": True,
            "control": "trackball",
            "axes": False,
            "axes0": False,
            "grid": [False, False, False],
            "ticks": 10,
            "ortho": True,
            "transparent": False,
            "black_edges": False,
            "reset_camera": True,
            "show_parent": True,
            "show_bbox": False,
            "position": None,
            "quaternion": None,
            "zoom": 1,
            "zoom_speed": 1.0,
            "pan_speed": 1.0,
            "rotate_speed": 1.0,
            "timeit": False,
            "js_debug": False,
        }


def get_defaults():
    return DEFAULTS.get_defaults()


def get_default(key, default_value=None):
    return DEFAULTS.get_default(key, default_value)


def set_defaults(**kwargs):
    if isinstance(kwargs.get("grid"), bool):
        warn(
            "Using bool for grid is deprecated, please use (xy-grid, xz-grid. yz-grid)", DeprecationWarning, "once",
        )
        kwargs["grid"] = (kwargs["grid"], False, False)

    DEFAULTS.set_defaults(**kwargs)


def apply_defaults(**kwargs):
    result = dict(get_defaults())
    for k, v in kwargs.items():
        if result.get(k, "") != "":
            result[k] = v
        else:
            print(f"unknown parameter {k}")
    return result


def reset_defaults():
    DEFAULTS.reset_defaults()


def create_args(config):
    adapt = lambda key: "title" if key == "viewer" else key

    return {
        adapt(k): v
        for k, v in config.items()
        if k in ["viewer", "title", "anchor", "cad_width", "tree_width", "height", "theme",]
    }


def add_shape_args(config):
    args = {
        k: v
        for k, v in config.items()
        if k
        in [
            "tools",
            "control",
            "axes",
            "axes0",
            "grid",
            "ortho",
            "transparent",
            "black_edges",
            "ticks",
            "reset_camera",
            "position",
            "quaternion",
            "zoom",
            "ambient_intensity",
            "direct_intensity",
            "zoom_speed",
            "pan_speed",
            "rotate_speed",
            "clipIntersection",
            "clipPlaneHelpers",
            "clipNormal",
            "timeit",
            "js_debug",
        ]
    }

    return args


def tessellation_args(config):
    return {
        k: v
        for k, v in config.items()
        if k
        in [
            "mate_scale",
            "render_edges",
            "render_mates",
            "angular_tolerance",
            "deviation",
            "optimal_bb",
            "edge_accuracy",
            "normal_len",
            "default_color",
            "default_edge_color",
            "default_opacity",
            "quality",
        ]
    }


def show_args(config):
    args = create_args(config)
    args.update(add_shape_args(config))

    if config.get("normal_len") is not None:
        args["normal_len"] = config["normal_len"]
    return args


DEFAULTS = Defaults()
