from traitlets import Unicode, validate, CUnicode, Bytes

from ipywidgets.widgets import register, Button
from ipywidgets.widgets.trait_types import bytes_serialization


@register
class ImageButton(Button):
    """An example widget."""
    _view_name = Unicode('ImageButtonView').tag(sync=True)
    _model_name = Unicode('ImageButtonModel').tag(sync=True)
    _view_module = Unicode('jupyter_cadquery').tag(sync=True)
    _model_module = Unicode('jupyter_cadquery').tag(sync=True)
    _view_module_version = Unicode('^0.1.0').tag(sync=True)
    _model_module_version = Unicode('^0.1.0').tag(sync=True)
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
