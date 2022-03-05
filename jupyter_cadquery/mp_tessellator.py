import json

from jupyter_cadquery.tessellator import cache, make_key
import multiprocessing
from multiprocessing import shared_memory
from cachetools import cached
from jupyter_cadquery.mp_tess import mp_tess
from jupyter_cadquery.ocp_utils import serialize

# use 80% of available CPUs
pool = multiprocessing.Pool(int(multiprocessing.cpu_count() * 0.8))


def clear_shared_mem(path):
    try:
        s = shared_memory.SharedMemory(path)
        s.close()
        s.unlink()
    except:  # pylint: disable=bare-except
        ...


def serialize_key(key):
    return json.dumps(key)


def deserialize_key(path):
    key = json.loads(path)
    key[0] = tuple(key[0])
    return tuple(key)


def get_mp_result(apply_result):
    path, result = apply_result.get()

    # update cache to hold full result instead of ApplyResult object
    key = deserialize_key(path)
    cache.__setitem__(key, result)

    clear_shared_mem(path)
    return result


def is_apply_result(obj):
    return isinstance(obj, multiprocessing.pool.ApplyResult)


# This will cache the ApplyResult object after calling mp_tess in an async way.
# Cache will be updated in get_mp_result so that it holds the actual result
@cached(cache, key=make_key)
def mp_tessellate(
    shapes,
    deviation,  # only provided for managing cache
    quality,
    angular_tolerance,
    compute_faces=True,
    compute_edges=True,
    debug=False,
):

    shape = shapes[0]
    path = serialize_key(
        make_key(shape, deviation, quality, angular_tolerance, compute_edges=True, compute_faces=True),
    )
    clear_shared_mem(path)

    s = serialize(shape)
    sm = shared_memory.SharedMemory(path, True, len(s))
    sm.buf[:] = bytearray(s)

    result = pool.apply_async(
        mp_tess, (path, deviation, quality, angular_tolerance, compute_faces, compute_edges, debug)
    )

    return result
