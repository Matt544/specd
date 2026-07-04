# Live samples

A self-contained sample project used by the test suite as committed fixtures. Changes to these files are validated by real tests, so they cannot drift from the code they document.

## Structure

- `pyproject.toml` — configures `[tool.specd]` paths for this sample project
- `specs/templates/` — Jinja2 spec templates (input for `specd render`)
- `specs/gen/` — generated spec files (output of `specd render`, input for `specd validate`)
- `tests/` — sample Python and JS test files citing spec items

## What validates what

The rendering test in `test_render.py` renders the template in `specs/templates/` into `specs/gen/` and verifies the output.

The validation test in `test_validate.py` runs `specd validate` against `specs/gen/` and `tests/` to verify that citation matching works end-to-end, including items containing `\\n` and `\\n\\n`.

## Why the sample tests are not collected by pytest

The files under `tests/` are sample test files — they exist for `specd validate` to parse, not for pytest to run. The `conftest.py` in this directory excludes them from pytest collection.
