"""The Driver Ants of the History dimension: a marching column of siafu.

Driver ants (siafu) of the forests of West and Central Africa march in a
long column of many thousands. The column moves as one low body. Small
red-brown workers fill its middle. Soldiers with big heads and long curved
jaws guard its front and its two edges. The column eats what does not move
out of its way, so the people of the forest step aside for it.

This creature is that column, seen from the side: dozens of ants in a long
low band that faces right. When it walks, each ant moves its legs at its
own phase, so the column ripples. When it sees you, the soldiers rear up
with their jaws open. Its windup bunches the front of the column; its
strike is a surge of the front to the right, and the jaws snap shut. A hit
scatters the ants a little. At its death the column breaks up, and the ants
run off in all directions and fade.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A

TARGET_NAME = "driver_ants"
FRAME_SIZE = (192, 64)
ROWS = K.ENEMY_ROWS
#: The ground row of the near edge of the column.
GROUND = 57.0
#: The column at rest runs from REAR to FRONT (frame px).
REAR, FRONT = 24.0, 140.0
#: How far up the far edge of the column is from the near edge.
DEPTH = 12.0
#: How far the front of the column surges in the strike.
REACH = 36.0
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 5.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Driver Ants", "benin_city", "Multileg", "Small", "Light", "Walk", ["ant", "swarm", "bite", "column"],
    "A marching column of African driver ants (siafu) in the History dimension's Benin City: dozens of red-brown "
    "ants in a long low band, big-jawed soldiers at its front and its edges. The front bunches up, surges and bites.",
)

BODY = (150, 62, 36, 255)
BODY_SHADE = (108, 40, 24, 255)
BODY_LIGHT = (198, 108, 66, 255)
SOLDIER = (126, 46, 26, 255)
SOLDIER_HEAD = (104, 34, 20, 255)
JAW = (52, 22, 16, 255)
LEG = (70, 30, 20, 255)
PUPA = (240, 230, 206, 255)

Point = Tuple[float, float]


class Ant:
    """One ant of the column: its place at rest, its depth in the band (0 the
    near edge, 1 the far edge), its size and its kind."""

    def __init__(self, x: float, z: float, size: float, soldier: bool, phase: float, carry: bool, k: int) -> None:
        self.x, self.z, self.size, self.soldier, self.phase, self.carry, self.k = x, z, size, soldier, phase, carry, k


def _column() -> List[Ant]:
    """The ants of the column, the same in every frame. The workers walk in
    three loose files, with a little space round each ant, so each one
    reads; the soldiers are larger and walk at the edges and the front."""
    rng = random.Random("driver_ants:column")
    ants: List[Ant] = []
    k = 0
    for lane, z in enumerate((1.0, 0.5, 0.0)):
        x = REAR + 4.0 + lane * 4.0
        while x < FRONT - 20.0:
            if (lane != 1 and rng.random() < 0.28) or k % 11 == 7:
                soldier = lane != 1 and rng.random() < 0.6
                ants.append(Ant(x, z + rng.uniform(-0.05, 0.05), 1.25 if soldier else rng.uniform(0.85, 0.95), soldier, rng.random(), False, k))
            else:
                ants.append(Ant(x, z + rng.uniform(-0.08, 0.08), rng.uniform(0.85, 0.95), False, rng.random(), k % 7 == 3, k))
            x += rng.uniform(10.5, 13.0) * (0.85 if lane == 1 else 1.0)
            k += 1
    # The soldiers at the front, in a wedge.
    for j, (dx, z) in enumerate(((0.0, 0.5), (-10.0, 0.0), (-10.0, 1.0), (-20.0, 0.5))):
        ants.append(Ant(FRONT - 4.0 + dx, z, 1.4 - 0.04 * j, True, rng.random(), False, 200 + j))
    # Draw the far ants first.
    ants.sort(key=lambda a: -a.z)
    return ants


ANTS = _column()


def _oval(cx: float, cy: float, rx: float, ry: float) -> List[Point]:
    return K.ellipse_points(cx, cy, rx, ry, count=14)


def _ant(f: K.Frame, x: float, y: float, a: Ant, heading: float, rear: float, gait: float, jaw: float, tone: float, mirror: bool = False) -> None:
    """One ant: its thorax at (`x`, `y`), its feet on the row `y` + 2.6 x
    size. `heading` turns the whole ant (0 faces right); `rear` lifts its
    head and thorax about its abdomen; `gait` is the phase of its legs; `jaw`
    opens the jaws of a soldier (0 shut, 1 wide); `tone` darkens the far
    ants (0 near, 1 far); `mirror` makes the ant face left."""
    s = a.size
    body = K.shade(SOLDIER if a.soldier else BODY, 1.0 - 0.18 * tone)
    shade = K.shade(BODY_SHADE, 1.0 - 0.15 * tone)
    leg = LEG
    pivot = (x - 4.6 * s, y)

    def place(points: List[Point], lift: bool = True) -> List[Point]:
        pts = [(x + px * s, y + py * s) for px, py in points]
        if lift and rear:
            pts = K.turn(pts, pivot[0], pivot[1], -rear)
        pts = K.turn(pts, pivot[0], pivot[1], heading) if heading else pts
        return [(2.0 * x - px, py) for px, py in pts] if mirror else pts

    # The legs: three pairs; the far legs are behind the body, the near legs
    # in front of it. A leg swings forward in the air and back on the ground.
    def legs(side: float) -> None:
        for j, root in enumerate((-1.2, 0.0, 1.2)):
            ph = (gait + j * 0.33 + (0.5 if side > 0 else 0.0)) % 1.0
            swing = 1.6 * math.cos(math.tau * ph)
            up = 0.9 * max(0.0, math.sin(math.tau * ph))
            spread = (-1.6, 0.0, 1.8)[j]
            knee = (root + spread * 1.1 + swing * 0.5, -1.8 - up)
            foot = (root + spread * 2.0 + swing * 1.2, 2.6 - up)
            pts = [(root, 0.4)] + [knee, foot]
            pts = [(px, py + (0.0 if side > 0 else -0.5)) for px, py in pts]
            colour = leg if side > 0 else K.shade(leg, 1.25)
            f.limb(place(pts, lift=j < 2), 0.7 * max(s, 0.85), colour, body=False)

    legs(-1.0)
    # The abdomen (gaster), the waist, the thorax and the head.
    f.poly(place([(px, py) for px, py in _oval(-4.6, -0.4, 3.0, 2.2)], lift=False), body)
    f.poly(place([(px, py) for px, py in _oval(-4.2, 0.3, 2.4, 1.3)], lift=False), shade, body=False)
    f.ellipse(*place([(-1.9, -0.2)], lift=False)[0], 0.8 * s, 0.8 * s, body)
    f.poly(place(_oval(0.0, -0.4, 1.9, 1.15)), body)
    if a.soldier:
        head_c, hrx, hry = (3.7, -0.7), 2.5, 2.0
        f.poly(place(_oval(head_c[0], head_c[1], hrx, hry)), K.shade(SOLDIER_HEAD, 1.0 - 0.15 * tone))
        f.poly(place(_oval(head_c[0] - 0.5, head_c[1] - 0.8, 1.2, 0.7)), K.shade(SOLDIER, 1.25), body=False)
        # The long curved jaws: two sickles that cross when shut.
        for sgn in (-1.0, 1.0):
            open_ = 38.0 * jaw * sgn
            base = (head_c[0] + hrx - 0.4, head_c[1] + 0.5 * sgn)
            pts = [base, (base[0] + 2.8, base[1] - 0.4 * sgn), (base[0] + 5.0, base[1] - 0.2 * sgn), (base[0] + 6.2, base[1] + 1.0 * sgn)]
            pts = K.turn(pts, base[0], base[1], -open_)
            f.limb(place(pts), 0.95 * s, JAW if sgn > 0 else K.shade(JAW, 1.5), body=False)
    else:
        head_c = (2.9, -0.6)
        f.poly(place(_oval(head_c[0], head_c[1], 1.5, 1.3)), body)
        f.limb(place([(head_c[0] + 1.3, head_c[1] + 0.2), (head_c[0] + 2.6, head_c[1] + 0.4)]), 0.5 * s, JAW, body=False)
    # The light on the back of the gaster and the thorax.
    f.ellipse(*place([(-5.0, -1.4)], lift=False)[0], 1.4 * s, 0.6 * s, K.shade(BODY_LIGHT, 1.0 - 0.2 * tone))
    # The antennae, elbowed, forward and up.
    tip_h = 3.0 + 1.0 * jaw
    f.limb(place([(head_c[0] + 0.4, head_c[1] - 1.0), (head_c[0] + 1.0, head_c[1] - tip_h), (head_c[0] + 3.0, head_c[1] - tip_h - 0.8)]), 0.4 * s, leg,
           body=False)
    if a.carry:
        # A white pupa, carried in the jaws to the new nest.
        f.poly(place(_oval(head_c[0] + 3.2, head_c[1] + 0.4, 2.0, 1.2)), PUPA)
    legs(1.0)


def _clamp(x: float, y: float, reach: float) -> Point:
    """Keep an ant `reach` px long inside the frame, with its feet over
    the ground row."""
    return (min(FRAME_SIZE[0] - MARGIN - reach, max(MARGIN + reach, x)), min(GROUND, max(MARGIN + 14.0, y)))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    fade = 1.0
    snap = False
    alarm = False
    front_x = FRONT
    for a in ANTS:
        along = (a.x - REAR) / (FRONT - REAR)
        x, y = a.x, GROUND - a.z * DEPTH
        heading, rear, jaw = 0.0, 0.0, 0.25 if a.soldier else 0.0
        gait = a.phase
        mirror = False
        if anim == "idle":
            # The column marks time: legs stir and the soldiers test the air.
            gait = a.phase + 0.25 * math.sin(cyc + a.k)
            y += 0.4 * math.sin(cyc * 2.0 + a.x * 0.2)
            if a.soldier:
                jaw = 0.3 + 0.25 * max(0.0, math.sin(cyc + a.k))
        elif anim == "walk":
            # Each ant walks at its own phase; a slow wave runs down the column.
            gait = a.phase + t * 2.0
            x += 1.2 * math.sin(cyc + a.phase * math.tau)
            y -= 0.7 * max(0.0, math.sin(cyc * 2.0 - a.x * 0.12))
        elif anim == "notice":
            k = math.sin(math.pi * min(1.0, t * 1.3))
            alarm = True
            if a.soldier:
                rear = 38.0 * k * (1.0 if along > 0.75 else 0.6)
                jaw = 0.25 + 0.75 * k
            else:
                gait = a.phase + t
                y -= 0.6 * k
        elif anim == "windup":
            # The front bunches up: the ants behind it close up on it, and
            # the soldiers of the front lift their heads.
            w = max(0.0, along - 0.35) / 0.65
            x = FRONT - (FRONT - a.x) * (1.0 - 0.22 * w) - 3.0 * w
            gait = a.phase + t * 2.0
            x += 0.6 * math.sin(cyc * 2.0 + a.k)
            if a.soldier and along > 0.6:
                rear = 16.0 + 4.0 * math.sin(cyc * 2.0 + a.k)
                jaw = 0.85
            y -= 1.5 * w
        elif anim == "attack_side":
            # The surge: the front runs out by REACH, the rear stays; then
            # the column draws back.
            u = min(1.0, t / 0.45)
            back = max(0.0, (t - 0.6) / 0.4)
            go = math.sin(math.pi * 0.5 * u) * (1.0 - back)
            w = along ** 1.6
            x = a.x + REACH * go * w
            gait = a.phase + t * 3.0
            if a.soldier and along > 0.6:
                jaw = 1.0 if i < 2 else (0.0 if i in (2, 3) else 0.4)
                rear = 10.0 * (1.0 - u) if i < 2 else -4.0 * go
            snap = i in (2, 3)
            front_x = FRONT + REACH * go
        elif anim == "hit":
            k = math.sin(math.pi * (i + 1) / (n + 1))
            rng = random.Random(f"driver_ants:hit:{a.k}")
            ang = rng.uniform(0.0, math.tau)
            x += -5.0 * k + math.cos(ang) * 5.0 * k
            y += math.sin(ang) * 2.5 * k
            heading = rng.uniform(-35.0, 35.0) * k
            gait = a.phase + t
        elif anim == "death":
            # The column breaks up: each ant runs off its own way and fades.
            rng = random.Random(f"driver_ants:death:{a.k}")
            ang = rng.uniform(0.0, math.tau)
            go = (t ** 1.2) * rng.uniform(26.0, 60.0)
            x += math.cos(ang) * go
            y += math.sin(ang) * go * 0.35
            heading = max(-35.0, min(35.0, math.degrees(math.atan2(math.sin(ang) * 0.35, abs(math.cos(ang)))))) * min(1.0, t * 3.0)
            mirror = math.cos(ang) < 0.0 and t > 0.1
            gait = a.phase + t * 4.0
            fade = 1.0 - max(0.0, t - 0.35) / 0.65
        x, y = _clamp(x, y, 11.0 * a.size)
        # A turned ant reaches lower than its feet: lift it to keep the margin.
        y = min(y, GROUND - abs(math.sin(math.radians(heading))) * 8.0 * a.size)
        _ant(f, x, y, a, heading, rear, gait, jaw, a.z, mirror)

    if snap:
        tx, ty = front_x + 7.0, GROUND - 0.45 * DEPTH - 3.0
        for k in range(4):
            ang = math.radians(-70.0 + k * 45.0)
            f.glow_line([(tx + math.cos(ang) * 3.0, ty + math.sin(ang) * 3.0), (min(FRAME_SIZE[0] - 10.0, tx + math.cos(ang) * 7.0), ty + math.sin(ang) * 8.0)],
                        1.3, K.alpha(K.WHITE, 0.9))
    if anim == "hit":
        rng = random.Random(f"driver_ants:hit:{i}")
        for _ in range(5):
            px, py = rng.uniform(60.0, 140.0), GROUND - DEPTH - rng.uniform(4.0, 12.0)
            f.glow_line([(px, py), (px + rng.uniform(-3.0, 3.0), py - 4.0)], 1.1, K.alpha(K.WHITE, 0.7))
    if anim == "death" and 0.1 < t < 0.8:
        A.dust(f, 90.0, GROUND - 2.0, 40.0, min(1.0, (t - 0.1) * 2.5) * (1.0 - t), f"driver_ants:death:{i}")
    if alarm:
        A.alarm_mark(f, FRONT + 4.0, 16.0)
    return A.finish(f, fade=fade, width=0.8)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
