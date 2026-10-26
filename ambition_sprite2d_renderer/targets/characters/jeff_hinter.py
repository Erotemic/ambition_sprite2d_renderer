"""Sprite generator for Jeff Hinter: the man who gives you a hint, and then the
dimension you are missing.

An affectionate caricature of Geoffrey Hinton.

The look (2026-10-13): the man when he was young, seen three quarters from
the front, facing right. Tall and thin. A mop of dark hair, going grey, that is not
combed: it falls on his forehead to his brows and over the top of his ear. A
long face with no beard and no glasses, dark brows, a strong nose, a small
dry smile. A dark blue jumper with the collar of his shirt over its neck, and
grey trousers. He stands straight, with his arms loose at his sides, and he
looks at something that is not in the room.

Jon, 2026-10-13, of the draft before this one (white hair combed over, thin
glasses, a blazer, bent from the hips with his hands behind him): "Hinter
needs to be less like an old man. Let's try to get more of his look when he
was younger."

He is drawn from the man and not from a type (Jon, 2026-10-13, of another
person of this cast: "needs to read like paul erdos not bearnie sanders"). He
is a grown man, not a mascot. He holds nothing; there is no drop shadow.

What he shows: points in a plane that fall into their groups; the number he
shouts (14, or 3 when the game has only two dimensions and he wants one
more); and the surface he wraps round himself.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, how he stands and what he shows are his. The
sheet ``jeff_hinter_armored`` is this person in his armor: his other side.
"""

from __future__ import annotations

import math
from typing import List

from PIL import Image, ImageChops, ImageFilter

from ._ai_era_kit import OUTLINE, WHITE, RGBA, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "jeff_hinter"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Jeff Hinter"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_jeff_hinter", "display_name": "Jeff Hinter"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": ["story", "humanoid", "scholar", "hint_npc", "ai_history", "manifold_armor"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": None,
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
    "tags": ["story", "humanoid", "scholar", "hint_npc", "ai_history", "manifold_armor"],
    "sockets": {
        "head": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 70.0, "y": 43.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 72.0, "y": 91.0},
        },
        "hand_l": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 52.0, "y": 105.0},
        },
        "hand_r": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 94.0, "y": 101.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 72.0, "y": 10.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "interaction.hint": {"animation": "hint", "events": []},
        "emote.visualize_2d": {"animation": "visualize_2d", "events": []},
        "emote.shout_14": {"animation": "shout_14", "events": []},
        "emote.shout_3": {"animation": "shout_3", "events": []},
        "ability.manifold_shrinkwrap": {"animation": "manifold_shrinkwrap", "events": []},
        "defense.block": {"animation": "block", "events": []},
    },
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Jeff Hinter is an affectionate caricature of Geoffrey Hinton, recast as an "
            "overenthusiastic hint NPC. He thinks in representations, dimensions, optimization "
            "landscapes, and manifold geometry, but is liable to shout the missing dimension before "
            "noticing that the game remains stubbornly two-dimensional."
        ),
        "gameplay_description": (
            "Use as a hint giver, machine-learning sage, comic lecturer, or transformation-capable "
            "support character. His hints should become useful before they become lectures; his "
            "special effects should project, compress, optimize, and occasionally lose something "
            "important."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'THREE! ...No. Still two-dimensional.',
        'A hint should become useful before it becomes a lecture.',
        'I projected away something important, usually a ladder.',
    ],
)

BLAZER: RGBA = (52, 82, 124, 255)
BLAZER_DARK: RGBA = (34, 54, 92, 255)
BLAZER_LIGHT: RGBA = (92, 126, 170, 255)
PULLOVER: RGBA = (86, 124, 172, 255)
PULLOVER_DARK: RGBA = (58, 86, 130, 255)
SHIRT: RGBA = (244, 242, 236, 255)
TROUSER: RGBA = (128, 130, 142, 255)
TROUSER_DARK: RGBA = (88, 90, 106, 255)
SHOE: RGBA = (70, 52, 46, 255)
SHOE_DARK: RGBA = (40, 30, 30, 255)
SKIN: RGBA = (240, 208, 190, 255)
SKIN_SHADE: RGBA = (212, 170, 156, 255)
SKIN_DEEP: RGBA = (168, 114, 108, 255)
HAIR: RGBA = (98, 90, 90, 255)
HAIR_SHADE: RGBA = (164, 160, 164, 255)
FRAME: RGBA = (96, 100, 116, 255)
LENS: RGBA = (232, 244, 250, 150)
INK: RGBA = (28, 24, 32, 255)
NET: RGBA = (130, 236, 222, 255)
NET_DARK: RGBA = (40, 130, 140, 255)
HOT: RGBA = (255, 206, 110, 255)
HOT_DARK: RGBA = (214, 120, 50, 255)
ROSE: RGBA = (250, 150, 170, 255)
VIOLET: RGBA = (186, 160, 250, 255)

#: Tall and thin, 178 cm.
BUILD = Build(hip_up=52.0, thigh=25.2, shin=24.0, neck=(0.6, -37.0), upper=20.4, fore=19.4, near_shoulder=(-3.6, -32.8), far_shoulder=(5.2, -32.4),
              near_hip=(-3.4, 0.0), far_hip=(3.4, 0.0), head_up=(0.8, -12.8), height=114.0, half_width=(12.5, 14.5))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0


def _front(d, hb: float, hf: float) -> None:
    """His jumper: the collar of his shirt over its neck, and the rib at its
    hem."""
    K.poly(d, [K.at(4.6, TOP - 1.0), K.at(8.2, TOP - 1.0), K.at(6.4, TOP + 3.6)], SKIN_SHADE)
    K.poly(d, [K.at(1.6, TOP - 1.4), K.at(5.0, TOP - 1.0), K.at(5.4, TOP + 4.8), K.at(1.8, TOP + 2.6)], SHIRT)
    K.poly(d, [K.at(7.8, TOP - 1.0), K.at(10.6, TOP - 1.0), K.at(9.6, TOP + 3.6), K.at(7.2, TOP + 4.6)], SHIRT)
    K.line(d, [K.at(1.8, TOP + 2.6), K.at(5.4, TOP + 4.8), K.at(7.2, TOP + 4.6), K.at(9.6, TOP + 3.6)], BLAZER_DARK, 0.6)
    K.line(d, [K.at(-8.6, 1.6), K.at(9.4 + hf, 1.8)], BLAZER_DARK, 0.7)
    for x in (-5.0, -1.0, 3.0, 7.0):
        K.line(d, [K.at(x, 2.4), K.at(x, 4.6)], BLAZER_DARK, 0.5)
    K.line(d, [K.at(2.0, -24.0), K.at(3.4, -12.0), K.at(3.0, -2.0)], BLAZER_LIGHT, 0.5)


# His chest is flat: the front edge is a straight line from his collar to
# his belt, and the far shoulder does not come past it. His back is straight
# too: the near shoulder is inside the line of his back, and his head is over
# his hips (Jon, 2026-10-13: "he shouldn't have a humped back like erdish").
X.torso = R.make_torso(K, ("hinter",), BLAZER, BLAZER_DARK, back=(7.4, 8.0, 7.8, 9.0), front=(7.8, 8.4, 8.6, 9.2), hem_y=5.0, top=TOP,
                       shoulders=((-3.4, -32.4), (4.2, -32.4)), shoulder_r=(4.2, 3.8), shade_from=40.0, detail=_front)

NEAR_EYE = (1.6, -0.6)
FAR_EYE = (7.0, -0.8)


def _hair_shape(d) -> None:
    # A mop: full on top, forward over his brow, and shaggy at his nape.
    K.oval(d, K.at(-0.8, -6.6), 9.6, 7.8, WHITE)
    K.poly(d, [K.at(4.0, -13.0), K.at(9.4, -9.6), K.at(9.6, -6.4), K.at(6.0, -6.0)], WHITE)
    K.poly(d, [K.at(-8.0, -6.0), K.at(-10.8, -2.0), K.at(-9.0, 0.6), K.at(-10.4, 4.0), K.at(-7.6, 5.0), K.at(-6.6, 8.0), K.at(-3.6, 6.6)], WHITE)


def _hair(d) -> None:
    # It falls to his brows in locks, and over the top of his ear.
    K.poly(d, [K.at(20.0, -7.2), K.at(9.4, -7.2), K.at(8.2, -5.4), K.at(6.6, -6.8), K.at(4.8, -4.9), K.at(2.8, -6.6), K.at(0.8, -4.6), K.at(-1.0, -5.6),
               K.at(-2.4, -2.6), K.at(-2.2, 0.6), K.at(-3.8, 1.4), K.at(-5.0, 0.2), K.at(-6.4, 3.4), K.at(-5.0, 4.8), K.at(-4.2, 7.2), K.at(-20.0, 9.0),
               K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
    for strand in ([(-3.0, -13.0), (2.0, -11.6), (6.6, -8.0)], [(-6.0, -11.0), (-1.0, -9.6), (2.8, -7.0)], [(-8.0, -6.0), (-5.6, -4.0), (-3.6, -0.6)],
                   [(-8.6, -1.0), (-8.0, 3.0)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_SHADE, 0.6)


def _face(d) -> None:
    # A long cheek, and no more: he is not old.
    K.line(d, [K.at(4.6, 4.6), K.at(3.2, 6.6)], mix(SKIN, SKIN_DEEP, 0.3), 0.45)


_head = R.make_head(K, ("hinter",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.8, 7.8, 9.4), jaw=(2.6, 4.2, 5.2, 7.8),
                    nose=((7.2, -1.2), (10.0, 2.8), (9.4, 4.4), (7.2, 4.8)), ear=(-5.0, 1.0, 2.2, 3.3), shape=_hair_shape, under=_hair, over=_face)
_eyes = R.make_eyes(K, (NEAR_EYE[0] + 0.2, NEAR_EYE[1] + 0.2), (FAR_EYE[0] + 0.1, FAR_EYE[1] + 0.2), ink=INK, white=None, lid=SKIN_DEEP, size=1.0)
_brows = R.make_brows(K, [(-0.8, -3.6), (1.8, -4.2), (4.4, -3.6)], [(5.8, -3.8), (7.2, -4.2), (8.6, -3.6)], HAIR, 1.3)
_mouth = R.make_mouth(K, (5.4, 8.4), (124, 60, 62, 255), wide=0.85)

X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"),
                              (_mouth(str(pose["mouth"])), "mouth")]
X.neck = R.make_neck(K, SKIN_SHADE, 4.4)
X.upper_arm = lambda near: [(0.0, 1.0, 6.6, 5.6, BLAZER if near else BLAZER_DARK)]
X.forearm = lambda near: [(0.0, 1.0, 5.6, 4.8, BLAZER if near else BLAZER_DARK)]
X.thigh = lambda near: [(0.0, 1.0, 7.0, 5.8, TROUSER if near else TROUSER_DARK)]
X.shin = lambda near: [(0.0, 1.0, 5.8, 5.0, TROUSER if near else TROUSER_DARK)]
X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, PULLOVER, PULLOVER_DARK, size=1.05)
X.shoe = R.make_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up, long=1.05)

# ---- How he holds himself ----------------------------------------------------

BEHIND_NEAR = (-5.5, 23.5)
BEHIND_FAR = (-5.0, 23.5)
X.set_rest(lean=0.0, nf=(-3.8, 0.0, 0.0), ff=(4.8, 0.0, 0.0))


@X.row
def idle(i: int, n: int):
    # His arms loose, and his eyes on a space with more room in it.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 + 0.3 * s), lean=0.4 * s, head=(0.3, 0.0, -6.0 + 3.0 * c), eyes="closed" if i == n - 2 else "up" if c < 0.2 else "open",
             mouth="smile" if c < -0.4 else "flat")


@X.row
def walk(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 8.6, 4.6)
    swing = 7.0 * math.sin(ph)
    return P(hip=(0.5, 0.8 * math.cos(2.0 * ph)), lean=2.5, head=(0.3, 0.0, -2.0 + 1.5 * s), nf=nf, ff=ff, hem=(1.0 + abs(c), abs(c)),
             na=(R.REST["na"][0] - swing, R.REST["na"][1] - abs(swing) * 0.2), fa=(R.REST["fa"][0] + swing, R.REST["fa"][1] - abs(swing) * 0.2))


@X.row
def talk(i: int, n: int):
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), lean=1.5, head=(0.4, 0.0, 2.0 * s), na=(14.0 + 3.0 * c, 6.0 - 5.0 * max(0.0, s)), nh="open", mouth=("open", "smile", "big", "smile")[i % 4],
             brows=1.0 if s > 0.3 else 0.0)


@X.row
def interact(i: int, n: int):
    reach = P(hip=(1.5, 1.0), lean=10.0, na=(26.0, -1.0), nh="point", mouth="o", brows=1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.35, reach), (0.7, dict(reach, na=(26.0, 3.0))), (1.0, P())])


@X.row
def hint(i: int, n: int):
    # He comes close, one finger up, and says the useful part first.
    lean_in = P(hip=(2.0, 1.5), lean=14.0, head=(1.0, 0.0, 4.0), na=(12.0, -9.0), nh="point", mouth="open", brows=1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.3, lean_in), (0.6, dict(lean_in, na=(12.0, -11.0), mouth="smile")), (0.85, dict(lean_in, mouth="open")), (1.0, P())])


#: Both hands held out, flat, a little apart: this is the plane.
PLANE = P(lean=6.0, head=(0.5, 0.0, 6.0), na=(17.0, 4.0), fa=(19.0, 9.0), nh="flat", fh="flat", brows=-1.0, mouth="flat")


@X.row
def visualize_2d(i: int, n: int):
    _, s, _c = loop(i, n)
    return X.keys(shot(i, n), [(0.0, P()), (0.2, PLANE), (0.8, dict(PLANE, na=(17.0, 3.0 + s))), (1.0, dict(PLANE, eyes="happy", mouth="smile", brows=1.0))])


#: All of him goes up with the number.
SHOUT = P(hip=(0.0, -1.0), lean=-6.0, head=(0.0, 0.0, -14.0), na=(-10.0, -24.0), nab=-1.0, fa=(17.0, -22.0), nh="open", fh="open", eyes="wide", mouth="big", brows=1.0,
          nf=(-5.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0))


@X.row
def shout_14(i: int, n: int):
    wind = P(hip=(0.0, 3.0), lean=12.0, na=(6.0, 14.0), fa=(9.0, 13.0), nh="fist", fh="fist", eyes="closed", brows=-1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.2, wind), (0.4, SHOUT), (0.85, SHOUT), (1.0, P(mouth="smile"))])


@X.row
def shout_3(i: int, n: int):
    # He shouts for the third dimension. It does not come.
    wind = P(hip=(0.0, 3.0), lean=12.0, na=(6.0, 14.0), fa=(9.0, 13.0), nh="fist", fh="fist", eyes="closed", brows=-1.0)
    flat = P(hip=(0.0, 1.0), lean=8.0, head=(0.5, 0.5, 10.0), na=(8.0, 20.0), fa=(10.0, 19.0), nh="open", fh="open", mouth="flat", brows=1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.2, wind), (0.35, SHOUT), (0.6, SHOUT), (0.8, flat), (1.0, flat)])


#: Set, his arms a little out from him and his eyes shut: the surface closes
#: on the shape he holds.
WRAPPED = P(hip=(0.0, 1.5), lean=0.0, head=(0.0, 0.0, -4.0), na=(-9.0, 18.0), fa=(13.0, 17.0), nh="open", fh="open", eyes="closed", brows=-1.0, mouth="flat",
            nf=(-5.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0))


@X.row
def manifold_shrinkwrap(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, P()), (0.25, WRAPPED), (0.85, WRAPPED), (1.0, P())])


X.alias(block="manifold_shrinkwrap", taunt="shout_14")
X.rows = [("idle", 8, 145), ("walk", 8, 105), ("talk", 8, 108), ("interact", 10, 92), ("hint", 10, 92), ("visualize_2d", 12, 92), ("shout_14", 12, 78),
          ("shout_3", 12, 78), ("manifold_shrinkwrap", 16, 82), ("block", 16, 82), ("taunt", 12, 78)]

# ---- From the front ------------------------------------------------------------


def _front_jumper(d) -> None:
    """His jumper from the front: the two points of his collar, and the rib
    at its hem."""
    K.poly(d, [K.at(-2.6, TOP - 1.0), K.at(2.6, TOP - 1.0), K.at(0.0, TOP + 4.0)], SKIN_SHADE)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(0.8 * sx, TOP + 1.0), K.at(5.2 * sx, TOP - 0.8), K.at(3.8 * sx, TOP + 5.4)], SHIRT)
    K.line(d, [K.at(-3.8, TOP + 5.4), K.at(0.0, TOP + 3.6), K.at(3.8, TOP + 5.4)], BLAZER_DARK, 0.6)
    K.line(d, [K.at(-10.0, 1.6), K.at(10.0, 1.6)], BLAZER_DARK, 0.7)
    for x in (-7.0, -3.5, 0.0, 3.5, 7.0):
        K.line(d, [K.at(x, 2.4), K.at(x, 4.6)], BLAZER_DARK, 0.5)
    for sx in (-1.0, 1.0):
        K.line(d, [K.at(7.0 * sx, -26.0), K.at(7.6 * sx, -6.0)], BLAZER_DARK, 0.5)


def _front_hair_shape(d) -> None:
    K.oval(d, K.at(0.0, -6.2), 10.2, 8.2, WHITE)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(8.0 * sx, -6.0), K.at(10.8 * sx, -2.0), K.at(9.4 * sx, 2.6), K.at(7.4 * sx, 3.6)], WHITE)


def _front_hair(d) -> None:
    # The mop: it falls on his forehead in locks, and over the top of each ear.
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 3.6), K.at(7.6, 3.6), K.at(7.8, -2.0), K.at(6.4, -5.2), K.at(4.6, -6.6), K.at(3.0, -4.9), K.at(1.2, -6.6),
               K.at(-0.8, -4.7), K.at(-2.8, -6.6), K.at(-4.8, -5.0), K.at(-6.4, -5.4), K.at(-7.8, -2.0), K.at(-7.6, 3.6), K.at(-20.0, 3.6)], HAIR)
    for strand in ([(-6.0, -11.0), (-2.0, -12.6), (3.0, -11.6)], [(-3.0, -9.0), (1.0, -10.0), (5.6, -8.0)], [(-8.6, -4.0), (-8.4, 1.0)], [(8.6, -4.0), (8.4, 1.0)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_SHADE, 0.6)


def _front_nose(d) -> None:
    K.line(d, [K.at(-0.4, -0.6), K.at(-1.6, 3.8), K.at(0.0, 4.8), K.at(1.6, 3.8)], SKIN_DEEP, 0.7)
    K.line(d, [K.at(-2.6, 11.4), K.at(0.0, 12.0), K.at(2.6, 11.4)], mix(SKIN, SKIN_DEEP, 0.4), 0.5)


FRONT_HEAD = R.make_front_head(K, ("hinter",), SKIN, SKIN_DEEP, wide=8.2, jaw=6.4, chin=4.6, ears=SKIN, shape=_front_hair_shape, hair=_front_hair, face=_front_nose)
FRONT_EYES = R.make_front_eyes(K, ("hinter",), white=None, ink=INK, spread=3.4)
FRONT_BROWS = R.make_front_brows(K, ("hinter",), HAIR, spread=3.4, y=-3.4)
FRONT_MOUTH = R.make_front_mouth(K, ("hinter",), y=8.8, colour=(124, 60, 62, 255), wide=0.85)
X.front_torso = R.make_front_torso(K, ("hinter",), BLAZER, BLAZER_DARK, [(TOP, 4.2), (TOP + 3.6, 9.0), (-24.0, 9.6), (-6.0, 9.2), (5.0, 9.6)],
                                   shoulder=(7.4, -32.8, 4.2, 4.6), detail=_front_jumper)
X.front_head_layers = R.front_face(FRONT_HEAD, FRONT_EYES, FRONT_BROWS, FRONT_MOUTH)
X.front_shoe = R.make_front_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up)
X.front_span = (8.2, 4.6)
R.add_front_rows(X, hands="sides")

# ---- What he shows -----------------------------------------------------------

#: Points in his plane: where each is, and which group it falls into.
POINTS = ((-9.0, -5.0, 0), (-6.0, -8.0, 0), (-10.0, -9.0, 0), (5.0, -9.0, 1), (9.0, -6.0, 1), (7.0, -11.0, 1), (0.0, 4.0, 2), (-3.0, 7.0, 2), (3.0, 8.0, 2),
          (-4.0, -1.0, 0), (6.0, -3.0, 1), (1.0, 9.0, 2))
GROUP = (NET, HOT, ROSE)


def _scatter(count: int, sorted_: bool):
    """His plane with ``count`` points on it. Before they are sorted they are
    one colour."""

    def paint(d) -> None:
        K.line(d, [K.at(-13.0, 12.0), K.at(13.0, 12.0)], NET_DARK, 1.0)
        K.line(d, [K.at(-13.0, 12.0), K.at(-13.0, -13.0)], NET_DARK, 1.0)
        for x, y, g in POINTS[:count]:
            K.oval(d, K.at(x, y), 2.1, 2.1, OUTLINE)
            K.oval(d, K.at(x, y), 1.3, 1.3, GROUP[g] if sorted_ else VIOLET)

    return K.aligned(("scatter", count, sorted_), paint)


# ---- The surface that fits him ---------------------------------------------------
#
# His surface is a manifold that is fitted to him as he fits a network to its
# data (Jon, 2026-10-13: "a manifold shrinkwrapping over to 'fit' his body.
# This is a play on how he imagines neural networks fitting the data"). It
# starts as a smooth shape that is near him and wrong: his arms are outside
# it. Step by step it closes on his outline, and the lines between it and him
# (what is still wrong) get short and go.

#: While this is set a frame is drawn with nothing shown over the person: the
#: outline of the body is read from it.
_BARE = [False]
_OUTLINES: dict = {}
_SURFACES: dict = {}
GLOW = (214, 252, 246)


def outline_of(person, anim: str, i: int, n: int) -> Image.Image:
    """Where the body of ``person`` is in this frame: a mask of the frame."""
    key = (person.target, anim, i, n)
    if key not in _OUTLINES:
        _BARE[0] = True
        try:
            frame = Person.render_frame(person, anim, i, n)
        finally:
            _BARE[0] = False
        _OUTLINES[key] = frame.getchannel("A").point(lambda a: 255 if a > 40 else 0)
    return _OUTLINES[key]


def warm_outlines(person, rows) -> None:
    """Read the outline of each frame of ``rows`` now. A module calls this
    before it publishes: a part flipbook records each part a frame places,
    and the frame an outline is read from must not be one of them."""
    for name, frames, _ms in person.rows:
        if name in rows:
            for i in range(frames):
                outline_of(person, name, i, frames)


def manifold(ctx, fit: float, show: float = 1.0, solid: float = 1.0) -> List[Stamp]:
    """The surface at ``fit`` of the way to his outline (0 is the first
    guess, 1 is on him). ``show`` is how much of it is seen, and ``solid`` is
    how much of him it hides when it is on him."""
    if show <= 0.02:
        return []
    person, K = ctx.person, ctx.person.K
    fit = max(0.0, min(1.0, fit))
    key = (person.target, ctx.anim, ctx.i, ctx.n, round(fit, 3), round(show, 2), round(solid, 2))
    if key not in _SURFACES:
        body = outline_of(person, ctx.anim, ctx.i, ctx.n)
        size = body.size
        loose = 18.0 * (1.0 - fit) ** 1.6
        if loose > 0.4:
            guess = body.filter(ImageFilter.GaussianBlur(loose)).point(lambda a: 255 if a > 14 else 0)
            # A step of the fit takes in a part of what was outside it.
            reach = body.filter(ImageFilter.GaussianBlur(1.0 + loose * 0.25)).point(lambda a: 255 if a > 255 * (1.0 - fit) ** 0.5 * 0.9 + 12 else 0)
            blob = ImageChops.lighter(guess, reach)
            blob = blob.filter(ImageFilter.GaussianBlur(1.2)).point(lambda a: 255 if a > 127 else 0)
            # It stands on the floor he stands on, and it stays in the cell.
            floor = int(person.ground) + 3
            blob.paste(0, (0, floor, size[0], size[1]))
            blob.paste(0, (0, 0, size[0], 3))
            blob = ImageChops.lighter(blob, body)
        else:
            blob = body
        inner = blob.filter(ImageFilter.MinFilter(3))
        edge = ImageChops.subtract(blob, inner)
        rim = ImageChops.subtract(blob.filter(ImageFilter.MaxFilter(3)), blob)
        lattice = Image.new("L", size, 0)
        ox, oy = int(round(ctx.hip[0])) % 7, int(round(ctx.hip[1])) % 7
        for x in range(ox, size[0], 7):
            lattice.paste(255, (x, 0, x + 1, size[1]))
        for y in range(oy, size[1], 7):
            lattice.paste(255, (0, y, size[0], y + 1))
        out = Image.new("RGBA", size, (0, 0, 0, 0))

        def lay(colour, mask, alpha: float) -> None:
            layer = Image.new("RGBA", size, tuple(colour[:3]) + (255,))
            layer.putalpha(mask.point(lambda v: int(v * max(0.0, min(1.0, alpha)))))
            out.alpha_composite(layer)

        lay(GLOW, blob, show * (0.22 + (solid - 0.22) * fit ** 2))
        lay(NET_DARK, ImageChops.multiply(lattice, inner), show * 0.8)
        lay(OUTLINE, rim, show * 0.85)
        lay(NET, edge, show)
        # What is still wrong: from his outline to the surface, on rays from
        # the middle of him.
        box = body.getbbox()
        if box is not None and fit < 0.97:
            cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
            b_px, s_px = body.load(), blob.load()
            for k in range(14):
                a = math.radians(k * 360.0 / 14.0 + 11.0)
                dx, dy = math.cos(a), math.sin(a)
                at_body = at_blob = 0
                for r in range(0, 130):
                    x, y = int(cx + dx * r), int(cy + dy * r)
                    if not (0 <= x < size[0] and 0 <= y < size[1]):
                        break
                    if b_px[x, y]:
                        at_body = r
                    if s_px[x, y]:
                        at_blob = r
                lo, hi = sorted((at_body, at_blob))
                if hi - lo >= 4:
                    for r in range(lo, hi):
                        out.putpixel((int(cx + dx * r), int(cy + dy * r)), HOT[:3] + (int(230 * show),))
                    x, y = int(cx + dx * at_body), int(cy + dy * at_body)
                    for px in ((x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)):
                        if 0 <= px[0] < size[0] and 0 <= px[1] < size[1]:
                            out.putpixel(px, HOT_DARK[:3] + (int(255 * show),))
        cut = out.getbbox()
        if cut is None:
            _SURFACES[key] = None
        else:
            s = K.scale
            big = out.crop(cut).resize(((cut[2] - cut[0]) * s, (cut[3] - cut[1]) * s), Image.Resampling.NEAREST)
            _SURFACES[key] = ((big, (0.0, 0.0)), (float(cut[0]), float(cut[1])))
    found = _SURFACES[key]
    return [] if found is None else [(found[0], found[1], "manifold", 0.0)]


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    if _BARE[0]:
        return out
    anim, i, n, u = ctx.anim, ctx.i, ctx.n, ctx.u
    if anim == "hint" and 0.3 <= u <= 0.85:
        out.append((R.glyph(K, "!", 9.0, HOT, HOT_DARK), (ctx.hand[0] + 6.0, ctx.hand[1] - 17.0), "hint", 0.0))
    elif anim == "visualize_2d" and u >= 0.2:
        count = min(len(POINTS), int((u - 0.2) / 0.5 * len(POINTS)) + 1)
        mid = ((ctx.hand[0] + ctx.far_hand[0]) / 2.0 + 16.0, ctx.hand[1] - 16.0)
        out.append((_scatter(count, u > 0.75), pin(mid), "scatter", 0.0))
    elif anim in ("shout_14", "taunt") and 0.35 <= u <= 0.9:
        size = 15.0 + (2.0 if i % 2 else 0.0)
        out.append((R.glyph(K, "14", size, HOT, HOT_DARK, width=3.0), (ctx.head[0] + 6.0, ctx.head[1] - 34.0), "fourteen", 0.0))
        out.append((R.burst(K, 9.0, HOT, HOT_DARK), (ctx.head[0] + 30.0, ctx.head[1] - 22.0), "burst", 0.0))
    elif anim == "shout_3":
        if 0.3 <= u <= 0.65:
            out.append((R.glyph(K, "3", 16.0, NET, NET_DARK, width=3.0), (ctx.head[0] + 6.0, ctx.head[1] - 34.0), "three", 0.0))
        elif u > 0.65:
            # It is still two.
            out.append((R.glyph(K, "2", 10.0, VIOLET, (96, 70, 170, 255)), (ctx.head[0] + 16.0, ctx.head[1] - 22.0 + 6.0 * (u - 0.65) / 0.35), "two", 0.0))
    elif anim in ("manifold_shrinkwrap", "block") and u >= 0.1:
        # It closes on him, holds, and lets go.
        out.extend(manifold(ctx, (u - 0.1) / 0.42, show=min(1.0, (1.0 - u) / 0.12), solid=0.8))
    elif anim == "interact" and 0.35 <= u <= 0.7:
        out.append((R.tick(K, 4.0, NET, NET_DARK), (ctx.hand[0] + 16.0, ctx.hand[1] - 5.0), "tick", 0.0))
    del n
    return out


X.effects = _effects

ROWS = X.rows
_render_frame = X.render_frame
_publish, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render(out_dir, **opts):
    warm_outlines(X, ("manifold_shrinkwrap", "block"))
    return _publish(out_dir, **opts)



# ---- In the round (``_round_cast``) --------------------------------------------
#
# His trunk and head in 3D come from the numbers of his own makers
# (``auto_trunk``, ``auto_head``); what they do not say is here, as data.
# His rows do not use this.

import numpy as np  # noqa: E402

from . import _person_round as O  # noqa: E402
from . import _round_cast as C  # noqa: E402
from . import _round_wear as W  # noqa: E402


#: His hair on the volume over his head: lighter strands in the grey.
_MOP = ((0.0, -5.0, -0.4), (8.6, 7.6, 8.6))

ROUND = C.Round(
    DISPLAY_NAME, C.PersonBody(X),
    C.Look(
        # A mop of dark hair going grey: on his forehead to his brows, over
        # the top of his ears, down to his collar behind; no glasses.
        C.auto_head(X, _head, _eyes,
                    hair=lambda u, v: (v < -4.9 + 1.0 * np.clip(np.abs(u) / 60.0, 0.0, 1.0)) | ((np.abs(u) > 65.0) & (v < 3.6))
                    | ((np.abs(u) > 100.0) & (v < 9.0)),
                    hair_colour=HAIR, hair_shade=HAIR_SHADE, volumes=[_MOP],
                    lines=[O.curve([O.on_ellipsoid(*_MOP, u + 20.0 * t, -11.6 + 4.0 * t, 0.2)[0] for t in (0.0, 0.5, 1.0)], HAIR_SHADE, 0.6)
                           for u in (-150.0, -100.0, -50.0, 0.0, 50.0, 100.0)]),
        # His jumper, the collar of his shirt over its neck, the rib at its hem.
        C.auto_trunk(X, [W.Neckline(TOP - 1.0, TOP + 3.6, 14.0, SKIN_SHADE), W.Patch(-34.0, -6.0, TOP - 1.4, TOP + 4.6, SHIRT),
                         W.Patch(6.0, 34.0, TOP - 1.4, TOP + 4.6, SHIRT), W.Across(-180.0, 180.0, 1.6, BLAZER_DARK, width=0.4)])),
    # Straight, his arms loose at his sides.
    C.Stance(hands={"r": C.Hand(l=-9.4, pole=(-0.4, 0.0, -1.0)), "l": C.Hand(l=9.4, pole=(0.4, 0.0, -1.0))}, stagger=2.0))


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
