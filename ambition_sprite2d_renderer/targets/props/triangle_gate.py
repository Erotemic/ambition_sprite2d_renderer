"""The triangle gate: the interdimensional gate reshaped into a triangle,
the gate network's main look (Jon, 2026-10-31: "turn the arch gate into more
of a triangle to go with the triangle theme more"; "I don't want it to look
too different from the gate ... the chevrons with the glyphs on it. They are
just along the sides now but the delta remains on the top. The old portal
effect should be reusable here with different clipping, and parts of the
chevrons should be reusable too. Don't completely rework the art, just
reshape it."; "the circle variant and triangle variant of the gates be
things we can place. Let's make the triangle the main variant though. Put
the circle as the gate for the jungle dimension.").

It is the round gate's own parts (``interdimensional_gate``) on a triangle:

- the BAND: the ring's bronze band, its concentric lines and its ticks,
  laid round an upright triangle, lit by the same light
  (``_shade_triangle_band``: the ring's torus shading across a straight
  band);
- the CHEVRONS: the ring's plaques (``PLAQUE_OUTER``/``PLAQUE_FACE``), their
  position-grid sockets and their glyphs, a little smaller
  (``CHEVRON_SCALE``): ΛΕΓΑΛΛΥ up the left side, the Δ at the apex,
  ΙΣΤΙΝΧΤ down the right side, each foot facing the opening;
- the CLAMPS: the ring's three lamp clamps, on the triangle's corners (the
  ring's stand at 12, 4 and 8 o'clock, where a triangle's corners are);
- the BASE: the ring's stepped base, its steps rising to the threshold at
  the opening's foot;
- the MEMBRANE: the ring's wormhole (``_gate_wormhole_triangles``), its door
  a little inside the triangular opening and clipped to it.

Three sheets of one assembly, on one canvas (``FRAME_SIZE``), as the round
gate's, with the same rows: ``_ring`` (``idle``, ``charge``), ``_portal``
(``PORTAL_ROWS``) and ``_glyphs`` (``idle``, ``lit``, ``bit``, ``used``: a
dialed chevron's glyph and its grid cells, where this frame draws them).
A travel portal (a ring of kind ``Portal``) wears the same frame and lights
no glyphs.

Portals are never painted into scenery: these sheets ARE the gate's
presentation. No drop shadows.
"""

from __future__ import annotations

import functools
import math
from pathlib import Path
from typing import List, Sequence, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ...authoring.sheet_build import alpha_bbox_metrics, build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw
from ambition_sprite2d_renderer.glyphs.legally_distinct import GLYPHS, Placement, glyphs_mask

from . import interdimensional_gate as gate
from ._gate_wormhole_triangles import Aperture, render_portal_frame as wormhole_frame

Point = Tuple[float, float]

TARGET_NAME = "triangle_gate"
RING_TARGET = f"{TARGET_NAME}_ring"
PORTAL_TARGET = f"{TARGET_NAME}_portal"
GLYPHS_TARGET = f"{TARGET_NAME}_glyphs"

RING_ROWS = gate.RING_ROWS
PORTAL_ROWS = gate.PORTAL_ROWS
GLYPH_ROWS = gate.GLYPH_ROWS

SHEET_FILES = [
    f"{RING_TARGET}_spritesheet.png",
    f"{RING_TARGET}_spritesheet.yaml",
    f"{PORTAL_TARGET}_spritesheet.png",
    f"{PORTAL_TARGET}_spritesheet.yaml",
    f"{GLYPHS_TARGET}_spritesheet.png",
    f"{GLYPHS_TARGET}_spritesheet.yaml",
]

# --- geometry (design units, y down; published at 2 px a unit) ---------------

FRAME_SIZE = (224, 224)
SUPER = gate.SUPER
OUT_SIZE = (FRAME_SIZE[0] * 2, FRAME_SIZE[1] * 2)

#: The band, across (the round ring's is 24).
BAND = 22.0
#: The opening's inradius and the band's outer edge's: all the triangles
#: share the centroid ``CENTROID`` and point up.
OPEN_IN_R = 28.0
OUTER_IN_R = OPEN_IN_R + BAND
#: The band's middle line, where the chevrons sit (the ring's
#: ``RING_MID_R``).
MID_IN_R = (OPEN_IN_R + OUTER_IN_R) / 2.0
#: The wormhole's door: inscribed in the opening, its edges ``DOOR_INSET``
#: inside the opening's.
DOOR_INSET = 2.0
DOOR_R = 2.0 * (OPEN_IN_R - DOOR_INSET)
#: The corner caps' size (see ``CORNER_DEGS``).
CORNER_CAP_HEIGHT = 14.0
CORNER_CAP_PROUD = 1.6
#: The triangle is set into a pedestal (Jon, 2026-10-31: "the gate to be
#: placed on the pedestal, rather than the pedestal in front of the gate"),
#: the opening's foot level with the pedestal's top, ``PEDESTAL_TOP`` ("the
#: bottom edge of the wormhole part aligned to the base of the pedestal (so
#: you can walk in)"). The plinth hides the band's foot as wide as the band
#: is at its top; the corners stand on the floor either side.
CENTROID = (FRAME_SIZE[0] / 2.0, 138.0)
PEDESTAL_TOP = CENTROID[1] + OPEN_IN_R
FLOOR = CENTROID[1] + OUTER_IN_R + CORNER_CAP_PROUD
#: The pedestal: the PLINTH's half width (the outer triangle's at the
#: pedestal's top), and in front of it the ring's flight of STAIRS climbing
#: from the floor to the opening's foot (Jon: "we still want the look of
#: stairs up to the gate"), each (half width, rise), bottom up.
PLINTH_HALF = (PEDESTAL_TOP - (CENTROID[1] - 2.0 * OUTER_IN_R)) / math.sqrt(3.0)
STAIRS = ((PLINTH_HALF - 6.0, (FLOOR - PEDESTAL_TOP) / 3.0), (PLINTH_HALF - 14.0, (FLOOR - PEDESTAL_TOP) / 3.0), (PLINTH_HALF - 22.0, (FLOOR - PEDESTAL_TOP) / 3.0))
#: The ring's plaques, glyphs and grids at this size on the sides, and the
#: Δ's at the apex, at the ring's own size (Jon: "make the delta chevron a
#: bit bigger").
CHEVRON_SCALE = 0.85
APEX_CHEVRON_SCALE = 1.0
#: Chevrons along a side: the distance between neighbours. Each side's row
#: slides up until its top chevron locks against the Δ (Jon: "slide the
#: chevrons up a bit so they lock in and are tight against the delta"), as
#: close as side neighbours are to each other ("the minimum distance between
#: two chevrons is constant and equal for all neighbors"; ``_chevron_slide``).
CHEVRON_PITCH = 15.6

#: The sides, by their outward normals (degrees, y down): the foot, the left
#: side (its chevrons read bottom to top) and the right (top to bottom).
FOOT_NORMAL_DEG = 90.0
LEFT_NORMAL_DEG = 210.0
RIGHT_NORMAL_DEG = 330.0
#: The apex chevron, the Δ, and the chevrons on each side of it.
APEX_DEG = -90.0
APEX_INDEX = 7
PER_SIDE = 7
#: The ring's three clamps (its lamps at 12, 4 and 8 o'clock), reshaped for
#: the triangle's corners: each a CORNER CAP, a small equilateral triangle
#: hugging the band's corner (``CORNER_CAP_HEIGHT`` from its tip to its inner
#: edge, standing ``CORNER_CAP_PROUD`` proud of the band), its lamp at its
#: middle. The lower two stand on the floor either side of the plinth.
CORNER_DEGS = (-90.0, 30.0, 150.0)

assert len(GLYPHS) == 2 * PER_SIDE + 1 and GLYPHS[APEX_INDEX].letter == "Δ"


def _s(v: float) -> float:
    """Design units to drawing pixels."""
    return v * SUPER


def _unit(deg: float) -> Point:
    rad = math.radians(deg)
    return (math.cos(rad), math.sin(rad))


def _from_centroid(normal_deg: float, out: float, along: float = 0.0) -> Point:
    """The drawing pixel ``out`` design units from the centroid along a
    side's normal and ``along`` units along the side (clockwise)."""
    n, t = _unit(normal_deg), _unit(normal_deg + 90.0)
    return (
        _s(CENTROID[0]) + _s(n[0] * out + t[0] * along),
        _s(CENTROID[1]) + _s(n[1] * out + t[1] * along),
    )


def _triangle(in_r: float) -> List[Point]:
    """An upright triangle about the centroid, inradius ``in_r`` design
    units, in drawing pixels: apex, lower right, lower left."""
    return [_from_centroid(a, 2.0 * in_r) for a in CORNER_DEGS]


def _draw_band_outline(draw, in_r: float, *, fill=None, outline=None, width: int = 1) -> None:
    """One of the band's concentric triangles (the ring's concentric
    circles): filled, outlined, or both."""
    pts = _triangle(in_r)
    if fill is not None:
        draw.polygon(pts, fill=fill)
    if outline is not None:
        draw.line(pts + [pts[0]], fill=outline, width=width, joint="curve")


# --- the chevrons ---------------------------------------------------------------


def _chevron_pose(index: int) -> Tuple[Point, float]:
    """Where chevron ``index``'s plaque stands (drawing pixels), and the way
    it points out (degrees): the ring's ray, here its side's normal.
    ΛΕΓΑΛΛΥ climbs the left side, the Δ tops the apex, ΙΣΤΙΝΧΤ runs down
    the right side."""
    if index == APEX_INDEX:
        return _from_centroid(APEX_DEG, 2.0 * MID_IN_R - 3.0), APEX_DEG
    left = index < APEX_INDEX
    # Counted from the apex: 0 is the chevron next to the Δ.
    from_apex = PER_SIDE - 1 - index if left else index - APEX_INDEX - 1
    up = _chevron_slide() - from_apex * CHEVRON_PITCH
    # The left side's clockwise way is up, the right side's down.
    normal = LEFT_NORMAL_DEG if left else RIGHT_NORMAL_DEG
    return _from_centroid(normal, MID_IN_R, up if left else -up), normal


def _convex_gap(a: Sequence[Point], b: Sequence[Point]) -> float:
    """The distance between two convex polygons; 0 when they overlap."""

    def edges(poly):
        return [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]

    def separated() -> bool:
        for p, q in edges(a) + edges(b):
            nx, ny = q[1] - p[1], p[0] - q[0]
            pa = [x * nx + y * ny for x, y in a]
            pb = [x * nx + y * ny for x, y in b]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return True
        return False

    def to_segment(pt, p, q) -> float:
        vx, vy = q[0] - p[0], q[1] - p[1]
        t = max(0.0, min(1.0, ((pt[0] - p[0]) * vx + (pt[1] - p[1]) * vy) / max(vx * vx + vy * vy, 1e-9)))
        return math.hypot(pt[0] - p[0] - vx * t, pt[1] - p[1] - vy * t)

    if not separated():
        return 0.0
    return min(
        min(to_segment(pt, p, q) for pt in a for p, q in edges(b)),
        min(to_segment(pt, p, q) for pt in b for p, q in edges(a)),
    )


def _chevron_scale(index: int) -> float:
    return APEX_CHEVRON_SCALE if index == APEX_INDEX else CHEVRON_SCALE


@functools.lru_cache(maxsize=1)
def _chevron_slide() -> float:
    """How far up its side (design units from the side's middle) the
    chevron next to the Δ stands: as far as it goes before its plaque comes
    as close to the Δ's as two side neighbours are to each other. Measured
    on the plaques' outlines, so a change of size or place keeps them
    locked."""

    def outline(at: Point, out: float, scale: float) -> List[Point]:
        turn = math.radians(out + 90.0)
        c, s = math.cos(turn), math.sin(turn)
        return [(at[0] + x * scale * c - y * scale * s, at[1] + x * scale * s + y * scale * c) for x, y in gate.PLAQUE_OUTER]

    apex = outline(*_chevron_pose(APEX_INDEX), APEX_CHEVRON_SCALE)
    gap = _convex_gap(
        outline(_from_centroid(LEFT_NORMAL_DEG, MID_IN_R, 0.0), LEFT_NORMAL_DEG, CHEVRON_SCALE),
        outline(_from_centroid(LEFT_NORMAL_DEG, MID_IN_R, CHEVRON_PITCH), LEFT_NORMAL_DEG, CHEVRON_SCALE),
    )
    lo, hi = 0.0, math.sqrt(3.0) * MID_IN_R
    for _ in range(40):
        mid = (lo + hi) / 2.0
        plaque = outline(_from_centroid(LEFT_NORMAL_DEG, MID_IN_R, mid), LEFT_NORMAL_DEG, CHEVRON_SCALE)
        if _convex_gap(plaque, apex) > gap:
            lo = mid
        else:
            hi = mid
    return lo


def _scaled(points: Sequence[Point], scale: float) -> List[Point]:
    return [(x * scale, y * scale) for x, y in points]


def _draw_chevron_plaque(draw, index: int) -> None:
    """Chevron ``index``'s plaque: the ring's bronze pentagon pointing at
    the opening, its dark face where the glyph is cut."""
    at, out = _chevron_pose(index)
    k = _chevron_scale(index)
    gate._draw_rotated_polygon(draw, at, _scaled(gate.PLAQUE_OUTER, k), out + 90.0, fill=gate._rgba(gate.PLAQUE), outline=gate._rgba(gate.OUTLINE), width=4)
    gate._draw_rotated_polygon(draw, at, _scaled(gate.PLAQUE_FACE, k), out + 90.0, fill=gate._rgba(gate.PLAQUE_INK), outline=gate._rgba(gate.BRONZE_LIGHT), width=2)


def _chevron_grid_cell(index: int, row: int, col: int) -> Point:
    """The centre of cell (row, col) of chevron ``index``'s position grid,
    as on the ring: row 0 the outermost, column 0 the left one as the plaque
    stands upright."""
    at, out = _chevron_pose(index)
    turn = math.radians(out + 90.0)
    k = _chevron_scale(index)
    pitch = gate.GRID_PITCH * k
    lx = (col - (gate.GRID_COLS - 1) / 2.0) * pitch
    ly = gate.GRID_Y * k + (row - (gate.GRID_ROWS - 1) / 2.0) * pitch
    return (at[0] + lx * math.cos(turn) - ly * math.sin(turn), at[1] + lx * math.sin(turn) + ly * math.cos(turn))


def _draw_chevron_grid_sockets(draw, index: int) -> None:
    """Chevron ``index``'s sixteen empty sockets."""
    r = gate.GRID_DOT * _chevron_scale(index)
    for row in range(gate.GRID_ROWS):
        for col in range(gate.GRID_COLS):
            x, y = _chevron_grid_cell(index, row, col)
            draw.rectangle((x - r, y - r, x + r, y + r), fill=gate._rgba("#070a0c"))


def _chevron_glyph_placement(index: int) -> Placement:
    """Glyph ``index`` on its plaque, its foot toward the opening (its up
    the plaque's outward way), set in toward the opening as on the ring."""
    at, out = _chevron_pose(index)
    n = _unit(out)
    k = _chevron_scale(index)
    inset = gate.GLYPH_INSET * k
    return Placement(GLYPHS[index], (at[0] - n[0] * inset, at[1] - n[1] * inset), gate.GLYPH_CAP * k, out + 90.0)


def _chevron_glyph_light(levels: List[float]) -> Image.Image:
    """Every glyph cut into its plaque, each lit at its own level (0..1):
    the ring's ``_ring_glyphs`` on these chevrons."""
    size = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)
    core = np.zeros((size[1], size[0]), np.float32)
    glow = np.zeros_like(core)
    for index, level in enumerate(levels):
        m = glyphs_mask([_chevron_glyph_placement(index)], size)
        core = np.maximum(core, m * (0.62 + 0.34 * level))
        glow = np.maximum(glow, m * (0.18 + 0.4 * level))
    return gate._light_layer(core, glow, 1.6 * SUPER, core_rgb=(104, 214, 232))


# --- the band, the clamps and the base -------------------------------------------


def _shade_triangle_band(layer: Image.Image) -> None:
    """Light the band's metal from the upper left, in place: the ring's
    torus shading (``_shade_metal``) across a straight band, its outer half
    facing away from the opening and its inner half toward it, square to
    its side. Alpha is not changed."""
    px = np.asarray(layer, dtype=np.float32)
    h, w = px.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = xs - _s(CENTROID[0]), ys - _s(CENTROID[1])
    normals = [_unit(a) for a in (FOOT_NORMAL_DEG, LEFT_NORMAL_DEG, RIGHT_NORMAL_DEG)]
    # A pixel belongs to the side it is farthest out from.
    out = np.stack([dx * nx + dy * ny for nx, ny in normals])
    side = np.argmax(out, axis=0)
    nxs = np.array([n[0] for n in normals], np.float32)[side]
    nys = np.array([n[1] for n in normals], np.float32)[side]
    across = np.clip((np.max(out, axis=0) - _s(MID_IN_R)) / _s(BAND / 2.0), -1.0, 1.0)
    nx, ny = nxs * across, nys * across
    nz = np.sqrt(np.clip(1.0 - across * across, 0.0, 1.0))
    light = np.array([-0.55, -0.62, 0.56], dtype=np.float32)
    light /= np.linalg.norm(light)
    lit = nx * light[0] + ny * light[1] + nz * light[2]
    gain = 0.62 + 0.62 * np.clip(lit, 0.0, 1.0)
    spec = np.clip(lit, 0.0, 1.0) ** 18 * 70.0
    px[..., :3] = np.clip(px[..., :3] * gain[..., None] + spec[..., None], 0.0, 255.0)
    layer.paste(Image.fromarray(px.astype(np.uint8), "RGBA"))


def _draw_band_ticks(draw) -> None:
    """The ring's engraved ticks across the band, square to each side:
    dark ones at an even pitch, every third a lighter one."""
    steps = 13
    for normal in (FOOT_NORMAL_DEG, LEFT_NORMAL_DEG, RIGHT_NORMAL_DEG):
        inner, outer = OPEN_IN_R + 4.5, OUTER_IN_R - 4.5
        for k in range(steps + 1):
            u = -1.0 + 2.0 * k / steps
            p1 = _from_centroid(normal, inner, u * math.sqrt(3.0) * inner)
            p2 = _from_centroid(normal, outer, u * math.sqrt(3.0) * inner)
            light = k % 3 == 1
            draw.line([p1, p2], fill=gate._rgba("#d2ab78", 80) if light else gate._rgba(gate.BRONZE_DARK, 115), width=2)


def _corner_cap(corner_deg: float, height: float, proud: float) -> List[Point]:
    """A corner cap's outline (drawing pixels): the corner of the band's
    outer triangle grown ``proud`` units, cut square to the corner's
    bisector ``height`` units in from its tip: an equilateral triangle
    pointing out of the corner."""
    tip = 2.0 * (OUTER_IN_R + proud)
    side = height * 2.0 / math.sqrt(3.0)
    base = tip - height
    return [
        _from_centroid(corner_deg, tip),
        _from_centroid(corner_deg, base, side / 2.0),
        _from_centroid(corner_deg, base, -side / 2.0),
    ]


def _draw_corner_clamp(layer: Image.Image, draw, lamp_index: int, level: float) -> None:
    """The ring's clamp on corner ``lamp_index`` (apex, lower right, lower
    left), reshaped for a corner: a bronze CORNER CAP with a lit bevel
    inside it, and the ring's triangular lamp at its middle pointing out of
    the corner."""
    ang = CORNER_DEGS[lamp_index]
    cap = _corner_cap(ang, CORNER_CAP_HEIGHT, CORNER_CAP_PROUD)
    draw.polygon(cap, fill=gate._rgba("#6b5034"))
    draw.line(cap + [cap[0]], fill=gate._rgba(gate.OUTLINE), width=4, joint="curve")
    face = _corner_cap(ang, CORNER_CAP_HEIGHT - 3.2, CORNER_CAP_PROUD - 1.6)
    draw.line(face + [face[0]], fill=gate._rgba(gate.BRONZE_LIGHT, 150), width=2, joint="curve")
    middle = 2.0 * (OUTER_IN_R + CORNER_CAP_PROUD) - CORNER_CAP_HEIGHT * 2.0 / 3.0
    gate._draw_clamp_lamp(layer, _from_centroid(ang, middle), ang, level)


def _draw_step(draw, half: float, top: float, bottom: float) -> None:
    """One bronze-stone block of the ring's base, ``half`` units either side
    of the centre from ``top`` down to ``bottom``: its face, the lit lip of
    its tread and the shadow line under the lip."""
    cx = _s(CENTROID[0])
    x0, x1, y0 = cx - _s(half), cx + _s(half), _s(top)
    draw.rectangle((x0, y0, x1, _s(bottom)), fill=gate._rgba("#5a4330"), outline=gate._rgba(gate.OUTLINE), width=4)
    draw.rectangle((x0 + 4, y0 + 4, x1 - 4, y0 + _s(2.2)), fill=gate._rgba("#a58258"))
    draw.rectangle((x0 + 4, y0 + _s(2.2), x1 - 4, y0 + _s(3.0)), fill=gate._rgba(gate.BRONZE_DARK))


def _draw_pedestal(img: Image.Image, lit: float) -> None:
    """The pedestal the triangle is set into: the PLINTH over the middle of
    its foot, and the ring's STAIRS in front, rising from the floor to the
    plinth's top (the opening's foot);
    the cyan line across the top stair, under the opening, ``lit`` (0..1)
    bright."""
    draw = blending_draw(img)
    _draw_step(draw, PLINTH_HALF, PEDESTAL_TOP, FLOOR)
    bottom = FLOOR
    for half, rise in STAIRS:
        top = bottom - rise
        _draw_step(draw, half, top, bottom + 0.5)
        bottom = top
    cx = _s(CENTROID[0])
    half = STAIRS[-1][0] - 14.0
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = blending_draw(glow)
    y = _s(PEDESTAL_TOP) + _s(1.0)
    gd.rectangle((cx - _s(half), y - 2, cx + _s(half), y + 2), fill=gate._rgba("#7ff3ff", int(255 * lit)))
    glow = glow.filter(ImageFilter.GaussianBlur(1.2 * SUPER))
    img.alpha_composite(glow)
    draw = blending_draw(img)
    draw.rectangle((cx - _s(half), y - 1, cx + _s(half), y + 1), fill=gate._rgba("#e6fdff", int(230 * lit)))


def _draw_triangle_frame(*, frame_index: int, nframes: int, idle_mode: bool) -> Image.Image:
    """The whole frame: the ring's band round the triangle, its chevrons,
    its clamps, the opening's cyan rim and the base."""
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    band = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = blending_draw(band)
    # The ring's concentric lines, as triangles (its offsets scaled to this
    # band).
    k = BAND / 24.0
    _draw_band_outline(bd, OUTER_IN_R, fill=gate._rgba(gate.BRONZE), outline=gate._rgba(gate.OUTLINE), width=12)
    _draw_band_outline(bd, OUTER_IN_R - 5 * k, outline=gate._rgba(gate.BRONZE_LIGHT), width=5)
    _draw_band_outline(bd, OUTER_IN_R - 9 * k, outline=gate._rgba(gate.BRONZE_DARK), width=6)
    _draw_band_outline(bd, OUTER_IN_R - 14 * k, fill=gate._rgba("#8a6842"), outline=gate._rgba(gate.BRONZE_LIGHT), width=3)
    _draw_band_outline(bd, OPEN_IN_R + 7 * k, fill=gate._rgba("#4d3824"), outline=gate._rgba("#a07d55"), width=4)
    # The opening: cut clear (a zero-alpha fill erases), then its dark lip.
    _draw_band_outline(bd, OPEN_IN_R, fill=(0, 0, 0, 0))
    _draw_band_outline(bd, OPEN_IN_R, outline=gate._rgba(gate.OUTLINE), width=8)
    _shade_triangle_band(band)
    _draw_band_ticks(bd)

    # The chevrons, then their glyphs: at rest breathing faintly out of step
    # with their neighbours, charging lit by the ring's pulse.
    for index in range(len(GLYPHS)):
        _draw_chevron_plaque(bd, index)
        _draw_chevron_grid_sockets(bd, index)
    if idle_mode:
        levels = [gate._rune_glow(frame_index, nframes, index * 2, dim=True) for index in range(len(GLYPHS))]
    else:
        levels = [gate._charge_level(index, frame_index, nframes) for index in range(len(GLYPHS))]
    band.alpha_composite(_chevron_glyph_light(levels))

    for lamp_index in range(len(CORNER_DEGS)):
        _draw_corner_clamp(band, bd, lamp_index, gate._lamp_level(lamp_index, frame_index, nframes, idle_mode))

    band = band.filter(ImageFilter.GaussianBlur(radius=0.25))
    img.alpha_composite(band)

    # The opening's cyan rim (the ring's inner glow).
    rim = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rd = blending_draw(rim)
    alpha = 78 if idle_mode else 106
    _draw_band_outline(rd, OPEN_IN_R + 2.5, outline=gate._rgba("#5fe2ff", alpha), width=4)
    _draw_band_outline(rd, OPEN_IN_R + 3.9, outline=gate._rgba("#a8f2ff", alpha // 2), width=2)
    rim = rim.filter(ImageFilter.GaussianBlur(radius=2.5))
    img.alpha_composite(rim)
    # The pedestal over the middle of the band's foot.
    _draw_pedestal(img, lit=0.55 if idle_mode else 0.55 + 0.45 * (frame_index + 1) / max(1, nframes))
    return img


def _downsample(img: Image.Image) -> Image.Image:
    return img.resize(OUT_SIZE, Image.Resampling.LANCZOS)


def render_ring_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    if animation not in ("idle", "charge"):
        raise ValueError(f"{RING_TARGET}: no row {animation!r}")
    return _downsample(_draw_triangle_frame(frame_index=frame_index, nframes=nframes, idle_mode=animation == "idle"))


def render_glyph_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    """The round gate's glyph sheet on these chevrons: chevron
    ``frame_index`` dialed (its glyph blazing, its plaque's face washed with
    its light), or one cell of a chevron's grid set (``bit``) or used."""
    if animation not in ("idle", "lit", "bit", "used"):
        raise ValueError(f"{GLYPHS_TARGET}: no row {animation!r}")
    del nframes
    size = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)
    if animation == "idle":
        return _downsample(Image.new("RGBA", size, (0, 0, 0, 0)))
    if animation in ("bit", "used"):
        index, cell = divmod(frame_index, gate.GRID_CELLS)
        x, y = _chevron_grid_cell(index, *divmod(cell, gate.GRID_COLS))
        dot = Image.new("L", size, 0)
        r = gate.GRID_DOT * _chevron_scale(index) * (1.0 if animation == "bit" else 0.7)
        ImageDraw.Draw(dot).rectangle((x - r, y - r, x + r, y + r), fill=255)  # raw-draw-ok: an L mask has no alpha to composite
        core = np.asarray(dot, np.float32) / 255.0
        if animation == "bit":
            return _downsample(gate._light_layer(core, core * 0.6, 0.5 * SUPER, core_rgb=(255, 255, 255)))
        return _downsample(gate._light_layer(core, core * 0.0, 0.3 * SUPER, core_rgb=(48, 150, 184)))
    core = glyphs_mask([_chevron_glyph_placement(frame_index)], size)
    wash = Image.new("L", size, 0)
    at, out = _chevron_pose(frame_index)
    gate._draw_rotated_polygon(
        ImageDraw.Draw(wash),  # raw-draw-ok: an L mask has no alpha to composite
        at,
        _scaled(gate.PLAQUE_FACE, _chevron_scale(frame_index)),
        out + 90.0,
        fill=255,
    )
    glow = np.maximum(core, np.asarray(wash, np.float32) / 255.0 * 0.2)
    return _downsample(gate._light_layer(core, glow, 2.6 * SUPER, core_rgb=(236, 255, 255)))


# --- the membrane ---------------------------------------------------------------

#: The ring's wormhole on this canvas: its door inside the triangular
#: opening, everything clipped to the opening.
WORMHOLE_APERTURE = Aperture(
    units=FRAME_SIZE[0],
    centre=CENTROID,
    door_r=DOOR_R,
    opening="triangle",
    opening_r=2.0 * OPEN_IN_R,
)


def render_portal_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    """One frame of the ring's wormhole, clipped to the triangle."""
    return wormhole_frame(animation, frame_index, nframes, out_size=OUT_SIZE[0], aperture=WORMHOLE_APERTURE)


@functools.lru_cache(maxsize=1)
def _assembly_body_metrics() -> dict:
    """The gate's one body: the ring's idle frame. Every sheet publishes it
    on one uncropped canvas, so the membrane and the lit glyphs land where
    drawn (as the round gate's do)."""
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
        (GLYPHS_TARGET, GLYPH_ROWS, render_glyph_frame),
    ):
        sheet = build_sheet(target=target, rows=rows, render_fn=fn, **shared)
        outputs += [sheet["canonical"], sheet["canonical_transparent"], sheet["spritesheet"], sheet["yaml"], sheet["preview"]]
    return outputs
