#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SETTINGS_DIR="${1:-packages/apps/Settings}"

python3 "$REPO/settings/apply-settings-integration.py" "$SETTINGS_DIR"
python3 "$REPO/settings/check-settings-integration.py" "$SETTINGS_DIR"
