"""
Tests for template file discovery in the render command.
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


class TestTemplateFilePattern:

    def test_render_writes_all_and_only_specd_templates(self, tmp_path):
        """
        Spec: a file is only recognised as a spec template if it is named in the form *.specd.md [render.md]
        Spec: When the user calls `render` all templates under the specd `templates` directory are rendered into the specd `specs` directory [render.md]
        """
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()

        # Two valid spec templates
        (templates_dir / "alpha.specd.md").write_text("# Alpha\n", encoding="utf-8")
        (templates_dir / "beta.specd.md").write_text("# Beta\n", encoding="utf-8")
        # Non-template files that should be ignored
        (templates_dir / "notes.md").write_text("# Notes\n", encoding="utf-8")
        (templates_dir / "partial.jinja").write_text("some jinja\n", encoding="utf-8")

        result = _run(
            "render", "-t", str(templates_dir), "-s", str(specs_dir)
        )
        assert result.returncode == 0

        output_files = {f.name for f in specs_dir.iterdir()}
        assert output_files == {"alpha.md", "beta.md"}

    def test_only_specd_md_extension_is_recognised(self, tmp_path):
        """
        Spec: a file is only recognised as a spec template if it is named in the form *.specd.md [render.md]
        """
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()

        # A plain .md file — not a *.specd.md template
        (templates_dir / "readme.md").write_text("# Readme\n", encoding="utf-8")

        _run("render", "-t", str(templates_dir), "-s", str(specs_dir))

        assert not any(specs_dir.iterdir())


class TestNoTemplatesFound:

    def test_no_templates_found_prints_message(self, tmp_path):
        """
        Spec: If no templates are found in the specd `templates` directory, `render` prints `No *.specd.md templates found in <templates dir name>/` [render.md]
        """
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()

        result = _run(
            "render", "-t", str(templates_dir), "-s", str(specs_dir)
        )
        expected = f"No *.specd.md templates found in {templates_dir.name}/"
        assert expected in result.stdout
