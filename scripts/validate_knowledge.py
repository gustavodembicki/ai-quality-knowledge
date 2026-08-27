#!/usr/bin/env python3

import re
import sys
from pathlib import Path


REQUIRED_MODULES = (
    "context.md",
    "continuity.md",
    "output.md",
    "coding.md",
    "testing.md",
    "reviewing.md",
    "github.md",
    "grill-me.md",
)
EXCLUSIVE_AGENT_ENTRIES = (
    ".agents",
    ".claude",
    ".cursor",
    ".devin",
    ".windsurf",
    "CLAUDE.md",
)
MAX_ROUTER_LINES = 100
ROUTE_PATTERN = re.compile(r"knowledge/[a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)*\.md")
PLACEHOLDER_USER_NAMES = r"(?:example|user|username|yourname)"
ABSOLUTE_USER_PATH_PATTERN = re.compile(
    rf"""
    (?:^|[\s`('\"])
    (?:
        /Users/(?!{PLACEHOLDER_USER_NAMES}(?:/|[\s`'\"]|$))[^/\s`'\"]+
        |/home/(?!{PLACEHOLDER_USER_NAMES}(?:/|[\s`'\"]|$))[^/\s`'\"]+
        |[A-Za-z]:\\Users\\(?!{PLACEHOLDER_USER_NAMES}(?:\\|[\s`'\"]|$))[^\\\s`'\"]+
    )
    """,
    re.MULTILINE | re.VERBOSE,
)
CREDENTIAL_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),
    re.compile(
        r"\b(?:api[_-]?key|access[_-]?key|token|password|secret)\s*[:=]\s*[\"']?[A-Za-z0-9/+_.=-]{16,}",
        re.IGNORECASE,
    ),
)


def read_text(path, errors):
    if not path.is_file():
        errors.append(f"Missing required file: {path.name}")
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append(f"File is not valid UTF-8: {path.relative_to(path.parent.parent)}")
        return None


def validate_heading(path, text, errors, root):
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    if not first_line.startswith("# "):
        errors.append(f"Markdown file lacks a top-level heading: {path.relative_to(root)}")


def validate_repository(root):
    root = Path(root).resolve()
    errors = []

    for entry in EXCLUSIVE_AGENT_ENTRIES:
        if (root / entry).exists():
            errors.append(f"Exclusive agent configuration is not allowed: {entry}")
    for skill_file in root.rglob("SKILL.md"):
        if ".git" not in skill_file.parts:
            errors.append(f"Exclusive agent skill is not allowed: {skill_file.relative_to(root)}")

    tool_versions = read_text(root / ".tool-versions", errors)
    if tool_versions is not None and not re.search(
        r"^python\s+\d+\.\d+\.\d+\s*$", tool_versions, re.MULTILINE
    ):
        errors.append(".tool-versions must pin Python to an exact semantic version")

    router_path = root / "AGENTS.md"
    router = read_text(router_path, errors)
    knowledge_directory = root / "knowledge"
    if not knowledge_directory.is_dir():
        errors.append("Missing required directory: knowledge")
        module_paths = []
    else:
        module_paths = sorted(knowledge_directory.rglob("*.md"))

    documents = []
    routes = set()
    for module in REQUIRED_MODULES:
        relative_path = f"knowledge/{module}"
        if not (root / relative_path).is_file():
            errors.append(f"Missing required module: {relative_path}")

    if router is not None:
        documents.append((router_path, router))
        validate_heading(router_path, router, errors, root)
        if len(router.splitlines()) > MAX_ROUTER_LINES:
            errors.append(
                f"Router exceeds {MAX_ROUTER_LINES} lines; move detail into a lazily loaded module"
            )

        routes = set(ROUTE_PATTERN.findall(router))
        for module in REQUIRED_MODULES:
            relative_path = f"knowledge/{module}"
            if relative_path not in routes:
                errors.append(f"Required module is not routed by AGENTS.md: {relative_path}")
        for route in routes:
            if not (root / route).is_file():
                errors.append(f"Broken module route in AGENTS.md: {route}")

    for path in module_paths:
        relative_path = path.relative_to(root).as_posix()
        if relative_path not in routes:
            errors.append(f"Orphan module is not routed by AGENTS.md: {relative_path}")

    for path in module_paths:
        text = read_text(path, errors)
        if text is not None:
            documents.append((path, text))
            validate_heading(path, text, errors, root)

    for path, text in documents:
        relative_path = path.relative_to(root)
        if ABSOLUTE_USER_PATH_PATTERN.search(text):
            errors.append(f"Absolute user path found in portable knowledge: {relative_path}")
        if any(pattern.search(text) for pattern in CREDENTIAL_PATTERNS):
            errors.append(f"Likely credential found in portable knowledge: {relative_path}")

    return errors


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    root = Path(arguments[0] if arguments else ".")
    errors = validate_repository(root)
    if errors:
        print("Knowledge validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Knowledge validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
