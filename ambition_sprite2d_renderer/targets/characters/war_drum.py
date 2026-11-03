"""The War Drum: a kettle drum of the Resonant Reach that marches.

A timpano: a round bowl of copper with a skin of ivory across its top, a
brass hoop round the skin and brass rods that tune it. It stands on two
stubby legs in brass boots. Its arms are mallets: thin ebony arms, and each
holds a stick with a ball of magenta felt. Its face is on the front of the
bowl, and its mouth is a row of piano keys.

It walks heavily and keeps time on its own skin. Its windup is a crouch
with both mallets high; its strike beats its own skin with one mallet and
slams the ground in front with the other, and rings of sound run along the
floor. A hit dents its skin; at its death the skin tears and the drum tips
over.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K

TARGET_NAME = "war_drum"
FRAME_SIZE = (160, 160)
ROWS = K.ENEMY_ROWS
GROUND = 156.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "War Drum", "Biped", "Large", "Heavy", "Walk", ["music", "drum", "brass"],
    "A kettle drum of the Resonant Reach of the Art dimension on two stubby legs, with mallets for arms. It walks "
    "heavily, crouches with both mallets high, then beats its skin and slams the ground in front of it.",
)

COPPER = (204, 116, 64, 255)
COPPER_SHADE = (146, 72, 40, 255)
COPPER_LIGHT = (240, 170, 120, 255)
IVORY = (250, 242, 220, 255)
IVORY_SHADE = (214, 202, 176, 255)
EBONY = (34, 28, 48, 255)
BRASS = K.GOLD
BRASS_DARK = K.GOLD_DARK
FELT = K.MAGENTA
SOUND = K.CYAN
SOUND_LIGHT = K.CYAN_LIGHT

#: The poses of the near (front) mallet: the hand and the felt ball, from
#: the shoulder.
NEAR = {
    "rest": ((8.0, -14.0), (-2.0, -36.0)),
    "tap": ((6.0, -12.0), (-14.0, -16.0)),
    "up": ((-2.0, -36.0), (-18.0, -60.0)),
    "slam": ((18.0, 14.0), (28.0, 38.0)),
    "low": ((14.0, 10.0), (26.0, 30.0)),
}
#: The far (back) mallet: the same, from its own shoulder.
FAR = {
    "rest": ((-8.0, -14.0), (2.0, -36.0)),
    "tap": ((-6.0, -12.0), (14.0, -16.0)),
    "up": ((-6.0, -34.0), (-14.0, -58.0)),
    "beat": ((2.0, -18.0), (24.0, -14.0)),
    "low": ((-10.0, 12.0), (-16.0, 32.0)),
}


def _mix(poses: dict, a: str, b: str, u: float) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    (ha, ba), (hb, bb) = poses[a], poses[b]
    u = max(0.0, min(1.0, u))
    lerp = lambda p, q: (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)
    return lerp(ha, hb), lerp(ba, bb)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"drum:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cx = 76.0
    tilt, crouch, hop, squash, fade, eyes, alarm, dent, tear = 0.0, 0.0, 0.0, 0.0, 1.0, "angry", False, 0.0, 0.0
    step = (0.0, 0.0)
    near = NEAR["rest"]
    far = FAR["rest"]
    boom, slam_rings, tip = 0.0, 0.0, 0.0
    if anim == "idle":
        squash = 0.02 * math.sin(cyc * 2.0)
        # It keeps time: the near mallet, then the far one.
        u_near = max(0.0, math.sin(cyc))
        u_far = max(0.0, -math.sin(cyc))
        near = _mix(NEAR, "rest", "tap", u_near)
        far = _mix(FAR, "rest", "tap", u_far)
        boom = max(u_near, u_far) ** 4
    elif anim == "walk":
        tilt = 4.0 * math.sin(cyc)
        crouch = 3.0 * abs(math.sin(cyc))
        step = (6.0 * max(0.0, math.sin(cyc)), 6.0 * max(0.0, -math.sin(cyc)))
        near = _mix(NEAR, "rest", "low", 0.5 + 0.4 * math.sin(cyc))
        far = _mix(FAR, "rest", "low", 0.5 - 0.4 * math.sin(cyc))
    elif anim == "notice":
        hop = 10.0 * math.sin(math.pi * t)
        eyes, alarm = "wide", True
        near = _mix(NEAR, "rest", "up", math.sin(math.pi * t))
        far = _mix(FAR, "rest", "up", math.sin(math.pi * t))
    elif anim == "windup":
        crouch, tilt = 8.0 + 1.0 * math.sin(cyc * 2.0), -8.0
        near = _mix(NEAR, "up", "up", 0.0)
        far = _mix(FAR, "up", "up", 0.0)
        near = ((near[0][0], near[0][1] + 1.5 * math.sin(cyc * 2.0)), (near[1][0], near[1][1] + 2.0 * math.sin(cyc * 2.0)))
    elif anim == "attack_side":
        swing = min(1.0, t * 2.4)
        tilt = -8.0 + 18.0 * swing
        crouch = 8.0 * (1.0 - swing) + 6.0 * swing
        hop = 8.0 * math.sin(math.pi * min(1.0, t * 2.4))
        cx += 8.0 * swing
        near = _mix(NEAR, "up", "slam", swing ** 1.5)
        far = _mix(FAR, "up", "beat", swing ** 1.5)
        if t > 0.35:
            slam_rings = (t - 0.35) / 0.65
            boom = 1.0 - slam_rings
    elif anim == "hit":
        squash, dent, eyes = 0.10 * math.sin(math.pi * t) + 0.04, 1.0, "shut"
        tilt = -8.0
        cx -= 5.0 * math.sin(math.pi * t)
        near = _mix(NEAR, "rest", "up", 0.5)
        far = _mix(FAR, "rest", "up", 0.5)
        boom = 1.0 - t * 0.6
    elif anim == "death":
        tear, eyes, tip = t, "x", min(1.0, t * 1.4)
        crouch = 14.0 * tip
        near = _mix(NEAR, "rest", "low", t)
        far = _mix(FAR, "rest", "low", t)
        fade = 1.0 - max(0.0, t - 0.6) / 0.4

    leg_h = 18.0 - crouch * 0.6
    base_y = GROUND - leg_h - hop
    depth = 44.0 * (1.0 - squash)
    rx, ry = 40.0 * (1.0 + squash * 0.6), 9.0
    top = base_y - depth
    pivot = (cx - 34.0, GROUND) if tip else (cx, GROUND)
    angle = tilt - 30.0 * tip * tip

    def at(points):
        pts = K.turn(points, pivot[0], pivot[1], angle)
        if tip:
            pts = [(x, y + 4.0 * tip) for x, y in pts]
        return pts

    def pt(x, y):
        return at([(x, y)])[0]

    # The far mallet, behind the bowl.
    far_sh = (cx - rx + 2.0, top + 14.0)
    _mallet(f, at, far_sh, far, back=True)

    # The stubby legs in brass boots.
    for k, side in enumerate((-1.0, 1.0)):
        lift = step[k]
        hip = pt(cx + side * 16.0, base_y - 2.0)
        if tip:
            foot = (hip[0] + side * 4.0, min(GROUND - 3.0, hip[1] + 14.0))
        else:
            foot = (cx + side * 17.0 + lift * 0.6, GROUND - 4.0 - lift)
        f.limb([hip, foot], 9.0, EBONY)
        boot = [(foot[0] - 7.0, foot[1] + 3.5), (foot[0] + 10.0, foot[1] + 3.5), (foot[0] + 9.0, foot[1] - 2.0), (foot[0] - 6.0, foot[1] - 4.0)]
        f.poly(boot, BRASS)
        f.ink([(foot[0] - 6.0, foot[1] - 1.0), (foot[0] + 8.0, foot[1] - 0.6)], 0.8, BRASS_DARK)

    # The bowl of copper: a round half below the rim, and a collar at its foot.
    bowl = [(cx + rx * math.cos(a), top + depth * math.sin(a)) for a in (math.pi * k / 24.0 for k in range(25))]
    f.poly(at(bowl), COPPER)
    shade_pts = [(cx + rx * math.cos(a), top + depth * math.sin(a)) for a in (math.pi * (0.55 + 0.45 * k / 12.0) for k in range(13))]
    f.poly(at(shade_pts + [(cx - rx * 0.6, top + 6.0)]), COPPER_SHADE, body=False)
    f.poly(at([(cx - rx * 0.30, top + 8.0), (cx - rx * 0.18, top + 8.0), (cx - rx * 0.24, top + depth * 0.70), (cx - rx * 0.34, top + depth * 0.62)]), COPPER_LIGHT, body=False)
    f.poly(at([(cx - 14.0, base_y - 4.0), (cx + 14.0, base_y - 4.0), (cx + 12.0, base_y + 2.0), (cx - 12.0, base_y + 2.0)]), EBONY)
    # The brass rods that tune the skin, down the front of the bowl.
    for a in (0.35, 0.95, 1.6, 2.25, 2.8):
        x = cx + rx * math.cos(a)
        y0 = top + ry * math.sin(a) + 3.0
        f.limb(at([(x, y0), (x * 0.96 + cx * 0.04, y0 + 12.0)]), 2.0, BRASS, body=False)
        f.ellipse(*pt(x * 0.96 + cx * 0.04, y0 + 12.5), 2.0, 2.0, BRASS_DARK, body=False)

    # The skin, and the hoop of brass round it, with the handles of the rods.
    for a in (0.6, 1.6, 2.6, 3.7, 4.6, 5.6):
        x, y = cx + (rx + 1.0) * math.cos(a), top + (ry + 1.0) * math.sin(a)
        f.limb(at([(x, y), (x, y - 5.0)]), 1.6, BRASS)
        f.limb(at([(x - 3.0, y - 5.0), (x + 3.0, y - 5.0)]), 1.6, BRASS)
    f.poly(at(K.ellipse_points(cx, top, rx + 1.5, ry + 2.5, 32)), BRASS)
    f.poly(at(K.ellipse_points(cx, top - 0.8, rx - 1.5, ry - 0.5, 32)), IVORY)
    f.poly(at(K.ellipse_points(cx + 4.0, top + 1.6, rx - 8.0, ry - 4.5, 24)), IVORY_SHADE, body=False)
    if dent:
        f.poly(at(K.ellipse_points(cx + 2.0, top + 0.6, 14.0, 3.4, 18)), K.shade(IVORY_SHADE, 0.8), body=False)
    if tear:
        f.ink(at([(cx - 24.0, top - 2.0), (cx - 10.0, top + 1.0), (cx - 2.0, top - 2.0), (cx + 12.0, top + 2.0), (cx + 22.0 * (0.4 + tear), top - 1.0)]), 1.6 + tear, EBONY)

    # The face, to the front of the bowl.
    fx, fy = cx + 14.0, top + 20.0
    for k, ox in enumerate((-9.0, 9.0)):
        ex, ey = pt(fx + ox, fy)
        if eyes == "x":
            for s in (-1.0, 1.0):
                f.ink([(ex - 3.0, ey - 3.0 * s), (ex + 3.0, ey + 3.0 * s)], 1.6, EBONY)
            continue
        if eyes == "shut":
            f.ink([(ex - 4.0, ey + 0.5), (ex, ey - 1.5), (ex + 4.0, ey + 0.5)], 1.6, EBONY)
            continue
        big = 1.25 if eyes == "wide" else 1.0
        f.ellipse(ex, ey, 4.6 * big, 5.2 * big, IVORY, body=False)
        f.dot(ex + 1.4, ey + 0.6, 2.2 * big, EBONY)
        if eyes == "angry":
            inner = 1.0 if ox < 0 else -1.0
            f.poly(at([(fx + ox - 6.0, fy - 7.0 - inner * 1.6), (fx + ox + 6.0, fy - 7.0 + inner * 1.6), (fx + ox + 6.0, fy - 4.6 + inner * 1.6), (fx + ox - 6.0, fy - 4.6 - inner * 1.6)]), EBONY, body=False)
    # The mouth: a row of piano keys, ivory, with the black keys over them.
    mw, my = 14.0, fy + 13.0
    open_h = 6.0 + (2.0 if eyes in ("wide", "x") or anim == "attack_side" else 0.0)
    f.poly(at([(fx - mw, my - 1.0), (fx + mw, my - 2.0), (fx + mw - 1.0, my + open_h), (fx - mw + 1.0, my + open_h + 0.6)]), EBONY, body=False)
    keys = 6
    for k in range(keys):
        x0 = fx - mw + 1.6 + k * (2.0 * mw - 3.2) / keys
        x1 = x0 + (2.0 * mw - 3.2) / keys - 0.8
        f.poly(at([(x0, my - 0.4), (x1, my - 0.6), (x1, my + open_h - 1.2), (x0, my + open_h - 1.0)]), IVORY, body=False)
    for k in (1, 2, 4, 5):
        x = fx - mw + 1.6 + k * (2.0 * mw - 3.2) / keys
        f.poly(at([(x - 1.3, my - 0.6), (x + 1.3, my - 0.6), (x + 1.3, my + open_h * 0.55), (x - 1.3, my + open_h * 0.55)]), EBONY, body=False)

    # The near mallet, in front of the bowl.
    near_sh = (cx + rx - 2.0, top + 14.0)
    ball = _mallet(f, at, near_sh, near, back=False)

    # Sound: a ring off the skin when it is struck, and rings along the floor.
    if boom > 0.05:
        bx, by = pt(cx + 4.0, top - 2.0)
        r = 18.0 + 30.0 * (1.0 - boom)
        f.glow_line(K.ellipse_points(bx, by, r * 1.3, r * 0.45, 30) + [K.ellipse_points(bx, by, r * 1.3, r * 0.45, 30)[0]], 1.8, K.alpha(SOUND, 0.85 * boom))
    if slam_rings > 0.0:
        hx = min(ball[0], 134.0)
        for k in range(3):
            u = slam_rings - k * 0.22
            if 0.0 < u < 1.0:
                rr = 6.0 + 22.0 * u
                pts = K.ellipse_points(hx, GROUND - 2.0, rr, rr * 0.22, 26)
                pts = [(min(x, 156.0), y) for x, y in pts]
                f.glow_line(pts + [pts[0]], 2.2 - u, K.alpha(SOUND, 0.95 * (1.0 - u)))
        for k in range(6):
            side = -1.0 if k % 2 else 1.0
            x = hx + side * (4.0 + 5.0 * k * slam_rings)
            f.ellipse(min(x, 150.0), GROUND - 3.0 - 2.0 * (k % 3), 4.0 + 2.0 * slam_rings, 2.6, K.alpha(K.PAPER_SHADE, 0.7 * (1.0 - slam_rings)), body=False)
        for k in range(3):
            x0 = hx - 8.0 + k * 8.0
            f.ink([(x0, GROUND), (x0 + 3.0, GROUND - 4.0), (x0 + 1.0, GROUND - 7.0)], 1.0, EBONY)
    if alarm:
        ax, ay = cx + 50.0, top - 30.0
        f.limb([(ax, ay - 10.0), (ax, ay)], 3.0, SOUND)
        f.ellipse(ax, ay + 5.5, 2.0, 2.0, SOUND)
    if anim == "death" and t > 0.2:
        # The last note leaks out of the tear.
        for k in range(3):
            u = (t - 0.2) / 0.8
            x, y = pt(cx - 6.0 + k * 10.0, top - 6.0 - 14.0 * u - k * 4.0)
            f.glow(x, y, 2.0, K.alpha(SOUND_LIGHT, 0.8 * (1.0 - u)))
    del rng
    return f.finish(width=1.8, fade=fade)


def _mallet(f: K.Frame, at, shoulder, pose, back: bool):
    """One mallet arm: a thin ebony arm, a stick and a ball of felt. Returns
    where the ball is."""
    (hx, hy), (bx, by) = pose
    sx, sy = shoulder
    hand = (sx + hx, sy + hy)
    ball = (sx + bx, sy + by)
    elbow = ((sx + hand[0]) / 2.0 + (-3.0 if back else 3.0), (sy + hand[1]) / 2.0 + 3.0)
    pts = at([(sx, sy), elbow, hand, ball])
    shade = 0.8 if back else 1.0
    f.limb(pts[:3], 3.6, K.shade(EBONY, 1.2 if not back else 1.0))
    f.limb([pts[2], pts[3]], 2.6, K.shade(K.WOOD, shade))
    f.ellipse(pts[2][0], pts[2][1], 3.2, 3.2, K.shade(EBONY, 1.3))
    f.ellipse(pts[3][0], pts[3][1], 6.2, 6.2, K.shade(FELT, shade))
    f.ellipse(pts[3][0] - 1.8, pts[3][1] - 1.8, 2.0, 2.0, K.alpha(K.MAGENTA_LIGHT, 0.9 * shade), body=False)
    return pts[3]


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
