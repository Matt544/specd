"""
Command-line interface for specd.

Usage:
    specd                         Print help
    specd render                  Render templates to specs (convention defaults)
    specd render -t PATH -s PATH  Render with explicit directories
    specd render --watch          Watch templates and re-render on change
    specd validate                Validate test/spec compliance
    specd validate --tests PATH   Validate with explicit tests directory
"""

import argparse
import sys

from specd.config import resolve_paths
from specd.render import render_all
from specd.validate import run_validation


def _add_path_flags(parser):
    """Add the -t/--templates and -s/--specs flags to a parser."""
    parser.add_argument(
        "-t", "--templates",
        help="Path to the templates directory",
    )
    parser.add_argument(
        "-s", "--specs",
        help="Path to the specs output directory",
    )


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="specd",
        description="Render Jinja2 spec templates and validate test/spec compliance.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Render subcommand
    render_parser = subparsers.add_parser(
        "render",
        help="Render *.specd.md templates into spec files",
    )
    _add_path_flags(render_parser)
    render_parser.add_argument(
        "-w", "--watch",
        action="store_true",
        help="Watch templates for changes and re-render automatically",
    )

    # Validate subcommand
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate test/spec citation compliance",
    )
    _add_path_flags(validate_parser)
    validate_parser.add_argument(
        "--tests",
        help="Path to the tests directory",
    )

    return parser


def _do_render(args):
    paths = resolve_paths(
        templates=args.templates,
        specs=args.specs,
    )
    templates_dir = paths["templates"]
    specs_dir = paths["specs"]

    if not templates_dir.is_dir():
        print(f"Templates directory not found: {templates_dir}")
        return 1

    if not specs_dir.is_dir():
        print(f"Specs directory not found: {specs_dir}")
        return 1

    render_all(templates_dir, specs_dir)
    return 0


def _do_watch(args):
    paths = resolve_paths(
        templates=args.templates,
        specs=args.specs,
    )
    templates_dir = paths["templates"]
    specs_dir = paths["specs"]

    if not templates_dir.is_dir():
        print(f"Templates directory not found: {templates_dir}")
        return 1

    if not specs_dir.is_dir():
        print(f"Specs directory not found: {specs_dir}")
        return 1

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        print("watchdog is required for --watch mode: pip install watchdog")
        return 1

    class RenderHandler(FileSystemEventHandler):
        def on_any_event(self, event):
            if event.src_path.endswith(".specd.md"):
                print(f"\nChange detected: {event.src_path}")
                render_all(templates_dir, specs_dir)

    # Do an initial render before watching
    render_all(templates_dir, specs_dir)

    observer = Observer()
    observer.schedule(RenderHandler(), str(templates_dir), recursive=True)
    observer.start()
    print(f"\nWatching {templates_dir} for changes... (Ctrl+C to stop)")

    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopped watching.")

    observer.join()
    return 0


def _do_validate(args):
    paths = resolve_paths(
        templates=args.templates,
        specs=args.specs,
        tests=args.tests,
    )
    specs_dir = paths["specs"]
    tests_dir = paths["tests"]

    if not specs_dir.is_dir():
        print(f"Specs directory not found: {specs_dir}")
        return 1

    if not tests_dir.is_dir():
        print(f"Tests directory not found: {tests_dir}")
        return 1

    return run_validation(specs_dir, tests_dir)


def main():
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "render":
        if args.watch:
            sys.exit(_do_watch(args))
        else:
            sys.exit(_do_render(args))
    elif args.command == "validate":
        sys.exit(_do_validate(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
