from cad_viewer_widget import AnimationTrack
from jupyter_cadquery.viewer import animate as viewer_animate


class Animation:
    def __init__(self, viewer=None):
        self.tracks = []
        self.viewer = viewer
        self.reset()

    def add_track(self, path, action, times, values):
        if path[0] != "/":
            path = f"/{path}"
        if self.viewer is None:
            self.tracks.append(AnimationTrack(path, action, times, values))
        else:
            self.viewer.add_track(AnimationTrack(path, action, times, values))

    def animate(self, speed=1):
        if self.viewer is None:
            viewer_animate(self.tracks, speed=speed)
        else:
            self.viewer.animate(speed=speed)

    def reset(self):
        if self.viewer is not None:
            self.viewer.clear_tracks()
