"""The Green Iguana: the big lizard of the forests of Mesoamerica.

A green iguana as long as a child is tall, long and low: a green body on
sprawled legs with long toes and claws, a crest of soft spines from the
neck down the back, and a tail as long again as the rest of it, with dark
bands. It has a blunt head with a big pale round scale on its cheek, and a
dewlap of skin under its chin.

It walks with a sway, its tail behind it on the ground. When it sees you it
lifts its head and spreads its dewlap. Its windup is the threat display of
an iguana: it stands high on its front legs, bobs its head, spreads its
dewlap wide and cocks its tail up behind it. Its strike is a tail whip: it
ducks its head and the tail cracks over its back and down in front of its
nose. A hit makes it flinch; at its death it sinks flat and lies still.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _stage_kit as S

TARGET_NAME = "green_iguana"
FRAME_SIZE = (192, 96)
ROWS = K.ENEMY_ROWS
GROUND = 91.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Green Iguana", "maya_city", "Quadruped", "Standard", "Medium", "Walk", ["lizard", "iguana", "tail_whip"],
    "A big green iguana of the History dimension's Caribbean and Maya forest, with a crest of spines and a dewlap. "
    "It stands high, bobs its head and cocks its tail, then whips the tail over its back at you.",
)

GREEN = (126, 182, 74, 255)
GREEN_SHADE = (86, 138, 56, 255)
GREEN_DARK = (52, 92, 44, 255)
GREEN_LIGHT = (186, 216, 116, 255)
BAND = (62, 84, 50, 255)
BELLY = (204, 220, 150, 255)
CHEEK = (226, 232, 198, 255)
CREST = (214, 222, 142, 255)
DEWLAP = (170, 206, 104, 255)
EYE = (232, 162, 48, 255)
MOUTH = (186, 86, 86, 255)
CLAW = (64, 54, 44, 255)

Point = Tuple[float, float]

#: The body from the neck back to the hips (x, y, half the depth there).
#: The head is drawn at the front of it and the tail goes back from its end.
BODY = [(150.0, 60.0, 8.0), (140.0, 60.0, 11.0), (128.0, 60.5, 13.0), (116.0, 61.5, 12.5), (106.0, 63.0, 10.0)]
SHOULDER_K, HIP_K = 1, 4
#: The tail: eight pieces, each at an angle (degrees on the screen: 180
#: points back, 270 up, 360 forward). These are its key poses.
TAIL_N = 8
TAIL_REST = [152.0, 160.0, 167.0, 173.0, 177.0, 180.0, 181.0, 181.0]
TAIL_COCKED = [212.0, 228.0, 244.0, 258.0, 272.0, 290.0, 312.0, 334.0]
TAIL_OVER = [258.0, 276.0, 296.0, 316.0, 336.0, 354.0, 14.0, 34.0]
TAIL_FORWARD = [270.0, 292.0, 316.0, 340.0, 4.0, 26.0, 46.0, 62.0]
TAIL_DOWN = [214.0, 236.0, 262.0, 292.0, 322.0, 346.0, 8.0, 26.0]
TAIL_SEG = 12.0
#: The size of the head.
HEAD = 1.0


def _chain(base: Point, angles: Sequence[float], seg: float) -> List[Point]:
    pts = [base]
    x, y = base
    for a in angles:
        x += math.cos(math.radians(a)) * seg
        y += math.sin(math.radians(a)) * seg
        pts.append((x, y))
    return pts


def _offsets(pts: Sequence[Point], widths: Sequence[float]) -> Tuple[List[Point], List[Point]]:
    """The two edges of a tapered strip round the line `pts`."""
    left, right = [], []
    for k, (x, y) in enumerate(pts):
        a = pts[max(0, k - 1)]
        b = pts[min(len(pts) - 1, k + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d, dx / d
        left.append((x + nx * widths[k], y + ny * widths[k]))
        right.append((x - nx * widths[k], y - ny * widths[k]))
    return left, right


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)

    dx, rear, head_up, jaw, dew, eyes, walk, flat, fade, alarm = 0.0, 0.0, 0.0, 0.0, 0.25, "open", None, 0.0, 1.0, False
    tail = list(TAIL_REST)
    seg = TAIL_SEG
    tail_front, crack = False, 0.0
    if anim == "idle":
        head_up = 1.5 * math.sin(cyc)
        dew = 0.25 + 0.15 * max(0.0, math.sin(cyc * 2.0))
        tail = [a + (k / TAIL_N) ** 2 * 6.0 * math.sin(cyc) for k, a in enumerate(TAIL_REST)]
        eyes = "shut" if i == 3 else "open"
    elif anim == "walk":
        walk = t
        tail = [a + 7.0 * (k / TAIL_N) * math.sin(cyc - k * 0.7) for k, a in enumerate(TAIL_REST)]
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        head_up, dew, eyes, alarm, rear = 10.0 * k, 0.3 + 0.7 * k, "wide", True, 0.4 * k
        tail = [a + (b - a) * 0.25 * k for a, b in zip(TAIL_REST, TAIL_COCKED)]
    elif anim == "windup":
        # The threat display: high on its front legs, head bobbing, dewlap
        # out, tail cocked behind.
        rear = 1.0
        head_up = 4.0 + 6.0 * math.sin(cyc * 2.0)
        dew, eyes, dx = 1.0, "narrow", -3.0
        tail = [a + (k / TAIL_N) * 6.0 * math.sin(cyc * 2.0) for k, a in enumerate(TAIL_COCKED)]
        seg = TAIL_SEG * 0.86
    elif anim == "attack_side":
        # The whip: the tail goes over the back and cracks down in front of
        # the nose, and the head ducks under it.
        tail = A.keyed([TAIL_COCKED, TAIL_OVER, TAIL_FORWARD, TAIL_FORWARD, TAIL_DOWN, TAIL_REST], t)
        # The whip stretches as it cracks.
        seg = TAIL_SEG * (0.86 + 0.3 * math.sin(math.pi * min(1.0, t / 0.9)))
        tail_front = t < 0.9
        duck = math.sin(math.pi * min(1.0, t / 0.85))
        head_up = -12.0 * duck
        rear = max(0.0, 1.0 - t * 2.5)
        dx = -3.0 - 6.0 * duck
        dew, eyes = 0.6, "narrow"
        crack = 1.0 if 0.35 < t < 0.75 else 0.0
    elif anim == "hit":
        k = math.sin(math.pi * t)
        dx, head_up, jaw, eyes = -5.0 * k, 8.0 * k, 0.5 * k, "shut"
        tail = [a + (b - a) * 0.2 * k for a, b in zip(TAIL_REST, TAIL_COCKED)]
    elif anim == "death":
        u = min(1.0, t / 0.8)
        flat, eyes, head_up, dew = u, "shut", -4.0 * u, 0.25 * (1.0 - u)
        tail = [a + (180.0 - a) * u * 0.6 for a in TAIL_REST]
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # The body of this frame: moved, its front lifted by the rear.
    hip_x = BODY[HIP_K][0]
    body: List[Tuple[float, float, float]] = []
    for k, (x, y, r) in enumerate(BODY):
        x += dx
        y += 5.0 * flat
        if rear:
            y -= rear * 0.34 * (x - hip_x - dx)
        if walk is not None:
            y -= 1.0 * abs(math.sin(math.tau * walk * 2.0))
        body.append((x, y, r * (1.0 - 0.15 * flat)))

    def normal(k: int) -> Point:
        a = body[max(0, k - 1)]
        b = body[min(len(body) - 1, k + 1)]
        dxs, dys = a[0] - b[0], a[1] - b[1]
        d = math.hypot(dxs, dys) or 1.0
        return (-dys / d, dxs / d)

    def top_of(k: int, s: float = 1.0) -> Point:
        x, y, r = body[k]
        nx, ny = normal(k)
        return (x - nx * r * s, y - ny * r * s)

    def bottom_of(k: int, s: float = 1.0) -> Point:
        x, y, r = body[k]
        nx, ny = normal(k)
        return (x + nx * r * s * 0.9, y + ny * r * s * 0.9)

    # The tail: a chain from the hips, tapered, with dark bands.
    hx, hy, hr = body[HIP_K]
    chain = _chain((hx + 2.0, hy + 1.0), tail, seg)
    chain = [(x, max(7.0, min(GROUND - 3.0, y))) for x, y in chain]
    widths = [9.0 * (1.0 - k / TAIL_N) ** 0.9 + 1.0 for k in range(TAIL_N + 1)]

    def draw_tail() -> None:
        left, right = _offsets(chain, widths)
        tip = chain[-1]
        a = chain[-2]
        d = math.hypot(tip[0] - a[0], tip[1] - a[1]) or 1.0
        end = (tip[0] + (tip[0] - a[0]) / d * 4.0, tip[1] + (tip[1] - a[1]) / d * 4.0)
        f.poly(left + [end] + right[::-1], GREEN)
        f.poly(left[: TAIL_N] + [chain[k] for k in range(TAIL_N - 1, -1, -1)], K.alpha(GREEN_SHADE, 0.55), body=False)
        for k in range(2, TAIL_N, 1):
            if k % 2:
                continue
            u0 = 0.15
            pa = A.lerp(left[k], left[k + 1], u0)
            pb = A.lerp(left[k], left[k + 1], u0 + 0.45)
            qa = A.lerp(right[k], right[k + 1], u0)
            qb = A.lerp(right[k], right[k + 1], u0 + 0.45)
            f.poly([pa, pb, qb, qa], BAND, body=False)
        # The crest goes on a little way down the tail.
        for k in range(0, 3):
            p = A.lerp(chain[k], chain[k + 1], 0.5)
            e = A.lerp(right[k], right[k + 1], 0.5)
            nx, ny = e[0] - p[0], e[1] - p[1]
            d2 = math.hypot(nx, ny) or 1.0
            h = 3.4 - k * 0.9
            base_a = A.lerp(right[k], right[k + 1], 0.25)
            base_b = A.lerp(right[k], right[k + 1], 0.75)
            f.poly([base_a, (e[0] + nx / d2 * h, e[1] + ny / d2 * h), base_b], CREST)

    def leg(k: int, ph: float, front: bool, near: bool) -> None:
        colour = GREEN if near else GREEN_SHADE
        root = (body[k][0] + (2.0 if near else -3.0), body[k][1] + 6.0)
        fx = root[0] + (5.0 if front else -4.0)
        fy = GROUND - 2.5
        if walk is not None:
            gx, gy = A.gait(ph, 16.0, 5.0)
            fx += gx
            fy += gy
        if flat:
            fx += (9.0 if front else -9.0) * flat
        # A sprawled leg: the elbow sticks out above the body line.
        elbow, foot = S.joint(root, (fx, fy), 12.0, 13.0, 1.0 if front else -1.0)
        elbow = (elbow[0], min(elbow[1], GROUND - 6.0))
        f.limb([root, elbow], 8.0, colour)
        f.limb([elbow, foot], 5.5, colour)
        # The long toes, splayed, with dark claws.
        for c in range(4):
            ang = math.radians((-14.0 + c * 10.0) if front else (194.0 - c * 12.0 if c < 2 else -10.0 + (c - 2) * 12.0))
            ln = 6.0 + (c % 3) * 1.6
            tip = (foot[0] + math.cos(ang) * ln, min(GROUND - 0.8, foot[1] + 1.4 + math.sin(ang) * ln * 0.3))
            f.limb([(foot[0], foot[1] + 0.8), tip], 1.7, colour)
            if near:
                f.ink([tip, (tip[0] + (1.6 if math.cos(ang) > 0 else -1.6), tip[1] + 0.8)], 0.8, CLAW)

    ph = walk or 0.0
    if not tail_front:
        draw_tail()
    leg(SHOULDER_K, ph + 0.5, True, False)
    leg(HIP_K, ph, False, False)

    # The body: one shape round the body line, with its belly and its back.
    upper = [top_of(k) for k in range(len(body))]
    lower = [bottom_of(k) for k in range(len(body))]
    f.poly(upper + [(hx - 4.0, hy + 1.0)] + lower[::-1], GREEN)
    f.poly([bottom_of(k, 0.45) for k in range(len(body))] + [bottom_of(k) for k in range(len(body) - 1, -1, -1)], BELLY, body=False)
    f.poly([top_of(k) for k in range(len(body))] + [top_of(k, 0.5) for k in range(len(body) - 1, -1, -1)], GREEN_LIGHT, body=False)
    # Faint stripes down the flank, and rows of small scales.
    for k in range(1, len(body) - 1):
        a, b = top_of(k, 0.4), bottom_of(k, 0.3)
        f.ink([a, A.lerp(a, b, 0.8)], 1.6, K.alpha(GREEN_SHADE, 0.7))
    for k in range(len(body) - 1):
        x, y = A.lerp(top_of(k, 0.0), bottom_of(k, 0.2), 0.5)
        f.dot(x + 4.0, y, 0.7, GREEN_SHADE)

    # The crest: a row of soft spines along the neck and the back.
    for k in range(len(body)):
        x, y = top_of(k, 0.92)
        h = 7.0 - k * 1.1
        f.poly([(x - 3.2, y + 1.0), (x - 1.0, y - h), (x + 2.6, y + 1.0)], CREST)
        if k < len(body) - 1:
            m = A.lerp(top_of(k, 0.92), top_of(k + 1, 0.92), 0.5)
            hm = h - 0.8
            f.poly([(m[0] - 2.8, m[1] + 1.0), (m[0] - 0.8, m[1] - hm), (m[0] + 2.4, m[1] + 1.0)], CREST)

    leg(SHOULDER_K, ph, True, True)
    leg(HIP_K, ph + 0.5, False, True)

    # The head: blunt, at the front of the neck, turned up by `head_up`.
    nx0, ny0, _ = body[0]
    ang = -head_up - rear * 12.0

    def Hd(*pts: Point) -> List[Point]:
        return K.turn([(nx0 + x * HEAD, ny0 + y * HEAD) for x, y in pts], nx0, ny0, ang)

    # The dewlap: a flap of skin under the chin, spread wide in a display.
    dl = 4.0 + 12.0 * dew
    f.poly(Hd((20.0, 6.0), (16.0, 8.0 + dl * 0.5), (8.0, 8.0 + dl), (1.0, 8.0 + dl * 0.7), (-3.0, 7.0)), DEWLAP)
    f.ink(Hd((17.0, 8.0), (8.0, 7.0 + dl * 0.8), (2.0, 8.0 + dl * 0.5)), 0.8, GREEN_SHADE)
    for c in range(3):
        f.dot(*Hd((14.0 - c * 4.0, 8.0 + dl * (0.4 + c * 0.15)))[0], 0.8, GREEN_LIGHT)
    hinge = Hd((8.0, 3.0))[0]
    gape = 26.0 * jaw
    if jaw > 0.05:
        f.poly([Hd((8.0, 2.0))[0], Hd((26.0, 2.0))[0]] + K.turn(Hd((26.0, 4.0), (10.0, 5.0)), hinge[0], hinge[1], gape), MOUTH, body=False)
    f.poly(K.turn(Hd((4.0, 2.0), (26.0, 2.6), (24.0, 6.0), (10.0, 8.0), (2.0, 7.0)), hinge[0], hinge[1], gape), GREEN)
    f.poly(Hd((-4.0, -8.0), (6.0, -10.0), (16.0, -9.0), (24.0, -6.0), (28.0, -2.0), (28.0, 2.0), (12.0, 3.0), (0.0, 6.0), (-6.0, 4.0)), GREEN)
    f.poly(Hd((-2.0, -7.0), (8.0, -9.0), (18.0, -8.0), (12.0, -6.0)), GREEN_LIGHT, body=False)
    f.ink(Hd((12.0, 2.6), (27.4, 1.6)), 0.9, GREEN_DARK)
    f.dot(*Hd((25.0, -3.0))[0], 0.9, GREEN_DARK)
    # The big round scale on the cheek, below the ear.
    cx, cy = Hd((5.0, 0.6))[0]
    f.ellipse(cx, cy, 3.4, 3.4, CHEEK)
    f.ellipse(cx + 0.6, cy - 0.6, 1.0, 1.0, K.alpha(K.WHITE, 0.7), body=False)
    ex, ey = Hd((15.0, -4.4))[0]
    if eyes == "shut":
        f.ink([(ex - 2.2, ey), (ex + 2.2, ey + 0.3)], 1.0, A.SEPIA_INK)
    else:
        r = {"open": 1.8, "wide": 2.3, "narrow": 1.1}[eyes]
        f.ellipse(ex, ey, 2.3, r, EYE, body=False)
        f.ellipse(ex + 0.4, ey, 0.8, min(r, 1.5), A.SEPIA_INK, body=False)
        if eyes == "narrow":
            f.ink([(ex - 2.8, ey - 2.2), (ex + 2.4, ey - 1.0)], 1.0, A.SEPIA_INK)

    if tail_front:
        draw_tail()
    if crack:
        # The crack of the whip: short lines round the tip of the tail.
        tx, ty = chain[-1]
        for c in (-1.0, 0.0, 1.0):
            f.glow_line([(min(184.0, tx + 4.0), ty + 2.0 + c * 4.0), (min(186.0, tx + 9.0), ty + 3.0 + c * 7.0)], 1.2, K.alpha(K.WHITE, 0.85))
    if anim == "death" and t > 0.3:
        A.dust(f, 110.0, GROUND - 4.0, 34.0, min(1.0, (t - 0.3) * 2.0), f"green_iguana:death:{i}")
    if alarm:
        hx2, hy2 = Hd((16.0, -12.0))[0]
        A.alarm_mark(f, min(182.0, hx2 + 6.0), max(17.0, hy2 - 14.0))
    return A.finish(f, fade=fade, width=1.4)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
