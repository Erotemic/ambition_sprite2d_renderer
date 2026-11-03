"""The Woolly Mammoth: the great beast of the Ice Age in Europe.

A mammoth in a coat of long red-brown hair that hangs from its belly like a
skirt. It has a high domed head, a hump of fat over its shoulders and a
back that slopes down to a small rump. Its ears are small, against the
cold. Its tusks are long and old ivory: they curve out and down, then
forward and up, and turn in at the tips. Its trunk is long and hairy.

It is heavy and slow, and then it charges. At rest it swings its trunk and
its breath steams in the cold. When it sees you it lifts its trunk high
and trumpets. Its windup puts its head down with the tusks at you and
stamps a forefoot; its strike is the charge, head low, with a sweep of the
tusks up at the end. A hit jerks its head back; at its death it goes down
on its knees, then on its side.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_cast_kit as H
from . import _history_europe_kit as E
from . import _stage_kit as S

TARGET_NAME = "woolly_mammoth"
FRAME_SIZE = (256, 256)
ROWS = K.ENEMY_ROWS
GROUND = 250.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Woolly Mammoth", "Quadruped", "Large", "Heavy", "Walk", ["mammoth", "tusks", "charge", "ice_age"],
    "The great beast of the Ice Age in the History dimension's Europe: a mammoth in a coat of long red-brown hair, with a "
    "domed head, a hump and long curved tusks. It trumpets with its trunk up, puts its head down and stamps, then charges.",
    "ice_age",
)

Point = Tuple[float, float]

#: The beast is drawn in its own numbers (ground at `GROUND`), then fitted
#: to the frame at this size about the middle of its ground row.
SIZE = 0.84
PIVOT = (124.0, GROUND)
UPPER, LOWER = 40.0, 40.0
EYE = (40, 26, 20, 255)
MOUTH = (120, 50, 50, 255)
NAIL = (232, 220, 196, 255)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = E.ScaledFrame(FRAME_SIZE, SIZE, PIVOT)

    dx, dy, tilt, pitch, breathe, swing = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    gait, gait_amp, stamp, eyes, fade = 0.0, 0.0, 0.0, "open", 1.0
    trunk_up, trunk_tuck, trumpet, puff, ear = 0.0, 0.0, 0.0, 0.0, 0.0
    fold_front, fold_back, speed, alarm = 0.0, 0.0, 0.0, False
    if anim == "idle":
        breathe = math.sin(cyc)
        swing = math.sin(cyc)
        pitch = 2.0 * math.sin(cyc)
        ear = 0.5 + 0.5 * math.sin(cyc * 2.0)
        puff = max(0.0, math.sin(cyc + 1.0))
    elif anim == "walk":
        gait, gait_amp = cyc, 1.0
        dy = -1.6 * abs(math.sin(cyc))
        pitch = 2.0 * math.sin(cyc * 2.0)
        swing = 0.7 * math.sin(cyc + 0.8)
        ear = 0.3
    elif anim == "notice":
        # The trunk goes up and it trumpets.
        k = math.sin(math.pi * min(1.0, t * 1.25))
        trunk_up, trumpet, pitch, eyes, alarm = k, k, -10.0 * k, "wide", True
        ear, tilt = 1.0 * k, -2.0 * k
    elif anim == "windup":
        # Head down, the tusks at you; a forefoot stamps and the ground shakes.
        pitch, tilt, dx = 16.0, 2.0, -6.0
        stamp = max(0.0, math.sin(cyc * 2.0))
        trunk_tuck, eyes, ear = 1.0, "narrow", 1.0
        puff = 0.5 + 0.5 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The charge: forward fast, head low, then the tusks sweep up.
        u = min(1.0, t * 1.25)
        dx = -6.0 + 22.0 * math.sin(math.pi * 0.5 * u) - 10.0 * max(0.0, u - 0.7) / 0.3
        sweep = max(0.0, math.sin(math.pi * (u - 0.4) / 0.6)) if u > 0.4 else 0.0
        pitch = 16.0 * (1.0 - u) + 6.0 * u - 30.0 * sweep
        tilt = 2.0 - 5.0 * sweep
        gait, gait_amp = cyc * 1.4, 1.3 * (1.0 - 0.5 * sweep)
        speed = math.sin(math.pi * min(1.0, u * 1.5))
        trunk_tuck, eyes, ear = 1.0 - sweep, "narrow", 1.0
    elif anim == "hit":
        k = math.sin(math.pi * t)
        pitch, dx, tilt, eyes, swing = -14.0 * k, -5.0 * k, -2.0 * k, "shut", -0.8 * k
        trumpet = 0.6 * k
    elif anim == "death":
        u = min(1.0, t / 0.8)
        fold_front = min(1.0, u * 1.6)
        fold_back = max(0.0, min(1.0, (u - 0.3) / 0.6))
        tilt = 8.0 * fold_front - 6.0 * fold_back
        dy = 34.0 * (0.6 * fold_front + 0.4 * fold_back)
        pitch, eyes, swing = 20.0 * fold_front, "shut", 0.4
        trunk_tuck = 0.9 * fold_front
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    shoulder_root = (140.0, 150.0)

    def B(pts: Sequence[Point]) -> List[Point]:
        """Points of the body: moved, then turned by the tilt about the shoulder."""
        out = [(x + dx, y + dy + (0.0 if y < 110 else 1.4 * breathe)) for x, y in pts]
        return K.turn(out, shoulder_root[0] + dx, shoulder_root[1] + dy, tilt)

    def leg(root: Point, phase: float, front: bool, near: bool) -> None:
        colour = E.MAMMOTH_FUR if near else E.MAMMOTH_FUR_DARK
        sw = math.sin(phase) * gait_amp
        lift = max(0.0, math.cos(phase)) * 8.0 * gait_amp
        fx = root[0] + 13.0 * sw
        fy = GROUND - 14.0 - lift
        if front and near and stamp:
            fx = root[0] + 4.0
            fy = GROUND - 14.0 - 14.0 * stamp
        fold = fold_front if front else fold_back
        if fold:
            knee = (root[0] + (8.0 if front else -4.0) * fold + 4.0, min(GROUND - 18.0, root[1] + 30.0 + 6.0 * fold))
            foot = (knee[0] + (18.0 if front else -16.0) * fold, GROUND - 14.0)
        else:
            knee, foot = S.joint(root, (fx, fy), UPPER, LOWER, -1.0 if front else 1.0)
        f.limb([root, knee], 28.0, colour)
        f.limb([knee, foot], 24.0, colour)
        # The foot: a round pad with pale nails.
        fx2, fy2 = foot
        f.ellipse(fx2 + 1.0, fy2 + 8.0, 14.0, 5.0, E.MAMMOTH_SKIN)
        for k in (-7.0, 0.0, 7.0):
            f.ellipse(fx2 + k + 3.0, fy2 + 10.0, 2.6, 2.0, NAIL if near else E.IVORY_SHADE, body=False)
        # Hair over the knee.
        E.fur(f, [(knee[0] - 12.0, knee[1] - 6.0), (knee[0] + 12.0, knee[1] - 6.0)], 14.0,
              E.MAMMOTH_FUR_DARK if near else K.shade(E.MAMMOTH_FUR_DARK, 0.8), f"wm:knee:{front}:{near}", 1.6)

    # The far legs.
    leg(B([(70.0, 150.0)])[0], gait + math.pi, False, False)
    leg(B([(146.0, 150.0)])[0], gait, True, False)

    # The tail: short, with a tuft.
    rump = B([(44.0, 112.0)])[0]
    tail = [rump, (rump[0] - 8.0, rump[1] + 14.0), (rump[0] - 10.0 + 3.0 * swing, rump[1] + 30.0)]
    f.limb(tail, 5.0, E.MAMMOTH_FUR_DARK)
    tx, ty = tail[-1]
    f.poly([(tx - 4.0, ty - 3.0), (tx + 4.0, ty - 3.0), (tx + 5.0 + 2.0 * swing, ty + 10.0), (tx - 5.0 + 2.0 * swing, ty + 11.0)], E.MAMMOTH_FUR_DARK)

    # The body: a sloped back up to the hump over the shoulders.
    body = B([(40.0, 128.0), (44.0, 100.0), (60.0, 86.0), (88.0, 74.0), (116.0, 62.0), (132.0, 58.0), (148.0, 64.0), (160.0, 80.0),
              (172.0, 112.0), (172.0, 150.0), (162.0, 176.0), (120.0, 182.0), (80.0, 182.0), (52.0, 174.0), (40.0, 154.0)])
    f.poly(body, E.MAMMOTH_FUR)
    # The shade on the belly and the light on the hump.
    f.poly(B([(48.0, 160.0), (80.0, 172.0), (120.0, 174.0), (164.0, 168.0), (162.0, 178.0), (120.0, 184.0), (80.0, 184.0), (50.0, 176.0)]),
           E.MAMMOTH_FUR_DARK, body=False)
    f.poly(B([(100.0, 72.0), (130.0, 60.0), (146.0, 66.0), (150.0, 84.0), (128.0, 82.0), (106.0, 86.0)]), E.MAMMOTH_FUR_LIGHT, body=False)
    # Long strands of hair down the flank.
    for k in range(7):
        x = 58.0 + k * 16.0
        top = 96.0 - 3.0 * min(k, 4) + (8.0 if k > 4 else 0.0)
        f.ink(B([(x, top), (x - 3.0, top + 30.0), (x - 6.0, top + 60.0)]), 1.6, E.MAMMOTH_FUR_DARK)

    # The near legs.
    leg(B([(78.0, 156.0)])[0], gait, False, True)
    leg(B([(150.0, 156.0)])[0], gait + math.pi, True, True)

    # The skirt of long hair from the belly, over the tops of the legs.
    hem = []
    for k in range(15):
        x = 46.0 + k * 9.0
        hem.append((x, 194.0 + (6.0 if k % 2 else 0.0) + 3.0 * math.sin(k * 1.7 + gait)))
    skirt = B([(42.0, 150.0), (60.0, 168.0), (100.0, 172.0), (150.0, 168.0), (170.0, 150.0), (172.0, 176.0)] + hem[::-1] + [(40.0, 176.0)])
    f.poly(skirt, E.MAMMOTH_FUR)
    for k in range(14):
        x = 50.0 + k * 9.0
        f.ink(B([(x, 172.0), (x - 1.0, 186.0), (x - 3.0, 196.0)]), 1.3, E.MAMMOTH_FUR_DARK)

    # The head, on the neck: turned by `pitch` (down is positive).
    neck = B([(158.0, 100.0)])[0]
    pr = pitch + tilt

    def Hd(pts: Sequence[Point]) -> List[Point]:
        return K.turn([(neck[0] + x, neck[1] + y) for x, y in pts], neck[0], neck[1], pr)

    def tusk(base: Point, near: bool) -> None:
        pts = Hd([base, (base[0] + 10.0, base[1] + 18.0), (base[0] + 28.0, base[1] + 28.0), (base[0] + 48.0, base[1] + 20.0),
                  (base[0] + 58.0, base[1] + 2.0), (base[0] + 52.0, base[1] - 14.0)])
        colour = E.IVORY if near else E.IVORY_SHADE
        mid = E.taper(f, pts, 12.0 if near else 10.0, 4.0, colour)
        if near:
            # Rings of growth, and the shade under the curve.
            for k in range(6, len(mid) - 6, 5):
                x, y = mid[k]
                f.ink([(x - 2.0, y - 2.6), (x + 1.0, y + 2.4)], 0.9, E.IVORY_SHADE)

    # The far tusk, behind the head.
    tusk((30.0, 22.0), False)
    # The head: a tall dome, the face, and the long hair under the jaw.
    head = Hd([(-14.0, -10.0), (-6.0, -34.0), (8.0, -50.0), (22.0, -52.0), (34.0, -40.0), (42.0, -16.0), (44.0, 12.0), (40.0, 30.0),
               (24.0, 38.0), (8.0, 40.0), (-6.0, 34.0), (-16.0, 14.0)])
    f.poly(head, E.MAMMOTH_FUR)
    f.poly(Hd([(8.0, -50.0), (22.0, -52.0), (32.0, -42.0), (22.0, -36.0), (10.0, -40.0)]), E.MAMMOTH_FUR_LIGHT, body=False)
    E.fur(f, Hd([(-6.0, 32.0), (8.0, 38.0), (24.0, 36.0)]), 26.0, E.MAMMOTH_FUR_DARK, "wm:beard", 1.8, lean=-6.0)
    beard = Hd([(-6.0, 30.0), (24.0, 34.0), (20.0, 58.0), (10.0, 52.0), (2.0, 60.0), (-6.0, 50.0)])
    f.poly(beard, E.MAMMOTH_FUR_DARK)
    # The ear: small and round, against the cold.
    ex0, ey0 = Hd([(4.0, -10.0)])[0]
    f.ellipse(ex0 - 1.0 * ear, ey0, 9.0 + 1.5 * ear, 11.0, E.MAMMOTH_FUR_DARK)
    f.ellipse(ex0 - 1.0 * ear + 1.5, ey0 + 1.0, 5.0 + 1.0 * ear, 7.0, K.shade(E.MAMMOTH_SKIN, 1.2), body=False)
    # The eye, small, with a wrinkle over it.
    ex, ey = Hd([(30.0, -14.0)])[0]
    f.ink(Hd([(24.0, -22.0), (32.0, -21.0), (36.0, -17.0)]), 1.1, E.MAMMOTH_FUR_DARK)
    if eyes == "shut":
        f.ink([(ex - 2.6, ey), (ex + 2.6, ey + 0.6)], 1.2, EYE)
    else:
        r = {"open": 2.2, "wide": 3.0, "narrow": 1.4}[eyes]
        f.ellipse(ex, ey, 2.6, r, (236, 226, 200, 255), body=False)
        f.dot(ex + 0.6, ey, 1.4, EYE)
        if eyes == "narrow":
            f.ink([(ex - 3.4, ey - 3.0), (ex + 3.0, ey - 1.0)], 1.3, EYE)

    # The trunk: from the face, hanging, raised, or tucked.
    hang = [(38.0, 18.0), (44.0, 46.0), (46.0, 74.0), (44.0, 100.0), (50.0, 114.0), (58.0, 110.0)]
    raised = [(38.0, 18.0), (54.0, 6.0), (62.0, -22.0), (56.0, -50.0), (44.0, -62.0), (36.0, -56.0)]
    tucked = [(38.0, 18.0), (42.0, 42.0), (34.0, 60.0), (22.0, 62.0), (16.0, 52.0), (20.0, 44.0)]
    pts = []
    for k in range(6):
        hx, hy = hang[k]
        hx += 6.0 * swing * (k / 5.0) ** 1.4
        rx, ry = raised[k]
        tx2, ty2 = tucked[k]
        x = hx + (rx - hx) * trunk_up + (tx2 - hx) * trunk_tuck
        y = hy + (ry - hy) * trunk_up + (ty2 - hy) * trunk_tuck
        pts.append((x, y))
    trunk = Hd(pts)
    widths = (17.0, 15.0, 13.0, 11.0, 9.0)
    for k in range(5):
        f.limb([trunk[k], trunk[k + 1]], widths[k], E.MAMMOTH_FUR)
    for k in range(1, 5):
        a, b = trunk[k - 1], trunk[k + 1]
        nx, ny = b[1] - a[1], -(b[0] - a[0])
        ln = math.hypot(nx, ny) or 1.0
        nx, ny = nx / ln, ny / ln
        x, y = trunk[k]
        w = widths[k] * 0.42
        f.ink([(x - nx * w, y - ny * w), (x + nx * w, y + ny * w)], 1.0, E.MAMMOTH_FUR_DARK)
    tipx, tipy = trunk[-1]
    f.ellipse(tipx, tipy, 5.0, 5.0, E.MAMMOTH_SKIN)
    # The mouth under the trunk: open when it trumpets.
    mx, my = Hd([(32.0, 34.0)])[0]
    if trumpet > 0.1:
        f.ellipse(mx, my, 5.0, 3.0 + 3.0 * trumpet, MOUTH, body=False)
    # The near tusk, in front of the trunk.
    tusk((34.0, 26.0), True)

    if trumpet > 0.1 and trunk_up > 0.3:
        # The sound: lines out of the raised trunk.
        for k in range(3):
            a = math.radians(-60.0 + k * 30.0)
            r0 = 10.0 + 4.0 * k
            f.ink([(tipx + math.cos(a) * r0, tipy + math.sin(a) * r0), (tipx + math.cos(a) * (r0 + 10.0 * trumpet), tipy + math.sin(a) * (r0 + 10.0 * trumpet))],
                  1.8, K.alpha(E.SNOW, trumpet))
    if puff > 0.05 and trunk_up < 0.3:
        E.breath(f, tipx + 6.0, tipy - 4.0, puff, limit=270.0)
    if stamp or speed > 0.1:
        for k in range(2):
            amount = (0.5 + 0.5 * stamp) if stamp else speed
            H.dust(f, B([(150.0, 0.0)])[0][0] - k * 70.0, GROUND - 2.0, 14.0, amount * (1.0 - 0.3 * k), f"wm:dust:{anim}:{i}:{k}", colour=E.SNOW)
    if speed > 0.1:
        for k in range(3):
            y = 110.0 + k * 22.0 + dy
            f.ink([(30.0 - 10.0 * speed, y), (44.0, y)], 1.8, K.alpha(K.WHITE, 0.6 * speed))
    if anim == "death" and t > 0.3:
        H.dust(f, 120.0, GROUND - 2.0, 40.0, min(1.0, (t - 0.3) * 2.0), f"wm:death:{i}", colour=E.SNOW)
    if alarm:
        H.alarm_mark(f, neck[0] - 10.0, 30.0)
    return f.finish(outline=E.OUTLINE, width=1.6, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
