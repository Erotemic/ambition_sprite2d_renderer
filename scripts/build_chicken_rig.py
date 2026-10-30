#!/usr/bin/env python3
"""Build the rig documents of the chicken (a cockerel) and of its hen.

The SVGs ``data/characters/chicken/chicken.svg`` and
``data/characters/chicken_hen/chicken_hen.svg`` own the art and say where
every joint is (the hen has the cockerel's joints, so the two share the clips); ``rigbuild.creature_rig``, with the ``bird`` anatomy, derives
the skeleton, binds every part to its bone and refreshes the SVG's rig
catalog. This script supplies only what the drawing cannot state: the frame,
the rows and the clips. It never draws.

    uv run python scripts/build_chicken_rig.py

A chicken is a ground bird: it walks with its head thrust at each step, runs
with its wings out, flutters when it is off the ground (``jump``, ``fall``)
and pecks (``slash``). Its rows have the names the game reads.

Clips are key poses: one key per drawn frame (``K``), so a one-shot row's
frame ``i`` IS key ``i`` and a loop's last key repeats its first. Angles are
degrees added to the drawing (positive turns clockwise on screen: a positive
``body`` pitches the bird forward, a positive ``head`` drops the beak, a
negative ``<side>_wing`` drives a raised wing down); distances are SVG units.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.rigbuild import bird as B  # noqa: E402
from ambition_sprite2d_renderer.rigbuild.bird import Pose, eyes, flap, track, wings  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"
DATA = PKG / "data" / "characters" / "chicken"
RIGGED = PKG / "targets" / "characters" / "rigged" / "chicken"

# The drawing (SVG units): centre line, ground, the ankles' height, the body joint.
CENTER_X, GROUND_Y = 256.0, 416.0
ANKLE_Y = 404.0
BODY = (250.0, 322.0)
NEAR_X, FAR_X = 14.0, -14.0
#: Feet drawn up under the belly off the ground (relative to the body joint).
TUCK_NEAR, TUCK_FAR = (26.0, 62.0), (4.0, 60.0)
#: Feet hanging under a body that comes down.
HANG_NEAR, HANG_FAR = (22.0, 76.0), (-2.0, 74.0)

#: (row, frames, ms, loops).
ROWS = [
    ("idle", 8, 120, True),
    ("walk", 8, 90, True),
    ("run", 8, 66, True),
    ("jump", 4, 70, True),
    ("fall", 4, 70, True),
    ("slash", 7, 70, False),
    ("taunt", 8, 100, True),
    ("hurt", 4, 92, False),
    ("death", 8, 108, False),
    # The game holds ``notice`` while it first sees its foe, and ``windup``
    # over its peck's startup (the telegraph). Both loop on the game's clock,
    # so every frame is the whole pose with a shiver.
    ("notice", 3, 120, False),
    ("windup", 3, 90, False),
]

K = track


def foot(p: Pose, side: str, local) -> None:
    B.foot_at(p, side, local, body_origin=BODY, center_x=CENTER_X, ankle_y=ANKLE_Y, pitch=30.0)


def standing(**extra: float) -> Pose:
    p: Pose = {"near_foot_x": NEAR_X, "far_foot_x": FAR_X, "near_foot_lift": 0.0, "far_foot_lift": 0.0}
    p.update(wings("folded"))
    p.update(eyes("open"))
    p.update(extra)
    return p


def eye_at(t: float, states: List[str]) -> Pose:
    """One eye state per drawn frame."""
    return eyes(states[min(len(states) - 1, int(round(t * (len(states) - 1))))])


def flutter(t: float, near, far, *, pitch: float, height: float) -> Pose:
    """Off the ground: short wings beating fast, the feet where ``near`` and
    ``far`` put them under the body."""
    w = math.tau * t
    p: Pose = {"body": pitch, "head": -0.7 * pitch - 6.0, "jaw": 10.0, "tail1": 8.0 + 4.0 * math.sin(w),
               "tail2": 6.0 * math.sin(w - 0.6)}
    p.update(flap(t, beats=1.0, depth=96.0, lift=0.0, lag=0.2))
    p["root_y"] = height - 6.0 * math.sin(w - 0.6)
    p.update(wings("open"))
    p.update(eyes("open"))
    foot(p, "near", near)
    foot(p, "far", far)
    return p


# --- rows ---------------------------------------------------------------------------


def idle(i: int, n: int, t: float) -> Pose:
    """Standing: the head moves in jerks and holds (a chicken does not turn
    its head smoothly), a cluck, a blink, the tail ticking."""
    w = math.tau * t
    p = standing()
    p["root_y"] = 2.0 * math.sin(w)
    p["body"] = -1.0 * math.sin(w)
    p["head"] = K([0, 0, -12, -12, 8, 8, 8, 0, 0], t)
    p["jaw"] = K([0, 0, 0, 10, 0, 0, 8, 0, 0], t)
    p["tail1"] = 3.0 * math.sin(w + 0.6)
    p["tail2"] = 4.0 * math.sin(w - 0.4)
    p.update(eye_at(t, ["open", "open", "open", "open", "open", "shut", "open", "open", "open"]))
    return p


def walk(i: int, n: int, t: float) -> Pose:
    """A strut: at each step the head is thrust forward, then held while the
    body walks up to it."""
    p = standing()
    nx, nl, npitch = B.step(t, NEAR_X + 2.0, 16.0, 18.0)
    fx, fl, fpitch = B.step(t + 0.5, FAR_X + 2.0, 16.0, 18.0)
    p.update(near_foot_x=nx, near_foot_lift=nl, near_foot_pitch=npitch,
             far_foot_x=fx, far_foot_lift=fl, far_foot_pitch=fpitch)
    w = math.tau * t
    p["root_y"] = -5.0 * abs(math.sin(w))
    p["body"] = 3.0 + 3.0 * math.sin(2.0 * w)
    p["head"] = K([14, -8, -8, 6, 14, -8, -8, 6, 14], t)
    p["tail1"] = -5.0 * math.sin(2.0 * w + 0.4)
    p["tail2"] = -6.0 * math.sin(2.0 * w - 0.4)
    p["jaw"] = 0.0
    return p


def run(i: int, n: int, t: float) -> Pose:
    """A panic run: the body thrown forward, the neck out, the wings held
    out and beating, long strides."""
    p = standing()
    nx, nl, npitch = B.step(t, NEAR_X + 8.0, 26.0, 26.0)
    fx, fl, fpitch = B.step(t + 0.5, FAR_X + 8.0, 26.0, 26.0)
    p.update(near_foot_x=nx, near_foot_lift=nl, near_foot_pitch=npitch,
             far_foot_x=fx, far_foot_lift=fl, far_foot_pitch=fpitch)
    w = math.tau * t
    p["root_y"] = -4.0 - 8.0 * abs(math.sin(w))
    p["body"] = 20.0 + 4.0 * math.sin(2.0 * w)
    p["head"] = 4.0 - 6.0 * math.sin(2.0 * w + 0.8)
    p["jaw"] = K([4, 14, 4, 14, 4, 14, 4, 14, 4], t)
    p["tail1"] = 10.0 - 6.0 * math.sin(2.0 * w + 0.4)
    p["tail2"] = -8.0 * math.sin(2.0 * w - 0.4)
    p.update(flap(t, beats=2.0, depth=50.0, lift=-56.0, lag=0.2))
    p.update(wings("open"))
    p.update(eye_at(t, ["angry"]))
    return p


def jump(i: int, n: int, t: float) -> Pose:
    return flutter(t, TUCK_NEAR, TUCK_FAR, pitch=-14.0, height=-30.0)


def fall(i: int, n: int, t: float) -> Pose:
    return flutter(t, HANG_NEAR, HANG_FAR, pitch=6.0, height=-22.0)


def slash(i: int, n: int, t: float) -> Pose:
    """A peck: the head drawn back, stabbed forward and down with the whole
    body behind it, and brought back."""
    p = standing()
    p["root_x"] = K([0, -8, 10, 22, 20, 8, 0], t)
    p["root_y"] = K([0, -4, 2, 6, 6, 2, 0], t)
    p["body"] = K([0, -14, 10, 28, 24, 8, 0], t)
    p["head"] = K([0, -30, 12, 46, 40, 10, 0], t)
    p["jaw"] = K([0, 12, 20, 4, 8, 2, 0], t)
    p["tail1"] = K([0, -8, 12, 22, 18, 6, 0], t)
    p["tail2"] = K([0, -6, 8, 14, 12, 4, 0], t)
    p.update(eye_at(t, ["open", "angry", "angry", "angry", "angry", "open", "open"]))
    p["fx.peck"] = K([0, 0, 0, 1, 0.6, 0, 0], t)
    p["fx.dust"] = K([0, 0, 0, 0.7, 1, 0.4, 0], t)
    return p


def taunt(i: int, n: int, t: float) -> Pose:
    """It crows: the chest up, the head thrown back, the beak wide, the
    wings beating twice."""
    w = math.tau * t
    p = standing()
    up = K([0, 0.6, 1, 1, 1, 1, 0.6, 0.2, 0], t)
    p["root_y"] = -8.0 * up
    p["body"] = -16.0 * up
    p["head"] = -26.0 * up + 4.0 * math.sin(4.0 * w)
    p["jaw"] = K([2, 18, 30, 34, 30, 34, 22, 6, 2], t)
    p["tail1"] = 10.0 * up
    p["tail2"] = 8.0 * up
    p.update(flap(t, beats=2.0, depth=80.0, lift=-30.0, lag=0.15))
    p.update(wings("open") if 0.1 < t < 0.9 else wings("folded"))
    p["fx.notes"] = K([0, 0.6, 1, 1, 1, 1, 0.6, 0, 0], t)
    return p


def hurt(i: int, n: int, t: float) -> Pose:
    """Knocked back with a burst of feathers, wings flung, then gathering."""
    p = standing()
    p["root_x"] = K([-14, -20, -12, -4], t)
    p["root_y"] = K([-8, -4, 0, 0], t)
    p["body"] = K([-22, -28, -12, -4], t)
    p["head"] = K([-26, -20, 4, 2], t)
    p["jaw"] = K([28, 22, 8, 4], t)
    p["tail1"] = K([16, 20, 8, 2], t)
    open_ = K([1, 1, 0.6, 0], t)
    p.update(wings("open") if open_ > 0.5 else wings("folded"))
    p["near_wing"] = K([-20, -34, -70, -90], t)
    p["near_hand"] = K([-34, -28, -20, -20], t)
    p["far_wing"] = K([-16, -30, -64, -84], t)
    p["far_hand"] = K([-30, -24, -20, -20], t)
    for side, x in (("near", NEAR_X), ("far", FAR_X)):
        p[f"{side}_foot_x"] = x + 0.6 * p["root_x"]
    p.update(eye_at(t, ["shut", "shut", "angry", "angry"]))
    p["fx.hit"] = K([1, 0.4, 0, 0], t)
    p["fx.feathers"] = K([0.6, 1, 0.7, 0.3], t)
    return p


def death(i: int, n: int, t: float) -> Pose:
    """Struck, flung up and over in a spray of feathers, down on its back
    with its feet in the air."""
    p = standing()
    p.update(wings("open"))
    p["root_x"] = K([-14, -26, -30, -20, -6, -4, -4, -4], t)
    p["root_y"] = K([-8, -60, -66, -20, 30, 22, 30, 30], t)
    p["body"] = K([-22, -60, -110, -150, -104, -96, -100, -100], t)
    p["head"] = K([-26, -30, -10, 10, -30, -38, -34, -34], t)
    p["jaw"] = K([28, 30, 20, 26, 30, 32, 30, 30], t)
    p["tail1"] = K([16, 24, 10, 0, 40, 56, 50, 50], t)
    p["tail2"] = K([0, 10, 6, 0, 10, 16, 12, 12], t)
    p["near_wing"] = K([-20, 10, -40, -20, 30, 22, 24, 24], t)
    p["near_hand"] = K([-34, -10, -20, -10, 12, 18, 16, 16], t)
    p["far_wing"] = K([-16, 14, -30, -10, 50, 46, 48, 48], t)
    p["far_hand"] = K([-30, -10, -20, -10, 8, 10, 10, 10], t)
    # The feet go limp with the body, then stick up once it lands.
    up = K([0, 0.3, 0.7, 1, 1, 1, 1, 1], t)
    for side, x, local in (("near", NEAR_X, (30.0, 84.0)), ("far", FAR_X, (6.0, 82.0))):
        foot(p, side, local)
        if up < 1.0:
            p[f"{side}_foot_x"] = x * (1 - up) + p[f"{side}_foot_x"] * up
            p[f"{side}_foot_lift"] = p[f"{side}_foot_lift"] * up
    # Down on its back the wings fall shut against the body.
    if t > 0.5:
        p.update(wings("folded"))
    p.update(eye_at(t, ["shut", "shut", "shut", "dead", "dead", "dead", "dead", "dead"]))
    p["fx.hit"] = K([1, 0.3, 0, 0, 0, 0, 0, 0], t)
    p["fx.feathers"] = K([0.6, 1, 1, 0.6, 0.3, 0.1, 0, 0], t)
    p["fx.dust"] = K([0, 0, 0, 0, 1, 0.6, 0.2, 0], t)
    p["fx.drift"] = K([0, 0, 0, 0.3, 0.6, 0.8, 1, 1], t)
    return p


def notice(i: int, n: int, t: float) -> Pose:
    """It has seen you: drawn up tall, the chest out, the head high and
    dead still, one eye on you, the tail up."""
    p = standing()
    p["root_y"] = -1.0
    p["body"] = -14.0
    p["head"] = -6.0
    p["jaw"] = 0.0
    p["tail1"] = 12.0 + K([0, 1.5, -1.5], t)
    p["tail2"] = 8.0
    return p


def windup(i: int, n: int, t: float) -> Pose:
    """The peck made ready: the weight back, the head drawn far back over
    the body, the beak open, the hackle up."""
    shiver = K([0, 1, -1], t)
    p = standing()
    p["root_x"] = -10.0 + shiver
    p["root_y"] = 0.0
    p["body"] = -16.0
    p["head"] = -30.0 + shiver
    p["jaw"] = 14.0
    p["tail1"] = 14.0
    p["tail2"] = 8.0
    for side, x in (("near", NEAR_X), ("far", FAR_X)):
        p[f"{side}_foot_x"] = x - 4.0
    p.update(eyes("angry"))
    return p


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {
    "idle": idle,
    "walk": walk,
    "run": run,
    "jump": jump,
    "fall": fall,
    "slash": slash,
    "taunt": taunt,
    "hurt": hurt,
    "death": death,
    "notice": notice,
    "windup": windup,
}

DEFAULTS: Pose = {"eye.open": 1.0, "wing.folded": 1.0, "wing.open": 0.0}

SPEC = B.bird_spec(
    name="chicken",
    svg_path=DATA / "chicken.svg",
    rig_path=RIGGED / "chicken_side.rig.json",
    view_label="Chicken - Side Right",
    # Drawn at 512 units square, published in a 128 px frame.
    scale=0.25,
    svg_center_x=CENTER_X,
    svg_ground_y=GROUND_Y,
    frame_size=(128, 128),
    rows=ROWS,
    clips=CLIPS,
    defaults=DEFAULTS,
    angle_channels=frozenset({"body"}),
)


#: The hen: the same joints (but for a shorter tail), so the same clips.
HEN_SPEC = B.bird_spec(
    name="chicken_hen",
    svg_path=PKG / "data" / "characters" / "chicken_hen" / "chicken_hen.svg",
    rig_path=PKG / "targets" / "characters" / "rigged" / "chicken_hen" / "chicken_hen_side.rig.json",
    view_label="Chicken Hen - Side Right",
    scale=0.25,
    svg_center_x=CENTER_X,
    svg_ground_y=GROUND_Y,
    frame_size=(128, 128),
    rows=ROWS,
    clips=CLIPS,
    defaults=DEFAULTS,
    angle_channels=frozenset({"body"}),
)


def main(argv: List[str] | None = None) -> int:
    del argv
    for spec in (SPEC, HEN_SPEC):
        missing = sorted({name for name, *_ in spec.rows} - set(spec.clips))
        if missing:
            raise SystemExit(f"{spec.name}: rows without clips: {missing}")
        for path in B.write(spec):
            print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
