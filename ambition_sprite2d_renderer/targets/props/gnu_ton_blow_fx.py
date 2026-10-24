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
    # Round 3: two blows that meet (Newton's third law), the scholar's power
    # on the giant's shoulders, the launch into space, and a puff of a push in
    # space.
    ("gnu_blow_clash", 9, 35),
    ("gnu_power_up", 12, 60),
    ("gnu_liftoff", 12, 50),
    ("gnu_thrust_puff", 7, 40),
    # The end of the fight: the golden apple falls on the beaten scholar's
    # head, and he wakes.
    ("gnu_apple_bonk", 14, 55),
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


def clash(p: float) -> list[str]:
    """Two blows that meet, along X: two wedges driven at the middle from each
    side, a flash ring where they meet, and sparks thrown out square to them.
    Equal and opposite: the picture is the same from each side."""
    out = []
    # The ring of the meeting: it goes out and thins.
    ring = 40.0 + 200.0 * _ease_out(p / 0.7)
    width = 22.0 * max(0.0, 1.0 - p / 0.8)
    if width > 0.5:
        out.append(svg.ellipse(0.0, 0.0, ring, ring * 0.82, "none", INK, width + 4.0))
        out.append(svg.ellipse(0.0, 0.0, ring, ring * 0.82, "none", GOLD_LIGHT, width))
    # The two wedges: driven in, then thrown back from each other.
    back = 70.0 * _ease_out(max(0.0, p - 0.15) / 0.6)
    size = 1.0 - max(0.0, p - 0.45) / 0.55
    if size > 0.05:
        for s in (-1.0, 1.0):
            x0 = s * (24.0 + back)
            pts = [(x0, 0.0), (x0 + s * 120.0 * size, -54.0 * size), (x0 + s * 96.0 * size, 0.0), (x0 + s * 120.0 * size, 54.0 * size)]
            out.append(svg.path(svg.poly(pts), WHITE if s > 0 else CREAM, INK, 3.0))
    # The flash where they met.
    if p < 0.4:
        f = 1.0 - p / 0.4
        out.append(svg.path(_star(0.0, 0.0, 4, 150.0 * f + 20.0, 26.0 * f + 6.0, 90.0), WHITE, INK, 3.0))
    # Sparks, square to the blows: up and down.
    for k, (a, speed) in enumerate(((-90, 1.0), (-70, 0.8), (-110, 0.85), (90, 1.0), (70, 0.75), (110, 0.9), (-80, 0.6), (100, 0.65))):
        r0 = 30.0 + 230.0 * speed * _ease_out(p)
        length = 46.0 * (1.0 - p)
        if length < 4.0:
            continue
        ar = math.radians(a)
        x0, y0 = r0 * math.cos(ar), r0 * math.sin(ar)
        x1, y1 = (r0 + length) * math.cos(ar), (r0 + length) * math.sin(ar)
        out.append(svg.path(f"M{x0:.1f},{y0:.1f} L{x1:.1f},{y1:.1f}", "none", GOLD_LIGHT if k % 2 else WHITE, 6.0 * (1.0 - p)))
    return out


def power_up(p: float) -> list[str]:
    """The scholar takes his power from the giant's shoulders: rings of gold
    go up round him, and sparks rise. Upright: its bottom is his feet
    (y = 200)."""
    out = []
    feet = 200.0
    for k in range(3):
        u = (p * 1.5 - k * 0.25) % 1.0
        if u < 0.02 or u > 0.98:
            continue
        y = feet - 400.0 * u
        r = 110.0 * (1.0 - 0.45 * u)
        w = 10.0 * (1.0 - u)
        out.append(svg.ellipse(0.0, y, r, r * 0.26, "none", INK, w + 3.0))
        out.append(svg.ellipse(0.0, y, r, r * 0.26, "none", GOLD_LIGHT if k % 2 else GOLD, w))
    for k in range(9):
        u = (p * 2.0 + k * 0.37) % 1.0
        x = 120.0 * math.sin(k * 2.1 + p * 3.0) * (1.0 - u * 0.4)
        y = feet - 30.0 - 380.0 * u
        size = 14.0 * (1.0 - u)
        if size < 2.0:
            continue
        out.append(svg.path(_star(x, y, 4, size * 2.2, size * 0.5, 45.0 * k), WHITE if k % 3 else GOLD_LIGHT, INK, 1.8))
    return out


def liftoff(p: float) -> list[str]:
    """The launch into space, from the floor (the line y = 160): a flat ring
    of force goes out along it, and a column of smoke and fire is left under
    what went up."""
    floor = 160.0
    out = []
    # The ring along the floor.
    spread = 60.0 + 200.0 * _ease_out(p)
    fade = max(0.0, 1.0 - p / 0.9)
    if fade > 0.02:
        out.append(svg.ellipse(0.0, floor - 6.0, spread, 26.0 + 30.0 * p, "none", INK, 14.0 * fade + 4.0))
        out.append(svg.ellipse(0.0, floor - 6.0, spread, 26.0 + 30.0 * p, "none", CREAM, 14.0 * fade))
    # The column: fire at its foot at first, then smoke that climbs.
    if p < 0.35:
        f = 1.0 - p / 0.35
        out.append(svg.path(_jagged(0.0, floor - 50.0, 8, 120.0 * f + 30.0, 40.0, 0.9, -90.0), GOLD, INK, 3.0))
        out.append(svg.path(_jagged(0.0, floor - 40.0, 7, 70.0 * f + 16.0, 24.0, 2.3, -90.0), WHITE, INK, 2.4))
    rise = 300.0 * _ease_out(p / 0.8)
    for k, (dx, up, r) in enumerate(((-40, 0.0, 50), (36, 0.15, 46), (-20, 0.35, 42), (24, 0.55, 36), (-8, 0.78, 30), (10, 1.0, 22))):
        rr = r * (0.6 + 0.8 * _ease_out(p / 0.5)) * (1.0 - 0.5 * max(0.0, p - 0.6) / 0.4)
        if rr < 4.0:
            continue
        out.append(svg.ellipse(dx * (1.0 + p), floor - 30.0 - rise * up, rr, rr * 0.9, DUST if k % 2 else DUST_DARK, INK, 2.2))
    return out


def thrust_puff(p: float) -> list[str]:
    """A push in space, along +X: a puff of vapour left behind (toward -X)
    that grows and goes."""
    out = []
    for k, (dx, r) in enumerate(((-20, 30), (-60, 24), (-96, 16))):
        x = dx * (1.0 + 1.6 * p)
        rr = r * (0.6 + 1.0 * _ease_out(p)) * (1.0 - p)
        if rr < 3.0:
            continue
        out.append(svg.ellipse(x, 0.0, rr, rr * 0.86, WHITE if k == 0 else CREAM, INK, 2.2))
    return out


APPLE = "#d6a21e"
APPLE_LIGHT = "#f6d763"
LEAF = "#5f9a3c"


def _golden_apple(x: float, y: float, r: float, turn: float) -> list[str]:
    out = [svg.ellipse(x, y, r, r * 0.92, APPLE, INK, 3.0),
           svg.ellipse(x - r * 0.36, y - r * 0.3, r * 0.3, r * 0.22, APPLE_LIGHT)]
    a = math.radians(turn - 90.0)
    sx, sy = x + math.cos(a) * r * 0.9, y + math.sin(a) * r * 0.9
    ex, ey = x + math.cos(a) * r * 1.5, y + math.sin(a) * r * 1.5
    out.append(svg.path(f"M{sx:.1f},{sy:.1f} L{ex:.1f},{ey:.1f}", "none", INK, 4.0))
    b = math.radians(turn - 40.0)
    leaf = [(ex, ey), (ex + math.cos(b) * r * 0.9, ey + math.sin(b) * r * 0.9 - r * 0.15),
            (ex + math.cos(b) * r * 0.5, ey + math.sin(b) * r * 0.5 + r * 0.2)]
    out.append(svg.path(svg.poly(leaf), LEAF, INK, 2.2))
    return out


def apple_bonk(p: float) -> list[str]:
    """The golden apple falls on a head at the middle (y = 0): it falls from
    the top of the frame under gravity (it gets faster), hits, a star and
    small stars go round, and it bounces off up and to the side."""
    out = []
    hit = 0.42
    if p < hit:
        u = p / hit
        out += _golden_apple(0.0, -230.0 + 200.0 * u * u, 34.0, 20.0 * u)
    else:
        u = (p - hit) / (1.0 - hit)
        # It bounces: up and away, and falls again.
        x, y = 150.0 * u, -30.0 - 260.0 * u + 330.0 * u * u
        if y < 230.0:
            out += _golden_apple(x, y, 34.0, 20.0 + 300.0 * u)
        if u < 0.35:
            f = 1.0 - u / 0.35
            out.append(svg.path(_star(0.0, -40.0, 6, 110.0 * f + 20.0, 34.0 * f + 8.0, 15.0), WHITE, INK, 3.0))
        # The small stars round the head.
        for k in range(3):
            a = 2.0 * math.pi * (k / 3.0 + 1.6 * u)
            sx, sy = 70.0 * math.cos(a), -60.0 + 18.0 * math.sin(a)
            if u < 0.95:
                out.append(svg.path(_star(sx, sy, 5, 16.0, 6.0, 30.0 * k), GOLD_LIGHT, INK, 2.0))
    return out


DRAWINGS = {"gnu_blow_glint": glint, "gnu_blow_streak": streak, "gnu_hammer_quake": quake, "gnu_blow_impact": impact,
            "gnu_blow_clash": clash, "gnu_power_up": power_up, "gnu_liftoff": liftoff, "gnu_thrust_puff": thrust_puff,
            "gnu_apple_bonk": apple_bonk}


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
    "gnu_blow_clash": make_spec("hit_impact", "Two blows that meet, along +X: wedges driven at the middle, a ring, sparks square to them.",
                                placement="world", orientation="directional", rotate_safe=True, size=300),
    "gnu_power_up": make_spec("aura", "Rings of gold that go up round a body standing at the bottom, and rising sparks.",
                              placement="world", orientation="gravity_relative", rotate_safe=False, size=420),
    "gnu_liftoff": make_spec("surface_impact", "A launch from the floor: a flat ring of force and a column of fire and smoke.",
                             placement="surface", orientation="gravity_relative", rotate_safe=False, size=440),
    "gnu_thrust_puff": make_spec("motion_smear", "A push in space along +X: a puff of vapour left behind.",
                                 placement="world", orientation="directional", rotate_safe=True, size=160),
    "gnu_apple_bonk": make_spec("story_beat", "A golden apple falls on a head at the middle, a star, and it bounces off.",
                                placement="world", orientation="gravity_relative", rotate_safe=False, size=480),
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
