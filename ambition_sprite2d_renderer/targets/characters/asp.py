"""The Asp: a cobra of the Nile with its hood out.

A cobra the colour of sandstone, with darker bands down its back, a pale
belly and two dark bands across its throat. It lies in two coils on the
ground and rears up out of them; its hood is spread wide behind its head,
and a thin band of gold and lapis crosses the hood, as on the cobra of a
pharaoh's crown. It has gold eyes and a red forked tongue.

It sways in its coils and flicks its tongue. It slithers with its hood half
shut. When it sees you it rears up high and spreads its hood. Its windup
draws its head back with its mouth open; its strike throws the head forward
and spits. A hit makes it flinch and shut its hood; at its death it falls
out of its coils and lies flat.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_ancient_kit as H

TARGET_NAME = "asp"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS
GROUND = 88.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Asp", "nile", "Serpentine", "Small", "Light", "Walk", ["snake", "cobra", "spit"],
    "A cobra of the History dimension's Nile, the colour of sandstone, with its hood spread. It sways in its coils, "
    "keeps its distance, draws its head back and spits.",
)

SCALE = H.SANDSTONE
SCALE_SHADE = H.SANDSTONE_SHADE
SCALE_DARK = (130, 92, 50, 255)
BELLY = (246, 230, 190, 255)
THROAT = (84, 54, 34, 255)
TONGUE = (214, 40, 48, 255)
MOUTH = (150, 40, 50, 255)
VENOM = (190, 240, 120, 255)

Point = Tuple[float, float]


def _bezier(p0: Point, p1: Point, p2: Point, p3: Point, u: float) -> Point:
    a = (1.0 - u) ** 3
    b = 3.0 * (1.0 - u) ** 2 * u
    c = 3.0 * (1.0 - u) * u * u
    d = u ** 3
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)

    rear, sway, reach, hood, mouth, eyes, tongue = 1.0, 0.0, 0.0, 1.0, 0.0, "open", 0.0
    coil_wave, fall, fade, spit, alarm = 0.0, 0.0, 1.0, 0.0, False
    if anim == "idle":
        sway = 3.0 * math.sin(cyc)
        tongue = 1.0 if i in (1, 4) else 0.0
        hood = 0.95 + 0.05 * math.sin(cyc)
    elif anim == "walk":
        rear, hood = 0.7, 0.55
        sway = 2.0 * math.sin(cyc * 2.0)
        coil_wave = cyc
        tongue = 1.0 if i % 4 == 1 else 0.0
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        rear, hood, mouth, alarm = 1.0 + 0.1 * k, 1.0 + 0.3 * k, 0.6 * k, True
    elif anim == "windup":
        rear, hood, reach = 1.1, 1.3, -9.0 + 1.0 * math.sin(cyc * 2.0)
        mouth, eyes = 0.5 + 0.1 * math.sin(cyc * 2.0), "narrow"
        sway = 0.8 * math.sin(cyc * 3.0)
    elif anim == "attack_side":
        # The strike: the head goes forward fast, spits, and comes back.
        u = min(1.0, t * 1.5)
        thrust = math.sin(math.pi * u)
        rear, hood, reach = 1.1 - 0.2 * thrust, 1.3, -9.0 + 20.0 * thrust
        mouth, eyes, spit = 1.0 - 0.5 * u, "narrow", thrust if t < 0.6 else 0.0
    elif anim == "hit":
        k = math.sin(math.pi * t)
        rear, hood, reach, eyes, sway = 1.0 - 0.25 * k, 1.0 - 0.6 * k, -8.0 * k, "shut", -2.0 * k
    elif anim == "death":
        fall = min(1.0, t / 0.8)
        rear, hood, eyes, mouth, tongue = 1.0 - 0.95 * fall, 1.0 - 0.9 * fall, "x" if fall > 0.5 else "shut", 0.3 * fall, 1.0 if fall > 0.6 else 0.0
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # The coils on the ground: a low heap of two loops, and the tail, which
    # curls out to the left and thins to a point.
    cx, cy = 44.0, GROUND - 7.0
    w = 1.5 * math.sin(coil_wave)
    tail = [(cx - 18.0, cy + 3.0), (cx - 25.0, cy + 2.0 + w), (cx - 30.0, cy - 1.0), (cx - 31.0, cy - 5.0), (cx - 28.0, cy - 7.0)]
    for k in range(len(tail) - 1):
        f.limb([tail[k], tail[k + 1]], 5.0 - 1.1 * k, SCALE)
    f.poly(K.ellipse_points(cx, cy - 1.0 + 0.5 * w, 21.0, 7.5, 30), SCALE_SHADE)
    lower = [(cx - 20.0 + 40.0 * k / 12.0, cy + 2.0 + 3.0 * math.sin(math.pi * k / 12.0) - 0.6 * w) for k in range(13)]
    upper = [(cx - 14.0 + 30.0 * k / 10.0, cy - 5.0 + 2.5 * math.sin(math.pi * k / 10.0) + 0.6 * w) for k in range(11)]
    for loop, width in ((upper, 7.5), (lower, 8.5)):
        f.limb(loop, width, SCALE)
        for k in range(1, len(loop) - 1, 2):
            x, y = loop[k]
            f.ink([(x - 1.5, y - width * 0.35), (x + 1.5, y - width * 0.42)], 1.6, SCALE_DARK)
        f.ink([(x0, y0 + width * 0.32) for x0, y0 in loop[1:-1]], 1.2, BELLY)

    # The body: up from the front coil to the head, in an S.
    hx = 64.0 + reach + sway
    hy = GROUND - 60.0 * rear
    if fall:
        hx += 8.0 * fall
        hy = hy + (GROUND - 8.0 - hy) * fall
    p0 = (cx + 18.0, cy + 2.0)
    p1 = (cx + 34.0, cy + 2.0 - 4.0 * rear)
    p2 = (hx - 18.0 - 4.0 * sway + 4.0 * fall, hy + 34.0 * rear)
    p3 = (hx - 6.0, hy + 10.0 * max(0.2, rear))
    spine = [_bezier(p0, p1, p2, p3, k / 14.0) for k in range(15)]
    for k in range(14):
        f.limb([spine[k], spine[k + 1]], 9.0 - 2.0 * k / 14.0, SCALE)
    # The pale belly along its front, and dark bands across its back.
    for k in range(1, 14):
        x0, y0 = spine[k - 1]
        x1, y1 = spine[k + 1]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = dy / ln, -dx / ln
        wid = 4.0 - 1.0 * k / 14.0
        x, y = spine[k]
        f.ink([(x - nx * wid * 0.2, y - ny * wid * 0.2), (x - nx * wid, y - ny * wid)], 2.0, BELLY)
        if k % 3 == 0:
            f.ink([(x + nx * wid * 0.1, y + ny * wid * 0.1), (x + nx * wid, y + ny * wid)], 2.4, SCALE_DARK)

    # The hood: a broad oval round the neck, behind the head.
    neck = p3
    hw, hh = 11.0 * hood, 14.0 * max(0.5, min(1.2, hood))
    if hood > 0.15:
        hc = (neck[0] - 3.0, neck[1] - 2.0 * hood)
        f.poly(K.turn(K.ellipse_points(hc[0], hc[1], hw, hh, 28), hc[0], hc[1], 12.0), SCALE)
        f.poly(K.turn(K.ellipse_points(hc[0] + 2.0, hc[1] + 1.0, hw * 0.62, hh * 0.78, 24), hc[0], hc[1], 12.0), BELLY, body=False)
        for k, dy in enumerate((2.0, 7.0)):
            band = K.turn([(hc[0] - hw * 0.5, hc[1] + dy), (hc[0] + hw * 0.6, hc[1] + dy - 1.0)], hc[0], hc[1], 12.0)
            f.ink(band, 2.4 if k == 0 else 1.8, THROAT)
        # A band of gold and lapis across the hood.
        ring = K.turn([(hc[0] - hw * 0.8, hc[1] - hh * 0.35), (hc[0], hc[1] - hh * 0.5), (hc[0] + hw * 0.8, hc[1] - hh * 0.35)], hc[0], hc[1], 12.0)
        f.ink(ring, 1.8, H.GOLD)
        f.dot(*K.turn([(hc[0], hc[1] - hh * 0.5)], hc[0], hc[1], 12.0)[0], 1.4, H.LAPIS)

    # The head: a broad wedge, snout to the right.
    head_tilt = -8.0 * fall + (6.0 if anim == "attack_side" and reach > 4.0 else 0.0)
    gape = 5.0 * mouth

    def hd(points):
        return K.turn(points, hx, hy, head_tilt)

    if gape > 0.5:
        f.poly(hd([(hx - 4.0, hy + 1.0), (hx + 9.0, hy + 1.0 + gape * 0.4), (hx + 6.0, hy + 3.0 + gape), (hx - 3.0, hy + 4.0)]), MOUTH)
        f.poly(hd([(hx + 2.0, hy + 2.0), (hx + 3.0, hy + 3.0 + gape * 0.6), (hx + 4.0, hy + 2.0)]), K.WHITE, body=False)
    f.poly(hd([(hx - 7.0, hy + 3.0), (hx - 6.0, hy - 4.0), (hx + 2.0, hy - 5.0), (hx + 9.0, hy - 2.0), (hx + 10.0, hy + 1.0), (hx + 2.0, hy + 2.5)]), SCALE)
    f.poly(hd([(hx - 6.0, hy - 4.0), (hx + 2.0, hy - 5.0), (hx + 9.0, hy - 2.0), (hx + 2.0, hy - 2.0)]), SCALE_SHADE, body=False)
    f.poly(hd([(hx - 6.0, hy + 4.0 + gape * 0.3), (hx + 6.0, hy + 2.5 + gape), (hx + 7.0, hy + 4.0 + gape), (hx - 5.0, hy + 6.0)]), BELLY)
    ex, ey = hd([(hx + 1.0, hy - 1.6)])[0]
    if eyes == "shut":
        f.ink([(ex - 1.8, ey), (ex + 1.8, ey + 0.4)], 1.0, H.OUTLINE)
    elif eyes == "x":
        f.ink([(ex - 1.4, ey - 1.4), (ex + 1.4, ey + 1.4)], 0.9, H.OUTLINE)
        f.ink([(ex - 1.4, ey + 1.4), (ex + 1.4, ey - 1.4)], 0.9, H.OUTLINE)
    else:
        f.ellipse(ex, ey, 2.0, 1.6 if eyes == "open" else 1.1, H.GOLD, body=False)
        f.poly([(ex - 0.4, ey - 1.4), (ex + 0.4, ey - 1.4), (ex + 0.4, ey + 1.4), (ex - 0.4, ey + 1.4)], H.OUTLINE, body=False)
        f.ink([(ex - 2.4, ey - 2.0), (ex + 2.0, ey - 2.4)], 1.0, H.OUTLINE)
    if tongue:
        tx, ty = hd([(hx + 10.0, hy + 1.5 + gape * 0.5)])[0]
        f.ink([(tx, ty), (tx + 5.0, ty + 0.5)], 0.9, TONGUE)
        f.ink([(tx + 5.0, ty + 0.5), (tx + 7.0, ty - 1.0)], 0.7, TONGUE)
        f.ink([(tx + 5.0, ty + 0.5), (tx + 7.0, ty + 2.0)], 0.7, TONGUE)
    if anim == "notice" and mouth > 0.3:
        # The hiss: three short lines out of the mouth.
        mx, my = hd([(hx + 11.0, hy + 2.0)])[0]
        for k in (-1.0, 0.0, 1.0):
            f.glow_line([(mx + 2.0, my + k * 3.0), (mx + 7.0, my + k * 4.5)], 1.0, K.alpha(K.WHITE, 0.8 * mouth))
    if spit > 0.2:
        # The spit leaves the mouth: drops of venom in a spray.
        mx, my = hd([(hx + 10.0, hy + 2.0)])[0]
        for k in range(4):
            d = 4.0 + k * 4.0 * spit
            r = 1.6 - 0.25 * k
            f.ellipse(min(90.0, mx + d), my + (k - 1.5) * 1.2, r, r, VENOM, body=False)
        f.glow(min(78.0, mx + 6.0), my, 4.0, K.alpha(VENOM, 0.5 * spit))
    if alarm:
        H.alarm_mark(f, min(84.0, hx + 16.0), max(16.0, hy - 2.0))
    return f.finish(outline=H.OUTLINE, width=1.3, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
