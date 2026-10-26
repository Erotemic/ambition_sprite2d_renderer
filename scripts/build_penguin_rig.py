#!/usr/bin/env python3
"""Build the penguin's rig document from its SVG.

The SVG ``data/characters/penguin/penguin.svg`` owns the art and says where
every joint is; ``rigbuild.creature_rig``, with the ``bird`` anatomy, derives
the skeleton, binds every part to its bone and refreshes the SVG's rig
catalog. This script supplies only what the drawing cannot state: the frame,
the rows and the clips. It never draws.

    uv run python scripts/build_penguin_rig.py

A penguin is a ground bird: it waddles, and when it wants to go fast it goes
down on its belly and slides (``run``), rowing with its flippers and pushing
with its feet. It slaps with a flipper (``slash``) and trumpets with its head
thrown back (``taunt``). Its rows have the names the game reads.

Clips are key poses: one key per drawn frame (``K``), so a one-shot row's
frame ``i`` IS key ``i`` and a loop's last key repeats its first. Angles are
degrees added to the drawing (positive turns clockwise on screen: a positive
``body`` pitches the bird forward, a positive ``head`` drops the beak; a
flipper hangs down, so a negative ``<side>_wing`` swings it forward and up);
distances are SVG units.
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
from ambition_sprite2d_renderer.rigbuild.bird import Pose, eyes, track  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"
DATA = PKG / "data" / "characters" / "penguin"
RIGGED = PKG / "targets" / "characters" / "rigged" / "penguin"

# The drawing (SVG units): centre line, ground, the ankles' height, the body joint.
CENTER_X, GROUND_Y = 256.0, 416.0
ANKLE_Y = 404.0
BODY = (252.0, 330.0)
NEAR_X, FAR_X = 16.0, -8.0
#: How far the body joint comes down for the bird to lie on its belly: the
#: belly on the ground line, where its feet stand (at 44 it slid 3 px into
#: the floor).
BELLY = 34.0

#: (row, frames, ms, loops).
ROWS = [
    ("idle", 8, 130, True),
    ("walk", 8, 100, True),
    ("run", 8, 70, True),
    ("jump", 4, 80, True),
    ("fall", 4, 80, True),
    ("slash", 7, 70, False),
    ("taunt", 8, 110, True),
    ("hurt", 4, 92, False),
    ("death", 8, 108, False),
]

K = track


def foot(p: Pose, side: str, local) -> None:
    B.foot_at(p, side, local, body_origin=BODY, center_x=CENTER_X, ankle_y=ANKLE_Y, pitch=30.0)


def standing(**extra: float) -> Pose:
    p: Pose = {"near_foot_x": NEAR_X, "far_foot_x": FAR_X, "near_foot_lift": 0.0, "far_foot_lift": 0.0}
    p.update(eyes("open"))
    p.update(extra)
    return p


def flippers(p: Pose, near: float, far: float | None = None) -> None:
    p["near_wing"] = near
    p["far_wing"] = near * 0.8 if far is None else far


def eye_at(t: float, states: List[str]) -> Pose:
    """One eye state per drawn frame."""
    return eyes(states[min(len(states) - 1, int(round(t * (len(states) - 1))))])


def idle(i: int, n: int, t: float) -> Pose:
    """Standing: a slow sway, the head carried round to look, a blink."""
    w = math.tau * t
    p = standing()
    p["root_y"] = 1.5 * math.sin(w)
    p["body"] = 2.0 * math.sin(w)
    p["head"] = K([0, 0, -10, -10, 8, 8, 0, 0, 0], t)
    flippers(p, -4.0 + 3.0 * math.sin(w))
    p.update(eye_at(t, ["open", "open", "open", "open", "open", "shut", "open", "open", "open"]))
    return p


def walk(i: int, n: int, t: float) -> Pose:
    """The waddle: short steps, the whole body rocked over each foot, the
    flippers held out to balance."""
    p = standing()
    nx, nl, npitch = B.step(t, NEAR_X + 2.0, 9.0, 9.0)
    fx, fl, fpitch = B.step(t + 0.5, FAR_X + 2.0, 9.0, 9.0)
    p.update(near_foot_x=nx, near_foot_lift=nl, near_foot_pitch=npitch,
             far_foot_x=fx, far_foot_lift=fl, far_foot_pitch=fpitch)
    w = math.tau * t
    rock = 9.0 * math.sin(w)
    p["root_y"] = -3.0 * abs(math.sin(w))
    p["body"] = 2.0 + rock
    p["head"] = -0.8 * rock
    p["tail1"] = -0.5 * rock
    flippers(p, -22.0 + 8.0 * math.sin(w), -18.0 - 8.0 * math.sin(w))
    return p


def run(i: int, n: int, t: float) -> Pose:
    """The slide: down on its belly, its head up to see, rowing with its
    flippers and pushing with its feet."""
    w = math.tau * t
    p: Pose = {"body": 80.0, "head": -64.0, "tail1": -20.0, "jaw": 4.0}
    p["root_y"] = BELLY + 1.5 * math.sin(2.0 * w)
    p["root_x"] = 10.0
    # A flipper rows: back along the body, then forward again, above the
    # ground it slides on (rowed down past the belly, it went 12 px into the
    # floor).
    flippers(p, 15.0 + 40.0 * math.sin(w), 15.0 + 40.0 * math.sin(w + 0.5))
    p.update(eyes("angry"))
    foot(p, "near", (14.0, 74.0 + 8.0 * math.sin(w)))
    foot(p, "far", (-6.0, 74.0 + 8.0 * math.sin(w + math.pi)))
    p["near_foot_pitch"] = p["far_foot_pitch"] = 110.0
    return p


def airborne(t: float, pitch: float, drop: float) -> Pose:
    w = math.tau * t
    p: Pose = {"body": pitch, "head": -0.6 * pitch, "tail1": 6.0, "root_y": -24.0 - 3.0 * math.sin(w)}
    flippers(p, -80.0 + 30.0 * math.sin(w), -70.0 - 30.0 * math.sin(w))
    p.update(eyes("open"))
    foot(p, "near", (18.0, drop))
    foot(p, "far", (-4.0, drop - 2.0))
    return p


def jump(i: int, n: int, t: float) -> Pose:
    return airborne(t, -10.0, 60.0)


def fall(i: int, n: int, t: float) -> Pose:
    return airborne(t, 8.0, 70.0)


def slash(i: int, n: int, t: float) -> Pose:
    """A slap: the flipper drawn back, then swung forward and up with the
    body behind it."""
    p = standing()
    p["root_x"] = K([0, -6, 6, 14, 12, 4, 0], t)
    p["body"] = K([0, -10, 6, 16, 12, 4, 0], t)
    p["head"] = K([0, -8, 4, 10, 8, 2, 0], t)
    p["jaw"] = K([0, 8, 14, 6, 4, 0, 0], t)
    flippers(p, K([0, 36, -40, -118, -100, -40, 0], t), K([0, 20, -10, -30, -24, -10, 0], t))
    p.update(eye_at(t, ["open", "angry", "angry", "angry", "angry", "open", "open"]))
    p["fx.peck"] = K([0, 0, 0, 1, 0.6, 0, 0], t)
    return p


def taunt(i: int, n: int, t: float) -> Pose:
    """It trumpets: its head thrown back, its beak open to the sky, its
    flippers out and shaking, its feet going."""
    w = math.tau * t
    p = standing()
    up = K([0, 0.6, 1, 1, 1, 1, 0.6, 0.2, 0], t)
    p["body"] = -6.0 * up
    p["head"] = -46.0 * up + 3.0 * math.sin(6.0 * w)
    p["jaw"] = K([0, 16, 28, 32, 28, 32, 20, 6, 0], t)
    flippers(p, -60.0 * up + 10.0 * math.sin(6.0 * w), -50.0 * up - 10.0 * math.sin(6.0 * w))
    p["near_foot_lift"] = 6.0 * up * max(0.0, math.sin(4.0 * w))
    p["far_foot_lift"] = 6.0 * up * max(0.0, -math.sin(4.0 * w))
    p["fx.notes"] = K([0, 0.6, 1, 1, 1, 1, 0.6, 0, 0], t)
    return p


def hurt(i: int, n: int, t: float) -> Pose:
    """Knocked back with a burst of feathers, its flippers thrown out."""
    p = standing()
    p["root_x"] = K([-14, -20, -12, -4], t)
    p["root_y"] = K([-6, -2, 0, 0], t)
    p["body"] = K([-20, -26, -12, -4], t)
    p["head"] = K([-22, -16, 4, 2], t)
    p["jaw"] = K([24, 18, 6, 2], t)
    flippers(p, K([-100, -80, -40, -6], t), K([-80, -64, -30, -4], t))
    for side, x in (("near", NEAR_X), ("far", FAR_X)):
        p[f"{side}_foot_x"] = x + 0.6 * p["root_x"]
    p.update(eye_at(t, ["shut", "shut", "angry", "angry"]))
    p["fx.hit"] = K([1, 0.4, 0, 0], t)
    p["fx.feathers"] = K([0.6, 1, 0.7, 0.3], t)
    return p


def death(i: int, n: int, t: float) -> Pose:
    """Struck, it goes over backward and lies on its back with its feet up."""
    p = standing()
    p["root_x"] = K([-10, -18, -22, -16, -8, -8, -8, -8], t)
    p["root_y"] = K([-6, -30, -34, 0, 46, 40, 46, 46], t)
    p["body"] = K([-20, -50, -80, -100, -92, -86, -90, -90], t)
    p["head"] = K([-20, -24, -10, 6, -10, -16, -12, -12], t)
    p["jaw"] = K([24, 26, 18, 22, 24, 26, 24, 24], t)
    flippers(p, K([-90, -110, -80, -40, -30, -20, -24, -24], t), K([-70, -90, -60, -30, 20, 26, 22, 22], t))
    up = K([0, 0.3, 0.7, 1, 1, 1, 1, 1], t)
    for side, x, local in (("near", NEAR_X, (22.0, 78.0)), ("far", FAR_X, (-2.0, 76.0))):
        foot(p, side, local)
        if up < 1.0:
            p[f"{side}_foot_x"] = x * (1 - up) + p[f"{side}_foot_x"] * up
            p[f"{side}_foot_lift"] = p[f"{side}_foot_lift"] * up
    p.update(eye_at(t, ["shut", "shut", "shut", "dead", "dead", "dead", "dead", "dead"]))
    p["fx.hit"] = K([1, 0.3, 0, 0, 0, 0, 0, 0], t)
    p["fx.feathers"] = K([0.6, 1, 1, 0.6, 0.3, 0.1, 0, 0], t)
    p["fx.dust"] = K([0, 0, 0, 0, 1, 0.6, 0.2, 0], t)
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
}

SPEC = B.bird_spec(
    name="penguin",
    svg_path=DATA / "penguin.svg",
    rig_path=RIGGED / "penguin_side.rig.json",
    view_label="Penguin - Side Right",
    # Drawn at 512 units square, published in a 128 px frame.
    scale=0.25,
    svg_center_x=CENTER_X,
    svg_ground_y=GROUND_Y,
    frame_size=(128, 128),
    rows=ROWS,
    clips=CLIPS,
    defaults={"eye.open": 1.0},
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
