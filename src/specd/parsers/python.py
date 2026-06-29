"""
Parser for extracting test entries from Python test files.

Supports both pytest and unittest conventions — any function or method
whose name starts with test_ is collected.
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
    relative_path = test_file.relative_to(tests_dir.parent).as_posix()
    entries = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                entries.append(
                    TestEntry(
                        identifier=f"{relative_path}::{node.name}",
                        docstring=ast.get_docstring(node),
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
                                docstring=ast.get_docstring(child),
                            )
                        )

    return entries
