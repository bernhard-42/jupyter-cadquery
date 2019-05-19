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

from ipywidgets import Button, HBox, VBox, Output, Select, Layout
import cadquery as cq
from IPython.display import display
from jupyter_cadquery.cadquery import show

_CONTEXT = None


# Note: This won't work for circle calls or recursions!
def _add_context(self, name):

    def _blacklist(name):
        return name.startswith("_") or name in ("workplane", "newObject", "vertices", "val", "vals", "all", "size",
                                                "add", "toOCC", "findSolid", "findFace", "toSvg", "exportSvg",
                                                "largestDimension")

    def intercept(func):

        def f(*args, **kwargs):
            global _CONTEXT
            if _CONTEXT is None:
                _CONTEXT = [func.__name__, args, kwargs]

            result = func(*args, **kwargs)

            if func.__name__ == _CONTEXT[0]:
                result._caller = _CONTEXT + [list(result.ctx.pendingEdges)]
                _CONTEXT = None
            return result

        return f

    attr = object.__getattribute__(self, name)
    if callable(attr):
        if not _blacklist(attr.__name__):
            return intercept(attr)
    return attr


class Replay(object):

    def __init__(self, sidecar, debug=False, cad_width=600, height=600):
        global _DEBUG, _SIDECAR
        _DEBUG = debug
        _SIDECAR = sidecar
        self._debug = debug

        print("Plugging into cadquery.Workplane to enable replay")
        cq.Workplane.__getattribute__ = _add_context

        self.debug_output = Output()
        self.cad_width = cad_width
        self.height = height
        self.select_tmp = 0

    def to_array(self, workplane):

        def _to_name(obj):
            name = getattr(obj, "name", None)
            return name or obj

        stack = []
        obj = workplane
        while obj is not None:
            caller = getattr(obj, "_caller", None)
            if caller is not None:
                name, args, kwargs, pendingeEdges = caller
                args = tuple([_to_name(arg) for arg in args])
                code = "%s%s" % (name, args)
                if len(args) == 1:
                    code = code[:-2]
                else:
                    code = code[:-1]
                if len(args) > 0 and len(kwargs) > 0:
                    code += ","
                if kwargs != {}:
                    code += ", ".join(["%s=%s" % (k, v) for k, v in kwargs.items()])
                code += ")"
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
        if self._debug:
            print("Dump of stack:")
            self.dump()

        self.select_box = Select(
            options=["[%02d] %s" % (i, code) for i, (code, obj) in enumerate(self.stack)],
            index=self.index,
            rows=len(self.stack),
            description='',
            disabled=False,
            layout=Layout(width="600px"))
        self.select_box.add_class("monospace")
        self.select_box.observe(self.select_handler)
        display(HBox([self.select_box, self.debug_output]))

        self.select(self.index)
