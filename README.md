# SpecD

`specd` (`/spɛk ˈdiː/` or "speck dee") facilitates developing software with LLM agents using a spec-test-matching approach.

It renders Jinja2 spec templates and validate that tests cite spec items.

## Install

```bash
pip install -e specd/
```

For JavaScript/TypeScript test support (requires tree-sitter):

```bash
pip install -e "specd/[js]"
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

Tests cite spec items by including a citation in this form:

```
Spec: <verbatim spec item text> [<spec filename>]
```

### Python tests

In Python, citations go in the test function's docstring:

```python
def test_log_with_no_args():
    """
    Spec: always log timestamp, status, and message [log.md]
    """
    ...
```

### JavaScript/TypeScript tests

In JS/TS, citations go in `//` comments inside the test body:

```javascript
test("logs with no args", () => {
  // Spec: always log timestamp, status, and message [log.md]
  ...
});
```

Multiple citations are separate comment lines. Citations work inside `describe()` blocks at any nesting depth. `test()`, `it()`, and their `.skip`/`.only` variants are all supported. Test files must match `*.test.{js,jsx,ts,tsx}`.

Supported frameworks: Jest, Vitest, Mocha, and any framework using the `test()`/`it()`/`describe()` API.

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

Note: `specd validate` reads specs from a single directory. If you use separate directories for templates and generated specs (e.g., `specs/templates/` and `specs/gen/`), hand-written spec files must also be placed in the configured `specs` directory so that validation can find them.
