"""Player robot v3 from behind: the rows that draw the back view (the climb,
the walk away from the camera, the end of the turn away).

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

The walk away goes into the depth of the picture (through a doorway). A
boot that steps lifts and shows its sole (the boot is shorter); the arm of
each side swings against its leg; the body dips when a boot comes down and
goes over the boot that holds. The back stays featureless and has no shadow.

The antenna stays rigid on the head, by ruling (see ``player_robot_v3_gait``).

Data and mathematics only: the rig builder calls ``author_back_rows`` after it
has built the document. Nothing here touches the filesystem.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from .player_robot_v3_motion import MIRRORED

#: The sheet rows that are drawn from the back view.
BACK_ROWS: Tuple[str, ...] = ("climb", "walk_away")

#: For a row of the side view, the frames drawn from the back view. The turn
#: away starts in the side view and ends in the back view.
BACK_FRAMES: Dict[str, Tuple[int, ...]] = {"turn_away": (2, 3)}

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


# The walk away from the camera (into a doorway). Distances are in SVG units.
STEP_LIFT = 4.2        # an ankle at the top of its step, above the floor
STEP_IN = 0.9          # a boot that steps comes in toward the column of the body
STEP_FOLD = 0.6        # the boot of the step shows its sole: it is this tall
WALK_DIP = 0.75        # the body is down this much when a boot comes down
WALK_SWAY = 0.9        # the body goes over the boot that holds
WALK_PELVIS, WALK_TORSO, WALK_HEAD = -2.5, 1.5, -1.0   # degrees, with the sway
ARM_AWAY = (-1.4, -2.2)     # (in, up) of a hand that swings away from the camera
ARM_TOWARD = (0.8, -1.6)    # (out, up) of a hand that swings toward the camera


def walk_away_channels(frames: int, scale: float, doc: dict) -> Dict[str, dict]:
    """The channels of one cycle of the walk away from the camera.

    "near" is the robot's right side (the right of the picture). In the first
    half of the cycle the near boot steps and the far boot holds; the arm of
    each side swings against its leg.
    """
    legs = {leg["channel_prefix"]: leg for leg in doc["ik_legs"]}
    arms = {chain["channel_prefix"]: chain for chain in doc["ik_chains"]}
    values: Dict[str, List[float]] = {}

    def put(name: str, value: float) -> None:
        values.setdefault(name, []).append(float(value))

    for index in range(frames):
        t = index / frames
        wave = math.sin(math.tau * t)            # + while the near boot steps
        root_x = -WALK_SWAY * wave * scale       # over the far boot, which holds
        root_y = WALK_DIP * math.cos(math.tau * t) ** 2 * scale
        put("root_x", root_x)
        put("root_y", root_y)
        put("pelvis", WALK_PELVIS * wave)
        put("torso", WALK_TORSO * wave)
        put("head", WALK_HEAD * wave)
        for side, sgn, step in (("near", 1.0, max(0.0, wave)), ("far", -1.0, max(0.0, -wave))):
            leg = legs[f"{side}_foot"]
            put(f"{side}_foot_x", float(leg["rest_x"]) - sgn * STEP_IN * step * scale)
            put(f"{side}_foot_lift", STEP_LIFT * step * scale)
            put(f"{side}_foot_pitch", 90.0)
            put(f"bone.{side}_leg_foot.scale_y", 1.0 - (1.0 - STEP_FOLD) * step)
            # The arm swings against the leg: toward the camera while its own
            # boot steps away.
            arm = arms[f"{side}_hand"]
            toward, away = max(0.0, sgn * wave), max(0.0, -sgn * wave)
            dx = sgn * (ARM_TOWARD[0] * toward + ARM_AWAY[0] * away)
            dy = ARM_TOWARD[1] * toward + ARM_AWAY[1] * away
            put(f"{side}_hand_x", float(arm["rest_x"]) + root_x + dx * scale)
            put(f"{side}_hand_y", float(arm["rest_y"]) + root_y + dy * scale)
            put(f"{side}_hand_pitch", 90.0 - sgn * 6.0 * (toward - away))
    return {name: _keys(series, loop=True) for name, series in values.items()}


# The back frames of the turn away, for a turn from a body that faced right:
# (root x, root y, pelvis, torso, head, near boot lift, near boot out, hands
# out) in SVG units and degrees. The body swings on past the column and the near
# boot comes down from its step round; the last frame is the stand.
TURN_AWAY_BEATS: Tuple[Tuple[float, ...], ...] = (
    (1.3, 0.9, -2.0, 2.5, -3.0, 2.2, 0.8, 1.2),
    (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
)


def back_frame(row: str, frame_idx: int) -> int:
    """The frame of the back clip of ``row`` that sheet frame ``frame_idx``
    draws (``BACK_FRAMES``)."""
    return BACK_FRAMES[row].index(frame_idx)


def turn_away_channels(scale: float, doc: dict, mirrored: bool) -> Dict[str, dict]:
    """The channels of the back frames of the turn away (``TURN_AWAY_BEATS``).

    From behind the robot is one picture for each facing (the ear cup stays at
    the right), so the turn of a body that faced left is not a mirror of the
    picture: it is the same beats with the sides and the lateral signs changed.
    """
    legs = {leg["channel_prefix"]: leg for leg in doc["ik_legs"]}
    arms = {chain["channel_prefix"]: chain for chain in doc["ik_chains"]}
    side = -1.0 if mirrored else 1.0
    step = "far" if mirrored else "near"
    values: Dict[str, List[float]] = {}

    def put(name: str, value: float) -> None:
        values.setdefault(name, []).append(float(value))

    for root_x, root_y, pelvis, torso, head, lift, out, hands in TURN_AWAY_BEATS:
        put("root_x", side * root_x * scale)
        put("root_y", root_y * scale)
        put("pelvis", side * pelvis)
        put("torso", side * torso)
        put("head", side * head)
        for name in ("near", "far"):
            leg = legs[f"{name}_foot"]
            stepping = 1.0 if name == step else 0.0
            put(f"{name}_foot_x", float(leg["rest_x"]) + side * out * stepping * scale)
            put(f"{name}_foot_lift", lift * stepping * scale)
            put(f"{name}_foot_pitch", 90.0)
            put(f"bone.{name}_leg_foot.scale_y", 1.0 - (1.0 - STEP_FOLD) * stepping * lift / STEP_LIFT)
            arm = arms[f"{name}_hand"]
            put(f"{name}_hand_x", float(arm["rest_x"]) + (side * (root_x + hands)) * scale)
            put(f"{name}_hand_y", float(arm["rest_y"]) + (root_y - 0.5 * hands) * scale)
            put(f"{name}_hand_pitch", 90.0 - side * 8.0 * hands)
    return {name: _keys(series, loop=False) for name, series in values.items()}


def author_back_rows(doc: dict, rows: Dict[str, dict]) -> None:
    """Write the clips of ``BACK_ROWS`` and ``BACK_FRAMES`` into the back rig
    document ``doc``. ``rows`` gives each row's ``frames`` and ``duration_ms``
    (the sheet's)."""
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
    info = rows["walk_away"]
    clips["walk_away"] = {
        "loop": True,
        "frames": int(info["frames"]),
        "duration_ms": int(info["duration_ms"]),
        "channels": walk_away_channels(int(info["frames"]), scale, doc),
    }
    for name, mirrored in (("turn_away", False), (MIRRORED.format("turn_away"), True)):
        clips[name] = {
            "loop": False,
            "frames": len(BACK_FRAMES["turn_away"]),
            "duration_ms": int(rows["turn_away"]["duration_ms"]),
            "channels": turn_away_channels(scale, doc, mirrored),
        }
