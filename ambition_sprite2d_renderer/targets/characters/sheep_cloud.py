"""A cloud sheep of Hobford: what a fell sheep becomes when it is killed.

Hobford's sheep are cloud sheep (Jon, 2026-11-20): struck down, a sheep
rises into the air as a cloud. This is the cloud: a small cumulus, white and
lit on top, flat and blue-grey underneath, with the sheep still in it. Its
long black face looks out of the front with its eyes shut, an ear out of the
wool, and its four black legs hang under the cloud.

Rows: `idle` billows (each puff swells and settles in its own time) and the
legs hang and sway; `walk` is the same drift with the legs paddling at the
air; `hit` blows the puffs apart and the eye opens; `death` lets the cloud
come apart and thin out to nothing.

The frame is 192 by 128 px: 96 by 64 room pixels at two frame pixels to
each. The cloud faces right, the tips of its legs on row 120.
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

TARGET_NAME = "sheep_cloud"
#: Room pixels of the drawing, and frame pixels to each.
WIDTH, HEIGHT, PPU = 96.0, 64.0, 2.0
FRAME_SIZE = (int(WIDTH * PPU), int(HEIGHT * PPU))
#: The tips of the hanging legs.
FOOT = HEIGHT - 4.0
#: The cloud's flat base, over the legs.
BASE = FOOT - 12.0

#: Sunlit top, and the blue-grey of a cumulus's shaded base.
CLOUD_TOP = (252, 252, 250)
CLOUD_BASE = (170, 182, 204)

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 12, 170),
    ("walk", 12, 120),
    ("hit", 3, 90),
    ("death", 6, 140),
]
LOOPS = {"idle", "walk"}

ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Cloud Sheep"},
    "body": {
        "body_plan": "cloud",
        "body_kind": "Floating",
        "mass_class": "Light",
        "traits": ["animal", "sheep", "cloud", "floating"],
        "locomotion_hint": "Float",
    },
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["animal", "art"],
    "authoring_description": (
        "A cloud sheep of Hobford: a fell sheep after it is killed, risen into the air as a small cumulus. White and "
        "sunlit on top, flat and blue-grey below, with the sheep's black face looking out of the front, eyes shut, and "
        "its four black legs hanging under the cloud. It billows and drifts; struck, it blows apart and gathers again."
    ),
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
}

#: The puffs of the cloud facing west: (x, y) from the cloud's middle, radius,
#: and the phase of its billow. The big ones are on top, as a cumulus's are.
PUFFS = [
    (-26.0, 3.0, 10.0, 0.0), (-14.0, -5.0, 13.0, 0.17), (2.0, -10.0, 15.0, 0.41), (17.0, -6.0, 13.0, 0.63),
    (30.0, 1.0, 10.0, 0.82), (-4.0, 2.0, 15.0, 0.29), (14.0, 4.0, 12.0, 0.55), (-20.0, 7.0, 9.0, 0.9),
    (25.0, 8.0, 8.0, 0.36),
]


def draw_cloud(c, *, t: float, legs, spread: float, eye: float, bob: float, thin: float) -> None:
    """The cloud facing west at billow phase `t` (0..1); `legs` is each leg's
    swing from its hip (front near, front far, hind far, hind near);
    `spread` blows the puffs out from the middle; `eye` 0 shut to 1 open;
    `bob` lifts the cloud; `thin` 0 whole to 1 gone (death)."""
    cx = WIDTH / 2 + 2
    cy = BASE - 14 - bob
    base = BASE - bob
    # The legs first, behind the cloud: thin and black, hanging from the base.
    hips = (cx - 15, cx - 8, cx + 9, cx + 16)
    far = (False, True, True, False)
    for hip, swing, is_far in sorted(zip(hips, legs, far), key=lambda leg: not leg[2]):
        hy = base - 2
        tip = (hip + swing, base + 10 - abs(swing) * 0.3)
        colour = scale(FACE, 0.7) if is_far else FACE
        c.put(c.mask(lambda pen: pen.line([(hip, hy), tip], 2.6)), colour, 1.0 - thin)
        c.put(c.mask(lambda pen: pen.ellipse(tip[0] - 0.3, tip[1] + 0.2, 1.6, 1.0)), scale(FACE, 0.8), 1.0 - thin)
    # The puffs: a lump of white with a flat base, rounded at its ends.
    r_scale = 1.0 - 0.25 * thin
    puffs = []
    for dx, dy, r, ph in PUFFS:
        swell = 1.0 + 0.07 * math.sin((t + ph) * math.tau)
        drift = 1.2 * math.sin((t + ph * 1.7) * math.tau)
        out = 1.0 + spread * 0.12 + thin * 0.5
        puffs.append((cx + dx * out + drift * 0.6, cy + dy * (1.0 + spread * 0.2) + drift * 0.3, r * swell * r_scale))
    tail = (cx + 38 + spread * 3, cy + 2, 4.5 * r_scale)
    wool = c.mask(lambda pen: [pen.ellipse(x, y, r) for x, y, r in puffs + [tail]], blur=0.8)
    flat = c.mask(lambda pen: pen.ellipse(cx, base - 4, 33 * (1.0 + spread * 0.1), 5.5), blur=0.8)
    cloud = np.maximum(wool * (c.y <= base).astype(np.float32), flat)
    # Thinned: holes open in it, from the noise.
    if thin > 0:
        cloud = cloud * np.clip((c.noise("thin", 6, 4, 2) - thin * 1.05) * 4.0, 0, 1)
    shade = np.clip((c.y - (cy - 14)) / (base - cy + 10), 0, 1)[:, :, None]
    paint = np.asarray(CLOUD_TOP, np.float32) * (1 - shade) + np.asarray(CLOUD_BASE, np.float32) * shade
    c.paint(cloud, paint, 1.0 - 0.6 * thin)
    c.tone(cloud * (c.noise("wool", 9, 6, 3) - 0.5), 0.12)
    # Sun on each puff's top: a cumulus is brightest at its crown.
    lit = c.mask(lambda pen: [pen.ellipse(x - r * 0.2, y - r * 0.35, r * 0.7, r * 0.5) for x, y, r in puffs], blur=1.6)
    c.light(lit * cloud, (255, 250, 236), 0.35)
    # The head on the cloud's west side: the sheep's long face, the muzzle
    # forward, its eyes shut. It is drawn over the wool, and a curl of the
    # crown's wool over it.
    hx, hy = cx - 40 - spread * 3, cy + 4
    head = c.mask(
        lambda pen: pen.poly([(hx + 7, hy - 4), (hx + 2, hy - 5), (hx - 5, hy - 1), (hx - 6, hy + 2), (hx - 3, hy + 4), (hx + 7, hy + 3)]),
        blur=0.4,
    )
    c.put(head, FACE, 1.0 - thin)
    # The ear, out of the wool behind the face.
    c.put(c.mask(lambda pen: pen.ellipse(hx + 7, hy - 5.5 - eye * 1.5, 3.4, 1.4)), FACE, 1.0 - thin)
    # The eye: a shut line, or open in a start.
    if eye > 0.5:
        c.put(c.mask(lambda pen: pen.ellipse(hx + 1, hy - 2, 1.0)), (230, 214, 160), 1.0 - thin)
    else:
        c.put(c.mask(lambda pen: pen.line([(hx - 0.5, hy - 1.6), (hx + 1, hy - 2.2), (hx + 2.4, hy - 1.6)], 0.7)), (150, 140, 120), 1.0 - thin)
    # A curl of wool on the crown, over the face.
    crown = c.mask(lambda pen: pen.ellipse(hx + 6, hy - 4.5, 3.2, 2.4), blur=0.5)
    c.put(crown, CLOUD_TOP, 1.0 - thin)


def _pose(anim: str, i: int, n: int) -> dict:
    t = K.phase(i, n, anim in LOOPS)
    if anim == "idle":
        sway = math.sin(t * math.tau)
        legs = [1.2 * sway, 0.9 * math.sin(t * math.tau + 0.8), 0.9 * math.sin(t * math.tau + 1.9), 1.2 * math.sin(t * math.tau + 2.6)]
        return dict(t=t, legs=legs, spread=0.0, eye=0.0, bob=0.8 * math.sin(t * math.tau), thin=0.0)
    if anim == "walk":
        # Paddling at the air, in diagonal pairs.
        a = math.sin(t * math.tau * 2)
        legs = [-3.0 * a, 3.0 * a, -3.0 * a, 3.0 * a]
        return dict(t=t, legs=legs, spread=0.0, eye=0.0, bob=0.8 * math.sin(t * math.tau), thin=0.0)
    if anim == "hit":
        k = [0.7, 1.0, 0.45][min(i, 2)]
        return dict(t=0.0, legs=[3.0 * k, -2.0 * k, 2.0 * k, -3.0 * k], spread=k, eye=1.0, bob=0.0, thin=0.0)
    # death: it comes apart and thins to nothing.
    s = t * t * (3 - 2 * t)
    return dict(t=t * 0.5, legs=[2.0 * s, -2.0 * s, 2.0 * s, -2.0 * s], spread=0.4 * s, eye=0.0, bob=4.0 * s, thin=s)


def _render_frame(anim: str, i: int, n: int) -> Image.Image:
    c = Canvas(TARGET_NAME, WIDTH, HEIGHT, (0.0, 0.0), PPU)
    draw_cloud(c, **_pose(anim, i, n))
    return c.image().transpose(Image.Transpose.FLIP_LEFT_RIGHT)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
