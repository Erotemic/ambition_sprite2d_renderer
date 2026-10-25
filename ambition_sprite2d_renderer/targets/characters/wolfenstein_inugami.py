"""Sprite generator for the Inugami: Wolfenstein's head, risen as a spirit.

Jon (2026-10-20): "an additional phase to Wolfenstein where the head
resurrects as an inugami and you fight the floating spectral head as an
additional boss".

The story: the regime sewed a wolf's head onto a soldier's body and gave it
orders. When the body dies, the wolf is free at last: the stitches round the
neck pop, the head tears itself off the body, and the ghost fire of an
inugami (the dog spirit of the old stories, made from a dog's severed head)
catches in it. It is a hunting dog of the regime, set free (Jon, 2026-10-22:
"it just doesn't have a strong boss identity"): it stalks you, it lunges, it
pounces, it calls his lightning down on the floor, and the leash they kept
it on is a ghost chain it cracks along the floor.

The look. It is HIS head: the same skull, jaw, ears, eyes and brain in a jar
(``wolfenstein.WolfHead``), drawn in the ink of a spirit (``SPIRIT``): a red
spectral glow (Jon, 2026-10-20), rose fur, a maroon outline, eyes that burn
pale gold with black points in them, a mouth lit from inside. The torn stitches hang from under its ruff, and ghost
fire streams from where the neck was. It is a little transparent. When it
dies the fire goes out of it, the spirit leaves as a wisp, and what is left
on the floor is his head again, in its own colours.

It faces right. There is no drop shadow. The glow round it is part of the
spirit, not a shadow on a floor.

Its ward (Jon, 2026-10-24: "default inugami should not have ghost fire around
its head, we should add them only during the chase where the wolf is
effectively invincible"): the four blue hitodama circle it only in the
``ward_`` rows, which the fight draws while the ward is lit (the chase). The
ward kindles in ``ward_kindle``, Kagero's talismans hold it in ``ward_bound``,
and it breaks in ``dispel``. His lightning is still in it: ``storm_tell``.

Rows: the rise (the head comes off the body; it is his own head until the
fire catches), the float, the drift and the hunt, its crash out of the arena,
and a tell and a strike row for each move of its fight
(``ambition_content_modules::inugami`` draws them by name). The chain's tip
and the lightning's bolts are the game's (sparks and rays); a row draws the
chain from the neck to the bottom of its frame.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

from ...authoring import rigdoc
from ...authoring.texel_density import published_frame
from ._ai_era_kit import OUTLINE, WHITE, RGBA, Kit, Point, Pose, keys, lerp, mix, turned
from . import _person_rig as R
from . import wolfenstein as W

TARGET_NAME = "wolfenstein_inugami"
DISPLAY_NAME = "Inugami Wolfenstein"

#: The frame, in its own pixels. The head is drawn ``ZOOM`` frame pixels to a
#: pixel of his head (his head kit draws it 1.2 to one of his 320 px frame).
FRAME_SIZE = (256, 256)
ZOOM = 2.0
#: The body the game moves, in the head's own pixels from its middle: the
#: skull, the muzzle, the ruff and the jar (not the ears or the fire).
BODY_HEAD_PX = (-20.0, -38.0, 26.0, 17.0)
#: Where the middle of the head is at rest: the body box is then in the
#: middle of the frame.
REST_AT: Point = (FRAME_SIZE[0] / 2.0 - (BODY_HEAD_PX[0] + BODY_HEAD_PX[2]) / 2.0 * ZOOM,
                  FRAME_SIZE[1] / 2.0 - (BODY_HEAD_PX[1] + BODY_HEAD_PX[3]) / 2.0 * ZOOM)
#: Its body box stands this many world units tall in the fight
#: (``boss_profiles.ron``, ``wolfenstein_inugami``): a giant head (Jon,
#: 2026-10-20: "so it's a giant head"), half as tall again as he stood. At the
#: game's texel density its frames would be some 1700 px. It is published at
#: ``DENSITY``, the median character's: its frame (830 px) with its art's
#: margin then fits the largest impostor cell (1152 px), which its hit flash
#: and its fades are drawn in.
WORLD_HEIGHT = 212.0
DENSITY = 1.68
OUT = published_frame(FRAME_SIZE, (BODY_HEAD_PX[3] - BODY_HEAD_PX[1]) * ZOOM, WORLD_HEIGHT, DENSITY)
SUPERSAMPLE = 2

# ---- The ink of a spirit -------------------------------------------------------

INK: RGBA = (58, 8, 22, 255)
#: Its fire is the ghost fire that came out of his neck.
FIRE_OUT, FIRE_MID, FIRE_CORE = W.GHOST_OUT, W.GHOST_MID, W.GHOST_CORE
GLOW: RGBA = (255, 70, 80, 255)
#: The onibi round it are blue (Jon, 2026-10-20: "the spirits around the
#: head should be blue"): cold fire about the red head.
ONIBI_OUT: RGBA = (70, 120, 255, 210)
ONIBI_MID: RGBA = (130, 210, 255, 235)
ONIBI_CORE: RGBA = (236, 250, 255, 255)
#: The leash: a ghost chain, fire in the shape of links.
CHAIN_OUT: RGBA = (230, 40, 64, 255)
CHAIN_CORE: RGBA = (255, 226, 196, 255)
RING: RGBA = (255, 214, 206, 255)
RING_DARK: RGBA = (176, 24, 48, 255)
THREAD: RGBA = (120, 22, 40, 255)

#: His head as a spirit: the same pieces as his own head, in a red spectral
#: ink (Jon, 2026-10-20: "a red spectral glow").
SPIRIT = W.HeadInk(
    "spirit",
    FUR=(236, 128, 132, 255), FUR_DARK=(196, 70, 88, 255), FUR_DEEP=(122, 24, 50, 255), FUR_LIGHT=(255, 214, 206, 255),
    EAR_INNER=(255, 160, 150, 255), NOSE=(70, 10, 26, 255), NOSE_LIGHT=(210, 110, 120, 255),
    GUM=(255, 150, 90, 255), MOUTH=(60, 6, 20, 255), TONGUE=(255, 196, 120, 255), TONGUE_LINE=(220, 100, 70, 255), TOOTH=(255, 240, 232, 255),
    EYE_WHITE=(255, 246, 200, 255), VEIN=(255, 120, 60, 255), IRIS=(40, 0, 8, 255), GLAZE=(220, 160, 160, 255), GLAZE_PUPIL=(140, 60, 70, 255),
    ARC_GLOW=W.ARC_GLOW, ARC_CORE=W.ARC_CORE, SERUM=W.SERUM, SERUM_CORE=W.SERUM_CORE, STITCH=THREAD, OUTLINE=INK,
    BRAIN=(255, 176, 186, 255), BRAIN_SHADE=(214, 110, 130, 255), BRAIN_LIGHT=(255, 226, 230, 255), BRAIN_FISSURE=(176, 70, 96, 255),
    JAR_FLUID=(255, 110, 110, 120), JAR_FLUID_TOP=(255, 190, 180, 150), JAR_GLASS_EDGE=(255, 190, 190, 255), GLASS=(255, 222, 222, 255),
    BUBBLE=(255, 236, 230, 200), GLINT=W.GLINT, GLINT_FAINT=W.GLINT_FAINT, BOLT=(220, 150, 160, 255), BOLT_DARK=(140, 60, 80, 255),
    COLLAR_LIGHT=(255, 210, 210, 255),
)
#: As a spirit it is a little transparent: the whole head fades as one
#: picture, so its pieces do not show through each other.
SPIRIT_OPACITY = 0.9

#: The frame's kit, and a kit for each ink of the head (a kit's outline is
#: its ink).
K = Kit(FRAME_SIZE, SUPERSAMPLE, out=OUT)
LIVING_HEAD = W.WolfHead(Kit(FRAME_SIZE, SUPERSAMPLE, out=OUT, zoom=ZOOM), W.LIVING)
SPIRIT_HEAD = W.WolfHead(Kit(FRAME_SIZE, SUPERSAMPLE, out=OUT, zoom=ZOOM, ink=INK), SPIRIT)

#: Where the neck was, in head pixels: the fire comes out of it.
NECK: Point = (-1.0, 15.0)
#: The tip of its nose, in head pixels.
NOSE_TIP: Point = (25.0, -1.0)


def _r(v: float, step: float = 1.0) -> float:
    """``v`` on a grid: a piece painted for one frame is the piece of every
    frame that rounds the same."""
    return round(v / step) * step


def _head_point(pose: Pose, p: Point) -> Point:
    """A point of the head (head pixels from its middle) in the frame."""
    at = pose["at"]
    q = turned((p[0] * ZOOM, p[1] * ZOOM * float(pose["sq"])), float(pose["rot"]))  # type: ignore[arg-type]
    return (REST_AT[0] + at[0] + q[0], REST_AT[1] + at[1] + q[1])  # type: ignore[index]


# ---- Pieces --------------------------------------------------------------------


def _tongue_of_fire(length: float, width: float, bend: float):
    """A tongue of ghost fire from ``home`` along +x: ``length`` long,
    ``width`` wide at its root, bent ``bend`` (frame pixels) to one side at
    its tip. Three layers: the red outside, the bright middle, the white core."""
    length, width, bend = _r(length, 2.0), _r(width, 1.0), _r(bend, 2.0)

    def side(scale: float, sign: float) -> List[Point]:
        out = []
        for k in range(9):
            t = k / 8.0
            w = width * scale * (1.0 - t) ** 0.7 * (0.75 + 0.5 * math.sin(math.pi * min(1.0, t * 1.6)))
            out.append(K.at(t * length * (0.6 + 0.4 * scale), bend * t * t + sign * w * 0.5))
        return out

    def paint(d) -> None:
        for scale, colour in ((1.0, FIRE_OUT), (0.62, FIRE_MID), (0.3, FIRE_CORE)):
            K.poly(d, side(scale, 1.0) + side(scale, -1.0)[::-1], colour)

    return K.piece(("fire", length, width, bend), paint)


def _wisp(size: float, flick: int = 0):
    """A ball of blue ghost fire (an onibi): a round white heart, and its flame
    licking up from it in three tongues. ``flick`` (0-2) bends the tongues."""
    size = _r(size, 1.0)
    flick = flick % 3

    def paint(d) -> None:
        lean = (-0.35, 0.0, 0.35)[flick]
        for scale, colour in ((1.0, ONIBI_OUT), (0.72, ONIBI_MID), (0.42, ONIBI_CORE)):
            r = size * scale
            for dx, tall in ((-0.55, 1.5), (0.5, 1.7), (0.0, 2.6)):
                base = r * dx
                K.poly(d, [K.at(base - r * 0.55, -r * 0.2), K.at(base + r * lean, -size * tall * scale), K.at(base + r * 0.55, -r * 0.2)], colour)
            K.oval(d, K.at(0.0, 0.0), r, r, colour)

    return K.piece(("wisp", size, flick), paint)


def _hitodama(size: float):
    """A small blue spirit (a hitodama): a round head of cold fire and its tail
    behind it, along -x (placed turned to the way it goes)."""
    size = _r(size, 1.0)

    def tail(scale: float) -> List[Point]:
        # A tail that waves as it thins, from the top of the head round the back.
        r = size * scale
        up = [K.at(-size * 4.6 * t * scale, -r * (1.0 - t) ** 0.8 + size * 0.5 * math.sin(t * 5.0) * t) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        down = [K.at(-size * 4.0 * t * scale, r * (1.0 - t) ** 1.2 + size * 0.5 * math.sin(t * 5.0) * t) for t in (1.0, 0.75, 0.5, 0.25, 0.0)]
        return up + down

    def paint(d) -> None:
        # Its cold light round it, then its fire, in three layers.
        for k, alpha in enumerate((26, 40)):
            K.oval(d, K.at(0.0, 0.0), size * (2.2 - 0.5 * k), size * (2.2 - 0.5 * k), ONIBI_MID[:3] + (alpha,))
        for scale, colour in ((1.0, ONIBI_OUT), (0.68, ONIBI_MID), (0.38, ONIBI_CORE)):
            K.poly(d, tail(scale), colour)
            K.oval(d, K.at(0.0, 0.0), size * scale, size * scale, colour)

    return K.piece(("hitodama", size), paint)


def _arc(p0: Point, p1: Point, seed: int):
    """His lightning from ``p0`` to ``p1`` (frame points): a jagged line,
    blue-white, in a glow, about ``home`` at ``p0``: place it at ``p0``."""
    p0 = (_r(p0[0], 2.0), _r(p0[1], 2.0))
    p1 = (_r(p1[0], 2.0), _r(p1[1], 2.0))
    seed = seed % 12

    def paint(d) -> None:
        pts = []
        steps = 7
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        length = max(1.0, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length
        for k in range(steps + 1):
            t = k / steps
            off = 0.0 if k in (0, steps) else 7.0 * math.sin(seed * 1.7 + k * 2.9)
            pts.append((dx * t + nx * off, dy * t + ny * off))
        K.line(d, [K.at(*q) for q in pts], W.ARC_GLOW[:3] + (150,), 5.0)
        K.line(d, [K.at(*q) for q in pts], W.ARC_CORE, 1.8)

    return K.piece(("arc", p0, p1, seed), paint)


def _ofuda(left: float):
    """Kagero's paper talisman, stuck on it: a white slip with a red seal,
    along +y. ``left`` (0-1) is how much is not yet burnt away."""
    left = _r(left, 0.125)

    def paint(d) -> None:
        tall = 22.0 * left
        if tall < 1.0:
            return
        K.poly(d, [K.at(-4.0, 0.0), K.at(4.0, 0.0), K.at(4.0, tall), K.at(-4.0, tall)], (244, 240, 228, 255), INK, 1.0)
        if tall > 8.0:
            K.line(d, [K.at(0.0, 2.5), K.at(0.0, min(tall - 2.0, 10.0))], (196, 36, 42, 255), 1.6)
        if tall > 14.0:
            K.oval(d, K.at(0.0, 15.0), 2.0, 2.0, (196, 36, 42, 255))
        if left < 1.0:
            K.line(d, [K.at(-4.0, tall), K.at(4.0, tall)], FIRE_MID, 2.0)

    return K.piece(("ofuda", left), paint)


def _glow(radius: float):
    """The cold light round the spirit: rings that fade outward."""
    radius = _r(radius, 2.0)

    def paint(d) -> None:
        for k, alpha in enumerate((14, 18, 24, 30)):
            r = radius * (1.0 - 0.14 * k)
            K.oval(d, K.at(0.0, 0.0), r, r * 0.92, GLOW[:3] + (alpha,))

    return K.piece(("glow", radius), paint)


def _chain(length: float, bend: float, links: float = 1.0):
    """The broken leash: links of ghost fire from ``home`` along +x,
    ``length`` long, its end bent ``bend`` frame pixels to one side. Only the
    first ``links`` of it (0-1) is drawn: the chain unrolls."""
    length, bend, links = _r(length, 4.0), _r(bend, 4.0), _r(links, 0.1)
    step = 12.0

    def ring(d, c: Point, angle: float, rx: float, ry: float, colour: RGBA, width: float) -> None:
        ca, sa = math.cos(angle), math.sin(angle)
        pts = []
        for k in range(12):
            a = math.tau * k / 12.0
            x, y = rx * math.cos(a), ry * math.sin(a)
            pts.append(K.at(c[0] + x * ca - y * sa, c[1] + x * sa + y * ca))
        K.line(d, pts + [pts[0]], colour, width)

    def paint(d) -> None:
        n = max(1, int(length * links / step))
        for k in range(n):
            t = (k + 0.5) * step / max(1.0, length)
            c = (t * length, bend * t * t)
            angle = math.atan2(2.0 * bend * t / max(1.0, length), 1.0)
            # The links turn a quarter turn each: one seen flat, one edge on.
            ry = 4.8 if k % 2 == 0 else 1.8
            K.oval(d, K.at(*c), 10.0, 10.0, GLOW[:3] + (60,))
            ring(d, c, angle, 8.0, ry, CHAIN_OUT, 3.6)
            ring(d, c, angle, 8.0, ry, CHAIN_CORE, 1.4)

    return K.piece(("chain", length, bend, links), paint)


def _torn_threads(swing: float):
    """The stitches it tore out of the neck: loose ends hanging from the
    seam under its ruff, swung ``swing`` degrees by its motion."""
    swing = _r(swing, 6.0)
    k = SPIRIT_HEAD.k
    roots = [(-8.0, 15.2), (-4.0, 16.4), (0.0, 16.4), (3.6, 15.6), (6.4, 14.4)]
    lengths = [5.0, 7.0, 4.0, 6.5, 3.6]

    def paint(d) -> None:
        for (x, y), n in zip(roots, lengths):
            a = math.radians(90.0 + swing)
            mid = (x + math.cos(a) * n * 0.5 + 0.8, y + math.sin(a) * n * 0.5)
            end = (x + math.cos(a) * n, y + math.sin(a) * n)
            k.line(d, [k.at(x, y), k.at(*mid), k.at(*end)], THREAD, 0.7)

    return k.piece(("torn", swing), paint)


# ---- Poses ---------------------------------------------------------------------
#
# ``at``: the middle of the head from where it rests (frame pixels).
# ``rot``: its turn, clockwise (nose down is positive). ``sq``: its squash.
# ``mouth``, ``eyes``, ``ears``, ``look``, ``brows``: as his own head.
# ``spirit``: 1 drawn as the spirit, 0 as his own head.
# ``flame``: how much fire there is (1 is its float). ``trail``: the way the
# fire streams, in the frame (90 down, 180 back, 270 up).
# ``fade``: the opacity of the whole frame.


def P(**kw) -> Pose:
    pose: Pose = dict(at=(0.0, 0.0), rot=0.0, sq=1.0, mouth="grit", eyes="pin", ears=-10.0, look=(0.0, 0.0), brows=-1.0, spirit=1.0,
                      flame=1.0, trail=120.0, fade=1.0)
    pose.update(kw)
    return pose


FLOAT = P()
#: Its jaws open on the float.
FLOAT_OPEN = P(at=(0.0, -3.0), mouth="open", ears=-4.0, look=(0.6, 0.2))
#: Dead on the floor as it fell off the body: his own head, eyes out, tongue
#: out.
OFF = P(at=(0.0, 0.0), rot=6.0, mouth="loll", eyes="dead", ears=-36.0, brows=1.0, spirit=0.0, flame=0.0, trail=270.0)
#: The fire catches: it shakes.
CATCH = P(rot=-4.0, mouth="big", eyes="roll", ears=-20.0, brows=1.0, flame=0.5, trail=100.0)
#: It throws its head back and howls.
HOWL = P(at=(-4.0, 4.0), rot=-40.0, sq=1.04, mouth="gape", eyes="pin", ears=-30.0, brows=1.0, flame=1.5, trail=110.0)
HOWL_DRAW = P(at=(4.0, -2.0), rot=10.0, sq=0.96, mouth="grit", eyes="squint", ears=-24.0, flame=1.1, trail=120.0)
#: Flying: nose a little down, the fire long behind it.
DRIFT = P(rot=8.0, mouth="grit", ears=-26.0, look=(1.0, 0.4), flame=1.3, trail=172.0)
#: Drawn back, jaws wide: the bite is coming.
GAPE = P(at=(-12.0, -4.0), rot=-14.0, sq=1.05, mouth="gape", eyes="pin", ears=-34.0, look=(1.0, 0.0), flame=1.4, trail=150.0)
SNAP = P(at=(10.0, 2.0), rot=6.0, sq=0.95, mouth="grit", eyes="pin", ears=-36.0, look=(1.0, 0.0), flame=1.6, trail=180.0)
BITE_OPEN = dict(SNAP, mouth="big", sq=1.0)
#: Past you: it tumbles on and shakes itself.
TUMBLE = P(at=(6.0, 4.0), rot=40.0, mouth="open", eyes="wince", ears=-8.0, brows=1.0, flame=0.8, trail=200.0)
DAZED = P(rot=-6.0, mouth="open", eyes="wince", ears=-14.0, brows=1.0, flame=0.8, trail=110.0)
#: High up, nose down at you.
AIM_DOWN = P(at=(0.0, -6.0), rot=70.0, mouth="gape", ears=-34.0, look=(0.6, 0.6), flame=1.4, trail=260.0)
DIVE = P(at=(0.0, 4.0), rot=86.0, sq=1.06, mouth="gape", ears=-40.0, look=(0.8, 0.6), flame=1.7, trail=270.0)
#: Its teeth in the floor: it wrenches at them.
STUCK = P(at=(0.0, 10.0), rot=82.0, sq=0.94, mouth="grit", eyes="squint", ears=0.0, brows=1.0, flame=0.6, trail=250.0)
FREED = P(at=(0.0, -2.0), rot=-10.0, mouth="big", eyes="pin", ears=-20.0, flame=1.2, trail=120.0)
#: The fire in it calls its fire out round it.
KINDLE = P(at=(-2.0, -2.0), rot=-8.0, mouth="open", eyes="pin", ears=-16.0, flame=1.3, trail=110.0)
FLING = P(at=(6.0, 0.0), rot=10.0, mouth="grit", eyes="pin", ears=-34.0, flame=1.5, trail=170.0)
#: Its fire is spent: on the floor, chin down, dim.
#: Spent, not dead (Jon, 2026-10-21: "It looks like he is dead, but he is
#: not"): heavy lids over eyes that still watch you, not the X of "closed",
#: which is the dead head's.
SPENT = P(at=(0.0, 10.0), rot=16.0, sq=0.95, mouth="loll", eyes="heavy", ears=-36.0, brows=1.0, flame=0.15, trail=270.0, fade=0.75)
#: THE HUNT: low and long, ears flat, jaws open, the fire long behind it.
HUNT = P(at=(4.0, 6.0), rot=12.0, sq=0.97, mouth="open", eyes="pin", ears=-42.0, look=(1.0, 0.2), flame=1.6, trail=178.0)
#: Its crash out of the arena: jaws first at the wall, everything flat back.
CRASH = P(at=(12.0, 0.0), rot=4.0, sq=0.92, mouth="big", eyes="pin", ears=-46.0, brows=1.0, look=(1.0, 0.0), flame=1.9, trail=180.0)
#: THE LEASH: it rears and strains at its neck, the stitches burning.
STRAIN = P(at=(-8.0, -4.0), rot=-22.0, sq=1.03, mouth="grit", eyes="pin", ears=-20.0, brows=1.0, look=(1.0, -0.2), flame=1.4, trail=100.0)
#: It throws its head round and the chain with it.
WHIP_BACK = P(at=(-10.0, -2.0), rot=-30.0, sq=1.04, mouth="gape", eyes="pin", ears=-28.0, look=(-0.4, 0.2), flame=1.5, trail=110.0)
WHIP_THROUGH = P(at=(12.0, 4.0), rot=28.0, sq=0.95, mouth="big", eyes="pin", ears=-40.0, look=(1.0, 0.4), flame=1.7, trail=190.0)
#: The chain fallen slack, it pants: chin low, tongue out.
SLACK = P(at=(0.0, 8.0), rot=10.0, sq=0.97, mouth="loll", eyes="heavy", ears=-10.0, brows=1.0, look=(0.6, 0.4), flame=0.7, trail=230.0)
#: THE STORM: head back to the vault, jaws open, eyes rolled up; his
#: lightning crawls over it.
STORM_UP = P(at=(-4.0, -2.0), rot=-34.0, sq=1.04, mouth="big", eyes="roll", ears=-26.0, brows=1.0, look=(0.4, -1.0), flame=1.3, trail=110.0)
#: Held by her talismans: it strains against them, its fire beaten low.
BOUND = P(at=(-2.0, 2.0), rot=-8.0, sq=0.97, mouth="grit", eyes="wince", ears=-40.0, brows=1.0, look=(0.0, 0.0), flame=0.8, trail=150.0)
#: Struck.
STRUCK = P(at=(-6.0, -2.0), rot=-14.0, mouth="big", eyes="wince", ears=-20.0, brows=1.0, flame=1.2, trail=140.0)


def _flicker(i: int, k: int = 0) -> float:
    """A frame's flicker of the fire, -1 to 1."""
    return math.sin(i * 2.3 + k * 1.7) * 0.6 + math.sin(i * 5.1 + k * 0.9) * 0.4


def _jitter(i: int, amp: float, seed: float = 0.0) -> float:
    return amp * math.sin(i * 7.3 + seed * 3.1)


#: The rows the fight draws while its ward is lit: each is its plain row
#: with the hitodama round it.
#: It turns round (Jon, 2026-10-25: it flipped): its head whips over, its
#: ears flat, and the fire streaming from its neck swings from the way it
#: was going, up over it, to behind it. The fight draws the row facing the
#: new way.
TURN_FROM = P(at=(-6.0, 0.0), rot=-4.0, sq=0.97, mouth="grit", eyes="squint", ears=-34.0, flame=1.3, trail=350.0)
TURN_OVER = P(at=(-3.0, -3.0), rot=-12.0, sq=1.03, mouth="grit", eyes="pin", ears=-30.0, flame=1.4, trail=265.0)


def _pose(anim: str, i: int, n: int) -> Pose:
    u = R.shot(i, n)
    _ph, s, c = R.loop(i, n)
    if anim in RING_ROWS:
        # The ward's own rows draw only its spirits, about the head at rest.
        return FLOAT
    if anim == "turn":
        return keys(u, [(0.0, TURN_FROM), (0.45, TURN_OVER, "out"), (1.0, FLOAT, "io")])
    if anim == "storm_tell":
        pose = keys(u, [(0.0, FLOAT), (0.4, HOWL_DRAW, "out"), (0.6, STORM_UP, "snap"), (1.0, STORM_UP, "hold")])
        return dict(pose, rot=float(pose["rot"]) + (_jitter(i, 2.5) if u > 0.6 else 0.0))  # type: ignore[arg-type]
    if anim == "ward_kindle":
        # It howls as the blue fire catches round it.
        pose = keys(u, [(0.0, FLOAT), (0.2, HOWL_DRAW, "out"), (0.35, HOWL, "snap"), (0.85, HOWL, "hold"), (1.0, dict(HOWL, rot=-30.0))])
        return dict(pose, rot=float(pose["rot"]) + (_jitter(i, 2.0) if 0.35 <= u < 0.85 else 0.0))  # type: ignore[arg-type]
    if anim == "ward_bound":
        # It strains against the talismans: a shake, side to side.
        return dict(BOUND, rot=-8.0 + 6.0 * s, at=(2.0 * c, 2.0 + 1.5 * abs(s)), mouth="grit" if i % 4 < 2 else "big")
    if anim == "dispel":
        # The ward breaks: it is thrown back, then shakes itself and faces you.
        pose = keys(u, [(0.0, BOUND), (0.15, dict(STRUCK, rot=-24.0, at=(-10.0, -4.0)), "snap"), (0.45, STRUCK, "back"), (0.7, DAZED, "io"),
                        (1.0, FLOAT, "out")])
        return dict(pose, rot=float(pose["rot"]) + (8.0 * math.sin(i * 2.6) if 0.5 <= u < 0.8 else 0.0))  # type: ignore[arg-type]
    if anim == "idle":
        pose = keys(R.cycle(i, n), [(0.0, FLOAT), (0.5, FLOAT_OPEN), (1.0, FLOAT)])
        return dict(pose, at=(pose["at"][0], pose["at"][1] + 3.0 * s), rot=2.0 * c, ears=float(pose["ears"]) + 4.0 * c)  # type: ignore[index]
    if anim == "drift":
        return dict(DRIFT, at=(0.0, 2.0 * s), rot=8.0 + 3.0 * c, mouth="grit" if i % 4 < 2 else "flat")
    if anim == "rise":
        # His head comes off his body, and the fire catches in it. Then it
        # throws its head back and howls.
        pose = keys(u, [(0.0, OFF), (0.2, dict(OFF, rot=0.0, mouth="open")), (0.28, CATCH, "snap"), (0.5, CATCH), (0.62, FLOAT, "out"),
                        (0.72, HOWL_DRAW, "io"), (0.82, HOWL, "snap"), (1.0, HOWL, "hold")])
        if u < 0.25:
            pose = dict(pose, spirit=0.0, rot=float(pose["rot"]) + _jitter(i, 4.0), flame=0.4 * u / 0.25, trail=270.0)  # type: ignore[arg-type]
        elif u < 0.5:
            pose = dict(pose, rot=float(pose["rot"]) + _jitter(i, 6.0), at=(_jitter(i, 2.0, 1.0), 0.0))  # type: ignore[arg-type]
        return pose
    if anim == "bite_tell":
        pose = keys(u, [(0.0, FLOAT), (0.6, GAPE, "out"), (1.0, GAPE, "hold")])
        return dict(pose, rot=float(pose["rot"]) + (_jitter(i, 1.5) if u > 0.6 else 0.0))  # type: ignore[arg-type]
    if anim == "bite":
        # Two snaps as it goes.
        return keys(u, [(0.0, GAPE), (0.25, SNAP, "snap"), (0.5, BITE_OPEN, "out"), (0.75, SNAP, "snap"), (1.0, SNAP, "hold")])
    if anim == "bite_miss":
        pose = keys(u, [(0.0, SNAP), (0.3, TUMBLE, "out"), (0.55, DAZED, "back"), (1.0, FLOAT)])
        if 0.55 <= u < 0.85:
            # It shakes its head clear.
            pose = dict(pose, rot=float(pose["rot"]) + 10.0 * math.sin(i * 2.6))  # type: ignore[arg-type]
        return pose
    if anim == "dive_tell":
        pose = keys(u, [(0.0, FLOAT), (0.5, AIM_DOWN, "out"), (1.0, AIM_DOWN, "hold")])
        return dict(pose, at=(pose["at"][0] + (_jitter(i, 1.2) if u > 0.5 else 0.0), pose["at"][1]))  # type: ignore[index]
    if anim == "dive":
        return dict(DIVE, rot=86.0 + _jitter(i, 2.0))
    if anim == "buried":
        # It wrenches at its teeth, from side to side.
        return dict(STUCK, rot=82.0 + 9.0 * s, at=(3.0 * s, 10.0 + 1.5 * abs(c)), ears=-30.0 + 30.0 * abs(s), flame=0.6 + 0.2 * _flicker(i))
    if anim == "pull_free":
        return keys(u, [(0.0, STUCK), (0.3, dict(STUCK, rot=60.0, mouth="open"), "snap"), (1.0, FREED, "out")])
    if anim == "hunt":
        # At a run: its head pumps, its jaws work.
        pose = dict(HUNT, at=(HUNT["at"][0] + 2.0 * c, HUNT["at"][1] + 4.0 * s), rot=12.0 + 5.0 * c)  # type: ignore[index]
        return dict(pose, mouth="open" if i % 4 < 2 else "big", ears=-42.0 + 4.0 * abs(s))
    if anim == "crash":
        return dict(CRASH, rot=4.0 + _jitter(i, 2.0), at=(12.0 + _jitter(i, 1.5, 1.0), 0.0))
    if anim == "leash_tell":
        # It rears and strains: the stitches burn, the chain unrolls.
        pose = keys(u, [(0.0, FLOAT), (0.4, STRAIN, "out"), (0.8, dict(STRAIN, rot=-26.0)), (1.0, WHIP_BACK, "in")])
        return dict(pose, rot=float(pose["rot"]) + (_jitter(i, 2.0) if 0.4 <= u < 0.8 else 0.0))  # type: ignore[arg-type]
    if anim == "leash_whip":
        # It throws the chain round: back, through, and it hangs on.
        return keys(u, [(0.0, WHIP_BACK), (0.45, WHIP_THROUGH, "snap"), (0.8, dict(WHIP_THROUGH, rot=22.0, mouth="grit"), "out"),
                        (1.0, dict(SLACK, at=(4.0, 4.0)), "io")])
    if anim == "leash_slack":
        # It pants, the chain hanging: its sides heave, its tongue lolls.
        return dict(SLACK, mouth="loll" if i % 4 < 2 else "open", sq=0.97 + 0.03 * s, at=(0.0, 8.0 + 2.0 * s), flame=0.7 + 0.1 * _flicker(i))
    if anim == "howl_tell":
        return keys(u, [(0.0, FLOAT), (1.0, HOWL_DRAW, "in")])
    if anim == "howl":
        pose = keys(u, [(0.0, HOWL_DRAW), (0.2, HOWL, "snap"), (0.85, HOWL, "hold"), (1.0, dict(HOWL, rot=-30.0, mouth="big"))])
        return dict(pose, rot=float(pose["rot"]) + (_jitter(i, 2.0) if 0.2 <= u < 0.85 else 0.0))  # type: ignore[arg-type]
    if anim == "gutter":
        # The fire goes out of it and it drops (the fight carries it down).
        pose = keys(u, [(0.0, FLOAT), (0.35, dict(FLOAT, mouth="open", eyes="wince", flame=0.6, rot=-6.0), "out"),
                        (0.75, dict(SPENT, at=(0.0, 4.0)), "in"), (0.85, dict(SPENT, at=(0.0, 13.0), sq=0.9), "snap"), (1.0, SPENT)])
        return pose
    if anim == "guttered":
        # Out, on the floor: a flicker of fire, its sides going.
        return dict(SPENT, mouth="loll" if i % 4 < 2 else "open", sq=0.95 + 0.02 * s, flame=0.15 + 0.1 * max(0.0, _flicker(i)))
    if anim == "rekindle":
        return keys(u, [(0.0, SPENT), (0.2, dict(CATCH, at=(0.0, 8.0), flame=1.6), "snap"), (1.0, FLOAT, "out")])
    if anim == "hit":
        return keys(u, [(0.0, FLOAT), (0.25, STRUCK, "snap"), (0.6, STRUCK, "hold"), (1.0, FLOAT, "out")])
    if anim == "death":
        # The fire goes out of it: it shakes, howls once, and the spirit
        # leaves. His own head drops to the floor.
        pose = keys(u, [(0.0, STRUCK), (0.15, dict(CATCH, flame=1.2)), (0.32, dict(HOWL, flame=0.8), "snap"), (0.42, dict(HOWL, flame=0.4), "hold"),
                        (0.44, dict(OFF, rot=-20.0, mouth="gape", at=(0.0, -4.0))), (0.6, dict(OFF, rot=30.0, at=(0.0, 6.0)), "in"),
                        (0.66, dict(OFF, rot=-4.0, at=(0.0, 10.0)), "snap"), (0.72, dict(OFF, rot=4.0, at=(0.0, 8.0)), "back"), (1.0, dict(OFF, at=(0.0, 10.0)))])
        if u < 0.42:
            pose = dict(pose, rot=float(pose["rot"]) + _jitter(i, 4.0))  # type: ignore[arg-type]
        return pose
    raise KeyError(anim)


#: Rows: name, frames, milliseconds a frame. The fight draws them by name.
ROWS: List[Tuple[str, int, int]] = [
    # Each row as long as it was, in more frames (Jon, 2026-10-24:
    # "Animations are not smooth enough"): the fight times its moves by them.
    ("idle", 24, 47), ("drift", 12, 53), ("rise", 30, 59), ("hit", 9, 40), ("death", 34, 69),
    ("bite_tell", 12, 47), ("bite", 12, 33), ("bite_miss", 18, 47),
    ("dive_tell", 12, 53), ("dive", 8, 25), ("buried", 16, 52), ("pull_free", 10, 42),
    ("howl_tell", 10, 48), ("howl", 20, 44), ("storm_tell", 14, 57),
    ("hunt", 16, 35), ("crash", 8, 25),
    ("leash_tell", 14, 57), ("leash_whip", 14, 43), ("leash_slack", 14, 71),
    ("gutter", 14, 57), ("guttered", 12, 80), ("rekindle", 9, 40), ("turn", 8, 30),
    # The ward: it kindles, her spell holds it, and it breaks.
    ("ward_kindle", 12, 75), ("ward_bound", 10, 60), ("dispel", 12, 75),
    # The ward's hitodama, a layer over whatever row the head is drawn in, on
    # the ward's own clock (Jon, 2026-10-25: the ring jumped where one warded
    # row handed over to the next): they catch, they circle, and they are
    # blown out. Each is `SPIRIT_TURN_S` a turn from its first frame, so the
    # ring circles on through the hand-over from one to the next.
    ("ward_ring_kindle", 26, 35), ("ward_ring", 32, 35), ("ward_ring_dispel", 26, 35),
    # Nothing: it is still his head on his body (before it tears off).
    ("unseen", 1, 100),
]

# ---- The frame -----------------------------------------------------------------

#: The blue spirits of its ward (Jon, 2026-10-20: "the Japanese ghost
#: spirits around him to be blue"): how many, their ring (frame pixels, a
#: tilted ellipse about the head at rest: the far half of it is behind the
#: head). They turn at `SPIRIT_TURN_S` a turn from the first frame of each
#: ring row, which the fight starts on the ward's clock; `ward_ring` is one
#: whole turn, so it loops without a jump.
SPIRITS = 4
SPIRIT_RING = (104.0, 40.0)
SPIRIT_TILT = -12.0
#: How long the ward's spirits take to go round once, s.
SPIRIT_TURN_S = 1.12
#: The ward's rows: its spirits only, drawn over the head's row.
RING_ROWS = ("ward_ring_kindle", "ward_ring", "ward_ring_dispel")
#: Each row's frames and milliseconds, by name.
ROW_MS = {name: (frames, ms) for name, frames, ms in ROWS}
#: Where the leash goes in its rows: the chain from its neck (frame pixels
#: long; the world's chain is longer, and its tip is the game's sparks), how
#: much of it is drawn, and how far its end bends, by row and ``u``.
CHAIN_LONG = 96.0


def _leash(anim: str, u: float) -> Optional[Tuple[float, float, float]]:
    """The chain of a row at ``u``: (how much of it, its bend, its turn from
    straight down, degrees), or None."""
    if anim == "leash_tell":
        return (min(1.0, max(0.0, (u - 0.3) / 0.6)), -24.0 * u, 30.0 * u)
    if anim == "leash_whip":
        # Its end trails the swing: back, then flung through.
        swing = -1.0 + 2.0 * min(1.0, u / 0.6)
        return (1.0, 40.0 * swing, -40.0 * swing)
    if anim == "leash_slack":
        return (1.0, 4.0, 0.0)
    return None


def _fire(img: Image.Image, pose: Pose, i: int) -> None:
    """The ghost fire that streams out of its neck, behind it."""
    flame = float(pose["flame"])  # type: ignore[arg-type]
    if flame <= 0.02:
        return
    root = _head_point(pose, NECK)
    trail = float(pose["trail"])  # type: ignore[arg-type]
    for k, (spread, size) in enumerate(((-24.0, 0.7), (22.0, 0.65), (-10.0, 0.9), (10.0, 0.85), (0.0, 1.0))):
        f = _flicker(i, k)
        length = (66.0 + 12.0 * f) * size * flame
        width = (34.0 + 4.0 * f) * size * min(1.0, 0.4 + flame * 0.6)
        K.place(img, _tongue_of_fire(length, width, 8.0 * f), root, f"fire_{k}", trail + spread + 6.0 * f)


def _licks(img: Image.Image, pose: Pose, i: int) -> None:
    """Small flames that lick up round its ruff, in front."""
    flame = float(pose["flame"])  # type: ignore[arg-type]
    if flame <= 0.3:
        return
    for k, p in enumerate(((-12.0, 10.0), (4.0, 15.0))):
        f = _flicker(i, k + 5)
        K.place(img, _tongue_of_fire((16.0 + 4.0 * f) * flame, 9.0, 4.0 * f), _head_point(pose, p), f"lick_{k}",
                float(pose["trail"]) + 30.0 * (1 if k else -1) + 8.0 * f)  # type: ignore[arg-type]


def _spirits(img: Image.Image, anim: str, i: int, behind: bool) -> None:
    """The blue spirits of its ward circling the head at rest: the half of the
    ring behind the head (``behind``, on tracks named so, which the game draws
    under the head) or in front of it. In ``ward_ring_kindle`` they catch one
    by one, and in ``ward_ring_dispel`` they are blown out of the ring and go
    out."""
    if anim not in RING_ROWS:
        return
    frames, ms = ROW_MS[anim]
    seconds = i * ms / 1000.0
    u = seconds / (frames * ms / 1000.0)
    centre = _head_point(FLOAT, (2.0, -8.0))
    rx, ry = SPIRIT_RING
    turn = math.tau * seconds / SPIRIT_TURN_S
    tilt = math.radians(SPIRIT_TILT)
    for k in range(SPIRITS):
        a = turn + math.tau * k / SPIRITS
        if (math.sin(a) < 0.0) != behind:
            continue
        grow, out = 1.0, 1.0
        if anim == "ward_ring_kindle":
            grow = min(1.0, max(0.0, (u - 0.2 - 0.12 * k) / 0.2))
            if grow <= 0.0:
                continue
        if anim == "ward_ring_dispel":
            # Blown out of the ring, no further than the frame's margin (its
            # hit flash is drawn in an impostor cell of its frame and margin).
            out = 1.0 + 0.3 * u
            grow = max(0.0, 1.0 - u * 1.6)
            if grow <= 0.05:
                continue
        x, y = rx * out * math.cos(a), ry * out * math.sin(a)
        at = (centre[0] + x * math.cos(tilt) - y * math.sin(tilt), centre[1] + x * math.sin(tilt) + y * math.cos(tilt))
        dx, dy = -rx * math.sin(a), ry * math.cos(a)
        heading = math.degrees(math.atan2(dx * math.sin(tilt) + dy * math.cos(tilt), dx * math.cos(tilt) - dy * math.sin(tilt)))
        size = (9.0 + 2.0 * math.sin(a) + 0.8 * _flicker(i, k)) * (0.35 + 0.65 * grow)
        K.place(img, _hitodama(size), at, f"spirit_{k}_behind" if behind else f"spirit_{k}", heading)


def _effects_over(img: Image.Image, anim: str, pose: Pose, i: int, n: int) -> None:
    """What the moves throw: his lightning over it, her talismans on it,
    the howl's rings, the stitches burning, the fire catching."""
    u = R.shot(i, n)
    centre = _head_point(pose, (2.0, -6.0))
    if anim == "storm_tell" and u >= 0.3:
        # His lightning crawls over it: from ear to ear, and down to its
        # stitches.
        for k, (p0, p1) in enumerate((((-12.0, -34.0), (12.0, -32.0)), ((-8.0, -30.0), (-4.0, 14.0)), ((8.0, -30.0), (6.0, 13.0)))):
            if (i + k) % 3 != 2:
                a0 = _head_point(pose, p0)
                K.place(img, _arc(a0, _head_point(pose, p1), i * 7 + k), a0, f"arc_{k}")
    if anim in ("ward_bound", "dispel"):
        # Her talismans, stuck on its brow and its jaw; they burn away as
        # the ward breaks.
        burn = 0.0 if anim == "ward_bound" else min(1.0, u / 0.4)
        if burn < 1.0:
            for k, (p0, a) in enumerate((((-6.0, -30.0), -20.0), ((6.0, -26.0), 12.0), ((14.0, -6.0), 40.0), ((-14.0, -10.0), -50.0))):
                K.place(img, _ofuda(1.0 - burn), _head_point(pose, p0), f"ofuda_{k}", a + float(pose["rot"]))  # type: ignore[arg-type]
    if anim == "dispel" and u < 0.3:
        K.place(img, R.burst(K, 44.0, ONIBI_CORE, ONIBI_OUT, 12), centre, "ward_breaks")
    if anim == "ward_kindle" and 0.2 <= u < 0.4:
        K.place(img, R.burst(K, 36.0, ONIBI_CORE, ONIBI_OUT, 10), centre, "ward_catches")
    if anim == "leash_tell" and 0.3 <= u:
        # The stitches burn as the chain comes out of them.
        for k, p in enumerate(((-8.0, 15.2), (-1.0, 16.4), (6.4, 14.4))):
            if (i + k) % 2 == 0:
                K.place(img, _tongue_of_fire(14.0, 8.0, 2.0 * _flicker(i, k)), _head_point(pose, p), f"stitch_{k}", 260.0 + 10.0 * k)
    if anim == "howl" and 0.2 <= u < 0.85:
        mouth = _head_point(pose, (18.0, 6.0))
        turn = int(float(pose["rot"]))  # type: ignore[arg-type]
        for k in range(1 + i % 3):
            r = 16.0 + 16.0 * k
            K.place(img, R.swoosh(K, r, turn - 40, turn + 40, 3.6, RING, RING_DARK), mouth, f"howl_{k}")
    if anim == "rise" and 0.22 <= u < 0.34:
        K.place(img, R.burst(K, 30.0, FIRE_CORE, FIRE_OUT, 10), _head_point(pose, NECK), "catch")
    if anim == "death" and 0.42 <= u < 0.48:
        K.place(img, R.burst(K, 34.0, FIRE_CORE, FIRE_OUT, 10), centre, "out")
    if anim == "death" and u >= 0.44:
        # The spirit leaves it: a wisp goes up out of the frame.
        t = (u - 0.44) / 0.56
        K.place(img, _wisp(9.0 * (1.0 - 0.6 * t), i), (centre[0] - 6.0 * math.sin(t * 9.0), centre[1] - 30.0 - 150.0 * t), "leaving")
    if anim == "rekindle" and u < 0.4:
        K.place(img, R.burst(K, 26.0, FIRE_CORE, FIRE_OUT, 10), _head_point(pose, NECK), "kindle")


def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    if anim == "unseen":
        return K.downsample(K.new_frame())
    if anim in RING_ROWS:
        img = K.new_frame()
        _spirits(img, anim, frame_idx, behind=True)
        _spirits(img, anim, frame_idx, behind=False)
        return K.downsample(rigdoc.faded_canvas(img, SPIRIT_OPACITY))
    pose = _pose(anim, frame_idx, nframes)
    spirit = float(pose["spirit"]) >= 0.5  # type: ignore[arg-type]
    head = SPIRIT_HEAD if spirit else LIVING_HEAD
    img = K.new_frame()
    centre = _head_point(pose, (2.0, -10.0))
    if spirit:
        K.place(img, _glow(64.0 + 6.0 * float(pose["flame"])), centre, "glow")  # type: ignore[arg-type]
    _fire(img, pose, frame_idx)
    leash = _leash(anim, R.shot(frame_idx, nframes))
    if leash is not None:
        links, bend, turn_from_down = leash
        if links > 0.0:
            K.place(img, _chain(CHAIN_LONG, bend, links), _head_point(pose, NECK), "leash", 90.0 + turn_from_down)
    turn, sq = float(pose["rot"]), float(pose["sq"])  # type: ignore[arg-type]
    at = _head_point(pose, (0.0, 0.0))
    for part, name in head.layers(pose):
        K.place(img, part, at, name, turn, sq)
    if spirit:
        K.place(img, _torn_threads(-float(pose["trail"]) + 180.0 - turn), at, "torn", turn, sq)  # type: ignore[arg-type]
        _licks(img, pose, frame_idx)
    _effects_over(img, anim, pose, frame_idx, nframes)
    fade = float(pose["fade"]) * (SPIRIT_OPACITY if spirit else 1.0)  # type: ignore[arg-type]
    if fade < 0.999:
        img = rigdoc.faded_canvas(img, max(0.0, fade))
    return K.downsample(img)


# ---- Publishing ----------------------------------------------------------------


def _body_box() -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = BODY_HEAD_PX
    return (REST_AT[0] + x0 * ZOOM, REST_AT[1] + y0 * ZOOM, REST_AT[0] + x1 * ZOOM, REST_AT[1] + y1 * ZOOM)


def _socket(p: Point) -> dict:
    x, y = _head_point(FLOAT, p)
    s = OUT[0] / FRAME_SIZE[0]
    return {"source": f"{TARGET_NAME}.geometry", "point": {"x": round(x * s, 1), "y": round(y * s, 1)}}


TRAITS = ["boss", "monster", "wolf", "spirit", "flying", "evil"]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_wolfenstein_inugami", "display_name": DISPLAY_NAME},
    "body": {"body_plan": "Floating", "body_kind": "Standard", "mass_class": "Light", "traits": TRAITS, "locomotion_hint": "Fly"},
    "capabilities": {
        "traversal": {"walk": None, "jump": None, "climb": None, "fly": True, "swim": None},
        "interactions": {"talk": None, "trade": None, "carry": None},
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "aggressive"},
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": TRAITS,
    "sockets": {"mouth": _socket((18.0, 6.0)), "neck": _socket(NECK), "nose": _socket(NOSE_TIP)},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.fly": {"animation": "drift", "events": []},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
    "authoring_description": (
        "The Inugami: Wolfenstein's wolf head, torn off his dead body and risen as a dog spirit. "
        "His own head (the Insanity Wolf eyes, the snarl, the brain in a jar) in the red glow of a "
        "ghost, the torn stitches hanging from its ruff, ghost fire streaming from its neck."
    ),
    "gameplay_description": (
        "A floating boss that hunts: it stalks you at your height, lunges, pounces with a shock "
        "both ways along the floor, calls lightning down on marks on the floor, howls a ring "
        "that pushes, and cracks its broken leash along the floor. Its fire gutters out once in "
        "a long cycle. In the chase a ward of blue hitodama makes it unhurtable, until Kagero's "
        "spell breaks it."
    ),
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return K.render(TARGET_NAME, ROWS, render_frame, out_dir, ACTOR_METADATA, _body_box())


def main(argv: Optional[list] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=f"Render the {DISPLAY_NAME} spritesheet.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

if __name__ == "__main__":
    raise SystemExit(main())
