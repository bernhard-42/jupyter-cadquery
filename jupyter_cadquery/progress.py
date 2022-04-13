import time


class Progress:
    """Simple, self deleting progress bar"""

    def __init__(self, max_value, tick="\u2014", length=60):
        """Init the progress bar with the max length"""
        self.max = max_value
        self.tick = tick
        self.length = length
        self.step = length / max_value
        self.value = 0
        self.start = time.time()
        self.reset()

    def update(self, step=1):
        """Update progress and delete when 100% is reached"""
        self.value = min(self.value + step, self.max)
        s = int(round(self.step * self.value, 0))
        r = int(self.value / self.max * 100)
        t = time.time() - self.start
        print(f"\r{r:3d}% \u22ee{self.tick * s}{' ' * (self.length - s)}\u22ee ({self.value}/{self.max}) {t:5.2f}s", end="")

    def done(self):
        """Finalize the progress bar"""
        self.value = self.max
        self.update()
        print()

    def reset(self):
        """Reset the progress bar"""
        self.value = 0
        self.update(0)

    def clear(self):
        """Remove the progress bar"""
        # print("\r" + " " * (self.length + 30))
        print()
