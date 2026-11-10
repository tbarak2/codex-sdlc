# Codex SDLC

A portable Codex-native version of Roy's gated software-development workflow.

## Install

### Windows PowerShell

Requires Windows PowerShell 5.1 and Python 3.11 or newer. A working native `py.exe`, `python.exe`, or `python3.exe` must be on PATH. The installer checks the interpreter version and skips batch shims (`.cmd`/`.bat`) and Windows Store aliases; it does not download prerequisites. Bash, Git Bash, WSL, and additional PowerShell modules are not required.

Preview changes, then install:

```powershell
.\install.ps1 -DryRun
.\install.ps1 -Yes
```

Choose another Codex home, including paths with spaces:

```powershell
.\install.ps1 -CodexHome 'C:\My Tools\.codex' -DryRun
.\install.ps1 -CodexHome 'C:\My Tools\.codex' -Yes
```

An explicit `-CodexHome` takes precedence over `CODEX_HOME`, then the default `$HOME\.codex`. Relative targets resolve from your working directory. Without `-Yes`, an interactive installation asks for confirmation. `-Help` works without Python. Organization extensions and project-mode installation remain unsupported.

If Windows blocks script execution, invoke a single child process with a temporary policy override:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DryRun
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Yes
```

This does not change the machine or user execution policy. An organization-enforced policy can still prevent execution; no script changes that policy automatically.

### Bash

Requires Bash, Python 3.11+, and the standard Unix utilities used by the scripts.

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

The PowerShell installer validates configuration, markers, file destinations, and ownership records before writing. Dry-run does not create the target or backups. Reinstalling unchanged content leaves file bytes and timestamps unchanged. Windows paths in generated TOML are escaped correctly. Native managed edits accept UTF-8 with or without a BOM and preserve BOM and uniform LF/CRLF; mixed newlines normalize to the first encountered style. New files use UTF-8 without a BOM and LF.

Changed existing files are backed up under `<codex-home>/backups/codex-sdlc/`. Native file replacements are individually atomic. An interrupted installation can leave earlier changes applied; the error reports the failing path and backup location. There is no whole-install rollback. Symbolic links/junctions in mutation paths, overlapping package/target directories, malformed managed blocks, and unsafe manifest paths are rejected. Use normal Windows drive or UNC paths; device/extended namespace paths (such as `\\?\C:\...`) are unsupported for package and installation locations.

## Validate

Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-package.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\run.ps1
```

The validator checks native PowerShell syntax and package contracts. The standard-library Python test suite launches real PowerShell processes and uses temporary installation targets; it does not modify the active Codex home. Test paths include spaces and Unicode. Windows PowerShell 5.1 and Python 3.12 are exercised locally; PowerShell 7 remains unverified. Symlink tests may skip if Windows denies link creation; junction tests exercise reparse-point rejection without that privilege.

See the [Windows QA results](docs/qa/QA-RESULT-windows-powershell.md) for the tested environment, acceptance results, and verification limits.

Bash:

```bash
bash scripts/validate-package.sh
bash tests/run.sh
```

There is currently no configured formatter, linter, build, or coverage command. Passing tests do not imply 100% coverage.

## Uninstall

Windows PowerShell:

```powershell
.\uninstall.ps1 -DryRun
.\uninstall.ps1 -Yes
```

Use `-CodexHome` for a custom target. If script execution is blocked, use the same process-only invocation as installation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\uninstall.ps1 -Yes
```

Bash:

```bash
./uninstall.sh
```

Uninstall removes unchanged package-owned files and managed blocks only. Locally modified installed files are retained for manual review.

## Other computer

Copy or clone this repository on the other computer. In PowerShell, inspect `.\install.ps1 -DryRun`, then run `.\install.ps1 -Yes`; in Bash, inspect `./install.sh --dry-run`, then run `./install.sh`. Install the prerequisites listed above first. A private Git remote can be added later without changing the package format.
