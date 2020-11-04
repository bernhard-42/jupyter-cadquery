import itertools
import numpy as np
from typing import Union, List, cast

from cadquery import Workplane, Location, Edge
from pythreejs import (
    Group,
    CombinedCamera,
    DirectionalLight,
    AmbientLight,
    Scene,
    OrbitControls,
    BufferAttribute,
    BufferGeometry,
    Mesh,
    Renderer,
)
from jupyter_cadquery.cad_helpers import CustomMaterial
from jupyter_cadquery.utils import BoundingBox, flatten, tessellate
from jupyter_cadquery.cadquery import show, Assembly, Part
from .massembly import MAssembly
from ..utils import Color

MATE_COLOR = (Color((255, 0, 0)), Color((0, 128, 0)), Color((0, 0, 255)))


def to_edge(mate, loc=None, scale=4) -> Workplane:
    w = Workplane()
    for d in (mate.x_dir, mate.y_dir, mate.z_dir):
        edge = Edge.makeLine(mate.pnt, mate.pnt + d * scale)
        w.objects.append(edge if loc is None else edge.moved(loc))

    return w


def _convert(assy, top: MAssembly, loc: Location = None, mates: bool = False):
    loc = assy.loc if loc is None else loc * assy.loc
    color = Color(assy.web_color)

    parent: List[Union[Part, Assembly]] = [
        Part(Workplane(shape.moved(loc)), "%s_%d" % (assy.name, i), color=color)
        for i, shape in enumerate(assy.shapes)
    ]

    if mates:
        if assy.matelist:
            parent.append(
                Assembly(
                    [
                        Part(
                            to_edge(top.mates[mate]["mate"].moved(loc)),
                            name=mate,
                            color=MATE_COLOR,
                        )
                        for mate in assy.matelist
                    ],
                    name="mates",
                )
            )

    children = [_convert(cast("MAssembly", c), top, loc, mates) for c in assy.children]
    return Assembly(parent + children, assy.name)


def jc_show(assy, mates=False, **kwargs):
    return show(_convert(assy, assy, mates=mates), **kwargs)


def jc_show_part(assy: MAssembly, top: MAssembly, loc: Location = None):
    if loc is None:
        obj = assy.obj
        ms = [top.mates[mate]["mate"] for mate in assy.matelist]
    else:
        obj = Workplane(assy.obj.val().moved(loc))  # type: ignore
        ms = [top.mates[mate]["mate"].moved(loc) for mate in assy.matelist]
    show(
        Part(obj, name=assy.name),
        *[Part(to_edge(m), color=MATE_COLOR) for m in ms],
    )


def material(color, transparent=False, opacity=1.0):
    material = CustomMaterial("standard")
    material.color = color
    material.clipping = True
    material.side = "DoubleSide"
    material.alpha = 0.7
    material.polygonOffset = True
    material.polygonOffsetFactor = 1
    material.polygonOffsetUnits = 1
    material.transparent = transparent
    material.opacity = opacity
    material.update("metalness", 0.3)
    material.update("roughness", 0.8)
    return material


class MAssemblyRenderer:
    def __init__(self, assy, width=800, height=600):
        self.assy = assy
        self.height = height
        self.width = width
        self.top = assy
        self.groups = {}
        self.shapes = None
        self.bb = None
        self.camera = None
        self.scene = None
        self.controller = None
        self.renderer = None

        self.camera_distance_factor = 6
        self.camera_initial_zoom = 2.5

    def _get_shapes(self, assy, loc=None):
        loc = assy.loc if loc is None else loc * assy.loc
        parent = [Workplane(shape.located(loc)).val().wrapped for shape in assy.shapes]
        children = [self._get_shapes(c, loc) for c in assy.children]
        return parent + flatten(children)

    def _add(self, vec1, vec2):
        return list(v1 + v2 for v1, v2 in zip(vec1, vec2))

    def _scale(self, vec):
        r = self.bb.max_dist_from_center() * self.camera_distance_factor
        n = np.linalg.norm(vec)
        new_vec = [v / n * r for v in vec]
        return new_vec

    def _update(self):
        self.controller.exec_three_obj_method("update")

    @staticmethod
    def _tq(loc):
        T = loc.wrapped.Transformation()
        t = T.Transforms()
        q = T.GetRotation()
        return (t, (q.X(), q.Y(), q.Z(), q.W()))

    def view(self):
        self.shapes = self.convert(self.assy)

        # Get the overall bounding box
        self.bb = BoundingBox([self._get_shapes(self.assy, self.assy.loc)])

        orbit_radius = 2 * self.bb.max_dist_from_center()

        # Set up camera
        camera_target = self.bb.center
        camera_up = (0.0, 0.0, 1.0)

        camera_position = self._add(self.bb.center, self._scale([1, 1, 1]))

        self.camera = CombinedCamera(
            position=camera_position,
            width=self.width,
            height=self.height,
            far=10 * orbit_radius,
            orthoFar=10 * orbit_radius,
        )
        self.camera.up = camera_up

        self.camera.mode = "orthographic"
        self.camera.position = camera_position

        # Set up lights in every of the 8 corners of the global bounding box
        positions = list(itertools.product(*[(-orbit_radius, orbit_radius)] * 3))
        key_lights = [
            DirectionalLight(color="white", position=position, intensity=0.12)
            for position in positions
        ]
        ambient_light = AmbientLight(intensity=1.0)

        # Set up scene
        environment = key_lights + [ambient_light, self.camera]
        self.scene = Scene(children=environment + [self.shapes])

        # Set up Controllers
        self.controller = OrbitControls(
            controlling=self.camera, target=camera_target, target0=camera_target
        )

        # Update controller to instantiate camera position
        self.camera.zoom = self.camera_initial_zoom
        self._update()

        # Create Renderer instance
        self.renderer = Renderer(
            scene=self.scene,
            camera=self.camera,
            controls=[self.controller],
            antialias=True,
            width=self.width,
            height=self.height,
        )

        return self.renderer

    def convert(self, assy):
        shapes = []
        for shape in assy.shapes:
            np_vertices, np_triangles, np_normals = tessellate(shape.wrapped, 0.01)
            shape_geometry = BufferGeometry(
                attributes={
                    "position": BufferAttribute(np_vertices),
                    "index": BufferAttribute(np_triangles.ravel()),
                    "normal": BufferAttribute(np_normals),
                }
            )
            shape_material = material(assy.web_color)
            shape_mesh = Mesh(
                geometry=shape_geometry, material=shape_material, name=assy.name
            )

            self.groups[assy.name] = shape_mesh
            shapes.append(shape_mesh)

        children = [self.convert(c) for c in assy.children]

        result = Group()
        result.name = assy.name
        for g in shapes + children:
            result.add(g)

        # Adapt group transformation and quaternion
        result.position, result.quaternion = self._tq(assy.loc)
        return result
