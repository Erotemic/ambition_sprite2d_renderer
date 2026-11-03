"""The Indus Unicorn: the one-horned bull of the Indus seals, come alive.

On most of the stone seals of the Indus cities there is one animal: a bull
in profile with one long horn that curves forward and up, a long neck with
folds, and a harness over its shoulders. Nobody knows what it was. Nobody
can read the signs above it either.

This one stepped off a seal. It is carved steatite: pale cream stone with
lines cut into it, the folds of its neck, the harness on its shoulders,
and two square marks on its side, each with signs of the script that
nobody can read. Its eye is a cut almond.

It walks stiffly, as a carving that is new to legs. When it sees you it
lifts its head and its horn. Its windup lowers the horn at you and paws
the ground; its strike is a charge, horn first, and a toss. A hit chips
it; at its death it cracks and falls back into a flat square seal.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_asia_kit as A
from . import _stage_kit as S

TARGET_NAME = "indus_unicorn"
FRAME_SIZE = (160, 128)
ROWS = K.ENEMY_ROWS
GROUND = 122.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Indus Unicorn", "Quadruped", "Standard", "Medium", "Walk", ["seal", "horn", "charge", "stone"],
    "The one-horned bull of the Indus seals, come alive on the South Asia floor of the History dimension: carved pale "
    "steatite with square seal marks on its side. It lowers its one horn, paws the ground and charges.",
    "south_asia",
)

STONE = A.STEATITE
STONE_SHADE = A.STEATITE_SHADE
STONE_DARK = A.STEATITE_DARK
CUT = (110, 84, 62, 255)
HORN = (250, 244, 228, 255)
HARNESS = A.CARNELIAN
HARNESS_DARK = (150, 56, 36, 255)
BEAD = A.FAIENCE
HOOF = (96, 74, 58, 255)

Point = Tuple[float, float]

UPPER, LOWER = 18.0, 20.0


def _sign(f: K.Frame, kind: int, x: float, y: float, s: float, colour) -> None:
    """One sign of the script, cut in the stone: a jar, a fish, strokes, a
    man, a wheel. A sign is drawn about (`x`, `y`) at size `s`."""
    if kind == 0:
        # The jar: the sign that comes most often.
        f.ink([(x - s, y - s), (x - s * 0.6, y + s), (x + s * 0.6, y + s), (x + s, y - s)], 0.8, colour)
        f.ink([(x - s * 1.2, y - s), (x + s * 1.2, y - s)], 0.8, colour)
    elif kind == 1:
        # The fish.
        f.ink([(x - s, y), (x, y - s * 0.7), (x + s, y), (x, y + s * 0.7), (x - s, y), (x - s * 1.4, y - s * 0.5)], 0.8, colour)
    elif kind == 2:
        for k in range(3):
            f.ink([(x - s + k * s, y - s), (x - s + k * s, y + s)], 0.8, colour)
    elif kind == 3:
        f.ink([(x, y - s), (x, y + s * 0.4)], 0.8, colour)
        f.ink([(x - s, y - s * 0.2), (x + s, y - s * 0.2)], 0.8, colour)
        f.ink([(x - s * 0.7, y + s), (x, y + s * 0.4), (x + s * 0.7, y + s)], 0.8, colour)
    else:
        f.ink(K.ellipse_points(x, y, s, s, 10) + [K.ellipse_points(x, y, s, s, 10)[0]], 0.8, colour)
        f.ink([(x - s, y), (x + s, y)], 0.7, colour)
        f.ink([(x, y - s), (x, y + s)], 0.7, colour)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    rng = random.Random(f"indus_unicorn:{anim}:{i}")

    dx, dy, tilt, pitch, swish = 0.0, 0.0, 0.0, 0.0, 0.0
    gait, gait_amp, paw, toss, eyes, fade = 0.0, 0.0, 0.0, 0.0, "open", 1.0
    speed, alarm, chips, flat = 0.0, False, 0.0, 0.0
    if anim == "idle":
        swish = math.sin(cyc)
        pitch = 4.0 + 3.0 * math.sin(cyc)
        dy = 0.5 * math.sin(cyc)
    elif anim == "walk":
        # A stiff walk: the legs swing, the body hardly bobs.
        gait, gait_amp = cyc, 1.0
        dy = -0.8 * abs(math.sin(cyc * 2.0))
        pitch = 3.0 + 2.0 * math.sin(cyc * 2.0)
        swish = 0.5 * math.sin(cyc + 1.0)
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        pitch, eyes, alarm = -14.0 * k, "wide", True
    elif anim == "windup":
        pitch, tilt, dx = 20.0, 2.0, -5.0
        paw = math.sin(cyc * 2.0)
        eyes = "narrow"
    elif anim == "attack_side":
        u = min(1.0, t * 1.25)
        dx = -5.0 + 14.0 * math.sin(math.pi * 0.5 * u) - 6.0 * max(0.0, u - 0.7) / 0.3
        toss = max(0.0, math.sin(math.pi * (u - 0.4) / 0.6)) if u > 0.4 else 0.0
        pitch = 20.0 * (1.0 - u) + 4.0 * u - 40.0 * toss
        tilt = 2.0 - 6.0 * toss
        gait, gait_amp = cyc * 1.5, 1.3 * (1.0 - toss * 0.5)
        speed = math.sin(math.pi * min(1.0, u * 1.5))
        eyes = "narrow"
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        pitch, dx, tilt, eyes, chips = -16.0 * k, -5.0 * k, -2.0 * k, "shut", k
    elif anim == "death":
        # It cracks, and sinks back into a flat seal.
        flat = min(1.0, t * 1.25)
        eyes, chips = "shut", 1.0
        fade = 1.0 - max(0.0, t - 0.8) / 0.2

    if flat > 0.0:
        _draw_seal(f, flat, t)
        return f.finish(outline=A.SEPIA_INK, width=1.4, fade=fade)

    dx -= 2.0
    shoulder = (98.0 + dx, 66.0 + dy)

    def B(pts: Sequence[Point]) -> List[Point]:
        return K.turn([(x + dx, y + dy) for x, y in pts], shoulder[0], shoulder[1], tilt)

    sh_w = B([(98.0, 66.0)])[0]
    hp_w = B([(46.0, 64.0)])[0]

    def leg(root: Point, phase: float, front: bool, near: bool) -> None:
        colour = STONE if near else STONE_SHADE
        swing = math.sin(phase) * gait_amp
        lift = max(0.0, math.cos(phase)) * 5.0 * gait_amp
        fx = root[0] + 9.0 * swing + (1.5 if front else -1.5)
        fy = GROUND - 3.0 - lift
        if front and near and paw:
            fx = root[0] + 5.0 * paw
            fy = GROUND - 3.0 - 7.0 * max(0.0, math.sin(cyc * 2.0 + 0.6))
        knee, foot = S.joint(root, (fx, fy), UPPER, LOWER, -1.0 if front else 1.0)
        f.limb([root, knee], 8.0 if front else 9.0, colour)
        f.limb([knee, foot], 5.4, colour)
        hx, hy = foot
        f.poly([(hx - 3.6, hy - 2.4), (hx + 3.6, hy - 2.4), (hx + 4.6, hy + 2.6), (hx - 3.6, hy + 2.6)], HOOF)
        f.ink([(hx + 0.6, hy), (hx + 0.6, hy + 2.6)], 0.6, STONE_SHADE)
        # A cut line at the knee, as a carver marks a joint.
        f.ink([(knee[0] - 2.4, knee[1]), (knee[0] + 2.4, knee[1] + 0.6)], 0.7, CUT)

    leg((hp_w[0] + 4.0, hp_w[1] + 6.0), gait + math.pi, False, False)
    leg((sh_w[0] - 3.0, sh_w[1] + 8.0), gait, True, False)

    # The tail: long and thin, with a tuft, as on the seals.
    rump = B([(32.0, 54.0)])[0]
    tail = [rump, (rump[0] - 5.0, rump[1] + 12.0), (rump[0] - 6.0 + 3.0 * swish, rump[1] + 26.0), (rump[0] - 4.0 + 5.0 * swish, rump[1] + 38.0)]
    f.limb(tail, 2.6, STONE)
    tx, ty = tail[-1]
    f.poly([(tx - 2.6, ty - 3.0), (tx + 2.6, ty - 3.0), (tx + 3.4 + 1.6 * swish, ty + 6.0), (tx - 3.4 + 1.6 * swish, ty + 6.4)], STONE_SHADE)
    f.ink([(tx - 1.0, ty - 1.0), (tx - 1.4 + swish, ty + 5.0)], 0.6, CUT)
    f.ink([(tx + 1.0, ty - 1.0), (tx + 1.6 + swish, ty + 5.0)], 0.6, CUT)

    # The body: a lean bull, the back level, the belly a little deep.
    body = B([(32.0, 56.0), (40.0, 50.0), (64.0, 50.0), (88.0, 48.0), (102.0, 50.0), (110.0, 60.0), (110.0, 76.0), (100.0, 88.0),
              (80.0, 90.0), (60.0, 90.0), (42.0, 86.0), (32.0, 76.0), (29.0, 64.0)])
    f.poly(body, STONE)
    f.poly(B([(42.0, 84.0), (60.0, 88.0), (80.0, 88.0), (100.0, 86.0), (98.0, 89.0), (80.0, 91.0), (60.0, 91.0), (42.0, 87.0)]), STONE_SHADE, body=False)
    f.poly(B([(31.0, 60.0), (38.0, 54.0), (50.0, 58.0), (50.0, 78.0), (38.0, 82.0)]), STONE_SHADE, body=False)
    # The two square seal marks on its side, with signs in them.
    for k, (sx, sy) in enumerate(((58.0, 62.0), (76.0, 64.0))):
        sq = B([(sx - 7.0, sy - 7.0), (sx + 7.0, sy - 7.0), (sx + 7.0, sy + 7.0), (sx - 7.0, sy + 7.0)])
        f.poly(sq, K.shade(STONE, 0.94), body=False)
        f.ink(sq + [sq[0]], 0.9, CUT)
        c = B([(sx, sy)])[0]
        _sign(f, (k * 2 + (0 if anim != "hit" else 1)) % 5, c[0] - 2.4, c[1], 2.0, CUT)
        _sign(f, (k * 2 + 1) % 5 + 2 if k == 0 else 4, c[0] + 2.6, c[1], 2.0, CUT)
    # The harness over the shoulders: a carnelian band with faience beads.
    band = B([(90.0, 49.0), (98.0, 49.0), (104.0, 86.0), (96.0, 88.0)])
    f.poly(band, HARNESS, body=False)
    f.ink([band[0], band[3]], 0.8, HARNESS_DARK)
    f.ink([band[1], band[2]], 0.8, HARNESS_DARK)
    for k in range(5):
        u = (k + 0.5) / 5.0
        bx = band[0][0] + (band[3][0] - band[0][0]) * u + 3.6
        by = band[0][1] + (band[3][1] - band[0][1]) * u
        f.dot(bx, by, 1.3, BEAD)

    leg((hp_w[0] - 2.0, hp_w[1] + 9.0), gait, False, True)
    leg((sh_w[0] + 3.0, sh_w[1] + 10.0), gait + math.pi, True, True)

    # The neck and the head: turned by `pitch` (down is positive) about the
    # neck. The neck has the folds of the seals.
    neck = B([(104.0, 56.0)])[0]
    pr = pitch + tilt

    def Hd(pts: Sequence[Point]) -> List[Point]:
        return K.turn([(neck[0] + x, neck[1] + y) for x, y in pts], neck[0], neck[1], pr)

    f.poly(Hd([(-6.0, -6.0), (10.0, -11.0), (18.0, -8.0), (18.0, 8.0), (8.0, 26.0), (-4.0, 24.0)]), STONE)
    for k in range(3):
        a, b = Hd([(3.0 + k * 4.0, -8.0 + k * 0.6)])[0], Hd([(1.0 + k * 3.4, 18.0 - k * 1.4)])[0]
        f.ink([a, ((a[0] + b[0]) / 2.0 + 1.6, (a[1] + b[1]) / 2.0), b], 0.8, CUT)
    head = Hd([(12.0, -12.0), (20.0, -14.0), (28.0, -9.0), (35.0, -3.0), (37.0, 3.0), (31.0, 7.0), (21.0, 7.0), (13.0, 3.0)])
    f.poly(head, STONE)
    f.poly(Hd([(30.0, -3.0), (35.0, -2.0), (37.0, 3.0), (31.0, 7.0), (27.0, 4.0)]), STONE_SHADE, body=False)
    nx, ny = Hd([(34.6, 1.0)])[0]
    f.dot(nx, ny, 0.9, CUT)
    f.ink(Hd([(29.0, 6.0), (35.0, 5.0)]), 0.7, CUT)
    # The ear, out at the back.
    f.poly(Hd([(14.0, -10.0), (5.0, -15.0), (3.0, -11.0), (10.0, -7.0)]), STONE_SHADE)
    # The eye: a cut almond.
    ex, ey = Hd([(22.0, -5.0)])[0]
    if eyes == "shut":
        f.ink([(ex - 2.4, ey), (ex + 2.4, ey + 0.6)], 1.0, CUT)
    else:
        r = {"open": 1.4, "wide": 2.0, "narrow": 0.9}[eyes]
        f.poly([(ex - 3.0, ey), (ex, ey - r), (ex + 3.0, ey), (ex, ey + r)], A.STEATITE_DARK, body=False)
        f.dot(ex + 0.6, ey, 0.8, A.SEPIA_INK)
        if eyes == "narrow":
            f.ink([(ex - 3.4, ey - 2.4), (ex + 2.6, ey - 1.0)], 1.0, CUT)

    # The horn: one long horn from the brow, forward and up, with rings.
    base = (19.0, -13.0)
    pts = Hd([base, (base[0] + 6.0, base[1] - 4.0), (base[0] + 13.0, base[1] - 6.0), (base[0] + 20.0, base[1] - 10.0), (base[0] + 24.0, base[1] - 16.0)])
    widths = (4.4, 3.6, 2.8, 2.0)
    for k in range(4):
        f.limb([pts[k], pts[k + 1]], widths[k], HORN)
    for k in range(1, 4):
        x, y = pts[k]
        f.ink([(x - 1.4, y - 1.4), (x + 1.0, y + 1.6)], 0.6, STONE_SHADE)

    if paw or speed > 0.1:
        dust = A.SILT
        for k in range(2):
            amount = (0.6 + 0.4 * abs(paw)) if paw else speed
            x0 = sh_w[0] - 4.0 - k * 46.0 - (10.0 if speed else 0.0)
            for q in range(4):
                r = (2.0 + rng.uniform(0.0, 2.6)) * amount
                f.ellipse(x0 + rng.uniform(-8.0, 8.0), GROUND - r * 0.6 - rng.uniform(0.0, 2.0), r, r * 0.75, K.alpha(dust, 0.6), body=False)
    if speed > 0.1:
        for k in range(3):
            y = 58.0 + k * 12.0 + dy
            f.ink([(max(6.0, hp_w[0] - 22.0 - 8.0 * speed), y), (max(6.0, hp_w[0] - 10.0), y)], 1.3, K.alpha(K.WHITE, 0.6 * speed))
    if chips > 0.05:
        # Chips of stone fly off it.
        for k in range(5):
            cx0 = sh_w[0] - 10.0 + rng.uniform(-20.0, 20.0)
            cy0 = 46.0 - 14.0 * chips + rng.uniform(-6.0, 8.0)
            s = rng.uniform(1.4, 2.4)
            f.poly([(cx0 - s, cy0), (cx0, cy0 - s), (cx0 + s, cy0 + s * 0.4)], STONE_SHADE)
    if alarm:
        ax, ay = Hd([(26.0, -34.0)])[0]
        A.alarm_mark(f, min(150.0, ax), max(14.0, ay))
    return f.finish(outline=A.SEPIA_INK, width=1.4, fade=fade)


def _draw_seal(f: K.Frame, u: float, t: float) -> None:
    """The death: the bull goes flat into a square seal on the ground, with
    a crack across it. `u` 0..1 is how far it has gone."""
    cx = 82.0
    side = 34.0 + 10.0 * (1.0 - u)
    lift = 30.0 * (1.0 - u)
    top = GROUND - 8.0 - side * 0.35 * (1.0 - u) - lift
    # The seal stands up at first and tips back flat: its height shrinks.
    h = side * (1.0 - 0.75 * u)
    pts = [(cx - side, top + h), (cx + side, top + h), (cx + side * 0.9, top), (cx - side * 0.9, top)]
    pts = [(x, min(GROUND - 2.0, y + (GROUND - 2.0 - (top + h)) * u)) for x, y in pts]
    f.poly([(x, y + 3.0) for x, y in pts], STONE_DARK)
    f.poly(pts, STONE)
    inset = K.grow(pts, -3.0)
    f.ink(inset + [inset[0]], 0.9, CUT)
    # The little bull carved on the seal, squashed with it.
    my = (pts[0][1] + pts[2][1]) / 2.0
    sy = max(0.2, (pts[0][1] - pts[2][1]) / (2.0 * side))
    f.ink([(cx - 12.0, my + 2.0 * sy), (cx + 8.0, my + 1.0 * sy), (cx + 14.0, my - 5.0 * sy), (cx + 20.0, my - 12.0 * sy)], 1.0, CUT)
    for x in (cx - 10.0, cx - 4.0, cx + 2.0, cx + 6.0):
        f.ink([(x, my + 2.0 * sy), (x, my + 9.0 * sy)], 0.8, CUT)
    # The crack.
    if t > 0.3:
        c = min(1.0, (t - 0.3) / 0.4)
        f.ink([(cx - side * 0.2, pts[2][1]), (cx - side * 0.05, my), (cx + side * 0.2 * c, pts[0][1])], 1.2, A.SEPIA_INK)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
