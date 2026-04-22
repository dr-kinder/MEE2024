# explore-mee

Read a MEE2024 source module and produce a structured summary useful for porting it to a CLI script.

## Usage

`/explore-mee <module>` — e.g. `/explore-mee stacker_implementation` or `/explore-mee distortion_fitter`

## What to do

1. Read the specified module from `mee2024/<module>.py`.
2. Also read `mee2024/UI_handler.py` to find the `interpret_UI_values` function(s) that feed options into this module.
3. Produce a structured report with these sections:

### What it does
One paragraph: the scientific/computational purpose of this module.

### Entry point(s)
The top-level function(s) called by `main.py` or `UI_handler.py`. Signature and brief description of each.

### Inputs
- Files consumed (type, format, where they come from in the pipeline)
- Keys read from the `options` dict — list every key this module uses, with its type, default value if known, and one-line description. Cross-reference against `interpret_UI_values` to flag any that are missing from the GUI config.

### Outputs
- Files written (name pattern, format, contents)
- Any return values passed back to `main.py`

### GUI coupling
List every import or call to `FreeSimpleGUI` (or `sg.*`) in this module. For each: what it does and what the CLI replacement should be (usually `tqdm`, `logging`, or a plain `print`).

### Essential vs. incidental
Which functions/classes are core scientific logic vs. GUI glue, file I/O boilerplate, or legacy workarounds. Flag anything that looks like dead code.

### Porting notes
Any gotchas, dependencies on other modules, or design decisions worth flagging before writing the CLI script.
