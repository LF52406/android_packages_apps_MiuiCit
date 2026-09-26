# Android 17 framework compatibility

The stock HyperOS MiuiCit APK is kept byte-for-byte unchanged in this repository. Android 17
exposes two framework incompatibilities that were confirmed by real device crash logs:

1. `CitKeyBoardCheckActivity` registers a legacy dynamic receiver without
   `RECEIVER_EXPORTED` / `RECEIVER_NOT_EXPORTED`. Android's broadcast controller rejects the
   call when `DYNAMIC_RECEIVER_EXPLICIT_EXPORT_REQUIRED` is active.
2. Xiaomi's CIT microphone code calls the OEM API
   `AudioRecord.setParameters(String): int`. AOSP Android 17 does not expose that Java method,
   although the native `AudioRecord` implementation still has per-record `setParameters()`.

`apply-framework-compat.py` applies narrow compatibility changes to `frameworks/base`:

- disables explicit dynamic-receiver flag enforcement only when the caller is both
  `com.miui.cit` and `SYSTEM_UID`; all other applications keep normal Android enforcement;
- restores the hidden `AudioRecord.setParameters(String)` bridge and routes it to the native
  AudioRecord input handle. It deliberately does not redirect CIT to global
  `AudioSystem.setParameters()`, because that would change the OEM semantics.

The patcher is idempotent and fail-closed. If the ROM's framework layout no longer matches the
supported Android implementation, it exits with an error instead of making a guessed edit.

From the ROM root:

```bash
packages/apps/MiuiCit/tools/apply-framework-compat.sh
```

Verification only:

```bash
packages/apps/MiuiCit/tools/apply-framework-compat.sh frameworks/base --check
```

`tools/setup-rom.sh` runs this automatically for a normal `frameworks/base` checkout.
