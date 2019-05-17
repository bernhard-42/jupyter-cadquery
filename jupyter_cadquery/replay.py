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

from ipywidgets import Button, HBox, Output
import cadquery as cq
from IPython.display import display
from jupyter_cadquery.cadquery import show

_last_signature = None
_skip_objects = 0
# first element: skip steps for "combine=False"
# second element: skip steps for "combine=True"
# Third element: add if clean=True
_skip_list = {
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
    "close": (1, 1, 0)
}

def _blacklist(name):
    return name.startswith("_") or name in ("workplane", "newObject", "vertices")


def _add_function_name(self, name):

    def make_interceptor(func):

        def f(*args, **kwargs):
            global _last_signature, _skip_objects
            if _last_signature is None:
                _last_signature = (func.__name__, args, [])
                skip = _skip_list.get(func.__name__, (0, 0, 0))
                if kwargs.get("combine", True):
                    _skip_objects = skip[1]
                else:
                    _skip_objects = skip[0]
                if kwargs.get("clean", True):
                    _skip_objects += skip[2]
                # print("New    ", func.__name__, _last_signature, _skip_objects, kwargs)
            return func(*args, **kwargs)

        return f

    attr = object.__getattribute__(self, name)
    if callable(attr):
        # print("Called", _skip_objects, _last_signature, attr.__name__)
        if not _blacklist(attr.__name__):
            return make_interceptor(attr)
    return attr


def _newObject(self, objlist):
    global _last_signature, _skip_objects
    ns = cq.Workplane("XY")
    ns.plane = self.plane
    ns.parent = self
    ns.objects = list(objlist)
    ns.ctx = self.ctx
    if _last_signature is not None:
        if _skip_objects == 0:
            # print("Set   ", _last_signature, "\n")
            ns._caller = list(_last_signature)
            if self.ctx.pendingEdges:
                ns._caller[2] = list(self.ctx.pendingEdges)
            _last_signature = None
        else:
            _skip_objects -= 1
            # print("Set skip", _skip_objects)
            ns._caller = None
    else:
        ns._caller = None
    return ns


class Replay(object):

    def __init__(self, sc, workplane, cad_width=600, height=600, dump=False):
        self.stack = self.to_array(workplane)
        self.index = -1
        self.debug_output = Output()
        self.sidecar = sc
        self.cad_width = cad_width
        self.height = height
        if dump:
            self.dump()

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

    def replay_next(self):
        if len(self.stack) > self.index:
            self.index += 1
            msg, cad_obj = self.stack[self.index]
            self.debug("(%d/%d) %s" % (self.index + 1, len(self.stack), msg))
            self.show(cad_obj)

    def replay_prev(self):
        if self.index > 0:
            self.index -= 1
            msg, cad_obj = self.stack[self.index]
            self.debug("(%d/%d) %s" % (self.index + 1, len(self.stack), msg))
            self.show(cad_obj)

    def replay_handler(self, b):
        if b.description == "next":
            self.replay_next()
        elif b.description == "prev":
            self.replay_prev()

    def show(self, cad_obj):
        show(
            cad_obj,
            transparent=True,
            axes=True,
            grid=True,
            cad_width=self.cad_width,
            height=self.height,
            sidecar=self.sidecar)

    def stepper(self, index=-1):
        self.index = index
        next_button = Button(description="next")
        next_button.on_click(self.replay_handler)
        prev_button = Button(description="prev")
        prev_button.on_click(self.replay_handler)
        display(HBox([prev_button, next_button, self.debug_output]))

        self.replay_next()

    @classmethod
    def enable(cls):
        print("Plugging into cadquery.Workplane to enable replay")

        cq.Workplane.__getattribute__ = _add_function_name
        cq.Workplane.newObject = _newObject
