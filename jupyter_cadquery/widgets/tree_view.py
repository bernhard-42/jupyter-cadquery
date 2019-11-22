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

import base64

from traitlets import Unicode, List, Dict

from ipywidgets.widgets import register, Button
from ipywidgets.widgets.trait_types import bytes_serialization

from jupyter_cadquery._version import __version__, __npm_version__

UNSELECTED = 0
SELECTED = 1
MIXED = 2
EMPTY = 3

def state_diff(old_states, new_states):
    result = []
    for key in old_states.keys():
        if old_states[key] != new_states[key]:
            for i in range(len(old_states[key])):
                if old_states[key][i] != new_states[key][i]:
                    result.append({key: {"icon": i, "new": new_states[key][i]}})
    return result

@register
class TreeView(Button):
    """An example widget."""
    _view_name = Unicode('TreeView').tag(sync=True)
    _model_name = Unicode('TreeModel').tag(sync=True)
    _view_module = Unicode('jupyter_cadquery').tag(sync=True)
    _model_module = Unicode('jupyter_cadquery').tag(sync=True)
    _view_module_version = Unicode('^%s' % __npm_version__).tag(sync=True)
    _model_module_version = Unicode('^%s' % __npm_version__).tag(sync=True)
    image_paths = List(Dict(None, allow_none=True))
    icons = List(Dict(None, allow_none=True)).tag(sync=True)
    tree = Dict(None, allow_none=True).tag(sync=True)
    state = Dict(None, allow_none=True).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        icons = []
        for image_set in self.image_paths:
            icons.append({k:self._load_image(v) for k,v in image_set.items()})
        self.icons = icons

    def _load_image(self, image_path):
        if image_path == "":
            return b""
        else:
            return base64.b64encode(open(image_path, 'rb').read()).decode()
