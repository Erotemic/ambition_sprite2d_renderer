"""The Critic: a theatre critic of the Amphitheatre, who throws tomatoes.

A portly man in evening dress: a black opera cape lined in red velvet with
a high collar, a gold waistcoat over a round belly, a white shirt front and
a black bow tie, a top hat with a red band. A monocle on a cord, a grey
moustache, and his nose in the air. He holds a notepad in one hand and
writes his review of you in it.

He keeps his distance and throws tomatoes. His windup lifts a tomato back
over his shoulder and holds the notepad up in front of him; his strike
throws it, and the tomato flies out of his hand. A hit knocks his hat off
and a page out of his notepad; at his death he faints, a hand on his brow,
and falls back, and his pages blow away.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _stage_kit as S

TARGET_NAME = "critic"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 124.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Critic", "Biped", "Standard", "Medium", "Walk", ["stage", "critic", "tomato"],
    "A portly theatre critic of the Amphitheatre of the Art dimension, in an opera cape and a top hat, with a monocle "
    "and a notepad. He keeps his distance, lifts a tomato back over his shoulder and throws it.",
)

THIGH, SHIN = 9.5, 9.5
UPPER_ARM, FOREARM = 9.0, 9.0
TORSO = 21.0
HEAD_R = 7.2
CAPE = (40, 36, 52, 255)
CAPE_SHADE = (26, 22, 36, 255)
WAISTCOAT = (226, 176, 64, 255)
WAISTCOAT_SHADE = (176, 126, 36, 255)
TROUSERS = (70, 70, 86, 255)
TROUSERS_SHADE = (48, 48, 62, 255)
MOUSTACHE = (196, 196, 206, 255)
FACE = (246, 196, 170, 255)
FACE_FLUSH = (236, 150, 140, 255)


def _tomato(pen: S.Pen, x: float, y: float, r: float = 4.2, spin: float = 0.0) -> None:
    pen.ellipse(x, y, r, r * 0.9, S.TOMATO)
    pen.ellipse(x + r * 0.25, y + r * 0.25, r * 0.6, r * 0.5, S.TOMATO_DARK, body=False)
    pen.dot(x - r * 0.4, y - r * 0.35, r * 0.25, K.alpha(K.WHITE, 0.9))
    for k in range(3):
        a = math.radians(spin - 90.0 + (k - 1) * 55.0)
        pen.ink([(x, y - r * 0.8), (x + math.cos(a) * r * 0.7, y - r * 0.8 + math.sin(a) * r * 0.5 - 0.6)], 1.0, S.LEAF)


def _notepad(pen: S.Pen, x: float, y: float, angle: float = 0.0, scribble: int = 3) -> None:
    pad = K.turn([(x - 4.0, y - 5.5), (x + 4.0, y - 5.5), (x + 4.0, y + 5.5), (x - 4.0, y + 5.5)], x, y, angle)
    pen.poly(pad, K.PAPER)
    pen.poly(K.turn([(x - 4.0, y - 5.5), (x + 4.0, y - 5.5), (x + 4.0, y - 3.8), (x - 4.0, y - 3.8)], x, y, angle), S.VELVET_DARK, body=False)
    for k in range(scribble):
        yy = y - 1.8 + k * 2.4
        pen.ink(K.turn([(x - 2.8, yy), (x - 0.5, yy - 0.5), (x + 1.0, yy + 0.3), (x + 2.8, yy - 0.2)], x, y, angle), 0.6, K.alpha(K.INK, 0.75))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"critic:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)

    hip_x, crouch, lean, stride, bob, sway = 48.0, 0.0, -4.0, 0.0, 0.0, 0.0
    brows, eyes, mouth, monocle, alarm, fade = "high", "lidded", "sniff", "eye", False, 1.0
    hand_n = hand_f = None
    tomato_in_hand, tomato_flying = False, None
    hat_off, cape_flare, rot, pages = None, 0.0, 0.0, 0
    nose_up = 6.0
    if anim == "idle":
        # He writes: the pencil scratches, the head goes down to the pad and up.
        bob = 0.6 * math.sin(cyc)
        nose_up = 4.0 + 5.0 * max(0.0, math.sin(cyc))
        hand_n = "write"
    elif anim == "walk":
        stride = math.sin(cyc)
        bob = -1.2 * abs(math.sin(cyc))
        sway = 3.0 * math.sin(cyc)
        cape_flare = 0.6 + 0.3 * math.sin(cyc * 2.0)
        lean = 2.0
    elif anim == "notice":
        brows, eyes, mouth, monocle, alarm = "up", "wide", "o", "drop", True
        bob = -3.0 * math.sin(math.pi * t)
        nose_up = 0.0
    elif anim == "windup":
        lean, crouch, stride = -12.0, 2.0, 0.5
        hand_n, hand_f, tomato_in_hand = "back", "shield", True
        brows, eyes, mouth = "down", "lidded", "sneer"
        bob = 0.5 * math.sin(cyc * 2.0)
        cape_flare = 0.3
    elif anim == "attack_side":
        # Back (0), over the head (1), out with the throw (2), and after.
        throw = min(1.0, t * 1.6)
        lean = -12.0 + 26.0 * math.sin(math.pi * 0.5 * throw)
        crouch, stride, cape_flare = 2.0 + 2.0 * throw, 0.5 + 0.4 * throw, 0.3 + 0.6 * throw
        hand_n, hand_f = ("throw", throw), "shield"
        tomato_in_hand = throw < 0.5
        if throw >= 0.5:
            u = (t - 0.5 / 1.6) / (1.0 - 0.5 / 1.6)
            tomato_flying = (78.0 + 36.0 * u, 76.0 - 10.0 * math.sin(math.pi * min(1.0, u * 0.9)) + 6.0 * u * u, 260.0 * u)
        brows, eyes, mouth = "down", "lidded", "open"
        hip_x += 4.0 * throw
    elif anim == "hit":
        lean, crouch = -16.0, 3.0
        hip_x -= 4.0 * math.sin(math.pi * t)
        brows, eyes, mouth, monocle = "up", "x", "o", "drop"
        hat_off = (hip_x + 8.0 + 10.0 * t, 52.0 - 12.0 * t, -40.0 * t)
        pages = 2
        hand_n, hand_f = "flail", "flail"
    elif anim == "death":
        fall = min(1.0, t / 0.85)
        brows, eyes, mouth, monocle = "up", "shut", "o", "drop"
        hand_n, hand_f = "brow", "limp"
        lean = -6.0 - 8.0 * fall
        crouch = 6.0 * min(1.0, fall * 2.0)
        hip_x += 30.0 * fall
        cape_flare = -0.8
        rot = -82.0 * max(0.0, (fall - 0.3) / 0.7) ** 1.3
        # The hat falls off behind him and rolls along the floor.
        drop = min(1.0, fall * 1.6)
        hat_off = (hip_x + 2.0 + 28.0 * fall, 64.0 + (GROUND - 72.0) * drop * drop, 120.0 * fall)
        pages = 1 + int(4 * t)
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    pen = S.Pen(f, (hip_x - 14.0, GROUND - 4.0), rot)
    flat = S.Pen(f)
    hip_y = GROUND - (THIGH + SHIN - 1.0) + crouch + bob
    lr = math.radians(lean + sway * 0.4)

    def up(p, length):
        return (p[0] + math.sin(lr) * length, p[1] - math.cos(lr) * length)

    def across(p, w):
        return (p[0] + math.cos(lr) * w, p[1] + math.sin(lr) * w)

    hip = (hip_x, hip_y)
    belly = up(across(hip, 4.0), 9.0)
    shoulder = up(hip, TORSO - 4.0)
    neck = up(hip, TORSO)
    head = up(across(neck, 1.0), HEAD_R + 1.0)
    hx, hy = head

    # The hands.
    if hand_n == "write":
        nh = (belly[0] + 10.0 + 1.5 * math.sin(cyc * 3.0), belly[1] - 2.0 + 0.8 * math.cos(cyc * 3.0))
    elif hand_n == "back":
        nh = (shoulder[0] - 11.0, shoulder[1] - 8.0 + 1.0 * math.sin(cyc * 2.0))
    elif isinstance(hand_n, tuple):
        th = hand_n[1]
        a = math.radians(200.0 + 150.0 * th)
        nh = (shoulder[0] + 2.0 + math.cos(a) * 16.0, shoulder[1] + math.sin(a) * 16.0)
    elif hand_n == "flail":
        nh = (shoulder[0] + 9.0, shoulder[1] - 13.0)
    elif hand_n == "brow":
        nh = (hx + 2.0, hy - 5.0)
    else:
        swing = math.sin(cyc) if anim == "walk" else 0.0
        nh = (hip_x + 9.0 + 4.0 * swing, hip_y - 1.0)
    if hand_f == "shield":
        fh = (shoulder[0] + 12.0, shoulder[1] - 2.0)
    elif hand_f == "flail":
        fh = (shoulder[0] - 8.0, shoulder[1] - 12.0)
    elif hand_f == "limp":
        fh = (hip_x - 10.0, hip_y + 2.0)
    else:
        fh = (belly[0] + 9.0, belly[1] - 3.0)

    # The cape, behind it all: a high collar and a fall of black lined in red.
    flare = 8.0 + 8.0 * cape_flare
    back_sh = across(shoulder, -6.0)
    hem_y = hip_y + 14.0
    cape = [(back_sh[0] + 2.0, back_sh[1] - 2.0), (neck[0] + 3.0, neck[1]), (hip_x + 2.0, hem_y - 2.0),
            (hip_x - 8.0 - flare * 0.6, hem_y), (hip_x - 12.0 - flare, hem_y - 3.0 - flare * 0.4), (back_sh[0] - 4.0, back_sh[1] + 6.0)]
    pen.poly(cape, CAPE)
    pen.poly([(hip_x - 8.0 - flare * 0.6, hem_y), (hip_x - 12.0 - flare, hem_y - 3.0 - flare * 0.4), (back_sh[0] - 3.0, back_sh[1] + 8.0),
              (hip_x - 9.0 - flare * 0.7, hem_y - 4.0)], S.VELVET, body=False)
    pen.ink([(back_sh[0] - 1.0, back_sh[1] + 6.0), (hip_x - 6.0 - flare * 0.5, hem_y - 2.0)], 0.8, CAPE_SHADE)
    collar = [(neck[0] - 5.0, neck[1] + 2.0), (neck[0] - 8.0, neck[1] - 9.0), (neck[0] - 3.0, neck[1] - 6.0), (neck[0] + 1.0, neck[1] + 1.0)]
    pen.poly(collar, S.VELVET)
    pen.poly([(neck[0] - 5.0, neck[1] + 2.0), (neck[0] - 8.0, neck[1] - 9.0), (neck[0] - 6.5, neck[1] - 8.0), (neck[0] - 3.5, neck[1] + 1.5)], S.VELVET_DARK, body=False)

    def leg(side: float, colour):
        swing = stride * side
        foot = (hip_x + 7.0 * swing + side * 2.5 + 1.0, GROUND - 2.0)
        knee, foot = S.joint((hip_x + side * 1.5, hip_y), foot, THIGH, SHIN, -1.0)
        pen.limb([(hip_x + side * 1.5, hip_y), knee, foot], 5.4, colour)
        pen.poly([(foot[0] - 2.5, foot[1] - 2.0), (foot[0] + 5.0, foot[1] - 1.0), (foot[0] + 5.5, foot[1] + 1.8), (foot[0] - 2.5, foot[1] + 1.8)], K.INK)
        pen.dot(foot[0] + 2.5, foot[1] - 0.6, 0.6, K.alpha(K.WHITE, 0.8))

    def arm(hand, colour, sleeve=CAPE):
        elbow, hand = S.joint(shoulder, hand, UPPER_ARM, FOREARM, 1.0)
        pen.limb([shoulder, elbow, hand], 4.6, sleeve)
        pen.ellipse(hand[0], hand[1], 2.4, 2.4, K.WHITE)
        return hand

    leg(-1.0, TROUSERS_SHADE)
    fhand = arm(fh, CAPE_SHADE, CAPE_SHADE)
    if hand_f in ("shield", None) and anim != "death":
        _notepad(pen, fhand[0] + 2.0, fhand[1] - 1.0, angle=8.0 if hand_f == "shield" else -10.0, scribble=3)

    # The body: a round belly in a gold waistcoat, a shirt front, a bow tie.
    hb, hf = across(hip, -6.0), across(hip, 7.0)
    sb, sf = across(shoulder, -6.5), across(shoulder, 5.0)
    nb, nf = across(neck, -3.5), across(neck, 3.0)
    bf = across(belly, 7.5)
    pen.poly([hb, hf, bf, sf, nf, nb, sb], WAISTCOAT)
    pen.ellipse(belly[0] + 1.5, belly[1] + 1.0, 9.5, 9.0, WAISTCOAT)
    pen.poly([hb, across(hip, -1.0), across(up(hip, 8.0), -1.5), across(shoulder, -2.0), sb], WAISTCOAT_SHADE, body=False)
    pen.poly([across(up(hip, 1.0), 3.0), across(up(hip, 1.0), 7.0), across(belly, 7.5), sf], K.alpha(WAISTCOAT, 1.0), body=False)
    shirt = [across(up(hip, 9.0), 4.5), across(up(hip, 9.0), 6.8), nf, across(neck, 0.5)]
    pen.poly(shirt, K.WHITE, body=False)
    for k in range(3):
        b = across(up(hip, 3.0 + k * 3.5), 6.2 + (1.2 if k < 2 else 0.4))
        pen.dot(b[0], b[1], 0.8, WAISTCOAT_SHADE)
    # A watch chain across the belly.
    pen.ink([across(up(hip, 4.0), 0.0), across(up(hip, 2.5), 4.0), across(up(hip, 5.0), 7.0)], 0.7, K.GOLD_DARK)
    bt = across(up(neck, -1.0), 2.5)
    pen.poly([(bt[0] - 2.4, bt[1] - 1.6), (bt[0], bt[1]), (bt[0] - 2.4, bt[1] + 1.6)], K.INK, body=False)
    pen.poly([(bt[0] + 2.4, bt[1] - 1.6), (bt[0], bt[1]), (bt[0] + 2.4, bt[1] + 1.6)], K.INK, body=False)
    leg(1.0, TROUSERS)

    # The head: nose in the air.
    tilt = -nose_up + lean * 0.3
    pen.ellipse(hx, hy, HEAD_R, HEAD_R * 1.02, FACE)
    pen.ellipse(hx - 2.6, hy + 1.4, 1.6, 2.2, FACE_FLUSH, body=False)

    def H(x, y):
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    nose = [H(5.4, -1.4), H(9.4, 0.6), H(5.6, 2.2)]
    pen.poly(nose, FACE)
    pen.dot(*H(1.4, 1.6), 1.6, FACE_FLUSH)
    # Moustache: a grey bar with two curled ends.
    m0 = H(5.8, 3.2)
    pen.poly([H(1.0, 3.2), H(4.0, 2.2), H(7.6, 2.6), H(8.4, 4.0), H(5.0, 4.6), H(2.0, 4.6)], MOUSTACHE)
    pen.ink([H(1.4, 3.8), H(-0.6, 2.8), H(-0.4, 1.4)], 1.2, MOUSTACHE)
    pen.ink([H(8.2, 3.6), H(9.8, 2.6), H(9.4, 1.2)], 1.2, MOUSTACHE)
    del m0
    if mouth == "o":
        pen.ellipse(*H(5.6, 6.0), 1.4, 1.6, K.INK, body=False)
    elif mouth == "open":
        pen.ellipse(*H(5.6, 5.8), 1.8, 1.2, K.INK, body=False)
    elif mouth == "sneer":
        pen.ink([H(4.0, 6.0), H(6.8, 5.2)], 0.9)
    else:
        pen.ink([H(4.2, 5.6), H(6.4, 5.8)], 0.8)
    ex, ey = H(3.6, -1.4)
    if eyes == "x":
        pen.ink([(ex - 1.2, ey - 1.2), (ex + 1.2, ey + 1.2)], 0.9)
        pen.ink([(ex - 1.2, ey + 1.2), (ex + 1.2, ey - 1.2)], 0.9)
    elif eyes == "shut":
        pen.ink([(ex - 1.5, ey), (ex, ey + 0.8), (ex + 1.5, ey)], 0.9)
    elif eyes == "wide":
        pen.ellipse(ex, ey, 1.7, 2.0, K.WHITE, body=False)
        pen.dot(ex + 0.4, ey, 0.9)
    else:
        pen.ellipse(ex, ey, 1.4, 1.1, K.WHITE, body=False)
        pen.poly([(ex - 1.6, ey - 1.3), (ex + 1.6, ey - 1.3), (ex + 1.6, ey + 0.1), (ex - 1.6, ey + 0.1)], FACE, body=False)
        pen.ink([(ex - 1.6, ey + 0.1), (ex + 1.6, ey + 0.1)], 0.7)
        pen.dot(ex + 0.3, ey + 0.6, 0.6)
    brow_y = {"high": -4.2, "up": -5.2, "down": -3.0}[brows]
    tip = -1.0 if brows == "down" else 0.6
    pen.ink([H(1.8, brow_y - 0.4), H(5.4, brow_y + tip)], 1.0, MOUSTACHE)
    # The monocle on its gold cord.
    if monocle == "eye":
        pen.ellipse(ex, ey, 2.4, 2.4, K.alpha(K.WHITE, 0.35), body=False)
        f.ink(pen.p(K.ellipse_points(ex, ey, 2.4, 2.4, 16) + [K.ellipse_points(ex, ey, 2.4, 2.4, 16)[0]]), 0.7, K.GOLD)
        pen.ink([(ex, ey + 2.4), (ex - 2.0, ey + 6.0), across(neck, 1.0)], 0.5, K.GOLD)
    else:
        mx, my = across(up(hip, 13.0), 6.5)
        pen.ink([(ex, ey + 1.0), (mx - 1.0, my - 4.0), (mx, my)], 0.5, K.GOLD)
        f.ink(pen.p(K.ellipse_points(mx, my + 2.0, 2.0, 2.0, 14) + [K.ellipse_points(mx, my + 2.0, 2.0, 2.0, 14)[0]]), 0.7, K.GOLD)

    # The top hat: on his head, or off it (a centre and a turn in the frame).
    def top_hat(hp: S.Pen, cx: float, cy: float, spin: float) -> None:
        def T(pts):
            return K.turn([(cx + x, cy + y) for x, y in pts], cx, cy, spin)
        crown = T([(-4.6, 4.0), (4.8, 4.0), (5.4, -6.0), (-4.4, -6.0)])
        hp.poly(T([(-7.4, 5.4), (7.2, 3.8), (7.4, 5.2), (-7.2, 6.6)]), CAPE)
        hp.poly(crown, CAPE)
        hp.poly(T([(-4.6, 1.6), (4.9, 1.0), (5.0, -0.8), (-4.5, -0.2)]), S.VELVET, body=False)
        hp.ink(T([(-4.2, -5.6), (5.0, -5.6)]), 0.8, S.BLACK_LIGHT)

    if hat_off is None:
        hc = H(0.2, -9.6)
        top_hat(pen, hc[0], hc[1], tilt)
    else:
        # The bare head: thin grey hair, combed over.
        pen.ink([H(-6.0, -4.0), H(-1.0, -7.0), H(4.0, -6.0)], 1.0, MOUSTACHE)
        top_hat(flat, *hat_off)

    hand = arm(nh, CAPE)
    if hand_n == "write":
        pen.limb([(hand[0] - 1.0, hand[1] + 2.0), (hand[0] + 2.0, hand[1] - 3.5)], 1.0, K.GOLD)
    if tomato_in_hand:
        _tomato(pen, hand[0] + 0.5, hand[1] - 3.0)
    if tomato_flying is not None:
        x, y, spin = tomato_flying
        for k in range(3):
            f.ink([(x - 6.0 - k * 4.0, y - 2.0 + k * 1.6), (x - 10.0 - k * 4.0, y - 2.0 + k * 1.6)], 1.0, K.alpha(S.SPOT, 0.8))
        _tomato(flat, x, y, 4.4, spin)

    for k in range(pages):
        px = hip_x - 20.0 + rng.uniform(-6.0, 40.0) + (30.0 * t if anim == "death" else 0.0)
        py = hip_y - 30.0 + rng.uniform(-10.0, 18.0) - 12.0 * t
        px, py = min(116.0, max(10.0, px)), min(GROUND - 8.0, max(10.0, py))
        page = K.turn([(px - 3.5, py - 4.5), (px + 3.5, py - 4.5), (px + 3.5, py + 4.5), (px - 3.5, py + 4.5)], px, py, rng.uniform(-40.0, 40.0))
        flat.poly(page, K.PAPER)
        flat.ink([page[0], page[2]], 0.5, K.alpha(K.INK, 0.5))

    if alarm:
        S.alarm_mark(f, hx + 13.0, hy - 22.0)
    return f.finish(width=1.4, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
