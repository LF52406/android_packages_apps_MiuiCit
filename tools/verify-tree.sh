#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"

for f in Android.bp miuicit.mk prebuilt/MiuiCit.apk config/mondrian/cit_param_config.json init/init.miuicit.rc; do
    [[ -f "$REPO/$f" ]] || { echo "missing: $f" >&2; exit 1; }
done

grep -q '"product"[[:space:]]*:[[:space:]]*"mondrian"' "$REPO/config/mondrian/cit_param_config.json"
unzip -tq "$REPO/prebuilt/MiuiCit.apk" >/dev/null
unzip -l "$REPO/prebuilt/MiuiCit.apk" | grep -q "classes.dex"

echo "base tree: OK"
sha256sum "$REPO/prebuilt/MiuiCit.apk"
sha256sum "$REPO/config/mondrian/cit_param_config.json"

if [[ -d "$REPO/runtime/generated/proprietary" ]]; then
    echo "factory runtime: imported for analysis (not auto-enabled)"
else
    echo "factory runtime: not imported (base/main-test mode)"
fi
