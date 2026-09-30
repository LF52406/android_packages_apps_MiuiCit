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
    void bind(android.widget.TextView kernel) {
        kernel.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                kernel.setText("full");
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
            self.assertIn("CitKernelTapLauncher.onKernelVersionTap(context);", hyper)
            self.assertIn('kernel.setText("full");', hyper)
            self.assertEqual(modern_before, (root / MODERN).read_bytes())
            self.assertEqual(catalyst_before, (root / CATALYST).read_bytes())

            second = run(APPLY, root)
            self.assertIn("already applied; no changes", second.stdout)

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
