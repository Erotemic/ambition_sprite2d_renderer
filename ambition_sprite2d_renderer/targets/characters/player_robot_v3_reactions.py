"""Player Robot v3's reaction rows: hits, launches, prone, balance and stops.

The foundational silhouettes of
`docs/planning/demos/smash-expressive-fighter-poses.md`, on the robot's own rig:
a high, mid, low and airborne hit; an upward, horizontal and downward launch;
face-up and face-down prone; a teeter hold; a floor-tech brace; a run brake.
The Polygon fighters' rows (`devtools/reaction_keys.py`) give the movement
ideas. The keys here are this body's: a big head on a short trunk, with
19 px legs and short arms.

A key is in world terms (`player_robot_v3_body.WorldPose`). 0 degrees points
the way the robot faces, 90 points down. A positive lean is forward. A hit
or a launch comes from the front, so the body goes BACK (`lunge` < 0).
`tilt` turns the whole body about the hips. A tilted or `carried` body carries
its legs in its own frame (a launch, a body on the floor). Otherwise each boot
reaches for its standing place, so a planted boot stays planted.

A recoil ENDS on its settled pose: the game holds the last frame of a clip
for the hitstun. The rows of `PLANTED` are put on the floor after the solve
(`player_robot_v3_ground.plant_on_ground`): the lowest paint of each frame,
in either facing, touches the ground line, so no key sets a floor height.

The rig builder calls ``author_reactions``. Nothing here touches the
filesystem.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple

from ...authoring.rigdoc import RigDocument
from .player_robot_v3_body import SIDES, Arm, RigBody, WorldPose, rot, write_frames
from .player_robot_v3_strikes import AIR_RISE, BLADE_DRAWN_DEG, TUCK, Foot, frame_phases
from .player_robot_v3_strikes import Key as StrikeKey
from .player_robot_v3_strikes import _pose as strike_pose

ArmAngles = Tuple[float, float]


@dataclass(frozen=True)
class Key:
    """One key pose at ``at`` (0..1) of the row.

    ``near`` / ``far`` are (upper arm, forearm) in world degrees. ``None``
    holds the arm at rest, carried by the trunk. ``feet`` places boots as
    (dx, lift, toe-down pitch). ``face`` is one of the rig's faces: "open",
    "strain", "fierce" or "blink". ``ease`` shapes the approach INTO this key.
    """

    at: float
    tilt: float = 0.0
    torso: float = 0.0
    head: float = 0.0
    lunge: float = 0.0
    drop: float = 0.0
    near: Optional[ArmAngles] = None
    far: Optional[ArmAngles] = None
    feet: Dict[str, Foot] = field(default_factory=dict)
    air: bool = False
    carried: bool = False
    face: str = "open"
    squint: float = 0.0
    ease: str = "smooth"


_EASES: Dict[str, Callable[[float], float]] = {
    "linear": lambda u: u,
    "smooth": lambda u: u * u * (3.0 - 2.0 * u),
    "out": lambda u: 1.0 - (1.0 - u) ** 3,
    "in": lambda u: u ** 3,
}


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _arm(body: RigBody, key: Key, side: str) -> ArmAngles:
    arm = key.near if side == "near" else key.far
    if arm is not None:
        return arm
    rest, lean = body.arm_rest[side], key.torso + key.tilt
    return (rest.upper + lean, rest.lower + lean)


def _blend(body: RigBody, a: Key, b: Key, u: float) -> Key:
    def feet(side: str) -> Foot:
        fa, fb = a.feet.get(side, (0.0, 0.0, 0.0)), b.feet.get(side, (0.0, 0.0, 0.0))
        return tuple(_lerp(x, y, u) for x, y in zip(fa, fb))  # type: ignore[return-value]

    def arm(side: str) -> ArmAngles:
        return tuple(_lerp(x, y, u) for x, y in zip(_arm(body, a, side), _arm(body, b, side)))  # type: ignore[return-value]

    nearest = a if u < 0.5 else b
    return Key(
        at=_lerp(a.at, b.at, u),
        tilt=_lerp(a.tilt, b.tilt, u),
        torso=_lerp(a.torso, b.torso, u),
        head=_lerp(a.head, b.head, u),
        lunge=_lerp(a.lunge, b.lunge, u),
        drop=_lerp(a.drop, b.drop, u),
        near=arm("near"),
        far=arm("far"),
        feet={side: feet(side) for side in SIDES},
        # A body is airborne or it is not: the boots' frame does not blend.
        air=a.air,
        carried=a.carried or b.carried,
        face=nearest.face,
        squint=_lerp(a.squint, b.squint, u),
    )


def sample(body: RigBody, keys: Sequence[Key], phase: float) -> Key:
    """The pose at ``phase``, eased into whichever key comes next."""
    if phase <= keys[0].at:
        return keys[0]
    for a, b in zip(keys, keys[1:]):
        if phase <= b.at:
            span = max(1e-6, b.at - a.at)
            return _blend(body, a, b, _EASES[b.ease]((phase - a.at) / span))
    return keys[-1]


def channels(body: RigBody, key: Key) -> Dict[str, float]:
    """The rig channels of ``key``."""
    pelvis = 0.35 * key.torso + key.tilt
    root = (body.root[0] + key.lunge, body.root[1] + key.drop)
    world = body.sk.world({"pelvis": pelvis - body.rest["pelvis"]}, root=root)
    carried = key.tilt != 0.0 or key.carried
    ankles = {}
    for side in SIDES:
        dx, lift, pitch = key.feet.get(side, (0.0, 0.0, 0.0))
        if carried:
            # The standing ankle in the body's frame, turned with it.
            hip = world[f"{side}_leg_u"].origin
            rx = body.ankle_rest[side][0] - body.hip_rest[side][0] + dx
            ry = body.ankle_rest[side][1] - body.hip_rest[side][1] - lift
            ox, oy = rot((rx, ry), key.tilt)
            ankles[side] = ((hip[0] + ox, hip[1] + oy), body.foot_rest[side] + pitch + key.tilt)
        else:
            x, y = body.ankle_rest[side]
            if key.air:
                x, y = x + key.lunge, y + key.drop
            ankles[side] = ((x + dx, y - lift), body.foot_rest[side] + pitch)
    pose = WorldPose(
        root_x=key.lunge,
        root_y=key.drop,
        pelvis=pelvis,
        torso=key.torso + key.tilt,
        head=key.head + key.tilt,
        arms={side: Arm(*_arm(body, key, side)) for side in SIDES},
        ankles=ankles,
    )
    # The face, the ear cup, the torso front and the stowed blade are the
    # strikes' switches; the body is this solve.
    near, far = body.arm_rest["near"], body.arm_rest["far"]
    out = strike_pose(body, StrikeKey(
        at=key.at, near=(near.upper, near.lower, BLADE_DRAWN_DEG), far=(far.upper, far.lower),
        blade=0.0, face=key.face, squint=key.squint))
    out.update(body.channels(pose))
    out["head_look"] = 1.0
    return out


# ── launches ──────────────────────────────────────────────────────────────────
#
# One impact frame folds the body, then the flight shape holds. The three
# directions differ in the trunk's angle and in where the loose limbs trail.


def launch_up(body: RigBody) -> List[Key]:
    """Thrown upward: the back arched hard, the head thrown back, the arms
    flung out and down and the legs hanging long below, all trailing the
    rise. Arms flung up hide behind the big head."""
    return [
        Key(0.0, torso=16.0, head=14.0, lunge=-2.0, drop=AIR_RISE, near=(70.0, 40.0), far=(80.0, 60.0),
            air=True, carried=True, feet={"near": (2.0, 6.0, 20.0), "far": (-2.0, 5.0, 15.0)}, face="strain"),
        Key(0.3, tilt=-24.0, torso=-16.0, head=-34.0, lunge=-3.0, drop=AIR_RISE,
            near=(150.0, 170.0), far=(30.0, 50.0), air=True, carried=True,
            feet={"near": (-10.0, 0.0, 70.0), "far": (-3.0, 0.0, 60.0)}, face="strain", ease="out"),
        Key(1.0, tilt=-26.0, torso=-18.0, head=-38.0, lunge=-3.0, drop=AIR_RISE,
            near=(155.0, 175.0), far=(26.0, 46.0), air=True, carried=True,
            feet={"near": (-11.0, 0.0, 72.0), "far": (-4.0, 0.0, 62.0)}, face="strain"),
    ]


def launch_horizontal(body: RigBody) -> List[Key]:
    """Thrown back: the back leads and the body folds into a V round the
    seat, the head thrown back and the arms and legs flung forward toward the
    hit. A pike with the head forward hides the legs behind the big head."""
    return [
        Key(0.0, torso=18.0, head=12.0, lunge=-2.0, drop=AIR_RISE, near=(70.0, 40.0), far=(80.0, 60.0),
            air=True, carried=True, feet={"near": (2.0, 6.0, 20.0)}, face="strain"),
        Key(0.3, tilt=-58.0, torso=-4.0, head=-14.0, lunge=-10.0, drop=AIR_RISE,
            near=(-50.0, -40.0), far=(-30.0, -20.0), air=True, carried=True,
            feet={"near": (17.0, 6.0, -50.0), "far": (18.0, 4.0, -55.0)}, face="strain", ease="out"),
        Key(1.0, tilt=-62.0, torso=-4.0, head=-16.0, lunge=-11.0, drop=AIR_RISE,
            near=(-54.0, -44.0), far=(-34.0, -24.0), air=True, carried=True,
            feet={"near": (18.0, 6.0, -55.0), "far": (19.0, 4.0, -60.0)}, face="strain"),
    ]


def launch_down(body: RigBody) -> List[Key]:
    """Spiked downward: the body pitched head first at the floor, the arms and
    legs trailing up behind it."""
    return [
        Key(0.0, torso=20.0, head=16.0, drop=AIR_RISE, near=(40.0, 20.0), far=(50.0, 30.0),
            air=True, carried=True, feet={"near": (2.0, 6.0, 20.0)}, face="strain"),
        Key(0.3, tilt=100.0, torso=6.0, head=10.0, lunge=4.0, drop=AIR_RISE,
            near=(-120.0, -110.0), far=(-80.0, -70.0), air=True, carried=True,
            feet={"near": (-6.0, 2.0, -20.0), "far": (4.0, 4.0, -10.0)}, face="strain", ease="out"),
        Key(1.0, tilt=106.0, torso=6.0, head=10.0, lunge=4.0, drop=AIR_RISE,
            near=(-126.0, -116.0), far=(-84.0, -74.0), air=True, carried=True,
            feet={"near": (-7.0, 2.0, -24.0), "far": (5.0, 4.0, -12.0)}, face="strain"),
    ]


# ── localized hits ────────────────────────────────────────────────────────────


def _rest(body: RigBody, at: float, *, air: bool = False) -> Key:
    return Key(at, drop=AIR_RISE if air else 0.0, air=air, feet=dict(TUCK) if air else {})


def hit_high(body: RigBody) -> List[Key]:
    """Struck at the head: the big head snaps back, the chest follows, the
    arms fly up and out, the weight rocks onto the back boot."""
    return [
        _rest(body, 0.0),
        Key(0.22, torso=-14.0, head=-32.0, lunge=-4.0, drop=1.0, near=(-150.0, -170.0), far=(-30.0, -60.0),
            feet={"far": (-3.0, 2.0, -14.0)}, face="strain", ease="out"),
        Key(0.8, torso=-7.0, head=-18.0, lunge=-3.0, drop=1.0, near=(-170.0, 160.0), far=(10.0, -10.0),
            feet={"far": (-3.0, 1.0, -8.0)}, face="strain", squint=0.3),
        Key(1.0, torso=-7.0, head=-18.0, lunge=-3.0, drop=1.0, near=(-170.0, 160.0), far=(10.0, -10.0),
            feet={"far": (-3.0, 1.0, -8.0)}, face="strain", squint=0.3),
    ]


def hit_mid(body: RigBody) -> List[Key]:
    """Struck in the body: it doubles over the blow, the hips pushed back and
    the knees giving, the head pitched down and the arms folding in."""
    return [
        _rest(body, 0.0),
        Key(0.22, torso=30.0, head=30.0, lunge=-7.0, drop=6.0, near=(40.0, -20.0), far=(110.0, 170.0),
            feet={"far": (-4.0, 0.0, 0.0)}, face="strain", ease="out"),
        Key(0.8, torso=22.0, head=22.0, lunge=-6.0, drop=5.0, near=(50.0, -10.0), far=(105.0, 160.0),
            feet={"far": (-4.0, 0.0, 0.0)}, face="strain", squint=0.3),
        Key(1.0, torso=22.0, head=22.0, lunge=-6.0, drop=5.0, near=(50.0, -10.0), far=(105.0, 160.0),
            feet={"far": (-4.0, 0.0, 0.0)}, face="strain", squint=0.3),
    ]


def hit_low(body: RigBody) -> List[Key]:
    """Struck at the legs: one boot is swept back and up off the floor, the
    body pitches forward over the other, the arms thrown out for balance.
    The swept leg is the near one: the far leg swept back hides behind it."""
    return [
        _rest(body, 0.0),
        Key(0.22, torso=34.0, head=14.0, lunge=1.0, drop=5.0, near=(-140.0, -165.0), far=(-60.0, -90.0),
            feet={"near": (-20.0, 15.0, -70.0)}, face="strain", ease="out"),
        Key(0.8, torso=28.0, head=10.0, lunge=1.0, drop=4.0, near=(-150.0, -175.0), far=(-40.0, -70.0),
            feet={"near": (-18.0, 13.0, -60.0)}, face="strain", squint=0.25),
        Key(1.0, torso=28.0, head=10.0, lunge=1.0, drop=4.0, near=(-150.0, -175.0), far=(-40.0, -70.0),
            feet={"near": (-18.0, 13.0, -60.0)}, face="strain", squint=0.25),
    ]


def hit_air(body: RigBody) -> List[Key]:
    """Struck in the air: the hips swing under, the knees come up to the
    chest and the chin tucks round the blow; then it opens part way, the
    arms flung back."""
    return [
        _rest(body, 0.0, air=True),
        Key(0.22, tilt=-32.0, torso=34.0, head=16.0, lunge=-5.0, drop=AIR_RISE,
            near=(60.0, 10.0), far=(70.0, 150.0), air=True, carried=True,
            feet={"near": (10.0, 14.0, 20.0), "far": (8.0, 13.0, 16.0)}, face="strain", ease="out"),
        Key(0.8, tilt=-24.0, torso=24.0, head=8.0, lunge=-4.0, drop=AIR_RISE,
            near=(-120.0, -150.0), far=(-30.0, -60.0), air=True, carried=True,
            feet={"near": (6.0, 10.0, 20.0), "far": (4.0, 9.0, 16.0)}, face="strain", squint=0.25),
        Key(1.0, tilt=-24.0, torso=24.0, head=8.0, lunge=-4.0, drop=AIR_RISE,
            near=(-120.0, -150.0), far=(-30.0, -60.0), air=True, carried=True,
            feet={"near": (6.0, 10.0, 20.0), "far": (4.0, 9.0, 16.0)}, face="strain", squint=0.25),
    ]


# ── on the floor ──────────────────────────────────────────────────────────────


def _breath(i: int, frames: int) -> float:
    return math.sin(2.0 * math.pi * i / frames)


PRONE_FRAMES = 8


def prone_face_up(body: RigBody) -> List[Key]:
    """On the back: the back of the head, the seat and a boot on the floor,
    the visor turned up toward the feet, one knee up, the arms out on the
    floor. A slow breath in the chest.

    The head is wider than the trunk is long, so the neck bends to put the
    head down beside the trunk. The ear cup rests on the floor; turned
    further back, the antenna props the whole body off it."""
    n = PRONE_FRAMES
    return [
        Key(i / n, tilt=-80.0, torso=2.0 * _breath(i, n), head=20.0 + 1.5 * _breath(i, n),
            near=(-170.0, -175.0), far=(30.0, -10.0), carried=True,
            feet={"near": (6.0, 12.0, 20.0), "far": (6.0, 0.0, 0.0)}, face="open", squint=0.45,
            ease="linear")
        for i in range(n)
    ]


def prone_face_down(body: RigBody) -> List[Key]:
    """On the front: a face-plant. The head is pitched over onto its face on
    the floor, the ear cup up, the knees folded under and both boots on the
    floor, the arms limp at the sides.

    The head is deep from the back to the visor, so a head on its face holds
    the neck about 34 px over the floor: a trunk laid flat leaves the legs
    in the air. Folded legs reach the floor."""
    n = PRONE_FRAMES
    return [
        Key(i / n, tilt=40.0, torso=2.0 * _breath(i, n), head=35.0 + 1.5 * _breath(i, n),
            near=(150.0, 175.0), far=(80.0, 60.0), carried=True,
            feet={"near": (-4.0, -2.0, 30.0), "far": (-14.0, 6.0, 70.0)}, face="open", squint=0.45,
            ease="linear")
        for i in range(n)
    ]


# ── balance and stops ─────────────────────────────────────────────────────────


TEETER_FRAMES = 8


def teeter(body: RigBody) -> List[Key]:
    """Held off balance at an edge: bent out over it from the hips, the toe
    of the front boot up past the edge, the arms windmilling back against
    the fall."""
    n = TEETER_FRAMES
    keys = []
    for i in range(n):
        turn = 2.0 * math.pi * i / n
        sway = math.sin(turn)
        # The arms circle backward, half a turn apart.
        near = -100.0 - 75.0 * math.cos(turn)
        far = -100.0 + 75.0 * math.cos(turn)
        keys.append(Key(
            i / n, torso=26.0 + 5.0 * sway, head=14.0 + 4.0 * sway, lunge=-3.0, drop=1.0,
            near=(near, near - 20.0), far=(far, far - 20.0),
            feet={"far": (2.0, 0.0, -24.0)}, face="strain", ease="linear"))
    return keys


def tech(body: RigBody) -> List[Key]:
    """A floor tech: the body catches the landing force low and wide, the
    front hand down at the floor and the back arm thrown out, then braces
    and rises."""
    return [
        Key(0.0, torso=24.0, head=8.0, drop=5.0, near=(170.0, 175.0), far=(75.0, 85.0),
            feet={"near": (-6.0, 0.0, 0.0), "far": (6.0, 0.0, 0.0)}, face="fierce"),
        Key(0.3, torso=46.0, head=10.0, drop=8.5, lunge=-1.0, near=(185.0, 195.0), far=(52.0, 128.0),
            feet={"near": (-8.0, 0.0, 0.0), "far": (8.0, 0.0, 0.0)}, face="fierce", ease="out"),
        Key(0.6, torso=20.0, head=6.0, drop=5.0, near=(160.0, 170.0), far=(60.0, 50.0),
            feet={"near": (-6.0, 0.0, 0.0), "far": (5.0, 0.0, 0.0)}, face="fierce"),
        Key(1.0, ease="smooth", face="fierce"),
    ]


def run_stop(body: RigBody) -> List[Key]:
    """A hard stop out of a run: the front boot planted ahead on its heel,
    the hips dropped low and back, the trunk thrown back against the momentum
    and the arms flung forward with it. The game slaves the row to the first
    0.2 s of the stop."""
    return [
        Key(0.0, torso=12.0, head=6.0, drop=3.0, lunge=4.0, near=(60.0, 30.0), far=(-20.0, -40.0),
            feet={"far": (8.0, 0.0, -10.0), "near": (-6.0, 3.0, 20.0)}),
        Key(0.25, torso=-28.0, head=-16.0, drop=6.0, lunge=-3.0, near=(-30.0, -10.0), far=(-10.0, 10.0),
            feet={"far": (11.0, 0.0, -30.0), "near": (-9.0, 0.0, 6.0)}, face="strain", ease="out"),
        Key(0.6, torso=-24.0, head=-12.0, drop=5.5, lunge=-2.0, near=(-20.0, 0.0), far=(0.0, 20.0),
            feet={"far": (10.0, 0.0, -26.0), "near": (-8.0, 0.0, 5.0)}, face="strain"),
        Key(0.85, torso=-6.0, head=-3.0, drop=3.0, near=(60.0, 60.0), far=(40.0, 50.0),
            feet={"far": (6.0, 0.0, -8.0), "near": (-4.0, 0.0, 2.0)}),
        Key(1.0, ease="smooth"),
    ]


class Row(NamedTuple):
    keys: Callable[[RigBody], List[Key]]
    #: Put on the floor after the solve (`plant_on_ground`).
    planted: bool


#: Every reaction row. Frame counts and durations are `ROBOT_ROWS`'.
REACTIONS: Dict[str, Row] = {
    "launch_up": Row(launch_up, False),
    "launch_horizontal": Row(launch_horizontal, False),
    "launch_down": Row(launch_down, False),
    "hit_high": Row(hit_high, True),
    "hit_mid": Row(hit_mid, True),
    "hit_low": Row(hit_low, True),
    "hit_air": Row(hit_air, False),
    "prone_face_up": Row(prone_face_up, True),
    "prone_face_down": Row(prone_face_down, True),
    "teeter": Row(teeter, True),
    "tech": Row(tech, True),
    "run_stop": Row(run_stop, True),
}

#: The rows put on the floor after the solve.
PLANTED: Tuple[str, ...] = tuple(name for name, row in REACTIONS.items() if row.planted)


def solve_reaction(doc: RigDocument, row: str) -> Dict[str, List[float]]:
    """One number of each channel for each frame of ``row``."""
    body = RigBody(doc)
    keys = REACTIONS[row].keys(body)
    if [k.at for k in keys] != sorted(k.at for k in keys):
        raise ValueError(f"{row}: key phases must be in order")
    clip = doc.clips[row]
    phases = frame_phases(int(clip["frames"]), bool(clip.get("loop")))
    frames = [channels(body, sample(body, keys, ph)) for ph in phases]
    return {key: [f[key] for f in frames] for key in frames[0] if not key.startswith("_")}


def author_reactions(doc: RigDocument) -> None:
    """Replace the clip of each reaction row of a built v3 rig with its keys."""
    for row in REACTIONS:
        write_frames(doc, row, solve_reaction(doc, row))


__all__ = ["Key", "PLANTED", "REACTIONS", "author_reactions", "solve_reaction"]
