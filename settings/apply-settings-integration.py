#!/usr/bin/env python3
"""Apply MiuiCit five-tap integration to AOSP-derived Settings trees.

MistOS is handled first because its About-phone UI uses com.mist.utils.HyperPreference
and does not dispatch the visible kernel-version click through the standard controller.
Other ROMs fall back to the standard modern/Catalyst or legacy Settings paths.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

MARKER = "MiuiCit kernel tap integration"
MIST_MARKER = "MiuiCit Mist kernel tap integration"

MODERN_CONTROLLER = Path(
    "src/com/android/settings/deviceinfo/firmwareversion/"
    "KernelVersionPreferenceController.java"
)
CATALYST_BINDING = Path(
    "src/com/android/settings/deviceinfo/firmwareversion/KernelVersionPreference.kt"
)
LEGACY_CONTROLLER = Path(
    "src/com/android/settings/deviceinfo/KernelVersionPreferenceController.java"
)
HELPER_DEST = Path("src/com/android/settings/deviceinfo/CitKernelTapLauncher.java")
MIST_HYPER_PREFERENCE = Path("src/com/mist/utils/HyperPreference.java")


def die(message: str) -> None:
    raise SystemExit(f"error: {message}")


def add_java_import(text: str, line: str) -> str:
    if line in text:
        return text
    imports = [item for item in text.splitlines() if item.startswith("import ")]
    if not imports:
        die(f"cannot insert Java import: {line}")
    anchor = imports[-1]
    return text.replace(anchor + "\n", anchor + "\n" + line + "\n", 1)


def insert_before_class_end(text: str, block: str) -> str:
    lint_suffix = "\n}\n// LINT.ThenChange"
    if lint_suffix in text:
        return text.replace(
            lint_suffix,
            "\n" + block.rstrip() + "\n}\n// LINT.ThenChange",
            1,
        )
    pos = text.rfind("\n}")
    if pos < 0:
        die("cannot locate Java class closing brace")
    return text[:pos] + "\n" + block.rstrip() + text[pos:]


def patch_mist_hyper_preference(path: Path) -> bool:
    text = path.read_text()
    if MIST_MARKER in text:
        return False

    text = add_java_import(
        text,
        "import com.android.settings.deviceinfo.CitKernelTapLauncher;",
    )

    anchor = """        kernel.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
"""
    if anchor not in text:
        die(f"cannot locate MistOS kernel click listener: {path}")

    replacement = (
        anchor
        + f"                // {MIST_MARKER}\n"
        + "                CitKernelTapLauncher.onKernelVersionTap(context);\n"
    )
    path.write_text(text.replace(anchor, replacement, 1))
    return True


def patch_modern_controller(path: Path) -> bool:
    text = path.read_text()
    if MARKER in text:
        return False

    text = add_java_import(text, "import androidx.preference.Preference;")
    text = add_java_import(
        text,
        "import com.android.settings.deviceinfo.CitKernelTapLauncher;",
    )

    signature = "    public boolean handlePreferenceTreeClick(Preference preference) {\n"
    if signature in text:
        hook = f"""        // {MARKER}
        if (getPreferenceKey().equals(preference.getKey())) {{
            CitKernelTapLauncher.onKernelVersionTap(mContext);
        }}
"""
        path.write_text(text.replace(signature, signature + hook, 1))
        return True

    text = add_java_import(text, "import androidx.preference.PreferenceScreen;")
    block = f"""
    // {MARKER}
    @Override
    public void displayPreference(PreferenceScreen screen) {{
        super.displayPreference(screen);
        final Preference preference = screen.findPreference(getPreferenceKey());
        if (preference != null) {{
            preference.setSelectable(true);
        }}
    }}

    @Override
    public boolean handlePreferenceTreeClick(Preference preference) {{
        if (!getPreferenceKey().equals(preference.getKey())) {{
            return false;
        }}
        return CitKernelTapLauncher.onKernelVersionTap(mContext);
    }}
"""
    path.write_text(insert_before_class_end(text, block))
    return True


def patch_catalyst_binding(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text()
    if MARKER in text:
        return False

    import_line = "import com.android.settings.deviceinfo.CitKernelTapLauncher"
    if import_line not in text:
        anchor = "import com.android.settings.R\n"
        if anchor not in text:
            die(f"unexpected Catalyst import layout: {path}")
        text = text.replace(anchor, anchor + import_line + "\n", 1)

    if "preference.isSelectable = false" in text:
        text = text.replace(
            "preference.isSelectable = false",
            "preference.isSelectable = true",
            1,
        )
    elif "preference.isSelectable = true" not in text:
        die(f"cannot locate Catalyst selectability assignment: {path}")

    copy_line = "        preference.isCopyingEnabled = true\n"
    if copy_line not in text:
        die(f"cannot locate Catalyst bind body: {path}")

    listener = (
        f"        // {MARKER}\n"
        "        preference.setOnPreferenceClickListener {\n"
        "            CitKernelTapLauncher.onKernelVersionTap(preference.context)\n"
        "        }\n"
    )
    path.write_text(text.replace(copy_line, copy_line + listener, 1))
    return True


def patch_legacy_controller(path: Path) -> bool:
    text = path.read_text()
    if MARKER in text:
        return False

    summary_line = (
        "        preference.setSummary("
        "DeviceInfoUtils.getFormattedKernelVersion(mContext));\n"
    )
    if summary_line not in text:
        die(f"unexpected legacy controller layout: {path}")

    text = text.replace(
        summary_line,
        summary_line
        + f"        // {MARKER}\n"
        + "        preference.setSelectable(true);\n",
        1,
    )

    block = f"""
    // {MARKER}
    @Override
    public boolean handlePreferenceTreeClick(Preference preference) {{
        if (!KEY_KERNEL_VERSION.equals(preference.getKey())) {{
            return false;
        }}
        return CitKernelTapLauncher.onKernelVersionTap(mContext);
    }}
"""
    path.write_text(insert_before_class_end(text, block))
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "settings_dir",
        nargs="?",
        default="packages/apps/Settings",
        help="path to the Settings source tree",
    )
    args = parser.parse_args()

    settings = Path(args.settings_dir).resolve()
    if not settings.is_dir():
        die(f"Settings tree not found: {settings}")

    repo = Path(__file__).resolve().parents[1]
    helper_src = repo / "settings" / "CitKernelTapLauncher.java"
    if not helper_src.is_file():
        die(f"helper source missing: {helper_src}")

    helper_dst = settings / HELPER_DEST
    helper_dst.parent.mkdir(parents=True, exist_ok=True)
    helper_changed = not (
        helper_dst.exists() and helper_dst.read_bytes() == helper_src.read_bytes()
    )
    if helper_changed:
        shutil.copyfile(helper_src, helper_dst)

    changed: list[str] = []
    mist_hyper = settings / MIST_HYPER_PREFERENCE

    # MistOS has a custom About-phone layout. Its visible kernel TextView is wired
    # directly in HyperPreference, so standard controller/Catalyst hooks are not
    # the runtime click path. Patch only the real MistOS handler and stop here.
    if mist_hyper.is_file():
        if patch_mist_hyper_preference(mist_hyper):
            changed.append(str(MIST_HYPER_PREFERENCE))
        integration = "MistOS HyperPreference"
    else:
        modern = settings / MODERN_CONTROLLER
        legacy = settings / LEGACY_CONTROLLER
        if modern.is_file():
            if patch_modern_controller(modern):
                changed.append(str(MODERN_CONTROLLER))
            catalyst = settings / CATALYST_BINDING
            if patch_catalyst_binding(catalyst):
                changed.append(str(CATALYST_BINDING))
            integration = "modern AOSP/Lineage Settings"
        elif legacy.is_file():
            if patch_legacy_controller(legacy):
                changed.append(str(LEGACY_CONTROLLER))
            integration = "legacy AOSP Settings"
        else:
            die(
                "no supported MistOS, modern, or legacy kernel click handler found; "
                "refusing to patch an unknown Settings layout"
            )

    if helper_changed:
        changed.append(str(HELPER_DEST))

    print("MiuiCit Settings integration: OK")
    print(f"Settings tree: {settings}")
    print(f"Integration path: {integration}")
    if changed:
        for item in changed:
            print(f"patched: {item}")
    else:
        print("already applied; no changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
