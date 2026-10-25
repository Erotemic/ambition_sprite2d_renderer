"""Sprite generator for Davy Hylbert: the proprietor of a hotel that is full,
and that has a room for you.

A flamboyant parody of David Hilbert.

The look (2026-10-13): a spare, upright man of sixty seen three quarters from
the front, facing right, as the photograph has him: the pale summer hat with
its dark band, round wire glasses, a white moustache and a short white beard
that comes to a point. A dark blue suit of three pieces with a watch chain
across the waistcoat, a wing collar and a bow tie. He stands like a man who
is about to address a congress, with a thumb in his waistcoat pocket.

He is drawn from the photograph of the man and not from a type (Jon,
2026-10-13, of another person of this cast: "needs to read like paul erdos
not bearnie sanders"). He is a grown man, not a mascot. He holds nothing;
there is no drop shadow.

What he shows: the doors of his hotel, each with its number, and how every
guest moves up one; the bell on his desk; the sign for what has no end.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, how he stands and what he shows are his.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, lerp, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "davy_hylbert"
DISPLAY_NAME = "Davy Hylbert"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_davy_hylbert", "display_name": "Davy Hylbert"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "mathematician",
            "axiomatic_showman",
            "infinite_hotel",
            "playable_candidate",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": True,
            "fly": None,
            "swim": True,
            "crawl": True,
            "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle"},
    "tags": [
        "story",
        "humanoid",
        "mathematician",
        "axiomatic_showman",
        "infinite_hotel",
        "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 65.0, "y": 28.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 65.0, "y": 63.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 48.0, "y": 79.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 84.0, "y": 79.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 65.0, "y": 5.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "prime_stride", "events": []},
        "action.ranged.primary": {"animation": "compressed_sense", "events": []},
        "action.special.primary": {"animation": "full_turn", "events": []},
        "action.special.secondary": {"animation": "polymath_chain", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Davy Hylbert is a flamboyant parody of David Hilbert, especially Hilbert's Hotel and the "
            "formalist dream of organizing mathematics through axioms. He treats infinity as a "
            "hospitality and logistics problem that can always admit one more guest."
        ),
        "gameplay_description": (
            "Use as an infinite-hotel proprietor, axiomatic showman, puzzle master, or spatial boss. "
            "His mechanics should shift every occupant, relabel rooms, and make apparently full "
            "spaces accept additional entities."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'Every room is occupied, and yet we continue admitting guests.',
        'Infinity rewards orderly management.',
        'When a level feels full, try a shift.',
    ],
)

SUIT: RGBA = (52, 66, 110, 255)
SUIT_DARK: RGBA = (32, 42, 78, 255)
SUIT_LIGHT: RGBA = (90, 106, 154, 255)
VEST: RGBA = (72, 88, 134, 255)
SHIRT: RGBA = (248, 246, 238, 255)
TIE: RGBA = (150, 46, 58, 255)
CHAIN: RGBA = (244, 206, 104, 255)
CHAIN_DARK: RGBA = (190, 130, 50, 255)
SHOE: RGBA = (60, 44, 40, 255)
SHOE_DARK: RGBA = (32, 24, 26, 255)
SKIN: RGBA = (238, 206, 184, 255)
SKIN_SHADE: RGBA = (208, 168, 150, 255)
SKIN_DEEP: RGBA = (164, 112, 104, 255)
BEARD: RGBA = (244, 242, 236, 255)
BEARD_DARK: RGBA = (184, 188, 198, 255)
HAT: RGBA = (240, 232, 208, 255)
HAT_DARK: RGBA = (190, 178, 150, 255)
BAND: RGBA = (56, 50, 60, 255)
FRAME: RGBA = (70, 60, 50, 255)
LENS: RGBA = (232, 244, 250, 150)
INK: RGBA = (28, 24, 32, 255)
DOOR: RGBA = (176, 116, 70, 255)
DOOR_DARK: RGBA = (104, 64, 44, 255)
BRASS: RGBA = (250, 214, 110, 255)

#: 170 cm, spare, very straight.
BUILD = Build(hip_up=48.0, thigh=23.2, shin=22.0, neck=(0.2, -36.0), upper=19.0, fore=18.0, near_shoulder=(-5.4, -31.8), far_shoulder=(6.8, -31.4),
              near_hip=(-3.4, 0.0), far_hip=(3.4, 0.0), head_up=(0.9, -12.4), height=109.0, half_width=(12.5, 14.0))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0


def _front(d, hb: float, hf: float) -> None:
    """The waistcoat and its chain where the jacket hangs open, the wing
    collar and the bow tie."""
    K.poly(d, [K.at(2.2, TOP), K.at(11.6, TOP), K.at(12.0 + hf, 12.0), K.at(4.8 + hf * 0.5, 12.0), K.at(3.8, -14.0)], VEST)
    K.poly(d, [K.at(9.4, TOP), K.at(12.6, TOP), K.at(13.0 + hf, 12.0), K.at(10.2 + hf, 12.0)], SUIT_DARK)
    K.poly(d, [K.at(3.6, TOP - 1.0), K.at(8.8, TOP - 1.0), K.at(6.6, TOP + 9.0)], SHIRT)
    K.poly(d, [K.at(3.6, TOP + 1.0), K.at(6.2, TOP + 2.6), K.at(3.6, TOP + 4.4)], TIE)
    K.poly(d, [K.at(8.8, TOP + 1.0), K.at(6.2, TOP + 2.6), K.at(8.8, TOP + 4.4)], TIE)
    for y in (-18.0, -12.0, -6.0):
        K.oval(d, K.at(6.6, y), 0.8, 0.8, SUIT_DARK)
    K.line(d, [K.at(4.6, -10.0), K.at(7.0, -7.6), K.at(9.6, -9.6)], CHAIN_DARK, 1.4)
    K.line(d, [K.at(4.6, -10.0), K.at(7.0, -7.6), K.at(9.6, -9.6)], CHAIN, 0.7)
    K.poly(d, [K.at(-0.6, TOP + 1.0), K.at(3.0, TOP), K.at(4.2, -20.0), K.at(0.2, -28.0)], SUIT_LIGHT)
    K.line(d, [K.at(0.2, -28.0), K.at(4.2, -20.0), K.at(3.8, -14.0), K.at(4.8 + hf * 0.5, 9.0)], SUIT_DARK, 0.7)
    K.line(d, [K.at(-7.0, -3.4), K.at(-1.4, -2.8)], SUIT_DARK, 0.7)


X.torso = R.make_torso(K, ("hylbert",), SUIT, SUIT_DARK, back=(9.0, 9.4, 8.4, 9.4), front=(8.2, 9.8, 9.2, 9.8), hem_y=9.5, top=TOP,
                       shoulders=((-5.2, -31.2), (6.2, -31.0)), shoulder_r=(5.2, 4.8), shade_from=40.0, detail=_front)

NEAR_EYE = (1.6, -0.4)
FAR_EYE = (7.0, -0.6)


def _shape(d) -> None:
    # The beard, to a point; and a little white hair at the back of his head.
    K.poly(d, [K.at(-1.0, 5.0), K.at(9.0, 5.6), K.at(8.6, 10.0), K.at(6.0, 14.6), K.at(4.4, 16.6), K.at(2.0, 13.0), K.at(-0.6, 9.0)], WHITE)
    K.oval(d, K.at(-5.6, 1.0), 3.6, 5.0, WHITE)


def _under(d) -> None:
    K.poly(d, [K.at(-3.4, -8.0), K.at(-3.6, -1.6), K.at(-6.4, -1.6), K.at(-7.0, 3.6), K.at(-5.2, 4.8), K.at(-4.8, 6.6), K.at(-20.0, 6.6), K.at(-20.0, -8.0)], BEARD)
    K.line(d, [K.at(-5.6, -4.0), K.at(-8.0, 0.0), K.at(-7.6, 4.0)], BEARD_DARK, 0.6)


def _over(d) -> None:
    for (cx, cy), r in ((NEAR_EYE, 2.8), (FAR_EYE, 2.0)):
        K.oval(d, K.at(cx, cy), r, r, LENS)
    # His moustache, wide; and the beard under it.
    K.poly(d, [K.at(-1.2, 4.8), K.at(3.0, 6.6), K.at(9.4, 5.6), K.at(9.0, 10.0), K.at(6.0, 14.6), K.at(4.4, 17.0), K.at(2.0, 13.0), K.at(-0.8, 9.0)], BEARD)
    K.poly(d, [K.at(1.6, 5.4), K.at(5.0, 4.4), K.at(9.6, 5.2), K.at(10.4, 7.0), K.at(6.0, 6.6), K.at(1.2, 7.4)], BEARD)
    K.line(d, [K.at(1.6, 7.4), K.at(6.0, 6.8), K.at(10.0, 7.0)], BEARD_DARK, 0.6)
    for x0, y0, x1, y1 in ((2.4, 9.6, 3.6, 14.0), (5.4, 9.6, 5.0, 14.6)):
        K.line(d, [K.at(x0, y0), K.at(x1, y1)], BEARD_DARK, 0.5)
    K.line(d, [K.at(3.6, 8.6), K.at(5.6, 9.2), K.at(7.6, 8.6)], (140, 80, 84, 255), 0.7)


def _glasses():
    def paint(d) -> None:
        for (cx, cy), r in ((NEAR_EYE, 2.8), (FAR_EYE, 2.0)):
            K.oval(d, K.at(cx, cy), r, r, None, FRAME, 0.6)  # type: ignore[arg-type]
        K.line(d, [K.at(NEAR_EYE[0] + 2.8, -0.8), K.at(FAR_EYE[0] - 2.0, -0.9)], FRAME, 0.6)
        K.line(d, [K.at(NEAR_EYE[0] - 2.8, -0.8), K.at(-4.6, -0.4)], FRAME, 0.6)

    return K.piece(("hylbert_glasses",), paint)


def _hat():
    """The summer hat: a pale crown with a dent, a dark band, a brim that
    comes down a little in front."""

    def shape(d) -> None:
        K.poly(d, [K.at(-8.0, -8.4), K.at(-7.0, -16.0), K.at(-2.0, -17.6), K.at(1.0, -16.0), K.at(5.0, -17.6), K.at(8.6, -15.0), K.at(8.4, -8.0)], WHITE)
        K.poly(d, [K.at(-13.6, -7.0), K.at(-8.0, -9.4), K.at(9.0, -9.6), K.at(15.0, -6.0), K.at(14.6, -4.8), K.at(-13.4, -5.4)], WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(-8.4, -11.6), K.at(9.0, -12.0), K.at(9.0, -8.6), K.at(-8.4, -8.2)], BAND)
        K.line(d, [K.at(-13.0, -5.8), K.at(14.4, -5.4)], HAT_DARK, 0.7)

    return K.solid(("hylbert_hat",), shape, HAT, detail, outline=1.2, rim=0.3, shade=0.35, shade_colour=HAT_DARK)


_head = R.make_head(K, ("hylbert",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.4, 7.8, 8.8), jaw=(2.6, 4.0, 5.4, 7.2),
                    nose=((7.2, -0.8), (10.2, 3.0), (9.6, 4.6), (7.2, 5.0)), ear=(-5.0, 1.0, 2.0, 3.0), shape=_shape, under=_under, over=_over)
_eyes = R.make_eyes(K, (NEAR_EYE[0] + 0.2, NEAR_EYE[1] + 0.2), (FAR_EYE[0] + 0.1, FAR_EYE[1] + 0.2), ink=INK, white=None, lid=SKIN_DEEP, size=0.9)
_brows = R.make_brows(K, [(-1.2, -4.2), (1.6, -5.0), (4.4, -4.4)], [(5.8, -4.6), (7.2, -5.0), (8.6, -4.4)], BEARD, 1.2, under=BEARD_DARK)

X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_glasses(), "glasses"), (_brows(R.brow_mood(pose)), "brows")] + (
    [] if float(pose["hat"]) < 0.5 else [(_hat(), "hat")])
X.neck = R.make_neck(K, SKIN_SHADE, 4.4)
X.upper_arm = lambda near: [(0.0, 1.0, 6.8, 5.8, SUIT if near else SUIT_DARK)]
X.forearm = lambda near: [(0.0, 1.0, 5.8, 5.0, SUIT if near else SUIT_DARK)]
X.thigh = lambda near: [(0.0, 1.0, 7.2, 6.0, SUIT if near else SUIT_DARK)]
X.shin = lambda near: [(0.0, 1.0, 6.0, 5.2, SUIT if near else SUIT_DARK)]
X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, SHIRT, (206, 206, 212, 255))
X.shoe = R.make_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up)

# ---- How he holds himself ----------------------------------------------------

#: A thumb in his waistcoat pocket. The other hand behind him.
IN_POCKET = (5.5, 15.0)
BEHIND = (-5.0, 23.0)
#: ``hat``: 1, it is on his head. 0: it is in his hand (and drawn there).
X.set_rest(na=IN_POCKET, nh="fist", fa=BEHIND, nf=(-3.6, 0.0, 0.0), ff=(4.6, 0.0, 0.0), hat=1.0)


@X.row
def idle(i: int, n: int):
    # He stands as if the hall were waiting for him, and it is.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 + 0.3 * s), lean=-1.0, head=(0.2, -0.2 * s, -2.0 + 2.0 * c), eyes="closed" if i == n - 2 else "open", brows=1.0 if c > 0.7 else 0.0)


@X.row
def walk(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 8.2, 4.6)
    return P(hip=(0.5, 0.8 * math.cos(2.0 * ph)), lean=1.0, head=(0.0, 0.0, 1.0 * s), fa=(2.0 + 7.0 * c, 24.0), nf=nf, ff=ff, hem=(1.0 + abs(c), abs(c)))


@X.row
def talk(i: int, n: int):
    # One arm out to the hall: "we must know, we shall know."
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), lean=-2.0, head=(0.3, 0.0, -2.0 + 2.0 * s), fa=(20.0 + 2.0 * c, -2.0 - 5.0 * max(0.0, s)), fh="open",
             eyes="happy" if i == n - 3 else "open", brows=1.0 if s > 0.2 else 0.0)


#: His hat in his hand, held out: after you.
DOFFED = P(hip=(-1.0, 1.0), lean=10.0, head=(1.0, 0.5, 6.0), na=(18.0, 8.0), nh="fist", fa=BEHIND, eyes="happy", hat=0.0)


@X.row
def celebrate(i: int, n: int):
    # He takes his hat off to the theorem.
    _, s, _c = loop(i, n)
    return X.keys(shot(i, n), [(0.0, P()), (0.25, dict(P(na=(8.0, -12.0), nh="fist"), hat=1.0)), (0.5, DOFFED), (0.85, dict(DOFFED, na=(18.0, 6.0 + s))), (1.0, DOFFED)])


@X.row
def taunt(i: int, n: int):
    # He rings the bell on his desk. There is a room. There is always a room.
    ring = P(hip=(1.0, 1.0), lean=6.0, na=(18.0, 12.0), nh="flat", fa=BEHIND, brows=1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.3, dict(ring, na=(18.0, 6.0))), (0.45, ring), (0.6, dict(ring, na=(18.0, 7.0))), (0.75, ring), (1.0, dict(ring, eyes="happy"))])


@X.row
def charge(i: int, n: int):
    # He counts the rooms. He does not get to the end.
    _, s, _c = loop(i, n)
    return P(hip=(0.0, 1.0 + 0.4 * s), lean=2.0, head=(0.0, 0.0, -6.0), na=(12.0, -4.0 - 2.0 * (i % 2)), nh="point", fa=BEHIND, eyes="up", brows=1.0)


@X.row
def full_turn(i: int, n: int):
    # All the way round on one heel, his arms out, and his coat goes with him.
    ph, s, c = loop(i, n)
    return P(hip=(0.0, 1.0), lean=6.0 * s, head=(0.0, 0.0, 8.0 * s), na=(-18.0 + 8.0 * c, -2.0), nab=-1.0, fa=(20.0 - 8.0 * c, -2.0), nh="open", fh="open",
             nf=(-4.0 + 3.0 * s, 0.0, 0.0), ff=(5.0 - 3.0 * s, -1.0 * abs(c), 10.0), mouth="open", hem=(4.0 * abs(s), 4.0 * abs(c)))


X.alias(epsilon_dash="dash", prime_stride="attack_side", compressed_sense="charge", polymath_chain="cast")
X.rows = [("idle", 8, 145), ("walk", 8, 104), ("run", 8, 76), ("crouch", 6, 95), ("crouch_walk", 8, 88), ("jump", 6, 92), ("fall", 6, 92), ("land_hard", 8, 92),
          ("land_recovery", 6, 72), ("dash_startup", 4, 48), ("dash", 6, 60), ("epsilon_dash", 8, 54), ("slide", 6, 68), ("roll", 8, 56), ("wall_grab", 6, 105),
          ("wall_jump", 6, 82), ("ledge_grab", 6, 98), ("ledge_climb", 6, 98), ("ledge_getup", 6, 42), ("ledge_roll", 8, 38), ("climb", 8, 98), ("swim", 8, 102),
          ("float_glide", 8, 108), ("block", 6, 82), ("hit", 5, 86), ("death", 8, 105), ("talk", 8, 104), ("interact", 8, 90), ("jab", 5, 56), ("punch", 7, 68),
          ("prime_stride", 8, 64), ("attack_up", 8, 64), ("attack_down", 8, 64), ("air_neutral", 8, 60), ("air_forward", 7, 60), ("air_back", 7, 60), ("air_down", 7, 68),
          ("air_up", 7, 60), ("compressed_sense", 8, 74), ("polymath_chain", 8, 78), ("full_turn", 10, 76), ("celebrate", 8, 88), ("taunt", 8, 92)]

# ---- From the front ------------------------------------------------------------

def _front_suit(d) -> None:
    """His three-piece suit from the front: the waistcoat and its chain, the
    shirt and the tie, a lapel each side."""
    K.poly(d, [K.at(-4.8, TOP), K.at(4.8, TOP), K.at(5.6, 9.0), K.at(-5.6, 9.0)], VEST)
    K.poly(d, [K.at(-3.0, TOP - 1.0), K.at(3.0, TOP - 1.0), K.at(0.0, -27.0)], SHIRT)
    K.poly(d, [K.at(-1.0, TOP + 0.6), K.at(1.0, TOP + 0.6), K.at(1.2, -25.0), K.at(0.0, -23.6), K.at(-1.2, -25.0)], TIE)
    K.line(d, [K.at(-4.6, -9.0), K.at(-1.0, -6.6), K.at(3.6, -8.6)], CHAIN_DARK, 1.1)
    K.line(d, [K.at(-4.6, -9.0), K.at(-1.0, -6.6), K.at(3.6, -8.6)], CHAIN, 0.5)
    for y in (-19.0, -13.0, -3.0):
        K.oval(d, K.at(0.0, y), 0.7, 0.7, SUIT_DARK)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(4.8 * sx, TOP), K.at(7.4 * sx, TOP + 1.0), K.at(5.6 * sx, -20.0)], SUIT_LIGHT)
        K.line(d, [K.at(5.6 * sx, -20.0), K.at(5.6 * sx, 9.0)], SUIT_DARK, 0.7)


def _front_hat_shape(d) -> None:
    # The hat, its brim wider than his head; and his beard, to his collar.
    K.rrect(d, K.home[0] - 7.6, K.home[1] - 16.6, K.home[0] + 7.6, K.home[1] - 7.0, 2.6, WHITE)
    K.oval(d, K.at(0.0, -7.4), 12.6, 2.6, WHITE)
    K.poly(d, [K.at(-6.6, 4.0), K.at(6.6, 4.0), K.at(5.4, 12.0), K.at(0.0, 16.0), K.at(-5.4, 12.0)], WHITE)


def _front_hat(d) -> None:
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -6.0), K.at(-20.0, -6.0)], HAT)
    K.poly(d, [K.at(-20.0, -10.4), K.at(20.0, -10.4), K.at(20.0, -8.4), K.at(-20.0, -8.4)], BAND)
    K.line(d, [K.at(-12.0, -6.0), K.at(12.0, -6.0)], HAT_DARK, 0.9)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(6.0 * sx, -5.6), K.at(9.0 * sx, -5.6), K.at(9.0 * sx, 1.0), K.at(7.0 * sx, 1.0)], BEARD)


def _front_beard(d) -> None:
    K.poly(d, [K.at(-7.0, 3.6), K.at(-3.6, 5.6), K.at(0.0, 5.0), K.at(3.6, 5.6), K.at(7.0, 3.6), K.at(5.6, 12.0), K.at(0.0, 16.0), K.at(-5.6, 12.0)], BEARD)
    for x in (-3.0, 0.0, 3.0):
        K.line(d, [K.at(x, 8.0), K.at(x * 0.8, 13.0)], BEARD_DARK, 0.5)
    K.line(d, [K.at(-2.4, 8.6), K.at(0.0, 9.2), K.at(2.4, 8.6)], (150, 90, 90, 255), 0.7)
    for sx in (-1.0, 1.0):
        K.oval(d, K.at(3.4 * sx, -0.6), 2.9, 2.9, LENS, FRAME, 0.8)
        K.line(d, [K.at(6.2 * sx, -0.8), K.at(8.0 * sx, -1.4)], FRAME, 0.7)
    K.line(d, [K.at(-0.5, -0.8), K.at(0.5, -0.8)], FRAME, 0.7)
    K.line(d, [K.at(-0.3, 0.8), K.at(-1.2, 3.4), K.at(0.0, 4.2), K.at(1.2, 3.4)], SKIN_DEEP, 0.6)


X.front_torso = R.make_front_torso(K, ("hylbert",), SUIT, SUIT_DARK, [(TOP, 4.2), (TOP + 3.6, 9.2), (-24.0, 9.8), (-6.0, 9.8), (9.5, 10.2)],
                                   shoulder=(7.4, -31.8, 4.4, 4.8), detail=_front_suit)
X.front_head_layers = R.front_face(R.make_front_head(K, ("hylbert",), SKIN, SKIN_DEEP, wide=7.8, jaw=6.4, chin=3.8, ears=SKIN, shape=_front_hat_shape, hair=_front_hat,
                                                    face=_front_beard),
                                   R.make_front_eyes(K, ("hylbert",), white=None, ink=INK, spread=3.4, y=-0.6, size=0.9),
                                   R.make_front_brows(K, ("hylbert",), BEARD_DARK, spread=3.4, y=-4.4))
X.front_shoe = R.make_front_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up)
X.front_span = (8.2, 4.6)
R.add_front_rows(X)

# ---- What he shows -----------------------------------------------------------


def _door(number: str, open_: bool = False):
    """A door of his hotel, with its number, from the middle of its foot."""

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 5.0, K.home[1] - 15.0, K.home[0] + 5.0, K.home[1], 1.0, WHITE)

    def detail(d) -> None:
        if open_:
            K.rrect(d, K.home[0] - 3.6, K.home[1] - 13.6, K.home[0] + 3.6, K.home[1], 0.0, (255, 240, 190, 255))
        K.oval(d, K.at(3.0, -6.6), 0.8, 0.8, BRASS)
        wide = 2.2 * len(number)
        for k, ch in enumerate(number):
            x0 = -wide / 2.0 + k * 2.4
            for line in R.STROKES[ch]:
                K.line(d, [K.at(x0 + x * 1.8, -12.4 + y * 3.4) for x, y in line], BRASS if not open_ else DOOR_DARK, 0.6)

    return K.solid(("door", number, open_), shape, DOOR, detail, outline=1.0, rim=0.3, shade=0.4, shade_colour=DOOR_DARK)


def _bell():
    def shape(d) -> None:
        K.poly(d, [K.at(-5.0, 0.0), K.at(-3.6, -4.6), K.at(0.0, -6.0), K.at(3.6, -4.6), K.at(5.0, 0.0)], WHITE)
        K.oval(d, K.at(0.0, -6.6), 1.2, 1.2, WHITE)
        K.rrect(d, K.home[0] - 6.0, K.home[1], K.home[0] + 6.0, K.home[1] + 1.8, 0.6, WHITE)

    return K.solid(("bell",), shape, BRASS, None, outline=1.0, rim=0.4, shade=0.4, shade_colour=CHAIN_DARK)


def _hat_in_hand():
    def shape(d) -> None:
        K.poly(d, [K.at(-4.0, -3.0), K.at(-3.0, -9.0), K.at(6.0, -9.0), K.at(7.0, -3.0)], WHITE)
        K.poly(d, [K.at(-9.0, -3.4), K.at(12.0, -3.4), K.at(12.0, -1.6), K.at(-9.0, -1.6)], WHITE)

    return K.solid(("hat_in_hand",), shape, HAT, lambda d: K.rrect(d, K.home[0] - 4.2, K.home[1] - 5.6, K.home[0] + 7.2, K.home[1] - 3.4, 0.0, BAND), outline=1.2,
                   rim=0.3, shade=0.35, shade_colour=HAT_DARK)


def _sym(symbols, size: float, fill: RGBA = BRASS):
    return R.glyph(K, symbols, size, fill, CHAIN_DARK)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, i, n, u, hand, head, hip = ctx.anim, ctx.i, ctx.n, ctx.u, ctx.hand, ctx.head, ctx.hip

    def doors(origin, first: int, count: int, step: float = 12.0, shift: float = 0.0) -> None:
        for k in range(count):
            out.append((_door(str(first + k), False), (origin[0] + k * step + shift, origin[1]), f"door_{k}", 0.0))

    if float(ctx.pose["hat"]) < 0.5:
        out.append((_hat_in_hand(), (hand[0] + 2.0, hand[1] + 1.0), "hat", 14.0))
    if anim == "jab" and 1 <= i <= 3:
        out.append((_sym("1", 8.0), (hand[0] + 18.0, hand[1] - 2.0), "one", 0.0))
    elif anim == "punch" and 3 <= i <= 5:
        out.append((R.burst(K, 8.0 + (i - 3), BRASS, CHAIN_DARK), (hand[0] + 16.0, hand[1]), "burst", 0.0))
        out.append((_sym(["+", "1"], 7.0), (hand[0] + 16.0, hand[1]), "plus_one", 0.0))
    elif anim in ("slash", "ledge_getup_attack") and 2 <= i <= 6:
        a = math.degrees(math.atan2(hand[1] - ctx.shoulder[1], hand[0] - ctx.shoulder[0]))
        lead = int(round(a / 5.0)) * 5
        out.append((R.swoosh(K, 48.0, lead - 90, lead + 6, 7.0, BRASS, CHAIN_DARK), ctx.shoulder, "swoosh", 0.0))
    elif anim in ("attack_side", "prime_stride") and 3 <= i <= 6:
        # Every guest moves up one room.
        doors((hand[0] + 16.0, ctx.ground - 0.0), 1 + (i - 3), 3, shift=3.0 * (i - 3))
    elif anim in ("attack_up", "air_up") and 3 <= i <= 6:
        y = hand[1] - 18.0 - 3.0 * (i - 3)
        if y > 16.0:
            out.append((_sym(["infinity"], 10.0), (hand[0] + 3.0, y), "infinity", 0.0))
    elif anim == "attack_down" and i >= 4:
        out.append((_door(str(i - 3), i >= 6), (hand[0] + 10.0, ctx.ground), "door", 0.0))
        out.append((R.burst(K, 10.0, BRASS, CHAIN_DARK, 6), (hand[0] + 10.0, ctx.ground - 8.0), "burst", 0.0))
    elif anim == "air_neutral":
        for k in range(3):
            a = ctx.phase + k * math.tau / 3.0
            out.append((_sym(str(k + 1), 8.0), (hip[0] + 34.0 * math.cos(a), hip[1] - 18.0 + 11.0 * math.sin(a)), f"num_{k}", 0.0))
    elif anim in ("charge", "compressed_sense"):
        doors((head[0] - 14.0, head[1] - 22.0), 1 + i, 3)
    elif anim in ("cast", "polymath_chain") and i >= 2:
        go = (i - 2) / max(1, n - 3)
        doors((hand[0] + 12.0, hand[1] + 9.0), 1, 2 + int(2.0 * go), step=11.0)
    elif anim == "taunt" and u >= 0.2:
        out.append((_bell(), (hip[0] + 28.0, hip[1] + 6.0), "bell", 0.0))
        if 0.4 <= u <= 0.8 and i % 2:
            out.append((R.burst(K, 7.0, BRASS, CHAIN_DARK, 6), (hip[0] + 28.0, hip[1] - 4.0), "ring", 0.0))
    elif anim == "interact" and 3 <= i <= 5:
        out.append((R.tick(K, 4.0, BRASS, CHAIN_DARK), (hand[0] + 16.0, hand[1] - 5.0), "tick", 0.0))
    elif anim == "celebrate" and u >= 0.5:
        out.append((_sym(["infinity"], 9.0), (head[0] + 4.0, head[1] - 22.0), "infinity", 0.0))
    return out


X.effects = _effects

ROWS = X.rows
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet: the clips his conversations
    name."""
    del opts
    return X.portraits(out_dir, {
        "default": ('idle', (0, 1, 2, 3, 4, 5, 6, 7), 145, True),
        "portrait": ('idle', (1,), 0, False),
        "lecturing": ('talk', (0, 1, 2, 3, 4, 5, 6, 7), 104, True),
        "axiomatic": ('polymath_chain', (0, 1, 2, 3, 4, 5, 6, 7), 78, True),
    }, still="portrait", view_width=34.0)


# ---- In the round (``_person_round``) -----------------------------------------
#
# His pieces as shapes in 3D, from his two views: the three-quarter view gives
# where a thing is forward of the middle, the front view how wide it is. His
# rows above do not use this; it draws the views he does not have. Body space
# is frame pixels from the middle of his hips: ``l`` to his left, ``y`` down,
# ``z`` forward.

import numpy as np  # noqa: E402

from . import _person_round as O  # noqa: E402

#: The middle of his head, and of his trunk.
HEAD = (0.0, BUILD.neck[1] - 12.4, 1.6)
TRUNK = (0.0, -20.0, 0.4)

# His joints, lifted from his two views: his three-quarter view draws a joint
# ``x`` across, his front view says how far to the side it is (``X.front_span``
# and ``FRONT_REST``), and ``O.lift`` gives how far forward it is.
_U = BUILD.hip_up / 37.0
_SW, _HW = X.front_span
_FOOT = _HW + R.FRONT_REST["lf"][0] * _U
SHOULDERS = {"r": (-_SW, BUILD.near_shoulder[1], O.lift(BUILD.near_shoulder[0], -_SW)),
             "l": (_SW, BUILD.far_shoulder[1], O.lift(BUILD.far_shoulder[0], _SW))}
HIPS = {"r": (-_HW, 0.0, O.lift(BUILD.near_hip[0], -_HW)), "l": (_HW, 0.0, O.lift(BUILD.far_hip[0], _HW))}
#: The feet are staggered, the near (right) one back and the far one forward,
#: as his three-quarter view stands them, so that a side view shows both.
_STAGGER = 3.0
ANKLES = {"r": (-_FOOT, BUILD.hip_up - BUILD.ankle_up, O.lift(X.rest["nf"][0] * _U, -_FOOT) - _STAGGER),
          "l": (_FOOT, BUILD.hip_up - BUILD.ankle_up, O.lift(X.rest["ff"][0] * _U, _FOOT) + _STAGGER)}
#: Where his hands are, and which way each elbow goes. At rest
#: (``set_rest``): the near (right) thumb in his waistcoat pocket, 5 to his
#: right of the middle, and the far (left) hand behind his back. In his front
#: rows (``front_arms``, clasped): the two hands meet low in front.
_POCKET = (BUILD.near_shoulder[0] + IN_POCKET[0] * _U, BUILD.near_shoulder[1] + IN_POCKET[1] * _U)
_CLASP = (_SW - (_SW - 5.0) * _U, BUILD.far_shoulder[1] + 0.56 * (BUILD.upper + BUILD.fore) * _U)
POSES = {
    "rest": {"r": ((-5.0, _POCKET[1], O.lift(_POCKET[0], -5.0)), (-0.6, 0.3, -1.0)), "l": ((2.0, -4.0, -7.6), (0.5, 0.3, -1.0))},
    "front": {"r": ((-_CLASP[0], _CLASP[1], 7.4), (-1.0, 0.0, -0.2)), "l": ((_CLASP[0], _CLASP[1], 7.4), (1.0, 0.0, -0.2))},
}

#: The skull and the jaw, from the middle of the head (his front view: 7.8 and
#: 6.4 wide; his three-quarter view: the jaw 2.6 forward of the skull).
SKULL = ((0.0, -2.0, 0.0), (7.8, 9.2, 7.8))
JAW = ((0.0, 3.9, 3.8), (6.2, 7.4, 4.2))
#: His eyes: 3.4 from the middle (front view), half a pixel over it.
EYE_U, EYE_V = 26.0, -0.5


def _round_scalp(u, v, lit, far):
    """Bald on top (under the hat), white hair round the back of the head
    and over the ears; the far side of the face in shade."""
    a = np.abs(u)
    out = O.fill(SKIN, len(u))
    O.put(out, lit < -0.45, mix(SKIN, SKIN_SHADE, 0.7))
    O.put(out, ((a > 96.0) & (v > -7.5) & (v < 6.5)) | ((a > 55.0) & (v > -6.5) & (v < 2.5)), BEARD)
    return out


def _round_beard(u, v, lit, far):
    """The short white beard; the mouth on it, in front."""
    out = O.fill(BEARD, len(u))
    O.put(out, lit < -0.6, BEARD_DARK)
    O.put(out, (np.abs(v - 8.8) < 0.35) & (np.abs(O.arc(u, 5.6)) < 2.0), (140, 80, 84, 255))
    return out


def _round_jacket(u, v, lit, far):
    """The jacket open over the waistcoat: the lapels, the shirt and the bow
    tie at the top, three buttons, the watch chain; a seam down the back and
    a pocket on each side."""
    a = np.abs(u)
    x = O.arc(u, 9.6)
    out = O.fill(SUIT, len(u))
    O.put(out, (a < 34.0) & (v > TOP + 1.0), VEST)
    O.put(out, (np.abs(x - np.sign(x) * O.arc(34.0, 9.6)) < 0.35) & (v > -20.0), SUIT_DARK)
    lapel = (v < -20.0) & (a >= 34.0 - 14.0 * (v + 20.0) / (TOP + 20.0)) & (a < 34.0 + 2.0)
    O.put(out, lapel & (v > TOP - 1.0), SUIT_LIGHT)
    O.put(out, (v < -27.0) & (a < 20.0 * (-27.0 - v) / (-27.0 - TOP)), SHIRT)
    for y in (-18.0, -12.0, -6.0):
        O.put(out, x ** 2 + (v - y) ** 2 < 0.8 ** 2, SUIT_DARK)
    # The watch chain: from a pocket on his right, down across the front, up
    # to a pocket on his left.
    reach = np.where(x < 0.0, O.arc(25.0, 9.6), O.arc(28.0, 9.6))
    sag = -7.6 - np.where(x < 0.0, 2.4, 2.0) * (x / reach) ** 2
    on = np.abs(x) < reach
    O.put(out, on & (np.abs(v - sag) < 0.7), CHAIN_DARK)
    O.put(out, on & (np.abs(v - sag) < 0.35), CHAIN)
    # The tie under the wing collar, as his front view has it, down into
    # the waistcoat.
    O.put(out, (v < -23.6) & (np.abs(x) < 1.0 + 0.2 * (v - TOP) / (-23.6 - TOP)), TIE)
    O.put(out, (v < TOP + 2.2) & (np.abs(x) < 1.2), mix(TIE, INK, 0.3))
    O.put(out, (np.abs(O.arc(180.0 - a, 9.6)) < 0.35) & (v > -24.0), SUIT_DARK)
    O.put(out, (a > 45.0) & (a < 75.0) & (np.abs(v + 3.2) < 0.35), SUIT_DARK)
    O.put(out, lit < -0.45, SUIT_DARK)
    return out


def _round_hat(u, v, lit, far):
    out = O.fill(HAT, len(u))
    O.put(out, (v > -11.4) & (v < -8.6), BAND)
    O.put(out, lit < -0.4, HAT_DARK)
    return out


def _round_brim(u, v, lit, far):
    """The top of the brim is the hat's colour, its edge and its underside
    darker."""
    out = O.fill(HAT, len(u))
    O.put(out, v > 1.5, HAT_DARK)
    return out


def _round_head() -> O.Part:
    skull_c, skull_r = SKULL
    head = [
        O.ellipsoid(skull_c, skull_r, _round_scalp),
        # The hair stands off the back of his head a little.
        O.ellipsoid((0.0, 1.2, -5.4), (6.8, 6.0, 4.4), O.flat(BEARD, shade=BEARD_DARK, at=-0.6)),
        O.ellipsoid(JAW[0], JAW[1], O.flat(SKIN, shade=mix(SKIN, SKIN_SHADE, 0.7), at=-0.45)),
        O.ellipsoid((0.0, 2.0, 10.0), (1.1, 2.4, 3.4), O.flat(SKIN, shade=mix(SKIN, SKIN_SHADE, 0.7), at=-0.45)),
        O.ellipsoid((-8.2, 1.0, -0.6), (1.6, 3.0, 2.0), O.flat(SKIN, shade=SKIN_SHADE)),
        O.ellipsoid((8.2, 1.0, -0.6), (1.6, 3.0, 2.0), O.flat(SKIN, shade=SKIN_SHADE)),
        # The beard: as wide as his face under the cheeks (his front view:
        # 7 each side at the moustache), to a point at his collar.
        O.loft([O.Ring(2.4, 0.0, 3.8, 7.2, 4.7), O.Ring(4.6, 0.0, 4.2, 7.0, 4.7), O.Ring(8.0, 0.0, 4.8, 6.4, 4.0), O.Ring(12.0, 0.0, 5.0, 5.0, 3.4),
                O.Ring(14.6, 0.0, 4.8, 3.0, 2.4), O.Ring(16.8, 0.0, 4.5, 0.5, 0.5)], _round_beard),
        # The moustache, wide, over his lip.
        O.ellipsoid((0.0, 5.9, 8.8), (5.2, 1.5, 2.1), O.flat(BEARD, shade=BEARD_DARK, at=-0.4)),
    ]
    lines: List[O.Line] = []
    for side in (-1.0, 1.0):
        eye, n = O.on_ellipsoid(skull_c, skull_r, side * EYE_U, EYE_V, 0.1)
        # The lens over the eye (the eye is drawn over it, as his own art
        # has it), then the eye.
        lens = eye + np.array([0.0, 0.0, 1.0])
        face = np.array([0.25 * side, 0.0, 1.0])
        lines.append(O.circle(lens, face, 2.9, None, fill=LENS))
        lines.append(O.circle(eye + n * 0.4, n, 1.0, None, fill=INK, slack=1.6))
        lid = [O.on_ellipsoid(skull_c, skull_r, side * EYE_U + du, EYE_V - 1.6 + 0.02 * du * du, 0.1)[0] for du in (-14.0, -6.0, 0.0, 6.0, 14.0)]
        lines.append(O.curve(lid, SKIN_DEEP, 0.5))
        brow = [O.on_ellipsoid(skull_c, skull_r, side * u, -4.6 - 0.4 * math.sin(math.radians((u - 10.0) * 6.0)), 0.3)[0] for u in (10.0, 20.0, 30.0, 40.0)]
        lines.append(O.curve(brow, BEARD_DARK, 1.6))
        lines.append(O.curve(brow, BEARD, 1.0))
        # The rims of the glasses, and their arms back to the ears.
        lines.append(O.circle(lens, face, 2.9, FRAME, 0.8))
        lines.append(O.curve([lens + [side * 2.8, -0.2, -0.4], (side * 7.4, -0.8, 3.0), (side * 7.9, -0.6, -0.6)], FRAME, 0.6))
        ear = np.array([side * 9.6, 1.0, -0.6])
        lines.append(O.circle(ear, (side, 0.0, 0.0), 1.8, OUTLINE, 0.6, slack=0.6))
        lines.append(O.curve([ear + [0.0, -1.4, 0.6], ear + [0.0, 0.0, -0.2], ear + [0.0, 1.4, 0.4]], SKIN_DEEP, 0.45, slack=0.6))
        # Strands in the beard.
        lines.append(O.curve([(side * 2.0, 9.6, 8.0), (side * 1.8, 13.0, 6.8)], BEARD_DARK, 0.5))
    left = O.on_ellipsoid(skull_c, skull_r, -EYE_U, EYE_V)[0] + [0.0, 0.0, 1.0]
    right = O.on_ellipsoid(skull_c, skull_r, EYE_U, EYE_V)[0] + [0.0, 0.0, 1.0]
    lines.append(O.curve([left + [2.8, -0.2, 0.2], (0.0, -0.9, 9.2), right + [-2.8, -0.2, 0.2]], FRAME, 0.6))
    lines.append(O.curve([(-1.2, 4.0, 10.6), (0.0, 4.6, 11.6), (1.2, 4.0, 10.6)], SKIN_DEEP, 0.6))
    lines.append(O.curve([(-4.0, 6.6, 9.6), (0.0, 7.0, 10.0), (4.0, 6.6, 9.6)], BEARD_DARK, 0.6))
    return O.Part("head", [s.moved(HEAD) for s in head], [O.Line(ln.points + HEAD, ln.colour, ln.width, ln.fill, ln.slack) for ln in lines],
                  base=SKIN, shade_colour=SKIN_DEEP, anchor=HEAD)


def _round_hat_part() -> O.Part:
    crown = O.loft([O.Ring(-7.0, 0.0, 0.4, 8.2, 8.0), O.Ring(-11.8, 0.0, 0.4, 8.0, 7.8), O.Ring(-15.4, 0.0, 0.3, 7.4, 7.2),
                    O.Ring(-16.4, 0.0, 0.2, 6.6, 6.0, lift=1.2), O.Ring(-15.4, 0.0, 0.2, 0.0, 0.0)], _round_hat)
    brim = O.loft([O.Ring(-7.4, 0.0, 0.4, 8.0, 7.8, v=0.0), O.Ring(-7.2, 0.0, 0.8, 12.8, 13.0, droop=1.0, v=1.0),
                   O.Ring(-6.4, 0.0, 0.8, 12.8, 13.0, droop=1.0, v=2.0), O.Ring(-6.6, 0.0, 0.4, 8.0, 7.8, v=3.0)], _round_brim)
    crease = O.curve([(0.0, -16.3, 5.6), (0.0, -15.6, 2.0), (0.0, -15.6, -1.6), (0.0, -16.3, -5.4)], HAT_DARK, 0.7)
    return O.Part("hat", [crown.moved(HEAD), brim.moved(HEAD)], [crease.moved(HEAD)], base=HAT,
                  outline=1.2, shade=0.35, shade_colour=HAT_DARK, anchor=(HEAD[0], HEAD[1] - 10.0, HEAD[2]))


def _round_trunk() -> O.Part:
    jacket = O.loft([O.Ring(TOP - 0.5, 0.0, 0.3, 4.4, 3.6), O.Ring(-35.0, 0.0, 0.4, 9.0, 6.0), O.Ring(-31.0, 0.0, 0.5, 9.6, 6.6),
                     O.Ring(-24.0, 0.0, 0.6, 9.8, 6.8), O.Ring(-14.0, 0.0, 0.5, 9.6, 6.4), O.Ring(-6.0, 0.0, 0.3, 9.6, 6.2),
                     O.Ring(0.0, 0.0, 0.0, 9.8, 6.4), O.Ring(9.5, 0.0, 0.0, 10.3, 6.8)], _round_jacket, cols=64)
    suit = O.flat(SUIT, shade=SUIT_DARK, at=-0.45)
    collar = O.loft([O.Ring(TOP - 2.6, 0.0, 0.6, 2.9, 2.7), O.Ring(TOP - 0.2, 0.0, 0.5, 3.4, 3.2), O.Ring(TOP + 1.2, 0.0, 0.8, 3.6, 3.6, droop=0.8)],
                    O.flat(SHIRT, shade=(214, 214, 220, 255), at=-0.4))
    return O.Part("trunk", [jacket, O.ellipsoid((-7.0, -31.2, 0.4), (4.8, 5.2, 4.8), suit), O.ellipsoid((7.0, -31.2, 0.4), (4.8, 5.2, 4.8), suit), collar],
                  base=SUIT, shade_colour=SUIT_DARK, anchor=TRUNK)


def _round_neck() -> O.Part:
    return O.Part("neck", [O.limb((0.0, -35.5, 0.4), (HEAD[0], HEAD[1] + 6.0, HEAD[2] - 0.4), 2.2, 2.2, O.flat(SKIN_SHADE))], base=SKIN_SHADE,
                  outline=1.1, rim=0.0, shade=0.0, anchor=(0.0, -38.0, 0.4))


def _round_arm(side: str, pose: str) -> List[O.Part]:
    target, pole = POSES[pose][side]
    elbow, wrist = O.two_bone(SHOULDERS[side], target, BUILD.upper, BUILD.fore, pole)
    cloth = O.flat(SUIT, SUIT_DARK, shade=SUIT_DARK, at=-0.5)
    sleeve = O.Part(f"{side}_arm", [O.limb(SHOULDERS[side], elbow, 3.4, 2.9, cloth), O.limb(elbow, wrist, 2.9, 2.5, cloth)], base=SUIT, outline=1.2,
                    rim=0.0, shade=0.0, anchor=tuple(elbow), dims=True)
    toward = (wrist - elbow) / np.linalg.norm(wrist - elbow)
    fist = wrist + toward * 2.6
    cuff = O.limb(tuple(wrist - toward * 0.8), tuple(wrist + toward * 0.6), 2.7, 2.7, O.flat(SHIRT, (206, 206, 212, 255)))
    hand = O.Part(f"{side}_hand", [O.ellipsoid(tuple(fist), (3.0, 3.1, 3.0), O.flat(SKIN, SKIN_SHADE, shade=SKIN_SHADE)), cuff], base=SKIN, outline=1.1,
                  shade=0.3, shade_colour=SKIN_DEEP, anchor=tuple(fist), dims=True)
    return [sleeve, hand]


def _round_leg(side: str) -> List[O.Part]:
    hip, ankle = np.asarray(HIPS[side]), np.asarray(ANKLES[side])
    knee, ankle = O.two_bone(tuple(hip), tuple(ankle), BUILD.thigh, BUILD.shin, (0.0, 0.0, 1.0))
    cloth = O.flat(SUIT, SUIT_DARK, shade=SUIT_DARK, at=-0.5)
    leg = O.Part(f"{side}_leg", [O.limb(tuple(hip), tuple(knee), 3.6, 3.0, cloth), O.limb(tuple(knee), tuple(ankle), 3.0, 2.7, cloth)], base=SUIT,
                 outline=1.2, rim=0.0, shade=0.0, anchor=tuple(knee), dims=True)
    return [leg, O.Sprite(f"{side}_shoe", tuple(ankle), _round_shoe_sprite, dims=True, lead=3.0)]


_BACK_SHOE = R.make_back_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up)


def _round_shoe_sprite(view, far):
    """His own shoes: seen from the toe, the shoe of his front view; from the
    heel, that shoe from behind; from any other side, the shoe of his
    three-quarter view, its toe to the side the foot points."""
    turn = O.facing(view)
    toward = math.cos(math.radians(turn))
    if toward > 0.85:
        return X.front_shoe(), 0.0, False
    if toward < -0.85:
        return _BACK_SHOE(), 0.0, False
    return X.shoe(not far), 0.0, turn < 0.0


#: The turns his own head is drawn at: his three-quarter view (and, mirrored,
#: its left), and his front view.
_OWN_HEAD = O.near_turn(45.0, -45.0, 0.0)


def _round_own_head(view, far):
    """His own head, hat and face, where he has them: the three-quarter
    view's (mirrored for the left) and the front view's."""
    turn = O.facing(view)
    if abs(turn) <= 10.0:
        return O.composed(K, X.front_head_layers(dict(R.FRONT_REST))), 0.0, False
    return O.composed(K, X.head_layers(X.full(X.rest))), 0.0, turn < 0.0


def round_figure(pose: str = "rest") -> O.Figure:
    """Davy Hylbert in the round, his hands as ``POSES`` has them. His own
    head is drawn where he has one; the head in 3D draws the other views."""
    other = lambda view: not _OWN_HEAD(view)  # noqa: E731
    head, hat = _round_head(), _round_hat_part()
    head.when, hat.when = other, other
    parts = [_round_trunk(), _round_neck(), head, hat, O.Sprite("own_head", HEAD, _round_own_head, when=_OWN_HEAD, lead=9.0)]
    for side in ("r", "l"):
        parts += _round_arm(side, pose) + _round_leg(side)
    return O.Figure(parts, X.frame, X.cx, X.ground, BUILD.hip_up, trunk=TRUNK)


def render_turnaround(path):
    """His eight views from 3D, with his own art (the three-quarter view and
    the front view, the first frame of ``idle`` and of ``front``) under the
    two views it draws."""
    rows = {name: n for name, n, _ms in X.rows}
    own = {"front_3q": X.render_frame("idle", 0, rows["idle"]), "front": X.render_frame("front", 0, rows["front"])}
    return O.turnaround(K, round_figure(), path, title=f"{DISPLAY_NAME} in the round", own=own)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
