"""SVG-rigged sprite target for the raptor stalker.

A feathered dromaeosaur that hunts in the open: a long low skull behind a dark
eye mask, a rust mane of raised feathers down the back of its neck and a rust
crest, barred teal plumage over a cream belly, feathered arms that flare as
wings, a stiff tail ending in a fan of vanes, and on each foot the raised
sickle claw it leads with when it pounces.

The SVG ``data/characters/raptor_stalker/raptor_stalker.svg`` owns the art and
marks every joint (its hidden ``Rig Joints`` layer). The rig document
``rigged/raptor_stalker/raptor_stalker_side.rig.json`` owns the skeleton and the
clips; ``scripts/build_raptor_stalker_rig.py`` derives it from the SVG (through
``rigbuild.theropod``, shared with the T-rex boss) and authors the clips. Each
clip also keys the eye state (``eye.*``) and the strength of each effect
(``fx.*``). This module owns only the effects and publication.

Rows, frame counts, durations, animation bindings and events are the sheet
contract the game already reads; they are unchanged by the SVG redesign.
"""

from __future__ import annotations

import argparse
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

TARGET_BASENAME = "raptor_stalker"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_BASENAME / "raptor_stalker_side.rig.json"
FRAME_SIZE = (228, 152)
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``): the art is
#: drawn at 600x400 units and published at the size the raptor always had.
ART_SCALE = 0.38
GROUND_Y = 372.0 * ART_SCALE


def _px(x: float, y: float) -> Dict[str, float]:
    """A point of the drawing (SVG units) as a sprite-frame point."""
    return {"x": round(x * ART_SCALE, 1), "y": round(y * ART_SCALE, 1)}


ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_raptor_stalker",
        "display_name": "Raptor Stalker",
    },
    "body": {
        "body_plan": "BeastBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "locomotion_hint": "Run",
        "traits": ["enemy", "beast", "dinosaur", "stalker", "no_hands", "svg_rigged"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": {"height_px": None, "distance_px": None, "source": "raptor_pounce_animation"},
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
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "striker_swipe"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.run": {"animation": "walk", "events": []},
        "action.melee.primary": {
            "animation": "bite",
            "events": [
                {"t": 0.34, "event": "hitbox_active_start", "source": "raptor_stalker.bite"},
                {"t": 0.56, "event": "hitbox_active_end", "source": "raptor_stalker.bite"},
            ],
        },
        "action.melee.tail_sweep": {
            "animation": "tail_sweep",
            "events": [
                {"t": 0.32, "event": "hitbox_active_start", "source": "raptor_stalker.tail_sweep"},
                {"t": 0.64, "event": "hitbox_active_end", "source": "raptor_stalker.tail_sweep"},
            ],
        },
        "action.special.pounce": {"animation": "pounce", "events": [{"t": 0.42, "event": "leap_commit", "source": "raptor_stalker.pounce"}]},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    # Points on the drawn frame (before the sheet's auto-crop), at rest.
    "sockets": {
        "head": {"source": "raptor_stalker.geometry", "point": _px(445.0, 152.0)},
        "mouth": {"source": "raptor_stalker.geometry", "point": _px(492.0, 170.0)},
        "tail_base": {"source": "raptor_stalker.geometry", "point": _px(256.0, 220.0)},
        "tail_tip": {"source": "raptor_stalker.geometry", "point": _px(80.0, 208.0)},
        "foreclaw": {"source": "raptor_stalker.geometry", "point": _px(396.0, 284.0)},
        "pounce_origin": {"source": "raptor_stalker.geometry", "point": _px(302.0, 372.0)},
    },
    "visual": {
        "default_pose": "idle",
        "canonical_source": "ambition_sprite2d_renderer/data/characters/raptor_stalker/raptor_stalker.svg",
        "portrait": {
            "face_guide": {
                "center": _px(452.0, 160.0),
                "size": {"width": round(120.0 * ART_SCALE, 1), "height": round(84.0 * ART_SCALE, 1)},
                "source_size": {"width": FRAME_SIZE[0], "height": FRAME_SIZE[1]},
            }
        },
    },
    "tags": ["enemy", "beast", "dinosaur", "svg_rigged"],
    "authoring_description": (
        "A dromaeosaur ('raptor') enemy: a genre creature, not a parody of a person. The look "
        "follows feathered reconstructions of Velociraptor and Deinonychus (pennaceous feathers on "
        "the arms and a fan at the tail's end, a long low skull, the raised sickle claw on the "
        "second toe) pushed toward a readable side-scroller hunter: a dark eye mask, a rust mane "
        "and crest, barred plumage. The stalking run, bite, tail sweep and claws-first pounce are "
        "gameplay inventions built on the animal's reputation, not claims about how it hunted."
    ),
}


def _doc() -> RigDocument:
    return FX.rig_document(RIG_PATH)


#: The sheet's rows are the rig's clips, in the rig's order (the game reads
#: them by name).
ROWS: List[Tuple[str, int, int]] = _doc().rows()

# --- Effect glyphs (`_creature_fx`), in SVG units like the art ----------------

RAKE = (255, 246, 214, 255)
RAKE_GLOW = (255, 196, 120, 140)


def _paint_rake(c: FxCanvas) -> None:
    # Three claw slashes, raked down and forward.
    for k in range(3):
        off = (k - 1) * 11.0
        pts = [(-22 + off, -24 + off * 0.3), (-4 + off, -4 + off * 0.3), (16 + off, 22 + off * 0.3)]
        c.line(pts, RAKE_GLOW, 6.0)
        c.line(pts, RAKE, 2.4)


SWEEP_R = 170.0

GLYPHS = FX.Glyphs(
    ART_SCALE,
    {
        **FX.COMMON,
        "sweep": ((8.0, 108.0, 50.0, 108.0), FX.tail_trail(SWEEP_R)),
        "rake": ((40.0, 34.0, 40.0, 34.0), _paint_rake),
    },
)
_place = GLYPHS.place
_local = GLYPHS.local


def _foot_ground(world, side: str) -> Point:
    """Where a foot's toes meet the ground under it."""
    ankle = world[f"{side}_foot"].origin
    return (ankle[0] + 22.0 * ART_SCALE, GROUND_Y - 1.0)


def _behind(canvas: FxCanvas, t: float, world, params) -> None:
    sweep = params.get("fx.sweep", 0.0)
    if sweep > 0.02:
        base = world["tail1"].origin
        _place(canvas, "sweep", (base[0] - SWEEP_R * ART_SCALE, base[1] - 10.0 * ART_SCALE), sweep)


def _front(canvas: FxCanvas, t: float, world, params) -> None:
    head = world["head"]
    _place(canvas, "bite", _local(head, 96.0, 6.0), params.get("fx.bite", 0.0), degrees=head.angle)
    dust = params.get("fx.dust", 0.0)
    if dust > 0.02:
        for side, fade in (("near", 1.0), ("far", 0.7)):
            x, y = _foot_ground(world, side)
            _place(canvas, "dust", (x - 18.0 * ART_SCALE, y - 2.0), dust * fade)
            _place(canvas, "dust", (x + 16.0 * ART_SCALE, y - 1.0), dust * fade * 0.8)
    rake = params.get("fx.rake", 0.0)
    if rake > 0.02:
        foot = world["near_foot"]
        _place(canvas, "rake", _local(foot, 40.0, 8.0), rake)
    hit = params.get("fx.hit", 0.0)
    if hit > 0.02:
        _place(canvas, "hit", _local(world["torso"], 70.0, 6.0), hit)
    thud = params.get("fx.thud", 0.0)
    if thud > 0.02:
        _place(canvas, "thud", (world["pelvis"].origin[0] + 30.0 * ART_SCALE, GROUND_Y - 3.0), thud)


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
    center_x=452.0 * ART_SCALE,
    center_y=160.0 * ART_SCALE,
    width=120.0 * ART_SCALE,
    height=84.0 * ART_SCALE,
    source_width=FRAME_SIZE[0],
    source_height=FRAME_SIZE[1],
)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    """Dialog portraits rerendered from the rig at 5x, never the sheet."""
    del opts
    doc = _doc()

    def portrait_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        source = doc.render_at(animation, doc.frame_time(animation, frame_idx, frame_count), supersample=3, scale=5)
        return render_framed_portrait(source, FACE, view_width=170.0 * ART_SCALE, center_y=164.0 * ART_SCALE)

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 1, 6)),
        "hissing": PortraitClip(
            tuple(portrait_frame("bite", frame, 7) for frame in (2, 3, 4)),
            duration_ms=90,
            looping=True,
        ),
        "hurt": PortraitClip.still(portrait_frame("hurt", 2, 4)),
    }
    return write_portrait_sheet(TARGET_BASENAME, clips, Path(out_dir))


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_BASENAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=True,
        actor_metadata=ACTOR_METADATA,
    )
    parts = publish_rig_flipbook(TARGET_BASENAME, ROWS, render_frame, outputs, frame_transform, out_dir)
    keys = ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "ROWS", "TARGET_BASENAME", "render", "render_frame", "render_portraits"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "generated" / TARGET_BASENAME,
    )
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
