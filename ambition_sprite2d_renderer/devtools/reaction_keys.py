"""The Polygon fighters' reaction rows: hits, launches, prone, balance and stops.

The foundational silhouettes of `docs/planning/demos/smash-expressive-fighter-poses.md`
(Phase 1): a high, mid, low and airborne hit; an upward, horizontal and
downward launch; face-up and face-down prone; a teeter hold; a floor-tech
brace; a run brake. Each is keyed in world terms on the shared pose core
(`pose_core.py`) and solved per fighter from its own rig, so one set of keys
reads on all three bodies. Nothing here knows attack timing or hitboxes.

The forward direction is the way the fighter faces. A hit or launch comes
from the front, so the body is driven BACK (`lunge` < 0) and its loose parts
lag the other way. Impacts arrive with the `out` ease (a cut); a hold eases
`smooth`. A grounded row is planted on the floor by the renderer
(`frame.plant`, the lowest visible row), so these keys never hand-tune a
floor height.

Run `python -m ambition_sprite2d_renderer.devtools.reaction_keys apply [fighter]
[--rows a,b]`, then review with `reaction_review.py`.
"""

from __future__ import annotations

import argparse
import math
from typing import Callable, Dict, List, NamedTuple, Optional, Sequence

from dataclasses import replace

from .pose_core import AIR_RISE, Body, Key, load_target

GENERATOR = "devtools/reaction_keys.py"

#: The three Polygon fighters.
FIGHTERS = ("pointed_polygon", "pugnacious_polygon", "projectile_polygon")


class Row(NamedTuple):
    keys: Callable[[Body], List[Key]]
    frames: int
    ms: int
    loop: bool
    #: The existing clip a new row's file starts from (schema and fields).
    template: str
    #: Planted on the floor by the renderer (`frame.plant` = "each").
    planted: bool


def _key(at: float, **kw) -> Key:
    return Key(at=at, **kw)


# ── launches ────────────────────────────────────────────────────────────────────
#
# A launch is the body thrown through the air: one impact frame (the hit
# folds it), then a held flight shape. The three directions differ in trunk
# angle and in which way the loose limbs trail — always opposite the travel.


def launch_up(b: Body) -> List[Key]:
    """Thrown upward: the body arched back hard, head thrown back, arms flung
    up over it and the legs trailing long below."""
    return [
        _key(0.0, torso=18.0, head=12.0, lunge=-3.0, near=(70.0, 40.0, 30.0), far=(80.0, 55.0, 40.0),
             air=True, carried=True, feet={"near": (3.0, 10.0, 25.0), "far": (-2.0, 8.0, 20.0)}),
        _key(0.3, tilt=-28.0, torso=-26.0, head=-40.0, lunge=-4.0, drop=AIR_RISE,
             near=(-128.0, -146.0, -156.0), far=(-108.0, -126.0, -136.0), air=True, carried=True,
             feet={"near": (-6.0, -4.0, -25.0), "far": (6.0, 0.0, 5.0)}, ease="out"),
        _key(1.0, tilt=-32.0, torso=-28.0, head=-42.0, lunge=-4.0, drop=AIR_RISE,
             near=(-134.0, -152.0, -162.0), far=(-112.0, -130.0, -140.0), air=True, carried=True,
             feet={"near": (-7.0, -5.0, -28.0), "far": (7.0, 0.0, 6.0)}),
    ]


def launch_horizontal(b: Body) -> List[Key]:
    """Thrown back along the ground: the hips lead, the body jackknifes
    around them, arms and legs trailing forward toward the hit."""
    return [
        _key(0.0, torso=20.0, head=14.0, lunge=-2.0, near=(60.0, 30.0, 20.0), far=(70.0, 45.0, 30.0),
             air=True, carried=True, feet={"near": (3.0, 8.0, 20.0)}),
        _key(0.3, tilt=22.0, torso=30.0, head=26.0, lunge=-10.0, drop=AIR_RISE,
             near=(12.0, 22.0, 28.0), far=(-8.0, 6.0, 14.0), air=True, carried=True,
             feet={"near": (16.0, 10.0, 30.0), "far": (10.0, 6.0, 22.0)}, ease="out"),
        _key(1.0, tilt=24.0, torso=32.0, head=28.0, lunge=-11.0, drop=AIR_RISE,
             near=(8.0, 18.0, 24.0), far=(-12.0, 2.0, 10.0), air=True, carried=True,
             feet={"near": (18.0, 11.0, 32.0), "far": (12.0, 7.0, 24.0)}),
    ]


def launch_down(b: Body) -> List[Key]:
    """Spiked downward: the body pitched head-first, limbs trailing above."""
    return [
        _key(0.0, torso=24.0, head=16.0, near=(40.0, 20.0, 10.0), far=(50.0, 30.0, 20.0),
             air=True, carried=True, feet={"near": (2.0, 10.0, 20.0)}),
        _key(0.3, tilt=78.0, torso=10.0, head=20.0, lunge=2.0,
             near=(-150.0, -158.0, -162.0), far=(-132.0, -142.0, -148.0), air=True, carried=True,
             feet={"near": (-4.0, 4.0, -10.0), "far": (3.0, 2.0, -4.0)}, ease="out"),
        _key(1.0, tilt=82.0, torso=10.0, head=20.0, lunge=2.0,
             near=(-154.0, -162.0, -166.0), far=(-136.0, -146.0, -152.0), air=True, carried=True,
             feet={"near": (-5.0, 5.0, -12.0), "far": (3.0, 2.0, -5.0)}),
    ]


# ── localized hits ─────────────────────────────────────────────────────────────
#
# A flinch in place: the struck part is driven back, the body recoils around
# it, and it comes back toward standing. One impact peak early, then a
# return; the arms are loose and lag the recoil.


# A recoil ENDS on its settled pose and does not return to rest: the
# animator holds a clip's last frame for as long as the hitstun lasts, and the
# body is drawn standing again when the hitstun ends.


def hit_high(b: Body) -> List[Key]:
    """Struck at the head: the head snaps back, the chest follows, the arms fly
    up and forward."""
    return [
        b.rest_key(0.0),
        _key(0.22, torso=-16.0, head=-34.0, lunge=-5.0, drop=2.0,
             near=(-38.0, -58.0, -66.0), far=(-20.0, -40.0, -48.0),
             feet={"near": (2.0, 0.0, 0.0), "far": (-5.0, 1.0, 8.0)}, ease="out"),
        _key(1.0, ease="smooth", torso=-8.0, head=-16.0, lunge=-4.0, drop=1.0,
             near=(40.0, 30.0, 25.0), far=(55.0, 45.0, 40.0), feet={"far": (-4.0, 0.0, 4.0)}),
    ]


def hit_mid(b: Body) -> List[Key]:
    """Struck in the body: it doubles over the blow, hips pushed back, knees
    giving, the arms folding in."""
    return [
        b.rest_key(0.0),
        _key(0.22, torso=36.0, head=22.0, lunge=-8.0, drop=7.0,
             near=(64.0, 20.0, 5.0), far=(74.0, 34.0, 18.0),
             feet={"near": (1.0, 0.0, 0.0), "far": (-6.0, 0.0, 6.0)}, ease="out"),
        _key(1.0, ease="smooth", torso=20.0, head=12.0, lunge=-6.0, drop=4.0,
             near=(75.0, 45.0, 35.0), far=(82.0, 55.0, 45.0), feet={"far": (-4.0, 0.0, 4.0)}),
    ]


def hit_low(b: Body) -> List[Key]:
    """Struck at the legs: the front foot is knocked back off the ground, the
    body pitches forward over it, the arms thrown up for balance."""
    return [
        b.rest_key(0.0),
        _key(0.22, torso=14.0, head=-8.0, lunge=-3.0, drop=3.0,
             near=(-24.0, -44.0, -52.0), far=(160.0, 170.0, 175.0),
             feet={"near": (-14.0, 7.0, -22.0), "far": (1.0, 0.0, 0.0)}, ease="out"),
        _key(1.0, ease="smooth", torso=8.0, head=-2.0, lunge=-2.0, drop=2.0,
             near=(20.0, 10.0, 5.0), far=(130.0, 140.0, 150.0), feet={"near": (-6.0, 2.0, -8.0)}),
    ]


def hit_air(b: Body) -> List[Key]:
    """Struck in the air: the body curls around the blow, knees up, and opens
    part way."""
    return [
        b.rest_key(0.0, air=True),
        _key(0.22, tilt=-10.0, torso=24.0, head=14.0, lunge=-5.0, drop=AIR_RISE,
             near=(50.0, 10.0, -5.0), far=(62.0, 24.0, 10.0), air=True, carried=True,
             feet={"near": (6.0, 16.0, 30.0), "far": (0.0, 12.0, 24.0)}, ease="out"),
        _key(1.0, ease="smooth", tilt=-4.0, torso=12.0, head=6.0, lunge=-3.0, drop=AIR_RISE,
             near=(70.0, 45.0, 35.0), far=(80.0, 55.0, 45.0), air=True, carried=True,
             feet={"near": (2.0, 12.0, 22.0), "far": (-2.0, 10.0, 18.0)}),
    ]


# ── on the floor ───────────────────────────────────────────────────────────────


def _breath(i: int, frames: int) -> float:
    return math.sin(2.0 * math.pi * i / frames)


def prone_face_up(b: Body) -> List[Key]:
    """Lying on the back, head behind, chest up, one knee raised: a slow
    breath in the chest."""
    frames = 8
    return [
        _key(i / frames, tilt=b.trunk_to(-90.0), torso=-2.0 + 2.0 * _breath(i, frames), head=-6.0 + 1.5 * _breath(i, frames),
             near=(8.0, 2.0, -4.0), far=(-150.0, -175.0, -178.0), carried=True,
             feet={"near": (10.0, 14.0, 40.0), "far": (2.0, 2.0, 10.0)}, ease="linear")
        for i in range(frames)
    ]


def prone_face_down(b: Body) -> List[Key]:
    """Lying on the front, head forward, face to the floor, one arm reaching
    ahead and one folded under."""
    frames = 8
    return [
        _key(i / frames, tilt=b.trunk_to(90.0), torso=2.0 + 2.0 * _breath(i, frames), head=10.0 + 1.5 * _breath(i, frames),
             near=(4.0, 10.0, 14.0), far=(60.0, 150.0, 170.0), carried=True,
             feet={"near": (-4.0, 6.0, -20.0), "far": (2.0, 2.0, -6.0)}, ease="linear")
        for i in range(frames)
    ]


# ── balance and stops ──────────────────────────────────────────────────────────


def teeter(b: Body) -> List[Key]:
    """Held off balance at an edge: leaning out over it from the hips, the
    front heel up, the arms windmilling against the fall."""
    frames = 8
    keys = []
    for i in range(frames):
        turn = 2.0 * math.pi * i / frames
        sway = math.sin(turn)
        keys.append(_key(
            i / frames, torso=18.0 + 4.0 * sway, head=14.0 + 2.0 * sway, lunge=-3.0,
            near=(-60.0 + 70.0 * math.cos(turn), -70.0 + 70.0 * math.cos(turn), -75.0 + 70.0 * math.cos(turn)),
            far=(-60.0 - 70.0 * math.cos(turn), -70.0 - 70.0 * math.cos(turn), -75.0 - 70.0 * math.cos(turn)),
            feet={"near": (4.0, 3.0, -22.0), "far": (-4.0, 0.0, 0.0)}, ease="linear"))
    return keys


def tech(b: Body) -> List[Key]:
    """A floor tech: the body catches the landing force low, one hand slapping
    the floor, then braces and rises."""
    return [
        # The FREE hand slaps the floor; the weapon hand swings back for balance,
        # so nothing the hand holds reaches below the feet.
        _key(0.0, torso=26.0, head=6.0, drop=14.0, near=(150.0, 160.0, 170.0), far=(70.0, 85.0, 90.0),
             feet={"near": (8.0, 0.0, 0.0), "far": (-12.0, 2.0, 28.0)}),
        _key(0.3, torso=40.0, head=6.0, drop=26.0, lunge=-2.0, near=(160.0, 172.0, 178.0), far=(84.0, 98.0, 98.0),
             feet={"near": (12.0, 0.0, 0.0), "far": (-16.0, 4.0, 60.0)}, ease="out"),
        _key(0.65, torso=22.0, head=2.0, drop=12.0, near=(150.0, 155.0, 160.0), far=(60.0, 40.0, 30.0),
             feet={"near": (6.0, 0.0, 0.0), "far": (-8.0, 1.0, 16.0)}),
        b.rest_key(1.0, ease="smooth"),
    ]


def run_stop(b: Body) -> List[Key]:
    """A hard stop out of a run: the lead foot planted ahead on its heel, the
    hips dropped back, the upper body still carried forward by the run and
    the arms flung forward against it."""
    return [
        _key(0.0, torso=10.0, head=4.0, drop=4.0, lunge=4.0, near=(40.0, 30.0, 20.0), far=(120.0, 110.0, 100.0),
             feet={"near": (14.0, 0.0, -18.0), "far": (-10.0, 3.0, 20.0)}),
        _key(0.3, torso=-16.0, head=-8.0, drop=8.0, lunge=2.0, near=(-24.0, -12.0, 0.0), far=(28.0, 36.0, 40.0),
             feet={"near": (18.0, 0.0, -24.0), "far": (-12.0, 2.0, 16.0)}, ease="out"),
        _key(0.65, torso=-6.0, head=-2.0, drop=4.0, lunge=1.0, near=(30.0, 40.0, 40.0), far=(70.0, 70.0, 65.0),
             feet={"near": (10.0, 0.0, -10.0), "far": (-6.0, 1.0, 8.0)}),
        b.rest_key(1.0, ease="smooth"),
    ]


#: Every reaction row: keys, frames, frame ms, loop, template clip, planted.
REACTIONS: Dict[str, Row] = {
    "launch_up": Row(launch_up, 7, 64, False, "launch", False),
    "launch_horizontal": Row(launch_horizontal, 7, 64, False, "launch", False),
    "launch_down": Row(launch_down, 7, 64, False, "meteor", False),
    "hit_high": Row(hit_high, 5, 48, False, "hit", True),
    "hit_mid": Row(hit_mid, 5, 48, False, "hit", True),
    "hit_low": Row(hit_low, 5, 48, False, "hit", True),
    "hit_air": Row(hit_air, 5, 48, False, "hit", False),
    "prone_face_up": Row(prone_face_up, 8, 104, True, "prone", True),
    "prone_face_down": Row(prone_face_down, 8, 104, True, "prone", True),
    "teeter": Row(teeter, 8, 92, True, "teeter", True),
    "tech": Row(tech, 6, 52, False, "tech", True),
    "run_stop": Row(run_stop, 6, 60, False, "walk_stop", True),
}

#: ANATOMY-SPECIFIC CHANGES, recorded per fighter: fields set on every key of
#: a row for that fighter's body, after review of its sheet.
ANATOMY: Dict[str, Dict[str, Dict[str, float]]] = {
    # The beast's tail spike is part of its pelvis art: lying fully on its
    # back points the tail at the floor and props the body up on it. It
    # sprawls back on its haunches instead (reviewed 2026-10-31).
    "projectile_polygon": {"prone_face_up": {"tilt": -55.0}},
}

#: The rows a target plants on the floor (`frame.plant` = "each").
PLANTED = tuple(name for name, row in REACTIONS.items() if row.planted)


def apply(fighter: str, rows: Optional[Sequence[str]] = None) -> List[str]:
    body = Body(load_target(fighter))
    written = []
    for name, row in REACTIONS.items():
        if rows and name not in rows:
            continue
        keys = row.keys(body)
        changes = ANATOMY.get(fighter, {}).get(name)
        if changes:
            keys = [replace(k, **changes) for k in keys]
        body.write_clip(name, keys, row.frames, row.ms, loop=row.loop,
                        generator=GENERATOR, template=row.template)
        written.append(name)
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("apply", help="write the reaction clips")
    a.add_argument("fighter", nargs="?", help="one fighter; default all three")
    a.add_argument("--rows", help="comma-separated rows; default every reaction row")
    args = parser.parse_args(argv)
    fighters = [args.fighter] if args.fighter else list(FIGHTERS)
    rows = args.rows.split(",") if args.rows else None
    for fighter in fighters:
        print(fighter, ", ".join(apply(fighter, rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
