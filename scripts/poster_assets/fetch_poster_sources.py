#!/usr/bin/env python3
"""Fetch reproducible poster inputs that are intentionally not versioned."""
from __future__ import annotations

import argparse
import sys

try:
    from .fetch_cutouts import fetch_cutouts
    from .fetch_title_logos import fetch_title_logos
    from .poster_io import POSTER_ASSETS, poster_bundle
    from .validate_promoted_poster import enabled_poster_bundles
except ImportError:  # Direct script execution
    from fetch_cutouts import fetch_cutouts
    from fetch_title_logos import fetch_title_logos
    from poster_io import POSTER_ASSETS, poster_bundle
    from validate_promoted_poster import enabled_poster_bundles


def fetch_sources(
    asset_keys: list[str],
    *,
    kind: str = "all",
    force: bool = False,
) -> int:
    """Populate each bundle's ignored source cache from configured URLs."""
    for asset_key in asset_keys:
        bundle = poster_bundle(asset_key, poster_assets=POSTER_ASSETS)
        print(f"\nPoster sources: {bundle.asset_key}")
        if kind in {"all", "cutouts"}:
            fetch_cutouts(bundle.asset_key, force=force)
        if kind in {"all", "logos"} and bundle.manifest.get("title_logo"):
            fetch_title_logos(bundle.asset_key, force=force)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--scope",
        action="append",
        dest="scopes",
        help="Poster asset key; may be repeated",
    )
    target.add_argument(
        "--all-enabled",
        action="store_true",
        help="Fetch sources for every PDF-enabled poster bundle",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Redownload existing cached sources",
    )
    parser.add_argument(
        "--kind",
        choices=("all", "cutouts", "logos"),
        default="all",
        help="Source class to fetch (default: all)",
    )
    args = parser.parse_args()
    asset_keys = (
        [bundle.asset_key for bundle in enabled_poster_bundles()]
        if args.all_enabled
        else list(args.scopes or [])
    )
    try:
        return fetch_sources(asset_keys, kind=args.kind, force=args.force)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
