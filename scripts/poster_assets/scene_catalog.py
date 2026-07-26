"""Load and validate the set-specific creative briefs for poster generation."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    from .poster_io import ROOT, SCOPE_DATA, load_json, load_yaml
except ImportError:
    from poster_io import ROOT, SCOPE_DATA, load_json, load_yaml


SCENE_CATALOG = ROOT / "config" / "poster_scenes.yaml"
REQUIRED_SCENE_FIELDS = (
    "concept",
    "setting",
    "lighting",
    "rendering",
    "ground_noun",
)


def _validate_scene(scope: str, scene: object) -> dict[str, Any]:
    if not isinstance(scene, dict):
        raise ValueError(f"Poster scene for {scope} must be a mapping")
    for field in REQUIRED_SCENE_FIELDS:
        value = scene.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Poster scene for {scope} needs non-empty field {field!r}"
            )
    constraints = scene.get("constraints", [])
    if isinstance(constraints, str):
        constraints = [constraints]
    if not isinstance(constraints, list) or not all(
        isinstance(item, str) and item.strip() for item in constraints
    ):
        raise ValueError(
            f"Poster scene constraints for {scope} must be text or a text list"
        )
    return scene


def load_scene_catalog(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Return the validated scope-to-scene mapping."""
    catalog_path = path or SCENE_CATALOG
    catalog = load_yaml(catalog_path)
    if catalog.get("version") != 1:
        raise ValueError(f"Unsupported poster scene catalog version: {catalog_path}")
    scopes = catalog.get("scopes")
    if not isinstance(scopes, dict) or not scopes:
        raise ValueError(f"Poster scene catalog has no scopes: {catalog_path}")
    return {
        str(scope): deepcopy(_validate_scene(str(scope), scene))
        for scope, scene in scopes.items()
    }


def scene_for_scope(
    scope: str,
    *,
    catalog_path: Path | None = None,
) -> dict[str, Any]:
    """Return one set's creative brief or fail before an expensive render."""
    scenes = load_scene_catalog(catalog_path)
    try:
        return scenes[scope]
    except KeyError as error:
        raise KeyError(
            f"No poster scene brief configured for TCG scope {scope!r} in "
            f"{catalog_path or SCENE_CATALOG}"
        ) from error


def current_tcg_scopes(data_dir: Path | None = None) -> set[str]:
    """Return every individual TCG-set scope in generated data."""
    scope_dir = data_dir or SCOPE_DATA
    result = set()
    for path in scope_dir.glob("*.json"):
        if load_json(path).get("type") == "tcg_set":
            result.add(path.stem)
    return result


def validate_catalog_coverage(
    *,
    catalog_path: Path | None = None,
    data_dir: Path | None = None,
) -> tuple[set[str], set[str]]:
    """Return missing and stale scene entries for the current generated data."""
    configured = set(load_scene_catalog(catalog_path))
    current = current_tcg_scopes(data_dir)
    return current - configured, configured - current
