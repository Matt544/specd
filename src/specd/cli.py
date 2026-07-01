"""
Command-line interface for specd.

Usage:
    specd                                   Print help
    specd render                            Render templates to specs (convention defaults)
    specd render -t PATH -s PATH            Render with explicit directories
    specd render --watch                    Watch templates and re-render on change
    specd validate                          Validate test/spec compliance
    specd validate --tests PATH             Validate with explicit tests directory
    specd policies --list                   List available policy keys and filenames
    specd policies --copy                   Copy all policy files to current directory
    specd policies --copy -t PATH           Copy all policy files to PATH
    specd policies --copy --only KEY        Copy one policy file to current directory
    specd policies --copy --only KEY -t PATH  Copy one policy file to PATH
    specd policies --copy --force           Overwrite existing files
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

    # Policies subcommand
    policies_parser = subparsers.add_parser(
        "policies",
        help="List or copy bundled policy template files",
    )
    policies_parser.add_argument(
        "--list",
        action="store_true",
        help="List available policy keys and their filenames",
    )
    policies_parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy policy files into a directory",
    )
    policies_parser.add_argument(
        "--only",
        metavar="KEY",
        help="Copy only the named policy (use with --copy)",
    )
    policies_parser.add_argument(
        "-t", "--target",
        metavar="DIR",
        help="Target directory for --copy (default: current working directory)",
    )
    policies_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files when copying",
    )
    # Store reference so _do_policies can print subcommand help.
    policies_parser.set_defaults(_subparser=policies_parser)

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
        def _handle(self, event):
            if not event.is_directory and event.src_path.endswith(".specd.md"):
                print(f"\nChange detected: {event.src_path}")
                render_all(templates_dir, specs_dir)

        on_modified = _handle
        on_created = _handle
        on_deleted = _handle
        on_moved = _handle

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


def _do_policies(args):
    import importlib.resources
    from pathlib import Path

    from specd._policies import POLICIES

    # Bare invocation: no flags set.
    if not args.list and not args.copy and not args.only:
        args._subparser.print_help()
        return 0

    # --only without --copy is an error.
    if args.only and not args.copy:
        print("Error: --only requires --copy.")
        print("Usage: specd policies --copy --only KEY")
        return 1

    # --list
    if args.list:
        for key, filename in POLICIES.items():
            print(f"{key}: {filename}")
        return 0

    # --copy
    target = Path(args.target) if args.target else Path.cwd()

    if not target.is_dir():
        print(f"Target directory does not exist: {target}")
        print("Create it first, then re-run.")
        return 1

    if args.only:
        if args.only not in POLICIES:
            print(f"Unknown policy key: '{args.only}'")
            print(f"Valid keys: {', '.join(POLICIES)}")
            return 1
        to_copy = {args.only: POLICIES[args.only]}
    else:
        to_copy = POLICIES

    if not args.force:
        conflicts = [
            filename for filename in to_copy.values()
            if (target / filename).exists()
        ]
        if conflicts:
            print("The following files already exist in the target directory:")
            for filename in conflicts:
                print(f"  {filename}")
            print("Use --force to overwrite.")
            return 1

    policies_dir = importlib.resources.files("specd") / "policies"
    for filename in to_copy.values():
        content = (policies_dir / filename).read_bytes()
        (target / filename).write_bytes(content)

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
    elif args.command == "policies":
        sys.exit(_do_policies(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
