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

import platform
from os.path import join, dirname
import numpy as np

from ipywidgets import ToggleButton, Label, Checkbox, Layout, HBox, VBox, Output, Box, FloatSlider, Tab, HTML, Box
from IPython.display import display

from .widgets import ImageButton, TreeView, state_diff, UNSELECTED, SELECTED, MIXED, EMPTY
from .cad_view import CadqueryView

SIDECAR = None


class Info(object):

    def __init__(self, width=230, height=300):
        self.html = HTML(
            value="",
            layout=Layout(width=("%dpx" % width), height=("%dpx" % height), border="solid 1px #ddd", overflow="scroll"))
        self.width = width
        self.height = height
        self.number = 0
        self.chunks = []

    def add_text(self, msg):
        self.add_html('<pre style="white-space: nowrap;">%s</pre>' % msg)

    def add_html(self, html):
        self.chunks.insert(0, (self.number, html))
        self.number += 1
        self.render()

    def render(self):
        html = '<table style="display: block; overflow-x: visible; white-space: nowrap;">'

        for n, chunk in self.chunks:
            html += '<tr style="vertical-align: text-top;">'
            html += '<td><pre style="color: #aaa; white-space: nowrap">[%2d]</pre></td>' % n
            html += '<td>%s</td>' % chunk
            html += "</tr>"
        html += "</table>"

        self.html.value = html

    def ready_msg(self, tick_size):
        html = """
        <b>Rendering done</b>
        <table>
            <tr class="small_table" >                      <td>Tick size</td>  <td>%s mm</td> </tr>
            <tr class="small_table" style="color: red;">   <td>X-Axis</td>     <td>Red</td>    </tr>
            <tr class="small_table" style="color: green;"> <td>Y-Axis</td>     <td>Green</td>  </tr>
            <tr class="small_table" style="color: blue;">  <td>Z-Axis</td>     <td>Blue</td>   </tr>
        </table>
        """ % tick_size
        self.add_html(html)

    def bb_info(self, name, bb):
        html = """
        <b> Object: '%s':</b>
        <table>
        """ % name
        html += '<tr class="small_table"><th></th><th>min</th><th>max</th><th>center</th></tr>'

        for t, a, c in zip(("x", "y", "z"), bb[:3], bb[3]):
            html += """<tr class="small_table">
                <th>%s</th><td>%5.2f</td><td>%5.2f</td><td>%5.2f</td>
            </tr>
            """ % (t, a[0], a[1], c)
        html += "</table>"
        self.add_html(html)


class Clipping(object):

    def __init__(self, image_path, out, cq_view, width):
        self.image_path = image_path
        self.cq_view = cq_view
        self.out = out
        self.width = width
        self.sliders = []
        self.normals = []
        self.labels = []

    def handler(self, b):
        i = int(b.type)
        self.cq_view.set_plane(i)
        self.labels[i].value = "N=(%5.2f, %5.2f, %5.2f)" % tuple(self.cq_view.direction())

    def slider(self, value, min, max, step, description):
        label = Label(description)
        self.labels.append(label)
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
            layout=Layout(width="%dpx" % (self.width - 20)))

        slider.observe(self.cq_view.clip(ind), "value")
        return [HBox([button, label]), slider]

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
        self.info = None
        self.cq_view = None
        self.assembly = None

        self.image_path = join(dirname(__file__), "icons")

        self.image_paths = [
            {
                UNSELECTED: "%s/no_shape.png" % self.image_path,
                SELECTED: "%s/shape.png" % self.image_path,
                MIXED: "%s/mix_shape.png" % self.image_path,
                EMPTY: "%s/empty_shape.png" % self.image_path
            },
            {
                UNSELECTED: "%s/no_mesh.png" % self.image_path,
                SELECTED: "%s/mesh.png" % self.image_path,
                MIXED: "%s/mix_mesh.png" % self.image_path,
                EMPTY: "%s/empty_mesh.png" % self.image_path
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

    def write(self, *msg):
        try:
            self.info.add_text(" ".join([str(m) for m in msg]))
        except:
            print(msg)

    def create(self,
                states,
                shapes,
                mapping,
                tree,
                height=600,
                tree_width=250,
                cad_width=800,
                quality=0.5,
                edge_accuracy=0.5,
                axes=True,
                axes0=False,
                grid=True,
                ortho=True,
                transparent=False,
                position=None,
                rotation=None,
                zoom=None,
                mac_scrollbar=True,
                timeit=False):

        if platform.system() != "Darwin":
            mac_scrollbar = False

        # Output widget
        output_height = height * 0.4 - 20 + 2
        self.info = Info(tree_width, output_height - 6)

        self.info.html.add_class("scroll-area")
        if mac_scrollbar:
            self.info.html.add_class("mac-scrollbar")

        self.output = Box([self.info.html])
        self.output.layout = Layout(
            height="%dpx" % output_height, width="%dpx" % tree_width, overflow_y="scroll", overflow_x="scroll")

        self.output.add_class("view_output")

        ## Threejs rendering of Cadquery objects
        self.cq_view = CadqueryView(
            width=cad_width,
            height=height,
            quality=quality,
            edge_accuracy=edge_accuracy,
            default_mesh_color=self.default_mesh_color,
            default_edge_color=self.default_edge_color,
            info=self.info,
            timeit=timeit)

        for shape in shapes:
            self.cq_view.add_shape(shape["name"], shape["shape"], shape["color"])
        renderer = self.cq_view.render(position, rotation, zoom)
        renderer.add_class("view_renderer")

        bb = self.cq_view.bb
        clipping = Clipping(self.image_path, self.output, self.cq_view, tree_width)
        for normal in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)):
            clipping.add_slider(bb.max * 1.2, -bb.max * 1.3, bb.max * 1.2, 0.01, normal)

        # Tree widget to change visibility
#       tree_height = height - output_height - 35
        tree_view = TreeView(
            image_paths=self.image_paths,
            tree=tree,
            state=states,
            layout=Layout(
                height="%dpx" % (height * 0.6 - 25),
                width="%dpx" % (tree_width - 20)))
        tree_view.add_class("view_tree")
        tree_view.add_class("scroll-area")
        if mac_scrollbar:
            tree_view.add_class("mac-scrollbar")

        tree_view.observe(self.cq_view.change_visibility(mapping), "state")

        tab_contents = ['Tree', 'Clipping']
        tree_clipping = Tab(layout=Layout(height="%dpx" % (height * 0.6 + 20), width="%dpx" % tree_width))
        tree_clipping.children = [tree_view, clipping.create()]
        for i in range(len(tab_contents)):
            tree_clipping.set_title(i, tab_contents[i])
        tree_clipping.add_class("tab-content-no-padding")

        # Check controls to swith orto, grid and axis
        self.check_controls = [
            self.create_checkbox("axes", "Axes", axes, self.cq_view.toggle_axes),
            self.create_checkbox("grid", "Grid", grid, self.cq_view.toggle_grid),
            self.create_checkbox("zero", "@ 0", axes0, self.cq_view.toggle_center),
            self.create_checkbox("ortho", "Ortho", ortho, self.cq_view.toggle_ortho),
            self.create_checkbox("transparent", "Transparency", transparent, self.cq_view.toggle_transparent),
            self.create_checkbox("black_edges", "Black Edges", False, self.cq_view.toggle_black_edges),
        ]
        self.check_controls[-2].add_class("indent")

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
        self.view_controls = []
        for typ in CadqueryDisplay.types:
            if typ == "refit":
                tooltip = "Fit view"
            elif typ == "reset":
                tooltip = "Reset view"
            else:
                tooltip = "Change view to %s" % typ
            button = self.create_button(typ, self.cq_view.change_view(typ, CadqueryDisplay.directions), tooltip)
            self.view_controls.append(button)

        return HBox([
            VBox([HBox(self.check_controls[:-2]), tree_clipping, self.output]),
            VBox([HBox(self.view_controls + self.check_controls[-2:]), renderer])
        ])


    def sidecar_display(self, widget, sidecar):
        sidecar.clear_output(True)
        with sidecar:
            display(widget)
        print("Done, using side car '%s'" % sidecar.title)


    def display(self, widget, sidecar=None):
        if sidecar is None:
            if SIDECAR is None:
                display(widget)
            else:
                self.sidecar_display(widget, SIDECAR)
        else:
            if not sidecar:  # global sidecar setting overwritten by False
                display(widget)
            else:  # use provided sidecar
                self.sidecar_display(widget, sidecar)


def set_sidecar(title):
    global SIDECAR
    try:
        from sidecar import Sidecar
        SIDECAR = Sidecar(title=title)
    except:
        print("Warning: module sidecar not installed")
