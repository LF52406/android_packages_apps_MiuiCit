#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
FRAMEWORKS_BASE="${1:-frameworks/base}"

if [[ $# -gt 2 ]]; then
    echo "usage: $0 [path/to/frameworks/base] [--check]" >&2
    exit 2
fi

if [[ ! -d "$FRAMEWORKS_BASE" ]]; then
    echo "frameworks/base not found: $FRAMEWORKS_BASE" >&2
    exit 1
fi

ARGS=("$FRAMEWORKS_BASE")
if [[ "${2:-}" == "--check" ]]; then
    ARGS+=("--check")
elif [[ $# -eq 2 ]]; then
    echo "unknown option: $2" >&2
    exit 2
fi

python3 "$REPO/compat/android17/apply-framework-compat.py" "${ARGS[@]}"
