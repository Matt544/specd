"""
Tests for the format and content of the validate report output.
"""

import re
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


def _write_spec(specs_dir, filename, items):
    """Write a spec file with the given list of item strings."""
    content = "# Spec\n\n" + "".join(f"- {item}\n" for item in items)
    (Path(specs_dir) / filename).write_text(content, encoding="utf-8")


def _write_test(tests_dir, filename, functions):
    """
    Write a Python test file.

    functions: list of (name, citations) where citations is a list of
    "item [file.md]" strings, or an empty list for no citations.
    """
    lines = []
    for name, citations in functions:
        lines.append(f"def {name}():")
        if citations:
            lines.append('    """')
            for citation in citations:
                lines.append(f"    Spec: {citation}")
            lines.append('    """')
        lines.append("    pass")
        lines.append("")
    (Path(tests_dir) / filename).write_text("\n".join(lines), encoding="utf-8")


class TestMainTitle:

    def test_report_starts_with_main_title(self, tmp_path):
        """
        Spec: The report starts with the main title "\\n=== Spec Compliance Report ===\\n\\n" [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [("test_one", ["item one [a.md]"])])

        result = _run_validate(specs_dir, tests_dir)
        assert result.stdout.startswith("\n=== Spec Compliance Report ===\n\n")


class TestSectionOrder:

    def test_section_order_fixed(self, tmp_path):
        """
        Spec: The report sections appear in this fixed order, each only if applicable: tests without specs, specs without tests, phantom citations, summary [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        # item_a has no test (uncited spec), test_uncited has no citation,
        # test_phantom has a phantom citation
        _write_spec(specs_dir, "a.md", ["item_a", "item_b"])
        _write_test(
            tests_dir,
            "test_a.py",
            [
                ("test_uncited", []),
                ("test_phantom", ["nonexistent item [nonexistent.md]"]),
                ("test_valid", ["item_b [a.md]"]),
            ],
        )

        result = _run_validate(specs_dir, tests_dir)
        output = result.stdout

        pos_tests_without = output.find("TESTS WITHOUT VALID SPEC ITEMS")
        pos_specs_without = output.find("SPEC ITEMS NOT CITED BY TESTS")
        pos_phantoms = output.find("PHANTOM CITATIONS")
        pos_summary = output.find("=== Summary ===")

        assert pos_tests_without < pos_specs_without
        assert pos_specs_without < pos_phantoms
        assert pos_phantoms < pos_summary


class TestTestsWithoutSpecsSection:

    def test_tests_without_specs_heading_format(self, tmp_path):
        """
        Spec: The tests without specs section has a heading: `TESTS WITHOUT VALID SPEC ITEMS (<num>)\\n\\n` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(
            tests_dir,
            "test_a.py",
            [("test_uncited", []), ("test_also_uncited", [])],
        )

        result = _run_validate(specs_dir, tests_dir)
        assert "TESTS WITHOUT VALID SPEC ITEMS (2)" in result.stdout

    def test_tests_without_specs_items_numbered_sequentially(self, tmp_path):
        """
        Spec: The list of tests without valid specs is number sequentially [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(
            tests_dir,
            "test_a.py",
            [("test_first", []), ("test_second", []), ("test_third", [])],
        )

        result = _run_validate(specs_dir, tests_dir)
        assert "1." in result.stdout
        assert "2." in result.stdout
        assert "3." in result.stdout

    def test_tests_without_specs_section_skipped_when_empty(self, tmp_path):
        """
        Spec: If there are no tests without valid spec citations, the report skips that section entirely [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [("test_one", ["item one [a.md]"])])

        result = _run_validate(specs_dir, tests_dir)
        assert "TESTS WITHOUT VALID SPEC ITEMS" not in result.stdout

    def test_tests_without_specs_section_ends_with_double_newline(self, tmp_path):
        """
        Spec: The tests without specs section ends with `\\n\\n` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [("test_uncited", [])])

        result = _run_validate(specs_dir, tests_dir)
        # The section heading for the next section (or summary) is preceded
        # by the double newline ending of the tests-without-specs section
        output = result.stdout
        heading_end = output.find("TESTS WITHOUT VALID SPEC ITEMS")
        section_start = output.find("TESTS WITHOUT VALID SPEC ITEMS")
        # Find where the section content ends by locating the next section heading
        next_heading = output.find("SPEC ITEMS NOT CITED BY TESTS", section_start)
        if next_heading == -1:
            next_heading = output.find("PHANTOM CITATIONS", section_start)
        if next_heading == -1:
            next_heading = output.find("=== Summary ===", section_start)
        section_content = output[section_start:next_heading]
        assert section_content.endswith("\n\n")


class TestSpecsWithoutTestsSection:

    def test_specs_without_tests_heading_format(self, tmp_path):
        """
        Spec: The specs without tests section has a heading: `SPEC ITEMS NOT CITED BY TESTS (<num>)\\n\\n` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one", "item two"])
        _write_test(tests_dir, "test_a.py", [])

        result = _run_validate(specs_dir, tests_dir)
        assert "SPEC ITEMS NOT CITED BY TESTS (2)" in result.stdout

    def test_specs_without_tests_item_format(self, tmp_path):
        """
        Spec: Each spec line item that is not cited by a test is shown on its own line as: `<n>. <spec file name>: <entire verbatim spec line item excluding "- ">` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [])

        result = _run_validate(specs_dir, tests_dir)
        assert "a.md" in result.stdout
        assert "item one" in result.stdout
        # The format includes the filename and item on the same entry line
        assert re.search(r"\d+\.\s+a\.md.*item one", result.stdout)

    def test_specs_without_tests_list_contains_all_and_only_uncited(self, tmp_path):
        """
        Spec: The specs without tests heading is followed by a list of all spec items that are not cited by tests [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item cited", "item uncited"])
        _write_test(
            tests_dir,
            "test_a.py",
            [("test_one", ["item cited [a.md]"])],
        )

        result = _run_validate(specs_dir, tests_dir)
        output = result.stdout
        section_start = output.find("SPEC ITEMS NOT CITED BY TESTS")
        assert section_start != -1
        next_heading = output.find("=== Summary ===", section_start)
        section_content = output[section_start:next_heading]
        assert "item uncited" in section_content
        assert "item cited" not in section_content

    def test_specs_without_tests_items_numbered_sequentially(self, tmp_path):
        """
        Spec: The list of uncited specs is number sequentially [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one", "item two", "item three"])
        _write_test(tests_dir, "test_a.py", [])

        result = _run_validate(specs_dir, tests_dir)
        assert "1." in result.stdout
        assert "2." in result.stdout
        assert "3." in result.stdout

    def test_specs_without_tests_section_skipped_when_empty(self, tmp_path):
        """
        Spec: If there are no uncited specs, the report skips that section entirely [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [("test_one", ["item one [a.md]"])])

        result = _run_validate(specs_dir, tests_dir)
        assert "SPEC ITEMS NOT CITED BY TESTS" not in result.stdout

    def test_specs_without_tests_section_ends_with_double_newline(self, tmp_path):
        """
        Spec: The specs without tests section ends with `\\n\\n` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [])

        result = _run_validate(specs_dir, tests_dir)
        output = result.stdout
        section_start = output.find("SPEC ITEMS NOT CITED BY TESTS")
        next_heading = output.find("PHANTOM CITATIONS", section_start)
        if next_heading == -1:
            next_heading = output.find("=== Summary ===", section_start)
        section_content = output[section_start:next_heading]
        assert section_content.endswith("\n\n")


class TestPhantomCitationsSection:

    def test_phantom_citations_heading_format(self, tmp_path):
        """
        Spec: The phantom citations section has a heading: `PHANTOM CITATIONS (<num>)\\n\\n` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(
            tests_dir,
            "test_a.py",
            [
                ("test_one", ["item one [a.md]"]),
                ("test_phantom", ["wrong item [a.md]"]),
            ],
        )

        result = _run_validate(specs_dir, tests_dir)
        assert "PHANTOM CITATIONS (1)" in result.stdout

    def test_phantom_citation_entry_format(self, tmp_path):
        """
        Spec: Each phantom citation is shown on its own line as: `<n>. <path from tests/ with `::` for internal resource delimiters>\\n   - <the verbatim phantom spec item> [<spec file name>]\\n   - <reason>` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(
            tests_dir,
            "test_a.py",
            [
                ("test_one", ["item one [a.md]"]),
                ("test_phantom", ["wrong item [a.md]"]),
            ],
        )

        result = _run_validate(specs_dir, tests_dir)
        output = result.stdout
        # Entry starts with a number and the test path
        assert re.search(r"\d+\.\s+.*test_phantom", output)
        # Followed by indented citation line and reason line
        assert "wrong item" in output
        assert "spec item not found in file" in output

    def test_phantom_reason_spec_file_not_found(self, tmp_path):
        """
        Spec: The `reason` for inclusion of a test-to-spec reference in the phantom citations section will be either `spec file not found` or `spec item not found in file` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(
            tests_dir,
            "test_a.py",
            [
                ("test_one", ["item one [a.md]"]),
                ("test_phantom", ["item one [nonexistent.md]"]),
            ],
        )

        result = _run_validate(specs_dir, tests_dir)
        assert "spec file not found" in result.stdout

    def test_phantom_reason_spec_item_not_found(self, tmp_path):
        """
        Spec: The `reason` for inclusion of a test-to-spec reference in the phantom citations section will be either `spec file not found` or `spec item not found in file` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(
            tests_dir,
            "test_a.py",
            [
                ("test_one", ["item one [a.md]"]),
                ("test_phantom", ["no such item [a.md]"]),
            ],
        )

        result = _run_validate(specs_dir, tests_dir)
        assert "spec item not found in file" in result.stdout

    def test_phantom_citations_items_numbered_sequentially(self, tmp_path):
        """
        Spec: The list of phantom citations is number sequentially [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(
            tests_dir,
            "test_a.py",
            [
                ("test_one", ["item one [a.md]"]),
                ("test_phantom_a", ["wrong a [a.md]"]),
                ("test_phantom_b", ["wrong b [a.md]"]),
                ("test_phantom_c", ["wrong c [a.md]"]),
            ],
        )

        result = _run_validate(specs_dir, tests_dir)
        assert "1." in result.stdout
        assert "2." in result.stdout
        assert "3." in result.stdout

    def test_phantom_citations_section_skipped_when_empty(self, tmp_path):
        """
        Spec: If there are no phantom citations, the report skips that section entirely [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [("test_one", ["item one [a.md]"])])

        result = _run_validate(specs_dir, tests_dir)
        assert "PHANTOM CITATIONS" not in result.stdout

    def test_phantom_citations_section_ends_with_double_newline(self, tmp_path):
        """
        Spec: The phantom citations section ends with `\\n\\n` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(
            tests_dir,
            "test_a.py",
            [
                ("test_one", ["item one [a.md]"]),
                ("test_phantom", ["wrong item [a.md]"]),
            ],
        )

        result = _run_validate(specs_dir, tests_dir)
        output = result.stdout
        section_start = output.find("PHANTOM CITATIONS")
        next_heading = output.find("=== Summary ===", section_start)
        section_content = output[section_start:next_heading]
        assert section_content.endswith("\n\n")

    def test_multiple_phantoms_for_same_test_each_listed_separately(self, tmp_path):
        """
        Spec: The list of phantom citations is number sequentially [validate.md]
        Spec: Each phantom citation is shown on its own line as: `<n>. <path from tests/ with `::` for internal resource delimiters>\\n   - <the verbatim phantom spec item> [<spec file name>]\\n   - <reason>` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        # One test with two phantom citations
        _write_test(
            tests_dir,
            "test_a.py",
            [
                ("test_one", ["item one [a.md]"]),
                ("test_two_phantoms", ["wrong one [a.md]", "wrong two [a.md]"]),
            ],
        )

        result = _run_validate(specs_dir, tests_dir)
        assert "PHANTOM CITATIONS (2)" in result.stdout

    def test_phantom_section_excludes_valid_citations(self, tmp_path):
        """
        Spec: a test fails to correctly cite a spec if it contains a reference in the form `Spec: <purported_spec> [<purported_file>]` but content of either the `purported_spec` or the file name does not match to an actual spec item or spec file [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(
            tests_dir,
            "test_a.py",
            [
                ("test_valid", ["item one [a.md]"]),
                ("test_phantom", ["wrong item [a.md]"]),
            ],
        )

        result = _run_validate(specs_dir, tests_dir)
        output = result.stdout
        phantom_start = output.find("PHANTOM CITATIONS")
        assert phantom_start != -1
        phantom_section = output[phantom_start:]
        assert "test_phantom" in phantom_section
        assert "test_valid" not in phantom_section

    def test_test_in_both_sections_when_only_phantom_citations(self, tmp_path):
        """
        Spec: The tests without specs heading is followed by a list of all functions or methods that do not have valid spec citations [validate.md]
        Spec: The phantom citations heading is followed by a list of all test-to-spec references that do not correctly cite a spec [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        # test_only_phantom has only a phantom citation — no valid citations
        # It should appear in both TESTS WITHOUT VALID SPEC ITEMS and PHANTOM CITATIONS
        _write_test(
            tests_dir,
            "test_a.py",
            [
                ("test_one", ["item one [a.md]"]),
                ("test_only_phantom", ["wrong item [a.md]"]),
            ],
        )

        result = _run_validate(specs_dir, tests_dir)
        output = result.stdout
        assert "TESTS WITHOUT VALID SPEC ITEMS" in output
        assert "PHANTOM CITATIONS" in output
        # test_only_phantom appears in both sections
        tests_without_section = output[
            output.find("TESTS WITHOUT VALID SPEC ITEMS"):
            output.find("SPEC ITEMS NOT CITED BY TESTS")
            if "SPEC ITEMS NOT CITED BY TESTS" in output
            else output.find("PHANTOM CITATIONS")
        ]
        assert "test_only_phantom" in tests_without_section
        phantom_section = output[output.find("PHANTOM CITATIONS"):]
        assert "test_only_phantom" in phantom_section


class TestSummary:

    def test_summary_always_present(self, tmp_path):
        """
        Spec: The summary report is never skipped [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        # Full compliance — no violations
        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [("test_one", ["item one [a.md]"])])

        result = _run_validate(specs_dir, tests_dir)
        assert "=== Summary ===" in result.stdout

    def test_summary_heading(self, tmp_path):
        """
        Spec: The summary has a heading: `=== Summary ===\\n\\n` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [("test_one", ["item one [a.md]"])])

        result = _run_validate(specs_dir, tests_dir)
        assert "=== Summary ===\n\n" in result.stdout

    def test_summary_content_follows_heading(self, tmp_path):
        """
        Spec: The summary heading is followed by a summary report [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [("test_one", ["item one [a.md]"])])

        result = _run_validate(specs_dir, tests_dir)
        output = result.stdout
        heading_pos = output.find("=== Summary ===\n\n")
        assert heading_pos != -1
        after_heading = output[heading_pos + len("=== Summary ===\n\n"):]
        assert re.search(r"Tests checked:\s+\d+", after_heading)

    def test_summary_five_lines_with_correct_counts(self, tmp_path):
        """
        Spec: The first summary line is: `Tests checked:   <n>` [validate.md]
        Spec: The second summary line is: `Tests with valid spec items:   <n>` [validate.md]
        Spec: The third summary line is: `Tests without valid spec items:   <n>` [validate.md]
        Spec: The fourth summary line is: `Spec items without related tests:   <n>` [validate.md]
        Spec: The fifth summary line is: `Phantom citations:   <n>` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        # 3 tests total: 2 valid, 1 uncited, 1 phantom; 1 uncited spec item; 1 phantom
        _write_spec(specs_dir, "a.md", ["item one", "item two"])
        _write_test(
            tests_dir,
            "test_a.py",
            [
                ("test_valid", ["item one [a.md]"]),
                ("test_uncited", []),
                ("test_phantom", ["wrong item [a.md]"]),
            ],
        )

        result = _run_validate(specs_dir, tests_dir)
        output = result.stdout

        assert re.search(r"Tests checked:\s+3", output)
        assert re.search(r"Tests with valid spec items:\s+1", output)
        assert re.search(r"Tests without valid spec items:\s+2", output)
        assert re.search(r"Spec items without related tests:\s+1", output)
        assert re.search(r"Phantom citations:\s+1", output)

    def test_summary_number_alignment(self, tmp_path):
        """
        Spec: The first digits of the numbers of each line of the summary report represented by `<n>` line up [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [("test_one", ["item one [a.md]"])])

        result = _run_validate(specs_dir, tests_dir)
        output = result.stdout

        summary_start = output.find("=== Summary ===")
        assert summary_start != -1
        summary_text = output[summary_start:]

        label_patterns = [
            r"Tests checked:",
            r"Tests with valid spec items:",
            r"Tests without valid spec items:",
            r"Spec items without related tests:",
            r"Phantom citations:",
        ]

        # Find the column position of the first digit on each summary line
        # by scanning line by line, so positions are relative to the line start
        digit_columns = []
        for line in summary_text.splitlines():
            for pattern in label_patterns:
                match = re.match(rf"\s*{re.escape(pattern)}\s*(\d)", line)
                if match:
                    digit_columns.append(match.start(1))
                    break

        assert len(digit_columns) == 5, (
            f"Expected 5 summary lines, found {len(digit_columns)}"
        )
        assert len(set(digit_columns)) == 1, (
            f"Summary number columns not aligned: {digit_columns}"
        )

    def test_summary_report_ends_with_double_newline(self, tmp_path):
        """
        Spec: The summary report ends with `\\n\\n` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [("test_one", ["item one [a.md]"])])

        result = _run_validate(specs_dir, tests_dir)
        output = result.stdout
        summary_start = output.find("=== Summary ===\n\n")
        assert summary_start != -1
        note_marker = 'Note: "Tests checked"'
        note_pos = output.find(note_marker, summary_start)
        assert note_pos != -1, "Note line not found after summary heading"
        report_block = output[summary_start:note_pos]
        assert report_block.endswith("\n\n"), (
            f"Summary report block should end with \\n\\n before the note; "
            f"got {report_block[-10:]!r}"
        )

    def test_summary_includes_parameterization_note(self, tmp_path):
        """
        Spec: After the summary report, there is: `Note: "Tests checked" are counted by function. Parameterized test functions may run more than once in a test suite, causing the test runner's count to be higher.` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [("test_one", ["item one [a.md]"])])

        result = _run_validate(specs_dir, tests_dir)
        assert (
            'Note: "Tests checked" are counted by function. '
            "Parameterized test functions may run more than once in a test suite, "
            "causing the test runner's count to be higher."
        ) in result.stdout

    def test_summary_section_ends_with_double_newline(self, tmp_path):
        """
        Spec: The summary section ends with `\\n\\n` [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(tests_dir, "test_a.py", [("test_one", ["item one [a.md]"])])

        result = _run_validate(specs_dir, tests_dir)
        assert result.stdout.endswith("\n\n")
