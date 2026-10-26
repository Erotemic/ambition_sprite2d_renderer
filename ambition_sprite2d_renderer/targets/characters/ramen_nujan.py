"""Sprite generator for Ramen-nujan: the mathematician who dreams his theorems.

A respectful parody of Srinivasa Ramanujan, of the Flying Spaghetti Monster's
faction. He is a person, not a food mascot: the noodles are in his clothes.

The look (2026-10-12): a slight young man seen three quarters from the front,
facing right, about five heads tall. Neat black hair with a side part, strong
brows, small dark eyes, a full face. A long night-blue coat buttoned to the
neck, with carrot buttons, a scallion-green lining and a few gold dots joined
like a constellation; cream trousers; and a long noodle-coloured scarf whose
two tails end in loose noodles and trail behind whatever he does. At rest he
stands with his hands behind his back and looks up.

He is a grown man, not a mascot (Jon, 2026-10-12, of the draft before this
one: "too cutsey", "too much like astro boy", and no lock of hair standing on
his head): no big head, no big eyes, no blush.

Everything he eats is vegetarian, and so are the colours: mushroom cream,
scallion green, carrot orange, sesame gold. He holds nothing; the runtime
held-item system is authoritative. There is no drop shadow.

His magic is written in chalk-gold: a summation sweep (the arc with a sigma at
its head), a factorial burst (the ``!``), the ``-1/12`` seal, a bracket for a
shield, the dots of a partition, and the dream bubble a theorem arrives in.

He is a rig: each limb is two bones through a solved elbow or knee, and each
thing is painted once and turned to where it sits (``_ai_era_kit``).

He is a platform fighter (the Smash roster's ``npc_ramen_nujan``): after the
rows of the main game come the rows that game asks a sheet for by name (the
grab kit, the dodges, ``tumble``, ``knockdown``, ``dizzy``) and the rows his
move table names. He takes hold of somebody with his scarf.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from PIL import Image

from ._ai_era_kit import OUTLINE, WHITE, Kit, Point, Pose, RGBA, angle, blend, ease, keys, lerp, mix, pin, solve, turned

TARGET_NAME = "ramen_nujan"
FRAME_SIZE = (208, 176)
GROUND = 164.0
CX = 104.0

# ---- The rig: lengths in frame pixels, from his hips, up is negative ---------

#: How high his hips are when he stands.
HIP_UP = 46.0
#: A length in a pose is in units of this many frame pixels: his hips stand 37
#: units high. A pose is of his body, whatever size it is drawn.
U = HIP_UP / 37.0
THIGH, SHIN = 22.2, 21.4
#: His hips to the base of his neck, along his spine.
NECK = 38.5
UPPER, FORE = 18.6, 17.4
NEAR_SHOULDER: Point = (-6.5, -33.0)
FAR_SHOULDER: Point = (7.5, -32.5)
NEAR_HIP: Point = (-3.8, 0.0)
FAR_HIP: Point = (3.8, 0.0)
#: The sole of a shoe is this far under its ankle.
ANKLE_UP = 3.0
#: The middle of his head from the base of his neck, his head level.
HEAD_UP: Point = (1.0, -11.0)
#: The top of his hair above the ground, standing.
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
        "head": {"source": "explicit.profile.humanoid", "point": {"x": CX + 2.0, "y": GROUND - 95.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": CX + 1.0, "y": GROUND - 68.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": CX - 10.0, "y": GROUND - 47.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": CX + 10.0, "y": GROUND - 47.0}},
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
    # How long the tails are, of their length at rest: he throws his scarf to
    # take hold of somebody.
    "long": 1.0,
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
         ff=(14.0, -30.0, 10.0), eyes="closed", mouth="flat", tail=180.0, wave=8.0, curl=34.0, arm="under", pivot=(15.5, -14.0), off=(-8.0, 14.0),
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
    asleep = dict(SAT, lean=-4.0, head=(1.0, 2.0, 22.0), mouth="smile", tail=96.0, wave=3.0)
    return keys(_shot(i, n), [(0.0, STRUCK), (0.28, sag), (0.5, SAT), (0.72, asleep), (1.0, asleep)])


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


# ---- The rows of a platform fighter ------------------------------------------


@row
def jab_2(i: int, n: int) -> Pose:
    # The second point of the argument, with the other hand.
    poke = dict(GUARD, hip=(4.0, 3.0), lean=13.0, na=(2.0, 15.0), fa=(27.0, 2.0), fh="point", nf=(-9.0, 0.0, 8.0), ff=(11.0, 0.0, 0.0),
                mouth="open", tail=150.0)
    return keys(_shot(i, n), [(0.0, GUARD), (0.3, poke), (0.6, poke), (1.0, GUARD)])


@row
def tilt_up(i: int, n: int) -> Pose:
    # A tick over his head, from in front of him to behind it.
    u = _shot(i, n)
    swing = ease(max(0.0, min(1.0, (u - 0.15) / 0.5)))
    a = math.radians(lerp(10.0, -130.0, swing))
    hand = (27.0 * math.cos(a), 27.0 * math.sin(a))
    base = dict(GUARD, hip=(0.0, lerp(4.0, 0.0, swing)), lean=lerp(6.0, -8.0, swing), head=(0.0, 0.0, -10.0 * swing), na=hand,
                nab=-1.0 if hand[1] < -6.0 and hand[0] < 6.0 else 1.0, arm="under" if hand[1] < -4.0 and hand[0] > -14.0 else "over", nh="flat",
                mouth="open" if 0.15 < u < 0.8 else "flat", brows=1.0, tail=lerp(110.0, 80.0, swing))
    if u > 0.8:
        return blend(base, GUARD, ease((u - 0.8) / 0.2))
    return base


@row
def tilt_down(i: int, n: int) -> Pose:
    low = dict(CROUCH, na=(-12.0, 14.0), nh="flat", brows=-1.0)
    sweep = dict(SWEEP_LOW, hip=(4.0, 14.0), lean=24.0, na=(26.0, 14.0))
    return keys(_shot(i, n), [(0.0, CROUCH), (0.25, low), (0.5, sweep), (0.75, sweep), (1.0, CROUCH)])


@row
def dash_attack(i: int, n: int) -> Pose:
    lunge = dict(DASH, hip=(7.0, 7.0), lean=27.0, na=(27.0, -3.0), fa=(25.0, 3.0), nf=(-12.0, 0.0, 20.0), ff=(13.0, 0.0, 0.0), eyes="wide", mouth="big",
                 tail=182.0, hem=(6.0, 0.0))
    return keys(_shot(i, n), [(0.0, DASH), (0.3, lunge), (0.7, lunge), (1.0, HALF_UP)])


@row
def smash_charge(i: int, n: int) -> Pose:
    # He holds a smash attack the way a theorem arrives.
    return charge(i, n)


@row
def special_side(i: int, n: int) -> Pose:
    # 1729, the taxicab number: forward, and it is a sum of two cubes two ways.
    coil = dict(GUARD, hip=(-4.0, 7.0), lean=-6.0, na=(-12.0, 12.0), fa=(-8.0, 14.0), tail=70.0)
    first = dict(DASH, hip=(6.0, 5.0), lean=24.0, na=(27.0, -4.0), nh="fist", fa=(-14.0, 10.0), fh="fist", nf=(-13.0, -3.0, 30.0), ff=(11.0, 0.0, 0.0),
                 mouth="big", tail=180.0)
    second = dict(first, hip=(8.0, 5.0), lean=26.0, na=(-10.0, 12.0), fa=(27.0, -2.0))
    return keys(_shot(i, n), [(0.0, GUARD), (0.18, coil), (0.4, first), (0.55, first), (0.7, second), (0.85, second), (1.0, HALF_UP)])


@row
def special_up(i: int, n: int) -> Pose:
    # A series that does not converge: each term is a step up.
    wind = P(hip=(-1.0, 9.0), lean=8.0, na=(6.0, 18.0), fa=(10.0, 17.0), nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), eyes="closed", tail=108.0)
    step = dict(RISE, lean=2.0, head=(0.0, 0.0, -10.0), na=(-5.0, -27.0), nh="point", fa=(-9.0, 18.0), fh="soft", eyes="closed", mouth="smile",
                brows=0.0, tail=92.0, wave=9.0)
    other = dict(step, nf=(6.0, -11.0, 12.0), ff=(-6.0, -1.0, 34.0))
    return keys(_shot(i, n), [(0.0, wind), (0.2, step), (0.45, other), (0.7, step), (1.0, dict(APEX, eyes="closed", mouth="smile"))])


@row
def special_down(i: int, n: int) -> Pose:
    # -1/12: the sum of all you throw at him. He waits for it with his eyes shut.
    calm = P(hip=(-1.0, 2.0), lean=-3.0, head=(0.0, 0.0, -3.0), na=(20.0, 2.0), nh="flat", fa=(-7.0, 22.0), nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0),
             eyes="closed", tail=96.0, wave=4.0)
    return keys(_shot(i, n), [(0.0, P()), (0.2, calm), (0.8, dict(calm, na=(21.0, 1.0))), (1.0, P())])


#: He has somebody at the end of his scarf.
HOLD = dict(GUARD, hip=(0.0, 2.0), lean=4.0, na=(22.0, 2.0), fa=(18.0, 6.0), ff=(9.0, 0.0, 0.0), tail=360.0, long=1.25, wave=2.0, curl=0.0)


@row
def grab(i: int, n: int) -> Pose:
    # His scarf goes out over his head and takes hold.
    throw = dict(GUARD, hip=(3.0, 3.0), lean=10.0, na=(26.0, -3.0), nh="open", fa=(8.0, 14.0), ff=(10.0, 0.0, 0.0), mouth="open", tail=360.0, long=1.7,
                 wave=3.0, curl=0.0)
    return keys(_shot(i, n), [(0.0, GUARD), (0.4, throw), (0.7, throw), (1.0, GUARD)])


@row
def grab_hold(i: int, n: int) -> Pose:
    _, s, _c = _loop(i, n)
    return dict(HOLD, hip=(0.0, 2.0 + 0.5 * s), lean=4.0 - 1.5 * s, tail=360.0 + 2.0 * s)


@row
def pummel(i: int, n: int) -> Pose:
    # He corrects them, with one finger.
    up = dict(HOLD, na=(15.0, -13.0), nh="point", brows=1.0)
    tap = dict(HOLD, na=(26.0, -2.0), nh="point", lean=8.0, mouth="open")
    return keys(_shot(i, n), [(0.0, HOLD), (0.35, up), (0.65, tap), (1.0, HOLD)])


@row
def throw_forward(i: int, n: int) -> Pose:
    wind = dict(HOLD, hip=(-3.0, 3.0), lean=-8.0, na=(8.0, 10.0), fa=(10.0, 9.0), nh="open", fh="open")
    push = dict(GUARD, hip=(5.0, 4.0), lean=16.0, na=(27.0, 0.0), fa=(25.0, 5.0), nh="open", fh="open", nf=(-10.0, 0.0, 14.0), ff=(12.0, 0.0, 0.0),
                mouth="big", tail=160.0, hem=(4.0, 1.0))
    return keys(_shot(i, n), [(0.0, HOLD), (0.3, wind), (0.5, push), (0.8, push), (1.0, GUARD)])


@row
def throw_back(i: int, n: int) -> Pose:
    # Over his head by the scarf, and down behind him.
    fling = dict(GUARD, hip=(-3.0, 3.0), lean=-20.0, head=(0.0, 0.0, 12.0), na=(-22.0, -8.0), nab=-1.0, fa=(-15.0, -3.0), nh="open", fh="open",
                 nf=(-9.0, 0.0, 0.0), ff=(8.0, 0.0, -10.0), mouth="open", tail=180.0, long=1.3, wave=3.0, curl=0.0, hem=(0.0, 4.0))
    return keys(_shot(i, n), [(0.0, HOLD), (0.5, fling), (0.75, fling), (1.0, dict(GUARD, tail=110.0))])


@row
def throw_up(i: int, n: int) -> Pose:
    toss = dict(GUARD, hip=(0.0, -1.0), lean=-4.0, head=(0.0, 0.0, -12.0), na=(-6.0, -27.0), nab=-1.0, fa=(8.0, -26.0), nh="open", fh="open",
                mouth="open", brows=1.0, tail=270.0, long=1.5, wave=3.0, curl=0.0)
    low = dict(HOLD, hip=(0.0, 8.0), lean=8.0, tail=380.0)
    return keys(_shot(i, n), [(0.0, HOLD), (0.25, low), (0.5, toss), (0.8, toss), (1.0, dict(GUARD, tail=110.0))])


@row
def throw_down(i: int, n: int) -> Pose:
    high = dict(HOLD, hip=(-1.0, 0.0), lean=-8.0, na=(-10.0, -24.0), nab=-1.0, fa=(6.0, -24.0), tail=300.0, long=1.3)
    slam = dict(GUARD, hip=(3.0, 11.0), lean=24.0, head=(1.0, 0.0, -6.0), na=(18.0, 22.0), fa=(14.0, 22.0), nh="open", fh="open", nf=(-9.0, 0.0, 0.0),
                ff=(9.0, 0.0, 0.0), mouth="big", tail=420.0, long=1.2, wave=3.0, curl=0.0, hem=(3.0, 3.0))
    return keys(_shot(i, n), [(0.0, HOLD), (0.3, high), (0.5, slam), (0.8, slam), (1.0, dict(HALF_UP, tail=464.0))])


@row
def grabbed(i: int, n: int) -> Pose:
    _, s, c = _loop(i, n)
    return P(hip=(-1.0, 1.0), lean=-6.0 + 4.0 * s, head=(0.0, 0.0, -8.0 + 5.0 * c), na=(-2.0, 24.0), fa=(3.0, 24.0), nh="fist", fh="fist",
             nf=(-3.0 + 2.0 * s, -2.0, 20.0), ff=(4.0 - 2.0 * s, -3.0, 14.0), eyes="wince", mouth="grit", brows=1.0, tail=100.0, wave=13.0)


@row
def spot_dodge(i: int, n: int) -> Pose:
    # He is not there: he steps back out of the line with his hands behind him.
    away = P(hip=(-6.0, 3.0), lean=-16.0, head=(-1.0, 0.0, 10.0), na=(-8.5, 21.5), fa=(-7.0, 22.0), nf=(-10.0, 0.0, 0.0), ff=(2.0, 0.0, -8.0),
             eyes="closed", tail=40.0, wave=8.0, hem=(0.0, 3.0))
    return keys(_shot(i, n), [(0.0, P()), (0.3, away), (0.7, away), (1.0, P())])


@row
def air_dodge(i: int, n: int) -> Pose:
    curl = dict(AIR, lean=20.0, head=(0.0, 0.0, -14.0), na=(9.0, 9.0), fa=(11.0, 8.0), nf=(3.0, -17.0, 14.0), ff=(8.0, -20.0, 10.0), eyes="closed",
                tail=200.0, wave=10.0)
    return keys(_shot(i, n), [(0.0, AIR), (0.3, curl), (0.75, curl), (1.0, AIR)])


@row
def tumble(i: int, n: int) -> Pose:
    # Sent flying: over backwards, about his middle.
    return P(hip=(0.0, -3.0), lean=-12.0, head=(-1.0, 0.0, -12.0), na=(-18.0, -14.0), nab=-1.0, fa=(20.0, -12.0), nh="open", fh="open",
             nf=(-8.0, -6.0, 30.0), ff=(8.0, -12.0, 0.0), eyes="wince", mouth="big", brows=1.0, tail=200.0, wave=14.0, hem=(3.0, 3.0),
             pivot=(0.0, -14.0), rot=-360.0 * i / n)


#: On his back, his head behind him and his toes up.
SUPINE = P(rot=-90.0, hip=(-2.0, 25.5), off=(13.0, 0.0), head=(0.0, 0.0, 0.0), na=(5.0, 26.0), nab=-1.0, fa=(8.0, 24.0), fab=-1.0, nh="open",
           fh="open", nf=(-4.5, 25.0, 0.0), ff=(4.5, 25.0, -10.0), eyes="wince", mouth="o", tail=215.0, long=0.7, wave=2.0, curl=8.0)
#: Sitting on the ground, his legs out in front of him.
SAT = P(hip=(-8.0, 26.5), lean=-13.0, head=(0.0, 0.0, 2.0), na=(-9.0, 25.0), fa=(9.0, 24.0), nh="open", fh="open", nf=(19.0, 0.0, -62.0),
        ff=(25.0, 0.0, -66.0), eyes="closed", mouth="o", tail=110.0, hem=(0.0, 2.0))


@row
def knockdown(i: int, n: int) -> Pose:
    _, s, _c = _loop(i, n)
    down = dict(SUPINE, off=(13.0, -0.4 - 0.4 * s))
    return keys(_shot(i, n), [(0.0, dict(STRUCK, rot=-40.0, off=(0.0, -4.0))), (0.25, dict(SUPINE, off=(13.0, -3.0))), (0.45, down), (1.0, down)])


@row
def getup(i: int, n: int) -> Pose:
    return keys(_shot(i, n), [(0.0, SUPINE), (0.35, dict(SAT, eyes="wince")), (0.7, HALF_UP), (1.0, P())])


@row
def dizzy(i: int, n: int) -> Pose:
    _, s, c = _loop(i, n)
    return P(hip=(1.5 * s, 2.0), lean=5.0 * s, head=(0.0, 0.0, 9.0 * c), na=(-4.0 - 2.0 * s, 25.0), fa=(4.0 - 2.0 * s, 24.5), nh="open", fh="open",
             nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), eyes="wince" if i % 4 < 2 else "closed", mouth="o", brows=1.0, tail=96.0 + 8.0 * s, wave=10.0)


@row
def jump_squat(i: int, n: int) -> Pose:
    wind = P(hip=(-1.0, 9.0), lean=10.0, na=(-14.0, 18.0), fa=(-10.0, 20.0), nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), brows=-1.0, tail=108.0)
    return keys(_shot(i, n), [(0.0, P()), (1.0, wind)])


@row
def shield_hit(i: int, n: int) -> Pose:
    held = block(0, 6)
    struck = dict(held, hip=(-5.0, 5.0), lean=-12.0, eyes="wince", mouth="grit", off=(-3.0, 0.0), tail=30.0)
    return keys(_shot(i, n), [(0.0, held), (0.35, struck), (1.0, held)])


@row
def parry(i: int, n: int) -> Pose:
    held = block(0, 6)
    met = dict(held, hip=(1.0, 3.0), lean=4.0, na=(26.0, -1.0), nh="flat", eyes="wide", mouth="open", brows=1.0, tail=140.0)
    return keys(_shot(i, n), [(0.0, held), (0.4, met), (1.0, held)])


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
    # A platform fighter's.
    ("jab_2", 5, 58),
    ("tilt_up", 7, 62),
    ("tilt_down", 7, 62),
    ("dash_attack", 7, 62),
    ("smash_charge", 8, 76),
    ("special_side", 8, 66),
    ("special_up", 8, 80),
    ("special_down", 8, 75),
    ("grab", 6, 60),
    ("grab_hold", 6, 110),
    ("pummel", 5, 50),
    ("throw_forward", 7, 60),
    ("throw_back", 7, 60),
    ("throw_up", 7, 60),
    ("throw_down", 7, 60),
    ("grabbed", 6, 80),
    ("spot_dodge", 6, 55),
    ("air_dodge", 6, 60),
    ("tumble", 8, 70),
    ("knockdown", 6, 90),
    ("getup", 7, 70),
    ("dizzy", 8, 110),
    ("jump_squat", 3, 30),
    ("shield_hit", 4, 60),
    ("parry", 4, 60),
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
        K.oval(d, K.at(2.6, 0.6), 6.0, 3.2, WHITE)
        K.rrect(d, h[0] - 3.4, h[1] - 0.4, h[0] + 8.4, h[1] + ANKLE_UP + 0.4, 1.6, WHITE)
        K.oval(d, h, 3.2, 3.0, WHITE)

    def detail(d) -> None:
        K.rrect(d, h[0] - 5.0, h[1] + ANKLE_UP - 1.0, h[0] + 10.0, h[1] + ANKLE_UP + 2.0, 0.0, SHOE_DARK)
        K.line(d, [K.at(2.0, -1.4), K.at(6.0, -0.6)], mix(SHOE, WHITE, 0.35), 0.8)

    return K.solid(("shoe", near), shape, SHOE if near else mix(SHOE, SHOE_DARK, 0.6), detail, outline=1.2, rim=0.25, shade=0.3,
                   shade_colour=SHOE_DARK)


def _coat(hem_back: int, hem_front: int):
    """His coat from his hips at ``home``, his spine straight up: long, to
    the middle of his thighs. The hem is ``hem_back`` and ``hem_front`` wider than it
    hangs."""
    hb, hf = float(hem_back), float(hem_front)
    back_hem, front_hem = K.at(-12.0 - hb, 10.0), K.at(12.6 + hf, 9.4)
    split_top, split = K.at(7.8, -4.0), K.at(8.2 + hf * 0.7, 9.6)

    def shape(d) -> None:
        K.poly(d, [K.at(-6.0, -38.5), K.at(-11.0, -33.5), K.at(-10.4, -17.0), K.at(-10.2, -4.0), back_hem, front_hem, K.at(12.0, -3.0),
                   K.at(11.2, -18.0), K.at(11.2, -33.0), K.at(6.0, -39.0)], WHITE)
        K.oval(d, K.at(-6.0, -32.4), 5.6, 6.0, WHITE)
        K.oval(d, K.at(6.2, -32.4), 5.8, 6.2, WHITE)

    def detail(d) -> None:
        # The far side of his chest is in his own shade.
        K.poly(d, [K.at(7.6, -42.0), K.at(16.0, -42.0), K.at(18.0 + hf, 12.0), K.at(8.2 + hf * 0.7, 12.0), split_top, K.at(6.8, -27.0)], COAT_DARK)
        # The lining, where the coat opens under its last button.
        K.poly(d, [split_top, (split[0] - 3.4, split[1] + 2.0), (split[0] + 2.6, split[1] + 2.0)], LINING)
        K.line(d, [K.at(6.4, -38.0), K.at(6.8, -27.0), split_top], COAT_LIGHT, 0.9)
        for k in range(5):
            t = k / 4.0
            K.oval(d, K.at(lerp(6.6, 7.6, t), lerp(-31.5, -7.0, t)), 1.4, 1.4, CARROT, OUTLINE, 0.4)
        # The hem's gold band.
        K.poly(d, [(back_hem[0] - 2.0, back_hem[1] - 2.4), (front_hem[0] + 2.0, front_hem[1] - 2.4), (front_hem[0] + 2.0, front_hem[1] + 3.0),
                   (back_hem[0] - 2.0, back_hem[1] + 3.0)], SESAME)
        # Gold dots, joined: a constellation, or a partition, or sesame.
        stars = [K.at(-6.0, -24.0), K.at(-2.0, -15.5), K.at(-7.0, -8.5), K.at(-1.0, -2.0), K.at(-6.0, 4.0)]
        K.line(d, stars, mix(COAT, SESAME, 0.4), 0.45)
        for k, p in enumerate(stars):
            K.oval(d, p, 1.1 if k % 2 == 0 else 0.8, 1.1 if k % 2 == 0 else 0.8, SESAME)

    return K.solid(("coat", hem_back, hem_front), shape, COAT, detail, outline=1.3, rim=0.3, shade=0.4, shade_colour=COAT_DARK)


def _wrap():
    """His scarf where it goes around his neck, from the base of his neck."""

    def shape(d) -> None:
        K.oval(d, K.at(0.8, 0.4), 8.4, 4.2, WHITE)
        K.oval(d, K.at(-7.4, 1.5), 3.4, 3.3, WHITE)

    def detail(d) -> None:
        for dy in (-0.8, 1.8):
            K.line(d, [K.at(-6.8, dy + 0.6), K.at(0.0, dy + 1.8), K.at(7.6, dy)], NOODLE_DARK, 0.6)

    return K.solid(("wrap",), shape, NOODLE, detail, outline=1.2, rim=0.4, shade=0.45, shade_colour=NOODLE_DARK)


LINK = 6.0


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


NEAR_EYE: Point = (0.6, 0.0)
FAR_EYE: Point = (6.4, -0.2)


def _head():
    """His head, from its middle: the skull, the jaw, the hair, an ear, a nose."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, -1.4), 9.4, 9.8, WHITE)
        K.oval(d, K.at(1.8, 3.4), 7.8, 8.2, WHITE)
        K.oval(d, K.at(-1.0, -4.2), 9.8, 8.6, WHITE)
        K.oval(d, K.at(-6.6, 1.6), 2.5, 3.2, WHITE)

    def detail(d) -> None:
        # The far cheek is in shade.
        K.oval(d, K.at(10.0, 3.0), 2.8, 7.4, mix(SKIN, SKIN_SHADE, 0.6))
        # His hair: short, parted on the near side and combed across.
        hairline = [K.at(9.6, -5.6), K.at(7.2, -8.4), K.at(2.6, -8.8), K.at(-1.6, -7.2), K.at(-4.2, -5.0), K.at(-4.6, -1.6),
                    K.at(-5.0, 1.0), K.at(-7.6, 3.6), K.at(-7.2, 8.4), K.at(-20.0, 8.4), K.at(-20.0, -26.0), K.at(20.0, -26.0),
                    K.at(20.0, -5.6)]
        K.poly(d, hairline, HAIR)
        K.line(d, [K.at(-3.0, -10.2), K.at(-0.8, -11.4), K.at(3.6, -11.2), K.at(7.0, -9.6)], HAIR_LIGHT, 0.9)
        K.line(d, [K.at(-1.8, -7.6), K.at(-2.6, -10.6)], HAIR_LIGHT, 0.5)
        K.line(d, [K.at(-9.4, -5.0), K.at(-10.2, -0.6), K.at(-9.6, 3.6)], HAIR_LIGHT, 0.7)
        # His ear, over his hair.
        K.oval(d, K.at(-6.4, 1.6), 2.0, 2.8, SKIN, OUTLINE, 0.6)
        K.line(d, [K.at(-6.8, 0.6), K.at(-6.0, 1.8), K.at(-6.6, 2.8)], SKIN_DEEP, 0.45)
        # His nose, and the line of his jaw.
        K.line(d, [K.at(3.6, -1.0), K.at(4.9, 2.6), K.at(3.4, 3.4)], SKIN_DEEP, 0.75)
        K.line(d, [K.at(-3.6, 6.6), K.at(-0.6, 10.0), K.at(3.0, 11.0)], mix(SKIN, SKIN_DEEP, 0.55), 0.6)

    return K.solid(("head",), shape, SKIN, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=SKIN_DEEP)


def _eyes(mode: str):
    def paint(d) -> None:
        for (ex, ey), rx, ry in ((NEAR_EYE, 2.1, 1.9), (FAR_EYE, 1.7, 1.8)):
            c = K.at(ex, ey)
            if mode == "closed":
                K.line(d, [(c[0] - rx, c[1] - 0.2), (c[0], c[1] + 0.9), (c[0] + rx, c[1] - 0.2)], INK, 0.9)
                continue
            if mode == "happy":
                K.line(d, [(c[0] - rx, c[1] + 0.7), (c[0], c[1] - 1.0), (c[0] + rx, c[1] + 0.7)], INK, 1.0)
                continue
            if mode == "wince":
                side = 1.0 if ex < 3.0 else -1.0
                K.line(d, [(c[0] - rx * side, c[1] - 1.4), (c[0] + rx * 0.6 * side, c[1]), (c[0] - rx * side, c[1] + 1.4)], INK, 0.9)
                continue
            tall = ry + (0.6 if mode == "wide" else 0.0)
            K.oval(d, c, rx, tall, EYE_WHITE)
            small = 0.8 if mode == "wide" else 1.0
            ic = (c[0] + 0.4, c[1] + (-0.5 if mode == "up" else 0.1))
            K.oval(d, ic, 1.3 * small, 1.45 * small, IRIS)
            K.oval(d, ic, 0.8 * small, 0.9 * small, INK)
            K.oval(d, (ic[0] - 0.5, ic[1] - 0.6), 0.4, 0.4, WHITE)
            # His upper lid: the heavy line of the eye.
            K.line(d, [(c[0] - rx - 0.3, c[1] - 0.2), (c[0] - rx * 0.4, c[1] - tall), (c[0] + rx * 0.5, c[1] - tall),
                       (c[0] + rx + 0.3, c[1] - 0.4)], INK, 0.9)
            K.line(d, [(c[0] - rx * 0.6, c[1] + tall), (c[0] + rx * 0.7, c[1] + tall)], SKIN_DEEP, 0.4)

    return K.piece(("eyes", mode), paint)


def _brows(mood: int):
    """His brows: 0 level, 1 raised, -1 set."""

    def paint(d) -> None:
        up = -1.0 if mood > 0 else 0.0
        inner = 1.0 if mood < 0 else 0.0
        K.stroke(d, [K.at(-2.2, -3.2 + up), K.at(0.6, -3.9 + up), K.at(3.0, -3.3 + up + inner)], HAIR, 1.3)
        K.stroke(d, [K.at(4.9, -3.5 + up + inner), K.at(6.6, -4.0 + up), K.at(8.3, -3.2 + up)], HAIR, 1.2)

    return K.piece(("brows", mood), paint)


def _mouth(mode: str):
    c = K.at(3.6, 6.6)

    def paint(d) -> None:
        if mode == "smile":
            K.line(d, [(c[0] - 2.4, c[1] - 0.3), (c[0] - 0.2, c[1] + 0.5), (c[0] + 2.2, c[1] - 0.5)], MOUTH, 0.8)
        elif mode == "flat":
            K.line(d, [(c[0] - 2.0, c[1]), (c[0] + 1.9, c[1] - 0.1)], MOUTH, 0.8)
        elif mode == "o":
            K.oval(d, c, 1.1, 1.3, MOUTH, INK, 0.4)
        elif mode == "grit":
            K.rrect(d, c[0] - 2.3, c[1] - 1.0, c[0] + 2.2, c[1] + 1.0, 0.7, EYE_WHITE, INK, 0.5)
            K.line(d, [(c[0], c[1] - 0.9), (c[0], c[1] + 0.9)], INK, 0.3)
        else:
            ry = 2.2 if mode == "big" else 1.4
            K.oval(d, (c[0], c[1] + 0.3), 2.2 if mode == "big" else 1.8, ry, MOUTH, INK, 0.5)
            K.oval(d, (c[0], c[1] + 0.3 + ry * 0.5), 1.2, ry * 0.4, TONGUE)

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
    elif anim == "jab_2" and 1 <= i <= 3:
        stamp(_infinity(6.0), (far_hand[0] + 16.0, far_hand[1] - 1.0), "infinity")
        stamp(_sparkle(3.0), (far_hand[0] + 24.0, far_hand[1] - 8.0), "sparkle_0")
    elif anim == "tilt_up" and 2 <= i <= 4:
        a = math.degrees(math.atan2(hand[1] - shoulder[1], hand[0] - shoulder[0]))
        lead = int(round(a / 5.0)) * 5
        stamp(_swoosh(46.0, lead - 6, lead + 70, 8.0), shoulder, "swoosh")
        tip = math.radians(lead - 12.0)
        stamp(_tick(4.0), (shoulder[0] + 50.0 * math.cos(tip), shoulder[1] + 50.0 * math.sin(tip)), "tick")
    elif anim == "tilt_down" and 3 <= i <= 5:
        stamp(_swoosh(13.0, -70, 70, 5.0), (hand[0] + 6.0, hand[1] + 1.0), "swoosh")
    elif anim == "dash_attack" and 2 <= i <= 4:
        centre = (hand[0] + 13.0, hand[1] + 2.0)
        stamp(_burst(8.0 + (i - 2)), centre, "burst")
        stamp(_sigma(4.5), centre, "sigma")
    elif anim == "special_side" and 3 <= i <= 6:
        fist = hand if i <= 4 else far_hand
        centre = (fist[0] + 14.0, fist[1])
        stamp(_burst(9.0 + 2.0 * (i % 2)), centre, "burst")
        stamp(_bang(6.0), centre, "bang")
    elif anim == "special_up" and i >= 1:
        stamp(_partition(), (hip[0] - 4.0, min(foot[1] + 10.0, GROUND - 10.0)), "partition")
        stamp(_sigma(5.0), (hand[0] + 1.0, hand[1] - 14.0), "sigma")
        sparkles([(-20.0, 6.0, 3.0), (20.0, 18.0, 3.0)], hip)
    elif anim == "special_down" and 1 <= i <= 6:
        disc, seal = _seal(9.0 + 0.5 * (i % 2))
        centre = (hand[0] + 15.0, hand[1] - 2.0)
        stamp(disc, centre, "seal_disc")
        stamp(seal, centre, "seal")
    elif anim == "pummel" and 2 <= i <= 3:
        stamp(_tick(3.5), (hand[0] + 13.0, hand[1] - 3.0), "tick")
    elif anim == "throw_forward" and 3 <= i <= 5:
        centre = (hand[0] + 15.0, hand[1] + 2.0)
        stamp(_burst(9.0), centre, "burst")
        stamp(_bang(6.0), centre, "bang")
    elif anim == "spot_dodge" and 2 <= i <= 4:
        sparkles([(26.0, -30.0, 3.0), (30.0, -4.0, 2.5)], hip)
    elif anim == "dizzy":
        for k in range(3):
            a = ph + k * math.tau / 3.0
            stamp(_sparkle(3.0 + (k % 2)), (head[0] + 15.0 * math.cos(a), head[1] - 17.0 + 4.0 * math.sin(a)), f"sparkle_{k}")
    elif anim == "parry" and 1 <= i <= 2:
        stamp(_bracket(19.0), (hip[0] + 40.0, hip[1] - 24.0), "bracket")
        stamp(_tick(4.5), (hip[0] + 30.0, hip[1] - 52.0), "tick")
    elif anim == "shield_hit":
        stamp(_bracket(18.0), (hip[0] + 40.0 - (3.0 if i == 1 else 0.0), hip[1] - 24.0), "bracket")
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
            stamp(_swoosh(48.0, lead - sweep, lead + 6, 10.0), shoulder, "swoosh")
            tip = math.radians(lead + 12.0)
            stamp(_sigma(6.5), (shoulder[0] + 52.0 * math.cos(tip), shoulder[1] + 52.0 * math.sin(tip)), "sigma")
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
        stamp(_bracket(18.0 + (i % 2)), (hip[0] + 40.0, hip[1] - 24.0), "bracket")
    elif anim == "interact" and 3 <= i <= 5:
        stamp(_tick(4.0), (hand[0] + 14.0, hand[1] - 5.0), "tick")
    elif anim in ("charge", "smash_charge"):
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
    hip = (hx * U, -HIP_UP + hy * U)
    px, py = pose["pivot"]  # type: ignore[misc]
    pivot = (hip[0] + px * U, hip[1] + py * U)

    def W(p: Point) -> Point:
        """A point of him (from the ground under him) in the frame."""
        r = turned((p[0] - pivot[0], p[1] - pivot[1]), rot)
        return (CX + ox * U + pivot[0] + r[0], GROUND + oy * U + pivot[1] + r[1])

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
        elbow, wrist = solve(shoulder, (shoulder[0] + dx * U, shoulder[1] + dy * U), UPPER, FORE, float(pose[key + "b"]))  # type: ignore[arg-type]
        colour = COAT if near else COAT_DARK
        limb(f"{name}_arm", [
            (shoulder, elbow, lambda edge: _bone("upper", UPPER, 7.4, 6.2, colour, COAT_DARK, edge)),
            (elbow, wrist, lambda edge: _bone("fore", FORE, 6.2, 5.4, colour, COAT_DARK, edge)),
        ])
        K.place(img, _hand(str(pose["nh" if near else "fh"]), near), W(wrist), f"{name}_hand", angle(W(elbow), W(wrist)))
        return W(wrist)

    def leg(near: bool) -> Point:
        key, name = ("nf", "near") if near else ("ff", "far")
        root = (hip[0] + (NEAR_HIP if near else FAR_HIP)[0], hip[1])
        fx, fy, toe = pose[key]  # type: ignore[misc]
        knee, ankle = solve(root, (fx * U, fy * U - ANKLE_UP), THIGH, SHIN, -1.0)
        colour = TROUSER if near else TROUSER_DARK
        limb(f"{name}_leg", [
            (root, knee, lambda edge: _bone("thigh", THIGH, 7.8, 6.4, colour, TROUSER_DARK, edge)),
            (knee, ankle, lambda edge: _bone("shin", SHIN, 6.4, 5.2, colour, TROUSER_DARK, edge)),
        ])
        K.place(img, _shoe(near), W(ankle), f"{name}_shoe", toe + rot)
        return W(ankle)

    far_hand = arm(False)
    leg(False)
    kicking = pose["leg"] == "over"
    near_foot = (0.0, 0.0) if kicking else leg(True)

    hem = pose["hem"]
    K.place(img, _coat(int(round(max(0.0, hem[0]) * U)), int(round(max(0.0, hem[1]) * U))), W(hip), "coat", lean + rot)  # type: ignore[index]
    if kicking:
        near_foot = leg(True)

    # His scarf's tails, from the knot at the back of his neck. They hang in
    # the world: turning him does not turn them.
    knot = W(trunk(-7.4, -NECK + 1.6))
    phase = math.tau * frame_idx / max(1, nframes)
    held = pin(knot)
    link = LINK * float(pose["long"])  # type: ignore[arg-type]
    chains = []
    for links, lead, spread in ((7, 0.0, 0.0), (6, 1.7, 13.0)):
        at = (knot[0] - held[0], knot[1] - held[1])
        chain = [at]
        for k in range(links):
            a = float(pose["tail"]) + spread + float(pose["curl"]) * k + float(pose["wave"]) * math.sin(phase - 0.85 * k + lead) * (0.35 + 0.65 * k / links)  # type: ignore[arg-type]
            at = (at[0] + link * math.cos(math.radians(a)), at[1] + link * math.sin(math.radians(a)))
            chain.append(at)
        chains.append(tuple(chain))
    K.place(img, _tails(tuple(chains)), held, "scarf_tails")

    under = pose["arm"] == "under"
    near_hand = arm(True) if under else (0.0, 0.0)

    neck = trunk(0.8, -NECK)
    hdx, hdy, tilt = pose["head"]  # type: ignore[misc]
    up = turned(HEAD_UP, lean * 0.5 + tilt * 0.3)
    head = W((neck[0] + up[0] + hdx * U, neck[1] + up[1] + hdy * U))
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


#: The body the game moves: his coat, standing, up to the top of his hair.
BODY_BOX = (CX - 14.0, GROUND - HEIGHT, CX + 15.0, GROUND)


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


# ---- In the round (``_round_cast``) --------------------------------------------
#
# Ramen-nujan in the round: his own art where he has it (his head, coat and
# the scarf round his neck in his three-quarter view; his sleeves, hands,
# trousers, shoes and the tails of his scarf in every view), placed by 3D;
# and what 3D draws for the other views, as data. He has no front view, so how
# wide he is from the front is read from his build. His rows do not use this.

from types import SimpleNamespace  # noqa: E402

import numpy as np  # noqa: E402

from . import _person_rig as R  # noqa: E402
from . import _person_round as O  # noqa: E402
from . import _round_cast as C  # noqa: E402
from . import _round_wear as W  # noqa: E402

#: As he rests (``idle``, its first frame): his hands behind his back, his
#: head tilted back, looking up.
_REST = ROW_POSES["idle"](0, dict((n, k) for n, k, _ in ROWS)["idle"])
_TILT = float(_REST["head"][2])
_up = turned(HEAD_UP, _TILT * 0.3)
_HEAD = (0.8 + _up[0] + float(_REST["head"][0]) * U, -NECK + _up[1])


def _drawn_wrist(shoulder: Point, reach: Point) -> Point:
    return (shoulder[0] + reach[0] * U, shoulder[1] + reach[1] * U)


JOINTS = C.lifted_joints(shoulders=(NEAR_SHOULDER, FAR_SHOULDER), hips=(NEAR_HIP, FAR_HIP),
                         feet=(float(_REST["nf"][0]) * U, float(_REST["ff"][0]) * U), neck=(0.8, -NECK), head=_HEAD,
                         widths=(7.6, 4.4, 4.4 + 2.2 * U), hip_up=HIP_UP, ankle_up=ANKLE_UP,
                         wrists=(_drawn_wrist(NEAR_SHOULDER, _REST["na"]), _drawn_wrist(FAR_SHOULDER, _REST["fa"])))
#: His hands behind his back, at its small: his three-quarter view draws them
#: out past his back so that they show; from behind they are together.
STANCE = C.Stance(hands={"r": C.Hand(at=(-2.6, -8.0, -9.4), pole=(-1.0, 0.2, -0.3)), "l": C.Hand(at=(2.6, -8.4, -9.6), pole=(1.0, 0.2, -0.3))},
                  stagger=1.0)

#: His head in 3D: a full face, short neat black hair parted on his right and
#: combed across, an ear each side, small dark eyes with whites, strong brows.
HEAD_3D = O.Head3D(
    skin=SKIN, shade=SKIN_SHADE, deep=SKIN_DEEP,
    skull=((0.0, -1.6, 0.0), (8.4, 9.6, 8.4)), jaw=((0.0, 3.4, 2.5), (7.0, 8.0, 5.0)), nose=((0.0, 1.6, 8.4), (1.2, 2.0, 1.8)),
    ear=((-8.0, 1.6, -1.0), (1.4, 3.0, 2.2)), eye=(30.0, 0.0), eye_size=0.95, ink=INK, eye_white=EYE_WHITE, iris=IRIS, lid=INK,
    brow=(HAIR, None, -3.6, 1.3),
    hair=lambda u, v: (v < -8.6 + 3.0 * np.clip(np.abs(u) / 45.0, 0.0, 1.0)) | ((np.abs(u) > 72.0) & (v < 2.0)) | ((np.abs(u) > 100.0) & (v < 8.4)),
    hair_colour=HAIR, hair_shade=mix(HAIR, INK, 0.5), volumes=[((0.0, -5.0, -0.6), (8.8, 7.4, 8.8))],
    lines=[O.curve([(-2.2, 6.4, 7.0), (0.0, 6.9, 7.3), (2.2, 6.3, 7.0)], MOUTH, 0.8)]
    + [O.curve([O.on_ellipsoid((0.0, -5.0, -0.6), (8.8, 7.4, 8.8), u0 + 70.0 * t, -11.6 + 1.6 * t, 0.2)[0] for t in (0.0, 0.5, 1.0)], HAIR_LIGHT, 0.7)
       for u0 in (-40.0, -60.0, -150.0)]
    + [O.curve([O.on_ellipsoid((0.0, -5.0, -0.6), (8.8, 7.4, 8.8), -38.0, v, 0.2)[0] for v in (-12.2, -10.0)], HAIR_LIGHT, 0.5)],
)

#: His coat: long, to the middle of his thighs, buttoned to the neck with
#: carrot buttons, its green lining where it opens under the last one, a gold
#: band at the hem, and gold dots joined like a constellation on his right.
COAT_3D = W.Trunk(
    rings=[O.Ring(-39.0, 0.0, 0.4, 4.6, 4.2), O.Ring(-35.0, 0.0, 0.3, 8.4, 6.8), O.Ring(-28.0, 0.0, 0.3, 9.2, 7.4), O.Ring(-17.0, 0.0, 0.2, 9.0, 7.2),
           O.Ring(-4.0, 0.0, 0.0, 9.2, 7.2), O.Ring(10.0, 0.0, 0.0, 10.6, 8.2)],
    garment=W.Garment(COAT, COAT_DARK, radius=9.0, features=[
        W.Down(6.0, -38.0, -4.0, COAT_LIGHT, width=0.45), W.Strip(0.0, -4.0, 10.0, 0.2, LINING, flare=3.0),
        W.Buttons(0.0, -31.5, -7.0, 5, 1.4, CARROT), W.Band(7.4, 11.0, SESAME),
        W.Path([(-55.0, -24.0), (-30.0, -15.5), (-62.0, -8.5), (-25.0, -2.0), (-55.0, 4.0)], mix(COAT, SESAME, 0.4), width=0.25),
        *[W.Glow(u, v, r, r, SESAME) for u, v, r in ((-55.0, -24.0, 1.1), (-30.0, -15.5, 0.8), (-62.0, -8.5, 1.1), (-25.0, -2.0, 0.8), (-55.0, 4.0, 1.1))],
        W.Shade()]),
    shoulder=((-6.4, -32.4, 0.3), (5.0, 5.6, 5.0)),
)
#: His scarf as his three-quarter view draws it (``_wrap``): a thick roll
#: wound round his neck, over the bottom of his chin (``lead``, as his view
#: paints it over his head), two dark lines along it, and its knot
#: behind his right shoulder; from the knot its two tails hang down behind
#: him on that side (``_tails``: each ends in loose noodles).
WRAP_3D = W.Worn("scarf", [O.Ring(-41.0, 0.0, 0.8, 5.0, 4.6), O.Ring(-39.6, 0.0, 0.8, 7.6, 7.0), O.Ring(-37.8, 0.0, 0.6, 8.0, 7.4),
                           O.Ring(-36.0, 0.0, 0.4, 6.8, 6.2)],
                 W.Garment(NOODLE, NOODLE_DARK, features=[W.Across(-180.0, 180.0, -38.9, NOODLE_DARK, width=0.3),
                                                          W.Across(-180.0, 180.0, -36.9, NOODLE_DARK, width=0.3), W.Shade(-0.45)]),
                 lumps=[((-3.0, -37.6, -6.4), (3.0, 3.0, 2.6))], lead=6.0)
_KNOT = np.array([-3.0, -37.0, -7.6])
TAILS = W.Chains("scarf_tails", [[tuple(_KNOT + k * np.array([-0.4, 5.9, -0.9])) for k in range(8)],
                                 [tuple(_KNOT + k * np.array([-0.2, 5.6, -1.7])) for k in range(7)]], _tails, lead=0.5)


# His head from the front, drawn as the cast draws a head from the front
# (``_person_rig.make_front_head`` and the rest), in the numbers of his
# three-quarter view: a full round face; short black hair, its line across his
# forehead, down at the temples and in front of his ears, parted on his right
# and combed across; eyes with whites under a heavy lid, strong brows, his
# nose a line, a small smile.


def _front_hair_shape(d) -> None:
    K.oval(d, K.at(0.0, -4.8), 9.6, 7.6, WHITE)


def _front_hair(d) -> None:
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 6.0), K.at(9.6, 6.0), K.at(8.8, 1.0), K.at(8.2, -4.6), K.at(5.8, -7.4), K.at(1.6, -8.4),
               K.at(-2.6, -8.2), K.at(-5.8, -6.8), K.at(-8.2, -4.4), K.at(-8.8, 1.0), K.at(-9.6, 6.0), K.at(-20.0, 6.0)], HAIR)
    # The part on his right, and the hair combed across from it.
    K.line(d, [K.at(-3.8, -12.6), K.at(-3.2, -8.6)], HAIR_LIGHT, 0.6)
    K.line(d, [K.at(-2.6, -11.4), K.at(1.8, -12.4), K.at(6.6, -10.8), K.at(8.6, -7.4)], HAIR_LIGHT, 0.9)
    K.line(d, [K.at(-8.8, -5.0), K.at(-9.4, -1.0), K.at(-9.0, 3.0)], HAIR_LIGHT, 0.6)


def _front_face(d) -> None:
    K.line(d, [K.at(-0.4, -0.4), K.at(-1.0, 2.8), K.at(0.0, 3.6), K.at(1.0, 2.8)], SKIN_DEEP, 0.7)


_FRONT_HEAD = R.front_face(
    R.make_front_head(K, ("ramen",), SKIN, SKIN_DEEP, wide=8.6, jaw=7.4, chin=3.4, ears=SKIN, shape=_front_hair_shape, hair=_front_hair, face=_front_face),
    R.make_front_eyes(K, ("ramen",), spread=3.6, y=-0.2, ink=INK, white=EYE_WHITE, iris=IRIS, size=1.0),
    R.make_front_brows(K, ("ramen",), HAIR, spread=3.6, y=-3.8, width=1.3),
    R.make_front_mouth(K, ("ramen",), y=7.0, colour=MOUTH, wide=0.7))


def _arm_bones(pts, near):
    colour = COAT if near else COAT_DARK
    return [(pts[0], pts[1], lambda edge, n: _bone("upper", n, 7.4, 6.2, colour, COAT_DARK, edge)),
            (pts[1], pts[2], lambda edge, n: _bone("fore", n, 6.2, 5.4, colour, COAT_DARK, edge))]


def _leg_bones(pts, near):
    colour = TROUSER if near else TROUSER_DARK
    return [(pts[0], pts[1], lambda edge, n: _bone("thigh", n, 7.8, 6.4, colour, TROUSER_DARK, edge)),
            (pts[1], pts[2], lambda edge, n: _bone("shin", n, 6.4, 5.2, colour, TROUSER_DARK, edge))]


def _own(J):
    """His own head, coat and scarf in his three-quarter view, and his head
    from the front (``_FRONT_HEAD``). His coat is not mirrored (the
    constellation is on his right); his scarf is."""
    turn = _TILT
    layers = lambda: O.composed(K, [(_head(), "head"), (_eyes(str(_REST["eyes"])), "eyes"),  # noqa: E731
                                    (_brows(1 if float(_REST["brows"]) > 0.5 else 0), "brows"), (_mouth(str(_REST["mouth"])), "mouth")], turn)
    front = dict(R.FRONT_REST, eyes=str(_REST["eyes"]), mouth=str(_REST["mouth"]), brows=float(_REST["brows"]))
    return {"trunk": C.own_art("own_coat", (0.0, 0.0, 0.0), lambda: _coat(0, 0), lead=0.4, mirror=False),
            "head": C.own_art("own_head", J.head, layers, lambda: O.composed(K, _FRONT_HEAD(front)), lead=9.0),
            "scarf": C.own_art("own_scarf", J.neck, _wrap, lead=9.5)}


BODY = C.RigBody(
    K, FRAME_SIZE, CX, GROUND, HIP_UP, UPPER, FORE, THIGH, SHIN, rest_joints=SimpleNamespace(**vars(JOINTS), rest=_REST),
    hand_modes=(str(_REST["nh"]), str(_REST["fh"])), arm_bones=_arm_bones, leg_bones=_leg_bones, hand=_hand, shoe=_shoe,
    front_shoe=R.make_front_shoe(K, SHOE, SHOE_DARK, ANKLE_UP), back_shoe=R.make_back_shoe(K, SHOE, SHOE_DARK, ANKLE_UP), own_pieces=_own,
    frames=lambda: {"front_3q": _render_frame("idle", 0, dict((n, k) for n, k, _ in ROWS)["idle"])})
ROUND = C.Round("Ramen-nujan", BODY, C.Look(HEAD_3D, COAT_3D, pieces=[("scarf", WRAP_3D)], back_pieces=[TAILS]), STANCE)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
