# Testing and Regression Validation

## Test strategy

Tests are executable behavior contracts and regression evidence. Prefer the cheapest test level that exercises the real risk through a stable public boundary.

Cover the relevant subset of:

- Primary success behavior.
- Boundaries, invalid input, errors, and partial failure.
- Previously supported behavior that must remain unchanged.
- Contracts across persistence, network, serialization, time, concurrency, or external boundaries.

Keep tests deterministic, independent, readable, and focused on one behavior. Prefer real collaborators inside the chosen boundary; mock slow or uncontrolled boundaries, not the behavior under test. Avoid assertions that duplicate implementation details or pass without exercising production behavior.

## Test-first workflow

For a feature, bug fix, or behavior change where automated testing is meaningful:

1. Add the smallest behavioral test expressing the requirement.
2. Run it and observe the expected failure. A syntax/setup error is not a valid red state; an immediate pass means the test does not demonstrate missing behavior.
3. Implement the smallest complete production change that passes.
4. Run the focused test and nearby tests.
5. Refactor only while green.
6. Add the next behavior through the same cycle.

A bug fix requires a reproducing regression test unless technically impossible. For a behavior-preserving refactor, first ensure characterization coverage is adequate; existing tests may remain green because no new behavior is intended.

When automation is not meaningful or practical—such as documentation, generated artifacts, some configuration, or an inaccessible external system—state why before implementation and define an alternative validation method. Do not create a ceremonial test with no behavioral value.

## Regression surface

Derive regression checks from the actual impact graph:

- Changed functions, modules, interfaces, routes, jobs, schemas, and configuration.
- Callers, consumers, sibling implementations, integrations, and public contracts.
- Data migrations, retries, idempotency, concurrency, resource cleanup, and failure recovery.
- Supported versions, platforms, feature flags, rollout states, and backward compatibility.

A new test passing is necessary but not sufficient. Validate old behavior that must remain unchanged.

## Verification ladder

Run in this order for fast, attributable feedback:

1. The new or changed focused test.
2. The affected test file/module/package.
3. Relevant integration, contract, or end-to-end tests.
4. Applicable lint, type, static analysis, and build checks.
5. The broadest practical project-required suite.

Do not hide failures, delete valid assertions, weaken tests, alter quality/security controls, or update snapshots blindly to obtain green output. Investigate whether a failure is caused by the change, exposed by it, or pre-existing.

## Completion evidence

Report:

- Tests added or changed and the behavior they prove.
- Confirmation that the red state failed for the expected reason when applicable.
- Commands/checks run and outcomes.
- Relevant checks not run, why, and residual risk.
- Flakiness, environmental limitations, or unrelated pre-existing failures.

Never claim verification that was not performed.
