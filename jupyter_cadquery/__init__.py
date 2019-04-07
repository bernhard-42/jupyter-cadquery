from ._version import version_info, __version__

from .image_button import *
from .tree_view import *

def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'jupyter_cadquery',
        'require': 'jupyter_cadquery/extension'
    }]
