"""Rigged SVG helpers for Madam LeBlanc.

Madam LeBlanc now uses a single polished three-quarter rig for every clip.
This keeps the presentation consistent and avoids the awkward side-profile pass.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

from PIL import Image

from ...authoring.rigdoc import RigDocument

TARGET_DIR = Path(__file__).resolve().parent
RIGGED_DIR = TARGET_DIR / "rigged" / "m_leblanc"

THREE_QUARTER_DOC = RIGGED_DIR / "m_leblanc_three_quarter.rig.json"

GLOBAL_SCALE = 0.72
SHIFT_BY_VIEW = {
    "three_quarter": (-28.9, -32.2),
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


def doc_for_clip(clip_name: str) -> tuple[str, RigDocument, str]:
    doc = load_doc()
    if clip_name in {"talk", "point", "nod"}:
        return "three_quarter", doc, "talk"
    if clip_name in {"gesture", "explain", "interact"}:
        return "three_quarter", doc, "interact"
    if clip_name in {"curtsy"}:
        return "three_quarter", doc, "curtsy"
    return "three_quarter", doc, "idle"


def _visible(part: dict, sample: dict[str, object]) -> bool:
    channel = part.get("opacity_channel") or part.get("vis_channel")
    if not channel:
        return True
    # Opacity-bound overlays are hidden unless the active clip explicitly
    # drives them. This keeps blink lids and talk mouths from sitting on top of
    # the neutral face in every frame.
    return float(sample.get(channel, 0.0)) > 0.01


def render_rig(doc: RigDocument, view_key: str, clip_name: str, frame_idx: int, frame_count: int) -> Image.Image:
    canvas = Image.new("RGBA", (128, 128), (255, 255, 255, 0))
    clip = doc.clips[clip_name]
    denom = max(frame_count, 1)
    time = (frame_idx % denom) / denom
    world, sample = doc.solve(clip_name, time)
    shift_x, shift_y = SHIFT_BY_VIEW[view_key]

    for part in sorted(doc.parts, key=lambda item: float(item.get("z", 0.0))):
        if part.get("kind") != "sprite" or not _visible(part, sample):
            continue
        sprite = doc.sprite_image(part, 1.0)
        if not sprite:
            continue
        source, pivot = sprite
        bone_name = str(part.get("bone", ""))
        bw = world.get(bone_name)
        if bw is None:
            continue

        local_scale = float(part.get("scale", 1.0)) * GLOBAL_SCALE
        ox, oy = part.get("offset", [0.0, 0.0])
        x0, y0 = bw.origin
        theta = math.radians(bw.angle)
        px = x0 + ox * math.cos(theta) - oy * math.sin(theta)
        py = y0 + ox * math.sin(theta) + oy * math.cos(theta)
        px = px * GLOBAL_SCALE + shift_x
        py = py * GLOBAL_SCALE + shift_y
        rotation = bw.angle + float(part.get("rotation", 0.0))

        placed = source
        scaled_pivot = (pivot[0], pivot[1])
        if abs(local_scale - 1.0) > 1e-3:
            placed = placed.resize(
                (
                    max(1, round(placed.width * local_scale)),
                    max(1, round(placed.height * local_scale)),
                ),
                Image.Resampling.LANCZOS,
            )
            scaled_pivot = (pivot[0] * local_scale, pivot[1] * local_scale)
        if abs(rotation) > 1e-3:
            placed = placed.rotate(
                -rotation,
                resample=Image.Resampling.BILINEAR,
                expand=True,
                center=scaled_pivot,
            )
        offset = (round(px - scaled_pivot[0]), round(py - scaled_pivot[1]))
        canvas.alpha_composite(placed, offset)
    return canvas


def render_frame(clip_name: str, frame_idx: int, frame_count: int) -> Image.Image:
    view_key, doc, native_clip = doc_for_clip(clip_name)
    return render_rig(doc, view_key, native_clip, frame_idx, frame_count)


def canonical_preview() -> Image.Image:
    return render_frame("idle", 0, 8)


__all__ = [
    "THREE_QUARTER_DOC",
    "canonical_preview",
    "doc_for_clip",
    "load_doc",
    "render_frame",
    "render_rig",
]
