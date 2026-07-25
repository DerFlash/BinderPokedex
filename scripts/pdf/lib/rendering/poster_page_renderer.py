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
from scripts.poster_assets.render_poster import load_yaml  # noqa: E402
from scripts.poster_assets.slice_poster import slice_poster  # noqa: E402


class PosterPageRenderer:
    """Prepare and draw an optional scope poster page."""

    def __init__(
        self, scope: str, language: str, artwork_path: Path, insertion: str
    ):
        self.scope = scope
        self.language = language
        self.artwork_path = artwork_path
        self.insertion = insertion
        temp_root = PROJECT_ROOT / "tmp" / "pdfs"
        temp_root.mkdir(parents=True, exist_ok=True)
        self._temp_dir = tempfile.TemporaryDirectory(
            prefix=f"poster-{scope.lower()}-{language}-", dir=temp_root
        )
        self._card_paths: list[Path] | None = None

    @classmethod
    def from_variant_data(
        cls, variant_data: dict, language: str
    ) -> "PosterPageRenderer | None":
        scope = variant_data.get("set_id") or variant_data.get("scope")
        if not scope:
            return None
        scope_dir = POSTER_ASSETS / str(scope)
        manifest_path = scope_dir / "poster.yaml"
        if not manifest_path.is_file():
            return None
        manifest = load_yaml(manifest_path)
        pdf_config = manifest.get("pdf", {})
        if not pdf_config.get("enabled", False):
            return None
        insertion = pdf_config.get("insertion", "after_first_section_cover")
        if insertion != "after_first_section_cover":
            raise ValueError(f"Unsupported poster PDF insertion: {insertion}")
        artwork_path = scope_dir / pdf_config.get(
            "artwork_file", "poster-flux2-artwork.png"
        )
        if not artwork_path.is_file():
            raise FileNotFoundError(f"Poster PDF artwork not found: {artwork_path}")
        return cls(str(scope), language, artwork_path, insertion)

    def _prepare_cards(self) -> list[Path]:
        if self._card_paths is not None:
            return self._card_paths
        temp_dir = Path(self._temp_dir.name)
        localized_poster = temp_dir / f"{self.scope.lower()}_{self.language}.png"
        finalize(self.scope, self.artwork_path, localized_poster, self.language)
        self._card_paths = slice_poster(
            self.scope, localized_poster, temp_dir / "cards"
        )
        return self._card_paths

    def render_page(self, canvas_obj, page_renderer: PageRenderer) -> None:
        card_paths = self._prepare_cards()
        expected = page_renderer.style.CARDS_PER_PAGE
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
        self._temp_dir.cleanup()
