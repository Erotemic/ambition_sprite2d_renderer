"""A person of the cast, as a rig: the bones, the poses and the frame that the
people share. What a person LOOKS like is not here.

A character module makes a ``Person``, gives it its own pieces (a head, a
torso, hands, shoes, what its limbs are dressed in), changes the poses that
are its own (how it stands, how it talks, what it does when it is pleased),
and names its rows. ``erdish.py`` is the first person drawn this way, by hand;
this module is that file with the man taken out.

The rig (as ``_ai_era_kit`` has it): each limb is two bones through a solved
elbow or knee, and each piece is painted once and turned to where it sits. A
person is seen three quarters from the front and faces right.

What is shared is how a body moves. Two people on this rig must still not look
like one person in two coats: each has its own ``Build`` (how long its legs
are, how round its back is, where its head sits), its own head and clothes,
and its own rest pose.

There is no drop shadow, and a person holds nothing (the runtime held-item
system is authoritative).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from PIL import Image

from ._ai_era_kit import OUTLINE, WHITE, Kit, Point, Pose, RGBA, angle, blend, ease, keys, lerp, mix, pin, solve, turned

__all__ = [
    "AIR", "APEX", "Build", "CROUCH", "DASH", "FALL", "FP", "FRONT_REST", "GUARD", "HALF_UP", "HANG", "LANDED", "LIBRARY", "MAIN_ROWS", "P", "PERCH", "Person", "REST",
    "RISE", "SAT", "STRUCK", "SUPINE", "TUCK", "UP", "Seg", "Stamp", "bone", "burst", "chain", "chalk", "dust", "glyph", "loop", "make_brows",
    "brow_mood", "entry_points", "make_eyes", "make_figure", "make_front_shoe", "make_hand", "make_head", "make_mouth", "make_neck", "make_shoe", "make_torso", "ribbon", "shot", "stride", "swoosh", "tick",
]

#: A part of a bone: from and to (as parts of its length), how wide it is at
#: each, and its colour. A sleeve that stops at the elbow is one ``Seg`` of
#: cloth and one of skin.
Seg = Tuple[float, float, float, float, RGBA]
#: A piece, where it goes in the frame, its name, and its turn.
Stamp = Tuple[object, Point, str, float]


@dataclass(frozen=True)
class Build:
    """The lengths of a person, in frame pixels, from the hips; up is
    negative and +x is forward. 168 cm is 108 pixels high."""

    #: How high the hips are, standing.
    hip_up: float = 48.0
    #: ``thigh + shin`` is a little more than ``hip_up - ankle_up``, or the
    #: person can not stand with a foot in front.
    thigh: float = 23.4
    shin: float = 22.4
    #: The base of the neck. An ``x`` over about 2 is a round back.
    neck: Point = (1.0, -36.0)
    upper: float = 19.0
    fore: float = 18.0
    near_shoulder: Point = (-6.0, -32.0)
    far_shoulder: Point = (7.6, -31.6)
    near_hip: Point = (-3.6, 0.0)
    far_hip: Point = (3.6, 0.0)
    #: The sole of a shoe is this far under its ankle.
    ankle_up: float = 3.0
    #: The middle of the head from the base of the neck, the head level.
    head_up: Point = (1.4, -11.6)
    #: Where the neck meets the head, from the middle of the head.
    throat: Point = (-0.2, 4.0)
    #: The top of the head above the ground, standing.
    height: float = 108.0
    #: The body the game moves is this wide behind and in front of the middle.
    half_width: Tuple[float, float] = (13.0, 15.0)

    def __post_init__(self) -> None:
        assert self.thigh + self.shin > self.hip_up - self.ankle_up, "the legs are too short to stand on"


# ---- The pose ----------------------------------------------------------------

#: Standing. A row states what differs. A length is in units: the hips stand
#: 37 units high, whatever the ``Build``.
REST: Pose = {
    # The hips from where they are standing: +x is forward, +y is down.
    "hip": (0.0, 0.0),
    # The trunk leans this far forward, about the hips.
    "lean": 0.0,
    # The head from where it sits on the neck, and its tilt.
    "head": (0.0, 0.0, 0.0),
    # Each hand from its shoulder; which way the elbow bends (1: behind the
    # arm, as it hangs); and what the hand does (soft, flat, fist, point,
    # open).
    "na": (-2.0, 26.0),
    "fa": (2.0, 25.5),
    "nab": 1.0,
    "fab": 1.0,
    # The near arm is painted over the head, or under it (a hand that reaches
    # up past the face comes out from behind it).
    "arm": "over",
    # The near leg is painted under the torso, or over it (a kick).
    "leg": "under",
    "nh": "soft",
    "fh": "soft",
    # The sole of each shoe from the ground under the person, and its toe's
    # turn.
    "nf": (-5.0, 0.0, 0.0),
    "ff": (6.0, 0.0, 0.0),
    # All of the person turned about a point (from the hips), and then moved.
    "rot": 0.0,
    "pivot": (0.0, 0.0),
    "off": (0.0, 0.0),
    # open, up, closed, happy, wince, wide.
    "eyes": "open",
    # smile, flat, o, grit, open, big.
    "mouth": "smile",
    # -1 set, 0 level, 1 raised.
    "brows": 0.0,
    # How far the hem of the torso swings out behind, and in front.
    "hem": (0.0, 0.0),
}


def P(**kw) -> Pose:
    unknown = set(kw) - set(REST)
    assert not unknown, unknown
    return dict(REST, **kw)


def loop(i: int, n: int) -> Tuple[float, float, float]:
    """The phase of frame ``i`` of a row that repeats, its sine and cosine."""
    ph = math.tau * i / max(1, n)
    return ph, math.sin(ph), math.cos(ph)


def shot(i: int, n: int) -> float:
    """How far frame ``i`` is through a row that plays once: 0 to 1."""
    return i / max(1, n - 1)


def stride(ph: float, reach: float, lift: float, mid: float = 0.5) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """The near and far soles of a step cycle."""

    def foot(p: float, x0: float) -> Tuple[float, float, float]:
        s, c = math.sin(p), math.cos(p)
        up = max(0.0, -s)
        # The toe comes up to land and goes down to push off.
        return (x0 + reach * c, -lift * up, -14.0 * max(0.0, c) * (1.0 if s < 0.0 else 0.35) + 22.0 * up * max(0.0, -c))

    return foot(ph, mid - 1.0), foot(ph + math.pi, mid + 1.0)


LIBRARY: Dict[str, Callable[[int, int], Pose]] = {}


def _row(fn: Callable[[int, int], Pose]) -> Callable[[int, int], Pose]:
    LIBRARY[fn.__name__] = fn
    return fn


@_row
def idle(i: int, n: int) -> Pose:
    _, s, _c = loop(i, n)
    return P(hip=(0.0, 0.4 + 0.4 * s), head=(0.2, -0.3 * s, 1.0 * s), eyes="closed" if i == n - 2 else "open")


@_row
def walk(i: int, n: int) -> Pose:
    ph, s, c = loop(i, n)
    nf, ff = stride(ph, 8.5, 5.0)
    return P(hip=(0.5, 0.9 * math.cos(2.0 * ph)), lean=3.0, head=(0.0, 0.0, 1.5 * s), na=(-2.0 - 7.5 * c, 25.0 - 1.5 * abs(c)),
             fa=(2.5 + 7.5 * c, 24.5 - 1.5 * abs(c)), nf=nf, ff=ff, hem=(1.0 + 1.5 * abs(c), 0.5 + 1.5 * abs(c)))


@_row
def run(i: int, n: int) -> Pose:
    ph, s, c = loop(i, n)
    nf, ff = stride(ph, 12.5, 9.5, 0.0)
    return P(hip=(2.0, 1.5 + 1.7 * math.cos(2.0 * ph)), lean=15.0, head=(0.5, 0.0, -7.0), na=(-1.0 - 11.0 * c, 16.0 + 2.0 * c),
             fa=(3.0 + 11.0 * c, 16.0 - 2.0 * c), nh="fist", fh="fist", nf=nf, ff=ff, mouth="open", brows=-1.0, hem=(5.0, 1.0))


CROUCH = P(hip=(-1.5, 15.5), lean=18.0, head=(1.0, 0.0, -10.0), na=(5.0, 15.0), fa=(8.0, 14.5), nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0),
           hem=(2.0, 3.0))


@_row
def crouch(i: int, n: int) -> Pose:
    _, s, _c = loop(i, n)
    return dict(CROUCH, hip=(-1.5, 15.5 + 0.5 * s), eyes="closed" if i == n - 2 else "open")


@_row
def crouch_walk(i: int, n: int) -> Pose:
    ph, _s, c = loop(i, n)
    nf, ff = stride(ph, 6.0, 2.8)
    return dict(CROUCH, hip=(-1.0, 15.0 + 0.7 * math.cos(2.0 * ph)), nf=nf, ff=ff, na=(5.0 - 2.5 * c, 15.0), fa=(8.0 + 2.5 * c, 14.5))


RISE = P(hip=(0.0, -2.0), lean=3.0, head=(0.0, 0.0, -8.0), na=(-12.0, -23.0), nab=-1.0, fa=(16.0, -20.0), nh="open", fh="open",
         nf=(-6.0, -1.0, 34.0), ff=(6.0, -10.0, 12.0), mouth="open", brows=1.0, hem=(1.0, 1.0))
APEX = P(hip=(0.0, -2.0), lean=1.0, head=(0.0, 0.0, -3.0), na=(-19.0, -7.0), nab=-1.0, fa=(21.0, -8.0), nh="open", fh="open",
         nf=(-5.0, -9.0, 22.0), ff=(8.0, -13.0, 4.0), eyes="happy", mouth="open", hem=(3.0, 3.0))
FALL = P(hip=(0.0, -3.0), lean=-5.0, head=(0.0, 0.0, 5.0), na=(-16.0, -20.0), nab=-1.0, fa=(19.0, -18.0), nh="open", fh="open",
         nf=(-8.0, -3.0, 28.0), ff=(7.0, -9.0, 8.0), eyes="wide", mouth="o", brows=1.0, hem=(5.0, 5.0))


@_row
def jump(i: int, n: int) -> Pose:
    wind = P(hip=(-1.0, 10.0), lean=12.0, na=(-13.0, 17.0), fa=(-9.0, 19.0), nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), brows=-1.0)
    return keys(shot(i, n), [(0.0, wind), (0.3, RISE), (0.6, RISE), (1.0, APEX)])


@_row
def fall(i: int, n: int) -> Pose:
    _, s, c = loop(i, n)
    return dict(FALL, na=(-16.0 + 2.0 * s, -20.0 - 2.0 * c), fa=(19.0 - 2.0 * s, -18.0 + 2.0 * c), nf=(-8.0, -3.0 + 1.5 * s, 28.0),
                ff=(7.0, -9.0 - 1.5 * s, 8.0))


LANDED = P(hip=(0.0, 18.0), lean=27.0, head=(2.0, 2.0, 4.0), na=(13.0, 22.0), fa=(17.0, 20.0), nh="open", fh="open", nf=(-8.0, 0.0, 0.0),
           ff=(9.0, 0.0, 0.0), eyes="wince", mouth="grit", hem=(4.0, 3.0))
HALF_UP = P(hip=(0.0, 7.0), lean=10.0, na=(5.0, 22.0), fa=(8.0, 21.0), nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), hem=(1.0, 2.0))


@_row
def land_hard(i: int, n: int) -> Pose:
    return keys(shot(i, n), [(0.0, FALL), (0.16, LANDED), (0.55, dict(LANDED, eyes="closed")), (1.0, HALF_UP)])


@_row
def land_recovery(i: int, n: int) -> Pose:
    return keys(shot(i, n), [(0.0, HALF_UP), (1.0, P())])


DASH = P(hip=(2.0, 6.0), lean=32.0, head=(1.0, 0.0, -22.0), na=(-19.0, 8.0), fa=(-15.0, 11.0), nh="open", fh="open", nf=(-13.0, -6.0, 38.0),
         ff=(9.0, 0.0, 0.0), brows=-1.0, mouth="flat", hem=(7.0, 0.0))


@_row
def dash_startup(i: int, n: int) -> Pose:
    back = P(hip=(-3.0, 4.0), lean=-8.0, na=(9.0, 13.0), fa=(12.0, 13.0), nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, -10.0), brows=-1.0)
    return keys(shot(i, n), [(0.0, back), (1.0, DASH)])


@_row
def dash(i: int, n: int) -> Pose:
    _, s, _c = loop(i, n)
    return dict(DASH, hip=(2.0, 6.0 + 0.8 * s), nf=(-13.0 - s, -6.0 - s, 38.0))


@_row
def slide(i: int, n: int) -> Pose:
    _, s, _c = loop(i, n)
    return P(hip=(-5.0, 23.0), lean=-38.0, head=(1.0, 0.0, 26.0), na=(-9.0, 17.0), fa=(13.0, 3.0), nh="open", fh="fist",
             nf=(17.0, -1.0 - 0.5 * s, -28.0), ff=(22.0, -5.0 + 0.5 * s, -34.0), brows=-1.0, mouth="grit", hem=(0.0, 5.0))


#: A ball, turned about its middle.
TUCK = P(hip=(0.0, 0.0), lean=36.0, head=(-17.0, 23.0, 46.0), na=(9.0, 14.0), fa=(11.0, 12.0), nh="fist", fh="fist", nf=(9.0, -26.0, 10.0),
         ff=(14.0, -29.0, 10.0), eyes="closed", mouth="flat", arm="under", pivot=(15.0, -13.5), off=(-8.0, 14.0), hem=(0.0, 3.0))


@_row
def roll(i: int, n: int) -> Pose:
    return dict(TUCK, rot=360.0 * i / n)


@_row
def wall_grab(i: int, n: int) -> Pose:
    _, s, _c = loop(i, n)
    return P(hip=(3.0, -2.0 + 0.8 * s), lean=-7.0, head=(0.0, 0.0, -5.0), na=(25.0, -8.0), fa=(21.0, -14.0), arm="under", nh="open", fh="open",
             nf=(12.0, -6.0 + 0.8 * s, -55.0), ff=(14.0, -17.0 + 0.8 * s, -55.0), mouth="grit", brows=1.0)


@_row
def wall_jump(i: int, n: int) -> Pose:
    held = wall_grab(0, 6)
    push = P(hip=(-4.0, -3.0), lean=-25.0, head=(0.0, 0.0, 15.0), na=(-18.0, -15.0), nab=-1.0, fa=(-8.0, -21.0), nh="open", fh="open",
             nf=(11.0, 0.0, -24.0), ff=(13.0, -7.0, -34.0), brows=-1.0, mouth="open", hem=(0.0, 5.0))
    away = dict(push, nf=(2.0, -8.0, 10.0), ff=(8.0, -13.0, 0.0), na=(-20.0, -6.0), fa=(-6.0, -16.0))
    return keys(shot(i, n), [(0.0, held), (0.4, push), (1.0, away)])


HANG = P(hip=(-1.0, 0.0), lean=2.0, head=(-1.0, 1.0, -13.0), na=(24.0, -15.0), fa=(18.0, -21.0), arm="under", nh="fist", fh="fist",
         nf=(-3.0, -1.0, 34.0), ff=(4.0, -3.0, 28.0), mouth="flat", brows=1.0)
PERCH = P(hip=(1.0, 16.0), lean=25.0, head=(1.0, 0.0, -14.0), na=(12.0, 21.0), fa=(15.0, 19.0), nh="open", fh="open", nf=(-7.0, 0.0, 0.0),
          ff=(9.0, 0.0, 0.0), hem=(3.0, 3.0))


@_row
def ledge_grab(i: int, n: int) -> Pose:
    _, s, _c = loop(i, n)
    return dict(HANG, lean=2.0 + 2.5 * s, nf=(-3.0 - 2.0 * s, -1.0, 34.0), ff=(4.0 - 2.0 * s, -3.0, 28.0))


@_row
def ledge_climb(i: int, n: int) -> Pose:
    pull = P(hip=(1.0, -3.0), lean=13.0, head=(1.0, 0.0, -11.0), na=(15.0, 4.0), fa=(17.0, 1.0), nh="fist", fh="fist", nf=(-4.0, -3.0, 30.0),
             ff=(10.0, -17.0, -8.0), mouth="grit", brows=-1.0, hem=(1.0, 3.0))
    return keys(shot(i, n), [(0.0, HANG), (0.5, pull), (1.0, PERCH)])


@_row
def ledge_getup(i: int, n: int) -> Pose:
    return keys(shot(i, n), [(0.0, PERCH), (0.6, HALF_UP), (1.0, P())])


@_row
def ledge_roll(i: int, n: int) -> Pose:
    u = shot(i, n)
    if u < 0.2:
        return keys(u, [(0.0, PERCH), (0.2, TUCK)])
    return dict(TUCK, rot=360.0 * ease((u - 0.2) / 0.8))


SWEEP_LOW = P(hip=(4.0, 9.0), lean=22.0, head=(1.0, 0.0, -14.0), na=(25.0, 9.0), fa=(-10.0, 13.0), nh="flat", fh="fist", nf=(-9.0, 0.0, 10.0),
              ff=(11.0, 0.0, 0.0), brows=-1.0, mouth="open", hem=(5.0, 2.0))


@_row
def ledge_getup_attack(i: int, n: int) -> Pose:
    wind = dict(HALF_UP, na=(-17.0, 4.0), nh="flat", brows=-1.0)
    return keys(shot(i, n), [(0.0, PERCH), (0.3, wind), (0.55, SWEEP_LOW), (0.75, SWEEP_LOW), (1.0, HALF_UP)])


@_row
def climb(i: int, n: int) -> Pose:
    _ph, s, c = loop(i, n)
    return P(hip=(1.0, -1.0 + abs(s)), lean=4.0, head=(0.0, 0.0, -11.0), na=(25.0, -3.0 - 8.0 * c), fa=(21.0, -5.0 + 8.0 * c), arm="under",
             nh="fist", fh="fist", nf=(5.0, -6.0 + 6.0 * c, -14.0), ff=(7.0, -6.0 - 6.0 * c, -14.0), mouth="flat")


@_row
def swim(i: int, n: int) -> Pose:
    ph, s, _c = loop(i, n)

    def stroke(p: float) -> Tuple[float, float]:
        a = math.radians(60.0 - 85.0 * math.cos(p))
        return (26.0 * math.sin(a), -26.0 * math.cos(a))

    return P(rot=62.0, off=(-4.0, -14.0 + 1.5 * s), lean=3.0, head=(0.0, 0.0, -43.0), na=stroke(ph), fa=stroke(ph + math.pi), arm="under", nh="flat",
             fh="flat", nf=(-4.0 + 5.0 * s, -1.0, 62.0), ff=(5.0 - 5.0 * s, -1.0, 62.0), mouth="o", hem=(2.0, 2.0))


@_row
def float_glide(i: int, n: int) -> Pose:
    _, s, c = loop(i, n)
    return P(hip=(0.0, -2.0 + 1.2 * s), lean=20.0, head=(0.0, 0.0, -16.0), na=(-22.0, 1.0 + s), nab=-1.0, fa=(21.0, -3.0 - s), nh="open", fh="open",
             nf=(-11.0, -4.0 + c, 44.0), ff=(-3.0, -2.0 - c, 38.0), hem=(8.0, 3.0))


@_row
def block(i: int, n: int) -> Pose:
    _, s, _c = loop(i, n)
    return P(hip=(-2.0, 4.0 + 0.4 * s), lean=-6.0, head=(-1.0, 0.0, 4.0), na=(21.0, 3.0), fa=(18.0, -3.0), nh="open", fh="open",
             nf=(-7.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), brows=-1.0, mouth="flat")


STRUCK = P(hip=(-4.0, 2.0), lean=-22.0, head=(-2.0, 0.0, -12.0), na=(16.0, 2.0), fa=(19.0, -4.0), nh="open", fh="open", nf=(-8.0, 0.0, 0.0),
           ff=(8.0, -5.0, -22.0), eyes="wince", mouth="big", brows=1.0, off=(-3.0, 0.0), hem=(0.0, 5.0))


@_row
def hit(i: int, n: int) -> Pose:
    back = P(hip=(-2.0, 2.0), lean=-6.0, na=(4.0, 22.0), fa=(7.0, 21.0), eyes="wince", mouth="grit")
    return keys(shot(i, n), [(0.0, P(lean=-4.0, eyes="wide", mouth="o")), (0.25, STRUCK), (0.6, STRUCK), (1.0, back)])


#: Sitting on the ground, the legs out in front.
SAT = P(hip=(-8.0, 26.5), lean=-10.0, head=(0.0, 0.0, 4.0), na=(-8.0, 24.0), fa=(9.0, 23.0), nh="open", fh="open", nf=(19.0, 0.0, -62.0),
        ff=(25.0, 0.0, -66.0), eyes="closed", mouth="o", hem=(0.0, 2.0))
#: On the back, the head behind and the toes up.
SUPINE = P(rot=-90.0, hip=(-2.0, 25.5), off=(13.0, 0.0), head=(0.0, 0.0, 0.0), na=(5.0, 13.0), fa=(2.0, 11.0), nh="flat", fh="flat",
           nf=(-4.5, 25.0, 0.0), ff=(4.5, 25.0, -10.0), eyes="closed", mouth="flat")


@_row
def death(i: int, n: int) -> Pose:
    sag = P(hip=(-5.0, 13.0), lean=-16.0, head=(-2.0, 0.0, -8.0), na=(7.0, 19.0), fa=(12.0, 15.0), nh="open", fh="open", nf=(-4.0, 0.0, 0.0),
            ff=(10.0, 0.0, -10.0), eyes="wince", mouth="o", off=(-3.0, 0.0), hem=(0.0, 3.0))
    return keys(shot(i, n), [(0.0, STRUCK), (0.25, sag), (0.5, SAT), (0.75, SUPINE), (1.0, SUPINE)])


@_row
def talk(i: int, n: int) -> Pose:
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.4 * s), head=(0.5, 0.0, 2.5 * s), na=(14.0 + 3.0 * c, 8.0 - 5.0 * max(0.0, s)), nh="open", fa=(3.0, 25.0), mouth=("open", "smile", "big", "smile")[i % 4],
             brows=1.0 if s > 0.3 else 0.0)


@_row
def interact(i: int, n: int) -> Pose:
    reach = P(hip=(1.5, 1.0), lean=8.0, head=(1.0, 0.0, 1.0), na=(26.0, -1.0), nh="point", mouth="o", brows=1.0)
    return keys(shot(i, n), [(0.0, P()), (0.35, reach), (0.7, dict(reach, na=(26.0, 3.0))), (1.0, P())])


GUARD = P(hip=(-1.0, 2.0), lean=2.0, na=(9.0, 12.0), fa=(13.0, 11.0), nh="fist", fh="fist", nf=(-7.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), brows=-1.0,
          mouth="flat")


@_row
def jab(i: int, n: int) -> Pose:
    poke = dict(GUARD, hip=(3.0, 3.0), lean=11.0, na=(27.0, 1.0), ff=(10.0, 0.0, 0.0), mouth="open")
    return keys(shot(i, n), [(0.0, GUARD), (0.3, poke), (0.6, poke), (1.0, GUARD)])


@_row
def punch(i: int, n: int) -> Pose:
    wind = dict(GUARD, hip=(-3.0, 3.0), lean=-8.0, na=(-13.0, 8.0))
    push = dict(GUARD, hip=(5.0, 4.0), lean=16.0, na=(27.0, 2.0), fa=(-8.0, 14.0), ff=(12.0, 0.0, 0.0), nf=(-9.0, 0.0, 12.0), mouth="big",
                hem=(5.0, 1.0))
    return keys(shot(i, n), [(0.0, GUARD), (0.25, wind), (0.5, push), (0.75, push), (1.0, GUARD)])


@_row
def slash(i: int, n: int) -> Pose:
    # The near arm comes over from behind the head to the ground in front.
    u = shot(i, n)
    swing = ease(max(0.0, min(1.0, (u - 0.2) / 0.5)))
    a = math.radians(lerp(-138.0, 56.0, swing))
    hand = (27.0 * math.cos(a), 27.0 * math.sin(a))
    base = dict(GUARD, hip=(lerp(-2.0, 4.0, swing), 3.0), lean=lerp(-8.0, 17.0, swing), na=hand, nh="flat",
                nab=-1.0 if hand[1] < -6.0 and hand[0] < 6.0 else 1.0, arm="under" if hand[1] < -4.0 and hand[0] > -14.0 else "over",
                fa=(lerp(13.0, -9.0, swing), 12.0), ff=(lerp(7.0, 11.0, swing), 0.0, 0.0), mouth="open" if 0.2 < u < 0.8 else "flat",
                hem=(4.0 * swing, 1.0))
    if u > 0.85:
        return blend(base, GUARD, ease((u - 0.85) / 0.15))
    return base


@_row
def attack_side(i: int, n: int) -> Pose:
    wind = dict(GUARD, hip=(-4.0, 4.0), lean=-10.0, na=(-12.0, 8.0), fa=(-6.0, 12.0))
    lunge = dict(GUARD, hip=(7.0, 6.0), lean=19.0, na=(27.0, 0.0), fa=(-13.0, 9.0), nf=(-12.0, 0.0, 16.0), ff=(15.0, 0.0, 0.0), eyes="wide",
                 mouth="big", hem=(6.0, 1.0))
    return keys(shot(i, n), [(0.0, GUARD), (0.25, wind), (0.45, lunge), (0.8, lunge), (1.0, GUARD)])


#: One hand as high as it goes.
UP = P(hip=(0.0, -1.0), lean=-5.0, head=(0.0, 0.0, -13.0), na=(4.0, -27.0), nab=-1.0, arm="under", nh="fist", fa=(-8.0, 16.0), fh="fist",
       nf=(-5.0, 0.0, 14.0), ff=(6.0, -1.0, 16.0), mouth="open", brows=-1.0)


@_row
def attack_up(i: int, n: int) -> Pose:
    low = dict(GUARD, hip=(0.0, 9.0), lean=12.0, na=(9.0, 19.0))
    return keys(shot(i, n), [(0.0, GUARD), (0.25, low), (0.45, UP), (0.8, UP), (1.0, GUARD)])


@_row
def attack_down(i: int, n: int) -> Pose:
    high = dict(GUARD, hip=(-1.0, 0.0), lean=-9.0, head=(0.0, 0.0, -8.0), na=(2.0, -26.0), nab=-1.0, arm="under", fa=(8.0, -24.0), fab=-1.0)
    slam = dict(GUARD, hip=(3.0, 11.0), lean=26.0, head=(1.0, 0.0, -8.0), na=(17.0, 21.0), fa=(20.0, 19.0), nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0),
                mouth="big", hem=(4.0, 2.0))
    return keys(shot(i, n), [(0.0, GUARD), (0.3, high), (0.5, slam), (0.85, slam), (1.0, HALF_UP)])


AIR = P(hip=(0.0, -3.0), nf=(-4.0, -8.0, 20.0), ff=(6.0, -12.0, 8.0), na=(9.0, 12.0), fa=(13.0, 11.0), nh="fist", fh="fist", brows=-1.0,
        mouth="flat", hem=(3.0, 2.0))


@_row
def air_neutral(i: int, n: int) -> Pose:
    _, s, _c = loop(i, n)
    return dict(AIR, lean=6.0 * s, na=(-21.0, -5.0 + 2.0 * s), nab=-1.0, fa=(22.0, -7.0 - 2.0 * s), nh="open", fh="open", mouth="open")


@_row
def air_forward(i: int, n: int) -> Pose:
    kick = dict(AIR, lean=-18.0, hip=(-1.0, -3.0), leg="over", nf=(30.0, -36.0, -78.0), ff=(-2.0, -17.0, 34.0), na=(-15.0, 9.0), fa=(10.0, 15.0),
                mouth="open", hem=(1.0, 5.0))
    return keys(shot(i, n), [(0.0, AIR), (0.35, kick), (0.7, kick), (1.0, AIR)])


@_row
def air_back(i: int, n: int) -> Pose:
    kick = dict(AIR, lean=26.0, head=(0.0, 0.0, -22.0), leg="over", nf=(-32.0, -32.0, 96.0), ff=(7.0, -16.0, 0.0), na=(15.0, 12.0), fa=(18.0, 6.0),
                mouth="open", hem=(6.0, 0.0))
    return keys(shot(i, n), [(0.0, AIR), (0.35, kick), (0.7, kick), (1.0, AIR)])


@_row
def air_down(i: int, n: int) -> Pose:
    dive = dict(AIR, hip=(0.0, 0.0), off=(0.0, -13.0), nf=(-1.5, 0.0, 58.0), ff=(3.0, 0.0, 52.0), na=(-14.0, -22.0), nab=-1.0, fa=(17.0, -20.0),
                nh="open", fh="open", mouth="open", hem=(4.0, 4.0))
    return keys(shot(i, n), [(0.0, AIR), (0.3, dive), (0.8, dive), (1.0, AIR)])


@_row
def air_up(i: int, n: int) -> Pose:
    reach = dict(UP, hip=(0.0, -3.0), nf=(-6.0, -2.0, 36.0), ff=(4.0, -8.0, 22.0), hem=(2.0, 2.0))
    return keys(shot(i, n), [(0.0, AIR), (0.3, reach), (0.75, reach), (1.0, AIR)])


CHARGE = P(hip=(0.0, 2.0), lean=4.0, head=(0.0, 0.0, 6.0), na=(10.0, 8.0), fa=(12.0, 6.0), nh="fist", fh="fist", eyes="closed", mouth="flat",
           brows=-1.0)


@_row
def charge(i: int, n: int) -> Pose:
    _, s, _c = loop(i, n)
    return dict(CHARGE, hip=(0.0, 2.0 + 0.6 * s), head=(0.0, 0.3 * s, 6.0 + 1.5 * s))


@_row
def cast(i: int, n: int) -> Pose:
    out = P(hip=(3.0, 3.0), lean=11.0, head=(1.0, 0.0, -5.0), na=(26.0, -2.0), fa=(23.0, 5.0), nh="open", fh="open", nf=(-9.0, 0.0, 10.0),
            ff=(10.0, 0.0, 0.0), eyes="wide", mouth="big", brows=1.0, hem=(6.0, 1.0))
    return keys(shot(i, n), [(0.0, CHARGE), (0.3, out), (1.0, dict(out, hip=(2.0, 3.0), lean=8.0))])


@_row
def celebrate(i: int, n: int) -> Pose:
    ph, s, _c = loop(i, n)
    up = abs(math.sin(ph))
    return P(off=(0.0, -8.0 * up), hip=(0.0, 3.0 * (1.0 - up)), lean=-3.0, head=(0.0, 0.0, -8.0), na=(-13.0, -23.0 + 2.0 * s), nab=-1.0,
             fa=(18.0, -21.0 - 2.0 * s), nh="open", fh="open", nf=(-6.0, -4.0 * up, 24.0 * up), ff=(7.0, -6.0 * up, 14.0 * up), eyes="happy",
             mouth="big", brows=1.0, hem=(3.0 * up, 3.0 * up))


@_row
def taunt(i: int, n: int) -> Pose:
    bow = P(hip=(-1.0, 2.0), lean=20.0, head=(1.0, 1.0, 8.0), na=(8.0, 12.0), fa=(-9.0, 20.0), nh="flat", eyes="closed", hem=(2.0, 0.0))
    return keys(shot(i, n), [(0.0, P()), (0.35, bow), (0.7, bow), (1.0, P(eyes="happy"))])


#: The rows of the main game, in sheet order: name, frames, milliseconds a
#: frame. A character names its own rows; this is the full set to start from.
MAIN_ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 150), ("walk", 8, 100), ("run", 8, 76), ("crouch", 6, 95), ("crouch_walk", 8, 88), ("jump", 6, 95), ("fall", 6, 95),
    ("land_hard", 8, 95), ("land_recovery", 6, 75), ("dash_startup", 4, 50), ("dash", 6, 65), ("slide", 6, 70), ("roll", 8, 58),
    ("wall_grab", 6, 110), ("wall_jump", 6, 85), ("ledge_grab", 6, 100), ("ledge_climb", 6, 100), ("ledge_getup", 6, 40),
    ("ledge_roll", 8, 37), ("ledge_getup_attack", 8, 37), ("climb", 8, 100), ("swim", 8, 105), ("float_glide", 8, 110), ("block", 6, 85),
    ("hit", 5, 90), ("death", 8, 120), ("talk", 8, 104), ("interact", 8, 92), ("jab", 5, 58), ("punch", 7, 72), ("slash", 8, 75),
    ("attack_side", 8, 65), ("attack_up", 8, 65), ("attack_down", 8, 65), ("air_neutral", 8, 60), ("air_forward", 7, 62), ("air_back", 7, 62),
    ("air_down", 7, 70), ("air_up", 7, 62), ("charge", 8, 90), ("cast", 8, 80), ("celebrate", 8, 92), ("taunt", 8, 110),
]


# ---- The person seen from the front -------------------------------------------

#: Standing, facing the viewer. Left and right are the VIEWER's: ``la`` is the
#: hand at the left of the picture.
FRONT_REST: Pose = {
    # The hips from where they stand: +y is down. And how far the trunk leans
    # to the right of the picture.
    "hip": (0.0, 0.0),
    "lean": 0.0,
    # The head from where it sits, and its tilt.
    "head": (0.0, 0.0, 0.0),
    # Each hand from its shoulder (+x is away from the body, for both), and
    # what it does.
    "la": (2.0, 26.0),
    "ra": (2.0, 26.0),
    "lh": "soft",
    "rh": "soft",
    # How much of each arm points at the viewer, 0 to 1: an arm that reaches
    # toward you is drawn short. A hand held out in talk is about 0.6.
    "lz": 0.0,
    "rz": 0.0,
    # Each foot: how far out from under its hip, and how far off the ground.
    "lf": (2.2, 0.0),
    "rf": (2.2, 0.0),
    "off": (0.0, 0.0),
    "eyes": "open",
    "mouth": "smile",
    "brows": 0.0,
}


def FP(**kw) -> Pose:
    unknown = set(kw) - set(FRONT_REST)
    assert not unknown, unknown
    return dict(FRONT_REST, **kw)


def make_front_shoe(K: Kit, colour: RGBA, dark: RGBA, ankle_up: float = 3.0, wide: float = 1.0):
    """``shoe()``: a shoe seen from its toe, from its ankle at ``home``."""

    def shoe():
        h = K.home

        def shape(d) -> None:
            K.oval(d, K.at(0.0, 1.6), 4.4 * wide, 3.4, WHITE)
            K.rrect(d, h[0] - 4.4 * wide, h[1] + 0.6, h[0] + 4.4 * wide, h[1] + ankle_up + 0.4, 1.4, WHITE)

        def detail(d) -> None:
            K.rrect(d, h[0] - 6.0, h[1] + ankle_up - 0.8, h[0] + 6.0, h[1] + ankle_up + 2.0, 0.0, dark)
            K.line(d, [K.at(-1.8 * wide, 0.0), K.at(1.8 * wide, 0.0)], mix(colour, WHITE, 0.35), 0.8)

        return K.solid(("front_shoe", colour, wide), shape, colour, detail, outline=1.2, rim=0.25, shade=0.3, shade_colour=dark)

    return shoe


# ---- Pieces that people share the making of ----------------------------------


def bone(K: Kit, tag: str, length: float, w0: float, w1: float, colour: RGBA, edge: bool):
    """A limb bone along +x from ``home``, ``w0`` wide at its root and ``w1``
    at its end. ``edge``: with its outline (a limb is placed twice, every
    bone's outline and then every bone, so a joint has no line through it)."""
    h = K.home

    def shape(d) -> None:
        K.poly(d, [K.at(0.0, -w0 / 2.0), K.at(length, -w1 / 2.0), K.at(length, w1 / 2.0), K.at(0.0, w0 / 2.0)], WHITE)
        K.oval(d, h, w0 / 2.0, w0 / 2.0, WHITE)
        K.oval(d, K.at(length, 0.0), w1 / 2.0, w1 / 2.0, WHITE)

    return K.solid(("bone", tag, round(length, 2), w0, w1, colour, edge), shape, colour, None, outline=1.2 if edge else 0.0, rim=0.0, shade=0.0)


def make_hand(K: Kit, skin: RGBA, shade: RGBA, deep: RGBA, cuff: Optional[RGBA] = None, cuff_far: Optional[RGBA] = None, size: float = 1.0):
    """``hand(mode, near)``: a hand along +x from its wrist at ``home``.
    ``cuff``: the colour of the band at its wrist, or none. ``size``: 1 is a
    usual hand; a person who talks with the hands has larger ones."""
    k = size

    def hand(mode: str, near: bool):
        h = K.home

        def shape(d) -> None:
            K.rrect(d, h[0] - 2.4, h[1] - 3.5 * k, h[0] + 1.4, h[1] + 3.5 * k, 1.2, WHITE)
            if mode == "flat":
                K.oval(d, K.at(5.2 * k, 0.0), 5.2 * k, 2.7 * k, WHITE)
            elif mode == "fist":
                K.oval(d, K.at(3.6 * k, 0.0), 3.7 * k, 3.6 * k, WHITE)
            else:
                K.oval(d, K.at(3.6 * k, 0.0), 3.8 * k, 3.3 * k, WHITE)
            if mode == "soft":
                K.stroke(d, [K.at(3.0 * k, -2.0 * k), K.at(5.4 * k, -3.6 * k)], WHITE, 2.2 * k)
                K.stroke(d, [K.at(4.8 * k, 0.6 * k), K.at(7.8 * k, 1.3 * k)], WHITE, 2.5 * k)
            elif mode == "point":
                K.stroke(d, [K.at(4.5 * k, -0.7 * k), K.at(10.8 * k, -1.4 * k)], WHITE, 2.3 * k)
                K.stroke(d, [K.at(3.0 * k, 2.0 * k), K.at(5.0 * k, 3.6 * k)], WHITE, 2.1 * k)
            elif mode == "open":
                for dy, reach in ((-3.2, 8.4), (-1.1, 9.8), (1.1, 9.6), (3.1, 8.2)):
                    K.stroke(d, [K.at(4.4 * k, dy * 0.6 * k), K.at(reach * k, dy * 1.25 * k)], WHITE, 2.0 * k)
                K.stroke(d, [K.at(2.6 * k, -2.4 * k), K.at(4.4 * k, -5.6 * k)], WHITE, 2.1 * k)

        def detail(d) -> None:
            band = cuff if near else (cuff_far or cuff)
            if band is not None:
                K.rrect(d, h[0] - 3.0, h[1] - 4.2 * k, h[0] + 1.2, h[1] + 4.2 * k, 0.0, band)
            if mode == "fist":
                K.line(d, [K.at(4.4 * k, -2.0 * k), K.at(5.6 * k, 0.0), K.at(4.4 * k, 2.0 * k)], deep, 0.6)
            if mode == "open":
                for dy in (-1.0, 1.0):
                    K.line(d, [K.at(5.2 * k, dy * 0.9 * k), K.at(7.6 * k, dy * 1.5 * k)], deep, 0.4)

        return K.solid(("hand", mode, near, skin, cuff, size), shape, skin if near else shade, detail, outline=1.1, rim=0.3, shade=0.3,
                       shade_colour=deep)

    return hand


def make_shoe(K: Kit, colour: RGBA, dark: RGBA, ankle_up: float = 3.0, long: float = 1.0, sole: Optional[RGBA] = None, heel: float = 0.0):
    """``shoe(near)``: a shoe from its ankle at ``home``; its sole is
    ``ankle_up`` under it. ``heel``: how high its heel is."""

    def shoe(near: bool):
        h = K.home

        def shape(d) -> None:
            K.oval(d, K.at(2.6 * long, 0.6), 6.0 * long, 3.2, WHITE)
            K.rrect(d, h[0] - 3.4, h[1] - 0.4, h[0] + 8.4 * long, h[1] + ankle_up + 0.4, 1.6, WHITE)
            K.oval(d, h, 3.2, 3.0, WHITE)
            if heel > 0.0:
                K.rrect(d, h[0] - 3.4, h[1] + ankle_up - 1.0, h[0] - 0.6, h[1] + ankle_up + heel, 0.4, WHITE)

        def detail(d) -> None:
            K.rrect(d, h[0] - 5.0, h[1] + ankle_up - 1.0, h[0] + 10.0 * long, h[1] + ankle_up + 2.0 + heel, 0.0, sole or dark)
            K.line(d, [K.at(2.0, -1.4), K.at(6.0 * long, -0.6)], mix(colour, WHITE, 0.35), 0.8)

        return K.solid(("shoe", near, colour, long, heel), shape, colour if near else mix(colour, dark, 0.6), detail, outline=1.2, rim=0.25,
                       shade=0.3, shade_colour=dark)

    return shoe


def make_neck(K: Kit, colour: RGBA, width: float = 5.0):
    """``neck(length)``: a neck along +x from its base."""

    def neck(length: float):
        def shape(d) -> None:
            K.poly(d, [K.at(-1.0, -width / 2.0), K.at(length, -width / 2.0 + 0.2), K.at(length, width / 2.0 - 0.2), K.at(-1.0, width / 2.0 + 0.2)],
                   WHITE)

        return K.solid(("neck", length, colour, width), shape, colour, None, outline=1.1, rim=0.0, shade=0.0)

    return neck


def make_eyes(K: Kit, near: Point, far: Point, *, ink: RGBA = (28, 24, 32, 255), white: Optional[RGBA] = (252, 248, 238, 255),
              iris: Optional[RGBA] = None, lid: Optional[RGBA] = None, size: float = 1.0, lash: float = 0.0):
    """``eyes(mode)``: two small eyes, from the middle of the head. With
    ``white`` they have whites (and an ``iris`` colour if given); without, they
    are dots. ``lid``: the colour of the line over an open eye. ``lash``: 0 to 1,
    how heavy the upper line is and how far it goes out past the corner of
    each eye, open or shut."""

    def eyes(mode: str):
        def paint(d) -> None:
            for (ex, ey), k in ((near, 1.0), (far, 0.85)):
                c = K.at(ex, ey)
                rx, ry = 2.0 * size * k, 1.8 * size
                out = -1.0 if (ex, ey) == near else 1.0
                if lash and mode in ("closed", "happy"):
                    y = 0.8 if mode == "closed" else -0.9
                    K.line(d, [(c[0] + out * rx, c[1] - y * 0.3), (c[0] + out * (rx + 1.5 * lash), c[1] - y * 0.3 - 1.0 * lash)], ink, 0.5 + 0.3 * lash)
                if mode == "closed":
                    K.line(d, [(c[0] - rx, c[1] - 0.2), (c[0], c[1] + 0.8), (c[0] + rx, c[1] - 0.2)], ink, 0.9 + 0.2 * lash)
                    continue
                if mode == "happy":
                    K.line(d, [(c[0] - rx, c[1] + 0.6), (c[0], c[1] - 0.9), (c[0] + rx, c[1] + 0.6)], ink, 0.9)
                    continue
                if mode == "wince":
                    side = 1.0 if (ex, ey) == near else -1.0
                    K.line(d, [(c[0] - rx * side, c[1] - 1.3), (c[0] + rx * 0.6 * side, c[1]), (c[0] - rx * side, c[1] + 1.3)], ink, 0.9)
                    continue
                tall = ry + (0.6 if mode == "wide" else 0.0)
                at = (c[0] + 0.3, c[1] - (0.6 if mode == "up" else 0.0))
                if white is not None:
                    K.oval(d, c, rx, tall, white)
                    if iris is not None:
                        K.oval(d, at, 1.3 * size * k, 1.4 * size, iris)
                    K.oval(d, at, 0.85 * size * k, 0.95 * size, ink)
                    K.oval(d, (at[0] - 0.4, at[1] - 0.5), 0.35, 0.35, WHITE)
                    K.line(d, [(c[0] - rx - 0.3, c[1] - 0.2), (c[0] - rx * 0.4, c[1] - tall), (c[0] + rx * 0.5, c[1] - tall),
                               (c[0] + rx + 0.3, c[1] - 0.4)], ink if lash else (lid or ink), 0.7 + 0.3 * lash)
                    if lash:
                        K.line(d, [(c[0] + out * (rx + 0.2), c[1] - 0.4), (c[0] + out * (rx + 0.5 + 1.2 * lash), c[1] - 0.5 - 1.2 * lash)], ink,
                               0.5 + 0.4 * lash)
                else:
                    if mode == "wide":
                        K.oval(d, at, 1.9 * size * k, 2.0 * size, WHITE)
                    K.oval(d, at, 1.0 * size * k, 1.1 * size, ink)
                    K.oval(d, (at[0] - 0.35, at[1] - 0.4), 0.3, 0.3, WHITE)
                    if lid is not None and mode != "wide":
                        K.line(d, [(c[0] - rx, c[1] - 0.8), (c[0], c[1] - 1.7), (c[0] + rx, c[1] - 1.0)], lid, 0.5)

        return K.piece(("eyes", mode, near, far, ink, white, iris, size, lash), paint)

    return eyes


def make_brows(K: Kit, near: Sequence[Point], far: Sequence[Point], colour: RGBA, width: float = 1.2, under: Optional[RGBA] = None):
    """``brows(mood)``: each brow a line of three points, from the middle of
    the head, the inner end last for the near brow and first for the far one.
    -1 set, 0 level, 1 raised."""

    def brows(mood: int):
        up = -1.1 if mood > 0 else 0.0
        inner = 0.9 if mood < 0 else 0.0

        def paint(d) -> None:
            a = [K.at(near[0][0], near[0][1] + up), K.at(near[1][0], near[1][1] + up), K.at(near[2][0], near[2][1] + up + inner)]
            b = [K.at(far[0][0], far[0][1] + up + inner), K.at(far[1][0], far[1][1] + up), K.at(far[2][0], far[2][1] + up)]
            for pts, w in ((a, width), (b, width * 0.9)):
                if under is not None:
                    K.stroke(d, pts, under, w + 0.6)
                K.stroke(d, pts, colour, w)

        return K.piece(("brows", mood, tuple(near), tuple(far), colour, width), paint)

    return brows


def make_mouth(K: Kit, at: Point, colour: RGBA = (112, 48, 50, 255), *, ink: RGBA = (28, 24, 32, 255), tongue: RGBA = (224, 122, 116, 255),
               teeth: RGBA = (250, 248, 240, 255), wide: float = 1.0, lips: Optional[RGBA] = None):
    """``mouth(mode)``: smile, flat, o, grit, open, big; from the middle of
    the head. ``lips``: a colour for full lips; without it a mouth is a
    line."""

    def mouth(mode: str):
        c = K.at(*at)
        w = wide

        def paint(d) -> None:
            if lips is not None and mode in ("smile", "flat"):
                up = 0.5 if mode == "smile" else 0.0
                K.poly(d, [(c[0] - 2.5 * w, c[1] - 0.2 - up), (c[0] - 0.9, c[1] - 1.1), (c[0], c[1] - 0.7), (c[0] + 0.8, c[1] - 1.1),
                           (c[0] + 2.3 * w, c[1] - 0.4 - up), (c[0] + 1.0, c[1] + 1.3), (c[0] - 1.0, c[1] + 1.4)], lips)
                K.line(d, [(c[0] - 2.5 * w, c[1] - 0.2 - up), (c[0], c[1] + 0.2), (c[0] + 2.3 * w, c[1] - 0.4 - up)], colour, 0.5)
                return
            if lips is not None and mode in ("o", "open", "big"):
                ry = 1.3 if mode == "o" else 2.2 if mode == "big" else 1.5
                K.oval(d, (c[0], c[1] + 0.2), (1.3 if mode == "o" else 2.1) * w + 0.7, ry + 0.7, lips)
                K.oval(d, (c[0], c[1] + 0.2), (1.3 if mode == "o" else 2.1) * w, ry, colour)
                if mode != "o":
                    K.oval(d, (c[0], c[1] + 0.2 + ry * 0.5), 1.1, ry * 0.4, tongue)
                return
            if mode == "smile":
                K.line(d, [(c[0] - 2.5 * w, c[1] - 0.4), (c[0] - 0.2, c[1] + 0.6), (c[0] + 2.3 * w, c[1] - 0.6)], colour, 0.8)
            elif mode == "flat":
                K.line(d, [(c[0] - 2.1 * w, c[1]), (c[0] + 2.0 * w, c[1] - 0.1)], colour, 0.8)
            elif mode == "o":
                K.oval(d, c, 1.1, 1.3, colour, ink, 0.4)
            elif mode == "grit":
                K.rrect(d, c[0] - 2.4 * w, c[1] - 1.0, c[0] + 2.2 * w, c[1] + 1.0, 0.7, teeth, ink, 0.5)
                K.line(d, [(c[0], c[1] - 0.9), (c[0], c[1] + 0.9)], ink, 0.3)
            else:
                ry = 2.1 if mode == "big" else 1.3
                K.oval(d, (c[0], c[1] + 0.3), (2.3 if mode == "big" else 1.8) * w, ry, colour, ink, 0.5)
                K.oval(d, (c[0], c[1] + 0.3 + ry * 0.5), 1.2, ry * 0.4, tongue)

        return K.piece(("mouth", mode, at, colour, wide, lips), paint)

    return mouth


def make_head(K: Kit, key: tuple, skin: RGBA, shade: RGBA, deep: RGBA, *, skull: Tuple[float, float, float, float] = (0.0, -2.4, 8.0, 9.0),
              jaw: Tuple[float, float, float, float] = (2.4, 4.0, 5.6, 7.4), nose: Optional[Sequence[Point]] = ((7.0, -1.0), (9.8, 3.2), (9.2, 4.6), (7.0, 5.0)),
              ear: Optional[Tuple[float, float, float, float]] = (-4.8, 1.0, 2.2, 3.3), shape: Optional[Callable] = None,
              under: Optional[Callable] = None, over: Optional[Callable] = None):
    """``head()``: a head from its middle, seen three quarters and facing
    right. ``skull`` and ``jaw`` are ovals ``(x, y, rx, ry)``; ``nose`` is
    the part of it that stands out of the face; ``ear`` an oval.

    ``shape(d)`` adds to the silhouette (hair that stands off the head, a
    beard, a bun). ``under(d)`` paints on the head before the ear (the hair,
    down to its line). ``over(d)`` paints after it (lenses, the lines of a
    face, a moustache). What stays the character's is all of that: this
    function is only the skull."""

    def head():
        def silhouette(d) -> None:
            K.oval(d, K.at(skull[0], skull[1]), skull[2], skull[3], WHITE)
            K.oval(d, K.at(jaw[0], jaw[1]), jaw[2], jaw[3], WHITE)
            if nose is not None:
                K.poly(d, [K.at(x, y) for x, y in nose], WHITE)
                tip = max(nose, key=lambda q: q[0])
                K.oval(d, K.at(tip[0] - 1.0, tip[1] + 0.6), 1.6, 1.5, WHITE)
            if shape is not None:
                shape(d)

        def detail(d) -> None:
            # The far side of the face is in shade.
            K.oval(d, K.at(jaw[0] + jaw[2] + 0.6, jaw[1] + 3.4), 2.2, 4.0, mix(skin, shade, 0.7))
            if under is not None:
                under(d)
            if ear is not None:
                K.oval(d, K.at(ear[0], ear[1]), ear[2], ear[3], skin, OUTLINE, 0.6)
                K.line(d, [K.at(ear[0] - 0.5, ear[1] - 1.4), K.at(ear[0] + 0.5, ear[1]), K.at(ear[0] - 0.3, ear[1] + 1.4)], deep, 0.45)
            if nose is not None:
                tip = max(nose, key=lambda q: q[0])
                K.line(d, [K.at(tip[0] - 1.0, tip[1] + 2.0), K.at(tip[0] - 2.8, tip[1] + 1.8), K.at(tip[0] - 3.4, tip[1] + 0.9)], deep, 0.7)
            K.line(d, [K.at(jaw[0] - 3.4, jaw[1] + 4.2), K.at(jaw[0] - 1.0, jaw[1] + 6.8), K.at(jaw[0] + 1.6, jaw[1] + 7.4)], mix(skin, deep, 0.55), 0.6)
            if over is not None:
                over(d)

        return K.solid(("head",) + tuple(key), silhouette, skin, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=deep)

    return head


def make_torso(K: Kit, key: tuple, colour: RGBA, dark: RGBA, *, back: Tuple[float, float, float, float] = (9.2, 9.6, 8.6, 9.4),
               front: Tuple[float, float, float, float] = (8.2, 10.0, 9.6, 10.2), hem_y: float = 9.0, top: float = -38.0,
               shoulders: Tuple[Point, Point] = ((-5.4, -31.0), (6.0, -30.8)), shoulder_r: Tuple[float, float] = (5.2, 4.8), neck: Tuple[float, float] = (-4.0, 4.0),
               belly: float = 0.0, shade_from: float = 7.4, detail: Optional[Callable] = None):
    """``torso(hem_back, hem_front)``: a trunk and what hangs from it, from
    the hips at ``home``, the spine up. ``back`` and ``front`` are how far
    the edge is from the spine at the shoulder, the chest, the waist and the
    hem; ``hem_y`` is how far under the hips the hem is (9 is a jacket, 26 a
    coat to the knee, 40 a robe to the ankle). ``belly`` pushes the front of
    the waist out. ``detail(d, hem_back, hem_front)`` paints the front of it
    (a shirt, lapels, buttons, a pattern): that is the character's."""

    def torso(hem_back: int, hem_front: int):
        hb, hf = float(hem_back), float(hem_front)
        long = max(0.0, (hem_y - 9.0) / 30.0)
        back_hem = K.at(-back[3] - hb * (1.0 + long), hem_y - hb * 0.25)
        front_hem = K.at(front[3] + hf * (1.0 + long), hem_y - 0.6)

        def shape(d) -> None:
            K.poly(d, [K.at(neck[0], top), K.at(-back[0], top + 4.0), K.at(-back[1], -24.0), K.at(-back[2], -4.0), back_hem, front_hem,
                       K.at(front[2] + belly, -4.0), K.at(front[1] + belly * 0.5, -16.0), K.at(front[1], -27.0), K.at(front[0], top + 3.0),
                       K.at(neck[1], top - 0.4)], WHITE)
            K.oval(d, K.at(*shoulders[0]), shoulder_r[0], shoulder_r[0] + 0.6, WHITE)
            K.oval(d, K.at(*shoulders[1]), shoulder_r[1], shoulder_r[1] + 0.6, WHITE)

        def paint(d) -> None:
            # The far side of the chest is in its own shade.
            K.poly(d, [K.at(shade_from, top - 2.0), K.at(40.0, top - 2.0), K.at(40.0, hem_y + 4.0), K.at(shade_from + 0.2 + hf * 0.6, hem_y + 4.0),
                       K.at(shade_from - 0.8, -6.0)], dark)
            if detail is not None:
                detail(d, hb, hf)

        return K.solid(("torso",) + tuple(key) + (hem_back, hem_front), shape, colour, paint, outline=1.3, rim=0.3, shade=0.4, shade_colour=dark)

    return torso


def make_figure(K: Kit, key: tuple, colour: RGBA, dark: RGBA, *, back: Tuple[float, float, float, float, float] = (7.4, 7.8, 6.0, 8.2, 9.0),
                front: Tuple[float, float, float, float, float] = (6.6, 9.4, 6.4, 8.8, 9.4), hem_y: float = 9.0, top: float = -38.0,
                shoulders: Tuple[Point, Point] = ((-4.6, -31.6), (5.4, -31.2)), shoulder_r: Tuple[float, float] = (4.4, 4.0), neck: Tuple[float, float] = (-3.2, 3.4),
                waist_y: float = -13.0, shade_from: float = 6.6, detail: Optional[Callable] = None):
    """``torso(hem_back, hem_front)`` of a woman: from the hips at ``home``,
    the spine up. ``back`` and ``front`` are how far the edge is from the
    spine at the shoulder, the bust, the waist, the hip and the hem. The
    waist (at ``waist_y``) is the narrow part; what is under the hip is a
    skirt or the skirt of a coat, and it swings.

    No two women of the cast have one set of these numbers: a slight woman, a
    tall one and a stout one are different shapes, not one shape in three
    sizes."""

    def torso(hem_back: int, hem_front: int):
        hb, hf = float(hem_back), float(hem_front)
        long = max(0.0, (hem_y - 9.0) / 30.0)
        back_hem = K.at(-back[4] - hb * (1.0 + long), hem_y - hb * 0.25)
        front_hem = K.at(front[4] + hf * (1.0 + long), hem_y - 0.6)
        bust_y = top + 12.5

        def shape(d) -> None:
            K.poly(d, [K.at(neck[0], top), K.at(-back[0], top + 4.0), K.at(-back[1], bust_y), K.at(-back[2] - 0.4, (bust_y + waist_y) / 2.0), K.at(-back[2], waist_y),
                       K.at(-back[3] + 0.6, waist_y + 6.0), K.at(-back[3], -1.0), back_hem, front_hem, K.at(front[3], -1.0), K.at(front[3] - 0.8, waist_y + 6.0),
                       K.at(front[2], waist_y), K.at(front[1] - 1.4, bust_y + 5.0), K.at(front[1], bust_y + 0.6), K.at(front[1] - 0.8, bust_y - 3.6),
                       K.at(front[0], top + 3.4), K.at(neck[1], top - 0.4)], WHITE)
            K.oval(d, K.at(*shoulders[0]), shoulder_r[0], shoulder_r[0] + 0.6, WHITE)
            K.oval(d, K.at(*shoulders[1]), shoulder_r[1], shoulder_r[1] + 0.6, WHITE)

        def paint(d) -> None:
            # The far side is in its own shade, and so is what is under the bust.
            K.poly(d, [K.at(shade_from, top - 2.0), K.at(40.0, top - 2.0), K.at(40.0, hem_y + 4.0), K.at(shade_from + 1.0 + hf * 0.6, hem_y + 4.0),
                       K.at(shade_from - 1.0, waist_y)], dark)
            K.line(d, [K.at(front[1] - 5.0, bust_y + 3.4), K.at(front[1] - 2.4, bust_y + 4.6), K.at(front[1] - 0.8, bust_y + 3.0)], dark, 0.7)
            if detail is not None:
                detail(d, hb, hf)

        return K.solid(("figure",) + tuple(key) + (hem_back, hem_front), shape, colour, paint, outline=1.3, rim=0.3, shade=0.4, shade_colour=dark)

    return torso


def brow_mood(pose: Pose) -> int:
    """-1, 0 or 1 from a pose's ``brows``."""
    v = float(pose["brows"])  # type: ignore[arg-type]
    return 1 if v > 0.5 else -1 if v < -0.5 else 0


def chain(anchor: Point, links: int, link: float, heading: float, *, wave: float = 0.0, curl: float = 0.0, phase: float = 0.0,
          lead: float = 0.0) -> Tuple[Point, ...]:
    """The points of something that hangs from ``anchor`` in the world (hair,
    a scarf, a ribbon): ``links`` of ``link`` each. ``heading``: 90 hangs,
    180 trails behind, 270 is up. It waves by ``wave`` and curls by ``curl``
    a link."""
    at = anchor
    out = [at]
    for k in range(links):
        a = heading + curl * k + wave * math.sin(phase - 0.85 * k + lead) * (0.35 + 0.65 * k / max(1, links))
        at = (at[0] + link * math.cos(math.radians(a)), at[1] + link * math.sin(math.radians(a)))
        out.append(at)
    return tuple(out)


def ribbon(K: Kit, key: tuple, chains: Sequence[Sequence[Point]], width: float, colour: RGBA, dark: Optional[RGBA] = None, taper: float = 1.0):
    """Ribbons through ``chains`` (points FROM the pin the piece is placed
    at), as ONE piece cut on whole frame pixels. Place it unturned at
    ``pin(anchor)``: a long thin thing does not survive being reduced and
    then turned. ``taper``: the width at the end, as a part of ``width``."""
    chains = tuple(tuple((round(x, 1), round(y, 1)) for x, y in ch) for ch in chains)

    def paint(d) -> None:
        for edge in (True, False):
            for ch in chains:
                pts = [K.at(x, y) for x, y in ch]
                for k in range(len(pts) - 1):
                    w = width * lerp(1.0, taper, k / max(1, len(pts) - 2))
                    K.stroke(d, pts[k:k + 2], OUTLINE if edge else colour, w + (2.4 if edge else 0.0))
        if dark is not None:
            for ch in chains:
                K.line(d, [K.at(x, y + width * 0.22) for x, y in ch], dark, max(0.6, width * 0.18))

    return K.aligned(("ribbon",) + tuple(key) + (chains, width, colour, taper), paint)


# ---- Things written in the air -----------------------------------------------


def chalk(K: Kit, key: tuple, shape: Callable, fill: RGBA, dark: RGBA):
    """A flat bright thing with an outline: a symbol, a sweep, a spark."""
    return K.solid(("chalk",) + tuple(key) + (fill,), shape, fill, None, outline=1.1, rim=0.0, shade=0.5, shade_colour=dark)


#: A symbol as lines in a box one wide and one high. A character adds its own.
STROKES: Dict[str, Tuple[Tuple[Point, ...], ...]] = {
    "0": (((0.5, 0.0), (0.1, 0.25), (0.1, 0.75), (0.5, 1.0), (0.9, 0.75), (0.9, 0.25), (0.5, 0.0)),),
    "1": (((0.25, 0.25), (0.6, 0.0), (0.6, 1.0)),),
    "2": (((0.05, 0.22), (0.35, 0.0), (0.8, 0.05), (0.95, 0.3), (0.6, 0.6), (0.05, 1.0), (1.0, 1.0)),),
    "3": (((0.05, 0.1), (0.5, 0.0), (0.95, 0.2), (0.5, 0.48), (0.95, 0.75), (0.5, 1.0), (0.05, 0.9)),),
    "4": (((0.7, 1.0), (0.7, 0.0), (0.05, 0.68), (1.0, 0.68)),),
    "5": (((0.95, 0.0), (0.15, 0.0), (0.05, 0.45), (0.6, 0.4), (0.95, 0.66), (0.7, 1.0), (0.05, 0.94)),),
    "6": (((0.85, 0.05), (0.4, 0.1), (0.1, 0.55), (0.3, 1.0), (0.8, 0.95), (0.9, 0.6), (0.5, 0.45), (0.15, 0.62)),),
    "7": (((0.05, 0.0), (0.95, 0.0), (0.4, 1.0)),),
    "8": (((0.5, 0.48), (0.15, 0.25), (0.5, 0.0), (0.85, 0.25), (0.5, 0.48), (0.1, 0.75), (0.5, 1.0), (0.9, 0.75), (0.5, 0.48)),),
    "9": (((0.85, 0.4), (0.5, 0.55), (0.12, 0.4), (0.2, 0.05), (0.7, 0.0), (0.9, 0.4), (0.7, 0.9), (0.2, 0.98)),),
    "+": (((0.5, 0.15), (0.5, 0.85)), ((0.1, 0.5), (0.9, 0.5))),
    "-": (((0.1, 0.5), (0.9, 0.5)),),
    "=": (((0.1, 0.35), (0.9, 0.35)), ((0.1, 0.68), (0.9, 0.68))),
    "?": (((0.1, 0.22), (0.4, 0.0), (0.85, 0.12), (0.85, 0.4), (0.5, 0.6), (0.5, 0.72)), ((0.5, 0.96), (0.5, 1.0))),
    "!": (((0.5, 0.0), (0.5, 0.68)), ((0.5, 0.96), (0.5, 1.0))),
    "x": (((0.1, 0.15), (0.9, 0.9)), ((0.9, 0.15), (0.1, 0.9))),
    "epsilon": (((1.0, 0.15), (0.5, 0.0), (0.1, 0.22), (0.5, 0.5), (0.05, 0.78), (0.5, 1.0), (1.0, 0.85)),),
    "sigma": (((0.95, 0.12), (0.9, 0.0), (0.05, 0.0), (0.6, 0.5), (0.05, 1.0), (0.9, 1.0), (0.95, 0.88)),),
    "pi": (((0.0, 0.12), (1.0, 0.12)), ((0.28, 0.12), (0.2, 1.0)), ((0.72, 0.12), (0.74, 0.85), (0.92, 1.0))),
    "tau": (((0.0, 0.12), (1.0, 0.12)), ((0.5, 0.12), (0.46, 0.85), (0.7, 1.0))),
    "delta": (((0.85, 0.05), (0.35, 0.0), (0.7, 0.42), (0.9, 0.72), (0.5, 1.0), (0.12, 0.72), (0.4, 0.4), (0.7, 0.42)),),
    "integral": (((0.95, 0.06), (0.72, 0.0), (0.56, 0.2), (0.44, 0.8), (0.28, 1.0), (0.05, 0.94)),),
    "turnstile": (((0.1, 0.05), (0.1, 0.95)), ((0.1, 0.5), (0.95, 0.5))),
    "forall": (((0.0, 0.0), (0.5, 1.0), (1.0, 0.0)), ((0.2, 0.42), (0.8, 0.42))),
    "exists": (((0.1, 0.0), (0.9, 0.0), (0.9, 1.0), (0.1, 1.0)), ((0.2, 0.5), (0.9, 0.5))),
    "in": (((0.95, 0.05), (0.4, 0.05), (0.08, 0.5), (0.4, 0.95), (0.95, 0.95)), ((0.1, 0.5), (0.9, 0.5))),
    "lambda": (((0.1, 0.0), (0.3, 0.05), (0.9, 1.0)), ((0.5, 0.42), (0.1, 1.0))),
    "psi": (((0.5, 0.0), (0.5, 1.0)), ((0.08, 0.15), (0.14, 0.55), (0.5, 0.7), (0.86, 0.55), (0.92, 0.15))),
    "aleph": (((0.1, 0.05), (0.9, 0.95)), ((0.85, 0.05), (0.8, 0.3), (0.56, 0.44)), ((0.42, 0.52), (0.15, 0.7), (0.12, 0.95))),
    "sqrt": (((0.0, 0.6), (0.14, 0.52), (0.32, 1.0), (0.5, 0.05), (1.0, 0.05)),),
    "infinity": (tuple((0.5 + 0.5 * math.cos(t) / (1.0 + math.sin(t) ** 2), 0.5 + 0.9 * math.sin(t) * math.cos(t) / (1.0 + math.sin(t) ** 2))
                       for t in [math.tau * k / 24.0 for k in range(25)]),),
}


def glyph(K: Kit, symbols: Sequence[str], size: float, fill: RGBA, dark: RGBA, width: Optional[float] = None):
    """Symbols of ``STROKES`` in a row, ``size`` high, the middle at ``home``.
    ``glyph(K, "13", ...)`` is a number; ``glyph(K, ["epsilon"], ...)`` a
    letter."""
    symbols = tuple(symbols)
    wide, gap = size * 0.6, size * 0.3
    total = len(symbols) * wide + (len(symbols) - 1) * gap
    w = width or max(1.4, size * 0.2)

    def shape(d) -> None:
        for k, sym in enumerate(symbols):
            x0 = -total / 2.0 + k * (wide + gap)
            for line in STROKES[sym]:
                K.stroke(d, [K.at(x0 + x * wide, (y - 0.5) * size) for x, y in line], WHITE, w)

    return chalk(K, ("glyph", symbols, size, w), shape, fill, dark)


def burst(K: Kit, size: float, fill: RGBA, dark: RGBA, rays: int = 8):
    """The lines that fly out of something."""

    def shape(d) -> None:
        for k in range(rays):
            a = math.tau * (k + 0.5) / rays
            K.stroke(d, [K.at(math.cos(a) * size * 0.62, math.sin(a) * size * 0.62), K.at(math.cos(a) * size, math.sin(a) * size)], WHITE, 1.5)

    return chalk(K, ("burst", size, rays), shape, fill, dark)


def swoosh(K: Kit, radius: float, a0: int, a1: int, width: float, fill: RGBA, dark: RGBA):
    """The arc a sweep leaves, about ``home``: from ``a0``, where it is thin,
    to ``a1``, where it is ``width``."""

    def shape(d) -> None:
        steps = max(4, abs(a1 - a0) // 5)
        outer, inner = [], []
        for k in range(steps + 1):
            t = k / steps
            a = math.radians(lerp(a0, a1, t))
            outer.append(K.at(radius * math.cos(a), radius * math.sin(a)))
            inner.append(K.at((radius - width * t) * math.cos(a), (radius - width * t) * math.sin(a)))
        K.poly(d, outer + inner[::-1], WHITE)

    return chalk(K, ("swoosh", radius, a0, a1, width), shape, fill, dark)


def tick(K: Kit, size: float, fill: RGBA, dark: RGBA):
    return chalk(K, ("tick", size), lambda d: K.tick(d, K.home, size, WHITE, max(1.4, size * 0.4)), fill, dark)


def dust(K: Kit, radius: float, fill: RGBA, dark: RGBA):
    return K.solid(("dust", radius, fill), lambda d: K.oval(d, K.home, radius, radius, WHITE), fill, None, outline=0.8, rim=0.0, shade=0.4,
                   shade_colour=dark)


def entry_points(person: "Person", actor_metadata: dict, name: str):
    """``(render, main, render_canonical)`` of a character module:

        render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, "Galwah")
        TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
    """
    import argparse

    def render(out_dir, **opts) -> List[Path]:
        del opts
        return person.render(out_dir, actor_metadata)

    def render_canonical(out_dir, **opts) -> Path:
        """One frame of the first row, alone, with no sheet."""
        del opts
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        row, frames, _ms = person.rows[0]
        path = out / f"{person.target}_canonical_transparent.png"
        person.render_frame(row, 0, frames).save(path)
        return path

    def main(argv=None) -> int:
        parser = argparse.ArgumentParser(description=f"Render the {name} spritesheet.")
        parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / person.target)
        args = parser.parse_args(argv)
        for path in render(args.out_dir):
            print(path)
        return 0

    return render, main, render_canonical


# ---- The person --------------------------------------------------------------


#: Every person that a module has made, by the name of its sheet.
CAST: Dict[str, "Person"] = {}


class Person:
    """One person: a ``Build``, the pieces a character module gives it, and
    its poses.

    The module sets, before it renders:

    ``torso(hem_back, hem_front)``
        The trunk and what hangs from it (a jacket, a coat, a dress), from
        the hips at ``home``, the spine up. The two numbers are how many
        pixels wider than it hangs the hem is, behind and in front.
    ``head_layers(pose)``
        ``[(piece, name), ...]``, each from the middle of the head, in paint
        order: the head, the eyes, glasses, brows, the mouth, a hat.
    ``upper_arm(near)``, ``forearm(near)``, ``thigh(near)``, ``shin(near)``
        What each bone is dressed in: a list of ``Seg``.
    ``hand(mode, near)``, ``shoe(near)``
        See ``make_hand`` and ``make_shoe``.
    ``neck(length)`` and ``collar()``
        Or none. The collar is painted over the chin.
    ``layers``
        ``back``, ``under_torso``, ``over_torso``, ``front``: lists of
        ``fn(ctx) -> [Stamp, ...]`` for what is the character's own (a cape,
        a braid, a tail of a coat, a bow, a badge that turns with the trunk).
    ``effects(ctx) -> [Stamp, ...]``
        What is drawn over the person this frame.

    ``ctx`` has ``anim``, ``i``, ``n``, ``u`` (0 to 1 through the row),
    ``phase``, ``pose``, and, in frame pixels: ``hip``, ``neck``, ``head``,
    ``hand``, ``far_hand``, ``elbow``, ``far_elbow``, ``shoulder``,
    ``far_shoulder``, ``foot``, ``far_foot``, ``knee``, ``far_knee``; the turns
    ``lean`` (the trunk), ``turn`` (the head) and ``rot`` (all of the person);
    ``trunk(x, y)`` (a point of the trunk in the frame) and ``ground``.
    """

    def __init__(self, target: str, build: Build = Build(), frame: Tuple[int, int] = (208, 176), ground: float = 164.0, cx: float = 104.0) -> None:
        self.target = target
        CAST[target] = self
        self.b = build
        self.frame = frame
        self.ground = ground
        self.cx = cx
        self.K = Kit(frame)
        self.U = build.hip_up / 37.0
        self.rest: Pose = dict(REST)
        self.poses: Dict[str, Callable[[int, int], Pose]] = dict(LIBRARY)
        self.rows: List[Tuple[str, int, int]] = list(MAIN_ROWS)
        self.torso: Callable[[int, int], object] = lambda hb, hf: None
        self.head_layers: Callable[[Pose], List[Tuple[object, str]]] = lambda pose: []
        self.upper_arm: Callable[[bool], List[Seg]] = lambda near: []
        self.forearm: Callable[[bool], List[Seg]] = lambda near: []
        self.thigh: Callable[[bool], List[Seg]] = lambda near: []
        self.shin: Callable[[bool], List[Seg]] = lambda near: []
        self.hand: Callable[[str, bool], object] = lambda mode, near: None
        self.shoe: Callable[[bool], object] = lambda near: None
        self.neck: Optional[Callable[[float], object]] = None
        self.collar: Optional[Callable[[], object]] = None
        self.layers: Dict[str, List[Callable[[SimpleNamespace], List[Stamp]]]] = {"back": [], "under_torso": [], "over_torso": [], "front": []}
        self.effects: Callable[[SimpleNamespace], List[Stamp]] = lambda ctx: []
        #: The rows that face the viewer: name -> pose function (``FP``).
        #: A character that has any sets ``front_torso()``,
        #: ``front_head_layers(pose)`` and ``front_shoe()`` too.
        self.front_poses: Dict[str, Callable[[int, int], Pose]] = {}
        self.front_torso: Callable[[], object] = lambda: None
        self.front_head_layers: Callable[[Pose], List[Tuple[object, str]]] = lambda pose: []
        self.front_shoe: Callable[[], object] = lambda: None
        #: Half the width between the shoulders, and between the hips, seen
        #: from the front.
        self.front_span: Tuple[float, float] = (9.0, 5.2)
        self.front_effects: Callable[[SimpleNamespace], List[Stamp]] = lambda ctx: []

    # -- poses -----------------------------------------------------------------

    def P(self, **kw) -> Pose:
        """A pose of this person: ``rest`` with what differs."""
        unknown = set(kw) - set(self.rest)
        assert not unknown, unknown
        return dict(self.rest, **kw)

    def full(self, pose: Pose) -> Pose:
        """``pose`` with every key this person has (a pose of the library
        does not know a key a character added)."""
        return dict(self.rest, **pose) if set(self.rest) - set(pose) else pose

    def keys(self, u: float, frames: List[Tuple[float, Pose]]) -> Pose:
        return keys(u, [(t, self.full(p)) for t, p in frames])

    def blend(self, a: Pose, b: Pose, t: float) -> Pose:
        return blend(self.full(a), self.full(b), t)

    def row(self, fn: Callable[[int, int], Pose]) -> Callable[[int, int], Pose]:
        """Decorator: this function is the pose of the row of its name."""
        self.poses[fn.__name__] = fn
        return fn

    def alias(self, **names: str) -> None:
        """``alias(hurt="hit")``: the row ``hurt`` is posed as ``hit`` is."""
        for name, of in names.items():
            self.poses[name] = self.poses[of]

    def set_rest(self, **kw) -> None:
        """How this person stands when a row says nothing else. A key that
        ``REST`` does not have is the character's own."""
        self.rest.update(kw)

    # -- the frame -------------------------------------------------------------

    def limb(self, img: Image.Image, name: str, bones: List[Tuple[Point, Point, List[Seg]]]) -> None:
        """Every part's outline, and then every part. ``bones``: frame points
        from and to, and what the bone is dressed in."""
        K = self.K
        for edge in (True, False):
            for k, (a, b, segs) in enumerate(bones):
                length = math.dist(a, b)
                turn = angle(a, b)
                for j, (t0, t1, w0, w1, colour) in enumerate(segs):
                    at = (lerp(a[0], b[0], t0), lerp(a[1], b[1], t0))
                    K.place(img, bone(K, name, length * (t1 - t0), w0, w1, colour, edge), at, f"{name}_{k}_{j}{'_edge' if edge else ''}", turn)

    def front_row(self, fn: Callable[[int, int], Pose]) -> Callable[[int, int], Pose]:
        """Decorator: this function is the pose of the row of its name, and
        the row faces the viewer."""
        self.front_poses[fn.__name__] = fn
        return fn

    def render_front(self, anim: str, i: int, n: int) -> Image.Image:
        """A frame that faces the viewer. The limbs are dressed as the side
        view dresses the NEAR ones; the torso, the head and the shoes are the
        character's front pieces."""
        K, b, U = self.K, self.b, self.U
        pose = dict(FRONT_REST, **self.front_poses[anim](i, n))
        img = K.new_frame()
        hx, hy = pose["hip"]  # type: ignore[misc]
        ox, oy = pose["off"]  # type: ignore[misc]
        lean = float(pose["lean"])  # type: ignore[arg-type]
        hip = (self.cx + (hx + ox) * U, self.ground - b.hip_up + (hy + oy) * U)
        sw, hw = self.front_span
        trunk = -b.neck[1]

        def T(x: float, y: float) -> Point:
            r = turned((x, y), lean)
            return (hip[0] + r[0], hip[1] + r[1])

        neck = T(0.0, -trunk)
        points = {}
        for side, sign in (("l", -1.0), ("r", 1.0)):
            root = (hip[0] + sign * hw, hip[1])
            out, up = pose[side + "f"]  # type: ignore[misc]
            ankle = (root[0] + sign * out * U, self.ground - b.ankle_up - up * U + oy * U)
            # A leg seen from the front is straight from the hip to the ankle
            # (a knee bends toward the viewer, and that does not show): its
            # knee is on the line, a little out, never in.
            split = b.thigh / (b.thigh + b.shin)
            knee = (lerp(root[0], ankle[0], split) + sign * 0.5, lerp(root[1], ankle[1], split))
            self.limb(img, f"front_{side}_leg", [(root, knee, self.thigh(True)), (knee, ankle, self.shin(True))])
            K.place(img, self.front_shoe(), ankle, f"front_{side}_shoe", 0.0)  # type: ignore[arg-type]
            points[side + "_foot"] = ankle
        K.place(img, self.front_torso(), hip, "front_torso", lean)  # type: ignore[arg-type]
        hdx, hdy, tilt = pose["head"]  # type: ignore[misc]
        head = (neck[0] + hdx * U + turned((0.0, b.head_up[1]), lean * 0.5 + tilt * 0.3)[0], neck[1] + hdy * U + turned((0.0, b.head_up[1]), lean * 0.5 + tilt * 0.3)[1])
        if self.neck is not None:
            K.place(img, self.neck(float(round(math.dist(neck, head) - 4.0))), neck, "front_neck", angle(neck, head))  # type: ignore[arg-type]
        for side, sign in (("l", -1.0), ("r", 1.0)):
            shoulder = T(sign * sw, -trunk + 4.6)
            dx, dy = pose[side + "a"]  # type: ignore[misc]
            target = (shoulder[0] + sign * dx * U, shoulder[1] + dy * U)
            z = float(pose[side + "z"])  # type: ignore[arg-type]
            upper, fore = b.upper * (1.0 - 0.35 * z), b.fore * (1.0 - 0.6 * z)
            # Of the two ways the elbow can bend, the one that hangs: down,
            # and a little out from the body.
            elbow, wrist = max((solve(shoulder, target, upper, fore, s) for s in (1.0, -1.0)),
                               key=lambda ew: (ew[0][1] - shoulder[1]) + 0.3 * sign * (ew[0][0] - shoulder[0]))
            self.limb(img, f"front_{side}_arm", [(shoulder, elbow, self.upper_arm(True)), (elbow, wrist, self.forearm(True))])
            K.place(img, self.hand(str(pose[side + "h"]), True), wrist, f"front_{side}_hand", angle(elbow, wrist))  # type: ignore[arg-type]
            points[side + "_hand"] = wrist
        for part, name in self.front_head_layers(pose):
            K.place(img, part, head, "front_" + name, lean * 0.4 + tilt)  # type: ignore[arg-type]
        ctx = SimpleNamespace(anim=anim, i=i, n=n, u=shot(i, n), phase=math.tau * i / max(1, n), pose=pose, hip=hip, neck=neck, head=head,
                              left_hand=points["l_hand"], right_hand=points["r_hand"], ground=self.ground, person=self)
        for part, at, name, degrees in self.front_effects(ctx):
            K.place(img, part, at, name, degrees)  # type: ignore[arg-type]
        return K.downsample(img)

    def render_frame(self, anim: str, i: int, n: int) -> Image.Image:
        if anim in self.front_poses:
            return self.render_front(anim, i, n)
        K, b, U = self.K, self.b, self.U
        pose = self.full(self.poses[anim](i, n))
        img = K.new_frame()
        rot = float(pose["rot"])  # type: ignore[arg-type]
        lean = float(pose["lean"])  # type: ignore[arg-type]
        hx, hy = pose["hip"]  # type: ignore[misc]
        ox, oy = pose["off"]  # type: ignore[misc]
        hip = (hx * U, -b.hip_up + hy * U)
        px, py = pose["pivot"]  # type: ignore[misc]
        pivot = (hip[0] + px * U, hip[1] + py * U)

        def W(p: Point) -> Point:
            """A point of the person (from the ground under them) in the frame."""
            r = turned((p[0] - pivot[0], p[1] - pivot[1]), rot)
            return (self.cx + ox * U + pivot[0] + r[0], self.ground + oy * U + pivot[1] + r[1])

        def trunk_local(x: float, y: float) -> Point:
            r = turned((x, y), lean)
            return (hip[0] + r[0], hip[1] + r[1])

        def arm_points(near: bool) -> Tuple[Point, Point, Point]:
            key = "na" if near else "fa"
            shoulder = trunk_local(*(b.near_shoulder if near else b.far_shoulder))
            dx, dy = pose[key]  # type: ignore[misc]
            elbow, wrist = solve(shoulder, (shoulder[0] + dx * U, shoulder[1] + dy * U), b.upper, b.fore, float(pose[key + "b"]))  # type: ignore[arg-type]
            return W(shoulder), W(elbow), W(wrist)

        def leg_points(near: bool) -> Tuple[Point, Point, Point, float]:
            root = (hip[0] + (b.near_hip if near else b.far_hip)[0], hip[1])
            fx, fy, toe = pose["nf" if near else "ff"]  # type: ignore[misc]
            knee, ankle = solve(root, (fx * U, fy * U - b.ankle_up), b.thigh, b.shin, -1.0)
            return W(root), W(knee), W(ankle), float(toe)

        n_sh, n_el, n_wr = arm_points(True)
        f_sh, f_el, f_wr = arm_points(False)
        n_hp, n_kn, n_an, n_toe = leg_points(True)
        f_hp, f_kn, f_an, f_toe = leg_points(False)
        neck_local = trunk_local(*b.neck)
        hdx, hdy, tilt = pose["head"]  # type: ignore[misc]
        up = turned(b.head_up, lean * 0.5 + tilt * 0.3)
        head_local = (neck_local[0] + up[0] + hdx * U, neck_local[1] + up[1] + hdy * U)
        turn = lean * 0.35 + tilt + rot
        head = W(head_local)
        throat = turned(b.throat, lean * 0.35 + tilt)
        ctx = SimpleNamespace(
            anim=anim, i=i, n=n, u=shot(i, n), phase=math.tau * i / max(1, n), pose=pose, hip=W(hip), neck=W(neck_local), head=head, hand=n_wr,
            far_hand=f_wr, elbow=n_el, far_elbow=f_el, shoulder=n_sh, far_shoulder=f_sh, foot=n_an, far_foot=f_an, knee=n_kn, far_knee=f_kn,
            lean=lean + rot, turn=turn, rot=rot, trunk=lambda x, y: W(trunk_local(x, y)), ground=self.ground, person=self,
        )

        def stamps(layer: str) -> None:
            for fn in self.layers[layer]:
                for part, at, name, degrees in fn(ctx):
                    K.place(img, part, at, name, degrees)  # type: ignore[arg-type]

        def arm(near: bool) -> None:
            name = "near" if near else "far"
            sh, el, wr = (n_sh, n_el, n_wr) if near else (f_sh, f_el, f_wr)
            self.limb(img, f"{name}_arm", [(sh, el, self.upper_arm(near)), (el, wr, self.forearm(near))])
            K.place(img, self.hand(str(pose["nh" if near else "fh"]), near), wr, f"{name}_hand", angle(el, wr))  # type: ignore[arg-type]

        def leg(near: bool) -> None:
            name = "near" if near else "far"
            hp, kn, an, toe = (n_hp, n_kn, n_an, n_toe) if near else (f_hp, f_kn, f_an, f_toe)
            self.limb(img, f"{name}_leg", [(hp, kn, self.thigh(near)), (kn, an, self.shin(near))])
            K.place(img, self.shoe(near), an, f"{name}_shoe", toe + rot)  # type: ignore[arg-type]

        stamps("back")
        arm(False)
        leg(False)
        kicking = pose["leg"] == "over"
        if not kicking:
            leg(True)
        if self.neck is not None:
            top = (head[0] + throat[0] * math.cos(math.radians(rot)) - throat[1] * math.sin(math.radians(rot)),
                   head[1] + throat[0] * math.sin(math.radians(rot)) + throat[1] * math.cos(math.radians(rot)))
            K.place(img, self.neck(float(round(math.dist(ctx.neck, top)))), ctx.neck, "neck", angle(ctx.neck, top))  # type: ignore[arg-type]
        stamps("under_torso")
        hem = pose["hem"]
        K.place(img, self.torso(int(round(max(0.0, hem[0]) * U)), int(round(max(0.0, hem[1]) * U))), ctx.hip, "torso", lean + rot)  # type: ignore[index,arg-type]
        if kicking:
            leg(True)
        stamps("over_torso")
        under = pose["arm"] == "under"
        if under:
            arm(True)
        for part, name in self.head_layers(pose):
            K.place(img, part, head, name, turn)  # type: ignore[arg-type]
        if self.collar is not None:
            K.place(img, self.collar(), ctx.neck, "collar", lean + rot)  # type: ignore[arg-type]
        if not under:
            arm(True)
        stamps("front")
        for part, at, name, degrees in self.effects(ctx):
            K.place(img, part, at, name, degrees)  # type: ignore[arg-type]
        return K.downsample(img)

    # -- publishing ------------------------------------------------------------

    @property
    def body_box(self) -> Tuple[float, float, float, float]:
        """The body the game moves: standing, up to the top of the head."""
        return (self.cx - self.b.half_width[0], self.ground - self.b.height, self.cx + self.b.half_width[1], self.ground)

    def check(self) -> None:
        names = [name for name, _f, _ms in self.rows]
        missing = [name for name in names if name not in self.poses and name not in self.front_poses]
        assert not missing, f"{self.target}: rows with no pose: {missing}"
        assert len(set(names)) == len(names), f"{self.target}: a row is named twice"

    def sockets(self) -> dict:
        """Where the head, the chest, the hands and a speech bubble are, in
        frame pixels, standing."""
        top = self.ground - self.b.height
        src = "explicit.profile.humanoid"
        return {
            "head": {"source": src, "point": {"x": self.cx + 2.0, "y": top + 13.0}},
            "chest": {"source": src, "point": {"x": self.cx + 1.0, "y": top + 40.0}},
            "hand_l": {"source": src, "point": {"x": self.cx - 9.0, "y": top + 62.0}},
            "hand_r": {"source": src, "point": {"x": self.cx + 11.0, "y": top + 62.0}},
            "speech_bubble": {"source": src, "point": {"x": self.cx + 2.0, "y": top - 16.0}},
        }

    def render(self, out_dir, actor_metadata: dict) -> List[Path]:
        self.check()
        if "sockets" in actor_metadata:
            # The metadata of a character that was drawn before on another
            # frame has that frame's points. These are this frame's.
            actor_metadata = dict(actor_metadata, sockets=self.sockets())
        return self.K.render(self.target, self.rows, self.render_frame, out_dir, actor_metadata, self.body_box)

    def cut_frames(self) -> List[Tuple[str, int, Tuple[int, int, int, int]]]:
        """The frames that touch the edge of their cell (and are cut there):
        ``(row, frame, box)``. A test of a character asserts there are none."""
        out = []
        w, h = self.frame
        for name, frames, _ms in self.rows:
            for i in range(frames):
                box = self.render_frame(name, i, frames).getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox()
                if box is None or box[0] <= 0 or box[1] <= 0 or box[2] >= w or box[3] >= h:
                    out.append((name, i, box))
        return out
