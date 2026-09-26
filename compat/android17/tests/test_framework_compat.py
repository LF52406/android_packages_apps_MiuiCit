#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "apply-framework-compat.py"
SPEC = importlib.util.spec_from_file_location("miuicit_framework_compat", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FrameworkCompatTest(unittest.TestCase):
    def make_tree(self, newline="\n"):
        root = Path(tempfile.mkdtemp(prefix="miuicit-framework-test-"))

        broadcast = root / MODULE.BROADCAST_REL
        audio_java = root / MODULE.AUDIORECORD_JAVA_REL
        audio_jni = root / MODULE.AUDIORECORD_JNI_REL

        broadcast.parent.mkdir(parents=True)
        audio_java.parent.mkdir(parents=True)
        audio_jni.parent.mkdir(parents=True)

        broadcast.write_text(
            (
                "class BroadcastController {\n"
                "    void test() {\n"
                "        boolean requireExplicitFlagForDynamicReceivers = CompatChanges.isChangeEnabled(\n"
                "                DYNAMIC_RECEIVER_EXPLICIT_EXPORT_REQUIRED, callingUid);\n"
                "    }\n"
                "}\n"
            ).replace("\n", newline),
            encoding="utf-8",
            newline="",
        )

        audio_java.write_text(
            (
                "class AudioRecord {\n"
                "    int mState;\n"
                "    static final int STATE_INITIALIZED = 1;\n"
                "    static final int ERROR_INVALID_OPERATION = -3;\n"
                "    static final int ERROR_BAD_VALUE = -2;\n"
                "    //---------------------------------------------------------\n"
                "    // Native methods called from the Java side\n"
                "    //--------------------\n"
                "    private native final boolean native_setInputDevice(int deviceId);\n"
                "}\n"
            ).replace("\n", newline),
            encoding="utf-8",
            newline="",
        )

        audio_jni.write_text(
            (
                "#include <utils/Log.h>\n"
                "static jboolean android_media_AudioRecord_setInputDevice(\n"
                "        JNIEnv *env, jobject thiz, jint device_id) { return true; }\n"
                "static const JNINativeMethod gMethods[] = {\n"
                "    {\"native_setInputDevice\", \"(I)Z\", "
                "(void *)android_media_AudioRecord_setInputDevice},\n"
                "};\n"
            ).replace("\n", newline),
            encoding="utf-8",
            newline="",
        )
        return root

    def test_patch_and_verify(self):
        root = self.make_tree()
        self.assertTrue(MODULE.patch_broadcast_controller(root / MODULE.BROADCAST_REL))
        self.assertTrue(MODULE.patch_audio_record_java(root / MODULE.AUDIORECORD_JAVA_REL))
        self.assertTrue(MODULE.patch_audio_record_jni(root / MODULE.AUDIORECORD_JNI_REL))
        MODULE.verify(root)

    def test_idempotent(self):
        root = self.make_tree()
        MODULE.patch_broadcast_controller(root / MODULE.BROADCAST_REL)
        MODULE.patch_audio_record_java(root / MODULE.AUDIORECORD_JAVA_REL)
        MODULE.patch_audio_record_jni(root / MODULE.AUDIORECORD_JNI_REL)

        self.assertFalse(MODULE.patch_broadcast_controller(root / MODULE.BROADCAST_REL))
        self.assertFalse(MODULE.patch_audio_record_java(root / MODULE.AUDIORECORD_JAVA_REL))
        self.assertFalse(MODULE.patch_audio_record_jni(root / MODULE.AUDIORECORD_JNI_REL))
        MODULE.verify(root)

    def test_crlf(self):
        root = self.make_tree("\r\n")
        MODULE.patch_broadcast_controller(root / MODULE.BROADCAST_REL)
        MODULE.patch_audio_record_java(root / MODULE.AUDIORECORD_JAVA_REL)
        MODULE.patch_audio_record_jni(root / MODULE.AUDIORECORD_JNI_REL)
        MODULE.verify(root)


if __name__ == "__main__":
    unittest.main()
