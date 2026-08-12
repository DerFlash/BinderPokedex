#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if (($# != 1)); then
  echo "Usage: $0 ABSOLUTE_RUNTIME_ROOT" >&2
  exit 2
fi

RUNTIME_ROOT="${1%/}"
if [[ "$RUNTIME_ROOT" != /* || "$RUNTIME_ROOT" == "/" ]]; then
  echo "Runtime root must be a safe absolute path" >&2
  exit 2
fi
"$RUNTIME_ROOT/venv/bin/python" "$SCRIPT_DIR/renderer_runtime.py" \
  destroy --runtime-root "$RUNTIME_ROOT"
