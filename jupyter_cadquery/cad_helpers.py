# Copyright 2019 Bernhard Walter

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
from functools import reduce

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from pythreejs import GridHelper, LineSegmentsGeometry, LineSegments2, LineMaterial

from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add


class Helpers(object):

    def __init__(self, bb_center):
        self.bb_center = bb_center
        self.center = (0, 0, 0)

    def _center(self, zero=True):
        return self.center if zero else self.bb_center

    def set_position(self, position):
        raise NotImplementedError()

    def set_visibility(self, change):
        raise NotImplementedError()

    def set_center(self, change):
        self.set_position(self._center(change))


class Grid(Helpers):

    def __init__(self, bb_center=None, maximum=5, ticks=10, colorCenterLine='#aaa', colorGrid='#ddd'):
        super().__init__(bb_center)
        self.maximum = maximum
        axis_start, axis_end, nice_tick = self.nice_bounds(-maximum, maximum, 2 * ticks)
        self.step = nice_tick
        self.size = axis_end - axis_start
        self.grid = GridHelper(
            self.size, int(self.size / self.step), colorCenterLine=colorCenterLine, colorGrid=colorGrid)
        self.set_center(True)

    # https://stackoverflow.com/questions/4947682/intelligently-calculating-chart-tick-positions
    def _nice_number(self, value, round_=False):
        exponent = math.floor(math.log(value, 10))
        fraction = value / 10**exponent

        if round_:
            if fraction < 1.5:
                nice_fraction = 1.
            elif fraction < 3.:
                nice_fraction = 2.
            elif fraction < 7.:
                nice_fraction = 5.
            else:
                nice_fraction = 10.
        else:
            if fraction <= 1:
                nice_fraction = 1.
            elif fraction <= 2:
                nice_fraction = 2.
            elif fraction <= 5:
                nice_fraction = 5.
            else:
                nice_fraction = 10.

        return nice_fraction * 10**exponent

    def nice_bounds(self, axis_start, axis_end, num_ticks=10):
        axis_width = axis_end - axis_start
        if axis_width == 0:
            nice_tick = 0
        else:
            nice_range = self._nice_number(axis_width)
            nice_tick = self._nice_number(nice_range / (num_ticks - 1), round_=True)
            axis_start = math.floor(axis_start / nice_tick) * nice_tick
            axis_end = math.ceil(axis_end / nice_tick) * nice_tick

        return axis_start, axis_end, nice_tick

    def set_position(self, position):
        self.grid.position = position

    def set_visibility(self, change):
        self.grid.visible = change

    def set_rotation(self, rotation):
        self.grid.rotation = rotation


class Axes(Helpers):

    def __init__(self, bb_center, length=1, width=3):
        super().__init__(bb_center)

        self.axes = []
        for vector, color in zip(([length, 0, 0], [0, length, 0], [0, 0, length]), ('red', 'green', 'blue')):
            self.axes.append(
                LineSegments2(
                    LineSegmentsGeometry(positions=[[self.center, self._shift(self.center, vector)]]),
                    LineMaterial(linewidth=width, color=color)))

    def _shift(self, v, offset):
        return [x + o for x, o in zip(v, offset)]

    def set_position(self, position):
        for i in range(3):
            self.axes[i].position = position

    def set_visibility(self, change):
        for i in range(3):
            self.axes[i].visible = change


class BoundingBox(object):

    def __init__(self, shapes, tol=1e-5):
        self.tol = tol
        bbox = reduce(self._opt, [self.bbox(shape) for shape in shapes])
        self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax = bbox
        self.xsize = self.xmax - self.xmin
        self.ysize = self.ymax - self.ymin
        self.zsize = self.zmax - self.zmin
        self.center = (self.xmin + self.xsize / 2.0, self.ymin + self.ysize / 2.0, self.zmin + self.zsize / 2.0)
        self.max = reduce(lambda a, b: max(abs(a), abs(b)), bbox)

    def _opt(self, b1, b2):
        return (min(b1[0], b2[0]), max(b1[1], b2[1]), min(b1[2], b2[2]), max(b1[3], b2[3]), min(b1[4], b2[4]),
                max(b1[5], b2[5]))

    def _bounding_box(self, obj, tol=1e-5):
        bbox = Bnd_Box()
        bbox.SetGap(self.tol)
        brepbndlib_Add(obj, bbox, True)
        values = bbox.Get()
        return (values[0], values[3], values[1], values[4], values[2], values[5])

    def bbox(self, shape):
        bb = reduce(self._opt, [self._bounding_box(obj.wrapped) for obj in shape.objects])
        return bb

    def __repr__(self):
        return "[x(%f .. %f), y(%f .. %f), z(%f .. %f)]" % \
               (self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax)
