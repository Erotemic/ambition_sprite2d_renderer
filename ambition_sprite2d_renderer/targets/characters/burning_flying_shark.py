"""SVG-rigged sprite target for the burning flying shark, the pirates' sky-mount.

A great shark that burns from the inside: charred gunmetal skin split by
glowing magma cracks, fins whose trailing edges smoulder orange, an amber eye
that rolls back under its membrane when it bites, and fire streaming from its
dorsal fin, pectoral fins and tail. It is tacked up for a rider: a red saddle
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
# Flames are authored pointing along +x from their base: a red-orange tongue,
# an orange body, a yellow heart and a pale core, in three flicker shapes and
# two lengths. Each is placed on a drawn feature and turned with its bone.

FLAME_LAYERS = (
    ((232, 70, 22, 205), 1.0),
    ((255, 140, 36, 230), 0.72),
    ((255, 214, 92, 240), 0.46),
    ((255, 248, 214, 255), 0.22),
)


def _flame(length: float, width: float, flicker: int):
    sway = (0.0, 0.18, -0.16)[flicker]
    lick = (1.0, 0.9, 1.08)[flicker]

    def paint(c: FxCanvas) -> None:
        for color, k in FLAME_LAYERS:
            L, w = length * k * lick, width * (0.4 + 0.6 * k)
            # A round root, a body that narrows, a tip that licks to one side.
            pts = [(-0.18 * L, 0.0), (-0.1 * L, -0.42 * w), (0.12 * L, -0.5 * w), (0.4 * L, -0.36 * w),
                   (0.7 * L, (-0.16 + sway * 0.6) * w), (L, sway * w), (0.74 * L, (0.1 + sway * 0.5) * w),
                   (0.46 * L, 0.3 * w), (0.16 * L, 0.48 * w), (-0.1 * L, 0.42 * w)]
            c.polygon(pts, color)

    return paint


def _paint_ember(c: FxCanvas) -> None:
    c.ellipse((0, 0), 4.5, 4.5, (255, 140, 36, 150))
    c.ellipse((0, 0), 2.2, 2.2, (255, 236, 160, 255))


def _paint_speed(c: FxCanvas) -> None:
    for y, length in ((-34, 70), (0, 110), (30, 80)):
        c.line([(0, y), (length, y)], (255, 246, 214, 120), 3.0)


_GLYPHS: Dict[str, Tuple[FX.Extent, FX.Paint]] = {**FX.COMMON}
for _k in range(3):
    _GLYPHS[f"flame{_k}"] = ((12.0, 16.0, 56.0, 16.0), _flame(48.0, 26.0, _k))
    _GLYPHS[f"flame_big{_k}"] = ((16.0, 20.0, 80.0, 20.0), _flame(70.0, 32.0, _k))
_GLYPHS["ember"] = ((6.0, 6.0, 6.0, 6.0), _paint_ember)
_GLYPHS["speed"] = ((4.0, 38.0, 114.0, 34.0), _paint_speed)
GLYPHS = FX.Glyphs(ART_SCALE, _GLYPHS)
_place = GLYPHS.place
_local = GLYPHS.local

REST = FX.rest_frames(_doc())

#: Where the fire burns: (bone, a drawn point on it in SVG units, the flame's
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
_ANCHORS = [FX.anchor(REST, bone, point, ART_SCALE) for bone, point, _deg, _phase in FLAMES]


def _behind(canvas: FxCanvas, t: float, world, params) -> None:
    flame = params.get("fx.flame", 0.0)
    flare = params.get("fx.flare", 0.0)
    if params.get("fx.speed", 0.0) > 0.02:
        body = world["body"]
        _place(canvas, "speed", _local(body, -130.0, -10.0), params["fx.speed"], degrees=body.angle + 180.0)
    if flame > 0.02:
        step = int(round(t * 24))
        for i, ((bone, _point, deg, phase), local) in enumerate(zip(FLAMES, _ANCHORS)):
            bw = world[bone]
            turn = bw.angle - REST[bone][1]
            wobble = 8.0 * math.sin(math.tau * t * 2.0 + phase)
            name = f"{'flame_big' if flare > 0.5 else 'flame'}{(step + i) % 3}"
            opacity = flame * (0.82 + 0.18 * math.cos(math.tau * t * 3.0 + phase))
            _place(canvas, name, bw.to_world(local), opacity, degrees=deg + turn + wobble)
        # Embers shed behind the tail.
        tail = world["fluke"].to_world((0.0, 0.0))
        for k in range(5):
            u = (t * 2.0 + k / 5.0) % 1.0
            x = tail[0] - (20.0 + 150.0 * u) * ART_SCALE
            y = tail[1] + (math.sin(k * 2.1 + u * 6.0) * 40.0 - 30.0 * u) * ART_SCALE
            _place(canvas, "ember", (x, y), flame * (1.0 - u))


def _front(canvas: FxCanvas, t: float, world, params) -> None:
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
