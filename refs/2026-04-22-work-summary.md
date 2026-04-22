# Work Summary — 2026-04-22

## What We Did

### 1. GUI improvements (gui-improvements branch)

**Load Config bug fixes:**
- `_apply_tab1`: file/dark/flat fields were not populating because the TOML configs use `input_folder`/`dark_folder`/`flat_folder` but the handler only knew about `workDir`/`-DARK-`/`-FLAT-`. Fixed with a translation layer in `_apply_tab1`.
- Folder paths now expanded to semicolon-separated FITS file lists by globbing for `.fit`/`.fits`/`.fts` (case-insensitive).

**Auto-populate inter-tab input files:**
- Tab 2 `-FILE2-`: when `workDir2` is absent from config, globs `output_dir` for `centroid_data*.zip`, picks most recent by mtime.
- Tab 3 `-FILE3-`: same pattern for `distortion_data*.zip`.
- `distortion_reference_files`: if the path in the config doesn't exist (e.g. points to planned inter-stage TOML not yet written), globs the same directory for `distortion_data*.zip` and substitutes. Updates both widget and `options` dict.

**Usability:**
- `sg.set_options(font=('Any', 14))` — 14pt default for all widgets.
- Title bumped to 18pt.
- Each tab wrapped in `sg.Column(scrollable=True, vertical_scroll_only=True, size=(None, 700))`.
- Window marked `resizable=True`.

**Result:** Complete Station 1 pipeline run (zenith → eclipse → deflection fit) using only TOML config files, with no manual field entry. All ZIP inputs auto-resolved.

### 2. Project infrastructure

- `tests/` directory created: `tests/golden/` (committed reference output), `tests/output/station1-calibration/`, `tests/output/station1-eclipse/` (output dirs with `.gitignore` to exclude run artifacts).
- Branching rule documented in CLAUDE.md: non-GUI files originate on `main`, cherry-picked to `gui-improvements`.
- `notes/.gitignore` added to exclude Quarto rendered output (HTML, PDF, docx).

### 3. Student guide and memo

- `docs/student-guide.md`: fixed FIXME paragraph (clarified that calibration fields model non-gravitational distortions, not compare stars directly); added "Note on 2024 Station 1 Data" section explaining the simplified 5-step pipeline and the plate-scale circularity tradeoff.
- `notes/2026-04-22-toml-config-memo.qmd`: Quarto memo for MEE research group; covers the reproducibility problem, Load Config feature, output config TOML, TOML snippet, known ZIP-timestamping limitation, GUI improvements, and future research questions. Renders to HTML/docx/PDF.

## Repository State

```
main             — all infrastructure + student guide + tests/ + memo + CLAUDE.md branching rule
gui-improvements — all of main + GUI improvements (Load Config, font/scroll, auto-ZIP resolution)
```

## Next Steps (Track 1)

3. CLI scripts (`find-stars.py`, `compute-distortion.py`, `fit-data.py`) — replicate each GUI tab as a standalone script driven by TOML config; produces inter-stage file format (`{run}_centroids.csv`, `{run}_distortion.toml`, `{run}_deflection.csv`). Eliminates the timestamped-ZIP workarounds.
4. Left/right calibration interpolation (Standard Pipeline step 7).
5. End-to-end validation on Bruns 2017 dataset.

Jesse also plans to set up a complete example folder for a data run (demonstrating the full config-driven workflow for students) — a natural follow-on to this session's memo.
