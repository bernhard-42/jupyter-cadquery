from collections import OrderedDict as odict
import cadquery as cq
from cadquery_massembly import MAssembly
from jupyter_cadquery.viewer.client import show
from jupyter_cadquery import web_color

# Note: Download https://www.matronics.dk/data/longship/files/products/vslot-2020_1.dxf first
# if you don't have it at hand

# Parameters
H = 400
W = 200
D = 350

PROFILE = cq.importers.importDXF("vslot-2020_1.dxf").wires()

SLOT_D = 6
PANEL_T = 3

HANDLE_D = 20
HANDLE_L = 50
HANDLE_W = 4


def make_vslot(l):

    return PROFILE.toPending().extrude(l)


def make_connector():

    rv = (
        cq.Workplane()
        .box(20, 20, 20)
        .faces("<X")
        .workplane()
        .cboreHole(6, 15, 18)
        .faces("<Z")
        .workplane(centerOption="CenterOfMass")
        .cboreHole(6, 15, 18)
    )

    # tag mating faces
    rv.faces(">X").tag("X").end()
    rv.faces(">Z").tag("Z").end()

    return rv


def make_panel(w, h, t, cutout):

    rv = (
        cq.Workplane("XZ")
        .rect(w, h)
        .extrude(t)
        .faces(">Y")
        .vertices()
        .rect(2 * cutout, 2 * cutout)
        .cutThruAll()
        .faces("<Y")
        .workplane()
        .pushPoints([(-w / 3, HANDLE_L / 2), (-w / 3, -HANDLE_L / 2)])
        .hole(3)
    )

    # tag mating edges
    rv.faces(">Y").edges("%CIRCLE").edges(">Z").tag("hole1")
    rv.faces(">Y").edges("%CIRCLE").edges("<Z").tag("hole2")

    return rv


def make_handle(w, h, r):

    pts = ((0, 0), (w, 0), (w, h), (0, h))

    path = cq.Workplane().polyline(pts)

    rv = (
        cq.Workplane("YZ")
        .rect(r, r)
        .sweep(path, transition="round")
        .tag("solid")
        .faces("<X")
        .workplane()
        .faces("<X", tag="solid")
        .hole(r / 1.5)
    )

    # tag mating faces
    rv.faces("<X").faces(">Y").tag("mate1")
    rv.faces("<X").faces("<Y").tag("mate2")

    return rv


# Assembly

# Some shortcuts
L = lambda *args: cq.Location(cq.Vector(*args))
C = lambda *args: cq.Color(*args)

h_slot = make_vslot(H)
w_slot = make_vslot(W)
conn = make_connector()

# For visualisation of mate, spread elements by adding locs
def make_door():
    door = (
        MAssembly(name="door")  # add a name for hierarchical addressing
        .add(w_slot, name="bottom", color=web_color("silver"))
        .add(h_slot, name="left", loc=L(0, 40, 0), color=web_color("silver"))
        .add(h_slot, name="right", loc=L(0, 80, 0), color=web_color("silver"))
        .add(w_slot, name="top", loc=L(0, 120, 0), color=web_color("silver"))
        .add(conn, name="con_tl", color=web_color("black"), loc=L(0, 0, -40))
        .add(conn, name="con_tr", color=web_color("black"), loc=L(0, 40, -40))
        .add(conn, name="con_bl", color=web_color("black"), loc=L(0, 80, -40))
        .add(conn, name="con_br", color=web_color("black"), loc=L(0, 120, -40))
        .add(
            make_panel(W + 2 * SLOT_D, H + 2 * SLOT_D, PANEL_T, SLOT_D),
            name="panel",
            color=cq.Color(0, 0, 1, 0.2),
            loc=L(0, -40, H / 2),
        )
        .add(
            make_handle(HANDLE_D, HANDLE_L, HANDLE_W),
            name="handle",
            color=web_color("yellow"),
            loc=L(0, -150, 0),
        )
    )
    return door


door = make_door()

# Mates

# add mates to the ends of the vslots

for v in ["bottom", "left", "top", "right"]:
    door.mate(f"{v}@faces@>Z", name=f"{v}_0", transforms=odict(rx=0))
    door.mate(f"{v}@faces@<Z", name=f"{v}_1")

# add mates to the connectors
for c in ["con_tl", "con_tr", "con_br", "con_bl"]:
    door.mate(f"{c}?X", name=f"{c}_0", transforms=odict(rx=180))
    door.mate(f"{c}?Z", name=f"{c}_1", transforms=odict(rx=180))

# add mates to bottom vslot and panel
door.mate("panel@faces@<Z", name="panel_0", transforms=odict(rx=180, rz=90))
door.mate("bottom@faces@>X[-4]", name="panel_1")

# add mates to handle and one hole
door.mate("handle?mate1", name="handle_0", transforms=odict(rx=180))
door.mate("panel?hole1", name="handle_1")


check_mates = False
if check_mates:
    show(door)
else:
    # Assemble the parts
    door.assemble("bottom_0", "con_bl_0")  # add bottom vslot to bottom-left connector
    door.assemble("con_br_1", "bottom_1")  # add bottom-right connector to bottom vslot
    door.assemble("left_1", "con_bl_1")  # add left vslot to bottom-left connector
    door.assemble("right_0", "con_br_0")  # add right vslot to bottom-right connector
    door.assemble("panel_0", "panel_1")  # add panel
    door.assemble("con_tl_0", "left_0")  # add top-left connector to left vslot
    door.assemble("con_tr_1", "right_1")  # add top-right connector to right vslot
    door.assemble("top_1", "con_tl_1")  # add top vslot to top-left connector
    door.assemble("handle_0", "handle_1")  # add handle

    show(door)