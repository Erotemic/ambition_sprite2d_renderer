"""Gravity Apple: a hostile green apple with separable field apparatus.

The ordinary spritesheet is an assembled preview for existing consumers.
`parts/` publishes individual transparent SVG/PNG assets and their pivots so
later gameplay can pose the fruit, fin leaves, orbit arcs and satellites
independently. No engine behavior is implemented by this art target.
"""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
import json
from pathlib import Path

from PIL import Image

from ...authoring.sheet_build import build_sheet, rendering_canonical_only
from ...authoring.svg_parts import _svg_to_png_bytes
from ._apple_enemy_family import FRAME_SIZE, GRAVITY_ROWS, SHEET_KEYS, _body_path
from ._gravity_apple_art import frame_svg as _frame_svg, parts as _parts

TARGET_NAME = "gravity_apple"
ROWS = GRAVITY_ROWS
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]

ACTOR_METADATA = {
    "actor": {"character_id": "gravity_apple", "display_name": "Gravity Apple"},
    "body": {
        "body_plan": "BeastBiped",
        "body_kind": "LowProfile",
        "mass_class": "Light",
        "locomotion_hint": "Fly",
        "traits": ["enemy", "fruit", "small", "gravity_variant", "hover"],
    },
    "capabilities": {"traversal": {"walk": None, "fly": True}},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.fly": {"animation": "float", "events": []},
        "locomotion.walk": {"animation": "float", "events": []},
        "action.melee.primary": {"animation": "charge", "events": []},
        "action.special.gravity": {"animation": "flip", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "tags": ["enemy", "fruit", "gravity_variant", "gnu_ton_handle"],
    "authoring_description": {
        "visual_inspirations": [
            "Bright green fruit, threatening narrow eyes and a compact gravity-well mouth.",
            "Independent equatorial bands, split calyx fins and faceted gravity satellites.",
        ],
        "rigging_notes": [
            "The composited sheet is a compatibility/preview assembly, not a layered runtime asset.",
            "See parts/parts.json and the per-part transparent SVG/PNG exports for independent posing.",
            "Do not draw the full composite simultaneously with extracted parts: that duplicates the apparatus.",
            "The actor's full-body rolling rotation belongs to the engine and is never baked into the sheet.",
            "No detached shadows or floor effects are authored.",
        ],
    },
    "gameplay_description": (
        "A calculating gravity-corrupted green apple. Its orbit and satellites "
        "are separately authored presentation geometry, not a source of physics, "
        "attacks, inversion effects, or collision behavior."
    ),
}


def _frame_count(animation: str) -> int:
    return dict((name, n) for name, n, _ in ROWS)[animation]


def render_svg(animation: str = "idle", frame: int = 0, count: int | None = None) -> str:
    if count is None:
        count = _frame_count(animation)
    return _frame_svg(animation, frame, count, body_path=_body_path())


def render_part_svg(
    part_name: str,
    animation: str = "idle",
    frame: int = 0,
    count: int | None = None,
) -> str:
    """Return one named part at any animation frame on a shared canvas."""
    if count is None:
        count = _frame_count(animation)
    return _frame_svg(animation, frame, count, body_path=_body_path(), only_part=part_name)


@lru_cache(maxsize=192)
def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    svg = render_svg(animation, frame_idx, frame_count)
    with Image.open(BytesIO(_svg_to_png_bytes(svg, dpi=96))) as png:
        return png.convert("RGBA")


def render_parts(out_dir: str | Path) -> list[Path]:
    """Publish independently renderable idle-pose art plus a pivot manifest.

    These are static *part sources*. At runtime the caller can move/rotate
    orbit rings, leaf fins or satellites without relying on the animation
    baked into the composite. No runtime wiring is implied.
    """
    out_dir = Path(out_dir)
    parts_dir = out_dir / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    specs = _parts("idle", 0, _frame_count("idle"), body_path=_body_path())
    files: list[Path] = []
    records = []
    for part in specs:
        svg = render_part_svg(part.name)
        svg_path = parts_dir / f"{part.name}.svg"
        png_path = parts_dir / f"{part.name}.png"
        svg_path.write_text(svg, encoding="utf8")
        with Image.open(BytesIO(_svg_to_png_bytes(svg, dpi=96))) as png:
            png.convert("RGBA").save(png_path)
        records.append({
            "name": part.name,
            "parent": part.parent,
            "z": part.z,
            "pivot_viewbox_xy_before_pose": list(part.pivot),
            "pivot_png_xy_at_idle": [part.pivot[0] / 2, (part.pivot[1] - 12) / 2],
            "source_svg": svg_path.name,
            "transparent_png": png_path.name,
        })
        files.extend([svg_path, png_path])
    manifest = parts_dir / "parts.json"
    manifest.write_text(json.dumps({
        "character_id": TARGET_NAME,
        "source_canvas_px": [512, 512],
        "image_size_px": list(FRAME_SIZE),
        "note": "Each part PNG has a full transparent 256x256 canvas and shared origin. The idle root pose translates y by -12 SVG units.",
        "composite_sheet_already_contains_parts": True,
        "composite_and_parts_must_not_be_drawn_together": True,
        "engine_owns_continuous_body_rotation": True,
        "parts": records,
    }, indent=2) + "\n", encoding="utf8")
    return files + [manifest]


def render(out_dir: str | Path, **opts):
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = build_sheet(
        target=TARGET_NAME,
        rows=list(ROWS),
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=True,
        crop_margin=6,
        actor_metadata=ACTOR_METADATA,
        pose_bodies="authored",
    )
    paths = [Path(result[k]) for k in SHEET_KEYS if result.get(k)]
    idle = out_dir / "gravity_apple_idle.svg"
    idle.write_text(render_svg("idle"), encoding="utf8")
    paths.append(idle)
    if not rendering_canonical_only():
        paths.extend(render_parts(out_dir))
    return paths


__all__ = [
    "ACTOR_METADATA", "FRAME_SIZE", "ROWS", "SHEET_FILES", "TARGET_NAME",
    "render", "render_frame", "render_parts", "render_part_svg", "render_svg",
]
