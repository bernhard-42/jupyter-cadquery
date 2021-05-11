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

from math import pi
import numpy as np
from scipy.spatial.transform import Rotation as R
from cadquery import Workplane, Location
from pythreejs import (
    NumberKeyframeTrack,
    AnimationAction,
    AnimationClip,
    AnimationMixer,
    BooleanKeyframeTrack,
    ColorKeyframeTrack,
    QuaternionKeyframeTrack,
    StringKeyframeTrack,
    VectorKeyframeTrack,
)
from .viewer.client import send


def _d2r(x):
    return x / 180 * pi


class AnimationException(BaseException):
    ...


valid_transforms = ["t", "tx", "ty", "tz", "q", "rx", "ry", "rz"]


class Animation:
    def __init__(self, root=None, viewer=False):
        if viewer and root is not None:
            print("Viewer can only animate last root, so parameter has to be None")
        elif not viewer and root is None:
            print("root group of assembly needs to be provided")

        self.viewer = viewer
        self.root = root
        self.tracks = []

    def add_track(self, selector, action, times, values):

        if self.viewer:
            self.tracks.append((selector, action, times, values))
            return

        if len(times) != len(values):
            raise AnimationException("times and values arrays need have the same lenght")

        selector = selector.replace("/", "\\")
        group = self.root.find_group(selector)
        if group is None:
            raise AnimationException(f"group '{selector}' not found")

        if action.startswith("t"):
            position = np.array(group.position).astype(np.float32)
            if action == "t":
                new_values = [position + v for v in values]
            elif action == "tx":
                new_values = [position + (v, 0, 0) for v in values]
            elif action == "ty":
                new_values = [position + (0, v, 0) for v in values]
            elif action == "tz":
                new_values = [position + (0, 0, v) for v in values]
            else:
                raise AnimationException(f"action {action} is not supported")

            self.tracks.append(
                NumberKeyframeTrack(
                    name=selector + ".position",
                    times=np.array(times).astype(np.float32),
                    values=new_values,
                )
            )

        else:
            if action.startswith("r"):
                r_values = np.array([_d2r(v) for v in values]).astype(np.float32)

                actual = R.from_quat(group.quaternion)
                if action == "rx":
                    rot_values = [R.from_rotvec((v, 0, 0)) for v in r_values]
                elif action == "ry":
                    rot_values = [R.from_rotvec((0, v, 0)) for v in r_values]
                elif action == "rz":
                    rot_values = [R.from_rotvec((0, 0, v)) for v in r_values]
                else:
                    raise AnimationException(f"action {action} not supported")
                new_values = [(actual * rot).as_quat() for rot in rot_values]

            elif action == "q":
                actual = R.from_quat(group.quaternion)
                new_values = [tuple((actual * R.from_quat(q)).as_quat()) for q in values]

            else:
                raise AnimationException(f"action {action} is not supported")

            self.tracks.append(
                QuaternionKeyframeTrack(
                    name=selector + ".quaternion",
                    times=np.array(times).astype(np.float32),
                    values=new_values,
                )
            )

    def animate(self, speed=1, autoplay=False):
        if self.viewer:
            data = {"tracks": self.tracks, "type": "animation", "speed": speed, "autoplay": autoplay}
            send(data)
            return

        if speed != 1:
            for track in self.tracks:
                track.times = track.times / float(speed)
        clip = AnimationClip(tracks=self.tracks)
        action = AnimationAction(AnimationMixer(self.root), clip, self.root)
        if autoplay:
            action.play()
        return action
