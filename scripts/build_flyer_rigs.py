#!/usr/bin/env python3
"""Build the rig documents of the European swallow, the African swallow and
the vulture from their SVGs.

The SVGs ``data/characters/<bird>/<bird>.svg`` own the art and say where every
joint is; ``rigbuild.creature_rig``, with the ``bird`` anatomy, derives each
skeleton, binds every part to its bone and refreshes each SVG's rig catalog.
This script supplies only what the drawings cannot state: the frame, the rows
and the clips. It never draws.

    uv run python scripts/build_flyer_rigs.py

The three are one anatomy and one set of rows (the names the game reads), so
they share the clips: each clip is written once and takes the bird's measures
and its manner (``Flyer``).

- the two swallows: quick shallow beats; a swallow darts in beak first; it
  chirps. (The coconut the African swallow carries is a thing of the world,
  not of its drawing.)
- vulture: slow beats of broad wings; it reaches down with its neck and tears;
  its ``taunt`` is the pose of a vulture in the sun, wings held wide.

Clips are key poses: one key per drawn frame (``K``), so a one-shot row's
frame ``i`` IS key ``i`` and a loop's last key repeats its first. Angles are
degrees added to the drawing (positive turns clockwise on screen: a positive
``body`` pitches the bird forward, a positive ``head`` drops the beak, a
negative ``<side>_wing`` drives a raised wing down); distances are SVG units.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.rigbuild import bird as B  # noqa: E402
from ambition_sprite2d_renderer.rigbuild.bird import Pose, eyes, flap, track, wings  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"
CENTER_X, GROUND_Y = 256.0, 416.0
K = track


@dataclass(frozen=True)
class Flyer:
    """What the clips need to know of one bird (SVG units)."""

    name: str
    label: str
    #: The body joint, the height its ankles are drawn at, each ankle's x
    #: from the centre line.
    body: Tuple[float, float]
    ankle_y: float
    near_x: float
    far_x: float
    scale: float
    frame: Tuple[int, int]
    #: Feet tucked under the belly in flight (relative to the body joint).
    tuck_near: Tuple[float, float]
    tuck_far: Tuple[float, float]
    #: Level flight: the body's pitch, beats per loop, how far a wing comes
    #: down, how high it starts, how high the body is carried and how much it
    #: rises on a downstroke.
    pitch: float
    beats: float
    depth: float
    lift: float
    height: float
    bob: float
    #: How far the body joint comes down to lie on the ground, and the turn
    #: of the tail that lays it along the ground there.
    lie: float
    tail_lie: float
    #: ``hop`` (both feet together) or ``step``.
    walk: str
    #: ``dart`` (beak first) or ``tear`` (the neck reaches down).
    attack: str
    #: ``chirp`` or ``spread``.
    taunt: str
    rows: Tuple[Tuple[str, int, int, bool], ...]
    #: How far forward its death carries it while its wings are out (a broad
    #: wing thrown back needs the room in the frame).
    death_shift: float = 0.0


SMALL_ROWS = (("idle", 8, 110, True), ("walk", 6, 80, True), ("fly", 8, 56, True), ("slash", 7, 64, False),
              ("taunt", 8, 90, True), ("hurt", 4, 92, False), ("death", 8, 108, False))
LARGE_ROWS = (("idle", 8, 140, True), ("walk", 8, 120, True), ("fly", 10, 100, True), ("slash", 8, 78, False),
              ("taunt", 8, 130, True), ("hurt", 4, 92, False), ("death", 8, 108, False))

FLYERS = [
    Flyer("european_swallow", "European Swallow", (252.0, 346.0), 404.0, 14.0, -2.0, 0.25, (128, 128), (22.0, 36.0),
          (10.0, 34.0), 40.0, 1.0, 96.0, -30.0, -66.0, 8.0, 40.0, -70.0, "hop", "dart", "chirp", SMALL_ROWS),
    Flyer("african_swallow", "African Swallow", (252.0, 346.0), 404.0, 14.0, -2.0, 0.25, (128, 128), (22.0, 36.0),
          (10.0, 34.0), 40.0, 1.0, 96.0, -30.0, -66.0, 8.0, 40.0, -70.0, "hop", "dart", "chirp", SMALL_ROWS),
    Flyer("vulture", "Vulture", (246.0, 318.0), 404.0, 12.0, -8.0, 0.5, (256, 256), (30.0, 58.0), (14.0, 56.0), 46.0,
          1.0, 104.0, -30.0, -40.0, 8.0, 48.0, -24.0, "step", "tear", "spread", LARGE_ROWS,
          death_shift=40.0),
]


def eye_at(t: float, states: List[str]) -> Pose:
    """One eye state per drawn frame."""
    return eyes(states[min(len(states) - 1, int(round(t * (len(states) - 1))))])


def clips(f: Flyer) -> Dict[str, Callable[[int, int, float], Pose]]:
    def foot(p: Pose, side: str, local) -> None:
        B.foot_at(p, side, local, body_origin=f.body, center_x=CENTER_X, ankle_y=f.ankle_y, pitch=30.0)

    def tuck(p: Pose) -> Pose:
        foot(p, "near", f.tuck_near)
        foot(p, "far", f.tuck_far)
        return p

    def perched(**extra: float) -> Pose:
        p: Pose = {"near_foot_x": f.near_x, "far_foot_x": f.far_x, "near_foot_lift": 0.0, "far_foot_lift": 0.0}
        p.update(wings("folded"))
        p.update(eyes("open"))
        p.update(extra)
        return p

    def flight(t: float, *, pitch: float | None = None, beats: float | None = None) -> Pose:
        """Level flight: the body laid forward, the head held level, the
        tail trailing, the wings beating, the body rising on each downstroke."""
        pitch = f.pitch if pitch is None else pitch
        beats = f.beats if beats is None else beats
        p: Pose = {"body": pitch, "head": -0.85 * pitch, "tail1": -0.4 * pitch, "tail2": -4.0, "jaw": 0.0}
        p.update(flap(t, beats=beats, depth=f.depth, lift=f.lift, lag=0.08))
        w = math.tau * t * beats
        p["root_y"] = f.height - f.bob * math.sin(w - 0.6)
        p["tail2"] += 3.0 * math.sin(w - 1.4)
        p.update(wings("open"))
        p.update(eyes("open"))
        return tuck(p)

    def idle(i: int, n: int, t: float) -> Pose:
        """Perched: a breath, the head carried round and held, a blink, the tail ticking."""
        w = math.tau * t
        p = perched()
        p["root_y"] = 1.5 * math.sin(w)
        p["head"] = K([0, 0, -12, -12, 8, 8, 0, 0, 0], t)
        p["tail1"] = 3.0 * math.sin(w + 0.6)
        p["tail2"] = 4.0 * math.sin(w - 0.4)
        p.update(eye_at(t, ["open", "open", "open", "open", "open", "shut", "open", "open", "open"]))
        return p

    def hop(i: int, n: int, t: float) -> Pose:
        """A small bird on the ground hops: both feet leave it together."""
        p = perched()
        up = math.sin(math.pi * t)
        p["root_y"] = -16.0 * up
        p["near_foot_lift"] = p["far_foot_lift"] = 16.0 * up
        p["body"] = 6.0 * math.cos(math.pi * t)
        p["head"] = -6.0 * math.cos(math.pi * t)
        p["tail1"] = -8.0 * up
        return p

    def step(i: int, n: int, t: float) -> Pose:
        """A big bird on foot: a rocking waddle, its head low."""
        p = perched()
        nx, nl, npitch = B.step(t, f.near_x + 2.0, 12.0, 12.0)
        fx, fl, fpitch = B.step(t + 0.5, f.far_x + 2.0, 12.0, 12.0)
        p.update(near_foot_x=nx, near_foot_lift=nl, near_foot_pitch=npitch,
                 far_foot_x=fx, far_foot_lift=fl, far_foot_pitch=fpitch)
        w = math.tau * t
        rock = 6.0 * math.sin(w)
        p["root_y"] = -4.0 * abs(math.sin(w))
        p["body"] = 6.0 + rock
        p["head"] = 4.0 - 0.8 * rock
        p["tail1"] = -0.6 * rock
        return p

    def fly(i: int, n: int, t: float) -> Pose:
        return flight(t)

    def dart(i: int, n: int, t: float) -> Pose:
        """The swallow's strike: it tips up, folds its wings back and goes
        in beak first, then throws them open to stop."""
        p = flight(t, beats=1.0)
        p["root_x"] = K([0, -14, 6, 30, 34, 16, 0], t)
        p["root_y"] = f.height + K([0, -10, -2, 6, 6, 0, 0], t)
        p["body"] = f.pitch + K([0, -18, 8, 14, 10, 4, 0], t)
        p["head"] = -0.85 * f.pitch + K([0, 6, -6, -10, -8, -2, 0], t)
        p["near_wing"] = K([-40, -10, -110, -128, -60, -30, -40], t)
        p["near_hand"] = K([0, -16, 24, 30, 0, -10, 0], t)
        p["far_wing"] = K([-34, -8, -100, -118, -54, -26, -34], t)
        p["far_hand"] = K([0, -14, 20, 26, 0, -8, 0], t)
        p["jaw"] = K([0, 8, 14, 4, 8, 2, 0], t)
        tuck(p)
        p.update(eye_at(t, ["open", "angry", "angry", "angry", "angry", "open", "open"]))
        p["fx.speed"] = K([0, 0, 0.8, 1, 0.4, 0, 0], t)
        p["fx.peck"] = K([0, 0, 0, 1, 0.6, 0, 0], t)
        return p

    def tear(i: int, n: int, t: float) -> Pose:
        """The vulture's strike, on the wing: its wings thrown up to stop, its
        bare neck reached down and its beak snapped shut on its prey."""
        p = flight(t)
        p["root_x"] = K([0, -10, -4, 12, 16, 12, 4, 0], t)
        p["root_y"] = f.height + K([0, -8, -4, 6, 8, 4, 0, 0], t)
        p["body"] = f.pitch + K([0, -20, -6, 12, 14, 8, 2, 0], t)
        p["head"] = -0.85 * f.pitch + K([0, -10, 30, 62, 58, 34, 10, 0], t)
        p["jaw"] = K([0, 18, 28, 2, 6, 2, 0, 0], t)
        p["near_wing"] = K([-50, 4, 10, -20, -70, -96, -70, -50], t)
        p["near_hand"] = K([0, -22, -26, -10, 12, 16, 8, 0], t)
        p["far_wing"] = K([-42, 2, 8, -16, -60, -84, -60, -42], t)
        p["far_hand"] = K([0, -18, -22, -10, 10, 14, 8, 0], t)
        tuck(p)
        p.update(eye_at(t, ["open", "angry", "angry", "angry", "angry", "angry", "open", "open"]))
        p["fx.peck"] = K([0, 0, 0, 1, 0.6, 0, 0, 0], t)
        return p

    def chirp(i: int, n: int, t: float) -> Pose:
        """Perched, it sings: its beak wide, its throat going, its wings flicked."""
        p = perched()
        sing = K([0, 1, 0.3, 1, 0.3, 1, 0.2, 0, 0], t)
        p["root_y"] = -3.0 * sing
        p["body"] = -8.0 * sing
        p["head"] = -14.0 * sing
        p["jaw"] = 30.0 * sing
        p["tail1"] = 10.0 * sing
        p["tail2"] = 8.0 * sing
        p["fx.notes"] = sing
        return p

    def spread(i: int, n: int, t: float) -> Pose:
        """The vulture in the sun: its wings opened wide and held, its neck
        out, a hiss."""
        p = perched()
        out = K([0, 0.5, 1, 1, 1, 1, 0.6, 0.2, 0], t)
        p.update(wings("open") if 0.08 < t < 0.92 else wings("folded"))
        p["body"] = -6.0 * out
        p["head"] = -10.0 * out + 4.0 * math.sin(math.tau * 2.0 * t)
        p["jaw"] = 20.0 * out
        p["near_wing"] = -40.0 * out
        p["near_hand"] = -12.0 * out
        p["far_wing"] = 14.0 * out
        p["far_hand"] = -24.0 * out
        p["fx.notes"] = K([0, 0, 1, 0.6, 1, 0.6, 0.2, 0, 0], t)
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
        for side, x in (("near", f.near_x), ("far", f.far_x)):
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
        p["root_x"] = K([-6, -10, -12, -8, 0, 0, 0, 0], t) + f.death_shift * K([0.3, 1, 1, 0.6, 0.2, 0.2, 0.2, 0.2], t)
        p["root_y"] = K([-8, -40, -46, f.lie * 0.2, f.lie, f.lie - 8, f.lie, f.lie], t)
        p["body"] = K([-22, -60, -110, -150, -98, -90, -94, -94], t)
        p["head"] = K([-20, -24, -10, 10, -20, -28, -24, -24], t)
        p["jaw"] = K([24, 26, 18, 22, 26, 28, 26, 26], t)
        p["tail1"] = K([12, 20, 10, 0, 0.8 * f.tail_lie, 1.1 * f.tail_lie, f.tail_lie, f.tail_lie], t)
        p["near_wing"] = K([-20, 44, 104, -20, 30, 22, 24, 24], t)
        p["near_hand"] = K([-34, 10, 20, -10, 12, 18, 16, 16], t)
        p["far_wing"] = K([-16, 40, 98, -10, 50, 46, 48, 48], t)
        p["far_hand"] = K([-30, 10, 16, -10, 8, 10, 10, 10], t)
        # The feet go limp with the body, then stick up once it lands.
        up = K([0, 0.3, 0.7, 1, 1, 1, 1, 1], t)
        legs = f.ankle_y - f.body[1]
        for side, x, local in (("near", f.near_x, (f.tuck_near[0] + 4.0, 0.95 * legs)),
                               ("far", f.far_x, (f.tuck_far[0] + 2.0, 0.92 * legs))):
            foot(p, side, local)
            if up < 1.0:
                p[f"{side}_foot_x"] = x * (1 - up) + p[f"{side}_foot_x"] * up
                p[f"{side}_foot_lift"] = p[f"{side}_foot_lift"] * up
        if t > 0.36:
            p.update(wings("folded"))
        p.update(eye_at(t, ["shut", "shut", "shut", "dead", "dead", "dead", "dead", "dead"]))
        p["fx.hit"] = K([1, 0.3, 0, 0, 0, 0, 0, 0], t)
        p["fx.feathers"] = K([0.6, 1, 1, 0.6, 0.3, 0.1, 0, 0], t)
        p["fx.dust"] = K([0, 0, 0, 0, 1, 0.6, 0.2, 0], t)
        p["fx.drift"] = K([0, 0, 0, 0.3, 0.6, 0.8, 1, 1], t)
        return p

    return {
        "idle": idle,
        "walk": hop if f.walk == "hop" else step,
        "fly": fly,
        "slash": {"dart": dart, "tear": tear}[f.attack],
        "taunt": chirp if f.taunt == "chirp" else spread,
        "hurt": hurt,
        "death": death,
    }


def spec(f: Flyer):
    return B.bird_spec(
        name=f.name,
        svg_path=PKG / "data" / "characters" / f.name / f"{f.name}.svg",
        rig_path=PKG / "targets" / "characters" / "rigged" / f.name / f"{f.name}_side.rig.json",
        view_label=f"{f.label} - Side Right",
        scale=f.scale,
        svg_center_x=CENTER_X,
        svg_ground_y=GROUND_Y,
        frame_size=f.frame,
        rows=list(f.rows),
        clips=clips(f),
        defaults={"eye.open": 1.0, "wing.folded": 1.0, "wing.open": 0.0},
        angle_channels=frozenset({"body"}),
    )


def main(argv: List[str] | None = None) -> int:
    only = set(argv or [])
    for f in FLYERS:
        if only and f.name not in only:
            continue
        s = spec(f)
        missing = sorted({name for name, *_ in s.rows} - set(s.clips))
        if missing:
            raise SystemExit(f"{s.name}: rows without clips: {missing}")
        for path in B.write(s):
            print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
