"""Fingertip targets: poses solved against contact, not authored by hand.

Two primitives on the model:

- ``close_until_contact``: curl one digit from where it is until any of
  its phalanges touches an object (a ``Rod``): a grip closes on what it
  holds, whatever its size.
- ``touch``: move two digits until their tips meet (tip radius to tip
  radius): an exact pinch, an OK sign.

``grip`` closes every digit round a rod held across the palm; ``pinch``
touches the thumb to a finger, folding the others away.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence, Tuple

import numpy as np

from .model import FINGER_NAMES, Digit, HandPose, HandSpec, digits, local

Vec = np.ndarray


@dataclass(frozen=True)
class Rod:
    """A held cylinder in hand space: its centre, its (unit) axis, its
    radius and half length (for drawing)."""

    centre: Vec
    axis: Vec
    radius: float
    half_length: float = 20.0

    def distance(self, p: Vec) -> float:
        """From a point to the rod's surface (negative inside it); the rod
        ends at its half length."""
        d = p - self.centre
        t = float(np.clip(np.dot(d, self.axis), -self.half_length, self.half_length))
        return float(np.linalg.norm(d - t * self.axis)) - self.radius


@dataclass(frozen=True)
class Union:
    """Several obstacles at once."""

    parts: Tuple

    def distance(self, p: Vec) -> float:
        return min(o.distance(p) for o in self.parts)


@dataclass(frozen=True)
class Capsule:
    """A segment with a radius (a phalanx as an obstacle)."""

    a: Vec
    b: Vec
    radius: float

    def distance(self, p: Vec) -> float:
        ab = self.b - self.a
        t = float(np.clip(np.dot(p - self.a, ab) / (np.dot(ab, ab) or 1.0), 0.0, 1.0))
        return float(np.linalg.norm(p - (self.a + ab * t))) - self.radius


def _digit(spec: HandSpec, pose: HandPose, name: str) -> Digit:
    return digits(spec, pose)[name]


def _with(pose: HandPose, name: str, curl: float) -> HandPose:
    curl = float(curl)
    if name == "thumb":
        return replace(pose, thumb=curl)
    curls = list(pose.curls)
    curls[FINGER_NAMES.index(name)] = curl
    return replace(pose, curls=tuple(curls))


def _curl(pose: HandPose, name: str) -> float:
    return pose.thumb if name == "thumb" else pose.curl(name)


def _clearance(digit: Digit, rod, skip_base: bool = True) -> float:
    """The least gap between the digit's flesh and the rod: each phalanx
    sampled along its length, its radius taken off."""
    gap = np.inf
    n = len(digit.joints) - 1
    for i in range(n):
        a, b = digit.joints[i], digit.joints[i + 1]
        r0 = digit.widths[i] / 2
        r1 = digit.widths[i + 1] / 2 if i + 1 < n else digit.widths[-1] * 0.44
        for t in np.linspace(0.25 if (skip_base and i == 0) else 0.0, 1.0, 6):
            gap = min(gap, rod.distance(a + (b - a) * t) - (r0 + (r1 - r0) * t))
    return gap


def close_until_contact(spec: HandSpec, pose: HandPose, name: str, rod, limit: float = 1.0) -> HandPose:
    """Curl ``name`` from its current curl until it touches ``rod`` (a
    ``Rod``, a ``Capsule``: anything with ``distance(point)``) or reaches
    ``limit``: bisection on the first contact."""
    lo = _curl(pose, name)
    if _clearance(_digit(spec, _with(pose, name, lo), name), rod) <= 0:
        return pose
    steps = np.linspace(lo, limit, 41)
    prev = lo
    for c in steps[1:]:
        if _clearance(_digit(spec, _with(pose, name, c), name), rod) <= 0:
            a, b = prev, c
            for _ in range(20):
                m = (a + b) / 2
                if _clearance(_digit(spec, _with(pose, name, m), name), rod) <= 0:
                    b = m
                else:
                    a = m
            return _with(pose, name, a)
        prev = c
    return _with(pose, name, limit)


def rest_tip_on(spec: HandSpec, pose: HandPose, name: str, obstacle, samples: int = 81) -> HandPose:
    """Curl ``name`` so its TIP rests on ``obstacle``: of the curls where
    no part of it goes into the obstacle, the one whose tip comes nearest
    to it (a closing sweep can pass beside a thin obstacle; this cannot)."""
    best, best_curl = np.inf, _curl(pose, name)
    for c in np.linspace(0.0, 1.0, samples):
        d = _digit(spec, _with(pose, name, c), name)
        if _clearance(d, obstacle) < -0.2:
            continue
        gap = obstacle.distance(d.joints[-1]) - _tip_radius(d)
        if abs(gap) < best:
            best, best_curl = abs(gap), c
    return _with(pose, name, best_curl)


def _tip_radius(digit: Digit) -> float:
    return digit.widths[-1] * 0.44


def touch(spec: HandSpec, pose: HandPose, a: str = "thumb", b: str = "index", rest: float = 0.6) -> Tuple[HandPose, float]:
    """Curl ``a`` and ``b`` so their tips just meet (flesh to flesh),
    preferring the pair nearest ``rest`` curl. Returns the pose and the
    miss (0 when they meet; positive when out of reach)."""

    def miss(ca: float, cb: float) -> float:
        p = _with(_with(pose, a, ca), b, cb)
        ds = digits(spec, p)
        gap = np.linalg.norm(ds[a].joints[-1] - ds[b].joints[-1]) - _tip_radius(ds[a]) - _tip_radius(ds[b])
        return abs(gap)

    grid = np.linspace(0.0, 1.0, 26)
    best = min(((miss(x, y) + 0.02 * ((x - rest) ** 2 + (y - rest) ** 2), x, y) for x in grid for y in grid))
    _, x, y = best
    step = grid[1] - grid[0]
    for _ in range(30):  # refine: coordinate descent, halving the step
        for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
            nx, ny = min(1.0, max(0.0, x + dx)), min(1.0, max(0.0, y + dy))
            if miss(nx, ny) + 0.02 * ((nx - rest) ** 2 + (ny - rest) ** 2) < miss(x, y) + 0.02 * ((x - rest) ** 2 + (y - rest) ** 2):
                x, y = nx, ny
        step /= 2
    return _with(_with(pose, a, x), b, y), miss(x, y)


def grip(spec: HandSpec, radius: float, open_pose: HandPose = HandPose()) -> Tuple[HandPose, Rod]:
    """Close the hand round a rod of ``radius`` held across the palm (a
    handle, a hilt): the rod sits on the palm's face just below the
    knuckles, every finger and then the thumb closes until it touches."""
    centre = local(spec, spec.palm_length * 0.86, 0.0, spec.palm_depth / 2 + radius + 0.3)
    across = local(spec, 0.0, 1.0, 0.0)
    rod = Rod(centre, across / np.linalg.norm(across), radius, spec.palm_half_width + 6.0)
    pose = open_pose
    for name in FINGER_NAMES:
        pose = close_until_contact(spec, pose, name, rod)
    # The thumb closes OVER the fingers (a hammer grip): it stops on the
    # index finger's middle phalanx, or on the rod if that comes first.
    index = digits(spec, pose)["index"]
    # It meets only the stretch of rod under the fingers (past them it
    # wraps round the rod's end, not stopping on it).
    under = Rod(rod.centre, rod.axis, rod.radius, spec.palm_half_width + 1.0)
    rest_on = Union((under, Capsule(index.joints[1], index.joints[2], index.widths[1] / 2)))
    pose = rest_tip_on(spec, pose, "thumb", rest_on)
    return pose, rod


def pinch(spec: HandSpec, finger: str = "index", others: Sequence[float] = (0.75, 0.85, 0.9)) -> Tuple[HandPose, float]:
    """The thumb's tip meeting ``finger``'s, the other fingers folded by
    ``others`` (in order, skipping ``finger``)."""
    curls, rest = [], iter(others)
    for name in FINGER_NAMES:
        curls.append(0.0 if name == finger else next(rest))
    return touch(spec, HandPose(tuple(curls), 0.0), "thumb", finger)
