import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path


TOOLS = ("codex", "claude", "devin")
BEGIN_MARKER = "<!-- ai-quality-knowledge:begin -->"
END_MARKER = "<!-- ai-quality-knowledge:end -->"
MANIFEST_NAME = "manifest.json"
MANIFEST_VERSION = 1
ROUTE_PATTERN = re.compile(r"knowledge/([a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)*\.md)")


class MigrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class InstallationTarget:
    tools: tuple[str, ...]
    instruction_file: Path
    payload_directory: Path
    module_reference_root: str


@dataclass(frozen=True)
class Change:
    action: str
    path: Path


def normalize_tools(tools):
    requested = tuple(dict.fromkeys(tools))
    unknown = sorted(set(requested) - set(TOOLS))
    if unknown:
        raise MigrationError(f"Unknown tools: {', '.join(unknown)}")
    if not requested:
        raise MigrationError("At least one tool is required")
    return tuple(tool for tool in TOOLS if tool in requested)


def resolve_targets(tools, scope, *, home, project, environment=None):
    selected_tools = normalize_tools(tools)
    if scope not in {"user", "project"}:
        raise MigrationError(f"Unknown scope: {scope}")

    home = Path(home).expanduser().absolute()
    project = Path(project).expanduser().absolute()
    environment = os.environ if environment is None else environment
    raw_targets = []

    if scope == "user":
        for tool in selected_tools:
            if tool == "codex":
                config_directory = Path(
                    environment.get("CODEX_HOME", home / ".codex")
                ).expanduser().absolute()
                instruction_file = config_directory / "AGENTS.md"
            elif tool == "claude":
                config_directory = home / ".claude"
                instruction_file = config_directory / "CLAUDE.md"
            else:
                if environment.get("XDG_CONFIG_HOME"):
                    config_directory = (
                        Path(environment["XDG_CONFIG_HOME"]).expanduser().absolute() / "devin"
                    )
                elif environment.get("APPDATA"):
                    config_directory = Path(environment["APPDATA"]).expanduser().absolute() / "devin"
                else:
                    config_directory = home / ".config/devin"
                instruction_file = config_directory / "AGENTS.md"
            payload_directory = config_directory / "ai-quality-knowledge"
            raw_targets.append(
                (
                    tool,
                    instruction_file,
                    payload_directory,
                    (payload_directory / "knowledge").as_posix(),
                )
            )
    else:
        payload_directory = project / ".ai-quality-knowledge"
        for tool in selected_tools:
            instruction_file = project / ("CLAUDE.md" if tool == "claude" else "AGENTS.md")
            raw_targets.append(
                (
                    tool,
                    instruction_file,
                    payload_directory,
                    ".ai-quality-knowledge/knowledge",
                )
            )

    grouped = {}
    for tool, instruction_file, payload_directory, module_reference_root in raw_targets:
        key = (instruction_file, payload_directory, module_reference_root)
        grouped.setdefault(key, []).append(tool)

    return [
        InstallationTarget(tuple(grouped[key]), *key)
        for key in grouped
    ]


def read_source(source_root):
    source_root = Path(source_root).expanduser().absolute()
    router_path = source_root / "AGENTS.md"
    knowledge_directory = source_root / "knowledge"
    if not router_path.is_file():
        raise MigrationError(f"Source router does not exist: {router_path}")
    if not knowledge_directory.is_dir():
        raise MigrationError(f"Source knowledge directory does not exist: {knowledge_directory}")

    router = router_path.read_text(encoding="utf-8")
    modules = {
        path.relative_to(knowledge_directory).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(knowledge_directory.rglob("*.md"))
    }
    if not modules:
        raise MigrationError("Source knowledge directory has no Markdown modules")

    routed_modules = set(ROUTE_PATTERN.findall(router))
    missing_routes = sorted(set(modules) - routed_modules)
    broken_routes = sorted(routed_modules - set(modules))
    if missing_routes:
        raise MigrationError(f"Source modules are not routed: {', '.join(missing_routes)}")
    if broken_routes:
        raise MigrationError(f"Source router has broken routes: {', '.join(broken_routes)}")
    return router, modules


def render_managed_block(router, modules, module_reference_root):
    def replace_route(match):
        module = match.group(1)
        if module not in modules:
            return match.group(0)
        return f"{module_reference_root}/{module}"

    rendered_router = ROUTE_PATTERN.sub(replace_route, router).rstrip()
    resolver = (
        f"Resolve bare module references relative to `{module_reference_root}`. "
        "Read only the modules selected by the router for the current task."
    )
    return f"{BEGIN_MARKER}\n{resolver}\n\n{rendered_router}\n{END_MARKER}"


def split_managed_block(content):
    begin_count = content.count(BEGIN_MARKER)
    end_count = content.count(END_MARKER)
    if begin_count != end_count or begin_count > 1:
        raise MigrationError("Instruction file has malformed AI quality knowledge markers")
    if begin_count == 0:
        return None
    begin = content.index(BEGIN_MARKER)
    end = content.index(END_MARKER, begin) + len(END_MARKER)
    return begin, end


def merge_managed_block(content, block):
    bounds = split_managed_block(content)
    if bounds is None:
        return f"{content.rstrip()}\n\n{block}\n" if content.strip() else f"{block}\n"
    begin, end = bounds
    return f"{content[:begin]}{block}{content[end:]}"


def sha256(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def expected_manifest(router, modules):
    return {
        "schema_version": MANIFEST_VERSION,
        "router_sha256": sha256(router),
        "files": {f"knowledge/{path}": sha256(content) for path, content in modules.items()},
    }


def manifest_content(router, modules):
    return json.dumps(expected_manifest(router, modules), indent=2, sort_keys=True) + "\n"


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as temporary_file:
        temporary_file.write(content)
        temporary_path = Path(temporary_file.name)
    os.replace(temporary_path, path)


def current_text(path):
    return path.read_text(encoding="utf-8") if path.is_file() else None


def plan_write(path, content, changes, dry_run):
    current = current_text(path)
    if current == content:
        return
    changes.append(Change("create" if current is None else "update", path))
    if not dry_run:
        atomic_write(path, content)


def apply_target(target, router, modules, *, dry_run, force):
    changes = []
    instruction_content = current_text(target.instruction_file) or ""
    block = render_managed_block(
        router, modules, target.module_reference_root
    )
    merged_content = merge_managed_block(instruction_content, block)

    manifest_path = target.payload_directory / MANIFEST_NAME
    payload_has_content = target.payload_directory.exists() and any(
        target.payload_directory.iterdir()
    )
    if payload_has_content and not manifest_path.is_file() and not force:
        raise MigrationError(
            f"Unmanaged payload directory requires --force: {target.payload_directory}"
        )

    if instruction_content and instruction_content != merged_content:
        backup_path = target.instruction_file.with_name(
            f"{target.instruction_file.name}.ai-quality-knowledge.bak"
        )
        if BEGIN_MARKER not in instruction_content and not backup_path.exists():
            changes.append(Change("backup", backup_path))
            if not dry_run:
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                backup_path.write_text(instruction_content, encoding="utf-8")

    plan_write(target.instruction_file, merged_content, changes, dry_run)
    for relative_path, content in modules.items():
        plan_write(
            target.payload_directory / "knowledge" / relative_path,
            content,
            changes,
            dry_run,
        )
    plan_write(manifest_path, manifest_content(router, modules), changes, dry_run)
    return changes


def apply_knowledge(
    source_root,
    tools,
    scope,
    *,
    home,
    project,
    environment=None,
    dry_run=False,
    force=False,
):
    router, modules = read_source(source_root)
    changes = []
    for target in resolve_targets(
        tools,
        scope,
        home=home,
        project=project,
        environment=environment,
    ):
        changes.extend(
            apply_target(target, router, modules, dry_run=dry_run, force=force)
        )
    return changes


def check_target(target, router, modules):
    errors = []
    instruction_content = current_text(target.instruction_file)
    if instruction_content is None:
        errors.append(f"Missing instruction file: {target.instruction_file}")
    else:
        try:
            bounds = split_managed_block(instruction_content)
        except MigrationError as error:
            errors.append(f"{target.instruction_file}: {error}")
        else:
            expected_block = render_managed_block(
                router, modules, target.module_reference_root
            )
            if bounds is None:
                errors.append(f"Missing managed router block: {target.instruction_file}")
            else:
                begin, end = bounds
                if instruction_content[begin:end] != expected_block:
                    errors.append(f"Managed router drift: {target.instruction_file}")

    manifest_path = target.payload_directory / MANIFEST_NAME
    expected = expected_manifest(router, modules)
    if not manifest_path.is_file():
        errors.append(f"Missing manifest: {manifest_path}")
    else:
        try:
            actual_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            errors.append(f"Invalid manifest: {manifest_path}")
        else:
            if actual_manifest != expected:
                errors.append(f"Manifest drift: {manifest_path}")

    for relative_path, content in modules.items():
        installed_path = target.payload_directory / "knowledge" / relative_path
        if not installed_path.is_file():
            errors.append(f"Missing payload module: {installed_path}")
        elif sha256(installed_path.read_text(encoding="utf-8")) != sha256(content):
            errors.append(f"Payload drift: {installed_path}")
    return errors


def check_knowledge(
    source_root,
    tools,
    scope,
    *,
    home,
    project,
    environment=None,
):
    router, modules = read_source(source_root)
    errors = []
    for target in resolve_targets(
        tools,
        scope,
        home=home,
        project=project,
        environment=environment,
    ):
        errors.extend(check_target(target, router, modules))
    return errors
