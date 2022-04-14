"""Code to be distributed by Multiprocessing, hence a separate file"""

from multiprocessing import shared_memory

from jupyter_cadquery.ocp_utils import deserialize
from jupyter_cadquery.tessellator import tessellate


def mp_tess(name, loc, deviation, quality, angular_tolerance, compute_faces, compute_edges, debug):
    """This function will be pickled by multiprocessing"""
    sm = shared_memory.SharedMemory(name)
    shape = deserialize(bytes(sm.buf[0 : sm.size]))
    t = tessellate([shape], loc, deviation, quality, angular_tolerance, compute_faces, compute_edges, debug)
    sm.close()
    sm.unlink()
    return (name, t)
