# Reviewing Changes

## Scope and safety

- Establish the exact repository, branch or change range, intended behavior, base, and applicable rules. Ask rather than silently choosing a materially ambiguous target.
- Default to read-only review. Do not modify code, branches, commits, remotes, or external systems unless the user separately requests fixes.
- Inspect the complete diff and all relevant commits plus working-tree changes; do not review only the latest commit.

## Review workflow

1. Understand the requirement, acceptance criteria, constraints, and behavior that must remain unchanged.
2. Read changed files in context and trace affected symbols through callers, consumers, tests, interfaces, configuration, data, and operational paths.
3. Compare sibling implementations and established patterns without treating style preference as correctness.
4. Run relevant non-mutating checks when practical.
5. Distinguish observed evidence, reasoned risk, and missing information.

## Risk lenses

Apply proportionately:

- Correctness, edge cases, error paths, partial failure, and state transitions.
- Security, authorization, validation, secrets, privacy, and unsafe inputs/outputs.
- Data integrity, schema/cardinality/null/order assumptions, transactions, migrations, backfills, retries, and idempotency.
- Compatibility across public APIs, serialization, supported versions, callers, and rollout states.
- Architecture: ownership, cohesion, coupling, dependency direction, duplication, leaky boundaries, and speculative abstractions.
- Dependencies: declared/locked version, actual API guarantees, lifecycle, timeouts, retries, cleanup, and responsibility boundaries.
- Resources: bounded work and memory, concurrency, cancellation, ordering, backpressure, rate/connection limits, leaks, and failure isolation.
- Renames/moves: imports, dynamic or string references, registration/discovery, case sensitivity, generated artifacts, and stale files.
- Operations: logging/metrics without sensitive data, deployment, migration, rollback, recovery, and supportability.
- Tests: meaningful changed behavior, defect reproduction, boundaries/failures, and regression coverage for preserved behavior.

If schemas, workload facts, external guarantees, or acceptance criteria are unavailable, identify the gap; do not invent details.

## Findings

Report actionable findings first, ordered by severity:

- **BLOCKER:** likely security breach, data loss, or fundamentally unsafe release.
- **HIGH:** likely correctness failure or significant regression in realistic use.
- **MEDIUM:** concrete defect or maintainability risk with bounded impact.
- **LOW:** worthwhile improvement with minor concrete impact.

Each finding includes location, impact, evidence/reasoning, and a remediation direction. Avoid praise, summaries, and style-only opinions before findings. Do not inflate severity to compensate for uncertainty.

Finish with checks performed, verification gaps, assumptions/questions, and a concise verdict. If no actionable findings exist, say so explicitly while disclosing residual risk and unrun checks. Offer full evidence on request.
