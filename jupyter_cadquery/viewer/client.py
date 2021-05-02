#
# Copyright 2021 Bernhard Walter
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

from jupyter_cadquery.cadquery.cad_objects import to_assembly
from jupyter_cadquery.defaults import get_defaults
from jupyter_cadquery.cad_objects import _combined_bb
import pickle
import zmq
from .server import ZMQ_PORT


def set_port(port):
    global ZMQ_PORT
    ZMQ_PORT = port


context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.connect(f"tcp://localhost:{ZMQ_PORT}")


def send_pickle(socket, obj, flags=0, protocol=4):
    p = pickle.dumps(obj, protocol)
    return socket.send(p, flags=flags)


class Progress:
    def update(self):
        print(".", end="")


def show(obj, **kwargs):
    """Show CAD objects in Jupyter

    Valid keywords:
    - height:            Height of the CAD view (default=600)
    - tree_width:        Width of navigation tree part of the view (default=250)
    - cad_width:         Width of CAD view part of the view (default=800)
    - bb_factor:         Scale bounding box to ensure compete rendering (default=1.5)
    - default_color:     Default mesh color (default=(232, 176, 36))
    - render_edges:      Render edges  (default=True)
    - render_normals:    Render normals (default=False)
    - render_mates:      Render mates (for MAssemblies)
    - mate_scale:        Scale of rendered mates (for MAssemblies)
    - quality:           Linear deflection for tessellation (default=None)
                         If None, uses bounding box as in (xlen + ylen + zlen) / 300 * deviation)
    - deviation:         Deviation from default for linear deflection value ((default=0.1)
    - angular_tolerance: Angular deflection in radians for tessellation (default=0.2)
    - edge_accuracy:     Presicion of edge discretizaion (default=None)
                         If None, uses: quality / 100
    - optimal_bb:        Use optimal bounding box (default=False)
    - axes:              Show axes (default=False)
    - axes0:             Show axes at (0,0,0) (default=False)
    - grid:              Show grid (default=False)
    - ortho:             Use orthographic projections (default=True)
    - transparent:       Show objects transparent (default=False)
    - ambient_intensity  Intensity of ambient ligth (default=1.0)
    - direct_intensity   Intensity of direct lights (default=0.12)
    - position:          Relative camera position that will be scaled (default=(1, 1, 1))
    - rotation:          z, y and y rotation angles to apply to position vector (default=(0, 0, 0))
    - zoom:              Zoom factor of view (default=2.5)
    - mac_scrollbar:     Prettify scrollbasrs on Macs (default=True)
    - display:           Select display: "sidecar", "cell", "html"
    - tools:             Show the viewer tools like the object tree
    - timeit:            Show rendering times, levels = False, 0,1,2,3,4,5 (default=False)

    For example isometric projection can be achieved in two ways:
    - position = (1, 1, 1)
    - position = (0, 0, 1) and rotation = (45, 35.264389682, 0)
    """

    part_group = to_assembly(obj, render_mates=kwargs.get("render_mates"), mate_scale=kwargs.get("mate_scale", 1))

    config = get_defaults()
    for k, v in kwargs.items():
        if v is not None:
            config[k] = v

    mapping = part_group.to_state()
    shapes = part_group.collect_mapped_shapes(
        mapping,
        quality=config.get("quality"),
        deviation=config.get("deviation"),
        angular_tolerance=config.get("angular_tolerance"),
        edge_accuracy=config.get("edge_accuracy"),
        render_edges=config.get("render_edges"),
        render_normals=config.get("render_normals"),
        timeit=config.get("timeit"),
        progress=Progress(),
    )
    tree = part_group.to_nav_dict()
    data = {
        "data": dict(mapping=mapping, shapes=shapes, tree=tree, bb=_combined_bb(shapes)),
        "type": "data",
        "config": config,
    }
    print(" sending")
    send_pickle(socket, data)
