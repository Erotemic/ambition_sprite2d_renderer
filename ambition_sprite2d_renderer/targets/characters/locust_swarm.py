"""The Locust Swarm: a cloud of locusts over the fields of the Fertile Crescent.

Many locusts that fly as one body: Drought and Famine. Each locust is the
yellow of a desert locust, with brown spots, a long body, pale wings that
beat and a bent hind leg. They wheel round a cloud of dust and chaff. In
the middle of the cloud the swarm makes a face: two ember eyes and a mouth
of shadow, and it grins.

It floats and wheels. When it sees you the cloud draws in and the face
glares. Its windup pulls the swarm back into a tight ball that seethes; its
strike throws the swarm forward in a long stream, the face first. A hit
scatters it; at its death the locusts fly apart and fall, and the dust
settles.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_ancient_kit as H

TARGET_NAME = "locust_swarm"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 124.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Locust Swarm", "crescent", "Amorphous", "Standard", "Light", "Float", ["insect", "swarm", "famine"],
    "A cloud of desert locusts of the History dimension's Fertile Crescent that flies as one body and makes a face. "
    "It wheels, pulls itself into a tight ball, then throws itself forward in a long stream.",
)

LOCUST = (222, 188, 76, 255)
LOCUST_SHADE = (168, 128, 44, 255)
LOCUST_FAR = (176, 146, 70, 255)
SPOT = (110, 72, 34, 255)
WING = (246, 236, 200, 255)
HAZE = (150, 116, 70, 255)
EMBER = (255, 132, 40, 255)
EMBER_CORE = (255, 224, 140, 255)

COUNT = 40


def _locust(f: K.Frame, x: float, y: float, heading: float, flap: float, size: float, colour) -> None:
    """One locust at `(x, y)`, its head toward `heading` (radians on the
    screen), its wings at `flap` (0 shut .. 1 open)."""
    c, s = math.cos(heading), math.sin(heading)
    flip = -1.0 if c < 0 else 1.0

    def at(u: float, v: float):
        # `u` along the body (to the head), `v` across it (up is negative).
        return (x + (u * c - v * s * flip) * size, y + (u * s + v * c * flip) * size)

    # The wings: two pale blades over the back, open or shut.
    for k, spread in enumerate((1.0, 0.6)):
        a = 0.25 + 0.9 * flap * spread
        tip = at(-5.0 * math.cos(a), -5.0 * math.sin(a) - 0.6)
        root = at(1.2, -0.8)
        f.poly([root, at(-0.6, -1.4 - 0.4 * k), tip, at(-1.4, -0.2)], K.alpha(WING, 0.85 if k == 0 else 0.65), body=False)
    body = [at(3.6, 0.0), at(2.4, -1.4), at(-1.0, -1.3), at(-4.6, -0.5), at(-4.8, 0.4), at(-1.0, 1.3), at(2.4, 1.3)]
    f.poly(body, colour)
    f.poly([at(-1.0, 0.4), at(-4.6, 0.4), at(-4.8, 0.2), at(-1.0, 1.3)], K.shade(colour, 0.78), body=False)
    f.dot(*at(2.6, -0.2), 0.75 * size, SPOT)
    f.dot(*at(-2.0, -0.5), 0.45 * size, SPOT)
    # The bent hind leg.
    f.limb([at(-0.4, 0.8), at(-2.4, -1.6), at(-4.4, 1.6)], 0.7 * size, K.shade(colour, 0.7))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    rng = random.Random("locust:swarm")

    cx, cy = 62.0, 58.0
    rx, ry, spin, jet, scatter, fall, fade = 44.0, 32.0, 1.0, 0.0, 0.0, 0.0, 1.0
    face, glare, grin, heading_bias, alarm = 1.0, 0.0, 0.5, None, False
    if anim == "idle":
        cy += 2.5 * math.sin(cyc)
    elif anim == "walk":
        cx += 2.0 * math.sin(cyc)
        cy += 1.5 * math.sin(cyc * 2.0)
        rx, ry = 46.0, 28.0
        heading_bias = 0.0
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        rx, ry = 44.0 - 9.0 * k, 32.0 - 6.0 * k
        glare, grin, alarm = k, 0.5 + 0.5 * k, True
    elif anim == "windup":
        cx -= 8.0
        rx, ry = 28.0 + 1.0 * math.sin(cyc * 2.0), 23.0 + 1.0 * math.sin(cyc * 2.0 + 1.0)
        spin, glare, grin = 2.0, 1.0, 1.0
    elif anim == "attack_side":
        # The stream: out (to 0.5), and back into a cloud.
        u = min(1.0, t * 1.2)
        jet = math.sin(math.pi * u)
        cx += -8.0 + 14.0 * u
        rx, ry = 28.0 + 14.0 * u, 23.0 + 8.0 * u
        spin, glare, grin, heading_bias = 2.0, 1.0, 1.0, 0.0
    elif anim == "hit":
        k = math.sin(math.pi * t)
        scatter, face, glare = 0.6 * k, 1.0 - 0.7 * k, 0.0
        cx -= 4.0 * k
    elif anim == "death":
        scatter = 0.9 * t
        fall = t
        face = max(0.0, 1.0 - t * 2.5)
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    # The cloud of dust and chaff the swarm carries.
    haze = K.alpha(HAZE, 0.28 * (1.0 - fall))
    if haze[3] > 4:
        hx = cx + 10.0 * jet
        f.poly(K.ellipse_points(hx, cy, rx * (0.9 + 0.5 * jet), ry * 0.85, 24, 2.5, random.Random(f"haze:{anim}:{i}")), haze, body=False)
        f.poly(K.ellipse_points(hx + 2.0, cy + 2.0, rx * (0.55 + 0.4 * jet), ry * 0.5, 20), K.alpha(HAZE, 0.25 * (1.0 - fall)), body=False)

    bugs = []
    for k in range(COUNT):
        a0 = k * 2.399963 + rng.uniform(-0.2, 0.2)
        r = 0.2 + 0.8 * rng.random() ** 0.8
        w = rng.choice((1, 1, 2, -1)) * spin
        a = a0 + w * cyc
        x = cx + math.cos(a) * rx * r
        y = cy + math.sin(a) * ry * r * 0.9 + 2.0 * math.sin(cyc * 2.0 + k)
        # The heading: along the orbit, or forward when the swarm flies.
        da = 1.0 if w > 0 else -1.0
        heading = math.atan2(math.cos(a) * ry * da, -math.sin(a) * rx * da)
        if heading_bias is not None:
            heading = heading * 0.25
        if jet:
            # The stream: each locust goes forward by how far out it is.
            lead = (math.cos(a) + 1.0) * 0.5
            x += jet * (14.0 + 34.0 * lead)
            y = cy + (y - cy) * (1.0 - 0.5 * jet)
        if scatter:
            d = 1.0 + 1.4 * scatter
            x, y = cx + (x - cx) * d, cy + (y - cy) * d
            heading += rng.uniform(-1.5, 1.5) * scatter
        if fall:
            land = GROUND - 4.0 - rng.uniform(0.0, 6.0)
            drop = min(1.0, fall * rng.uniform(1.2, 2.2))
            y = y + (land - y) * drop * drop
            heading = heading * (1.0 - drop) + (0.15 if rng.random() < 0.5 else math.pi - 0.15) * drop
        x = max(14.0, min(114.0, x))
        y = max(12.0, min(GROUND - 5.0, y))
        depth = math.sin(a)
        flap = 0.5 + 0.5 * math.sin(cyc * 6.0 + k * 1.7)
        if fall > 0.6 and y > GROUND - 12.0:
            flap = 0.0
        bugs.append((depth, x, y, heading, flap, k))

    def draw(group):
        for depth, x, y, heading, flap, k in group:
            far = depth < 0.0
            _locust(f, x, y, heading, flap, 1.0 if far else 1.25, LOCUST_FAR if far else LOCUST)

    bugs.sort()
    back = [b for b in bugs if b[0] < 0.0]
    front = [b for b in bugs if b[0] >= 0.0]
    draw(back)

    # The face of the swarm: two ember eyes and a grin of shadow.
    if face > 0.05:
        fx, fy = cx + 6.0 + 22.0 * jet, cy - 2.0
        mouth = [(fx - 10.0, fy + 8.0), (fx - 5.0, fy + 10.0 + 3.0 * grin), (fx, fy + 9.0 + 4.0 * grin), (fx + 5.0, fy + 10.0 + 3.0 * grin),
                 (fx + 10.0, fy + 7.0), (fx + 5.0, fy + 12.0 + 5.0 * grin), (fx - 5.0, fy + 12.0 + 4.0 * grin)]
        f.poly(mouth, K.alpha(H.OUTLINE, 0.9 * face), body=False)
        for ex in (fx - 7.5, fx + 7.5):
            ey = fy - 1.0
            slant = 1.0 if ex > fx else -1.0
            eye = [(ex - 5.0, ey - 2.0 - 2.4 * glare * slant), (ex + 5.0, ey - 2.0 + 2.4 * glare * slant), (ex + 4.0, ey + 3.0), (ex - 4.0, ey + 3.0)]
            f.poly(eye, K.alpha(EMBER, face), body=False)
            f.dot(ex, ey + 0.8, 1.3, K.alpha(EMBER_CORE, face))
            f.glow(ex, ey + 0.6, 4.0 + 2.0 * glare, K.alpha(EMBER, 0.5 * face))
    draw(front)

    if anim == "death" and t > 0.4:
        H.dust(f, cx, GROUND - 2.0, min(1.0, (t - 0.4) * 2.0), f"locust:death:{i}", spread=3.0)
    if alarm:
        H.alarm_mark(f, min(118.0, cx + rx * 0.7 + 8.0), max(16.0, cy - ry - 4.0))
    return f.finish(outline=H.OUTLINE, width=0.9, glow_blur=2.0, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
