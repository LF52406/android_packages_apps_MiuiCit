# Settings integration — five taps on Kernel version

This integration reproduces the Xiaomi-style entry path without tying MiuiCit to a specific ROM.

User flow:

```text
Settings
  → About phone
  → Android version / firmware details
  → Kernel version
  → tap 5 times
  → com.miui.cit/.home.HomeActivity
```

The original secret code `*#*#6484#*#*` remains a second entry path.

## Why a Settings source hook is required

A resource overlay cannot reliably implement "five taps on an existing Preference" across AOSP-derived ROMs. The click counter therefore lives in a tiny Settings helper and the existing kernel-version controller/binding delegates to it.

There is deliberately **no compile-time dependency** from Settings to MiuiCit. The launcher uses the explicit component name as strings. This keeps Settings buildable on ROM variants where the app is temporarily omitted.

## Apply

From the ROM root, with this repository checked out at `packages/apps/MiuiCit`:

```bash
packages/apps/MiuiCit/tools/apply-settings-integration.sh
```

The patcher is idempotent.

It supports:

1. Current AOSP/Lineage-style `deviceinfo/firmwareversion/KernelVersionPreferenceController.java`.
2. Current Catalyst `KernelVersionPreference.kt` when present.
3. The older `deviceinfo/KernelVersionPreferenceController.java` layout as a fallback.

If a ROM has replaced the AOSP kernel-version screen with a completely different implementation, the script **fails instead of guessing**. A small adapter for that Settings fork can then be added without touching MiuiCit itself.

## Behavior

- five consecutive taps are required;
- a gap longer than 3 seconds resets the sequence;
- no toast or visible intermediate UI is shown;
- the fifth tap launches the exported MiuiCit home activity explicitly;
- if MiuiCit is missing, Settings does not crash; the failed launch is only logged.

## One-command ROM setup

```bash
packages/apps/MiuiCit/tools/setup-rom.sh device/xiaomi/mondrian/device.mk
```

This validates the MiuiCit tree, adds the product include if missing, and applies/verifies the Settings hook. It is safe to run again.
