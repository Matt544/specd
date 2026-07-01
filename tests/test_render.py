"""
Tests for spec template rendering.

Most tests use pytest's tmp_path fixture for isolation. The live samples
tests verify the committed template/spec pair under live_samples/specs/
— those files serve as living documentation.
"""

from pathlib import Path

from specd.render import GENERATED_MARKER, render_all

LIVE_SAMPLES_DIR = Path(__file__).parent / "live_samples"


def _setup(tmp_path, templates):
    """
    Create templates/ and specs/ under tmp_path and write template files.

    templates: dict mapping filename to content.
    """
    templates_dir = tmp_path / "templates"
    specs_dir = tmp_path / "specs"
    templates_dir.mkdir()
    specs_dir.mkdir()
    for name, content in templates.items():
        (templates_dir / name).write_text(content, encoding="utf-8")
    return templates_dir, specs_dir


class TestFileNaming:

    def test_specd_md_extension_becomes_md(self, tmp_path):
        """The .specd.md suffix is replaced with .md in the output filename."""
        templates_dir, specs_dir = _setup(
            tmp_path, {"example.spec.specd.md": "# Example"},
        )
        render_all(templates_dir, specs_dir)
        assert (specs_dir / "example.spec.md").exists()

    def test_output_file_does_not_retain_specd_suffix(self, tmp_path):
        """No .specd.md file is created in the specs directory."""
        templates_dir, specs_dir = _setup(
            tmp_path, {"example.spec.specd.md": "# Example"},
        )
        render_all(templates_dir, specs_dir)
        assert not list(specs_dir.glob("*.specd.md"))

    def test_multiple_templates_produce_multiple_specs(self, tmp_path):
        """Each .specd.md template produces its own .md spec file."""
        templates_dir, specs_dir = _setup(
            tmp_path,
            {"one.spec.specd.md": "# One", "two.spec.specd.md": "# Two"},
        )
        render_all(templates_dir, specs_dir)
        specs = sorted(f.name for f in specs_dir.iterdir())
        assert specs == ["one.spec.md", "two.spec.md"]


class TestGeneratedMarker:

    def test_output_starts_with_marker(self, tmp_path):
        """Every rendered spec starts with the generated-file marker."""
        templates_dir, specs_dir = _setup(
            tmp_path, {"a.spec.specd.md": "# A\n"},
        )
        render_all(templates_dir, specs_dir)
        result = (specs_dir / "a.spec.md").read_text(encoding="utf-8")
        assert result.startswith(GENERATED_MARKER)

    def test_blank_line_separates_marker_from_content(self, tmp_path):
        """The marker is followed by exactly one blank line before content."""
        templates_dir, specs_dir = _setup(
            tmp_path, {"a.spec.specd.md": "# A\n"},
        )
        render_all(templates_dir, specs_dir)
        result = (specs_dir / "a.spec.md").read_text(encoding="utf-8")
        lines = result.split("\n", 2)
        assert lines[0] == GENERATED_MARKER
        assert lines[1] == ""
        assert lines[2].startswith("# A")


class TestRendering:

    def test_plain_text_passes_through(self, tmp_path):
        """A template with no Jinja syntax renders as-is, after the marker."""
        content = "# Title\n\n- item one\n- item two\n"
        templates_dir, specs_dir = _setup(
            tmp_path, {"plain.spec.specd.md": content},
        )
        render_all(templates_dir, specs_dir)
        result = (specs_dir / "plain.spec.md").read_text(encoding="utf-8")
        assert result == GENERATED_MARKER + "\n\n" + content

    def test_variable_substitution(self, tmp_path):
        """Jinja2 variable expressions are rendered in the output."""
        template = "{% set name = 'frequency' %}\n- method: {{ name }}\n"
        templates_dir, specs_dir = _setup(
            tmp_path, {"vars.spec.specd.md": template},
        )
        render_all(templates_dir, specs_dir)
        result = (specs_dir / "vars.spec.md").read_text(encoding="utf-8")
        assert "- method: frequency" in result

    def test_for_loop_generates_repeated_lines(self, tmp_path):
        """A for loop stamps out one spec line per iteration."""
        template = (
            "{% for m in ['frequency', 'data'] %}\n"
            "- The `question` arg is validated (re: `{{ m }}`)\n"
            "{% endfor %}\n"
        )
        templates_dir, specs_dir = _setup(
            tmp_path, {"loop.spec.specd.md": template},
        )
        render_all(templates_dir, specs_dir)
        result = (specs_dir / "loop.spec.md").read_text(encoding="utf-8")
        assert "- The `question` arg is validated (re: `frequency`)" in result
        assert "- The `question` arg is validated (re: `data`)" in result

    def test_macro_expands_with_parameter(self, tmp_path):
        """A macro call expands its body with the supplied argument."""
        template = (
            "{% macro greet(name) %}\n"
            "- hello {{ name }}\n"
            "{% endmacro %}\n"
            "{{ greet('world') }}\n"
        )
        templates_dir, specs_dir = _setup(
            tmp_path, {"macro.spec.specd.md": template},
        )
        render_all(templates_dir, specs_dir)
        result = (specs_dir / "macro.spec.md").read_text(encoding="utf-8")
        assert "- hello world" in result


class TestWhitespace:

    def test_trim_blocks_removes_tag_newlines(self, tmp_path):
        """Block tags do not inject extra blank lines into the output."""
        template = "# Title\n{% set x = 1 %}\n- item\n"
        templates_dir, specs_dir = _setup(
            tmp_path, {"ws.spec.specd.md": template},
        )
        render_all(templates_dir, specs_dir)
        result = (specs_dir / "ws.spec.md").read_text(encoding="utf-8")
        assert result == GENERATED_MARKER + "\n\n" + "# Title\n- item\n"

    def test_lstrip_blocks_removes_leading_whitespace(self, tmp_path):
        """Leading whitespace before block tags is stripped."""
        template = "# Title\n  {% set x = 1 %}\n- item\n"
        templates_dir, specs_dir = _setup(
            tmp_path, {"lstrip.spec.specd.md": template},
        )
        render_all(templates_dir, specs_dir)
        result = (specs_dir / "lstrip.spec.md").read_text(encoding="utf-8")
        assert result == GENERATED_MARKER + "\n\n" + "# Title\n- item\n"

    def test_trailing_newline_is_preserved(self, tmp_path):
        """The final newline of the template is kept in the output."""
        template = "# Title\n"
        templates_dir, specs_dir = _setup(
            tmp_path, {"trail.spec.specd.md": template},
        )
        render_all(templates_dir, specs_dir)
        result = (specs_dir / "trail.spec.md").read_text(encoding="utf-8")
        assert result.endswith("\n")

    def test_macro_at_top_does_not_inject_blank_lines_before_content(
        self, tmp_path
    ):
        """
        A macro defined at the top of the template does not produce
        blank lines before the first visible content.
        """
        template = (
            "{% macro m(x) %}\n"
            "- {{ x }}\n"
            "{% endmacro %}\n"
            "# Title\n"
            "{{ m('item') }}\n"
        )
        templates_dir, specs_dir = _setup(
            tmp_path, {"top_macro.spec.specd.md": template},
        )
        render_all(templates_dir, specs_dir)
        result = (specs_dir / "top_macro.spec.md").read_text(encoding="utf-8")
        assert result.startswith(GENERATED_MARKER + "\n\n# Title\n")


class TestEdgeCases:

    def test_no_templates_prints_message(self, tmp_path, capsys):
        """When templates/ has no .specd.md files, a message is printed."""
        templates_dir, specs_dir = _setup(tmp_path, {})
        render_all(templates_dir, specs_dir)
        captured = capsys.readouterr()
        assert "No *.specd.md templates found" in captured.out

    def test_non_specd_files_are_ignored(self, tmp_path):
        """Files without a .specd.md extension in templates/ are not rendered."""
        templates_dir, specs_dir = _setup(
            tmp_path, {"real.spec.specd.md": "# Real"},
        )
        (templates_dir / "notes.txt").write_text(
            "ignore me", encoding="utf-8",
        )
        render_all(templates_dir, specs_dir)
        output_files = [f.name for f in specs_dir.iterdir()]
        assert output_files == ["real.spec.md"]

    def test_curly_braces_in_spec_text(self, tmp_path):
        """
        Literal curly braces in spec text (e.g. format strings) survive
        rendering when not valid Jinja syntax.
        """
        template = '- the report says "{comma separated matching keys}"\n'
        templates_dir, specs_dir = _setup(
            tmp_path, {"braces.spec.specd.md": template},
        )
        render_all(templates_dir, specs_dir)
        result = (specs_dir / "braces.spec.md").read_text(encoding="utf-8")
        assert "{comma separated matching keys}" in result


class TestLiveSamplesRendering:

    def test_template_renders_to_committed_spec(self):
        """
        The committed template renders to match the committed spec.
        This test also regenerates the spec, so that both files stay
        in sync and serve as readable documentation of how a template
        produces a spec.
        """
        templates_dir = LIVE_SAMPLES_DIR / "specs" / "templates"
        specs_dir = LIVE_SAMPLES_DIR / "specs" / "gen"
        render_all(templates_dir, specs_dir)

        template_path = templates_dir / "sample.spec.specd.md"
        spec_path = specs_dir / "sample.spec.md"

        assert template_path.exists(), "Sample template is missing"
        assert spec_path.exists(), "Sample spec was not generated"

        result = spec_path.read_text(encoding="utf-8")

        assert result.startswith(GENERATED_MARKER + "\n\n")
        assert "# Sample" in result

    def test_spec_lines_are_unique_per_command(self):
        """
        Each command section in the sample spec has its own unique
        lines, demonstrating that the macro stamps out independently
        citable spec items.
        """
        spec_path = LIVE_SAMPLES_DIR / "specs" / "gen" / "sample.spec.md"
        result = spec_path.read_text(encoding="utf-8")
        lines = [line for line in result.splitlines() if line.startswith("- ")]

        assert len(lines) == len(set(lines)), (
            "Spec lines are not all unique — the macro should produce "
            "distinct lines per command"
        )
