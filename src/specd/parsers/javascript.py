"""
Parser for extracting test entries from JavaScript and TypeScript test files.

Supports test frameworks that use test()/it()/describe() conventions
(Jest, Vitest, Mocha). Uses tree-sitter for robust parsing.
"""

from pathlib import Path

import tree_sitter_javascript as tsjs
import tree_sitter_typescript as tsts
from tree_sitter import Language, Parser

from specd.validate import TestEntry

FILE_PATTERNS = ["*.test.js", "*.test.jsx", "*.test.ts", "*.test.tsx"]

_JS_LANGUAGE = Language(tsjs.language())
_TS_LANGUAGE = Language(tsts.language_typescript())
_TSX_LANGUAGE = Language(tsts.language_tsx())

_LANGUAGES = {
    ".js": _JS_LANGUAGE,
    ".jsx": _JS_LANGUAGE,
    ".ts": _TS_LANGUAGE,
    ".tsx": _TSX_LANGUAGE,
}

_TEST_FUNCTIONS = {"test", "it"}


def collect_test_entries(test_file, tests_dir):
    """
    Parse a JS/TS test file and return a TestEntry for each test()
    or it() call, including those nested inside describe() blocks.
    """
    test_file = Path(test_file)
    tests_dir = Path(tests_dir)

    language = _LANGUAGES.get(test_file.suffix)
    if language is None:
        return []

    source = test_file.read_bytes()
    parser = Parser(language)
    tree = parser.parse(source)

    relative_path = test_file.relative_to(tests_dir.parent).as_posix()
    entries = []
    _process_block(tree.root_node, [], entries, relative_path)
    return entries


def _process_block(block_node, describe_stack, entries, relative_path):
    """Walk direct children of a block looking for test/it/describe calls."""
    for child in block_node.children:
        if child.type != "expression_statement":
            continue

        call = _find_call_expression(child)
        if call is None:
            continue

        name = _get_function_name(call)
        if name is None:
            continue

        if name in _TEST_FUNCTIONS:
            description = _get_first_string_arg(call)
            if description is None:
                continue
            body = _get_callback_body(call)
            docstring = _collect_comments(body) if body else None
            parts = [relative_path] + list(describe_stack) + [description]
            entries.append(TestEntry(
                identifier="::".join(parts),
                docstring=docstring,
            ))
        elif name == "describe":
            description = _get_first_string_arg(call)
            if description is None:
                continue
            body = _get_callback_body(call)
            if body is not None:
                describe_stack.append(description)
                _process_block(body, describe_stack, entries, relative_path)
                describe_stack.pop()


def _find_call_expression(node):
    """Find a call_expression that is a direct child of the node."""
    for child in node.children:
        if child.type == "call_expression":
            return child
    return None


def _get_function_name(call_node):
    """Extract the base function name from a call_expression.

    Returns "test", "it", or "describe" for both plain calls
    (test(...)) and member calls (test.skip(...), describe.only(...)).
    """
    func = call_node.child_by_field_name("function")
    if func is None:
        return None
    if func.type == "identifier":
        return func.text.decode()
    if func.type == "member_expression":
        obj = func.child_by_field_name("object")
        if obj is not None and obj.type == "identifier":
            return obj.text.decode()
    return None


def _get_first_string_arg(call_node):
    """Extract the text content of the first string argument."""
    args = call_node.child_by_field_name("arguments")
    if args is None:
        return None
    named = args.named_children
    if named and named[0].type == "string":
        text = named[0].text.decode()
        return text[1:-1]
    return None


def _get_callback_body(call_node):
    """Find the statement_block body of the callback argument."""
    args = call_node.child_by_field_name("arguments")
    if args is None:
        return None
    for child in args.named_children:
        if child.type in ("arrow_function", "function_expression"):
            body = child.child_by_field_name("body")
            if body is not None and body.type == "statement_block":
                return body
    return None


def _collect_comments(body_node):
    """Collect all comment text from descendants of body_node.

    Returns a newline-joined string of comment contents with comment
    markers stripped, or None if no comments are found.
    """
    comments = []
    _walk_comments(body_node, comments)
    if not comments:
        return None
    return "\n".join(comments)


def _walk_comments(node, comments):
    """Recursively collect comment text from a node and its descendants."""
    for child in node.children:
        if child.type == "comment":
            text = child.text.decode().strip()
            if text.startswith("//"):
                text = text[2:].strip()
            elif text.startswith("/*") and text.endswith("*/"):
                text = text[2:-2].strip()
            comments.append(text)
        else:
            _walk_comments(child, comments)
