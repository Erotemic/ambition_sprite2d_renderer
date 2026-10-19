"""Captain Pulse: Claude's own redesign of the v2 robot, in the Pulse Voyagers' colours.

An SVG rig. The drawing is ``data/characters/pulse_voyager_captain/pulse_voyager_captain.svg``
(``scripts/svg_art/pulse_voyager_captain_art.py``), and the skeleton and the
rows are ``rigged/pulse_voyager_captain/pulse_voyager_captain.rig.json``
(``scripts/build_pulse_voyager_captain_rig.py``).

Jon, 2026-10-18: "if I had to ask you to redesign the main character what
would it look like?", then "refine that and then use that to replace a
different robot character (captain something?)", and on 2026-10-19 "finish
captain pulse." Before, he was a preset of the robot template, which the
faction lineup drew in the Pulse Voyagers' colours.

The rows are the eight he has always had: ``idle``, ``walk``, ``run``,
``talk``, ``dash``, ``celebrate``, ``hit``, ``death``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "pulse_voyager_captain"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "pulse_voyager_captain.rig.json"

ACTOR_METADATA = {
    # The sheet is `pulse_voyager_captain`; the character the game shows is `npc_pulse_voyager_captain`.
    "actor": {"character_id": "npc_pulse_voyager_captain", "display_name": "Captain Pulse"},
    "authoring_description": {
        "visual_inspirations": [
            "The v2 robot rebuilt: a box head with a dark visor and oval cyan eyes, a light muzzle, one rigid antenna.",
            "White shell plates over a dark jointed suit; a navy hull with a comet badge, gold shoulder boards.",
            "Swept winglets at the ear and the heels, and a comet trail when he runs or dashes.",
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
        "locomotion.run": {"animation": "run", "events": []},
        "locomotion.dash": {"animation": "dash", "events": []},
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
