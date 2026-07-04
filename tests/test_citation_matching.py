"""
Tests for test-to-spec citation format and matching.
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


class TestCitationFormat:

    def test_valid_citation_form_matches(self, tmp_path):
        """
        Spec: A spec is only cited by a test if the citation is in the form `Spec: <entire verbatim spec line item excluding "- "> [<spec file name>]` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        (specs_dir / "a.md").write_text("# A\n\n- item one\n", encoding="utf-8")
        (tests_dir / "test_foo.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0

    def test_citation_wrong_format_not_matched(self, tmp_path):
        """
        Spec: A spec is only cited by a test if the citation is in the form `Spec: <entire verbatim spec line item excluding "- "> [<spec file name>]` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        (specs_dir / "a.md").write_text("# A\n\n- item one\n", encoding="utf-8")
        (tests_dir / "test_foo.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec item one in a.md\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 1

    def test_backslash_n_in_spec_matches_citation(self, tmp_path):
        r"""
        Spec: Representations of newlines in specs as `\\n` will match up with the same in test-to-spec references [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        # Spec file with \\n (two backslashes + n) on disk
        (specs_dir / "a.md").write_bytes(
            b"# A\n\n- output ends with \\\\n\n"
        )

        # Test file citing the same text with \\n (two backslashes + n) on disk
        (tests_dir / "test_foo.py").write_bytes(
            b"def test_one():\n"
            b"    \"\"\"\n"
            b"    Spec: output ends with \\\\n [a.md]\n"
            b"    \"\"\"\n"
            b"    pass\n"
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0

    def test_mismatched_backslash_n_does_not_match(self, tmp_path):
        r"""
        Spec: Representations of newlines in specs as `\\n` will match up with the same in test-to-spec references [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        # Spec file with \\n (two backslashes + n) on disk
        (specs_dir / "a.md").write_bytes(
            b"# A\n\n- output ends with \\\\n\n"
        )

        # Test file using \n (one backslash + n) — should not match
        (tests_dir / "test_foo.py").write_bytes(
            b"def test_one():\n"
            b"    \"\"\"\n"
            b"    Spec: output ends with \\n [a.md]\n"
            b"    \"\"\"\n"
            b"    pass\n"
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 1
