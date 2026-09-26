#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 2 ]]; then
    echo "usage: $0 [path/to/device.mk] [path/to/packages/apps/Settings]" >&2
    exit 2
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEVICE_MK="${1:-device/xiaomi/mondrian/device.mk}"
SETTINGS_DIR="${2:-packages/apps/Settings}"

[[ -f "$DEVICE_MK" ]] || {
    echo "device makefile not found: $DEVICE_MK" >&2
    exit 1
}

[[ -d "$SETTINGS_DIR" ]] || {
    echo "Settings tree not found: $SETTINGS_DIR" >&2
    exit 1
}

"$REPO/tools/verify-tree.sh"
"$REPO/tools/apply-product-integration.sh" "$DEVICE_MK"
"$REPO/tools/apply-settings-integration.sh" "$SETTINGS_DIR"

# The base modules are defined in Android.mk so Kati sees the same modules that
# PRODUCT_PACKAGES validates. If this repo replaced an earlier Android.bp-based
# checkout, refresh only the source finder lists/cache.
"$REPO/tools/refresh-soong-discovery.sh" "$(pwd)"

echo
echo "MiuiCit ROM integration is ready."
echo "Device makefile: $DEVICE_MK"
echo "Settings tree:   $SETTINGS_DIR"
echo
echo "Review:"
echo "  git diff -- $DEVICE_MK"
echo "  git -C $SETTINGS_DIR diff"
