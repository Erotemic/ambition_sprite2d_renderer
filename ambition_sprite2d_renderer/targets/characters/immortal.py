"""The Immortal: a Persian royal guard of the Classical Shore.

A guard of the Great King in a long robe of saffron with rosettes of lapis
blue, as the glazed bricks of Susa show them: wide sleeves, a sash, a
twisted band round black hair, and a square black beard in tight curls. He
holds a spear with a silver pomegranate at its butt and a tall shield of
woven wicker.

There were always ten thousand of them: when one fell, another stepped up.
At rest he stands to attention with the pomegranate on the ground. When he
sees you he lifts the shield and lowers the spear to his hip; his windup
draws it back, and his strike is a long thrust from the hip with a step.
A hit staggers him. At his death he falls on his face, and the shadow of
the next Immortal steps up behind him.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_cast_kit as H
from . import _stage_kit as S

TARGET_NAME = "immortal"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 124.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Immortal", "Biped", "Standard", "Medium", "Walk", ["soldier", "spear", "wicker_shield", "persian"],
    "A Persian royal guard of the Classical Shore in the History dimension: a saffron robe with lapis rosettes, a spear "
    "with a silver pomegranate and a wicker shield. He lowers the spear to his hip and thrusts; when one falls, another steps up.",
    "classical",
)

THIGH, SHIN = 13.0, 13.0
UPPER_ARM, FOREARM = 10.0, 10.0
TORSO = 19.0
SPEAR_FRONT, SPEAR_BACK = 42.0, 28.0
ROBE = (232, 176, 58, 255)
ROBE_SHADE = (184, 126, 36, 255)
LAPIS = (38, 70, 160, 255)
WICKER = (200, 160, 96, 255)
WICKER_DARK = (140, 100, 52, 255)
HAIR = (34, 26, 30, 255)
SILVER = (214, 218, 228, 255)


def _spear(pen: S.Pen, grip, angle: float) -> None:
    a = math.radians(angle)
    d = (math.cos(a), math.sin(a))
    nrm = (-d[1], d[0])

    def at(s: float, w: float = 0.0):
        return (grip[0] + d[0] * s + nrm[0] * w, grip[1] + d[1] * s + nrm[1] * w)

    pen.limb([at(-SPEAR_BACK), at(SPEAR_FRONT - 5.0)], 2.2, K.WOOD)
    pen.poly([at(SPEAR_FRONT - 6.0, -1.6), at(SPEAR_FRONT + 3.0, 0.0), at(SPEAR_FRONT - 6.0, 1.6)], K.STEEL)
    # The silver pomegranate at the butt, with its crown.
    px, py = at(-SPEAR_BACK - 2.0)
    pen.ellipse(px, py, 3.0, 3.0, SILVER)
    tip = at(-SPEAR_BACK - 5.4)
    pen.poly([(tip[0] - 1.4, tip[1] - 1.0), (tip[0] + 1.4, tip[1] - 1.0), (tip[0], tip[1] + 1.4)], SILVER)
    pen.dot(px + 0.8, py - 0.8, 0.8, K.WHITE)


def _shield(pen: S.Pen, cx: float, cy: float, tilt: float) -> None:
    """The wicker shield, face on: tall, with rounded ends and a weave."""
    w, h = 9.0, 16.0
    pts = []
    for k in range(24):
        a = math.tau * k / 24
        c, s = math.cos(a), math.sin(a)
        pts.append((cx + w * (abs(c) ** 0.5) * (1 if c >= 0 else -1), cy + h * (abs(s) ** 0.7) * (1 if s >= 0 else -1)))
    pts = K.turn(pts, cx, cy, tilt)
    pen.poly(pts, WICKER)
    for k in range(-3, 4):
        y = cy + k * 4.0
        pen.ink(K.turn([(cx - w + 1.5, y), (cx + w - 1.5, y)], cx, cy, tilt), 0.6, WICKER_DARK)
    for k in (-1, 0, 1):
        x = cx + k * 4.0
        pen.ink(K.turn([(x, cy - h + 2.0), (x, cy + h - 2.0)], cx, cy, tilt), 0.6, K.alpha(WICKER_DARK, 0.7))
    pen.poly(K.turn(K.ellipse_points(cx, cy, 3.0, 3.0, 12), cx, cy, tilt), LAPIS, body=False)


def _figure(f: K.Frame, pen: S.Pen, hip_x: float, crouch: float, lean: float, bob: float, near_foot, far_foot, spear_grip, spear_angle,
            shield_up: float, eyes: str, cyc: float, alarm: bool, t: float, anim: str) -> None:
    hip_y = GROUND - (THIGH + SHIN - 1.0) + crouch + bob
    lr = math.radians(lean)

    def up(p, length):
        return (p[0] + math.sin(lr) * length, p[1] - math.cos(lr) * length)

    def across(p, w):
        return (p[0] + math.cos(lr) * w, p[1] + math.sin(lr) * w)

    hip = (hip_x, hip_y)
    shoulder = up(hip, TORSO - 3.0)
    neck = up(hip, TORSO)
    hx, hy = up(neck, 8.0)

    feet = []
    for spec in (far_foot, near_foot):
        dx, lift = spec
        foot = (hip_x + dx, GROUND - 2.0 - lift)
        _knee, ankle = S.joint(hip, foot, THIGH, SHIN, -1.0)
        feet.append(ankle)
    # The feet, in soft shoes, under the hem.
    for (ax, ay), colour in zip(feet, (K.shade(H.OCHRE_DARK, 0.8), H.OCHRE_DARK)):
        pen.poly([(ax - 2.5, ay - 1.5), (ax + 6.0, ay), (ax + 6.0, ay + 2.2), (ax - 2.5, ay + 2.2)], colour)
    # The robe: to the ankles, its hem following the feet.
    far, near = feet
    hem_back = (min(far[0], near[0]) - 5.0, max(far[1], near[1]) - 2.5)
    hem_front = (max(far[0], near[0]) + 4.0, min(far[1], near[1]) - 3.0 + 1.0)
    robe = [across(up(hip, 2.0), -7.0), across(up(hip, 2.0), 7.0), (hem_front[0] + 2.0, hem_front[1]), (near[0] + 1.0, near[1] - 1.5),
            (far[0] - 1.0, far[1] - 1.5), hem_back]
    pen.poly(robe, ROBE)
    pen.poly([across(up(hip, 2.0), -7.0), across(up(hip, 2.0), -3.0), (far[0] - 1.0, far[1] - 1.5), hem_back], ROBE_SHADE, body=False)
    # The fold between the legs, and the rosettes.
    pen.ink([across(hip, 1.0), H.lerp(far, near, 0.5)], 0.7, ROBE_SHADE)
    for u, w in ((0.35, -2.0), (0.65, 3.0), (0.5, 7.5), (0.8, -4.5)):
        p = H.lerp(across(hip, w * 0.6), (H.lerp(far, near, 0.5)[0] + w, near[1] - 2.0), u)
        pen.ellipse(p[0], p[1], 1.4, 1.4, LAPIS, body=False)
        pen.dot(p[0], p[1], 0.5, K.WHITE)
    pen.ink([(hem_back[0] + 1.0, hem_back[1] - 1.5), (hem_front[0] + 1.0, hem_front[1] - 1.5)], 1.2, LAPIS)
    # The body of the robe, with its sash.
    sb, sf = across(shoulder, -6.5), across(shoulder, 6.5)
    pen.poly([across(hip, -6.5), across(hip, 6.5), sf, across(neck, 3.0), across(neck, -3.0), sb], ROBE)
    pen.poly([across(hip, -6.5), across(hip, -3.0), across(shoulder, -3.0), sb], ROBE_SHADE, body=False)
    pen.poly([across(hip, -6.8), across(hip, 6.8), across(up(hip, 3.0), 6.8), across(up(hip, 3.0), -6.8)], LAPIS, body=False)
    for h_, w in ((9.0, 1.5), (13.0, -2.5)):
        p = across(up(hip, h_), w)
        pen.ellipse(p[0], p[1], 1.4, 1.4, LAPIS, body=False)
        pen.dot(p[0], p[1], 0.5, K.WHITE)

    # The head: a square curled beard, black hair to the nape, a twisted band.
    tilt = lean * 0.3

    def Hd(x, y):
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    pen.poly([Hd(-7.5, -2.0), Hd(-4.0, -7.5), Hd(3.0, -7.8), Hd(-1.0, -1.0), Hd(-4.0, 7.0), Hd(-8.5, 6.0)], HAIR)
    pen.ellipse(hx, hy, 6.5, 7.0, H.SKIN_DARK)
    pen.poly([Hd(5.5, -1.0), Hd(8.2, 1.6), Hd(5.6, 2.6)], H.SKIN_DARK)
    pen.poly([Hd(-6.6, -1.5), Hd(-4.0, -7.6), Hd(3.0, -7.6), Hd(6.0, -4.5), Hd(1.0, -4.2), Hd(-3.0, -2.0)], HAIR)
    pen.poly([Hd(-1.0, 1.0), Hd(6.6, 3.8), Hd(7.0, 8.0), Hd(4.0, 11.0), Hd(-2.0, 10.0), Hd(-3.0, 4.0)], HAIR)
    for k in range(3):
        pen.ink([Hd(0.5 + k * 2.0, 6.0), Hd(0.5 + k * 2.0, 10.0)], 0.6, (80, 66, 72, 255))
    band = [Hd(-7.0, -2.8), Hd(-3.5, -6.0), Hd(3.0, -6.4), Hd(6.4, -3.8)]
    pen.limb(band, 2.0, K.WHITE)
    for k in range(3):
        a, b = H.lerp(band[k], band[k + 1], 0.3), H.lerp(band[k], band[k + 1], 0.7)
        pen.ink([a, b], 0.6, H.SAFFRON)
    ex, ey = Hd(3.4, -0.4)
    if eyes == "shut":
        pen.ink([(ex - 1.3, ey), (ex + 1.3, ey + 0.4)], 0.8)
    elif eyes == "wide":
        pen.dot(ex, ey, 1.3)
        pen.dot(ex - 0.3, ey - 0.4, 0.4, K.WHITE)
    else:
        pen.ink([(ex - 1.4, ey), (ex + 1.4, ey - 0.2)], 1.0)
    pen.ink([Hd(1.6, -2.4), Hd(5.0, -2.8)], 0.8)

    # The spear arm (far), the shield on the near arm, then the spear.
    if spear_grip == "rest":
        a = math.radians(spear_angle)
        grip = (hip_x + 12.0 + math.cos(a) * (SPEAR_BACK + 5.0), GROUND - 2.0 + math.sin(a) * (SPEAR_BACK + 5.0))
    else:
        grip = (hip_x + spear_grip, hip_y - 2.0)
    sleeve = K.shade(ROBE, 0.85)
    H.arm(pen, across(shoulder, -2.0), grip, UPPER_ARM, FOREARM, 4.4, sleeve, elbow_out=1.0)
    _spear(pen, grip, spear_angle)
    pen.ellipse(grip[0], grip[1], 2.3, 2.1, H.SKIN_DARK)
    sx, sy = hip_x + 9.0 + (3.0 if shield_up else 0.0), hip_y - 6.0 - shield_up
    H.arm(pen, across(shoulder, 2.0), (sx - 2.0, sy + 1.0), UPPER_ARM, FOREARM, 4.4, ROBE, elbow_out=1.0)
    _shield(pen, sx, sy, lean * 0.4)
    if alarm:
        H.alarm_mark(f, hx + 13.0, hy - 18.0)


def _shadow(f: K.Frame, x: float, a: float) -> None:
    """The next Immortal: a dark shape that steps up, a spear upright."""
    colour = K.alpha(H.INDIGO_DARK, a)
    g = GROUND - 2.0
    f.poly([(x - 7.0, g), (x + 8.0, g), (x + 6.0, g - 30.0), (x + 6.5, g - 44.0), (x - 6.0, g - 44.0), (x - 8.0, g - 30.0)], colour, body=False)
    f.ellipse(x, g - 51.0, 6.5, 7.0, colour, body=False)
    f.poly([(x - 1.0, g - 49.0), (x + 7.0, g - 47.0), (x + 6.0, g - 40.0), (x - 1.0, g - 41.0)], colour, body=False)
    f.limb([(x + 12.0, g - 1.0), (x + 12.0, g - 72.0)], 2.0, colour, body=False)
    f.poly([(x + 10.4, g - 72.0), (x + 12.0, g - 80.0), (x + 13.6, g - 72.0)], colour, body=False)
    f.poly([(x + 6.0, g - 46.0), (x + 18.0, g - 46.0), (x + 18.0, g - 18.0), (x + 6.0, g - 18.0)], colour, body=False)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    hip_x, crouch, lean, bob = 48.0, 0.0, 0.0, 0.0
    near_foot, far_foot = (4.0, 0.0), (-3.0, 0.0)
    spear_grip, spear_angle = "rest", -90.0
    shield_up, eyes, alarm, fade, rot = 0.0, "open", False, 1.0, 0.0
    shadow = 0.0
    if anim == "idle":
        # To attention: still, but for his breath.
        bob = 0.5 * math.sin(cyc)
        spear_angle = -90.0 + 1.0 * math.sin(cyc)
        eyes = "shut" if i == 3 else "open"
    elif anim == "walk":
        # In step, as ten thousand walk.
        near_foot = (7.0 * math.sin(cyc), 4.0 * max(0.0, math.cos(cyc)))
        far_foot = (-7.0 * math.sin(cyc), 4.0 * max(0.0, -math.cos(cyc)))
        bob = -1.2 * abs(math.cos(cyc))
        lean = 3.0
        spear_angle = -86.0 + 2.0 * math.sin(cyc)
    elif anim == "notice":
        u = min(1.0, t * 1.6)
        shield_up, crouch, eyes, alarm = 5.0 * u, 2.0 * u, "wide", True
        near_foot, far_foot = (9.0 * u, 0.0), (-8.0 * u, 0.0)
        if u > 0.4:
            spear_grip, spear_angle = 6.0, -90.0 + 92.0 * u
    elif anim == "windup":
        shield_up, crouch, lean = 5.0, 4.0 + 0.5 * math.sin(cyc * 2.0), -6.0
        near_foot, far_foot = (10.0, 0.0), (-10.0, 0.0)
        spear_grip, spear_angle = -6.0, 2.0
    elif anim == "attack_side":
        jab = math.sin(math.pi * min(1.0, t * 1.3))
        hip_x += 5.0 * min(1.0, t * 1.6)
        shield_up, crouch, lean = 4.0, 4.0, 8.0 * jab
        near_foot, far_foot = (14.0, 0.0), (-10.0, 0.0)
        spear_grip, spear_angle = -6.0 + 22.0 * jab, 2.0
    elif anim == "hit":
        hip_x -= 4.0 * math.sin(math.pi * t)
        lean, crouch, eyes = -12.0, 2.0, "shut"
        near_foot, far_foot = (6.0, 0.0), (-10.0, 0.0)
        spear_grip, spear_angle = 0.0, -40.0
    elif anim == "death":
        # He falls on his face; the next one steps up behind him.
        fall = min(1.0, t / 0.6)
        crouch = 6.0 * fall
        hip_x -= 8.0 * fall
        rot = 80.0 * min(1.0, max(0.0, (fall - 0.2) / 0.8)) ** 1.2
        eyes = "shut"
        # The spear falls with him and lies flat beside him.
        spear_grip, spear_angle = ("rest" if fall < 0.45 else 0.0), -86.0
        shadow = max(0.0, (t - 0.35) / 0.65)
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # A body on its face lies on its face, not under the floor.
    pen = S.Pen(f, (hip_x + 8.0, GROUND - 3.0), rot, (0.0, -7.0 * rot / 80.0))
    if shadow > 0.0:
        _shadow(f, 22.0 + 6.0 * shadow, 0.75 * min(1.0, shadow * 1.5))
    _figure(f, pen, hip_x, crouch, lean, bob, near_foot, far_foot, spear_grip, spear_angle, shield_up, eyes, cyc, alarm, t, anim)
    return f.finish(outline=H.SEPIA_INK, width=1.4, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
