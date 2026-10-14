"""Sprite generator for the Hunny Horror: a stuffed bear that has been hungry
for a very long time.

A horror parody of Winnie-the-Pooh. The changed name keeps the reference
clear; the bear is not presented as the original.

The look (redrawn 2026-10-14). These are the design elements that a rework
must keep:

- He reads as the honey bear of the book: honey-coloured fur, a round belly,
  round ears, black bead eyes and a black nose. He wears NOTHING: the red
  shirt is not in the public-domain bear (Jon, 2026-10-14: "Can't do the red
  shirt, that's not public domain").
- He is a STUFFED TOY grown to the size of a door: a lighter tummy, an
  embroidered smile. He has NO SCARS (Jon, 2026-10-14): no seam, no
  stitches, no split on his body or his face.
- He goes from CUTE AND INNOCENT to HORRIFIC (Jon, 2026-10-14). At rest and
  when he walks he is a sweet teddy: big shiny eyes, a small smile, no claws.
  When he attacks or is angry (``horror`` in a pose), his fur bristles, his
  brow comes down, his eyes go to a honey glow, his smile tears open on too
  many teeth with honey between them, and his claws come out. After an attack he is sweet again at once.
- His arms are too long: at rest his paws hang at his knees.
- Dead, he sits down and goes limp, smaller, with X eyes: a toy again.

He faces right and stands on his hind legs, seen three quarters from the
side. He holds nothing (no honey pot: a pot would be an item). There is no
drop shadow.

Each limb is ONE piece from the shoulder or hip to the end of the paw, drawn
through a solved elbow or knee (``_ai_era_kit``): a limb has no joint for a
seam to show at. The body and the head are painted once and turned.
"""

from __future__ import annotations

import argparse
import math
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image

from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ._ai_era_kit import Kit, Point, Pose, RGBA, angle, keys, lerp, mix, solve, turned

TARGET_NAME = "hunny_horror_boss"
FRAME_SIZE = (288, 212)
GROUND = 200.0
CX = 120.0
#: Row names are the ones the game reads (`CharacterAnim::from_name`).
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 150),
    ("walk", 8, 115),
    ("slash", 8, 85),
    ("punch", 10, 80),
    ("special", 10, 84),
    ("taunt", 10, 100),
    ("hurt", 4, 90),
    ("death", 12, 110),
    # The rows of his boss fight (the conductor
    # `ambition_content_modules::hunny` draws them by name).
    ("hug", 6, 100),
    ("squeeze", 4, 110),
    ("throw", 5, 80),
    ("spit", 6, 90),
    ("run", 6, 75),
    ("flop", 8, 90),
    ("stunned", 6, 140),
]

INK: RGBA = (46, 26, 20, 255)
FUR: RGBA = (218, 160, 70, 255)
FUR_FAR: RGBA = (172, 118, 52, 255)
FUR_SHADE: RGBA = (132, 74, 30, 255)
FUR_DEEP: RGBA = (168, 104, 38, 255)
EAR_INNER: RGBA = (176, 110, 44, 255)
HONEY: RGBA = (244, 164, 24, 255)
HONEY_LIGHT: RGBA = (255, 226, 124, 255)
STUFFING: RGBA = (246, 238, 218, 255)
STUFFING_SHADE: RGBA = (210, 196, 172, 255)
THREAD: RGBA = (24, 14, 14, 255)
MOUTH: RGBA = (66, 14, 22, 255)
TONGUE: RGBA = (226, 112, 120, 255)
GUM: RGBA = (150, 46, 58, 255)
TOOTH: RGBA = (246, 238, 214, 255)
CLAW: RGBA = (232, 222, 196, 255)
NOSE: RGBA = (30, 18, 18, 255)
BEAD: RGBA = (18, 10, 10, 255)
GLOW: RGBA = (255, 188, 44, 255)
GLOW_CORE: RGBA = (255, 248, 196, 255)
WHITE: RGBA = (255, 255, 255, 255)

K = Kit(FRAME_SIZE, ink=INK)

# ---- The rig: frame pixels at full size, up is negative -----------------------

#: How high his pelvis stands over his feet.
PELVIS_UP = 33.0
#: Points of the body (from the pelvis, before the body turns).
NEAR_SHOULDER: Point = (12.0, -70.0)
FAR_SHOULDER: Point = (-12.0, -73.0)
NECK: Point = (14.0, -78.0)
NEAR_HIP: Point = (8.0, -8.0)
FAR_HIP: Point = (-12.0, -9.0)
#: The front of his tummy: where a blow knocks stuffing out of him.
TUMMY: Point = (34.0, -30.0)
#: Points of the head (from the neck, before the head turns).
HINGE: Point = (6.0, -10.0)
LIP_FRONT: Point = (41.0, -13.0)
MOUTH_CORNER: Point = (35.0, -11.5)
HEAD_MIDDLE: Point = (8.0, -26.0)
#: Limb lengths: thigh, shin; upper arm, forearm.
THIGH, SHIN = 18.0, 19.0
UPPER_ARM, FOREARM = 30.0, 28.0
#: The head is drawn this much larger than the body's unit: a nursery bear's
#: head is big.
HEAD_SCALE = 1.15
#: How far each jaw opens, in degrees.
JAW_OPEN = 40.0


def _r(v: float, step: float = 0.5) -> float:
    """``v`` on a grid: a piece painted for one pose is the piece of every pose
    that rounds the same."""
    return round(v / step) * step


# ---- Painting helpers -----------------------------------------------------------


def _P(k: float, x: float, y: float) -> Point:
    return K.at(x * k, y * k)


def _limb(d, pts: Sequence[Point], widths: Sequence[float], fill: RGBA) -> None:
    """A tapered tube through ``pts`` (scratch points), ``widths`` wide at each."""
    for (a, wa), (b, wb) in zip(zip(pts, widths), zip(pts[1:], widths[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n
        quad = [
            (a[0] + nx * wa / 2, a[1] + ny * wa / 2),
            (b[0] + nx * wb / 2, b[1] + ny * wb / 2),
            (b[0] - nx * wb / 2, b[1] - ny * wb / 2),
            (a[0] - nx * wa / 2, a[1] - ny * wa / 2),
        ]
        K.poly(d, quad, fill)
    for p, w in zip(pts, widths):
        K.oval(d, p, w / 2, w / 2, fill)


def _claws(d, paw: Point, toward: float, length: float, k: float, fill: RGBA, spread: float = 22.0, curl: float = 1.0) -> None:
    """Four hooked claws out of the paw at ``paw``, pointing ``toward`` degrees."""
    for i in range(4):
        a = math.radians(toward + spread * (i - 1.5))
        base = (paw[0] + math.cos(a) * 8.0 * k, paw[1] + math.sin(a) * 8.0 * k)
        tip_a = a + math.radians(18.0 * curl)
        tip = (base[0] + math.cos(tip_a) * length * k, base[1] + math.sin(tip_a) * length * k)
        nx, ny = -math.sin(a), math.cos(a)
        w = 2.0 * k
        K.poly(d, [(base[0] + nx * w, base[1] + ny * w), tip, (base[0] - nx * w, base[1] - ny * w)], fill)


# ---- Pieces ---------------------------------------------------------------------


def _leg_piece(foot: Point, k: float, far: bool):
    """A leg from the hip (the anchor) to the sole; ``foot`` from the hip."""
    foot = (_r(foot[0]), _r(foot[1]))
    knee, ankle = solve((0.0, 0.0), foot, THIGH * k, SHIN * k, -1.0)
    fill = FUR_FAR if far else FUR

    def pts():
        hip = K.at(0.0, 0.0)
        return hip, K.at(*knee), K.at(*ankle)

    def shape(d) -> None:
        hip, kn, an = pts()
        _limb(d, [hip, kn, an], [26.0 * k, 21.0 * k, 18.0 * k], WHITE)
        # The hind paw: a flat round foot that points forward.
        K.oval(d, (an[0] + 5.0 * k, an[1] + 3.5 * k), 12.0 * k, 6.0 * k, WHITE)

    def detail(d) -> None:
        hip, kn, an = pts()
        # The pad of the sole, seen from the side.
        K.oval(d, (an[0] + 5.0 * k, an[1] + 8.0 * k), 11.0 * k, 2.6 * k, mix(fill, INK, 0.45))

    return K.solid(("leg", foot, k, far), shape, fill, detail, outline=1.4, shade=0.45, shade_colour=FUR_SHADE)


def _arm_piece(hand: Point, k: float, far: bool, claw: float):
    """An arm from the shoulder (the anchor) to the paw; ``hand`` from the
    shoulder. ``claw`` is how far the claws are out, 0 to 1."""
    hand = (_r(hand[0]), _r(hand[1]))
    claw = _r(claw, 0.25)
    elbow, wrist = solve((0.0, 0.0), hand, UPPER_ARM * k, FOREARM * k, 1.0)
    toward = angle(elbow, wrist)
    fill = FUR_FAR if far else FUR
    claw_len = lerp(5.0, 12.0, claw)

    def shape(d) -> None:
        sh, el, wr = K.at(0.0, 0.0), K.at(*elbow), K.at(*wrist)
        _limb(d, [sh, el, wr], [22.0 * k, 17.0 * k, 15.0 * k], WHITE)
        K.oval(d, wr, 10.5 * k, 10.5 * k, WHITE)
        _claws(d, wr, toward, claw_len, k, WHITE, curl=1.0)

    def detail(d) -> None:
        wr = K.at(*wrist)
        _claws(d, wr, toward, claw_len - 1.2, k, mix(CLAW, FUR_SHADE, 0.35) if far else CLAW, curl=1.0)

    return K.solid(("arm", hand, k, far, claw), shape, fill, detail, outline=1.4, shade=0.45, shade_colour=FUR_SHADE)


def _bristle(d, k: float, pts: Sequence[Point], length: float, normal_sign: float = 1.0) -> None:
    """Spikes of fur standing up along the edge through ``pts`` (scratch
    points): the outward side is the left of the way the edge runs."""
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        nx, ny = dy / n * normal_sign, -dx / n * normal_sign
        mid = ((a[0] + b[0]) / 2 + nx * length * k, (a[1] + b[1]) / 2 + ny * length * k)
        K.poly(d, [(a[0] - nx * 3.0 * k, a[1] - ny * 3.0 * k), mid, (b[0] - nx * 3.0 * k, b[1] - ny * 3.0 * k)], WHITE)


def _arc(k: float, c: Point, rx: float, ry: float, a0: float, a1: float, steps: int) -> List[Point]:
    """Points along an ellipse about ``c`` (body units) from ``a0`` to ``a1`` degrees."""
    out = []
    for i in range(steps + 1):
        a = math.radians(lerp(a0, a1, i / steps))
        out.append(_P(k, c[0] + math.cos(a) * rx, c[1] + math.sin(a) * ry))
    return out


def _body_piece(k: float, horror: float):
    """The body from the pelvis (the anchor): belly, chest, shoulders. With
    ``horror`` his back bristles."""
    horror = _r(horror, 0.25)

    def shape(d) -> None:
        P = lambda x, y: _P(k, x, y)
        K.oval(d, P(12.0, -31.0), 38.0 * k, 32.0 * k, WHITE)
        K.oval(d, P(-10.0, -29.0), 22.0 * k, 24.0 * k, WHITE)
        K.oval(d, P(0.0, -58.0), 31.0 * k, 25.0 * k, WHITE)
        K.oval(d, P(-2.0, -73.0), 23.0 * k, 12.0 * k, WHITE)
        if horror > 0.0:
            # Up the back from the rump to the shoulders.
            _bristle(d, k, _arc(k, (-4.0, -50.0), 30.0, 30.0, 150.0, 268.0, 9), 9.0 * horror, 1.0)

    def detail(d) -> None:
        P = lambda x, y: _P(k, x, y)
        # The tummy of a teddy bear: a lighter patch.
        K.oval(d, P(20.0, -32.0), 25.0 * k, 26.0 * k, mix(FUR, WHITE, 0.2))
        # Honey has run down his chest and dried.
        K.stroke(d, [P(28.0, -66.0), P(30.0, -58.0), P(29.0, -50.0)], mix(FUR, HONEY, 0.6), 3.6 * k)
        K.line(d, [P(28.8, -64.0), P(29.8, -58.0)], mix(HONEY_LIGHT, WHITE, 0.3), 1.0 * k)

    return K.solid(("body", k, horror), shape, FUR, detail, outline=1.5, rim=0.42, shade=0.5, shade_colour=FUR_SHADE)


def _jaw_points(open_: float) -> List[Point]:
    """The lower jaw from the neck, closed, then turned about the hinge."""
    closed = [HINGE, (40.0, -11.0), (37.0, -4.0), (22.0, 0.0), (6.0, -3.0)]
    a = JAW_OPEN * open_
    return [(HINGE[0] + q[0], HINGE[1] + q[1]) for q in (turned((p[0] - HINGE[0], p[1] - HINGE[1]), a) for p in closed)]


def _head_piece(k: float, jaw: float, eyes: str, horror: float):
    """The head from the neck (the anchor). ``jaw`` opens his mouth (0 to 1);
    ``eyes`` is ``bead``, ``glow``, ``shut`` or ``x``; ``horror`` (0 to 1)
    takes the sweet face to the monster's."""
    jaw = _r(jaw, 0.125)
    horror = _r(horror, 0.25)
    jp = _jaw_points(jaw)

    def P(x: float, y: float) -> Point:
        return _P(k, x, y)

    def shape(d) -> None:
        K.oval(d, P(4.0, -26.0), 26.0 * k, 24.0 * k, WHITE)
        K.oval(d, P(12.0, -14.0), 20.0 * k, 11.0 * k, WHITE)
        K.oval(d, P(30.0, -19.0), 13.5 * k, 9.5 * k, WHITE)
        K.oval(d, P(-8.0, -45.0), 9.5 * k, 9.5 * k, WHITE)
        K.oval(d, P(14.0, -48.0), 9.0 * k, 9.0 * k, WHITE)
        K.poly(d, [P(*p) for p in jp], WHITE)
        if jaw > 0.0:
            K.poly(d, [P(*HINGE), P(*LIP_FRONT), P(*jp[1]), P(*jp[4])], WHITE)
        if horror > 0.0:
            # Over the crown and down the back of the head, between the ears.
            _bristle(d, k, _arc(k, (4.0, -26.0), 25.0, 23.0, 110.0, 215.0, 6), 7.0 * horror, 1.0)
            _bristle(d, k, _arc(k, (4.0, -26.0), 25.0, 23.0, 252.0, 262.0, 1), 6.0 * horror, 1.0)
            # Hackles under the jaw.
            _bristle(d, k, [P(2.0, -2.0), P(10.0, 0.0), P(18.0, 0.5)], 4.0 * horror, -1.0)

    def detail(d) -> None:
        # Inner ears.
        K.oval(d, P(-8.0, -45.0), 5.0 * k, 5.0 * k, EAR_INNER)
        K.oval(d, P(14.0, -48.0), 4.6 * k, 4.6 * k, EAR_INNER)
        # The muzzle is a shade lighter, worn by handling.
        K.oval(d, P(31.0, -17.0), 11.0 * k, 7.0 * k, mix(FUR, WHITE, 0.2))
        if jaw > 0.0 and horror < 0.5:
            # A teddy bear talking: a small open mouth and a tongue.
            K.poly(d, [P(*HINGE), P(*LIP_FRONT), P(*jp[1]), P(*jp[0])], MOUTH)
            K.poly(d, [P(*p) for p in jp], FUR)
            K.oval(d, P(lerp(jp[0][0], jp[1][0], 0.7), lerp(jp[0][1], jp[1][1], 0.7) - 0.6), 5.0 * k, 2.0 * k, TONGUE)
            K.line(d, [P(*jp[0]), P(*jp[1])], mix(FUR, WHITE, 0.2), 1.2 * k)
        elif jaw > 0.0:
            K.poly(d, [P(*HINGE), P(*LIP_FRONT), P(*jp[1]), P(*jp[0])], MOUTH)
            K.poly(d, [P(*p) for p in jp], FUR)
            K.line(d, [P(*jp[0]), P(*jp[1])], GUM, 2.2 * k)
            K.line(d, [P(*HINGE), P(*LIP_FRONT)], GUM, 2.2 * k)
            # Too many teeth, none of them the same.
            for i in range(9):
                t = (i + 0.5) / 9.0
                x = lerp(HINGE[0] + 3.0, LIP_FRONT[0] - 1.0, t)
                y = lerp(HINGE[1], LIP_FRONT[1], t)
                h = (3.0 + 2.2 * ((i * 7) % 3)) * min(1.0, jaw * 2.0)
                K.poly(d, [P(x - 1.7, y), P(x + 1.7, y), P(x + 0.3, y + h)], TOOTH, INK, 0.5 * k)
            for i in range(7):
                t = (i + 0.5) / 7.0
                x = lerp(jp[0][0] + 4.0, jp[1][0] - 1.0, t)
                y = lerp(jp[0][1], jp[1][1], t)
                h = (2.6 + 2.0 * ((i * 5) % 3)) * min(1.0, jaw * 2.0)
                K.poly(d, [P(x - 1.6, y), P(x + 1.6, y), P(x - 0.2, y - h)], TOOTH, INK, 0.5 * k)
            # Honey strings between the jaws.
            if jaw >= 0.375:
                for t, sag in ((0.38, 2.5), (0.7, 1.6)):
                    top = (lerp(HINGE[0], LIP_FRONT[0], t), lerp(HINGE[1], LIP_FRONT[1], t) + 2.0)
                    bot = (lerp(jp[0][0], jp[1][0], t), lerp(jp[0][1], jp[1][1], t) - 2.0)
                    mid = ((top[0] + bot[0]) / 2 + sag, (top[1] + bot[1]) / 2)
                    K.line(d, [P(*top), P(*mid), P(*bot)], HONEY, 1.1 * k)
        elif horror >= 0.5:
            # The smile has grown back to his cheek.
            smile = [P(8.0, -10.5), P(18.0, -7.5), P(30.0, -8.5), P(40.0, -13.0)]
            K.line(d, smile, INK, 1.4 * k)
        else:
            # The embroidered smile of a teddy bear: a line down from the nose,
            # a small curve.
            K.line(d, [P(40.5, -19.5), P(39.0, -14.0)], INK, 1.1 * k)
            K.line(d, [P(31.0, -14.5), P(35.0, -12.0), P(39.0, -14.0), P(42.0, -13.0)], INK, 1.2 * k)
        # The nose.
        K.poly(d, [P(37.0, -27.0), P(46.0, -26.0), P(45.5, -20.5), P(40.5, -18.5), P(36.5, -22.0)], NOSE)
        K.oval(d, P(42.0, -25.2), 1.6 * k, 0.9 * k, (120, 100, 100, 255))
        # The eyes: the near one, and the far one over the bridge of the snout.
        for (ex, ey), size in (((15.0, -30.0), 1.0), ((32.0, -31.5), 0.7)):
            c = P(ex, ey)
            if horror > 0.0:
                K.oval(d, c, 6.2 * k * size, 5.4 * k * size, mix(FUR, FUR_SHADE, 0.6 * horror))
            if eyes == "glow":
                K.oval(d, c, 3.6 * k * size, 3.8 * k * size, GLOW)
                K.oval(d, c, 1.8 * k * size, 2.0 * k * size, GLOW_CORE)
                K.line(d, [(c[0], c[1] - 2.2 * k * size), (c[0], c[1] + 2.2 * k * size)], BEAD, 0.9 * k * size)
            elif eyes == "shut":
                K.line(d, [(c[0] - 3.2 * k * size, c[1]), (c[0], c[1] + 1.4 * k * size), (c[0] + 3.2 * k * size, c[1])], BEAD, 1.2 * k)
            elif eyes == "dizzy":
                pts = []
                for j in range(14):
                    a = j * 0.9
                    rr = (0.4 + j * 0.24) * k * size
                    pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
                K.line(d, pts, BEAD, 0.9 * k)
            elif eyes == "x":
                r = 2.6 * k * size
                K.line(d, [(c[0] - r, c[1] - r), (c[0] + r, c[1] + r)], THREAD, 1.1 * k)
                K.line(d, [(c[0] - r, c[1] + r), (c[0] + r, c[1] - r)], THREAD, 1.1 * k)
            else:
                # Big shiny bead eyes.
                K.oval(d, c, 3.8 * k * size, 4.6 * k * size, BEAD)
                K.oval(d, (c[0] + 1.1 * k * size, c[1] - 1.6 * k * size), 1.3 * k * size, 1.4 * k * size, WHITE)
                K.oval(d, (c[0] - 1.2 * k * size, c[1] + 1.8 * k * size), 0.6 * k * size, 0.6 * k * size, WHITE)
        if horror > 0.0:
            # A heavy brow that comes down toward the snout.
            brow_in = lerp(-38.0, -33.0, horror)
            K.line(d, [P(8.0, -38.5), P(15.0, -39.0), P(23.0, brow_in)], FUR_SHADE, 1.8 * k)
        else:
            # A soft, raised brow.
            K.line(d, [P(10.0, -38.0), P(15.0, -39.5), P(20.0, -38.6)], mix(FUR, FUR_SHADE, 0.5), 1.0 * k)

    return K.solid(("head", k, jaw, eyes, horror), shape, FUR, detail, outline=1.5, rim=0.42, shade=0.42, shade_colour=FUR_SHADE)


def _drip_piece(k: float, length: float, drop: float):
    """Honey hanging from the corner of his mouth: a string ``length`` long
    with a drop at its end. The anchor is where it hangs from."""
    length, drop = _r(length), _r(drop, 0.25)

    def shape(d) -> None:
        a, b = K.at(0.0, 0.0), K.at(0.3 * k, length * k)
        _limb(d, [a, b], [2.4 * k, 1.4 * k], WHITE)
        K.oval(d, (b[0], b[1] + drop * k), drop * k, (drop + 0.6) * k, WHITE)

    return K.solid(("drip", k, length, drop), shape, HONEY, None, outline=0.9, rim=0.6, shade=0.3, shade_colour=(176, 96, 10, 255))


def _bee_piece(wing: int):
    """A honey bee, facing the way it flies (right); ``wing`` up or down."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, 0.0), 6.0, 4.4, WHITE)
        K.oval(d, K.at(-1.4, -4.6 if wing else -2.8), 3.4, 2.4 if wing else 1.4, WHITE)

    def detail(d) -> None:
        K.oval(d, K.at(-1.4, -4.6 if wing else -2.8), 3.4, 2.4 if wing else 1.4, (236, 244, 255, 255))
        for x in (-2.4, 1.2):
            K.line(d, [K.at(x, -3.8), K.at(x, 3.8)], BEAD, 1.5)
        K.oval(d, K.at(4.4, -0.6), 1.0, 1.0, BEAD)

    return K.solid(("bee", wing), shape, (250, 206, 52, 255), detail, outline=0.8, rim=0.4, shade=0.3, shade_colour=(176, 120, 20, 255))


def _tuft_piece(k: float, r: float):
    def shape(d) -> None:
        for dx, dy, rr in ((0.0, 0.0, 1.0), (1.2, -0.8, 0.7), (-1.0, 0.7, 0.75)):
            K.oval(d, K.at(dx * r * k, dy * r * k), rr * r * k, rr * r * k, WHITE)

    return K.solid(("tuft", k, r), shape, STUFFING, None, outline=0.8, rim=0.3, shade=0.4, shade_colour=STUFFING_SHADE)


# ---- Poses ------------------------------------------------------------------------

REST: Pose = {
    "root": (0.0, 0.0),
    "lean": 6.0,
    "head": 0.0,
    "jaw": 0.0,
    "eyes": "bead",
    "near_hand": (18.0, 52.0),
    "far_hand": (4.0, 50.0),
    "near_foot": (8.0, 0.0),
    "far_foot": (-12.0, 0.0),
    "ground": 0.0,
    "claw": 0.0,
    "horror": 0.0,
    "k": 1.0,
}


def P(**kw) -> Pose:
    """REST with ``kw``. Glowing eyes are the monster's: full ``horror``
    unless the pose says otherwise."""
    out = dict(REST)
    if kw.get("eyes") == "glow":
        out["horror"] = 1.0
    out.update(kw)
    return out


def _pose(anim: str, i: int, n: int) -> Tuple[Pose, dict]:
    """The pose of frame ``i`` of ``n`` of a row, and its effects: ``drip``
    (0 to 1 through a drip's fall, or ``None``) and ``tufts`` (stuffing
    knocked out of him, ``(x, y, r)`` from his tummy)."""
    loop = i / n
    u = i / max(1, n - 1)
    fx: dict = {"drip": None, "tufts": ()}
    if anim == "idle":
        s = math.sin(math.tau * loop)
        tilt = 0.5 - 0.5 * math.cos(math.tau * loop)
        fx["drip"] = loop
        return P(root=(0.0, 1.2 * s), lean=6.0 + 1.0 * s, head=-2.0 + 9.0 * tilt,
                 near_hand=(18.0 + 1.5 * s, 52.0 + 1.0 * s), far_hand=(4.0 - 1.0 * s, 50.0)), fx
    if anim == "walk":
        p = math.tau * loop
        s, c = math.sin(p), math.cos(p)
        stride = 15.0
        fx["drip"] = (loop * 2.0) % 1.0
        return P(
            root=(0.0, -2.5 * abs(c)),
            lean=10.0 + 1.5 * math.sin(2 * p),
            head=-1.5 * math.sin(2 * p),
            near_foot=(8.0 + stride * s, -7.0 * max(0.0, c)),
            far_foot=(-12.0 - stride * s, -7.0 * max(0.0, -c)),
            near_hand=(14.0 - 16.0 * s, 48.0 - 4.0 * abs(s)),
            far_hand=(4.0 + 16.0 * s, 48.0 - 4.0 * abs(s)),
        ), fx
    if anim == "slash":
        wind = P(lean=-4.0, head=-6.0, jaw=0.25, eyes="glow", near_hand=(-34.0, -30.0), far_hand=(10.0, 40.0), claw=1.0,
                 root=(-3.0, 0.0), far_foot=(-16.0, 0.0))
        strike = P(lean=20.0, head=6.0, jaw=1.0, eyes="glow", near_hand=(58.0, 12.0), far_hand=(-14.0, 40.0), claw=1.0,
                   root=(7.0, 1.0), near_foot=(20.0, 0.0))
        follow = P(lean=18.0, head=4.0, jaw=0.75, eyes="glow", near_hand=(40.0, 46.0), far_hand=(-10.0, 44.0), claw=1.0,
                   root=(6.0, 1.0), near_foot=(20.0, 0.0))
        return keys(u, [(0.0, REST), (0.3, wind), (0.5, strike), (0.68, follow),
                        (1.0, P(near_foot=(14.0, 0.0), root=(3.0, 0.0)))]), fx
    if anim == "punch":
        rear = P(root=(-2.0, -5.0), lean=-12.0, head=-12.0, jaw=0.5, eyes="glow", near_hand=(14.0, -54.0), far_hand=(-4.0, -56.0), claw=1.0)
        down = P(root=(8.0, 2.0), lean=26.0, head=8.0, jaw=1.0, eyes="glow", near_hand=(54.0, 30.0), far_hand=(42.0, 34.0), claw=1.0,
                 near_foot=(22.0, 0.0))
        lift = P(root=(8.0, 0.0), lean=18.0, head=0.0, jaw=0.75, eyes="glow", near_hand=(44.0, -12.0), far_hand=(34.0, -6.0), claw=1.0,
                 near_foot=(22.0, 0.0))
        again = P(root=(12.0, 2.0), lean=28.0, head=8.0, jaw=1.0, eyes="glow", near_hand=(58.0, 34.0), far_hand=(48.0, 38.0), claw=1.0,
                  near_foot=(26.0, 0.0))
        return keys(u, [(0.0, REST), (0.22, rear), (0.4, down), (0.55, lift), (0.7, again),
                        (1.0, P(root=(6.0, 0.0), near_foot=(20.0, 0.0)))]), fx
    if anim == "special":
        up = P(root=(0.0, -7.0), lean=-8.0, head=-14.0, jaw=0.5, eyes="glow", near_hand=(10.0, -58.0), far_hand=(-6.0, -58.0), claw=0.5,
               near_foot=(10.0, -2.0), far_foot=(-14.0, -2.0))
        slam = P(root=(6.0, 9.0), lean=40.0, head=14.0, jaw=1.0, eyes="glow", near_hand=(30.0, 60.0), far_hand=(18.0, 60.0), ground=1.0,
                 claw=0.5, near_foot=(14.0, 0.0), far_foot=(-18.0, 0.0))
        return keys(u, [(0.0, REST), (0.3, up), (0.55, slam), (0.8, slam),
                        (1.0, P(root=(3.0, 0.0)))]), fx
    if anim == "taunt":
        # He is getting angry: the smile grows and the brow comes down while
        # his eyes are still the sweet ones.
        breathe = P(root=(-2.0, -2.0), lean=-6.0, head=-14.0, jaw=0.0, horror=0.5, near_hand=(40.0, -14.0), far_hand=(-30.0, -18.0),
                    claw=0.5)
        roar = P(root=(-2.0, -3.0), lean=-10.0, head=-24.0, jaw=1.0, eyes="glow", near_hand=(46.0, -24.0), far_hand=(-36.0, -26.0),
                 claw=1.0)
        pose = keys(u, [(0.0, REST), (0.25, breathe), (0.4, roar), (0.8, roar), (1.0, REST)])
        if 0.4 <= u <= 0.8:
            shake = 2.0 if i % 2 else -2.0
            pose = dict(pose, head=float(pose["head"]) + shake)
        return pose, fx
    if anim == "hurt":
        hit = P(root=(-7.0, 0.0), lean=-14.0, head=-16.0, jaw=0.25, eyes="shut", near_hand=(34.0, 18.0), far_hand=(-30.0, 16.0),
                near_foot=(4.0, 0.0), far_foot=(-18.0, 0.0))
        pose = keys(u, [(0.0, hit), (0.34, hit), (1.0, REST)])
        fx["tufts"] = tuple((6.0 + 10.0 * j * (1 + i), -4.0 - 8.0 * j * (1 + i) + 3.0 * i * i, 2.6 - 0.4 * i)
                            for j in (0.5, 1.0) if i < 3)
        return pose, fx
    if anim == "death":
        hit = P(root=(-7.0, 0.0), lean=-14.0, head=-16.0, jaw=0.25, eyes="shut", near_hand=(34.0, 18.0), far_hand=(-30.0, 16.0),
                near_foot=(4.0, 0.0), far_foot=(-18.0, 0.0))
        totter = P(root=(-12.0, 4.0), lean=-18.0, head=-8.0, jaw=0.0, eyes="shut", near_hand=(26.0, 30.0), far_hand=(-24.0, 30.0),
                   near_foot=(2.0, 0.0), far_foot=(-20.0, 0.0))
        sit = P(root=(-10.0, 22.0), lean=-8.0, head=18.0, jaw=0.0, eyes="x", near_hand=(18.0, 44.0), far_hand=(-12.0, 44.0),
                near_foot=(34.0, 0.0), far_foot=(24.0, 0.0))
        limp = P(root=(-10.0, 22.0), lean=-4.0, head=30.0, jaw=0.0, eyes="x", near_hand=(16.0, 46.0), far_hand=(-12.0, 46.0),
                 near_foot=(36.0, 0.0), far_foot=(26.0, 0.0), k=0.72)
        pose = keys(u, [(0.0, hit), (0.2, totter), (0.5, sit), (0.7, sit), (1.0, limp)])
        if i in (4, 5, 6):
            fx["tufts"] = tuple((10.0 + 6.0 * (i - 3) * j, -14.0 - 7.0 * (i - 3) * j, 2.6) for j in (0.6, 1.2))
        return pose, fx
    if anim == "hug":
        # The tell is the bait: arms wide for a hug, the smile wider than it
        # should be. Then the arms close on whoever came near.
        wide = P(lean=0.0, head=-4.0, horror=0.5, near_hand=(42.0, -18.0), far_hand=(-34.0, -22.0), claw=0.5)
        close = P(lean=16.0, head=6.0, horror=1.0, jaw=0.5, eyes="glow", near_hand=(40.0, 10.0), far_hand=(30.0, 8.0),
                  claw=1.0, root=(6.0, 0.0), near_foot=(16.0, 0.0))
        return keys(u, [(0.0, P(horror=0.5)), (0.3, wide), (0.45, wide), (0.8, close), (1.0, close)]), fx
    if anim == "squeeze":
        shake = 1.0 if i % 2 else -1.0
        return P(lean=10.0 + 2.0 * shake, head=6.0 + 4.0 * shake, horror=1.0, jaw=0.75 + 0.25 * (i % 2), eyes="glow",
                 near_hand=(34.0, 8.0 + shake), far_hand=(26.0, 6.0 - shake), claw=1.0, root=(6.0, 0.0),
                 near_foot=(16.0, 0.0)), fx
    if anim == "throw":
        hold = P(lean=10.0, head=6.0, horror=1.0, jaw=1.0, eyes="glow", near_hand=(34.0, 8.0), far_hand=(26.0, 6.0), claw=1.0,
                 root=(6.0, 0.0), near_foot=(16.0, 0.0))
        fling = P(lean=-8.0, head=-10.0, horror=1.0, jaw=1.0, eyes="glow", near_hand=(44.0, -44.0), far_hand=(34.0, -48.0),
                  claw=1.0, root=(2.0, -3.0), near_foot=(16.0, 0.0))
        return keys(u, [(0.0, hold), (0.35, fling), (1.0, P(root=(2.0, 0.0)))]), fx
    if anim == "spit":
        # The tell: his tummy rumbles and his cheeks fill. Then he spits
        # honey (the glob is the projectile's own picture).
        fill = P(lean=-4.0, head=-16.0, horror=0.5, near_hand=(10.0, 40.0), far_hand=(0.0, 42.0), root=(-2.0, 0.0))
        spit = P(lean=14.0, head=10.0, horror=1.0, jaw=1.0, eyes="glow", near_hand=(18.0, 46.0), far_hand=(6.0, 46.0),
                 root=(4.0, 0.0))
        return keys(u, [(0.0, REST), (0.4, fill), (0.6, spit), (1.0, spit)]), fx
    if anim == "run":
        # On all fours, the way a bear charges.
        p = math.tau * loop
        s, c = math.sin(p), math.cos(p)
        return P(root=(10.0, -4.0 - 3.0 * abs(c)), lean=62.0 + 3.0 * s, head=-48.0 - 3.0 * s, horror=1.0, jaw=0.75, eyes="glow",
                 claw=1.0, ground=1.0, near_hand=(26.0 + 14.0 * s, 60.0), far_hand=(16.0 - 14.0 * s, 60.0),
                 near_foot=(-6.0 - 14.0 * s, -6.0 * max(0.0, c)), far_foot=(-20.0 + 14.0 * s, -6.0 * max(0.0, -c))), fx
    if anim == "flop":
        crouch = P(root=(-2.0, 6.0), lean=-6.0, head=-10.0, horror=1.0, jaw=0.5, eyes="glow", near_hand=(30.0, -30.0),
                   far_hand=(20.0, -34.0), claw=1.0)
        fly = P(root=(10.0, -26.0), lean=40.0, head=-20.0, horror=1.0, jaw=1.0, eyes="glow", near_hand=(50.0, -10.0),
                far_hand=(40.0, -14.0), claw=1.0, near_foot=(-12.0, -20.0), far_foot=(-26.0, -16.0))
        land = P(root=(18.0, -9.0), lean=72.0, head=-52.0, horror=1.0, jaw=0.75, eyes="glow", near_hand=(40.0, 60.0),
                 far_hand=(26.0, 60.0), ground=1.0, claw=1.0, near_foot=(-14.0, 0.0), far_foot=(-28.0, 0.0))
        return keys(u, [(0.0, crouch), (0.14, crouch), (0.5, fly), (0.72, land), (1.0, land)]), fx
    if anim == "stunned":
        # Dazed, sitting, sweet again: honey bees circle his head.
        wobble = math.sin(math.tau * loop)
        bees = []
        for j in range(3):
            a = math.tau * (loop + j / 3.0)
            bees.append((math.cos(a) * 30.0, math.sin(a) * 7.0, (i + j) % 2))
        fx["bees"] = tuple(bees)
        return P(root=(-10.0, 22.0), lean=-6.0 + 2.0 * wobble, head=10.0 + 6.0 * wobble, eyes="dizzy", jaw=0.125,
                 near_hand=(18.0, 44.0), far_hand=(-12.0, 44.0), near_foot=(34.0, 0.0), far_foot=(24.0, 0.0)), fx
    raise KeyError(anim)


# ---- Frames ------------------------------------------------------------------------


def _world(p: Point) -> Point:
    return (CX + p[0], GROUND + p[1])


def _layout(pose: Pose) -> dict:
    """Where each piece goes in the frame, and how it is turned."""
    k = float(pose["k"])
    rx, ry = pose["root"]  # type: ignore[misc]
    lean = float(pose["lean"])
    pelvis = (rx * k, (-PELVIS_UP + ry) * k)

    def on_body(p: Point) -> Point:
        q = turned((p[0] * k, p[1] * k), lean)
        return (pelvis[0] + q[0], pelvis[1] + q[1])

    neck = on_body(NECK)
    head_turn = lean * 0.5 + float(pose["head"])
    near_sh, far_sh = on_body(NEAR_SHOULDER), on_body(FAR_SHOULDER)

    def hand(shoulder: Point, off: Point) -> Point:
        target = (off[0] * k, off[1] * k)
        g = float(pose["ground"])
        if g > 0.0:
            reach = (shoulder[0] + target[0], lerp(shoulder[1] + target[1], -13.0 * k, g))
            target = (reach[0] - shoulder[0], reach[1] - shoulder[1])
        return target

    def foot(hip: Point, at: Point) -> Point:
        sole = (at[0] * k, at[1] * k - 11.0 * k)
        return (sole[0] - hip[0], sole[1] - hip[1])

    near_hip, far_hip = on_body(NEAR_HIP), on_body(FAR_HIP)
    hk = k * HEAD_SCALE
    hq = turned((MOUTH_CORNER[0] * hk, MOUTH_CORNER[1] * hk), head_turn)
    return {
        "k": k,
        "pelvis": pelvis,
        "lean": lean,
        "neck": neck,
        "head_turn": head_turn,
        "near_shoulder": near_sh,
        "far_shoulder": far_sh,
        "near_hand": hand(near_sh, pose["near_hand"]),  # type: ignore[arg-type]
        "far_hand": hand(far_sh, pose["far_hand"]),  # type: ignore[arg-type]
        "near_hip": near_hip,
        "far_hip": far_hip,
        "near_foot": foot(near_hip, pose["near_foot"]),  # type: ignore[arg-type]
        "far_foot": foot(far_hip, pose["far_foot"]),  # type: ignore[arg-type]
        "mouth_corner": (neck[0] + hq[0], neck[1] + hq[1]),
        "tummy": on_body(TUMMY),
    }


def _paint(img: Image.Image, pose: Pose, fx: dict) -> None:
    at = _layout(pose)
    k = at["k"]
    claw = float(pose["claw"])
    K.place(img, _arm_piece(at["far_hand"], k, True, claw), _world(at["far_shoulder"]), "far_arm")
    K.place(img, _leg_piece(at["far_foot"], k, True), _world(at["far_hip"]), "far_leg")
    horror = float(pose["horror"])
    K.place(img, _body_piece(k, horror), _world(at["pelvis"]), "body", at["lean"])
    K.place(img, _leg_piece(at["near_foot"], k, False), _world(at["near_hip"]), "near_leg")
    K.place(img, _head_piece(k * HEAD_SCALE, float(pose["jaw"]), str(pose["eyes"]), horror), _world(at["neck"]), "head", at["head_turn"])
    drip = fx.get("drip")
    if drip is not None and float(pose["jaw"]) == 0.0:
        length = 4.0 + 14.0 * drip
        K.place(img, _drip_piece(k, length, 1.4 + 1.2 * drip), _world(at["mouth_corner"]), "drip")
    for n, (x, y, wing) in enumerate(fx.get("bees", ())):
        top = (at["neck"][0], at["neck"][1] - 60.0 * k)
        K.place(img, _bee_piece(wing), _world((top[0] + x * k, top[1] + y * k)), f"bee{n}")
    for n, (x, y, r) in enumerate(fx.get("tufts", ())):
        K.place(img, _tuft_piece(k, r), _world((at["tummy"][0] + x * k, at["tummy"][1] + y * k)), f"tuft{n}")
    K.place(img, _arm_piece(at["near_hand"], k, False, claw), _world(at["near_shoulder"]), "near_arm")


def render_pose(pose: Pose, fx: Optional[dict] = None) -> Image.Image:
    """``pose`` before it is reduced: ``K.scale`` times the frame size."""
    img = K.new_frame()
    _paint(img, pose, fx or {})
    return img


def render_source(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    """A frame of a row before it is reduced."""
    return render_pose(*_pose(anim, frame_idx, nframes))


def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    return K.downsample(render_source(anim, frame_idx, nframes))


# ---- The contract the game reads --------------------------------------------------


def _event(t: float, name: str) -> dict:
    return {"t": t, "event": name, "source": TARGET_NAME}


ACTOR_METADATA = {
    "actor": {"character_id": "npc_hunny_horror_boss", "display_name": "Hunny Horror"},
    "visual": {"default_pose": "idle"},
    "body": {
        "body_plan": "BossBrute",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "traits": ["boss", "bear", "horror", "honey", "monster"],
        "locomotion_hint": "Lumber",
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": None, "climb": None, "fly": None},
        "interactions": {"talk": None, "trade": None, "carry": None},
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "aggressive"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [_event(0.3, "telegraph_peak"), _event(0.45, "hitbox_active_start"), _event(0.68, "hitbox_active_end")],
        },
        "action.melee.heavy": {
            "animation": "punch",
            "events": [
                _event(0.22, "telegraph_peak"),
                _event(0.34, "hitbox_active_start"),
                _event(0.46, "hitbox_active_end"),
                _event(0.64, "hitbox_active_start"),
                _event(0.76, "hitbox_active_end"),
            ],
        },
        "action.special.primary": {
            "animation": "special",
            "events": [_event(0.3, "telegraph_peak"), _event(0.55, "ground_impact")],
        },
        "action.special.roar": {
            "animation": "taunt",
            "events": [_event(0.25, "roar_charge_start"), _event(0.4, "roar_peak"), _event(0.8, "roar_release")],
        },
        "damage.hit": {"animation": "hurt", "events": []},
        "interaction.talk": {"animation": "idle", "events": []},
        "death": {"animation": "death", "events": []},
    },
    "tags": ["boss", "bear", "horror", "honey"],
    "authoring_description": (
        "Hunny Horror is a horror parody of the honey bear of the nursery: a stuffed bear the size "
        "of a door, sweet at rest. When he attacks or is angry his fur bristles, his eyes glow and "
        "his smile opens on too many teeth and honey."
    ),
    "gameplay_description": (
        "A boss driven by hunger. Honey, a rumbly-tummy tell, reaching paws and falsely comforting "
        "speech make childhood familiarity work against the player."
    ),
}


def _sockets() -> dict:
    at = _layout(REST)
    head = turned((HEAD_MIDDLE[0] * HEAD_SCALE, HEAD_MIDDLE[1] * HEAD_SCALE), at["head_turn"])
    mouth = turned((24.0 * HEAD_SCALE, -10.0 * HEAD_SCALE), at["head_turn"])

    def point(p: Point) -> dict:
        x, y = _world(p)
        return {"source": f"{TARGET_NAME}.geometry", "point": {"x": round(x, 1), "y": round(y, 1)}}

    near = (at["near_shoulder"][0] + at["near_hand"][0], at["near_shoulder"][1] + at["near_hand"][1])
    far = (at["far_shoulder"][0] + at["far_hand"][0], at["far_shoulder"][1] + at["far_hand"][1])
    return {
        "head": point((at["neck"][0] + head[0], at["neck"][1] + head[1])),
        "mouth": point((at["neck"][0] + mouth[0], at["neck"][1] + mouth[1])),
        "claw_near": point(near),
        "claw_far": point(far),
        "belly": point(at["tummy"]),
    }


ACTOR_METADATA["sockets"] = _sockets()


@lru_cache(maxsize=1)
def _body_box() -> Tuple[float, float, float, float]:
    """The body the game moves: the idle bear without the paws that hang
    in front of him, to the top of his ears."""
    pose, fx = _pose("idle", 0, 8)
    img = K.new_frame()
    at = _layout(pose)
    K.place(img, _leg_piece(at["far_foot"], 1.0, True), _world(at["far_hip"]), "far_leg")
    K.place(img, _body_piece(1.0, 0.0), _world(at["pelvis"]), "body", at["lean"])
    K.place(img, _leg_piece(at["near_foot"], 1.0, False), _world(at["near_hip"]), "near_leg")
    K.place(img, _head_piece(HEAD_SCALE, 0.0, "bead", 0.0), _world(at["neck"]), "head", at["head_turn"])
    x0, y0, x1, y1 = K.downsample(img).getchannel("A").point(lambda a: 255 if a > 128 else 0).getbbox()
    return (float(x0), float(y0), float(x1), float(GROUND))


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return K.render(TARGET_NAME, ROWS, render_frame, out_dir, ACTOR_METADATA, _body_box())


def render_portraits(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    at = _layout(REST)
    head = turned((HEAD_MIDDLE[0] * HEAD_SCALE, HEAD_MIDDLE[1] * HEAD_SCALE), at["head_turn"])
    cx, cy = _world((at["neck"][0] + head[0] + 6.0, at["neck"][1] + head[1]))
    face = FaceGuide(center_x=cx, center_y=cy, width=56.0, height=56.0,
                     source_width=float(FRAME_SIZE[0]), source_height=float(FRAME_SIZE[1]))

    def framed(source: Image.Image) -> Image.Image:
        return render_framed_portrait(source, face, view_width=96.0, center_y=cy + 12.0)

    def frame(anim: str, i: int, n: int) -> Image.Image:
        return framed(render_source(anim, i, n))

    def frames(anim: str, idx: Sequence[int], n: int) -> Tuple[Image.Image, ...]:
        return tuple(frame(anim, i, n) for i in idx)

    def face_of(**kw) -> Image.Image:
        return framed(render_pose(P(**kw)))

    sweet = face_of()
    monster = face_of(jaw=1.0, eyes="glow", claw=1.0, head=-6.0)
    # The beats of a conversation (`hall.yarn`), from the sweet bear to the
    # monster: `speaking` is sweet; `creepy` is the mask slipping (a wide
    # smile, a glimpse of teeth, the same sweet eyes); `snarl`, `evil_hold`
    # and `roar` are the monster; `evil_flash` cuts between the two.
    clips = {
        "default": PortraitClip.loop(frames("idle", range(8), 8), duration_ms=150),
        # The pose a UI box draws.
        "portrait": PortraitClip.still(frame("idle", 0, 8)),
        "speaking": PortraitClip(
            tuple(face_of(jaw=j, head=h) for j, h in ((0.0, 0.0), (0.25, 1.0), (0.125, 2.0), (0.25, 1.0))),
            duration_ms=130,
            looping=True,
        ),
        "creepy": PortraitClip(
            tuple(face_of(horror=0.5, jaw=j, head=h) for j, h in ((0.0, 6.0), (0.125, 7.0), (0.0, 8.0), (0.25, 7.0))),
            duration_ms=150,
            looping=True,
        ),
        "snarl": PortraitClip.still(face_of(horror=1.0, jaw=0.375, eyes="glow", head=4.0)),
        "evil_flash": PortraitClip((sweet, monster, sweet, sweet), duration_ms=95, looping=True),
        "evil_hold": PortraitClip.still(monster),
        "roar": PortraitClip(
            tuple(face_of(jaw=j, eyes="glow", claw=1.0, head=h) for j, h in ((0.75, -8.0), (1.0, -12.0), (1.0, -8.0), (1.0, -12.0))),
            duration_ms=100,
            looping=True,
        ),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir), still_clip="portrait")


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Hunny Horror spritesheet.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
