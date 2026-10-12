"""Sprite generator for Ramen-nujan: the mathematician who dreams his theorems.

A respectful parody of Srinivasa Ramanujan, of the Flying Spaghetti Monster's
faction. He is a person, not a food mascot: the noodles are in his clothes.

The look (redrawn 2026-10-11): a small, round young scholar seen three
quarters from the front, facing right. A big head with very large dark eyes,
side-parted black hair and one lock that stands up in a wave like a noodle. A
night-blue coat buttoned to the neck, with carrot buttons, a scallion-green
lining and a few gold dots joined like a constellation; cream trousers; and a
long noodle-coloured scarf whose two tails end in loose noodles and trail
behind whatever he does. At rest he stands with his hands behind his back and
looks up.

Everything he eats is vegetarian, and so are the colours: mushroom cream,
scallion green, carrot orange, sesame gold. He holds nothing; the runtime
held-item system is authoritative. There is no drop shadow.

His magic is written in chalk-gold: a summation sweep (the arc with a sigma at
its head), a factorial burst (the ``!``), the ``-1/12`` seal, a bracket for a
shield, the dots of a partition, and the dream bubble a theorem arrives in.

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

TARGET_NAME = "ramen_nujan"
FRAME_SIZE = (176, 160)
GROUND = 150.0
CX = 84.0

# ---- The rig: lengths in frame pixels, from his hips, up is negative ---------

#: How high his hips are when he stands.
HIP_UP = 37.0
THIGH, SHIN = 17.5, 17.0
#: His hips to the base of his neck, along his spine.
NECK = 31.0
UPPER, FORE = 15.0, 14.0
NEAR_SHOULDER: Point = (-5.5, -26.5)
FAR_SHOULDER: Point = (6.5, -26.0)
NEAR_HIP: Point = (-3.5, 0.0)
FAR_HIP: Point = (3.5, 0.0)
#: The sole of a shoe is this far under its ankle.
ANKLE_UP = 3.0
#: The top of his hair above the ground, standing (the lock stands higher).
HEIGHT = 108.0

COAT: RGBA = (58, 70, 150, 255)
COAT_DARK: RGBA = (40, 46, 108, 255)
COAT_LIGHT: RGBA = (92, 108, 196, 255)
LINING: RGBA = (118, 178, 88, 255)
LINING_DARK: RGBA = (78, 132, 66, 255)
CARROT: RGBA = (242, 134, 52, 255)
NOODLE: RGBA = (252, 228, 158, 255)
NOODLE_DARK: RGBA = (222, 172, 84, 255)
SESAME: RGBA = (250, 208, 110, 255)
TROUSER: RGBA = (226, 212, 180, 255)
TROUSER_DARK: RGBA = (176, 160, 132, 255)
SHOE: RGBA = (104, 66, 46, 255)
SHOE_DARK: RGBA = (70, 44, 36, 255)
SKIN: RGBA = (182, 120, 80, 255)
SKIN_SHADE: RGBA = (142, 86, 60, 255)
SKIN_DEEP: RGBA = (112, 62, 46, 255)
BLUSH: RGBA = (226, 112, 90, 110)
HAIR: RGBA = (30, 26, 40, 255)
HAIR_LIGHT: RGBA = (84, 84, 124, 255)
EYE_WHITE: RGBA = (252, 248, 238, 255)
IRIS: RGBA = (74, 44, 30, 255)
INK: RGBA = (26, 18, 30, 255)
MOUTH: RGBA = (96, 36, 40, 255)
TONGUE: RGBA = (226, 112, 108, 255)
DREAM: RGBA = (255, 224, 122, 255)
DREAM_DARK: RGBA = (226, 150, 60, 255)
DREAM_PALE: RGBA = (255, 250, 224, 255)
CLOUD: RGBA = (238, 234, 255, 255)
CLOUD_DARK: RGBA = (170, 160, 226, 255)

K = Kit(FRAME_SIZE)

ACTOR_METADATA = {
    "actor": {"character_id": "npc_ramen_nujan", "display_name": "Ramen-nujan"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "mathematician", "number_theorist", "fsm_faction", "vegetarian", "playable_candidate", "dream_math"],
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
    "tags": ["story", "humanoid", "mathematician", "number_theorist", "fsm_faction", "vegetarian", "playable_candidate", "dream_math"],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": CX + 2.0, "y": GROUND - 87.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": CX + 1.0, "y": GROUND - 54.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": CX - 14.0, "y": GROUND - 42.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": CX + 9.0, "y": GROUND - 41.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": CX + 2.0, "y": GROUND - 124.0}},
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
        "Ramen-nujan is a respectful noodle-inflected parody of Srinivasa Ramanujan. He remains a "
        "human mathematical visionary, not a food mascot: dreams supply astonishing identities, "
        "while waking life is spent constructing the proof-path back to them. His noodle scarf "
        "connects him to the Flying Spaghetti Monster faction."
    ),
    "gameplay_description": (
        "Use as an intuitive number theorist, dream oracle, glass-cannon mathematician, or quest "
        "giver. His abilities should leap to summations, partitions, factorial bursts, and "
        "unexpected constants, then ask the player to build the missing proof or route."
    ),
    "dialogue_hints": {
        "barks": [
            "Last night I dreamt an infinite bowl of noodles.",
            "The answer came first. The proof is still on its way.",
            "1729 is a very interesting number.",
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
    "na": (-3.0, 26.0),
    "fa": (2.0, 25.5),
    "nab": 1.0,
    "fab": 1.0,
    # His near arm is painted over his head, or under it (a hand that
    # reaches up past his face comes out from behind it).
    "arm": "over",
    # His near leg is painted under his coat, or over it (a kick).
    "leg": "under",
    "nh": "soft",
    "fh": "soft",
    # The sole of each shoe from the ground under him, and its toe's turn.
    "nf": (-5.0, 0.0, 0.0),
    "ff": (6.0, 0.0, 0.0),
    # All of him turned about a point (from his hips), and then moved.
    "rot": 0.0,
    "pivot": (0.0, 0.0),
    "off": (0.0, 0.0),
    "eyes": "open",
    "mouth": "smile",
    "brows": 0.0,
    # Where his scarf's tails point (90 hangs, 180 trails behind, 270 is up),
    # how far they wave and how much they curl.
    "tail": 100.0,
    "wave": 9.0,
    "curl": 3.0,
    # How far the hem of his coat swings out behind and in front.
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


@row
def idle(i: int, n: int) -> Pose:
    # Hands behind his back, looking up at whatever he is working out.
    _, s, _c = _loop(i, n)
    return P(hip=(0.0, 0.5 + 0.5 * s), head=(0.4, -0.4 * s, -4.0 + s), na=(-8.5, 21.5), fa=(-7.0, 22.0),
             eyes="closed" if i == n - 2 else "up", tail=98.0 + 3.0 * s, wave=7.0)


def _stride(ph: float, reach: float, lift: float, mid: float = 0.5) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """The near and far soles of a step cycle."""

    def foot(p: float, x0: float) -> Tuple[float, float, float]:
        s, c = math.sin(p), math.cos(p)
        up = max(0.0, -s)
        # The toe comes up to land and goes down to push off.
        return (x0 + reach * c, -lift * up, -16.0 * max(0.0, c) * (1.0 if s < 0.0 else 0.35) + 26.0 * up * max(0.0, -c))

    return foot(ph, mid - 1.0), foot(ph + math.pi, mid + 1.0)


@row
def walk(i: int, n: int) -> Pose:
    ph, s, c = _loop(i, n)
    nf, ff = _stride(ph, 9.0, 5.5)
    return P(hip=(0.5, 1.0 * math.cos(2.0 * ph)), lean=3.0, head=(0.0, 0.0, 1.5 * s), na=(-2.0 - 8.0 * c, 25.0 - 1.5 * abs(c)),
             fa=(2.5 + 8.0 * c, 24.5 - 1.5 * abs(c)), nf=nf, ff=ff, tail=122.0, wave=11.0, hem=(1.0 + 1.5 * abs(c), 0.5 + 1.5 * abs(c)))


@row
def run(i: int, n: int) -> Pose:
    ph, s, c = _loop(i, n)
    nf, ff = _stride(ph, 13.0, 10.0, 0.0)
    return P(hip=(2.0, 1.5 + 1.8 * math.cos(2.0 * ph)), lean=14.0, head=(0.5, 0.0, -6.0), na=(-1.0 - 11.0 * c, 16.0 + 2.0 * c),
             fa=(3.0 + 11.0 * c, 16.0 - 2.0 * c), nh="fist", fh="fist", nf=nf, ff=ff, mouth="open", brows=-1.0, tail=168.0, wave=13.0,
             curl=1.0, hem=(4.0, 1.0))


CROUCH = P(hip=(-1.0, 15.0), lean=15.0, head=(1.0, 0.0, -9.0), na=(11.0, 17.0), fa=(13.0, 16.0), nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0),
           tail=108.0, hem=(2.0, 3.0))


@row
def crouch(i: int, n: int) -> Pose:
    _, s, _c = _loop(i, n)
    return dict(CROUCH, hip=(-1.0, 15.0 + 0.6 * s), eyes="closed" if i == n - 2 else "open")


@row
def crouch_walk(i: int, n: int) -> Pose:
    ph, _s, c = _loop(i, n)
    nf, ff = _stride(ph, 6.5, 3.0)
    return dict(CROUCH, hip=(-0.5, 14.5 + 0.8 * math.cos(2.0 * ph)), nf=nf, ff=ff, na=(10.0 - 3.0 * c, 17.0), fa=(12.0 + 3.0 * c, 16.0),
                tail=126.0)


RISE = P(hip=(0.0, -2.0), lean=4.0, head=(0.0, 0.0, -8.0), na=(-12.0, -24.0), nab=-1.0, fa=(17.0, -20.0), nh="open", fh="open",
         nf=(-6.0, -1.0, 34.0), ff=(6.0, -11.0, 12.0), mouth="open", brows=1.0, tail=96.0, wave=5.0, curl=0.0, hem=(1.0, 1.0))
APEX = P(hip=(0.0, -2.0), lean=2.0, head=(0.0, 0.0, -3.0), na=(-19.0, -8.0), nab=-1.0, fa=(21.0, -8.0), nh="open", fh="open",
         nf=(-4.0, -9.0, 22.0), ff=(7.0, -13.0, 6.0), eyes="happy", mouth="open", tail=150.0, wave=10.0, hem=(3.0, 3.0))
FALL = P(hip=(0.0, -3.0), lean=-4.0, head=(0.0, 0.0, 4.0), na=(-17.0, -19.0), nab=-1.0, fa=(20.0, -17.0), nh="open", fh="open",
         nf=(-7.0, -4.0, 26.0), ff=(6.0, -9.0, 10.0), eyes="wide", mouth="o", brows=1.0, tail=264.0, wave=13.0, curl=1.0, hem=(4.0, 4.0))


@row
def jump(i: int, n: int) -> Pose:
    wind = P(hip=(-1.0, 9.0), lean=10.0, na=(-14.0, 18.0), fa=(-10.0, 20.0), nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), brows=-1.0, tail=108.0)
    return keys(_shot(i, n), [(0.0, wind), (0.3, RISE), (0.6, RISE), (1.0, APEX)])


@row
def fall(i: int, n: int) -> Pose:
    _, s, c = _loop(i, n)
    return dict(FALL, na=(-17.0 + 2.0 * s, -19.0 - 2.0 * c), fa=(20.0 - 2.0 * s, -17.0 + 2.0 * c), nf=(-7.0, -4.0 + 1.5 * s, 26.0),
                ff=(6.0, -9.0 - 1.5 * s, 10.0))


LANDED = P(hip=(0.0, 18.0), lean=24.0, head=(2.0, 2.0, 6.0), na=(14.0, 24.0), fa=(18.0, 21.0), nh="open", fh="open", nf=(-8.0, 0.0, 0.0),
           ff=(9.0, 0.0, 0.0), eyes="wince", mouth="grit", tail=70.0, wave=6.0, hem=(3.0, 4.0))
HALF_UP = P(hip=(0.0, 7.0), lean=9.0, na=(4.0, 23.0), fa=(7.0, 22.0), nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), tail=104.0, hem=(1.0, 2.0))


@row
def land_hard(i: int, n: int) -> Pose:
    return keys(_shot(i, n), [(0.0, dict(FALL, tail=250.0)), (0.16, LANDED), (0.55, dict(LANDED, eyes="closed", tail=110.0)), (1.0, HALF_UP)])


@row
def land_recovery(i: int, n: int) -> Pose:
    return keys(_shot(i, n), [(0.0, HALF_UP), (1.0, P(na=(-8.5, 21.5), fa=(-7.0, 22.0)))])


DASH = P(hip=(2.0, 6.0), lean=31.0, head=(1.0, 0.0, -20.0), na=(-20.0, 8.0), fa=(-15.0, 12.0), nh="open", fh="open", nf=(-13.0, -6.0, 38.0),
         ff=(9.0, 0.0, 0.0), brows=-1.0, mouth="flat", tail=180.0, wave=4.0, curl=0.0, hem=(6.0, 0.0))


@row
def dash_startup(i: int, n: int) -> Pose:
    back = P(hip=(-3.0, 4.0), lean=-9.0, na=(10.0, 15.0), fa=(13.0, 13.0), nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, -10.0), brows=-1.0, tail=80.0)
    return keys(_shot(i, n), [(0.0, back), (1.0, DASH)])


@row
def dash(i: int, n: int) -> Pose:
    _, s, _c = _loop(i, n)
    return dict(DASH, hip=(2.0, 6.0 + 0.8 * s), nf=(-13.0 - s, -6.0 - s, 38.0), tail=180.0 + 3.0 * s)


@row
def slide(i: int, n: int) -> Pose:
    _, s, _c = _loop(i, n)
    return P(hip=(-5.0, 23.0), lean=-40.0, head=(1.0, 0.0, 30.0), na=(-10.0, 18.0), fa=(12.0, 4.0), nh="open", fh="fist",
             nf=(17.0, -1.0 - 0.5 * s, -28.0), ff=(22.0, -5.0 + 0.5 * s, -34.0), brows=-1.0, mouth="grit", tail=178.0 + 3.0 * s, wave=6.0,
             curl=0.0, hem=(0.0, 5.0))


#: A ball, turned about its middle (which is 37 above the ground).
TUCK = P(hip=(0.0, 0.0), lean=38.0, head=(-17.0, 24.0, 50.0), na=(18.0, 18.0), fa=(20.0, 15.0), nh="fist", fh="fist", nf=(9.0, -27.0, 10.0),
         ff=(14.0, -30.0, 10.0), eyes="closed", mouth="flat", tail=180.0, wave=8.0, curl=34.0, arm="under", pivot=(15.5, -14.0), off=(-8.0, HIP_UP + 14.0 - 37.0),
         hem=(0.0, 3.0))


@row
def roll(i: int, n: int) -> Pose:
    return dict(TUCK, rot=360.0 * i / n)


@row
def wall_grab(i: int, n: int) -> Pose:
    _, s, _c = _loop(i, n)
    return P(hip=(3.0, -2.0 + 0.8 * s), lean=-6.0, head=(0.0, 0.0, -6.0), na=(26.0, -9.0), fa=(22.0, -14.0), arm="under", nh="open", fh="open",
             nf=(12.0, -6.0 + 0.8 * s, -55.0), ff=(14.0, -17.0 + 0.8 * s, -55.0), mouth="grit", brows=1.0, tail=96.0, wave=5.0)


@row
def wall_jump(i: int, n: int) -> Pose:
    held = wall_grab(0, 6)
    push = P(hip=(-4.0, -3.0), lean=-24.0, head=(0.0, 0.0, 14.0), na=(-18.0, -16.0), nab=-1.0, fa=(-8.0, -22.0), nh="open", fh="open",
             nf=(11.0, 0.0, -24.0), ff=(13.0, -7.0, -34.0), brows=-1.0, mouth="open", tail=20.0, wave=8.0, hem=(0.0, 4.0))
    away = dict(push, nf=(2.0, -8.0, 10.0), ff=(8.0, -13.0, 0.0), na=(-20.0, -6.0), fa=(-6.0, -16.0), tail=40.0)
    return keys(_shot(i, n), [(0.0, held), (0.4, push), (1.0, away)])


HANG = P(hip=(-1.0, 0.0), lean=3.0, head=(-1.0, 1.0, -12.0), na=(25.0, -14.0), fa=(19.0, -21.0), arm="under", nh="fist", fh="fist", nf=(-3.0, -1.0, 34.0),
         ff=(4.0, -3.0, 28.0), mouth="flat", brows=1.0, tail=92.0, wave=6.0)
PERCH = P(hip=(1.0, 16.0), lean=22.0, head=(1.0, 0.0, -12.0), na=(13.0, 23.0), fa=(16.0, 20.0), nh="open", fh="open", nf=(-7.0, 0.0, 0.0),
          ff=(9.0, 0.0, 0.0), tail=112.0, hem=(2.0, 4.0))


@row
def ledge_grab(i: int, n: int) -> Pose:
    _, s, _c = _loop(i, n)
    return dict(HANG, lean=3.0 + 2.5 * s, nf=(-3.0 - 2.0 * s, -1.0, 34.0), ff=(4.0 - 2.0 * s, -3.0, 28.0), tail=92.0 - 6.0 * s)


@row
def ledge_climb(i: int, n: int) -> Pose:
    pull = P(hip=(1.0, -3.0), lean=12.0, head=(1.0, 0.0, -10.0), na=(16.0, 4.0), fa=(18.0, 1.0), nh="fist", fh="fist", nf=(-4.0, -3.0, 30.0),
             ff=(10.0, -17.0, -8.0), mouth="grit", brows=-1.0, tail=110.0, hem=(1.0, 3.0))
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


SWEEP_LOW = P(hip=(4.0, 9.0), lean=20.0, head=(1.0, 0.0, -12.0), na=(26.0, 10.0), fa=(-10.0, 14.0), nh="flat", fh="fist", nf=(-9.0, 0.0, 10.0),
              ff=(11.0, 0.0, 0.0), brows=-1.0, mouth="open", tail=150.0, hem=(4.0, 3.0))


@row
def ledge_getup_attack(i: int, n: int) -> Pose:
    wind = dict(HALF_UP, na=(-18.0, 4.0), nh="flat", brows=-1.0)
    return keys(_shot(i, n), [(0.0, PERCH), (0.3, wind), (0.55, SWEEP_LOW), (0.75, SWEEP_LOW), (1.0, HALF_UP)])


@row
def climb(i: int, n: int) -> Pose:
    ph, s, c = _loop(i, n)
    return P(hip=(1.0, -1.0 + abs(s)), lean=5.0, head=(0.0, 0.0, -11.0), na=(26.0, -3.0 - 8.0 * c), fa=(22.0, -5.0 + 8.0 * c), arm="under", nh="fist",
             fh="fist", nf=(5.0, -6.0 + 6.0 * c, -14.0), ff=(7.0, -6.0 - 6.0 * c, -14.0), mouth="flat", tail=94.0, wave=5.0)


@row
def swim(i: int, n: int) -> Pose:
    ph, s, c = _loop(i, n)

    def stroke(p: float) -> Tuple[float, float]:
        a = math.radians(60.0 - 85.0 * math.cos(p))
        return (27.0 * math.sin(a), -27.0 * math.cos(a))

    return P(rot=64.0, off=(-4.0, -14.0 + 1.5 * s), lean=4.0, head=(0.0, 0.0, -42.0), na=stroke(ph), fa=stroke(ph + math.pi), arm="under", nh="flat",
             fh="flat", nf=(-4.0 + 5.0 * s, -1.0, 62.0), ff=(5.0 - 5.0 * s, -1.0, 62.0), mouth="o", tail=176.0, wave=12.0, curl=0.0,
             hem=(2.0, 2.0))


@row
def float_glide(i: int, n: int) -> Pose:
    # He floats the way he dreams: eyes shut, coat and scarf out behind him.
    _, s, c = _loop(i, n)
    return P(hip=(0.0, -2.0 + 1.2 * s), lean=22.0, head=(0.0, 0.0, -18.0), na=(-19.0, 9.0 + s), fa=(-14.0, 4.0 - s), nh="open", fh="open",
             nf=(-12.0, -4.0 + c, 46.0), ff=(-4.0, -2.0 - c, 40.0), eyes="closed", tail=196.0, wave=12.0, curl=-1.0, hem=(6.0, 1.0))


@row
def block(i: int, n: int) -> Pose:
    _, s, _c = _loop(i, n)
    return P(hip=(-2.0, 4.0 + 0.4 * s), lean=-5.0, head=(-1.0, 0.0, 3.0), na=(22.0, 4.0), fa=(19.0, -2.0), nh="open", fh="open",
             nf=(-7.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), brows=-1.0, mouth="flat", tail=84.0)


STRUCK = P(hip=(-4.0, 2.0), lean=-21.0, head=(-2.0, 0.0, -13.0), na=(17.0, 4.0), fa=(20.0, -2.0), nh="open", fh="open", nf=(-8.0, 0.0, 0.0),
           ff=(8.0, -5.0, -22.0), eyes="wince", mouth="big", brows=1.0, tail=24.0, wave=12.0, off=(-3.0, 0.0), hem=(0.0, 4.0))


@row
def hit(i: int, n: int) -> Pose:
    back = P(hip=(-2.0, 2.0), lean=-8.0, na=(3.0, 23.0), fa=(6.0, 22.0), eyes="wince", mouth="grit", tail=70.0)
    return keys(_shot(i, n), [(0.0, P(lean=-4.0, eyes="wide", mouth="o")), (0.25, STRUCK), (0.6, STRUCK), (1.0, back)])


@row
def death(i: int, n: int) -> Pose:
    # He sits down where he stood and is asleep: the dream goes on.
    sag = P(hip=(-5.0, 13.0), lean=-18.0, head=(-2.0, 0.0, -10.0), na=(6.0, 20.0), fa=(12.0, 16.0), nh="open", fh="open", nf=(-4.0, 0.0, 0.0),
            ff=(10.0, 0.0, -10.0), eyes="wince", mouth="o", tail=60.0, off=(-3.0, 0.0), hem=(0.0, 3.0))
    sat = P(hip=(-8.0, HIP_UP - 10.5), lean=-13.0, head=(0.0, 0.0, 2.0), na=(-9.0, 25.0), fa=(9.0, 24.0), nh="open", fh="open",
            nf=(19.0, 0.0, -62.0), ff=(25.0, 0.0, -66.0), eyes="closed", mouth="o", tail=110.0, hem=(0.0, 2.0))
    asleep = dict(sat, lean=-4.0, head=(1.0, 2.0, 22.0), mouth="smile", tail=96.0, wave=3.0)
    return keys(_shot(i, n), [(0.0, STRUCK), (0.28, sag), (0.5, sat), (0.72, asleep), (1.0, asleep)])


@row
def talk(i: int, n: int) -> Pose:
    _, s, c = _loop(i, n)
    return P(hip=(0.0, 0.4 * s), head=(0.5, 0.0, 2.5 * s), na=(-8.5, 21.5) if c > -0.2 else (13.0, 9.0 - 3.0 * s), nh="soft" if c > -0.2 else "point",
             fa=(19.0, 4.0 + 2.5 * s), fh="open", mouth=("open", "smile", "big", "smile")[i % 4], brows=1.0 if s > 0.3 else 0.0, tail=100.0 + 4.0 * s)


@row
def interact(i: int, n: int) -> Pose:
    reach = P(hip=(1.5, 1.0), lean=7.0, head=(1.0, 0.0, 2.0), na=(27.0, -1.0), nh="point", fa=(-7.0, 22.0), mouth="o", tail=108.0)
    return keys(_shot(i, n), [(0.0, P()), (0.35, reach), (0.7, dict(reach, na=(27.0, 3.0))), (1.0, P())])


GUARD = P(hip=(-1.0, 2.0), lean=2.0, na=(8.0, 13.0), fa=(14.0, 11.0), nh="fist", fh="fist", nf=(-7.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), brows=-1.0,
          mouth="flat", tail=96.0)


@row
def jab(i: int, n: int) -> Pose:
    poke = dict(GUARD, hip=(3.0, 3.0), lean=11.0, na=(28.0, 1.0), nh="point", ff=(10.0, 0.0, 0.0), mouth="open", tail=140.0)
    return keys(_shot(i, n), [(0.0, GUARD), (0.3, poke), (0.6, poke), (1.0, GUARD)])


@row
def punch(i: int, n: int) -> Pose:
    wind = dict(GUARD, hip=(-3.0, 3.0), lean=-7.0, na=(-14.0, 8.0), nh="open", tail=70.0)
    push = dict(GUARD, hip=(5.0, 4.0), lean=15.0, na=(28.0, 2.0), nh="open", fa=(-8.0, 15.0), ff=(12.0, 0.0, 0.0), nf=(-9.0, 0.0, 12.0),
                mouth="big", tail=160.0, hem=(4.0, 1.0))
    return keys(_shot(i, n), [(0.0, GUARD), (0.25, wind), (0.5, push), (0.75, push), (1.0, GUARD)])


@row
def slash(i: int, n: int) -> Pose:
    # The summation sweep: his arm comes over from behind his head to the
    # ground in front of him.
    u = _shot(i, n)
    a = math.radians(lerp(-140.0, 58.0, ease(max(0.0, min(1.0, (u - 0.2) / 0.5)))))
    hand = (28.0 * math.cos(a), 28.0 * math.sin(a))
    swing = ease(max(0.0, min(1.0, (u - 0.2) / 0.5)))
    base = dict(GUARD, hip=(lerp(-2.0, 4.0, swing), 3.0), lean=lerp(-8.0, 16.0, swing), na=hand, nab=-1.0 if hand[1] < -6.0 and hand[0] < 6.0 else 1.0,
                arm="under" if hand[1] < -4.0 and hand[0] > -14.0 else "over", nh="flat", fa=(lerp(14.0, -9.0, swing), 12.0),
                ff=(lerp(7.0, 11.0, swing), 0.0, 0.0), mouth="open" if 0.2 < u < 0.8 else "flat", tail=lerp(70.0, 160.0, swing),
                hem=(3.0 * swing, 1.0))
    if u > 0.85:
        return blend(base, GUARD, ease((u - 0.85) / 0.15))
    return base


@row
def attack_side(i: int, n: int) -> Pose:
    wind = dict(GUARD, hip=(-4.0, 4.0), lean=-9.0, na=(-13.0, 9.0), fa=(-7.0, 12.0), nh="open", fh="open", tail=70.0)
    lunge = dict(GUARD, hip=(6.0, 5.0), lean=17.0, na=(27.0, 1.0), fa=(24.0, 7.0), nh="open", fh="open", nf=(-11.0, 0.0, 16.0),
                 ff=(14.0, 0.0, 0.0), eyes="wide", mouth="big", tail=170.0, hem=(5.0, 1.0))
    return keys(_shot(i, n), [(0.0, GUARD), (0.25, wind), (0.45, lunge), (0.8, lunge), (1.0, GUARD)])


@row
def attack_up(i: int, n: int) -> Pose:
    low = dict(GUARD, hip=(0.0, 9.0), lean=10.0, na=(10.0, 20.0), nh="point", tail=108.0)
    up = dict(GUARD, hip=(0.0, -1.0), lean=-4.0, head=(0.0, 0.0, -12.0), na=(-11.0, -26.0), nab=-1.0, nh="point", fa=(-8.0, 16.0), nf=(-5.0, 0.0, 14.0),
              ff=(6.0, -1.0, 16.0), mouth="open", brows=1.0, tail=96.0, wave=5.0)
    return keys(_shot(i, n), [(0.0, GUARD), (0.25, low), (0.45, up), (0.8, up), (1.0, GUARD)])


@row
def attack_down(i: int, n: int) -> Pose:
    high = dict(GUARD, hip=(-1.0, 0.0), lean=-8.0, head=(0.0, 0.0, -8.0), na=(-12.0, -25.0), nab=-1.0, nh="open", tail=92.0)
    slam = dict(GUARD, hip=(3.0, 11.0), lean=24.0, head=(1.0, 0.0, -6.0), na=(18.0, 22.0), nh="open", fa=(-9.0, 13.0), nf=(-9.0, 0.0, 0.0),
                ff=(9.0, 0.0, 0.0), mouth="big", tail=250.0, wave=8.0, hem=(3.0, 3.0))
    return keys(_shot(i, n), [(0.0, GUARD), (0.3, high), (0.5, slam), (0.85, dict(slam, tail=120.0)), (1.0, HALF_UP)])


AIR = P(hip=(0.0, -3.0), nf=(-4.0, -8.0, 20.0), ff=(6.0, -12.0, 8.0), na=(8.0, 13.0), fa=(14.0, 11.0), nh="fist", fh="fist", brows=-1.0,
        mouth="flat", tail=150.0, hem=(2.0, 2.0))


@row
def air_neutral(i: int, n: int) -> Pose:
    # Arms out, and his symbols go around him.
    _, s, _c = _loop(i, n)
    return dict(AIR, lean=6.0 * s, na=(-22.0, -5.0 + 2.0 * s), nab=-1.0, fa=(23.0, -7.0 - 2.0 * s), nh="open", fh="open", eyes="happy", mouth="open",
                tail=150.0 + 60.0 * s, wave=12.0)


@row
def air_forward(i: int, n: int) -> Pose:
    kick = dict(AIR, lean=-18.0, hip=(-1.0, -3.0), leg="over", nf=(30.0, -37.0, -78.0), ff=(-2.0, -17.0, 34.0), na=(-16.0, 9.0), fa=(10.0, 16.0),
                mouth="open", tail=176.0, wave=5.0, hem=(1.0, 5.0))
    return keys(_shot(i, n), [(0.0, AIR), (0.35, kick), (0.7, kick), (1.0, AIR)])


@row
def air_back(i: int, n: int) -> Pose:
    kick = dict(AIR, lean=27.0, head=(0.0, 0.0, -24.0), leg="over", nf=(-33.0, -33.0, 96.0), ff=(7.0, -16.0, 0.0), na=(16.0, 12.0), fa=(19.0, 6.0),
                mouth="open", tail=20.0, wave=6.0, hem=(6.0, 0.0))
    return keys(_shot(i, n), [(0.0, AIR), (0.35, kick), (0.7, kick), (1.0, AIR)])


@row
def air_down(i: int, n: int) -> Pose:
    dive = dict(AIR, hip=(0.0, 0.0), off=(0.0, -13.0), nf=(-1.5, 0.0, 58.0), ff=(3.0, 0.0, 52.0), na=(-15.0, -22.0), nab=-1.0, fa=(18.0, -20.0), nh="open",
                fh="open", mouth="open", tail=268.0, wave=8.0, curl=0.0, hem=(3.0, 3.0))
    return keys(_shot(i, n), [(0.0, AIR), (0.3, dive), (0.8, dive), (1.0, AIR)])


@row
def air_up(i: int, n: int) -> Pose:
    reach = dict(AIR, lean=-5.0, head=(0.0, 0.0, -12.0), na=(-11.0, -26.0), nab=-1.0, nh="point", fa=(-9.0, 14.0), nf=(-6.0, -2.0, 36.0), ff=(4.0, -8.0, 22.0),
                 mouth="open", brows=1.0, tail=94.0, wave=5.0)
    return keys(_shot(i, n), [(0.0, AIR), (0.3, reach), (0.75, reach), (1.0, AIR)])


CHARGE = P(hip=(0.0, 1.0), head=(0.0, 0.0, -7.0), na=(10.0, 4.0), fa=(10.0, 6.0), nh="flat", fh="flat", eyes="closed", tail=205.0, wave=13.0,
           curl=-2.0, hem=(1.0, 1.0))


@row
def charge(i: int, n: int) -> Pose:
    # The theorem arrives: eyes shut, hands together, and his scarf lifts.
    _, s, _c = _loop(i, n)
    return dict(CHARGE, hip=(0.0, 1.0 + 0.6 * s), head=(0.0, 0.3 * s, -7.0 + 1.5 * s))


@row
def cast(i: int, n: int) -> Pose:
    out = P(hip=(3.0, 3.0), lean=10.0, head=(1.0, 0.0, -4.0), na=(27.0, 0.0), fa=(24.0, 6.0), nh="open", fh="open", nf=(-9.0, 0.0, 10.0),
            ff=(10.0, 0.0, 0.0), eyes="wide", mouth="big", brows=1.0, tail=178.0, wave=10.0, curl=0.0, hem=(5.0, 1.0))
    return keys(_shot(i, n), [(0.0, CHARGE), (0.3, out), (1.0, dict(out, hip=(2.0, 3.0), lean=7.0))])


@row
def celebrate(i: int, n: int) -> Pose:
    ph, s, _c = _loop(i, n)
    up = abs(math.sin(ph))
    return P(off=(0.0, -9.0 * up), hip=(0.0, 3.0 * (1.0 - up)), head=(0.0, 0.0, -6.0), na=(-16.0, -22.0 + 2.0 * s), nab=-1.0, fa=(19.0, -20.0 - 2.0 * s),
             nh="open", fh="open", nf=(-6.0, -4.0 * up, 24.0 * up), ff=(7.0, -6.0 * up, 14.0 * up), eyes="happy", mouth="big",
             tail=lerp(110.0, 230.0, up), wave=12.0, hem=(2.0 * up, 2.0 * up))


@row
def taunt(i: int, n: int) -> Pose:
    # Hands together and a small bow: he means it kindly.
    together = P(na=(10.0, 4.0), fa=(10.0, 6.0), nh="flat", fh="flat", eyes="happy")
    bow = dict(together, hip=(-1.0, 2.0), lean=19.0, head=(1.0, 1.0, 9.0), eyes="closed", tail=84.0, hem=(2.0, 0.0))
    return keys(_shot(i, n), [(0.0, P()), (0.2, together), (0.5, bow), (0.75, bow), (1.0, together)])


ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 145),
    ("walk", 8, 104),
    ("run", 8, 78),
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
    ("death", 8, 110),
    ("talk", 8, 108),
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
    ("charge", 8, 76),
    ("cast", 8, 80),
    ("celebrate", 8, 92),
    ("taunt", 8, 95),
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


def _hand(mode: str, near: bool):
    """A hand along +x from its wrist at ``home``, with the cuff of its sleeve."""
    skin = SKIN if near else SKIN_SHADE
    h = K.home

    def shape(d) -> None:
        K.rrect(d, h[0] - 2.4, h[1] - 3.5, h[0] + 1.4, h[1] + 3.5, 1.2, WHITE)
        if mode == "flat":
            K.oval(d, K.at(5.2, 0.0), 5.2, 2.7, WHITE)
        elif mode == "fist":
            K.oval(d, K.at(3.6, 0.0), 3.7, 3.6, WHITE)
        else:
            K.oval(d, K.at(3.6, 0.0), 3.8, 3.3, WHITE)
        if mode == "soft":
            K.stroke(d, [K.at(3.0, -2.0), K.at(5.4, -3.6)], WHITE, 2.2)
        elif mode == "point":
            K.stroke(d, [K.at(4.5, -0.6), K.at(10.4, -1.2)], WHITE, 2.3)
            K.stroke(d, [K.at(3.0, 2.0), K.at(5.0, 3.6)], WHITE, 2.1)
        elif mode == "open":
            for dy, reach in ((-3.2, 8.4), (-1.1, 9.8), (1.1, 9.6), (3.1, 8.2)):
                K.stroke(d, [K.at(4.4, dy * 0.6), K.at(reach, dy * 1.25)], WHITE, 2.0)
            K.stroke(d, [K.at(2.6, -2.4), K.at(4.4, -5.6)], WHITE, 2.1)

    def detail(d) -> None:
        K.rrect(d, h[0] - 3.0, h[1] - 4.0, h[0] + 1.4, h[1] + 4.0, 0.0, LINING if near else LINING_DARK)
        if mode == "fist":
            K.line(d, [K.at(4.4, -2.0), K.at(5.6, 0.0), K.at(4.4, 2.0)], SKIN_DEEP, 0.6)
        if mode == "open":
            for dy in (-1.0, 1.0):
                K.line(d, [K.at(5.2, dy * 0.9), K.at(7.6, dy * 1.5)], SKIN_DEEP, 0.4)

    return K.solid(("hand", mode, near), shape, skin, detail, outline=1.1, rim=0.3, shade=0.3, shade_colour=SKIN_DEEP)


def _shoe(near: bool):
    """A shoe from its ankle at ``home``; its sole is ``ANKLE_UP`` under it."""
    h = K.home

    def shape(d) -> None:
        K.oval(d, K.at(3.0, 0.6), 6.6, 3.3, WHITE)
        K.rrect(d, h[0] - 3.6, h[1] - 0.4, h[0] + 9.4, h[1] + ANKLE_UP + 0.4, 1.6, WHITE)
        K.oval(d, h, 3.2, 3.0, WHITE)

    def detail(d) -> None:
        K.rrect(d, h[0] - 5.0, h[1] + ANKLE_UP - 1.0, h[0] + 11.0, h[1] + ANKLE_UP + 2.0, 0.0, SHOE_DARK)
        K.line(d, [K.at(2.0, -1.4), K.at(6.0, -0.6)], mix(SHOE, WHITE, 0.35), 0.8)

    return K.solid(("shoe", near), shape, SHOE if near else mix(SHOE, SHOE_DARK, 0.6), detail, outline=1.2, rim=0.25, shade=0.3,
                   shade_colour=SHOE_DARK)


def _coat(hem_back: int, hem_front: int):
    """His coat from his hips at ``home``, his spine straight up. The hem is
    ``hem_back`` and ``hem_front`` wider than it hangs."""
    hb, hf = float(hem_back), float(hem_front)
    back_hem, front_hem = K.at(-12.5 - hb, 10.6), K.at(13.0 + hf, 10.0)
    split_top, split = K.at(8.2, -1.0), K.at(8.4 + hf * 0.7, 10.2)

    def shape(d) -> None:
        K.poly(d, [K.at(-5.5, -31.0), K.at(-10.5, -27.0), K.at(-11.0, -14.0), K.at(-10.4, -4.0), back_hem, front_hem, K.at(13.2, -3.0),
                   K.at(12.2, -15.0), K.at(10.5, -26.5), K.at(5.5, -31.5)], WHITE)
        K.oval(d, K.at(-5.6, -25.6), 5.6, 5.8, WHITE)
        K.oval(d, K.at(5.6, -25.6), 5.8, 6.0, WHITE)
        K.oval(d, K.at(2.6, -8.0), 11.2, 10.5, WHITE)

    def detail(d) -> None:
        # The far side of his chest is in his own shade.
        K.poly(d, [K.at(8.0, -34.0), K.at(16.0, -34.0), K.at(18.0 + hf, 12.0), K.at(8.4 + hf * 0.7, 12.0), split_top, K.at(6.8, -22.0)], COAT_DARK)
        # The lining, where the coat opens under its last button.
        K.poly(d, [split_top, (split[0] - 3.4, split[1] + 2.0), (split[0] + 2.6, split[1] + 2.0)], LINING)
        K.line(d, [K.at(6.4, -31.0), K.at(6.8, -22.0), split_top], COAT_LIGHT, 0.9)
        for k in range(4):
            t = k / 3.0
            K.oval(d, K.at(lerp(6.5, 8.0, t), lerp(-25.0, -4.0, t)), 1.5, 1.5, CARROT, OUTLINE, 0.4)
        # The hem's gold band.
        K.poly(d, [(back_hem[0] - 2.0, back_hem[1] - 2.6), (front_hem[0] + 2.0, front_hem[1] - 2.6), (front_hem[0] + 2.0, front_hem[1] + 3.0),
                   (back_hem[0] - 2.0, back_hem[1] + 3.0)], SESAME)
        # Gold dots, joined: a constellation, or a partition, or sesame.
        stars = [K.at(-6.0, -19.0), K.at(-2.0, -11.5), K.at(-7.0, -5.0), K.at(-1.0, 0.5), K.at(-6.5, 5.0)]
        K.line(d, stars, mix(COAT, SESAME, 0.4), 0.45)
        for k, p in enumerate(stars):
            K.oval(d, p, 1.1 if k % 2 == 0 else 0.8, 1.1 if k % 2 == 0 else 0.8, SESAME)

    return K.solid(("coat", hem_back, hem_front), shape, COAT, detail, outline=1.3, rim=0.3, shade=0.4, shade_colour=COAT_DARK)


def _wrap():
    """His scarf where it goes around his neck, from the base of his neck."""

    def shape(d) -> None:
        K.oval(d, K.at(0.8, 0.4), 10.0, 4.6, WHITE)
        K.oval(d, K.at(-8.8, 1.6), 3.7, 3.6, WHITE)

    def detail(d) -> None:
        for dy in (-0.8, 1.8):
            K.line(d, [K.at(-8.0, dy + 0.6), K.at(0.0, dy + 2.0), K.at(9.0, dy)], NOODLE_DARK, 0.6)

    return K.solid(("wrap",), shape, NOODLE, detail, outline=1.2, rim=0.4, shade=0.45, shade_colour=NOODLE_DARK)


LINK = 5.2


def _tails(chains: Tuple[Tuple[Point, ...], ...]):
    """Both tails of his scarf as ONE piece, painted where they hang: each of
    ``chains`` is a tail's points from ``home``. Each ends in three loose
    noodles.

    One piece, cut and placed on whole frame pixels (``Kit.aligned``), because
    a tail made of turned links is a long cream edge on a dark line, and a
    part flipbook does not reproduce that edge link by link (measured
    2026-10-11: blobs of 8 to 12 wrong pixels along it; 6 are allowed)."""
    chains = tuple(tuple((round(x, 1), round(y, 1)) for x, y in chain) for chain in chains)

    def paint(d) -> None:
        paths = []
        for chain in chains:
            pts = [K.at(x, y) for x, y in chain]
            (ax, ay), (bx, by) = pts[-2], pts[-1]
            along = math.atan2(by - ay, bx - ax)
            strands = []
            for side, reach in ((-1.7, 7.0), (0.0, 8.6), (1.7, 6.4)):
                strand = []
                for t in range(6):
                    u, v = reach * t / 5.0, side * (1.0 + 0.1 * t) + 0.9 * math.sin(t * 1.5 + side)
                    strand.append((bx + u * math.cos(along) - v * math.sin(along), by + u * math.sin(along) + v * math.cos(along)))
                strands.append(strand)
            paths.append((pts, strands))
        for pts, strands in paths:
            K.stroke(d, pts, OUTLINE, 5.0 + 2.4)
            for strand in strands:
                K.stroke(d, strand, OUTLINE, 3.0)
        for pts, strands in paths:
            K.stroke(d, pts, NOODLE, 5.0)
            for strand in strands:
                K.stroke(d, strand, NOODLE, 1.4)
        for pts, _strands in paths:
            K.line(d, [(x, y + 1.1) for x, y in pts], mix(NOODLE, NOODLE_DARK, 0.6), 0.9)

    return K.aligned(("tails", chains), paint)


NEAR_EYE: Point = (0.6, 0.8)
FAR_EYE: Point = (10.4, 0.5)


def _head():
    """His head, from its middle: the skull, the hair, an ear, a nose."""

    def lock(d, fill: RGBA, width: float) -> None:
        K.stroke(d, [K.at(2.0, -16.0), K.at(-1.4, -21.0), K.at(4.0, -24.4), K.at(-0.6, -28.4), K.at(4.6, -31.6), K.at(7.4, -29.4)], fill, width)

    def shape(d) -> None:
        K.oval(d, K.at(0.0, -1.0), 17.0, 16.5, WHITE)
        K.oval(d, K.at(2.6, 5.0), 14.6, 12.6, WHITE)
        K.oval(d, K.at(-3.0, -5.5), 18.4, 15.2, WHITE)
        K.oval(d, K.at(-11.0, 3.6), 4.2, 5.4, WHITE)
        lock(d, WHITE, 1.2)

    def detail(d) -> None:
        # The far cheek is in shade.
        K.oval(d, K.at(17.5, 6.0), 5.0, 12.0, mix(SKIN, SKIN_SHADE, 0.6))
        hairline = [K.at(18.5, -6.0), K.at(13.6, -11.6), K.at(7.0, -14.6), K.at(0.0, -11.4), K.at(-6.0, -8.6), K.at(-9.4, -3.0),
                    K.at(-10.2, 4.0), K.at(-14.0, 7.5), K.at(-12.6, 15.0), K.at(-34.0, 15.0), K.at(-34.0, -44.0), K.at(34.0, -44.0),
                    K.at(34.0, -6.0)]
        K.poly(d, hairline, HAIR)
        # The side-swept lock over his brow.
        K.poly(d, [K.at(7.0, -14.6), K.at(13.6, -11.6), K.at(17.0, -5.6), K.at(12.4, -8.8), K.at(8.6, -10.6)], HAIR)
        K.line(d, [K.at(-11.0, -15.0), K.at(-3.0, -19.4), K.at(6.0, -18.4), K.at(12.0, -14.6)], HAIR_LIGHT, 1.2)
        K.line(d, [K.at(-15.6, -8.0), K.at(-17.0, -1.0), K.at(-16.0, 6.0)], HAIR_LIGHT, 1.0)
        K.line(d, [K.at(7.0, -14.4), K.at(3.0, -17.6)], HAIR_LIGHT, 0.6)
        # His ear, over his hair.
        K.oval(d, K.at(-10.6, 3.6), 3.4, 4.7, SKIN, OUTLINE, 0.7)
        K.line(d, [K.at(-11.4, 1.6), K.at(-9.8, 3.6), K.at(-11.0, 5.6)], SKIN_DEEP, 0.6)
        K.oval(d, K.at(-3.4, 8.6), 3.0, 1.9, BLUSH)
        K.oval(d, K.at(12.4, 7.8), 2.4, 1.8, BLUSH)
        K.line(d, [K.at(6.6, 2.6), K.at(8.0, 5.6), K.at(6.0, 6.4)], SKIN_DEEP, 0.9)

    return K.solid(("head",), shape, SKIN, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=SKIN_DEEP)


def _eyes(mode: str):
    def paint(d) -> None:
        for (ex, ey), rx, ry in ((NEAR_EYE, 3.6, 4.5), (FAR_EYE, 2.8, 4.2)):
            c = K.at(ex, ey)
            if mode == "closed":
                K.line(d, [(c[0] - rx, c[1] - 0.2), (c[0], c[1] + 1.8), (c[0] + rx, c[1] - 0.2)], INK, 1.3)
                continue
            if mode == "happy":
                K.line(d, [(c[0] - rx, c[1] + 1.4), (c[0], c[1] - 1.8), (c[0] + rx, c[1] + 1.4)], INK, 1.4)
                continue
            if mode == "wince":
                side = 1.0 if ex < 6.0 else -1.0
                K.line(d, [(c[0] - rx * side, c[1] - 2.4), (c[0] + rx * 0.6 * side, c[1]), (c[0] - rx * side, c[1] + 2.4)], INK, 1.3)
                continue
            tall = ry + (0.9 if mode == "wide" else 0.0)
            K.oval(d, c, rx, tall, EYE_WHITE, INK, 0.7)
            small = 0.72 if mode == "wide" else 1.0
            ic = (c[0] + 0.8, c[1] + (-1.5 if mode == "up" else 0.3))
            K.oval(d, ic, rx * 0.72 * small, ry * 0.76 * small, IRIS)
            K.oval(d, ic, rx * 0.44 * small, ry * 0.5 * small, INK)
            K.oval(d, (ic[0] - 0.9, ic[1] - 1.5), 1.05, 1.05, WHITE)
            K.oval(d, (ic[0] + 0.9, ic[1] + 1.5), 0.5, 0.5, WHITE)
            K.line(d, [(c[0] - rx - 0.5, c[1] - 1.4), (c[0] - rx * 0.4, c[1] - tall + 0.2), (c[0] + rx * 0.5, c[1] - tall + 0.2),
                       (c[0] + rx + 0.4, c[1] - 1.6)], INK, 1.3)

    return K.piece(("eyes", mode), paint)


def _brows(mood: int):
    """His brows: 0 level, 1 raised, -1 set."""

    def paint(d) -> None:
        up = -1.6 if mood > 0 else 0.0
        inner = 1.5 if mood < 0 else 0.0
        K.stroke(d, [K.at(-4.0, -6.2 + up), K.at(0.4, -7.4 + up), K.at(4.4, -6.6 + up + inner)], HAIR, 1.7)
        K.stroke(d, [K.at(7.8, -6.8 + up + inner), K.at(10.8, -7.6 + up), K.at(13.6, -6.2 + up)], HAIR, 1.6)

    return K.piece(("brows", mood), paint)


def _mouth(mode: str):
    c = K.at(5.8, 10.4)

    def paint(d) -> None:
        if mode == "smile":
            K.line(d, [(c[0] - 3.6, c[1] - 0.9), (c[0] - 0.4, c[1] + 1.1), (c[0] + 3.2, c[1] - 1.1)], MOUTH, 1.0)
        elif mode == "flat":
            K.line(d, [(c[0] - 2.8, c[1]), (c[0] + 2.6, c[1] - 0.2)], MOUTH, 1.0)
        elif mode == "o":
            K.oval(d, c, 1.7, 2.0, MOUTH, INK, 0.5)
        elif mode == "grit":
            K.rrect(d, c[0] - 3.4, c[1] - 1.5, c[0] + 3.2, c[1] + 1.5, 1.0, EYE_WHITE, INK, 0.6)
            for dx in (-1.2, 1.0):
                K.line(d, [(c[0] + dx, c[1] - 1.4), (c[0] + dx, c[1] + 1.4)], INK, 0.4)
        else:
            ry = 3.3 if mode == "big" else 2.1
            K.oval(d, (c[0], c[1] + 0.4), 3.2 if mode == "big" else 2.6, ry, MOUTH, INK, 0.6)
            K.oval(d, (c[0], c[1] + 0.4 + ry * 0.5), 1.8, ry * 0.42, TONGUE)

    return K.piece(("mouth", mode), paint)


# ---- His mathematics ---------------------------------------------------------


def _chalk(key: tuple, shape: Callable, fill: RGBA = DREAM):
    return K.solid(("chalk",) + key, shape, fill, None, outline=1.1, rim=0.6, shade=0.5, shade_colour=DREAM_DARK)


def _sigma(size: float):
    def shape(d) -> None:
        k = size / 5.0
        K.stroke(d, [K.at(4.0 * k, -5.0 * k), K.at(-4.0 * k, -5.0 * k), K.at(1.0 * k, 0.0), K.at(-4.0 * k, 5.0 * k), K.at(4.0 * k, 5.0 * k)], WHITE,
                 max(1.5, size * 0.36))

    return _chalk(("sigma", size), shape)


def _bang(size: float):
    def shape(d) -> None:
        k = size / 5.0
        K.poly(d, [K.at(-1.5 * k, -5.6 * k), K.at(1.5 * k, -5.6 * k), K.at(0.7 * k, 1.6 * k), K.at(-0.7 * k, 1.6 * k)], WHITE)
        K.oval(d, K.at(0.0, 4.4 * k), 1.3 * k, 1.3 * k, WHITE)

    return _chalk(("bang", size), shape, mix(DREAM, CARROT, 0.35))


def _burst(size: float):
    """The lines that fly out of a factorial."""

    def shape(d) -> None:
        for k in range(8):
            a = math.radians(k * 45.0 + 22.5)
            K.stroke(d, [K.at(math.cos(a) * size * 0.62, math.sin(a) * size * 0.62), K.at(math.cos(a) * size, math.sin(a) * size)], WHITE, 1.5)

    return _chalk(("burst", size), shape, DREAM_PALE)


def _infinity(size: float):
    def shape(d) -> None:
        pts = []
        for k in range(33):
            t = math.tau * k / 32.0
            den = 1.0 + math.sin(t) ** 2
            pts.append(K.at(size * math.cos(t) / den, size * 0.9 * math.sin(t) * math.cos(t) / den))
        K.stroke(d, pts, WHITE, max(1.4, size * 0.26))

    return _chalk(("infinity", size), shape, mix(DREAM, LINING, 0.45))


def _bracket(size: float):
    """The closing bracket he blocks with."""

    def shape(d) -> None:
        pts = [K.at(-size * 0.42 + size * 0.6 * math.cos(math.radians(a)), size * math.sin(math.radians(a))) for a in range(-66, 67, 6)]
        K.stroke(d, pts, WHITE, 3.2)

    return _chalk(("bracket", size), shape)


def _partition():
    """The dots of a partition: 4 + 3 + 1."""

    def shape(d) -> None:
        for r, count in enumerate((4, 3, 1)):
            for c in range(count):
                K.oval(d, K.at(c * 3.6, r * 3.6), 1.25, 1.25, WHITE)

    return _chalk(("partition",), shape, mix(DREAM, LINING, 0.5))


def _seal(radius: float):
    """The ``-1/12`` seal."""
    r = radius

    def disc(d) -> None:
        K.oval(d, K.home, r, r, (255, 240, 180, 84))

    def shape(d) -> None:
        K.oval(d, K.home, r, r, None, WHITE, 1.5)  # type: ignore[arg-type]
        w = max(1.2, r * 0.14)
        K.stroke(d, [K.at(-0.74 * r, 0.0), K.at(-0.44 * r, 0.0)], WHITE, w)
        K.stroke(d, [K.at(-0.02 * r, -0.5 * r), K.at(0.16 * r, -0.64 * r), K.at(0.16 * r, -0.16 * r)], WHITE, w)
        K.stroke(d, [K.at(-0.24 * r, 0.02 * r), K.at(0.62 * r, 0.02 * r)], WHITE, w * 0.8)
        K.stroke(d, [K.at(-0.1 * r, 0.22 * r), K.at(-0.1 * r, 0.66 * r)], WHITE, w)
        K.stroke(d, [K.at(0.12 * r, 0.3 * r), K.at(0.3 * r, 0.2 * r), K.at(0.46 * r, 0.32 * r), K.at(0.14 * r, 0.66 * r), K.at(0.5 * r, 0.66 * r)], WHITE, w)

    return K.piece(("seal_disc", r), disc), _chalk(("seal", r), shape)


def _swoosh(radius: float, a0: int, a1: int, width: float):
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

    return _chalk(("swoosh", radius, a0, a1, width), shape, DREAM_PALE)


def _noodle(length: int):
    """A line of chalk that is also a noodle, along +x."""

    def shape(d) -> None:
        K.stroke(d, [K.at(x, 2.2 * math.sin(x * 0.5)) for x in range(0, length + 1, 2)], WHITE, 2.4)

    return _chalk(("noodle", length), shape, NOODLE)


def _sparkle(size: float):
    def paint(d) -> None:
        K.star4(d, K.home, size, DREAM)
        K.star4(d, K.home, size * 0.45, DREAM_PALE, None, 0.0, 0.4)

    return K.piece(("sparkle", size), paint)


def _tick(size: float):
    return _chalk(("tick", size), lambda d: K.tick(d, K.home, size, WHITE, max(1.4, size * 0.4)), mix(DREAM, LINING, 0.55))


def _bubble(size: float, glyph: bool = True):
    """The cloud a theorem arrives in."""
    k = size

    def shape(d) -> None:
        for x, y, r in ((-7.0, 1.0, 6.4), (0.0, -3.0, 8.0), (7.4, 0.6, 6.6), (0.0, 3.4, 7.4), (-3.6, -1.0, 7.0), (4.0, 2.6, 6.4)):
            K.oval(d, K.at(x * k, y * k), r * k, r * k * 0.92, WHITE)

    def detail(d) -> None:
        if glyph:
            s = 4.6 * k
            K.stroke(d, [K.at(0.8 * s, -s), K.at(-0.8 * s, -s), K.at(0.2 * s, 0.0), K.at(-0.8 * s, s), K.at(0.8 * s, s)], COAT, 1.7 * k)

    return K.solid(("bubble", size, glyph), shape, CLOUD, detail, outline=1.1, rim=0.5, shade=0.5, shade_colour=CLOUD_DARK)


def _puff(radius: float):
    return K.solid(("puff", radius), lambda d: K.oval(d, K.home, radius, radius, WHITE), CLOUD, None, outline=1.0, rim=0.4, shade=0.5,
                   shade_colour=CLOUD_DARK)


Stamp = Tuple[object, Point, str, float]


def _effects(anim: str, i: int, n: int, at: Dict[str, Point]) -> List[Stamp]:
    """What his mathematics draws this frame, over him."""
    out: List[Stamp] = []
    u = _shot(i, n)
    ph = math.tau * i / max(1, n)
    hand, far_hand, head, hip, foot, shoulder = at["hand"], at["far_hand"], at["head"], at["hip"], at["foot"], at["shoulder"]

    def stamp(part, p: Point, name: str, degrees: float = 0.0) -> None:
        out.append((part, p, name, degrees))

    def sparkles(points: List[Tuple[float, float, float]], origin: Point) -> None:
        for k, (x, y, r) in enumerate(points):
            size = r * (0.5 + 0.5 * math.sin(ph + k * 2.1) ** 2)
            stamp(_sparkle(round(size * 2.0) / 2.0 + 1.0), (origin[0] + x, origin[1] + y), f"sparkle_{k}")

    if anim == "jab" and 1 <= i <= 3:
        stamp(_sigma(4.5), (hand[0] + 15.0, hand[1] - 1.0), "sigma")
        stamp(_sparkle(3.0), (hand[0] + 23.0, hand[1] - 8.0), "sparkle_0")
    elif anim == "punch" and 3 <= i <= 5:
        grow = float(i - 3)
        stamp(_burst(9.0 + 2.0 * grow), (hand[0] + 16.0, hand[1] - 1.0), "burst")
        stamp(_bang(6.0 + grow), (hand[0] + 16.0, hand[1] - 1.0), "bang")
    elif anim in ("slash", "ledge_getup_attack"):
        lo, hi = (2, 5) if anim == "slash" else (4, 6)
        if lo <= i <= hi:
            a = math.degrees(math.atan2(hand[1] - shoulder[1], hand[0] - shoulder[0]))
            lead = int(round(a / 5.0)) * 5
            sweep = 100 if anim == "slash" else 60
            stamp(_swoosh(42.0, lead - sweep, lead + 6, 10.0), shoulder, "swoosh")
            tip = math.radians(lead + 12.0)
            stamp(_sigma(6.5), (shoulder[0] + 46.0 * math.cos(tip), shoulder[1] + 46.0 * math.sin(tip)), "sigma")
    elif anim == "attack_side" and 3 <= i <= 6:
        grow = float(i - 3)
        centre = (hand[0] + 17.0 + 2.0 * grow, hand[1] + 1.0)
        stamp(_burst(11.0 + 2.0 * grow), centre, "burst")
        stamp(_bang(8.0 + grow), centre, "bang")
        stamp(_sigma(4.0), (centre[0] - 4.0, centre[1] + 17.0), "sigma")
    elif anim in ("attack_up", "air_up") and 3 <= i <= 6:
        rise = 4.0 * (i - 3)
        stamp(_bang(7.0), (hand[0] + 2.0, hand[1] - 20.0 - rise), "bang")
        stamp(_swoosh(11.0, 200, 340, 4.0), (hand[0] + 2.0, hand[1] - 12.0 - rise), "swoosh")
        sparkles([(-10.0, -16.0, 3.0), (13.0, -22.0, 3.0)], hand)
    elif anim == "attack_down" and i >= 4:
        r = min(11.0, 7.0 + 1.5 * (i - 4))
        disc, seal = _seal(r)
        centre = (hand[0] + 9.0, GROUND - 10.0)
        stamp(disc, centre, "seal_disc")
        stamp(seal, centre, "seal")
        sparkles([(-14.0, -12.0, 3.0), (15.0, -14.0, 3.0)], centre)
    elif anim == "air_down" and 2 <= i <= 5:
        disc, seal = _seal(8.0 + 0.5 * (i % 2))
        centre = (hip[0] + 1.0, GROUND - 6.0)
        stamp(disc, centre, "seal_disc")
        stamp(seal, centre, "seal")
    elif anim == "air_neutral":
        for k, part in enumerate((_sigma(4.5), _bang(4.5), _infinity(6.0))):
            a = ph + k * math.tau / 3.0
            stamp(part, (hip[0] + 34.0 * math.cos(a), hip[1] - 16.0 + 11.0 * math.sin(a)), ("sigma", "bang", "infinity")[k])
    elif anim == "air_forward" and 2 <= i <= 4:
        stamp(_swoosh(13.0, -70, 70, 5.0), (foot[0] + 2.0, foot[1]), "swoosh")
        stamp(_sparkle(3.5), (foot[0] + 20.0, foot[1] - 6.0), "sparkle_0")
    elif anim == "air_back" and 2 <= i <= 4:
        stamp(_burst(8.0), (foot[0] - 10.0, foot[1]), "burst")
        stamp(_bang(5.0), (foot[0] - 10.0, foot[1]), "bang")
    elif anim == "block":
        stamp(_bracket(18.0 + (i % 2)), (hip[0] + 38.0, hip[1] - 20.0), "bracket")
    elif anim == "interact" and 3 <= i <= 5:
        stamp(_tick(4.0), (hand[0] + 14.0, hand[1] - 5.0), "tick")
    elif anim == "charge":
        pulse = (1.0, 1.06, 1.12, 1.06)[i % 4]
        stamp(_puff(2.0), (head[0] - 13.0, head[1] - 22.0), "puff_0")
        stamp(_puff(3.2), (head[0] - 19.0, head[1] - 28.0), "puff_1")
        stamp(_bubble(pulse), (head[0] - 26.0, head[1] - 42.0), "bubble")
        sparkles([(16.0, -30.0, 3.5), (-44.0, -30.0, 3.0), (24.0, -8.0, 2.5)], head)
    elif anim == "cast":
        if i < 2:
            stamp(_puff(2.0), (head[0] - 13.0, head[1] - 22.0), "puff_0")
            stamp(_bubble(1.12 - 0.3 * i, glyph=i == 0), (head[0] - 26.0 + 14.0 * i, head[1] - 42.0 + 10.0 * i), "bubble")
        else:
            go = (i - 2) / max(1, n - 3)
            mid = ((hand[0] + far_hand[0]) / 2.0 + 8.0, (hand[1] + far_hand[1]) / 2.0)
            reach = 4 * int(round((8.0 + 16.0 * go) / 4.0))
            stamp(_noodle(reach), mid, "noodle", -6.0)
            stamp(_sigma(7.0 + 3.0 * go), (mid[0] + reach + 11.0, mid[1] - 4.0 - 3.0 * go), "sigma")
            stamp(_partition(), (mid[0] + 6.0 + 14.0 * go, mid[1] + 10.0 + 4.0 * go), "partition")
            sparkles([(reach + 8.0, -20.0, 3.5), (reach - 6.0, 16.0, 3.0)], mid)
    elif anim == "celebrate":
        sparkles([(-30.0, -34.0, 4.0), (30.0, -40.0, 4.5), (38.0, -8.0, 3.0), (-36.0, -4.0, 3.0)], head)
    elif anim == "taunt" and i >= 3:
        sparkles([(14.0, -8.0, 3.0), (20.0, 4.0, 2.5)], hand)
    elif anim == "float_glide":
        sparkles([(-30.0, -4.0, 3.0), (-40.0, 10.0, 2.5), (-24.0, 16.0, 2.5)], hip)
    elif anim == "death" and i >= n - 3:
        k = i - (n - 3)
        stamp(_puff(2.0), (head[0] - 12.0, head[1] - 22.0), "puff_0")
        if k >= 1:
            stamp(_puff(3.0), (head[0] - 17.0, head[1] - 29.0), "puff_1")
        if k >= 2:
            stamp(_bubble(0.8), (head[0] - 22.0, head[1] - 41.0), "bubble")
    return out


# ---- The frame ---------------------------------------------------------------


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = ROW_POSES[anim](frame_idx, nframes)
    img = K.new_frame()
    rot = float(pose["rot"])  # type: ignore[arg-type]
    lean = float(pose["lean"])  # type: ignore[arg-type]
    hx, hy = pose["hip"]  # type: ignore[misc]
    ox, oy = pose["off"]  # type: ignore[misc]
    hip = (hx, -HIP_UP + hy)
    px, py = pose["pivot"]  # type: ignore[misc]
    pivot = (hip[0] + px, hip[1] + py)

    def W(p: Point) -> Point:
        """A point of him (from the ground under him) in the frame."""
        r = turned((p[0] - pivot[0], p[1] - pivot[1]), rot)
        return (CX + ox + pivot[0] + r[0], GROUND + oy + pivot[1] + r[1])

    def trunk(x: float, y: float) -> Point:
        """A point of his trunk, from his hips, his spine straight up."""
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
        elbow, wrist = solve(shoulder, (shoulder[0] + dx, shoulder[1] + dy), UPPER, FORE, float(pose[key + "b"]))  # type: ignore[arg-type]
        colour = COAT if near else COAT_DARK
        limb(f"{name}_arm", [
            (shoulder, elbow, lambda edge: _bone("upper", UPPER, 7.2, 6.0, colour, COAT_DARK, edge)),
            (elbow, wrist, lambda edge: _bone("fore", FORE, 6.0, 5.4, colour, COAT_DARK, edge)),
        ])
        K.place(img, _hand(str(pose["nh" if near else "fh"]), near), W(wrist), f"{name}_hand", angle(W(elbow), W(wrist)))
        return W(wrist)

    def leg(near: bool) -> Point:
        key, name = ("nf", "near") if near else ("ff", "far")
        root = (hip[0] + (NEAR_HIP if near else FAR_HIP)[0], hip[1])
        fx, fy, toe = pose[key]  # type: ignore[misc]
        knee, ankle = solve(root, (fx, fy - ANKLE_UP), THIGH, SHIN, -1.0)
        colour = TROUSER if near else TROUSER_DARK
        limb(f"{name}_leg", [
            (root, knee, lambda edge: _bone("thigh", THIGH, 7.4, 6.2, colour, TROUSER_DARK, edge)),
            (knee, ankle, lambda edge: _bone("shin", SHIN, 6.2, 5.0, colour, TROUSER_DARK, edge)),
        ])
        K.place(img, _shoe(near), W(ankle), f"{name}_shoe", toe + rot)
        return W(ankle)

    far_hand = arm(False)
    leg(False)
    kicking = pose["leg"] == "over"
    near_foot = (0.0, 0.0) if kicking else leg(True)

    hem = pose["hem"]
    K.place(img, _coat(int(round(max(0.0, hem[0]))), int(round(max(0.0, hem[1])))), W(hip), "coat", lean + rot)  # type: ignore[index]
    if kicking:
        near_foot = leg(True)

    # His scarf's tails, from the knot at the back of his neck. They hang in
    # the world: turning him does not turn them.
    knot = W(trunk(-8.8, -NECK + 1.8))
    phase = math.tau * frame_idx / max(1, nframes)
    held = pin(knot)
    chains = []
    for links, lead, spread in ((7, 0.0, 0.0), (6, 1.7, 13.0)):
        at = (knot[0] - held[0], knot[1] - held[1])
        chain = [at]
        for k in range(links):
            a = float(pose["tail"]) + spread + float(pose["curl"]) * k + float(pose["wave"]) * math.sin(phase - 0.85 * k + lead) * (0.35 + 0.65 * k / links)  # type: ignore[arg-type]
            at = (at[0] + LINK * math.cos(math.radians(a)), at[1] + LINK * math.sin(math.radians(a)))
            chain.append(at)
        chains.append(tuple(chain))
    K.place(img, _tails(tuple(chains)), held, "scarf_tails")

    under = pose["arm"] == "under"
    near_hand = arm(True) if under else (0.0, 0.0)

    neck = trunk(0.8, -NECK)
    hdx, hdy, tilt = pose["head"]  # type: ignore[misc]
    up = turned((1.5, -19.0), lean * 0.5 + tilt * 0.3)
    head = W((neck[0] + up[0] + hdx, neck[1] + up[1] + hdy))
    turn = lean * 0.35 + tilt + rot
    K.place(img, _head(), head, "head", turn)
    K.place(img, _eyes(str(pose["eyes"])), head, "eyes", turn)
    brows = float(pose["brows"])  # type: ignore[arg-type]
    K.place(img, _brows(1 if brows > 0.5 else -1 if brows < -0.5 else 0), head, "brows", turn)
    K.place(img, _mouth(str(pose["mouth"])), head, "mouth", turn)
    K.place(img, _wrap(), W(neck), "scarf", lean + rot)

    if not under:
        near_hand = arm(True)

    at = {"hand": near_hand, "far_hand": far_hand, "head": head, "hip": W(hip), "foot": near_foot, "shoulder": W(trunk(*NEAR_SHOULDER))}
    for part, p, name, degrees in _effects(anim, frame_idx, nframes, at):
        K.place(img, part, p, name, degrees)  # type: ignore[arg-type]
    return K.downsample(img)


#: The body the game moves: his head and his coat, standing.
BODY_BOX = (CX - 17.0, GROUND - HEIGHT, CX + 19.0, GROUND)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return K.render(TARGET_NAME, ROWS, _render_frame, out_dir, ACTOR_METADATA, BODY_BOX)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Ramen-nujan spritesheet.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
