# DevOps readiness: Windows PowerShell installation

Date: 2026-11-10. Branch: `feature/windows-powershell`. Package version: `0.1.0`.

Verdict: **ready for controlled local manual testing within the verified Windows PowerShell 5.1 scope.** No shipping, global installation, push, PR, or deployment is approved. The repository's finish/push coverage gate remains unresolved.

## Inputs and verification

Reviewed the [QA results](QA-RESULT-windows-powershell.md), [independent code review](CODE-REVIEW-windows-powershell.md), [security review](SECURITY-REVIEW-windows-powershell.md), approved architecture, README, native runtime discovery, and installation recovery behavior. Independent QA/code/security reviews passed after both security corrections.

Executed during this readiness phase:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-package.ps1
git diff --check
```

Both exited 0. The validator printed `PASS: package validation`; it checks PowerShell syntax and portable package contracts. It is the available package-validation check, not a production build or coverage measurement.

Existing final verification evidence was reviewed rather than redundantly repeating the full suites:

- Actual Windows PowerShell 5.1.26100.9711 with Python 3.12.10: 36 test methods, 35 passed and one symbolic-link privilege skip. Actual junction rejection tests passed.
- Existing Bash package validation and six test suites passed before and after implementation, executed by the root agent in Git Bash 5.3.15 with native Python 3.12 through a temporary exported `python3` shim. No global interpreter configuration changed.
- Final QA separately confirmed Unicode public-command install/uninstall without UTF-8 environment overrides.

## Operational readiness

| Area | Assessment |
|---|---|
| Installation target | Local Codex home selected explicitly, through `CODEX_HOME`, or the user's default. Temporary targets were verified; no real global installation occurred. |
| Prerequisites | README requires Windows PowerShell 5.1 and native Python 3.11+ executables on PATH. Batch shims and WindowsApps aliases are skipped; no automatic prerequisite downloads. |
| Execution policy | README provides an optional child-process `-ExecutionPolicy Bypass` invocation. Machine/user policy is not changed; enforced organizational restrictions can still block execution. |
| Configuration | Managed blocks and generated TOML are preflighted before writes. Existing settings, unrelated files, and locally modified files on uninstall are preserved according to documented ownership rules. |
| Filesystem boundary | Normal drive/UNC syntax is the interface. Namespace aliases, package/target overlap, unsafe manifest paths, and reparse-point mutation paths are rejected. |
| Backup/recovery | Changed existing files receive backups; replacement is atomic per file and manifest publication is last. Errors identify the failing path and backup location. Whole-install rollback is not promised. |
| Uninstall | Preview is available. Matching owned files and managed blocks are removed; modified files, unrelated content, and existing backups remain. |
| Secrets | No credentials or secret settings are needed. Package validation rejects forbidden runtime paths and private-key markers. Reviewed security findings are resolved. |
| Network/ports/services | No hosted service, network listener, ports, or deployment credentials are introduced. Runtime dependency downloads are absent. |
| Migration | Existing Bash commands remain supported. The ownership manifest schema remains compatible; no database migration or data service is involved. |
| Performance | Operations are bounded by package files, selected destinations, and hashing installed ownership files. No benchmark was required or performed. Concurrent installers and adversarial filesystem races are excluded. |

## Tooling and release limits

Repository inspection found no configured build system, formatter, linter, type checker, coverage command, CI pipeline, container image, or deployment target. No production build was run because no build command exists; this is an explicit tooling gap, not a claimed build success. `shellcheck`, `ruff`, `mypy`, and `PSScriptAnalyzer` were also unavailable on this host. Native parser/package validation and the reported tests are the checks actually available.

No 100% coverage result exists. Test counts are not coverage, and passing readiness checks do not satisfy the user's required finish/push gate. A reliable coverage-tooling decision and its required result must be resolved before declaring the feature finished or pushing it under that rule.

PowerShell 7, actual older Python installations, live Store aliases, and arbitrary Windows releases remain unverified. Physical locks, ACL denial, antivirus interference, and interrupted whole-install recovery were not reproduced; deterministic backup/replacement error tests exercise the documented failure boundary.

## Handoff

Only this readiness report was changed in this phase. No implementation, tests, infrastructure, global settings, dependency installation, commit, push, PR, or deployment was changed.

The next phase is the explicit shipping decision. Ask whether the user wants local manual testing before any separately authorized PR or shipping action. A decision to test or review does not authorize global installation, publishing, or bypassing the unresolved coverage gate.
