#!/usr/bin/env bash

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/test-lib.sh"

new_fixture
run_installer

first_agents_digest="$(tree_digest "$CODEX_HOME/agents")"
first_skills_digest="$(tree_digest "$CODEX_HOME/skills")"

run_installer

[[ "$first_agents_digest" == "$(tree_digest "$CODEX_HOME/agents")" ]] || fail "second install changed agent files"
[[ "$first_skills_digest" == "$(tree_digest "$CODEX_HOME/skills")" ]] || fail "second install changed skill files"
assert_count 1 "<!-- codex-sdlc:start -->" "$CODEX_HOME/AGENTS.md"
assert_count 1 "# codex-sdlc:start" "$CODEX_HOME/config.toml"

echo "PASS: installer idempotency"

