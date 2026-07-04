"""
Tests for configuration resolution.
"""

from pathlib import Path

from specd.config import find_pyproject, resolve_paths


class TestFindPyproject:

    def test_finds_pyproject_in_start_dir(self, tmp_path):
        """Finds [tool.specd] in a pyproject.toml in the start directory."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.specd]\ntemplates = "my_templates"\n',
            encoding="utf-8",
        )
        config, root = find_pyproject(tmp_path)
        assert config == {"templates": "my_templates"}
        assert root == tmp_path.resolve()

    def test_walks_up_to_find_pyproject(self, tmp_path):
        """Walks up from a subdirectory to find pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.specd]\nspecs = "output"\n',
            encoding="utf-8",
        )
        child = tmp_path / "sub" / "deep"
        child.mkdir(parents=True)
        config, root = find_pyproject(child)
        assert config == {"specs": "output"}
        assert root == tmp_path.resolve()

    def test_ignores_pyproject_without_tool_specd(self, tmp_path):
        """A pyproject.toml without [tool.specd] is skipped."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.black]\nline-length = 88\n',
            encoding="utf-8",
        )
        config, _ = find_pyproject(tmp_path)
        assert config == {}

    def test_returns_empty_when_no_pyproject(self, tmp_path):
        """Returns an empty dict when no pyproject.toml is found."""
        empty = tmp_path / "isolated"
        empty.mkdir()
        config, _ = find_pyproject(empty)
        assert config == {}


class TestResolvePaths:

    def test_explicit_args_take_priority(self, tmp_path):
        """Explicit arguments override everything else."""
        templates_arg = tmp_path / "explicit_templates"
        specs_arg = tmp_path / "explicit_specs"
        tests_arg = tmp_path / "explicit_tests"

        paths = resolve_paths(
            templates=str(templates_arg),
            specs=str(specs_arg),
            tests=str(tests_arg),
        )
        assert paths["templates"] == templates_arg.resolve()
        assert paths["specs"] == specs_arg.resolve()
        assert paths["tests"] == tests_arg.resolve()

    def test_pyproject_config_used_when_no_explicit_args(self, tmp_path):
        """Config from pyproject.toml is used when no args are supplied."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.specd]\ntemplates = "src/templates"\n'
            'specs = "src/specs"\n',
            encoding="utf-8",
        )
        paths = resolve_paths(start_dir=tmp_path)
        assert paths["templates"] == (tmp_path / "src" / "templates").resolve()
        assert paths["specs"] == (tmp_path / "src" / "specs").resolve()

    def test_explicit_overrides_pyproject(self, tmp_path):
        """An explicit arg overrides the pyproject.toml value."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.specd]\ntemplates = "configured"\n',
            encoding="utf-8",
        )
        explicit = tmp_path / "override"
        paths = resolve_paths(
            templates=str(explicit),
            start_dir=tmp_path,
        )
        assert paths["templates"] == explicit.resolve()
