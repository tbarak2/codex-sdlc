"""Isolated subprocess fixtures for the Windows installer contract."""

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
AGENTS = {f"sdlc-{name}" for name in (
    "pm", "architect", "ui", "developer", "qa", "ui-qa", "security", "devops"
)}
MANIFEST = "codex-sdlc-install-manifest.tsv"


def snapshot(root):
    """Include empty directories and bytes, so dry-run cannot hide writes."""
    if not root.exists():
        return None
    return {
        path.relative_to(root).as_posix(): None if path.is_dir() else path.read_bytes()
        for path in sorted(root.rglob("*"))
    }


class InstallerFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sdlc-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.target = self.base / "Codex Home \u05e9\u05dc\u05d5\u05dd"
        self.env = os.environ.copy()
        self.env.update({
            "CODEX_HOME": str(self.target), "PYTHONUTF8": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "HOME": str(self.base / "user"),
            "USERPROFILE": str(self.base / "user"),
        })

    def package_copy(self):
        package = self.base / "Package With Spaces \u05e9\u05dc\u05d5\u05dd"
        shutil.copytree(ROOT, package, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", ".pytest_cache"
        ))
        return package

    def run_process(self, arguments, env=None, cwd=None):
        return subprocess.run(
            [str(item) for item in arguments], cwd=cwd or self.base,
            env=self.env if env is None else env, input="", capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=45,
        )

    def cli(self, command="install", *arguments, package=ROOT, env=None):
        script = package / "scripts" / "package_cli.py"
        self.assertTrue(script.is_file(), "planned portable lifecycle CLI is missing")
        return self.run_process(
            [sys.executable, "-B", script, command, *arguments], env=env
        )

    def succeeds(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def fails_unchanged(self, invoke, root=None):
        root = root or self.target
        before = snapshot(root)
        result = invoke()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(snapshot(root), before, "rejected operation changed target")
        self.assertTrue((result.stdout + result.stderr).strip(), "missing diagnostic")
        return result

    def seed_settings(self):
        self.target.mkdir(parents=True)
        (self.target / "config.toml").write_bytes(b'model = "keep-model"\n# keep-config\n')
        (self.target / "AGENTS.md").write_bytes(b"# keep-user-rule\n")
        (self.target / "unrelated.txt").write_bytes(b"keep-file")
