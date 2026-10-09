"""Procedural rope prop for the cut-rope boss arena.

A narrow hanging rope authored as a Prop with kind ``cut_rope_rope``.

The frame is a kit for a rope of any length (``column_tile``): a tie at the
top (the cap), one tile of braid that the game repeats, and a knot at the
bottom (the end). The game draws the cap at the top of the Prop's box, the
knot at its bottom, and the tile between them, so the rope is as long as the
box the map gives it. The LDtk hitbox is that box, so a player cannot cut a
part of the rope that is not drawn.

The braid has a period of ``PERIOD`` rows and the tile is two periods. The
cap and the end each keep one period of plain braid next to the tile, so the
rows on each side of a boundary are the same in the tile and outside it, also
in a reduced copy of the sheet. Each part is a multiple of ``PERIOD`` rows, so
each boundary is on a whole texel in the half, quarter and one-sixth copies.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageColor, ImageDraw

from ...authoring.sheet_build import build_sheet, write_canonical
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]

TARGET_NAME = "cut_rope_rope"
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]

# Rows of one turn of the braid. The strands and the bands repeat with it.
PERIOD = 12
# The rows of the tie at the top, of the tile, and of the knot at the bottom.
# The tie and the knot each take 20 rows; the rest of the cap and of the end
# is plain braid.
CAP_ROWS = 3 * PERIOD
TILE_ROWS = 2 * PERIOD
END_ROWS = 3 * PERIOD
# ``(first row, row after the last)`` of the tile.
COLUMN_TILE = (CAP_ROWS, CAP_ROWS + TILE_ROWS)

FRAME_SIZE = (48, CAP_ROWS + TILE_ROWS + END_ROWS)

ACTOR_METADATA = {
    "actor": {
        "character_id": "prop_cut_rope_rope",
        "display_name": "Cut-Rope Rope",
    },
    "body": {
        "body_plan": "Prop",
        "body_kind": "HangingRope",
        "mass_class": "Light",
        "locomotion_hint": "Stationary",
        "traits": ["prop", "rope", "cuttable"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
    },
    "sockets": {
        "top": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 24.0, "y": 2.0}},
        "bottom": {
            "source": f"{TARGET_NAME}.geometry",
            "point": {"x": 24.0, "y": float(FRAME_SIZE[1] - 2)},
        },
    },
    "tags": ["prop", "rope", "cuttable", "boss-arena"],
}

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 1, 1000),
]

SUPER = 4
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER

ROPE_DARK = ImageColor.getrgb("#5B3518") + (255,)
ROPE_MID = ImageColor.getrgb("#A66B2E") + (255,)
ROPE_LIGHT = ImageColor.getrgb("#E2B15E") + (255,)
ROPE_SHADOW = ImageColor.getrgb("#2B1A12") + (255,)


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _box(x1: float, y1: float, x2: float, y2: float) -> Tuple[int, int, int, int]:
    return (_s(x1), _s(y1), _s(x2), _s(y2))


def _rope_wave(y: float, strand: int) -> float:
    # Static braided silhouette. A deterministic triangular-ish wave reads as
    # rope twist without the DNA/dancing-flower motion the old idle row had.
    t = (y / PERIOD + strand * 0.33) % 1.0
    return (abs(t - 0.5) - 0.25) * 7.0


def _rope_band_wave(y: float) -> float:
    t = (y / PERIOD) % 1.0
    return (abs(t - 0.5) - 0.25) * 5.0


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    del frame_idx, nframes
    if anim != "idle":
        raise ValueError(f"unknown animation: {anim}")
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = blending_draw(img)

    cx = 24.0
    bottom = float(FRAME_SIZE[1])

    # Braided strands. Three strands and a band on each turn, so the line
    # reads as twisted rope at small scale. Each is drawn on a multiple of
    # 3 rows, which divides ``PERIOD``: the braid is the same picture each
    # ``PERIOD`` rows, and the tile joins the next copy of itself. No drop
    # shadow: this is the visible rope only.
    for strand, color, offset in [
        (0, ROPE_DARK, -3.4),
        (1, ROPE_MID, 0.0),
        (2, ROPE_LIGHT, 3.4),
    ]:
        pts = []
        for y in range(PERIOD, int(bottom) - 9, 3):
            wave = _rope_wave(y, strand)
            pts.append((_s(cx + offset + wave), _s(y)))
        draw.line(pts, fill=color, width=_s(2.2))

    for y in range(PERIOD + 2, int(bottom) - 8, PERIOD):
        wave = _rope_band_wave(y)
        draw.arc(
            _box(cx - 6 + wave, y - 4, cx + 6 + wave, y + 8),
            210,
            330,
            fill=ROPE_SHADOW,
            width=_s(1.0),
        )
        draw.arc(
            _box(cx - 6 - wave, y - 4, cx + 6 - wave, y + 8),
            30,
            150,
            fill=ROPE_LIGHT,
            width=_s(0.8),
        )

    # The cap: the tie that hangs the rope. A period of plain braid is between
    # it and the tile.
    draw.ellipse(_box(cx - 6, 1, cx + 6, 14), outline=ROPE_DARK, width=_s(3.0))
    draw.ellipse(_box(cx - 3.5, 4, cx + 3.5, 11), outline=ROPE_LIGHT, width=_s(1.1))
    draw.rectangle(_box(cx - 7, 13, cx + 7, 20), fill=ROPE_DARK)
    for x in (cx - 4.5, cx, cx + 4.5):
        draw.line((_s(x), _s(13), _s(x), _s(20)), fill=ROPE_LIGHT, width=_s(0.6))

    # The end: the knot that holds the load, a period of plain braid under
    # the tile.
    draw.rectangle(_box(cx - 7, bottom - 20, cx + 7, bottom - 13), fill=ROPE_DARK)
    for x in (cx - 4.5, cx, cx + 4.5):
        draw.line(
            (_s(x), _s(bottom - 20), _s(x), _s(bottom - 13)),
            fill=ROPE_LIGHT,
            width=_s(0.6),
        )
    draw.ellipse(
        _box(cx - 6, bottom - 14, cx + 6, bottom - 1), outline=ROPE_DARK, width=_s(3.0)
    )
    draw.ellipse(
        _box(cx - 3.5, bottom - 11, cx + 3.5, bottom - 4),
        outline=ROPE_LIGHT,
        width=_s(1.1),
    )

    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    del frame_idx, nframes
    return {
        "anchors": {
            "top": {"x": 24.0, "y": 2.0},
            "bottom": {"x": 24.0, "y": float(FRAME_SIZE[1] - 2)},
        },
        "prop": {"kind": TARGET_NAME, "animation": anim},
    }


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_draw_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=108,
        frame_meta_fn=_frame_meta,
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        column_tile=COLUMN_TILE,
    )
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ]


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        _draw_frame,
        Path(out_dir),
        frame_size=FRAME_SIZE,
        label_width=108,
    )
