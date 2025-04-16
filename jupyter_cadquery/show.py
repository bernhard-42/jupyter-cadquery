#
# Copyright 2025 Bernhard Walter
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

import orjson
from cad_viewer_widget.utils import viewer_args
from cad_viewer_widget import (
    open_viewer as _open_viewer,
)
from .comms import send_measure_request, send_backend
from ocp_vscode.backend_logo import logo as b_logo
from .logo import logo
from ocp_vscode.show import _show, _show_object

__all__ = [
    "open_viewer",
    "show",
    "show_object",
]


def none_filter(d, excludes):
    if excludes is None:
        excludes = []
    return {k: v for k, v in dict(d).items() if v is not None and k not in excludes}


def open_viewer(
    title=None,
    anchor="right",
    cad_width=800,
    tree_width=250,
    height=600,
    aspect_ratio=None,
    theme="browser",
    glass=True,
    tools=True,
    pinning=True,
    default=True,
):
    viewer = _open_viewer(
        title=title,
        anchor=anchor,
        cad_width=cad_width,
        tree_width=tree_width,
        aspect_ratio=aspect_ratio,
        height=height,
        theme=theme,
        glass=glass,
        tools=tools,
        pinning=pinning,
        default=default,
    )
    l = orjson.loads(logo)
    l["config"]["collapse"] = "R"
    viewer.add_shapes(l["data"], **viewer_args(l["config"]), _is_logo=True)

    send_backend({"model": b_logo}, jcv_id=viewer.widget.id)
    viewer.widget.measure_callback = send_measure_request

    return viewer


def show(
    *cad_objs,
    names=None,
    colors=None,
    alphas=None,
    viewer=None,
    anchor=None,
    cad_width=None,
    height=None,
    theme=None,
    pinning=None,
    progress="-+*c",
    glass=None,
    tools=None,
    tree_width=None,
    axes=None,
    axes0=None,
    grid=None,
    ortho=None,
    transparent=None,
    default_opacity=None,
    black_edges=None,
    orbit_control=None,
    tab=None,
    control=None,
    collapse=None,
    explode=None,
    ticks=None,
    center_grid=None,
    up=None,
    zoom=None,
    position=None,
    quaternion=None,
    target=None,
    reset_camera=None,
    clip_slider_0=None,
    clip_slider_1=None,
    clip_slider_2=None,
    clip_normal_0=None,
    clip_normal_1=None,
    clip_normal_2=None,
    clip_intersection=None,
    clip_planes=None,
    clip_object_colors=None,
    pan_speed=None,
    rotate_speed=None,
    zoom_speed=None,
    deviation=None,
    angular_tolerance=None,
    edge_accuracy=None,
    default_color=None,
    default_edgecolor=None,
    default_facecolor=None,
    default_thickedgecolor=None,
    default_vertexcolor=None,
    ambient_intensity=None,
    direct_intensity=None,
    metalness=None,
    roughness=None,
    render_edges=None,
    render_normals=None,
    render_mates=None,
    render_joints=None,
    show_parent=None,
    show_sketch_local=None,
    helper_scale=None,
    mate_scale=None,  # DEPRECATED
    debug=None,
    timeit=None,
    _force_in_debug=False,
):
    # pylint: disable=line-too-long
    """Show CAD objects in Visual Studio Code
    Parameters
        cad_objs:                All cad objects that should be shown as positional parameters

    Valid keywords for the CAD object attributes:
        names:                   List of names for the cad_objs. Needs to have the same length as cad_objs
        colors:                  List of colors for the cad_objs. Needs to have the same length as cad_objs
        alphas:                  List of alpha values for the cad_objs. Needs to have the same length as cad_objs

    Valid keywords for the viewer location:
        viewer                   The name of the viewer. If None or "", then the viewer will be opened in the cell output
        anchor:                  The location where to open the viewer
                                 (sidecar: "right", split windows: "split-right", "split-left", "split-top", "split-bottom")
        cad_width:               The width of the viewer canvas for cell based viewers (viewer is None or "") (default=800)
        height:                  The height of the viewer canvas for cell based viewers (viewer is None or "") (default=600)

    Valid keywords to configure the viewer:
    - UI
        glass:                   Use glass mode where tree is an overlay over the cad object (default=False)
        tools:                   Show tools (default=True)
        tree_width:              Width of the object tree (default=240)
        theme:                   The theme of the viewer ("light" or "dark")
        pinning:                 Whether cell based viewers (viewer is None or "") can be pinned as png

    - Viewer
        axes:                    Show axes (default=False)
        axes0:                   Show axes at (0,0,0) (default=False)
        grid:                    Show grid (default=False)
        ortho:                   Use orthographic projections (default=True)
        transparent:             Show objects transparent (default=False)
        default_opacity:         Opacity value for transparent objects (default=0.5)
        black_edges:             Show edges in black color (default=False)
        orbit_control:           Mouse control use "orbit" control instead of "trackball" control (default=False)
        collapse:                Collapse.LEAVES: collapse all single leaf nodes,
                                 Collapse.ROOT: expand root only,
                                 Collapse.ALL: collapse all nodes,
                                 Collapse.NONE: expand all nodes
                                 (default=Collapse.ROOT)
        ticks:                   Hint for the number of ticks in both directions (default=10)
        center_grid:             Center the grid at the origin or center of mass (default=False)
        up:                      Use z-axis ('Z') or y-axis ('Y') as up direction for the camera (default="Z")
        explode:                 Turn on explode mode (default=False)

        zoom:                    Zoom factor of view (default=1.0)
        position:                Camera position
        quaternion:              Camera orientation as quaternion
        target:                  Camera look at target
        reset_camera:            Camera.RESET: Reset camera position, rotation, zoom and target
                                 Camera.CENTER: Keep camera position, rotation, zoom, but look at center
                                 Camera.KEEP: Keep camera position, rotation, zoom, and target
                                 (default=Camera.RESET)

        clip_slider_0:           Setting of clipping slider 0 (default=None)
        clip_slider_1:           Setting of clipping slider 1 (default=None)
        clip_slider_2:           Setting of clipping slider 2 (default=None)
        clip_normal_0:           Setting of clipping normal 0 (default=None)
        clip_normal_1:           Setting of clipping normal 1 (default=None)
        clip_normal_2:           Setting of clipping normal 2 (default=None)
        clip_intersection:       Use clipping intersection mode (default=False)
        clip_planes:             Show clipping plane helpers (default=False)
        clip_object_colors:      Use object color for clipping caps (default=False)

        pan_speed:               Speed of mouse panning (default=1)
        rotate_speed:            Speed of mouse rotate (default=1)
        zoom_speed:              Speed of mouse zoom (default=1)

    - Renderer
        deviation:               Shapes: Deviation from linear deflection value (default=0.1)
        angular_tolerance:       Shapes: Angular deflection in radians for tessellation (default=0.2)
        edge_accuracy:           Edges: Precision of edge discretization (default: mesh quality / 100)

        default_color:           Default mesh color (default=(232, 176, 36))
        default_edgecolor:       Default color of the edges of a mesh (default=#707070)
        default_facecolor:       Default color of the edges of a mesh (default=#ee82ee)
        default_thickedgecolor:  Default color of the edges of a mesh (default=#ba55d3)
        default_vertexcolor:     Default color of the edges of a mesh (default=#ba55d3)
        ambient_intensity:       Intensity of ambient light (default=1.00)
        direct_intensity:        Intensity of direct light (default=1.10)
        metalness:               Metalness property of the default material (default=0.30)
        roughness:               Roughness property of the default material (default=0.65)

        render_edges:            Render edges  (default=True)
        render_normals:          Render normals (default=False)
        render_mates:            Render mates for MAssemblies (default=False)
        render_joints:           Render build123d joints (default=False)
        show_parent:             Render parent of faces, edges or vertices as wireframe (default=False)
        show_sketch_local:       In build123d show local sketch in addition to relocate sketch (default=True)
        helper_scale:            Scale of rendered helpers (locations, axis, mates for MAssemblies) (default=1)
        progress:                Show progress of tessellation with None is no progress indicator. (default="-+*c")
                                 for object: "-": is reference,
                                             "+": gets tessellated with Python code,
                                             "*": gets tessellated with native code,
                                             "c": from cache

    - Debug
        debug:                   Show debug statements to the VS Code browser console (default=False)
        timeit:                  Show timing information from level 0-3 (default=False)
    """
    kwargs = none_filter(locals(), ["cad_objs"])
    return _show(*cad_objs, **kwargs)


def show_object(
    obj,
    name=None,
    options=None,
    viewer=None,
    anchor=None,
    cad_width=None,
    height=None,
    theme=None,
    pinning=None,
    parent=None,
    clear=False,
    port=None,
    progress="-+*c",
    glass=None,
    tools=None,
    tree_width=None,
    axes=None,
    axes0=None,
    grid=None,
    ortho=None,
    transparent=None,
    default_opacity=None,
    black_edges=None,
    orbit_control=None,
    tab=None,
    collapse=None,
    ticks=None,
    center_grid=None,
    up=None,
    zoom=None,
    position=None,
    quaternion=None,
    target=None,
    reset_camera=None,
    clip_slider_0=None,
    clip_slider_1=None,
    clip_slider_2=None,
    clip_normal_0=None,
    clip_normal_1=None,
    clip_normal_2=None,
    clip_intersection=None,
    clip_planes=None,
    clip_object_colors=None,
    pan_speed=None,
    rotate_speed=None,
    zoom_speed=None,
    deviation=None,
    angular_tolerance=None,
    edge_accuracy=None,
    default_color=None,
    default_facecolor=None,
    default_thickedgecolor=None,
    default_vertexcolor=None,
    default_edgecolor=None,
    ambient_intensity=None,
    metalness=None,
    roughness=None,
    direct_intensity=None,
    render_edges=None,
    render_normals=None,
    render_mates=None,
    render_joints=None,
    show_parent=None,
    show_sketch_local=None,
    helper_scale=None,
    mate_scale=None,  # DEPRECATED
    debug=None,
    timeit=None,
):
    # pylint: disable=line-too-long
    """Incrementally show CAD objects in Visual Studio Code

    Parameters:
        obj:                     The CAD object to be shown

    Valid keywords for the CAD object attributes:
        name:                    The name of the CAD object
        options:                 A dict of color and alpha value: {"alpha":0.5, "color": (64, 164, 223)}
                                 0 <= alpha <= 1.0 and color is a 3-tuple of values between 0 and 255
        clear:                   In interactice mode, clear the stack of objects to be shown (typically used for the first object)
        parent:                  Add another object, usually the parent of e.g. edges or vertices with alpha=0.25

    Valid keywords for the viewer location:
        viewer                   The name of the viewer. If None or "", then the viewer will be opened in the cell output
        anchor:                  The location where to open the viewer
                                 (sidecar: "right", split windows: "split-right", "split-left", "split-top", "split-bottom")
        cad_width:               The width of the viewer canvas for cell based viewers (viewer is None or "") (default=800)
        height:                  The height of the viewer canvas for cell based viewers (viewer is None or "") (default=600)

    Valid keywords to configure the viewer (**kwargs):
    - UI
        glass:                   Use glass mode where tree is an overlay over the cad object (default=False)
        tools:                   Show tools (default=True)
        tree_width:              Width of the object tree (default=240)
        theme:                   The theme of the viewer ("light" or "dark")
        pinning:                 Whether cell based viewers (viewer is None or "") can be pinned as png

    - Viewer
        axes:                    Show axes (default=False)
        axes0:                   Show axes at (0,0,0) (default=False)
        grid:                    Show grid (default=False)
        ortho:                   Use orthographic projections (default=True)
        transparent:             Show objects transparent (default=False)
        default_opacity:         Opacity value for transparent objects (default=0.5)
        black_edges:             Show edges in black color (default=False)
        orbit_control:           Mouse control use "orbit" control instead of "trackball" control (default=False)
        collapse:                Collapse.LEAVES: collapse all single leaf nodes,
                                 Collapse.ROOT: expand root only,
                                 Collapse.ALL: collapse all nodes,
                                 Collapse.NONE: expand all nodes
                                 (default=Collapse.ROOT)
        ticks:                   Hint for the number of ticks in both directions (default=10)
        center_grid:             Center the grid at the origin or center of mass (default=False)
        up:                      Use z-axis ('Z') or y-axis ('Y') as up direction for the camera (default="Z")

        zoom:                    Zoom factor of view (default=1.0)
        position:                Camera position
        quaternion:              Camera orientation as quaternion
        target:                  Camera look at target
        reset_camera:            Camera.RESET: Reset camera position, rotation, zoom and target
                                 Camera.CENTER: Keep camera position, rotation, zoom, but look at center
                                 Camera.KEEP: Keep camera position, rotation, zoom, and target
                                 (default=Camera.RESET)

        clip_slider_0:           Setting of clipping slider 0 (default=None)
        clip_slider_1:           Setting of clipping slider 1 (default=None)
        clip_slider_2:           Setting of clipping slider 2 (default=None)
        clip_normal_0:           Setting of clipping normal 0 (default=[-1,0,0])
        clip_normal_1:           Setting of clipping normal 1 (default=[0,-1,0])
        clip_normal_2:           Setting of clipping normal 2 (default=[0,0,-1])
        clip_intersection:       Use clipping intersection mode (default=[False])
        clip_planes:             Show clipping plane helpers (default=False)
        clip_object_colors:      Use object color for clipping caps (default=False)

        pan_speed:               Speed of mouse panning (default=1)
        rotate_speed:            Speed of mouse rotate (default=1)
        zoom_speed:              Speed of mouse zoom (default=1)

    - Renderer
        deviation:               Shapes: Deviation from linear deflection value (default=0.1)
        angular_tolerance:       Shapes: Angular deflection in radians for tessellation (default=0.2)
        edge_accuracy:           Edges: Precision of edge discretization (default: mesh quality / 100)

        default_color:           Default mesh color (default=(232, 176, 36))
        default_edgecolor:       Default color of the edges of a mesh (default=(128, 128, 128))
        default_facecolor:       Default color of the edges of a mesh (default=#ee82ee / Violet)
        default_thickedgecolor:  Default color of the edges of a mesh (default=#ba55d3 / MediumOrchid)
        default_vertexcolor:     Default color of the edges of a mesh (default=#ba55d3 / MediumOrchid)
        ambient_intensity:       Intensity of ambient light (default=1.00)
        direct_intensity:        Intensity of direct light (default=1.10)
        metalness:               Metalness property of the default material (default=0.30)
        roughness:               Roughness property of the default material (default=0.65)


        render_edges:            Render edges  (default=True)
        render_normals:          Render normals (default=False)
        render_mates:            Render mates for MAssemblies (default=False)
        render_joints:           Render build123d joints (default=False)
        show_parent:             Render parent of faces, edges or vertices as wireframe (default=False)
        show_sketch_local:       In build123d show local sketch in addition to relocate sketch (default=True)
        helper_scale:            Scale of rendered helpers (locations, axis, mates for MAssemblies) (default=1)
        progress:                Show progress of tessellation with None is no progress indicator. (default="-+*c")
                                 for object: "-": is reference,
                                             "+": gets tessellated with Python code,
                                             "*": gets tessellated with native code,
                                             "c": from cache

    - Debug
        debug:                   Show debug statements to the VS Code browser console (default=False)
        imeit:                   Show timing information from level 0-3 (default=False)
    """

    kwargs = none_filter(locals(), ["obj"])
    return _show_object(obj, **kwargs)
