# Codex SDLC

A portable Codex-native version of Roy's gated software-development workflow.

## Install

Preview changes:

```bash
./install.sh --dry-run
```

Install into the current Codex home:

```bash
./install.sh
```

Install into another location:

```bash
./install.sh --codex-home /path/to/.codex
```

The installer copies the core skill and eight custom agents, then updates only marked blocks in `AGENTS.md` and `config.toml`. Existing files are backed up before changes. It never reads `~/.claude` or copies credentials, histories, sessions, logs, or caches.

## Validate

```bash
bash tests/run.sh
```

## Uninstall

```bash
./uninstall.sh
```

Uninstall removes unchanged package-owned files and managed blocks only. Locally modified installed files are retained for manual review.

## Other computer

Copy or clone this repository on the other computer, inspect `./install.sh --dry-run`, then run `./install.sh`. A private Git remote can be added later without changing the package format.
