"""The fell sheep of Hobford's hills: the fell's dressing sheep, alive.

The drawing is the fell prop's (`targets/props/hill_village_props.py`
`sheep`): a white fleece of many round tufts, a long black face with its
muzzle forward, an ear back, a tuft of wool on the crown, black legs. Here
the head and the legs move, so the same sheep grazes, walks and starts.

Rows: `idle` grazes, its head down to the grass and nibbling, and it lifts
its head once a cycle to look about; `walk` is a steady amble with the head
up, the legs in diagonal pairs; `hit` is a start, the head flung up; `death`
is a Hobford sheep's: its legs go slack, its fleece swells into a cumulus and
lifts it off the grass, and as it fades the cloud it has become
(`sheep_cloud`) takes its place and rises.

Hobford's sheep are cloud sheep (Jon, 2026-11-20), so the fleece is a cloud's
already: white and lit on its tufts, blue-grey under its belly.

The frame is 128 by 88 px: the prop's 64 by 44 room pixels drawn at two
frame pixels to each. The sheep faces right, its feet on row 84.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image

from . import _art_cast_kit as K
from ..props._town_kit import Canvas, scale
from ..props.hill_village_props import FACE

TARGET_NAME = "fell_sheep"
#: Room pixels of the drawing, and frame pixels to each.
WIDTH, HEIGHT, PPU = 64.0, 44.0, 2.0
FRAME_SIZE = (int(WIDTH * PPU), int(HEIGHT * PPU))
FOOT = HEIGHT - 2.0

#: A cloud's fleece: its sunlit top, and the blue-grey under it.
CLOUD_FLEECE = (246, 246, 242)
CLOUD_BELLY = (184, 192, 210)

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 10, 200),
    ("walk", 8, 120),
    ("hit", 3, 90),
    ("death", 6, 140),
]
LOOPS = {"idle", "walk"}

ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Fell Sheep"},
    "body": {
        "body_plan": "quadruped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": ["animal", "sheep", "grazer", "flock"],
        "locomotion_hint": "Walk",
    },
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["animal", "art"],
    "authoring_description": (
        "A black-faced fell sheep of Hobford's hills, the fell's dressing sheep drawn to move: it grazes with its head "
        "down and lifts it to look about, ambles with its head up, starts when struck, and lies down in the grass."
    ),
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
}

def draw_sheep(c, *, graze: float, nibble: float, legs, sink: float, bob: float, start: float, puff: float = 0.0) -> None:
    """The prop's sheep, facing west, posed: `graze` 0 (head up) to 1 (head
    down at the grass); `nibble` turns the muzzle; `legs` is each leg's
    (swing, lift) from its hip, front near, front far, hind far, hind near;
    `sink` folds the legs and lowers the body; `bob` lifts the body; `start`
    flings the head up and back; `puff` swells the fleece into a cloud."""
    foot = FOOT
    cx = WIDTH / 2 + 4
    top = foot - 30 + sink * 13.0 - bob
    rng = c.rand("sheep")
    # The legs: the far pair darker, behind the fleece. A folded leg is short.
    reach = 12.0 * (1.0 - sink * 0.85)
    hips = (cx - 12, cx - 6, cx + 8, cx + 13)
    far = (False, True, True, False)
    for hip, (swing, lift), is_far in sorted(zip(hips, legs, far), key=lambda leg: not leg[2]):
        hy = foot - 12 + sink * 11.0 - bob
        tip = (hip + swing, min(foot, hy + reach) - lift)
        colour = scale(FACE, 0.7) if is_far else FACE
        c.put(c.mask(lambda pen: pen.line([(hip, hy - 1), tip], 3.0)), colour)
        c.put(c.mask(lambda pen: pen.ellipse(tip[0] - 0.4, tip[1] - 0.6, 1.9, 1.1)), scale(FACE, 0.8))
    grow = 1.0 + 0.22 * puff
    tufts = [(cx + rng.uniform(-14, 14) * grow, top + 9 + rng.uniform(-4, 4) * grow, rng.uniform(7, 10) * grow,
              rng.uniform(6, 8) * grow) for _ in range(12)]
    body = c.mask(lambda pen: [pen.ellipse(*t) for t in tufts] + [pen.ellipse(cx, top + 10, 18 * grow, 9)], blur=0.7)
    # A cloud's wool: white on top, blue-grey underneath; the whiter, the
    # more it has puffed.
    under = np.clip((c.y - top - 4) / 14, 0, 1)[:, :, None]
    wool = np.asarray(CLOUD_FLEECE, np.float32) * (1 - under) + np.asarray(CLOUD_BELLY, np.float32) * under
    c.paint(body, wool)
    c.tone(body * (c.noise("wool", 10, 6, 2) - 0.5), 0.2 * (1 - puff) + 0.1)
    lit = c.mask(lambda pen: [pen.ellipse(x - rx * 0.2, y - ry * 0.4, rx * 0.6, ry * 0.45) for x, y, rx, ry in tufts], blur=1.0)
    c.light(lit * body, (255, 250, 236), 0.3 + 0.2 * puff)
    # The tail: a short woolly tuft at the rump.
    c.put(c.mask(lambda pen: pen.ellipse(cx + 19 * grow, top + 8 + graze * 1.0, 3.0, 4.0), blur=0.4), CLOUD_FLEECE)
    # The head on its neck from the fleece's front: raised, or down to the
    # grass. A start throws it up and back.
    up = (cx - 25, top + 1 - start * 4.0)
    down = (cx - 24, foot - 5)
    g = max(0.0, min(1.0, graze))
    hx = up[0] + (down[0] - up[0]) * g + start * 3.0
    hy = up[1] + (down[1] - up[1]) * g
    tilt = 0.35 + 0.55 * g - start * 0.5 + nibble * 0.25
    hx -= 6 * puff
    neck = c.mask(lambda pen: pen.line([(cx - 13, top + 9), (hx + 6, hy - 1)], 6), blur=0.6)
    c.paint(neck, wool)
    c.tone(neck * (c.noise("wool", 10, 6, 2) - 0.5), 0.15)
    head = c.mask(
        lambda pen: pen.poly(
            [(hx + 7, hy - 4), (hx + 2, hy - 5), (hx - 5, hy - 2 + tilt * 3), (hx - 6, hy + 1 + tilt * 3), (hx - 3, hy + 3 + tilt * 2), (hx + 6, hy + 3)]
        ),
        blur=0.4,
    )
    c.put(head, FACE)
    ear_droop = 1.4 * g - 1.6 * start
    c.put(c.mask(lambda pen: pen.ellipse(hx + 8, hy - 3 + ear_droop, 3.2, 1.4)), FACE)
    c.put(c.mask(lambda pen: pen.ellipse(hx + 1, hy - 2, 0.9)), (230, 214, 160))
    c.put(c.mask(lambda pen: pen.ellipse(hx + 6, hy - 4, 3, 2.2), blur=0.4), CLOUD_FLEECE)
    if g > 0.85:
        # A mouthful of grass at the muzzle while it nibbles.
        c.put(c.mask(lambda pen: pen.line([(hx - 6, hy + 2 + tilt * 3), (hx - 8, hy + 5 + nibble)], 0.8)), (92, 128, 60))


def _smooth(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def _pose(anim: str, i: int, n: int) -> dict:
    t = K.phase(i, n, anim in LOOPS)
    still = [(0.0, 0.0)] * 4
    if anim == "idle":
        # Head down most of the cycle; up to look about from t 0.6 to 0.85.
        look = _smooth((t - 0.55) / 0.12) * (1.0 - _smooth((t - 0.8) / 0.12))
        return dict(graze=1.0 - look, nibble=math.sin(t * math.tau * 3.0) * (1.0 - look), legs=still, sink=0.0, bob=0.0, start=0.0)
    if anim == "walk":
        # Diagonal pairs: front near with hind far, front far with hind near.
        a = math.sin(t * math.tau)
        b = -a
        lift_a = max(0.0, math.cos(t * math.tau)) * 2.2
        lift_b = max(0.0, -math.cos(t * math.tau)) * 2.2
        legs = [(-3.0 * a, lift_a), (-3.0 * b, lift_b), (-3.0 * a, lift_a), (-3.0 * b, lift_b)]
        return dict(graze=0.05, nibble=0.0, legs=legs, sink=0.0, bob=0.6 * abs(math.sin(t * math.tau)), start=0.0)
    if anim == "hit":
        k = [0.6, 1.0, 0.4][min(i, 2)]
        return dict(graze=0.0, nibble=0.0, legs=[(1.5 * k, 0.0)] * 4, sink=0.08 * k, bob=0.0, start=k)
    # death: the legs go slack and hang, the fleece swells into a cloud and
    # lifts the sheep off the grass, its head up and its eyes on the sky.
    s = _smooth(t * 1.25)
    sway = 1.5 * math.sin(t * math.tau)
    legs = [(sway, 0.0), (-sway, 0.0), (sway, 0.0), (-sway, 0.0)]
    return dict(graze=0.0, nibble=0.0, legs=legs, sink=0.0, bob=4.0 * s, start=0.0, puff=s)


def _render_frame(anim: str, i: int, n: int) -> Image.Image:
    c = Canvas(TARGET_NAME, WIDTH, HEIGHT, (0.0, 0.0), PPU)
    draw_sheep(c, **_pose(anim, i, n))
    image = c.image().transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if anim == "death":
        t = K.phase(i, n, False)
        fade = 1.0 - _smooth((t - 0.7) / 0.3)
        if fade < 1.0:
            image.putalpha(image.getchannel("A").point(lambda v: int(v * fade)))
    return image


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
