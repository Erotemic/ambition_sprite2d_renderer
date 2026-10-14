"""Player robot v3 from behind: the rows that draw the back view, and the climb.

The back view is a second SVG view with a rig of its own
(``rigged/player_robot_v3/player_robot_v3_back.rig.json``). It has the same
scale and the same frame as the side view, so a row of it sits in the sheet as
any other row does.

The climb is a list of facts about a ladder, and the joints are solved from
them: a hand and the foot of the other side move as one pair; a limb that holds
goes down at the speed of the ladder; a limb that reaches goes up in half the
time. The rig's two-bone IK puts the elbows and the knees.

The head is wider than a ladder. A hand that is on a rail is thus partly behind
the head. The row does not make the arms longer to show it.

The antenna stays rigid on the head, by ruling (see ``player_robot_v3_gait``).

Data and mathematics only: the rig builder calls ``author_back_rows`` after it
has built the document. Nothing here touches the filesystem.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

#: The sheet rows that are drawn from the back view.
BACK_ROWS: Tuple[str, ...] = ("climb",)

# Distances are in units of the SVG; the builder gives the scale to rig pixels.
RAIL = 19.5                        # a hand on a rail, from the column of the body
HAND_HIGH, HAND_LOW = 47.0, 33.5   # the middle of a hand, above the floor
WRIST_BELOW_HAND = 3.6             # the hand points up, so its wrist is below its middle
FOOT_OUT = 9.8                     # an ankle on a rung, from the column
ANKLE_HIGH, ANKLE_LOW = 16.0, 7.5  # an ankle, above the floor
REACH_IN = 1.6                     # a limb that reaches comes off the ladder by this
BODY_UP = 0.8                      # the hips are above their standing height
BODY_BOB = 0.7
BODY_SWAY = 1.5
TORSO_LEAN, PELVIS_LEAN, HEAD_LEAN = 3.4, 1.0, -3.0   # degrees, with the sway
BOOT_TURN = 5.0                    # the toes point out
BOOT_LIFT_TURN = 6.0               # and a boot that reaches turns in


def _keys(values: List[float], loop: bool) -> Dict[str, list]:
    count = len(values)
    times = [i / count for i in range(count)] if loop else [i / max(1, count - 1) for i in range(count)]
    pairs = [[round(t, 6), round(v, 5)] for t, v in zip(times, values)]
    if loop and values:
        pairs.append([1.0, round(values[0], 5)])
    return {"keys": pairs}


def _limb(phase: float, high: float, low: float) -> Tuple[float, float]:
    """``(height, reach)`` of a limb at ``phase`` of the cycle. In the first
    half it holds, and the ladder carries it down from ``high`` to ``low``. In
    the second half it reaches up; ``reach`` is 1 in the middle of that."""
    phase %= 1.0
    if phase < 0.5:
        return high + (low - high) * (phase / 0.5), 0.0
    u = (phase - 0.5) / 0.5
    return low + (high - low) * (u * u * (3.0 - 2.0 * u)), math.sin(math.pi * u)


def climb_channels(frames: int, scale: float, ankle_h: float) -> Dict[str, dict]:
    """The channels of one climb cycle. ``scale`` is rig pixels in one SVG unit;
    ``ankle_h`` is the rig's height of an ankle above the floor.

    "near" is the robot's right side (the ear cup's): the right of the picture.
    """
    values: Dict[str, List[float]] = {}

    def put(name: str, value: float) -> None:
        values.setdefault(name, []).append(float(value))

    for index in range(frames):
        t = index / frames
        sway = math.sin(math.tau * (t + 0.125))
        put("root_x", BODY_SWAY * sway * scale)
        put("root_y", -(BODY_UP + BODY_BOB * abs(math.cos(math.tau * t))) * scale)
        put("pelvis", PELVIS_LEAN * sway)
        put("torso", TORSO_LEAN * sway)
        put("head", HEAD_LEAN * sway)
        # The right hand and the left foot are one pair; the other pair is
        # half a cycle behind.
        for side, sgn, hand_phase, foot_phase in (("near", 1.0, t, t + 0.5), ("far", -1.0, t + 0.5, t)):
            hand, hand_reach = _limb(hand_phase, HAND_HIGH, HAND_LOW)
            put(f"{side}_hand_x", sgn * (RAIL - REACH_IN * hand_reach) * scale)
            put(f"{side}_hand_y", -(hand - WRIST_BELOW_HAND) * scale)
            put(f"{side}_hand_pitch", -90.0)
            # The elbow points out and down for the whole cycle. The rig's own
            # branch is that of an arm that hangs, which puts the elbow of a
            # raised arm in the body.
            put(f"{side}_hand_bend", -sgn)
            ankle, foot_reach = _limb(foot_phase, ANKLE_HIGH, ANKLE_LOW)
            put(f"{side}_foot_x", sgn * (FOOT_OUT - REACH_IN * foot_reach) * scale)
            put(f"{side}_foot_lift", ankle * scale - ankle_h)
            put(f"{side}_foot_pitch", 90.0 + sgn * (BOOT_TURN - BOOT_LIFT_TURN * foot_reach))
    return {name: _keys(series, loop=True) for name, series in values.items()}


def author_back_rows(doc: dict, rows: Dict[str, dict]) -> None:
    """Write the clips of ``BACK_ROWS`` into the back rig document ``doc``.
    ``rows`` gives each row's ``frames`` and ``duration_ms`` (the sheet's)."""
    scale = float(doc["svg_source"]["scale"])
    ankle_h = float(doc["frame"]["ankle_h"])
    clips = doc.setdefault("clips", {})
    info = rows["climb"]
    clips["climb"] = {
        "loop": True,
        "frames": int(info["frames"]),
        "duration_ms": int(info["duration_ms"]),
        "channels": climb_channels(int(info["frames"]), scale, ankle_h),
    }
