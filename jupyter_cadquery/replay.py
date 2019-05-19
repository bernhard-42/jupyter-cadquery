#
# Copyright 2019 Bernhard Walter
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from ipywidgets import Button, HBox, VBox, Output, Select
import cadquery as cq
from IPython.display import display
from jupyter_cadquery.cadquery import show

_DEBUG = False
_SIDECAR = None
_LAST_SIGNATURE = None
_SKIP_OBJECTS = 0
# first element: skip steps for "combine=False"
# second element: skip steps for "combine=True"
# Third element: add if clean=True
_SKIP_LIST = {
    "fillet": (1, 1, 0),
    "chamfer": (1, 1, 0),
    "circle": (1, 1, 0),
    "rect": (1, 1, 0),
    "polygon": (1, 1, 0),
    "box": (1, 2, 1),
    "mirrorX": (4, 4, 0),
    "mirrorY": (4, 4, 0),
    "cboreHole": (2, 2, 0),
    "cskHole": (2, 2, 0),
    "hole": (2, 2, 0),
    "extrude": (0, 0, 1),
    "twistExtrude": (0, 0, 1),
    "revolve": (0, 0, 1),
    "close": (1, 1, 0),
    "mirror": (1, 1, 0)
}

def _blacklist(name):
    return name.startswith("_") or name in ("workplane", "newObject", "vertices")


def _add_function_name(self, name):

    def make_interceptor(func):

        def f(*args, **kwargs):
            global _LAST_SIGNATURE, _SKIP_OBJECTS
            if _LAST_SIGNATURE is None:
                _LAST_SIGNATURE = (func.__name__, args, [])
                skip = _SKIP_LIST.get(func.__name__, (0, 0, 0))
                if kwargs.get("combine", True):
                    _SKIP_OBJECTS = skip[1]
                else:
                    _SKIP_OBJECTS = skip[0]
                if kwargs.get("clean", True):
                    _SKIP_OBJECTS += skip[2]
                if _DEBUG: print("New    ", func.__name__, _LAST_SIGNATURE, _SKIP_OBJECTS, kwargs)
            return func(*args, **kwargs)

        return f

    attr = object.__getattribute__(self, name)
    if callable(attr):
        if _DEBUG: print("Called", _SKIP_OBJECTS, _LAST_SIGNATURE, attr.__name__)
        if not _blacklist(attr.__name__):
            return make_interceptor(attr)
    return attr


def _newObject(self, objlist):
    global _LAST_SIGNATURE, _SKIP_OBJECTS
    ns = cq.Workplane("XY")
    ns.plane = self.plane
    ns.parent = self
    ns.objects = list(objlist)
    ns.ctx = self.ctx
    if _LAST_SIGNATURE is not None:
        if _SKIP_OBJECTS == 0:
            if _DEBUG: print("Set   ", _LAST_SIGNATURE, "\n")
            ns._caller = list(_LAST_SIGNATURE)
            if self.ctx.pendingEdges:
                ns._caller[2] = list(self.ctx.pendingEdges)
            _LAST_SIGNATURE = None
        else:
            _SKIP_OBJECTS -= 1
            if _DEBUG: print("Set skip", _SKIP_OBJECTS)
            ns._caller = None
    else:
        ns._caller = None
    return ns


class Replay(object):

    def __init__(self, sidecar, debug=False, cad_width=600, height=600):
        global _DEBUG, _SIDECAR
        _DEBUG = debug
        _SIDECAR = sidecar
        self.debug = debug
        
        print("Plugging into cadquery.Workplane to enable replay")
        cq.Workplane.__getattribute__ = _add_function_name
        cq.Workplane.newObject = _newObject

        self.debug_output = Output()
        self.cad_width = cad_width
        self.height = height
        self.select_tmp = 0

    def to_array(self, workplane):
        stack = []
        obj = workplane
        while obj is not None:
            caller = getattr(obj, "_caller", None)
            if caller is not None:
                name, args, pendingeEdges = caller
                code = "%s%s" % (name, args)
                if len(args) == 1:
                    code = code[:-2] + ")"
                if pendingeEdges:
                    stack.insert(0, (code, obj.newObject(pendingeEdges)))
                else:
                    stack.insert(0, (code, obj))
            obj = obj.parent
        return stack

    def dump(self):
        for o in self.stack:
            print(o, o[1].val().__class__.__name__)

    def debug(self, *msgs):
        self.debug_output.clear_output()
        with self.debug_output:
            print(*msgs)

    def get_ctx(self, cad_obj):
        if len(cad_obj.ctx.pendingEdges) > 0:
            return cad_obj.newObject(cad_obj.ctx.pendingEdges)
        else:
            return cad_obj

    def select(self, index):
        self.index = index
        cad_obj = self.stack[self.index][1]
        self.show(cad_obj)

    def select_handler(self, change):
        if change["name"] == "index":
            self.select(change["new"])

    def show(self, cad_obj):
        show(
            cad_obj,
            transparent=True,
            axes=True,
            grid=True,
            cad_width=self.cad_width,
            height=self.height,
            sidecar=_SIDECAR)

    def replay(self, workplane, index=0):
        self.stack = self.to_array(workplane)
        self.index = index
        if self.debug:
            print("Dump of stack:")
            self.dump()

        self.select_box = Select(
            options=["[%02d] %s" % (i, code) for i, (code, obj) in enumerate(self.stack)],
            index=self.index,
            rows=len(self.stack),
            description='',
            disabled=False)
        self.select_box.add_class("monospace")
        self.select_box.observe(self.select_handler)
        display(HBox([self.select_box, self.debug_output]))

        self.select(self.index)
