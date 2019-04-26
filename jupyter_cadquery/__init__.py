from ._version import version_info, __version__

from .cad_objects import Assembly, Part, Edges, Faces, display

from .image_button import ImageButton
from .tree_view import TreeView, UNSELECTED, SELECTED, MIXED, EMPTY, state_diff
from .cad_display import CadqueryDisplay

from cadquery import Workplane


def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'jupyter_cadquery',
        'require': 'jupyter_cadquery/extension'
    }]


print("Overwriting auto display for cadquery Workplane and Shape")

def _cadquery_display_(obj):
    from IPython.display import display as idisplay
    idisplay(display(obj))

from cadquery import Workplane, Shape
try:
    del Workplane._repr_html_
    del Shape._repr_html_
except:
    pass

Workplane._ipython_display_ = _cadquery_display_
Shape._ipython_display_ = _cadquery_display_
