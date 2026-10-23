# Settings integration — inline kernel version / MiuiCit (MistOS)

On MistOS Android 17, the **first tap** on Kernel version expands the full
kernel information directly in the existing card of the Android version page.
No dialog is shown. **Five additional taps on that expanded information** open
MiuiCit (six taps total). The full details stay visible during this sequence.
Pauses over three seconds restart the five-tap count without hiding the text.

The listener is stored per TextView binding: leaving and reopening the page
recreates the listener. The shorter kernel summary is the initial view.

Other ROMs using the standard kernel-version preference retain six direct taps.
The secret code \`*#*#6484#*#*\` is unchanged.

## Why a Settings hook is required

MistOS uses \`com.mist.utils.HyperPreference\` for its visible kernel version,
rather than the standard AOSP kernel preference controller.

The patcher replaces the **entire** MistOS kernel click listener with
\`CitKernelTapLauncher.installMistKernelTapListener(kernel, SystemInfoUtils.getFullKernelVersion())\`.
Replacing the old listener, not appending to it, avoids an extra dialog
and prevents the stock short/full toggle from collapsing the text on later taps.

There is no compile-time dependency on MiuiCit: Settings launches the explicit
MiuiCit component by name.

## Apply only the Settings integration

From the ROM root with this repository at \`packages/apps/MiuiCit\`:

\`\`\`bash
packages/apps/MiuiCit/tools/apply-settings-integration.sh packages/apps/Settings
\`\`\`

This is idempotent and migrates the old dialog-based integration in-place.

Other supported Settings paths remain unchanged:

1. Modern AOSP/Lineage \`KernelVersionPreferenceController.java\`.
2. Catalyst \`KernelVersionPreference.kt\`, when present.
3. Legacy AOSP \`KernelVersionPreferenceController.java\`.

Unrecognized layouts fail rather than changing unrelated code.

## Complete ROM setup

\`\`\`bash
packages/apps/MiuiCit/tools/setup-rom.sh device/xiaomi/mondrian/device.mk
\`\`\`

Run full setup only when product/framework integration is also required.
