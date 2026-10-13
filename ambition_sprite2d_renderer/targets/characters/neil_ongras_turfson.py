"""Sprite generator for Neil onGras Turfson: the astrophysicist who audits your
jump, and then touches grass.

A pun-heavy parody of Neil deGrasse Tyson.

The look (2026-10-13): a tall, broad man seen three quarters from the front,
facing right. A round full face, short black hair, a thick moustache and no
beard, large warm eyes. A dark blazer that hangs open on the waistcoat he is
known for: night-purple, with a sun, a moon and stars on it. An open collar,
jeans, boots. He stands up straight, he is a little stout, he talks with both
arms, and he looks up.

He is drawn from the man and not from a type (Jon, 2026-10-13, of another
person of this cast: "needs to read like paul erdos not bearnie sanders"). He
is a grown man, not a mascot. He holds nothing; there is no drop shadow.

What he shows you: stars, a planet with a ring, and the grass under your
feet, which is made of the same stuff.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, how he stands and what he shows are his.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, mix
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "neil_ongras_turfson"

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_neil_ongras_turfson",
        "display_name": "Neil onGras Turfson",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "scientist",
            "cosmic_naturalist",
            "touch_grass",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": False,
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
    "visual": {
        "default_pose": "idle",
        "portrait_style": "dialog_closeup",
        "portrait_source": TARGET_NAME,
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "locomotion.run": {"animation": "run", "events": []},
            "traversal.jump": {"animation": "jump", "events": []},
            "traversal.fall": {"animation": "fall", "events": []},
            "interaction.talk": {"animation": "talk", "events": []},
            "interaction.use": {"animation": "interact", "events": []},
            "emote.point": {"animation": "point_sky", "events": []},
            "ability.cosmic_lecture": {"animation": "cosmic_lecture", "events": []},
            "ability.touch_grass": {"animation": "touch_grass", "events": []},
            "ability.grass_sweep": {"animation": "grass_sweep", "events": []},
            "action.defense.block": {"animation": "block", "events": []},
            "emote.taunt": {"animation": "taunt", "events": []},
        },
    },
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Neil onGras Turfson is a pun-heavy parody of Neil deGrasse Tyson: the name sends him 'on "
            "grass turf,' while the character enthusiastically audits the physics of platforming and "
            "explains that even ordinary ground is made from stellar material."
        ),
        "gameplay_description": (
            "Use as a science commentator, tutorial critic, narrator, or playable explainer. He "
            "should notice impossible jumps, distinguish game feel from physical law, direct "
            "attention upward, and continue explaining long after nearby characters have left."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'The universe did not consent to that jump.',
        'The universe is under no obligation to make your platforming feel good.',
        'Look up more.',
    ],
)


BLAZER: RGBA = (48, 56, 84, 255)
BLAZER_DARK: RGBA = (30, 34, 58, 255)
BLAZER_LIGHT: RGBA = (82, 92, 128, 255)
VEST: RGBA = (88, 52, 128, 255)
VEST_DARK: RGBA = (58, 34, 92, 255)
STAR: RGBA = (252, 214, 110, 255)
STAR_DARK: RGBA = (214, 140, 60, 255)
MOON: RGBA = (236, 240, 250, 255)
SHIRT: RGBA = (244, 242, 236, 255)
JEANS: RGBA = (78, 108, 156, 255)
JEANS_DARK: RGBA = (52, 74, 116, 255)
BOOT: RGBA = (112, 72, 48, 255)
BOOT_DARK: RGBA = (68, 42, 32, 255)
SKIN: RGBA = (150, 100, 70, 255)
SKIN_SHADE: RGBA = (116, 74, 54, 255)
SKIN_DEEP: RGBA = (84, 50, 42, 255)
HAIR: RGBA = (30, 26, 32, 255)
HAIR_LIGHT: RGBA = (76, 70, 86, 255)
INK: RGBA = (22, 18, 24, 255)
GRASS: RGBA = (116, 200, 96, 255)
GRASS_DARK: RGBA = (50, 120, 66, 255)
PLANET: RGBA = (240, 170, 110, 255)

#: Tall and broad, 188 cm, and he stands up straight (Jon, 2026-10-13: a
#: round back was right for Erdish, and it is not right for him): his neck is
#: over his hips and his shoulders are level with it, not behind it.
BUILD = Build(hip_up=55.0, thigh=26.7, shin=25.6, neck=(-0.4, -40.0), upper=21.6, fore=20.2, near_shoulder=(-6.4, -34.6), far_shoulder=(8.4, -34.2),
              near_hip=(-4.0, 0.0), far_hip=(4.0, 0.0), head_up=(0.8, -13.2), height=121.0, half_width=(15.0, 17.0))

N = Person(TARGET_NAME, BUILD)
K = N.K
P = N.P


# ---- The pieces --------------------------------------------------------------


def _front(d, hb: float, hf: float) -> None:
    """His waistcoat and his shirt, where his blazer hangs open."""
    K.poly(d, [K.at(1.6, -41.0), K.at(13.0, -41.0), K.at(13.6 + hf, 14.0), K.at(4.4 + hf * 0.5, 14.0), K.at(3.6, -14.0)], VEST)
    K.poly(d, [K.at(10.4, -41.0), K.at(14.0, -41.0), K.at(14.4 + hf, 14.0), K.at(11.6 + hf, 14.0)], BLAZER_DARK)
    K.poly(d, [K.at(3.4, -43.0), K.at(9.6, -43.0), K.at(7.2, -30.0)], SHIRT)
    K.poly(d, [K.at(5.0, -43.0), K.at(8.4, -43.0), K.at(6.8, -36.0)], SKIN_SHADE)
    # The sky on his waistcoat: a sun, a moon and stars.
    K.oval(d, K.at(7.6, -22.0), 1.9, 1.9, STAR)
    K.oval(d, K.at(6.4, -9.0), 1.7, 1.7, MOON)
    K.oval(d, K.at(7.2, -9.4), 1.5, 1.5, VEST)
    for x, y in ((5.4, -27.0), (9.4, -15.4), (5.6, -16.0), (9.0, -3.0), (6.0, 2.0), (9.6, 6.0)):
        K.oval(d, K.at(x, y), 0.7, 0.7, STAR)
    # His near lapel, and the edge of the blazer under it.
    K.poly(d, [K.at(-0.6, -42.0), K.at(3.4, -42.0), K.at(4.2, -22.0), K.at(0.2, -31.0)], BLAZER_LIGHT)
    K.line(d, [K.at(0.2, -31.0), K.at(4.2, -22.0), K.at(3.6, -14.0), K.at(4.4 + hf * 0.5, 10.0)], BLAZER_DARK, 0.7)
    K.line(d, [K.at(-8.0, -4.0), K.at(-1.6, -3.2)], BLAZER_DARK, 0.7)


N.torso = R.make_torso(K, ("blazer",), BLAZER, BLAZER_DARK, back=(10.2, 10.8, 10.6, 11.4), front=(10.6, 13.0, 13.2, 13.0), hem_y=10.0, top=-42.0,
                       shoulders=((-6.0, -34.0), (8.0, -33.8)), shoulder_r=(5.6, 5.4), neck=(-5.4, 4.6), belly=2.4, shade_from=40.0, detail=_front)

NEAR_EYE = (1.0, -0.6)
FAR_EYE = (7.0, -0.8)


def _hair_shape(d) -> None:
    # Short, and round over all of the top of his head.
    K.oval(d, K.at(-0.6, -5.6), 10.0, 8.8, WHITE)


def _hair(d) -> None:
    K.poly(d, [K.at(20.0, -8.6), K.at(9.4, -8.6), K.at(7.0, -7.6), K.at(3.0, -8.2), K.at(-0.4, -7.2), K.at(-2.8, -5.4), K.at(-3.6, -2.4),
               K.at(-6.4, -2.0), K.at(-7.2, 3.6), K.at(-5.6, 5.0), K.at(-5.0, 7.0), K.at(-20.0, 7.0), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
    for x, y in ((-5.0, -9.6), (-1.0, -12.0), (4.0, -12.0), (-7.4, -5.0), (7.4, -10.4), (1.6, -9.6), (-8.0, -0.4)):
        K.oval(d, K.at(x, y), 0.8, 0.6, HAIR_LIGHT)


def _face(d) -> None:
    # His moustache: thick, over all of his lip. No beard.
    K.poly(d, [K.at(2.2, 5.6), K.at(5.2, 4.6), K.at(8.6, 5.2), K.at(9.6, 7.0), K.at(6.0, 6.8), K.at(2.0, 7.4)], HAIR)
    # The round of his cheek.
    K.line(d, [K.at(0.4, 3.6), K.at(1.2, 5.6)], mix(SKIN, SKIN_DEEP, 0.5), 0.5)


_head = R.make_head(K, ("neil",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.2, 8.8, 9.0), jaw=(2.2, 4.4, 7.0, 7.6),
                    nose=((7.4, -0.6), (10.6, 2.8), (10.2, 4.6), (7.2, 5.0)), ear=(-5.4, 1.2, 2.3, 3.2), shape=_hair_shape, under=_hair, over=_face)
_eyes = R.make_eyes(K, NEAR_EYE, FAR_EYE, ink=INK, iris=(70, 40, 28, 255), size=1.05)
_brows = R.make_brows(K, [(-1.6, -3.8), (1.0, -4.8), (3.6, -4.2)], [(5.4, -4.4), (7.2, -5.0), (8.8, -4.2)], HAIR, 1.4)
_mouth = R.make_mouth(K, (5.6, 8.6), (98, 40, 44, 255), wide=1.1)

N.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"),
                              (_mouth(str(pose["mouth"])), "mouth")]
N.neck = R.make_neck(K, SKIN_SHADE, 6.0)
N.upper_arm = lambda near: [(0.0, 1.0, 8.4, 7.0, BLAZER if near else BLAZER_DARK)]
N.forearm = lambda near: [(0.0, 1.0, 7.0, 6.0, BLAZER if near else BLAZER_DARK)]
N.thigh = lambda near: [(0.0, 1.0, 8.8, 7.2, JEANS if near else JEANS_DARK)]
N.shin = lambda near: [(0.0, 1.0, 7.2, 6.4, JEANS if near else JEANS_DARK)]
N.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, SHIRT, (200, 200, 208, 255), size=1.15)
N.shoe = R.make_shoe(K, BOOT, BOOT_DARK, BUILD.ankle_up, long=1.1, heel=1.0)


# ---- How he holds himself ----------------------------------------------------

#: One hand flat on his waistcoat; the other hangs.
ON_CHEST = (7.5, 13.0)
N.set_rest(na=ON_CHEST, nh="flat", nf=(-3.6, 0.0, 0.0), ff=(4.6, 0.0, 0.0))


@N.row
def idle(i: int, n: int):
    # A hand on his waistcoat, and his eyes on what is over your head.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.4 + 0.4 * s), head=(0.3, -0.3 * s, -5.0 + 3.0 * c), eyes="closed" if i == n - 2 else "up" if c < 0.0 else "open",
             brows=1.0 if c < -0.4 else 0.0)


@N.row
def walk(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 9.0, 5.0)
    return P(hip=(0.5, 0.9 * math.cos(2.0 * ph)), lean=2.0, head=(0.0, 0.0, 1.5 * s), na=(-2.0 - 7.0 * c, 25.0 - 1.5 * abs(c)), nh="soft", fh="soft",
             fa=(2.5 + 7.0 * c, 24.5 - 1.5 * abs(c)), nf=nf, ff=ff, hem=(1.0 + abs(c), 0.5 + abs(c)))


@N.row
def talk(i: int, n: int):
    # Both arms: this is how large the thing is.
    _, s, c = loop(i, n)
    wide = max(0.0, s)
    return P(hip=(0.0, 0.4 * s), lean=-1.0, head=(0.4, 0.0, -2.0 + 3.0 * s), na=(4.0 - 16.0 * wide, 6.0 - 6.0 * wide), nab=-1.0 if wide > 0.3 else 1.0,
             fa=(16.0 + 5.0 * wide, 6.0 - 8.0 * wide), nh="open", fh="open", mouth=("open", "smile", "big", "smile")[i % 4],
             brows=1.0 if s > 0.2 else 0.0)


#: He leans back, both palms up and out, and he is very pleased with himself.
BADASS = P(hip=(-1.0, 0.5), lean=-9.0, head=(-0.5, 0.0, -4.0), na=(-12.0, -5.0), nab=-1.0, fa=(17.0, -6.0), nh="open", fh="open", eyes="closed",
           mouth="smile", brows=1.0)


@N.row
def taunt(i: int, n: int):
    return N.keys(shot(i, n), [(0.0, P()), (0.3, BADASS), (0.8, dict(BADASS, lean=-11.0)), (1.0, dict(BADASS, eyes="happy"))])


POINT_SKY = P(hip=(0.0, -0.5), lean=-5.0, head=(0.0, 0.0, -16.0), na=(9.0, -26.0), nab=-1.0, arm="under", nh="point", fa=(3.0, 25.0), fh="soft",
              eyes="up", mouth="open", brows=1.0)


@N.row
def point_sky(i: int, n: int):
    _, s, _c = loop(i, n)
    return N.keys(shot(i, n), [(0.0, P()), (0.3, POINT_SKY), (0.8, dict(POINT_SKY, na=(9.0, -26.0 - s))), (1.0, P())])


@N.row
def cosmic_lecture(i: int, n: int):
    # Both arms as wide as they go, and all of it over his head.
    _, s, _c = loop(i, n)
    return P(hip=(0.0, 0.5 * s), lean=-4.0, head=(0.0, 0.0, -10.0), na=(-15.0, -18.0 + 2.0 * s), nab=-1.0, fa=(20.0, -18.0 - 2.0 * s), nh="open", fh="open",
             eyes="up" if i % 4 else "happy", mouth=("big", "open")[i % 2], brows=1.0)


#: On one knee, a hand on the ground.
KNEEL = P(hip=(-1.0, 17.0), lean=24.0, head=(1.0, 0.0, -6.0), na=(15.0, 24.0), nh="flat", fa=(4.0, 14.0), fh="soft", nf=(-11.0, 0.0, 34.0),
          ff=(9.0, 0.0, 0.0), hem=(3.0, 2.0))


@N.row
def kneel(i: int, n: int):
    return N.keys(shot(i, n), [(0.0, P()), (0.5, dict(KNEEL, na=(10.0, 16.0))), (1.0, KNEEL)])


@N.row
def touch_grass(i: int, n: int):
    # He strokes it. It is made of stars, as you are.
    _, s, _c = loop(i, n)
    return dict(N.full(KNEEL), na=(15.0 + 3.0 * s, 24.0), head=(1.0, 0.0, 2.0), eyes="happy" if i % 5 > 2 else "open", mouth="smile")


@N.row
def grass_sweep(i: int, n: int):
    wind = dict(N.full(KNEEL), na=(-8.0, 20.0), nh="open", brows=-1.0)
    sweep = dict(N.full(KNEEL), hip=(2.0, 15.0), lean=28.0, na=(25.0, 14.0), nh="open", mouth="open", brows=-1.0)
    return N.keys(shot(i, n), [(0.0, KNEEL), (0.3, wind), (0.6, sweep), (0.85, sweep), (1.0, KNEEL)])


@N.row
def celebrate(i: int, n: int):
    ph, s, _c = loop(i, n)
    up = abs(math.sin(ph))
    return P(off=(0.0, -5.0 * up), hip=(0.0, 3.0 * (1.0 - up)), lean=-3.0, head=(0.0, 0.0, -8.0), na=(-12.0, -22.0 + 2.0 * s), nab=-1.0,
             fa=(17.0, -20.0 - 2.0 * s), nh="open", fh="open", nf=(-6.0, -3.0 * up, 20.0 * up), ff=(7.0, -4.0 * up, 12.0 * up), eyes="happy", mouth="big",
             brows=1.0)


# ---- From the front ----------------------------------------------------------
#
# A TEST (Jon, 2026-10-13: "none of these character seem to have a forward
# facing pose ... can we add a forward facing pose for neil as a test?"). The
# rows `front` and `front_talk` face the viewer. The game does not play them
# yet: their names are not ones `CharacterAnim::from_name` knows.

FRONT_TOP = -42.0


def _front_torso():
    """His trunk from the front, from his hips: the blazer open on the
    waistcoat, a lapel each side, the sky down the middle of him."""

    def shape(d) -> None:
        K.poly(d, [K.at(-5.0, FRONT_TOP), K.at(-11.6, FRONT_TOP + 4.0), K.at(-13.0, -24.0), K.at(-13.4, -6.0), K.at(-13.0, 10.0), K.at(13.0, 10.0), K.at(13.4, -6.0),
                   K.at(13.0, -24.0), K.at(11.6, FRONT_TOP + 4.0), K.at(5.0, FRONT_TOP)], WHITE)
        for sx in (-1.0, 1.0):
            K.oval(d, K.at(9.6 * sx, -34.2), 5.6, 6.0, WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(-5.6, FRONT_TOP), K.at(5.6, FRONT_TOP), K.at(6.6, 12.0), K.at(-6.6, 12.0)], VEST)
        K.poly(d, [K.at(-3.4, FRONT_TOP - 1.0), K.at(3.4, FRONT_TOP - 1.0), K.at(0.0, -29.0)], SHIRT)
        K.poly(d, [K.at(-1.8, FRONT_TOP - 1.0), K.at(1.8, FRONT_TOP - 1.0), K.at(0.0, -35.0)], SKIN_SHADE)
        K.oval(d, K.at(0.0, -22.0), 2.2, 2.2, STAR)
        K.oval(d, K.at(-1.6, -9.0), 1.9, 1.9, MOON)
        K.oval(d, K.at(-0.8, -9.4), 1.7, 1.7, VEST)
        for x, y in ((-3.0, -27.0), (3.2, -16.0), (-3.4, -15.0), (2.6, -3.0), (-2.6, 2.0), (3.4, 6.0), (0.4, -30.0)):
            K.oval(d, K.at(x, y), 0.7, 0.7, STAR)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(5.6 * sx, FRONT_TOP), K.at(8.4 * sx, FRONT_TOP + 1.0), K.at(6.6 * sx, -20.0)], BLAZER_LIGHT)
            K.line(d, [K.at(6.6 * sx, -20.0), K.at(6.4 * sx, 10.0)], BLAZER_DARK, 0.7)
            K.line(d, [K.at(12.0 * sx, -4.0), K.at(8.0 * sx, -3.4)], BLAZER_DARK, 0.7)

    return K.solid(("front_blazer",), shape, BLAZER, detail, outline=1.3, rim=0.3, shade=0.4, shade_colour=BLAZER_DARK)


def _front_head():
    def shape(d) -> None:
        K.oval(d, K.at(0.0, -1.6), 9.0, 9.4, WHITE)
        K.oval(d, K.at(0.0, 3.6), 7.6, 7.8, WHITE)
        K.oval(d, K.at(0.0, -5.4), 10.2, 8.6, WHITE)
        for sx in (-1.0, 1.0):
            K.oval(d, K.at(9.0 * sx, 0.8), 2.0, 3.0, WHITE)

    def detail(d) -> None:
        # His hair: short, round over the top of his head, down to each ear.
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 0.0), K.at(8.4, 0.0), K.at(7.8, -4.6), K.at(5.0, -7.6), K.at(0.0, -8.4), K.at(-5.0, -7.6),
                   K.at(-7.8, -4.6), K.at(-8.4, 0.0), K.at(-20.0, 0.0)], HAIR)
        for x, y in ((-6.0, -10.0), (-2.0, -12.4), (3.0, -12.2), (7.0, -9.4), (0.6, -10.0), (-8.6, -5.0), (8.8, -5.4)):
            K.oval(d, K.at(x, y), 0.8, 0.6, HAIR_LIGHT)
        for sx in (-1.0, 1.0):
            K.oval(d, K.at(9.0 * sx, 0.8), 1.5, 2.5, SKIN, OUTLINE, 0.6)
        # His nose, broad, and the moustache under it.
        K.line(d, [K.at(-0.6, -0.6), K.at(-1.9, 3.4), K.at(0.0, 4.4), K.at(1.9, 3.4)], SKIN_DEEP, 0.7)
        K.poly(d, [K.at(-4.6, 6.6), K.at(-2.0, 5.0), K.at(0.0, 5.6), K.at(2.0, 5.0), K.at(4.6, 6.6), K.at(2.0, 7.2), K.at(0.0, 6.8), K.at(-2.0, 7.2)], HAIR)
        K.line(d, [K.at(-3.6, 12.0), K.at(0.0, 13.0), K.at(3.6, 12.0)], mix(SKIN, SKIN_DEEP, 0.5), 0.6)

    return K.solid(("front_head",), shape, SKIN, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=SKIN_DEEP)


def _front_eyes(mode: str):
    def paint(d) -> None:
        for sx in (-1.0, 1.0):
            c = K.at(3.6 * sx, -0.8)
            if mode in ("closed", "happy"):
                up = 0.8 if mode == "closed" else -0.9
                K.line(d, [(c[0] - 2.0, c[1] - up * 0.2), (c[0], c[1] + up), (c[0] + 2.0, c[1] - up * 0.2)], INK, 0.9)
                continue
            K.oval(d, c, 2.0, 1.8 + (0.5 if mode == "wide" else 0.0), (252, 248, 238, 255))
            at = (c[0], c[1] - (0.6 if mode == "up" else 0.0))
            K.oval(d, at, 1.3, 1.4, (70, 40, 28, 255))
            K.oval(d, at, 0.8, 0.9, INK)
            K.oval(d, (at[0] - 0.4, at[1] - 0.5), 0.35, 0.35, WHITE)
            K.line(d, [(c[0] - 2.3, c[1] - 0.2), (c[0] - 0.8, c[1] - 1.8), (c[0] + 0.8, c[1] - 1.8), (c[0] + 2.3, c[1] - 0.2)], INK, 0.8)

    return K.piece(("front_eyes", mode), paint)


def _front_brows(mood: int):
    def paint(d) -> None:
        up = -1.1 if mood > 0 else 0.0
        inner = 0.9 if mood < 0 else 0.0
        for sx in (-1.0, 1.0):
            K.stroke(d, [K.at(6.0 * sx, -4.0 + up), K.at(3.6 * sx, -4.9 + up), K.at(1.4 * sx, -4.2 + up + inner)], HAIR, 1.4)

    return K.piece(("front_brows", mood), paint)


def _front_mouth(mode: str):
    c = K.at(0.0, 9.2)

    def paint(d) -> None:
        if mode == "smile":
            K.line(d, [(c[0] - 3.0, c[1] - 0.6), (c[0], c[1] + 0.8), (c[0] + 3.0, c[1] - 0.6)], (98, 40, 44, 255), 0.9)
        elif mode == "flat":
            K.line(d, [(c[0] - 2.4, c[1]), (c[0] + 2.4, c[1])], (98, 40, 44, 255), 0.9)
        else:
            ry = 2.2 if mode == "big" else 1.4
            K.oval(d, (c[0], c[1] + 0.4), 2.6 if mode == "big" else 2.0, ry, (98, 40, 44, 255), INK, 0.5)
            K.oval(d, (c[0], c[1] + 0.4 + ry * 0.5), 1.3, ry * 0.4, (224, 122, 116, 255))

    return K.piece(("front_mouth", mode), paint)


N.front_torso = _front_torso
N.front_head_layers = lambda pose: [(_front_head(), "head"), (_front_eyes(str(pose["eyes"])), "eyes"), (_front_brows(R.brow_mood(pose)), "brows"),
                                    (_front_mouth(str(pose["mouth"])), "mouth")]
N.front_shoe = R.make_front_shoe(K, BOOT, BOOT_DARK, BUILD.ankle_up, wide=1.1)
N.front_span = (10.4, 5.6)


@N.front_row
def front(i: int, n: int):
    # He faces you, his hands one in the other in front of him, and looks
    # over your head.
    _, s, c = loop(i, n)
    return R.FP(hip=(0.0, 0.4 + 0.4 * s), head=(0.0, -0.3 * s, 0.0), la=(-5.5, 21.0), ra=(-5.5, 21.5), lz=0.35, rz=0.35, lh="flat", rh="flat",
                eyes="closed" if i == n - 2 else "up" if c < 0.0 else "open", brows=1.0 if c < -0.4 else 0.0)


@N.front_row
def front_talk(i: int, n: int):
    # His elbows at his sides and his open hands out to you, one and then the
    # other; and then both, and his shoulders: there it is.
    _, s, c = loop(i, n)
    if i >= n - 3:
        return R.FP(hip=(0.0, -0.4), head=(0.0, 0.0, 6.0), la=(11.0, 9.0), ra=(11.0, 9.0), lz=0.6, rz=0.6, lh="open", rh="open", eyes="closed", mouth="smile",
                    brows=1.0)
    lift_l, lift_r = max(0.0, s), max(0.0, -s)
    return R.FP(hip=(0.0, 0.4 * s), head=(0.0, 0.0, 3.0 * c), la=(8.0 + 3.0 * lift_l, 14.0 - 5.0 * lift_l), ra=(8.0 + 3.0 * lift_r, 14.0 - 5.0 * lift_r), lz=0.6, rz=0.6,
                lh="open", rh="open", mouth=("open", "smile", "big", "smile")[i % 4], brows=1.0 if abs(s) > 0.3 else 0.0)


N.alias(land="land_hard")
N.rows = [
    ("idle", 8, 145), ("walk", 8, 104), ("run", 8, 76), ("crouch", 6, 92), ("jump", 6, 84), ("fall", 6, 92), ("land", 6, 76), ("talk", 8, 104),
    ("interact", 8, 90), ("point_sky", 8, 80), ("cosmic_lecture", 10, 82), ("kneel", 8, 88), ("touch_grass", 10, 84), ("grass_sweep", 8, 76),
    ("block", 6, 82), ("hit", 5, 88), ("celebrate", 8, 88), ("taunt", 8, 94), ("front", 8, 145), ("front_talk", 8, 110),
]


# ---- What he shows you -------------------------------------------------------


def _star(size: float, fill: RGBA = STAR):
    def paint(d) -> None:
        K.star4(d, K.home, size, fill)
        K.star4(d, K.home, size * 0.45, WHITE, None, 0.0, 0.4)

    return K.piece(("star", size, fill), paint)


def _planet(radius: float):
    """A planet with a ring."""

    def shape(d) -> None:
        K.oval(d, K.home, radius, radius, WHITE)
        K.oval(d, K.home, radius * 1.9, radius * 0.5, WHITE)

    def detail(d) -> None:
        K.oval(d, K.home, radius * 1.9, radius * 0.5, STAR)
        K.oval(d, K.at(0.0, -radius * 0.34), radius, radius * 0.8, PLANET)
        K.line(d, [K.at(-radius * 0.8, 0.2), K.at(radius * 0.8, -0.6)], mix(PLANET, STAR_DARK, 0.6), 0.7)

    return K.solid(("planet", radius), shape, PLANET, detail, outline=1.0, rim=0.3, shade=0.4, shade_colour=STAR_DARK)


def _tuft(blades: int, lean: int):
    """Grass, growing up from ``home``; it leans by ``lean`` degrees."""

    def shape(d) -> None:
        for k in range(blades):
            x = (k - (blades - 1) / 2.0) * 2.6
            a = math.radians(-90.0 + (k - (blades - 1) / 2.0) * 9.0 + lean)
            tall = 7.0 + 2.5 * ((k * 7) % 3)
            K.poly(d, [K.at(x - 1.2, 0.0), K.at(x + 1.2, 0.0), K.at(x + tall * math.cos(a), tall * math.sin(a))], WHITE)

    return R.chalk(K, ("tuft", blades, lean), shape, GRASS, GRASS_DARK)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, i, n, hand, head = ctx.anim, ctx.i, ctx.n, ctx.hand, ctx.head

    def stamp(part, p, name: str, degrees: float = 0.0) -> None:
        out.append((part, p, name, degrees))

    def stars(points, origin) -> None:
        for k, (x, y, r) in enumerate(points):
            size = r * (0.55 + 0.45 * math.sin(ctx.phase + k * 2.1) ** 2)
            stamp(_star(round(size * 2.0) / 2.0 + 1.0), (origin[0] + x, origin[1] + y), f"star_{k}")

    if anim == "point_sky" and 0.25 <= ctx.u <= 0.85:
        stamp(_star(4.5), (hand[0] + 8.0, hand[1] - 15.0), "star_0")
        stamp(_star(2.5), (hand[0] + 19.0, hand[1] - 7.0), "star_1")
    elif anim == "cosmic_lecture":
        a = ctx.phase
        mid = (head[0], head[1] - 24.0)
        stamp(_planet(4.0), (mid[0] + 20.0 * math.cos(a), mid[1] + 5.0 * math.sin(a)), "planet")
        stars([(-30.0, 6.0, 3.0), (26.0, 2.0, 3.5), (-12.0, -8.0, 2.5), (34.0, 16.0, 2.5)], mid)
    elif anim in ("touch_grass", "kneel") and (anim == "touch_grass" or ctx.u > 0.6):
        sway = int(round(6.0 * math.sin(ctx.phase)))
        stamp(_tuft(5, sway), (hand[0] + 9.0, ctx.ground - 1.0), "tuft")
        if anim == "touch_grass" and i % 5 > 2:
            stamp(_star(2.5), (hand[0] + 9.0, ctx.ground - 17.0), "star_0")
    elif anim == "grass_sweep" and 0.5 <= ctx.u <= 0.9:
        for k in range(3):
            stamp(_tuft(3, 20 + 10 * k), (hand[0] + 8.0 + 9.0 * k, hand[1] + 4.0 - 5.0 * k), f"tuft_{k}", 20.0 * k)
    elif anim == "celebrate":
        stars([(-28.0, -26.0, 3.5), (30.0, -24.0, 3.5), (-38.0, -2.0, 2.5)], head)
    elif anim == "taunt" and ctx.u >= 0.3:
        stamp(_star(3.0), (head[0] + 16.0, head[1] - 16.0), "star_0")
    elif anim == "interact" and 3 <= i <= 5:
        stamp(_star(3.0), (hand[0] + 16.0, hand[1] - 5.0), "star_0")
    del n
    return out


N.effects = _effects
ROWS = N.rows


def _render_frame(anim: str, frame_idx: int, nframes: int):
    return N.render_frame(anim, frame_idx, nframes)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return N.render(out_dir, ACTOR_METADATA)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Neil onGras Turfson spritesheet.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet: the clips his conversations
    name."""
    del opts
    return N.portraits(out_dir, {
        "default": ('idle', (0, 1, 2, 3, 4, 5, 6, 7), 145, True),
        "portrait": ('idle', (1,), 0, False),
        "talking": ('talk', (0, 1, 2, 3, 4, 5, 6, 7), 104, True),
        "lecture": ('cosmic_lecture', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9), 82, True),
        "inspecting": ('interact', (0, 1, 2, 3, 4, 5, 6, 7), 90, True),
    }, still="portrait", view_width=38.0)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
