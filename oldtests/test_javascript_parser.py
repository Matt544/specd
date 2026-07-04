"""
Tests for the JavaScript/TypeScript test file parser.

Covers: test()/it() collection, describe() nesting, identifier format,
citation extraction from // comments, skip/only variants, callback
styles, TypeScript and TSX support, and non-test code exclusion.
"""

from specd.parsers.javascript import FILE_PATTERNS, collect_test_entries
from specd.validate import parse_citations


def _write_js(tests_dir, filename, content):
    """Write a JS/TS test file with the given content."""
    (tests_dir / filename).write_text(content, encoding="utf-8")


# -- File patterns -----------------------------------------------------------


class TestFilePatterns:

    def test_includes_all_js_ts_extensions(self):
        """FILE_PATTERNS covers .test.js, .test.jsx, .test.ts, .test.tsx."""
        assert "*.test.js" in FILE_PATTERNS
        assert "*.test.jsx" in FILE_PATTERNS
        assert "*.test.ts" in FILE_PATTERNS
        assert "*.test.tsx" in FILE_PATTERNS

    def test_exactly_four_patterns(self):
        """No unexpected extra patterns."""
        assert len(FILE_PATTERNS) == 4


# -- Basic test collection ---------------------------------------------------


class TestCollectBasicTests:

    def test_top_level_test_call(self, tmp_path):
        """A bare test() at file scope is collected."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test("adds numbers", () => {\n'
            '  // Spec: addition returns sum of operands [math.md]\n'
            '  expect(add(1, 2)).toBe(3);\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1
        assert "adds numbers" in entries[0].identifier
        citations = parse_citations(entries[0].docstring)
        assert citations == [
            ("addition returns sum of operands", "math.md"),
        ]

    def test_top_level_it_call(self, tmp_path):
        """A bare it() at file scope is collected, same as test()."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'it("adds numbers", () => {\n'
            '  // Spec: addition returns sum of operands [math.md]\n'
            '  expect(add(1, 2)).toBe(3);\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1
        assert "adds numbers" in entries[0].identifier

    def test_multiple_tests_in_file(self, tmp_path):
        """All test()/it() calls in a single file are collected."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test("adds", () => {\n'
            '  // Spec: addition works [math.md]\n'
            '});\n'
            '\n'
            'test("subtracts", () => {\n'
            '  // Spec: subtraction works [math.md]\n'
            '});\n'
            '\n'
            'it("multiplies", () => {\n'
            '  // Spec: multiplication works [math.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 3

    def test_empty_file_returns_no_entries(self, tmp_path):
        """An empty test file produces no entries."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "empty.test.js", "")
        entries = collect_test_entries(tests_dir / "empty.test.js", tests_dir)
        assert entries == []


# -- describe() nesting ------------------------------------------------------


class TestDescribeBlocks:

    def test_test_inside_describe(self, tmp_path):
        """test() inside describe() has describe name in identifier."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "parser.test.js", (
            'describe("Parser", () => {\n'
            '  test("handles empty input", () => {\n'
            '    // Spec: returns empty array for empty input [parser.md]\n'
            '  });\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "parser.test.js", tests_dir)
        assert len(entries) == 1
        assert entries[0].identifier == (
            "tests/parser.test.js::Parser::handles empty input"
        )

    def test_it_inside_describe(self, tmp_path):
        """it() inside describe() works identically to test()."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "parser.test.js", (
            'describe("Parser", () => {\n'
            '  it("handles empty input", () => {\n'
            '    // Spec: returns empty array [parser.md]\n'
            '  });\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "parser.test.js", tests_dir)
        assert entries[0].identifier == (
            "tests/parser.test.js::Parser::handles empty input"
        )

    def test_nested_describes(self, tmp_path):
        """Nested describe blocks concatenate all ancestor names with ::."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "parser.test.js", (
            'describe("Parser", () => {\n'
            '  describe("edge cases", () => {\n'
            '    it("handles empty input", () => {\n'
            '      // Spec: returns empty array [parser.md]\n'
            '    });\n'
            '  });\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "parser.test.js", tests_dir)
        assert entries[0].identifier == (
            "tests/parser.test.js::Parser::edge cases::handles empty input"
        )

    def test_three_levels_of_nesting(self, tmp_path):
        """Three nested describe blocks all appear in the identifier."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "parser.test.js", (
            'describe("Parser", () => {\n'
            '  describe("tokenizer", () => {\n'
            '    describe("edge cases", () => {\n'
            '      it("handles empty", () => {\n'
            '        // Spec: returns empty [parser.md]\n'
            '      });\n'
            '    });\n'
            '  });\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "parser.test.js", tests_dir)
        assert entries[0].identifier == (
            "tests/parser.test.js"
            "::Parser::tokenizer::edge cases::handles empty"
        )

    def test_top_level_test_has_no_describe_segment(self, tmp_path):
        """A top-level test() without any describe() wrapper has
        no describe segment — just path::test name."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "parser.test.js", (
            'test("handles empty input", () => {\n'
            '  // Spec: returns empty array [parser.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "parser.test.js", tests_dir)
        assert entries[0].identifier == (
            "tests/parser.test.js::handles empty input"
        )

    def test_sibling_describes(self, tmp_path):
        """Tests in sibling describe blocks get distinct identifiers."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "parser.test.js", (
            'describe("Parser", () => {\n'
            '  it("parses", () => {\n'
            '    // Spec: parses input [parser.md]\n'
            '  });\n'
            '});\n'
            '\n'
            'describe("Lexer", () => {\n'
            '  it("tokenizes", () => {\n'
            '    // Spec: tokenizes input [parser.md]\n'
            '  });\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "parser.test.js", tests_dir)
        assert len(entries) == 2
        ids = {e.identifier for e in entries}
        assert "tests/parser.test.js::Parser::parses" in ids
        assert "tests/parser.test.js::Lexer::tokenizes" in ids


# -- Identifier path formatting ----------------------------------------------


class TestIdentifierPaths:

    def test_relative_path_starts_with_tests_dir_name(self, tmp_path):
        """Identifier path is relative to tests_dir's parent."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test("a test", () => {});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert entries[0].identifier.startswith("tests/")

    def test_subdirectory_included_in_path(self, tmp_path):
        """Test files in subdirectories include the full relative path."""
        tests_dir = tmp_path / "tests"
        sub_dir = tests_dir / "unit" / "parsers"
        sub_dir.mkdir(parents=True)
        _write_js(sub_dir, "math.test.js", (
            'test("a test", () => {});\n'
        ))
        entries = collect_test_entries(sub_dir / "math.test.js", tests_dir)
        assert entries[0].identifier.startswith("tests/unit/parsers/")

    def test_uses_posix_separators(self, tmp_path):
        """Identifier uses forward slashes regardless of platform."""
        tests_dir = tmp_path / "tests"
        sub_dir = tests_dir / "unit"
        sub_dir.mkdir(parents=True)
        _write_js(sub_dir, "math.test.js", (
            'test("a test", () => {});\n'
        ))
        entries = collect_test_entries(sub_dir / "math.test.js", tests_dir)
        assert "\\" not in entries[0].identifier


# -- Citation extraction from comments ---------------------------------------


class TestCitationExtraction:

    def test_single_citation(self, tmp_path):
        """A single // Spec: comment yields one citation."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test("adds", () => {\n'
            '  // Spec: addition returns sum [math.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        citations = parse_citations(entries[0].docstring)
        assert citations == [("addition returns sum", "math.md")]

    def test_multiple_citations(self, tmp_path):
        """Multiple // Spec: comments in one test are all captured."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test("validates and computes", () => {\n'
            '  // Spec: must validate input [math.md]\n'
            '  // Spec: must reject negative values [math.md]\n'
            '  validate(input);\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        citations = parse_citations(entries[0].docstring)
        assert len(citations) == 2
        assert ("must validate input", "math.md") in citations
        assert ("must reject negative values", "math.md") in citations

    def test_no_citation_still_collected(self, tmp_path):
        """A test with no // Spec: comment is collected with no citations."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test("does something", () => {\n'
            '  expect(true).toBe(true);\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1
        citations = parse_citations(entries[0].docstring)
        assert citations == []

    def test_citation_anywhere_in_body(self, tmp_path):
        """A // Spec: comment anywhere in the test body is captured,
        not just at the top."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test("middle citation", () => {\n'
            '  const x = setup();\n'
            '  doSomething(x);\n'
            '  // Spec: must process data [math.md]\n'
            '  expect(x).toBeDefined();\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        citations = parse_citations(entries[0].docstring)
        assert len(citations) == 1

    def test_non_spec_comments_not_citations(self, tmp_path):
        """Regular comments (without 'Spec:') don't produce citations."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test("has comments", () => {\n'
            '  // This is a regular comment\n'
            '  // TODO: fix this later\n'
            '  // Spec: must validate input [math.md]\n'
            '  expect(true).toBe(true);\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        citations = parse_citations(entries[0].docstring)
        assert len(citations) == 1
        assert citations[0] == ("must validate input", "math.md")

    def test_backslash_n_in_comment_stays_raw(self, tmp_path):
        r"""\\n in a // comment is returned as raw bytes (5C 5C 6E)."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        # b"\\\\n" produces bytes 5C 5C 6E on disk (two backslashes + n).
        (tests_dir / "math.test.js").write_bytes(
            b'test("newline", () => {\n'
            b'  // Spec: output ends with \\\\n [math.md]\n'
            b'});\n'
        )
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        doc_bytes = entries[0].docstring.encode("utf-8")
        # Raw \\n: two backslash bytes followed by n (5C 5C 6E).
        assert bytes([0x5C, 0x5C, 0x6E]) in doc_bytes

    def test_long_citation(self, tmp_path):
        """A long spec item (~264 chars) is captured in full."""
        long_item = (
            "when the input contains nested brackets and escaped characters "
            "the parser must correctly identify the outermost bracket pair "
            "and treat escaped brackets as literal characters rather than "
            "treating them as delimiters"
        )
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "parser.test.js", (
            'test("handles complex input", () => {\n'
            f'  // Spec: {long_item} [parser.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(
            tests_dir / "parser.test.js", tests_dir,
        )
        citations = parse_citations(entries[0].docstring)
        assert len(citations) == 1
        assert citations[0] == (long_item, "parser.md")

    def test_spec_comment_outside_test_not_attached(self, tmp_path):
        """A // Spec: comment outside any test() or it() body does not
        attach to any test entry."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            '// Spec: orphan at module level [math.md]\n'
            '\n'
            'describe("Math", () => {\n'
            '  // Spec: orphan inside describe [math.md]\n'
            '\n'
            '  test("adds", () => {\n'
            '    // Spec: addition works [math.md]\n'
            '  });\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1
        citations = parse_citations(entries[0].docstring)
        assert len(citations) == 1
        assert citations[0] == ("addition works", "math.md")

    def test_each_test_gets_own_citations(self, tmp_path):
        """Citations inside one test do not leak to adjacent tests."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test("first", () => {\n'
            '  // Spec: item one [math.md]\n'
            '});\n'
            '\n'
            'test("second", () => {\n'
            '  // Spec: item two [math.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        first = next(e for e in entries if "first" in e.identifier)
        second = next(e for e in entries if "second" in e.identifier)
        assert parse_citations(first.docstring) == [
            ("item one", "math.md"),
        ]
        assert parse_citations(second.docstring) == [
            ("item two", "math.md"),
        ]


# -- skip/only variants ------------------------------------------------------


class TestSkipAndOnly:

    def test_test_skip_collected(self, tmp_path):
        """test.skip() is collected like a regular test."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test.skip("skipped test", () => {\n'
            '  // Spec: item [math.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1
        assert "skipped test" in entries[0].identifier

    def test_it_skip_collected(self, tmp_path):
        """it.skip() is collected like a regular it()."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'it.skip("skipped test", () => {\n'
            '  // Spec: item [math.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1

    def test_test_only_collected(self, tmp_path):
        """test.only() is collected like a regular test."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test.only("focused test", () => {\n'
            '  // Spec: item [math.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1
        assert "focused test" in entries[0].identifier

    def test_it_only_collected(self, tmp_path):
        """it.only() is collected like a regular it()."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'it.only("focused test", () => {\n'
            '  // Spec: item [math.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1

    def test_describe_skip_tests_collected(self, tmp_path):
        """Tests inside describe.skip() are still collected."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'describe.skip("Skipped suite", () => {\n'
            '  test("still collected", () => {\n'
            '    // Spec: item [math.md]\n'
            '  });\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1
        assert "Skipped suite" in entries[0].identifier
        assert "still collected" in entries[0].identifier

    def test_describe_only_tests_collected(self, tmp_path):
        """Tests inside describe.only() are still collected."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'describe.only("Focused suite", () => {\n'
            '  it("still collected", () => {\n'
            '    // Spec: item [math.md]\n'
            '  });\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1


# -- Callback styles ---------------------------------------------------------


class TestCallbackStyles:

    def test_function_expression(self, tmp_path):
        """test() with a function() {} callback is collected."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test("with function expression", function() {\n'
            '  // Spec: item [math.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1
        assert "with function expression" in entries[0].identifier

    def test_async_arrow(self, tmp_path):
        """test() with an async arrow callback is collected."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test("async test", async () => {\n'
            '  // Spec: item [math.md]\n'
            '  const result = await fetchData();\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1

    def test_async_function_expression(self, tmp_path):
        """test() with an async function() {} callback is collected."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'test("async func", async function() {\n'
            '  // Spec: item [math.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1


# -- TypeScript and TSX support ----------------------------------------------


class TestTypeScriptSupport:

    def test_ts_file_with_type_annotations(self, tmp_path):
        """A .test.ts file with TypeScript syntax is parsed correctly."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "parser.test.ts", (
            'import { describe, it, expect } from "vitest";\n'
            'import { parse } from "../src/parser";\n'
            '\n'
            'describe("Parser", () => {\n'
            '  it("handles typed input", () => {\n'
            '    // Spec: must accept string input [parser.md]\n'
            '    const result: string[] = parse("hello");\n'
            '    expect(result).toEqual(["hello"]);\n'
            '  });\n'
            '});\n'
        ))
        entries = collect_test_entries(
            tests_dir / "parser.test.ts", tests_dir,
        )
        assert len(entries) == 1
        assert entries[0].identifier == (
            "tests/parser.test.ts::Parser::handles typed input"
        )
        citations = parse_citations(entries[0].docstring)
        assert citations == [("must accept string input", "parser.md")]

    def test_tsx_file_with_jsx(self, tmp_path):
        """A .test.tsx file with JSX syntax is parsed correctly."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "component.test.tsx", (
            'import { render } from "@testing-library/preact";\n'
            'import { App } from "../src/App";\n'
            '\n'
            'describe("App", () => {\n'
            '  it("renders heading", () => {\n'
            '    // Spec: must render welcome heading [app.md]\n'
            '    const { getByText } = render(<App />);\n'
            '    expect(getByText("Welcome")).toBeTruthy();\n'
            '  });\n'
            '});\n'
        ))
        entries = collect_test_entries(
            tests_dir / "component.test.tsx", tests_dir,
        )
        assert len(entries) == 1
        assert entries[0].identifier == (
            "tests/component.test.tsx::App::renders heading"
        )

    def test_tsx_file_with_generic_types(self, tmp_path):
        """TSX files with generic type parameters don't confuse the parser."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "hooks.test.tsx", (
            'import { renderHook } from "@testing-library/preact";\n'
            '\n'
            'describe("useStore", () => {\n'
            '  it("returns typed state", () => {\n'
            '    // Spec: hook returns current state [hooks.md]\n'
            '    const { result } = renderHook<void, State>(\n'
            '      () => useStore()\n'
            '    );\n'
            '    expect(result.current).toBeDefined();\n'
            '  });\n'
            '});\n'
        ))
        entries = collect_test_entries(
            tests_dir / "hooks.test.tsx", tests_dir,
        )
        assert len(entries) == 1


# -- Non-test code is ignored ------------------------------------------------


class TestNonTestCodeIgnored:

    def test_imports_not_collected(self, tmp_path):
        """Import statements are not treated as tests."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'import { add } from "../src/math";\n'
            'import { describe, it, expect } from "vitest";\n'
            '\n'
            'test("adds", () => {\n'
            '  // Spec: item [math.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1

    def test_helper_functions_not_collected(self, tmp_path):
        """Plain function declarations are not treated as tests."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'function setup() {\n'
            '  return { x: 1 };\n'
            '}\n'
            '\n'
            'const helper = () => {\n'
            '  return true;\n'
            '};\n'
            '\n'
            'test("real test", () => {\n'
            '  // Spec: item [math.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1
        assert "real test" in entries[0].identifier

    def test_lifecycle_hooks_not_collected(self, tmp_path):
        """beforeEach, afterEach, beforeAll, afterAll are not tests."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'describe("Math", () => {\n'
            '  beforeEach(() => {\n'
            '    // setup\n'
            '  });\n'
            '\n'
            '  afterEach(() => {\n'
            '    // teardown\n'
            '  });\n'
            '\n'
            '  beforeAll(() => {\n'
            '    // one-time setup\n'
            '  });\n'
            '\n'
            '  afterAll(() => {\n'
            '    // one-time teardown\n'
            '  });\n'
            '\n'
            '  test("adds", () => {\n'
            '    // Spec: item [math.md]\n'
            '  });\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1

    def test_variable_declarations_not_collected(self, tmp_path):
        """Top-level variable declarations are not tests."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        _write_js(tests_dir, "math.test.js", (
            'const TIMEOUT = 5000;\n'
            'let counter = 0;\n'
            '\n'
            'test("real test", () => {\n'
            '  // Spec: item [math.md]\n'
            '});\n'
        ))
        entries = collect_test_entries(tests_dir / "math.test.js", tests_dir)
        assert len(entries) == 1
