# Changelog

## Release v3.1.0 (xx.04.2022)

### New features:

- **Performance**

  - Change exchange of shapes and tracks from Python to Javascript to binary mode
  - Introduced LRU cache for tessellation results (128MB default)
  - Introduced LRU cache for bounding box calculation
  - Introduced multiprocessing for large assemblies (10s to 100s objects)

- **Step reader**

  - Added import function for STEP files into CadQuery assemblies preserving names and colors
  - Added save_assembly/load_assembly to quickly store and load parsed STEP files

- **Animation system**

  - Introduced slider for animation
  - Added animated explode mode for CadQuery assemblies based on Animation system

- **Bounding Box**

  - Removed OCCT bounding box algorithm and created a fast and precise top level bounding box after tessellation via numpy
  - Show bounding box (AABB) on tree click or cad view double click

- **CAD view**

  - Element isolation
    - Added feature to isolate elements (shift double click or shift click on navigation tree)
    - Isolated objects are centered around the center of elements bounding box
  - Added highlighting of tree nodes when element picked
  - Added remove elements via navigation tree (meta click)

- **UI**
  - Introduced light progress bar for assemblies
  - Parameters cad_width, tree_width and height can be changed after view is opened
  - Introduce glass mode
  - Hide checkbox options behind a 'More' menu for small CAD viewers
  - Enable auto-dark mode according to browser setting (added 'browser' mode to theme keyword)
  - Added highlighting for the most recent selected view button
  - Added tree collapsing/expanding buttons
  - Extend help for new features

### Fixes:

- Change radio button behaviour to standard behaviour
- Send notifications for changed "target" parameter
- Fixed slider color for Safari
- Fixed scrollbar for Firefox
- Fixed initial zoom for views wider than high
- Fixed get_pick to support cq.Assembly

## Release v3.0.0 (24.02.2022)

### New features

- **Performance**

  - By removing the back and forth communication from pythreejs (Python) to Javascript (threejs), the new version is significantly faster in showing multi object assemblies.

- **CadQuery feature support**

  - Supports the latest **CadQuery Sketch class**.

- **New CAD View Controller**

  - Besides the _orbit_ controller (with z-axis being restricted to show up) it now also supports a **trackball controller** with full freedom of moving the CAD objects. The trackball controller uses the holroyd algorithm (see e.g. [here](https://www.mattkeeter.com/projects/rotation/)) to have better control of movements and avoid the usual trackball tumbling.

- **A full re-implementation of Sidecar**

  - Sidecars will be **reused** based on name of the sidecar
  - Supports **different anchors** (_right_, _split-right_, _split-left_, _split-top_, _split-bottom_).
  - Sidecars opening with anchor _right_ will adapt the size to the the size of the CAD view

- **WebGL contexts**

  - In a browser only a limited number of WebGL context can be shown at the same time (e.g. 16 in Chrome on my Mac). Hence, _Jupyter-CadQuery_ now thoroughly tracks WebGL contexts, i.e. **releases WebGL context** when sidecar gets closed.

- **Replay mode**

  - Supports **CadQuery Sketch class**.
  - Replay mode now can **show bounding box** instead of result to compare step with result.

- **New features**

  - _Jupyter-CadQuery_ now allows to show **all three grids** (xy, xz, yz).
  - `show_bbox` additionally shows the bounding box.
  - CAD viewer icons are scalable svg icons.
  - Clipping supports an **intersection mode**.
  - The animation controller is now part of the Javascript component.
  - export_html exports the whole view (with tools) as a HTML page
  - export_png export the CAD view (without tools) as a PNG

- **Fixes**

  - more than I can remember (or am willing to read out of git log) ...

## Release v2.2.1 (07.10.2021)

- **New features**

  - The docker container now supports Viewer mode (added new flags `-v` and `-d`)

- **Fixes**

  - Fix [#47](https://github.com/bernhard-42/jupyter-cadquery/issues/47) Unable to see cadquery.Assembly when top level object of an Assembly is empty
  - Fix [#52](https://github.com/bernhard-42/jupyter-cadquery/issues/52) add `zoom` to ignored attributes for `reset_camera=False`
  - Fix [#53](https://github.com/bernhard-42/jupyter-cadquery/issues/53) Replaced `scipy` with `pyquaternion` for less heavyweight dependencies (and since CadQuery dropped `scipy`)

## Release v2.2.0 (28.06.2021)

- **New features**

  - A new Viewer component based on [`voilà`](https://github.com/voila-dashboards/voila) allows to use _Jupyter-CadQuery_ as viewer for any IDE
  - Dark theme support
  - Tessellation normals can be rendered now for inspection
  - _Jupyter-CadQuery_ now has a logo, which is show as 3D objects when CAD viewer starts in (both sidecar and new Viewer)
  - `set_sidecar` can now immediatly start the viewer (parameter `init`)

- **Changes**

  - `show` has new parameters
    - `ambient_intensity`: set ambient light intensity
    - `direct_intensity`: set direct light intensity
    - `default_edgecolor`: set default edge color
    - `render_normals`: render normals
  - During tessellation, normals are normalized
  - Defaults system now lives in `jupyter_cadquery.defaults` and is more consistent
  - Lean scrollbars are now default (`mac_scrollbar` parameter)
  - Rendering timer restructured with finer granular selection

- **Fixes**
  - Hidden edges are now visible in transparent view
  - Fixed reset camera logic between different calls to `show`
  - Optimized bounding box calculation
  - Double scrollbars removed
  - Fix html export (including OrbitControls fix)

## Release v2.0.0 (06.03.2021)

- **New features**

  - _Jupyter-CadQuery_ supports the latest _CadQuery 2.1_ with _OCP_ (note, it will not run with the _FreeCAD_ version of _CadQuery_).
  - Uses JupyterLab 3.0 which has a new extension deployment system which simplifies the installation of `Jupyter-CadQuery` drastically (see below)
  - It supports the new [CadQuery Assemblies](https://cadquery.readthedocs.io/en/latest/assy.html)
  - Splits UI and shape rendering and shows a progress bar during rendering, especially useful for large assembblies
  - If you install `cadquery-massembly` (see below) then the class `MAssembly` (meaning "Mate base Assembly") is available, which is derived from `cadquery.Assembly` but similar to `cqparts` or FreeCad's `Assembly4` works with mates to manually connect instead of constraints and a numerical solver.
  - Comes with an animation system to simulate models built with `MAssembly`

- **Changes**
  - Deprecates _Jupyter-CadQuery_'s `Assembly` (too many assemblies in the meantime) and has renamed it to `PartGroup` (no semantic change). `Assembly` can still be used with warnings at the moment.
  - Does not test or change the `cqparts` support since the project doesn't seem to be active any more

## Relase v2.1.0 "Performance Release" (07.04.2021)

- **New features**

  - Complete new tessellator class. Significantly faster (for a 15MB STEP file it reduced the rendering time from 3 min to <10 sec)
  - Mesh quality is calculated as in FreeCad (sum of bounding box x-, y-, z-widths divided by 300 times deviation parameter)

- **Changes**
  - Pan speed is adapted to object size sum of bounding box x-, y-, z-widths divided by 300)
  - Replay warnings can be suppressed now (`replay(warning=False)`)
