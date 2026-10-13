"""Sprite generator for Jeff Hinter: the man who gives you a hint, and then the
dimension you are missing.

An affectionate caricature of Geoffrey Hinton.

The look (2026-10-13): a tall thin old man seen three quarters from the
front, facing right. Fine white hair, thin on top and combed over to the
side; a high forehead, a long face, a sharp nose, a small dry smile; glasses
with thin frames and no heavy rims. A dark blazer over a blue pullover and an
open collar, grey trousers. He stands (he does not sit), a little bent from
the hips with his hands behind his back, and he looks at something that is
not in the room.

He is drawn from the man and not from a type (Jon, 2026-10-13, of another
person of this cast: "needs to read like paul erdos not bearnie sanders"). He
is a grown man, not a mascot. He holds nothing; there is no drop shadow.

What he shows: points in a plane that fall into their groups; the number he
shouts (14, or 3 when the game has only two dimensions and he wants one
more); and the surface he wraps round himself.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, how he stands and what he shows are his. The
sheet ``jeff_hinter_armored`` is still drawn by the painter before this one
(``_jeff_hinter_base``).
"""

from __future__ import annotations

import math
from typing import List

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

BLAZER: RGBA = (62, 66, 84, 255)
BLAZER_DARK: RGBA = (40, 42, 60, 255)
BLAZER_LIGHT: RGBA = (100, 106, 130, 255)
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
HAIR: RGBA = (242, 242, 240, 255)
HAIR_SHADE: RGBA = (180, 186, 198, 255)
FRAME: RGBA = (96, 100, 116, 255)
LENS: RGBA = (232, 244, 250, 150)
INK: RGBA = (28, 24, 32, 255)
NET: RGBA = (130, 236, 222, 255)
NET_DARK: RGBA = (40, 130, 140, 255)
HOT: RGBA = (255, 206, 110, 255)
HOT_DARK: RGBA = (214, 120, 50, 255)
ROSE: RGBA = (250, 150, 170, 255)
VIOLET: RGBA = (186, 160, 250, 255)

#: Tall and thin, 178 cm, and bent a little from the hips.
BUILD = Build(hip_up=52.0, thigh=25.2, shin=24.0, neck=(1.4, -37.0), upper=20.4, fore=19.4, near_shoulder=(-5.0, -32.8), far_shoulder=(7.4, -32.4),
              near_hip=(-3.4, 0.0), far_hip=(3.4, 0.0), head_up=(1.4, -12.8), height=114.0, half_width=(12.5, 14.5))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0


def _front(d, hb: float, hf: float) -> None:
    """The blue pullover where the blazer hangs open, and his open collar."""
    K.poly(d, [K.at(2.2, TOP), K.at(11.6, TOP), K.at(12.0 + hf, 13.0), K.at(4.8 + hf * 0.5, 13.0), K.at(3.8, -14.0)], PULLOVER)
    K.poly(d, [K.at(9.4, TOP), K.at(12.6, TOP), K.at(13.0 + hf, 13.0), K.at(10.2 + hf, 13.0)], BLAZER_DARK)
    K.poly(d, [K.at(3.4, TOP - 1.0), K.at(8.8, TOP - 1.0), K.at(6.6, TOP + 8.0)], SHIRT)
    K.poly(d, [K.at(4.8, TOP - 1.0), K.at(7.8, TOP - 1.0), K.at(6.4, TOP + 4.6)], SKIN_SHADE)
    K.line(d, [K.at(4.0, TOP + 9.0), K.at(8.6, TOP + 9.4)], PULLOVER_DARK, 0.7)
    K.poly(d, [K.at(-0.6, TOP + 1.0), K.at(3.0, TOP), K.at(4.2, -20.0), K.at(0.2, -28.0)], BLAZER_LIGHT)
    K.line(d, [K.at(0.2, -28.0), K.at(4.2, -20.0), K.at(3.8, -14.0), K.at(4.8 + hf * 0.5, 10.0)], BLAZER_DARK, 0.7)
    K.line(d, [K.at(-7.0, -3.4), K.at(-1.4, -2.8)], BLAZER_DARK, 0.7)


X.torso = R.make_torso(K, ("hinter",), BLAZER, BLAZER_DARK, back=(8.8, 9.2, 8.2, 9.4), front=(8.0, 9.6, 9.0, 9.8), hem_y=10.0, top=TOP,
                       shoulders=((-4.8, -32.2), (6.6, -32.0)), shoulder_r=(5.0, 4.6), shade_from=40.0, detail=_front)

NEAR_EYE = (1.6, -0.6)
FAR_EYE = (7.0, -0.8)


def _hair_shape(d) -> None:
    # Fine, and it stands off his head a little at the back.
    K.oval(d, K.at(-1.4, -6.0), 8.6, 7.0, WHITE)
    K.poly(d, [K.at(-7.6, -6.0), K.at(-10.6, -3.0), K.at(-8.2, -1.0), K.at(-10.0, 2.6), K.at(-7.0, 4.0), K.at(-5.0, 6.6)], WHITE)


def _hair(d) -> None:
    # Combed over from the near side; his forehead is high under it.
    K.poly(d, [K.at(20.0, -11.4), K.at(6.0, -11.4), K.at(1.6, -9.6), K.at(-1.6, -7.4), K.at(-3.2, -4.4), K.at(-3.4, -1.6), K.at(-6.2, -1.4), K.at(-6.8, 3.6),
               K.at(-5.2, 4.8), K.at(-4.8, 6.6), K.at(-20.0, 6.6), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
    for strand in ([(5.0, -12.0), (0.0, -10.6), (-5.0, -6.6)], [(1.0, -12.6), (-4.0, -11.0), (-8.0, -6.0)], [(-6.0, -1.0), (-8.6, 1.6)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_SHADE, 0.6)


def _face(d) -> None:
    crease = mix(SKIN, SKIN_DEEP, 0.5)
    K.line(d, [K.at(2.6, -6.6), K.at(5.0, -7.0), K.at(7.4, -6.6)], crease, 0.45)
    K.line(d, [K.at(2.0, -8.8), K.at(4.6, -9.2), K.at(6.8, -8.8)], crease, 0.45)
    for (cx, cy), rx in ((NEAR_EYE, 3.0), (FAR_EYE, 1.9)):
        K.rrect(d, K.home[0] + cx - rx, K.home[1] + cy - 2.2, K.home[0] + cx + rx, K.home[1] + cy + 2.0, 0.8, LENS)
    K.line(d, [K.at(4.8, 4.4), K.at(2.8, 6.4), K.at(2.6, 8.6)], crease, 0.5)


def _glasses():
    def paint(d) -> None:
        for (cx, cy), rx in ((NEAR_EYE, 3.0), (FAR_EYE, 1.9)):
            K.rrect(d, K.home[0] + cx - rx, K.home[1] + cy - 2.2, K.home[0] + cx + rx, K.home[1] + cy + 2.0, 0.8, None, FRAME, 0.6)  # type: ignore[arg-type]
        K.line(d, [K.at(NEAR_EYE[0] + 3.0, -1.6), K.at(FAR_EYE[0] - 1.9, -1.7)], FRAME, 0.6)
        K.line(d, [K.at(NEAR_EYE[0] - 3.0, -1.6), K.at(-4.6, -1.0)], FRAME, 0.6)

    return K.piece(("hinter_glasses",), paint)


_head = R.make_head(K, ("hinter",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.8, 7.8, 9.4), jaw=(2.6, 4.2, 5.2, 7.8),
                    nose=((7.2, -1.2), (10.8, 3.0), (10.0, 4.6), (7.2, 5.0)), ear=(-5.0, 1.0, 2.2, 3.3), shape=_hair_shape, under=_hair, over=_face)
_eyes = R.make_eyes(K, (NEAR_EYE[0] + 0.2, NEAR_EYE[1] + 0.2), (FAR_EYE[0] + 0.1, FAR_EYE[1] + 0.2), ink=INK, white=None, lid=SKIN_DEEP, size=0.9)
_brows = R.make_brows(K, [(-1.2, -4.6), (1.6, -5.4), (4.4, -4.8)], [(5.8, -5.0), (7.2, -5.4), (8.6, -4.8)], HAIR, 1.2, under=HAIR_SHADE)
_mouth = R.make_mouth(K, (5.4, 8.4), (124, 60, 62, 255), wide=0.85)

X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_glasses(), "glasses"), (_brows(R.brow_mood(pose)), "brows"),
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
X.set_rest(lean=5.0, na=BEHIND_NEAR, fa=BEHIND_FAR, nf=(-3.8, 0.0, 0.0), ff=(4.8, 0.0, 0.0))


@X.row
def idle(i: int, n: int):
    # His hands behind him, and his eyes on a space with more room in it.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 + 0.3 * s), lean=5.0 + s, head=(0.3, 0.0, -6.0 + 3.0 * c), eyes="closed" if i == n - 2 else "up" if c < 0.2 else "open",
             mouth="smile" if c < -0.4 else "flat")


@X.row
def walk(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 8.6, 4.6)
    return P(hip=(0.5, 0.8 * math.cos(2.0 * ph)), lean=7.0, head=(0.3, 0.0, -2.0 + 1.5 * s), nf=nf, ff=ff, hem=(1.0 + abs(c), abs(c)))


@X.row
def talk(i: int, n: int):
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), lean=4.0, head=(0.4, 0.0, 2.0 * s), na=(14.0 + 3.0 * c, 6.0 - 5.0 * max(0.0, s)), nh="open", mouth=("open", "smile", "big", "smile")[i % 4],
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


#: Folded in on himself, inside the surface.
WRAPPED = P(hip=(0.0, 5.0), lean=10.0, head=(0.5, 1.0, 10.0), na=(9.0, 4.0), fa=(6.0, 7.0), nh="fist", fh="fist", eyes="closed", brows=-1.0, mouth="flat",
            nf=(-5.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0))


@X.row
def manifold_shrinkwrap(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, P()), (0.25, WRAPPED), (0.85, WRAPPED), (1.0, P())])


X.alias(block="manifold_shrinkwrap", taunt="shout_14")
X.rows = [("idle", 8, 145), ("walk", 8, 105), ("talk", 8, 108), ("interact", 10, 92), ("hint", 10, 92), ("visualize_2d", 12, 92), ("shout_14", 12, 78),
          ("shout_3", 12, 78), ("manifold_shrinkwrap", 16, 82), ("block", 16, 82), ("taunt", 12, 78)]

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


def _wrap(tight: int, turn: int):
    """The surface: rings round him, ``tight`` of 4 closed in."""

    def paint(d) -> None:
        r = 44.0 - 5.0 * tight
        for k in range(3):
            ry = r * (0.26 + 0.1 * k)
            pts = [K.at(r * 0.62 * math.cos(math.radians(a + turn + 40 * k)), -4.0 + (k - 1) * 24.0 + ry * math.sin(math.radians(a + turn + 40 * k))) for a in range(0, 361, 15)]
            K.line(d, pts, NET_DARK, 2.2)
            K.line(d, pts, NET, 0.9)

    return K.aligned(("wrap", tight, turn), paint)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
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
    elif anim in ("manifold_shrinkwrap", "block") and 0.15 <= u <= 0.9:
        tight = min(4, int((u - 0.15) / 0.12))
        out.append((_wrap(tight, 20 * i), pin((ctx.hip[0] + 2.0, ctx.hip[1] - 22.0)), "wrap", 0.0))
    elif anim == "interact" and 0.35 <= u <= 0.7:
        out.append((R.tick(K, 4.0, NET, NET_DARK), (ctx.hand[0] + 16.0, ctx.hand[1] - 5.0), "tick", 0.0))
    del n
    return out


X.effects = _effects

ROWS = X.rows
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)
TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
