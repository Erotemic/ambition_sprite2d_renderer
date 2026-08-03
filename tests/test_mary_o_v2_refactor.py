from __future__ import annotations

import ast
import hashlib
from collections import Counter
from pathlib import Path

import yaml
from PIL import Image

from ambition_sprite2d_renderer.targets.characters import mary_o_v2
from ambition_sprite2d_renderer.targets.super_mary_o_common import OUTLINE
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_art import (
    _debug_part_image,
    _draw_front_nose,
    _draw_side_nose,
    list_nose_variants,
)


def _pixel_digest(path: Path) -> str:
    image = Image.open(path).convert("RGBA")
    hasher = hashlib.sha256()
    hasher.update(image.mode.encode())
    hasher.update(str(image.size).encode())
    hasher.update(image.tobytes())
    return hasher.hexdigest()


def test_mary_o_v2_matches_reviewed_visual_baseline(tmp_path: Path) -> None:
    """Lock the reviewed output after intentional visual edits."""
    renderers = [
        mary_o_v2.render_mary_o_v2,
        mary_o_v2.render_mary_o_v2_tall,
        mary_o_v2.render_mary_o_v2_fire,
    ]
    for render in renderers:
        render(tmp_path)

    expected = {
        "mary_o_v2_canonical.png": "77d632375b90672b59b48a673acfaef7feb5eeeeece0c1b942336a9d2565db55",
        "mary_o_v2_spritesheet.png": "f3d5c308398d82669fdee80e953fafb94d612c706ac41efb77427f0a5dd1cc14",
        "mary_o_v2_tall_canonical.png": "93d0d3cdfb419f733fb70e93d79c0bdeec390e8beab168c17b1646ad4b563d21",
        "mary_o_v2_tall_spritesheet.png": "caadcfd5cc6bc36d46c9f245c59097e28ef3f2f8cc95c56c72a83b23e0296576",
        "mary_o_v2_fire_canonical.png": "9be563c6141d79b0dbdf52e01766c29a40131f67b5d3fd7259cd64b05a465122",
        "mary_o_v2_fire_spritesheet.png": "8a49ecf66afb9748a38710f415136d6e214e2d83dcb8a2919a4837eec3bf2157",
    }
    actual = {name: _pixel_digest(tmp_path / name) for name in expected}
    assert actual == expected




def test_mary_o_v2_publishes_at_exactly_two_x_resolution(tmp_path: Path) -> None:
    """Increase texture dimensions without changing the authored logical art."""
    outputs = mary_o_v2.render_mary_o_v2(tmp_path)
    assert mary_o_v2.OUTPUT_RESOLUTION_SCALE == 2.0
    assert mary_o_v2.AUTHORING_FRAME_SIZE == (80, 96)
    assert mary_o_v2.FRAME_SIZE == (160, 192)

    canonical = Image.open(tmp_path / "mary_o_v2_canonical.png")
    transparent = Image.open(tmp_path / "mary_o_v2_canonical_transparent.png")
    assert canonical.size == mary_o_v2.FRAME_SIZE
    assert transparent.size == mary_o_v2.FRAME_SIZE
    assert all(path.exists() for path in outputs)

    metadata = mary_o_v2._actor_metadata(mary_o_v2.SHORT_FORM)
    sockets = metadata["sockets"]
    assert sockets["head"]["point"] == {"x": 78.0, "y": 40.0}
    assert sockets["hand_r"]["point"] == {"x": 116.0, "y": 108.0}
    assert sockets["foot_r"]["point"] == {"x": 98.0, "y": 176.0}


def _alpha_bbox_size(image: Image.Image) -> tuple[int, int]:
    bbox = image.getchannel("A").getbbox()
    assert bbox is not None
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def test_nose_geometry_scales_with_logical_rasterization() -> None:
    """Prevent a return to fixed physical-pixel nose stencils."""
    painters = [
        lambda px: _draw_front_nose(px, mary_o_v2.TALL_FORM, 5.0, 5.0),
        lambda px: _draw_side_nose(px, mary_o_v2.TALL_FORM, 5.0, 5.0),
    ]
    for painter in painters:
        small = _debug_part_image(painter, logical_size=(16, 16), scale=3)
        large = _debug_part_image(painter, logical_size=(16, 16), scale=9)
        small_w, small_h = _alpha_bbox_size(small)
        large_w, large_h = _alpha_bbox_size(large)
        # Allow a little quantization slack for very tiny cute noses while
        # still enforcing clear logical-coordinate growth across raster scales.
        assert large_w >= small_w * 2.2
        assert large_h >= small_h * 2.4
        assert (large_w * large_h) >= (small_w * small_h) * 5.2


def test_mary_o_v2_modules_do_not_shadow_part_definitions() -> None:
    package_dir = Path(mary_o_v2.__file__).parent
    module_names = [
        "mary_o_v2.py",
        "_mary_o_v2_model.py",
        "_mary_o_v2_art.py",
    ]
    for module_name in module_names:
        source = (package_dir / module_name).read_text()
        tree = ast.parse(source)
        names = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        ]
        duplicates = {name for name, count in Counter(names).items() if count > 1}
        assert not duplicates, (module_name, duplicates)


def test_mary_o_v2_uses_selected_button_east_profile_step_nose() -> None:
    assert list_nose_variants() == ["button_east_profile_step"]


def test_side_nose_reads_as_outline_plus_skin_profile() -> None:
    image = _debug_part_image(
        lambda px: _draw_side_nose(px, mary_o_v2.TALL_FORM, 5.0, 5.0),
        logical_size=(16, 16),
        scale=12,
    )
    pixels = image.load()
    colors = {
        pixels[x, y]
        for y in range(image.height)
        for x in range(image.width)
        if pixels[x, y][3] > 0
    }
    assert OUTLINE in colors
    assert len(colors) >= 3


def test_side_nose_flips_horizontally_for_lookback() -> None:
    east = _debug_part_image(
        lambda px: _draw_side_nose(px, mary_o_v2.TALL_FORM, 5.0, 5.0, lookback=False),
        logical_size=(16, 16),
        scale=12,
    )
    west = _debug_part_image(
        lambda px: _draw_side_nose(px, mary_o_v2.TALL_FORM, 5.0, 5.0, lookback=True),
        logical_size=(16, 16),
        scale=12,
    )
    east_bbox = east.getchannel("A").getbbox()
    west_bbox = west.getchannel("A").getbbox()
    assert east_bbox is not None and west_bbox is not None
    east_center_x = (east_bbox[0] + east_bbox[2]) / 2
    west_center_x = (west_bbox[0] + west_bbox[2]) / 2
    assert west_center_x < east_center_x


def _idle_alpha_bbox(sheet_png: Path, yaml_path: Path):
    """Alpha extent of the idle frame — what the box is deliberately tighter than."""
    meta = yaml.safe_load(yaml_path.read_text())
    rect = {row["animation"]: row for row in meta["rows"]}["idle"]["rects"][0]
    frame = Image.open(sheet_png).convert("RGBA").crop(
        (rect["x"], rect["y"], rect["x"] + rect["w"], rect["y"] + rect["h"])
    )
    return frame.getchannel("A").getbbox(), meta


def test_mary_o_v2_collision_box_is_authored_not_measured(tmp_path: Path) -> None:
    """The gameplay body is stated by the target, not read off the alpha bbox.

    The measured bbox includes her cap tip, ponytail, sleeves, and the fire
    form's flame frills. Colliding on those reads as unfair, and it let the fire
    form drift 22% wider than the tall form on decoration alone.
    """
    renders = {
        "mary_o_v2": mary_o_v2.render_mary_o_v2,
        "mary_o_v2_tall": mary_o_v2.render_mary_o_v2_tall,
        "mary_o_v2_fire": mary_o_v2.render_mary_o_v2_fire,
    }
    boxes = {}
    for target, render in renders.items():
        render(tmp_path)
        alpha, meta = _idle_alpha_bbox(
            tmp_path / f"{target}_spritesheet.png", tmp_path / f"{target}_spritesheet.yaml"
        )
        box = meta["body_metrics"]["body_pixel_bbox"]
        boxes[target] = box

        # Forgiveness on the sides: narrower than everything she visibly has out.
        assert box["w"] < (alpha[2] - alpha[0]), target
        # Forgiveness on the cap tip: the box starts below the top of the art.
        assert box["y"] > alpha[1], target
        # ...but her feet are still enclosed, since the box bottom is what stands.
        assert box["y"] + box["h"] >= alpha[3], target

    # One width for every form, so growing or catching fire never changes how
    # wide she is.
    widths = {t: b["w"] for t, b in boxes.items()}
    assert len(set(widths.values())) == 1, widths

    # Tall stays taller than short, at the ratio the shipped art had (88/63),
    # so every ceiling and pipe in the level still fits her as it does today.
    ratio = boxes["mary_o_v2_tall"]["h"] / boxes["mary_o_v2"]["h"]
    assert abs(ratio - 88 / 63) < 0.01, ratio
    assert boxes["mary_o_v2_fire"]["h"] == boxes["mary_o_v2_tall"]["h"]
