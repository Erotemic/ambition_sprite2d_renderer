"""The General: a coat like a box on two legs like sticks, under an officer's peaked cap.

An SVG rig. The drawing is ``data/characters/absurd_general/absurd_general.svg``
(``scripts/svg_art/absurd_general_art.py`` made its first draft), and the
skeleton and the rows are ``rigged/absurd_general/absurd_general.rig.json``
(``scripts/build_absurd_general_rig.py``).

Jon, 2026-10-13, with a picture of a cartoon general for inspiration: "I'm
going for a general specific sort of vibe (although again, we are not copying
the character, this is just inspiration)". Before that day he was a preset of
the toon template, which cannot have these proportions.

The death row ends with the General on his back. The game holds this last
frame for the corpse.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "absurd_general"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "absurd_general.rig.json"

ACTOR_METADATA = {
    # The sheet is `absurd_general`; the character the game shows is `npc_general`.
    "actor": {"character_id": "npc_general", "display_name": "General"},
    "authoring_description": {
        "visual_inspirations": [
            "A cartoon general: a coat like a box, legs like sticks, a nose like a bulb, teeth shut tight.",
            "An officer's peaked cap: a wide crown, a gold strap, a black peak, a gold star badge.",
            "Olive and gold, a red sash, a rack of ribbons, a swagger stick under his arm.",
        ],
        "rigging_notes": [
            "The SVG owns the part shapes. The rig owns the joints and motion.",
            "The cap is a bone of its own, and lags the head a little.",
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["human", "officer", "faction_leader"],
        "locomotion_hint": "Walk",
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.celebrate": {"animation": "celebrate", "events": []},
        "combat.hit": {"animation": "hit", "events": []},
        "life.death": {"animation": "death", "events": []},
    },
    "tags": ["human", "officer", "hub", "faction_leader", "svg_rigged"],
}


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


def INSPECTION() -> dict:
    """List the source clips and the clips selected for publication."""
    rows = [name for name, _, _ in _doc().rows()]
    return {"available": rows, "selected": rows, "visual_family": "svg_rigged"}


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
