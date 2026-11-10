# Test plan: Windows PowerShell installation

Status: pre-development QA approved by the user's `Go` on 2026-11-10; implementation authorized.

Inputs: approved [PRD](../prd/PRD-windows-powershell.md) and [architecture](../arch/ARCH-windows-powershell.md). No frontend changes; browser/UI testing is not applicable.

## Environment and isolation

Baseline executed on 2026-11-10 using Windows PowerShell 5.1.26100.9711 and Python 3.12.10. PowerShell 7 is unavailable. No additional packages or global configuration changes are needed for this suite.

Each test owns a `TemporaryDirectory`. Child-process environments set `CODEX_HOME`, `HOME`, and `USERPROFILE` to fixture locations, without changing the invoking process environment. Default-target tests also point the child user's home into that fixture. No test installs into the actual Codex home. Repository-copy tests use paths containing spaces and Hebrew characters. Child Python uses UTF-8 mode for deterministic capture; default legacy console encoding remains a separate check.

PowerShell subprocesses use `-NoProfile -NonInteractive -ExecutionPolicy Bypass -File`; the execution-policy override is limited to that child process. Mutation commands pass `-Yes`. The public-command lifecycle test restricts PATH to the real Python executable directory, so Bash/WSL/Unix tools cannot satisfy hidden dependencies. Package imports must not leave `__pycache__` in the copied source.

## Executable tests

- `tests/windows_test_support.py`: process fixtures, target snapshots including empty directories, explicit assertions that planned commands exist, and unchanged-target failure checks.
- `tests/test_package_cli.py`: portable CLI lifecycle and safety contracts; no imports of nonexistent implementation modules.
- `tests/test_windows_installation.py`: actual Windows PowerShell entry-point subprocesses, with a platform skip outside Windows.

Tests deliberately assert that a planned entry point exists before invoking it. A negative-case test therefore cannot pass merely because the implementation file is absent. No private Python function names or PowerShell helper APIs are prescribed.

## Acceptance matrix

| Criterion | Automated cases | Additional verification before acceptance |
|---|---|---|
| AC-1 Native installation | Windows lifecycle from Unicode repository copy with no Bash on PATH; eight agents, valid TOML paths, manifest; help; failure exit propagation; native validator | Execute suite after implementation; review scripts for process dependencies |
| AC-2 Target selection and paths | Explicit relative target overrides environment; environment overrides fixture home; default fixture home; source and destination with spaces/Unicode; every TOML agent path resolves correctly | Inspect README examples on Windows; empty PowerShell target value behavior |
| AC-3 Safe preview | Missing/populated target install dry-runs compare all bytes and directories; portable and PowerShell uninstall previews; no Python cache in package copy | Review implementation for no-write planning, including backup creation |
| AC-4 Preservation and updates | Unrelated model/rules/files retained; changed agent/config backed up; repeat install preserves all bytes and file mtimes; unique managed block | Inspect manifest replacement backup and interrupted-I/O reporting |
| AC-5 Errors and prerequisites | Invalid TOML, agent collision, unbalanced/reversed/duplicate markers in both files, invalid UTF-8, directory collision, unknown/empty/reserved options; missing and unusable Python candidates; fallback from unusable launcher; unchanged-target assertion | Add targeted old-version and WindowsApps alias probes once helper exists; verify no Store launch and version rejection; confirmation decline/interactive prompt |
| AC-6 Safe removal | Preview unchanged; modified installed agent retained/reported; unchanged files removed; unrelated content and existing backups preserved; malformed/duplicate manifest rows, traversal/absolute/UNC/drive/backslash/ADS paths rejected for install and uninstall; missing manifest; both managed files preflighted before removal | Windows junction/reparse-point case, including backup/manifest components; existing symlink test may require privileges |
| AC-7 Text handling | BOM, CRLF, Hebrew content and valid TOML through install/uninstall; exact original simple fixtures restored | Add mixed-newline normalization and LF-without-BOM cases during implementation; shared managed-block CLI Bash compatibility |
| AC-8 Bash compatibility | Existing `tests/run.sh` and `scripts/validate-package.sh` retained as regression commands | Execute in demonstrated functioning Bash with Python 3.11+; executable presence alone is insufficient |
| AC-9 Reproduction/docs | Native validation command contract | Review README for prerequisites, preview/install/custom target/tests/uninstall, process-only policy troubleshooting, text behavior, and tested versus unverified environments; record final QA evidence |

No acceptance criterion is currently passed: these are pre-code tests, and the new implementation is absent. Deferred checks above remain explicit requirements for implementation/verification, rather than implied coverage from the initial suite.

## Boundaries, failure paths, and authorization

The safety tests append malicious manifest rows after valid rows, ensuring whole-manifest validation must finish before any deletion. A sentinel outside the target must remain unchanged. Source/target overlap is rejected against a copied repository. A symlinked destination must not modify an outside fixture. The test skips that single case if Windows denies link creation; a later nonprivileged junction test or capable runner must supply reparse-point evidence.

Production verification must also cover invalid package assets, package links, malformed existing manifest at install, Windows reparse points at target/backup/manifest ancestors, failures during backup/atomic replacement, missing target-parent permissions, and mixed newlines. The current suite covers malformed package TOML and manifest-at-install cases; additional cases should be added with the implementation where deterministic fixtures become available. Whole-install rollback and adversarial concurrent modification are excluded by architecture.

Global install, dependency downloads, execution-policy changes, pushes, PRs, deployment, and shipping are not part of this test run. Manual authorization checks verify no such action occurs. The proposed implementation must not automatically install Python or other prerequisites.

## Commands and pre-code results

Syntax check, avoiding bytecode files:

```powershell
python -B -c "import ast,pathlib; paths=list(pathlib.Path('tests').glob('*.py')); [ast.parse(p.read_text(encoding='utf-8'),filename=str(p)) for p in paths]; print('PASS: AST syntax for',len(paths),'test files')"
```

Result: PASS, all three test/helper files parse.

Suite:

```powershell
python -B -m unittest discover -s tests -p 'test_*.py'
```

Baseline: 23 test methods, 39 assertion failures including subtests, zero errors, one skip. Failures are exclusively explicit missing-entry-point assertions for `scripts/package_cli.py`, `install.ps1`, `uninstall.ps1`, and `scripts/validate-package.ps1`. This is the expected pre-implementation result, not evidence of Windows compatibility. The skipped link case reports Windows error 1314 (symlink privilege unavailable). A compact `unittest.TextTestRunner` summary was also executed after the final fixture additions to verify these counts and diagnoses without truncating output.

After implementation, required commands include:

```powershell
powershell.exe -NoProfile -File .\scripts\validate-package.ps1
powershell.exe -NoProfile -File .\tests\run.ps1
python -B -m unittest discover -s tests -p 'test_*.py'
```

Existing regressions, in a functioning Bash environment:

```bash
bash scripts/validate-package.sh
bash tests/run.sh
```

PowerShell 7 is unverified until corresponding `pwsh` commands run. Bash regressions have not been run in this phase. There is no configured formatter, linter, build, or coverage command; do not claim those checks or 100% coverage. Resolve the coverage-tooling decision before marking the feature finished or pushing under the repository's finish gate.

## Handoff

Pre-code readiness: PASS for a syntactically valid initial executable contract and mapped follow-up checks. Production acceptance: pending. No production code was changed. Reply `Go`, `Approved`, or `Proceed` to authorize the development phase under the repository workflow.
