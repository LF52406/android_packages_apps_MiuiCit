#!/usr/bin/env python3
"""Verify the binary AndroidManifest.xml inside the stock MiuiCit APK.

No Android SDK tools are required. This is intentionally small and validates only
properties that are contractual for this AOSP port.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import struct
import sys
import zipfile

NO_INDEX = 0xFFFFFFFF


@dataclass
class Element:
    tag: str
    attrs: dict
    children: list["Element"] = field(default_factory=list)


class BinaryXml:
    def __init__(self, data: bytes):
        self.data = data
        self.strings: list[str] = []
        self.root: Element | None = None

    def u16(self, offset: int) -> int:
        return struct.unpack_from("<H", self.data, offset)[0]

    def u32(self, offset: int) -> int:
        return struct.unpack_from("<I", self.data, offset)[0]

    @staticmethod
    def read_len8(data: bytes, offset: int) -> tuple[int, int]:
        value = data[offset]
        offset += 1
        if value & 0x80:
            value = ((value & 0x7F) << 8) | data[offset]
            offset += 1
        return value, offset

    @staticmethod
    def read_len16(data: bytes, offset: int) -> tuple[int, int]:
        value = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        if value & 0x8000:
            second = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            value = ((value & 0x7FFF) << 16) | second
        return value, offset

    def string(self, index: int):
        return None if index == NO_INDEX else self.strings[index]

    def parse_string_pool(self) -> None:
        offset = 8
        while offset < len(self.data):
            chunk_type = self.u16(offset)
            header_size = self.u16(offset + 2)
            chunk_size = self.u32(offset + 4)
            if chunk_type == 0x0001:
                string_count = self.u32(offset + 8)
                flags = self.u32(offset + 16)
                strings_start = self.u32(offset + 20)
                string_offsets = [
                    self.u32(offset + header_size + index * 4)
                    for index in range(string_count)
                ]
                utf8 = bool(flags & 0x100)
                base = offset + strings_start

                for string_offset in string_offsets:
                    cursor = base + string_offset
                    if utf8:
                        _, cursor = self.read_len8(self.data, cursor)
                        byte_len, cursor = self.read_len8(self.data, cursor)
                        value = self.data[cursor:cursor + byte_len].decode(
                            "utf-8", "replace"
                        )
                    else:
                        char_len, cursor = self.read_len16(self.data, cursor)
                        value = self.data[cursor:cursor + char_len * 2].decode(
                            "utf-16le", "replace"
                        )
                    self.strings.append(value)
                return

            if chunk_size <= 0:
                break
            offset += chunk_size

        raise ValueError("AXML string pool not found")

    def decode_value(self, raw_index: int, data_type: int, value_data: int):
        if raw_index != NO_INDEX:
            return self.string(raw_index)
        if data_type == 0x03:
            return self.string(value_data)
        if data_type == 0x12:
            return bool(value_data)
        if data_type in (0x10, 0x11):
            return int(value_data)
        if data_type == 0x01:
            return f"@0x{value_data:08x}"
        return {"type": data_type, "data": value_data}

    def parse(self) -> Element:
        self.parse_string_pool()

        stack: list[Element] = []
        offset = 8
        while offset < len(self.data):
            chunk_type = self.u16(offset)
            chunk_size = self.u32(offset + 4)

            if chunk_type == 0x0102:
                ext = offset + 16
                name_index = self.u32(ext + 4)
                attr_start = self.u16(ext + 8)
                attr_size = self.u16(ext + 10)
                attr_count = self.u16(ext + 12)

                attrs = {}
                first_attr = ext + attr_start
                for index in range(attr_count):
                    attr = first_attr + index * attr_size
                    attr_name = self.u32(attr + 4)
                    raw_value = self.u32(attr + 8)
                    data_type = self.data[attr + 15]
                    value_data = self.u32(attr + 16)
                    attrs[self.string(attr_name)] = self.decode_value(
                        raw_value, data_type, value_data
                    )

                element = Element(self.string(name_index), attrs)
                if stack:
                    stack[-1].children.append(element)
                else:
                    self.root = element
                stack.append(element)

            elif chunk_type == 0x0103 and stack:
                stack.pop()

            if chunk_size <= 0:
                break
            offset += chunk_size

        if self.root is None:
            raise ValueError("AXML root element not found")
        return self.root


def walk(element: Element):
    yield element
    for child in element.children:
        yield from walk(child)


def find(root: Element, tag: str, name: str | None = None):
    for element in walk(root):
        if element.tag != tag:
            continue
        if name is None or element.attrs.get("name") == name:
            return element
    return None


def descendants(root: Element | None, tag: str):
    return [] if root is None else [e for e in walk(root) if e.tag == tag]


def has_action(root: Element | None, action: str) -> bool:
    return any(e.attrs.get("name") == action for e in descendants(root, "action"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("apk")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        with zipfile.ZipFile(args.apk) as apk:
            manifest = apk.read("AndroidManifest.xml")
        root = BinaryXml(manifest).parse()
    except Exception as exc:
        print(f"ERROR: cannot parse APK manifest: {exc}", file=sys.stderr)
        return 1

    failures: list[str] = []

    def expect(label: str, actual, expected) -> None:
        if actual != expected:
            failures.append(
                f"{label}: expected {expected!r}, got {actual!r}"
            )

    expect("package", root.attrs.get("package"), "com.miui.cit")
    expect("sharedUserId", root.attrs.get("sharedUserId"), "android.uid.system")
    expect("versionCode", root.attrs.get("versionCode"), 47)
    expect("versionName", root.attrs.get("versionName"), "0.4.9-SNAPSHOT")

    sdk = find(root, "uses-sdk")
    expect("minSdkVersion", sdk.attrs.get("minSdkVersion") if sdk else None, 28)
    expect("targetSdkVersion", sdk.attrs.get("targetSdkVersion") if sdk else None, 33)

    app = find(root, "application")
    expect(
        "application",
        app.attrs.get("name") if app else None,
        "com.miui.cit.CitApplication",
    )
    expect(
        "extractNativeLibs",
        app.attrs.get("extractNativeLibs") if app else None,
        False,
    )

    home = find(root, "activity", "com.miui.cit.home.HomeActivity")
    expect("HomeActivity exported", home.attrs.get("exported") if home else None, True)
    if not has_action(home, "com.miui.cit.MAGIC_NUMBER"):
        failures.append("HomeActivity MAGIC_NUMBER action missing")

    receiver = find(
        root, "receiver", "com.miui.cit.receiver.CitBroadcastReceiver"
    )
    expect(
        "CitBroadcastReceiver exported",
        receiver.attrs.get("exported") if receiver else None,
        True,
    )
    if not has_action(receiver, "android.provider.Telephony.SECRET_CODE"):
        failures.append("SECRET_CODE action missing")

    secret_code_ok = any(
        node.attrs.get("scheme") == "android_secret_code"
        and str(node.attrs.get("host")) == "6484"
        for node in descendants(receiver, "data")
    )
    if not secret_code_ok:
        failures.append("secret code 6484 data missing")

    permissions = [
        node.attrs.get("name")
        for node in descendants(root, "uses-permission")
    ]
    for permission in (
        "android.permission.MODIFY_PHONE_STATE",
        "android.permission.READ_PRIVILEGED_PHONE_STATE",
        "android.permission.WRITE_SECURE_SETTINGS",
        "android.permission.INTERACT_ACROSS_USERS_FULL",
        "android.permission.MANAGE_FINGERPRINT",
    ):
        if permission not in permissions:
            failures.append(
                f"required permission declaration missing: {permission}"
            )

    uses_libraries = [
        node.attrs.get("name")
        for node in descendants(root, "uses-library")
    ]

    summary = {
        "package": root.attrs.get("package"),
        "sharedUserId": root.attrs.get("sharedUserId"),
        "versionCode": root.attrs.get("versionCode"),
        "versionName": root.attrs.get("versionName"),
        "minSdkVersion": sdk.attrs.get("minSdkVersion") if sdk else None,
        "targetSdkVersion": sdk.attrs.get("targetSdkVersion") if sdk else None,
        "application": app.attrs.get("name") if app else None,
        "extractNativeLibs": app.attrs.get("extractNativeLibs") if app else None,
        "homeActivity": {
            "name": home.attrs.get("name") if home else None,
            "exported": home.attrs.get("exported") if home else None,
            "magicNumberAction": has_action(home, "com.miui.cit.MAGIC_NUMBER"),
        },
        "secretCodeReceiver": {
            "name": receiver.attrs.get("name") if receiver else None,
            "exported": receiver.attrs.get("exported") if receiver else None,
            "code6484": secret_code_ok,
        },
        "requestedPermissionCount": len(permissions),
        "usesLibraries": uses_libraries,
        "status": "failed" if failures else "verified",
        "failures": failures,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
    else:
        print("MiuiCit manifest: VERIFIED")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
