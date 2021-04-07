# jupyter-cadquery

An extension to render cadquery objects in JupyterLab via *[pythreejs](https://pythreejs.readthedocs.io/en/stable/)*.


## New Relase Candidate v2.1.0 "Performance Release" (06.04.2021)
- **New features**
    - Complete new tessellator class. Significantly faster (for a 15MB STEP file it reduced the rendering time from 3 min to <10 sec)
    - Mesh quality is calculated as in FreeCad (sum of bounding box x-, y-, z-widths divided by 300 times deviation paramter)

- **Changes**
    - Pan speed is adapted to object size sum of bounding box x-, y-, z-widths divided by 300)
    - Replay warnings can be suppressed now (`replay(warning=False)`)
## New Relase v2.0.0 (06.03.2021)

- **New features**
    - *jupyter-cadquery* supports the latest *CadQuery 2.1* with *OCP* (note, it will not run with the *FreeCAD* version of *CadQuery*).
    - Uses JupyterLab 3.0 which has a new extension deployment system which simplifies the installation of `jupyter-cadquery` drastically (see below)
    - It supports the new [CadQuery Assemblies](https://cadquery.readthedocs.io/en/latest/assy.html)
    - Splits UI and shape rendering and shows a progress bar during rendering, especially useful for large assembblies
    - If you install `cadquery-massembly` (see below) then the class `MAssembly` (meaning "Mate base Assembly") is available, which is derived from `cadquery.Assembly` but similar to `cqparts` or FreeCad's `Assembly4` works with mates to manually connect instead of constraints and a numerical solver.
    - Comes with an animation system to simulate models built with `MAssembly`

        ![Animated Hexapod in Sidecar](screenshots/hexapod-crawling.gif)

- **Changes**
    - Deprecates *jupyter-cadquery*'s `Assembly` (too many assemblies in the meantime) and has renamed it to `PartGroup` (no semantic change). `Assembly` can still be used with warnings at the moment.
    - Does not test or change the `cqparts` support since the project doesn't seem to be active any more

## Quick use via Binder

Click on the icon to start *jupyter-cadquery* on binder:

[![Binder: Latest development version](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/bernhard-42/jupyter-cadquery/v2.1.0?urlpath=lab&filepath=examples%2Fassemblies%2F1-disk-arm.ipynb)

## Overview

![Overview](screenshots/0_intro.png)

### a) Key features:

- Support for *CadQuery* and *OCP*
- Auto display of *CadQuery* shapes
- Viewer features
    - Jupyterlab sidecar support
    - Toggle visibilty of shapes and edges
    - Orthographic and perspective view
    - Clipping with max 3 clipping planes (of free orientation)
    - Transparency mode
    - Double click on shapes shows bounding box info
- Assemblies
    - Supports [CadQuery Assemblies](https://cadquery.readthedocs.io/en/latest/assy.html)
    - Support [Manual Assemblies](https://github.com/bernhard-42/cadquery-massembly) with animation of models
- Visual debugging by
    - displaying selected *CadQuery* faces and edges
    - replaying steps of the rendered object


### b) Example: CadQuery using Sidecar

```python
import cadquery as cq
from jupyter_cadquery.cadquery import (PartGroup, Part, Edges, Faces, Vertices, show)
from jupyter_cadquery import set_sidecar, set_defaults, reset_defaults

set_sidecar("CadQuery")  # force usage of one cad view on the right
set_defaults(axes=False, grid=True, axes0=True, ortho=True, transparent=True) # Set default values

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

![Sidecar](screenshots/sidecar.png)

## Installation

### a) Using conda

- **Create a conda environment with Jupyterlab:**

    - If you don't have it already, create a new conda environment with CadQuery 2.1

        ```bash
        conda create -n cq21-jl3 -c conda-forge -c cadquery python=3.7 cadquery
        conda activate cq21-jl3
        ```

    - Install jupyter-cadquery (note, matplotlib is only used for the examples)

        ```bash
        pip install jupyter-cadquery==2.1.0 matplotlib
        ```

- **Install cadquery-massembly (Optional)**

    - If you want to use that manual assembly in cadquery, install it via

        ```bash
        pip install git+https://github.com/bernhard-42/cadquery-massembly
        ```
    
- **Run jupyter-cadquery**

    ```bash
    conda activate cq21-jl3
    jupyter lab
    ```

### b) Using a docker image

- Run the docker container (jupyter in the container will start in `/home/cq`)

    ```bash
    WORKDIR=/tmp/jupyter
    mkdir -p "$WORKDIR"  # this has to exists, otherwise an access error will occur
    docker run -it --rm -v $WORKDIR:/home/cq -p 8888:8888 bwalter42/jupyter_cadquery:2.1.0
    ```

    **Notes:** 
    - To start with examples, you can 
        - omit the volume mapping and just run `docker run -it --rm -p 8888:8888 bwalter42/jupyter_cadquery:2.1.0` or
        - copy the example notebooks to your `$WORKDIR`. They will be available for JupyterLab in the container.
    - If you want to change the Dockerfile, `make docker` will create a new docker image

## Demos

*(animated gifs)*

- [Features demo](doc/features.md)
- [Clipping demo](doc/clipping.md)
- [Faces-Edges-Vertices demo](doc/faces-edges-vertices.md)
- [Replay demo](doc/replay.md) (*experimental*)
- [OCC demo](doc/occ.md)

## Usage

### a) Show objects

- `show(cad_objs, **kwargs)`

    args:
    - `cad_objs`: Comma separated list of cadquery objects; **Note**: For OCP objects only one object is supported

    kwargs:
    - `height`:            Height of the CAD view (default=600)
    - `tree_width`:        Width of navigation tree part of the view (default=250)
    - `cad_width`:         Width of CAD view part of the view (default=800)
    - `bb_factor`:         Scale bounding box to ensure compete rendering (default=1.5)
    - `render_shapes`:     Render shapes  (default=True)
    - `render_edges`:      Render edges  (default=True)
    - `render_mates`:      Render mates (for MAssemblies)
    - `mate_scale`:        Scale of rendered mates (for MAssemblies)
    - `quality`:           Linear deflection for tessellation (default=None). If None, uses bounding box as in (xlen + ylen + zlen) / 300 * deviation)
    - `deviation`:         Deviation from default for linear deflection value ((default=0.5)
    - `angular_tolerance`: Angular deflection in radians for tessellation (default=0.3)
    - `edge_accuracy`:     Presicion of edge discretizaion (default=None). If None, uses: quality / 100
    - `optimal_bb`:        Use optimal bounding box (default=False)
    - `axes`:              Show axes (default=False)
    - `axes0`:             Show axes at (0,0,0) (default=False)
    - `grid`:              Show grid (default=False)
    - `ortho`:             Use orthographic projections (default=True)
    - `transparent`:       Show objects transparent (default=False)
    - `position`:          Relative camera position that will be scaled (default=(1, 1, 1))
    - `rotation`:          z, y and y rotation angles to apply to position vector (default=(0, 0, 0))
    - `zoom`:              Zoom factor of view (default=2.5)
    - `mac_scrollbar`:     Prettify scrollbasrs on Macs (default=True)
    - `display`:           Select display: "sidecar", "cell", "html"
    - `tools`:             Show the viewer tools like the object tree
    - `timeit`:            Show rendering times (default=False)

    For example isometric projection can be achieved in two ways:
    - `position = (1, 1, 1)`
    - `position = (0, 0, 1)` and `rotation = (45, 35.264389682, 0)` 
    
### b) Manage default values

- `set_defaults(**kwargs)`

    kwargs: 
    - see `show`

- `get_defaults()`
- `reset_defaults()`

### c) Replay objects

- `replay(args)`

    args:

    - `cad_obj`: cadquery object
    - `index` (`default=0`): Element in the fluent API stack to show
    - `debug` (`default=False`): Trace building the replay stack
    - `cad_width` (`default=600`): Width of the CAD view
    - `height` (`default=600`): Height of the CAD view

### d) Export the rendered object as STL:

- OCC

    ```python
    from jupyter_cadquery import exportSTL

    exportSTL(a1, "a1.stl", linear_deflection=0.01, angular_deflection=0.1)
    ```

    Lower `linear_deflection` and `angular_deflection` means more details.

### e) Export the rendering view as HTML:

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

1. If you use `sidecar`then you need to close it first:

    ```
    from jupyter_cadquery import cad_display
    cad_display.SIDECAR.close()
    ```

2. Buttons and treeview can be exported, however the interaction logic of the UI is implemented in Python. So the treeview and the buttons won't have any effect in an exported HTML page.


## Jupyter_cadquery classes

- `Part`: A CadQuery shape plus some attributes for it:
    - `shape`: Cadquery shape
    - `name`: Part name in the view
    - `color`: Part color in the view
    - `show_faces`: show the faces of this particular part
    - `show_edges`: show the edges of this particular part

- `Faces`: Cadquery faces plus some attributes
    - `faces`: List of cadquery faces (`shape.faces(selector))`)
    - `name`: Part name in the view
    - `color`: Part color in the view
    - `show_faces`: show the faces for these particular faces
    - `show_edges`: show the edges for these particular faces

- `Edges`:
    - `edges`: List of cadquery edges (`shape.edges(selector))`)
    - `name`: Part name in the view
    - `color`: Part color in the view

- `Vertices`:
    - `vertices`: List of cadquery vertices (`shape.vertices(selector))`)
    - `name`: Part name in the view
    - `color`: Part color in the view

- `PartGroup`: Basically a list of parts and some attributes for the view:
    - `name`: PartGroup name in the view
    - `objects`: all parts and assemblies included in the assembly as a list


## Credits

- Thomas Paviot for [python-occ](https://github.com/tpaviot/pythonocc-core). Ideas are derived/taken from his `jupyter_renderer.py`
- Dave Cowden for [CadQuery](https://github.com/dcowden/cadquery)
- Adam Urbańczyk for the OCP version of [CadQuery](https://github.com/CadQuery/cadquery/tree/master)

## Known issues

- [z-fighting](https://en.wikipedia.org/wiki/Z-fighting) happens some times, especially when using multiple clip planes (cannot be solved in general)
- Using more than one clip plane will lead to cut surfaces not being shown as solid. (very hard to solve in general)