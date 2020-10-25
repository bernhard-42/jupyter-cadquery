import itertools
import numpy as np

import cadquery as cq
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
from jupyter_cadquery.utils import BoundingBox, flatten
from jupyter_cadquery.cad_view import tessellate
from .massembly import rgb

MATE_COLOR = ((255, 0, 0), (0, 255, 0), (0, 0, 255))


def pp_vec(v):
    return "(" + ", ".join([f"{o:10.5f}" for o in v]) + ")"


def pp_loc(loc, format=True):
    T = loc.wrapped.Transformation()
    t = T.Transforms()
    q = T.GetRotation()
    if format:
        return pp_vec(t) + ", " + pp_vec((q.X(), q.Y(), q.Z(), q.W()))
    else:
        return (t, (q.X(), q.Y(), q.Z(), q.W()))


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
        parent = [
            cq.Workplane(shape.located(loc)).val().wrapped for shape in assy.shapes
        ]
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
            shape_material = material(rgb(assy))
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
