"""Render a localized poster artwork as one physical image per binder card."""
from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

from reportlab.lib.utils import ImageReader

from .page_renderer import PageRenderer


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[4]
POSTER_ASSETS = PROJECT_ROOT / "data" / "poster_assets"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.poster_assets.finalize_comfyui_poster import finalize  # noqa: E402
from scripts.poster_assets.layout import (  # noqa: E402
    DEFAULT_LAYOUT_NAME,
    pdf_page_hint,
    resolve_layout_name,
)
from scripts.poster_assets.poster_io import (  # noqa: E402
    PosterBundle,
    poster_asset_slug,
    poster_bundles_for_scope,
    select_poster_scope_data,
)
from scripts.poster_assets.slice_poster import slice_poster  # noqa: E402


class PosterPageRenderer:
    """Prepare and draw an optional scope poster page."""

    def __init__(
        self,
        bundle: PosterBundle,
        language: str,
        artwork_path: Path,
        layout_name: str = DEFAULT_LAYOUT_NAME,
    ):
        self.bundle = bundle
        self.scope = bundle.asset_key
        self.section_id = bundle.section_id
        self.poster_id = bundle.poster_id
        self.language = language
        self.artwork_path = artwork_path
        self.insertion = bundle.insertion
        self.layout_name = layout_name
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None
        self._card_paths: list[Path] | None = None

    @classmethod
    def from_variant_data(
        cls,
        variant_data: dict,
        language: str,
        *,
        include_poster: bool = True,
    ) -> "PosterPageRenderer | None":
        if not include_poster:
            return None
        scope = variant_data.get("set_id") or variant_data.get("scope")
        if not scope:
            return None
        collection = PosterPageCollection.from_scope(
            str(scope),
            variant_data,
            language,
            include_poster=include_poster,
        )
        if len(collection.renderers) > 1:
            collection.cleanup()
            raise ValueError(
                "from_variant_data() cannot return multiple poster renderers; "
                "use PosterPageCollection.from_scope()"
            )
        return collection.renderers[0] if collection.renderers else None

    @classmethod
    def from_bundle(
        cls,
        bundle: PosterBundle,
        language: str,
    ) -> "PosterPageRenderer":
        artwork_path = bundle.asset_dir / bundle.artwork_file
        if not artwork_path.is_file():
            raise FileNotFoundError(f"Poster PDF artwork not found: {artwork_path}")
        layout_name = bundle.manifest.get("layout", {}).get(
            "name",
            DEFAULT_LAYOUT_NAME,
        )
        resolve_layout_name(layout_name)
        return cls(bundle, language, artwork_path, layout_name)

    def _prepare_cards(self) -> list[Path]:
        if self._card_paths is not None:
            return self._card_paths
        if self._temp_dir is None:
            temp_root = PROJECT_ROOT / "tmp" / "pdfs"
            temp_root.mkdir(parents=True, exist_ok=True)
            self._temp_dir = tempfile.TemporaryDirectory(
                prefix=(
                    f"poster-{poster_asset_slug(self.scope)}-"
                    f"{self.language}-"
                ),
                dir=temp_root,
            )
        temp_dir = Path(self._temp_dir.name)
        localized_poster = (
            temp_dir
            / f"{poster_asset_slug(self.scope)}_{self.language}.png"
        )
        finalize(self.scope, self.artwork_path, localized_poster, self.language)
        self._card_paths = slice_poster(
            self.scope, localized_poster, temp_dir / "cards"
        )
        return self._card_paths

    def render_page(self, canvas_obj, page_renderer: PageRenderer) -> None:
        card_paths = self._prepare_cards()
        layout = resolve_layout_name(self.layout_name)
        poster_grid = (int(layout["columns"]), int(layout["rows"]))
        page_grid = (
            int(page_renderer.style.CARDS_PER_ROW),
            int(page_renderer.style.CARDS_PER_COLUMN),
        )
        if poster_grid != page_grid:
            paper, orientation = pdf_page_hint(self.layout_name)
            raise ValueError(
                f"Poster layout {self.layout_name} needs a "
                f"{poster_grid[0]}x{poster_grid[1]} PDF page renderer; current "
                f"renderer is {page_grid[0]}x{page_grid[1]}. A matching "
                f"{paper} {orientation} renderer is the intended extension."
            )
        expected = poster_grid[0] * poster_grid[1]
        if len(card_paths) != expected:
            raise ValueError(
                f"Poster layout produced {len(card_paths)} cards, PDF page expects {expected}"
            )
        page_renderer.create_page(canvas_obj)
        for index, card_path in enumerate(card_paths):
            x, y = page_renderer.calculate_card_position(index)
            canvas_obj.drawImage(
                ImageReader(str(card_path)),
                x,
                y,
                width=page_renderer.style.CARD_WIDTH,
                height=page_renderer.style.CARD_HEIGHT,
                preserveAspectRatio=False,
                mask="auto",
            )
        page_renderer.draw_cutting_guides(canvas_obj)

    def cleanup(self) -> None:
        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None
        self._card_paths = None


class PosterPageCollection:
    """Own and route every enabled poster page for one PDF scope."""

    def __init__(self, renderers: list[PosterPageRenderer] | None = None):
        self.renderers = renderers or []

    @classmethod
    def from_scope(
        cls,
        scope: str | None,
        variant_data: dict,
        language: str,
        *,
        include_poster: bool = True,
    ) -> "PosterPageCollection":
        if not include_poster or not scope:
            return cls()
        bundles = poster_bundles_for_scope(
            str(scope),
            poster_assets=POSTER_ASSETS,
        )
        renderers: list[PosterPageRenderer] = []
        try:
            for bundle in bundles:
                # Validate every binding against the complete source data even
                # while disabled; --skip-poster intentionally bypasses this.
                select_poster_scope_data(
                    bundle,
                    variant_data,
                    source_name=f"PDF scope {scope}",
                )
                if bundle.pdf_enabled:
                    renderers.append(
                        PosterPageRenderer.from_bundle(bundle, language)
                    )
        except Exception:
            for renderer in renderers:
                renderer.cleanup()
            raise
        return cls(renderers)

    def for_section(
        self,
        section_id: str | None,
        section_index: int,
    ) -> list[PosterPageRenderer]:
        """Return configured pages in routing order for the rendered section."""
        return [
            renderer
            for renderer in self.renderers
            if (
                renderer.insertion == "after_first_section_cover"
                and section_index == 0
            )
            or (
                renderer.insertion == "after_section_cover"
                and renderer.section_id == section_id
            )
        ]

    def cleanup(self) -> None:
        for renderer in self.renderers:
            renderer.cleanup()
