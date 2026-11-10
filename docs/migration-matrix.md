# Claude-to-Codex Migration Matrix

| Source | Status | Codex destination | Notes |
|---|---|---|---|
| Global `CLAUDE.md` SDLC rules | Migrated | `AGENTS.md`, `skills/sdlc/` | Preserves gates, artifacts, branches, and flow |
| PM agent | Migrated | `agents/sdlc-pm.toml` | Custom Codex agent |
| Architecture agent | Migrated | `agents/sdlc-architect.toml` | Custom Codex agent |
| UI agent | Migrated | `agents/sdlc-ui.toml` | Custom Codex agent |
| Developer agent | Migrated | `agents/sdlc-developer.toml` | Custom Codex agent |
| QA agent | Migrated | `agents/sdlc-qa.toml` | Supports pre-code and verification modes |
| UI QA agent | Migrated | `agents/sdlc-ui-qa.toml` | Playwright is optional and detected at runtime |
| Security agent | Migrated | `agents/sdlc-security.toml` | Read-only sandbox |
| DevOps agent | Migrated | `agents/sdlc-devops.toml` | Deployment readiness; shipping remains gated |
| Tokomni log analyzer | Deferred | Optional organization extension | Requires proprietary systems and a separate review |
| Generic commands | Deferred | Future utility skills | Core SDLC is the first milestone |
| GitLab/ProofHub/Graylog commands | Deferred | Optional organization extension | Requires credentials/connectors |
| Existing Claude skills | Deferred | Future core/extension review | Must be reviewed individually |
| Claude hooks | Not copied | None in core | Hook semantics and dependencies differ |
| Claude plugins | Not copied | Documented optional dependencies | No credentials or plugin state copied |
| Agent memory | Excluded | None | May contain personal/project-specific state |
| Credentials, sessions, histories, caches, logs | Excluded | None | Never portable workflow content |
