#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$PWD}"
ROOT="$(cd "$ROOT" && pwd)"
BP_REL="packages/apps/MiuiCit/Android.bp"
LIST="$ROOT/out/.module_paths/Android.bp.list"
DB="$ROOT/out/.module_paths/files.db"

[[ -f "$ROOT/$BP_REL" ]] || {
    echo "MiuiCit Android.bp not found at: $ROOT/$BP_REL" >&2
    exit 1
}

if [[ ! -d "$ROOT/out" ]]; then
    echo "Soong discovery cache: not present yet; nothing to refresh."
    exit 0
fi

if [[ -f "$LIST" ]] && grep -Fxq "$BP_REL" "$LIST"; then
    echo "Soong discovery: MiuiCit Android.bp is already listed."
    exit 0
fi

echo "Soong discovery cache does not contain $BP_REL."
echo "Removing only the module-finder cache/list so the next build rescans Android.bp files."

rm -f "$LIST" "$DB"
rm -f "$ROOT/out/.module_paths/Android.mk.list"
rm -f "$ROOT/out/.module_paths/configuration.list"

echo "Soong discovery cache refreshed."
