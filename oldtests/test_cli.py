"""
Tests for the specd CLI entry point.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from watchdog.events import (
    DirModifiedEvent,
    FileClosedEvent,
    FileClosedNoWriteEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileOpenedEvent,
)

PACKAGE_ROOT = Path(__file__).parents[1]


def _run_specd(*args, cwd=None):
    """Run specd as a subprocess and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "specd.cli", *args],
        capture_output=True,
        text=True,
        cwd=cwd or PACKAGE_ROOT,
    )


class TestRenderCommand:

    def test_renders_with_explicit_paths(self, tmp_path):
        """specd render -t TEMPLATES -s SPECS renders templates."""
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()
        (templates_dir / "a.spec.specd.md").write_text(
            "# A\n\n- item\n", encoding="utf-8",
        )

        result = _run_specd(
            "render", "-t", str(templates_dir), "-s", str(specs_dir),
        )
        assert result.returncode == 0
        assert (specs_dir / "a.spec.md").exists()

    def test_exits_nonzero_for_missing_templates_dir(self, tmp_path):
        """specd render exits with code 1 when the templates dir doesn't exist."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        result = _run_specd(
            "render",
            "-t", str(tmp_path / "nonexistent"), "-s", str(specs_dir),
        )
        assert result.returncode == 1
        assert "not found" in result.stdout

    def test_exits_nonzero_for_missing_specs_dir(self, tmp_path):
        """specd render exits with code 1 when the specs dir doesn't exist."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        result = _run_specd(
            "render",
            "-t", str(templates_dir), "-s", str(tmp_path / "nonexistent"),
        )
        assert result.returncode == 1
        assert "not found" in result.stdout


class TestValidateCommand:

    def test_validate_passes_with_compliance(self, tmp_path):
        """specd validate exits 0 when all checks pass."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        (specs_dir / "a.md").write_text(
            "# A\n\n- item one\n", encoding="utf-8",
        )
        (tests_dir / "test_a.py").write_text(
            'def test_one():\n'
            '    """Spec: item one [a.md]"""\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run_specd(
            "validate",
            "-s", str(specs_dir),
            "--tests", str(tests_dir),
        )
        assert result.returncode == 0
        assert "All checks passed" in result.stdout

    def test_validate_fails_with_violations(self, tmp_path):
        """specd validate exits 1 when violations exist."""
        specs_dir = tmp_path / "specs"
        tests_dir = tmp_path / "tests"
        specs_dir.mkdir()
        tests_dir.mkdir()

        (specs_dir / "a.md").write_text(
            "# A\n\n- item one\n- item two\n", encoding="utf-8",
        )
        (tests_dir / "test_a.py").write_text(
            'def test_one():\n'
            '    """Spec: item one [a.md]"""\n'
            '    pass\n',
            encoding="utf-8",
        )

        result = _run_specd(
            "validate",
            "-s", str(specs_dir),
            "--tests", str(tests_dir),
        )
        assert result.returncode == 1
        assert "SPEC ITEMS WITHOUT RELATED TESTS" in result.stdout

    def test_validate_exits_nonzero_for_missing_dirs(self, tmp_path):
        """specd validate exits 1 when dirs don't exist."""
        result = _run_specd(
            "validate",
            "-s", str(tmp_path / "no_specs"),
            "--tests", str(tmp_path / "no_tests"),
        )
        assert result.returncode == 1


class TestHelpOutput:

    def test_bare_specd_prints_help(self):
        """Bare specd (no subcommand) prints help and exits 0."""
        result = _run_specd()
        assert result.returncode == 0
        assert "render" in result.stdout
        assert "validate" in result.stdout

    def test_help_flag(self):
        """specd --help exits cleanly."""
        result = _run_specd("--help")
        assert result.returncode == 0
        assert "specd" in result.stdout

    def test_render_help_flag(self):
        """specd render --help exits cleanly."""
        result = _run_specd("render", "--help")
        assert result.returncode == 0
        assert "templates" in result.stdout.lower()

    def test_validate_help_flag(self):
        """specd validate --help exits cleanly."""
        result = _run_specd("validate", "--help")
        assert result.returncode == 0
        assert "tests" in result.stdout.lower()


def _capture_watch_handler(tmp_path):
    """Start _do_watch with a fake Observer and return the handler it creates.

    Sets up a minimal templates+specs directory so _do_watch gets past the
    existence checks, patches Observer so the watch loop exits immediately,
    and returns the FileSystemEventHandler instance that was scheduled.
    """
    from specd.cli import _do_watch

    templates_dir = tmp_path / "templates"
    specs_dir = tmp_path / "specs"
    templates_dir.mkdir()
    specs_dir.mkdir()
    (templates_dir / "test.specd.md").write_text("# Test\n", encoding="utf-8")

    captured = {}

    mock_observer = MagicMock()
    mock_observer.is_alive.return_value = False  # exit the while-loop immediately

    def save_handler(handler, path, recursive=False):
        captured["handler"] = handler

    mock_observer.schedule.side_effect = save_handler

    args = MagicMock()
    args.templates = str(templates_dir)
    args.specs = str(specs_dir)
    args.watch = True

    with patch("watchdog.observers.Observer", return_value=mock_observer):
        _do_watch(args)

    return captured["handler"], templates_dir, specs_dir


TEMPLATE_PATH = "/fake/templates/test.specd.md"


class TestWatchHandler:
    """The watch-mode handler must only re-render on content modifications.

    Regression tests for an infinite-loop bug triggered on WSL when VSCode
    opens a .specd.md file.  The root cause: the handler used on_any_event,
    which fires on opens, closes, and attribute changes — not just writes.
    When VSCode opens a template, the open event triggers a render; the
    render reads the template via Jinja2, which produces close/access events
    on the same file, which trigger another render, and so on indefinitely.

    The handler must react only to events that indicate content changed
    (modified, created, deleted, moved) and ignore everything else.
    """

    def test_reacts_to_file_modified(self, tmp_path):
        """FileModifiedEvent on a .specd.md file should trigger a render."""
        handler, templates_dir, specs_dir = _capture_watch_handler(tmp_path)
        event = FileModifiedEvent(TEMPLATE_PATH)

        with patch("specd.cli.render_all") as mock_render:
            handler.dispatch(event)
            assert mock_render.call_count == 1

    def test_reacts_to_file_created(self, tmp_path):
        """FileCreatedEvent on a .specd.md file should trigger a render."""
        handler, templates_dir, specs_dir = _capture_watch_handler(tmp_path)
        event = FileCreatedEvent(TEMPLATE_PATH)

        with patch("specd.cli.render_all") as mock_render:
            handler.dispatch(event)
            assert mock_render.call_count == 1

    def test_reacts_to_file_deleted(self, tmp_path):
        """FileDeletedEvent on a .specd.md file should trigger a render."""
        handler, templates_dir, specs_dir = _capture_watch_handler(tmp_path)
        event = FileDeletedEvent(TEMPLATE_PATH)

        with patch("specd.cli.render_all") as mock_render:
            handler.dispatch(event)
            assert mock_render.call_count == 1

    def test_ignores_file_opened(self, tmp_path):
        """FileOpenedEvent must NOT trigger a render (causes infinite loops)."""
        handler, templates_dir, specs_dir = _capture_watch_handler(tmp_path)
        event = FileOpenedEvent(TEMPLATE_PATH)

        with patch("specd.cli.render_all") as mock_render:
            handler.dispatch(event)
            assert mock_render.call_count == 0, (
                "Handler fired on FileOpenedEvent — this causes infinite "
                "re-render loops when an editor opens the template file"
            )

    def test_ignores_file_closed_no_write(self, tmp_path):
        """FileClosedNoWriteEvent must NOT trigger a render."""
        handler, templates_dir, specs_dir = _capture_watch_handler(tmp_path)
        event = FileClosedNoWriteEvent(TEMPLATE_PATH)

        with patch("specd.cli.render_all") as mock_render:
            handler.dispatch(event)
            assert mock_render.call_count == 0, (
                "Handler fired on FileClosedNoWriteEvent — this causes "
                "infinite re-render loops when the template file is read"
            )

    def test_ignores_file_closed(self, tmp_path):
        """FileClosedEvent (close-after-write) should not double-fire.

        A write already produces a FileModifiedEvent, so reacting to the
        subsequent close would cause duplicate renders.
        """
        handler, templates_dir, specs_dir = _capture_watch_handler(tmp_path)
        event = FileClosedEvent(TEMPLATE_PATH)

        with patch("specd.cli.render_all") as mock_render:
            handler.dispatch(event)
            assert mock_render.call_count == 0, (
                "Handler fired on FileClosedEvent — writes already produce "
                "FileModifiedEvent so this causes duplicate renders"
            )

    def test_ignores_dir_modified(self, tmp_path):
        """DirModifiedEvent must NOT trigger a render."""
        handler, templates_dir, specs_dir = _capture_watch_handler(tmp_path)
        event = DirModifiedEvent("/fake/templates/")

        with patch("specd.cli.render_all") as mock_render:
            handler.dispatch(event)
            assert mock_render.call_count == 0, (
                "Handler fired on DirModifiedEvent — directory metadata "
                "changes should not trigger re-renders"
            )

    def test_ignores_non_specd_files(self, tmp_path):
        """Events on non-.specd.md files should be ignored."""
        handler, templates_dir, specs_dir = _capture_watch_handler(tmp_path)
        event = FileModifiedEvent("/fake/templates/notes.md")

        with patch("specd.cli.render_all") as mock_render:
            handler.dispatch(event)
            assert mock_render.call_count == 0
