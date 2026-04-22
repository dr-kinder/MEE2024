# Eclipse Astrometry Pipeline — One-Page Summary

## Goal

Measure Einstein's predicted gravitational deflection of starlight: Δθ = (1.75″) / R, where R is the star's angular distance from the Sun in solar radii. The free parameter is the Einstein Coefficient L ≈ 1.75″; we recover it by fitting a curve to many stars at different angular distances.

## Why Eclipses

Stars near the Sun are normally invisible. Total solar eclipses provide a few minutes of darkness close to the Sun. Distortion and plate-scale errors grow as stars get farther away, so the most scientifically valuable stars are the ones within a few degrees of the Sun — exactly where only a total eclipse provides access.

## The Measurement

Compare observed star positions during the eclipse to their catalog positions (from Gaia) when the Sun is absent. The difference is the deflection. The challenge is that the differences are tiny — 0.1–1.7 arcseconds — while the optical distortion of the lens and the atmosphere can shift apparent positions by tens of arcseconds. Separating the true deflection from these systematics is the central problem.

## Pipeline Stages

### 1. Acquire
Collect three types of image sets:
- **Eclipse field:** Images taken during totality, with the Sun near the field center.
- **Eclipse-day calibration (LEFT/RIGHT):** Fields ~7° left and right of the Sun, taken immediately before and after totality. Same sky, same atmosphere, same camera temperature — but no Sun-induced deflection.
- **Nighttime zenith calibration:** Wide-field images of a rich star field near zenith, taken before or after the eclipse night. Used to characterize high-order optical distortion under stable conditions.

### 2. Stack
Align and co-add many short-exposure frames. Averaging suppresses atmospheric turbulence, cosmic rays, and read noise. For eclipse images, the bright solar corona is subtracted using a blurred-frame technique before centroiding.

### 3. Find Stars
Detect star centroids to sub-pixel accuracy (target: ~0.03 px RMS). Blind plate-solve against the Tycho-2 catalog to determine the plate scale (arcsec/px), pointing (RA/Dec of field center), and roll angle.

### 4. Characterize Optical Distortion
Fit a 2D polynomial to the residuals between observed and catalog positions in the nighttime zenith data. High-order terms (cubic and above) describe the lens's intrinsic distortion and are stable over time. These coefficients are fixed for all subsequent processing.

### 5. Recalibrate Plate Scale
Run the eclipse-day LEFT and RIGHT calibration fields through the same fitting procedure, holding the high-order distortion coefficients fixed. Only the linear and quadratic (plate scale / tilt) terms are adjusted. Interpolate between LEFT and RIGHT to obtain the plate scale at the moment of totality. This accounts for thermal drift and atmospheric refraction changes between the zenith calibration and eclipse day.

### 6. Correct Positions
Apply the full distortion polynomial to the eclipse-field centroids. Then apply Gaia-based astrometric corrections: proper motion, parallax, and atmospheric refraction (which depends on elevation angle and local weather). Stellar aberration is corrected using the observatory's velocity relative to the solar system barycenter.

### 7. Fit for Deflection
Compare corrected observed positions to Gaia catalog positions. The deflection model has four free parameters: L (the Einstein Coefficient) plus small rigid-body offsets (ΔRA, ΔDec, Δroll) that absorb any residual pointing error. Solve for all four simultaneously by least squares over all detected stars.

## Calibration Philosophy

Every systematic that shifts all stars together (pointing drift, atmospheric refraction, roll error) is absorbed by the three rigid-body offsets in the fit. Only the *radial pattern* — stars closer to the Sun deflected more — is attributable to L. This is why a large number of stars at a range of distances is essential: it breaks the degeneracy between a uniform offset and a curved deflection field.

## Error Budget

The dominant uncertainties are:
- **Centroid noise:** ~0.03 px per star; averages down as 1/√N.
- **Distortion residuals:** Fit errors in the polynomial; reduced by more stars in the calibration field.
- **Plate-scale interpolation:** Systematic if the plate scale changes non-linearly between LEFT and RIGHT; reduced by bracketing the eclipse closely in time.
- **Atmospheric refraction model:** Depends on temperature, pressure, humidity; corrected to ~0.01″ with ground-station weather data.

Bruns (2017) achieved 3.4% precision with ~20 stars. MEE2024 targets ~1% with hundreds of stars and improved calibration.
