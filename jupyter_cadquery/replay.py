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
from jupyter_cadquery.cadquery import Part, show

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

    def __init__(self, debug=False, cad_width=600, height=600):
        self._debug = debug

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
        self.stack = stack

    def dump(self):
        for o in self.stack:
            print(o, o[1].val().__class__.__name__)

    def debug(self, *msgs):
        self.debug_output.clear_output()
        with self.debug_output:
            print(*msgs)

    def select(self, indexes):
        with self.debug_output:
            self.indexes = indexes
            cad_objs = [self.stack[i][1] for i in self.indexes]
            self.show(cad_objs)

    def select_handler(self, change):
        with self.debug_output:
            if change["name"] == "index":
                self.select(change["new"])

    def show(self, cad_objs):
        self.debug_output.clear_output()
        # Add hidden result to start with final size and allow for comparison
        result = Part(self.stack[-1][1], "Result", show_faces=False, show_edges=False)
        with self.debug_output:
            show(
                result,
                *cad_objs,
                transparent=True,
                axes=True,
                grid=True,
                cad_width=self.cad_width,
                height=self.height,
                show_parents=(len(cad_objs)==1))


def replay(workplane, index=0, debug=False, cad_width=600, height=600):

    r = Replay(debug, cad_width, height)
    r.to_array(workplane)
    r.indexes = [index]

    if r._debug:
        print("Dump of stack:")
        r.dump()

    r.select_box = SelectMultiple(
        options=["[%02d] %s" % (i, code) for i, (code, obj) in enumerate(r.stack)],
        index=r.indexes,
        rows=len(r.stack),
        description='',
        disabled=False,
        layout=Layout(width="600px"))
    r.select_box.add_class("monospace")
    r.select_box.observe(r.select_handler)
    display(HBox([r.select_box, r.debug_output]))

    r.select(r.indexes)
    return r


print("Plugging into cadquery.Workplane to enable replay")
cq.Workplane.__getattribute__ = _add_context
