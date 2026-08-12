#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if (($# != 2)); then
  echo "Usage: $0 ABSOLUTE_RUNTIME_ROOT OUTPUT_TAR_GZ" >&2
  exit 2
fi

RUNTIME_ROOT="${1%/}"
OUTPUT_ARCHIVE="$2"
if [[ "$RUNTIME_ROOT" != /* ]]; then
  echo "Runtime root must be absolute" >&2
  exit 2
fi
if [[ "$OUTPUT_ARCHIVE" != /* ]]; then
  OUTPUT_ARCHIVE="$(pwd)/$OUTPUT_ARCHIVE"
fi
case "$OUTPUT_ARCHIVE" in
  "$RUNTIME_ROOT"/*)
    echo "Output archive must live outside the runtime" >&2
    exit 2
    ;;
esac
if [[ -e "$OUTPUT_ARCHIVE" ]]; then
  echo "Refusing to overwrite bundle archive: $OUTPUT_ARCHIVE" >&2
  exit 1
fi

"$RUNTIME_ROOT/venv/bin/python" "$SCRIPT_DIR/renderer_runtime.py" \
  validate --runtime-root "$RUNTIME_ROOT"
mkdir -p "$(dirname "$OUTPUT_ARCHIVE")"
tar -czf "$OUTPUT_ARCHIVE" \
  -C "$(dirname "$RUNTIME_ROOT")" \
  "$(basename "$RUNTIME_ROOT")"

echo "Renderer bundle: $OUTPUT_ARCHIVE"
echo "After extraction, run renderer_runtime.py bind-models for that worker."
