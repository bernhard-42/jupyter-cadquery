import numpy as np
from os.path import join, dirname

from ipywidgets import ToggleButton, Button, Checkbox, Layout, HBox, VBox, Output, Box

from cadquery import Workplane

from .image_button import ImageButton
from .tree_view import TreeView, state_diff, UNSELECTED, SELECTED, MIXED, EMPTY
from .cad_view import CadqueryView
import jupyter_cadquery as jcq # break import circle


class CadqueryDisplay(object):

    types = ["reset", "fit", "isometric", "right", "front", "left", "rear", "top", "bottom"]
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
        super().__init__()
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

    def create_checkbox(self, kind, description, value, handler):
        checkbox = Checkbox(value=value, description=description, indent=False)
        checkbox.observe(handler, "value")
        checkbox.add_class("view_%s" % kind)
        return checkbox

    def _debug(self, *msg):
        try:
            with self.output:
                print(*msg)
        except:
            print(msg)

    def addAssembly(self, cad_obj):
        result = {}
        if isinstance(cad_obj, jcq.Assembly):
            for obj in cad_obj.objects:
                result.update(self.addAssembly(obj))
        else:
            self.cq_view.addShape(cad_obj.shape, cad_obj.web_color())
            result.update(cad_obj.to_state())
        return result

    def display(self, assembly, height=600, tree_width=250, cad_width=800,
                axes=True, axes0=True, grid=True, ortho=True, mac_scrollbar=True):
        self.assembly = assembly

        ## Threejs rendering of Cadquery objects
        self.cq_view = CadqueryView(width=cad_width, height=height, debug=self._debug)
        tree = assembly.to_nav_dict()
        states = self.addAssembly(assembly)
        renderer = self.cq_view.render()
        renderer.add_class("view_renderer")

        # Output widget
        self.output = Output(layout=Layout(height="%dpx" % (height*0.4), width="%dpx" % tree_width,
                              overflow_y="scroll", overflow_x="scroll"))
        self.output.add_class("view_output")

        if mac_scrollbar:
            self.output.add_class("mac-scrollbar")

        # Tree widget to change visibility
        tree_view = TreeView(image_paths=self.image_paths, tree=tree, state=states,
                             layout=Layout(height="%dpx" % (height*0.6), width="%dpx" % tree_width,
                             overflow_y="scroll", overflow_x="scroll"))
        tree_view.add_class("view_tree")

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
            self.create_checkbox("axes",  "Axes",   axes,  self.cq_view.toggleAxes),
            self.create_checkbox("grid",  "Grid",   grid,  self.cq_view.toggleGrid),
            self.create_checkbox("zero",  "@ 0",    axes0, self.cq_view.toggleCenter),
            self.create_checkbox("ortho", "Ortho",  ortho, self.cq_view.toggleOrtho)
        ]
        if not ortho:
            self.cq_view.setOrtho(ortho)

        if not axes:
            self.cq_view.setAxes(axes)

        if not axes0:
            self.cq_view.setCenter(axes0)

        if not grid:
            self.cq_view.setGrid(grid)

        # Buttons to switch camera position
        view_controls = []
        for typ in CadqueryDisplay.types:
            button = self.create_button(typ, self.cq_view.changeView(typ, CadqueryDisplay.directions))
            view_controls.append(button)

        return HBox([VBox([HBox(check_controls),
                        tree_view,
                        self.output]),
                 VBox([HBox(view_controls), renderer])])

