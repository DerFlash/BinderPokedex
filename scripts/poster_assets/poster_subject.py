"""Canonical poster-subject identities shared by fetch and poster tooling.

Card/cover artwork and the transparent subject used to generate a poster are
different assets.  ``poster_subject`` keeps the latter explicit so special
forms cannot silently fall back to their base species.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SOURCE = "pokeapi_official_artwork"
SUBJECT_KEY_PREFIX = "pokeapi:official-artwork:"
OFFICIAL_ARTWORK_URL = (
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
    "sprites/pokemon/other/official-artwork/{artwork_id}.png"
)
_OFFICIAL_ARTWORK_URL = re.compile(
    r"https://raw\.githubusercontent\.com/PokeAPI/sprites/master/"
    r"sprites/pokemon/other/official-artwork/([1-9][0-9]*)\.png"
)
FORM_SPECIES_REGISTRY_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "pokeapi_form_species.json"
)


def _positive_int(value: object, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _load_form_species_registry() -> tuple[int, dict[int, int]]:
    """Load the pinned PokeAPI form-to-species trust root."""
    try:
        payload = json.loads(
            FORM_SPECIES_REGISTRY_PATH.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Cannot load poster-subject registry "
            f"{FORM_SPECIES_REGISTRY_PATH}"
        ) from error
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise RuntimeError("Unsupported PokeAPI form-species registry")
    max_species_id = _positive_int(
        payload.get("max_species_id"),
        "max_species_id",
    )
    raw_mapping = payload.get("form_species")
    if not isinstance(raw_mapping, dict) or not raw_mapping:
        raise RuntimeError("PokeAPI form-species registry is empty")
    mapping: dict[int, int] = {}
    for raw_artwork_id, raw_species_id in raw_mapping.items():
        if (
            not isinstance(raw_artwork_id, str)
            or not raw_artwork_id.isdigit()
        ):
            raise RuntimeError(
                "PokeAPI form-species registry has an invalid artwork ID"
            )
        artwork_id = int(raw_artwork_id)
        species_id = _positive_int(raw_species_id, "registry species_id")
        if artwork_id <= max_species_id or species_id > max_species_id:
            raise RuntimeError(
                "PokeAPI form-species registry contains an invalid mapping"
            )
        mapping[artwork_id] = species_id
    return max_species_id, mapping


MAX_SPECIES_ID, FORM_SPECIES_BY_ARTWORK_ID = _load_form_species_registry()


@dataclass(frozen=True)
class PosterSubject:
    """One exact PokeAPI artwork subject and its base species."""

    species_id: int
    official_artwork_id: int
    source: str = SOURCE

    def __post_init__(self) -> None:
        species_id = _positive_int(self.species_id, "species_id")
        artwork_id = _positive_int(
            self.official_artwork_id,
            "official_artwork_id",
        )
        if self.source != SOURCE:
            raise ValueError(
                f"Unsupported poster subject source {self.source!r}"
            )
        if species_id > MAX_SPECIES_ID:
            raise ValueError(
                f"Pokemon species #{species_id} is not present in the pinned "
                "PokeAPI registry"
            )
        if artwork_id != species_id:
            registered_species = FORM_SPECIES_BY_ARTWORK_ID.get(artwork_id)
            if registered_species is None:
                raise ValueError(
                    f"Official artwork #{artwork_id} is not present in the "
                    "pinned PokeAPI form registry"
                )
            if registered_species != species_id:
                raise ValueError(
                    f"Official artwork #{artwork_id} belongs to Pokemon "
                    f"#{registered_species}, not #{species_id}"
                )

    @property
    def subject_key(self) -> str:
        return f"{SUBJECT_KEY_PREFIX}{self.official_artwork_id}"

    @property
    def image_url(self) -> str:
        return OFFICIAL_ARTWORK_URL.format(
            artwork_id=self.official_artwork_id
        )

    @property
    def is_special_form(self) -> bool:
        return self.official_artwork_id != self.species_id

    def as_mapping(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "species_id": self.species_id,
            "official_artwork_id": self.official_artwork_id,
            "subject_key": self.subject_key,
            "image_url": self.image_url,
        }

    def artwork_key(self) -> tuple[str, int]:
        return self.source, self.official_artwork_id

    def selection_key(self) -> tuple[str, int, int]:
        return self.source, self.species_id, self.official_artwork_id

    def fingerprint_identity(self) -> int | dict[str, Any]:
        """Preserve the historic integer identity for ordinary base forms."""
        if not self.is_special_form:
            return self.species_id
        return {
            "pokemon_id": self.species_id,
            "poster_subject": {
                "source": self.source,
                "official_artwork_id": self.official_artwork_id,
            },
        }


def official_artwork_id_from_url(url: object) -> int:
    """Parse only the canonical allowlisted PokeAPI official-artwork URL."""
    if not isinstance(url, str):
        raise ValueError("poster subject image_url must be text")
    match = _OFFICIAL_ARTWORK_URL.fullmatch(url)
    if match is None:
        raise ValueError(
            "poster subject image_url must be a canonical PokeAPI "
            "official-artwork URL"
        )
    return int(match.group(1))


def poster_subject_from_card(card: dict[str, Any]) -> dict[str, Any]:
    """Derive an explicit poster subject from a transformed source card.

    Transformed cards normally carry their exact base/form official artwork in
    ``image_url``.  A missing unrelated card image remains compatible with the
    historic base-form behavior.  A malformed official-artwork URL is rejected
    rather than being converted into a different subject.
    """
    species_id = _positive_int(card.get("pokemon_id"), "pokemon_id")
    image_url = card.get("image_url")
    form_marker = card.get("prefix")
    requires_exact_form = (
        isinstance(form_marker, str)
        and form_marker.casefold() in {"mega", "primal", "[m]"}
    )
    if isinstance(image_url, str) and "official-artwork" in image_url:
        artwork_id = official_artwork_id_from_url(image_url)
        if requires_exact_form and artwork_id == species_id:
            raise ValueError(
                f"Pokemon #{species_id} requests the {form_marker} form "
                "without an exact official artwork URL"
            )
    elif isinstance(image_url, str) and image_url.startswith(
        "https://raw.githubusercontent.com/PokeAPI/sprites/"
    ):
        raise ValueError(
            f"Pokemon #{species_id} has a malformed official artwork URL"
        )
    else:
        if requires_exact_form:
            raise ValueError(
                f"Pokemon #{species_id} requests the {form_marker} form "
                "without an exact official artwork URL"
            )
        artwork_id = species_id
    return PosterSubject(species_id, artwork_id).as_mapping()


def resolve_poster_subject(item: dict[str, Any]) -> PosterSubject:
    """Resolve and strictly validate an explicit or legacy base subject."""
    species_id = _positive_int(item.get("pokemon_id"), "pokemon_id")
    value = item.get("poster_subject")
    if value is None:
        return PosterSubject(species_id, species_id)
    if not isinstance(value, dict):
        raise ValueError("poster_subject must be a mapping")

    source = value.get("source")
    if source != SOURCE:
        raise ValueError(
            f"Unsupported poster_subject.source {source!r}; expected {SOURCE!r}"
        )
    recorded_species = _positive_int(
        value.get("species_id"),
        "poster_subject.species_id",
    )
    if recorded_species != species_id:
        raise ValueError(
            "poster_subject.species_id must match the element pokemon_id"
        )
    artwork_id = _positive_int(
        value.get("official_artwork_id"),
        "poster_subject.official_artwork_id",
    )
    subject = PosterSubject(species_id, artwork_id, source)
    if value.get("subject_key") != subject.subject_key:
        raise ValueError(
            "poster_subject.subject_key does not match its official artwork ID"
        )
    parsed_artwork_id = official_artwork_id_from_url(value.get("image_url"))
    if parsed_artwork_id != artwork_id or value.get("image_url") != subject.image_url:
        raise ValueError(
            "poster_subject.image_url does not match its official artwork ID"
        )
    return subject


def subject_fingerprint_identity(
    item: dict[str, Any],
) -> int | dict[str, Any]:
    return resolve_poster_subject(item).fingerprint_identity()


def manifest_subject_fields(item: dict[str, Any]) -> dict[str, Any]:
    """Emit form metadata only when it adds information over legacy base IDs."""
    subject = resolve_poster_subject(item)
    if not subject.is_special_form:
        return {}
    return {"poster_subject": subject.as_mapping()}
