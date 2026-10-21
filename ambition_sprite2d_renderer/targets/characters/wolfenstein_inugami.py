"""Sprite generator for the Inugami: Wolfenstein's head, risen as a spirit.

Jon (2026-10-20): "an additional phase to Wolfenstein where the head
resurrects as an inugami and you fight the floating spectral head as an
additional boss".

The story: the regime sewed a wolf's head onto a soldier's body and gave it
orders. When the body dies, the wolf is free at last: the stitches round the
neck pop, the head tears itself off the body, and the ghost fire of an
inugami (the dog spirit of the old stories, made from a dog's severed head)
catches in it. It floats, it bites, it howls, and it throws ghost fire.

The look. It is HIS head: the same skull, jaw, ears, eyes and brain in a jar
(``wolfenstein.WolfHead``), drawn in the ink of a spirit (``SPIRIT``): a red
spectral glow (Jon, 2026-10-20), rose fur, a maroon outline, eyes that burn
pale gold with black points in them, a mouth lit from inside. The torn stitches hang from under its ruff, and ghost
fire streams from where the neck was. It is a little transparent. When it
dies the fire goes out of it, the spirit leaves as a wisp, and what is left
on the floor is his head again, in its own colours.

It faces right. There is no drop shadow. The glow round it is part of the
spirit, not a shadow on a floor.

Rows: the rise (the head comes off the body; it is his own head until the
fire catches), the float and the drift, and a tell and a strike row for each
move of its fight (``ambition_content_modules::inugami`` draws them by
name).
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
DISPLAY_NAME = "Inugami"

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


def _glow(radius: float):
    """The cold light round the spirit: rings that fade outward."""
    radius = _r(radius, 2.0)

    def paint(d) -> None:
        for k, alpha in enumerate((14, 18, 24, 30)):
            r = radius * (1.0 - 0.14 * k)
            K.oval(d, K.at(0.0, 0.0), r, r * 0.92, GLOW[:3] + (alpha,))

    return K.piece(("glow", radius), paint)


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
SPENT = P(at=(0.0, 10.0), rot=16.0, sq=0.95, mouth="loll", eyes="closed", ears=-36.0, brows=1.0, flame=0.15, trail=270.0, fade=0.75)
#: Struck.
STRUCK = P(at=(-6.0, -2.0), rot=-14.0, mouth="big", eyes="wince", ears=-20.0, brows=1.0, flame=1.2, trail=140.0)


def _flicker(i: int, k: int = 0) -> float:
    """A frame's flicker of the fire, -1 to 1."""
    return math.sin(i * 2.3 + k * 1.7) * 0.6 + math.sin(i * 5.1 + k * 0.9) * 0.4


def _jitter(i: int, amp: float, seed: float = 0.0) -> float:
    return amp * math.sin(i * 7.3 + seed * 3.1)


def _pose(anim: str, i: int, n: int) -> Pose:
    u = R.shot(i, n)
    _ph, s, c = R.loop(i, n)
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
    if anim == "onibi_tell":
        pose = keys(u, [(0.0, FLOAT), (0.4, KINDLE, "out"), (1.0, KINDLE)])
        return dict(pose, at=(pose["at"][0], pose["at"][1] + 1.5 * s))  # type: ignore[index]
    if anim == "onibi":
        return keys(u, [(0.0, KINDLE), (0.25, FLING, "snap"), (0.6, FLING, "hold"), (1.0, FLOAT)])
    if anim == "howl_tell":
        return keys(u, [(0.0, FLOAT), (1.0, HOWL_DRAW, "in")])
    if anim == "howl":
        pose = keys(u, [(0.0, HOWL_DRAW), (0.2, HOWL, "snap"), (0.85, HOWL, "hold"), (1.0, dict(HOWL, rot=-30.0, mouth="big"))])
        return dict(pose, rot=float(pose["rot"]) + (_jitter(i, 2.0) if 0.2 <= u < 0.85 else 0.0))  # type: ignore[arg-type]
    if anim == "vanish":
        pose = keys(u, [(0.0, FLOAT), (0.3, dict(FLOAT, mouth="open", eyes="squint")), (1.0, dict(FLOAT, sq=0.6, flame=1.8, trail=270.0))])
        return dict(pose, fade=max(0.0, 1.0 - u * 1.1))
    if anim == "appear":
        pose = keys(u, [(0.0, dict(FLOAT, sq=0.6, flame=1.8, trail=270.0)), (0.6, dict(GAPE, at=(0.0, 0.0))), (1.0, FLOAT)])
        return dict(pose, fade=min(1.0, u * 1.4))
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
    ("idle", 12, 90), ("drift", 8, 80), ("rise", 22, 80), ("hit", 6, 60), ("death", 26, 90),
    ("bite_tell", 8, 70), ("bite", 8, 50), ("bite_miss", 12, 70),
    ("dive_tell", 8, 80), ("dive", 4, 50), ("buried", 12, 70), ("pull_free", 6, 70),
    ("onibi_tell", 10, 80), ("onibi", 8, 60),
    ("howl_tell", 6, 80), ("howl", 12, 70),
    ("vanish", 8, 60), ("appear", 8, 60),
    ("gutter", 10, 80), ("guttered", 8, 120), ("rekindle", 6, 60),
    # Nothing: it is still his head on his body (before it tears off).
    ("unseen", 1, 100),
]

# ---- The frame -----------------------------------------------------------------

#: The blue spirits that circle it always (Jon, 2026-10-20: "the Japanese
#: ghost spirits around him to be blue"): how many, their ring (frame pixels,
#: a tilted ellipse: the far half of it is behind the head), and how many
#: turns a row's frames make (a looping row comes back to where it began).
SPIRITS = 4
SPIRIT_RING = (104.0, 40.0)
SPIRIT_TILT = -12.0
#: Rows in which the spirits are not circling: before the fire catches, while
#: they swell into its onibi, and once the spirit has left it.
NO_SPIRITS = ("onibi_tell", "onibi", "vanish", "appear")

#: The onibi round it: their places on their ring (degrees) and the ring's
#: size, frame pixels.
ONIBI_ANGLES = (-150.0, -30.0, 90.0)
ONIBI_RING = 74.0


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


def _spirits(img: Image.Image, anim: str, pose: Pose, i: int, n: int, behind: bool) -> None:
    """The blue spirits circling it: the half of the ring behind the head
    (``behind``) or in front of it."""
    if anim in NO_SPIRITS or float(pose["spirit"]) < 0.5 or float(pose["flame"]) < 0.3:  # type: ignore[arg-type]
        return
    centre = _head_point(pose, (2.0, -8.0))
    rx, ry = SPIRIT_RING
    turn = math.tau * i / max(1, n)
    tilt = math.radians(SPIRIT_TILT)
    for k in range(SPIRITS):
        a = turn + math.tau * k / SPIRITS
        if (math.sin(a) < 0.0) != behind:
            continue
        x, y = rx * math.cos(a), ry * math.sin(a)
        at = (centre[0] + x * math.cos(tilt) - y * math.sin(tilt), centre[1] + x * math.sin(tilt) + y * math.cos(tilt))
        # It goes round the ring: its tail points back along it.
        dx, dy = -rx * math.sin(a), ry * math.cos(a)
        heading = math.degrees(math.atan2(dx * math.sin(tilt) + dy * math.cos(tilt), dx * math.cos(tilt) - dy * math.sin(tilt)))
        # Nearer is bigger.
        size = 9.0 + 2.0 * math.sin(a) + 0.8 * _flicker(i, k)
        K.place(img, _hitodama(size), at, f"spirit_{k}", heading)


def _effects_over(img: Image.Image, anim: str, pose: Pose, i: int, n: int) -> None:
    """What the moves throw: the onibi, the howl's rings, the fire catching."""
    u = R.shot(i, n)
    centre = _head_point(pose, (2.0, -6.0))
    if anim == "onibi_tell" or (anim == "onibi" and u < 0.25):
        grow = min(1.0, u / 0.6) if anim == "onibi_tell" else 1.0
        for k, a in enumerate(ONIBI_ANGLES):
            a = math.radians(a + 40.0 * u)
            at = (centre[0] + math.cos(a) * ONIBI_RING, centre[1] + math.sin(a) * ONIBI_RING * 0.8)
            K.place(img, _wisp((5.0 + 6.0 * grow) * (1.0 + 0.1 * _flicker(i, k)), i + k), at, f"onibi_{k}")
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
    pose = _pose(anim, frame_idx, nframes)
    spirit = float(pose["spirit"]) >= 0.5  # type: ignore[arg-type]
    head = SPIRIT_HEAD if spirit else LIVING_HEAD
    img = K.new_frame()
    centre = _head_point(pose, (2.0, -10.0))
    if spirit:
        K.place(img, _glow(64.0 + 6.0 * float(pose["flame"])), centre, "glow")  # type: ignore[arg-type]
    _fire(img, pose, frame_idx)
    _spirits(img, anim, pose, frame_idx, nframes, behind=True)
    turn, sq = float(pose["rot"]), float(pose["sq"])  # type: ignore[arg-type]
    at = _head_point(pose, (0.0, 0.0))
    for part, name in head.layers(pose):
        K.place(img, part, at, name, turn, sq)
    if spirit:
        K.place(img, _torn_threads(-float(pose["trail"]) + 180.0 - turn), at, "torn", turn, sq)  # type: ignore[arg-type]
        _licks(img, pose, frame_idx)
    _spirits(img, anim, pose, frame_idx, nframes, behind=False)
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
        "A floating boss: a darting bite, a dive that sinks its teeth in the floor, ghost fire it "
        "throws, a howl that pushes, and a vanish. Its fire gutters out at the end of each cycle."
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
