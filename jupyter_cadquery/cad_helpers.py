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

import math
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from pythreejs import (
        GridHelper,
        LineSegmentsGeometry,
        LineSegments2,
        LineMaterial,
        ShaderMaterial,
        ShaderLib,
    )

import numpy as np


class Helpers(object):
    def __init__(self, bb_center):
        self.bb_center = bb_center
        self.center = (0, 0, 0)
        self.zero = True

    def _center(self, zero=True):
        self.zero = zero
        return self.center if zero else self.bb_center

    def get_position(self):
        raise NotImplementedError()

    def set_position(self, position):
        raise NotImplementedError()

    def set_visibility(self, change):
        raise NotImplementedError()

    def get_center(self):
        return self.get_position()

    def is_center(self):
        return self.zero

    def set_center(self, change):
        self.set_position(self._center(change))


class Grid(Helpers):
    def __init__(self, bb_center=None, maximum=5, ticks=10, colorCenterLine="#aaa", colorGrid="#ddd"):
        super().__init__(bb_center)
        self.maximum = maximum
        axis_start, axis_end, nice_tick = self.nice_bounds(-maximum, maximum, 2 * ticks)
        self.step = nice_tick
        self.size = axis_end - axis_start
        self.grid = GridHelper(
            self.size, int(self.size / self.step), colorCenterLine=colorCenterLine, colorGrid=colorGrid
        )
        self.set_center(True)

    # https://stackoverflow.com/questions/4947682/intelligently-calculating-chart-tick-positions
    def _nice_number(self, value, round_=False):
        exponent = math.floor(math.log(value, 10))
        fraction = value / 10 ** exponent

        if round_:
            if fraction < 1.5:
                nice_fraction = 1.0
            elif fraction < 3.0:
                nice_fraction = 2.0
            elif fraction < 7.0:
                nice_fraction = 5.0
            else:
                nice_fraction = 10.0
        else:
            if fraction <= 1:
                nice_fraction = 1.0
            elif fraction <= 2:
                nice_fraction = 2.0
            elif fraction <= 5:
                nice_fraction = 5.0
            else:
                nice_fraction = 10.0

        return nice_fraction * 10 ** exponent

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

    def get_position(self):
        return self.grid.position

    def set_position(self, position):
        self.grid.position = position

    def get_visibility(self):
        return self.grid.visible

    def set_visibility(self, change):
        self.grid.visible = change

    def set_rotation(self, rotation):
        self.grid.rotation = rotation


class Axes(Helpers):
    def __init__(self, bb_center, length=1, width=3):
        super().__init__(bb_center)

        self.axes = []
        for vector, color in zip(([length, 0, 0], [0, length, 0], [0, 0, length]), ("red", "green", "blue")):
            self.axes.append(
                LineSegments2(
                    LineSegmentsGeometry(positions=[[self.center, self._shift(self.center, vector)]]),
                    LineMaterial(linewidth=width, color=color),
                )
            )

    def _shift(self, v, offset):
        return [x + o for x, o in zip(v, offset)]

    def get_position(self):
        return self.axes[0].position

    def set_position(self, position):
        for i in range(3):
            self.axes[i].position = position

    def get_visibility(self):
        return self.axes[0].visible

    def set_visibility(self, change):
        for i in range(3):
            self.axes[i].visible = change


class CustomMaterial(ShaderMaterial):
    def __init__(self, typ):
        self.types = {
            "diffuse": "c",
            "uvTransform": "m3",
            "normalScale": "v2",
            "fogColor": "c",
            "emissive": "c",
        }

        shader = ShaderLib[typ]

        fragmentShader = """
        uniform float alpha;
        """
        frag_from = "gl_FragColor = vec4( outgoingLight, diffuseColor.a );"
        frag_to = """
            if ( gl_FrontFacing ) {
                gl_FragColor = vec4( outgoingLight, alpha * diffuseColor.a );
            } else {
                gl_FragColor = vec4( diffuseColor.r, diffuseColor.g, diffuseColor.b, alpha * diffuseColor.a );
            }"""
        fragmentShader += shader["fragmentShader"].replace(frag_from, frag_to)

        vertexShader = shader["vertexShader"]
        uniforms = shader["uniforms"]
        uniforms["alpha"] = dict(value=0.7)

        super().__init__(uniforms=uniforms, vertexShader=vertexShader, fragmentShader=fragmentShader)
        self.lights = True

    @property
    def color(self):
        return self.uniforms["diffuse"]["value"]

    @color.setter
    def color(self, value):
        self.update("diffuse", value)

    @property
    def alpha(self):
        return self.uniforms["alpha"]["value"]

    @alpha.setter
    def alpha(self, value):
        self.update("alpha", value)

    def update(self, key, value):
        uniforms = dict(**self.uniforms)
        if self.types.get(key) is None:
            uniforms[key] = {"value": value}
        else:
            uniforms[key] = {"type": self.types.get(key), "value": value}
        self.uniforms = uniforms
        self.needsUpdate = True
