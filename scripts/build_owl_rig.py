#!/usr/bin/env python3
"""Build the owl's rig document from its SVG.

The SVG ``data/characters/owl/owl.svg`` owns the art and says where every
joint is; ``rigbuild.creature_rig``, with the ``bird`` anatomy, derives the
skeleton, binds every part to its bone and refreshes the SVG's rig catalog.
This script supplies only what the drawing cannot state: the frame, the rows
and the clips. It never draws.

    uv run python scripts/build_owl_rig.py

An owl flies on slow, deep beats, strikes feet first with its talons
(``slash``, in the air) and, on the ground, stands tall, tilts its head and
hoots (``taunt``). Its rows have the names the game reads.

Clips are key poses: one key per drawn frame (``K``), so a one-shot row's
frame ``i`` IS key ``i`` and a loop's last key repeats its first. Angles are
degrees added to the drawing (positive turns clockwise on screen: a positive
``body`` pitches the bird forward, a positive ``head`` tips the face down, a
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
DATA = PKG / "data" / "characters" / "owl"
RIGGED = PKG / "targets" / "characters" / "rigged" / "owl"

# The drawing (SVG units): centre line, ground, the ankles' height, the body joint.
CENTER_X, GROUND_Y = 256.0, 416.0
ANKLE_Y = 404.0
BODY = (248.0, 322.0)
NEAR_X, FAR_X = 14.0, -8.0
#: Feet tucked up under the belly in flight (relative to the body joint).
TUCK_NEAR, TUCK_FAR = (30.0, 58.0), (14.0, 56.0)

#: (row, frames, ms, loops).
ROWS = [
    ("idle", 8, 130, True),
    ("walk", 8, 110, True),
    ("fly", 10, 90, True),
    ("slash", 8, 76, False),
    ("taunt", 10, 100, True),
    ("hurt", 4, 92, False),
    ("death", 8, 108, False),
]

K = track


def foot(p: Pose, side: str, local) -> None:
    B.foot_at(p, side, local, body_origin=BODY, center_x=CENTER_X, ankle_y=ANKLE_Y, pitch=30.0)


def tuck(p: Pose) -> Pose:
    foot(p, "near", TUCK_NEAR)
    foot(p, "far", TUCK_FAR)
    return p


def perched(**extra: float) -> Pose:
    p: Pose = {"near_foot_x": NEAR_X, "far_foot_x": FAR_X, "near_foot_lift": 0.0, "far_foot_lift": 0.0}
    p.update(wings("folded"))
    p.update(eyes("open"))
    p.update(extra)
    return p


def eye_at(t: float, states: List[str]) -> Pose:
    """One eye state per drawn frame."""
    return eyes(states[min(len(states) - 1, int(round(t * (len(states) - 1))))])


def flight(t: float, *, beats: float = 1.0, pitch: float = 44.0, depth: float = 118.0, lift: float = -26.0,
           height: float = -44.0, bob: float = 10.0) -> Pose:
    """Level flight: the body laid forward, the face held level, the tail
    trailing, the broad wings beating slow and deep, the body rising on each
    downstroke."""
    p: Pose = {"body": pitch, "head": -0.9 * pitch, "tail1": -0.4 * pitch, "tail2": -4.0, "jaw": 0.0}
    p.update(flap(t, beats=beats, depth=depth, lift=lift, lag=0.08))
    w = math.tau * t * beats
    p["root_y"] = height - bob * math.sin(w - 0.6)
    p["tail2"] += 3.0 * math.sin(w - 1.4)
    p.update(wings("open"))
    p.update(eyes("open"))
    return tuck(p)


# --- rows ---------------------------------------------------------------------------


def idle(i: int, n: int, t: float) -> Pose:
    """Standing tall and still: a slow breath, the head tipped right over to
    one side and held, a slow blink."""
    w = math.tau * t
    p = perched()
    p["root_y"] = 2.0 * math.sin(w)
    p["body"] = -1.0 * math.sin(w)
    p["head"] = K([0, 0, -22, -24, -24, -6, 4, 0, 0], t)
    p["tail1"] = 2.0 * math.sin(w + 0.6)
    p.update(eye_at(t, ["open", "open", "open", "open", "shut", "open", "open", "open", "open"]))
    return p


def walk(i: int, n: int, t: float) -> Pose:
    """An owl on foot waddles: short steps, the whole body rocking from one
    foot to the other, the face held level."""
    p = perched()
    nx, nl, npitch = B.step(t, NEAR_X + 2.0, 11.0, 12.0)
    fx, fl, fpitch = B.step(t + 0.5, FAR_X + 2.0, 11.0, 12.0)
    p.update(near_foot_x=nx, near_foot_lift=nl, near_foot_pitch=npitch,
             far_foot_x=fx, far_foot_lift=fl, far_foot_pitch=fpitch)
    w = math.tau * t
    rock = 7.0 * math.sin(w)
    p["root_y"] = -5.0 * abs(math.sin(w))
    p["body"] = 4.0 + rock
    p["head"] = -4.0 - 0.9 * rock
    p["tail1"] = -0.6 * rock
    p["tail2"] = -0.4 * rock
    return p


def fly(i: int, n: int, t: float) -> Pose:
    return flight(t)


def slash(i: int, n: int, t: float) -> Pose:
    """The strike, on the wing: it rears back with its wings thrown up,
    swings its legs through and drives its talons forward, then gathers."""
    p = flight(t, beats=1.0, pitch=30.0)
    p["root_x"] = K([0, -14, -10, 14, 22, 18, 8, 0], t)
    p["root_y"] = K([-44, -54, -52, -40, -36, -38, -42, -44], t)
    p["body"] = K([44, 10, -18, -30, -26, -4, 26, 44], t)
    p["head"] = K([-40, -12, 10, 20, 18, 0, -24, -40], t)
    p["tail1"] = K([-18, 6, 22, 30, 26, 10, -8, -18], t)
    # Wings: thrown up and back to brake, then beaten down once.
    p["near_wing"] = K([-60, 6, 16, -30, -96, -108, -80, -60], t)
    p["near_hand"] = K([0, -24, -30, -10, 16, 20, 8, 0], t)
    p["far_wing"] = K([-50, 4, 12, -24, -84, -96, -70, -50], t)
    p["far_hand"] = K([0, -20, -26, -10, 12, 16, 8, 0], t)
    tuck(p)
    reach = K([0, 0.2, 0.7, 1, 1, 0.6, 0.2, 0], t)
    foot(p, "near", (TUCK_NEAR[0] + 30 * reach, TUCK_NEAR[1] + 22 * reach))
    foot(p, "far", (TUCK_FAR[0] + 24 * reach, TUCK_FAR[1] + 26 * reach))
    p.update(eye_at(t, ["open", "angry", "angry", "angry", "angry", "angry", "open", "open"]))
    p["fx.rake"] = K([0, 0, 0.4, 1, 0.8, 0.2, 0, 0], t)
    p["fx.strike"] = K([0, 0, 0, 1, 0.5, 0, 0, 0], t)
    return p


def taunt(i: int, n: int, t: float) -> Pose:
    """It hoots: drawn up tall, the throat pumping, the head pushed forward
    on each hoot, the wings lifted off the body and settled again."""
    p = perched()
    hoot = K([0, 1, 0.2, 1, 0.2, 0, 0, 1, 0.2, 0, 0], t)
    p["root_y"] = -4.0 * hoot
    p["body"] = -6.0 + 4.0 * hoot
    p["head"] = 4.0 + 12.0 * hoot
    p["jaw"] = 26.0 * hoot
    p["tail1"] = -6.0 * hoot
    p.update(eye_at(t, ["open", "shut", "open", "shut", "open", "open", "open", "shut", "open", "open", "open"]))
    p["fx.notes"] = hoot
    return p


def hurt(i: int, n: int, t: float) -> Pose:
    """Knocked back with a burst of feathers, wings flung, then gathering."""
    p = perched()
    p["root_x"] = K([-14, -20, -12, -4], t)
    p["root_y"] = K([-8, -4, 0, 0], t)
    p["body"] = K([-20, -26, -12, -4], t)
    p["head"] = K([-20, -16, 4, 2], t)
    p["jaw"] = K([24, 18, 6, 2], t)
    p["tail1"] = K([12, 16, 6, 2], t)
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
    p = perched()
    p.update(wings("open"))
    p["root_x"] = K([-6, -10, -12, -8, 0, 0, 0, 0], t)
    p["root_y"] = K([-8, -56, -62, -30, 44, 36, 44, 44], t)
    p["body"] = K([-22, -60, -110, -150, -98, -90, -94, -94], t)
    p["head"] = K([-20, -24, -10, 10, -20, -28, -24, -24], t)
    p["jaw"] = K([24, 26, 18, 22, 26, 28, 26, 26], t)
    p["tail1"] = K([12, 20, 10, 0, -20, -28, -24, -24], t)
    p["near_wing"] = K([-20, 44, 104, -20, 30, 22, 24, 24], t)
    p["near_hand"] = K([-34, 10, 20, -10, 12, 18, 16, 16], t)
    p["far_wing"] = K([-16, 40, 98, -10, 50, 46, 48, 48], t)
    p["far_hand"] = K([-30, 10, 16, -10, 8, 10, 10, 10], t)
    # The feet go limp with the body, then stick up once it lands.
    up = K([0, 0.3, 0.7, 1, 1, 1, 1, 1], t)
    for side, x, local in (("near", NEAR_X, (34.0, 78.0)), ("far", FAR_X, (16.0, 76.0))):
        foot(p, side, local)
        if up < 1.0:
            p[f"{side}_foot_x"] = x * (1 - up) + p[f"{side}_foot_x"] * up
            p[f"{side}_foot_lift"] = p[f"{side}_foot_lift"] * up
    # Down on its back the wings fall shut against the body.
    if t > 0.36:
        p.update(wings("folded"))
    p.update(eye_at(t, ["shut", "shut", "shut", "dead", "dead", "dead", "dead", "dead"]))
    p["fx.hit"] = K([1, 0.3, 0, 0, 0, 0, 0, 0], t)
    p["fx.feathers"] = K([0.6, 1, 1, 0.6, 0.3, 0.1, 0, 0], t)
    p["fx.dust"] = K([0, 0, 0, 0, 1, 0.6, 0.2, 0], t)
    p["fx.drift"] = K([0, 0, 0, 0.3, 0.6, 0.8, 1, 1], t)
    return p


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {
    "idle": idle,
    "walk": walk,
    "fly": fly,
    "slash": slash,
    "taunt": taunt,
    "hurt": hurt,
    "death": death,
}

DEFAULTS: Pose = {"eye.open": 1.0, "wing.folded": 1.0, "wing.open": 0.0}

SPEC = B.bird_spec(
    name="owl",
    svg_path=DATA / "owl.svg",
    rig_path=RIGGED / "owl_side.rig.json",
    view_label="Owl - Side Right",
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


def main(argv: List[str] | None = None) -> int:
    del argv
    missing = sorted({name for name, *_ in SPEC.rows} - set(SPEC.clips))
    if missing:
        raise SystemExit(f"{SPEC.name}: rows without clips: {missing}")
    for path in B.write(SPEC):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
