#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

CIT_PACKAGE = "com.miui.cit"

BROADCAST_REL = Path("services/core/java/com/android/server/am/BroadcastController.java")
AUDIORECORD_JAVA_REL = Path("media/java/android/media/AudioRecord.java")
AUDIORECORD_JNI_REL = Path("core/jni/android_media_AudioRecord.cpp")

BROADCAST_MARKER = '"com.miui.cit".equals(callerPackage)'
AUDIO_JAVA_MARKER = "public int setParameters(String keyValuePairs)"
AUDIO_JNI_MARKER = "android_media_AudioRecord_setParameters"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def newline_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def with_nl(text: str, nl: str) -> str:
    return text.replace("\n", nl)


def patch_broadcast_controller(path: Path) -> bool:
    text = read_text(path)
    if BROADCAST_MARKER in text:
        return False

    pattern = re.compile(
        r'(?m)^(?P<indent>[ \t]*)(?P<decl>(?:final\s+)?boolean\s+requireExplicitFlagForDynamicReceivers\s*=\s*'
        r'CompatChanges\.isChangeEnabled\(\s*'
        r'DYNAMIC_RECEIVER_EXPLICIT_EXPORT_REQUIRED\s*,\s*callingUid\s*\))'
        r'(?P<semi>\s*;)'
    )
    match = pattern.search(text)
    if match is None:
        raise RuntimeError(
            f"{path}: cannot find Android dynamic-receiver compatibility check"
        )

    indent = match.group("indent")
    cont = indent + "        "
    replacement = (
        indent
        + "// Xiaomi CIT is a platform-signed system diagnostic app whose stock APK "
        "predates explicit dynamic-receiver export flags.\n"
        + indent
        + "// Keep legacy receiver behavior only for the system-UID CIT package.\n"
        + indent
        + match.group("decl")
        + "\n"
        + cont
        + "&& !(callingUid == android.os.Process.SYSTEM_UID\n"
        + cont
        + f'        && "{CIT_PACKAGE}".equals(callerPackage))'
        + match.group("semi")
    )

    nl = newline_of(text)
    replacement = with_nl(replacement, nl)
    start, end = match.span()
    text = text[:start] + replacement + text[end:]
    write_text(path, text)
    return True


def patch_audio_record_java(path: Path) -> bool:
    text = read_text(path)
    changed = False
    nl = newline_of(text)

    # If the ROM already provides the OEM-compatible API, preserve it.
    if AUDIO_JAVA_MARKER in text and "return native_setParameters(keyValuePairs);" not in text:
        return False

    if AUDIO_JAVA_MARKER not in text:
        anchor = with_nl(
            """    //---------------------------------------------------------
    // Native methods called from the Java side
    //--------------------
""",
            nl,
        )
        if anchor not in text:
            raise RuntimeError(
                f"{path}: cannot find AudioRecord native-method section"
            )
        method = with_nl(
            """    /**
     * Sets implementation-specific parameters on this AudioRecord instance.
     *
     * <p>This hidden compatibility API is required by Xiaomi's stock CIT audio
     * diagnostics. Parameters are sent to the native AudioRecord input handle,
     * matching the OEM framework behavior instead of using global AudioSystem
     * parameters.</p>
     *
     * @hide
     */
    public int setParameters(String keyValuePairs) {
        if (mState != STATE_INITIALIZED) {
            return ERROR_INVALID_OPERATION;
        }
        if (keyValuePairs == null) {
            return ERROR_BAD_VALUE;
        }
        return native_setParameters(keyValuePairs);
    }

""",
            nl,
        )
        text = text.replace(anchor, method + anchor, 1)
        changed = True

    if "private native final int native_setParameters(String keyValuePairs);" not in text:
        anchor = "    private native final boolean native_setInputDevice(int deviceId);"
        if anchor not in text:
            raise RuntimeError(
                f"{path}: cannot find native_setInputDevice declaration"
            )
        text = text.replace(
            anchor,
            "    private native final int native_setParameters(String keyValuePairs);"
            + nl
            + anchor,
            1,
        )
        changed = True

    if changed:
        write_text(path, text)
    return changed


def patch_audio_record_jni(path: Path) -> bool:
    text = read_text(path)
    changed = False
    nl = newline_of(text)

    if "#include <utils/String8.h>" not in text:
        anchor = "#include <utils/Log.h>"
        if anchor not in text:
            raise RuntimeError(f"{path}: cannot find utils/Log.h include")
        text = text.replace(
            anchor, anchor + nl + "#include <utils/String8.h>", 1
        )
        changed = True

    if AUDIO_JNI_MARKER not in text:
        anchor_pattern = re.compile(
            r"(?m)^static jboolean android_media_AudioRecord_setInputDevice\("
        )
        match = anchor_pattern.search(text)
        if match is None:
            raise RuntimeError(
                f"{path}: cannot find AudioRecord setInputDevice JNI function"
            )
        function = with_nl(
            """static jint android_media_AudioRecord_setParameters(
        JNIEnv* env, jobject thiz, jstring keyValuePairs) {
    sp<AudioRecord> lpRecorder = getAudioRecord(env, thiz);
    if (lpRecorder == nullptr) {
        return (jint)AUDIO_JAVA_INVALID_OPERATION;
    }
    if (keyValuePairs == nullptr) {
        return (jint)AUDIO_JAVA_BAD_VALUE;
    }

    ScopedUtfChars params(env, keyValuePairs);
    if (params.c_str() == nullptr) {
        return (jint)AUDIO_JAVA_BAD_VALUE;
    }

    return nativeToJavaStatus(lpRecorder->setParameters(String8(params.c_str())));
}

// ----------------------------------------------------------------------------
""",
            nl,
        )
        text = text[: match.start()] + function + text[match.start() :]
        changed = True

    entry = (
        '{"native_setParameters", "(Ljava/lang/String;)I", '
        "(void *)android_media_AudioRecord_setParameters},"
    )
    if entry not in text:
        anchor = (
            '{"native_setInputDevice", "(I)Z", '
            "(void *)android_media_AudioRecord_setInputDevice},"
        )
        if anchor not in text:
            raise RuntimeError(
                f"{path}: cannot find native_setInputDevice JNI registration"
            )
        text = text.replace(anchor, entry + nl + "    " + anchor, 1)
        changed = True

    if changed:
        write_text(path, text)
    return changed


def verify(root: Path) -> None:
    broadcast = read_text(root / BROADCAST_REL)
    audio_java = read_text(root / AUDIORECORD_JAVA_REL)
    audio_jni = read_text(root / AUDIORECORD_JNI_REL)

    errors: list[str] = []
    if BROADCAST_MARKER not in broadcast:
        errors.append("CIT dynamic-receiver compatibility exception missing")
    if "android.os.Process.SYSTEM_UID" not in broadcast:
        errors.append("CIT receiver exception is not restricted to SYSTEM_UID")
    if AUDIO_JAVA_MARKER not in audio_java:
        errors.append("AudioRecord.setParameters(String) compatibility API missing")

    if "return native_setParameters(keyValuePairs);" in audio_java:
        if "private native final int native_setParameters(String keyValuePairs);" not in audio_java:
            errors.append("AudioRecord native_setParameters declaration missing")
        if AUDIO_JNI_MARKER not in audio_jni:
            errors.append("AudioRecord setParameters JNI bridge missing")
        if (
            '{"native_setParameters", "(Ljava/lang/String;)I", '
            "(void *)android_media_AudioRecord_setParameters},"
        ) not in audio_jni:
            errors.append("AudioRecord setParameters JNI registration missing")

    if errors:
        raise RuntimeError("; ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply Android framework compatibility required by stock Xiaomi MiuiCit"
    )
    parser.add_argument(
        "frameworks_base",
        nargs="?",
        default="frameworks/base",
        help="path to frameworks/base (default: frameworks/base)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that the compatibility patch is already present",
    )
    args = parser.parse_args()

    root = Path(args.frameworks_base)
    required = [
        root / BROADCAST_REL,
        root / AUDIORECORD_JAVA_REL,
        root / AUDIORECORD_JNI_REL,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        for path in missing:
            print(f"missing: {path}", file=sys.stderr)
        return 1

    try:
        if args.check:
            verify(root)
            print("MiuiCit Android framework compatibility: VERIFIED")
            return 0

        broadcast_changed = patch_broadcast_controller(root / BROADCAST_REL)
        audio_java_changed = patch_audio_record_java(root / AUDIORECORD_JAVA_REL)
        audio_java = read_text(root / AUDIORECORD_JAVA_REL)
        audio_jni_changed = False
        if "return native_setParameters(keyValuePairs);" in audio_java:
            audio_jni_changed = patch_audio_record_jni(root / AUDIORECORD_JNI_REL)

        changed = {
            "BroadcastController": broadcast_changed,
            "AudioRecord.java": audio_java_changed,
            "AudioRecord JNI": audio_jni_changed,
        }
        verify(root)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for name, did_change in changed.items():
        print(f"{name}: {'patched' if did_change else 'already present'}")
    print("MiuiCit Android framework compatibility: VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
