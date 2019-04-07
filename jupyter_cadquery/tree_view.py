from traitlets import Unicode, List, Dict

from ipywidgets.widgets import register, Button
from ipywidgets.widgets.trait_types import bytes_serialization


@register
class Tree(Button):
    """An example widget."""
    _view_name = Unicode('TreeView').tag(sync=True)
    _model_name = Unicode('TreeModel').tag(sync=True)
    _view_module = Unicode('jupyter_cadquery').tag(sync=True)
    _model_module = Unicode('jupyter_cadquery').tag(sync=True)
    _view_module_version = Unicode('^0.1.0').tag(sync=True)
    _model_module_version = Unicode('^0.1.0').tag(sync=True)
    icons = List(Dict(None, allow_none=True)).tag(sync=True)
    tree = Dict(None, allow_none=True).tag(sync=True)
    state = Dict(None, allow_none=True).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
