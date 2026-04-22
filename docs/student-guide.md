# Guide to the Modern Eddington Experiment: What We're Doing and Why

## The Experiment in One Sentence

We photograph stars near the Sun during a total solar eclipse, measure how much gravity has bent their light, and compare the result to Einstein's prediction.

---

## Historical Background

In 1919, Arthur Eddington photographed the Hyades star cluster during a total solar eclipse and measured that stars appeared shifted outward from their catalog positions, consistent with Einstein's General Theory of Relativity. The measurement had large uncertainties (roughly 20–30%), but it was the first experimental test of a non-Newtonian theory of gravity and made Einstein world-famous.

Since then, the prediction has been confirmed to better than 0.01% using radio interferometry (VLBI) of quasars passing near the Sun. But optical measurements from ground-based telescopes during eclipses remain scientifically interesting because:

1. They test whether the deflection law holds for visible-wavelength photons.
2. They can be performed with modest equipment by university groups.
3. Better equipment and software have not been fully applied — the best modern optical measurement (Bruns 2017) still had 3.4% uncertainty, leaving real room for improvement.

The Modern Eddington Experiment (MEE) is a coordinated effort by an international group of amateur and professional astronomers to push this precision toward 1% or better.

---

## What Einstein's Theory Predicts

A photon passing at an angular distance R (in solar radii) from the center of the Sun is deflected by:

```
Δθ = 1.7512 arcseconds / R
```

This number — 1.7512 arcseconds — is the **Einstein Coefficient** L. It is derived from the Sun's mass and the speed of light; Newtonian gravity predicts exactly half this value. We call L the thing we are measuring.

One arcsecond is 1/3600 of a degree, or roughly the angular size of a dime seen from 4 km away. The deflections we're after are sub-arcsecond for all but the closest stars.

---

## Why Total Eclipses?

Stars near the Sun are washed out by scattered sunlight in the day sky. Stray light from the sky is bright enough to hide even fairly bright stars within several degrees of the Sun. Total solar eclipses suppress this background for a few minutes — long enough to take useful images.

The catch is that the deflection is largest *close to the Sun*, where it matters most scientifically and where it is also hardest to observe. Stars 2–3 solar radii from the Sun are deflected by 0.6–0.9 arcseconds; stars 10–20 solar radii away by 0.09–0.17 arcseconds. We need precise position measurements for stars across this range.

---

## The Central Challenge: Optical Distortion

A camera lens doesn't project a perfect map of the sky. Barrel distortion, pin-cushion distortion, and higher-order aberrations can shift stars' apparent positions by tens of arcseconds — far more than the deflections we want to measure. We can't simply subtract these by calibrating one night, because:

- The lens changes slightly with temperature.
- The atmosphere refracts light by different amounts depending on elevation angle, temperature, pressure, and humidity.
- The plate scale (arcseconds per pixel) can shift by a small amount between the night of calibration and the day of the eclipse.

**Everything the pipeline does is aimed at separating the true gravitational deflection from these optical and atmospheric systematics.**

---

## Data Collection Strategy

Three types of images are needed:

### Nighttime Zenith Calibration
Taken the night before (or after) the eclipse. A rich star field near the zenith is photographed under stable, slow-moving conditions. These images are used to characterize the *optical distortion* of the lens — the repeatable geometric errors in how the lens maps sky positions to pixel positions. High-order distortion terms (cubic and above) are stable over time and are fixed using these data.

### Eclipse-Day Calibration: LEFT and RIGHT Fields
Taken *during the eclipse event* — before and after totality — at fields ~7° to the left and right of the Sun. These fields contain the same sky, the same atmosphere, and the same camera temperature as the eclipse. Since the Sun is not in the field, there is no gravitational deflection. These images let us recalibrate the plate scale and low-order distortion at the exact epoch of the eclipse, fixing the thermal drift and refraction mismatch.

### Eclipse Field
Taken during totality with the Sun near the center of the field. These are the science images. We want as many short-exposure frames as possible to reduce noise.

The key insight is: by comparing the eclipse field to the immediately preceding and following calibration fields, we isolate what changed *because the Sun is present*. That difference is the deflection.

---

## The Pipeline, Step by Step

### Step 1: Stack

Each image set contains hundreds of individual frames. We align them to a common reference (accounting for atmospheric jitter and small tracking errors) and average them together. Averaging N frames reduces noise by √N. We also subtract the bright solar corona in the eclipse images by subtracting a heavily blurred version of the stacked image — the corona is extended and blurs easily; the stars do not.

**What comes out:** A single deep image per field, with stars detectable to faint limiting magnitudes.

### Step 2: Find Stars (Centroiding)

For each star in the stacked image, we fit a 2D profile to find the center of light to sub-pixel precision. Good centroiding algorithms achieve 0.03–0.05 pixel (roughly 0.05–0.1 arcsecond) RMS. The number of detected stars matters: more stars → lower statistical uncertainty in the final fit.

**What comes out:** A table of (x, y) pixel positions for every detected star.

### Step 3: Plate Solve

We match the pattern of detected stars against a catalog (Tycho-2, which covers the whole sky to magnitude ~11). This is called a "blind" plate solve because we don't tell the solver where in the sky to look — it figures out the pointing, plate scale, and roll angle from the star pattern alone. After a successful solve, we know exactly which catalog star corresponds to which detected pixel position.

**What comes out:** RA/Dec pointing, plate scale (arcsec/px), roll angle, and a matched list of catalog↔pixel pairs.

### Step 4: Characterize Optical Distortion (Zenith Data)

Using the matched catalog↔pixel pairs from the nighttime zenith images, we fit a 2D polynomial in pixel coordinates:

```
x_corrected = x + Σ A_{n,i} α^i β^(n-i)
y_corrected = y + Σ B_{n,i} α^i β^(n-i)
```

where (α, β) are pixel coordinates scaled to the range [-1, 1]. The sum runs over polynomial terms of degree 1 through 5 (or higher for wide-field lenses). The coefficients A and B describe how much each point in the image is shifted by the lens distortion.

The low-degree terms (1st and 2nd order) are plate scale, tilt, and quadratic terms that can shift slowly with temperature. The **high-degree terms** (3rd order and above) are the stable geometric distortion of the lens, fixed once for the night from the zenith data.

**What comes out:** A table of polynomial coefficients that map observed pixel positions to "true" (corrected) pixel positions.

### Step 5: Recalibrate Plate Scale (LEFT/RIGHT Data)

We run the LEFT and RIGHT eclipse-day calibration fields through the same fitting procedure, but hold the high-order polynomial coefficients fixed at their nighttime values. Only the 1st- and 2nd-order terms are allowed to vary. The result is a plate scale and tilt valid at the moment the LEFT and RIGHT fields were taken.

We then **interpolate** between LEFT and RIGHT to get the plate scale at the moment of totality. This is necessary because temperature, atmospheric conditions, and refraction change throughout the eclipse event, and the plate scale changes with them.

**What comes out:** Corrected polynomial coefficients valid at eclipse epoch.

### Step 6: Correct Star Positions

Apply the full distortion polynomial to the eclipse-field centroids. This removes the optical distortion and brings positions to a flat, undistorted sky plane.

Then apply astrometric corrections from the Gaia catalog:
- **Proper motion:** Stars are moving. Gaia gives velocities; we propagate catalog positions to the epoch of observation.
- **Parallax:** Stars appear shifted by up to ~1 arcsecond due to Earth's orbital position. Gaia provides precise parallaxes for all nearby stars.
- **Atmospheric refraction:** The atmosphere bends light toward the zenith by an amount that depends on elevation angle, wavelength, temperature, pressure, and humidity. We compute the correction using ground-station weather data.
- **Stellar aberration:** Earth's orbital motion (~30 km/s) shifts star positions by up to ~20 arcseconds. We apply the classical (and relativistic) aberration correction.

**What comes out:** Corrected observed positions in the undistorted, atmospherically-corrected sky frame.

### Step 7: Measure Deflections and Fit for L

For each star, compute the difference between the corrected observed position and the Gaia catalog position. This residual is the combination of:
1. Gravitational deflection (what we want)
2. Small residual pointing error (ΔRA, ΔDec, Δroll) from imperfect plate solving

We fit a model with four free parameters:

```
Δθ_observed = L × (1.7512″ / R) + rigid_body_offset(ΔRA, ΔDec, Δroll)
```

by minimizing the sum of squared residuals over all detected stars simultaneously. The rigid-body offsets absorb any residual systematic pointing error. The curve shape — stars closer to the Sun are deflected more — is unique to gravitation and can't be mimicked by a pointing offset.

The best-fit value of L is the result.

---

## Why This is Hard (and Interesting)

| Challenge | Scale | Mitigation |
|-----------|-------|------------|
| Gravitational deflection (signal) | 0.1–1.7 arcsec | — |
| Optical distortion | up to ~50 arcsec | Polynomial fit from zenith data |
| Thermal plate-scale drift | ~0.1% = ~1 arcsec for stars 10′ from center | LEFT/RIGHT recalibration |
| Atmospheric refraction | up to ~1 arcsec at low elevation | Computed from weather data |
| Stellar proper motion | up to ~1 arcsec/year for nearby stars | Gaia catalog + epoch propagation |
| Centroid noise (per star) | ~0.05 arcsec | Averages as 1/√N_stars |

The measurement is the difference between the corrected observed position and the Gaia position. Gaia positions have uncertainties of a few tens of microarcseconds — essentially perfect. The limitation is our ability to correct for the optical and atmospheric systematics above.

---

## What We've Measured So Far

**Bruns (2017):** L = 1.75 ± 0.05 arcseconds, 3.4% precision. Used a CCD camera, ~20 stars, LEFT/RIGHT calibration fields 7.4° from the Sun. Published in *Classical and Quantum Gravity*.

**MEE2024 (2024 eclipse):** L = 1.84 ± 0.24 arcseconds, ~13% precision, from one station. The analysis is still being refined. Multiple stations observed the 2024 eclipse; combining data from all stations should improve precision.

---

## The Software

The MEE2024 pipeline is a Python package currently structured around a three-tab GUI:

- **Tab 1 (find-stars):** Image stacking, centroid finding, plate solving.
- **Tab 2 (compute-distortion):** Distortion polynomial fitting, including the zenith/calibration workflow.
- **Tab 3 (fit-data):** Astrometric corrections, deflection measurement, L fit.

We are building CLI scripts (`find-stars`, `compute-distortion`, `fit-data`) driven by TOML configuration files, so the full 10-step Standard Pipeline can be run reproducibly from the command line. The GUI remains available for interactive exploration.

---

## Further Reading

- Bruns (2017), *Classical and Quantum Gravity* 34, 195009 — the best modern optical measurement; detailed methods
- Smith et al. (MEE2024 pre-eclipse paper) — survey of the method, equipment, and simulated precision estimates
- Smith et al. (MEE2024 results paper) — description of the 2024 eclipse observations and preliminary results
