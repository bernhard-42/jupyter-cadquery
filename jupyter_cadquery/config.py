"""Configuration of the viewer"""

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

from pathlib import Path

from yaml import safe_dump, safe_load

WORKSPACE_DEFAULTS = None

__all__ = ["get_user_defaults", "save_user_defaults"]


def workspace_defaults():
    return {
        "_splash": False,
        "ambient_intensity": 1,
        "angular_tolerance": 0.2,
        "axes": False,
        "axes0": True,
        "black_edges": False,
        "center_grid": False,
        "collapse": "1",
        "control": "trackball",
        "default_color": "#e8b024",
        "default_edgecolor": "#707070",
        "default_facecolor": "Violet",
        "default_opacity": 0.5,
        "default_thickedgecolor": "MediumOrchid",
        "default_vertexcolor": "MediumOrchid",
        "deviation": 0.1,
        "direct_intensity": 1.1,
        "explode": False,
        "glass": True,
        "grid": [False, False, False],
        "metalness": 0.3,
        "modifier_keys": {
            "shift": "shiftKey",
            "ctrl": "ctrlKey",
            "meta": "metaKey",
        },
        "new_tree_behavior": True,
        "ortho": True,
        "pan_speed": 1,
        "reset_camera": "reset",
        "rotate_speed": 1,
        "roughness": 0.65,
        "ticks": 10,
        "tools": True,
        "transparent": False,
        "tree_width": 240,
        "up": "Z",
        "zoom_speed": 1,
    }


def get_user_defaults():
    global WORKSPACE_DEFAULTS
    if WORKSPACE_DEFAULTS is None:
        path = Path("~/.jcq_config").expanduser()
        if path.exists():
            with open(path, "r") as fd:
                WORKSPACE_DEFAULTS = workspace_defaults()
                try:
                    config = safe_load(fd)
                    WORKSPACE_DEFAULTS.update(config)
                except:
                    print(f"Error: Cannot parse {path}")
                    WORKSPACE_DEFAULTS = workspace_defaults()
        else:
            WORKSPACE_DEFAULTS = workspace_defaults()
    return dict(WORKSPACE_DEFAULTS)


def save_user_defaults():
    path = Path("~/.jcq_config").expanduser()
    config = dict(WORKSPACE_DEFAULTS)

    del config["_splash"]
    with open(path, "w") as fd:
        fd.write(safe_dump(config))
        print(f"Wrote config {path}")
