"""
Tests for spec file discovery and parsing in the validate command.
"""

import subprocess
import sys
from pathlib import Path

SPECD = [sys.executable, "-m", "specd.cli"]


def _run_validate(specs_dir, tests_dir):
    """Run specd validate with explicit directory paths and return CompletedProcess."""
    return subprocess.run(
        SPECD + ["validate", "-s", str(specs_dir), "--tests", str(tests_dir)],
        capture_output=True,
        text=True,
    )


def _write_spec(specs_dir, filename, content):
    """Write a spec file, creating parent directories as needed."""
    path = Path(specs_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_citing_test(tests_dir, spec_item, spec_filename):
    """Write a minimal Python test file that cites the given spec item."""
    (Path(tests_dir) / "test_cite.py").write_text(
        f"def test_item():\n"
        f'    """\n'
        f"    Spec: {spec_item} [{spec_filename}]\n"
        f'    """\n'
        f"    pass\n",
        encoding="utf-8",
    )


class TestSpecItemRecognition:

    def test_dash_space_lines_are_spec_items(self, tmp_path):
        """
        Spec: A spec item is any line that starts with "- " in a .md file located anywhere under the specd `specs` directory [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", "# A\n\n- the item\n")
        _write_citing_test(tests_dir, "the item", "a.md")

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0

    def test_other_lines_are_not_spec_items(self, tmp_path):
        """
        Spec: A spec item is any line that starts with "- " in a .md file located anywhere under the specd `specs` directory [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        # Heading, paragraph text, and asterisk bullet — none start with "- "
        _write_spec(
            specs_dir,
            "a.md",
            "# A Title\n\nSome intro text.\n\n* asterisk bullet\n",
        )

        # No tests: if any lines were treated as spec items, there would be
        # uncited spec items and exit code would be 1
        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0

    def test_spec_item_in_html_comment_excluded(self, tmp_path):
        """
        Spec: A line item in the form of a spec item but inside a comment delineated by `<!-- -->` is not a spec item [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        # One real item, one inside an HTML comment
        _write_spec(
            specs_dir,
            "a.md",
            "# A\n\n- real item\n\n<!--\n- commented item\n-->\n",
        )

        # Cite only the real item; if the commented line were a spec item
        # it would show as uncited and exit code would be 1
        _write_citing_test(tests_dir, "real item", "a.md")

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0

    def test_spec_discovery_is_recursive(self, tmp_path):
        """
        Spec: A spec item is any line that starts with "- " in a .md file located anywhere under the specd `specs` directory [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        # Spec file nested in a subdirectory
        _write_spec(specs_dir, "sub/deep.md", "# Deep\n\n- deep item\n")
        _write_citing_test(tests_dir, "deep item", "deep.md")

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0
