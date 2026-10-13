"""Sprite generator for the Puppy Slug: a slug that a dream made out of dogs.

The look (2026-10-13, a redraw: Jon, "I would also like to see redone puppy
slug art"): the "puppyslug" of the pictures an image network dreamed in 2015,
when each cloud and each leaf came out with the eyes and the nose of a dog. It
is seen from its side, facing right, on the ground:

- the head of a puppy at its front: a round skull, a short pale muzzle, a wet
  black nose, a dark ear that hangs, a patch round its eye;
- the body of a slug behind that: fat at the shoulders, thin at the tail,
  flat on the ground, with a pale foot under it that ripples. The fur of the
  head goes over into the wet green skin of the slug half of the way down;
- the two eye stalks of a slug on the top of the dog's head;
- what the dream did not finish: a second, smaller face that sleeps on its
  back, and two eyes in its flank that look at you.

It is wildlife. It is a little wrong and it does not know. It is not a
monster, and it is not a toy. There is no drop shadow.

The dream itself is a second picture of this target, ``dream_skin``: eyes in a
lattice, a whorl of ripples round each, dots as scales. The game lays it over
the slug and moves it (a shader that draws no art of its own). The sheet is
good to look at with no shader on it.

The rows: ``idle`` (it pants), ``walk`` (a wave goes down its body, and it
goes longer and shorter), ``hurt`` (it bunches up) and ``death`` (it goes
flat, and the dream goes out of it). The game turns the sprite when the slug
is on a wall or a ceiling: the sheet has no row for those. The old sheet had
two, and no code read them.

The frame and the box of its body are those of the old sheet, so it is the
size in the game that it was.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

from . import _person_rig as R
from ._ai_era_kit import OUTLINE, WHITE, Kit, Point, RGBA, ease, keys, mix, pin, turned

TARGET_NAME = "puppy_slug"
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
    # The skin of the dream: see `dream_skin`.
    f"{TARGET_NAME}_dream_skin.png",
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_puppy_slug",
        "display_name": "Puppy Slug",
    },
    "body": {
        "body_plan": "Crawler",
        "body_kind": "Crawler",
        "mass_class": "Light",
        "locomotion_hint": "Slither",
        "traits": ["enemy", "ai_era", "crawler", "no_hands", "wall_crawler"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": True,
            "fly": None,
            "swim": None,
            "crawl": True,
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {
            "talk": None,
            "trade": None,
            "carry": None,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "wanderer_puppy_slug"},
    "actions": {"default_preset": "peaceful_slither"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "mouth": {"source": "puppy_slug.geometry", "point": {"x": 112.0, "y": 62.0}},
        "head": {"source": "puppy_slug.geometry", "point": {"x": 98.0, "y": 54.0}},
        "belly": {"source": "puppy_slug.geometry", "point": {"x": 62.0, "y": 72.0}},
        "tail": {"source": "puppy_slug.geometry", "point": {"x": 10.0, "y": 72.0}},
        "wall_contact": {"source": "puppy_slug.geometry", "point": {"x": 62.0, "y": 74.0}},
    },
    "tags": ["enemy", "ai_era", "crawler"],
}

#: The frame of the old sheet, as it was published: a row of the catalog with
#: no height of its own takes its size in the game from the height of the frame.
FRAME_SIZE = (128, 95)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 140),
    ("walk", 10, 90),
    ("hurt", 4, 70),
    ("death", 8, 110),
]

K = Kit(FRAME_SIZE)
#: The ground under it, the end of its tail and the base of its neck at rest.
GROUND = 74.0
TAIL = 8.0
NECK = 88.0

# The fur of the dog: a warm caramel. The skin of the slug: a wet green, with
# a darker saddle. The foot under it: pale.
FUR: RGBA = (216, 160, 98, 255)
FUR_LIGHT: RGBA = (246, 220, 176, 255)
FUR_DARK: RGBA = (150, 96, 58, 255)
EAR: RGBA = (118, 72, 48, 255)
EAR_DARK: RGBA = (76, 44, 34, 255)
SKIN: RGBA = (104, 170, 140, 255)
SKIN_DARK: RGBA = (54, 106, 104, 255)
SKIN_LIGHT: RGBA = (176, 226, 190, 255)
SADDLE: RGBA = (62, 122, 122, 255)
SPOT: RGBA = (140, 206, 184, 255)
SHEEN: RGBA = (238, 156, 196, 255)
FOOT: RGBA = (240, 214, 184, 255)
FOOT_DARK: RGBA = (190, 150, 128, 255)
NOSE: RGBA = (30, 22, 30, 255)
EYE_WHITE: RGBA = (252, 248, 238, 255)
IRIS: RGBA = (96, 58, 34, 255)
INK: RGBA = (28, 24, 32, 255)
TONGUE: RGBA = (236, 122, 138, 255)
TONGUE_DARK: RGBA = (190, 82, 104, 255)
STAR: RGBA = (250, 226, 130, 255)

Pose = Dict[str, object]

#: At rest. A row states what differs.
REST: Pose = {
    # The wave down its body: where it is (0 to 1) and how strong.
    "phase": 0.0,
    "amp": 0.03,
    # How high it is (1 is at rest), and how far its tail and its head are
    # from where they rest (+x is forward).
    "tall": 1.0,
    "tail": 0.0,
    "reach": 0.0,
    # The head: up or down from where it sits, and its turn.
    "head": (0.0, 0.0),
    # The turn of its ear from where it hangs, and of its stalks from up.
    "ear": 0.0,
    "stalk": 0.0,
    # How far its tongue is out, 0 to 1.
    "tongue": 0.0,
    # open, closed, wince, wide: the eyes of its head, the eyes in its flank,
    # and the eyes of the face on its back.
    "eyes": "open",
    "flank": "open",
    "bud": "closed",
    # How much of the dream is left in it: 1, to 0 when it is dead.
    "dream": 1.0,
}


def P(**kw) -> Pose:
    unknown = set(kw) - set(REST)
    assert not unknown, unknown
    return dict(REST, **kw)


#: How high its back is over the ground, from the end of its tail to its neck.
PROFILE = ((0.0, 3.0), (0.04, 6.4), (0.1, 10.0), (0.2, 14.0), (0.34, 17.4), (0.5, 19.4), (0.68, 20.4), (0.84, 20.8), (1.0, 21.4))


def _high(t: float) -> float:
    for (t0, h0), (t1, h1) in zip(PROFILE, PROFILE[1:]):
        if t <= t1:
            return h0 + (h1 - h0) * (t - t0) / (t1 - t0)
    return PROFILE[-1][1]


def _back(pose: Pose) -> List[Point]:
    """The line of its back, in the frame, from its tail to its neck."""
    x0, x1 = TAIL + float(pose["tail"]), NECK + float(pose["reach"])  # type: ignore[arg-type]
    phase, amp, tall = float(pose["phase"]), float(pose["amp"]), float(pose["tall"])  # type: ignore[arg-type]
    out = []
    for k in range(25):
        t = k / 24.0
        h = _high(t) * tall * (1.0 + amp * math.sin(math.tau * (1.6 * t - phase)) * min(1.0, 4.0 * t))
        out.append((round(x0 + (x1 - x0) * t, 1), round(GROUND - h, 1)))
    return out


def _eye(d, c: Point, rx: float, ry: float, mode: str, look: Point = (0.5, 0.2), iris: RGBA = IRIS) -> None:
    """An eye at a frame point: a white, a brown iris, a pupil and its light."""
    if mode == "closed":
        K.line(d, [(c[0] - rx, c[1] - 0.2), (c[0], c[1] + 0.8), (c[0] + rx, c[1] - 0.2)], INK, 0.8)
        return
    if mode == "wince":
        K.line(d, [(c[0] - rx, c[1] - ry * 0.7), (c[0] + rx * 0.5, c[1]), (c[0] - rx, c[1] + ry * 0.7)], INK, 0.8)
        return
    big = 1.18 if mode == "wide" else 1.0
    K.oval(d, c, rx * big, ry * big, EYE_WHITE, OUTLINE, 0.5)
    at = (c[0] + look[0], c[1] + look[1])
    k = 0.5 if mode == "wide" else 0.74
    K.oval(d, at, rx * k, ry * k, iris)
    K.oval(d, at, rx * k * 0.55, ry * k * 0.55, INK)
    K.oval(d, (at[0] - rx * 0.28, at[1] - ry * 0.34), 0.5, 0.5, WHITE)


def _body(pose: Pose):
    """All of the slug but its head: one shape from the line of its back to
    the ground, the fur that goes over into skin, its saddle and its spots,
    the foot under it, and what the dream left on it."""
    back = _back(pose)
    dream = float(pose["dream"])  # type: ignore[arg-type]
    phase = float(pose["phase"])  # type: ignore[arg-type]
    x0, x1 = back[0][0], back[-1][0]
    front = x1 + 15.0
    flank, bud = str(pose["flank"]), str(pose["bud"])

    def on(t: float, down: float = 0.0) -> Point:
        """A frame point on its side: ``t`` along it, ``down`` (0 to 1) from its back to the ground."""
        i = min(len(back) - 2, int(t * (len(back) - 1)))
        u = t * (len(back) - 1) - i
        x = back[i][0] + (back[i + 1][0] - back[i][0]) * u
        y = back[i][1] + (back[i + 1][1] - back[i][1]) * u
        return (x, y + (GROUND - y) * down)

    bx, by = on(0.44)
    bump = 5.6 * dream

    def at(p: Point) -> Point:
        return K.at(p[0], p[1])

    def shape(d) -> None:
        # The back, down the front of the chest to the ground, and back along
        # the ground to the tail, whose end is a little off it.
        K.poly(d, [at(p) for p in back] + [K.at(x1 + 9.0, GROUND - 13.0), K.at(front, GROUND - 5.0), K.at(front + 1.0, GROUND), K.at(x0 + 2.0, GROUND),
                                           K.at(x0 - 1.4, GROUND - 1.6)], WHITE)
        # The end of its tail is round.
        K.oval(d, K.at(x0 + 1.0, back[0][1] + 1.6), 2.6, 2.2, WHITE)
        if bump > 1.0:
            # The face on its back stands up out of the line of it.
            K.oval(d, K.at(bx, by - 1.0), bump + 0.6, bump, WHITE)
            K.poly(d, [K.at(bx - bump - 3.4, by + 1.0), K.at(bx - bump + 0.6, by - 2.6), K.at(bx - bump + 1.4, by + 2.6)], WHITE)

    def fill(d) -> None:
        # Fur at the front, and it goes over into the skin of the slug.
        a, b = on(0.6)[0], on(0.9)[0]
        steps = 28
        d.rectangle([0, 0, K.canvas[0] * 2, K.canvas[1] * 2], fill=SKIN)
        for k in range(steps):
            t = k / (steps - 1)
            x = a + (b - a) * t
            xa = K.pt(K.at(x, 0.0))[0]
            d.rectangle([xa, 0, K.canvas[0] * 2, K.canvas[1] * 2], fill=mix(SKIN, FUR, ease(t)))

    def detail(d) -> None:
        # The saddle of the slug: darker, from its back half of the way down.
        top = [on(t) for t in (0.08, 0.16, 0.24, 0.34, 0.44, 0.54, 0.62, 0.7)]
        low = [on(t, k) for t, k in ((0.7, 0.24), (0.62, 0.44), (0.5, 0.52), (0.36, 0.5), (0.22, 0.44), (0.1, 0.3))]
        K.poly(d, [at(p) for p in top + low], SADDLE)
        # Its spots are rings, as the eyes of the dream are: a pale ring, a
        # dark middle, a point of light.
        for t, k, r in ((0.16, 0.22, 1.5), (0.27, 0.32, 2.0), (0.36, 0.16, 1.3), (0.54, 0.34, 1.8), (0.62, 0.16, 1.2), (0.46, 0.4, 1.1)):
            c = at(on(t, k))
            K.oval(d, c, r * 1.25, r * 1.05, SPOT)
            K.oval(d, c, r * 0.62, r * 0.55, SKIN_DARK)
            K.oval(d, (c[0] - r * 0.3, c[1] - r * 0.3), 0.35, 0.35, WHITE)
        # And dots in rows where the fur is, as on the dogs of those pictures.
        for t, k in ((0.7, 0.34), (0.74, 0.6), (0.79, 0.3), (0.84, 0.62), (0.89, 0.36), (0.95, 0.66)):
            K.oval(d, at(on(t, k)), 0.9, 0.8, FUR_DARK)
        # It is wet: a line of light down its back, and a little pink at its tail.
        K.line(d, [at(on(t, 0.14)) for t in (0.16, 0.24, 0.32)], SKIN_LIGHT, 0.9)
        K.line(d, [at(on(t, 0.4)) for t in (0.05, 0.1, 0.16)], SHEEN[:3] + (int(170 * dream),), 1.1)
        K.line(d, [at(on(t, 0.62)) for t in (0.2, 0.3, 0.42)], SKIN_DARK[:3] + (150,), 0.7)
        # Tufts where the fur starts.
        for t, k in ((0.76, 0.2), (0.8, 0.5), (0.87, 0.28), (0.93, 0.52)):
            p = on(t, k)
            K.line(d, [K.at(p[0] - 1.6, p[1] - 1.0), K.at(p[0], p[1] + 1.2), K.at(p[0] + 1.6, p[1] - 0.8)], FUR_DARK, 0.6)
        # The pale chest under its chin.
        K.poly(d, [K.at(x1 + 2.0, GROUND - 9.0), K.at(x1 + 9.0, GROUND - 12.0), K.at(front, GROUND - 5.0), K.at(front + 1.0, GROUND), K.at(x1 + 1.0, GROUND)],
               FUR_LIGHT)
        # The foot: a pale band along the ground, and its edge ripples.
        edge = []
        for k in range(33):
            t = k / 32.0
            x = x0 + 2.0 + (front - x0 - 1.0) * t
            edge.append(K.at(x, GROUND - 3.4 - 0.9 * math.sin(math.tau * (5.0 * t - 2.0 * phase))))
        K.poly(d, edge + [K.at(front + 2.0, GROUND + 2.0), K.at(x0, GROUND + 2.0)], FOOT)
        K.line(d, edge, FOOT_DARK, 0.6)
        if dream > 0.35:
            # The two eyes in its flank. They do not look where its head looks.
            for t, k, r, look in ((0.26, 0.56, 2.5, (-0.5, 0.3)), (0.64, 0.6, 2.2, (0.5, -0.3))):
                _eye(d, at(on(t, k)), r, r * 0.9, flank, look, (120, 70, 150, 255))
        if bump > 2.0:
            # The face on its back: fur, a muzzle, a nose, an ear, two eyes.
            K.oval(d, K.at(bx, by + 1.0), bump + 2.6, bump + 1.6, FUR)
            K.poly(d, [K.at(bx - bump - 3.4, by + 1.0), K.at(bx - bump + 0.6, by - 2.6), K.at(bx - bump + 1.4, by + 2.6)], EAR)
            K.oval(d, K.at(bx + 2.6, by + 0.6), 2.9, 2.2, FUR_LIGHT)
            K.oval(d, K.at(bx + 4.4, by - 0.4), 1.1, 0.9, NOSE)
            for ex in (-2.0, 1.2):
                _eye(d, K.at(bx + ex, by - 2.4), 1.3, 1.3, bud, (0.3, 0.1))

    key = ("puppy_slug_body", tuple(back), round(dream, 2), round(phase, 3), flank, bud)
    return K.solid(key, shape, fill, detail, outline=1.3, rim=0.34, shade=0.38, shade_colour=SKIN_DARK)


def _head(eyes: str):
    """The head of the puppy, from its middle."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, -1.0), 11.4, 10.8, WHITE)
        K.oval(d, K.at(2.0, 5.0), 9.4, 6.8, WHITE)
        K.oval(d, K.at(10.0, 4.0), 7.4, 5.8, WHITE)

    def detail(d) -> None:
        # The patch round its near eye, the pale muzzle, the nose, the mouth.
        K.oval(d, K.at(1.6, -3.4), 5.4, 5.8, mix(FUR, FUR_DARK, 0.7))
        K.oval(d, K.at(10.6, 5.0), 6.6, 4.8, FUR_LIGHT)
        K.oval(d, K.at(15.8, 1.6), 2.7, 2.2, NOSE)
        K.oval(d, K.at(15.2, 0.8), 0.9, 0.6, (120, 110, 130, 255))
        K.line(d, [K.at(15.6, 3.8), K.at(14.4, 6.6), K.at(10.0, 8.8), K.at(6.0, 7.6)], INK, 0.8)
        K.line(d, [K.at(-6.0, -8.0), K.at(-2.6, -9.8), K.at(1.0, -9.6)], FUR_LIGHT, 0.8)
        _eye(d, K.at(1.8, -3.2), 3.3, 3.6, eyes, (0.7, 0.3))
        _eye(d, K.at(9.4, -4.4), 2.4, 2.8, eyes, (0.5, 0.3))
        if eyes in ("open", "wide"):
            K.line(d, [K.at(-1.8, -7.6), K.at(1.8, -8.2), K.at(5.0, -6.8)], FUR_DARK, 0.9)

    return K.solid(("puppy_slug_head", eyes), shape, FUR, detail, outline=1.3, rim=0.34, shade=0.36, shade_colour=FUR_DARK)


def _ear(near: bool):
    """An ear from its root: it hangs."""
    s = 1.0 if near else 0.8

    def shape(d) -> None:
        K.poly(d, [K.at(x * s, y * s) for x, y in ((1.6, -1.4), (-3.6, 0.0), (-7.6, 6.0), (-8.0, 13.0), (-5.0, 17.4), (-1.0, 15.6), (1.6, 9.0), (3.2, 2.0))], WHITE)

    def detail(d) -> None:
        K.line(d, [K.at(-2.0 * s, 2.0 * s), K.at(-4.6 * s, 8.0 * s), K.at(-4.4 * s, 13.6 * s)], EAR_DARK, 0.8)

    return K.solid(("puppy_slug_ear", near), shape, EAR if near else EAR_DARK, detail, outline=1.2, rim=0.3, shade=0.34, shade_colour=EAR_DARK)


def _tongue(out: float):
    long = 2.0 + 5.0 * out

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 2.0, K.home[1] - 0.6, K.home[0] + 2.0, K.home[1] + long, 1.8, WHITE)

    def detail(d) -> None:
        K.line(d, [K.at(0.0, 0.4), K.at(0.0, long - 1.4)], TONGUE_DARK, 0.6)

    return K.solid(("puppy_slug_tongue", round(long, 1)), shape, TONGUE, detail, outline=1.0, rim=0.2, shade=0.2, shade_colour=TONGUE_DARK)


def _stalk_eye(mode: str):
    def paint(d) -> None:
        _eye(d, K.at(0.0, 0.0), 2.3, 2.3, "open" if mode == "wide" else mode, (0.4, 0.0), (60, 110, 110, 255))

    return K.piece(("puppy_slug_stalk_eye", mode), paint)


def _stars(n: int):
    def paint(d) -> None:
        for k in range(n):
            a = math.tau * k / max(1, n)
            K.star4(d, K.at(7.0 * math.cos(a), 3.0 * math.sin(a)), 2.4, STAR)

    return K.piece(("puppy_slug_stars", n), paint)


# ---- The skin of the dream -------------------------------------------------------

DREAM_SKIN_FILE = f"{TARGET_NAME}_dream_skin.png"


def dream_skin(size: int = 256, seed: int = 2015) -> Image.Image:
    """The skin of the dream: a picture that TILES in both directions, for the
    game's dream pass to lay over the slug (the pass draws no art of its own).

    It is what the pictures of 2015 are made of: eyes in a loose lattice (a
    dark pupil, an amber or a teal iris, a pale lid), a whorl of fine ripples
    round each eye in the colours of oil on water, a dark crease where two
    whorls meet, and rows of dots round each eye, as scales.

    The alpha is how much of the skin shows: all of an eye, most of a dot,
    less of the ripples."""
    rng = random.Random(seed)
    cols, rows = 7, 8
    sx, sy = size / cols, size / rows
    sites = []
    for j in range(rows):
        for i in range(cols):
            x = (i + 0.5 + (0.5 if j % 2 else 0.0) + rng.uniform(-0.22, 0.22)) * sx
            y = (j + 0.5 + rng.uniform(-0.22, 0.22)) * sy
            sites.append((x % size, y % size, rng.uniform(6.0, 10.5), rng.random(), rng.random()))
    S = 3
    n = size * S
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / S
    d1 = np.full((n, n), 1e9, np.float32); d2 = np.full((n, n), 1e9, np.float32)
    idx = np.zeros((n, n), np.int32); ang = np.zeros((n, n), np.float32)
    for k, (x, y, r, h, t) in enumerate(sites):
        dx = (xx - x + size / 2) % size - size / 2
        dy = (yy - y + size / 2) % size - size / 2
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < d1
        d2 = np.where(closer, d1, np.minimum(d2, d))
        ang = np.where(closer, np.arctan2(dy, dx), ang)
        idx = np.where(closer, k, idx)
        d1 = np.where(closer, d, d1)
    rad = np.array([s[2] for s in sites], np.float32)[idx]
    hue0 = np.array([s[3] for s in sites], np.float32)[idx]
    kind = np.array([s[4] for s in sites], np.float32)[idx]
    u = d1 / rad
    # the whorl: fine ripples round each eye, bent a little by the angle
    phase = d1 * 1.25 + 0.6 * np.sin(ang * 3.0 + hue0 * 6.28)
    ripple = 0.5 + 0.5 * np.sin(phase)
    hue = (0.52 + 0.30 * np.sin(hue0 * 6.28) + 0.07 * np.sin(ang * 2.0) + d1 * 0.011) % 1.0
    sat = 0.50 + 0.25 * ripple
    val = 0.50 + 0.50 * ripple
    rgb = np.zeros((n, n, 3), np.float32)
    h6 = hue * 6.0; i6 = np.floor(h6).astype(np.int32) % 6; f = h6 - np.floor(h6)
    p = val * (1 - sat); q = val * (1 - sat * f); t = val * (1 - sat * (1 - f))
    for c, table in enumerate(((val, q, p, p, t, val), (t, val, val, q, p, p), (p, p, t, val, val, q))):
        rgb[..., c] = np.choose(i6, table)
    alpha = 0.14 + 0.24 * ripple
    # the crease where two whorls meet
    crease = np.clip(1.0 - (d2 - d1) / 2.4, 0.0, 1.0)
    rgb *= (1.0 - 0.55 * crease)[..., None]
    alpha = np.maximum(alpha, 0.5 * crease)
    # rows of dots round each eye, as scales
    for ring, count in ((1.55, 9), (2.05, 13)):
        band = np.clip(1.0 - np.abs(u - ring) / 0.16, 0.0, 1.0)
        dots = np.clip((np.cos(ang * count + hue0 * 9.0) - 0.55) / 0.3, 0.0, 1.0) * band
        dot_rgb = np.stack([0.20 + 0.0 * u, 0.12 + 0.0 * u, 0.20 + 0.0 * u], -1)
        rgb = rgb * (1 - dots[..., None]) + dot_rgb * dots[..., None]
        alpha = np.maximum(alpha, 0.9 * dots)
    # the eye
    def ring(lo, hi, soft=0.06):
        return np.clip((u - lo) / soft, 0, 1) * np.clip((hi - u) / soft, 0, 1)
    lid = ring(0.80, 1.04); limbus = ring(0.68, 0.82); iris = ring(0.30, 0.70); pupil = np.clip((0.34 - u) / 0.06, 0, 1)
    amber = np.stack([0.98 + 0 * u, 0.62 + 0.2 * np.cos(ang * 9.0) * 0 + 0 * u, 0.16 + 0 * u], -1)
    teal = np.stack([0.30 + 0 * u, 0.86 + 0 * u, 0.80 + 0 * u], -1)
    iris_rgb = np.where((kind > 0.42)[..., None], amber, teal) * (0.80 + 0.20 * np.cos(ang * 11.0))[..., None]
    for mask, colour in ((lid, np.array([0.98, 0.94, 0.84], np.float32)), (limbus, np.array([0.16, 0.10, 0.14], np.float32))):
        rgb = rgb * (1 - mask[..., None]) + colour * mask[..., None]
    rgb = rgb * (1 - iris[..., None]) + iris_rgb * iris[..., None]
    rgb = rgb * (1 - pupil[..., None]) + np.array([0.04, 0.03, 0.06], np.float32) * pupil[..., None]
    outline = ring(1.02, 1.16)
    rgb = rgb * (1 - 0.8 * outline[..., None])
    alpha = np.maximum(alpha, np.clip((1.16 - u) / 0.06, 0, 1))
    # a point of light in each pupil
    gx = (np.cos(ang) * d1 + rad * 0.14); gy = (np.sin(ang) * d1 + rad * 0.16)
    glint = np.clip(1.0 - np.sqrt(gx * gx + gy * gy) / (rad * 0.13), 0, 1)
    rgb = rgb * (1 - glint[..., None]) + glint[..., None]
    out = np.dstack([np.clip(rgb, 0, 1), np.clip(alpha, 0, 1)])
    img = Image.fromarray((out * 255).astype(np.uint8), "RGBA")
    return img.resize((size, size), Image.LANCZOS)


# ---- The rows ------------------------------------------------------------------


def _loop(i: int, n: int) -> Tuple[float, float, float]:
    ph = i / max(1, n)
    return ph, math.sin(math.tau * ph), math.cos(math.tau * ph)


def _idle(i: int, n: int) -> Pose:
    # It pants. Its back goes up and down, and its stalks look about.
    ph, s, c = _loop(i, n)
    return P(phase=ph, tall=1.0 + 0.035 * s, head=(-0.6 * s, 1.5 * s), ear=2.5 * c, stalk=7.0 * s, tongue=0.7 + 0.3 * abs(s),
             eyes="closed" if i == n - 2 else "open", flank="closed" if i == 1 else "open")


def _walk(i: int, n: int) -> Pose:
    # A wave goes down its body from its head: it goes long (the head goes
    # forward) and then short (the tail comes after it).
    ph, s, c = _loop(i, n)
    return P(phase=ph, amp=0.2, tall=1.0 - 0.04 * s, reach=2.6 * s, tail=2.6 * c, head=(-0.8 * c, 3.0 * c), ear=9.0 * c, stalk=-14.0 + 6.0 * s,
             bud="open" if i in (4, 5) else "closed", flank="closed" if i == 7 else "open")


def _hurt(i: int, n: int) -> Pose:
    struck = P(amp=0.0, tall=1.26, tail=9.0, reach=-4.0, head=(-2.0, -14.0), ear=-34.0, stalk=30.0, eyes="wince", flank="wide", bud="wide")
    back = P(amp=0.0, tall=1.08, tail=3.0, reach=-1.0, head=(-0.6, -5.0), ear=-8.0, stalk=10.0, eyes="wince", flank="open", bud="open")
    return keys(i / max(1, n - 1), [(0.0, P(eyes="wide", flank="wide", bud="wide", ear=-16.0)), (0.34, struck), (0.67, struck), (1.0, back)])


def _death(i: int, n: int) -> Pose:
    # It goes flat and long, its head goes down, and the dream goes out of it:
    # the face on its back and the eyes in its flank are gone.
    u = i / max(1, n - 1)
    hit = P(amp=0.0, tall=1.2, tail=6.0, reach=-3.0, head=(-2.0, -12.0), ear=-30.0, stalk=30.0, eyes="wince", flank="wide", bud="wide")
    sag = P(amp=0.0, tall=0.74, tail=1.0, reach=4.0, head=(5.0, 14.0), ear=14.0, stalk=70.0, tongue=0.8, eyes="wince", flank="closed", bud="closed", dream=0.6)
    flat = P(amp=0.0, tall=0.42, tail=-3.0, reach=9.0, head=(9.0, 26.0), ear=24.0, stalk=104.0, tongue=1.0, eyes="closed", flank="closed", bud="closed", dream=0.0)
    return keys(u, [(0.0, hit), (0.2, hit), (0.55, sag), (0.85, flat), (1.0, flat)])


POSES = {"idle": _idle, "walk": _walk, "hurt": _hurt, "death": _death}


def _render_frame(anim: str, i: int, n: int) -> Image.Image:
    pose = POSES[anim](i, n)
    img = K.new_frame()
    back = _back(pose)
    neck = back[-1]
    lift, tilt = pose["head"]  # type: ignore[misc]
    tall = float(pose["tall"])  # type: ignore[arg-type]
    # The middle of the head: in front of the neck and over it. A body that
    # is low has a low head.
    head = (neck[0] + 9.0, GROUND - 17.0 * min(1.0, 0.3 + 0.7 * tall) + float(lift) - 0.0)
    head = (head[0], min(head[1], GROUND - 9.0))
    turn = float(tilt)

    def on_head(x: float, y: float) -> Point:
        p = turned((x, y), turn)
        return (head[0] + p[0], head[1] + p[1])

    K.place(img, _ear(False), on_head(4.6, -8.6), "far_ear", turn + float(pose["ear"]) * 0.6 - 8.0)  # type: ignore[arg-type]
    K.place(img, _body(pose), (0.0, 0.0), "body")
    # Its two stalks, from the top of its head; an eye at the end of each.
    sway = float(pose["stalk"])  # type: ignore[arg-type]
    phase = math.tau * float(pose["phase"])  # type: ignore[arg-type]
    stalks = []
    for k, (root, lead) in enumerate((((4.0, -10.0), 0.9), ((-2.4, -10.4), 0.0))):
        base = on_head(*root)
        at = pin(base)
        chain = R.chain((base[0] - at[0], base[1] - at[1]), 4, 2.9, -90.0 + sway + turn - 8.0 * k, wave=7.0, curl=3.0 + 0.1 * sway, phase=phase, lead=lead)
        stalks.append((at, chain))
    for k, (at, chain) in enumerate(stalks):
        K.place(img, R.ribbon(K, ("puppy_slug_stalk", k), [chain], 2.3, SKIN if k else SKIN_DARK, None, taper=0.8), at, f"stalk_{k}", 0.0)
    K.place(img, _head(str(pose["eyes"])), head, "head", turn)
    for k, (at, chain) in enumerate(stalks):
        K.place(img, _stalk_eye(str(pose["eyes"])), (at[0] + chain[-1][0], at[1] + chain[-1][1]), f"stalk_eye_{k}", 0.0)
    out = float(pose["tongue"])  # type: ignore[arg-type]
    if out > 0.05:
        K.place(img, _tongue(out), on_head(11.0, 8.0), "tongue", turn * 0.5)
    K.place(img, _ear(True), on_head(-5.6, -6.6), "near_ear", turn + float(pose["ear"]))  # type: ignore[arg-type]
    if anim == "hurt" and 0 < i < n - 1:
        K.place(img, _stars(3), (head[0] - 2.0, head[1] - 22.0), "stars", 20.0 * i)
    return K.downsample(img)


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    return _render_frame(animation, frame_idx, nframes)


#: The body the game moves: the slug from its tail to its nose, up to its
#: back. Its stalks and its ears are not of it. It is the box of the old sheet.
BODY_BOX = (4.0, 44.0, 118.0, GROUND)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    outputs = K.render(TARGET_NAME, ROWS, _render_frame, out_dir, ACTOR_METADATA, BODY_BOX)
    skin = Path(out_dir) / DREAM_SKIN_FILE
    dream_skin().save(skin)
    return outputs + [skin]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Puppy Slug sprite target.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA, "sheet_files": SHEET_FILES}}


if __name__ == "__main__":
    raise SystemExit(main())
