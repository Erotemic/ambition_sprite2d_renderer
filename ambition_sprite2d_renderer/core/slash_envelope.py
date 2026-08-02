"""The swing envelope — ONE smooth curve, shared by the art and the hit polygon.

A slash has exactly one shape, and two consumers with opposite needs:

* the **effect** wants it dense and smooth, because a blade's edge is a curve
  and any faceting reads as a wobble;
* the **hit polygon** wants it coarse and convex, because it is a container, not
  a drawing — a handful of vertices around the art, with no curvature of its
  own.

So the envelope is defined once, analytically, and each consumer samples it at
the density it needs. `half_at` is the whole definition; everything else here is
sampling.

⚠ THIS REPLACES A MEASURED TABLE. The first attempt sampled the polygon's
profile off a rasterised scan and interpolated the results — which imported the
scan's 1-pixel quantisation as ripple, and a Catmull-Rom through noisy samples
is a wobble with extra steps. Jon, 2026-08-02: "The vfx should be curved and
smooth, not a perfect arc, but no wobblyness like it has now." An analytic
profile cannot ripple: there is nothing between the samples to disagree with.

## Coordinates

`t` runs 0 at the body to 1 at the tip along the swing axis; `half_at(t)` is the
half-width across it, normalised so the peak is exactly 1. Both consumers place
that into world or frame units themselves, which is what lets the same curve
describe a 99-unit forehand and a shorter aerial.

## Why this profile

A quadratic through three authored points: the near edge, the belly, and a
BLUNT far end. Jon's sketch measures 86% of full height at the body, 100% at the
bulge and 38% at the far end — it is a half disc squashed forward, not a spike,
and a profile that runs to zero is "too pokey at the end".

Quadratic on purpose. It is the lowest-order curve that can hit three points,
it has no inflection to ripple through, and a hull sampled evenly across it
stays close — which is what lets the containing polygon be coarse.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import List, Tuple

# The three authored stations, measured off Jon's sketch (see
# `player_robot_v3.py`): half-width at the body, at the bulge, and at the blunt
# far end, as fractions of the peak.
NEAR = 0.86
FAR = 0.38
BELLY_T = 0.42
# Both consumers must agree where the swing STOPS, because the polygon's extent
# is what the runtime turns into the quad the art is stretched into. The profile
# ends blunt now, so the swing runs its full length — the old 0.96 existed only
# to blunt a spike the profile no longer has.
TIP = 1.0


@dataclass(frozen=True)
class SwingDescriptor:
    """**Everything a swing IS, written once.**

    The profile above says what SHAPE a swing has; this says how big it is,
    where it sits, and how much room the container leaves around the art. Both
    the hit polygon and the effect read it, so a swing has one spelling instead
    of two.

    ⚠ It had two, and they had already drifted. The polygon carried
    `SLASH_REACH / SLASH_HALF / SLASH_HULL_MARGIN / SLASH_TIP / SLASH_RISE` in
    character-frame pixels while the art carried `REACH / PEAK_HALF / AXIS_Y /
    T_INSET_*` in its own 160-pixel frame — and the polygon was passing
    `SLASH_TIP = 0.96` into a sampler whose shared default was `TIP = 1.0`, so
    the two ends of the same swing disagreed by 4% of its reach. Four percent is
    harmless; two files holding two spellings of one swing is how the original
    `box`-versus-`cone` split started, and that one reached 80%.

    ## The art does not restate any of this

    The runtime stretches the effect's frame into the quad it derives from the
    POLYGON, so the frame IS the swing: its width is the polygon's extent and
    its half-height is the polygon's widest station. The art therefore derives
    its own frame constants from the descriptor (`art_peak_half`), rather than
    naming numbers that have to be kept in step by hand.

    ## Sharing an effect means sharing the RECIPE

    Point a second character's sheet at the same generator with its own
    descriptor and the art is drawn for ITS volume. Sharing the pixels instead
    would hand it a silhouette cut for somebody else's polygon, which is the
    defect that made the slash sheet per-character in the first place.
    """

    #: Body to tip, in the character's authoring frame.
    reach: float
    #: Peak half-width, same units. The profile is normalised to a peak of 1, so
    #: this is the only size it needs.
    half: float
    #: How far above the body's centre the swing's axis sits. Free of tilt since
    #: `swing_shape` began taking its axis from the volume rather than from the
    #: attacker's centroid.
    rise: float = 0.0
    #: How far the coarse container sits outside the envelope. A hull of points
    #: on a curve cuts the chord between them; this covers that sag and buys the
    #: slight overreach Jon allows ("its ok if it slightly gives a hit outside
    #: the vfx, just slightly though").
    hull_margin: float = 1.11
    #: Where the swing stops, as a fraction of `reach`. Both consumers must
    #: agree, which is exactly what they previously did not.
    tip: float = TIP
    #: How far the art pulls inside the container, so a blurred edge still lands
    #: within the volume.
    art_inset: float = 0.885
    #: How far the blade's horns sit back from its point, as a fraction of
    #: reach. Art only — the container closes on a blunt chord.
    horn_pull: float = 0.42

    def scaled(self, reach: float = 1.0, half: float = 1.0) -> "SwingDescriptor":
        """A variant of this swing — an aerial with less room, a shorter back-air.

        Per-attack deviation is a multiplier on the ONE descriptor, never a
        second set of numbers.
        """
        return replace(self, reach=self.reach * reach, half=self.half * half)

    def hull(self) -> List[Tuple[float, float]]:
        """The coarse convex container, as `(t, half)` pairs."""
        return hull_points(self.hull_margin, self.tip)

    def art_peak_half(self, frame_height: float) -> float:
        """The art's peak half-width, in ITS frame's pixels.

        The frame's half-height maps to the polygon's widest station, which is
        `half * hull_margin`; the art wants `half * art_inset`. So the ratio is
        the only thing that crosses, and neither side names the other's units.
        """
        return (frame_height / 2.0) * (self.art_inset / self.hull_margin)


# Quadratic through (0, NEAR), (BELLY_T, 1.0), (1.0, FAR).
_A = ((1.0 - NEAR) - BELLY_T * (FAR - NEAR)) / (BELLY_T * BELLY_T - BELLY_T)
_B = (FAR - NEAR) - _A
_C = NEAR


def half_at(t: float) -> float:
    """Half-width of the swing at `t` along it, peaking at 1.

    Never zero: the swing is TALL where it leaves the body and still has real
    height at its blunt end. Only outside `[0, 1]` is there nothing.
    """
    if t < 0.0 or t > 1.0:
        return 0.0
    return _A * t * t + _B * t + _C


def outline(samples: int, scale: float = 1.0) -> List[Tuple[float, float]]:
    """`(t, half)` around the whole envelope: up one side, back along the other.

    `samples` is the density knob and the ONLY difference between what the art
    draws and what the polygon contains. `scale` widens the envelope — the
    polygon uses a little over 1 so it sits outside the art rather than on it.
    """
    top = [(i / samples, half_at(i / samples) * scale) for i in range(samples + 1)]
    return top + [(t, -h) for t, h in reversed(top[1:-1])]


# Where the coarse container puts its vertices. Even spacing is fine for a
# quadratic — it has no steep climb for a chord to cut across, which the
# previous profile did. Six stations, ~10 vertices, no curvature of its own.
HULL_STATIONS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)


def hull_points(
    scale: float = 1.0, tip: float = TIP
) -> List[Tuple[float, float]]:
    """A COARSE convex container for the envelope, as `(t, half)` pairs.

    The polygon does not trace the curve, it encloses it. Sampling sparsely and
    taking the convex hull is what makes the container convex by construction
    while keeping the vertex count in single digits — and a hull of points ON a
    curve bulges OUTWARD of the chord between them, so `scale` only has to cover
    the sag, not the whole shape.

    `tip` shortens the last station so the point is blunt rather than a spike:
    a needle-sharp vertex adds reach that the art never draws.
    """
    top = [(min(t, tip), half_at(t) * scale) for t in HULL_STATIONS]
    return _convex_hull(top + [(t, -h) for t, h in top])


def _convex_hull(points):
    """Monotone chain, counter-clockwise.

    The runtime lowers a convex volume through `ConvexPolygon::from_convex_hull`,
    so an authored outline that is not already convex is silently played as its
    hull — a shape nobody drew and no overlay shows. Hulling here means the
    authored polygon IS the tested polygon.
    """
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in points))
    if len(pts) < 3:
        return list(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: List[Tuple[float, float]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: List[Tuple[float, float]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


#: **The protagonist's swing.** Lives here rather than beside either consumer
#: because both of them read it and neither owns it — the polygon builder is a
#: character target and the effect is a prop target, and whichever one held it
#: would make the other import across that boundary to ask what it was drawing.
#:
#: Sized off Jon's sketch: 6.6 player-widths across, 1.9 player-heights tall,
#: near edge 86% of full height, far end 38%. See `player_robot_v3.py` for the
#: scale reading that turned those ratios into these pixels.
PLAYER_ROBOT_SWING = SwingDescriptor(
    reach=128 * 1.53,
    half=83.0,
    rise=128 * 0.22,
)
