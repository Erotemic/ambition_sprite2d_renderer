"""Procedural artwork for Mary-O v2.

The public entry points in this module each own one visual responsibility. The
module intentionally preserves the accepted v2 pixels while removing the old
runtime aliasing / duplicate-definition pattern.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..super_mary_o_common import OUTLINE, WHITE, rasterize_logical
from ._mary_o_v2_model import (
    AURA_GOLD,
    AURA_PINK,
    BLUSH,
    BROOCH_GOLD,
    BROOCH_LIGHT,
    EMBER_CORE,
    EMBER_ORANGE,
    FIRE_FORM,
    FormSpec,
    LIP,
    MARY_NORMAL,
    Pose,
    RIBBON_PINK,
    SCALE,
    SHORT_FORM,
    WING_PEARL,
    _fire_accessory_t,
    _fire_transition_t,
    _lerp_rgba,
    _magic_stage_value,
)

def _debug_part_image(painter, *, logical_size=(24, 32), scale=8):
    """Render one drawing entry point on a transparent debug canvas."""
    return rasterize_logical(logical_size, scale, painter)


def _outlined_rect(px, x1, y1, x2, y2, *, fill, inset: float = 0.5) -> None:
    px.rect(x1, y1, x2, y2, fill=OUTLINE)
    ix1, iy1 = x1 + inset, y1 + inset
    ix2, iy2 = x2 - inset, y2 - inset
    if ix2 <= ix1 or iy2 <= iy1:
        px.rect(x1, y1, x2, y2, fill=fill)
        return
    px.rect(ix1, iy1, ix2, iy2, fill=fill)


def _ellipse_dome_points(
    x1: float,
    top_y: float,
    x2: float,
    base_y: float,
    *,
    steps: int = 20,
) -> list[tuple[float, float]]:
    """Return the upper half of an ellipse closed by its flat diameter."""
    cx = (x1 + x2) * 0.5
    rx = (x2 - x1) * 0.5
    ry = base_y - top_y
    arc = [
        (
            cx + rx * math.cos(math.pi + math.pi * idx / steps),
            base_y + ry * math.sin(math.pi + math.pi * idx / steps),
        )
        for idx in range(steps + 1)
    ]
    return [*arc, (x2, base_y), (x1, base_y)]


def _draw_ellipse_dome(
    px,
    x1: float,
    top_y: float,
    x2: float,
    base_y: float,
    *,
    fill,
    outline=OUTLINE,
    width: float = 0.7,
) -> None:
    """Draw a literal elliptical dome, not a full ellipse hidden by a band."""
    steps = 20
    points = _ellipse_dome_points(x1, top_y, x2, base_y, steps=steps)
    px.polygon(points, fill=fill, outline=None)
    px.line(points[: steps + 1], fill=outline, width=width)


def _segment_quad(x1: float, y1: float, x2: float, y2: float, half_w: float) -> List[Tuple[float, float]]:
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy) or 1.0
    ox = -dy / dist * half_w
    oy = dx / dist * half_w
    return [
        (x1 + ox, y1 + oy),
        (x2 + ox, y2 + oy),
        (x2 - ox, y2 - oy),
        (x1 - ox, y1 - oy),
    ]


def _draw_segment(px, x1: float, y1: float, x2: float, y2: float, *, half_w: float, fill) -> None:
    px.polygon(_segment_quad(x1, y1, x2, y2, half_w), fill=fill, outline=OUTLINE, width=0.55)


def _rotated_endpoint(pivot_x: float, pivot_y: float, angle_deg: float, length: float) -> Tuple[float, float]:
    radians = math.radians(angle_deg)
    return (
        pivot_x + math.sin(radians) * length,
        pivot_y + math.cos(radians) * length,
    )


def _draw_star(px, cx: float, cy: float, *, outer: float, inner: float, fill, outline=OUTLINE, width: float = 0.45) -> None:
    pts: List[Tuple[float, float]] = []
    for idx in range(10):
        angle = math.radians(-90 + idx * 36)
        radius = outer if idx % 2 == 0 else inner
        pts.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    px.polygon(pts, fill=fill, outline=outline, width=width)


def _draw_ribbon_tail(px, x: float, y: float, *, flip: bool, fill, long: bool = False) -> None:
    sign = -1.0 if flip else 1.0
    loop_dx = 1.5 * sign
    px.polygon(
        [(x, y), (x + loop_dx, y - 1.0), (x + loop_dx * 1.2, y + 0.9)],
        fill=fill,
        outline=OUTLINE,
        width=0.45,
    )
    px.polygon(
        [(x, y), (x + loop_dx, y + 1.0), (x + loop_dx * 1.1, y + 2.1)],
        fill=fill,
        outline=OUTLINE,
        width=0.45,
    )
    tail_len = 4.2 if long else 3.0
    px.polygon(
        [(x, y + 0.4), (x + sign * 0.9, y + 2.0), (x + sign * 0.4, y + tail_len), (x - sign * 0.3, y + 2.6)],
        fill=fill,
        outline=OUTLINE,
        width=0.45,
    )

_SIDE_HEAD_MIRROR_X = 5.05
_NATIVE_PIXEL = 1.0 / SCALE
_SIDE_EYE_OUTER_BOX = (6.00, 6.00, 7.333333333333333, 7.333333333333333)
_SIDE_EYE_WHITE_BOX = (6.333333333333333, 6.333333333333333, 7.00, 7.00)
_SIDE_EYE_PUPIL_BOX = (7.00, 6.333333333333333, 7.00, 7.00)


def _snap_native(value: float) -> float:
    """Snap logical coordinates to the native three-pixels-per-unit grid."""
    return round(value * SCALE) / SCALE


def _snap_side_head_origin(x: float, y: float) -> tuple[float, float]:
    """Keep the complete head on one native-pixel translation lattice."""
    return _snap_native(x), _snap_native(y)


def _orient_side_x(local_x: float, *, lookback: bool) -> float:
    """Reflect a side-head x coordinate around the authored head center."""
    return (2.0 * _SIDE_HEAD_MIRROR_X - local_x) if lookback else local_x


def _orient_side_points(
    points: tuple[tuple[float, float], ...] | list[tuple[float, float]],
    *,
    x: float,
    y: float,
    lookback: bool,
) -> list[tuple[float, float]]:
    return [
        (x + _orient_side_x(local_x, lookback=lookback), y + local_y)
        for local_x, local_y in points
    ]


def _orient_side_box(
    box: tuple[float, float, float, float],
    *,
    x: float,
    y: float,
    lookback: bool,
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = box
    ox1 = _orient_side_x(x1, lookback=lookback)
    ox2 = _orient_side_x(x2, lookback=lookback)
    return (x + min(ox1, ox2), y + y1, x + max(ox1, ox2), y + y2)


def _side_head_feature_anchors(*, lookback: bool = False) -> dict[str, tuple[float, float]]:
    """Return canonical face-feature anchors after the side-view reflection."""
    canonical = {
        "forehead": (8.90, 5.85),
        "nose_tip": (9.58, 7.80),
        "nose_shadow": (8.97, 8.01),
        "eye": (6.75, 6.75),
        "pupil": (7.10, 6.75),
        "brow": (7.80, 5.90),
        "blush": (5.25, 8.20),
        "mouth": (8.15, 9.25),
        "ear_star": (2.60, 8.00),
        "beanie_back": (1.10, 4.20),
        "beanie_front": (8.95, 4.20),
    }
    return {
        name: (_orient_side_x(px, lookback=lookback), py)
        for name, (px, py) in canonical.items()
    }


_SIDE_PROFILE_SKIN = (
    (1.82, 4.80),
    (8.90, 4.80),
    (8.90, 7.18),
    (9.58, 7.18),
    (9.58, 8.42),
    (8.90, 8.42),
    (8.90, 11.10),
    (1.82, 11.10),
)

# Adapt the original Super Mary-O side hair into the canonical v2 head.  The
# old silhouette came from two overlapping masses: a large four-point rear
# ponytail and a head-hair polygon whose back edge remained visible beside the
# skin.  Keep that same construction rather than inventing a new poof.
_SIDE_REAR_HAIR = (
    (1.00, 3.20),
    (-3.30, 8.30),
    (-2.10, 13.80),
    (1.60, 11.90),
)
_SIDE_HEAD_HAIR = (
    # Keep the old broad hair foundation behind the face.  The visible rear
    # rectangle is drawn separately after the skin so its face-side edge reads.
    (1.32, 2.90),
    (9.45, 3.20),
    (8.85, 10.85),
    (0.82, 10.60),
)
_SIDE_BACK_HAIR_RECT = (1.32, 4.75, 2.55, 10.90)
# A wider, slightly deeper strip keeps a visible line of hair emerging from
# beneath the beanie instead of letting the hat appear glued to bare skin.
_SIDE_HAT_TRIM_RECT = (1.05, 3.20, 8.95, 4.80)
_SIDE_UNDER_HAT_HAIR_RECT = (1.05, 3.80, 8.95, 5.40)
# Simple pink band around the ponytail root, adapted from the original Mary-O
# ribbon attachment but kept deliberately compact in every power form.
_SIDE_PONYTAIL_TIE_RECT = (0.48, 4.62, 1.58, 5.62)
_SIDE_BEANIE_DOME_BOX = (1.05, -0.55, 8.95, 3.65)
_FRONT_HAT_TRIM_RECT = (1.25, 3.30, 9.75, 4.90)
_FRONT_UNDER_HAT_HAIR_RECT = (1.25, 3.90, 9.75, 5.50)
_SIDE_BACK_NECK_HAIR_EDGE = (
    (2.55, 5.00),
    (2.55, 10.90),
    (1.72, 11.22),
)
_SIDE_HAIRLINE = (
    # Direct adaptation of the original side-view triangle.  Its rear corner
    # overlaps the front edge of the visible hair rectangle so the two masses
    # read as one continuous hairstyle.
    (2.40, 4.80),
    (5.10, 4.80),
    (3.20, 7.20),
)


def _side_profile_skin_polygon(x: float, y: float, *, lookback: bool = False) -> list[tuple[float, float]]:
    """Return the side-face silhouette as an exact horizontal reflection."""
    return _orient_side_points(_SIDE_PROFILE_SKIN, x=x, y=y, lookback=lookback)


def _draw_side_profile_nose_shadow(px, form: FormSpec, x: float, y: float, *, lookback: bool = False) -> None:
    """A tiny underside tint gives the silhouette step a nose read."""
    px.rect(
        *_orient_side_box(
            (8.74, 7.82, 9.20, 8.20),
            x=x,
            y=y,
            lookback=lookback,
        ),
        fill=_nose_tone(form),
    )


def _draw_head_foundation_side(px, form: FormSpec, x: float, y: float, *, lookback: bool = False) -> None:
    """Draw one canonical side head and reflect it rigidly for lookback."""
    pal = form.palette
    px.polygon(
        _orient_side_points(_SIDE_REAR_HAIR, x=x, y=y, lookback=lookback),
        fill=pal.hair,
        outline=OUTLINE,
        width=0.75,
    )
    px.polygon(
        _orient_side_points(_SIDE_HEAD_HAIR, x=x, y=y, lookback=lookback),
        fill=pal.hair,
        outline=OUTLINE,
        width=0.75,
    )

    if form.magic_stage >= 1:
        ribbon_x = x + _orient_side_x(1.20, lookback=lookback)
        _draw_ribbon_tail(
            px,
            ribbon_x,
            y + 4.20,
            flip=not lookback,
            fill=RIBBON_PINK,
            long=form.magic_stage >= 2,
        )
        if form.magic_stage >= 2:
            px.polygon(
                _orient_side_points(
                    ((-0.80, 1.50), (-2.80, 2.70), (-1.50, 4.30)),
                    x=x,
                    y=y,
                    lookback=lookback,
                ),
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.4,
            )

    px.polygon(
        _side_profile_skin_polygon(x, y, lookback=lookback),
        fill=pal.skin,
        outline=OUTLINE,
        width=0.35,
    )
    _draw_side_profile_nose_shadow(px, form, x, y, lookback=lookback)

    # The visible back-hair strip belongs in front of the skin but behind the
    # beanie.  Also duplicate the hat-band rectangle as a slightly lowered hair
    # strip so more hair protrudes from under the hat across the full head.
    px.rect(
        *_orient_side_box(_SIDE_BACK_HAIR_RECT, x=x, y=y, lookback=lookback),
        fill=pal.hair,
    )
    px.rect(
        *_orient_side_box(_SIDE_UNDER_HAT_HAIR_RECT, x=x, y=y, lookback=lookback),
        fill=pal.hair,
    )
    px.polygon(
        _orient_side_points(_SIDE_HAIRLINE, x=x, y=y, lookback=lookback),
        fill=pal.hair,
        outline=OUTLINE,
        width=0.35,
    )
    px.line(
        _orient_side_points(_SIDE_BACK_NECK_HAIR_EDGE, x=x, y=y, lookback=lookback),
        fill=OUTLINE,
        width=0.45,
    )
    _outlined_rect(
        px,
        *_orient_side_box(_SIDE_PONYTAIL_TIE_RECT, x=x, y=y, lookback=lookback),
        fill=RIBBON_PINK,
        inset=0.16,
    )

    # Draw a literal upper-half ellipse whose diameter sits behind the band.
    # This is a true dome, rather than a full ellipse cropped by the band.
    dome_x1, dome_top, dome_x2, dome_base = _orient_side_box(
        _SIDE_BEANIE_DOME_BOX,
        x=x,
        y=y,
        lookback=lookback,
    )
    _draw_ellipse_dome(
        px,
        dome_x1,
        dome_top,
        dome_x2,
        dome_base,
        fill=pal.cap,
        width=0.7,
    )
    _outlined_rect(
        px,
        *_orient_side_box(_SIDE_HAT_TRIM_RECT, x=x, y=y, lookback=lookback),
        fill=pal.accent,
        inset=0.25,
    )
    seam_x = x + _orient_side_x(1.10, lookback=lookback)
    px.line([(seam_x, y + 3.45), (seam_x, y + 5.00)], fill=OUTLINE, width=0.35)

    if form.magic_stage >= 1:
        badge_x = x + _orient_side_x(6.30, lookback=lookback)
        _draw_star(
            px,
            badge_x,
            y + 2.40,
            outer=1.4 if form.magic_stage >= 2 else 1.1,
            inner=0.55,
            fill=BROOCH_GOLD,
        )

    # Draw the eye as an explicit native-pixel sprite.  The old fractional
    # outlined rectangle could quantize to different border thicknesses when
    # the head moved by a fraction of a logical unit between poses.
    px.rect(
        *_orient_side_box(_SIDE_EYE_OUTER_BOX, x=x, y=y, lookback=lookback),
        fill=OUTLINE,
    )
    px.rect(
        *_orient_side_box(_SIDE_EYE_WHITE_BOX, x=x, y=y, lookback=lookback),
        fill=WHITE,
    )
    px.rect(
        *_orient_side_box(_SIDE_EYE_PUPIL_BOX, x=x, y=y, lookback=lookback),
        fill=OUTLINE,
    )
    px.line(
        _orient_side_points(((7.40, 6.10), (8.20, 5.70)), x=x, y=y, lookback=lookback),
        fill=OUTLINE,
        width=0.35,
    )

    if form.magic_stage >= 2:
        star_x = x + _orient_side_x(2.80, lookback=lookback)
        _draw_star(px, star_x, y + 6.0, outer=0.7, inner=0.3, fill=BROOCH_LIGHT, width=0.25)


def _draw_head_foundation_front(px, form: FormSpec, x: float, y: float) -> None:
    pal = form.palette
    px.polygon(
        [(x + 1.5, y + 3.0), (x - 1.5, y + 9.5), (x + 1.0, y + 14.0), (x + 4.5, y + 11.2)],
        fill=pal.hair,
        outline=OUTLINE,
        width=0.75,
    )
    px.polygon(
        [(x + 8.5, y + 3.0), (x + 11.5, y + 9.5), (x + 9.0, y + 14.0), (x + 5.5, y + 11.2)],
        fill=pal.hair,
        outline=OUTLINE,
        width=0.75,
    )
    if form.magic_stage >= 1:
        _draw_ribbon_tail(px, x + 1.3, y + 4.4, flip=True, fill=RIBBON_PINK, long=form.magic_stage >= 2)
        _draw_ribbon_tail(px, x + 9.7, y + 4.4, flip=False, fill=RIBBON_PINK, long=form.magic_stage >= 2)
    # Use the same literal upper-half ellipse in front view.
    _draw_ellipse_dome(
        px,
        x + 1.25,
        y - 0.45,
        x + 9.75,
        y + 3.75,
        fill=pal.cap,
        width=0.7,
    )
    px.rect(
        x + _FRONT_UNDER_HAT_HAIR_RECT[0],
        y + _FRONT_UNDER_HAT_HAIR_RECT[1],
        x + _FRONT_UNDER_HAT_HAIR_RECT[2],
        y + _FRONT_UNDER_HAT_HAIR_RECT[3],
        fill=pal.hair,
    )
    _outlined_rect(
        px,
        x + _FRONT_HAT_TRIM_RECT[0],
        y + _FRONT_HAT_TRIM_RECT[1],
        x + _FRONT_HAT_TRIM_RECT[2],
        y + _FRONT_HAT_TRIM_RECT[3],
        fill=pal.accent,
        inset=0.25,
    )
    if form.magic_stage >= 1:
        _draw_star(px, x + 5.4, y + 2.4, outer=1.5 if form.magic_stage >= 2 else 1.2, inner=0.6, fill=BROOCH_GOLD)
        if form.magic_stage >= 2:
            px.polygon(
                [(x + 0.8, y + 2.5), (x - 1.2, y + 3.3), (x + 0.1, y + 5.0)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.35,
            )
            px.polygon(
                [(x + 10.2, y + 2.5), (x + 12.2, y + 3.3), (x + 10.9, y + 5.0)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.35,
            )
    _outlined_rect(px, x + 1.8, y + 4.8, x + 9.2, y + 11.1, fill=pal.skin)
    px.polygon(
        [(x + 2.2, y + 4.6), (x + 8.8, y + 4.6), (x + 7.6, y + 6.2), (x + 3.4, y + 6.2)],
        fill=pal.hair,
        outline=OUTLINE,
        width=0.35,
    )
    _outlined_rect(px, x + 3.2, y + 6.5, x + 4.8, y + 7.6, fill=WHITE, inset=0.2)
    _outlined_rect(px, x + 6.0, y + 6.5, x + 7.6, y + 7.6, fill=WHITE, inset=0.2)
    _outlined_rect(px, x + 3.8, y + 6.8, x + 4.25, y + 7.3, fill=OUTLINE, inset=0.0)
    _outlined_rect(px, x + 6.7, y + 6.8, x + 7.15, y + 7.3, fill=OUTLINE, inset=0.0)


def _draw_short_body_side(px, form: FormSpec, x: float, y: float, crouch: float, *, compact: bool = False) -> None:
    pal = form.palette
    if compact:
        body_h = form.body_height - 0.72 * crouch
        body_w = form.body_width - 0.10 * min(crouch, 1.6)
    else:
        body_h = form.body_height - 0.55 * crouch
        body_w = form.body_width + 0.4 * min(crouch, 1.4)
    waist = y + body_h * 0.63
    if form.magic_stage >= 1:
        skirt_fill = pal.accent if form.magic_stage == 1 else pal.shirt
        hem_fill = pal.buttons if form.magic_stage == 1 else BROOCH_LIGHT
        px.polygon(
            [
                (x + 1.0, waist - 0.1),
                (x + 1.0 + body_w - 0.6, waist + 0.1),
                (x + 1.0 + body_w + 1.2, y + body_h + 1.9),
                (x + 0.5, y + body_h + 1.7),
            ],
            fill=skirt_fill,
            outline=OUTLINE,
            width=0.55,
        )
        px.line([(x + 1.5, y + body_h + 1.2), (x + 1.0 + body_w + 0.6, y + body_h + 1.2)], fill=hem_fill, width=0.6)
        px.polygon(
            [(x + 0.6, waist + 0.2), (x - 1.0, waist - 0.6), (x - 0.2, waist + 1.0)],
            fill=RIBBON_PINK if form.magic_stage == 1 else pal.buttons,
            outline=OUTLINE,
            width=0.35,
        )
        _outlined_rect(px, x + 4.1, y + body_h + 0.2, x + 5.0, y + body_h + 1.1, fill=pal.buttons, inset=0.18)
        _outlined_rect(px, x + 7.0, y + body_h + 0.2, x + 7.9, y + body_h + 1.1, fill=pal.buttons, inset=0.18)
    _outlined_rect(px, x + 1.0, y + 0.0, x + 1.0 + body_w, y + body_h, fill=pal.shirt)
    px.polygon(
        [
            (x + 2.0, y + 1.5),
            (x + 1.0 + body_w - 0.8, y + 1.5),
            (x + 1.0 + body_w, y + body_h + 0.9),
            (x + 1.0, y + body_h + 0.9),
        ],
        fill=pal.overalls,
        outline=OUTLINE,
        width=0.75,
    )
    px.line([(x + 2.3, y + 0.4), (x + 4.5, waist)], fill=pal.overalls, width=1.2)
    px.line([(x + 1.0 + body_w - 1.3, y + 0.4), (x + 6.3, waist)], fill=pal.overalls, width=1.2)
    px.line([(x + 2.0, waist), (x + 1.0 + body_w - 0.9, waist)], fill=OUTLINE, width=0.45)
    _outlined_rect(px, x + 3.5, y + 3.0, x + 4.5, y + 4.1, fill=pal.buttons, inset=0.2)
    _outlined_rect(px, x + 6.5, y + 3.0, x + 7.5, y + 4.1, fill=pal.buttons, inset=0.2)
    if form.magic_stage >= 1:
        _draw_star(px, x + 5.7, y + 2.3, outer=1.0 if form.magic_stage == 1 else 1.3, inner=0.45, fill=BROOCH_GOLD, width=0.35)
        px.polygon(
            [(x + 5.7, y + 2.9), (x + 4.6, y + 4.1), (x + 6.8, y + 4.1)],
            fill=RIBBON_PINK if form.magic_stage == 1 else pal.accent,
            outline=OUTLINE,
            width=0.3,
        )
        if form.magic_stage >= 2:
            px.polygon(
                [(x + 1.2, y + 1.2), (x - 0.9, y + 2.3), (x + 0.4, y + 5.4)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.35,
            )
            px.polygon(
                [(x + 10.2, y + 1.0), (x + 12.0, y + 2.2), (x + 9.8, y + 5.6)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.35,
            )
        _draw_suspender_fasteners_side(px, x, y, form)


def _draw_short_body_front(px, form: FormSpec, x: float, y: float, *, crouch: float = 0.0) -> None:
    pal = form.palette
    body_h = form.body_height - 0.55 * crouch
    body_w = form.body_width + 0.4 * min(crouch, 1.4)
    waist = y + body_h * 0.63
    if form.magic_stage >= 1:
        skirt_fill = pal.accent if form.magic_stage == 1 else pal.shirt
        hem_fill = pal.buttons if form.magic_stage == 1 else BROOCH_LIGHT
        px.polygon(
            [
                (x + 1.4, waist),
                (x + 1.2 + body_w - 0.2, waist),
                (x + 1.2 + body_w + 0.8, y + body_h + 1.9),
                (x + 0.4, y + body_h + 1.9),
            ],
            fill=skirt_fill,
            outline=OUTLINE,
            width=0.55,
        )
        px.line([(x + 1.0, y + body_h + 1.2), (x + 1.2 + body_w, y + body_h + 1.2)], fill=hem_fill, width=0.6)
        px.polygon(
            [(x + 1.2, waist + 0.2), (x - 0.9, waist - 0.6), (x - 0.1, waist + 1.2)],
            fill=RIBBON_PINK if form.magic_stage == 1 else pal.buttons,
            outline=OUTLINE,
            width=0.35,
        )
        px.polygon(
            [(x + 1.2 + body_w, waist + 0.2), (x + 3.3 + body_w, waist - 0.6), (x + 2.5 + body_w, waist + 1.2)],
            fill=RIBBON_PINK if form.magic_stage == 1 else pal.buttons,
            outline=OUTLINE,
            width=0.35,
        )
    _outlined_rect(px, x + 1.2, y + 0.0, x + 1.2 + body_w, y + body_h, fill=pal.shirt)
    px.polygon(
        [
            (x + 2.0, y + 1.4),
            (x + 1.2 + body_w - 0.8, y + 1.4),
            (x + 1.2 + body_w - 1.4, y + body_h + 0.8),
            (x + 2.8, y + body_h + 0.8),
        ],
        fill=pal.overalls,
        outline=OUTLINE,
        width=0.75,
    )
    px.line([(x + 3.2, y + 0.6), (x + 4.8, y + 4.6)], fill=pal.overalls, width=1.2)
    px.line([(x + 8.8, y + 0.6), (x + 7.2, y + 4.6)], fill=pal.overalls, width=1.2)
    _outlined_rect(px, x + 4.0, y + 2.8, x + 5.0, y + 4.0, fill=pal.buttons, inset=0.2)
    _outlined_rect(px, x + 7.0, y + 2.8, x + 8.0, y + 4.0, fill=pal.buttons, inset=0.2)
    if form.magic_stage >= 1:
        _draw_star(px, x + 5.9, y + 2.1, outer=1.0 if form.magic_stage == 1 else 1.35, inner=0.45, fill=BROOCH_GOLD, width=0.35)
        px.polygon(
            [(x + 5.9, y + 2.8), (x + 4.7, y + 4.1), (x + 7.1, y + 4.1)],
            fill=RIBBON_PINK if form.magic_stage == 1 else pal.accent,
            outline=OUTLINE,
            width=0.3,
        )
        if form.magic_stage >= 2:
            px.polygon(
                [(x + 1.4, y + 1.0), (x - 1.0, y + 2.0), (x + 1.0, y + 5.4)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.35,
            )
            px.polygon(
                [(x + 10.8, y + 1.0), (x + 13.2, y + 2.0), (x + 11.2, y + 5.4)],
                fill=pal.buttons,
                outline=OUTLINE,
                width=0.35,
            )

def _draw_suspender_fasteners_front(px, x: float, y: float, form: FormSpec) -> None:
    # Keep the classic overall-button read from the base Mary-O sprite.
    for cx in (x + 4.5, x + 7.5):
        px.ellipse(cx - 0.9, y + 2.65, cx + 0.9, y + 4.15, fill=form.palette.buttons, outline=OUTLINE, width=0.34)
        px.ellipse(cx - 0.28, y + 2.95, cx + 0.28, y + 3.50, fill=BROOCH_LIGHT, outline=None)


def _draw_suspender_fasteners_side(px, x: float, y: float, form: FormSpec) -> None:
    # Side views still keep two readable gold fasteners so the silhouette maps
    # back to the corresponding detail in the short/base form.
    for cx in (x + 4.15, x + 7.05):
        px.ellipse(cx - 0.84, y + 2.75, cx + 0.84, y + 4.18, fill=form.palette.buttons, outline=OUTLINE, width=0.34)
        px.ellipse(cx - 0.24, y + 3.02, cx + 0.24, y + 3.56, fill=BROOCH_LIGHT, outline=None)


def _draw_transform_outfit_stars(px, body_x: float, body_top: float, *, phase: int, form: FormSpec) -> None:
    star_fill = AURA_GOLD if form.magic_stage >= 2 else BROOCH_GOLD
    positions = [
        (body_x + 8.6, body_top + 2.2, 0.9),
        (body_x + 6.0, body_top + 6.3, 0.8),
        (body_x + 3.5, body_top + 9.2, 0.72),
    ]
    for sx, sy, outer in positions[: max(0, min(phase, len(positions)))]:
        _draw_star(px, sx, sy, outer=outer, inner=outer * 0.42, fill=star_fill, width=0.22)

def _draw_transform_aura(px, frame_idx: int) -> None:
    blast = min(frame_idx, 5)
    radii = [4.2, 5.2, 6.4, 7.6, 8.8, 8.0, 7.0, 6.0]
    rx = radii[frame_idx % len(radii)]
    ry = rx * 1.18
    cx, cy = 12.0, 12.8
    px.ellipse(cx - rx, cy - ry, cx + rx, cy + ry, fill=AURA_PINK, outline=None)
    px.ellipse(cx - rx * 0.78, cy - ry * 0.78, cx + rx * 0.78, cy + ry * 0.78, fill=AURA_GOLD, outline=None)
    if blast >= 3:
        px.ellipse(cx - rx * 0.48, cy - ry * 0.48, cx + rx * 0.48, cy + ry * 0.48, fill=(255, 248, 220, 255), outline=None)
    burst_sets = [
        [(2.6, 8.0, 1.0), (21.2, 8.0, 1.0), (12.0, 2.8, 0.9), (12.0, 21.0, 0.8)],
        [(2.0, 7.2, 1.15), (21.8, 7.2, 1.15), (4.5, 16.8, 0.8), (19.5, 16.8, 0.8), (12.0, 2.2, 1.0)],
        [(1.6, 6.2, 1.28), (22.2, 6.2, 1.28), (3.5, 15.8, 0.95), (20.3, 15.8, 0.95), (12.0, 1.8, 1.1), (12.0, 22.1, 0.95)],
        [(1.2, 5.5, 1.45), (22.8, 5.5, 1.45), (2.8, 14.8, 1.1), (21.0, 14.8, 1.1), (12.0, 1.2, 1.22), (12.0, 22.6, 1.0)],
        [(1.5, 5.8, 1.25), (22.5, 5.8, 1.25), (3.2, 14.5, 0.95), (20.8, 14.5, 0.95), (12.0, 1.5, 1.05)],
        [(2.5, 6.6, 1.0), (21.5, 6.6, 1.0), (4.2, 15.3, 0.75), (19.2, 15.3, 0.75)],
        [(3.6, 7.4, 0.8), (20.4, 7.4, 0.8), (5.6, 16.0, 0.65), (18.2, 16.0, 0.65)],
        [(4.2, 7.8, 0.65), (19.8, 7.8, 0.65), (6.0, 16.2, 0.55), (17.8, 16.2, 0.55)],
    ]
    for x, y, outer in burst_sets[frame_idx % len(burst_sets)]:
        fill = (255, 248, 220, 255) if outer >= 1.2 else (AURA_GOLD if outer >= 0.85 else AURA_PINK)
        _draw_star(px, x, y, outer=outer, inner=outer * 0.42, fill=fill, width=0.22)


def _draw_power_loss_sparkles(px, frame_idx: int, *, fire: bool = False) -> None:
    sparkle_sets = [
        [(6.0, 8.4, 0.7), (17.8, 9.2, 0.6), (11.8, 18.4, 0.5)],
        [(7.0, 10.1, 0.65), (18.0, 11.0, 0.55), (12.0, 19.6, 0.45)],
        [(8.4, 12.0, 0.55), (17.0, 13.0, 0.45)],
        [(9.4, 14.0, 0.5), (15.8, 14.8, 0.4)],
        [(10.3, 15.2, 0.42)],
        [],
    ]
    for x, y, outer in sparkle_sets[min(frame_idx, len(sparkle_sets) - 1)]:
        fill = AURA_GOLD if fire and outer >= 0.55 else AURA_PINK
        _draw_star(px, x, y, outer=outer, inner=max(0.2, outer * 0.42), fill=fill, width=0.22)
    if fire and frame_idx <= 3:
        # a few embers trail downward as the power drains away
        ember_sets = [
            [(18.8, 13.5), (20.3, 15.2)],
            [(18.1, 14.7), (19.4, 16.4)],
            [(17.2, 16.0)],
            [(16.4, 17.2)],
        ]
        for ex, ey in ember_sets[min(frame_idx, len(ember_sets) - 1)]:
            px.ellipse(ex - 0.55, ey - 0.55, ex + 0.55, ey + 0.55, fill=EMBER_ORANGE, outline=OUTLINE, width=0.2)


def _draw_dead_front(px, form: FormSpec, pose: Pose, *, wing_boost: float = 0.0) -> None:
    body_x = 6.0
    foot_y = 29.2 + pose.bob
    torso_bottom = foot_y - form.leg_height
    body_top = torso_bottom - form.body_height
    head_top = body_top - (9.8 if form.tall else 10.1)

    left_hip_x = body_x + 4.9
    right_hip_x = body_x + 7.3
    hip_y = torso_bottom + 0.3
    _draw_rotated_leg(
        px,
        left_hip_x,
        hip_y,
        form=form,
        angle_deg=-12.0,
        length=form.leg_height - 0.35,
        front=True,
    )
    _draw_rotated_leg(
        px,
        right_hip_x,
        hip_y,
        form=form,
        angle_deg=16.0,
        length=form.leg_height - 0.35,
        front=True,
    )

    _draw_wings_front(px, body_x + 6.0, body_top + 2.3, form=form, spread=wing_boost)
    _draw_body_front(px, form, body_x, body_top)
    head_x = body_x + 0.58
    _draw_head_front(px, form, head_x, head_top)
    _draw_dead_eyes_front(px, head_x, head_top)
    if pose.mode == "dead":
        if form.magic_stage >= 1:
            cover_fill = form.palette.overalls if form.magic_stage <= 1 else V2_IVORY
            px.polygon([(body_x + 2.25, body_top + 3.55), (body_x + 9.75, body_top + 3.55), (body_x + 8.95, body_top + 10.8), (body_x + 3.05, body_top + 10.8)], fill=cover_fill, outline=None)
            px.line([(body_x + 2.45, body_top + 4.15), (body_x + 9.2, body_top + 4.15)], fill=OUTLINE, width=0.34)
        _draw_dead_mouth_front(px, head_x, head_top)

    shoulder_y = body_top + 1.0
    _draw_rotated_arm(
        px,
        body_x + 3.0,
        shoulder_y,
        front=True,
        form=form,
        angle_deg=-118.0,
        length=4.9,
    )
    _draw_rotated_arm(
        px,
        body_x + 9.0,
        shoulder_y,
        front=True,
        form=form,
        angle_deg=118.0,
        length=4.9,
    )


def _side_pose_head_origin(form: FormSpec, pose: Pose) -> tuple[float, float, bool]:
    """Return the native-pixel-snapped head origin used by a side pose."""
    foot_y = 30.2 + pose.bob
    torso_bottom = foot_y - form.leg_height + 0.4 * pose.crouch
    body_top = torso_bottom - form.body_height + 0.6 * pose.crouch
    head_top = body_top - 10.0 + 0.8 * pose.crouch + pose.head_dy
    body_x = 7.0 + pose.body_lean
    if pose.mode == "swim":
        body_x = 6.3 + pose.body_lean
        head_top -= 0.6
    elif pose.mode == "crouch":
        body_x = 6.8 + pose.body_lean
    elif pose.mode == "climb":
        body_x = 6.4 + pose.body_lean
    head_x = body_x + 0.02 + pose.head_dx
    head_x, head_top = _snap_side_head_origin(head_x, head_top)
    return head_x, head_top, pose.mode == "lookback"


def _draw_side_pose(px, form: FormSpec, pose: Pose, *, animation: str = "idle", wing_boost: float = 0.0, sleeve_wing_boost: float = 0.0, extra_star_phase: int = 0) -> None:
    """Compose one complete side-facing character frame.

    Example:
        >>> from ambition_sprite2d_renderer.targets.characters.mary_o_v2 import *  # NOQA
        >>> image = _debug_part_image(
        >>>     lambda px: _draw_side_pose(px, TALL_FORM, Pose()))
        >>> # xdoctest: +REQUIRES(--show)
        >>> image.show()
    """
    stage = _magic_stage_value(form)
    fire_accessory_t = _fire_accessory_t(form)
    foot_y = 30.2 + pose.bob
    torso_bottom = foot_y - form.leg_height + 0.4 * pose.crouch
    body_top = torso_bottom - form.body_height + 0.6 * pose.crouch
    head_top = body_top - 10.0 + 0.8 * pose.crouch + pose.head_dy
    body_x = 7.0 + pose.body_lean

    if pose.mode == "swim":
        body_x = 6.3 + pose.body_lean
        head_top -= 0.6
    elif pose.mode == "crouch":
        body_x = 6.8 + pose.body_lean
    elif pose.mode == "climb":
        body_x = 6.4 + pose.body_lean

    compact_crouch = pose.mode == "crouch"
    body_w = (form.body_width - 0.10 * min(pose.crouch, 1.6)) if compact_crouch else (form.body_width + 0.4 * min(pose.crouch, 1.4))
    back_shoulder = (body_x + 1.8 + pose.arm_back_dx, body_top + 1.4 + pose.arm_back_dy)
    front_shoulder = (body_x + body_w - 0.2 + pose.arm_front_dx, body_top + 1.2 + pose.arm_front_dy)
    back_hip = (body_x + 3.0 + pose.leg_back_dx, torso_bottom + pose.leg_back_dy)
    front_hip = (body_x + 6.3 + pose.leg_front_dx, torso_bottom + pose.leg_front_dy)

    if pose.arm_back_angle is not None:
        _draw_rotated_arm(
            px,
            back_shoulder[0],
            back_shoulder[1],
            front=False,
            form=form,
            angle_deg=pose.arm_back_angle,
            length=4.4 if pose.mode != "climb" else 4.8,
        )
    else:
        _draw_arm(
            px,
            body_x - 1.4 + pose.arm_back_dx,
            body_top + 1.1 + pose.arm_back_dy,
            front=False,
            form=form,
            length=4.0,
        )

    if pose.leg_back_angle is not None:
        _draw_rotated_leg(
            px,
            back_hip[0],
            back_hip[1],
            form=form,
            angle_deg=pose.leg_back_angle,
            length=form.leg_height - 0.5 * pose.crouch,
            front=False,
        )
    else:
        _draw_leg(
            px,
            body_x + 2.1 + pose.leg_back_dx,
            torso_bottom + pose.leg_back_dy,
            form=form,
            length=form.leg_height - 0.6 * pose.crouch,
        )

    side_wing_boost = wing_boost + 0.45 * fire_accessory_t + (0.25 if animation == "fireball" else 0.0)
    sleeve_boost = sleeve_wing_boost + 0.85 * fire_accessory_t
    _draw_wing_side(px, body_x + 1.6, body_top + 3.4, form=form, spread=side_wing_boost)
    if stage >= 1.7:
        _draw_wing_side(px, body_x + 2.6, body_top + 5.1, form=form, spread=max(0.0, side_wing_boost - 0.15))
    if sleeve_boost > 0.0:
        _draw_sleeve_wing_side(px, back_shoulder[0] - 0.3, back_shoulder[1] + 1.1, form=form, strength=max(0.45, sleeve_boost * 0.8), facing=-1.0)

    # Keep the front leg tucked behind the dress / skirt silhouette in side view.
    if pose.leg_front_angle is not None:
        _draw_rotated_leg(
            px,
            front_hip[0],
            front_hip[1],
            form=form,
            angle_deg=pose.leg_front_angle,
            length=form.leg_height - 0.5 * pose.crouch,
            front=True,
        )
    else:
        _draw_leg(
            px,
            body_x + 5.1 + pose.leg_front_dx,
            torso_bottom + pose.leg_front_dy,
            form=form,
            length=form.leg_height - 0.6 * pose.crouch,
            front=True,
        )

    _draw_body_side(px, form, body_x, body_top, pose.crouch, compact=compact_crouch)
    if extra_star_phase > 0:
        _draw_transform_outfit_stars(px, body_x, body_top, phase=extra_star_phase, form=form)
    head_x, head_top, lookback = _side_pose_head_origin(form, pose)
    _draw_head_side(px, form, head_x, head_top, lookback=lookback)
    if pose.mode == "dead":
        # Restore the classic "oh no!" read and keep the ponytail behind the torso.
        _draw_dead_mouth_side(px, head_x, head_top, lookback=lookback)
        cover_fill = form.palette.overalls if form.magic_stage <= 1 else V2_IVORY
        px.polygon([(body_x + 0.6, body_top + 3.2), (body_x + 6.6, body_top + 3.5), (body_x + 5.9, body_top + 11.0), (body_x + 1.2, body_top + 10.8)], fill=cover_fill, outline=None)
        px.line([(body_x + 1.2, body_top + 4.0), (body_x + 5.8, body_top + 4.25)], fill=OUTLINE, width=0.34)

    if sleeve_boost > 0.0:
        _draw_sleeve_wing_side(px, front_shoulder[0] + 0.2, front_shoulder[1] + 1.0, form=form, strength=sleeve_boost, facing=1.0)
    if pose.arm_front_angle is not None:
        _draw_rotated_arm(
            px,
            front_shoulder[0],
            front_shoulder[1],
            front=True,
            form=form,
            angle_deg=pose.arm_front_angle,
            length=5.2 if pose.mode == "fireball" else (4.8 if pose.mode in {"swim", "climb"} else 4.4),
        )
    else:
        _draw_arm(
            px,
            body_x + 8.3 + pose.arm_front_dx,
            body_top + 0.8 + pose.arm_front_dy,
            front=True,
            form=form,
            length=4.0,
        )

    if form.power == "fire" and animation == "fireball":
        orb_x = front_shoulder[0] + 5.0
        orb_y = front_shoulder[1] + 0.8
        _draw_fire_orb(px, orb_x, orb_y)


V2_TEAL_DARK = (17, 91, 117, 255)
V2_TEAL_LIGHT = (40, 144, 172, 255)
V2_PINK_DARK = (184, 72, 121, 255)
V2_PINK_LIGHT = (229, 132, 180, 255)
V2_GOLD_DARK = (217, 126, 28, 255)
V2_GOLD = (255, 201, 64, 255)
V2_IVORY = (255, 250, 239, 255)
V2_ORANGE = (255, 116, 38, 255)
V2_ORANGE_DARK = (211, 70, 25, 255)


def _draw_v2_cap_badge(px, form: FormSpec, x: float, y: float, *, lookback: bool) -> None:
    cx = x + _orient_side_x(6.20, lookback=lookback)
    cy = y + 2.35
    ring = form.palette.buttons
    center = form.palette.cap if form.magic_stage < 2 else V2_ORANGE
    px.ellipse(cx - 1.15, cy - 1.05, cx + 1.15, cy + 1.05, fill=ring, outline=OUTLINE, width=0.35)
    _draw_star(px, cx, cy, outer=0.72, inner=0.31, fill=center, outline=OUTLINE, width=0.22)


def _draw_v2_hat_wing(px, form: FormSpec, x: float, y: float, *, lookback: bool) -> None:
    accessory_t = _fire_accessory_t(form)
    if accessory_t <= 0.0:
        return
    sign = 1.0 if lookback else -1.0
    anchor_x = x + _orient_side_x(1.45, lookback=lookback)
    anchor_y = y + 2.2
    outer = _lerp_rgba(V2_PINK_LIGHT, V2_GOLD, accessory_t)
    inner = _lerp_rgba(BROOCH_LIGHT, V2_IVORY, accessory_t)
    spans = (2.3 + 0.6 * accessory_t, 1.75 + 0.55 * accessory_t)
    if accessory_t >= 0.62:
        spans += (1.15 + 0.65 * accessory_t,)
    for i, span in enumerate(spans):
        dy = i * 0.75
        px.polygon(
            [
                (anchor_x, anchor_y + dy),
                (anchor_x + sign * span, anchor_y - 0.9 + dy),
                (anchor_x + sign * 0.45, anchor_y + 0.7 + dy),
            ],
            fill=outer if i % 2 == 0 else inner,
            outline=OUTLINE,
            width=0.3,
        )
    if accessory_t >= 0.55:
        lift = 1.5 + 1.0 * accessory_t
        px.polygon(
            [
                (anchor_x + sign * 0.1, anchor_y - 0.1),
                (anchor_x + sign * (0.4 + 0.5 * accessory_t), anchor_y - lift),
                (anchor_x + sign * (0.8 + 0.75 * accessory_t), anchor_y - 0.4),
            ],
            fill=V2_ORANGE,
            outline=OUTLINE,
            width=0.3,
        )


def _draw_v2_ear_star(px, form: FormSpec, x: float, y: float, *, lookback: bool) -> None:
    if _magic_stage_value(form) < 1:
        return
    cx = x + _orient_side_x(2.60, lookback=lookback)
    cy = y + 8.0
    outer = 0.72 + 0.16 * _fire_transition_t(form)
    _draw_star(px, cx, cy, outer=outer, inner=0.34, fill=form.palette.buttons, outline=OUTLINE, width=0.24)


def _add_side_blush(px, x: float, y: float, *, lookback: bool = False) -> None:
    px.rect(
        *_orient_side_box((4.75, 7.85, 5.75, 8.55), x=x, y=y, lookback=lookback),
        fill=BLUSH,
    )


def _nose_tone(form: FormSpec) -> tuple[int, int, int, int]:
    """Return a skin-derived nose shade distinct from the pink blush."""
    r, g, b, a = form.palette.skin
    return (max(0, r - 28), max(0, g - 30), max(0, b - 24), a)


@dataclass(frozen=True)
class NoseVariant:
    """A small nose design with independent front/profile silhouettes."""

    name: str
    description: str
    front_fill_path: tuple[tuple[float, float], ...]
    front_outline_path: tuple[tuple[float, float], ...]
    side_fill_path: tuple[tuple[float, float], ...]
    side_outline_path: tuple[tuple[float, float], ...]
    front_anchor: tuple[float, float]
    side_anchor: tuple[float, float]
    side_anchor_lookback: tuple[float, float] | None = None


def _make_nose_variants() -> Dict[str, NoseVariant]:
    # Keep the approved button-east front nose. The side profile now lives in
    # the face silhouette itself, so the side-specific path fields are empty.
    front_fill_path = (
        (-0.16, 0.00),
        (0.20, 0.00),
        (0.20, 0.92),
        (0.48, 1.04),
        (0.62, 1.26),
        (0.54, 1.50),
        (0.20, 1.66),
        (-0.12, 1.62),
        (-0.26, 1.36),
        (-0.20, 1.02),
        (-0.16, 0.00),
    )
    front_outline_path = (
        (0.02, 0.02),
        (0.02, 0.92),
        (0.22, 1.06),
        (0.34, 1.30),
        (0.24, 1.52),
        (0.02, 1.60),
    )
    return {
        "button_east_profile_step": NoseVariant(
            name="button_east_profile_step",
            description=(
                "Button-east front nose with a side-view nose integrated into "
                "the face silhouette."
            ),
            front_fill_path=front_fill_path,
            front_outline_path=front_outline_path,
            side_fill_path=(),
            side_outline_path=(),
            front_anchor=(5.62, 7.08),
            side_anchor=(0.0, 0.0),
            side_anchor_lookback=(0.0, 0.0),
        ),
    }


NOSE_VARIANTS = _make_nose_variants()
DEFAULT_NOSE_VARIANT = "button_east_profile_step"


def list_nose_variants() -> list[str]:
    return list(NOSE_VARIANTS)


def _resolve_nose_variant(variant_name: str | None) -> NoseVariant:
    name = DEFAULT_NOSE_VARIANT if variant_name is None else variant_name
    try:
        return NOSE_VARIANTS[name]
    except KeyError as ex:  # pragma: no cover - internal programming error
        raise KeyError(f"Unknown Mary-O v2 nose variant: {name!r}") from ex


def _nose_feature_scale(form: FormSpec) -> float:
    """Scale the nose with the authored face, never with output pixels."""
    return 0.96 if not form.tall else 1.08


def _transform_nose_path(points, *, anchor_x: float, anchor_y: float, scale: float, orientation: str):
    transformed = []
    for local_x, local_y in points:
        local_x *= scale
        local_y *= scale
        if orientation in {"front", "east"}:
            dx, dy = local_x, local_y
        elif orientation == "west":
            dx, dy = -local_x, local_y
        else:  # pragma: no cover - internal programming error
            raise KeyError(orientation)
        transformed.append((anchor_x + dx, anchor_y + dy))
    return transformed


def _draw_nose_path(
    px,
    form: FormSpec,
    *,
    fill_path: tuple[tuple[float, float], ...],
    outline_path: tuple[tuple[float, float], ...],
    anchor_x: float,
    anchor_y: float,
    orientation: str,
    close_silhouette: bool = False,
) -> None:
    """Draw a filled nose path in front/east/west orientation."""
    scale = _nose_feature_scale(form)
    fill_pts = _transform_nose_path(
        fill_path,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
        scale=scale,
        orientation=orientation,
    )
    outline_pts = _transform_nose_path(
        outline_path,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
        scale=scale,
        orientation=orientation,
    )
    polygon_outline = OUTLINE if (close_silhouette and outline_path) else None
    px.polygon(
        fill_pts,
        fill=_nose_tone(form),
        outline=polygon_outline,
        width=0.24 * scale,
    )
    if outline_path:
        px.line(outline_pts, fill=OUTLINE, width=0.24 * scale)


def _draw_side_nose(px, form: FormSpec, x: float, y: float, *, lookback: bool = False, variant_name: str | None = None) -> None:
    """Draw the side-profile nose as the tiny integrated silhouette step.

    Example:
        >>> from ambition_sprite2d_renderer.targets.characters.mary_o_v2 import *  # NOQA
        >>> image = _debug_part_image(
        >>>     lambda px: _draw_side_nose(px, TALL_FORM, 5.0, 5.0))
        >>> image.size
        (192, 256)
        >>> # xdoctest: +REQUIRES(--show)
        >>> image.show()
    """
    del variant_name  # Side-view geometry is now anchored in the head silhouette.
    px.polygon(
        _side_profile_skin_polygon(x, y, lookback=lookback),
        fill=form.palette.skin,
        outline=OUTLINE,
        width=0.35,
    )
    _draw_side_profile_nose_shadow(px, form, x, y, lookback=lookback)


def _draw_side_face_features(px, form: FormSpec, x: float, y: float, *, lookback: bool = False, variant_name: str | None = None) -> None:
    del form, variant_name
    _add_side_blush(px, x, y, lookback=lookback)
    px.line(
        _orient_side_points(((7.80, 9.25), (8.50, 9.25)), x=x, y=y, lookback=lookback),
        fill=LIP,
        width=0.28,
    )


def _draw_front_nose(px, form: FormSpec, x: float, y: float, *, variant_name: str | None = None) -> None:
    """Draw the shared nose straight down with a softly curled tip.

    Example:
        >>> from ambition_sprite2d_renderer.targets.characters.mary_o_v2 import *  # NOQA
        >>> image = _debug_part_image(
        >>>     lambda px: _draw_front_nose(px, TALL_FORM, 7.0, 7.0))
        >>> image.size
        (192, 256)
        >>> # xdoctest: +REQUIRES(--show)
        >>> image.show()
    """
    variant = _resolve_nose_variant(variant_name)
    _draw_nose_path(
        px,
        form,
        fill_path=variant.front_fill_path,
        outline_path=variant.front_outline_path,
        anchor_x=x + variant.front_anchor[0],
        anchor_y=y + variant.front_anchor[1],
        orientation="front",
    )


def _draw_front_face_features(px, form: FormSpec, x: float, y: float, *, variant_name: str | None = None) -> None:
    px.rect(x + 2.4, y + 7.5, x + 3.95, y + 8.5, fill=BLUSH)
    px.rect(x + 7.05, y + 7.5, x + 8.6, y + 8.5, fill=BLUSH)
    _draw_front_nose(px, form, x, y, variant_name=variant_name)
    px.line([(x + 4.78, y + 9.55), (x + 6.2, y + 9.55)], fill=LIP, width=0.28)

def _draw_dead_mouth_side(px, x: float, y: float, *, lookback: bool = False) -> None:
    px.ellipse(
        *_orient_side_box((7.35, 8.93, 8.55, 9.93), x=x, y=y, lookback=lookback),
        fill=LIP,
        outline=OUTLINE,
        width=0.22,
    )
    px.ellipse(
        *_orient_side_box((7.71, 9.18, 8.19, 9.72), x=x, y=y, lookback=lookback),
        fill=(56, 20, 34, 255),
        outline=None,
    )


def _draw_dead_mouth_front(px, x: float, y: float) -> None:
    px.ellipse(x + 4.72, y + 9.03, x + 6.38, y + 10.23, fill=LIP, outline=OUTLINE, width=0.22)
    px.ellipse(x + 5.10, y + 9.30, x + 6.00, y + 9.96, fill=(56, 20, 34, 255), outline=None)


def _draw_dead_eyes_front(px, x: float, y: float) -> None:
    for cx in (x + 3.95, x + 6.85):
        px.line([(cx - 0.60, y + 6.55), (cx + 0.60, y + 7.45)], fill=OUTLINE, width=0.26)
        px.line([(cx - 0.60, y + 7.45), (cx + 0.60, y + 6.55)], fill=OUTLINE, width=0.26)


def _draw_skid_dust(px, x: float, y: float) -> None:
    fill = (216, 202, 176, 255)
    px.polygon(
        [(x - 1.8, y + 0.4), (x - 0.4, y - 0.15), (x + 0.9, y + 0.55), (x - 0.2, y + 1.2)],
        fill=fill,
        outline=OUTLINE,
        width=0.22,
    )
    px.line([(x - 2.3, y + 0.9), (x - 1.2, y + 0.75)], fill=OUTLINE, width=0.20)
    px.line([(x - 2.0, y + 1.35), (x - 0.95, y + 1.08)], fill=OUTLINE, width=0.20)


def _draw_head_side(px, form: FormSpec, x: float, y: float, *, lookback: bool = False, variant_name: str | None = None) -> None:
    """Draw a complete side-facing head from foundation and features.

    Example:
        >>> from ambition_sprite2d_renderer.targets.characters.mary_o_v2 import *  # NOQA
        >>> image = _debug_part_image(
        >>>     lambda px: _draw_head_side(px, TALL_FORM, 6.0, 4.0))
        >>> # xdoctest: +REQUIRES(--show)
        >>> image.show()
    """
    # Snap the entire head as one rigid unit before rasterization.  This keeps
    # the eye and other small features on the same native-pixel phase in every
    # pose instead of allowing fractional head translations to alter borders.
    x, y = _snap_side_head_origin(x, y)
    _draw_head_foundation_side(px, form, x, y, lookback=lookback)
    _draw_side_face_features(px, form, x, y, lookback=lookback, variant_name=variant_name)
    if _magic_stage_value(form) <= 0:
        return
    _draw_v2_ear_star(px, form, x, y, lookback=lookback)
    _draw_v2_hat_wing(px, form, x, y, lookback=lookback)


def _draw_head_front(px, form: FormSpec, x: float, y: float, *, variant_name: str | None = None) -> None:
    _draw_head_foundation_front(px, form, x, y)
    _draw_front_face_features(px, form, x, y, variant_name=variant_name)
    accessory_t = _fire_accessory_t(form)
    if accessory_t > 0.0:
        for sign in (-1, 1):
            anchor = x + 5.4 + sign * 5.1
            span = 1.15 + 0.65 * accessory_t
            px.polygon(
                [(anchor, y + 2.5), (anchor + sign * span, y + 1.9 - 0.35 * accessory_t), (anchor + sign * 0.45, y + 3.45)],
                fill=_lerp_rgba(V2_PINK_LIGHT, V2_GOLD, accessory_t),
                outline=OUTLINE,
                width=0.28,
            )


def _draw_v2_button(px, cx: float, cy: float, fill) -> None:
    px.ellipse(cx - 0.78, cy - 0.72, cx + 0.78, cy + 0.72, fill=fill, outline=OUTLINE, width=0.32)
    px.ellipse(cx - 0.21, cy - 0.20, cx + 0.21, cy + 0.20, fill=BROOCH_LIGHT, outline=None)


def _draw_hand_outline(px, x1: float, y1: float, x2: float, y2: float) -> None:
    px.line([(x1, y1), (x2, y1)], fill=OUTLINE, width=0.34)
    px.line([(x1, y2), (x2, y2)], fill=OUTLINE, width=0.34)
    px.line([(x1, y1), (x1, y2)], fill=OUTLINE, width=0.34)
    px.line([(x2, y1), (x2, y2)], fill=OUTLINE, width=0.34)


def _draw_body_side(px, form: FormSpec, x: float, y: float, crouch: float, *, compact: bool = False) -> None:
    """Draw the authoritative side-view body for one form.

    Example:
        >>> from ambition_sprite2d_renderer.targets.characters._mary_o_v2_art import *  # NOQA
        >>> image = _debug_part_image(
        >>>     lambda px: _draw_body_side(px, FIRE_FORM, 6.0, 10.0, 0.0))
        >>> # xdoctest: +REQUIRES(--show)
        >>> image.show()
    """
    pal = form.palette
    stage = _magic_stage_value(form)
    fire_t = _fire_transition_t(form)
    accessory_t = _fire_accessory_t(form)
    body_h = form.body_height - 0.55 * crouch
    body_w = form.body_width + 0.4 * min(crouch, 1.4)
    waist = y + body_h * (0.58 if stage else 0.62)
    bottom = y + body_h

    # Shirt / blouse base.
    _outlined_rect(px, x + 1.0, y, x + 1.0 + body_w, waist + 0.7, fill=pal.shirt, inset=0.42)

    if stage == 0:
        return _draw_short_body_side(px, form, x, y, crouch, compact=compact)

    # Powered forms: integrated bodice, star centerpiece, and flared skirt.
    bodice_fill = pal.overalls
    px.polygon(
        [(x + 2.0, y + 1.1), (x + body_w + 0.05, y + 1.1), (x + body_w - 0.35, waist + 0.7), (x + 1.65, waist + 0.7)],
        fill=bodice_fill,
        outline=OUTLINE,
        width=0.7,
    )
    strap = _lerp_rgba(V2_TEAL_DARK, V2_GOLD_DARK, fire_t)
    px.line([(x + 2.5, y + 0.25), (x + 4.05, y + 3.0)], fill=strap, width=1.1)
    px.line([(x + body_w - 0.65, y + 0.25), (x + 7.05, y + 3.0)], fill=strap, width=1.1)
    _draw_v2_button(px, x + 4.05, y + 3.1, pal.buttons)
    _draw_v2_button(px, x + 7.05, y + 3.1, pal.buttons)

    flare = 1.45 + 0.55 * fire_t
    skirt_fill = _lerp_rgba(pal.overalls, V2_IVORY, fire_t)
    px.polygon(
        [
            (x + 1.7, waist + 0.4),
            (x + body_w + 0.25, waist + 0.4),
            (x + body_w + flare, bottom + 2.0),
            (x + 0.75 - flare * 0.25, bottom + 1.9),
        ],
        fill=skirt_fill,
        outline=OUTLINE,
        width=0.72,
    )
    hem = _lerp_rgba(V2_GOLD, V2_ORANGE, fire_t)
    px.line([(x + 1.0, bottom + 1.25), (x + body_w + flare - 0.4, bottom + 1.25)], fill=hem, width=0.82)
    if fire_t >= 0.72:
        # Keep the tall form closer to classic SMB1; only the late fire phase
        # gets the extra vertical pleat rhythm.
        pleat = _lerp_rgba(V2_TEAL_DARK, V2_GOLD_DARK, fire_t)
        px.line([(x + 4.0, waist + 0.8), (x + 3.65, bottom + 1.0)], fill=pleat, width=0.28)
        px.line([(x + 7.0, waist + 0.8), (x + 7.45, bottom + 1.0)], fill=pleat, width=0.28)

    _draw_star(px, x + 5.65, y + 4.25, outer=1.45 + 0.27 * fire_t, inner=0.68, fill=pal.buttons, width=0.34)
    # A small bow at the back echoes the generated second-draft concept.
    bow = _lerp_rgba(V2_PINK_LIGHT, V2_GOLD, fire_t)
    px.polygon([(x + 1.0, waist + 0.4), (x - 1.15, waist - 0.6), (x - 0.25, waist + 1.05)], fill=bow, outline=OUTLINE, width=0.32)
    px.polygon([(x + 0.9, waist + 0.55), (x - 0.35, waist + 2.0), (x + 1.2, waist + 1.25)], fill=bow, outline=OUTLINE, width=0.32)

    if accessory_t >= 0.5:
        # Flame-feather epaulettes ramp in during the late transform instead of
        # snapping on in a single frame.
        span = 1.2 + 0.8 * accessory_t
        for ax in (x + 0.9, x + body_w + 0.95):
            sign = -1.0 if ax < x + body_w / 2 else 1.0
            px.polygon([(ax, y + 1.0), (ax + sign * span, y + 0.6 - 0.5 * accessory_t), (ax + sign * 0.6, y + 2.6)], fill=V2_GOLD, outline=OUTLINE, width=0.32)
            px.polygon([(ax, y + 1.5), (ax + sign * (span + 0.4), y + 1.7), (ax + sign * 0.5, y + 3.0)], fill=V2_ORANGE, outline=OUTLINE, width=0.3)


def _draw_body_front(px, form: FormSpec, x: float, y: float, *, crouch: float = 0.0) -> None:
    pal = form.palette
    stage = _magic_stage_value(form)
    fire_t = _fire_transition_t(form)
    body_h = form.body_height - 0.55 * crouch
    body_w = form.body_width + 0.4 * min(crouch, 1.4)
    waist = y + body_h * (0.58 if stage else 0.62)
    bottom = y + body_h
    _outlined_rect(px, x + 1.2, y, x + 1.2 + body_w, waist + 0.7, fill=pal.shirt, inset=0.42)

    if stage == 0:
        return _draw_short_body_front(px, form, x, y, crouch=crouch)

    px.polygon([(x + 2.1, y + 1.0), (x + body_w + 0.3, y + 1.0), (x + body_w - 0.25, waist + 0.7), (x + 1.8, waist + 0.7)], fill=pal.overalls, outline=OUTLINE, width=0.7)
    strap = _lerp_rgba(V2_TEAL_DARK, V2_GOLD_DARK, fire_t)
    px.line([(x + 3.1, y + 0.25), (x + 4.7, y + 3.0)], fill=strap, width=1.1)
    px.line([(x + 9.0, y + 0.25), (x + 7.35, y + 3.0)], fill=strap, width=1.1)
    _draw_v2_button(px, x + 4.7, y + 3.1, pal.buttons)
    _draw_v2_button(px, x + 7.35, y + 3.1, pal.buttons)
    flare = 1.55 + 0.60 * fire_t
    skirt_fill = _lerp_rgba(pal.overalls, V2_IVORY, fire_t)
    px.polygon([(x + 1.8, waist + 0.35), (x + body_w + 0.55, waist + 0.35), (x + body_w + flare, bottom + 2.0), (x + 0.6 - flare * 0.2, bottom + 2.0)], fill=skirt_fill, outline=OUTLINE, width=0.72)
    px.line([(x + 0.9, bottom + 1.25), (x + body_w + flare - 0.2, bottom + 1.25)], fill=_lerp_rgba(V2_GOLD, V2_ORANGE, fire_t), width=0.82)
    _draw_star(px, x + 6.0, y + 4.15, outer=1.5 + 0.25 * fire_t, inner=0.7, fill=pal.buttons, width=0.34)


def _draw_arm(px, x: float, y: float, *, front: bool, form: FormSpec, length: float = 4.2, glove_down: bool = True) -> None:
    pal = form.palette
    glove_fill = pal.skin if form.magic_stage == 0 else pal.gloves
    sleeve_fill = pal.shirt
    if form.magic_stage >= 1:
        puff = RIBBON_PINK if form.magic_stage == 1 else V2_IVORY
        px.ellipse(x - 0.65, y - 0.4, x + 2.35, y + 2.5, fill=puff, outline=OUTLINE, width=0.42)
        if form.magic_stage >= 2:
            px.polygon([(x + 0.1, y - 0.2), (x + 0.8, y - 1.5), (x + 1.5, y - 0.1)], fill=V2_GOLD, outline=OUTLINE, width=0.28)
    _outlined_rect(px, x, y + (1.0 if form.magic_stage >= 1 else 0.0), x + 1.6, y + length, fill=sleeve_fill, inset=0.35)
    glove_y = y + (length - 0.5 if glove_down else -1.2)
    if form.magic_stage >= 1:
        cuff_fill = V2_GOLD if form.magic_stage >= 2 else form.palette.cap
        _outlined_rect(px, x - 0.2, glove_y - 0.9, x + 1.8, glove_y + 0.1, fill=cuff_fill, inset=0.14)
    _outlined_rect(px, x - 0.25, glove_y, x + 1.85, glove_y + 1.75, fill=glove_fill, inset=0.15)
    _draw_hand_outline(px, x - 0.3, glove_y - 0.02, x + 1.9, glove_y + 1.8)


def _draw_rotated_arm(px, shoulder_x: float, shoulder_y: float, *, front: bool, form: FormSpec, angle_deg: float, length: float = 4.4) -> None:
    pal = form.palette
    hand_fill = pal.skin if form.magic_stage == 0 else pal.gloves
    end_x, end_y = _rotated_endpoint(shoulder_x, shoulder_y, angle_deg, length)
    if form.magic_stage >= 1:
        puff = RIBBON_PINK if form.magic_stage == 1 else V2_IVORY
        px.ellipse(shoulder_x - 1.35, shoulder_y - 1.25, shoulder_x + 1.35, shoulder_y + 1.35, fill=puff, outline=OUTLINE, width=0.42)
        if form.magic_stage >= 2:
            px.polygon([(shoulder_x - 0.7, shoulder_y - 0.8), (shoulder_x, shoulder_y - 2.0), (shoulder_x + 0.7, shoulder_y - 0.8)], fill=V2_GOLD, outline=OUTLINE, width=0.28)
    _draw_segment(px, shoulder_x, shoulder_y, end_x, end_y, half_w=0.74, fill=pal.shirt)
    if form.magic_stage >= 1:
        cuff_x, cuff_y = _rotated_endpoint(shoulder_x, shoulder_y, angle_deg, max(0.0, length - 0.95))
        _draw_segment(px, cuff_x, cuff_y, end_x, end_y, half_w=0.92, fill=V2_GOLD if form.magic_stage >= 2 else form.palette.cap)
    _outlined_rect(px, end_x - 1.0, end_y - 0.9, end_x + 1.0, end_y + 0.9, fill=hand_fill, inset=0.15)
    _draw_hand_outline(px, end_x - 1.05, end_y - 0.95, end_x + 1.05, end_y + 0.95)


def _draw_leg(px, x: float, y: float, *, form: FormSpec, length: float = 5.2, front: bool = False) -> None:
    pal = form.palette
    leg_fill = V2_TEAL_DARK if form.magic_stage == 1 else pal.overalls
    _outlined_rect(px, x + 0.2, y, x + 2.0, y + length, fill=leg_fill, inset=0.34)
    if form.magic_stage >= 1:
        _outlined_rect(px, x - 0.05, y + length - 1.25, x + 2.25, y + length - 0.15, fill=V2_GOLD if form.magic_stage >= 2 else V2_PINK_LIGHT, inset=0.14)
    _outlined_rect(px, x - 0.55, y + length - 0.45, x + 3.05, y + length + 1.3, fill=pal.shoes, inset=0.2)
    px.line([(x + 1.55, y + length + 0.15), (x + 2.75, y + length + 0.15)], fill=BROOCH_LIGHT if form.magic_stage >= 1 else (139, 91, 55, 255), width=0.34)


def _draw_rotated_leg(px, hip_x: float, hip_y: float, *, form: FormSpec, angle_deg: float, length: float = 5.4, front: bool = False) -> None:
    pal = form.palette
    leg_fill = V2_TEAL_DARK if form.magic_stage == 1 else pal.overalls
    end_x, end_y = _rotated_endpoint(hip_x, hip_y, angle_deg, length)
    _draw_segment(px, hip_x, hip_y, end_x, end_y, half_w=0.88, fill=leg_fill)
    shoe_dir = 1.0 if math.sin(math.radians(angle_deg)) >= 0 else -1.0
    x1 = end_x - 0.5 if shoe_dir > 0 else end_x - 2.9
    x2 = end_x + 2.5 if shoe_dir > 0 else end_x + 0.5
    if form.magic_stage >= 1:
        _outlined_rect(px, x1 + 0.1, end_y - 1.35, x2 - 0.1, end_y - 0.1, fill=V2_GOLD if form.magic_stage >= 2 else V2_PINK_LIGHT, inset=0.14)
    _outlined_rect(px, x1, end_y - 0.4, x2, end_y + 1.05, fill=pal.shoes, inset=0.16)


def _draw_wing_side(px, anchor_x: float, anchor_y: float, *, form: FormSpec, spread: float = 0.0) -> None:
    if form.magic_stage < 1:
        return
    if form.magic_stage == 1:
        # A controlled three-feather shoulder wing: more designed, less noisy.
        lengths = (3.3 + spread, 2.8 + spread * 0.7, 2.2 + spread * 0.5)
        for i, length in enumerate(lengths):
            dy = i * 0.85
            px.polygon(
                [(anchor_x, anchor_y + dy), (anchor_x - length, anchor_y - 1.1 + dy), (anchor_x - 0.35, anchor_y + 0.8 + dy)],
                fill=V2_IVORY if i == 1 else V2_PINK_LIGHT,
                outline=OUTLINE,
                width=0.32,
            )
        return

    # Fire form: make the wings read clearly even against the ponytail. Use a
    # larger rear fan, a visible shoulder root, and a forward curl that always
    # peeks out past the torso silhouette.
    rear_lengths = (
        5.9 + spread * 1.20,
        5.1 + spread * 1.00,
        4.3 + spread * 0.85,
        3.5 + spread * 0.70,
    )
    rear_fills = (V2_GOLD, V2_IVORY, V2_GOLD, V2_IVORY)
    for i, (length, fill) in enumerate(zip(rear_lengths, rear_fills)):
        dy = i * 0.95
        px.polygon(
            [
                (anchor_x + 0.25, anchor_y + 0.15 + dy),
                (anchor_x - length, anchor_y - 1.9 + dy),
                (anchor_x - 0.55, anchor_y + 1.00 + dy),
            ],
            fill=fill,
            outline=OUTLINE,
            width=0.34,
        )

    px.polygon(
        [
            (anchor_x - 0.2, anchor_y + 2.45),
            (anchor_x - 4.2, anchor_y + 5.8),
            (anchor_x - 1.35, anchor_y + 4.95),
            (anchor_x - 2.45, anchor_y + 8.1),
            (anchor_x + 0.65, anchor_y + 4.55),
        ],
        fill=V2_ORANGE,
        outline=OUTLINE,
        width=0.34,
    )

    # Shoulder root / coverts: this gives the wing a clear start point instead
    # of letting it visually dissolve into hair or the dress edge.
    px.polygon(
        [
            (anchor_x - 0.15, anchor_y - 0.55),
            (anchor_x + 1.05, anchor_y + 0.25),
            (anchor_x + 0.25, anchor_y + 1.55),
            (anchor_x - 0.95, anchor_y + 0.75),
        ],
        fill=V2_GOLD,
        outline=OUTLINE,
        width=0.30,
    )
    px.polygon(
        [
            (anchor_x + 0.15, anchor_y + 0.10),
            (anchor_x + 0.85, anchor_y + 0.55),
            (anchor_x + 0.30, anchor_y + 1.18),
            (anchor_x - 0.30, anchor_y + 0.70),
        ],
        fill=V2_IVORY,
        outline=OUTLINE,
        width=0.26,
    )

    # Curl some pinions around the front so the fire form reads as winged even
    # in poses where the ponytail or torso would otherwise hide the main fan.
    front_lengths = (
        4.9 + spread * 0.60,
        4.0 + spread * 0.48,
        3.2 + spread * 0.40,
        2.5 + spread * 0.30,
    )
    front_fills = (V2_GOLD, V2_IVORY, V2_ORANGE, V2_IVORY)
    for i, (length, fill) in enumerate(zip(front_lengths, front_fills)):
        dy = i * 0.86
        px.polygon(
            [
                (anchor_x + 0.75, anchor_y + 0.35 + dy),
                (anchor_x + length, anchor_y - 1.55 + dy),
                (anchor_x + 1.18, anchor_y + 1.20 + dy),
            ],
            fill=fill,
            outline=OUTLINE,
            width=0.32,
        )

    _draw_star(px, anchor_x - 4.6, anchor_y - 1.35, outer=0.75, inner=0.31, fill=BROOCH_LIGHT, width=0.22)


def _draw_wings_front(px, center_x: float, shoulder_y: float, *, form: FormSpec, spread: float = 0.0) -> None:
    if form.magic_stage < 1:
        return
    for sign in (-1, 1):
        if form.magic_stage == 1:
            for i, length in enumerate((3.5 + spread, 2.8 + spread * 0.7, 2.2 + spread * 0.5)):
                px.polygon(
                    [(center_x + sign * 1.2, shoulder_y + 0.4 + i * 0.75), (center_x + sign * (1.2 + length), shoulder_y - 1.2 + i * 0.75), (center_x + sign * 1.8, shoulder_y + 1.2 + i * 0.75)],
                    fill=V2_PINK_LIGHT if i != 1 else V2_IVORY,
                    outline=OUTLINE,
                    width=0.3,
                )
        else:
            for i, length in enumerate((5.7 + spread, 4.8 + spread * 0.9, 4.0 + spread * 0.72, 3.1 + spread * 0.52)):
                px.polygon(
                    [(center_x + sign * 1.25, shoulder_y + 0.25 + i * 0.82), (center_x + sign * (1.25 + length), shoulder_y - 1.95 + i * 0.82), (center_x + sign * 2.0, shoulder_y + 1.28 + i * 0.82)],
                    fill=V2_GOLD if i % 2 == 0 else V2_IVORY,
                    outline=OUTLINE,
                    width=0.32,
                )
            px.polygon(
                [
                    (center_x + sign * 1.5, shoulder_y + 2.45),
                    (center_x + sign * 4.0, shoulder_y + 5.05),
                    (center_x + sign * 2.3, shoulder_y + 4.55),
                    (center_x + sign * 3.2, shoulder_y + 6.65),
                    (center_x + sign * 0.95, shoulder_y + 4.10),
                ],
                fill=V2_ORANGE,
                outline=OUTLINE,
                width=0.32,
            )
            px.polygon(
                [
                    (center_x + sign * 1.00, shoulder_y - 0.35),
                    (center_x + sign * 2.20, shoulder_y + 0.35),
                    (center_x + sign * 1.35, shoulder_y + 1.55),
                    (center_x + sign * 0.15, shoulder_y + 0.90),
                ],
                fill=V2_GOLD,
                outline=OUTLINE,
                width=0.28,
            )


def _draw_sleeve_wing_side(px, anchor_x: float, anchor_y: float, *, form: FormSpec, strength: float = 1.0, facing: float = 1.0) -> None:
    if strength <= 0.0 or form.magic_stage < 1:
        return
    count = 2 if form.magic_stage == 1 else 3
    for i in range(count):
        span = 1.5 + strength * 0.9 - i * 0.2
        px.polygon(
            [(anchor_x, anchor_y + i * 0.55), (anchor_x + facing * span, anchor_y - 0.65 + i * 0.55), (anchor_x + facing * 0.2, anchor_y + 0.75 + i * 0.55)],
            fill=(V2_PINK_LIGHT if form.magic_stage == 1 else (V2_GOLD if i % 2 == 0 else V2_IVORY)),
            outline=OUTLINE,
            width=0.28,
        )


def _draw_fire_orb(px, x: float, y: float) -> None:
    # More substantial than the first draft: a bright core, hot ring, and
    # asymmetric flame crown that still reads as a compact gameplay projectile.
    px.ellipse(x - 2.45, y - 2.35, x + 2.45, y + 2.35, fill=V2_ORANGE_DARK, outline=OUTLINE, width=0.48)
    px.ellipse(x - 1.75, y - 1.75, x + 1.75, y + 1.75, fill=V2_ORANGE, outline=V2_GOLD_DARK, width=0.34)
    px.ellipse(x - 0.9, y - 0.9, x + 0.9, y + 0.9, fill=V2_IVORY, outline=V2_GOLD, width=0.26)
    px.polygon([(x - 1.3, y - 1.7), (x - 0.7, y - 4.2), (x + 0.2, y - 2.0)], fill=V2_GOLD, outline=OUTLINE, width=0.3)
    px.polygon([(x + 0.1, y - 1.8), (x + 1.2, y - 4.8), (x + 1.6, y - 1.5)], fill=V2_ORANGE, outline=OUTLINE, width=0.3)
    px.polygon([(x + 1.4, y - 0.9), (x + 3.8, y - 2.2), (x + 2.3, y + 0.2)], fill=V2_GOLD, outline=OUTLINE, width=0.3)
    _draw_star(px, x + 3.4, y + 1.9, outer=0.72, inner=0.3, fill=BROOCH_LIGHT, width=0.22)
