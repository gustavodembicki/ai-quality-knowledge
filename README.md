# AI Quality Knowledge

A vendor-neutral quality contract for AI coding agents, with safe adapters for Codex, Claude Code, and Devin CLI.

## Intent

This repository gives AI agents a consistent way to produce reliable software work without loading a large instruction set into every session. It is designed to:

- Gather enough material context before implementation without blocking on irrelevant questions.
- Prefer concise answers while making deeper rationale, risks, alternatives, and evidence available on request.
- Apply test-first development where meaningful and require regression validation.
- Encourage cohesive architecture, focused changes, safe Git/GitHub workflows, and evidence-based review.
- Separate facts, assumptions, inferences, unknowns, and verification results.
- Preserve existing project and user instructions during migration between supported CLIs.

It intentionally contains no company, repository, or domain-specific guidance. Repository-local rules remain authoritative for project-specific behavior.

## How context stays small

[`AGENTS.md`](AGENTS.md) is the always-on router. It contains only the shared contract, session working-set protocol, precedence rules, and a routing table.

For each request, the agent should load only the relevant files from [`knowledge/`](knowledge/):

| Module | Loaded for |
|---|---|
| [`context.md`](knowledge/context.md) | Ambiguity, planning, specifications, and long sessions |
| [`output.md`](knowledge/output.md) | Brief, compact, standard, or detailed response control |
| [`coding.md`](knowledge/coding.md) | Architecture, implementation, refactoring, and debugging |
| [`testing.md`](knowledge/testing.md) | TDD, regression coverage, and verification |
| [`reviewing.md`](knowledge/reviewing.md) | Code, branch, patch, and pull-request review |
| [`github.md`](knowledge/github.md) | Git, commits, branches, pull requests, and CI |
| [`grill-me.md`](knowledge/grill-me.md) | Explicit one-question-at-a-time design interrogation |

The router instructs the agent to maintain a minimal session brief, reuse already loaded guidance, and stop relying on irrelevant context when the task changes. It does not claim that an LLM can erase tokens already loaded into its context window.

## Requirements

- Python `3.14.6`, pinned in [`.tool-versions`](.tool-versions).
- No third-party Python packages.
- A supported CLI only when installing the adapter for that CLI.

With asdf installed:

```bash
asdf install
```

## Validate the repository

Run the complete test suite and knowledge validator:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_knowledge.py .
```

The validator checks required modules, router coverage, broken or orphaned routes, Markdown structure, UTF-8, router size, tool-exclusive source configuration, personal absolute paths, and likely credentials.

## Preview an installation

Always preview changes first:

```bash
python3 scripts/apply_knowledge.py \
  --tool all \
  --scope user \
  --dry-run
```

Choose one tool with `--tool codex`, `--tool claude`, or `--tool devin`.

## Install for the current user

Install globally for all supported CLIs:

```bash
python3 scripts/apply_knowledge.py --tool all --scope user
```

Native destinations are used:

| Tool | Global instruction file | Managed payload |
|---|---|---|
| Codex | `$CODEX_HOME/AGENTS.md`, defaulting to `~/.codex/AGENTS.md` | `$CODEX_HOME/ai-quality-knowledge/` |
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/ai-quality-knowledge/` |
| Devin CLI | `$XDG_CONFIG_HOME/devin/AGENTS.md`, defaulting to `~/.config/devin/AGENTS.md` | The adjacent `ai-quality-knowledge/` directory |

On Windows, Devin uses `%APPDATA%/devin/` when `XDG_CONFIG_HOME` is not set.

## Install in a project

Preview project-local changes:

```bash
python3 scripts/apply_knowledge.py \
  --tool all \
  --scope project \
  --project /path/to/project \
  --dry-run
```

Apply them:

```bash
python3 scripts/apply_knowledge.py \
  --tool all \
  --scope project \
  --project /path/to/project
```

Project destinations:

- Codex and Devin share `<project>/AGENTS.md`.
- Claude uses `<project>/CLAUDE.md`.
- All three share `<project>/.ai-quality-knowledge/` for copied neutral modules.

Using one shared payload avoids conflicting or duplicated knowledge while each CLI receives its native bootstrap file.

## Check an installation

Check user-global adapters:

```bash
python3 scripts/check_knowledge.py --tool all --scope user
```

Check a project installation:

```bash
python3 scripts/check_knowledge.py \
  --tool all \
  --scope project \
  --project /path/to/project
```

The check fails when a managed router, manifest, or module is missing, corrupted, or different from this repository.

## Update installed knowledge

After updating this repository, preview and reapply:

```bash
git pull
python3 scripts/apply_knowledge.py --tool all --scope user --dry-run
python3 scripts/apply_knowledge.py --tool all --scope user
python3 scripts/check_knowledge.py --tool all --scope user
```

Apply and check project scope separately when project-local adapters are used.

## Migration safety

[`apply_knowledge.py`](scripts/apply_knowledge.py) and [`knowledge_adapters.py`](scripts/knowledge_adapters.py) are designed to be repeatable and conservative:

- Existing instruction files are preserved outside a managed marker block.
- The original instruction file is backed up before the first managed modification.
- Reapplying replaces only managed content and does not overwrite the original backup.
- Writes are atomic.
- SHA-256 manifests detect source or installed-content drift.
- Codex and Devin project installs are deduplicated automatically.
- `--dry-run` performs no writes.
- A non-empty payload directory without a migration manifest is rejected.
- `--force` adopts such a directory but does not delete its unknown files.
- Malformed or duplicate managed markers stop migration instead of guessing.

Review the dry-run output before using `--force`.

## Response modes

Compact output is the default. A requester can explicitly select:

- `brief` — answer only, with a caveat when omission would mislead.
- `compact` — outcome, essential evidence, material caveat, and next action.
- `standard` — short rationale, main trade-offs, evidence, and next steps.
- `detailed` — context, reasoning, alternatives, edge cases, evidence, and operational concerns as relevant.

For non-trivial compact responses, the agent should offer an unobtrusive way to request rationale, risks, alternatives, or full evidence.

## Development and CI

Tests live under [`tests/`](tests/) and use only Python's standard library. GitHub Actions runs them on pushes, pull requests, and manual dispatch through [`.github/workflows/validate.yml`](.github/workflows/validate.yml).

The CI job:

1. Reads the exact Python version from `.tool-versions`.
2. Runs all unit and integration tests.
3. Validates the real knowledge repository.

## Non-goals

This repository does not:

- Replace repository-local architecture, style, security, or contribution rules.
- Install MCP servers, credentials, hooks, plugins, or permissions.
- Automatically modify real user configuration merely by being cloned.
- Preload every knowledge module into every session.
- Guarantee that a CLI will obey an instruction it cannot access; use the check script after installation and verify behavior in the target CLI when upgrading it.
