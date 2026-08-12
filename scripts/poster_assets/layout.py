"""Shared poster page layout helpers."""
from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction


CARD_WIDTH_MM = 63.5
CARD_HEIGHT_MM = 88.9
GAP_X_MM = 5.0
GAP_Y_MM = 5.0
LATENT_ALIGNMENT_PX = 16
RASTER_GEOMETRY_CONTRACT_VERSION = 2


DEFAULT_LAYOUT_NAME = "standard_3x3"
LAYOUTS = {
    "standard_2x2": {
        "columns": 2,
        "rows": 2,
        "pdf_paper": "A4",
        "pdf_orientation": "portrait",
    },
    "standard_3x3": {
        "columns": 3,
        "rows": 3,
        "pdf_paper": "A4",
        "pdf_orientation": "portrait",
    },
    "wide_4x3": {
        "columns": 4,
        "rows": 3,
        "pdf_paper": "A3",
        "pdf_orientation": "landscape",
    },
    "wide_4x4": {
        "columns": 4,
        "rows": 4,
        "pdf_paper": "A3",
        "pdf_orientation": "portrait",
    },
}


@dataclass(frozen=True)
class Cell:
    row: int
    column: int
    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2

    def inset(self, x_ratio: float = 0.08, y_ratio: float = 0.08) -> tuple[int, int, int, int]:
        pad_x = int(self.width * x_ratio)
        pad_y = int(self.height * y_ratio)
        return (
            self.x + pad_x,
            self.y + pad_y,
            self.x + self.width - pad_x,
            self.y + self.height - pad_y,
        )


@dataclass(frozen=True)
class PageLayout:
    name: str
    columns: int
    rows: int
    width_px: int
    height_px: int
    column_spans: tuple[tuple[int, int], ...]
    row_spans: tuple[tuple[int, int], ...]

    @property
    def pokemon_count(self) -> int:
        return self.columns

    @staticmethod
    def _uniform_extent(
        spans: tuple[tuple[int, int], ...],
        description: str,
    ) -> int:
        extents = tuple(end - start for start, end in spans)
        if len(set(extents)) != 1:
            raise ValueError(
                f"{description} vary by rasterized cell: {extents}"
            )
        return extents[0]

    @property
    def card_widths_px(self) -> tuple[int, ...]:
        return tuple(end - start for start, end in self.column_spans)

    @property
    def card_heights_px(self) -> tuple[int, ...]:
        return tuple(end - start for start, end in self.row_spans)

    @property
    def gap_widths_px(self) -> tuple[int, ...]:
        return tuple(
            self.column_spans[index + 1][0] - self.column_spans[index][1]
            for index in range(len(self.column_spans) - 1)
        )

    @property
    def gap_heights_px(self) -> tuple[int, ...]:
        return tuple(
            self.row_spans[index + 1][0] - self.row_spans[index][1]
            for index in range(len(self.row_spans) - 1)
        )

    @property
    def card_width_px(self) -> int:
        """Return the card width when every rasterized column is uniform."""
        return self._uniform_extent(self.column_spans, "Card widths")

    @property
    def card_height_px(self) -> int:
        """Return the card height when every rasterized row is uniform."""
        return self._uniform_extent(self.row_spans, "Card heights")

    @property
    def gap_x_px(self) -> int:
        """Return the horizontal gap when every rasterized gap is uniform."""
        gaps = tuple(
            (start, end)
            for start, end in zip(
                (span[1] for span in self.column_spans[:-1]),
                (span[0] for span in self.column_spans[1:]),
                strict=True,
            )
        )
        return self._uniform_extent(gaps, "Horizontal gaps")

    @property
    def gap_y_px(self) -> int:
        """Return the vertical gap when every rasterized gap is uniform."""
        gaps = tuple(
            (start, end)
            for start, end in zip(
                (span[1] for span in self.row_spans[:-1]),
                (span[0] for span in self.row_spans[1:]),
                strict=True,
            )
        )
        return self._uniform_extent(gaps, "Vertical gaps")

    def cell(self, row: int, column: int) -> Cell:
        if row < 1 or row > self.rows:
            raise ValueError(f"row must be 1-{self.rows}, got {row}")
        if column < 1 or column > self.columns:
            raise ValueError(f"column must be 1-{self.columns}, got {column}")
        x, right = self.column_spans[column - 1]
        y, bottom = self.row_spans[row - 1]
        return Cell(
            row=row,
            column=column,
            x=x,
            y=y,
            width=right - x,
            height=bottom - y,
        )

    def bottom_row_cells(self) -> list[Cell]:
        return [self.cell(self.rows, column) for column in range(1, self.columns + 1)]


def resolve_layout_name(name: str | None) -> dict[str, int | str]:
    layout_name = name or DEFAULT_LAYOUT_NAME
    if layout_name not in LAYOUTS:
        raise ValueError(f"Unknown layout '{layout_name}'. Known layouts: {', '.join(sorted(LAYOUTS))}")
    return LAYOUTS[layout_name]


def default_text_cells(name: str | None) -> dict[str, dict[str, float | int]]:
    """Return deterministic title and information cells for a poster grid."""
    layout_name = name or DEFAULT_LAYOUT_NAME
    spec = resolve_layout_name(layout_name)
    if layout_name == "standard_2x2":
        title = {"row": 1, "column": 1}
        set_info = {"row": 1, "column": 2}
    else:
        center_column = max(1, (int(spec["columns"]) + 1) // 2)
        title = {"row": 1, "column": center_column}
        set_info = {
            "row": min(2, int(spec["rows"])),
            "column": center_column,
        }
    return {
        "title": title,
        "set_info": {
            **set_info,
            "max_width_ratio": 0.92,
            "max_height_ratio": 0.68,
        },
    }


def pdf_page_hint(name: str | None) -> tuple[str, str]:
    """Return the paper family for one continuous physical-grid print."""
    spec = resolve_layout_name(name)
    return str(spec["pdf_paper"]), str(spec["pdf_orientation"])


def _fraction(value: float) -> Fraction:
    """Preserve decimal physical measurements without binary float drift."""
    return Fraction(str(value))


def _physical_layout_size_fraction(
    name: str | None,
) -> tuple[Fraction, Fraction]:
    spec = resolve_layout_name(name)
    columns = int(spec["columns"])
    rows = int(spec["rows"])
    return (
        columns * _fraction(CARD_WIDTH_MM)
        + (columns - 1) * _fraction(GAP_X_MM),
        rows * _fraction(CARD_HEIGHT_MM)
        + (rows - 1) * _fraction(GAP_Y_MM),
    )


def physical_layout_size_mm(name: str | None) -> tuple[float, float]:
    """Return complete grid size, including binder gaps, in millimetres."""
    width, height = _physical_layout_size_fraction(name)
    return float(width), float(height)


def _rasterized_card_spans(
    count: int,
    card_mm: float,
    gap_mm: float,
    pixels_per_mm: Fraction,
) -> tuple[tuple[int, int], ...]:
    """Rasterize every card from cumulative physical endpoints.

    Independent card and gap rounding can accumulate beyond the real canvas.
    Mapping each cumulative millimetre position distributes sub-pixel rounding
    while guaranteeing that the last card ends exactly at the rasterized
    physical endpoint.
    """
    if count <= 0 or pixels_per_mm <= 0:
        raise ValueError("Rasterized layout dimensions must be positive")
    card = _fraction(card_mm)
    gap = _fraction(gap_mm)
    cursor = Fraction(0)
    spans: list[tuple[int, int]] = []
    for index in range(count):
        start = round(cursor * pixels_per_mm)
        cursor += card
        end = round(cursor * pixels_per_mm)
        if end <= start:
            raise ValueError(
                f"Raster scale is too small for {count} cards"
            )
        spans.append((start, end))
        if index < count - 1:
            cursor += gap
    extent_px = round(cursor * pixels_per_mm)
    if spans[0][0] != 0 or spans[-1][1] != extent_px:
        raise AssertionError("Cumulative rasterization lost a canvas endpoint")
    return tuple(spans)


def _normalized_card_spans(
    count: int,
    card_mm: float,
    gap_mm: float,
    extent_px: int,
) -> tuple[tuple[int, int], ...]:
    if extent_px <= 0:
        raise ValueError("Rasterized layout dimensions must be positive")
    total_mm = (
        count * _fraction(card_mm)
        + (count - 1) * _fraction(gap_mm)
    )
    return _rasterized_card_spans(
        count,
        card_mm,
        gap_mm,
        Fraction(extent_px, 1) / total_mm,
    )


def proportional_height_px(name: str | None, width_px: int) -> int:
    """Return the exact physical-ratio height for a rasterized page width."""
    if width_px <= 0:
        raise ValueError("Poster width must be positive")
    grid_width_mm, grid_height_mm = _physical_layout_size_fraction(name)
    return round(
        width_px * grid_height_mm / grid_width_mm
    )


def latent_canvas_dimensions(
    name: str | None,
    megapixels: float,
    *,
    alignment_px: int = LATENT_ALIGNMENT_PX,
) -> tuple[int, int]:
    """Return an independently aligned generation canvas at physical ratio."""
    if megapixels <= 0:
        raise ValueError("megapixels must be positive")
    if alignment_px <= 0:
        raise ValueError("alignment_px must be positive")
    width_mm, height_mm = _physical_layout_size_fraction(name)
    ratio = float(width_mm / height_mm)
    height = math.sqrt(megapixels * 1_000_000 / ratio)
    width = height * ratio

    def aligned(value: float) -> int:
        return max(
            alignment_px,
            round(value / alignment_px) * alignment_px,
        )

    return aligned(width), aligned(height)


def page_canvas_dimensions(
    name: str | None,
    megapixels: float,
) -> tuple[int, int]:
    """Return a width-aligned canvas normalized to the physical page ratio."""
    width_px, _latent_height = latent_canvas_dimensions(name, megapixels)
    return width_px, proportional_height_px(name, width_px)


def build_source_layout(
    name: str | None,
    *,
    width_px: int,
    height_px: int,
    aspect_tolerance_px: int | None = None,
) -> PageLayout:
    """Validate a real image canvas and rasterize cells to its exact edges."""
    if aspect_tolerance_px is None:
        if (
            width_px % LATENT_ALIGNMENT_PX == 0
            and height_px % LATENT_ALIGNMENT_PX == 0
        ):
            grid_width_mm, grid_height_mm = (
                _physical_layout_size_fraction(name)
            )
            # Width and height are independently rounded to the latent grid.
            # Express both half-step errors on the vertical axis.
            aspect_tolerance_px = (
                math.ceil(
                    Fraction(LATENT_ALIGNMENT_PX, 2)
                    * (
                        1
                        + grid_height_mm / grid_width_mm
                    )
                )
                + 1
            )
        else:
            aspect_tolerance_px = LATENT_ALIGNMENT_PX
    if aspect_tolerance_px < 0:
        raise ValueError("Aspect tolerance must not be negative")
    expected_height = proportional_height_px(name, width_px)
    if abs(expected_height - height_px) > aspect_tolerance_px:
        raise ValueError(
            "Poster canvas does not match card-layout aspect ratio: "
            f"{(width_px, height_px)} vs {(width_px, expected_height)}"
        )
    return build_page_layout(
        name,
        width_px=width_px,
        height_px=height_px,
    )


def build_image_layout(
    name: str | None,
    *,
    width_px: int,
    height_px: int,
    dpi: tuple[float, float] | None = None,
) -> PageLayout:
    """Rasterize a loaded image using exact print dpi when it is trustworthy."""
    if dpi is not None and len(dpi) == 2:
        dpi_x, dpi_y = float(dpi[0]), float(dpi[1])
        rounded_dpi = round((dpi_x + dpi_y) / 2)
        if (
            rounded_dpi > 0
            and abs(dpi_x - rounded_dpi) <= 0.1
            and abs(dpi_y - rounded_dpi) <= 0.1
        ):
            print_layout = build_print_layout(name, rounded_dpi)
            if (
                print_layout.width_px == width_px
                and print_layout.height_px == height_px
            ):
                return print_layout
    return build_source_layout(
        name,
        width_px=width_px,
        height_px=height_px,
    )


def build_print_layout(name: str | None, dpi: int = 300) -> PageLayout:
    """Build a layout whose physical grid is rendered at the requested dpi."""
    if dpi <= 0:
        raise ValueError("dpi must be positive")
    spec = resolve_layout_name(name)
    columns = int(spec["columns"])
    rows = int(spec["rows"])
    pixels_per_mm = Fraction(dpi, 1) / _fraction(25.4)
    column_spans = _rasterized_card_spans(
        columns,
        CARD_WIDTH_MM,
        GAP_X_MM,
        pixels_per_mm,
    )
    row_spans = _rasterized_card_spans(
        rows,
        CARD_HEIGHT_MM,
        GAP_Y_MM,
        pixels_per_mm,
    )
    return PageLayout(
        name=name or DEFAULT_LAYOUT_NAME,
        columns=columns,
        rows=rows,
        width_px=column_spans[-1][1],
        height_px=row_spans[-1][1],
        column_spans=column_spans,
        row_spans=row_spans,
    )


def build_generation_output_layout(
    name: str | None,
    generation: Mapping[str, object],
) -> PageLayout:
    """Return the exact raster expected from one generation output contract."""
    output_dpi = generation.get("output_dpi")
    if output_dpi is not None:
        if (
            not isinstance(output_dpi, int)
            or isinstance(output_dpi, bool)
            or output_dpi <= 0
        ):
            raise ValueError("Generation output_dpi must be a positive integer")
        return build_print_layout(name, output_dpi)

    output_megapixels = generation.get("output_megapixels")
    if (
        not isinstance(output_megapixels, (int, float))
        or isinstance(output_megapixels, bool)
        or output_megapixels <= 0
    ):
        raise ValueError(
            "Generation must define positive output_dpi or "
            "output_megapixels"
        )
    output_width, output_height = page_canvas_dimensions(
        name,
        float(output_megapixels),
    )
    return build_page_layout(
        name,
        width_px=output_width,
        height_px=output_height,
    )


def effective_dpi(layout: PageLayout) -> tuple[float, float]:
    """Return the horizontal and vertical pixel density of a page layout."""
    width_mm, height_mm = physical_layout_size_mm(layout.name)
    return (
        layout.width_px / (width_mm / 25.4),
        layout.height_px / (height_mm / 25.4),
    )


def build_page_layout(
    name: str | None,
    width_px: int = 1400,
    height_px: int | None = None,
) -> PageLayout:
    spec = resolve_layout_name(name)
    columns = int(spec["columns"])
    rows = int(spec["rows"])
    if width_px <= 0:
        raise ValueError("Poster width must be positive")
    if height_px is None:
        height_px = proportional_height_px(name, width_px)
    elif height_px <= 0:
        raise ValueError("Poster height must be positive")

    return PageLayout(
        name=name or DEFAULT_LAYOUT_NAME,
        columns=columns,
        rows=rows,
        width_px=width_px,
        height_px=height_px,
        column_spans=_normalized_card_spans(
            columns,
            CARD_WIDTH_MM,
            GAP_X_MM,
            width_px,
        ),
        row_spans=_normalized_card_spans(
            rows,
            CARD_HEIGHT_MM,
            GAP_Y_MM,
            height_px,
        ),
    )
