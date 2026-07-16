#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMFY_ROOT="${COMFY_ROOT:-/Volumes/Daten/Entwicklung/BinderPokedex/.local_ai/ComfyUI}"
COMFY_PY="${COMFY_PY:-/Volumes/Daten/Entwicklung/BinderPokedex/.local_ai/venv-comfyui/bin/python}"
POSTER_SCOPE="${POSTER_SCOPE:-Base1}"
EXPERIMENT_DIR="$ROOT_DIR/data/poster_assets/$POSTER_SCOPE/comfyui_poster"

if [[ ! -x "$COMFY_PY" || ! -f "$COMFY_ROOT/main.py" ]]; then
  echo "ComfyUI installation not found. Set COMFY_ROOT and COMFY_PY." >&2
  exit 1
fi

mkdir -p "$EXPERIMENT_DIR/output" "$EXPERIMENT_DIR/temp"
exec "$COMFY_PY" "$COMFY_ROOT/main.py" \
  --listen 127.0.0.1 \
  --port "${COMFYUI_PORT:-8188}" \
  --input-directory "$EXPERIMENT_DIR" \
  --output-directory "$EXPERIMENT_DIR/output" \
  --temp-directory "$EXPERIMENT_DIR/temp" \
  "$@"
