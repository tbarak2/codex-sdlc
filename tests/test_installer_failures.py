"""Deterministic confirmation and filesystem failure behavior."""

import os
from pathlib import Path
import sys
from unittest import mock

from windows_test_support import InstallerFixture, ROOT, snapshot

sys.path.insert(0, str(ROOT / "scripts"))
import package_cli


class FailureTests(InstallerFixture):
    def invoke_main(self, *options):
        with mock.patch.dict(os.environ, self.env), mock.patch.object(
            sys, "argv", ["package_cli.py", "install", *options]
        ):
            return package_cli.main()

    def test_interactive_decline_leaves_target_untouched(self):
        with mock.patch.object(sys.stdin, "isatty", return_value=True), mock.patch(
            "builtins.input", return_value="n"
        ):
            self.assertEqual(self.invoke_main(), 1)
        self.assertFalse(self.target.exists())

    def test_backup_failure_preserves_existing_settings_and_reports_location(self):
        self.seed_settings()
        before = snapshot(self.target)
        with mock.patch.object(package_cli.shutil, "copy2", side_effect=PermissionError("locked backup")), mock.patch(
            "sys.stderr"
        ) as error:
            self.assertEqual(self.invoke_main("--yes"), 1)
        # Creating a backup directory is permitted once mutation starts.
        for relative, content in before.items():
            self.assertEqual(snapshot(self.target)[relative], content)
        self.assertIn("backups", str(error.write.call_args_list))

    def test_atomic_replacement_failure_keeps_old_bytes_and_backup(self):
        self.seed_settings()
        original = (self.target / "AGENTS.md").read_bytes()
        with mock.patch("managed_block.os.replace", side_effect=PermissionError("locked destination")), mock.patch(
            "sys.stderr"
        ) as error:
            self.assertEqual(self.invoke_main("--yes"), 1)
        self.assertEqual((self.target / "AGENTS.md").read_bytes(), original)
        self.assertTrue(any(p.read_bytes() == original for p in (self.target / "backups").rglob("AGENTS.md")))
        self.assertFalse(any(p.name.startswith(".AGENTS.md.") for p in self.target.iterdir()))
        self.assertIn("locked destination", str(error.write.call_args_list))
