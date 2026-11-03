"""The Desert Bandit: a quick raider of the Silk Road.

A lean raider on foot (his camel left without him) in an indigo head wrap
that covers his face to the eyes, a loose ochre coat to the knee with a
crimson sash, baggy sand trousers and soft boots. He has a curved sword of
bright steel with a gold hilt. The tails of his wrap and of his sash fly
out behind him.

He is fast and he does not stay. At rest he bounces on his toes and turns
his sword over in his hand. He runs low. When he sees you his eyes narrow
and the sword comes up; his windup coils him low with the sword back by
his hip, and his strike is a lunge and a wide slash that leaves an arc of
light. A hit throws him back; at his death he falls, and his sword drops
point first into the sand and stands there.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_cast_kit as H
from . import _stage_kit as S

TARGET_NAME = "desert_bandit"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 124.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Desert Bandit", "Biped", "Standard", "Light", "Walk", ["raider", "curved_sword", "face_wrap", "fast"],
    "A quick raider of the Silk Road in the History dimension: an indigo face wrap, an ochre coat, a crimson sash and a "
    "curved sword. He coils low, lunges with a wide slash, and is gone again.",
    "silk",
)

THIGH, SHIN = 12.0, 12.0
UPPER_ARM, FOREARM = 9.5, 9.0
TORSO = 17.0
COAT = H.OCHRE
COAT_SHADE = H.OCHRE_DARK
TROUSER = (226, 204, 160, 255)
TROUSER_SHADE = (180, 156, 112, 255)
WRAP = (70, 74, 150, 255)
WRAP_DARK = (40, 42, 96, 255)
BOOT = (110, 70, 44, 255)
SASH = H.CRIMSON
SKIN = (196, 140, 98, 255)


def _sword(pen: S.Pen, grip, angle: float) -> tuple:
    """The curved sword at `grip`, pointed at `angle`. Returns its tip."""
    a = math.radians(angle)
    d = (math.cos(a), math.sin(a))
    nrm = (-d[1], d[0])

    def at(s: float, w: float = 0.0):
        return (grip[0] + d[0] * s + nrm[0] * w, grip[1] + d[1] * s + nrm[1] * w)

    # The blade curves to its back edge, and widens toward its point.
    back = [at(2.0 + 22.0 * k / 8.0, -(1.6 * (k / 8.0) ** 2) * 4.0 - 0.8) for k in range(9)]
    edge = [at(2.0 + 22.0 * k / 8.0, -(1.6 * (k / 8.0) ** 2) * 4.0 + 1.0 + 1.2 * k / 8.0) for k in range(9)]
    tip = at(27.0, -8.0)
    pen.poly(back + [tip] + edge[::-1], H.STEEL)
    pen.ink([at(4.0, 0.0), at(18.0, -2.6)], 0.6, K.WHITE)
    pen.limb([at(0.6, -3.2), at(0.6, 3.2)], 1.6, K.GOLD)
    pen.limb([at(-6.0), at(0.0)], 2.2, K.WOOD_DARK)
    pen.ellipse(at(-6.4)[0], at(-6.4)[1], 1.4, 1.4, K.GOLD)
    return tip


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    hip_x, crouch, lean, bob = 50.0, 0.0, 0.0, 0.0
    near_foot, far_foot = (5.0, 0.0), (-5.0, 0.0)
    hand, sword = None, -60.0
    eyes, alarm, fade, rot = "open", False, 1.0, 0.0
    wind, slash, stuck = 0.3, 0.0, 0.0
    if anim == "idle":
        # On his toes, turning the sword over in his hand.
        bob = -1.2 * abs(math.sin(cyc))
        near_foot, far_foot = (7.0, 1.0 * abs(math.sin(cyc))), (-6.0, 0.0)
        hand = (hip_x + 12.0, 96.0 - 2.0 * math.sin(cyc))
        sword = -70.0 + 360.0 * t if i in (2, 3) else -70.0 + 10.0 * math.sin(cyc)
        wind = 0.3 + 0.2 * math.sin(cyc)
    elif anim == "walk":
        # A low, fast run.
        near_foot = (11.0 * math.sin(cyc), 7.0 * max(0.0, math.cos(cyc)))
        far_foot = (-11.0 * math.sin(cyc), 7.0 * max(0.0, -math.cos(cyc)))
        bob = -2.5 * abs(math.cos(cyc))
        lean = 16.0
        hand = (hip_x + 6.0 - 6.0 * math.sin(cyc), 100.0)
        sword = 160.0
        wind = 1.0
    elif anim == "notice":
        u = math.sin(math.pi * min(1.0, t * 1.4))
        crouch, eyes, alarm = 3.0 * u, "narrow", True
        near_foot, far_foot = (9.0, 0.0), (-8.0, 0.0)
        hand = (hip_x + 16.0, 84.0)
        sword = -50.0
        wind = 0.5
    elif anim == "windup":
        # Coiled low, the sword back by his hip.
        crouch, lean = 7.0 + 0.6 * math.sin(cyc * 2.0), 10.0
        near_foot, far_foot = (12.0, 0.0), (-12.0, 0.0)
        hand = (hip_x - 12.0, 102.0)
        sword = 170.0
        eyes, wind = "narrow", 0.6
    elif anim == "attack_side":
        # The lunge and a wide slash, up and across.
        sw = min(1.0, t * 1.7)
        e = 1.0 - (1.0 - sw) ** 2
        hip_x += 18.0 * e
        crouch, lean = 6.0, 10.0 + 10.0 * e
        near_foot, far_foot = (16.0, 0.0), (-14.0, 0.0)
        a = math.radians(160.0 - 200.0 * e)
        hand = (hip_x + 4.0 + math.cos(a) * 16.0, 88.0 + math.sin(a) * 10.0)
        sword = 170.0 - 210.0 * e
        slash = e if t < 0.8 else 0.0
        eyes, wind = "narrow", 1.0
    elif anim == "hit":
        hip_x -= 5.0 * math.sin(math.pi * t)
        lean, crouch, eyes = -16.0, 2.0, "shut"
        near_foot, far_foot = (6.0, 0.0), (-10.0, 0.0)
        hand = (hip_x - 10.0, 84.0)
        sword = -120.0
        wind = 1.0
    elif anim == "death":
        fall = min(1.0, t / 0.7)
        crouch = 8.0 * min(1.0, fall * 2.0)
        hip_x -= 8.0 * fall
        rot = 78.0 * min(1.0, max(0.0, (fall - 0.2) / 0.8)) ** 1.2
        eyes = "shut"
        hand = (hip_x + 10.0, 100.0)
        sword = 60.0
        stuck = min(1.0, t * 1.6)
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    pen = S.Pen(f, (hip_x + 6.0, GROUND - 3.0), rot, (0.0, -4.0 * rot / 78.0))
    hip_y = GROUND - (THIGH + SHIN - 1.0) + crouch + bob
    lr = math.radians(lean)

    def up(p, length):
        return (p[0] + math.sin(lr) * length, p[1] - math.cos(lr) * length)

    def across(p, w):
        return (p[0] + math.cos(lr) * w, p[1] + math.sin(lr) * w)

    hip = (hip_x, hip_y)
    shoulder = up(hip, TORSO - 3.0)
    neck = up(hip, TORSO)
    hx, hy = up(neck, 7.0)

    # The tails of the wrap and the sash, out behind him in the wind.
    flap = math.sin(cyc * 2.0)
    for root, length, width, colour, phase0 in ((up(neck, 3.0), 14.0, 2.6, WRAP, 0.0), (across(up(hip, 1.0), -6.0), 12.0, 2.2, SASH, 1.3)):
        pts = []
        for k in range(6):
            u = k / 5.0
            pts.append((root[0] - length * u * (0.5 + 0.7 * wind), root[1] + length * u * (0.9 - 0.8 * wind) + 2.0 * math.sin(cyc * 2.0 + phase0 + u * 3.0) * u))
        pen.limb(pts, width, colour)
    del flap

    def a_leg(spec, trouser, boot):
        dx, lift = spec
        foot = (hip_x + dx, GROUND - 2.0 - lift)
        knee, ankle = H.leg(pen, hip, foot, THIGH, SHIN, 5.4, trouser)
        # Baggy above the boot; a soft boot with a turned-up toe.
        mid = H.lerp(knee, ankle, 0.55)
        pen.ellipse(mid[0], mid[1], 3.6, 3.2, trouser)
        pen.limb([H.lerp(knee, ankle, 0.7), ankle], 4.2, boot)
        pen.poly([(ankle[0] - 2.5, ankle[1] - 1.5), (ankle[0] + 5.0, ankle[1] - 0.5), (ankle[0] + 7.0, ankle[1] - 2.6), (ankle[0] + 6.6, ankle[1] + 2.0),
                  (ankle[0] - 2.5, ankle[1] + 2.0)], boot)

    a_leg(far_foot, TROUSER_SHADE, K.shade(BOOT, 0.8))
    # The far arm, empty, behind.
    far_hand = (hip_x - 8.0 + (6.0 if anim == "walk" and math.sin(cyc) > 0 else 0.0), hip_y - 2.0) if anim != "windup" else (hip_x + 10.0, hip_y - 8.0)
    H.arm(pen, across(shoulder, -2.0), far_hand, UPPER_ARM, FOREARM, 3.6, K.shade(COAT, 0.8), elbow_out=1.0)
    # The coat: to the knee, open at the front over the trousers.
    sb, sf = across(shoulder, -6.0), across(shoulder, 5.5)
    hem = 13.0
    coat = [across(up(hip, -hem), -8.5), across(up(hip, -hem + 2.0), 3.0), across(hip, 6.0), sf, across(neck, 2.6), across(neck, -2.6), sb]
    pen.poly(coat, COAT)
    pen.poly([across(up(hip, -hem), -8.5), across(up(hip, -hem + 1.0), -3.0), across(shoulder, -2.5), sb], COAT_SHADE, body=False)
    pen.ink([across(up(hip, -hem + 2.0), 1.0), across(up(hip, -4.0), 3.0)], 0.7, COAT_SHADE)
    pen.limb([across(up(hip, 1.0), -6.0), across(up(hip, 1.0), 6.2)], 2.6, SASH, body=False)
    pen.ink([across(neck, 2.0), across(up(hip, 4.0), 4.6)], 0.8, K.shade(COAT, 1.2))

    a_leg(near_foot, TROUSER, BOOT)

    # The head: a wrap of indigo over all but the eyes.
    tilt = lean * 0.4

    def Hd(x, y):
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    pen.ellipse(hx, hy, 6.4, 6.8, WRAP)
    pen.poly([Hd(-6.6, 2.0), Hd(-7.4, -3.0), Hd(-4.0, -8.4), Hd(3.0, -8.6), Hd(7.0, -5.0), Hd(2.0, -5.6)], WRAP_DARK, body=False)
    pen.poly([Hd(1.0, 1.0), Hd(7.6, 0.8), Hd(7.2, 6.4), Hd(2.0, 7.0)], WRAP)
    pen.ink([Hd(2.0, 3.4), Hd(7.0, 3.0)], 0.6, WRAP_DARK)
    pen.ink([Hd(1.5, 5.4), Hd(6.4, 5.4)], 0.6, WRAP_DARK)
    # The slit for the eyes: skin, and a hard white glint.
    pen.poly([Hd(1.0, -3.6), Hd(7.6, -3.4), Hd(7.8, -0.4), Hd(1.0, -0.2)], SKIN, body=False)
    ex, ey = Hd(4.8, -1.8)
    if eyes == "shut":
        pen.ink([(ex - 1.4, ey), (ex + 1.4, ey + 0.4)], 0.8)
    elif eyes == "narrow":
        pen.ink([(ex - 1.6, ey - 0.4), (ex + 1.6, ey + 0.4)], 1.1)
        pen.ink([(ex - 1.4, ey - 1.6), (ex + 1.6, ey - 0.6)], 0.8)
    else:
        pen.dot(ex, ey, 1.0)
        pen.dot(ex - 0.3, ey - 0.3, 0.35, K.WHITE)

    # The near arm and the sword.
    if hand is None:
        hand = (hip_x + 10.0, 96.0)
    if slash > 0.05:
        arc = []
        for k in range(10):
            a = math.radians(170.0 - 210.0 * slash * k / 9.0)
            arc.append((hip_x + 4.0 + math.cos(a) * 34.0, 86.0 + math.sin(a) * 22.0))
        f.glow_line(arc, 3.0, K.alpha(K.WHITE, 0.7 * (1.0 - max(0.0, slash - 0.7) / 0.3)))
    if stuck > 0.0:
        # The sword falls point first and stands in the sand.
        sx = hip_x - 16.0 + 6.0 * (1.0 - stuck)
        sy = GROUND - 50.0 + 22.0 * stuck * stuck
        _sword(S.Pen(f), (sx, sy), 96.0 - 140.0 * (1.0 - stuck))
        H.arm(pen, across(shoulder, 2.0), hand, UPPER_ARM, FOREARM, 3.8, COAT, elbow_out=1.0)
        pen.ellipse(hand[0], hand[1], 2.0, 2.0, SKIN)
    else:
        H.arm(pen, across(shoulder, 2.0), hand, UPPER_ARM, FOREARM, 3.8, COAT, elbow_out=1.0)
        _sword(pen, hand, sword)
        pen.ellipse(hand[0], hand[1], 2.0, 2.0, SKIN)
    if alarm:
        H.alarm_mark(f, hx + 13.0, hy - 18.0)
    return f.finish(outline=H.SEPIA_INK, width=1.4, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
