"""
@author: Andrew Smith
Version 6 May 2024
"""

import datetime
import os
import traceback
import sys
import json
import logging
import numpy as np
from pathlib import Path
from platformdirs import user_data_dir, user_config_dir

def _version():
    return 'v0.6.0'

'''
if options['output_dir'] is empty, then output there
else output same file name, but into directory in options
'''
def output_path(path, options):
    if options['output_dir'].strip() == '':
        return path
    return os.path.join(options['output_dir'], os.path.basename(path))

def resource_path(relative_path):
    """
    Get absolute path to a resource.

    - Works for PyInstaller (_MEIPASS)
    - Works for pip-installed package (relative to package)
    """
    try:
        # PyInstaller
        base_path = sys._MEIPASS
        return os.path.join(base_path, relative_path)
    except AttributeError:
        # pip-installed package
        package_dir = Path(__file__).parent
        return str(package_dir / relative_path)

APP_NAME = "MEE2024"
APP_AUTHOR = "MEE2024"

def get_triangle_db_path():
    base = Path(
        user_data_dir(
            appname=APP_NAME,
            appauthor=APP_AUTHOR,  # optional but recommended
        )
    )
    db_dir = base / "TripleTrianglePlatesolveDatabase"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "TripleTriangle_pattern_data.npz"

def get_config_path():
    cfg_dir = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "MEE_config.txt"

'''
open config.txt and read parameters
return parameters from file, or default if file not found or invalid
'''
def read_ini(options):
    # check for config.txt file for working directory
    print('loading config file...')
    try:
        with open(get_config_path(), 'r', encoding="utf-8") as fp:
            loaded = json.load(fp)
            if not '__version__' in loaded or not loaded['__version__'] == _version(): # update ini
                loaded['__version__'] = _version()
                loaded['rough_match_threshhold'] = 36 # reset threshhold (since it was changed from degrees to arcsec)
            options.update(loaded) # if config has missing entries keep default   
    except FileNotFoundError:
        print('note: no config file found - using default parameters')
    except Exception:
        traceback.print_exc()
        print('note: error reading config file - using default parameters')


def write_ini(options):
    try:
        print('saving config file ...')
        with open(get_config_path(), 'w', encoding="utf-8") as fp:
            json.dump(options, fp, sort_keys=True, indent=4)
    except Exception:
        traceback.print_exc()
        print('ERROR: failed to write config file: ' + get_config_path())

'''
convert a iso-format datestring e.g 01/02/2023 to a float (e.g. 2023.08)
'''
def date_string_to_float(x):
    return datetime.datetime.fromisoformat(x).toordinal()/365.24+1

def date_from_float(x):
    return datetime.datetime.fromordinal(int((x - 1) * 365.24)).date().isoformat()

def get_bbox(corners):
    def one_dim(q):
        t = (np.min(q), np.max(q))
        if t[1] - t[0] > 180:
            t = (t[1], t[0])
        return t
    return one_dim(corners[:, 1]), one_dim(corners[:, 0])

def load_config_toml(path):
    """Read a TOML config file and return a flat dict suitable for merging into options.

    Section names are discarded; only leaf key-value pairs are returned.
    This means both flat TOMLs and section-grouped TOMLs load identically.
    Raises on file-not-found, parse error, or any other I/O problem.
    """
    import tomllib
    with open(path, 'rb') as f:
        data = tomllib.load(f)
    flat = {}
    def _flatten(d):
        for k, v in d.items():
            if isinstance(v, dict):
                _flatten(v)
            else:
                flat[k] = v
    _flatten(data)
    return flat


def write_config_toml(options, path):
    """Write the current options dict to a TOML file at path.

    Keys are grouped under comment headers for readability.
    Any existing file at path is silently overwritten.
    """
    import datetime as _dt

    def _val(v):
        if isinstance(v, bool):
            return 'true' if v else 'false'
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            return repr(v)
        escaped = str(v).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f'"{escaped}"'

    sections = [
        ('Tab 1 — image inputs',
         ['workDir', '-DARK-', '-FLAT-', 'output_dir']),
        ('Tab 1 — stacking alignment',
         ['m', 'n', 'k', 'd', 'pxl_tol', 'cutoff', 'img_edge_distance']),
        ('Tab 1 — blob removal',
         ['delete_saturated_blob', 'blob_saturation_level',
          'blob_radius_extra', 'centroid_gap_blob']),
        ('Tab 1 — centroid detection',
         ['centroid_gaussian_subtract', 'sensitive_mode_stack',
          'background_subtraction_mode', 'centroid_gaussian_thresh',
          'min_area', 'sigma_subtract', 'experimental_background_subtract',
          'remove_edgy_centroids', 'sanity_check_centroids']),
        ('Tab 1 — output',
         ['flag_display', 'flag_debug', 'save_dark_flat', 'float_fits']),
        ('Tab 2 — distortion inputs',
         ['workDir2', 'distortion_reference_files', 'distortion_fixed_coefficients']),
        ('Tab 2 — catalog',
         ['catalogue', 'database', 'max_star_mag_dist', 'safety_limit_mag',
          'double_star_cutoff', 'double_star_mag']),
        ('Tab 2 — fit',
         ['distortionOrder', 'distortion_fit_tol', 'rough_match_threshhold',
          'remove_double_tab2', 'crop_circle', 'crop_circle_thresh',
          'basis_type', 'gravity_sweep', 'do_tetra_platesolve']),
        ('Tab 2 — date',
         ['observation_date', 'guess_date', 'DEFAULT_DATE']),
        ('Tab 2 — astrometric corrections',
         ['enable_corrections', 'enable_corrections_ref', 'enable_gravitational_def']),
        ('Tab 2 — observatory',
         ['observation_time', 'observation_lat', 'observation_long',
          'observation_temp', 'observation_pressure', 'observation_humidity',
          'observation_height', 'observation_wavelength']),
        ('Tab 2 — output',
         ['flag_display2']),
        ('Tab 3 — eclipse analysis',
         ['eclipse_method', 'eclipse_limiting_mag',
          'limit_radial_sun_radii', 'limit_radial_sun_radii_value',
          'remove_double_stars_eclipse', 'object_centre_moon']),
        ('Tab 3 — output',
         ['flag_display3']),
    ]

    written = set()
    lines = [
        f'# MEE2024 configuration — {_version()} — '
        f'{_dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC',
        '# Written automatically at run time. Load via "Load Config".',
        '',
    ]
    for section_name, keys in sections:
        lines.append(f'# --- {section_name} ---')
        for key in keys:
            if key in options:
                lines.append(f'{key} = {_val(options[key])}')
                written.add(key)
        lines.append('')

    remaining = [k for k in options if k not in written]
    if remaining:
        lines.append('# --- other ---')
        for key in remaining:
            lines.append(f'{key} = {_val(options[key])}')
        lines.append('')

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


'''
logging setup
'''
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
