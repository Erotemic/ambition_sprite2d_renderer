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
GLYPH_ROWS: List[Tuple[str, int, int]] = [("idle", 1, 100), ("lit", len(GLYPHS), 100)]

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
CENTER = (FRAME_SIZE[0] * SUPER / 2.0, FRAME_SIZE[1] * SUPER / 2.0)
OUTER_R = 69.0 * SUPER
INNER_R = 45.0 * SUPER
PORTAL_R = 39.5 * SUPER
RING_MID_R = (INNER_R + OUTER_R) / 2.0
#: The bottom slice of the ring the base hides: no plaque there.
BASE_GAP_DEG = ARCH_GAP_DEG
#: The plaques shrink to fit the shorter arc.
PLAQUE_SCALE = 0.78
#: A plaque's dark face, about its centre, foot down (y down), where the
#: glyph is cut and where a dialed glyph's light washes.
PLAQUE_FACE = [
    (x * PLAQUE_SCALE * SUPER, y * PLAQUE_SCALE * SUPER)
    for x, y in ((-5.6, -4.0), (5.6, -4.0), (8.4, 1.95), (0.0, 8.8), (-8.4, 1.95))
]
#: A glyph's cap height, and how far its centre sits inward of the band's
#: middle (the plaque's open face is nearer the aperture than its middle).
GLYPH_CAP = 7.0 * SUPER
GLYPH_INSET = 1.3 * SUPER

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
    img: Image.Image, final_size: Tuple[int, int] = FRAME_SIZE
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
    outer = [
        (-8.35 * SUPER, -5.8 * SUPER),
        (8.35 * SUPER, -5.8 * SUPER),
        (12.7 * SUPER, 2.55 * SUPER),
        (0.0, 12.2 * SUPER),
        (-12.7 * SUPER, 2.55 * SUPER),
    ]
    inner = PLAQUE_FACE
    outer = [(x * PLAQUE_SCALE, y * PLAQUE_SCALE) for x, y in outer]
    _draw_rotated_polygon(draw, center, outer, ang + 90.0, fill=_rgba(PLAQUE), outline=_rgba(OUTLINE), width=4)
    _draw_rotated_polygon(draw, center, inner, ang + 90.0, fill=_rgba(PLAQUE_INK), outline=_rgba(BRONZE_LIGHT), width=2)


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
    if animation not in ("idle", "lit"):
        raise ValueError(f"unknown animation: {animation}")
    del nframes
    size = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)
    if animation == "idle":
        return _downsample(Image.new("RGBA", size, (0, 0, 0, 0)))
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
    glow = np.maximum(core, np.asarray(wash, np.float32) / 255.0 * 0.32)
    return _downsample(_light_layer(core, glow, 2.6 * SUPER, core_rgb=(236, 255, 255)))


def _portal_mask(radius: float) -> Image.Image:
    mask = Image.new("L", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), 0)
    md = blending_draw(mask)
    md.ellipse(_ring_bbox(radius), fill=255)
    return mask


def _draw_star_specks(
    draw: ImageDraw.ImageDraw, t: float, radius: float, opening: float
) -> None:
    for i in range(16):
        ang = i * 137.5 + t * 180.0
        rr = radius * (0.22 + ((i * 37) % 100) / 120.0)
        x, y = _polar(CENTER, rr, ang)
        spark = 1.1 + ((i * 13) % 7) * 0.22
        alpha = int(_lerp(0, 165, opening) * (0.55 + 0.45 * math.sin(t * math.tau + i)))
        draw.ellipse(
            (
                x - spark * SUPER,
                y - spark * SUPER,
                x + spark * SUPER,
                y + spark * SUPER,
            ),
            fill=(255, 255, 255, max(0, alpha)),
        )


def _ease_out_back(t: float, overshoot: float = 1.35) -> float:
    t = max(0.0, min(1.0, t)) - 1.0
    return 1.0 + t * t * ((overshoot + 1.0) * t + overshoot)


def _portal_surface(
    radius: float, loop_t: float, alpha_scale: float, flash: float, splash: float = -1.0, outward: bool = False
) -> Image.Image:
    """The membrane: a deep, water-like surface with ripples moving outward.

    ``loop_t`` in [0, 1) is the loop phase; every motion term is periodic in it,
    so the stable row loops without a seam.

    ``splash`` in [0, 1] is how far through a crossing the surface is (none
    when negative): a ring runs out from the middle to the lip and dies. A
    body going in (``outward`` false) dents the middle, dark, and the surface
    closes over it; a body coming out (``outward``) swells it, bright, and the
    swell falls back.
    """
    size = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)
    ys, xs = np.mgrid[0 : size[1], 0 : size[0]].astype(np.float32)
    dx = xs - CENTER[0]
    dy = ys - CENTER[1]
    dist = np.sqrt(dx * dx + dy * dy)
    d = dist / max(radius, 1.0)
    theta = np.arctan2(dy, dx)
    tau = math.tau

    deep = np.array([18, 34, 122], dtype=np.float32)
    mid = np.array([44, 118, 232], dtype=np.float32)
    edge = np.array([118, 226, 255], dtype=np.float32)
    k = np.clip(d, 0.0, 1.0)[..., None]
    base = deep * (1 - k) ** 2 + mid * 2 * k * (1 - k) + edge * k**2

    # Ripples travelling outward, one wavelength per loop.
    ripple = 0.5 + 0.5 * np.sin((d * 6.0 - loop_t) * tau)
    ripple = ripple**4 * (0.25 + 0.75 * np.clip(d, 0.0, 1.0))
    # A slow swirl, so the surface is not a static target.
    swirl = 0.5 + 0.5 * np.sin(theta * 3.0 + d * 7.0 - loop_t * tau * 2.0)
    swirl = swirl**6 * 0.35
    # A specular highlight from the upper left, like a lit liquid surface.
    hx = dx / max(radius, 1.0) + 0.38
    hy = dy / max(radius, 1.0) + 0.42
    spec = np.exp(-(hx * hx * 9.0 + hy * hy * 22.0)) * 0.55

    light = ripple * 95.0 + swirl * 70.0 + spec * 255.0 + flash * 180.0
    if splash >= 0.0:
        u = float(splash)
        fade = (1.0 - u) ** 1.3
        # The ring that runs out to the lip, a smaller one behind it, and the
        # surface between them pulled into folds.
        # Each crest has its trough just behind it, so it reads as a wave.
        front, back = u * 1.08, max(0.0, u - 0.3) * 1.08
        lead = np.exp(-(((d - front) / 0.06) ** 2))
        lead_trough = np.exp(-(((d - front + 0.1) / 0.06) ** 2)) * (d < front)
        trail = np.exp(-(((d - back) / 0.045) ** 2)) * 0.7
        trail_trough = np.exp(-(((d - back + 0.075) / 0.045) ** 2)) * (d < back) * 0.7
        light = light + (lead * 300.0 + trail * 220.0) * fade
        base = base * (1.0 - ((lead_trough + trail_trough) * 0.55 * fade)[..., None])
        light = light - (lead_trough + trail_trough) * 120.0 * fade
        # The middle: a dent, or a swell, that settles as the ring goes out.
        middle = np.exp(-((d / (0.22 + 0.25 * u)) ** 2)) * (1.0 - _ease(u))
        if outward:
            light = light + middle * 260.0
        else:
            base = base * (1.0 - middle[..., None] * 0.75)
            light = light - middle * 90.0
    light = light[..., None]
    rgb = base + light * np.array([0.78, 0.94, 1.0], dtype=np.float32)

    # Bright lip at the edge of the membrane, with a soft glow past it.
    lip = np.exp(-(((d - 0.965) / 0.035) ** 2))
    rgb = rgb * (1 - lip[..., None] * 0.6) + np.array([220, 250, 255]) * lip[..., None] * 0.6
    inside = np.clip((1.0 - d) * radius / (1.2 * SUPER), 0.0, 1.0)
    halo = np.exp(-(((d - 1.0) / 0.07) ** 2)) * (d > 1.0)
    alpha = np.clip(inside * 238.0 + halo * 150.0, 0.0, 255.0) * alpha_scale
    halo_rgb = np.array([150, 236, 255], dtype=np.float32)
    rgb = np.where((d > 1.0)[..., None], halo_rgb, rgb)

    px = np.zeros((size[1], size[0], 4), dtype=np.float32)
    px[..., :3] = np.clip(rgb, 0.0, 255.0)
    px[..., 3] = alpha
    return Image.fromarray(px.astype(np.uint8), "RGBA")


def render_portal_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    img = Image.new(
        "RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0)
    )
    t = frame_index / max(1, nframes - 1)
    if animation == "opening":
        # Bursts out slightly past the ring's aperture and settles back.
        size = _ease_out_back(t)
        alpha_scale = _ease(min(1.0, t * 2.2))
        flash = max(0.0, 1.0 - abs(t - 0.55) / 0.3) * 0.4
        loop_t = t
    elif animation == "closing":
        # Swells once, then collapses to a point.
        size = (1.0 + 0.06 * math.sin(min(1.0, t * 2.5) * math.pi)) * (1.0 - _ease(t) ** 1.6)
        alpha_scale = 1.0 - _ease(max(0.0, t - 0.55) / 0.45)
        flash = max(0.0, 1.0 - abs(t - 0.8) / 0.2) * 0.6
        loop_t = t
    else:
        size = 1.0
        alpha_scale = 1.0
        flash = 0.0
        loop_t = frame_index / max(1, nframes)
    splash = -1.0
    if animation in ("swallow", "emit"):
        # On the stable surface's own clock, so it cuts in from ``stable``.
        splash = t
        loop_t = (frame_index * 0.5 / max(1, nframes)) % 1.0
        # The membrane gives a little where the body meets it.
        dip = math.sin(min(1.0, t * 3.0) * math.pi) * (1.0 - t)
        size = 1.0 + (0.035 if animation == "emit" else -0.025) * dip
        flash = (0.35 if animation == "emit" else 0.15) * max(0.0, 1.0 - t * 4.0)
    if size <= 0.01 or alpha_scale <= 0.01:
        return _downsample(img)

    radius = PORTAL_R * size
    surface = _portal_surface(radius, loop_t, alpha_scale, flash, splash, animation == "emit")
    draw = blending_draw(surface)
    _draw_star_specks(draw, loop_t, radius, alpha_scale)

    # The overshoot may pass the ring's aperture; the ring covers the rest.
    mask = _portal_mask(PORTAL_R * 1.12)
    clipped = Image.new("RGBA", surface.size, (0, 0, 0, 0))
    clipped.paste(surface, (0, 0), mask)
    img.alpha_composite(clipped)
    return _downsample(img)


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


def _periodic_noise(rng: np.random.Generator, size: int, falloff: float) -> np.ndarray:
    """Noise that tiles: random phases under a power-law spectrum, 0..1."""
    fy = np.fft.fftfreq(size)[:, None]
    fx = np.fft.fftfreq(size)[None, :]
    freq = np.sqrt(fx * fx + fy * fy)
    freq[0, 0] = 1.0
    spectrum = (rng.normal(size=(size, size)) + 1j * rng.normal(size=(size, size))) / freq**falloff
    spectrum[0, 0] = 0.0
    field = np.real(np.fft.ifft2(spectrum))
    return (field - field.min()) / max(1e-6, field.max() - field.min())


def render_tunnel_picture() -> Image.Image:
    """The inside of the wormhole, tiling both ways (see the module)."""
    n = TUNNEL_SIZE
    rng = np.random.default_rng(1977)
    cloud = _periodic_noise(rng, n, 1.6)
    wisps = _periodic_noise(rng, n, 1.1)
    deep = np.array([10, 22, 70], np.float32)
    blue = np.array([40, 120, 230], np.float32)
    cyan = np.array([120, 236, 255], np.float32)
    violet = np.array([120, 70, 210], np.float32)
    k = np.clip((cloud - 0.35) / 0.5, 0.0, 1.0)[..., None]
    rgb = deep * (1 - k) + blue * k
    rgb = rgb + (cyan - rgb) * (np.clip((wisps - 0.62) / 0.3, 0.0, 1.0) ** 2)[..., None]
    rgb = rgb + (violet - rgb) * (np.clip((0.3 - cloud) / 0.3, 0.0, 1.0) * 0.6)[..., None]
    # Streaks: stars stretched along the way in, wrapped at the edges.
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float32)
    stars = np.zeros((n, n), np.float32)
    for _ in range(150):
        sx, sy = rng.uniform(0, n, 2)
        length = rng.uniform(3.0, 11.0)
        bright = rng.uniform(0.35, 1.0)
        dx = (xs - sx + n / 2) % n - n / 2
        dy = (ys - sy + n / 2) % n - n / 2
        stars += bright * np.exp(-(dx * dx) / (2 * 0.7**2) - (dy * dy) / (2 * length**2))
    rgb = rgb + np.clip(stars, 0.0, 1.4)[..., None] * np.array([210, 245, 255], np.float32)
    px = np.dstack([np.clip(rgb, 0, 255), np.full((n, n), 255.0)])
    return Image.fromarray(px.astype(np.uint8), "RGBA")


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
        frame_size=FRAME_SIZE,
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
