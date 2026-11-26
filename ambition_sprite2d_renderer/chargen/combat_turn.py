"""Discrete multiview body turns, in the fixed side-view gameplay stage.

Only the selected drawing changes. A clip retains its normalized time,
root trajectory and world-space foot targets. The clip's own 3D hand
poses are solved in every participating view; no idle-frame substitutions.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Mapping, Sequence

Turn = tuple[tuple[float, float], ...]

# Angles use geometry.View's convention: 45 front 3/4, 90 side,
# 135 back 3/4. The path describes the body, not the game camera.
# Windup and follow-through deliberately use opposite sides of profile.
FORWARD: Turn = ((0., 90.), (.27, 45.), (.40, 90.), (.51, 90.), (.65, 135.), (1., 90.))
BACKHAND: Turn = tuple((t, 180.-yaw) for t, yaw in FORWARD)
UP: Turn = ((0., 90.), (.28, 45.), (.46, 90.), (.58, 90.), (.73, 45.), (1., 90.))
DOWN: Turn = ((0., 90.), (.28, 135.), (.44, 90.), (.57, 90.), (.72, 45.), (1., 90.))
DASH: Turn = ((0., 90.), (.17, 45.), (.30, 90.), (.46, 90.), (.60, 135.), (1., 90.))
STAFF_DOWN: Turn = ((0., 90.), (.25, 135.), (.38, 90.), (.64, 90.), (.78, 45.), (1., 90.))


def yaw_at(path: Sequence[Sequence[float]], t: float) -> float:
    """Interpolate the authored yaw; the renderer samples the closest art."""
    if t <= path[0][0]:
        return path[0][1]
    for (a, ya), (b, yb) in zip(path, path[1:]):
        if t <= b:
            u = (t-a)/(b-a)
            return ya + (yb-ya)*u
    return path[-1][1]


def view_at(clip: Mapping, t: float, default: str, available) -> str:
    """Resolve the same view for art, effects and hit geometry at time t."""
    path = clip.get("publish_turn")
    if not path:
        return default
    yaw = yaw_at(path, t)
    choices = {"front_3q": 45., "side": 90., "back_3q": 135.}
    # Prefer the side at a tie. Partial rig sets retain their existing view.
    return min((key for key in choices if key in available),
               key=lambda key: (abs(choices[key]-yaw), abs(choices[key]-90.)),
               default=default)


def with_combat_turns(clips, *, staff=False):
    """Add direction-specific turn tracks to the existing authored keys.

    The charge uses the release's loaded orientation. A staff thrust is
    side-on at contact; the double sweep stays side-on across both strikes.
    No timings or pose counts are replaced here.
    """
    tracks = {"attack_side": FORWARD, "attack": FORWARD, "slash": BACKHAND,
              "attack_up": UP, "attack_down": DOWN,
              "smash_forward": FORWARD, "smash_up": UP,
              "smash_down": STAFF_DOWN if staff else DOWN,
              "dash_attack": DASH}
    if not staff:
        tracks["jab_2"] = BACKHAND
    for name, path in tracks.items():
        if name in clips:
            clips[name] = replace(clips[name], turn=path)
    for direction in ("forward", "up", "down"):
        name = f"smash_charge_{direction}"
        if name in clips:
            yaw = tracks[f"smash_{direction}"][1][1]
            clips[name] = replace(clips[name], turn=((0., yaw), (1., yaw)))
    if "smash_charge" in clips:
        clips["smash_charge"] = replace(clips["smash_charge"], turn=clips["smash_charge_forward"].turn)
    return clips
