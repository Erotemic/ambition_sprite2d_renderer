"""Procedural interdimensional portal / gate sprite sheets.

This target intentionally evokes a monumental sci-fi portal ring while staying
well clear of an exact screen-used reproduction. The ring is old bronze, and
carries the inscription "ΛΕΓΑΛΛΥ ΔΙΣΤΙΝΧΤ" in the gate's fifteen glyphs
(``glyphs.legally_distinct``: each chevron its own symbol), cut into dark
plaques and lit a faint cyan. The ring's bottom slice sinks into a stepped
base (the way in), so the plaques run round the rest of it: clockwise from
the lower left over the top to the lower right, reading LEGALLY DISTINCT left
to right, Δ at 12 o'clock. Each glyph's foot faces the centre: its baseline
is square to the ray from the centre through it.

Three sheets of one assembly, on one canvas:

- ``_ring``: the ring on its base (``idle``; ``charge``, a pulse running
  round the plaques from the first to the last as a link opens, the lamps
  locking one by one; the band does not turn, the base holds it);
- ``_portal``: the wormhole membrane, layered over the ring while a link is
  open;
- ``_glyphs``: ``idle``, nothing lit; ``lit``, one frame per chevron, that glyph alone blazing on
  its plaque where the ring draws it. Laid over the ring, frame k lights
  chevron k as it is dialed.

And two pictures. ``_glyph_icons.png``: the fifteen glyphs in a row, white,
upright, each centred in its own ``GLYPH_ICON``-pixel cell, for a terminal's
dial wheel to tint. ``_tunnel.png``: the inside of the wormhole for the Ultra
layer over the membrane (``gate_portal_fx.wgsl``), which streams it down a
twisting tunnel. It tiles both ways: across it is the way round the tunnel,
down it the way in. Stars drawn as streaks along the way in, and a nebula of
the membrane's blues with a little violet.
"""


from __future__ import annotations

import functools
import math
from pathlib import Path
from typing import List, Sequence, Tuple

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFilter

from ...authoring.sheet_build import alpha_bbox_metrics, build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw
from ambition_sprite2d_renderer.glyphs.legally_distinct import ARCH_GAP_DEG, GLYPHS, Placement, arch_angle, glyphs_mask

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "interdimensional_gate"
RING_TARGET = f"{TARGET_NAME}_ring"
PORTAL_TARGET = f"{TARGET_NAME}_portal"
GLYPHS_TARGET = f"{TARGET_NAME}_glyphs"

RING_ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 140),
    ("charge", 30, 34),
]
PORTAL_ROWS: List[Tuple[str, int, int]] = [
    ("opening", 8, 80),
    ("stable", 8, 110),
    ("closing", 8, 80),
    # A body goes in, and a body comes out (Jon, 2026-10-19: "some sort of
    # ripple in the gate showing they moved through it"). Each starts and
    # ends on the stable surface, so either can cut in from ``stable``.
    ("swallow", 12, 55),
    ("emit", 12, 55),
]

# `idle` is the sheet at rest, nothing lit (a sheet's loader wants one).
# `bit` and `used`: one frame per cell of each chevron's position grid
# (chevron * 16 + row * 4 + column): a set bit ablaze, a used row's clear bit
# dim. Row k is the chevron's k-th use in the address, the columns the bits
# of its place, most significant first (Jon, 2026-10-24): the lit ring spells
# the whole address.
GRID_ROWS, GRID_COLS = 4, 4
GRID_CELLS = GRID_ROWS * GRID_COLS
GLYPH_ROWS: List[Tuple[str, int, int]] = [
    ("idle", 1, 100),
    ("lit", len(GLYPHS), 100),
    ("bit", len(GLYPHS) * GRID_CELLS, 100),
    ("used", len(GLYPHS) * GRID_CELLS, 100),
]

SHEET_FILES = [
    f"{RING_TARGET}_spritesheet.png",
    f"{RING_TARGET}_spritesheet.yaml",
    f"{PORTAL_TARGET}_spritesheet.png",
    f"{PORTAL_TARGET}_spritesheet.yaml",
    f"{GLYPHS_TARGET}_spritesheet.png",
    f"{GLYPHS_TARGET}_spritesheet.yaml",
    f"{TARGET_NAME}_tunnel.png",
    f"{TARGET_NAME}_glyph_icons.png",
]

GLYPH_ICON = 96

TUNNEL_SIZE = 256

# Use a larger canvas than the default character sheets so the gate has more
# room for legible inscription detail and cleaner anti-aliased edges.
FRAME_SIZE = (192, 192)
SUPER = 4
#: The sheets' frame: twice the design units, so the 288 world-unit ring
#: (Jon, 2026-10-24: a bigger gate, to read the position grids) keeps its
#: detail (`FRAME_SIZE` is the units the geometry is drawn in).
OUT_SIZE = (FRAME_SIZE[0] * 2, FRAME_SIZE[1] * 2)
CENTER = (FRAME_SIZE[0] * SUPER / 2.0, FRAME_SIZE[1] * SUPER / 2.0)
OUTER_R = 69.0 * SUPER
INNER_R = 45.0 * SUPER
PORTAL_R = 39.5 * SUPER
RING_MID_R = (INNER_R + OUTER_R) / 2.0
#: The bottom slice of the ring the base hides: no plaque there.
BASE_GAP_DEG = ARCH_GAP_DEG
#: A plaque about its centre on the band's middle, foot down (y down: toward
#: the aperture): a tall pentagon pointing at the aperture, and its dark face
#: where the glyph is cut (the inner half) and the position grid sits (the
#: outer half), and where a dialed glyph's light washes.
PLAQUE_OUTER = [(x * SUPER, y * SUPER) for x, y in ((-7.4, -10.2), (7.4, -10.2), (8.6, 3.6), (0.0, 10.6), (-8.6, 3.6))]
PLAQUE_FACE = [(x * SUPER, y * SUPER) for x, y in ((-6.0, -8.9), (6.0, -8.9), (7.0, 3.0), (0.0, 8.8), (-7.0, 3.0))]
#: A glyph's cap height, and how far its centre sits inward of the band's
#: middle.
GLYPH_CAP = 5.8 * SUPER
GLYPH_INSET = 3.6 * SUPER
#: The position grid on the plaque's outer half: its centre (plaque y), the
#: pitch of its cells and the radius of a cell's socket and light.
GRID_Y = -4.3 * SUPER
GRID_PITCH = 2.15 * SUPER
GRID_DOT = 0.85 * SUPER

# The palette of the concept (Jon, 2026-10-24): old bronze, cyan light.
BRONZE = "#7a5b3a"
BRONZE_LIGHT = "#b08a5c"
BRONZE_DARK = "#3e2c1c"
OUTLINE = "#1b130c"
PLAQUE = "#3a2b1d"
PLAQUE_INK = "#241a12"
GLYPH_CORE = (143, 246, 255)
GLYPH_GLOW = (57, 212, 255)


def _rgba(color: str, alpha: int = 255) -> RGBA:
    r, g, b = ImageColor.getrgb(color)
    return (r, g, b, alpha)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _downsample(
    img: Image.Image, final_size: Tuple[int, int] = OUT_SIZE
) -> Image.Image:
    return img.resize(final_size, Image.Resampling.LANCZOS)


def _polar(center: Point, radius: float, deg: float) -> Point:
    rad = math.radians(deg)
    return (center[0] + math.cos(rad) * radius, center[1] + math.sin(rad) * radius)


def _ring_bbox(radius: float) -> Tuple[float, float, float, float]:
    return (
        CENTER[0] - radius,
        CENTER[1] - radius,
        CENTER[0] + radius,
        CENTER[1] + radius,
    )


def _draw_rotated_polygon(
    draw: ImageDraw.ImageDraw,
    center: Point,
    points: Sequence[Point],
    angle_deg: float,
    *,
    fill: RGBA,
    outline: RGBA | None = None,
    width: int = 1,
) -> None:
    rad = math.radians(angle_deg)
    c = math.cos(rad)
    s = math.sin(rad)
    tx, ty = center
    pts = []
    for x, y in points:
        pts.append((tx + x * c - y * s, ty + x * s + y * c))
    draw.polygon(pts, fill=fill, outline=outline)
    if outline is not None:
        draw.line(pts + [pts[0]], fill=outline, width=width, joint="curve")


def _rune_glow(
    frame_index: int, nframes: int, offset: int = 0, *, dim: bool = False
) -> float:
    phase = ((frame_index + offset) / max(1, nframes)) * math.tau
    base = 0.26 if dim else 0.46
    amp = 0.16 if dim else 0.34
    return max(0.0, min(1.0, base + amp * (0.5 + 0.5 * math.sin(phase))))


def _plaque_angle(index: int) -> float:
    """The direction of chevron ``index`` from the centre (``arch_angle``):
    the first at the lower left, just above the base, the last at the lower
    right."""
    return arch_angle(index)


def _draw_plaque(draw: ImageDraw.ImageDraw, ang: float) -> None:
    """One chevron's plaque: a bronze pentagon pointing at the aperture,
    its dark face where the glyph is cut."""
    center = _polar(CENTER, RING_MID_R, ang)
    _draw_rotated_polygon(draw, center, PLAQUE_OUTER, ang + 90.0, fill=_rgba(PLAQUE), outline=_rgba(OUTLINE), width=4)
    _draw_rotated_polygon(draw, center, PLAQUE_FACE, ang + 90.0, fill=_rgba(PLAQUE_INK), outline=_rgba(BRONZE_LIGHT), width=2)


def _grid_cell(index: int, row: int, col: int) -> Point:
    """The centre of cell (row, col) of chevron ``index``'s position grid:
    row 0 the outermost, column 0 the left one as the plaque stands at the
    top."""
    ang = _plaque_angle(index)
    turn = math.radians(ang + 90.0)
    lx = (col - (GRID_COLS - 1) / 2.0) * GRID_PITCH
    ly = GRID_Y + (row - (GRID_ROWS - 1) / 2.0) * GRID_PITCH
    cx, cy = _polar(CENTER, RING_MID_R, ang)
    return (cx + lx * math.cos(turn) - ly * math.sin(turn), cy + lx * math.sin(turn) + ly * math.cos(turn))


def _draw_grid_sockets(draw: ImageDraw.ImageDraw, index: int) -> None:
    """Chevron ``index``'s sixteen empty sockets."""
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x, y = _grid_cell(index, row, col)
            r = GRID_DOT
            draw.rectangle((x - r, y - r, x + r, y + r), fill=_rgba("#070a0c"))


def _placement(index: int) -> Placement:
    """Glyph ``index`` on its plaque. Turned by its ray's angle plus a
    quarter turn, its up is the ray outward: its foot faces the centre."""
    ang = _plaque_angle(index)
    return Placement(GLYPHS[index], _polar(CENTER, RING_MID_R - GLYPH_INSET, ang), GLYPH_CAP, ang + 90.0)


def _light_layer(core: np.ndarray, glow: np.ndarray, glow_radius: float, core_rgb=GLYPH_CORE) -> Image.Image:
    """Light, from a core coverage and a glow strength per pixel (both 0..1):
    the glow spread ``glow_radius`` pixels in cyan, the core over it."""
    size = (core.shape[1], core.shape[0])
    halo = Image.fromarray(np.clip(glow * 255.0, 0, 255).astype(np.uint8), "L")
    halo = np.asarray(halo.filter(ImageFilter.GaussianBlur(glow_radius)), np.float32) / 255.0
    halo = np.clip(halo * 2.2, 0.0, 1.0)
    a = np.clip(core + halo * (1.0 - core), 0.0, 1.0)
    w = np.where(a > 1e-6, core / np.maximum(a, 1e-6), 0.0)[..., None]
    rgb = np.asarray(core_rgb, np.float32) * w + np.asarray(GLYPH_GLOW, np.float32) * (1.0 - w)
    px = np.dstack([rgb, a * 255.0])
    out = Image.fromarray(np.clip(px, 0, 255).astype(np.uint8), "RGBA")
    assert out.size == size
    return out


def _ring_glyphs(levels: List[float]) -> Image.Image:
    """Every glyph cut into its plaque, each lit at its own level (0..1)."""
    size = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)
    core = np.zeros((size[1], size[0]), np.float32)
    glow = np.zeros_like(core)
    for index, level in enumerate(levels):
        m = glyphs_mask([_placement(index)], size)
        core = np.maximum(core, m * (0.62 + 0.34 * level))
        glow = np.maximum(glow, m * (0.18 + 0.4 * level))
    return _light_layer(core, glow, 1.6 * SUPER, core_rgb=(104, 214, 232))


def _draw_gate_ring_base(*, frame_index: int, nframes: int, idle_mode: bool) -> Image.Image:
    img = Image.new(
        "RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0)
    )
    draw = blending_draw(img)

    ring = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rd = blending_draw(ring)

    rd.ellipse(
        _ring_bbox(OUTER_R), fill=_rgba(BRONZE), outline=_rgba(OUTLINE), width=12
    )
    rd.ellipse(_ring_bbox(OUTER_R - 5 * SUPER), outline=_rgba(BRONZE_LIGHT), width=5)
    rd.ellipse(_ring_bbox(OUTER_R - 9 * SUPER), outline=_rgba(BRONZE_DARK), width=6)
    rd.ellipse(
        _ring_bbox(OUTER_R - 14 * SUPER),
        fill=_rgba("#8a6842"),
        outline=_rgba(BRONZE_LIGHT),
        width=3,
    )
    rd.ellipse(
        _ring_bbox(INNER_R + 7 * SUPER),
        fill=_rgba("#4d3824"),
        outline=_rgba("#a07d55"),
        width=4,
    )
    rd.ellipse(
        _ring_bbox(INNER_R), fill=(0, 0, 0, 0), outline=_rgba(OUTLINE), width=8
    )

    _shade_metal(ring)

    for i in range(30):
        ang = i * (360.0 / 30.0)
        p1 = _polar(CENTER, INNER_R + 4.5 * SUPER, ang)
        p2 = _polar(CENTER, OUTER_R - 4.5 * SUPER, ang)
        rd.line([p1, p2], fill=_rgba(BRONZE_DARK, 115), width=2)

    for i in range(10):
        ang = i * 36.0 + 6.0
        p1 = _polar(CENTER, INNER_R + 8.0 * SUPER, ang)
        p2 = _polar(CENTER, OUTER_R - 8.0 * SUPER, ang)
        rd.line([p1, p2], fill=_rgba("#d2ab78", 80), width=2)

    # The plaques, then the glyphs cut into them, each foot toward the
    # aperture: at rest breathing faintly out of step with its neighbours,
    # charging lit by the pulse.
    for index in range(len(GLYPHS)):
        _draw_plaque(rd, _plaque_angle(index))
        _draw_grid_sockets(rd, index)
    if idle_mode:
        levels = [_rune_glow(frame_index, nframes, index * 2, dim=True) for index in range(len(GLYPHS))]
    else:
        levels = [_charge_level(index, frame_index, nframes) for index in range(len(GLYPHS))]
    ring.alpha_composite(_ring_glyphs(levels))

    for lamp_index, ang in enumerate((-90, 30, 150)):
        cap_center = _polar(CENTER, OUTER_R + 4.0 * SUPER, ang)
        _draw_rotated_polygon(
            rd,
            cap_center,
            [
                (-10 * SUPER, -4.5 * SUPER),
                (10 * SUPER, -4.5 * SUPER),
                (8 * SUPER, 5.5 * SUPER),
                (-8 * SUPER, 5.5 * SUPER),
            ],
            ang + 90.0,
            fill=_rgba("#6b5034"),
            outline=_rgba(OUTLINE),
            width=4,
        )
        _draw_clamp_lamp(
            ring,
            _polar(CENTER, OUTER_R + 4.6 * SUPER, ang),
            ang,
            _lamp_level(lamp_index, frame_index, nframes, idle_mode),
        )

    ring = ring.filter(ImageFilter.GaussianBlur(radius=0.25))
    img.alpha_composite(ring)

    rim = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rim_draw = blending_draw(rim)
    rim_alpha = 78 if idle_mode else 106
    rim_draw.ellipse(
        _ring_bbox(INNER_R + 2.5 * SUPER), outline=_rgba("#5fe2ff", rim_alpha), width=4
    )
    rim_draw.ellipse(
        _ring_bbox(INNER_R + 3.9 * SUPER),
        outline=_rgba("#a8f2ff", rim_alpha // 2),
        width=2,
    )
    rim = rim.filter(ImageFilter.GaussianBlur(radius=2.5))
    img.alpha_composite(rim)
    _draw_base(img, lit=0.55 if idle_mode else 0.55 + 0.45 * (frame_index + 1) / max(1, nframes))
    return img


#: The base's steps, bottom up, in frame pixels: (half width, top). The top
#: step meets the ring just under the aperture, so the base hides the band's
#: bottom slice and nothing else; the bottom step stands on the floor.
BASE_STEPS = ((74.0, 158.0), (62.0, 150.5), (50.0, 143.0))
BASE_FLOOR = 168.0


def _draw_base(img: Image.Image, lit: float) -> None:
    """The stepped base the ring stands in, and the cyan line of the
    threshold on its top step, ``lit`` (0..1) bright."""
    draw = blending_draw(img)
    cx = CENTER[0]
    bottom = BASE_FLOOR * SUPER
    for half, top in BASE_STEPS:
        x0, x1, y0 = cx - half * SUPER, cx + half * SUPER, top * SUPER
        draw.rectangle((x0, y0, x1, bottom), fill=_rgba("#5a4330"), outline=_rgba(OUTLINE), width=4)
        draw.rectangle((x0 + 4, y0 + 4, x1 - 4, y0 + 2.2 * SUPER), fill=_rgba("#a58258"))
        draw.rectangle((x0 + 4, y0 + 2.2 * SUPER, x1 - 4, y0 + 3.0 * SUPER), fill=_rgba(BRONZE_DARK))
        bottom = y0 + 2
    half, top = BASE_STEPS[-1]
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = blending_draw(glow)
    y = top * SUPER + 1.0 * SUPER
    gd.rectangle((cx - (half - 14) * SUPER, y - 2, cx + (half - 14) * SUPER, y + 2), fill=_rgba("#7ff3ff", int(255 * lit)))
    glow = glow.filter(ImageFilter.GaussianBlur(1.2 * SUPER))
    img.alpha_composite(glow)
    draw = blending_draw(img)
    draw.rectangle((cx - (half - 14) * SUPER, y - 1, cx + (half - 14) * SUPER, y + 1), fill=_rgba("#e6fdff", int(230 * lit)))


def _charge_level(index: int, frame_index: int, nframes: int) -> float:
    """How lit chevron ``index`` is as a link opens: a pulse runs from the
    first plaque to the last and leaves each it passes lit."""
    head = (frame_index + 1) / max(1, nframes) * (len(GLYPHS) + 1.0)
    passed = min(1.0, max(0.0, head - index)) * 0.7
    pulse = math.exp(-((index - head + 0.5) ** 2) / 1.4) * 0.7
    return min(1.0, 0.3 + passed + pulse)


def _shade_metal(layer: Image.Image) -> None:
    """Light the ring's metal from the upper left, in place.

    The band is a torus seen face-on: its outer half faces away from the
    centre and its inner half faces toward it. Each pixel is lit by the dot
    product of that normal with a light from the upper left, so the band reads
    as a solid object instead of flat paint. Alpha is not changed.
    """
    px = np.asarray(layer, dtype=np.float32)
    h, w = px.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = xs - CENTER[0]
    dy = ys - CENTER[1]
    dist = np.sqrt(dx * dx + dy * dy) + 1e-6
    # -1 at the inner edge, +1 at the outer edge of the band.
    across = np.clip((dist - RING_MID_R) / ((OUTER_R - INNER_R) / 2.0), -1.0, 1.0)
    nx = dx / dist * across
    ny = dy / dist * across
    nz = np.sqrt(np.clip(1.0 - across * across, 0.0, 1.0))
    light = np.array([-0.55, -0.62, 0.56], dtype=np.float32)
    light /= np.linalg.norm(light)
    lit = nx * light[0] + ny * light[1] + nz * light[2]
    gain = 0.62 + 0.62 * np.clip(lit, 0.0, 1.0)
    spec = np.clip(lit, 0.0, 1.0) ** 18 * 70.0
    rgb = px[..., :3] * gain[..., None] + spec[..., None]
    px[..., :3] = np.clip(rgb, 0.0, 255.0)
    layer.paste(Image.fromarray(px.astype(np.uint8), "RGBA"))


def _lamp_level(lamp_index: int, frame_index: int, nframes: int, idle: bool) -> float:
    """How bright one clamp lamp is.

    Idle: every lamp glows low, so a powered gate reads as powered. Spin: the
    lamps lock one at a time, clockwise from the top, as the inscription turns;
    the last one lights on the last frame of the turn.
    """
    if idle:
        return 0.45 + 0.08 * math.sin(
            (frame_index / max(1, nframes)) * math.tau + lamp_index * 2.1
        )
    locked = (frame_index + 1) / max(1, nframes) >= (lamp_index + 1) / 3.0 - 1e-6
    return 1.0 if locked else 0.22


def _draw_clamp_lamp(layer: Image.Image, center: Point, outward_deg: float, level: float) -> None:
    """A clamp's lamp: a small solid triangle pointing away from the centre.
    The three clamps stand at the corners of a triangle, so the gate wears the
    Δ of its keystone three times."""
    glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    gd = blending_draw(glow)
    gr = (4.5 + 5.5 * level) * SUPER
    gd.ellipse(
        (center[0] - gr, center[1] - gr, center[0] + gr, center[1] + gr),
        fill=_rgba("#45d6ff", int(150 * level)),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=3.0 * SUPER))
    layer.alpha_composite(glow)
    draw = blending_draw(layer)
    r = 3.6 * SUPER
    dim = ImageColor.getrgb("#1f5a6a")
    lit = ImageColor.getrgb("#e6fdff")
    mix = max(0.0, min(1.0, level))
    core = tuple(int(_lerp(a, b, mix)) for a, b in zip(dim, lit)) + (255,)
    corners = [_polar(center, r, outward_deg + k * 120.0) for k in range(3)]
    draw.polygon(corners, fill=core, outline=_rgba(OUTLINE))
    draw.line(corners + [corners[0]], fill=_rgba(OUTLINE), width=3, joint="curve")


def render_ring_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    if animation not in ("idle", "charge"):
        raise ValueError(f"unknown animation: {animation}")
    high = _draw_gate_ring_base(frame_index=frame_index, nframes=nframes, idle_mode=animation == "idle")
    return _downsample(high)


def render_glyph_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    """Chevron ``frame_index`` dialed: its glyph blazing on its plaque at the
    idle ring's place, and the plaque's face washed with its light."""
    if animation not in ("idle", "lit", "bit", "used"):
        raise ValueError(f"unknown animation: {animation}")
    del nframes
    size = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)
    if animation == "idle":
        return _downsample(Image.new("RGBA", size, (0, 0, 0, 0)))
    if animation in ("bit", "used"):
        index, cell = divmod(frame_index, GRID_CELLS)
        x, y = _grid_cell(index, *divmod(cell, GRID_COLS))
        dot = Image.new("L", size, 0)
        r = GRID_DOT * (1.0 if animation == "bit" else 0.7)
        ImageDraw.Draw(dot).rectangle((x - r, y - r, x + r, y + r), fill=255)
        core = np.asarray(dot, np.float32) / 255.0
        if animation == "bit":
            return _downsample(_light_layer(core, core * 0.6, 0.5 * SUPER, core_rgb=(255, 255, 255)))
        return _downsample(_light_layer(core, core * 0.0, 0.3 * SUPER, core_rgb=(48, 150, 184)))
    core = glyphs_mask([_placement(frame_index)], size)
    wash = Image.new("L", size, 0)
    ang = _plaque_angle(frame_index)
    _draw_rotated_polygon(
        ImageDraw.Draw(wash),
        _polar(CENTER, RING_MID_R, ang),
        PLAQUE_FACE,
        ang + 90.0,
        fill=255,
    )
    glow = np.maximum(core, np.asarray(wash, np.float32) / 255.0 * 0.2)
    return _downsample(_light_layer(core, glow, 2.6 * SUPER, core_rgb=(236, 255, 255)))


def render_portal_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    """The wormhole: a triangle door (Jon, 2026-10-24: "triangle is better").
    Three rays inscribe a triangle in the ring, it opens to a tunnel of
    nested triangles, and closes into its centre (`_gate_wormhole_triangles`)."""
    from ._gate_wormhole_triangles import render_portal_frame as triangle_door

    return triangle_door(animation, frame_index, nframes, out_size=OUT_SIZE[0])


def render_glyph_icons() -> Image.Image:
    """The fifteen glyphs in a row of ``GLYPH_ICON`` cells, white and upright,
    each centred by its ink, a stroke of air round the tallest."""
    from ambition_sprite2d_renderer.glyphs.legally_distinct import CAP, STROKE, render_glyph

    strip = Image.new("RGBA", (GLYPH_ICON * len(GLYPHS), GLYPH_ICON), (0, 0, 0, 0))
    height = int(round(GLYPH_ICON * 0.78 * (CAP + 2 * STROKE) / CAP))
    for glyph in GLYPHS:
        tile = render_glyph(glyph, height, "#ffffff")
        box = tile.getchannel("A").getbbox()
        if box is None:
            continue
        ink = tile.crop(box)
        x = glyph.index * GLYPH_ICON + (GLYPH_ICON - ink.width) // 2
        strip.alpha_composite(ink, (x, (GLYPH_ICON - ink.height) // 2))
    return strip


def render_tunnel_picture() -> Image.Image:
    """The inside of the wormhole, tiling both ways: a lattice of Sierpinski
    triangles (``_gate_wormhole_triangles``)."""
    from ._gate_wormhole_triangles import render_tunnel_picture as triangle_tunnel

    return triangle_tunnel(TUNNEL_SIZE)


@functools.lru_cache(maxsize=1)
def _assembly_body_metrics() -> dict:
    """The gate's one body: the ring's idle frame, on the shared canvas.

    The ring and the membrane are two sheets of ONE assembly, placed on the
    same prop box. The runtime scales and anchors each sheet by its own body,
    so both sheets publish this same body on the same uncropped canvas. Then
    the membrane lands inside the aperture exactly as drawn here. If each
    sheet measured its own art, the membrane would scale by its own (smaller,
    and at opening frame 0 empty) extent and cover the chevrons.
    """
    return alpha_bbox_metrics(render_ring_frame("idle", 0, RING_ROWS[0][1]))


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # No auto-crop: the two sheets share one logical frame (the drawing canvas),
    # which `_assembly_body_metrics` is measured in. The packer still trims
    # each frame's texture to its own ink.
    shared = dict(
        out_dir=out_dir,
        frame_size=OUT_SIZE,
        label_width=128,
        auto_crop=False,
        body_metrics_fn=lambda _fw, _fh: _assembly_body_metrics(),
    )
    ring_outputs = build_sheet(
        target=RING_TARGET,
        rows=RING_ROWS,
        render_fn=render_ring_frame,
        **shared,
    )
    portal_outputs = build_sheet(
        target=PORTAL_TARGET,
        rows=PORTAL_ROWS,
        render_fn=render_portal_frame,
        **shared,
    )
    glyph_outputs = build_sheet(
        target=GLYPHS_TARGET,
        rows=GLYPH_ROWS,
        render_fn=render_glyph_frame,
        **shared,
    )
    tunnel = out_dir / f"{TARGET_NAME}_tunnel.png"
    render_tunnel_picture().save(tunnel)
    icons = out_dir / f"{TARGET_NAME}_glyph_icons.png"
    render_glyph_icons().save(icons)
    ordered = [
        tunnel,
        icons,
        ring_outputs["canonical"],
        ring_outputs["canonical_transparent"],
        ring_outputs["spritesheet"],
        ring_outputs["yaml"],
        ring_outputs["preview"],
        portal_outputs["canonical"],
        portal_outputs["canonical_transparent"],
        portal_outputs["spritesheet"],
        portal_outputs["yaml"],
        portal_outputs["preview"],
        glyph_outputs["canonical"],
        glyph_outputs["canonical_transparent"],
        glyph_outputs["spritesheet"],
        glyph_outputs["yaml"],
        glyph_outputs["preview"],
    ]
    return ordered
