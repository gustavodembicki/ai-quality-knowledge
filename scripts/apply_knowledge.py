#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path

from knowledge_adapters import MigrationError, TOOLS, apply_knowledge


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(
        description="Apply the neutral AI quality knowledge pack to supported CLI instruction files."
    )
    parser.add_argument(
        "--tool",
        choices=("all", *TOOLS),
        default="all",
        help="Target one CLI or all supported CLIs (default: all).",
    )
    parser.add_argument(
        "--scope",
        choices=("user", "project"),
        default="user",
        help="Install globally for one user or locally in a project (default: user).",
    )
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Adopt an existing unmanaged payload directory without deleting its files.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    arguments = parse_arguments(argv)
    tools = TOOLS if arguments.tool == "all" else (arguments.tool,)
    try:
        changes = apply_knowledge(
            arguments.source,
            tools,
            arguments.scope,
            home=arguments.home,
            project=arguments.project,
            environment=os.environ,
            dry_run=arguments.dry_run,
            force=arguments.force,
        )
    except (MigrationError, OSError, UnicodeError) as error:
        print(f"Migration failed: {error}", file=sys.stderr)
        return 1

    if not changes:
        print("Knowledge installation is already current")
        return 0
    prefix = "Would" if arguments.dry_run else "Did"
    for change in changes:
        print(f"{prefix} {change.action}: {change.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
