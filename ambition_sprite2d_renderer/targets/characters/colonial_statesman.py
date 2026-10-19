"""The Colonial Statesman: a Federalist orator in a bottle-green coat, his speech in hand, a rapier at his hip.

An SVG rig. The drawing is ``data/characters/colonial_statesman/colonial_statesman.svg``
(``scripts/svg_art/colonial_statesman_art.py``), and the skeleton and the rows are
``rigged/colonial_statesman/colonial_statesman.rig.json`` (``scripts/build_colonial_statesman_rig.py``).

Jon, 2026-10-18, of three redraws: "A for statesmen". He was a recolour of
the President's body, facing us; he now stands in the cast's side view,
facing right: slim, a bottle-green coat over a buff waistcoat and breeches,
powdered hair in a queue with a black bow, his twelve-page speech in hand. The
two other looks (a stout royal governor in claret, a tricorn duelist in
charcoal) are drawn by the art script and cast nowhere.

The rows are the seven he has always had: ``idle``, ``walk``, ``address``,
``thrust`` (he draws his rapier and lunges), ``pistol`` (he draws a flintlock
and fires), ``hurt``, ``death``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "colonial_statesman"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "colonial_statesman.rig.json"

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_colonial_statesman",
        "display_name": "Colonial Statesman",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "story", "statesman"],
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
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle"},
    "tags": ["story", "humanoid", "story", "statesman", "svg_rigged"],
    # Frame pixels of the 320x352 frame, from the drawing at rest
    # (scripts/svg_art/colonial_statesman_art.py JOINTS; 0.5 px a unit).
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 166.0, "y": 190.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 167.0, "y": 235.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 159.0, "y": 279.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 175.0, "y": 252.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 166.0, "y": 163.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
    },
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
