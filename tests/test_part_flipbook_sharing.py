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
    _near_sources,
    _share_near_parts,
    _share_transformed_parts,
    _split_symmetric_parts,
    keep_distinct,
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


def _limb(shade: float, length: int) -> Image.Image:
    """A capsule-ish limb, outline dark, fill shaded."""
    image = Image.new("RGBA", (length + 6, 14), (0, 0, 0, 0))
    for x in range(2, length + 4):
        for y in range(2, 12):
            edge = x in (2, length + 3) or y in (2, 11)
            fill = tuple(int(c * shade) for c in ((40, 30, 30) if edge else (200, 150, 120)))
            image.putpixel((x, y), (*fill, 255))
    # A knuckle at the far end: no mirror of the limb is the limb.
    for x in range(length, length + 3):
        for y in range(4, 9):
            image.putpixel((x, y), (*(int(c * shade) for c in (240, 90, 60)), 255))
    return image


def _limb_flipbook(back):
    front = _limb(1.0, 30)
    parts = [PartRaster("front", front, (3.0, 7.0)), PartRaster("back", back, (4.0, 7.0))]
    draws = [PartDraw(0, (-10.0, -30.0), 0.2, (1.0, 1.0), "front_arm"), PartDraw(1, (12.0, -28.0), -0.4, (1.0, 1.0), "back_arm")]
    flipbook = PartFlipbook("limbs", (96, 72), (48.0, 66.0), parts, {"idle": (0.1, [draws])}, placement=PLACEMENT_CONTINUOUS)
    return flipbook, {("idle", 0): flipbook.recompose("idle", 0)}


def test_a_back_limb_that_is_its_front_limb_darker_and_mirrored_is_drawn_from_it():
    # The back limb: the front limb mirrored, 80% as bright, padded a texel
    # further in. Exact sharing cannot see it; the near pass draws it as the
    # front limb with a flip and a tint, and the frame still replays.
    back = Image.new("RGBA", (37, 15), (0, 0, 0, 0))
    back.alpha_composite(_limb(0.8, 30).transpose(Image.Transpose.FLIP_LEFT_RIGHT), (1, 1))
    flipbook, rendered = _limb_flipbook(back)
    sources = _near_sources(flipbook)
    assert set(sources) == {1}, sources
    src, op, _offset, tint = sources[1]
    assert src == 0 and op == Image.Transpose.FLIP_LEFT_RIGHT and abs(tint[0] - 0.8) < 0.02
    shared = _share_near_parts(flipbook, rendered)
    assert len(shared.parts) == 1
    assert _differs(rendered[("idle", 0)], shared.recompose("idle", 0)) <= 3


def test_a_twin_with_a_real_difference_is_kept():
    # A back limb with a stripe the front limb lacks is its own art.
    back = _limb(1.0, 30)
    for y in range(4, 10):
        back.putpixel((15, y), (20, 200, 20, 255))
        back.putpixel((16, y), (20, 200, 20, 255))
    flipbook, rendered = _limb_flipbook(back)
    assert _near_sources(flipbook) == {}


def test_an_author_keeps_twins_apart():
    flipbook, rendered = _limb_flipbook(_limb(0.8, 30))
    assert _near_sources(flipbook)
    keep_distinct("limbs", "back_arm")
    assert _near_sources(flipbook, frozenset({"back_arm"})) == {}


def _symmetric(width: int) -> Image.Image:
    """A capsule symmetric end to end (any width, odd or even)."""
    image = Image.new("RGBA", (width, 14), (0, 0, 0, 0))
    for x in range(2, width - 2):
        for y in range(2, 12):
            edge = x in (2, width - 3) or y in (2, 11)
            image.putpixel((x, y), ((40, 30, 30) if edge else (200, 150, 120)) + (255,))
    return image


def test_a_part_that_is_its_own_mirror_is_stored_as_half():
    for width in (34, 35):
        part = _symmetric(width)
        draws = [PartDraw(0, (-10.0, -30.0), 0.3, (1.0, 1.0), "limb"), PartDraw(0, (14.0, -20.0), -1.1, (-1.0, 1.0), "limb2")]
        flipbook = PartFlipbook("sym", (96, 72), (48.0, 66.0), [PartRaster("limb", part, (5.0, 7.0))],
                                {"idle": (0.1, [draws])}, placement=PLACEMENT_CONTINUOUS)
        rendered = {("idle", 0): flipbook.recompose("idle", 0)}
        split = _split_symmetric_parts(flipbook, rendered)
        assert split is not flipbook, f"width {width}: not split"
        assert len(split.parts) == 1 and split.parts[0].image.width < width - 8
        assert len(split.clips["idle"][1][0]) == 4
        # The publisher's own replay contract: the overlap composites a few
        # anti-aliased texels twice, within it.
        from ambition_sprite2d_renderer.authoring.part_flipbook import (
            CONTINUOUS_REPLAY_BLOB, CONTINUOUS_REPLAY_PARITY, CONTINUOUS_REPLAY_TOLERANCE, largest_wrong_blob, parity,
        )
        got = split.recompose("idle", 0)
        assert parity(rendered[("idle", 0)], got, **CONTINUOUS_REPLAY_TOLERANCE) <= CONTINUOUS_REPLAY_PARITY
        assert largest_wrong_blob(rendered[("idle", 0)], got, **CONTINUOUS_REPLAY_TOLERANCE) <= CONTINUOUS_REPLAY_BLOB


def test_an_asymmetric_part_stays_whole():
    draws = [PartDraw(0, (-10.0, -30.0), 0.3, (1.0, 1.0), "limb")]
    flipbook = PartFlipbook("asym", (96, 72), (48.0, 66.0), [PartRaster("limb", _limb(1.0, 30), (5.0, 7.0))],
                            {"idle": (0.1, [draws])}, placement=PLACEMENT_CONTINUOUS)
    assert _split_symmetric_parts(flipbook, {("idle", 0): flipbook.recompose("idle", 0)}) is flipbook


def test_a_squash_scales_about_the_pivot_row():
    from ambition_sprite2d_renderer.authoring.rigdoc import squashed_sprite

    art = Image.new("RGBA", (10, 40), (0, 0, 0, 0))
    art.paste((200, 60, 60, 255), (2, 0, 8, 40))
    squashed, pivot = squashed_sprite(art, (5.0, 30.4), 0.5)
    alpha = [squashed.getpixel((4, y))[3] for y in range(squashed.height)]
    covered = [y for y, a in enumerate(alpha) if a >= 128]
    # 30 rows above the pivot become 15, 10 below become 5.
    assert pivot[1] == round(pivot[1]) and covered[0] == pivot[1] - 15 and covered[-1] == pivot[1] + 4


def test_a_half_keeps_a_transparent_border_on_its_cut_side():
    """The GPU filter reads past a part's rect into its atlas neighbour, so every
    part ends in transparent texels; a half cut flush ended opaque and drew a
    seam down Hunny Horror (2026-10-04)."""
    from ambition_sprite2d_renderer.authoring.part_flipbook import PART_BORDER

    part = _symmetric(34)
    draws = [PartDraw(0, (-10.0, -30.0), 0.3, (1.0, 1.0), "limb"), PartDraw(0, (14.0, -20.0), -1.1, (-1.0, 1.0), "limb2")]
    flipbook = PartFlipbook("sym", (96, 72), (48.0, 66.0), [PartRaster("limb", part, (5.0, 7.0))],
                            {"idle": (0.1, [draws])}, placement=PLACEMENT_CONTINUOUS)
    split = _split_symmetric_parts(flipbook, {("idle", 0): flipbook.recompose("idle", 0)})
    assert split is not flipbook
    alpha = split.parts[0].image.getchannel("A")
    width, height = alpha.size
    for x in range(width - PART_BORDER, width):
        assert max(alpha.getpixel((x, y)) for y in range(height)) == 0, f"column {x} of {width} is drawn"
