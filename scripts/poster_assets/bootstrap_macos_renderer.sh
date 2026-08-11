#!/usr/bin/env bash
set -euo pipefail

UV_VERSION="0.11.16"
UV_ARCHIVE_URL="https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-aarch64-apple-darwin.tar.gz"
UV_ARCHIVE_SHA256="2b25be1af546be330b340b0a76b99f989daa6d92678fdffb87438e661e9d88fb"
PYTHON_VERSION="3.11.13"
COMFYUI_COMMIT="87d23b81765161624889febfb3b81f19f3c8435b"
COMFYUI_ARCHIVE_URL="https://github.com/Comfy-Org/ComfyUI/archive/${COMFYUI_COMMIT}.tar.gz"
COMFYUI_ARCHIVE_SHA256="0dfde1cf40340cad7d1f96ff450af00f6498aa6234d9a7abcccba24e1d4b1a25"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIREMENTS_LOCK="$SCRIPT_DIR/renderer-requirements.lock"

if (($# != 2)); then
  echo "Usage: $0 ABSOLUTE_RUNTIME_ROOT ABSOLUTE_MODEL_ROOT" >&2
  exit 2
fi

RUNTIME_ROOT="${1%/}"
MODEL_ROOT="${2%/}"
if [[ "$RUNTIME_ROOT" != /* || "$MODEL_ROOT" != /* ]]; then
  echo "Runtime and model roots must be absolute" >&2
  exit 2
fi
if [[ "$RUNTIME_ROOT" == "/" || "$MODEL_ROOT" == "/" ]]; then
  echo "Refusing a filesystem root as runtime or model cache" >&2
  exit 2
fi
case "$MODEL_ROOT/" in
  "$RUNTIME_ROOT/"*)
    echo "Model cache must live outside the ephemeral runtime" >&2
    exit 2
    ;;
esac
case "$RUNTIME_ROOT/" in
  "$MODEL_ROOT/"*)
    echo "Runtime must not live inside the persistent model cache" >&2
    exit 2
    ;;
esac
if [[ -e "$RUNTIME_ROOT" || -L "$RUNTIME_ROOT" ]]; then
  echo "Runtime root already exists; validate or destroy it first: $RUNTIME_ROOT" >&2
  exit 1
fi
if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "The native renderer requires Darwin on Apple Silicon arm64" >&2
  exit 1
fi
for command in curl tar shasum awk; do
  if ! command -v "$command" >/dev/null; then
    echo "Required macOS command is missing: $command" >&2
    exit 1
  fi
done

verify_sha256() {
  local path="$1"
  local expected="$2"
  local actual
  actual="$(shasum -a 256 "$path" | awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "SHA-256 mismatch for $path: expected $expected, got $actual" >&2
    exit 1
  fi
}

created_runtime=0
cleanup_failed_runtime() {
  if ((created_runtime == 1)) && [[ -f "$RUNTIME_ROOT/.binder-bootstrap-incomplete" ]]; then
    rm -rf "$RUNTIME_ROOT"
  fi
}
trap cleanup_failed_runtime EXIT

mkdir -p "$RUNTIME_ROOT/downloads" "$RUNTIME_ROOT/tools" "$MODEL_ROOT"
created_runtime=1
touch "$RUNTIME_ROOT/.binder-bootstrap-incomplete"

UV_ARCHIVE="$RUNTIME_ROOT/downloads/uv.tar.gz"
curl -fL --proto '=https' --tlsv1.2 "$UV_ARCHIVE_URL" -o "$UV_ARCHIVE"
verify_sha256 "$UV_ARCHIVE" "$UV_ARCHIVE_SHA256"
tar -xzf "$UV_ARCHIVE" -C "$RUNTIME_ROOT/tools" --strip-components=1 \
  uv-aarch64-apple-darwin/uv \
  uv-aarch64-apple-darwin/uvx
UV_BIN="$RUNTIME_ROOT/tools/uv"

export UV_CACHE_DIR="$RUNTIME_ROOT/cache/uv"
export UV_PYTHON_INSTALL_DIR="$RUNTIME_ROOT/python"
export UV_PYTHON_BIN_DIR="$RUNTIME_ROOT/python-bin"
export UV_NO_MODIFY_PATH=1
export UV_ISOLATED=1

"$UV_BIN" python install "$PYTHON_VERSION" \
  --install-dir "$UV_PYTHON_INSTALL_DIR"
PYTHON_BIN="$("$UV_BIN" python find --managed-python "$PYTHON_VERSION")"
"$PYTHON_BIN" "$SCRIPT_DIR/renderer_runtime.py" validate-lock
"$UV_BIN" venv "$RUNTIME_ROOT/venv" \
  --python "$PYTHON_BIN" \
  --relocatable
"$UV_BIN" pip sync "$REQUIREMENTS_LOCK" \
  --python "$RUNTIME_ROOT/venv/bin/python" \
  --require-hashes \
  --strict

COMFYUI_ARCHIVE="$RUNTIME_ROOT/downloads/ComfyUI.tar.gz"
curl -fL --proto '=https' --tlsv1.2 "$COMFYUI_ARCHIVE_URL" \
  -o "$COMFYUI_ARCHIVE"
verify_sha256 "$COMFYUI_ARCHIVE" "$COMFYUI_ARCHIVE_SHA256"
tar -xzf "$COMFYUI_ARCHIVE" -C "$RUNTIME_ROOT"
mv "$RUNTIME_ROOT/ComfyUI-$COMFYUI_COMMIT" "$RUNTIME_ROOT/ComfyUI"
COMFY_ROOT="$RUNTIME_ROOT/ComfyUI"

# Seed only ComfyUI's small directory/config skeleton into the persistent
# cache. The verified source archive never contains model weights.
cp -R "$COMFY_ROOT/models/." "$MODEL_ROOT/"
rm -rf "$COMFY_ROOT/models"
ln -s "$MODEL_ROOT" "$COMFY_ROOT/models"
for directory in diffusion_models text_encoders vae upscale_models; do
  mkdir -p "$MODEL_ROOT/$directory"
done

SITE_PACKAGES="$("$RUNTIME_ROOT/venv/bin/python" -c \
  'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
"$RUNTIME_ROOT/venv/bin/python" "$SCRIPT_DIR/patch_comfyui_mps.py" \
  "$SITE_PACKAGES/comfy_kitchen/backends/eager/quantization.py" \
  --model-management-py "$COMFY_ROOT/comfy/model_management.py" \
  --nvfp4-py "$SITE_PACKAGES/comfy_kitchen/tensor/nvfp4.py"

"$RUNTIME_ROOT/venv/bin/python" "$SCRIPT_DIR/renderer_runtime.py" \
  write-marker \
  --runtime-root "$RUNTIME_ROOT" \
  --model-root "$MODEL_ROOT"

"$RUNTIME_ROOT/venv/bin/python" - <<'PY'
import platform
import torch

if platform.machine() != "arm64":
    raise SystemExit(f"Expected Apple Silicon arm64, got {platform.machine()}")
if not torch.backends.mps.is_available():
    raise SystemExit("PyTorch MPS is not available")
print(f"renderer ready: torch={torch.__version__}, device=mps")
PY

rm "$RUNTIME_ROOT/.binder-bootstrap-incomplete"
rm -rf "$RUNTIME_ROOT/downloads" "$RUNTIME_ROOT/cache"
trap - EXIT

echo "Runtime: $RUNTIME_ROOT"
echo "ComfyUI: $COMFY_ROOT@$COMFYUI_COMMIT"
echo "Python:  $RUNTIME_ROOT/venv/bin/python"
echo "Models:  $MODEL_ROOT (external, retained on destroy)"
echo "Jobs:    choose a separate path below the operator's private render root"
