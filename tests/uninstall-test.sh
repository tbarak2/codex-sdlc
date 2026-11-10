#!/usr/bin/env bash

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/test-lib.sh"

new_fixture

cat > "$CODEX_HOME/AGENTS.md" <<'EOF'
KEEP-AGENTS-SENTINEL
EOF
cat > "$CODEX_HOME/config.toml" <<'EOF'
model = "existing-model"
# KEEP-CONFIG-SENTINEL
EOF

run_installer
modified="$CODEX_HOME/skills/sdlc/SKILL.md"
printf '\nlocal modification\n' >> "$modified"

output="$FIXTURE_ROOT/uninstall.txt"
run_uninstaller > "$output"

assert_file "$modified"
assert_contains "$output" "retained modified file"
assert_contains "$CODEX_HOME/AGENTS.md" "KEEP-AGENTS-SENTINEL"
assert_contains "$CODEX_HOME/config.toml" "# KEEP-CONFIG-SENTINEL"
assert_count 0 "<!-- codex-sdlc:start -->" "$CODEX_HOME/AGENTS.md"
assert_count 0 "# codex-sdlc:start" "$CODEX_HOME/config.toml"
[[ ! -f "$CODEX_HOME/agents/sdlc-pm.toml" ]] || fail "unchanged agent file was not removed"
[[ ! -f "$CODEX_HOME/codex-sdlc-install-manifest.tsv" ]] || fail "install manifest was not removed"

echo "PASS: safe uninstall"
