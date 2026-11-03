"""The Terracotta Warrior: a clay soldier of the first emperor's army.

A soldier of fired clay as tall as a man, from the army that was buried
with the first emperor of China: a coat of lamellar armour in rows of small
plates over a knee-long robe, puttees and square-toed shoes, a topknot on
the side of his head and a calm moustache. He holds a ji, a halberd with a
spear point and a dagger-axe blade of bronze. He was painted once; a few
patches of red, green and violet are all that is left. He is cracked.

He is slow and very heavy. At rest he does not move, but a little dust
falls from him. When he sees you his head turns with a puff of clay dust;
his windup lifts the ji high over his head with both hands, and his strike
chops it down into the ground in front of him. A hit knocks a chip off
him; at his death he falls apart into shards and a cloud of dust.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_cast_kit as H
from . import _stage_kit as S

TARGET_NAME = "terracotta_warrior"
FRAME_SIZE = (160, 160)
ROWS = K.ENEMY_ROWS
GROUND = 153.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Terracotta Warrior", "Biped", "Standard", "Heavy", "WalkHeavy", ["clay", "soldier", "halberd", "cracked"],
    "A clay soldier of the first emperor's army in the History dimension: lamellar armour, a topknot, faded paint and "
    "cracks. Slow and heavy: he lifts his halberd over his head and chops it into the ground in front of him.",
    "silk",
)

THIGH, SHIN = 15.0, 15.0
UPPER_ARM, FOREARM = 11.5, 11.0
TORSO = 22.0
CLAY, CLAY_SHADE, CLAY_LIGHT = H.CLAY, H.CLAY_SHADE, H.CLAY_LIGHT
PLATE = (138, 112, 98, 255)
PLATE_DARK = (98, 78, 68, 255)
PAINT_RED = (176, 70, 58, 255)
PAINT_GREEN = (96, 130, 92, 255)
PAINT_VIOLET = (120, 96, 140, 255)
JI_FRONT, JI_BACK = 58.0, 22.0


def _ji(pen: S.Pen, grip, angle: float) -> None:
    """The halberd: a long shaft, a spear point and a dagger-axe blade."""
    a = math.radians(angle)
    d = (math.cos(a), math.sin(a))
    nrm = (-d[1], d[0])

    def at(s: float, w: float = 0.0):
        return (grip[0] + d[0] * s + nrm[0] * w, grip[1] + d[1] * s + nrm[1] * w)

    pen.limb([at(-JI_BACK), at(JI_FRONT - 4.0)], 2.8, K.WOOD_DARK)
    pen.ink([at(-JI_BACK + 2.0, -0.6), at(JI_FRONT - 6.0, -0.6)], 0.6, K.WOOD)
    pen.poly([at(JI_FRONT - 6.0, -1.6), at(JI_FRONT + 6.0, -1.0), at(JI_FRONT + 12.0, 0.0), at(JI_FRONT + 6.0, 1.0), at(JI_FRONT - 6.0, 1.6)],
             H.BRONZE)
    # The dagger-axe blade, out from the shaft below the point.
    pen.poly([at(JI_FRONT - 5.0, 1.0), at(JI_FRONT - 7.0, 9.0), at(JI_FRONT - 11.0, 17.0), at(JI_FRONT - 6.0, 15.0), at(JI_FRONT - 1.0, 8.0),
              at(JI_FRONT, 1.0)], H.BRONZE)
    pen.ink([at(JI_FRONT - 4.0, 3.0), at(JI_FRONT - 8.0, 14.0)], 0.6, H.BRONZE_LIGHT)
    pen.limb([at(JI_FRONT - 9.0), at(JI_FRONT - 5.0)], 3.6, H.CRIMSON, body=False)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    hip_x, crouch, lean, bob = 62.0, 0.0, 0.0, 0.0
    near_foot, far_foot = (5.0, 0.0), (-5.0, 0.0)
    grip, ji_angle = "rest", -90.0
    head_turn, eyes, alarm, fade = 0.0, "calm", False, 1.0
    apart, chip, crack, dust_at = 0.0, 0.0, 0.0, None
    falling_grain = None
    if anim == "idle":
        # Still as a statue; only a little dust falls from his elbow.
        bob = 0.3 * math.sin(cyc)
        falling_grain = t
        eyes = "calm"
    elif anim == "walk":
        # A heavy, stiff step; dust where each foot comes down.
        near_foot = (7.0 * math.sin(cyc), 3.5 * max(0.0, math.cos(cyc)))
        far_foot = (-7.0 * math.sin(cyc), 3.5 * max(0.0, -math.cos(cyc)))
        bob = 1.5 * abs(math.sin(cyc)) - 1.0
        lean = 2.0 * math.sin(cyc)
        ji_angle = -88.0 + 2.0 * math.sin(cyc)
        if i in (2, 6):
            foot = near_foot if i == 2 else far_foot
            dust_at = (hip_x + foot[0] + 2.0, GROUND - 1.0, 0.5)
    elif anim == "notice":
        # The head turns to you with a grind and a puff of dust; the eyes open.
        u = min(1.0, t * 1.5)
        head_turn, eyes, alarm = 1.0, "open" if u > 0.3 else "calm", True
        dust_at = (hip_x + 6.0, GROUND - TORSO - THIGH - SHIN + 4.0, u)
    elif anim == "windup":
        # The ji high over his head, both hands on it.
        crouch, lean = 4.0 + 0.5 * math.sin(cyc * 2.0), -6.0
        near_foot, far_foot = (12.0, 0.0), (-10.0, 0.0)
        grip, ji_angle = ("up", 0.0), -125.0 + 2.0 * math.sin(cyc * 2.0)
        eyes = "open"
    elif anim == "attack_side":
        # The chop: down into the ground in front, and a burst of dust.
        sw = min(1.0, t * 1.8)
        e = sw * sw * (3.0 - 2.0 * sw)
        crouch, lean = 4.0 + 4.0 * e, -6.0 + 18.0 * e
        near_foot, far_foot = (14.0, 0.0), (-10.0, 0.0)
        grip, ji_angle = ("up", e), -125.0 + 140.0 * e
        eyes = "open"
        if t > 0.3:
            dust_at = (hip_x + 70.0, GROUND - 1.0, min(1.0, (t - 0.3) / 0.6))
    elif anim == "hit":
        lean, crouch = -6.0, 2.0
        hip_x -= 2.0 * math.sin(math.pi * t)
        chip, crack, eyes = t, 1.0, "shut"
    elif anim == "death":
        apart = t
        crack = 1.0
        eyes = "shut"
        # The ji topples back on its own and slides as it falls.
        grip, ji_angle = "rest", -90.0 - 90.0 * min(1.0, t * 1.4) ** 2
        dust_at = (hip_x, GROUND - 4.0, min(1.0, t * 1.3))
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    hip_y = GROUND - (THIGH + SHIN - 1.0) + crouch + bob
    lr = math.radians(lean)

    def up(p, length):
        return (p[0] + math.sin(lr) * length, p[1] - math.cos(lr) * length)

    def across(p, w):
        return (p[0] + math.cos(lr) * w, p[1] + math.sin(lr) * w)

    hip = (hip_x, hip_y)
    shoulder = up(hip, TORSO - 4.0)
    neck = up(hip, TORSO)
    hx, hy = up(neck, 8.5)

    # Each piece falls its own way when he falls apart: (spin, dx, drop).
    def piece(pivot, spin, dx, drop):
        if apart <= 0.0:
            return S.Pen(f)
        a = apart
        return S.Pen(f, pivot, spin * a, (dx * a, drop * a * a))

    legs_pen = piece((hip_x, GROUND), -6.0, -4.0, 0.0)
    body_pen = piece(hip, -24.0, -6.0, 18.0)
    head_pen = piece((hx, hy), 70.0, 22.0, 56.0)
    arm_pen = piece(shoulder, 40.0, 12.0, 28.0)

    def a_leg(spec, colour):
        dx, lift = spec
        foot = (hip_x + dx, GROUND - 2.0 - lift)
        knee, ankle = H.leg(legs_pen, hip, foot, THIGH, SHIN, 6.4, colour)
        # Puttees: bands round the shin; a square-toed shoe.
        for u in (0.35, 0.55, 0.75):
            a, b = H.lerp(knee, ankle, u), H.lerp(knee, ankle, u + 0.06)
            legs_pen.ink([(a[0] - 3.2, a[1]), (b[0] + 3.2, b[1])], 0.7, CLAY_SHADE)
        legs_pen.poly([(ankle[0] - 3.5, ankle[1] - 2.0), (ankle[0] + 7.5, ankle[1] - 1.0), (ankle[0] + 8.0, ankle[1] + 2.4), (ankle[0] - 3.5, ankle[1] + 2.4)],
                      K.shade(colour, 0.85))
        legs_pen.poly([(ankle[0] + 5.5, ankle[1] - 2.6), (ankle[0] + 8.0, ankle[1] - 2.6), (ankle[0] + 8.0, ankle[1] - 0.6)], K.shade(colour, 0.85))

    a_leg(far_foot, CLAY_SHADE)

    # The far arm holds the shaft low; it is drawn behind the body.
    if grip == "rest":
        ga = math.radians(ji_angle)
        butt_x = hip_x + 15.0 + 41.0 * min(1.0, apart * 1.4) ** 2
        g = (butt_x + math.cos(ga) * (JI_BACK + 2.0), GROUND - 3.0 + math.sin(ga) * (JI_BACK + 2.0))
        g_far = (g[0], g[1] + 12.0)
    else:
        e = grip[1]
        g = H.lerp((shoulder[0] - 2.0, shoulder[1] - 18.0), (shoulder[0] + 16.0, shoulder[1] + 4.0), e)
        ga = math.radians(ji_angle)
        g_far = (g[0] - math.cos(ga) * 8.0, g[1] - math.sin(ga) * 8.0)
    H.arm(arm_pen, across(shoulder, -2.0), g_far, UPPER_ARM, FOREARM, 5.4, CLAY_SHADE, elbow_out=1.0)

    # The robe under the armour: knee long, with a patch of old red paint.
    bp = body_pen
    skirt = [across(hip, -8.0), across(hip, 8.0), across(up(hip, -12.0), 10.0), across(up(hip, -12.0), -9.5)]
    bp.poly(skirt, CLAY)
    bp.poly([across(up(hip, -4.0), 2.0), across(up(hip, -4.0), 8.6), across(up(hip, -11.0), 9.6), across(up(hip, -11.0), 3.0)], K.alpha(PAINT_RED, 0.7), body=False)
    bp.poly([skirt[0], across(hip, -4.0), across(up(hip, -12.0), -5.0), skirt[3]], CLAY_SHADE, body=False)
    # The armour: rows of little plates with a rivet each.
    sb, sf = across(shoulder, -8.0), across(shoulder, 7.5)
    coat = [across(up(hip, 2.0), -8.5), across(up(hip, 2.0), 8.5), sf, across(neck, 3.5), across(neck, -3.5), sb]
    bp.poly(coat, PLATE)
    bp.poly([across(up(hip, 2.0), -8.5), across(up(hip, 2.0), -4.0), across(shoulder, -4.0), sb], PLATE_DARK, body=False)
    for row in range(5):
        h0 = 3.0 + row * 3.4
        bp.ink([across(up(hip, h0), -8.0), across(up(hip, h0), 8.0)], 0.6, PLATE_DARK)
        for col in range(5):
            w = -6.5 + col * 3.2 + (1.6 if row % 2 else 0.0)
            if w < 7.5:
                p = across(up(hip, h0 + 1.7), w)
                bp.dot(p[0], p[1], 0.55, CLAY_LIGHT)
    bp.poly([across(up(hip, 12.0), 1.0), across(up(hip, 12.0), 7.0), across(up(hip, 17.0), 6.5), across(up(hip, 17.0), 2.0)], K.alpha(PAINT_GREEN, 0.55), body=False)
    bp.limb([across(up(hip, 2.0), -8.5), across(up(hip, 2.0), 8.5)], 2.2, CLAY_SHADE, body=False)
    # The cracks: always a few, and more when he is hurt.
    cracks = [[across(up(hip, 16.0), -2.0), across(up(hip, 12.0), 0.5), across(up(hip, 9.0), -1.0)],
              [across(up(hip, -3.0), 6.0), across(up(hip, -7.0), 4.0)]]
    if crack:
        cracks += [[across(up(hip, 18.0), 5.0), across(up(hip, 13.0), 3.0), across(up(hip, 8.0), 6.0), across(up(hip, 4.0), 3.0)],
                   [across(up(hip, 6.0), -7.0), across(up(hip, 2.0), -3.0), across(up(hip, -6.0), -5.0)]]
    for c in cracks:
        bp.ink(c, 0.9, (70, 50, 40, 255))

    a_leg(near_foot, CLAY)
    legs_pen.ink([(hip_x + near_foot[0] - 1.0, GROUND - 16.0), (hip_x + near_foot[0] + 1.0, GROUND - 11.0)], 0.8, (70, 50, 40, 255))

    # The head: a calm face, a moustache, a topknot to the side.
    hp = head_pen
    tilt = lean * 0.3 + (-12.0 * head_turn * min(1.0, t * 3.0) if anim == "notice" else 0.0)

    def Hd(x, y):
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    hp.poly([Hd(-7.6, -2.0), Hd(-4.0, -8.6), Hd(4.0, -8.8), Hd(7.6, -4.0), Hd(2.0, -5.0), Hd(-3.0, -3.0), Hd(-5.0, 3.0), Hd(-7.8, 3.0)], CLAY_SHADE)
    hp.ellipse(hx, hy, 7.2, 8.0, CLAY)
    hp.poly([Hd(6.4, -1.0), Hd(9.4, 2.0), Hd(6.6, 3.2)], CLAY)
    hp.poly([Hd(-7.6, -2.0), Hd(-4.0, -8.6), Hd(4.0, -8.8), Hd(7.6, -4.0), Hd(2.0, -5.4), Hd(-3.0, -4.0), Hd(-5.4, 2.0), Hd(-7.8, 2.0)], CLAY_SHADE)
    for k in range(4):
        hp.ink([Hd(-5.0 + k * 2.6, -7.6), Hd(-4.0 + k * 2.6, -5.0)], 0.5, CLAY)
    # The topknot, tied with a cord, on the side and top of his head.
    hp.ellipse(Hd(-1.0, -11.5)[0], Hd(-1.0, -11.5)[1], 3.6, 3.0, CLAY_SHADE)
    hp.limb([Hd(-3.4, -9.4), Hd(1.4, -9.4)], 1.4, K.alpha(PAINT_RED, 0.8), body=False)
    hp.ellipse(Hd(-0.6, 3.2)[0], Hd(-0.6, 3.2)[1], 2.0, 2.4, CLAY_LIGHT, body=False)
    ex, ey = Hd(3.8, -0.8)
    if eyes == "open":
        hp.dot(ex, ey, 1.2, (50, 34, 30, 255))
    elif eyes == "shut":
        hp.ink([(ex - 1.4, ey - 0.6), (ex + 1.4, ey + 0.6)], 0.9, (50, 34, 30, 255))
    else:
        hp.ink([(ex - 1.5, ey), (ex, ey + 0.7), (ex + 1.5, ey)], 0.9, (50, 34, 30, 255))
    hp.ink([Hd(2.0, -3.0), Hd(5.4, -3.4)], 0.9, CLAY_SHADE)
    # The moustache, curled up at its ends.
    hp.ink([Hd(9.0, 4.4), Hd(6.0, 4.6), Hd(4.0, 4.2), Hd(3.2, 3.0)], 1.2, (70, 50, 40, 255))
    hp.ink([Hd(6.4, 6.8), Hd(8.2, 6.6)], 0.8, (70, 50, 40, 255))

    # The ji, and the near arm on it.
    if grip == "rest":
        _ji(S.Pen(f) if apart else arm_pen, g, ji_angle)
        g_near = (g[0] - 1.0, g[1] - 4.0)
    else:
        _ji(arm_pen, g, ji_angle)
        g_near = g
    H.arm(arm_pen, across(shoulder, 2.0), g_near, UPPER_ARM, FOREARM, 5.8, CLAY, elbow_out=1.0)
    arm_pen.poly([across(shoulder, -1.0), across(shoulder, 7.5), across(up(hip, 13.0), 8.0), across(up(hip, 13.0), 0.0)], PLATE)
    arm_pen.ink([across(up(hip, 15.5), 0.5), across(up(hip, 15.5), 7.5)], 0.6, PLATE_DARK)
    arm_pen.poly([across(shoulder, 1.5), across(shoulder, 6.0), across(up(hip, 14.0), 6.0), across(up(hip, 14.0), 2.0)], K.alpha(PAINT_VIOLET, 0.6), body=False)
    arm_pen.ellipse(g_near[0], g_near[1], 3.0, 2.8, CLAY)

    # Dust and chips.
    rng = random.Random(f"terracotta-{anim}-{i}")
    if falling_grain is not None:
        gx = hip_x + 10.0
        for k in range(3):
            u = (falling_grain + k / 3.0) % 1.0
            f.ellipse(gx + rng.uniform(-1.0, 1.0), hip_y - 8.0 + u * 40.0, 0.9, 0.9, K.alpha(CLAY_LIGHT, 1.0 - u), body=False)
    if chip > 0.0:
        cx, cy = shoulder[0] + 6.0 + 18.0 * chip, shoulder[1] - 4.0 - 10.0 * math.sin(math.pi * chip) + 10.0 * chip
        f.poly(K.turn([(cx - 2.5, cy - 2.0), (cx + 2.5, cy - 1.5), (cx + 1.5, cy + 2.0), (cx - 2.0, cy + 1.5)], cx, cy, 200.0 * chip), CLAY)
        H.dust(f, shoulder[0] + 6.0, shoulder[1], 8.0, chip, "chip", CLAY_LIGHT)
    if dust_at:
        x, y, amt = dust_at
        H.dust(f, x, y, 14.0, amt, f"dust-{anim}", CLAY_LIGHT, count=9)
    if apart > 0.3:
        # Shards on the ground where he stood.
        for k in range(7):
            sx = hip_x - 26.0 + k * 10.0 + rng.uniform(-3.0, 3.0)
            sy = GROUND - 2.0 - rng.uniform(0.0, 2.0)
            r = rng.uniform(2.0, 3.6) * min(1.0, (apart - 0.3) * 3.0)
            f.poly(K.turn([(sx - r, sy + 1.0), (sx - r * 0.3, sy - r), (sx + r, sy - r * 0.4), (sx + r * 0.6, sy + 1.0)], sx, sy, k * 40.0), CLAY)
    if alarm:
        H.alarm_mark(f, hx + 16.0, hy - 22.0)
    return f.finish(outline=H.SEPIA_INK, width=1.6, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
