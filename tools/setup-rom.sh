#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "usage: $0 path/to/device.mk [path/to/packages/apps/Settings]" >&2
    exit 2
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEVICE_MK="$1"
SETTINGS_DIR="${2:-packages/apps/Settings}"

"$REPO/tools/verify-tree.sh"
"$REPO/tools/apply-product-integration.sh" "$DEVICE_MK"
"$REPO/tools/apply-settings-integration.sh" "$SETTINGS_DIR"

# The base modules are defined in Android.mk so Kati sees the same modules that
# PRODUCT_PACKAGES validates. If this repo replaced an earlier Android.bp-based
# checkout, refresh only the source finder lists/cache.
"$REPO/tools/refresh-soong-discovery.sh" "$(pwd)"

echo
echo "MiuiCit ROM integration is ready."
echo "Review:"
echo "  git diff -- $DEVICE_MK"
echo "  git -C $SETTINGS_DIR diff"
