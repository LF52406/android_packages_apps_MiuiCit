#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$PWD}"
ROOT="$(cd "$ROOT" && pwd)"
MK="$ROOT/packages/apps/MiuiCit/Android.mk"

[[ -f "$MK" ]] || {
    echo "ERROR: missing $MK" >&2
    exit 1
}

if [[ -f "$ROOT/packages/apps/MiuiCit/Android.bp" ]]; then
    echo "ERROR: stale Android.bp exists next to Android.mk" >&2
    exit 1
fi

echo "== MiuiCit AOSP preflight =="

for mod in MiuiCit miuicit_mondrian_config miuicit_hardware_init; do
    grep -q "LOCAL_MODULE := $mod" "$MK" || {
        echo "ERROR: module missing from Android.mk: $mod" >&2
        exit 1
    }
done

LIST="$ROOT/out/.module_paths/Android.mk.list"
if [[ -f "$LIST" ]]; then
    if grep -Fxq "packages/apps/MiuiCit/Android.mk" "$LIST"; then
        echo "Kati module discovery: VERIFIED"
    else
        echo "Kati module discovery: STALE"
        echo "Run: packages/apps/MiuiCit/tools/refresh-soong-discovery.sh"
        exit 2
    fi
else
    echo "Kati module discovery: no cache yet (normal before first build)"
fi

BP_LIST="$ROOT/out/.module_paths/Android.bp.list"
if [[ -f "$BP_LIST" ]] && grep -Fxq "packages/apps/MiuiCit/Android.bp" "$BP_LIST"; then
    echo "ERROR: stale MiuiCit Android.bp remains in Android.bp.list" >&2
    echo "Run: packages/apps/MiuiCit/tools/refresh-soong-discovery.sh" >&2
    exit 2
fi

echo "MiuiCit AOSP preflight: VERIFIED"
