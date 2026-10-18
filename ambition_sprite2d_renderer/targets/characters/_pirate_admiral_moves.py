"""The Pirate Admiral's fighting rows: one row for each move he plays.

Before these he had one ``slash`` row, and every move of his Smash table fell
back to it: the jab, the tilts, the aerials and the smashes were all the same
sword raised over the head and brought down late, so the blade was still over
his head while the hit was live in front of him.

A move's row is slaved to the move (frame = progress x frames), so each row is
keyed in the SECONDS of its move (``MOVES``: the duration and the live window of
the table, ``data/movesets/pirate_admiral.ron``). The blade is on the line of
the hit volume through the live window, and comes back to the guard by the end.

A limb angle is a world angle: 0 is down, negative is to the front, -180 is up.
The sword's angle is its own: 0 points to the front, -90 up, 90 down. The hit
volumes are the table's: this sheet publishes no hit area, so the table's
boxes are the damage, and these poses are drawn to put the blade on them.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

Key = Tuple[float, Dict[str, float]]

#: The guard, as ``_pirate_common.home_pose`` has it, for the channels below.
GUARD: Dict[str, float] = {}


def _lunge(front: float = -34.0, back: float = 26.0) -> Dict[str, float]:
    """The legs of a step to the front: the front leg out, the back leg long."""
    return {
        "right_thigh": front, "right_shin": front * 0.35,
        "left_thigh": back, "left_shin": back + 12.0,
    }


def _crouch(depth: float = 1.0) -> Dict[str, float]:
    """The legs bent under him, a knee to the front and a knee to the back."""
    return {
        "right_thigh": -20.0 - 46.0 * depth, "right_shin": -6.0 + 30.0 * depth,
        "left_thigh": 16.0 + 40.0 * depth, "left_shin": 20.0 + 70.0 * depth,
    }


def _tuck(depth: float = 1.0) -> Dict[str, float]:
    """The knees drawn up, as a body in the air holds them."""
    return {
        "right_thigh": -20.0 - 50.0 * depth, "right_shin": -6.0 + 20.0 * depth,
        "left_thigh": 16.0 - 40.0 * depth, "left_shin": 20.0 + 40.0 * depth,
    }


def _merge(*parts: Dict[str, float]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for part in parts:
        out.update(part)
    return out


#: Arm and blade poses, each one place of the sword.
#: A thrust: the arm straight to the front at the shoulder, the point out.
THRUST = {"sword_upper": -88.0, "sword_fore": -92.0, "weapon": 0.0, "off_upper": 40.0, "off_fore": 30.0}
#: The blade back over the shoulder: the windup of a cut.
OVER_BACK = {"sword_upper": -165.0, "sword_fore": -215.0, "weapon": -165.0, "off_upper": -30.0, "off_fore": -50.0}
#: The cut through the front, level.
CUT_LEVEL = {"sword_upper": -96.0, "sword_fore": -98.0, "weapon": -4.0, "off_upper": 44.0, "off_fore": 38.0}
#: The cut gone on, down and to the front.
CUT_THROUGH = {"sword_upper": -62.0, "sword_fore": -50.0, "weapon": 40.0, "off_upper": 40.0, "off_fore": 30.0}
#: The blade low at the back, the windup of a rising cut.
LOW_BACK = {"sword_upper": 30.0, "sword_fore": 50.0, "weapon": 130.0, "off_upper": -30.0, "off_fore": -40.0}
#: The arm and the blade straight up.
STRAIGHT_UP = {"sword_upper": -172.0, "sword_fore": -178.0, "weapon": -92.0, "off_upper": 40.0, "off_fore": 50.0}
#: The arm up and the blade gone over, to the back.
UP_OVER = {"sword_upper": -190.0, "sword_fore": -205.0, "weapon": -140.0, "off_upper": 40.0, "off_fore": 50.0}
#: Low to the front, the blade along the deck.
LOW_FRONT = {"sword_upper": -58.0, "sword_fore": -66.0, "weapon": 14.0, "off_upper": 50.0, "off_fore": 40.0}
#: Low to the back.
LOW_BEHIND = {"sword_upper": 56.0, "sword_fore": 70.0, "weapon": 172.0, "off_upper": -40.0, "off_fore": -30.0}
#: Behind him at the chest, the point to the back.
BEHIND = {"sword_upper": 92.0, "sword_fore": 96.0, "weapon": 182.0, "off_upper": -40.0, "off_fore": -60.0}
#: Straight down, the point under his feet.
DOWN = {"sword_upper": -8.0, "sword_fore": -4.0, "weapon": 90.0, "off_upper": 60.0, "off_fore": 70.0}


def _strike(
    duration: float,
    live: Tuple[float, float],
    windup: Dict[str, float],
    hit: Dict[str, float],
    follow: Dict[str, float],
    hit_end: Dict[str, float] | None = None,
) -> List[Key]:
    """The keys of one blow: from the guard to the windup, to the hit by the
    start of the live window (a little before it: the frame that holds the
    start shows the hit), held through it, the follow-through, the guard."""
    a, b = live
    lead = min(a * 0.5, 0.03)
    keys: List[Key] = [(0.0, GUARD)]
    if a - lead > 0.02:
        keys.append((max(0.01, (a - lead) * 0.55), windup))
    keys.append((max(0.0, a - lead), hit))
    keys.append((b, hit_end or hit))
    keys.append((b + (duration - b) * 0.4, follow))
    keys.append((duration, GUARD))
    return keys


def _held(duration: float, *keys: Key) -> List[Key]:
    return [(0.0, GUARD), *keys, (duration, GUARD)]


#: Each row: (seconds of its move, frames, keys, planted on the ground).
MOVES: Dict[str, Tuple[float, int, List[Key], bool]] = {}


def _row(name: str, duration: float, frames: int, keys: List[Key], planted: bool = True) -> None:
    MOVES[name] = (duration, frames, keys, planted)


# The jab: a quick point to the front, at the chest. Live 0.06-0.13 of 0.29.
_row("jab", 0.29, 6, _strike(
    0.29, (0.06, 0.13),
    windup=_merge({"sword_upper": -40.0, "sword_fore": -30.0, "weapon": -20.0, "body_tilt": -2.0}),
    hit=_merge(THRUST, _lunge(-30.0, 22.0), {"body_tilt": 10.0, "root_x": 4.0, "mouth_open": 0.4}),
    follow=_merge({"sword_upper": -70.0, "sword_fore": -76.0, "weapon": -10.0, "body_tilt": 6.0}),
))
# The forward tilt: a cut from over the shoulder, level through the front.
# Live 0.10-0.18 of 0.38.
_row("attack_side", 0.38, 7, _strike(
    0.38, (0.10, 0.18),
    windup=_merge(OVER_BACK, {"body_tilt": -6.0, "root_x": -2.0}),
    hit=_merge(CUT_LEVEL, _lunge(-34.0, 24.0), {"body_tilt": 12.0, "root_x": 6.0, "mouth_open": 0.6}),
    hit_end=_merge(CUT_LEVEL, {"weapon": 16.0}, _lunge(-34.0, 24.0), {"body_tilt": 14.0, "root_x": 6.0}),
    follow=_merge(CUT_THROUGH, _lunge(-26.0, 20.0), {"body_tilt": 10.0, "root_x": 4.0}),
))
# The up tilt: a cut that rises over his head from the front.
# Live 0.09-0.17 of 0.36. The box is over the front of his head.
_row("attack_up", 0.36, 7, _strike(
    0.36, (0.09, 0.17),
    windup=_merge({"sword_upper": -40.0, "sword_fore": -24.0, "weapon": 30.0}, _crouch(0.4)),
    hit=_merge({"sword_upper": -138.0, "sword_fore": -148.0, "weapon": -58.0}, {"body_tilt": 2.0, "head_tilt": -10.0, "mouth_open": 0.6}),
    hit_end=_merge({"sword_upper": -160.0, "sword_fore": -172.0, "weapon": -96.0}, {"body_tilt": -2.0, "head_tilt": -12.0}),
    follow=_merge(UP_OVER, {"body_tilt": -6.0}),
))
# The down tilt: low, a sweep along the deck at the shins. Live 0.08-0.15 of 0.33.
_row("attack_down", 0.33, 7, _strike(
    0.33, (0.08, 0.15),
    windup=_merge({"sword_upper": -20.0, "sword_fore": 10.0, "weapon": 100.0}, _crouch(0.7), {"body_tilt": 10.0}),
    hit=_merge(LOW_FRONT, _crouch(1.0), {"body_tilt": 24.0, "root_x": 4.0}),
    hit_end=_merge(LOW_FRONT, {"weapon": 4.0}, _crouch(1.0), {"body_tilt": 24.0, "root_x": 4.0}),
    follow=_merge({"sword_upper": -40.0, "sword_fore": -40.0, "weapon": -10.0}, _crouch(0.6), {"body_tilt": 14.0}),
))
# The forward smash: the blade far back over the head for the charge, then a
# cleave with a big step. Live 0.34-0.42 of 0.80.
_row("smash_forward", 0.80, 14, _strike(
    0.80, (0.34, 0.42),
    windup=_merge(OVER_BACK, {"sword_upper": -175.0, "weapon": -185.0, "body_tilt": -12.0, "root_x": -4.0, "head_tilt": -6.0},
                  _lunge(-18.0, 30.0)),
    hit=_merge(CUT_LEVEL, {"weapon": -2.0}, _lunge(-46.0, 34.0), {"body_tilt": 16.0, "root_x": 2.0, "mouth_open": 0.8}),
    hit_end=_merge(CUT_LEVEL, {"weapon": 14.0}, _lunge(-46.0, 34.0), {"body_tilt": 18.0, "root_x": 2.0, "mouth_open": 0.8}),
    follow=_merge(CUT_THROUGH, {"weapon": 60.0}, _lunge(-40.0, 30.0), {"body_tilt": 14.0, "root_x": 2.0}),
))
# The up smash: low and back for the charge, then the arm and the blade
# straight up. Live 0.30-0.39 of 0.73.
_row("smash_up", 0.73, 13, _strike(
    0.73, (0.30, 0.39),
    windup=_merge(LOW_BACK, _crouch(1.0), {"body_tilt": 16.0}),
    hit=_merge(STRAIGHT_UP, {"weapon": -84.0}, {"body_tilt": -4.0, "bob": -6.0, "head_tilt": -14.0, "mouth_open": 0.9,
                                                "right_thigh": -10.0, "right_shin": 0.0, "left_thigh": 12.0, "left_shin": 16.0}),
    hit_end=_merge(STRAIGHT_UP, {"weapon": -100.0}, {"body_tilt": -6.0, "bob": -6.0, "head_tilt": -14.0,
                                                     "right_thigh": -10.0, "right_shin": 0.0, "left_thigh": 12.0, "left_shin": 16.0}),
    follow=_merge(UP_OVER, {"body_tilt": -4.0}),
))
# The down smash: crouched low, the blade along the deck to the front, then
# round to the back. Live 0.28-0.38 of 0.74: both sides of him.
_row("smash_down", 0.74, 13, [
    (0.0, GUARD),
    (0.16, _merge({"sword_upper": -150.0, "sword_fore": -170.0, "weapon": -120.0}, _crouch(0.5))),
    (0.26, _merge(LOW_FRONT, {"weapon": 6.0}, _crouch(1.1), {"body_tilt": 18.0})),
    (0.31, _merge(LOW_FRONT, {"weapon": 8.0}, _crouch(1.1), {"body_tilt": 18.0, "mouth_open": 0.8})),
    (0.37, _merge(LOW_BEHIND, _crouch(1.1), {"body_tilt": 10.0})),
    (0.52, _merge(LOW_BEHIND, {"weapon": 150.0}, _crouch(0.7), {"body_tilt": 6.0})),
    (0.74, GUARD),
])
# The charge of a smash: the game holds this row while the button is held
# (``SMASH_CHARGE_CLIP``), for each of the three. Coiled, the blade back over
# the shoulder, shaking with the strain.
_COIL = _merge(OVER_BACK, {"sword_upper": -170.0, "weapon": -180.0, "body_tilt": -8.0, "root_x": -3.0, "mouth_open": 0.5},
               _lunge(-22.0, 30.0))
_row("smash_charge", 0.32, 4, [
    (0.0, _COIL),
    (0.08, _merge(_COIL, {"weapon": -186.0, "body_tilt": -9.0, "shoulder_bounce": -1.5})),
    (0.16, _merge(_COIL, {"weapon": -176.0, "body_tilt": -7.5, "shoulder_bounce": 1.0})),
    (0.24, _merge(_COIL, {"weapon": -184.0, "body_tilt": -8.5, "shoulder_bounce": -1.0})),
    (0.32, _COIL),
])
# The neutral air: the blade round him once. Live 0.07-0.19 of 0.35.
_row("air_neutral", 0.35, 8, [
    (0.0, _merge(GUARD, _tuck(0.6))),
    (0.05, _merge(CUT_LEVEL, {"weapon": -40.0}, _tuck(1.0))),
    (0.09, _merge(STRAIGHT_UP, {"weapon": -120.0}, _tuck(1.0), {"body_tilt": -6.0})),
    (0.13, _merge(BEHIND, {"weapon": 170.0}, _tuck(1.0), {"body_tilt": -4.0})),
    (0.17, _merge(DOWN, {"weapon": 100.0, "sword_upper": -30.0}, _tuck(1.0))),
    (0.21, _merge(CUT_LEVEL, {"weapon": 20.0}, _tuck(0.8))),
    (0.35, _merge(GUARD, _tuck(0.5))),
], planted=False)
# The forward air: a chop from over the head to the front. Live 0.11-0.19 of 0.39.
_row("air_forward", 0.39, 7, _strike(
    0.39, (0.11, 0.19),
    windup=_merge(OVER_BACK, _tuck(0.7), {"body_tilt": -8.0}),
    hit=_merge(CUT_LEVEL, {"weapon": -16.0}, _tuck(0.9), {"body_tilt": 12.0, "mouth_open": 0.6}),
    hit_end=_merge(CUT_LEVEL, {"weapon": 20.0}, _tuck(0.9), {"body_tilt": 14.0}),
    follow=_merge(CUT_THROUGH, {"weapon": 70.0}, _tuck(0.7), {"body_tilt": 10.0}),
), planted=False)
# The back air: the blade behind him, the point back. Live 0.13-0.20 of 0.44.
_row("air_back", 0.44, 8, _strike(
    0.44, (0.13, 0.20),
    windup=_merge({"sword_upper": -80.0, "sword_fore": -60.0, "weapon": -30.0}, _tuck(0.7), {"body_tilt": 6.0}),
    hit=_merge(BEHIND, _tuck(0.6), {"body_tilt": -10.0, "head_tilt": 8.0, "mouth_open": 0.6, "left_thigh": 40.0, "left_shin": 30.0}),
    hit_end=_merge(BEHIND, {"weapon": 196.0}, _tuck(0.6), {"body_tilt": -10.0, "head_tilt": 8.0, "left_thigh": 40.0, "left_shin": 30.0}),
    follow=_merge(LOW_BEHIND, _tuck(0.6), {"body_tilt": -4.0}),
), planted=False)
# The up air: an arc over his head, from the front to the back.
# Live 0.08-0.17 of 0.34.
_row("air_up", 0.34, 7, _strike(
    0.34, (0.08, 0.17),
    windup=_merge({"sword_upper": -60.0, "sword_fore": -50.0, "weapon": -10.0}, _tuck(0.8)),
    hit=_merge(STRAIGHT_UP, {"sword_upper": -158.0, "sword_fore": -165.0, "weapon": -64.0}, _tuck(0.8), {"head_tilt": -12.0, "mouth_open": 0.6}),
    hit_end=_merge(UP_OVER, {"weapon": -128.0}, _tuck(0.8), {"head_tilt": -12.0}),
    follow=_merge(UP_OVER, {"sword_upper": -200.0, "weapon": -160.0}, _tuck(0.6)),
), planted=False)
# The down air: the point straight down, under his feet, the knees drawn up
# out of its way. Live 0.14-0.22 of 0.48.
_row("air_down", 0.48, 9, _strike(
    0.48, (0.14, 0.22),
    windup=_merge(STRAIGHT_UP, {"weapon": -90.0}, _tuck(0.6)),
    hit=_merge(DOWN, {"right_thigh": -90.0, "right_shin": -10.0, "left_thigh": -40.0, "left_shin": 40.0, "body_tilt": 4.0,
                      "mouth_open": 0.6}),
    follow=_merge(DOWN, {"weapon": 84.0}, _tuck(0.8)),
), planted=False)
# The dash attack: a running lunge with the point out. Live 0.05-0.14 of 0.40.
_row("dash_attack", 0.40, 7, _strike(
    0.40, (0.05, 0.14),
    windup=_merge(THRUST, {"weapon": -10.0, "sword_upper": -70.0}, _lunge(-30.0, 30.0), {"body_tilt": 18.0}),
    hit=_merge(THRUST, {"weapon": 8.0}, _lunge(-44.0, 40.0), {"body_tilt": 18.0, "root_x": 0.0, "mouth_open": 0.6}),
    follow=_merge(THRUST, {"weapon": 20.0, "sword_upper": -70.0, "sword_fore": -70.0}, _lunge(-36.0, 30.0), {"body_tilt": 14.0, "root_x": 0.0}),
))
# The neutral special and its gun ship: he points the sword to the front and
# calls the shot, the other hand up. Live 0.14-0.20 of 0.44.
_row("special", 0.44, 8, _strike(
    0.44, (0.14, 0.20),
    windup=_merge({"sword_upper": -150.0, "sword_fore": -170.0, "weapon": -110.0, "off_upper": -140.0, "off_fore": -160.0}),
    hit=_merge(THRUST, {"weapon": -6.0, "off_upper": -130.0, "off_fore": -170.0}, _lunge(-30.0, 26.0),
               {"body_tilt": 10.0, "root_x": 6.0, "mouth_open": 1.0}),
    follow=_merge(THRUST, {"weapon": 10.0, "off_upper": -60.0, "off_fore": -80.0}, {"body_tilt": 6.0}),
))
# The up special: the sword raised high to call the shark.
_row("special_up", 0.34, 6, _held(
    0.34,
    (0.08, _merge(STRAIGHT_UP, {"weapon": -96.0, "off_upper": -40.0, "off_fore": -90.0, "head_tilt": -14.0, "mouth_open": 1.0})),
    (0.26, _merge(STRAIGHT_UP, {"weapon": -86.0, "off_upper": -40.0, "off_fore": -90.0, "head_tilt": -14.0, "mouth_open": 0.7})),
))
# The down special: the point driven into the deck at his feet.
# Live 0.12-0.22 of 0.52.
_row("special_down", 0.52, 9, _strike(
    0.52, (0.12, 0.22),
    windup=_merge(STRAIGHT_UP, {"weapon": -100.0}, {"body_tilt": -4.0}),
    hit=_merge({"sword_upper": -40.0, "sword_fore": -30.0, "weapon": 62.0, "off_upper": -60.0, "off_fore": -40.0}, _crouch(0.8),
               {"body_tilt": 18.0, "mouth_open": 0.8}),
    follow=_merge({"sword_upper": -40.0, "sword_fore": -30.0, "weapon": 64.0}, _crouch(0.6), {"body_tilt": 14.0}),
))
# The grab: the free hand out to the front. Live 0.07-0.12 of 0.32.
_row("grab", 0.32, 6, _strike(
    0.32, (0.07, 0.12),
    windup={"off_upper": -30.0, "off_fore": -50.0, "body_tilt": 4.0},
    hit=_merge({"off_upper": -88.0, "off_fore": -92.0, "sword_upper": 20.0, "sword_fore": 10.0, "weapon": 120.0},
               _lunge(-28.0, 22.0), {"body_tilt": 12.0, "root_x": 4.0}),
    follow={"off_upper": -60.0, "off_fore": -70.0, "body_tilt": 6.0},
))
# The pummel: the pommel to the held one's head.
_row("pummel", 0.13, 3, _held(
    0.13,
    (0.05, {"off_upper": -80.0, "off_fore": -90.0, "sword_upper": -120.0, "sword_fore": -100.0, "weapon": 150.0, "body_tilt": 8.0}),
))
# The throws: the free hand flings the held one, the sword arm swings with it.
_HOLD = {"off_upper": -84.0, "off_fore": -90.0}
_row("throw_forward", 0.26, 5, _held(
    0.26,
    (0.06, _merge(_HOLD, {"off_upper": -40.0, "off_fore": -20.0, "body_tilt": -6.0})),
    (0.12, _merge({"off_upper": -110.0, "off_fore": -120.0}, CUT_LEVEL, _lunge(-34.0, 26.0), {"body_tilt": 16.0, "mouth_open": 0.8})),
))
_row("throw_back", 0.28, 5, _held(
    0.28,
    (0.07, _merge(_HOLD, {"body_tilt": 8.0})),
    (0.14, _merge({"off_upper": 100.0, "off_fore": 110.0}, BEHIND, {"body_tilt": -14.0, "head_tilt": 8.0, "mouth_open": 0.8})),
))
_row("throw_up", 0.27, 5, _held(
    0.27,
    (0.06, _merge(_HOLD, _crouch(0.6))),
    (0.13, _merge({"off_upper": -170.0, "off_fore": -178.0}, STRAIGHT_UP, {"body_tilt": -6.0, "head_tilt": -14.0, "mouth_open": 0.8})),
))
_row("throw_down", 0.29, 5, _held(
    0.29,
    (0.07, _merge({"off_upper": -150.0, "off_fore": -170.0}, {"body_tilt": -4.0})),
    (0.14, _merge({"off_upper": -40.0, "off_fore": -10.0}, {"sword_upper": -150.0, "sword_fore": -170.0, "weapon": 70.0},
                  _crouch(0.7), {"body_tilt": 22.0, "mouth_open": 0.8})),
))


def rows(base: list) -> list:
    """The pirate's rows, then a row for each of his moves."""
    out = list(base)
    for name, (duration, frames, _keys, _planted) in MOVES.items():
        out.append((name, frames, max(1, round(duration * 1000.0 / frames))))
    return out


#: The mouths the family's rows open to (``_SLASH``), and closed.
MOUTHS = (0.0, 0.3, 0.6, 0.8)


def _smooth(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def pose(anim: str, frame_idx: int, nframes: int) -> dict:
    """The pose of one frame of the admiral: a fighting row from its keys, any
    other row as the family poses it."""
    from . import _pirate_common as pc

    if anim not in MOVES:
        return pc.animation_pose(anim, frame_idx, nframes)
    duration, _frames, keys, grounded = MOVES[anim]
    # The game shows frame i over [i/n, (i+1)/n) of the move: draw its middle.
    at = (frame_idx + 0.5) / max(1, nframes) * duration
    home = pc.home_pose()
    full = [(t, {**home, **k}) for t, k in keys]
    out = dict(home)
    for (t0, k0), (t1, k1) in zip(full, full[1:]):
        if t0 <= at <= t1 or (t1 == full[-1][0] and at > t1):
            u = _smooth((at - t0) / (t1 - t0)) if t1 > t0 else 1.0
            for channel, value in k0.items():
                if isinstance(value, bool):
                    out[channel] = value
                else:
                    out[channel] = value + (k1[channel] - value) * u
            break
    out["blink"] = False
    # A face is a part painted once for each look it has: a mouth on a
    # continuous scale would paint a new face on every frame. Snap it to the
    # few the family's own rows have.
    out["mouth_open"] = min(MOUTHS, key=lambda m: abs(m - out["mouth_open"]))
    if grounded:
        return pc.planted(out)
    # In the air the hip stays where the guard has it: the legs are drawn up
    # under a body that does not go down to put a foot on the deck.
    return out


def register(rows_table: dict, poses_table: dict, base: list) -> None:
    rows_table["pirate_admiral"] = rows(base)
    poses_table["pirate_admiral"] = pose


__all__ = ["MOVES", "pose", "register", "rows"]
del math
