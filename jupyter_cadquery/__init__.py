from ._version import version_info, __version__

from .cad_objects import Assembly, Part, Edges, Faces, convert

from .image_button import ImageButton
from .tree_view import TreeView, UNSELECTED, SELECTED, MIXED, EMPTY, state_diff
from .cad_view import CadqueryView
from .display import CadqueryDisplay

def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'jupyter_cadquery',
        'require': 'jupyter_cadquery/extension'
    }]
