from mee2024 import database_lookup2
from mee2024 import gaia_search
import numpy as np
from scipy.spatial import KDTree
import time
from mee2024 import platesolve_new
from mee2024.MEE2024util import get_triangle_db_path
from multiprocessing import Process, Queue
from multiprocessing import Manager
import logging
_log = logging.getLogger(__name__)

class _cache:

    database_cache = {}

    catalogue_cache = {}

    q = None

    prepare_process = None

class TriangleData:

    def __init__(self, cata_data):
        self.triangles = cata_data['triangles'] # (n x T x 2 array) - radius ratio and angular seperation for each triangle (note: T = N(N-1)/2)
        self.anchors = cata_data['anchors'] # vector rep of each "anchor" star
        self.pattern_data = cata_data['pattern_data'] # (n x N x 5 array) of (dtheta, phi, star_vector) for each neighbour star
        self.pattern_ind = cata_data['pattern_ind'] # n x N array of integer : the indices of neighbouring stars
        self.kd_tree = KDTree(self.triangles.reshape((-1, 2)), boxsize=[9999999, np.pi*2]) # use a 2-pi periodic condition for polar angle (and basically infinity for ratio)

def work(q):
    _log.debug("loading triangle database")
    try:
        q.put(TriangleData(np.load(get_triangle_db_path())))
        _log.debug("triangle database loaded")
    except Exception:
        _log.info("no triangle database found, generating (this may take a few minutes)")
        platesolve_new.generate()
        q.put(TriangleData(np.load(get_triangle_db_path())))
    _log.debug("triangle database ready")

def prepare_triangles():
    _log.debug("preparing triangle database")
    manager = Manager()
    result_queue = manager.Queue()
    _cache.q=result_queue
    _cache.prepare_process = Process(target=work, args = (_cache.q,))
    _cache.prepare_process.start()
    
def open_database(path):
    raise Exception("Function has been removed")

def open_catalogue(path, debug_folder=None, **kwaargs):
    if not path in _cache.catalogue_cache:
        if path == 'gaia':
            _cache.catalogue_cache[path] = gaia_search.dbs_gaia(**kwaargs)
        elif path == get_triangle_db_path():
            if _cache.q is None:
                # prepare_triangles() was never called (headless/API use) — load synchronously
                _log.info("loading triangle database synchronously")
                _cache.catalogue_cache[path] = TriangleData(np.load(path))
            else:
                i = 1
                while _cache.q.empty() and not path in _cache.catalogue_cache:
                    _log.info("waiting for triangle database (%ds)", i)
                    time.sleep(1)
                    i += 1
                if not path in _cache.catalogue_cache:
                    _cache.catalogue_cache[path] = _cache.q.get()
                    _cache.prepare_process.join()
                    _log.debug("triangle database process joined")
            
        else:
            _cache.catalogue_cache[path] = database_lookup2.database_searcher(path, debug_folder=debug_folder, star_max_magnitude=12)

    return _cache.catalogue_cache[path]


