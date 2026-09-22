# Current mondrian tree integration gaps

Checked against the current `lineage-24.0` branches of the user's mondrian and sm8450-common trees.

## Already present in sm8450-common

- `system_ext/framework/qcrilhook.jar`
- `system_ext/etc/permissions/qcrilhook.xml`
- `system_ext/priv-app/qcrilmsgtunnel/qcrilmsgtunnel.apk`
- `vendor/lib64/vendor.qti.hardware.radio.qcrilhook@1.0.so`

These are already packaged by `sm8450-common-vendor.mk`, so MiuiCit must not duplicate them.

## Not present in the current proprietary file lists

- `MiuiCit.apk`
- `/odm/etc/cit_param_config.json`
- Xiaomi CIT Wi-Fi service
- Xiaomi CIT Bluetooth service
- Xiaomi CIT sensor service
- Xiaomi sensor communicate service
- MiSys factory services/libraries
- Xiaomi MTD service
- `spkcal` factory binary

The standalone MiuiCit repository therefore owns the app/config integration, while optional factory runtime remains gated until the exact stock blobs and their transitive ELF dependencies are imported and validated.

## First bring-up target

Build only the base APK + mondrian ODM config + stock-verified init fragment. Do not enable the optional factory services in the first build. This isolates framework/signing/UID compatibility from factory HAL and SELinux issues.
