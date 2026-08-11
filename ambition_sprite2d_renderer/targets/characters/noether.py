"""Canonical SVG-rigged fighter target for Noether.

``assets/noether.svg`` is the art, z-order, joint, and source-view authority.
The generated rig owns natural pose, IK anatomy, skirt secondary motion, and
fighter clips. The source SVG is never rewritten by this target or its builder.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.canonical_scientist_rig import load_scientist_rig
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from .noether_motion import FIGHTER_MOTION_COVERAGE, NOETHER_ROWS

TARGET_NAME = "noether"
RIG_FRAME_SIZE = (192, 208)
RIG_RENDER_PADDING = 28
FRAME_SIZE = (
    RIG_FRAME_SIZE[0] + RIG_RENDER_PADDING * 2,
    RIG_FRAME_SIZE[1] + RIG_RENDER_PADDING * 2,
)
ROWS: List[Tuple[str, int, int]] = list(NOETHER_ROWS)

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_noether",
        "display_name": "Emmy No-Ether",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "special_character",
            "humanoid",
            "noether",
            "classification_fighter",
            "playable_candidate",
            "svg_rigged",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": True,
            "swim": True,
            "crawl": True,
            "use_lifts": True,
        },
        "interactions": {
            "talk": True,
            "carry": True,
        },
    },
    "visual": {
        "default_pose": "idle",
        "canonical_source": "assets/noether.svg",
    },
    "actions": {"default_preset": "noether"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "generator_strike", "events": []},
        "action.special.primary": {"animation": "conservation_law", "events": []},
        "action.special.secondary": {"animation": "symmetry_shift", "events": []},
        "action.special.up": {"animation": "ethereal_lift", "events": []},
        "action.special.down": {"animation": "invariant_field", "events": []},
        "action.super": {"animation": "noether_theorem", "events": []},
        "action.defense.parry": {"animation": "invariant_parry", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "authoring_description": (
        "A Noether-inspired fighter whose visual and mechanical language centers on "
        "symmetry, invariants, conservation laws, and an ethereal transformation motif. "
        "The canonical side-view paper doll is manually traced in assets/noether.svg; "
        "generated rig data must not rewrite that source artwork."
    ),
    "gameplay_description": (
        "A technical medium-weight fighter using symmetry transformations and conserved "
        "quantities for spacing, reversals, and control. Her up special is an ethereal "
        "lift/recovery, while the three-panel dress uses restrained rigid secondary "
        "motion rather than cloth simulation."
    ),
}


def _doc() -> RigDocument:
    return load_scientist_rig(TARGET_NAME)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return _doc().render_frame(
        animation,
        frame_idx,
        frame_count,
        padding=RIG_RENDER_PADDING,
    )


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning or {"collision_scale": 1.86},
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        trim=True,
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
    "FIGHTER_MOTION_COVERAGE",
    "ROWS",
    "TARGET_NAME",
    "render",
    "render_canonical",
    "render_frame",
]
