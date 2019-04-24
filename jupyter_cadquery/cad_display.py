import numpy as np
from os.path import join, dirname

from ipywidgets import ToggleButton, Label, Checkbox, Layout, HBox, VBox, Output, Box, FloatSlider, Tab

from cadquery import Workplane

from .image_button import ImageButton
from .tree_view import TreeView, state_diff, UNSELECTED, SELECTED, MIXED, EMPTY
from .cad_view import CadqueryView
import jupyter_cadquery as jcq  # break import circle


class Clipping(object):

    def __init__(self, image_path, out, cq_view):
        self.image_path = image_path
        self.cq_view = cq_view
        self.out = out
        self.sliders = []
        self.normals = []

    def handler(self, b):
        self.out.append_stdout(str(b.type) + "\n")

    def slider(self, value, min, max, step, description):
        ind = len(self.normals)
        button = ImageButton(
            width=36,
            height=28,
            image_path="%s/plane.png" % (self.image_path),
            tooltip="Set clipping plane",
            type=str(ind),
            layout=Layout(margin="0px 10px 0px 0px"))
        button.on_click(self.handler)
        button.add_class("view_button")

        slider = FloatSlider(
            value=value,
            min=min,
            max=max,
            step=step,
            description="",
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='.2f',
            layout=Layout(width="230px"))

        slider.observe(self.cq_view.clip(ind), "value")
        return [HBox([button, Label(description)]), slider]

    def add_slider(self, value, v_min, v_max, step, normal):
        self.sliders += self.slider(value, v_min, v_max, step, "N=(%5.2f, %5.2f, %5.2f)" % normal)
        self.normals.append(normal)

    def create(self):
        return VBox(self.sliders)


class CadqueryDisplay(object):

    types = ["reset", "fit", "isometric", "right", "front", "left", "rear", "top", "bottom"]
    directions = {
        "left": (1, 0, 0),
        "right": (-1, 0, 0),
        "front": (0, 1, 0),
        "rear": (0, -1, 0),
        "top": (0, 0, 1),
        "bottom": (0, 0, -1),
        "isometric": (1, 1, 1)
    }

    def __init__(self, default_mesh_color=None, default_edge_color=None):
        self.default_mesh_color = default_mesh_color
        self.default_edge_color = default_edge_color

        super().__init__()
        self.output = None
        self.cq_view = None
        self.assembly = None

        self.image_path = join(dirname(__file__), "icons")

        self.image_paths = [
            {
                UNSELECTED: "%s/no_shape.png" % self.image_path,
                SELECTED: "%s/shape.png" % self.image_path,
                MIXED: "%s/mix_shape.png" % self.image_path,
                EMPTY: "%s/empty.png" % self.image_path
            },
            {
                UNSELECTED: "%s/no_mesh.png" % self.image_path,
                SELECTED: "%s/mesh.png" % self.image_path,
                MIXED: "%s/mix_mesh.png" % self.image_path,
                EMPTY: "%s/empty.png" % self.image_path
            }]

    def create_button(self, image_name, handler, tooltip):
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
            self.output.append_stdout("".join([str(m) for m in msg]))
            self.output.append_stdout("\n")
        except:
            print(msg)

    def add_assembly(self, cad_obj):
        result = {}
        if isinstance(cad_obj, jcq.Assembly):
            for obj in cad_obj.objects:
                result.update(self.add_assembly(obj))
        else:
            self.cq_view.add_shape(cad_obj.name, cad_obj.shape, cad_obj.web_color())
            result.update(cad_obj.to_state())
        return result

    def display(self,
                assembly,
                height=600,
                tree_width=250,
                cad_width=800,
                axes=True,
                axes0=True,
                grid=True,
                ortho=True,
                transparent=False,
                mac_scrollbar=True):
        self.assembly = assembly

        ## Threejs rendering of Cadquery objects
        self.cq_view = CadqueryView(
            width=cad_width,
            height=height,
            default_mesh_color=self.default_mesh_color,
            default_edge_color=self.default_edge_color,
            debug=self._debug)
        tree = assembly.to_nav_dict()
        states = self.add_assembly(assembly)
        renderer = self.cq_view.render()
        renderer.add_class("view_renderer")

        # Output widget
        self.output = Output(
            layout=Layout(
                height="%dpx" % (height * 0.4), width="%dpx" % tree_width, overflow_y="scroll", overflow_x="scroll"))
        self.output.add_class("view_output")
        self.output.add_class("scroll_down")

        if mac_scrollbar:
            self.output.add_class("mac-scrollbar")

        bb = self.cq_view.bb
        clipping = Clipping(self.image_path, self.output, self.cq_view)
        for normal in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)):
            clipping.add_slider(bb.max * 1.2, -bb.max * 1.3, bb.max * 1.2, 0.01, normal)

        # Tree widget to change visibility
        tree_view = TreeView(
            image_paths=self.image_paths,
            tree=tree,
            state=states,
            layout=Layout(
                height="%dpx" % (height * 0.6 - 55),
                width="%dpx" % tree_width,
                overflow_y="scroll",
                overflow_x="scroll"))
        tree_view.add_class("view_tree")

        if mac_scrollbar:
            tree_view.add_class("mac-scrollbar")

        mapping = assembly.obj_mapping()
        tree_view.observe(self.cq_view.change_visibility(mapping), "state")

        tab_contents = ['Tree', 'Clipping']
        tree_clipping = Tab(layout=Layout(height="%dpx" % (height * 0.6), width="%dpx" % tree_width))
        tree_clipping.children = [tree_view, clipping.create()]
        for i in range(len(tab_contents)):
            tree_clipping.set_title(i, tab_contents[i])

        # Check controls to swith orto, grid and axis
        check_controls = [
            self.create_checkbox("axes", "Axes", axes, self.cq_view.toggle_axes),
            self.create_checkbox("grid", "Grid", grid, self.cq_view.toggle_grid),
            self.create_checkbox("zero", "@ 0", axes0, self.cq_view.toggle_center),
            self.create_checkbox("ortho", "Ortho", ortho, self.cq_view.toggle_ortho),
            self.create_checkbox("transparent", "Transparency", transparent, self.cq_view.toggle_transparent),
            self.create_checkbox("black_edges", "Black Edges", False, self.cq_view.toggle_black_edges),
        ]
        check_controls[-2].add_class("indent")

        # Set initial state
        self.cq_view.toggle_ortho(ortho)
        self.cq_view.toggle_axes(axes)
        self.cq_view.toggle_center(axes0)
        self.cq_view.toggle_grid(grid)
        self.cq_view.toggle_transparent(transparent)

        for obj, vals in states.items():
            for i, val in enumerate(vals):
                self.cq_view.set_visibility(mapping[obj], i, val)

        # Buttons to switch camera position
        view_controls = []
        for typ in CadqueryDisplay.types:
            if typ == "refit":
                tooltip = "Fit view"
            elif typ == "reset":
                tooltip = "Reset view"
            else:
                tooltip = "Change view to %s" % typ
            button = self.create_button(typ, self.cq_view.change_view(typ, CadqueryDisplay.directions), tooltip)
            view_controls.append(button)

        return HBox([
            VBox([HBox(check_controls[:-2]), tree_clipping, self.output]),
            VBox([HBox(view_controls + check_controls[-2:]), renderer])
        ])
