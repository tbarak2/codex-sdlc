---
name: sdlc
description: Run a gated software-development lifecycle for features or bug fixes using product, architecture, UI, QA, development, code-review, security, and DevOps roles. Use when the user asks to build, change, or fix software through the full workflow; do not use for a simple explanation or read-only question.
---

# Gated SDLC

Announce the active phase at the beginning of each response. Preserve unrelated workspace changes and all user decisions.

## Approval rule

Advance a gated phase only when the user's response explicitly communicates one of these approval tokens: `Go`, `Approved`, or `Proceed` (case-insensitive). Questions, corrections, partial agreement, or silence do not approve advancement. Ask once for the next approval after reporting the phase artifact and open questions.

## Route selection

- A new capability or materially expanded behavior follows the feature route.
- A localized defect that restores intended behavior follows the bug-fix route.
- If a bug fix expands into a feature, stop and return to the product phase.
- When evidence cannot distinguish the route and the choice changes required artifacts, ask the user.

## Feature route

Run these phases in order:

1. `pm`: create `docs/prd/PRD-<feature>.md`; stop for approval.
2. `architecture`: create `docs/arch/ARCH-<feature>.md`; stop for approval.
3. `ui`: when frontend behavior or presentation changes, create `docs/ui/UI-<feature>.md`; stop for approval.
4. `qa` pre-code: create the test plan and failing automated tests; stop for approval.
5. `development`: implement on a feature branch and run tests, lint, and build checks.
6. `qa` verification: verify every acceptance criterion without fixing production code.
7. `ui-qa`: when frontend changed, exercise the rendered application and committed E2E tests.
8. `code-review`: run an independent review of the branch diff and verify findings before accepting them.
9. `security`: perform a read-only security review.
10. `devops`: validate production build, configuration, and deployment readiness.
11. `ship`: ask whether the user wants manual testing before opening a PR/MR; never open, merge, deploy, or ship implicitly.

## Bug-fix route

Start at `development` on a `fix/` or `hotfix/` branch, then run `qa`, conditional `ui-qa`, `code-review`, `security`, `devops`, and the explicit `ship` decision. Do not skip post-development gates.

## Failure loops

- Development test failure stays in development until resolved or genuinely blocked.
- QA failure produces a report and returns to development; repeat QA afterward.
- Confirmed blocker from code-review or security returns to development, followed by QA and the failed review again.
- A missing optional dependency blocks only the phase that requires it and must be reported accurately.

## Agent invocation

Use the registered `sdlc-*` custom agent matching the phase. Give it the repository root, feature identifier, approved upstream artifact paths, allowed mutation scope, and expected handoff. Do not run future phases concurrently because approval gates create hard dependencies.

Read [references/phase-contracts.md](references/phase-contracts.md) when preparing an agent handoff. Read [references/artifact-templates.md](references/artifact-templates.md) when an artifact does not already have a project-specific template.
