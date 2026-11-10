#!/usr/bin/env bash

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/test-lib.sh"

forbidden_names='\.credentials\.json|/sessions/|/file-history/|/cache/|/logs?/|security_warnings_state'
if grep -RIE --exclude='security-test.sh' --exclude='TEST-PLAN-*' "$forbidden_names" \
  "$TEST_ROOT/agents" "$TEST_ROOT/skills" "$TEST_ROOT/scripts" "$TEST_ROOT/config" 2>/dev/null; then
  fail "runtime or credential path found in distributable content"
fi

if grep -RIE --exclude='security-test.sh' -- '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----' "$TEST_ROOT"; then
  fail "private key material found"
fi

if grep -RIF --exclude='security-test.sh' --exclude='validate-package.sh' -- '/home/roybarak' \
  "$TEST_ROOT/agents" "$TEST_ROOT/skills" "$TEST_ROOT/scripts" "$TEST_ROOT/config" 2>/dev/null; then
  fail "source-machine absolute path found in runtime package"
fi

echo "PASS: package security scan"

