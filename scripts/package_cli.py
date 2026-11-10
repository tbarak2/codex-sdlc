#!/usr/bin/env python3
"""Plan and apply native installation without a shell or external dependencies."""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tomllib
import uuid

from managed_block import atomic_write_bytes, managed_bytes, replace_block
from validate_package import AGENT_NAMES, reject_link, validate_package

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "codex-sdlc-install-manifest.tsv"
MARKERS = {
    "AGENTS.md": ("<!-- codex-sdlc:start -->", "<!-- codex-sdlc:end -->"),
    "config.toml": ("# codex-sdlc:start", "# codex-sdlc:end"),
}
DESCRIPTIONS = {
    "sdlc-pm": "Turns a feature request into a testable PRD before architecture or code.",
    "sdlc-architect": "Transforms an approved PRD into concrete technical contracts and architecture.",
    "sdlc-ui": "Defines component, state, responsive, copy, and accessibility contracts.",
    "sdlc-developer": "Implements approved feature specifications and tests, or fast-tracked bug fixes.",
    "sdlc-qa": "Authors pre-code tests and verifies implementation acceptance criteria.",
    "sdlc-ui-qa": "Verifies rendered frontend behavior and E2E tests.",
    "sdlc-security": "Performs a read-only security review of the branch diff.",
    "sdlc-devops": "Checks production build, configuration, CI/CD, and deployment readiness.",
}


@dataclass
class Change:
    path: Path
    content: bytes | None


def check_path(path: Path, file: bool = False) -> None:
    """Inspect lexical ancestors before resolving, so junctions cannot disappear."""
    for component in reversed((path, *path.parents)):
        if os.path.lexists(component):
            reject_link(component)
            if component != path and not component.is_dir():
                raise ValueError(f"parent is not a directory: {component}")
    if path.exists() and (not path.is_file() if file else not path.is_dir()):
        raise ValueError(f"expected {'regular file' if file else 'directory'}: {path}")


def read_file(path: Path) -> bytes:
    check_path(path, file=True)
    return path.read_bytes() if path.exists() else b""


def reject_windows_namespace(path: str) -> None:
    normalized = path.replace("/", "\\")
    if normalized.startswith(("\\\\?\\", "\\\\.\\", "\\??\\")):
        raise ValueError("Windows device/extended namespace paths are not supported; use a normal drive or UNC path")


def valid_relative(relative: str) -> None:
    pieces = relative.split("/")
    if (len(pieces) < 2 or pieces[0] not in ("agents", "skills")
            or any(p in ("", ".", "..") or p.endswith((" ", ".")) for p in pieces)
            or any(c in relative for c in "\\:\t\r\n\x00")
            or any(re.match(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", p, re.I) for p in pieces)):
        raise ValueError(f"unsafe manifest/package path: {relative!r}")


def manifest_rows(home: Path, required: bool = False) -> dict[str, str]:
    path = home / MANIFEST
    raw = read_file(path)
    if not path.exists():
        if required:
            raise ValueError(f"No Codex SDLC manifest found at {path}")
        return {}
    rows = {}
    seen = set()
    for row in raw.decode("utf-8-sig").splitlines():
        columns = row.split("\t")
        if len(columns) != 2 or not re.fullmatch(r"[0-9a-fA-F]{64}", columns[0]):
            raise ValueError(f"invalid manifest row in {path}")
        digest, relative = columns
        valid_relative(relative)
        key = os.path.normcase(relative)
        if key in seen:
            raise ValueError(f"duplicate manifest path: {relative}")
        seen.add(key)
        target = home / relative
        check_path(target, file=True)
        if not target.resolve().is_relative_to(home):
            raise ValueError(f"manifest path escapes target: {relative}")
        rows[relative] = digest.lower()
    if not rows:
        raise ValueError(f"empty manifest: {path}")
    return rows


def settings(home: Path, installing: bool) -> list[Change]:
    changes = []
    for filename, (start, end) in MARKERS.items():
        path = home / filename
        raw = read_file(path)
        try:
            text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
            stripped = replace_block(text, start, end, None)
            if filename == "config.toml":
                data = tomllib.loads(stripped)
                agents = data.get("agents", {})
                if not isinstance(agents, dict):
                    raise ValueError("agents must be a TOML table")
                collisions = AGENT_NAMES.intersection(agents)
                if installing and collisions:
                    raise ValueError("unmanaged Codex agent name collision: " + ", ".join(sorted(collisions)))
                body = "\n".join(
                    f"[agents.{name}]\ndescription = {json.dumps(description)}\n"
                    f"config_file = {json.dumps(str(home / 'agents' / (name + '.toml')))}\n"
                    for name, description in DESCRIPTIONS.items()
                )
            else:
                body = ROOT.joinpath("AGENTS.md").read_text(encoding="utf-8-sig")
                body = body.replace(start, "").replace(end, "").strip()
            updated = managed_bytes(raw, start, end, body if installing else None)
            if filename == "config.toml":
                tomllib.loads(updated.decode("utf-8-sig"))
        except (ValueError, UnicodeError) as error:
            raise ValueError(f"{path}: {error}") from error
        if raw != updated:
            changes.append(Change(path, updated))
    return changes


def plan_install(home: Path) -> list[Change]:
    sources = validate_package(ROOT)
    manifest_rows(home)
    changes = settings(home, installing=True)
    manifest = []
    for source in sources:
        relative = source.relative_to(ROOT).as_posix()
        valid_relative(relative)
        target = home / relative
        original = read_file(target)
        content = source.read_bytes()
        if not target.exists() or original != content:
            changes.append(Change(target, content))
        manifest.append(f"{hashlib.sha256(content).hexdigest()}\t{relative}\n")
    content = "".join(manifest).encode("utf-8")
    if read_file(home / MANIFEST) != content:
        changes.append(Change(home / MANIFEST, content))
    return changes


def plan_uninstall(home: Path) -> list[Change]:
    rows = manifest_rows(home, required=True)
    changes = settings(home, installing=False)
    for relative, digest in rows.items():
        path = home / relative
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest() == digest:
                changes.append(Change(path, None))
            else:
                print(f"retained modified file: {path}")
    changes.append(Change(home / MANIFEST, None))
    return changes


def apply(home: Path, changes: list[Change], dry_run: bool) -> None:
    backup = home / "backups" / "codex-sdlc" / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex
    )
    # Backups are also mutation destinations; check them before any writes.
    check_path(backup)
    for change in changes:
        check_path(change.path, file=True)
        if change.content is not None and change.path.exists():
            check_path(backup / change.path.relative_to(home), file=True)
    for change in changes:
        action = "remove" if change.content is None else "update" if change.path.exists() else "install"
        print(f"{'would ' if dry_run else ''}{action}: {change.path}")
        if dry_run:
            continue
        try:
            if change.content is None:
                change.path.unlink()
            else:
                if change.path.exists():
                    destination = backup / change.path.relative_to(home)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(change.path, destination)
                atomic_write_bytes(change.path, change.content)
        except OSError as error:
            raise OSError(f"failed to {action} {change.path}: {error}; backups: {backup}") from error
    if not changes:
        print(f"unchanged: {home}")


def prune_empty_directories(home: Path, changes: list[Change]) -> None:
    directories = set()
    for change in changes:
        if change.content is None and change.path != home / MANIFEST:
            for parent in change.path.parents:
                if parent in (home, home / "skills"):
                    break
                directories.add(parent)
    for directory in sorted(directories, key=lambda p: len(p.parts), reverse=True):
        if directory.exists():
            check_path(directory)
            if not any(directory.iterdir()):
                directory.rmdir()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("install", "uninstall", "validate"):
        sub = subparsers.add_parser(command)
        if command != "validate":
            sub.add_argument("--codex-home")
            sub.add_argument("--dry-run", action="store_true")
            sub.add_argument("--yes", action="store_true")
        if command == "install":
            sub.add_argument("--with-organization", action="store_true")
            sub.add_argument("--project")
    args = parser.parse_args()
    if args.command != "validate" and args.codex_home == "":
        parser.error("--codex-home must not be empty")
    if args.command == "install" and (args.with_organization or args.project is not None):
        parser.error("Organization extensions and project-mode installation are not supported")
    return args


def main() -> int:
    # Native redirected output can otherwise use a legacy Windows encoding.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    args = parse_args()
    try:
        reject_windows_namespace(str(ROOT))
        if args.command == "validate":
            validate_package(ROOT)
            print("PASS: package validation")
            return 0
        selected = args.codex_home or os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
        reject_windows_namespace(selected)
        home = Path(os.path.abspath(selected))
        check_path(home)
        home = home.resolve()
        if home.is_relative_to(ROOT) or ROOT.is_relative_to(home):
            raise ValueError("package and installation target must not overlap")
        changes = plan_install(home) if args.command == "install" else plan_uninstall(home)
        if not args.dry_run and not args.yes and sys.stdin.isatty():
            if input(f"{args.command.capitalize()} Codex SDLC at {home}? [y/N] ").lower() != "y":
                return 1
        apply(home, changes, args.dry_run)
        if args.command == "uninstall" and not args.dry_run:
            prune_empty_directories(home, changes)
        return 0
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
