#!/usr/bin/env bash

set -euo pipefail

package_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
codex_home="${CODEX_HOME:-${HOME}/.codex}"
dry_run=false
assume_yes=false
with_organization=false
project_path=""

usage() {
  echo "Usage: ./install.sh [--codex-home PATH] [--dry-run] [--yes] [--with-organization] [--project PATH]"
}

while (($#)); do
  case "$1" in
    --codex-home)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      codex_home="$2"
      shift 2
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    --yes)
      assume_yes=true
      shift
      ;;
    --with-organization)
      with_organization=true
      shift
      ;;
    --project)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      project_path="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$with_organization" == true ]]; then
  echo "Organization extensions are not included in version $(<"$package_root/VERSION")." >&2
  exit 2
fi

if [[ -n "$project_path" ]]; then
  echo "Project-mode installation is reserved for a later milestone; core global installation is available." >&2
  exit 2
fi

if [[ "$dry_run" == false && "$assume_yes" == false && -t 0 ]]; then
  read -r -p "Install Codex SDLC into $codex_home? [y/N] " answer
  [[ "$answer" =~ ^[Yy]$ ]] || exit 1
fi

bash "$package_root/scripts/validate-package.sh"

temporary_dir="$(mktemp -d)"
trap 'rm -rf -- "$temporary_dir"' EXIT
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="$codex_home/backups/codex-sdlc/$timestamp"
manifest="$codex_home/codex-sdlc-install-manifest.tsv"

if [[ "$dry_run" == true ]]; then
  echo "DRY RUN: target $codex_home"
else
  mkdir -p "$codex_home/agents" "$codex_home/skills"
fi

copy_file() {
  local source="$1"
  local destination="$2"
  local relative="$3"
  if [[ -f "$destination" ]] && cmp -s "$source" "$destination"; then
    echo "unchanged: $destination"
  elif [[ "$dry_run" == true ]]; then
    echo "would install: $destination"
  else
    if [[ -f "$destination" ]]; then
      mkdir -p "$backup_dir/$(dirname "$relative")"
      cp -p "$destination" "$backup_dir/$relative"
    fi
    mkdir -p "$(dirname "$destination")"
    cp -p "$source" "$destination"
    echo "installed: $destination"
  fi
}

while IFS= read -r source; do
  relative="${source#"$package_root/"}"
  copy_file "$source" "$codex_home/$relative" "$relative"
done < <(find "$package_root/agents" -type f -name '*.toml' | sort)

while IFS= read -r source; do
  relative="${source#"$package_root/"}"
  copy_file "$source" "$codex_home/$relative" "$relative"
done < <(find "$package_root/skills" -type f | sort)

sed '/<!-- codex-sdlc:start -->/d; /<!-- codex-sdlc:end -->/d' "$package_root/AGENTS.md" > "$temporary_dir/agents-body.md"

managed_args=(
  --file "$codex_home/AGENTS.md"
  --start '<!-- codex-sdlc:start -->'
  --end '<!-- codex-sdlc:end -->'
  --content-file "$temporary_dir/agents-body.md"
  --backup-dir "$backup_dir"
)
[[ "$dry_run" == true ]] && managed_args+=(--dry-run)
python3 "$package_root/scripts/managed_block.py" "${managed_args[@]}"

python3 - "$codex_home" "$temporary_dir/config-body.toml" <<'PY'
from pathlib import Path
import json
import sys

home = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2])
agents = {
    "sdlc-pm": "Turns a feature request into a testable PRD before architecture or code.",
    "sdlc-architect": "Transforms an approved PRD into concrete technical contracts and architecture.",
    "sdlc-ui": "Defines component, state, responsive, copy, and accessibility contracts.",
    "sdlc-developer": "Implements approved feature specifications and tests, or fast-tracked bug fixes.",
    "sdlc-qa": "Authors pre-code tests and verifies implementation acceptance criteria.",
    "sdlc-ui-qa": "Verifies rendered frontend behavior and E2E tests.",
    "sdlc-security": "Performs a read-only security review of the branch diff.",
    "sdlc-devops": "Checks production build, configuration, CI/CD, and deployment readiness.",
}
lines = []
for name, description in agents.items():
    lines.extend([
        f"[agents.{name}]",
        f"description = {json.dumps(description)}",
        f"config_file = {json.dumps(str(home / 'agents' / f'{name}.toml'))}",
        "",
    ])
output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
PY

config_args=(
  --file "$codex_home/config.toml"
  --start '# codex-sdlc:start'
  --end '# codex-sdlc:end'
  --content-file "$temporary_dir/config-body.toml"
  --backup-dir "$backup_dir"
)
[[ "$dry_run" == true ]] && config_args+=(--dry-run)
python3 "$package_root/scripts/managed_block.py" "${config_args[@]}"

if [[ "$dry_run" == false ]]; then
  : > "$temporary_dir/manifest.tsv"
  while IFS= read -r source; do
    relative="${source#"$package_root/"}"
    checksum="$(sha256sum "$codex_home/$relative" | awk '{print $1}')"
    printf '%s\t%s\n' "$checksum" "$relative" >> "$temporary_dir/manifest.tsv"
  done < <(find "$package_root/agents" "$package_root/skills" -type f | sort)
  mv "$temporary_dir/manifest.tsv" "$manifest"
  echo "Installed Codex SDLC $(<"$package_root/VERSION") into $codex_home"
fi
