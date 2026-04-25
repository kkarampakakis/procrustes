# ------------------------------------------------------------------------------------------
# __main__
# ------------------------------------------------------------------------------------------

import argparse

from .commands import (
    inquire,
    resume,
    open_settings,
    reset,
)

# ------------------------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="procrustes",
        description="Procrustes: An LLM-assisted tool for structured PDF inquiry.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "inquire",
        help="Start a new PDF inquiry.",
    )

    subparsers.add_parser(
        "resume",
        help="Resume from the saved pickle.",
    )

    subparsers.add_parser(
        "open-settings",
        help="Open settings.toml.",
    )

    subparsers.add_parser(
        "reset",
        help="Reset settings.toml from default_settings.toml.",
    )

    args = parser.parse_args()

    if args.command == "inquire":
        inquire()

    elif args.command == "resume":
        resume()

    elif args.command == "open-settings":
        open_settings()

    elif args.command == "reset":
        reset()

# ------------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()

# ------------------------------------------------------------------------------------------
