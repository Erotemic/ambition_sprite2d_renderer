"""Publish the SVG and bone rig for a four-legged companion dog."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "companion_dog"
RIG_PATH = (
    Path(__file__).resolve().parent
    / "rigged"
    / TARGET_NAME
    / "companion_dog_side.rig.json"
)

ACTOR_METADATA = {
    "actor": {"character_id": "npc_companion_dog", "display_name": "Companion Dog"},
    "authoring_description": {
        "visual_inspirations": [
            "A domestic dog with four legs, a long muzzle, a floppy ear, and a wagging tail.",
            "A collar marks the dog as a companion.",
        ],
        "rigging_notes": [
            "The SVG owns the part shapes. The rig owns the joints and motion.",
            "Each leg has an upper part, a lower part, and a paw.",
        ],
    },
    "body": {
        "body_plan": "Quadruped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": ["animal", "dog", "quadruped", "no_hands", "companion"],
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
        "interactions": {
            "talk": None,
            "trade": None,
            "carry": None,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "companion_dog_roam"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle"},
    "sockets": {
        "head": {"source": "companion_dog.rig", "point": {"x": 126.0, "y": 55.0}},
        "muzzle": {"source": "companion_dog.rig", "point": {"x": 151.0, "y": 62.0}},
        "back": {"source": "companion_dog.rig", "point": {"x": 84.0, "y": 54.0}},
        "tail_tip": {"source": "companion_dog.rig", "point": {"x": 36.0, "y": 41.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "locomotion.jump": {"animation": "jump", "events": []},
        "interaction.use": {"animation": "happy", "events": []},
        "interaction.talk": {"animation": "sit_idle", "events": []},
        "vocalization.bark": {"animation": "bark", "events": []},
        "life.death": {"animation": "death", "events": []},
    },
    "tags": ["animal", "dog", "quadruped", "companion", "svg_rigged"],
}


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return _doc().render_frame(animation, frame_idx, frame_count)


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=doc.rows(),
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=(168, 168),
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning,
    )
    keys = (
        "spritesheet",
        "yaml",
        "ron",
        "actor",
        "canonical",
        "canonical_transparent",
        "preview",
    )
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


__all__ = ["ACTOR_METADATA", "render"]
