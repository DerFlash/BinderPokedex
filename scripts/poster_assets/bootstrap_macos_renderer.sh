#!/usr/bin/env bash
set -euo pipefail

COMFYUI_COMMIT="87d23b81765161624889febfb3b81f19f3c8435b"
PYTHON_BIN="${PYTHON_BIN:-/opt/homebrew/bin/python3.11}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if (($# != 1)); then
  echo "Usage: $0 ABSOLUTE_RENDER_ROOT" >&2
  exit 2
fi

RENDER_ROOT="$1"
if [[ "$RENDER_ROOT" != /* ]]; then
  echo "ABSOLUTE_RENDER_ROOT must be absolute" >&2
  exit 2
fi
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python 3.11 not found: $PYTHON_BIN" >&2
  exit 1
fi

COMFY_ROOT="$RENDER_ROOT/ComfyUI"
VENV_ROOT="$RENDER_ROOT/venv"
mkdir -p "$RENDER_ROOT/jobs"

if [[ ! -d "$COMFY_ROOT/.git" ]]; then
  git clone --filter=blob:none \
    https://github.com/Comfy-Org/ComfyUI.git \
    "$COMFY_ROOT"
fi

git -C "$COMFY_ROOT" fetch --depth 1 origin "$COMFYUI_COMMIT"
git -C "$COMFY_ROOT" checkout --detach "$COMFYUI_COMMIT"

if [[ ! -x "$VENV_ROOT/bin/python" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_ROOT"
fi
"$VENV_ROOT/bin/python" -m pip install --upgrade pip
"$VENV_ROOT/bin/python" -m pip install -r "$COMFY_ROOT/requirements.txt"

SITE_PACKAGES="$("$VENV_ROOT/bin/python" -c \
  'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
"$VENV_ROOT/bin/python" "$SCRIPT_DIR/patch_comfyui_mps.py" \
  "$SITE_PACKAGES/comfy_kitchen/backends/eager/quantization.py" \
  --model-management-py "$COMFY_ROOT/comfy/model_management.py" \
  --nvfp4-py "$SITE_PACKAGES/comfy_kitchen/tensor/nvfp4.py"

actual_commit="$(git -C "$COMFY_ROOT" rev-parse HEAD)"
if [[ "$actual_commit" != "$COMFYUI_COMMIT" ]]; then
  echo "Unexpected ComfyUI commit: $actual_commit" >&2
  exit 1
fi

"$VENV_ROOT/bin/python" - <<'PY'
import platform
import torch

if platform.machine() != "arm64":
    raise SystemExit(f"Expected Apple Silicon arm64, got {platform.machine()}")
if not torch.backends.mps.is_available():
    raise SystemExit("PyTorch MPS is not available")
print(f"renderer ready: torch={torch.__version__}, device=mps")
PY

echo "ComfyUI: $COMFY_ROOT@$actual_commit"
echo "Python:  $VENV_ROOT/bin/python"
echo "Models:  $COMFY_ROOT/models"
echo "Jobs:    $RENDER_ROOT/jobs"
