"""
Tests for validate command CLI behavior: subcommand, exit codes, and
directory resolution options.
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


def _write_compliant_workspace(specs_dir, tests_dir):
    """Populate specs and tests dirs with a minimal compliant fixture."""
    (Path(specs_dir) / "a.md").write_text(
        "# A\n\n- item one\n", encoding="utf-8"
    )
    (Path(tests_dir) / "test_a.py").write_text(
        'def test_one():\n'
        '    """\n'
        '    Spec: item one [a.md]\n'
        '    """\n'
        '    pass\n',
        encoding="utf-8",
    )


class TestValidateSubcommand:

    def test_validate_is_valid_subcommand(self, tmp_path):
        """
        Spec: `validate` is a valid positional argument to the `specd` command line entrypoint [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()
        _write_compliant_workspace(specs_dir, tests_dir)

        result = _run("validate", "-s", str(specs_dir), "--tests", str(tests_dir))
        # If validate were not a valid subcommand, we'd get a usage error
        assert "invalid" not in result.stdout.lower()
        assert "unrecognized" not in result.stderr.lower()

    def test_report_is_printed(self, tmp_path):
        """
        Spec: When the user calls `validate`, a report is printed showing the results of spec-test matching [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()
        _write_compliant_workspace(specs_dir, tests_dir)

        result = _run("validate", "-s", str(specs_dir), "--tests", str(tests_dir))
        assert "=== Spec Compliance Report ===" in result.stdout


class TestExitCodes:

    def test_exit_code_zero_on_full_compliance(self, tmp_path):
        """
        Spec: If there are no tests without specs, specs without tests, or phantom citations, the exit code is 0 [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()
        _write_compliant_workspace(specs_dir, tests_dir)

        result = _run("validate", "-s", str(specs_dir), "--tests", str(tests_dir))
        assert result.returncode == 0

    def test_exit_code_one_on_tests_without_specs(self, tmp_path):
        """
        Spec: If there are any tests without specs, specs without tests, or phantom citations, the exit code is 1 [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        (specs_dir / "a.md").write_text("# A\n\n- item one\n", encoding="utf-8")
        (tests_dir / "test_a.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    """\n'
            '    pass\n'
            'def test_uncited():\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run("validate", "-s", str(specs_dir), "--tests", str(tests_dir))
        assert result.returncode == 1

    def test_exit_code_one_on_specs_without_tests(self, tmp_path):
        """
        Spec: If there are any tests without specs, specs without tests, or phantom citations, the exit code is 1 [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        (specs_dir / "a.md").write_text(
            "# A\n\n- item one\n- uncited item\n", encoding="utf-8"
        )
        (tests_dir / "test_a.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run("validate", "-s", str(specs_dir), "--tests", str(tests_dir))
        assert result.returncode == 1

    def test_exit_code_one_on_phantom_citations(self, tmp_path):
        """
        Spec: If there are any tests without specs, specs without tests, or phantom citations, the exit code is 1 [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        (specs_dir / "a.md").write_text("# A\n\n- item one\n", encoding="utf-8")
        (tests_dir / "test_a.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    Spec: nonexistent item [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run("validate", "-s", str(specs_dir), "--tests", str(tests_dir))
        assert result.returncode == 1


class TestDirectoryOptions:

    def test_specs_option_overrides_discovery_location(self, tmp_path):
        """
        Spec: if `validate` is called with the `-s` or `--specs` options, specs are discovered only at the supplied location [validate.md]
        """
        custom_specs = tmp_path / "custom_specs"
        tests_dir = tmp_path / "tests"
        custom_specs.mkdir()
        tests_dir.mkdir()

        (custom_specs / "a.md").write_text("# A\n\n- item one\n", encoding="utf-8")
        (tests_dir / "test_a.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run("validate", "-s", str(custom_specs), "--tests", str(tests_dir))
        assert result.returncode == 0

    def test_tests_option_overrides_discovery_location(self, tmp_path):
        """
        Spec: if `validate` is called with the `--tests` option, tests are discovered only at the supplied location [validate.md]
        """
        specs_dir = tmp_path / "specs"
        custom_tests = tmp_path / "custom_tests"
        specs_dir.mkdir()
        custom_tests.mkdir()

        (specs_dir / "a.md").write_text("# A\n\n- item one\n", encoding="utf-8")
        (custom_tests / "test_a.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run("validate", "-s", str(specs_dir), "--tests", str(custom_tests))
        assert result.returncode == 0

    def test_default_specs_dir_used_by_default(self, tmp_path):
        """
        Spec: If the specd `specs` directory is not configured with a pyproject.toml and the `-s` or `--specs` options are not used, the specs are discovered in `specs/` under the cwd [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        (specs_dir / "a.md").write_text("# A\n\n- item one\n", encoding="utf-8")
        (tests_dir / "test_a.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        # Run from tmp_path with no -s or --tests; no pyproject.toml present
        result = _run("validate", cwd=tmp_path)
        assert result.returncode == 0

    def test_default_tests_dir_used_by_default(self, tmp_path):
        """
        Spec: If the specd `tests` directory is not configured with a pyproject.toml and the `--tests` options is not used, the tests are discovered in `tests/` under the cwd [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        (specs_dir / "a.md").write_text("# A\n\n- item one\n", encoding="utf-8")
        (tests_dir / "test_a.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        # Run from tmp_path with no -s or --tests; no pyproject.toml present
        result = _run("validate", cwd=tmp_path)
        assert result.returncode == 0

    def test_pyproject_specs_dir_used(self, tmp_path):
        """
        Spec: If the specd `specs` directory is configured with a pyproject.toml, that is the directory in which specs are discovered [validate.md]
        """
        configured_specs = tmp_path / "my_specs"
        tests_dir = tmp_path / "tests"
        configured_specs.mkdir()
        tests_dir.mkdir()

        (tmp_path / "pyproject.toml").write_text(
            "[tool.specd]\n"
            f'specs = "my_specs"\n',
            encoding="utf-8",
        )
        (configured_specs / "a.md").write_text(
            "# A\n\n- item one\n", encoding="utf-8"
        )
        (tests_dir / "test_a.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run("validate", "--tests", str(tests_dir), cwd=tmp_path)
        assert result.returncode == 0

    def test_pyproject_tests_dir_used(self, tmp_path):
        """
        Spec: If the specd `tests` directory is configured with a pyproject.toml, that is the directory in which tests are discovered [validate.md]
        """
        specs_dir = tmp_path / "specs"
        configured_tests = tmp_path / "my_tests"
        specs_dir.mkdir()
        configured_tests.mkdir()

        (tmp_path / "pyproject.toml").write_text(
            "[tool.specd]\n"
            f'tests = "my_tests"\n',
            encoding="utf-8",
        )
        (specs_dir / "a.md").write_text(
            "# A\n\n- item one\n", encoding="utf-8"
        )
        (configured_tests / "test_a.py").write_text(
            'def test_one():\n'
            '    """\n'
            '    Spec: item one [a.md]\n'
            '    """\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run("validate", "-s", str(specs_dir), cwd=tmp_path)
        assert result.returncode == 0
