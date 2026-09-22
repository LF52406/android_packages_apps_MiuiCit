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
