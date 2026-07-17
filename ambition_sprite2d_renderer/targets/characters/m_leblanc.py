"""Rigged SVG helpers for Madam LeBlanc.

Madam LeBlanc now uses a single polished three-quarter rig for every clip.
This keeps the presentation consistent and avoids the awkward side-profile pass.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical

TARGET_DIR = Path(__file__).resolve().parent
RIGGED_DIR = TARGET_DIR / "rigged" / "m_leblanc"

THREE_QUARTER_DOC = RIGGED_DIR / "m_leblanc_three_quarter.rig.json"

# The discovered target name is the module stem, and `build_sheet` names its
# outputs `{TARGET_NAME}_spritesheet.*`; the two must agree so install/discovery
# find the rendered sheet.
TARGET_NAME = "m_leblanc"
# The rig frame is 128x128 at render_scale 2, so the shared compositor emits
# 256x256 frames.
FRAME_W, FRAME_H = 256, 256

# Madam LeBlanc is a peaceful hall/social NPC, so she shares the four-clip
# vocabulary of the other three-quarter conversationalists (Eve, Mallory,
# Erdish). Her rig has no walk cycle of its own; `doc_for_clip` folds `walk`
# onto the idle pose, which reads fine for a character the game only ever leaves
# standing at her pedestal.
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 150),
    ("walk", 8, 120),
    ("talk", 8, 120),
    ("interact", 8, 130),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": TARGET_NAME,
        "display_name": "Madam LeBlanc",
    },
    "body": {
        "body_plan": "Scholar",
        "body_kind": "Grounded",
        "traits": [
            "mathematician",
            "peaceful",
            "expressive",
            "three_quarter_rig",
        ],
    },
    "visual": {
        "default_pose": "idle",
        "facing_policy": "three_quarter",
    },
    "provenance": {
        "variant_family": TARGET_NAME,
        "variant_id": "opus_4_8_render_wiring_2026_07_17",
        "lineage": [
            {
                "revision_id": "gpt_5_6_leblanc_rig_2026_07_17",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "contribution": "three_quarter_svg_rig_and_clip_authoring_for_sophie_germain",
                "date": "2026-07-17",
            },
            {
                "revision_id": "opus_4_8_render_wiring_2026_07_17",
                "creator_kind": "model",
                "creator": "claude-opus-4.8",
                "contribution": "module_render_entry_point_rows_and_actor_metadata_so_the_rig_registers_and_installs",
                "parent_revision_id": "gpt_5_6_leblanc_rig_2026_07_17",
                "date": "2026-07-17",
            },
        ],
    },
    "tags": ["npc", "mathematician", "peaceful", "custom"],
}


@lru_cache(maxsize=8)
def load_doc(name: str = "m_leblanc_three_quarter.rig.json") -> RigDocument:
    doc = RigDocument.load(RIGGED_DIR / name)
    for clip in doc.clips.values():
        channels = clip.get("channels", {})
        for channel_name, spec in list(channels.items()):
            if isinstance(spec, list):
                if spec and isinstance(spec[0], dict):
                    channels[channel_name] = {"keys": spec}
                else:
                    denom = max(len(spec) - 1, 1)
                    channels[channel_name] = {
                        "keys": [[idx / denom, value] for idx, value in enumerate(spec)]
                    }
    return doc


def doc_for_clip(clip_name: str) -> tuple[RigDocument, str]:
    """Map a requested animation row onto one of the rig's native clips.

    The rig authors only ``idle``/``talk``/``interact``/``curtsy``; a peaceful
    hall NPC never needs more, so anything else (including ``walk``) folds onto
    the neutral idle pose.
    """
    doc = load_doc()
    if clip_name in {"talk", "point", "nod"}:
        return doc, "talk"
    if clip_name in {"gesture", "explain", "interact"}:
        return doc, "interact"
    if clip_name in {"curtsy"}:
        return doc, "curtsy"
    return doc, "idle"


def render_frame(clip_name: str, frame_idx: int, frame_count: int) -> Image.Image:
    """Render one frame through the shared rig compositor.

    Madam LeBlanc's rig follows the standard multiview-SVG contract — each
    part's ``pivot`` is its bone joint and ``rest_angle`` is the bone's rest
    world angle — so the one canonical :meth:`RigDocument.render_frame` places
    every part correctly. The earlier bespoke compositor here reimplemented the
    joint math with ad-hoc scale/shift constants and dropped the arms, legs, and
    skirt sides; delegating to the shared path is both correct and the same code
    the other multiview-SVG characters (Oiler) run.
    """
    doc, native_clip = doc_for_clip(clip_name)
    return doc.render_frame(native_clip, frame_idx, frame_count)


def canonical_preview() -> Image.Image:
    return render_frame("idle", 0, 8)


def render(out_dir: Path, **opts) -> List[Path]:
    """Module-target entry point: build Madam LeBlanc's full sheet."""
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        actor_metadata=ACTOR_METADATA,
        animation_key_map={name: name for name, _frames, _duration in ROWS},
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


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        render_frame,
        Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
    )


__all__ = [
    "ACTOR_METADATA",
    "ROWS",
    "TARGET_NAME",
    "THREE_QUARTER_DOC",
    "canonical_preview",
    "doc_for_clip",
    "load_doc",
    "render",
    "render_canonical",
    "render_frame",
]
