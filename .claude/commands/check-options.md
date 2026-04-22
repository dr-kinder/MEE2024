# check-options

Extract every `options` key used by a module and generate a skeleton TOML config with all parameters documented.

## Usage

`/check-options <module>` — e.g. `/check-options stacker_implementation`

## What to do

1. Read `mee2024/<module>.py`.
2. Read `mee2024/UI_handler.py` and `mee2024/main.py` to cross-reference defaults and GUI labels.
3. Find every place the module reads from `options` (pattern: `options['...']` or `options.get('...')`).
4. For each key found, collect:
   - Key name
   - Type (infer from usage or default)
   - Default value (from `main.py` options dict or `options.get(..., default)`)
   - GUI label or description (from `UI_handler.py` if present)
   - Brief description of what it controls

5. Write a skeleton TOML config to `examples/<module>.toml` with:
   - Every parameter present, set to its default value
   - A comment on every line explaining the parameter
   - Parameters grouped logically (input/output paths, stacking, centroid finding, etc.)
   - A header comment block with: script name, pipeline stage, what inputs it expects, what outputs it produces

6. Report any keys that appear in the module but have no default and no GUI entry (potential hidden required parameters).
