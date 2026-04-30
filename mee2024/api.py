"""
MEE2024 headless API — three functions mirroring the three GUI tabs.

Usage:
    from mee2024.api import find_stars, compute_distortion, fit_data

    find_stars('configs/find-stars-calibration.toml')
    compute_distortion('configs/compute-distortion-zenith.toml')
    fit_data('configs/fit-data.toml')

Each function loads a TOML config, merges it with the same defaults the GUI
uses, forces headless display flags (no interactive plots), and calls the
underlying processing module directly.  Progress is reported via tqdm on
stderr; detailed diagnostics go to the stacker's per-run LOG file.
"""

import glob
import logging
from pathlib import Path

from mee2024 import stacker_implementation, distortion_fitter, eclipse_analysis
from mee2024.MEE2024util import load_config_toml

# Silence astroquery's per-query INFO chatter.
logging.getLogger('astroquery').setLevel(logging.WARNING)

_log = logging.getLogger(__name__)

# Configure mee2024 logging to show INFO+ on stderr if the caller hasn't
# already set up a handler.  Callers who want to control logging themselves
# can configure the root logger or 'mee2024' logger before importing api.
_mee2024_log = logging.getLogger('mee2024')
if not _mee2024_log.handlers and not logging.root.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter('%(message)s'))
    _mee2024_log.addHandler(_h)
    _mee2024_log.setLevel(logging.INFO)

_IMAGE_EXTENSIONS = (
    '*.fit', '*.fts', '*.fits',
    '*.FIT', '*.FTS', '*.FITS',
    '*.tif', '*.tiff', '*.png', '*.jpg', '*.jpeg',
)

# Mirrors the defaults dict in main.py.  Kept here so api.py has no dependency
# on main.py (which imports FreeSimpleGUI at the top level).
_DEFAULTS = {
    'flag_display':  False,
    'flag_display2': False,
    'flag_display3': False,
    'flag_debug': False,
    'save_dark_flat': False,
    'sensitive_mode_stack': True,
    'workDir': '',
    'workDir2': '',
    '-DARK-': '',
    '-FLAT-': '',
    'output_dir': '',
    'database': '',
    'catalogue': 'gaia',
    'k': 12,
    'm': 30,
    'n': 30,
    'd': 100,
    'img_edge_distance': 5,
    'pxl_tol': 10,
    'cutoff': 100,
    'delete_saturated_blob': True,
    'blob_saturation_level': 100,
    'blob_radius_extra': 100,
    'centroid_gap_blob': 30,
    'centroid_gaussian_subtract': False,
    'centroid_gaussian_thresh': 5,
    'min_area': 4,
    'experimental_background_subtract': False,
    'sanity_check_centroids': True,
    'float_fits': False,
    'max_star_mag_dist': 12,
    'observation_date': '2023-12-01',
    'distortion_fit_tol': 1,
    'remove_edgy_centroids': True,
    'sigma_subtract': 3,
    'distortionOrder': 'cubic',
    'guess_date': False,
    'DEFAULT_DATE': '2020-01-01',
    'double_star_cutoff': 10,
    'double_star_mag': 17,
    'rough_match_threshhold': 36,
    'enable_corrections': False,
    'observation_time': '',
    'observation_lat': '',
    'observation_long': '',
    'enable_corrections_ref': False,
    'enable_gravitational_def': False,
    'observation_temp': 10,
    'observation_pressure': 1010,
    'observation_humidity': 0,
    'observation_height': 0,
    'observation_wavelength': 0.65,
    'do_tetra_platesolve': False,
    'basis_type': 'polynomial',
    'distortion_reference_files': '',
    'distortion_fixed_coefficients': 'None',
    'background_subtraction_mode': 'annular',
    'eclipse_limiting_mag': 11,
    'remove_double_stars_eclipse': False,
    'safety_limit_mag': 13,
    'object_centre_moon': False,
    'gravity_sweep': False,
    'limit_radial_sun_radii': False,
    'limit_radial_sun_radii_value': 9,
    'crop_circle': False,
    'crop_circle_thresh': 1.0,
    'remove_double_tab2': False,
    'eclipse_method': 'Method 1 & 2',
}


def _load(config_path):
    """Load TOML config, merge with defaults, force headless display flags."""
    flat = load_config_toml(config_path)
    options = dict(_DEFAULTS)
    options.update(flat)
    # API is always headless — ignore any flag_display* values in the TOML.
    options['flag_display']  = False
    options['flag_display2'] = False
    options['flag_display3'] = False
    return options


def _stable_link(out_dir, glob_pat, stable_name):
    """Point stable_name → the most recently modified file matching glob_pat."""
    out_dir = Path(out_dir)
    matches = sorted(out_dir.glob(glob_pat), key=lambda p: p.stat().st_mtime)
    if not matches:
        _log.warning("no file matching %s found in %s", glob_pat, out_dir)
        return
    stable = out_dir / stable_name
    if stable.exists() or stable.is_symlink():
        stable.unlink()
    stable.symlink_to(matches[-1].name)
    _log.info("stable output: %s → %s", stable.name, matches[-1].name)


def _resolve_files(folder, file_list, *, label):
    """Return a sorted list of image paths from a folder glob or an explicit list."""
    if folder:
        files = sorted(
            f for pat in _IMAGE_EXTENSIONS
            for f in glob.glob(str(Path(folder) / pat))
        )
        if not files:
            _log.warning("%s: no image files found in %s", label, folder)
        return files
    return [f for f in (file_list or []) if f]


def find_stars(config_path):
    """Run Tab 1 (stacker) from a TOML config file."""
    options = _load(config_path)
    files = _resolve_files(options.get('input_folder', ''), options.get('input_files', []), label='input')
    darks = _resolve_files(options.get('dark_folder',  ''), options.get('dark_files',  []), label='dark')
    flats = _resolve_files(options.get('flat_folder',  ''), options.get('flat_files',  []), label='flat')
    _log.info("find_stars: %d images  %d darks  %d flats  output=%s",
              len(files), len(darks), len(flats), options.get('output_dir', ''))
    stacker_implementation.do_stack(files, darks, flats, options)
    run_name = options.get('run_name', '')
    if run_name and options.get('output_dir'):
        _stable_link(options['output_dir'], 'centroid_data*.zip', f'{run_name}_centroids.zip')


def compute_distortion(config_path):
    """Run Tab 2 (distortion fitter) from a TOML config file."""
    options = _load(config_path)
    input_file = options['input_file']
    _log.info("compute_distortion: %s  output=%s", input_file, options.get('output_dir', ''))
    distortion_fitter.match_and_fit_distortion(input_file, options, None)
    run_name = options.get('run_name', '')
    if run_name and options.get('output_dir'):
        _stable_link(options['output_dir'], 'distortion_data*.zip', f'{run_name}_distortion.zip')


def fit_data(config_path):
    """Run Tab 3 (eclipse analysis) from a TOML config file."""
    options = _load(config_path)
    input_file = options['input_file']
    _log.info("fit_data: %s  output=%s", input_file, options.get('output_dir', ''))
    eclipse_analysis.eclipse_analysis(input_file, options)
