"""Sprite generator for Joseph Furrier: he is cold, and he hears the parts a
sound is made of.

An affectionate caricature of Joseph Fourier.

The look (2026-10-13): a man of fifty in a very large blanket, seen three
quarters from the front, facing right. The blanket is his outline: dark
blue, as thick as a coat and as long as one, with fur along each edge and a
roll of fur at his neck. He holds it shut at his chest with both hands, and
his shoulders are up. Under it a cream shirt with a high collar, dark
trousers and brown shoes. Short dark curls, a round mild face, and a nose
that is pink with the cold.

THE DESIGN ELEMENTS A REDRAW MUST KEEP (Jon, 2026-10-13: "Joseph Furrier
needs to have some idle sprites where he is wrapped in a blanket. We lost
that detail from the original ... That detail should be noted in the comments
for his generator ... so we know what the important design elements for the
character are if we ever decide to rework him again."):

1. THE BLANKET, AND HE IS WRAPPED IN IT. It is the joke of the character (the
   story that Fourier kept himself wrapped up for warmth) and it is his
   outline. When he does nothing he is IN it: it is round him and over the
   back of his head, his arms are inside, and one hand holds it shut. It is a
   blanket, not a coat: it has no sleeves and no buttons when it is wrapped.
   It opens only when he does something (he talks, he strikes, he casts).
2. THE FUR along the edges of the blanket: that is the fur of "Furrier". He
   is a man and not a fox.
3. HE IS COLD: a pink nose, shoulders up, and now and then he shakes.
4. THE STEPS are in the rows that are their own (``step_function``,
   ``spectral_descent``) and never in how he stands.
5. THE WAVES: one wave that comes apart into its parts.

He is a man and not a fox: the fur of his name is the fur of the blanket.
He is a grown man, not a mascot. He holds nothing; there is no drop shadow.

What he shows: the snap of the blanket; steps (a function that goes up by
steps), which are in the rows that are their own and not in how he stands;
one wave that comes apart into the waves it is made of; and a rough wave
that he makes smooth.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, how he stands and what he shows are his. His
portraits are frames of this sheet.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import WHITE, RGBA, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "joseph_furrier"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Joseph Furrier"
USES_DROP_SHADOW = False
USES_PROPS = False

authoring_description = (
    "Joseph Furrier is a transformative parody of French mathematician and "
    "physicist Joseph Fourier. The oversized blanket is inspired by the "
    "commonly repeated biographical anecdote that Fourier habitually kept "
    "himself heavily wrapped for warmth; Ambition exaggerates that private "
    "eccentricity into his permanent bundled silhouette. The name's furrier "
    "pun is expressed through the blanket's thick trim rather than by turning "
    "Fourier into an animal. Stair shapes are deliberately limited to the "
    "step_function and spectral_descent gameplay actions: they are a game-facing "
    "homage to stepwise/discrete approximation and platforming, not another "
    "claim about Fourier's life. The spectral lining, separated color bands, "
    "wave attacks, and low-pass defensive posture draw on Fourier analysis, "
    "frequency decomposition, and filtering. The overall tone is dark, cold, "
    "and eccentric, but affectionate rather than horrific."
)

ACTOR_METADATA = {
    "authoring_description": authoring_description,
    "actor": {
        "character_id": "npc_joseph_furrier",
        "display_name": "Joseph Furrier",
    },
    "lineage": {
        "family": "joseph_furrier",
        "variant": "blanket_harmonic_eccentric",
        "creator": {"kind": "model", "model": "GPT-5.6 Thinking"},
        "method": "procedural_python_pillow",
    },
    "dialogue_hints": {
        "suggested_barks": [
            'Everything decomposes. Be patient.',
            'That was a single frequency. Rude.',
            'Heat always finds the edges.',
            'I am cold. This is not a metaphor.',
        ],
        "fallback_dialogue": [
            'Any shape at all, given enough simple waves. It sounds like a trick until you check it.',
            'I wrapped myself in blankets and studied how warmth leaves a room. The two facts are related.',
            'A sharp corner costs infinitely many terms. Corners usually do.',
            'People hear a chord. I hear the sum.',
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "mathematician",
            "blanket_wrapped",
            "harmonic_caster",
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
        "blanket_wrapped",
        "harmonic_caster",
        "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 64.0, "y": 29.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 64.0, "y": 64.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 48.0, "y": 73.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 82.0, "y": 73.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 64.0, "y": 5.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "blanket_snap", "events": []},
        "action.ranged.primary": {"animation": "harmonic_split", "events": []},
        "action.special.primary": {"animation": "step_function", "events": []},
        "action.special.secondary": {"animation": "spectral_descent", "events": []},
        "action.defense.block": {"animation": "low_pass_lament", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
}

OUTLINE = (18, 18, 24, 255)
SKIN: RGBA = (226, 190, 160, 255)
SKIN_SHADE: RGBA = (190, 146, 124, 255)
SKIN_DEEP: RGBA = (150, 100, 90, 255)
NOSE: RGBA = (232, 150, 140, 255)
HAIR: RGBA = (55, 48, 51, 255)
HAIR_LIGHT: RGBA = (104, 90, 92, 255)
INK: RGBA = (26, 23, 26, 255)
SHIRT: RGBA = (232, 226, 206, 255)
TROUSER: RGBA = (50, 52, 66, 255)
TROUSER_DARK: RGBA = (32, 34, 46, 255)
SHOE: RGBA = (88, 60, 48, 255)
SHOE_DARK: RGBA = (52, 36, 32, 255)
BLANKET: RGBA = (52, 60, 96, 255)
BLANKET_LIGHT: RGBA = (88, 100, 144, 255)
BLANKET_DARK: RGBA = (34, 38, 64, 255)
LINING: RGBA = (132, 52, 72, 255)
FUR: RGBA = (206, 194, 170, 255)
FUR_LIGHT: RGBA = (238, 230, 212, 255)
FUR_DARK: RGBA = (146, 132, 114, 255)
GOLD: RGBA = (236, 190, 92, 255)
GOLD_DARK: RGBA = (170, 116, 50, 255)
BANDS = ((83, 177, 217, 255), (87, 201, 177, 255), (150, 112, 203, 255), (205, 82, 100, 255))
BAND_DARK: RGBA = (40, 60, 96, 255)
DAMP: RGBA = (150, 176, 214, 255)

#: 168 cm, and wide: most of the width is blanket.
BUILD = Build(hip_up=48.0, thigh=23.2, shin=22.2, neck=(0.6, -34.4), upper=18.6, fore=17.6, near_shoulder=(-4.2, -30.4), far_shoulder=(5.6, -30.0),
              near_hip=(-3.4, 0.0), far_hip=(3.4, 0.0), head_up=(0.8, -12.0), height=108.0, half_width=(14.0, 15.0))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0
#: How far under his hips the blanket hangs.
HEM = 27.0


def _tufts(d, points, r: float = 2.2) -> None:
    """A line of fur: tufts, each with its light."""
    for x, y in points:
        K.oval(d, K.at(x, y), r, r * 0.9, FUR)
    for x, y in points[::2]:
        K.oval(d, K.at(x - 0.4, y - 0.6), r * 0.5, r * 0.45, FUR_LIGHT)


def _front(d, hb: float, hf: float) -> None:
    """The fur at each edge of the blanket and at his neck, the folds of it,
    and a little of his shirt where it does not meet."""
    K.poly(d, [K.at(4.0, TOP + 2.0), K.at(8.6, TOP + 2.0), K.at(7.4, TOP + 9.0), K.at(5.0, TOP + 9.0)], SHIRT)
    # The edge that is over the other one, from his neck to the hem.
    edge = [(4.4 + 0.5 * math.sin(k * 0.9), TOP + 8.0 + k * 3.8) for k in range(int((HEM - TOP - 8.0) / 3.8) + 1)]
    K.line(d, [K.at(x - 2.4, y) for x, y in edge], BLANKET_DARK, 0.8)
    _tufts(d, edge)
    # The hem.
    _tufts(d, [(x, HEM - 2.0 + 0.4 * math.sin(x)) for x in [-13.0 + 3.4 * k for k in range(10)]], 2.4)
    # The roll at his neck.
    _tufts(d, [(-4.0, TOP + 3.0), (-0.6, TOP + 4.4), (3.0, TOP + 4.8), (6.6, TOP + 4.4), (9.6, TOP + 3.0)], 3.0)
    for x0, x1 in ((-7.0, -9.0), (10.0, 12.6)):
        K.line(d, [K.at(x0, -18.0), K.at(x1 + (hf if x0 > 0 else -hb) * 0.4, HEM - 6.0)], BLANKET_DARK, 0.6)
    K.line(d, [K.at(-3.0, -20.0), K.at(-4.6, 8.0)], BLANKET_LIGHT, 0.5)


X.torso = R.make_torso(K, ("furrier",), BLANKET, BLANKET_DARK, back=(9.4, 10.2, 10.2, 12.4), front=(9.6, 10.0, 10.6, 12.6), hem_y=HEM, top=TOP,
                       shoulders=((-4.6, -30.0), (5.6, -30.0)), shoulder_r=(5.6, 4.6), shade_from=40.0, detail=_front)

NEAR_EYE = (1.8, -0.6)
FAR_EYE = (7.0, -0.8)


def _hair_shape(d) -> None:
    # Short curls: the edge of his head is not a smooth line.
    K.oval(d, K.at(-0.6, -5.8), 8.8, 6.8, WHITE)
    for x, y, r in ((-7.6, -6.0, 2.6), (-8.4, -2.0, 2.4), (-7.0, 2.0, 2.2), (-4.0, -11.0, 2.6), (0.6, -12.4, 2.6), (5.0, -11.4, 2.6), (8.0, -8.4, 2.2)):
        K.oval(d, K.at(x, y), r, r, WHITE)


def _hair(d) -> None:
    K.poly(d, [K.at(20.0, -8.6), K.at(8.6, -8.6), K.at(6.0, -6.8), K.at(3.0, -8.0), K.at(0.0, -6.4), K.at(-2.4, -3.4), K.at(-2.6, -0.4), K.at(-5.2, -0.2),
               K.at(-5.8, 3.6), K.at(-4.6, 5.0), K.at(-20.0, 5.4), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
    for x, y in ((-5.0, -8.0), (-1.0, -10.0), (3.6, -9.6), (-7.0, -3.0), (6.6, -8.6)):
        K.line(d, [K.at(x - 1.4, y + 0.8), K.at(x, y - 0.8), K.at(x + 1.4, y + 0.6)], HAIR_LIGHT, 0.6)


def _face(d) -> None:
    # His nose is pink with the cold, and so is his cheek.
    K.oval(d, K.at(9.0, 3.0), 1.5, 1.4, NOSE)
    K.oval(d, K.at(3.4, 4.0), 2.0, 1.3, mix(SKIN, NOSE, 0.45))


_head = R.make_head(K, ("furrier",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.4, 8.0, 9.0), jaw=(2.4, 4.0, 5.8, 7.2),
                    nose=((7.2, -0.8), (10.0, 2.6), (9.6, 4.2), (7.2, 4.6)), ear=(-4.8, 1.0, 2.2, 3.2), shape=_hair_shape, under=_hair, over=_face)
_eyes = R.make_eyes(K, (NEAR_EYE[0] + 0.2, NEAR_EYE[1] + 0.2), (FAR_EYE[0] + 0.1, FAR_EYE[1] + 0.2), ink=INK, white=None, lid=SKIN_DEEP, size=1.0)
_brows = R.make_brows(K, [(-0.8, -4.0), (1.8, -4.8), (4.4, -4.0)], [(5.8, -4.2), (7.2, -4.6), (8.6, -4.0)], HAIR, 1.3)
_mouth = R.make_mouth(K, (5.6, 7.2), (118, 67, 65, 255), wide=0.8)

def _hood():
    """The blanket over the back and the top of his head, when he is wrapped
    in it: his face and the curls over his brow are out of it."""

    def shape(d) -> None:
        K.poly(d, [K.at(-6.0, 8.4), K.at(-10.6, 5.0), K.at(-11.6, -4.0), K.at(-8.6, -11.4), K.at(-1.0, -14.8), K.at(6.4, -13.2), K.at(9.4, -9.6), K.at(5.6, -8.2),
                   K.at(0.4, -8.6), K.at(-3.0, -5.4), K.at(-4.0, 0.6), K.at(-3.6, 6.4)], WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(-11.6, -4.0), K.at(-8.6, -11.4), K.at(-6.0, -9.0), K.at(-8.4, -3.0), K.at(-7.6, 5.0), K.at(-10.6, 5.0)], BLANKET_DARK)
        K.line(d, [K.at(-7.0, -8.0), K.at(-1.0, -11.6), K.at(5.0, -10.6)], BLANKET_LIGHT, 0.5)
        # The fur of its edge goes round his face.
        _tufts(d, [(7.6, -9.4), (4.4, -8.6), (1.2, -8.2), (-1.6, -6.2), (-3.2, -3.2), (-3.8, 0.2), (-3.8, 3.6), (-4.4, 6.6)], 1.7)

    return K.solid(("furrier_hood",), shape, BLANKET, detail, outline=1.2, rim=0.2, shade=0.0)


X.head_layers = lambda pose: ([(_head(), "head")] + ([(_hood(), "hood")] if float(pose["wrap"]) > 0.5 else []) +
                              [(_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"), (_mouth(str(pose["mouth"])), "mouth")])
X.neck = R.make_neck(K, SKIN_SHADE, 4.6)
# His arms are in the blanket to the wrist, and it has fur there too.
X.upper_arm = lambda near: [(0.0, 1.0, 8.0, 7.2, BLANKET if near else BLANKET_DARK)]
X.forearm = lambda near: [(0.0, 0.86, 7.4, 6.6, BLANKET if near else BLANKET_DARK), (0.72, 1.0, 7.0, 6.8, FUR if near else FUR_DARK)]
X.thigh = lambda near: [(0.0, 1.0, 6.8, 5.8, TROUSER if near else TROUSER_DARK)]
X.shin = lambda near: [(0.0, 1.0, 5.8, 5.0, TROUSER if near else TROUSER_DARK)]
X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, size=0.95)
X.shoe = R.make_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up, long=1.0)

def _wrapped(ctx) -> List[Stamp]:
    """He is wrapped in the blanket: it is round all of him from his chin to
    his shins, his arms are inside it, and one hand holds the edge that is
    over the other one."""
    if float(ctx.pose["wrap"]) <= 0.5:
        return []
    sway = int(round(float(ctx.pose["hem"][0])))

    def shape(d) -> None:
        K.poly(d, [K.at(-5.0, TOP - 0.6), K.at(-11.4, TOP + 4.0), K.at(-14.4, -22.0), K.at(-16.0, -4.0), K.at(-15.4 - sway, HEM + 1.0), K.at(-9.0, HEM + 4.0),
                   K.at(2.0, HEM + 2.4), K.at(13.4 + sway, HEM + 4.0), K.at(15.4, -2.0), K.at(13.8, -20.0), K.at(10.8, TOP + 5.0), K.at(6.4, TOP - 0.6)], WHITE)
        for x in (-6.4, -2.4, 1.8, 6.0, 9.4):
            K.oval(d, K.at(x, TOP + 1.6), 3.4, 3.2, WHITE)

    def detail(d) -> None:
        # The flap that is on top goes from his far shoulder down across him;
        # what is under it is in its shade.
        flap = [(10.4, TOP + 6.0), (7.6, -22.0), (4.0, -8.0), (-1.0, 8.0), (-5.6, HEM + 3.0)]
        K.poly(d, [K.at(x, y) for x, y in flap] + [K.at(13.4 + sway, HEM + 4.0), K.at(15.4, -2.0), K.at(13.8, -20.0)], BLANKET_DARK)
        K.line(d, [K.at(-11.0, TOP + 8.0), K.at(-13.6, -4.0), K.at(-13.0 - sway, HEM - 2.0)], BLANKET_LIGHT, 0.6)
        for x0, y0, x1, y1 in ((-7.0, -24.0, -9.6, 4.0), (-2.0, -20.0, -5.0, 12.0), (10.6, -14.0, 11.6 + sway, 16.0)):
            K.line(d, [K.at(x0, y0), K.at(x1, y1)], mix(BLANKET, BLANKET_DARK, 0.6) if x0 < 8 else (22, 24, 44, 255), 0.6)
        # The fur of its edge is one band (tufts that are apart read as the
        # buttons of a coat).
        steps = 26
        _tufts(d, [(flap[0][0] + (flap[-1][0] - flap[0][0]) * t - 3.0 * math.sin(math.pi * t), flap[0][1] + (flap[-1][1] - flap[0][1]) * t) for t in
                   [k / steps for k in range(steps + 1)]], 2.1)
        _tufts(d, [(x, HEM + 1.6 + 0.5 * math.sin(x)) for x in [-13.6 + 3.3 * k for k in range(9)]], 2.4)
        # The roll at his chin.
        _tufts(d, [(-6.4, TOP + 1.6), (-2.4, TOP + 2.8), (1.8, TOP + 3.2), (6.0, TOP + 2.8), (9.4, TOP + 1.6)], 3.2)
        # The hand that holds it shut.
        K.oval(d, K.at(6.0, -21.0), 3.1, 2.7, OUTLINE)
        K.oval(d, K.at(6.0, -21.0), 2.5, 2.1, SKIN)
        for dx in (-0.9, 0.5, 1.8):
            K.line(d, [K.at(6.0 + dx, -22.4), K.at(6.0 + dx - 0.2, -20.0)], SKIN_DEEP, 0.4)

    return [(K.solid(("furrier_wrap", sway), shape, BLANKET, detail, outline=1.3, rim=0.3, shade=0.0), ctx.hip, "wrap", ctx.lean)]


X.layers["front"].append(_wrapped)

# ---- How he holds himself ----------------------------------------------------

#: Both hands hold the blanket shut at his chest.
SHUT_NEAR = (9.0, 9.0)
SHUT_FAR = (6.0, 12.0)
#: His arms when he is wrapped: all of them is inside the blanket.
IN_NEAR = (7.0, 12.0)
IN_FAR = (1.0, 14.0)
# ``wrap``: he is wrapped in the blanket (``_wrapped``, ``_hood``). He is
# when he does nothing and when he walks; a row in which he does something
# opens it.
X.set_rest(lean=0.0, na=SHUT_NEAR, fa=SHUT_FAR, nh="fist", fh="fist", nf=(-3.8, 0.0, 0.0), ff=(4.8, 0.0, 0.0), wrap=0.0)


@X.row
def idle(i: int, n: int):
    # He is cold. Now and then all of him shakes once.
    _, s, c = loop(i, n)
    shake = 0.6 if i in (5, 6) else 0.0
    return P(hip=(shake * (1.0 if i == 5 else -1.0), 0.3 + 0.3 * s), lean=0.4 * s, head=(0.3, 0.2, 2.0 + 2.0 * c), eyes="closed" if i == n - 2 else "open",
             mouth="grit" if shake else "flat", brows=-1.0 if shake else 0.0, wrap=1.0, na=IN_NEAR, fa=IN_FAR)


@X.row
def walk(i: int, n: int):
    # Small steps: the blanket stays shut.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 6.4, 3.4)
    return P(hip=(0.5, 0.7 * math.cos(2.0 * ph)), lean=2.0, head=(0.3, 0.0, 1.0 + 1.5 * s), nf=nf, ff=ff, hem=(1.0 + abs(c), abs(c)), wrap=1.0, na=IN_NEAR, fa=IN_FAR)


@X.row
def talk(i: int, n: int):
    # One hand comes out to count the parts of the wave, and goes back in.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), lean=1.0, head=(0.4, 0.0, 2.0 * s), na=(14.0 + 2.0 * c, 3.0 - 4.0 * max(0.0, s)), nh="open", mouth=("open", "smile", "big", "flat")[i % 4],
             brows=1.0 if s > 0.3 else 0.0)


@X.row
def blanket_snap(i: int, n: int):
    # He takes a corner of it and cracks it like a whip.
    back = P(hip=(-1.5, 1.0), lean=-6.0, na=(-8.0, -4.0), nab=-1.0, nh="fist", brows=-1.0, nf=(-6.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0))
    out = P(hip=(3.0, 1.5), lean=10.0, head=(1.0, 0.0, 4.0), na=(26.0, 2.0), nh="fist", brows=-1.0, mouth="grit", nf=(-8.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), hem=(4.0, 3.0))
    return X.keys(shot(i, n), [(0.0, P()), (0.25, back), (0.42, out), (0.7, dict(out, na=(24.0, 5.0))), (1.0, P())])


@X.row
def step_function(i: int, n: int):
    # A foot up on the first step he has made, and a hand to the next.
    up = P(hip=(1.5, -1.0), lean=4.0, head=(0.5, 0.0, -6.0), na=(22.0, -8.0), nh="point", ff=(11.0, -6.0, 0.0), nf=(-5.0, 0.0, 0.0), eyes="up", brows=1.0, mouth="open")
    return X.keys(shot(i, n), [(0.0, P()), (0.3, up), (0.8, dict(up, na=(23.0, -12.0), mouth="smile")), (1.0, P())])


#: The blanket open, both arms out: what was one wave is its parts.
OPEN = P(hip=(0.0, 0.5), lean=-3.0, head=(0.0, 0.0, -6.0), na=(-13.0, 2.0), nab=-1.0, fa=(21.0, -2.0), nh="open", fh="open", eyes="wide", brows=1.0, mouth="big",
         nf=(-5.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0), hem=(4.0, 4.0))


@X.row
def harmonic_split(i: int, n: int):
    wind = P(hip=(0.0, 2.0), lean=6.0, head=(0.5, 0.5, 6.0), eyes="closed", brows=-1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.2, wind), (0.4, OPEN), (0.85, OPEN), (1.0, P())])


@X.row
def low_pass_lament(i: int, n: int):
    # He goes down into the blanket, and what comes at him comes through soft.
    _, s, _c = loop(i, n)
    down = P(hip=(-1.0, 5.0 + 0.4 * s), lean=8.0, head=(0.5, 1.5, 12.0), eyes="closed", brows=-1.0, mouth="flat", nf=(-6.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0))
    return X.keys(shot(i, n), [(0.0, P()), (0.25, down), (0.85, down), (1.0, P())])


@X.row
def full_turn(i: int, n: int):
    # All the way round, the blanket out from him like a bell.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 1.0), lean=5.0 * s, head=(0.0, 0.0, 6.0 * s), na=(-16.0 + 7.0 * c, 0.0), nab=-1.0, fa=(19.0 - 7.0 * c, 0.0), nh="fist", fh="fist",
             nf=(-4.0 + 3.0 * s, 0.0, 0.0), ff=(5.0 - 3.0 * s, -1.0 * abs(c), 10.0), mouth="open", hem=(5.0 * abs(s), 5.0 * abs(c)))


X.alias(spectral_descent="air_down")
X.rows = [("idle", 8, 145), ("walk", 8, 106), ("run", 8, 78), ("crouch", 6, 96), ("crouch_walk", 8, 90), ("jump", 6, 92), ("fall", 6, 92), ("land_hard", 8, 88),
          ("land_recovery", 6, 72), ("dash_startup", 4, 48), ("dash", 6, 60), ("slide", 6, 68), ("roll", 8, 56), ("wall_grab", 6, 105), ("wall_jump", 6, 82),
          ("ledge_grab", 6, 98), ("ledge_climb", 6, 98), ("ledge_getup", 6, 42), ("ledge_roll", 8, 38), ("climb", 8, 98), ("swim", 8, 102), ("float_glide", 8, 108),
          ("block", 6, 82), ("hit", 5, 86), ("death", 8, 105), ("talk", 8, 104), ("interact", 8, 90), ("blanket_snap", 7, 62), ("step_function", 8, 70),
          ("harmonic_split", 8, 74), ("low_pass_lament", 8, 82), ("spectral_descent", 8, 72), ("air_neutral", 8, 62), ("air_forward", 7, 60), ("air_back", 7, 60),
          ("air_down", 7, 68), ("air_up", 7, 60), ("full_turn", 10, 72), ("celebrate", 8, 88), ("taunt", 8, 96)]

# ---- From the front ------------------------------------------------------------
#
# From the front he is wrapped in the blanket too: it is what he is.


def _front_blanket(d) -> None:
    """The blanket round him from the front: the flap that is on top, the
    band of fur along its edge and along the hem, the roll at his chin, and
    the hand that holds it."""
    flap = [(8.6, TOP + 6.0), (5.0, -20.0), (0.0, -6.0), (-5.0, 10.0), (-9.0, HEM + 3.0)]
    K.poly(d, [K.at(x, y) for x, y in flap] + [K.at(20.0, HEM + 6.0), K.at(20.0, TOP)], BLANKET_DARK)
    for x0, y0, x1, y1 in ((-9.0, -24.0, -12.0, 6.0), (-4.0, -20.0, -8.0, 14.0), (11.0, -14.0, 12.6, 16.0)):
        K.line(d, [K.at(x0, y0), K.at(x1, y1)], mix(BLANKET, BLANKET_DARK, 0.6) if x0 < 8 else (22, 24, 44, 255), 0.6)
    steps = 26
    _tufts(d, [(flap[0][0] + (flap[-1][0] - flap[0][0]) * t - 3.0 * math.sin(math.pi * t), flap[0][1] + (flap[-1][1] - flap[0][1]) * t) for t in
               [k / steps for k in range(steps + 1)]], 2.1)
    _tufts(d, [(x, HEM + 1.6 + 0.5 * math.sin(x)) for x in [-13.2 + 3.3 * k for k in range(9)]], 2.4)
    _tufts(d, [(-7.6, TOP + 1.6), (-3.8, TOP + 2.8), (0.0, TOP + 3.2), (3.8, TOP + 2.8), (7.6, TOP + 1.6)], 3.2)
    K.oval(d, K.at(3.6, -21.0), 3.1, 2.7, OUTLINE)
    K.oval(d, K.at(3.6, -21.0), 2.5, 2.1, SKIN)
    for dx in (-0.9, 0.5, 1.8):
        K.line(d, [K.at(3.6 + dx, -22.4), K.at(3.6 + dx - 0.2, -20.0)], SKIN_DEEP, 0.4)


def _front_hood_shape(d) -> None:
    K.oval(d, K.at(0.0, -3.0), 11.0, 12.0, WHITE)
    K.poly(d, [K.at(-10.4, 0.0), K.at(-9.0, 10.0), K.at(9.0, 10.0), K.at(10.4, 0.0)], WHITE)


def _front_hood(d) -> None:
    # The blanket is over his head: his face is in the opening of it, with
    # the fur of its edge round it, and his curls at the top of it.
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 20.0), K.at(-20.0, 20.0)], BLANKET)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(7.6 * sx, -12.0), K.at(11.6 * sx, -4.0), K.at(10.4 * sx, 10.0), K.at(7.6 * sx, 10.0)], BLANKET_DARK)
    K.oval(d, K.at(0.0, 1.2), 6.6, 8.6, SKIN)
    K.poly(d, [K.at(-6.0, -4.0), K.at(-4.0, -7.4), K.at(0.0, -8.2), K.at(4.0, -7.4), K.at(6.0, -4.0), K.at(3.6, -5.6), K.at(1.4, -4.6), K.at(-1.0, -5.8), K.at(-3.4, -4.6)],
           HAIR)
    ring = [(6.9 * math.cos(math.radians(a)), 1.2 + 9.0 * math.sin(math.radians(a))) for a in range(-200, 21, 20)]
    _tufts(d, ring, 1.6)


def _front_cold(d) -> None:
    K.oval(d, K.at(0.0, 3.6), 1.6, 1.4, NOSE)
    for sx in (-1.0, 1.0):
        K.oval(d, K.at(3.8 * sx, 4.4), 1.7, 1.1, mix(SKIN, NOSE, 0.45))


X.front_torso = R.make_front_torso(K, ("furrier",), BLANKET, BLANKET_DARK, [(TOP - 0.6, 5.0), (TOP + 4.0, 11.4), (-22.0, 13.8), (-4.0, 15.2), (HEM + 1.0, 14.8),
                                                                           (HEM + 3.6, 12.0)], detail=_front_blanket)
X.front_head_layers = R.front_face(R.make_front_head(K, ("furrier",), SKIN, SKIN_DEEP, wide=8.0, jaw=6.8, chin=3.6, shape=_front_hood_shape, hair=_front_hood,
                                                    face=_front_cold),
                                   R.make_front_eyes(K, ("furrier",), white=None, ink=INK, spread=3.0, y=-0.2), R.make_front_brows(K, ("furrier",), HAIR, spread=3.0, y=-3.2),
                                   R.make_front_mouth(K, ("furrier",), y=8.0, colour=(118, 67, 65, 255), wide=0.7))
X.front_shoe = R.make_front_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up)
X.front_span = (8.6, 4.6)


@X.front_row
def front(i: int, n: int):
    # His arms are inside the blanket: only the hand on its edge is out.
    _, s, _c = loop(i, n)
    shake = 0.6 if i in (5, 6) else 0.0
    return R.FP(hip=(shake * (1.0 if i == 5 else -1.0), 0.4 + 0.3 * s), la=(-6.0, 12.0), ra=(-6.0, 12.0), lz=0.8, rz=0.8, lh="fist", rh="fist",
                eyes="closed" if i == n - 2 else "open", mouth="grit" if shake else "flat", brows=-1.0 if shake else 0.0)


R.add_front_rows(X)

# ---- What he shows -----------------------------------------------------------


def _wave(cycles: float, amp: float, colour: RGBA, length: int = 34, rough: float = 0.0):
    """A wave along +x from ``home``. ``rough``: how much of a second, fast
    wave is on it."""

    def paint(d) -> None:
        pts = [K.at(x, amp * math.sin(math.tau * cycles * x / length) + rough * math.sin(math.tau * cycles * 5.3 * x / length + 1.0)) for x in
               [k * 0.5 for k in range(length * 2 + 1)]]
        K.line(d, pts, BAND_DARK, 2.0)
        K.line(d, pts, colour, 0.9)

    return K.aligned(("wave", cycles, amp, colour, length, rough), paint)


def _steps(count: int, down: bool = False):
    """Steps, from ``home`` at the floor: each as far up (or down) as it is
    along."""

    def paint(d) -> None:
        for k in range(count):
            y = (6.0 * (k + 1)) * (1.0 if down else -1.0)
            x0, x1 = 8.0 * k, 8.0 * (k + 1)
            K.poly(d, [K.at(x0, 0.0), K.at(x1, 0.0), K.at(x1, y), K.at(x0, y)], GOLD_DARK)
            K.poly(d, [K.at(x0 + 0.8, -0.8 if not down else 0.8), K.at(x1 - 0.8, -0.8 if not down else 0.8), K.at(x1 - 0.8, y + (0.8 if not down else -0.8)),
                       K.at(x0 + 0.8, y + (0.8 if not down else -0.8))], GOLD)

    return K.aligned(("steps", count, down), paint)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, i, u = ctx.anim, ctx.i, ctx.u
    if anim == "blanket_snap" and 0.35 <= u <= 0.7:
        out.append((R.swoosh(K, 22.0, -60, 30, 5.0, BLANKET_LIGHT, BLANKET_DARK), pin((ctx.hand[0] - 6.0, ctx.hand[1] + 2.0)), "snap", 0.0))
        out.append((R.burst(K, 6.0, FUR_LIGHT, FUR_DARK), (ctx.hand[0] + 16.0, ctx.hand[1]), "crack", 0.0))
    elif anim == "step_function" and u >= 0.2:
        out.append((_steps(min(3, 1 + int((u - 0.2) / 0.2))), pin((ctx.hip[0] + 8.0, ctx.ground)), "steps", 0.0))
    elif anim == "spectral_descent" and 0.15 <= u <= 0.9:
        out.append((_steps(3, down=True), pin((ctx.hip[0] + 6.0, ctx.hip[1] + 8.0)), "steps", 0.0))
    elif anim == "harmonic_split":
        if 0.2 <= u < 0.4:
            out.append((_wave(2.0, 4.0, WHITE, 26, rough=1.6), pin((ctx.hip[0] + 12.0, ctx.hip[1] - 26.0)), "sum", 0.0))
        elif u >= 0.4:
            for k, colour in enumerate(BANDS):
                spread = min(1.0, (u - 0.4) / 0.25)
                out.append((_wave(1.0 + k, 3.4 - 0.5 * k, colour), pin((ctx.far_hand[0] + 4.0, ctx.hip[1] - 26.0 + (k - 1.5) * 9.0 * spread)), f"band_{k}", 0.0))
    elif anim == "low_pass_lament" and 0.2 <= u <= 0.9:
        # Rough where it comes in, smooth where it reaches him.
        out.append((_wave(2.0, 3.6, DAMP, 22, rough=1.8), pin((ctx.hip[0] + 30.0 - 6.0 * (i % 2), ctx.hip[1] - 24.0)), "rough", 0.0))
        out.append((_wave(1.0, 2.4, DAMP, 14), pin((ctx.hip[0] + 14.0, ctx.hip[1] - 24.0)), "smooth", 0.0))
    return out


X.effects = _effects

ROWS = X.rows
FRAME_W, FRAME_H = X.frame
render_frame = X.render_frame
_render_frame = render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet."""
    del opts
    r8 = tuple(range(8))
    return X.portraits(out_dir, {
        "default": ("idle", (1,), 0, False),
        "murmuring": ("talk", r8, 104, True),
        "listening": ("idle", r8, 145, True),
        "spectral": ("harmonic_split", (3, 4, 5, 6), 110, True),
    }, view_width=38.0)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
