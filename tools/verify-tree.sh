#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
EXPECTED_APK_SHA256="145e4d8d8193c0ef7171ca83df1a2d901d413c11a6366a6affa1a8dde8340390"
EXPECTED_APK_GIT_BLOB="fae160bb25c17a520c841864e3e127f00f94dbc4"
EXPECTED_CONFIG_SHA256="45a349999612b6e7e6cdf16c69921d9e02f0d3846dc6712d08d9e0dd549c187f"

for f in \
    Android.bp \
    miuicit.mk \
    prebuilt/MiuiCit.apk \
    config/mondrian/cit_param_config.json \
    init/init.miuicit.rc \
    tools/check-apk-manifest.py; do
    [[ -f "$REPO/$f" ]] || {
        echo "missing: $f" >&2
        exit 1
    }
done

grep -q '^soong_namespace' "$REPO/Android.bp" || {
    echo "Android.bp: soong_namespace is missing" >&2
    exit 1
}
grep -q 'certificate: "platform"' "$REPO/Android.bp" || {
    echo "Android.bp: platform certificate is missing" >&2
    exit 1
}
grep -q 'product_specific: true' "$REPO/Android.bp" || {
    echo "Android.bp: MiuiCit is not product_specific" >&2
    exit 1
}
grep -q 'device_specific: true' "$REPO/Android.bp" || {
    echo "Android.bp: mondrian config is not device_specific" >&2
    exit 1
}
grep -q '"product"[[:space:]]*:[[:space:]]*"mondrian"' \
    "$REPO/config/mondrian/cit_param_config.json" || {
    echo "cit_param_config.json: product is not mondrian" >&2
    exit 1
}

unzip -tq "$REPO/prebuilt/MiuiCit.apk" >/dev/null || {
    echo "MiuiCit.apk: ZIP integrity check failed" >&2
    exit 1
}

python3 - "$REPO/prebuilt/MiuiCit.apk" <<'PY'
import sys
import zipfile

apk = sys.argv[1]
with zipfile.ZipFile(apk) as zf:
    names = set(zf.namelist())

missing = [name for name in ("classes.dex", "AndroidManifest.xml") if name not in names]
if missing:
    raise SystemExit("MiuiCit.apk: missing " + ", ".join(missing))
PY

APK_SHA256="$(sha256sum "$REPO/prebuilt/MiuiCit.apk" | cut -d" " -f1)"
CONFIG_SHA256="$(sha256sum "$REPO/config/mondrian/cit_param_config.json" | cut -d" " -f1)"

[[ "$APK_SHA256" == "$EXPECTED_APK_SHA256" ]] || {
    echo "MiuiCit.apk SHA-256 mismatch" >&2
    echo "expected: $EXPECTED_APK_SHA256" >&2
    echo "actual:   $APK_SHA256" >&2
    exit 1
}

[[ "$CONFIG_SHA256" == "$EXPECTED_CONFIG_SHA256" ]] || {
    echo "cit_param_config.json SHA-256 mismatch" >&2
    echo "expected: $EXPECTED_CONFIG_SHA256" >&2
    echo "actual:   $CONFIG_SHA256" >&2
    exit 1
}

if command -v git >/dev/null 2>&1; then
    APK_GIT_BLOB="$(git -C "$REPO" hash-object prebuilt/MiuiCit.apk)"
    [[ "$APK_GIT_BLOB" == "$EXPECTED_APK_GIT_BLOB" ]] || {
        echo "MiuiCit.apk Git blob mismatch" >&2
        echo "expected: $EXPECTED_APK_GIT_BLOB" >&2
        echo "actual:   $APK_GIT_BLOB" >&2
        exit 1
    }
fi

python3 "$REPO/tools/check-apk-manifest.py" "$REPO/prebuilt/MiuiCit.apk"

echo "MiuiCit base tree: VERIFIED"
echo "APK:    $APK_SHA256"
echo "config: $CONFIG_SHA256"

if [[ -d "$REPO/runtime/generated/proprietary" ]]; then
    echo "factory runtime: imported for analysis (not auto-enabled)"
else
    echo "factory runtime: not imported (base/main-test mode)"
fi
