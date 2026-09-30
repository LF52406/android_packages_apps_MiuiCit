#!/usr/bin/env python3
from pathlib import Path
import argparse
import sys

MARKER = "MiuiCit kernel tap integration"

parser = argparse.ArgumentParser()
parser.add_argument("settings_dir", nargs="?", default="packages/apps/Settings")
args = parser.parse_args()

root = Path(args.settings_dir).resolve()
helper = root / "src/com/android/settings/deviceinfo/CitKernelTapLauncher.java"
modern = root / (
    "src/com/android/settings/deviceinfo/firmwareversion/"
    "KernelVersionPreferenceController.java"
)
catalyst = root / (
    "src/com/android/settings/deviceinfo/firmwareversion/KernelVersionPreference.kt"
)
legacy = root / "src/com/android/settings/deviceinfo/KernelVersionPreferenceController.java"
mist_hyper = root / "src/com/mist/utils/HyperPreference.java"

errors = []

if not helper.is_file():
    errors.append("CitKernelTapLauncher.java is missing")
else:
    text = helper.read_text()
    for needle in (
        'REQUIRED_TAPS = 5',
        'CIT_PACKAGE = "com.miui.cit"',
        'CIT_HOME_ACTIVITY = "com.miui.cit.home.HomeActivity"',
    ):
        if needle not in text:
            errors.append(f"helper missing: {needle}")

if mist_hyper.is_file():
    htext = mist_hyper.read_text()
    if "MiuiCit Mist kernel tap integration" not in htext:
        errors.append("MistOS HyperPreference kernel tap is not patched")
    if "CitKernelTapLauncher.onKernelVersionTap(context);" not in htext:
        errors.append("MistOS HyperPreference CIT launcher call is missing")

if modern.is_file():
    text = modern.read_text()
    if MARKER not in text:
        errors.append("modern kernel controller is not patched")
    if catalyst.is_file():
        ktext = catalyst.read_text()
        if MARKER not in ktext:
            errors.append("Catalyst kernel binding is not patched")
        if "preference.isSelectable = true" not in ktext:
            errors.append("Catalyst kernel preference is not selectable")
elif legacy.is_file():
    text = legacy.read_text()
    if MARKER not in text:
        errors.append("legacy kernel controller is not patched")
else:
    errors.append("no supported kernel controller exists")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    sys.exit(1)

print("MiuiCit Settings five-tap integration: VERIFIED")
