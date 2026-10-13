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


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
