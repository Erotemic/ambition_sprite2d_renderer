"""The Moa of the History dimension: the giant moa of Aotearoa.

The giant moa (Dinornis) was the tallest bird that ever lived: with its
neck up it stood about 3.6 m tall, and the females were much bigger than
the males. It had no wings at all, not even small bones of them. Coarse
red-brown feathers like hair hung over its body and its long neck; its
head was small and flat, with a short, broad beak for leaves and twigs.
Its legs were massive, and its feet had three thick toes. It had no enemy
but Haast's eagle until people came to Aotearoa, about 1300; within about
150 years all nine kinds of moa were gone.

It browses and sways its neck. It walks with long slow steps. When it sees
you it lifts its neck high. Its windup lowers its head and neck at you and
draws one leg up under its chest; its strike is the kick: the leg shoots
forward, toes first, under the lowered head. A hit throws its head back
and ruffles its plumage; at its death it sinks onto its belly and its
neck droops to the ground.

The frame is 352 by 320 px. The bird is drawn in small units and made
`SIZE` times larger about its foot, so that its neck up reaches about
274 px above the ground row (3.6 m at 76 px a metre, the scale of the
residents).
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _stage_kit as S

TARGET_NAME = "moa"
FRAME_SIZE = (352, 320)
ROWS = K.ENEMY_ROWS
GROUND = 314.0
#: The bird is drawn in small units and made this much larger about `PIVOT`.
SIZE = 1.7
PIVOT = (152.0, GROUND)

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Moa", "aotearoa", "Biped", "Large", "Heavy", "Walk", ["bird", "ratite", "moa", "kick"],
    "The giant moa of the History dimension's Aotearoa, the tallest bird that ever lived: about 3.6 m with its neck up, "
    "no wings at all, coarse red-brown plumage like hair, a small flat head and massive legs. It lowers its head and "
    "neck at you, draws one leg up, and kicks forward with its great three-toed foot.",
)

PLUME = (128, 86, 54, 255)
PLUME_SHADE = (88, 58, 38, 255)
PLUME_LIGHT = (176, 130, 86, 255)
#: The pale tips of the long feathers.
PLUME_TIP = (204, 168, 118, 255)
LEG = (134, 126, 110, 255)
LEG_SHADE = (100, 94, 82, 255)
CLAW = (72, 62, 54, 255)
BEAK = (216, 198, 152, 255)
BEAK_SHADE = (166, 146, 106, 255)
EYE = (70, 44, 28, 255)
GLINT = (236, 226, 200, 255)

Point = Tuple[float, float]
#: The size of the body against the legs.
BODY = 1.3
#: The lengths of the two parts of the neck (units).
NECK_LOW, NECK_HIGH = 32.0, 33.0


def _egg() -> List[Point]:
    """The top of the body (units, about its middle): the arc of an egg
    from the low rump, over the back, to the deep breast. The fringe of
    long feathers closes it below."""
    pts = []
    for k in range(15):
        a = math.radians(150.0 + 240.0 * k / 14.0)
        x, y = math.cos(a) * 29.0, math.sin(a) * 20.0
        # The back rises to the shoulders; the rump hangs low.
        y += -3.0 * max(0.0, math.cos(a)) * (1.0 if y < 0 else 0.0) + 4.0 * max(0.0, -math.cos(a)) * (1.0 if y > 0 else 0.4)
        pts.append((x, y - 2.0))
    return pts


def _curve(a: Point, b: Point, c: Point, steps: int = 10) -> List[Point]:
    """A smooth curve from `a` to `c`, pulled toward `b`."""
    out = []
    for k in range(steps + 1):
        u = k / steps
        out.append(((1 - u) ** 2 * a[0] + 2 * u * (1 - u) * b[0] + u * u * c[0], (1 - u) ** 2 * a[1] + 2 * u * (1 - u) * b[1] + u * u * c[1]))
    return out


def _tube(spine: List[Point], w0: float, w1: float, side: int = 0, inner: float = 1.0) -> List[Point]:
    """A shape round the curve `spine` whose half width goes from `w0` to
    `w1`. `side` 0 gives both sides; 1 or -1 gives one side only, from the
    curve out to `inner` of the half width."""
    left, right = [], []
    n = len(spine)
    for k, (x, y) in enumerate(spine):
        x0, y0 = spine[max(0, k - 1)]
        x1, y1 = spine[min(n - 1, k + 1)]
        ln = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = (y1 - y0) / ln, -(x1 - x0) / ln
        w = w0 + (w1 - w0) * k / (n - 1)
        if side == 0:
            left.append((x + nx * w, y + ny * w))
            right.append((x - nx * w, y - ny * w))
        else:
            left.append((x - side * nx * w, y - side * ny * w))
            right.append((x - side * nx * w * (1.0 - inner), y - side * ny * w * (1.0 - inner)))
    return left + right[::-1]


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"moa:{anim}:{i}")
    f = A.ScaledFrame(FRAME_SIZE, SIZE, PIVOT)

    # The pose. `dx`/`dy` move the body; `lean` turns it (degrees, + is
    # nose down); `neck_lean` turns the neck forward (+) or back (-);
    # `head_pitch` turns the head (+ is beak down); `walk` is the phase of
    # the gait; `chamber` draws the near leg up; `kick` sends it forward;
    # `sink` folds the legs under the body.
    dx, dy, lean, neck_lean, head_pitch, walk, kick, chamber, sink, ruffle = 0.0, 0.0, 0.0, 26.0, 8.0, None, 0.0, 0.0, 0.0, 0.0
    eyes, beak, fade, alarm, feathers = "open", 0.0, 1.0, False, 0
    if anim == "idle":
        # It stands and browses: the neck sways forward and back, the beak nibbles.
        neck_lean = 26.0 + 8.0 * math.sin(cyc)
        head_pitch = 10.0 + 8.0 * math.sin(cyc + 0.8)
        beak = 0.3 * max(0.0, math.sin(cyc * 2.0))
        dy = 0.5 * math.sin(cyc * 2.0)
        eyes = "shut" if i == 4 else "open"
    elif anim == "walk":
        walk = t
        dy = -1.6 * abs(math.sin(cyc))
        neck_lean = 30.0 + 5.0 * math.sin(cyc * 2.0)
        lean = 3.0
    elif anim == "notice":
        # It lifts its neck high and looks at you.
        k = math.sin(math.pi * min(1.0, t * 1.3))
        neck_lean, head_pitch, beak, eyes, alarm = 26.0 - 30.0 * k, 8.0 - 12.0 * k, 0.5 * k, "wide", True
        dy = -2.0 * k
        ruffle = 0.5 * k
    elif anim == "windup":
        # The head and neck go down at you; one leg is drawn up under the chest.
        chamber = 0.9 + 0.1 * math.sin(cyc * 2.0)
        neck_lean, head_pitch, lean, eyes = 62.0 + 3.0 * math.sin(cyc * 2.0), 6.0, 2.0, "narrow"
        dy = -1.0
        ruffle = 0.7
    elif anim == "attack_side":
        # The kick under the lowered head: the leg shoots forward, then comes back.
        u = t
        kick = math.sin(math.pi * min(1.0, u * 1.6)) if u < 0.62 else max(0.0, 1.0 - (u - 0.62) / 0.38) * 0.3
        chamber = max(0.0, 1.0 - u * 3.0)
        neck_lean, head_pitch, eyes = 62.0 - 6.0 * kick, 4.0, "narrow"
        lean = -10.0 * kick + 2.0 * chamber
        dx = 6.0 * kick
        dy = -2.0 * kick
        beak = 0.4 * kick
        ruffle = 0.9
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, lean, neck_lean, head_pitch, eyes, ruffle = -4.0 * k, -5.0 * k, 26.0 - 30.0 * k, -14.0 * k, "shut", k
        beak = 0.6 * k
        feathers = 4
    elif anim == "death":
        u = min(1.0, t / 0.8)
        sink = u
        neck_lean, head_pitch, eyes = 26.0 + 70.0 * u, 30.0 * u, "shut"
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    body_c = (PIVOT[0] - 6.0 + dx, GROUND - 68.0 + dy + 30.0 * sink)
    hip = (body_c[0] + 2.0, body_c[1] + 18.0)
    bx, by = body_c

    def Bd(pts):
        return K.turn([(bx + x * BODY, by + y * BODY) for x, y in pts], bx, by, lean)

    def leg(near: bool, ph: float) -> None:
        colour = LEG if near else LEG_SHADE
        thigh = PLUME if near else PLUME_SHADE
        fx, fy = hip[0] + (4.0 if near else -3.0), GROUND - 6.0
        if walk is not None:
            gx, gy = A.gait(ph, 30.0, 12.0)
            fx += gx
            fy += gy
        if near and chamber > kick:
            # The leg drawn up: the foot comes up under the chest.
            fx, fy = hip[0] + 12.0 * chamber, hip[1] + 26.0 - 12.0 * chamber
        if near and kick > chamber:
            fx = hip[0] + 16.0 + 26.0 * kick
            fy = hip[1] + 28.0 - 18.0 * kick
        if sink:
            fx = hip[0] + (10.0 if near else 4.0) * sink
            fy = GROUND - 6.0
        knee, foot = S.joint(hip, (fx, fy), 28.0, 28.0, 1.0)
        knee = (knee[0], min(knee[1], GROUND - 11.0))
        # The feathered drumstick, then the bare scaly shank.
        f.limb([hip, knee], 18.0, thigh)
        f.limb([knee, foot], 10.0, colour)
        for k in range(4):
            x, y = A.lerp(knee, foot, 0.18 + 0.2 * k)
            f.ink([(x + 1.0, y), (x + 3.4, y + 0.6)], 0.6, LEG_SHADE)
        # The three thick forward toes and the small hind toe, with dark claws.
        ang = math.atan2(foot[1] - knee[1], foot[0] - knee[0]) - math.pi / 2.0 if (kick > 0.2 and near) else 0.0
        toes = [(foot[0] + 14.0, foot[1] + 2.0), (foot[0] + 11.0, foot[1] + 4.0), (foot[0] + 6.0, foot[1] + 4.6), (foot[0] - 6.0, foot[1] + 2.4)]
        toes = K.turn(toes, foot[0], foot[1], math.degrees(ang) * 0.6)
        for k, (tx, ty) in enumerate(toes):
            f.limb([foot, (tx, ty)], 4.6 if k < 3 else 3.0, colour)
            if k < 3:
                ux, uy = tx - foot[0], ty - foot[1]
                ln = math.hypot(ux, uy) or 1.0
                f.limb([(tx, ty), (tx + 2.6 * ux / ln, ty + 2.6 * uy / ln)], 1.8, CLAW)

    ph = walk or 0.0
    leg(False, ph + 0.5)

    # The body: a great egg of coarse red-brown plumage like hair, with a
    # long fringe that hangs over the tops of the legs. No wings.
    body = Bd(_egg())
    fringe = []
    for k in range(11):
        u = k / 10.0
        x = 20.0 - 54.0 * u
        y = 17.0 + 9.0 * math.sin(math.pi * u) + (6.0 if k % 2 else 0.0) + 3.0 * ruffle * (1 if k % 2 else -1)
        fringe.append((x, y))
    # The fringe of a bird that lies down rests on the ground.
    f.poly(body + [(x, min(y, GROUND - 6.0)) for x, y in Bd(fringe)], PLUME)
    # The shade of the belly.
    f.poly(Bd([(-30.0, 6.0), (-22.0, 16.0), (-2.0, 24.0), (18.0, 18.0), (26.0, 6.0), (14.0, 13.0), (-4.0, 16.0), (-22.0, 10.0)]), PLUME_SHADE,
           body=False)
    # The long feathers: strokes that run down and back over the body.
    for k in range(10):
        x0 = -26.0 + k * 5.4
        top = -14.0 + abs(k - 4.5) * 1.8
        f.ink(Bd([(x0, top), (x0 - 3.0 - 2.0 * ruffle, top + 14.0), (x0 - 4.0 - 3.0 * ruffle, top + 24.0)]), 0.8, PLUME_LIGHT)
    for k in range(6):
        x0 = 14.0 - k * 8.0
        f.ink(Bd([(x0, 18.0 + 4.0 * math.sin(math.pi * k / 5.0)), (x0 - 1.0, 23.0 + 4.0 * math.sin(math.pi * k / 5.0))]), 0.9, PLUME_TIP)

    leg(True, ph)

    # The neck: long, thick at its base, feathered like the body. It
    # bends in two parts: the low part leans less than the high part.
    base = Bd([(18.0, -14.0)])[0]
    low = neck_lean * 1.1 + lean * 0.5
    high = neck_lean * 0.6 + max(0.0, neck_lean - 40.0) * 1.2 + lean * 0.5
    mid = K.turn([(base[0], base[1] - NECK_LOW)], base[0], base[1], low)[0]
    top = K.turn([(mid[0], mid[1] - NECK_HIGH)], mid[0], mid[1], high)[0]
    # A neck that droops to the ground lies on it.
    mid = (mid[0], min(mid[1], GROUND - 12.0))
    top = (top[0], min(top[1], GROUND - 10.0))
    spine = _curve(base, mid, top)
    f.poly(_tube(spine, 9.0, 5.0), PLUME)
    # The shade along the front of the neck (the throat side).
    f.poly(_tube(spine, 9.0, 5.0, side=1, inner=0.45), PLUME_SHADE, body=False)
    # The shaggy feathers on the neck: short strokes that hang down its back.
    for k in range(1, len(spine) - 2, 2):
        (x0, y0), (x1, y1) = spine[k], spine[k + 1]
        ln = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = (y1 - y0) / ln, -(x1 - x0) / ln
        w = 9.0 - 4.0 * k / len(spine)
        p = (x0 - nx * w * 0.5, y0 - ny * w * 0.5)
        f.ink([p, (p[0] - 3.0 - 1.6 * ruffle, p[1] + 4.0)], 0.8, PLUME_LIGHT)
    # The body's plumage runs over the base of the neck.
    f.ellipse(base[0] - 2.0, base[1] + 4.0, 11.0, 8.0, PLUME)

    # The head: small and flat, with a short, broad, slightly hooked beak.
    pr = head_pitch + (neck_lean - 26.0) * 0.4

    def Hd(*pts: Point) -> List[Point]:
        return K.turn([(top[0] + x, top[1] + y) for x, y in pts], top[0], top[1], pr)

    f.poly(Hd((-6.0, -2.0), (-2.0, -5.4), (5.0, -5.0), (8.0, -1.0), (6.0, 3.0), (-1.0, 4.0), (-6.0, 3.0)), PLUME)
    f.poly(Hd((-6.0, -2.0), (-2.0, -5.4), (3.0, -5.2), (-1.0, -2.6)), PLUME_LIGHT, body=False)
    hinge = Hd((6.0, 1.0))[0]
    f.poly(K.turn(Hd((6.0, 1.0), (13.0, 2.2), (6.6, 3.6)), hinge[0], hinge[1], 22.0 * beak), BEAK_SHADE)
    f.poly(Hd((6.0, -3.6), (11.0, -2.4), (14.0, 0.4), (13.4, 2.4), (6.0, 1.6)), BEAK)
    f.ink(Hd((8.0, -2.6), (8.8, -1.6)), 0.6, BEAK_SHADE)
    ex, ey = Hd((2.0, -1.4))[0]
    if eyes == "shut":
        f.ink([(ex - 1.8, ey), (ex + 1.8, ey + 0.3)], 0.9, A.SEPIA_INK)
    else:
        r = {"open": 1.3, "wide": 1.8, "narrow": 0.8}[eyes]
        f.ellipse(ex, ey, 1.6, r, EYE, body=False)
        f.dot(ex + 0.5, ey - 0.3, 0.4, GLINT)
        if eyes == "narrow":
            f.ink([(ex - 2.2, ey - 2.0), (ex + 2.2, ey - 1.0)], 0.9, A.SEPIA_INK)

    if anim == "attack_side" and 0.15 < t < 0.65:
        # The swish of the kick.
        for k in range(3):
            y = hip[1] + 8.0 + k * 6.0
            f.glow_line([(hip[0] + 26.0, y), (hip[0] + 50.0, y - 3.0)], 1.2, K.alpha(K.WHITE, 0.6))
    for k in range(feathers):
        # Loose feathers knocked out by a hit.
        px = bx + rng.uniform(-24.0, 30.0)
        py = by + rng.uniform(-40.0, 10.0)
        a = rng.uniform(0.0, 180.0)
        quill = K.turn([(px - 4.0, py), (px, py - 1.2), (px + 4.0, py), (px, py + 1.2)], px, py, a)
        f.poly(quill, PLUME_LIGHT if k % 2 else PLUME)
    if anim == "death" and t > 0.3:
        A.dust(f, bx + 4.0, GROUND - 9.0, 30.0, min(1.0, (t - 0.3) * 2.0), f"moa:death:{i}")
    if alarm:
        A.alarm_mark(f, top[0] + 14.0, top[1] - 16.0)
    return A.finish(f, fade=fade, width=1.6)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
