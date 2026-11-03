"""The props of the Workshop Deeps of the Art dimension (biome `art_forge`).

The workshops of the makers, under the ground: kilns, wheels, looms and
cranes, drawn in the cel style of the dimension's cast
(`targets/characters/_art_cast_kit.py`) in the colours of the forge:
terracotta, brick, brass, copper, the orange of the kiln and the colours of
the thread.

- ``art_bridge_planks``: the look of the bridge the crane swings in (a
  `LockWall` of 224 by 24 world units, drawn at 2 to 1). A row of planks
  seen from the side, bound on two ropes, with a brass ring at each end
  where the crane holds it.
- ``art_kiln``: scenery. A bottle kiln of brick, held in copper bands, with
  the fire alive in its mouth and smoke from its neck (its ``idle`` row
  flickers).
- ``art_potters_wheel``: scenery. A kick wheel with a pot half thrown on
  its head (its ``idle`` row turns the wheel).
- ``art_great_loom``: scenery. A great loom with a tapestry half woven on
  it, and threads that run up past its beam into the dark.
- ``art_crane``: scenery. A wooden crane: a mast, an arm and a brace, a
  winch, and a rope over a brass pulley to a hook (its ``idle`` row swings
  the hook a little).

No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from ..characters import _art_cast_kit as K
from .art_props import _publisher

STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
LOOP: List[Tuple[str, int, int]] = [("idle", 6, 120)]

BRICK = (178, 84, 58, 255)
BRICK_SHADE = (128, 56, 42, 255)
BRICK_LIGHT = (214, 122, 86, 255)
MORTAR = (98, 44, 36, 255)
CLAY = (198, 108, 70, 255)
CLAY_SHADE = (150, 74, 50, 255)
CLAY_LIGHT = (232, 156, 116, 255)
BRASS = (226, 180, 76, 255)
BRASS_DARK = (150, 106, 38, 255)
BRASS_LIGHT = (252, 226, 150, 255)
COPPER = (206, 112, 62, 255)
COPPER_DARK = (134, 64, 36, 255)
COPPER_PATINA = (92, 176, 150, 255)
ROPE = (210, 178, 116, 255)
ROPE_DARK = (148, 116, 64, 255)
FIRE = (255, 132, 36, 255)
FIRE_MID = (255, 196, 60, 255)
FIRE_CORE = (255, 246, 196, 255)
SOOT = (40, 28, 34, 255)
SMOKE = (130, 120, 132, 255)
IRON = (84, 80, 98, 255)
OUTLINE = (44, 24, 26, 255)
THREADS = (K.MAGENTA, K.CYAN, K.YELLOW, K.VIOLET)


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


# ---------------------------------------------------------------------------
# The bridge: a row of planks on ropes.
# ---------------------------------------------------------------------------

BRIDGE_FRAME = (448, 48)


def _draw_bridge(anim: str, i: int, n: int):
    w, h = BRIDGE_FRAME
    f = K.Frame(BRIDGE_FRAME)
    rng = random.Random("art_bridge_planks")
    # The rings at its ends, where the crane holds it.
    for x in (9.0, w - 9.0):
        f.ellipse(x, 24.0, 6.0, 7.0, BRASS)
        f.ellipse(x, 24.0, 2.6, 3.4, OUTLINE, body=False)
        f.ink([(x - 3.0, 19.0), (x - 4.0, 23.0)], 1.0, BRASS_LIGHT)
    # The planks, seen from their ends: a little uneven, as planks are.
    planks = []
    x = 15.0
    while x < w - 30.0:
        pw = 17.0 + rng.uniform(-1.5, 1.5)
        top = 4.0 + rng.uniform(0.0, 1.5)
        foot = 42.0 + rng.uniform(-1.0, 1.0)
        lean = rng.uniform(-0.8, 0.8)
        if x + pw > w - 15.0:
            pw = w - 15.0 - x
        planks.append((x, pw))
        tone = K.WOOD if rng.random() < 0.7 else K.shade(K.WOOD, 1.08)
        f.poly([(x + lean, top), (x + pw + lean, top), (x + pw - lean, foot), (x - lean, foot)], tone)
        f.poly([(x + pw * 0.66, top), (x + pw + lean, top), (x + pw - lean, foot), (x + pw * 0.66, foot)], K.WOOD_DARK, body=False)
        f.ink([(x + lean + 1.0, top + 1.0), (x + pw * 0.6, top + 1.0)], 1.0, K.shade(K.WOOD, 1.3))
        # The grain, and a knot in some of them.
        for k in range(2):
            gx = x + 4.0 + k * 5.0 + rng.uniform(-1.0, 1.0)
            f.ink([(gx, top + 4.0), (gx + rng.uniform(-1.0, 1.0), foot - 4.0)], 0.7, K.alpha(K.WOOD_DARK, 0.5))
        if rng.random() < 0.3:
            f.ellipse(x + pw * 0.4, rng.uniform(16.0, 32.0), 2.0, 3.0, K.alpha(K.WOOD_DARK, 0.8), body=False)
        x += pw + 4.0
    # The two ropes that bind them, with a turn round each plank.
    for y in (12.0, 34.0):
        pts = [(9.0, 24.0 + (y - 24.0) * 0.4)]
        for k in range(1, 40):
            u = k / 40.0
            pts.append((9.0 + (w - 18.0) * u, y + 1.4 * math.sin(u * math.pi * 19.0) ** 2))
        pts.append((w - 9.0, 24.0 + (y - 24.0) * 0.4))
        f.limb(pts, 3.2, ROPE)
        f.ink(pts, 0.8, K.alpha(ROPE_DARK, 0.8))
        for px, pw in planks:
            for d in (2.0, 5.0):
                f.ink([(px + pw * 0.5 - 3.0 + d, y - 2.6), (px + pw * 0.5 - 1.0 + d, y + 2.6)], 1.0, ROPE_DARK)
    return f.finish(outline=OUTLINE, width=1.4)


# ---------------------------------------------------------------------------
# The kiln: a bottle of brick with the fire in its mouth.
# ---------------------------------------------------------------------------

KILN_FRAME = (256, 320)
#: The bottle's half width at each height (`y` down), from its lip to its foot.
KILN_PROFILE = [(28.0, 34.0), (40.0, 30.0), (46.0, 30.0), (80.0, 36.0), (120.0, 52.0), (160.0, 76.0), (200.0, 94.0), (240.0, 102.0),
                (280.0, 104.0), (310.0, 106.0)]


def _kiln_half(x: float, profile=KILN_PROFILE) -> List[Tuple[float, float]]:
    return [(128.0 + x * hw, y) for y, hw in profile]


def _draw_kiln(anim: str, i: int, n: int):
    t = _phase(i, n)
    f = K.Frame(KILN_FRAME)
    cx = 128.0
    rng = random.Random("art_kiln")
    # Smoke from its neck, behind it: puffs that rise and grow.
    for k in range(3):
        u = (t + k / 3.0) % 1.0
        f.ellipse(cx - 4.0 + 10.0 * math.sin(u * 4.0 + k * 2.0), 24.0 - 12.0 * u, 9.0 + 7.0 * u, 6.0 + 4.0 * u,
                  K.alpha(SMOKE, 0.55 * (1.0 - u)), body=False)
    # The bottle.
    right = _kiln_half(1.0)
    left = _kiln_half(-1.0)
    f.poly(right + list(reversed(left)), BRICK)
    shade = [(128.0 - hw, y) for y, hw in KILN_PROFILE] + [(128.0 - hw * 0.55, y) for y, hw in reversed(KILN_PROFILE)]
    f.poly(shade, BRICK_SHADE, body=False)
    light = [(128.0 + hw * 0.35, y) for y, hw in KILN_PROFILE[3:]] + [(128.0 + hw * 0.62, y) for y, hw in reversed(KILN_PROFILE[3:])]
    f.poly(light, K.alpha(BRICK_LIGHT, 0.55), body=False)
    # The courses of brick: lines across, and the joints between bricks.
    for row, y in enumerate(range(52, 310, 10)):
        hw = _half_width(float(y))
        f.ink([(cx - hw + 1.0, y), (cx + hw - 1.0, y)], 0.9, K.alpha(MORTAR, 0.6))
        off = 9.0 if row % 2 else 0.0
        bx = cx - hw + off + 6.0
        while bx < cx + hw - 4.0:
            f.ink([(bx, y), (bx, y + 10.0)], 0.9, K.alpha(MORTAR, 0.5))
            bx += 18.0 * (0.6 + 0.4 * hw / 104.0)
    # The lip of the neck, and its soot.
    f.poly([(cx - 38.0, 28.0), (cx + 38.0, 28.0), (cx + 36.0, 38.0), (cx - 36.0, 38.0)], BRICK_SHADE)
    f.poly([(cx - 26.0, 28.0), (cx + 26.0, 28.0), (cx + 22.0, 33.0), (cx - 22.0, 33.0)], SOOT, body=False)
    f.ink([(cx - 37.0, 29.5), (cx + 37.0, 29.5)], 1.4, BRICK_LIGHT)
    # Copper bands that hold it, green where the weather got at them.
    for y in (130.0, 190.0):
        hw = _half_width(y)
        f.limb([(cx - hw - 1.0, y), (cx + hw + 1.0, y)], 6.0, COPPER)
        f.ink([(cx - hw, y - 1.4), (cx + hw, y - 1.4)], 1.0, K.shade(COPPER, 1.3))
        f.ink([(cx - hw, y + 2.0), (cx - hw * 0.4, y + 2.0)], 1.4, K.alpha(COPPER_PATINA, 0.8))
        for k in range(5):
            f.dot(cx - hw * 0.8 + k * hw * 0.4, y, 1.4, COPPER_DARK)
    # The mouth: an arch of brick, black inside, with the fire alive in it.
    arch = [(cx - 32.0, 312.0)] + [(cx + math.cos(a) * 32.0, 262.0 - math.sin(a) * 30.0) for a in [math.pi * (1.0 - u / 16.0) for u in range(17)]] + \
           [(cx + 32.0, 312.0)]
    f.poly(K.grow(arch, 6.0), BRICK_SHADE, body=False)
    for k in range(9):
        a = math.pi * (1.0 - k / 8.0)
        f.ink([(cx + math.cos(a) * 32.0, 262.0 - math.sin(a) * 30.0), (cx + math.cos(a) * 40.0, 262.0 - math.sin(a) * 38.0)], 1.0,
              K.alpha(MORTAR, 0.7))
    f.poly(arch, SOOT, body=False)
    flick = math.sin(t * math.tau)
    flick2 = math.sin(t * math.tau * 2.0 + 1.0)
    for k, (colour, scale) in enumerate(((FIRE, 1.0), (FIRE_MID, 0.72), (FIRE_CORE, 0.42))):
        tongues = []
        for j in range(5):
            u = j / 4.0
            bx = cx - 26.0 * scale + 52.0 * scale * u
            height = (34.0 + 12.0 * math.sin(j * 1.9 + t * math.tau * (1.0 + 0.3 * j))) * scale
            tongues.append((bx, 310.0 - height))
            if j < 4:
                tongues.append((bx + 6.5 * scale, 310.0 - height * 0.45))
        f.poly([(cx - 28.0 * scale, 311.0)] + tongues + [(cx + 28.0 * scale, 311.0)], colour, body=False)
    f.glow(cx, 290.0, 20.0 + 2.0 * flick, K.alpha(FIRE, 0.22))
    # Logs in the fire.
    f.limb([(cx - 24.0, 308.0), (cx + 18.0, 304.0)], 6.0, SOOT, body=False)
    f.limb([(cx - 10.0, 304.0), (cx + 26.0, 309.0)], 5.0, K.shade(SOOT, 1.4), body=False)
    # Light from the fire on the bricks round the mouth.
    for k in range(7):
        a = math.pi * (1.0 - k / 6.0)
        f.ink([(cx + math.cos(a) * 41.0, 262.0 - math.sin(a) * 39.0), (cx + math.cos(a) * 47.0, 262.0 - math.sin(a) * 45.0)], 2.0,
              K.alpha(FIRE_MID, 0.35 + 0.15 * flick2))
    # Embers that go up in front of it.
    for k in range(4):
        u = (t + k / 4.0) % 1.0
        ex = cx - 18.0 + k * 12.0 + 8.0 * math.sin(u * 5.0 + k)
        ey = 268.0 - 50.0 * u
        f.glow(ex, ey, 1.6, K.alpha(FIRE_MID, 1.0 - u))
    # A spy hole in its side, lit.
    f.ellipse(cx + 54.0, 222.0, 5.0, 4.0, SOOT, body=False)
    f.ellipse(cx + 54.0, 222.5, 3.0, 2.2, K.alpha(FIRE_MID, 0.8 + 0.2 * flick), body=False)
    f.glow(cx + 54.0, 222.0, 5.0, K.alpha(FIRE, 0.35))
    del rng
    return f.finish(outline=OUTLINE, width=1.8, glow_blur=3.0)


def _half_width(y: float) -> float:
    """The kiln's half width at the height `y` (between the points of its profile)."""
    for (y0, w0), (y1, w1) in zip(KILN_PROFILE, KILN_PROFILE[1:]):
        if y0 <= y <= y1:
            return w0 + (w1 - w0) * (y - y0) / (y1 - y0)
    return KILN_PROFILE[-1][1]


# ---------------------------------------------------------------------------
# The potter's wheel: a kick wheel with a pot half thrown.
# ---------------------------------------------------------------------------

WHEEL_FRAME = (160, 128)


def _draw_wheel(anim: str, i: int, n: int):
    t = _phase(i, n)
    f = K.Frame(WHEEL_FRAME)
    cx, foot = 92.0, 124.0
    # The bench: a frame of wood with a seat at its left, where the potter sits.
    f.limb([(14.0, foot - 2.0), (18.0, 74.0)], 5.0, K.WOOD_DARK)
    f.limb([(44.0, foot - 2.0), (40.0, 74.0)], 5.0, K.WOOD_DARK)
    f.poly([(8.0, 70.0), (52.0, 70.0), (52.0, 78.0), (8.0, 78.0)], K.WOOD)
    f.ink([(9.0, 71.5), (51.0, 71.5)], 1.0, K.shade(K.WOOD, 1.3))
    f.limb([(18.0, 100.0), (cx - 30.0, 100.0)], 4.0, K.WOOD_DARK)
    f.limb([(cx - 36.0, foot - 2.0), (cx - 36.0, 70.0)], 5.0, K.WOOD)
    f.limb([(cx + 36.0, foot - 2.0), (cx + 36.0, 70.0)], 5.0, K.WOOD)
    # The kick wheel: a heavy disc low down, on the shaft.
    f.ellipse(cx, foot - 12.0, 30.0, 7.0, K.WOOD_DARK)
    f.ellipse(cx, foot - 14.0, 30.0, 7.0, K.WOOD)
    for k in range(4):
        a = t * math.tau / 4.0 + k * math.pi / 2.0
        mx = cx + 26.0 * math.cos(a)
        if math.sin(a) > -0.2:
            f.ink([(mx, foot - 14.0 + 6.0 * math.sin(a) - 1.0), (mx, foot - 14.0 + 6.0 * math.sin(a) + 1.0)], 1.6, K.WOOD_DARK)
    f.limb([(cx, foot - 14.0), (cx, 66.0)], 4.0, IRON)
    # The tray round the head, which catches the slip, and the head.
    f.poly([(cx - 34.0, 62.0), (cx + 34.0, 62.0), (cx + 31.0, 76.0), (cx - 31.0, 76.0)], CLAY_SHADE)
    f.ellipse(cx, 62.0, 34.0, 5.0, CLAY)
    f.ellipse(cx, 62.0, 30.0, 3.6, K.alpha(CLAY_SHADE, 1.0), body=False)
    f.ellipse(cx, 60.0, 20.0, 3.4, IRON)
    f.ellipse(cx, 59.5, 18.0, 2.4, K.STEEL_SHADE, body=False)
    # Slip splashed on the tray.
    for x, r in ((cx - 26.0, 2.4), (cx + 22.0, 3.0), (cx + 28.0, 1.8)):
        f.ellipse(x, 66.0, r, r * 0.6, CLAY_LIGHT, body=False)
    # The pot on the head, half thrown: a cylinder whose wall is still
    # rising, with a rim that is not yet even.
    base, top = 58.0, 28.0
    prof = [(base, 16.0), (50.0, 18.0), (42.0, 17.0), (35.0, 14.0), (top, 13.0)]
    rim = [(cx + 13.0, top), (cx + 9.0, top - 2.5), (cx + 3.0, top - 1.0), (cx - 4.0, top - 3.0), (cx - 9.0, top - 1.2), (cx - 13.0, top)]
    f.poly([(cx + w, y) for y, w in prof] + [(cx - w, y) for y, w in reversed(prof)], CLAY)
    f.poly(rim + [(cx - 13.0, top + 3.0), (cx + 13.0, top + 3.0)], CLAY)
    f.poly([(cx - w, y) for y, w in prof] + [(cx - w * 0.5, y) for y, w in reversed(prof)], CLAY_SHADE, body=False)
    f.ellipse(cx, top + 0.5, 10.5, 2.2, CLAY_SHADE, body=False)
    # The rings of the throw, which turn with the wheel.
    for k in range(4):
        y = 34.0 + ((k * 6.0 + t * 6.0) % 24.0)
        hw = _interp(prof, y) - 0.5
        f.ink([(cx - hw, y), (cx, y + 1.6), (cx + hw, y)], 1.0, K.alpha(CLAY_SHADE, 0.7))
    f.ink([(cx + 9.0, 50.0), (cx + 12.0, 40.0), (cx + 11.0, 32.0)], 1.8, K.alpha(CLAY_LIGHT, 0.9))
    f.dot(cx + 11.0, 36.0, 1.1, K.alpha(K.WHITE, 0.9))
    # A tool left on the tray: a wire with two toggles.
    f.ink([(cx + 30.0, 59.0), (cx + 36.0, 52.0), (cx + 46.0, 54.0)], 0.9, IRON)
    f.limb([(cx + 46.0, 51.0), (cx + 46.0, 57.0)], 2.6, K.WOOD)
    return f.finish(outline=OUTLINE, width=1.5)


def _interp(prof, y: float) -> float:
    for (y0, w0), (y1, w1) in zip(prof, prof[1:]):
        lo, hi = min(y0, y1), max(y0, y1)
        if lo <= y <= hi:
            return w0 + (w1 - w0) * (y - y0) / ((y1 - y0) or 1.0)
    return prof[-1][1]


# ---------------------------------------------------------------------------
# The great loom: a tapestry half woven.
# ---------------------------------------------------------------------------

LOOM_FRAME = (512, 448)


def _draw_loom(anim: str, i: int, n: int):
    w, h = LOOM_FRAME
    f = K.Frame(LOOM_FRAME)
    foot = h - 6.0
    left, right = 44.0, w - 44.0
    beam_y, cloth_y, fell_y = 60.0, 392.0, 236.0
    warp_x0, warp_x1 = left + 26.0, right - 26.0
    # Threads that run up past the beam into the dark.
    for k in range(16):
        x = warp_x0 + 10.0 + k * (warp_x1 - warp_x0 - 20.0) / 15.0
        colour = THREADS[k % 4]
        for s in range(6):
            y0 = beam_y - 4.0 - s * 8.0
            f.ink([(x, y0), (x + (k % 3 - 1) * 1.0, y0 - 8.0)], 1.2, K.alpha(colour, 0.9 * (1.0 - s / 6.0)))
    # The uprights, the top beam and the feet.
    for x in (left, right):
        f.poly([(x - 12.0, foot), (x + 12.0, foot), (x + 10.0, 24.0), (x - 10.0, 24.0)], K.WOOD)
        f.poly([(x + 3.0, foot), (x + 12.0, foot), (x + 10.0, 24.0), (x + 3.0, 24.0)], K.WOOD_DARK, body=False)
        f.poly([(x - 34.0, foot), (x + 34.0, foot), (x + 30.0, foot - 14.0), (x - 30.0, foot - 14.0)], K.WOOD_DARK)
        f.ellipse(x, 22.0, 13.0, 6.0, K.WOOD)
    f.poly([(left - 18.0, beam_y - 14.0), (right + 18.0, beam_y - 14.0), (right + 18.0, beam_y + 6.0), (left - 18.0, beam_y + 6.0)], K.WOOD)
    f.ink([(left - 17.0, beam_y - 11.0), (right + 17.0, beam_y - 11.0)], 1.4, K.shade(K.WOOD, 1.3))
    f.poly([(left - 18.0, beam_y + 1.0), (right + 18.0, beam_y + 1.0), (right + 18.0, beam_y + 6.0), (left - 18.0, beam_y + 6.0)], K.WOOD_DARK,
           body=False)
    for x in (left, right):
        for y in (beam_y - 8.0, beam_y):
            f.dot(x, y, 2.4, BRASS)
    # The warp: threads from the beam down to the cloth.
    warp = [warp_x0 + k * 6.0 for k in range(int((warp_x1 - warp_x0) / 6.0) + 1)]
    for k, x in enumerate(warp):
        f.ink([(x, beam_y + 6.0), (x, fell_y)], 1.0, K.alpha(K.PAPER, 0.9 if k % 2 else 0.7))
    # The heddles: a bar across, on cords, and the beater (the reed) below it.
    f.limb([(left + 6.0, 128.0), (right - 6.0, 128.0)], 6.0, K.WOOD)
    for x in (left + 60.0, right - 60.0):
        f.ink([(x, beam_y + 6.0), (x, 125.0)], 1.4, ROPE_DARK)
    for k, x in enumerate(warp[::2]):
        f.ink([(x, 124.0), (x, 132.0)], 0.8, K.alpha(BRASS_DARK, 0.9))
    f.poly([(left + 4.0, 196.0), (right - 4.0, 196.0), (right - 4.0, 208.0), (left + 4.0, 208.0)], K.WOOD)
    f.ink([(left + 5.0, 198.0), (right - 5.0, 198.0)], 1.2, K.shade(K.WOOD, 1.3))
    f.poly([(left + 4.0, 204.0), (right - 4.0, 204.0), (right - 4.0, 208.0), (left + 4.0, 208.0)], K.WOOD_DARK, body=False)
    # The tapestry: the part that is woven, from the fell down to the cloth
    # beam. Its picture: a gate of the dimension over hills of colour,
    # with a border of diamonds.
    tx0, tx1 = warp_x0 - 2.0, warp_x1 + 2.0
    f.poly([(tx0, fell_y), (tx1, fell_y), (tx1, cloth_y), (tx0, cloth_y)], K.PAPER)
    # The hills.
    for k, (colour, y0, amp) in enumerate(((K.VIOLET, 330.0, 16.0), (K.MAGENTA, 352.0, 12.0), (K.CYAN, 370.0, 10.0))):
        pts = [(tx0, cloth_y)]
        for s in range(25):
            u = s / 24.0
            x = tx0 + (tx1 - tx0) * u
            # Woven pictures go in steps: a hill is a stair of rows.
            y = y0 - amp * math.sin(u * math.pi * (2.0 + k) + k)
            pts.append((x, round(y / 6.0) * 6.0))
        pts.append((tx1, cloth_y))
        f.poly(pts, colour, body=False)
    # The gate: rings of colour, stepped as a weave steps them.
    gx, gy = (tx0 + tx1) / 2.0, 296.0
    for colour, r in ((K.MAGENTA_LIGHT, 44.0), (K.CYAN_LIGHT, 32.0), (K.YELLOW, 20.0), (K.WHITE, 9.0)):
        pts = []
        for s in range(32):
            a = math.tau * s / 32.0
            x, y = gx + math.cos(a) * r, gy + math.sin(a) * r * 1.1
            if y < fell_y + 4.0:
                y = fell_y + 4.0
            pts.append((round(x / 6.0) * 6.0, round(y / 6.0) * 6.0))
        f.poly(pts, colour, body=False)
    # The border of diamonds along the foot of the cloth.
    for k in range(int((tx1 - tx0) / 24.0)):
        x = tx0 + 12.0 + k * 24.0
        colour = THREADS[k % 4]
        f.poly([(x, cloth_y - 14.0), (x + 8.0, cloth_y - 7.0), (x, cloth_y), (x - 8.0, cloth_y - 7.0)], colour, body=False)
    f.poly([(tx0, cloth_y - 18.0), (tx1, cloth_y - 18.0), (tx1, cloth_y - 16.0), (tx0, cloth_y - 16.0)], K.INK, body=False)
    # The weft: fine lines across, and the warp seen through it.
    for y in range(int(fell_y) + 3, int(cloth_y), 3):
        f.ink([(tx0, y), (tx1, y)], 0.5, K.alpha(K.INK, 0.12))
    for x in warp:
        f.ink([(x, fell_y), (x, cloth_y)], 0.5, K.alpha(K.INK, 0.1))
    # The fell: the edge of the weaving, not straight, with a row half done.
    f.ink([(tx0, fell_y), (tx0 + 150.0, fell_y), (tx0 + 150.0, fell_y - 3.0), (tx0 + 230.0, fell_y - 3.0)], 2.0, K.MAGENTA)
    # The shuttle, left in the shed with its thread.
    sx, sy = tx0 + 236.0, fell_y - 4.0
    f.poly([(sx - 24.0, sy), (sx - 14.0, sy - 5.0), (sx + 14.0, sy - 5.0), (sx + 24.0, sy), (sx + 14.0, sy + 5.0), (sx - 14.0, sy + 5.0)], K.WOOD)
    f.ellipse(sx, sy, 8.0, 2.6, K.MAGENTA, body=False)
    f.ink([(sx - 22.0, sy), (sx + 22.0, sy)], 0.8, K.WOOD_DARK)
    # The cloth beam that the tapestry rolls on to, and the spools.
    f.limb([(left, cloth_y + 6.0), (right, cloth_y + 6.0)], 14.0, K.WOOD)
    f.ellipse(left - 2.0, cloth_y + 6.0, 6.0, 9.0, K.WOOD_DARK)
    f.ink([(left + 4.0, cloth_y + 1.0), (right - 4.0, cloth_y + 1.0)], 1.4, K.shade(K.WOOD, 1.3))
    for k, colour in enumerate(THREADS):
        x = right - 20.0
        y = 166.0 + k * 22.0
        f.limb([(right + 2.0, y), (right + 14.0, y)], 3.0, K.WOOD_DARK)
        f.poly([(x + 22.0, y - 8.0), (x + 38.0, y - 8.0), (x + 38.0, y + 8.0), (x + 22.0, y + 8.0)], colour)
        f.poly([(x + 20.0, y - 9.5), (x + 24.0, y - 9.5), (x + 24.0, y + 9.5), (x + 20.0, y + 9.5)], K.WOOD)
        f.poly([(x + 36.0, y - 9.5), (x + 40.0, y - 9.5), (x + 40.0, y + 9.5), (x + 36.0, y + 9.5)], K.WOOD)
        f.ink([(x + 25.0, y - 5.0), (x + 35.0, y - 5.0)], 1.0, K.alpha(K.WHITE, 0.6))
    return f.finish(outline=OUTLINE, width=2.0)


# ---------------------------------------------------------------------------
# The crane: a mast, an arm, a winch, a rope and a hook.
# ---------------------------------------------------------------------------

CRANE_FRAME = (192, 320)


def _draw_crane(anim: str, i: int, n: int):
    t = _phase(i, n)
    f = K.Frame(CRANE_FRAME)
    foot = 314.0
    mast_x = 52.0
    pulley = (164.0, 52.0)
    # The hook swings a little on its rope.
    swing = 4.0 * math.sin(t * math.tau)
    hook_len = 150.0
    a = math.radians(90.0 + swing)
    hook = (pulley[0] + 9.0 + math.cos(a) * hook_len, pulley[1] + math.sin(a) * hook_len)
    # The base: a block of brick the mast stands in.
    f.poly([(16.0, foot), (96.0, foot), (92.0, foot - 30.0), (20.0, foot - 30.0)], BRICK)
    f.poly([(66.0, foot), (96.0, foot), (92.0, foot - 30.0), (66.0, foot - 30.0)], BRICK_SHADE, body=False)
    for y in (foot - 20.0, foot - 10.0):
        f.ink([(19.0, y), (94.0, y)], 0.9, K.alpha(MORTAR, 0.6))
    # The mast.
    f.poly([(mast_x - 8.0, foot - 28.0), (mast_x + 8.0, foot - 28.0), (mast_x + 7.0, 34.0), (mast_x - 7.0, 34.0)], K.WOOD)
    f.poly([(mast_x + 2.0, foot - 28.0), (mast_x + 8.0, foot - 28.0), (mast_x + 7.0, 34.0), (mast_x + 2.0, 34.0)], K.WOOD_DARK, body=False)
    f.ellipse(mast_x, 32.0, 9.0, 4.0, K.WOOD)
    # The arm, from the head of the mast out to the pulley, and its brace.
    f.limb([(mast_x - 4.0, 58.0), (pulley[0], pulley[1] + 2.0)], 9.0, K.WOOD)
    f.ink([(mast_x, 55.0), (pulley[0] - 6.0, pulley[1] - 1.0)], 1.2, K.shade(K.WOOD, 1.3))
    f.limb([(mast_x + 2.0, 150.0), (118.0, 58.0)], 7.0, K.WOOD)
    f.ink([(mast_x + 5.0, 146.0), (116.0, 62.0)], 1.0, K.shade(K.WOOD, 1.25))
    # A stay of rope from the head of the mast to the end of the arm.
    f.ink([(mast_x, 36.0), (pulley[0] - 8.0, pulley[1] - 3.0)], 1.4, ROPE_DARK)
    # Iron straps and brass bolts where the timbers meet.
    for x, y in ((mast_x, 58.0), (mast_x + 2.0, 150.0), (118.0, 58.0)):
        f.ellipse(x, y, 5.0, 5.0, IRON)
        f.dot(x, y, 2.0, BRASS)
    # The winch on the mast: a drum with rope round it, and its crank.
    drum = (mast_x + 16.0, 238.0)
    f.limb([(mast_x, drum[1]), drum], 4.0, IRON)
    f.poly([(drum[0] - 10.0, drum[1] - 12.0), (drum[0] + 10.0, drum[1] - 12.0), (drum[0] + 10.0, drum[1] + 12.0), (drum[0] - 10.0, drum[1] + 12.0)],
           K.WOOD_DARK)
    for k in range(6):
        y = drum[1] - 10.0 + k * 4.0
        f.ink([(drum[0] - 9.0, y), (drum[0] + 9.0, y + 1.4)], 2.0, ROPE)
    for x in (drum[0] - 11.0, drum[0] + 11.0):
        f.ellipse(x, drum[1], 2.6, 14.0, BRASS)
    crank = (drum[0] + 13.0, drum[1])
    f.limb([crank, (crank[0] + 10.0, crank[1] - 12.0)], 3.0, IRON)
    f.limb([(crank[0] + 10.0, crank[1] - 12.0), (crank[0] + 18.0, crank[1] - 12.0)], 4.0, K.WOOD)
    # The rope: from the drum up the arm to the pulley, and down to the hook.
    f.ink([(drum[0] + 4.0, drum[1] - 12.0), (mast_x + 22.0, 140.0), (pulley[0] - 6.0, pulley[1] + 6.0)], 1.8, ROPE)
    f.ink([(pulley[0] + 9.0, pulley[1]), hook], 1.8, ROPE)
    # The pulley.
    f.ellipse(pulley[0], pulley[1], 11.0, 11.0, BRASS)
    f.ellipse(pulley[0], pulley[1], 7.0, 7.0, BRASS_DARK, body=False)
    for k in range(4):
        sa = k * math.pi / 2.0 + t * math.tau * 0.25
        f.ink([(pulley[0], pulley[1]), (pulley[0] + math.cos(sa) * 7.0, pulley[1] + math.sin(sa) * 7.0)], 1.2, BRASS)
    f.dot(pulley[0], pulley[1], 2.4, BRASS_LIGHT)
    # The hook: a block of brass and a curl of iron.
    hx, hy = hook
    f.poly(K.turn([(hx - 6.0, hy), (hx + 6.0, hy), (hx + 5.0, hy + 12.0), (hx - 5.0, hy + 12.0)], hx, hy, -swing), BRASS)
    curl = [(hx, hy + 12.0), (hx, hy + 22.0), (hx - 2.0, hy + 28.0), (hx - 9.0, hy + 30.0), (hx - 14.0, hy + 26.0), (hx - 14.0, hy + 20.0)]
    f.limb(K.turn(curl, hx, hy, -swing), 3.6, IRON)
    f.ellipse(*K.turn([(hx - 14.0, hy + 19.0)], hx, hy, -swing)[0], 2.6, 2.6, IRON)
    return f.finish(outline=OUTLINE, width=1.6)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

TARGETS: Dict[str, dict] = {
    "art_bridge_planks": _publisher("art_bridge_planks", "Bridge Planks", STILL, BRIDGE_FRAME, _draw_bridge, {"foot": (224.0, 48.0)}, "Door",
                                    ["prop", "door", "bridge", "art"], forward=(0.0, -1.0)),
    "art_kiln": _publisher("art_kiln", "Kiln", LOOP, KILN_FRAME, _draw_kiln, {"foot": (128.0, 320.0)}, "Scenery", ["prop", "scenery", "art"]),
    "art_potters_wheel": _publisher("art_potters_wheel", "Potter's Wheel", LOOP, WHEEL_FRAME, _draw_wheel, {"foot": (80.0, 128.0)}, "Scenery",
                                    ["prop", "scenery", "art"]),
    "art_great_loom": _publisher("art_great_loom", "Great Loom", STILL, LOOM_FRAME, _draw_loom, {"foot": (256.0, 448.0)}, "Scenery",
                                 ["prop", "scenery", "art"]),
    "art_crane": _publisher("art_crane", "Crane", LOOP, CRANE_FRAME, _draw_crane, {"foot": (96.0, 320.0)}, "Scenery", ["prop", "scenery", "art"]),
}
