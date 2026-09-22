#!/system/bin/sh
# Collect the stock Xiaomi factory runtime needed to finish MiuiCit bring-up.
# Run as root. No "su" is embedded intentionally.

ROOT="${1:-/data/local/UnpackerSystem/erofs}"
OUT="${2:-/sdcard/Download/miuicit-stock-runtime.tar.gz}"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd)"
REPO="$(CDPATH= cd -- "$SCRIPT_DIR/.." 2>/dev/null && pwd)"
WORK="/data/local/tmp/miuicit-stock-runtime.$$"
FILES="$WORK/files"
MISSING="$WORK/MISSING_REQUIRED.txt"

if [ ! -d "$ROOT" ]; then
    echo "missing unpack root: $ROOT" >&2
    exit 1
fi

rm -rf "$WORK"
mkdir -p "$FILES"
: > "$MISSING"

copy_rel() {
    rel="$1"
    src="$ROOT/$rel"
    if [ -f "$src" ]; then
        mkdir -p "$FILES/$(dirname "$rel")"
        cp -p "$src" "$FILES/$rel"
        echo "COPIED: $rel"
        return 0
    fi
    return 1
}

if [ -f "$REPO/runtime/REQUIRED_STOCK_FILES.txt" ]; then
    while IFS= read -r rel; do
        case "$rel" in
            ""|\#*) continue ;;
        esac
        if ! copy_rel "$rel"; then
            echo "$rel" >> "$MISSING"
            echo "MISSING: $rel" >&2
        fi
    done < "$REPO/runtime/REQUIRED_STOCK_FILES.txt"
fi

# Configuration and the stock init behavior used by CIT/MMI.
for rel in     odm_a/etc/cit_param_config.json     vendor_a/etc/init/hw/init.target.rc     vendor_a/etc/init/vendor.xiaomi.cit.wifi@1.0-service.rc     vendor_a/etc/init/vendor.xiaomi.cit.bluetooth@1.0-service.rc     vendor_a/etc/init/vendor.xiaomi.sensor.citsensorservice@2.0-service.rc     vendor_a/etc/init/vendor.xiaomi.sensor.communicate@1.0-service.rc     vendor_a/etc/init/vendor.xiaomi.hardware.misys@1.0-service.rc     vendor_a/etc/init/vendor.xiaomi.hardware.misys@2.0-service.rc     vendor_a/etc/init/vendor.xiaomi.hardware.misys@3.0-service.rc     vendor_a/etc/init/vendor.xiaomi.hardware.misys@4.0-service.rc     vendor_a/etc/init/vendor.xiaomi.hardware.mtdservice@1.3-service.rc
do
    copy_rel "$rel" >/dev/null 2>&1 || true
done

# Java/interface pieces used by Xiaomi's fallback/reflection paths.
for rel in     system_a/system/framework/vendor.xiaomi.hardware.misys-V1.0-java.jar     system_a/system/framework/vendor.xiaomi.hardware.misys-V2.0-java.jar     system_a/system/framework/vendor.xiaomi.hardware.misys.V3_0.jar     system_a/system/framework/vendor.xiaomi.hardware.misys-V4.0-java.jar     system_ext_a/framework/vendor.xiaomi.hardware.misys.common-V1-java.jar     system_ext_a/framework/qcrilhook.jar     system_ext_a/priv-app/qcrilmsgtunnel/qcrilmsgtunnel.apk
do
    copy_rel "$rel" >/dev/null 2>&1 || true
done

# Additional MiSys generations are useful for dependency analysis even though
# the base CIT port does not enable them by default.
for rel in     vendor_a/bin/hw/vendor.xiaomi.hardware.misys@3.0-service     vendor_a/bin/hw/vendor.xiaomi.hardware.misys@4.0-service     vendor_a/lib64/vendor.xiaomi.hardware.misys@3.0.so     vendor_a/lib64/vendor.xiaomi.hardware.misys@4.0.so     vendor_a/lib64/hw/vendor.xiaomi.hardware.misys@3.0-impl.so     vendor_a/lib64/hw/vendor.xiaomi.hardware.misys@4.0-impl.so
do
    copy_rel "$rel" >/dev/null 2>&1 || true
done

# Stock SELinux labels are essential for reproducing factory HAL behavior
# without permissive policy.
for rel in     vendor_a/etc/selinux/vendor_file_contexts     vendor_a/etc/selinux/vendor_hwservice_contexts     vendor_a/etc/selinux/vendor_service_contexts     vendor_a/etc/selinux/vndservice_contexts     vendor_a/etc/selinux/vendor_property_contexts     vendor_a/etc/selinux/vendor_seapp_contexts     vendor_a/etc/selinux/vendor_mac_permissions.xml     odm_a/etc/selinux/odm_file_contexts     odm_a/etc/selinux/odm_hwservice_contexts     odm_a/etc/selinux/odm_service_contexts     odm_a/etc/selinux/odm_property_contexts     odm_a/etc/selinux/odm_seapp_contexts     odm_a/etc/selinux/odm_mac_permissions.xml
do
    copy_rel "$rel" >/dev/null 2>&1 || true
done

# Preserve all matching VINTF declarations.
if [ -d "$ROOT/vendor_a/etc/vintf/manifest" ]; then
    find "$ROOT/vendor_a/etc/vintf/manifest" -type f 2>/dev/null         | grep -E 'vendor\.xiaomi\.(cit|sensor|hardware\.misys|hardware\.mtdservice)'         | while IFS= read -r src; do
            rel="${src#$ROOT/}"
            copy_rel "$rel" >/dev/null 2>&1 || true
        done
fi

# External factory APKs invoked by auxiliary CIT pages, if present.
find "$ROOT" -type f \(     -iname '*cameratools*.apk' -o     -iname '*gftest*.apk' -o     -iname '*fingerprint*setting*.apk' -o     -iname '*factory*test*.apk' \) 2>/dev/null | while IFS= read -r src; do
    rel="${src#$ROOT/}"
    copy_rel "$rel" >/dev/null 2>&1 || true
done

(
    cd "$FILES" || exit 1
    find . -type f | sort > "$WORK/CONTENTS.txt"
)

if command -v sha256sum >/dev/null 2>&1; then
    (
        cd "$FILES" || exit 1
        find . -type f -print0 2>/dev/null             | sort -z             | xargs -0 sha256sum
    ) > "$WORK/SHA256SUMS.txt" 2>/dev/null || true
fi

rm -f "$OUT"
(
    cd "$WORK" || exit 1
    tar -czf "$OUT" files CONTENTS.txt SHA256SUMS.txt MISSING_REQUIRED.txt
)

chmod 0644 "$OUT" 2>/dev/null || true
echo
echo "DONE: $OUT"
ls -lh "$OUT" 2>/dev/null || true
if [ -s "$MISSING" ]; then
    echo "Some required files were missing; see MISSING_REQUIRED.txt in the archive."
fi

rm -rf "$WORK"
