"""Visualization tools for MEE2024 eclipse astrometry results.

Two-layer API:

  Low level — add one run's data to existing axes:
    plot_deflection_curve(ax, data_dir, ...)
    plot_n_of_r(ax, data_dir, ...)
    plot_delta_of_r(ax, data_dir, ...)
    plot_quiver(ax, data_dir, ...)

  High level — make all four plots for one run:
    plot_all(data_dir, output_dir=None) -> Figure

  Grid summary:
    plot_grid_heatmap(results_csv, column, ...) -> Figure

Each low-level function returns the axes object so calls can be chained.
All functions accept **kwargs passed through to the underlying matplotlib call.
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# GR deflection constant: deflection at 1 solar radius in arcseconds
_GR_ARCSEC = 1.7512


def _radial_bins(df, bin_width=0.5):
    """Bin edges at fixed bin_width (solar radii) covering the data range."""
    r_min = np.floor(df['rad_dist_solar_radii'].min() / bin_width) * bin_width
    r_max = np.ceil( df['rad_dist_solar_radii'].max() / bin_width) * bin_width
    return np.arange(r_min, r_max + bin_width, bin_width)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_deflections(data_dir) -> pd.DataFrame:
    """Load ECLIPSE_DEFLECTIONS_DATA from a run directory.

    Returns a DataFrame with the original columns plus:
      dRA_arcsec   — (RA_obs  − RA_catalog) · cos(DEC_catalog), in arcsec
      dDEC_arcsec  — (DEC_obs − DEC_catalog) in arcsec
      predicted_arcsec — L × 1.7512 / rad_dist_solar_radii
      residual_arcsec  — deflection_arcsec − predicted_arcsec
    where L is read from the ECLIPSE_OUTPUT file in the same directory.
    """
    data_dir = Path(data_dir)
    csvs = sorted(data_dir.glob('ECLIPSE_DEFLECTIONS_DATA*.csv'), key=lambda p: p.name)
    if not csvs:
        raise FileNotFoundError(f"No ECLIPSE_DEFLECTIONS_DATA*.csv in {data_dir}")
    df = pd.read_csv(csvs[-1])

    # Vector residuals in arcseconds
    cos_dec = np.cos(np.radians(df['DEC_catalog']))
    df['dRA_arcsec']  = (df['RA_obs']  - df['RA_catalog'])  * cos_dec * 3600
    df['dDEC_arcsec'] = (df['DEC_obs'] - df['DEC_catalog']) * 3600

    # GR prediction using fitted L
    L = _read_L(data_dir)
    df['predicted_arcsec'] = L * _GR_ARCSEC / df['rad_dist_solar_radii']
    df['residual_arcsec']  = df['deflection_arcsec'] - df['predicted_arcsec']

    df.attrs['L'] = L
    df.attrs['data_dir'] = str(data_dir)
    return df


def _read_L(data_dir: Path) -> float:
    """Extract Method 1 L value from ECLIPSE_OUTPUT*.txt."""
    txts = sorted(data_dir.glob('ECLIPSE_OUTPUT*.txt'), key=lambda p: p.name)
    if not txts:
        return float('nan')
    text = txts[-1].read_text()
    m = re.search(r'Method 1 results: L=([\d.]+)', text)
    return float(m.group(1)) if m else float('nan')


# ---------------------------------------------------------------------------
# Low-level plot functions
# ---------------------------------------------------------------------------

def plot_deflection_curve(ax, data_dir, *, label=None, show_gr=True,
                          gr_color='black', **scatter_kw):
    """Scatter plot of measured deflection vs. radial distance.

    Overlays the fitted GR curve L × 1.7512 / r if show_gr=True.
    """
    df = load_deflections(data_dir)
    L  = df.attrs['L']

    scatter_kw.setdefault('s', 20)
    scatter_kw.setdefault('alpha', 0.7)
    sc = ax.scatter(df['rad_dist_solar_radii'], df['deflection_arcsec'],
                    label=label, **scatter_kw)

    if show_gr:
        r = np.linspace(df['rad_dist_solar_radii'].min() * 0.9,
                        df['rad_dist_solar_radii'].max() * 1.05, 200)
        ax.plot(r, L * _GR_ARCSEC / r, color=gr_color, lw=1.2,
                label=f'GR fit (L={L:.3f})' if label is None else None)

    ax.set_xlabel('Radial distance (solar radii)')
    ax.set_ylabel('Deflection (arcsec)')
    ax.axhline(0, color='gray', lw=0.5, ls='--')
    return ax


def plot_n_of_r(ax, data_dir, *, label=None, bin_width=0.5, bins=None, **bar_kw):
    """Histogram of star counts vs. radial distance from the Sun.

    Default bin width is 0.5 solar radii. Pass bins= to override with an
    explicit count or edge array.
    """
    df = load_deflections(data_dir)
    if bins is None:
        bins = _radial_bins(df, bin_width)

    bar_kw.setdefault('alpha', 0.7)
    ax.hist(df['rad_dist_solar_radii'], bins=bins, label=label, **bar_kw)
    ax.set_xlabel('Radial distance (solar radii)')
    ax.set_ylabel('Number of stars')
    return ax


def plot_delta_of_r(ax, data_dir, *, label=None, **scatter_kw):
    """Scatter plot of residuals (observed − GR fit) vs. radial distance."""
    df = load_deflections(data_dir)

    scatter_kw.setdefault('s', 20)
    scatter_kw.setdefault('alpha', 0.7)
    ax.scatter(df['rad_dist_solar_radii'], df['residual_arcsec'],
               label=label, **scatter_kw)
    ax.axhline(0, color='gray', lw=0.8, ls='--')
    ax.set_xlabel('Radial distance (solar radii)')
    ax.set_ylabel('Residual (arcsec)')
    return ax


def plot_mean_deflection(ax, data_dir, *, label=None, bin_width=0.5,
                         show_gr=True, gr_color='black', **errorbar_kw):
    """Binned mean deflection ⟨D(r)⟩ with standard-error bars.

    Each point is the mean of deflection_arcsec for all stars in a 0.5-solar-
    radii bin; error bars are the standard error of the mean. The fitted GR
    curve L × 1.7512 / r is overlaid for comparison.

    The bin edges match plot_n_of_r so the two plots are directly comparable.
    """
    df = load_deflections(data_dir)
    L  = df.attrs['L']

    edges   = _radial_bins(df, bin_width)
    centers = 0.5 * (edges[:-1] + edges[1:])

    means, errs, valid = [], [], []
    for lo, hi, ctr in zip(edges[:-1], edges[1:], centers):
        vals = df.loc[(df['rad_dist_solar_radii'] >= lo) &
                      (df['rad_dist_solar_radii'] <  hi), 'deflection_arcsec']
        if len(vals) >= 1:
            means.append(vals.mean())
            errs.append(vals.sem() if len(vals) > 1 else np.nan)
            valid.append(ctr)

    errorbar_kw.setdefault('fmt', 'o')
    errorbar_kw.setdefault('capsize', 3)
    ax.errorbar(valid, means, yerr=errs, label=label, **errorbar_kw)

    if show_gr:
        r = np.linspace(edges[0], edges[-1], 300)
        ax.plot(r, L * _GR_ARCSEC / r, color=gr_color, lw=1.2,
                label=f'GR fit (L={L:.3f})' if label is None else None)

    ax.axhline(0, color='gray', lw=0.5, ls='--')
    ax.set_xlabel('Radial distance (solar radii)')
    ax.set_ylabel('Mean deflection ⟨D(r)⟩ (arcsec)')
    return ax


def plot_quiver(ax, data_dir, *, label=None, amplify=None,
               ref_arcsec=0.5, ref_frac=0.05, **quiver_kw):
    """Quiver plot of position residuals on the sky.

    Arrow direction and length show the (dRA, dDEC) displacement of each
    star's observed position relative to its catalog position.

    Strategy: pre-amplify the arrows so that `ref_arcsec` arcseconds spans
    `ref_frac` of the field width, then draw with scale=1 in data (degree)
    units. A quiverkey reference arrow is added automatically.

    Parameters
    ----------
    amplify   : explicit amplification factor (arcsec → degrees multiplier).
                Default: computed so ref_arcsec spans ref_frac of field width.
    ref_arcsec: arcseconds shown on the quiverkey reference arrow (default 0.5)
    ref_frac  : fraction of field width the reference arrow should span (default 0.05)
    """
    df = load_deflections(data_dir)

    field_width = df['RA_catalog'].max() - df['RA_catalog'].min()  # degrees
    if amplify is None:
        # ref_arcsec arcsec → ref_frac of field_width degrees
        amplify = ref_frac * field_width * 3600 / ref_arcsec

    # Convert arcsec → degrees, pre-amplified
    u = df['dRA_arcsec']  * amplify / 3600
    v = df['dDEC_arcsec'] * amplify / 3600

    quiver_kw.setdefault('width', 0.003)
    q = ax.quiver(df['RA_catalog'], df['DEC_catalog'], u, v,
                  scale=1, scale_units='xy', angles='xy',
                  label=label, **quiver_kw)

    # Reference arrow in upper-right corner
    ref_len = ref_arcsec * amplify / 3600
    ax.quiverkey(q, X=0.87, Y=0.95, U=ref_len,
                 label=f'{ref_arcsec}"', labelpos='E',
                 coordinates='axes', fontproperties={'size': 8})

    ax.set_xlabel('RA (deg)')
    ax.set_ylabel('DEC (deg)')
    ax.invert_xaxis()  # RA increases to the left on sky
    return ax


# ---------------------------------------------------------------------------
# High-level: all four plots for one run
# ---------------------------------------------------------------------------

def plot_all(data_dir, *, output_dir=None, title=None, figsize=(12, 10)) -> plt.Figure:
    """Make all four diagnostic plots for a single run.

    Parameters
    ----------
    data_dir : path to a directory containing ECLIPSE_DEFLECTIONS_DATA*.csv
               and ECLIPSE_OUTPUT*.txt
    output_dir : if given, save 'diagnostic.png' there
    title : figure suptitle (defaults to the directory name)

    Returns
    -------
    matplotlib Figure
    """
    data_dir = Path(data_dir)
    fig, axs = plt.subplots(2, 2, figsize=figsize)

    plot_deflection_curve(axs[0, 0], data_dir)
    axs[0, 0].set_title('Deflection vs. radius')

    plot_n_of_r(axs[0, 1], data_dir)
    axs[0, 1].set_title('Star count N(r)')

    plot_delta_of_r(axs[1, 0], data_dir)
    axs[1, 0].set_title('Residuals Δ(r)')

    plot_quiver(axs[1, 1], data_dir)
    axs[1, 1].set_title('Position residuals (quiver)')

    fig.suptitle(title or data_dir.name, fontsize=13)
    fig.tight_layout()

    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        fig.savefig(out / 'diagnostic.png', dpi=150)

    return fig


# ---------------------------------------------------------------------------
# Grid summary
# ---------------------------------------------------------------------------

def plot_grid_heatmap(results_csv, column='L_m1', *,
                      title=None, cmap='RdYlGn_r',
                      vmin=None, vmax=None,
                      figsize=(10, 5)) -> plt.Figure:
    """Heatmap of a scalar result over the zenith × exposure grid.

    Reads experiments/local-grid/results.csv plus the Kaggle results
    passed as additional rows, or just the CSV if it already contains all cells.

    Parameters
    ----------
    results_csv : path to a CSV with columns [zenith, exposure, <column>]
    column      : which column to plot (default 'L_m1')
    """
    df = pd.read_csv(results_csv)
    df[column] = df[column].astype(float)

    # Pivot to zenith (rows) × exposure (cols)
    exposures = ['250ms', '300ms-A', '300ms-B', '400ms']
    zeniths   = [f'z{i:02d}' for i in range(1, 18)]

    # Keep only rows that match our grid
    df = df[df['zenith'].isin(zeniths) & df['exposure'].isin(exposures)]
    pivot = df.pivot(index='zenith', columns='exposure', values=column)
    pivot = pivot.reindex(index=zeniths, columns=exposures)

    fig, ax = plt.subplots(figsize=figsize)
    vmin = vmin or pivot.min().min()
    vmax = vmax or pivot.max().max()
    im = ax.imshow(pivot.values, aspect='auto', cmap=cmap,
                   vmin=vmin, vmax=vmax)

    ax.set_xticks(range(len(exposures)))
    ax.set_xticklabels(exposures)
    ax.set_yticks(range(len(zeniths)))
    ax.set_yticklabels(zeniths)
    ax.set_xlabel('Exposure')
    ax.set_ylabel('Zenith session')

    # Annotate cells with values
    for i in range(len(zeniths)):
        for j in range(len(exposures)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f'{val:.3f}', ha='center', va='center',
                        fontsize=7,
                        color='white' if abs(val - (vmin+vmax)/2) > (vmax-vmin)*0.3
                              else 'black')

    fig.colorbar(im, ax=ax, label=column)
    fig.suptitle(title or column, fontsize=12)
    fig.tight_layout()
    return fig


def plot_grid_deviation(results_csv, column='L_m1', *,
                        title=None, cmap='RdBu_r',
                        figsize=(10, 5)) -> plt.Figure:
    """Heatmap of per-zenith deviations from each exposure's mean.

    For each exposure (column), subtracts that exposure's mean L across all
    17 zenith sessions. The result isolates the zenith systematic: a zenith
    that is consistently red/blue is biasing results regardless of exposure.

    Colour scale is symmetric about zero.
    """
    df = pd.read_csv(results_csv)
    df[column] = df[column].astype(float)

    exposures = ['250ms', '300ms-A', '300ms-B', '400ms']
    zeniths   = [f'z{i:02d}' for i in range(1, 18)]

    df = df[df['zenith'].isin(zeniths) & df['exposure'].isin(exposures)]
    pivot = df.pivot(index='zenith', columns='exposure', values=column)
    pivot = pivot.reindex(index=zeniths, columns=exposures)

    # Subtract each exposure's mean — isolates zenith effect
    deviation = pivot.sub(pivot.mean(axis=0), axis=1)

    vmax = deviation.abs().max().max()
    vmax = np.ceil(vmax * 20) / 20  # round up to nearest 0.05

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(deviation.values, aspect='auto', cmap=cmap,
                   vmin=-vmax, vmax=vmax)

    ax.set_xticks(range(len(exposures)))
    ax.set_xticklabels(exposures)
    ax.set_yticks(range(len(zeniths)))
    ax.set_yticklabels(zeniths)
    ax.set_xlabel('Exposure')
    ax.set_ylabel('Zenith session')

    for i in range(len(zeniths)):
        for j in range(len(exposures)):
            val = deviation.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f'{val:+.3f}', ha='center', va='center',
                        fontsize=7,
                        color='white' if abs(val) > vmax * 0.6 else 'black')

    fig.colorbar(im, ax=ax, label=f'Δ{column} (deviation from exposure mean)')
    fig.suptitle(title or f'{column} deviation from exposure mean', fontsize=12)
    fig.tight_layout()
    return fig
