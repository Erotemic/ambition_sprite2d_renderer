"""The Viking Raider: a raider of the Viking north.

A raider with a big ginger beard in two braids, a conical iron helmet with
a nose guard and NO horns (no Viking wore horns in battle: the horns are
from an opera costume of 1876). He wears a blue wool tunic with a belt,
brown trousers with wraps round the shins, and a short red cloak. He holds
a round wooden shield painted red and white with an iron boss, and a
bearded axe.

At rest the axe is on his shoulder. When he sees you he bangs the axe on
the rim of his shield. His windup lifts the axe high behind his head, with
the shield in front; his strike is a step and a chop down in front of him.
A hit thuds on the shield and pushes him back; at his death he falls on
his back.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_cast_kit as H
from . import _history_europe_kit as E
from . import _stage_kit as S

TARGET_NAME = "viking_raider"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 124.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Viking Raider", "Biped", "Standard", "Medium", "Walk", ["soldier", "shield", "axe", "viking"],
    "A raider of the Viking north in the History dimension: a ginger beard in braids, a conical iron helmet with a nose "
    "guard and no horns, a round red and white shield and a bearded axe. He bangs the axe on his shield, lifts it high "
    "and chops down with a step.",
    "viking",
)

THIGH, SHIN = 13.0, 13.0
UPPER_ARM, FOREARM = 10.0, 10.0
TORSO = 19.0
HAFT = 28.0
SHIELD_R = 13.0


def _axe(pen: S.Pen, grip, angle: float) -> None:
    """The axe, held at `grip`, its haft pointed at `angle` degrees (0 is
    forward, -90 is up). The blade is on the clockwise side of the haft."""
    a = math.radians(angle)
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])

    def at(s: float, w: float = 0.0):
        return (grip[0] + d[0] * s + n[0] * w, grip[1] + d[1] * s + n[1] * w)

    pen.limb([at(-5.0), at(HAFT)], 2.4, E.OAK)
    pen.ink([at(-4.0, -0.4), at(HAFT - 2.0, -0.4)], 0.5, E.OAK_LIGHT)
    # The bearded head: a narrow neck, then a blade that hangs down the haft.
    head = [at(HAFT - 4.0, -1.6), at(HAFT + 2.0, -1.6), at(HAFT + 3.0, 1.4), at(HAFT + 6.0, 9.0), at(HAFT - 1.0, 10.0),
            at(HAFT - 9.0, 9.0), at(HAFT - 4.0, 6.0), at(HAFT - 3.0, 1.4)]
    pen.poly(head, E.IRON)
    pen.poly([at(HAFT + 5.0, 8.0), at(HAFT + 6.0, 9.0), at(HAFT - 1.0, 10.0), at(HAFT - 9.0, 9.0), at(HAFT - 7.0, 8.0)], E.IRON_LIGHT, body=False)


def _shield(pen: S.Pen, cx: float, cy: float, spin: float, thud: float = 0.0) -> None:
    """The round shield, face on: four boards painted red and white, a
    leather rim, and an iron boss in the middle."""
    r = SHIELD_R
    pen.ellipse(cx, cy, r, r, E.LEATHER_DARK)
    for q in range(4):
        a0 = math.radians(spin + q * 90.0)
        pts = [(cx, cy)] + [(cx + (r - 1.6) * math.cos(a0 + math.radians(90.0) * k / 8.0), cy + (r - 1.6) * math.sin(a0 + math.radians(90.0) * k / 8.0))
                            for k in range(9)]
        pen.poly(pts, E.WOOL_RED if q % 2 == 0 else E.WOOL, body=False)
    for q in range(4):
        a0 = math.radians(spin + q * 90.0)
        pen.ink([(cx, cy), (cx + (r - 1.6) * math.cos(a0), cy + (r - 1.6) * math.sin(a0))], 0.6, E.OAK_DARK)
    pen.ellipse(cx, cy, 4.0, 4.0, E.IRON, body=False)
    pen.ellipse(cx - 0.8, cy - 0.8, 1.6, 1.6, E.IRON_LIGHT, body=False)
    if thud > 0.0:
        for k in range(5):
            a = math.radians(-80.0 + k * 35.0)
            r0 = r + 2.0
            pen.ink([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * (r0 + 6.0 * thud), cy + math.sin(a) * (r0 + 6.0 * thud))],
                    1.2, K.alpha(K.WHITE, thud))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    hip_x, crouch, lean, bob = 52.0, 0.0, 0.0, 0.0
    near_foot, far_foot = (4.0, 0.0), (-4.0, 0.0)
    axe_hand, axe_angle = (10.0, -18.0), -150.0
    shield_up, shield_fwd, thud, bang = 0.0, 0.0, 0.0, 0.0
    cape, alarm, fade, rot, shout = 0.0, False, 1.0, 0.0, 0.0
    if anim == "idle":
        # The axe on his shoulder, the shield at his side.
        bob = 0.6 * math.sin(cyc)
        cape = 0.3 * math.sin(cyc + 1.0)
        axe_hand, axe_angle = (2.0, 2.0 + 0.6 * math.sin(cyc)), -142.0 + 2.0 * math.sin(cyc)
    elif anim == "walk":
        near_foot = (8.0 * math.sin(cyc), 5.0 * max(0.0, math.cos(cyc)))
        far_foot = (-8.0 * math.sin(cyc), 5.0 * max(0.0, -math.cos(cyc)))
        bob = -1.5 * abs(math.cos(cyc))
        lean, cape = 4.0, 0.6 + 0.3 * math.sin(cyc * 2.0)
        axe_hand, axe_angle = (2.0, 2.0), -142.0 + 3.0 * math.sin(cyc)
        shield_fwd = 1.0 * math.sin(cyc)
    elif anim == "notice":
        # He bangs the axe on the rim of his shield and shouts.
        k = math.sin(math.tau * t * 2.0)
        shield_up, shield_fwd, crouch = 4.0, 3.0, 2.0
        near_foot, far_foot = (8.0, 0.0), (-8.0, 0.0)
        axe_hand, axe_angle = (14.0, -14.0 - 4.0 * max(0.0, -k)), -60.0 + 40.0 * max(0.0, k)
        bang, shout, alarm = max(0.0, k), 1.0, True
    elif anim == "windup":
        # The axe high behind his head, the shield in front.
        shield_up, shield_fwd, crouch, lean = 6.0, 4.0, 3.0 + 0.6 * math.sin(cyc * 2.0), -6.0
        near_foot, far_foot = (10.0, 0.0), (-10.0, 0.0)
        axe_hand, axe_angle = (-4.0, -26.0), -160.0 + 4.0 * math.sin(cyc * 2.0)
        cape, shout = -0.3, 0.5
    elif anim == "attack_side":
        # A step and a chop down in front.
        u = min(1.0, t * 1.5)
        chop = min(1.0, u / 0.5)
        hip_x += 7.0 * u
        shield_up, shield_fwd, crouch, lean = 2.0, -2.0, 3.0 + 2.0 * chop, -6.0 + 16.0 * chop
        near_foot, far_foot = (12.0 + 2.0 * u, 0.0), (-10.0, 0.0)
        axe_hand = (-4.0 + 26.0 * chop, -26.0 + 16.0 * chop)
        axe_angle = -160.0 + 190.0 * chop * chop
        cape, shout = 0.8, 1.0 - u
    elif anim == "hit":
        hip_x -= 4.0 * math.sin(math.pi * t)
        lean, shield_up, shield_fwd, crouch = -10.0, 5.0, 3.0, 3.0
        near_foot, far_foot = (8.0, 0.0), (-10.0, 0.0)
        axe_hand, axe_angle = (2.0, 0.0), -136.0
        thud = 1.0 - t * 0.6
    elif anim == "death":
        fall = min(1.0, t / 0.8)
        crouch = 8.0 * min(1.0, fall * 2.0)
        hip_x += 30.0 * fall
        rot = -80.0 * min(1.0, max(0.0, (fall - 0.15) / 0.7)) ** 1.2
        lean = -8.0 * min(1.0, fall * 3.0)
        near_foot, far_foot = (6.0, 0.0), (-4.0, 0.0)
        axe_hand, axe_angle = (12.0, -6.0), -60.0 + 80.0 * fall
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
    head = up(neck, 8.0)
    hx, hy = head

    # The short red cloak, behind.
    flow = 6.0 + 5.0 * cape
    pen.poly([across(shoulder, -4.0), across(neck, 1.0), (hip_x - 5.0, hip_y + 4.0), (hip_x - 9.0 - flow, hip_y + 6.0), (hip_x - 9.0 - flow * 0.6, hip_y - 8.0)],
             E.WOOL_RED)
    pen.poly([across(shoulder, -4.0), (hip_x - 9.0 - flow, hip_y + 6.0), (hip_x - 9.0 - flow * 0.6, hip_y - 8.0)], E.WOOL_RED_DARK, body=False)

    def a_leg(spec, colour, wrap):
        dx, lift = spec
        foot = (hip_x + dx, GROUND - 2.0 - lift)
        knee, ankle = H.leg(pen, hip, foot, THIGH, SHIN, 5.0, colour)
        # The wraps round the shin, and a leather shoe.
        pen.limb([H.lerp(knee, ankle, 0.15), H.lerp(knee, ankle, 0.9)], 5.2, wrap)
        for u in (0.3, 0.5, 0.7):
            p = H.lerp(knee, ankle, u)
            pen.ink([(p[0] - 2.4, p[1] - 1.0), (p[0] + 2.4, p[1] + 1.0)], 0.6, E.WOOL_SHADE)
        pen.poly([(ankle[0] - 3.0, ankle[1] - 1.5), (ankle[0] + 5.5, ankle[1] + 0.4), (ankle[0] + 5.5, ankle[1] + 2.2), (ankle[0] - 3.0, ankle[1] + 2.2)],
                 E.LEATHER_DARK)

    a_leg(far_foot, E.LEATHER_DARK, K.shade(E.WOOL, 0.8))

    # The tunic: blue wool to mid thigh, with a belt.
    hb, hf = across(hip, -6.0), across(hip, 6.0)
    pen.poly([across(hip, -7.0), across(hip, 7.5), across(up(hip, -8.0), 8.5), across(up(hip, -8.0), -8.0)], E.WOOL_BLUE)
    sb, sf = across(shoulder, -6.5), across(shoulder, 6.5)
    nb, nf = across(neck, -3.0), across(neck, 3.0)
    pen.poly([hb, hf, across(up(hip, 8.0), 7.5), sf, nf, nb, sb], E.WOOL_BLUE)
    pen.poly([hb, across(hip, -2.0), across(shoulder, -3.0), sb], E.WOOL_BLUE_DARK, body=False)
    pen.limb([across(hip, -6.5), across(hip, 6.5)], 2.6, E.LEATHER_DARK)
    pen.poly([across(hip, 1.0), across(hip, 3.6), across(up(hip, -1.6), 3.6), across(up(hip, -1.6), 1.0)], E.GOLD)
    pen.ink([across(up(hip, -8.0), -8.0), across(up(hip, -8.0), 8.5)], 1.2, E.GOLD)

    a_leg(near_foot, E.LEATHER, E.WOOL)

    # The head: a face, a big ginger beard in two braids, and the helmet.
    tilt = lean * 0.4 + (10.0 if anim == "death" else 0.0)

    def Hd(x, y):
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    pen.poly([Hd(-6.0, 6.0), Hd(-7.0, -2.0), Hd(-3.0, -6.0), Hd(5.0, -6.0), Hd(8.0, -1.0), Hd(8.0, 4.0), Hd(4.0, 7.0)], E.SKIN)
    pen.ellipse(*Hd(-4.5, 0.5), 1.8, 2.2, E.SKIN_SHADE, body=False)
    # The beard, over the chin and the throat, and its braids.
    beard = [Hd(-4.0, 2.0), Hd(0.0, 4.0), Hd(4.0, 3.0), Hd(8.6, 2.6), Hd(9.0, 7.0), Hd(6.0, 13.0), Hd(0.0, 14.0), Hd(-4.0, 9.0)]
    pen.poly(beard, E.BEARD)
    pen.poly([Hd(6.0, 13.0), Hd(0.0, 14.0), Hd(-4.0, 9.0), Hd(2.0, 10.0)], E.BEARD_DARK, body=False)
    for bx in (1.0, 5.0):
        sway = 0.8 * math.sin(cyc + bx) if anim in ("idle", "walk") else 0.0
        pen.limb([Hd(bx, 12.0), Hd(bx + sway, 17.0), Hd(bx + sway * 1.5, 20.0)], 2.2, E.BEARD)
        pen.dot(*Hd(bx + sway, 16.0), 0.5, E.BEARD_DARK)
        pen.ellipse(*Hd(bx + sway * 1.5, 20.6), 1.1, 0.9, E.GOLD)
    # The moustache, and the mouth when he shouts.
    if shout > 0.2:
        pen.ellipse(*Hd(6.0, 5.6), 1.8, 1.4 * shout + 0.4, (110, 40, 40, 255), body=False)
    pen.poly([Hd(3.0, 2.6), Hd(9.0, 2.0), Hd(9.6, 3.6), Hd(6.0, 4.2), Hd(3.0, 4.6)], E.BEARD_DARK, body=False)
    # The helmet: a cone of iron with a band round it and a nose guard.
    helm = [Hd(-7.6, 0.0), Hd(-7.0, -5.0), Hd(-3.0, -10.0), Hd(1.6, -13.0), Hd(5.0, -9.6), Hd(8.6, -4.0), Hd(8.8, -1.0)]
    pen.poly(helm, E.IRON)
    pen.poly([Hd(-7.6, 0.0), Hd(-7.0, -5.0), Hd(-3.0, -10.0), Hd(1.6, -13.0), Hd(-1.0, -6.0), Hd(-3.0, 0.0)], E.IRON_DARK, body=False)
    pen.limb([Hd(-7.4, -1.2), Hd(8.6, -2.0)], 2.2, E.IRON_LIGHT)
    pen.limb([Hd(7.4, -2.0), Hd(8.2, 3.2)], 1.8, E.IRON_LIGHT)
    ex, ey = Hd(5.2, 0.2)
    if anim == "death" and t > 0.4:
        pen.ink([(ex - 1.2, ey), (ex + 1.2, ey)], 0.8, K.INK)
    else:
        pen.dot(ex, ey, 0.9, K.INK)
        if anim in ("windup", "attack_side", "notice"):
            pen.ink([(ex - 1.8, ey - 2.2), (ex + 1.4, ey - 1.2)], 0.7, K.INK)

    # The axe arm (the far arm) and the axe, then the shield on the near arm.
    grip = (shoulder[0] + axe_hand[0], shoulder[1] + 9.0 + axe_hand[1])
    H.arm(pen, across(shoulder, -2.0), grip, UPPER_ARM, FOREARM, 4.0, E.WOOL_BLUE_DARK, elbow_out=-1.0)
    _axe(pen, grip, axe_angle)
    pen.ellipse(grip[0], grip[1], 2.4, 2.2, E.SKIN)
    sx = hip_x + 10.0 + shield_fwd
    sy = hip_y - 2.0 - 0.6 * shield_up
    H.arm(pen, across(shoulder, 2.0), (sx - 2.0, sy + 2.0), UPPER_ARM, FOREARM, 4.0, E.WOOL_BLUE, elbow_out=1.0)
    _shield(pen, sx, sy, 20.0 + (8.0 if anim == "hit" else 0.0), thud)
    if bang > 0.5:
        bx, by = sx + 6.0, sy - SHIELD_R
        for k in range(3):
            a = math.radians(-120.0 + k * 30.0)
            pen.ink([(bx + math.cos(a) * 3.0, by + math.sin(a) * 3.0), (bx + math.cos(a) * 8.0, by + math.sin(a) * 8.0)], 1.2, K.alpha(K.WHITE, bang))
    if alarm:
        H.alarm_mark(f, hx + 14.0, hy - 26.0)
    return f.finish(outline=E.OUTLINE, width=1.4, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
