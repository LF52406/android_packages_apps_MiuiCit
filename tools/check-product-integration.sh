#!/usr/bin/env bash
set -euo pipefail

LINE='$(call inherit-product, packages/apps/MiuiCit/miuicit.mk)'

if [[ $# -ne 1 ]]; then
    echo "usage: $0 path/to/device.mk" >&2
    exit 2
fi

TARGET="$1"
[[ -f "$TARGET" ]] || { echo "not found: $TARGET" >&2; exit 1; }

grep -Fqx "$LINE" "$TARGET" && { echo "MiuiCit product integration: PRESENT"; exit 0; }
echo "MiuiCit product integration: MISSING"
exit 1
