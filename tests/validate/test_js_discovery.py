"""
Tests for JavaScript and TypeScript test file discovery in the validate command.
"""

import importlib
import subprocess
import sys
from pathlib import Path

SPECD = [sys.executable, "-m", "specd.cli"]


def _run_validate(specs_dir, tests_dir):
    """Run specd validate with explicit directory paths and return CompletedProcess."""
    return subprocess.run(
        SPECD + ["validate", "-s", str(specs_dir), "--tests", str(tests_dir)],
        capture_output=True,
        text=True,
    )


def _write_spec(specs_dir, content):
    """Write a single spec file named a.md with the given content."""
    (Path(specs_dir) / "a.md").write_text(content, encoding="utf-8")


class TestJsTestFileDiscovery:

    def test_js_test_file_patterns(self, tmp_path):
        """
        Spec: a JS/TS test file is a file named *.test.{js,jsx,ts,tsx} located anywhere under the specd `tests` directory [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n- item two\n- item three\n- item four\n")

        # All four JS/TS extensions should be discovered
        for ext, item in [
            ("js", "item one"),
            ("jsx", "item two"),
            ("ts", "item three"),
            ("tsx", "item four"),
        ]:
            (tests_dir / f"foo.test.{ext}").write_text(
                f'test("test", () => {{\n'
                f"  // Spec: {item} [a.md]\n"
                f"}});\n",
                encoding="utf-8",
            )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0

    def test_non_test_js_file_not_discovered(self, tmp_path):
        """
        Spec: a JS/TS test file is a file named *.test.{js,jsx,ts,tsx} located anywhere under the specd `tests` directory [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

        # helper.js does not match *.test.js — should not be discovered
        (tests_dir / "helper.js").write_text(
            'test("test", () => {\n'
            '  // Spec: item one [a.md]\n'
            '});\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 1
        assert "item one" in result.stdout


class TestJsTestFunctionDiscovery:

    def test_js_test_call_recognized(self, tmp_path):
        """
        Spec: a JS/TS test is a call to a `test()` or `it()` function [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

        (tests_dir / "foo.test.js").write_text(
            'test("the test", () => {\n'
            '  // Spec: item one [a.md]\n'
            '});\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0

    def test_it_call_recognized(self, tmp_path):
        """
        Spec: a JS/TS test is a call to a `test()` or `it()` function [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

        (tests_dir / "foo.test.js").write_text(
            'it("the test", () => {\n'
            '  // Spec: item one [a.md]\n'
            '});\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0


class TestJsCitationDiscovery:

    def test_js_citation_in_line_comment(self, tmp_path):
        """
        Spec: JS/TS functions validly cite specs by placing the references on their own lines in `//` line comments or `/* */` block comments [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

        (tests_dir / "foo.test.js").write_text(
            'test("the test", () => {\n'
            '  // Spec: item one [a.md]\n'
            '});\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0

    def test_js_citation_in_block_comment(self, tmp_path):
        """
        Spec: JS/TS functions validly cite specs by placing the references on their own lines in `//` line comments or `/* */` block comments [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

        (tests_dir / "foo.test.js").write_text(
            'test("the test", () => {\n'
            '  /* Spec: item one [a.md] */\n'
            '});\n',
            encoding="utf-8",
        )

        result = _run_validate(specs_dir, tests_dir)
        assert result.returncode == 0


class TestJsParserOptional:

    def test_js_discovery_disabled_without_dependency(self, tmp_path):
        """
        Spec: JS discoverability patterns only apply when the specd[js] optional dependencies are installed [validate.md]
        """
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        _write_spec(specs_dir, "# A\n\n- item one\n")

        (tests_dir / "foo.test.js").write_text(
            'test("the test", () => {\n'
            '  // Spec: item one [a.md]\n'
            '});\n',
            encoding="utf-8",
        )

        # Simulate tree_sitter not being installed by blocking the imports
        js_module_keys = [
            k for k in sys.modules
            if "tree_sitter" in k
            or k in ("specd.parsers.javascript", "specd.parsers")
        ]
        saved_modules = {k: sys.modules.pop(k) for k in js_module_keys}

        sys.modules["tree_sitter"] = None
        sys.modules["tree_sitter_javascript"] = None
        sys.modules["tree_sitter_typescript"] = None

        try:
            import specd.parsers
            importlib.reload(specd.parsers)

            from specd.parsers import PARSERS
            parser_names = [
                getattr(p, "__name__", str(p)) for p in PARSERS
            ]
            assert not any("javascript" in name for name in parser_names)

        finally:
            for key in ("tree_sitter", "tree_sitter_javascript", "tree_sitter_typescript"):
                sys.modules.pop(key, None)
            sys.modules.update(saved_modules)
            # Reload parsers to restore original state
            if "specd.parsers" in sys.modules:
                importlib.reload(sys.modules["specd.parsers"])

        # Functional check: run validate in a subprocess that blocks tree_sitter
        # before any specd imports, confirming JS citations are not discovered
        block_script = (
            "import sys\n"
            "sys.modules['tree_sitter'] = None\n"
            "sys.modules['tree_sitter_javascript'] = None\n"
            "sys.modules['tree_sitter_typescript'] = None\n"
            "from specd.cli import main\n"
            "main()\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", block_script,
             "validate", "-s", str(specs_dir), "--tests", str(tests_dir)],
            capture_output=True,
            text=True,
        )
        # The JS test file is ignored, so item one has no citing test
        assert result.returncode == 1
        assert "item one" in result.stdout
