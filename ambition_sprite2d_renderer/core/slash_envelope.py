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
