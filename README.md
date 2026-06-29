# specd

Render Jinja2 spec templates and validate that tests cite spec items.

## Install

```bash
pip install -e specd/
```

## Usage

### Render templates

Templates are `*.specd.md` files in the templates directory. Each template is rendered through Jinja2 and written to the specs directory as a `.md` file (e.g., `qa.specd.md` becomes `qa.md`). Rendered files are prefixed with a generated-file marker — do not edit them by hand, as they will be overwritten on the next render.

```bash
specd render
specd render -t path/to/templates -s path/to/specs
specd render --watch
```

### Validate test/spec compliance

Validation checks three things:

- Every test function has at least one `Spec:` citation linking it to a spec item
- Every spec item in `specs/` is cited by at least one test
- Every citation resolves to a real item in a real spec file (no phantom references)

Spec files are `.md` files in the specs directory. Each line starting with `- ` is treated as a spec item.

Tests cite spec items by including a line in their docstring in this form:

```
Spec: <verbatim spec item text> [<spec filename>]
```

For example:

```python
def test_log_with_no_args():
    """
    Spec: always log timestamp, status, and message [log.md]
    """
    ...
```

Run validation:

```bash
specd validate
specd validate -s path/to/specs --tests path/to/tests
```

## Configuration

By default, specd looks for `templates/`, `specs/`, and `tests/` directories relative to the current working directory. You can override these with CLI flags (`-t`, `-s`, `--tests`) or by adding a `[tool.specd]` section to your `pyproject.toml`:

```toml
[tool.specd]
templates = "path/to/templates"
specs = "path/to/specs"
tests = "path/to/tests"
```

CLI flags take priority over `pyproject.toml`, which takes priority over the defaults.
