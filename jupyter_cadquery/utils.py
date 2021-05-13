import math
import numpy as np
import time
import warnings
from webcolors import name_to_rgb, hex_to_rgb, rgb_to_hex
import ipywidgets as widgets


class Color:
    def __init__(self, color=None):
        if color is None:
            self.r = self.g = self.b = 160
        elif isinstance(color, Color):
            self.r, self.g, self.b = color.r, color.g, color.b
        elif isinstance(color, str):
            if color[0] == "#":
                c = hex_to_rgb(color)
            else:
                c = name_to_rgb(color)
            self.r = c.red
            self.g = c.green
            self.b = c.blue
        elif isinstance(color, (tuple, list)) and len(color) == 3:
            if all((isinstance(c, float) and (c <= 1.0) and (c >= 0.0)) for c in color):
                self.r, self.g, self.b = (int(c * 255) for c in color)
            elif all((isinstance(c, int) and (c <= 255) and (c >= 0)) for c in color):
                self.r, self.g, self.b = color
            else:
                self._invalid(color)
        else:
            self._invalid(color)

    def __str__(self):
        return f"Color({self.r}, {self.g}, {self.b})"

    def _invalid(self, color):
        print(f"warning: {color} is an invalid color, using grey (#aaa)")
        self.r = self.g = self.b = 160

    @property
    def rgb(self):
        return (self.r, self.g, self.b)

    @property
    def percentage(self):
        return (self.r / 255, self.g / 255, self.b / 255)

    @property
    def web_color(self):
        return rgb_to_hex((self.r, self.g, self.b))


def explode(edge_list):
    return [[edge_list[i], edge_list[i + 1]] for i in range(len(edge_list) - 1)]


def flatten(nested_list):
    return [y for x in nested_list for y in x]


# CAD helpers


def distance(v1, v2):
    return np.linalg.norm([x - y for x, y in zip(v1, v2)])


def rad(deg):
    return deg / 180.0 * math.pi


def rotate_x(vector, angle):
    angle = rad(angle)
    mat = np.array(
        [
            [1, 0, 0],
            [0, math.cos(angle), -math.sin(angle)],
            [0, math.sin(angle), math.cos(angle)],
        ]
    )
    return tuple(np.matmul(mat, vector))


def rotate_y(vector, angle):
    angle = rad(angle)
    mat = np.array(
        [
            [math.cos(angle), 0, math.sin(angle)],
            [0, 1, 0],
            [-math.sin(angle), 0, math.cos(angle)],
        ]
    )
    return tuple(np.matmul(mat, vector))


def rotate_z(vector, angle):
    angle = rad(angle)
    mat = np.array(
        [
            [math.cos(angle), -math.sin(angle), 0],
            [math.sin(angle), math.cos(angle), 0],
            [0, 0, 1],
        ]
    )
    return tuple(np.matmul(mat, vector))


def rotate(vector, angle_x=0, angle_y=0, angle_z=0):
    v = tuple(vector)
    if angle_z != 0:
        v = rotate_z(v, angle_z)
    if angle_y != 0:
        v = rotate_y(v, angle_y)
    if angle_x != 0:
        v = rotate_x(v, angle_x)
    return v


def pp_vec(v):
    return "(" + ", ".join([f"{o:10.5f}" for o in v]) + ")"


def pp_loc(loc, format=True):
    T = loc.wrapped.Transformation()
    t = T.Transforms()
    q = T.GetRotation()
    if format:
        return pp_vec(t) + ", " + pp_vec((q.X(), q.Y(), q.Z(), q.W()))
    else:
        return (t, (q.X(), q.Y(), q.Z(), q.W()))


#
# tree search
#


def tree_find_single_selector(tree, selector):
    if tree.name == selector:
        return tree

    for c in tree.children:
        result = tree_find_single_selector(c, selector)
        if result is not None:
            return result
    return None


class Timer:
    def __init__(self, timeit, name, activity, level=0):
        if isinstance(timeit, bool):
            self.timeit = 99 if timeit else -1
        else:
            self.timeit = timeit
        self.activity = activity
        self.name = name
        self.level = level
        self.info = ""
        self.start = time.time()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.level <= self.timeit:
            prefix = ""
            if self.level > 0:
                prefix += "| " * self.level

            if self.name != "":
                self.name = f'"{self.name}"'

            print("%8.3f sec: %s%s %s %s" % (time.time() - self.start, prefix, self.activity, self.name, self.info))


class Progress:
    def __init__(self, max_, width):
        self.max = max_
        self.progress = widgets.IntProgress(
            0,
            0,
            max_,
            layout=widgets.Layout(
                width=f"{width}px", height="10px", padding="0px 4px 0px 0px !important", margin="-3px 0px -3px 2px"
            ),
        )
        self.progress.add_class("jc-progress")

    def reset(self, max_):
        self.max = max_
        self.progress.value = 0
        self.progress.max = max_

    def update(self):
        if self.progress.value < self.max:
            self.progress.value += 1


def px(w):
    return f"{w}px"


def warn(msg):
    def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
        return "%s: %s" % (category.__name__, message)

    warn_format = warnings.formatwarning
    warnings.formatwarning = warning_on_one_line
    warnings.simplefilter("always", RuntimeWarning)
    warnings.warn(msg + "\n", RuntimeWarning)
    warnings.formatwarning = warn_format