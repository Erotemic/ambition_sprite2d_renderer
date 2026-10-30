#!/usr/bin/env python3
"""Build the rig documents of the ratites from their SVGs.

The SVGs ``data/characters/<bird>/<bird>.svg`` (the ``ostrich``, the ``emu``,
the ``cassowary``, the ``kiwi`` and the ``shoebill``, which has their build)
own the art and say where every joint is;
``rigbuild.creature_rig``, with the ``ratite`` anatomy, derives each skeleton,
binds every part to its bone and refreshes each SVG's rig catalog. This script
supplies only what the drawings cannot state: the frame, the rows and the
clips. It never draws.

    uv run python scripts/build_ratite_rigs.py

The small two-legged dinosaurs (the ``compsognathus``, the ``dilophosaurus``,
the ``pachycephalosaurus``) are here too: the same build, with arms on the
wing bones. They bite or ram, and the dilophosaurus has a ``shoot`` row.

They are one anatomy and one set of rows (the names the game reads), so
they share the clips: each clip is written once and takes the bird's measures
(``Bird``). What is its own is each bird's attack, the ``windup`` that
telegraphs it, and its ``taunt``:

- the three tall birds kick (``slash``): the body thrown back, the near leg
  driven forward and up. The kiwi stabs with its beak. The shoebill falls on
  its prey bill first.
- the ostrich puts its head in the sand; the emu dances; the cassowary stamps;
  the kiwi probes the ground; the shoebill clatters its bill and bows.

A tall bird that dies goes down on its hocks and its neck falls forward along
the ground. The kiwi goes over on its back.

Clips are key poses: one key per drawn frame (``K``), so a one-shot row's
frame ``i`` IS key ``i`` and a loop's last key repeats its first. Angles are
degrees added to the drawing (positive turns clockwise on screen: a positive
``body`` pitches the bird forward, a positive ``neck`` swings the head forward
and down, a negative ``<side>_wing`` raises the wing); distances are SVG
units.
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

from ambition_sprite2d_renderer.rigbuild import ratite as R  # noqa: E402
from ambition_sprite2d_renderer.rigbuild.ratite import Pose, eyes, track  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"
CENTER_X, GROUND_Y = 256.0, 416.0
ANKLE_Y = 404.0

#: (row, frames, ms, loops).
ROWS = [
    ("idle", 8, 130, True),
    ("walk", 8, 95, True),
    ("run", 8, 64, True),
    ("jump", 4, 80, True),
    ("fall", 4, 80, True),
    ("slash", 7, 68, False),
    ("taunt", 8, 110, True),
    ("hurt", 4, 92, False),
    ("death", 8, 110, False),
    # The game holds ``notice`` while a creature first sees its foe, and
    # ``windup`` over a melee move's startup (its telegraph) before the
    # attack row plays.
    ("notice", 3, 120, False),
    ("windup", 3, 90, False),
]

K = track


@dataclass(frozen=True)
class Bird:
    """What the clips need to know of one bird's drawing (SVG units)."""

    name: str
    label: str
    #: The body joint, and each ankle's x from the centre line.
    body: Tuple[float, float]
    near_x: float
    far_x: float
    #: Sprite pixels per SVG unit, and the frame.
    scale: float
    frame: Tuple[int, int]
    #: Half a step of the walk and of the run, and how high a foot lifts.
    stride: float
    run_stride: float
    lift: float
    #: How far the body comes down to sit on the ground (on its hocks).
    sit: float
    #: How its wings move when it balances (degrees at full).
    wing: float
    #: ``kick`` (a tall ratite), ``stab`` (the kiwi's beak), ``lunge`` (the
    #: shoebill's bill), ``bite`` (a small dinosaur's jaws) or ``butt`` (the
    #: pachycephalosaurus's skull).
    attack: str
    #: ``sand``, ``dance``, ``stamp``, ``probe`` or ``clatter``.
    taunt: str
    #: The height its ankles are drawn at (a drawing made smaller about a
    #: point on the ground has them lower).
    ankle_y: float = ANKLE_Y
    #: It has a ``shoot`` row too (the dilophosaurus spits).
    shoots: bool = False
    #: How far its neck falls when it dies (a part of a long bird neck's fall)
    #: and how far its head turns back up, so that a short neck with a long
    #: skull lies on the ground and not under it.
    death_neck: float = 1.0
    death_head: float = 0.0

    @property
    def leg(self) -> float:
        """The body joint's height over the ankles."""
        return self.ankle_y - self.body[1]

    @property
    def rows(self) -> List[Tuple[str, int, int, bool]]:
        return ROWS + ([("shoot", 7, 70, False)] if self.shoots else [])


BIRDS = [
    Bird("ostrich", "Ostrich", (246.0, 232.0), 8.0, -12.0, 0.5, (256, 256), 26.0, 44.0, 34.0, 130.0, 70.0, "kick", "sand"),
    Bird("ostrich_hen", "Ostrich Hen", (246.0, 232.0), 8.0, -12.0, 0.5, (256, 256), 26.0, 44.0, 34.0, 130.0, 70.0, "kick",
         "sand"),
    Bird("emu", "Emu", (244.0, 252.0), 4.0, -14.0, 0.5, (256, 256), 24.0, 40.0, 30.0, 100.0, 30.0, "kick", "dance"),
    Bird("cassowary", "Cassowary", (242.0, 258.0), 4.0, -14.0, 0.5, (256, 256), 22.0, 36.0, 28.0, 96.0, 30.0, "kick", "stamp"),
    Bird("kiwi", "Kiwi", (236.0, 332.0), 4.0, -28.0, 0.25, (128, 128), 12.0, 18.0, 12.0, 20.0, 20.0, "stab", "probe"),
    Bird("shoebill", "Shoebill", (244.0, 250.0), 2.0, -16.0, 0.5, (256, 256), 16.0, 26.0, 22.0, 100.0, 46.0, "lunge",
         "clatter"),
    # The small dinosaurs (`scripts/svg_art/dinosaurs_art.py`): the same build, with arms where a bird has wings.
    Bird("dilophosaurus", "Dilophosaurus", (236.0, 262.0), -18.0, -36.0, 0.5, (256, 256), 24.0, 40.0, 30.0, 104.0, 30.0,
         "bite", "stamp", shoots=True, death_neck=0.62, death_head=-50.0),
    Bird("pachycephalosaurus", "Pachycephalosaurus", (236.0, 262.0), -18.0, -36.0, 0.5, (256, 256), 22.0, 38.0, 28.0, 104.0,
         30.0, "butt", "stamp", death_neck=0.62, death_head=-50.0),
    # The build at 0.62 about (236, 416): its joints are where that puts them.
    Bird("compsognathus", "Compsognathus", (236.0, 320.5), -18.8, -29.9, 0.25, (128, 128), 15.0, 25.0, 18.0, 64.0, 30.0,
         "bite", "dance", ankle_y=408.6, death_neck=0.62, death_head=-50.0),
]


def eye_at(t: float, states: List[str]) -> Pose:
    """One eye state per drawn frame."""
    return eyes(states[min(len(states) - 1, int(round(t * (len(states) - 1))))])


def clips(b: Bird) -> Dict[str, Callable[[int, int, float], Pose]]:
    def foot(p: Pose, side: str, local) -> None:
        R.foot_at(p, side, local, body_origin=b.body, center_x=CENTER_X, ankle_y=b.ankle_y, pitch=30.0)

    def standing(**extra: float) -> Pose:
        p: Pose = {"near_foot_x": b.near_x, "far_foot_x": b.far_x, "near_foot_lift": 0.0, "far_foot_lift": 0.0}
        p.update(eyes("open"))
        p.update(extra)
        return p

    def wings(p: Pose, amount: float, beat: float = 0.0) -> None:
        """Raise the wings ``amount`` (0..1) of the bird's range; ``beat`` flutters them."""
        p["near_wing"] = -b.wing * amount + 0.25 * b.wing * beat
        p["far_wing"] = -0.8 * b.wing * amount - 0.25 * b.wing * beat

    def idle(i: int, n: int, t: float) -> Pose:
        """Standing: a breath, the head carried round to look, a blink."""
        w = math.tau * t
        p = standing()
        p["root_y"] = 2.0 * math.sin(w)
        p["neck"] = K([0, 0, -7, -7, 5, 5, 0, 0, 0], t)
        p["head"] = K([0, 0, 12, 12, -8, -8, 0, 0, 0], t)
        p["tail"] = 3.0 * math.sin(w + 0.6)
        wings(p, 0.0, 0.2 * math.sin(w))
        p.update(eye_at(t, ["open", "open", "open", "open", "open", "shut", "open", "open", "open"]))
        return p

    def gait(t: float, stride: float, lift: float) -> Pose:
        p = standing()
        nx, nl, npitch = R.step(t, b.near_x + 0.2 * stride, stride, lift)
        fx, fl, fpitch = R.step(t + 0.5, b.far_x + 0.2 * stride, stride, lift)
        p.update(near_foot_x=nx, near_foot_lift=nl, near_foot_pitch=npitch,
                 far_foot_x=fx, far_foot_lift=fl, far_foot_pitch=fpitch)
        return p

    def walk(i: int, n: int, t: float) -> Pose:
        """Long easy steps, the neck swinging against each one."""
        w = math.tau * t
        p = gait(t, b.stride, b.lift)
        p["root_y"] = -0.03 * b.leg * abs(math.sin(w))
        p["body"] = 2.0 + 2.0 * math.sin(2.0 * w)
        p["neck"] = 5.0 * math.sin(2.0 * w + 0.6)
        p["head"] = -5.0 * math.sin(2.0 * w + 0.6)
        p["tail"] = -4.0 * math.sin(2.0 * w + 0.4)
        wings(p, 0.0, 0.2 * math.sin(2.0 * w))
        return p

    def run(i: int, n: int, t: float) -> Pose:
        """Flat out: the body laid forward, the neck out ahead, long strides,
        the wings out for balance."""
        w = math.tau * t
        p = gait(t, b.run_stride, 1.3 * b.lift)
        p["root_y"] = 0.04 * b.leg - 0.06 * b.leg * abs(math.sin(w))
        p["body"] = 12.0 + 3.0 * math.sin(2.0 * w)
        p["neck"] = 16.0 + 5.0 * math.sin(2.0 * w + 0.6)
        p["head"] = -24.0 - 4.0 * math.sin(2.0 * w + 0.6)
        p["tail"] = 8.0 - 6.0 * math.sin(2.0 * w + 0.4)
        wings(p, 0.5, math.sin(2.0 * w))
        return p

    def airborne(t: float, *, pitch: float, tuck: float) -> Pose:
        """Off the ground: the wings beating, the legs drawn up ``tuck`` (0..1)."""
        w = math.tau * t
        p: Pose = {"body": pitch, "neck": -0.5 * pitch + 6.0, "head": -0.4 * pitch, "tail": 8.0 + 5.0 * math.sin(w)}
        p["root_y"] = -0.18 * b.leg - 0.02 * b.leg * math.sin(w)
        wings(p, 0.7, math.sin(w))
        p.update(eyes("open"))
        drop = b.leg * (1.0 - 0.34 * tuck)
        foot(p, "near", (b.near_x + CENTER_X - b.body[0] - 8.0 * tuck, drop))
        foot(p, "far", (b.far_x + CENTER_X - b.body[0] - 14.0 * tuck, drop - 0.04 * b.leg))
        return p

    def jump(i: int, n: int, t: float) -> Pose:
        return airborne(t, pitch=-10.0, tuck=1.0)

    def fall(i: int, n: int, t: float) -> Pose:
        return airborne(t, pitch=6.0, tuck=0.3)

    def kick(i: int, n: int, t: float) -> Pose:
        """The kick: the body thrown back over the far leg, the near leg
        driven forward and up with the claws leading, and set down again."""
        p = standing()
        reach = 0.56 * b.leg
        p["root_x"] = K([0, -8, -12, 4, 6, 2, 0], t)
        p["body"] = K([0, -10, -22, -26, -20, -8, 0], t)
        p["neck"] = K([0, 8, 16, 22, 16, 6, 0], t)
        p["head"] = K([0, -4, -8, -12, -8, -4, 0], t)
        p["jaw"] = K([0, 6, 14, 18, 12, 4, 0], t)
        p["tail"] = K([0, -6, -12, -14, -10, -4, 0], t)
        p["near_foot_x"] = b.near_x + reach * K([0, -0.1, 0.25, 1, 0.9, 0.3, 0], t)
        p["near_foot_lift"] = b.leg * K([0, 0.16, 0.42, 0.46, 0.36, 0.12, 0], t)
        p["near_foot_pitch"] = K([0, 20, -30, -70, -60, -20, 0], t)
        wing = K([0, 0.3, 0.8, 1, 0.7, 0.2, 0], t)
        wings(p, wing)
        p.update(eye_at(t, ["open", "angry", "angry", "angry", "angry", "open", "open"]))
        p["fx.strike"] = K([0, 0, 0, 1, 0.5, 0, 0], t)
        p["fx.rake"] = K([0, 0, 0.3, 1, 0.6, 0, 0], t)
        return p

    def stab(i: int, n: int, t: float) -> Pose:
        """The kiwi's attack: the head drawn back, the long beak run in like
        a needle with the whole body behind it."""
        p = standing()
        p["root_x"] = K([0, -8, 12, 28, 24, 8, 0], t)
        p["body"] = K([0, -12, 4, 12, 10, 4, 0], t)
        p["neck"] = K([0, -16, -6, -26, -22, -8, 0], t)
        p["head"] = K([0, -10, -20, -14, -12, -4, 0], t)
        p["jaw"] = K([0, 4, 8, 2, 4, 0, 0], t)
        p["near_foot_x"] = b.near_x + K([0, 0, 6, 14, 12, 4, 0], t)
        p.update(eye_at(t, ["open", "angry", "angry", "angry", "angry", "open", "open"]))
        p["fx.peck"] = K([0, 0, 0, 1, 0.6, 0, 0], t)
        return p

    def bite(i: int, n: int, t: float) -> Pose:
        """A bite: the head drawn back with the jaws wide, thrown forward, and
        the jaws shut on it."""
        p = standing()
        p["root_x"] = K([0, -8, 10, 24, 20, 8, 0], t)
        p["body"] = K([0, -6, 6, 14, 10, 4, 0], t)
        p["neck"] = K([0, -18, 10, 30, 24, 8, 0], t)
        p["head"] = K([0, -14, -6, 6, 4, 0, 0], t)
        p["jaw"] = K([0, 30, 36, 2, 6, 2, 0], t)
        p["tail"] = K([0, 6, -6, -10, -8, -2, 0], t)
        wings(p, K([0, 0.4, 0.8, 0.3, 0.2, 0, 0], t))
        p.update(eye_at(t, ["open", "angry", "angry", "angry", "angry", "open", "open"]))
        p["fx.peck"] = K([0, 0, 0, 1, 0.6, 0, 0], t)
        return p

    def butt(i: int, n: int, t: float) -> Pose:
        """The ram: it draws back, drops its skull and drives it forward with
        every part of it behind the blow."""
        p = standing()
        p["root_x"] = K([0, -16, -8, 34, 40, 18, 0], t)
        p["body"] = K([0, -10, 10, 20, 16, 6, 0], t)
        p["neck"] = K([0, -16, 24, 34, 28, 10, 0], t)
        p["head"] = K([0, -10, 20, 26, 20, 8, 0], t)
        p["tail"] = K([0, 8, -8, -14, -10, -4, 0], t)
        for side, x in (("near", b.near_x), ("far", b.far_x)):
            p[f"{side}_foot_x"] = x + 0.6 * p["root_x"]
        wings(p, K([0, 0.2, 0.6, 0.8, 0.5, 0.1, 0], t))
        p.update(eye_at(t, ["open", "angry", "angry", "angry", "angry", "open", "open"]))
        p["fx.peck"] = K([0, 0, 0, 1, 0.6, 0, 0], t)
        p["fx.dust"] = K([0, 0, 0.4, 1, 0.6, 0.2, 0], t)
        return p

    def shoot(i: int, n: int, t: float) -> Pose:
        """It spits: the head reared back, then thrown forward with the jaws wide."""
        p = standing()
        p["body"] = K([0, -8, -10, 4, 2, 0, 0], t)
        p["neck"] = K([0, -22, -26, 10, 6, 2, 0], t)
        p["head"] = K([0, -16, -20, 6, 4, 0, 0], t)
        p["jaw"] = K([0, 10, 40, 44, 30, 8, 0], t)
        p["tail"] = K([0, 6, 10, -6, -4, 0, 0], t)
        wings(p, K([0, 0.5, 0.8, 0.4, 0.2, 0, 0], t))
        p.update(eye_at(t, ["open", "angry", "angry", "angry", "angry", "open", "open"]))
        return p

    def lunge(i: int, n: int, t: float) -> Pose:
        """The shoebill's strike: it stands and stares, then the whole bird
        falls on its prey bill first, and it gathers itself up again."""
        p = standing()
        p["root_x"] = K([0, -4, 6, 18, 16, 6, 0], t)
        p["root_y"] = 0.3 * b.sit * K([0, 0, 0.4, 1, 0.9, 0.3, 0], t)
        p["body"] = K([0, -6, 12, 26, 22, 8, 0], t)
        p["neck"] = K([0, -12, 18, 40, 36, 12, 0], t)
        p["head"] = K([0, -6, 0, 2, 2, 0, 0], t)
        p["jaw"] = K([0, 22, 30, 2, 6, 2, 0], t)
        p["tail"] = K([0, -6, 8, 18, 14, 4, 0], t)
        wings(p, K([0, 0.1, 0.6, 1, 0.8, 0.2, 0], t))
        p.update(eye_at(t, ["open", "angry", "angry", "angry", "angry", "open", "open"]))
        p["fx.peck"] = K([0, 0, 0, 1, 0.6, 0, 0], t)
        p["fx.dust"] = K([0, 0, 0, 0.6, 1, 0.4, 0], t)
        return p

    def taunt_clatter(i: int, n: int, t: float) -> Pose:
        """The shoebill's greeting: its head thrown back and its bill
        clattered like a gun, then one slow bow."""
        p = standing()
        back = K([0, 1, 1, 1, 1, 0.4, -0.6, -0.3, 0], t)
        p["body"] = -4.0 * back
        p["neck"] = -14.0 * back
        p["head"] = -18.0 * back
        p["jaw"] = K([0, 22, 2, 22, 2, 14, 0, 0, 0], t)
        wings(p, 0.2 * max(0.0, back))
        p["fx.notes"] = K([0, 1, 0.6, 1, 0.6, 0.3, 0, 0, 0], t)
        return p

    def taunt_sand(i: int, n: int, t: float) -> Pose:
        """The ostrich's answer to a problem: down on its hocks, its head in
        the sand, and up again to see if the problem went away."""
        p = standing()
        down = K([0, 0.5, 1, 1, 1, 1, 0.5, 0, 0], t)
        p["root_y"] = 0.28 * b.sit * down
        p["body"] = 26.0 * down
        p["neck"] = 128.0 * down
        p["head"] = 14.0 * down
        p["tail"] = 14.0 * down
        wings(p, 0.3 * down, K([0, 0, 1, -1, 1, -1, 0, 0, 0], t))
        p.update(eye_at(t, ["open", "open", "shut", "shut", "shut", "shut", "open", "open", "open"]))
        p["fx.dust"] = K([0, 0, 1, 0.6, 0.8, 0.5, 0.2, 0, 0], t)
        return p

    def taunt_dance(i: int, n: int, t: float) -> Pose:
        """The emu's dance: it bounces from foot to foot, its neck weaving, its beak open."""
        w = math.tau * t
        p = standing()
        hop = abs(math.sin(2.0 * w))
        p["root_y"] = -0.07 * b.leg * hop
        p["body"] = 6.0 * math.sin(2.0 * w)
        p["neck"] = 14.0 * math.sin(2.0 * w + 0.5)
        p["head"] = -16.0 * math.sin(2.0 * w + 0.9)
        p["jaw"] = 16.0 + 10.0 * math.sin(4.0 * w)
        p["tail"] = 10.0 * math.sin(2.0 * w)
        p["near_foot_lift"] = 0.12 * b.leg * max(0.0, math.sin(2.0 * w))
        p["far_foot_lift"] = 0.12 * b.leg * max(0.0, -math.sin(2.0 * w))
        wings(p, 0.6, math.sin(4.0 * w))
        p["fx.notes"] = 1.0
        return p

    def taunt_stamp(i: int, n: int, t: float) -> Pose:
        """The cassowary's warning: drawn up to its full height, its neck
        swelled and booming, and one foot brought down hard, twice."""
        p = standing()
        up = K([0, 0.6, 1, 1, 1, 1, 0.8, 0.3, 0], t)
        p["root_y"] = -0.04 * b.leg * up
        p["body"] = -8.0 * up
        p["neck"] = -8.0 * up
        p["head"] = 14.0 * up
        p["jaw"] = K([0, 10, 20, 8, 20, 8, 14, 4, 0], t)
        p["near_foot_lift"] = 0.2 * b.leg * K([0, 0.6, 1, 0, 1, 0, 0, 0, 0], t)
        p["near_foot_x"] = b.near_x + 0.1 * b.leg * K([0, 0.6, 1, 1, 1, 1, 0.5, 0, 0], t)
        wings(p, 0.8 * up)
        p.update(eye_at(t, ["open", "angry", "angry", "angry", "angry", "angry", "angry", "open", "open"]))
        p["fx.dust"] = K([0, 0, 0, 1, 0.3, 1, 0.4, 0, 0], t)
        p["fx.notes"] = up
        return p

    def taunt_probe(i: int, n: int, t: float) -> Pose:
        """The kiwi feeds: its beak run into the ground again and again, sniffing."""
        p = standing()
        dip = K([0, 1, 0.4, 1, 0.4, 1, 0.2, 0, 0], t)
        p["root_x"] = 6.0 * dip
        p["body"] = 16.0 * dip
        p["neck"] = 10.0 * dip
        p["head"] = 12.0 * dip
        p["jaw"] = 6.0 * (1.0 - dip)
        p["fx.dust"] = 0.6 * dip
        return p

    def hurt(i: int, n: int, t: float) -> Pose:
        """Knocked back: the neck whipped back, the wings thrown out, a foot
        slid under it to stay up."""
        p = standing()
        p["root_x"] = K([-14, -22, -14, -4], t)
        p["root_y"] = K([-6, -2, 0, 0], t)
        p["body"] = K([-16, -22, -10, -2], t)
        p["neck"] = K([-26, -18, 6, 2], t)
        p["head"] = K([22, 14, -4, 0], t)
        p["jaw"] = K([24, 18, 6, 2], t)
        p["tail"] = K([14, 18, 8, 2], t)
        wings(p, K([1, 0.8, 0.4, 0], t))
        for side, x in (("near", b.near_x), ("far", b.far_x)):
            p[f"{side}_foot_x"] = x + 0.6 * p["root_x"]
        p.update(eye_at(t, ["shut", "shut", "angry", "angry"]))
        p["fx.hit"] = K([1, 0.4, 0, 0], t)
        p["fx.feathers"] = K([0.6, 1, 0.7, 0.3], t)
        return p

    def death_tall(i: int, n: int, t: float) -> Pose:
        """Struck, it sways, its legs fold under it (down on its hocks, as a
        bird sits) and its neck falls forward along the ground."""
        p = standing()
        p["root_x"] = K([-12, -18, -10, -4, 0, 0, 0, 0], t)
        p["root_y"] = b.sit * K([-0.04, 0, 0.3, 0.75, 1, 0.96, 1, 1], t)
        p["body"] = K([-16, -20, -8, 4, 8, 6, 8, 8], t)
        fall = K([0, 0, 0.1, 0.5, 1, 1, 1, 1], t)
        p["neck"] = K([-24, -10, 10, 50, 96, 104, 100, 100], t) * (1.0 + (b.death_neck - 1.0) * fall)
        p["head"] = K([20, 10, 0, -10, -4, 6, 4, 4], t) + b.death_head * fall
        p["jaw"] = K([24, 20, 14, 10, 16, 20, 18, 18], t)
        p["tail"] = K([14, 16, 8, 0, -8, -4, -6, -6], t)
        wings(p, K([1, 0.8, 0.5, 0.6, 0.2, 0, 0, 0], t))
        p.update(eye_at(t, ["shut", "shut", "shut", "dead", "dead", "dead", "dead", "dead"]))
        p["fx.hit"] = K([1, 0.3, 0, 0, 0, 0, 0, 0], t)
        p["fx.feathers"] = K([0.6, 1, 0.8, 0.4, 0.2, 0, 0, 0], t)
        p["fx.dust"] = K([0, 0, 0, 0.4, 1, 0.6, 0.2, 0], t)
        return p

    def death_small(i: int, n: int, t: float) -> Pose:
        """Struck, flung up and over, down on its back with its feet in the air."""
        p = standing()
        p["root_x"] = K([-14, -26, -30, -20, -6, -4, -4, -4], t)
        p["root_y"] = K([-8, -50, -56, -20, 20, 14, 20, 20], t)
        p["body"] = K([-22, -60, -110, -150, -168, -160, -164, -164], t)
        p["neck"] = K([-16, -10, 0, 6, 10, 14, 12, 12], t)
        p["head"] = K([10, 6, 0, -6, -10, -14, -12, -12], t)
        p["jaw"] = K([20, 22, 16, 18, 20, 22, 20, 20], t)
        up = K([0, 0.3, 0.7, 1, 1, 1, 1, 1], t)
        for side, x, local in (("near", b.near_x, (22.0, 0.9 * b.leg)), ("far", b.far_x, (-8.0, 0.86 * b.leg))):
            foot(p, side, local)
            if up < 1.0:
                p[f"{side}_foot_x"] = x * (1 - up) + p[f"{side}_foot_x"] * up
                p[f"{side}_foot_lift"] = p[f"{side}_foot_lift"] * up
        p.update(eye_at(t, ["shut", "shut", "shut", "dead", "dead", "dead", "dead", "dead"]))
        p["fx.hit"] = K([1, 0.3, 0, 0, 0, 0, 0, 0], t)
        p["fx.feathers"] = K([0.6, 1, 1, 0.6, 0.3, 0.1, 0, 0], t)
        p["fx.dust"] = K([0, 0, 0, 0, 1, 0.6, 0.2, 0], t)
        return p

    def notice(i: int, n: int, t: float) -> Pose:
        """Startled by its foe: drawn up tall, head up and back, beak open,
        wings or arms thrown up and the tail raised. Held, with a shiver."""
        p = standing()
        up = K([0.92, 1, 0.96], t)
        p["root_y"] = -0.05 * b.leg * up
        p["body"] = -12.0 * up
        p["neck"] = -26.0 * up
        p["head"] = 12.0 * up + K([0, 0, -3], t)
        p["jaw"] = K([18, 26, 22], t)
        p["tail"] = 22.0 * up
        wings(p, 0.9 * up, K([0, 0.4, -0.4], t))
        p.update(eyes("open"))
        return p

    def windup_kick(t: float, tremble: float) -> Pose:
        """Back on the far leg, the body thrown back, the near leg drawn up
        and cocked with its claws turned back."""
        p = standing()
        p["root_x"] = -12.0 + tremble
        p["root_y"] = 0.04 * b.leg
        p["body"] = -22.0
        p["neck"] = 18.0
        p["head"] = -10.0
        p["jaw"] = 14.0
        p["tail"] = 6.0
        p["near_foot_x"] = b.near_x - 0.06 * b.leg + tremble
        p["near_foot_lift"] = 0.40 * b.leg
        p["near_foot_pitch"] = 34.0
        p["far_foot_x"] = b.far_x - 4.0
        wings(p, 0.9, tremble / 2.0)
        return p

    def windup_bite(t: float, tremble: float) -> Pose:
        """Coiled: down on its hocks, weight back, the neck drawn back in an S
        and the jaws open, the tail up."""
        p = standing()
        p["root_x"] = -10.0 + tremble
        p["root_y"] = 0.18 * b.leg
        p["body"] = 12.0
        p["neck"] = -16.0
        p["head"] = 14.0
        p["jaw"] = 34.0 + 2.0 * tremble
        p["tail"] = 14.0 + tremble
        for side, x in (("near", b.near_x), ("far", b.far_x)):
            p[f"{side}_foot_x"] = x - 4.0
        wings(p, 0.6, tremble / 2.0)
        return p

    def windup_butt(t: float, tremble: float) -> Pose:
        """Head lowered, the dome aimed, the weight drawn back and the far
        (back) foot scraping the ground."""
        p = standing()
        p["root_x"] = -20.0 + tremble
        p["root_y"] = 0.10 * b.leg
        p["body"] = 8.0
        p["neck"] = 22.0
        p["head"] = 6.0
        p["tail"] = 8.0
        p["near_foot_x"] = b.near_x - 6.0
        p["far_foot_x"] = b.far_x - 10.0 + K([0, -18, -6], t)
        p["far_foot_lift"] = K([10, 0, 8], t)
        p["far_foot_pitch"] = K([20, 0, 16], t)
        p["fx.dust"] = K([0, 0.9, 0.2], t)
        wings(p, 0.2)
        return p

    def windup_stab(t: float, tremble: float) -> Pose:
        """The beak drawn back like a needle, the body low behind it."""
        p = standing()
        p["root_x"] = -12.0 + tremble
        p["root_y"] = 0.06 * b.leg
        p["body"] = -14.0
        p["neck"] = -22.0
        p["head"] = 2.0
        p["jaw"] = 4.0
        return p

    def windup_lunge(t: float, tremble: float) -> Pose:
        """It stares: drawn up over its prey, the bill aimed, everything still
        but a shiver."""
        p = standing()
        p["root_x"] = -6.0 + tremble
        p["body"] = -8.0
        p["neck"] = -16.0
        p["head"] = 4.0
        p["tail"] = 4.0
        wings(p, 0.4, tremble / 2.0)
        return p

    windups = {"kick": windup_kick, "bite": windup_bite, "butt": windup_butt,
               "stab": windup_stab, "lunge": windup_lunge}

    def windup(i: int, n: int, t: float) -> Pose:
        """The telegraph of the attack: a held anticipation pose with a
        shiver (the game loops it)."""
        p = windups[b.attack](t, K([0, 1.5, -1.5], t))
        if i == 0:
            p["root_x"] = 0.92 * p["root_x"]
        p.update(eyes("angry"))
        return p

    taunts = {"sand": taunt_sand, "dance": taunt_dance, "stamp": taunt_stamp, "probe": taunt_probe,
              "clatter": taunt_clatter}
    attacks = {"kick": kick, "stab": stab, "lunge": lunge, "bite": bite, "butt": butt}
    return {
        "idle": idle,
        "walk": walk,
        "run": run,
        "jump": jump,
        "fall": fall,
        "slash": attacks[b.attack],
        "taunt": taunts[b.taunt],
        "hurt": hurt,
        "death": death_small if b.attack == "stab" else death_tall,
        "notice": notice,
        "windup": windup,
        **({"shoot": shoot} if b.shoots else {}),
    }


def spec(b: Bird):
    return R.ratite_spec(
        name=b.name,
        svg_path=PKG / "data" / "characters" / b.name / f"{b.name}.svg",
        rig_path=PKG / "targets" / "characters" / "rigged" / b.name / f"{b.name}_side.rig.json",
        view_label=f"{b.label} - Side Right",
        scale=b.scale,
        svg_center_x=CENTER_X,
        svg_ground_y=GROUND_Y,
        frame_size=b.frame,
        rows=b.rows,
        clips=clips(b),
        defaults={"eye.open": 1.0},
        angle_channels=frozenset({"body", "neck"}),
    )


def main(argv: List[str] | None = None) -> int:
    only = set(argv or [])
    for b in BIRDS:
        if only and b.name not in only:
            continue
        s = spec(b)
        missing = sorted({name for name, *_ in s.rows} - set(s.clips))
        if missing:
            raise SystemExit(f"{s.name}: rows without clips: {missing}")
        for path in R.write(s):
            print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
