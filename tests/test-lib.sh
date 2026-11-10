#!/usr/bin/env bash

set -euo pipefail

TEST_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_file() {
  [[ -f "$1" ]] || fail "expected file: $1"
}

assert_dir() {
  [[ -d "$1" ]] || fail "expected directory: $1"
}

assert_contains() {
  local file="$1"
  local text="$2"
  grep -Fq -- "$text" "$file" || fail "expected '$text' in $file"
}

assert_count() {
  local expected="$1"
  local pattern="$2"
  local file="$3"
  local actual
  actual="$(grep -Fc -- "$pattern" "$file" || true)"
  [[ "$actual" == "$expected" ]] || fail "expected $expected occurrences of '$pattern' in $file; got $actual"
}

tree_digest() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    printf '%s\n' missing
    return
  fi
  find "$path" -type f -print0 \
    | sort -z \
    | xargs -0 sha256sum \
    | sha256sum \
    | awk '{print $1}'
}

new_fixture() {
  FIXTURE_ROOT="$(mktemp -d)"
  export HOME="$FIXTURE_ROOT/home"
  export CODEX_HOME="$HOME/.codex"
  mkdir -p "$CODEX_HOME"
  trap 'rm -rf -- "$FIXTURE_ROOT"' EXIT
}

run_installer() {
  "$TEST_ROOT/install.sh" --codex-home "$CODEX_HOME" --yes "$@"
}

run_uninstaller() {
  "$TEST_ROOT/uninstall.sh" --codex-home "$CODEX_HOME" --yes "$@"
}

