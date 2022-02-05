import numpy as np

import cadquery as cq
from cadquery_massembly import MAssembly, relocate
from jupyter_cadquery import web_color
from jupyter_cadquery.viewer.client import show
from jupyter_cadquery.animation import Animation

# Parts

thickness = 2
height = 40
width = 65
length = 100
diam = 4
tol = 0.05


def create_base(rotate=False):
    x1, x2 = 0.63, 0.87
    base_holes = {
        "right_back": (-x1 * length, -x1 * width),
        "right_middle": (0, -x2 * width),
        "right_front": (x1 * length, -x1 * width),
        "left_back": (-x1 * length, x1 * width),
        "left_middle": (0, x2 * width),
        "left_front": (x1 * length, x1 * width),
    }
    stand_holes = {"front_stand": (0.75 * length, 0), "back_stand": (-0.8 * length, 0)}

    workplane = cq.Workplane()
    if rotate:
        workplane = workplane.transformed(rotate=(30, 45, 60))

    base = (
        workplane.ellipseArc(length, width, 25, -25, startAtCurrent=False)
        .close()
        .pushPoints(list(base_holes.values()))
        .circle(diam / 2 + tol)
        .moveTo(*stand_holes["back_stand"])
        .rect(thickness + 2 * tol, width / 2 + 2 * tol)
        .moveTo(*stand_holes["front_stand"])
        .rect(thickness + 2 * tol, width / 2 + 2 * tol)
        .extrude(thickness)
    )
    base

    # tag mating points
    if rotate:
        l_coord = lambda vec2d: workplane.plane.toWorldCoords(vec2d).toTuple()
        l_nps = lambda vec2d: cq.NearestToPointSelector(l_coord(vec2d))

        base.faces(f"<{l_coord((0,0,1))}").tag("bottom")
        base.faces(f">{l_coord((0,0,1))}").tag("top")

        for name, hole in base_holes.items():
            base.faces(f"<{l_coord((0,0,1))}").edges(l_nps(hole)).tag(name)

        for name, hole in stand_holes.items():
            base.faces(f"<{l_coord((0,0,1))}").wires(l_nps(hole)).tag(name)
    else:
        base.faces("<Z").tag("bottom")
        base.faces(">Z").tag("top")

        for name, hole in base_holes.items():
            base.faces("<Z").wires(cq.NearestToPointSelector(hole)).tag(name)

        for name, hole in stand_holes.items():
            base.faces("<Z").wires(cq.NearestToPointSelector(hole)).tag(name)

    return base


base_holes_names = {
    "right_back",
    "right_middle",
    "right_front",
    "left_back",
    "left_middle",
    "left_front",
}


def create_stand():
    stand = cq.Workplane().box(height, width / 2 + 10, thickness)
    inset = cq.Workplane().box(thickness, width / 2, thickness)
    backing = cq.Workplane("ZX").polyline([(10, 0), (0, 0), (0, 10)]).close().extrude(thickness)

    stand = (
        stand.union(inset.translate(((height + thickness) / 2, 0, 0)))
        .union(inset.translate((-(height + thickness) / 2, 0, 0)))
        .union(backing.translate((-height / 2, -thickness / 2, thickness / 2)))
        .union(backing.rotate((0, 0, 0), (0, 1, 0), -90).translate((height / 2, -thickness / 2, thickness / 2)))
    )
    return stand


stand_names = ("front_stand", "back_stand")


def create_upper_leg():
    l1, l2 = 50, 80
    pts = [(0, 0), (0, height / 2), (l1, height / 2 - 5), (l2, 0)]
    upper_leg_hole = (l2 - 10, 0)

    upper_leg = (
        cq.Workplane()
        .polyline(pts)
        .mirrorX()
        .pushPoints([upper_leg_hole])
        .circle(diam / 2 + tol)
        .extrude(thickness)
        .edges("|Z and (not <X)")
        .fillet(4)
    )

    axle = (
        cq.Workplane("XZ", origin=(0, height / 2 + thickness + tol, thickness / 2))
        .circle(diam / 2)
        .extrude(2 * (height / 2 + thickness + tol))
    )

    upper_leg = upper_leg.union(axle)

    # tag mating points
    upper_leg.faces(">Z").edges(cq.NearestToPointSelector(upper_leg_hole)).tag("top")
    upper_leg.faces("<Z").edges(cq.NearestToPointSelector(upper_leg_hole)).tag("bottom")

    return upper_leg


def create_lower_leg():
    w, l1, l2 = 15, 20, 120
    pts = [(0, 0), (l1, w), (l2, 0)]
    lower_leg_hole = (l1 - 10, 0)

    lower_leg = (
        cq.Workplane()
        .polyline(pts)
        .mirrorX()
        .pushPoints([lower_leg_hole])
        .circle(diam / 2 + tol)
        .extrude(thickness)
        .edges("|Z")
        .fillet(5)
    )

    # tag mating points
    lower_leg.faces(">Z").edges(cq.NearestToPointSelector(lower_leg_hole)).tag("top"),
    lower_leg.faces("<Z").edges(cq.NearestToPointSelector(lower_leg_hole)).tag("bottom")

    return lower_leg


leg_angles = {
    "right_back": -105,
    "right_middle": -90,
    "right_front": -75,
    "left_back": 105,
    "left_middle": 90,
    "left_front": 75,
}
leg_names = list(leg_angles.keys())


base = create_base(rotate=False)
stand = create_stand()
upper_leg = create_upper_leg()
lower_leg = create_lower_leg()


# Assembly


def create_hexapod():
    # Some shortcuts
    L = lambda *args: cq.Location(cq.Vector(*args))
    C = lambda name: web_color(name)

    # Leg assembly
    leg = MAssembly(upper_leg, name="upper", color=C("orange")).add(
        lower_leg, name="lower", color=C("orange"), loc=L(80, 0, 0)
    )
    # Hexapod assembly
    hexapod = (
        MAssembly(base, name="bottom", color=C("silver"), loc=L(0, 1.1 * width, 0))
        .add(base, name="top", color=C("gainsboro"), loc=L(0, -2.2 * width, 0))
        .add(stand, name="front_stand", color=C("SkyBlue"), loc=L(40, 100, 0))
        .add(stand, name="back_stand", color=C("SkyBlue"), loc=L(-40, 100, 0))
    )

    for i, name in enumerate(leg_names):
        hexapod.add(leg, name=name, loc=L(100, -55 * (i - 1.7), 0))

    return hexapod


# Mates

from collections import OrderedDict as odict

hexapod = create_hexapod()
# show(hexapod)

hexapod.mate("bottom?top", name="bottom", origin=True)
hexapod.mate("top?bottom", name="top", origin=True, transforms=odict(rx=180, tz=-(height + 2 * tol)))

for name in stand_names:
    hexapod.mate(f"bottom?{name}", name=f"{name}_bottom", transforms=odict(rz=-90 if "f" in name else 90))
    hexapod.mate(f"{name}@faces@<X", name=name, origin=True, transforms=odict(rx=180))

for name in base_holes_names:
    hexapod.mate(f"bottom?{name}", name=f"{name}_hole", transforms=odict(rz=leg_angles[name]))

for name in leg_names:
    lower, upper, angle = ("top", "bottom", -75) if "left" in name else ("bottom", "top", -75)
    hexapod.mate(f"{name}?{upper}", name=f"leg_{name}_hole", transforms=odict(rz=angle))
    hexapod.mate(f"{name}@faces@<Y", name=f"leg_{name}_hinge", origin=True, transforms=odict(rx=180, rz=-90))
    hexapod.mate(f"{name}/lower?{lower}", name=f"leg_{name}_lower_hole", origin=True)

# show(hexapod, reset_camera=False)
relocate(hexapod)

# Assemble the parts
for leg in leg_names:
    hexapod.assemble(f"leg_{leg}_lower_hole", f"leg_{leg}_hole")
    hexapod.assemble(f"leg_{leg}_hinge", f"{leg}_hole")

hexapod.assemble("top", "bottom")

for stand_name in stand_names:
    hexapod.assemble(f"{stand_name}", f"{stand_name}_bottom")

show(hexapod, render_mates=True, mate_scale=5)

# Animation

horizontal_angle = 25


def intervals(count):
    r = [min(180, (90 + i * (360 // count)) % 360) for i in range(count)]
    return r


def times(end, count):
    return np.linspace(0, end, count + 1)


def vertical(count, end, offset, reverse):
    ints = intervals(count)
    heights = [round(35 * np.sin(np.deg2rad(x)) - 15, 1) for x in ints]
    heights.append(heights[0])
    return times(end, count), heights[offset:] + heights[1 : offset + 1]


def horizontal(end, reverse):
    factor = 1 if reverse else -1
    return times(end, 4), [0, factor * horizontal_angle, 0, -factor * horizontal_angle, 0]


leg_group = ("left_front", "right_middle", "left_back")

animation = Animation()

for name in leg_names:
    # move upper leg
    animation.add_track(f"/bottom/{name}", "rz", *horizontal(4, "middle" in name))

    # move lower leg
    animation.add_track(f"/bottom/{name}/lower", "rz", *vertical(8, 4, 0 if name in leg_group else 4, "left" in name))

    # lift hexapod to run on grid
    # animation.add_track(f"bottom", "tz", [0, 4], [61.25] * 2)

animation.animate(speed=3)
