"""The Vandal: a barbarian of the Fall of Rome, with a pot of paint.

A shaggy barbarian with a horned iron helmet (the horns are a legend, and he
likes the legend), a braided ginger beard, a fur vest over a green tunic,
checked trousers bound with straps, and boots. In one hand he has a little
wooden pot of black paint; in the other, a brush.

He does not burn Rome. He paints moustaches on its statues, and on you. He
is quick: at rest he dips his brush and looks for a face to improve. When
he sees you he grins and lifts the brush; his windup draws it back over
his shoulder, and his strike is a swipe that leaves a curled moustache of
paint in the air. A hit slops paint out of the pot; at his death he falls
on his back and the paint runs out in a puddle.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_cast_kit as H
from . import _stage_kit as S

TARGET_NAME = "vandal"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 124.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Vandal", "Biped", "Standard", "Light", "Walk", ["barbarian", "paint", "brush", "horned_helmet"],
    "A barbarian of the Fall of Rome in the History dimension: a horned helmet, a ginger beard, a fur vest, a pot of black "
    "paint and a brush. He paints moustaches on statues: his swipe leaves a curled moustache of paint in the air.",
    "classical",
)

THIGH, SHIN = 12.5, 12.5
UPPER_ARM, FOREARM = 10.0, 9.5
TORSO = 18.0
TUNIC = (86, 130, 70, 255)
TUNIC_SHADE = (58, 92, 48, 255)
FUR = (138, 96, 60, 255)
FUR_DARK = (92, 60, 36, 255)
TROUSER = (168, 120, 70, 255)
TROUSER_CHECK = (118, 70, 40, 255)
BEARD = (206, 112, 44, 255)
BEARD_DARK = (150, 70, 24, 255)
IRON = (120, 122, 136, 255)
IRON_DARK = (78, 78, 92, 255)
HORN = (240, 228, 196, 255)
HORN_SHADE = (196, 176, 136, 255)
PAINT = (30, 26, 34, 255)
PAINT_SHINE = (120, 116, 140, 255)
SKIN = (238, 186, 150, 255)
SKIN_SHADE = (196, 140, 108, 255)


def _moustache(cx: float, cy: float, s: float):
    """The curled handlebar moustache: a list of strokes (point lists)."""
    out = []
    for side in (-1.0, 1.0):
        pts = []
        for k in range(12):
            u = k / 11.0
            # From the middle out, then a curl up and back in.
            x = side * (2.0 + 13.0 * u) * s
            y = (2.0 * math.sin(math.pi * u) - 7.0 * max(0.0, u - 0.6) ** 1.2 * 3.0) * s
            pts.append((cx + x, cy + y))
        a = math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])
        cxr, cyr = pts[-1]
        for k in range(1, 6):
            a2 = a - side * 0.7 * k
            cxr += math.cos(a2) * 1.8 * s
            cyr += math.sin(a2) * 1.8 * s
            pts.append((cxr, cyr))
        out.append(pts)
    return out


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    hip_x, crouch, lean, bob = 52.0, 0.0, 0.0, 0.0
    near_foot, far_foot = (4.0, 0.0), (-4.0, 0.0)
    brush_hand, pot_hand = None, None
    brush_angle = -60.0
    grin, alarm, fade, rot = 0.4, False, 1.0, 0.0
    stroke, slop, puddle = 0.0, 0.0, 0.0
    if anim == "idle":
        # He dips his brush in the pot, and looks about for a face.
        bob = 0.6 * math.sin(cyc)
        dip = max(0.0, math.sin(cyc))
        pot_hand = (hip_x + 12.0, 94.0)
        brush_hand = (hip_x + 13.0 + 1.0 * math.cos(cyc), 76.0 + 6.0 * dip)
        brush_angle = 86.0 - 4.0 * dip
        lean = 6.0 * dip
        grin = 0.5
    elif anim == "walk":
        # A quick sneaking trot, bent forward, the pot swinging.
        near_foot = (9.0 * math.sin(cyc), 6.0 * max(0.0, math.cos(cyc)))
        far_foot = (-9.0 * math.sin(cyc), 6.0 * max(0.0, -math.cos(cyc)))
        bob = -2.0 * abs(math.cos(cyc))
        lean = 12.0
        pot_hand = (hip_x - 8.0 - 4.0 * math.sin(cyc), 104.0 + 2.0 * math.cos(cyc))
        brush_hand = (hip_x + 14.0 + 3.0 * math.sin(cyc), 84.0)
        brush_angle = -30.0
    elif anim == "notice":
        # A wide grin, the brush up: a face to improve.
        u = math.sin(math.pi * min(1.0, t * 1.4))
        bob = -3.0 * u
        lean = -4.0
        pot_hand = (hip_x - 6.0, 100.0)
        brush_hand = (hip_x + 14.0, 66.0)
        brush_angle = -80.0
        grin, alarm = 1.0, True
    elif anim == "windup":
        # The brush back over his shoulder, low on his toes.
        crouch, lean = 4.0 + 0.6 * math.sin(cyc * 2.0), -6.0
        near_foot, far_foot = (10.0, 0.0), (-10.0, 0.0)
        pot_hand = (hip_x + 8.0, 98.0)
        brush_hand = (hip_x - 8.0, 66.0 + 1.0 * math.sin(cyc * 2.0))
        brush_angle = -150.0
        grin = 1.0
    elif anim == "attack_side":
        # The swipe: the brush sweeps across in front and leaves a moustache.
        sw = min(1.0, t * 1.5)
        e = 1.0 - (1.0 - sw) ** 2
        hip_x += 6.0 * sw
        crouch, lean = 4.0, -6.0 + 20.0 * e
        near_foot, far_foot = (14.0, 0.0), (-10.0, 0.0)
        pot_hand = (hip_x - 8.0, 100.0)
        a = math.radians(-150.0 + 170.0 * e)
        brush_hand = (hip_x + 4.0 + math.cos(a) * 18.0, 80.0 + math.sin(a) * 16.0)
        brush_angle = -150.0 + 170.0 * e
        stroke = max(0.0, (t - 0.15) / 0.85)
        grin = 1.0
    elif anim == "hit":
        hip_x -= 4.0 * math.sin(math.pi * t)
        lean, crouch = -14.0, 2.0
        pot_hand = (hip_x + 12.0, 90.0)
        brush_hand = (hip_x - 14.0, 80.0)
        brush_angle = -120.0
        slop, grin = 1.0 - t * 0.5, -1.0
    elif anim == "death":
        fall = min(1.0, t / 0.75)
        crouch = 8.0 * min(1.0, fall * 2.0)
        hip_x += 30.0 * fall
        rot = -80.0 * min(1.0, max(0.0, (fall - 0.15) / 0.7)) ** 1.2
        pot_hand = (hip_x + 14.0, 96.0)
        brush_hand = (hip_x - 14.0, 84.0)
        brush_angle = -110.0
        grin = -1.0
        puddle = max(0.0, (t - 0.4) / 0.6)
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    pen = S.Pen(f, (hip_x - 6.0, GROUND - 3.0), rot, (0.0, 9.0 * rot / 80.0))
    if puddle > 0.0:
        # The paint runs out of the pot where it fell.
        qx = pen.at(*pot_hand)[0]
        f.ellipse(qx + 4.0, GROUND - 1.5, 5.0 + 12.0 * puddle, 1.6 + 1.2 * puddle, PAINT, body=False)
        f.ellipse(qx + 1.0, GROUND - 2.2, 2.0 + 4.0 * puddle, 0.6, PAINT_SHINE, body=False)
    hip_y = GROUND - (THIGH + SHIN - 1.0) + crouch + bob
    lr = math.radians(lean)

    def up(p, length):
        return (p[0] + math.sin(lr) * length, p[1] - math.cos(lr) * length)

    def across(p, w):
        return (p[0] + math.cos(lr) * w, p[1] + math.sin(lr) * w)

    hip = (hip_x, hip_y)
    shoulder = up(hip, TORSO - 3.0)
    neck = up(hip, TORSO)
    hx, hy = up(neck, 7.5)

    def a_leg(spec, colour, check):
        dx, lift = spec
        foot = (hip_x + dx, GROUND - 2.0 - lift)
        knee, ankle = H.leg(pen, hip, foot, THIGH, SHIN, 5.0, colour)
        # The cross straps on the shin, and a boot.
        for u in (0.3, 0.6):
            a, b = H.lerp(knee, ankle, u), H.lerp(knee, ankle, u + 0.18)
            pen.ink([(a[0] - 2.4, a[1]), (b[0] + 2.4, b[1])], 0.7, check)
            pen.ink([(a[0] + 2.4, a[1]), (b[0] - 2.4, b[1])], 0.7, check)
        pen.poly([(ankle[0] - 3.0, ankle[1] - 3.0), (ankle[0] + 2.5, ankle[1] - 3.0), (ankle[0] + 6.5, ankle[1] + 0.5), (ankle[0] + 6.5, ankle[1] + 2.2),
                  (ankle[0] - 3.0, ankle[1] + 2.2)], FUR_DARK)

    a_leg(far_foot, K.shade(TROUSER, 0.8), K.shade(TROUSER_CHECK, 0.8))
    # The far arm with the pot. When he dips his brush, the pot is in front.
    if pot_hand is None:
        pot_hand = (hip_x - 6.0, 100.0)
    pot_front = anim == "idle"

    def pot():
        H.arm(pen, across(shoulder, -2.0), pot_hand, UPPER_ARM, FOREARM, 4.2, SKIN_SHADE, elbow_out=1.0)
        px, py = pot_hand
        pen.limb([(px - 4.0, py + 1.0), (px, py - 2.0), (px + 4.0, py + 1.0)], 1.0, FUR_DARK, body=False)
        pen.poly([(px - 5.0, py + 1.0), (px + 5.0, py + 1.0), (px + 4.0, py + 10.0), (px - 4.0, py + 10.0)], K.WOOD)
        pen.ink([(px - 4.6, py + 4.0), (px + 4.6, py + 4.0)], 0.8, K.WOOD_DARK)
        pen.ink([(px - 4.2, py + 8.0), (px + 4.2, py + 8.0)], 0.8, K.WOOD_DARK)
        pen.ellipse(px, py + 1.2, 4.6, 1.3, PAINT, body=False)
        pen.limb([(px - 1.0, py + 2.0), (px - 1.4, py + 6.0)], 1.4, PAINT, body=False)
        if slop > 0.0:
            for k in range(4):
                a = math.radians(-120.0 + 25.0 * k)
                r = 5.0 + 9.0 * slop
                pen.ellipse(px + math.cos(a) * r, py + math.sin(a) * r, 1.6, 1.4, PAINT)

    if not pot_front:
        pot()

    # The body: a green tunic, a fur vest, a belt.
    hb, hf = across(hip, -6.0), across(hip, 6.0)
    sb, sf = across(shoulder, -6.5), across(shoulder, 6.0)
    pen.poly([across(up(hip, -5.0), -7.0), across(up(hip, -5.0), 7.0), hf, sf, across(neck, 3.0), across(neck, -3.0), sb, hb], TUNIC)
    pen.poly([across(up(hip, -5.0), -7.0), across(up(hip, -5.0), -3.0), across(shoulder, -3.0), sb], TUNIC_SHADE, body=False)
    vest = [across(up(hip, 2.0), -7.0), across(up(hip, 1.0), -1.0), across(up(hip, 10.0), 1.5), across(shoulder, 2.0), across(neck, -1.0), sb]
    pen.poly(vest, FUR)
    for k in range(5):
        a = H.lerp(vest[0], vest[-1], k / 4.0)
        pen.ink([(a[0] + 0.5, a[1]), (a[0] + 2.5, a[1] + 1.5)], 0.7, FUR_DARK)
    pen.limb([across(up(hip, 1.0), -6.5), across(up(hip, 1.0), 6.5)], 2.0, FUR_DARK, body=False)
    pen.ellipse(across(up(hip, 1.0), 3.0)[0], across(up(hip, 1.0), 3.0)[1], 1.4, 1.4, K.GOLD, body=False)

    a_leg(near_foot, TROUSER, TROUSER_CHECK)
    if pot_front:
        pot()

    # The head: a horned helmet, a mane of ginger hair and a braided beard.
    tilt = lean * 0.3

    def Hd(x, y):
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    pen.poly([Hd(-6.0, -4.0), Hd(-9.5, 2.0), Hd(-10.5, 9.0), Hd(-7.0, 7.0), Hd(-6.5, 11.0), Hd(-3.0, 5.0)], BEARD)
    pen.ellipse(hx, hy, 6.4, 6.8, SKIN)
    pen.poly([Hd(5.4, -1.4), Hd(8.6, 1.4), Hd(5.6, 2.8)], SKIN)
    pen.ellipse(Hd(6.8, 1.0)[0], Hd(6.8, 1.0)[1], 1.4, 1.2, (226, 120, 100, 255), body=False)
    beard = [Hd(-3.0, 1.0), Hd(1.0, 3.0), Hd(7.0, 3.6), Hd(6.0, 8.0), Hd(3.5, 10.0), Hd(3.0, 15.0), Hd(1.0, 15.5), Hd(0.0, 10.0), Hd(-3.0, 7.0)]
    pen.poly(beard, BEARD)
    pen.ink([Hd(1.2, 10.5), Hd(3.0, 11.6)], 0.6, BEARD_DARK)
    pen.ink([Hd(1.0, 12.8), Hd(2.8, 13.8)], 0.6, BEARD_DARK)
    # The mouth: a grin in the beard.
    mx, my = Hd(4.4, 4.6)
    if grin > 0.7:
        pen.poly([(mx - 2.6, my - 0.6), (mx + 2.4, my - 0.8), (mx + 1.6, my + 1.6), (mx - 1.8, my + 1.4)], K.INK, body=False)
        pen.poly([(mx - 2.0, my - 0.4), (mx + 1.8, my - 0.6), (mx + 1.6, my + 0.3), (mx - 1.8, my + 0.4)], K.WHITE, body=False)
    elif grin < 0.0:
        pen.ellipse(mx, my + 0.5, 1.2, 1.6, K.INK, body=False)
    else:
        pen.ink([(mx - 2.4, my), (mx, my + 0.9), (mx + 2.2, my - 0.6)], 0.9)
    ex, ey = Hd(3.4, -1.4)
    if anim in ("hit", "death"):
        pen.ink([(ex - 1.2, ey - 1.2), (ex + 1.2, ey + 1.2)], 0.8)
        pen.ink([(ex - 1.2, ey + 1.2), (ex + 1.2, ey - 1.2)], 0.8)
    else:
        pen.dot(ex, ey, 1.1)
        pen.dot(ex - 0.3, ey - 0.4, 0.35, K.WHITE)
    pen.ink([Hd(1.6, -3.6), Hd(3.4, -4.4), Hd(5.6, -3.2)], 0.9, BEARD_DARK)
    # The helmet: an iron cap with a rim, and two horns that curve up.
    for side, col in ((-1.0, HORN_SHADE), (1.0, HORN)):
        base = Hd(side * 4.6, -5.0)
        horn = [Hd(side * 3.0, -5.6), Hd(side * 6.5, -5.4), Hd(side * 9.5, -8.0), Hd(side * 10.5, -12.5), Hd(side * 9.0, -16.0),
                Hd(side * 8.6, -12.0), Hd(side * 6.0, -8.8), Hd(side * 3.0, -8.0)]
        pen.poly(horn, col)
        pen.ink([Hd(side * 7.2, -7.0), Hd(side * 8.2, -8.4)], 0.6, HORN_SHADE)
        del base
    cap = [Hd(-6.8, -2.0), Hd(-6.0, -6.2), Hd(-2.0, -8.6), Hd(3.0, -8.4), Hd(6.4, -5.4), Hd(7.0, -2.0)]
    pen.poly(cap, IRON)
    pen.limb([Hd(-7.0, -2.2), Hd(7.2, -2.2)], 1.8, IRON_DARK)
    pen.ink([Hd(-1.0, -8.2), Hd(-1.0, -2.6)], 0.8, IRON_DARK)
    pen.ink([Hd(-4.0, -6.0), Hd(1.0, -7.6)], 0.6, K.shade(IRON, 1.3))

    # The near arm and the brush.
    if brush_hand is None:
        brush_hand = (hip_x + 10.0, 92.0)
    H.arm(pen, across(shoulder, 2.0), brush_hand, UPPER_ARM, FOREARM, 4.2, SKIN, elbow_out=1.0)
    a = math.radians(brush_angle)
    d = (math.cos(a), math.sin(a))
    bx, by = brush_hand
    pen.limb([(bx - d[0] * 5.0, by - d[1] * 5.0), (bx + d[0] * 9.0, by + d[1] * 9.0)], 2.0, K.WOOD)
    tip = (bx + d[0] * 16.0, by + d[1] * 16.0)
    pen.limb([(bx + d[0] * 9.0, by + d[1] * 9.0), tip], 3.4, PAINT)
    pen.ellipse(bx, by, 2.4, 2.2, SKIN)
    if stroke > 0.0:
        # The moustache of paint, drawn in the air by the swipe.
        s = 1.0 + 0.25 * stroke
        cx, cy = hip_x + 36.0, 80.0
        for pts in _moustache(cx, cy, s):
            k = max(2, int(len(pts) * min(1.0, stroke * 1.6)))
            pen.ink(pts[:k], 4.2, K.alpha(PAINT, 0.95 * (1.0 - max(0.0, stroke - 0.7) / 0.3 * 0.6)))
        pen.ellipse(cx, cy + 1.0, 2.6, 2.2, K.alpha(PAINT, 0.9), body=False)
    if alarm:
        H.alarm_mark(f, hx + 14.0, hy - 26.0)
    return f.finish(outline=H.SEPIA_INK, width=1.4, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
