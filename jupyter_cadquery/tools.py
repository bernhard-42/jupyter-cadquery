import html

import numpy as np
import cadquery as cq

from jupyter_cadquery import Part, PartGroup, Faces, Edges, Vertices, show
from jupyter_cadquery.cad_objects import to_assembly
from jupyter_cadquery.base import _tessellate_group
from .utils import numpy_to_json

# pylint: disable=protected-access
# pylint: disable=unnecessary-lambda
def auto_show():
    PartGroup._ipython_display_ = lambda self: self.show()
    Part._ipython_display_ = lambda self: self.show()
    Faces._ipython_display_ = lambda self: self.show(grid=None, axes=False)
    Edges._ipython_display_ = lambda self: self.show(grid=None, axes=False)
    Vertices._ipython_display_ = lambda self: self.show(grid=None, axes=False)

    print("Overwriting auto display for cadquery Workplane and Shape")

    try:
        del cq.Workplane._repr_html_  # pylint: disable=no-member
        del cq.Shape._repr_html_  # pylint: disable=no-member
    except:  # pylint: disable=bare-except
        pass
    cq.Workplane._ipython_display_ = lambda cad_obj: show(cad_obj)
    cq.Shape._ipython_display_ = lambda cad_obj: show(cad_obj)
    cq.Assembly._ipython_display_ = lambda cad_obj: show(cad_obj)
    cq.Sketch._ipython_display_ = lambda cad_obj: show(cad_obj)


def show_constraints(assy, qs):
    colors = [
        "#e41a1c",
        "#377eb8",
        "#4daf4a",
        "#984ea3",
        "#ff7f00",
        "#ffff33",
        "#a65628",
        "#f781bf",
        "#999999",
        "#8dd3c7",
        "#ffffb3",
        "#bebada",
        "#fb8072",
        "#80b1d3",
        "#fdb462",
        "#b3de69",
        "#fccde5",
        "#d9d9d9",
    ]

    constraints = []
    objects = []
    cache = {}

    for i, q1q2 in enumerate(qs):
        parts = []

        kind = q1q2[-1]

        if len(q1q2) == 3:
            q1q2 = ((q1q2[0].split("@")[0], q1q2[0]), (q1q2[1].split("@")[0], q1q2[1]))
        else:
            q1q2 = (q1q2[0:2], q1q2[2:4])

        for q in q1q2:
            name, shape = q
            if name in cache:
                obj = cache[name]["obj"]
                loc = cache[name]["loc"]
            else:
                obj = assy.objects[name].obj
                loc = assy.objects[name].loc

                parent = assy.objects[name].parent
                while parent is not None:
                    loc = parent.loc * loc
                    parent = parent.parent

                cache[name] = {"obj": obj, "loc": loc, "shape": shape}

                objects.append(Part(cq.Workplane(obj.val().located(loc)), name=name, show_faces=False))

            label = str(shape)
            if isinstance(shape, str):
                shape = assy._query(shape)[1]

            parts.append(
                Faces(
                    cq.Workplane(cq.Workplane(shape).val().located(loc)),
                    name=html.escape(label),
                    color=colors[i % len(colors)],
                )
            )
        constraints.append(PartGroup(parts, "%s_%d" % (kind, i)))

    show(PartGroup([PartGroup(objects, "objects")] + constraints), axes=True, axes0=True)


def show_accuracy(assy, cs):
    def relocate(name, shape):
        a = assy.objects[name]
        loc = a.loc

        parent = a.parent
        while parent is not None:
            loc = parent.loc * loc
            parent = parent.parent

        if isinstance(shape, str):
            shape = assy._query(shape)[1]
        return cq.Workplane(cq.Workplane(shape).val().located(loc))

    def center(face):
        c = face.Center()
        return np.array((c.x, c.y, c.z))

    def normal(face):
        n = face.normalAt()
        return np.array((n.x, n.y, n.z))

    def print_metric(results):
        l = max([len(r[1]) for r in results])
        h = ("Constraint", "Normal-Dist", "Normal-Angle", "Point-Dist")
        print(f"{h[0]:{l+7}s} {h[1]:12s}  {h[2]:12s}  {h[3]:12s}")
        print("-" * (l + 46))
        for kind, label, nrm_dist, nrm_angle, pnt_dist in results:
            metric = f"{kind:5s} {label:{l}s} "
            metric += " " * 27 if nrm_dist is None else f"{nrm_dist:12.9f}  {nrm_angle:12.8}°"
            metric += " " * 13 if pnt_dist is None else f"{pnt_dist:12.9f}"
            print(metric)

    results = []
    for q1q2 in cs:
        kind = q1q2[-1]

        if len(q1q2) == 3:
            n_q1q2 = ((q1q2[0].split("@")[0], q1q2[0]), (q1q2[1].split("@")[0], q1q2[1]))
            label = "%s - %s" % q1q2[:2]
        else:
            n_q1q2 = (q1q2[0:2], q1q2[2:4])
            label = "%s<%s> - %s<%s>" % (q1q2[0], q1q2[1].__class__.__name__, q1q2[2], q1q2[3].__class__.__name__)

        shape1 = relocate(*n_q1q2[0])
        shape2 = relocate(*n_q1q2[1])

        pnt_dist = None
        nrm_dist = None
        nrm_angle = None

        if kind in ["Point", "Plane"]:
            c1, c2 = center(shape1.val()), center(shape2.val())
            pnt_dist = np.linalg.norm(c1 - c2)
        if kind in ["Axis", "Plane"]:
            n1, n2 = normal(shape1.val()), normal(shape2.val())
            nrm_dist = np.linalg.norm(n1 + n2)  # distance between n1 and -n2 since n1 and n2 point opposite
            c = np.dot(n1, -n2) / np.linalg.norm(n1) / np.linalg.norm(n2)
            nrm_angle = np.arccos(np.clip(c, -1, 1)) / np.pi * 180

        results.append((kind, label, nrm_dist, nrm_angle, pnt_dist))

    print_metric(results)


def cq_to_json(obj, indent=None):
    shapes, states = _tessellate_group(to_assembly(obj), {}, None, False)
    return [numpy_to_json(shapes, indent=indent), states]
