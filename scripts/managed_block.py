#!/usr/bin/env python3
"""Safely insert, replace, or remove one uniquely marked text block."""

from __future__ import annotations

import argparse
import codecs
import os
from pathlib import Path
import shutil
import tempfile
import tomllib
import re


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--content-file", type=Path)
    parser.add_argument("--remove", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--toml", action="store_true")
    return parser.parse_args()


def replace_block(original: str, start: str, end: str, body: str | None) -> str:
    start_count = original.count(start)
    end_count = original.count(end)
    if start_count != end_count or start_count > 1:
        raise ValueError("managed block markers must be balanced and unique")
    if start_count and original.index(end) < original.index(start):
        raise ValueError("managed block markers must be correctly ordered")

    if start_count == 1:
        before, remainder = original.split(start, 1)
        _, after = remainder.split(end, 1)
        before = before.rstrip("\n")
        after = after.lstrip("\n")
        if body is None:
            pieces = [piece for piece in (before, after.rstrip("\n")) if piece]
            return "\n\n".join(pieces) + ("\n" if pieces else "")
    else:
        before = original.rstrip("\n")
        after = ""

    if body is None:
        return original

    managed = f"{start}\n{body.rstrip()}\n{end}"
    pieces = [piece for piece in (before, managed, after.rstrip("\n")) if piece]
    return "\n\n".join(pieces) + "\n"


def managed_bytes(original: bytes, start: str, end: str, body: str | None) -> bytes:
    """Edit UTF-8 text while retaining its BOM and first newline convention."""
    text = original.decode("utf-8-sig")
    match = re.search(r"\r\n|\n|\r", text)
    newline = match.group() if match else "\n"
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    result = replace_block(normalized, start, end, body)
    prefix = codecs.BOM_UTF8 if original.startswith(codecs.BOM_UTF8) else b""
    return prefix + result.replace("\n", newline).encode("utf-8")


def atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def atomic_write(path: Path, content: str) -> None:
    atomic_write_bytes(path, content.encode("utf-8"))


def main() -> int:
    args = parse_args()
    if args.remove == (args.content_file is not None):
        raise SystemExit("provide exactly one of --remove or --content-file")

    original = args.file.read_bytes() if args.file.exists() else b""
    body = None if args.remove else args.content_file.read_text(encoding="utf-8")
    try:
        updated = managed_bytes(original, args.start, args.end, body)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    if args.toml:
        try:
            tomllib.loads(updated.decode("utf-8-sig"))
        except tomllib.TOMLDecodeError as error:
            raise SystemExit(f"managed update would create invalid TOML: {error}") from error

    if updated == original:
        print(f"unchanged: {args.file}")
        return 0
    action = "would update" if args.dry_run else "updated"
    print(f"{action}: {args.file}")
    if args.dry_run:
        return 0

    if args.file.exists() and args.backup_dir:
        args.backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.file, args.backup_dir / args.file.name)
    atomic_write_bytes(args.file, updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
