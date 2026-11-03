"""The Privateer: a pirate with a licence, from the Age of Sail.

A lean sailor in a black tricorn with a brass edge over a red bandana, a
long red coat with brass buttons and wide cuffs, a white shirt, a sea-green
sash, brown breeches and tall black boots. A black moustache, stubble and a
gold earring. A cutlass in his hand, and on his belt his letter of marque:
a scroll with a red wax seal. A privateer was a pirate with a paper from a
king, and he wants you to know it.

He is fast. He notices you and shows you his licence first. His windup
lifts the cutlass back over his head; his strike is a long lunge and a cut
down in front. A hit knocks his hat up; at his death he falls back, his hat
rolls away, and his licence flutters down onto him.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_modern_kit as H
from . import _stage_kit as S

TARGET_NAME = "privateer"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 123.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Privateer", "Biped", "Standard", "Medium", "Walk", ["history", "sail", "pirate", "cutlass"],
    "A pirate with a licence from the Age of Sail in the History dimension: a tricorn, a long red coat, a cutlass, and "
    "a letter of marque with a red seal on his belt. He is fast; he shows you his licence, then lunges and cuts.",
)
ACTOR_METADATA["tags"] = ["enemy", "history"]

THIGH, SHIN = 10.5, 10.5
UPPER_ARM, FOREARM = 8.5, 8.5
TORSO = 19.0
HEAD_R = 6.6
BREECHES = (150, 110, 70, 255)
BREECHES_SHADE = (112, 80, 50, 255)
BANDANA = (196, 40, 44, 255)
MOUSTACHE = (34, 26, 24, 255)


def _cutlass(pen: S.Pen, hand, angle: float, length: float = 22.0) -> None:
    """A cutlass held in `hand`, its blade at `angle` degrees (0 points up,
    clockwise on the screen). The blade curves to its back edge."""
    a = math.radians(angle)
    ux, uy = math.sin(a), -math.cos(a)
    nx, ny = -uy, ux
    hx, hy = hand
    # The grip under the hand and the pommel.
    pen.limb([(hx - ux * 3.0, hy - uy * 3.0), (hx + ux * 1.5, hy + uy * 1.5)], 2.0, H.OAK_DARK)
    # The blade: wide at its middle, curved, with a point.
    base = (hx + ux * 2.5, hy + uy * 2.5)
    pts_a, pts_b = [], []
    for k in range(9):
        u = k / 8.0
        bow = 3.2 * math.sin(math.pi * u * 0.9)
        w = 2.2 * (1.0 - u) + 0.6 * math.sin(math.pi * u)
        cx = base[0] + ux * length * u + nx * bow
        cy = base[1] + uy * length * u + ny * bow
        pts_a.append((cx + nx * w, cy + ny * w))
        pts_b.append((cx - nx * w * 0.4, cy - ny * w * 0.4))
    pen.poly(pts_a + pts_b[::-1], H.STEEL)
    pen.ink([pts_b[1], pts_b[6]], 0.7, K.alpha(H.STEEL_SHADE, 0.9))
    # The brass basket over the hand.
    pen.poly([(hx + nx * 3.6 + ux * 1.0, hy + ny * 3.6 + uy * 1.0), (hx + nx * 4.4 - ux * 4.0, hy + ny * 4.4 - uy * 4.0),
              (hx - nx * 2.0 - ux * 3.0, hy - ny * 2.0 - uy * 3.0), (hx - nx * 3.4 + ux * 2.4, hy - ny * 3.4 + uy * 2.4)], H.BRASS)
    pen.ink([(hx + nx * 3.0, hy + ny * 3.0), (hx - nx * 2.6 + ux * 1.6, hy - ny * 2.6 + uy * 1.6)], 0.6, H.BRASS_DARK)


def _scroll_rolled(pen: S.Pen, x: float, y: float, angle: float) -> None:
    """The letter of marque rolled up, with its seal on a ribbon."""
    body = K.turn([(x - 2.0, y - 5.0), (x + 2.0, y - 5.0), (x + 2.0, y + 5.0), (x - 2.0, y + 5.0)], x, y, angle)
    pen.poly(body, H.PARCHMENT)
    pen.ellipse(*K.turn([(x, y - 5.0)], x, y, angle)[0], 2.0, 1.0, H.PARCHMENT_SHADE, body=False)
    sx, sy = K.turn([(x + 1.0, y + 3.0)], x, y, angle)[0]
    pen.ink([(sx, sy), (sx + 0.6, sy + 3.0)], 0.7, H.SEAL_RED)
    pen.ellipse(sx + 0.8, sy + 3.6, 1.8, 1.8, H.SEAL_RED)


def _scroll_open(pen: S.Pen, x: float, y: float, u: float, angle: float = 0.0) -> None:
    """The letter of marque unrolled `u` (0..1) down from its top roll, held up
    at its top. Lines of writing, a signature and a red seal."""
    w, h = 13.0, 4.0 + 13.0 * u

    def T(px, py):
        return K.turn([(x + px, y + py)], x, y, angle)[0]

    pen.poly([T(-w / 2, 0.0), T(w / 2, 0.0), T(w / 2, h), T(-w / 2, h)], H.PARCHMENT)
    pen.limb([T(-w / 2 - 1.0, 0.0), T(w / 2 + 1.0, 0.0)], 2.6, H.PARCHMENT_SHADE)
    pen.limb([T(-w / 2 - 1.0, h), T(w / 2 + 1.0, h)], 2.6, H.PARCHMENT_SHADE)
    for k in range(int(4 * u)):
        yy = 3.0 + k * 2.4
        pen.ink([T(-w / 2 + 2.0, yy), T(w / 2 - 2.0 - (k % 2) * 2.0, yy)], 0.6, K.alpha(H.SEPIA_DARK, 0.85))
    if u > 0.7:
        pen.ellipse(*T(w / 2 - 3.2, h - 3.0), 2.2, 2.2, H.SEAL_RED)
        pen.ink([T(-w / 2 + 2.0, h - 2.6), T(-w / 2 + 3.6, h - 3.8), T(-w / 2 + 5.0, h - 2.4), T(-w / 2 + 6.6, h - 3.6)], 0.6, H.SEPIA_DARK)


def _tricorn(pen: S.Pen, cx: float, cy: float, spin: float) -> None:
    """The tricorn from the side: a low crown in a brim turned up, a point to
    the front and one to the back, a brass edge."""
    def T(pts):
        return K.turn([(cx + x, cy + y) for x, y in pts], cx, cy, spin)

    pen.poly(T([(-5.0, 2.0), (5.0, 2.0), (4.4, -4.4), (0.0, -6.2), (-4.4, -4.4)]), H.TAR)
    brim = T([(-10.0, -1.2), (-6.0, 1.4), (0.0, 2.6), (6.0, 1.4), (10.4, -1.6), (8.0, 3.6), (0.0, 5.0), (-8.0, 3.6)])
    pen.poly(brim, H.TAR)
    pen.ink(T([(-10.0, -1.2), (-6.0, 1.4), (0.0, 2.6), (6.0, 1.4), (10.4, -1.6)]), 0.9, H.BRASS)
    pen.ink(T([(-3.0, -3.6), (1.8, -4.8)]), 0.7, H.TAR_LIGHT)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"privateer:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)

    hip_x, crouch, lean, stride, bob = 50.0, 0.0, 2.0, 0.0, 0.0
    eyes, mouth, brows, alarm, fade, rot = "squint", "grin", "down", False, 1.0, 0.0
    sword = ("shoulder", 0.0)
    far = "hip"
    scroll_u = None
    hat_off, tails, licence_drop = None, 0.2, None
    if anim == "idle":
        # He rocks on his heels, a hand on his hip and the other on the
        # pommel of his cutlass, its point on the deck. He taps the pommel.
        bob = 0.7 * math.sin(cyc)
        lean = 2.0 + 1.5 * math.sin(cyc)
        tails = 0.2 + 0.15 * math.sin(cyc)
        sword = ("lean", max(0.0, math.sin(cyc * 2.0)))
    elif anim == "walk":
        # A fast swagger: a long stride, leaning in, the coat tails flying.
        stride = math.sin(cyc)
        bob = -1.6 * abs(math.sin(cyc))
        lean = 10.0
        tails = 0.8 + 0.2 * math.sin(cyc * 2.0)
        sword = ("low", 6.0 * math.sin(cyc))
        far = ("swing", -math.sin(cyc))
    elif anim == "notice":
        # The licence first: he holds it up and it unrolls. "All legal."
        eyes, mouth, brows, alarm = "wide", "grin", "up", True
        bob = -1.5 * math.sin(math.pi * t)
        far, scroll_u = "show", min(1.0, 0.25 + t)
        sword = ("low", 0.0)
    elif anim == "windup":
        lean, crouch, stride = -10.0, 3.0, 0.6
        sword = ("raised", 4.0 * math.sin(cyc * 2.0))
        far = "forward"
        eyes, mouth, brows = "squint", "teeth", "down"
        bob = 0.4 * math.sin(cyc * 2.0)
        tails = 0.4
    elif anim == "attack_side":
        # The lunge: the cut comes over and down in front, the body after it.
        u = min(1.0, t * 1.5)
        lean = -10.0 + 30.0 * math.sin(math.pi * 0.5 * u)
        crouch = 3.0 + 4.0 * u
        stride = 0.6 + 0.5 * u
        hip_x += 14.0 * u
        sword = ("cut", u)
        far = "back"
        eyes, mouth, brows = "squint", "teeth", "down"
        tails = 0.5 + 0.5 * u
    elif anim == "hit":
        lean, crouch = -16.0, 3.0
        hip_x -= 5.0 * math.sin(math.pi * t)
        eyes, mouth, brows = "x", "o", "up"
        hat_off = (hip_x + 6.0 + 8.0 * t, 58.0 - 10.0 * t, -30.0 - 40.0 * t)
        sword = ("flail", 0.0)
        far = "flail"
        tails = 0.6
    elif anim == "death":
        fall = min(1.0, t / 0.85)
        eyes, mouth, brows = "shut", "o", "up"
        lean = -8.0 - 6.0 * fall
        crouch = 5.0 * min(1.0, fall * 2.0)
        hip_x += 24.0 * fall
        rot = -84.0 * max(0.0, (fall - 0.25) / 0.75) ** 1.3
        sword = ("drop", fall)
        far = "limp"
        tails = -0.6
        drop = min(1.0, fall * 1.5)
        hat_off = (hip_x - 8.0 + 34.0 * fall, 60.0 + (GROUND - 66.0) * drop * drop, 200.0 * fall)
        # The licence flutters down and lands on his chest.
        # It leaves his belt, goes up on the air of his fall, and comes down.
        rise = math.sin(math.pi * min(1.0, fall * 1.4))
        licence_drop = (hip_x - 4.0 + 4.0 * math.sin(cyc * 1.5), GROUND - 22.0 - 30.0 * rise + 12.0 * fall, 40.0 * math.sin(cyc * 2.0))
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    pen = S.Pen(f, (hip_x - 12.0, GROUND - 4.0), rot, (0.0, 6.0 * rot / 84.0))
    flat = S.Pen(f)
    hip_y = GROUND - (THIGH + SHIN - 1.0) + crouch + bob
    lr = math.radians(lean)

    def up(p, length):
        return (p[0] + math.sin(lr) * length, p[1] - math.cos(lr) * length)

    def across(p, w):
        return (p[0] + math.cos(lr) * w, p[1] + math.sin(lr) * w)

    hip = (hip_x, hip_y)
    shoulder = up(hip, TORSO - 3.0)
    neck = up(hip, TORSO)
    head = up(across(neck, 0.6), HEAD_R + 1.4)
    hx, hy = head

    # The coat behind the body: its tails fly behind as he moves.
    fly = 6.0 + 10.0 * tails
    back_sh = across(shoulder, -4.0)
    hem = hip_y + 13.0
    coat_back = [(back_sh[0], back_sh[1]), (hip_x - 3.0, hip_y), (hip_x - 5.0 - fly * 0.5, hem),
                 (hip_x - 9.0 - fly, hem - 2.0 - fly * 0.45), (hip_x - 7.0 - fly * 0.4, hip_y - 2.0)]
    pen.poly(coat_back, H.COAT_RED_DARK)
    pen.ink([(hip_x - 5.0, hip_y + 2.0), (hip_x - 7.0 - fly * 0.7, hem - 2.0)], 0.7, K.shade(H.COAT_RED_DARK, 0.7))

    # The far arm and hand.
    if far == "hip":
        fh = (hip_x - 3.0, hip_y - 4.0)
    elif far == "show":
        fh = (shoulder[0] + 15.0, shoulder[1] - 6.0)
    elif far == "forward":
        fh = (shoulder[0] + 13.0, shoulder[1] + 1.0)
    elif far == "back":
        fh = (shoulder[0] - 12.0, shoulder[1] + 4.0)
    elif far == "flail":
        fh = (shoulder[0] - 7.0, shoulder[1] - 12.0)
    elif far == "limp":
        fh = (hip_x - 10.0, hip_y + 3.0)
    else:
        fh = (hip_x + 6.0 * far[1], hip_y + 1.0)
    f_elbow, fh = S.joint(shoulder, fh, UPPER_ARM, FOREARM, 1.0)
    pen.limb([shoulder, f_elbow, fh], 4.2, H.COAT_RED_DARK)
    pen.ellipse(fh[0], fh[1], 2.2, 2.2, H.SKIN_TAN_SHADE)

    def leg(side: float, colour, boot):
        swing = stride * side
        foot = (hip_x + 8.0 * swing + side * 1.5 + 1.0, GROUND - 2.0)
        if anim == "walk":
            foot = (foot[0], GROUND - 2.0 - max(0.0, 4.0 * math.sin(cyc + (0.0 if side > 0 else math.pi))))
        knee, foot = S.joint((hip_x + side * 1.2, hip_y), foot, THIGH, SHIN, -1.0)
        pen.limb([(hip_x + side * 1.2, hip_y), knee], 5.0, colour)
        # A tall boot from under the knee, with a turned-down cuff.
        mid = (knee[0] * 0.25 + foot[0] * 0.75, knee[1] * 0.25 + foot[1] * 0.75)
        pen.limb([knee, foot], 5.0, boot)
        pen.limb([(knee[0] * 0.8 + foot[0] * 0.2, knee[1] * 0.8 + foot[1] * 0.2), (knee[0] * 0.65 + foot[0] * 0.35, knee[1] * 0.65 + foot[1] * 0.35)], 6.2, boot)
        del mid
        pen.poly([(foot[0] - 2.6, foot[1] - 2.2), (foot[0] + 5.4, foot[1] - 1.0), (foot[0] + 5.6, foot[1] + 1.8), (foot[0] - 2.6, foot[1] + 1.8)], boot)
        pen.dot(foot[0] + 2.6, foot[1] - 0.4, 0.6, K.alpha(H.WHITE, 0.6))

    leg(-1.0, BREECHES_SHADE, K.shade(H.TAR, 0.8))

    # The body: a shirt, the coat open over it, the sash and the belt.
    hb, hf = across(hip, -5.0), across(hip, 5.0)
    sb, sf = across(shoulder, -5.5), across(shoulder, 4.5)
    nb, nf = across(neck, -3.0), across(neck, 2.6)
    pen.poly([hb, hf, sf, nf, nb, sb], H.COAT_RED)
    pen.poly([across(up(hip, 2.0), 0.5), across(up(hip, 2.0), 4.6), sf, nf, across(neck, 0.0)], H.SHIRT, body=False)
    # The ruffle of the shirt at the throat.
    for k in range(3):
        p = across(up(neck, -2.0 - k * 2.2), 2.6)
        pen.ellipse(p[0], p[1], 1.6, 1.2, H.SHIRT)
    pen.poly([hb, across(hip, -1.5), across(shoulder, -2.0), sb], H.COAT_RED_DARK, body=False)
    for k in range(3):
        b = across(up(hip, 5.0 + k * 4.0), 4.8)
        pen.dot(b[0], b[1], 0.9, H.BRASS)
    # The front skirt of the coat, which swings as he goes.
    front_hem = (hip_x + 5.0 + 2.0 * tails, hem - 1.0)
    pen.poly([hf, across(hip, 1.0), (hip_x + 1.0, hem), front_hem], H.COAT_RED)
    pen.ink([across(hip, 1.5), (hip_x + 1.5, hem - 0.5)], 0.7, H.COAT_RED_DARK)
    sash = [across(up(hip, -1.0), -5.2), across(up(hip, -1.0), 5.2), across(up(hip, 3.0), 5.0), across(up(hip, 3.0), -5.0)]
    pen.poly(sash, H.SEA_GREEN)
    pen.ink([across(up(hip, 1.0), -4.8), across(up(hip, 1.0), 4.8)], 0.6, H.SEA_GREEN_DARK)
    pen.poly([across(up(hip, -1.0), -7.0), across(up(hip, -1.0), -4.6), (hip_x - 8.0 - tails * 3.0, hip_y + 6.0)], H.SEA_GREEN)
    buckle = across(up(hip, 1.0), 1.6)
    pen.poly([(buckle[0] - 1.6, buckle[1] - 1.4), (buckle[0] + 1.6, buckle[1] - 1.4), (buckle[0] + 1.6, buckle[1] + 1.4), (buckle[0] - 1.6, buckle[1] + 1.4)], H.BRASS, body=False)
    # The licence on his belt (not when it is in his hand, or blown away).
    if scroll_u is None and licence_drop is None:
        lp = across(up(hip, -2.0), 6.0)
        _scroll_rolled(pen, lp[0], lp[1] + 3.0, -12.0 + 6.0 * stride)

    leg(1.0, BREECHES, H.TAR)

    # The head: a tan face, a red bandana and the tricorn.
    pen.ellipse(hx, hy, HEAD_R, HEAD_R * 1.05, H.SKIN_TAN)
    pen.poly([(hx - HEAD_R + 0.6, hy - 1.0), (hx - 1.0, hy - 4.6), (hx + 4.0, hy - 5.0), (hx + HEAD_R - 0.4, hy - 3.2),
              (hx + HEAD_R - 0.4, hy - 5.4), (hx - 1.0, hy - 7.4), (hx - HEAD_R, hy - 4.0)], BANDANA, body=False)
    # The knot of the bandana and its tails behind the head.
    kx, ky = hx - HEAD_R + 0.5, hy - 3.6
    sway = (2.0 + 4.0 * tails) if anim != "death" else 0.0
    pen.limb([(kx, ky), (kx - 3.0 - sway * 0.5, ky + 4.0), (kx - 4.0 - sway, ky + 7.0)], 2.0, BANDANA)
    pen.limb([(kx, ky), (kx - 4.5 - sway * 0.6, ky + 2.0)], 1.8, BANDANA)
    # Stubble and a shade under the cheek.
    pen.ellipse(hx + 2.6, hy + 3.6, 3.8, 2.4, K.alpha(H.SKIN_TAN_SHADE, 0.9), body=False)
    # The nose.
    pen.poly([(hx + HEAD_R - 1.4, hy - 1.6), (hx + HEAD_R + 2.6, hy + 1.6), (hx + HEAD_R - 1.0, hy + 2.2)], H.SKIN_TAN)
    # The moustache: black, with curled ends.
    my = hy + 3.0
    pen.poly([(hx + 2.6, my), (hx + 5.0, my - 1.0), (hx + 7.6, my - 0.6), (hx + 8.0, my + 0.8), (hx + 5.0, my + 1.4), (hx + 2.6, my + 1.2)], MOUSTACHE)
    pen.ink([(hx + 2.8, my + 0.6), (hx + 1.0, my - 0.4), (hx + 1.2, my - 1.8)], 1.0, MOUSTACHE)
    if mouth == "o":
        pen.ellipse(hx + 5.0, my + 3.2, 1.3, 1.5, H.OUTLINE, body=False)
    elif mouth == "teeth":
        pen.poly([(hx + 3.2, my + 2.0), (hx + 7.2, my + 1.6), (hx + 6.6, my + 3.8), (hx + 3.8, my + 3.8)], H.WHITE, body=False)
        pen.ink([(hx + 3.2, my + 2.9), (hx + 7.0, my + 2.7)], 0.5, H.OUTLINE)
    else:
        pen.ink([(hx + 3.0, my + 2.4), (hx + 5.0, my + 3.2), (hx + 7.0, my + 2.0)], 0.8, H.OUTLINE)
        pen.dot(hx + 5.6, my + 2.8, 0.6, (250, 220, 90, 255))
    # The gold earring.
    pen.ellipse(hx - 0.6, hy + 2.6, 1.0, 1.4, K.alpha(H.GOLD, 1.0), body=False)
    ex, ey = hx + 3.6, hy - 1.2
    if eyes == "x":
        pen.ink([(ex - 1.2, ey - 1.2), (ex + 1.2, ey + 1.2)], 0.9, H.OUTLINE)
        pen.ink([(ex - 1.2, ey + 1.2), (ex + 1.2, ey - 1.2)], 0.9, H.OUTLINE)
    elif eyes == "shut":
        pen.ink([(ex - 1.4, ey), (ex, ey + 0.8), (ex + 1.4, ey)], 0.9, H.OUTLINE)
    elif eyes == "wide":
        pen.ellipse(ex, ey, 1.6, 1.9, H.WHITE, body=False)
        pen.dot(ex + 0.5, ey, 0.9, H.OUTLINE)
    else:
        pen.ellipse(ex, ey, 1.4, 1.0, H.WHITE, body=False)
        pen.dot(ex + 0.4, ey + 0.1, 0.7, H.OUTLINE)
    brow_y = {"down": -3.0, "up": -4.4}[brows]
    tip = -1.0 if brows == "down" else 0.5
    pen.ink([(ex - 2.0, ey + brow_y - 0.6), (ex + 1.8, ey + brow_y + tip + 0.4)], 1.1, MOUSTACHE)

    if hat_off is None:
        _tricorn(pen, hx - 0.5, hy - 6.6, lean * 0.3)
    else:
        _tricorn(flat, *hat_off)

    # The near arm and the cutlass.
    kind, v = sword
    if kind == "lean":
        nh, blade = (hip_x + 11.0, hip_y - 6.0 - 1.2 * v), 172.0
    elif kind == "low":
        nh, blade = (hip_x + 9.0 + 0.6 * v, hip_y - 3.0), 80.0 + v
    elif kind == "raised":
        nh, blade = (shoulder[0] - 3.0, shoulder[1] - 13.0 + 0.3 * v), -60.0 + v
    elif kind == "cut":
        a = math.radians(-60.0 + 170.0 * v)
        nh = (shoulder[0] + 2.0 + math.sin(a) * 15.0, shoulder[1] - math.cos(a) * 15.0)
        blade = -60.0 + 170.0 * v
        if 0.15 < v < 0.8:
            # The swish of the cut: a short arc behind the blade.
            arc = []
            for k in range(8):
                aa = math.radians(blade - 90.0 + 80.0 * k / 7.0)
                r = 30.0
                arc.append((shoulder[0] + 2.0 + math.sin(aa) * r, shoulder[1] - math.cos(aa) * r))
            pen.ink(arc, 1.8, K.alpha(H.STEEL, 0.5))
            pen.ink(arc[4:], 0.9, K.alpha(H.WHITE, 0.85))
    elif kind == "flail":
        nh, blade = (shoulder[0] + 10.0, shoulder[1] - 6.0), 70.0
    else:
        nh, blade = (hip_x + 8.0, hip_y + 2.0), 100.0 + 50.0 * v
    if kind == "drop" and v > 0.5:
        # The cutlass falls from his hand and lies on the floor.
        _cutlass(flat, (hip_x + 6.0, GROUND - 6.0), 94.0)
        n_elbow, nh = S.joint(shoulder, nh, UPPER_ARM, FOREARM, 1.0)
        pen.limb([shoulder, n_elbow, nh], 4.4, H.COAT_RED)
        pen.ellipse(nh[0], nh[1], 2.2, 2.2, H.SKIN_TAN)
    else:
        n_elbow, nh = S.joint(shoulder, nh, UPPER_ARM, FOREARM, 1.0)
        pen.limb([shoulder, n_elbow, nh], 4.4, H.COAT_RED)
        cuff = (n_elbow[0] * 0.3 + nh[0] * 0.7, n_elbow[1] * 0.3 + nh[1] * 0.7)
        pen.ellipse(cuff[0], cuff[1], 2.8, 2.8, H.COAT_RED_DARK)
        _cutlass(pen, nh, blade)
        pen.ellipse(nh[0], nh[1], 2.2, 2.2, H.SKIN_TAN)

    if scroll_u is not None:
        _scroll_open(pen, fh[0] + 1.0, fh[1] - 2.0, scroll_u, 4.0)
        pen.ellipse(fh[0], fh[1], 2.2, 2.2, H.SKIN_TAN_SHADE)
    if licence_drop is not None:
        x, y, spin = licence_drop
        if anim == "death":
            x, y = min(x, 112.0), min(y, GROUND - 23.0)
        _scroll_open(flat, x, y, 1.0, spin)
    if anim == "hit":
        for k in range(4):
            a = math.radians(-60.0 + k * 40.0)
            sx, sy = hx + 2.0 + math.cos(a) * 11.0, hy - 2.0 + math.sin(a) * 11.0
            flat.ink([(sx, sy), (sx + math.cos(a) * 4.0, sy + math.sin(a) * 4.0)], 1.0, H.BRASS_LIGHT)
    del rng
    if alarm:
        H.alarm_mark(f, hx + 12.0, hy - 22.0)
    return H.finish(f, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
