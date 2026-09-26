#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$PWD}"
ROOT="$(cd "$ROOT" && pwd)"
MK_REL="packages/apps/MiuiCit/Android.mk"
MK_LIST="$ROOT/out/.module_paths/Android.mk.list"
BP_LIST="$ROOT/out/.module_paths/Android.bp.list"
DB="$ROOT/out/.module_paths/files.db"

[[ -f "$ROOT/$MK_REL" ]] || {
    echo "MiuiCit Android.mk not found at: $ROOT/$MK_REL" >&2
    exit 1
}

if [[ ! -d "$ROOT/out/.module_paths" ]]; then
    echo "Build discovery cache: not present yet; nothing to refresh."
    exit 0
fi

mk_ok=false
if [[ -f "$MK_LIST" ]] && grep -Fxq "$MK_REL" "$MK_LIST"; then
    mk_ok=true
fi

bp_stale=false
if [[ -f "$BP_LIST" ]] && grep -Fxq "packages/apps/MiuiCit/Android.bp" "$BP_LIST"; then
    bp_stale=true
fi

if [[ "$mk_ok" == true && "$bp_stale" == false ]]; then
    echo "Build discovery: MiuiCit Android.mk is already listed."
    exit 0
fi

echo "Refreshing only Android build module-finder cache."
echo "Compiled objects, target files and images are left untouched."

rm -f "$DB"
rm -f "$MK_LIST"
rm -f "$BP_LIST"
rm -f "$ROOT/out/.module_paths/configuration.list"

echo "Build discovery cache refreshed."
