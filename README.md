# Xiaomi MiuiCit — AOSP integration for mondrian

Standalone, ROM-agnostic integration tree for Xiaomi HyperOS `com.miui.cit` on POCO F5 Pro (`mondrian`).

The project preserves Xiaomi's original CIT APK/UI/test logic. Device-specific data remains outside the APK, matching stock behavior.

## Checkout path

```text
packages/apps/MiuiCit
```

## Base integration

- installs `MiuiCit.apk` to `/product/app/MiuiCit/MiuiCit.apk`
- installs the stock mondrian config to `/odm/etc/cit_param_config.json`
- installs a small init fragment containing only stock-verified CIT torch/speaker-calibration setup
- re-signs the APK with the target ROM platform certificate because the manifest uses `android:sharedUserId="android.uid.system"`

## Prepare the APK

```bash
packages/apps/MiuiCit/tools/import-apk.sh /path/to/MiuiCit.apk
```

Analyzed stock APK SHA-256:

```text
145e4d8d8193c0ef7171ca83df1a2d901d413c11a6366a6affa1a8dde8340390
```

## Product integration

```make
$(call inherit-product, packages/apps/MiuiCit/miuicit.mk)
```

Then run:

```bash
packages/apps/MiuiCit/tools/verify-tree.sh
```

The current mondrian/sm8450-common vendor setup already supplies `qcrilhook` and `qcrilmsgtunnel`; they are not duplicated here.

## Launch

Secret code: `*#*#6484#*#*`

Direct validation launch:

```bash
adb shell am start -a com.miui.cit.MAGIC_NUMBER -n com.miui.cit/.home.HomeActivity
```

## Factory runtime

Auxiliary factory/calibration pages depend on Xiaomi CIT Wi-Fi/Bluetooth, CIT sensor services, sensor communicate, MiSys, MTD and `spkcal`. Stock declarations are preserved under `runtime/reference/`. Main tests are brought up first; optional factory runtime is enabled only after the required blobs are imported and validated.

## SELinux

No permissive policy and no broad generic `system_app` rules. Collect real AVCs first with `tools/collect-device-validation.sh`, then add only the rules actually required by mondrian.

See `analysis/PORTING_REPORT.md` and `analysis/test_matrix.csv`.

## Baseline status

The original `MiuiCit.apk` is now present and byte-verified. The repository is ready for the first base AOSP build. Optional Xiaomi factory HAL/runtime remains intentionally disabled until device validation.


## Settings five-tap integration

The repository also contains a ROM-agnostic AOSP Settings hook. After integration, five consecutive taps on **Kernel version** launch MiuiCit, while `*#*#6484#*#*` remains supported.

Apply it from the ROM root:

```bash
packages/apps/MiuiCit/tools/apply-settings-integration.sh
```

Or prepare both product and Settings integration in one step:

```bash
packages/apps/MiuiCit/tools/setup-rom.sh device/xiaomi/mondrian/device.mk
```

See `settings/README.md`.


## Validation

Run the complete static repository audit before building:

```bash
packages/apps/MiuiCit/tools/audit-repository.sh
```

For full Xiaomi factory-runtime bring-up, collect the missing stock runtime and SELinux context files from the unpacked HyperOS image:

```sh
packages/apps/MiuiCit/tools/collect-stock-runtime.sh
```

This repository intentionally keeps optional factory HALs disabled until their ELF dependencies and enforcing-SELinux domains are verified.


## Soong discovery cache

When MiuiCit is cloned into an AOSP tree **after that tree has already been built**, an existing
`out/.module_paths` finder cache can cause Kati to report all three MiuiCit PRODUCT_PACKAGES
entries as non-existent even though `Android.bp` is correct.

`tools/setup-rom.sh` now detects this condition and refreshes only the source-module finder cache.
It does not remove compiled objects or images.

Manual check:

```bash
packages/apps/MiuiCit/tools/preflight-aosp.sh
```
