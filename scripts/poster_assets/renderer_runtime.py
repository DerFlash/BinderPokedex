#!/usr/bin/env python3
"""Validate and manage an ephemeral native macOS poster renderer runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = Path(__file__).with_name("renderer-runtime.lock.json")
RUNTIME_MARKER = ".binder-renderer-runtime.json"
MODEL_DIRECTORIES = (
    "diffusion_models",
    "text_encoders",
    "vae",
    "upscale_models",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def project_file(relative_path: str, project_root: Path = PROJECT_ROOT) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe project-relative path: {relative_path!r}")
    path = (project_root / relative).resolve()
    root = project_root.resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"Project path escapes repository: {relative_path!r}")
    return path


def validate_runtime_lock(
    lock_path: Path = LOCK_PATH,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    lock_path = lock_path.resolve()
    lock = load_json(lock_path)
    if lock.get("format_version") != 1:
        raise ValueError("Unsupported renderer runtime lock format")
    if lock.get("platform") != {"machine": "arm64", "system": "Darwin"}:
        raise ValueError("Renderer runtime lock must target Darwin arm64")

    for section in ("uv", "python", "comfyui", "requirements"):
        if not isinstance(lock.get(section), dict):
            raise ValueError(f"Renderer runtime lock is missing {section!r}")

    for section in ("uv", "comfyui"):
        url = str(lock[section].get("archive_url", ""))
        digest = str(lock[section].get("archive_sha256", ""))
        if not url.startswith("https://"):
            raise ValueError(f"{section} archive must use HTTPS")
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError(f"Invalid {section} archive SHA-256")

    requirements = lock["requirements"]
    for kind in ("input", "lock"):
        path = project_file(str(requirements.get(f"{kind}_path", "")), project_root)
        expected = str(requirements.get(f"{kind}_sha256", ""))
        if not path.is_file():
            raise FileNotFoundError(f"Missing renderer requirements {kind}: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(
                f"Renderer requirements {kind} SHA-256 mismatch: "
                f"expected {expected}, got {actual}"
            )
    return lock


def runtime_marker_path(runtime_root: Path) -> Path:
    return runtime_root.expanduser().resolve() / RUNTIME_MARKER


def write_runtime_marker(
    runtime_root: Path,
    model_root: Path,
    lock_path: Path = LOCK_PATH,
) -> Path:
    runtime_root = runtime_root.expanduser().resolve()
    model_root = model_root.expanduser().resolve()
    comfyui_root = runtime_root / "ComfyUI"
    python_bin = runtime_root / "venv" / "bin" / "python"
    models_link = comfyui_root / "models"
    if not comfyui_root.is_dir() or not python_bin.is_file():
        raise ValueError(f"Incomplete renderer runtime: {runtime_root}")
    if runtime_root == model_root or runtime_root in model_root.parents:
        raise ValueError("Model cache must live outside the ephemeral runtime")
    if model_root in runtime_root.parents:
        raise ValueError("Runtime must not live inside the persistent model cache")
    if not models_link.is_symlink() or models_link.resolve() != model_root:
        raise ValueError("ComfyUI/models must link to the selected model cache")
    for relative in MODEL_DIRECTORIES:
        if not (model_root / relative).is_dir():
            raise ValueError(f"Model cache is missing directory: {relative}")

    lock = validate_runtime_lock(lock_path)
    marker = {
        "format_version": 1,
        "comfyui_commit": lock["comfyui"]["commit"],
        "model_root": str(model_root),
        "runtime_lock_sha256": sha256_file(lock_path),
    }
    marker_path = runtime_root / RUNTIME_MARKER
    marker_path.write_text(
        json.dumps(marker, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return marker_path


def bind_model_cache(
    runtime_root: Path,
    model_root: Path,
    lock_path: Path = LOCK_PATH,
) -> Path:
    runtime_root = runtime_root.expanduser().resolve()
    model_root = model_root.expanduser().resolve()
    if runtime_root == model_root or runtime_root in model_root.parents:
        raise ValueError("Model cache must live outside the ephemeral runtime")
    if model_root in runtime_root.parents:
        raise ValueError("Runtime must not live inside the persistent model cache")
    comfyui_root = runtime_root / "ComfyUI"
    if not comfyui_root.is_dir():
        raise ValueError(f"Renderer has no ComfyUI directory: {runtime_root}")

    model_root.mkdir(parents=True, exist_ok=True)
    for relative in MODEL_DIRECTORIES:
        (model_root / relative).mkdir(parents=True, exist_ok=True)

    models_link = comfyui_root / "models"
    if models_link.is_symlink():
        models_link.unlink()
    elif models_link.exists():
        if any(models_link.iterdir()):
            raise ValueError(
                "Refusing to replace a non-empty ComfyUI/models directory"
            )
        models_link.rmdir()
    models_link.symlink_to(model_root, target_is_directory=True)
    return write_runtime_marker(runtime_root, model_root, lock_path)


def load_runtime_marker(runtime_root: Path) -> dict[str, Any]:
    marker_path = runtime_marker_path(runtime_root)
    marker = load_json(marker_path)
    if marker.get("format_version") != 1:
        raise ValueError("Unsupported renderer runtime marker format")
    return marker


def comfyui_commit(comfyui_root: Path) -> str:
    comfyui_root = comfyui_root.expanduser().resolve()
    if (comfyui_root / ".git").is_dir():
        return subprocess.run(
            ["git", "-C", str(comfyui_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    marker = load_runtime_marker(comfyui_root.parent)
    return str(marker.get("comfyui_commit", ""))


def validate_runtime(
    runtime_root: Path,
    lock_path: Path = LOCK_PATH,
) -> dict[str, Any]:
    runtime_root = runtime_root.expanduser().resolve()
    lock = validate_runtime_lock(lock_path)
    marker = load_runtime_marker(runtime_root)
    if marker.get("runtime_lock_sha256") != sha256_file(lock_path):
        raise ValueError("Renderer runtime was built from a different lock")
    if marker.get("comfyui_commit") != lock["comfyui"]["commit"]:
        raise ValueError("Renderer runtime ComfyUI commit does not match lock")
    model_root = Path(str(marker.get("model_root", ""))).expanduser().resolve()
    models_link = runtime_root / "ComfyUI" / "models"
    if not models_link.is_symlink() or models_link.resolve() != model_root:
        raise ValueError("Renderer model-cache link is missing or stale")
    if comfyui_commit(runtime_root / "ComfyUI") != lock["comfyui"]["commit"]:
        raise ValueError("Renderer ComfyUI source does not match lock")
    return marker


def destroy_runtime(runtime_root: Path, lock_path: Path = LOCK_PATH) -> None:
    runtime_root = runtime_root.expanduser().resolve()
    if runtime_root == Path("/") or len(runtime_root.parts) < 4:
        raise ValueError(f"Refusing unsafe runtime path: {runtime_root}")
    marker = load_runtime_marker(runtime_root)
    if not (runtime_root / "ComfyUI").is_dir():
        raise ValueError("Refusing to delete a directory without ComfyUI")
    if not (runtime_root / "venv" / "bin" / "python").is_file():
        raise ValueError("Refusing to delete a directory without renderer Python")
    commit = str(marker.get("comfyui_commit", ""))
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("Refusing to delete a runtime with an invalid marker")
    model_root = Path(str(marker["model_root"])).expanduser().resolve()
    if runtime_root == model_root or runtime_root in model_root.parents:
        raise ValueError("Refusing to delete a runtime that contains its model cache")
    shutil.rmtree(runtime_root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate-lock")

    marker = subparsers.add_parser("write-marker")
    marker.add_argument("--runtime-root", type=Path, required=True)
    marker.add_argument("--model-root", type=Path, required=True)

    bind = subparsers.add_parser("bind-models")
    bind.add_argument("--runtime-root", type=Path, required=True)
    bind.add_argument("--model-root", type=Path, required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--runtime-root", type=Path, required=True)

    destroy = subparsers.add_parser("destroy")
    destroy.add_argument("--runtime-root", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate-lock":
        validate_runtime_lock()
        print("renderer runtime lock valid")
    elif args.command == "write-marker":
        print(write_runtime_marker(args.runtime_root, args.model_root))
    elif args.command == "bind-models":
        print(bind_model_cache(args.runtime_root, args.model_root))
    elif args.command == "validate":
        validate_runtime(args.runtime_root)
        print("renderer runtime valid")
    elif args.command == "destroy":
        destroy_runtime(args.runtime_root)
        print(f"removed renderer runtime: {args.runtime_root}")
    else:
        raise AssertionError(args.command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
