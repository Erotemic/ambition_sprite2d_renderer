"""SVG-rigged Shock Warden.

The authored SVG owns the parts and joint locations. The rig document owns
poses. This is a sprite target, not a registered Castle Godwin encounter.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "shock_warden"
RIG_PATH = (Path(__file__).resolve().parent / "rigged" / TARGET_NAME
            / f"{TARGET_NAME}.rig.json")


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


ACTOR_METADATA = _doc().data["actor_metadata"]


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return _doc().render_frame(animation, frame_idx, frame_count)


def render(out_dir: str | Path, **opts):
    del opts
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    doc = _doc()
    frame = doc.frame
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=doc.rows(),
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=(int(frame["width"]), int(frame["height"])),
        auto_crop=True,
        crop_margin=5,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning,
    )
    keys = ("spritesheet", "yaml", "ron", "actor",
            "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(
        TARGET_NAME, doc.rows(), _render_frame, outputs,
        frame_transform, Path(out_dir)
    )
    return [Path(outputs[k]) for k in keys if outputs.get(k)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "render"]
