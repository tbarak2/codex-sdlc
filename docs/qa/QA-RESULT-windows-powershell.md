# QA verification: Windows PowerShell installation

Date: 2026-11-10. Phase: independent QA verification, repeated after security corrections. Verdict: **PASS for the approved Windows PowerShell 5.1 scope, with the environment limits below.** No unresolved QA blocker was found in the reviewed corrections. This is a QA verdict, not a shipping decision or coverage claim.

Inputs: [PRD](../prd/PRD-windows-powershell.md), [architecture](../arch/ARCH-windows-powershell.md), and [test plan](TEST-PLAN-windows-powershell.md). Reviewed current lifecycle implementation, runtime discovery, shared managed-text logic, validation, automated tests, and README. No production or test files were changed during verification.

## Independent commands and results

Host: Windows, Windows PowerShell 5.1.26100.9711, Python 3.12.10.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-package.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\run.ps1
```

- Native validator: PASS, including PowerShell parser and portable package validation.
- Final post-correction test runner: exit 0; `Ran 36 tests in 32.402s`, `OK (skipped=1)`. Thus 35 methods passed and one method skipped; subtests also completed successfully. The earlier independent pre-security run had 34 methods, 33 passing and one skipped. The skipped symbolic-link case requires a privilege unavailable on this host (Windows error 1314). Actual Windows junction cases at selected target, agent-copy, and backup paths passed and exercise reparse-point rejection without that privilege.
- Additional independent sample: installed and uninstalled into an isolated temporary path containing spaces and Hebrew, with `PYTHONUTF8` and `PYTHONIOENCODING` removed from the child environment. Both public PowerShell commands exited 0, emitted the Unicode target correctly as UTF-8, and produced a parseable configuration containing all eight agents. The ownership manifest was removed on uninstall.

All lifecycle targets were temporary. No command installed into the actual Codex home, downloaded dependencies, changed global execution policy, pushed, opened a PR, or deployed anything.

## Acceptance results

| Criterion | Verdict and evidence |
|---|---|
| AC-1 Native installation | PASS on Windows PowerShell 5.1. Public install/update/uninstall commands execute with PATH restricted to Python's directory; no Bash/WSL/Unix utility dependency. Eight agents, skill content, valid configuration, manifest, help, validator, and failure exits verified. |
| AC-2 Target selection and paths | PASS. Explicit relative target, environment target, and isolated default-home precedence pass. Source and target paths with spaces/Hebrew, ampersand metacharacter, and target trailing separator pass. Generated TOML paths match installed files. Device/extended namespace aliases are explicitly rejected rather than allowed to bypass overlap checks. |
| AC-3 Preview | PASS. Missing and populated install targets and uninstall previews retain original bytes and directory snapshots. Source-copy test confirms no package bytecode caches. Plan computation and backup preflight perform no target writes. |
| AC-4 Preservation and updates | PASS. Unrelated settings/rules/files remain; changed installed files/configuration have backups; repeat install preserves bytes and file timestamps without duplicate blocks. Implementation backs up changed existing manifest before replacement and publishes it last. |
| AC-5 Prerequisites and errors | PASS with simulation limits. Missing/unusable candidate handling, fallback, invalid settings/markers/UTF-8, collisions, unsupported/unknown/empty inputs, interactive decline, and no-write failures pass. Batch shims are rejected; discovery finds a native executable later on PATH. Old-version rejection uses the actual native Python executable with isolated `PYTHONPATH`/`sitecustomize.py` simulating `sys.version_info` 3.10 and recording that the probe ran. WindowsApps skipping uses a temporary junction exposing a functional native executable, with a successful control invocation and a sentinel proving discovery did not invoke it. These do not prove behavior of an actual Python 3.10 installation or a live Store alias. |
| AC-6 Safe removal | PASS with privilege limit. Modified owned files are reported/retained; unchanged files and manifest removed; unrelated files/settings and pre-existing backups survive. Malicious manifest paths, duplicate/case-alias rows, reserved Windows filenames, target overlap, and junction destinations are rejected before mutations. Both managed settings files are preflighted before deletion. Direct symbolic-link case is skipped as described above. |
| AC-7 Windows text | PASS. UTF-8 BOM, CRLF, LF, mixed-newline normalization, and Unicode survive install/uninstall with parseable TOML and expected preservation. Additional independent sample checks public wrappers without UTF-8 environment overrides. |
| AC-8 Existing Bash behavior | PASS based on root agent's separately executed regression evidence: actual Git Bash 5.3.15 and native Python 3.12; package validation and all six existing Bash suites passed before and after implementation. A temporary exported `python3` function invoked the full real Python executable with `-B`; no global interpreter setup changed. This QA agent reviewed the unchanged Bash lifecycle scripts and shared-helper changes but did not independently repeat that Bash run. |
| AC-9 Reproduction and docs | PASS. README includes prerequisites, native preview/install/custom target/test/validation/uninstall, process-only policy troubleshooting, text/backup/recovery behavior, and PowerShell 7 limitation. This report records actual Windows results and Bash evidence provenance. |

## Limits and remaining workflow

Security-review delta: the initial QA suite did not expose two subsequently confirmed security findings: batch runtime command reparsing and device-namespace source/target aliases. Development restricted runtime discovery to native `.exe` applications (while considering later PATH matches) and rejects device/extended namespaces before resolution. The repeated suite includes focused regressions: a batch-only runtime rejects an ampersand target without changing the entire fixture, native fallback installs into that exact target without a reparsed sibling, and explicit/environment namespace aliases fail while leaving the copied package unchanged. This QA rerun verifies those corrections and does not replace the subsequent security re-review.

- PowerShell 7 remains unverified because it is unavailable. Windows testing here does not establish all Windows versions or arbitrary downstream commands used by installed agents.
- Direct filesystem failure paths use deterministic mocked `PermissionError` for backup and atomic replacement; physical file locks, ACL denial, antivirus interference, and interrupted whole-install recovery were not reproduced. The documented boundary is per-file atomic replacement, not full rollback.
- Whole-install rollback, concurrent installers, and adversarial filesystem races remain architecture exclusions.
- No formatter, linter, production build, or coverage command is configured. The native validator checks syntax/contracts, not those absent tools. Passing tests do not establish 100% coverage; the repository's finish/push coverage decision remains unresolved.
- Repeat code/security review as required by the correction loop, DevOps readiness, and the explicit shipping decision remain downstream. UI QA is not applicable.

No separate QA bug report was created; the security findings are tracked by the security review and no new defect was found during this focused rerun. Do not interpret this result as authorization to install globally, push, publish, or ship.
