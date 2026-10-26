"""Sprite generator for Data Lovelace: the engine she wrote for, and it can
think about what it is for.

An affectionate caricature of Ada Lovelace, as a robot.

The look (2026-10-13): a robot of brass, seen three quarters from the front,
facing right. A round head with a plate of pale enamel for a face: two round
lenses with green light in them, and a small grille to speak through. On it a
cap cast in dark copper in the shape of Ada's hair (parted in the middle, a
knot behind, and at each ear a coil that is a spring), and one thin aerial. A
neck of rings. A chest that is a riveted barrel, and on it what she is: a row
of number wheels, a dial, and the slot her cards go in. Arms that are hoses
of rings, and hands that are two-fingered grips. Under a ball at her waist a
tall bell of bronze, and a base on small wheels: she has no legs, and she
rolls. A band of punched card goes round the bell near its foot.

She is a robot, and a person of rank: she is no one's maid, and nothing she
wears is a servant's (Jon, 2026-10-13, of the draft before this one, a lady
of enamel in a dress: "Data Lovelace needs to read more as a robot. Think
Rosie the robot from the Jetson's minus the maid motif. I want her to be more
dignified than a maid to reflect her intellectual prowess."). She holds
herself very straight, her grips one on the other. She holds nothing; there
is no drop shadow.

What she shows: the cards of a program, dealt in an arc from her hand; the
pattern they make (a weave, as a loom weaves flowers); and a gear that she
sets right in her own arm.

She is a person of ``_person_rig``: the bones of her trunk, her arms and her
head, the poses and the frame are shared. She has no legs: the bell and its
wheels are a part of her trunk. Her portraits are frames of this sheet.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import RGBA, mix, pin
from ._ai_era_kit import WHITE as _SOLID
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "data_lovelace"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Data Lovelace"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_data_lovelace", "display_name": "Data Lovelace"},
    "visual": {"default_pose": "idle"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Slim",
        "mass_class": "Light",
        "traits": ["robot", "automaton", "computing", "victorian", "playable_candidate"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": None, "fly": None, "swim": None, "crawl": False, "use_lifts": True, "door_access": ["public"]},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "tags": ["robot", "automaton", "computing", "victorian", "playable_candidate"],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 80.0, "y": 30.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 80.0, "y": 86.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 31.0, "y": 122.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 129.0, "y": 122.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 80.0, "y": 6.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "self_repair", "events": []},
        "action.special.primary": {"animation": "compute", "events": []},
        "action.special.secondary": {"animation": "analytical_burst", "events": []},
        "death": {"animation": "death", "events": []},
    },
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Data Lovelace is Ada Lovelace reimagined as the brass-and-punch-card automaton she could "
            "only describe. The name also literalizes 'data': she is both the visionary author of "
            "programs for the Analytical Engine and a machine capable of enacting them."
        ),
        "gameplay_description": (
            "Use as an analytical companion, inventor, programmer, or playable automaton. Her "
            "abilities should compose patterns rather than merely calculate totals, and her dialogue "
            "should be imaginative, precise, and slightly ahead of the machinery around her."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'They asked what the engine could add. I asked what it could compose.',
        'My notes were longer than the paper they annotated.',
        'The engine weaves algebra.',
    ],
)



BRASS: RGBA = (216, 170, 86, 255)
BRASS_DARK: RGBA = (150, 104, 54, 255)
BRASS_LIGHT: RGBA = (248, 218, 146, 255)
BRASS_DEEP: RGBA = (98, 64, 40, 255)
BRONZE: RGBA = (168, 118, 70, 255)
BRONZE_DARK: RGBA = (112, 74, 50, 255)
TEAL: RGBA = (58, 154, 152, 255)
TEAL_DARK: RGBA = (32, 98, 108, 255)
TEAL_LIGHT: RGBA = (124, 208, 196, 255)
COPPER: RGBA = (132, 70, 56, 255)
COPPER_LIGHT: RGBA = (190, 112, 84, 255)
COPPER_DARK: RGBA = (84, 42, 40, 255)
ENAMEL: RGBA = (240, 230, 210, 255)
ENAMEL_SHADE: RGBA = (204, 190, 172, 255)
ENAMEL_DEEP: RGBA = (150, 132, 124, 255)
CARD: RGBA = (244, 236, 208, 255)
CARD_DARK: RGBA = (176, 160, 128, 255)
LIGHT: RGBA = (140, 244, 224, 255)
INK: RGBA = (30, 30, 40, 255)

#: 165 cm, on her wheels.
BUILD = Build(hip_up=47.0, thigh=22.9, shin=21.3, neck=(0.6, -35.0), upper=18.4, fore=17.4, near_shoulder=(-4.8, -30.6), far_shoulder=(4.8, -30.4),
              near_hip=(-3.8, 0.0), far_hip=(3.8, 0.0), head_up=(0.8, -12.4), height=106.0, half_width=(14.0, 15.0))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0
#: How far under the ball of her waist the floor is: her wheels are on it.
FLOOR = BUILD.hip_up


def _rivets(d, points) -> None:
    for x, y in points:
        K.oval(d, K.at(x, y), 0.7, 0.7, BRASS_DEEP)
        K.oval(d, K.at(x - 0.2, y - 0.2), 0.35, 0.35, BRASS_LIGHT)


def _torso(hem_back: int, hem_front: int, drop=None):
    """Her trunk, the ball of her waist at ``home``: the barrel of her chest
    over it, and under it the bell, its base and its wheels. ``drop``: the
    floor is this far under her waist (the bell is shorter in a low pose)."""
    floor = FLOOR if drop is None else max(14.0, min(FLOOR, float(drop)))
    hb, hf = float(hem_back), float(hem_front)
    foot = floor - 7.0

    def shape(d) -> None:
        h = K.home
        K.rrect(d, h[0] - 8.6, h[1] + TOP + 1.0, h[0] + 9.2, h[1] - 12.0, 4.0, _SOLID)
        K.oval(d, K.at(-4.6, -30.4), 4.6, 4.8, _SOLID)
        K.oval(d, K.at(4.4, -30.4), 3.6, 4.0, _SOLID)
        K.oval(d, K.at(0.4, -9.6), 4.0, 3.6, _SOLID)
        K.poly(d, [K.at(-5.6, -8.0), K.at(6.6, -8.0), K.at(14.0 + hf, foot), K.at(-13.0 - hb, foot)], _SOLID)
        K.rrect(d, h[0] - 13.6 - hb, h[1] + foot - 0.6, h[0] + 14.6 + hf, h[1] + floor - 2.6, 1.2, _SOLID)
        for x in (-8.6, 9.4):
            K.oval(d, K.at(x, floor - 3.0), 3.0, 3.0, _SOLID)

    def paint(d) -> None:
        h = K.home
        # The far side of the barrel is in its own shade; rivets on its rims.
        K.poly(d, [K.at(6.0, TOP), K.at(12.0, TOP), K.at(12.0, -12.0), K.at(6.4, -12.0)], BRASS_DARK)
        K.line(d, [K.at(-8.6, TOP + 5.0), K.at(9.2, TOP + 5.2)], BRASS_DARK, 0.6)
        K.line(d, [K.at(-8.6, -15.4), K.at(9.2, -15.2)], BRASS_DARK, 0.6)
        _rivets(d, [(x, TOP + 3.0) for x in (-5.6, -1.6, 2.4, 6.4)] + [(x, -13.6) for x in (-5.6, -1.6, 2.4, 6.4)])
        # What she is: number wheels, a dial, and the slot her cards go in.
        K.rrect(d, h[0] - 0.6, h[1] - 30.4, h[0] + 8.0, h[1] - 25.6, 0.6, INK)
        for k in range(3):
            K.rrect(d, h[0] + 0.1 + k * 2.7, h[1] - 29.7, h[0] + 2.1 + k * 2.7, h[1] - 26.3, 0.2, CARD)
            K.line(d, [K.at(1.1 + k * 2.7, -29.0), K.at(1.1 + k * 2.7, -27.0 - (k % 2))], INK, 0.5)
        K.oval(d, K.at(-4.0, -22.6), 2.7, 2.7, ENAMEL, BRASS_DEEP, 0.5)
        K.line(d, [K.at(-4.0, -22.6), K.at(-2.6, -24.2)], COPPER_DARK, 0.5)
        K.rrect(d, h[0] + 0.2, h[1] - 21.6, h[0] + 8.2, h[1] - 20.2, 0.3, INK)
        K.poly(d, [K.at(1.4, -20.8), K.at(7.0, -20.8), K.at(7.0, -18.2), K.at(1.4, -18.2)], CARD)
        for k in range(4):
            K.oval(d, K.at(2.4 + k * 1.2, -19.4), 0.3, 0.3, INK)
        # The ball of her waist.
        K.oval(d, K.at(0.4, -9.6), 4.0, 3.6, BRASS_DEEP)
        K.oval(d, K.at(-0.6, -10.4), 1.4, 1.1, BRASS_DARK)
        # The bell: bronze, with a band of teal, seams, and the band of card.
        K.poly(d, [K.at(-5.6, -8.0), K.at(6.6, -8.0), K.at(14.0 + hf, foot), K.at(-13.0 - hb, foot)], BRONZE)
        K.poly(d, [K.at(3.0, -8.0), K.at(6.6, -8.0), K.at(14.0 + hf, foot), K.at(7.0 + hf * 0.5, foot)], BRONZE_DARK)
        K.poly(d, [K.at(-6.2, -5.6), K.at(7.2, -5.6), K.at(7.9, -2.8), K.at(-6.9, -2.8)], TEAL)
        K.line(d, [K.at(-6.2, -5.6), K.at(7.2, -5.6)], TEAL_DARK, 0.5)
        K.line(d, [K.at(-6.9, -2.8), K.at(7.9, -2.8)], TEAL_DARK, 0.5)
        for x in (-3.0, 0.6, 4.2):
            K.line(d, [K.at(x * 0.7 + 0.3, -2.4), K.at(x * 2.3 + 0.4, foot - 5.4)], BRASS, 0.7)
        _rivets(d, [(-4.6, -0.6), (-0.4, -0.4), (3.8, -0.6)])
        K.poly(d, [K.at(-30.0, foot - 5.2), K.at(30.0, foot - 5.2), K.at(30.0, foot - 0.8), K.at(-30.0, foot - 0.8)], CARD)
        K.line(d, [K.at(-30.0, foot - 5.2), K.at(30.0, foot - 5.2)], CARD_DARK, 0.5)
        for k in range(-7, 9):
            if (k * 7) % 5 != 0:
                K.rrect(d, h[0] + k * 2.6 - 0.6, h[1] + foot - 4.2 + 1.2 * (k % 2), h[0] + k * 2.6 + 0.6, h[1] + foot - 3.0 + 1.2 * (k % 2), 0.2, INK)
        # Her base, and her wheels.
        K.rrect(d, h[0] - 30.0, h[1] + foot - 0.6, h[0] + 30.0, h[1] + floor - 2.6, 0.0, BRASS_DEEP)
        for x in (-8.6, 9.4):
            K.oval(d, K.at(x, floor - 3.0), 3.0, 3.0, INK)
            K.oval(d, K.at(x, floor - 3.0), 1.1, 1.1, BRASS)

    return K.solid(("lovelace_trunk", hem_back, hem_front, round(floor, 1)), shape, BRASS, paint, outline=1.3, rim=0.3, shade=0.0)


_torso.takes_drop = True  # type: ignore[attr-defined]
X.torso = _torso

NEAR_EYE = (2.6, -1.0)
FAR_EYE = (7.4, -1.2)


def _cap_shape(d) -> None:
    # The cap cast in the shape of her hair: a knot behind and a coil at her
    # ear. And her aerial.
    K.oval(d, K.at(-0.8, -5.2), 9.0, 6.8, _SOLID)
    K.oval(d, K.at(-9.0, -2.6), 3.4, 3.2, _SOLID)
    K.rrect(d, K.home[0] - 6.4, K.home[1] + 0.6, K.home[0] - 2.6, K.home[1] + 9.6, 1.4, _SOLID)
    K.stroke(d, [K.at(-1.4, -11.0), K.at(-2.4, -18.6)], _SOLID, 1.3)
    K.oval(d, K.at(-2.5, -19.4), 1.6, 1.6, _SOLID)


def _cap(d) -> None:
    K.poly(d, [K.at(20.0, -9.2), K.at(8.6, -9.2), K.at(5.6, -7.0), K.at(2.0, -4.6), K.at(-0.8, -2.0), K.at(-2.4, 0.4), K.at(-2.4, 12.0), K.at(-20.0, 12.0),
               K.at(-20.0, -26.0), K.at(20.0, -26.0)], COPPER)
    # The parting is a seam with rivets, and the metal takes the light.
    K.line(d, [K.at(3.0, -12.2), K.at(1.6, -8.0)], COPPER_DARK, 0.6)
    for x, y in ((2.8, -11.2), (2.2, -9.2)):
        K.oval(d, K.at(x + 1.2, y), 0.5, 0.5, COPPER_LIGHT)
    for strand in ([(-5.0, -10.4), (-1.0, -11.4), (1.4, -10.6)], [(4.8, -11.0), (7.0, -9.8)], [(-6.0, -6.0), (-3.0, -3.6)]):
        K.line(d, [K.at(x, y) for x, y in strand], COPPER_LIGHT, 0.6)
    K.oval(d, K.at(-9.0, -2.6), 1.9, 1.7, None, COPPER_DARK, 0.5)  # type: ignore[arg-type]
    # The coil at her ear is a spring.
    spring = [K.at(-6.0 + 3.2 * (k % 2), 1.4 + k * 1.3) for k in range(7)]
    K.line(d, spring, COPPER_DARK, 1.3)
    K.line(d, spring, COPPER_LIGHT, 0.5)
    # Her aerial, and the light at its end.
    K.stroke(d, [K.at(-1.4, -11.0), K.at(-2.4, -18.6)], BRASS_DARK, 0.8)
    K.oval(d, K.at(-2.5, -19.4), 1.3, 1.3, LIGHT)


def _face(d) -> None:
    # A plate of enamel, with a brass edge, and in it her two lenses.
    plate = [K.at(1.0, -6.6), K.at(7.6, -7.0), K.at(10.2, -3.0), K.at(10.4, 3.4), K.at(8.0, 7.6), K.at(3.0, 7.8), K.at(0.4, 4.0)]
    K.poly(d, plate, ENAMEL)
    K.poly(d, [K.at(7.6, -7.0), K.at(10.2, -3.0), K.at(10.4, 3.4), K.at(8.0, 7.6), K.at(7.0, 7.6), K.at(8.4, 3.0), K.at(8.2, -3.0)], ENAMEL_SHADE)
    K.line(d, plate + plate[:1], BRASS_DEEP, 0.6)
    for (cx, cy), r in ((NEAR_EYE, 2.7), (FAR_EYE, 2.0)):
        K.oval(d, K.at(cx, cy), r + 0.7, r + 0.7, BRASS, BRASS_DEEP, 0.5)
        K.oval(d, K.at(cx, cy), r, r, INK)
        K.oval(d, K.at(cx, cy), r * 0.62, r * 0.62, TEAL)
        K.oval(d, K.at(cx + r * 0.2, cy), r * 0.3, r * 0.3, LIGHT)
        K.oval(d, K.at(cx - r * 0.4, cy - r * 0.45), r * 0.2, r * 0.2, ENAMEL)
    _rivets(d, [(-0.8, -1.0), (-0.6, 3.0)])


_head = R.make_head(K, ("lovelace",), BRASS, BRASS_DARK, BRASS_DEEP, skull=(0.0, -2.2, 8.2, 8.4), jaw=(2.2, 3.6, 6.2, 5.8), nose=None, ear=None, shape=_cap_shape,
                    under=_cap, over=_face)


def _lids(mode: str):
    """Her lenses are in her head; this is their shutters, when they are shut."""
    if mode != "closed":
        return None

    def paint(d) -> None:
        for (cx, cy), r in ((NEAR_EYE, 2.7), (FAR_EYE, 2.0)):
            K.oval(d, K.at(cx, cy), r, r, BRASS_DARK)
            K.line(d, [K.at(cx - r, cy), K.at(cx + r, cy)], BRASS_DEEP, 0.6)

    return K.piece(("lovelace_lids",), paint)


def _grille(mode: str):
    """The grille she speaks through: its bars are lit when she speaks."""
    lit = {"open": 2, "big": 3, "o": 2, "smile": 1}.get(mode, 0)

    def paint(d) -> None:
        K.rrect(d, K.home[0] + 3.4, K.home[1] + 4.2, K.home[0] + 8.6, K.home[1] + 6.6, 0.6, INK, BRASS_DEEP, 0.4)
        for k in range(3):
            K.line(d, [K.at(4.4 + k * 1.6, 4.8), K.at(4.4 + k * 1.6, 6.0)], LIGHT if k < lit else ENAMEL_DEEP, 0.6)

    return K.piece(("lovelace_grille", lit), paint)


X.head_layers = lambda pose: [(_head(), "head"), (_lids(str(pose["eyes"])), "lids"), (_grille(str(pose["mouth"])), "grille")]
X.neck = R.make_neck(K, BRASS_DEEP, 3.4)


def _hose(near: bool, cuff: RGBA, at_end: bool):
    """An arm of hers is a hose of rings, with a cuff at one end of it."""
    a, b_ = (BRASS, BRASS_DARK) if near else (BRASS_DARK, BRASS_DEEP)
    rings = [(k * 0.2, k * 0.2 + 0.2, 5.0, 5.0, a if k % 2 == 0 else b_) for k in range(5)]
    return rings + [((0.8, 1.0, 5.8, 5.8, cuff) if at_end else (0.0, 0.14, 6.2, 6.2, cuff))]


X.upper_arm = lambda near: _hose(near, BRASS_LIGHT if near else BRASS, False)
X.forearm = lambda near: _hose(near, TEAL if near else TEAL_DARK, True)
# She has no legs.
X.thigh = lambda near: []
X.shin = lambda near: []
X.shoe = lambda near: None


def _grip(mode: str, near: bool):
    """Her hand, along +x from its wrist: two fingers of brass that close."""
    gap = {"open": 3.2, "flat": 1.6, "point": 0.9}.get(mode, 0.5)
    reach = 7.6 if mode in ("flat", "point") else 6.4

    def shape(d) -> None:
        K.oval(d, K.at(1.0, 0.0), 2.6, 2.8, _SOLID)
        K.stroke(d, [K.at(1.6, -1.4), K.at(reach * 0.6, -gap - 0.8), K.at(reach, -gap * 0.5)], _SOLID, 2.0)
        if mode != "point":
            K.stroke(d, [K.at(1.6, 1.4), K.at(reach * 0.6, gap + 0.8), K.at(reach, gap * 0.5)], _SOLID, 2.0)
        else:
            K.stroke(d, [K.at(1.6, 1.4), K.at(4.0, 2.0), K.at(3.0, 0.8)], _SOLID, 2.0)

    def detail(d) -> None:
        K.oval(d, K.at(1.0, 0.0), 1.1, 1.2, BRASS_DEEP)

    return K.solid(("grip", mode, near), shape, BRASS_LIGHT if near else BRASS, detail, outline=1.0, rim=0.0, shade=0.0)


X.hand = _grip

# ---- How she holds herself -----------------------------------------------------

#: Her grips one on the other in front of her, as a person of rank stands.
X.set_rest(lean=0.0, na=(5.0, 19.0), fa=(4.0, 21.0), nh="fist", fh="fist", nf=(-3.0, 0.0, 0.0), ff=(3.6, 0.0, 0.0))


@X.row
def idle(i: int, n: int):
    # She is still, as a machine is; her head turns a little, and the lights
    # of her eyes go out and come on.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.2 * s), head=(0.3, 0.0, -2.0 + 3.0 * (1.0 if c > 0.3 else 0.0)), eyes="closed" if i == n - 2 else "open", mouth="smile")


@X.row
def walk(i: int, n: int):
    # She rolls: she leans a little into it, and nothing of her goes up and down.
    _, s, _c = loop(i, n)
    return P(lean=3.0, head=(0.3, 0.0, -2.0 + 0.6 * s))


@X.row
def talk(i: int, n: int):
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.2 * s), head=(0.4, 0.0, 2.0 * s), na=(14.0 + 2.0 * c, 3.0 - 4.0 * max(0.0, s)), nh="open", mouth=("open", "smile", "big", "smile")[i % 4],
             brows=1.0 if s > 0.3 else 0.0)


#: One hand out, flat and palm up: she deals the cards from it.
DEAL = P(lean=2.0, head=(0.5, 0.0, 2.0), na=(19.0, 2.0), nh="flat", eyes="open", brows=1.0, mouth="smile")


@X.row
def compute(i: int, n: int):
    _, s, _c = loop(i, n)
    return X.keys(shot(i, n), [(0.0, P()), (0.2, DEAL), (0.85, dict(DEAL, na=(19.0, 1.0 + s))), (1.0, P())])


#: Both arms up and out: the pattern is woven.
WEAVE = P(hip=(0.0, -0.6), lean=-3.0, head=(0.0, 0.0, -8.0), na=(-12.0, -14.0), nab=-1.0, fa=(19.0, -14.0), nh="open", fh="open", eyes="wide", brows=1.0, mouth="big",
          hem=(3.0, 3.0))


@X.row
def analytical_burst(i: int, n: int):
    wind = P(hip=(0.0, 1.5), lean=4.0, head=(0.4, 0.4, 6.0), na=(6.0, 10.0), fa=(8.0, 11.0), nh="fist", fh="fist", eyes="closed", brows=-1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.2, wind), (0.4, WEAVE), (0.85, WEAVE), (1.0, P())])


@X.row
def self_repair(i: int, n: int):
    # She holds her far arm out and sets a gear in it right with the other hand.
    mend = P(lean=3.0, head=(0.6, 0.6, 12.0), fa=(18.0, 6.0), fh="flat", na=(15.0, 4.0), nh="point", eyes="open", brows=-1.0, mouth="flat")
    _, s, _c = loop(i, n)
    return X.keys(shot(i, n), [(0.0, P()), (0.2, mend), (0.75, dict(mend, na=(15.0 + 1.5 * s, 4.0))), (0.9, dict(mend, mouth="smile", brows=1.0)), (1.0, P())])


X.rows = [("idle", 8, 130), ("walk", 8, 102), ("talk", 8, 110), ("compute", 8, 92), ("analytical_burst", 8, 88), ("self_repair", 8, 96), ("death", 8, 116)]

# ---- From the front --------------------------------------------------------------


def _front_trunk(d) -> None:
    """Her trunk from the front: the barrel and what is on it, the ball of
    her waist, the bell, its band of card, her base and her wheels."""
    h = K.home
    foot = FLOOR - 7.0
    K.line(d, [K.at(-9.4, TOP + 5.0), K.at(9.4, TOP + 5.0)], BRASS_DARK, 0.6)
    K.line(d, [K.at(-9.4, -15.4), K.at(9.4, -15.4)], BRASS_DARK, 0.6)
    _rivets(d, [(x, TOP + 3.0) for x in (-6.6, -2.2, 2.2, 6.6)] + [(x, -13.6) for x in (-6.6, -2.2, 2.2, 6.6)])
    K.rrect(d, h[0] - 4.4, h[1] - 30.4, h[0] + 4.4, h[1] - 25.6, 0.6, INK)
    for k in range(3):
        K.rrect(d, h[0] - 3.7 + k * 2.7, h[1] - 29.7, h[0] - 1.7 + k * 2.7, h[1] - 26.3, 0.2, CARD)
        K.line(d, [K.at(-2.7 + k * 2.7, -29.0), K.at(-2.7 + k * 2.7, -27.0 - (k % 2))], INK, 0.5)
    K.oval(d, K.at(-5.4, -21.0), 2.5, 2.5, ENAMEL, BRASS_DEEP, 0.5)
    K.line(d, [K.at(-5.4, -21.0), K.at(-4.0, -22.6)], COPPER_DARK, 0.5)
    K.rrect(d, h[0] - 1.6, h[1] - 21.8, h[0] + 7.2, h[1] - 20.4, 0.3, INK)
    K.poly(d, [K.at(-0.4, -21.0), K.at(6.0, -21.0), K.at(6.0, -18.4), K.at(-0.4, -18.4)], CARD)
    K.oval(d, K.at(0.0, -9.6), 4.0, 3.6, BRASS_DEEP)
    K.poly(d, [K.at(-6.4, -8.0), K.at(6.4, -8.0), K.at(13.4, foot), K.at(-13.4, foot)], BRONZE)
    K.poly(d, [K.at(-7.0, -5.6), K.at(7.0, -5.6), K.at(7.8, -2.8), K.at(-7.8, -2.8)], TEAL)
    for x in (-3.4, 0.0, 3.4):
        K.line(d, [K.at(x * 0.8, -2.4), K.at(x * 2.6, foot - 5.4)], BRASS, 0.7)
    K.poly(d, [K.at(-30.0, foot - 5.2), K.at(30.0, foot - 5.2), K.at(30.0, foot - 0.8), K.at(-30.0, foot - 0.8)], CARD)
    for k in range(-5, 6):
        if (k * 7) % 5 != 0:
            K.rrect(d, h[0] + k * 2.4 - 0.6, h[1] + foot - 4.2 + 1.2 * (k % 2), h[0] + k * 2.4 + 0.6, h[1] + foot - 3.0 + 1.2 * (k % 2), 0.2, INK)
    K.rrect(d, h[0] - 30.0, h[1] + foot - 0.6, h[0] + 30.0, h[1] + FLOOR - 2.6, 0.0, BRASS_DEEP)
    for x in (-9.0, 9.0):
        K.rrect(d, h[0] + x - 2.0, h[1] + FLOOR - 5.6, h[0] + x + 2.0, h[1] + FLOOR, 0.8, INK)


def _front_cap_shape(d) -> None:
    K.oval(d, K.at(0.0, -5.0), 9.6, 7.0, _SOLID)
    for sx in (-1.0, 1.0):
        K.rrect(d, K.home[0] + 6.6 * sx - 2.0, K.home[1] + 0.4, K.home[0] + 6.6 * sx + 2.0, K.home[1] + 9.6, 1.4, _SOLID)
    K.stroke(d, [K.at(0.0, -11.0), K.at(0.0, -18.6)], _SOLID, 1.3)
    K.oval(d, K.at(0.0, -19.4), 1.6, 1.6, _SOLID)


def _front_cap(d) -> None:
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 12.0), K.at(5.4, 12.0), K.at(5.4, -3.0), K.at(3.0, -7.0), K.at(0.0, -8.4), K.at(-3.0, -7.0), K.at(-5.4, -3.0),
               K.at(-5.4, 12.0), K.at(-20.0, 12.0)], COPPER)
    K.line(d, [K.at(0.0, -12.2), K.at(0.0, -8.4)], COPPER_DARK, 0.6)
    for sx in (-1.0, 1.0):
        K.line(d, [K.at(2.0 * sx, -11.6), K.at(6.0 * sx, -8.4)], COPPER_LIGHT, 0.6)
        spring = [K.at((6.6 + 1.6 * (1 if k % 2 else -1)) * sx, 1.4 + k * 1.3) for k in range(7)]
        K.line(d, spring, COPPER_DARK, 1.3)
        K.line(d, spring, COPPER_LIGHT, 0.5)
    K.stroke(d, [K.at(0.0, -11.0), K.at(0.0, -18.6)], BRASS_DARK, 0.8)
    K.oval(d, K.at(0.0, -19.4), 1.3, 1.3, LIGHT)


def _front_plate(d) -> None:
    plate = [K.at(-4.6, -6.4), K.at(4.6, -6.4), K.at(5.6, -2.0), K.at(5.2, 4.4), K.at(3.0, 8.2), K.at(-3.0, 8.2), K.at(-5.2, 4.4), K.at(-5.6, -2.0)]
    K.poly(d, plate, ENAMEL)
    K.line(d, plate + plate[:1], BRASS_DEEP, 0.6)
    for sx in (-1.0, 1.0):
        c = (2.6 * sx, -1.2)
        K.oval(d, K.at(*c), 2.7, 2.7, BRASS, BRASS_DEEP, 0.5)
        K.oval(d, K.at(*c), 2.0, 2.0, INK)
        K.oval(d, K.at(*c), 1.3, 1.3, TEAL)
        K.oval(d, K.at(*c), 0.6, 0.6, LIGHT)


def _front_grille(mode: str):
    lit = {"open": 2, "big": 3, "o": 2, "smile": 1}.get(mode, 0)

    def paint(d) -> None:
        K.rrect(d, K.home[0] - 2.8, K.home[1] + 4.2, K.home[0] + 2.8, K.home[1] + 6.6, 0.6, INK, BRASS_DEEP, 0.4)
        for k in range(3):
            K.line(d, [K.at(-1.6 + k * 1.6, 4.8), K.at(-1.6 + k * 1.6, 6.0)], LIGHT if k < lit else ENAMEL_DEEP, 0.6)

    return K.piece(("lovelace_front_grille", lit), paint)


X.front_torso = R.make_front_torso(K, ("lovelace",), BRASS, BRASS_DARK, [(TOP + 1.0, 6.0), (TOP + 3.0, 9.4), (-14.0, 9.4), (-12.0, 4.0), (-8.0, 4.6), (-8.0, 6.4),
                                                                         (FLOOR - 7.0, 13.4), (FLOOR - 7.0, 14.2), (FLOOR - 2.6, 14.2)],
                                   shoulder=(8.6, -30.4, 3.8, 4.2), detail=_front_trunk)
X.front_head_layers = R.front_face(R.make_front_head(K, ("lovelace",), BRASS, BRASS_DEEP, wide=7.8, jaw=6.6, chin=3.2, shape=_front_cap_shape, hair=_front_cap,
                                                    face=_front_plate), mouth=_front_grille)
X.front_shoe = lambda: None
X.front_span = (9.0, 4.0)
R.add_front_rows(X)

# ---- What she shows ------------------------------------------------------------


def _card(seed: int):
    """A card of a program: holes in rows. ``seed`` says which holes."""

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 5.0, K.home[1] - 3.2, K.home[0] + 5.0, K.home[1] + 3.2, 0.6, _SOLID)

    def detail(d) -> None:
        for r in range(3):
            for c in range(6):
                if (seed * 7 + r * 5 + c * 3) % 4 != 0:
                    K.rrect(d, K.home[0] - 4.0 + c * 1.5, K.home[1] - 2.2 + r * 1.7, K.home[0] - 3.2 + c * 1.5, K.home[1] - 1.2 + r * 1.7, 0.1, INK)

    return K.solid(("card", seed), shape, CARD, detail, outline=0.9, rim=0.0, shade=0.0)


def _gear(r: float, teeth: int, turn: int):
    def shape(d) -> None:
        pts = []
        for k in range(teeth * 2):
            a = math.radians(turn + k * 180.0 / teeth)
            rr = r if k % 2 == 0 else r * 0.72
            pts.append(K.at(rr * math.cos(a), rr * math.sin(a)))
        K.poly(d, pts, _SOLID)
        K.oval(d, K.home, r * 0.7, r * 0.7, _SOLID)

    def detail(d) -> None:
        K.oval(d, K.home, r * 0.3, r * 0.3, BRASS_DEEP)

    return K.solid(("gear", r, teeth, turn), shape, BRASS, detail, outline=0.9, rim=0.0, shade=0.3, shade_colour=BRASS_DARK)


def _weave(count: int):
    """What the cards make: threads over and under, a diamond of them."""

    def paint(d) -> None:
        for k in range(count):
            t = k - (count - 1) / 2.0
            colour = TEAL_LIGHT if k % 2 == 0 else BRASS_LIGHT
            K.line(d, [K.at(-14.0, t * 4.0), K.at(0.0, t * 4.0 - 6.0 + abs(t) * 2.0), K.at(14.0, t * 4.0)], TEAL_DARK if k % 2 == 0 else BRASS_DARK, 1.8)
            K.line(d, [K.at(-14.0, t * 4.0), K.at(0.0, t * 4.0 - 6.0 + abs(t) * 2.0), K.at(14.0, t * 4.0)], colour, 0.8)

    return K.aligned(("weave", count), paint)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, i, u = ctx.anim, ctx.i, ctx.u
    if anim == "compute" and u >= 0.2:
        # The cards go up from her hand in an arc, one at each step.
        count = min(5, 1 + int((u - 0.2) / 0.13))
        for k in range(count):
            a = math.radians(-150.0 + 30.0 * k)
            at = (ctx.hand[0] + 4.0 + 20.0 * math.cos(a) + 12.0, ctx.hand[1] - 6.0 + 20.0 * math.sin(a))
            out.append((_card(k), at, f"card_{k}", -60.0 + 30.0 * k))
    elif anim == "analytical_burst" and u >= 0.35:
        out.append((_weave(min(5, 1 + int((u - 0.35) / 0.1))), pin((ctx.head[0] + 3.0, ctx.head[1] - 30.0)), "weave", 0.0))
        for k in range(2):
            hand = ctx.hand if k == 0 else ctx.far_hand
            out.append((_card(k + 3 + i % 2), (hand[0] + (-3.0 if k == 0 else 3.0), hand[1] - 9.0), f"card_{k}", -20.0 + 40.0 * k))
    elif anim == "self_repair" and 0.2 <= u <= 0.9:
        out.append((_gear(4.0, 8, 22 * i), (ctx.far_elbow[0] + 2.0, ctx.far_elbow[1] - 7.0), "gear", 0.0))
        if u >= 0.75:
            out.append((R.tick(K, 3.4, LIGHT, TEAL_DARK), (ctx.far_elbow[0] + 12.0, ctx.far_elbow[1] - 12.0), "tick", 0.0))
    elif anim == "death" and u >= 0.5:
        # Steam, and then nothing.
        for k in range(2):
            rise = (u - 0.5) * 2.0 + k * 0.4
            out.append((R.dust(K, 2.4 - 0.5 * k, ENAMEL, ENAMEL_SHADE), (ctx.head[0] + 4.0 * k, ctx.head[1] - 10.0 - 14.0 * rise), f"steam_{k}", 0.0))
    return out


X.effects = _effects

ROWS = X.rows
FRAME_SIZE = X.frame
render_frame = X.render_frame
_render_frame = render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """Her portraits are frames of this sheet: the clips her conversations
    name."""
    del opts
    r8 = tuple(range(8))
    return X.portraits(out_dir, {
        "default": ("idle", r8, 148, True),
        "portrait": ("idle", (1,), 0, False),
        "talk": ("talk", r8, 110, True),
        "compute": ("compute", r8, 92, True),
    }, still="portrait", view_width=38.0)


# ---- In the round (``_round_cast``) --------------------------------------------
#
# Her head in 3D comes from the numbers of her own makers (``auto_head``).
# Her trunk is drawn by her own ``_torso``, which keeps no numbers, so its
# rings here are the numbers of her front and three-quarter trunk: the
# barrel, the ball of her waist, the bell, its base and her wheels. Her
# rows do not use this.

from types import SimpleNamespace  # noqa: E402

import numpy as np  # noqa: E402

from . import _person_round as O  # noqa: E402
from . import _round_cast as C  # noqa: E402
from . import _round_wear as W  # noqa: E402

_FOOT = FLOOR - 7.0

#: Her trunk: the riveted barrel of her chest and what is on it (the number
#: wheels, the dial, the slot of her cards), the ball of her waist, the bell
#: of bronze with its band of teal, its seams and its band of punched card,
#: and the base under it.
TRUNK_3D = W.Trunk(
    rings=[O.Ring(TOP + 1.0, 0.0, 0.4, 6.0, 5.4), O.Ring(TOP + 3.0, 0.0, 0.4, 9.4, 8.4), O.Ring(-14.0, 0.0, 0.4, 9.4, 8.4), O.Ring(-12.0, 0.0, 0.4, 4.4, 4.0),
           O.Ring(-9.6, 0.0, 0.4, 4.6, 4.2), O.Ring(-8.0, 0.0, 0.4, 6.4, 5.8), O.Ring(_FOOT, 0.0, 0.4, 13.4, 12.0), O.Ring(_FOOT, 0.0, 0.4, 14.2, 12.8),
           O.Ring(FLOOR - 2.6, 0.0, 0.4, 14.2, 12.8)],
    garment=W.Garment(BRASS, BRASS_DARK, radius=9.4, features=[
        W.Across(-180.0, 180.0, TOP + 5.0, BRASS_DARK, width=0.3), W.Across(-180.0, 180.0, -15.4, BRASS_DARK, width=0.3)]
        + [W.Dot(u, v, 0.7, BRASS_DEEP) for u in (-150.0, -110.0, -70.0, -40.0, -13.0, 13.0, 40.0, 70.0, 110.0, 150.0) for v in (TOP + 3.0, -13.6)]
        + [W.Patch(-27.0, 27.0, -30.4, -25.6, INK)] + [W.Patch(-23.0 + k * 16.5, -11.0 + k * 16.5, -29.7, -26.3, CARD) for k in range(3)]
        + [W.Dot(-33.0, -21.0, 2.5, ENAMEL, BRASS_DEEP), W.Patch(-10.0, 44.0, -21.8, -20.4, INK), W.Patch(-2.4, 36.6, -21.0, -18.4, CARD),
           W.Band(-12.0, -8.0, BRASS_DEEP), W.Band(-8.0, _FOOT, BRONZE), W.Band(-5.6, -2.8, TEAL)]
        + [W.Down(u, -2.4, _FOOT - 5.4, BRASS, spread=8.0 * np.sign(u) if u else 0.0) for u in (-120.0, -40.0, 0.0, 40.0, 120.0)]
        + [W.Band(_FOOT - 5.2, _FOOT - 0.8, CARD)]
        + [W.Dot(-180.0 + k * 15.0, _FOOT - 3.6 + 1.2 * (k % 2), 0.6, INK) for k in range(24) if (k * 7) % 5 != 0]
        + [W.Band(_FOOT - 0.6, FLOOR, BRASS_DEEP), W.Shade()]),
    shoulder=((8.6, -30.4, 0.4), (3.8, 4.2, 4.0)))
#: Her four wheels under her base.
WHEELS_3D = W.Worn("wheels", [O.Ring(FLOOR - 4.0, 0.0, 0.4, 1.0, 1.0), O.Ring(FLOOR - 3.0, 0.0, 0.4, 1.0, 1.0)], W.Garment(INK, INK),
                   lumps=[((x, FLOOR - 3.0, z), (1.4, 3.0, 3.0)) for x in (-9.0, 9.0) for z in (-5.6, 6.4)])


# Her head from the side, drawn as the cast draws a head in the numbers of a
# profile: the copper cap in the shape of her hair, its knot behind and the
# spring at her ear, her aerial, the enamel plate of her face with one lens
# and the grille.

_SIDE_EYE = (7.2, -1.0)


def _side_cap_shape(d) -> None:
    K.oval(d, K.at(-1.6, -5.2), 9.6, 6.8, _SOLID)
    K.oval(d, K.at(-10.0, -2.6), 3.4, 3.2, _SOLID)
    K.rrect(d, K.home[0] - 3.6, K.home[1] + 0.6, K.home[0] + 0.2, K.home[1] + 9.6, 1.4, _SOLID)
    K.stroke(d, [K.at(-1.6, -11.0), K.at(-2.6, -18.6)], _SOLID, 1.3)
    K.oval(d, K.at(-2.7, -19.4), 1.6, 1.6, _SOLID)


def _side_cap(d) -> None:
    K.poly(d, [K.at(20.0, -9.2), K.at(9.6, -9.2), K.at(6.6, -7.0), K.at(3.0, -4.6), K.at(1.0, -2.0), K.at(0.2, 0.4), K.at(0.2, 12.0), K.at(-20.0, 12.0),
               K.at(-20.0, -26.0), K.at(20.0, -26.0)], COPPER)
    for strand in ([(-6.0, -10.4), (-1.6, -11.6), (2.4, -10.8)], [(5.0, -10.8), (7.6, -9.4)], [(-7.0, -6.0), (-4.0, -3.6)]):
        K.line(d, [K.at(x, y) for x, y in strand], COPPER_LIGHT, 0.6)
    K.oval(d, K.at(-10.0, -2.6), 1.9, 1.7, None, COPPER_DARK, 0.5)  # type: ignore[arg-type]
    spring = [K.at(-3.2 + 3.2 * (k % 2), 1.4 + k * 1.3) for k in range(7)]
    K.line(d, spring, COPPER_DARK, 1.3)
    K.line(d, spring, COPPER_LIGHT, 0.5)
    K.stroke(d, [K.at(-1.6, -11.0), K.at(-2.6, -18.6)], BRASS_DARK, 0.8)
    K.oval(d, K.at(-2.7, -19.4), 1.3, 1.3, LIGHT)


def _side_face(d) -> None:
    plate = [K.at(2.0, -6.6), K.at(8.6, -7.0), K.at(11.0, -3.0), K.at(11.2, 3.4), K.at(8.8, 7.6), K.at(3.8, 7.8), K.at(1.6, 4.0)]
    K.poly(d, plate, ENAMEL)
    K.line(d, plate + plate[:1], BRASS_DEEP, 0.6)
    (cx, cy), r = _SIDE_EYE, 2.7
    K.oval(d, K.at(cx, cy), r * 0.7 + 0.7, r + 0.7, BRASS, BRASS_DEEP, 0.5)
    K.oval(d, K.at(cx, cy), r * 0.7, r, INK)
    K.oval(d, K.at(cx, cy), r * 0.44, r * 0.62, TEAL)
    K.oval(d, K.at(cx + 0.4, cy), r * 0.22, r * 0.3, LIGHT)
    _rivets(d, [(0.4, -1.0), (0.6, 3.0)])


_side_head = R.make_head(K, ("lovelace_side",), BRASS, BRASS_DARK, BRASS_DEEP, skull=(0.0, -2.2, 9.2, 8.4), jaw=(3.0, 3.6, 6.8, 5.8), nose=None, ear=None,
                         shape=_side_cap_shape, under=_side_cap, over=_side_face, far_shade=False)


def _side_lids(mode: str):
    if mode != "closed":
        return None

    def paint(d) -> None:
        (cx, cy), r = _SIDE_EYE, 2.7
        K.oval(d, K.at(cx, cy), r * 0.7, r, BRASS_DARK)
        K.line(d, [K.at(cx - r * 0.7, cy), K.at(cx + r * 0.7, cy)], BRASS_DEEP, 0.6)

    return K.piece(("lovelace_side_lids",), paint)


def _side_grille(mode: str):
    lit = {"open": 2, "big": 3, "o": 2, "smile": 1}.get(mode, 0)

    def paint(d) -> None:
        K.rrect(d, K.home[0] + 7.8, K.home[1] + 4.2, K.home[0] + 10.8, K.home[1] + 6.6, 0.6, INK, BRASS_DEEP, 0.4)
        for k in range(2):
            K.line(d, [K.at(8.8 + k * 1.2, 4.8), K.at(8.8 + k * 1.2, 6.0)], LIGHT if k < lit else ENAMEL_DEEP, 0.6)

    return K.piece(("lovelace_side_grille", lit), paint)


def _side_layers(pose):
    return [(_side_head(), "head"), (_side_lids(str(pose["eyes"])), "lids"), (_side_grille(str(pose["mouth"])), "grille")]


#: Her front head's numbers for ``auto_head``: its lenses are painted in
#: the head and its grille has no numbers, so only the head counts.
_FRONT_NUMBERS = SimpleNamespace(front_head_layers=SimpleNamespace(spec=SimpleNamespace(head=X.front_head_layers.spec.head, eyes=None, brows=None, mouth=None)))
_CAP = ((0.0, -4.8, -1.0), (8.8, 6.8, 8.8))

ROUND = C.Round(
    DISPLAY_NAME, C.PersonBody(X, lambda: None, mirror=("head",), heads={"side": _side_layers}),
    C.Look(
        # The copper cap in the shape of her hair: all of her head but the
        # plate of her face, a knot behind, a spring at each ear; her aerial.
        C.auto_head(_FRONT_NUMBERS, _head, None, hair=lambda u, v: ~((np.abs(u) < 56.0) & (v > -6.6)), hair_colour=COPPER, hair_shade=COPPER_DARK,
                    volumes=[_CAP, ((0.0, -2.6, -9.4), (3.4, 3.2, 3.2))] + [((s * 7.2, 4.6, -0.6), (1.8, 4.6, 1.8)) for s in (-1.0, 1.0)],
                    eye_size=1.6, ink=INK, eye_white=INK, iris=TEAL,
                    lines=[O.curve([O.on_ellipsoid(*_CAP, u, v, 0.2)[0] for v in (-11.0, -8.0)], COPPER_LIGHT, 0.6) for u in (-130.0, -60.0, 60.0, 130.0)]),
        TRUNK_3D,
        head_pieces=[W.Antlers([[(0.0, -11.0, -1.0), (0.0, -18.6, -1.6)]], 0.8, BRASS_DARK, BRASS_DEEP, name="aerial", lead=0.5)],
        pieces=[("trunk", WHEELS_3D)]),
    # Her grips one on the other in front of her, as a person of rank stands.
    C.Stance(hands={"r": C.Hand(at=(1.0, -14.0, 10.6), pole=(-1.0, 0.3, -0.4), mode="fist"),
                    "l": C.Hand(at=(3.2, -13.0, 10.2), pole=(1.0, 0.3, -0.4), mode="fist")}))


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

del mix

if __name__ == "__main__":
    raise SystemExit(main())
