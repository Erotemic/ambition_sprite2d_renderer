"""Dedicated full-fighter target for the Perfect Cellular Automaton (PCA).

The hand-drawn SVG + extracted rig remain the character-art authority.  This
module supplies the Smash-facing publication contract: bespoke combat clip
refinements, code-authored cellular effects, authored body/hurt/hit geometry,
and per-frame anchors.  Nothing rewrites the SVG.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from ._svg_fighter_effects import compose_rig_frame
from .pca_combat_authoring import author_pca_combat_clips
from .pca_effects import draw_pca_behind, draw_pca_front
from .pca_gameplay import (
    ATTACK_HITBOXES,
    PADDING,
    PCA_MOVE_BLUEPRINT,
    RENDER_SCALE,
    RIG_SIZE,
    body_metrics as authored_body_metrics,
    hurtbox_parts_for_rows,
)
from .pca_motion import FIGHTER_MOTION_COVERAGE, PCA_ROWS

TARGET_NAME = "perfect_cellular_automaton"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / "perfect_cellular_automaton.rig.json"
ROWS: List[Tuple[str, int, int]] = list(PCA_ROWS)
FRAME_SIZE = (
    (RIG_SIZE[0] + 2 * PADDING) * RENDER_SCALE,
    (RIG_SIZE[1] + 2 * PADDING) * RENDER_SCALE,
)


def _doc() -> RigDocument:
    doc = RigDocument.load(RIG_PATH)
    author_pca_combat_clips(doc.data)
    missing = [name for name, _frames, _duration in ROWS if name not in doc.clips]
    if missing:
        raise RuntimeError(
            "PCA rig is missing full-fighter clips: "
            + ", ".join(missing[:12])
            + (" ..." if len(missing) > 12 else "")
            + "; run targets/characters/rigged/pca_rig_extract.py build"
        )
    return doc


def _actor_metadata(doc: RigDocument) -> dict:
    metadata = deepcopy(doc.data.get("actor_metadata") or {})
    metadata.setdefault("actor", {})
    metadata["actor"].update(
        {
            "character_id": TARGET_NAME,
            "display_name": "Perfect Cellular Automaton",
        }
    )
    metadata.setdefault("body", {})
    metadata["body"].setdefault("body_plan", "HumanoidBiped")
    metadata["body"].setdefault("body_kind", "Standard")
    metadata["body"].setdefault("mass_class", "MediumHeavy")
    traits = list(metadata["body"].get("traits") or [])
    for trait in (
        "cellular_automaton",
        "classification_fighter",
        "playable_candidate",
        "svg_rigged",
    ):
        if trait not in traits:
            traits.append(trait)
    metadata["body"]["traits"] = traits
    metadata.setdefault("visual", {})
    metadata["visual"].update(
        {
            "default_pose": "idle",
            "canonical_source": "assets/perfect-cellular-automaton/PCA-multiview.svg",
            "facing_policy": "front_right_faces_positive_x",
        }
    )
    metadata.setdefault("actions", {})
    metadata["actions"].update(
        {
            "default_preset": TARGET_NAME,
            "authored_moves": PCA_MOVE_BLUEPRINT,
        }
    )
    return metadata


def _out_point(point) -> dict:
    return {
        "x": round((float(point[0]) + PADDING) * RENDER_SCALE, 3),
        "y": round((float(point[1]) + PADDING) * RENDER_SCALE, 3),
    }


def frame_meta(animation: str, frame_idx: int, frame_count: int) -> dict:
    doc = _doc()
    t = doc.frame_time(animation, frame_idx, frame_count)
    world, _params = doc.solve(animation, t)

    near = world.get("near_arm_hand")
    far = world.get("far_arm_hand")
    near_p = getattr(near, "origin", (40.0, 112.0))
    far_p = getattr(far, "origin", (86.0, 112.0))
    forward, rear = (near_p, far_p) if near_p[0] >= far_p[0] else (far_p, near_p)

    def origin(name: str, fallback):
        transform = world.get(name)
        return getattr(transform, "origin", fallback)

    anchors = {
        "cell_core": _out_point(origin("torso", (64.0, 86.0))),
        "pelvis": _out_point(origin("pelvis", (64.0, 108.0))),
        "head": _out_point(origin("head", (64.0, 52.0))),
        "forward_hand": _out_point(forward),
        "rear_hand": _out_point(rear),
        "near_foot": _out_point(origin("near_leg_foot", (52.0, 162.0))),
        "far_foot": _out_point(origin("far_leg_foot", (72.0, 162.0))),
    }
    return {"anchors": anchors}


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    doc = _doc()
    return compose_rig_frame(
        doc,
        animation,
        frame_idx,
        frame_count,
        behind=lambda canvas, t, world, params: draw_pca_behind(
            animation, canvas, t, world, params
        ),
        front=lambda canvas, t, world, params: draw_pca_front(
            animation, canvas, t, world, params
        ),
        padding=PADDING,
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
        frame_meta_fn=frame_meta,
        auto_crop=False,
        actor_metadata=_actor_metadata(doc),
        body_metrics_fn=authored_body_metrics,
        sheet_tuning=doc.sprite_tuning or {"collision_scale": 2.4},
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        attack_hitboxes=ATTACK_HITBOXES,
        hurtbox_parts=hurtbox_parts_for_rows(ROWS),
        pose_bodies="authored",
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
    "FIGHTER_MOTION_COVERAGE",
    "FRAME_SIZE",
    "ROWS",
    "TARGET_NAME",
    "frame_meta",
    "render",
    "render_canonical",
    "render_frame",
]
