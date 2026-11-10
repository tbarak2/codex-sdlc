# Independent code review: Windows PowerShell installation

Date: 2026-11-10. Branch: `feature/windows-powershell`, compared with `main` plus the new untracked implementation and tests.

## Verdict

PASS after focused repeat review of the security corrections. No confirmed material correctness or maintainability finding remains in the reviewed Windows PowerShell 5.1 scope. The initial review did not identify the two subsequently confirmed security findings described below. This verdict does not authorize shipping or establish 100% coverage.

## Scope and checks

Applied the `code-quality-review` skill independently of the implementation agent. Reviewed:

- Native install/uninstall parameters, help, reserved options, trailing-backslash handling, argument-array invocation, dependency probing, exit propagation, and temporary output-encoding restoration.
- Portable lifecycle planning and preflight, managed configuration validation, reserved-agent collisions, Windows path serialization, backups, per-file atomic replacement, manifest publication, and safe uninstall.
- Manifest parsing and containment: duplicate/case-alias detection, traversal/absolute/UNC/drive/ADS rejection, reserved/trailing-dot Windows aliases, and lexical ancestor reparse checks before resolution.
- Shared marker editing and BOM/newline preservation, including compatibility of the existing helper CLI used by Bash.
- Portable validation, Bash validator extraction, all new test files and fixtures, README instructions, and the approved PRD/architecture/test plan.

The design keeps PowerShell invocation separate from Python filesystem behavior, uses a small change record and cohesive functions, and avoids introducing unnecessary frameworks or dependencies. Tests exercise observable lifecycle behavior and meaningful failure paths with isolated targets. Mocking is limited to deterministic failure and confirmation cases; public Windows commands are also exercised in real subprocesses.

`git diff --check` independently passed. Updated independent QA evidence records native validation and 36 test methods: 35 passed and one symlink-privilege skip. Junction tests passed on the actual Windows host. The root agent separately executed the existing Bash validator and six suites before and after the changes; this review did not repeat those already passing suites.

## Focused security-correction review

The security phase confirmed that accepting a batch runtime could reparse an ampersand in a target through `cmd.exe`, and that Windows device/extended namespace aliases could bypass source/target overlap checks. Those findings superseded the initial review's lack of findings.

Reviewed the final correction delta independently:

- `Get-SdlcPython` now considers all application matches in PATH order, accepts native `.exe` files only, and skips WindowsApps locations before probing. A batch-only environment fails before invocation; a later native Python remains discoverable. Native argument passing avoids the batch reparsing layer.
- The lifecycle rejects device/extended namespace prefixes for the package and selected target before target canonicalization and overlap checks. Ordinary drive and UNC paths remain the documented interface.
- README states the native-executable prerequisite and namespace restrictions. Regression tests check the entire rejected fixture for changes, verify successful native fallback into an ampersand-containing target, reject explicit and environment namespace aliases, and exercise version/WindowsApps probing with a real native interpreter and sentinels.

Independently executed `python -B -m unittest discover -s tests -p test_safety_edges.py`: all nine test methods passed. `git diff --check` also passed after the corrections. No additional finding was confirmed in this focused repeat review; separate security re-review is still required.

## Limits

- PowerShell 7 is unavailable and unverified. Tested Windows evidence is Windows PowerShell 5.1.26100.9711 with Python 3.12.10.
- Old-version checks simulate `sys.version_info` through isolated `sitecustomize.py` on a native interpreter. WindowsApps skipping uses a functional native executable exposed through a temporary junction and a probe sentinel; no live Store alias was launched. Actual ACL, antivirus, and file-lock failures were not reproduced. Backup and replacement failures have deterministic mocked tests.
- Whole-install rollback, concurrent installers, and adversarial filesystem races are documented exclusions; replacement is atomic per file.
- No formatter, linter, type-checker, build, or coverage command is configured. Passing tests are not a coverage measurement. The finish/push coverage decision remains unresolved.
- Security and DevOps readiness are separate subsequent gates.

Only this review artifact was changed. No production fixes, global installation, dependency download, commit, push, or external action occurred.
