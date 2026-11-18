"""The Jungle's portal arch: a travel portal (a ring of kind ``Portal``,
which reaches only the arches of its own dimension within its reach), drawn
as an old stone arch (WORLD-LAYERS JL-2). The gate rings are 288 world units
and stand through the Jungle's branch platforms; an arch is a door's size,
small enough to stand under a branch or on one.

It is the gate's assembly at a door's scale, in the Jungle's stone:

- the ARCH: a round head of voussoirs on two jambs of coursed blocks, an
  impost at each springing, on a stepped threshold, every block a little
  its own colour, lit from the upper left;
- the KEYSTONE: proud of the head, the network's Δ cut in it, glowing low
  at rest (a powered arch reads as powered) and ablaze as it opens;
- the SEAM: a line of the gate's cyan light round the opening's edge; as
  the arch opens (the ``charge`` row, played with the portal's ``opening``)
  it climbs both jambs from the threshold and meets at the keystone;
- the JUNGLE: moss on the head and the threshold, a vine hanging from the
  left shoulder and a fern at the right foot;
- the MEMBRANE: the gate's wormhole (``_gate_wormhole_triangles``), its
  triangle door in the opening and everything clipped to the arch.

Two sheets of one assembly, on one canvas (``FRAME_SIZE``), with the gate's
rows: ``_ring`` (``idle``, ``charge``) and ``_portal`` (``PORTAL_ROWS``). A
portal lights no address, so there is no glyph sheet. No drop shadows.
"""

from __future__ import annotations

import functools
import math
import random
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ...authoring.sheet_build import alpha_bbox_metrics, build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

from . import interdimensional_gate as gate
from ._gate_wormhole_triangles import Aperture, render_portal_frame as wormhole_frame

Point = Tuple[float, float]
RGBA = Tuple[int, int, int, int]

TARGET_NAME = "jungle_arch"
RING_TARGET = f"{TARGET_NAME}_ring"
PORTAL_TARGET = f"{TARGET_NAME}_portal"

RING_ROWS = gate.RING_ROWS
PORTAL_ROWS = gate.PORTAL_ROWS

SHEET_FILES = [
    f"{RING_TARGET}_spritesheet.png",
    f"{RING_TARGET}_spritesheet.yaml",
    f"{PORTAL_TARGET}_spritesheet.png",
    f"{PORTAL_TARGET}_spritesheet.yaml",
]

# --- geometry (design units, y down; published at 3 px a unit) ---------------

FRAME_SIZE = (96, 96)
SUPER = 4
OUT_SIZE = (FRAME_SIZE[0] * 3, FRAME_SIZE[1] * 3)

CX = FRAME_SIZE[0] / 2.0
#: The opening's half width and the arch's (to the jambs' outer faces).
OPEN_W = 17.0
OUTER_W = 27.0
#: The springing line: the head's centre; the head is a half circle on it.
SPRING_Y = 40.0
#: The opening's foot (the threshold's top) and the floor (the lowest step's
#: foot).
THRESHOLD_Y = 86.0
FLOOR_Y = 93.0
#: The head's voussoirs (odd: the middle one is the keystone), and how far
#: the keystone stands proud above the head and is wider at its top.
VOUSSOIRS = 9
KEY_PROUD = 3.0
KEY_FLARE = 1.6
#: The jambs' courses, bottom up (heights, summing to the jamb's height).
COURSES = (10.0, 8.0, 10.0, 8.0, 10.0)
#: The imposts: a block at each springing, proud of the jamb either side.
IMPOST_H = 4.0
IMPOST_PROUD = 2.0
#: The threshold's steps, bottom up: (half width, rise).
STEPS = ((OUTER_W + 4.0, 3.5), (OUTER_W + 1.0, 3.5))

assert abs(sum(COURSES) - (THRESHOLD_Y - SPRING_Y)) < 1e-6
assert abs(sum(rise for _, rise in STEPS) - (FLOOR_Y - THRESHOLD_Y)) < 1e-6

#: The wormhole's door (circumradius) and its centre: low in the opening, so
#: a body walking in meets its middle.
DOOR_R = 14.0
DOOR_CENTRE = (CX, 60.0)

# Old jungle stone, lichen grey-green; moss and leaves; the gate's light.
STONE = (118, 124, 104)
STONE_LIGHT = (160, 166, 140)
STONE_DARK = (70, 76, 62)
MORTAR = (44, 48, 38)
OUTLINE = (24, 27, 20)
MOSS = (78, 122, 46)
MOSS_LIGHT = (122, 168, 70)
LEAF = (58, 104, 40)
LEAF_LIGHT = (104, 152, 62)
VINE = (52, 82, 34)
GLOW_CORE = gate.GLYPH_CORE
GLOW = gate.GLYPH_GLOW


def _s(v: float) -> float:
    """Design units to drawing pixels."""
    return v * SUPER


def _pt(x: float, y: float) -> Point:
    return (_s(x), _s(y))


def _size() -> Tuple[int, int]:
    return (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)


def _shade(color: Tuple[int, int, int], k: float) -> Tuple[int, int, int]:
    """``color`` lightened (k > 0) or darkened (k < 0)."""
    if k >= 0:
        return tuple(int(round(c + (255 - c) * k)) for c in color)  # type: ignore[return-value]
    return tuple(int(round(c * (1.0 + k))) for c in color)  # type: ignore[return-value]


def _rgba(color: Tuple[int, int, int], alpha: int = 255) -> RGBA:
    return (color[0], color[1], color[2], alpha)


def _polar(r: float, deg: float) -> Point:
    """The drawing pixel ``r`` units from the head's centre at ``deg``
    (0 is east, -90 the crown; y down)."""
    a = math.radians(deg)
    return (_s(CX + math.cos(a) * r), _s(SPRING_Y + math.sin(a) * r))


# --- the stone -------------------------------------------------------------------


def _blocks() -> List[Tuple[List[Point], float, str]]:
    """Every block of the arch as (polygon in drawing pixels, its own
    shade, its part), drawn back to front: the steps, the jambs, the
    imposts, the voussoirs, the keystone."""
    rng = random.Random(7)
    blocks: List[Tuple[List[Point], float, str]] = []
    y = FLOOR_Y
    for half, rise in STEPS:
        blocks.append(([_pt(CX - half, y - rise), _pt(CX + half, y - rise), _pt(CX + half, y), _pt(CX - half, y)], rng.uniform(-0.08, 0.06), "step"))
        y -= rise
    for side in (-1, 1):
        y = THRESHOLD_Y
        for k, h in enumerate(COURSES):
            inner, outer = CX + side * OPEN_W, CX + side * OUTER_W
            # Alternate courses are a little proud: coursed rubble, not ashlar.
            proud = 0.6 if k % 2 else 0.0
            outer += side * proud
            blocks.append(([_pt(min(inner, outer), y - h), _pt(max(inner, outer), y - h), _pt(max(inner, outer), y), _pt(min(inner, outer), y)], rng.uniform(-0.1, 0.08), "jamb"))
            y -= h
        lo, hi = CX + side * (OPEN_W - 0.5), CX + side * (OUTER_W + IMPOST_PROUD)
        blocks.append(([_pt(min(lo, hi), SPRING_Y - IMPOST_H / 2), _pt(max(lo, hi), SPRING_Y - IMPOST_H / 2), _pt(max(lo, hi), SPRING_Y + IMPOST_H / 2), _pt(min(lo, hi), SPRING_Y + IMPOST_H / 2)], rng.uniform(-0.02, 0.06), "impost"))
    step = 180.0 / VOUSSOIRS
    for k in range(VOUSSOIRS):
        a0, a1 = 180.0 + k * step, 180.0 + (k + 1) * step
        key = k == VOUSSOIRS // 2
        outer = OUTER_W + (KEY_PROUD if key else 0.0)
        flare = KEY_FLARE if key else 0.0
        arc_in = [_polar(OPEN_W, a0 + (a1 - a0) * t / 6.0) for t in range(7)]
        arc_out = [_polar(outer, a1 + flare - (a1 - a0 + 2 * flare) * t / 6.0) for t in range(7)]
        if key:
            # The keystone's top is flat, not curved.
            arc_out = [_polar(outer, a1 + flare), _polar(outer, a0 - flare)]
        blocks.append((arc_in + arc_out, rng.uniform(-0.1, 0.08) + (0.06 if key else 0.0), "key" if key else "voussoir"))
    return blocks


def _block_layer() -> Image.Image:
    """The stone: each block filled in its own shade, a light edge on its
    upper left, a dark one on its lower right, its joints dark."""
    layer = Image.new("RGBA", _size(), (0, 0, 0, 0))
    draw = blending_draw(layer)
    for poly, tone, _part in _blocks():
        base = _shade(STONE, tone)
        draw.polygon(poly, fill=_rgba(base))
        # Light from the upper left: each edge lit by how much it faces it.
        n = len(poly)
        cx = sum(p[0] for p in poly) / n
        cy = sum(p[1] for p in poly) / n
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            mx, my = (a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy
            facing = (-mx - my) / max(1e-6, math.hypot(mx, my) * math.sqrt(2.0))
            if facing > 0.25:
                draw.line([a, b], fill=_rgba(_shade(base, 0.32 * facing), 230), width=int(_s(0.9)))
            elif facing < -0.25:
                draw.line([a, b], fill=_rgba(_shade(base, 0.38 * facing), 230), width=int(_s(0.9)))
        draw.line(poly + [poly[0]], fill=_rgba(MORTAR), width=int(_s(0.5)), joint="curve")
    return layer


def _weathering(layer: Image.Image) -> None:
    """Pits and lichen speckle on the stone (only where there is stone)."""
    rng = np.random.default_rng(11)
    w, h = layer.size
    alpha = np.asarray(layer.getchannel("A"), np.float32) / 255.0
    # Half-unit grains: a pixel and a half on the published sheet.
    grain = SUPER // 2
    noise = rng.random((h // grain + 1, w // grain + 1)).astype(np.float32)
    noise = np.kron(noise, np.ones((grain, grain), np.float32))[:h, :w]
    px = np.asarray(layer, np.float32)
    dark = (noise < 0.06) * 0.13
    light = (noise > 0.96) * 0.08
    rgb = px[..., :3] * (1.0 - dark[..., None]) + (255.0 - px[..., :3]) * light[..., None]
    lichen = (noise > 0.88) & (noise <= 0.95)
    rgb[lichen] = rgb[lichen] * 0.8 + np.array(MOSS_LIGHT, np.float32) * 0.2
    px[..., :3] = np.where(alpha[..., None] > 0, rgb, px[..., :3])
    layer.paste(Image.fromarray(px.clip(0, 255).astype(np.uint8), "RGBA"))


def _outline(layer: Image.Image) -> Image.Image:
    """The arch's silhouette, a stroke wide, behind it."""
    a = layer.getchannel("A").point(lambda v: 255 if v > 8 else 0)
    grown = a.filter(ImageFilter.MaxFilter(int(_s(0.8)) | 1))
    out = Image.new("RGBA", layer.size, _rgba(OUTLINE))
    out.putalpha(grown)
    out.alpha_composite(layer)
    return out


# --- the jungle --------------------------------------------------------------------


def _moss(draw) -> None:
    """Moss lying on the head's back and the threshold's top, and a few
    tufts in the joints."""
    rng = random.Random(23)
    for k in range(34):
        deg = 200.0 + rng.uniform(0.0, 140.0)
        if 262.0 < deg < 278.0:
            continue  # the keystone stays clean: the Δ is cut there
        r = OUTER_W + rng.uniform(-1.2, 0.6)
        x, y = _polar(r, deg)
        rad = _s(rng.uniform(0.9, 2.0))
        tone = MOSS if rng.random() < 0.6 else MOSS_LIGHT
        draw.ellipse((x - rad, y - rad * 0.7, x + rad, y + rad * 0.7), fill=_rgba(tone))
    for k in range(18):
        x = _s(CX + rng.uniform(-OUTER_W - 3.5, OUTER_W + 3.5))
        y = _s(THRESHOLD_Y + rng.uniform(-0.6, 0.8))
        if abs(x / SUPER - CX) < OPEN_W - 2:
            continue  # the threshold is worn clean where feet go
        rad = _s(rng.uniform(0.8, 1.6))
        draw.ellipse((x - rad, y - rad * 0.6, x + rad, y + rad * 0.6), fill=_rgba(MOSS if k % 2 else MOSS_LIGHT))
    for side in (-1, 1):
        for y in (THRESHOLD_Y - COURSES[0], THRESHOLD_Y - COURSES[0] - COURSES[1]):
            x = _s(CX + side * (OUTER_W - 1.5))
            draw.ellipse((x - _s(1.4), _s(y) - _s(0.8), x + _s(1.4), _s(y) + _s(0.8)), fill=_rgba(MOSS))


def _leaf(draw, at: Point, deg: float, length: float, tone) -> None:
    """A pointed leaf from ``at`` (drawing pixels), ``length`` units long."""
    a = math.radians(deg)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    L = _s(length)
    W = L * 0.3
    tip = (at[0] + ux * L, at[1] + uy * L)
    mid = (at[0] + ux * L * 0.45, at[1] + uy * L * 0.45)
    draw.polygon([at, (mid[0] + nx * W, mid[1] + ny * W), tip, (mid[0] - nx * W, mid[1] - ny * W)], fill=_rgba(tone))
    draw.line([at, tip], fill=_rgba(_shade(tone, -0.3)), width=max(1, int(_s(0.25))))


def _vine(draw) -> None:
    """A vine over the left shoulder, hanging down the left jamb's face."""
    rng = random.Random(5)
    pts = []
    for k in range(26):
        t = k / 25.0
        if t < 0.35:
            deg = 250.0 - t / 0.35 * 70.0
            x, y = _polar(OUTER_W + 0.6, deg)
        else:
            u = (t - 0.35) / 0.65
            x = _s(CX - OUTER_W - 0.4 + math.sin(u * 7.0) * 1.2)
            y = _s(SPRING_Y + u * 30.0)
        pts.append((x, y))
    draw.line(pts, fill=_rgba(VINE), width=int(_s(0.9)), joint="curve")
    for k, p in enumerate(pts[1::2]):
        deg = rng.uniform(100.0, 260.0) if k % 2 else rng.uniform(-80.0, 80.0)
        _leaf(draw, p, deg, rng.uniform(2.6, 3.8), LEAF if k % 3 else LEAF_LIGHT)


def _fern(draw) -> None:
    """A fern at the right foot, its fronds arching out of the step."""
    base = _pt(CX + OUTER_W + 2.0, FLOOR_Y - 0.5)
    for deg, length in ((-150.0, 9.0), (-120.0, 11.0), (-95.0, 12.0), (-70.0, 11.0), (-40.0, 9.0)):
        a = math.radians(deg)
        spine = []
        for t in range(9):
            u = t / 8.0
            bend = math.radians(deg + 40.0 * u * u * (1 if deg > -95 else -1))
            spine.append((base[0] + math.cos(a) * _s(length) * u + math.cos(bend) * _s(1.2) * u, base[1] + math.sin(a) * _s(length) * u))
        draw.line(spine, fill=_rgba(VINE), width=int(_s(0.5)), joint="curve")
        for t, p in enumerate(spine[1:-1], 1):
            size = 2.6 * (1.0 - t / 9.0) + 0.6
            _leaf(draw, p, deg + 70.0, size, LEAF_LIGHT if t % 2 else LEAF)
            _leaf(draw, p, deg - 70.0, size, LEAF if t % 2 else LEAF_LIGHT)


# --- the light ---------------------------------------------------------------------


def _delta_points(scale: float = 1.0) -> List[Point]:
    """The Δ cut in the keystone: an upright triangle at the keystone's
    middle."""
    cx, cy = CX, SPRING_Y - (OPEN_W + OUTER_W + KEY_PROUD) / 2.0
    r = 3.4 * scale
    return [_pt(cx + math.cos(math.radians(-90.0 + 120.0 * k)) * r, cy + 0.8 + math.sin(math.radians(-90.0 + 120.0 * k)) * r) for k in range(3)]


def _seam_points() -> List[Point]:
    """The opening's edge from the left threshold, up the jamb, round the
    head and down the right jamb (drawing pixels), a little inside the
    stone."""
    inset = OPEN_W - 0.4
    left = [_pt(CX - inset, THRESHOLD_Y - k * (THRESHOLD_Y - SPRING_Y) / 12.0) for k in range(13)]
    head = [_polar(inset, 180.0 + 180.0 * k / 40.0) for k in range(1, 40)]
    right = [_pt(CX + inset, SPRING_Y + k * (THRESHOLD_Y - SPRING_Y) / 12.0) for k in range(13)]
    return left + head + right


def _light_layer(core: np.ndarray, glow_radius: float, gain: float) -> Image.Image:
    """``core`` (0..1 per drawing pixel) as the gate's light: a white-cyan
    core in a cyan glow."""
    glow = Image.fromarray((core * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(glow_radius))
    g = np.asarray(glow, np.float32) / 255.0 * gain
    a = np.clip(np.maximum(core, g), 0.0, 1.0)
    rgb = np.where(core[..., None] > g[..., None], np.array(GLOW_CORE, np.float32), np.array(GLOW, np.float32))
    px = np.dstack([rgb, a * 255.0]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(px, "RGBA")


def _seam_and_key(level_key: float, seam_lit: float) -> Image.Image:
    """The keystone's Δ at ``level_key`` and the seam lit along the first
    ``seam_lit`` of each jamb's way to the keystone (0..1)."""
    size = _size()
    mask = Image.new("L", size, 0)
    md = ImageDraw.Draw(mask)  # raw-draw-ok: an L mask has no alpha to composite
    md.polygon(_delta_points(), fill=int(255 * level_key))
    if seam_lit > 0.0:
        pts = _seam_points()
        half = len(pts) // 2
        n = int(round(seam_lit * half))
        width = int(_s(0.7))
        if n >= 2:
            md.line(pts[: n], fill=255, width=width, joint="curve")
            md.line(pts[len(pts) - n :], fill=255, width=width, joint="curve")
    core = np.asarray(mask, np.float32) / 255.0
    return _light_layer(core, _s(1.6), 0.9)


def _key_level(animation: str, frame_index: int, nframes: int) -> Tuple[float, float]:
    """(how lit the Δ is, how far up the jambs the seam is lit)."""
    t = frame_index / max(1, nframes - 1)
    if animation == "idle":
        return 0.42 + 0.1 * math.sin(frame_index / max(1, nframes) * math.tau), 0.0
    climb = min(1.0, t / 0.7)
    flare = max(0.0, (t - 0.65) / 0.35)
    return min(1.0, 0.45 + 0.55 * flare), climb


# --- the frames --------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def _stone() -> Image.Image:
    """The arch at rest, unlit: stone, outline, moss, vine and fern."""
    layer = _block_layer()
    _weathering(layer)
    # The Δ is cut: a dark recess the light fills.
    draw = blending_draw(layer)
    draw.polygon(_delta_points(1.15), fill=_rgba(MORTAR))
    layer = _outline(layer)
    draw = blending_draw(layer)
    _moss(draw)
    _vine(draw)
    _fern(draw)
    return layer


def _downsample(img: Image.Image) -> Image.Image:
    return img.resize(OUT_SIZE, Image.LANCZOS)


def render_ring_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    if animation not in ("idle", "charge"):
        raise ValueError(f"unknown animation: {animation}")
    img = _stone().copy()
    key, seam = _key_level(animation, frame_index, nframes)
    img.alpha_composite(_seam_and_key(key, seam))
    return _downsample(img)


#: The wormhole on this canvas: its triangle door low in the opening,
#: everything clipped to the arch.
WORMHOLE_APERTURE = Aperture(
    units=FRAME_SIZE[0],
    centre=DOOR_CENTRE,
    door_r=DOOR_R,
    opening="arch",
    opening_r=OPEN_W - 0.6,
    arch_crown=DOOR_CENTRE[1] - (SPRING_Y - OPEN_W) - 0.6,
    arch_foot=THRESHOLD_Y - DOOR_CENTRE[1],
)


def render_portal_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    """One frame of the arch's wormhole, clipped to the opening."""
    return wormhole_frame(animation, frame_index, nframes, out_size=OUT_SIZE[0], aperture=WORMHOLE_APERTURE)


@functools.lru_cache(maxsize=1)
def _assembly_body_metrics() -> dict:
    """The arch's one body: the ring's idle frame. Both sheets publish it on
    one uncropped canvas, so the membrane lands where drawn (as the gates'
    do)."""
    return alpha_bbox_metrics(render_ring_frame("idle", 0, RING_ROWS[0][1]))


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    shared = dict(
        out_dir=out_dir,
        frame_size=OUT_SIZE,
        label_width=128,
        auto_crop=False,
        body_metrics_fn=lambda _fw, _fh: _assembly_body_metrics(),
    )
    outputs = []
    for target, rows, fn in (
        (RING_TARGET, RING_ROWS, render_ring_frame),
        (PORTAL_TARGET, PORTAL_ROWS, render_portal_frame),
    ):
        sheet = build_sheet(target=target, rows=rows, render_fn=fn, **shared)
        outputs += [sheet["canonical"], sheet["canonical_transparent"], sheet["spritesheet"], sheet["yaml"], sheet["preview"]]
    return outputs
