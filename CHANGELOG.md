# Changelog

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
