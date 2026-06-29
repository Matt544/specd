"""
Parser registry for extracting test entries from different file types.

Each parser module must provide:
    - FILE_PATTERNS: list of glob patterns to match test files
    - collect_test_entries(test_file, tests_dir) -> list[TestEntry]
"""

from specd.parsers import python

PARSERS = [python]

try:
    from specd.parsers import javascript
    PARSERS.append(javascript)
except ImportError:
    pass
