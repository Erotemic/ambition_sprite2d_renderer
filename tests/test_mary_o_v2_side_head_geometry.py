from __future__ import annotations

import math

import pytest
from PIL import Image

from ambition_sprite2d_renderer.targets.characters import mary_o_v2
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_art import (
    BLUSH,
    LIP,
    OUTLINE,
    RIBBON_PINK,
    WHITE,
    _SIDE_BACK_HAIR_RECT,
    _SIDE_BACK_NECK_HAIR_EDGE,
    _SIDE_BEANIE_DOME_BOX,
    _SIDE_HEAD_HAIR,
    _SIDE_HAIRLINE,
    _SIDE_HEAD_MIRROR_X,
    _SIDE_PONYTAIL_TIE_RECT,
    _SIDE_REAR_HAIR,
    _SIDE_UNDER_HAT_HAIR_RECT,
    _HEAD_BOTTOM_LOCAL,
    _debug_part_image,
    _draw_head_front,
    _draw_head_side,
    _draw_side_pose,
    _nose_tone,
    _side_head_feature_anchors,
)
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_model import (
    SHORT_POSES,
    TALL_LIKE_POSES,
)

_SCALE = 12
_HEAD_X = 8.0
_HEAD_Y = 4.0

#: ⭐⭐ **the pivots a re-proportioned head is scaled about**, matching
#: `_draw_head_side` and `_draw_head_front`. Every probe below is written in the
#: head's ORIGINAL local coordinates and mapped through this, because a form
#: with `head_scale != 1.0` draws the same head in a smaller frame — a probe
#: that skips the mapping is measuring where the head USED to be and reports a
#: transparent pixel as a missing feature.
_SIDE_HEAD_PIVOT = (5.05, _HEAD_BOTTOM_LOCAL)
_FRONT_HEAD_PIVOT = (5.5, _HEAD_BOTTOM_LOCAL)


def _head_scale(form) -> float:
    return getattr(form, "head_scale", 1.0)


def _sx(form, local_x: float) -> float:
    """A side-head local x, in pixels, following the form's head scale."""
    pivot = _SIDE_HEAD_PIVOT[0]
    return (_HEAD_X + pivot + (local_x - pivot) * _head_scale(form)) * _SCALE


def _sy(form, local_y: float) -> float:
    pivot = _SIDE_HEAD_PIVOT[1]
    return (_HEAD_Y + pivot + (local_y - pivot) * _head_scale(form)) * _SCALE


def _fx(form, head_x: float, local_x: float) -> float:
    pivot = _FRONT_HEAD_PIVOT[0]
    return (head_x + pivot + (local_x - pivot) * _head_scale(form)) * _SCALE


def _fy(form, head_y: float, local_y: float) -> float:
    pivot = _FRONT_HEAD_PIVOT[1]
    return (head_y + pivot + (local_y - pivot) * _head_scale(form)) * _SCALE


def _color_centroid(
    image: Image.Image,
    color: tuple[int, int, int, int],
) -> tuple[float, float]:
    pixels = image.load()
    points = [
        (x, y)
        for y in range(image.height)
        for x in range(image.width)
        if pixels[x, y] == color
    ]
    assert points, f"Expected rendered color {color!r}"
    return (
        sum(x for x, _ in points) / len(points),
        sum(y for _, y in points) / len(points),
    )


def _pairwise_squared_distances(
    points: list[tuple[float, float]],
) -> list[list[float]]:
    return [
        [
            (ax - bx) ** 2 + (ay - by) ** 2
            for bx, by in points
        ]
        for ax, ay in points
    ]


def _visible_hair_pixels(image: Image.Image, hair_color: tuple[int, int, int, int]) -> int:
    pixels = image.load()
    return sum(
        pixels[x, y] == hair_color
        for y in range(image.height)
        for x in range(image.width)
    )


def test_side_feature_anchor_gram_matrix_is_reflection_invariant() -> None:
    """All authored face features must undergo one rigid horizontal reflection."""
    east = _side_head_feature_anchors(lookback=False)
    west = _side_head_feature_anchors(lookback=True)
    names = sorted(east)

    for name in names:
        east_x, east_y = east[name]
        west_x, west_y = west[name]
        assert west_x == pytest.approx(2.0 * _SIDE_HEAD_MIRROR_X - east_x)
        assert west_y == pytest.approx(east_y)

    east_gram = _pairwise_squared_distances([east[name] for name in names])
    west_gram = _pairwise_squared_distances([west[name] for name in names])
    for east_row, west_row in zip(east_gram, west_gram):
        assert west_row == pytest.approx(east_row)


def test_rendered_side_features_are_rigidly_reflected() -> None:
    """Rendered mouth, eye, nose, and blush retain their relative geometry."""
    form = mary_o_v2.SHORT_FORM
    images = {
        lookback: _debug_part_image(
            lambda px, lookback=lookback: _draw_head_side(
                px,
                form,
                _HEAD_X,
                _HEAD_Y,
                lookback=lookback,
            ),
            logical_size=(24, 20),
            scale=_SCALE,
        )
        for lookback in (False, True)
    }
    colors = {
        "mouth": LIP,
        "eye": WHITE,
        "nose": _nose_tone(form),
        "blush": BLUSH,
    }
    east = {
        name: _color_centroid(images[False], color)
        for name, color in colors.items()
    }
    west = {
        name: _color_centroid(images[True], color)
        for name, color in colors.items()
    }
    mirror_px = _sx(form, _SIDE_HEAD_MIRROR_X)

    for name in colors:
        assert east[name][0] + west[name][0] == pytest.approx(2.0 * mirror_px, abs=1.0)
        # ⚠ a form with a non-integer `head_scale` puts the mirrored features
        # on a different sub-pixel phase, so the two orientations can land one
        # probe row apart. MEASURED: |Δy| is exactly 0.00px at `head_scale=1.0`
        # and 1.00px at 0.72, which is quantization, not a broken reflection —
        # the x-mirror and gram-matrix assertions above stay tight either way.
        rows = 0.5 if _head_scale(form) == 1.0 else 1.0
        assert west[name][1] == pytest.approx(east[name][1], abs=rows)

    east_gram = _pairwise_squared_distances(list(east.values()))
    west_gram = _pairwise_squared_distances(list(west.values()))
    for east_row, west_row in zip(east_gram, west_gram):
        assert west_row == pytest.approx(east_row, abs=40.0)

    def front_edge(image: Image.Image, *, lookback: bool) -> int:
        pixels = image.load()
        xs = [
            x
            for y in range(round(_sy(form, 5.05)), round(_sy(form, 7.00)) + 1)
            for x in range(image.width)
            if pixels[x, y] == form.palette.skin
        ]
        assert xs
        return min(xs) if lookback else max(xs)

    east_front = front_edge(images[False], lookback=False)
    west_front = front_edge(images[True], lookback=True)
    east_mouth_clearance = east_front - east["mouth"][0]
    west_mouth_clearance = west["mouth"][0] - west_front
    assert west_mouth_clearance == pytest.approx(east_mouth_clearance, abs=1.0)


def test_canonical_side_hair_is_adapted_from_v1_geometry() -> None:
    """Keep the old Mary hair construction while retaining the clean v2 head."""
    assert _SIDE_REAR_HAIR == (
        (1.00, 3.20),
        (-3.30, 8.30),
        (-2.10, 13.80),
        (1.60, 11.90),
    )
    assert _SIDE_HAIRLINE == (
        (2.40, 4.80),
        (5.10, 4.80),
        (3.20, 7.20),
    )
    # The cleaned face starts 0.68 units farther back than v1, so only the rear
    # edge of the old head-hair polygon is shifted by that amount. This preserves
    # the old visible back strip without moving hair in front of the face.
    assert _SIDE_HEAD_HAIR == (
        (1.32, 2.90),
        (9.45, 3.20),
        (8.85, 10.85),
        (0.82, 10.60),
    )
    assert _SIDE_BACK_HAIR_RECT == (1.32, 4.75, 2.55, 10.90)
    assert _SIDE_UNDER_HAT_HAIR_RECT == (1.05, 3.80, 8.95, 5.40)
    assert _SIDE_PONYTAIL_TIE_RECT == (0.48, 4.62, 1.58, 5.62)
    assert _SIDE_BEANIE_DOME_BOX == (1.05, -0.55, 8.95, 3.65)
    assert _SIDE_BACK_NECK_HAIR_EDGE == (
        (2.55, 5.00),
        (2.55, 10.90),
        (1.72, 11.22),
    )
    # The triangle and the visible rear rectangle deliberately overlap so no
    # skin-colored gap can appear between them after rasterization.
    assert _SIDE_HAIRLINE[0][0] <= _SIDE_BACK_HAIR_RECT[2]
    assert _SIDE_HAIRLINE[0][1] <= _SIDE_UNDER_HAT_HAIR_RECT[3]


@pytest.mark.parametrize(
    "form",
    [mary_o_v2.SHORT_FORM, mary_o_v2.TALL_FORM, mary_o_v2.FIRE_FORM],
)
def test_back_hair_volume_is_orientation_consistent(form) -> None:
    """The adapted v1 hair must remain a rigidly reflected side silhouette."""
    areas = []
    for lookback in (False, True):
        image = _debug_part_image(
            lambda px, lookback=lookback: _draw_head_side(
                px,
                form,
                _HEAD_X,
                _HEAD_Y,
                lookback=lookback,
            ),
            logical_size=(24, 20),
            scale=_SCALE,
        )
        pixels = image.load()
        mirror_px = round(_sx(form, _SIDE_HEAD_MIRROR_X))
        area = sum(
            pixels[x, y] == form.palette.hair
            and (x < mirror_px if not lookback else x > mirror_px)
            for y in range(image.height)
            for x in range(image.width)
        )
        areas.append(area)

    # ⚠ the short form's figure is NOT the others scaled by `head_scale`: it also
    # carries `hair_drop = 0.52`, which deliberately cuts the ponytail short
    # ("a one-brick character cannot wear a two-brick ponytail"), so its area is
    # below what the scale alone would predict. Re-recorded, not derived.
    minimum_area = {
        "mary_o_v2": 1250,
        "mary_o_v2_tall": 3050,
        "mary_o_v2_fire": 2950,
    }[form.target_name]
    assert min(areas) >= minimum_area
    assert max(areas) / min(areas) <= 1.03


@pytest.mark.parametrize("lookback", [False, True])
def test_v1_back_hair_strip_is_continuous_and_poof_is_wider(lookback: bool) -> None:
    """The old silhouette has a visible rear strip feeding a wider ponytail.

    ⚠ **this runs on the GROWN form, which is the one that still makes the
    claim.** The short form was given `hair_drop = 0.52` on purpose, so its
    ponytail stops above where the poof used to be — MEASURED, its rear span
    runs 26→41 between local y 5.0 and 6.0 and then falls to 6 below 8.5, where
    the grown form widens all the way to 57. Asserting a stem-to-poof read there
    would be asserting the shape the re-proportioning deliberately removed.
    `test_short_form_ponytail_is_shortened_not_missing` covers it instead.
    """
    form = mary_o_v2.TALL_FORM
    image = _debug_part_image(
        lambda px: _draw_head_side(
            px,
            form,
            _HEAD_X,
            _HEAD_Y,
            lookback=lookback,
        ),
        logical_size=(24, 20),
        scale=_SCALE,
    )
    pixels = image.load()

    def oriented_x(local_x: float) -> int:
        # ⚠ mirror in LOCAL space, then scale. The two commute (the scale pivot
        # reflects onto the scaled mirror), so this is the same point either way.
        if lookback:
            local_x = 2.0 * _SIDE_HEAD_MIRROR_X - local_x
        return round(_sx(form, local_x))

    # Every row from beneath the cap to the lower head must contain hair in the
    # one-unit strip immediately behind the skin boundary.
    strip_x1, strip_x2 = sorted((oriented_x(0.72), oriented_x(1.82)))
    for local_y in (5.0, 6.0, 7.0, 8.0, 9.0, 10.0):
        y = round(_sy(form, local_y))
        assert any(
            pixels[x, y] == form.palette.hair
            for x in range(strip_x1, strip_x2 + 1)
        ), local_y

    # Measure the rear hair span at the narrow upper connection and through the
    # lower ponytail body. The latter must be materially wider, which is the old
    # stem-to-poof read the newer variants had lost.
    face_back = oriented_x(1.82)

    def rear_span(local_y: float) -> int:
        y = round(_sy(form, local_y))
        if lookback:
            xs = [
                x for x in range(face_back, image.width)
                if pixels[x, y] == form.palette.hair
            ]
        else:
            xs = [
                x for x in range(0, face_back + 1)
                if pixels[x, y] == form.palette.hair
            ]
        assert xs
        return max(xs) - min(xs) + 1

    upper_span = rear_span(5.5)
    poof_span = rear_span(9.5)
    assert poof_span >= upper_span * 1.9


@pytest.mark.parametrize("lookback", [False, True])
def test_short_form_ponytail_is_shortened_not_missing(lookback: bool) -> None:
    """The short form keeps a full-width rear strip and loses only the tail.

    Guards both halves of the decision at once: shortening it must not thin the
    hair the face sits against, and must not leave the tail hanging at grown-form
    length on a one-brick character.
    """
    form = mary_o_v2.SHORT_FORM
    image = _debug_part_image(
        lambda px: _draw_head_side(px, form, _HEAD_X, _HEAD_Y, lookback=lookback),
        logical_size=(24, 20),
        scale=_SCALE,
    )
    pixels = image.load()

    def rear_span(local_y: float) -> int:
        local_back = 1.82
        if lookback:
            local_back = 2.0 * _SIDE_HEAD_MIRROR_X - local_back
        back = round(_sx(form, local_back))
        y = round(_sy(form, local_y))
        span = range(back, image.width) if lookback else range(0, back + 1)
        xs = [x for x in span if pixels[x, y] == form.palette.hair]
        return (max(xs) - min(xs) + 1) if xs else 0

    assert rear_span(6.0) >= 30, "the rear hair the face sits against went thin"
    assert rear_span(9.5) <= 12, "the tail is still hanging at grown-form length"


@pytest.mark.parametrize("lookback", [False, True])
def test_back_hair_is_in_front_of_face_but_under_the_hat(lookback: bool) -> None:
    """The visible rear rectangle must cover skin while remaining hat-tucked."""
    form = mary_o_v2.SHORT_FORM
    image = _debug_part_image(
        lambda px: _draw_head_side(
            px,
            form,
            _HEAD_X,
            _HEAD_Y,
            lookback=lookback,
        ),
        logical_size=(24, 20),
        scale=_SCALE,
    )
    pixels = image.load()

    def point(local_x: float, local_y: float) -> tuple[int, int]:
        if lookback:
            local_x = 2.0 * _SIDE_HEAD_MIRROR_X - local_x
        return (round(_sx(form, local_x)), round(_sy(form, local_y)))

    # This point lies inside the v2 skin polygon, so it can only be hair if the
    # rear rectangle is drawn after the face.
    assert pixels[point(2.20, 8.00)] == form.palette.hair
    # The shallow wide strip should leave a tiny row of hair immediately below
    # the band, while the band itself still covers the same x coordinate.
    assert pixels[point(3.60, 5.05)] == form.palette.hair
    # The widened strip also reaches farther toward the forehead and remains
    # visible below the band as a small top hairline.
    assert pixels[point(5.20, 5.30)] == form.palette.hair
    assert pixels[point(3.60, 4.50)] == form.palette.accent


@pytest.mark.parametrize("lookback", [False, True])
def test_ponytail_has_simple_pink_tie(lookback: bool) -> None:
    """A compact pink band should remain visible at the ponytail root."""
    form = mary_o_v2.SHORT_FORM
    image = _debug_part_image(
        lambda px: _draw_head_side(
            px,
            form,
            _HEAD_X,
            _HEAD_Y,
            lookback=lookback,
        ),
        logical_size=(24, 20),
        scale=_SCALE,
    )
    pixels = image.load()

    local_x = 1.02
    if lookback:
        local_x = 2.0 * _SIDE_HEAD_MIRROR_X - local_x
    cx = round(_sx(form, local_x))
    cy = round(_sy(form, 5.15))
    assert pixels[cx, cy] == RIBBON_PINK

    pink_pixels = sum(
        pixels[x, y] == RIBBON_PINK
        for y in range(round(_sy(form, 4.70)), round(_sy(form, 5.65)) + 1)
        for x in range(image.width)
    )
    # area scales with the SQUARE of the head scale
    assert pink_pixels >= round(60 * _head_scale(form) ** 2)


@pytest.mark.parametrize("lookback", [False, True])
def test_back_neck_hairline_outline_is_visible_in_front(lookback: bool) -> None:
    """The face-side edge of the neck hair must render as an outline."""
    form = mary_o_v2.SHORT_FORM
    image = _debug_part_image(
        lambda px: _draw_head_side(
            px,
            form,
            _HEAD_X,
            _HEAD_Y,
            lookback=lookback,
        ),
        logical_size=(24, 20),
        scale=_SCALE,
    )
    pixels = image.load()

    canonical_xs = (2.42, 2.68)
    oriented_xs = [
        2.0 * _SIDE_HEAD_MIRROR_X - local_x if lookback else local_x
        for local_x in canonical_xs
    ]
    x1, x2 = sorted(round(_sx(form, x)) for x in oriented_xs)
    y1 = round(_sy(form, 5.40))
    y2 = round(_sy(form, 10.70))
    outline_pixels = sum(
        pixels[x, y] == OUTLINE
        for y in range(y1, y2 + 1)
        for x in range(x1, x2 + 1)
    )
    assert outline_pixels >= 45


@pytest.mark.parametrize("lookback", [False, True])
def test_side_forehead_hairline_remains_visible(lookback: bool) -> None:
    """The side hairline should show a visible front wedge like the older art."""
    form = mary_o_v2.SHORT_FORM
    image = _debug_part_image(
        lambda px: _draw_head_side(
            px,
            form,
            _HEAD_X,
            _HEAD_Y,
            lookback=lookback,
        ),
        logical_size=(24, 20),
        scale=_SCALE,
    )
    pixels = image.load()
    canonical_xs = (2.50, 5.00)
    oriented_xs = [
        2.0 * _SIDE_HEAD_MIRROR_X - local_x if lookback else local_x
        for local_x in canonical_xs
    ]
    x1, x2 = sorted(round(_sx(form, x)) for x in oriented_xs)
    y1 = round(_sy(form, 4.85))
    y2 = round(_sy(form, 6.95))

    hair_pixels = sum(
        pixels[x, y] == form.palette.hair
        for y in range(y1, y2 + 1)
        for x in range(x1, x2 + 1)
    )
    assert hair_pixels >= round(180 * _head_scale(form) ** 2)


@pytest.mark.parametrize(
    ("form", "pose_table"),
    [
        (mary_o_v2.SHORT_FORM, SHORT_POSES),
        (mary_o_v2.TALL_FORM, TALL_LIKE_POSES),
        (mary_o_v2.FIRE_FORM, TALL_LIKE_POSES),
    ],
)
def test_visible_hair_volume_stays_consistent_across_poses(form, pose_table) -> None:
    """Pose layering must not accidentally erase most of the back hair."""
    idle = _debug_part_image(
        lambda px: _draw_side_pose(px, form, pose_table["idle"][0], animation="idle"),
        logical_size=(32, 32),
        scale=4,
    )
    idle_area = _visible_hair_pixels(idle, form.palette.hair)

    for animation, poses in pose_table.items():
        for frame_idx, pose in enumerate(poses):
            image = _debug_part_image(
                lambda px, pose=pose, animation=animation: _draw_side_pose(
                    px,
                    form,
                    pose,
                    animation=animation,
                ),
                logical_size=(32, 32),
                scale=4,
            )
            area = _visible_hair_pixels(image, form.palette.hair)
            assert area >= math.floor(idle_area * 0.58), (
                f"Hair disappeared in {animation}[{frame_idx}]: "
                f"area={area}, idle={idle_area}"
            )
            assert area <= math.ceil(idle_area * 1.12), (
                f"Hair unexpectedly grew in {animation}[{frame_idx}]: "
                f"area={area}, idle={idle_area}"
            )


def test_front_bangs_are_visible_above_the_eyes() -> None:
    """Preserve the original broad front-view fringe above the eyes."""
    form = mary_o_v2.SHORT_FORM
    head_x = 5.0
    head_y = 3.0
    image = _debug_part_image(
        lambda px: _draw_head_front(px, form, head_x, head_y),
        logical_size=(20, 18),
        scale=_SCALE,
    )
    pixels = image.load()
    x1 = round(_fx(form, head_x, 2.2))
    x2 = round(_fx(form, head_x, 8.8))
    y1 = round(_fy(form, head_y, 4.6))
    y2 = round(_fy(form, head_y, 6.1))
    bang_area = sum(
        pixels[x, y] == form.palette.hair
        for y in range(y1, y2 + 1)
        for x in range(x1, x2 + 1)
    )
    assert bang_area >= 300

    # The center lock should descend visibly while staying above the eyes.
    center_x = round(_fx(form, head_x, 5.5))
    center_ys = [
        y
        for y in range(y1, y2 + 1)
        if pixels[center_x, y] == form.palette.hair
    ]
    assert center_ys
    assert max(center_ys) >= round(_fy(form, head_y, 5.75))
