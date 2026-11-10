#!/usr/bin/env bash

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash -n "$root"/tests/*.sh

for test_file in \
  "$root/tests/installer-test.sh" \
  "$root/tests/idempotency-test.sh" \
  "$root/tests/uninstall-test.sh" \
  "$root/tests/package-contract-test.sh" \
  "$root/tests/security-test.sh"; do
  bash "$test_file"
done

echo "PASS: all tests"
