"""Player Robot v3 on a wall: it lands on it, clings to it, slides down it and
kicks off it.

Jon, 2026-10-21: "Right now when you cling to a wall, you or slide down, the
pose is bad. ... we need a posed animation for jumping off of a wall, landing on
a wall, clinging to a wall, and sliding on a wall." He chose the robot to face
AWAY from the wall, out into the room (the game turns it so).

The wall is behind the robot, at the back edge of its body box (``WALL_X``).
The side view draws the robot in three-quarter, with its near shoulder at the
back of the body, so its near hand is the one that grips the wall behind it,
and its near boot the one braced on it. The rows are key poses in world terms
(``Key``): where the body is, how it leans, and where each hand and boot is.
Between the keys the poses are blended, and the elbows and the knees are
solved by two-bone IK (the elbows hang down, the knees point out).

* ``wall_land``: the body comes onto the wall, takes the hit in its knees and
  its gripping arm, and settles into the cling. The game draws it over the
  first moments on a wall (``BodyPoseView::wall_secs``).
* ``wall_grab``: the cling, held: a slow breath.
* ``wall_slide``: down the wall. The gripping hand drags high, the boot
  scrapes, the head looks down at where it goes; a small shake is the friction.
* ``wall_jump``: the kick off the wall. The game plays it over the hold of the
  kick (``WALL_JUMP_ANIM_HOLD_SECS``): a crouch against the wall, the legs
  driving back into it, then the tuck of the jump.

The antenna stays rigid on the head, by ruling (see ``player_robot_v3_gait``).

Data plus maths: the rig builder calls ``author_wall_cling`` after it has
built the side rig, and nothing here touches the filesystem.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ...authoring.rigdoc import RigDocument
from ...authoring.skeleton import two_bone_ik
from .player_robot_v3_body import SIDES, Arm, RigBody, WorldPose, rot, write_frames
from .player_robot_v3_wall_climb import _shoulders

Point = Tuple[float, float]

#: The wall, behind the robot: the back edge of its body box (57 px wide about
#: x 114.5, ``player_robot_v3.BODY_BOX_*``).
WALL_X = 86.0

#: A hand: ``("at", x, y, hand_angle)`` puts the wrist at a point (IK), and
#: ``("arm", upper, lower)`` gives the arm's world angles.
HandSpec = Tuple
#: A boot: ``(x, y, foot_angle)``, the ankle and the world angle of the foot
#: (90 points the toes straight down, so the sole faces the wall behind).
BootSpec = Tuple[float, float, float]


@dataclass(frozen=True)
class Key:
    """One key pose, in frame pixels and world degrees."""

    at: float
    root_x: float
    root_y: float
    torso: float
    head: float
    hands: Dict[str, HandSpec]
    boots: Dict[str, BootSpec]
    pelvis: Optional[float] = None
    squash: float = 1.0
    squint: float = 0.15


def _wall(dx: float) -> float:
    return WALL_X + dx


# The cling, held: the back hand grips the wall at shoulder height, the back boot
# is flat on the wall, the front knee is up, the head looks out into the room.
CLING = dict(
    root_x=5.0, root_y=-6.0, torso=4.0, head=4.0,
    hands={"near": ("at", _wall(4.0), 112.0, 200.0), "far": ("arm", 72.0, 38.0)},
    boots={"near": (_wall(6.0), 146.0, 96.0), "far": (124.0, 141.0, 34.0)},
)

ROWS: Dict[str, Tuple[Key, ...]] = {
    "wall_land": (
        # Arriving: still the fall, the arms up and out, the legs down.
        Key(0.0, root_x=3.0, root_y=-8.0, torso=-4.0, head=-6.0,
            hands={"near": ("at", 92.0, 100.0, 230.0), "far": ("arm", -20.0, -40.0)},
            boots={"near": (100.0, 156.0, 40.0), "far": (120.0, 156.0, 30.0)}, squint=0.1),
        # The hit: the back slams into the wall, the knees take it, the hand slaps.
        Key(0.3, root_x=6.0, root_y=-3.0, torso=8.0, head=10.0, squash=0.92,
            hands={"near": ("at", _wall(3.0), 110.0, 205.0), "far": ("arm", 50.0, 10.0)},
            boots={"near": (_wall(6.0), 142.0, 100.0), "far": (126.0, 138.0, 40.0)}, squint=0.4),
        Key(1.0, **CLING),
    ),
    "wall_grab": (
        Key(0.0, **CLING),
        Key(0.5, **{**CLING, "root_y": CLING["root_y"] - 0.8, "head": CLING["head"] - 1.5,
                    "hands": {"near": ("at", _wall(4.0), 111.4, 200.0), "far": ("arm", 70.0, 34.0)}}),
        Key(1.0, **CLING),
    ),
    "wall_slide": (
        # Down the wall: the back hand drags high, the head looks down, the
        # front leg reaches down to brace. Two keys a little apart are the shake
        # of the friction.
        Key(0.0, root_x=5.0, root_y=-4.0, torso=8.0, head=20.0,
            hands={"near": ("at", _wall(3.0), 102.0, 250.0), "far": ("arm", 40.0, 0.0)},
            boots={"near": (_wall(6.0), 150.0, 94.0), "far": (127.0, 151.0, 45.0)}, squint=0.35),
        Key(0.5, root_x=5.6, root_y=-4.6, torso=8.6, head=21.0,
            hands={"near": ("at", _wall(3.0), 101.2, 250.0), "far": ("arm", 38.0, -4.0)},
            boots={"near": (_wall(6.4), 150.6, 94.0), "far": (127.5, 151.0, 45.0)}, squint=0.35),
        Key(1.0, root_x=5.0, root_y=-4.0, torso=8.0, head=20.0,
            hands={"near": ("at", _wall(3.0), 102.0, 250.0), "far": ("arm", 40.0, 0.0)},
            boots={"near": (_wall(6.0), 150.0, 94.0), "far": (127.0, 151.0, 45.0)}, squint=0.35),
    ),
    "wall_jump": (
        # The crouch against the wall: both boots on it, the body low.
        Key(0.0, root_x=6.0, root_y=-3.0, torso=14.0, head=8.0, squash=0.9,
            hands={"near": ("at", _wall(4.0), 116.0, 200.0), "far": ("arm", 100.0, 60.0)},
            boots={"near": (_wall(6.0), 140.0, 100.0), "far": (_wall(14.0), 136.0, 110.0)}, squint=0.45),
        # The kick: the legs drive back into the wall, the body leans out, the
        # arms swing through.
        Key(0.35, root_x=12.0, root_y=-8.0, torso=24.0, head=4.0, squash=1.04,
            hands={"near": ("arm", 150.0, 175.0), "far": ("arm", -10.0, -30.0)},
            boots={"near": (_wall(4.0), 150.0, 70.0), "far": (_wall(10.0), 154.0, 60.0)}, squint=0.3),
        # Away: the tuck of the jump. The near arm trails back and down (it is
        # drawn over the head, so raised it would cover the face).
        Key(1.0, root_x=6.0, root_y=-12.0, torso=6.0, head=-4.0,
            hands={"near": ("arm", 160.0, 120.0), "far": ("arm", -30.0, -60.0)},
            boots={"near": (104.0, 148.0, 30.0), "far": (120.0, 146.0, 30.0)}, squint=0.1),
    ),
}

#: The frame count of each row is `ROBOT_ROWS`'s; these rows loop.
LOOPING = ("wall_grab", "wall_slide")


def _smooth(q: float) -> float:
    q = max(0.0, min(1.0, q))
    return q * q * (3.0 - 2.0 * q)


def _mix(a, b, q: float):
    if isinstance(a, tuple):
        return tuple(_mix(x, y, q) for x, y in zip(a, b))
    if isinstance(a, str):
        return a if q < 0.5 else b
    return a + (b - a) * q


def _key_at(keys: Tuple[Key, ...], t: float) -> Key:
    for a, b in zip(keys, keys[1:]):
        if a.at <= t <= b.at:
            q = _smooth((t - a.at) / max(1e-6, b.at - a.at))
            hands = {}
            for side in SIDES:
                ha, hb = a.hands[side], b.hands[side]
                if ha[0] != hb[0]:
                    # An arm that lets go of the wall (or takes it) changes
                    # spec at a key: the nearer key's spec wins.
                    hands[side] = ha if q < 0.5 else hb
                else:
                    hands[side] = (ha[0],) + _mix(ha[1:], hb[1:], q)
            return Key(
                t,
                root_x=_mix(a.root_x, b.root_x, q),
                root_y=_mix(a.root_y, b.root_y, q),
                torso=_mix(a.torso, b.torso, q),
                head=_mix(a.head, b.head, q),
                hands=hands,
                boots={side: _mix(a.boots[side], b.boots[side], q) for side in SIDES},
                pelvis=None if a.pelvis is None or b.pelvis is None else _mix(a.pelvis, b.pelvis, q),
                squash=_mix(a.squash, b.squash, q),
                squint=_mix(a.squint, b.squint, q),
            )
    return keys[-1]


def _ik(root: Point, target: Point, upper: float, lower: float, prefer) -> Tuple[float, float]:
    """The two-bone solution whose middle joint ``prefer`` picks (a key of the
    joint's point): elbows hang down, knees point out."""
    best = None
    for bend in (1.0, -1.0):
        a1, a2 = two_bone_ik(root, target, upper, lower, bend=bend)
        joint = (root[0] + upper * math.cos(math.radians(a1)), root[1] + upper * math.sin(math.radians(a1)))
        score = prefer(joint)
        if best is None or score > best[0]:
            best = (score, a1, a2)
    return best[1], best[2]


def _pose(body: RigBody, key: Key) -> Dict[str, float]:
    pose = WorldPose(
        root_x=key.root_x,
        root_y=key.root_y,
        pelvis=0.4 * key.torso if key.pelvis is None else key.pelvis,
        torso=key.torso,
        head=key.head,
        squash=key.squash,
    )
    shoulders = _shoulders(body, pose)
    for side in SIDES:
        spec = key.hands[side]
        if spec[0] == "arm":
            pose.arms[side] = Arm(spec[1], spec[2], None)
            continue
        _, x, y, hand = spec
        upper = body.sk.bones[f"{side}_arm_u"].length
        lower = body.sk.bones[f"{side}_arm_l"].length
        a1, a2 = _ik(shoulders[side], (x, y), upper, lower, prefer=lambda j: j[1])
        pose.arms[side] = Arm(a1, a2, hand)
    for side in SIDES:
        x, y, foot = key.boots[side]
        pose.ankles[side] = ((x, y), foot)
    channels = body.channels(pose)
    channels["eye_squint"] = key.squint
    return channels


def solve_row(doc: RigDocument, row: str) -> Dict[str, List[float]]:
    body = RigBody(doc)
    clip = doc.data["clips"][row]
    n = int(clip["frames"])
    loop = bool(clip.get("loop", True))
    times = [i / n for i in range(n)] if loop else [i / max(1, n - 1) for i in range(n)]
    frames = [_pose(body, _key_at(ROWS[row], t)) for t in times]
    return {k: [f[k] for f in frames] for k in frames[0] if not k.startswith("_")}


def author_wall_cling(doc: RigDocument) -> None:
    """Replace the wall rows of a built v3 side rig with the solved ones."""
    for row in ROWS:
        write_frames(doc, row, solve_row(doc, row))


__all__ = ["LOOPING", "ROWS", "WALL_X", "author_wall_cling", "solve_row"]
