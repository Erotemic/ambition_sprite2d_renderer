"""SVG-rigged Stochastic Parrot (v2): a scarlet macaw that mimics, squawks and dive-bombs.

The second version of :mod:`stochastic_parrot`, which stays published as its
lineage. A scarlet macaw drawn as an SVG and posed by a rig: the bare white
face patch lined with tiny red feathers, a great hooked pale beak over a black
lower mandible that gabbles, a smooth round crown,
pinning eyes, and wings that really spread: red shoulders, a yellow band
tipped green, blue flight feathers. Perched, the wing folds on the body;
flying, it beats.

The SVGs ``data/characters/stochastic_parrot_v2/stochastic_parrot_v2.svg``
(side), ``stochastic_parrot_v2_front.svg`` (facing the viewer) and
``stochastic_parrot_v2_three_quarter.svg`` (turned halfway) own the art
and mark every joint (their hidden ``Rig Joints`` layers). The rig documents
under ``rigged/stochastic_parrot_v2/`` own the skeletons and the clips;
``scripts/build_stochastic_parrot_v2_rig.py`` derives them (through
``rigbuild.creature_rig`` with the ``bird`` anatomy) and authors the clips.
Each clip also keys the eye state (``eye.*``), the wing look (``wing.folded``
/ ``wing.open``) and the strength of each effect (``fx.*``). This module owns
only the effects and publication.

A turnaround hops round through a three-quarter view and the front: its
frames are the side rig, the three-quarter rig, the front rig, then the
three-quarter and side rigs mirrored (the turning rigs' clips share the
turnaround rows' names).

Rows, frame counts and durations are the sheet contract the target always
published.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish stochastic_parrot_v2
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from . import _creature_fx as FX
from ._svg_fighter_effects import FxCanvas, compose_rig_frame

Point = Tuple[float, float]

TARGET_NAME = "stochastic_parrot_v2"
PARENT_TARGET = "stochastic_parrot"
VERSION = 2
USES_DROP_SHADOW = False
USES_PROPS = False
LINEAGE = {
    "family": "stochastic_parrot",
    "variant": "svg_rigged_v2",
    "parents": [PARENT_TARGET],
    "method": "svg_rig",
    "revision": "svg_rigged_redesign",
}
RIGGED = Path(__file__).resolve().parent / "rigged" / TARGET_NAME
RIG_PATH = RIGGED / "stochastic_parrot_v2_side.rig.json"
FRONT_RIG_PATH = RIGGED / "stochastic_parrot_v2_front.rig.json"
THREE_QUARTER_RIG_PATH = RIGGED / "stochastic_parrot_v2_three_quarter.rig.json"
FRAME_W, FRAME_H = 128, 128
#: Sprite pixels per SVG unit (the rigs' ``svg_source.scale``): drawn 512
#: units square, published in a 128 px frame.
ART_SCALE = 0.25
LOOPS = {"idle", "walk", "fly", "taunt"}
TURN_ROWS = {"turnaround", "turnaround_flight"}
#: Which view draws each turnaround frame.
TURN_VIEWS = ("side", "side", "three_quarter", "front", "front", "front", "three_quarter_mirror", "side_mirror", "side_mirror")


def _px(x: float, y: float) -> Dict[str, float]:
    """A point of the side drawing (SVG units) as a sprite-frame point."""
    return {"x": round(x * ART_SCALE, 1), "y": round(y * ART_SCALE, 1)}


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Stochastic Parrot v2"},
    "body": {
        "body_plan": "AvianBiped",
        "body_kind": "Floating",
        "mass_class": "Light",
        "locomotion_hint": "Fly",
        "traits": [
            "enemy",
            "bird",
            "mimic",
            "noisy",
            "chaotic",
            "versioned_variant",
            "svg_rigged",
        ],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "fly": True,
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
    "brain": {"default_preset": "parrot_lively"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.fly": {"animation": "fly", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {"t": 0.14, "event": "telegraph_peak", "source": TARGET_NAME},
                {"t": 0.29, "event": "hitbox_active_start", "source": TARGET_NAME},
                {"t": 0.57, "event": "hitbox_active_end", "source": TARGET_NAME},
            ],
        },
        "action.melee.peck": {
            "animation": "hover_peck",
            "events": [
                {"t": 0.22, "event": "hitbox_active_start", "source": TARGET_NAME},
                {"t": 0.33, "event": "hitbox_active_end", "source": TARGET_NAME},
                {"t": 0.56, "event": "hitbox_active_start", "source": TARGET_NAME},
                {"t": 0.67, "event": "hitbox_active_end", "source": TARGET_NAME},
            ],
        },
        "action.special.dive": {
            "animation": "dive_bomb",
            "events": [
                {"t": 0.12, "event": "telegraph_peak", "source": TARGET_NAME},
                {"t": 0.25, "event": "dive_commit", "source": TARGET_NAME},
                {"t": 0.62, "event": "hitbox_active_start", "source": TARGET_NAME},
                {"t": 0.75, "event": "hitbox_active_end", "source": TARGET_NAME},
            ],
        },
        "action.special.strafe": {
            "animation": "banked_strafe",
            "events": [
                {"t": 0.33, "event": "hitbox_active_start", "source": TARGET_NAME},
                {"t": 0.67, "event": "hitbox_active_end", "source": TARGET_NAME},
            ],
        },
        "emote.taunt": {"animation": "taunt", "events": []},
        "reaction.hurt": {"animation": "hurt", "events": []},
        "reaction.death": {"animation": "death", "events": []},
    },
    # Points on the drawn frame (before the sheet's auto-crop), perched at rest.
    "sockets": {
        "beak": {"source": "stochastic_parrot_v2.geometry", "point": _px(352.0, 250.0)},
        "head": {"source": "stochastic_parrot_v2.geometry", "point": _px(304.0, 208.0)},
        "talons": {"source": "stochastic_parrot_v2.geometry", "point": _px(270.0, 410.0)},
        "tail": {"source": "stochastic_parrot_v2.geometry", "point": _px(110.0, 402.0)},
    },
    "visual": {
        "default_pose": "idle",
        "canonical_source": "ambition_sprite2d_renderer/data/characters/stochastic_parrot_v2/stochastic_parrot_v2.svg",
    },
    "tags": [
        "enemy",
        "bird",
        "stochastic_parrot",
        "versioned_variant",
        "svg_rigged",
    ],
    "authoring_description": (
        "Stochastic Parrot v2 is the second rendering of the 'stochastic parrots' language-model "
        "critique: a scarlet macaw drawn as an SVG and posed by a rig. It keeps the same joke "
        "(impressive continuation and mimicry are not automatically comprehension) with a bird "
        "that really flies: its wings fold on the body when it perches and spread and beat when "
        "it takes off, and it squawks a balloon of noise when it taunts."
    ),
    "gameplay_description": (
        "Use as the preferred high-readability mimic enemy or chatter NPC. It can walk, fly, "
        "strafe with its talons, peck, wing-chop, dive-bomb and remix dialogue; games may choose "
        "this version while retaining the original as lineage or a weaker variant."
    ),
    "dialogue_hints": {
        "barks": [
            "Version two: twice the plumage, same epistemology.",
            "Fluent! Therefore correct!",
            "I can continue that sentence for you.",
        ]
    },
}


def _doc() -> RigDocument:
    return FX.rig_document(RIG_PATH)


def _turn_doc(view: str) -> RigDocument:
    return FX.rig_document(FRONT_RIG_PATH if view == "front" else THREE_QUARTER_RIG_PATH)


#: The sheet's rows are the side rig's clips, in its order (the game reads
#: them by name).
ROWS: List[Tuple[str, int, int]] = _doc().rows()

# --- Effect glyphs (`_creature_fx`), in glyph units (``FX_UNIT`` art units) ----

INK = (29, 20, 24, 255)
WHITE = (255, 252, 244, 255)
STREAK = (255, 248, 226, 150)
RED = (216, 53, 43, 255)
RED_DARK = (156, 28, 26, 255)
BLUE = (47, 111, 208, 255)
BLUE_LIGHT = (94, 156, 240, 255)
YELLOW = (246, 198, 50, 255)
SCRATCH = (255, 244, 214, 235)


def _feather(fill, tip):
    def paint(c: FxCanvas) -> None:
        pts = [(-14, 0), (-8, -5), (4, -5.5), (14, -2), (18, 0), (14, 2), (4, 5.5), (-8, 5)]
        c.polygon(pts, fill, INK, 1.2)
        c.polygon([(6, -4.5), (14, -2), (18, 0), (14, 2), (6, 4.5)], tip)
        c.line([(-16, 0), (14, 0)], INK, 0.9)

    return paint


def _paint_speed(c: FxCanvas) -> None:
    for y, x0, length in ((-24, 30, 60), (-6, 24, 84), (12, 34, 66), (28, 44, 46)):
        c.line([(x0, y), (x0 + length, y)], STREAK, 2.4)


def _paint_balloon(c: FxCanvas) -> None:
    """A squawk balloon full of plausible-looking nonsense: jagged edge, a
    tail to the beak, three lines of scribbled 'words'."""
    pts = []
    for k in range(18):
        a = math.tau * k / 18
        r = 1.0 if k % 2 == 0 else 0.8
        pts.append((36 * r * math.cos(a), 24 * r * math.sin(a)))
    c.polygon([(-20, 14), (-38, 32), (-8, 20)], WHITE, INK, 1.6)
    c.polygon(pts, WHITE, INK, 1.6)
    c.polygon([(-19, 13), (-34, 28), (-8, 19)], WHITE)
    for row, (y, words) in enumerate(((-8, (10, 6, 12)), (0, (7, 14, 4)), (8, (11, 8)))):
        x = -22 + 3 * row
        for wlen in words:
            wave = [(x + u, y + 1.0 * math.sin(u * 1.2 + row)) for u in range(0, wlen + 1, 2)]
            c.line(wave, (40, 40, 52, 255) if row != 1 else (200, 40, 40, 255), 1.8)
            x += wlen + 4


def _paint_noise(c: FxCanvas) -> None:
    """Sound coming off the beak: three arcs and two glints."""
    for r in (14, 26, 38):
        c.arc((0, 0), r, r, -40, 40, (255, 246, 214, 220), 2.6)
    c.star((44, -24), 6.0, YELLOW, points=4, inner=0.3, rotation=0)
    c.star((40, 26), 5.0, WHITE, points=4, inner=0.3, rotation=0)


def _paint_peck(c: FxCanvas) -> None:
    c.star((0, 0), 12.0, (255, 236, 120, 255), points=6, inner=0.35, rotation=0)
    c.star((0, 0), 6.0, WHITE, points=6, inner=0.45, rotation=30)
    for ang in (-50.0, 0.0, 50.0):
        r = math.radians(ang)
        c.line([(14 * math.cos(r), 14 * math.sin(r)), (24 * math.cos(r), 24 * math.sin(r))], WHITE, 2.0)


def _paint_chop(c: FxCanvas) -> None:
    """The wing chop's trail: an arc about the shoulder from over the back,
    over the head and down in front."""
    R = 170.0 / FX_UNIT
    c.arc((0, 0), R, R, -150, 50, (255, 255, 255, 90), 22.0)
    c.arc((0, 0), R, R, -140, 44, (255, 246, 214, 210), 7.0)
    c.arc((0, 0), R - 26, R - 26, -120, 36, (255, 246, 214, 130), 3.0)


def _paint_rake(c: FxCanvas) -> None:
    """Three claw slashes."""
    for k in (-1, 0, 1):
        c.polygon([(-26, -14 + 10 * k), (24, 8 + 10 * k), (28, 12 + 10 * k), (-20, -8 + 10 * k)], SCRATCH)


_GLYPHS: Dict[str, Tuple[FX.Extent, FX.Paint]] = {**FX.COMMON}
_GLYPHS["feather_red"] = ((18.0, 8.0, 20.0, 8.0), _feather(RED, BLUE))
_GLYPHS["feather_blue"] = ((18.0, 8.0, 20.0, 8.0), _feather(BLUE, BLUE_LIGHT))
_GLYPHS["feather_yellow"] = ((18.0, 8.0, 20.0, 8.0), _feather(YELLOW, RED))
_GLYPHS["speed"] = ((4.0, 28.0, 112.0, 32.0), _paint_speed)
_GLYPHS["balloon"] = ((42.0, 28.0, 40.0, 36.0), _paint_balloon)
_GLYPHS["noise"] = ((6.0, 44.0, 52.0, 44.0), _paint_noise)
_GLYPHS["peck"] = ((26.0, 26.0, 26.0, 26.0), _paint_peck)
_GLYPHS["chop"] = ((118.0, 118.0, 118.0, 96.0), _paint_chop)
_GLYPHS["rake"] = ((30.0, 26.0, 32.0, 26.0), _paint_rake)
#: The effects read at the sprite's small size only drawn bigger than the
#: art's own units: glyph units are this much larger than the drawing's.
FX_UNIT = 1.6
GLYPHS = FX.Glyphs(ART_SCALE * FX_UNIT, _GLYPHS)
_place = GLYPHS.place


def _local(bone, x: float, y: float) -> Point:
    """A point in a bone's frame given in the drawing's SVG units."""
    return bone.to_world((x * ART_SCALE, y * ART_SCALE))


#: The beak tip in the head bone's frame (SVG units: the bone runs from the
#: neck joint to the beak tip, 70 units).
BEAK_TIP = (72.0, 2.0)
FEATHERS = ("feather_red", "feather_blue", "feather_red", "feather_yellow", "feather_red", "feather_blue")


def _feather_burst(canvas: FxCanvas, t: float, world, strength: float) -> None:
    """Loose feathers flung out from the body, drifting as they go."""
    body = world["body"]
    centre = _local(body, 10.0, 0.0)
    for k, name in enumerate(FEATHERS):
        a = math.tau * k / len(FEATHERS) + 0.6
        reach = (50.0 + 90.0 * ((t * 1.6 + 0.13 * k) % 1.0)) * ART_SCALE
        at = (centre[0] + math.cos(a) * reach, centre[1] + math.sin(a) * reach * 0.8)
        _place(canvas, name, at, strength, degrees=math.degrees(a) + 40.0 * math.sin(t * 9.0 + k))


def _behind(canvas: FxCanvas, t: float, world, params) -> None:
    speed = params.get("fx.speed", 0.0)
    if speed > 0.02:
        body = world["body"]
        # Streaks trail back from the body against its flight line (level
        # flight pitches the body 36 degrees forward).
        _place(canvas, "speed", body.origin, speed, degrees=body.angle - 36.0 + 180.0)
    chop = params.get("fx.smear", 0.0)
    if chop > 0.02:
        _place(canvas, "chop", world["near_wing"].origin, chop)
    dust = params.get("fx.dust", 0.0)
    if dust > 0.02:
        ground = float(_doc().frame["ground_y"])
        x = world["body"].origin[0]
        _place(canvas, "dust", (x - 26.0 * ART_SCALE, ground), dust)
        _place(canvas, "dust", (x + 36.0 * ART_SCALE, ground), dust * 0.8)


def _front(canvas: FxCanvas, t: float, world, params) -> None:
    head = world["head"]
    beak = _local(head, *BEAK_TIP)
    for key, glyph in (("fx.peck", "peck"), ("fx.peck_big", "hit")):
        if params.get(key, 0.0) > 0.02:
            _place(canvas, glyph, _local(head, BEAK_TIP[0] + 10.0, BEAK_TIP[1]), params[key])
    # A blow landing on the parrot's chest; its own talons striking.
    _place(canvas, "hit", _local(world["body"], 40.0, -20.0), params.get("fx.hit", 0.0))
    foot = world["near_foot"].origin
    _place(canvas, "hit", (foot[0] + 10.0 * ART_SCALE, foot[1]), params.get("fx.strike", 0.0))
    if params.get("fx.rake", 0.0) > 0.02:
        _place(canvas, "rake", (foot[0] + 8.0 * ART_SCALE, foot[1] + 10.0 * ART_SCALE), params["fx.rake"])
    feathers = params.get("fx.feathers", 0.0)
    if feathers > 0.02:
        _feather_burst(canvas, t, world, feathers)
    drift = params.get("fx.drift", 0.0)
    if drift > 0.02:
        # One last feather seesawing down onto the body.
        body = world["body"].origin
        y = body[1] - (110.0 - 70.0 * t) * ART_SCALE
        x = body[0] + 18.0 * math.sin(t * 9.0) * ART_SCALE
        _place(canvas, "feather_red", (x, y), drift, degrees=25.0 * math.sin(t * 9.0))
    squawk = params.get("fx.squawk", 0.0)
    if squawk > 0.02:
        x, y = head.origin
        _place(canvas, "balloon", (x + 80.0 * ART_SCALE, y - 120.0 * ART_SCALE), squawk)
    noise = params.get("fx.notes", 0.0)
    if noise > 0.02 and params.get("jaw", 0.0) > 14.0:
        _place(canvas, "noise", beak, noise, degrees=head.angle)


def _side_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return compose_rig_frame(_doc(), animation, frame_idx, frame_count, behind=_behind, front=_front, fx_pieces=True)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    if animation in TURN_ROWS:
        view = TURN_VIEWS[min(frame_idx, len(TURN_VIEWS) - 1)]
        base = view.removesuffix("_mirror")
        if base == "side":
            frame = _side_frame(animation, frame_idx, frame_count)
        else:
            frame = compose_rig_frame(_turn_doc(base), animation, frame_idx, frame_count, fx_pieces=True)
        return rigdoc.mirrored_canvas(frame) if view.endswith("mirror") else frame
    return _side_frame(animation, frame_idx, frame_count)


# ---- Target registration hooks ------------------------------------------------


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        actor_metadata=ACTOR_METADATA,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[k]) for k in keys if outputs.get(k)] + list(parts.values())


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir))


__all__ = [
    "ACTOR_METADATA",
    "LINEAGE",
    "LOOPS",
    "PARENT_TARGET",
    "ROWS",
    "TARGET_NAME",
    "render",
    "render_canonical",
    "render_frame",
]
