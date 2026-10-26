"""Sprite generator for Pipi Tau: the mathematician who turns one problem that
can not be done into six lemmas that can.

A loose parody of Terence Tao (tau for Tao, and pi twice for a full turn). He
is not a portrait.

The look (2026-10-13): a slight man in his thirties seen three quarters from
the front, facing right, who looks younger than he is. Straight black hair
that falls to one side of his brow, thin rectangular glasses, a quick small
smile. A short teal jacket open over a dark shirt with a tau on it, slim grey
trousers, running shoes. He does not stand still for long: his weight is on
the front of his feet.

He is drawn from the man and not from a type (Jon, 2026-10-13, of another
person of this cast: "needs to read like paul erdos not bearnie sanders"). He
is a grown man, not a mascot. He holds nothing; there is no drop shadow.

What he shows: an epsilon; the primes, in a row with gaps; a few points that
are enough to know the whole (the sense he compresses); and the lemmas,
linked into a chain.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, how he stands and what he shows are his.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, lerp, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "pipi_tau"
DISPLAY_NAME = "Pipi Tau"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_pipi_tau", "display_name": "Pipi Tau"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "mathematician",
            "problem_runner",
            "collaborative",
            "playable_candidate",
        ],
        "locomotion_hint": "Run",
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
        "problem_runner",
        "collaborative",
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
            "Pipi Tau is a loose Terence Tao-inspired polymath parody rather than a biographical "
            "portrait. The name turns Tao into tau and doubles pi for a full circle; the character "
            "emphasizes breadth, collaboration, compression, rotating problems into known forms, and "
            "reducing impossible goals to reachable lemmas."
        ),
        "gameplay_description": (
            "Use as a fast generalist, collaborative mathematician, traversal coach, or playable "
            "problem solver. His toolkit should chain small techniques across domains, rotate problem "
            "geometry, and win by repeatedly reaching the next lemma instead of unveiling one grand "
            "trick."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'One pi gets you halfway home. Tau finishes the trip.',
        'I rotate it until it resembles a problem somebody else already knows how to annoy.',
        'Do not solve the whole level. Reach the next platform.',
    ],
)

JACKET: RGBA = (40, 150, 150, 255)
JACKET_DARK: RGBA = (24, 100, 110, 255)
JACKET_LIGHT: RGBA = (100, 200, 190, 255)
TEE: RGBA = (40, 44, 58, 255)
TEE_MARK: RGBA = (250, 226, 130, 255)
TROUSER: RGBA = (118, 122, 136, 255)
TROUSER_DARK: RGBA = (80, 84, 100, 255)
SHOE: RGBA = (238, 238, 232, 255)
SHOE_DARK: RGBA = (150, 156, 170, 255)
SOLE: RGBA = (230, 110, 70, 255)
SKIN: RGBA = (232, 190, 152, 255)
SKIN_SHADE: RGBA = (200, 152, 122, 255)
SKIN_DEEP: RGBA = (150, 102, 90, 255)
HAIR: RGBA = (28, 28, 36, 255)
HAIR_LIGHT: RGBA = (78, 82, 100, 255)
FRAME: RGBA = (40, 44, 58, 255)
LENS: RGBA = (232, 244, 250, 140)
INK: RGBA = (26, 22, 30, 255)
MATH: RGBA = (252, 230, 140, 255)
MATH_DARK: RGBA = (206, 136, 56, 255)
COOL: RGBA = (150, 226, 240, 255)
COOL_DARK: RGBA = (40, 120, 150, 255)

#: 173 cm, slight, on the front of his feet.
BUILD = Build(hip_up=50.0, thigh=24.2, shin=23.1, neck=(1.0, -35.0), upper=18.8, fore=17.8, near_shoulder=(-4.8, -30.8), far_shoulder=(6.6, -30.4),
              near_hip=(-3.2, 0.0), far_hip=(3.2, 0.0), head_up=(1.0, -12.2), height=109.0, half_width=(12.0, 13.5))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0


def _front(d, hb: float, hf: float) -> None:
    """The dark shirt with the tau on it, where his jacket is open."""
    K.poly(d, [K.at(1.8, TOP), K.at(11.6, TOP), K.at(12.0 + hf, 9.0), K.at(4.4 + hf * 0.5, 9.0), K.at(3.4, -14.0)], TEE)
    K.poly(d, [K.at(9.6, TOP), K.at(12.6, TOP), K.at(13.0 + hf, 9.0), K.at(10.4 + hf, 9.0)], JACKET_DARK)
    K.poly(d, [K.at(3.6, TOP - 1.0), K.at(8.4, TOP - 1.0), K.at(6.2, TOP + 3.4)], SKIN_SHADE)
    for line in R.STROKES["tau"]:
        K.line(d, [K.at(4.8 + x * 4.4, -24.0 + y * 6.0) for x, y in line], TEE_MARK, 1.0)
    K.poly(d, [K.at(-0.6, TOP + 1.0), K.at(2.6, TOP), K.at(3.8, -18.0), K.at(0.2, -25.0)], JACKET_LIGHT)
    K.line(d, [K.at(0.2, -25.0), K.at(3.8, -18.0), K.at(3.4, -14.0), K.at(4.4 + hf * 0.5, 6.0)], JACKET_DARK, 0.7)
    K.line(d, [K.at(-8.0, 3.0), K.at(8.0, 3.6)], JACKET_DARK, 0.9)


X.torso = R.make_torso(K, ("tau",), JACKET, JACKET_DARK, back=(8.2, 8.6, 7.4, 8.4), front=(7.6, 9.0, 8.4, 9.0), hem_y=6.0, top=TOP,
                       shoulders=((-4.6, -30.2), (6.0, -30.0)), shoulder_r=(4.8, 4.4), shade_from=40.0, detail=_front)

NEAR_EYE = (1.8, -0.4)
FAR_EYE = (7.0, -0.6)


def _hair_shape(d) -> None:
    K.oval(d, K.at(-0.8, -5.0), 9.0, 8.0, WHITE)
    K.poly(d, [K.at(1.0, -11.6), K.at(9.4, -9.6), K.at(10.2, -3.6), K.at(6.4, -6.0)], WHITE)


def _hair(d) -> None:
    # Straight and black; it falls across his brow toward the far side.
    K.poly(d, [K.at(20.0, -3.8), K.at(9.6, -3.8), K.at(7.0, -6.6), K.at(3.6, -6.0), K.at(0.4, -4.4), K.at(-2.4, -4.0), K.at(-3.2, -1.4), K.at(-6.0, -1.2),
               K.at(-6.6, 3.2), K.at(-5.0, 4.4), K.at(-4.8, 6.2), K.at(-20.0, 6.2), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
    for strand in ([(-4.0, -11.0), (2.0, -9.6), (8.0, -5.6)], [(-6.0, -8.0), (0.0, -7.4), (5.6, -5.0)], [(-6.0, -1.0), (-8.0, 1.6)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_LIGHT, 0.6)


def _face(d) -> None:
    for (cx, cy), rx in ((NEAR_EYE, 3.0), (FAR_EYE, 2.0)):
        K.rrect(d, K.home[0] + cx - rx, K.home[1] + cy - 1.9, K.home[0] + cx + rx, K.home[1] + cy + 1.9, 0.6, LENS)


def _glasses():
    def paint(d) -> None:
        for (cx, cy), rx in ((NEAR_EYE, 3.0), (FAR_EYE, 2.0)):
            K.rrect(d, K.home[0] + cx - rx, K.home[1] + cy - 1.9, K.home[0] + cx + rx, K.home[1] + cy + 1.9, 0.6, None, FRAME, 0.7)  # type: ignore[arg-type]
        K.line(d, [K.at(NEAR_EYE[0] + 3.0, -1.0), K.at(FAR_EYE[0] - 2.0, -1.1)], FRAME, 0.7)
        K.line(d, [K.at(NEAR_EYE[0] - 3.0, -1.0), K.at(-4.6, -0.6)], FRAME, 0.7)

    return K.piece(("tau_glasses",), paint)


_head = R.make_head(K, ("tau",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.2, 7.8, 8.6), jaw=(2.4, 3.8, 5.6, 6.8),
                    nose=((7.2, 0.2), (9.2, 3.0), (8.8, 4.0), (7.2, 4.4)), ear=(-4.8, 1.0, 2.0, 2.9), shape=_hair_shape, under=_hair, over=_face)
_eyes = R.make_eyes(K, (NEAR_EYE[0] + 0.2, NEAR_EYE[1] + 0.2), (FAR_EYE[0] + 0.1, FAR_EYE[1] + 0.2), ink=INK, white=None, lid=None, size=0.9)
_brows = R.make_brows(K, [(-0.8, -3.6), (1.8, -4.2), (4.4, -3.8)], [(5.8, -3.9), (7.2, -4.2), (8.6, -3.8)], HAIR, 1.0)
_mouth = R.make_mouth(K, (5.4, 7.4), (130, 60, 64, 255), wide=0.85)

X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_glasses(), "glasses"), (_brows(R.brow_mood(pose)), "brows"),
                              (_mouth(str(pose["mouth"])), "mouth")]
X.neck = R.make_neck(K, SKIN_SHADE, 4.2)
X.upper_arm = lambda near: [(0.0, 1.0, 6.4, 5.4, JACKET if near else JACKET_DARK)]
X.forearm = lambda near: [(0.0, 1.0, 5.4, 4.6, JACKET if near else JACKET_DARK)]
X.thigh = lambda near: [(0.0, 1.0, 6.8, 5.6, TROUSER if near else TROUSER_DARK)]
X.shin = lambda near: [(0.0, 1.0, 5.6, 4.6, TROUSER if near else TROUSER_DARK)]
X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, JACKET_LIGHT, JACKET, size=0.95)
X.shoe = R.make_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up, long=1.08, sole=SOLE)

# ---- How he holds himself ----------------------------------------------------

AT_TEMPLE = (8.0, -9.0)
X.set_rest(lean=3.0, na=(-2.0, 24.5), fa=(2.5, 24.0), nf=(-3.8, 0.0, 0.0), ff=(4.8, 0.0, 0.0))


@X.row
def idle(i: int, n: int):
    # He comes up on his toes and down again, and taps his temple: one more case.
    _, s, c = loop(i, n)
    tap = i in (2, 3, 4)
    return P(hip=(0.0, 0.2 - 0.8 * max(0.0, s)), lean=3.0, head=(0.3, 0.0, 2.0 * c), na=AT_TEMPLE if tap else (9.0, 9.0), nh="point" if tap else "soft", fa=(-1.0, 21.0),
             nf=(-3.8, 0.0, 6.0 * max(0.0, s)), ff=(4.8, 0.0, 6.0 * max(0.0, s)), eyes="closed" if i == n - 2 else "open", mouth="smile" if tap else "flat")


@X.row
def talk(i: int, n: int):
    # Fast, both hands: first this, then this, and so that.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.4 * s), lean=4.0, head=(0.3, 0.0, 3.0 * s), na=(14.0 + 4.0 * c, 4.0 - 6.0 * max(0.0, s)), nh="open", fa=(16.0 - 4.0 * c, 7.0 + 5.0 * min(0.0, s)), fh="open",
             mouth=("open", "smile", "big", "smile")[i % 4], brows=1.0 if s > 0.2 else 0.0)


@X.row
def epsilon_dash(i: int, n: int):
    # A very short step, done very fast, done again.
    _, s, _c = loop(i, n)
    return dict(X.full(R.DASH), hip=(2.0, 5.0 + 0.8 * s), lean=28.0, na=(24.0, 6.0), nh="point", fa=(-16.0, 10.0), nf=(-12.0 - s, -5.0 - s, 36.0))


@X.row
def full_turn(i: int, n: int):
    # Two pi: once all the way round, and he comes down where he began.
    ph, s, c = loop(i, n)
    up = math.sin(math.pi * shot(i, n))
    return P(off=(0.0, -9.0 * up), hip=(0.0, 1.0), lean=8.0 * s, head=(0.0, 0.0, 8.0 * s), na=(-18.0 + 8.0 * c, 0.0), nab=-1.0, fa=(20.0 - 8.0 * c, 0.0), nh="open", fh="open",
             nf=(-4.0 + 3.0 * s, -4.0 * up, 20.0 * up), ff=(5.0 - 3.0 * s, -6.0 * up, 10.0 * up), mouth="open", eyes="happy")


@X.row
def celebrate(i: int, n: int):
    ph, s, _c = loop(i, n)
    up = abs(math.sin(ph))
    return P(off=(0.0, -9.0 * up), hip=(0.0, 3.0 * (1.0 - up)), lean=-3.0, head=(0.0, 0.0, -8.0), na=(8.0, -25.0 + 2.0 * s), nab=-1.0, arm="under", nh="fist",
             fa=(-8.0, 16.0), fh="fist", nf=(-6.0, -4.0 * up, 24.0 * up), ff=(7.0, -6.0 * up, 14.0 * up), eyes="happy", mouth="big", brows=1.0)


@X.row
def taunt(i: int, n: int):
    # He writes it on his hand, shows you, and it is short.
    write = P(lean=6.0, head=(0.5, 0.5, 10.0), na=(10.0, 9.0), nh="point", fa=(12.0, 11.0), fh="flat", brows=-1.0)
    show = P(lean=0.0, na=(-2.0, 24.5), fa=(20.0, 0.0), fh="flat", mouth="smile", brows=1.0, eyes="happy")
    return X.keys(shot(i, n), [(0.0, P()), (0.25, write), (0.6, dict(write, na=(12.0, 10.0))), (0.8, show), (1.0, show)])


X.alias(prime_stride="attack_side", compressed_sense="charge", polymath_chain="cast")
X.rows = [("idle", 8, 145), ("walk", 8, 104), ("run", 8, 76), ("crouch", 6, 95), ("crouch_walk", 8, 88), ("jump", 6, 92), ("fall", 6, 92), ("land_hard", 8, 92),
          ("land_recovery", 6, 72), ("dash_startup", 4, 48), ("dash", 6, 60), ("epsilon_dash", 8, 54), ("slide", 6, 68), ("roll", 8, 56), ("wall_grab", 6, 105),
          ("wall_jump", 6, 82), ("ledge_grab", 6, 98), ("ledge_climb", 6, 98), ("ledge_getup", 6, 42), ("ledge_roll", 8, 38), ("climb", 8, 98), ("swim", 8, 102),
          ("float_glide", 8, 108), ("block", 6, 82), ("hit", 5, 86), ("death", 8, 105), ("talk", 8, 104), ("interact", 8, 90), ("jab", 5, 56), ("punch", 7, 68),
          ("prime_stride", 8, 64), ("attack_up", 8, 64), ("attack_down", 8, 64), ("air_neutral", 8, 60), ("air_forward", 7, 60), ("air_back", 7, 60), ("air_down", 7, 68),
          ("air_up", 7, 60), ("compressed_sense", 8, 74), ("polymath_chain", 8, 78), ("full_turn", 10, 76), ("celebrate", 8, 88), ("taunt", 8, 92)]

# ---- From the front ------------------------------------------------------------

def _front_jacket(d) -> None:
    """His jacket open on the tee with the tau on it."""
    K.poly(d, [K.at(-4.4, TOP - 1.0), K.at(4.4, TOP - 1.0), K.at(5.0, 8.0), K.at(-5.0, 8.0)], TEE)
    K.poly(d, [K.at(-2.6, TOP - 1.0), K.at(2.6, TOP - 1.0), K.at(0.0, TOP + 3.4)], SKIN_SHADE)
    K.line(d, [K.at(-2.6, -22.6), K.at(2.6, -22.6)], TEE_MARK, 1.0)
    K.line(d, [K.at(0.2, -22.6), K.at(-0.4, -17.6), K.at(0.8, -16.8)], TEE_MARK, 1.0)
    for sx in (-1.0, 1.0):
        K.line(d, [K.at(4.4 * sx, TOP), K.at(5.0 * sx, 6.0)], JACKET_DARK, 0.7)
        K.poly(d, [K.at(4.4 * sx, TOP - 1.0), K.at(7.0 * sx, TOP), K.at(5.0 * sx, TOP + 6.0)], JACKET_LIGHT)
        K.line(d, [K.at(8.6 * sx, -2.0), K.at(6.0 * sx, -1.6)], JACKET_DARK, 0.6)


def _front_hair_shape(d) -> None:
    K.oval(d, K.at(0.0, -5.8), 9.4, 7.4, WHITE)


def _front_hair(d) -> None:
    # Swept across his forehead from one side.
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -1.0), K.at(7.6, -1.0), K.at(7.4, -5.0), K.at(5.0, -7.4), K.at(0.0, -6.4), K.at(-4.6, -4.6),
               K.at(-7.2, -3.4), K.at(-7.6, -1.0), K.at(-20.0, -1.0)], HAIR)
    for strand in ([(5.0, -11.0), (0.0, -9.0), (-5.0, -6.0)], [(7.0, -8.0), (2.0, -7.6)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_LIGHT, 0.6)


def _front_glasses(d) -> None:
    for sx in (-1.0, 1.0):
        K.rrect(d, K.home[0] + 3.4 * sx - 2.8, K.home[1] - 2.6, K.home[0] + 3.4 * sx + 2.8, K.home[1] + 1.6, 0.8, LENS, FRAME, 0.9)
        K.line(d, [K.at(6.2 * sx, -1.4), K.at(8.0 * sx, -1.8)], FRAME, 0.8)
    K.line(d, [K.at(-0.6, -1.2), K.at(0.6, -1.2)], FRAME, 0.8)
    K.line(d, [K.at(-0.3, 0.8), K.at(-1.2, 3.8), K.at(0.0, 4.6), K.at(1.2, 3.8)], SKIN_DEEP, 0.6)


X.front_torso = R.make_front_torso(K, ("tau",), JACKET, JACKET_DARK, [(TOP, 4.0), (TOP + 3.6, 8.4), (-24.0, 9.0), (-6.0, 8.6), (6.0, 9.0)],
                                   shoulder=(6.8, -30.8, 4.2, 4.6), detail=_front_jacket)
X.front_head_layers = R.front_face(R.make_front_head(K, ("tau",), SKIN, SKIN_DEEP, wide=7.8, jaw=6.2, chin=4.0, ears=SKIN, shape=_front_hair_shape, hair=_front_hair,
                                                    face=_front_glasses),
                                   R.make_front_eyes(K, ("tau",), white=None, ink=INK, spread=3.4, y=-0.6, size=0.9), R.make_front_brows(K, ("tau",), HAIR, spread=3.4, y=-4.2),
                                   R.make_front_mouth(K, ("tau",), y=8.2, colour=(130, 60, 64, 255), wide=0.8))
X.front_shoe = R.make_front_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up)
X.front_span = (7.8, 4.4)
R.add_front_rows(X, hands="sides")

# ---- What he shows -----------------------------------------------------------

PRIMES = ("2", "3", "5", "7", "11", "13")


def _sym(symbols, size: float, fill: RGBA = MATH, dark: RGBA = MATH_DARK):
    return R.glyph(K, symbols, size, fill, dark)


def _sparse(count: int, known: bool):
    """A grid, a few points of it lit: that is all he needs. ``known``: he has
    the rest of it."""
    lit = ((0, 1), (2, 0), (3, 2), (1, 3), (4, 1), (2, 4), (4, 4))

    def paint(d) -> None:
        for gx in range(5):
            for gy in range(5):
                on = (gx, gy) in lit[:count]
                q = K.at(-10.0 + gx * 5.0, -10.0 + gy * 5.0)
                if on or known:
                    K.oval(d, q, 2.2, 2.2, OUTLINE)
                    K.oval(d, q, 1.4, 1.4, MATH if on else COOL)
                else:
                    K.oval(d, q, 0.8, 0.8, COOL_DARK)

    return K.aligned(("sparse", count, known), paint)


def _chain(links: int):
    """Lemmas, linked, along +x."""

    def paint(d) -> None:
        for k in range(links):
            c = K.at(5.0 + 8.0 * k, 1.2 * (-1.0 if k % 2 else 1.0))
            for edge in (True, False):
                K.oval(d, c, 5.0, 3.2, None, COOL_DARK if edge else (MATH if k == links - 1 else COOL), 2.6 if edge else 1.2)  # type: ignore[arg-type]

    return K.aligned(("chain", links), paint)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, i, n, u, hand, head, hip = ctx.anim, ctx.i, ctx.n, ctx.u, ctx.hand, ctx.head, ctx.hip
    if anim in ("jab", "epsilon_dash") and (anim == "epsilon_dash" or 1 <= i <= 3):
        out.append((_sym(["epsilon"], 8.0, COOL, COOL_DARK), (hand[0] + 18.0, hand[1] - 2.0), "epsilon", 0.0))
        if anim == "epsilon_dash":
            for k in range(2):
                out.append((R.dust(K, 1.4 - 0.4 * k, COOL, COOL_DARK), (hip[0] - 22.0 - 9.0 * k, hip[1] + 6.0 + 3.0 * ((i + k) % 2)), f"dust_{k}", 0.0))
    elif anim == "punch" and 3 <= i <= 5:
        out.append((R.burst(K, 8.0 + (i - 3), MATH, MATH_DARK), (hand[0] + 16.0, hand[1]), "burst", 0.0))
        out.append((_sym(["tau"], 8.0), (hand[0] + 16.0, hand[1]), "tau", 0.0))
    elif anim in ("slash", "ledge_getup_attack") and 2 <= i <= 6:
        a = math.degrees(math.atan2(hand[1] - ctx.shoulder[1], hand[0] - ctx.shoulder[0]))
        lead = int(round(a / 5.0)) * 5
        out.append((R.swoosh(K, 46.0, lead - 90, lead + 6, 7.0, MATH, MATH_DARK), ctx.shoulder, "swoosh", 0.0))
    elif anim in ("attack_side", "prime_stride") and 3 <= i <= 6:
        # The primes in a row, and the gaps between them.
        for k in range(1 + (i - 3)):
            x = hand[0] + 14.0 + (4.0, 9.0, 18.0, 27.0)[k] * 1.0
            out.append((_sym(PRIMES[k], 7.0, MATH if k % 2 == 0 else COOL, MATH_DARK if k % 2 == 0 else COOL_DARK), (min(x, 196.0), hand[1] - 2.0 - 3.0 * (k % 2)), f"prime_{k}", 0.0))
    elif anim in ("attack_up", "air_up") and 3 <= i <= 6:
        y = hand[1] - 16.0 - 4.0 * (i - 3)
        if y > 14.0:
            out.append((_sym(PRIMES[(i - 3) % 6], 8.0), (hand[0] + 3.0, y), "prime", 0.0))
    elif anim == "attack_down" and i >= 4:
        out.append((R.burst(K, 10.0 + min(3, i - 4), COOL, COOL_DARK, 10), (hand[0] + 8.0, ctx.ground - 12.0), "burst", 0.0))
        out.append((_sym(["epsilon"], 8.0), (hand[0] + 8.0, ctx.ground - 12.0), "epsilon", 0.0))
    elif anim == "air_neutral":
        for k, sym in enumerate((["tau"], ["pi"], ["epsilon"])):
            a = ctx.phase + k * math.tau / 3.0
            out.append((_sym(sym, 8.0, (MATH, COOL, MATH)[k], (MATH_DARK, COOL_DARK, MATH_DARK)[k]), (hip[0] + 34.0 * math.cos(a), hip[1] - 18.0 + 11.0 * math.sin(a)), f"sym_{k}", 0.0))
    elif anim in ("charge", "compressed_sense"):
        out.append((_sparse(min(7, 1 + i), i >= n - 1), pin((head[0] - 2.0, head[1] - 34.0)), "sparse", 0.0))
    elif anim in ("cast", "polymath_chain") and i >= 2:
        out.append((_chain(min(5, i - 1)), pin((hand[0] + 6.0, hand[1] - 2.0)), "chain", 0.0))
    elif anim == "full_turn":
        a = ctx.phase
        out.append((_sym(["pi"], 8.0), (hip[0] + 30.0 * math.cos(a), hip[1] - 20.0 + 9.0 * math.sin(a)), "pi_0", 0.0))
        out.append((_sym(["pi"], 8.0, COOL, COOL_DARK), (hip[0] - 30.0 * math.cos(a), hip[1] - 20.0 - 9.0 * math.sin(a)), "pi_1", 0.0))
    elif anim == "celebrate":
        out.append((_sym(["tau"], 9.0), (head[0] + 4.0, head[1] - 26.0 - 2.0 * abs(math.sin(ctx.phase))), "tau", 0.0))
    elif anim == "taunt" and u >= 0.8:
        out.append((_sym(["epsilon"], 7.0), (ctx.far_hand[0] + 8.0, ctx.far_hand[1] - 10.0), "epsilon", 0.0))
    elif anim == "interact" and 3 <= i <= 5:
        out.append((R.tick(K, 4.0, MATH, MATH_DARK), (hand[0] + 16.0, hand[1] - 5.0), "tick", 0.0))
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
        "default": ("idle", (1,), 0, False),
        "explaining": ("talk", tuple(range(8)), 104, True),
        "thinking": ("idle", (2, 3, 4, 5), 180, True),
    }, view_width=34.0)


# ---- In the round (``_round_cast``) --------------------------------------------
#
# His trunk and head in 3D come from the numbers of his own makers
# (``auto_trunk``, ``auto_head``); what they do not say is here, as data. His
# rows do not use this.

import numpy as np  # noqa: E402

from . import _round_cast as C  # noqa: E402
from . import _round_wear as W  # noqa: E402

ROUND = C.Round(
    DISPLAY_NAME, C.PersonBody(X),
    C.Look(
        # Straight black hair that falls across his brow, short at the back;
        # thin rectangular glasses.
        C.auto_head(X, _head, _eyes,
                    hair=lambda u, v: (v < -6.4 + 3.0 * np.clip(np.abs(u) / 60.0, 0.0, 1.0)) | ((np.abs(u) > 75.0) & (v < -1.0))
                    | ((np.abs(u) > 105.0) & (v < 6.2)),
                    hair_colour=HAIR, hair_shade=HAIR_LIGHT, volumes=[((0.0, -5.4, -0.6), (8.4, 7.0, 8.4))],
                    glasses=C.O.Glasses("square", (2.8, 2.1), FRAME, LENS, 0.8)),
        # His short jacket open on the dark shirt with the tau on it.
        C.auto_trunk(X, [W.Opening(30.0, TEE, top=TOP), W.Neckline(TOP - 1.0, TOP + 3.4, 14.0, SKIN_SHADE),
                         W.Path([(-14.0, -22.6), (14.0, -22.6)], TEE_MARK, 0.5), W.Path([(1.0, -22.6), (-2.0, -17.6), (5.0, -16.8)], TEE_MARK, 0.5),
                         W.Lapels(30.0, TOP, -25.0, 10.0, JACKET_LIGHT, line=JACKET_DARK), W.Across(40.0, 80.0, 3.2, JACKET_DARK, both=True)])),
    # His arms loose at his sides, his weight forward.
    C.Stance(hands={"r": C.Hand(l=-8.8, pole=(-0.4, 0.0, -1.0)), "l": C.Hand(l=8.8, pole=(0.4, 0.0, -1.0))}, stagger=2.0))


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
