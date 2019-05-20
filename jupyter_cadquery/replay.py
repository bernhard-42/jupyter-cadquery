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

from ipywidgets import Button, HBox, VBox, Output, SelectMultiple, Layout
import cadquery as cq
from IPython.display import display
from jupyter_cadquery.cadquery import show

_CONTEXT = None


# Note: This won't work for circle calls or recursions!
def _add_context(self, name):

    def _blacklist(name):
        return name.startswith("_") or name in ("newObject", "val", "vals", "all", "size", "add", "toOCC", "findSolid",
                                                "findFace", "toSvg", "exportSvg", "largestDimension")

    def intercept(func):

        def f(*args, **kwargs):
            global _CONTEXT
            if _CONTEXT is None:
                _CONTEXT = [func.__name__, args, kwargs]

            result = func(*args, **kwargs)

            if func.__name__ == _CONTEXT[0]:
                result._caller = _CONTEXT
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
        self.indexes = [0]

    def to_array(self, workplane):

        def _to_name(obj):
            name = getattr(obj, "name", None)
            return name or obj

        stack = []
        obj = workplane
        while obj is not None:
            caller = getattr(obj, "_caller", None)
            if caller is not None:
                name, args, kwargs = caller
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

    def select(self, indexes):
        self.indexes = indexes
        cad_objs = [self.stack[i][1] for i in self.indexes]
        self.show(cad_objs)

    def select_handler(self, change):
        if change["name"] == "index":
            self.select(change["new"])

    def show(self, cad_objs):
        show(
            *cad_objs,
            transparent=True,
            axes=True,
            grid=True,
            cad_width=self.cad_width,
            height=self.height,
            sidecar=_SIDECAR)

    def replay(self, workplane, index=0):
        self.stack = self.to_array(workplane)
        self.indexes = [index]
        if self._debug:
            print("Dump of stack:")
            self.dump()

        self.select_box = SelectMultiple(
            options=["[%02d] %s" % (i, code) for i, (code, obj) in enumerate(self.stack)],
            index=self.indexes,
            rows=len(self.stack),
            description='',
            disabled=False,
            layout=Layout(width="600px"))
        self.select_box.add_class("monospace")
        self.select_box.observe(self.select_handler)
        display(HBox([self.select_box, self.debug_output]))

        self.select(self.indexes)
        return self
