"""
Configuration resolution for specd.

Resolves templates, specs, and tests directories using this priority:
1. Explicit arguments (from CLI flags)
2. [tool.specd] in a pyproject.toml found by walking up from cwd
3. Convention defaults relative to cwd
"""

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib


def find_pyproject(start_dir=None):
    """
    Walk up from start_dir (default: cwd) looking for a pyproject.toml
    that contains a [tool.specd] section. Returns the parsed section as
    a dict, or an empty dict if none is found.
    """
    if start_dir is None:
        start_dir = Path.cwd()
    current = Path(start_dir).resolve()

    while True:
        candidate = current / "pyproject.toml"
        if candidate.is_file():
            with open(candidate, "rb") as f:
                data = tomllib.load(f)
            specd_config = data.get("tool", {}).get("specd", {})
            if specd_config:
                return specd_config, current
        parent = current.parent
        if parent == current:
            break
        current = parent

    return {}, Path.cwd()


def resolve_paths(templates=None, specs=None, tests=None, start_dir=None):
    """
    Resolve the templates, specs, and tests directories.

    Explicit arguments take priority, then [tool.specd] from
    pyproject.toml, then convention defaults relative to cwd.

    Returns a dict with keys "templates", "specs", "tests", each a Path.
    """
    file_config, project_root = find_pyproject(start_dir)

    def _resolve(explicit, config_key, default):
        if explicit is not None:
            return Path(explicit).resolve()
        if config_key in file_config:
            return (project_root / file_config[config_key]).resolve()
        return Path.cwd().resolve() / default

    return {
        "templates": _resolve(templates, "templates", "templates"),
        "specs": _resolve(specs, "specs", "specs"),
        "tests": _resolve(tests, "tests", "tests"),
    }
