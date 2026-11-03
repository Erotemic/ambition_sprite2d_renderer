"""The Taotie Spirit: the mask of the Shang bronzes, as a floating spirit.

On the bronze vessels of the Shang court there is one face again and
again: the taotie. It looks at you from the front: two big round eyes, a
ridge down its nose, horns that curl, an upper jaw with fangs and no lower
jaw, and on each side of it the long body of a dragon. Square spirals (the
"thunder pattern") fill every gap. Nobody knows what it meant. It has
been staring for three thousand years.

This one has come off its vessel. It is old bronze, green with verdigris
and bright where it is worn. It floats and keeps its distance. Its eyes
follow you. Its windup is a breath: its horns curl back and its mouth
glows. Its strike spits a gob of molten bronze at you, and it kicks back.
A hit flakes verdigris off it; at its death it cracks and falls in pieces.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_asia_kit as A

TARGET_NAME = "taotie_spirit"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Taotie Spirit", "Amorphous", "Small", "Light", "Float", ["bronze", "mask", "spirit", "floating"],
    "The taotie mask of the Shang bronzes as a floating spirit of green bronze, on the East Asia floor of the History "
    "dimension. It keeps its distance, its eyes follow you, and it spits gobs of molten bronze.",
    "east_asia",
)

BODY = A.BRONZE_GREEN
LIGHT = A.BRONZE_GREEN_LIGHT
DARK = A.BRONZE_GREEN_DARK
DEEP = A.BRONZE_GREEN_DEEP
WORN = A.BRONZE_BRIGHT
EYE = (236, 230, 200, 255)
PUPIL = (30, 22, 20, 255)
MOLTEN = (255, 186, 70, 255)
MOLTEN_LIGHT = (255, 238, 170, 255)
FANG = (232, 222, 190, 255)

Point = Tuple[float, float]

#: The mask is drawn at this size about its middle.
SCALE = 0.86


def _square_spiral(cx: float, cy: float, s: float, turns: int = 2, flip: float = 1.0) -> List[Point]:
    """The thunder pattern: a square spiral from the middle out, `s` wide."""
    pts = [(cx, cy)]
    step = s / (2.0 * turns + 1.0)
    x, y, d = cx, cy, step
    dirs = [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)]
    for k in range(turns * 4):
        ux, uy = dirs[k % 4]
        x += ux * d * flip
        y += uy * d
        pts.append((x, y))
        if k % 2 == 1:
            d += step
    return pts


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"taotie:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cx, cy, sx, sy, lean = 62.0, 68.0, 1.0, 1.0, 0.0
    look, eyes, glow, curl, jet, kick, flakes, alarm, fade = 1.0, "open", 0.0, 0.0, 0.0, 0.0, 0.0, False, 1.0
    crack, fall, wings = 0.0, 0.0, math.sin(cyc)
    if anim == "idle":
        cy += 2.5 * math.sin(cyc)
        look = math.sin(cyc)
        wings = 0.5 * math.sin(cyc)
    elif anim == "walk":
        cy += 1.5 * math.sin(cyc * 2.0)
        lean, look = 6.0, 1.0
        wings = math.sin(cyc * 2.0)
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        eyes, alarm, look = "wide", True, 1.0
        cy -= 4.0 * k
        sx = sy = 1.0 + 0.06 * k
    elif anim == "windup":
        sx, sy = 1.08 + 0.02 * math.sin(cyc * 2.0), 1.06
        curl, glow, eyes, lean = 1.0, 0.6 + 0.4 * math.sin(cyc * 2.0), "narrow", -6.0
        cx -= 3.0
        wings = 1.0
    elif anim == "attack_side":
        spit = math.sin(math.pi * min(1.0, t * 1.4))
        jet, kick, glow = spit, spit, 1.0 - t
        lean, eyes = -10.0 * spit, "narrow"
        cx -= 6.0 * spit
        wings = -1.0
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        sx, sy, eyes, flakes = 1.0 + 0.12 * k, 1.0 - 0.1 * k, "shut", k
        cx -= 5.0 * k
        lean = 8.0 * k
    elif anim == "death":
        crack = min(1.0, t * 2.0)
        fall = max(0.0, t - 0.35) / 0.65
        eyes = "shut"
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    def P(x: float, y: float, piece: int = 0) -> Point:
        """A point of the mask: `x` and `y` about its middle, scaled and
        turned; a piece of a broken mask falls on its own way."""
        px, py = cx + x * sx * SCALE, cy + y * sy * SCALE
        if fall and piece:
            px += piece * 10.0 * fall
            py += 50.0 * fall * fall + (8.0 if piece > 0 else 4.0) * fall
        return K.turn([(px, py)], cx, cy, lean + (piece * 18.0 * fall))[0]

    def poly(pts, colour, body=True, piece=0):
        f.poly([P(x, y, piece) for x, y in pts], colour, body)

    def ink(pts, w, colour, piece=0):
        f.ink([P(x, y, piece) for x, y in pts], w, colour)

    def limb(pts, w, colour, body=True, piece=0):
        f.limb([P(x, y, piece) for x, y in pts], w * sx * SCALE, colour, body)

    # The mask is symmetric: each half is one piece when it breaks.
    for side in (-1.0, 1.0):
        pc = int(side) if fall else 0
        # The flank: the long body of a dragon, out to the side, with a
        # tail that curls up.
        flap = 3.0 * wings
        flank = [(side * 24.0, -6.0), (side * 40.0, -10.0 - flap), (side * 50.0, -4.0 - flap * 1.4), (side * 50.0, 4.0 - flap),
                 (side * 40.0, 8.0 - flap * 0.6), (side * 24.0, 10.0)]
        poly(flank, BODY, piece=pc)
        limb([(side * 46.0, -6.0 - flap * 1.4), (side * 50.0, -16.0 - flap * 1.6), (side * 45.0, -21.0 - flap * 1.6), (side * 41.0, -17.0 - flap * 1.5)],
             4.0, BODY, piece=pc)
        ink([(side * 28.0, -1.0), (side * 44.0, -4.0 - flap)], 1.0, DARK, piece=pc)
        ink(_square_spiral(side * 34.0, 2.0 - flap * 0.6, 7.0, 1, side), 0.8, DEEP, piece=pc)
        # The horn: a big C that curls out and down; in the windup it
        # curls back.
        hc = 1.0 + 0.12 * curl
        horn = [(side * 8.0, -22.0), (side * 16.0, -34.0 * hc), (side * 28.0, -38.0 * hc), (side * 36.0, -32.0 * hc), (side * 34.0, -24.0),
                (side * 27.0, -22.0)]
        limb(horn, 7.0, BODY, piece=pc)
        limb(horn[2:5], 3.0, LIGHT, body=False, piece=pc)
        limb([(side * 27.0, -22.0), (side * 30.0, -27.0)], 4.0, DARK, body=False, piece=pc)

    for side in (-1.0, 1.0):
        pc = int(side) if fall else 0
        # The face: a broad plate, square at the brow and narrow at the jaw.
        half = [(0.0, -26.0), (side * 22.0, -26.0), (side * 28.0, -14.0), (side * 28.0, 6.0), (side * 22.0, 18.0), (side * 12.0, 24.0),
                (0.0, 24.0)]
        poly(half, BODY, piece=pc)
        poly([(side * 22.0, -26.0), (side * 28.0, -14.0), (side * 28.0, 6.0), (side * 22.0, 18.0), (side * 19.0, 14.0), (side * 24.0, 4.0),
              (side * 24.0, -12.0), (side * 19.0, -22.0)], DARK, body=False, piece=pc)
        # The thunder pattern on the cheek and the brow.
        ink(_square_spiral(side * 18.0, 8.0, 8.0, 2, side), 0.8, DEEP, piece=pc)
        ink(_square_spiral(side * 12.0, -21.0, 6.0, 1, side), 0.8, DEEP, piece=pc)
        # The brow: a raised curl over the eye, worn bright on its edge.
        brow = [(side * 4.0, -12.0), (side * 10.0, -18.0), (side * 20.0, -18.0), (side * 25.0, -12.0)]
        if eyes == "narrow":
            brow = [(side * 4.0, -9.0), (side * 10.0, -15.0), (side * 20.0, -17.0), (side * 25.0, -13.0)]
        limb(brow, 3.6, DARK, body=False, piece=pc)
        limb(brow[1:3], 1.4, WORN, body=False, piece=pc)
        # The eye: a big round boss; its pupil follows you.
        ex, ey = side * 14.0, -6.0
        if eyes == "shut":
            poly([(ex - 6.0, ey - 1.0), (ex + 6.0, ey - 1.0), (ex + 5.0, ey + 2.0), (ex - 5.0, ey + 2.0)], DARK, body=False, piece=pc)
            ink([(ex - 5.0, ey), (ex + 5.0, ey)], 1.2, DEEP, piece=pc)
        else:
            r = {"open": 6.0, "wide": 7.0, "narrow": 6.0}[eyes]
            h = r * (0.55 if eyes == "narrow" else 1.0)
            pts = [(ex + r * math.cos(a), ey + h * math.sin(a)) for a in [math.tau * q / 20.0 for q in range(20)]]
            poly([(x * 1.0, y) for x, y in K.grow(pts, 1.6)], DEEP, body=False, piece=pc)
            poly(pts, EYE, body=False, piece=pc)
            px = ex + 2.6 * look
            pr = 2.8 if eyes != "wide" else 2.2
            ppts = [(px + pr * math.cos(a), ey + min(h, pr * 1.2) * math.sin(a)) for a in [math.tau * q / 14.0 for q in range(14)]]
            poly(ppts, PUPIL, body=False, piece=pc)
            if glow > 0.05:
                gx, gy = P(px, ey, pc)
                f.glow(gx, gy, 3.0, K.alpha(MOLTEN, 0.7 * glow))

    # The ridge down the nose, with its notches: the flange of the mould.
    if not fall:
        poly([(-3.0, -28.0), (3.0, -28.0), (3.0, 4.0), (-3.0, 4.0)], DARK, body=False)
        for k in range(5):
            y = -25.0 + k * 6.0
            ink([(-3.0, y), (3.0, y)], 0.8, WORN)
        # The snout: broad, with a curl for each nostril.
        poly([(-11.0, 2.0), (11.0, 2.0), (13.0, 10.0), (-13.0, 10.0)], LIGHT, body=False)
        for side in (-1.0, 1.0):
            ink(_square_spiral(side * 7.0, 6.0, 5.0, 1, side), 0.9, DEEP)
        # The upper jaw, with its fangs; no lower jaw. In the windup the
        # mouth glows; in the strike it opens wide and spits.
        mouth = [(-16.0, 12.0), (16.0, 12.0), (14.0, 20.0 + 6.0 * jet), (-14.0, 20.0 + 6.0 * jet)]
        poly(mouth, DEEP)
        if glow > 0.05 or jet > 0.05:
            g = max(glow, jet)
            poly([(-12.0, 14.0), (12.0, 14.0), (11.0, 18.0 + 5.0 * jet), (-11.0, 18.0 + 5.0 * jet)], K.alpha(MOLTEN, g), body=False)
            mx, my = P(0.0, 16.0)
            f.glow(mx, my, 10.0 * sx, K.alpha(MOLTEN, 0.35 * g))
        for k in range(6):
            x = -12.5 + k * 5.0
            poly([(x - 1.8, 12.0), (x + 1.8, 12.0), (x, 16.6)], FANG, body=False)
        for side in (-1.0, 1.0):
            # The tusks at the corners of the mouth, curled up.
            limb([(side * 15.0, 12.0), (side * 19.0, 20.0), (side * 22.0, 18.0)], 3.0, FANG)

    if jet > 0.05:
        # A gob of molten bronze, out of the mouth to the front.
        x0, y0 = P(14.0, 18.0)
        reach = 10.0 + 34.0 * jet
        bx = min(112.0, x0 + reach)
        f.glow_line([(x0, y0), (bx, y0 + 4.0 * jet)], 4.0 * jet, K.alpha(MOLTEN, 0.6))
        f.ellipse(bx, y0 + 4.0 * jet, 8.0 * jet + 1.0, 6.0 * jet + 1.0, MOLTEN)
        f.ellipse(bx - 1.6, y0 + 3.0 * jet, 2.6 * jet + 0.6, 1.8 * jet + 0.4, MOLTEN_LIGHT, body=False)
        for k in range(4):
            u = (k + 1) / 5.0
            f.dot(x0 + reach * u * 0.8, y0 + 3.0 * u + rng.uniform(-3.0, 3.0), 1.4, MOLTEN)
    if flakes > 0.05:
        # Verdigris flakes off it.
        for k in range(8):
            a = rng.uniform(0.0, math.tau)
            r = rng.uniform(30.0, 46.0) * (0.8 + 0.3 * flakes)
            x = min(120.0, max(8.0, cx + math.cos(a) * r))
            y = min(120.0, max(8.0, cy + math.sin(a) * r * 0.8))
            s = rng.uniform(1.4, 2.6)
            f.poly([(x - s, y), (x, y - s), (x + s, y + s * 0.5)], LIGHT if k % 2 else BODY)
    if crack > 0.05 and fall < 0.15:
        # The crack down the middle, from the brow to the jaw.
        ink([(0.0, -30.0), (2.0, -18.0), (-2.0, -6.0), (2.0, 6.0), (-1.0, 14.0 + 10.0 * crack)], 1.6, PUPIL)
    if alarm:
        ax, ay = P(30.0, -44.0)
        A.alarm_mark(f, min(120.0, ax), max(14.0, ay))
    return f.finish(outline=A.SEPIA_INK, width=1.4, glow_blur=2.0, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
