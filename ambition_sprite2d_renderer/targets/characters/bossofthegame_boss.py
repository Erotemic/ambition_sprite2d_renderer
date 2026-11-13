"""The bossofthegame: the final boss, a developer in a hoodie and a paper crown with a keyboard on a strap.

An SVG rig. The drawing is ``data/characters/bossofthegame/bossofthegame.svg``
(``scripts/svg_art/bossofthegame_art.py``), and the skeleton and the rows are
``rigged/bossofthegame/bossofthegame.rig.json``
(``scripts/build_bossofthegame_rig.py``).

The game's design: ``docs/planning/game/final-boss.md``. He stands on the
shoulders of Full Stack (``full_stack_giant``). The sheet is a boss sheet: its
first six rows are the boss slots (``rest``, ``floor_slam``, ``side_sweep``,
``spike_halo``, ``hit``, ``death``), in that order (the game's
``boss_sheets.ron``), then ``talk``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "bossofthegame_boss"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / "bossofthegame" / "bossofthegame.rig.json"

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_bossofthegame",
        "display_name": "bossofthegame",
        "actor_id": "bossofthegame",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "boss", "final_boss"],
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
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "rest"},
    "tags": ["story", "humanoid", "boss", "final_boss"],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 97.2, "y": 63.9}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 93.0, "y": 101.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 97.2, "y": 30.0}},
    },
    "animation_bindings": {
        "default": {"animation": "rest", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
    },
    "missing_information": [
        "His fight is authored by the game (boss_profiles.ron, bossofthegame); "
        "the renderer draws his rows only."
    ],
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
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, doc.rows(), _render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "render"]
