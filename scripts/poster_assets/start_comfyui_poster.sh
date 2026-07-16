#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMFY_ROOT="${COMFY_ROOT:-/Volumes/Daten/Entwicklung/BinderPokedex/.local_ai/ComfyUI}"
COMFY_PY="${COMFY_PY:-/Volumes/Daten/Entwicklung/BinderPokedex/.local_ai/venv-comfyui/bin/python}"
COMFY_PY_PREFIX="$(dirname "$(dirname "$COMFY_PY")")"
POSTER_SCOPE="${POSTER_SCOPE:-Base1}"
EXPERIMENT_DIR="$ROOT_DIR/data/poster_assets/$POSTER_SCOPE/comfyui_poster"

if [[ ! -x "$COMFY_PY" || ! -f "$COMFY_ROOT/main.py" ]]; then
  echo "ComfyUI installation not found. Set COMFY_ROOT and COMFY_PY." >&2
  exit 1
fi

"$COMFY_PY" "$ROOT_DIR/scripts/poster_assets/patch_comfyui_mps.py" \
  "$COMFY_PY_PREFIX/lib/python3.11/site-packages/comfy_kitchen/backends/eager/quantization.py" \
  --model-management-py "$COMFY_ROOT/comfy/model_management.py" \
  --nvfp4-py "$COMFY_PY_PREFIX/lib/python3.11/site-packages/comfy_kitchen/tensor/nvfp4.py"

mkdir -p "$EXPERIMENT_DIR/output" "$EXPERIMENT_DIR/temp"
exec "$COMFY_PY" "$COMFY_ROOT/main.py" \
  --listen 127.0.0.1 \
  --port "${COMFYUI_PORT:-8188}" \
  --input-directory "$EXPERIMENT_DIR" \
  --output-directory "$EXPERIMENT_DIR/output" \
  --temp-directory "$EXPERIMENT_DIR/temp" \
  "$@"
