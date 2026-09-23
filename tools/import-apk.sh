#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 /path/to/MiuiCit.apk" >&2
    exit 2
fi

SRC="$1"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DST="$REPO/prebuilt/MiuiCit.apk"
EXPECTED="145e4d8d8193c0ef7171ca83df1a2d901d413c11a6366a6affa1a8dde8340390"

[[ -f "$SRC" ]] || {
    echo "missing APK: $SRC" >&2
    exit 1
}

unzip -tq "$SRC" >/dev/null || {
    echo "APK ZIP integrity check failed: $SRC" >&2
    exit 1
}

python3 - "$SRC" <<'PY'
import sys
import zipfile

apk = sys.argv[1]
with zipfile.ZipFile(apk) as zf:
    names = set(zf.namelist())

missing = [name for name in ("classes.dex", "AndroidManifest.xml") if name not in names]
if missing:
    raise SystemExit("APK is missing " + ", ".join(missing))
PY

ACTUAL="$(sha256sum "$SRC" | cut -d" " -f1)"
if [[ "$ACTUAL" != "$EXPECTED" ]]; then
    echo "warning: APK differs from analyzed stock baseline" >&2
    echo "expected: $EXPECTED" >&2
    echo "actual:   $ACTUAL" >&2
fi

mkdir -p "$(dirname "$DST")"
cp -f "$SRC" "$DST"
printf "%s  prebuilt/MiuiCit.apk\n" "$ACTUAL" > "$REPO/analysis/APK_SHA256"
echo "MiuiCit.apk imported."
