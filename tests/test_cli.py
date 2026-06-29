"""
Tests for the specd CLI entry point.
"""

import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[1]


def _run_specd(*args, cwd=None):
    """Run specd as a subprocess and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "specd.cli", *args],
        capture_output=True,
        text=True,
        cwd=cwd or PACKAGE_ROOT,
    )


class TestRenderCommand:

    def test_renders_with_explicit_paths(self, tmp_path):
        """specd render -t TEMPLATES -s SPECS renders templates."""
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()
        (templates_dir / "a.spec.specd.md").write_text(
            "# A\n\n- item\n", encoding="utf-8",
        )

        result = _run_specd(
            "render", "-t", str(templates_dir), "-s", str(specs_dir),
        )
        assert result.returncode == 0
        assert (specs_dir / "a.spec.md").exists()

    def test_exits_nonzero_for_missing_templates_dir(self, tmp_path):
        """specd render exits with code 1 when the templates dir doesn't exist."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        result = _run_specd(
            "render",
            "-t", str(tmp_path / "nonexistent"), "-s", str(specs_dir),
        )
        assert result.returncode == 1
        assert "not found" in result.stdout

    def test_exits_nonzero_for_missing_specs_dir(self, tmp_path):
        """specd render exits with code 1 when the specs dir doesn't exist."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        result = _run_specd(
            "render",
            "-t", str(templates_dir), "-s", str(tmp_path / "nonexistent"),
        )
        assert result.returncode == 1
        assert "not found" in result.stdout


class TestValidateCommand:

    def test_validate_passes_with_compliance(self, tmp_path):
        """specd validate exits 0 when all checks pass."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        (specs_dir / "a.md").write_text(
            "# A\n\n- item one\n", encoding="utf-8",
        )
        (tests_dir / "test_a.py").write_text(
            'def test_one():\n'
            '    """Spec: item one [a.md]"""\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run_specd(
            "validate",
            "-s", str(specs_dir),
            "--tests", str(tests_dir),
        )
        assert result.returncode == 0
        assert "All checks passed" in result.stdout

    def test_validate_fails_with_violations(self, tmp_path):
        """specd validate exits 1 when violations exist."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        (specs_dir / "a.md").write_text(
            "# A\n\n- item one\n- item two\n", encoding="utf-8",
        )
        (tests_dir / "test_a.py").write_text(
            'def test_one():\n'
            '    """Spec: item one [a.md]"""\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run_specd(
            "validate",
            "-s", str(specs_dir),
            "--tests", str(tests_dir),
        )
        assert result.returncode == 1
        assert "SPEC ITEMS WITHOUT RELATED TESTS" in result.stdout

    def test_validate_exits_nonzero_for_missing_dirs(self, tmp_path):
        """specd validate exits 1 when dirs don't exist."""
        result = _run_specd(
            "validate",
            "-s", str(tmp_path / "no_specs"),
            "--tests", str(tmp_path / "no_tests"),
        )
        assert result.returncode == 1


class TestHelpOutput:

    def test_bare_specd_prints_help(self):
        """Bare specd (no subcommand) prints help and exits 0."""
        result = _run_specd()
        assert result.returncode == 0
        assert "render" in result.stdout
        assert "validate" in result.stdout

    def test_help_flag(self):
        """specd --help exits cleanly."""
        result = _run_specd("--help")
        assert result.returncode == 0
        assert "specd" in result.stdout

    def test_render_help_flag(self):
        """specd render --help exits cleanly."""
        result = _run_specd("render", "--help")
        assert result.returncode == 0
        assert "templates" in result.stdout.lower()

    def test_validate_help_flag(self):
        """specd validate --help exits cleanly."""
        result = _run_specd("validate", "--help")
        assert result.returncode == 0
        assert "tests" in result.stdout.lower()
