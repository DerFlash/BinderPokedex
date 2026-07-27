#!/usr/bin/env python3
"""Update README release pointers from a published release manifest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


LANGUAGE_LINKS_EN = [
    ("de", "🇩🇪", "Deutsch"),
    ("en", "🇬🇧", "English"),
    ("fr", "🇫🇷", "Français"),
    ("es", "🇪🇸", "Español"),
    ("it", "🇮🇹", "Italiano"),
    ("ja", "🇯🇵", "日本語"),
    ("ko", "🇰🇷", "한국어"),
    ("zh_hans", "🇨🇳", "简体中文"),
    ("zh_hant", "🇹🇼", "繁體中文"),
]

LANGUAGE_LINKS_DE = [
    ("de", "🇩🇪", "DE"),
    ("en", "🇬🇧", "EN"),
    ("fr", "🇫🇷", "FR"),
    ("es", "🇪🇸", "ES"),
    ("it", "🇮🇹", "IT"),
    ("ja", "🇯🇵", "JA"),
    ("ko", "🇰🇷", "KO"),
    ("zh_hans", "🇨🇳", "ZH"),
    ("zh_hant", "🇹🇼", "ZH-T"),
]


def read_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def replace_one(text: str, pattern: str, replacement: str, path: Path) -> str:
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"Expected exactly one match for {pattern!r} in {path}")
    return new_text


def upsert_release_note(
    text: str, path: Path, markdown_language: str, manifest: dict[str, Any]
) -> str:
    """Insert the current release note once, preserving older release notes."""
    tag = re.escape(manifest["tag"])
    section_title = "What's New" if markdown_language == "en" else "Was ist neu"
    if re.search(rf"^### {tag} \(", text, flags=re.MULTILINE):
        return text
    return replace_one(
        text,
        rf"## 📝 {re.escape(section_title)}\n\n",
        f"## 📝 {section_title}\n\n" + release_note(markdown_language, manifest) + "\n\n",
        path,
    )


def release_url(manifest: dict[str, Any], explicit_url: str | None) -> str:
    if explicit_url:
        return explicit_url
    tag = manifest["tag"]
    return f"https://github.com/DerFlash/BinderPokedex/releases/tag/{tag}"


def download_url(tag: str, asset: str) -> str:
    return f"https://github.com/DerFlash/BinderPokedex/releases/download/{tag}/{asset}"


def language_links(tag: str, links: list[tuple[str, str, str]], separator: str) -> str:
    parts = []
    for language, flag, label in links:
        asset = f"binder-pokedex-{language}.zip"
        parts.append(f"{flag} [{label}]({download_url(tag, asset)})")
    return separator.join(parts)


def release_note(markdown_language: str, manifest: dict[str, Any]) -> str:
    notes = manifest.get("release_notes", {}).get("whats_new", {}).get(markdown_language, {})
    title = notes.get("title", manifest["tag"])
    body = notes.get("body", [])
    month = "July 2026" if markdown_language == "en" else "Juli 2026"
    heading = f"### {manifest['tag']} ({month})\n\n**{title}** 🎴"
    if body:
        heading += "\n\n" + "\n".join(f"- {item}" for item in body)
    return heading


def summary(markdown_language: str, manifest: dict[str, Any]) -> str:
    fallback = manifest["tag"]
    return manifest.get("release_notes", {}).get("summary", {}).get(markdown_language, fallback)


def update_readme_en(path: Path, manifest: dict[str, Any], explicit_url: str | None) -> None:
    tag = manifest["tag"]
    pdf_count = manifest["pdfs"]["total"]
    scope_count = manifest["scope_count"]
    mega_scopes = ", ".join(manifest["scope_groups"]["mega"])
    sv_count = len(manifest["scope_groups"]["scarlet_violet"])
    text = path.read_text(encoding="utf-8")

    text = replace_one(text, r"!\[v[^\]]+\]\(https://img\.shields\.io/badge/version-v[^)]+-green\.svg\)", f"![{tag}](https://img.shields.io/badge/version-{tag}-green.svg)", path)
    text = replace_one(text, r"  - \*\*\d+ (?:Modern|Scarlet & Violet) Sets:\*\* Full Scarlet & Violet era \(SV01-SV10 \+ specials\)", f"  - **{sv_count} Scarlet & Violet Sets:** Full Scarlet & Violet era (SV01-SV10 + specials)", path)
    text = replace_one(text, r"  - \*\*(?:Paldea|Mega Evolution) Era:\*\* .+", f"  - **Mega Evolution Era:** {mega_scopes}", path)
    text = replace_one(text, r"- \*\*Scope-Based System\*\* with \d+ total scopes", f"- **Scope-Based System** with {scope_count} total scopes", path)
    text = replace_one(
        text,
        r"\*\*Latest \(v[^)]+\):\*\* \[All \d+ PDFs\]\([^)]+\) ✨ \*New: [^*]+\*",
        f"**Latest ({tag}):** [All {pdf_count} PDFs]({release_url(manifest, explicit_url)}) ✨ *New: {summary('en', manifest)}!*",
        path,
    )
    text = replace_one(
        text,
        r"\*\*By Language \(v[^)]+\):\*\*\n(?:.+\n){8}.+",
        f"**By Language ({tag}):**\n{language_links(tag, LANGUAGE_LINKS_EN, ' |\n')}",
        path,
    )
    text = upsert_release_note(text, path, "en", manifest)
    text = replace_one(
        text,
        r"# List available scopes \(\d+ total: 1 Pokedex \+ 3 ExGen \+ \d+ TCG sets\)",
        f"# List available scopes ({scope_count} total: 1 Pokedex + 3 ExGen + {scope_count - 4} TCG sets)",
        path,
    )

    path.write_text(text, encoding="utf-8")


def update_readme_de(path: Path, manifest: dict[str, Any], explicit_url: str | None) -> None:
    tag = manifest["tag"]
    pdf_count = manifest["pdfs"]["total"]
    scope_count = manifest["scope_count"]
    mega_scopes = ", ".join(manifest["scope_groups"]["mega"])
    sv_count = len(manifest["scope_groups"]["scarlet_violet"])
    text = path.read_text(encoding="utf-8")

    text = replace_one(text, r"!\[v[^\]]+\]\(https://img\.shields\.io/badge/Version-v[^)]+-green\.svg\)", f"![{tag}](https://img.shields.io/badge/Version-{tag}-green.svg)", path)
    text = replace_one(text, r"  - \*\*\d+ (?:Moderne Sets|Karmesin-&-Purpur-Sets):\*\* Komplette Karmesin & Purpur-Ära \(SV01-SV10 \+ Spezial-Sets\)", f"  - **{sv_count} Karmesin-&-Purpur-Sets:** Komplette Karmesin & Purpur-Ära (SV01-SV10 + Spezial-Sets)", path)
    text = replace_one(text, r"  - \*\*(?:Paldea-Ära|Mega-Evolution-Ära):\*\* .+", f"  - **Mega-Evolution-Ära:** {mega_scopes}", path)
    text = replace_one(text, r"- \*\*Scope-basiertes System\*\* mit \d+ Scopes insgesamt", f"- **Scope-basiertes System** mit {scope_count} Scopes insgesamt", path)
    text = replace_one(
        text,
        r"\*\*Aktuelle Version \(v[^)]+\):\*\* \[Alle \d+ PDFs\]\([^)]+\) ✨ \*Neu: [^*]+\*",
        f"**Aktuelle Version ({tag}):** [Alle {pdf_count} PDFs]({release_url(manifest, explicit_url)}) ✨ *Neu: {summary('de', manifest)}!*",
        path,
    )
    text = replace_one(
        text,
        r"\*\*Nach Sprache \(v[^)]+\):\*\* .+",
        f"**Nach Sprache ({tag}):** {language_links(tag, LANGUAGE_LINKS_DE, ' | ')}",
        path,
    )
    text = upsert_release_note(text, path, "de", manifest)
    text = replace_one(
        text,
        r"# Verfügbare Scopes anzeigen \(\d+ gesamt: 1 Pokedex \+ 3 ExGen \+ \d+ TCG Sets\)",
        f"# Verfügbare Scopes anzeigen ({scope_count} gesamt: 1 Pokedex + 3 ExGen + {scope_count - 4} TCG Sets)",
        path,
    )

    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--release-url", default=None)
    parser.add_argument("--project-dir", default=".")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    manifest = read_manifest(Path(args.manifest))
    update_readme_en(project_dir / "README.md", manifest, args.release_url)
    update_readme_de(project_dir / "README.de.md", manifest, args.release_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
