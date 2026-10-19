"""Searchlight Crawler concept character.

This module exposes a render entry point for the concept rig. It is not wired
into gameplay content yet. Use it to review art, silhouette, and pose choices.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "searchlight_crawler"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / f"{TARGET_NAME}.rig.json"


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


ACTOR_METADATA = _doc().data.get("actor_metadata", {})


#: Rows the game asks for by its own names, drawn from the rig's rows. An enemy's melee swing plays `attack_side`.
ROW_ALIASES = {"attack_side": "strike"}


def _rows():
    """The rig's rows, then each alias the rig has the source row for."""
    rows = list(_doc().rows())
    by_name = {row[0]: row for row in rows}
    return rows + [(alias,) + tuple(by_name[source][1:]) for alias, source in ROW_ALIASES.items() if source in by_name]


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return _doc().render_frame(ROW_ALIASES.get(animation, animation), frame_idx, frame_count)


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    frame = doc.data["frame"]
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=_rows(),
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=(int(frame["width"]), int(frame["height"])),
        auto_crop=True,
        crop_margin=6,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, _rows(), _render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "render"]
