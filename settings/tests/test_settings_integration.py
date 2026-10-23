#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
APPLY = REPO / "settings" / "apply-settings-integration.py"
CHECK = REPO / "settings" / "check-settings-integration.py"

MODERN = Path(
    "src/com/android/settings/deviceinfo/firmwareversion/"
    "KernelVersionPreferenceController.java"
)
CATALYST = Path(
    "src/com/android/settings/deviceinfo/firmwareversion/KernelVersionPreference.kt"
)
LEGACY = Path("src/com/android/settings/deviceinfo/KernelVersionPreferenceController.java")
MIST_HYPER = Path("src/com/mist/utils/HyperPreference.java")


def write(root: Path, path: Path, data: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data)


def run(script: Path, root: Path, check: bool = True):
    return subprocess.run(
        [sys.executable, str(script), str(root)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def modern_fixture(existing_handler: bool = False) -> str:
    handler = """
    @Override
    public boolean handlePreferenceTreeClick(Preference preference) {
        preference.setSummary("full kernel");
        return false;
    }
""" if existing_handler else ""
    pref_import = "import androidx.preference.Preference;\n" if existing_handler else ""
    return f"""package com.android.settings.deviceinfo.firmwareversion;
import android.content.Context;
{pref_import}import com.android.settings.core.BasePreferenceController;
import com.android.settingslib.DeviceInfoUtils;
public class KernelVersionPreferenceController extends BasePreferenceController {{
    public KernelVersionPreferenceController(Context context, String preferenceKey) {{
        super(context, preferenceKey);
    }}
    @Override
    public CharSequence getSummary() {{
        return DeviceInfoUtils.getFormattedKernelVersion(mContext);
    }}
{handler}}}
"""


def catalyst_fixture() -> str:
    return """package com.android.settings.deviceinfo.firmwareversion
import android.content.Context
import androidx.preference.Preference
import com.android.settings.R
import com.android.settingslib.metadata.PreferenceMetadata
import com.android.settingslib.preference.PreferenceBinding
class KernelVersionPreference : PreferenceMetadata, PreferenceBinding {
    override val key: String get() = "kernel_version"
    override fun bind(preference: Preference, metadata: PreferenceMetadata) {
        super.bind(preference, metadata)
        preference.isSelectable = false
        preference.isCopyingEnabled = true
    }
}
"""


def mist_fixture() -> str:
    return """package com.mist.utils;
import android.content.Context;
import android.view.View;
import com.android.settings.R;
public class HyperPreference {
    private Context context;
    private boolean fullKernelVersion = false;
    void bind(android.widget.TextView kernel) {
        kernel.setText("short");
        kernel.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (fullKernelVersion) {
                    kernel.setText("short");
                    fullKernelVersion = false;
                } else {
                    kernel.setText("full");
                    fullKernelVersion = true;
                }
            }
        });
    }
}
"""


class SettingsIntegrationTest(unittest.TestCase):
    def test_modern_and_catalyst_are_patched_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, MODERN, modern_fixture())
            write(root, CATALYST, catalyst_fixture())
            first = run(APPLY, root)
            self.assertIn("modern AOSP/Lineage Settings", first.stdout)
            run(CHECK, root)
            modern = (root / MODERN).read_text()
            catalyst = (root / CATALYST).read_text()
            self.assertIn("CitKernelTapLauncher.onKernelVersionTap", modern)
            self.assertIn("preference.setSelectable(true)", modern)
            self.assertIn("preference.isSelectable = true", catalyst)
            self.assertIn("setOnPreferenceClickListener", catalyst)
            before = ((root / MODERN).read_bytes(), (root / CATALYST).read_bytes())
            second = run(APPLY, root)
            self.assertIn("already applied; no changes", second.stdout)
            self.assertEqual(before[0], (root / MODERN).read_bytes())
            self.assertEqual(before[1], (root / CATALYST).read_bytes())

    def test_existing_handler_is_extended_not_duplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, MODERN, modern_fixture(existing_handler=True))
            run(APPLY, root)
            run(CHECK, root)
            text = (root / MODERN).read_text()
            self.assertEqual(
                text.count("public boolean handlePreferenceTreeClick(Preference preference)"),
                1,
            )
            self.assertIn("CitKernelTapLauncher.onKernelVersionTap(mContext);", text)
            self.assertIn('preference.setSummary("full kernel");', text)

    def test_mistos_patches_only_real_hyperpreference_click_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, MIST_HYPER, mist_fixture())
            write(root, MODERN, modern_fixture(existing_handler=True))
            write(root, CATALYST, catalyst_fixture())
            modern_before = (root / MODERN).read_bytes()
            catalyst_before = (root / CATALYST).read_bytes()

            first = run(APPLY, root)
            self.assertIn("MistOS HyperPreference", first.stdout)
            run(CHECK, root)

            hyper = (root / MIST_HYPER).read_text()
            self.assertIn("MiuiCit Mist kernel tap integration", hyper)
            self.assertIn("CitKernelTapLauncher.installMistKernelTapListener(kernel, SystemInfoUtils.getFullKernelVersion());", hyper)
            self.assertNotIn("CitKernelTapLauncher.showKernelDetails(", hyper)
            self.assertNotIn("kernel.setOnClickListener(new View.OnClickListener()", hyper)
            self.assertIn('kernel.setText("short");', hyper)
            self.assertNotIn("private boolean fullKernelVersion = false;", hyper)
            self.assertEqual(modern_before, (root / MODERN).read_bytes())
            self.assertEqual(catalyst_before, (root / CATALYST).read_bytes())

            second = run(APPLY, root)
            self.assertIn("already applied; no changes", second.stdout)

    def test_mistos_mixed_indentation_preserves_kernel_details(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = mist_fixture().replace(
                "        kernel.setOnClickListener",
                "    \tkernel.setOnClickListener",
            )
            write(root, MIST_HYPER, fixture)
            run(APPLY, root)
            run(CHECK, root)
            text = (root / MIST_HYPER).read_text()
            self.assertEqual(text.count("CitKernelTapLauncher.installMistKernelTapListener(kernel, SystemInfoUtils.getFullKernelVersion());"), 1)
            self.assertNotIn("kernel.setOnClickListener(new View.OnClickListener()", text)
            helper = (root / "src/com/android/settings/deviceinfo/CitKernelTapLauncher.java").read_text()
            self.assertIn("REQUIRED_INLINE_TAPS = REQUIRED_TAPS - 1", helper)
            self.assertIn("kernel.setText(fullKernelVersion);", helper)
            self.assertNotIn("AlertDialog", helper)
            self.assertFalse(
                any(
                    " \t" in line[:len(line) - len(line.lstrip(" \t"))]
                    for line in text.splitlines()
                    if "MiuiCit Mist kernel tap integration" in line
                    or "installMistKernelTapListener(" in line
                ),
                "Generated Java lines contain space-before-tab indentation",
            )
            before = (root / MIST_HYPER).read_bytes()
            run(APPLY, root)
            self.assertEqual(before, (root / MIST_HYPER).read_bytes())


    def test_mistos_reapply_repairs_previously_generated_mixed_indent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, MIST_HYPER, mist_fixture())
            run(APPLY, root)
            destination = root / MIST_HYPER
            clean = destination.read_text()
            old = clean.replace(
                "        // MiuiCit Mist kernel tap integration",
                "    \t// MiuiCit Mist kernel tap integration",
                1,
            ).replace(
                "        CitKernelTapLauncher.installMistKernelTapListener(",
                "    \tCitKernelTapLauncher.installMistKernelTapListener(",
                1,
            )
            self.assertNotEqual(clean, old)
            destination.write_text(old)
            repaired = run(APPLY, root)
            self.assertIn("patched:", repaired.stdout)
            run(CHECK, root)
            self.assertEqual(destination.read_text(), clean)
            again = run(APPLY, root)
            self.assertIn("already applied; no changes", again.stdout)

    def test_mistos_upgrades_existing_dialog_listener_without_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, MIST_HYPER, mist_fixture())
            # Simulate the previously installed helper call + original toggle.
            old = (root / MIST_HYPER).read_text().replace(
                "                if (fullKernelVersion) {",
                "                // MiuiCit Mist kernel tap integration\n"
                "                CitKernelTapLauncher.showKernelDetails(context, SystemInfoUtils.getFullKernelVersion());\n"
                "                if (fullKernelVersion) {",
                1,
            )
            write(root, MIST_HYPER, old)
            run(APPLY, root)
            run(CHECK, root)
            new = (root / MIST_HYPER).read_text()
            self.assertEqual(new.count("MiuiCit Mist kernel tap integration"), 1)
            self.assertEqual(new.count("installMistKernelTapListener("), 1)
            self.assertNotIn("showKernelDetails(", new)
            self.assertNotIn("kernel.setOnClickListener(new View.OnClickListener()", new)
            self.assertNotIn("private boolean fullKernelVersion = false;", new)
            again = run(APPLY, root)
            self.assertIn("already applied; no changes", again.stdout)

    def test_mistos_inline_listener_replaces_old_short_full_toggle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, MIST_HYPER, mist_fixture())
            run(APPLY, root)
            run(CHECK, root)
            code = (root / MIST_HYPER).read_text()
            self.assertIn('kernel.setText("short");', code)
            self.assertNotIn('kernel.setText("full");', code)
            self.assertNotIn("fullKernelVersion = false", code)
            self.assertEqual(code.count("installMistKernelTapListener("), 1)
            helper = (root / "src/com/android/settings/deviceinfo/CitKernelTapLauncher.java").read_text()
            self.assertNotIn("AlertDialog", helper)
            self.assertIn("++additionalTaps == REQUIRED_INLINE_TAPS", helper)

    def test_legacy_controller_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root,
                LEGACY,
                """package com.android.settings.deviceinfo;
import android.content.Context;
import androidx.preference.Preference;
import com.android.settings.core.PreferenceControllerMixin;
import com.android.settingslib.DeviceInfoUtils;
import com.android.settingslib.core.AbstractPreferenceController;
public class KernelVersionPreferenceController
        extends AbstractPreferenceController implements PreferenceControllerMixin {
    private static final String KEY_KERNEL_VERSION = "kernel_version";
    public KernelVersionPreferenceController(Context context) { super(context); }
    @Override
    public void updateState(Preference preference) {
        super.updateState(preference);
        preference.setSummary(DeviceInfoUtils.getFormattedKernelVersion(mContext));
    }
    @Override
    public String getPreferenceKey() { return KEY_KERNEL_VERSION; }
}
""",
            )
            run(APPLY, root)
            run(CHECK, root)
            text = (root / LEGACY).read_text()
            self.assertIn("preference.setSelectable(true)", text)
            self.assertIn("CitKernelTapLauncher.onKernelVersionTap", text)

    def test_unknown_settings_layout_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run(APPLY, Path(tmp), check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no supported MistOS, modern, or legacy", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
