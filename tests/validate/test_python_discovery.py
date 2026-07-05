"""
Tests for Python test file and function discovery in the validate command.
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


def _write_spec(specs_dir, content):
    """Write a single spec file named a.md with the given content."""
    (Path(specs_dir) / "a.md").write_text(content, encoding="utf-8")


class TestPythonTestFileDiscovery:

    def test_python_test_file_pattern(self, tmp_path):
        """
        Spec: a python test file is a file named test_*.py located anywhere under the specd `tests` directory [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n- item two\n")

        # test_valid.py — matches test_*.py, cites item one
        (tests_dir / "test_valid.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        # helper.py — does NOT match test_*.py, cites item two
        (tests_dir / "helper.py").write_text(
            'def test_two():\n'
            '    """\n'
            '    Spec: item two [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        # item two should be uncited because helper.py is not discovered
        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 1
        assert "item two" in result.stdout

    def test_python_test_file_discovery_is_recursive(self, tmp_path):
        """
        Spec: a python test file is a file named test_*.py located anywhere under the specd `tests` directory [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

        # test file nested in a subdirectory
        subdir = tests_dir / "unit"
        subdir.mkdir()
        (subdir / "test_sub.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0


class TestPythonTestFunctionDiscovery:

    def test_python_test_function_recognized(self, tmp_path):
        """
        Spec: a python test is a function or method with a name in the form `test_*` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

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

    def test_non_test_function_not_recognized(self, tmp_path):
        """
        Spec: a python test is a function or method with a name in the form `test_*` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

        # helper_one does not start with test_ — should not be discovered
        (tests_dir / "test_foo.py").write_text(
            'def helper_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 1
        assert "item one" in result.stdout

    def test_python_test_method_in_class(self, tmp_path):
        """
        Spec: a python test is a function or method with a name in the form `test_*` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

        (tests_dir / "test_foo.py").write_text(
            'class TestFoo:\n'
            '    def test_one(self):\n'
            '        """\n'
            '        Spec: item one [a.md]\n'
            '        """\n'
            '        pass\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0


class TestPythonCitationDiscovery:

    def test_python_citation_on_own_docstring_line(self, tmp_path):
        """
        Spec: python functions or methods validly cite specs by placing the references on their own lines in the docstring [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

        (tests_dir / "test_foo.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Some description.\n'
            '    Spec: item one [a.md]\n'
            '    More text.\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0

    def test_python_citation_not_on_own_line_not_valid(self, tmp_path):
        """
        Spec: python functions or methods validly cite specs by placing the references on their own lines in the docstring [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

        # Citation embedded in surrounding text on the same line — not valid
        (tests_dir / "test_foo.py").write_text(
            'def test_one():\n'
            '    """See also: Spec: item one [a.md] for details."""\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 1

    def test_test_path_uses_double_colon_delimiter(self, tmp_path):
        """
        Spec: Each function or method that does not have a valid spec citation is shown on its own line as: `<n>. <path from tests/ with `::` for internal resource delimiters>` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

        # test_uncited has no citation — should appear in report with :: delimiter
        (tests_dir / "test_foo.py").write_text(
            'def test_uncited():\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)

        # The path uses :: as the internal resource delimiter
        assert "test_foo.py::test_uncited" in result.stdout

        # The path is relative to tests_dir's parent, so it starts with "tests/"
        lines_with_test = [
            line for line in result.stdout.splitlines()
            if "test_uncited" in line
        ]
        assert lines_with_test, "test_uncited not found in output"
        for line in lines_with_test:
            assert line.lstrip(".0123456789 ").startswith("tests/"), (
                f"Path should start with 'tests/' (relative to tests_dir parent): {line!r}"
            )
