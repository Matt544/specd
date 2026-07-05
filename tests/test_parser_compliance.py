"""
Parser compliance tests.

Every parser registered in specd.parsers.PARSERS must pass these tests.
They enforce the behavioral contract all parsers must satisfy, as defined
in specs/parsers.md. The contract covers:

  - the module interface (FILE_PATTERNS and collect_test_entries)
  - the structure and format of TestEntry identifiers
  - the docstring field: markers stripped, None when absent
  - the raw-text invariant: no escape-sequence processing is applied

The suite is parameterised over the live PARSERS registry. When a new
parser is added to PARSERS, it automatically becomes subject to all
tests here. The content-factory functions below must be extended to cover
the new parser; if a factory has no branch for the new parser it will
call _builder_missing, which fails with a message telling the developer
what to add.

Escaping note: the raw-text contract tests use write_bytes with explicit
byte literals so that Python's own escape processing does not interfere
with the bytes written to disk. Assertions for those tests use bytes()
comparisons for the same reason. Follow this pattern when adding
builders for new parsers.
"""

import pytest

from specd.parsers import PARSERS
from specd.parsers import python as _py_parser
from specd.validate import TestEntry

try:
    from specd.parsers import javascript as _js_parser
except ImportError:
    _js_parser = None


# ---------------------------------------------------------------------------
# Content factories
#
# Each factory produces test-file content for a specific scenario.
#
# Factories that return text return (filename, content_str).
# Factories that return bytes return (filename, content_bytes) and should
# be written with write_bytes.
# Factories that are not meaningful for a given parser (e.g. deep nesting
# for Python) return None; the consuming test skips automatically.
#
# When adding a new parser, add a branch to every factory. If you forget,
# the test will call _builder_missing and fail with a clear message.
# ---------------------------------------------------------------------------


def _builder_missing(parser):
    pytest.fail(
        f"No content builder for {parser.__name__}. "
        f"Add one to tests/test_parser_compliance.py."
    )


def _top_level_cited_file(parser):
    """A file with one top-level test that has a Spec: citation."""
    if parser is _py_parser:
        return (
            "test_cited.py",
            'def test_cited():\n'
            '    """Spec: some item [s.md]"""\n'
            '    pass\n',
        )
    if parser is _js_parser:
        return (
            "cited.test.js",
            'test("cited", () => {\n'
            '  // Spec: some item [s.md]\n'
            '});\n',
        )
    _builder_missing(parser)


def _empty_file(parser):
    """An empty file matching the parser's file patterns."""
    if parser is _py_parser:
        return ("test_empty.py", "")
    if parser is _js_parser:
        return ("empty.test.js", "")
    _builder_missing(parser)


def _no_comment_file(parser):
    """A file with a test that has no docstring or inline comments."""
    if parser is _py_parser:
        return (
            "test_nodoc.py",
            'def test_nodoc():\n'
            '    pass\n',
        )
    if parser is _js_parser:
        return (
            "nodoc.test.js",
            'test("nodoc", () => {\n'
            '});\n',
        )
    _builder_missing(parser)


def _nested_test_file(parser):
    """A file with one test nested inside a single named container."""
    if parser is _py_parser:
        return (
            "test_nested.py",
            'class TestSuite:\n'
            '    def test_method(self):\n'
            '        """Spec: some item [s.md]"""\n'
            '        pass\n',
        )
    if parser is _js_parser:
        return (
            "nested.test.js",
            'describe("Suite", () => {\n'
            '  test("the test", () => {\n'
            '    // Spec: some item [s.md]\n'
            '  });\n'
            '});\n',
        )
    _builder_missing(parser)


def _deeply_nested_file(parser):
    """
    A file with one test nested two containers deep.

    Returns None for parsers that do not support multiple nesting levels
    in their standard test structure; the consuming test will skip.
    """
    if parser is _py_parser:
        return None
    if parser is _js_parser:
        return (
            "deep.test.js",
            'describe("outer", () => {\n'
            '  describe("inner", () => {\n'
            '    test("the test", () => {\n'
            '      // Spec: some item [s.md]\n'
            '    });\n'
            '  });\n'
            '});\n',
        )
    _builder_missing(parser)


def _backslash_n_file(parser):
    r"""A file with a citation containing \\n (bytes 5C 5C 6E on disk).

    Returns (filename, bytes_content). Write with write_bytes, not
    write_text, to avoid any further encoding transformations.
    """
    if parser is _py_parser:
        return (
            "test_bsn.py",
            b'def test_bsn():\n'
            b'    """Spec: item with \\\\n [s.md]"""\n'
            b'    pass\n',
        )
    if parser is _js_parser:
        return (
            "bsn.test.js",
            b'test("bsn", () => {\n'
            b'  // Spec: item with \\\\n [s.md]\n'
            b'});\n',
        )
    _builder_missing(parser)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(params=PARSERS, ids=lambda p: p.__name__.rsplit(".", 1)[-1])
def parser(request):
    return request.param


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestParserInterface:

    def test_file_patterns_is_nonempty_list_of_strings(self, parser):
        """
        Spec: `FILE_PATTERNS` is a non-empty list of glob strings matched against file names (not full paths) [parsers.md]
        """
        patterns = parser.FILE_PATTERNS
        assert isinstance(patterns, list), "FILE_PATTERNS must be a list"
        assert len(patterns) > 0, "FILE_PATTERNS must not be empty"
        assert all(isinstance(p, str) for p in patterns), (
            "every entry in FILE_PATTERNS must be a string"
        )

    def test_collect_test_entries_is_callable(self, parser):
        """
        Spec: A parser is a Python module that exposes `FILE_PATTERNS` and `collect_test_entries` [parsers.md]
        """
        assert callable(parser.collect_test_entries)


class TestCollectTestEntries:

    def test_returns_list_of_test_entries(self, parser, tmp_path):
        """
        Spec: `collect_test_entries(test_file, tests_dir)` accepts a path to a test file and a path to the tests root directory, and returns a list of `TestEntry` objects [parsers.md]
        """
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content = _top_level_cited_file(parser)
        (tests_dir / filename).write_text(content, encoding="utf-8")

        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)

        assert isinstance(entries, list)
        assert len(entries) >= 1
        for entry in entries:
            assert isinstance(entry, TestEntry)

    def test_empty_file_returns_empty_list(self, parser, tmp_path):
        """
        Spec: `collect_test_entries` returns an empty list when the file contains no tests [parsers.md]
        """
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content = _empty_file(parser)
        (tests_dir / filename).write_text(content, encoding="utf-8")

        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)

        assert entries == []

    def test_test_entry_has_identifier_and_docstring(self, parser, tmp_path):
        """
        Spec: Each test found in a file is represented as a `TestEntry` with an `identifier` and a `docstring` [parsers.md]
        """
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content = _top_level_cited_file(parser)
        (tests_dir / filename).write_text(content, encoding="utf-8")

        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)
        entry = entries[0]

        assert isinstance(entry.identifier, str) and entry.identifier, (
            "identifier must be a non-empty string"
        )
        assert entry.docstring is None or isinstance(entry.docstring, str), (
            "docstring must be a string or None"
        )


class TestParserRegistration:

    def test_parsers_list_exists(self):
        """
        Spec: Parsers are registered in the `PARSERS` list in `specd.parsers` [parsers.md]
        """
        from specd.parsers import PARSERS

        assert isinstance(PARSERS, list)

    def test_python_parser_always_registered(self):
        """
        Spec: The Python parser is always registered [parsers.md]
        """
        from specd.parsers import PARSERS
        from specd.parsers import python as _python_parser

        assert _python_parser in PARSERS

    def test_javascript_parser_registered_when_installed(self):
        """
        Spec: The JavaScript/TypeScript parser is registered only when the `specd[js]` optional dependencies are installed [parsers.md]
        """
        if _js_parser is None:
            pytest.skip("specd[js] not installed")

        from specd.parsers import PARSERS

        assert _js_parser in PARSERS


class TestIdentifier:

    def test_top_level_identifier_format(self, parser, tmp_path):
        """
        Spec: For a top-level test, the identifier takes the form `<path>::<test name>` [parsers.md]
        """
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content = _top_level_cited_file(parser)
        (tests_dir / filename).write_text(content, encoding="utf-8")

        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)
        identifier = entries[0].identifier

        parts = identifier.split("::")
        assert len(parts) == 2, (
            f"top-level identifier should have exactly two ::-separated components "
            f"(<path>::<test name>), got {identifier!r}"
        )

    def test_identifier_path_from_tests_dir_parent(self, parser, tmp_path):
        """
        Spec: The `identifier` is a string with components joined by `::`, where the first component is a POSIX-style path from the tests directory's parent — e.g. a file at `tests/subdir/test_foo.py` has path component `tests/subdir/test_foo.py` [parsers.md]
        """
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content = _top_level_cited_file(parser)
        (tests_dir / filename).write_text(content, encoding="utf-8")

        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)
        path_component = entries[0].identifier.split("::")[0]

        assert path_component.startswith("tests/"), (
            f"path component should start with 'tests/' (relative to the parent "
            f"of tests_dir), got {path_component!r}"
        )

    def test_identifier_uses_posix_separators(self, parser, tmp_path):
        """
        Spec: The `identifier` is a string with components joined by `::`, where the first component is a POSIX-style path from the tests directory's parent — e.g. a file at `tests/subdir/test_foo.py` has path component `tests/subdir/test_foo.py` [parsers.md]
        """
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content = _top_level_cited_file(parser)
        (tests_dir / filename).write_text(content, encoding="utf-8")

        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)

        assert "\\" not in entries[0].identifier, (
            f"identifier must use forward slashes, got {entries[0].identifier!r}"
        )

    def test_nested_identifier_includes_container_name(self, parser, tmp_path):
        """
        Spec: For a test nested inside a container (class, describe block, or equivalent), each container name is inserted as a `::` component between the path and the test name, in order from outermost to innermost [parsers.md]
        """
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content = _nested_test_file(parser)
        (tests_dir / filename).write_text(content, encoding="utf-8")

        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)
        assert len(entries) >= 1
        identifier = entries[0].identifier

        parts = identifier.split("::")
        assert len(parts) == 3, (
            f"nested identifier should have three ::-separated components "
            f"(<path>::<container>::<test name>), got {identifier!r}"
        )

    def test_deeply_nested_identifier_container_order(self, tmp_path):
        """
        Spec: For a test nested inside a container (class, describe block, or equivalent), each container name is inserted as a `::` component between the path and the test name, in order from outermost to innermost [parsers.md]

        This test targets the JS parser, which supports arbitrary describe nesting.
        The single-container case (TestIdentifier::test_nested_identifier_includes_container_name)
        covers the same spec item for all parsers.
        """
        if _js_parser is None:
            pytest.skip("specd[js] not installed")
        filename, content = _deeply_nested_file(_js_parser)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / filename).write_text(content, encoding="utf-8")

        entries = _js_parser.collect_test_entries(tests_dir / filename, tests_dir)
        assert len(entries) >= 1
        identifier = entries[0].identifier

        parts = identifier.split("::")
        assert len(parts) == 4, (
            f"two-level nested identifier should have four ::-separated components "
            f"(<path>::<outer>::<inner>::<test name>), got {identifier!r}"
        )
        assert parts[1] == "outer", (
            f"first container component should be 'outer' (outermost first), "
            f"got {parts[1]!r}"
        )
        assert parts[2] == "inner", (
            f"second container component should be 'inner', got {parts[2]!r}"
        )


class TestDocstring:

    def test_docstring_is_none_when_no_comments(self, parser, tmp_path):
        """
        Spec: The `docstring` is the body of the docstring or comment block associated with the test — with language markers stripped but no further processing applied — or `None` if the test has no docstring or comment block [parsers.md]
        """
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content = _no_comment_file(parser)
        (tests_dir / filename).write_text(content, encoding="utf-8")

        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)

        assert len(entries) == 1
        assert entries[0].docstring is None

    def test_docstring_body_has_language_markers_stripped(self, parser, tmp_path):
        """
        Spec: The `docstring` is the body of the docstring or comment block associated with the test — with language markers stripped but no further processing applied — or `None` if the test has no docstring or comment block [parsers.md]
        """
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content = _top_level_cited_file(parser)
        (tests_dir / filename).write_text(content, encoding="utf-8")

        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)
        docstring = entries[0].docstring

        assert docstring is not None
        # The body of the docstring/comment is the content between the language
        # markers. For the content written by _top_level_cited_file, the body
        # is exactly the citation text with no surrounding markers.
        assert docstring == "Spec: some item [s.md]", (
            f"docstring body should be exactly the content between language "
            f"markers with no further processing; got {docstring!r}"
        )


class TestRawTextContract:

    def test_backslash_n_is_preserved_raw(self, parser, tmp_path):
        r"""
        Spec: Characters in the `docstring` body are the literal characters from the source file: no escape-sequence processing is applied [parsers.md]
        Spec: This contract holds for all parsers regardless of language [parsers.md]
        """
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content_bytes = _backslash_n_file(parser)
        (tests_dir / filename).write_bytes(content_bytes)

        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)
        assert len(entries) == 1
        docstring = entries[0].docstring
        assert docstring is not None

        # The source file contains the 3-byte sequence 5C 5C 6E (two backslashes
        # followed by n). After marker stripping these must appear unchanged —
        # not collapsed to a single backslash-n or to a newline character.
        assert bytes([0x5C, 0x5C, 0x6E]) in docstring.encode("utf-8"), (
            r"\\n on disk must be preserved as-is; it must not be "
            "processed into a single backslash-n or a newline"
        )
