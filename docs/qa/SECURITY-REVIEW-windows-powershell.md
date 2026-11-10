# Security review: Windows PowerShell installation

Date: 2026-11-10. Final verdict: **PASS after correction and repeated independent QA/code review.** Both initial confirmed findings were returned to development and resolved.

The independent `sdlc-security` reviewer inspected the full new untracked implementation and the tracked changes. The reviewer was read-only; this report records its findings and the root agent's isolated reproduction.

## Confirmed findings

1. **High: batch interpreter shims reinterpret native arguments.** `Get-Command -CommandType Application` accepts `.cmd`/`.bat`, and invoking such a candidate passes arguments through `cmd.exe`. A functional `python.cmd` forwarding `%*` passed the version probe. A target containing `&` then installed into a truncated temporary directory and executed a harmless injected `echo` command. Root confirmed this with `test_cmd_runtime_does_not_reparse_target_metacharacters`. Required fix: invoke a native interpreter executable, skipping batch candidates and safely continuing discovery; never pass target arguments through a command shell.
2. **Medium: Windows device namespace aliases bypass overlap protection.** `Path.resolve()` preserves an extended-length prefix, so a target written as `\\?\` plus the source directory was not considered equal to ordinary drive syntax. A read-only dry run exited successfully and planned writes into the source repository. Required fix: reject unsupported namespace targets before resolution, or canonicalize source and target consistently. Regression checks must cover explicit and environment-selected targets without writing into the source.

## Scope and limits

Reviewed manifest traversal/ADS/device aliases, lexical reparse checks, containment, backups, managed configuration, package-content validation, native invocation, dependencies, and documentation. No other confirmed issue was reported. No discovered secret values were printed. Whole-install rollback, concurrent installers, and adversarial filesystem races remain explicit architecture exclusions.

## Resolution and final verification

- Batch invocation: `scripts/python-runtime.ps1:5` enumerates all application matches; lines 9–10 reject non-`.exe` candidates and WindowsApps paths. Only an accepted native executable reaches invocation at line 37. Tests reject a batch-only environment without fixture changes, then verify that a later native interpreter installs into the exact ampersand-containing target without a truncated sibling.
- Namespace aliases: `scripts/package_cli.py:60` rejects unsupported prefixes after slash normalization. The package path is checked at line 244 and raw selected target at line 250, before target resolution and planning. Tests cover explicit and environment-selected namespace aliases against an isolated source copy.
- Repeated independent QA: native validator passed; 36 test methods ran, with 35 passed and one symlink-privilege skip. Actual Windows junction cases passed. Repeated independent code review also executed all nine safety-edge methods successfully.
- The independent security follow-up statically verified both corrections and their regression evidence. No remaining confirmed defect was reported. This follow-up did not run additional payloads or modify files.

PowerShell 7, a live Store alias, and an actual older Python installation remain unverified. These limits do not change the tested Windows PowerShell 5.1/Python 3.12 scope.

No global installation, dependency download, commit, push, PR, or deployment was performed. Shipping remains a separate explicit decision.
