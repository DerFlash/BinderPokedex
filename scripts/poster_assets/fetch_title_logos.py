#!/usr/bin/env python3
"""Fetch deterministic, language-specific title logos for a poster scope."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

from PIL import Image

try:
    from .fetch_cutouts import download_bytes
    from .poster_io import POSTER_ASSETS, load_poster_scope_data, poster_bundle
except ImportError:
    from fetch_cutouts import download_bytes
    from poster_io import POSTER_ASSETS, load_poster_scope_data, poster_bundle


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "data" / "output"


def resolve_logo_downloads(
    manifest: dict[str, Any],
    scope_data: dict[str, Any],
) -> list[tuple[str, str, str]]:
    """Return ``(language, relative file, URL)`` logo downloads."""
    config = manifest.get("title_logo", {})
    files = config.get("files")
    explicit_sources = config.get("sources", {})
    scope_sources = scope_data.get("logo_urls", {})

    if isinstance(files, dict):
        downloads = []
        for language, relative_file in files.items():
            url = (
                explicit_sources.get(language)
                if isinstance(explicit_sources, dict)
                else None
            ) or scope_sources.get(language)
            if not relative_file or not url:
                raise ValueError(
                    f"Missing title-logo file or URL for language '{language}'"
                )
            downloads.append((language, str(relative_file), str(url)))
        return downloads

    relative_file = config.get("file")
    if not relative_file:
        return []
    url = config.get("source") or scope_sources.get("en") or next(
        (value for value in scope_sources.values() if value),
        None,
    )
    if not url:
        raise ValueError("No title-logo source URL is configured")
    return [("default", str(relative_file), str(url))]


def fetch_title_logos(scope: str, force: bool = False) -> list[Path]:
    """Download and normalize every configured title logo to RGBA PNG."""
    bundle = poster_bundle(scope, poster_assets=POSTER_ASSETS)
    scope_dir = bundle.asset_dir
    manifest_path = bundle.manifest_path
    manifest = bundle.manifest
    scope_data = load_poster_scope_data(
        bundle,
        scope_data_dir=OUTPUT_DIR,
    )
    downloads = resolve_logo_downloads(manifest, scope_data)
    if not downloads:
        raise ValueError(f"No title logos configured in {manifest_path}")

    written = []
    scope_root = scope_dir.resolve()
    for language, relative_file, url in downloads:
        destination = (scope_dir / relative_file).resolve()
        if not destination.is_relative_to(scope_root):
            raise ValueError(
                f"Title-logo destination escapes the scope directory: "
                f"{relative_file}"
            )
        if destination.exists() and not force:
            print(f"  - {language}: exists ({destination.name})")
            written.append(destination)
            continue

        parsed = urlparse(url)
        if parsed.scheme in {"http", "https"}:
            print(f"  - {language}: downloading {url}")
            try:
                image_bytes = download_bytes(url)
            except (HTTPError, URLError, TimeoutError) as exc:
                raise RuntimeError(f"Failed to download {url}: {exc}") from exc
        elif not parsed.scheme:
            source = (ROOT / url).resolve()
            if not source.is_relative_to(ROOT.resolve()):
                raise ValueError(f"Title-logo source escapes the repository: {url}")
            if not source.is_file():
                raise FileNotFoundError(f"Local title-logo source does not exist: {url}")
            print(f"  - {language}: copying {url}")
            image_bytes = source.read_bytes()
        else:
            raise ValueError(f"Unsupported title-logo source: {url}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp.png")
        temporary.write_bytes(image_bytes)
        with Image.open(temporary) as image:
            if image.width < 32 or image.height < 16:
                raise ValueError(
                    f"Title logo is unexpectedly small: {image.size}"
                )
            image.convert("RGBA").save(destination, format="PNG", optimize=True)
        temporary.unlink(missing_ok=True)
        written.append(destination)

    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        for path in fetch_title_logos(args.scope, args.force):
            print(path)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
