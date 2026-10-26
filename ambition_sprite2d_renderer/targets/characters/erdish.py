"""Sprite generator for Erdish: the mathematician who has no home but other
people's problems.

An affectionate parody of Paul Erdos. The changed name keeps the reference
clear and does not make him a biography.

The look (2026-10-13): a gaunt old man seen three quarters from the front,
facing right, about five heads tall. His back is round and his head is in
front of his feet. Iron-grey hair that is all there and is not combed, a long
thin face with hollow cheeks and deep lines from his nose to his mouth, large
ears, a long nose, and large square black glasses. A grey suit that is too
large for him, with chalk and two pens in its pocket; a wine-red pullover; a
white shirt with no tie, its collar open and out over his lapels; trousers
that are too short; socks in sandals. He has no beard.

He reads as Paul Erdos and as nobody else (Jon, 2026-10-13, of the first
draft, which had white hair round a bare head and a finger in the air: "needs
to read like paul erdos not bearnie sanders"; and "erdos did not have a
beard", of a white collar under his chin). So: his hair is grey and on top of
his head, his neck shows over his collar, and at rest he thinks; he does not
point.

He is a grown man, not a mascot (Jon, 2026-10-12, of another person of this
cast: "too cutsey"): no big head, no big eyes, no blush.

He holds nothing; the runtime held-item system is authoritative. One row is
the exception: in ``taunt`` he drinks a cup of coffee, which is part of the
joke and not an item. There is no drop shadow.

His mathematics is written in chalk: a graph that grows a point and a line at
a time (he gives everybody a number), the primes, an epsilon, and the black
square that ends a proof.

He is a rig: each limb is two bones through a solved elbow or knee, and each
thing is painted once and turned to where it sits (``_ai_era_kit``).
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from PIL import Image

from ._ai_era_kit import OUTLINE, WHITE, Kit, Point, Pose, RGBA, angle, blend, ease, keys, lerp, mix, pin, solve, turned

TARGET_NAME = "erdish"
FRAME_SIZE = (208, 176)
GROUND = 164.0
CX = 104.0

# ---- The rig: lengths in frame pixels, from his hips, up is negative ---------

#: How high his hips are when he stands. His legs are long and thin.
HIP_UP = 50.0
#: A length in a pose is in units of this many frame pixels: his hips stand 37
#: units high. A pose is of his body, whatever size it is drawn.
U = HIP_UP / 37.0
THIGH, SHIN = 24.4, 23.4
#: His trousers stop this far above his ankle; below them is his sock.
SOCK = 10.5
#: The base of his neck from his hips, his spine "straight": it is not
#: straight, and his neck is in front of his hips.
NECK: Point = (3.4, -35.0)
UPPER, FORE = 19.6, 18.6
NEAR_SHOULDER: Point = (-3.6, -31.0)
FAR_SHOULDER: Point = (9.0, -30.4)
NEAR_HIP: Point = (-3.4, 0.0)
FAR_HIP: Point = (3.4, 0.0)
#: The sole of a sandal is this far under its ankle.
ANKLE_UP = 3.0
#: The middle of his head from the base of his neck, his head level.
HEAD_UP: Point = (2.6, -12.6)
#: The top of his head above the ground, standing.
HEIGHT = 109.0

TWEED: RGBA = (112, 122, 138, 255)
TWEED_DARK: RGBA = (72, 80, 100, 255)
TWEED_LIGHT: RGBA = (150, 160, 174, 255)
PATCH: RGBA = (134, 96, 72, 255)
CARDIGAN: RGBA = (150, 60, 68, 255)
CARDIGAN_DARK: RGBA = (104, 40, 54, 255)
SHIRT: RGBA = (246, 242, 232, 255)
SHIRT_DARK: RGBA = (196, 194, 198, 255)
TEETH: RGBA = (250, 248, 240, 255)
TROUSER: RGBA = (84, 88, 106, 255)
TROUSER_DARK: RGBA = (58, 60, 78, 255)
SOCK_FILL: RGBA = (226, 216, 190, 255)
SOCK_DARK: RGBA = (170, 156, 138, 255)
SANDAL: RGBA = (124, 80, 50, 255)
SANDAL_DARK: RGBA = (74, 46, 34, 255)
SKIN: RGBA = (230, 194, 168, 255)
SKIN_SHADE: RGBA = (200, 156, 134, 255)
SKIN_DEEP: RGBA = (156, 104, 92, 255)
HAIR: RGBA = (134, 138, 150, 255)
HAIR_LIGHT: RGBA = (192, 196, 206, 255)
HAIR_SHADE: RGBA = (90, 92, 108, 255)
FRAME: RGBA = (24, 22, 30, 255)
LENS: RGBA = (236, 246, 250, 190)
INK: RGBA = (28, 24, 32, 255)
MOUTH: RGBA = (112, 48, 50, 255)
TONGUE: RGBA = (224, 122, 116, 255)
CHALK: RGBA = (250, 250, 244, 255)
CHALK_DARK: RGBA = (150, 176, 214, 255)
CHALK_BLUE: RGBA = (150, 206, 250, 255)
CHALK_PINK: RGBA = (250, 170, 176, 255)
CHALK_GOLD: RGBA = (252, 218, 120, 255)
CUP: RGBA = (246, 242, 232, 255)
CUP_DARK: RGBA = (182, 176, 170, 255)
COFFEE: RGBA = (84, 52, 36, 255)

K = Kit(FRAME_SIZE)

_TRAITS = ["intro", "story", "humanoid", "mathematician", "number_theorist", "graph_theorist", "collaborator", "scheduled_candidate",
           "playable_candidate"]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_erdish", "display_name": "Erdish"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": _TRAITS,
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": True, "fly": None, "swim": True, "crawl": True, "use_lifts": True,
                      "door_access": ["public"]},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle"},
    "tags": _TRAITS,
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": CX + 6.0, "y": GROUND - 95.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": CX + 2.0, "y": GROUND - 70.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": CX - 8.0, "y": GROUND - 48.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": CX + 12.0, "y": GROUND - 48.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": CX + 6.0, "y": GROUND - 124.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "slash", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
    },
    "authoring_description": (
        "Erdish is an affectionate parody of Paul Erdos: an itinerant mathematician fueled by coffee, "
        "collaboration, number theory, and the conviction that proofs belong to a shared mathematical world. "
        "The altered name keeps the reference recognizable without making the character a literal biography."
    ),
    "gameplay_description": (
        "Use as a wandering collaborator, theorem quest giver, support character, or playable mathematical "
        "generalist. He should seek coauthors, trade small lemmas, talk to primes as old friends, and treat "
        "ownership of ideas as less important than getting the proof into the world."
    ),
    "dialogue_hints": {
        "barks": [
            "My brain is a machine for turning coffee into theorems.",
            "I co-author with everyone.",
            "The primes never run out. Isn't that a kindness?",
        ]
    },
}


# ---- The pose ----------------------------------------------------------------

#: Standing. A row states what differs.
REST: Pose = {
    # His hips from where they are standing: +x is forward, +y is down.
    "hip": (0.0, 0.0),
    # His trunk leans this far forward, about his hips.
    "lean": 0.0,
    # His head from where it sits on his neck, and its tilt.
    "head": (0.0, 0.0, 0.0),
    # Each hand from its shoulder; which way the elbow bends (1: behind the
    # arm, as it hangs); and what the hand does.
    "na": (-1.0, 25.5),
    "fa": (2.0, 25.0),
    "nab": 1.0,
    "fab": 1.0,
    # His near arm is painted over his head, or under it (a hand that
    # reaches up past his face comes out from behind it).
    "arm": "over",
    # His near leg is painted under his jacket, or over it (a kick).
    "leg": "under",
    "nh": "soft",
    "fh": "soft",
    # The sole of each sandal from the ground under him, and its toe's turn.
    "nf": (-5.0, 0.0, 0.0),
    "ff": (6.0, 0.0, 0.0),
    # All of him turned about a point (from his hips), and then moved.
    "rot": 0.0,
    "pivot": (0.0, 0.0),
    "off": (0.0, 0.0),
    "eyes": "open",
    "mouth": "smile",
    "brows": 0.0,
    # How far the tail of his jacket swings out behind, and its front edge in
    # front.
    "hem": (0.0, 0.0),
}


def P(**kw) -> Pose:
    unknown = set(kw) - set(REST)
    assert not unknown, unknown
    return dict(REST, **kw)


ROW_POSES: Dict[str, Callable[[int, int], Pose]] = {}


def row(fn: Callable[[int, int], Pose]) -> Callable[[int, int], Pose]:
    ROW_POSES[fn.__name__] = fn
    return fn


def _loop(i: int, n: int) -> Tuple[float, float, float]:
    ph = math.tau * i / max(1, n)
    return ph, math.sin(ph), math.cos(ph)


def _shot(i: int, n: int) -> float:
    return i / max(1, n - 1)


#: One hand behind his back.
BEHIND: Point = (-9.0, 20.5)
#: His hand at his chin: he is thinking.
AT_CHIN: Point = (9.5, 2.2)


@row
def idle(i: int, n: int) -> Pose:
    # He is in the middle of a problem: one hand behind his back, his chin
    # in the other, and he looks up when a step of it comes right.
    _, s, c = _loop(i, n)
    return P(hip=(0.0, 0.4 + 0.4 * s), lean=2.0, head=(0.3, -0.3 * s, 5.0 + 2.5 * c), na=(AT_CHIN[0], AT_CHIN[1] + 0.5 * s), nh="fist",
             fa=BEHIND, eyes="closed" if i == n - 2 else "up" if s > 0.6 else "open", brows=1.0 if s > 0.6 else 0.0,
             mouth="flat" if s < 0.0 else "smile")


def _stride(ph: float, reach: float, lift: float, mid: float = 0.5) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """The near and far soles of a step cycle."""

    def foot(p: float, x0: float) -> Tuple[float, float, float]:
        s, c = math.sin(p), math.cos(p)
        up = max(0.0, -s)
        # The toe comes up to land and goes down to push off.
        return (x0 + reach * c, -lift * up, -14.0 * max(0.0, c) * (1.0 if s < 0.0 else 0.35) + 22.0 * up * max(0.0, -c))

    return foot(ph, mid - 1.0), foot(ph + math.pi, mid + 1.0)


@row
def walk(i: int, n: int) -> Pose:
    # Short quick steps, both hands behind his back, his head out in front.
    ph, s, c = _loop(i, n)
    nf, ff = _stride(ph, 7.0, 4.0)
    return P(hip=(0.5, 0.8 * math.cos(2.0 * ph)), lean=6.0, head=(0.6, 0.0, 2.0 * s), na=(-9.5, 20.0 + 0.6 * c), fa=(-8.0, 20.5 - 0.6 * c), nf=nf,
             ff=ff, hem=(1.0 + 1.5 * abs(c), 1.5 * abs(c)))


@row
def run(i: int, n: int) -> Pose:
    # He is late for a proof: all of him forward, and his hands out behind
    # him with his jacket.
    ph, s, c = _loop(i, n)
    nf, ff = _stride(ph, 12.0, 9.0, 0.0)
    return P(hip=(2.0, 1.5 + 1.6 * math.cos(2.0 * ph)), lean=20.0, head=(0.5, 0.0, -12.0), na=(-17.0 - 3.0 * c, 9.0 + 4.0 * s),
             fa=(-13.0 + 3.0 * c, 12.0 - 4.0 * s), nh="open", fh="open", nf=nf, ff=ff, mouth="open", brows=1.0, hem=(6.0, 0.0))


CROUCH = P(hip=(-2.0, 16.0), lean=24.0, head=(1.0, 0.0, -14.0), na=(4.0, 15.0), fa=(7.0, 14.5), nh="soft", fh="soft", nf=(-7.0, 0.0, 0.0),
           ff=(8.0, 0.0, 0.0), hem=(3.0, 2.0))


@row
def crouch(i: int, n: int) -> Pose:
    # His hands on his knees.
    _, s, _c = _loop(i, n)
    return dict(CROUCH, hip=(-2.0, 16.0 + 0.5 * s), eyes="closed" if i == n - 2 else "open")


@row
def crouch_walk(i: int, n: int) -> Pose:
    ph, _s, c = _loop(i, n)
    nf, ff = _stride(ph, 6.0, 2.6)
    return dict(CROUCH, hip=(-1.5, 15.5 + 0.7 * math.cos(2.0 * ph)), nf=nf, ff=ff, na=(4.0 - 2.5 * c, 15.0), fa=(7.0 + 2.5 * c, 14.5))


RISE = P(hip=(0.0, -2.0), lean=2.0, head=(0.0, 0.0, -10.0), na=(8.0, -26.0), nab=-1.0, fa=(15.0, -22.0), arm="under", nh="point", fh="open",
         nf=(-6.0, -1.0, 34.0), ff=(6.0, -10.0, 12.0), mouth="open", brows=1.0, hem=(1.0, 1.0))
APEX = P(hip=(0.0, -2.0), lean=0.0, head=(0.0, 0.0, -4.0), na=(-20.0, -6.0), nab=-1.0, fa=(21.0, -8.0), nh="open", fh="open",
         nf=(-5.0, -9.0, 22.0), ff=(8.0, -13.0, 4.0), eyes="happy", mouth="open", hem=(3.0, 3.0))
FALL = P(hip=(0.0, -3.0), lean=-6.0, head=(0.0, 0.0, 6.0), na=(-15.0, -21.0), nab=-1.0, fa=(19.0, -18.0), nh="open", fh="open",
         nf=(-8.0, -3.0, 28.0), ff=(7.0, -9.0, 8.0), eyes="wide", mouth="o", brows=1.0, hem=(5.0, 5.0))


@row
def jump(i: int, n: int) -> Pose:
    wind = P(hip=(-1.0, 10.0), lean=14.0, na=(-13.0, 17.0), fa=(-9.0, 19.0), nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), brows=-1.0)
    return keys(_shot(i, n), [(0.0, wind), (0.3, RISE), (0.6, RISE), (1.0, APEX)])


@row
def fall(i: int, n: int) -> Pose:
    _, s, c = _loop(i, n)
    return dict(FALL, na=(-15.0 + 2.0 * s, -21.0 - 2.0 * c), fa=(19.0 - 2.0 * s, -18.0 + 2.0 * c), nf=(-8.0, -3.0 + 1.5 * s, 28.0),
                ff=(7.0, -9.0 - 1.5 * s, 8.0))


LANDED = P(hip=(0.0, 18.0), lean=30.0, head=(2.0, 2.0, 2.0), na=(13.0, 22.0), fa=(17.0, 20.0), nh="open", fh="open", nf=(-8.0, 0.0, 0.0),
           ff=(9.0, 0.0, 0.0), eyes="wince", mouth="grit", hem=(4.0, 3.0))
HALF_UP = P(hip=(0.0, 7.0), lean=12.0, na=(5.0, 22.0), fa=(8.0, 21.0), nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), hem=(1.0, 2.0))


@row
def land_hard(i: int, n: int) -> Pose:
    return keys(_shot(i, n), [(0.0, FALL), (0.16, LANDED), (0.55, dict(LANDED, eyes="closed")), (1.0, HALF_UP)])


@row
def land_recovery(i: int, n: int) -> Pose:
    return keys(_shot(i, n), [(0.0, HALF_UP), (1.0, P(lean=2.0, na=AT_CHIN, nh="fist", fa=BEHIND))])


DASH = P(hip=(2.0, 6.0), lean=34.0, head=(1.0, 0.0, -24.0), na=(25.0, 5.0), nh="point", fa=(-16.0, 10.0), fh="open", nf=(-13.0, -6.0, 38.0),
         ff=(9.0, 0.0, 0.0), brows=-1.0, mouth="open", hem=(7.0, 0.0))


@row
def dash_startup(i: int, n: int) -> Pose:
    back = P(hip=(-3.0, 4.0), lean=-8.0, na=(9.0, 12.0), nh="point", fa=(12.0, 13.0), nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, -10.0), brows=1.0)
    return keys(_shot(i, n), [(0.0, back), (1.0, DASH)])


@row
def dash(i: int, n: int) -> Pose:
    # After his own finger.
    _, s, _c = _loop(i, n)
    return dict(DASH, hip=(2.0, 6.0 + 0.8 * s), nf=(-13.0 - s, -6.0 - s, 38.0), fa=(-16.0, 10.0 + s))


@row
def slide(i: int, n: int) -> Pose:
    _, s, _c = _loop(i, n)
    return P(hip=(-5.0, 23.0), lean=-38.0, head=(1.0, 0.0, 26.0), na=(-9.0, 17.0), fa=(13.0, -6.0), nh="open", fh="open",
             nf=(17.0, -1.0 - 0.5 * s, -28.0), ff=(22.0, -5.0 + 0.5 * s, -34.0), brows=1.0, mouth="o", eyes="wide", hem=(0.0, 5.0))


#: A ball, turned about its middle.
TUCK = P(hip=(0.0, 0.0), lean=36.0, head=(-17.0, 23.0, 46.0), na=(9.0, 14.0), fa=(11.0, 12.0), nh="fist", fh="fist", nf=(9.0, -26.0, 10.0),
         ff=(14.0, -29.0, 10.0), eyes="closed", mouth="flat", arm="under", pivot=(15.0, -13.5), off=(-8.0, 14.0), hem=(0.0, 3.0))


@row
def roll(i: int, n: int) -> Pose:
    return dict(TUCK, rot=360.0 * i / n)


@row
def wall_grab(i: int, n: int) -> Pose:
    _, s, _c = _loop(i, n)
    return P(hip=(3.0, -2.0 + 0.8 * s), lean=-8.0, head=(0.0, 0.0, -4.0), na=(25.0, -8.0), fa=(21.0, -14.0), arm="under", nh="open", fh="open",
             nf=(12.0, -6.0 + 0.8 * s, -55.0), ff=(14.0, -17.0 + 0.8 * s, -55.0), mouth="grit", brows=1.0)


@row
def wall_jump(i: int, n: int) -> Pose:
    held = wall_grab(0, 6)
    push = P(hip=(-4.0, -3.0), lean=-26.0, head=(0.0, 0.0, 16.0), na=(-18.0, -15.0), nab=-1.0, fa=(-8.0, -21.0), nh="open", fh="open",
             nf=(11.0, 0.0, -24.0), ff=(13.0, -7.0, -34.0), brows=1.0, mouth="open", hem=(0.0, 5.0))
    away = dict(push, nf=(2.0, -8.0, 10.0), ff=(8.0, -13.0, 0.0), na=(-20.0, -6.0), fa=(-6.0, -16.0))
    return keys(_shot(i, n), [(0.0, held), (0.4, push), (1.0, away)])


HANG = P(hip=(-1.0, 0.0), lean=1.0, head=(-1.0, 1.0, -14.0), na=(24.0, -15.0), fa=(18.0, -21.0), arm="under", nh="fist", fh="fist",
         nf=(-3.0, -1.0, 34.0), ff=(4.0, -3.0, 28.0), mouth="grit", brows=1.0)
PERCH = P(hip=(1.0, 16.0), lean=28.0, head=(1.0, 0.0, -16.0), na=(12.0, 21.0), fa=(15.0, 19.0), nh="open", fh="open", nf=(-7.0, 0.0, 0.0),
          ff=(9.0, 0.0, 0.0), hem=(3.0, 3.0))


@row
def ledge_grab(i: int, n: int) -> Pose:
    _, s, _c = _loop(i, n)
    return dict(HANG, lean=1.0 + 2.5 * s, nf=(-3.0 - 2.0 * s, -1.0, 34.0), ff=(4.0 - 2.0 * s, -3.0, 28.0))


@row
def ledge_climb(i: int, n: int) -> Pose:
    pull = P(hip=(1.0, -3.0), lean=14.0, head=(1.0, 0.0, -12.0), na=(15.0, 4.0), fa=(17.0, 1.0), nh="fist", fh="fist", nf=(-4.0, -3.0, 30.0),
             ff=(10.0, -17.0, -8.0), mouth="grit", brows=-1.0, hem=(1.0, 3.0))
    return keys(_shot(i, n), [(0.0, HANG), (0.5, pull), (1.0, PERCH)])


@row
def ledge_getup(i: int, n: int) -> Pose:
    return keys(_shot(i, n), [(0.0, PERCH), (0.6, HALF_UP), (1.0, P())])


@row
def ledge_roll(i: int, n: int) -> Pose:
    u = _shot(i, n)
    if u < 0.2:
        return keys(u, [(0.0, PERCH), (0.2, TUCK)])
    return dict(TUCK, rot=360.0 * ease((u - 0.2) / 0.8))


SWEEP_LOW = P(hip=(4.0, 9.0), lean=24.0, head=(1.0, 0.0, -16.0), na=(25.0, 9.0), fa=(-10.0, 13.0), nh="point", fh="open", nf=(-9.0, 0.0, 10.0),
              ff=(11.0, 0.0, 0.0), brows=-1.0, mouth="open", hem=(5.0, 2.0))


@row
def ledge_getup_attack(i: int, n: int) -> Pose:
    wind = dict(HALF_UP, na=(-17.0, 4.0), nh="point", brows=-1.0)
    return keys(_shot(i, n), [(0.0, PERCH), (0.3, wind), (0.55, SWEEP_LOW), (0.75, SWEEP_LOW), (1.0, HALF_UP)])


@row
def climb(i: int, n: int) -> Pose:
    ph, s, c = _loop(i, n)
    return P(hip=(1.0, -1.0 + abs(s)), lean=3.0, head=(0.0, 0.0, -12.0), na=(25.0, -3.0 - 8.0 * c), fa=(21.0, -5.0 + 8.0 * c), arm="under",
             nh="fist", fh="fist", nf=(5.0, -6.0 + 6.0 * c, -14.0), ff=(7.0, -6.0 - 6.0 * c, -14.0), mouth="flat")


@row
def swim(i: int, n: int) -> Pose:
    ph, s, c = _loop(i, n)

    def stroke(p: float) -> Tuple[float, float]:
        a = math.radians(60.0 - 85.0 * math.cos(p))
        return (26.0 * math.sin(a), -26.0 * math.cos(a))

    return P(rot=62.0, off=(-4.0, -14.0 + 1.5 * s), lean=2.0, head=(0.0, 0.0, -44.0), na=stroke(ph), fa=stroke(ph + math.pi), arm="under", nh="flat",
             fh="flat", nf=(-4.0 + 5.0 * s, -1.0, 62.0), ff=(5.0 - 5.0 * s, -1.0, 62.0), mouth="o", hem=(2.0, 2.0))


@row
def float_glide(i: int, n: int) -> Pose:
    # His jacket is a wing: his arms are out, its tail is out behind him,
    # and he goes on thinking.
    _, s, c = _loop(i, n)
    return P(hip=(0.0, -2.0 + 1.2 * s), lean=20.0, head=(0.0, 0.0, -16.0), na=(-22.0, 1.0 + s), nab=-1.0, fa=(21.0, -3.0 - s), nh="open", fh="open",
             nf=(-11.0, -4.0 + c, 44.0), ff=(-3.0, -2.0 - c, 38.0), eyes="up", brows=1.0, hem=(8.0, 3.0))


@row
def block(i: int, n: int) -> Pose:
    # "Wait, wait": both his palms out.
    _, s, _c = _loop(i, n)
    return P(hip=(-2.0, 4.0 + 0.4 * s), lean=-8.0, head=(-1.0, 0.0, 6.0), na=(22.0, 3.0), fa=(19.0, -3.0), nh="open", fh="open",
             nf=(-7.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), brows=1.0, mouth="o")


STRUCK = P(hip=(-4.0, 2.0), lean=-22.0, head=(-2.0, 0.0, -12.0), na=(16.0, 2.0), fa=(19.0, -4.0), nh="open", fh="open", nf=(-8.0, 0.0, 0.0),
           ff=(8.0, -5.0, -22.0), eyes="wince", mouth="big", brows=1.0, off=(-3.0, 0.0), hem=(0.0, 5.0))


@row
def hit(i: int, n: int) -> Pose:
    back = P(hip=(-2.0, 2.0), lean=-6.0, na=(4.0, 22.0), fa=(7.0, 21.0), eyes="wince", mouth="grit")
    return keys(_shot(i, n), [(0.0, P(lean=-4.0, eyes="wide", mouth="o")), (0.25, STRUCK), (0.6, STRUCK), (1.0, back)])


#: Sitting on the ground, his legs out in front of him.
SAT = P(hip=(-8.0, 26.5), lean=-10.0, head=(0.0, 0.0, 4.0), na=(-8.0, 24.0), fa=(9.0, 23.0), nh="open", fh="open", nf=(19.0, 0.0, -62.0),
        ff=(25.0, 0.0, -66.0), eyes="closed", mouth="o", hem=(0.0, 2.0))
#: On his back, his head behind him and his toes up, his hands on his chest.
SUPINE = P(rot=-90.0, hip=(-2.0, 25.5), off=(13.0, 0.0), head=(0.0, 0.0, 0.0), na=(5.0, 13.0), fa=(2.0, 11.0), nh="flat", fh="flat",
           nf=(-4.5, 25.0, 0.0), ff=(4.5, 25.0, -10.0), eyes="closed", mouth="smile")


@row
def death(i: int, n: int) -> Pose:
    # He would say that he has left. He sits, and then he lies down with his
    # hands on his chest, and the proof is somebody else's now.
    sag = P(hip=(-5.0, 13.0), lean=-16.0, head=(-2.0, 0.0, -8.0), na=(7.0, 19.0), fa=(12.0, 15.0), nh="open", fh="open", nf=(-4.0, 0.0, 0.0),
            ff=(10.0, 0.0, -10.0), eyes="wince", mouth="o", off=(-3.0, 0.0), hem=(0.0, 3.0))
    return keys(_shot(i, n), [(0.0, STRUCK), (0.25, sag), (0.5, SAT), (0.75, SUPINE), (1.0, SUPINE)])


@row
def talk(i: int, n: int) -> Pose:
    # Both his open hands talk, one after the other.
    _, s, c = _loop(i, n)
    return P(hip=(0.0, 0.4 * s), head=(0.5, 0.0, 3.0 * s), na=(15.0 + 4.0 * c, 7.0 - 6.0 * max(0.0, s)), nh="open",
             fa=(17.0 - 3.0 * c, 9.0 + 5.0 * min(0.0, s)), fh="open", mouth=("open", "smile", "big", "smile")[i % 4], brows=1.0 if s > 0.3 else 0.0,
             eyes="happy" if i == n - 3 else "open")


@row
def interact(i: int, n: int) -> Pose:
    reach = P(hip=(1.5, 1.0), lean=9.0, head=(1.0, 0.0, 0.0), na=(26.0, -1.0), nh="point", fa=BEHIND, mouth="o", brows=1.0)
    return keys(_shot(i, n), [(0.0, P(fa=BEHIND)), (0.35, reach), (0.7, dict(reach, na=(26.0, 3.0))), (1.0, P(fa=BEHIND))])


#: He is not a fighter: the hand he argues with is up, and that is all.
GUARD = P(hip=(-1.0, 2.0), lean=2.0, na=(11.0, 8.0), fa=(13.0, 12.0), nh="point", fh="open", nf=(-7.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), brows=-1.0,
          mouth="flat")


@row
def jab(i: int, n: int) -> Pose:
    # A small point: an epsilon.
    poke = dict(GUARD, hip=(3.0, 3.0), lean=12.0, na=(27.0, 1.0), ff=(10.0, 0.0, 0.0), mouth="open")
    return keys(_shot(i, n), [(0.0, GUARD), (0.3, poke), (0.6, poke), (1.0, GUARD)])


@row
def punch(i: int, n: int) -> Pose:
    # Both his palms: the proof is done, and it is put in front of you.
    wind = dict(GUARD, hip=(-3.0, 3.0), lean=-8.0, na=(-2.0, 10.0), fa=(2.0, 12.0), nh="open", fh="open")
    push = dict(GUARD, hip=(5.0, 4.0), lean=16.0, na=(27.0, 2.0), nh="open", fa=(24.0, 6.0), fh="open", ff=(12.0, 0.0, 0.0), nf=(-9.0, 0.0, 12.0),
                mouth="big", brows=1.0, hem=(5.0, 1.0))
    return keys(_shot(i, n), [(0.0, GUARD), (0.25, wind), (0.5, push), (0.75, push), (1.0, GUARD)])


@row
def slash(i: int, n: int) -> Pose:
    # He writes a line across the air, from behind his head to the ground,
    # and there is a prime at the end of it.
    u = _shot(i, n)
    swing = ease(max(0.0, min(1.0, (u - 0.2) / 0.5)))
    a = math.radians(lerp(-138.0, 56.0, swing))
    hand = (27.0 * math.cos(a), 27.0 * math.sin(a))
    base = dict(GUARD, hip=(lerp(-2.0, 4.0, swing), 3.0), lean=lerp(-8.0, 18.0, swing), na=hand,
                nab=-1.0 if hand[1] < -6.0 and hand[0] < 6.0 else 1.0, arm="under" if hand[1] < -4.0 and hand[0] > -14.0 else "over",
                fa=(lerp(13.0, -9.0, swing), 12.0), ff=(lerp(7.0, 11.0, swing), 0.0, 0.0), mouth="open" if 0.2 < u < 0.8 else "flat",
                hem=(4.0 * swing, 1.0))
    if u > 0.85:
        return blend(base, GUARD, ease((u - 0.85) / 0.15))
    return base


@row
def attack_side(i: int, n: int) -> Pose:
    # A long step and his finger at the end of it: quod erat demonstrandum.
    wind = dict(GUARD, hip=(-4.0, 4.0), lean=-10.0, na=(-10.0, 4.0), fa=(-6.0, 12.0))
    lunge = dict(GUARD, hip=(7.0, 6.0), lean=20.0, na=(27.0, 0.0), fa=(-14.0, 8.0), nf=(-12.0, 0.0, 16.0), ff=(15.0, 0.0, 0.0), eyes="wide",
                 mouth="big", brows=1.0, hem=(6.0, 1.0))
    return keys(_shot(i, n), [(0.0, GUARD), (0.25, wind), (0.45, lunge), (0.8, lunge), (1.0, GUARD)])


UP = P(hip=(0.0, -1.0), lean=-6.0, head=(0.0, 0.0, -14.0), na=(4.0, -27.0), nab=-1.0, arm="under", nh="point", fa=(-8.0, 16.0), fh="open",
       nf=(-5.0, 0.0, 14.0), ff=(6.0, -1.0, 16.0), mouth="open", brows=1.0)


@row
def attack_up(i: int, n: int) -> Pose:
    # The primes go up, and they do not stop.
    low = dict(GUARD, hip=(0.0, 9.0), lean=12.0, na=(9.0, 19.0))
    return keys(_shot(i, n), [(0.0, GUARD), (0.25, low), (0.45, UP), (0.8, UP), (1.0, GUARD)])


@row
def attack_down(i: int, n: int) -> Pose:
    # He puts the whole graph on the floor.
    high = dict(GUARD, hip=(-1.0, 0.0), lean=-9.0, head=(0.0, 0.0, -8.0), na=(2.0, -26.0), nab=-1.0, arm="under", nh="open", fa=(8.0, -24.0),
                fab=-1.0, fh="open")
    slam = dict(GUARD, hip=(3.0, 11.0), lean=28.0, head=(1.0, 0.0, -10.0), na=(17.0, 21.0), nh="open", fa=(20.0, 19.0), fh="open",
                nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), mouth="big", hem=(4.0, 2.0))
    return keys(_shot(i, n), [(0.0, GUARD), (0.3, high), (0.5, slam), (0.85, slam), (1.0, HALF_UP)])


AIR = P(hip=(0.0, -3.0), nf=(-4.0, -8.0, 20.0), ff=(6.0, -12.0, 8.0), na=(11.0, 8.0), fa=(13.0, 12.0), nh="point", fh="open", brows=-1.0,
        mouth="flat", hem=(3.0, 2.0))


@row
def air_neutral(i: int, n: int) -> Pose:
    # His arms out, and the primes go around him.
    _, s, _c = _loop(i, n)
    return dict(AIR, lean=6.0 * s, na=(-21.0, -5.0 + 2.0 * s), nab=-1.0, fa=(22.0, -7.0 - 2.0 * s), nh="open", fh="open", eyes="happy", mouth="open")


@row
def air_forward(i: int, n: int) -> Pose:
    poke = dict(AIR, lean=14.0, hip=(1.0, -3.0), na=(27.0, 3.0), fa=(-14.0, 6.0), nf=(-11.0, -6.0, 40.0), ff=(-2.0, -12.0, 30.0), mouth="open",
                hem=(6.0, 0.0))
    return keys(_shot(i, n), [(0.0, AIR), (0.35, poke), (0.7, poke), (1.0, AIR)])


@row
def air_back(i: int, n: int) -> Pose:
    # He does not look: a sandal goes out behind him.
    kick = dict(AIR, lean=26.0, head=(0.0, 0.0, -22.0), leg="over", nf=(-32.0, -32.0, 96.0), ff=(7.0, -16.0, 0.0), na=(15.0, 12.0), fa=(18.0, 6.0),
                nh="open", mouth="open", hem=(6.0, 0.0))
    return keys(_shot(i, n), [(0.0, AIR), (0.35, kick), (0.7, kick), (1.0, AIR)])


@row
def air_down(i: int, n: int) -> Pose:
    dive = dict(AIR, hip=(0.0, 0.0), off=(0.0, -13.0), nf=(-1.5, 0.0, 58.0), ff=(3.0, 0.0, 52.0), na=(-14.0, -22.0), nab=-1.0, fa=(17.0, -20.0),
                nh="open", fh="open", mouth="open", hem=(4.0, 4.0))
    return keys(_shot(i, n), [(0.0, AIR), (0.3, dive), (0.8, dive), (1.0, AIR)])


@row
def air_up(i: int, n: int) -> Pose:
    reach = dict(UP, hip=(0.0, -3.0), nf=(-6.0, -2.0, 36.0), ff=(4.0, -8.0, 22.0), hem=(2.0, 2.0))
    return keys(_shot(i, n), [(0.0, AIR), (0.3, reach), (0.75, reach), (1.0, AIR)])


#: He counts on his fingers, his eyes shut.
CHARGE = P(hip=(0.0, 1.0), lean=5.0, head=(0.0, 0.0, 8.0), na=(13.0, 7.0), fa=(14.0, 4.0), nh="point", fh="open", eyes="closed", mouth="flat")


@row
def charge(i: int, n: int) -> Pose:
    # A graph comes together over his head, a point and a line at a time.
    _, s, _c = _loop(i, n)
    return dict(CHARGE, hip=(0.0, 1.0 + 0.5 * s), na=(13.0, 7.0 - 2.0 * (i % 2)), head=(0.0, 0.3 * s, 8.0 + 1.5 * s))


@row
def cast(i: int, n: int) -> Pose:
    # And he gives it away.
    out = P(hip=(3.0, 3.0), lean=12.0, head=(1.0, 0.0, -6.0), na=(26.0, -2.0), fa=(23.0, 5.0), nh="open", fh="open", nf=(-9.0, 0.0, 10.0),
            ff=(10.0, 0.0, 0.0), eyes="wide", mouth="big", brows=1.0, hem=(6.0, 1.0))
    return keys(_shot(i, n), [(0.0, CHARGE), (0.3, out), (1.0, dict(out, hip=(2.0, 3.0), lean=9.0))])


@row
def celebrate(i: int, n: int) -> Pose:
    # A proof from the Book: both his hands up, and he does not stay on the
    # ground.
    ph, s, _c = _loop(i, n)
    up = abs(math.sin(ph))
    return P(off=(0.0, -8.0 * up), hip=(0.0, 3.0 * (1.0 - up)), lean=-3.0, head=(0.0, 0.0, -8.0), na=(-13.0, -23.0 + 2.0 * s), nab=-1.0,
             fa=(18.0, -21.0 - 2.0 * s), nh="open", fh="open", nf=(-6.0, -4.0 * up, 24.0 * up), ff=(7.0, -6.0 * up, 14.0 * up), eyes="happy",
             mouth="big", brows=1.0, hem=(3.0 * up, 3.0 * up))


@row
def taunt(i: int, n: int) -> Pose:
    # Coffee goes in. A theorem will come out.
    held = P(na=(16.0, 9.0), nh="fist", fa=BEHIND)
    sip = dict(held, lean=-4.0, head=(0.0, 0.0, -12.0), na=(13.5, -2.5), eyes="closed", mouth="flat")
    after = dict(held, eyes="happy", mouth="big", brows=1.0)
    return keys(_shot(i, n), [(0.0, held), (0.3, sip), (0.6, sip), (0.8, after), (1.0, after)])


# name, frames, duration_ms. The rows of the main game.
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 150),
    ("walk", 8, 96),
    ("run", 8, 74),
    ("crouch", 6, 95),
    ("crouch_walk", 8, 88),
    ("jump", 6, 95),
    ("fall", 6, 95),
    ("land_hard", 8, 95),
    ("land_recovery", 6, 75),
    ("dash_startup", 4, 50),
    ("dash", 6, 65),
    ("slide", 6, 70),
    ("roll", 8, 58),
    ("wall_grab", 6, 110),
    ("wall_jump", 6, 85),
    ("ledge_grab", 6, 100),
    ("ledge_climb", 6, 100),
    ("ledge_getup", 6, 40),
    ("ledge_roll", 8, 37),
    ("ledge_getup_attack", 8, 37),
    ("climb", 8, 100),
    ("swim", 8, 105),
    ("float_glide", 8, 110),
    ("block", 6, 85),
    ("hit", 5, 90),
    ("death", 8, 120),
    ("talk", 8, 104),
    ("interact", 8, 92),
    ("jab", 5, 58),
    ("punch", 7, 72),
    ("slash", 8, 75),
    ("attack_side", 8, 65),
    ("attack_up", 8, 65),
    ("attack_down", 8, 65),
    ("air_neutral", 8, 60),
    ("air_forward", 7, 62),
    ("air_back", 7, 62),
    ("air_down", 7, 70),
    ("air_up", 7, 62),
    ("charge", 8, 90),
    ("cast", 8, 80),
    ("celebrate", 8, 92),
    ("taunt", 8, 120),
]
assert [name for name, _, _ in ROWS] == list(ROW_POSES), "every row has a pose, in sheet order"


# ---- The pieces --------------------------------------------------------------


def _bone(tag: str, length: float, w0: float, w1: float, colour: RGBA, dark: RGBA, edge: bool):
    """A limb bone along +x from ``home``, ``w0`` wide at its root and ``w1``
    at its end. ``edge``: with its outline (a limb is placed twice, every
    bone's outline and then every bone, so a joint has no line through it)."""
    h = K.home

    def shape(d) -> None:
        K.poly(d, [K.at(0.0, -w0 / 2.0), K.at(length, -w1 / 2.0), K.at(length, w1 / 2.0), K.at(0.0, w0 / 2.0)], WHITE)
        K.oval(d, h, w0 / 2.0, w0 / 2.0, WHITE)
        K.oval(d, K.at(length, 0.0), w1 / 2.0, w1 / 2.0, WHITE)

    return K.solid(("bone", tag, length, w0, w1, colour, edge), shape, colour, None, outline=1.2 if edge else 0.0, rim=0.0, shade=0.0,
                   shade_colour=dark)


def _patch():
    """The patch on the elbow of his jacket, along his forearm from his elbow."""

    def shape(d) -> None:
        K.oval(d, K.at(1.6, 1.0), 3.6, 2.5, WHITE)

    return K.solid(("patch",), shape, PATCH, None, outline=0.5, rim=0.2, shade=0.3, shade_colour=SANDAL_DARK)


def _hand(mode: str, near: bool):
    """A hand along +x from its wrist at ``home``, with the cuff of his shirt.
    His hands are large: he talks with them."""
    skin = SKIN if near else SKIN_SHADE
    h = K.home

    def shape(d) -> None:
        K.rrect(d, h[0] - 2.4, h[1] - 3.6, h[0] + 1.4, h[1] + 3.6, 1.2, WHITE)
        if mode == "flat":
            K.oval(d, K.at(5.6, 0.0), 5.6, 2.8, WHITE)
        elif mode == "fist":
            K.oval(d, K.at(3.8, 0.0), 3.9, 3.7, WHITE)
        else:
            K.oval(d, K.at(3.8, 0.0), 4.0, 3.4, WHITE)
        if mode == "soft":
            K.stroke(d, [K.at(3.2, -2.0), K.at(5.8, -3.8)], WHITE, 2.2)
            K.stroke(d, [K.at(5.0, 0.6), K.at(8.4, 1.4)], WHITE, 2.6)
        elif mode == "point":
            K.stroke(d, [K.at(4.6, -0.8), K.at(11.6, -1.6)], WHITE, 2.3)
            K.stroke(d, [K.at(3.0, 2.0), K.at(5.2, 3.8)], WHITE, 2.1)
        elif mode == "open":
            for dy, reach in ((-3.3, 9.0), (-1.1, 10.6), (1.1, 10.4), (3.2, 8.8)):
                K.stroke(d, [K.at(4.6, dy * 0.6), K.at(reach, dy * 1.3)], WHITE, 2.0)
            K.stroke(d, [K.at(2.6, -2.4), K.at(4.6, -6.0)], WHITE, 2.1)

    def detail(d) -> None:
        K.rrect(d, h[0] - 3.0, h[1] - 4.2, h[0] + 1.2, h[1] + 4.2, 0.0, SHIRT if near else SHIRT_DARK)
        if mode == "fist":
            K.line(d, [K.at(4.6, -2.0), K.at(5.8, 0.0), K.at(4.6, 2.0)], SKIN_DEEP, 0.6)
        if mode == "open":
            for dy in (-1.0, 1.0):
                K.line(d, [K.at(5.4, dy * 0.9), K.at(8.0, dy * 1.5)], SKIN_DEEP, 0.4)

    return K.solid(("hand", mode, near), shape, skin, detail, outline=1.1, rim=0.3, shade=0.3, shade_colour=SKIN_DEEP)


def _sandal(near: bool):
    """A foot in its sock and its sandal, from its ankle at ``home``; its
    sole is ``ANKLE_UP`` under it."""
    h = K.home

    def shape(d) -> None:
        K.oval(d, K.at(3.0, 0.6), 6.2, 3.0, WHITE)
        K.rrect(d, h[0] - 3.4, h[1] - 0.2, h[0] + 9.6, h[1] + ANKLE_UP + 0.4, 1.4, WHITE)
        K.oval(d, h, 3.0, 2.9, WHITE)

    def detail(d) -> None:
        K.rrect(d, h[0] - 5.0, h[1] + ANKLE_UP - 0.9, h[0] + 11.0, h[1] + ANKLE_UP + 2.0, 0.0, SANDAL_DARK)
        # Two straps, and the one at the back of his heel.
        for x0, x1 in ((4.6, 6.6), (0.6, 2.4)):
            K.poly(d, [K.at(x0, -4.0), K.at(x1, -4.0), K.at(x1 + 1.0, ANKLE_UP), K.at(x0 + 1.0, ANKLE_UP)], SANDAL)
        K.poly(d, [K.at(-4.0, -0.6), K.at(1.0, 0.4), K.at(1.4, 2.0), K.at(-4.0, 1.0)], SANDAL)

    return K.solid(("sandal", near), shape, SOCK_FILL if near else mix(SOCK_FILL, SOCK_DARK, 0.7), detail, outline=1.2, rim=0.25, shade=0.3,
                   shade_colour=SOCK_DARK)


def _jacket(hem_back: int, hem_front: int):
    """His jacket from his hips at ``home``, his spine up: it hangs open on
    his cardigan and his shirt, and its back is round. The hem is
    ``hem_back`` and ``hem_front`` wider than it hangs."""
    hb, hf = float(hem_back), float(hem_front)
    back_hem, front_hem = K.at(-10.6 - hb, 8.4 - hb * 0.25), K.at(11.4 + hf, 7.6)
    #: The near edge of the jacket, where it hangs open.
    edge_top, edge_low = K.at(3.6, -34.0), K.at(5.4 + hf * 0.5, 8.0)

    def shape(d) -> None:
        K.poly(d, [K.at(-1.6, -38.0), K.at(-8.4, -35.0), K.at(-11.2, -28.0), K.at(-10.8, -17.0), K.at(-9.0, -4.0), back_hem, front_hem,
                   K.at(10.6, -4.0), K.at(11.2, -18.0), K.at(11.8, -29.0), K.at(8.4, -36.4)], WHITE)
        K.oval(d, K.at(-5.6, -30.6), 6.0, 6.6, WHITE)
        K.oval(d, K.at(7.4, -30.4), 5.4, 6.0, WHITE)

    def detail(d) -> None:
        # What his jacket hangs open on: his cardigan, and his shirt over it.
        K.poly(d, [edge_top, K.at(12.0, -34.0), K.at(12.6 + hf, 12.0), (edge_low[0], edge_low[1] + 4.0), K.at(4.6, -12.0)], CARDIGAN)
        K.poly(d, [K.at(9.6, -34.0), K.at(13.0, -34.0), K.at(13.0 + hf, 12.0), K.at(10.4 + hf, 12.0)], TWEED_DARK)
        K.line(d, [K.at(9.6, -31.0), K.at(10.0, -10.0), K.at(10.4 + hf, 9.0)], CARDIGAN_DARK, 0.7)
        K.poly(d, [K.at(2.8, -39.0), K.at(9.0, -39.0), K.at(7.2, -26.5)], SHIRT)
        K.poly(d, [K.at(4.4, -39.0), K.at(7.6, -39.0), K.at(6.2, -32.6)], SKIN_SHADE)
        for k in range(4):
            t = k / 3.0
            K.oval(d, K.at(lerp(7.6, 8.2, t), lerp(-23.0, 2.0, t)), 0.9, 0.9, CARDIGAN_DARK)
        # Its near lapel, and the line of the edge under it.
        K.poly(d, [K.at(-0.4, -38.0), edge_top, K.at(4.6, -20.0), K.at(0.6, -27.0)], TWEED_LIGHT)
        K.line(d, [K.at(0.6, -27.0), K.at(4.6, -20.0), K.at(4.6, -12.0), edge_low], TWEED_DARK, 0.7)
        # The pocket on his chest: a stick of chalk and two pens.
        K.line(d, [K.at(-7.4, -21.6), K.at(-2.2, -21.0)], TWEED_DARK, 0.7)
        K.rrect(d, K.home[0] - 6.8, K.home[1] - 25.0, K.home[0] - 5.2, K.home[1] - 21.6, 0.3, CHALK)
        K.line(d, [K.at(-4.2, -24.4), K.at(-4.1, -21.6)], CHALK_BLUE, 0.8)
        K.line(d, [K.at(-3.0, -24.0), K.at(-2.9, -21.4)], CARDIGAN, 0.8)
        # A pocket low on its side, and the round of his back.
        K.line(d, [K.at(-7.6, -3.4), K.at(-1.4, -2.6)], TWEED_DARK, 0.7)
        K.line(d, [K.at(-9.4, -30.0), K.at(-9.8, -22.0), K.at(-9.2, -14.0)], TWEED_LIGHT, 0.6)

    return K.solid(("jacket", hem_back, hem_front), shape, TWEED, detail, outline=1.3, rim=0.3, shade=0.4, shade_colour=TWEED_DARK)


def _neck(length: float):
    """His neck, along +x from its base."""

    def shape(d) -> None:
        K.poly(d, [K.at(-1.0, -2.6), K.at(length, -2.4), K.at(length, 2.4), K.at(-1.0, 2.8)], WHITE)

    return K.solid(("neck", length), shape, SKIN_SHADE, None, outline=1.1, rim=0.0, shade=0.0)


def _collar():
    """The collar of his shirt, from the base of his neck: open, no tie, and
    its two points out over his lapels. His throat shows between them."""

    def shape(d) -> None:
        K.poly(d, [K.at(-2.2, -1.4), K.at(1.6, -0.6), K.at(0.6, 5.0), K.at(-4.8, 2.6)], WHITE)
        K.poly(d, [K.at(3.6, -0.8), K.at(5.6, -1.4), K.at(7.6, 2.8), K.at(4.4, 4.6)], WHITE)

    return K.solid(("collar",), shape, SHIRT, None, outline=1.0, rim=0.0, shade=0.3, shade_colour=SHIRT_DARK)


NEAR_EYE: Point = (1.2, 0.0)
FAR_EYE: Point = (7.3, -0.2)
#: Half the width and half the height of each lens: his glasses are large.
NEAR_LENS: Point = (3.5, 3.0)
FAR_LENS: Point = (1.9, 2.8)


def _head():
    """His head, from its middle: a long skull, a thin jaw, a large ear, and
    grey hair on top of it that is not combed."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, -2.4), 8.0, 9.0, WHITE)
        K.oval(d, K.at(2.6, 4.2), 5.6, 7.6, WHITE)
        # His hair: all of the top of his head, higher at the front, and it
        # stands up where he has had his hand in it.
        K.oval(d, K.at(-0.6, -8.4), 8.6, 5.0, WHITE)
        K.poly(d, [K.at(-6.6, -11.0), K.at(-5.6, -15.2), K.at(-3.4, -13.2), K.at(-1.4, -15.8), K.at(0.8, -13.4), K.at(3.4, -15.4),
                   K.at(5.2, -12.8), K.at(8.4, -12.6), K.at(8.0, -8.0), K.at(-6.0, -6.0)], WHITE)
        K.poly(d, [K.at(-7.0, -4.0), K.at(-10.0, -3.4), K.at(-8.0, -0.6), K.at(-9.6, 2.2), K.at(-7.0, 2.6), K.at(-7.4, 5.8), K.at(-4.6, 6.0)], WHITE)
        # His nose: long.
        K.poly(d, [K.at(7.0, -1.0), K.at(10.8, 3.2), K.at(10.2, 4.8), K.at(7.0, 5.4)], WHITE)
        K.oval(d, K.at(9.5, 3.9), 1.7, 1.6, WHITE)

    def detail(d) -> None:
        # The far side of his face is in shade, and his cheek is hollow.
        K.oval(d, K.at(8.6, 8.0), 2.2, 4.0, mix(SKIN, SKIN_SHADE, 0.7))
        K.poly(d, [K.at(-1.6, 3.6), K.at(2.0, 4.6), K.at(1.4, 9.4), K.at(-1.8, 8.0)], mix(SKIN, SKIN_SHADE, 0.55))
        # His hair, down to its line: high over his forehead, back at his
        # temple, down in front of his ear and round behind it to his neck.
        K.poly(d, [K.at(20.0, -8.4), K.at(8.0, -8.4), K.at(5.0, -9.2), K.at(2.0, -8.4), K.at(0.0, -6.6), K.at(-2.2, -6.0), K.at(-3.2, -3.0),
                   K.at(-3.6, -1.4), K.at(-6.2, -1.6), K.at(-7.0, 3.4), K.at(-5.2, 4.6), K.at(-4.4, 7.4), K.at(-20.0, 7.4), K.at(-20.0, -26.0),
                   K.at(20.0, -26.0)], HAIR)
        for strand in ([(6.6, -9.6), (3.4, -12.6), (0.6, -12.8)], [(3.0, -9.4), (-0.6, -11.6), (-4.0, -11.0)], [(-0.8, -7.6), (-4.4, -8.4), (-6.8, -6.6)],
                       [(-4.2, -13.6), (-3.6, -11.6)], [(1.6, -14.0), (1.0, -12.4)]):
            K.line(d, [K.at(x, y) for x, y in strand], HAIR_LIGHT, 0.6)
        for strand in ([(-4.4, -4.6), (-7.4, -3.4), (-8.6, -1.6)], [(-6.6, 2.4), (-7.6, 4.2)], [(7.6, -9.4), (7.8, -11.6)]):
            K.line(d, [K.at(x, y) for x, y in strand], HAIR_SHADE, 0.6)
        # The lines of his forehead.
        crease = mix(SKIN, SKIN_DEEP, 0.55)
        K.line(d, [K.at(2.6, -6.6), K.at(5.0, -7.0), K.at(7.2, -6.6)], crease, 0.45)
        # His ear, over his hair: large.
        K.oval(d, K.at(-5.0, 1.2), 2.5, 3.7, SKIN, OUTLINE, 0.6)
        K.line(d, [K.at(-5.6, -0.6), K.at(-4.4, 1.2), K.at(-5.2, 2.8)], SKIN_DEEP, 0.45)
        # What his lenses do to the light.
        for (cx, cy), (rx, ry) in ((NEAR_EYE, NEAR_LENS), (FAR_EYE, FAR_LENS)):
            K.rrect(d, K.home[0] + cx - rx, K.home[1] + cy - ry, K.home[0] + cx + rx, K.home[1] + cy + ry, 0.9, LENS)
        # Under his nose, and the deep line from it down past his mouth.
        K.line(d, [K.at(9.0, 5.6), K.at(7.0, 5.6), K.at(6.2, 4.6)], SKIN_DEEP, 0.7)
        K.line(d, [K.at(5.2, 4.2), K.at(2.8, 6.4), K.at(2.4, 9.2)], SKIN_DEEP, 0.6)
        K.line(d, [K.at(-1.0, 8.4), K.at(1.2, 11.0), K.at(4.0, 11.6)], mix(SKIN, SKIN_DEEP, 0.55), 0.6)

    return K.solid(("head",), shape, SKIN, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=SKIN_DEEP)


def _eyes(mode: str):
    """His eyes are small behind his lenses."""

    def paint(d) -> None:
        for (ex, ey), r in ((NEAR_EYE, 1.0), (FAR_EYE, 0.85)):
            c = K.at(ex + 0.4, ey + 0.4)
            w = r + 0.9
            if mode == "closed":
                K.line(d, [(c[0] - w, c[1] - 0.1), (c[0], c[1] + 0.8), (c[0] + w, c[1] - 0.1)], INK, 0.8)
                continue
            if mode == "happy":
                K.line(d, [(c[0] - w, c[1] + 0.6), (c[0], c[1] - 0.9), (c[0] + w, c[1] + 0.6)], INK, 0.9)
                continue
            if mode == "wince":
                side = 1.0 if ex < 3.0 else -1.0
                K.line(d, [(c[0] - w * side, c[1] - 1.2), (c[0] + w * 0.6 * side, c[1]), (c[0] - w * side, c[1] + 1.2)], INK, 0.8)
                continue
            if mode == "wide":
                K.oval(d, c, r + 0.9, r + 1.0, WHITE)
            at = (c[0], c[1] - (0.9 if mode == "up" else 0.0))
            K.oval(d, at, r, r * 1.1, INK)
            K.oval(d, (at[0] - 0.35, at[1] - 0.4), 0.3, 0.3, WHITE)
            if mode != "wide":
                # His lid: he is old, and it is heavy.
                K.line(d, [(c[0] - w, c[1] - 0.6), (c[0] - 0.2, c[1] - 1.5), (c[0] + w, c[1] - 0.9)], SKIN_DEEP, 0.5)

    return K.piece(("eyes", mode), paint)


def _glasses():
    """His glasses, from the middle of his head: large, square and black."""

    def paint(d) -> None:
        h = K.home
        for (cx, cy), (rx, ry) in ((NEAR_EYE, NEAR_LENS), (FAR_EYE, FAR_LENS)):
            K.rrect(d, h[0] + cx - rx, h[1] + cy - ry, h[0] + cx + rx, h[1] + cy + ry, 0.9, None, FRAME, 0.9)  # type: ignore[arg-type]
            # The top of a frame is the heavy part.
            K.line(d, [(h[0] + cx - rx, h[1] + cy - ry + 0.3), (h[0] + cx + rx, h[1] + cy - ry + 0.3)], FRAME, 1.4)
        K.line(d, [K.at(NEAR_EYE[0] + NEAR_LENS[0], -1.9), K.at(FAR_EYE[0] - FAR_LENS[0], -2.0)], FRAME, 1.0)
        K.line(d, [K.at(NEAR_EYE[0] - NEAR_LENS[0], -2.0), K.at(-4.8, -1.2)], FRAME, 1.0)

    return K.piece(("glasses",), paint)


def _brows(mood: int):
    """His brows, over his frames: 0 level, 1 raised, -1 set."""

    def paint(d) -> None:
        up = -1.1 if mood > 0 else 0.0
        inner = 0.9 if mood < 0 else 0.0
        K.stroke(d, [K.at(-1.4, -4.2 + up), K.at(1.4, -5.0 + up), K.at(4.2, -4.4 + up + inner)], HAIR_SHADE, 1.1)
        K.stroke(d, [K.at(6.0, -4.6 + up + inner), K.at(7.4, -5.0 + up), K.at(8.8, -4.4 + up)], HAIR_SHADE, 1.0)

    return K.piece(("brows", mood), paint)


def _mouth(mode: str):
    c = K.at(5.4, 8.2)

    def paint(d) -> None:
        if mode == "smile":
            K.line(d, [(c[0] - 2.8, c[1] - 0.5), (c[0] - 0.2, c[1] + 0.6), (c[0] + 2.4, c[1] - 0.7)], MOUTH, 0.8)
        elif mode == "flat":
            K.line(d, [(c[0] - 2.2, c[1]), (c[0] + 2.0, c[1] - 0.1)], MOUTH, 0.8)
        elif mode == "o":
            K.oval(d, c, 1.1, 1.3, MOUTH, INK, 0.4)
        elif mode == "grit":
            K.rrect(d, c[0] - 2.4, c[1] - 1.0, c[0] + 2.2, c[1] + 1.0, 0.7, TEETH, INK, 0.5)
            K.line(d, [(c[0], c[1] - 0.9), (c[0], c[1] + 0.9)], INK, 0.3)
        else:
            ry = 2.1 if mode == "big" else 1.3
            K.oval(d, (c[0], c[1] + 0.3), 2.3 if mode == "big" else 1.8, ry, MOUTH, INK, 0.5)
            K.oval(d, (c[0], c[1] + 0.3 + ry * 0.5), 1.2, ry * 0.4, TONGUE)

    return K.piece(("mouth", mode), paint)


# ---- His mathematics ---------------------------------------------------------


def _chalk(key: tuple, shape: Callable, fill: RGBA = CHALK):
    return K.solid(("chalk",) + key, shape, fill, None, outline=1.1, rim=0.0, shade=0.5, shade_colour=CHALK_DARK)


#: A digit, as a line in a box one wide and one high.
DIGITS: Dict[str, Tuple[Point, ...]] = {
    "1": ((0.25, 0.25), (0.6, 0.0), (0.6, 1.0)),
    "2": ((0.05, 0.22), (0.35, 0.0), (0.8, 0.05), (0.95, 0.3), (0.6, 0.6), (0.05, 1.0), (1.0, 1.0)),
    "3": ((0.05, 0.1), (0.5, 0.0), (0.95, 0.2), (0.5, 0.48), (0.95, 0.75), (0.5, 1.0), (0.05, 0.9)),
    "5": ((0.95, 0.0), (0.15, 0.0), (0.05, 0.45), (0.6, 0.4), (0.95, 0.66), (0.7, 1.0), (0.05, 0.94)),
    "7": ((0.05, 0.0), (0.95, 0.0), (0.4, 1.0)),
}


def _prime(text: str, size: float, fill: RGBA = CHALK):
    """A prime, written in chalk ``size`` high, its middle at ``home``."""
    wide, gap = size * 0.56, size * 0.3
    total = len(text) * wide + (len(text) - 1) * gap

    def shape(d) -> None:
        for k, ch in enumerate(text):
            x0 = -total / 2.0 + k * (wide + gap)
            K.stroke(d, [K.at(x0 + x * wide, (y - 0.5) * size) for x, y in DIGITS[ch]], WHITE, max(1.4, size * 0.2))

    return _chalk(("prime", text, size, fill), shape, fill)


def _epsilon(size: float):
    """His word for something small."""

    def shape(d) -> None:
        pts = ((1.0, 0.15), (0.5, 0.0), (0.1, 0.22), (0.5, 0.5), (0.05, 0.78), (0.5, 1.0), (1.0, 0.85))
        K.stroke(d, [K.at((x - 0.5) * size * 0.8, (y - 0.5) * size) for x, y in pts], WHITE, max(1.4, size * 0.22))

    return _chalk(("epsilon", size), shape, CHALK_BLUE)


def _qed(size: float):
    """The black square that ends a proof, in chalk."""

    def shape(d) -> None:
        K.rrect(d, K.home[0] - size * 0.42, K.home[1] - size / 2.0, K.home[0] + size * 0.42, K.home[1] + size / 2.0, 0.6, WHITE)

    return _chalk(("qed", size), shape, CHALK_GOLD)


def _burst(size: float):
    """The lines that fly out of a proof that is done."""

    def shape(d) -> None:
        for k in range(8):
            a = math.radians(k * 45.0 + 22.5)
            K.stroke(d, [K.at(math.cos(a) * size * 0.62, math.sin(a) * size * 0.62), K.at(math.cos(a) * size, math.sin(a) * size)], WHITE, 1.5)

    return _chalk(("burst", size), shape)


def _swoosh(radius: float, a0: int, a1: int, width: float):
    """The line of chalk a sweep leaves, about ``home``: from ``a0``, where it
    is thin, to ``a1``, where it is ``width``."""

    def shape(d) -> None:
        steps = max(4, abs(a1 - a0) // 5)
        outer, inner = [], []
        for k in range(steps + 1):
            t = k / steps
            a = math.radians(lerp(a0, a1, t))
            outer.append(K.at(radius * math.cos(a), radius * math.sin(a)))
            inner.append(K.at((radius - width * t) * math.cos(a), (radius - width * t) * math.sin(a)))
        K.poly(d, outer + inner[::-1], WHITE)

    return _chalk(("swoosh", radius, a0, a1, width), shape)


def _tick(size: float):
    return _chalk(("tick", size), lambda d: K.tick(d, K.home, size, WHITE, max(1.4, size * 0.4)), CHALK_GOLD)


def _dust(radius: float):
    """A bit of chalk dust."""
    return K.solid(("dust", radius), lambda d: K.oval(d, K.home, radius, radius, WHITE), CHALK, None, outline=0.8, rim=0.0, shade=0.4,
                   shade_colour=CHALK_DARK)


#: The points of his graph, in a box 2 wide and 2 high about its middle, and
#: its lines in the order they are drawn: a line is drawn when both its points
#: are there.
GRAPH_POINTS: Tuple[Point, ...] = ((0.0, 0.0), (-0.8, -0.5), (0.7, -0.7), (0.9, 0.3), (-0.2, 0.9), (-1.0, 0.5), (0.1, -1.0))
GRAPH_LINES: Tuple[Tuple[int, int], ...] = ((0, 1), (0, 2), (1, 2), (0, 3), (2, 3), (0, 4), (3, 4), (0, 5), (4, 5), (1, 5), (0, 6), (2, 6), (1, 6))
GRAPH_COLOURS: Tuple[RGBA, ...] = (CHALK_GOLD, CHALK, CHALK_BLUE, CHALK_PINK, CHALK, CHALK_BLUE, CHALK_PINK)


def _graph(count: int, size: int, spread: int = 0):
    """His graph with its first ``count`` points, ``size`` from its middle to
    its edge, and thrown ``spread`` wider toward +x.

    One piece, cut and placed on whole frame pixels (``Kit.aligned``): its
    lines are thin, and a thin line does not survive being turned."""

    def where(k: int) -> Point:
        x, y = GRAPH_POINTS[k]
        return K.at(x * size + (x + 1.0) * spread * 0.5, y * size)

    def paint(d) -> None:
        lines = [(a, b) for a, b in GRAPH_LINES if a < count and b < count]
        for a, b in lines:
            K.stroke(d, [where(a), where(b)], OUTLINE, 2.6)
        for k in range(count):
            K.oval(d, where(k), 3.3 if k == 0 else 2.7, 3.3 if k == 0 else 2.7, OUTLINE)
        for a, b in lines:
            K.stroke(d, [where(a), where(b)], CHALK, 1.0)
        for k in range(count):
            K.oval(d, where(k), 2.3 if k == 0 else 1.7, 2.3 if k == 0 else 1.7, GRAPH_COLOURS[k])

    return K.aligned(("graph", count, size, spread), paint)


def _cup():
    """His cup of coffee, held by its handle: ``home`` is his hand."""

    def shape(d) -> None:
        K.rrect(d, K.home[0] + 1.0, K.home[1] - 6.0, K.home[0] + 9.4, K.home[1] + 3.6, 1.6, WHITE)
        K.oval(d, K.at(0.6, -1.2), 2.6, 3.0, WHITE)

    def detail(d) -> None:
        K.oval(d, K.at(5.2, -5.6), 3.6, 1.2, COFFEE)
        K.line(d, [K.at(2.0, 0.6), K.at(8.6, 0.6)], CHALK_BLUE, 0.9)

    return K.solid(("cup",), shape, CUP, detail, outline=1.1, rim=0.3, shade=0.4, shade_colour=CUP_DARK)


def _steam(phase: int):
    """What comes off his coffee."""

    def paint(d) -> None:
        for x, lead in ((0.0, 0.0), (3.4, 1.6)):
            pts = [K.at(x + 1.3 * math.sin(lead + phase * 1.57 + t * 1.3), -t * 2.0) for t in range(5)]
            K.line(d, pts, (250, 250, 250, 170), 0.9)

    return K.piece(("steam", phase), paint)


Stamp = Tuple[object, Point, str, float]

#: The primes, in the order he says them.
PRIMES: Tuple[str, ...] = ("2", "3", "5", "7", "11", "13")


def _effects(anim: str, i: int, n: int, at: Dict[str, Point]) -> List[Stamp]:
    """What his mathematics draws this frame, over him."""
    out: List[Stamp] = []
    u = _shot(i, n)
    ph = math.tau * i / max(1, n)
    hand, far_hand, head, hip, foot, shoulder = at["hand"], at["far_hand"], at["head"], at["hip"], at["foot"], at["shoulder"]

    def stamp(part, p: Point, name: str, degrees: float = 0.0) -> None:
        out.append((part, p, name, degrees))

    def dust(points: List[Tuple[float, float, float]], origin: Point) -> None:
        for k, (x, y, r) in enumerate(points):
            size = r * (0.5 + 0.5 * math.sin(ph + k * 2.1) ** 2)
            stamp(_dust(round(size * 2.0) / 2.0 + 0.5), (origin[0] + x, origin[1] + y), f"dust_{k}")

    def graph(count: int, size: int, centre: Point, spread: int = 0) -> None:
        stamp(_graph(count, size, spread), pin(centre), "graph")

    if anim == "jab" and 1 <= i <= 3:
        stamp(_epsilon(8.0), (hand[0] + 19.0, hand[1] - 2.0), "epsilon")
        stamp(_dust(1.5), (hand[0] + 27.0, hand[1] - 9.0), "dust_0")
    elif anim == "punch" and 3 <= i <= 5:
        grow = float(i - 3)
        centre = (hand[0] + 18.0, hand[1] - 1.0)
        stamp(_burst(9.0 + 2.0 * grow), centre, "burst")
        stamp(_qed(7.0 + grow), centre, "qed")
    elif anim in ("slash", "ledge_getup_attack"):
        lo, hi = (2, 5) if anim == "slash" else (4, 6)
        if lo <= i <= hi:
            a = math.degrees(math.atan2(hand[1] - shoulder[1], hand[0] - shoulder[0]))
            lead = int(round(a / 5.0)) * 5
            sweep = 100 if anim == "slash" else 60
            stamp(_swoosh(50.0, lead - sweep, lead + 6, 9.0), shoulder, "swoosh")
            tip = math.radians(lead + 13.0)
            stamp(_prime(PRIMES[min(5, i)], 9.0, CHALK_GOLD), (shoulder[0] + 55.0 * math.cos(tip), shoulder[1] + 55.0 * math.sin(tip)), "prime")
    elif anim == "attack_side" and 3 <= i <= 6:
        grow = float(i - 3)
        centre = (hand[0] + 20.0 + 2.0 * grow, hand[1])
        stamp(_burst(10.0 + 2.0 * grow), centre, "burst")
        stamp(_qed(8.0 + grow), centre, "qed")
        dust([(-6.0, 14.0, 2.0), (8.0, -15.0, 2.0)], centre)
    elif anim in ("attack_up", "air_up") and 3 <= i <= 6:
        # The primes go up from his finger, one after the other.
        for k in range(3):
            step = (i - 3) + k
            rise = 11.0 * k + 3.0 * (i - 3)
            y = hand[1] - 16.0 - rise
            # One that would leave the cell has gone.
            if y > 9.0:
                stamp(_prime(PRIMES[step % 6], 8.0 - k, (CHALK_GOLD, CHALK, CHALK_BLUE)[k]), (hand[0] + 4.0 + 5.0 * math.sin(step * 1.9), y),
                      f"prime_{k}")
    elif anim == "attack_down" and i >= 4:
        graph(min(7, 3 + 2 * (i - 4)), 13 + min(3, i - 4), (hand[0] + 6.0, GROUND - 15.0), 4 * min(3, i - 4))
        dust([(-18.0, 8.0, 2.0), (24.0, 6.0, 2.0)], (hand[0] + 6.0, GROUND - 15.0))
    elif anim == "air_down" and 2 <= i <= 5:
        graph(4 + (i % 2), 10, (hip[0] + 1.0, GROUND - 10.0))
    elif anim == "air_neutral":
        for k in range(3):
            a = ph + k * math.tau / 3.0
            stamp(_prime(PRIMES[k], 8.0, (CHALK_GOLD, CHALK, CHALK_BLUE)[k]), (hip[0] + 35.0 * math.cos(a), hip[1] - 18.0 + 11.0 * math.sin(a)),
                  f"prime_{k}")
    elif anim == "air_forward" and 2 <= i <= 4:
        stamp(_epsilon(8.0), (hand[0] + 19.0, hand[1] - 1.0), "epsilon")
        stamp(_dust(1.5), (hand[0] + 27.0, hand[1] - 8.0), "dust_0")
    elif anim == "air_back" and 2 <= i <= 4:
        stamp(_burst(8.0), (foot[0] - 11.0, foot[1]), "burst")
    elif anim == "interact" and 3 <= i <= 5:
        stamp(_tick(4.0), (hand[0] + 17.0, hand[1] - 5.0), "tick")
    elif anim == "charge":
        graph(min(7, 1 + i), 13, (head[0] - 4.0, head[1] - 34.0))
    elif anim == "cast":
        if i < 2:
            graph(7, 13, (head[0] - 4.0 + 12.0 * i, head[1] - 34.0 + 12.0 * i))
        else:
            go = (i - 2) / max(1, n - 3)
            mid = ((hand[0] + far_hand[0]) / 2.0, (hand[1] + far_hand[1]) / 2.0)
            graph(7, 13 + int(round(3.0 * go)), (mid[0] + 21.0 + 4.0 * go, mid[1] - 4.0), int(round(10.0 * go)))
            dust([(8.0, -22.0, 2.5), (14.0, 18.0, 2.0)], mid)
    elif anim == "celebrate":
        stamp(_qed(7.0), (head[0] + 3.0, head[1] - 27.0 - 3.0 * abs(math.sin(ph))), "qed")
        dust([(-38.0, -4.0, 2.5), (40.0, -6.0, 2.5)], head)
    elif anim == "taunt":
        stamp(_cup(), hand, "cup", -8.0 if 0.25 <= u <= 0.65 else 0.0)
        if u < 0.25 or u > 0.7:
            stamp(_steam(i % 4), pin((hand[0] + 4.0, hand[1] - 9.0)), "steam")
        if u > 0.7:
            stamp(_prime("2", 7.0, CHALK_GOLD), (head[0] + 15.0, head[1] - 20.0), "prime")
    elif anim == "death" and i >= n - 2:
        stamp(_qed(6.0), (head[0] + 4.0, head[1] - 17.0 - 4.0 * (i - (n - 2))), "qed")
    return out


# ---- The frame ---------------------------------------------------------------


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = ROW_POSES[anim](frame_idx, nframes)
    img = K.new_frame()
    rot = float(pose["rot"])  # type: ignore[arg-type]
    lean = float(pose["lean"])  # type: ignore[arg-type]
    hx, hy = pose["hip"]  # type: ignore[misc]
    ox, oy = pose["off"]  # type: ignore[misc]
    hip = (hx * U, -HIP_UP + hy * U)
    px, py = pose["pivot"]  # type: ignore[misc]
    pivot = (hip[0] + px * U, hip[1] + py * U)

    def W(p: Point) -> Point:
        """A point of him (from the ground under him) in the frame."""
        r = turned((p[0] - pivot[0], p[1] - pivot[1]), rot)
        return (CX + ox * U + pivot[0] + r[0], GROUND + oy * U + pivot[1] + r[1])

    def trunk(x: float, y: float) -> Point:
        """A point of his trunk, from his hips, his spine up."""
        r = turned((x, y), lean)
        return (hip[0] + r[0], hip[1] + r[1])

    def limb(name: str, bones: List[Tuple[Point, Point, Callable]]) -> None:
        """Every bone's outline, and then every bone."""
        for edge in (True, False):
            for k, (a, b, bone) in enumerate(bones):
                K.place(img, bone(edge), W(a), f"{name}_{k}{'_edge' if edge else ''}", angle(W(a), W(b)))

    def arm(near: bool) -> Point:
        key, name = ("na", "near") if near else ("fa", "far")
        shoulder = trunk(*(NEAR_SHOULDER if near else FAR_SHOULDER))
        dx, dy = pose[key]  # type: ignore[misc]
        elbow, wrist = solve(shoulder, (shoulder[0] + dx * U, shoulder[1] + dy * U), UPPER, FORE, float(pose[key + "b"]))  # type: ignore[arg-type]
        colour = TWEED if near else TWEED_DARK
        limb(f"{name}_arm", [
            (shoulder, elbow, lambda edge: _bone("upper", UPPER, 7.0, 5.8, colour, TWEED_DARK, edge)),
            (elbow, wrist, lambda edge: _bone("fore", FORE, 5.8, 5.0, colour, TWEED_DARK, edge)),
        ])
        if near:
            K.place(img, _patch(), W(elbow), "elbow_patch", angle(W(elbow), W(wrist)))
        K.place(img, _hand(str(pose["nh" if near else "fh"]), near), W(wrist), f"{name}_hand", angle(W(elbow), W(wrist)))
        return W(wrist)

    def leg(near: bool) -> Point:
        key, name = ("nf", "near") if near else ("ff", "far")
        root = (hip[0] + (NEAR_HIP if near else FAR_HIP)[0], hip[1])
        fx, fy, toe = pose[key]  # type: ignore[misc]
        knee, ankle = solve(root, (fx * U, fy * U - ANKLE_UP), THIGH, SHIN, -1.0)
        # His trousers stop above his ankle.
        t = 1.0 - SOCK / SHIN
        cuff = (lerp(knee[0], ankle[0], t), lerp(knee[1], ankle[1], t))
        colour = TROUSER if near else TROUSER_DARK
        sock = SOCK_FILL if near else mix(SOCK_FILL, SOCK_DARK, 0.7)
        limb(f"{name}_leg", [
            (cuff, ankle, lambda edge: _bone("sock", SOCK, 4.2, 4.0, sock, SOCK_DARK, edge)),
            (root, knee, lambda edge: _bone("thigh", THIGH, 7.4, 6.2, colour, TROUSER_DARK, edge)),
            (knee, cuff, lambda edge: _bone("shin", SHIN - SOCK, 6.2, 6.4, colour, TROUSER_DARK, edge)),
        ])
        K.place(img, _sandal(near), W(ankle), f"{name}_sandal", toe + rot)
        return W(ankle)

    far_hand = arm(False)
    leg(False)
    kicking = pose["leg"] == "over"
    near_foot = (0.0, 0.0) if kicking else leg(True)

    neck = trunk(*NECK)
    hdx, hdy, tilt = pose["head"]  # type: ignore[misc]
    up = turned(HEAD_UP, lean * 0.5 + tilt * 0.3)
    head_at = (neck[0] + up[0] + hdx * U, neck[1] + up[1] + hdy * U)
    head = W(head_at)
    throat = W((head_at[0] - 0.2, head_at[1] + 4.0))
    K.place(img, _neck(round(math.dist(W(neck), throat))), W(neck), "neck", angle(W(neck), throat))

    hem = pose["hem"]
    K.place(img, _jacket(int(round(max(0.0, hem[0]) * U)), int(round(max(0.0, hem[1]) * U))), W(hip), "jacket", lean + rot)  # type: ignore[index]
    if kicking:
        near_foot = leg(True)

    under = pose["arm"] == "under"
    near_hand = arm(True) if under else (0.0, 0.0)

    turn = lean * 0.35 + tilt + rot
    K.place(img, _head(), head, "head", turn)
    K.place(img, _eyes(str(pose["eyes"])), head, "eyes", turn)
    K.place(img, _glasses(), head, "glasses", turn)
    brows = float(pose["brows"])  # type: ignore[arg-type]
    K.place(img, _brows(1 if brows > 0.5 else -1 if brows < -0.5 else 0), head, "brows", turn)
    K.place(img, _mouth(str(pose["mouth"])), head, "mouth", turn)
    K.place(img, _collar(), W(neck), "collar", lean + rot)

    if not under:
        near_hand = arm(True)

    at = {"hand": near_hand, "far_hand": far_hand, "head": head, "hip": W(hip), "foot": near_foot, "shoulder": W(trunk(*NEAR_SHOULDER))}
    for part, p, name, degrees in _effects(anim, frame_idx, nframes, at):
        K.place(img, part, p, name, degrees)  # type: ignore[arg-type]
    return K.downsample(img)


#: The body the game moves: his jacket, standing, up to the top of his head.
BODY_BOX = (CX - 13.0, GROUND - HEIGHT, CX + 15.0, GROUND)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return K.render(TARGET_NAME, ROWS, _render_frame, out_dir, ACTOR_METADATA, BODY_BOX)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Erdish spritesheet.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


# ---- In the round (``_person_round``) -----------------------------------------
#
# His pieces placed in 3D, so he can be drawn from the views he has no art
# for. His own pieces draw him: his head, jacket and collar in his
# three-quarter view (and its mirror for the left), his sleeves, hands,
# trousers, socks and sandals in every view. A head and a jacket in 3D draw
# the other views. He has no front view, so how wide he is from the front is
# read from his build, not drawn. His rows do not use this.

import numpy as np  # noqa: E402

from types import SimpleNamespace  # noqa: E402

from . import _person_round as O  # noqa: E402
from . import _round_cast as C  # noqa: E402
from . import _round_wear as W  # noqa: E402

#: As he rests (``idle``, its first frame): thinking, his chin on his near
#: hand, his far hand behind his back.
_REST = ROW_POSES["idle"](0, dict((n, k) for n, k, _ in ROWS)["idle"])
_LEAN = float(_REST["lean"])
_TILT = float(_REST["head"][2])
#: Half his width from the front at the shoulders, at the hips, and at the
#: feet (he is thin).
_SW, _HW = 7.8, 4.2
_FOOT = _HW + 2.2 * U


def _seen(p: Point, lean: float = _LEAN) -> Point:
    """A point of his trunk where his three-quarter view draws it (it leans)."""
    return turned(p, lean)


def _lifted(p: Point, l: float, lean: float = _LEAN) -> Tuple[float, float, float]:
    x, y = _seen(p, lean)
    return (l, y, O.lift(x, l))


_NECK3 = _lifted(NECK, 0.0)
_up = turned(HEAD_UP, _LEAN * 0.5 + _TILT * 0.3)
HEAD3 = (0.0, _seen(NECK)[1] + _up[1], O.lift(_seen(NECK)[0] + _up[0] + float(_REST["head"][0]) * U, 0.0))
SHOULDERS3 = {"r": _lifted(NEAR_SHOULDER, -_SW), "l": _lifted(FAR_SHOULDER, _SW)}
HIPS3 = {"r": (-_HW, 0.0, O.lift(NEAR_HIP[0], -_HW)), "l": (_HW, 0.0, O.lift(FAR_HIP[0], _HW))}
ANKLES3 = {"r": (-_FOOT, HIP_UP - ANKLE_UP, O.lift(float(_REST["nf"][0]) * U, -_FOOT)),
           "l": (_FOOT, HIP_UP - ANKLE_UP, O.lift(float(_REST["ff"][0]) * U, _FOOT))}
#: Where his three-quarter view puts his wrists at rest: his chin on his near
#: hand, his far hand behind his back.
_CHIN = (NEAR_SHOULDER[0] + AT_CHIN[0] * U, NEAR_SHOULDER[1] + AT_CHIN[1] * U)
_BACK = (FAR_SHOULDER[0] + BEHIND[0] * U, FAR_SHOULDER[1] + BEHIND[1] * U)
#: As he rests: his chin is in the middle; his far hand behind his back.
STANCE = C.Stance(hands={"r": C.Hand(l=-1.0, pole=(-0.4, 1.0, 0.1)), "l": C.Hand(l=3.0, pole=(1.0, 0.2, -0.4))})

#: His hair: the mass on top of his head, and what goes round behind his ears.
_HAIR_TOP = ((0.0, -8.8, -0.6), (7.8, 4.8, 8.4))
_HAIR_BACK = ((0.0, 1.0, -6.0), (7.0, 5.2, 3.6))


def _strands() -> List[object]:
    """The lines in his hair, as his three-quarter view draws them, all round
    his head: light strands over the top that curl back, dark ones down the
    back and the sides of what is behind his ears."""
    out = []
    for k, u in enumerate(range(-160, 180, 40)):
        u0 = float(u) + (7.0 if k % 2 else -5.0)
        pts = [O.on_ellipsoid(*_HAIR_TOP, u0 + 22.0 * t, -13.2 + 5.0 * t + 0.8 * math.sin(3.0 * t), 0.2)[0] for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        out.append(O.curve(pts, HAIR_LIGHT, 0.6))
    for u in (-150.0, -120.0, -95.0, 95.0, 120.0, 150.0, 180.0):
        pts = [O.on_ellipsoid(*_HAIR_BACK, u + 10.0 * t, -3.4 + 7.0 * t, 0.2)[0] for t in (0.0, 0.5, 1.0)]
        out.append(O.curve(pts, HAIR_SHADE, 0.6))
    for u in (-60.0, 60.0):
        pts = [O.on_ellipsoid(*_HAIR_TOP, u, -6.6 - 2.4 * t, 0.2)[0] for t in (0.0, 0.5, 1.0)]
        out.append(O.curve(pts, HAIR_SHADE, 0.6))
    return out


#: His head in 3D, from his three-quarter view: a long skull, a thin jaw well
#: forward of it, a long nose, large ears, grey hair on top that stands up,
#: high over the forehead and down behind the ears; large square black
#: glasses; no beard.
HEAD_3D = O.Head3D(
    skin=SKIN, shade=SKIN_SHADE, deep=SKIN_DEEP,
    skull=((0.0, -2.4, 0.0), (7.4, 9.0, 8.2)), jaw=((0.0, 4.2, 3.7), (5.0, 7.6, 3.8)), nose=((0.0, 1.4, 8.0), (0.9, 2.6, 1.9)), nose_tip=((0.0, 3.8, 9.4), (1.2, 1.3, 1.3)),
    ear=((-7.6, 1.2, 0.5), (1.8, 3.7, 2.5)), eye=(36.0, -0.1), eye_size=0.95, ink=INK, lid=SKIN_DEEP, brow=(HAIR_SHADE, None, -4.6, 1.1),
    hair=lambda u, v: (v < -8.4 + 2.4 * np.abs(u) / 180.0) | ((np.abs(u) > 80.0) & (v < 5.0)),
    hair_colour=HAIR, hair_shade=HAIR_SHADE,
    volumes=[_HAIR_TOP, _HAIR_BACK,
             ((-3.4, -13.0, 1.0), (2.2, 2.4, 2.2)), ((1.0, -13.8, -1.6), (2.2, 2.6, 2.2)), ((3.6, -12.8, 2.6), (2.0, 2.2, 2.0))],
    glasses=O.Glasses("square", (3.1, 2.9), FRAME, LENS, 0.9, top=0.5),
    lines=[O.curve([(-2.4, 8.0, 6.4), (0.0, 8.4, 7.0), (2.4, 8.0, 6.4)], MOUTH, 0.8),
           O.curve([(-3.4, 4.4, 8.0), (-3.8, 6.6, 7.0), (-3.6, 9.2, 6.0)], SKIN_DEEP, 0.6),
           O.curve([(3.4, 4.4, 8.0), (3.8, 6.6, 7.0), (3.6, 9.2, 6.0)], SKIN_DEEP, 0.6),
           O.curve([(-2.2, -6.6, 7.0), (0.0, -7.0, 7.4), (2.2, -6.6, 7.0)], mix(SKIN, SKIN_DEEP, 0.55), 0.45)] + _strands(),
)


#: His jacket: narrow, its back round (the rings go back at the shoulders),
#: open on his cardigan (four buttons) and his shirt (no tie, the collar open);
#: lapels; a pocket on his right chest with a stick of chalk and two pens in
#: it, a pocket low on each side, a seam down his back.
JACKET_3D = W.Trunk(
    rings=[O.Ring(-38.5, 0.0, 2.6, 4.0, 3.4), O.Ring(-35.0, 0.0, 1.4, 7.8, 6.4), O.Ring(-30.0, 0.0, 0.0, 8.6, 7.8), O.Ring(-24.0, 0.0, 0.0, 8.8, 7.4),
           O.Ring(-14.0, 0.0, 0.4, 8.4, 6.4), O.Ring(-4.0, 0.0, 0.4, 8.4, 6.2), O.Ring(0.0, 0.0, 0.2, 8.8, 6.4), O.Ring(8.0, 0.0, 0.2, 9.6, 7.0)],
    garment=W.Garment(TWEED, TWEED_DARK, radius=8.8, features=[
        W.Opening(30.0, CARDIGAN, top=-34.0), W.Buttons(0.0, -23.0, 2.0, 4, 0.9, CARDIGAN_DARK), W.Neckline(-39.0, -26.5, 24.0, SHIRT),
        W.Neckline(-39.0, -32.6, 12.0, SKIN_SHADE), W.Lapels(30.0, -38.0, -20.0, 12.0, TWEED_LIGHT, line=TWEED_DARK),
        W.Across(-62.0, -28.0, -21.4, TWEED_DARK), W.Patch(-58.0, -50.0, -25.0, -21.6, CHALK), W.Patch(-42.0, -38.0, -24.4, -21.6, CHALK_BLUE),
        W.Patch(-35.0, -31.0, -24.0, -21.4, CARDIGAN), W.Across(50.0, 85.0, -3.0, TWEED_DARK, both=True), W.Down(180.0, -26.0, 20.0, TWEED_DARK),
        W.Shade()]),
    shoulder=((-6.6, -30.4, 0.6), (4.6, 5.4, 4.6)),
    collar=([O.Ring(-40.0, 0.0, 3.0, 2.9, 2.7), O.Ring(-38.4, 0.0, 2.8, 3.6, 3.4), O.Ring(-36.6, 0.0, 3.0, 4.2, 4.0, droop=1.2)],
            W.Garment(SHIRT, SHIRT_DARK, features=[W.Opening(16.0, SKIN_SHADE)])),
)


def _front_sandal():
    """A foot in its sock and its sandal, seen from the toe: two straps over
    the sock."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, 1.4), 4.2, 3.2, WHITE)
        K.rrect(d, K.home[0] - 4.2, K.home[1] + 0.4, K.home[0] + 4.2, K.home[1] + ANKLE_UP + 0.4, 1.4, WHITE)

    def detail(d) -> None:
        K.rrect(d, K.home[0] - 6.0, K.home[1] + ANKLE_UP - 0.9, K.home[0] + 6.0, K.home[1] + ANKLE_UP + 2.0, 0.0, SANDAL_DARK)
        K.rrect(d, K.home[0] - 4.4, K.home[1] + 0.2, K.home[0] + 4.4, K.home[1] + 1.6, 0.4, SANDAL)

    return K.solid(("front_sandal",), shape, SOCK_FILL, detail, outline=1.2, rim=0.25, shade=0.3, shade_colour=SOCK_DARK)


def _back_sandal():
    """A foot in its sock and its sandal, seen from the heel: the strap round
    the back of the heel."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, 1.4), 3.8, 3.0, WHITE)
        K.rrect(d, K.home[0] - 3.8, K.home[1] + 0.4, K.home[0] + 3.8, K.home[1] + ANKLE_UP + 0.4, 1.4, WHITE)

    def detail(d) -> None:
        K.rrect(d, K.home[0] - 6.0, K.home[1] + ANKLE_UP - 0.9, K.home[0] + 6.0, K.home[1] + ANKLE_UP + 2.0, 0.0, SANDAL_DARK)
        K.rrect(d, K.home[0] - 3.8, K.home[1] + 0.8, K.home[0] + 3.8, K.home[1] + 2.2, 0.4, SANDAL)

    return K.solid(("back_sandal",), shape, SOCK_FILL, detail, outline=1.2, rim=0.25, shade=0.3, shade_colour=SOCK_DARK)


def _wrist(near, l):
    x, y = _seen(_CHIN if near else _BACK)
    return (l, y, O.lift(x, l))


def _arm_bones(pts, near):
    colour = TWEED if near else TWEED_DARK
    return [(pts[0], pts[1], lambda edge, n: _bone("upper", n, 7.0, 5.8, colour, TWEED_DARK, edge)),
            (pts[1], pts[2], lambda edge, n: _bone("fore", n, 5.8, 5.0, colour, TWEED_DARK, edge))]


def _leg_bones(pts, near):
    # His trousers stop above his ankle; his sock is under them.
    h, k, a = pts
    c = (lerp(k[0], a[0], 1.0 - SOCK / SHIN), lerp(k[1], a[1], 1.0 - SOCK / SHIN))
    colour = TROUSER if near else TROUSER_DARK
    sock = SOCK_FILL if near else mix(SOCK_FILL, SOCK_DARK, 0.7)
    return [(c, a, lambda edge, n: _bone("sock", n, 4.2, 4.0, sock, SOCK_DARK, edge)),
            (h, k, lambda edge, n: _bone("thigh", n, 7.4, 6.2, colour, TROUSER_DARK, edge)),
            (k, c, lambda edge, n: _bone("shin", n, 6.2, 6.4, colour, TROUSER_DARK, edge))]


def _elbow_patch(side, img, pts, near):
    if side == "r":
        K.place(img, _patch(), pts[1], "elbow_patch", angle(pts[1], pts[2]))


def _own(J):
    """His own head, jacket and collar in his three-quarter view. His jacket
    and collar are not mirrored: the pocket on his chest is on his right."""
    turn = _LEAN * 0.35 + _TILT
    layers = lambda: O.composed(K, [(_head(), "head"), (_eyes(str(_REST["eyes"])), "eyes"), (_glasses(), "glasses"),  # noqa: E731
                                    (_brows(1 if float(_REST["brows"]) > 0.5 else 0), "brows"), (_mouth(str(_REST["mouth"])), "mouth")], turn)
    return {"trunk": C.own_art("own_jacket", (0.0, 0.0, 0.0), lambda: _jacket(0, 0), degrees=_LEAN, lead=0.4, mirror=False),
            "head": C.own_art("own_head", J.head, layers, lead=9.0),
            "collar": C.own_art("own_collar", J.neck, _collar, degrees=_LEAN, lead=9.5, mirror=False)}


#: Erdish as a body (``_round_cast.RigBody``): his joints lifted from his
#: three-quarter view and his build, his own pieces drawn at them.
BODY = C.RigBody(
    K, FRAME_SIZE, CX, GROUND, HIP_UP, UPPER, FORE, THIGH, SHIN,
    rest_joints=SimpleNamespace(shoulders=SHOULDERS3, hips=HIPS3, ankles=ANKLES3, neck=_NECK3, head=HEAD3,
                                throat=tuple(np.asarray(HEAD3) + [0.0, 4.0, -0.6]), rest=_REST, wrist=_wrist),
    hand_modes=(str(_REST["nh"]), str(_REST["fh"])), arm_bones=_arm_bones, leg_bones=_leg_bones, hand=_hand, shoe=_sandal, front_shoe=_front_sandal,
    back_shoe=_back_sandal, own_pieces=_own, frames=lambda: {"front_3q": _render_frame("idle", 0, dict((n, k) for n, k, _ in ROWS)["idle"])},
    neck_piece=_neck, arm_extra=_elbow_patch)
ROUND = C.Round("Erdish", BODY, C.Look(HEAD_3D, JACKET_3D), STANCE)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
