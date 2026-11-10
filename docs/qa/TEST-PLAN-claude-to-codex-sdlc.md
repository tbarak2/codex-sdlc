# Test Plan: Portable Claude-to-Codex SDLC

## Purpose

Define the executable contract for the portable Codex SDLC package before implementation. Tests must run without changing the active `~/.codex` installation.

## Test Environment

- Bash 4+
- Python 3.11+ with `tomllib`
- A temporary fake home and Codex home created per test
- No network access required
- No proprietary organization integrations required for core tests

## Acceptance-Criteria Matrix

| ID | Acceptance criterion | Automated coverage |
|---|---|---|
| AC-1 | Clean installation uses one documented command | `installer-test.sh`: installs into an empty temporary Codex home and checks required files |
| AC-2 | Running installer twice is idempotent | `idempotency-test.sh`: snapshots the first installation and compares it after the second run |
| AC-3 | Dry run lists changes but writes nothing | `installer-test.sh`: compares filesystem snapshots before and after `--dry-run` |
| AC-4 | Workflow enforces explicit approval between specification phases | `package-contract-test.sh`: checks the orchestrator contract and approved tokens |
| AC-5 | Feature and bug-fix routing preserve review stages | `package-contract-test.sh`: verifies required phase contracts for both routes |
| AC-6 | Every role declares inputs, outputs, completion, and handoff | `package-contract-test.sh`: validates eight agent TOMLs and required contract markers |
| AC-7 | Installer does not copy sensitive Claude runtime data | `security-test.sh`: scans manifest and output for forbidden source/runtime paths |
| AC-8 | All skills and scripts pass validation | `validate-package.sh` invoked by `run.sh`; shell syntax and TOML parsing are mandatory |
| AC-9 | Temporary-home integration test proves isolation | Every installer test sets `HOME` and `CODEX_HOME` to temporary paths and checks the real Codex home fingerprint |
| AC-10 | Unsupported or non-equivalent capabilities are documented | `package-contract-test.sh`: requires a migration matrix with a status for each source component |

## Installer Scenarios

### Fresh install

1. Create an empty temporary home.
2. Run `install.sh --codex-home <temp> --yes`.
3. Assert global `AGENTS.md`, agent TOMLs, skills, manifest, and install metadata exist.
4. Parse generated `config.toml`.
5. Assert the active real Codex home was not changed.

### Existing unmanaged configuration

1. Seed temporary `AGENTS.md` and `config.toml` with sentinel content.
2. Install.
3. Assert sentinels remain exactly once.
4. Assert managed markers are balanced and appear exactly once.
5. Assert resulting TOML parses.

### Dry run

1. Seed a temporary Codex home.
2. Record its recursive checksum.
3. Run installer with `--dry-run`.
4. Assert output describes planned changes.
5. Assert recursive checksum is unchanged.

### Idempotent update

1. Install once.
2. Record checksums and managed-marker counts.
3. Install again.
4. Assert no duplicate markers or registrations.
5. Assert installed file content is unchanged.

### Safe uninstall

1. Install into a seeded temporary Codex home.
2. Modify one installed skill file.
3. Uninstall.
4. Assert unmanaged configuration remains.
5. Assert unchanged package-owned files are removed.
6. Assert the locally modified installed file remains and is reported.

## Package Contract Scenarios

- Exactly eight core custom agents are registered.
- Security agent is read-only.
- Each write-capable role is restricted by instructions to its documented output scope.
- The orchestrator recognizes only `Go`, `Approved`, and `Proceed` as approval tokens.
- The feature route includes PM, architecture, conditional UI, QA pre-code, development, QA verification, conditional UI QA, code review, security, DevOps, and ship approval.
- The bug-fix route begins with development but retains all post-development quality gates.
- Review blockers route back through development and repeated verification.
- Shipping and real-home installation are never implicit.

## Security Scenarios

The distributable package and a temporary installation must not contain:

- `.credentials.json`
- Session keys or session directories
- Conversation/file history
- Cache, log, backup, or security-state content
- Private-key blocks
- Common bearer/API-token assignments
- `/home/roybarak` or another source-machine absolute path in installed runtime files

Documentation may mention the literal source directory `~/.claude` and sanitized examples, but must not contain secret values.

## Verification Commands

```bash
bash -n install.sh uninstall.sh tests/*.sh
bash tests/run.sh
```

When available:

```bash
shellcheck install.sh uninstall.sh tests/*.sh scripts/*.sh
```

## Expected Pre-Implementation Result

The test runner must fail because `install.sh`, `uninstall.sh`, agents, skills, and validation scripts do not exist yet. Shell syntax checks for the test harness itself must pass.

## Open Questions

None. Organization-extension tests are deferred until those extensions enter scope.

