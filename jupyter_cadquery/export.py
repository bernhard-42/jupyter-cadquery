import cadquery
from cadquery import Compound
import jupyter_cadquery.cadquery as jcq_cq


def exportSTL(cadObj, filename, precision=0.001):
    compound = None
    if isinstance(cadObj, cadquery.Shape):
        compound = Compound.makeCompound(cadObj.objects)
    elif isinstance(cadObj, cadquery.Workplane):
        compound = Compound.makeCompound(cadObj.objects)
    elif isinstance(cadObj, jcq_cq.Assembly):
        compound = cadObj.compound()
    elif isinstance(cadObj, jcq_cq.Part):
        compound = cadObj.compound()
    else:
        print("Unknown CAD object", type(cadObj))

    if compound is not None:
        compound.exportStl(filename, precision=precision)
