"""The President Portrait: George Washington as the Continental general, facing us as a portrait does.

An SVG rig. The drawing is ``data/characters/president_portrait/president_portrait.svg``
(``scripts/svg_art/president_portrait_art.py``), and the skeleton and the rows are
``rigged/president_portrait/president_portrait.rig.json`` (``scripts/build_president_portrait_rig.py``).

Jon, 2026-10-18, of three redraws: "B for colonial general". He wears the
Continental Army's blue and buff with gold epaulettes and the pale-blue
riband, riding boots, his powdered hair in side rolls, his hand on his sword.
The two other looks (the black-velvet Lansdowne portrait and the dollar-bill
engraving) are drawn by the art script and cast nowhere.

The rows are the seven he has always had: ``idle``, ``walk``, ``address``,
``decree`` (he holds up a proclamation), ``oath`` (his right hand raised, a
book to his heart), ``hurt``, ``death``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "president_portrait"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "president_portrait.rig.json"

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_president_portrait",
        "display_name": "President Portrait",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "locomotion_hint": "Walk",
        "traits": ["hub", "story", "statesman", "speaker"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "fly": None,
            "swim": None,
            "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.address": {"animation": "address", "events": []},
        "interaction.decree": {"animation": "decree", "events": []},
        "interaction.oath": {"animation": "oath", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    # Frame pixels of the 320x352 frame, from the drawing at rest
    # (scripts/svg_art/president_portrait_art.py JOINTS; 0.5 px a unit).
    "sockets": {
        "head": {"source": "president_portrait.geometry", "point": {"x": 160.0, "y": 195.0}},
        "chest": {"source": "president_portrait.geometry", "point": {"x": 160.0, "y": 238.0}},
        "hand_l": {"source": "president_portrait.geometry", "point": {"x": 134.0, "y": 281.0}},
        "hand_r": {"source": "president_portrait.geometry", "point": {"x": 191.0, "y": 269.0}},
        "decree_origin": {"source": "president_portrait.geometry", "point": {"x": 230.0, "y": 230.0}},
        "speech_bubble": {"source": "president_portrait.geometry", "point": {"x": 160.0, "y": 160.0}},
    },
    "tags": ["hub", "static", "story", "statesman", "svg_rigged"],
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
