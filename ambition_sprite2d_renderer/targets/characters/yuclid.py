"""SVG-rigged sprite target for Yuclid, the Euclid parody boss.

Yuclid is a severe geometer who regards portals as an affront: they skip the
clean path, they bend the plane, and worst of all they let people arrive
without proving how they got there.  He presents as a high-status boss rather
than a generic professor: a laurel wreath on dark curls, a squared
philosopher's beard, a white chiton under a cobalt himation with geometric
gold trim, and an imposing lecture-hall posture.

The SVG ``data/characters/yuclid/yuclid.svg`` owns his art. The rig document
``rigged/yuclid/yuclid_three_quarter.rig.json`` owns his joints and his clips.
Each clip also keys the expression set, the hand pose and the props he holds
(``eyes.*``, ``mouth.*``, ``hand.<side>.*``, ``prop.*``), and the strength of
each effect (``fx.*``). This module owns only the effects and publication.

The combat kit uses the two tools of every Euclidean construction:

* ``straightedge_slam`` cleaves the space with an unmarked golden straightedge;
* ``parallel_banish`` drives out distortions using rigid line-barrages;
* ``postulate_burst`` erupts as a triangle in a square in a circle;
* ``compass_orbit`` cages foes inside pure circles drawn with his compass;
* ``portal_denial`` condemns a portal inside a barred forbidden diagram.

Each effect is a glyph painted once and placed with an opacity, so his part
flipbook stores one raster per glyph, not one per frame.
"""

from __future__ import annotations

import argparse
import math
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

from PIL import Image

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from ._svg_fighter_effects import FxCanvas, compose_rig_frame

Point = Tuple[float, float]
RGBA = Tuple[int, int, int, int]

TARGET_NAME = "yuclid"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "yuclid_three_quarter.rig.json"
FRAME_W = 144
FRAME_H = 144

ACTOR_METADATA = {
    "actor": {"character_id": "npc_yuclid", "display_name": "Yuclid"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "boss",
            "story",
            "humanoid",
            "mathematician",
            "geometer",
            "anti_portal",
            "lecture_duelist",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": True,
            "use_lifts": True,
            "door_access": ["boss", "public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["boss", "public"],
        },
    },
    "brain": {"default_preset": "boss_guard"},
    "actions": {"default_preset": "boss_combat"},
    "visual": {
        "default_pose": "idle",
        "portrait": {
            "face_guide": {
                "center": {"x": 74.0, "y": 31.0},
                "size": {"width": 28.0, "height": 31.0},
                "source_size": {"width": FRAME_W, "height": FRAME_H},
            }
        },
    },
    "tags": [
        "boss",
        "story",
        "humanoid",
        "mathematician",
        "geometer",
        "anti_portal",
        "lecture_duelist",
    ],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 72.0, "y": 29.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 72.0, "y": 69.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 48.0, "y": 84.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 95.0, "y": 82.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 72.0, "y": 7.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "action.melee.primary": {"animation": "straightedge_slam", "events": []},
        "action.ranged.primary": {"animation": "parallel_banish", "events": []},
        "action.special.primary": {"animation": "portal_denial", "events": []},
        "action.special.secondary": {"animation": "compass_orbit", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Yuclid is a stern parody of Euclid, with the name shifted toward 'you' because he "
            "personally enforces the axioms. He treats straightedge geometry as law, rejects portal "
            "shortcuts, and turns definitions, constructions, and the absence of a royal road into "
            "combat doctrine."
        ),
        "gameplay_description": (
            "Use as a geometer, anti-portal boss, construction puzzle master, or exacting lecturer. "
            "His mechanics should create lines and circles, deny non-Euclidean shortcuts, and force "
            "the player to build a valid path from permitted operations."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'You did not walk here. You were placed here.',
        'Between any two points there is one straight line.',
        'There is no royal road to geometry.',
    ],
)

ACTOR_METADATA["tags"].append("svg_rigged")
ACTOR_METADATA["body"]["traits"].append("svg_rigged")
ACTOR_METADATA["visual"]["canonical_source"] = "ambition_sprite2d_renderer/data/characters/yuclid/yuclid.svg"

GOLD = (239, 191, 78, 255)
GOLD_LIGHT = (255, 225, 130, 255)
GOLD_DEEP = (172, 115, 36, 255)
GEO_CYAN = (97, 216, 224, 255)
GEO_VIOLET = (174, 112, 226, 255)
GEO_RED = (224, 100, 96, 255)
PORTAL = (240, 138, 44, 255)
PORTAL_SOFT = (240, 138, 44, 70)


@lru_cache(maxsize=4)
def _load_doc_cached(path_text: str, mtime_ns: int, size: int) -> RigDocument:
    del mtime_ns, size
    return RigDocument.load(path_text)


def _doc() -> RigDocument:
    stat = RIG_PATH.stat()
    return _load_doc_cached(str(RIG_PATH), stat.st_mtime_ns, stat.st_size)


#: The sheet's rows are the rig's clips, in the rig's order (the game reads
#: them by name).
ROWS: List[Tuple[str, int, int]] = _doc().rows()

# --- Effect glyphs -----------------------------------------------------------
#
# Each glyph is painted ONCE at full strength, at the effect canvas's
# supersample, about its own pivot (logical (0, 0)). A frame places it with the
# clip's ``fx.*`` strength as the draw's opacity.

#: ``compose_rig_frame``'s effect supersample for a rig published at 1x.
FX_SCALE = 3

Paint = Callable[[FxCanvas], None]


def _paint_cleave(c: FxCanvas) -> None:
    # A flawless line: the straightedge flares along its whole length.
    c.line([(0, 0), (35, 0)], (255, 225, 130, 110), 4.2)
    c.line([(2, 0), (35, 0)], (255, 248, 214, 255), 1.0)
    c.star((35.5, 0), 3.4, GOLD_LIGHT, points=4)


def _paint_parallel(c: FxCanvas) -> None:
    for y, color, width in ((-7.0, GEO_CYAN, 1.2), (0.0, GOLD_LIGHT, 1.8), (7.0, GEO_CYAN, 1.2)):
        c.line([(0, y), (34, y)], color, width)
        c.line([(30, y - 2.4), (35, y), (30, y + 2.4)], color, width)


def _paint_veto(c: FxCanvas) -> None:
    c.line([(0, -13), (0, 13)], GEO_RED, 1.3)


def _paint_postulate(c: FxCanvas) -> None:
    c.ellipse((0, 0), 10.6, 10.6, None, (97, 216, 224, 150), 0.8)
    c.polygon([(-7.5, -7.5), (7.5, -7.5), (7.5, 7.5), (-7.5, 7.5)], None, GOLD_LIGHT, 1.0)
    c.polygon([(0, -10.6), (-9.2, 5.3), (9.2, 5.3)], None, GEO_CYAN, 1.4)
    c.ellipse((0, 0), 1.2, 1.2, GOLD_LIGHT)


def _paint_compass_ring(c: FxCanvas) -> None:
    c.arc((0, 0), 23.0, 30.0, 130, 320, GEO_CYAN, 1.9)
    c.arc((0, 0), 15.0, 21.0, 305, 100, (255, 225, 130, 190), 1.1)


def _paint_aura(c: FxCanvas) -> None:
    c.arc((0, 0), 19.0, 26.0, 196, 352, GEO_CYAN, 1.8)


def _dot(color: RGBA) -> Paint:
    def paint(c: FxCanvas) -> None:
        c.ellipse((0, 0), 1.8, 1.8, color, (39, 47, 55, 255), 0.4)

    return paint


def _paint_denial(c: FxCanvas) -> None:
    # The portal he refuses: an orange door in the plane, barred and struck out.
    c.ellipse((0, 0), 9.0, 12.5, PORTAL_SOFT, PORTAL, 1.6)
    c.ellipse((0, 0), 15.0, 17.0, None, GEO_VIOLET, 2.0)
    c.ellipse((0, 0), 11.6, 14.6, None, (97, 216, 224, 140), 0.9)
    for x in (-8.0, 0.0, 8.0):
        c.line([(x, -12.0), (x, 12.0)], GOLD, 0.9)
    c.line([(-13.0, 11.0), (13.0, -11.0)], GEO_RED, 2.3)


def _paint_ward(c: FxCanvas) -> None:
    c.arc((0, 0), 13.0, 15.0, 250, 110, GEO_CYAN, 2.2)
    c.arc((0, 0), 9.0, 11.0, 250, 110, (255, 225, 130, 204), 1.0)


def _paint_disdain(c: FxCanvas) -> None:
    c.line([(0, 0), (4, -1.5), (0, 3)], GEO_RED, 1.4)


def _paint_lecture(c: FxCanvas) -> None:
    c.polygon([(-4.0, 3.0), (0.0, -4.0), (4.0, 3.0)], None, GOLD, 0.9)
    c.line([(8.0, -2.0), (13.0, -2.0)], GEO_CYAN, 0.9)
    c.line([(10.5, -4.5), (10.5, 0.5)], GEO_CYAN, 0.9)


def _paint_halo(c: FxCanvas) -> None:
    c.ellipse((0, 0), 17.0, 5.5, None, GOLD_LIGHT, 1.5)


#: name -> (logical half-extent, paint).
GLYPHS: Dict[str, Tuple[float, Paint]] = {
    "cleave": (40.0, _paint_cleave),
    "parallel": (38.0, _paint_parallel),
    "veto": (15.0, _paint_veto),
    "postulate": (13.0, _paint_postulate),
    "compass_ring": (33.0, _paint_compass_ring),
    "aura": (28.0, _paint_aura),
    "dot_gold": (3.0, _dot(GOLD)),
    "dot_cyan": (3.0, _dot(GEO_CYAN)),
    "dot_violet": (3.0, _dot(GEO_VIOLET)),
    "denial": (19.0, _paint_denial),
    "ward": (17.0, _paint_ward),
    "disdain": (6.0, _paint_disdain),
    "lecture": (15.0, _paint_lecture),
    "halo": (19.0, _paint_halo),
}


@lru_cache(maxsize=None)
def _glyph(name: str) -> Tuple[Image.Image, Point]:
    """The glyph's raster and its pivot, in effect-canvas pixels."""
    half, paint = GLYPHS[name]
    side = int(math.ceil(half * 2))
    canvas = FxCanvas((side, side), scale=FX_SCALE, origin=(half, half))
    paint(canvas)
    return canvas.image, (half * FX_SCALE, half * FX_SCALE)


def _place(canvas: FxCanvas, name: str, at: Point, opacity: float, degrees: float = 0.0) -> None:
    if opacity > 0.02:
        canvas.place(_glyph(name), at, degrees, min(1.0, opacity), name=name)


def _hand(world, side: str) -> Point:
    """The middle of a hand: a little past the wrist along the hand."""
    return world[f"{side}_arm_hand"].to_world((3.0, 0.0))


def _behind(canvas: FxCanvas, t: float, world, params) -> None:
    orbit = params.get("fx.orbit", 0.0)
    if orbit > 0.02:
        center = (72.0, 70.0)
        _place(canvas, "compass_ring", center, orbit)
        angle = orbit * 280.0
        for radius, dot, phase in ((23.0, "dot_gold", 0.0), (18.0, "dot_cyan", 110.0), (15.5, "dot_violet", 220.0)):
            rad = math.radians(angle + phase)
            _place(canvas, dot, (center[0] + math.cos(rad) * radius, center[1] + math.sin(rad) * radius * 0.78), orbit)
    _place(canvas, "aura", (72.0, 69.0), params.get("fx.aura", 0.0))
    _place(canvas, "denial", (112.0, 52.0), params.get("fx.denial", 0.0))
    burst = params.get("fx.burst", 0.0)
    if burst > 0.02:
        hand = _hand(world, "near")
        _place(canvas, "postulate", (hand[0] + 14.0, hand[1] - 8.0), burst * 0.9, degrees=burst * 30.0)


def _front(canvas: FxCanvas, t: float, world, params) -> None:
    hand = _hand(world, "near")
    edge = params.get("fx.straightedge", 0.0)
    if edge > 0.6 and params.get("prop.straightedge", 0.0) > 0.5:
        # The cleave flares along the straightedge held in the fist.
        grip = world["near_arm_hand"]
        _place(canvas, "cleave", grip.origin, (edge - 0.6) * 2.5, degrees=grip.angle)
    parallel = params.get("fx.parallel", 0.0)
    if parallel > 0.02:
        _place(canvas, "parallel", (hand[0] - 1.0, hand[1]), parallel)
        _place(canvas, "veto", (hand[0] + 9.0, hand[1]), params.get("fx.denial", 0.0))
    _place(canvas, "ward", (hand[0] + 8.0, hand[1] - 1.0), params.get("fx.block", 0.0))
    head = world["head"]
    head_center = head.to_world((14.0, 0.0))
    _place(canvas, "disdain", (head_center[0] + 13.0, head_center[1] - 2.0), params.get("fx.disdain", 0.0))
    _place(canvas, "lecture", (hand[0] + 11.0, hand[1] - 17.0), params.get("fx.glyphs", 0.0))
    _place(canvas, "halo", head.to_world((21.0, 0.0)), params.get("fx.halo", 0.0), degrees=head.angle + 90.0)


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


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    del opts
    doc = _doc()
    face = FaceGuide(
        center_x=74.0,
        center_y=31.0,
        width=28.0,
        height=31.0,
        source_width=FRAME_W,
        source_height=FRAME_H,
    )

    def portrait_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        source = doc.render_at(animation, doc.frame_time(animation, frame_idx, frame_count), supersample=4, scale=4)
        return render_framed_portrait(source, face, view_width=58.0, center_y=37.0)

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 1, 8)),
        "lecturing": PortraitClip(
            tuple(portrait_frame("talk", frame, 8) for frame in range(8)),
            duration_ms=104,
            looping=True,
        ),
        "disdain": PortraitClip(
            tuple(portrait_frame("taunt", frame, 8) for frame in (1, 3, 5, 7)),
            duration_ms=118,
            looping=True,
        ),
        "condemning": PortraitClip(
            tuple(portrait_frame("portal_denial", frame, 12) for frame in (2, 4, 6, 8, 10)),
            duration_ms=88,
            looping=True,
        ),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {"x": int(fw * 0.24), "y": int(fh * 0.09), "w": int(fw * 0.57), "h": int(fh * 0.84)},
        "feet_pixel": {"x": fw * 0.52, "y": fh * 0.92},
        "feet_anchor_norm": {"x": 0.01, "y": round(0.5 - 0.92, 6)},
    }


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
        label_width=112,
        auto_crop=False,
        body_metrics_fn=_body_metrics_override,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.0, "frame_sample_inset": 1},
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        attack_hitboxes={
            "straightedge_slam": {"bbox": {"x": 86, "y": 50, "w": 52, "h": 32}},
            "parallel_banish": {"bbox": {"x": 84, "y": 42, "w": 48, "h": 38}},
            "portal_denial": {"bbox": {"x": 90, "y": 26, "w": 44, "h": 45}},
            "postulate_burst": {"bbox": {"x": 83, "y": 37, "w": 40, "h": 35}},
            "compass_orbit": {"bbox": {"x": 44, "y": 31, "w": 62, "h": 62}},
        },
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=(FRAME_W, FRAME_H))


__all__ = ["ACTOR_METADATA", "ROWS", "TARGET_NAME", "render", "render_canonical", "render_frame", "render_portraits"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir", nargs="?", type=Path, default=Path("generated") / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
