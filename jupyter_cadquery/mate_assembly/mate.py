from typing import overload, Union, Tuple, cast
from math import sin, cos, pi
from cadquery import Workplane, Vector, Location, Plane, Edge


class Mate:
    @overload
    def __init__(
        self,
        pnt: Union[Vector, list, tuple] = None,
        x_dir: Union[Vector, list, tuple] = None,
        z_dir: Union[Vector, list, tuple] = None,
    ):
        ...

    @overload
    def __init__(self, workplane: Workplane):
        ...

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], Workplane):
            plane = args[0]
            self.pnt = plane.val().Center()
            self.x_dir = plane.workplane().plane.xDir
            self.z_dir = plane.workplane().plane.zDir
        else:
            c = lambda v: v if isinstance(v, Vector) else Vector(*v)
            self.pnt = Vector(0, 0, 0) if len(args) == 0 else c(args[0])
            self.x_dir = Vector(1, 0, 0) if len(args) <= 1 else c(args[1])
            self.z_dir = Vector(0, 0, 1) if len(args) <= 2 else c(args[2])
        self.y_dir = self.z_dir.cross(self.x_dir)

    @property
    def loc(self):
        return Location(Plane(self.pnt, self.x_dir, self.z_dir))

    def __repr__(self) -> str:
        c = lambda v: f"({v.x:.4f}, {v.y:.4f}, {v.z:.4f})"
        return f"Mate(pnt={c(self.pnt)}, x_dir={c(self.x_dir)}, z_dir={c(self.z_dir)})"

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
        self.pnt = self.pnt + axis * dist

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
        def move(pnt: Vector, vec: Vector, loc: Location) -> Tuple[Vector, Vector]:
            reloc = cast(Edge, Edge.makeLine(pnt, pnt + vec).moved(loc))
            v1, v2 = reloc.startPoint(), reloc.endPoint()
            return v1, v2 - v1

        pnt, x_dir = move(self.pnt, self.x_dir, loc)
        _, z_dir = move(self.pnt, self.z_dir, loc)
        return Mate(pnt, x_dir, z_dir)
