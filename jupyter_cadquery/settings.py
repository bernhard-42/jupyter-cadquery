"""The workspace settings this host stores, and the file they live in."""

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
        # The name, not the "1"/"E"/"C"/"R" shorthand. The widget still speaks
        # letters and still gets one - `_collapse_to_letter` turns the enum the
        # core resolves this to back into "1" - so this is the vocabulary a
        # user's config file is written in, aligned with the other three hosts.
        # An existing ~/.jcq_config keeps working: the mapping takes both.
        "collapse": "leaves",
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
        # 12, as the standalone stores and as the core's VIEWER_DEFAULTS say.
        # The renderer's own default is 10, so leaving this unstored did not
        # mean "follow the renderer" - it meant this host silently disagreed
        # with the other two about how big a grid label is.
        "grid_font_size": 12,
        "metalness": 0.3,
        "modifier_keys": {
            "shift": "shiftKey",
            "ctrl": "ctrlKey",
            "meta": "metaKey",
            # The other two hosts ship four keys and the standalone even
            # patches `alt` into config files written before it existed. This
            # host's own default was still the three-key form - moot while
            # `modifier_keys` reached nothing here, and not moot now that it
            # does.
            "alt": "altKey",
        },
        "new_tree_behavior": True,
        "ortho": True,
        "pan_speed": 1,
        "reset_camera": "KEEP",
        "rotate_speed": 1,
        "roughness": 0.65,
        "ticks": 5,
        # Stored like every other viewer setting, rather than left out. `theme`
        # became a first-class config key when `dark` was retired, and this
        # host was the only one with nowhere to keep it - so a notebook user's
        # choice could not survive the session. "browser" keeps the previous
        # behaviour as the default: follow the notebook, until told otherwise.
        "theme": "browser",
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
