"""SVG-rigged sprite target for the burning flying shark, the pirates' sky-mount.

A great white shark on fire: pale grey over white, with the black eye of its
kind (Jon, 2026-10-13: "make the burning flying shark look less like an
orca"; it was dark over pale, as an orca is). Its skin has glowing cracks, the
trailing edges of its fins smoulder, its eye rolls back under its membrane
when it bites, and it BURNS: fire stands along the whole of its back, streams
from its fins and its tail, and small flames come away behind it. It is tacked up for a rider: a red saddle
blanket with a skull and crossbones, a leather saddle, a girth with a brass
buckle, a stirrup and reins to a bit in its jaw.

The SVG ``data/characters/burning_flying_shark/burning_flying_shark.svg`` owns
the art and marks every joint (its hidden ``Rig Joints`` layer). The rig
document ``rigged/burning_flying_shark/burning_flying_shark_side.rig.json``
owns the skeleton and the clips; ``scripts/build_burning_flying_shark_rig.py``
derives it from the SVG (through ``rigbuild.creature_rig`` with the ``fish``
anatomy) and authors the clips. Each clip also keys the eye state (``eye.*``)
and the strength of each effect (``fx.*``). This module owns only the effects
(the fire above all) and publication.

Rows, frame counts, durations, animation bindings and events are the sheet
contract the game already reads; they are unchanged by the SVG redesign.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet
from . import _creature_fx as FX
from ._svg_fighter_effects import FxCanvas, compose_rig_frame

Point = Tuple[float, float]

TARGET_NAME = "burning_flying_shark"
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "burning_flying_shark_side.rig.json"
FRAME_SIZE = (223, 130)
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``): the art is
#: drawn at 620x360 units and published at the size the shark always had.
ART_SCALE = 0.36


def _px(x: float, y: float) -> Dict[str, float]:
    """A point of the drawing (SVG units) as a sprite-frame point."""
    return {"x": round(x * ART_SCALE, 1), "y": round(y * ART_SCALE, 1)}


ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_burning_flying_shark",
        "display_name": "Burning Flying Shark",
    },
    "body": {
        "body_plan": "Flyer",
        "body_kind": "Floating",
        "mass_class": "Heavy",
        "locomotion_hint": "Fly",
        "traits": ["enemy", "pirate", "aerial", "mount", "beast", "no_hands", "fire", "svg_rigged"],
    },
    "capabilities": {
        "traversal": {
            "walk": False,
            "jump": None,
            "climb": None,
            "fly": True,
            "swim": None,
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {
            "talk": None,
            "trade": None,
            "carry": None,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "wanderer_puppy_slug"},
    "actions": {"default_preset": "peaceful_float"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.fly": {"animation": "fly", "events": []},
        "action.melee.primary": {
            "animation": "chomp",
            "events": [
                {"t": 0.24, "event": "telegraph_peak", "source": "burning_flying_shark"},
                {"t": 0.36, "event": "hitbox_active_start", "source": "burning_flying_shark"},
                {"t": 0.64, "event": "hitbox_active_end", "source": "burning_flying_shark"},
            ],
        },
        "action.special.dive": {
            "animation": "dive",
            "events": [
                {"t": 0.40, "event": "dive_commit", "source": "burning_flying_shark"},
            ],
        },
    },
    # Points on the drawn frame (before the sheet's auto-crop), at rest.
    "sockets": {
        "mouth": {"source": "burning_flying_shark.geometry", "point": _px(530.0, 225.0)},
        "head": {"source": "burning_flying_shark.geometry", "point": _px(490.0, 200.0)},
        "tail": {"source": "burning_flying_shark.geometry", "point": _px(130.0, 210.0)},
        "saddle": {"source": "burning_flying_shark.geometry", "point": _px(396.0, 152.0)},
        "ember_origin": {"source": "burning_flying_shark.geometry", "point": _px(350.0, 130.0)},
    },
    "visual": {
        "default_pose": "idle",
        "canonical_source": "ambition_sprite2d_renderer/data/characters/burning_flying_shark/burning_flying_shark.svg",
        "portrait": {
            "face_guide": {
                "center": _px(488.0, 206.0),
                "size": {"width": round(110.0 * ART_SCALE, 1), "height": round(80.0 * ART_SCALE, 1)},
                "source_size": {"width": FRAME_SIZE[0], "height": FRAME_SIZE[1]},
            }
        },
    },
    "tags": ["pirate", "aerial", "enemy", "beast", "fire", "svg_rigged"],
    "authoring_description": (
        "A flying, burning great shark kept as a pirate crew's sky-mount: a genre mash-up, not a "
        "parody of a person. The body follows a great white's side profile (conical snout, gill "
        "slits, a tall first dorsal, crescent tail, pectoral fins) with the pectorals beating "
        "like wings, the nictitating membrane it closes as it bites, and the fire, magma cracks "
        "and tack (saddle, girth, stirrup, reins and a skull-and-crossbones blanket) invented "
        "for the pirate setting."
    ),
}


def _doc() -> RigDocument:
    return FX.rig_document(RIG_PATH)


#: The sheet's rows are the rig's clips, in the rig's order (the game reads
#: them by name).
ROWS: List[Tuple[str, int, int]] = _doc().rows()

# --- Effect glyphs (`_creature_fx`), in SVG units like the art ----------------
#
# THE FIRE IS ONE BODY OF FLAME, NOT A PIECE PLACED MANY TIMES (Jon,
# 2026-10-13, of fire made of one small tongue at eight places: "too same-y
# ... We shouldn't just slapdash the same small fire piece around. It looks
# tiled").
#
# A MANE is a whole stretch of fire drawn as one picture: many tongues of
# different heights, widths and leans, close enough that their roots are one
# mass, with small flames between the large ones. No two tongues of a mane
# are the same, and each has its own beat, so a mane is not the same shape at
# two places or at two times. The shark has four manes: behind its body,
# behind each half of its tail, and a low one on its flank over a line of
# soot. Each is drawn at twelve moments of its loop.
#
# The fins and the tail keep single tongues off their trailing edges, in
# three sizes, and small flames come away from the back and go out.

FLAME_LAYERS = (
    ((214, 52, 18, 215), 1.0, 1.0),
    ((255, 128, 30, 235), 0.76, 0.78),
    ((255, 208, 84, 245), 0.52, 0.56),
    ((255, 248, 214, 255), 0.27, 0.32),
)

#: The six shapes of a single tongue: (how far the tip leans, how often the
#: centre line bends, where in the bend it starts, its length, the side the
#: fork is on).
FLAME_SHAPES = (
    (0.34, 1.0, 0.0, 1.00, 1.0),
    (-0.30, 1.2, 0.8, 0.88, -1.0),
    (0.46, 1.5, 1.9, 1.10, -1.0),
    (-0.40, 0.9, 2.7, 0.80, 1.0),
    (0.24, 1.8, 3.6, 1.05, 1.0),
    (-0.50, 1.3, 4.4, 0.94, -1.0),
)


def _tongue(length: float, width: float, lean: float, bends: float, start: float) -> List[Point]:
    """The outline of one tongue of flame along +x: round at the root, a point at the tip."""
    upper, lower = [], []
    count = 13
    for i in range(count):
        s = i / (count - 1)
        centre = lean * width * s * math.sin(math.pi * bends * s + start)
        half = 0.5 * width * min(1.0, (s + 0.10) / 0.24) * (1.0 - s) ** 0.72
        x = (s - 0.12) * length
        upper.append((x, centre - half))
        lower.append((x, centre + half))
    return upper + lower[::-1]


def _flame(length: float, width: float, shape: int, fork: bool = True):
    lean, bends, start, lick, side = FLAME_SHAPES[shape]

    def paint(c: FxCanvas) -> None:
        for color, k_len, k_wide in FLAME_LAYERS:
            if fork:
                # The fork: a small tongue to one side of the root.
                turn = math.radians(side * 26.0)
                small = _tongue(length * 0.52 * k_len, width * 0.62 * k_wide, -lean, bends, start + 1.3)
                c.polygon([(0.16 * length + x * math.cos(turn) - y * math.sin(turn),
                            x * math.sin(turn) + y * math.cos(turn)) for x, y in small], color)
            c.polygon(_tongue(length * lick * k_len, width * k_wide, lean, bends, start), color)

    return paint


def _flame_extent(length: float, width: float) -> FX.Extent:
    reach = max(0.95 * width, 0.36 * length)
    return (0.2 * length, reach, 1.2 * length, reach)


# A mane is drawn in a frame of its own: +x runs along the back toward the
# tail, and +y is the height of the fire. It is placed turned half round, so
# +x is toward the tail on the screen and +y is up.

#: How many moments of its loop a mane is drawn at.
MANE_MOMENTS = 12


def _mane_tongues(seed: int, length: float, tall: Tuple[float, float], count: int, lean: Tuple[float, float],
                  crest: float) -> List[Tuple[float, ...]]:
    """The tongues of a mane: ``(x, height, width, lean, beats, phase, wiggle)``.

    ``count`` large tongues at places that are not even, each of a height of
    its own between ``tall`` (and higher toward ``crest``, a place along the
    mane from 0 to 1), and a small flame at each few units between them.
    """
    rng = random.Random(seed)
    out: List[Tuple[float, ...]] = []
    x = rng.uniform(4.0, 14.0)
    step = (length - 16.0) / count
    for _ in range(count):
        place = x / length
        swell = 0.55 + 0.45 * math.cos(math.pi * (place - crest)) ** 2
        height = rng.uniform(*tall) * swell
        out.append((x, height, rng.uniform(0.30, 0.46) * height + 9.0, rng.uniform(*lean), float(rng.choice((1, 1, 2, 3))),
                    rng.uniform(0.0, math.tau), rng.uniform(0.15, 0.45)))
        x += step * rng.uniform(0.55, 1.45)
    x = 0.0
    while x < length:
        out.append((x, rng.uniform(0.12, 0.30) * tall[1], rng.uniform(9.0, 16.0), rng.uniform(*lean),
                    float(rng.choice((1, 2, 2, 3))), rng.uniform(0.0, math.tau), rng.uniform(0.2, 0.6)))
        x += rng.uniform(6.0, 13.0)
    return out


def _mane_tongue(x: float, root: float, height: float, width: float, lean: float, wiggle: float, start: float) -> List[Point]:
    """One tongue of a mane: it stands at ``(x, root)`` and leans toward +x."""
    left, right = [], []
    count = 12
    for i in range(count):
        s = i / (count - 1)
        cx = x + lean * height * s ** 1.4 + wiggle * width * s * math.sin(math.pi * 1.3 * s + start)
        half = 0.5 * width * min(1.0, (s + 0.08) / 0.2) * (1.0 - s) ** 0.7
        left.append((cx - half, root + s * height))
        right.append((cx + half, root + s * height))
    return left + right[::-1]


def _mane(length: float, tongues, moment: int, lift, over: bool = False):
    """A mane at one moment of its loop.

    ``lift(x)`` is how high the skin is over the straight line between the
    two ends of the mane, at ``x`` along it: the back of the shark is a curve,
    and each tongue stands on the skin, not on the straight line. A mane that
    is BEHIND the body has a mass of root that goes down behind it; a mane
    that is OVER the body has no such mass, and has the burn it makes on the
    skin under it.
    """
    at = moment / MANE_MOMENTS
    xs = [float(x) for x in range(-6, int(length) + 7, 6)]

    def paint(c: FxCanvas) -> None:
        if over:
            c.polygon([(x, lift(x) - 11.0 - 3.0 * math.sin(0.09 * x + 1.0)) for x in xs]
                      + [(x, lift(x) + 4.0) for x in reversed(xs)], (92, 60, 40, 150))
            c.polygon([(x, lift(x) - 6.0 - 2.0 * math.sin(0.11 * x)) for x in xs[1:-1]]
                      + [(x, lift(x) + 3.0) for x in reversed(xs[1:-1])], (44, 32, 30, 185))
        for layer, (color, k_len, k_wide) in enumerate(FLAME_LAYERS):
            # The roots are one mass along the skin. Over the body it is in
            # the two outer colours only: a pale band of it is a stripe on
            # the shark, not fire.
            if not over or layer < 2:
                under = -3.0 if over else -14.0
                top = (4.0 if over else 6.0) * k_wide
                c.polygon([(x, lift(x) + under) for x in xs] + [(x, lift(x) + top) for x in reversed(xs)], color)
            for x, height, width, lean, beats, phase, wiggle in tongues:
                beat = math.tau * beats * at + phase
                live = 0.62 + 0.38 * math.sin(beat)
                c.polygon(_mane_tongue(x, lift(x) - 2.0, height * live * k_len, width * (0.85 + 0.15 * live) * k_wide,
                                       lean + 0.16 * math.sin(beat + 1.1), wiggle, beat), color)

    return paint


def _mane_extent(length: float, tongues, lift) -> FX.Extent:
    high = max(height + lift(x) for x, height, *_rest in tongues)
    reach = max(x + (lean + 0.2) * height + width for x, height, width, lean, *_rest in tongues)
    return (10.0, 16.0, max(length + 8.0, reach) + 6.0, high + 8.0)


def _paint_ember(c: FxCanvas) -> None:
    c.ellipse((0, 0), 4.5, 4.5, (255, 140, 36, 150))
    c.ellipse((0, 0), 2.2, 2.2, (255, 236, 160, 255))


def _paint_speed(c: FxCanvas) -> None:
    for y, length in ((-34, 70), (0, 110), (30, 80)):
        c.line([(0, y), (length, y)], (255, 246, 214, 120), 3.0)


#: The sizes of a single tongue: name -> (length, width, it forks).
FLAME_SIZES = {
    "flame": (48.0, 26.0, True),
    "flame_big": (70.0, 32.0, True),
    "flame_small": (32.0, 19.0, True),
    "lick_a": (34.0, 20.0, False),      # a flame that has come away, and
    "lick_b": (22.0, 13.0, False),      # the same one as it goes out
    "lick_c": (13.0, 8.0, False),
}

#: The line of the back, nose to tail, in SVG units (the art script's ``TOP``).
_BACK = ((536, 218), (530, 206), (516, 194), (492, 183), (460, 174), (420, 167), (380, 163), (340, 164),
         (300, 172), (265, 184), (235, 196), (210, 204), (188, 208), (168, 210))


def _back_y(x: float) -> float:
    for (x0, y0), (x1, y1) in zip(_BACK, _BACK[1:]):
        if x1 <= x <= x0:
            return y0 + (y1 - y0) * (x0 - x) / (x0 - x1)
    return _BACK[0][1] if x > _BACK[0][0] else _BACK[-1][1]


#: The manes: name -> (the bone it is on, the x of its front end and of its
#: rear end on the back (SVG units), how far under the line of the back its
#: roots are, it is in front of the body, its tongues).
MANES = {
    # Behind the body: the tallest fire, highest over the shoulder.
    "mane_body": ("body", 484.0, 286.0, 6.0, False, _mane_tongues(11, 198.0, (66.0, 132.0), 10, (0.22, 0.55), 0.42)),
    # Behind the tail: lower, and it streams back.
    "mane_tail1": ("tail1", 300.0, 218.0, 6.0, False, _mane_tongues(23, 84.0, (40.0, 84.0), 5, (0.5, 0.95), 0.2)),
    "mane_tail2": ("tail2", 230.0, 172.0, 5.0, False, _mane_tongues(37, 60.0, (28.0, 60.0), 4, (0.7, 1.15), 0.2)),
    # On the flank: low fire over the burn it makes.
    "mane_flank": ("body", 466.0, 300.0, 24.0, True, _mane_tongues(53, 166.0, (34.0, 78.0), 9, (0.3, 0.75), 0.5)),
}

_GLYPHS: Dict[str, Tuple[FX.Extent, FX.Paint]] = {**FX.COMMON}
for _name, (_length, _width, _fork) in FLAME_SIZES.items():
    for _k in range(len(FLAME_SHAPES)):
        _GLYPHS[f"{_name}{_k}"] = (_flame_extent(_length, _width), _flame(_length, _width, _k, _fork))


def _mane_lift(front_x: float, rear_x: float):
    """How high the back is over the straight line between the ends of a
    mane, at ``x`` along the mane from its front end."""
    length = front_x - rear_x
    front_y, rear_y = _back_y(front_x), _back_y(rear_x)

    def lift(x: float) -> float:
        along = min(1.0, max(0.0, x / length))
        return (front_y + (rear_y - front_y) * along) - _back_y(front_x - along * length)

    return lift


for _name, (_bone, _front_x, _rear_x, _sink, _over, _tongues) in MANES.items():
    _lift = _mane_lift(_front_x, _rear_x)
    for _k in range(MANE_MOMENTS):
        _GLYPHS[f"{_name}{_k}"] = (
            _mane_extent(_front_x - _rear_x, _tongues, _lift),
            _mane(_front_x - _rear_x, _tongues, _k, _lift, over=_over),
        )
_GLYPHS["ember"] = ((6.0, 6.0, 6.0, 6.0), _paint_ember)
_GLYPHS["speed"] = ((4.0, 38.0, 114.0, 34.0), _paint_speed)
GLYPHS = FX.Glyphs(ART_SCALE, _GLYPHS)
_place = GLYPHS.place
_local = GLYPHS.local

REST = FX.rest_frames(_doc())

#: Where the fins burn: (bone, a drawn point on it in SVG units, the flame's
#: rest heading in degrees (y down; 180 streams straight back), its phase,
#: its size). Each is rooted a little inside its fin's trailing edge, so the
#: fin covers its root, and licks up and back the way fire rises off a moving
#: body. No two flames next to each other have one size.
FLAMES = (
    ("dorsal", (350.0, 116.0), 218.0, 0.0, "flame_big"),
    ("dorsal", (354.0, 140.0), 206.0, 1.7, "flame_small"),
    ("near_pec", (358.0, 294.0), 196.0, 0.9, "flame"),
    ("near_pec", (380.0, 268.0), 202.0, 2.6, "flame_small"),
    ("fluke", (130.0, 164.0), 210.0, 1.3, "flame_big"),
    ("fluke", (150.0, 206.0), 196.0, 2.2, "flame_small"),
    ("fluke", (136.0, 236.0), 188.0, 0.4, "flame"),
)
_ANCHORS = [FX.anchor(REST, bone, point, ART_SCALE) for bone, point, _deg, _phase, _size in FLAMES]

#: Each mane: (its bone, where its front end is on the bone, its heading).
_MANE_PLACES = {
    name: (
        bone,
        FX.anchor(REST, bone, (front_x, _back_y(front_x) + sink), ART_SCALE),
        math.degrees(math.atan2((_back_y(rear_x) + sink) - (_back_y(front_x) + sink), rear_x - front_x)),
    )
    for name, (bone, front_x, rear_x, sink, _over, _tongues) in MANES.items()
}
#: How many small flames are in the air at once, and how many embers.
LICKS, EMBERS = 5, 8


def _shape(t: float, index: int, rate: int) -> int:
    """The shape a place shows at ``t``: one after the other, ``rate`` times
    through the six in a row, from a start of its own."""
    return int((t * rate + index * 0.37) * len(FLAME_SHAPES)) % len(FLAME_SHAPES)


def _manes(canvas: FxCanvas, t: float, world, strength: float, over: bool) -> None:
    for index, (name, (_bone, _front, _rear, _sink, is_over, _tongues)) in enumerate(MANES.items()):
        if is_over != over:
            continue
        bone, local, heading = _MANE_PLACES[name]
        bw = world[bone]
        # Each mane is at a moment of its own, so they do not beat as one.
        moment = (int(round(t * MANE_MOMENTS)) + index * 5) % MANE_MOMENTS
        _place(canvas, f"{name}{moment}", bw.to_world(local), strength, degrees=heading + bw.angle - REST[bone][1])


def _behind(canvas: FxCanvas, t: float, world, params) -> None:
    flame = params.get("fx.flame", 0.0)
    flare = params.get("fx.flare", 0.0)
    if params.get("fx.speed", 0.0) > 0.02:
        body = world["body"]
        _place(canvas, "speed", _local(body, -130.0, -10.0), params["fx.speed"], degrees=body.angle + 180.0)
    if flame > 0.02:
        _manes(canvas, t, world, flame, over=False)
        for i, ((bone, _point, deg, phase, size), local) in enumerate(zip(FLAMES, _ANCHORS)):
            bw = world[bone]
            turn = bw.angle - REST[bone][1]
            sway = 8.0 * math.sin(math.tau * t * 2.0 + phase)
            name = "flame_big" if flare > 0.5 and size != "flame_small" else size
            opacity = flame * (0.84 + 0.16 * math.cos(math.tau * t * 3.0 + phase))
            _place(canvas, f"{name}{_shape(t, i, 1)}", bw.to_world(local), opacity, degrees=deg + turn + sway)
        # Embers come off the whole of the back and are left behind.
        body = world["body"]
        lean = math.radians(body.angle - REST["body"][1])
        base = body.to_world(_MANE_PLACES["mane_body"][1])
        for k in range(EMBERS):
            u = (t * 2.0 + k / EMBERS) % 1.0
            along = (30.0 + 36.0 * k) * ART_SCALE
            back, up = along + (30.0 + 190.0 * u) * ART_SCALE, (40.0 + 80.0 * u + 26.0 * math.sin(k * 2.1 + u * 6.0)) * ART_SCALE
            x = base[0] - back * math.cos(lean) + up * math.sin(lean)
            y = base[1] - back * math.sin(lean) - up * math.cos(lean)
            _place(canvas, "ember", (x, y), flame * (1.0 - u))


def _front(canvas: FxCanvas, t: float, world, params) -> None:
    flame = params.get("fx.flame", 0.0)
    if flame > 0.02:
        _manes(canvas, t, world, flame, over=True)
        # Small flames come away from the back, go up and back, and go out.
        body = world["body"]
        lean = math.radians(body.angle - REST["body"][1])
        base = body.to_world(_MANE_PLACES["mane_body"][1])
        for k in range(LICKS):
            u = (t + k / LICKS) % 1.0
            along = (20.0 + 47.0 * ((k * 3) % LICKS)) * ART_SCALE
            back, up = along + (30.0 + 130.0 * u) * ART_SCALE, (70.0 + 80.0 * u) * ART_SCALE
            x = base[0] - back * math.cos(lean) + up * math.sin(lean)
            y = base[1] - back * math.sin(lean) - up * math.cos(lean)
            size = "lick_a" if u < 0.4 else "lick_b" if u < 0.72 else "lick_c"
            _place(canvas, f"{size}{_shape(t, k, 2)}", (x, y), flame * (1.0 - u) ** 0.6,
                   degrees=232.0 + math.degrees(lean) + 16.0 * math.sin(math.tau * u + k))
    head = world["head"]
    _place(canvas, "bite", _local(head, 112.0, 14.0), params.get("fx.bite", 0.0), degrees=head.angle)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return compose_rig_frame(_doc(), animation, frame_idx, frame_count, behind=_behind, front=_front, fx_pieces=True)


FACE = FaceGuide(
    center_x=488.0 * ART_SCALE,
    center_y=206.0 * ART_SCALE,
    width=110.0 * ART_SCALE,
    height=80.0 * ART_SCALE,
    source_width=FRAME_SIZE[0],
    source_height=FRAME_SIZE[1],
)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    """Dialog portraits rerendered from the rig at 6x, never the sheet."""
    del opts
    doc = _doc()

    def portrait_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        source = doc.render_at(animation, doc.frame_time(animation, frame_idx, frame_count), supersample=3, scale=6)
        return render_framed_portrait(source, FACE, view_width=180.0 * ART_SCALE, center_y=206.0 * ART_SCALE)

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 0, 6)),
        "gaping": PortraitClip(
            tuple(portrait_frame("idle", frame, 6) for frame in (0, 1, 2, 3, 4, 5)),
            duration_ms=135,
            looping=True,
        ),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


#: The body of the shark on the drawn frame (before the sheet's crop), in
#: frame pixels: ``(x, y, width, height)``. AUTHORED, not measured from the
#: picture: the game makes the shark's size, its box and its saddle seat from
#: this, and the fire is not the shark. Measured, the box moved each time the
#: fire changed (and the frame's crop with it), and the rider's seat with it.
#: These are the numbers the sheet published before the fire of 2026-10-13.
BODY_BOX = (10, 29, 185, 81)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}

    def body_metrics(fw: int, fh: int) -> dict:
        # The sheet is cropped to what is drawn; the crop moves the box.
        x = BODY_BOX[0] + int(frame_transform.get("dx", 0))
        y = BODY_BOX[1] + int(frame_transform.get("dy", 0))
        if x < 0 or y < 0 or x + BODY_BOX[2] > fw or y + BODY_BOX[3] > fh:
            raise RuntimeError(f"the crop of the sheet ({fw}x{fh}, {frame_transform}) cuts the body of the shark")
        feet_x, feet_y = x + (BODY_BOX[2] - 1) / 2.0, float(y + BODY_BOX[3] - 1)
        return {
            "body_pixel_bbox": {"x": x, "y": y, "w": BODY_BOX[2], "h": BODY_BOX[3]},
            "feet_pixel": {"x": feet_x, "y": feet_y},
            "feet_anchor_norm": {"x": round(feet_x / fw - 0.5, 6), "y": round(0.5 - feet_y / fh, 6)},
        }

    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=118,
        actor_metadata=ACTOR_METADATA,
        body_metrics_fn=body_metrics,
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, out_dir)
    keys = ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "ROWS", "SHEET_FILES", "TARGET_NAME", "render", "render_frame", "render_portraits"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME,
    )
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
