#!/usr/bin/env bash

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash -n "$root/install.sh" "$root/uninstall.sh" "$root"/scripts/*.sh "$root"/tests/*.sh

python3 - "$root" <<'PY'
from pathlib import Path
import re
import sys
import tomllib

root = Path(sys.argv[1])
expected_agents = {
    "sdlc-pm", "sdlc-architect", "sdlc-ui", "sdlc-developer",
    "sdlc-qa", "sdlc-ui-qa", "sdlc-security", "sdlc-devops",
}
found = set()
for path in sorted((root / "agents").glob("*.toml")):
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    for key in ("name", "description", "sandbox_mode", "developer_instructions"):
        if not data.get(key):
            raise SystemExit(f"{path}: missing {key}")
    found.add(data["name"])
if found != expected_agents:
    raise SystemExit(f"agent mismatch: expected {sorted(expected_agents)}, got {sorted(found)}")

for path in sorted((root / "skills").glob("*/SKILL.md")):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match or "name:" not in match.group(1) or "description:" not in match.group(1):
        raise SystemExit(f"{path}: invalid skill frontmatter")
    if "TODO" in text or "[TODO" in text:
        raise SystemExit(f"{path}: unfinished scaffold")
PY

if grep -RIF --exclude='validate-package.sh' -- '/home/roybarak' "$root/agents" "$root/skills" "$root/scripts" "$root/config" 2>/dev/null; then
  echo "source-machine absolute path found in runtime files" >&2
  exit 1
fi

echo "PASS: package validation"
