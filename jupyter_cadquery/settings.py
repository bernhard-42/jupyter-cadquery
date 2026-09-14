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

import sys
from pathlib import Path

from yaml import safe_dump, safe_load

WORKSPACE_DEFAULTS = None

__all__ = ["get_user_defaults", "save_user_defaults"]


DEFAULT_MODIFIER_KEYS = {
    "macOS": {"shift": "shiftKey", "ctrl": "ctrlKey", "meta": "metaKey", "alt": "altKey"},
    "default": {"shift": "shiftKey", "ctrl": "ctrlKey", "meta": "altKey", "alt": "metaKey"},
}


def resolve_modifier_keys(value, platform=None):
    """The stored map for this machine's operating system.

    The stored value is one map per platform, `{"macOS": ..., "default": ...}`,
    so that whoever opens the file sees which platform gets what - the shape
    build123d Studio and the VS Code extension store. `meta` rotates, hides
    and isolates, and `metaKey` is Cmd on macOS but the Win/Super key on
    Windows and Linux, which the desktop takes for itself (the Start menu,
    window snapping, moving windows) - those chords never reach the page, so
    there `meta` and `alt` swap physical keys. A flat map, the shape of a file
    written by an earlier release, is taken as it is on every platform.
    """
    if not isinstance(value, dict) or ("default" not in value and "macOS" not in value):
        return value
    platform = sys.platform if platform is None else platform
    if platform == "darwin" and value.get("macOS") is not None:
        return dict(value["macOS"])
    return dict(value.get("default", value.get("macOS")))


def upgrade_modifier_keys(value, platform=None):
    """A flat map from an older file, lifted into the per-platform shape.

    The flat map is what the user chose on the machine that wrote the file,
    so it goes under that machine's platform; the other platform gets the
    shipped default. Written back that way, the file then works on both. A
    value already in the per-platform shape is returned as it is.
    """
    if not isinstance(value, dict) or "default" in value or "macOS" in value:
        return value
    platform = sys.platform if platform is None else platform
    upgraded = {key: dict(keys) for key, keys in DEFAULT_MODIFIER_KEYS.items()}
    upgraded["macOS" if platform == "darwin" else "default"] = dict(value)
    return upgraded


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
        "modifier_keys": dict(DEFAULT_MODIFIER_KEYS),
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
                    # A file from an earlier release holds one flat map; the
                    # next `save_user_defaults` writes it per platform.
                    WORKSPACE_DEFAULTS["modifier_keys"] = upgrade_modifier_keys(
                        WORKSPACE_DEFAULTS.get("modifier_keys")
                    )
                except:
                    print(f"Error: Cannot parse {path}")
                    WORKSPACE_DEFAULTS = workspace_defaults()
        else:
            WORKSPACE_DEFAULTS = workspace_defaults()
    # The file keeps one map per platform; the viewer gets this platform's.
    config = dict(WORKSPACE_DEFAULTS)
    config["modifier_keys"] = resolve_modifier_keys(config.get("modifier_keys"))
    return config


def save_user_defaults():
    path = Path("~/.jcq_config").expanduser()
    config = dict(WORKSPACE_DEFAULTS)

    del config["_splash"]
    with open(path, "w") as fd:
        fd.write(safe_dump(config))
        print(f"Wrote config {path}")
