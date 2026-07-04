"""
Tests for render --watch mode: blocking behavior, trigger conditions, and output format.
"""

import subprocess
import sys
import time
from pathlib import Path

SPECD = [sys.executable, "-m", "specd.cli"]

# -u disables stdout/stderr buffering so output is captured before process termination
SPECD_UNBUFFERED = [sys.executable, "-u", "-m", "specd.cli"]

# Generous delays to account for watchdog startup and event propagation across platforms
WATCHER_STARTUP_DELAY = 1.5
EVENT_PROPAGATION_DELAY = 1.5


def _start_watch(templates_dir, specs_dir, flag="-w"):
    """Start specd render in watch mode as a background process and return Popen."""
    return subprocess.Popen(
        SPECD_UNBUFFERED + ["render", "-t", str(templates_dir), "-s", str(specs_dir), flag],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


class TestWatchBlocking:

    def test_watch_flag_is_blocking(self, tmp_path):
        """
        Spec: Calling `render` with `--watch` or `-w` occupies the terminal with a blocking file watcher that runs until the process is interrupted [render.md]
        """
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()

        process = _start_watch(templates_dir, specs_dir, flag="--watch")
        try:
            time.sleep(WATCHER_STARTUP_DELAY)
            assert process.poll() is None, "Watch process exited unexpectedly"
        finally:
            process.terminate()
            process.communicate(timeout=5)

    def test_w_flag_is_blocking(self, tmp_path):
        """
        Spec: Calling `render` with `--watch` or `-w` occupies the terminal with a blocking file watcher that runs until the process is interrupted [render.md]
        """
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()

        process = _start_watch(templates_dir, specs_dir, flag="-w")
        try:
            time.sleep(WATCHER_STARTUP_DELAY)
            assert process.poll() is None, "Watch process exited unexpectedly"
        finally:
            process.terminate()
            process.communicate(timeout=5)


class TestWatchTriggers:

    def test_watch_triggers_on_template_save(self, tmp_path):
        """
        Spec: When called with `--watch` or `-w`, the saving of any template triggers template rendering as though `render` were called [render.md]
        """
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()

        template = templates_dir / "foo.specd.md"
        template.write_text("# Foo\n\n- original\n", encoding="utf-8")

        process = _start_watch(templates_dir, specs_dir)
        try:
            time.sleep(WATCHER_STARTUP_DELAY)

            # Save the template with updated content
            template.write_text("# Foo\n\n- updated\n", encoding="utf-8")
            time.sleep(EVENT_PROPAGATION_DELAY)

            content = (specs_dir / "foo.md").read_text(encoding="utf-8")
            assert "updated" in content
        finally:
            process.terminate()
            process.communicate(timeout=5)

    def test_watch_triggers_on_template_creation(self, tmp_path):
        """
        Spec: When called with `--watch` or `-w`, the saving of any template triggers template rendering as though `render` were called [render.md]
        """
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()

        process = _start_watch(templates_dir, specs_dir)
        try:
            time.sleep(WATCHER_STARTUP_DELAY)

            # Creating a new template file is a save event
            (templates_dir / "new.specd.md").write_text(
                "# New\n\n- new item\n", encoding="utf-8"
            )
            time.sleep(EVENT_PROPAGATION_DELAY)

            assert (specs_dir / "new.md").exists()
        finally:
            process.terminate()
            process.communicate(timeout=5)


class TestWatchNonTrigger:

    def test_watch_no_trigger_on_non_save_event(self, tmp_path):
        """
        Spec: When called with `--watch` or `-w`, non-save-related events on a template do not trigger template rendering [render.md]
        """
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()

        template = templates_dir / "foo.specd.md"
        template.write_text("# Foo\n\n- item\n", encoding="utf-8")

        process = _start_watch(templates_dir, specs_dir)
        try:
            time.sleep(WATCHER_STARTUP_DELAY)

            # Deletion is a non-save event on the template
            template.unlink()
            time.sleep(EVENT_PROPAGATION_DELAY)

            process.terminate()
            stdout, _ = process.communicate(timeout=5)
        except Exception:
            process.kill()
            process.communicate()
            raise

        # Deletion should not trigger rendering; no "Change detected:" line expected
        assert "Change detected:" not in stdout


class TestWatchOutput:

    def test_watch_output_preceded_by_change_detected_line(self, tmp_path):
        """
        Spec: When called with `--watch` or `-w`, and when rendering is triggered, the normal `render` output is preceded by `Change detected: <path to changed file from templates dir>\\n` [render.md]
        """
        templates_dir = tmp_path / "templates"
        specs_dir = tmp_path / "specs"
        templates_dir.mkdir()
        specs_dir.mkdir()

        template = templates_dir / "foo.specd.md"
        template.write_text("# Foo\n\n- original\n", encoding="utf-8")

        process = _start_watch(templates_dir, specs_dir)
        try:
            time.sleep(WATCHER_STARTUP_DELAY)

            template.write_text("# Foo\n\n- updated\n", encoding="utf-8")
            time.sleep(EVENT_PROPAGATION_DELAY)

            process.terminate()
            stdout, _ = process.communicate(timeout=5)
        except Exception:
            process.kill()
            process.communicate()
            raise

        # Path is relative to the templates directory — just the filename
        assert "Change detected: foo.specd.md" in stdout

        # The change-detected line appears before the per-template render line
        lines = stdout.splitlines()
        change_line_idx = next(
            i for i, line in enumerate(lines) if "Change detected:" in line
        )
        render_line_idx = next(
            i for i, line in enumerate(lines) if "foo.specd.md ->" in line
        )
        assert change_line_idx < render_line_idx
