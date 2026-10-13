"""Sprite generator for Girdle: the logician who found the room no proof can
enter.

A severe parody of Kurt Godel (the name is the sound of his, bent into an
ordinary object).

The look (2026-10-13): a thin, upright man seen three quarters from the front,
facing right. Dark hair combed straight back from a high forehead, round black
glasses, a narrow face, a small mouth that does not smile much. A cream linen
suit of three pieces, buttoned, a dark tie, brown shoes: the suit he walked in
with his one friend. He stands very straight with his hands behind his back,
and now and then he puts his glasses right with one finger.

He is drawn from the man and not from a type (Jon, 2026-10-13, of another
person of this cast: "needs to read like paul erdos not bearnie sanders"). He
is a grown man, not a mascot. He holds nothing; there is no drop shadow.

His logic is written in pale green: the turnstile, the sentence G that says
of itself that it can not be proved, and the arrow that goes round and comes
back to where it began.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the suit, how he stands and what he writes are his.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, keys, lerp, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "girdle"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_girdle", "display_name": "Girdle"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": ["story", "humanoid", "logician", "playable_candidate"],
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
    "tags": ["story", "humanoid", "logician", "playable_candidate"],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 65.0, "y": 28.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 65.0, "y": 65.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 48.0, "y": 87.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 84.0, "y": 86.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 65.0, "y": 5.0}},
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
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Girdle is a severe parody of Kurt Godel, named by bending the sound of Godel into an "
            "ordinary object. He personifies incompleteness, self-reference, consistency anxiety, and "
            "the unnerving discovery that sufficiently strong formal systems contain truths they "
            "cannot prove from within."
        ),
        "gameplay_description": (
            "Use as a logician, unsettling advisor, precision fighter, or rule-breaking boss. His "
            "gameplay should expose statements outside a system, weaponize self-reference, and make "
            "apparently complete structures reveal inaccessible rooms."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'Every consistent structure has one room it cannot enter.',
        'Do not tell me the structure is sound.',
        'The proof cannot live entirely inside the thing it judges.',
    ],
)


SUIT: RGBA = (236, 226, 200, 255)
SUIT_DARK: RGBA = (186, 172, 146, 255)
SUIT_LIGHT: RGBA = (250, 244, 226, 255)
VEST: RGBA = (214, 202, 174, 255)
SHIRT: RGBA = (250, 250, 246, 255)
TIE: RGBA = (62, 52, 72, 255)
SHOE: RGBA = (112, 72, 50, 255)
SHOE_DARK: RGBA = (70, 44, 36, 255)
SKIN: RGBA = (234, 204, 178, 255)
SKIN_SHADE: RGBA = (204, 166, 144, 255)
SKIN_DEEP: RGBA = (160, 112, 98, 255)
HAIR: RGBA = (52, 42, 44, 255)
HAIR_LIGHT: RGBA = (104, 90, 96, 255)
FRAME: RGBA = (22, 20, 28, 255)
LENS: RGBA = (232, 244, 248, 180)
INK: RGBA = (28, 24, 32, 255)
LOGIC: RGBA = (196, 250, 214, 255)
LOGIC_DARK: RGBA = (70, 150, 120, 255)
LOGIC_GOLD: RGBA = (252, 226, 140, 255)

#: Thin and straight: narrow shoulders, long legs, his head over his heels.
BUILD = Build(hip_up=50.0, thigh=24.1, shin=23.2, neck=(0.4, -35.0), upper=19.0, fore=18.0, near_shoulder=(-5.4, -31.4), far_shoulder=(6.6, -31.0),
              near_hip=(-3.2, 0.0), far_hip=(3.2, 0.0), head_up=(0.8, -12.4), height=109.0, half_width=(12.0, 13.0))

G = Person(TARGET_NAME, BUILD)
K = G.K

#: Both hands behind his back.
BEHIND_NEAR = (-5.5, 23.0)
BEHIND_FAR = (-5.0, 23.0)
G.set_rest(na=BEHIND_NEAR, fa=BEHIND_FAR, mouth="flat", nf=(-3.6, 0.0, 0.0), ff=(4.6, 0.0, 0.0))

R.STROKES["G"] = (((0.95, 0.2), (0.6, 0.0), (0.2, 0.15), (0.05, 0.5), (0.2, 0.85), (0.6, 1.0), (0.95, 0.8), (0.95, 0.52), (0.55, 0.52)),)
R.STROKES["not"] = (((0.05, 0.4), (0.95, 0.4), (0.95, 0.78)),)


# ---- The pieces --------------------------------------------------------------


def _torso(hem_back: int, hem_front: int):
    """His jacket from his hips, his spine up: buttoned, narrow, its hem a
    little below his hips."""
    hb, hf = float(hem_back), float(hem_front)
    back_hem, front_hem = K.at(-9.4 - hb, 9.0 - hb * 0.25), K.at(10.2 + hf, 8.4)

    def shape(d) -> None:
        K.poly(d, [K.at(-4.0, -38.0), K.at(-9.2, -34.0), K.at(-9.6, -24.0), K.at(-8.8, -12.0), K.at(-8.4, -3.0), back_hem, front_hem,
                   K.at(9.6, -3.0), K.at(9.4, -14.0), K.at(10.0, -27.0), K.at(8.2, -35.0), K.at(4.0, -38.4)], WHITE)
        K.oval(d, K.at(-5.4, -31.0), 5.2, 5.8, WHITE)
        K.oval(d, K.at(6.0, -30.8), 4.8, 5.4, WHITE)

    def detail(d) -> None:
        # The far side of his chest is in his own shade.
        K.poly(d, [K.at(7.4, -40.0), K.at(14.0, -40.0), K.at(14.0 + hf, 12.0), K.at(7.6 + hf * 0.6, 12.0), K.at(6.6, -6.0)], SUIT_DARK)
        # His shirt and his tie, in the V of his vest and his lapels.
        K.poly(d, [K.at(-0.4, -38.6), K.at(9.2, -38.6), K.at(6.0, -17.0)], VEST)
        K.poly(d, [K.at(1.2, -38.6), K.at(8.0, -38.6), K.at(5.6, -23.0)], SHIRT)
        K.poly(d, [K.at(3.4, -37.4), K.at(6.0, -37.4), K.at(6.4, -25.0), K.at(5.0, -22.4), K.at(3.8, -25.0)], TIE)
        K.poly(d, [K.at(-2.4, -38.6), K.at(1.2, -38.6), K.at(5.6, -17.6), K.at(0.4, -27.0)], SUIT_LIGHT)
        K.line(d, [K.at(0.4, -27.0), K.at(5.6, -17.6), K.at(6.2, -6.0), K.at(7.2 + hf * 0.6, 9.0)], SUIT_DARK, 0.7)
        for y in (-13.0, -7.0):
            K.oval(d, K.at(4.8, y), 0.9, 0.9, SUIT_DARK)
        # A pocket square, and a pocket low on his side.
        K.poly(d, [K.at(-5.4, -24.6), K.at(-2.4, -24.2), K.at(-3.0, -26.4), K.at(-4.4, -25.4)], SHIRT)
        K.line(d, [K.at(-5.8, -24.2), K.at(-2.0, -23.8)], SUIT_DARK, 0.6)
        K.line(d, [K.at(-6.6, -3.6), K.at(-1.0, -3.0)], SUIT_DARK, 0.6)

    return K.solid(("jacket", hem_back, hem_front), shape, SUIT, detail, outline=1.3, rim=0.3, shade=0.4, shade_colour=SUIT_DARK)


def _collar():
    """The collar of his shirt, closed, and the knot of his tie."""

    def shape(d) -> None:
        K.poly(d, [K.at(-2.6, -1.0), K.at(2.0, -1.6), K.at(2.4, 2.6), K.at(-2.0, 1.8)], WHITE)
        K.poly(d, [K.at(2.0, -1.6), K.at(5.4, -1.2), K.at(5.8, 1.8), K.at(3.6, 2.8)], WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(1.6, 0.4), K.at(3.8, 0.4), K.at(3.4, 3.4), K.at(2.0, 3.4)], TIE)

    return K.solid(("collar",), shape, SHIRT, detail, outline=1.0, rim=0.0, shade=0.25, shade_colour=(196, 196, 204, 255))


NEAR_EYE = (1.4, -0.2)
FAR_EYE = (7.0, -0.4)
#: Each lens is round.
NEAR_LENS, FAR_LENS = 3.1, 2.3


def _head():
    """His head, from its middle: narrow, a high forehead, dark hair combed
    straight back and flat, a thin jaw."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, -2.6), 7.8, 9.0, WHITE)
        K.oval(d, K.at(2.4, 4.0), 5.4, 7.4, WHITE)
        K.oval(d, K.at(-1.6, -5.0), 8.0, 7.6, WHITE)
        # His nose: thin and straight.
        K.poly(d, [K.at(7.2, -0.8), K.at(9.8, 3.4), K.at(9.2, 4.6), K.at(7.0, 4.8)], WHITE)

    def detail(d) -> None:
        K.oval(d, K.at(8.4, 7.6), 2.0, 4.0, mix(SKIN, SKIN_SHADE, 0.7))
        K.poly(d, [K.at(-1.4, 3.8), K.at(1.8, 4.8), K.at(1.4, 9.2), K.at(-1.6, 8.0)], mix(SKIN, SKIN_SHADE, 0.45))
        # His hair: back from a high line that comes to a point over his
        # nose, flat to his head, short at his neck.
        K.poly(d, [K.at(20.0, -10.2), K.at(7.6, -10.2), K.at(5.4, -8.6), K.at(3.4, -9.8), K.at(0.4, -8.4), K.at(-2.4, -6.6), K.at(-3.4, -3.4),
                   K.at(-3.6, -1.6), K.at(-6.0, -1.8), K.at(-6.6, 3.0), K.at(-5.0, 4.4), K.at(-4.6, 6.4), K.at(-20.0, 6.4), K.at(-20.0, -26.0),
                   K.at(20.0, -26.0)], HAIR)
        for strand in ([(5.0, -10.6), (0.6, -11.6), (-4.4, -9.8)], [(1.4, -9.2), (-2.6, -9.4), (-6.2, -6.6)], [(-3.6, -5.4), (-6.6, -3.8)]):
            K.line(d, [K.at(x, y) for x, y in strand], HAIR_LIGHT, 0.6)
        # His ear, over his hair.
        K.oval(d, K.at(-4.8, 1.0), 2.1, 3.2, SKIN, OUTLINE, 0.6)
        K.line(d, [K.at(-5.2, -0.4), K.at(-4.2, 1.0), K.at(-5.0, 2.4)], SKIN_DEEP, 0.45)
        for (cx, cy), r in ((NEAR_EYE, NEAR_LENS), (FAR_EYE, FAR_LENS)):
            K.oval(d, K.at(cx, cy), r if r == NEAR_LENS else r * 0.86, r, LENS)
        K.line(d, [K.at(8.6, 5.0), K.at(7.0, 5.0), K.at(6.4, 4.2)], SKIN_DEEP, 0.7)
        K.line(d, [K.at(-0.8, 8.2), K.at(1.4, 10.8), K.at(4.0, 11.4)], mix(SKIN, SKIN_DEEP, 0.55), 0.6)

    return K.solid(("head",), shape, SKIN, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=SKIN_DEEP)


def _glasses():
    """Round, black and heavy."""

    def paint(d) -> None:
        K.oval(d, K.at(*NEAR_EYE), NEAR_LENS, NEAR_LENS, None, FRAME, 1.0)  # type: ignore[arg-type]
        K.oval(d, K.at(*FAR_EYE), FAR_LENS * 0.86, FAR_LENS, None, FRAME, 1.0)  # type: ignore[arg-type]
        K.line(d, [K.at(NEAR_EYE[0] + NEAR_LENS, -0.8), K.at(FAR_EYE[0] - FAR_LENS * 0.86, -0.9)], FRAME, 0.9)
        K.line(d, [K.at(NEAR_EYE[0] - NEAR_LENS, -0.8), K.at(-4.6, -0.4)], FRAME, 0.9)

    return K.piece(("glasses",), paint)


_eyes = R.make_eyes(K, (NEAR_EYE[0] + 0.3, NEAR_EYE[1] + 0.2), (FAR_EYE[0] + 0.2, FAR_EYE[1] + 0.2), ink=INK, white=None, lid=SKIN_DEEP, size=0.95)
_brows = R.make_brows(K, [(-1.4, -4.4), (1.4, -5.0), (4.2, -4.4)], [(5.8, -4.6), (7.2, -5.0), (8.6, -4.4)], HAIR, 1.0)
_mouth = R.make_mouth(K, (5.2, 8.0), (112, 54, 58, 255), wide=0.8)

G.torso = _torso
G.collar = _collar
G.neck = R.make_neck(K, SKIN_SHADE, 4.6)
G.head_layers = lambda pose: [
    (_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_glasses(), "glasses"),
    (_brows(1 if float(pose["brows"]) > 0.5 else -1 if float(pose["brows"]) < -0.5 else 0), "brows"), (_mouth(str(pose["mouth"])), "mouth"),
]
G.upper_arm = lambda near: [(0.0, 1.0, 6.8, 5.6, SUIT if near else SUIT_DARK)]
G.forearm = lambda near: [(0.0, 1.0, 5.6, 4.8, SUIT if near else SUIT_DARK)]
G.thigh = lambda near: [(0.0, 1.0, 7.2, 6.0, SUIT if near else SUIT_DARK)]
G.shin = lambda near: [(0.0, 1.0, 6.0, 5.2, SUIT if near else SUIT_DARK)]
G.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, SHIRT, (206, 206, 212, 255))
G.shoe = R.make_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up)


# ---- How he holds himself ----------------------------------------------------

P = G.P
#: One finger at the bridge of his glasses.
AT_GLASSES = (10.5, -8.5)


@G.row
def idle(i: int, n: int):
    # Very straight and very still, and then his glasses are not right.
    _, s, _c = loop(i, n)
    fix = i in (n - 3, n - 2)
    return P(hip=(0.0, 0.3 + 0.3 * s), head=(0.0, -0.2 * s, 3.0 if fix else 0.0), na=AT_GLASSES if fix else BEHIND_NEAR, nh="point" if fix else "soft",
             eyes="closed" if i == n - 2 else "open")


@G.row
def walk(i: int, n: int):
    # He walks as he stands: his hands stay behind him.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 8.0, 4.5)
    return P(hip=(0.5, 0.8 * math.cos(2.0 * ph)), lean=1.0, head=(0.0, 0.0, 1.0 * s), na=(BEHIND_NEAR[0], BEHIND_NEAR[1] + 0.5 * c),
             fa=(BEHIND_FAR[0], BEHIND_FAR[1] - 0.5 * c), nf=nf, ff=ff, hem=(1.0 + abs(c), abs(c)))


@G.row
def talk(i: int, n: int):
    # One hand, and not much of it: he states, he does not persuade.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), head=(0.3, 0.0, 2.0 * s), na=(13.0 + 2.0 * c, 6.0 - 3.0 * max(0.0, s)), nh="point" if s > 0.2 else "flat",
             mouth=("open", "flat", "o", "flat")[i % 4], brows=1.0 if s > 0.5 else 0.0)


@G.row
def interact(i: int, n: int):
    reach = P(hip=(1.5, 1.0), lean=6.0, na=(26.0, -1.0), nh="point", mouth="o", brows=1.0)
    return G.keys(shot(i, n), [(0.0, P()), (0.35, reach), (0.7, dict(reach, na=(26.0, 3.0))), (1.0, P())])


@G.row
def land_recovery(i: int, n: int):
    return G.keys(shot(i, n), [(0.0, R.HALF_UP), (1.0, P())])


@G.row
def ledge_getup(i: int, n: int):
    return G.keys(shot(i, n), [(0.0, R.PERCH), (0.6, R.HALF_UP), (1.0, P())])


#: Two fingers, held close: he fights as he argues.
GUARD = P(hip=(-1.0, 2.0), lean=1.0, na=(10.0, 7.0), fa=BEHIND_FAR, nh="point", nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), brows=-1.0)


@G.row
def jab(i: int, n: int):
    poke = dict(GUARD, hip=(3.0, 3.0), lean=10.0, na=(27.0, 0.0), ff=(10.0, 0.0, 0.0))
    return G.keys(shot(i, n), [(0.0, GUARD), (0.3, poke), (0.6, poke), (1.0, GUARD)])


@G.row
def block(i: int, n: int):
    # His arms crossed in front of him.
    _, s, _c = loop(i, n)
    return P(hip=(-2.0, 4.0 + 0.4 * s), lean=-4.0, head=(-1.0, 0.0, 6.0), na=(13.0, 1.0), fa=(8.0, 4.0), nh="fist", fh="fist", nf=(-7.0, 0.0, 0.0),
             ff=(7.0, 0.0, 0.0), brows=-1.0)


@G.row
def charge(i: int, n: int):
    # He builds the sentence: his eyes shut, a finger at his temple.
    _, s, _c = loop(i, n)
    return P(hip=(0.0, 1.0 + 0.4 * s), lean=2.0, head=(0.0, 0.0, 6.0 + s), na=(9.0, -9.0), nh="point", eyes="closed", brows=-1.0)


@G.row
def cast(i: int, n: int):
    out = P(hip=(3.0, 3.0), lean=10.0, head=(1.0, 0.0, -4.0), na=(26.0, -3.0), nh="point", nf=(-9.0, 0.0, 10.0), ff=(10.0, 0.0, 0.0), eyes="wide",
            mouth="open", brows=1.0, hem=(5.0, 1.0))
    return G.keys(shot(i, n), [(0.0, charge(0, 8)), (0.3, out), (1.0, dict(out, hip=(2.0, 3.0), lean=7.0))])


@G.row
def celebrate(i: int, n: int):
    # As pleased as he gets: one small nod, and a finger up.
    _, s, _c = loop(i, n)
    return P(hip=(0.0, 0.6 + 0.6 * s), head=(0.0, 0.0, 5.0 * max(0.0, s)), na=(11.0, -4.0 - 2.0 * max(0.0, s)), nh="point", eyes="happy" if s > 0.3 else "open",
             mouth="smile", brows=1.0)


@G.row
def taunt(i: int, n: int):
    # He looks at you over his glasses, and puts them back.
    down = P(lean=6.0, head=(1.0, 0.5, 12.0), na=(10.0, -7.0), nh="point", brows=1.0, eyes="up")
    return G.keys(shot(i, n), [(0.0, P()), (0.3, down), (0.7, down), (1.0, P(na=AT_GLASSES, nh="point"))])


# ---- His logic ---------------------------------------------------------------


def _sym(symbols, size: float, fill: RGBA = LOGIC):
    return R.glyph(K, symbols, size, fill, LOGIC_DARK)


def _loop_arrow(radius: float, turn: int):
    """The arrow that goes round and comes back: all but a gap of a circle,
    with a head, turned by ``turn`` degrees."""

    def shape(d) -> None:
        pts = [K.at(radius * math.cos(math.radians(a + turn)), radius * math.sin(math.radians(a + turn))) for a in range(20, 321, 12)]
        K.stroke(d, pts, WHITE, 1.6)
        a = math.radians(320 + turn)
        tip = K.at(radius * math.cos(a), radius * math.sin(a))
        for da, k in ((-0.55, 0.62), (0.75, 1.3)):
            K.stroke(d, [tip, (tip[0] - 4.2 * math.cos(a + math.pi / 2.0 + da) * 1.0, tip[1] - 4.2 * math.sin(a + math.pi / 2.0 + da) * 1.0)], WHITE, 1.5)
            del k

    return R.chalk(K, ("loop_arrow", radius, turn), shape, LOGIC, LOGIC_DARK)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, i, n, hand, head, hip, shoulder = ctx.anim, ctx.i, ctx.n, ctx.hand, ctx.head, ctx.hip, ctx.shoulder

    def stamp(part, p, name: str, degrees: float = 0.0) -> None:
        out.append((part, p, name, degrees))

    def sentence(centre, size: float, turn: int) -> None:
        """G, and the arrow round it."""
        stamp(_loop_arrow(size, turn), centre, "loop")
        stamp(_sym("G", size * 0.9, LOGIC_GOLD), centre, "g")

    if anim == "jab" and 1 <= i <= 3:
        stamp(_sym(["turnstile"], 7.0), (hand[0] + 18.0, hand[1] - 1.0), "turnstile")
    elif anim == "punch" and 3 <= i <= 5:
        centre = (hand[0] + 15.0, hand[1])
        stamp(R.burst(K, 8.0 + (i - 3), LOGIC, LOGIC_DARK), centre, "burst")
        stamp(_sym(["not"], 6.0, LOGIC_GOLD), centre, "not")
    elif anim in ("slash", "ledge_getup_attack"):
        lo, hi = (2, 5) if anim == "slash" else (4, 6)
        if lo <= i <= hi:
            a = math.degrees(math.atan2(hand[1] - shoulder[1], hand[0] - shoulder[0]))
            lead = int(round(a / 5.0)) * 5
            stamp(R.swoosh(K, 48.0, lead - (100 if anim == "slash" else 60), lead + 6, 7.0, LOGIC, LOGIC_DARK), shoulder, "swoosh")
            tip = math.radians(lead + 13.0)
            stamp(_sym(["turnstile"], 8.0, LOGIC_GOLD), (shoulder[0] + 53.0 * math.cos(tip), shoulder[1] + 53.0 * math.sin(tip)), "turnstile")
    elif anim == "attack_side" and 3 <= i <= 6:
        sentence((hand[0] + 19.0 + 2.0 * (i - 3), hand[1]), 8.0 + (i - 3), 45 * (i - 3))
    elif anim in ("attack_up", "air_up") and 3 <= i <= 6:
        y = hand[1] - 16.0 - 4.0 * (i - 3)
        if y > 16.0:
            sentence((hand[0] + 2.0, y), 8.0, 45 * (i - 3))
    elif anim == "attack_down" and i >= 4:
        centre = (hand[0] + 8.0, ctx.ground - 13.0)
        stamp(R.burst(K, 11.0 + min(3, i - 4), LOGIC, LOGIC_DARK, 10), centre, "burst")
        stamp(_sym("?", 9.0, LOGIC_GOLD), centre, "question")
    elif anim == "air_down" and 2 <= i <= 5:
        stamp(_sym(["not"], 7.0), (hip[0] + 1.0, ctx.ground - 8.0), "not")
    elif anim == "air_neutral":
        for k, sym in enumerate((["turnstile"], "G", ["not"])):
            a = ctx.phase + k * math.tau / 3.0
            stamp(_sym(sym, 8.0, (LOGIC, LOGIC_GOLD, LOGIC)[k]), (hip[0] + 34.0 * math.cos(a), hip[1] - 18.0 + 11.0 * math.sin(a)), f"sym_{k}")
    elif anim == "air_forward" and 2 <= i <= 4:
        stamp(R.swoosh(K, 13.0, -70, 70, 5.0, LOGIC, LOGIC_DARK), (ctx.foot[0] + 2.0, ctx.foot[1]), "swoosh")
    elif anim == "air_back" and 2 <= i <= 4:
        stamp(R.burst(K, 8.0, LOGIC, LOGIC_DARK), (ctx.foot[0] - 11.0, ctx.foot[1]), "burst")
    elif anim == "interact" and 3 <= i <= 5:
        stamp(R.tick(K, 4.0, LOGIC_GOLD, LOGIC_DARK), (hand[0] + 16.0, hand[1] - 5.0), "tick")
    elif anim == "charge":
        sentence((head[0] - 2.0, head[1] - 31.0), 6.0 + min(4, i) * 0.75, 45 * i)
    elif anim == "cast":
        if i < 2:
            sentence((head[0] - 2.0 + 12.0 * i, head[1] - 31.0 + 10.0 * i), 9.0, 45 * i)
        else:
            go = (i - 2) / max(1, n - 3)
            sentence((hand[0] + 20.0 + 8.0 * go, hand[1] - 2.0), 9.0 + round(4.0 * go), 45 * i)
    elif anim == "celebrate" and i >= 2:
        stamp(_sym(["turnstile"], 7.0, LOGIC_GOLD), (head[0] + 15.0, head[1] - 21.0), "turnstile")
    elif anim == "taunt" and 0.3 <= ctx.u <= 0.7:
        stamp(_sym("?", 7.0), (head[0] + 17.0, head[1] - 17.0), "question")
    elif anim == "death" and i >= n - 2:
        stamp(_sym(["not"], 6.0), (head[0] + 3.0, head[1] - 17.0 - 3.0 * (i - (n - 2))), "not")
    return out


G.effects = _effects

# ---- From the front ------------------------------------------------------------

FRONT_TOP = BUILD.neck[1] - 2.0


def _front_suit(d) -> None:
    """His suit from the front: the waistcoat and the shirt where the jacket
    is open, his tie, and a lapel each side."""
    K.poly(d, [K.at(-4.6, FRONT_TOP), K.at(4.6, FRONT_TOP), K.at(5.4, 9.0), K.at(-5.4, 9.0)], VEST)
    K.poly(d, [K.at(-3.0, FRONT_TOP - 1.0), K.at(3.0, FRONT_TOP - 1.0), K.at(0.0, -27.0)], SHIRT)
    K.poly(d, [K.at(-1.0, FRONT_TOP + 0.6), K.at(1.0, FRONT_TOP + 0.6), K.at(1.2, -24.0), K.at(0.0, -22.6), K.at(-1.2, -24.0)], TIE)
    for y in (-18.0, -12.0, -6.0):
        K.oval(d, K.at(0.0, y), 0.7, 0.7, SUIT_DARK)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(4.6 * sx, FRONT_TOP), K.at(7.2 * sx, FRONT_TOP + 1.0), K.at(5.4 * sx, -19.0)], SUIT_LIGHT)
        K.line(d, [K.at(5.4 * sx, -19.0), K.at(5.4 * sx, 9.0)], SUIT_DARK, 0.7)
        K.line(d, [K.at(9.6 * sx, -3.0), K.at(6.6 * sx, -2.6)], SUIT_DARK, 0.7)


def _front_hair_shape(d) -> None:
    K.oval(d, K.at(0.0, -6.0), 9.2, 7.0, WHITE)


def _front_hair(d) -> None:
    # Flat to his head, parted at one side, off a high forehead.
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -2.0), K.at(7.8, -2.0), K.at(7.2, -6.6), K.at(4.0, -9.0), K.at(-2.0, -9.6), K.at(-5.6, -8.0),
               K.at(-7.6, -5.0), K.at(-7.8, -2.0), K.at(-20.0, -2.0)], HAIR)
    K.line(d, [K.at(-4.0, -12.6), K.at(-3.0, -9.4)], SKIN_SHADE, 0.5)
    for strand in ([(-2.0, -12.0), (2.0, -12.4), (6.0, -10.0)], [(-7.0, -8.0), (-6.4, -4.0)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_LIGHT, 0.6)


def _front_glasses(d) -> None:
    # Round, black and heavy; and a thin nose under them.
    for sx in (-1.0, 1.0):
        K.oval(d, K.at(3.4 * sx, -0.6), 3.0, 3.0, LENS, FRAME, 1.0)
        K.line(d, [K.at(6.4 * sx, -0.8), K.at(8.4 * sx, -1.4)], FRAME, 0.9)
    K.line(d, [K.at(-0.5, -0.8), K.at(0.5, -0.8)], FRAME, 0.9)
    K.line(d, [K.at(-0.3, 0.6), K.at(-1.2, 4.0), K.at(0.0, 4.8), K.at(1.2, 4.0)], SKIN_DEEP, 0.6)


G.front_torso = R.make_front_torso(K, ("girdle",), SUIT, SUIT_DARK, [(FRONT_TOP, 4.2), (FRONT_TOP + 3.6, 9.2), (-24.0, 9.8), (-6.0, 9.6), (9.0, 10.2)],
                                   shoulder=(7.4, -31.4, 4.4, 4.8), detail=_front_suit)
G.front_head_layers = R.front_face(R.make_front_head(K, ("girdle",), SKIN, SKIN_DEEP, wide=7.8, jaw=6.0, chin=4.4, ears=SKIN, shape=_front_hair_shape,
                                                    hair=_front_hair, face=_front_glasses),
                                   R.make_front_eyes(K, ("girdle",), white=None, ink=INK, spread=3.4, y=-0.6, size=0.9),
                                   R.make_front_brows(K, ("girdle",), HAIR, spread=3.4, y=-4.6, width=1.0), R.make_front_mouth(K, ("girdle",), y=8.8, colour=(112, 54, 58, 255),
                                                                                                                         wide=0.7))
G.front_shoe = R.make_front_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up)
G.front_span = (8.2, 4.6)
R.add_front_rows(G, hands="sides")

ROWS = G.rows


def _render_frame(anim: str, frame_idx: int, nframes: int):
    return G.render_frame(anim, frame_idx, nframes)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return G.render(out_dir, ACTOR_METADATA)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Girdle spritesheet.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
