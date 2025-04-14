# Jupyter-CadQuery / Build123d / OCP v4.0.0 (2025-04-...)

**!!! The README is work in progess !!!**

View [CadQuery](https://github.com/cadquery/cadquery), [Build123d](https://github.com/gumyr/build123d), and [OCP](https://github.com/cadquery/OCP) objects in JupyterLab

![Overview](screenshots/jupyter-cadquery.png)

Click on the "launch binder" icon to start _Jupyter-CadQuery_ on binder:

[![Binder: Latest development version](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/bernhard-42/jupyter-cadquery/master?urlpath=lab&filepath=examples%2Fassemblies%2F1-disk-arm.ipynb)

## Overview

_Jupyter-CadQuery_  release 4 is a complete rewrite of _Jupyter-CadQuery_ 3: 

It is now based on:

- the show logic provided by [ocp_vscode](https://github.com/bernhard-42/vscode-ocp-cad-viewer) (_OCP CAD Viewer for VS Code_),
- the viewer is [three-cad-viewer](https://github.com/bernhard-42/three-cad-viewer)
- the tessellation logic provided by [ocp-tessellate](https://github.com/bernhard-42/ocp-tessellate),
- the communication between Python and Javascript provided by [cad-viewer-widget](https://github.com/bernhard-42/cad-viewer-widget), a custom [ipywidget](https://github.com/jupyter-widgets/ipywidgets),
- and the measurement feature (NEW!) provided again by [ocp_vscode](https://github.com/bernhard-42/vscode-ocp-cad-viewer)

**Note:** For changes see the migration section at the end of this page.

## Key Features

- Code CAD support
  - _CadQuery >= 2.5_ including _master_ (as of 2025-04)
  - _Build123d_ >=0.9 including _master_ (as of 2025-04)
  - _OCP_ == 7.8.X (as of 2025-04)
  - Auto display of _CadQuery_ and _Build123d_ shapes
  - Replay mode for CadQuery objects

- Viewing options:
  - Directly in the JupyterLab output cell
  - In a central Jupyterlab sidecar for any JupyterLab cell

- Animations (see examples below)
  - Support [Manual Assemblies](https://github.com/bernhard-42/cadquery-massembly) with animation of model
  - Animated explode mode for _CadQuery_ and _build123d_ assemblies

- Viewer features
  - Clipping with max 3 clipping planes (of free orientation) with cap faces being properly shown
  - Toggle visibility of shapes and edges
  - Orthographic and perspective view
  - Material editor (light intensity, metalness and roughness)
  - Transparency mode
  - Double click on shapes shows bounding box info
  - Click on tree labels shows bounding box info and optionally hides or isolates the elements
  - 

## Examples

### Animation system in JupyterLab

- Self programmed animation

    ![Animated Hexapod](screenshots/hexapod-crawling.gif)

- Explode objects animation

    ![Exploded Quadruped](screenshots/explode.gif)

- Measurement mode

    ![Exploded Quadruped](screenshots/measure.gif)

## Installation

### CadQuery

1. Create and activate a virtual conda environment

    ```python
    mamba create -n jcq4 python=3.12.9
    mamba activate jcq4
    ```

2. Install latest cadquery master

    ```python
    mamba install -c conda-forge -c cadquery cadquery=master
    ```

3. Install and run jupyter-cadquery

    ```python
    pip install jupyter-cadquery

    jupyter lab
    ```

### Build123d

1. Create and activate virtual environment (conda, pyenv-virtualenv, ...)

2. Install build123d

    ```python
    pip install build123d
    ```

3. Install and run jupyter-cadquery

    ```python
    pip install jupyter-cadquery

    jupyter lab
    ```

### Verfiy the installation

Note: On a Mac the first run of the below commands can take minutes until the native libraries OCP and vtk are initialized. Afterwards it takes seconds only.

1. Check Jupyter server extension

    ```bash
    $ jupyter server extension list

    Config dir: /Users/bernhard/.jupyter

    Config dir: /Users/bernhard/.pyenv/versions/3.12.9/envs/jcq4/etc/jupyter
        jupyter_lsp enabled
        - Validating jupyter_lsp...
        jupyter_lsp 2.2.5 OK
        jupyter_cadquery enabled
        - Validating jupyter_cadquery...
    Extension package jupyter_cadquery took 1.6050s to import
        jupyter_cadquery 4.0.0 OK
        jupyter_server_terminals enabled
        - Validating jupyter_server_terminals...
        jupyter_server_terminals 0.5.3 OK
        jupyterlab enabled
        - Validating jupyterlab...
        jupyterlab 4.4.0 OK
        notebook_shim enabled
        - Validating notebook_shim...
        notebook_shim  OK

    Config dir: /usr/local/etc/jupyter
    ```

    You should see `jupyter_cadquery 4.0.0 OK`. This ensures that the measurement backend is properly installed

2. Check Jupyter lab extension

    ```bash
    $ jupyter lab extension list

    Config dir: /Users/bernhard/.jupyter

    Config dir: /Users/bernhard/.pyenv/versions/3.12.9/envs/jcq4/etc/jupyter
        jupyter_lsp enabled
        - Validating jupyter_lsp...
        jupyter_lsp 2.2.5 OK
        jupyter_cadquery enabled
        - Validating jupyter_cadquery...
        jupyter_cadquery 4.0.0 OK
        jupyter_server_terminals enabled
        - Validating jupyter_server_terminals...
        jupyter_server_terminals 0.5.3 OK
        jupyterlab enabled
        - Validating jupyterlab...
        jupyterlab 4.4.0 OK
        notebook_shim enabled
        - Validating notebook_shim...
        notebook_shim  OK

    Config dir: /usr/local/etc/jupyter
    ```

    You should see `jupyter_cadquery 4.0.0 OK`. This ensures that the frontend is properly installed

### Standalone

The *standalone version* of _Jupyter CadQuery_ is now replaced with the one of _OCP CAD Viewer for VS Code_. To start it:

1. Activate your python environment
2. Execute `python -m ocp_vscode [--port 3939]

3939 is the standard port that will be used automatically by the `show` commands


## Demo Notebooks

Standard examples

- [A run through of many features](./examples/1-cadquery.ipynb)
- [Standard CadQuery examples in Jupyter CadQuery](./examples/2-cadquery-examples.ipynb)
- [An OCP example (the OCC bottle)](./examples/3-occ.ipynb)
- [CadQuery Sketch support](./examples/4-sketches.ipynb)
- [Build123d examples](./examples/5-build123d.ipynb)

Animated examples (requires `pip install cadquery-massembly matplotlib`):

- [Rotating disk arm](./examples/assemblies/1-disk-arm.ipynb)
- [Hexapod](./examples/assemblies/2-hexapod.ipynb)
- [Jansen Linkage](./examples/assemblies/3-jansen-linkage.ipynb)
- [CadQuery's door assembly example](./examples/assemblies/5-door.ipynb)
- [A nested Assembly](./examples/assemblies/6-nested-assemblies.ipynb)


## Usage

### a) Show objects

**`show(cad_objs, **kwargs)`\*\*

_Positional arguments `args`:_

- `cad_objs`: Comma separated list of cadquery objects;

_Keywork arguments `kwargs`:_

- Display options

  - `viewer`: Name of the sidecar viewer (default=None)
  - `anchor`: How to open sidecar: "right", "split-right", "split-bottom", ... (default="right")
  - `cad_width`: Width of CAD view part of the view (default=800)
  - `tree_width`: Width of navigation tree part of the view (default=250)
  - `aspect_ratio`: The ratio of height to width (for all non cell viewers)
  - `height`: Height of the CAD view (default=600)
  - `theme`: Theme "light" or "dark" (default="light")
  - `pinning`: Allow replacing the CAD View by a canvas screenshot (default=True in cells, else False)

- Tessellation options

  - `angular_tolerance`: Shapes: Angular deflection in radians for tessellation (default=0.2)
  - `deviation`: Shapes: Deviation from linear deflection value (default=0.1)
  - `edge_accuracy`: Edges: Precision of edge discretization (default=None, i.e. mesh quality / 100)
  - `default_color`: Default face color (default=(232, 176, 36))
  - `default_edge_color`: Default edge color (default="#707070")
  - `optimal_bb`: Use optimal bounding box (default=False)
  - `render_normals`: Render the vertex normals (default=False)
  - `render_edges`: Render edges (default=True)
  - `render_mates`: Render mates (for MAssemblies, default=False)
  - `helper_scale`: Scale of rendered mates (for MAssemblies, default=1)

- Viewer options

  - `control`: Use trackball controls ('trackball') or orbit controls ('orbit') (default='trackball')
  - `up`: Use z-axis ('Z') or y-axis ('Z') as up direction for the camera, legacy behaviour: 'L' (default='Z')
  - `axes`: Show axes (default=False)
  - `axes0`: Show axes at (0,0,0) (default=False)
  - `grid`: Show grid (default=[False, False, False])
  - `ticks`: Hint for the number of ticks in both directions (default=10)
  - `ortho`: Use orthographic projections (default=True)
  - `transparent`: Show objects transparent (default=False)
  - `black_edges`: Show edges in black (default=False)
  - `position`: Absolute camera position that will be scaled (default=None)
  - `quaternion`: Camera rotation as quaternion (x, y, z, w) (default=None)
  - `target`: Camera target to look at (default=None)
  - `zoom`: Zoom factor of view (default=2.5)
  - `reset_camera`: Reset camera position, rotation and zoom to default (default=True)
  - `zoom_speed`: Mouse zoom speed (default=1.0)
  - `pan_speed`: Mouse pan speed (default=1.0)
  - `rotate_speed`: Mouse rotate speed (default=1.0)
  - `ambient_intensity`: Intensity of ambient light (default=0.75)
  - `direct_intensity`: Intensity of direct lights (default=0.15)
  - `show_parent`: Show the parent for edges, faces and vertices objects
  - `tools`: Show the viewer tools like the object tree (default=True)
  - `timeit`: Show rendering times, levels = False, 0,1,2,3,4,5 (default=False)
  - `js_debug`: Enable debug output in browser console (default=False)

### b) Manage default values

- **`set_defaults(**kwargs)`:** allows to globally set the defaults value so they do not need to be provided with every `show` call

    kwargs:

  - see `show`

- **`get_default(value)`:** Get the global default for a single `value`
- **`get_defaults()`:** Get all global defaults
- **`reset_defaults()`**: Reset all defaults back to its initial value

### c) Replay objects

Note, this is not supported in the standalone viewer for the time being.

- **`replay(args)`**

    _Argument `args`:_

  - `cad_obj`: cadquery object
  - `index` (`default=0`): Element in the fluent API stack to show
  - `debug` (`default=False`): Trace building the replay stack
  - `cad_width` (`default=600`): Width of the CAD view
  - `height` (`default=600`): Height of the CAD view

### d) Exports:

- **Export as PNG:**

    Display your object via

    ```python
    cv = show(a1)
    ```

    and adapt the cad view as wanted (camera location, axis, transparency, ...).

    Then call

    ```python
    cv.export_png("example.png")
    ```

- **Export as HTML:**

    Display your object without using a sidecar (set `viewer` to `None`) via

    ```python
    cv = show(a1, viewer=None)
    ```

    and adapt the cad view as wanted (camera location, axis, transparency, ...).

    Then call

    ```python
    cv.export_html()
    ```

    Note: This does not work with viewers in sidecars!


## Release v4.0.0 (2025-04-...)

### Changes

tbd.

### Fixes

tbd.


## Migration from 3.x

**Deprecations:**

tbd.

**Changed behavior:**

tbd.


## Known issues

-   [z-fighting](https://en.wikipedia.org/wiki/Z-fighting) happens some times, especially when using multiple clip planes (cannot be solved in general)

