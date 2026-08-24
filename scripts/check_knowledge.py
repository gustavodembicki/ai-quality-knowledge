#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path

from knowledge_adapters import MigrationError, TOOLS, check_knowledge


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(
        description="Check installed AI quality knowledge adapters for missing or drifted content."
    )
    parser.add_argument(
        "--tool",
        choices=("all", *TOOLS),
        default="all",
        help="Check one CLI or all supported CLIs (default: all).",
    )
    parser.add_argument(
        "--scope",
        choices=("user", "project"),
        default="user",
        help="Check a user-global or project-local installation (default: user).",
    )
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--project", type=Path, default=Path.cwd())
    return parser.parse_args(argv)


def main(argv=None):
    arguments = parse_arguments(argv)
    tools = TOOLS if arguments.tool == "all" else (arguments.tool,)
    try:
        errors = check_knowledge(
            arguments.source,
            tools,
            arguments.scope,
            home=arguments.home,
            project=arguments.project,
            environment=os.environ,
        )
    except (MigrationError, OSError, UnicodeError) as error:
        print(f"Adapter check failed: {error}", file=sys.stderr)
        return 1

    if errors:
        print("Knowledge adapter check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Knowledge adapters are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
