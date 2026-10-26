"""Sprite generator for Gottfried Leib-Knives: the courtier who wrote the
notation everybody still uses, and who cuts with it.

A parody of Gottfried Wilhelm Leibniz.

The look (2026-10-13): a man of the court of about 1700 seen three quarters
from the front, facing right. The great dark wig of his portraits, in curls
past his shoulders; a long face under it, a large nose, a small polite mouth.
A burgundy coat to his knees with gold at its edges, lace at his throat and
his wrists, dark breeches, white stockings, shoes with buckles and heels. Two
narrow blades: at rest they are in their sheaths at his hip, and he stands
with a hand on one of them; in the rows where he fights there is one in each
hand, the short one for a differential and the long one for the sweep of an
integral.

He is drawn from the portraits of the man and not from a type (Jon,
2026-10-13, of another person of this cast: "needs to read like paul erdos
not bearnie sanders"). He is a grown man, not a mascot. There is no drop
shadow.

What he shows: the long S of the integral, and dx.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, the blades, how he stands and what he writes
are his.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, lerp, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "leib_knives"
DISPLAY_NAME = "Gottfried Leib-Knives"

AUTHORING_DESCRIPTION = (
    "Gottfried Leib-Knives parodies Gottfried Wilhelm Leibniz, the German "
    "mathematician, philosopher, and polymath associated with the development "
    "of differential and integral calculus and with the d/dx and integral "
    "notation that became standard. The name turns Leibniz into Leib-Knives: "
    "a courtly dual-blade duelist whose paired weapons draw differentials and "
    "integral curves. His long dark curled peruke, lace cravat, formal coat, "
    "and diplomatic bearing are inspired by late-seventeenth-century portraits. "
    "The recurring priority-dispute jokes refer to Leibniz and Isaac Newton "
    "developing calculus independently and later partisans arguing over credit. "
    "The design should remain affectionate rather than depicting him as merely "
    "a plagiarist. Ambition treats humans, animals, machines, and fantastic "
    "figures as an ordinary mixed society, so his being human is never itself "
    "a joke or a subject of dialogue."
)

GAMEPLAY_DESCRIPTION = (
    "A light precision duelist built around two complementary blades. Fast "
    "differential cuts apply short-lived marks that represent local change; a "
    "wide integral sweep cashes accumulated marks into displacement and damage. "
    "Crosscut is a compact anti-rush tool, while notation creates a brief "
    "calculus glyph that alters the trajectory or timing of the next attack. "
    "He should reward spacing, sequencing, and exact timing rather than raw "
    "durability. The initial catalog entry uses the existing generic swipe kit "
    "until those mechanics receive dedicated runtime actions."
)

SUGGESTED_BARKS = {
    "on_hit": [
        "An infinitesimal cut still counts.",
        "You have mistaken notation for weakness.",
        "That was neither necessary nor sufficient.",
    ],
    "provoked": ["Very well. Let us differentiate."],
    "idle": [
        "A small difference, correctly placed, decides everything.",
        "I developed this stance independently.",
        "Good notation is a weapon against confusion.",
    ],
    "hall": [
        "Two blades, one calculus. The priority dispute is ongoing.",
        "My notation survived. I consider that a point.",
        "The best of all possible move sets is still being balanced.",
    ],
}

FALLBACK_DIALOGUE = [
    "I prefer notation that reveals the operation instead of concealing it. A symbol should do useful work.",
    "GNU Ton and I reached similar techniques by different roads. Posterity then paved the roads with arguments.",
    "A derivative tells you how quickly the present is becoming the future. In a duel, that is practical information.",
    "An integral gathers countless small changes into one result. Do not stand inside the result.",
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_leib_knives",
        "display_name": "Gottfried Leib-Knives",
    },
    "dialogue_hints": {
        "suggested_barks": [
            'An infinitesimal cut still counts.',
            'You have mistaken notation for weakness.',
            'That was neither necessary nor sufficient.',
            'Very well. Let us differentiate.',
        ],
        "fallback_dialogue": [
            'I prefer notation that reveals the operation instead of concealing it. A symbol should do useful work.',
            'GNU Ton and I reached similar techniques by different roads. Posterity then paved the roads with arguments.',
            'A derivative tells you how quickly the present is becoming the future. In a duel, that is practical information.',
            'An integral gathers countless small changes into one result. Do not stand inside the result.',
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "human",
            "mathematician",
            "polymath",
            "courtly_duelist",
            "dual_blades",
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
    "actions": {"default_preset": "striker_swipe"},
    "visual": {"default_pose": "idle"},
    "tags": [
        "human",
        "mathematician",
        "polymath",
        "courtly_duelist",
        "dual_blades",
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
            "source": "explicit.profile.humanoid",
            "point": {"x": 127.0, "y": 58.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 126.0, "y": 132.0},
        },
        "hand_l": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 92.0, "y": 162.0},
        },
        "hand_r": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 160.0, "y": 160.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 127.0, "y": 12.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "action.melee.primary": {"animation": "slash", "events": []},
        "action.melee.secondary": {"animation": "crosscut", "events": []},
        "action.special.primary": {"animation": "integral_sweep", "events": []},
        "action.special.secondary": {"animation": "notation", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
}

COAT: RGBA = (128, 40, 56, 255)
COAT_DARK: RGBA = (82, 24, 42, 255)
COAT_LIGHT: RGBA = (172, 70, 84, 255)
GOLD: RGBA = (238, 196, 96, 255)
GOLD_DARK: RGBA = (170, 118, 50, 255)
LACE: RGBA = (250, 248, 240, 255)
LACE_DARK: RGBA = (196, 196, 206, 255)
BREECHES: RGBA = (58, 50, 64, 255)
BREECHES_DARK: RGBA = (36, 30, 44, 255)
STOCKING: RGBA = (240, 236, 226, 255)
STOCKING_DARK: RGBA = (190, 186, 184, 255)
SHOE: RGBA = (44, 36, 40, 255)
SHOE_DARK: RGBA = (22, 18, 22, 255)
SKIN: RGBA = (238, 208, 186, 255)
SKIN_SHADE: RGBA = (208, 170, 150, 255)
SKIN_DEEP: RGBA = (162, 112, 102, 255)
WIG: RGBA = (60, 44, 44, 255)
WIG_LIGHT: RGBA = (110, 86, 80, 255)
INK: RGBA = (26, 22, 30, 255)
STEEL: RGBA = (214, 222, 236, 255)
STEEL_DARK: RGBA = (120, 130, 156, 255)
NOTE: RGBA = (255, 232, 150, 255)
NOTE_DARK: RGBA = (206, 136, 60, 255)

#: 168 cm, upright, a little stout under the coat.
BUILD = Build(hip_up=47.0, thigh=22.8, shin=21.5, neck=(0.4, -36.0), upper=18.8, fore=17.8, near_shoulder=(-5.6, -31.8), far_shoulder=(7.2, -31.4),
              near_hip=(-3.6, 0.0), far_hip=(3.6, 0.0), head_up=(1.0, -12.4), height=108.0, half_width=(13.0, 15.0))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
FRAME_SIZE = X.frame
TOP = BUILD.neck[1] - 2.0

R.STROKES.setdefault("d", (((0.9, 0.0), (0.9, 1.0)), ((0.9, 0.55), (0.55, 0.4), (0.15, 0.6), (0.15, 0.85), (0.55, 1.0), (0.9, 0.85))))


def _front(d, hb: float, hf: float) -> None:
    """Gold down the edge of the coat and round its hem, its buttons, the
    lace at his throat, and the two hilts at his hip."""
    K.poly(d, [K.at(5.4, TOP + 2.0), K.at(7.6, TOP + 2.0), K.at(9.2 + hf, 27.0), K.at(6.6 + hf * 0.6, 27.0)], GOLD)
    K.poly(d, [K.at(7.6, TOP + 2.0), K.at(12.6, TOP + 2.0), K.at(13.0 + hf, 27.0), K.at(9.2 + hf, 27.0)], COAT_DARK)
    K.poly(d, [K.at(-20.0 - hb, 22.6), K.at(20.0 + hf, 22.6), K.at(20.0 + hf, 25.0), K.at(-20.0 - hb, 25.0)], GOLD)
    for y in (-22.0, -15.0, -8.0, -1.0):
        K.oval(d, K.at(3.6, y), 1.0, 1.0, GOLD)
    K.poly(d, [K.at(1.6, TOP - 1.0), K.at(8.6, TOP - 1.0), K.at(8.0, TOP + 9.0), K.at(5.0, TOP + 12.0), K.at(2.2, TOP + 9.0)], LACE)
    for y in (TOP + 3.0, TOP + 6.4):
        K.line(d, [K.at(2.2, y), K.at(5.0, y + 1.4), K.at(8.0, y)], LACE_DARK, 0.5)
    K.line(d, [K.at(-8.4, -3.0), K.at(-2.0, -2.4)], COAT_DARK, 0.7)


X.torso = R.make_torso(K, ("leib",), COAT, COAT_DARK, back=(9.4, 9.8, 8.6, 11.8), front=(8.6, 10.4, 10.0, 11.4), hem_y=26.0, top=TOP,
                       shoulders=((-5.4, -31.2), (6.4, -31.0)), shoulder_r=(5.4, 5.0), belly=0.8, shade_from=40.0, detail=_front)


def _hilts(ctx) -> List[Stamp]:
    """The two blades in their sheaths at his hip, behind him, when he does
    not have them in his hands."""
    if float(ctx.pose["armed"]) > 0.5:
        return []

    def shape(d) -> None:
        for dy, long in ((0.0, 26.0), (3.0, 20.0)):
            K.stroke(d, [K.at(2.0, dy), K.at(-long, dy + long * 0.42)], WHITE, 2.2)
            K.stroke(d, [K.at(2.0, dy), K.at(7.0, dy - 2.2)], WHITE, 1.8)
            K.oval(d, K.at(2.6, dy - 0.2), 2.4, 2.4, WHITE)

    def detail(d) -> None:
        for dy in (0.0, 3.0):
            K.oval(d, K.at(2.6, dy - 0.2), 2.4, 2.4, GOLD)
            K.stroke(d, [K.at(3.0, dy - 0.4), K.at(7.0, dy - 2.2)], GOLD, 1.6)

    part = K.solid(("hilts",), shape, BREECHES_DARK, detail, outline=1.0, rim=0.2, shade=0.3, shade_colour=SHOE_DARK)
    return [(part, ctx.trunk(-6.0, -4.0), "hilts", ctx.lean)]


X.layers["under_torso"].append(_hilts)


def _wig_shape(d) -> None:
    # The great wig: high over his brow, and down past his shoulders in curls.
    K.oval(d, K.at(-1.4, -6.0), 10.8, 9.6, WHITE)
    for x, y, r in ((-9.6, 0.0, 4.2), (-10.0, 6.0, 4.2), (-9.4, 12.0, 4.0), (-7.6, 17.6, 3.6), (-3.0, 15.0, 3.4), (9.6, 9.0, 2.8), (9.0, 14.0, 2.6)):
        K.oval(d, K.at(x, y), r, r * 0.92, WHITE)


def _wig(d) -> None:
    K.poly(d, [K.at(20.0, -8.0), K.at(8.6, -8.0), K.at(6.0, -9.6), K.at(3.4, -8.2), K.at(1.0, -9.4), K.at(-1.2, -6.4), K.at(-2.6, -2.0), K.at(-2.4, 3.0),
               K.at(-1.4, 8.0), K.at(-0.6, 12.0), K.at(-0.6, 30.0), K.at(-30.0, 30.0), K.at(-30.0, -30.0), K.at(20.0, -30.0)], WIG)
    for x, y, r in ((-9.6, 0.0, 3.0), (-10.0, 6.0, 3.0), (-9.4, 12.0, 2.8), (-7.6, 17.6, 2.4), (-3.2, 15.0, 2.2), (-6.0, -6.0, 3.0), (-1.0, -11.6, 2.8),
                    (5.0, -12.0, 2.4), (-4.6, 8.0, 2.6)):
        K.oval(d, K.at(x, y), r, r * 0.85, None, WIG_LIGHT, 0.6)  # type: ignore[arg-type]


def _face(d) -> None:
    # The curls at the far side of his face.
    for x, y, r in ((9.6, 9.0, 2.6), (9.0, 14.0, 2.4)):
        K.oval(d, K.at(x, y), r, r * 0.9, WIG)
        K.oval(d, K.at(x, y), r * 0.6, r * 0.5, None, WIG_LIGHT, 0.5)  # type: ignore[arg-type]
    K.line(d, [K.at(4.8, 4.4), K.at(3.0, 6.4), K.at(2.8, 8.4)], mix(SKIN, SKIN_DEEP, 0.5), 0.5)


_head = R.make_head(K, ("leib",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.4, 8.0, 9.0), jaw=(2.6, 4.2, 5.6, 7.8),
                    nose=((7.2, -1.6), (11.2, 3.0), (10.4, 4.8), (7.2, 5.2)), ear=None, shape=_wig_shape, under=_wig, over=_face)
_eyes = R.make_eyes(K, (1.8, -0.6), (7.0, -0.8), ink=INK, iris=(70, 56, 44, 255), size=0.95, lid=SKIN_DEEP)
_brows = R.make_brows(K, [(-0.8, -4.0), (1.8, -4.8), (4.4, -4.2)], [(5.8, -4.4), (7.2, -4.8), (8.6, -4.2)], WIG, 1.1)
_mouth = R.make_mouth(K, (5.6, 8.2), (130, 60, 64, 255), wide=0.7)

X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"),
                              (_mouth(str(pose["mouth"])), "mouth")]
X.neck = R.make_neck(K, SKIN_SHADE, 4.6)
X.upper_arm = lambda near: [(0.0, 1.0, 7.4, 6.6, COAT if near else COAT_DARK)]
# A wide cuff, turned back.
X.forearm = lambda near: [(0.0, 0.62, 6.6, 6.2, COAT if near else COAT_DARK), (0.6, 1.0, 7.6, 7.2, COAT_LIGHT if near else COAT)]
X.thigh = lambda near: [(0.0, 1.0, 7.6, 6.4, BREECHES if near else BREECHES_DARK)]
X.shin = lambda near: [(0.0, 0.22, 6.4, 5.8, BREECHES if near else BREECHES_DARK), (0.2, 1.0, 5.2, 4.2, STOCKING if near else STOCKING_DARK)]
X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, LACE, LACE_DARK, size=0.95)


def _shoe(near: bool):
    h = K.home

    def shape(d) -> None:
        K.oval(d, K.at(2.8, 0.6), 6.0, 3.0, WHITE)
        K.rrect(d, h[0] - 3.4, h[1] - 0.4, h[0] + 8.6, h[1] + BUILD.ankle_up + 0.4, 1.4, WHITE)
        K.oval(d, h, 3.0, 2.8, WHITE)
        K.rrect(d, h[0] - 3.6, h[1] + BUILD.ankle_up - 1.0, h[0] - 0.8, h[1] + BUILD.ankle_up + 1.6, 0.3, WHITE)

    def detail(d) -> None:
        K.rrect(d, h[0] + 1.6, h[1] - 2.6, h[0] + 5.4, h[1] + 0.6, 0.4, GOLD, OUTLINE, 0.5)
        K.rrect(d, h[0] - 5.0, h[1] + BUILD.ankle_up - 0.2, h[0] + 10.0, h[1] + BUILD.ankle_up + 3.0, 0.0, SHOE_DARK)

    return K.solid(("court_shoe", near), shape, SHOE if near else mix(SHOE, SHOE_DARK, 0.6), detail, outline=1.2, rim=0.25, shade=0.3, shade_colour=SHOE_DARK)


X.shoe = _shoe

# ---- How he holds himself ----------------------------------------------------

#: A hand on the hilt at his hip. The other behind him.
ON_HILT = (-2.0, 17.0)
BEHIND = (-5.0, 22.5)
#: ``armed``: his blades are in his hands. ``nb``, ``fb``: how far each
#: blade turns from the line of its forearm.
X.set_rest(lean=-2.0, na=ON_HILT, nh="fist", fa=BEHIND, nf=(-3.8, 0.0, 0.0), ff=(4.8, 0.0, 0.0), armed=0.0, nb=0.0, fb=0.0)


@X.row
def idle(i: int, n: int):
    # A hand on a hilt, his weight on his back foot, his chin up: a courtier
    # waits well.
    _, s, c = loop(i, n)
    return P(hip=(-0.5, 0.3 + 0.3 * s), head=(0.2, 0.0, -3.0 + 2.0 * c), eyes="closed" if i == n - 2 else "open", brows=1.0 if c > 0.6 else 0.0)


@X.row
def walk(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 7.6, 4.4)
    return P(hip=(0.5, 0.8 * math.cos(2.0 * ph)), lean=0.0, head=(0.0, 0.0, 1.0 * s), fa=(2.0 + 6.0 * c, 24.0), nf=nf, ff=ff,
             hem=(1.0 + 1.5 * abs(c), 0.5 + 1.5 * abs(c)))


@X.row
def talk(i: int, n: int):
    # He turns his wrist to make a point, and the lace goes with it.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), head=(0.3, 0.0, 2.0 * s), na=(14.0 + 2.0 * c, 4.0 - 4.0 * max(0.0, s)), nh="open" if s > 0.0 else "point",
             mouth=("open", "smile", "o", "smile")[i % 4], brows=1.0 if s > 0.3 else 0.0)


#: On guard: side on, the long blade out in front, the short one low and back.
EN_GARDE = P(hip=(-1.0, 3.0), lean=2.0, na=(16.0, 6.0), fa=(-8.0, 14.0), nh="fist", fh="fist", nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), armed=1.0, nb=-14.0,
             fb=30.0, brows=-1.0, mouth="flat")


@X.row
def slash(i: int, n: int):
    # The short blade: a differential. A small cut, and it counts.
    wind = dict(EN_GARDE, na=(4.0, -12.0), nb=-60.0, lean=-4.0)
    cut = dict(EN_GARDE, hip=(4.0, 4.0), lean=12.0, na=(25.0, 8.0), nb=20.0, ff=(11.0, 0.0, 0.0), mouth="open", hem=(4.0, 1.0))
    return X.keys(shot(i, n), [(0.0, EN_GARDE), (0.25, wind), (0.5, cut), (0.75, cut), (1.0, EN_GARDE)])


@X.row
def crosscut(i: int, n: int):
    # Both, across each other.
    open_ = dict(EN_GARDE, lean=-4.0, na=(-6.0, -14.0), nab=-1.0, nb=-40.0, fa=(20.0, -12.0), fb=-150.0)
    shut = dict(EN_GARDE, hip=(3.0, 4.0), lean=10.0, na=(24.0, 10.0), nb=30.0, fa=(8.0, 14.0), fb=40.0, mouth="open", hem=(4.0, 1.0))
    return X.keys(shot(i, n), [(0.0, EN_GARDE), (0.25, open_), (0.5, shut), (0.8, shut), (1.0, EN_GARDE)])


@X.row
def integral_sweep(i: int, n: int):
    # The long blade, from low behind him to high in front: the long S.
    low = dict(EN_GARDE, hip=(-2.0, 6.0), lean=10.0, na=(-10.0, 20.0), nb=40.0)
    mid = dict(EN_GARDE, hip=(2.0, 3.0), lean=4.0, na=(22.0, 6.0), nb=-30.0, mouth="open")
    high = dict(EN_GARDE, hip=(3.0, 0.0), lean=-6.0, head=(0.0, 0.0, -10.0), na=(16.0, -22.0), nab=-1.0, arm="under", nb=-20.0, mouth="open", hem=(3.0, 2.0))
    return X.keys(shot(i, n), [(0.0, EN_GARDE), (0.2, low), (0.45, mid), (0.7, high), (0.85, high), (1.0, EN_GARDE)])


@X.row
def notation(i: int, n: int):
    # He writes it in the air with the point of the short blade, and it is clear.
    _, s, c = loop(i, n)
    return dict(X.full(EN_GARDE), hip=(0.0, 1.0), lean=0.0, na=(19.0 + 3.0 * c, -6.0 + 4.0 * s), nb=-10.0, fa=BEHIND, fb=80.0, mouth="smile", brows=1.0)


@X.row
def block(i: int, n: int):
    _, s, _c = loop(i, n)
    return dict(X.full(EN_GARDE), hip=(-2.0, 4.0 + 0.3 * s), lean=-4.0, na=(14.0, 2.0), nb=-80.0, fa=(16.0, 6.0), fb=-110.0)


@X.row
def hit(i: int, n: int):
    back = P(hip=(-2.0, 2.0), lean=-6.0, na=(4.0, 22.0), fa=(7.0, 21.0), eyes="wince", mouth="grit", armed=1.0, nb=30.0, fb=40.0)
    struck = dict(X.full(R.STRUCK), armed=1.0, nb=-40.0, fb=-60.0)
    return X.keys(shot(i, n), [(0.0, P(lean=-4.0, eyes="wide", mouth="o", armed=1.0)), (0.25, struck), (0.6, struck), (1.0, back)])


@X.row
def death(i: int, n: int):
    back = dict(X.full(R.STRUCK), lean=-12.0, armed=1.0, nb=-40.0, fb=-60.0)
    # His wig is under his head when he is down: he lies that much higher.
    down = dict(X.full(R.SUPINE), armed=0.0, off=(13.0, -7.0))
    return X.keys(shot(i, n), [(0.0, back), (0.2, dict(back, lean=-20.0)), (0.7, down), (1.0, down)])


@X.row
def taunt(i: int, n: int):
    # The salute: the blade up in front of his face, and a small bow.
    up = dict(X.full(EN_GARDE), hip=(0.0, 0.0), lean=-2.0, na=(11.0, -4.0), nb=-150.0, fa=BEHIND, fb=80.0, brows=1.0)
    bow = dict(up, hip=(-1.0, 2.0), lean=16.0, head=(1.0, 1.0, 8.0), na=(18.0, 12.0), nb=30.0, eyes="closed", mouth="smile")
    return X.keys(shot(i, n), [(0.0, EN_GARDE), (0.3, up), (0.5, up), (0.75, bow), (1.0, bow)])


X.rows = [("idle", 8, 132), ("walk", 8, 96), ("talk", 8, 106), ("slash", 7, 70), ("crosscut", 8, 66), ("integral_sweep", 9, 72), ("notation", 8, 92),
          ("block", 6, 82), ("hit", 5, 86), ("death", 8, 110), ("taunt", 8, 96)]

# ---- From the front ------------------------------------------------------------

_CURLS = [(sx * x, y, r) for sx in (-1.0, 1.0) for x, y, r in ((9.4, 0.0, 4.0), (10.0, 6.0, 4.0), (9.6, 12.0, 3.8), (8.4, 17.6, 3.4))]


def _front_coat(d) -> None:
    """His coat from the front: gold down each edge and round its hem, its
    buttons, and the lace at his throat."""
    K.poly(d, [K.at(-1.6, TOP + 2.0), K.at(1.6, TOP + 2.0), K.at(2.6, 27.0), K.at(-2.6, 27.0)], COAT_DARK)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(1.6 * sx, TOP + 2.0), K.at(3.2 * sx, TOP + 2.0), K.at(4.4 * sx, 27.0), K.at(2.6 * sx, 27.0)], GOLD)
        for y in (-20.0, -13.0, -6.0, 1.0):
            K.oval(d, K.at(5.6 * sx, y), 0.9, 0.9, GOLD)
    K.poly(d, [K.at(-20.0, 22.6), K.at(20.0, 22.6), K.at(20.0, 25.0), K.at(-20.0, 25.0)], GOLD)
    K.poly(d, [K.at(-3.8, TOP - 1.0), K.at(3.8, TOP - 1.0), K.at(3.2, TOP + 9.0), K.at(0.0, TOP + 12.4), K.at(-3.2, TOP + 9.0)], LACE)
    for y in (TOP + 3.0, TOP + 6.4):
        K.line(d, [K.at(-3.2, y), K.at(0.0, y + 1.4), K.at(3.2, y)], LACE_DARK, 0.5)


def _front_wig_shape(d) -> None:
    # The great wig: high over his brow, and down past each shoulder in curls.
    K.oval(d, K.at(0.0, -6.4), 11.0, 9.8, WHITE)
    for x, y, r in _CURLS:
        K.oval(d, K.at(x, y), r, r * 0.92, WHITE)


def _front_wig(d) -> None:
    K.poly(d, [K.at(-30.0, -30.0), K.at(30.0, -30.0), K.at(30.0, -2.0), K.at(7.2, -2.0), K.at(6.4, -6.0), K.at(3.6, -8.2), K.at(0.0, -6.6), K.at(-3.6, -8.2),
               K.at(-6.4, -6.0), K.at(-7.2, -2.0), K.at(-30.0, -2.0)], WIG)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(7.2 * sx, -2.0), K.at(6.8 * sx, 3.0), K.at(5.4 * sx, 7.0), K.at(4.8 * sx, 30.0), K.at(30.0 * sx, 30.0), K.at(30.0 * sx, -2.0)], WIG)
    for x, y, r in _CURLS + [(-5.4, -11.0, 3.0), (0.0, -13.0, 2.8), (5.4, -11.0, 3.0)]:
        K.oval(d, K.at(x, y), r * 0.7, r * 0.6, None, WIG_LIGHT, 0.6)  # type: ignore[arg-type]


def _front_nose(d) -> None:
    K.line(d, [K.at(-0.3, 0.0), K.at(-1.4, 3.8), K.at(0.0, 4.8), K.at(1.4, 3.8)], SKIN_DEEP, 0.7)


X.front_torso = R.make_front_torso(K, ("leib",), COAT, COAT_DARK, [(TOP, 4.4), (TOP + 3.6, 9.6), (-24.0, 10.2), (-6.0, 9.6), (26.0, 12.4)],
                                   shoulder=(7.6, -31.4, 4.6, 5.0), detail=_front_coat)
X.front_head_layers = R.front_face(R.make_front_head(K, ("leib",), SKIN, SKIN_DEEP, wide=7.6, jaw=6.4, chin=4.4, ears=None, shape=_front_wig_shape, hair=_front_wig,
                                                    face=_front_nose),
                                   R.make_front_eyes(K, ("leib",), ink=INK, iris=(70, 56, 44, 255), spread=3.3, y=-0.6, size=0.95),
                                   R.make_front_brows(K, ("leib",), WIG, spread=3.3, y=-4.2, width=1.2),
                                   R.make_front_mouth(K, ("leib",), y=8.4, colour=(130, 60, 64, 255), wide=0.65))
X.front_shoe = R.make_front_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up)
X.front_span = (8.2, 4.6)
R.add_front_rows(X)

# ---- His blades, and what he writes -------------------------------------------


def _blade(length: int):
    """A narrow blade along +x from his hand, with its guard."""

    def shape(d) -> None:
        K.poly(d, [K.at(2.0, -1.1), K.at(float(length), 0.0), K.at(2.0, 1.1)], WHITE)
        K.rrect(d, K.home[0] - 3.4, K.home[1] - 1.2, K.home[0] + 2.4, K.home[1] + 1.2, 0.6, WHITE)
        K.oval(d, K.at(2.6, 0.0), 1.4, 3.6, WHITE)

    def detail(d) -> None:
        K.rrect(d, K.home[0] - 4.0, K.home[1] - 2.0, K.home[0] + 2.2, K.home[1] + 2.0, 0.0, GOLD)
        K.oval(d, K.at(2.6, 0.0), 1.4, 3.6, GOLD)
        K.line(d, [K.at(4.0, 0.3), K.at(float(length) - 2.0, 0.2)], STEEL_DARK, 0.4)

    return K.solid(("blade", length), shape, STEEL, detail, outline=0.9, rim=0.4, shade=0.3, shade_colour=STEEL_DARK)


def _blades(ctx) -> List[Stamp]:
    if float(ctx.pose["armed"]) < 0.5:
        return []
    out: List[Stamp] = []
    for name, hand, elbow, key, length in (("far_blade", ctx.far_hand, ctx.far_elbow, "fb", 26), ("near_blade", ctx.hand, ctx.elbow, "nb", 34)):
        turn = math.degrees(math.atan2(hand[1] - elbow[1], hand[0] - elbow[0])) + float(ctx.pose[key])
        out.append((_blade(length), hand, name, turn))
    return out


def _tip(ctx, key: str = "nb", length: float = 34.0):
    hand, elbow = (ctx.hand, ctx.elbow) if key == "nb" else (ctx.far_hand, ctx.far_elbow)
    a = math.atan2(hand[1] - elbow[1], hand[0] - elbow[0]) + math.radians(float(ctx.pose[key]))
    return (hand[0] + length * math.cos(a), hand[1] + length * math.sin(a))


def _effects(ctx) -> List[Stamp]:
    out = _blades(ctx)
    anim, u = ctx.anim, ctx.u
    if anim == "slash" and 0.4 <= u <= 0.8:
        tip = _tip(ctx)
        out.append((R.swoosh(K, 16.0, -80, 40, 5.0, NOTE, NOTE_DARK), (tip[0] - 10.0, tip[1] - 4.0), "swoosh", 0.0))
        out.append((R.glyph(K, ["d", "x"], 8.0, NOTE, NOTE_DARK), (tip[0] + 12.0, tip[1] - 6.0), "dx", 0.0))
    elif anim == "crosscut" and 0.4 <= u <= 0.85:
        mid = ((ctx.hand[0] + ctx.far_hand[0]) / 2.0 + 24.0, (ctx.hand[1] + ctx.far_hand[1]) / 2.0 - 2.0)
        out.append((R.glyph(K, "x", 16.0, NOTE, NOTE_DARK, width=2.4), mid, "cross", 0.0))
    elif anim == "integral_sweep" and 0.4 <= u <= 0.9:
        size = 30.0 + round(14.0 * min(1.0, (u - 0.4) / 0.35))
        out.append((R.glyph(K, ["integral"], size, NOTE, NOTE_DARK, width=3.0), (ctx.hip[0] + 34.0, ctx.hip[1] - 18.0), "integral", 0.0))
    elif anim == "notation":
        tip = _tip(ctx)
        shown = ["integral", "d", "x"][: 1 + min(2, ctx.i // 2)]
        out.append((R.glyph(K, shown, 11.0, NOTE, NOTE_DARK), (ctx.head[0] + 34.0, ctx.head[1] - 14.0), "written", 0.0))
        out.append((R.dust(K, 1.2, NOTE, NOTE_DARK), tip, "spark", 0.0))
    elif anim == "block" and ctx.i % 3 == 1:
        out.append((R.burst(K, 6.0, STEEL, STEEL_DARK, 6), _tip(ctx, "nb", 20.0), "ring", 0.0))
    return out


X.effects = _effects

ROWS = X.rows
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)

# ---- In the round (``_round_cast``) --------------------------------------------
#
# His trunk and head in 3D come from the numbers of his own makers
# (``auto_trunk``, ``auto_head``); what they do not say is here, as data.
# His rows do not use this.

import numpy as np  # noqa: E402

from . import _person_round as O  # noqa: E402
from . import _round_cast as C  # noqa: E402
from . import _round_wear as W  # noqa: E402


#: The great wig over his head, and its curls down past his shoulders each
#: side and behind.
_WIG = ((0.0, -5.6, -1.6), (10.8, 9.6, 10.0))
_WIG_CURLS = ([((sx * x, y, z), (r, r * 0.92, r)) for sx in (-1.0, 1.0) for x, y, r in ((9.4, 0.0, 4.0), (10.0, 6.0, 4.0), (9.6, 12.0, 3.8), (8.4, 17.6, 3.4))
               for z in (-1.0, -5.0)]
              + [((x, y, -8.6 + 0.4 * abs(x) / 6.0), (4.0, 3.8, 3.4)) for x, y in ((-6.0, 2.4), (0.4, 1.6), (6.2, 2.8), (-3.2, 8.4), (3.4, 7.8),
                                                                             (-6.4, 14.0), (-0.2, 14.6), (5.8, 13.6))])


def _curl(centre, radii):
    """The light ring of a curl, on its outside (away from his middle)."""
    out = np.array([centre[0], 0.0, centre[2] + 4.0])
    out /= np.linalg.norm(out)
    return O.circle(tuple(np.asarray(centre) + out * 0.8 * radii[0]), tuple(out), radii[0] * 0.55, WIG_LIGHT, 0.6, slack=1.0)


# His head from the side, drawn as the cast draws a head in the numbers of a
# profile: the wig high over his brow and down behind in curls, his long nose.


def _side_wig_shape(d) -> None:
    K.oval(d, K.at(-2.6, -6.0), 11.2, 9.6, WHITE)
    for x, y, r in ((-10.4, 0.0, 4.2), (-10.8, 6.0, 4.2), (-10.2, 12.0, 4.0), (-8.4, 17.6, 3.6), (-3.6, 15.0, 3.4)):
        K.oval(d, K.at(x, y), r, r * 0.92, WHITE)


def _side_wig(d) -> None:
    K.poly(d, [K.at(20.0, -8.0), K.at(9.4, -8.0), K.at(6.8, -9.6), K.at(4.2, -8.2), K.at(1.8, -9.4), K.at(0.4, -6.4), K.at(-0.4, -2.0), K.at(0.0, 3.0),
               K.at(0.8, 8.0), K.at(1.2, 12.0), K.at(1.2, 30.0), K.at(-30.0, 30.0), K.at(-30.0, -30.0), K.at(20.0, -30.0)], WIG)
    for x, y, r in ((-10.4, 0.0, 3.0), (-10.8, 6.0, 3.0), (-10.2, 12.0, 2.8), (-8.4, 17.6, 2.4), (-3.8, 15.0, 2.2), (-6.8, -6.0, 3.0), (-1.8, -11.6, 2.8),
                    (4.2, -12.0, 2.4), (-4.2, 6.0, 2.6), (-3.4, 0.0, 2.4)):
        K.oval(d, K.at(x, y), r, r * 0.85, None, WIG_LIGHT, 0.6)  # type: ignore[arg-type]


_side_head = R.make_head(K, ("leib_side",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.4, 9.0, 9.0), jaw=(3.4, 4.2, 6.2, 7.8),
                         nose=((8.0, -1.6), (12.0, 3.0), (11.2, 4.8), (8.0, 5.2)), ear=None, shape=_side_wig_shape, under=_side_wig,
                         over=lambda d: K.line(d, [K.at(6.0, 4.4), K.at(4.4, 6.4), K.at(4.2, 8.4)], mix(SKIN, SKIN_DEEP, 0.5), 0.5), far_shade=False)
_side_eyes = R.make_eyes(K, (6.2, -0.6), None, ink=INK, iris=(70, 56, 44, 255), size=0.95, lid=SKIN_DEEP)
_side_brows = R.make_brows(K, [(4.0, -4.0), (6.2, -4.8), (8.4, -4.2)], None, WIG, 1.1)
_side_mouth = R.make_mouth(K, (8.2, 8.2), (130, 60, 64, 255), wide=0.5)


def _sheaths(length: int):
    """His two blades in their sheaths, along +x from their hilts."""
    n = float(length)

    def shape(d) -> None:
        for dy, k in ((0.0, 1.0), (2.8, 0.78)):
            K.stroke(d, [K.at(0.0, dy), K.at(n * k, dy)], WHITE, 2.2)
            K.stroke(d, [K.at(0.0, dy), K.at(-5.0, dy - 0.6)], WHITE, 1.8)
            K.oval(d, K.at(-0.4, dy), 2.4, 2.4, WHITE)

    def detail(d) -> None:
        for dy in (0.0, 2.8):
            K.oval(d, K.at(-0.4, dy), 2.4, 2.4, GOLD)
            K.stroke(d, [K.at(-0.8, dy - 0.2), K.at(-5.0, dy - 0.6)], GOLD, 1.6)

    return K.solid(("sheaths", length), shape, BREECHES_DARK, detail, outline=1.0, rim=0.2, shade=0.3, shade_colour=SHOE_DARK)


ROUND = C.Round(
    DISPLAY_NAME, C.PersonBody(X, R.make_back_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up), heads={"side": lambda pose: [(_side_head(), "head"), (_side_eyes(str(pose["eyes"])), "eyes"),
                                                               (_side_brows(R.brow_mood(pose)), "brows"), (_side_mouth(str(pose["mouth"])), "mouth")]}),
    C.Look(
        # The great dark wig: all of his head but his face, high over his
        # brow, in curls past his shoulders each side and down his back.
        C.auto_head(X, _head, _eyes,
                    hair=lambda u, v: (v < -8.0 + 1.6 * np.clip(np.abs(u) / 60.0, 0.0, 1.0)) | (np.abs(u) > 58.0),
                    hair_colour=WIG, hair_shade=mix(WIG, INK, 0.4), volumes=[_WIG] + _WIG_CURLS,
                    lines=[_curl(c, r) for c, r in _WIG_CURLS]
                    # and the curls over his crown, as his own art has them.
                    + [O.circle(*O.on_ellipsoid(*_WIG, u, v, 0.2), 2.2, WIG_LIGHT, 0.6, slack=1.0)
                       for u, v in ((-150.0, -10.0), (-100.0, -12.0), (-40.0, -14.0), (30.0, -14.6), (95.0, -11.6), (155.0, -9.0), (180.0, -2.0),
                                    (-120.0, -4.0), (125.0, -3.0))]),
        # His burgundy coat to his knees: gold down its edges and round its
        # hem, gold buttons each side, the lace at his throat.
        C.auto_trunk(X, [W.Strip(0.0, TOP + 2.0, 27.0, 3.2, GOLD, flare=1.2), W.Strip(0.0, TOP + 2.0, 27.0, 1.6, COAT_DARK, flare=1.0),
                         W.Buttons(32.0, -20.0, 1.0, 4, 0.9, GOLD), W.Buttons(-32.0, -20.0, 1.0, 4, 0.9, GOLD), W.Band(22.6, 25.0, GOLD),
                         W.Strip(0.0, TOP - 1.0, TOP + 12.4, 3.8, LACE, flare=-3.8), W.Down(180.0, 0.0, 26.0, COAT_DARK)]),
        # His blades in their sheaths at his near hip, their hilts forward.
        back_pieces=[W.Prop("sheaths", (-10.6, -2.0, 4.0), (-10.6, 9.0, -20.0), _sheaths, lead=1.0)]),
    # His near hand on a hilt, his far hand behind his back.
    C.Stance(hands={"r": C.Hand(l=-10.0, at=(-11.4, -3.0, 6.0), mode="fist"), "l": C.Hand(l=4.0, at=(3.0, -2.0, -11.0))}, stagger=2.0))


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
