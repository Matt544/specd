"""
Tests for the `specd policies` command.

Covers:
- The POLICIES manifest dict (keys, filenames, existence in package data)
- specd policies --list
- specd policies --copy (all, one, to target)
- Overwrite protection and --force
- Error conditions: --only without --copy, invalid key, missing target dir
"""

import importlib.resources
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[1]

EXPECTED_POLICIES = {
    "spec-writing": "spec-writing-policy.md",
    "test-writing": "test-writing-policy.md",
    "spec-implementation": "spec-implementation-policy.md",
}


def _run_specd(*args, cwd=None):
    """Run specd as a subprocess and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "specd.cli", *args],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else str(PACKAGE_ROOT),
    )


# -- Manifest -----------------------------------------------------------------


class TestPoliciesManifest:
    """Unit tests for the POLICIES manifest dict.

    Import path matches the implementation module; update if it moves.
    """

    def _get_policies(self):
        from specd._policies import POLICIES
        return POLICIES

    def test_manifest_has_exactly_three_keys(self):
        """POLICIES contains exactly the three expected keys."""
        POLICIES = self._get_policies()
        assert set(POLICIES.keys()) == set(EXPECTED_POLICIES.keys())

    def test_manifest_values_are_md_filenames(self):
        """Each value in POLICIES is a string ending in .md."""
        POLICIES = self._get_policies()
        for filename in POLICIES.values():
            assert isinstance(filename, str)
            assert filename.endswith(".md")

    def test_manifest_matches_expected_mapping(self):
        """Each key maps to its expected filename."""
        POLICIES = self._get_policies()
        assert POLICIES == EXPECTED_POLICIES

    def test_policy_files_exist_in_package_data(self):
        """Every filename in POLICIES resolves to a real file in the
        package's policies/ data directory."""
        POLICIES = self._get_policies()
        policies_dir = importlib.resources.files("specd") / "policies"
        for filename in POLICIES.values():
            assert (policies_dir / filename).is_file(), (
                f"{filename} not found in package data"
            )


# -- --list -------------------------------------------------------------------


class TestPoliciesList:

    def test_list_exits_zero(self):
        """specd policies --list exits with code 0."""
        result = _run_specd("policies", "--list")
        assert result.returncode == 0

    def test_list_shows_all_keys(self):
        """specd policies --list outputs all three policy keys."""
        result = _run_specd("policies", "--list")
        for key in EXPECTED_POLICIES:
            assert key in result.stdout

    def test_list_shows_all_filenames(self):
        """specd policies --list outputs all three policy filenames."""
        result = _run_specd("policies", "--list")
        for filename in EXPECTED_POLICIES.values():
            assert filename in result.stdout

    def test_list_shows_key_and_filename_on_same_line(self):
        """Each key and its corresponding filename appear on the same line."""
        result = _run_specd("policies", "--list")
        for key, filename in EXPECTED_POLICIES.items():
            matching = [
                line for line in result.stdout.splitlines()
                if key in line and filename in line
            ]
            assert matching, (
                f"No line in --list output contains both '{key}' and '{filename}'"
            )


# -- --copy (all) -------------------------------------------------------------


class TestPoliciesCopyAll:

    def test_copy_all_exits_zero(self, tmp_path):
        """specd policies --copy exits 0 when no conflicts exist."""
        result = _run_specd("policies", "--copy", cwd=tmp_path)
        assert result.returncode == 0

    def test_copy_all_creates_all_files_in_cwd(self, tmp_path):
        """specd policies --copy (no -t) creates all policy files in cwd."""
        _run_specd("policies", "--copy", cwd=tmp_path)
        for filename in EXPECTED_POLICIES.values():
            assert (tmp_path / filename).exists(), (
                f"{filename} was not created in cwd"
            )

    def test_copy_all_with_target_creates_files_in_target(self, tmp_path):
        """specd policies --copy -t dir/ creates all policy files in dir/."""
        target = tmp_path / "dest"
        target.mkdir()
        _run_specd("policies", "--copy", "-t", str(target))
        for filename in EXPECTED_POLICIES.values():
            assert (target / filename).exists(), (
                f"{filename} was not created in target"
            )

    def test_copy_all_with_target_does_not_write_to_cwd(self, tmp_path):
        """specd policies --copy -t dir/ does not create files in cwd."""
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        target = tmp_path / "dest"
        target.mkdir()
        _run_specd("policies", "--copy", "-t", str(target), cwd=cwd)
        for filename in EXPECTED_POLICIES.values():
            assert not (cwd / filename).exists(), (
                f"{filename} was unexpectedly created in cwd"
            )


# -- --copy --only ------------------------------------------------------------


class TestPoliciesCopyOne:

    def test_copy_only_spec_writing_creates_that_file(self, tmp_path):
        """--copy --only spec-writing creates spec-writing-policy.md."""
        _run_specd("policies", "--copy", "--only", "spec-writing", cwd=tmp_path)
        assert (tmp_path / "spec-writing-policy.md").exists()

    def test_copy_only_does_not_create_other_files(self, tmp_path):
        """--copy --only spec-writing does not create the other two files."""
        _run_specd("policies", "--copy", "--only", "spec-writing", cwd=tmp_path)
        assert not (tmp_path / "test-writing-policy.md").exists()
        assert not (tmp_path / "spec-implementation-policy.md").exists()

    def test_copy_only_test_writing(self, tmp_path):
        """--copy --only test-writing creates test-writing-policy.md."""
        _run_specd("policies", "--copy", "--only", "test-writing", cwd=tmp_path)
        assert (tmp_path / "test-writing-policy.md").exists()

    def test_copy_only_spec_implementation(self, tmp_path):
        """--copy --only spec-implementation creates spec-implementation-policy.md."""
        _run_specd("policies", "--copy", "--only", "spec-implementation", cwd=tmp_path)
        assert (tmp_path / "spec-implementation-policy.md").exists()

    def test_copy_only_with_target(self, tmp_path):
        """--copy --only spec-writing -t dir/ creates the file in dir/."""
        target = tmp_path / "dest"
        target.mkdir()
        _run_specd(
            "policies", "--copy", "--only", "spec-writing", "-t", str(target),
        )
        assert (target / "spec-writing-policy.md").exists()

    def test_copy_only_exits_zero(self, tmp_path):
        """--copy --only <valid key> exits 0."""
        result = _run_specd(
            "policies", "--copy", "--only", "test-writing", cwd=tmp_path,
        )
        assert result.returncode == 0


# -- Overwrite protection and --force -----------------------------------------


class TestPoliciesCopyConflicts:

    def test_refuses_when_one_file_exists(self, tmp_path):
        """With one existing file and no --force, exits nonzero."""
        (tmp_path / "spec-writing-policy.md").write_text(
            "existing", encoding="utf-8",
        )
        result = _run_specd("policies", "--copy", cwd=tmp_path)
        assert result.returncode != 0

    def test_reports_conflict_in_output(self, tmp_path):
        """The conflicting filename appears in the output when refused."""
        (tmp_path / "spec-writing-policy.md").write_text(
            "existing", encoding="utf-8",
        )
        result = _run_specd("policies", "--copy", cwd=tmp_path)
        assert "spec-writing-policy.md" in result.stdout

    def test_reports_all_conflicts(self, tmp_path):
        """All conflicting filenames are reported when multiple exist."""
        (tmp_path / "spec-writing-policy.md").write_text("x", encoding="utf-8")
        (tmp_path / "test-writing-policy.md").write_text("x", encoding="utf-8")
        result = _run_specd("policies", "--copy", cwd=tmp_path)
        assert "spec-writing-policy.md" in result.stdout
        assert "test-writing-policy.md" in result.stdout

    def test_no_files_copied_when_any_conflict(self, tmp_path):
        """When one file conflicts, non-conflicting files are also not copied."""
        (tmp_path / "spec-writing-policy.md").write_text("x", encoding="utf-8")
        _run_specd("policies", "--copy", cwd=tmp_path)
        # The other two files should not have been created.
        assert not (tmp_path / "test-writing-policy.md").exists()
        assert not (tmp_path / "spec-implementation-policy.md").exists()

    def test_existing_file_not_overwritten_without_force(self, tmp_path):
        """The content of an existing file is unchanged when refused."""
        target_file = tmp_path / "spec-writing-policy.md"
        target_file.write_text("do not overwrite", encoding="utf-8")
        _run_specd("policies", "--copy", cwd=tmp_path)
        assert target_file.read_text(encoding="utf-8") == "do not overwrite"

    def test_force_overwrites_existing_file(self, tmp_path):
        """--force replaces an existing file with the policy content."""
        target_file = tmp_path / "spec-writing-policy.md"
        target_file.write_text("old content", encoding="utf-8")
        result = _run_specd("policies", "--copy", "--force", cwd=tmp_path)
        assert result.returncode == 0
        assert target_file.read_text(encoding="utf-8") != "old content"

    def test_force_copies_all_when_multiple_conflicts(self, tmp_path):
        """--force copies all files even when multiple conflicts exist."""
        (tmp_path / "spec-writing-policy.md").write_text("x", encoding="utf-8")
        (tmp_path / "test-writing-policy.md").write_text("x", encoding="utf-8")
        result = _run_specd("policies", "--copy", "--force", cwd=tmp_path)
        assert result.returncode == 0
        for filename in EXPECTED_POLICIES.values():
            assert (tmp_path / filename).exists()

    def test_force_with_only_overwrites_one_file(self, tmp_path):
        """--copy --only <key> --force overwrites just that one file."""
        target_file = tmp_path / "spec-writing-policy.md"
        target_file.write_text("old", encoding="utf-8")
        result = _run_specd(
            "policies", "--copy", "--only", "spec-writing", "--force", cwd=tmp_path,
        )
        assert result.returncode == 0
        assert target_file.read_text(encoding="utf-8") != "old"


# -- Bare subcommand ----------------------------------------------------------


class TestPoliciesBare:

    def test_bare_policies_exits_zero(self):
        """specd policies (no flags) exits 0."""
        result = _run_specd("policies")
        assert result.returncode == 0

    def test_bare_policies_prints_help(self):
        """specd policies (no flags) prints help mentioning its flags."""
        result = _run_specd("policies")
        output = result.stdout + result.stderr
        assert "--list" in output
        assert "--copy" in output


# -- Error conditions ---------------------------------------------------------


class TestPoliciesErrors:

    def test_only_without_copy_exits_nonzero(self):
        """--only without --copy exits nonzero."""
        result = _run_specd("policies", "--only", "spec-writing")
        assert result.returncode != 0

    def test_only_without_copy_prints_informative_message(self):
        """--only without --copy prints a message explaining --copy is required."""
        result = _run_specd("policies", "--only", "spec-writing")
        output = result.stdout + result.stderr
        assert "--copy" in output

    def test_copy_only_invalid_key_exits_nonzero(self, tmp_path):
        """--copy --only with an unrecognised key exits nonzero."""
        result = _run_specd(
            "policies", "--copy", "--only", "nonexistent-key", cwd=tmp_path,
        )
        assert result.returncode != 0

    def test_copy_only_invalid_key_indicates_key_is_invalid(self, tmp_path):
        """Output for an invalid key tells the user the key is not recognised."""
        result = _run_specd(
            "policies", "--copy", "--only", "nonexistent-key", cwd=tmp_path,
        )
        output = result.stdout + result.stderr
        assert "nonexistent-key" in output

    def test_copy_only_invalid_key_lists_valid_keys(self, tmp_path):
        """Output for an invalid key lists the valid keys."""
        result = _run_specd(
            "policies", "--copy", "--only", "nonexistent-key", cwd=tmp_path,
        )
        output = result.stdout + result.stderr
        for key in EXPECTED_POLICIES:
            assert key in output

    def test_copy_nonexistent_target_exits_nonzero(self):
        """--copy -t pointing to a non-existent directory exits nonzero."""
        result = _run_specd(
            "policies", "--copy", "-t", "/nonexistent/path/that/does/not/exist",
        )
        assert result.returncode != 0

    def test_copy_nonexistent_target_tells_user_to_create_dir(self):
        """Output for a missing -t directory tells the user to create it."""
        result = _run_specd(
            "policies", "--copy", "-t", "/nonexistent/path/that/does/not/exist",
        )
        output = result.stdout + result.stderr
        assert "create" in output.lower()
