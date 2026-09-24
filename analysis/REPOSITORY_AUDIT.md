# Repository audit — mondrian / AOSP

Audit baseline: stock HyperOS MiuiCit `0.4.9-SNAPSHOT` (`versionCode 47`) and the supplied stock `mondrian` CIT configuration.

## Verified and fixed

- The committed APK is byte-identical to the supplied stock APK:
  - SHA-256: `145e4d8d8193c0ef7171ca83df1a2d901d413c11a6366a6affa1a8dde8340390`
  - Git blob: `fae160bb25c17a520c841864e3e127f00f94dbc4`
- Binary manifest is verified without relying on aapt:
  - package `com.miui.cit`
  - `android.uid.system`
  - HomeActivity exported with `com.miui.cit.MAGIC_NUMBER`
  - secret-code receiver exported for `6484`
  - no manifest `uses-library` declarations
- The AOSP build re-signs the imported APK with the target ROM platform key.
- APK is installed in `/product/app/MiuiCit/`, matching stock partition placement.
- The stock mondrian config is byte-preserved and installed to `/odm/etc/cit_param_config.json`.
- The init fragment contains only mondrian-relevant stock CIT/MMI behavior for flash channels 0/1 and speaker-calibration file lifecycle.
- The repository is now an explicit Soong namespace; the existing `PRODUCT_SOONG_NAMESPACES` export is therefore valid and isolated.
- The Settings five-tap hook is covered by regression tests for:
  - current AOSP/Lineage firmware-version controller
  - Catalyst Kotlin preference binding
  - legacy AOSP controller fallback
  - idempotent re-application
  - unknown Settings layout fail-closed behavior
- Current sm8450-common already provides qcrilhook/qcrilmsgtunnel, so this repository does not duplicate them.
- Partial factory-runtime imports are now deleted on failure instead of leaving misleading generated output.
- GitHub CI runs the same repository audit on every push/PR.

## What can be considered ready before device testing

The base integration is structurally ready for a real AOSP build:

```text
/product/app/MiuiCit/MiuiCit.apk
/odm/etc/cit_param_config.json
/vendor/etc/init/init.miuicit.rc
```

and the Settings source hook can expose the Xiaomi-style five-tap entry path.

## What cannot be honestly marked complete without a device run

MiuiCit is a factory/diagnostic client, not a self-contained APK. The following remain runtime validation items:

1. Android 17 behavior of Xiaomi calls into hidden/system APIs.
2. Direct sysfs access under enforcing SELinux, especially:
   - `disp_param`
   - `brightness_clone`
   - torch/switch channels
   - qcom-battery nodes
   - touch/fingerprint factory nodes
3. Optional Xiaomi factory HALs:
   - CIT Wi-Fi
   - CIT Bluetooth
   - CIT sensor service
   - sensor communicate
   - MiSys
   - MTD service
4. `spkcal` and its transitive ELF dependencies.
5. External factory applications invoked by auxiliary pages:
   - Xiaomi CameraTools calibration
   - Goodix/fingerprint factory/calibration tools where selected by the active sensor vendor.

These are deliberately not emulated and are not solved with permissive SELinux.

## Next production gate

Build the base modules first. If the app starts, collect one validation bundle with
`tools/collect-device-validation.sh` after exercising the main tests.

For full factory/calibration bring-up, collect the actual stock binaries and stock SELinux contexts with
`tools/collect-stock-runtime.sh`. The resulting archive is sufficient for ELF dependency analysis and exact service-domain policy work.


## Audit correction: display DAC permissions

A second comparison against stock `vendor/etc/init/hw/init.target.rc` found that the base fragment originally carried the CIT/MMI torch permissions but omitted the two display nodes used directly by the mondrian config. This is now corrected:

- `/sys/class/mi_display/disp-DSI-0/disp_param` → `system:system 0664`
- `/sys/class/mi_display/disp-DSI-0/brightness_clone` → `system:system 0664`

The trigger remains `post-fs-data`, matching stock. This fixes the DAC side of FOD-HBM and brightness-clone access. Enforcing SELinux access is still validated separately from real AVCs.


## DEX compatibility check against Android 17

The actual `classes.dex` was inspected at method/type-reference level.

- `CitApplication` startup code does not directly link Xiaomi/MIUI framework classes.
- `HomeActivity` startup code does not directly link Xiaomi/MIUI framework classes.
- There are no DEX type IDs under `Lmiui/` or `Lvendor/xiaomi/`; Xiaomi framework/HAL selection is performed through strings/reflection/HIDL lookup instead of verifier-time class linkage.
- Android 17 still contains the checked hidden APIs used by the relevant code paths: `SystemProperties`, `ServiceManager`, `HwBinder`, `AudioSystem.setParameters`, `AudioSystem.setForceUse`, and the checked FingerprintManager methods.
- `com.android.internal.telephony.Phone.invokeOemRilRequestStrings` is no longer present in the current Lineage 24 telephony source. The APK's direct reference to it is confined to `CitSarMtkAuthenticaTestActivity.invokeOemRilRequestStringsEmPhone`, an MTK-oriented auxiliary SAR-auth path, not the Qualcomm mondrian main startup path. The mondrian Qualcomm path must still be validated through qcril during device testing.

This substantially reduces the risk of an immediate AOSP startup `NoClassDefFoundError`; it does not replace runtime validation of individual factory activities.


## Build-system correction: global Soong namespace

The first full-ROM integration exposed a Make/Soong visibility failure: all three MiuiCit modules were reported as non-existent in PRODUCT_PACKAGES. The standalone repository had an unnecessary `soong_namespace {}` while its export depended on product-make namespace plumbing.

For maximum AOSP ROM portability the repository now stays in the **global Soong namespace**. The explicit namespace block and `PRODUCT_SOONG_NAMESPACES` addition were removed. The module names are unique and can now be resolved directly by PRODUCT_PACKAGES on standard AOSP/Lineage-derived builds.


## Module-discovery failure mode

The exact Kati error

```text
includes non-existent modules in PRODUCT_PACKAGES
MiuiCit
miuicit_hardware_init
miuicit_mondrian_config
```

means Make never received those Soong modules in `ALL_MODULES`. When all three disappear together
while `Android.bp` is valid, the relevant failure mode is whole-file discovery/export rather than
an individual module definition.

For ROM trees where MiuiCit is cloned after an earlier build, refresh
`out/.module_paths/Android.bp.list` / `files.db` so the next Soong invocation rescans the new
`packages/apps/MiuiCit/Android.bp`. The repository now automates this without deleting normal
compiled outputs.
