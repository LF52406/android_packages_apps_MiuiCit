#!/usr/bin/env bash
set -Eeuo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"

trap 'rc=$?; echo "Repository audit: FAILED at line $LINENO (exit $rc)" >&2; exit $rc' ERR

echo "== MiuiCit repository audit =="

echo "[1/5] Shell syntax"
bash -n "$REPO"/tools/*.sh

echo "[2/5] Python syntax"
python3 -m py_compile \
    "$REPO/tools/check-apk-manifest.py" \
    "$REPO/settings/apply-settings-integration.py" \
    "$REPO/settings/check-settings-integration.py" \
    "$REPO/settings/tests/test_settings_integration.py" \
    "$REPO/compat/android17/apply-framework-compat.py" \
    "$REPO/compat/android17/tests/test_framework_compat.py"

echo "[3/5] APK/config/base integration"
"$REPO/tools/verify-tree.sh"

echo "[4/5] Settings integration regression tests"
python3 "$REPO/settings/tests/test_settings_integration.py"

echo "[5/5] Android framework compatibility regression tests"
python3 "$REPO/compat/android17/tests/test_framework_compat.py"

trap - ERR
echo "Repository audit: VERIFIED"
