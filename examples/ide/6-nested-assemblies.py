import cadquery as cq
from cadquery_massembly import MAssembly, Mate
from cadquery_massembly.cq_editor import show_mates


box0 = cq.Workplane("XY").box(10, 20, 10)
box1 = cq.Workplane("XZ").box(10, 20, 10)
box2 = cq.Workplane("YX").box(10, 20, 10)
box3 = cq.Workplane("YZ").box(10, 20, 10)

for box, name, dirs in (
    (box0, "box0", ("Y", "X")),
    (box1, "box1", ("Z", "X")),
    (box2, "box2", ("X", "Y")),
    (box3, "box3", ("Z", "Y")),
):
    for i, direction in enumerate(dirs):
        box.faces(f">{direction}").tag(f"{name}_m{i}")


cyl1 = cq.Workplane("XY").circle(2).extrude(10)
cyl2 = cq.Workplane("XZ").circle(2).extrude(10)
cyl3 = cq.Workplane("YZ").circle(2).extrude(10)

for cyl, name, ax in (
    (cyl1, "cyl1", "Z"),
    (cyl2, "cyl2", "Y"),
    (cyl3, "cyl3", "X"),
):
    cyl.faces(f">{ax}").tag(f"{name}_m0")
    cyl.faces(f"<{ax}").tag(f"{name}_m1")


# Assembly


def create():
    L = lambda *args: cq.Location(cq.Vector(*args))
    C = lambda *args: cq.Color(*args)

    a = MAssembly(cyl3, name="cyl3", color=C(1, 0, 0), loc=L(-20, -10, 20)).add(
        box3, name="box3", color=C(1, 0, 0), loc=L(20, 10, 0)
    )
    b = (
        MAssembly(cyl2, name="cyl2", color=C(0, 0.5, 0.25), loc=L(0, -20, 20))
        .add(box2, name="box2", color=C(0, 0.5, 0.25), loc=L(0, 20, 20))
        .add(a, name="a")
    )
    c = (
        MAssembly(cyl1, name="cyl1", color=C(0, 0, 1), loc=L(10, 0, -10))
        .add(box1, name="box1", color=C(0, 0, 1), loc=L(10, 0, 10))
        .add(b, name="b")
    )
    d = MAssembly(box0, name="box0", color=C(0.5, 0.5, 0.5), loc=L(30, 30, 30)).add(c, name="c")
    return d


assy = create()


# Mates

from collections import OrderedDict as odict

assy = create()
for obj, name in (
    ("box0", "box0"),
    ("c/box1", "box1"),
    ("c/b/box2", "box2"),
    ("c/b/a/box3", "box3"),
    ("c", "cyl1"),
    ("c/b", "cyl2"),
    ("c/b/a", "cyl3"),
):
    assy.mate(
        f"{obj}?{name}_m0",
        name=f"{name}_m0",
        transforms=odict(rx=180 if "c" in name else 0),
        origin=True,
    )
    assy.mate(f"{obj}?{name}_m1", name=f"{name}_m1", transforms=odict(rx=0 if "b" in name else 180))


check_mates = True
if check_mates:
    show_object(assy, name="assy")
    show_mates(assy, show_object, length=2)
else:
    # Assemble the parts
    assy.assemble("cyl1_m0", "box0_m0")
    assy.assemble("box1_m1", "cyl1_m1")
    assy.assemble("cyl2_m0", "box1_m0")
    assy.assemble("box2_m1", "cyl2_m1")
    assy.assemble("cyl3_m0", "box2_m0")
    assy.assemble("box3_m1", "cyl3_m1")

    show_object(assy)
