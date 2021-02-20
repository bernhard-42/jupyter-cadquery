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

from dataclasses import dataclass, field
from typing import Any, List, Dict
import warnings

from IPython.display import display
from IPython import get_ipython

from ipywidgets import Button, HBox, VBox, Output, SelectMultiple, Layout

import cadquery as cq
from cadquery import Compound
from jupyter_cadquery.cadquery import Part, show
from jupyter_cadquery.cadquery.cqparts import is_cqparts_part, convert_cqparts
from jupyter_cadquery.cad_display import CadqueryDisplay
from .cad_objects import to_assembly

#
# The Runtime part
# It hooks into __getattribute__ and intercept EVERY python call
# One should only enable replay when necessary for debugging
#


def attributes(names):
    def wrapper(cls):
        for name in names:

            def fget(self, name=name):
                if self.is_empty():
                    raise ValueError("Context empty")
                return self.stack[-1][name]

            def fset(self, value, name=name):
                if self.is_empty():
                    raise ValueError("Context empty")
                self.stack[-1][name] = value

            setattr(cls, name, property(fget, fset))
        return cls

    return wrapper


@attributes(("func", "args", "kwargs", "obj", "children"))
class Context(object):
    def __init__(self):
        self.stack = []
        self.new()

    def _to_dict(self, func, args, kwargs, obj, children):
        return {
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "obj": obj,
            "children": children,
        }

    def new(self):
        self.push(None, None, None, None, [])

    def clear(self):
        self.stack = []

    def is_empty(self):
        return self.stack == []

    def is_top_level(self):
        return len(self.stack) == 1

    def pop(self):
        if not self.is_empty():
            result = self.stack[-1]
            self.stack = self.stack[:-1]
            return result
        else:
            raise ValueError("Empty context")

    def push(self, func, args, kwargs, obj, children):
        self.stack.append(self._to_dict(func, args, kwargs, obj, children))

    def append(self, func, args, kwargs, obj, children):
        self.stack[-1].append(self._to_dict(func, args, kwargs, obj, children))

    def update(self, func, args, kwargs, obj=None, children=None):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        if obj is not None:
            self.obj = obj
        if children is not None:
            self.children = children

    def append_child(self, context):
        self.stack[-1]["children"].append(context)

    def __repr__(self):
        if self.is_empty():
            result = "   >> Context empty"
        else:
            result = ""
            for i, e in enumerate(self.stack):
                result += "  >> %d: %s(%s, %s); %s / %s\n" % (
                    i,
                    e["func"],
                    e["args"],
                    e["kwargs"],
                    e["obj"],
                    e["children"],
                )
        return result


_CTX = Context()
DEBUG = True
REPLAY = False


def _trace(*objs):
    if DEBUG:
        print(*objs)


def _add_context(self, name):
    def _blacklist(name):
        return name.startswith("_") or name in (
            "Workplane",
            "val",
            "vals",
            "all",
            "size",
            "add",
            "toOCC",
            "findSolid",
            "findFace",
            "toSvg",
            "exportSvg",
            "largestDimension",
        )

    def _is_recursive(func):
        return func in ["union", "cut", "intersect"]

    def intercept(parent, func):
        def f(*args, **kwargs):
            _trace("1  calling", func.__name__, args, kwargs)
            _trace(_CTX)

            if _is_recursive(func.__name__):
                _ = _CTX.pop()
                _trace("  --> level down")
                _trace(_CTX)

            if _CTX.args is None:
                _trace("2  updating")
                _CTX.update(func.__name__, args, kwargs)
                _trace(_CTX)

            result = func(*args, **kwargs)

            if func.__name__ == _CTX.func:
                _CTX.obj = result

                if _CTX.is_top_level():
                    result._caller = _CTX.pop()
                    _trace("<== _caller", func.__name__, result._caller)
                else:
                    context = _CTX.pop()
                    _CTX.append_child(context)
                    _trace("<== added child", context)
                _CTX.new()

            _trace("3  leaving", func.__name__)
            _trace(_CTX)
            return result

        return f

    attr = object.__getattribute__(self, name)
    if callable(attr):
        if not _blacklist(attr.__name__):
            _trace("==> intercepting", attr.__name__)
            if _is_recursive(attr.__name__):
                _trace("  --> level up")
                _CTX.new()
            _trace(_CTX)

            return intercept(self, attr)
    return attr


#
# The UI part
# It evaluates and optimizes what the runtime part had collected
#


@dataclass
class Step:
    level: int = 0
    func: str = ""
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[Any, str] = field(default_factory=dict)
    var: str = ""
    result_name: str = ""
    result_obj: Any = None

    def clear_func(self):
        self.func = self.args = self.kwargs = ""


class Replay(object):
    def __init__(self, debug, cad_width, height):
        self.debug_output = Output()
        self.debug = debug
        self.cad_width = cad_width
        self.height = height
        self.display = CadqueryDisplay()
        widget = self.display.create(height=height, cad_width=cad_width)
        self.display.display(widget)

    def format_steps(self, raw_steps):
        def to_code(step, results):
            def to_name(obj):
                if isinstance(obj, cq.Workplane):
                    name = results.get(obj, None)
                else:
                    name = str(obj)
                return obj if name is None else name

            if step.func != "":
                if step.func == "newObject":
                    args = ("...",)
                else:
                    args = tuple([to_name(arg) for arg in step.args])
                code = "%s%s%s" % ("| " * step.level, step.func, args)
                code = code[:-2] if len(step.args) == 1 else code[:-1]
                if len(step.args) > 0 and len(step.kwargs) > 0:
                    code += ","
                if step.kwargs != {}:
                    code += ", ".join(["%s=%s" % (k, v) for k, v in step.kwargs.items()])
                code += ")"
                if step.result_name != "":
                    code += " => %s" % step.result_name
            elif step.var != "":
                code = "%s%s" % ("| " * step.level, step.var)
            else:
                code = "ERROR"
            return code

        steps = []
        entries = []
        obj_index = 1

        results = {step.result_obj: None for step in raw_steps}

        for i in range(len(raw_steps)):
            step = raw_steps[i]
            next_level = step.level if i == (len(raw_steps) - 1) else raw_steps[i + 1].level

            # level change, so add/use the variable name
            if step.level > 0 and step.level != next_level and step.result_name == "":
                obj_name = "_v%d" % obj_index
                obj_index += 1
                step.result_name = obj_name
            steps.append(step)

        for step in steps:
            if results[step.result_obj] is None:
                # first occurence, take note and keep
                results[step.result_obj] = step.result_name
            else:
                # next occurences remove function and add variable name
                step.var = results[step.result_obj]
                step.clear_func()

        last_level = 1000000
        for step in reversed(steps):
            if step.level < last_level:
                last_level = 1000000
                entries.insert(0, (to_code(step, results), step.result_obj))
                if step.var != "":
                    last_level = step.level

        return entries

    def to_array(self, workplane, level=0, result_name=""):
        def walk(caller, level=0, result_name=""):
            stack = [
                Step(
                    level,
                    func=caller["func"],
                    args=caller["args"],
                    kwargs=caller["kwargs"],
                    result_name=result_name,
                    result_obj=caller["obj"],
                )
            ]
            for child in reversed(caller["children"]):
                stack = walk(child, level + 1) + stack
                for arg in child["args"]:
                    if isinstance(arg, cq.Workplane):
                        result_name = getattr(arg, "name", None)
                        stack = self.to_array(arg, level=level + 2, result_name=result_name) + stack
            return stack

        stack = []

        obj = workplane
        while obj is not None:
            caller = getattr(obj, "_caller", None)
            result_name = getattr(obj, "name", "")
            if caller is not None:
                stack = walk(caller, level, result_name) + stack
                for arg in caller["args"]:
                    if isinstance(arg, cq.Workplane):
                        result_name = getattr(arg, "name", "")
                        stack = self.to_array(arg, level=level + 1, result_name=result_name) + stack
            obj = obj.parent

        return stack

    def select_handler(self, change):
        with self.debug_output:
            if change["name"] == "index":
                self.select(change["new"])

    def select(self, indexes):
        self.debug_output.clear_output()
        with self.debug_output:
            self.indexes = indexes
            cad_objs = [self.stack[i][1] for i in self.indexes]

        # Add hidden result to start with final size and allow for comparison
        if not isinstance(self.stack[-1][1].val(), cq.Vector):
            result = Part(self.stack[-1][1], "Result", show_faces=False, show_edges=False)
            objs = [result] + cad_objs
        else:
            objs = cad_objs

        with self.debug_output:
            assembly = to_assembly(*objs)
            mapping = assembly.to_state()
            shapes = assembly.collect_mapped_shapes(mapping)
            tree = tree = assembly.to_nav_dict()
            self.display.add_shapes(shapes=shapes, mapping=mapping, tree=tree, reset=False)


def replay(cad_obj, index=-1, debug=False, cad_width=600, height=600):

    if not REPLAY:
        print("Replay is not enabled. To do so call 'enable_replay()'. Falling back to 'show()'")
        return show(cad_obj, cad_width=cad_width, height=height)
    else:
        print("Use the multi select box below to select one or more steps you want to examine")

    r = Replay(debug, cad_width, height)

    if isinstance(cad_obj, cq.Workplane):
        workplane = cad_obj
    elif is_cqparts_part(cad_obj):
        workplane = convert_cqparts(cad_obj, replay=True)
    else:
        print("Cannot replay", cad_obj)
        return None

    r.stack = r.format_steps(r.to_array(workplane, result_name=getattr(workplane, "name", None)))
    if index == -1:
        r.indexes = [len(r.stack) - 1]
    else:
        r.indexes = [index]

    r.select_box = SelectMultiple(
        options=["[%02d] %s" % (i, code) for i, (code, obj) in enumerate(r.stack)],
        index=r.indexes,
        rows=len(r.stack),
        description="",
        disabled=False,
        layout=Layout(width="600px"),
    )
    r.select_box.add_class("monospace")
    r.select_box.observe(r.select_handler)
    display(HBox([r.select_box, r.debug_output]))

    r.select(r.indexes)
    return r


#
# Control functions to enable, disable and reset replay
#


def reset_replay():
    def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
        return "%s: %s" % (category.__name__, message)

    warn_format = warnings.formatwarning
    warnings.formatwarning = warning_on_one_line
    warnings.simplefilter("always", RuntimeWarning)
    warnings.warn("jupyter_cadquery replay is enabled, turn off with disable_replay()", RuntimeWarning)
    warnings.formatwarning = warn_format

    _CTX.clear()
    _CTX.new()


def enable_replay(debug=False):
    global DEBUG, REPLAY

    DEBUG = debug

    print("\nEnabling jupyter_cadquery replay")
    cq.Workplane.__getattribute__ = _add_context

    ip = get_ipython()
    if not "reset_replay" in [f.__name__ for f in ip.events.callbacks["pre_run_cell"]]:
        ip.events.register("pre_run_cell", reset_replay)
    REPLAY = True


def disable_replay():
    global REPLAY
    print("Removing replay from cadquery.Workplane (will show a final RuntimeWarning)")
    cq.Workplane.__getattribute__ = object.__getattribute__

    ip = get_ipython()
    if "reset_replay" in [f.__name__ for f in ip.events.callbacks["pre_run_cell"]]:
        ip.events.unregister("pre_run_cell", reset_replay)
    REPLAY = False
