#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 /path/to/UnpackerSystem/erofs" >&2
    exit 2
fi

ROOT="${1%/}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LIST="$REPO/runtime/REQUIRED_STOCK_FILES.txt"
GEN="$REPO/runtime/generated"
DEST="$GEN/proprietary"

rm -rf "$GEN"
mkdir -p "$DEST"

missing=0
count=0
while IFS= read -r rel; do
    [[ -z "$rel" || "$rel" == \#* ]] && continue
    src="$ROOT/$rel"
    if [[ ! -f "$src" ]]; then
        echo "MISSING: $rel" >&2
        missing=1
        continue
    fi

    mkdir -p "$DEST/$(dirname "$rel")"
    cp -a "$src" "$DEST/$rel"
    count=$((count + 1))
done < "$LIST"

if [[ $missing -ne 0 ]]; then
    echo "runtime import incomplete; removing partial output" >&2
    rm -rf "$GEN"
    exit 1
fi

find "$DEST" -type f -print0     | sort -z     | xargs -0 sha256sum     > "$GEN/SHA256SUMS"

echo "Imported $count stock runtime files into runtime/generated/proprietary."
echo "Runtime remains intentionally disabled until ELF dependencies and SELinux domains are validated."
