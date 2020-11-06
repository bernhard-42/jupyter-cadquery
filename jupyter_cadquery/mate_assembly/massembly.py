from typing import Optional, Union, Tuple, cast

from cadquery import Shape, Workplane, Location, NearestToPointSelector, Assembly
from .mate import Mate
from ..utils import tree_find

Selector = Tuple[str, Union[str, Tuple[float, float]]]


class MAssembly(Assembly):
    def __init__(self, *args, **kwargs):
        self.mates = {}
        self.matelist = []
        self.origin = None
        self.relocated = False
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
        b = lambda x: int(255 * x)
        if self.color is None:
            return "#aaa"
        rgb = self.color.wrapped.GetRGB()
        return "#%02x%02x%02x" % (b(rgb.Red()), b(rgb.Green()), b(rgb.Blue()))

    def add(self, arg, **kwargs) -> "MAssembly":  # type: ignore[override]
        if isinstance(arg, MAssembly):
            super().add(arg, **kwargs)
        else:
            assy = MAssembly(arg, **kwargs)
            assy.parent = self
            self.add(assy)

        return self

    def find_assembly(self, selector: str) -> Optional["MAssembly"]:
        return tree_find(self, selector)

    def find_obj(
        self, assembly: "MAssembly", obj_selectors: Tuple[Selector, ...] = None
    ) -> Optional[Shape]:
        obj = assembly.obj
        if obj_selectors is not None and isinstance(obj, (Workplane, Shape)):
            for selector in obj_selectors:
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
        assembly = self.find_assembly(selector)
        if assembly is None:
            print(f"No assembly for '{selector}' found")
            return None
        else:
            return self.find_obj(assembly, obj_selectors)

    def mate(self, name: str, selector: str, mate: Mate, is_origin=False):
        assembly = self.find_assembly(selector)
        if assembly is not None:
            # TODO remove assembly or add object to dict
            self.mates[name] = {"mate": mate, "assembly": selector}
            assembly.matelist.append(name)
            if is_origin:
                assembly.origin = mate

        return self

    def set_origin(self):
        if self.origin is not None:
            self.obj = Workplane(self.obj.val().moved(self.origin.loc.inverse))
            self.loc = Location()
        for c in self.children:
            c.set_origin()

    def relocate(self):
        if self.relocated:
            print("Already relocated")
        else:
            self.set_origin()
            for _, v in self.mates.items():
                assy = self.find_assembly(v["assembly"])
                if assy.origin is not None:
                    v["mate"] = v["mate"].moved(assy.origin.loc.inverse)
            self.relocated = True

    def assemble(self, mate_obj: str, mate_target: str):
        m_obj = self.mates[mate_obj]["mate"]
        assy = self.find_assembly(self.mates[mate_obj]["assembly"])
        if assy is not None:
            m_target = self.mates[mate_target]["mate"]
            assy.loc = m_target.loc * m_obj.loc.inverse

        return self
