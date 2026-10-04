"""A part that is another part mirrored or turned a quarter is ONE source with
a transform on its draw (Jon, 2026-10-04: a zero-cost flip or quarter turn is
not a second raster)."""

import math
import random

from PIL import Image

from ambition_sprite2d_renderer.authoring.part_flipbook import (
    PLACEMENT_CONTINUOUS,
    TWEEN_LINEAR,
    PartDraw,
    PartFlipbook,
    PartRaster,
    _LOSSLESS,
    _share_transformed_parts,
)


def _piece() -> Image.Image:
    """An asymmetric piece on uneven padding: no transform of it is itself.

    At least the publisher's 2-texel border on every side (`PART_BORDER`):
    resampled, PIL treats a raster's edge one way on its left and top and
    another on its right and bottom, so art touching it differs by a pixel
    between a raster and its mirror."""
    random.seed(7)
    image = Image.new("RGBA", (15, 11), (0, 0, 0, 0))
    for x in range(2, 12):
        for y in range(2, 8):
            if x + 2 * y < 17:
                image.putpixel((x, y), (random.randrange(256), random.randrange(256), 90, 255))
    return image


def _flipbook(tween: bool = False) -> PartFlipbook:
    base = _piece()
    parts = [PartRaster("base", base, (4.0, 3.0))]
    draws = [PartDraw(0, (-20.0, -40.0), 0.3, (1.0, 1.0), "base")]
    # Every lossless transform of the base, each with its own pivot and
    # padding, drawn at its own place, turn and (mirrored) scale.
    for k, op in enumerate(_LOSSLESS):
        turned = base.transpose(op)
        padded = Image.new("RGBA", (turned.width + k, turned.height + 2), (0, 0, 0, 0))
        padded.alpha_composite(turned, (k, 1))
        parts.append(PartRaster(f"copy{k}", padded, (2.0 + k * 0.5, 5.0)))
        draws.append(
            PartDraw(k + 1, (-30.0 + 9 * k, -20.0 - 3 * k), 0.4 * k - 1.0, (-1.0 if k % 3 == 0 else 1.0, 1.0), f"copy{k}")
        )
    clips = {"idle": (0.1, [draws])}
    tweens = {}
    if tween:
        # The same tracks in a second frame, drawing the BASE: each copy's
        # track changes part between the frames, so it holds still.
        clips["idle"] = (0.1, [draws, [PartDraw(0, d.at, d.rotation, (1.0, 1.0), d.track) for d in draws]])
        tweens = {"idle": TWEEN_LINEAR}
    return PartFlipbook("sharing", (96, 72), (60.0, 66.0), parts, clips, tweens=tweens, placement=PLACEMENT_CONTINUOUS)


def _differs(a: Image.Image, b: Image.Image) -> int:
    pa, pb = a.load(), b.load()
    return sum(
        1
        for x in range(a.width)
        for y in range(a.height)
        if max(abs(u - v) for u, v in zip(pa[x, y], pb[x, y])) > 2
    )


def test_every_lossless_copy_is_drawn_from_one_source():
    flipbook = _flipbook()
    shared = _share_transformed_parts(flipbook)
    assert len(flipbook.parts) == 1 + len(_LOSSLESS)
    assert len(shared.parts) == 1, f"{len(shared.parts)} parts remain"
    before = flipbook.recompose("idle", 0)
    after = shared.recompose("idle", 0)
    assert before.getchannel("A").getbbox() is not None
    assert _differs(before, after) == 0, "a shared copy does not draw where its own raster drew"


def test_a_tweened_track_that_changed_part_is_not_made_one_part():
    shared = _share_transformed_parts(_flipbook(tween=True))
    # Every copy's track draws the base in the next frame: sharing would turn
    # a held step into a flip interpolated through zero. None is shared.
    assert len(shared.parts) == 1 + len(_LOSSLESS)


def test_a_draw_turned_by_a_shared_quarter_turn_keeps_square_axes():
    shared = _share_transformed_parts(_flipbook())
    for draw in shared.clips["idle"][1][0]:
        assert abs(abs(draw.scale[0]) - 1.0) < 1e-9 and abs(abs(draw.scale[1]) - 1.0) < 1e-9
        assert math.isfinite(draw.rotation)


def test_the_same_pixels_at_another_pivot_are_one_part():
    base = _piece()
    padded = Image.new("RGBA", (base.width + 3, base.height + 1), (0, 0, 0, 0))
    padded.alpha_composite(base, (3, 1))
    parts = [PartRaster("a", base, (4.0, 3.0)), PartRaster("b", padded, (1.5, 6.0))]
    draws = [PartDraw(0, (-30.0, -40.0), 0.0, (1.0, 1.0), "a"), PartDraw(1, (5.0, -20.0), 0.6, (-1.0, 1.0), "b")]
    flipbook = PartFlipbook("twin", (96, 72), (60.0, 66.0), parts, {"idle": (0.1, [draws])}, placement=PLACEMENT_CONTINUOUS)
    shared = _share_transformed_parts(flipbook)
    assert len(shared.parts) == 1
    assert _differs(flipbook.recompose("idle", 0), shared.recompose("idle", 0)) == 0
