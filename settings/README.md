# Settings integration — MiuiCit via kernel details (MistOS)

On MistOS Android 17, the first tap on Kernel version opens a dialog showing the full
kernel version. Five additional taps on the information inside the open dialog
launch MiuiCit (six total taps). Closing the dialog resets the count; pauses over
three seconds between dialog taps also reset it. MistOS's existing short/full kernel
version toggle in the About screen is preserved.

Other ROMs with the standard kernel-version preference retain six direct taps
on that preference. The secret code `*#*#6484#*#*` is unchanged.

## Why a Settings source hook is required

A resource overlay cannot reliably implement "five taps inside the kernel-details dialog" across AOSP-derived ROMs. The click counter therefore lives in a tiny Settings helper and the existing kernel-version controller/binding delegates to it.

There is deliberately **no compile-time dependency** from Settings to MiuiCit. The launcher uses the explicit component name as strings. This keeps Settings buildable on ROM variants where the app is temporarily omitted.

## Apply

From the ROM root, with this repository checked out at `packages/apps/MiuiCit`:

```bash
packages/apps/MiuiCit/tools/apply-settings-integration.sh
```

The patcher is idempotent; it also upgrades the previously inserted MistOS inline counter.

It supports:

1. MistOS Android 17 `com.mist.utils.HyperPreference`.
2. Current AOSP/Lineage-style `deviceinfo/firmwareversion/KernelVersionPreferenceController.java`.
2. Current Catalyst `KernelVersionPreference.kt` when present.
3. The older `deviceinfo/KernelVersionPreferenceController.java` layout as a fallback.

If a ROM has replaced the AOSP kernel-version screen with a completely different implementation, the script **fails instead of guessing**. A small adapter for that Settings fork can then be added without touching MiuiCit itself.

## Behavior

- MistOS: first tap opens the full kernel information dialog; five more taps within it launch MiuiCit.
- Other ROMs: six consecutive kernel preference taps launch MiuiCit.
- A gap over 3 seconds resets the active tap sequence.
- Closing the MistOS dialog cancels its count.
- Missing MiuiCit is logged without crashing Settings.

## One-command ROM setup

```bash
packages/apps/MiuiCit/tools/setup-rom.sh device/xiaomi/mondrian/device.mk
```

This validates the MiuiCit tree, adds the product include if missing, and applies/verifies the Settings hook. It is safe to run again.
