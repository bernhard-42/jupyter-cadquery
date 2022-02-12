import cadquery as cq
from cadquery_massembly import MAssembly, relocate
from jupyter_cadquery.viewer.client import show
from jupyter_cadquery import web_color
from jupyter_cadquery.animation import Animation

# Jansen Linkage

import math
import numpy as np

Vec = lambda x, y: np.array((x, y))


def intersect(p0, r0, p1, r1):
    """
    Bourke's algorithm (http://paulbourke.net/geometry/circlesphere)
    to find intersect points of circle0 (p0, r0) and circle1 (p1, r1)
    """
    p10 = p1 - p0
    d = np.linalg.norm(p10)
    if (d > r0 + r1) or (d < abs(r1 - r0)) or ((d == 0) and (r0 == r1)):
        return None

    a = (r0 ** 2 - r1 ** 2 + d ** 2) / (2 * d)
    h = np.sqrt(r0 ** 2 - a ** 2)
    p2 = p0 + (a / d) * p10
    r = Vec(-p10[1], p10[0]) * (h / d)

    return (p2 - r, p2 + r)


def link_loc(name, joints, links):
    p1_index, p2_index = name.split("_")[1:]
    p1 = joints[int(p1_index)]
    p2 = joints[int(p2_index)]
    a = math.degrees(math.atan2(p1[1] - p2[1], p1[0] - p2[0]))
    return (np.array((links[name]["lev"], *p1)), a)


def linkage(alpha, x, y, links):
    """For a given angle return the 2d location of each joint"""
    p0 = Vec(0, 0)
    p1 = Vec(x, y)
    p2 = p1 + links["link_1_2"]["len"] * Vec(np.cos(np.deg2rad(alpha)), np.sin(np.deg2rad(alpha)))
    p3 = intersect(p0, links["link_0_3"]["len"], p2, links["link_2_3"]["len"])[1]
    p4 = intersect(p0, links["link_4_0"]["len"], p3, links["link_3_4"]["len"])[1]
    p5 = intersect(p0, links["link_0_5"]["len"], p2, links["link_2_5"]["len"])[0]
    p6 = intersect(p4, links["link_4_6"]["len"], p5, links["link_5_6"]["len"])[0]
    p7 = intersect(p5, links["link_7_5"]["len"], p6, links["link_6_7"]["len"])[1]
    return (p0, p1, p2, p3, p4, p5, p6, p7)


height = 2
x = 38.0
y = 7.8

links = {}
links["link_1_2"] = {"len": 15.0, "lev": 3 * height, "col": "DarkBlue"}
links["link_2_3"] = {"len": 50.0, "lev": 4 * height, "col": "DarkGreen"}
links["link_3_4"] = {"len": 55.8, "lev": 3 * height, "col": "Red"}
links["link_4_0"] = {"len": 40.1, "lev": 1 * height, "col": "Red"}
links["link_0_3"] = {"len": 41.5, "lev": 2 * height, "col": "Red"}
links["link_4_6"] = {"len": 39.4, "lev": 2 * height, "col": "Purple"}
links["link_0_5"] = {"len": 39.3, "lev": 3 * height, "col": "OliveDrab"}
links["link_2_5"] = {"len": 61.9, "lev": 1 * height, "col": "Orange"}
links["link_5_6"] = {"len": 36.7, "lev": 0 * height, "col": "RoyalBlue"}
links["link_6_7"] = {"len": 65.7, "lev": 1 * height, "col": "RoyalBlue"}
links["link_7_5"] = {"len": 49.0, "lev": 2 * height, "col": "RoyalBlue"}

link_list = list(links.keys())


# Parts


def make_link(length, width=2, height=1):
    link = (
        cq.Workplane("YZ")
        .rect(length + 4, width + 2)
        .pushPoints(((-length / 2, 0), (length / 2, 0)))
        .circle(1)
        .extrude(height)
        .edges("|X")
        .fillet(1.99)
    )
    link.faces(">X").wires(cq.NearestToPointSelector((0, length / 2))).tag("mate")
    return link


parts = {
    name: make_link(links[name]["len"], height=(2 * height if name == "link_1_2" else height)) for name in link_list
}


# Assembly


def create_leg(x, y):
    L = lambda *args: cq.Location(cq.Vector(*args))
    C = lambda name: web_color(name)

    leg = MAssembly(cq.Workplane("YZ").polyline([(0, 0), (x, 0), (x, y)]), name="base", color=C("Gray"))
    for i, name in enumerate(link_list):
        leg.add(parts[name], name=name, color=C(links[name]["col"]), loc=L(0, 0, i * 10 - 50))
    return leg


leg = create_leg(x, y)

# Mates

for name in link_list:
    leg.mate(f"{name}?mate", name=name, origin=True)

# Relocate
relocate(leg)

# Assemble the parts
alpha = 0
joints = linkage(alpha, x, y, links)

for name in link_list:
    v, a = link_loc(name, joints, links)
    abs_loc = cq.Location(
        cq.Workplane("YZ").plane.rotated((0, 0, a)), cq.Vector(*v)
    )  # calculate the absolute location ...
    loc = abs_loc * leg.mates[name].mate.loc.inverse  # ... and center the mate of the link first
    leg.assemble(name, loc)

cv = show(leg)


alphas = {name: [] for name in link_list}
positions = {name: [] for name in link_list}

for alpha in range(0, -375, -15):
    for name in link_list:
        p, a = link_loc(name, linkage(alpha, x, y, links), links)
        alphas[name].append(a)
        positions[name].append(p)

time = np.linspace(0, 4, 25)

animation = Animation(cv)

for name in link_list:
    animation.add_track(f"/base/{name}", "t", time, [(p - positions[name][0]).tolist() for p in positions[name]])
    animation.add_track(f"/base/{name}", "rz", time, [a - alphas[name][0] for a in alphas[name]])

animation.animate(2)