"""Sprite generator for the Paradox Barber: he shaves every man who does not
shave himself, and only those men.

The barber of Bertrand Russell's paradox, as a man.

The look (2026-10-13): a tall thin barber, seen three quarters from the
front, facing right. Dark hair with a parting and oil in it, and a small
wave over his brow; a moustache with its ends curled up. His face is the
paradox: there is lather on his cheek, and there is a beard on his chin.
Whichever he does, the other is true. A white shirt with the sleeves rolled,
a red bow tie, and a long cream apron tied at his waist, with the stripes of
a barber's pole at its hem and a comb in its pocket. Dark trousers. He stands
straight, as a man does who is on his feet all day.

He is a grown man, not a mascot. He holds nothing at rest: his razor is in
his hand only in the rows that are its own. There is no drop shadow.

What he shows: the stroke of a razor; the question the paradox asks (is x in
x?), which goes round his head; and his own face, shaved, with the beard
back before the razor is down.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, how he stands and what he shows are his. His
portraits are frames of this sheet.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "paradox_barber"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "The Paradox Barber"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_paradox_barber", "display_name": "The Paradox Barber"},
    "visual": {"default_pose": "idle"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Slim",
        "mass_class": "Light",
        "traits": ["story", "humanoid", "barber", "paradox", "logic", "playable_candidate"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": None, "fly": None, "swim": None, "crawl": False, "use_lifts": True, "door_access": ["public"]},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "tags": ["story", "humanoid", "barber", "paradox", "logic", "playable_candidate"],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 80.0, "y": 34.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 80.0, "y": 86.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 32.0, "y": 120.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 128.0, "y": 120.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 80.0, "y": 6.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "self_shave", "events": []},
        "action.melee.primary": {"animation": "clean_cut", "events": []},
        "action.special.primary": {"animation": "paradox_loop", "events": []},
        "death": {"animation": "death", "events": []},
    },
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "The Paradox Barber personifies Bertrand Russell's barber paradox: he shaves every man "
            "who does not shave himself, and only those men, leaving his own grooming logically "
            "impossible. The split face and immaculate shop make self-reference visible before the "
            "dialogue explains it."
        ),
        "gameplay_description": (
            "Use as a logic puzzle NPC, gatekeeper, comic boss, or rule-system tutorial. Interactions "
            "should force the player to examine who a rule applies to, especially when the rule "
            "refers to its own enforcer."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'I shave every man here who does not shave himself, and only those men.',
        'I have been mid-stroke for eleven years.',
        'Stop letting a collection contain itself.',
    ],
)



SHIRT: RGBA = (246, 244, 238, 255)
SHIRT_DARK: RGBA = (196, 200, 214, 255)
APRON: RGBA = (236, 226, 200, 255)
APRON_DARK: RGBA = (184, 168, 140, 255)
TROUSER: RGBA = (58, 60, 78, 255)
TROUSER_DARK: RGBA = (36, 38, 54, 255)
SHOE: RGBA = (40, 34, 38, 255)
SHOE_DARK: RGBA = (20, 18, 24, 255)
SKIN: RGBA = (238, 202, 178, 255)
SKIN_SHADE: RGBA = (208, 164, 146, 255)
SKIN_DEEP: RGBA = (164, 110, 102, 255)
HAIR: RGBA = (46, 36, 40, 255)
HAIR_SHADE: RGBA = (96, 82, 92, 255)
RED: RGBA = (206, 60, 66, 255)
RED_DARK: RGBA = (140, 36, 50, 255)
BLUE: RGBA = (62, 104, 190, 255)
FOAM: RGBA = (252, 252, 250, 255)
FOAM_SHADE: RGBA = (200, 214, 232, 255)
STEEL: RGBA = (214, 224, 236, 255)
STEEL_DARK: RGBA = (124, 138, 160, 255)
INK: RGBA = (28, 24, 32, 255)
GOLD: RGBA = (244, 196, 92, 255)
GOLD_DARK: RGBA = (180, 120, 50, 255)

#: Tall and thin, 175 cm, and straight.
BUILD = Build(hip_up=51.0, thigh=24.7, shin=23.6, neck=(0.6, -36.4), upper=20.0, fore=19.0, near_shoulder=(-3.8, -32.2), far_shoulder=(5.2, -31.8),
              near_hip=(-3.4, 0.0), far_hip=(3.4, 0.0), head_up=(0.8, -12.6), height=112.5, half_width=(12.5, 14.5))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0
#: How far under his hips the hem of his apron is.
HEM = 25.0


def _front(d, hb: float, hf: float) -> None:
    """His shirt and trousers where the apron is not, the apron's edge and
    tie, his collar and bow tie, the pocket with its comb, and the stripes
    of the pole at the hem."""
    # Behind the apron: his shirt, and under his waist his trousers.
    K.poly(d, [K.at(-14.0, TOP - 3.0), K.at(-0.6, TOP - 3.0), K.at(-2.0, -8.0), K.at(-14.0, -8.0)], SHIRT)
    K.poly(d, [K.at(-14.0, TOP + 8.0), K.at(-6.4, TOP + 8.0), K.at(-6.8, -8.0), K.at(-14.0, -8.0)], SHIRT_DARK)
    K.poly(d, [K.at(-16.0, -8.0), K.at(-2.0, -8.0), K.at(-3.6 - hb * 0.3, HEM + 4.0), K.at(-16.0 - hb, HEM + 4.0)], TROUSER)
    K.line(d, [K.at(-0.6, TOP + 4.0), K.at(-2.0, -8.0), K.at(-3.6 - hb * 0.3, HEM)], APRON_DARK, 0.8)
    # The strap of the bib, his collar and the bow tie.
    K.line(d, [K.at(0.0, TOP + 5.0), K.at(2.4, TOP - 1.0)], APRON_DARK, 1.0)
    K.poly(d, [K.at(2.0, TOP - 1.4), K.at(9.6, TOP - 1.0), K.at(8.6, TOP + 3.0), K.at(3.0, TOP + 2.6)], SHIRT)
    K.poly(d, [K.at(4.0, TOP + 1.4), K.at(6.0, TOP + 2.6), K.at(4.0, TOP + 4.4)], RED)
    K.poly(d, [K.at(8.4, TOP + 1.4), K.at(6.2, TOP + 2.6), K.at(8.4, TOP + 4.4)], RED)
    K.oval(d, K.at(6.1, TOP + 2.8), 0.9, 0.9, RED_DARK)
    # The tie of the apron at his waist.
    K.line(d, [K.at(-2.0, -8.0), K.at(11.0 + hf * 0.3, -7.4)], APRON_DARK, 0.8)
    # The pocket: a comb and the rings of his scissors.
    K.rrect(d, K.home[0] + 2.0, K.home[1] - 3.0, K.home[0] + 8.6, K.home[1] + 4.0, 0.8, mix(APRON, APRON_DARK, 0.25), APRON_DARK, 0.6)
    K.poly(d, [K.at(3.0, -6.4), K.at(4.4, -6.4), K.at(4.4, -2.4), K.at(3.0, -2.4)], HAIR)
    K.oval(d, K.at(6.4, -4.4), 1.2, 1.2, None, STEEL_DARK, 0.6)  # type: ignore[arg-type]
    K.oval(d, K.at(7.6, -3.4), 1.0, 1.0, None, STEEL_DARK, 0.6)  # type: ignore[arg-type]
    # The stripes of the pole, along the hem.
    K.poly(d, [K.at(-3.4, HEM - 6.0), K.at(16.0 + hf, HEM - 6.0), K.at(16.0 + hf, HEM - 1.2), K.at(-3.6, HEM - 1.2)], FOAM)
    for k in range(-1, 6):
        x = -3.0 + k * 4.4
        K.poly(d, [K.at(x, HEM - 1.2), K.at(x + 2.2, HEM - 6.0), K.at(x + 3.6, HEM - 6.0), K.at(x + 1.4, HEM - 1.2)], RED if k % 2 == 0 else BLUE)
    K.line(d, [K.at(-3.4, HEM - 6.0), K.at(16.0 + hf, HEM - 6.0)], APRON_DARK, 0.5)


X.torso = R.make_torso(K, ("barber",), APRON, APRON_DARK, back=(7.4, 8.0, 7.8, 9.0), front=(7.8, 8.4, 8.6, 10.2), hem_y=HEM, top=TOP,
                       shoulders=((-3.4, -32.0), (4.2, -32.0)), shoulder_r=(4.2, 3.8), shade_from=40.0, detail=_front)

NEAR_EYE = (1.8, -0.8)
FAR_EYE = (7.0, -1.0)


def _hair_shape(d) -> None:
    # Flat to his head with oil, and one wave over his brow.
    K.oval(d, K.at(-0.8, -6.2), 8.8, 6.6, WHITE)
    K.poly(d, [K.at(3.0, -12.2), K.at(8.6, -11.6), K.at(10.2, -8.6), K.at(7.0, -7.0)], WHITE)
    K.poly(d, [K.at(-8.0, -5.0), K.at(-9.4, -1.0), K.at(-7.4, 3.4), K.at(-5.0, 4.6)], WHITE)


def _hair(d) -> None:
    K.poly(d, [K.at(20.0, -8.4), K.at(9.0, -8.4), K.at(6.4, -7.0), K.at(3.0, -7.8), K.at(-0.6, -7.0), K.at(-2.4, -3.6), K.at(-2.6, -0.8), K.at(-5.4, -0.6),
               K.at(-5.8, 3.4), K.at(-4.6, 4.8), K.at(-20.0, 5.0), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
    # The parting, and the light the oil takes.
    K.line(d, [K.at(1.0, -11.8), K.at(-0.4, -7.4)], SKIN_SHADE, 0.5)
    for strand in ([(-6.0, -10.4), (-2.0, -11.6), (0.4, -11.2)], [(3.0, -11.4), (6.6, -10.6), (8.6, -9.0)], [(-7.4, -6.0), (-6.4, -2.0)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_SHADE, 0.6)


def _face(lather: bool = True):
    """The paradox: lather on his cheek, and a beard on his chin. With
    ``lather`` false his cheek is bare and the beard is all of his jaw."""

    def paint(d) -> None:
        if lather:
            for (x, y), r in (((0.6, 4.0), 2.4), ((2.6, 5.8), 2.6), ((4.6, 7.4), 2.0), ((1.4, 6.6), 2.0)):
                K.oval(d, K.at(x, y), r, r * 0.86, FOAM_SHADE)
            for (x, y), r in (((0.4, 3.6), 2.0), ((2.4, 5.2), 2.2), ((4.4, 6.9), 1.6)):
                K.oval(d, K.at(x, y), r, r * 0.86, FOAM)
            K.poly(d, [K.at(5.8, 6.6), K.at(9.0, 6.0), K.at(9.2, 8.6), K.at(7.0, 10.4), K.at(5.0, 9.6)], HAIR)
        else:
            K.poly(d, [K.at(-1.4, 2.6), K.at(2.0, 5.4), K.at(5.8, 6.4), K.at(9.0, 6.0), K.at(9.2, 8.6), K.at(7.0, 10.4), K.at(2.6, 9.6), K.at(-1.0, 6.0)], HAIR)
        # His moustache: black, with its ends curled up.
        K.stroke(d, [K.at(8.4, 4.2), K.at(5.6, 4.9), K.at(3.6, 4.2), K.at(3.0, 2.6)], HAIR, 1.5)
        K.stroke(d, [K.at(8.4, 4.2), K.at(10.6, 4.4), K.at(11.6, 2.8)], HAIR, 1.3)

    return paint


_HEADS = {}


def _head(lather: bool):
    if lather not in _HEADS:
        _HEADS[lather] = R.make_head(K, ("barber", lather), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.8, 7.8, 9.2), jaw=(2.6, 4.2, 5.2, 7.6),
                                     nose=((7.2, -1.2), (10.2, 2.6), (9.6, 4.0), (7.2, 4.4)), ear=(-4.8, 1.0, 2.2, 3.2), shape=_hair_shape, under=_hair,
                                     over=_face(lather))
    return _HEADS[lather]()


_eyes = R.make_eyes(K, (NEAR_EYE[0] + 0.2, NEAR_EYE[1] + 0.2), (FAR_EYE[0] + 0.1, FAR_EYE[1] + 0.2), ink=INK, white=None, lid=SKIN_DEEP, size=1.0)
# One brow is higher than the other. It is always so.
_brows = R.make_brows(K, [(-0.8, -4.6), (1.8, -5.6), (4.4, -4.8)], [(5.8, -3.6), (7.2, -3.9), (8.6, -3.4)], HAIR, 1.4)
_mouth = R.make_mouth(K, (5.6, 7.4), (124, 60, 62, 255), wide=0.7)

X.head_layers = lambda pose: [(_head(bool(pose["lather"])), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"),
                              (_mouth(str(pose["mouth"])), "mouth")]
X.neck = R.make_neck(K, SKIN_SHADE, 4.4)
# His sleeves are rolled to the elbow.
X.upper_arm = lambda near: [(0.0, 1.0, 6.2, 5.6, SHIRT if near else SHIRT_DARK)]
X.forearm = lambda near: [(0.0, 0.3, 6.0, 5.8, SHIRT if near else SHIRT_DARK), (0.26, 1.0, 4.8, 4.2, SKIN if near else SKIN_SHADE)]
X.thigh = lambda near: [(0.0, 1.0, 6.8, 5.8, TROUSER if near else TROUSER_DARK)]
X.shin = lambda near: [(0.0, 1.0, 5.8, 5.0, TROUSER if near else TROUSER_DARK)]
X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, size=1.0)
X.shoe = R.make_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up, long=1.08)

# ---- How he holds himself ----------------------------------------------------

# One hand at the tie of his apron, the other at his side. ``lather``: his
# cheek is in lather (and it is, but for a part of ``self_shave``).
X.set_rest(lean=0.0, na=(7.0, 21.0), nf=(-3.8, 0.0, 0.0), ff=(4.8, 0.0, 0.0), lather=True)


@X.row
def idle(i: int, n: int):
    # He waits for the next man, and looks at his own face in a glass that is not there.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 + 0.3 * s), lean=0.4 * s, head=(0.3, 0.0, -3.0 + 3.0 * c), eyes="closed" if i == n - 2 else "open", brows=1.0 if c > 0.5 else 0.0,
             mouth="flat")


@X.row
def walk(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 8.4, 4.4)
    swing = 6.0 * math.sin(ph)
    return P(hip=(0.5, 0.8 * math.cos(2.0 * ph)), lean=2.5, head=(0.3, 0.0, -2.0 + 1.5 * s), nf=nf, ff=ff, hem=(1.0 + abs(c), abs(c)),
             na=(-2.0 - swing, 26.0 - abs(swing) * 0.2), fa=(R.REST["fa"][0] + swing, R.REST["fa"][1] - abs(swing) * 0.2))


@X.row
def talk(i: int, n: int):
    # A finger up for each half of the rule.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), lean=1.5, head=(0.4, 0.0, 2.0 * s), na=(13.0 + 2.0 * c, 2.0 - 5.0 * max(0.0, s)), nh="point", mouth=("open", "smile", "big", "flat")[i % 4],
             brows=1.0 if s > 0.3 else 0.0)


#: The razor is back, and then it is through.
BACK = P(hip=(-1.5, 1.0), lean=-6.0, head=(0.0, 0.0, -4.0), na=(-10.0, -8.0), nab=-1.0, nh="fist", fa=(14.0, 8.0), fh="open", brows=-1.0, mouth="flat",
         nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0))
THROUGH = P(hip=(3.0, 2.0), lean=12.0, head=(1.0, 0.0, 6.0), na=(27.0, 4.0), nh="fist", fa=(-4.0, 16.0), brows=-1.0, mouth="grit", nf=(-8.0, 0.0, 0.0), ff=(10.0, 0.0, 0.0))


@X.row
def clean_cut(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, P()), (0.25, BACK), (0.4, THROUGH), (0.7, dict(THROUGH, na=(25.0, 8.0))), (1.0, P())])


#: A hand to his chin: he thinks about who shaves him.
THINK = P(lean=-1.0, head=(0.0, 0.0, -8.0), na=(10.0, -7.0), nh="point", fa=(6.0, 14.0), eyes="up", brows=1.0, mouth="flat")


@X.row
def paradox_loop(i: int, n: int):
    # It repeats: the row is a loop, as the question is.
    _, s, c = loop(i, n)
    return dict(THINK, head=(0.0, 0.0, -8.0 + 5.0 * s), hip=(0.0, 0.4 * c), eyes="up" if c > 0.0 else "closed", mouth="o" if s > 0.6 else "flat")


#: The razor at his own cheek.
SHAVE = P(lean=-2.0, head=(0.0, 0.0, -10.0), na=(9.0, -9.0), nh="fist", fa=(12.0, -6.0), fh="flat", eyes="up", brows=1.0, mouth="o")


@X.row
def self_shave(i: int, n: int):
    # He shaves his cheek clean, and so he is a man who shaves himself, and
    # so he is not shaved by the barber: the beard is on all of his jaw.
    u = shot(i, n)
    pose = X.keys(u, [(0.0, P()), (0.2, SHAVE), (0.45, dict(SHAVE, na=(11.0, -5.0))), (0.6, dict(SHAVE, na=(13.0, 0.0), eyes="happy", mouth="smile")),
                      (0.8, dict(SHAVE, na=(14.0, 4.0), eyes="wide", mouth="big", brows=1.0)), (1.0, P(eyes="closed", mouth="flat", brows=-1.0))])
    return dict(pose, lather=not 0.5 <= u < 0.9)


X.rows = [("idle", 8, 130), ("walk", 8, 102), ("talk", 8, 110), ("clean_cut", 8, 84), ("paradox_loop", 8, 96), ("self_shave", 8, 100), ("death", 8, 116)]

# ---- From the front ------------------------------------------------------------

def _front_apron(d) -> None:
    """His apron from the front: the bib and its straps over his shirt, his
    bow tie, the tie at his waist, the pocket, and the stripes of the pole."""
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(4.6 * sx, TOP - 2.0), K.at(14.0 * sx, TOP - 2.0), K.at(14.0 * sx, -8.0), K.at(6.0 * sx, -8.0), K.at(5.0 * sx, TOP + 6.0)], SHIRT)
        K.line(d, [K.at(5.0 * sx, TOP + 6.0), K.at(3.0 * sx, TOP - 1.0)], APRON_DARK, 1.0)
        K.line(d, [K.at(5.0 * sx, TOP + 6.0), K.at(6.0 * sx, -8.0)], APRON_DARK, 0.7)
    K.poly(d, [K.at(-3.4, TOP - 1.4), K.at(3.4, TOP - 1.4), K.at(2.6, TOP + 3.0), K.at(-2.6, TOP + 3.0)], SHIRT)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(0.4 * sx, TOP + 2.8), K.at(2.8 * sx, TOP + 1.4), K.at(2.8 * sx, TOP + 4.4)], RED)
    K.oval(d, K.at(0.0, TOP + 2.9), 0.9, 0.9, RED_DARK)
    K.line(d, [K.at(-9.6, -8.0), K.at(9.6, -8.0)], APRON_DARK, 0.8)
    K.rrect(d, K.home[0] - 3.4, K.home[1] - 3.0, K.home[0] + 3.4, K.home[1] + 4.0, 0.8, mix(APRON, APRON_DARK, 0.25), APRON_DARK, 0.6)
    K.poly(d, [K.at(-2.2, -6.4), K.at(-0.8, -6.4), K.at(-0.8, -2.4), K.at(-2.2, -2.4)], HAIR)
    K.poly(d, [K.at(-12.0, HEM - 6.0), K.at(12.0, HEM - 6.0), K.at(12.0, HEM - 1.2), K.at(-12.0, HEM - 1.2)], FOAM)
    for k in range(-3, 4):
        x = k * 4.4 - 1.8
        K.poly(d, [K.at(x, HEM - 1.2), K.at(x + 2.2, HEM - 6.0), K.at(x + 3.6, HEM - 6.0), K.at(x + 1.4, HEM - 1.2)], RED if k % 2 == 0 else BLUE)
    K.line(d, [K.at(-12.0, HEM - 6.0), K.at(12.0, HEM - 6.0)], APRON_DARK, 0.5)


def _front_hair_shape(d) -> None:
    K.oval(d, K.at(0.0, -6.0), 9.2, 6.8, WHITE)
    K.poly(d, [K.at(-2.0, -12.4), K.at(5.0, -13.4), K.at(8.4, -9.0), K.at(2.0, -8.0)], WHITE)


def _front_hair(d) -> None:
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -2.0), K.at(7.8, -2.0), K.at(7.2, -6.4), K.at(3.0, -8.4), K.at(-3.0, -7.2), K.at(-6.4, -6.6),
               K.at(-7.8, -2.0), K.at(-20.0, -2.0)], HAIR)
    K.line(d, [K.at(-3.0, -12.4), K.at(-3.4, -7.4)], SKIN_SHADE, 0.5)
    for strand in ([(-1.0, -11.6), (3.0, -12.2), (6.6, -9.6)], [(-7.0, -8.0), (-6.6, -4.0)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_SHADE, 0.6)


def _front_paradox(d) -> None:
    # From the front the paradox is two halves: lather on one cheek, a beard
    # on the other. And his moustache, with both ends up.
    for (x, y), r in (((-5.0, 4.0), 2.4), ((-3.6, 6.6), 2.6), ((-1.6, 8.8), 2.0)):
        K.oval(d, K.at(x, y), r, r * 0.86, FOAM_SHADE)
    for (x, y), r in (((-5.2, 3.6), 2.0), ((-3.8, 6.0), 2.2), ((-1.8, 8.2), 1.6)):
        K.oval(d, K.at(x, y), r, r * 0.86, FOAM)
    K.poly(d, [K.at(0.2, 7.0), K.at(3.0, 6.4), K.at(6.6, 3.0), K.at(6.4, 7.6), K.at(3.6, 11.0), K.at(0.4, 11.4)], HAIR)
    K.line(d, [K.at(-0.3, 0.6), K.at(-1.2, 3.6), K.at(0.0, 4.4), K.at(1.2, 3.6)], SKIN_DEEP, 0.6)
    for sx in (-1.0, 1.0):
        K.stroke(d, [K.at(0.0, 5.4), K.at(3.0 * sx, 6.2), K.at(5.0 * sx, 5.2), K.at(5.6 * sx, 3.4)], HAIR, 1.4)


X.front_torso = R.make_front_torso(K, ("barber",), APRON, APRON_DARK, [(TOP, 4.0), (TOP + 3.6, 8.6), (-24.0, 9.0), (-8.0, 8.8), (HEM, 10.6)],
                                   shoulder=(7.0, -32.0, 4.2, 4.6), detail=_front_apron)
X.front_head_layers = R.front_face(R.make_front_head(K, ("barber",), SKIN, SKIN_DEEP, wide=7.8, jaw=6.2, chin=4.2, ears=SKIN, shape=_front_hair_shape, hair=_front_hair,
                                                    face=_front_paradox),
                                   R.make_front_eyes(K, ("barber",), white=None, ink=INK, spread=3.4, y=-0.8),
                                   R.make_front_brows(K, ("barber",), HAIR, spread=3.4, y=-4.4, width=1.4))
X.front_shoe = R.make_front_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up)
X.front_span = (7.8, 4.6)
R.add_front_rows(X)

# ---- What he shows -----------------------------------------------------------


def _razor(open_: bool = True):
    """His razor, along +x from the hand that holds it: the handle, and the
    blade out of it."""

    def shape(d) -> None:
        K.stroke(d, [K.at(-6.0, 1.6), K.at(2.0, 0.6)], WHITE, 3.0)
        if open_:
            K.poly(d, [K.at(1.0, -1.6), K.at(13.0, -2.6), K.at(14.0, 0.2), K.at(12.6, 2.0), K.at(1.4, 1.6)], WHITE)

    def detail(d) -> None:
        K.stroke(d, [K.at(-6.0, 1.6), K.at(2.0, 0.6)], HAIR, 2.2)
        K.oval(d, K.at(1.4, 0.4), 0.8, 0.8, GOLD)
        if open_:
            K.line(d, [K.at(2.0, 1.2), K.at(12.8, 1.6)], STEEL_DARK, 0.6)
            K.line(d, [K.at(2.0, -1.2), K.at(12.6, -2.0)], WHITE, 0.5)

    return K.solid(("razor", open_), shape, STEEL, detail, outline=1.0, rim=0.0, shade=0.0)


def _question(turn: int):
    """Is x in x? The question, and the arrow that takes it back to its
    start."""

    def paint(d) -> None:
        pts = [K.at(15.0 * math.cos(math.radians(a + turn)), 6.0 * math.sin(math.radians(a + turn))) for a in range(20, 341, 20)]
        K.line(d, pts, GOLD_DARK, 2.0)
        K.line(d, pts, GOLD, 0.9)
        tip, before = pts[-1], pts[-2]
        back = math.atan2(before[1] - tip[1], before[0] - tip[0])
        for da in (-0.6, 0.6):
            K.line(d, [tip, (tip[0] + 4.0 * math.cos(back + da), tip[1] + 4.0 * math.sin(back + da))], GOLD, 1.2)

    return K.aligned(("question", turn), paint)


def _fleck(r: float):
    return R.dust(K, r, FOAM, FOAM_SHADE)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, i, u = ctx.anim, ctx.i, ctx.u
    grip = math.degrees(math.atan2(ctx.hand[1] - ctx.elbow[1], ctx.hand[0] - ctx.elbow[0]))
    if anim == "clean_cut":
        if 0.15 <= u <= 0.85:
            out.append((_razor(), ctx.hand, "razor", grip - 20.0))
        if 0.35 <= u <= 0.6:
            out.append((R.swoosh(K, 26.0, -70, 30, 4.0, STEEL, STEEL_DARK), pin((ctx.shoulder[0] + 6.0, ctx.shoulder[1] + 6.0)), "cut", 0.0))
    elif anim == "paradox_loop":
        out.append((_question(45 * i), pin((ctx.head[0] + 1.0, ctx.head[1] - 20.0)), "loop", 0.0))
        out.append((R.glyph(K, ["x", "in", "x", "?"], 7.0, GOLD, GOLD_DARK), (ctx.head[0] + 2.0, ctx.head[1] - 33.0), "question", 0.0))
    elif anim == "self_shave":
        if 0.15 <= u < 0.9:
            out.append((_razor(), ctx.hand, "razor", grip - 60.0))
        if 0.3 <= u < 0.6:
            for k in range(3):
                t = (u - 0.3) / 0.3
                out.append((_fleck(1.6 - 0.3 * k), (ctx.head[0] + 6.0 + 7.0 * t * (k + 1), ctx.head[1] + 4.0 + 14.0 * t * t + 2.0 * k), f"fleck_{k}", 0.0))
        if 0.6 <= u < 0.95:
            out.append((R.glyph(K, "?" if u < 0.8 else "!", 9.0, GOLD, GOLD_DARK), (ctx.head[0] + 14.0, ctx.head[1] - 20.0), "mark", 0.0))
    return out


X.effects = _effects

ROWS = X.rows
FRAME_SIZE = X.frame
render_frame = X.render_frame
_render_frame = render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet: the clips his conversations
    name."""
    del opts
    r8 = tuple(range(8))
    return X.portraits(out_dir, {
        "default": ("idle", r8, 148, True),
        "portrait": ("idle", (1,), 0, False),
        "talk": ("talk", r8, 110, True),
        "paradox": ("paradox_loop", r8, 96, True),
    }, still="portrait", view_width=36.0)


# ---- In the round (``_round_cast``) --------------------------------------------
#
# His trunk and head in 3D come from the numbers of his own makers
# (``auto_trunk``, ``auto_head``); what they do not say is here, as data.
# His rows do not use this.

import numpy as np  # noqa: E402

from . import _person_round as O  # noqa: E402
from . import _round_cast as C  # noqa: E402
from . import _round_wear as W  # noqa: E402


_OILED = ((0.0, -5.6, -0.6), (8.4, 7.0, 8.4))
_head(True)  # his head with lather is the one at rest (``set_rest``)

ROUND = C.Round(
    DISPLAY_NAME, C.PersonBody(X),
    C.Look(
        # Dark hair with oil in it and a parting; a moustache whose ends curl
        # up; the paradox: lather on his cheek, and a beard on his chin.
        C.auto_head(X, _HEADS[True], _eyes,
                    hair=lambda u, v: (v < -7.2 + 1.2 * np.clip(np.abs(u) / 60.0, 0.0, 1.0)) | ((np.abs(u) > 70.0) & (v < -0.6))
                    | ((np.abs(u) > 100.0) & (v < 5.0)),
                    hair_colour=HAIR, hair_shade=HAIR_SHADE, volumes=[_OILED], moustache=((0.0, 5.0, 7.6), (4.4, 1.0, 1.6)),
                    beard=[O.Ring(8.4, 0.0, 4.4, 3.0, 2.8), O.Ring(10.6, 0.0, 4.6, 2.4, 2.2), O.Ring(12.6, 0.0, 4.4, 0.4, 0.4)],
                    lines=[O.curve([O.on_ellipsoid(*_OILED, -20.0, v, 0.2)[0] for v in (-12.0, -7.6)], SKIN_SHADE, 0.5),
                           O.curve([(-4.2, 5.0, 7.0), (-5.6, 4.2, 6.2), (-5.4, 3.0, 5.8)], HAIR, 0.8),
                           O.curve([(4.2, 5.0, 7.0), (5.6, 4.2, 6.2), (5.4, 3.0, 5.8)], HAIR, 0.8),
                           O.circle((-5.6, 4.0, 4.6), (-1.0, 0.2, 0.6), 2.2, None, fill=FOAM, slack=1.2)]),
        # His long cream apron in front, its bib to his collar, tied at his
        # waist, a pocket with his comb, the stripes of the pole at its hem;
        # behind it his white shirt and his dark trousers; his collar and red
        # bow tie.
        C.auto_trunk(X, [W.Behind(70.0, SHIRT, bottom=-8.0), W.Behind(70.0, TROUSER, top=-8.0), W.Down(70.0, TOP + 4.0, HEM, APRON_DARK),
                         W.Down(-70.0, TOP + 4.0, HEM, APRON_DARK), W.Strip(0.0, TOP - 1.4, TOP + 3.0, 4.0, SHIRT),
                         W.Glow(-9.0, TOP + 2.8, 1.8, 1.3, RED, both=True), W.Dot(0.0, TOP + 2.8, 0.9, RED_DARK),
                         W.Across(-180.0, 180.0, -8.0, APRON_DARK, width=0.4), W.Patch(10.0, 45.0, -3.0, 4.0, mix(APRON, APRON_DARK, 0.25)),
                         W.Patch(14.0, 20.0, -6.4, -2.4, HAIR),
                         W.Stripes(HEM - 6.0, HEM - 1.2, 2.2, (RED, FOAM, BLUE, FOAM), slant=0.45, half=70.0)])),
    # Straight: his near hand forward, as if it held his scissors.
    C.Stance(hands={"r": C.Hand(l=-6.0, pole=(-1.0, 0.4, -0.4)), "l": C.Hand(l=9.2, pole=(0.4, 0.0, -1.0))}, stagger=2.0))


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

del OUTLINE

if __name__ == "__main__":
    raise SystemExit(main())
