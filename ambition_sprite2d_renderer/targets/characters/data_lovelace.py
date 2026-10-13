"""Sprite generator for Data Lovelace: the engine she wrote for, as a woman
of brass.

An affectionate caricature of Ada Lovelace, as an automaton of her own
century.

The look (2026-10-13): a Victorian automaton in the shape of a lady, seen
three quarters from the front, facing right. Her face is a mask of pale
enamel with two eyes of green light. Her hair is cast in dark copper: parted
in the middle, flat over her ears, with a coil of ringlets at each ear and a
knot behind, as in the portrait of Ada. A bodice of teal enamel with brass
ribs, puffed sleeves, and a bell of a skirt to her ankles: brass hoops with
teal between them, and at its hem a band of card with holes punched in it.
A gear is the clasp of her belt. Her arms and hands are brass.

She is a machine and she is a lady: she is not a robot of the future. She
holds nothing; there is no drop shadow.

What she shows: the cards of a program, dealt in an arc from her hand; the
pattern they make (a weave, as a loom weaves flowers); and a gear that she
sets right in her own arm.

She is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, how she stands and what she shows are hers.
Her portraits are frames of this sheet.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import WHITE, RGBA, mix, pin
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

#: 165 cm.
BUILD = Build(hip_up=47.0, thigh=22.9, shin=21.3, neck=(0.6, -35.0), upper=18.4, fore=17.4, near_shoulder=(-4.6, -30.8), far_shoulder=(5.6, -30.4),
              near_hip=(-3.8, 0.0), far_hip=(3.8, 0.0), head_up=(1.0, -12.2), height=106.0, half_width=(13.0, 14.0))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0
#: How far under her hips the hem of her skirt is.
HEM = BUILD.hip_up - 5.0


def _front(d, hb: float, hf: float) -> None:
    """The ribs of her bodice, the light on her bust and the shade under it,
    her belt and its gear, the hoops of her skirt and the band of card at
    its hem."""
    by = TOP + 12.5
    # The bodice: a brass yoke, and ribs down to her waist.
    K.poly(d, [K.at(-6.0, TOP - 1.0), K.at(9.0, TOP - 1.0), K.at(8.0, TOP + 4.0), K.at(4.0, TOP + 6.0), K.at(-5.0, TOP + 4.0)], BRASS)
    K.line(d, [K.at(-5.0, TOP + 4.0), K.at(4.0, TOP + 6.0), K.at(8.0, TOP + 4.0)], BRASS_DARK, 0.6)
    for x in (-3.4, 0.6, 4.6):
        K.line(d, [K.at(x, TOP + 6.0), K.at(x * 0.6 + 0.6, -14.0)], BRASS, 0.9)
    K.oval(d, K.at(6.2, by + 0.4), 2.6, 2.0, TEAL_LIGHT)
    K.poly(d, [K.at(0.6, by + 3.4), K.at(4.6, by + 5.0), K.at(10.4, by + 3.6), K.at(9.2, by + 6.4), K.at(4.4, by + 7.2), K.at(0.6, by + 5.2)], TEAL_DARK)
    # Her belt, and the gear that is its clasp.
    K.poly(d, [K.at(-9.0, -14.6), K.at(9.4, -13.8), K.at(9.4, -11.4), K.at(-9.0, -12.2)], BRASS_DARK)
    for a in range(0, 360, 45):
        K.line(d, [K.at(3.6, -12.8), K.at(3.6 + 3.4 * math.cos(math.radians(a)), -12.8 + 3.4 * math.sin(math.radians(a)))], BRASS_DEEP, 1.3)
    K.oval(d, K.at(3.6, -12.8), 2.5, 2.5, BRASS_LIGHT, BRASS_DEEP, 0.5)
    K.oval(d, K.at(3.6, -12.8), 0.9, 0.9, BRASS_DEEP)
    # The skirt: hoops of brass, and ribs from her waist to the hem.
    for k, y in enumerate((-4.0, 6.0, 16.0, 26.0)):
        wide = 10.6 + 2.2 * k
        K.line(d, [K.at(-wide - hb * 0.3 * k, y), K.at(0.0, y + 1.6), K.at(wide + 1.0 + hf * 0.3 * k, y)], BRASS_DARK, 1.5)
        K.line(d, [K.at(-wide - hb * 0.3 * k, y - 0.3), K.at(0.0, y + 1.3), K.at(wide + 1.0 + hf * 0.3 * k, y - 0.3)], BRASS, 0.7)
    for x in (-5.0, 0.4, 5.6, 9.6):
        K.line(d, [K.at(x * 0.7, -11.0), K.at(x * 1.9 - hb * 0.3 + hf * 0.3, HEM - 6.0)], BRASS, 0.6)
    # The hem: a band of card, with holes punched in it.
    K.poly(d, [K.at(-30.0, HEM - 6.4), K.at(30.0, HEM - 6.4), K.at(30.0, HEM + 6.0), K.at(-30.0, HEM + 6.0)], CARD)
    K.line(d, [K.at(-30.0, HEM - 6.4), K.at(30.0, HEM - 6.4)], CARD_DARK, 0.6)
    for k in range(-8, 10):
        if (k * 7) % 5 != 0:
            K.rrect(d, K.home[0] + k * 2.8 - 0.7, K.home[1] + HEM - 4.6 + 1.6 * (k % 2), K.home[0] + k * 2.8 + 0.7, K.home[1] + HEM - 3.2 + 1.6 * (k % 2), 0.2, INK)


X.torso = R.make_figure(K, ("lovelace",), TEAL, TEAL_DARK, back=(7.4, 7.6, 6.0, 10.4, 17.6), front=(6.4, 10.4, 6.2, 10.8, 17.4), hem_y=HEM, top=TOP,
                        shoulders=((-4.6, -30.2), (3.8, -30.2)), shoulder_r=(4.8, 3.6), shade_from=8.0, detail=_front)

NEAR_EYE = (2.0, -0.4)
FAR_EYE = (7.0, -0.6)


def _hair_shape(d) -> None:
    # Cast in one piece: smooth on top, a knot behind, and a coil at her ear.
    K.oval(d, K.at(-0.8, -5.6), 8.8, 7.0, WHITE)
    K.oval(d, K.at(-8.6, -3.0), 3.6, 3.4, WHITE)
    for y in (2.6, 5.6, 8.4):
        K.oval(d, K.at(-4.4, y), 2.6, 1.9, WHITE)


def _hair(d) -> None:
    K.poly(d, [K.at(20.0, -9.0), K.at(8.4, -9.0), K.at(5.6, -7.0), K.at(2.4, -4.4), K.at(-0.4, -2.0), K.at(-2.0, 0.4), K.at(-2.0, 12.0), K.at(-20.0, 12.0),
               K.at(-20.0, -26.0), K.at(20.0, -26.0)], COPPER)
    # The parting, and the light the metal takes.
    K.line(d, [K.at(3.0, -12.4), K.at(1.6, -8.0)], COPPER_DARK, 0.6)
    for strand in ([(-5.0, -10.6), (-1.0, -11.6), (1.6, -10.8)], [(4.6, -11.2), (7.0, -9.8)], [(-6.0, -6.0), (-3.0, -3.6)]):
        K.line(d, [K.at(x, y) for x, y in strand], COPPER_LIGHT, 0.6)
    K.oval(d, K.at(-8.6, -3.0), 2.0, 1.8, None, COPPER_DARK, 0.5)  # type: ignore[arg-type]
    for y in (2.6, 5.6, 8.4):
        K.line(d, [K.at(-6.4, y - 0.4), K.at(-2.6, y + 0.6)], COPPER_DARK, 0.6)
        K.line(d, [K.at(-6.0, y - 1.0), K.at(-3.4, y - 0.4)], COPPER_LIGHT, 0.5)


def _face(d) -> None:
    # The seam of her mask, and a rivet at her temple.
    K.line(d, [K.at(-1.4, 1.0), K.at(0.4, 6.4), K.at(3.6, 9.0)], ENAMEL_DEEP, 0.45)
    K.oval(d, K.at(-0.6, -1.6), 0.7, 0.7, BRASS)


_head = R.make_head(K, ("lovelace",), ENAMEL, ENAMEL_SHADE, ENAMEL_DEEP, skull=(0.0, -2.4, 7.8, 8.8), jaw=(2.6, 4.0, 5.2, 6.8),
                    nose=((7.4, -0.6), (9.4, 2.6), (8.8, 3.8), (7.2, 4.0)), ear=None, shape=_hair_shape, under=_hair, over=_face)
_eyes = R.make_eyes(K, NEAR_EYE, FAR_EYE, ink=TEAL_DARK, white=LIGHT, lid=ENAMEL_DEEP, size=0.95, lash=0.5)
_brows = R.make_brows(K, [(-0.4, -3.8), (2.0, -4.6), (4.4, -4.0)], [(5.8, -4.2), (7.2, -4.6), (8.4, -4.2)], COPPER_DARK, 0.9)
_mouth = R.make_mouth(K, (5.6, 6.6), (150, 70, 70, 255), wide=0.7, lips=(196, 92, 92, 255))

X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"), (_mouth(str(pose["mouth"])), "mouth")]
X.neck = R.make_neck(K, BRASS_DARK, 3.6)
# A puffed sleeve of teal, and under it an arm of brass with a joint.
X.upper_arm = lambda near: [(0.0, 0.5, 8.0, 6.4, TEAL if near else TEAL_DARK), (0.42, 1.0, 4.4, 4.0, BRASS if near else BRASS_DARK), (0.86, 1.0, 5.0, 5.0, BRASS_DEEP)]
X.forearm = lambda near: [(0.0, 0.12, 5.0, 5.0, BRASS_DEEP), (0.1, 1.0, 4.6, 3.8, BRASS if near else BRASS_DARK), (0.78, 1.0, 4.6, 4.4, BRASS_LIGHT if near else BRASS)]
X.thigh = lambda near: [(0.0, 1.0, 6.0, 5.2, BRASS if near else BRASS_DARK)]
X.shin = lambda near: [(0.0, 1.0, 5.2, 4.4, BRASS if near else BRASS_DARK)]
X.hand = R.make_hand(K, BRASS_LIGHT, BRASS, BRASS_DEEP, size=0.86)
X.shoe = R.make_shoe(K, BRASS_DARK, BRASS_DEEP, BUILD.ankle_up, long=0.92)

# ---- How she holds herself -----------------------------------------------------

#: Her hands one on the other at her waist.
X.set_rest(lean=0.0, na=(5.0, 19.0), fa=(4.0, 21.0), nh="fist", fh="fist", nf=(-3.0, 0.0, 0.0), ff=(3.6, 0.0, 0.0))


@X.row
def idle(i: int, n: int):
    # She is still, as a machine is; her head turns a little, and the lights
    # of her eyes go out and come on.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.2 * s), head=(0.3, 0.0, -2.0 + 3.0 * (1.0 if c > 0.3 else 0.0)), eyes="closed" if i == n - 2 else "open", mouth="smile")


@X.row
def walk(i: int, n: int):
    # She glides: the skirt hides her steps, and it swings.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 6.0, 2.6)
    return P(hip=(0.4, 0.4 * math.cos(2.0 * ph)), lean=1.0, head=(0.2, 0.0, 1.0 * s), nf=nf, ff=ff, hem=(1.5 + 1.5 * abs(c), 1.5 * abs(s)))


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

# ---- What she shows ------------------------------------------------------------


def _card(seed: int):
    """A card of a program: holes in rows. ``seed`` says which holes."""

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 5.0, K.home[1] - 3.2, K.home[0] + 5.0, K.home[1] + 3.2, 0.6, WHITE)

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
        K.poly(d, pts, WHITE)
        K.oval(d, K.home, r * 0.7, r * 0.7, WHITE)

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


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

del mix

if __name__ == "__main__":
    raise SystemExit(main())
