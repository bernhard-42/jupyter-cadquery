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

from traitlets import Unicode, validate, CUnicode, Bytes

from ipywidgets.widgets import register, Button
from ipywidgets.widgets.trait_types import bytes_serialization
from jupyter_cadquery._version import __version__, __npm_version__


@register
class ImageButton(Button):
    """An example widget."""
    _view_name = Unicode('ImageButtonView').tag(sync=True)
    _model_name = Unicode('ImageButtonModel').tag(sync=True)
    _view_module = Unicode('jupyter_cadquery').tag(sync=True)
    _model_module = Unicode('jupyter_cadquery').tag(sync=True)
    _view_module_version = Unicode('^%s' % __npm_version__).tag(sync=True)
    _model_module_version = Unicode('^%s' % __npm_version__).tag(sync=True)
    image_path = Unicode("")
    value = Bytes().tag(sync=True, **bytes_serialization)
    width = CUnicode("36", help="Width of the image in pixels.").tag(sync=True)
    height = CUnicode("28", help="Height of the image in pixels.").tag(sync=True)
    type = Unicode("").tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = self._load_image(self.image_path)

    def _load_image(self, image_path):
        if image_path == "":
            return b""
        else:
            return open(image_path, 'rb').read()
