"""
Command-line interface for specd.

Usage:
    specd                                   Print help
    specd render                            Render templates to specs (convention defaults)
    specd render -t PATH -s PATH            Render with explicit directories
    specd render --watch                    Watch templates and re-render on change
    specd validate                          Validate test/spec compliance
    specd validate --tests PATH             Validate with explicit tests directory
    specd resources --list                  List available resource keys and filenames
    specd resources --create                  Create all resource files at current directory
    specd resources --create -t PATH          Create all resource files at PATH
    specd resources --create --only KEY       Create one resource file at current directory
    specd resources --create --only KEY -t PATH  Create one resource file at PATH
    specd resources --create --force          Overwrite existing files
"""

import argparse
import sys
from pathlib import Path

from specd.config import resolve_paths
from specd.render import render_all
from specd.validate import run_validation


class _TrailingNewlineFormatter(argparse.HelpFormatter):
    """HelpFormatter that appends a blank line after the last option."""

    def format_help(self):
        return super().format_help() + "\n"


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
        formatter_class=_TrailingNewlineFormatter,
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

    # Resources subcommand
    resources_parser = subparsers.add_parser(
        "resources",
        help="List or create bundled resource files",
        formatter_class=lambda prog: _TrailingNewlineFormatter(prog, width=120),
    )
    resources_parser.add_argument(
        "--list",
        action="store_true",
        help="List available resource keys and their filenames",
    )
    resources_parser.add_argument(
        "--create",
        action="store_true",
        help="Create resource files in a directory",
    )
    resources_parser.add_argument(
        "--only",
        metavar="KEY",
        help="Create only the named resource (use with --create)",
    )
    resources_parser.add_argument(
        "--target",
        metavar="DIR",
        help="Target directory for --create (default: current working directory)",
    )
    resources_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files when creating",
    )
    # Store reference so _do_resources can print subcommand help.
    resources_parser.set_defaults(_subparser=resources_parser)

    return parser


def _do_render(args):
    paths = resolve_paths(
        templates=args.templates,
        specs=args.specs,
    )
    templates_dir = paths["templates"]
    specs_dir = paths["specs"]

    if not templates_dir.is_dir():
        print("The expected templates dir does not exist")
        return 1

    if not specs_dir.is_dir():
        print("The expected specs dir does not exist")
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
        print("The expected templates dir does not exist")
        return 1

    if not specs_dir.is_dir():
        print("The expected specs dir does not exist")
        return 1

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        print("watchdog is required for --watch mode: pip install watchdog")
        return 1

    class RenderHandler(FileSystemEventHandler):
        def _handle(self, event):
            if not event.is_directory and event.src_path.endswith(".specd.md"):
                relative = Path(event.src_path).relative_to(templates_dir)
                print(f"\nChange detected: {relative}")
                render_all(templates_dir, specs_dir)

        # Only save-related events trigger a re-render
        on_modified = _handle
        on_created = _handle

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


def _do_resources(args):
    from pathlib import Path

    from specd._resources import RESOURCES, read_resource

    # Options that require --create
    if args.target and not args.create:
        print("--target can only be used with --create")
        return 1

    if args.force and not args.create:
        print("--force can only be used with --create")
        return 1

    if args.only and not args.create:
        print("--only can only be used with --create")
        return 1

    # Bare invocation: no flags set.
    if not args.list and not args.create:
        args._subparser.print_help()
        return 0

    # --list (must not be combined with other options)
    if args.list:
        if args.create or args.only or args.target or args.force:
            print("The --list option can't be combined with other options")
            return 1
        for key, filename in RESOURCES.items():
            print(f"{key}: {filename}")
        return 0

    # --create
    target = Path(args.target) if args.target else Path.cwd()

    if not target.is_dir():
        print(f"The target directory does not exist. Create it first.")
        print(f"The target was {target}")
        return 1

    if args.only:
        if args.only not in RESOURCES:
            print(f"Unknown resource key: '{args.only}'. Use --list to get the correct keys.")
            return 1
        to_copy = {args.only: RESOURCES[args.only]}
    else:
        to_copy = RESOURCES

    if not args.force:
        conflicts = [
            filename for filename in to_copy.values()
            if (target / filename).exists()
        ]
        if conflicts:
            print("\nThe following files already exist in the target directory:")
            for filename in conflicts:
                print(f"- {filename}")
            print("Use --force to overwrite them.\n")
            return 1

    created = []
    for filename in to_copy.values():
        content = read_resource(filename)
        # write_bytes to preserve \n line endings on all platforms
        (target / filename).write_bytes(content.encode("utf-8"))
        if args.target:
            created.append(str(target / filename))
        else:
            created.append(filename)

    print("The following were created:")
    for path_display in created:
        print(f"- {path_display}")

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
    elif args.command == "resources":
        sys.exit(_do_resources(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
