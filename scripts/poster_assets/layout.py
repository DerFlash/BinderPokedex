"""Shared poster page layout helpers."""
from __future__ import annotations

from dataclasses import dataclass


CARD_WIDTH_MM = 63.5
CARD_HEIGHT_MM = 88.9
GAP_X_MM = 5.0
GAP_Y_MM = 5.0


DEFAULT_LAYOUT_NAME = "standard_3x3"
LAYOUTS = {
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
    card_width_px: int
    card_height_px: int
    gap_x_px: int
    gap_y_px: int

    @property
    def pokemon_count(self) -> int:
        return self.columns

    def cell(self, row: int, column: int) -> Cell:
        if row < 1 or row > self.rows:
            raise ValueError(f"row must be 1-{self.rows}, got {row}")
        if column < 1 or column > self.columns:
            raise ValueError(f"column must be 1-{self.columns}, got {column}")
        x = (column - 1) * (self.card_width_px + self.gap_x_px)
        y = (row - 1) * (self.card_height_px + self.gap_y_px)
        return Cell(
            row=row,
            column=column,
            x=x,
            y=y,
            width=self.card_width_px,
            height=self.card_height_px,
        )

    def bottom_row_cells(self) -> list[Cell]:
        return [self.cell(self.rows, column) for column in range(1, self.columns + 1)]


def resolve_layout_name(name: str | None) -> dict[str, int | str]:
    layout_name = name or DEFAULT_LAYOUT_NAME
    if layout_name not in LAYOUTS:
        raise ValueError(f"Unknown layout '{layout_name}'. Known layouts: {', '.join(sorted(LAYOUTS))}")
    return LAYOUTS[layout_name]


def pdf_page_hint(name: str | None) -> tuple[str, str]:
    """Return the physical page family intended for a future matching renderer."""
    spec = resolve_layout_name(name)
    return str(spec["pdf_paper"]), str(spec["pdf_orientation"])


def physical_layout_size_mm(name: str | None) -> tuple[float, float]:
    """Return complete grid size, including binder gaps, in millimetres."""
    spec = resolve_layout_name(name)
    columns = int(spec["columns"])
    rows = int(spec["rows"])
    return (
        columns * CARD_WIDTH_MM + (columns - 1) * GAP_X_MM,
        rows * CARD_HEIGHT_MM + (rows - 1) * GAP_Y_MM,
    )


def build_print_layout(name: str | None, dpi: int = 300) -> PageLayout:
    """Build a layout whose physical grid is rendered at the requested dpi."""
    if dpi <= 0:
        raise ValueError("dpi must be positive")
    width_mm, _height_mm = physical_layout_size_mm(name)
    width_px = round(width_mm / 25.4 * dpi)
    return build_page_layout(name, width_px=width_px)


def effective_dpi(layout: PageLayout) -> tuple[float, float]:
    """Return the horizontal and vertical pixel density of a page layout."""
    width_mm, height_mm = physical_layout_size_mm(layout.name)
    return (
        layout.width_px / (width_mm / 25.4),
        layout.height_px / (height_mm / 25.4),
    )


def build_page_layout(name: str | None, width_px: int = 1400) -> PageLayout:
    spec = resolve_layout_name(name)
    columns = int(spec["columns"])
    rows = int(spec["rows"])

    grid_width_mm, grid_height_mm = physical_layout_size_mm(name)
    height_px = round(width_px * grid_height_mm / grid_width_mm)
    px_per_mm = width_px / grid_width_mm

    return PageLayout(
        name=name or DEFAULT_LAYOUT_NAME,
        columns=columns,
        rows=rows,
        width_px=width_px,
        height_px=height_px,
        card_width_px=round(CARD_WIDTH_MM * px_per_mm),
        card_height_px=round(CARD_HEIGHT_MM * px_per_mm),
        gap_x_px=round(GAP_X_MM * px_per_mm),
        gap_y_px=round(GAP_Y_MM * px_per_mm),
    )
