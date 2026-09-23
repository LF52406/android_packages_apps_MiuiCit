#!/usr/bin/env bash
set -Eeuo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"

trap 'rc=$?; echo "Repository audit: FAILED at line $LINENO (exit $rc)" >&2; exit $rc' ERR

echo "== MiuiCit repository audit =="

echo "[1/4] Shell syntax"
bash -n "$REPO"/tools/*.sh

echo "[2/4] Python syntax"
python3 -m py_compile \
    "$REPO/tools/check-apk-manifest.py" \
    "$REPO/settings/apply-settings-integration.py" \
    "$REPO/settings/check-settings-integration.py" \
    "$REPO/settings/tests/test_settings_integration.py"

echo "[3/4] APK/config/base integration"
"$REPO/tools/verify-tree.sh"

echo "[4/4] Settings integration regression tests"
python3 "$REPO/settings/tests/test_settings_integration.py"

trap - ERR
echo "Repository audit: VERIFIED"
