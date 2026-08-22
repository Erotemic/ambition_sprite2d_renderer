"""Shared analytic swing envelope for slash art and hit geometry.

`half_at(t)` defines normalized half-width from body (`t=0`) to tip (`t=1`).
Visual effects sample it densely for a smooth edge; hit polygons sample it
coarsely as a convex container. A single analytic profile keeps both consumers
on the same authored shape without raster-derived ripple."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import List, Tuple

# Authored half-width stations at the body, bulge, and blunt far end, expressed
# as fractions of the peak.
NEAR = 0.86
FAR = 0.38
BELLY_T = 0.42
# Art and hit geometry must agree on the swing endpoint because runtime stretches
# the effect into the polygon-derived quad.
TIP = 1.0


@dataclass(frozen=True)
class SwingDescriptor:
    """Complete shared description of one swing envelope.

The hit polygon and effect art derive from the same reach, width, axis offset,
container margin, and endpoint so their geometry cannot drift. Per-attack
variants scale this descriptor rather than restating the recipe."""

    #: Body to tip, in the character's authoring frame.
    reach: float
    #: Peak half-width, same units. The profile is normalised to a peak of 1, so
    #: this is the only size it needs.
    half: float
    #: How far above the body's centre the swing's axis sits. Free of tilt since
    #: `swing_shape` began taking its axis from the volume rather than from the
    #: attacker's centroid.
    rise: float = 0.0
    #: Margin outside the sampled envelope to cover hull chord sag and a small
    #: amount of hit-volume overreach.
    hull_margin: float = 1.11
    #: Where the swing stops, as a fraction of `reach`; shared by both consumers.
    tip: float = 0.96
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


#: The protagonist's swing. Lives here rather than beside either consumer
#: because both of them read it and neither owns it — the polygon builder is a
#: character target and the effect is a prop target, and whichever one held it
#: would make the other import across that boundary to ask what it was drawing.
#:
#: Swing proportions: 6.6 player-widths across, 1.9 player-heights tall,
#: near edge 86% of full height, far end 38%. See `player_robot_v3.py` for the
#: corresponding pixel scale.
PLAYER_ROBOT_SWING = SwingDescriptor(
    reach=128 * 1.53,
    half=83.0,
    rise=0.0,
)
