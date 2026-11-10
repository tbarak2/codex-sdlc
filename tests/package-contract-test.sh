#!/usr/bin/env bash

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/test-lib.sh"

skill="$TEST_ROOT/skills/sdlc/SKILL.md"
matrix="$TEST_ROOT/docs/migration-matrix.md"

assert_file "$skill"
assert_file "$matrix"

for token in Go Approved Proceed; do
  assert_contains "$skill" "$token"
done

for phase in pm architecture ui qa development ui-qa code-review security devops ship; do
  assert_contains "$skill" "$phase"
done

for agent in pm architect ui developer qa ui-qa security devops; do
  file="$TEST_ROOT/agents/sdlc-$agent.toml"
  assert_file "$file"
  assert_contains "$file" "Inputs"
  assert_contains "$file" "Outputs"
  assert_contains "$file" "Completion"
  assert_contains "$file" "Handoff"
done

assert_contains "$TEST_ROOT/agents/sdlc-security.toml" 'sandbox_mode = "read-only"'

echo "PASS: package contracts"

