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

import base64
from os.path import join, dirname
import pickle
from uuid import uuid4
from IPython.display import display as ipy_display

from ipywidgets import Label, Checkbox, Layout, HBox, VBox, Box, FloatSlider, Tab, HTML, Box, Output

from jupyter_cadquery_widgets.widgets import ImageButton, TreeView, UNSELECTED, SELECTED, MIXED, EMPTY
from .cad_view import CadqueryView
from .utils import Timer, Progress, px
from ._version import __version__
from .defaults import set_defaults, get_default, split_args
from .logo import LOGO_DATA
from .style import set_css

DISPLAY = None
SIDECAR = None


def has_sidecar():
    if SIDECAR is not None:
        return SIDECAR.title
    else:
        return None


def close_sidecar():
    global DISPLAY, SIDECAR

    if SIDECAR is not None:
        SIDECAR.close()

    DISPLAY, SIDECAR = None, None


def set_sidecar(title, init=False):
    global SIDECAR
    try:
        from sidecar import Sidecar

        _has_sidecar = True
    except:
        print("Warning: module sidecar not installed")
        _has_sidecar = False

    if _has_sidecar:
        close_sidecar()
        SIDECAR = Sidecar(title=title)
        set_defaults(display="sidecar")

        if init:
            d = get_or_create_display(init=True)


def reset_sidecar(init=True):
    if SIDECAR is None:
        title = "CadQuery"
    else:
        title = SIDECAR.title

    close_sidecar()
    set_sidecar(title, init)


def get_or_create_display(init=False, **kwargs):
    global DISPLAY

    def resize():
        t = kwargs.get("tree_width")
        w = kwargs.get("cad_width")
        h = kwargs.get("height")
        if w is not None or h is not None:
            DISPLAY.set_size(t, w, h)

    if kwargs.get("display", get_default("display")) != "sidecar" or SIDECAR is None:
        d = CadqueryDisplay()
        widget = d.create(**kwargs)
        ipy_display(widget)
        set_css(get_default("theme"))
        return d

    if DISPLAY is None:
        DISPLAY = CadqueryDisplay()
        widget = DISPLAY.create(**kwargs)
        resize()
        SIDECAR.clear_output(True)
        with SIDECAR:
            ipy_display(widget)

        data = pickle.loads(base64.b64decode(LOGO_DATA))
        mesh_data = data["data"]
        config = data["config"]
        DISPLAY.init_progress(data.get("count", 1))
        create_args, add_shape_args = split_args(config)
        DISPLAY._update_settings(**create_args)
        DISPLAY.add_shapes(**mesh_data, **add_shape_args)
        DISPLAY.info.ready_msg(DISPLAY.cq_view.grid.step)
        DISPLAY.splash = True
        set_css(get_default("theme"), True)

    else:
        # Use the existing Cad Display, so set the defaults and parameters again
        DISPLAY._update_settings(**kwargs)
        resize()
        set_css(get_default("theme"))

    # Change latest settings
    # DISPLAY._update_settings(**kwargs)
    DISPLAY.cq_view.timeit = kwargs.get("timeit", get_default("timeit"))

    return DISPLAY


class Info(object):
    def __init__(self, width=230, height=300):
        self.html = HTML(
            value="",
            layout=Layout(
                width=(px(width)),
                height=(px(height)),
                border="solid 1px #ddd",
                overflow="scroll",
            ),
        )
        self.width = width
        self.height = height
        self.number = 0
        self.chunks = []

    def clear(self):
        self.html.value = ""
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

    def version_msg(self, version):
        self.add_html(
            f"""
        <b>Versions</b>
        <table>
            <tr class="small_table"><td>CadQuery:</td>        <td>{version}</td> </tr>
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
                <th>%s</th><td align='right'>%5.2f</td><td align='right'>%5.2f</td><td align='right'>%5.2f</td>
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

    def set_width(self, width):
        self.width = width
        for slider in self.sliders:
            slider.layout.width = px(width - 20)

    def slider(self, value, min, max, step, description):
        label = Label(description)
        self.labels.append(label)
        ind = len(self.normals)
        button = ImageButton(
            width=36,
            height=28,
            image_path=join(self.image_path, "plane.png"),
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
            layout=Layout(width=px(self.width - 20)),
        )

        slider.observe(self.cq_view.clip(ind), "value")
        return [HBox([button, label]), slider]

    def add_slider(self, value, v_min, v_max, step, normal):
        self.sliders += self.slider(value, v_min, v_max, step, "N=(%5.2f, %5.2f, %5.2f)" % normal)
        self.normals.append(normal)

    def create(self):
        return VBox(self.sliders, layout=Layout(overflow="hidden"))


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

        self.image_path = join(dirname(__file__), "icons", get_default("theme"))

        self.image_paths = [
            {
                UNSELECTED: join(self.image_path, "no_shape.png"),
                SELECTED: join(self.image_path, "shape.png"),
                MIXED: join(self.image_path, "mix_shape.png"),
                EMPTY: join(self.image_path, "empty_shape.png"),
            },
            {
                UNSELECTED: join(self.image_path, "no_mesh.png"),
                SELECTED: join(self.image_path, "mesh.png"),
                MIXED: join(self.image_path, "mix_mesh.png"),
                EMPTY: join(self.image_path, "empty_mesh.png"),
            },
        ]

        self._display = "cell"
        self._tools = True
        self.id = uuid4().hex[:10]
        self.clean = True
        self.splash = False
        self.tree_clipping = None

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
            image_path=join(self.image_path, f"{image_name}.png"),
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
            self.cq_view._reset_camera()

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

    def toggle_axes0(self, change):
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

    def init_progress(self, num_shapes):
        self.progress.progress.value = 0
        self.progress.reset(num_shapes)

    def _set_checkboxes(self):
        self.checkbox_axes.value = self.axes
        self.checkbox_grid.value = self.grid
        self.checkbox_axes0.value = self.axes0
        self.checkbox_ortho.value = self.ortho
        self.checkbox_transparent.value = self.transparent
        self.checkbox_black_edges.value = self.black_edges

    def _update_settings(self, **kwargs):
        preset = lambda key, value: get_default(key) if value is None else value

        self.height = preset("height", kwargs.get("height"))
        self.tree_width = preset("tree_width", kwargs.get("tree_width"))
        self.cad_width = preset("cad_width", kwargs.get("cad_width"))
        self.bb_factor = preset("bb_factor", kwargs.get("bb_factor"))
        self.axes = preset("axes", kwargs.get("axes"))
        self.axes0 = preset("axes0", kwargs.get("axes0"))
        self.grid = preset("grid", kwargs.get("grid"))
        self.ortho = preset("ortho", kwargs.get("ortho"))
        self.transparent = preset("transparent", kwargs.get("transparent"))
        self.black_edges = preset("black_edges", kwargs.get("black_edges"))
        self.mac_scrollbar = preset("mac_scrollbar", kwargs.get("mac_scrollbar"))
        self.timeit = preset("timeit", kwargs.get("timeit"))
        self._display = preset("display", kwargs.get("display"))
        self._tools = preset("tools", kwargs.get("tools"))

    def _info_height(self, height):
        return int(height * 0.4) - 20 + 2

    def _tree_clipping_height(self, height):
        return int(height * 0.6) + 17

    def _tree_height(self, height):
        return int(height * 0.6) - 30

    def set_size(self, tree_width, width, height):
        if width is not None:
            # adapt renderer
            self.cad_width = width
            self.cq_view.camera.width = width
            self.cq_view.renderer.width = width

        if height is not None:
            # adapt renderer
            self.height = height
            self.cq_view.camera.height = height
            self.cq_view.renderer.height = height
            # adapt info box
            info_height = self._info_height(height)
            self.info.height = info_height
            self.info.html.layout.height = px(info_height - 6)
            self.output.layout.height = px(info_height)
            # adapt tree and clipping
            tree_clipping_height = self._tree_clipping_height(height)
            self.tree_clipping.layout.height = px(tree_clipping_height)

            tree_height = self._tree_height(height)
            self.tree_view.layout.height = px(tree_height)

        if tree_width is not None:
            # adapt tree and clipping
            self.tree_clipping.layout.width = px(tree_width)
            self.tree_view.layout.width = px(tree_width)
            self.clipping.set_width(tree_width)
            # adapt info box
            self.output.layout.width = px(tree_width)
            self.info.html.layout.width = px(tree_width)
            # adapt progress bar
            self.progress.progress.layout.width = px(tree_width)

    def create(
        self,
        height=None,
        bb_factor=None,
        tree_width=None,
        cad_width=None,
        axes=None,
        axes0=None,
        grid=None,
        ortho=None,
        transparent=None,
        mac_scrollbar=None,
        display=None,
        tools=None,
        timeit=None,
    ):
        self._update_settings(
            height=height,
            bb_factor=bb_factor,
            tree_width=tree_width,
            cad_width=cad_width,
            axes=axes,
            axes0=axes0,
            grid=grid,
            ortho=ortho,
            transparent=transparent,
            mac_scrollbar=mac_scrollbar,
            display=display,
            tools=tools,
            timeit=timeit,
        )

        # Output widget
        output_height = self._info_height(self.height)
        self.info = Info(self.tree_width, output_height - 6)
        self.info.html.add_class("scroll-area")
        if self.mac_scrollbar:
            self.info.html.add_class("mac-scrollbar")

        ## Threejs rendering of Cadquery objects
        self.cq_view = CadqueryView(
            width=self.cad_width,
            height=self.height,
            info=self.info,
            timeit=self.timeit,
        )

        renderer = self.cq_view.create()
        renderer.add_class("view_renderer")
        renderer.add_class(f"view_renderer_{self.id}")

        # Prepare the CAD view tools
        # Output area

        self.output = Box([self.info.html])
        self.output.layout = Layout(
            height=px(output_height),
            width=px(self.tree_width),
            overflow_y="hidden",
            overflow_x="hidden",
        )
        self.output.add_class("view_output")
        # TODO
        # if get_default("theme") == "dark":
        #     self.output.add_class("p-Collapse-contents")

        # Clipping tool
        self.clipping = Clipping(self.image_path, self.output, self.cq_view, self.tree_width)
        for normal in ((-1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)):
            self.clipping.add_slider(1, -1, 1, 0.01, normal)

        # Empty dummy Tree View
        self.tree_view = Output()
        self.progress = Progress(3, self.tree_width)

        # Tab widget with Tree View and Clipping tools
        self.tree_clipping = Tab(
            layout=Layout(height=px(self._tree_clipping_height(self.height)), width=px(self.tree_width))
        )
        self.tree_clipping.children = [self.tree_view, self.clipping.create()]
        for i, c in enumerate(["Tree", "Clipping"]):
            self.tree_clipping.set_title(i, c)
        self.tree_clipping.observe(self.toggle_clipping)
        self.tree_clipping.add_class("tab-content-no-padding")

        # Check controls to switch orto, grid and axis
        self.checkbox_axes = self.create_checkbox("axes", "Axes", self.axes, self.toggle_axes)
        self.checkbox_grid = self.create_checkbox("grid", "Grid", self.grid, self.toggle_grid)
        self.checkbox_axes0 = self.create_checkbox("zero", "@ 0", self.axes0, self.toggle_axes0)
        self.checkbox_ortho = self.create_checkbox("ortho", "Ortho", self.ortho, self.toggle_ortho)
        self.checkbox_transparent = self.create_checkbox(
            "transparent",
            "Transparency",
            self.transparent,
            self.toggle_transparent,
        )
        self.checkbox_black_edges = self.create_checkbox("black_edges", "Black Edges", False, self.toggle_black_edges)
        self.check_controls = [
            self.checkbox_axes,
            self.checkbox_grid,
            self.checkbox_axes0,
            self.checkbox_ortho,
            self.checkbox_transparent,
            self.checkbox_black_edges,
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

        # only show pure renderer
        if self._tools == False:
            return renderer
        else:
            return HBox(
                [
                    VBox([HBox(self.check_controls[:-2]), self.tree_clipping, self.progress.progress, self.output]),
                    VBox([HBox(self.view_controls + self.check_controls[-2:]), renderer]),
                ]
            )

    def add_shapes(
        self,
        shapes,
        mapping,
        tree,
        bb,
        ticks=None,
        reset_camera=True,
        bb_factor=None,
        ambient_intensity=None,
        direct_intensity=None,
        default_edgecolor=None,
        position=None,
        rotation=None,
        zoom=None,
    ):
        self.clear()
        self.states = {k: v["state"] for k, v in mapping.items()}
        self.paths = {k: v["path"] for k, v in mapping.items()}

        self.tree_view = Output()
        self.tree_clipping.children = [self.tree_view, self.tree_clipping.children[1]]

        # Force reset of camera to inhereit splash settings for first object
        if self.splash:
            reset_camera = True
            self.splash = False

        with Timer(self.timeit, "", "mesh shapes", 2):
            self.cq_view.add_shapes(
                shapes,
                bb,
                ticks,
                self.progress,
                reset_camera=reset_camera,
                bb_factor=bb_factor,
                ambient_intensity=ambient_intensity,
                direct_intensity=direct_intensity,
                default_edgecolor=default_edgecolor,
                position=position,
                rotation=rotation,
                zoom=zoom,
            )

        with Timer(self.timeit, "", "configure display", 2):

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
                layout=Layout(height=px(self._tree_height(self.height)), width=px(self.tree_width - 20)),
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

            self._set_checkboxes()
            self.toggle_axes(self.axes)
            self.toggle_axes0(self.axes0)
            self.toggle_grid(self.grid)
            self.toggle_transparent(self.transparent)
            self.toggle_black_edges(self.black_edges)
            self.toggle_ortho(self.ortho)

            self.clean = False

    def clear(self):
        if not self.clean:
            self.cq_view.clear()
            self.info.clear()

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
