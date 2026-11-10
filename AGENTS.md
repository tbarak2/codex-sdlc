<!-- codex-sdlc:start -->
# Portable SDLC Workflow

For feature work, use the `sdlc` skill and progress through product specification, architecture, conditional UI specification, pre-development tests, implementation, QA verification, conditional UI QA, independent code review, security review, DevOps readiness, and an explicit shipping decision.

For a genuine bug fix, fast-track to implementation but retain every post-development quality gate.

Announce the active phase. A gated phase advances only when the user explicitly replies `Go`, `Approved`, or `Proceed`. Questions, edits, and silence are holds.

Store feature artifacts under the repository's `docs/` directory:

- Product: `docs/prd/PRD-<feature>.md`
- Architecture: `docs/arch/ARCH-<feature>.md`
- UI: `docs/ui/UI-<feature>.md`
- QA: `docs/qa/TEST-PLAN-<feature>.md`

Use `feature/<description>`, `fix/<description>`, or `hotfix/<description>` branches. Never open or merge a pull/merge request, deploy, or install global configuration without explicit authorization.

All implementations include tests and must pass the repository's lint, test, and build checks where configured. Preserve unrelated user changes.
<!-- codex-sdlc:end -->
