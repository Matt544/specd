"""
Manifest and rendering support for the `specd resources` command.

Keys are short names used with --only; values are filenames in the
package's resources/ data directory. Most resources are copied verbatim;
test-writing-policy.md is rendered through Jinja2 with language-dependent
context derived from the project's pyproject.toml configuration.
"""

import importlib.resources

from jinja2 import Environment, BaseLoader

from specd.config import find_pyproject

RESOURCES = {
    "spec-writing": "spec-writing-policy.md",
    "test-writing": "test-writing-policy.md",
    "spec-implementation": "spec-implementation-policy.md",
    "specd-orientation": "specd-orientation.md",
}

_TEMPLATE_RESOURCES = {"test-writing-policy.md", "specd-orientation.md"}


def _js_deps_installed():
    """Check whether the specd[js] optional dependencies are available."""
    try:
        import tree_sitter_javascript  # noqa: F401

        return True
    except ImportError:
        return False


_DIR_DEFAULTS = {
    "templates": "templates/",
    "specs": "specs/",
    "tests": "tests/",
    "resources": "resources/",
}


def _build_template_context():
    """
    Compute Jinja template variables for resource templates.

    Provides language flags (for test-writing-policy.md) and directory
    path strings (for specd-orientation.md), all derived from the
    project's [tool.specd] configuration.
    """
    specd_config, _ = find_pyproject()

    # Language flags
    languages = specd_config.get("languages")

    if languages is not None:
        include_python = "python" in languages
        include_js_ts = (
            "javascript" in languages or "typescript" in languages
        )
    else:
        include_python = True
        include_js_ts = _js_deps_installed()

    # Directory path strings: configured value + "/" or the default
    dir_vars = {}
    for key, default in _DIR_DEFAULTS.items():
        if key in specd_config:
            dir_vars[f"{key}_dir"] = specd_config[key].rstrip("/") + "/"
        else:
            dir_vars[f"{key}_dir"] = default

    return {
        "include_python": include_python,
        "include_js_ts": include_js_ts,
        **dir_vars,
    }


def read_resource(filename):
    """
    Read a bundled resource file and return its content as a string.

    All resources are read as text, which normalizes line endings to
    ``\\n``. Template resources (test-writing-policy.md) are additionally
    rendered through Jinja2 with language-dependent context.
    """
    resources_dir = importlib.resources.files("specd") / "resources"
    raw = (resources_dir / filename).read_text(encoding="utf-8")

    if filename in _TEMPLATE_RESOURCES:
        context = _build_template_context()
        env = Environment(
            loader=BaseLoader(),
            keep_trailing_newline=True,
        )
        template = env.from_string(raw)
        return template.render(**context)

    return raw
