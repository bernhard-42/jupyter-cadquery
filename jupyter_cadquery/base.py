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

from cad_viewer_widget import _set_default_sidecar, get_default_sidecar, get_sidecar
from cad_viewer_widget import show as viewer_show
from ocp_tessellate.convert import combined_bb, get_normal_len, mp_get_results, tessellate_group
from ocp_tessellate.defaults import (
    add_shape_args,
    apply_defaults,
    create_args,
    get_default,
    get_defaults,
    preset,
    show_args,
    tessellation_args,
)
from ocp_tessellate.mp_tessellator import close_pool, get_mp_result, init_pool, is_apply_result, keymap, mp_tessellate
from ocp_tessellate.tessellator import bbox_edges, compute_quality, discretize_edge, tessellate
from ocp_tessellate.utils import Timer, warn

from jupyter_cadquery.progress import Progress

# UNSELECTED = 0
# SELECTED = 1
# EMPTY = 3


def insert_bbox(bbox, shapes, states):
    # derive the top level states path part
    prefix = list(states)[0].split("/")[1]

    bbox = {
        "id": f"/{prefix}/BoundingBox",
        "type": "edges",
        "name": "BoundingBox",
        "shape": bbox_edges(bbox),
        "color": "#FF00FF",
        "width": 1,
        "bb": bbox,
    }
    # inject bounding box into shapes
    shapes["parts"].insert(0, bbox)
    # and states
    states[f"/{prefix}/BoundingBox"] = [3, 1]


def _show(part_group, **kwargs):
    for k in kwargs:
        if get_default(k, "n/a") == "n/a":
            raise KeyError(f"Paramater {k} is not a valid argument for show()")

    if kwargs.get("cad_width") is not None and kwargs.get("cad_width") < 640:
        warn("cad_width has to be >= 640, setting to 640")
        kwargs["cad_width"] = 640

    if kwargs.get("height") is not None and kwargs.get("height") < 400:
        warn("height has to be >= 400, setting to 400")
        kwargs["height"] = 400

    if kwargs.get("tree_width") is not None and kwargs.get("tree_width") < 250:
        warn("tree_width has to be >= 250, setting to 250")
        kwargs["tree_width"] = 250

    if kwargs.get("quality") is not None:
        warn("quality is ignored. Use deviation to control smoothness of edges")
        del kwargs["quality"]

    sidecar_backup = None

    # if kwargs.get("parallel") is not None:
    #     if kwargs["parallel"] and platform.system() != "Linux":
    #         warn("parallel=True only works on Linux. Setting parallel=False")
    #         kwargs["parallel"] = False

    timeit = preset("timeit", kwargs.get("timeit"))

    with Timer(timeit, "", "overall"):

        if part_group is None:

            import base64  # pylint:disable=import-outside-toplevel
            import pickle  # pylint:disable=import-outside-toplevel

            from jupyter_cadquery.logo import LOGO_DATA  # pylint:disable=import-outside-toplevel

            logo = pickle.loads(base64.b64decode(LOGO_DATA))

            config = add_shape_args(logo["config"])

            defaults = get_defaults()
            config["cad_width"] = defaults["cad_width"]
            config["tree_width"] = defaults["tree_width"]
            config["height"] = defaults["height"]
            config["glass"] = defaults["glass"]
            config["title"] = defaults["viewer"]

            for k, v in create_args(kwargs).items():
                config[k] = v

            shapes = logo["data"]["shapes"]
            states = logo["data"]["states"]

        else:

            config = apply_defaults(**kwargs)

            if config.get("viewer") == "":
                # If viewer is "" (the show default), then the default sidecar should be taken into account
                config["viewer"] = None
                viewer = get_sidecar()
            elif config.get("viewer") is None:
                # if viewer is None (explicitely set), then ignore the default sidecar, i.e. back it up and set to None
                sidecar_backup = get_default_sidecar()
                _set_default_sidecar(None)
                viewer = None
            else:
                viewer = get_sidecar(config["viewer"])

            if viewer is not None:
                # Clear remaining animation tracks. They might not fit to the next assembly
                viewer.clear_tracks()

            if config.get("reset_camera") is False:  #  could be None
                if config.get("zoom") is not None:
                    del config["zoom"]
                if config.get("position") is not None:
                    del config["position"]
                if config.get("quaternion") is not None:
                    del config["quaternion"]

            parallel = preset("parallel", config.get("parallel"))
            with Timer(timeit, "", "tessellate", 1):
                num_shapes = part_group.count_shapes()
                progress_len = 2 * num_shapes if parallel else num_shapes
                progress = None if num_shapes < 2 else Progress(progress_len)

                if parallel:
                    init_pool()
                    keymap.reset()

                shapes, states = tessellate_group(part_group, tessellation_args(config), progress, timeit)

                if parallel:
                    mp_get_results(shapes, progress)
                    close_pool()

                bb = combined_bb(shapes).to_dict()
                # add global bounding box
                shapes["bb"] = bb

                if progress is not None:
                    progress.done()

            # Calculate normal length

            config["normal_len"] = get_normal_len(
                preset("render_normals", config.get("render_normals")),
                shapes,
                preset("deviation", config.get("deviation")),
            )

            show_bbox = preset("show_bbox", kwargs.get("show_bbox"))
            if show_bbox:
                insert_bbox(show_bbox, shapes, states)

        with Timer(timeit, "", "show shapes", 1):
            cv = viewer_show(shapes, states, **show_args(config))

            # If we forced to ignore the default sidecar, restore it
            if sidecar_backup is not None:
                _set_default_sidecar(sidecar_backup)

    return cv
