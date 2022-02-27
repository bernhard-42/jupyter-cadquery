import json
import math
import numpy as np
import time
import warnings
from webcolors import name_to_rgb, hex_to_rgb, rgb_to_hex


def round_sig(x, sig):
    return round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)


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


#
# Helpers
#


def explode(edge_list):
    return [[edge_list[i], edge_list[i + 1]] for i in range(len(edge_list) - 1)]


def flatten(nested_list):
    return [y for x in nested_list for y in x]


def numpy_to_json(obj, indent=None):
    class NumpyArrayEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, np.integer):
                return int(o)
            if isinstance(o, np.floating):
                return float(o)
            if isinstance(o, np.ndarray):
                return o.tolist()

            return super(NumpyArrayEncoder, self).default(o)

    return json.dumps(obj, cls=NumpyArrayEncoder, indent=indent)


def distance(v1, v2):
    return np.linalg.norm([x - y for x, y in zip(v1, v2)])


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


def px(w):
    return f"{w}px"


def warn(message, warning=RuntimeWarning, when="always"):
    def warning_on_one_line(
        message, category, filename, lineno, file=None, line=None
    ):  # pylint: disable=unused-argument
        return "%s: %s" % (category.__name__, message)

    warn_format = warnings.formatwarning
    warnings.formatwarning = warning_on_one_line
    warnings.simplefilter(when, warning)
    warnings.warn(message + "\n", warning)
    warnings.formatwarning = warn_format
    warnings.simplefilter("ignore", warning)
