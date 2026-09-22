# Xiaomi MiuiCit — AOSP integration

Standalone integration tree for the original HyperOS `com.miui.cit` application used on Xiaomi POCO F5 Pro (`mondrian`).

This repository is intentionally ROM-agnostic. Expected checkout path: `packages/apps/MiuiCit`.

The integration preserves the original Xiaomi CIT UI/test logic and keeps the device configuration outside the APK at `/odm/etc/cit_param_config.json`. The APK must be re-signed with the target ROM platform certificate because its manifest uses `android:sharedUserId="android.uid.system"`.
