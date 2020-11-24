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

try:
    import cqparts
    from cqparts.display.material import COLOR
    from cqparts.utils.geometry import CoordSystem

    has_cqparts = True
except:
    has_cqparts = False

import jupyter_cadquery as jcq


def is_cqparts_assembly(cad_obj):
    return has_cqparts and has_cqparts and isinstance(cad_obj, cqparts.Assembly)


def is_cqparts_part(cad_obj):
    return has_cqparts and has_cqparts and isinstance(cad_obj, cqparts.Part)


def is_cqparts(cad_obj):
    return is_cqparts_assembly(cad_obj) or is_cqparts_part(cad_obj)


def convert_cqparts(cad_obj, name="root", default_color=None, replay=False):
    cad_obj.world_coords = CoordSystem()
    return _convert_cqparts(cad_obj, name, default_color, replay)


def _convert_cqparts(cad_obj, name, default_color, replay):
    if default_color is None:
        default_color = (255, 255, 0)

    if isinstance(cad_obj, cqparts.Assembly):
        parts = []
        for k, v in cad_obj._components.items():
            parts.append(_convert_cqparts(v, k, default_color, replay))
        return jcq.cadquery.PartGroup(parts, name)

    elif isinstance(cad_obj, cqparts.Part):
        if replay:
            return cad_obj.world_obj
        else:
            color = cad_obj._render.color
            if isinstance(color, (list, tuple)):
                pass
            elif isinstance(color, str):
                color = COLOR.get(color)
                if color is None:
                    color = default_color
            else:
                color = default_color
            color = tuple((c / 255.0 for c in color))
            return jcq.cadquery.Part(cad_obj.world_obj, name, color)
    else:
        print("No cqparts object")
        return None


def get_parts(cad_obj, name="root"):
    parts = {}
    if isinstance(cad_obj, cqparts.Assembly):
        for k, v in cad_obj._components.items():
            parts[k] = get_parts(v, k)
        return parts
    elif isinstance(cad_obj, cqparts.Part):
        return cad_obj.world_obj
