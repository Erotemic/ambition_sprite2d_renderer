"""Sprite generator for Georg Canter: a professor of sets, who is a centaur.

An affectionate caricature of Georg Cantor.

The look (2026-10-13): from the withers up, a professor of the 1880s, seen
three quarters from the front, facing right: a high bare forehead, dark hair
going grey at the sides, a full beard, a black frock coat over a grey
waistcoat, a white collar and a dark bow tie, and on his chest a small gold
aleph. From the withers down, a bay horse: a deep chest, a round barrel, four
dark legs with black hooves, a black tail. On his back a blanket with sets
inside sets drawn on it. He stands straight, one hand on his lapel.

He is a centaur because that is who he is: nothing in the game stops to
explain it. He is a grown man, not a mascot. He holds nothing at rest: his
lance is in his hand only in the row that is its own. There is no drop
shadow.

What he shows: a table of numbers and the line down its diagonal, which is
the number the table does not have; the whole numbers, counted off behind
him as he runs; a set, and the set of its parts, and the set of those; and
alephs, which fall.

He is a person of ``_person_rig`` from the withers up, and his front legs are
its legs: the bones, the poses and the frame are shared. His barrel, his hind
legs and his tail are layers of his own.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import RGBA, mix, pin, solve
from ._ai_era_kit import WHITE as _SOLID
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "georg_canter"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Georg Canter"

AUTHORING_DESCRIPTION = (
    "Georg Canter parodies Georg Cantor, the mathematician who founded modern "
    "set theory and introduced transfinite numbers for comparing different "
    "sizes of infinity. The surname becomes Canter, making him a centaur whose "
    "equine body supplies a strong silhouette and a natural high-mobility combat "
    "identity. His diagonal lance refers to Cantor's diagonal argument; nested "
    "rings, braces, and doubling constellations refer to sets, power sets, and "
    "Cantor's theorem; aleph ornaments refer to transfinite cardinal numbers. "
    "The human half draws loosely from late-nineteenth-century portraits: dark "
    "formal coat, high collar, intense eyes, swept hair, and a full beard, without "
    "reproducing one portrait exactly. He is a direct Cantor parody and is not a "
    "replacement for the separate Genghis Can and Genghis Can't pair. Ambition "
    "treats humans, animals, machines, and mixed bodies as an ordinary society, "
    "so nobody explains or comments on his being a centaur."
)

GAMEPLAY_DESCRIPTION = (
    "A mobile mid-heavy controller who turns increasing cardinality into escalating "
    "space control. His horse body gives him fast grounded acceleration and a long "
    "hurtbox, while the diagonal lance reaches through clustered opponents. "
    "Diagonalize marks one element from each nearby group and then cuts across the "
    "resulting diagonal. Countable Charge leaves a numbered procession of fading "
    "afterimages. Power Set surrounds a marked region with a strictly larger nested "
    "attack pattern, and Aleph Rain drops ordered sigils that become denser over "
    "time. He should feel commanding and inevitable rather than frantic: excellent "
    "at occupying lanes, weaker when crowded from directly above or behind. The "
    "initial catalog entry uses the existing generic swipe action set until these "
    "dedicated mechanics are authored in the unified moveset system."
)

SUGGESTED_BARKS = {
    "on_hit": [
        "You have removed one point, not the set.",
        "Finite irritation.",
        "The argument survives contact.",
    ],
    "provoked": [
        "Very well. Choose a number.",
        "You may begin counting whenever you are ready.",
    ],
    "idle": [
        "Infinity is not a number. It is a crowded neighborhood.",
        "There is always a larger collection.",
        "Count carefully. Then count what counting missed.",
    ],
    "hall": [
        "Some infinities fit inside others and still fail to be the same size.",
        "I can list your options. I can also construct the one you omitted.",
        "The diagonal is not rude. It is conclusive.",
        "Genghis Can and Genghis Can't are not my graduate students.",
    ],
}

FALLBACK_DIALOGUE = [
    "A list may continue forever and still leave something out. The interesting step is constructing the omission rather than merely asserting it.",
    "Given any collection, the collection of all its subcollections is larger. The universe is remarkably consistent about refusing a largest size.",
    "People say infinity as though it were one distant place. I have spent my career explaining that it has districts.",
    "My lance follows the diagonal: one choice from each row, changed just enough that the result cannot already be on the list.",
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_georg_canter",
        "display_name": "Georg Canter",
    },
    "dialogue_hints": {
        "suggested_barks": [
            'Some infinities are roomier.',
            'You cannot list us all. I have checked.',
            'Count again. Slower.',
            'There is always one more.',
        ],
        "fallback_dialogue": [
            'I showed the line holds more than the counting numbers, and was told this was indecent.',
            'Between any two of your objections there is another objection. That is the shape of the problem.',
            'The set of things you have not tried is strictly larger than the set of things you have.',
            'A diagonal is a very quiet kind of proof.',
        ],
    },
    "body": {
        "body_plan": "Centauroid",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "traits": [
            "centaur",
            "mathematician",
            "set_theorist",
            "transfinite",
            "lancer",
            "playable_candidate",
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
            "crawl": None,
            "use_lifts": True,
            "door_access": ["public", "wide"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": True,
            "open_doors": ["public", "wide"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "striker_swipe"},
    "visual": {"default_pose": "idle"},
    "tags": [
        "centaur",
        "mathematician",
        "set_theorist",
        "transfinite",
        "lancer",
        "playable_candidate",
    ],
    "authoring": {
        "authoring_description": AUTHORING_DESCRIPTION,
        "gameplay_description": GAMEPLAY_DESCRIPTION,
        "suggested_barks": SUGGESTED_BARKS,
        "fallback_dialogue": FALLBACK_DIALOGUE,
    },
    "sockets": {
        "head": {
            "source": "explicit.profile.centauroid",
            "point": {"x": 202.0, "y": 57.0},
        },
        "chest": {
            "source": "explicit.profile.centauroid",
            "point": {"x": 203.0, "y": 116.0},
        },
        "hand_l": {
            "source": "explicit.profile.centauroid",
            "point": {"x": 166.0, "y": 139.0},
        },
        "hand_r": {
            "source": "explicit.profile.centauroid",
            "point": {"x": 232.0, "y": 137.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.centauroid",
            "point": {"x": 200.0, "y": 8.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "action.melee.primary": {"animation": "diagonalize", "events": []},
        "action.melee.secondary": {"animation": "countable_charge", "events": []},
        "action.special.primary": {"animation": "power_set", "events": []},
        "action.special.secondary": {"animation": "aleph_rain", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
}

# Palette: academic indigo and gold above a deep chestnut horse body.
OUTLINE = (25, 20, 32, 255)
HORSE: RGBA = (150, 84, 54, 255)
HORSE_LIGHT: RGBA = (190, 118, 74, 255)
HORSE_DARK: RGBA = (104, 56, 42, 255)
SOCK: RGBA = (58, 40, 40, 255)
SOCK_DARK: RGBA = (36, 26, 30, 255)
HOOF: RGBA = (30, 26, 32, 255)
MANE: RGBA = (38, 30, 36, 255)
SKIN: RGBA = (232, 196, 170, 255)
SKIN_SHADE: RGBA = (198, 154, 136, 255)
SKIN_DEEP: RGBA = (156, 106, 98, 255)
HAIR: RGBA = (70, 62, 66, 255)
HAIR_GREY: RGBA = (150, 146, 150, 255)
BEARD: RGBA = (62, 54, 58, 255)
COAT: RGBA = (44, 44, 60, 255)
COAT_DARK: RGBA = (26, 26, 40, 255)
COAT_LIGHT: RGBA = (86, 88, 112, 255)
VEST: RGBA = (132, 136, 150, 255)
SHIRT: RGBA = (244, 242, 236, 255)
INK: RGBA = (26, 24, 30, 255)
GOLD: RGBA = (240, 196, 92, 255)
GOLD_DARK: RGBA = (176, 120, 50, 255)
TEAL: RGBA = (96, 200, 196, 255)
TEAL_DARK: RGBA = (40, 110, 124, 255)
BLANKET: RGBA = (70, 60, 110, 255)
BLANKET_DARK: RGBA = (44, 38, 78, 255)
STEEL: RGBA = (214, 224, 236, 255)
STEEL_DARK: RGBA = (124, 138, 160, 255)

#: The "hips" of this person are the points of his horse's shoulders: his
#: front legs start there. His own waist is at the withers, this far up.
WAIST = -15.0
BUILD = Build(hip_up=46.0, thigh=22.4, shin=21.4, neck=(1.0, WAIST - 35.0), upper=18.6, fore=17.6, near_shoulder=(-3.8, WAIST - 31.0), far_shoulder=(5.2, WAIST - 30.6),
              near_hip=(-2.6, 0.0), far_hip=(3.6, 0.0), head_up=(0.8, -12.4), height=120.0, half_width=(46.0, 16.0))

X = Person(TARGET_NAME, BUILD, cx=126.0)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0


def _torso(hem_back: int, hem_front: int):
    """The professor from his waist at the withers up, and the skirt of his
    coat, which lies on his own back."""
    hb, hf = float(hem_back), float(hem_front)

    def shape(d) -> None:
        K.poly(d, [K.at(-3.6, TOP), K.at(-7.6, TOP + 4.0), K.at(-8.2, WAIST - 20.0), K.at(-8.0, WAIST - 2.0), K.at(-13.0 - hb, WAIST + 7.0), K.at(10.6 + hf, WAIST + 8.0),
                   K.at(8.6, WAIST - 2.0), K.at(8.4, WAIST - 14.0), K.at(8.4, WAIST - 24.0), K.at(7.8, TOP + 3.0), K.at(4.0, TOP - 0.4)], _SOLID)
        K.oval(d, K.at(-3.4, WAIST - 30.4), 4.4, 5.0, _SOLID)
        K.oval(d, K.at(4.2, WAIST - 30.4), 3.8, 4.4, _SOLID)

    def paint(d) -> None:
        # The waistcoat and the shirt where the coat is open, and his bow tie.
        K.poly(d, [K.at(2.4, TOP), K.at(11.6, TOP), K.at(11.6, WAIST + 2.0), K.at(4.6, WAIST + 2.0), K.at(3.6, WAIST - 16.0)], VEST)
        K.poly(d, [K.at(9.4, TOP), K.at(12.6, TOP), K.at(12.6 + hf, WAIST + 8.0), K.at(10.0, WAIST + 8.0)], COAT_DARK)
        K.poly(d, [K.at(3.4, TOP - 1.0), K.at(8.8, TOP - 1.0), K.at(6.6, TOP + 7.0)], SHIRT)
        K.poly(d, [K.at(4.2, TOP + 1.6), K.at(6.0, TOP + 2.8), K.at(4.2, TOP + 4.4)], INK)
        K.poly(d, [K.at(8.0, TOP + 1.6), K.at(6.2, TOP + 2.8), K.at(8.0, TOP + 4.4)], INK)
        for y in (WAIST - 18.0, WAIST - 12.0, WAIST - 6.0):
            K.oval(d, K.at(6.4, y), 0.7, 0.7, INK)
        # The lapel, the seam of the coat, and the aleph on his chest.
        K.poly(d, [K.at(-0.6, TOP + 1.0), K.at(3.0, TOP), K.at(4.0, WAIST - 20.0), K.at(0.2, WAIST - 26.0)], COAT_LIGHT)
        K.line(d, [K.at(0.2, WAIST - 26.0), K.at(4.0, WAIST - 20.0), K.at(3.6, WAIST - 16.0), K.at(4.8, WAIST + 6.0)], COAT_DARK, 0.7)
        K.oval(d, K.at(0.2, WAIST - 20.0), 1.6, 1.6, GOLD, GOLD_DARK, 0.4)
        K.line(d, [K.at(-9.0, WAIST + 0.6), K.at(-12.0 - hb, WAIST + 6.0)], COAT_DARK, 0.6)

    return K.solid(("canter_torso", hem_back, hem_front), shape, COAT, paint, outline=1.3, rim=0.3, shade=0.4, shade_colour=COAT_DARK)


X.torso = _torso

NEAR_EYE = (2.0, -0.4)
FAR_EYE = (7.0, -0.6)


def _hair_shape(d) -> None:
    # Bare on top; hair at the sides and the back, and a beard to his collar.
    K.poly(d, [K.at(-7.8, -6.0), K.at(-9.6, -1.0), K.at(-8.4, 4.0), K.at(-5.0, 6.6), K.at(-3.0, 2.0)], _SOLID)
    K.poly(d, [K.at(-1.0, 4.0), K.at(9.6, 5.0), K.at(9.0, 11.0), K.at(5.0, 15.0), K.at(0.6, 12.6), K.at(-2.4, 8.0)], _SOLID)


def _hair(d) -> None:
    K.poly(d, [K.at(-20.0, -9.4), K.at(-4.6, -9.4), K.at(-2.6, -5.0), K.at(-2.4, -0.6), K.at(-5.0, -0.2), K.at(-5.6, 3.6), K.at(-4.2, 5.4), K.at(-20.0, 8.0)], HAIR)
    K.poly(d, [K.at(-9.0, -4.0), K.at(-3.4, -3.0), K.at(-3.6, 0.0), K.at(-9.0, 1.0)], HAIR_GREY)
    for strand in ([(-7.6, -7.0), (-5.0, -4.6)], [(-8.4, 2.0), (-6.0, 3.6)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_GREY, 0.5)


def _face(d) -> None:
    # His beard, and the lines of a man who has been told he is wrong.
    K.poly(d, [K.at(-1.6, 3.0), K.at(1.6, 4.6), K.at(4.4, 4.2), K.at(8.6, 4.8), K.at(9.6, 6.6), K.at(8.8, 11.0), K.at(5.0, 15.0), K.at(0.6, 12.6), K.at(-2.4, 8.0)], BEARD)
    K.line(d, [K.at(1.0, 8.0), K.at(3.0, 12.0)], HAIR_GREY, 0.5)
    K.line(d, [K.at(4.4, 8.6), K.at(5.4, 13.0)], HAIR_GREY, 0.5)
    K.line(d, [K.at(2.4, -7.6), K.at(5.0, -8.0), K.at(7.4, -7.6)], mix(SKIN, SKIN_DEEP, 0.5), 0.45)


_head = R.make_head(K, ("canter",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.8, 7.8, 9.2), jaw=(2.6, 4.2, 5.4, 7.6),
                    nose=((7.2, -1.0), (10.2, 2.8), (9.6, 4.2), (7.2, 4.6)), ear=(-4.8, 1.0, 2.2, 3.2), shape=_hair_shape, under=_hair, over=_face)
_eyes = R.make_eyes(K, NEAR_EYE, FAR_EYE, ink=INK, white=None, lid=SKIN_DEEP, size=1.0)
_brows = R.make_brows(K, [(-0.4, -3.4), (2.2, -4.6), (4.6, -3.4)], [(5.8, -3.6), (7.2, -4.6), (8.6, -4.0)], BEARD, 1.5)
_mouth = R.make_mouth(K, (6.0, 7.0), (150, 76, 76, 255), wide=0.6)

X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"), (_mouth(str(pose["mouth"])), "mouth")]
X.neck = R.make_neck(K, SKIN_SHADE, 4.6)
X.upper_arm = lambda near: [(0.0, 1.0, 6.6, 5.6, COAT if near else COAT_DARK)]
X.forearm = lambda near: [(0.0, 1.0, 5.6, 4.8, COAT if near else COAT_DARK), (0.84, 1.0, 5.0, 5.0, SHIRT)]
X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, size=1.0)
# His front legs: the forearm of a horse, a knee, and a dark cannon to the hoof.
X.thigh = lambda near: [(0.0, 1.0, 8.2, 5.4, HORSE if near else HORSE_DARK)]
X.shin = lambda near: [(0.0, 0.16, 5.8, 5.8, HORSE if near else HORSE_DARK), (0.1, 1.0, 4.6, 3.8, SOCK if near else SOCK_DARK)]


def _hoof(near: bool):
    def shape(d) -> None:
        K.poly(d, [K.at(-2.6, -1.6), K.at(2.4, -1.6), K.at(4.6, BUILD.ankle_up), K.at(-3.4, BUILD.ankle_up)], _SOLID)

    return K.solid(("hoof", near), shape, HOOF if near else mix(HOOF, SOCK, 0.4), None, outline=1.1, rim=0.2, shade=0.0)


X.shoe = _hoof

# ---- The horse of him ------------------------------------------------------------

#: Where his hind legs start, from the points of his shoulders, and how long
#: their two bones are.
HIND = (-43.0, -3.0)
HIND_UPPER = 21.0
HIND_LOWER = 24.0


def _barrel():
    """His barrel, from his chest back to his rump, the points of his
    shoulders at ``home``; and the blanket on it."""

    def shape(d) -> None:
        K.poly(d, [K.at(9.6, -6.0), K.at(8.6, -13.0), K.at(2.0, WAIST - 1.0), K.at(-12.0, WAIST + 1.0), K.at(-30.0, WAIST + 0.4), K.at(-44.0, WAIST - 0.6), K.at(-52.0, -9.0),
                   K.at(-53.0, -2.0), K.at(-49.0, 4.6), K.at(-40.0, 7.6), K.at(-22.0, 9.0), K.at(-6.0, 8.4), K.at(5.0, 5.6), K.at(9.6, 0.0)], _SOLID)

    def paint(d) -> None:
        # The light along his back, and the shade of his belly.
        K.poly(d, [K.at(-50.0, -11.0), K.at(-30.0, WAIST + 1.6), K.at(-6.0, WAIST + 2.0), K.at(-6.0, WAIST + 4.6), K.at(-30.0, WAIST + 4.0), K.at(-49.0, -7.6)], HORSE_LIGHT)
        K.poly(d, [K.at(-50.0, 3.0), K.at(-22.0, 6.0), K.at(4.0, 3.0), K.at(6.0, 8.0), K.at(-22.0, 12.0), K.at(-50.0, 9.0)], HORSE_DARK)
        # The blanket: sets inside sets.
        K.poly(d, [K.at(-30.0, WAIST + 0.6), K.at(-9.0, WAIST + 1.0), K.at(-10.0, 2.0), K.at(-29.0, 2.6)], BLANKET)
        K.line(d, [K.at(-30.0, WAIST + 0.6), K.at(-29.0, 2.6), K.at(-10.0, 2.0), K.at(-9.0, WAIST + 1.0)], GOLD_DARK, 0.7)
        for r, colour in ((6.4, GOLD), (4.4, TEAL), (2.4, GOLD)):
            K.oval(d, K.at(-19.6, -6.4), r, r * 0.86, None, colour, 0.6)  # type: ignore[arg-type]
        K.oval(d, K.at(-19.6, -6.4), 0.8, 0.8, TEAL)
        K.line(d, [K.at(-24.0, 2.4), K.at(-23.6, 8.0)], BLANKET_DARK, 1.2)

    return K.solid(("barrel",), shape, HORSE, paint, outline=1.3, rim=0.3, shade=0.0)


def _hind_feet(ctx):
    """Where his two hind hooves are, in the frame: on the ground under his
    rump, or in the step of the row."""
    root = (ctx.hip[0] + HIND[0], ctx.hip[1] + HIND[1])
    U = X.U
    if ctx.anim == "walk":
        near, far = R.stride(ctx.phase + math.pi / 2.0, 7.0, 3.6)
    elif ctx.anim == "countable_charge":
        near, far = R.stride(ctx.phase + math.pi / 2.0, 11.0, 5.0)
    else:
        near, far = (-3.0, 0.0, 0.0), (3.0, 0.0, 0.0)
    return root, [(root[0] + 3.0 + f[0] * U, ctx.ground + f[1] * U - BUILD.ankle_up) for f in (near, far)]


def _hind_leg(ctx, near: bool) -> List[Stamp]:
    root, feet = _hind_feet(ctx)
    hock, ankle = solve(root, feet[0 if near else 1], HIND_UPPER, HIND_LOWER, 1.0)
    tag = "near" if near else "far"
    out: List[Stamp] = []
    bones = ((root, hock, [(9.6, 6.0, HORSE if near else HORSE_DARK)]), (hock, ankle, [(4.8, 3.8, SOCK if near else SOCK_DARK)]))
    for edge in (True, False):
        for k, (a, b, parts) in enumerate(bones):
            for w0, w1, colour in parts:
                length = math.hypot(b[0] - a[0], b[1] - a[1])
                out.append((R.bone(K, f"hind_{tag}_{k}", length, w0, w1, colour, edge), a, f"hind_{tag}_{k}_{'edge' if edge else 'fill'}",
                            math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))))
    out.append((_hoof(near), ankle, f"hind_{tag}_hoof", 0.0))
    return out


def _behind(ctx) -> List[Stamp]:
    """His far hind leg, his tail and his barrel."""
    rump = (ctx.hip[0] - 52.0, ctx.hip[1] - 8.0)
    at = pin(rump)
    moving = ctx.anim in ("walk", "countable_charge")
    chains = [R.chain((rump[0] - at[0], rump[1] - at[1] + dy), 6, 5.0, (150.0 if moving else 108.0) + spread, wave=9.0 if moving else 3.0, curl=-6.0, phase=ctx.phase,
                      lead=lead) for dy, spread, lead in ((0.0, 0.0, 0.0), (1.6, 10.0, 1.2))]
    out = _hind_leg(ctx, False)
    out.append((R.ribbon(K, ("canter_tail",), chains, 4.4, MANE, (70, 60, 70, 255), taper=0.5), at, "tail", 0.0))
    out.append((_barrel(), ctx.hip, "barrel", 0.0))
    return out


X.layers["back"].append(_behind)
X.layers["under_torso"].append(lambda ctx: _hind_leg(ctx, True))

# ---- How he holds himself ----------------------------------------------------

#: One hand at his lapel.
X.set_rest(lean=0.0, na=(7.0, 9.0), nh="fist", nf=(-3.0, 0.0, 0.0), ff=(3.6, 0.0, 0.0))


@X.row
def idle(i: int, n: int):
    # He looks at something that goes on for ever, and one front hoof paws once.
    _, s, c = loop(i, n)
    paw = (2.5, -3.0, 0.0) if i in (5, 6) else (3.6, 0.0, 0.0)
    return P(hip=(0.0, 0.2 * s), head=(0.3, 0.0, -4.0 + 3.0 * c), eyes="closed" if i == n - 2 else "up" if c < 0.0 else "open", ff=paw, mouth="flat")


@X.row
def walk(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 7.0, 3.6)
    return P(hip=(0.3, 0.5 * math.cos(2.0 * ph)), lean=1.0, head=(0.2, 0.0, -2.0 + 1.0 * s), nf=nf, ff=ff)


@X.row
def talk(i: int, n: int):
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.2 * s), lean=1.0, head=(0.4, 0.0, 2.0 * s), na=(14.0 + 2.0 * c, 2.0 - 5.0 * max(0.0, s)), nh="point", mouth=("open", "flat", "big", "flat")[i % 4],
             brows=1.0 if s > 0.3 else -1.0)


#: The lance is level, and then it is down the diagonal.
COUCH = P(lean=-3.0, head=(0.0, 0.0, -4.0), na=(-6.0, 6.0), nab=-1.0, nh="fist", fa=(14.0, 8.0), fh="open", brows=-1.0, mouth="flat")
STRIKE = P(hip=(1.5, 0.5), lean=8.0, head=(0.6, 0.0, 6.0), na=(22.0, 12.0), nh="fist", fa=(-4.0, 16.0), brows=-1.0, mouth="grit")


@X.row
def diagonalize(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, P()), (0.2, COUCH), (0.4, COUCH), (0.55, STRIKE), (0.85, STRIKE), (1.0, P())])


@X.row
def countable_charge(i: int, n: int):
    # He runs, and counts.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 11.0, 5.0)
    return P(hip=(1.0, -1.0 * abs(s)), lean=10.0, head=(0.6, 0.0, 4.0), na=(20.0, -2.0), nh="point", fa=(-6.0, 14.0), fh="fist", nf=nf, ff=ff, brows=-1.0, mouth="open")


#: A hand held up and open: the set is over it.
HOLD = P(lean=-1.0, head=(0.3, 0.0, -8.0), na=(14.0, -6.0), nh="flat", eyes="up", brows=1.0, mouth="o")


@X.row
def power_set(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, P()), (0.2, HOLD), (0.85, dict(HOLD, na=(14.0, -8.0))), (1.0, P())])


#: Both arms up: he calls them down.
CALL = P(hip=(0.0, -0.5), lean=-4.0, head=(0.0, 0.0, -14.0), na=(-9.0, -22.0), nab=-1.0, fa=(15.0, -22.0), nh="open", fh="open", eyes="up", brows=1.0, mouth="big")


@X.row
def aleph_rain(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, P()), (0.25, CALL), (0.85, CALL), (1.0, P())])


@X.row
def hit(i: int, n: int):
    back = P(hip=(-2.0, 1.0), lean=-12.0, head=(-1.0, 0.0, -14.0), na=(-6.0, 4.0), nab=-1.0, fa=(12.0, 2.0), nh="open", fh="open", eyes="closed", mouth="grit", brows=-1.0,
             ff=(5.0, -4.0, 0.0))
    return X.keys(shot(i, n), [(0.0, P()), (0.3, back), (0.7, back), (1.0, P())])


@X.row
def death(i: int, n: int):
    # His legs fold under him, and he bows his head.
    kneel = P(hip=(1.0, 14.0), lean=14.0, head=(0.6, 1.0, 16.0), na=(4.0, 22.0), fa=(8.0, 22.0), nh="open", fh="open", eyes="closed", mouth="flat", brows=-1.0,
              nf=(8.0, 0.0, 0.0), ff=(12.0, 0.0, 0.0))
    down = dict(kneel, hip=(1.0, 22.0), lean=34.0, head=(1.0, 2.0, 28.0), nf=(13.0, 0.0, 0.0), ff=(17.0, 0.0, 0.0))
    return X.keys(shot(i, n), [(0.0, P()), (0.2, P(lean=-6.0, eyes="wide", mouth="o")), (0.55, kneel), (0.85, down), (1.0, down)])


@X.row
def taunt(i: int, n: int):
    # He rears a little, and points up: there is always a larger one.
    up = P(hip=(-1.0, -3.0), lean=-8.0, head=(0.0, 0.0, -10.0), na=(8.0, -24.0), nab=-1.0, nh="point", nf=(4.0, -9.0, 0.0), ff=(8.0, -6.0, 0.0), eyes="up", brows=1.0,
           mouth="smile")
    return X.keys(shot(i, n), [(0.0, P()), (0.3, up), (0.75, up), (1.0, P())])


X.rows = [("idle", 8, 132), ("walk", 8, 92), ("talk", 8, 104), ("diagonalize", 9, 76), ("countable_charge", 8, 74), ("power_set", 10, 84), ("aleph_rain", 8, 90),
          ("hit", 5, 84), ("death", 10, 112), ("taunt", 8, 98)]

# ---- What he shows -----------------------------------------------------------


def _lance():
    """His lance, along +x from the hand that holds it."""

    def shape(d) -> None:
        K.stroke(d, [K.at(-10.0, 0.0), K.at(30.0, 0.0)], _SOLID, 2.0)
        K.poly(d, [K.at(29.0, -2.4), K.at(38.0, 0.0), K.at(29.0, 2.4)], _SOLID)

    def detail(d) -> None:
        K.stroke(d, [K.at(-10.0, 0.0), K.at(29.0, 0.0)], GOLD_DARK, 1.4)
        K.oval(d, K.at(-2.0, 0.0), 2.0, 2.0, GOLD)

    return K.solid(("lance",), shape, STEEL, detail, outline=1.0, rim=0.0, shade=0.0)


def _table(struck: int):
    """A table of digits, and the line down its diagonal as far as row
    ``struck``."""

    def paint(d) -> None:
        for r in range(4):
            for c in range(4):
                on = (r * 3 + c * 5) % 2 == 0
                K.oval(d, K.at(c * 6.0, r * 6.0), 1.9, 1.9, OUTLINE)
                K.oval(d, K.at(c * 6.0, r * 6.0), 1.2, 1.2, TEAL if on else TEAL_DARK)
        if struck > 0:
            K.line(d, [K.at(-2.0, -2.0), K.at(struck * 6.0 - 4.0, struck * 6.0 - 4.0)], OUTLINE, 2.4)
            K.line(d, [K.at(-2.0, -2.0), K.at(struck * 6.0 - 4.0, struck * 6.0 - 4.0)], GOLD, 1.0)

    return K.aligned(("table", struck), paint)


def _sets(depth: int):
    """A set of ``depth`` things, and round it the set of its parts."""

    def paint(d) -> None:
        for k in range(depth):
            r = 4.0 + 4.0 * k
            K.oval(d, K.home, r, r * 0.8, None, OUTLINE, 2.2)  # type: ignore[arg-type]
            K.oval(d, K.home, r, r * 0.8, None, GOLD if k % 2 == 0 else TEAL, 0.9)  # type: ignore[arg-type]
        K.oval(d, K.home, 1.4, 1.4, TEAL)

    return K.aligned(("sets", depth), paint)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, i, u = ctx.anim, ctx.i, ctx.u
    if anim == "diagonalize":
        grip = math.degrees(math.atan2(ctx.hand[1] - ctx.elbow[1], ctx.hand[0] - ctx.elbow[0]))
        if 0.15 <= u <= 0.9:
            out.append((_lance(), ctx.hand, "lance", 0.0 if u < 0.45 else 45.0 if u >= 0.55 else grip))
        if u >= 0.2:
            struck = 0 if u < 0.5 else min(4, 1 + int((u - 0.5) / 0.08))
            out.append((_table(struck), pin((ctx.hip[0] + 34.0, ctx.hip[1] - 52.0)), "table", 0.0))
    elif anim == "countable_charge":
        for k in range(3):
            digit = str((i + 3 - k) % 9 + 1)
            out.append((R.glyph(K, digit, 8.0 - 1.2 * k, GOLD, GOLD_DARK), (ctx.hip[0] - 60.0 - 13.0 * k, ctx.hip[1] - 26.0 + 3.0 * ((i + k) % 2)), f"count_{k}", 0.0))
    elif anim == "power_set" and u >= 0.2:
        out.append((_sets(min(4, 1 + int((u - 0.2) / 0.16))), pin((ctx.hand[0] + 2.0, ctx.hand[1] - 22.0)), "sets", 0.0))
    elif anim == "aleph_rain" and u >= 0.2:
        for k in range(4):
            fall = ((u - 0.2) * 1.6 + k * 0.27) % 1.0
            out.append((R.glyph(K, ["aleph"], 9.0, GOLD, GOLD_DARK), (ctx.hip[0] - 34.0 + 22.0 * k, 16.0 + fall * (ctx.ground - 40.0)), f"aleph_{k}", 0.0))
    elif anim == "taunt" and 0.3 <= u <= 0.8:
        out.append((R.glyph(K, ["aleph"], 10.0, GOLD, GOLD_DARK), (ctx.hand[0] + 4.0, ctx.hand[1] - 14.0), "aleph", 0.0))
    return out


X.effects = _effects

ROWS = X.rows
FRAME_SIZE = X.frame
render_frame = X.render_frame
_render_frame = render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet."""
    del opts
    r8 = tuple(range(8))
    return X.portraits(out_dir, {
        "default": ("idle", r8, 148, True),
        "portrait": ("idle", (1,), 0, False),
        "talk": ("talk", r8, 104, True),
    }, still="portrait", view_width=38.0)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

del STEEL_DARK

if __name__ == "__main__":
    raise SystemExit(main())
