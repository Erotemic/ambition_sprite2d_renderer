"""Sprite generator for Marie Curry: the chemist whose cooking glows, and who
measures the dose.

A parody of Marie Curie, with a pot of curry where the pitchblende was.

The look (2026-10-13): a small, slight woman of about forty seen three
quarters from the front, facing right. Fair hair going grey, put up loose on
top of her head and coming down in wisps; a grave thin face, a high brow, a
mouth that does not smile for a picture. The plain black dress with a high
neck that she wore to the laboratory and to both prizes, its sleeves pushed
up, and a white apron over it, stained green at the hem. She is tired and
she does not stop.

She is drawn from the woman, and as herself, not as one shape that every
woman of the cast shares (Jon, 2026-10-13: "The women need to read more as
women, and there needs to be variation"; and, of another person of the cast:
"needs to read like paul erdos not bearnie sanders"). She is a grown woman,
not a mascot. There is no drop shadow. At rest she holds nothing: the pot,
the ladle and the vial are drawn in the rows that are theirs.

What she shows: the glow.

She is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the dress, how she stands and what she shows are hers.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, lerp, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "marie_curry"
DISPLAY_NAME = "Marie Curry"
ROWS = [("idle", 8, 140), ("walk", 8, 96), ("talk", 6, 110), ("interact", 6, 104), ("stir", 8, 82), ("toss", 7, 86), ("taunt", 8, 92), ("hurt", 5, 90),
        ("death", 8, 112)]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_marie_curry",
        "display_name": "Marie Curry",
    },
    "authoring_description": {
        "parody_of": "Marie Curie",
        "core_joke": "A culinary-radiant parody of Marie Curie: the brilliant scientist reimagined as a dangerous curry alchemist whose cookware glows with suspiciously energetic spice.",
        "visual_inspirations": [
            "Marie Curie portraiture and late-19th-century scholar silhouettes",
            "apron-over-dress chef-scientist hybrid costume",
            "a glowing curry pot carried like lab equipment",
            "green radiance cues kept stylized and playful rather than realistic or grim",
        ],
        "design_notes": [
            "The joke should read instantly as Curie becomes Curry, but the character should still feel competent, prestigious, and formidable.",
            "Blend laboratory and kitchen language: apron, stirring spoon, potion pot, notebook-minded posture.",
            "She should feel dangerous because she knows exactly what she is doing, not because she is chaotic.",
            "The glow should imply radiant chemistry and experimental cooking at once.",
        ],
        "reference_hooks": [
            "radioactivity and luminous materials",
            "scientific rigor",
            "kitchen alchemy",
            "precise, understated intensity",
        ],
    },
    "gameplay_description": {
        "role": "mid-range alchemist / area-control scientist",
        "combat_identity": [
            "stirs volatile curry compounds before releasing them",
            "controls space with splashes, fumes, or radiant puddles",
            "reads as a smart caster rather than a brawler",
        ],
        "signature_moves": [
            "Radium Roux: a glowing stir that charges her concoction",
            "Curry Burst: a lob or toss of volatile sauce",
            "Half-Life Simmer: a lingering hazard puddle or aura",
        ],
        "authoring_notes": [
            "This sheet includes a stir attack and a toss animation that can back future spell or projectile mechanics.",
            "A later expansion would benefit from a dedicated throw, splash impact, and maybe a 'measure sample' or note-taking pose.",
            "Dialog should feel calm, exacting, and a little dry, even while the food chemistry becomes absurd.",
        ],
    },
    "dialogue_hints": {
        "suggested_barks": [
            "Careful, it is still reactive.",
            "Let it simmer.",
            "A measured dose.",
            "Observe the glow.",
            "That mixture was unstable anyway.",
            "The spice is luminous today.",
        ],
        "fallback_dialogue": [
            "Precision matters in both science and cooking.",
            "People panic around invisible forces. I prefer to study them.",
            "A good experiment and a good recipe both deserve patience.",
            "The hazard is usually not the substance. It is the carelessness.",
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "combatant",
            "scientist_parody",
            "chemist",
            "chef",
            "caster",
            "mentor",
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
            "carry": True,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "portrait_style": "dialog_closeup",
        "portrait_source": TARGET_NAME,
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "action.ability.primary": {
            "animation": "stir",
            "events": [
                {"t": 0.28, "event": "cast_start", "source": "marie_curry.stir"},
                {"t": 0.70, "event": "cast_release", "source": "marie_curry.stir"},
            ],
        },
        "action.ranged.primary": {
            "animation": "toss",
            "events": [
                {"t": 0.52, "event": "projectile_release", "source": "marie_curry.toss"},
            ],
        },
        "emote.taunt": {"animation": "taunt", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "marie_curry.authored", "point": {"x": 72.0, "y": 24.0}},
        "chest": {"source": "marie_curry.authored", "point": {"x": 66.0, "y": 52.0}},
        "hand_l": {"source": "marie_curry.authored", "point": {"x": 56.0, "y": 66.0}},
        "hand_r": {"source": "marie_curry.authored", "point": {"x": 88.0, "y": 64.0}},
        "speech_bubble": {"source": "marie_curry.authored", "point": {"x": 72.0, "y": 8.0}},
        "projectile_origin": {"source": "marie_curry.authored", "point": {"x": 98.0, "y": 62.0}},
        "prop_anchor": {"source": "marie_curry.authored", "point": {"x": 54.0, "y": 70.0}},
    },
    "tags": [
        "story",
        "combatant",
        "scientist_parody",
        "chemist",
        "chef",
        "caster",
        "marie_curie_parody",
    ],
}

DRESS: RGBA = (44, 42, 56, 255)
DRESS_DARK: RGBA = (24, 22, 34, 255)
DRESS_LIGHT: RGBA = (86, 84, 106, 255)
APRON: RGBA = (244, 240, 230, 255)
APRON_DARK: RGBA = (196, 190, 180, 255)
SKIN: RGBA = (240, 212, 194, 255)
SKIN_SHADE: RGBA = (210, 174, 160, 255)
SKIN_DEEP: RGBA = (164, 116, 110, 255)
HAIR: RGBA = (196, 178, 150, 255)
HAIR_DARK: RGBA = (140, 124, 108, 255)
HAIR_LIGHT: RGBA = (232, 226, 214, 255)
BOOT: RGBA = (40, 36, 44, 255)
INK: RGBA = (26, 22, 30, 255)
GLOW: RGBA = (170, 250, 130, 255)
GLOW_DARK: RGBA = (60, 150, 70, 255)
GLOW_PALE: RGBA = (230, 255, 200, 255)
GLOW_HAZE: RGBA = (170, 250, 130, 64)
CURRY: RGBA = (236, 170, 60, 255)
IRON: RGBA = (78, 80, 96, 255)
IRON_DARK: RGBA = (44, 44, 60, 255)
GLASS: RGBA = (214, 238, 244, 255)

#: Small and slight: 155 cm.
BUILD = Build(hip_up=43.0, thigh=20.9, shin=19.4, neck=(0.6, -34.0), upper=17.4, fore=16.4, near_shoulder=(-4.2, -29.6), far_shoulder=(5.2, -29.2),
              near_hip=(-3.6, 0.0), far_hip=(3.6, 0.0), head_up=(1.0, -12.2), height=100.0, half_width=(11.5, 13.0))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0
HEM = BUILD.hip_up - 5.0


def _front(d, hb: float, hf: float) -> None:
    """Her apron: a bib and a skirt, tied at her waist, green at its hem."""
    K.poly(d, [K.at(0.0, TOP + 8.0), K.at(8.4, TOP + 8.6), K.at(8.2, TOP + 19.0), K.at(-0.6, TOP + 18.4)], APRON)
    K.poly(d, [K.at(-3.0, TOP + 18.4), K.at(9.4, TOP + 19.2), K.at(11.2 + hf, HEM - 5.0), K.at(-5.0 - hb * 0.4, HEM - 5.0)], APRON)
    K.line(d, [K.at(-9.0, TOP + 17.6), K.at(10.0, TOP + 19.0)], APRON_DARK, 1.2)
    K.line(d, [K.at(0.4, TOP + 8.0), K.at(-3.0, TOP + 1.0)], APRON_DARK, 0.9)
    for x, y, r in ((0.0, HEM - 8.0, 1.6), (5.6, HEM - 6.6, 1.2), (8.6 + hf, HEM - 9.0, 1.0)):
        K.oval(d, K.at(x, y), r, r * 0.8, GLOW)
    K.poly(d, [K.at(0.6, TOP - 1.0), K.at(7.4, TOP - 1.0), K.at(7.0, TOP + 3.2), K.at(1.0, TOP + 3.2)], DRESS_DARK)
    for x in (-6.4, -8.0):
        K.line(d, [K.at(x, 2.0), K.at(x * 1.4 - hb * 0.4, HEM - 2.0)], DRESS_LIGHT, 0.6)


X.torso = R.make_figure(K, ("curry",), DRESS, DRESS_DARK, back=(6.6, 6.8, 5.6, 7.6, 11.6), front=(5.8, 7.6, 5.8, 7.8, 11.2), hem_y=HEM, top=TOP,
                        shoulders=((-4.2, -29.0), (4.8, -28.8)), shoulder_r=(4.2, 3.8), waist_y=TOP + 18.0, shade_from=8.8, detail=_front)


def _hair_shape(d) -> None:
    # Up, loose, in a soft knot on top; it does not stay.
    K.oval(d, K.at(-1.0, -5.0), 9.0, 8.4, WHITE)
    K.oval(d, K.at(-3.0, -12.0), 5.4, 4.2, WHITE)
    K.poly(d, [K.at(-8.6, -3.0), K.at(-10.6, 1.6), K.at(-8.0, 2.6), K.at(-8.6, 6.0), K.at(-5.0, 5.4)], WHITE)


def _hair(d) -> None:
    K.poly(d, [K.at(20.0, -8.6), K.at(8.4, -8.6), K.at(5.0, -7.6), K.at(1.6, -6.2), K.at(-1.4, -4.0), K.at(-2.6, -1.0), K.at(-5.6, -0.6), K.at(-6.2, 3.6),
               K.at(-4.8, 5.0), K.at(-4.4, 6.6), K.at(-20.0, 6.6), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
    for strand in ([(6.0, -9.8), (0.0, -10.0), (-5.0, -7.0)], [(-0.6, -13.6), (-4.0, -14.6), (-7.0, -12.0)], [(-6.4, -1.0), (-9.0, 2.0)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_DARK, 0.6)
    K.line(d, [K.at(3.0, -8.2), K.at(-2.0, -8.4), K.at(-6.0, -4.6)], HAIR_LIGHT, 0.7)


def _face(d) -> None:
    # She has not slept enough for thirty years.
    K.line(d, [K.at(0.4, 2.4), K.at(3.0, 2.8)], mix(SKIN, SKIN_DEEP, 0.45), 0.5)
    K.line(d, [K.at(0.6, 4.6), K.at(2.0, 7.4)], mix(SKIN, SKIN_DEEP, 0.4), 0.5)


_head = R.make_head(K, ("curry",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.6, 7.6, 9.0), jaw=(2.4, 3.6, 5.0, 6.8),
                    nose=((7.2, 0.4), (8.9, 3.0), (8.5, 3.9), (7.2, 4.1)), ear=(-4.6, 1.2, 1.8, 2.6), shape=_hair_shape, under=_hair, over=_face)
_eyes = R.make_eyes(K, (2.0, -0.4), (7.2, -0.6), ink=INK, iris=(90, 110, 130, 255), size=0.9, lash=0.3)
_brows = R.make_brows(K, [(-0.4, -4.2), (2.0, -4.6), (4.6, -3.8)], [(6.0, -4.0), (7.4, -4.6), (8.6, -4.2)], HAIR_DARK, 0.9)
_mouth = R.make_mouth(K, (5.4, 7.2), (130, 66, 72, 255), wide=0.75)

X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"),
                              (_mouth(str(pose["mouth"])), "mouth")]
X.neck = R.make_neck(K, SKIN_SHADE, 3.6)
# Her sleeves are pushed up above her wrists.
X.upper_arm = lambda near: [(0.0, 1.0, 5.8, 5.0, DRESS if near else DRESS_DARK)]
X.forearm = lambda near: [(0.6, 1.0, 4.0, 3.6, SKIN if near else SKIN_SHADE), (0.0, 0.66, 5.0, 4.8, DRESS if near else DRESS_DARK)]
X.thigh = lambda near: [(0.0, 1.0, 6.2, 5.2, DRESS if near else DRESS_DARK)]
X.shin = lambda near: [(0.0, 1.0, 5.2, 4.4, DRESS if near else DRESS_DARK)]
X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, size=0.84)
X.shoe = R.make_shoe(K, BOOT, (20, 18, 24, 255), BUILD.ankle_up, long=0.9, heel=0.8)

# ---- How she holds herself ---------------------------------------------------

HELD_NEAR = (5.0, 14.0)
HELD_FAR = (-1.0, 21.0)
X.set_rest(na=HELD_NEAR, fa=HELD_FAR, nh="flat", mouth="flat", nf=(-3.4, 0.0, 0.0), ff=(4.4, 0.0, 0.0))


@X.row
def idle(i: int, n: int):
    # Her hands at her apron. She is counting something in her head.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 + 0.3 * s), head=(0.2, -0.2 * s, 2.0 + 2.0 * c), eyes="closed" if i == n - 2 else "open")


@X.row
def walk(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 6.4, 3.2)
    return P(hip=(0.5, 0.7 * math.cos(2.0 * ph)), lean=3.0, head=(0.0, 0.0, 1.0 * s), nf=nf, ff=ff, hem=(1.0 + 1.5 * abs(c), 0.5 + 1.5 * abs(c)))


@X.row
def talk(i: int, n: int):
    _, s, _c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), head=(0.3, 0.0, 2.0 * s), na=(12.0, 5.0 - 3.0 * max(0.0, s)), nh="open" if s > 0.0 else "flat", mouth=("open", "flat", "o", "flat")[i % 4],
             brows=1.0 if s > 0.5 else 0.0)


@X.row
def interact(i: int, n: int):
    # She holds the vial up to the light and reads it.
    up = P(lean=-2.0, head=(0.0, 0.0, -8.0), na=(13.0, -8.0), nh="fist", brows=-1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.35, up), (0.8, dict(up, na=(13.0, -9.0))), (1.0, P())])


#: Over the pot, the ladle in both hands.
AT_POT = P(hip=(1.0, 3.0), lean=14.0, head=(0.6, 0.0, 10.0), na=(16.0, 9.0), fa=(14.0, 12.0), nh="fist", fh="fist", brows=-1.0)


@X.row
def stir(i: int, n: int):
    _, s, c = loop(i, n)
    return dict(X.full(AT_POT), na=(16.0 + 3.0 * c, 9.0 + 1.5 * s), fa=(14.0 + 3.0 * c, 12.0 + 1.5 * s))


@X.row
def toss(i: int, n: int):
    dip = dict(X.full(AT_POT), na=(15.0, 13.0))
    back = P(hip=(-2.0, 2.0), lean=-8.0, na=(-10.0, -6.0), nab=-1.0, nh="fist", fa=(8.0, 14.0), brows=-1.0)
    out = P(hip=(3.0, 2.0), lean=12.0, na=(23.0, -6.0), nh="fist", fa=(-4.0, 20.0), mouth="open", brows=-1.0, hem=(3.0, 1.0))
    return X.keys(shot(i, n), [(0.0, dip), (0.3, back), (0.55, out), (0.8, out), (1.0, P())])


@X.row
def taunt(i: int, n: int):
    # "Observe the glow." And for once she almost smiles.
    show = P(lean=-3.0, head=(0.0, 0.0, -4.0), na=(15.0, -6.0), nh="fist", brows=1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.3, show), (0.8, dict(show, mouth="smile")), (1.0, dict(show, mouth="smile", eyes="happy"))])


@X.row
def hurt(i: int, n: int):
    back = P(hip=(-2.0, 2.0), lean=-6.0, eyes="wince", mouth="grit")
    return X.keys(shot(i, n), [(0.0, P(lean=-4.0, eyes="wide", mouth="o")), (0.3, R.STRUCK), (0.6, R.STRUCK), (1.0, back)])


@X.row
def death(i: int, n: int):
    # She goes down straight, as she did everything (a long skirt does not sit).
    back = dict(X.full(R.STRUCK), lean=-12.0)
    return X.keys(shot(i, n), [(0.0, back), (0.2, dict(back, lean=-20.0)), (0.7, R.SUPINE), (1.0, R.SUPINE)])


X.rows = list(ROWS)

# ---- From the front ------------------------------------------------------------

def _front_dress(d) -> None:
    """Her black dress from the front, and the white apron over it: its bib,
    its tie, and the green of what she cooks at its hem."""
    K.poly(d, [K.at(-3.0, TOP - 1.0), K.at(3.0, TOP - 1.0), K.at(2.6, TOP + 2.4), K.at(-2.6, TOP + 2.4)], DRESS_LIGHT)
    K.poly(d, [K.at(-4.6, TOP + 7.0), K.at(4.6, TOP + 7.0), K.at(5.4, -12.0), K.at(8.4, -9.0), K.at(9.8, HEM - 6.0), K.at(-9.8, HEM - 6.0), K.at(-8.4, -9.0),
               K.at(-5.4, -12.0)], APRON)
    for sx in (-1.0, 1.0):
        K.line(d, [K.at(4.6 * sx, TOP + 7.0), K.at(3.0 * sx, TOP + 1.0)], APRON_DARK, 0.9)
        K.line(d, [K.at(5.4 * sx, -12.0), K.at(9.0 * sx, -12.6)], APRON_DARK, 0.8)
    K.line(d, [K.at(-5.4, -12.0), K.at(5.4, -12.0)], APRON_DARK, 0.6)
    for x in (-4.0, 0.0, 4.0):
        K.line(d, [K.at(x, -8.0), K.at(x * 1.5, HEM - 8.0)], APRON_DARK, 0.5)
    for x, y, r in ((-5.0, HEM - 9.0, 1.6), (3.0, HEM - 8.0, 2.0), (6.6, HEM - 10.6, 1.2)):
        K.oval(d, K.at(x, y), r, r * 0.8, mix(APRON, GLOW, 0.6))


def _front_hair_shape(d) -> None:
    # Put up loose on top of her head, and wisps at each side.
    K.oval(d, K.at(0.0, -6.0), 9.2, 7.4, WHITE)
    K.oval(d, K.at(0.6, -12.6), 5.4, 4.0, WHITE)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(6.6 * sx, -4.0), K.at(9.4 * sx, 0.0), K.at(8.6 * sx, 5.0), K.at(6.6 * sx, 3.0)], WHITE)


def _front_hair(d) -> None:
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 5.0), K.at(6.6, 5.0), K.at(7.0, -2.6), K.at(4.6, -7.0), K.at(0.0, -8.4), K.at(-4.6, -7.0),
               K.at(-7.0, -2.6), K.at(-6.6, 5.0), K.at(-20.0, 5.0)], HAIR)
    for strand in ([(-4.0, -12.6), (0.6, -14.6), (4.6, -12.0)], [(-6.0, -8.0), (-2.0, -10.0), (2.0, -9.6)], [(6.0, -8.0), (7.6, -3.0)], [(-7.8, -2.0), (-7.6, 3.0)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_DARK, 0.6)
    K.line(d, [K.at(2.0, -11.0), K.at(5.0, -9.0)], HAIR_LIGHT, 0.6)


def _front_grave(d) -> None:
    K.line(d, [K.at(-0.2, 0.4), K.at(-0.9, 3.2), K.at(0.0, 3.9), K.at(0.9, 3.2)], SKIN_DEEP, 0.5)
    for sx in (-1.0, 1.0):
        K.line(d, [K.at(2.6 * sx, 1.6), K.at(4.4 * sx, 2.2)], mix(SKIN, SKIN_DEEP, 0.4), 0.4)


X.front_torso = R.make_front_torso(K, ("curry",), DRESS, DRESS_DARK, [(TOP, 3.2), (TOP + 3.6, 6.6), (TOP + 12.5, 7.6), (-13.0, 5.8), (0.0, 7.6), (HEM, 11.4)],
                                   shoulder=(5.4, -29.4, 3.6, 4.0), detail=_front_dress)
X.front_head_layers = R.front_face(R.make_front_head(K, ("curry",), SKIN, SKIN_DEEP, wide=7.2, jaw=5.6, chin=4.0, shape=_front_hair_shape, hair=_front_hair,
                                                    face=_front_grave),
                                   R.make_front_eyes(K, ("curry",), ink=INK, iris=(90, 110, 130, 255), spread=3.2, y=-0.4, size=0.85, lash=0.3),
                                   R.make_front_brows(K, ("curry",), HAIR_DARK, spread=3.2, y=-3.8, width=0.9),
                                   R.make_front_mouth(K, ("curry",), y=7.8, colour=(130, 66, 72, 255), wide=0.7))
X.front_shoe = R.make_front_shoe(K, BOOT, (20, 18, 24, 255), BUILD.ankle_up, wide=0.85)
X.front_span = (6.4, 4.0)
R.add_front_rows(X)

# ---- What she shows ----------------------------------------------------------


def _pot(level: int):
    """Her pot, on its three legs, from the middle of its mouth. ``level``:
    how hard it glows, 0 to 3."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, 6.0), 9.6, 7.6, WHITE)
        K.rrect(d, K.home[0] - 10.4, K.home[1] - 1.0, K.home[0] + 10.4, K.home[1] + 2.2, 1.0, WHITE)
        for x in (-6.0, 6.0):
            K.stroke(d, [K.at(x, 12.0), K.at(x * 1.2, 17.0)], WHITE, 2.0)

    def detail(d) -> None:
        K.oval(d, K.at(0.0, 0.4), 8.6, 1.9, mix(CURRY, GLOW, level / 3.0))
        K.line(d, [K.at(-6.0, 5.0), K.at(-7.4, 10.0)], mix(IRON, WHITE, 0.3), 0.8)

    return K.solid(("pot", level), shape, IRON, detail, outline=1.2, rim=0.3, shade=0.4, shade_colour=IRON_DARK)


def _ladle(length: float):
    """Her ladle, along +x from her hand to its bowl."""

    def shape(d) -> None:
        K.stroke(d, [K.at(-2.0, 0.0), K.at(length, 0.0)], WHITE, 1.6)
        K.oval(d, K.at(length + 2.0, 0.6), 3.2, 2.6, WHITE)

    return K.solid(("ladle", length), shape, (176, 180, 194, 255), lambda d: K.oval(d, K.at(length + 2.0, 0.2), 2.2, 1.4, GLOW), outline=1.0, rim=0.3,
                   shade=0.4, shade_colour=IRON_DARK)


def _vial():
    def shape(d) -> None:
        K.rrect(d, K.home[0] - 1.8, K.home[1] - 9.0, K.home[0] + 1.8, K.home[1] + 1.0, 1.6, WHITE)

    def detail(d) -> None:
        K.rrect(d, K.home[0] - 1.8, K.home[1] - 4.6, K.home[0] + 1.8, K.home[1] + 1.0, 0.0, GLOW)
        K.rrect(d, K.home[0] - 2.2, K.home[1] - 9.6, K.home[0] + 2.2, K.home[1] - 8.0, 0.0, (150, 110, 70, 255))

    return K.solid(("vial",), shape, GLASS, detail, outline=1.0, rim=0.3, shade=0.3, shade_colour=(120, 150, 170, 255))


def _haze(radius: float):
    return K.piece(("haze", radius), lambda d: K.oval(d, K.home, radius, radius, GLOW_HAZE))


def _mote(radius: float):
    return K.solid(("mote", radius), lambda d: K.oval(d, K.home, radius, radius, WHITE), GLOW, None, outline=0.8, rim=0.0, shade=0.4, shade_colour=GLOW_DARK)


def _blob(radius: float):
    def shape(d) -> None:
        K.oval(d, K.home, radius, radius * 0.86, WHITE)
        K.oval(d, K.at(-radius * 0.9, 0.6), radius * 0.6, radius * 0.5, WHITE)

    return K.solid(("blob", radius), shape, mix(CURRY, GLOW, 0.5), lambda d: K.oval(d, K.at(1.0, -1.0), radius * 0.4, radius * 0.3, GLOW_PALE), outline=1.0,
                   rim=0.3, shade=0.4, shade_colour=GLOW_DARK)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, i, u = ctx.anim, ctx.i, ctx.u

    def motes(origin, count: int) -> None:
        for k in range(count):
            t = (ctx.phase / math.tau + k / count) % 1.0
            out.append((_mote(1.6 - 0.8 * t), (origin[0] + 6.0 * math.sin(k * 2.4 + t * 4.0), origin[1] - 16.0 * t), f"mote_{k}", 0.0))

    if anim in ("stir", "toss") and not (anim == "toss" and u > 0.9):
        pot = (ctx.hip[0] + 30.0, ctx.ground - 20.0)
        level = (1 + i % 3) if anim == "stir" else 2
        out.append((_haze(13.0 + level), (pot[0], pot[1] - 2.0), "haze", 0.0))
        out.append((_pot(level), pot, "pot", 0.0))
        motes((pot[0], pot[1] - 4.0), 3)
        if anim == "stir" or u < 0.25:
            turn = math.degrees(math.atan2(pot[1] - ctx.hand[1], pot[0] - ctx.hand[0]))
            out.append((_ladle(round(math.dist(ctx.hand, pot)) - 3.0), ctx.hand, "ladle", turn))
        else:
            turn = math.degrees(math.atan2(ctx.hand[1] - ctx.elbow[1], ctx.hand[0] - ctx.elbow[0]))
            out.append((_ladle(12.0), ctx.hand, "ladle", turn))
            if u >= 0.55:
                t = (u - 0.55) / 0.45
                out.append((_blob(4.0), (ctx.hand[0] + 16.0 + 34.0 * t, ctx.hand[1] - 6.0 - 26.0 * math.sin(t * math.pi) + 14.0 * t), "blob", 40.0 * t))
    elif anim in ("interact", "taunt") and 0.25 <= u:
        out.append((_haze(8.0 + (i % 2)), (ctx.hand[0] + 1.0, ctx.hand[1] - 6.0), "haze", 0.0))
        out.append((_vial(), (ctx.hand[0] + 1.0, ctx.hand[1] - 1.0), "vial", 0.0))
        if anim == "taunt":
            motes((ctx.hand[0] + 1.0, ctx.hand[1] - 10.0), 3)
    return out


X.effects = _effects

_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)
TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
