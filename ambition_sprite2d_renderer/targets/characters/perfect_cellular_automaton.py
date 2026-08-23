"""Dedicated full-fighter target for the Perfect Cellular Automaton (PCA).

The hand-drawn SVG + extracted rig remain the character-art authority.  This
module supplies the Smash-facing publication contract: bespoke combat clip
refinements, code-authored cellular effects, authored body/hurt/hit geometry,
and per-frame anchors.  Nothing rewrites the SVG.
"""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.rigdoc import RigDocument
from ...profiling import profile
from ...authoring.sheet_build import build_sheet, write_canonical
from ...authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ._svg_fighter_effects import compose_rig_frame
from .pca_combat_authoring import author_pca_combat_clips
from .pca_effects import EFFECTFUL_ANIMATIONS, draw_pca_behind, draw_pca_front
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

# PCA already publishes at 3x logical resolution. Rendering every SVG part at
# the rig document's legacy 4x supersample would therefore transform at 12x
# logical resolution before shrinking back to 3x. The profile for the complete
# fighter sheet showed almost all frame time in those oversized part rotations.
# Native 3x SVG rasters plus Pillow's bicubic rotation are the publication
# resolution here; the game/display can still downsample the finished sheet.
RIG_RENDER_SUPERSAMPLE = 1


@lru_cache(maxsize=4)
@profile
def _load_doc_cached(path_text: str, mtime_ns: int, size: int) -> RigDocument:
    """Load and author one PCA rig revision exactly once per process.

    Keeping the same :class:`RigDocument` alive is important beyond avoiding
    JSON parsing: the document owns the expensive SVG-part raster and rotated
    sprite caches. Reconstructing it per frame used to throw those caches away
    and could invoke native SVG rasterization hundreds of times per sheet.
    """
    del mtime_ns, size
    doc = RigDocument.load(path_text)
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


@profile
def _doc() -> RigDocument:
    stat = RIG_PATH.stat()
    return _load_doc_cached(str(RIG_PATH), stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=8)
@profile
def _frame_solution_cached(
    animation: str,
    frame_idx: int,
    frame_count: int,
    mtime_ns: int,
    size: int,
):
    """Share the solve used by render_frame with the immediately-following metadata pass."""
    del mtime_ns, size
    doc = _doc()
    t = doc.frame_time(animation, frame_idx, frame_count)
    return t, doc.solve(animation, t)


@profile
def _frame_solution(animation: str, frame_idx: int, frame_count: int):
    stat = RIG_PATH.stat()
    return _frame_solution_cached(
        animation, frame_idx, frame_count, stat.st_mtime_ns, stat.st_size
    )


def actor_metadata() -> dict:
    """**This character's actor metadata**, resolved from its rig document.

    ⭐ **the public name exists because the metadata is REAL but was invisible.**
    Most character targets publish a module-level `ACTOR_METADATA` constant, and
    the contract test looked for exactly that — so this target, whose metadata is
    authored in `perfect_cellular_automaton.rig.json` and handed to `build_sheet`
    at render time, read as *"a registered character with no local actor
    metadata"* and had the suite red on it.

    ⚠ **a function, not a constant, on purpose**: the constant form would parse
    the rig document at IMPORT time, for every discovery, and the whole reason
    `_load_doc_cached` exists is that this document is expensive.
    """
    return _actor_metadata(_doc())


@profile
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


@profile
def frame_meta(animation: str, frame_idx: int, frame_count: int) -> dict:
    _t, solved = _frame_solution(animation, frame_idx, frame_count)
    world, _params = solved

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


@profile
def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    doc = _doc()
    t, solved = _frame_solution(animation, frame_idx, frame_count)

    # Most of the 900+ PCA sheet frames have no cellular effect at all. Avoid
    # allocating and downsampling two large transparent FX canvases for those
    # rows; render the rig directly while still sharing the solved pose with
    # frame_meta().
    if animation not in EFFECTFUL_ANIMATIONS:
        return doc.render_at(
            animation,
            t,
            solved=solved,
            padding=PADDING,
            supersample=RIG_RENDER_SUPERSAMPLE,
        )

    return compose_rig_frame(
        doc,
        animation,
        frame_idx,
        frame_count,
        solved=solved,
        behind=lambda canvas, t, world, params: draw_pca_behind(
            animation, canvas, t, world, params
        ),
        front=lambda canvas, t, world, params: draw_pca_front(
            animation, canvas, t, world, params
        ),
        padding=PADDING,
        rig_supersample=RIG_RENDER_SUPERSAMPLE,
    )


@profile
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


@profile
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
    "render_portraits",
    "render_canonical",
    "render_frame",
]


# PCA's portrait viewport in her 128x192 rig canvas. Measured off the idle pose,
# not from the `head` bone at (64, 66) -- that is the neck joint.
#
# The view is deliberately TALL enough to keep her ears. They reach y=22, well
# above the face, and they are the most recognisable thing about her silhouette;
# a tight head-and-shoulders crop decapitated them.
_PORTRAIT_FACE = FaceGuide(
    center_x=64.0,
    center_y=52.0,
    width=30.0,
    height=34.0,
    source_width=128.0,
    source_height=192.0,
)
_PORTRAIT_VIEW_WIDTH = 62.0
_PORTRAIT_CENTER_Y = 56.0
_PORTRAIT_RENDER_SCALE = 3


def render_portraits(out_dir: str | Path, **opts):
    """Publish PCA's close-ups natively from her extracted rig.

    Idle draws no effects -- `EFFECTFUL_ANIMATIONS` covers her attacks and
    blinks, not her standing pose -- so the bare rig render IS what she looks
    like here, and there is nothing to compose over it.
    """
    del opts
    doc = _doc()

    def frame(animation: str, index: int, count: int) -> Image.Image:
        source = doc.render_at(
            animation,
            doc.frame_time(animation, index, count),
            supersample=4,
            scale=_PORTRAIT_RENDER_SCALE,
        )
        return render_framed_portrait(
            source,
            _PORTRAIT_FACE,
            view_width=_PORTRAIT_VIEW_WIDTH,
            center_y=_PORTRAIT_CENTER_Y,
        )

    def loop(animation: str, count: int, duration_ms: int) -> PortraitClip:
        return PortraitClip.loop(
            tuple(frame(animation, index, count) for index in range(count)),
            duration_ms,
        )

    clips = {
        "default": loop("idle", 8, 148),
        "portrait": PortraitClip.still(frame("idle", 2, 8)),
    }
    return write_portrait_sheet(
        TARGET_NAME, clips, Path(out_dir), still_clip="portrait"
    )
