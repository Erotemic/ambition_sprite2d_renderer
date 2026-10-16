"""The attack hound of Castle Godwin: a lean guard dog of the regime.

A dark dog like a German shepherd, with its hackles up and its teeth bared,
and a spiked collar with the red tag of the regime (``_evil_faction``). It
comes in low and fast with the soldiers.

The drawing is ``data/characters/evil_attack_hound/evil_attack_hound_side.svg``
(``scripts/svg_art/evil_attack_hound_art.py``). The bones are the companion
dog's, with longer legs and a lower jaw that turns; the clips are the
hound's own (``scripts/build_evil_attack_hound_rig.py``).

``slash`` is the snapping bite. ``attack_side`` is the long leaping lunge.
``taunt`` is barking.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "evil_attack_hound"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / f"{TARGET_NAME}_side.rig.json"

#: The body, in frame pixels (x0, y0, x1, y1): the alpha box of the first
#: frame of ``idle`` with no tail. The ears are of the body, as for the house
#: dogs. The bottom edge is the ground line of the paws.
BODY_BOX = (68.0, 41.0, 178.0, 143.0)

ACTOR_METADATA = {
    "actor": {"character_id": "npc_evil_attack_hound", "display_name": "Attack Hound"},
    "authoring_description": {
        "visual_inspirations": [
            "A lean guard dog like a German shepherd: a black saddle on a dark rust coat, tall ears turned forward.",
            "The hackles up, an amber eye under a low brow, the lip pulled up off the teeth.",
            "A black collar with steel spikes and a red stripe; a red tag with the mark of the regime.",
        ],
        "rigging_notes": [
            "The SVG owns the part shapes. The bones are the companion dog's, with a jaw that turns.",
            "slash is the snapping bite; attack_side is the long leaping lunge; taunt is barking.",
        ],
    },
    "body": {
        "body_plan": "Quadruped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": ["animal", "dog", "quadruped", "no_hands", "enemy", "evil"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "crawl": None,
            "fly": None,
            "swim": None,
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {"talk": None, "trade": None, "carry": None, "open_doors": []},
    },
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "striker_swipe"},
    "visual": {"default_pose": "idle"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "locomotion.jump": {"animation": "jump", "events": []},
        "locomotion.fall": {"animation": "fall", "events": []},
        "attack.bite": {"animation": "slash", "events": []},
        "attack.lunge": {"animation": "attack_side", "events": []},
        "vocalization.bark": {"animation": "taunt", "events": []},
        "reaction.hit": {"animation": "hit", "events": []},
        "life.death": {"animation": "death", "events": []},
    },
    "tags": ["animal", "dog", "quadruped", "enemy", "evil", "svg_rigged"],
}


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return _doc().render_frame(animation, frame_idx, frame_count)


def _body_metrics(fw: int, fh: int) -> dict:
    x0, y0, x1, y1 = BODY_BOX
    x, y, w, h = int(x0), int(y0), int(x1 - x0), int(y1 - y0)
    feet = (x + w / 2.0, float(y + h))
    return {
        "body_pixel_bbox": {"x": x, "y": y, "w": w, "h": h},
        "feet_pixel": {"x": feet[0], "y": feet[1]},
        "feet_anchor_norm": {"x": round((feet[0] - fw / 2.0) / fw, 6), "y": round((fh / 2.0 - feet[1]) / fh, 6)},
    }


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    frame = doc.data["frame"]
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=doc.rows(),
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=(int(frame["width"]), int(frame["height"])),
        # The frame is authored, so the body box is in its pixels.
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        body_metrics_fn=_body_metrics,
        sheet_tuning=doc.sprite_tuning,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, doc.rows(), _render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "BODY_BOX", "render"]
