#!/usr/bin/env bash

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash -n "$root/install.sh" "$root/uninstall.sh" "$root"/scripts/*.sh "$root"/tests/*.sh

python3 -B "$root/scripts/validate_package.py" "$root"

if grep -RIF --exclude='validate-package.sh' -- '/home/roybarak' "$root/agents" "$root/skills" "$root/scripts" "$root/config" 2>/dev/null; then
  echo "source-machine absolute path found in runtime files" >&2
  exit 1
fi
