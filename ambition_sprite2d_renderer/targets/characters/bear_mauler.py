"""SVG-rigged sprite target for the bear mauler.

A battle-scarred grizzly: a heavy body under a shoulder hump of
silver-tipped fur, shaggy fringes along the back and belly, a dished face with
a tan muzzle and a black nose, round ears (the near one torn), small amber
eyes under a heavy brow, long ivory claws on the forepaws, and three pale
claw scars across the shoulder from the last thing that fought it.

The SVG ``data/characters/bear_mauler/bear_mauler.svg`` owns the art and marks
every joint (its hidden ``Rig Joints`` layer). The rig document
``rigged/bear_mauler/bear_mauler_side.rig.json`` owns the skeleton and the
clips; ``scripts/build_bear_mauler_rig.py`` derives it from the SVG (through
``rigbuild.creature_rig`` with the ``quadruped`` anatomy) and authors the
clips. Each clip also keys the eye state (``eye.*``) and the strength of each
effect (``fx.*``). This module owns only the effects and publication.

Rows, frame counts and durations are the sheet contract the game already
reads; they are unchanged by the SVG redesign.
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

TARGET_BASENAME = "bear_mauler"
TARGET_NAME = TARGET_BASENAME
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_BASENAME / "bear_mauler_side.rig.json"
FRAME_SIZE = (202, 144)
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``): the art is
#: drawn at 560x400 units and published at the size the bear always had.
ART_SCALE = 0.36
GROUND_Y = 372.0 * ART_SCALE


def _px(x: float, y: float) -> Dict[str, float]:
    """A point of the drawing (SVG units) as a sprite-frame point."""
    return {"x": round(x * ART_SCALE, 1), "y": round(y * ART_SCALE, 1)}


ACTOR_METADATA = {
    "actor": {"character_id": "npc_bear_mauler", "display_name": "Bear Mauler"},
    "body": {
        "body_plan": "Quadruped",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "traits": ["enemy", "beast", "no_hands", "bear", "mauler", "svg_rigged"],
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
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {"talk": None, "trade": None, "carry": None, "open_doors": []},
    },
    "brain": {"default_preset": "melee_brute_brute"},
    "actions": {"default_preset": "beast_bite"},
    "visual": {
        "default_pose": "idle",
        "canonical_source": "ambition_sprite2d_renderer/data/characters/bear_mauler/bear_mauler.svg",
        "portrait": {
            "face_guide": {
                "center": _px(432.0, 224.0),
                "size": {"width": round(110.0 * ART_SCALE, 1), "height": round(90.0 * ART_SCALE, 1)},
                "source_size": {"width": FRAME_SIZE[0], "height": FRAME_SIZE[1]},
            }
        },
    },
    "tags": ["enemy", "beast", "no_hands", "bear", "mauler", "svg_rigged"],
    # Points on the drawn frame (before the sheet's auto-crop), at rest.
    "sockets": {
        "mouth": {"source": "explicit.profile.beast", "point": _px(474.0, 252.0)},
        "tail_tip": {"source": "explicit.profile.beast", "point": _px(130.0, 216.0)},
        "center": {"source": "explicit.profile.beast", "point": _px(256.0, 232.0)},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        # The primary attack is the claw swipe (this bound a "bite" row the
        # sheet never had).
        "action.melee.primary": {
            "animation": "swipe",
            "events": [
                {"t": 0.35, "event": "hitbox_active_start", "source": "explicit.profile.beast"},
                {"t": 0.58, "event": "hitbox_active_end", "source": "explicit.profile.beast"},
            ],
        },
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "authoring_description": (
        "A grizzly bear enemy: a genre wilderness threat, not a parody of a person. The look "
        "follows a brown bear's real side profile (the shoulder hump, dished face, small round "
        "ears, plantigrade paws with long fore-claws) pushed toward a readable brute: grizzled "
        "fur, a torn ear and claw scars from earlier fights. The swipe, rear-up slam and charge "
        "are gameplay inventions built on the animal's reputation, not claims about how bears "
        "fight."
    ),
}


def _doc() -> RigDocument:
    return FX.rig_document(RIG_PATH)


#: The sheet's rows are the rig's clips, in the rig's order (the game reads
#: them by name).
ROWS: List[Tuple[str, int, int]] = _doc().rows()

# --- Effect glyphs (`_creature_fx`), in SVG units like the art ----------------

STREAK = (255, 246, 214, 255)
STREAK_GLOW = (255, 214, 150, 130)


def _paint_claw_swipe(c: FxCanvas) -> None:
    # Three claw streaks curving down and forward, the path of the paw.
    for k in range(3):
        r = 58.0 + k * 10.0
        c.arc((-r * 0.35, -r * 0.55), r, r, 20, 110, STREAK_GLOW, 7.0)
        c.arc((-r * 0.35, -r * 0.55), r, r, 24, 106, STREAK, 2.6)


GLYPHS = FX.Glyphs(
    ART_SCALE,
    {
        **FX.COMMON,
        "claw_swipe": ((90.0, 70.0, 70.0, 40.0), _paint_claw_swipe),
    },
)
_place = GLYPHS.place
_local = GLYPHS.local


def _paw_ground(world, leg: str) -> Point:
    """Where a paw meets the ground under it."""
    wrist = world[f"{leg}_paw"].origin
    return (wrist[0] + 14.0 * ART_SCALE, GROUND_Y - 1.0)


def _front(canvas: FxCanvas, t: float, world, params) -> None:
    swipe = params.get("fx.swipe", 0.0)
    if swipe > 0.02:
        _place(canvas, "claw_swipe", _local(world["near_fore_paw"], 10.0, 0.0), swipe)
    shock = params.get("fx.shock", 0.0)
    if shock > 0.02:
        x, _y = _paw_ground(world, "near_fore")
        _place(canvas, "shock", (x, GROUND_Y), shock)
    dust = params.get("fx.dust", 0.0)
    if dust > 0.02:
        for leg, fade in (("near_fore", 1.0), ("near_hind", 0.8), ("far_fore", 0.6)):
            x, y = _paw_ground(world, leg)
            _place(canvas, "dust", (x - 10.0 * ART_SCALE, y - 1.0), dust * fade)
    hit = params.get("fx.hit", 0.0)
    if hit > 0.02:
        _place(canvas, "hit", _local(world["torso"], 120.0, 10.0), hit)
    thud = params.get("fx.thud", 0.0)
    if thud > 0.02:
        _place(canvas, "thud", (world["pelvis"].origin[0] + 70.0 * ART_SCALE, GROUND_Y - 2.0), thud)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return compose_rig_frame(_doc(), animation, frame_idx, frame_count, front=_front, fx_pieces=True)


FACE = FaceGuide(
    center_x=432.0 * ART_SCALE,
    center_y=224.0 * ART_SCALE,
    width=110.0 * ART_SCALE,
    height=90.0 * ART_SCALE,
    source_width=FRAME_SIZE[0],
    source_height=FRAME_SIZE[1],
)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    """Dialog portraits rerendered from the rig at 6x, never the sheet."""
    del opts
    doc = _doc()

    def portrait_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        source = doc.render_at(animation, doc.frame_time(animation, frame_idx, frame_count), supersample=3, scale=6)
        return render_framed_portrait(source, FACE, view_width=170.0 * ART_SCALE, center_y=228.0 * ART_SCALE)

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 1, 6)),
        "snarling": PortraitClip(
            tuple(portrait_frame("charge", frame, 7) for frame in (0, 1, 2, 3)),
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


__all__ = ["ACTOR_METADATA", "ROWS", "TARGET_BASENAME", "TARGET_NAME", "render", "render_frame", "render_portraits"]


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
