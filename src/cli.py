"""AutoDocker CLI entry point."""

import argparse
import logging
import sys

from .commands import cmd_build, cmd_info, cmd_list, cmd_remove, cmd_run
from .setup import ensure_autodocker_dir


def _configure_logging() -> None:
    """Set up logging to print clean messages to stdout."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )


def _build_parser() -> argparse.ArgumentParser:
    """Construct and return the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="autodocker",
        description="Build and run GitHub repos inside Docker containers.",
    )

    subparsers = parser.add_subparsers(dest="command")

    # --- build ---
    build_parser = subparsers.add_parser(
        "build", help="Clone a GitHub repo and build a Docker image from it."
    )
    build_parser.add_argument("url", help="GitHub repository URL.")
    build_parser.add_argument(
        "--name", "-n", dest="name", default=None,
        help="Custom name for the Docker image.",
    )

    # --- list ---
    subparsers.add_parser("list", help="List AutoDocker-managed images.")

    # --- remove ---
    remove_parser = subparsers.add_parser("remove", help="Remove an AutoDocker image.")
    remove_parser.add_argument("image_name", help="Name of the image to remove.")

    # --- info ---
    info_parser = subparsers.add_parser("info", help="Show info about an AutoDocker image.")
    info_parser.add_argument("image_name", help="Name of the image to inspect.")

    # --- run ---
    run_parser = subparsers.add_parser(
        "run", help="Run a script inside an AutoDocker image."
    )
    run_parser.add_argument("image_name", help="Name of the Docker image.")
    run_parser.add_argument(
        "script_args", nargs=argparse.REMAINDER,
        help="Script filename and optional arguments.",
    )

    return parser


def _is_url(value: str) -> bool:
    """Return True if the string looks like a repository URL."""
    return value.startswith(("https://", "http://", "git@", "git://"))


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate command."""
    _configure_logging()
    ensure_autodocker_dir()

    # Shorthand: inject 'build' before argparse sees argv so it never
    # tries to match the URL as a subcommand name.
    if len(sys.argv) >= 2 and _is_url(sys.argv[1]):
        sys.argv.insert(1, "build")

    parser = _build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "build":
        cmd_build(args.url, custom_name=args.name)
    elif args.command == "list":
        cmd_list()
    elif args.command == "remove":
        cmd_remove(args.image_name)
    elif args.command == "info":
        cmd_info(args.image_name)
    elif args.command == "run":
        cmd_run(args.image_name, args.script_args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()