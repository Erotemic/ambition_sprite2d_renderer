"""Sprite generator for the Hand Saint: an icon of a saint whose head is an
open hand.

The look (redrawn 2026-10-11): a figure in a violet robe with a gold stole,
seen from the front like a painted icon. Where its head would be there is a
hand, palm out, with seven fingers and a thumb on each side, an eye in its
palm, and a gold halo behind it. Its two arms are raised to bless, and each
ends in a hand with six fingers. Under the hem of the robe it stands on two
more hands, on their fingertips. It is the same from both sides.

It walks on the hands under its robe. Its attack is the reach: it draws its
hands in, and its arms go out far longer than arms are, with the fingers
spread. Struck, the eye shuts and the fingers of its head curl. Dead, the
head closes into a fist, the robe goes down in a heap and the halo falls
on it.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ._ai_era_kit import OUTLINE, WHITE, Kit, Point, RGBA, actor_metadata, ease, lerp

TARGET_NAME = "hand_saint"
FRAME_SIZE = (232, 208)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 140),
    ("walk", 8, 100),
    ("slash", 6, 85),
    ("hurt", 4, 90),
    ("death", 8, 115),
]

GROUND = 198.0
CX = 104.0
#: The robe at rest: how high its shoulders are, how wide its hem is (half).
SHOULDER, HEM = 104.0, 38.0

ROBE: RGBA = (98, 70, 164, 255)
ROBE_DARK: RGBA = (64, 44, 118, 255)
ROBE_LIGHT: RGBA = (138, 108, 204, 255)
GOLD: RGBA = (246, 204, 96, 255)
GOLD_DARK: RGBA = (196, 146, 54, 255)
SKIN: RGBA = (248, 226, 208, 255)
SKIN_SHADE: RGBA = (222, 178, 164, 255)
EYE: RGBA = (254, 252, 246, 255)
IRIS: RGBA = (226, 168, 48, 255)
INK: RGBA = (44, 28, 56, 255)

K = Kit(FRAME_SIZE)

ACTOR_METADATA = actor_metadata(
    "npc_hand_saint",
    "Hand Saint",
    attack_row="slash",
    ranged=False,
    traits=["ai_era", "icon", "enemy", "heavy"],
    description=(
        "The Hand Saint is a robed icon whose head is an open hand with seven fingers, two thumbs and "
        "an eye in its palm, under a gold halo. Its arms end in hands of six fingers, and it stands on "
        "two more hands under its robe."
    ),
    gameplay="A heavy melee enemy. Its attack is a reach: its arms go out much further than they should.",
)


def _aim(angle: float) -> Point:
    """A direction: 0 is down, 90 is to the right, 180 is up."""
    a = math.radians(angle)
    return (math.sin(a), math.cos(a))


# ---- The pose ----------------------------------------------------------------


def _pose(anim: str, i: int, n: int) -> Dict[str, object]:
    ph = math.tau * i / max(1, n)
    pose: Dict[str, object] = {
        "x": 0.0,
        "bob": 0.0,
        "lean": 0.0,
        # How far the robe has gone down in a heap, 0 to 1.
        "heap": 0.0,
        "sway": 0.0,
        # How far the fingers of the head are curled, 0 to 1.
        "curl": 0.0,
        "eye": "open",
        "look": 0.0,
        "halo": (0.0, 0.0, 0.0),
        "halo_turn": 0.0,
        # Each arm (left, right): the way its sleeve points, the way its
        # forearm points, how long its forearm is, how its fingers are spread.
        "arms": ((-128.0, -168.0, 6.0, 1.0), (128.0, 168.0, 6.0, 1.0)),
        # The hands it stands on: how far each has stepped, how high it is.
        "feet": ((0.0, 0.0), (0.0, 0.0)),
        "rays": 0.0,
    }
    if anim == "idle":
        breath = math.sin(ph)
        pose.update(
            bob=1.6 * breath,
            sway=1.0 * math.sin(ph + 0.6),
            eye="closed" if i == 4 else "open",
            look=2.0 * math.sin(ph),
            halo_turn=15.0 * i,
            arms=((-128.0 - 6.0 * breath, -168.0 + 8.0 * math.sin(ph + 1.0), 6.0, 1.0 + 0.15 * breath),
                  (128.0 + 6.0 * breath, 168.0 - 8.0 * math.sin(ph + 1.0), 6.0, 1.0 + 0.15 * breath)),
            rays=0.5 + 0.5 * max(0.0, math.sin(ph * 2.0)),
        )
    elif anim == "walk":
        step = math.sin(ph)
        pose.update(
            bob=1.8 * abs(math.cos(ph)) - 0.9,
            lean=3.0,
            sway=4.0 * step,
            look=3.0,
            halo_turn=11.25 * i,
            arms=((-120.0 + 5.0 * step, -160.0 + 6.0 * step, 6.0, 1.0), (120.0 + 5.0 * step, 160.0 + 6.0 * step, 6.0, 1.0)),
            feet=((7.0 * step, 4.0 * max(0.0, math.cos(ph))), (-7.0 * step, 4.0 * max(0.0, -math.cos(ph)))),
            rays=0.4,
        )
    elif anim == "slash":
        keys = [
            # x, lean, left arm, right arm, eye, curl
            (-2.0, -3.0, (-70.0, -140.0, 6.0, 0.6), (70.0, 140.0, 6.0, 0.6), "open", 0.1),
            (-4.0, -6.0, (-40.0, -110.0, 5.0, 0.3), (40.0, 110.0, 5.0, 0.3), "half", 0.25),
            (4.0, 6.0, (60.0, 84.0, 32.0, 1.5), (104.0, 96.0, 36.0, 1.5), "wide", 0.0),
            (6.0, 8.0, (70.0, 92.0, 44.0, 1.6), (98.0, 90.0, 48.0, 1.6), "wide", 0.0),
            (3.0, 4.0, (20.0, 96.0, 26.0, 1.2), (110.0, 100.0, 30.0, 1.2), "open", 0.0),
            (0.0, 0.0, (-110.0, -160.0, 8.0, 1.0), (118.0, 160.0, 8.0, 1.0), "open", 0.0),
        ]
        x, lean, left, right, eye, curl = keys[i % len(keys)]
        pose.update(x=x, lean=lean, arms=(left, right), eye=eye, curl=curl, look=4.0, halo_turn=20.0 * i,
                    rays=(0.4, 0.7, 1.0, 1.0, 0.6, 0.4)[i % 6], sway=lean)
    elif anim == "hurt":
        pose.update(
            x=(-4.0, -7.0, -4.0, -1.0)[i % 4],
            lean=(-8.0, -11.0, -6.0, -2.0)[i % 4],
            sway=(-8.0, -10.0, -5.0, -2.0)[i % 4],
            curl=(0.75, 0.9, 0.6, 0.25)[i % 4],
            eye="closed" if i < 3 else "half",
            halo=((8.0, -4.0, 16.0), (12.0, -6.0, 26.0), (7.0, -3.0, 14.0), (2.0, 0.0, 4.0))[i % 4],
            arms=(((-150.0, -110.0, 8.0, 1.5), (160.0, 120.0, 8.0, 1.5)), ((-164.0, -126.0, 9.0, 1.6), (170.0, 140.0, 9.0, 1.6)),
                  ((-140.0, -150.0, 7.0, 1.3), (146.0, 150.0, 7.0, 1.3)), ((-130.0, -166.0, 6.0, 1.1), (130.0, 166.0, 6.0, 1.1)))[i % 4],
        )
    elif anim == "death":
        t = i / max(1, n - 1)
        heap = ease((t - 0.2) / 0.7)
        pose.update(
            lean=-4.0 * (1.0 - heap),
            heap=heap,
            sway=0.0,
            curl=ease(t / 0.5),
            eye="closed" if i >= 1 else "half",
            # The halo falls, and lies on the heap.
            halo=(10.0 * heap, 44.0 * heap * heap, 80.0 * heap),
            arms=((-128.0 + 110.0 * ease(t * 1.6), -168.0 + 160.0 * ease(t * 1.4), 6.0, 0.5),
                  (128.0 - 110.0 * ease(t * 1.6), 168.0 - 160.0 * ease(t * 1.4), 6.0, 0.5)),
        )
    return pose


# ---- Pieces ------------------------------------------------------------------


def _robe(heap: float, sway: float):
    """The robe from the middle of its hem at ``home``: a bell that the walk
    sways and that goes down in a heap."""
    heap, sway = round(heap, 2), round(sway, 1)
    top = SHOULDER * (1.0 - 0.72 * heap)
    hem = HEM + 12.0 * heap
    shoulder = 21.0 + 6.0 * heap

    def outline() -> List[Point]:
        left = [K.at(-hem + sway * 0.4, -12.0), K.at(-hem * 0.86 + sway * 0.3, -top * 0.45), K.at(-shoulder - 3.0, -top * 0.86), K.at(-shoulder + 5.0, -top)]
        right = [K.at(shoulder - 5.0, -top), K.at(shoulder + 3.0, -top * 0.86), K.at(hem * 0.86 + sway * 0.3, -top * 0.45), K.at(hem + sway * 0.4, -12.0)]
        # The hem is scallops.
        scallops = []
        for k in range(9):
            x = hem - 2.0 * hem * k / 8.0 + sway * 0.4
            scallops.append(K.at(x, -12.0 + (4.0 if k % 2 else 0.0)))
        return left + right + scallops[1:-1]

    def shape(d) -> None:
        K.poly(d, outline(), WHITE)
        K.oval(d, K.at(0.0, -top + 2.0), shoulder - 3.0, 7.0, WHITE)

    def detail(d) -> None:
        # Folds, a gold stole down the middle with a hand on it, a gold hem.
        for x in (-0.55, 0.55):
            K.line(d, [K.at(x * shoulder * 1.2, -top * 0.8), K.at(x * hem + sway * 0.3, -10.0)], ROBE_DARK, 1.4)
        K.poly(d, [K.at(-7.0, -top - 4.0), K.at(7.0, -top - 4.0), K.at(9.0 + sway * 0.3, -8.0), K.at(-9.0 + sway * 0.3, -8.0)], GOLD)
        for sign in (-1.0, 1.0):
            K.line(d, [K.at(sign * 7.0, -top - 4.0), K.at(sign * 9.0 + sway * 0.3, -8.0)], GOLD_DARK, 1.0)
        for k in range(3):
            y = -top * (0.74 - 0.24 * k)
            if y > -26.0:
                continue
            K.oval(d, K.at(sway * 0.1, y), 3.4, 3.8, GOLD_DARK)
            for a in (-40.0, -14.0, 14.0, 40.0):
                dx, dy = _aim(180.0 + a)
                K.stroke(d, [K.at(sway * 0.1 + dx * 3.0, y + dy * 3.0), K.at(sway * 0.1 + dx * 7.5, y + dy * 7.5)], GOLD_DARK, 1.5)
        K.rrect(d, K.home[0] - hem - 8.0, K.home[1] - 19.0, K.home[0] + hem + 8.0, K.home[1] - 15.5, 0.0, GOLD)
        K.oval(d, K.at(0.0, -top + 2.0), shoulder - 4.0, 5.0, GOLD)
        K.oval(d, K.at(0.0, -top + 1.0), shoulder - 8.0, 3.0, ROBE_DARK)

    return K.solid(("robe", heap, sway), shape, ROBE, detail)


#: The seven fingers of the head: the way each points, from straight up.
HEAD_FINGERS = (-62.0, -41.0, -20.0, 0.0, 20.0, 41.0, 62.0)


def _head(curl: float, eye: str, look: float):
    """The head: an open hand, its palm at ``home``, with an eye in the palm."""
    curl, look = round(curl, 2), round(look, 1)
    palm = (20.0, 22.0)
    strokes: List[Tuple[List[Point], float]] = [([K.at(0.0, 16.0), K.at(0.0, 34.0)], 15.0)]
    for k, angle in enumerate(HEAD_FINGERS):
        dx, dy = _aim(180.0 + angle)
        length = 23.0 - 3.5 * abs(k - 3) + (1.5 if k == 2 else 0.0)
        root = (dx * 16.0, dy * 19.0 - 2.0)
        open_tip = (root[0] + dx * length, root[1] + dy * length)
        fist = (dx * 9.0, -13.0 + 2.5 * abs(k - 3))
        tip = (lerp(open_tip[0], fist[0], curl), lerp(open_tip[1], fist[1], curl))
        knee = (lerp((root[0] + open_tip[0]) / 2.0, root[0] + dx * 7.0, curl), lerp((root[1] + open_tip[1]) / 2.0, root[1] + dy * 9.0, curl))
        strokes.append(([K.at(*root), K.at(*knee), K.at(*tip)], 6.6))
    # A thumb on each side.
    for sign in (-1.0, 1.0):
        root = (sign * 17.0, 4.0)
        tip = (lerp(sign * 31.0, sign * 9.0, curl), lerp(-9.0, 6.0, curl))
        strokes.append(([K.at(*root), K.at((root[0] + tip[0]) / 2.0 + sign * 2.0 * (1.0 - curl), (root[1] + tip[1]) / 2.0 + 3.0), K.at(*tip)], 7.4))

    def shape(d) -> None:
        K.oval(d, K.home, palm[0], palm[1], WHITE)
        for pts, width in strokes:
            K.stroke(d, pts, WHITE, width)

    def detail(d) -> None:
        # The joints of the fingers, the lines of the palm.
        for pts, width in strokes[1:8]:
            mid = pts[1]
            K.line(d, [(mid[0] - width * 0.3, mid[1] + 0.6), (mid[0] + width * 0.3, mid[1] - 0.6)], SKIN_SHADE, 0.8)
        K.line(d, [K.at(-13.0, 9.0), K.at(-4.0, 13.0), K.at(8.0, 12.0), K.at(14.0, 7.0)], SKIN_SHADE, 0.9)
        if curl > 0.6:
            # A fist: the eye is under the fingers, and the knuckles show.
            for x in (-12.0, -6.0, 0.0, 6.0, 12.0):
                K.line(d, [K.at(x - 2.4, -9.0), K.at(x, -11.0), K.at(x + 2.4, -9.0)], SKIN_SHADE, 0.9)
            K.line(d, [K.at(-14.0, -3.0), K.at(0.0, -1.0), K.at(14.0, -3.0)], SKIN_SHADE, 0.9)
            return
        c = K.at(look * 0.5, -1.0)
        if eye == "closed":
            # A shut lid, with its lashes.
            K.stroke(d, [(c[0] - 11.0, c[1] + 0.5), (c[0] - 4.0, c[1] + 1.8), (c[0] + 4.0, c[1] + 1.8), (c[0] + 11.0, c[1] + 0.5)], INK, 1.6)
            for x in (-7.0, -2.4, 2.4, 7.0):
                K.stroke(d, [(c[0] + x, c[1] + 1.8), (c[0] + x * 1.2, c[1] + 5.0)], INK, 1.0)
            return
        open_by = {"open": 6.6, "half": 3.6, "wide": 9.0}[eye]
        almond = [(c[0] - 12.0, c[1]), (c[0] - 6.0, c[1] - open_by), (c[0] + 6.0, c[1] - open_by), (c[0] + 12.0, c[1]), (c[0] + 6.0, c[1] + open_by * 0.8),
                  (c[0] - 6.0, c[1] + open_by * 0.8)]
        K.poly(d, almond, EYE, INK, 1.1)
        r = min(5.4, open_by * 0.92)
        K.oval(d, (c[0] + look, c[1]), r, r, IRIS, INK, 0.7)
        K.oval(d, (c[0] + look, c[1]), r * 0.46, r * 0.46, INK)
        K.oval(d, (c[0] + look - 1.6, c[1] - 1.6), 1.0, 1.0, WHITE)
        K.line(d, [(c[0] - 12.0, c[1]), (c[0] - 6.0, c[1] - open_by), (c[0] + 6.0, c[1] - open_by), (c[0] + 12.0, c[1])], INK, 1.7)

    return K.solid(("head", curl, eye, look), shape, SKIN, detail, shade_colour=SKIN_SHADE, shade=0.7)


def _halo(rays: float):
    """The halo, its middle at ``home``: a ring of gold with rays round it."""
    rays = round(rays, 1)

    def paint(d) -> None:
        for colour, width in ((OUTLINE, 6.2), (GOLD, 3.8)):
            ring = [K.at(42.0 * math.cos(math.tau * j / 48), 42.0 * math.sin(math.tau * j / 48)) for j in range(49)]
            K.line(d, ring, colour, width)
        K.line(d, [K.at(41.0 * math.cos(a), 41.0 * math.sin(a)) for a in (math.radians(v) for v in range(200, 251, 5))], (255, 240, 180, 255), 1.2)
        for j in range(12):
            a = math.tau * j / 12
            near, far = 47.0, 47.0 + 3.0 + 5.0 * rays * (1.0 if j % 2 == 0 else 0.5)
            K.stroke(d, [K.at(near * math.cos(a), near * math.sin(a)), K.at(far * math.cos(a), far * math.sin(a))], GOLD, 1.8)

    return K.piece(("halo", rays), paint)


def _sleeve():
    """A sleeve from the shoulder at ``home`` down: a bell with a gold cuff."""

    def shape(d) -> None:
        K.poly(d, [K.at(-6.0, -3.0), K.at(6.0, -3.0), K.at(11.0, 22.0), K.at(-11.0, 22.0)], WHITE)
        K.oval(d, K.home, 6.5, 6.0, WHITE)

    def detail(d) -> None:
        K.rrect(d, K.home[0] - 14.0, K.home[1] + 17.0, K.home[0] + 14.0, K.home[1] + 25.0, 0.0, GOLD)
        K.line(d, [K.at(0.0, 0.0), K.at(2.0, 17.0)], ROBE_DARK, 1.0)

    return K.solid(("sleeve",), shape, ROBE, detail)


def _forearm(length: float):
    """The arm out of the sleeve, from ``home`` down. A long one has more
    joints than an arm has."""
    length = round(length * 2.0) / 2.0

    def shape(d) -> None:
        K.stroke(d, [K.home, K.at(0.0, length)], WHITE, 7.0)
        for k in range(1, int(length // 16) + 1):
            K.oval(d, K.at(0.0, 16.0 * k - 4.0), 4.6, 4.2, WHITE)

    def detail(d) -> None:
        for k in range(1, int(length // 16) + 1):
            K.line(d, [K.at(-3.0, 16.0 * k - 4.0), K.at(3.0, 16.0 * k - 4.0)], SKIN_SHADE, 0.8)

    return K.solid(("forearm", length), shape, SKIN, detail, shade_colour=SKIN_SHADE, shade=0.6)


def _hand(spread: float):
    """A hand of six fingers from its wrist at ``home`` down."""
    spread = round(spread, 1)
    strokes: List[Tuple[List[Point], float]] = []
    for k, angle in enumerate((-50.0, -30.0, -10.0, 10.0, 30.0, 50.0)):
        dx, dy = _aim(angle * spread)
        length = 11.5 - 1.6 * abs(k - 2.5)
        strokes.append(([K.at(dx * 5.0, 7.0 + dy * 5.0), K.at(dx * (5.0 + length), 7.0 + dy * (5.0 + length))], 3.6))
    strokes.append(([K.at(-6.0, 5.0), K.at(-12.0, 0.0)], 4.0))

    def shape(d) -> None:
        K.oval(d, K.at(0.0, 7.0), 7.4, 7.0, WHITE)
        for pts, width in strokes:
            K.stroke(d, pts, WHITE, width)

    def detail(d) -> None:
        K.line(d, [K.at(-4.0, 8.0), K.at(0.0, 10.0), K.at(4.0, 8.0)], SKIN_SHADE, 0.8)

    return K.solid(("hand", spread), shape, SKIN, detail, shade_colour=SKIN_SHADE, shade=0.6)


def _foot(lift: float):
    """A hand it stands on, from the ground under it at ``home`` up: on its
    fingertips, or with two of them lifted."""
    lift = round(lift * 2.0) / 2.0

    def shape(d) -> None:
        K.oval(d, K.at(0.0, -18.0 - lift), 10.5, 7.0, WHITE)
        for k, x in enumerate((-8.0, -2.8, 2.8, 8.0)):
            up = lift * (1.0 if k % 2 == 0 else 0.4)
            K.stroke(d, [K.at(x, -15.0 - lift), K.at(x * 1.25, -7.5 - up * 0.6), K.at(x * 1.15, -2.0 - up)], WHITE, 4.0)

    return K.solid(("foot", lift), shape, SKIN, None, shade_colour=SKIN_SHADE, shade=0.6)


# ---- Frames ------------------------------------------------------------------


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose(anim, frame_idx, nframes)
    img = K.new_frame()
    heap = float(pose["heap"])
    lean = float(pose["lean"])
    base = (CX + float(pose["x"]), GROUND)
    top = SHOULDER * (1.0 - 0.72 * heap)
    bob = float(pose["bob"]) * (1.0 - heap)
    # Its shoulders, and its head on them. A lean moves the top of it.
    shoulders = (base[0] + lean * 0.9, base[1] - 6.0 - top - bob)
    head = (shoulders[0] + lean * 0.5, shoulders[1] - 30.0 + 22.0 * heap)

    hx, hy, halo_turn = pose["halo"]  # type: ignore[misc]
    K.place(img, _halo(float(pose["rays"])), (head[0] + hx, head[1] - 4.0 + hy), "halo", float(pose["halo_turn"]) + halo_turn)

    if heap < 0.6:
        for k, (step, lift) in enumerate(pose["feet"]):  # type: ignore[arg-type]
            K.place(img, _foot(lift), (base[0] + (-16.0 if k == 0 else 16.0) + step, GROUND), f"foot_{k}")

    K.place(img, _robe(heap, float(pose["sway"])), (base[0], base[1] - bob * 0.3), "robe")

    for k, (sleeve, fore, length, spread) in enumerate(pose["arms"]):  # type: ignore[arg-type]
        side = -1.0 if k == 0 else 1.0
        shoulder = (shoulders[0] + side * (20.0 + 5.0 * heap), shoulders[1] + 8.0)
        sx, sy = _aim(sleeve)
        cuff = (shoulder[0] + sx * 21.0, shoulder[1] + sy * 21.0)
        fx, fy = _aim(fore)
        wrist = (cuff[0] + fx * length, cuff[1] + fy * length)
        name = "left" if k == 0 else "right"
        K.place(img, _forearm(length), cuff, f"{name}_forearm", -fore)
        K.place(img, _hand(spread), wrist, f"{name}_hand", -fore)
        K.place(img, _sleeve(), shoulder, f"{name}_sleeve", -sleeve)

    K.place(img, _head(float(pose["curl"]), str(pose["eye"]), float(pose["look"])), head, "head", lean * 0.8)
    return K.downsample(img)


#: The gameplay body: the robe and the palm of the head, without the halo,
#: the fingers of the head and the arms.
BODY_BOX = (CX - HEM, GROUND - SHOULDER - 62.0, CX + HEM, GROUND + 1.0)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return K.render(TARGET_NAME, ROWS, _render_frame, out_dir, ACTOR_METADATA, BODY_BOX)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Hand Saint sprite target.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
