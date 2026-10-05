"""SVG-rigged boss chest: the big-item chest, royal blue and gold on lion-claw feet.

The chest a boss leaves, or that holds a key item: deep blue lacquered panels
in a gold frame set with jewelled lozenges, a gold-ribbed domed lid bearing a
crowned medallion, a great shield lock set with a ruby, lion-claw feet, red
velvet lining. Bigger than ``treasure_chest`` (a 160 px frame at the same
pixels per drawing unit) and drawn the same way: from the front and a little
above, the lid a swap set hinged at the box's back edge.

The SVG ``data/props/boss_chest/boss_chest.svg`` owns the art and marks every
joint; the rig document ``rigged/boss_chest/boss_chest.rig.json`` owns the
skeleton and the clips, which ``scripts/build_boss_chest_rig.py`` derives (the
``chest`` anatomy) and authors. This module owns only the effects and
publication.

Rows:

- ``closed``: shut (one frame);
- ``opening``: the ruby in the lock wakes, the chest shudders and heaves,
  the lock falls loose, light cracks round the lid and the lid is flung back
  in a burst of light that dies away (once);
- ``open``: open and empty (one frame).

The chest is empty: an item placed at runtime anchors on the ``item`` socket
(the middle of the box's mouth) and layers between the box's interior and
its front (above z 10, below z 25), so the front hides the item's lower part.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from ..characters import _creature_fx as FX
from ..characters._svg_fighter_effects import FxCanvas, compose_rig_frame
from . import _chest_fx as CHEST_FX

TARGET_NAME = "boss_chest"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "boss_chest.rig.json"
FRAME_SIZE = (160, 160)
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``).
ART_SCALE = 0.25


def _px(x: float, y: float) -> Dict[str, float]:
    """A point of the drawing (SVG units) as a sprite-frame point."""
    return {"x": round(x * ART_SCALE, 1), "y": round(y * ART_SCALE, 1)}


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Boss Chest"},
    "body": {
        "body_plan": "Prop",
        "body_kind": "Device",
        "locomotion_hint": "Stationary",
        "traits": ["prop", "chest", "reward", "boss_reward", "interactable", "svg_rigged"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "closed", "events": []},
        "state.closed": {"animation": "closed", "events": []},
        "interact.open": {
            "animation": "opening",
            "events": [
                {"t": 0.38, "event": "unlock", "source": TARGET_NAME},
                {"t": 0.62, "event": "lid_open", "source": TARGET_NAME},
                {"t": 0.62, "event": "reward_spawn", "source": TARGET_NAME},
            ],
        },
        "state.open": {"animation": "open", "events": []},
    },
    # Points on the drawn frame (before the sheet's auto-crop).
    "sockets": {
        "lock": {"source": f"{TARGET_NAME}.geometry", "point": _px(320.0, 430.0)},
        "item": {"source": f"{TARGET_NAME}.geometry", "point": _px(320.0, 372.0)},
        "base": {"source": f"{TARGET_NAME}.geometry", "point": _px(320.0, 600.0)},
    },
    "visual": {
        "default_pose": "closed",
        "canonical_source": "ambition_sprite2d_renderer/data/props/boss_chest/boss_chest.svg",
    },
    "tags": ["prop", "chest", "reward", "boss_reward", "animated", "svg_rigged"],
}


def _doc() -> RigDocument:
    return FX.rig_document(RIG_PATH)


ROWS: List[Tuple[str, int, int]] = _doc().rows()

# --- Effect glyphs (`_creature_fx`, `_chest_fx`) ------------------------------------


def _paint_gem(c: FxCanvas) -> None:
    """The ruby waking: a red halo and a white glint."""
    for r, alpha in ((40, 40), (28, 70), (18, 110)):
        c.ellipse((0, 0), r, r * 0.9, (255, 60, 90, alpha))
    c.star((0, 0), 30.0, (255, 236, 240, 255), points=4, inner=0.18, rotation=0)


#: The light glyphs are the treasure chest's, drawn this much bigger to
#: match the bigger box (their sizes are in the treasure chest's units).
LIGHT_SCALE = 1.3
LIGHTS = FX.Glyphs(ART_SCALE * LIGHT_SCALE, {**FX.COMMON, **CHEST_FX.GLYPHS})
GEMS = FX.Glyphs(ART_SCALE, {"gem": ((42.0, 38.0, 42.0, 38.0), _paint_gem)})


def _local(bone, x: float, y: float):
    """A point in a bone's frame given in the drawing's SVG units."""
    return bone.to_world((x * ART_SCALE, y * ART_SCALE))


#: In the box's frame (SVG units from its bottom centre): the opening's
#: middle, the crack under a lifted lid, and where sparkles catch the rim.
MOUTH = (0.0, -204.0)
CRACK = (0.0, -186.0)
SPARKLES = ((-120.0, -200.0, 0.0), (112.0, -210.0, 0.35), (0.0, -236.0, 0.7), (-60.0, -186.0, 0.5),
            (70.0, -194.0, 0.15))


def _front(canvas: FxCanvas, t: float, world, params) -> None:
    base = world["base"]
    mouth = _local(base, *MOUTH)
    LIGHTS.place(canvas, "glow", mouth, params.get("fx.glow", 0.0))
    LIGHTS.place(canvas, "rays", _local(base, 0.0, -196.0), params.get("fx.rays", 0.0))
    LIGHTS.place(canvas, "leak", _local(base, *CRACK), params.get("fx.leak", 0.0))
    LIGHTS.place(canvas, "burst", mouth, params.get("fx.burst", 0.0) * 0.85)
    lock = world["lock"]
    # The lock bone runs down the plate: the ruby sits 28 units down it.
    GEMS.place(canvas, "gem", _local(lock, 28.0, 0.0), params.get("fx.gem", 0.0))
    LIGHTS.place(canvas, "click", _local(lock, 4.0, 0.0), params.get("fx.click", 0.0))
    dust = params.get("fx.dust", 0.0)
    LIGHTS.place(canvas, "dust", _local(base, -176.0, 26.0), dust)
    LIGHTS.place(canvas, "dust", _local(base, 176.0, 26.0), dust)
    sparkle = params.get("fx.sparkle", 0.0)
    if sparkle > 0.02:
        for x, y, offset in SPARKLES:
            w = 0.5 + 0.5 * math.sin(math.tau * (t * 3.0 + offset))
            LIGHTS.place(canvas, "sparkle", _local(base, x, y), sparkle * w)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return compose_rig_frame(_doc(), animation, frame_idx, frame_count, front=_front, fx_pieces=True)


# ---- Target registration hooks ------------------------------------------------


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
        actor_metadata=ACTOR_METADATA,
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, out_dir)
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[k]) for k in keys if outputs.get(k)] + list(parts.values())


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir))


__all__ = ["ACTOR_METADATA", "ROWS", "SHEET_FILES", "TARGET_NAME", "render", "render_canonical", "render_frame"]
