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
    "src/com/android/settings/deviceinfo/firmwareversion/"
    "KernelVersionPreference.kt"
)
LEGACY = Path(
    "src/com/android/settings/deviceinfo/KernelVersionPreferenceController.java"
)
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


class SettingsIntegrationTest(unittest.TestCase):
    def test_modern_and_catalyst_are_patched_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root,
                MODERN,
                """package com.android.settings.deviceinfo.firmwareversion;

import android.content.Context;

import com.android.settings.core.BasePreferenceController;
import com.android.settingslib.DeviceInfoUtils;

// LINT.IfChange
public class KernelVersionPreferenceController extends BasePreferenceController {
    public KernelVersionPreferenceController(Context context, String preferenceKey) {
        super(context, preferenceKey);
    }

    @Override
    public int getAvailabilityStatus() {
        return AVAILABLE;
    }

    @Override
    public CharSequence getSummary() {
        return DeviceInfoUtils.getFormattedKernelVersion(mContext);
    }
}
// LINT.ThenChange(KernelVersionPreference.kt)
""",
            )
            write(
                root,
                CATALYST,
                """package com.android.settings.deviceinfo.firmwareversion

import android.content.Context
import androidx.preference.Preference
import com.android.settings.R
import com.android.settingslib.metadata.PreferenceMetadata
import com.android.settingslib.preference.PreferenceBinding

class KernelVersionPreference : PreferenceMetadata, PreferenceBinding {
    override val key: String
        get() = "kernel_version"

    override fun bind(preference: Preference, metadata: PreferenceMetadata) {
        super.bind(preference, metadata)
        preference.isSelectable = false
        preference.isCopyingEnabled = true
    }
}
""",
            )

            first = run(APPLY, root)
            self.assertIn("MiuiCit Settings integration: OK", first.stdout)
            run(CHECK, root)

            modern = (root / MODERN).read_text()
            catalyst = (root / CATALYST).read_text()

            self.assertIn("CitKernelTapLauncher.onKernelVersionTap", modern)
            self.assertIn("preference.setSelectable(true)", modern)
            self.assertIn("preference.isSelectable = true", catalyst)
            self.assertIn("setOnPreferenceClickListener", catalyst)

            before = {
                MODERN: (root / MODERN).read_bytes(),
                CATALYST: (root / CATALYST).read_bytes(),
            }
            second = run(APPLY, root)
            self.assertIn("already applied; no changes", second.stdout)
            self.assertEqual(before[MODERN], (root / MODERN).read_bytes())
            self.assertEqual(before[CATALYST], (root / CATALYST).read_bytes())

    def test_existing_handler_is_extended_not_duplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root,
                MODERN,
                """package com.android.settings.deviceinfo.firmwareversion;

import android.content.Context;
import androidx.preference.Preference;
import com.android.settings.core.BasePreferenceController;

public class KernelVersionPreferenceController extends BasePreferenceController {
    public KernelVersionPreferenceController(Context context, String preferenceKey) {
        super(context, preferenceKey);
    }

    @Override
    public boolean handlePreferenceTreeClick(Preference preference) {
        if (!getPreferenceKey().equals(preference.getKey())) {
            return false;
        }
        preference.setSummary("full kernel");
        return false;
    }
}
""",
            )

            run(APPLY, root)
            text = (root / MODERN).read_text()
            self.assertEqual(
                text.count("public boolean handlePreferenceTreeClick(Preference preference)"),
                1,
            )
            self.assertIn("CitKernelTapLauncher.onKernelVersionTap(mContext);", text)
            self.assertIn('preference.setSummary("full kernel");', text)

    def test_mistos_hyper_preference_kernel_view_is_patched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root,
                MODERN,
                """package com.android.settings.deviceinfo.firmwareversion;
import android.content.Context;
import com.android.settings.core.BasePreferenceController;
public class KernelVersionPreferenceController extends BasePreferenceController {
    public KernelVersionPreferenceController(Context context, String preferenceKey) {
        super(context, preferenceKey);
    }
}
""",
            )
            write(
                root,
                MIST_HYPER,
                """package com.mist.utils;

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
""",
            )

            run(APPLY, root)
            text = (root / MIST_HYPER).read_text()
            self.assertIn(
                "import com.android.settings.deviceinfo.CitKernelTapLauncher;",
                text,
            )
            self.assertIn("MiuiCit Mist kernel tap integration", text)
            self.assertIn("CitKernelTapLauncher.onKernelVersionTap(context);", text)
            self.assertIn('kernel.setText("full");', text)

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

    public KernelVersionPreferenceController(Context context) {
        super(context);
    }

    @Override
    public void updateState(Preference preference) {
        super.updateState(preference);
        preference.setSummary(DeviceInfoUtils.getFormattedKernelVersion(mContext));
    }

    @Override
    public String getPreferenceKey() {
        return KEY_KERNEL_VERSION;
    }
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
            self.assertIn(
                "no supported KernelVersionPreferenceController found",
                result.stderr,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
