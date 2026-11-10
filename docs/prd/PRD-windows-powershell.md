# PRD: Windows PowerShell Installation

Status: approved by the user's `Go` on 2026-11-10; architecture is the next phase.

## Problem and target user

A Windows user working in PowerShell cannot run the documented Bash installer directly. The current installation and validation paths invoke Bash, Unix utilities (`sed`, `find`, `sha256sum`, and others), and `python3`. A PowerShell wrapper that merely invokes the Bash script would retain these dependencies.

The target user wants to install, update, preview, and uninstall the existing Codex SDLC package on Windows from PowerShell with predictable preservation of existing Codex configuration.

## Desired outcome and success metrics

Provide documented PowerShell commands that work without Bash, Git Bash, or WSL. Acceptance requires passing automated installation lifecycle tests on an actual Windows host in Windows PowerShell 5.1. Record the exact tested environment and results. PowerShell 7 compatibility is desirable, but must be labelled unverified unless executed there successfully.

All acceptance criteria below must have verification evidence before claiming Windows support. Tests use isolated temporary targets and never install into the real user Codex home.

Discovery environment: Windows PowerShell 5.1.26100.9711 and Python 3.12.10 are available on the current Windows host. PowerShell 7 (`pwsh`) is unavailable, and `python3` resolves to a WindowsApps alias. This confirms test tooling availability, not successful package installation.

## Options and recommendation

| Approach | User value | Complexity and risk | Time to first delivery |
|---|---|---|---|
| Document Bash through WSL or Git Bash | Reuses current scripts | Adds environment setup and path translation; does not solve native PowerShell use | Shortest, but insufficient |
| Implement the full lifecycle independently in PowerShell | Native commands and no Python requirement if TOML validation is replaced | Duplicates safety logic; correct TOML handling needs another solution | Longest |
| PowerShell entry points using portable Python lifecycle/validation logic | Native PowerShell use with existing Python/TOML capabilities | Requires a working Python 3.11+ installation; shared logic must preserve Bash behavior | Recommended balance |

Recommend `install.ps1` and `uninstall.ps1`, with portable Python logic where useful. Architecture decides how much existing logic to share. Keep existing Bash commands working.

## MVP scope and functional rules

- Native PowerShell install, dry-run, update/reinstall, and uninstall entry points, plus a Windows-compatible validation command.
- Support Windows PowerShell 5.1; test PowerShell 7 when available and report any gap.
- Resolve a functional Python 3.11+ runtime, checking its version rather than trusting a command name or Windows Store alias. Do not download dependencies automatically.
- Preserve existing target selection: an explicit Codex-home argument takes precedence over `CODEX_HOME`, which takes precedence over the user's default `.codex` directory.
- Preserve installation of eight agent definitions, the SDLC skill and references, managed blocks, backups, and manifest-based ownership.
- Validate inputs and predictable configuration errors before changing target files.
- Preserve unrelated configuration and files; reject conflicting unmanaged agent names and malformed or duplicate managed markers with an actionable error.
- Document dependencies, invocation, dry-run, custom target paths, validation, uninstall, and execution-policy troubleshooting without changing global execution policy automatically.

## User stories and acceptance criteria

| ID | User story | Acceptance criteria |
|---|---|---|
| AC-1 | Install from my usual Windows shell | From Windows PowerShell 5.1, installation succeeds without invoking Bash/WSL/Unix executables and produces all eight agents, skill files, valid managed configuration, and an ownership manifest. Help and failures return appropriate process exit codes. |
| AC-2 | Use my chosen Codex directory | Explicit target, environment target, and default target follow the stated precedence. Tests cover repository and target paths containing spaces and non-ASCII characters. Generated TOML parses successfully and each registered Windows agent path resolves to the installed file. |
| AC-3 | Preview safely | Dry-run reports intended changes while creating, updating, or deleting no target files or directories, backups, or manifests. Verify both a missing target and an existing populated target. |
| AC-4 | Preserve my settings | Installation preserves unrelated configuration and files. Existing changed files receive backups before replacement. Managed blocks remain unique. Repeating installation leaves installed content unchanged and adds no duplicate blocks. |
| AC-5 | Understand prerequisites and errors | Missing, unusable, or too-old Python yields a clear setup error before target changes. Invalid TOML, unmanaged agent collisions, malformed markers in either managed file, and unsupported options also fail before target changes. |
| AC-6 | Remove only package-owned content | Uninstall dry-run makes no target changes. Real uninstall removes unchanged package-owned files and managed blocks, preserves modified installed files, unrelated files/settings, and backups, and reports retained files. Manifest paths cannot cause removal outside the selected target. |
| AC-7 | Trust Windows text handling | Tests cover existing CRLF configuration, Unicode content, and UTF-8 files including BOM handling with an explicitly documented supported behavior. Managed edits preserve unrelated content semantically and do not produce invalid TOML. |
| AC-8 | Keep using the package elsewhere | Existing Bash install/uninstall and test behavior continue to pass in a supported Bash environment. If that environment is unavailable locally, report the gap and obtain evidence through an available suitable runner before claiming regression verification. |
| AC-9 | Reproduce the verification | README includes runnable Windows install, preview, custom target, test/validation, and uninstall commands with prerequisites. QA records Windows and PowerShell versions, Python version, commands, results, and any unverified environment. |

## Non-goals

- Installing or configuring WSL, Bash, Python, Codex, global execution policy, or other global settings automatically.
- Running a real global installation during implementation or verification without explicit authorization.
- Changing the SDLC workflow, agent responsibilities, or approval gates.
- Adding organization extensions or project-mode installation; existing unsupported features remain explicitly rejected.
- Guaranteeing native execution of arbitrary downstream development commands used by installed agents.
- Publishing, opening a pull request, pushing, or deploying this change.

## Assumptions and risks

- Python 3.11+ is an acceptable prerequisite because the current package already relies on Python's `tomllib`; this remains subject to product approval.
- A `python3.exe` command on Windows may be a Windows Store alias rather than a working interpreter. Dependency checks must exercise the selected runtime.
- Windows path separators and quoting must survive PowerShell argument passing and TOML serialization, including spaces and Unicode.
- Existing scripts and tests rely on Unix utilities; merely adding `.ps1` wrappers cannot establish native Windows compatibility.
- CRLF translation and BOMs can affect configuration parsing, content hashing, and uninstall ownership checks. Tests must establish coherent behavior rather than relying on source-control newline settings.
- Antivirus/file locks and permission failures can interrupt filesystem updates. Architecture should define failure reporting and recovery limits; this PRD does not promise full transactional rollback.

## Open questions and approval

No blocking question remains if the recommended approach and Python prerequisite are accepted. PowerShell 7 verification depends on runtime availability; do not install it globally without authorization or claim it was tested when unavailable.

Product approval covers the scope and acceptance criteria only. Reply `Go`, `Approved`, or `Proceed` to advance to architecture under the repository's gated workflow.
