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
from uuid import uuid4
from IPython.core.display import ProgressBar
from IPython.display import display as ipy_display

from ipywidgets import Label, Checkbox, Layout, HBox, VBox, Box, FloatSlider, Tab, HTML, Box, Output, IntProgress

from jupyter_cadquery_widgets.widgets import ImageButton, TreeView, UNSELECTED, SELECTED, MIXED, EMPTY
import cadquery
from .cad_view import CadqueryView
from .utils import Timer, Progress
from ._version import __version__
from .ocp_utils import is_compound, is_shape, is_solid


class Defaults:
    def __init__(self):
        self.reset_defaults()

    def get_defaults(self):
        return self.defaults

    def get_default(self, key, default_value=None):
        return self.defaults.get(key, default_value)

    def set_defaults(self, **kwargs):
        """Set defaults for CAD viewer

        Valid keywords:
        - height:            Height of the CAD view (default=600)
        - tree_width:        Width of navigation tree part of the view (default=250)
        - cad_width:         Width of CAD view part of the view (default=800)
        - bb_factor:         Scale bounding box to ensure compete rendering (default=1.5)
        - render_shapes:     Render shapes  (default=True)
        - render_edges:      Render edges  (default=True)
        - render_mates:      Render mates (for MAssemblies)
        - mate_scale:        Scale of rendered mates (for MAssemblies)
        - quality:           Tolerance for tessellation (default=0.1)
        - angular_tolerance: Angular tolerance for building the mesh for tessellation (default=0.1)
        - edge_accuracy:     Presicion of edge discretizaion (default=0.01)
        - optimal_bb:        Use optimal bounding box (default=True)
        - axes:              Show axes (default=False)
        - axes0:             Show axes at (0,0,0) (default=False)
        - grid:              Show grid (default=False)
        - ortho:             Use orthographic projections (default=True)
        - transparent:       Show objects transparent (default=False)
        - position:          Relative camera position that will be scaled (default=(1, 1, 1))
        - rotation:          z, y and y rotation angles to apply to position vector (default=(0, 0, 0))
        - zoom:              Zoom factor of view (default=2.5)
        - mac_scrollbar:     Prettify scrollbasrs on Macs (default=True)
        - display:           Select display: "sidecar", "cell", "html"
        - tools:             Show the viewer tools like the object tree
        - timeit:            Show rendering times (default=False)

        For example isometric projection can be achieved in two ways:
        - position = (1, 1, 1)
        - position = (0, 0, 1) and rotation = (45, 35.264389682, 0)
        """

        for k, v in kwargs.items():
            if self.get_default(k) is None:
                print("Paramater %s is not a valid argument for show()" % k)
            else:
                if k == "zoom" and v == 1.0:
                    # for zoom == 1 viewing has a bug, so slightly increase it
                    v = 1 + 1e-6
                self.defaults[k] = v

    def reset_defaults(self):
        self.defaults = {
            "height": 600,
            "tree_width": 250,
            "cad_width": 800,
            "bb_factor": 1.0,
            "render_shapes": True,
            "render_edges": True,
            "render_mates": False,
            "mate_scale": 1,
            "quality": 0.1,
            "edge_accuracy": 0.01,
            "angular_tolerance": 0.1,
            "optimal_bb": True,
            "axes": False,
            "axes0": False,
            "grid": False,
            "ortho": True,
            "transparent": False,
            "position": (1, 1, 1),
            "rotation": (0, 0, 0),
            "zoom": 2.5,
            "mac_scrollbar": True,
            "display": "cell",
            "tools": True,
            "timeit": False,
        }


def get_defaults():
    return DEFAULTS.get_defaults()


def get_default(key, default_value=None):
    return DEFAULTS.get_default(key, default_value)


def set_defaults(**kwargs):
    DEFAULTS.set_defaults(**kwargs)


def reset_defaults():
    DEFAULTS.reset_defaults()


def set_sidecar(title):
    global SIDECAR
    try:
        from sidecar import Sidecar

        SIDECAR = Sidecar(title=title)
        set_defaults(display="sidecar")
    except:
        print("Warning: module sidecar not installed")


SIDECAR = None
DEFAULTS = Defaults()


class Info(object):
    def __init__(self, width=230, height=300):
        self.html = HTML(
            value="",
            layout=Layout(
                width=("%dpx" % width),
                height=("%dpx" % height),
                border="solid 1px #ddd",
                overflow="scroll",
            ),
        )
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
            html += "<td>%s</td>" % chunk
            html += "</tr>"
        html += "</table>"

        self.html.value = html

    def version_msg(self):
        self.add_html(
            f"""
        <b>Versions</b>
        <table>
            <tr class="small_table"><td>CadQuery:</td>        <td>{cadquery.__version__}</td> </tr>
            <tr class="small_table"><td>Jupyter CadQuery:</td><td>{__version__}</td> </tr>
        </table>
        """
        )

    def ready_msg(self, tick_size):
        html = (
            """
        <b>Rendering done</b>
        <table>
            <tr class="small_table" >                      <td>Tick size</td>  <td>%s mm</td> </tr>
            <tr class="small_table" style="color: red;">   <td>X-Axis</td>     <td>Red</td>    </tr>
            <tr class="small_table" style="color: green;"> <td>Y-Axis</td>     <td>Green</td>  </tr>
            <tr class="small_table" style="color: blue;">  <td>Z-Axis</td>     <td>Blue</td>   </tr>
        </table>
        """
            % tick_size
        )
        self.add_html(html)

    def bb_info(self, name, bb):
        html = (
            """
        <b> Object: '%s':</b>
        <table>
        """
            % name
        )
        html += '<tr class="small_table"><th></th><th>min</th><th>max</th><th>center</th></tr>'

        for t, a, c in zip(("x", "y", "z"), bb[:3], bb[3]):
            html += """<tr class="small_table">
                <th>%s</th><td>%5.2f</td><td>%5.2f</td><td>%5.2f</td>
            </tr>
            """ % (
                t,
                a[0],
                a[1],
                c,
            )
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
            layout=Layout(margin="0px 10px 0px 0px"),
        )
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
            orientation="horizontal",
            readout=True,
            readout_format=".2f",
            layout=Layout(width="%dpx" % (self.width - 20)),
        )

        slider.observe(self.cq_view.clip(ind), "value")
        return [HBox([button, label]), slider]

    def add_slider(self, value, v_min, v_max, step, normal):
        self.sliders += self.slider(value, v_min, v_max, step, "N=(%5.2f, %5.2f, %5.2f)" % normal)
        self.normals.append(normal)

    def create(self):
        return VBox(self.sliders)


class CadqueryDisplay(object):

    types = [
        "reset",
        "fit",
        "isometric",
        "right",
        "front",
        "left",
        "rear",
        "top",
        "bottom",
    ]
    directions = {
        "left": (1, 0, 0),
        "right": (-1, 0, 0),
        "front": (0, 1, 0),
        "rear": (0, -1, 0),
        "top": (0, 0, 1),
        "bottom": (0, 0, -1),
        "isometric": (1, 1, 1),
    }

    def __init__(self):
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
                EMPTY: "%s/empty_shape.png" % self.image_path,
            },
            {
                UNSELECTED: "%s/no_mesh.png" % self.image_path,
                SELECTED: "%s/mesh.png" % self.image_path,
                MIXED: "%s/mix_mesh.png" % self.image_path,
                EMPTY: "%s/empty_mesh.png" % self.image_path,
            },
        ]

        self._display = "cell"
        self._tools = True
        self.id = uuid4().hex[:10]
        self.clean = True

    def _dump_config(self):
        print("\nCadDisplay:")
        config = {
            k: v
            for k, v in self.__dict__.items()
            if not k
            in [
                "cq_view",
                "output",
                "info",
                "clipping",
                "tree_clipping",
                "image_paths",
                "image_path",
                "view_controls",
                "check_controls",
            ]
        }
        for k, v in config.items():
            print(f"- {k:30s}: {v}")

        print("\nCadView:")
        config = {
            k: v
            for k, v in self.cq_view.__dict__.items()
            if not k
            in [
                "pickable_objects",
                "scene",
                "controller",
                "renderer",
                "key_lights",
                "picker",
                "shapes",
                "camera",
                "info",
                "axes",
                "grid",
                "cq_renderer",
            ]
        }
        for k, v in config.items():
            print(f"- {k:30s}: {v}")

        print("\nCamera:")
        config = {
            k: v
            for k, v in self.cq_view.camera.__dict__["_trait_values"].items()
            if not k
            in [
                "keys",
                "matrix",
                "matrixWorldInverse",
                "modelViewMatrix",
                "normalMatrix",
                "matrixWorld",
                "projectionMatrix",
                "comm",
            ]
            and not k.startswith("_")
        }
        for k, v in config.items():
            print(f"- {k:30s}: {v}")

    # Buttons

    def create_button(self, image_name, handler, tooltip):
        button = ImageButton(
            width=36,
            height=28,
            image_path="%s/%s.png" % (self.image_path, image_name),
            tooltip=tooltip,
            type=image_name,
        )
        button.on_click(handler)
        button.add_class("view_button")
        return button

    def create_checkbox(self, kind, description, value, handler):
        checkbox = Checkbox(value=value, description=description, indent=False)
        checkbox.observe(handler, "value")
        checkbox.add_class("view_%s" % kind)
        return checkbox

    # UI Handler

    def change_view(self, typ, directions):
        def reset(b):
            self.cq_view._reset()

        def refit(b):
            self.cq_view.camera.zoom = self.cq_view.camera_initial_zoom
            self.cq_view._update()

        def change(b):
            self.cq_view.camera.position = self.cq_view._add(
                self.cq_view.bb.center, self.cq_view._scale(directions[typ])
            )
            self.cq_view._update()

        if typ == "fit":
            return refit
        elif typ == "reset":
            return reset
        else:
            return change

    def bool_or_new(self, val):
        return val if isinstance(val, bool) else val["new"]

    def toggle_axes(self, change):
        self.axes = self.bool_or_new(change)
        self.cq_view.set_axes_visibility(self.axes)

    def toggle_grid(self, change):
        self.grid = self.bool_or_new(change)
        self.cq_view.set_grid_visibility(self.grid)

    def toggle_center(self, change):
        self.axes0 = self.bool_or_new(change)
        self.cq_view.set_axes_center(self.axes0)

    def toggle_ortho(self, change):
        self.ortho = self.bool_or_new(change)
        self.cq_view.toggle_ortho(self.ortho)

    def toggle_transparent(self, change):
        self.transparent = self.bool_or_new(change)
        self.cq_view.set_transparent(self.transparent)

    def toggle_black_edges(self, change):
        self.black_edges = self.bool_or_new(change)
        self.cq_view.set_black_edges(self.black_edges)

    def toggle_clipping(self, change):
        if change["name"] == "selected_index":
            self.cq_view.set_clipping(change["new"])

    def create(
        self,
        render_shapes=None,
        render_edges=None,
        height=None,
        bb_factor=None,
        tree_width=None,
        cad_width=None,
        quality=None,
        angular_tolerance=None,
        optimal_bb=None,
        edge_accuracy=None,
        axes=None,
        axes0=None,
        grid=None,
        ortho=None,
        transparent=None,
        position=None,
        rotation=None,
        zoom=None,
        mac_scrollbar=None,
        display=None,
        tools=None,
        timeit=None,
    ):
        def preset(key, value):
            return get_default(key) if value is None else value

        self.height = preset("height", height)
        self.tree_width = preset("tree_width", tree_width)
        self.cad_width = preset("cad_width", cad_width)
        self.bb_factor = preset("bb_factor", bb_factor)
        self.render_shapes = preset("render_shapes", render_shapes)
        self.render_edges = preset("render_edges", render_edges)
        self.quality = preset("quality", quality)
        self.angular_tolerance = preset("angular_tolerance", angular_tolerance)
        self.optimal_bb = preset("optimal_bb", optimal_bb)
        self.edge_accuracy = preset("edge_accuracy", edge_accuracy)
        self.axes = preset("axes", axes)
        self.axes0 = preset("axes0", axes0)
        self.grid = preset("grid", grid)
        self.ortho = preset("ortho", ortho)
        self.transparent = preset("transparent", transparent)
        self.position = preset("position", position)
        self.rotation = preset("rotation", rotation)
        self.zoom = preset("zoom", zoom)
        self.mac_scrollbar = (platform.system() == "Darwin") and preset("mac_scrollbar", mac_scrollbar)
        self.timeit = preset("timeit", timeit)
        self._display = preset("display", display)
        self._tools = preset("tools", tools)
        self.black_edges = False

        # Output widget
        output_height = self.height * 0.4 - 20 + 2
        self.info = Info(self.tree_width, output_height - 6)
        self.info.html.add_class("scroll-area")

        ## Threejs rendering of Cadquery objects
        self.cq_view = CadqueryView(
            width=self.cad_width,
            height=self.height,
            bb_factor=self.bb_factor,
            quality=self.quality,
            edge_accuracy=self.edge_accuracy,
            angular_tolerance=self.angular_tolerance,
            optimal_bb=self.optimal_bb,
            render_shapes=self.render_shapes,
            render_edges=self.render_edges,
            info=self.info,
            position=self.position,
            rotation=self.rotation,
            zoom=self.zoom,
            timeit=self.timeit,
        )

        renderer = self.cq_view.create()
        renderer.add_class("view_renderer")
        renderer.add_class(f"view_renderer_{self.id}")

        # Prepare the CAD view tools
        # Output area

        self.output = Box([self.info.html])
        self.output.layout = Layout(
            height="%dpx" % output_height,
            width="%dpx" % self.tree_width,
            overflow_y="scroll",
            overflow_x="scroll",
        )
        self.output.add_class("view_output")

        # Clipping tool
        self.clipping = Clipping(self.image_path, self.output, self.cq_view, self.tree_width)
        for normal in ((-1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)):
            self.clipping.add_slider(1, -1, 1, 0.01, normal)

        # Empty dummy Tree View
        self.tree_view = Output()

        # Tab widget with Tree View and Clipping tools
        self.tree_clipping = Tab(
            layout=Layout(height="%dpx" % (self.height * 0.6 + 20), width="%dpx" % self.tree_width)
        )
        self.tree_clipping.children = [self.tree_view, self.clipping.create()]
        for i, c in enumerate(["Tree", "Clipping"]):
            self.tree_clipping.set_title(i, c)
        self.tree_clipping.observe(self.toggle_clipping)
        self.tree_clipping.add_class("tab-content-no-padding")

        # Check controls to swith orto, grid and axis
        self.check_controls = [
            self.create_checkbox("axes", "Axes", self.axes, self.toggle_axes),
            self.create_checkbox("grid", "Grid", self.grid, self.toggle_grid),
            self.create_checkbox("zero", "@ 0", self.axes0, self.toggle_center),
            self.create_checkbox("ortho", "Ortho", self.ortho, self.toggle_ortho),
            self.create_checkbox(
                "transparent",
                "Transparency",
                self.transparent,
                self.toggle_transparent,
            ),
            self.create_checkbox("black_edges", "Black Edges", False, self.toggle_black_edges),
        ]
        self.check_controls[-2].add_class("indent")

        # Buttons to switch camera position
        self.view_controls = []
        for typ in CadqueryDisplay.types:
            if typ == "refit":
                tooltip = "Fit view"
            elif typ == "reset":
                tooltip = "Reset view"
            else:
                tooltip = "Change view to %s" % typ
            button = self.create_button(typ, self.change_view(typ, CadqueryDisplay.directions), tooltip)
            self.view_controls.append(button)

        self.info.version_msg()

        # only show pure renderer
        if self._tools == False:
            return renderer
        else:
            return HBox(
                [
                    VBox([HBox(self.check_controls[:-2]), self.tree_clipping, self.output]),
                    VBox([HBox(self.view_controls + self.check_controls[-2:]), renderer]),
                ]
            )

    def add_shapes(self, shapes, mapping, tree, reset=True):
        def count_shapes(shapes):
            count = 0
            for shape in shapes["parts"]:
                if shape.get("parts") is None:
                    count += 1
                else:
                    count += count_shapes(shape)
            return count

        self.clear()
        self.states = {k: v["state"] for k, v in mapping.items()}
        self.paths = {k: v["path"] for k, v in mapping.items()}

        self.tree_view = Output()
        self.tree_clipping.children = [self.tree_view, self.tree_clipping.children[1]]
        self.progress = Progress(count_shapes(shapes) + 3)
        with self.tree_view:
            ipy_display(self.progress.progress)

        add_shapes_timer = Timer(self.timeit, "add shapes")
        self.cq_view.add_shapes(shapes, self.progress, reset=reset)
        add_shapes_timer.stop()

        configure_display_timer = Timer(self.timeit, "configure display")

        def set_slider(i, s_min, s_max):
            s_min = -0.02 if abs(s_min) < 1e-4 else s_min * self.bb_factor
            s_max = 0.02 if abs(s_max) < 1e-4 else s_max * self.bb_factor
            self.clipping.sliders[i].max = 2 ** 31  #  first increase max to avoid traitlet error that min > max
            self.clipping.sliders[i].min = s_min  # set min which now is always < max
            self.clipping.sliders[i].max = s_max  # correct max
            self.clipping.sliders[i].value = s_max

        bb = self.cq_view.bb
        set_slider(1, bb.xmin, bb.xmax)
        set_slider(3, bb.ymin, bb.ymax)
        set_slider(5, bb.zmin, bb.zmax)

        # Tree widget to change visibility
        self.tree_view = TreeView(
            image_paths=self.image_paths,
            tree=tree,
            state=self.states,
            layout=Layout(height="%dpx" % (self.height * 0.6 - 25), width="%dpx" % (self.tree_width - 20)),
        )
        self.tree_view.add_class("view_tree")
        self.tree_view.add_class("scroll-area")
        if self.mac_scrollbar:
            self.tree_view.add_class("mac-scrollbar")

        self.tree_view.observe(self.cq_view.change_visibility(self.paths), "state")
        self.tree_clipping.children = [self.tree_view, self.tree_clipping.children[1]]

        # Set initial state

        for obj, vals in self.states.items():
            for i, val in enumerate(vals):
                self.cq_view.set_visibility(self.paths[obj], i, val)

        self.toggle_axes(self.axes)
        self.toggle_center(self.axes0)
        self.toggle_grid(self.grid)
        self.toggle_transparent(self.transparent)
        self.toggle_black_edges(self.black_edges)
        self.toggle_ortho(self.ortho)

        self.clean = False
        configure_display_timer.stop()
        if SIDECAR is not None:
            print("Done, using side car '%s'" % SIDECAR.title)

    def clear(self):
        if not self.clean:
            self.cq_view.clear()

            # clear tree
            self.tree_clipping.children = [Output(), self.tree_clipping.children[1]]

            self.clean = True

    def display(self, widget):
        if self._display == "cell" or SIDECAR is None:
            ipy_display(widget)
        else:
            SIDECAR.clear_output(True)
            with SIDECAR:
                ipy_display(widget)

    @property
    def root_group(self):
        return self.cq_view.root_group
