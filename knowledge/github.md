# Git and GitHub Workflow

## Before acting

- Read repository contribution, branch, commit, pull-request, release, and CI rules.
- Inspect status, current branch, remotes/upstream, relevant log, and the complete diff before commit or pull-request work.
- Preserve unrelated and user-authored changes. Never checkout, reset, clean, stash, or overwrite them without explicit agreement.
- Do not create branches, commits, tags, pushes, releases, issues, pull requests, comments, or reviews unless requested.

## Branch and history safety

- Base work on the intended branch and confirm the comparison range rather than assuming `main` or another default.
- Prefer reversible operations. Never rewrite published history, force-push, delete branches/tags, bypass hooks, or discard changes without explicit authorization for that action.
- If an authorized force push is necessary, prefer lease-protected semantics and first confirm nobody else’s work will be overwritten.
- Never change Git configuration to work around a workflow problem.

## Commits

- Keep each commit focused on one coherent reason for change, following repository-specific history and policy.
- Before committing, review staged files and diff, remove secrets and accidental artifacts, and run applicable checks.
- Stage exact intended paths; do not absorb unrelated files.
- Write an imperative subject and explain why or constraints in the body when the reason is not obvious.
- Do not claim tests in a commit message unless they ran.

## Pull requests

Before opening or updating a pull request:

1. Review all commits and the full base-to-head diff.
2. Confirm branch/base, required title convention, issue references, and template.
3. Ensure the description explains why, what changed, behavior/architecture impact, test evidence, risks, rollout/rollback, migrations, and screenshots when applicable.
4. Check for secrets, debug output, generated noise, unrelated changes, and missing documentation or release notes.
5. Push or publish only when explicitly requested.

After publication, do not call the work ready until required CI and review gates are green. Report failing, pending, skipped, or unavailable checks exactly; never weaken tests, hooks, branch protection, dependency/security policy, or CI to force success.

## Collaboration

- Treat review comments and issue updates as external side effects; post only with authorization.
- Address feedback at the root cause, rerun relevant checks, and update the existing change according to repository policy.
- Do not resolve another person’s conversation, merge, release, or close work unless requested.
- Keep credentials, private URLs, personal data, and internal identifiers out of commits, logs, issue text, and pull-request descriptions.
