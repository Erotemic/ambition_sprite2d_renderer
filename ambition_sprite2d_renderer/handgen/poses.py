"""Named hand poses, and blending between them for animation."""

from __future__ import annotations

from typing import Dict

from .model import HandPose

POSES: Dict[str, HandPose] = {
    "relaxed": HandPose((0.25, 0.3, 0.35, 0.4), 0.25),
    "open": HandPose((0.05,) * 4, 0.0),
    "splay": HandPose((-0.1,) * 4, -0.05, spread=1.0),
    "flat": HandPose((0.0,) * 4, 0.3, spread=-0.6),
    "point": HandPose((0.0, 1.0, 1.0, 1.0), 0.8),
    "grasp": HandPose((0.8, 0.85, 0.85, 0.9), 0.75),
    "fist": HandPose((1.0,) * 4, 0.9),
    "claw": HandPose((0.55,) * 4, 0.35, spread=0.6, hook=1.0),
    "cup": HandPose((0.45, 0.5, 0.5, 0.55), 0.5, spread=-0.3),
    # Solved by ``solve.pinch`` on the default hand (thumb tip on index tip).
    "pinch": HandPose((0.65, 0.75, 0.85, 0.9), 0.444),
}


def blend(a: HandPose, b: HandPose, t: float) -> HandPose:
    """The pose ``t`` of the way from ``a`` to ``b`` (joint angles mix
    linearly; the skeleton keeps its lengths)."""
    mix = lambda x, y: x + (y - x) * t  # noqa: E731
    return HandPose(tuple(mix(x, y) for x, y in zip(a.curls, b.curls)), mix(a.thumb, b.thumb), mix(a.spread, b.spread), mix(a.hook, b.hook))
