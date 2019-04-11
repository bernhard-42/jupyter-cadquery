import numpy as np
from os.path import join, dirname

from ipywidgets import ToggleButton, Button, Checkbox, Layout, HBox, VBox, Output

from .image_button import ImageButton
from .tree_view import TreeView, state_diff, UNSELECTED, SELECTED, MIXED, EMPTY
from .cad_view import CadqueryView
from .cad_objects import Assembly, Part


class CadqueryDisplay(object):

    types = ["fit", "isometric", "right", "front", "left", "rear", "top", "bottom"]
    directions = {
        "left":      ( 1,  0,  0),
        "right":     (-1,  0,  0),
        "front":     ( 0,  1,  0),
        "rear":      ( 0, -1,  0),
        "top":       ( 0,  0,  1),
        "bottom":    ( 0,  0, -1),
        "isometric": ( 1,  1,  1)
    }

    def __init__(self):
        self.output = None
        self.cq_view = None
        self.assembly = None

        self.image_path = join(dirname(__file__), "icons")

        self.image_paths = [
            {UNSELECTED: "%s/no_shape.png"  % self.image_path,
             SELECTED:   "%s/shape.png"     % self.image_path,
             MIXED:      "%s/mix_shape.png" % self.image_path,
             EMPTY:      "%s/empty.png"     % self.image_path},
            {UNSELECTED: "%s/no_mesh.png"   % self.image_path,
             SELECTED:   "%s/mesh.png"      % self.image_path,
             MIXED:      "%s/mix_mesh.png"  % self.image_path,
             EMPTY:      "%s/empty.png"     % self.image_path}
        ]

    def create_button(self, image_name, handler):
        button = ImageButton(
            width=36,
            height=28,
            image_path="%s/%s.png" % (self.image_path, image_name),
            tooltip="Change view to %s" % image_name,
            type=image_name)
        button.on_click(handler)
        button.add_class("view_button")
        return button

    def create_checkbox(self, ind, description, handler):
        if ind == 0:
            width = "65px"
        elif ind == 1:
            width = "50px"
        elif ind == 3:
            width = "75px"
        else:
            width = "70px"
        checkbox = Checkbox(value=True, description=description, indent=False, layout=Layout(width=width))
        checkbox.observe(handler, "value")
        return checkbox

    def _debug(self, *msg):
        with self.output:
            print(*msg)

    def addAssembly(self, cad_obj):
        result = {}
        if isinstance(cad_obj, Assembly):
            for obj in cad_obj.objects:
                result.update(self.addAssembly(obj))
        else:
            self.cq_view.addShape(cad_obj.shape, cad_obj.web_color())
            result.update(cad_obj.to_state())
        return result

    def display(self, assembly, height=600, tree_width=250, out_width=600, cad_width=600, mac_scrollbar=True):
        self.assembly = assembly

        ## Threejs rendering of Cadquery objects
        self.cq_view = CadqueryView(width=cad_width, height=height, debug=self._debug)
        tree = assembly.to_nav_dict()
        states = self.addAssembly(assembly)
        renderer = self.cq_view.render()

        # Output widget
        self.output = Output(layout=Layout(height="%dpx"%height, width="%dpx"%out_width,
                              overflow_y="scroll", overflow_x="scroll"))
        if mac_scrollbar:
            self.output.add_class("mac-scrollbar")

        # Tree widget to change visibility
        tree_view = TreeView(image_paths=self.image_paths, tree=tree, state=states,
                             layout=Layout(height="%dpx"%height, width="%dpx"%tree_width,
                             overflow_y="scroll", overflow_x="scroll"))
        if mac_scrollbar:
            tree_view.add_class("mac-scrollbar")

        mapping = assembly.obj_mapping()
        tree_view.observe(self.cq_view.changeVisibility(mapping), "state")

        # Set initial state
        for obj, vals in states.items():
            for i, val in enumerate(vals):
                self.cq_view.setVisibility(mapping[obj], i, val)

        # Check controls to swith orto, grid and axis
        check_controls = [
            self.create_checkbox(0, "Axis (", self.cq_view.toggleAxis),
            self.create_checkbox(1, "0)", self.cq_view.toggleAxisCenter),
            self.create_checkbox(2, "Grid", self.cq_view.toggleGrid),
            self.create_checkbox(3, "Ortho", self.cq_view.toggleOrtho)
        ]

        # Buttons to switch camera position
        view_controls = []
        for typ in CadqueryDisplay.types:
            button = self.create_button(typ, self.cq_view.changeView(typ, CadqueryDisplay.directions))
            view_controls.append(button)

        return HBox([VBox([HBox(check_controls), tree_view]),
                     VBox([HBox(view_controls), renderer]), self.output])