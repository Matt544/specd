"""
Tests for render command --help output.
"""

import os
import subprocess
import sys

SPECD = [sys.executable, "-m", "specd.cli"]

# Prevent argparse from wrapping help text based on a narrow pipe-default column width
_WIDE_ENV = {**os.environ, "COLUMNS": "200"}


def _run_help(flag):
    """Run specd render with the given help flag and return CompletedProcess."""
    return subprocess.run(
        SPECD + ["render", flag],
        capture_output=True,
        text=True,
        env=_WIDE_ENV,
    )


class TestHelp:

    def test_h_flag_prints_help(self):
        """
        Spec: Calling `render` with `--help` or `-h` prints help [render.md]
        """
        result = _run_help("-h")
        assert result.stdout

    def test_help_flag_prints_help(self):
        """
        Spec: Calling `render` with `--help` or `-h` prints help [render.md]
        """
        result = _run_help("--help")
        assert result.stdout

    def test_help_usage_line(self):
        """
        Spec: Help text includes `usage: specd render [-h] [-t TEMPLATES] [-s SPECS] [-w]\\n\\n` [render.md]
        """
        result = _run_help("--help")
        assert "usage: specd render [-h] [-t TEMPLATES] [-s SPECS] [-w]" in result.stdout

    def test_help_options_header(self):
        """
        Spec: Help text includes `options:\\n` [render.md]
        """
        result = _run_help("--help")
        assert "options:" in result.stdout

    def test_help_h_option_line(self):
        """
        Spec: Help text includes `  -h, --help            show this help message and exit\\n` [render.md]
        """
        result = _run_help("--help")
        assert "-h, --help" in result.stdout
        assert "show this help message and exit" in result.stdout

    def test_help_templates_option_text(self):
        """
        Spec: Help text includes `  -t, --templates TEMPLATES\\n` + `Path to the templates directory` [render.md]
        """
        result = _run_help("--help")
        assert "-t, --templates TEMPLATES" in result.stdout
        assert "Path to the templates directory" in result.stdout

    def test_help_specs_option_text(self):
        """
        Spec: Help text includes `  -s, --specs SPECS     Path to the specs output directory` [render.md]
        """
        result = _run_help("--help")
        assert "-s, --specs SPECS" in result.stdout
        assert "Path to the specs output directory" in result.stdout

    def test_help_watch_option_text(self):
        """
        Spec: Help text includes `  -w, --watch           Watch templates for changes and re-render automatically` [render.md]
        """
        result = _run_help("--help")
        assert "-w, --watch" in result.stdout
        assert "Watch templates for changes and re-render automatically" in result.stdout

    def test_help_followed_by_blank_line(self):
        """
        Spec: Help text is followed by a blank line [render.md]
        """
        result = _run_help("--help")
        assert result.stdout.endswith("\n\n")
