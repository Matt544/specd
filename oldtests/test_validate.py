"""
Tests for the spec/test compliance validator.
"""

from pathlib import Path

from specd.validate import (
    TestEntry,
    load_specs,
    parse_citations,
    run_validation,
    validate,
)

LIVE_SAMPLES_DIR = Path(__file__).parent / "live_samples"


def _write_spec(specs_dir, filename, items):
    """Write a spec file with the given list items."""
    content = "# Test Spec\n\n" + "\n".join(f"- {item}" for item in items) + "\n"
    (specs_dir / filename).write_text(content, encoding="utf-8")


def _write_test(tests_dir, filename, functions):
    """
    Write a test file with the given function definitions.

    functions: list of (name, docstring) tuples.
    """
    lines = []
    for name, docstring in functions:
        lines.append(f"def {name}():")
        if docstring:
            lines.append(f'    """{docstring}"""')
        lines.append("    pass")
        lines.append("")
    (tests_dir / filename).write_text("\n".join(lines), encoding="utf-8")


class TestLoadSpecs:

    def test_loads_spec_items(self, tmp_path):
        """Spec items are parsed from lines starting with '- '."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        _write_spec(specs_dir, "example.spec.md", ["item one", "item two"])
        specs = load_specs(specs_dir)
        assert specs["example.spec.md"] == ["item one", "item two"]

    def test_ignores_non_item_lines(self, tmp_path):
        """Lines that don't start with '- ' are not treated as items."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        content = "# Title\n\nSome intro text.\n\n- actual item\n"
        (specs_dir / "mixed.spec.md").write_text(content, encoding="utf-8")
        specs = load_specs(specs_dir)
        assert specs["mixed.spec.md"] == ["actual item"]

    def test_only_loads_md_files(self, tmp_path):
        """Only files matching *.md are loaded."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        _write_spec(specs_dir, "real.md", ["item"])
        (specs_dir / "notes.txt").write_text("- not a spec\n", encoding="utf-8")
        specs = load_specs(specs_dir)
        assert "notes.txt" not in specs
        assert "real.md" in specs

    def test_backslash_n_stored_raw(self, tmp_path):
        r"""\\n in a spec item is stored as raw characters, not transformed."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        # b"\\\\n" produces bytes 5C 5C 6E on disk (two backslashes + n).
        (specs_dir / "spec.md").write_bytes(
            b"# Spec\n\n- output ends with \\\\n\n"
        )
        specs = load_specs(specs_dir)
        item = specs["spec.md"][0]
        item_bytes = item.encode("utf-8")
        # Must contain \\n as three bytes: 5C 5C 6E
        assert bytes([0x5C, 0x5C, 0x6E]) in item_bytes


class TestParseCitations:

    def test_extracts_citation(self):
        """A well-formed Spec: citation is extracted."""
        docstring = "Spec: item text here [example.md]"
        citations = parse_citations(docstring)
        assert citations == [("item text here", "example.md")]

    def test_extracts_multiple_citations(self):
        """Multiple Spec: citations in one docstring are all extracted."""
        docstring = (
            "Spec: first item [a.md]\n"
            "Spec: second item [b.md]"
        )
        citations = parse_citations(docstring)
        assert len(citations) == 2

    def test_returns_empty_for_no_docstring(self):
        """A None docstring returns no citations."""
        assert parse_citations(None) == []

    def test_returns_empty_for_no_citations(self):
        """A docstring without Spec: lines returns no citations."""
        assert parse_citations("Just a description.") == []


class TestValidate:

    def test_all_passing(self):
        """No violations when all specs are cited and all tests cite specs."""
        specs = {"a.md": ["item one"]}
        entries = [
            TestEntry(
                identifier="t::test_one",
                docstring="Spec: item one [a.md]",
            ),
        ]
        uncited_tests, uncited_items, phantoms = validate(specs, entries)
        assert uncited_tests == []
        assert uncited_items == []
        assert phantoms == []

    def test_uncited_test(self):
        """A test with no valid citation is reported."""
        specs = {"a.md": ["item one"]}
        entries = [
            TestEntry(identifier="t::test_one", docstring="No spec here."),
        ]
        uncited_tests, _, _ = validate(specs, entries)
        assert "t::test_one" in uncited_tests

    def test_uncited_spec_item(self):
        """A spec item with no test citing it is reported."""
        specs = {"a.md": ["item one", "item two"]}
        entries = [
            TestEntry(
                identifier="t::test_one",
                docstring="Spec: item one [a.md]",
            ),
        ]
        _, uncited_items, _ = validate(specs, entries)
        assert ("a.md", "item two") in uncited_items

    def test_phantom_citation_wrong_file(self):
        """A citation referencing a nonexistent spec file is a phantom."""
        specs = {"a.md": ["item one"]}
        entries = [
            TestEntry(
                identifier="t::test_one",
                docstring="Spec: item one [nonexistent.md]",
            ),
        ]
        _, _, phantoms = validate(specs, entries)
        assert len(phantoms) == 1
        assert phantoms[0][3] == "spec file not found"

    def test_phantom_citation_wrong_text(self):
        """A citation whose text doesn't match any item is a phantom."""
        specs = {"a.md": ["item one"]}
        entries = [
            TestEntry(
                identifier="t::test_one",
                docstring="Spec: item TYPO [a.md]",
            ),
        ]
        _, _, phantoms = validate(specs, entries)
        assert len(phantoms) == 1
        assert phantoms[0][3] == "spec item not found in file"


class TestRunValidation:

    def test_passes_with_full_compliance(self, tmp_path, capsys):
        """run_validation returns 0 when all checks pass."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one"])
        _write_test(
            tests_dir,
            "test_a.py",
            [("test_one", "Spec: item one [a.md]")],
        )

        result = run_validation(specs_dir, tests_dir)
        assert result == 0
        captured = capsys.readouterr()
        assert "All checks passed" in captured.out

    def test_fails_with_violations(self, tmp_path, capsys):
        """run_validation returns 1 when violations exist."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "a.md", ["item one", "item two"])
        _write_test(
            tests_dir,
            "test_a.py",
            [("test_one", "Spec: item one [a.md]")],
        )

        result = run_validation(specs_dir, tests_dir)
        assert result == 1
        captured = capsys.readouterr()
        assert "SPEC ITEMS WITHOUT RELATED TESTS" in captured.out

    def test_backslash_n_python_end_to_end(self, tmp_path, capsys):
        r"""A spec item with \\n matches a Python citation with \\n."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        # Both files use b"\\\\n" → bytes 5C 5C 6E on disk.
        (specs_dir / "out.md").write_bytes(
            b"# Spec\n\n- output ends with \\\\n\n"
        )
        (tests_dir / "test_out.py").write_bytes(
            b'def test_newline():\n'
            b'    """Spec: output ends with \\\\n [out.md]"""\n'
            b'    pass\n'
        )

        result = run_validation(specs_dir, tests_dir)
        assert result == 0, capsys.readouterr().out

    def test_backslash_n_js_end_to_end(self, tmp_path, capsys):
        r"""A spec item with \\n matches a JS citation with \\n."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        (specs_dir / "out.md").write_bytes(
            b"# Spec\n\n- output ends with \\\\n\n"
        )
        (tests_dir / "out.test.js").write_bytes(
            b'test("newline", () => {\n'
            b'  // Spec: output ends with \\\\n [out.md]\n'
            b'});\n'
        )

        result = run_validation(specs_dir, tests_dir)
        assert result == 0


class TestLiveSamples:

    def test_live_samples_pass_validation(self, capsys):
        r"""The committed sample specs and tests pass validation,
        including items with \\n and \\n\\n."""
        specs_dir = LIVE_SAMPLES_DIR / "specs" / "gen"
        tests_dir = LIVE_SAMPLES_DIR / "tests"
        result = run_validation(specs_dir, tests_dir)
        assert result == 0, capsys.readouterr().out
