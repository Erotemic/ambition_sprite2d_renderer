"""SVG-rigged sprite target for the T-rex boss, the Tyrant King.

A modern side-view tyrannosaur, built to read as a boss at a glance: a massive
deep skull with a rust-coloured brow horn and a fan of curved fangs, a heavy
horizontal body balanced over drumstick thighs, tiny two-clawed arms, a long
counterbalancing tail, olive tiger stripes over countershaded cream scales,
and three raked claw scars on its flank from some earlier rival.

The SVG ``data/characters/trex_enemy/trex_enemy.svg`` owns the art and marks
every joint (its hidden ``Rig Joints`` layer). The rig document
``rigged/trex_enemy/trex_enemy_side.rig.json`` owns the skeleton and the clips;
``scripts/build_trex_enemy_rig.py`` derives it from the SVG and authors the
clips. Each clip also keys the eye state (``eye.*``) and the strength of each
effect (``fx.*``). This module owns only the effects and publication.

Rows, frame counts, durations, animation bindings and events are the sheet
contract the game already reads; they are unchanged by the SVG redesign.

Each effect is a glyph painted once and placed with its strength as the draw's
opacity, so the part flipbook stores one raster per glyph, not one per frame.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image
import yaml

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

TARGET_NAME = "trex_enemy"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "trex_enemy_side.rig.json"
FRAME_SIZE = (480, 300)
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``): the art is
#: drawn at 640x400 units and published at the size the T-rex always had.
ART_SCALE = 0.75
GROUND_Y = 372.0 * ART_SCALE


def _px(x: float, y: float) -> Dict[str, float]:
    """A point of the drawing (SVG units) as a sprite-frame point."""
    return {"x": round(x * ART_SCALE, 1), "y": round(y * ART_SCALE, 1)}


ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_trex_enemy",
        "display_name": "T-Rex Enemy",
    },
    "body": {
        "body_plan": "BeastBiped",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "locomotion_hint": "HeavyWalk",
        "traits": ["enemy", "beast", "dinosaur", "heavy", "no_hands", "stomper", "svg_rigged"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "crawl": None,
            "fly": None,
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
    "brain": {"default_preset": "melee_brute_brute"},
    "actions": {"default_preset": "brute_lunge"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk_heavy": {"animation": "walk", "events": []},
        "action.special.charge": {
            "animation": "charge",
            "events": [
                {"t": 0.20, "event": "charge_commit", "source": "trex_enemy.charge"}
            ],
        },
        "action.melee.primary": {
            "animation": "bite",
            "events": [
                {
                    "t": 0.32,
                    "event": "hitbox_active_start",
                    "source": "trex_enemy.bite",
                },
                {"t": 0.55, "event": "hitbox_active_end", "source": "trex_enemy.bite"},
            ],
        },
        "action.melee.tail_sweep": {
            "animation": "tail_swipe",
            "events": [
                {
                    "t": 0.36,
                    "event": "hitbox_active_start",
                    "source": "trex_enemy.tail_swipe",
                },
                {
                    "t": 0.66,
                    "event": "hitbox_active_end",
                    "source": "trex_enemy.tail_swipe",
                },
            ],
        },
        "action.melee.stomp": {
            "animation": "stomp",
            "events": [
                {"t": 0.48, "event": "ground_impact", "source": "trex_enemy.stomp"}
            ],
        },
        "interaction.roar": {
            "animation": "roar",
            "events": [{"t": 0.44, "event": "sfx_cue", "source": "trex_enemy.roar"}],
        },
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    # Points on the drawn frame (before the sheet's auto-crop), at rest.
    "sockets": {
        "head": {"source": "trex_enemy.geometry", "point": _px(456.0, 121.0)},
        "mouth": {"source": "trex_enemy.geometry", "point": _px(524.0, 160.0)},
        "roar_origin": {"source": "trex_enemy.geometry", "point": _px(546.0, 160.0)},
        "tail_base": {"source": "trex_enemy.geometry", "point": _px(222.0, 198.0)},
        "tail_tip": {"source": "trex_enemy.geometry", "point": _px(38.0, 217.0)},
        "foot_l": {"source": "trex_enemy.geometry", "point": _px(312.0, 371.0)},
        "foot_r": {"source": "trex_enemy.geometry", "point": _px(328.0, 371.0)},
    },
    "visual": {
        "default_pose": "idle",
        "canonical_source": "ambition_sprite2d_renderer/data/characters/trex_enemy/trex_enemy.svg",
        "portrait": {
            "face_guide": {
                "center": _px(474.0, 140.0),
                "size": {"width": round(150.0 * ART_SCALE, 1), "height": round(105.0 * ART_SCALE, 1)},
                "source_size": {"width": FRAME_SIZE[0], "height": FRAME_SIZE[1]},
            }
        },
    },
    "tags": ["enemy", "heavy", "dinosaur", "boss", "svg_rigged"],
    "authoring_description": (
        "A Tyrannosaurus rex boss: the genre's apex movie monster rather than a parody of a "
        "person. The art follows modern side-view reconstructions (horizontal back, tail held "
        "out as a counterweight, a deep skull with a brow horn over the eye, tiny two-fingered "
        "arms, digitigrade three-toed feet) and pushes them toward a readable game boss: an "
        "oversized head, a fan of fangs outside the closed mouth, tiger striping, and claw "
        "scars from an earlier rival. The bite, roar, tail sweep, stomp and charge are "
        "gameplay inventions built on the animal's reputation, not claims about how it hunted."
    ),
}


def _doc() -> RigDocument:
    return FX.rig_document(RIG_PATH)


#: The sheet's rows are the rig's clips, in the rig's order (the game reads
#: them by name).
ROWS: List[Tuple[str, int, int]] = _doc().rows()

# --- Effect glyphs (`_creature_fx`), in SVG units like the art ----------------

ROAR = (255, 244, 214, 255)
ROAR_SOFT = (255, 214, 150, 150)


def _roar_wave(rx: float, ry: float, width: float) -> FX.Paint:
    def paint(c: FxCanvas) -> None:
        c.arc((-rx * 0.82, 0), rx, ry, -42, 42, ROAR_SOFT, width + 2.2)
        c.arc((-rx * 0.82, 0), rx, ry, -40, 40, ROAR, width)

    return paint


SWIPE_R = 175.0

STAR = (255, 230, 110, 255)
STAR_EDGE = (150, 96, 20, 255)


def _star(c: FxCanvas) -> None:
    c.star((0, 0), 16.0, STAR, points=5, inner=0.45, outline=STAR_EDGE)

GLYPHS = FX.Glyphs(
    ART_SCALE,
    {
        **FX.COMMON,
        "roar0": ((28.0, 30.0, 12.0, 30.0), _roar_wave(26.0, 34.0, 2.6)),
        "roar1": ((40.0, 46.0, 14.0, 46.0), _roar_wave(40.0, 52.0, 2.4)),
        "roar2": ((54.0, 62.0, 16.0, 62.0), _roar_wave(54.0, 70.0, 2.2)),
        "swipe": ((8.0, 110.0, 52.0, 110.0), FX.tail_trail(SWIPE_R)),
        "star": ((18.0, 18.0, 18.0, 18.0), _star),
    },
)
_place = GLYPHS.place
_local = GLYPHS.local


def _foot_ground(world, side: str) -> Point:
    """Where a foot's toes meet the ground under it."""
    ankle = world[f"{side}_foot"].origin
    return (ankle[0] + 28.0 * ART_SCALE, GROUND_Y - 1.5)


def _behind(canvas: FxCanvas, t: float, world, params) -> None:
    swipe = params.get("fx.swipe", 0.0)
    if swipe > 0.02:
        base = world["tail1"].origin
        _place(canvas, "swipe", (base[0] - SWIPE_R * ART_SCALE, base[1] + 4.0), swipe)


def _front(canvas: FxCanvas, t: float, world, params) -> None:
    head = world["head"]
    jaw = world["jaw"]
    roar = params.get("fx.roar", 0.0)
    if roar > 0.02:
        # Waves leave the open mouth along the gape's bisector.
        gape = (head.angle + jaw.angle) / 2.0
        mouth = _local(jaw, 96.0, -12.0)
        rad = math.radians(gape)
        for i, dist in enumerate((14.0, 32.0, 50.0)):
            at = (mouth[0] + math.cos(rad) * dist, mouth[1] + math.sin(rad) * dist)
            _place(canvas, f"roar{i}", at, roar * (1.0 - 0.18 * i), degrees=gape)
    _place(canvas, "bite", _local(head, 126.0, 6.0), params.get("fx.bite", 0.0), degrees=head.angle)
    dust = params.get("fx.dust", 0.0)
    if dust > 0.02:
        for side, shift, fade in (("near", 0.0, 1.0), ("far", -18.0, 0.7)):
            x, y = _foot_ground(world, side)
            k = ART_SCALE
            _place(canvas, "dust", (x + (shift - 22.0) * k, y - 3.0), dust * fade)
            _place(canvas, "dust", (x + (shift + 18.0) * k, y - 2.0), dust * fade * 0.8)
    stomp = params.get("fx.stomp", 0.0)
    if stomp > 0.02:
        x, _y = _foot_ground(world, "near")
        _place(canvas, "shock", (x, GROUND_Y), stomp)
    hit = params.get("fx.hit", 0.0)
    if hit > 0.02:
        _place(canvas, "hit", _local(world["torso"], 104.0, 4.0), hit)
    stars = params.get("fx.stars", 0.0)
    if stars > 0.02:
        # Three stars circling over his brow, a third of a turn apart, going
        # round once a loop of the row.
        brow = _local(head, 60.0, -46.0)
        for k in range(3):
            a = math.tau * (t + k / 3.0)
            at = (brow[0] + math.cos(a) * 52.0 * ART_SCALE, brow[1] + math.sin(a) * 14.0 * ART_SCALE)
            _place(canvas, "star", at, stars * (0.75 + 0.25 * math.sin(a)))
    thud = params.get("fx.thud", 0.0)
    if thud > 0.02:
        _place(canvas, "thud", (world["pelvis"].origin[0] + 40.0 * ART_SCALE, GROUND_Y - 4.0), thud)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return compose_rig_frame(
        _doc(),
        animation,
        frame_idx,
        frame_count,
        behind=_behind,
        front=_front,
        fx_pieces=True,
    )


FACE = FaceGuide(
    center_x=474.0 * ART_SCALE,
    center_y=140.0 * ART_SCALE,
    width=150.0 * ART_SCALE,
    height=105.0 * ART_SCALE,
    source_width=FRAME_SIZE[0],
    source_height=FRAME_SIZE[1],
)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    """Dialog portraits rerendered from the rig at 3x, never the sheet."""
    del opts
    doc = _doc()

    def portrait_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        source = doc.render_at(animation, doc.frame_time(animation, frame_idx, frame_count), supersample=3, scale=3)
        return render_framed_portrait(source, FACE, view_width=215.0 * ART_SCALE, center_y=146.0 * ART_SCALE)

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 1, 6)),
        "roaring": PortraitClip(
            tuple(portrait_frame("roar", frame, 6) for frame in (2, 3, 4)),
            duration_ms=104,
            looping=True,
        ),
        "hurt": PortraitClip.still(portrait_frame("hurt", 2, 4)),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=opts.get("frame_size", FRAME_SIZE),
        crop_margin=10,
        auto_crop=True,
        actor_metadata=ACTOR_METADATA,
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, out_dir)
    # His semantic body rig, solved from the same rig as the frames above: the
    # parts the game hits him through follow his pose (a gameplay product; it
    # does not change the sheet).
    from ._trex_enemy_body_rig import body_rig

    metrics = yaml.safe_load(Path(outputs["yaml"]).read_text()).get("body_metrics") or {}
    feet = metrics.get("feet_pixel") or {}
    rig = body_rig(_doc(), TARGET_NAME, ROWS, frame_transform, (float(feet["x"]), float(feet["y"])))
    keys = ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values()) + [rig.write(out_dir)]


__all__ = ["ACTOR_METADATA", "ROWS", "TARGET_NAME", "render", "render_frame", "render_portraits"]


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
