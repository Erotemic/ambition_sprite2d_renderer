"""User-authored player robot candidate bound to the direct-SVG rig pipeline.

The editable source is
``data/characters/player_robot_candidate_svg/player-robot-candidate-rigged.svg``.
Its current joint markers are intentionally provisional so they can be corrected
in Inkscape and the rig regenerated without changing the target module.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical

TARGET_NAME = "player_robot_candidate_svg"
RIG_PATH = (
    Path(__file__).resolve().parent
    / "rigged/player_robot_candidate_svg/player_robot_candidate_side.rig.json"
)
FRAME_SIZE = (256, 256)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 120),
    ("walk", 8, 95),
    ("run", 8, 75),
    ("jump", 6, 80),
    ("fall", 6, 85),
    ("dash", 6, 62),
    ("attack_side", 7, 62),
    ("attack_up", 6, 68),
    ("air_back", 6, 68),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": TARGET_NAME,
        "display_name": "Player Robot Candidate (SVG)",
    },
    "visual": {"default_pose": "idle"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "LightMedium",
        "traits": ["robot", "player_candidate", "svg_rig"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": False,
            "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": None,
            "trade": None,
            "carry": None,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "player"},
    "actions": {"default_preset": "player"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "locomotion.jump": {"animation": "jump", "events": []},
        "locomotion.fall": {"animation": "fall", "events": []},
        "locomotion.dash": {"animation": "dash", "events": []},
        "action.attack.side": {"animation": "attack_side", "events": []},
        "action.attack.up": {"animation": "attack_up", "events": []},
        "action.attack.air_back": {"animation": "air_back", "events": []},
    },
    "tags": ["robot", "player_candidate", "svg_rig"],
}


@lru_cache(maxsize=1)
def load_doc() -> RigDocument:
    if not RIG_PATH.exists():
        raise FileNotFoundError(
            f"missing rig {RIG_PATH}; rebuild it with "
            "`uv run python scripts/build_player_robot_candidate_svg.py build`"
        )
    return RigDocument.load(RIG_PATH)


def render_frame(animation: str, frame_idx: int, frame_count: int):
    return load_doc().render_frame(animation, frame_idx, frame_count)


def render(out_dir: str | Path, **opts):
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.65},
        animation_key_map={row[0]: row[0] for row in ROWS},
        trim=False,
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


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        render_frame,
        Path(out_dir),
        frame_size=FRAME_SIZE,
    )


__all__ = [
    "ACTOR_METADATA",
    "FRAME_SIZE",
    "ROWS",
    "TARGET_NAME",
    "load_doc",
    "render",
    "render_canonical",
    "render_frame",
]
