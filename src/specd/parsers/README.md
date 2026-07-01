# Adding a parser

## The contract

A parser is a Python module that exposes:

- `FILE_PATTERNS`: a list of glob strings (e.g., `["test_*.py"]`)
- `collect_test_entries(test_file, tests_dir) -> list[TestEntry]`

`TestEntry` is imported from `specd.validate`. It has two fields:
- `identifier`: a string starting with a POSIX-style relative path from `tests_dir`'s parent, using `::` to separate path from test name (e.g., `tests/test_example.py::test_one`)
- `docstring`: the raw source text containing `Spec:` citations, or `None`

Raw means raw: no escape processing. The bytes on disk are the bytes in the string. This is the core invariant that makes citation matching work uniformly across languages.

## Steps

1. Create `src/specd/parsers/<language>.py` implementing `FILE_PATTERNS` and `collect_test_entries`.
2. Register the module in `src/specd/parsers/__init__.py` by appending it to `PARSERS`.
3. Add content builders to `tests/test_parser_compliance.py`: one branch each in `_cited_file`, `_empty_file`, and `_backslash_n_file` for your parser module.
4. Run `pytest` — the compliance suite automatically picks up the new parser and runs every behavioral test against it.

If you skip step 3, the compliance tests will fail with a message telling you what to add.

## Reference

- `python.py` and `javascript.py` in this directory are the existing implementations.
- `tests/test_parser_compliance.py` is the authoritative behavioral contract.
- `tests/README.md` documents the `write_bytes` pattern for `\\n` test fixtures.
