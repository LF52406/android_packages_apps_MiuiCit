#!/usr/bin/env bash
set -euo pipefail

LINE='$(call inherit-product, packages/apps/MiuiCit/miuicit.mk)'

if [[ $# -ne 1 ]]; then
    echo "usage: $0 path/to/device.mk" >&2
    exit 2
fi

TARGET="$1"
[[ -f "$TARGET" ]] || { echo "not found: $TARGET" >&2; exit 1; }

if grep -Fqx "$LINE" "$TARGET"; then
    echo "MiuiCit integration already present: $TARGET"
    exit 0
fi

printf '\n# Xiaomi CIT\n%s\n' "$LINE" >> "$TARGET"
echo "Added MiuiCit integration to $TARGET"
echo "This changes only the local ROM checkout; commit it only if you want permanent integration."
