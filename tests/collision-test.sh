#!/usr/bin/env bash

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/test-lib.sh"

new_fixture

cat > "$CODEX_HOME/config.toml" <<'EOF'
[agents.sdlc-pm]
description = "user-owned agent"
config_file = "/example/user-agent.toml"
EOF

before="$(tree_digest "$CODEX_HOME")"
output="$FIXTURE_ROOT/collision.txt"
if run_installer > "$output" 2>&1; then
  fail "installer accepted an unmanaged agent-name collision"
fi
after="$(tree_digest "$CODEX_HOME")"

[[ "$before" == "$after" ]] || fail "collision preflight modified the target Codex home"
assert_contains "$output" "unmanaged Codex agent name collision"

echo "PASS: collision preflight"
