#!/usr/bin/env python3
"""Portable, standard-library validation of distributable package assets."""

from pathlib import Path
import re
import stat
import sys
import tomllib

AGENT_NAMES = {f"sdlc-{role}" for role in (
    "pm", "architect", "ui", "developer", "qa", "ui-qa", "security", "devops"
)}


def reject_link(path: Path) -> None:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError(f"links/reparse points are not supported: {path}")


def package_files(root: Path) -> list[Path]:
    files = []
    for folder in ("agents", "skills"):
        directory = root / folder
        reject_link(directory)
        if not directory.is_dir():
            raise ValueError(f"package directory missing: {directory}")
        for path in sorted(directory.rglob("*")):
            reject_link(path)
            if path.is_file():
                files.append(path)
            elif not path.is_dir():
                raise ValueError(f"package asset is not a regular file: {path}")
    return sorted(files)


def validate_package(root: Path) -> list[Path]:
    files = package_files(root)
    found = []
    for path in (root / "agents").glob("*.toml"):
        data = tomllib.loads(path.read_text(encoding="utf-8-sig"))
        for key in ("name", "description", "sandbox_mode", "developer_instructions"):
            if not isinstance(data.get(key), str) or not data[key]:
                raise ValueError(f"{path}: missing or invalid {key}")
        if path.stem != data["name"]:
            raise ValueError(f"{path}: agent name differs from filename")
        found.append(data["name"])
    if set(found) != AGENT_NAMES or len(found) != len(AGENT_NAMES):
        raise ValueError("package must contain exactly the eight core agents")
    if not (root / "skills" / "sdlc" / "SKILL.md").is_file():
        raise ValueError("package is missing the sdlc skill")
    for path in (root / "skills").glob("*/SKILL.md"):
        text = path.read_text(encoding="utf-8-sig")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if not match or "name:" not in match[1] or "description:" not in match[1]:
            raise ValueError(f"{path}: invalid skill frontmatter")
        if "TODO" in text:
            raise ValueError(f"{path}: unfinished scaffold")
    source_path = "/home/" + "roybarak"
    forbidden = ["." + "credentials.json", "security_" + "warnings_state"]
    forbidden += ["/" + name + "/" for name in ("sessions", "file-history", "cache", "log", "logs")]
    private_key = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
    for path in files:
        text = path.read_text(encoding="utf-8-sig")
        if source_path in text or private_key.search(text) or any(token in text for token in forbidden):
            raise ValueError(f"{path}: forbidden runtime path, source path or private key")
    return files


if __name__ == "__main__":
    try:
        validate_package(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
        print("PASS: package validation")
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error
