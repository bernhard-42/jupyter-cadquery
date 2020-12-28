from typing import overload, Union, Tuple, cast
from math import sin, cos, pi
from cadquery import Workplane, Vector, Location, Plane, Edge, Face


class Mate:
    @overload
    def __init__(
        self,
        origin: Union[Vector, list, tuple] = None,
        x_dir: Union[Vector, list, tuple] = None,
        z_dir: Union[Vector, list, tuple] = None,
    ):
        ...

    @overload
    def __init__(self, workplane: Workplane):
        ...

    def __init__(self, *args, tol=0.0001):
        if len(args) == 1 and isinstance(args[0], Workplane):
            workplane = args[0]
            self.origin = workplane.val().Center()
            self.x_dir = workplane.plane.xDir
            self.z_dir = workplane.plane.zDir

            normal = None
            val = workplane.val()
            if val.geomType() in ["CIRCLE", "ELLIPSE"]:
                normal = val.normal()
            elif isinstance(val, Face):
                normal = val.normalAt(val.Center())

            if normal is not None:
                if abs(abs(self.x_dir.dot(normal)) - 1) < tol:  # x_dir and normal parallel ...
                    self.x_dir = workplane.plane.zDir  # ... so choose zDir as new x_dir ...
                self.z_dir = normal  # ... and make normal to z_dir
        else:
            c = lambda v: v if isinstance(v, Vector) else Vector(*v)
            self.origin = Vector(0, 0, 0) if len(args) == 0 else c(args[0])
            self.x_dir = Vector(1, 0, 0) if len(args) <= 1 else c(args[1])
            self.z_dir = Vector(0, 0, 1) if len(args) <= 2 else c(args[2])

        self.y_dir = self.z_dir.cross(self.x_dir)

    @property
    def loc(self):
        return Location(Plane(self.origin, self.x_dir, self.z_dir))

    def __repr__(self) -> str:
        c = lambda v: f"({v.x:.4f}, {v.y:.4f}, {v.z:.4f})"
        return f"Mate(origin={c(self.origin)}, x_dir={c(self.x_dir)}, z_dir={c(self.z_dir)})"

    @staticmethod
    def _rotate(v, axis, angle) -> float:
        # https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
        return v * cos(angle) + axis.cross(v) * sin(angle) + axis * axis.dot(v) * (1 - cos(angle))

    def rx(self, angle: float) -> "Mate":
        """
        Rotate with a given angle around x axis
        :param angle: angle to ratate in degrees
        :return: self
        """
        a = angle / 180 * pi
        self.y_dir = Mate._rotate(self.y_dir, self.x_dir, a)
        self.z_dir = Mate._rotate(self.z_dir, self.x_dir, a)
        return self

    def ry(self, angle: float) -> "Mate":
        """
        Rotate with a given angle around y axis
        :param angle: angle to ratate in degrees
        :return: self
        """
        a = angle / 180 * pi
        self.x_dir = Mate._rotate(self.x_dir, self.y_dir, a)
        self.z_dir = Mate._rotate(self.z_dir, self.y_dir, a)
        return self

    def rz(self, angle: float) -> "Mate":
        """
        Rotate with a given angle around z axis
        :param angle: angle to ratate in degrees
        :return: self
        """
        a = angle / 180 * pi
        self.x_dir = Mate._rotate(self.x_dir, self.z_dir, a)
        self.y_dir = Mate._rotate(self.y_dir, self.z_dir, a)
        return self

    def translate(self, axis: Vector, dist: float):
        """
        Translate with a given direction scaled by dist
        :param axis: the direction to translate
        :param dist: scale of axis
        """
        self.origin = self.origin + axis * dist

    def tx(self, dist: float) -> "Mate":
        """
        Translate with a given distance along x axis
        :param dist: distance to translate
        :return: self
        """
        self.translate(self.x_dir, dist)
        return self

    def ty(self, dist: float) -> "Mate":
        """
        Translate with a given distance along y axis
        :param dist: distance to translate
        :return: self
        """
        self.translate(self.y_dir, dist)
        return self

    def tz(self, dist: float) -> "Mate":
        """
        Translate with a given distance along z axis
        :param dist: distance to translate
        :return: self
        """
        self.translate(self.z_dir, dist)
        return self

    def moved(self, loc: Location) -> "Mate":
        """
        Return a new mate moved by the given Location
        :param loc: The Location object to move the mate
        :return: Mate
        """

        def move(origin: Vector, vec: Vector, loc: Location) -> Tuple[Vector, Vector]:
            reloc = cast(Edge, Edge.makeLine(origin, origin + vec).moved(loc))
            v1, v2 = reloc.startPoint(), reloc.endPoint()
            return v1, v2 - v1

        origin, x_dir = move(self.origin, self.x_dir, loc)
        _, z_dir = move(self.origin, self.z_dir, loc)
        return Mate(origin, x_dir, z_dir)
