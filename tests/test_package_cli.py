"""Behavioral contract for portable installation, without global writes."""

import codecs
import hashlib
from pathlib import Path
import tomllib

from windows_test_support import AGENTS, MANIFEST, ROOT, InstallerFixture, snapshot


class PackageLifecycleTests(InstallerFixture):
    def install(self, *arguments):
        result = self.cli("install", "--yes", *arguments)
        self.succeeds(result)
        return result

    def test_install_content_paths_and_manifest(self):
        self.seed_settings()
        self.install()
        config = tomllib.loads((self.target / "config.toml").read_text("utf-8-sig"))
        self.assertEqual(config["model"], "keep-model")
        self.assertEqual(set(config["agents"]), AGENTS)
        for name in AGENTS:
            installed = self.target / "agents" / f"{name}.toml"
            self.assertEqual(Path(config["agents"][name]["config_file"]), installed.resolve())
            self.assertEqual(installed.read_bytes(), (ROOT / "agents" / installed.name).read_bytes())
        expected = {
            path.relative_to(ROOT).as_posix()
            for folder in ("agents", "skills")
            for path in (ROOT / folder).rglob("*") if path.is_file()
        }
        manifest = {}
        for row in (self.target / MANIFEST).read_text("utf-8").splitlines():
            digest, relative = row.split("\t")
            self.assertNotIn(relative, manifest)
            self.assertEqual(digest, hashlib.sha256((self.target / relative).read_bytes()).hexdigest())
            manifest[relative] = digest
        self.assertEqual(set(manifest), expected)
        self.assertEqual((self.target / "unrelated.txt").read_bytes(), b"keep-file")

    def test_dry_run_missing_and_populated_target_creates_nothing(self):
        for populated in (False, True):
            with self.subTest(populated=populated):
                if populated:
                    self.seed_settings()
                before = snapshot(self.target)
                result = self.cli("install", "--dry-run")
                self.succeeds(result)
                self.assertIn("would", result.stdout.lower())
                self.assertEqual(snapshot(self.target), before)

    def test_reinstall_is_byte_and_timestamp_idempotent(self):
        self.install()
        before = snapshot(self.target)
        times = {p.relative_to(self.target): p.stat().st_mtime_ns
                 for p in self.target.rglob("*") if p.is_file()}
        self.install()
        self.assertEqual(snapshot(self.target), before)
        self.assertEqual({p.relative_to(self.target): p.stat().st_mtime_ns
                          for p in self.target.rglob("*") if p.is_file()}, times)
        self.assertEqual((self.target / "AGENTS.md").read_text("utf-8").count(
            "<!-- codex-sdlc:start -->"), 1)

    def test_update_backs_up_changed_files_and_settings(self):
        self.seed_settings()
        self.install()
        agent = self.target / "agents" / "sdlc-pm.toml"
        agent.write_bytes(b"user modified agent")
        original_config = (self.target / "config.toml").read_bytes()
        # Replace a managed description while keeping TOML valid.
        (self.target / "config.toml").write_bytes(original_config.replace(
            b"Turns a feature request", b"Local description of a feature request"))
        modified_config = (self.target / "config.toml").read_bytes()
        self.assertNotEqual(modified_config, original_config)
        self.install()
        backups = self.target / "backups" / "codex-sdlc"
        self.assertTrue(any(p.read_bytes() == b"user modified agent"
                            for p in backups.rglob("sdlc-pm.toml")))
        self.assertTrue(any(p.read_bytes() == modified_config
                            for p in backups.rglob("config.toml")))

    def test_target_precedence_and_relative_explicit_path(self):
        explicit = self.base / "explicit home"
        self.install("--codex-home", explicit.name)
        self.assertTrue((explicit / MANIFEST).is_file())
        self.assertFalse(self.target.exists())
        self.install()
        self.assertTrue((self.target / MANIFEST).is_file())
        env = self.env.copy()
        env.pop("CODEX_HOME")
        default = self.base / "user" / ".codex"
        self.succeeds(self.cli("install", "--yes", env=env))
        self.assertTrue((default / MANIFEST).is_file())

    def test_utf8_bom_crlf_and_unicode_survive_full_lifecycle(self):
        self.target.mkdir()
        originals = {
            "config.toml": codecs.BOM_UTF8 + 'model = "\u05e9\u05dc\u05d5\u05dd"\r\n# keep\r\n'.encode(),
            "AGENTS.md": codecs.BOM_UTF8 + '# \u05e9\u05dc\u05d5\u05dd\r\nkeep rule\r\n'.encode(),
        }
        for name, content in originals.items():
            (self.target / name).write_bytes(content)
        self.install()
        for name in originals:
            raw = (self.target / name).read_bytes()
            self.assertTrue(raw.startswith(codecs.BOM_UTF8))
            self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))
            self.assertIn("\u05e9\u05dc\u05d5\u05dd", raw.decode("utf-8-sig"))
        tomllib.loads((self.target / "config.toml").read_text("utf-8-sig"))
        self.succeeds(self.cli("uninstall", "--yes"))
        for name in originals:
            self.assertEqual((self.target / name).read_bytes(), originals[name])

    def test_uninstall_preview_and_modified_file_retention(self):
        self.seed_settings()
        self.install()
        changed = self.target / "agents" / "sdlc-pm.toml"
        changed.write_bytes(b"keep edited agent")
        before = snapshot(self.target)
        self.succeeds(self.cli("uninstall", "--dry-run"))
        self.assertEqual(snapshot(self.target), before)
        backup_before = snapshot(self.target / "backups")
        result = self.cli("uninstall", "--yes")
        self.succeeds(result)
        self.assertIn("retain", result.stdout.lower())
        self.assertEqual(changed.read_bytes(), b"keep edited agent")
        self.assertFalse((self.target / "agents" / "sdlc-qa.toml").exists())
        self.assertFalse((self.target / MANIFEST).exists())
        self.assertEqual((self.target / "unrelated.txt").read_bytes(), b"keep-file")
        backup_after = snapshot(self.target / "backups")
        for relative, content in (backup_before or {}).items():
            self.assertEqual(backup_after[relative], content)
        self.assertNotIn("codex-sdlc:start", (self.target / "config.toml").read_text("utf-8"))
        self.assertIn("keep-user-rule", (self.target / "AGENTS.md").read_text("utf-8"))


class PreflightTests(InstallerFixture):
    def test_invalid_settings_markers_and_collisions_fail_without_changes(self):
        self.seed_settings()
        cases = [
            ("config.toml", b"invalid = ["),
            ("config.toml", b'[agents.sdlc-pm]\ndescription = "mine"\n'),
            ("config.toml", b"# codex-sdlc:start\n"),
            ("config.toml", b"# codex-sdlc:end\n# codex-sdlc:start\n"),
            ("config.toml", b"# codex-sdlc:start\n# codex-sdlc:end\n" * 2),
            ("AGENTS.md", b"<!-- codex-sdlc:start -->\n"),
            ("AGENTS.md", b"<!-- codex-sdlc:end -->\n<!-- codex-sdlc:start -->\n"),
            ("AGENTS.md", b"<!-- codex-sdlc:start -->\n<!-- codex-sdlc:end -->\n" * 2),
            ("AGENTS.md", b"\xff\xfeinvalid UTF8"),
        ]
        for filename, content in cases:
            with self.subTest(filename=filename, content=content):
                path = self.target / filename
                original = path.read_bytes()
                path.write_bytes(content)
                self.fails_unchanged(lambda: self.cli("install", "--yes"))
                path.write_bytes(original)

    def test_unknown_empty_and_reserved_options_fail_without_changes(self):
        for options in (("--unknown",), ("--codex-home", ""),
                        ("--with-organization",), ("--project", "somewhere")):
            with self.subTest(options=options):
                result = self.fails_unchanged(lambda: self.cli("install", "--yes", *options))
                self.assertEqual(result.returncode, 2)

    def test_directory_at_copy_destination_is_rejected_before_writes(self):
        (self.target / "agents" / "sdlc-pm.toml").mkdir(parents=True)
        self.fails_unchanged(lambda: self.cli("install", "--yes"))

    def test_corrupt_manifest_is_rejected_before_any_uninstall(self):
        self.succeeds(self.cli("install", "--yes"))
        outside = self.base / "outside.txt"
        outside.write_bytes(b"outside sentinel")
        digest = hashlib.sha256(outside.read_bytes()).hexdigest()
        rows = [f"{digest}\t{path}\n" for path in (
            "../outside.txt", str(outside.resolve()), "agents/../../outside.txt",
            "agents/../sdlc-pm.toml", "agents\\sdlc-pm.toml",
            "agents/file:stream", "C:/outside.txt", "//server/share/file", "unrelated.txt",
        )]
        original = (self.target / MANIFEST).read_text("utf-8")
        rows.extend(["bad row\n", "not-a-hash\tagents/sdlc-pm.toml\n",
                     original.splitlines()[0] + "\n"])
        for row in rows:
            with self.subTest(row=row):
                (self.target / MANIFEST).write_text(original + row, encoding="utf-8")
                self.fails_unchanged(lambda: self.cli("uninstall", "--yes"))
                self.fails_unchanged(lambda: self.cli("install", "--yes"))
                self.assertEqual(outside.read_bytes(), b"outside sentinel")

    def test_uninstall_missing_manifest_fails_without_writes(self):
        self.seed_settings()
        self.fails_unchanged(lambda: self.cli("uninstall", "--yes"))

    def test_uninstall_preflights_both_managed_files_before_removal(self):
        self.succeeds(self.cli("install", "--yes"))
        (self.target / "AGENTS.md").write_bytes(b"<!-- codex-sdlc:start -->\n")
        self.fails_unchanged(lambda: self.cli("uninstall", "--yes"))

    def test_package_target_overlap_is_rejected(self):
        package = self.package_copy()
        self.fails_unchanged(lambda: self.cli(
            "install", "--yes", "--codex-home", str(package / "target"), package=package
        ), root=package)

    def test_linked_destination_cannot_modify_outside_target(self):
        self.target.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        link = self.target / "agents"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlink creation unavailable: {error}")
        self.addCleanup(link.unlink)
        before = snapshot(outside)
        self.fails_unchanged(lambda: self.cli("install", "--yes"))
        self.assertEqual(snapshot(outside), before)

    def test_portable_package_validation(self):
        self.succeeds(self.cli("validate"))
        package = self.package_copy()
        (package / "agents" / "sdlc-pm.toml").write_bytes(b"broken = [")
        result = self.cli("validate", package=package)
        self.assertNotEqual(result.returncode, 0)
