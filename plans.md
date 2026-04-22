= Plans for MEE Code =

Work with Claude to flesh out and implement successive improvements to the MEE
data analysis pipeline.

== Track 1: Make It Work (Reproducible Research) ==

Goal: Community tool.  Shareable with MEE collaborators and the broader community.

The Problem
-----------

The GUI is a user-friendly interface for beginners, but a straightjacket for
doing anything other than the "standard analysis" --- in particular, batch
processing of different experiments on the data.

It is also an impediment to reproducible research.  There are many parameters
and no easy way to ensure they are set consistently each time.  The different
parameters required for different stages in the analysis make consistent data
analysis protocols difficult to execute.

The output is currently zipped for no apparent reason.  The file names are
unique, but difficult to parse and identify when needed:
`distortion_data20260121154518__centroid_data2026012115381020260121153810.zip`

The Solution
------------

TOML config files that can be shared and version-controlled.  Two interfaces:
a GUI button to load a config file (for students), and CLI scripts for
scripted/batch work.

Station 1 (wide angle with no eclipse day calibration) requires one sequence:

1. Tab 1 on zenith
2. Tab 2 on output of 1 (fix distortion coefficients)
3. Tab 1 on eclipse
4. Tab 2 on output of 2+3
5. Tab 3 on output of 4

The other stations and the 2017 data require a different sequence:

1. Tab 1 on zenith
2. Tab 2 on output of #1
3. Tab 1 on eclipse calibration left
4. Tab 1 on eclipse calibration right
5. Tab 2 on output of 2+3
6. Tab 2 on output of 2+4
7. Interpolation of output of 5+6  <-- NEW, not available in GUI
8. Tab 1 on eclipse field
9. Tab 2 on output of 7+8
10. Tab 3 on output of 9

All planned future MEE eclipse campaigns include eclipse-day calibration images,
so the Standard Pipeline (steps 1-10) is the target for all new work.


The Plan
--------

Ordered by priority:

0. [DONE] Define the inter-stage file format.
   - Each stage writes human-readable output with descriptive names:
       find-stars     --> {run}_centroids.csv  +  {run}_stack.fits
       compute-distortion --> {run}_distortion.toml  (coefficients + metadata)
       fit-data       --> {run}_deflection.csv  +  diagnostic plots
   - Replace tqdm for progress output (replaces FreeSimpleGUI progress popups).

1. [DONE] Write TOML config files for each script.
   - Five configs in configs/ covering the Station 1 simple pipeline:
       station1-sample-find-stars-calibration.toml
       station1-sample-find-stars-eclipse.toml
       station1-sample-compute-distortion-zenith.toml
       station1-sample-compute-distortion-eclipse.toml
       station1-sample-fit-data.toml
   - All parameters documented with comments grounded in the oas-poster analysis.
   - Supports folder OR explicit file list input.
   - configs/ = ready-to-run run configs; examples/ = skeleton templates (from /check-options).

2. [DONE] Add "Load config" button to GUI.
   - Populates all GUI fields from a TOML file (gui-improvements branch).
   - Also added: write output config_tab{1,2,3}.toml to output dir on each run,
     recording the exact settings used (written before processing begins).

3. CLI scripts replicating each GUI tab.
   - find-stars.py     (Tab 1 / stacker_implementation.py)
   - compute-distortion.py  (Tab 2 / distortion_fitter.py)
   - fit-data.py       (Tab 3 / eclipse_analysis.py)

4. Implement left/right calibration interpolation (Standard Pipeline step 7).
   - This is the critical new piece that makes the Standard Pipeline possible.
   - Not in the GUI at all.  Must be a new script or function.

5. End-to-end validation on Bruns 2017 dataset.
   - Reproduce Bruns' published deflection measurement.
   - Use as regression test going forward.


Potential Use
-------------

Does the choice of zenith field affect the final results?
Run eclipse analysis with nothing changed but the set of calibration images.

Are more images better?
Run eclipse analysis with batches of 10, 20, 40, 100, 200, ..., images.
Look for point of diminishing returns in precision.

What is the optimal set of parameters?
Run eclipse analysis on well-chosen sets of parameters to infer sensitivity,
do a grid optimization.


== Track 2: Make It Right (Toolkit) ==

Goal: Personal research tool for Jesse.  May be useful to the community but
is not the primary goal.  Begin only after Track 1 is working and validated.

The Problem
-----------

The current MEE pipeline is a complex machine designed to do one particular
set of tasks.  This inhibits exploration and adaptation for other analyses.

The goal is not to wrap the existing code in modules and functions, but to
strip it down to essentials and make these accessible to programmers.

The Solution
------------

Reorganize or rewrite the existing codebase as a set of tools that can be
used independently and modified easily.

Make it easy to ...
- run the analysis in a Jupyter notebook, on Kaggle
- run experiments with Python scripts
- build new analysis pipelines with current tools (e.g., Bruns analysis)
- replace functions or modules with alternatives (e.g., centroid finding)
- explore alternative data analysis methods (e.g., maximum likelihood stacking)


The Plan
--------

1. Strip the existing code down to only what is essential.
2. Identify functions with natural modularity.
3. Reorganize into modules for specific astrometric tasks.


Potential Use
-------------

Replace distortion polynomials with orthogonal Legendre polynomials.

Explore alternative centroid finding algorithms.

Develop a data analysis pipeline for coronagraph images.

Adapt Sigworth's maximum-likelihood stacking method for cryoelectron microscopy
to eclipse and zenith images.
