"""The effects of the giant gnu's blows through a portal (GNU-ton's fight).

A blow of the giant goes into a portal's line by its body and comes out of a
line by the player. These effects are the weight of it, drawn in the giant's
own ink and colours:

* ``gnu_blow_glint`` — a star of light where the limb will come out: the blow
  is cocked and goes NOW (it plays as the giant draws back the last of the way).
* ``gnu_blow_streak`` — the lines of speed of a limb that comes out of a line,
  drawn along +X (the way it comes); the game turns it to the line's normal.
* ``gnu_hammer_quake`` — a fist into the floor: the floor cracks, a ring of
  dust goes out flat along it each way, and stones jump.
* ``gnu_blow_impact`` — a blow that lands on a body: a burst, and its shards.

None of them is a portal: the game draws each portal (its portal
presentation). None has a shadow. Each frame is square: the game draws an
effect into a square (`draw_effect_clip`), turned by the pose it is given.

The sheet is OWNED by the giant (``owners``): it is decoded when the giant's
sheet is, as a fighter's effects are decoded with the fighter.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

from ..characters.gnu_ton_boss import _svg as svg
from ..characters.gnu_ton_boss import giant_art as art
from ._character_vfx_common import Canvas, make_spec, publish_canonical, publish_catalog, sheet_files

TARGET_NAME = "gnu_ton_blow_fx"
FX = {"cue_family": "gnu_ton", "residency": "OwnedByCharacter", "fade": "InItsFrames", "owners": ["npc_giant_gnu"]}
SHEET_FILES = sheet_files(TARGET_NAME)
FRAME_SIZE = (256, 256)
#: Design units across a frame (the drawing is about the frame's middle).
VIEW = 512.0

ROWS = [
    ("gnu_blow_glint", 7, 40),
    ("gnu_blow_streak", 7, 33),
    ("gnu_hammer_quake", 10, 45),
    ("gnu_blow_impact", 8, 35),
]

INK = art.INK
CREAM = "#f4ecd8"
GOLD = art.C["gold"]
GOLD_LIGHT = art.C["gold_light"]
WHITE = "#fffaf0"
DUST = "#cbb994"
DUST_DARK = "#9c8a68"
STONE = "#6b5a48"
STONE_LIGHT = "#8d7a63"


def _ease_out(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return 1.0 - (1.0 - t) ** 3


def _star(cx, cy, points, outer, inner, turn=0.0):
    pts = []
    for k in range(points * 2):
        r = outer if k % 2 == 0 else inner
        a = math.radians(turn) + math.pi * k / points
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return svg.poly(pts)


def _jagged(cx, cy, n, outer, inner, seed, turn=0.0):
    """A burst of ``n`` spikes whose lengths differ (a comic impact)."""
    pts = []
    for k in range(n * 2):
        wobble = 0.78 + 0.22 * math.sin(seed + k * 2.39)
        r = (outer * wobble) if k % 2 == 0 else inner
        a = math.radians(turn) + math.pi * k / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return svg.poly(pts)


def glint(p: float) -> list[str]:
    """A four-point star that flares, turns a little, and goes out."""
    grow = math.sin(math.pi * min(1.0, p / 0.85))
    if grow <= 0.02:
        return []
    out = []
    long, short = 150.0 * grow, 22.0 * grow
    turn = 12.0 * p
    out.append(svg.path(_star(0.0, 0.0, 4, long, short * 0.6, turn - 90.0), WHITE, INK, 3.0))
    out.append(svg.path(_star(0.0, 0.0, 4, long * 0.55, short * 0.35, turn - 45.0), GOLD_LIGHT, INK, 2.4))
    out.append(svg.ellipse(0.0, 0.0, 16.0 * grow, 16.0 * grow, WHITE, INK, 2.4))
    return out


def streak(p: float) -> list[str]:
    """Lines of speed along +X, out of a line at x = 0: they shoot out with the
    limb and thin away behind it."""
    out = []
    reach = 240.0 * _ease_out(p / 0.45)
    thin = max(0.0, 1.0 - max(0.0, p - 0.35) / 0.65)
    if thin <= 0.02:
        return out
    for i, (dy, length, width) in enumerate(((-96, 0.7, 12), (-52, 1.0, 18), (-12, 0.85, 22), (30, 1.0, 18), (74, 0.75, 14),
                                             (108, 0.55, 9))):
        head = 10.0 + reach * length
        tail = 10.0 + reach * length * max(0.0, (p - 0.2) / 0.8) ** 0.7
        if head - tail < 6.0:
            continue
        w = width * thin
        pts = [(tail, dy), (head - w, dy - w * 0.5), (head, dy), (head - w, dy + w * 0.5)]
        out.append(svg.path(svg.poly(pts), CREAM if i % 2 else WHITE, INK, 2.4))
    return out


def quake(p: float) -> list[str]:
    """A fist into the floor. The floor is the line y = 120: the cracks run
    along it, a ring of dust goes out flat each way, and stones jump."""
    floor = 120.0
    out = []
    # The flash of the blow, flat on the floor, gone at once.
    if p < 0.3:
        f = 1.0 - p / 0.3
        out.append(svg.path(_jagged(0.0, floor - 30.0, 9, 170.0 * (0.6 + 0.4 * f), 50.0, 1.3), GOLD_LIGHT, INK, 3.0))
        out.append(svg.ellipse(0.0, floor - 8.0, 70.0 * f, 22.0 * f, WHITE, INK, 2.4))
    # The plume: dust thrown up where the fist went in, that billows and thins.
    plume = max(0.0, 1.0 - max(0.0, p - 0.3) / 0.7)
    if p > 0.04 and plume > 0.02:
        rise = 170.0 * _ease_out(p / 0.6)
        for k, (dx, up, r) in enumerate(((-30, 0.12, 54), (28, 0.28, 50), (-12, 0.48, 46), (16, 0.68, 40), (-6, 0.88, 32))):
            rr = r * (0.5 + 0.7 * _ease_out(p / 0.5)) * (0.45 + 0.55 * plume)
            out.append(svg.ellipse(dx * (1.0 + p), floor - 20.0 - rise * up, rr, rr * 0.9, DUST if k % 2 else DUST_DARK, INK, 2.2))
    # The ring of dust: two rolls that go out along the floor each way.
    spread = 40.0 + 150.0 * _ease_out(p)
    dust = max(0.0, 1.0 - max(0.0, p - 0.45) / 0.55)
    if dust > 0.02:
        for s in (-1.0, 1.0):
            for k, (back, r) in enumerate(((0.0, 34.0), (-36.0, 26.0), (-66.0, 18.0))):
                x = s * (spread + back)
                rr = r * (0.6 + 0.6 * p) * (0.4 + 0.6 * dust)
                out.append(svg.ellipse(x, floor - rr * 0.7, rr * 1.35, rr, DUST if k == 0 else DUST_DARK, INK, 2.2))
    # The cracks in the floor: zigzags out from the middle that stay a moment.
    if p < 0.85:
        reach = 170.0 * _ease_out(p / 0.25)
        for s in (-1.0, 1.0):
            pts = [(0.0, floor)]
            for k in range(1, 6):
                x = s * reach * k / 5.0
                pts.append((x, floor - (6.0 if k % 2 else -4.0) - 2.0 * k))
            out.append(svg.path("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts), "none", INK, 5.0 * (1.0 - p)))
    # Stones that jump and fall.
    for k, (vx, vy, size) in enumerate(((-260, -760, 22), (-120, -900, 16), (70, -860, 19), (230, -720, 24), (-30, -1000, 14),
                                        (300, -560, 15))):
        t = p * 0.55
        x, y = vx * t, floor - 10.0 + vy * t + 2600.0 * t * t
        if y > floor or p > 0.95:
            continue
        r = size * (1.0 - 0.3 * p)
        turn = 160.0 * p * (1 if k % 2 else -1)
        pts = [(x + r * math.cos(math.radians(turn + a)), y + r * 0.8 * math.sin(math.radians(turn + a)))
               for a in (0, 70, 150, 215, 290)]
        out.append(svg.path(svg.poly(pts), STONE if k % 2 else STONE_LIGHT, INK, 2.2))
    return out


def impact(p: float) -> list[str]:
    """A blow that lands: a burst that flares, and shards that fly out."""
    out = []
    if p < 0.55:
        f = _ease_out(p / 0.2) * (1.0 - max(0.0, p - 0.25) / 0.3)
        out.append(svg.path(_jagged(0.0, 0.0, 11, 190.0 * f + 20.0, 70.0 * f + 8.0, 0.7, 8.0), GOLD, INK, 3.2))
        out.append(svg.path(_jagged(0.0, 0.0, 9, 120.0 * f + 10.0, 46.0 * f + 4.0, 2.1, -6.0), WHITE, INK, 2.6))
    for k in range(8):
        a = math.tau * k / 8.0 + 0.3
        r0 = 60.0 + 260.0 * _ease_out(p)
        length = 60.0 * (1.0 - p)
        if length < 4.0:
            continue
        x0, y0 = r0 * math.cos(a), r0 * math.sin(a)
        x1, y1 = (r0 + length) * math.cos(a), (r0 + length) * math.sin(a)
        w = 9.0 * (1.0 - p)
        nx, ny = -math.sin(a) * w, math.cos(a) * w
        out.append(svg.path(svg.poly([(x0, y0), ((x0 + x1) / 2 + nx, (y0 + y1) / 2 + ny), (x1, y1),
                                      ((x0 + x1) / 2 - nx, (y0 + y1) / 2 - ny)]), CREAM, INK, 2.0))
    return out


DRAWINGS = {"gnu_blow_glint": glint, "gnu_blow_streak": streak, "gnu_hammer_quake": quake, "gnu_blow_impact": impact}


def render_row(anim: str, p: float) -> Image.Image:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=art.OW, colors=art.C)
    svg.part("fx", "Effect", "fx", "fx", 10, DRAWINGS[anim](p))
    half = VIEW / 2.0
    return art._raster(art._document((-half, -half, VIEW, VIEW)), FRAME_SIZE)


def _drawer(anim: str):
    def draw(canvas: Canvas, p: float) -> None:
        canvas.image.alpha_composite(render_row(anim, p).resize(canvas.image.size, Image.LANCZOS))

    return draw


DRAWERS = {name: _drawer(name) for name, _, _ in ROWS}

SPECS = {
    "gnu_blow_glint": make_spec("telegraph", "A star of light where the giant's limb will come out of a portal: it goes now.",
                                placement="world", orientation="radial", size=180),
    "gnu_blow_streak": make_spec("motion_smear", "Lines of speed of the giant's limb as it comes out of a portal's line, along +X.",
                                 placement="world", orientation="directional", rotate_safe=True, size=240),
    "gnu_hammer_quake": make_spec("surface_impact", "The giant's fist into the floor: cracks, a flat ring of dust, stones.",
                                  placement="surface", orientation="gravity_relative", rotate_safe=False, size=320),
    "gnu_blow_impact": make_spec("hit_impact", "A blow of the giant that lands on a body: a burst and its shards.",
                                 placement="world", orientation="radial", size=260),
}

ORIGINS = {name: (FRAME_SIZE[0] * 0.5, FRAME_SIZE[1] * 0.5) for name, _, _ in ROWS}


def render(out_dir: str | Path, **opts):
    del opts
    return publish_catalog(
        fx=FX,
        target_name=TARGET_NAME,
        display_name="Giant GNU blow VFX",
        character_context_id="npc_giant_gnu",
        character_context_display="Giant GNU",
        rows=ROWS,
        drawers=DRAWERS,
        specs=SPECS,
        origins=ORIGINS,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        supersample=1,
        whole_frames=True,
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
        supersample=1,
    )
