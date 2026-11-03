"""The Inflated Coin: a gold coin of the Monsoon Coast that blows itself up.

When Mansa Musa of Mali went through Cairo on his way to Mecca in 1324, he
gave away so much gold that the price of gold fell there for years. This is
one of those coins: it is gold, it is round, and it is worth less each time
it gets bigger.

A thick gold coin with a milled rim, a crown stamped above its face, and a
face: two eyes and the round cheeks of somebody who holds a breath. It
floats. Its idle row breathes in and out; its walk floats on, turning on
its edge. When it sees you it puffs up. Its windup blows it up as big as it
can go; its strike is a rush at you, spinning. A hit lets air out of it; at
its death it lets all its air out, goes dull, and falls, worth nothing.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_steppe_kit as H

TARGET_NAME = "inflated_coin"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Inflated Coin", "Blob", "Small", "Light", "Float", ["history", "monsoon", "gold", "coin", "floating"],
    "A gold coin of the Monsoon Coast in the History dimension, from the gold that Mansa Musa gave away until it lost "
    "its value. It floats, blows itself up bigger and bigger, and rushes at you spinning.",
)

FACE = H.GOLD
FACE_LIGHT = H.GOLD_LIGHT
RIM = (214, 150, 40, 255)
RIM_DARK = H.GOLD_DARK
DULL = (150, 140, 120, 255)
DULL_DARK = (104, 96, 84, 255)
CHEEK = (250, 150, 90, 255)


def _mix(a, b, k: float):
    return tuple(int(a[j] + (b[j] - a[j]) * k) for j in range(3)) + (255,)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    cx, cy, puff, wobble, spin = 46.0, 46.0, 0.0, 12.0 * math.sin(cyc), 0.0
    eyes, mouth, cheeks, dull, fade, alarm = "open", "held", 0.4, 0.0, 1.0, False
    strain, hiss, rush = 0.0, 0.0, 0.0
    if anim == "idle":
        cy += 2.5 * math.sin(cyc)
        puff = 0.12 + 0.12 * math.sin(cyc)
        cheeks = 0.4 + 0.4 * max(0.0, math.sin(cyc))
    elif anim == "walk":
        cy += 1.5 * math.sin(cyc * 2.0)
        wobble = 34.0 * math.sin(cyc)
        spin = 8.0
        puff = 0.15
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        puff, eyes, alarm, cheeks, mouth = 0.1 + 0.25 * k, "wide", True, 0.9 * k, "o"
        cy -= 4.0 * k
        wobble = 0.0
    elif anim == "windup":
        # As big as it can go, and shaking with the strain.
        puff = 0.42 + 0.03 * math.sin(cyc * 2.0)
        cx += 1.2 * math.sin(cyc * 4.0)
        cheeks, eyes, strain, wobble = 1.0, "squeeze", 1.0, 0.0
    elif anim == "attack_side":
        # Back (0), the rush (1..3), and back to its place, spinning.
        u = t
        rush = math.sin(math.pi * min(1.0, u * 1.25))
        cx = 40.0 + 16.0 * rush
        puff = 0.40 - 0.1 * rush
        wobble = (u * 540.0) % 360.0 - 180.0 if 0.1 < u < 0.8 else 0.0
        eyes, cheeks, mouth = "narrow", 1.0, "grit"
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        puff, eyes, mouth, cheeks, hiss = 0.1 - 0.2 * k, "shut", "o", 0.0, k
        cx -= 5.0 * k
    elif anim == "death":
        u = t
        puff = 0.1 - 0.55 * min(1.0, u * 1.4)
        dull = min(1.0, u * 1.6)
        eyes, mouth, cheeks = "x", "o", 0.0
        wobble = 70.0 * min(1.0, u * 1.2)
        cy = 46.0 + 34.0 * max(0.0, u - 0.35) ** 2 * 2.4
        hiss = 1.0 - u
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    r = 21.0 * (1.0 + puff)
    sx = abs(math.cos(math.radians(wobble)))
    edge_dir = 1.0 if math.sin(math.radians(wobble)) >= 0.0 else -1.0
    edge = 5.0 * abs(math.sin(math.radians(wobble))) * (1.0 + puff * 0.5)
    face = _mix(FACE, DULL, dull)
    face_light = _mix(FACE_LIGHT, DULL, dull)
    rim = _mix(RIM, DULL_DARK, dull)
    rim_dark = _mix(RIM_DARK, DULL_DARK, dull * 0.8)

    def T(pts):
        return K.turn(pts, cx, cy, spin)

    # The edge of the coin, seen as it turns: a band with its milling.
    if edge > 0.4:
        back = (cx - edge_dir * edge, cy)
        f.poly(T(K.ellipse_points(back[0], back[1], max(1.0, r * sx), r, 32)), rim_dark)
        f.poly(T([(cx, cy - r), (back[0], cy - r), (back[0], cy + r), (cx, cy + r)]), rim_dark)
        for k in range(9):
            yy = cy - r * 0.85 + k * r * 0.21
            xx = cx - edge_dir * (r * sx * math.sqrt(max(0.0, 1.0 - ((yy - cy) / r) ** 2)))
            f.ink(T([(xx, yy), (xx - edge_dir * edge, yy)]), 0.8, K.shade(rim_dark, 0.75))
    # The face of the coin: a rim, and the field inside it.
    f.poly(T(K.ellipse_points(cx, cy, max(1.0, r * sx), r, 36)), rim)
    fr = r * 0.84
    f.poly(T(K.ellipse_points(cx, cy, max(0.6, fr * sx), fr, 32)), face, body=False)
    # Milling round the rim.
    for k in range(28):
        a = math.tau * k / 28.0
        p0 = (cx + math.cos(a) * r * 0.86 * sx, cy + math.sin(a) * r * 0.86)
        p1 = (cx + math.cos(a) * r * 0.98 * sx, cy + math.sin(a) * r * 0.98)
        f.ink(T([p0, p1]), 0.6, rim_dark)
    # The light on the gold, upper left.
    f.poly(T([(cx - fr * 0.75 * sx, cy - fr * 0.1), (cx - fr * 0.55 * sx, cy - fr * 0.6), (cx - fr * 0.1 * sx, cy - fr * 0.82),
              (cx - fr * 0.3 * sx, cy - fr * 0.5), (cx - fr * 0.6 * sx, cy - fr * 0.05)]), face_light, body=False)

    if sx > 0.35:
        def P(x, y):
            return T([(cx + x * sx * (1.0 + puff), cy + y * (1.0 + puff))])[0]

        # The crown stamped above the face.
        crown = [P(-7.0, -10.0), P(-7.0, -15.0), P(-4.0, -12.4), P(0.0, -16.6), P(4.0, -12.4), P(7.0, -15.0), P(7.0, -10.0)]
        f.poly(crown, rim, body=False)
        f.ink(crown + [crown[0]], 0.7, rim_dark)
        # The cheeks, puffed out round the held breath.
        if cheeks > 0.05:
            for side in (-1.0, 1.0):
                bx, by = P(side * 10.0, 4.0)
                f.ellipse(bx, by, (3.0 + 3.0 * cheeks) * sx * (1.0 + puff), (2.6 + 2.6 * cheeks) * (1.0 + puff), _mix(CHEEK, DULL, dull), body=False)
                f.ellipse(bx - 1.0 * sx, by - 1.0, 1.0 * sx * (1.0 + puff), 0.8 * (1.0 + puff), K.alpha(K.WHITE, 0.8), body=False)
        # The eyes.
        for side in (-1.0, 1.0):
            ex, ey = P(side * 6.0, -4.0)
            s = (1.0 + puff)
            if eyes == "shut":
                f.ink([(ex - 2.4 * sx * s, ey), (ex + 2.4 * sx * s, ey + 0.6)], 1.2, H.SEPIA_INK)
            elif eyes == "x":
                f.ink([(ex - 2.0 * sx * s, ey - 2.0 * s), (ex + 2.0 * sx * s, ey + 2.0 * s)], 1.1, H.SEPIA_INK)
                f.ink([(ex - 2.0 * sx * s, ey + 2.0 * s), (ex + 2.0 * sx * s, ey - 2.0 * s)], 1.1, H.SEPIA_INK)
            elif eyes == "squeeze":
                # Shut tight: a ">" and a "<".
                w = 2.4 * sx * s
                f.ink([(ex + side * w, ey - 2.2 * s), (ex - side * w, ey), (ex + side * w, ey + 2.2 * s)], 1.2, H.SEPIA_INK)
            else:
                big = 1.25 if eyes == "wide" else 1.0
                h = 3.4 if eyes != "narrow" else 2.0
                f.ellipse(ex, ey, 2.6 * sx * s * big, h * s * big, K.WHITE, body=False)
                f.dot(ex + 0.8 * sx, ey + 0.4, 1.4 * s * big, H.SEPIA_INK)
                if eyes == "narrow":
                    f.ink([(ex - 3.0 * sx * s, ey - 3.4 - side * 0.8), (ex + 3.0 * sx * s, ey - 3.4 + side * 0.8)], 1.0, H.SEPIA_INK)
        # The mouth: a breath held in, an "o", or teeth set.
        mx, my = P(0.0, 6.0)
        if mouth == "held":
            f.ellipse(mx, my, 2.4 * sx * (1.0 + puff), 1.4 * (1.0 + puff), H.SEPIA_INK, body=False)
        elif mouth == "o":
            f.ellipse(mx, my, 2.2 * sx * (1.0 + puff), 2.8 * (1.0 + puff), H.SEPIA_INK, body=False)
        else:
            f.poly([P(-4.0, 4.6), P(4.0, 4.6), P(4.0, 7.6), P(-4.0, 7.6)], K.WHITE, body=False)
            f.ink([P(-4.0, 6.1), P(4.0, 6.1)], 0.7, H.SEPIA_INK)
            f.ink([P(0.0, 4.6), P(0.0, 7.6)], 0.6, H.SEPIA_INK)
    if strain:
        # Lines of strain round it, and a creak at its rim.
        for k in range(6):
            a = math.tau * k / 6.0 + 0.4
            p0 = (cx + math.cos(a) * (r + 4.0), cy + math.sin(a) * (r + 4.0))
            p1 = (cx + math.cos(a) * (r + 8.0), cy + math.sin(a) * (r + 8.0))
            f.ink([p0, p1], 1.2, K.alpha(H.GOLD_LIGHT, 0.95))
    if hiss > 0.05:
        # The air that leaks out of it, as puffs.
        for k in range(3):
            px = cx - r - 4.0 - k * 6.0
            py = cy - 6.0 + k * 4.0
            f.ellipse(max(6.0, px), py, 2.6 + k, 2.0 + k * 0.6, K.alpha(K.WHITE, 0.75 * hiss), body=False)
    if rush > 0.3:
        for k in range(3):
            y0 = cy - 10.0 + k * 10.0
            f.ink([(cx - r - 6.0, y0), (max(4.0, cx - r - 18.0), y0)], 1.4, K.alpha(K.WHITE, 0.8 * rush))
    # A glint that goes round the gold.
    if dull < 0.5:
        ga = cyc + 0.8
        gx, gy = cx + math.cos(ga) * r * 0.7 * sx, cy + math.sin(ga) * r * 0.7
        f.glow_poly([(gx, gy - 4.0), (gx + 1.0, gy - 1.0), (gx + 4.0, gy), (gx + 1.0, gy + 1.0), (gx, gy + 4.0), (gx - 1.0, gy + 1.0),
                     (gx - 4.0, gy), (gx - 1.0, gy - 1.0)], K.alpha(K.WHITE, 0.95))
        f.glow_poly(T(K.ellipse_points(cx, cy, max(2.0, r * 1.05 * sx), r * 1.05, 28)), K.alpha(H.GOLD, 0.18 * (1.0 - dull)))
    if alarm:
        H.alarm_mark(f, cx + r * 0.6 + 6.0, max(14.0, cy - r - 12.0))
    return f.finish(outline=H.SEPIA_INK, width=1.4, glow_blur=2.0, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
