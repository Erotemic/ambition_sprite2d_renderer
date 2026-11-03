"""The Sea Raider: one of the Sea Peoples of the Bronze Age collapse.

Around 1177 BCE raiders came by sea to the coasts of the eastern
Mediterranean, and the old kingdoms fell one after another. The reliefs of
Medinet Habu in Egypt show some of them: a headdress of upright feathers on
a band, a corselet of bands, a kilt with tassels, a round shield with
bosses, and a long bronze sword.

This raider is fast. His walk is a jog with the shield up. When he sees you
he lifts the shield and points the sword. His windup draws the sword back
over his head; his strike is a running lunge and a downward cut. A hit
knocks his feathers askew; at his death he falls on his back and drops his
shield.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_africa_kit as H
from . import _history_cast_kit as C
from . import _stage_kit as S

TARGET_NAME = "sea_raider"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 122.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Sea Raider", "bronze_age", "Biped", "Standard", "Medium", "Walk", ["raider", "sword", "shield", "bronze"],
    "One of the Sea Peoples of the Bronze Age collapse in the History dimension, as the reliefs of Medinet Habu show them: "
    "a headdress of upright feathers, a round shield with bosses and a long bronze sword. He runs in fast and cuts.",
)

THIGH, SHIN = 13.0, 13.0
UPPER_ARM, FOREARM = 10.0, 10.0
TORSO = 19.0
SWORD = 24.0
SHIELD_R = 10.5
KILT = (226, 214, 184, 255)
KILT_SHADE = (180, 164, 128, 255)
TASSEL = (186, 58, 40, 255)
HAIR = (44, 32, 26, 255)


def _sword(pen: S.Pen, grip, angle: float) -> None:
    """The long bronze sword (a Naue II), held at `grip`, pointed at `angle` degrees."""
    a = math.radians(angle)
    d = (math.cos(a), math.sin(a))
    nrm = (-d[1], d[0])

    def at(s: float, w: float = 0.0):
        return (grip[0] + d[0] * s + nrm[0] * w, grip[1] + d[1] * s + nrm[1] * w)

    pen.poly([at(2.0, -1.8), at(SWORD * 0.7, -2.2), at(SWORD, 0.0), at(SWORD * 0.7, 2.2), at(2.0, 1.8)], H.BRONZE)
    pen.ink([at(3.0), at(SWORD - 2.0)], 0.6, H.BRONZE_LIGHT)
    pen.limb([at(1.0, -3.6), at(1.0, 3.6)], 2.2, H.BRONZE_DARK)
    pen.limb([at(-4.0), at(0.0)], 2.6, K.WOOD_DARK)
    pen.ellipse(*at(-5.0), 1.8, 1.8, H.BRONZE_DARK)


def _shield(pen: S.Pen, cx: float, cy: float, ring: float = 0.0) -> None:
    """The round shield, face on: hide on a frame, a ring of bronze bosses."""
    pen.ellipse(cx, cy, SHIELD_R, SHIELD_R, K.WOOD_DARK)
    pen.ellipse(cx + 0.6, cy + 0.6, SHIELD_R - 2.2, SHIELD_R - 2.2, (196, 160, 112, 255), body=False)
    pen.poly([(cx + 2.0, cy - 8.0), (cx + 9.0, cy - 2.0), (cx + 7.0, cy + 7.0), (cx + 2.0, cy + 9.0)], K.alpha((150, 118, 80, 255), 0.7), body=False)
    for k in range(8):
        a = math.tau * k / 8.0
        pen.dot(cx + math.cos(a) * (SHIELD_R - 4.6), cy + math.sin(a) * (SHIELD_R - 4.6), 1.3, H.BRONZE)
    pen.ellipse(cx, cy, 2.6, 2.6, H.BRONZE)
    pen.dot(cx - 0.6, cy - 0.8, 0.9, H.BRONZE_LIGHT)
    if ring > 0.0:
        for k in range(5):
            a = math.radians(-70.0 + k * 35.0)
            r0 = SHIELD_R + 2.0
            pen.ink([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * (r0 + 5.0 * ring), cy + math.sin(a) * (r0 + 5.0 * ring))],
                    1.2, K.alpha(K.WHITE, ring))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    hip_x, crouch, lean, bob = 52.0, 0.0, 0.0, 0.0
    near_foot, far_foot = (4.0, 0.0), (-4.0, 0.0)
    sword_hand, sword_angle = (10.0, 6.0), 60.0
    shield_up, shield_fwd, ring = 0.0, 0.0, 0.0
    alarm, fade, rot, askew = False, 1.0, 0.0, 0.0
    if anim == "idle":
        bob = 0.6 * math.sin(cyc)
        sword_hand, sword_angle = (9.0, 8.0 + 0.6 * math.sin(cyc)), 70.0 + 3.0 * math.sin(cyc)
    elif anim == "walk":
        # A fast jog: knees up, shield forward, the sword low.
        near_foot = (9.0 * math.sin(cyc), 6.0 * max(0.0, math.cos(cyc)))
        far_foot = (-9.0 * math.sin(cyc), 6.0 * max(0.0, -math.cos(cyc)))
        bob = -2.0 * abs(math.cos(cyc))
        lean = 8.0
        sword_hand, sword_angle = (8.0 - 3.0 * math.sin(cyc), 4.0), 40.0
        shield_fwd = 2.0 + 1.0 * math.sin(cyc)
    elif anim == "notice":
        u = min(1.0, t * 1.6)
        shield_up, crouch = 6.0 * u, 2.0 * u
        near_foot, far_foot = (8.0 * u, 0.0), (-7.0 * u, 0.0)
        sword_hand, sword_angle = (12.0 + 4.0 * u, -6.0 * u), 70.0 - 75.0 * u
        alarm = True
    elif anim == "windup":
        # The sword back over his head, the shield up, the weight back.
        shield_up, crouch, lean = 6.0, 4.0 + 0.6 * math.sin(cyc * 2.0), -6.0
        near_foot, far_foot = (10.0, 0.0), (-10.0, 0.0)
        sword_hand, sword_angle = (-4.0, -22.0 + 0.6 * math.sin(cyc * 2.0)), -150.0 + 3.0 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # A running lunge, and the cut comes down in front.
        u = min(1.0, t * 1.4)
        cut = min(1.0, max(0.0, (t - 0.1) / 0.4))
        hip_x += 14.0 * math.sin(math.pi * 0.5 * u) - 6.0 * max(0.0, t - 0.7) / 0.3
        crouch, lean = 5.0, 12.0 * math.sin(math.pi * min(1.0, t * 1.4))
        near_foot, far_foot = (14.0, 0.0), (-12.0, 0.0)
        sword_hand = (-4.0 + 22.0 * cut, -22.0 + 26.0 * cut)
        sword_angle = -150.0 + 180.0 * cut
        shield_up = 3.0
    elif anim == "hit":
        hip_x -= 4.0 * math.sin(math.pi * t)
        lean, shield_up, crouch, askew = -10.0, 5.0, 3.0, math.sin(math.pi * t)
        near_foot, far_foot = (8.0, 0.0), (-10.0, 0.0)
        sword_hand, sword_angle = (6.0, 4.0), 30.0
        ring = 1.0 - t * 0.6
    elif anim == "death":
        fall = min(1.0, t / 0.8)
        crouch = 8.0 * min(1.0, fall * 2.0)
        hip_x += 30.0 * fall
        rot = -80.0 * min(1.0, max(0.0, (fall - 0.15) / 0.7)) ** 1.2
        lean, askew = -8.0 * min(1.0, fall * 3.0), fall
        near_foot, far_foot = (6.0, 0.0), (-4.0, 0.0)
        sword_hand, sword_angle = (12.0, 6.0), 40.0 + 60.0 * fall
        shield_up = -8.0 * fall
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    pen = S.Pen(f, (hip_x - 6.0, GROUND - 3.0), rot, (0.0, 10.0 * rot / 80.0))
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

    # The shield arm (the far arm), with the shield on it, behind the body.
    sx = hip_x + 15.0 + shield_fwd
    sy = hip_y - 7.0 - shield_up
    C.arm(pen, across(shoulder, 2.0), (sx - 2.0, sy + 2.0), UPPER_ARM, FOREARM, 3.8, H.SKIN_SHADE, elbow_out=-1.0)

    def a_leg(spec, colour):
        dx, lift = spec
        foot = (hip_x + dx, GROUND - 2.0 - lift)
        knee, ankle = C.leg(pen, hip, foot, THIGH, SHIN, 4.6, colour)
        pen.poly([(ankle[0] - 2.5, ankle[1] - 1.0), (ankle[0] + 5.5, ankle[1] + 0.4), (ankle[0] + 5.5, ankle[1] + 2.2), (ankle[0] - 2.5, ankle[1] + 2.2)],
                 K.WOOD_DARK)
        # Sandal straps.
        pen.ink([(ankle[0] - 1.0, ankle[1] - 3.0), (ankle[0] + 2.0, ankle[1] - 1.0)], 0.7, K.WOOD_DARK)

    a_leg(far_foot, H.SKIN_SHADE)
    # The kilt: short, with a point in front and tassels at the hem.
    k0, k1 = across(up(hip, 2.0), -6.5), across(up(hip, 2.0), 6.5)
    hem_b, hem_f = across(up(hip, -9.0), -7.0), across(up(hip, -12.0), 8.0)
    pen.poly([k0, k1, hem_f, across(up(hip, -8.0), 1.0), hem_b], KILT)
    pen.poly([k0, across(up(hip, 2.0), -1.0), across(up(hip, -8.5), -1.0), hem_b], KILT_SHADE, body=False)
    pen.limb([across(up(hip, 1.0), -6.0), across(up(hip, 1.0), 6.6)], 2.0, TASSEL, body=False)
    for k in range(3):
        a = across(up(hip, -1.0), 2.0 + k * 1.8)
        pen.limb([a, (a[0] + 0.4, a[1] + 8.0 + k * 1.4)], 1.2, TASSEL, body=False)
    # The body: bare arms, and a corselet of horizontal bands.
    sb, sf = across(shoulder, -6.0), across(shoulder, 6.0)
    nb, nf = across(neck, -3.0), across(neck, 3.0)
    hb, hf = across(up(hip, 2.0), -5.5), across(up(hip, 2.0), 5.5)
    pen.poly([hb, hf, across(up(hip, 9.0), 7.0), sf, nf, nb, sb], H.SKIN)
    pen.poly([across(up(hip, 2.0), -6.0), across(up(hip, 2.0), 6.0), across(up(hip, 14.0), 7.0), across(up(hip, 14.0), -6.5)], H.LINEN)
    for k in range(4):
        y = 3.6 + k * 3.0
        pen.ink([across(up(hip, y), -6.0), across(up(hip, y), 6.6)], 1.0, H.SEA_DARK)
    pen.poly([across(up(hip, 2.0), -6.0), across(up(hip, 2.0), -2.0), across(up(hip, 14.0), -2.0), across(up(hip, 14.0), -6.5)],
             K.alpha(H.LINEN_SHADE, 0.8), body=False)

    a_leg(near_foot, H.SKIN)

    # The head: a short beardless face and a band of upright feathers.
    tilt = lean * 0.4 + (10.0 if anim == "death" else 0.0)

    def Hd(x, y):
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    pen.poly([Hd(-6.0, 2.0), Hd(-6.0, -4.0), Hd(-2.0, -7.0), Hd(4.0, -6.0), Hd(6.5, -2.0), Hd(7.6, 1.0), Hd(6.0, 3.0), Hd(6.0, 6.0), Hd(2.0, 7.6),
              Hd(-3.0, 6.6)], H.SKIN)
    pen.poly([Hd(-6.0, 2.0), Hd(-6.0, -4.0), Hd(-2.0, -5.0), Hd(-2.0, 4.0), Hd(-3.0, 6.6)], HAIR, body=False)
    pen.ink([Hd(2.6, -1.2), Hd(5.0, -1.4)], 0.9, H.SEPIA_INK)
    pen.dot(*Hd(4.2, -0.4), 0.9, H.SEPIA_INK)
    pen.ink([Hd(3.0, 4.6), Hd(5.6, 4.2)], 0.8, H.SEPIA_INK)
    # The feathers: upright, in a fan, on a band with a row of discs.
    for k in range(9):
        u = (k - 4) / 4.0
        lean_f = u * 14.0 + 10.0 * askew * (1.0 if k % 2 else 0.6)
        base = Hd(-5.0 + k * 1.3, -5.6)
        a = math.radians(-90.0 + lean_f)
        tip = (base[0] + math.cos(a) * 12.0, base[1] + math.sin(a) * 12.0)
        pen.limb([base, tip], 2.6, H.FEATHER if k % 2 else H.FEATHER_SHADE)
    pen.poly([Hd(-6.6, -3.0), Hd(6.6, -3.6), Hd(6.6, -6.6), Hd(-6.6, -6.4)], H.SEA)
    for k in range(4):
        pen.dot(*Hd(-4.4 + k * 3.0, -4.8), 0.8, H.BRONZE_LIGHT)
    pen.limb([Hd(-5.0, -3.0), Hd(-4.0, 6.0)], 1.4, H.SEA_DARK, body=False)

    # The shield over the far arm, then the sword arm in front.
    _shield(pen, sx, sy, ring)
    grip = (shoulder[0] + sword_hand[0], shoulder[1] + 6.0 + sword_hand[1])
    _sword(pen, grip, sword_angle)
    C.arm(pen, across(shoulder, -2.0), grip, UPPER_ARM, FOREARM, 3.8, H.SKIN, elbow_out=1.0)
    pen.ellipse(grip[0], grip[1], 2.4, 2.2, H.SKIN)
    pen.limb([(grip[0] - 2.0, grip[1] - 3.6), (grip[0] - 3.0, grip[1] - 1.0)], 1.6, H.BRONZE)
    if anim == "attack_side" and 1 <= i <= 3:
        # The arc of the cut.
        r = SWORD + 4.0
        pts = []
        for k in range(7):
            a = math.radians(-120.0 + 25.0 * k)
            pts.append((shoulder[0] + math.cos(a) * r * 0.9, shoulder[1] + 6.0 + math.sin(a) * r * 0.9))
        f.ink(pen.p(pts), 1.4, K.alpha(K.WHITE, 0.8))
    if alarm:
        H.alarm_mark(f, hx + 14.0, max(14.0, hy - 26.0))
    return f.finish(outline=H.SEPIA_INK, width=1.4, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
