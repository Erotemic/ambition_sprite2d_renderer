"""Sprite generator for Willson: a pelican riding a bicycle.

A parody of Simon Willison, who asks every new model to draw a pelican riding
a bicycle. He is the picture: if he has two wheels, a frame that joins them
and a bird whose feet are on the pedals, the model passed.

The look (redrawn 2026-10-11): a round white pelican with a long orange bill
and a deep pouch, a small crest, round glasses, and long orange legs, on a red
bicycle. He wears a brown satchel with a ``W`` on its flap, on a strap across
his chest. He faces right.

The bird and the bicycle are one actor and two rigs. The bicycle (frame,
cranks, pedals) is painted whole for each tilt and crank turn, and each wheel
for each turn, on whole pixels (``Kit.aligned``): spokes and thin tubes do not
survive being reduced and then turned. The bird is turned pieces: his wings
and legs are two bones through a solved joint, to the grips and the pedals.

Rows: ``idle`` (a track stand: he rocks the pedals to stay up), ``walk`` and
``run`` (he pedals), ``slash`` (the front wheel comes up and his bill comes
down), ``fly`` (he carries the bicycle by its top tube), ``taunt`` (both wings
up and a clack of the bill), ``hurt``, and ``death`` (the bicycle goes over
backward onto its saddle and he sits down beside it).
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from PIL import Image

from ._ai_era_kit import OUTLINE, WHITE, Kit, Point, Pose, RGBA, angle, ease, keys, lerp, mix, pin, solve, turned

TARGET_NAME = "willson"
FRAME_SIZE = (256, 240)
GROUND = 226.0
CX = 112.0

# ---- The bicycle: from the ground between its wheels, up is negative ---------

WHEEL = 27.0
REAR: Point = (-38.0, -WHEEL)
FRONT: Point = (38.0, -WHEEL)
BRACKET: Point = (-3.0, -28.0)
CRANK = 9.0
#: Where he sits.
SADDLE: Point = (-16.0, -68.0)
#: Where a wing holds the handlebar.
GRIP: Point = (27.5, -85.0)
#: The top tube, where his feet hold it in the air.
TUBE_BACK: Point = (-5.0, -63.0)
TUBE_FRONT: Point = (8.0, -65.0)
#: A wheel is painted at each of these turns.
WHEEL_STEP = 15.0

# ---- The bird: from his seat, his back straight up ---------------------------

NECK_ROOT: Point = (12.0, -42.0)
NECK_LOW, NECK_HIGH = 15.0, 14.0
NEAR_SHOULDER: Point = (6.0, -35.0)
FAR_SHOULDER: Point = (10.0, -36.0)
WING_UPPER, WING_FORE = 19.0, 17.0
NEAR_HIP: Point = (3.0, -3.0)
FAR_HIP: Point = (6.0, -4.0)
THIGH, SHIN = 28.0, 28.0
ANKLE_UP = 2.5
BAG_HANGS: Point = (-9.0, -15.0)

FEATHER: RGBA = (248, 246, 238, 255)
FEATHER_SHADE: RGBA = (204, 210, 228, 255)
FEATHER_DARK: RGBA = (150, 158, 186, 255)
PRIMARY: RGBA = (56, 52, 72, 255)
BILL: RGBA = (255, 172, 58, 255)
BILL_DARK: RGBA = (224, 118, 38, 255)
POUCH: RGBA = (255, 214, 130, 255)
POUCH_DARK: RGBA = (234, 166, 84, 255)
LEG: RGBA = (246, 142, 54, 255)
LEG_DARK: RGBA = (204, 100, 42, 255)
INK: RGBA = (30, 22, 38, 255)
GLASSES: RGBA = (48, 38, 66, 255)
LENS: RGBA = (176, 220, 255, 170)
BIKE: RGBA = (226, 64, 62, 255)
BIKE_DARK: RGBA = (158, 36, 54, 255)
BIKE_LIGHT: RGBA = (255, 142, 122, 255)
TYRE: RGBA = (50, 46, 66, 255)
RIM: RGBA = (204, 210, 230, 255)
SPOKE: RGBA = (176, 184, 210, 255)
METAL: RGBA = (124, 130, 156, 255)
METAL_LIGHT: RGBA = (196, 202, 222, 255)
SADDLE_BROWN: RGBA = (112, 70, 50, 255)
BAG: RGBA = (152, 98, 58, 255)
BAG_DARK: RGBA = (106, 64, 42, 255)
BAG_FLAP: RGBA = (180, 122, 72, 255)
LETTER: RGBA = (255, 242, 208, 255)
BELL: RGBA = (250, 208, 88, 255)
REFLECTOR: RGBA = (255, 176, 60, 255)

K = Kit(FRAME_SIZE)

ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Willson"},
    "body": {
        "body_plan": "AvianCyclist",
        "body_kind": "Grounded",
        "mass_class": "Medium",
        "traits": ["pelican", "bicycle_bound", "inseparable_composite_actor", "aerial_bicycle_carry", "pedal_locomotion", "beak_melee",
                   "expressive"],
        "locomotion_hint": "Walk",
    },
    "visual": {"default_pose": "idle", "facing_policy": "side_right"},
    "tags": ["npc", "avian", "cyclist", "custom", "beak_melee"],
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "locomotion.fly": {"animation": "fly", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {"t": 0.45, "event": "hitbox_active_start", "source": "explicit.profile.willson"},
                {"t": 0.7, "event": "hitbox_active_end", "source": "explicit.profile.willson"},
            ],
        },
        "combat.hurt": {"animation": "hurt", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
    "authoring_description": (
        "Willson is a pelican riding a bicycle, built from the kind of compositional prompt that "
        "image-generation systems notoriously mishandle. The extra L distinguishes him from "
        "unrelated Wilson characters and makes him a living benchmark for whether an intelligence "
        "can keep rider, bird, wheels, and motion coherent."
    ),
    "gameplay_description": (
        "Use as a benchmark mascot, composite traversal character, courier, or comic evaluator of "
        "generated art. Pelican and bicycle are one actor: he can pedal, carry the bicycle in "
        "flight, and complain whenever a depiction loses a wheel. As an enemy he rides at what "
        "he sees and brings his bill down on it."
    ),
    "dialogue_hints": {
        "barks": [
            "Draw me riding this bicycle. SVG only.",
            "Every intelligence arrives with a brass band. Then it gives the bicycle one wheel.",
            "A benchmark that cannot molt is just homework with a leaderboard.",
        ]
    },
}


# ---- The pose ----------------------------------------------------------------

#: Riding, upright and still. A row states what differs.
REST: Pose = {
    # The bicycle: moved (whole pixels), and turned about a point of its own
    # (the foot of its rear wheel: a wheelie).
    "bike": (0.0, 0.0),
    "tilt": 0.0,
    "pivot": (REAR[0], 0.0),
    # How far its cranks have turned (0: the near pedal is forward) and its
    # wheels have (in `WHEEL_STEP`s).
    "crank": 0.0,
    "wheel": 0.0,
    # His seat from the saddle. `free` 1: his seat is at `at` (from the ground
    # under the frame's middle) and he does not turn with the bicycle.
    "seat": (0.0, 0.0),
    "free": 0.0,
    "at": (0.0, 0.0),
    # He leans this far forward.
    "lean": 20.0,
    # His head from the root of his neck, its tilt, and how far his bill is open.
    "head": (11.0, -24.0),
    "tilt_head": 0.0,
    "gape": 0.0,
    "eyes": "open",
    # His wings: "bars" hold the grips, "spread" are out at `flap` (0 is up,
    # negative is back), "fold" are at his sides.
    "wings": "bars",
    "flap": -60.0,
    # Each foot: on its "pedal", or "at" a place (from the ground under the
    # frame's middle; `nf` is the near one).
    "feet": "pedal",
    "nf": (0.0, 0.0),
    "ff": (0.0, 0.0),
    # His bag swings this far back.
    "bag": 0.0,
}


def P(**kw) -> Pose:
    unknown = set(kw) - set(REST)
    assert not unknown, unknown
    return dict(REST, **kw)


ROW_POSES: Dict[str, Callable[[int, int], Pose]] = {}


def row(fn: Callable[[int, int], Pose]) -> Callable[[int, int], Pose]:
    ROW_POSES[fn.__name__] = fn
    return fn


def _loop(i: int, n: int) -> Tuple[float, float, float]:
    ph = math.tau * i / max(1, n)
    return ph, math.sin(ph), math.cos(ph)


def _shot(i: int, n: int) -> float:
    return i / max(1, n - 1)


@row
def idle(i: int, n: int) -> Pose:
    # A track stand: he rocks the pedals a little forward and back to stay up.
    _, s, c = _loop(i, n)
    rock = (0, 1, 1, 0, 0, -1, -1, 0)[i % 8]
    return P(crank=20.0 + 15.0 * rock, wheel=float(rock), lean=18.0 + 1.5 * s, head=(10.0 + 1.5 * c, -24.5 - 0.6 * s), tilt_head=-4.0 + 3.0 * c,
             eyes="closed" if i == n - 2 else "open", bag=2.0 * s)


@row
def walk(i: int, n: int) -> Pose:
    _, s, _c = _loop(i, n)
    bob = math.sin(2.0 * math.tau * i / n)
    return P(crank=45.0 * i, wheel=3.0 * i, seat=(0.0, -0.8 * bob), lean=21.0 + 1.5 * bob, head=(11.0, -24.0 + 0.8 * bob), tilt_head=2.0 * s,
             bag=4.0 + 3.0 * bob)


@row
def run(i: int, n: int) -> Pose:
    # Out of the saddle and over the bars.
    bob = math.sin(2.0 * math.tau * i / n)
    return P(crank=90.0 * i, wheel=9.0 * i, seat=(5.0, -6.0 - 1.2 * bob), lean=37.0 + 2.0 * bob, head=(16.0, -18.0 + bob), tilt_head=10.0,
             gape=4.0 + 3.0 * bob, bag=24.0 + 5.0 * bob)


@row
def slash(i: int, n: int) -> Pose:
    # The front wheel comes up, and his bill comes down with the wheel.
    ride = P(crank=0.0, wheel=0.0)
    rear_up = P(tilt=-17.0, crank=70.0, wheel=4.0, seat=(-2.0, -3.0), lean=4.0, head=(1.0, -27.0), tilt_head=-34.0, gape=16.0, bag=-12.0)
    strike = P(tilt=0.0, bike=(4.0, 0.0), crank=150.0, wheel=9.0, seat=(6.0, -5.0), lean=44.0, head=(26.0, -9.0), tilt_head=26.0, gape=0.0,
               eyes="wide", bag=30.0)
    return keys(_shot(i, n), [(0.0, ride), (0.3, rear_up), (0.42, rear_up), (0.58, strike), (0.76, strike), (1.0, dict(ride, crank=180.0, wheel=12.0))])


@row
def fly(i: int, n: int) -> Pose:
    # He carries it: his feet hold the top tube and the wheels turn in the air.
    ph, s, c = _loop(i, n)
    return P(bike=(0.0, round(-16.0 - 3.0 * s)), tilt=round(3.0 * c), pivot=(0.0, -64.0), crank=30.0, wheel=float(i), seat=(4.0, -24.0),
             lean=30.0 + 3.0 * c, head=(14.0, -21.0), tilt_head=6.0, wings="spread", flap=-88.0 - 50.0 * s, feet="tube", bag=14.0 + 6.0 * c)


@row
def taunt(i: int, n: int) -> Pose:
    clack = (0.0, 26.0, 2.0, 26.0, 2.0, 0.0)[i % 6]
    up = (0.0, 1.0, 0.7, 1.0, 0.7, 0.0)[i % 6]
    return P(tilt=round(-9.0 * up), crank=30.0 + 20.0 * up, wheel=float(round(2.0 * up)), lean=lerp(20.0, 2.0, up), head=(lerp(11.0, 5.0, up), -24.0 - 3.0 * up),
             tilt_head=lerp(0.0, -32.0, up), gape=clack, eyes="happy" if up > 0.5 else "open", wings="spread" if up > 0.5 else "bars",
             flap=-30.0 - 26.0 * (i % 2), bag=-8.0 * up)


STRUCK = P(bike=(-4.0, 0.0), tilt=-15.0, crank=40.0, wheel=-2.0, seat=(-3.0, -5.0), lean=-8.0, head=(0.0, -26.0), tilt_head=-30.0, gape=24.0,
           eyes="wince", wings="spread", flap=-20.0, bag=-22.0)


@row
def hurt(i: int, n: int) -> Pose:
    back = P(bike=(-2.0, 0.0), tilt=-4.0, crank=20.0, wheel=-1.0, lean=10.0, head=(7.0, -25.0), tilt_head=-10.0, gape=8.0, eyes="wince", bag=-8.0)
    return keys(_shot(i, n), [(0.0, P(eyes="wide", gape=10.0)), (0.34, STRUCK), (0.67, STRUCK), (1.0, back)])


def _lowest(tilt: float, pivot: Point) -> float:
    """How far under the ground the lowest thing of a bicycle is when it is
    tilted ``tilt`` about ``pivot`` and not moved: a tyre, the saddle or a grip."""
    low = -1e9
    for point, reach in ((REAR, WHEEL), (FRONT, WHEEL), ((-17.0, -71.0), 1.5), ((GRIP[0], GRIP[1] - 1.0), 2.5)):
        q = turned((point[0] - pivot[0], point[1] - pivot[1]), tilt)
        low = max(low, pivot[1] + q[1] + reach)
    return low


@row
def death(i: int, n: int) -> Pose:
    # The bicycle goes over backward and comes to rest on its saddle and its
    # bars, a wheel still turning. He sits down in front of it.
    u = _shot(i, n)
    middle = (0.0, -40.0)
    over = ease(min(1.0, u / 0.62))
    bike_tilt = round(lerp(-15.0, -184.0, over))
    slide = round(lerp(-4.0, -30.0, over))
    # It turns over on the ground: whatever is lowest is on it.
    lift = round(-_lowest(float(bike_tilt), middle))
    seat_start = (SADDLE[0] - 6.0, SADDLE[1] - 8.0)
    thrown = keys(u, [
        (0.0, dict(STRUCK, free=0.0, at=seat_start)),
        (0.2, dict(STRUCK, free=1.0, at=(seat_start[0] + 8.0, seat_start[1] - 18.0), lean=-20.0, feet="at", nf=(8.0, -58.0), ff=(14.0, -62.0),
                   flap=-70.0)),
        (0.45, dict(STRUCK, free=1.0, at=(44.0, -64.0), lean=10.0, feet="at", nf=(70.0, -34.0), ff=(74.0, -40.0), flap=-110.0, tilt_head=0.0,
                    head=(8.0, -25.0))),
        (0.66, P(free=1.0, at=(56.0, -9.0), lean=-12.0, feet="at", nf=(92.0, -1.0), ff=(87.0, -2.0), wings="fold", head=(6.0, -22.0),
                 tilt_head=24.0, gape=14.0, eyes="wince", bag=-30.0)),
        (1.0, P(free=1.0, at=(56.0, -9.0), lean=-6.0, feet="at", nf=(92.0, -1.0), ff=(87.0, -2.0), wings="fold", head=(9.0, -21.0),
                tilt_head=34.0, gape=4.0, eyes="closed", bag=-30.0)),
    ])
    return dict(thrown, bike=(float(slide), float(lift)), tilt=float(bike_tilt), pivot=middle, crank=40.0, wheel=float(-2 + i))


ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 140),
    ("walk", 8, 78),
    ("run", 8, 52),
    ("slash", 8, 72),
    ("fly", 8, 86),
    ("taunt", 6, 108),
    ("hurt", 4, 94),
    ("death", 10, 92),
]
assert [name for name, _, _ in ROWS] == list(ROW_POSES), "every row has a pose, in sheet order"


# ---- The bicycle's pieces ----------------------------------------------------


def _wheel(step: int):
    """A wheel from its hub, turned ``step`` steps. A reflector on one spoke
    and the valve across from it show the turn."""
    turn = math.radians(step * WHEEL_STEP)

    def spoke(k: int, r: float) -> Point:
        a = turn + k * math.tau / 6.0
        return K.at(r * math.cos(a), r * math.sin(a))

    def paint(d) -> None:
        for k in range(6):
            K.line(d, [K.home, spoke(k, WHEEL - 4.0)], SPOKE, 0.9)
        K.oval(d, K.home, WHEEL, WHEEL, None, OUTLINE, 7.4)  # type: ignore[arg-type]
        K.oval(d, K.at(0.0, 0.0), WHEEL - 1.1, WHEEL - 1.1, None, TYRE, 4.4)  # type: ignore[arg-type]
        K.oval(d, K.at(0.0, 0.0), WHEEL - 5.3, WHEEL - 5.3, None, RIM, 1.4)  # type: ignore[arg-type]
        K.oval(d, K.at(0.0, 0.0), WHEEL - 1.3, WHEEL - 1.3, None, mix(TYRE, WHITE, 0.22), 0.7)  # type: ignore[arg-type]
        a, b = spoke(0, 12.0), spoke(0, 18.0)
        K.stroke(d, [a, b], OUTLINE, 4.6)
        K.stroke(d, [a, b], REFLECTOR, 2.6)
        K.oval(d, spoke(3, WHEEL - 7.6), 1.4, 1.4, METAL)
        K.oval(d, K.home, 3.6, 3.6, METAL, OUTLINE, 1.0)
        K.oval(d, K.at(-0.8, -0.8), 1.2, 1.2, METAL_LIGHT)

    return K.aligned(("wheel", step % 24), paint)


def _bicycle(tilt: int, crank: int, pivot: Point):
    """The frame, the cranks and the pedals, from ``pivot`` (a point of it),
    tilted ``tilt`` degrees and its cranks turned ``crank``."""

    def at(p: Point) -> Point:
        q = turned((p[0] - pivot[0], p[1] - pivot[1]), float(tilt))
        return K.at(q[0], q[1])

    c = math.radians(crank)
    near_pedal = (BRACKET[0] + CRANK * math.cos(c), BRACKET[1] + CRANK * math.sin(c))
    far_pedal = (BRACKET[0] - CRANK * math.cos(c), BRACKET[1] - CRANK * math.sin(c))
    seat_top, head_top, head_low = (-15.0, -60.0), (25.0, -70.0), (28.5, -57.0)
    tubes = [
        ([BRACKET, REAR], 2.8, BIKE_DARK),
        ([seat_top, REAR], 2.6, BIKE_DARK),
        ([BRACKET, (-15.6, -63.0)], 3.4, BIKE),
        ([seat_top, (25.6, -67.0)], 3.4, BIKE),
        ([BRACKET, (27.6, -60.0)], 3.6, BIKE),
        ([head_low, (33.5, -43.0), FRONT], 3.0, BIKE),
        ([head_top, head_low], 4.6, BIKE),
    ]
    metal = [
        ([(-15.6, -63.0), (-16.0, -67.0)], 2.2, METAL),
        ([head_top, (24.2, -82.0)], 2.6, METAL),
        ([(21.0, -83.4), (30.0, -85.6)], 3.2, INK),
    ]
    saddle = [(-26.0, -70.0), (-8.0, -71.4), (-4.6, -69.0), (-11.0, -66.6), (-25.0, -66.0)]

    def pedal(p: Point) -> List[Point]:
        return [at((p[0] - 4.6, p[1])), at((p[0] + 4.6, p[1]))]

    def paint(d) -> None:
        # The far crank and its pedal are behind the frame.
        K.stroke(d, [at(BRACKET), at(far_pedal)], OUTLINE, 4.6)
        K.stroke(d, pedal(far_pedal), OUTLINE, 5.2)
        K.stroke(d, [at(BRACKET), at(far_pedal)], mix(METAL, OUTLINE, 0.35), 2.2)
        K.stroke(d, pedal(far_pedal), mix(METAL, OUTLINE, 0.5), 2.8)
        for pts, width, _colour in tubes + metal:
            K.stroke(d, [at(p) for p in pts], OUTLINE, width + 2.4)
        K.poly(d, [at(p) for p in saddle], OUTLINE, OUTLINE, 2.4)
        for pts, width, colour in tubes + metal:
            K.stroke(d, [at(p) for p in pts], colour, width)
        # A light along the top of the two long tubes.
        K.line(d, [at((-13.0, -61.2)), at((23.0, -68.0))], BIKE_LIGHT, 0.9)
        K.line(d, [at((0.0, -30.6)), at((25.0, -59.6))], BIKE_LIGHT, 0.9)
        K.poly(d, [at(p) for p in saddle], SADDLE_BROWN)
        K.line(d, [at((-23.0, -68.8)), at((-9.0, -70.0))], mix(SADDLE_BROWN, WHITE, 0.3), 0.9)
        # The bell, and the hubs' nuts.
        K.oval(d, at((22.4, -87.2)), 3.0, 3.0, BELL, OUTLINE, 1.0)
        K.oval(d, at((21.6, -88.0)), 0.9, 0.9, WHITE)
        for hub in (REAR, FRONT):
            K.oval(d, at(hub), 2.2, 2.2, METAL_LIGHT, OUTLINE, 0.9)
        # The chainring, the near crank and its pedal are in front of it.
        K.oval(d, at(BRACKET), 6.4, 6.4, METAL, OUTLINE, 1.1)
        K.oval(d, at(BRACKET), 3.4, 3.4, mix(METAL, OUTLINE, 0.5))
        K.stroke(d, [at(BRACKET), at(near_pedal)], OUTLINE, 4.8)
        K.stroke(d, pedal(near_pedal), OUTLINE, 5.4)
        K.stroke(d, [at(BRACKET), at(near_pedal)], METAL_LIGHT, 2.4)
        K.stroke(d, pedal(near_pedal), INK, 3.0)
        K.oval(d, at(BRACKET), 1.6, 1.6, METAL_LIGHT)

    return K.aligned(("bicycle", tilt, crank % 360, pivot), paint)


# ---- The bird's pieces -------------------------------------------------------


def _bone(tag: str, length: float, w0: float, w1: float, colour: RGBA, edge: bool):
    """A bone along +x from ``home``. ``edge``: with its outline (a limb is
    placed twice, every bone's outline and then every bone, so a joint has no
    line through it)."""

    def shape(d) -> None:
        K.poly(d, [K.at(0.0, -w0 / 2.0), K.at(length, -w1 / 2.0), K.at(length, w1 / 2.0), K.at(0.0, w0 / 2.0)], WHITE)
        K.oval(d, K.home, w0 / 2.0, w0 / 2.0, WHITE)
        K.oval(d, K.at(length, 0.0), w1 / 2.0, w1 / 2.0, WHITE)

    return K.solid(("bone", tag, length, w0, w1, colour, edge), shape, colour, None, outline=1.2 if edge else 0.0, rim=0.0, shade=0.0)


def _body():
    """His body from his seat, his back straight up: the strap of his bag
    goes across it."""

    def shape(d) -> None:
        K.oval(d, K.at(5.0, -24.0), 20.0, 25.0, WHITE)
        K.oval(d, K.at(11.0, -30.0), 14.0, 16.0, WHITE)
        K.oval(d, K.at(-4.0, -12.0), 15.0, 13.0, WHITE)

    def detail(d) -> None:
        K.oval(d, K.at(-8.0, -14.0), 20.0, 26.0, mix(FEATHER, FEATHER_SHADE, 0.55))
        K.oval(d, K.at(9.0, -27.0), 17.0, 22.0, FEATHER)
        for y in (-30.0, -22.0, -14.0):
            K.line(d, [K.at(14.0, y), K.at(17.0, y + 2.4), K.at(20.0, y)], FEATHER_SHADE, 0.8)
        strap = [K.at(19.0, -47.0), K.at(8.0, -32.0), K.at(-10.0, -15.0)]
        K.line(d, strap, OUTLINE, 5.4)
        K.line(d, strap, BAG_DARK, 3.2)
        K.line(d, [(x - 0.6, y - 0.6) for x, y in strap], BAG, 0.9)

    return K.solid(("body",), shape, FEATHER, detail, outline=1.3, rim=0.3, shade=0.4, shade_colour=FEATHER_DARK)


def _tail():
    """His tail, from where it leaves his body: three feathers, back and down."""

    feathers = ((146.0, 19.0), (170.0, 23.0), (196.0, 18.0))

    def feather(a: float, reach: float, half: float) -> List[Point]:
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        return [K.at(4.0 * s, -4.0 * c), K.at(reach * 0.6 * c + half * s, reach * 0.6 * s - half * c), K.at(reach * c, reach * s),
                K.at(reach * 0.6 * c - half * s, reach * 0.6 * s + half * c), K.at(-4.0 * s, 4.0 * c)]

    def shape(d) -> None:
        for a, reach in feathers:
            K.poly(d, feather(a, reach, 4.4), WHITE)
        K.oval(d, K.home, 5.0, 5.0, WHITE)

    def detail(d) -> None:
        for a, reach in feathers:
            c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
            K.line(d, [K.at(3.0 * c, 3.0 * s), K.at((reach - 3.0) * c, (reach - 3.0) * s)], FEATHER_SHADE, 0.9)

    return K.solid(("tail",), shape, FEATHER, detail, outline=1.2, rim=0.2, shade=0.3, shade_colour=FEATHER_DARK)


def _bag():
    """His satchel, from where it hangs on its strap: a ``W`` on its flap."""
    h = K.home

    def shape(d) -> None:
        K.rrect(d, h[0] - 10.0, h[1] - 1.0, h[0] + 10.0, h[1] + 18.0, 3.0, WHITE)

    def detail(d) -> None:
        K.rrect(d, h[0] - 12.0, h[1] + 9.0, h[0] + 12.0, h[1] + 20.0, 0.0, BAG_DARK)
        K.poly(d, [K.at(-12.0, -3.0), K.at(12.0, -3.0), K.at(10.0, 9.0), K.at(0.0, 12.5), K.at(-10.0, 9.0)], BAG_FLAP, OUTLINE, 0.9)
        K.stroke(d, [K.at(-5.4, 1.4), K.at(-2.8, 8.0), K.at(0.0, 3.6), K.at(2.8, 8.0), K.at(5.4, 1.4)], LETTER, 1.7)
        K.oval(d, K.at(0.0, 14.6), 1.5, 1.5, BELL, OUTLINE, 0.5)

    return K.solid(("bag",), shape, BAG, detail, outline=1.3, rim=0.3, shade=0.4, shade_colour=BAG_DARK)


def _foot(near: bool):
    """A webbed foot from its ankle; its sole is ``ANKLE_UP`` under it."""

    def shape(d) -> None:
        K.poly(d, [K.at(-3.4, -1.6), K.at(3.0, -2.2), K.at(11.6, ANKLE_UP), K.at(-3.4, ANKLE_UP)], WHITE)
        K.oval(d, K.home, 2.6, 2.6, WHITE)

    def detail(d) -> None:
        for x in (2.0, 6.0):
            K.line(d, [K.at(x - 2.0, -1.0), K.at(x + 2.6, ANKLE_UP)], LEG_DARK, 0.7)

    return K.solid(("foot", near), shape, LEG if near else LEG_DARK, detail, outline=1.2, rim=0.25, shade=0.3, shade_colour=LEG_DARK)


def _wing_tip(near: bool):
    """The end of a wing that holds a grip, along +x from its wrist: three
    dark feathers around the bar."""
    colour = FEATHER if near else FEATHER_SHADE

    def shape(d) -> None:
        K.oval(d, K.at(3.0, 0.0), 4.6, 3.8, WHITE)
        for dy in (-2.4, 0.0, 2.4):
            K.stroke(d, [K.at(4.0, dy), K.at(8.6, dy * 1.3)], WHITE, 2.4)

    def detail(d) -> None:
        K.rrect(d, K.home[0] + 5.0, K.home[1] - 8.0, K.home[0] + 14.0, K.home[1] + 8.0, 0.0, PRIMARY)

    return K.solid(("wing_tip", near), shape, colour, detail, outline=1.2, rim=0.2, shade=0.3, shade_colour=FEATHER_DARK)


def _wing_spread(near: bool):
    """A wing held out, from its shoulder, pointing up: its leading edge is to
    the front, its long dark feathers to the back."""
    colour = FEATHER if near else FEATHER_SHADE
    edge = [K.at(-5.0, 2.0), K.at(-6.0, -20.0), K.at(-1.0, -46.0), K.at(4.0, -52.0), K.at(9.0, -46.0), K.at(8.0, -39.0), K.at(13.0, -35.0),
            K.at(10.0, -29.0), K.at(15.0, -24.0), K.at(11.0, -18.0), K.at(15.0, -11.0), K.at(9.0, -6.0), K.at(8.0, 3.0)]

    def shape(d) -> None:
        K.poly(d, edge, WHITE)
        K.oval(d, K.home, 6.4, 6.0, WHITE)

    def detail(d) -> None:
        # The long feathers: dark from the middle of the wing to its tip.
        K.poly(d, [K.at(1.0, -60.0), K.at(20.0, -60.0), K.at(20.0, -8.0), K.at(8.0, -8.0), K.at(4.0, -30.0)], PRIMARY)
        K.poly(d, [K.at(-8.0, -30.0), K.at(4.0, -30.0), K.at(1.0, -60.0), K.at(-8.0, -60.0)], mix(colour, FEATHER_DARK, 0.25))
        for y in (-36.0, -26.0, -16.0):
            K.line(d, [K.at(4.0, y - 4.0), K.at(12.0, y + 3.0)], mix(PRIMARY, WHITE, 0.25), 0.8)
        K.line(d, [K.at(-3.0, -4.0), K.at(-3.6, -22.0), K.at(0.0, -44.0)], FEATHER_SHADE, 0.9)

    return K.solid(("wing_spread", near), shape, colour, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=FEATHER_DARK)


def _wing_fold():
    """A wing at his side, from its shoulder."""

    def shape(d) -> None:
        K.poly(d, [K.at(4.0, -5.0), K.at(-8.0, 0.0), K.at(-22.0, 14.0), K.at(-31.0, 27.0), K.at(-18.0, 23.0), K.at(-5.0, 13.0), K.at(6.0, 4.0)], WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(-36.0, 34.0), K.at(-24.0, 12.0), K.at(-13.0, 30.0)], PRIMARY)
        K.line(d, [K.at(0.0, 2.0), K.at(-12.0, 11.0), K.at(-21.0, 21.0)], FEATHER_SHADE, 0.9)

    return K.solid(("wing_fold",), shape, FEATHER, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=FEATHER_DARK)


def _head():
    """His head, from its middle: a crest at the back of it."""

    def shape(d) -> None:
        K.oval(d, K.home, 11.5, 11.0, WHITE)
        for a, reach in ((186.0, 19.0), (204.0, 21.0), (224.0, 17.0)):
            c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
            K.poly(d, [K.at(8.0 * c + 2.6 * s, 8.0 * s - 2.6 * c), K.at(reach * c, reach * s), K.at(8.0 * c - 2.6 * s, 8.0 * s + 2.6 * c)], WHITE)

    def detail(d) -> None:
        K.oval(d, K.at(-5.0, 4.0), 9.0, 8.0, mix(FEATHER, FEATHER_SHADE, 0.6))
        K.oval(d, K.at(6.6, 4.8), 2.6, 1.6, (255, 150, 130, 110))

    return K.solid(("head",), shape, FEATHER, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=FEATHER_DARK)


EYE: Point = (3.6, -2.4)


def _eyes(mode: str):
    """His eye, and his round glasses."""
    c = K.at(*EYE)

    def paint(d) -> None:
        K.oval(d, c, 5.6, 5.6, LENS)
        if mode == "closed":
            K.line(d, [(c[0] - 2.6, c[1] - 0.2), (c[0], c[1] + 1.4), (c[0] + 2.6, c[1] - 0.2)], INK, 1.2)
        elif mode == "happy":
            K.line(d, [(c[0] - 2.6, c[1] + 1.0), (c[0], c[1] - 1.5), (c[0] + 2.6, c[1] + 1.0)], INK, 1.3)
        elif mode == "wince":
            K.line(d, [(c[0] - 2.4, c[1] - 2.0), (c[0] + 1.6, c[1]), (c[0] - 2.4, c[1] + 2.0)], INK, 1.2)
        else:
            r = 3.4 if mode == "wide" else 2.9
            K.oval(d, c, r, r, WHITE, INK, 0.6)
            K.oval(d, (c[0] + 0.5, c[1] + 0.2), 1.9 if mode == "wide" else 2.1, 1.9 if mode == "wide" else 2.1, INK)
            K.oval(d, (c[0] - 0.3, c[1] - 0.8), 0.75, 0.75, WHITE)
        K.oval(d, c, 5.8, 5.8, None, GLASSES, 1.7)  # type: ignore[arg-type]
        K.line(d, [(c[0] - 5.4, c[1] - 0.6), (c[0] - 13.0, c[1] + 0.6)], GLASSES, 1.5)

    return K.piece(("eyes", mode), paint)


#: Where his bill meets his head, from the middle of his head.
BILL_ROOT: Point = (8.0, 2.6)


def _bill_upper():
    def shape(d) -> None:
        K.poly(d, [K.at(-3.0, -5.6), K.at(14.0, -4.6), K.at(30.0, -1.6), K.at(40.5, 2.4), K.at(41.6, 7.2), K.at(38.0, 5.4), K.at(20.0, 3.6),
                   K.at(-3.0, 2.8)], WHITE)

    def detail(d) -> None:
        K.line(d, [K.at(-2.0, -1.0), K.at(20.0, 0.4), K.at(38.0, 3.6)], BILL_DARK, 0.9)
        K.poly(d, [K.at(36.0, 1.0), K.at(43.0, 2.0), K.at(43.0, 9.0), K.at(37.0, 6.0)], BILL_DARK)
        K.oval(d, K.at(6.0, -2.0), 1.1, 0.7, BILL_DARK)

    return K.solid(("bill_upper",), shape, BILL, detail, outline=1.3, rim=0.35, shade=0.3, shade_colour=BILL_DARK)


def _bill_lower():
    """His lower bill and its pouch, from the hinge."""

    def shape(d) -> None:
        K.poly(d, [K.at(-3.0, -0.6), K.at(37.0, 2.4), K.at(34.0, 5.6), K.at(25.0, 11.4), K.at(13.0, 14.4), K.at(4.0, 11.6), K.at(-3.0, 5.0)], WHITE)

    def detail(d) -> None:
        K.line(d, [K.at(-3.0, 0.2), K.at(18.0, 1.8), K.at(37.0, 3.2)], BILL_DARK, 1.6)
        for x in (7.0, 15.0, 23.0):
            K.line(d, [K.at(x, 3.0), K.at(x + 1.6, 11.0)], POUCH_DARK, 0.7)

    return K.solid(("bill_lower",), shape, POUCH, detail, outline=1.3, rim=0.3, shade=0.4, shade_colour=POUCH_DARK)


# ---- The frame ---------------------------------------------------------------


def _bike_of(pose: Pose) -> Tuple[Callable[[Point], Point], Point, int, int]:
    """Where a point of the bicycle is in the frame, with where its pivot is
    pinned, its tilt and its crank turn: the ones it is painted with."""
    bx, by = pose["bike"]  # type: ignore[misc]
    pivot: Point = pose["pivot"]  # type: ignore[assignment]
    tilt = int(round(float(pose["tilt"])))  # type: ignore[arg-type]
    crank = int(round(float(pose["crank"]))) % 360  # type: ignore[arg-type]
    held = pin((CX + bx + pivot[0], GROUND + by + pivot[1]))

    def at(p: Point) -> Point:
        q = turned((p[0] - pivot[0], p[1] - pivot[1]), float(tilt))
        return (held[0] + q[0], held[1] + q[1])

    return at, held, tilt, crank


def pedal_points(pose: Pose) -> Tuple[Point, Point]:
    """The near and the far pedal of the bicycle of ``pose``, in the frame."""
    at, _held, _tilt, crank = _bike_of(pose)
    c = math.radians(crank)
    return (at((BRACKET[0] + CRANK * math.cos(c), BRACKET[1] + CRANK * math.sin(c))),
            at((BRACKET[0] - CRANK * math.cos(c), BRACKET[1] - CRANK * math.sin(c))))


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = ROW_POSES[anim](frame_idx, nframes)
    img = K.new_frame()
    bike, held, tilt, crank = _bike_of(pose)
    pivot: Point = tuple(round(v, 2) for v in pose["pivot"])  # type: ignore[assignment]
    free = float(pose["free"])  # type: ignore[arg-type]

    # His seat, and how he is turned: with the bicycle, unless he is off it.
    sx, sy = pose["seat"]  # type: ignore[misc]
    on = bike((SADDLE[0] + sx, SADDLE[1] + sy))
    ax, ay = pose["at"]  # type: ignore[misc]
    seat = (lerp(on[0], CX + ax, free), lerp(on[1], GROUND + ay, free))
    lean = float(pose["lean"]) + tilt * (1.0 - free)  # type: ignore[arg-type]

    def bird(p: Point) -> Point:
        """A point of him (from his seat, his back straight up) in the frame."""
        q = turned(p, lean)
        return (seat[0] + q[0], seat[1] + q[1])

    def limb(name: str, bones: List[Tuple[Point, Point, Callable]]) -> None:
        for edge in (True, False):
            for k, (a, b, bone) in enumerate(bones):
                K.place(img, bone(edge), a, f"{name}_{k}{'_edge' if edge else ''}", angle(a, b))

    wings, flap = str(pose["wings"]), float(pose["flap"])  # type: ignore[arg-type]

    def wing(near: bool) -> None:
        name = "near" if near else "far"
        shoulder = bird(NEAR_SHOULDER if near else FAR_SHOULDER)
        colour = FEATHER if near else FEATHER_SHADE
        if wings == "spread":
            K.place(img, _wing_spread(near), shoulder, f"{name}_wing", lean * 0.4 + flap + (0.0 if near else 14.0))
        elif wings == "fold":
            if near:
                K.place(img, _wing_fold(), shoulder, f"{name}_wing", lean)
        else:
            grip = bike(GRIP if near else (GRIP[0] + 1.6, GRIP[1] - 1.2))
            elbow, wrist = solve(shoulder, grip, WING_UPPER, WING_FORE, 1.0)
            limb(f"{name}_wing", [
                (shoulder, elbow, lambda edge: _bone("wing_upper", WING_UPPER, 10.0, 8.0, colour, edge)),
                (elbow, wrist, lambda edge: _bone("wing_fore", WING_FORE, 8.0, 6.4, colour, edge)),
            ])
            K.place(img, _wing_tip(near), wrist, f"{name}_wing_tip", angle(elbow, wrist))

    feet = str(pose["feet"])
    near_pedal, far_pedal = pedal_points(pose)

    def leg(near: bool) -> None:
        name = "near" if near else "far"
        hip = bird(NEAR_HIP if near else FAR_HIP)
        if feet == "pedal":
            p = near_pedal if near else far_pedal
            sole, turn = (p[0] - 2.0, p[1] - 1.4), float(tilt)
        elif feet == "tube":
            sole, turn = bike(TUBE_BACK if near else TUBE_FRONT), 30.0 + tilt
        else:
            x, y = pose["nf" if near else "ff"]  # type: ignore[misc]
            sole, turn = (CX + x, GROUND + y), -20.0 * free * (1.0 if y > -8.0 else 0.0)
        knee, ankle = solve(hip, (sole[0], sole[1] - ANKLE_UP), THIGH, SHIN, -1.0)
        colour = LEG if near else LEG_DARK
        limb(f"{name}_leg", [
            (hip, knee, lambda edge: _bone("thigh", THIGH, 5.0, 4.4, colour, edge)),
            (knee, ankle, lambda edge: _bone("shin", SHIN, 4.4, 3.8, colour, edge)),
        ])
        K.place(img, _foot(near), ankle, f"{name}_foot", turn)

    wing(False)
    leg(False)
    for name, hub in (("rear", REAR), ("front", FRONT)):
        K.place(img, _wheel(int(round(float(pose["wheel"])))), pin(bike(hub)), f"{name}_wheel")  # type: ignore[arg-type]
    K.place(img, _bicycle(tilt, crank, pivot), held, "bicycle")

    K.place(img, _tail(), bird((-15.0, -9.0)), "tail", lean)
    K.place(img, _body(), seat, "body", lean)
    K.place(img, _bag(), bird(BAG_HANGS), "bag", lean * 0.25 + float(pose["bag"]))  # type: ignore[arg-type]
    leg(True)

    root = bird(NECK_ROOT)
    hx, hy = pose["head"]  # type: ignore[misc]
    bend, head = solve(root, (root[0] + hx, root[1] + hy), NECK_LOW, NECK_HIGH, -1.0)
    limb("neck", [
        (root, bend, lambda edge: _bone("neck_low", NECK_LOW, 11.0, 9.0, FEATHER, edge)),
        (bend, head, lambda edge: _bone("neck_high", NECK_HIGH, 9.0, 8.0, FEATHER, edge)),
    ])
    turn = lean * 0.2 + float(pose["tilt_head"])  # type: ignore[arg-type]
    hinge_off = turned(BILL_ROOT, turn)
    hinge = (head[0] + hinge_off[0], head[1] + hinge_off[1])
    K.place(img, _bill_lower(), hinge, "bill_lower", turn + 12.0 + float(pose["gape"]))  # type: ignore[arg-type]
    K.place(img, _head(), head, "head", turn)
    K.place(img, _eyes(str(pose["eyes"])), head, "eyes", turn)
    K.place(img, _bill_upper(), hinge, "bill_upper", turn + 12.0)
    wing(True)
    return K.downsample(img)


#: The body the game moves: both wheels and the bird on them, riding.
BODY_BOX = (CX - 62.0, GROUND - 142.0, CX + 62.0, GROUND)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return K.render(TARGET_NAME, ROWS, _render_frame, out_dir, ACTOR_METADATA, BODY_BOX)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Willson spritesheet.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
