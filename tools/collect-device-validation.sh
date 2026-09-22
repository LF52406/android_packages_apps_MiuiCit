#!/system/bin/sh
OUT="/sdcard/Download/miuicit-validation-$(date +%Y%m%d-%H%M%S).txt"
exec >"$OUT" 2>&1

echo '===== BUILD ====='
getprop ro.product.device
getprop ro.build.version.release
getprop ro.build.version.sdk
getprop ro.build.fingerprint

echo '===== PACKAGE ====='
dumpsys package com.miui.cit | grep -E 'userId=|sharedUserId|versionName=|versionCode=|codePath=|signatures|grantedPermissions' -A40

echo '===== CONFIG ====='
ls -lZ /odm/etc/cit_param_config.json
head -12 /odm/etc/cit_param_config.json

echo '===== FACTORY HIDL ====='
command -v lshal >/dev/null && lshal | grep -Ei 'vendor.xiaomi.(cit|sensor|hardware.misys|hardware.mtdservice)' || true

echo '===== NODES ====='
for f in \
 /sys/class/mi_display/disp-DSI-0/disp_param \
 /sys/class/mi_display/disp-DSI-0/brightness_clone \
 /sys/class/mi_display/disp-DSI-0/panel_info \
 /sys/class/qcom-battery/chip_ok \
 /sys/class/qcom-battery/authentic \
 /sys/class/qcom-battery/battcont_online \
 /sys/class/qcom-battery/cc_orientation \
 /sys/class/power_supply/usb/type \
 /sys/class/leds/led:torch_0/brightness \
 /sys/class/leds/led:torch_1/brightness \
 /sys/class/leds/led:switch_0/brightness \
 /sys/class/leds/led:switch_1/brightness; do
    ls -lZ "$f" 2>/dev/null || echo "MISSING $f"
done

echo '===== PROPERTIES ====='
getprop | grep -Ei 'persist.vendor.sys.fp|vendor.panel.color|vendor.camera.sensor|camera.sensor|vendor.audio.cit|ro.miui|ro.vendor.miui' || true

echo '===== SELINUX / LOGS ====='
getenforce
logcat -d -b all | grep -Ei 'avc: denied|MiuiCit|com.miui.cit|citsensor|vendor.xiaomi.cit|misys|mtdservice|spkcal' | tail -1600

echo "saved: $OUT"
