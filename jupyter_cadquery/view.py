from ipywidgets import ToggleButton, Button, Checkbox, Layout, HBox
from .image_button import ImageButton
import numpy as np


class ViewWidgets(object):

    def __init__(self, view, image_path):
        self.image_path = image_path
        self.view = view

    def create_button(self, image_name, handler):
        button = ImageButton(
            width=36,
            height=28,
            image_path="%s/%s.png" % (self.image_path, image_name),
            tooltip="Change view to %s" % image_name,
            type=image_name)
        button.on_click(handler)
        return button
        
    def create_checkbox(self, kind, handler):
        checkbox = Checkbox(value=True, description=kind, indent=False, layout=Layout(width="65px"))
        checkbox.observe(handler, "value")
        return checkbox