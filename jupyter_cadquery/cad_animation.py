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


def _d2r(x):
    return x / 180 * pi


class AnimationException(BaseException):
    ...


valid_transforms = ["t", "tx", "ty", "tz", "q", "rx", "ry", "rz"]


class Animation:
    def __init__(self, assembly):
        self.root = assembly
        self.tracks = []

    def add_track(self, selector, action, times, values):
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
        if speed != 1:
            for track in self.tracks:
                track.times = track.times / float(speed)
        clip = AnimationClip(tracks=self.tracks)
        action = AnimationAction(AnimationMixer(self.root), clip, self.root)
        if autoplay:
            action.play()
        return action
