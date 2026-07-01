# Tests

## Writing tests that involve `\\n`

specd treats `\\n` (a literal backslash followed by `n`) as the universal
convention for representing newlines in spec items and test citations.
All parsers return raw source text with no escape processing, and
`specd validate` compares raw text on both sides.

When writing test fixtures that contain literal `\\n` sequences, use
`write_bytes` with explicit byte literals and assert against byte values.
This avoids Python's own string literal escaping stacking with the
escaping semantics of the target file format, which is a reliable source
of confusion.

**Example — writing a fixture file:**

```python
# b"\\\\n" in Python source produces bytes 5C 5C 6E on disk
# (one backslash, one backslash, one n).
(tests_dir / "test_example.py").write_bytes(
    b'def test_newline():\n'
    b'    """Spec: output ends with \\\\n [out.md]"""\n'
    b'    pass\n'
)
```

**Example — asserting raw preservation:**

```python
doc_bytes = entries[0].docstring.encode("utf-8")
# Must contain the raw 3-byte sequence: backslash backslash n
assert bytes([0x5C, 0x5C, 0x6E]) in doc_bytes
```

**Why not `write_text` with string literals?** A Python string literal
like `"\\n"` is two characters (backslash + n) but `"\\\\n"` is three
(backslash + backslash + n). When the file being written also has its own
escaping rules (Python docstrings, JS comments), the layers compound and
it becomes easy to end up with the wrong bytes on disk. `write_bytes`
with `b"..."` literals makes the disk content unambiguous.

See `test_parser_compliance.py` for the canonical examples of this pattern.
