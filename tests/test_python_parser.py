"""
Tests for the Python test file parser.

Covers: file patterns, test function collection, class nesting,
identifier format, and raw docstring extraction.
"""

from specd.parsers.python import FILE_PATTERNS, collect_test_entries


def _write_py(tests_dir, filename, content):
    """Write a Python test file."""
    (tests_dir / filename).write_text(content, encoding="utf-8")


# -- File patterns -----------------------------------------------------------


class TestFilePatterns:

    def test_includes_test_underscore_py(self):
        """FILE_PATTERNS contains test_*.py."""
        assert "test_*.py" in FILE_PATTERNS

    def test_exactly_one_pattern(self):
        """No unexpected extra patterns."""
        assert len(FILE_PATTERNS) == 1


# -- Basic test collection ---------------------------------------------------


class TestCollectBasicTests:

    def test_top_level_test_function(self, tmp_path):
        """Top-level test_ functions are collected."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_py(tests_dir, "test_example.py", (
            'def test_one():\n'
            '    """Spec: item [s.md]"""\n'
            '    pass\n'
        ))
        entries = collect_test_entries(tests_dir / "test_example.py", tests_dir)
        assert len(entries) == 1
        assert "test_one" in entries[0].identifier

    def test_class_nested_method(self, tmp_path):
        """Test methods inside classes are collected."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_py(tests_dir, "test_grouped.py", (
            'class TestGroup:\n'
            '    def test_nested(self):\n'
            '        """Spec: item [s.md]"""\n'
            '        pass\n'
        ))
        entries = collect_test_entries(tests_dir / "test_grouped.py", tests_dir)
        assert len(entries) == 1
        assert "TestGroup::test_nested" in entries[0].identifier

    def test_ignores_non_test_functions(self, tmp_path):
        """Functions not starting with test_ are skipped."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_py(tests_dir, "test_example.py", (
            'def helper():\n'
            '    pass\n'
            '\n'
            'def test_real():\n'
            '    """Spec: item [s.md]"""\n'
            '    pass\n'
        ))
        entries = collect_test_entries(tests_dir / "test_example.py", tests_dir)
        assert len(entries) == 1
        assert "test_real" in entries[0].identifier

    def test_empty_file(self, tmp_path):
        """An empty file produces no entries."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_py(tests_dir, "test_empty.py", "")
        entries = collect_test_entries(tests_dir / "test_empty.py", tests_dir)
        assert entries == []

    def test_no_docstring_yields_none(self, tmp_path):
        """A test with no docstring has docstring=None."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_py(tests_dir, "test_example.py", (
            'def test_bare():\n'
            '    pass\n'
        ))
        entries = collect_test_entries(tests_dir / "test_example.py", tests_dir)
        assert len(entries) == 1
        assert entries[0].docstring is None


# -- Identifier path formatting ----------------------------------------------


class TestIdentifierPaths:

    def test_starts_with_tests_dir_name(self, tmp_path):
        """Identifier path is relative to tests_dir's parent."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_py(tests_dir, "test_a.py", 'def test_a():\n    pass\n')
        entries = collect_test_entries(tests_dir / "test_a.py", tests_dir)
        assert entries[0].identifier.startswith("tests/")

    def test_subdirectory_included(self, tmp_path):
        """Files in subdirectories include the full relative path."""
        tests_dir = tmp_path / "tests"
        sub = tests_dir / "unit"
        sub.mkdir(parents=True)
        _write_py(sub, "test_a.py", 'def test_a():\n    pass\n')
        entries = collect_test_entries(sub / "test_a.py", tests_dir)
        assert entries[0].identifier.startswith("tests/unit/")

    def test_posix_separators(self, tmp_path):
        """Identifiers use forward slashes on all platforms."""
        tests_dir = tmp_path / "tests"
        sub = tests_dir / "unit"
        sub.mkdir(parents=True)
        _write_py(sub, "test_a.py", 'def test_a():\n    pass\n')
        entries = collect_test_entries(sub / "test_a.py", tests_dir)
        assert "\\" not in entries[0].identifier


# -- Raw docstring extraction ------------------------------------------------


class TestRawDocstringExtraction:

    def test_backslash_n_stays_raw(self, tmp_path):
        r"""\\n in a Python docstring is returned as raw source bytes
        (5C 5C 6E), not processed through Python escape rules."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        # b"\\\\n" produces bytes 5C 5C 6E on disk (two backslashes + n).
        (tests_dir / "test_example.py").write_bytes(
            b'def test_newline():\n'
            b'    """Spec: output ends with \\\\n [out.md]"""\n'
            b'    pass\n'
        )
        entries = collect_test_entries(tests_dir / "test_example.py", tests_dir)
        assert len(entries) == 1
        doc_bytes = entries[0].docstring.encode("utf-8")
        # Raw \\n: two backslash bytes followed by n (5C 5C 6E).
        assert bytes([0x5C, 0x5C, 0x6E]) in doc_bytes
