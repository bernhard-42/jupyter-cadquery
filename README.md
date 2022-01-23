# Jupyter-CadQuery

View [CadQuery](https://github.com/cadquery/cadquery) objects in JupyterLab or in a standalone viewer for any IDE

![Overview](screenshots/jupyter-cadquery.png)

Click on the "launch binder" icon to start _Jupyter-CadQuery_ on binder:

[![Binder: Latest development version](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/bernhard-42/jupyter-cadquery/v3.0.0rc0?urlpath=lab&filepath=examples%2Fassemblies%2F1-disk-arm.ipynb)

## Release v3.0.0rc0 (23.01.2022)

Release 3 is a complete rewrite of _Jupyter-CadQuery_: While the selection of _[pythreejs](https://github.com/jupyter-widgets/pythreejs)_ and JupyterLab's _[sidecar](https://github.com/jupyter-widgets/jupyterlab-sidecar)_ looked reasonable in 2019, it turned out they had too many limitations. _pythreejs_ is stuck with an outdated version of _[threejs](https://github.com/mrdoob/three.js/)_ and the _sidecar_ project did not improve usability to a level I would have liked to have.

_Jupyter-CadQuery_ is now a 3 layer project:

1. **[three-cad-viewer](https://github.com/bernhard-42/three-cad-viewer)**
   This is the complete CAD viewer written in Javascript with _[threejs](https://github.com/mrdoob/three.js/)_ being the only dependency. There is are a bunch of [live examples](https://bernhard-42.github.io/three-cad-viewer/example.html) and an [API documentation](https://bernhard-42.github.io/three-cad-viewer/Viewer.html). This layer ould alos serve as the viewer for a CadQuery integration into VS Code (anybody willing to give it a try?)

2. **[cad-view-widget](https://github.com/bernhard-42/cad-viewer-widget)**
   A thin layer on top of _cad-viewer-widget_ that wraps the CAD viewer into an [ipywidget](https://github.com/jupyter-widgets/ipywidgets). The API documentation can be found [here](https://bernhard-42.github.io/cad-viewer-widget/cad_viewer_widget/index.html)

3. **jupyter-cadquery** (this repository)
   The actual CadQuery viewer, collecting and tessellating CadQuery objects, using _cad-view-widget_ to visualize the objects. It was written with the intent to be as compatible with Jupyter-CadQuery 2.x as reasonable. For changes se the migration section below.

**New features**

- Performance

  - By removing the back and forth communication from pythreejs (Python) to Javascript (threejs), the new version is significantly faster in showing multi object assemblies.

- CadQuery feature support

  - Supports the latest **CadQuery Sketch class**.

- New CAD View Controller

  - Besides the _orbit_ controller (with z-axis being restricted to show up) it now also supports a **_trackball_ controller** with full freedom of moving the CAD objects. The trackball controller uses the holroyd algorithm (see e.g. [here](https://www.mattkeeter.com/projects/rotation/)) to have better control of movements and avoid the usual trackball tumpling.

- A full reimplementation of Sidecar:

  - Will be **reused based on name** of the sidecar
  - **Supports differnet anchors** (_right_, _split-right_, _split-left_, _split-top_, _split-bottom_).

- WebGL contexts

  - In a browser only a limited number of WebGL context can be shown at the same time (e.g. 16 in Chrome on my Mac). Hence, _Jupyter-CadQuery_ now thoroughly tracks WebGL contexts, i.e. **releases WebGL context** when sidecar gets closed.

- Replay mode

  - Supports **CadQuery Sketch class**.
  - Replay mode now can **show bounding box** instead of result to compare step with result.

- New features

  - _Jupyter-CadQuery_ now allows to **show all three grids (xy, xz, yz)**
  - CAD viewer icons are scalable svg icons.

- Clipping

  - Clipping supports an **intersection mode**.

- Animation Controller
  - The animation controller is now part of the Javascript component.

**Fixes**

- more than I can remember (or am willing to read out of git log) ...

## Migration from 2.x

**Deprecations:**

- Import structure changed:
  - `from jupyter_cadquery.cadquery import show, ...` will raise a deprecation error:
    Use `from jupyter_cadquery import show, ...` instead.
  - `from jupyter_cadquery.occ import show, ...` will raise a deprecation error:
    Use `from jupyter_cadquery import show, ...` instead.
  - `from jupyter_cadquery.animation import Animation` will raise a deprecation error:
    Use `from jupyter_cadquery.cad_animation import Animation` instead.
- Sidecar handling changed
  - `set_sidecar(title, init=True)` will raise a deprecation error:
    Use `open_viewer(title)` instead.
  - `close_sidecar()` will raise a deprecation error:
    Use `close_viewer(title)` instead.
  - `close_sidecars()` will raise a deprecation error:
    Use `close_viewers(title)` instead.
- Change parameters:
  - Parameter `grid` is now a tuple `(xy-grid, xz-grid, yz-grid)` instead of a boolean. A deprecation warning will be shown and the tuple `(grid, False, False)` used to invoke the old behaviour.

**Changed behaviour:**

- The replay mode now shows the result's bounding box as top level step by default instead of the result. Use `show_result=True` for the old behaviour.
- New parameters `viewer` and `anchor` of function `show` set a sidecar (with title <viewer>) and `anchor` to determine location of the sidecar (`right`, `split-right`, `split-left`, `split-top`, `split-bottom`).
- The parameter `rotation` of function `show` has been replaced by `quaternion`, since the new viewer uses quaternions instead of Euler angles.
- In 7.5 of opencascade something changed with color handling, so some colors might be different.
- The default view does not render the back material, making transparent views brighter. When switching to clipping view, the back material will set to the edge color to give the impression of cut planes. This means that transparent object look darker.

**Parameters of function `show` and `set_defaults` not supported any more:**

- `mac_scrollbar`: This is used as default now.
- `bb_factor`: Not necessary any more.
- `display`: For sidecar display use `viewer="<viewer title>"` and for cell display use `viewer=None`.

## Key Features

- Support for _CadQuery >= 2.1_ (including master at least as of 2021-01-18)
- Viewing options:
  - Directly in the JupyterLab output cell
  - In a central Jupyterlab sidecar for any JupyterLab cell (see example 1 below)
  - As a standalone viewer for use from any IDE (see example 2 below)
- Viewer features
  - Toggle visibilty of shapes and edges
  - Orthographic and perspective view
  - Clipping with max 3 clipping planes (of free orientation)
  - Transparency mode
  - Double click on shapes shows bounding box info
- Assemblies
  - Supports [CadQuery Assemblies](https://cadquery.readthedocs.io/en/latest/assy.html)
  - Support [Manual Assemblies](https://github.com/bernhard-42/cadquery-massembly) with animation of models
- Sketches
  - Support Sketch class for both `show` and `replay`
- Auto display of _CadQuery_ shapes
- Visual debugging by
  - displaying selected _CadQuery_ faces and edges
  - replaying steps of the rendered object (note, this is not supported in the standalone viewer for the time being)

## Examples

1. **Simple Example in JupyterLab using Sidecar (light theme)**

   ![Sidecar](screenshots/sidecar.png)

   To try this yourself, you can use the code [here](#example-code)

2. **Animation system in JupyterLab**

   ![Animated Hexapod in Sidecar](screenshots/hexapod-crawling.gif)

3. **Debugging in VS Code with Standalone Viewer (dark theme)**

   ![Sidecar](screenshots/debugging.gif)

   Note:

   - The top half is the CadQuery code being debugged in VS Code
   - The bottom half is the standalone viewer in a browser window
   - The `show` command in the code will tessellate the objects and send them via [zmq](https://pyzmq.readthedocs.io/en/latest/) to the standalone viewer

## Installation and Usage

1. **Using conda**

   - Create a conda environment with Jupyterlab:

     - If you don't have it already, create a new conda environment with CadQuery 2.1

       ```bash
       conda create -n jcq3 -c conda-forge -c cadquery python=3.8 cadquery
       conda activate jcq3
       ```

     - Install _Jupyter-CadQuery_ (note, matplotlib is only used for the examples)

       ```bash
       pip install jupyter-cadquery==3.0.0rc0 matplotlib
       ```

       Windows users should also install `pywin32` again with `conda` to ensure it is configured correctly

       ```bash
       conda install pywin32
       ```

   - Run _Jupyter-CadQuery_ in **JupyterLab**

     ```bash
     conda activate jcq3
     jupyter lab
     ```

     If you use the dark theme of JuypterLab, add the following code in the first cell of your notebook:

     ```python
     [1]: from jupyter_cadquery import set_defaults, set_sidecar
          set_defaults(theme="dark")
          set_sidecar("CadQuery", init=True)
     ```

   - Run _Jupyter-CadQuery_ as **standalone viewer**

     ```bash
     conda activate jcq3
     jcv     # light theme
     jcv -d  # dark theme
     ```

     In your code import the `show` or `show_object` function from the viewer:

     ```python
     import cadqueray as cq
     from jupyter_cadquery.viewer.client import show, show_object

     obj = cq. ...
     show(obj) # or show_object(obj)
     ```

     `show` works as in JupyterLab, while `show_object` views objects incrementally as in CQ-Editor

2. **Using a docker image**

   - Run _Jupyter-CadQuery_ in **JupyterLab**

     ```bash
     WORKDIR=/tmp/jupyter
     mkdir -p "$WORKDIR"  # this has to exist, otherwise an access error will be thrown
     docker run -it --rm -v $WORKDIR:/home/cq -p 8888:8888 bwalter42/jupyter_cadquery:3.0.0rc0
     ```

     Notes:

     - Jupyter in the container will start in directory `/home/cq`
     - To start with examples, you can
       - omit the volume mapping and just run `docker run -it --rm -p 8888:8888 bwalter42/jupyter_cadquery:3.0.0rc0` or
       - copy the example notebooks to your `$WORKDIR`. They will be available for JupyterLab in the container.
     - If you want to change the Dockerfile, `make docker` will create a new docker image

   - Run _Jupyter-CadQuery_ as **standalone viewer**

     ```bash
     docker run -it --rm -p 8888:8888 -p 5555:5555 bwalter42/jupyter_cadquery:3.0.0rc0 -v [-d]
     ```

     In your code import the `show` or `show_object` function from the viewer:

     ```python
     import cadqueray as cq
     from jupyter_cadquery.viewer.client import show, show_object

     obj = cq. ...
     show(obj) # or show_object(obj)
     ```

     `show` works as in JupyterLab, while `show_object` views objects incrementally as in CQ-Editor

     Notes:

     - To simplify port forwarding, the viewer in the docker container also starts with port 8888 (and not with voila's default port 8866)
     - Port 5555 (the zmq port) needs to be forwarded. The `show` of the viewer client will send cad objects to this port
     - Use `-d` for dark mode

## Demos

_(animated gifs)_

- [Features demo](doc/features.md)
- [Clipping demo](doc/clipping.md)
- [Faces-Edges-Vertices demo](doc/faces-edges-vertices.md)
- [Replay demo](doc/replay.md) (note, this is not supported in the standalone viewer for the time being)
- [OCC demo](doc/occ.md)

## Usage

### a) Show objects

- `show(cad_objs, **kwargs)`

  args:

  - `cad_objs`: Comma separated list of cadquery objects; **Note**: For OCP objects only one object is supported

  kwargs:

  - `height`: Height of the CAD view (default=600)
  - `tree_width`: Width of navigation tree part of the view (default=250)
  - `cad_width`: Width of CAD view part of the view (default=800)
  - `default_color`: Default mesh color (default=(232, 176, 36))
  - `default_edgecolor`: Default mesh color (default=(128, 128, 128))
  - `render_edges`: Render edges (default=True)
  - `render_normals`: Render normals (default=False)
  - `render_mates`: Render mates (for MAssemblies)
  - `mate_scale`: Scale of rendered mates (for MAssemblies)
  - `quality`: Linear deflection for tessellation (default=None). If None, uses: (xlen + ylen + zlen) / 300 \* deviation)
  - `deviation`: Deviation from default for linear deflection value ((default=0.1)
  - `angular_tolerance`: Angular deflection in radians for tessellation (default=0.2)
  - `edge_accuracy`: Presicion of edge discretizaion (default=None). If None, uses: quality / 100
  - `optimal_bb`: Use optimal bounding box (default=False)
  - `axes`: Show axes (default=False)
  - `axes0`: Show axes at (0,0,0) (default=False)
  - `grid`: Show grid (default=False)
  - `ticks`: Hint for the number of ticks in both directions (default=10)
  - `ortho`: Use orthographic projections (default=True)
  - `transparent`: Show objects transparent (default=False)
  - `ambient_intensity` Intensity of ambient ligth (default=1.0)
  - `direct_intensity` Intensity of direct lights (default=0.12)
  - `position`: Relative camera position that will be scaled (default=(1, 1, 1))
  - `rotation`: z, y and y rotation angles to apply to position vector (default=(0, 0, 0))
  - `zoom`: Zoom factor of view (default=2.5)
  - `reset_camera`: Reset camera position, rotation and zoom to default (default=True)
  - `show_parent`: Show the parent for edges, faces and vertices objects
  - `show_bbox`: Show bounding box (default=False)
  - `viewer`: Name of the sidecar viewer
  - `anchor`: How to open sidecar: "right", "split-right", "split-bottom", ...
  - `theme`: Theme "light" or "dark" (default="light")
  - `tools`: Show the viewer tools like the object tree
  - `timeit`: Show rendering times, levels = False, 0,1,2,3,4,5 (default=False)

### b) Manage default values

- `set_defaults(**kwargs)`: allows to globally set the defaults value so they do not need to be provided with every `show` call

  kwargs:

  - see `show`

- `get_default(value)`: Get the global default for a single `value`
- `get_defaults()`: Get all global defaults
- `reset_defaults()`: Reset all defaults back to its initial value

### c) Replay objects

Note, this is not supported in the standalone viewer for the time being.

- `replay(args)`

  args:

  - `cad_obj`: cadquery object
  - `index` (`default=0`): Element in the fluent API stack to show
  - `debug` (`default=False`): Trace building the replay stack
  - `cad_width` (`default=600`): Width of the CAD view
  - `height` (`default=600`): Height of the CAD view

### d) Export as HTML:

1. Export full notebook

   In the first cell of the notebook set output to "html"

   ```python
   set_defaults(display="html")
   ```

   and then use JupyterLab's _File -> Export Notebook as ... -> HTML_ menu entry

   Notes:

   - `display="html"` will automatically turn off tools
   - Browsers can only a set of 8-16 WebGL contexts. So try to have a small number of renderings. If there are too much, they will be shown as black box, that renders after hovering over it.
   - In JupyterLab the widget state needs to be saved automatically for this to work (menu _Settings -> Save Widget State Automatically_)

2. Export single rendering view

   A straight forward approach is to use

   ```python
   w = show(a1)
   ```

   adapt the cad view as wanted (axis, viewpoint, transparency, ...) and then call

   ```python
   from ipywidgets.embed import embed_minimal_html
   embed_minimal_html('export.html', views=[w.cq_view.renderer], title='Renderer')
   ```

   Using `w.cq_view.renderer` this will save the exact state of the visible pythreejs view.

   Of course, you can also call `w = show(a1, *params)` where `params` is the dict of show parameters you'd like to be used and then call the `embed_minimal_html` with `views=w.cq_view.renderer`

   Notes:

   - If you use `sidecar` then you need to close it first:

     ```python
     from jupyter_cadquery import cad_display
     cad_display.SIDECAR.close()
     ```

   - Buttons and treeview can be exported, however the interaction logic of the UI is implemented in Python. So the treeview and the buttons won't have any effect in an exported HTML page. Best is to set `set_defaults(tools=False)` to omit all buttons and the tree

### e) Export the rendered object as STL:

- OCC

  ```python
  from jupyter_cadquery import exportSTL

  exportSTL(a1, "a1.stl", linear_deflection=0.01, angular_deflection=0.1)
  ```

  Smaller `linear_deflection` and `angular_deflection` means more details.

## Jupyter-CadQuery classes

- `Part`: A CadQuery shape plus some attributes for it:

  - `shape`: CadQuery shape
  - `name`: Part name in the view
  - `color`: Part color in the view
  - `show_faces`: show the faces of this particular part
  - `show_edges`: show the edges of this particular part

- `Faces`: CadQuery faces plus some attributes

  - `faces`: List of CadQuery faces (`shape.faces(selector))`)
  - `name`: Part name in the view
  - `color`: Part color in the view
  - `show_faces`: show the faces for these particular faces
  - `show_edges`: show the edges for these particular faces

- `Edges`:

  - `edges`: List of CadQuery edges (`shape.edges(selector))`)
  - `name`: Part name in the view
  - `color`: Part color in the view

- `Vertices`:

  - `vertices`: List of CadQuery vertices (`shape.vertices(selector))`)
  - `name`: Part name in the view
  - `color`: Part color in the view

- `PartGroup`: Basically a list of parts and some attributes for the view:
  - `name`: PartGroup name in the view
  - `objects`: all parts and assemblies included in the assembly as a list

## Example Code

```python
import cadquery as cq
from jupyter_cadquery import (PartGroup, Part, Edges, Faces, Vertices, show, set_viewer, set_defaults)

set_defaults(axes=False, grid=True, axes0=True, ortho=True, transparent=True)
set_sidecar("CadQuery", init=True)

box1 = cq.Workplane('XY').box(10, 20, 30).edges(">X or <X").chamfer(2)
box2 = cq.Workplane('XY').box(8, 18, 28).edges(">X or <X").chamfer(2)
box3 = cq.Workplane('XY').transformed(offset=(0, 15, 7)).box(30, 20, 6).edges(">Z").fillet(3)
box4 = box3.mirror("XY").translate((0, -5, 0))

box1 = box1\
    .cut(box2)\
    .cut(box3)\
    .cut(box4)

a1 = PartGroup(
    [
        Part(box1, "red box",   "#d7191c", show_edges=False),
        Part(box3, "green box", "#abdda4", show_edges=False),
        Part(box4, "blue box",  "#2b83ba", show_faces=False),
    ],
    "example 1"
)

show(a1, grid=False)  # overwrite grid default value
```

## Credits

- Thomas Paviot for [python-occ](https://github.com/tpaviot/pythonocc-core). Ideas are derived/taken from his `jupyter_renderer.py`
- Dave Cowden for [CadQuery](https://github.com/dcowden/cadquery)
- Adam Urbańczyk for the OCP version of [CadQuery](https://github.com/CadQuery/cadquery/tree/master)

## Known issues

- [z-fighting](https://en.wikipedia.org/wiki/Z-fighting) happens some times, especially when using multiple clip planes (cannot be solved in general)
- Using more than one clip plane will lead to cut surfaces not being shown as solid. (very hard to solve in general)
