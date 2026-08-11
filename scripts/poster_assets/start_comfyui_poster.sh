#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
POSTER_ASSETS_DIR="${BINDER_POKEDEX_POSTER_ASSETS:-$ROOT_DIR/data/poster_assets}"
if [[ "$POSTER_ASSETS_DIR" != /* ]]; then
  POSTER_ASSETS_DIR="$ROOT_DIR/$POSTER_ASSETS_DIR"
fi
COMFY_ROOT="${COMFY_ROOT:-$ROOT_DIR/.local_ai/ComfyUI}"
COMFY_PY="${COMFY_PY:-$ROOT_DIR/.local_ai/venv-comfyui/bin/python}"
COMFY_PY_PREFIX="$(dirname "$(dirname "$COMFY_PY")")"
POSTER_SCOPE="${POSTER_SCOPE:-Base1}"

COMFY_ARGS=()
while (($#)); do
  case "$1" in
    --scope)
      if (($# < 2)); then
        echo "--scope requires a value" >&2
        exit 2
      fi
      POSTER_SCOPE="$2"
      shift 2
      ;;
    --scope=*)
      POSTER_SCOPE="${1#*=}"
      shift
      ;;
    *)
      COMFY_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ -n "${BINDER_POKEDEX_POSTER_ASSETS:-}" ]]; then
  POSTER_CONFIG_ROOT="$BINDER_POKEDEX_POSTER_ASSETS"
  POSTER_WORK_ROOT="$BINDER_POKEDEX_POSTER_ASSETS"
else
  POSTER_CONFIG_ROOT="$ROOT_DIR/config/posters"
  POSTER_WORK_ROOT="$ROOT_DIR/tmp/poster-workspaces"
fi
if [[ "$POSTER_CONFIG_ROOT" != /* ]]; then
  POSTER_CONFIG_ROOT="$ROOT_DIR/$POSTER_CONFIG_ROOT"
  POSTER_WORK_ROOT="$ROOT_DIR/$POSTER_WORK_ROOT"
fi
EXPERIMENT_DIR="$POSTER_WORK_ROOT/$POSTER_SCOPE/comfyui_poster"
if ((${#COMFY_ARGS[@]})); then
  set -- "${COMFY_ARGS[@]}"
else
  set --
fi

if [[ ! -x "$COMFY_PY" || ! -f "$COMFY_ROOT/main.py" ]]; then
  echo "ComfyUI installation not found. Set COMFY_ROOT and COMFY_PY." >&2
  exit 1
fi
if [[ ! -f "$POSTER_CONFIG_ROOT/$POSTER_SCOPE/poster.yaml" ]]; then
  echo "Poster scope not found: $POSTER_SCOPE" >&2
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
