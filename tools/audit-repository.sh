#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"

bash -n "$REPO"/tools/*.sh
python3 -m py_compile     "$REPO"/tools/check-apk-manifest.py     "$REPO"/settings/apply-settings-integration.py     "$REPO"/settings/check-settings-integration.py     "$REPO"/settings/tests/test_settings_integration.py

"$REPO/tools/verify-tree.sh"
python3 "$REPO/settings/tests/test_settings_integration.py"

echo "Repository audit: VERIFIED"
