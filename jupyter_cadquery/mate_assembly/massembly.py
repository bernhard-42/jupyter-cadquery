from typing import Optional, Union, Tuple, cast, overload

from cadquery import Shape, Workplane, Location, NearestToPointSelector, Assembly
from .mate import Mate
from ..utils import tree_find
from ..ocp_utils import get_rgb

Selector = Tuple[str, Union[str, Tuple[float, float]]]


class MAssembly(Assembly):
    def __init__(self, *args, **kwargs):
        self.mates = {}
        self.matelist = []
        self.origin = None
        self._relocated = False

        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        def to_string(self, ind=""):
            result = f"{ind}MAssembly({self.name}: {self.obj})\n"
            if self.matelist:
                result += f"{ind}  mates={self.matelist}\n"
            for c in self.children:
                result += to_string(c, ind + "  ")
            return result

        return to_string(self, "")

    @property
    def web_color(self) -> str:
        return "#%02x%02x%02x" % get_rgb(self.color)

    # Override only because CadQuery.Assembly uses "assy = Assembly(arg, **kwargs)"
    def add(self, arg, **kwargs) -> "MAssembly":  # type: ignore[override]
        if isinstance(arg, MAssembly):
            super().add(arg, **kwargs)
        else:
            assy = MAssembly(arg, **kwargs)
            assy.parent = self
            self.add(assy)

        return self

    def find_assembly(self, assy_selector: str) -> Optional["MAssembly"]:
        """
        Find an assembly
        :param assy_selector: an MAssembly selector (enhanced CadQuery Assembly selector)

        To find sub assemblies of the same object in assemblies this is an enhanced CadQuery
        Assembly selector joining assembly name with ">".
        Valid selectors: "name", "name>child", "name>child>child", ...
        """
        return tree_find(self, assy_selector)

    def find_obj(self, obj_selectors: Tuple[Selector, ...] = None) -> Optional[Shape]:
        """
        Find a CadQuery object in an assembly
        :param assembly: A MAssembly object
        :param obj_selectors: a list of an CadQuery object selectors (enhanced CadQuery selectors)

        Finding wires around points, e.g. holes, is often needed. To ease life here, there is one enhanced
        CadQuery  obj_selector: ("wires", (x,y))", often use as a chain
            ("faces", ">Z)\\            # select a face
            .("wires", (x[i], y[i]))    # and from there select holes i by its 2 dim coordinates on the face
        """
        obj = self.obj
        if obj_selectors is not None and isinstance(obj, (Workplane, Shape)):
            for selector in obj_selectors:
                if isinstance(selector, str):
                    selector = selector.split("@")
                tmp = Workplane()
                tmp.add(cast(Workplane, obj))
                kind = selector[0]
                select = getattr(tmp, kind)
                if isinstance(selector[1], (tuple, list)):
                    obj = select(NearestToPointSelector(selector[1]))
                else:
                    obj = select(selector[1])

        return cast(Shape, obj)

    def find(self, selector: str, *obj_selectors: Selector) -> Optional[Shape]:
        """
        Find an assembly and one of its CadQuery shapes
        :param selector: an MAssembly selector (enhanced CadQuery Assembly selector)
        :param obj_selectors: a list of an CadQuery object selectors (enhanced CadQuery selectors)

        To find sub assemblies of the same object in assemblies this is an enhanced CadQuery
        Assembly selector joining assembly name with ">".
        Valid selectors: "name", "name>child", "name>child>child", ...

        Finding wires around points, e.g. holes, is often needed. To ease life here, there is one enhanced
        CadQuery  obj_selector: ("wires", (x,y))", often use as a chain
            ("faces", ">Z)\\            # select a face
            .("wires", (x[i], y[i]))    # and from there select holes i by its 2 dim coordinates on the face
        """
        assembly = self.find_assembly(selector)
        if assembly is None:
            print(f"No assembly for '{selector}' found")
            return None
        else:
            return assembly.find_obj(obj_selectors)

    def mate(self, name: str, selector: str, mate: Mate, origin=False):
        """
        Add a mate to an assembly
        :param name: name of the new mate
        :param selector: an object assembly (enhanced CadQuery selector)
        :param mate: the mate to be added
        :returns mate
        """
        assembly = self.find_assembly(selector)
        if assembly is not None:
            # TODO remove assembly or add object to dict
            self.mates[name] = {"mate": mate, "assembly": selector}
            assembly.matelist.append(name)
            if origin:
                assembly.origin = mate

        return self

    def _set_origin(self):
        """Relocate every shape to have its origin at the assembly origin"""
        if self.origin is not None:
            self.obj = Workplane(self.obj.val().moved(self.origin.loc.inverse))
            self.loc = Location()  # change location to identity
        for c in self.children:
            c._set_origin()

    def relocate(self):
        """Relocate every sub assembly so that all its shapes have their origin at the assembly origin"""
        if self._relocated:
            print("Already relocated")
        else:
            self._set_origin()
            for _, v in self.mates.items():
                assy = self.find_assembly(v["assembly"])
                if assy.origin is not None:
                    v["mate"] = v["mate"].moved(assy.origin.loc.inverse)
            self._relocated = True

    def assemble(self, mate_name: str, target: Union[str, Location]):
        """
        Translate and rotate a mate onto a target mate
        :param mate: name of the mate to be relocated
        :param target: name of the target mate or a Location object to relocate the mate to
        :returns self
        """
        mate = self.mates[mate_name]["mate"]
        assy = self.find_assembly(self.mates[mate_name]["assembly"])
        if isinstance(target, str):
            if assy is not None:
                target_mate = self.mates[target]["mate"]
                assy.loc = target_mate.loc * mate.loc.inverse
        else:
            assy.loc = target

        return self

