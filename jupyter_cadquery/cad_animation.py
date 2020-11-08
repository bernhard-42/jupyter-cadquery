from math import pi
import numpy as np
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


class Animation:
    def __init__(self, assembly):
        self.root = assembly
        self.tracks = []

    def add_boolean_track(self, name, times, values):
        self.tracks.append(BooleanKeyframeTrack(name=name, times=times, values=values))

    def add_color_track(self, name, times, values):
        self.tracks.append(ColorKeyframeTrack(name=name, times=times, values=values))

    def add_number_track(self, name, times, values):
        if len(times) != len(values):
            raise AnimationException(
                "times and values arrays need have the same lenght"
            )

        values = np.array(values).astype(np.float32)
        times = np.array(times).astype(np.float32)

        group_name, action = name.split(".")
        group = self.root.find_group(group_name)

        if group is not None:
            if action.startswith("rotation"):
                r_values = np.array([_d2r(v) for v in values]).astype(np.float32)
                angle = 0
                if action == "rotation":
                    values = r_values + group.rotation
                elif action == "rotation[x]":
                    angle = group.rotation[0]
                elif action == "rotation[y]":
                    angle = group.rotation[1]
                elif action == "rotation[z]":
                    angle = group.rotation[2]
                values = r_values + angle
            elif action.startswith("position"):
                position = np.array(group.position).astype(np.float32)
                if action == "position":
                    values += position
                elif action == "position[x]":
                    values += position[0]
                elif action == "position[y]":
                    values += position[1]
                elif action == "position[z]":
                    values += position[2]
        else:
            raise AnimationException(f"group {group_name} not found")

        self.tracks.append(NumberKeyframeTrack(name=name, times=times, values=values))

    def add_quaternion_track(self, name, times, values):
        self.tracks.append(
            QuaternionKeyframeTrack(name=name, times=times, values=values)
        )

    def add_string_track(self, name, times, values):
        self.tracks.append(StringKeyframeTrack(name=name, times=times, values=values))

    def add_vector_track(self, name, times, values):
        self.tracks.append(VectorKeyframeTrack(name=name, times=times, values=values))

    def animate(self, speed=1, autoplay=False):
        for track in self.tracks:
            track.times /= speed
        clip = AnimationClip(tracks=self.tracks)
        action = AnimationAction(AnimationMixer(self.root), clip, self.root)
        if autoplay:
            action.play()
        return action
