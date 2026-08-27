# Context and Session Control

## Goal

Acquire enough reliable context to make the next decision safely without flooding the session with unrelated information.

## Material context

Context is material when it can change the outcome, architecture, safety, compatibility, data behavior, acceptance criteria, rollout, or verification. Depending on the task, establish:

- Desired outcome, current behavior, and behavior that must remain unchanged.
- Scope, non-goals, constraints, stakeholders, and acceptance criteria.
- Relevant runtime, data, interfaces, dependencies, deployment, and compatibility requirements.
- Repository rules, existing patterns, tests, and authoritative documentation.

Do not demand fields that cannot affect the decision.

## Evidence order

1. Current user request and explicit decisions.
2. Applicable repository and directory rules.
3. Relevant implementation, tests, schemas, configuration, and lockfiles.
4. Analogous code and recent history when it explains intent.
5. Authoritative external documentation when local evidence is insufficient.
6. A focused user question for facts only the user can decide or provide.

Explore before asking. Never use a question to outsource a codebase search.

## Ambiguity gate

- Distinguish facts, evidence-backed inferences, assumptions, and unknowns.
- Resolve prerequisites before dependent decisions.
- If an unknown is material, stop the affected work and ask exactly one focused question. Include the recommended answer and primary trade-off.
- If ambiguity is immaterial, choose the simplest reversible option and record the assumption concisely.
- Do not ask for confirmation when evidence already determines the safe path.

## Decision protocol

Use an evidence-to-decision loop proportional to the task:

1. Frame the outcome, decision, constraints, and proof of success.
2. Gather the narrowest authoritative evidence that can change the decision.
3. Reconcile freshness, provenance, conflicts, and affected consumers.
4. Decide with a concise rationale, separating facts, inferences, assumptions, and unknowns.
5. Verify the resulting behavior and refresh evidence that may have changed during the work.

Prefer exact local sources before broad or external retrieval. A populated search result is not proof of completeness; expand only when material gaps, weak evidence, or contradictions remain. Never silently choose one source when authoritative evidence conflicts.

For long work, session boundaries, compaction, handoffs, or context/token budgeting, load `knowledge/continuity.md`.

Implementation may begin only when all material context for the current step is known or explicitly accepted as an assumption.
