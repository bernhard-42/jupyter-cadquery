# Changelog

## Unreleased

- **`export_html(filename, title=..., viewer=...)` is back** (#122), for sidecars as well as cell viewers - a sidecar is exported as a cell viewer of the same size. The page loads `cad-viewer-widget` from the npm registry at the installed version, which is why the export stopped working: no 4.x had been published there, so the page had nothing to load. Also needed cad-viewer-widget to draw a saved state at all, which its view had not done since 3.2.3.
- **A notebook converted with `nbconvert` after an interactive run shows its viewers** (#109). The renderer decoded the widget's `shapes` in place, so the widget state JupyterLab saved held typed arrays serialised as `{"0": ...}` objects and every mesh in the converted page had zero vertices. The renderer now works on a copy; the state keeps the wire format.

## Release v5.1.0

This release moves Jupyter CadQuery onto `ocp-viewer-core`, the shared half of the viewer stack, and aligns its defaults with the other viewers. Behaviour that differed between viewers for no chosen reason is a support and maintenance cost, so where this host disagreed with OCP CAD Viewer and the standalone viewer, it now follows them.

### Breaking changes

- **`reset_camera` now defaults to `Camera.KEEP`** instead of `"reset"`. A second `show()` of the same object keeps the camera where you left it rather than resetting the view. Pass `reset_camera=Camera.RESET` explicitly for the old behaviour.
- **`ticks` now defaults to 5** instead of 10, so grids are labelled as they are in the other viewers.
- **`modifier_keys` gains `alt`**, matching the four-key map the other viewers ship.

**These defaults only apply to a fresh configuration.** `~/.jcq_config` is written with every setting it knows, so a file created by an earlier version still holds `reset_camera: reset`, `ticks: 10` and a three-key `modifier_keys`, and those stored values continue to win. **To pick up the new defaults, delete `~/.jcq_config`** - it is rewritten from the defaults on next use - **or edit those three entries by hand.**

### Fixes

- `modifier_keys` now applies at all. The widget's traitlet declared its values as pairs where a keymap holds single DOM property names, and no code path set it - so a `modifier_keys` entry in `~/.jcq_config` reached nothing. It is also accepted by `set_viewer_config` now.
- `set_viewer_config(..., viewer="name")` configures the sidecar it names. It configured the default sidecar instead, and set a stray `viewer` attribute on the widget.
- The pin-as-PNG button appears in cell viewers again; `pinning` was dropped before it reached the renderer.
- `theme` and `grid_font_size` are stored settings, so a choice survives the session.

## Release v5.0.0 (07.08.2026)

This release moves Jupyter CadQuery to the new viewer stack: cad-viewer-widget 4 (based on three-cad-viewer 5), ocp_vscode 4 and ocp-tessellate 3.4. It requires JupyterLab >= 4.6.2.

### Changes

- **Studio mode**: a new Studio tab provides physically based rendering with environment maps, shadows, ambient occlusion and tone mapping; per-object PBR materials can be assigned via the `materials`/`modes` parameters (threejs-materials); all `studio_*` options of ocp_vscode are supported in `show`, `show_object` and `set_viewer_config`
- **Zebra analysis**: the Zebra tab and the `zebra_*` options (count, opacity, direction, color scheme, mapping mode) are supported end to end
- New viewer capabilities from three-cad-viewer 5: GPU id-based picking with much better scaling for large models, always-on hover preselection with a status bar, an always available topology filter, and section caps that scale to large assemblies
- `show` and `show_object` signatures are fully aligned with ocp_vscode 4 (including `grid_font_size`, `analysis_tool`, `show_locals`, `update`)
- `analysis_tool="distance" | "properties" | "select"` starts a show with the tool already activated
- `reset_camera` accepts the camera position presets (`Camera.ISO`, `Camera.TOP`, ...) in addition to `RESET`/`KEEP`/`CENTER`
- The viewer is reused across `show` calls (flicker free) and renders directly into the target `tab`
- The clip flags and zebra settings keep their last values across shows on the same viewer; studio settings reset to the ocp_vscode viewer defaults
- `save_screenshot` is supported via the viewer's PNG export
- The tessellated model is passed to the viewer in its raw form and decoded natively by three-cad-viewer

### Fixes

- `show()` without a viewer name now falls back to a cell viewer when the default sidecar has been closed, instead of reopening it
- All HTTP requests from the kernel to the measurement backend use timeouts, so a stuck backend can no longer hang `show()`
- The `Collapse` enum translation was adapted to the changed enum values of ocp_vscode 4
- `replay` was adapted to the changed `_tessellate` return value of ocp_vscode 4

## Release v4.0.2 (17.04.2025)

### Fixes

- Fixed the cad-viewer-widget dependency to 3.0.2 and the installation verification instructions

## Release v4.0.1 (17.04.2025)

### Changes

- Restructured the installation documentation, Dockerfile and binder setup
- Protected the measurement backend endpoints with a per-session API key and exposed the Jupyter port to the kernel

### Fixes

- Injected the `Collapse` enum into cad-viewer-widget so `viewer.collapse` returns the enum

## Release v4.0.0 (14.04.2025)

Jupyter CadQuery 4 is a complete re-architecture: it is now a thin integration layer that reuses [OCP CAD Viewer for VS Code](https://github.com/bernhard-42/vscode-ocp-cad-viewer) (`ocp_vscode`) for the show logic and configuration, [ocp-tessellate](https://github.com/bernhard-42/ocp-tessellate) for tessellation, and [cad-viewer-widget](https://github.com/bernhard-42/cad-viewer-widget) (based on three-cad-viewer) for rendering. `show` therefore behaves the same in JupyterLab and in VS Code.

### Changes

- `show`, `show_object`, `show_all` and the config system (`set_defaults`, `workspace_config`, ...) now mirror the ocp_vscode API, including the `Camera` and `Collapse` enums
- **Measurement tools** (distance, properties) computed by an exact OCCT backend, implemented as a Jupyter server extension
- Auto display of CadQuery and build123d shapes; replay mode ported to ocp-tessellate
- Support for viewer `aspect_ratio`; `show` returns the viewer object
- Build system migrated from setup.py to pyproject.toml with hatchling

### Breaking changes (see the migration section in the README)

- `mate_scale` replaced by `helper_scale`; `control` replaced by `orbit_control`; `reset_camera` and `collapse` take enums instead of booleans/strings; `default_edge_color` renamed to `default_edgecolor`
- `PartGroup`, `Part`, `Faces`, `Edges`, `Vertices` classes removed - use CadQuery or build123d assemblies
- `select_clipping`/`select_tree` replaced by `viewer.tab = "clip" | "tree" | "material"`
- The voila based standalone viewer, HTML export and `webcol_to_cq` were removed; docker support reduced to a Dockerfile

## Release v3.5.2 (03.01.2023)

### Changes
- Default python now is 3.10
- Add support for `Compound`s with mixed shape types
- Aligned `show_object` with `CQ-Editor` (e.g. support `options` dict)
- Improved [build123d](https://github.com/gumyr/build123d) support
- Add support for my private `Alg123d` library (a thin facade on top of `build123d` to remove all implicit behavior and give control back to the user)

### Fixes
- OCCT bug with helix: If height = 2 * pitch, `GCPnts_QuasiUniformDeflection` returns 2 points only. Jupyter CadQuery detects this and uses `GCPnts_QuasiUniformAbscissa` instead


## Release v3.4.0 (18.10.2022)

Support for [build123d](https://github.com/gumyr/build123d) (experimental).

## Release v3.3.0 (18.09.2022)

This version changes the default view angle, hence the change of the minor version number. If you want to keep the old view behaviour of _Jupyter CadQuery_ for existing models, use `up="L"` (L as in legacy) as `show` parameter directly or via `set_defaults`.

### Changes:

- Changed view button orientation behaviour:
  - up="Z" now works like FreeCAD, Onshape, ... with isometric view changed and buttons adapted (e.g. front is now defined differently!)
  - up="Y" works like "Fusion 360" in "y up" mode
  - up="L" works like the old z up mode of Jupyter CadQuery
- Logo and hexapod example adapted to new view behaviour

### Fixes:

- Fixed default parameters of `exportSTL`

## Release v3.2.2 (21.08.2022)

No feature change, change dependency to cad-viewer-widget 1.3.5 which fixes using ipywidgets 7.7.2

## Release v3.2.1 (20.08.2022)

No feature change, just re-released 3.2.0 since a deployment error happened with 3.2.0 to Pypi

## Release v3.2.0 (13.08.2022)

### New features:

- Support of **y-axis as camera up** axis like in Fusion 360
- Support for **alpha channel for colors**.
  **Note:** Transparent objects in WebGL are tricky and sometimes don't render at the right depth of the object.
  Jupyter CadQuery uses the following algorithm:
  - First draw all opaque objects with the correct depth information
  - Then draw all transparent objects.
    Unfortunately, WebGL does not support depth info for transparent objects, see https://stackoverflow.com/a/37651610
    Impact: Transparent objects might be fully or parts drawn at a wrong depth level.
    Nevertheless, I decided to support alpha channel

### Fixes:

- Top level bounding box returned numpy values which broke export to HTML

## Release v3.1.0 (08.07.2022)

### New features:

- **Performance**

  - Change exchange of shapes and tracks from Python to Javascript to binary mode
  - Introduced LRU cache for tessellation results (128MB default)
  - Introduced LRU cache for bounding box calculation
  - Introduced multiprocessing for large assemblies (10s to 100s objects)

- **Step reader**

  - Added import function for STEP files into CadQuery assemblies preserving names and colors (for colors, best effort only, since Jupyter CadQuery does not support colored faces)
  - Added save_assembly/load_assembly to quickly save and load parsed STEP files in a binary BRep

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
