#!/usr/bin/env bash
set -euo pipefail

UV_VERSION="0.11.16"
UV_ARCHIVE_URL="https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-aarch64-apple-darwin.tar.gz"
UV_ARCHIVE_SHA256="2b25be1af546be330b340b0a76b99f989daa6d92678fdffb87438e661e9d88fb"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INPUT="$SCRIPT_DIR/renderer-requirements.in"
LOCK="$SCRIPT_DIR/renderer-requirements.lock"
INPUT_REL="scripts/poster_assets/renderer-requirements.in"
LOCK_REL="scripts/poster_assets/renderer-requirements.lock"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "Renderer locks must be refreshed on Darwin arm64" >&2
  exit 1
fi

TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/binder-renderer-lock.XXXXXX")"
cleanup() {
  rm -rf "$TEMP_ROOT"
}
trap cleanup EXIT

ARCHIVE="$TEMP_ROOT/uv.tar.gz"
curl -fL --proto '=https' --tlsv1.2 "$UV_ARCHIVE_URL" -o "$ARCHIVE"
actual_sha="$(shasum -a 256 "$ARCHIVE" | awk '{print $1}')"
if [[ "$actual_sha" != "$UV_ARCHIVE_SHA256" ]]; then
  echo "uv SHA-256 mismatch: expected $UV_ARCHIVE_SHA256, got $actual_sha" >&2
  exit 1
fi
tar -xzf "$ARCHIVE" -C "$TEMP_ROOT"
UV_BIN="$TEMP_ROOT/uv-aarch64-apple-darwin/uv"

cd "$PROJECT_ROOT"
"$UV_BIN" pip compile "$INPUT_REL" \
  --python-platform aarch64-apple-darwin \
  --python-version 3.11.13 \
  --generate-hashes \
  --output-file "$LOCK_REL" \
  --custom-compile-command scripts/poster_assets/refresh_renderer_lock.sh \
  --no-cache \
  --quiet

input_sha="$(shasum -a 256 "$INPUT" | awk '{print $1}')"
lock_sha="$(shasum -a 256 "$LOCK" | awk '{print $1}')"
echo "Renderer dependency lock refreshed."
echo "Update renderer-runtime.lock.json requirements.input_sha256 to $input_sha"
echo "Update renderer-runtime.lock.json requirements.lock_sha256 to $lock_sha"
echo "Then run renderer tests and one native MPS smoke render."
