from astroquery.gaia import Gaia
from astropy.table import Table
import astropy.units as u
#from astropy.coordinates import SkyCoord
import hashlib
import matplotlib.pyplot as plt
import numpy as np
import platformdirs
import time
from pathlib import Path
from mee2024 import StarData
import logging
_log = logging.getLogger(__name__)

def _gaia_cache_path(T1, ra_range, dec_range, max_mag):
    key = f"{T1:.3f}_{ra_range[0]:.5f}_{ra_range[1]:.5f}_{dec_range[0]:.5f}_{dec_range[1]:.5f}_{max_mag:.2f}"
    digest = hashlib.md5(key.encode()).hexdigest()[:12]
    cache_dir = Path(platformdirs.user_cache_dir('MEE2024')) / 'gaia'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"gaia_{digest}.fits"

def _gaia_query(query, retries=5, delay=10):
    """Run an async Gaia TAP query with retries for transient server errors."""
    for attempt in range(1, retries + 1):
        try:
            _log.info("submitting Gaia TAP query (attempt %d/%d)...", attempt, retries)
            job = Gaia.launch_job_async(query)
            results = job.get_results()
            _log.info("Gaia returned %d rows", len(results))
            return results
        except Exception as e:
            if attempt == retries:
                raise
            _log.warning("Gaia query failed (attempt %d/%d): %s — retrying in %ds",
                         attempt, retries, e, delay)
            time.sleep(delay)

'''
coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
width = u.Quantity(0.1, u.deg)
height = u.Quantity(0.1, u.deg)
r = Gaia.query_object_async(coordinate=coord, width=width, height=height)
r.pprint(max_lines=12, max_width=400)
print(r)

dist_lim    = 10.0 * u.lightyear                                # Spherical radius in Light Years
dist_lim_pc = dist_lim.to(u.parsec, equivalencies=u.parallax()) # Spherical radius in Parsec

query = f"SELECT source_id, ra, dec, parallax, distance_gspphot, teff_gspphot, azero_gspphot, phot_g_mean_mag, radial_velocity \
FROM gaiadr3.gaia_source \
WHERE distance_gspphot <= {dist_lim_pc.value}\
AND ruwe <1.4"
'''
'''
job     = Gaia.launch_job_async(query)
results = job.get_results()
print(f'Table size (rows): {len(results)}')

results['distance_lightyear'] = results['distance_gspphot'].to(u.lightyear)
results['radial_velocity_ms'] = results['radial_velocity'].to(u.meter/u.second)
print(results)
'''

def get_prop_pos(T1):
    query = f"SELECT COORD1(ESDC_EPOCH_PROP_POS(ra, dec, parallax, pmra, pmdec, radial_velocity, ref_epoch, {T1})),\
COORD2(ESDC_EPOCH_PROP_POS(ra, dec, parallax, pmra, pmdec, radial_velocity, {T1}, ref_epoch)), pmra, pmdec \
FROM gaiadr3.gaia_source \
WHERE source_id = 5853498713190525696"#  4472832130942575872"
    job     = Gaia.launch_job_async(query)
    results = job.get_results()
    _log.debug("get_prop_pos: %d rows", len(results))
    return results[0][0], results[0][1]

def select_in_box(T1, ra_range, dec_range, max_mag):
    cache_path = _gaia_cache_path(T1, ra_range, dec_range, max_mag)
    if cache_path.exists():
        _log.info("loading Gaia catalog from cache (%s)", cache_path.name)
        return Table.read(str(cache_path))

    _log.info("querying Gaia (mag ≤ %.1f, RA %.2f–%.2f, dec %.2f–%.2f) — may take 1–2 min",
              max_mag, ra_range[0], ra_range[1], dec_range[0], dec_range[1])
    query = f"SELECT source_id, phot_g_mean_mag, COORD1(ESDC_EPOCH_PROP_POS(ra, dec, parallax, pmra, pmdec, radial_velocity, ref_epoch, {T1})),\
COORD2(ESDC_EPOCH_PROP_POS(ra, dec, parallax, pmra, pmdec, radial_velocity, ref_epoch, {T1})), parallax, pmra, pmdec, ref_epoch \
FROM gaiadr3.gaia_source \
WHERE ra BETWEEN {ra_range[0]} AND {ra_range[1]} AND \
dec BETWEEN {dec_range[0]} AND {dec_range[1]} AND \
phot_g_mean_mag BETWEEN 3 AND {max_mag}"
    _log.debug("select_in_box query: %s", query)
    results = _gaia_query(query)
    _log.info("select_in_box: %d stars returned", len(results))
    try:
        results.write(str(cache_path), format='fits', overwrite=True)
        _log.info("cached Gaia results to %s", cache_path.name)
    except Exception as e:
        _log.warning("could not write Gaia cache (%s) — proceeding without cache", e)
    return results

def lookup_nearby(startable, distance, max_mag_neighbours):
    query = f"SELECT source_id, phot_g_mean_mag, ra, dec, ref_epoch \
FROM gaiadr3.gaia_source \
WHERE "

    def helper(ra, dec):
        # ra and dec are in degrees here; np.cos requires radians
        return f'(ra BETWEEN {(ra - distance/3600/np.cos(np.radians(dec))):.5f} AND {(ra + distance / 3600 / np.cos(np.radians(dec))):.5f} AND \
dec BETWEEN  {(dec - distance/3600):.5f} AND {(dec + distance / 3600):.5f})'
        
    
    p = [helper(ra, dec) for (ra, dec) in list(zip(np.degrees(startable.get_ra()), np.degrees(startable.get_dec())))]
    query += '(' + ' OR '.join(p) + ')'
    query += f' AND phot_g_mean_mag BETWEEN 3 AND {max_mag_neighbours}'
    _log.debug("lookup_nearby query: %s", query)
    results = _gaia_query(query)
    _log.debug("lookup_nearby: %d rows", len(results))

    star_table = np.zeros((len(results), 9), dtype=float)

    star_table[:, 0] = np.radians(results['ra'])
    star_table[:, 1] = np.radians(results['dec'])
    star_table[:, 5] = results['phot_g_mean_mag']
    star_table[:, 2] = np.cos(star_table[:, 0]) * np.cos(star_table[:, 1])
    star_table[:, 3] = np.sin(star_table[:, 0]) * np.cos(star_table[:, 1])
    star_table[:, 4] = np.sin(star_table[:, 1])
    star_catID = results['SOURCE_ID']
    return StarData.StarData(results, 2016, False)

class dbs_gaia:

    def __init__(self, gaia_limit=13):
        self.gaia_limit=gaia_limit
    
    def lookup_objects(self, range_ra, range_dec, star_max_magnitude=12, time=2024):
        if star_max_magnitude>self.gaia_limit:
            star_max_magnitude = self.gaia_limit # safety
            _log.info("star_max_magnitude capped at %.1f for safety", self.gaia_limit)
        results = select_in_box(time, range_ra, range_dec, star_max_magnitude) # TODO: dynamic current epoch
        l = len(results)

        star_table = np.zeros((l, 9), dtype=float)
        results['ra'] = results['COORD1'] * u.deg
        results['dec'] = results['COORD2'] * u.deg
        star_table[:, 0] = np.radians(results['COORD1'])
        star_table[:, 1] = np.radians(results['COORD2'])
        star_table[:, 5] = results['phot_g_mean_mag']
        star_table[:, 6] = results['parallax']
        star_table[:, 2] = np.cos(star_table[:, 0]) * np.cos(star_table[:, 1])
        star_table[:, 3] = np.sin(star_table[:, 0]) * np.cos(star_table[:, 1])
        star_table[:, 4] = np.sin(star_table[:, 1])
        star_table[:, 7] = results['pmra']
        star_table[:, 8] = results['pmdec']
        star_catID = results['SOURCE_ID']
        return StarData.StarData(results, time, True)

def select_bright(T1, max_mag):
    query = f"SELECT SOURCE_ID, phot_g_mean_mag, COORD1(ESDC_EPOCH_PROP_POS(ra, dec, parallax, pmra, pmdec, radial_velocity, ref_epoch, {T1})),\
COORD2(ESDC_EPOCH_PROP_POS(ra, dec, parallax, pmra, pmdec, radial_velocity, ref_epoch, {T1})) \
FROM gaiadr3.gaia_source \
WHERE phot_g_mean_mag BETWEEN -2 AND {max_mag}"
    _log.debug("select_bright query: %s", query)
    job     = Gaia.launch_job_async(query)
    results = job.get_results()
    _log.info("select_bright: %d rows", len(results))
    return results
        
if __name__ == '__main__':
    l = select_bright(2024.0, 4)
    #l = select_in_box(2024, (37.4, 37.5), (0.35, 0.45), 16)
    #l = select_in_box(2016, (38.25, 38.35), (0.85, 0.95), 16)
    #l = select_in_box(2016, (38.5, 38.8), (0.65, 0.75), 16)
    #l = select_in_box(2016, (38.6, 38.75), (0.65, 0.75), 16)
    if 0:
        l = select_in_box(2016, (264.0, 264.03), (11.81, 11.84), 18)
        
        l.pprint(show_unit=True, max_width=300, max_lines=30)
        ghjk=ghj
        dbs = dbs_gaia()
        stardata = dbs.lookup_objects((37, 38), (-1, 1))
        lookup_nearby(stardata, 10, 16)
    
    if 0:
        ra, dec = [], []
        for t in [2022.0, 2022.25, 2022.5, 2022.75, 2023, 2023.25, 2023.5]:
            rai, deci = get_prop_pos(t)
            ra.append(rai)
            dec.append(deci)
        plt.scatter(ra, dec)
        plt.show()
        results = select_in_box(2023, (263, 265), (11.5, 13.5), 8.5)
