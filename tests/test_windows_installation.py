"""Exercise the public commands in actual Windows PowerShell subprocesses."""

import os
from pathlib import Path
import shutil
import sys
import tomllib
import unittest

from windows_test_support import AGENTS, MANIFEST, ROOT, InstallerFixture, snapshot

POWERSHELL = shutil.which("powershell.exe")


@unittest.skipUnless(os.name == "nt" and POWERSHELL, "requires Windows PowerShell")
class WindowsCommandsTests(InstallerFixture):
    def ps(self, name="install.ps1", *arguments, package=ROOT, env=None):
        script = package / name
        self.assertTrue(script.is_file(), f"planned PowerShell command is missing: {name}")
        return self.run_process([
            POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", script, *arguments,
        ], env=env)

    def test_real_windows_lifecycle_with_unicode_package_and_target(self):
        package = self.package_copy()
        # Runtime discovery may find Python; no Bash, WSL, sed or find is on PATH.
        env = self.env.copy()
        env["PATH"] = str(Path(sys.executable).parent)
        before = snapshot(self.target)
        self.succeeds(self.ps("install.ps1", "-DryRun", package=package, env=env))
        self.assertEqual(snapshot(self.target), before)
        self.succeeds(self.ps("install.ps1", "-Yes", "-CodexHome", str(self.target),
                              package=package, env=env))
        self.assertTrue((self.target / MANIFEST).is_file())
        config = tomllib.loads((self.target / "config.toml").read_text("utf-8-sig"))
        self.assertEqual(set(config["agents"]), AGENTS)
        for name in AGENTS:
            self.assertEqual(Path(config["agents"][name]["config_file"]),
                             (self.target / "agents" / f"{name}.toml").resolve())
        before = snapshot(self.target)
        self.succeeds(self.ps("install.ps1", "-Yes", package=package, env=env))
        self.assertEqual(snapshot(self.target), before)
        self.succeeds(self.ps("uninstall.ps1", "-DryRun", package=package, env=env))
        self.assertEqual(snapshot(self.target), before)
        self.succeeds(self.ps("uninstall.ps1", "-Yes", package=package, env=env))
        self.assertFalse((self.target / MANIFEST).exists())
        self.assertFalse((self.target / "agents" / "sdlc-pm.toml").exists())
        self.assertFalse(any(package.rglob("__pycache__")), "commands wrote bytecode into package")

    def test_help_succeeds_without_python_or_target_writes(self):
        env = self.env.copy()
        env["PATH"] = ""
        for script in ("install.ps1", "uninstall.ps1"):
            with self.subTest(script=script):
                self.succeeds(self.ps(script, "-Help", env=env))
                self.assertFalse(self.target.exists())

    def test_missing_python_reports_prerequisite_without_writes(self):
        env = self.env.copy()
        env["PATH"] = ""
        for script in ("install.ps1", "uninstall.ps1"):
            with self.subTest(script=script):
                result = self.fails_unchanged(lambda: self.ps(script, "-Yes", env=env))
                self.assertIn("python", (result.stdout + result.stderr).lower())
                self.assertIn("3.11", result.stdout + result.stderr)

    def test_batch_candidates_are_skipped_and_native_discovery_can_fall_back(self):
        candidates = self.base / "runtime candidates"
        candidates.mkdir()
        for name in ("py", "python", "python3"):
            (candidates / f"{name}.cmd").write_bytes(b"@exit /b 1\r\n")
        env = self.env.copy()
        env["PATH"] = str(candidates)
        result = self.fails_unchanged(lambda: self.ps("install.ps1", "-DryRun", env=env))
        self.assertIn("python", (result.stdout + result.stderr).lower())
        # A native exe behind same-name batch shims must still be discovered.
        env["PATH"] = str(candidates) + os.pathsep + str(Path(sys.executable).parent)
        self.succeeds(self.ps("install.ps1", "-DryRun", env=env))
        self.assertFalse(self.target.exists())

    def test_unknown_and_reserved_options_fail_without_writes(self):
        for options in (("-UnknownOption",), ("-WithOrganization",),
                        ("-Project", "somewhere"), ("-CodexHome",)):
            with self.subTest(options=options):
                self.fails_unchanged(lambda: self.ps("install.ps1", *options))

    def test_old_version_probe_rejected_and_windowsapps_alias_not_launched(self):
        # Exercise the actual native executable's probe with a simulated version.
        candidates = self.base / "old runtime"
        candidates.mkdir()
        (candidates / "sitecustomize.py").write_text("import sys\nsys.version_info=(3,10)\n", encoding="utf-8")
        env = self.env.copy()
        env["PATH"] = str(Path(sys.executable).parent)
        env["PYTHONPATH"] = str(candidates)
        result = self.fails_unchanged(lambda: self.ps("install.ps1", "-DryRun", env=env))
        self.assertIn("3.11", result.stdout + result.stderr)
        aliases = self.base / "WindowsApps"
        aliases.mkdir()
        marker = self.base / "alias-launched.txt"
        (aliases / "python.cmd").write_text(
            f'@echo launched > "{marker}"\r\n@exit /b 0\r\n', encoding="utf-8"
        )
        env["PATH"] = str(aliases)
        env.pop("PYTHONPATH")
        self.fails_unchanged(lambda: self.ps("install.ps1", "-DryRun", env=env))
        self.assertFalse(marker.exists(), "WindowsApps alias was launched")

    def test_configuration_failure_exit_propagates_without_writes(self):
        self.seed_settings()
        (self.target / "config.toml").write_bytes(b"invalid = [")
        result = self.fails_unchanged(lambda: self.ps("install.ps1", "-Yes"))
        self.assertIn("config.toml", result.stdout + result.stderr)

    def test_native_package_validation_command(self):
        self.succeeds(self.ps("scripts/validate-package.ps1"))
