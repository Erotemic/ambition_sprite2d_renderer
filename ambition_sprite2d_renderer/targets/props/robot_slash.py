"""Robot melee slash effect — a broad, readable Hollow-Knight-style sweep.

The game sizes this effect to the resolved melee hitbox and selects a row for
the attack pose. The runtime rotates rows only with the gravity frame and uses
a local horizontal mirror for left-facing side attacks, so facing never turns
the asymmetric accent layers upside down.

The five-frame, 100 ms rows match the melee ACTIVE window exactly, and begin in
the fully active state for Hollow-Knight-like responsiveness:

- impact: a broad white cut is already out on frame 0,
- follow-through: the same readable footprint starts to contract,
- dissipate: the sweep shrinks and feathers,
- release: the remaining energy thins quickly,
- clear: transparent.

``side`` is the broad forward/back swoop, ``up`` and ``down`` are the same
attack language above or below the body, and ``poke`` is the intentionally odd
grounded down-tilt thrust.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ...core import slash_envelope

TARGET_NAME = "robot_slash"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

FRAME_SIZE = (160, 160)
SUPER = 4
# 5 frames x 20 ms = 100 ms, matching `SwipeSpec.active_s = 0.10` so the
# visible effect and damaging window end together.
ROWS: List[Tuple[str, int, int]] = [
    ("side", 5, 20),
    ("up", 5, 20),
    ("down", 5, 20),
    ("poke", 5, 20),
    # The two halves of the 1-2 string of the robot at home: the blade goes up
    # across its front, then comes down. One reach, and the same sweep; the
    # picture says which way the blade went.
    ("rise", 5, 20),
    ("fall", 5, 20),
]

# Pale blue ramp: keep even the deepest stop in mid blue so the effect reads as
# motion rather than a solid dark object.
CORE = (255, 255, 255, 255)
HOT = (240, 251, 255, 255)
BODY = (206, 238, 255, 255)
EDGE = (150, 205, 245, 255)
DEEP = (96, 158, 214, 255)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    t = _clamp((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def _phase(t: float) -> str:
    if t < 0.18:
        return "impact"
    if t < 0.44:
        return "follow_through"
    if t < 0.72:
        return "dissipate"
    if t < 0.95:
        return "release"
    return "clear"


def _amplitude(t: float) -> float:
    if t <= 0.56:
        return _lerp(1.0, 0.82, _smoothstep(0.0, 0.56, t))
    return 0.82 * (1.0 - _smoothstep(0.62, 1.0, t))


# ── The swept region, in SWING SPACE ─────────────────────────────────────────
#
# The frame IS the swing: `x = 0` is the body, `x = REACH` the tip, and `y` runs
# across the arc about `AXIS_Y`. `SwingShape` hands the renderer a quad with
# exactly those axes, so art authored here lands ON the hit polygon rather than
# near it.
#
# Keep all visible art inside the hit polygon. The polygon expands the shared
# envelope by its margin, leaving room for the visual blur without drawing a
# non-damaging edge.
#  THE FRAME IS THE SWING, and its size is DERIVED, not restated.
#
# The runtime stretches this frame into the quad it computes from the hit
# POLYGON, so the frame's width is the polygon's extent and its half-height is
# the polygon's widest station. Naming pixel sizes here was therefore naming the
# polygon's numbers a second time in different units, and they had already
# drifted: the polygon stopped its swing at 0.96 of reach while this file drew
# to 1.0.
#
# `SwingDescriptor` is the one spelling both read. When a second character gets
# its own sheet this becomes a parameter rather than a module constant, which is
# what makes sharing an effect mean sharing the RECIPE — the same generator run
# against another character's descriptor, drawing for ITS volume.
SWING = slash_envelope.PLAYER_ROBOT_SWING
AXIS_Y = FRAME_SIZE[1] / 2.0
REACH = float(FRAME_SIZE[0])
PEAK_HALF = SWING.art_peak_half(FRAME_SIZE[1])
# The art's own margin at the two ENDS, where the envelope narrows and no
# perpendicular inset can help: the polygon closes to a point there, so the
# effect starts and stops slightly inside it.
T_INSET_NEAR = 0.05
T_INSET_FAR = 0.06


def _half_at(t: float) -> float:
    """Half-height of the swept region a fraction `t` along the swing.

    ⚠ THIS WAS A MEASURED TABLE and the table is why the effect wobbled. It
    sampled the polygon's profile off a rasterised scan, which imported the
    scan's 1-pixel quantisation as ripple, and then ran a spline through the
    noise — a wobble with extra steps. The analytic envelope cannot ripple:
    there is nothing between the samples to disagree with.

    The descriptor's `tip` is folded in because the frame maps to the QUAD, and
    the quad spans the polygon's extent — which stops at the blunt tip, not at
    t=1.
    """
    # SHORTENED at both ends, not remapped. The envelope goes to zero at the
    # body and at the tip, so the polygon comes to a point there and no amount
    # of perpendicular margin can contain a blurred pixel drawn past it —
    # widening the container from 1.07 to 1.16 moved the leak by 0.03%. The art
    # instead occupies a slightly shorter span of the frame and reaches zero
    # width INSIDE the volume's points.
    u = (t - T_INSET_NEAR) / max(1e-6, 1.0 - T_INSET_NEAR - T_INSET_FAR)
    if u < 0.0 or u > 1.0:
        return 0.0
    return slash_envelope.half_at(u * SWING.tip) * PEAK_HALF


# How far back the blade's horns sit from its point, as a fraction of reach. The
# leading edge is a curve between them.
HORN_PULL = SWING.horn_pull


def _far_edge_x(dy: float, width_scale: float) -> float:
    """The BLADE's leading edge at height `dy` off the axis — a smooth curve.

    ⚠ NOT the polygon's front. The polygon ends in a blunt vertical chord,
    because it is a coarse convex container and a chord is the cheapest honest
    way to close one. Following that chord with the bright edge drew a straight
    vertical line down the middle of the swing with curves only at the top and
    bottom — the "weird tip" and the jaggedness, in a shape whose every
    definition is smooth.
    
    So the art gets its own front: a parabola from the point back to the horns.
    It is inside the chord everywhere except its single tangent point, so
    containment is unaffected and nothing drawn is straight.
    """
    half = max(1e-6, PEAK_HALF * width_scale)
    k = _clamp(abs(dy) / half)
    # A hair short of the polygon's blunt chord, so the bright edge never lands
    # exactly on it — a tangent there shows as a small flat tick at the point.
    tip_x = REACH * SWING.tip * 0.98
    return tip_x - (tip_x * HORN_PULL) * k * k


def _frame_feather(size, pixels: float = 3.0):
    """1 in the frame and 0 in the frame's outermost pixel on each of its four
    sides, over `pixels` frame pixels between."""
    import numpy as np

    ys, xs = np.mgrid[0 : size[1], 0 : size[0]]
    to_side = np.minimum(np.minimum(xs, size[0] - 1 - xs), np.minimum(ys, size[1] - 1 - ys)) / SUPER
    return np.clip((to_side - 1.25) / pixels, 0.0, 1.0)


def _draw_sweep_frame(t: float) -> Image.Image:
    """One frame of a swing with no direction: the whole crescent at once."""
    return _draw_crescent_frame(t, None)


#  `up` and `down` are NOT pre-rotated any more, and that is a contract change
# shared with `slash_visuals.rs`.
#
# The rows used to be drawn turned a quarter turn because the renderer added a
# per-pose rotation offset on top of the swing direction — an up-swing came out
# at rotation zero, so its artwork had to be drawn already pointing up. That was
# coherent when the sprite was a SQUARE: rotating a square changes nothing about
# which side is long.
#
# It stopped being coherent when the quad became the swing's own extent. The
# renderer sizes the sprite (length along the swing, width across it) on the
# sprite's LOCAL axes, so a row drawn a quarter turn out has its long dimension
# across the swing instead of along it — measured at 8.8% of the drawn ink
# landing outside the volume for the up attacks and 9.2% for the down.
#
# So: every row is drawn in swing space, and orientation is the swing axis
# alone. `pose` now selects WHICH artwork, never how it is turned.
def _draw_up_frame_raw(t: float) -> Image.Image:
    return _draw_sweep_frame(t)


def _draw_down_frame_raw(t: float) -> Image.Image:
    return _draw_sweep_frame(t)


def _draw_directed_frame(t: float, rises: bool) -> Image.Image:
    """A swing with a direction: a rise (low to high) or a fall."""
    return _draw_crescent_frame(t, rises)


# The comet of a swing with a direction (see `_draw_crescent_frame`). Its
# centre, as a part of the reach from the hand; the angle it starts at and the
# angle it goes through, in degrees (0 is the front, 90 the side it ends on).
COMET_CENTRE = 0.3
COMET_START = -110.0
COMET_SPAN = 250.0
# Where its head and its tail are (0 to 1 of the span) at each part of the
# row. The head is at the front on the first frame: a swing that starts at
# rest is not seen. From 0.8 the head is over the top: the follow through.
# Nothing is drawn past the head: the air the blade has not come to is dark.
COMET_TIMES = (0.0, 0.25, 0.5, 0.75, 1.0)
COMET_HEAD = (0.4, 0.78, 1.0, 1.08, 1.1)
COMET_TAIL = (-0.05, 0.1, 0.38, 0.58, 0.95)

# The comet's colours: pale. A fibre has less ALPHA than the band, and not a
# darker blue: a dark line on a bright room is a scratch.
COMET_STOPS = ((0.00, EDGE), (0.2, BODY), (0.5, HOT), (1.00, CORE))
# The solid band of the comet, as a part of its thickness at each place.
SOLID_PART = 0.34
# The fibres behind the band. For each: how deep it is (a part of the comet's
# thickness there, so each comes to the comet's point), its light, how long
# after the tail it starts (of the span), and its width in pixels.
FIBRES = (
    (0.44, 0.95, 0.0, 1.3),
    (0.56, 0.8, 0.05, 1.1),
    (0.68, 0.7, 0.02, 1.5),
    (0.83, 0.55, 0.1, 1.0),
    (0.97, 0.48, 0.04, 1.3),
    (1.16, 0.34, 0.13, 1.0),
    (1.36, 0.26, 0.07, 1.2),
)


def _draw_crescent_frame(t: float, rises) -> Image.Image:
    """A swing of the blade: a crescent at its edge, and the air behind it.

    Three things are drawn, each a closed form of the distance behind the
    blade's leading edge (`_far_edge_x`), so nothing has a step or a layer:

    - The CRESCENT: white at the edge, thick at the middle of the swing, and
      a point at each horn. It goes thin as the swing spends.
    - The FIBRES: thin lines behind the edge, where the blade was. They say
      that the blade moved.
    - The WASH: a pale light on the air the blade came through. All of the
      region that hurts has ink on the first frame (the complaint this
      effect had was "a big empty part of the hitpoly"); the wash goes back
      to the edge as the swing spends.

    `rises` is `None` for a swing with no direction: the whole crescent is
    there on the first frame. `True` and `False` are the two halves of the
    1-2 string: the blade turns across the reach (low to high for a rise),
    the crescent is drawn where the blade has been, and it goes out from the
    end where it started. A rise is drawn for a strike to the right; the game
    turns the frame to the strike, and for a strike to the left it asks for
    the other row (a half turn makes a rise a fall).

    The front edge is sharp and the other edges are soft, so the picture is
    a crescent with light behind it and not a filled shape.
    """
    import numpy as np

    amp = _amplitude(t)
    size = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)
    if amp <= 0.01:
        return Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    ys, xs = np.mgrid[0 : size[1], 0 : size[0]]
    x = (xs + 0.5) / SUPER
    dy = (ys + 0.5) / SUPER - AXIS_Y

    def ramp(edge0, edge1, value):
        k = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
        return k * k * (3.0 - 2.0 * k)

    spend = _smoothstep(0.0, 0.9, t)

    def half_of(u):
        # The envelope has no width before its inset at the hand. The region
        # closes to the hand in a straight side from there: the ink starts at
        # the hand, as the volume does.
        near = T_INSET_NEAR + 1e-3
        return _half_at(u) if u >= near else _half_at(near) * (u / near)

    half = np.array([half_of((col + 0.5) / SUPER / REACH) for col in range(size[0])])
    far = np.array([_far_edge_x((row + 0.5) / SUPER - AXIS_Y, 1.0) for row in range(size[1])])[:, None]
    # How far a point is behind the blade's leading edge.
    behind_edge = far - x
    # 0 on the axis of the swing, 1 at a horn.
    across = np.clip(np.abs(dy) / PEAK_HALF, 0.0, 1.0)
    horn = (1.0 - across**2) ** 0.75
    # The swept region: a soft edge on its sides and a sharp one at its front.
    soft = np.clip((half[None, :] - np.abs(dy)) / 5.0, 0.0, 1.0)
    crisp = np.clip((half[None, :] - np.abs(dy)) / 1.5, 0.0, 1.0)
    front = np.clip(behind_edge / 1.5, 0.0, 1.0)

    reach_part = np.clip(x / np.maximum(far, 1.0), 0.0, 1.0)
    # The light on the air the blade came through. Less at the hand: the
    # region ends there in a flat side, and that side is not to be seen.
    air = (0.14 + 0.2 * reach_part**1.4) * (0.4 + 0.6 * ramp(0.0, REACH * 0.25, x)) * ramp(0.0, REACH * 0.1, x)
    # It goes back to the edge as the swing spends.
    trail = _lerp(REACH * 1.05, REACH * 0.3, spend)

    stops = ((0.00, DEEP), (0.3, EDGE), (0.62, BODY), (0.84, HOT), (1.00, CORE))
    if rises is None:
        # A swing with no direction: the whole crescent at one time, thick at
        # the middle of the swing and a point at each horn.
        # The same parts as the comet's: a solid band at the edge, fibres
        # behind it, and a little light between them.
        thick = np.maximum(REACH * _lerp(0.38, 0.12, spend) * horn**1.3, 1e-3)
        there = np.clip(thick / 2.5, 0.0, 1.0)
        solid = np.clip((thick * SOLID_PART - behind_edge) / 1.5, 0.0, 1.0)
        fibres = np.zeros_like(x)
        for off, light, late, wide in FIBRES:
            # Each is parallel to the edge, and goes out toward the horns. One
            # that starts later is shorter.
            line = np.exp(-(((behind_edge - REACH * _lerp(0.3, 0.12, spend) * off) / wide) ** 2))
            fibres = np.maximum(fibres, line * light * (1.0 - ramp(0.75 - 4.0 * late, 0.98 - 2.0 * late, across)))
        glow = 0.4 * np.clip(1.0 - behind_edge / thick, 0.0, 1.0) ** 1.2
        crescent = np.maximum(np.maximum(solid, fibres), glow) * there
        wash = 0.62 * air * np.clip((trail - behind_edge) / (REACH * 0.12), 0.0, 1.0)
        stops = COMET_STOPS
    else:
        # A swing with a direction is a COMET that goes along the edge of the
        # region: from the low horn, across the front, to the high horn, and
        # then back over the top toward the hand (the follow through). Its
        # head is the blade and its tail is where the blade was. The tail
        # comes after the head, so the last frames are the curl at the END of
        # the swing and nothing at its start: no frame is the same above the
        # axis and below it. (Jon, 2026-10-12: "I want more of the upward or
        # downward motion and follow through visible in the slashes. The
        # symmetric parts at the end are what I don't like.")
        side = 1.0 if rises else -1.0
        # The angle of a point about a centre in the near part of the region:
        # 0 is the front, 90 is the side the swing ends on.
        angle = np.degrees(np.arctan2(-dy * side, x - REACH * COMET_CENTRE))
        angle = np.where(angle < COMET_START - 25.0, angle + 360.0, angle)
        along = (angle - COMET_START) / COMET_SPAN
        head = float(np.interp(t, COMET_TIMES, COMET_HEAD))
        tail = float(np.interp(t, COMET_TIMES, COMET_TAIL))
        # 0 at the tail, 1 at the head.
        grown = np.clip((along - tail) / max(1e-6, head - tail), 0.0, 1.0)
        # The head ends in a point a little past the blade.
        point = 1.0 - ramp(head - 0.14, head + 0.04, along)
        # How far a point is inside the outline of the region: its front and
        # its two sides. The comet is on the outline.
        # A SOFT least of the two: with a hard one, each line that follows
        # the outline has a corner where the front meets a side.
        round_by = REACH * 0.22
        to_side = half[None, :] - np.abs(dy)
        inside_by = -round_by * np.log(
            np.exp(-np.clip(behind_edge, -50.0, 400.0) / round_by) + np.exp(-np.clip(to_side, -50.0, 400.0) / round_by)
        )
        # The follow through stops before the flat side at the hand.
        off_hand = ramp(REACH * 0.06, REACH * 0.3, x)
        # A point at the tail, at the head, and where the follow through
        # comes to the hand: no end of the comet is a flat cut.
        whole = np.maximum(REACH * _lerp(0.34, 0.2, spend) * grown**1.25 * point, 1e-3)
        thick = np.maximum(whole * off_hand, 1e-3)
        # No comet where it has no thickness: the soft least is under zero at
        # the outline, and that is not a place the blade is.
        deep = np.maximum(inside_by, 0.0)
        there = np.clip(whole / 2.5, 0.0, 1.0)
        # The comet has three parts, from its outline in: a SOLID white band
        # with a sharp inner edge (the blade's edge is a thing, not a glow),
        # FIBRES that come off that band and go thin (the air it cut), and a
        # little light between them.
        solid = np.clip((thick * SOLID_PART - deep) / 1.5, 0.0, 1.0)
        fibres = np.zeros_like(x)
        for off, light, late, wide in FIBRES:
            # Its depth is of the comet's thickness with no taper at the hand:
            # a taper along x makes a bend in each line.
            line = np.exp(-(((deep - whole * off) / wide) ** 2))
            # Each fibre starts some way after the tail and stops behind the
            # head: the head is the clean edge.
            # (before the comet starts to come to its point there: a fibre in
            # that part has a bend).
            span = ramp(tail + late, tail + late + 0.18, along) * (1.0 - ramp(head - 0.27 - late, head - 0.13, along))
            fibres = np.maximum(fibres, line * light * span)
        glow = 0.4 * np.clip(1.0 - deep / whole, 0.0, 1.0) ** 1.2
        crescent = np.maximum(solid, np.maximum(fibres, glow) * off_hand) * there
        # Only the air the blade came through has the light (Jon, 2026-10-12:
        # "parts of the slash should not be visible until the slash has
        # 'traveled through' that area"). It goes out from the start of the
        # swing.
        # Wide ramps: an edge of the wash along a line from the centre is a
        # line that the eye sees.
        swept = (1.0 - ramp(head - 0.2, head + 0.02, along)) * ramp(tail - 0.4, tail + 0.25, along)
        wash = 0.7 * air * swept * (1.0 - 0.5 * _smoothstep(0.3, 0.9, t)) * ramp(0.0, REACH * 0.4, x)
        # It is behind the comet and goes out toward the middle of the region:
        # a part of a disc about the centre has a corner there.
        wash = wash * np.clip(1.0 - deep / (REACH * 0.55), 0.0, 1.0)
        # The curl at the end of the swing is to be seen: this row keeps its
        # light to its last drawn frame, and then it is gone.
        amp = max(amp, 0.96 if t <= 0.5 else 0.62)
        stops = COMET_STOPS

    value = np.maximum(crescent * crisp, wash * soft)
    value = np.clip(value, 0.0, 1.0) * front
    # Nothing has alpha at a side of the frame (Jon, 2026-10-12: "any alpha
    # parts you add fade to complete transparency before the sheet ends, so
    # there isn't any discontinuity by overlaying on something").
    value = value * _frame_feather(size)

    keys = np.array([k for k, _ in stops])
    rgba = np.zeros(size[::-1] + (4,), dtype=np.float64)
    for channel in range(3):
        rgba[..., channel] = np.interp(value, keys, [color[channel] for _, color in stops])
    rgba[..., 3] = np.clip(value * 1.15, 0.0, 1.0) * 255.0 * amp
    canvas = Image.fromarray(np.clip(rgba, 0.0, 255.0).astype(np.uint8), "RGBA")
    return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _draw_poke_frame_raw(t: float) -> Image.Image:
    """The straight thrust: a lance of light from the hand to a point, bright
    along its middle and brightest toward the point. It goes from the hand's
    end: the last light is the point.

    The frame is the thrust's volume (a box: the row has no hit polygon), so
    the lance is as long as the frame and nearly as tall at the hand.
    """
    import numpy as np

    amp = _amplitude(t)
    size = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)
    if amp <= 0.01:
        return Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    ys, xs = np.mgrid[0 : size[1], 0 : size[0]]
    along = np.clip((xs + 0.5) / SUPER / REACH, 0.0, 1.0)
    dy = np.abs((ys + 0.5) / SUPER - AXIS_Y)

    def ramp(edge0, edge1, value):
        k = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
        return k * k * (3.0 - 2.0 * k)

    # A point at the far end, and a soft start at the hand.
    half = FRAME_SIZE[1] * 0.46 * (1.0 - along**1.7) ** 0.85 * ramp(0.0, 0.1, along)
    half = np.maximum(half, 1e-3)
    across = dy / half
    body = np.clip(1.0 - across, 0.0, 1.0) ** 1.1
    core = np.exp(-((across / 0.34) ** 2)) * (across < 1.0)
    toward_point = 0.4 + 0.6 * along**1.1
    # The hand's end goes first.
    start = _lerp(-0.2, 0.8, _smoothstep(0.1, 0.95, t))
    left = ramp(start - 0.14, start + 0.14, along)
    value = np.clip(np.maximum(body * 0.6, core) * toward_point * left, 0.0, 1.0)
    value = value * _frame_feather(size)

    stops = ((0.00, DEEP), (0.35, EDGE), (0.72, BODY), (0.90, HOT), (1.00, CORE))
    keys = np.array([k for k, _ in stops])
    rgba = np.zeros(size[::-1] + (4,), dtype=np.float64)
    for channel in range(3):
        rgba[..., channel] = np.interp(value, keys, [color[channel] for _, color in stops])
    rgba[..., 3] = np.clip(value * 1.25, 0.0, 1.0) * 255.0 * amp
    canvas = Image.fromarray(np.clip(rgba, 0.0, 255.0).astype(np.uint8), "RGBA")
    return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _draw_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    t = frame_idx / max(1, frame_count - 1)
    if animation == "up":
        image = _draw_up_frame_raw(t)
    elif animation == "down":
        image = _draw_down_frame_raw(t)
    elif animation == "poke":
        image = _draw_poke_frame_raw(t)
    elif animation in ("rise", "fall"):
        image = _draw_directed_frame(t, animation == "rise")
    else:
        image = _draw_sweep_frame(t)
    # NO global rotation. Every row above is drawn in SWING SPACE — x is the
    # swing axis, which is the axis `SwingShape` hands the renderer — so a
    # blanket 90-degree turn here would put the art across its own hitbox.
    return image


def _frame_meta(animation: str, frame_idx: int, frame_count: int) -> dict:
    t = frame_idx / max(1, frame_count - 1)
    # Swing space: every row runs body -> tip along +x about the axis. `up` and
    # `down` are the side sweep turned a quarter turn by `_draw_*_frame_raw`,
    # so their anchors turn with them.
    anchors = {
        "side": ((0.0, AXIS_Y), (REACH, AXIS_Y)),
        "up": ((AXIS_Y, FRAME_SIZE[1] - 2.0), (AXIS_Y, FRAME_SIZE[1] - REACH)),
        "down": ((AXIS_Y, 2.0), (AXIS_Y, REACH)),
        "poke": ((0.0, AXIS_Y), (REACH, AXIS_Y)),
        "rise": ((0.0, AXIS_Y), (REACH, AXIS_Y)),
        "fall": ((0.0, AXIS_Y), (REACH, AXIS_Y)),
    }
    origin, tip = anchors[animation]
    return {
        "anchors": {
            "origin": {"x": origin[0], "y": origin[1]},
            "tip": {"x": tip[0], "y": tip[1]},
        },
        "effect": {
            "kind": animation,
            "progress": round(t, 4),
            "phase": _phase(t),
            "intensity": round(_amplitude(t), 4),
        },
    }


ACTOR_METADATA = {
    "actor": {"character_id": "fx_robot_slash", "display_name": "Robot Slash"},
    "body": {
        "body_plan": "Effect",
        "body_kind": "Slash",
        "locomotion_hint": "Stationary",
        "traits": ["fx", "slash", "melee", "overlay"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "side", "events": []},
        "action.melee.side": {"animation": "side", "events": []},
        "action.melee.up": {"animation": "up", "events": []},
        "action.melee.down_air": {"animation": "down", "events": []},
        "action.melee.down_tilt": {"animation": "poke", "events": []},
    },
    "sockets": {
        "origin": {
            "source": f"{TARGET_NAME}.geometry",
            "point": {"x": 78.0, "y": 12.0},
        },
    },
    "tags": ["fx", "slash", "melee", "overlay"],
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_draw_frame,
        out_dir=out_dir,
        frame_size=opts.get("frame_size") or FRAME_SIZE,
        frame_meta_fn=_frame_meta,
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
    )
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
    ]
