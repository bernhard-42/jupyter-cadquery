from __future__ import print_function, absolute_import

from functools import reduce
import enum
import math
import operator
import sys
import uuid
import time

import numpy as np

from IPython.display import display

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from pythreejs import BufferAttribute, BufferGeometry, CombinedCamera, GridHelper, PointLight,\
                          AmbientLight, Scene, OrbitControls, Renderer, Mesh, MeshLambertMaterial,\
                          LineSegmentsGeometry, LineMaterial, LineSegments2, MeshStandardMaterial,\
                          Picker, Group

from OCC.Core.Visualization import Tesselator
from OCC.Extend.TopologyUtils import TopologyExplorer, is_edge, discretize_edge
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add

from cadquery import Compound, Vector

from .tree_view import state_diff

HAVE_SMESH = False
SERVER_SIDE = 1
CLIENT_SIDE = 2

def _decomp(a):
    [item] = a.items()
    return item

def explode(edge_list):
    return [[edge_list[i], edge_list[i + 1]] for i in range(len(edge_list) - 1)]

def flatten(nested_list):
    return [y for x in nested_list for y in x]


from functools import reduce
import math


class Grid(object):

    def __init__(self, maximum, ticks=10, colorCenterLine='#aaa', colorGrid='#ddd'):
        axis_start, axis_end, nice_tick = self.nice_bounds(-maximum, maximum, 2*ticks)
        self.step = nice_tick
        self.size = axis_end - axis_start
        self.grid = GridHelper(self.size, int(self.size/self.step),
                               colorCenterLine=colorCenterLine, colorGrid=colorGrid)

    def set_position(self, position):
        self.grid.position = position

    def  set_rotation(self, rotation):
        self.grid.rotation = rotation

    def set_visiblility(self, change):
        self.grid.visible = change

    # https://stackoverflow.com/questions/4947682/intelligently-calculating-chart-tick-positions
    def _nice_number(self, value, round_=False):
        exponent = math.floor(math.log(value, 10))
        fraction = value / 10**exponent

        if round_:
            if fraction < 1.5:  nice_fraction = 1.
            elif fraction < 3.: nice_fraction = 2.
            elif fraction < 7.: nice_fraction = 5.
            else:               nice_fraction = 10.
        else:
            if fraction <= 1:   nice_fraction = 1.
            elif fraction <= 2: nice_fraction = 2.
            elif fraction <= 5: nice_fraction = 5.
            else:               nice_fraction = 10.

        return nice_fraction * 10**exponent

    def nice_bounds(self, axis_start, axis_end, num_ticks=10):
        axis_width = axis_end - axis_start
        if axis_width == 0:
            nice_tick = 0
        else:
            nice_range = self._nice_number(axis_width)
            nice_tick = self._nice_number(nice_range / (num_ticks - 1), round_=True)
            axis_start = math.floor(axis_start / nice_tick) * nice_tick
            axis_end = math.ceil(axis_end / nice_tick) * nice_tick

        return axis_start, axis_end, nice_tick


class Axes(object):

    def __init__(self, origin=None, length=1, width=3):
        if origin is None:
            origin = (0, 0, 0)
        x = LineSegmentsGeometry(positions=[[origin, self._shift(origin, [length, 0, 0])]])
        y = LineSegmentsGeometry(positions=[[origin, self._shift(origin, [0, length, 0])]])
        z = LineSegmentsGeometry(positions=[[origin, self._shift(origin, [0, 0, length])]])

        mx = LineMaterial(linewidth=width, color='red')
        my = LineMaterial(linewidth=width, color='green')
        mz = LineMaterial(linewidth=width, color='blue')

        self.axes = [LineSegments2(x, mx), LineSegments2(y, my), LineSegments2(z, mz)]

    def _shift(self, v, offset):
        return [x + o for x, o in zip(v, offset)]

    def toggleAxes(self, change):
        for i in range(3):
            self.axes[i].visible = change


class BndBox(object):

    def __init__(self, shapes, tol=1e-5):
        self.tol = tol
        _bbox = reduce(self._opt, [self.bbox(shape) for shape in shapes])
        self.xmin = _bbox[0]
        self.xmax = _bbox[1]
        self.ymin = _bbox[2]
        self.ymax = _bbox[3]
        self.zmin = _bbox[4]
        self.zmax = _bbox[5]
        self.xsize = self.xmax - self.xmin
        self.ysize = self.ymax - self.ymin
        self.zsize = self.zmax - self.zmin
        self.center = (self.xmin + self.xsize / 2.0,
                       self.ymin + self.ysize / 2.0,
                       self.zmin + self.zsize / 2.0)
        self.max = reduce(lambda a,b: max(abs(a), abs(b)), _bbox)

    def _opt(self, b1, b2):
        return (min(b1[0], b2[0]), max(b1[1], b2[1]),
                min(b1[2], b2[2]), max(b1[3], b2[3]),
                min(b1[4], b2[4]), max(b1[5], b2[5]))

    def _bounding_box(self, obj, tol=1e-5):
        bbox = Bnd_Box()
        bbox.SetGap(self.tol)
        brepbndlib_Add(obj, bbox, True)
        values = bbox.Get()
        return (values[0], values[3], values[1], values[4], values[2], values[5])

    def bbox(self, shape):
        bb = reduce(self._opt, [self._bounding_box(obj.wrapped) for obj in shape.objects])
        return bb

    def __repr__(self):
        return "[x(%f .. %f), y(%f .. %f), z(%f .. %f)]" % (self.xmin, self.xmax,
                                                            self.ymin, self.ymax,
                                                            self.zmin, self.zmax)


class CadqueryView(object):

    def __init__(self, width=600, height=400, render_edges=True, debug=None):
        self.width = width
        self.height = height
        self.render_edges = render_edges
        self._debug = debug

        self._compute_normals_mode = SERVER_SIDE
        self.features = ["mesh", "edges"]

        self.default_shape_color = self._format_color(166, 166, 166)
        self.pick_color = self._format_color(232, 176, 36)
        self.default_mesh_color = 'white'
        self.default_edge_color = self._format_color(0, 0, 0)
        self.default_selection_material = self._material('orange')

        self.shapes = []
        self.pickable_objects = Group()
        self.pick_last_mesh = None
        self.pick_last_mesh_color = None
        self.mash_edges_mapping = []

        self.camera = None
        self.axes = None
        self.grid = None
        self.scene = None
        self.controller = None
        self.renderer = None

        self.savestate = None

    def _format_color(self, r, g, b):
        return '#%02x%02x%02x' % (r, g, b)

    def _material(self, color, transparent=False, opacity=1.0):
        return MeshStandardMaterial(color=color, transparent=transparent, opacity=opacity)

    def _render_shape(self,
        shape_index, # index in self.shapes
        shape=None,  # the TopoDS_Shape to be displayed
        edges=None,  # or the edges to be displayed 
        shape_color=None,
        render_edges=False,
        edge_color=None,
        edge_width=1,
        deflection=0.05,
        compute_uv_coords=False,
        quality=1.0,
        transparent=True,
        opacity=0.6):

        edge_list = None
        edge_lines = None

        if shape is not None:
            if shape_color is None:
                shape_color = self.default_shape_color
            if edge_color is None:
                edge_color = self.default_edge_color

            # first, compute the tesselation
            tess = Tesselator(shape)
            tess.Compute(uv_coords=compute_uv_coords, compute_edges=render_edges,
                         mesh_quality=quality, parallel=True)

            # get vertices and normals
            vertices_position = tess.GetVerticesPositionAsTuple()

            number_of_triangles = tess.ObjGetTriangleCount()
            number_of_vertices = len(vertices_position)

            # number of vertices should be a multiple of 3
            if number_of_vertices % 3 != 0:
                raise AssertionError("Wrong number of vertices")
            if number_of_triangles * 9 != number_of_vertices:
                raise AssertionError("Wrong number of triangles")

            # then we build the vertex and faces collections as numpy ndarrays
            np_vertices = np.array(vertices_position, dtype='float32')\
                            .reshape(int(number_of_vertices / 3), 3)
            # Note: np_faces is just [0, 1, 2, 3, 4, 5, ...], thus arange is used
            np_faces = np.arange(np_vertices.shape[0], dtype='uint32')

            # set geometry properties
            buffer_geometry_properties = {
                'position': BufferAttribute(np_vertices),
                'index': BufferAttribute(np_faces)
            }
            if self._compute_normals_mode == SERVER_SIDE:
                # get the normal list, converts to a numpy ndarray. This should not raise
                # any issue, since normals have been computed by the server, and are available
                # as a list of floats
                np_normals = np.array(tess.GetNormalsAsTuple(), dtype='float32').reshape(-1, 3)
                # quick check
                if np_normals.shape != np_vertices.shape:
                    raise AssertionError("Wrong number of normals/shapes")
                buffer_geometry_properties['normal'] = BufferAttribute(np_normals)

            # build a BufferGeometry instance
            shape_geometry = BufferGeometry(attributes=buffer_geometry_properties)

            # if the client has to render normals, add the related js instructions
            if self._compute_normals_mode == CLIENT_SIDE:
                shape_geometry.exec_three_obj_method('computeVertexNormals')

            # then a default material
            shp_material = self._material(shape_color, transparent, opacity)

            # finally create the mash
            shape_mesh = Mesh(geometry=shape_geometry, material=shp_material, name="mesh_%d" % shape_index)

            # edge rendering, if set to True

            if render_edges:
                edge_list = list(
                    map(lambda i_edge: [tess.GetEdgeVertex(i_edge, i_vert)
                                        for i_vert in range(tess.ObjEdgeGetVertexCount(i_edge))],
                        range(tess.ObjGetEdgeCount())))

        if edges is not None:
            shape_mesh = None
            edge_list = [discretize_edge(edge, deflection) for edge in edges]

        if edge_list is not None:
            edge_list = flatten(list(map(explode, edge_list)))
            lines = LineSegmentsGeometry(positions=edge_list)
            mat = LineMaterial(linewidth=edge_width, color=edge_color)
            edge_lines = LineSegments2(lines, mat, name="edges_%d" % shape_index)

        if shape_mesh is not None or edge_lines is not None:
            index_mapping = {"mesh": None, "edges": None, "shape": shape_index}
            if shape_mesh is not None:
                ind = len(self.pickable_objects.children)
                self.pickable_objects.add(shape_mesh)
                index_mapping["mesh"] = ind
            if edge_lines is not None:
                ind = len(self.pickable_objects.children)
                self.pickable_objects.add(edge_lines)
                index_mapping["edges"] = ind
            self.mash_edges_mapping.append(index_mapping)

    def _scale(self, vec):
        r = self.bb.max * 2.5
        n = np.linalg.norm(vec)
        new_vec = (vec / n * r) + self.bb.center
        return new_vec.tolist()

    def _update(self):
        self.controller.exec_three_obj_method('update')
        pass

    def _reset(self):
        self.camera.rotation, self.controller.target = self.savestate
        self.camera.position = self._scale((1,1,1))
        self.camera.zoom = 1.0
        self._update()

    # UI Handler

    def change_view(self, typ, directions):
        def reset(b):
            self._reset()

        def refit(b):
            self.camera.zoom = 1.0
            self._update()

        def change(b):
            self.camera.position = self._scale(directions[typ])
            self._update()

        if typ == "fit":
            return refit
        elif typ == "reset":
            return reset
        else:
            return change

    def set_axes(self, change):
        self.axes.toggleAxes(change)

    def toggle_axes(self, change):
        self.set_axes(change["new"])

    def set_center(self, change):
        center = (0, 0, 0) if change else self.bb.center
        self.grid.set_position(center)
        for i in range(3):
            self.scene.children[i].position = center

    def toggle_center(self, change):
        self.set_center(change["new"])

    def set_grid(self, change):
        self.grid.set_visiblility(change)

    def toggle_grid(self, change):
        self.set_grid(change["new"])

    def set_ortho(self, change):
        self.camera.mode = 'orthographic' if change else 'perspective'

    def toggle_ortho(self, change):
        self.set_ortho(change["new"])

    def set_visibility(self, ind, i, state):
        feature = self.features[i]
        group_index = self.mash_edges_mapping[ind][feature]
        if  group_index is not None:
            self.pickable_objects.children[group_index].visible = (state == 1)

    def change_visibility(self, mapping):
        def f(states):
            diffs = state_diff(states.get("old"), states.get("new"))
            for diff in diffs:
                obj, val = _decomp(diff)
                self.set_visibility(mapping[obj], val["icon"], val["new"])
        return f

    def pick(self, value):
        if self.pick_last_mesh != value.owner.object:
            # Reset
            if value.owner.object is None or self.pick_last_mesh is not None:
                self.pick_last_mesh.material.color = self.pick_last_mesh_color
                self.pick_last_mesh = None
                self.pick_last_mesh_color = None
            # Change mesh
            if isinstance(value.owner.object, Mesh):
                _, ind = value.owner.object.name.split("_")
                shape = self.shapes[int(ind)]
                bbox = BndBox([shape["shape"]])
                self._debug("\n%s:" % shape["name"])
                self._debug(" x~[%5.2f,%5.2f] ~ %5.2f" % (bbox.xmin, bbox.xmax, bbox.xsize))
                self._debug(" y~[%5.2f,%5.2f] ~ %5.2f" % (bbox.ymin, bbox.ymax, bbox.ysize))
                self._debug(" z~[%5.2f,%5.2f] ~ %5.2f" % (bbox.zmin, bbox.zmax, bbox.zsize))
                self.pick_last_mesh = value.owner.object
                self.pick_last_mesh_color = self.pick_last_mesh.material.color
                self.pick_last_mesh.material.color = self.pick_color

    # public methods to add shapes and render the view

    def add_shape(self, name, shape, color="#ff0000"):
        self.shapes.append({"name": name, "shape": shape, "color": color})

    def render(self):
        for i, shape in enumerate(self.shapes):
            if is_edge(shape["shape"].toOCC()):
                # TODO Check it is safe to omit these edges
                # The edges with on1 vertex are CurveOnSurface
                # curve_adaptator = BRepAdaptor_Curve(edge)
                # curve_adaptator.IsCurveOnSurface() == True
                edges = [edge.wrapped
                         for edge in shape["shape"].objects
                         if TopologyExplorer(edge.wrapped).number_of_vertices() >= 2 ]
                self._render_shape(i, edges=edges,
                                   render_edges=True, edge_color=shape["color"], edge_width=3)
            else:
                self._render_shape(i, shape=shape["shape"].toOCC(),
                                   render_edges=True, shape_color=shape["color"])

        self.bb = BndBox([shape["shape"] for shape in self.shapes])
        bb_max = max((abs(self.bb.xmin), abs(self.bb.xmax),
                      abs(self.bb.ymin), abs(self.bb.ymax),
                      abs(self.bb.zmin), abs(self.bb.zmax)))
        camera_target = self.bb.center
        camera_position = self._scale([1, 1, 1])

        self.camera = CombinedCamera(position=camera_position,
                                     width=self.width, height=self.height)
        self.camera.up = (0.0, 0.0, 1.0)
        self.camera.lookAt(camera_target)
        self.camera.mode = 'orthographic'

        self.axes = Axes(length=bb_max)
        self.axes.toggleAxes(True)

        self.grid = Grid(bb_max, colorCenterLine='#aaa', colorGrid='#ddd')
        self.grid.set_position(camera_target)

        key_light = PointLight(position=[-100, 100, 100])
        ambient_light = AmbientLight(intensity=0.4)

        non_pickable_objects = self.axes.axes + [self.grid.grid, key_light, ambient_light, self.camera]

        self.scene = Scene(children=non_pickable_objects + [self.pickable_objects])

        self.controller = OrbitControls(controlling=self.camera, target=camera_target)

        self.picker = Picker(controlling=self.pickable_objects, event='mouseup')
        self.picker.observe(self.pick)

        self.renderer = Renderer(scene=self.scene, camera=self.camera,
                                 controls=[self.controller, self.picker],
                                 width=self.width, height=self.height)

        self.camera.position = self._scale(self.camera.position)

        # needs to be done after setup of camera
        self.grid.set_rotation((math.pi / 2.0, 0, 0, "XYZ"))
        self.grid.set_position((0, 0, 0))

        self.savestate = (self.camera.rotation, self.controller.target)

        # Workaround: Zoom forth and back to update frame. Sometimes necessary :(
        self.camera.zoom = 1.01
        self._update()
        self.camera.zoom = 1.0
        self._update()

        return self.renderer
