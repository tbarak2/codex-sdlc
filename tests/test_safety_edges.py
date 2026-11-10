"""Windows filesystem and text boundaries for the installation lifecycle."""

import base64
import codecs
import hashlib
import os
from pathlib import Path
import shutil
import sys
import unittest

from windows_test_support import MANIFEST, ROOT, InstallerFixture, snapshot


class SafetyEdgesTests(InstallerFixture):
    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"), "requires Windows PowerShell")
    def test_cmd_runtime_does_not_reparse_target_metacharacters(self):
        # Windows PowerShell initializes this profile directory on first startup.
        (self.base / "user" / "AppData" / "Roaming").mkdir(parents=True)
        candidates = self.base / "shims"
        candidates.mkdir()
        (candidates / "python.cmd").write_text(
            f'@"{sys.executable}" %*\n', encoding="utf-8"
        )
        env = self.env.copy()
        env["PATH"] = str(candidates)
        target = self.base / "amp&echo.SDLC_INJECTION_MARKER"
        command = [
            shutil.which("powershell.exe"), "-NoProfile", "-NonInteractive",
            "-ExecutionPolicy", "Bypass", "-File",
            ROOT / "install.ps1", "-Yes", "-CodexHome", target,
        ]
        self.fails_unchanged(lambda: self.run_process(command, env=env), root=self.base)
        self.assertFalse((self.base / "amp").exists(), "batch runtime reparsed target at '&'")
        env["PATH"] += os.pathsep + str(Path(sys.executable).parent)
        result = self.run_process(command, env=env)
        self.succeeds(result)
        self.assertTrue((target / MANIFEST).is_file(), result.stdout + result.stderr)
        self.assertFalse((self.base / "amp").exists(), "batch runtime reparsed target at '&'")

    @unittest.skipUnless(os.name == "nt", "Windows device namespaces")
    def test_device_namespace_targets_cannot_bypass_package_overlap(self):
        package = self.package_copy()
        for prefix in ("\\\\?\\", "\\\\.\\", "//?/", "\\??\\"):
            with self.subTest(prefix=prefix):
                self.fails_unchanged(lambda: self.cli(
                    "install", "--dry-run", "--codex-home", prefix + str(package), package=package
                ), root=package)
                env = self.env.copy()
                env["CODEX_HOME"] = prefix + str(package)
                self.fails_unchanged(lambda: self.cli(
                    "install", "--dry-run", package=package, env=env
                ), root=package)

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"), "requires Windows PowerShell")
    def test_powershell_target_with_trailing_separator(self):
        self.succeeds(self.run_process([
            shutil.which("powershell.exe"), "-NoProfile", "-NonInteractive",
            "-ExecutionPolicy", "Bypass", "-File",
            self.package_copy() / "install.ps1", "-Yes", "-CodexHome", str(self.target) + "\\",
        ]))
        self.assertTrue((self.target / MANIFEST).is_file())

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"), "requires Windows PowerShell")
    def test_old_runtime_and_store_alias_do_not_pass_dependency_probe(self):
        candidates = self.base / "runtime probes"
        candidates.mkdir()
        shim = candidates / "sitecustomize.py"
        probed = candidates / "probe-executed.txt"
        shim.write_text(
            f"import sys\nopen({str(probed)!r}, 'w').close()\nsys.version_info = (3, 10, 0)\n",
            encoding="utf-8",
        )
        env = self.env.copy()
        env["PATH"] = str(Path(sys.executable).parent)
        env["PYTHONPATH"] = str(candidates)
        command = [
            shutil.which("powershell.exe"), "-NoProfile", "-NonInteractive",
            "-ExecutionPolicy", "Bypass", "-File",
            self.package_copy() / "install.ps1", "-DryRun",
        ]
        before = snapshot(self.target)
        result = self.run_process(command, env=env)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(snapshot(self.target), before)
        self.assertIn("3.11", result.stdout + result.stderr)
        self.assertTrue(probed.exists(), "native interpreter never exercised the version probe")
        probed.unlink()
        store = candidates / "WindowsApps"
        link_env = self.env.copy()
        link_env.update({"SDLC_TEST_LINK": str(store), "SDLC_TEST_OUTSIDE": str(Path(sys.executable).parent)})
        create_link = (
            "New-Item -ItemType Junction -Path $env:SDLC_TEST_LINK "
            "-Target $env:SDLC_TEST_OUTSIDE -ErrorAction Stop | Out-Null"
        )
        self.succeeds(self.run_process([
            shutil.which("powershell.exe"), "-NoProfile", "-NonInteractive", "-EncodedCommand",
            base64.b64encode(create_link.encode("utf-16-le")).decode("ascii"),
        ], env=link_env))
        self.addCleanup(os.rmdir, store)
        env["PATH"] = str(store)
        # Control: this is a functional native interpreter, not an inert alias file.
        self.succeeds(self.run_process([store / "python.exe", "-B", "-c", "pass"], env=env))
        self.assertTrue(probed.exists())
        probed.unlink()
        result = self.fails_unchanged(lambda: self.run_process(command, env=env))
        self.assertIn("3.11", result.stdout + result.stderr)
        self.assertFalse(probed.exists(), "runtime discovery invoked a WindowsApps executable")

    def test_lf_and_mixed_newlines_use_first_style_without_bom(self):
        for index, (original, newline) in enumerate((
            (b'model = "keep"\n# sentinel\n', b"\n"),
            (b'model = "keep"\r\n# sentinel\n', b"\r\n"),
        )):
            with self.subTest(newline=newline):
                target = self.base / f"text-{index}"
                target.mkdir()
                path = target / "config.toml"
                path.write_bytes(original)
                self.succeeds(self.cli("install", "--yes", "--codex-home", target))
                installed = path.read_bytes()
                self.assertFalse(installed.startswith(codecs.BOM_UTF8))
                self.assertIn(b"# sentinel" + newline, installed)
                if newline == b"\r\n":
                    self.assertNotIn(b"\n", installed.replace(b"\r\n", b""))
                else:
                    self.assertNotIn(b"\r", installed)
                self.succeeds(self.cli("uninstall", "--yes", "--codex-home", target))
                self.assertEqual(path.read_bytes(), original.replace(b"\r\n", b"\n").replace(b"\n", newline))

    def test_windows_alias_manifest_paths_fail_before_deleting_files(self):
        self.succeeds(self.cli("install", "--yes"))
        manifest = self.target / MANIFEST
        original = manifest.read_text(encoding="utf-8")
        digest = hashlib.sha256(b"sentinel").hexdigest()
        aliases = ("agents/NUL", "agents/con.txt", "skills/file.", "skills/file ")
        for alias in aliases:
            with self.subTest(alias=alias):
                manifest.write_bytes((original + f"{digest}\t{alias}\n").encode())
                self.fails_unchanged(lambda: self.cli("uninstall", "--yes"))

    @unittest.skipUnless(os.name == "nt", "Windows case-insensitive filesystem")
    def test_case_alias_manifest_duplicates_are_rejected(self):
        self.succeeds(self.cli("install", "--yes"))
        manifest = self.target / MANIFEST
        original = manifest.read_text(encoding="utf-8")
        first = original.splitlines()[0]
        digest, relative = first.split("\t")
        folder, filename = relative.rsplit("/", 1)
        manifest.write_bytes((original + f"{digest}\t{folder}/{filename.upper()}\n").encode())
        self.fails_unchanged(lambda: self.cli("uninstall", "--yes"))

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"), "requires Windows junctions")
    def test_junction_at_target_copy_and_backup_paths_is_rejected(self):
        # Junction creation does not require Windows symlink privileges.
        for location in ("target", "agents", "backups"):
            with self.subTest(location=location):
                parent = self.base / location
                parent.mkdir()
                target = parent / "codex"
                outside = parent / "outside"
                outside.mkdir()
                (outside / "sentinel.txt").write_bytes(b"keep-outside")
                if location == "target":
                    link = target
                else:
                    target.mkdir()
                    link = target / location
                env = self.env.copy()
                env.update({"SDLC_TEST_LINK": str(link), "SDLC_TEST_OUTSIDE": str(outside)})
                command = (
                    "New-Item -ItemType Junction -Path $env:SDLC_TEST_LINK "
                    "-Target $env:SDLC_TEST_OUTSIDE -ErrorAction Stop | Out-Null"
                )
                encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
                result = self.run_process([
                    shutil.which("powershell.exe"), "-NoProfile", "-NonInteractive",
                    "-EncodedCommand", encoded,
                ], env=env)
                self.succeeds(result)
                self.addCleanup(os.rmdir, link)
                before = snapshot(outside)
                self.fails_unchanged(lambda: self.cli(
                    "install", "--yes", "--codex-home", target
                ), root=target)
                self.assertEqual(snapshot(outside), before)

    def test_sensitive_package_content_is_rejected(self):
        package = self.package_copy()
        probe = package / "skills" / "sdlc" / "unsafe.txt"
        for content in (
            ".credentials.json", "path=/sessions/example", "path=/cache/example",
            "path=/logs/example", "security_warnings_state",
            "-----BEGIN " + "RSA PRIVATE KEY-----",
            "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
        ):
            with self.subTest(content=content):
                probe.write_bytes(content.encode())
                result = self.cli("validate", package=package)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse(self.target.exists())
