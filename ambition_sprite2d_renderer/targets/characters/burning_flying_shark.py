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
# THE FIRE. A flame is a tongue along +x from its root: a red edge, an orange
# body, a yellow heart and a pale core. It has a centre line that bends, more
# toward its tip, and a small second tongue that forks off it. There are six
# shapes of each size; a place on the shark shows one shape after the other,
# so the fire moves, and each place is at a phase of its own, so the fire does
# not beat as one. A tongue is drawn once and placed many times.
#
# Fire is in four places:
# * the fins and the tail: tongues off each trailing edge (as before);
# * BEHIND the back: tall tongues that rise from the far side of the back;
# * ON the back: shorter tongues over the upper flank, on a line of soot;
# * off the shark: small flames that come away, go up and back, and go out.

FLAME_LAYERS = (
    ((214, 52, 18, 215), 1.0, 1.0),
    ((255, 128, 30, 235), 0.76, 0.78),
    ((255, 208, 84, 245), 0.52, 0.56),
    ((255, 248, 214, 255), 0.27, 0.32),
)

#: The six shapes: (how far the tip leans, how often the centre line bends,
#: where in the bend it starts, its length, the side the fork is on).
FLAME_SHAPES = (
    (0.34, 1.0, 0.0, 1.00, 1.0),
    (-0.30, 1.2, 0.8, 0.88, -1.0),
    (0.46, 1.5, 1.9, 1.10, -1.0),
    (-0.40, 0.9, 2.7, 0.80, 1.0),
    (0.24, 1.8, 3.6, 1.05, 1.0),
    (-0.50, 1.3, 4.4, 0.94, -1.0),
)


def _tongue(length: float, width: float, lean: float, bends: float, start: float) -> List[Point]:
    """The outline of one tongue of flame: round at the root, a point at the tip."""
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


def _paint_ember(c: FxCanvas) -> None:
    c.ellipse((0, 0), 4.5, 4.5, (255, 140, 36, 150))
    c.ellipse((0, 0), 2.2, 2.2, (255, 236, 160, 255))


def _paint_speed(c: FxCanvas) -> None:
    for y, length in ((-34, 70), (0, 110), (30, 80)):
        c.line([(0, y), (length, y)], (255, 246, 214, 120), 3.0)


def _paint_soot(c: FxCanvas) -> None:
    """A burn on the skin, under a flame: dark at the middle, brown at the edge."""
    c.polygon([(-26, 0), (-16, -6), (0, -8), (18, -6), (28, 0), (20, 7), (2, 9), (-14, 7)], (96, 62, 40, 150))
    c.polygon([(-16, 0), (-6, -4), (8, -4), (18, 0), (8, 5), (-6, 5)], (44, 32, 30, 190))


#: The sizes of flame: name -> (length, width, it forks).
FLAME_SIZES = {
    "flame": (48.0, 26.0, True),        # a fin, at rest
    "flame_big": (70.0, 32.0, True),    # a fin, in a flare
    "fire": (60.0, 34.0, True),         # on the back
    "fire_tall": (92.0, 42.0, True),    # behind the back
    "lick_a": (34.0, 20.0, False),      # a flame that has come away, and
    "lick_b": (22.0, 13.0, False),      # the same one as it goes out
    "lick_c": (13.0, 8.0, False),
}

_GLYPHS: Dict[str, Tuple[FX.Extent, FX.Paint]] = {**FX.COMMON}
for _name, (_length, _width, _fork) in FLAME_SIZES.items():
    for _k in range(len(FLAME_SHAPES)):
        _GLYPHS[f"{_name}{_k}"] = (_flame_extent(_length, _width), _flame(_length, _width, _k, _fork))
_GLYPHS["ember"] = ((6.0, 6.0, 6.0, 6.0), _paint_ember)
_GLYPHS["speed"] = ((4.0, 38.0, 114.0, 34.0), _paint_speed)
_GLYPHS["soot"] = ((30.0, 11.0, 32.0, 12.0), _paint_soot)
GLYPHS = FX.Glyphs(ART_SCALE, _GLYPHS)
_place = GLYPHS.place
_local = GLYPHS.local

REST = FX.rest_frames(_doc())

#: Where the fins burn: (bone, a drawn point on it in SVG units, the flame's
#: rest heading in degrees (y down; 180 streams straight back), its phase).
#: Each is rooted a little inside its fin's trailing edge, so the fin covers
#: its root, and licks up and back the way fire rises off a moving body.
FLAMES = (
    ("dorsal", (350.0, 116.0), 218.0, 0.0),
    ("dorsal", (354.0, 140.0), 206.0, 1.7),
    ("near_pec", (358.0, 294.0), 196.0, 0.9),
    ("near_pec", (380.0, 268.0), 202.0, 2.6),
    ("fluke", (130.0, 164.0), 210.0, 1.3),
    ("fluke", (150.0, 206.0), 196.0, 2.2),
    ("fluke", (136.0, 236.0), 188.0, 0.4),
    ("tail1", (276.0, 180.0), 222.0, 3.1),
)

#: The line of the back, nose to tail, in SVG units (the art script's ``TOP``).
_BACK = ((536, 218), (530, 206), (516, 194), (492, 183), (460, 174), (420, 167), (380, 163), (340, 164),
         (300, 172), (265, 184), (235, 196), (210, 204), (188, 208), (168, 210))


def _back_y(x: float) -> float:
    for (x0, y0), (x1, y1) in zip(_BACK, _BACK[1:]):
        if x1 <= x <= x0:
            return y0 + (y1 - y0) * (x0 - x) / (x0 - x1)
    return _BACK[0][1] if x > _BACK[0][0] else _BACK[-1][1]


def _back_bone(x: float) -> str:
    """The bone that carries the back at ``x``."""
    return "head" if x > 432.0 else "body" if x > 282.0 else "tail1" if x > 216.0 else "tail2"


def _back_fire(xs: Sequence[float], sink: float, heading: float, spread: float) -> Tuple[Tuple[str, Point, float, float], ...]:
    """Flames along the back at each ``x``, rooted ``sink`` under its line."""
    return tuple(
        (_back_bone(x), (x, _back_y(x) + sink), heading + spread * math.sin(1.7 * i), 0.9 * i + 0.3 * sink)
        for i, x in enumerate(xs)
    )


#: The fire behind the back (tall, it rises), and the fire on it (shorter, it
#: streams back), with a burn of soot under each of those.
FIRE_BEHIND = _back_fire((486.0, 438.0, 392.0, 348.0, 306.0, 266.0, 228.0), 10.0, 246.0, 9.0)
FIRE_ON = _back_fire((462.0, 414.0, 368.0, 324.0, 284.0, 246.0), 22.0, 226.0, 8.0)


def _anchors(places) -> List[Point]:
    return [FX.anchor(REST, bone, point, ART_SCALE) for bone, point, _deg, _phase in places]


_ANCHORS = _anchors(FLAMES)
_ANCHORS_BEHIND = _anchors(FIRE_BEHIND)
_ANCHORS_ON = _anchors(FIRE_ON)
#: How many small flames are in the air at once, and how many embers.
LICKS, EMBERS = 6, 8


def _shape(t: float, index: int, rate: int) -> int:
    """The shape a place shows at ``t``: one after the other, ``rate`` times
    through the six in a row, from a start of its own."""
    return int((t * rate + index * 0.37) * len(FLAME_SHAPES)) % len(FLAME_SHAPES)


def _burn(canvas: FxCanvas, t: float, world, strength: float, places, anchors, name: str, rate: int, wobble: float) -> None:
    for i, ((bone, _point, deg, phase), local) in enumerate(zip(places, anchors)):
        bw = world[bone]
        turn = bw.angle - REST[bone][1]
        sway = wobble * math.sin(math.tau * t * 2.0 + phase)
        opacity = strength * (0.84 + 0.16 * math.cos(math.tau * t * 3.0 + phase))
        _place(canvas, f"{name}{_shape(t, i, rate)}", bw.to_world(local), opacity, degrees=deg + turn + sway)


def _behind(canvas: FxCanvas, t: float, world, params) -> None:
    flame = params.get("fx.flame", 0.0)
    flare = params.get("fx.flare", 0.0)
    if params.get("fx.speed", 0.0) > 0.02:
        body = world["body"]
        _place(canvas, "speed", _local(body, -130.0, -10.0), params["fx.speed"], degrees=body.angle + 180.0)
    if flame > 0.02:
        _burn(canvas, t, world, flame, FIRE_BEHIND, _ANCHORS_BEHIND, "fire_tall", 1, 7.0)
        _burn(canvas, t, world, flame, FLAMES, _ANCHORS, "flame_big" if flare > 0.5 else "flame", 1, 8.0)
        # Embers come off the whole of the back and are left behind.
        body = world["body"]
        lean = math.radians(body.angle - REST["body"][1])
        for k in range(EMBERS):
            u = (t * 2.0 + k / EMBERS) % 1.0
            bone, point, _deg, _phase = FIRE_BEHIND[k % len(FIRE_BEHIND)]
            root = world[bone].to_world(_ANCHORS_BEHIND[k % len(FIRE_BEHIND)])
            back, up = (30.0 + 190.0 * u) * ART_SCALE, (26.0 + 70.0 * u + 26.0 * math.sin(k * 2.1 + u * 6.0)) * ART_SCALE
            x = root[0] - back * math.cos(lean) + up * math.sin(lean)
            y = root[1] - back * math.sin(lean) - up * math.cos(lean)
            _place(canvas, "ember", (x, y), flame * (1.0 - u))


def _front(canvas: FxCanvas, t: float, world, params) -> None:
    flame = params.get("fx.flame", 0.0)
    if flame > 0.02:
        for (bone, _point, _deg, _phase), local in zip(FIRE_ON, _ANCHORS_ON):
            bw = world[bone]
            _place(canvas, "soot", bw.to_world(local), min(1.0, flame), degrees=bw.angle - REST[bone][1] + 4.0)
        _burn(canvas, t, world, flame, FIRE_ON, _ANCHORS_ON, "fire", 1, 9.0)
        # Small flames come away from the back, go up and back, and go out.
        body = world["body"]
        lean = math.radians(body.angle - REST["body"][1])
        for k in range(LICKS):
            u = (t + k / LICKS) % 1.0
            bone, _point, deg, _phase = FIRE_ON[(k * 2) % len(FIRE_ON)]
            root = world[bone].to_world(_ANCHORS_ON[(k * 2) % len(FIRE_ON)])
            back, up = (24.0 + 120.0 * u) * ART_SCALE, (38.0 + 86.0 * u) * ART_SCALE
            x = root[0] - back * math.cos(lean) + up * math.sin(lean)
            y = root[1] - back * math.sin(lean) - up * math.cos(lean)
            size = "lick_a" if u < 0.4 else "lick_b" if u < 0.72 else "lick_c"
            _place(canvas, f"{size}{_shape(t, k, 2)}", (x, y), flame * (1.0 - u) ** 0.6,
                   degrees=deg + math.degrees(lean) + 14.0 * math.sin(math.tau * u + k))
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


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=118,
        actor_metadata=ACTOR_METADATA,
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
