"""The Kiln Sprite: a spirit of the kiln fire, in a glazed pot.

A round pot of terracotta with two little handles, glazed blue-green over
its shoulders; the glaze ran in the firing and hangs in drips. A fire lives
in it. The flame rises out of its mouth, and the face of the spirit is in
the flame: two dark eyes and a mouth, in the yellow at its heart. Embers go
up from it.

It floats, keeps its distance and spits coals. Its windup is a breath in:
the flame sinks into the pot and the pot glows hot. Its strike is the spit:
the flame bursts up, its mouth opens wide and a burning coal flies out. A
hit blows its flame back and cracks its glaze; at its death the flame goes
out in smoke and the pot breaks in two.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K

TARGET_NAME = "kiln_sprite"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Kiln Sprite", "Blob", "Small", "Light", "Float", ["fire", "pottery", "floating", "glowing"],
    "A spirit of the kiln fire from the Workshop Deeps of the Art dimension, that lives in a glazed pot. It floats, "
    "keeps its distance, breathes in until its pot glows, and spits a burning coal.",
)

CLAY = (196, 106, 68, 255)
CLAY_SHADE = (142, 70, 46, 255)
CLAY_HOT = (255, 150, 70, 255)
GLAZE = (40, 158, 172, 255)
GLAZE_DARK = (22, 98, 118, 255)
GLAZE_LIGHT = (160, 232, 230, 255)
FLAME = (255, 120, 32, 255)
FLAME_MID = (255, 190, 56, 255)
FLAME_CORE = (255, 244, 190, 255)
EMBER = (255, 90, 30, 255)
COAL = (58, 38, 40, 255)
SMOKE = (150, 140, 150, 255)
OUTLINE = (52, 22, 26, 255)

#: The pot: its half width at each height (from its lip, `y` -14, to its
#: foot, `y` 14), before the squash of the frame.
POT_PROFILE = [(-14.0, 9.5), (-12.0, 8.5), (-9.0, 13.0), (-5.0, 16.5), (0.0, 18.0), (5.0, 17.0), (9.0, 14.0), (12.0, 10.0), (14.0, 7.0)]


def _smooth(points, keep=()):
    """One round of Chaikin's corner cutting: a polygon with its corners
    rounded, but for the corners in `keep` (by index), which stay sharp."""
    pts = list(points)
    out = []
    for k in range(len(pts)):
        (x0, y0), (x1, y1) = pts[k], pts[(k + 1) % len(pts)]
        if k in keep:
            out.append((x0, y0))
        out.append((0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1))
        out.append((0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1))
    return out


def _flame(cx: float, base_y: float, h: float, w: float, sway: float, back: float, wob: float):
    """A flame of three tongues that rises from `base_y`: a tall one in the
    middle, two short ones at its sides. `back` blows its tips backward."""
    s = math.sin(wob * math.tau)
    c = math.cos(wob * math.tau)
    lean = -back * h * 0.55
    pts = [
        (cx - w, base_y),
        (cx - w * 1.08, base_y - h * 0.3),
        (cx - w * 0.78 + sway * 1.5 + lean * 0.6, base_y - h * (0.7 + 0.06 * s)),
        (cx - w * 0.38 + lean * 0.4, base_y - h * 0.52),
        (cx + sway * 2.5 + lean, base_y - h * (1.0 + 0.05 * c)),
        (cx + w * 0.4 + lean * 0.4, base_y - h * 0.5),
        (cx + w * 0.8 + sway * 1.5 + lean * 0.6, base_y - h * (0.64 - 0.06 * s)),
        (cx + w * 1.08, base_y - h * 0.28),
        (cx + w, base_y),
        (cx, base_y + 3.0),
    ]
    return _smooth(pts, keep=(2, 4, 6))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"kiln:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cx, cy = 44.0, 64.0
    lean, flame_h, flame_w, sway, back, heat = 0.0, 27.0, 14.0, math.sin(cyc), 0.0, 0.0
    eyes, mouth, fade, sx, sy, crack, split, smoke, coal = "open", 0.0, 1.0, 1.0, 1.0, False, 0.0, 0.0, None
    wob = t * 2.0
    if anim == "idle":
        cy += 2.5 * math.sin(cyc)
        flame_h += 2.5 * math.sin(cyc * 2.0)
        eyes = "blink" if i == 3 else "open"
    elif anim == "walk":
        cy += 1.5 * math.sin(cyc * 2.0)
        lean, back = 10.0, 0.45
    elif anim == "notice":
        up = math.sin(math.pi * t)
        flame_h, flame_w, eyes = 27.0 + 9.0 * up, 14.0 + 2.0 * up, "wide"
        cy -= 3.0 * up
    elif anim == "windup":
        # It breathes in: the flame goes down into the pot and the pot glows.
        flame_h, flame_w, heat = 15.0 + 1.5 * math.sin(cyc * 2.0), 11.5, 0.8 + 0.2 * math.sin(cyc * 2.0)
        sx, sy, eyes, lean = 1.08, 0.94, "narrow", -6.0
        cx += 0.8 * math.sin(cyc * 3.0)
    elif anim == "attack_side":
        burst = math.sin(math.pi * min(1.0, t * 1.5))
        flame_h, flame_w, mouth, eyes = 27.0 + 9.0 * burst, 14.0 + 2.0 * burst, burst, "narrow"
        lean, heat, back = -12.0 * burst + 4.0, 0.6 * (1.0 - t), -0.25 * burst
        cx -= 3.0 * burst
        # The coal leaves its mouth; the game flies it on from there.
        coal = (t - 0.1) / 0.6 if 0.1 < t < 0.75 else None
    elif anim == "hit":
        lean, back, eyes, crack = -14.0, 0.9, "shut", True
        flame_h, flame_w = 23.0, 13.0
        cx -= 3.0 * math.sin(math.pi * min(1.0, t * 1.5))
    elif anim == "death":
        flame_h = 27.0 * (1.0 - t) ** 1.5 if t < 0.6 else 0.0
        flame_w = 14.0 * (1.0 - 0.5 * t)
        eyes, crack, split, smoke = "shut", True, max(0.0, (t - 0.35) / 0.65), t
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    def at(points):
        return K.turn(points, cx, cy, lean)

    def half(points, side: float):
        """A half of the pot. It falls away from the other half as it breaks."""
        if not split:
            return at(points)
        moved = K.turn(points, cx, cy + 14.0 * sy, side * 40.0 * split)
        return at([(x + side * 8.0 * split, y + 10.0 * split * split) for x, y in moved])

    def pot_point(x: float, y: float):
        return (cx + x * sx, cy + y * sy)

    clay = tuple(int(a + (b - a) * heat * 0.8) for a, b in zip(CLAY, CLAY_HOT))
    mouth_y = cy - 13.0 * sy

    # -- smoke, behind everything --------------------------------------------
    if smoke > 0.2:
        for k in range(3):
            u = (smoke * 1.4 + k * 0.3) % 1.0
            f.ellipse(cx - 2.0 + 5.0 * math.sin(u * 5.0 + k), mouth_y - 8.0 - 28.0 * u, 3.5 + 5.0 * u, 3.0 + 4.0 * u,
                      K.alpha(SMOKE, 0.6 * (1.0 - u) * min(1.0, smoke * 1.5)), body=False)

    # -- the flame, behind the lip of the pot ----------------------------------
    face = None
    if flame_h > 2.0:
        fx, fy = at([(cx, mouth_y + 2.0)])[0]
        f.poly(_flame(fx, fy, flame_h, flame_w, sway, back, wob), FLAME)
        f.poly(_flame(fx, fy, flame_h * 0.74, flame_w * 0.72, sway * 0.8, back, wob + 0.15), FLAME_MID, body=False)
        core_h = flame_h * 0.5
        f.poly(K.ellipse_points(fx - back * 2.0, fy - core_h * 0.72, flame_w * 0.52, core_h * 0.7, 20), FLAME_CORE, body=False)
        face = (fx + 1.0 - back * 2.0, fy - core_h * 0.8)
        f.glow(fx, fy - flame_h * 0.45, flame_w * 0.6, K.alpha(FLAME_MID, 0.2 * fade))

    # -- the pot ---------------------------------------------------------------
    for side in (-1.0, 1.0):
        # A handle: a little loop at its shoulder.
        hx, hy = pot_point(side * 15.5, -7.0)
        loop = [(hx, hy - 3.5), (hx + side * 5.5, hy - 3.0), (hx + side * 6.0, hy + 2.5), (hx, hy + 3.5)]
        f.limb(half(loop, side), 2.6, GLAZE_DARK)
    right = [pot_point(w, y) for y, w in POT_PROFILE]
    left = [pot_point(-w, y) for y, w in POT_PROFILE]
    mid_top, mid_foot = pot_point(0.0, -14.0), pot_point(0.0, 14.0)
    f.poly(half([mid_top] + left + [mid_foot], -1.0), clay)
    f.poly(half([mid_top] + right + [mid_foot], 1.0), clay)
    # Its shade, low on its far side.
    f.poly(half([pot_point(-7.0, 14.0), pot_point(-14.0, 9.0), pot_point(-17.0, 5.0), pot_point(-18.0, 0.0), pot_point(-10.0, 6.0),
                 pot_point(-2.0, 14.0)], -1.0), CLAY_SHADE, body=False)
    # The glaze over its shoulders, with a hem of drips where it ran.
    def hem(x: float) -> float:
        return 1.0 + 4.5 * max(0.0, math.sin(x * 0.55 + 0.8)) ** 3

    for side in (-1.0, 1.0):
        top = [pot_point(side * w, y) for y, w in POT_PROFILE if y < hem(side * w) - 0.5]
        xs = [side * 18.0 * u / 10.0 for u in range(10, -1, -1)]
        edge = [pot_point(x if abs(x) < 17.5 else side * 17.5, min(hem(x), 6.5)) for x in xs]
        f.poly(half([pot_point(0.0, -14.0)] + top + edge, side), GLAZE if side > 0 else GLAZE_DARK, body=False)
    # The shine of the glaze, and the lip.
    f.ink(half([pot_point(7.0, -10.0), pot_point(13.0, -6.5), pot_point(15.0, -1.0)], 1.0), 1.5, K.alpha(GLAZE_LIGHT, 0.95))
    f.dot(*half([pot_point(5.0, -11.0)], 1.0)[0], 1.1, K.alpha(K.WHITE, 0.95))
    if not split:
        f.poly(at(K.ellipse_points(cx, mouth_y, 10.0 * sx, 2.4, 18)), GLAZE_DARK)
        f.poly(at(K.ellipse_points(cx, mouth_y + 0.3, 7.6 * sx, 1.4, 16)), FLAME_MID if flame_h > 2.0 else COAL, body=False)
    if crack and not split:
        f.ink(at([(cx + 5.0, mouth_y + 1.0), (cx + 2.0, cy - 5.0), (cx + 6.0, cy + 1.0), (cx + 3.0, cy + 8.0)]), 1.1, OUTLINE)
    if heat > 0.0:
        f.ink(at([pot_point(-15.0, 7.0), pot_point(-6.0, 12.5), pot_point(6.0, 12.5), pot_point(15.0, 7.0)]), 1.4,
              K.alpha(FLAME_CORE, 0.8 * heat))

    # -- the face, in the heart of the flame -------------------------------------
    if face is not None and flame_h > 8.0:
        fcx, fcy = face
        k = max(0.6, min(1.0, flame_h / 27.0))
        for ox in (-4.0 * k, 4.0 * k):
            ex, ey = fcx + ox, fcy
            if eyes in ("shut", "blink"):
                f.ink([(ex - 2.2, ey + (0.8 if ox < 0 else -0.8) * (eyes == "shut")), (ex + 2.2, ey)], 1.3, OUTLINE)
            elif eyes == "narrow":
                slant = -1.2 if ox > 0 else 1.2
                f.poly([(ex - 2.2, ey - 1.0 - slant * 0.6), (ex + 2.2, ey - 1.0 + slant * 0.6), (ex + 1.8, ey + 1.8), (ex - 1.8, ey + 1.8)],
                       OUTLINE, body=False)
            else:
                big = 1.25 if eyes == "wide" else 1.0
                f.ellipse(ex, ey, 1.9 * big * k, 2.9 * big * k, OUTLINE, body=False)
                f.dot(ex + 0.6, ey - 1.0, 0.7 * big, FLAME_CORE)
        if mouth > 0.05:
            f.ellipse(fcx + 1.0, fcy + 5.5 * k, 2.4 + 2.4 * mouth, 1.4 + 2.6 * mouth, OUTLINE, body=False)
        else:
            f.ink([(fcx - 2.0, fcy + 4.4 * k), (fcx + 0.5, fcy + 5.6 * k), (fcx + 3.0, fcy + 4.2 * k)], 1.0, OUTLINE)

    # -- embers, the coal, the hit, the notice ------------------------------------
    if anim in ("idle", "walk", "notice", "attack_side"):
        for k in range(3):
            u = (t * (2.0 if anim == "walk" else 1.0) + k / 3.0) % 1.0
            ex = cx + (k - 1) * 7.0 + 3.0 * math.sin(u * 6.0 + k) - (14.0 * u if anim == "walk" else 0.0)
            ey = mouth_y - flame_h * 0.75 - 14.0 * u
            if ey > 6.0:
                f.dot(ex, ey, 1.1 * (1.0 - 0.5 * u), K.alpha(FLAME_MID, 1.0 - u))
                f.glow(ex, ey, 1.4, K.alpha(EMBER, 0.6 * (1.0 - u)))
    if coal is not None:
        gx = cx + 14.0 + 26.0 * coal
        gy = mouth_y - 10.0 + 8.0 * coal * coal
        f.poly(K.ellipse_points(gx, gy, 4.8, 4.0, 9, 0.8, rng), COAL)
        f.ink([(gx - 2.6, gy - 1.0), (gx - 0.2, gy + 0.8), (gx + 2.4, gy - 1.4)], 1.1, EMBER)
        f.ink([(gx - 0.2, gy + 0.8), (gx + 0.6, gy + 3.0)], 0.9, EMBER)
        f.glow(gx, gy, 3.0, K.alpha(FLAME, 0.35))
        for k in range(3):
            f.dot(gx - 7.0 - k * 5.0, gy - 1.0 + (k % 2) * 2.0, 1.2 - 0.25 * k, K.alpha(FLAME_MID, 0.9 - 0.25 * k))
    if anim == "hit":
        for k in range(5):
            a = math.radians(170.0 + k * 20.0)
            r = 18.0 + 10.0 * t
            px, py = cx + math.cos(a) * r, mouth_y - 6.0 + math.sin(a) * r
            f.dot(px, py, 1.3, K.alpha(FLAME_MID, 1.0 - 0.5 * t))
    if anim == "notice":
        ax, ay = cx + 22.0, max(16.0, mouth_y - flame_h)
        f.limb([(ax, ay - 8.0), (ax, ay)], 2.8, FLAME)
        f.ellipse(ax, ay + 4.6, 1.8, 1.8, FLAME)
    return f.finish(outline=OUTLINE, width=1.4, glow_blur=2.2, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
