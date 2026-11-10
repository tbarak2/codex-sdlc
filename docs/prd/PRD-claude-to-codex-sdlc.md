# PRD: Portable Claude-to-Codex SDLC

## Goal

Reproduce Roy's existing Claude Code software-development workflow in Codex while adapting it to Codex-native capabilities, and package it so the same workflow can be installed safely on another computer.

## Source Inventory

The migration source is `~/.claude`. The reusable workflow is concentrated in:

- `CLAUDE.md`: global phase ordering, approval gates, artifact locations, branch conventions, and definitions of done.
- `agents/`: PM, architecture, UI, development, QA, browser/UI QA, security, DevOps, and a Tokomni-specific log-analysis agent.
- `commands/`: 15 reusable engineering commands covering review, debugging, documentation, Git activity, incidents, migrations, onboarding, performance, refactoring, and security.
- `skills/`: four reusable or organization-specific skills.
- `settings.json`: selected workflow hooks and plugin declarations.

Runtime data such as credentials, session keys, conversation history, caches, logs, backups, security state, and shell snapshots is not portable workflow configuration and must not be copied.

## Users and Primary Use Cases

### Primary user

Roy, working on software projects from Codex CLI on multiple computers.

### Use cases

1. Start a feature and move through PM, architecture, UI, test planning, implementation, verification, review, security, DevOps, and shipping gates.
2. Fast-track a bug fix through implementation and the mandatory verification/review stages.
3. Invoke reusable engineering workflows such as code review, debugging, migration safety review, onboarding, and incident reporting.
4. Install or update the same workflow on a second computer without copying secrets or machine-specific state.
5. Validate that an installation has the expected files and passes structural checks.

## Functional Requirements

### FR-1: Codex-native orchestration

Provide a top-level `sdlc` skill that:

- Identifies whether work is a feature or bug fix.
- Announces the active phase.
- Enforces the existing explicit `Go`, `Approved`, or `Proceed` phase gates.
- Preserves the current artifact paths and branch conventions.
- Routes work to appropriate Codex specialist agents when delegation is available.
- Falls back to performing a role directly from its role instructions when a matching specialist agent is unavailable.
- Never silently skips a required phase.

### FR-2: Role preservation

Translate the reusable behavior of these Claude agents into Codex role skills or references:

- Product manager
- Architect
- UI/UX designer
- Developer
- QA/test author and verifier
- Browser/UI QA
- Security reviewer
- DevOps/release readiness reviewer

The Tokomni log analyzer is organization-specific and will be packaged as an optional extension rather than part of the generic core.

### FR-3: Command migration

Translate each reusable Claude command into a discoverable Codex skill. Commands with overlapping behavior may share references or scripts, but their user-facing intent must remain independently discoverable.

Commands that require organization services, credentials, MCP servers, or proprietary plugins must declare those dependencies and fail safely with a useful setup message.

### FR-4: Existing skill migration

Review the four Claude skills individually:

- Migrate generic and still-relevant skills.
- Mark organization-specific dependencies explicitly.
- Do not copy secrets, personal data, or machine-specific absolute paths.
- Do not migrate a skill whose required integration is unavailable without documenting the gap.

### FR-5: Portable package

Create a version-controlled package under `/home/roybarak/code/codex-sdlc` containing:

- Global `AGENTS.md` template.
- Codex skills and supporting references/scripts.
- Optional organization-specific extensions separated from the generic core.
- An idempotent installer that installs into a configurable Codex home.
- A dry-run mode showing intended changes.
- Backup behavior before replacing an existing managed file.
- An uninstaller or manifest-based removal mechanism limited to files installed by the package.
- Setup and migration documentation.

### FR-6: Safe configuration handling

The package must never contain:

- Claude or Codex credentials.
- API tokens, session keys, cookies, or private keys.
- Conversation history, file history, caches, logs, or security state.
- Personal agent memory unless explicitly reviewed and converted into a non-sensitive reusable rule.
- Machine-specific paths where a portable variable or relative path is possible.

### FR-7: Verification

Provide automated checks for:

- Skill frontmatter and naming.
- Required files and links between skills and references.
- Installer dry-run and idempotency.
- Secret-pattern scanning of the distributable package.
- Installation into a temporary Codex home.
- Shell linting where the required tool is available.

## Proposed Codex Mapping

| Claude concept | Codex representation |
|---|---|
| Global `CLAUDE.md` | Portable `AGENTS.md` plus the top-level SDLC skill |
| Custom agent definitions | Role skills/references plus available Codex specialist agent types |
| Slash commands | Individually discoverable Codex skills |
| Claude skills | Codex skills after dependency and portability review |
| Claude hooks | Installer-supported Codex hooks only where Codex has an equivalent; otherwise documented omission |
| Claude plugins/MCP | Dependency declarations and optional setup guidance; no credentials copied |
| Agent memory | Excluded by default; reusable non-sensitive lessons may be curated later |

## SDLC Flow to Preserve

```text
Feature:
PM -> approval -> Architecture -> approval -> UI (if applicable)
   -> approval -> QA test authoring -> approval -> Development
   -> QA verification -> UI QA (if applicable) -> Code Review
   -> Security Review -> DevOps -> approval -> Ship

Bug fix:
Development -> QA verification -> UI QA (if applicable) -> Code Review
   -> Security Review -> DevOps -> approval -> Ship
```

## Non-Goals

- Copying the whole `~/.claude` directory.
- Migrating credentials, runtime state, histories, caches, or backups.
- Guaranteeing that proprietary Claude plugins have exact Codex equivalents.
- Publishing the package publicly or pushing it to a remote repository without separate authorization.
- Automatically opening or merging pull/merge requests.
- Changing existing project repositories during the migration implementation.

## Acceptance Criteria

1. A clean Codex installation can install the package using one documented command.
2. Running the installer twice produces no unintended duplicate or destructive changes.
3. A dry run lists every destination change without writing files.
4. The installed SDLC workflow enforces explicit approval between specification phases.
5. Feature and bug-fix routing preserve the source workflow's required review stages.
6. Each migrated role has documented inputs, outputs, completion conditions, and handoff behavior.
7. The installer never reads or copies Claude credential/session/history locations.
8. Automated validation passes for all shipped skills and scripts.
9. A temporary-home integration test proves installation without modifying the real `~/.codex` directory.
10. The package documents any Claude capability that could not be reproduced exactly in Codex.

## Delivery Phases

1. Architecture: finalize Codex structure, agent/skill routing, installer strategy, and dependency boundaries.
2. Core workflow: implement `AGENTS.md`, SDLC orchestration, and eight generic roles.
3. Commands and skills: migrate reusable commands and compatible skills.
4. Portability: implement installer, backup/manifest behavior, dry run, and documentation.
5. Quality: add validators, integration tests, secret scanning, and lint/build checks.
6. Optional extensions: migrate Tokomni- and organization-specific workflows separately.

## Open Questions

1. Should the first delivery include all 15 commands and four existing skills, or should it first deliver the core SDLC pipeline and then migrate utilities in a second milestone?
2. Should organization-specific Tokomni/Omni/ProofHub/GitLab workflows be included in the portable repository as optional extensions, or excluded from the first version?
3. Should installation manage a global `~/.codex/AGENTS.md`, install only skills, or offer both global and per-project modes? Recommended: offer both, with skills installed globally and an optional project `AGENTS.md` template.
4. How should the package be transferred to the other computer: a private Git repository, a local archive, or both? Recommended: private Git repository plus an archive export command.

