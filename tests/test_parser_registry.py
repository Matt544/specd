"""
Tests for the parser registry and its consumption by run_validation.

The registry was restructured from a dict (keyed by extension) to a list
of parser modules to prevent duplicate processing when multiple extensions
map to the same parser. These tests verify:

- The registry is a list with no duplicates
- Every registered parser satisfies the parser interface
- run_validation iterates parsers without duplication
- run_validation discovers JS test files alongside Python test files
"""

from specd.parsers import PARSERS
from specd.validate import run_validation


def _write_spec(specs_dir, filename, items):
    """Write a spec file with the given list items."""
    content = "# Spec\n\n" + "\n".join(f"- {item}" for item in items) + "\n"
    (specs_dir / filename).write_text(content, encoding="utf-8")


# -- Registry structure ------------------------------------------------------


class TestRegistryStructure:

    def test_parsers_is_a_list(self):
        """PARSERS is a list, not a dict."""
        assert isinstance(PARSERS, list)

    def test_no_duplicate_parsers(self):
        """Each parser module appears exactly once."""
        assert len(PARSERS) == len(set(id(p) for p in PARSERS))

    def test_python_parser_registered(self):
        """The Python parser is in the registry."""
        from specd.parsers import python
        assert python in PARSERS

    def test_javascript_parser_registered(self):
        """The JavaScript parser is in the registry when tree-sitter
        is available."""
        from specd.parsers import javascript
        assert javascript in PARSERS


class TestParserInterface:

    def test_all_parsers_have_file_patterns(self):
        """Every registered parser has a FILE_PATTERNS list."""
        for parser in PARSERS:
            assert hasattr(parser, "FILE_PATTERNS")
            assert isinstance(parser.FILE_PATTERNS, list)
            assert len(parser.FILE_PATTERNS) > 0

    def test_all_parsers_have_collect_test_entries(self):
        """Every registered parser has a collect_test_entries callable."""
        for parser in PARSERS:
            assert hasattr(parser, "collect_test_entries")
            assert callable(parser.collect_test_entries)


# -- No duplicate processing -------------------------------------------------


class TestNoDuplicateProcessing:

    def test_js_tests_not_duplicated(self, tmp_path):
        """A JS test file is processed exactly once, not once per
        extension that maps to the JS parser."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "math.md", ["addition works"])
        (tests_dir / "math.test.js").write_text(
            'test("adds", () => {\n'
            '  // Spec: addition works [math.md]\n'
            '});\n',
            encoding="utf-8",
        )

        result = run_validation(specs_dir, tests_dir)
        assert result == 0

    def test_mixed_extensions_no_duplication(self, tmp_path, capsys):
        """When JS and TS test files both exist, each is processed
        once — not multiplied by the number of registered extensions."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "math.md", ["addition works", "types work"])

        (tests_dir / "math.test.js").write_text(
            'test("adds", () => {\n'
            '  // Spec: addition works [math.md]\n'
            '});\n',
            encoding="utf-8",
        )
        (tests_dir / "types.test.ts").write_text(
            'test("types", () => {\n'
            '  // Spec: types work [math.md]\n'
            '});\n',
            encoding="utf-8",
        )

        result = run_validation(specs_dir, tests_dir)
        assert result == 0
        captured = capsys.readouterr()
        assert "Tests checked:                     2" in captured.out


# -- Integration: mixed Python + JS validation --------------------------------


class TestMixedLanguageValidation:

    def test_python_and_js_tests_both_discovered(self, tmp_path, capsys):
        """run_validation finds both Python and JS test files."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "app.md", ["backend works", "frontend works"])

        (tests_dir / "test_backend.py").write_text(
            'def test_backend():\n'
            '    """Spec: backend works [app.md]"""\n'
            '    pass\n',
            encoding="utf-8",
        )
        (tests_dir / "frontend.test.ts").write_text(
            'test("frontend", () => {\n'
            '  // Spec: frontend works [app.md]\n'
            '});\n',
            encoding="utf-8",
        )

        result = run_validation(specs_dir, tests_dir)
        assert result == 0
        captured = capsys.readouterr()
        assert "Tests checked:                     2" in captured.out
        assert "All checks passed" in captured.out

    def test_uncited_js_test_reported(self, tmp_path, capsys):
        """A JS test without a citation is reported as uncited."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "app.md", ["item one"])

        (tests_dir / "test_backend.py").write_text(
            'def test_backend():\n'
            '    """Spec: item one [app.md]"""\n'
            '    pass\n',
            encoding="utf-8",
        )
        (tests_dir / "frontend.test.js").write_text(
            'test("no citation here", () => {\n'
            '  expect(true).toBe(true);\n'
            '});\n',
            encoding="utf-8",
        )

        result = run_validation(specs_dir, tests_dir)
        assert result == 1
        captured = capsys.readouterr()
        assert "TESTS WITHOUT VALID SPEC ITEMS" in captured.out
        assert "frontend.test.js" in captured.out

    def test_phantom_js_citation_reported(self, tmp_path, capsys):
        """A JS test citing a nonexistent spec item is reported as phantom."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "app.md", ["real item"])

        (tests_dir / "app.test.js").write_text(
            'test("cites wrong item", () => {\n'
            '  // Spec: nonexistent item [app.md]\n'
            '});\n',
            encoding="utf-8",
        )

        result = run_validation(specs_dir, tests_dir)
        assert result == 1
        captured = capsys.readouterr()
        assert "PHANTOM CITATIONS" in captured.out

    def test_js_test_cites_spec_item_making_it_covered(self, tmp_path, capsys):
        """A spec item cited only by a JS test is not reported as uncited."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "app.md", ["only js covers this"])

        (tests_dir / "app.test.tsx").write_text(
            'test("covers it", () => {\n'
            '  // Spec: only js covers this [app.md]\n'
            '});\n',
            encoding="utf-8",
        )

        result = run_validation(specs_dir, tests_dir)
        assert result == 0
        captured = capsys.readouterr()
        assert "All checks passed" in captured.out
