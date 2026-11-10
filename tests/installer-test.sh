#!/usr/bin/env bash

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/test-lib.sh"

new_fixture

cat > "$CODEX_HOME/AGENTS.md" <<'EOF'
# Existing user rule
KEEP-AGENTS-SENTINEL
EOF

cat > "$CODEX_HOME/config.toml" <<'EOF'
model = "existing-model"
# KEEP-CONFIG-SENTINEL
EOF

before_dry_run="$(tree_digest "$CODEX_HOME")"
dry_run_output="$FIXTURE_ROOT/dry-run.txt"
run_installer --dry-run > "$dry_run_output"
after_dry_run="$(tree_digest "$CODEX_HOME")"

[[ "$before_dry_run" == "$after_dry_run" ]] || fail "dry run modified the target Codex home"
assert_contains "$dry_run_output" "DRY RUN"

run_installer

assert_contains "$CODEX_HOME/AGENTS.md" "KEEP-AGENTS-SENTINEL"
assert_count 1 "<!-- codex-sdlc:start -->" "$CODEX_HOME/AGENTS.md"
assert_count 1 "<!-- codex-sdlc:end -->" "$CODEX_HOME/AGENTS.md"
assert_contains "$CODEX_HOME/config.toml" "# KEEP-CONFIG-SENTINEL"
assert_count 1 "# codex-sdlc:start" "$CODEX_HOME/config.toml"
assert_count 1 "# codex-sdlc:end" "$CODEX_HOME/config.toml"

for agent in pm architect ui developer qa ui-qa security devops; do
  assert_file "$CODEX_HOME/agents/sdlc-$agent.toml"
done

assert_file "$CODEX_HOME/skills/sdlc/SKILL.md"
assert_file "$CODEX_HOME/codex-sdlc-install-manifest.tsv"

python3 - "$CODEX_HOME/config.toml" <<'PY'
import pathlib
import sys
import tomllib

with pathlib.Path(sys.argv[1]).open("rb") as handle:
    data = tomllib.load(handle)

agents = data.get("agents", {})
expected = {
    "sdlc-pm", "sdlc-architect", "sdlc-ui", "sdlc-developer",
    "sdlc-qa", "sdlc-ui-qa", "sdlc-security", "sdlc-devops",
}
missing = expected.difference(agents)
if missing:
    raise SystemExit(f"missing registered agents: {sorted(missing)}")
PY

echo "PASS: installer integration"

