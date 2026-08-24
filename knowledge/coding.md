# Coding and Architecture

Load `testing.md` with this module for behavioral changes.

## Intent gate

Before changing behavior, state at most four concise bullets:

- **Intent:** user-visible or system outcome.
- **Expected behavior:** success, edge cases, and behavior that must remain unchanged.
- **Evidence:** tests and checks that will prove it.
- **Assumptions:** only material assumptions.

Do not implement while a material ambiguity remains.

## Explore before editing

- Read applicable rules, dependencies, neighboring code, callers, consumers, tests, and analogous implementations.
- Reproduce a bug before fixing it. Trace the real path and identify the root cause rather than treating symptoms.
- Verify libraries, APIs, versions, defaults, lifecycle, and failure semantics from local declarations or authoritative documentation. Never infer guarantees from a package name.
- Preserve established conventions unless changing them is explicitly part of the requirement.

## Construction principles

- Implement the smallest complete change that satisfies the contract; avoid unrelated cleanup and speculative features.
- Keep responsibilities cohesive, ownership singular, boundaries explicit, dependencies directed, and coupling low.
- Reuse an existing abstraction when its responsibility and change driver match. Do not duplicate behavior, but do not force unrelated concepts behind a shared abstraction.
- Prefer simple data flow and explicit contracts over hidden global state, action at a distance, parameter sprawl, stringly typed protocols, and cleverness.
- Separate domain policy from transport, persistence, framework, and presentation concerns where the distinction is real.
- Encapsulate volatility at boundaries. Keep pure decision logic separate from side effects when practical.
- Comments explain non-obvious constraints or rationale, not what clearly named code already says.
- Optimize only with evidence, while preventing obvious unbounded work, repeated I/O, N+1 behavior, leaks, and hot-path blocking.

## System qualities

Evaluate in proportion to risk:

- Compatibility and public contracts.
- Validation, authorization, secrets, and data exposure.
- Data integrity, transactions, idempotency, retries, and partial failure.
- Timeouts, cancellation, cleanup, bounded memory/work, backpressure, ordering, and concurrency limits.
- Observability, supportability, feature rollout, migration, rollback, and recovery.

For schema or data changes, verify the actual engine, dialect, schema, keys, nullability, cardinality, indexes/partitions, transaction behavior, migration registration, backfill, and downstream consumers.

## Change discipline

- Keep the diff focused and preserve user-authored work.
- Avoid new dependencies unless existing capabilities are insufficient and the maintenance/security trade-off is justified.
- Do not expose secrets, bypass safeguards, weaken validation, or change security/quality policy to make checks pass.
- Treat generated artifacts according to project rules; change their source rather than hand-editing output when applicable.

## Completion

Inspect the final diff, trace affected callers and operational paths, and apply `testing.md`. Report scope deviations and unverified risks explicitly.
