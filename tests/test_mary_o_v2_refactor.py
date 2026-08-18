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
    """Lock the reviewed output after intentional visual edits.

    ⚠ **this hash moves whenever the art is DELIBERATELY re-proportioned, and it
    is not the thing that says the art is right.** Its job is to make an
    unintended change loud. Re-record it only alongside a render you have
    actually looked at.

    Last re-recorded for the rig refactor: parts now hang off `FormRig` anchors
    expressed as fractions of the form's authored size instead of the grown
    form's absolute offsets. The GROWN form is byte-identical through that change
    (verified frame by frame against a control render) — every moved pixel is on
    the short form, which is what the refactor set out to fix.
    """
    renderers = [
        mary_o_v2.render_mary_o_v2,
        mary_o_v2.render_mary_o_v2_tall,
        mary_o_v2.render_mary_o_v2_fire,
    ]
    for render in renderers:
        render(tmp_path)

    expected = {
        "mary_o_v2_canonical.png": "9387751b78613cccb59d081832128e0142040d95e6594f59cd18a63bd05f489f",
        "mary_o_v2_spritesheet.png": "e36b05d162dc7bb7b4aede9d1d3f54bf8d95d955d0269859edef870c29c7d1fe",
        "mary_o_v2_tall_canonical.png": "c1c1d0a5bdfbe36479992e860ed2dcc630651b8f05fe66927b938075d77a5055",
        "mary_o_v2_tall_spritesheet.png": "9c8854062b6f04481e0a375c2fd81ab7afbb0764d0519bcb8c19b9573cddbb8a",
        "mary_o_v2_fire_canonical.png": "39a0edcc7db661e7a751ff373e8a9a956f1542c8fea4e74befcc8542404124dc",
        "mary_o_v2_fire_spritesheet.png": "b9fd4196e0bc0aedba28e94d9fdefcaa123125ceca71e06d4f70d93cb22eb426",
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
        # ⚠ **the box top is set by the HEIGHT CONTRACT, not measured off the
        # art** (Jon, 2026-08-18: small Mary-O is one brick, grown is two), so
        # "the box starts below the top of the art" — which this asserted while
        # every form still had a hat poking out — is no longer the invariant.
        # Both forms now top out AT or just inside their box.
        #
        # What still matters is the gap, in both directions. Decoration ABOVE
        # the box is the point (the fire form's frills clear it by 14 px and
        # must never collide). The box floating far above the DRAWING is the
        # unfair case in the other direction: she would hit a ceiling with the
        # empty air over her head. MEASURED: grown 0 px, fire -14 px, short 6 px.
        headroom = alpha[1] - box["y"]
        assert headroom <= 8, (target, headroom)
        # ...but her feet are still enclosed, since the box bottom is what
        # stands. ⚠ allow one publish pixel: frames are bottom-anchored on
        # publish, so a flat-soled figure's last ink row lands ON the frame edge
        # while the authored shoe line sits just inside it. MEASURED: grown +2,
        # short -2. A real sinking foot is many pixels, not one.
        assert box["y"] + box["h"] >= alpha[3] - 2, target

    # One width for every form, so growing or catching fire never changes how
    # wide she is.
    widths = {t: b["w"] for t, b in boxes.items()}
    assert len(set(widths.values())) == 1, widths

    # ⭐⭐ **EXACTLY two to one** — Jon, 2026-08-18: small Mary-O is 16 world
    # units (one brick) and grown is 32. This asserted 88/63 = 1.397, the ratio
    # the art happened to have before the re-proportioning, which is a
    # measurement of the old sprites rather than the rule they now answer to.
    ratio = boxes["mary_o_v2_tall"]["h"] / boxes["mary_o_v2"]["h"]
    assert abs(ratio - 2.0) < 0.01, ratio
    assert boxes["mary_o_v2_fire"]["h"] == boxes["mary_o_v2_tall"]["h"]
