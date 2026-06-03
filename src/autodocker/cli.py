"""AutoDocker CLI entry point."""

import argparse
import logging
import sys

from autodocker.commands import cmd_build, cmd_info, cmd_list, cmd_remove, cmd_run


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
        description="Build and run Python GitHub repos inside Docker containers.",
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


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate command."""
    _configure_logging()

    parser = _build_parser()

    # Support shorthand: autodocker <url> [-n name]  (no explicit 'build' subcommand)
    args, unknown = parser.parse_known_args()

    if args.command is None:
        # Check if the first positional argument looks like a URL
        remaining = sys.argv[1:]
        if remaining and (
            remaining[0].startswith("https://")
            or remaining[0].startswith("http://")
            or remaining[0].startswith("git@")
        ):
            # Re-parse with 'build' injected
            sys.argv.insert(1, "build")
            args = parser.parse_args()
        else:
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
