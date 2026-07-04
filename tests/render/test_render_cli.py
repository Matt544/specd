"""
Tests for render command CLI behavior: subcommand, directory resolution options,
and per-template terminal output.
"""

import subprocess
import sys
from pathlib import Path

SPECD = [sys.executable, "-m", "specd.cli"]


def _run(*args, cwd=None):
    """Run specd with the given arguments and return CompletedProcess."""
    return subprocess.run(
        SPECD + list(args),
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )


def _write_template(templates_dir, name="foo.specd.md", content="# Foo\n"):
    """Write a single template file in the given directory."""
    (Path(templates_dir) / name).write_text(content, encoding="utf-8")


class TestRenderSubcommand:

    def test_render_is_valid_subcommand(self):
        """
        Spec: `render` is a valid positional argument to the `specd` command line entrypoint [render.md]
        """
        result = _run("render", "--help")
        assert "invalid" not in result.stdout.lower()
        assert "unrecognized" not in result.stderr.lower()


class TestRenderTerminalOutput:

    def test_render_terminal_output_line_format(self, tmp_path):
        """
        Spec: When the user calls `render`, each template that is rendered to a spec file is represented in the terminal as `  <scope>.specd.md -> <specs directory name>/<scope>.md` [render.md]
        """
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "my_specs"
        templates_dir.mkdir()
        specs_dir.mkdir()

        _write_template(templates_dir, "foo.specd.md")

        result = _run(
            "render", "-t", str(templates_dir), "-s", str(specs_dir)
        )
        assert f"  foo.specd.md -> {specs_dir.name}/foo.md" in result.stdout


class TestTemplateDirectoryOptions:

    def test_t_flag_sets_templates_dir(self, tmp_path):
        """
        Spec: if `render` is called with the `-t` or `--templates` options, templates are discovered only at the supplied location [render.md]
        """
        custom_templates = tmp_path / "my_templates"
        specs_dir = tmp_path / "specs"
        custom_templates.mkdir()
        specs_dir.mkdir()

        _write_template(custom_templates)

        result = _run(
            "render", "-t", str(custom_templates), "-s", str(specs_dir)
        )
        assert result.returncode == 0
        assert (specs_dir / "foo.md").exists()

    def test_templates_flag_sets_templates_dir(self, tmp_path):
        """
        Spec: if `render` is called with the `-t` or `--templates` options, templates are discovered only at the supplied location [render.md]
        """
        custom_templates = tmp_path / "my_templates"
        specs_dir = tmp_path / "specs"
        custom_templates.mkdir()
        specs_dir.mkdir()

        _write_template(custom_templates)

        result = _run(
            "render", "--templates", str(custom_templates), "-s", str(specs_dir)
        )
        assert result.returncode == 0
        assert (specs_dir / "foo.md").exists()

    def test_default_templates_dir_is_cwd_templates(self, tmp_path):
        """
        Spec: If the specd `templates` directory is not configured with a pyproject.toml and the `-t` or `--templates` options are not used, the templates are discovered in `templates/` under the cwd [render.md]
        """
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()

        _write_template(templates_dir)

        result = _run("render", "-s", str(specs_dir), cwd=tmp_path)
        assert result.returncode == 0
        assert (specs_dir / "foo.md").exists()

    def test_templates_dir_from_pyproject_toml(self, tmp_path):
        """
        Spec: If the specd `templates` directory is configured with a pyproject.toml, that is the directory in which templates are discovered [render.md]
        """
        custom_templates = tmp_path / "my_templates"
        specs_dir = tmp_path / "specs"
        custom_templates.mkdir()
        specs_dir.mkdir()

        (tmp_path / "pyproject.toml").write_text(
            "[tool.specd]\n"
            'templates = "my_templates"\n',
            encoding="utf-8",
        )
        _write_template(custom_templates)

        result = _run("render", "-s", str(specs_dir), cwd=tmp_path)
        assert result.returncode == 0
        assert (specs_dir / "foo.md").exists()

    def test_missing_templates_dir_prints_warning_and_exits_1(self, tmp_path):
        """
        Spec: If no directory exists at the specd `templates` directory location, a warning is printed: "The expected templates dir does not exist"; then it exits code 1 [render.md]
        """
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        nonexistent = tmp_path / "no_such_dir"

        result = _run(
            "render", "-t", str(nonexistent), "-s", str(specs_dir)
        )
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "The expected templates dir does not exist" in combined


class TestSpecsDirectoryOptions:

    def test_s_flag_sets_specs_dir(self, tmp_path):
        """
        Spec: If `render` is called with the `-s` or `--specs` options, specs are written into the supplied location [render.md]
        """
        templates_dir = tmp_path / "templates"
        custom_specs = tmp_path / "my_specs"
        templates_dir.mkdir()
        custom_specs.mkdir()

        _write_template(templates_dir)

        result = _run(
            "render", "-t", str(templates_dir), "-s", str(custom_specs)
        )
        assert result.returncode == 0
        assert (custom_specs / "foo.md").exists()

    def test_specs_flag_sets_specs_dir(self, tmp_path):
        """
        Spec: If `render` is called with the `-s` or `--specs` options, specs are written into the supplied location [render.md]
        """
        templates_dir = tmp_path / "templates"
        custom_specs = tmp_path / "my_specs"
        templates_dir.mkdir()
        custom_specs.mkdir()

        _write_template(templates_dir)

        result = _run(
            "render", "-t", str(templates_dir), "--specs", str(custom_specs)
        )
        assert result.returncode == 0
        assert (custom_specs / "foo.md").exists()

    def test_default_specs_dir_is_cwd_specs(self, tmp_path):
        """
        Spec: If the specd `specs` directory is not configured with a pyproject.toml and the `-s` or `--specs` options are not used, the specs are written into `specs/` under the cwd [render.md]
        """
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()

        _write_template(templates_dir)

        result = _run("render", "-t", str(templates_dir), cwd=tmp_path)
        assert result.returncode == 0
        assert (specs_dir / "foo.md").exists()

    def test_specs_dir_from_pyproject_toml(self, tmp_path):
        """
        Spec: If the specd `specs` directory is configured with a pyproject.toml, that is the directory in which specs are written [render.md]
        """
        templates_dir = tmp_path / "templates"
        custom_specs = tmp_path / "my_specs"
        templates_dir.mkdir()
        custom_specs.mkdir()

        (tmp_path / "pyproject.toml").write_text(
            "[tool.specd]\n"
            'specs = "my_specs"\n',
            encoding="utf-8",
        )
        _write_template(templates_dir)

        result = _run("render", "-t", str(templates_dir), cwd=tmp_path)
        assert result.returncode == 0
        assert (custom_specs / "foo.md").exists()

    def test_missing_specs_dir_prints_warning_and_exits_1(self, tmp_path):
        """
        Spec: If no directory exists at the specd `specs` directory location, a warning is printed: "The expected specs dir does not exist"; then it exits code 1 [render.md]
        """
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        _write_template(templates_dir)
        nonexistent = tmp_path / "no_such_specs"

        result = _run(
            "render", "-t", str(templates_dir), "-s", str(nonexistent)
        )
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        assert "The expected specs dir does not exist" in combined
