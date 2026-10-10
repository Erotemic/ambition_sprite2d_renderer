"""Procedural interdimensional portal / gate sprite sheets.

This target intentionally evokes a monumental sci-fi portal ring while staying
well clear of an exact screen-used reproduction. The ring carries the Greek
inscription "ΛΕΓΑΛΛΥ ΔΙΣΤΙΝΧΤ" on plaque-like chevron housings, with Λ anchored
at 12 o'clock. The wormhole / portal membrane is rendered as a separate
transparent overlay sheet so gameplay can layer it over the ring when active.
"""

from __future__ import annotations

import functools
import math
from pathlib import Path
from typing import List, Sequence, Tuple

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont

from ...authoring.sheet_build import alpha_bbox_metrics, build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "interdimensional_gate"
RING_TARGET = f"{TARGET_NAME}_ring"
PORTAL_TARGET = f"{TARGET_NAME}_portal"

RING_ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 140),
    ("spin", 12, 85),
]
PORTAL_ROWS: List[Tuple[str, int, int]] = [
    ("opening", 8, 80),
    ("stable", 8, 110),
    ("closing", 8, 80),
]

SHEET_FILES = [
    f"{RING_TARGET}_spritesheet.png",
    f"{RING_TARGET}_spritesheet.yaml",
    f"{PORTAL_TARGET}_spritesheet.png",
    f"{PORTAL_TARGET}_spritesheet.yaml",
]

# Use a larger canvas than the default character sheets so the gate has more
# room for legible inscription detail and cleaner anti-aliased edges.
FRAME_SIZE = (192, 192)
SUPER = 4
CENTER = (FRAME_SIZE[0] * SUPER / 2.0, FRAME_SIZE[1] * SUPER / 2.0)
OUTER_R = 69.0 * SUPER
INNER_R = 45.0 * SUPER
PORTAL_R = 39.5 * SUPER
RING_MID_R = (INNER_R + OUTER_R) / 2.0
INSCRIPTION = [c for c in "ΛΕΓΑΛΛΥ ΔΙΣΤΙΝΧΤ" if c != " "]
GLYPH_STEP_DEG = 360.0 / len(INSCRIPTION)


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


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


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


def _paste_center(dst: Image.Image, src: Image.Image, center: Point) -> None:
    x = int(round(center[0] - src.width / 2.0))
    y = int(round(center[1] - src.height / 2.0))
    dst.alpha_composite(src, (x, y))


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


def _center_layer_to(layer: Image.Image, dest_center: Point) -> Image.Image:
    """Translate ``layer`` so the alpha-bbox center lands on ``dest_center``."""
    alpha = layer.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return layer
    bx = (bbox[0] + bbox[2]) / 2.0
    by = (bbox[1] + bbox[3]) / 2.0
    dx = int(round(dest_center[0] - bx))
    dy = int(round(dest_center[1] - by))
    shifted = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shifted.alpha_composite(layer, (dx, dy))
    return shifted


def _make_glyph_chevron(glyph: str, glow_strength: float) -> Image.Image:
    """Build one upright icon tile, then rotate/translate it into place.

    The glyph is rendered upright in its own local layer, centered from its
    alpha bbox both horizontally and vertically, and only then embedded inside a
    slightly oversized chevron icon. Later, the *whole* icon is rotated and
    translated onto the ring.
    """
    tile_size = 40 * SUPER
    tile = Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
    draw = blending_draw(tile)
    cx = cy = tile_size / 2.0

    # Slightly bigger border / housing to give the glyph more visual breathing
    # room while keeping the glyph size itself unchanged.
    outer = [
        (-8.35 * SUPER, -5.8 * SUPER),
        (8.35 * SUPER, -5.8 * SUPER),
        (12.7 * SUPER, 2.55 * SUPER),
        (0.0, 12.2 * SUPER),
        (-12.7 * SUPER, 2.55 * SUPER),
    ]
    inner = [
        (-4.9 * SUPER, -3.2 * SUPER),
        (4.9 * SUPER, -3.2 * SUPER),
        (7.7 * SUPER, 1.95 * SUPER),
        (0.0, 8.35 * SUPER),
        (-7.7 * SUPER, 1.95 * SUPER),
    ]
    _draw_rotated_polygon(
        draw,
        (cx, cy),
        outer,
        0.0,
        fill=_rgba("#765f3f"),
        outline=_rgba("#151922"),
        width=4,
    )
    _draw_rotated_polygon(
        draw,
        (cx, cy),
        inner,
        0.0,
        fill=_rgba("#34261a"),
        outline=_rgba("#97784e"),
        width=2,
    )

    font = _font(12 * SUPER)

    # Render the glyph on a temporary layer, then recentre it by its actual
    # alpha bounds so the symbol center sits close to the icon center.
    core_layer = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    core_draw = blending_draw(core_layer)
    bbox = font.getbbox(glyph)
    tx = int(round(cx - (bbox[0] + bbox[2]) / 2.0))
    ty = int(round(cy - (bbox[1] + bbox[3]) / 2.0))
    core_color = _rgba("#fff7e1", int(255 * min(1.0, 0.78 + 0.22 * glow_strength)))
    core_draw.text((tx, ty), glyph, font=font, fill=core_color)
    core_layer = _center_layer_to(core_layer, (cx, cy))

    glow_layer = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    glow_draw = blending_draw(glow_layer)
    glow_color = _rgba("#ff9f3d", int(245 * glow_strength))
    alpha_bbox = core_layer.getchannel("A").getbbox()
    if alpha_bbox is not None:
        gx = int(round(cx - (alpha_bbox[0] + alpha_bbox[2]) / 2.0))
        gy = int(round(cy - (alpha_bbox[1] + alpha_bbox[3]) / 2.0))
        # Reuse the same nominal origin and recenter again to ensure the glow
        # tracks the core glyph exactly.
        glow_draw.text((tx, ty), glyph, font=font, fill=glow_color)
        glow_layer = _center_layer_to(glow_layer, (cx, cy))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=max(3, SUPER + 1)))
    tile.alpha_composite(glow_layer)
    tile.alpha_composite(core_layer)

    ember = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    ember_draw = blending_draw(ember)
    dot_r = 0.95 * SUPER
    ember_draw.ellipse(
        (cx - dot_r, cy + 4.7 * SUPER - dot_r, cx + dot_r, cy + 4.7 * SUPER + dot_r),
        fill=_rgba("#ff9d43", int(170 * glow_strength)),
    )
    tile.alpha_composite(ember)
    return tile


def _draw_gate_ring_base(
    rotation_deg: float, *, frame_index: int, nframes: int, idle_mode: bool
) -> Image.Image:
    img = Image.new(
        "RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0)
    )
    draw = blending_draw(img)

    ring = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rd = blending_draw(ring)

    rd.ellipse(
        _ring_bbox(OUTER_R), fill=_rgba("#454b57"), outline=_rgba("#1a1e28"), width=12
    )
    rd.ellipse(_ring_bbox(OUTER_R - 5 * SUPER), outline=_rgba("#778091"), width=5)
    rd.ellipse(_ring_bbox(OUTER_R - 9 * SUPER), outline=_rgba("#2c313b"), width=6)
    rd.ellipse(
        _ring_bbox(OUTER_R - 14 * SUPER),
        fill=_rgba("#596170"),
        outline=_rgba("#8790a1"),
        width=3,
    )
    rd.ellipse(
        _ring_bbox(INNER_R + 7 * SUPER),
        fill=_rgba("#353b46"),
        outline=_rgba("#7f8797"),
        width=4,
    )
    rd.ellipse(
        _ring_bbox(INNER_R), fill=(0, 0, 0, 0), outline=_rgba("#151922"), width=8
    )

    _shade_metal(ring)

    for i in range(30):
        ang = rotation_deg + i * (360.0 / 30.0)
        p1 = _polar(CENTER, INNER_R + 4.5 * SUPER, ang)
        p2 = _polar(CENTER, OUTER_R - 4.5 * SUPER, ang)
        rd.line([p1, p2], fill=_rgba("#2a2f39", 115), width=2)

    for i in range(10):
        ang = rotation_deg + i * 36.0 + 6.0
        p1 = _polar(CENTER, INNER_R + 8.0 * SUPER, ang)
        p2 = _polar(CENTER, OUTER_R - 8.0 * SUPER, ang)
        rd.line([p1, p2], fill=_rgba("#98a2b1", 92), width=2)

    # Build each icon upright, then rotate and place it.  Rotation angle is
    # chosen so the bottom of the glyph points toward the centre of the gate.
    for idx, glyph in enumerate(INSCRIPTION):
        ang = rotation_deg - 90.0 + idx * GLYPH_STEP_DEG
        housing_center = _polar(CENTER, RING_MID_R, ang)
        glow_strength = _rune_glow(frame_index, nframes, idx * 2, dim=idle_mode)
        icon = _make_glyph_chevron(glyph, glow_strength)
        rotated_icon = icon.rotate(
            -(ang + 90.0), expand=True, resample=Image.Resampling.BICUBIC
        )
        _paste_center(ring, rotated_icon, housing_center)

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
            fill=_rgba("#6d7581"),
            outline=_rgba("#1a1e28"),
            width=4,
        )
        _draw_clamp_lamp(
            ring,
            _polar(CENTER, OUTER_R + 4.6 * SUPER, ang),
            _lamp_level(lamp_index, frame_index, nframes, idle_mode),
        )

    ring = ring.filter(ImageFilter.GaussianBlur(radius=0.25))
    img.alpha_composite(ring)

    rim = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rim_draw = blending_draw(rim)
    rim_alpha = 78 if idle_mode else 106
    rim_draw.ellipse(
        _ring_bbox(INNER_R + 2.5 * SUPER), outline=_rgba("#ff9d4b", rim_alpha), width=4
    )
    rim_draw.ellipse(
        _ring_bbox(INNER_R + 3.9 * SUPER),
        outline=_rgba("#ffbe73", rim_alpha // 2),
        width=2,
    )
    rim = rim.filter(ImageFilter.GaussianBlur(radius=2.5))
    img.alpha_composite(rim)
    return img


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


def _draw_clamp_lamp(layer: Image.Image, center: Point, level: float) -> None:
    glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    gd = blending_draw(glow)
    gr = (4.5 + 5.5 * level) * SUPER
    gd.ellipse(
        (center[0] - gr, center[1] - gr, center[0] + gr, center[1] + gr),
        fill=_rgba("#ffae45", int(150 * level)),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=3.0 * SUPER))
    layer.alpha_composite(glow)
    draw = blending_draw(layer)
    r = 2.8 * SUPER
    dim = ImageColor.getrgb("#8a4f1f")
    lit = ImageColor.getrgb("#fff0c8")
    mix = max(0.0, min(1.0, level))
    core = tuple(int(_lerp(a, b, mix)) for a, b in zip(dim, lit)) + (255,)
    draw.ellipse(
        (center[0] - r, center[1] - r, center[0] + r, center[1] + r),
        fill=core,
        outline=_rgba("#1a1e28"),
        width=3,
    )


def render_ring_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    if animation == "spin":
        rotation = 360.0 * (frame_index / max(1, nframes))
        idle_glow = False
    else:
        rotation = 0.0
        idle_glow = True
    high = _draw_gate_ring_base(
        rotation, frame_index=frame_index, nframes=nframes, idle_mode=idle_glow
    )
    return _downsample(high)


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


def _portal_surface(radius: float, loop_t: float, alpha_scale: float, flash: float) -> Image.Image:
    """The membrane: a deep, water-like surface with ripples moving outward.

    ``loop_t`` in [0, 1) is the loop phase; every motion term is periodic in it,
    so the stable row loops without a seam.
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

    light = (ripple * 95.0 + swirl * 70.0 + spec * 255.0 + flash * 180.0)[..., None]
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
    if size <= 0.01 or alpha_scale <= 0.01:
        return _downsample(img)

    radius = PORTAL_R * size
    surface = _portal_surface(radius, loop_t, alpha_scale, flash)
    draw = blending_draw(surface)
    _draw_star_specks(draw, loop_t, radius, alpha_scale)

    # The overshoot may pass the ring's aperture; the ring covers the rest.
    mask = _portal_mask(PORTAL_R * 1.12)
    clipped = Image.new("RGBA", surface.size, (0, 0, 0, 0))
    clipped.paste(surface, (0, 0), mask)
    img.alpha_composite(clipped)
    return _downsample(img)


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
    ordered = [
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
    ]
    return ordered
