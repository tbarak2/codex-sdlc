#!/usr/bin/env bash

set -euo pipefail

package_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
codex_home="${CODEX_HOME:-${HOME}/.codex}"
dry_run=false
assume_yes=false

usage() {
  echo "Usage: ./uninstall.sh [--codex-home PATH] [--dry-run] [--yes]"
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

manifest="$codex_home/codex-sdlc-install-manifest.tsv"
[[ -f "$manifest" ]] || { echo "No Codex SDLC manifest found at $manifest" >&2; exit 1; }

if [[ "$dry_run" == false && "$assume_yes" == false && -t 0 ]]; then
  read -r -p "Uninstall managed Codex SDLC files from $codex_home? [y/N] " answer
  [[ "$answer" =~ ^[Yy]$ ]] || exit 1
fi

while IFS=$'\t' read -r expected relative; do
  target="$codex_home/$relative"
  [[ -f "$target" ]] || continue
  actual="$(sha256sum "$target" | awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "retained modified file: $target"
  elif [[ "$dry_run" == true ]]; then
    echo "would remove: $target"
  else
    rm -- "$target"
    echo "removed: $target"
  fi
done < "$manifest"

for specification in \
  "$codex_home/AGENTS.md|<!-- codex-sdlc:start -->|<!-- codex-sdlc:end -->" \
  "$codex_home/config.toml|# codex-sdlc:start|# codex-sdlc:end"; do
  IFS='|' read -r file start end <<< "$specification"
  [[ -f "$file" ]] || continue
  args=(--file "$file" --start "$start" --end "$end" --remove)
  [[ "$dry_run" == true ]] && args+=(--dry-run)
  python3 "$package_root/scripts/managed_block.py" "${args[@]}"
done

if [[ "$dry_run" == false ]]; then
  rm -- "$manifest"
  find "$codex_home/skills/sdlc" "$codex_home/agents" -depth -type d -empty -delete 2>/dev/null || true
  echo "Uninstalled unchanged Codex SDLC files. Modified files and backups were retained."
fi
