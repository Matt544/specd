"""
Parser for extracting test entries from Python test files.

Supports both pytest and unittest conventions — any function or method
whose name starts with test_ is collected.

Docstrings are extracted as raw source text (no Python escape processing)
so that citation matching is raw-to-raw with spec item text.
"""

import ast
from pathlib import Path

from specd.validate import TestEntry

FILE_PATTERNS = ["test_*.py"]


def collect_test_entries(test_file, tests_dir):
    """
    Parse a Python test file and return a TestEntry for each test
    function, including methods nested inside classes.
    """
    test_file = Path(test_file)
    tests_dir = Path(tests_dir)
    source = test_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(test_file))
    relative_path = test_file.relative_to(tests_dir).as_posix()
    entries = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                entries.append(
                    TestEntry(
                        identifier=f"{relative_path}::{node.name}",
                        docstring=_extract_raw_docstring(source, node),
                    )
                )
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if child.name.startswith("test_"):
                        entries.append(
                            TestEntry(
                                identifier=(
                                    f"{relative_path}::{node.name}"
                                    f"::{child.name}"
                                ),
                                docstring=_extract_raw_docstring(source, child),
                            )
                        )

    return entries


def _extract_raw_docstring(source, function_node):
    """Extract raw docstring text from a function node.

    Returns the literal source characters between the quote delimiters,
    with no Python escape processing.  Returns None if the function has
    no docstring.
    """
    if not function_node.body:
        return None
    first_stmt = function_node.body[0]
    if not isinstance(first_stmt, ast.Expr):
        return None
    if not isinstance(first_stmt.value, ast.Constant):
        return None
    if not isinstance(first_stmt.value.value, str):
        return None

    raw = ast.get_source_segment(source, first_stmt.value)
    if raw is None:
        return None

    return _strip_string_delimiters(raw)


def _strip_string_delimiters(literal):
    """Strip quote delimiters and any string prefix from a string literal.

    Given raw source like ``r\"\"\"content\"\"\"``, returns ``content``.
    Handles prefixes u, U, r, R and quote styles ``\"\"\"``, ``'''``,
    ``\"``, ``'``.
    """
    text = literal

    # Strip prefix characters (u, U, r, R).
    # f-strings and b-strings cannot be docstrings, so only these prefixes
    # are possible for an ast.Constant with a str value.
    while text and text[0] in "uUrR":
        text = text[1:]

    if text.startswith('"""') and text.endswith('"""'):
        return text[3:-3]
    if text.startswith("'''") and text.endswith("'''"):
        return text[3:-3]
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    if text.startswith("'") and text.endswith("'"):
        return text[1:-1]

    return text
