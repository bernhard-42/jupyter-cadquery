from collections import OrderedDict as odict
from math import cos, sin

import numpy as np

import cadquery as cq
from cadquery_massembly import MAssembly, relocate
from jupyter_cadquery.viewer.client import show
from jupyter_cadquery import web_color, set_defaults
from jupyter_cadquery.animation import Animation

set_defaults(axes0=True, mate_scale=4)

r_disk = 100
dist_pivot = 200

thickness = 5
nr = 5

disk = cq.Workplane().circle(r_disk + 2 * nr).extrude(thickness)
nipple = cq.Workplane().circle(nr).extrude(thickness)
disk = disk.cut(nipple).union(nipple.translate((r_disk, 0, thickness)))

pivot_base = cq.Workplane().circle(2 * nr).extrude(thickness)
base = (
    cq.Workplane()
    .rect(6 * nr + dist_pivot, 6 * nr)
    .extrude(thickness)
    .translate((dist_pivot / 2, 0, 0))
    .union(nipple.translate((dist_pivot, 0, thickness)))
    .union(pivot_base.translate((0, 0, thickness)))
    .union(nipple.translate((0, 0, 2 * thickness)))
    .edges("|Z")
    .fillet(3)
)
base.faces(">Z[-2]").wires(cq.NearestToPointSelector((dist_pivot + r_disk, 0))).tag("mate")

slot = (
    cq.Workplane()
    .rect(2 * r_disk, 2 * nr)
    .extrude(thickness)
    .union(nipple.translate((-r_disk, 0, 0)))
    .union(nipple.translate((r_disk - 1e-9, 0, 0)))
    .translate((dist_pivot, 0, 0))
)

arm = (
    cq.Workplane()
    .rect(4 * nr + (r_disk + dist_pivot), 4 * nr)
    .extrude(thickness)
    .edges("|Z")
    .fillet(3)
    .translate(((r_disk + dist_pivot) / 2, 0, 0))
    .cut(nipple)
    .cut(slot)
)
arm.faces(">Z").wires(cq.NearestToPointSelector((0, 0))).tag("mate")


def create_disk_arm():
    L = lambda *args: cq.Location(cq.Vector(*args))
    C = lambda name: web_color(name)

    return (
        MAssembly(base, name="base", color=C("silver"), loc=L(-dist_pivot / 2, 0, 0))
        .add(disk, name="disk", color=C("MediumAquaMarine"), loc=L(r_disk, -1.5 * r_disk, 0))
        .add(arm, name="arm", color=C("orange"), loc=L(0, 10 * nr, 0))
    )


disk_arm = create_disk_arm()

disk_arm.mate("base?mate", name="disk_pivot", origin=True, transforms=odict(rz=180))
disk_arm.mate("base@faces@>Z", name="arm_pivot")
disk_arm.mate("disk@faces@>Z[-2]", name="disk", origin=True)
disk_arm.mate("arm?mate", name="arm", origin=True)

relocate(disk_arm)

# show(disk_arm)

disk_arm.assemble("arm", "arm_pivot")
disk_arm.assemble("disk", "disk_pivot")

show(disk_arm, reset_camera=True)

r_disk = 100
dist_pivot = 200


def angle_arm(angle_disk):
    ra = np.deg2rad(angle_disk)
    v = np.array((dist_pivot, 0)) - r_disk * np.array((cos(ra), sin(ra)))
    return np.rad2deg(np.arctan2(*v[::-1]))


animation = Animation()

times = np.linspace(0, 5, 181)
disk_angles = np.linspace(0, 360, 181)
arm_angles = [angle_arm(d) for d in disk_angles]

# move disk
# Note, the selector must follow the path in the CAD view navigation hierarchy
animation.add_track("/base/disk", "rz", times, disk_angles)

# move arm
animation.add_track("/base/arm", "rz", times, arm_angles)

animation.animate(speed=2)
