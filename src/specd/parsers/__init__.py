"""
Parser registry for extracting test entries from different file types.

Each parser module must provide:
    - FILE_PATTERNS: list of glob patterns to match test files
    - collect_test_entries(test_file, tests_dir) -> list[TestEntry]
"""

from specd.parsers import python

PARSERS_BY_EXTENSION = {
    ".py": python,
}


def get_parser(extension):
    """Return the parser module for a given file extension, or None."""
    return PARSERS_BY_EXTENSION.get(extension)
