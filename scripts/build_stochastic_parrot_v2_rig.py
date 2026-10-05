#!/usr/bin/env python3
"""Build the Stochastic Parrot's rig documents from its SVGs.

The SVGs ``data/characters/stochastic_parrot_v2/stochastic_parrot_v2.svg``
(side), ``stochastic_parrot_v2_front.svg`` (facing the viewer) and
``stochastic_parrot_v2_three_quarter.svg`` (turned halfway) own the art
and say where every joint is; ``rigbuild.creature_rig``, with the ``bird``
anatomy, derives each skeleton, binds every part to its bone and refreshes
each SVG's rig catalog. This script supplies only what the drawings cannot
state: the frame, the rows and the clips. It never draws.

    uv run python scripts/build_stochastic_parrot_v2_rig.py

The rows keep the sheet contract ``stochastic_parrot_v2`` always published:
the same twelve rows, frame counts and durations. A turnaround turns
through a three-quarter view and the front (rigs whose clips share the
turnaround rows' names) and ends on the side rig mirrored
(``targets/characters/stochastic_parrot_v2.py`` picks the view per frame).

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
DATA = PKG / "data" / "characters" / "stochastic_parrot_v2"
RIGGED = PKG / "targets" / "characters" / "rigged" / "stochastic_parrot_v2"

# The drawing (SVG units): centre line, ground, the ankles' height, the body joint.
CENTER_X, GROUND_Y = 256.0, 416.0
ANKLE_Y = 404.0
BODY = (250.0, 328.0)
NEAR_X, FAR_X = 14.0, -6.0
#: Feet tucked up under the belly in flight (relative to the body joint).
TUCK_NEAR, TUCK_FAR = (40.0, 52.0), (26.0, 50.0)
#: A turnaround's hop (root height per frame), shared by every view of it.
HOP = [0, 8, -20, -34, -38, -34, -20, 6, 0]

#: (row, frames, ms, loops): the contract the game already reads.
ROWS = [
    ("idle", 8, 120, True),
    ("walk", 8, 95, True),
    ("fly", 10, 82, True),
    ("turnaround", 9, 82, False),
    ("turnaround_flight", 9, 74, False),
    ("dive_bomb", 9, 72, False),
    ("hover_peck", 10, 68, False),
    ("banked_strafe", 10, 74, False),
    ("slash", 8, 76, False),
    ("taunt", 10, 90, True),
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


def eye_at(t: float, frames: int, states: List[str]) -> Pose:
    """One eye state per drawn frame."""
    i = min(len(states) - 1, int(round(t * (len(states) - 1))))
    del frames
    return eyes(states[i])


def flight(t: float, *, beats: float = 1.0, pitch: float = 36.0, depth: float = 140.0, lift: float = -18.0,
           height: float = -44.0, bob: float = 8.0) -> Pose:
    """Level flight: the body pitched forward, the head held level, the tail
    trailing, the wings beating, the body rising on each downstroke."""
    p: Pose = {"body": pitch, "head": -0.8 * pitch, "tail1": -0.5 * pitch, "tail2": -6.0, "jaw": 4.0}
    p.update(flap(t, beats=beats, depth=depth, lift=lift))
    w = math.tau * t * beats
    p["root_y"] = height - bob * math.sin(w - 0.6)
    p["tail2"] += 4.0 * math.sin(w - 1.4)
    p.update(wings("open"))
    p.update(eyes("open"))
    return tuck(p)


# --- rows ---------------------------------------------------------------------------


def idle(i: int, n: int, t: float) -> Pose:
    """Perched and restless: breathing, a curious head cock, a mutter, a
    blink, the tail ticking."""
    w = math.tau * t
    p = perched()
    p["root_y"] = 3.0 * math.sin(w)
    p["body"] = -1.5 * math.sin(w)
    p["head"] = K([0, -4, -14, -14, 0, 10, 10, 2, 0], t)
    p["jaw"] = K([2, 2, 2, 12, 2, 2, 9, 2, 2], t)
    p["tail1"] = 3.0 * math.sin(w + 0.6)
    p["tail2"] = 5.0 * math.sin(w - 0.4)
    p.update(eye_at(t, n, ["open", "open", "open", "open", "shut", "open", "open", "open", "open"]))
    return p


def walk(i: int, n: int, t: float) -> Pose:
    """A parrot's waddle: short steps, the body rocking onto each foot, the
    head bobbing with the stride, the tail swinging against it."""
    p = perched()
    nx, nl, npitch = B.step(t, NEAR_X + 4.0, 14.0, 14.0)
    fx, fl, fpitch = B.step(t + 0.5, FAR_X + 4.0, 14.0, 14.0)
    p.update(near_foot_x=nx, near_foot_lift=nl, near_foot_pitch=npitch,
             far_foot_x=fx, far_foot_lift=fl, far_foot_pitch=fpitch)
    w = math.tau * t
    p["root_y"] = -7.0 * abs(math.sin(w))
    p["body"] = 6.0 + 5.0 * math.sin(2.0 * w)
    p["head"] = -6.0 - 8.0 * math.sin(2.0 * w + 0.8)
    p["tail1"] = -6.0 * math.sin(2.0 * w + 0.4)
    p["tail2"] = -8.0 * math.sin(2.0 * w - 0.4)
    p["jaw"] = 2.0
    return p


def fly(i: int, n: int, t: float) -> Pose:
    return flight(t)


def turnaround(i: int, n: int, t: float) -> Pose:
    """The side frames of a hop-turn: crouch, (the three-quarter and front
    rigs turn), land facing the other way (drawn mirrored) and settle."""
    p = perched()
    p["root_y"] = K(HOP, t)
    p["body"] = K([0, 8, 0, 0, 0, 0, 0, -6, 0], t)
    p["head"] = K([0, 10, 0, 0, 0, 0, 0, -8, 0], t)
    p["tail1"] = K([0, -6, 0, 0, 0, 0, 0, 12, 0], t)
    p["tail2"] = K([0, -4, 0, 0, 0, 0, 0, 10, 0], t)
    p["jaw"] = 2.0
    lift = K([0, 0, 20, 34, 38, 34, 20, 0, 0], t)
    p["near_foot_lift"] = p["far_foot_lift"] = lift
    return p


def turnaround_flight(i: int, n: int, t: float) -> Pose:
    p = flight(t, beats=2.0, pitch=24.0, height=-40.0)
    return p


def dive_bomb(i: int, n: int, t: float) -> Pose:
    """Climb and flare with a shriek, fold the wings and stoop nose-first,
    then throw the wings open and rake with the talons at the bottom."""
    p = flight(t, beats=1.0)
    p["root_x"] = K([0, -18, -10, 10, 30, 44, 46, 30, 14], t)
    p["root_y"] = K([-50, -76, -64, -36, -14, -10, -18, -36, -46], t)
    p["body"] = K([24, -12, 58, 78, 70, 4, -4, 18, 28], t)
    p["head"] = K([-20, -18, -30, -40, -36, 6, 4, -12, -20], t)
    p["tail1"] = K([-10, 14, -30, -36, -30, 22, 18, -6, -12], t)
    p["tail2"] = K([-4, 10, -12, -16, -14, 14, 10, -2, -4], t)
    # Wings: hovering, flared high and back, swept tight along the body
    # through the stoop, snapped open (a hard downstroke) for the strike.
    p["near_wing"] = K([-40, 16, -56, -64, -60, -140, -40, -120, -30], t)
    p["near_hand"] = K([0, -22, -40, -44, -40, 18, -12, 14, 0], t)
    p["far_wing"] = K([-30, 10, -50, -58, -54, -120, -30, -100, -20], t)
    p["far_hand"] = K([0, -20, -36, -40, -36, 14, -10, 12, 0], t)
    p["jaw"] = K([4, 26, 6, 4, 10, 22, 14, 6, 4], t)
    tuck(p)
    # The talons come forward for the strike.
    reach = K([0, 0, 0, 0, 0.4, 1, 0.8, 0.2, 0], t)
    foot(p, "near", (TUCK_NEAR[0] + 46 * reach, TUCK_NEAR[1] + 4 * reach))
    foot(p, "far", (TUCK_FAR[0] + 38 * reach, TUCK_FAR[1] + 8 * reach))
    p.update(eye_at(t, n, ["open", "angry", "angry", "angry", "angry", "angry", "angry", "open", "open"]))
    p["fx.speed"] = K([0, 0, 0.5, 1, 1, 0.3, 0, 0, 0], t)
    p["fx.squawk"] = K([0, 1, 0.4, 0, 0, 0, 0, 0, 0], t)
    p["fx.strike"] = K([0, 0, 0, 0, 0, 1, 0.5, 0, 0], t)
    p["fx.feathers"] = K([0, 0, 0, 0, 0, 0.8, 1, 0.4, 0], t)
    return p


def hover_peck(i: int, n: int, t: float) -> Pose:
    """Hovering on fast beats, two pecks: a short one, then a big one."""
    p = flight(t, beats=3.0, pitch=16.0, depth=110.0, lift=-10.0, height=-36.0, bob=5.0)
    p["root_x"] = K([0, -10, 18, 10, -14, 30, 32, 16, 4, 0], t)
    p["body"] = K([14, 4, 30, 22, 0, 36, 34, 22, 16, 14], t)
    p["head"] = K([-12, -34, 26, 8, -40, 34, 30, 6, -10, -12], t)
    p["jaw"] = K([4, 30, 0, 6, 34, 0, 2, 6, 4, 4], t)
    p["tail1"] = K([-6, 4, -16, -10, 6, -20, -20, -12, -8, -6], t)
    tuck(p)
    p.update(eye_at(t, n, ["open", "angry", "angry", "angry", "angry", "angry", "angry", "open", "open", "open"]))
    p["fx.peck"] = K([0, 0, 1, 0.2, 0, 1, 0.6, 0, 0, 0], t)
    p["fx.peck_big"] = K([0, 0, 0, 0, 0, 1, 0.6, 0, 0, 0], t)
    return p


def banked_strafe(i: int, n: int, t: float) -> Pose:
    """Bank in (the near wing dropped, the far one high: the bird rolled
    toward the viewer), rake low across with the talons, bank out."""
    p = flight(t, beats=1.0, pitch=36.0)
    bank = K([0, 0.6, 1, 1, 1, 1, 1, 0.7, 0.2, 0], t)
    p["root_x"] = K([0, -30, -24, -10, 6, 22, 34, 30, 16, 0], t)
    p["root_y"] = K([-44, -40, -26, -14, -10, -12, -18, -30, -40, -44], t)
    p["body"] = K([36, 46, 54, 50, 44, 40, 40, 44, 40, 36], t)
    p["head"] = K([-28, -36, -46, -40, -34, -30, -30, -36, -32, -28], t)
    p["near_wing"] = p["near_wing"] * (1 - bank) + bank * K([-120] * 10, t)
    p["near_hand"] = p["near_hand"] * (1 - bank) + bank * 14.0
    p["far_wing"] = p["far_wing"] * (1 - bank) + bank * 12.0
    p["far_hand"] = p["far_hand"] * (1 - bank) + bank * -18.0
    p["jaw"] = K([4, 8, 18, 22, 24, 22, 18, 10, 6, 4], t)
    tuck(p)
    rake = K([0, 0, 0.3, 1, 1, 1, 0.6, 0.1, 0, 0], t)
    foot(p, "near", (TUCK_NEAR[0] + 30 * rake, TUCK_NEAR[1] + 30 * rake))
    foot(p, "far", (TUCK_FAR[0] + 20 * rake, TUCK_FAR[1] + 34 * rake))
    p.update(eye_at(t, n, ["open", "angry", "angry", "angry", "angry", "angry", "angry", "angry", "open", "open"]))
    p["fx.speed"] = K([0, 0.5, 1, 1, 1, 1, 0.8, 0.4, 0, 0], t)
    p["fx.rake"] = K([0, 0, 0, 0.7, 1, 1, 0.5, 0, 0, 0], t)
    return p


def slash(i: int, n: int, t: float) -> Pose:
    """A wing chop: rear back with the wing cocked behind, hop in, bring the
    spread wing over the head and down in front like a blade, land."""
    p = perched()
    p.update(wings("open"))
    p["root_x"] = K([0, -8, 6, 22, 26, 20, 8, 0], t)
    p["root_y"] = K([0, 8, -30, -22, -8, 4, 2, 0], t)
    p["body"] = K([0, -16, -10, 22, 30, 16, 4, 0], t)
    p["head"] = K([0, -14, -18, 10, 16, 6, 0, 0], t)
    # The near wing: cocked back, over the top, chopped down in front.
    p["near_wing"] = K([-60, -76, 10, 118, 134, 70, -20, -60], t)
    p["near_hand"] = K([-30, -36, -20, 24, 30, 6, -20, -30], t)
    p["far_wing"] = K([-60, -70, -10, 40, 60, 20, -30, -60], t)
    p["far_hand"] = K([-30, -30, -20, 6, 10, 0, -20, -30], t)
    p["jaw"] = K([2, 16, 24, 30, 20, 8, 2, 2], t)
    p["tail1"] = K([0, 12, 16, -14, -18, -6, 4, 0], t)
    p["tail2"] = K([0, 8, 10, -10, -12, -4, 2, 0], t)
    air = K([0, 0, 1, 1, 0.4, 0, 0, 0], t)
    for side, x in (("near", NEAR_X), ("far", FAR_X)):
        p[f"{side}_foot_x"] = x + p["root_x"] * 0.9
        p[f"{side}_foot_lift"] = max(0.0, -p["root_y"]) * air + 10.0 * air
    p.update(eye_at(t, n, ["open", "angry", "angry", "angry", "angry", "angry", "open", "open"]))
    # Fold the wing away once it is back at the body.
    fold = K([1, 0, 0, 0, 0, 0, 0.0, 1], t)
    p.update({"wing.open": 1.0 - fold, "wing.folded": fold})
    p["fx.smear"] = K([0, 0, 0.6, 1, 0.6, 0, 0, 0], t)
    p["fx.dust"] = K([0, 0, 0, 0, 0, 1, 0.5, 0], t)
    return p


def taunt(i: int, n: int, t: float) -> Pose:
    """The parrot's party piece: a bobbing squawk-dance, wings half open,
    the beak gabbling, a word balloon of noise."""
    w = math.tau * t
    p = perched()
    p.update(wings("open"))
    beat = 0.5 + 0.5 * math.cos(2.0 * w)
    p["root_y"] = -14.0 * (1.0 - beat)
    p["near_foot_lift"] = p["far_foot_lift"] = 0.0
    p["body"] = -6.0 + 8.0 * math.sin(w)
    p["head"] = K([-10, 18, -20, 14, -14, 22, -18, 12, -16, 16, -10], t)
    p["jaw"] = K([24, 4, 30, 6, 26, 4, 32, 6, 22, 6, 24], t)
    # Wings raised in a display, beating to the bobs.
    p["near_wing"] = -24.0 + 20.0 * math.sin(2.0 * w)
    p["near_hand"] = -16.0 + 12.0 * math.sin(2.0 * w - 0.6)
    p["far_wing"] = -18.0 + 20.0 * math.sin(2.0 * w - 0.3)
    p["far_hand"] = -16.0 + 12.0 * math.sin(2.0 * w - 0.9)
    p["tail1"] = 10.0 * math.sin(w + 0.5)
    p["tail2"] = 12.0 * math.sin(w - 0.2)
    p.update(eye_at(t, n, ["angry", "open", "angry", "open", "angry", "open", "angry", "open", "angry", "open", "angry"]))
    p["fx.squawk"] = 1.0
    p["fx.notes"] = 1.0
    return p


def hurt(i: int, n: int, t: float) -> Pose:
    """Knocked back with a burst of feathers, wings flung, then gathering."""
    p = perched()
    p["root_x"] = K([-14, -20, -12, -4], t)
    p["root_y"] = K([-8, -4, 0, 0], t)
    p["body"] = K([-22, -28, -12, -4], t)
    p["head"] = K([-26, -20, 4, 2], t)
    p["jaw"] = K([28, 22, 8, 4], t)
    p["tail1"] = K([16, 20, 8, 2], t)
    open_ = K([1, 1, 0.6, 0], t)
    p.update({"wing.open": 1.0 if open_ > 0.5 else 0.0, "wing.folded": 0.0 if open_ > 0.5 else 1.0})
    p["near_wing"] = K([-20, -34, -70, -90], t)
    p["near_hand"] = K([-34, -28, -20, -20], t)
    p["far_wing"] = K([-16, -30, -64, -84], t)
    p["far_hand"] = K([-30, -24, -20, -20], t)
    for side, x in (("near", NEAR_X), ("far", FAR_X)):
        p[f"{side}_foot_x"] = x + 0.6 * p["root_x"]
    p.update(eye_at(t, n, ["shut", "shut", "angry", "angry"]))
    p["fx.hit"] = K([1, 0.4, 0, 0], t)
    p["fx.feathers"] = K([0.6, 1, 0.7, 0.3], t)
    return p


def death(i: int, n: int, t: float) -> Pose:
    """Struck, flung up and over in a spray of feathers, down on its back
    with its feet in the air."""
    p = perched()
    p.update(wings("open"))
    p["root_x"] = K([-14, -26, -30, -20, -6, -4, -4, -4], t)
    p["root_y"] = K([-8, -60, -66, -20, 46, 34, 46, 46], t)
    p["body"] = K([-22, -60, -110, -150, -104, -96, -100, -100], t)
    p["head"] = K([-26, -30, -10, 10, -36, -44, -40, -40], t)
    p["jaw"] = K([28, 30, 20, 26, 30, 32, 30, 30], t)
    p["tail1"] = K([16, 24, 10, 0, -40, -50, -46, -46], t)
    p["tail2"] = K([0, 10, 6, 0, -10, -14, -12, -12], t)
    p["near_wing"] = K([-20, 10, -40, -20, 30, 22, 24, 24], t)
    p["near_hand"] = K([-34, -10, -20, -10, 12, 18, 16, 16], t)
    p["far_wing"] = K([-16, 14, -30, -10, 50, 46, 48, 48], t)
    p["far_hand"] = K([-30, -10, -20, -10, 8, 10, 10, 10], t)
    # The feet go limp with the body, then stick up once it lands.
    up = K([0, 0.3, 0.7, 1, 1, 1, 1, 1], t)
    for side, x, local in (("near", NEAR_X, (36.0, 74.0)), ("far", FAR_X, (20.0, 70.0))):
        foot(p, side, local)
        if up < 1.0:
            p[f"{side}_foot_x"] = x * (1 - up) + p[f"{side}_foot_x"] * up
            p[f"{side}_foot_lift"] = p[f"{side}_foot_lift"] * up
    # Down on its back the wings fall shut against the body.
    if t > 0.5:
        p.update(wings("folded"))
    p.update(eye_at(t, n, ["shut", "shut", "shut", "dead", "dead", "dead", "dead", "dead"]))
    p["fx.hit"] = K([1, 0.3, 0, 0, 0, 0, 0, 0], t)
    p["fx.feathers"] = K([0.6, 1, 1, 0.6, 0.3, 0.1, 0, 0], t)
    p["fx.dust"] = K([0, 0, 0, 0, 1, 0.6, 0.2, 0], t)
    p["fx.drift"] = K([0, 0, 0, 0.3, 0.6, 0.8, 1, 1], t)
    return p


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {
    "idle": idle,
    "walk": walk,
    "fly": fly,
    "turnaround": turnaround,
    "turnaround_flight": turnaround_flight,
    "dive_bomb": dive_bomb,
    "hover_peck": hover_peck,
    "banked_strafe": banked_strafe,
    "slash": slash,
    "taunt": taunt,
    "hurt": hurt,
    "death": death,
}

DEFAULTS: Pose = {"eye.open": 1.0, "wing.folded": 1.0, "wing.open": 0.0}

SPEC = B.bird_spec(
    name="stochastic_parrot_v2",
    svg_path=DATA / "stochastic_parrot_v2.svg",
    rig_path=RIGGED / "stochastic_parrot_v2_side.rig.json",
    view_label="Stochastic Parrot - Side Right",
    # Drawn at 512 units square, published in the 128 px frame v2 always had.
    scale=0.25,
    svg_center_x=CENTER_X,
    svg_ground_y=GROUND_Y,
    frame_size=(128, 128),
    rows=ROWS,
    clips=CLIPS,
    defaults=DEFAULTS,
    angle_channels=frozenset({"body"}),
)


# --- the turning views: the front and the three-quarter rigs ---------------------------
#
# A turnaround's nine frames: side, side (crouch), three-quarter, front x3,
# three-quarter mirrored, side mirrored x2 (``TURN_VIEWS`` in the target).
# Every view keys the whole row on the same hop, so whichever view draws a
# frame, the bird is at the same height.


def turn_clip(head: List[float]) -> Callable[[int, int, float], Pose]:
    """A turning view mid hop-turn: up off the perch with the side rig's hop,
    the head cocked one way then the other (the parrot's look), down again."""

    def clip(i: int, n: int, t: float) -> Pose:
        p: Pose = {"root_y": K(HOP, t)}
        p["head"] = K(head, t)
        p["body"] = K([0, 0, -4, 0, 3, 0, 4, 0, 0], t)
        p["jaw"] = K([0, 0, 0, 6, 10, 4, 0, 0, 0], t)
        p["near_wing"] = p["far_wing"] = 0.0
        p.update(wings("folded"))
        return p

    return clip


def turn_flight_clip(near_sign: float) -> Callable[[int, int, float], Pose]:
    """A turning view on the wing: both wings beating with the side rig's
    flight. ``near_sign`` is the way the near wing turns on its downstroke
    (it opens to the viewer's right facing front, to the left at three
    quarters)."""

    def clip(i: int, n: int, t: float) -> Pose:
        w = math.tau * 2.0 * t
        down = 0.5 - 0.5 * math.cos(w)
        p: Pose = {"root_y": -40.0 - 8.0 * math.sin(w - 0.6)}
        p["near_wing"] = near_sign * 96.0 * down
        p["far_wing"] = -near_sign * 96.0 * down
        p["head"] = K([0, 0, -6, -10, 4, 12, 4, 0, 0], t)
        p["jaw"] = 4.0
        p.update(wings("open"))
        return p

    return clip


TURN_ROWS = [("turnaround", 9, 82, False), ("turnaround_flight", 9, 74, False)]
FRONT_SPEC = B.bird_front_spec(
    name="stochastic_parrot_v2_front",
    svg_path=DATA / "stochastic_parrot_v2_front.svg",
    rig_path=RIGGED / "stochastic_parrot_v2_front.rig.json",
    view_label="Stochastic Parrot - Front",
    scale=0.25,
    svg_center_x=CENTER_X,
    svg_ground_y=GROUND_Y,
    frame_size=(128, 128),
    rows=TURN_ROWS,
    clips={"turnaround": turn_clip([0, 0, 0, -16, 4, 20, 0, 0, 0]), "turnaround_flight": turn_flight_clip(1.0)},
    defaults={"wing.folded": 1.0, "wing.open": 0.0},
)
THREE_QUARTER_SPEC = B.bird_front_spec(
    name="stochastic_parrot_v2_three_quarter",
    svg_path=DATA / "stochastic_parrot_v2_three_quarter.svg",
    rig_path=RIGGED / "stochastic_parrot_v2_three_quarter.rig.json",
    view_label="Stochastic Parrot - Three Quarter Right",
    scale=0.25,
    svg_center_x=CENTER_X,
    svg_ground_y=GROUND_Y,
    frame_size=(128, 128),
    rows=TURN_ROWS,
    clips={"turnaround": turn_clip([0, 0, -8, 0, 0, 0, -6, 0, 0]), "turnaround_flight": turn_flight_clip(-1.0)},
    defaults={"wing.folded": 1.0, "wing.open": 0.0},
)


def main(argv: List[str] | None = None) -> int:
    del argv
    for spec in (SPEC, FRONT_SPEC, THREE_QUARTER_SPEC):
        missing = sorted({name for name, *_ in spec.rows} - set(spec.clips))
        if missing:
            raise SystemExit(f"{spec.name}: rows without clips: {missing}")
        for path in B.write(spec):
            print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
