"""Sprite generator for Python Goras: the geometer of the right angle, and the
python that chose to stay with him.

A parody of Pythagoras.

The look (2026-10-13): a man of middle years seen three quarters from the
front, facing right, as the old busts have him: a full dark beard, curled
hair held by a white band, a strong straight nose. A long white chiton to his
ankles with a blue key border, a cloak over his near shoulder, a bronze
triangle on his chest, sandals. The python is green and lies over his
shoulders: its tail hangs down his back, its head stands up in front of his
far shoulder and looks where he looks. It is a living animal, not an emblem,
and it does a good part of the acting.

He is drawn from the old pictures of the man and not from a type (Jon,
2026-10-13, of another person of this cast: "needs to read like paul erdos
not bearnie sanders"). He is a grown man, not a mascot. He holds nothing;
there is no drop shadow.

What he shows: the right triangle, with the square on each of its sides.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, the snake, how he stands and what he shows are
his.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, lerp, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "python_goras"


AUTHORING_DESCRIPTION = (
    "Parody of Pythagoras. The joke is not just the near-homophone 'Python '"
    "Goras'; the design pushes him toward a mystical mathematician whose "
    "relationship with triangles, ratios, and secretive doctrine is constantly "
    "literalized by a pet python. Visual inspirations include classical Greek "
    "philosopher iconography, schoolbook right-triangle diagrams, occult "
    "geometry, and cartoon snake charmers. The costume stays mostly toga-based "
    "so he still reads as Pythagoras rather than as a generic wizard."
)

GAMEPLAY_DESCRIPTION = (
    "A mid-range geometry controller. Python Goras should pressure space with "
    "triangle-shaped hit areas, measured pokes, and serpent-assisted lashes. "
    "He reads best as a thoughtful spacing character: not the heaviest hitter, "
    "but good at creating awkward approach angles and rewarding clean positioning. "
    "A future bespoke kit could include a right-triangle dash cut, a harmonic "
    "projectile, and a theorem stance that changes the angle of his follow-up."
)

SUGGESTED_BARKS = [
    "Observe the hypotenuse.",
    "All things are number!",
    "Mind the angle.",
    "The serpent agrees.",
    "You stand at the wrong vertex.",
]

FALLBACK_DIALOGUE_LINES = [
    "I seek the hidden ratios beneath ordinary things.",
    "Most people remember the triangle. Fewer remember the cult.",
    "The python is not symbolic. He simply chose to stay.",
    "Harmony, number, and a clean right angle can solve more than people think.",
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_python_goras", "display_name": "Python Goras"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "locomotion_hint": "Walk",
        "traits": [
            "humanoid",
            "mathematician",
            "philosopher",
            "snake_companion",
            "geometry_mage",
            "playable_candidate",
        ],
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
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "face_guide": {
            "center": {"x": 64.0, "y": 27.0},
            "size": {"w": 28.0, "h": 30.0},
            "source_size": {"w": 128.0, "h": 128.0},
        },
        "portrait": {"animation": "idle", "frame": 1},
    },
    "tags": [
        "humanoid",
        "mathematician",
        "philosopher",
        "snake_companion",
        "geometry_mage",
        "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "python_goras.geometry", "point": {"x": 64.0, "y": 26.0}},
        "chest": {"source": "python_goras.geometry", "point": {"x": 64.0, "y": 60.0}},
        "hand_l": {"source": "python_goras.geometry", "point": {"x": 47.0, "y": 70.0}},
        "hand_r": {"source": "python_goras.geometry", "point": {"x": 83.0, "y": 70.0}},
        "speech_bubble": {
            "source": "python_goras.geometry",
            "point": {"x": 64.0, "y": 4.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
        "action.melee.primary": {"animation": "slash", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "dialogue_hints": {
        "barks": SUGGESTED_BARKS,
        "fallback_lines": FALLBACK_DIALOGUE_LINES,
    },
    "authoring": {
        "authoring_description": AUTHORING_DESCRIPTION,
        "gameplay_description": GAMEPLAY_DESCRIPTION,
    },
}

CHITON: RGBA = (246, 242, 226, 255)
CHITON_DARK: RGBA = (196, 188, 168, 255)
CLOAK: RGBA = (226, 214, 184, 255)
CLOAK_DARK: RGBA = (170, 154, 124, 255)
KEY: RGBA = (60, 104, 170, 255)
BRONZE: RGBA = (206, 150, 76, 255)
BRONZE_DARK: RGBA = (132, 88, 48, 255)
SKIN: RGBA = (214, 168, 126, 255)
SKIN_SHADE: RGBA = (178, 130, 98, 255)
SKIN_DEEP: RGBA = (130, 86, 70, 255)
HAIR: RGBA = (62, 46, 40, 255)
HAIR_LIGHT: RGBA = (112, 88, 74, 255)
#: The band round his head is gold, with the leaves of a laurel. (A white
#: band and a white chiton read as a tennis player: Jon, 2026-10-13.)
BAND: RGBA = (236, 196, 92, 255)
BAND_DARK: RGBA = (160, 112, 44, 255)
SANDAL: RGBA = (124, 84, 50, 255)
SANDAL_DARK: RGBA = (74, 48, 34, 255)
INK: RGBA = (26, 22, 28, 255)
SNAKE: RGBA = (104, 176, 86, 255)
SNAKE_DARK: RGBA = (56, 110, 60, 255)
SNAKE_LIGHT: RGBA = (196, 226, 130, 255)
TONGUE: RGBA = (226, 70, 80, 255)
GLOW: RGBA = (252, 226, 130, 255)
GLOW_DARK: RGBA = (206, 136, 56, 255)
GLOW_FILL: RGBA = (252, 226, 130, 70)

#: 175 cm: straight, broad in the chest.
BUILD = Build(hip_up=50.0, thigh=24.2, shin=23.1, neck=(0.2, -37.0), upper=19.6, fore=18.6, near_shoulder=(-6.2, -32.6), far_shoulder=(7.8, -32.2),
              near_hip=(-3.6, 0.0), far_hip=(3.6, 0.0), head_up=(0.9, -12.6), height=112.0, half_width=(13.5, 15.0))

G = Person(TARGET_NAME, BUILD)
K = G.K
P = G.P
TOP = BUILD.neck[1] - 2.0
HEM = BUILD.hip_up - 6.0


# ---- The pieces --------------------------------------------------------------


def _front(d, hb: float, hf: float) -> None:
    """His cloak down from his near shoulder across him, the folds of the
    chiton, the blue key at its hem, and the bronze triangle on his chest."""
    K.poly(d, [K.at(-12.0, TOP), K.at(-1.0, TOP), K.at(9.6, -10.0), K.at(11.0 + hf, 8.0), K.at(-2.0, 14.0), K.at(-14.0 - hb, 8.0)], CLOAK)
    K.line(d, [K.at(-1.0, TOP), K.at(9.6, -10.0), K.at(11.0 + hf, 8.0)], KEY, 1.2)
    for x0, y0, x1, y1 in ((-7.0, -30.0, 2.0, -10.0), (-9.0, -20.0, -2.0, 2.0)):
        K.line(d, [K.at(x0, y0), K.at(x1, y1)], CLOAK_DARK, 0.6)
    for x in (-6.0, -1.0, 4.0, 8.0):
        K.line(d, [K.at(x, 16.0), K.at(x * 1.25 - hb * 0.3 + hf * 0.2, HEM - 5.0)], CHITON_DARK, 0.6)
    K.poly(d, [K.at(-20.0 - hb, HEM - 4.4), K.at(20.0 + hf, HEM - 4.4), K.at(20.0 + hf, HEM - 1.6), K.at(-20.0 - hb, HEM - 1.6)], KEY)
    for k in range(-5, 7):
        K.rrect(d, K.home[0] + k * 3.4, K.home[1] + HEM - 3.8, K.home[0] + k * 3.4 + 1.6, K.home[1] + HEM - 2.2, 0.0, CHITON)
    K.poly(d, [K.at(4.6, -26.0), K.at(8.6, -20.6), K.at(4.6, -20.6)], BRONZE, OUTLINE, 0.5)


G.torso = R.make_torso(K, ("goras",), CHITON, CHITON_DARK, back=(10.0, 10.4, 9.6, 12.6), front=(9.0, 10.8, 10.4, 12.2), hem_y=HEM, top=TOP,
                       shoulders=((-6.0, -32.0), (7.2, -31.8)), shoulder_r=(5.8, 5.2), shade_from=10.0, detail=_front)


def _hair_shape(d) -> None:
    # Curled hair, close to his head, and a full beard to his chest.
    K.oval(d, K.at(-1.0, -4.8), 9.2, 8.4, WHITE)
    K.poly(d, [K.at(-3.4, 3.0), K.at(9.0, 4.0), K.at(9.6, 9.0), K.at(7.0, 15.0), K.at(3.0, 17.6), K.at(-0.6, 13.0), K.at(-3.6, 8.0)], WHITE)


def _hair(d) -> None:
    K.poly(d, [K.at(20.0, -8.4), K.at(8.4, -8.4), K.at(4.0, -7.4), K.at(0.6, -6.0), K.at(-2.4, -4.4), K.at(-3.2, -1.4), K.at(-6.2, -1.4), K.at(-6.8, 3.6),
               K.at(-5.2, 4.8), K.at(-4.8, 6.6), K.at(-20.0, 6.6), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
    for x, y in ((-6.0, -8.0), (-2.0, -11.0), (3.0, -11.4), (-8.0, -3.0), (6.6, -10.0), (-7.6, 2.0)):
        K.oval(d, K.at(x, y), 1.5, 1.2, None, HAIR_LIGHT, 0.5)  # type: ignore[arg-type]
    # The gold band round his head, and its leaves.
    K.poly(d, [K.at(-10.0, -6.0), K.at(9.6, -9.6), K.at(9.6, -7.6), K.at(-10.0, -3.8)], BAND)
    for x in (-7.0, -3.0, 1.0, 5.0):
        y = -5.4 - (x + 10.0) * 0.18
        K.line(d, [K.at(x, y + 1.0), K.at(x + 1.8, y - 1.2)], BAND_DARK, 0.6)


def _beard(d) -> None:
    K.poly(d, [K.at(-3.6, 2.6), K.at(0.6, 4.6), K.at(4.6, 4.4), K.at(9.6, 4.8), K.at(9.8, 9.0), K.at(7.0, 15.4), K.at(3.0, 18.0), K.at(-0.8, 13.0),
               K.at(-3.8, 8.0)], HAIR)
    for x0, y0, x1, y1 in ((0.6, 8.0, 2.4, 15.0), (4.0, 8.4, 4.0, 16.0), (7.4, 8.0, 6.0, 13.6)):
        K.line(d, [K.at(x0, y0), K.at(x1, y1)], HAIR_LIGHT, 0.6)
    K.line(d, [K.at(3.6, 7.0), K.at(5.8, 7.6), K.at(8.0, 7.0)], (140, 84, 84, 255), 0.8)


_head = R.make_head(K, ("goras",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.4, 8.2, 9.0), jaw=(2.6, 4.2, 6.0, 7.4),
                    nose=((7.2, -1.4), (10.4, 3.0), (9.8, 4.6), (7.2, 5.0)), ear=(-5.0, 1.2, 2.1, 3.0), shape=_hair_shape, under=_hair, over=_beard)
_eyes = R.make_eyes(K, (1.4, -0.6), (7.0, -0.8), ink=INK, iris=(70, 46, 30, 255), size=0.95)
_brows = R.make_brows(K, [(-1.4, -3.8), (1.4, -4.6), (4.2, -3.8)], [(5.8, -4.0), (7.2, -4.6), (8.8, -3.8)], HAIR, 1.4)

G.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows")]
G.neck = R.make_neck(K, SKIN_SHADE, 5.4)
# His near arm is under his cloak to the elbow; his far arm is bare.
G.upper_arm = lambda near: [(0.0, 1.0, 7.8, 7.0, CLOAK)] if near else [(0.0, 1.0, 6.6, 5.6, SKIN_SHADE)]
G.forearm = lambda near: [(0.0, 1.0, 5.6, 4.8, SKIN if near else SKIN_SHADE)]
G.thigh = lambda near: [(0.0, 1.0, 7.0, 6.0, CHITON if near else CHITON_DARK)]
G.shin = lambda near: [(0.0, 0.5, 6.0, 5.6, CHITON if near else CHITON_DARK), (0.45, 1.0, 5.0, 4.4, SKIN if near else SKIN_SHADE)]
G.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, size=1.05)


def _sandal(near: bool):
    h = K.home

    def shape(d) -> None:
        K.oval(d, K.at(3.0, 0.6), 6.0, 2.8, WHITE)
        K.rrect(d, h[0] - 3.4, h[1] - 0.2, h[0] + 9.4, h[1] + BUILD.ankle_up + 0.4, 1.4, WHITE)
        K.oval(d, h, 2.8, 2.8, WHITE)

    def detail(d) -> None:
        K.rrect(d, h[0] - 5.0, h[1] + BUILD.ankle_up - 0.9, h[0] + 11.0, h[1] + BUILD.ankle_up + 2.0, 0.0, SANDAL_DARK)
        for x0, x1 in ((4.6, 6.4), (0.8, 2.4)):
            K.poly(d, [K.at(x0, -4.0), K.at(x1, -4.0), K.at(x1 + 1.0, BUILD.ankle_up), K.at(x0 + 1.0, BUILD.ankle_up)], SANDAL)
        K.line(d, [K.at(-3.0, -2.6), K.at(2.0, -3.0)], SANDAL, 1.2)

    return K.solid(("sandal", near), shape, SKIN if near else SKIN_SHADE, detail, outline=1.2, rim=0.25, shade=0.3, shade_colour=SKIN_DEEP)


G.shoe = _sandal


# ---- The python --------------------------------------------------------------


def _snake_head(open_: bool, tongue: bool):
    """Its head, along +x from its neck."""

    def shape(d) -> None:
        K.poly(d, [K.at(-1.0, -2.6), K.at(4.0, -3.6), K.at(8.4, -1.6), K.at(9.4, 0.4), K.at(4.0, 3.2), K.at(-1.0, 2.6)], WHITE)
        if open_:
            K.poly(d, [K.at(3.0, 1.0), K.at(8.6, 4.6), K.at(3.0, 4.2)], WHITE)
        if tongue:
            K.stroke(d, [K.at(9.0, 0.6), K.at(13.0, 0.6)], WHITE, 1.0)
            K.stroke(d, [K.at(13.0, 0.6), K.at(15.0, -1.0)], WHITE, 0.9)
            K.stroke(d, [K.at(13.0, 0.6), K.at(15.0, 2.2)], WHITE, 0.9)

    def detail(d) -> None:
        if tongue:
            K.poly(d, [K.at(9.0, -1.4), K.at(16.0, -2.4), K.at(16.0, 3.4), K.at(9.0, 2.4)], TONGUE)
        K.poly(d, [K.at(-1.0, 1.0), K.at(9.0, 1.4), K.at(9.0, 6.0), K.at(-1.0, 6.0)], SNAKE_LIGHT)
        if open_:
            K.poly(d, [K.at(3.4, 1.4), K.at(7.6, 3.8), K.at(3.4, 3.6)], TONGUE)
        K.oval(d, K.at(4.8, -1.2), 1.3, 1.3, (252, 232, 120, 255))
        K.oval(d, K.at(5.0, -1.2), 0.5, 1.0, INK)
        K.oval(d, K.at(8.2, -0.6), 0.4, 0.4, SNAKE_DARK)

    return K.solid(("snake_head", open_, tongue), shape, SNAKE, detail, outline=1.1, rim=0.3, shade=0.35, shade_colour=SNAKE_DARK)


def _snake_body(key: tuple, pts):
    """Its body through ``pts`` (from the pin it is placed at): one piece, cut
    on whole frame pixels, with a pale belly line and dark marks on its back."""
    pts = tuple((round(x, 1), round(y, 1)) for x, y in pts)

    def paint(d) -> None:
        line = [K.at(x, y) for x, y in pts]
        K.stroke(d, line, OUTLINE, 5.0 + 2.4)
        K.stroke(d, line, SNAKE, 5.0)
        K.line(d, [(x, y + 1.2) for x, y in line], SNAKE_LIGHT, 1.0)
        for k in range(1, len(line) - 1):
            a, b = line[k], line[k + 1]
            K.oval(d, ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0 - 0.8), 1.3, 1.0, SNAKE_DARK)
        K.oval(d, line[0], 1.6, 1.6, SNAKE)

    return K.aligned(("snake_body",) + tuple(key) + (pts,), paint)


def _spline(points, per: int = 4):
    """More points through ``points``, so the body bends and does not corner."""
    out = []
    n = len(points)
    for k in range(n - 1):
        p0, p1, p2, p3 = points[max(0, k - 1)], points[k], points[k + 1], points[min(n - 1, k + 2)]
        for j in range(per):
            t = j / per
            out.append(tuple(0.5 * (2 * p1[c] + (p2[c] - p0[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t * t
                                    + (3 * p1[c] - p0[c] - 3 * p2[c] + p3[c]) * t ** 3) for c in (0, 1)))
    out.append(points[-1])
    return out


def _snake_layers(ctx):
    """Where the python is this frame: ``(tail, front, head, turn)`` in frame
    pixels. Its tail hangs down his back; it goes behind his neck; and the
    front of it stands up from his far shoulder."""
    sway = 2.0 * math.sin(ctx.phase)
    reach = float(ctx.pose["snake"])  # 0: at rest. 1: it strikes.
    up = float(ctx.pose["rise"])  # 1: it stands tall beside his head.
    tail = [ctx.trunk(-9.6 - sway * 0.4, -8.0), ctx.trunk(-10.6, -16.0), ctx.trunk(-9.4, -25.0), ctx.trunk(-6.6, -33.0), ctx.trunk(-2.0, TOP + 0.6)]
    sh = ctx.trunk(7.6, TOP + 2.4)
    rest_head = ctx.trunk(17.0 + sway * 0.5, -31.0 - 5.0 * up + sway)
    head = (lerp(rest_head[0], ctx.hand[0] + 16.0, reach), lerp(rest_head[1], ctx.hand[1] - 2.0, reach))
    mid = ctx.trunk(12.0, -26.0 + 3.0 * (1.0 - up))
    mid = (lerp(mid[0], (sh[0] + head[0]) / 2.0, reach), lerp(mid[1], (sh[1] + head[1]) / 2.0 + 4.0, reach))
    neck_pt = (head[0] - 5.0, head[1] + (2.0 if reach < 0.5 else 0.6))
    front = [ctx.trunk(3.0, TOP + 0.6), sh, mid, neck_pt, (head[0] - 1.0, head[1])]
    turn = math.degrees(math.atan2(head[1] - neck_pt[1], head[0] - neck_pt[0])) * 0.5
    return tail, front, head, turn


def _snake_back(ctx) -> List[Stamp]:
    tail, _front, _head, _turn = _snake_layers(ctx)
    at = pin(ctx.hip)
    pts = _spline([(x - at[0], y - at[1]) for x, y in tail])
    return [(_snake_body(("tail",), pts), at, "snake_tail", 0.0)]


def _snake_front(ctx) -> List[Stamp]:
    _tail, front, head, turn = _snake_layers(ctx)
    at = pin(ctx.hip)
    pts = _spline([(x - at[0], y - at[1]) for x, y in front])
    strike = float(ctx.pose["snake"]) > 0.6
    flick = (not strike) and ctx.i % 4 == 1
    return [(_snake_body(("front",), pts), at, "snake_front", 0.0), (_snake_head(strike, flick), head, "snake_head", turn)]


G.layers["over_torso"].append(_snake_back)
G.layers["front"].append(_snake_front)


# ---- How he holds himself ----------------------------------------------------

#: One hand flat on his chest, over the triangle; the other hangs.
ON_CHEST = (7.0, 11.0)
G.set_rest(na=ON_CHEST, nh="flat", nf=(-3.6, 0.0, 0.0), ff=(4.6, 0.0, 0.0), snake=0.0, rise=0.0)


@G.row
def idle(i: int, n: int):
    # He is still. The python looks about for him.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.4 + 0.3 * s), head=(0.2, -0.2 * s, 2.0 * c), eyes="closed" if i == n - 2 else "open", rise=0.3 + 0.3 * c)


@G.row
def walk(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 7.4, 3.8)
    return P(hip=(0.5, 0.8 * math.cos(2.0 * ph)), lean=2.0, head=(0.0, 0.0, 1.2 * s), fa=(3.0 + 6.0 * c, 24.0), nf=nf, ff=ff,
             hem=(1.0 + 1.5 * abs(c), 0.5 + 1.5 * abs(c)), rise=0.2)


@G.row
def talk(i: int, n: int):
    # He teaches with his far hand. The python agrees.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), head=(0.3, 0.0, 2.0 * s), fa=(18.0 + 2.0 * c, 6.0 - 5.0 * max(0.0, s)), fh="open", brows=1.0 if s > 0.3 else 0.0,
             rise=0.5 + 0.5 * max(0.0, s))


@G.row
def taunt(i: int, n: int):
    # He draws the triangle in the air, and the python stands up to see it.
    up = P(lean=-3.0, head=(0.0, 0.0, -8.0), na=(14.0, -14.0), nh="point", brows=1.0, rise=1.0)
    return G.keys(shot(i, n), [(0.0, P()), (0.25, up), (0.5, dict(up, na=(24.0, -14.0))), (0.75, dict(up, na=(24.0, -2.0))), (1.0, dict(up, na=(14.0, -2.0)))])


@G.row
def slash(i: int, n: int):
    # He points, and it is the python that goes.
    wind = P(hip=(-2.0, 2.0), lean=-6.0, na=(-4.0, 6.0), nh="point", brows=-1.0, rise=1.0)
    out = P(hip=(4.0, 3.0), lean=12.0, na=(25.0, 2.0), nh="point", nf=(-7.0, 0.0, 10.0), ff=(8.0, 0.0, 0.0), brows=-1.0, snake=1.0, hem=(4.0, 1.0))
    return G.keys(shot(i, n), [(0.0, P()), (0.25, wind), (0.5, out), (0.75, out), (1.0, P())])


@G.row
def hurt(i: int, n: int):
    return G.keys(shot(i, n), [(0.0, P(lean=-4.0, eyes="wide", rise=1.0)), (0.4, dict(G.full(R.STRUCK), rise=1.0)), (1.0, P(lean=-6.0, eyes="wince"))])


@G.row
def death(i: int, n: int):
    # He goes over backward, straight, as a column goes (a man in a robe to
    # his ankles does not sit down in it). The python stays up.
    back = dict(G.full(R.STRUCK), lean=-12.0, rise=1.0)
    down = dict(G.full(R.SUPINE), rise=0.6)
    return G.keys(shot(i, n), [(0.0, back), (0.2, dict(back, lean=-20.0)), (0.7, down), (1.0, down)])


G.rows = [("idle", 6, 150), ("walk", 8, 96), ("talk", 8, 112), ("taunt", 8, 108), ("slash", 7, 84), ("hurt", 4, 86), ("death", 8, 112)]


# ---- From the front ------------------------------------------------------------

def _front_chiton(d) -> None:
    """His chiton from the front: pinned at each shoulder with bronze, a
    cord at his waist, the key pattern at its hem, and the folds."""
    K.poly(d, [K.at(-3.6, TOP - 1.0), K.at(3.6, TOP - 1.0), K.at(0.0, TOP + 7.0)], SKIN_SHADE)
    # His cloak, from his right shoulder across him, with its blue edge; and
    # the bronze triangle on his chest.
    K.poly(d, [K.at(-20.0, TOP), K.at(-1.6, TOP), K.at(10.4, -13.0), K.at(20.0, -4.0), K.at(20.0, 9.0), K.at(-2.0, 14.0), K.at(-20.0, 8.0)], CLOAK)
    K.line(d, [K.at(-1.6, TOP), K.at(10.4, -13.0)], KEY, 1.2)
    K.line(d, [K.at(-20.0, 8.0), K.at(-2.0, 14.0), K.at(20.0, 9.0)], CLOAK_DARK, 0.8)
    for x0, y0, x1, y1 in ((-6.6, -30.0, 3.0, -10.0), (-8.4, -20.0, -1.0, 4.0)):
        K.line(d, [K.at(x0, y0), K.at(x1, y1)], CLOAK_DARK, 0.6)
    K.poly(d, [K.at(4.4, -27.0), K.at(8.4, -21.6), K.at(4.4, -21.6)], BRONZE, OUTLINE, 0.5)
    K.oval(d, K.at(6.6, TOP + 4.0), 1.5, 1.5, BRONZE, BRONZE_DARK, 0.5)
    for x in (-5.0, -1.6, 1.6, 5.0):
        K.line(d, [K.at(x, 16.0), K.at(x * 1.5, HEM - 6.0)], CHITON_DARK, 0.6)
    K.poly(d, [K.at(-20.0, HEM - 5.0), K.at(20.0, HEM - 5.0), K.at(20.0, HEM - 2.0), K.at(-20.0, HEM - 2.0)], KEY)
    for k in range(-5, 6):
        K.poly(d, [K.at(k * 2.6 - 0.6, HEM - 4.4), K.at(k * 2.6 + 0.6, HEM - 4.4), K.at(k * 2.6 + 0.6, HEM - 2.8), K.at(k * 2.6 - 0.6, HEM - 2.8)], CHITON)


def _front_hair_shape(d) -> None:
    # Thick dark curls, and a full beard to his chest.
    K.oval(d, K.at(0.0, -5.6), 9.6, 7.6, WHITE)
    K.poly(d, [K.at(-7.4, 2.0), K.at(7.4, 2.0), K.at(6.4, 11.0), K.at(0.0, 16.0), K.at(-6.4, 11.0)], WHITE)


def _front_hair(d) -> None:
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -1.0), K.at(7.4, -1.0), K.at(7.0, -5.0), K.at(4.0, -7.2), K.at(0.0, -6.4), K.at(-4.0, -7.2),
               K.at(-7.0, -5.0), K.at(-7.4, -1.0), K.at(-20.0, -1.0)], HAIR)
    K.poly(d, [K.at(-20.0, -9.8), K.at(20.0, -9.8), K.at(20.0, -7.6), K.at(-20.0, -7.6)], BAND)
    for sx in (-1.0, 1.0):
        for x in (1.4, 4.4, 7.4):
            K.line(d, [K.at(x * sx, -7.8), K.at((x + 1.6) * sx, -9.6)], BAND_DARK, 0.6)
    for x, y in ((-5.0, -11.6), (0.0, -12.6), (5.0, -11.6), (-7.6, -4.0), (7.6, -4.0)):
        K.line(d, [K.at(x - 1.4, y + 0.8), K.at(x, y - 0.8), K.at(x + 1.4, y + 0.6)], HAIR_LIGHT, 0.6)


def _front_beard(d) -> None:
    K.line(d, [K.at(-0.3, 0.4), K.at(-1.4, 3.6), K.at(0.0, 4.4), K.at(1.4, 3.6)], SKIN_DEEP, 0.7)
    K.poly(d, [K.at(-7.6, 1.6), K.at(-4.0, 5.2), K.at(0.0, 4.8), K.at(4.0, 5.2), K.at(7.6, 1.6), K.at(6.4, 11.0), K.at(0.0, 16.0), K.at(-6.4, 11.0)], HAIR)
    K.line(d, [K.at(-2.4, 8.2), K.at(0.0, 8.8), K.at(2.4, 8.2)], (150, 90, 84, 255), 0.8)
    for x in (-3.4, 0.0, 3.4):
        K.line(d, [K.at(x, 10.0), K.at(x * 0.7, 14.0)], HAIR_LIGHT, 0.5)


G.front_torso = R.make_front_torso(K, ("goras",), CHITON, CHITON_DARK, [(TOP, 4.4), (TOP + 3.6, 9.6), (-24.0, 10.2), (-9.0, 10.0), (HEM, 12.4)],
                                   shoulder=(7.6, -32.6, 4.6, 5.0), detail=_front_chiton)
G.front_head_layers = R.front_face(R.make_front_head(K, ("goras",), SKIN, SKIN_DEEP, wide=8.0, jaw=6.6, chin=3.8, ears=SKIN, shape=_front_hair_shape, hair=_front_hair,
                                                    face=_front_beard),
                                   R.make_front_eyes(K, ("goras",), ink=INK, iris=(70, 46, 30, 255), spread=3.4, y=-0.6, size=0.9),
                                   R.make_front_brows(K, ("goras",), HAIR, spread=3.4, y=-4.0, width=1.4))
G.front_shoe = R.make_front_shoe(K, SANDAL, SANDAL_DARK, BUILD.ankle_up)
G.front_span = (8.4, 4.8)


def _snake_face(tongue: bool):
    """The head of the python from the front, from its middle."""

    def shape(d) -> None:
        K.poly(d, [K.at(-3.6, -2.6), K.at(0.0, -3.6), K.at(3.6, -2.6), K.at(4.2, 0.4), K.at(2.4, 3.4), K.at(-2.4, 3.4), K.at(-4.2, 0.4)], WHITE)
        if tongue:
            K.stroke(d, [K.at(0.0, 3.0), K.at(0.0, 6.4)], WHITE, 1.0)
            K.stroke(d, [K.at(0.0, 6.4), K.at(-1.6, 8.2)], WHITE, 0.9)
            K.stroke(d, [K.at(0.0, 6.4), K.at(1.6, 8.2)], WHITE, 0.9)

    def detail(d) -> None:
        if tongue:
            K.poly(d, [K.at(-2.6, 3.4), K.at(2.6, 3.4), K.at(2.6, 9.4), K.at(-2.6, 9.4)], TONGUE)
        K.poly(d, [K.at(-2.6, 1.6), K.at(2.6, 1.6), K.at(2.4, 3.4), K.at(-2.4, 3.4)], SNAKE_LIGHT)
        for sx in (-1.0, 1.0):
            K.oval(d, K.at(2.2 * sx, -0.8), 1.3, 1.3, (252, 232, 120, 255))
            K.oval(d, K.at(2.2 * sx, -0.8), 0.5, 1.0, INK)
            K.oval(d, K.at(0.8 * sx, 1.8), 0.35, 0.35, SNAKE_DARK)

    return K.solid(("snake_face", tongue), shape, SNAKE, detail, outline=1.1, rim=0.3, shade=0.35, shade_colour=SNAKE_DARK)


def _front_snake(ctx) -> List[Stamp]:
    """The python from the front. It lies over his shoulders, behind his
    neck: its tail hangs down his chest at one side, and at the other the
    front of it stands up beside his head and looks at you."""
    sway = 1.6 * math.sin(ctx.phase)
    up = 4.0 if ctx.anim == "front_talk" else 0.0
    at = pin(ctx.neck)
    tail = [(-6.6, 1.6), (-7.0, 7.0), (-5.4, 14.0), (-3.8, 21.0), (-4.8 + sway * 0.5, 27.0)]
    head = (17.0 + sway, -9.0 - up + sway * 0.5)
    front = [(6.6, 1.6), (10.0, 3.0), (13.6, 1.0), (15.6 + sway * 0.5, -3.0 - up * 0.5), (head[0] - 0.4, head[1] + 3.0)]
    return [(_snake_body(("front_tail",), _spline(tail)), at, "front_snake_tail", 0.0), (_snake_body(("front_rise",), _spline(front)), at, "front_snake_rise", 0.0),
            (_snake_face(ctx.i % 4 == 1), (at[0] + head[0], at[1] + head[1]), "front_snake_head", 4.0 * math.sin(ctx.phase))]


G.front_effects = _front_snake
R.add_front_rows(G, hands="sides")

# ---- What he shows -----------------------------------------------------------


def _triangle(size: int, sides: int):
    """The right triangle, ``sides`` of its sides drawn (it is drawn a side at
    a time), and the square on each side when all three are there."""
    a, b = float(size), float(size) * 0.75
    pts = [(0.0, 0.0), (a, 0.0), (a, -b)]

    def paint(d) -> None:
        lines = [(pts[0], pts[1]), (pts[1], pts[2]), (pts[2], pts[0])][:sides]
        if sides >= 3:
            K.poly(d, [K.at(*q) for q in pts], GLOW_FILL)
            K.rrect(d, K.home[0], K.home[1] + 0.6, K.home[0] + a, K.home[1] + 0.6 + a * 0.34, 0.0, GLOW_FILL)
            K.rrect(d, K.home[0] + a + 0.6, K.home[1] - b, K.home[0] + a + 0.6 + b * 0.34, K.home[1], 0.0, GLOW_FILL)
        for edge in (True, False):
            for q0, q1 in lines:
                K.stroke(d, [K.at(*q0), K.at(*q1)], GLOW_DARK if edge else GLOW, 2.6 if edge else 1.2)
        if sides >= 2:
            K.line(d, [K.at(a - 3.0, 0.0), K.at(a - 3.0, -3.0), K.at(a, -3.0)], GLOW, 0.7)

    return K.aligned(("triangle", size, sides), paint)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    if ctx.anim == "taunt" and ctx.u > 0.2:
        sides = 1 if ctx.u < 0.5 else 2 if ctx.u < 0.75 else 3
        out.append((_triangle(16, sides), pin((ctx.shoulder[0] + 20.0, ctx.shoulder[1] - 4.0)), "triangle", 0.0))
    elif ctx.anim == "slash" and 0.45 <= ctx.u <= 0.8:
        out.append((_triangle(12, 3), pin((ctx.hand[0] + 26.0, ctx.hand[1] + 6.0)), "triangle", 0.0))
    elif ctx.anim == "talk" and ctx.i in (2, 3):
        out.append((_triangle(10, 3), pin((ctx.far_hand[0] + 6.0, ctx.far_hand[1] - 8.0)), "triangle", 0.0))
    return out


G.effects = _effects
ROWS = G.rows


def _render_frame(anim: str, frame_idx: int, nframes: int):
    return G.render_frame(anim, frame_idx, nframes)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return G.render(out_dir, ACTOR_METADATA)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Python Goras spritesheet.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
