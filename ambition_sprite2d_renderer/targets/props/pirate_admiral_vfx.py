"""Detached VFX for the Pirate Admiral.

The admiral's effects are physical and maritime rather than magical: black
powder, cutlass steel, boarding momentum, rope tension, anchor braking, deck
splinters, and restrained navy/gold command marks.  They complement the
character renderer without baking move execution into the sprite catalog.
"""

from __future__ import annotations

import math
from pathlib import Path

from ._character_vfx_common import (
    Canvas,
    fade,
    make_spec,
    mix,
    publish_canonical,
    publish_catalog,
    pulse,
    sheet_files,
    smooth,
    window,
)

TARGET_NAME = "pirate_admiral_vfx"
SHEET_FILES = sheet_files(TARGET_NAME)
FRAME_SIZE = (144, 144)

ROWS = [
    ("black_powder_flash", 6, 38),
    ("grapeshot_cloud", 8, 52),
    ("cutlass_wake", 7, 46),
    ("cutlass_clash", 7, 48),
    ("boarding_wake", 8, 48),
    ("grapple_cast", 8, 50),
    ("grapple_tension", 10, 66),
    ("grapple_catch", 7, 46),
    ("heave_to_anchor", 9, 56),
    ("heave_to_brake", 8, 48),
    ("captains_mark", 8, 54),
    ("compass_lock", 10, 62),
    ("powder_smoke", 12, 72),
    ("deck_splinter_burst", 8, 48),
]

OUTLINE = (26, 28, 35, 255)
NAVY = (28, 31, 41, 255)
COAT = (88, 108, 138, 255)
STEEL = (210, 216, 228, 255)
STEEL_HOT = (248, 249, 242, 255)
GOLD = (206, 171, 74, 255)
GOLD_HOT = (244, 220, 132, 255)
SASH = (113, 40, 40, 255)
EMBER = (222, 72, 55, 255)
POWDER = (72, 73, 77, 255)
SMOKE = (126, 132, 140, 255)
ROPE = (178, 145, 90, 255)
ROPE_DARK = (92, 66, 43, 255)
WOOD = (151, 101, 55, 255)
WOOD_LIGHT = (214, 159, 83, 255)


def _polyline_arc(c: Canvas, center, radius: float, start: float, sweep: float, color, width: float = 2.0, segments: int = 18) -> None:
    pts = []
    for i in range(segments + 1):
        a = start + sweep * i / segments
        pts.append((center[0] + math.cos(a) * radius, center[1] + math.sin(a) * radius))
    c.line(pts, color, width)


def _smoke_blob(c: Canvas, center, radius: float, alpha: float, warm: float = 0.0) -> None:
    color = mix(SMOKE, (126, 102, 83, 255), warm)
    c.ellipse(center, radius * 1.08, radius * 0.82, fill=fade(color, 0.28 * alpha), outline=fade(STEEL, 0.10 * alpha), width=0.7)


def _black_powder_flash(c: Canvas, p: float) -> None:
    q = window(p, 0.18)
    origin = (38.0, 72.0)
    length = 24 + 44 * smooth(min(1.0, p * 2.0))
    c.star((origin[0] + length * 0.35, origin[1]), 17 + 16 * q, fade(GOLD_HOT, q), points=8, inner=0.16, rotation=0.0)
    c.star((origin[0] + length * 0.50, origin[1]), 8 + 8 * q, fade(STEEL_HOT, 0.95 * q), points=4, inner=0.18, rotation=0.0)
    c.polygon([(origin[0], 66), (origin[0] + length, 72), (origin[0], 78)], fill=fade(EMBER, 0.55 * q))
    for i in range(5):
        a = (-0.52 + i * 0.26)
        r = 19 + i * 7 + p * 14
        c.ellipse((origin[0] + 20 + math.cos(a) * r, origin[1] + math.sin(a) * r), 2.0, fill=fade(GOLD, q * (0.9 - i * 0.09)))


def _grapeshot_cloud(c: Canvas, p: float) -> None:
    q = window(p, 0.28)
    drift = 34 * p
    blobs = [(-18, -9, 13), (-3, -14, 17), (15, -7, 15), (-10, 8, 18), (11, 10, 20), (27, 4, 12)]
    for i, (dx, dy, r) in enumerate(blobs):
        _smoke_blob(c, (56 + drift + dx * (0.55 + p * 0.45), 72 + dy), r * (0.45 + 0.8 * p), q * (0.92 - i * 0.05), warm=0.18)
    for i in range(7):
        x = 48 + drift * 1.4 + i * 9 + math.sin(i * 2.1) * 4
        y = 61 + (i % 3) * 9 + math.sin(p * 5 + i) * 3
        c.ellipse((x, y), max(1.0, 3.3 - p * 1.3), fill=fade(OUTLINE, q * 0.72))


def _cutlass_wake(c: Canvas, p: float) -> None:
    q = window(p, 0.38)
    center = (62, 77)
    sweep = 0.55 + 1.55 * smooth(p)
    start = -1.25
    for i, (rad, alpha, width) in enumerate(((52, 0.20, 8.0), (48, 0.55, 3.0), (45, 0.95, 1.2))):
        _polyline_arc(c, center, rad, start, sweep, fade(STEEL_HOT if i == 2 else COAT, q * alpha), width)
    tip_a = start + sweep
    tip = (center[0] + math.cos(tip_a) * 48, center[1] + math.sin(tip_a) * 48)
    c.star(tip, 6 + 4 * q, fade(GOLD_HOT, q), points=4, inner=0.16, rotation=tip_a)


def _cutlass_clash(c: Canvas, p: float) -> None:
    q = window(p, 0.20)
    center = (72, 71)
    c.line([(31, 101), (110, 42)], fade(STEEL, 0.75 * q), 4.0)
    c.line([(36, 38), (106, 105)], fade(STEEL, 0.68 * q), 4.0)
    c.star(center, 18 + 18 * q, fade(STEEL_HOT, q), points=8, inner=0.12, rotation=math.pi / 8)
    c.star(center, 10 + 12 * q, fade(GOLD_HOT, q), points=4, inner=0.2, rotation=0.0)
    for i in range(8):
        a = i * math.tau / 8 + 0.15
        r = 20 + p * (30 + (i % 3) * 7)
        c.line([(72 + math.cos(a) * 12, 71 + math.sin(a) * 12), (72 + math.cos(a) * r, 71 + math.sin(a) * r)], fade(GOLD, q * (0.82 - i * 0.035)), 1.1)


def _boarding_wake(c: Canvas, p: float) -> None:
    q = window(p, 0.44)
    head = 38 + p * 72
    for i in range(5):
        tail = head - 12 - i * 15
        alpha = q * (0.72 - i * 0.10)
        c.polygon([(tail, 58 + i * 4), (head - i * 3, 72), (tail, 86 - i * 4)], fill=fade(COAT, alpha * 0.34), outline=fade(STEEL, alpha * 0.34), width=0.7)
    c.line([(22, 104), (122, 104)], fade(ROPE_DARK, 0.18 * q), 1.0)
    for i in range(7):
        x = 33 + i * 13 + p * 12
        c.polygon([(x, 99), (x + 5, 103), (x + 1, 108)], fill=fade(WOOD_LIGHT, q * (0.60 - i * 0.05)))


def _grapple_cast(c: Canvas, p: float) -> None:
    q = window(p, 0.48)
    origin = (28, 94)
    end = (42 + p * 78, 88 - p * 54)
    # Rope bows under its own weight early, then straightens as the hook flies.
    mid = ((origin[0] + end[0]) * 0.5, (origin[1] + end[1]) * 0.5 + 20 * (1.0 - p))
    pts = []
    for i in range(19):
        t = i / 18
        x = (1 - t) ** 2 * origin[0] + 2 * (1 - t) * t * mid[0] + t * t * end[0]
        y = (1 - t) ** 2 * origin[1] + 2 * (1 - t) * t * mid[1] + t * t * end[1]
        pts.append((x, y))
    c.line(pts, fade(ROPE, 0.90 * q), 2.2)
    c.line([(end[0] - 7, end[1] - 6), end, (end[0] - 4, end[1] + 8)], fade(STEEL, q), 2.4)
    c.arc((end[0] - 5, end[1] + 2), 8, 8, 300, 115, fade(STEEL_HOT, q), 1.8)


def _grapple_tension(c: Canvas, p: float) -> None:
    beat = pulse(p)
    start, end = (24, 102), (120, 38)
    c.line([start, end], fade(ROPE_DARK, 0.56), 4.2)
    c.line([start, end], fade(ROPE, 0.88), 2.0)
    for i in range(1, 6):
        t = i / 6
        x = start[0] + (end[0] - start[0]) * t
        y = start[1] + (end[1] - start[1]) * t
        nx, ny = 0.554, 0.832
        off = math.sin(p * math.tau * 2 + i * 1.7) * (1.2 + 1.5 * beat)
        c.line([(x - nx * 4 + nx * off, y - ny * 4 + ny * off), (x + nx * 4 + nx * off, y + ny * 4 + ny * off)], fade(GOLD, 0.42 + 0.24 * beat), 0.9)
    c.star(end, 5 + beat * 2, fade(STEEL_HOT, 0.60 + 0.3 * beat), points=4, inner=0.20)


def _grapple_catch(c: Canvas, p: float) -> None:
    q = window(p, 0.20)
    center = (88, 59)
    c.line([(25, 111), center], fade(ROPE, 0.85 * q), 2.0)
    c.arc(center, 17 + 5 * q, 17 + 5 * q, 250, 80, fade(STEEL_HOT, q), 2.4)
    c.star(center, 9 + 9 * q, fade(GOLD_HOT, q), points=6, inner=0.18, rotation=0.2)
    for i in range(5):
        a = -1.3 + i * 0.58
        c.line([center, (center[0] + math.cos(a) * (18 + 20 * p), center[1] + math.sin(a) * (18 + 20 * p))], fade(STEEL, q * (0.72 - i * 0.05)), 1.0)


def _anchor_shape(c: Canvas, center, scale: float, alpha: float) -> None:
    x, y = center
    c.line([(x, y - 28 * scale), (x, y + 18 * scale)], fade(STEEL, alpha), 4.0 * scale)
    c.ellipse((x, y - 28 * scale), 5 * scale, fill=fade(GOLD, alpha), outline=fade(OUTLINE, alpha), width=1.0)
    c.line([(x - 20 * scale, y - 13 * scale), (x + 20 * scale, y - 13 * scale)], fade(STEEL, alpha), 3.0 * scale)
    c.arc((x, y + 5 * scale), 24 * scale, 21 * scale, 18, 162, fade(STEEL, alpha), 4.0 * scale)
    c.line([(x - 22 * scale, y + 12 * scale), (x - 30 * scale, y + 5 * scale)], fade(STEEL, alpha), 3.2 * scale)
    c.line([(x + 22 * scale, y + 12 * scale), (x + 30 * scale, y + 5 * scale)], fade(STEEL, alpha), 3.2 * scale)


def _heave_to_anchor(c: Canvas, p: float) -> None:
    q = window(p, 0.48)
    y = 36 + smooth(p) * 54
    _anchor_shape(c, (72, y), 0.95, q)
    if p > 0.45:
        impact = smooth((p - 0.45) / 0.55)
        c.ellipse((72, 104), 16 + 34 * impact, 5 + 7 * impact, outline=fade(GOLD, q * (1 - impact) * 0.85), width=1.4)
        for i in range(5):
            x = 42 + i * 15
            c.polygon([(x, 101), (x + (i - 2) * 4, 92 - impact * 10), (x + 5, 105)], fill=fade(WOOD_LIGHT, q * 0.55 * (1 - impact * 0.4)))


def _heave_to_brake(c: Canvas, p: float) -> None:
    q = window(p, 0.40)
    center = (72, 74)
    for side in (-1, 1):
        for i in range(4):
            y = 54 + i * 13
            length = (20 + i * 8) * (1.0 - smooth(p) * 0.62)
            c.line([(center[0] + side * (8 + length), y), (center[0] + side * 9, y)], fade(COAT, q * (0.72 - i * 0.08)), 2.0)
    c.ellipse(center, 19 - smooth(p) * 6, outline=fade(GOLD_HOT, q * 0.92), width=2.0)
    c.line([(72, 47), (72, 101)], fade(STEEL, 0.35 * q), 1.0)
    c.line([(45, 74), (99, 74)], fade(STEEL, 0.35 * q), 1.0)


def _captains_mark(c: Canvas, p: float) -> None:
    q = window(p, 0.45)
    center = (72, 72)
    r = 20 + 25 * smooth(p)
    c.ellipse(center, r, outline=fade(GOLD, q * 0.88), width=2.2)
    c.star(center, r * 0.72, fade(COAT, 0.34 * q), points=8, inner=0.38, rotation=math.pi / 8, outline=fade(GOLD_HOT, q), width=1.0)
    c.star(center, 9 + 7 * q, fade(SASH, 0.72 * q), points=4, inner=0.28, rotation=0.0, outline=fade(GOLD_HOT, q), width=1.0)
    for i in range(4):
        a = i * math.pi / 2
        c.line([(72 + math.cos(a) * (r + 3), 72 + math.sin(a) * (r + 3)), (72 + math.cos(a) * (r + 12), 72 + math.sin(a) * (r + 12))], fade(STEEL, q * 0.55), 1.1)


def _compass_lock(c: Canvas, p: float) -> None:
    beat = 0.62 + 0.38 * pulse(p)
    center = (72, 72)
    angle = -math.pi / 2 + math.sin(p * math.tau) * 0.18
    c.ellipse(center, 42, outline=fade(GOLD, 0.55 * beat), width=1.3)
    c.ellipse(center, 29, outline=fade(COAT, 0.42 * beat), width=1.0)
    for i in range(8):
        a = i * math.pi / 4
        inner = 31 if i % 2 else 27
        c.line([(72 + math.cos(a) * inner, 72 + math.sin(a) * inner), (72 + math.cos(a) * 41, 72 + math.sin(a) * 41)], fade(STEEL, 0.48 * beat), 1.0)
    c.arrow(center, (72 + math.cos(angle) * 30, 72 + math.sin(angle) * 30), fade(EMBER, 0.92 * beat), 2.0, 6)
    c.ellipse(center, 4.0, fill=fade(GOLD_HOT, 0.94 * beat))


def _powder_smoke(c: Canvas, p: float) -> None:
    beat = pulse(p)
    for i in range(7):
        phase = (p + i * 0.143) % 1.0
        x = 64 + math.sin(i * 2.31 + p * math.tau) * (7 + phase * 11)
        y = 112 - phase * 84
        r = 7 + 13 * phase
        alpha = (1.0 - phase) * (0.34 + 0.18 * beat)
        _smoke_blob(c, (x, y), r, alpha, warm=0.08 + 0.10 * (i % 2))
    for i in range(3):
        phase = (p * 1.4 + i * 0.33) % 1.0
        c.ellipse((66 + math.sin(i * 2.2) * 9, 111 - phase * 58), 1.6 + phase, fill=fade(EMBER, (1 - phase) * 0.55))


def _deck_splinter_burst(c: Canvas, p: float) -> None:
    q = window(p, 0.22)
    origin = (72, 91)
    for i in range(11):
        a = -2.75 + i * 0.22
        speed = 22 + (i % 4) * 9
        x = origin[0] + math.cos(a) * speed * p
        y = origin[1] + math.sin(a) * speed * p + 26 * p * p
        dx = math.cos(a) * (5 + (i % 3) * 3)
        dy = math.sin(a) * (5 + (i % 3) * 3)
        c.polygon([(x - dy * 0.25, y + dx * 0.25), (x + dx, y + dy), (x + dy * 0.25, y - dx * 0.25)], fill=fade(WOOD_LIGHT if i % 2 else WOOD, q * (0.92 - i * 0.035)), outline=fade(ROPE_DARK, q * 0.52), width=0.5)
    c.ellipse(origin, 12 + p * 32, 4 + p * 7, outline=fade(GOLD, q * (1 - p) * 0.56), width=1.1)


DRAWERS = {
    "black_powder_flash": _black_powder_flash,
    "grapeshot_cloud": _grapeshot_cloud,
    "cutlass_wake": _cutlass_wake,
    "cutlass_clash": _cutlass_clash,
    "boarding_wake": _boarding_wake,
    "grapple_cast": _grapple_cast,
    "grapple_tension": _grapple_tension,
    "grapple_catch": _grapple_catch,
    "heave_to_anchor": _heave_to_anchor,
    "heave_to_brake": _heave_to_brake,
    "captains_mark": _captains_mark,
    "compass_lock": _compass_lock,
    "powder_smoke": _powder_smoke,
    "deck_splinter_burst": _deck_splinter_burst,
}

SPECS = {
    "black_powder_flash": make_spec("black_powder", "Short hot pistol flash with ember-rich black-powder character.", placement="source", orientation="positive_x_is_forward", mirror_x=True, relationship="release", extra_anchor="emitter", size=104),
    "grapeshot_cloud": make_spec("black_powder", "Wide dirty powder cloud and scattered shot residue after grapeshot release.", placement="source", orientation="positive_x_is_forward", mirror_x=True, relationship="aftermath", extra_anchor="emitter", size=122),
    "cutlass_wake": make_spec("cutlass", "Heavy steel cutting arc with a gold-hot terminal glint; reads as weight rather than energy magic.", placement="source", orientation="positive_x_is_forward", mirror_x=True, relationship="active", extra_anchor="emitter", size=126),
    "cutlass_clash": make_spec("cutlass", "Crossed-steel impact star for parries, blade clashes, and hard metal contact.", placement="hit_point", relationship="impact", extra_anchor="contact", size=112),
    "boarding_wake": make_spec("boarding", "Triangular momentum wake and deck flecks for the admiral's additive boarding charge.", placement="source", orientation="positive_x_is_forward", mirror_x=True, relationship="active", size=132),
    "grapple_cast": make_spec("grapple", "Visible rope cast with hook-tip silhouette; presentation of the line being thrown, not an independently simulated projectile.", placement="source", orientation="positive_x_is_forward", mirror_x=True, rotate_safe=False, relationship="release", extra_anchor="emitter", size=138),
    "grapple_tension": make_spec("grapple", "Looping taut rope line with tiny transverse tension ticks; intended to persist while the haul owns movement.", loop=True, placement="source", orientation="positive_x_is_forward", mirror_x=True, rotate_safe=False, relationship="sustain", extra_anchor="emitter", size=138),
    "grapple_catch": make_spec("grapple", "Hook catch flash and rope convergence at the contacted stage point.", placement="target", relationship="impact", extra_anchor="target", size=116),
    "heave_to_anchor": make_spec("anchor", "Anchor-shaped braking mark slams down into a flattened deck ring; a visual metaphor for the move's commanded full stop.", placement="source", relationship="active", extra_anchor="origin", size=122),
    "heave_to_brake": make_spec("braking", "Lateral motion streaks collapse inward around a centered stop-ring.", placement="source", orientation="positive_x_is_forward", mirror_x=True, relationship="active", size=128),
    "captains_mark": make_spec("command", "Restrained navy-and-gold compass-rose command seal for leader-only confirmations and orders.", placement="world", relationship="release", size=116),
    "compass_lock": make_spec("navigation", "Looping compass rose whose red needle settles and breathes around a chosen heading.", loop=True, placement="source", relationship="sustain", size=112),
    "powder_smoke": make_spec("black_powder", "Looping rising powder-smoke wisps with occasional dying embers for lingering firearm aftermath.", loop=True, placement="source", attachment="source_follow", relationship="sustain", extra_anchor="emitter", size=104),
    "deck_splinter_burst": make_spec("deck_contact", "Physical wood splinters fan from a deck-level impact without turning debris into gameplay physics.", placement="surface", relationship="impact", extra_anchor="contact", size=122),
}

ORIGINS = {name: (72.0, 72.0) for name, _, _ in ROWS}
ORIGINS.update({
    "black_powder_flash": (38.0, 72.0),
    "grapeshot_cloud": (38.0, 72.0),
    "cutlass_wake": (60.0, 80.0),
    "boarding_wake": (34.0, 72.0),
    "grapple_cast": (28.0, 94.0),
    "grapple_tension": (24.0, 102.0),
    "grapple_catch": (88.0, 59.0),
    "powder_smoke": (66.0, 112.0),
    "deck_splinter_burst": (72.0, 91.0),
})


def render(out_dir: str | Path, **opts):
    del opts
    return publish_catalog(
        target_name=TARGET_NAME,
        display_name="Pirate Admiral Detached VFX",
        character_context_id="npc_pirate_admiral",
        character_context_display="Pirate Admiral",
        rows=ROWS,
        drawers=DRAWERS,
        specs=SPECS,
        origins=ORIGINS,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
    )


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return publish_canonical(
        target_name=TARGET_NAME,
        rows=ROWS,
        drawers=DRAWERS,
        specs=SPECS,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
    )
