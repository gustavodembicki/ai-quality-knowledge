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

## Session working set

Maintain an internal brief with:

- Objective and current task.
- Scope and non-goals.
- Constraints and authoritative rules.
- Decisions already made and their rationale.
- Evidence gathered and checks run.
- Material unknowns and next action.
- Active knowledge modules.

Update the brief after a decision, failed assumption, scope change, or verification result. On a major task switch, create a fresh task section and carry forward only explicit user preferences and still-relevant facts.

## Context budget

- Start from likely entry points; search before reading broad directories or entire documents.
- Read enough surrounding code to understand contracts, callers, side effects, and tests, not just the edited line.
- Summarize large evidence into decisions and citations; avoid repeatedly loading raw content.
- Do not load unrelated knowledge modules “just in case.”
- Recheck authoritative files and the current diff when a long session may have made earlier observations stale.
- Never persist secrets, credentials, personal data, or transient session details into the knowledge base.

Implementation may begin only when all material context for the current step is known or explicitly accepted as an assumption.
