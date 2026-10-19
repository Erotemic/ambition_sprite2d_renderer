"""Chadwick Disruptor III: a white gadget robot in a fleece vest, eyes on his phone.

An SVG rig. The drawing is ``data/characters/tech_bro_disruptor/tech_bro_disruptor.svg``
(look A, ``founder``, of ``scripts/svg_art/chadwick/chadwick_robot_drafts.py``),
and the skeleton and the rows are ``rigged/tech_bro_disruptor/tech_bro_disruptor.rig.json``
(``scripts/build_tech_bro_disruptor_rig.py``).

Jon, 2026-10-18: "I also want you to redesign Chadwick", "Chadwick is a
robot", and of the robot drafts, "We can actually use variant A for
chadwick". Before that day he was a preset of the robot template, which the
faction lineup drew in the Tech-Bros' colours.

The rows are the eight he has always had: ``idle``, ``walk``, ``talk``,
``charge``, ``cast``, ``celebrate``, ``hit``, ``death``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "tech_bro_disruptor"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "tech_bro_disruptor.rig.json"

ACTOR_METADATA = {
    # The sheet is `tech_bro_disruptor`; the character the game shows is `npc_tech_bro_disruptor`.
    "actor": {"character_id": "npc_tech_bro_disruptor", "display_name": "Chadwick Disruptor III"},
    "authoring_description": {
        "visual_inspirations": [
            "A white gadget robot: a round helmet head, a black visor with smug neon pixel eyes, an earbud for an ear.",
            "A founder's uniform: a grey quilted fleece vest, a lanyard and badge, white sneakers with neon soles.",
            "Always on his phone, its screen a graph going up.",
        ],
        "rigging_notes": [
            "The SVG owns the part shapes. The rig owns the joints and motion.",
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["robot", "faction_leader"],
        "locomotion_hint": "Walk",
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "emote.celebrate": {"animation": "celebrate", "events": []},
        "combat.hit": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
    "tags": ["robot", "hub", "faction_leader", "svg_rigged"],
}


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return _doc().render_frame(animation, frame_idx, frame_count)


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=doc.rows(),
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=(int(doc.data["frame"]["width"]), int(doc.data["frame"]["height"])),
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, doc.rows(), _render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "render"]
