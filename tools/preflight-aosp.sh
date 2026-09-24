#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$PWD}"
ROOT="$(cd "$ROOT" && pwd)"
BP="$ROOT/packages/apps/MiuiCit/Android.bp"

[[ -f "$BP" ]] || {
    echo "ERROR: missing $BP" >&2
    exit 1
}

echo "== MiuiCit AOSP preflight =="

if grep -q '^soong_namespace' "$BP"; then
    echo "ERROR: MiuiCit must remain in the global Soong namespace" >&2
    exit 1
fi

for mod in MiuiCit miuicit_mondrian_config miuicit_hardware_init; do
    grep -q "name: \"$mod\"" "$BP" || {
        echo "ERROR: module missing from Android.bp: $mod" >&2
        exit 1
    }
done

LIST="$ROOT/out/.module_paths/Android.bp.list"
if [[ -f "$LIST" ]]; then
    if grep -Fxq "packages/apps/MiuiCit/Android.bp" "$LIST"; then
        echo "Soong module discovery: VERIFIED"
    else
        echo "Soong module discovery: STALE"
        echo "Run: packages/apps/MiuiCit/tools/refresh-soong-discovery.sh"
        exit 2
    fi
else
    echo "Soong module discovery: no cache yet (normal before first build)"
fi

echo "MiuiCit AOSP preflight: VERIFIED"
