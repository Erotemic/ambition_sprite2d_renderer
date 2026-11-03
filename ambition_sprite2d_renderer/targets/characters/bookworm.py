"""The Bookworm: a fat green worm of the Story Stacks that eats books.

A fat green worm of round segments with a pale belly, a round head in
round gold spectacles, and a page of a book in its mouth that it chews.
The idiom made literal: it reads by eating.

It humps along as a caterpillar does: a wave goes from its tail to its
head. When it sees you it rears up and its spectacles flash, and the page
falls out of its mouth. Its windup pulls its head back with its mouth wide
open; its strike is a lunge and a chomp. A hit knocks its spectacles
crooked. At its death it hops, its spectacles fall off, and it lands on
its back with its legs in the air, and fades.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K

TARGET_NAME = "bookworm"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS
GROUND = 92.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Bookworm", "Serpentine", "Small", "Light", "Walk", ["worm", "book", "paper"],
    "A fat green worm in round spectacles from the Story Stacks of the Art dimension, that chews through a page. It "
    "humps along the shelves, rears up when it sees you, and lunges with a chomp.",
)

WORM: K.RGBA = (122, 188, 74, 255)
WORM_DARK: K.RGBA = (70, 128, 50, 255)
WORM_BELLY: K.RGBA = (204, 228, 128, 255)
GLASS: K.RGBA = (226, 246, 255, 255)
PARCHMENT: K.RGBA = (240, 226, 190, 255)

#: The segments from the tail to the neck: the radius of each.
RADII = (9.0, 11.5, 13.5, 14.5, 14.5)
SPACING = 8.5


def _spine(anim: str, cyc: float, stretch: float, bunch: float, hop: float) -> List[Tuple[float, float, float]]:
    """The segments (x, y, radius) from the tail to the neck."""
    out: List[Tuple[float, float, float]] = []
    gap = SPACING * (1.0 + stretch - bunch)
    tail_x = 14.0 + bunch * 18.0 - stretch * 4.0
    n = len(RADII)
    for j, r in enumerate(RADII):
        x = tail_x + j * gap
        lift = 0.0
        if anim == "walk":
            # A hump that travels from the tail to the head.
            lift = 7.0 * max(0.0, math.sin(cyc - j * 1.05))
        elif anim == "windup":
            # A coil: the middle bunches up into a hump.
            lift = bunch * 9.0 * math.sin(math.pi * j / (n - 1)) + 0.6 * math.sin(cyc * 2.0 + j)
        y = GROUND - r - 1.0 - lift - hop
        out.append((x, y, r))
    return out


def _page(f: K.Frame, x: float, y: float, angle: float, bitten: float) -> None:
    """A page of a book, held at its left edge at `(x, y)`. `bitten` is how
    much of its right side is eaten away."""
    w, h = 15.0 - 4.0 * bitten, 12.0
    edge = [(x + w, y - h / 2.0)]
    for k in range(1, 4):
        # A scalloped edge: the marks of the bites.
        yy = y - h / 2.0 + h * k / 4.0
        edge.append((x + w - 2.6, yy - h / 8.0))
        edge.append((x + w, yy))
    pts = [(x, y - h / 2.0)] + edge + [(x + w, y + h / 2.0), (x, y + h / 2.0)]
    pts = K.turn(pts, x, y, angle)
    f.poly(pts, PARCHMENT)
    for k in range(3):
        yy = y - 3.0 + k * 3.0
        f.ink(K.turn([(x + 3.0, yy), (x + w - 4.0, yy)], x, y, angle), 0.7, K.alpha(K.INK, 0.6))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"bookworm:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    stretch, bunch, hop, flip, fade = 0.0, 0.0, 0.0, False, 1.0
    rear, head_dx, jaw, eyes, tilt = 0.0, 0.0, 0.25 + 0.25 * math.sin(cyc * 2.0), "dot", 0.0
    page, page_drop, alarm, specs_off, specs_glint = True, 0.0, False, 0.0, 0.0
    breathe = 0.0
    if anim == "idle":
        breathe = 0.04 * math.sin(cyc)
        rear = 1.5 * math.sin(cyc)
        specs_glint = max(0.0, math.sin(cyc - 1.0))
    elif anim == "walk":
        rear = 3.0 * max(0.0, math.sin(cyc - 6 * 1.05))
        jaw = 0.2
    elif anim == "notice":
        rear, alarm, eyes, jaw = 14.0 * math.sin(math.pi * min(1.0, t * 1.4)), True, "wide", 0.6
        page_drop, specs_glint = t, 1.0
        head_dx = -2.0
    elif anim == "windup":
        bunch, rear, head_dx, jaw, eyes = 0.35, 12.0 + 1.0 * math.sin(cyc * 2.0), -12.0, 1.0, "narrow"
        page = False
    elif anim == "attack_side":
        strike = math.sin(math.pi * min(1.0, t * 1.5))
        stretch, head_dx, rear = 0.12 * strike, 6.0 * strike, 6.0 * (1.0 - strike)
        jaw = 1.0 if t < 0.35 else max(0.0, 1.0 - (t - 0.35) * 4.0)
        eyes, page = "narrow", False
        tilt = 12.0 * strike
    elif anim == "hit":
        k = math.sin(math.pi * t)
        breathe, rear, head_dx, eyes, jaw, tilt = -0.15 * k, 4.0, -6.0 * k, "x", 0.5, -18.0 * k
        specs_off, page = 1.0, False
    elif anim == "death":
        # A hop up, then it lands on its back.
        hop = 12.0 * math.sin(math.pi * min(1.0, t / 0.4)) if t < 0.4 else 0.0
        flip, eyes, jaw, page = t >= 0.4, "x", 0.8, False
        specs_off = 2.0 if t >= 0.2 else 1.0
        fade = 1.0 - max(0.0, t - 0.6) / 0.4

    spine = _spine(anim, cyc, stretch, bunch, hop)
    if flip:
        # On its back the body lies lower, squashed on the ground.
        spine = [(x, GROUND - r * 0.85 - 1.0, r) for x, _, r in spine]
    sx = 1.0 + breathe
    # The segments, tail first: each one in front of the one behind it.
    for j, (x, y, r) in enumerate(spine):
        rx, ry = r * sx, r * (1.0 - breathe) * (0.85 if flip else 1.0)
        up = -1.0 if flip else 1.0
        if flip:
            # Its legs in the air.
            f.ellipse(x + 1.0, y - ry - 1.5, 2.4, 2.8, WORM_DARK)
        f.ellipse(x, y, rx, ry, WORM)
        f.ellipse(x - rx * 0.12, y + up * ry * 0.38, rx * 0.8, ry * 0.5, WORM_BELLY, body=False)
        if not flip:
            f.ellipse(x + rx * 0.2, y - ry * 0.45, rx * 0.35, ry * 0.18, K.shade(WORM, 1.35), body=False)
        if j > 0:
            # The ring between this segment and the one behind it.
            f.ink([(x - rx * 0.78, y - ry * 0.6), (x - rx * 0.95, y), (x - rx * 0.78, y + ry * 0.6)], 1.1, WORM_DARK)
        if not flip:
            # A stub of a leg under the segment.
            f.ellipse(x + 1.0, GROUND - 2.0 - (GROUND - r - 1.0 - y) * 0.9, 2.6, 2.0, WORM_DARK)

    # The head: in front of the neck, reared up and pushed forward.
    nx, ny, nr = spine[-1]
    hx, hy = nx + 13.0 + head_dx, ny - 6.0 - rear
    if flip:
        hx, hy = nx + 14.0, GROUND - 14.0
    hr = 16.0
    f.ellipse(hx, hy, hr, hr * 0.94, WORM)
    f.ellipse(hx - 3.0, hy + hr * 0.5, hr * 0.7, hr * 0.32, K.shade(WORM, 0.88), body=False)
    f.ellipse(hx + 2.0, hy - hr * 0.55, hr * 0.4, hr * 0.18, K.shade(WORM, 1.35), body=False)

    # The mouth, at the front and low: a dark open shape when the jaw drops.
    mx, my = hx + hr * 0.62, hy + hr * 0.42
    gape = 1.5 + 6.0 * jaw
    mouth = K.turn([(mx - 6.0, my), (mx + 7.0, my - 2.0 - gape * 0.3), (mx + 7.5, my + gape * 0.7), (mx - 4.0, my + 1.5)], mx, my, tilt)
    f.poly(mouth, K.shade(WORM_DARK, 0.5), body=False)
    if jaw > 0.55:
        # Two flat teeth, for chewing paper.
        f.poly(K.turn([(mx + 1.0, my - 1.0), (mx + 4.5, my - 1.6), (mx + 4.2, my + 1.6), (mx + 1.2, my + 1.8)], mx, my, tilt), K.WHITE, body=False)
    if page:
        _page(f, mx + 2.0, min(GROUND - 7.0, my + 1.0 + 30.0 * page_drop * page_drop), 10.0 + 70.0 * page_drop + 6.0 * math.sin(cyc * 2.0), 0.5 + 0.3 * math.sin(cyc))

    # The spectacles: two round gold rims on the front of the face, a bridge
    # between them and an arm back to where an ear would be.
    off = specs_off
    lx, ly = hx + 4.0, hy - 3.0
    if off >= 2.0:
        # Fallen off, on the ground in front of it.
        lx, ly = 79.0, GROUND - 6.0
    lens_turn = -20.0 * min(off, 1.0) if off < 2.0 else 12.0
    if off >= 1.0 and off < 2.0:
        lx, ly = lx + 2.0, ly + 3.0
    near, far = (lx + 4.0, ly), (lx - 5.0, ly - 0.5)
    near, far = K.turn([near, far], lx, ly, lens_turn)
    if off < 2.0:
        f.ink([far, (hx - hr * 0.55, hy - 4.0)], 1.2, K.GOLD_DARK)
    for (cx, cy), r in ((far, 4.0), (near, 4.8)):
        f.ellipse(cx, cy, r + 1.3, r + 1.3, K.GOLD, body=False)
        f.ellipse(cx, cy, r, r, GLASS, body=False)
    f.ink([(far[0] + 3.6, far[1]), (near[0] - 4.2, near[1])], 1.2, K.GOLD_DARK)
    if off >= 2.0:
        # No spectacles: the eyes are on the bare face.
        for cx, cy in ((hx + 3.0, hy - 3.0), (hx + 10.0, hy - 3.5)):
            f.ink([(cx - 2.2, cy - 2.2), (cx + 2.2, cy + 2.2)], 1.2)
            f.ink([(cx - 2.2, cy + 2.2), (cx + 2.2, cy - 2.2)], 1.2)
    else:
        # The eyes, made big by the glass.
        for (cx, cy), big in ((far, 0.85), (near, 1.0)):
            if eyes == "x":
                f.ink([(cx - 2.0, cy - 2.0), (cx + 2.0, cy + 2.0)], 1.1)
                f.ink([(cx - 2.0, cy + 2.0), (cx + 2.0, cy - 2.0)], 1.1)
            elif eyes == "narrow":
                f.poly([(cx - 2.8, cy - 1.6), (cx + 2.8, cy - 0.4), (cx + 2.8, cy + 1.2), (cx - 2.8, cy + 1.2)], K.INK, body=False)
            else:
                f.dot(cx + 0.8, cy + 0.3, (2.4 if eyes == "wide" else 1.9) * big)
                f.dot(cx + 0.2, cy - 0.6, 0.6, K.WHITE)
    if specs_glint > 0.05 and off < 2.0:
        cx, cy = near
        f.ink([(cx - 2.6, cy + 1.6), (cx + 0.4, cy - 2.6)], 1.0, K.alpha(K.WHITE, specs_glint))
        f.glow(cx, cy, 4.0, K.alpha(K.GOLD, 0.45 * specs_glint))

    if alarm:
        ax, ay = hx + hr + 6.0, max(10.0, hy - hr - 4.0)
        f.limb([(ax, ay - 9.0), (ax, ay)], 2.6, K.MAGENTA)
        f.ellipse(ax, ay + 5.0, 1.7, 1.7, K.MAGENTA)
    if anim == "attack_side" and 0.2 < t < 0.8:
        # The chomp: the marks of a bite in the air in front of the mouth.
        a = 1.0 - abs(t - 0.5) / 0.3
        bx = min(mx + 9.0, 84.0)
        for k in (-1.0, 1.0):
            arc = [(bx + 5.0 * math.sin(u), my + k * (2.0 + 6.0 * (1.0 - math.cos(u)) / 2.0)) for u in (0.0, 0.8, 1.6, 2.4, 3.1)]
            f.glow_line(arc, 2.2, K.alpha(K.WHITE, 0.95 * a))
            for u in (0.8, 1.6, 2.4):
                tx, ty = bx + 5.0 * math.sin(u), my + k * (2.0 + 6.0 * (1.0 - math.cos(u)) / 2.0)
                f.glow_line([(tx, ty), (tx - 1.0, ty - k * 3.0)], 1.6, K.alpha(K.GOLD, 0.95 * a))
    if anim == "hit":
        # Scraps of paper knocked out of it.
        for k in range(4):
            a = rng.uniform(-2.6, -0.6)
            d = 14.0 + 10.0 * t
            px, py = hx + math.cos(a) * d, hy + math.sin(a) * d
            f.poly(K.turn([(px - 2.0, py - 1.5), (px + 2.0, py - 1.5), (px + 2.0, py + 1.5), (px - 2.0, py + 1.5)], px, py, rng.uniform(0, 90)), PARCHMENT, body=False)
    return f.finish(width=1.6, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
