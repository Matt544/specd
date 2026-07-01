"""
Parser compliance tests.

Every parser registered in specd.parsers.PARSERS must pass these tests.
They enforce the behavioral contract that all parsers must satisfy:
return raw source text with no escape processing.

When adding a new parser, register it in specd.parsers.PARSERS and add
a content builder to the _cited_file, _empty_file, and _backslash_n_file
functions below. If a builder is missing, the test will fail with a
message telling you what to add.

Escaping note: tests that verify \\n handling use write_bytes with
explicit byte literals (e.g., b"\\\\n" to produce bytes 5C 5C 6E on
disk) and assert against bytes([0x5C, 0x5C, 0x6E]) rather than string
comparisons. This avoids Python's own string escaping stacking with the
target file's escaping, which is a reliable source of confusion. Follow
the same pattern when adding builders for new parsers.
"""

import pytest

from specd.parsers import PARSERS
from specd.parsers import python as _py_parser
from specd.validate import TestEntry

try:
    from specd.parsers import javascript as _js_parser
except ImportError:
    _js_parser = None


# -- Content builders --------------------------------------------------------
#
# Each builder returns (filename, content) for text or (filename, bytes)
# for the backslash-n test.  Keyed by parser module identity.
#
# When you add a new parser to PARSERS, add a branch for it in each
# builder.  If you forget, the test will fail with a clear message.


def _cited_file(parser):
    """Minimal test file with a Spec: citation."""
    if parser is _py_parser:
        return ("test_compliance.py",
                'def test_cited():\n'
                '    """Spec: some item [s.md]"""\n'
                '    pass\n')
    if parser is _js_parser:
        return ("compliance.test.js",
                'test("cited", () => {\n'
                '  // Spec: some item [s.md]\n'
                '});\n')
    pytest.fail(
        f"No content builder for {parser.__name__}. "
        f"Add one to tests/test_parser_compliance.py."
    )


def _empty_file(parser):
    """Empty test file matching the parser's patterns."""
    if parser is _py_parser:
        return ("test_empty.py", "")
    if parser is _js_parser:
        return ("empty.test.js", "")
    pytest.fail(
        f"No content builder for {parser.__name__}. "
        f"Add one to tests/test_parser_compliance.py."
    )


def _backslash_n_file(parser):
    r"""Test file with \\n (bytes 5C 5C 6E) in a citation.

    Returns (filename, content_bytes).  Use write_bytes to write.
    """
    if parser is _py_parser:
        return ("test_bsn.py",
                b'def test_bsn():\n'
                b'    """Spec: item with \\\\n [s.md]"""\n'
                b'    pass\n')
    if parser is _js_parser:
        return ("bsn.test.js",
                b'test("bsn", () => {\n'
                b'  // Spec: item with \\\\n [s.md]\n'
                b'});\n')
    pytest.fail(
        f"No content builder for {parser.__name__}. "
        f"Add one to tests/test_parser_compliance.py."
    )


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture(params=PARSERS, ids=lambda p: p.__name__.rsplit(".", 1)[-1])
def parser(request):
    return request.param


# -- Interface tests ---------------------------------------------------------


class TestParserInterface:

    def test_file_patterns_is_nonempty_list(self, parser):
        """FILE_PATTERNS exists, is a list of strings, and is non-empty."""
        patterns = parser.FILE_PATTERNS
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        assert all(isinstance(p, str) for p in patterns)

    def test_collect_test_entries_is_callable(self, parser):
        """collect_test_entries exists and is callable."""
        assert callable(parser.collect_test_entries)


# -- Behavioral tests -------------------------------------------------------


class TestParserBehavior:

    def test_returns_test_entries(self, parser, tmp_path):
        """Given a file with a test, returns TestEntry objects."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content = _cited_file(parser)
        (tests_dir / filename).write_text(content, encoding="utf-8")
        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)
        assert len(entries) >= 1
        for entry in entries:
            assert isinstance(entry, TestEntry)
            assert entry.identifier
            assert entry.docstring is not None

    def test_empty_file_returns_empty_list(self, parser, tmp_path):
        """An empty file produces no entries."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content = _empty_file(parser)
        (tests_dir / filename).write_text(content, encoding="utf-8")
        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)
        assert entries == []

    def test_identifier_includes_posix_path(self, parser, tmp_path):
        """Identifiers include a forward-slash relative path."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content = _cited_file(parser)
        (tests_dir / filename).write_text(content, encoding="utf-8")
        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)
        assert entries[0].identifier.startswith("tests/")
        assert "\\" not in entries[0].identifier


# -- Raw text contract -------------------------------------------------------


class TestRawTextContract:

    def test_backslash_n_preserved_raw(self, parser, tmp_path):
        r"""\\n in a citation is returned as raw bytes (5C 5C 6E),
        not processed through language-specific escape rules."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        filename, content_bytes = _backslash_n_file(parser)
        (tests_dir / filename).write_bytes(content_bytes)
        entries = parser.collect_test_entries(tests_dir / filename, tests_dir)
        assert len(entries) == 1
        doc = entries[0].docstring
        assert doc is not None
        doc_bytes = doc.encode("utf-8")
        # Must contain the raw 3-byte sequence: backslash backslash n
        assert bytes([0x5C, 0x5C, 0x6E]) in doc_bytes
