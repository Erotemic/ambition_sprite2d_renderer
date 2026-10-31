"""Bespoke fighter choreography refinements for the Perfect Cellular Automaton.

The first full-fighter pass intentionally seeded many semantic rows from PCA's
existing authored poses.  This pass graduates the important Smash-facing rows
from aliases into deliberate choreography while preserving the SVG geometry and
all unrelated GUI-authored clips.
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Mapping, MutableMapping, Sequence

from ...profiling import profile


def _keys(values: Sequence[float], times: Sequence[float] | None = None, *, ease: str = "smooth") -> dict:
    vals = [float(v) for v in values]
    if times is None:
        denom = max(1, len(vals) - 1)
        ts = [i / denom for i in range(len(vals))]
    else:
        ts = [float(v) for v in times]
    if len(vals) != len(ts):
        raise ValueError("keyframe values/times length mismatch")
    return {"keys": [[round(t, 4), round(v, 4), ease] for t, v in zip(ts, vals)]}


def _replace_channels(clip: Mapping[str, object], replacements: Mapping[str, object]) -> dict:
    out = deepcopy(dict(clip))
    channels = deepcopy(dict(out.get("channels") or {}))
    channels.update(deepcopy(dict(replacements)))
    out["channels"] = channels
    out["loop"] = False
    return out


# --- Fight poses ------------------------------------------------------------
#
# PCA's attacks start and end in one fighting stance (the rig's `fight_idle`
# clip at rest: knees bent, lead hand out, rear hand at the chest). Each pose
# names its arms by WORLD angle -- 0 forward (+x), 90 down, -90 up, 180 back --
# as (upper arm, forearm, hand), so a pose reads as where the limb points
# rather than as offsets from the drawn rest. The far arm is the lead arm and
# draws behind the torso; the near arm is the rear arm and draws in front.

_ARM_REST = {"far": (78.434, 13.035, 8.811), "near": (104.338, -11.296, -14.124)}
_LEGS = {
    "near_foot_x": -23.0,
    "far_foot_x": 18.0,
    "near_foot_lift": 0.0,
    "far_foot_lift": 0.0,
    "near_foot_pitch": 50.96,
    "far_foot_pitch": 27.34,
}
_GUARD_FAR = (30.4, -21.6, -22.8)
_GUARD_NEAR = (51.3, -15.0, -39.1)

# Swap parts drawn by `scripts/svg_art/pca_swap_parts.py`: one channel per
# variant, `<slot>.<variant>`; the drawn art is `<slot>.open`.
_SWAPS = {
    "near_hand": ("open", "fist", "palm", "claw"),
    "far_hand": ("open", "fist", "palm", "claw"),
    "eyes": ("open", "fierce", "smug", "wide", "laugh"),
}


def _arm(side: str, torso: float, upper: float, lower: float, hand: float) -> dict:
    rest_u, rest_l, rest_h = _ARM_REST[side]
    return {
        f"{side}_arm_u": upper - torso - rest_u,
        f"{side}_arm_l": lower - upper - rest_l,
        f"{side}_arm_hand": hand - lower - rest_h,
    }


def _pose(
    torso: float = 7.0,
    far: Sequence[float] = _GUARD_FAR,
    near: Sequence[float] = _GUARD_NEAR,
    root_x: float = 0.0,
    root_y: float = 9.0,
    head: float = -6.0,
    near_hand: str = "open",
    far_hand: str = "open",
    eyes: str = "fierce",
    **legs: float,
) -> dict:
    """One full-body fight pose; anything unnamed stays in the stance."""
    pose = {"root_x": root_x, "root_y": root_y, "torso": torso, "head": head}
    pose.update(_arm("far", torso, *far))
    pose.update(_arm("near", torso, *near))
    pose.update(_LEGS)
    pose.update(legs)
    chosen = {"near_hand": near_hand, "far_hand": far_hand, "eyes": eyes}
    for slot, variants in _SWAPS.items():
        if chosen[slot] not in variants:
            raise ValueError(f"PCA has no {slot} variant {chosen[slot]!r}")
        for variant in variants:
            pose[f"{slot}.{variant}"] = 1.0 if variant == chosen[slot] else 0.0
    return pose


def _pose_channels(poses: Sequence[dict], eases: Sequence[str]) -> dict:
    """Key one pose per published frame (one-shot frame times are i/(n-1))."""
    denom = max(1, len(poses) - 1)
    channels = {}
    for name in poses[0]:
        values = [round(float(pose[name]), 3) for pose in poses]
        if all(value == values[0] for value in values):
            channels[name] = {"const": values[0]}
        else:
            # A part swap cuts on its frame; it never cross-fades.
            hold = "." in name
            channels[name] = {
                "keys": [[round(i / denom, 4), value, "hold" if hold else ease]
                         for i, (value, ease) in enumerate(zip(values, eases))]
            }
    return channels


def _strike(*poses: dict, contact: int) -> dict:
    """Frames ease into each pose; the contact frame snaps in (`out`)."""
    eases = ["smooth"] * len(poses)
    eases[contact] = "out"
    return _pose_channels(poses, eases)


_LEAD_HOME = (95, -50, -60)
_KICK = dict(
    torso=-16, root_x=-6, root_y=4, head=-2, far=(150, 120, 110), near=(60, -40, -60),
    far_foot_x=56, far_foot_lift=56, far_foot_pitch=0, near_foot_x=-20, near_hand="fist", far_hand="fist",
)
_SWEEP = dict(
    root_y=24, torso=22, head=-14, root_x=2, far=(120, 60, 50), near=(80, 95, 95),
    far_foot_x=50, far_foot_lift=10, far_foot_pitch=-5, near_foot_x=-14, near_hand="palm",
)
_LUNGE = dict(
    torso=20, root_x=12, root_y=12, head=-10, far=(0, -2, -5), near=(-8, -6, -10),
    far_foot_x=40, near_foot_x=-30, near_foot_pitch=75, near_hand="palm", far_hand="palm",
)
# Both hands drawn back past the rear hip: the smash wind-up.
_COIL = dict(
    torso=-12, root_x=-5, root_y=17, head=-2, near=(165, 115, 95), far=(165, 150, 140),
    far_foot_x=20, near_foot_x=-25, near_hand="fist", far_hand="fist",
)
_PALMS = dict(
    torso=20, root_x=12, root_y=13, head=-6, far=(10, 8, -55), near=(16, 12, -50),
    far_foot_x=40, near_foot_x=-28, near_foot_pitch=78, near_hand="palm", far_hand="palm", eyes="wide",
)
_SQUAT = dict(
    root_y=22, torso=18, head=-2, near=(100, 70, 60), far=(90, 70, 60), near_foot_x=-20, far_foot_x=18,
)
_REACH_UP = dict(
    root_y=0, torso=-6, head=-22, near=(-95, -97, -100), far=(-85, -88, -92),
    near_foot_x=-18, far_foot_x=16, near_foot_lift=2, far_foot_lift=2,
    near_foot_pitch=70, far_foot_pitch=50, near_hand="palm", far_hand="palm",
)
_RAISE = dict(
    root_y=4, torso=-4, head=-14, near=(-110, -120, -130), far=(-70, -60, -50), near_hand="claw", far_hand="claw",
)
_SLAM = dict(
    root_y=24, torso=10, head=-2, near=(150, 140, 135), far=(40, 50, 55), near_foot_x=-26, far_foot_x=24,
    near_hand="palm", far_hand="palm",
)


def _fight_moves() -> dict:
    """Channels for each ground attack, one pose per published frame."""
    return {
        # Lead hand snaps straight out; the rear hand stays home.
        "jab": _strike(
            _pose(),
            _pose(torso=5, root_x=-1, far=(45, -40, -40), far_hand="fist"),
            _pose(torso=11, root_x=3, far_foot_x=22, head=-4, far=(-4, -2, 0), far_hand="fist"),
            _pose(torso=9, root_x=2, far_foot_x=21, far=(15, -15, -15), far_hand="fist"),
            _pose(),
            contact=2,
        ),
        # Rear-hand cross: the hips drive it, the back heel lifts, the lead hand comes home.
        "punch": _strike(
            _pose(),
            _pose(torso=2, root_x=-3, near=(80, -30, -45), near_hand="fist"),
            _pose(torso=21, root_x=10, root_y=11, head=-3, near=(16, 10, 8), far=_LEAD_HOME,
                  near_foot_lift=4, near_foot_pitch=76, far_foot_x=26, near_hand="fist", far_hand="fist"),
            _pose(torso=20, root_x=10, root_y=11, head=-3, near=(18, 12, 10), far=_LEAD_HOME,
                  near_foot_lift=3, near_foot_pitch=72, far_foot_x=26, near_hand="fist", far_hand="fist"),
            _pose(torso=12, root_x=4, near=(40, -15, -30), near_hand="fist"),
            _pose(),
            contact=2,
        ),
        # Overhand rake with the rear claw, high-front to low-front; the camera-side
        # arm keeps the wind-up visible beside the head.
        "slash": _strike(
            _pose(),
            _pose(torso=-10, root_x=-4, head=-10, near=(-115, -150, -165), far=(60, -30, -40), near_hand="claw"),
            _pose(torso=6, root_x=3, head=-8, near=(-30, -20, -10), far=(80, -20, -40), near_hand="claw"),
            _pose(torso=16, root_x=7, far_foot_x=25, head=-3, near=(15, 25, 40), far=(100, -10, -30),
                  near_hand="claw"),
            _pose(torso=20, root_x=7, far_foot_x=25, head=-2, near=(60, 75, 90), far=(100, -10, -30),
                  near_hand="claw"),
            _pose(torso=13, root_x=4, far_foot_x=21, near=(70, 30, 10)),
            _pose(),
            contact=2,
        ),
        # Forward tilt: lead-leg side kick at hip height, leaning back to balance.
        "attack_side": _strike(
            _pose(),
            _pose(torso=-8, root_x=-5, root_y=6, far_foot_x=24, far_foot_lift=30, far_foot_pitch=45,
                  near_foot_x=-20, far=(120, 60, 40)),
            _pose(**_KICK),
            _pose(**{**_KICK, "far_foot_x": 54, "far_foot_lift": 54}),
            _pose(torso=-6, root_x=-4, root_y=6, far_foot_x=24, far_foot_lift=28, far_foot_pitch=45,
                  near_foot_x=-20, far=(110, 50, 30)),
            _pose(),
            contact=2,
        ),
        # Up tilt: dips, then rakes the lead claw from the front up over his head.
        "attack_up": _strike(
            _pose(),
            _pose(root_y=14, torso=12, far=(60, 20, 10)),
            _pose(root_y=3, torso=0, head=-14, far=(-60, -70, -75), near=(70, 10, -10), far_hand="claw"),
            _pose(root_y=3, torso=-6, head=-18, far=(-100, -110, -120), near=(75, 20, 0), far_hand="claw"),
            _pose(root_y=7, torso=3, head=-9, far=(-30, -60, -70)),
            _pose(),
            contact=2,
        ),
        # Down tilt: drops low on the rear hand and sweeps the lead foot along the floor.
        "attack_down": _strike(
            _pose(),
            _pose(root_y=22, torso=18, head=-12, far=(70, -10, -20), near=(80, 85, 85),
                  far_foot_x=24, far_foot_lift=6, near_foot_x=-16),
            _pose(**_SWEEP),
            _pose(**{**_SWEEP, "far_foot_x": 48}),
            _pose(root_y=18, torso=14, head=-10, far_foot_x=26, near_foot_x=-18),
            _pose(),
            contact=2,
        ),
        # Out of the run into a lunging double palm strike.
        "dash_attack": _strike(
            _pose(torso=14, root_y=6),
            _pose(torso=6, root_x=2, root_y=8, far=(120, -10, -20), near=(130, 0, -10), far_foot_x=26,
                  near_hand="fist", far_hand="fist"),
            _pose(**_LUNGE),
            _pose(**{**_LUNGE, "root_x": 14, "far_foot_x": 42}),
            _pose(**{**_LUNGE, "root_x": 14, "far_foot_x": 42, "torso": 18}),
            _pose(torso=12, root_x=7, root_y=11, far=(40, -10, -20), far_foot_x=30, near_foot_x=-26),
            _pose(),
            contact=2,
        ),
        # Coil at the hip, then both palms thrust out on a long lunge.
        "smash_forward": _strike(
            _pose(),
            _pose(**_COIL),
            _pose(**{**_COIL, "torso": -15, "root_x": -7}),
            _pose(**_PALMS),
            _pose(**{**_PALMS, "root_x": 14, "far_foot_x": 42}),
            _pose(**{**_PALMS, "root_x": 14, "far_foot_x": 42, "torso": 18}),
            _pose(torso=12, root_x=7, root_y=11, far=(30, -10, -20), far_foot_x=30, near_foot_x=-26),
            _pose(),
            contact=3,
        ),
        # Squat with the palms low, then explode up with both arms straight overhead.
        "smash_up": _strike(
            _pose(),
            _pose(**_SQUAT),
            _pose(**{**_SQUAT, "root_y": 24}),
            _pose(**_REACH_UP),
            _pose(**{**_REACH_UP, "root_y": -1}),
            _pose(**{**_REACH_UP, "torso": -4, "head": -18}),
            _pose(root_y=6, torso=2, head=-10, near=(-20, -60, -70), far=(-10, -50, -60)),
            _pose(),
            contact=3,
        ),
        # Both claws rise overhead, then slam to the floor on either side.
        "smash_down": _strike(
            _pose(),
            _pose(**_RAISE),
            _pose(**{**_RAISE, "root_y": 2, "head": -18}),
            _pose(**_SLAM),
            _pose(**{**_SLAM, "root_y": 26}),
            _pose(**{**_SLAM, "root_y": 25}),
            _pose(root_y=15, torso=8, head=-5, near=(110, 80, 70), far=(60, 20, 10)),
            _pose(),
            contact=3,
        ),
    }


def _smash_charge() -> dict:
    """The held wind-up every smash charges from: the coil, trembling."""
    channels = _pose_channels([_pose(**_COIL)], ["smooth"])
    channels["torso"] = {"expr": "-12+1.2*sin(4*tau*t)"}
    channels["root_x"] = {"expr": "-5+0.7*sin(6*tau*t)"}
    channels["head"] = {"expr": "-2+1.0*sin(4*tau*(t-0.1))"}
    return channels


# --- Reactions ---------------------------------------------------------------
#
# The Smash reaction vocabulary (docs/planning/demos/smash-expressive-fighter-poses.md)
# on PCA's own rig and manner: struck, PCA's eyes go wide (an affront to
# perfection) and its claws splay; bracing or recovering, it is fierce again.
# The art is drawn three-quarter front, so a fall forward lays the head
# toward +x and a fall back toward -x.
#
# A reaction pose adds `tilt`, the whole body turned about the pelvis
# (forward positive), to the fight pose's fields; the arms stay in world
# angles. A foot is ("g", x, lift, pitch) planted in the world, as the leg IK
# takes it, or ("b", dx, dy, pitch) carried with the body: an offset from its
# rest ankle in the pelvis frame (a body in the air or on the floor). A
# recoil ENDS on its settled pose: the game holds the last frame for the
# hitstun. Rows in `REACTION_PLANTED` are put on the floor by the target.

_GROUND_Y, _ANKLE_H, _PELVIS_UP = 176.0, 15.295, 67.998
_HIP_X = {"near": -7.417, "far": 7.417}
# Hip-to-ankle at rest in the pelvis frame, and the feet's rest pitch.
_ANKLE_REST = {"near": (-5.62, 52.338), "far": (0.184, 53.076)}
_PITCH_REST = {"near": 50.96, "far": 27.34}


def _rot(x: float, y: float, degrees: float) -> tuple:
    a = math.radians(degrees)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def _foot(side: str, foot: Sequence, tilt: float, root_x: float, root_y: float) -> dict:
    kind, a, b, pitch = foot
    if kind == "g":
        x, lift, world_pitch = a, b, pitch
    else:
        hx, hy = _rot(_HIP_X[side], 0.0, tilt)
        rx, ry = _ANKLE_REST[side]
        ox, oy = _rot(rx + a, ry + b, tilt)
        x = root_x + hx + ox
        lift = -(root_y - _PELVIS_UP + hy + oy) - _ANKLE_H
        world_pitch = _PITCH_REST[side] + tilt + pitch
    return {f"{side}_foot_x": x, f"{side}_foot_lift": lift, f"{side}_foot_pitch": world_pitch}


def _react(
    tilt: float = 0.0,
    torso: float = 0.0,
    head: float = 0.0,
    far: Sequence[float] | None = None,
    near: Sequence[float] | None = None,
    root_x: float = 0.0,
    root_y: float = 0.0,
    feet: Mapping[str, Sequence] | None = None,
    eyes: str = "wide",
    near_hand: str = "open",
    far_hand: str = "open",
) -> dict:
    """One whole-body reaction pose (see the section comment)."""
    lean = tilt + torso
    rest = {side: tuple(lean + sum(_ARM_REST[side][:k + 1]) for k in range(3)) for side in _ARM_REST}
    pose = _pose(torso=torso, far=far or rest["far"], near=near or rest["near"], root_x=root_x, root_y=root_y,
                 head=head, near_hand=near_hand, far_hand=far_hand, eyes=eyes)
    pose.update(_arm("far", lean, *(far or rest["far"])))
    pose.update(_arm("near", lean, *(near or rest["near"])))
    pose["pelvis"] = tilt
    carried = tilt != 0.0
    stance = {"near": ("g", _LEGS["near_foot_x"], 0.0, _LEGS["near_foot_pitch"]),
              "far": ("g", _LEGS["far_foot_x"], 0.0, _LEGS["far_foot_pitch"])}
    for side in ("near", "far"):
        foot = (feet or {}).get(side) or (("b", 0.0, 0.0, 0.0) if carried else stance[side])
        pose.update(_foot(side, foot, tilt, root_x, root_y))
    return pose


_EASE = {
    "smooth": lambda u: u * u * (3.0 - 2.0 * u),
    "out": lambda u: 1.0 - (1.0 - u) ** 3,
    "linear": lambda u: u,
}


def _sample(keys: Sequence[tuple], t: float) -> dict:
    """The pose at `t` between timed keys `(at, pose[, ease into it])`."""
    if t <= keys[0][0]:
        return dict(keys[0][1])
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            u = _EASE[b[2] if len(b) > 2 else "smooth"]((t - a[0]) / max(1e-9, b[0] - a[0]))
            # A part swap cuts at the half way; every other channel blends.
            return {k: (a[1][k] if u < 0.5 else b[1][k]) if "." in k else a[1][k] + (b[1][k] - a[1][k]) * u
                    for k in a[1]}
    return dict(keys[-1][1])


def _reaction_clip(keys: Sequence[tuple], frames: int, duration_ms: int, loop: bool = False) -> dict:
    """A clip with one pose per published frame (loops sample i/n and close
    back on frame 0)."""
    times = [i / frames for i in range(frames)] if loop else [i / max(1, frames - 1) for i in range(frames)]
    poses = [_sample(keys, t) for t in times]
    if loop:
        poses.append(poses[0])
    channels = _pose_channels(poses, ["smooth"] * len(poses))
    if loop:
        # `_pose_channels` keys pose i at i/(len-1); a loop's frame i is at i/n.
        for spec in channels.values():
            for i, key in enumerate(spec.get("keys", [])):
                key[0] = round(i / frames, 4)
    return {"loop": loop, "frames": frames, "duration_ms": duration_ms, "channels": channels}


def _breath(t: float) -> float:
    return math.sin(math.tau * t)


_STAND = _react(eyes="fierce")


def _recoil(peak: dict, settle: dict, *, start: dict = _STAND) -> list:
    """The blow lands on the first frame after rest; the body settles and holds."""
    return [(0.0, start), (0.25, peak, "out"), (0.75, settle), (1.0, settle)]


def _reaction_moves() -> dict:
    """`{row: (keys, frames, duration_ms, loop)}` for every reaction row."""
    air = _react(root_y=-16.0, torso=4.0, eyes="fierce",
                 feet={"near": ("b", 4.0, -14.0, 20.0), "far": ("b", 6.0, -10.0, 20.0)})
    hit_high = _react(torso=-20.0, head=-24.0, root_x=-8.0, root_y=12.0, far=(-120.0, -150.0, -165.0),
                      near=(150.0, 165.0, 175.0), far_hand="claw",
                      feet={"near": ("g", -28.0, 0.0, 50.0), "far": ("g", 16.0, 6.0, 0.0)})
    hit_mid = _react(torso=40.0, head=16.0, root_x=-10.0, root_y=24.0, far=(100.0, 80.0, 70.0),
                     near=(70.0, 170.0, 190.0), feet={"near": ("g", -30.0, 0.0, 60.0), "far": ("g", 16.0, 0.0, 27.0)})
    hit_low = _react(tilt=0.0, torso=26.0, head=-12.0, root_x=-2.0, root_y=14.0, far=(-40.0, -60.0, -70.0),
                     near=(170.0, 185.0, 195.0), far_hand="claw",
                     feet={"near": ("g", -16.0, 0.0, 50.0), "far": ("g", -2.0, 30.0, -40.0)})
    hit_air = _react(tilt=-24.0, torso=34.0, head=12.0, root_y=-12.0, far=(60.0, 150.0, 170.0),
                     near=(70.0, 160.0, 180.0), feet={"near": ("b", 16.0, -28.0, 20.0), "far": ("b", 20.0, -24.0, 20.0)})
    launch_up = _react(tilt=-12.0, torso=-16.0, head=-34.0, root_y=-20.0, far=(70.0, 80.0, 85.0),
                       near=(130.0, 120.0, 115.0), far_hand="claw", near_hand="claw",
                       feet={"near": ("b", -16.0, 2.0, 40.0), "far": ("b", 12.0, -8.0, 40.0)})
    launch_horizontal = _react(tilt=-72.0, torso=36.0, head=6.0, root_y=-8.0, far=(-20.0, -10.0, -5.0),
                               near=(-30.0, -20.0, -10.0), far_hand="claw", near_hand="claw",
                               feet={"near": ("b", 22.0, -12.0, -20.0), "far": ("b", 26.0, -8.0, -20.0)})
    launch_down = _react(tilt=118.0, torso=4.0, head=12.0, root_y=-24.0, far=(-100.0, -95.0, -90.0),
                         near=(-115.0, -110.0, -105.0), far_hand="claw", near_hand="claw",
                         feet={"near": ("b", -6.0, -4.0, 10.0), "far": ("b", 6.0, -10.0, 10.0)})

    def flight(pose: dict) -> list:
        return [(0.0, air), (0.17, pose, "out"), (1.0, pose)]

    def prone_up(t: float) -> dict:
        return _react(tilt=-90.0, torso=2.0 * _breath(t), head=-6.0 + 2.0 * _breath(t), root_y=40.0,
                      far=(-20.0, 60.0, 90.0), near=(180.0, 182.0, 184.0), eyes="open",
                      feet={"near": ("b", 0.0, 0.0, 0.0), "far": ("b", 10.0, -26.0, -20.0)})

    def prone_down(t: float) -> dict:
        # On its belly, too proud to stay down: propped on the near forearm,
        # the chest up and glaring ahead, the far claw reaching on along the floor.
        return _react(tilt=90.0, torso=-24.0 + 1.5 * _breath(t), head=-36.0 + 2.0 * _breath(t), root_y=40.0,
                      far=(8.0, 4.0, 0.0), near=(96.0, 4.0, 0.0), near_hand="palm", far_hand="claw",
                      eyes="fierce", feet={"near": ("b", 0.0, 0.0, 0.0), "far": ("b", -4.0, -2.0, 0.0)})

    def teeter(t: float) -> dict:
        c = math.cos(math.tau * t)
        return _react(torso=22.0 + 5.0 * _breath(t), head=8.0 + 3.0 * _breath(t), root_x=-3.0, root_y=6.0,
                      far=(-100.0 + 70.0 * c, -120.0 + 70.0 * c, -130.0 + 70.0 * c),
                      near=(-100.0 - 70.0 * c, -120.0 - 70.0 * c, -130.0 - 70.0 * c),
                      feet={"near": ("g", -18.0, 0.0, 50.0), "far": ("g", 16.0, 4.0, -10.0)})

    def looped(fn, frames: int) -> list:
        return [(i / frames, fn(i / frames), "linear") for i in range(frames + 1)]

    return {
        "hit_high": (_recoil(hit_high, _react(**{**_HIT_HIGH_SETTLE})), 5, 48, False),
        "hit_mid": (_recoil(hit_mid, _react(**{**_HIT_MID_SETTLE})), 5, 48, False),
        "hit_low": (_recoil(hit_low, _react(**{**_HIT_LOW_SETTLE})), 5, 48, False),
        "hit_air": (_recoil(hit_air, _react(**{**_HIT_AIR_SETTLE}), start=air), 5, 48, False),
        "launch_up": (flight(launch_up), 7, 64, False),
        "launch_horizontal": (flight(launch_horizontal), 7, 64, False),
        "launch_down": (flight(launch_down), 7, 64, False),
        "prone_face_up": (looped(prone_up, 8), 8, 104, True),
        "prone_face_down": (looped(prone_down, 8), 8, 104, True),
        "teeter": (looped(teeter, 8), 8, 92, True),
        # Out of the run: the lead foot planted far ahead on its heel, the hips
        # dropped behind it, the trunk thrown back against the momentum and
        # the arms flung on forward.
        "run_stop": ([
            (0.0, _react(torso=14.0, head=-4.0, root_x=4.0, root_y=6.0, far=(120.0, 100.0, 90.0),
                         near=(-20.0, -60.0, -70.0), eyes="fierce",
                         feet={"near": ("g", -24.0, 8.0, 80.0), "far": ("g", 22.0, 0.0, 27.0)})),
            (0.2, _brake, "out"),
            (0.6, _react(**{**_BRAKE, "torso": -14.0, "root_y": 18.0})),
            (0.85, _react(torso=0.0, head=-6.0, root_y=12.0, eyes="fierce",
                          feet={"near": ("g", -26.0, 0.0, 50.0), "far": ("g", 26.0, 0.0, 27.0)})),
            (1.0, _STAND),
        ], 6, 56, False),
        **_fallback_reactions(air, looped),
    }


def _spun(tilt: float, *angles: float) -> tuple:
    """Arm angles held in the body's frame: world angles turned by `tilt`."""
    return tuple(tilt + a for a in angles)


def _fallback_reactions(air: dict, looped) -> dict:
    """The generic rows the game falls back to, which PCA had seeded from
    unrelated rows: `launch` and `meteor` were one pose (its fall), `prone`
    played the death fall over and over, `tumble` and `getup_roll` were its
    standing roll, `getup` and `tech` the landing crouch, `teeter` and
    `turnaround` its idle."""
    launch = _react(**_LAUNCH)
    meteor = _react(tilt=56.0, torso=30.0, head=16.0, root_y=-20.0, far=(-120.0, -115.0, -110.0),
                    near=(-140.0, -135.0, -130.0), far_hand="claw", near_hand="claw",
                    feet={"near": ("b", -22.0, -8.0, 30.0), "far": ("b", -16.0, -16.0, 30.0)})

    def lying(t: float = 0.0, **over) -> dict:
        """Flat on the back, head toward -x, arms down along the body."""
        fields = dict(tilt=-90.0, torso=1.5 * _breath(t), head=-4.0 + 1.5 * _breath(t), root_y=40.0,
                      far=_spun(-90.0, 80.0, 85.0, 90.0), near=_spun(-90.0, 100.0, 95.0, 90.0), eyes="open")
        fields.update(over)
        return _react(**fields)

    def tumble(t: float) -> dict:
        turn = -360.0 * t
        return _react(tilt=turn, torso=-10.0, head=-16.0, root_y=-30.0, far=_spun(turn, -60.0, -80.0, -90.0),
                      near=_spun(turn, 150.0, 170.0, 180.0), far_hand="claw", near_hand="claw",
                      feet={"near": ("b", -14.0, -6.0, 30.0), "far": ("b", 18.0, -22.0, 10.0)})

    sit = _react(tilt=-40.0, torso=30.0, head=-6.0, root_y=46.0, far=(60.0, 80.0, 90.0), near=(140.0, 100.0, 90.0),
                 near_hand="palm", eyes="fierce",
                 feet={"near": ("g", 30.0, 0.0, 0.0), "far": ("g", 26.0, 0.0, 10.0)})
    kneel = _react(torso=30.0, head=-14.0, root_x=-4.0, root_y=40.0, far=(80.0, 60.0, 40.0),
                   near=(100.0, 80.0, 70.0), eyes="fierce",
                   feet={"near": ("g", -22.0, 0.0, 80.0), "far": ("g", 18.0, 0.0, 27.0)})
    brace = _react(torso=40.0, head=-20.0, root_y=46.0, far=(-150.0, -160.0, -170.0), near=(96.0, 92.0, 90.0),
                   near_hand="palm", far_hand="claw", eyes="fierce",
                   feet={"near": ("g", -30.0, 0.0, 70.0), "far": ("g", 26.0, 0.0, 27.0)})
    return {
        "launch": ([(0.0, air), (0.17, launch, "out"), (1.0, _react(**{**_LAUNCH, "tilt": -46.0}))], 7, 64, False),
        "meteor": ([(0.0, air), (0.17, meteor, "out"), (1.0, meteor)], 7, 64, False),
        "prone": (looped(lying, 8), 8, 104, True),
        "tumble": (looped(tumble, 8), 8, 70, True),
        # Up off the back: sit up on a palm, gather onto a knee, stand.
        "getup": ([(0.0, lying()), (0.3, sit), (0.6, kneel), (0.85, _react(**{**_KNEEL_RISE})), (1.0, _STAND)],
                  8, 70, False),
        # Back over the shoulders, onto the feet, a claw sweep at the floor
        # before rising.
        "getup_roll": ([
            (0.0, lying()),
            (0.33, lying(tilt=-170.0, torso=30.0, root_y=24.0, feet={"near": ("b", 0.0, -30.0, 0.0),
                                                                     "far": ("b", 4.0, -26.0, 0.0)})),
            (0.67, kneel), (1.0, _STAND)], 7, 52, False),
        "getup_attack": ([
            (0.0, lying()), (0.17, sit),
            (0.5, _react(tilt=-30.0, torso=24.0, head=-10.0, root_y=40.0, far=(10.0, 4.0, 0.0),
                         near=(150.0, 110.0, 90.0), near_hand="palm", far_hand="claw", eyes="fierce",
                         feet={"near": ("g", 30.0, 0.0, 0.0), "far": ("g", 64.0, 10.0, -20.0)}), "out"),
            (0.75, kneel), (1.0, _STAND)], 7, 52, False),
        # A floor tech: caught low and wide on a palm slapped to the floor,
        # the far claw thrown back, then braced up into the stance.
        "tech": ([(0.0, _react(**{**_TECH_LAND})), (0.3, brace, "out"), (0.65, kneel), (1.0, _STAND)], 6, 52, False),
        # A pivot onto the new side (the row is drawn in the new facing): it
        # starts wound the old way, arms trailing back, and steps round into
        # the stance.
        "turnaround": ([
            (0.0, _react(torso=-12.0, head=-8.0, root_x=-6.0, root_y=10.0, far=(150.0, 160.0, 165.0),
                         near=(170.0, 175.0, 180.0), eyes="fierce",
                         feet={"near": ("g", -10.0, 0.0, 50.0), "far": ("g", -2.0, 8.0, 60.0)})),
            (0.4, _react(torso=10.0, head=-6.0, root_x=2.0, root_y=16.0, far=(60.0, 40.0, 30.0),
                         near=(110.0, 90.0, 80.0), eyes="fierce",
                         feet={"near": ("g", -20.0, 0.0, 50.0), "far": ("g", 24.0, 6.0, 20.0)})),
            (1.0, _STAND)], 6, 72, False),
    }


_LAUNCH = dict(tilt=-40.0, torso=-12.0, head=-20.0, root_y=-14.0, far=(40.0, 30.0, 20.0), near=(70.0, 60.0, 50.0),
               far_hand="claw", near_hand="claw",
               feet={"near": ("b", 10.0, -6.0, 20.0), "far": ("b", 16.0, -14.0, 20.0)})
_KNEEL_RISE = dict(torso=14.0, head=-8.0, root_y=20.0, far=_GUARD_FAR, near=_GUARD_NEAR, eyes="fierce",
                   feet={"near": ("g", -24.0, 0.0, 60.0), "far": ("g", 18.0, 0.0, 27.0)})
_TECH_LAND = dict(torso=10.0, head=-10.0, root_y=24.0, far=(-60.0, -70.0, -80.0), near=(40.0, 30.0, 20.0),
                  eyes="wide", feet={"near": ("g", -26.0, 4.0, 60.0), "far": ("g", 22.0, 2.0, 27.0)})


_HIT_HIGH_SETTLE = dict(torso=-14.0, head=-16.0, root_x=-6.0, root_y=11.0, far=(-100.0, -130.0, -150.0),
                        near=(140.0, 155.0, 165.0), far_hand="claw",
                        feet={"near": ("g", -28.0, 0.0, 50.0), "far": ("g", 16.0, 4.0, 10.0)})
_HIT_MID_SETTLE = dict(torso=32.0, head=10.0, root_x=-8.0, root_y=20.0, far=(95.0, 70.0, 60.0),
                       near=(75.0, 165.0, 185.0), feet={"near": ("g", -30.0, 0.0, 60.0), "far": ("g", 16.0, 0.0, 27.0)})
_HIT_LOW_SETTLE = dict(torso=20.0, head=-8.0, root_x=-2.0, root_y=12.0, far=(-20.0, -40.0, -50.0),
                       near=(160.0, 175.0, 185.0), far_hand="claw",
                       feet={"near": ("g", -16.0, 0.0, 50.0), "far": ("g", 0.0, 20.0, -30.0)})
_HIT_AIR_SETTLE = dict(tilt=-16.0, torso=22.0, head=4.0, root_y=-12.0, far=(-40.0, -70.0, -80.0),
                       near=(160.0, 175.0, 185.0), far_hand="claw",
                       feet={"near": ("b", 10.0, -20.0, 20.0), "far": ("b", 14.0, -16.0, 20.0)})

_BRAKE = dict(torso=-22.0, head=-12.0, root_x=-8.0, root_y=22.0, far=(-20.0, -10.0, 0.0), near=(-40.0, -30.0, -20.0),
              far_hand="claw", near_hand="claw", eyes="fierce",
              feet={"near": ("g", -34.0, 4.0, 70.0), "far": ("g", 40.0, 0.0, -14.0)})
_brake = _react(**_BRAKE)

#: The grounded reaction rows, which the target puts on the floor: every
#: frame's lowest paint on the ground line. A body lying down has no foot to
#: plant, and a heel or toe turned up lifts the IK-planted foot off it.
REACTION_PLANTED = (
    "hit_high", "hit_mid", "hit_low", "prone_face_up", "prone_face_down", "teeter", "run_stop",
    "prone", "getup", "getup_roll", "getup_attack", "tech", "turnaround",
)


def author_pca_reactions(clips: MutableMapping[str, object]) -> None:
    """Write every reaction row's clip, replacing what was there."""
    for name, (keys, frames, duration_ms, loop) in _reaction_moves().items():
        clips[name] = _reaction_clip(keys, frames, duration_ms, loop)


@profile
def author_pca_combat_clips(data: MutableMapping[str, object]) -> MutableMapping[str, object]:
    """Make the alias-heavy Smash rows genuinely PCA-specific.

    The values intentionally stay in the established rig's channel vocabulary;
    no new bones or art are introduced.  Existing locomotion and already-bespoke
    aerial/special clips are preserved.
    """

    clips = data.get("clips")
    if not isinstance(clips, dict):
        return data

    def have(name: str) -> bool:
        return isinstance(clips.get(name), dict)

    times4 = (0.0, 0.28, 0.58, 1.0)
    times5 = (0.0, 0.22, 0.48, 0.70, 1.0)

    if have("parry"):
        clips["parry"] = _replace_channels(
            clips["parry"],
            {
                "near_arm_u": _keys([-69.34, -28.0, -78.0, -69.34], times4),
                "near_arm_l": _keys([-100.7, -42.0, -112.0, -100.7], times4),
                "far_arm_u": _keys([-55.43, -92.0, -48.0, -55.43], times4),
                "far_arm_l": _keys([-115.03, -46.0, -123.0, -115.03], times4),
                "near_arm_hand": _keys([8.0, -15.0, 12.0, 8.0], times4),
                "far_arm_hand": _keys([8.0, 15.0, -12.0, 8.0], times4),
                "torso": _keys([5.0, -6.0, 7.0, 5.0], times4),
                "root_y": _keys([4.0, 1.0, 5.0, 4.0], times4),
            },
        )

    for name, channels in _fight_moves().items():
        if have(name):
            clips[name] = _replace_channels(clips[name], channels)
    if have("smash_charge"):
        clips["smash_charge"] = _replace_channels(clips["smash_charge"], _smash_charge())

    if have("grab"):
        clips["grab"] = _replace_channels(
            clips["grab"],
            {
                "root_x": _keys([0.0, 1.0, 5.0, 4.0, 0.0], times5),
                "torso": _keys([0.0, -3.0, 9.0, 7.0, 0.0], times5),
                "near_arm_u": _keys([0.0, -18.0, -105.0, -101.0, 0.0], times5),
                "near_arm_l": _keys([0.0, -94.0, 8.0, 5.0, 0.0], times5),
                "far_arm_u": _keys([0.0, -9.0, -93.0, -89.0, 0.0], times5),
                "far_arm_l": _keys([0.0, -101.0, 5.0, 3.0, 0.0], times5),
            },
        )

    # Throws each get a body trajectory rather than merely borrowing an attack.
    if have("throw_forward"):
        clips["throw_forward"] = _replace_channels(
            clips["throw_forward"],
            {
                "root_x": _keys([0.0, -2.0, 1.0, 10.0, 3.0], times5),
                "torso": _keys([4.0, -14.0, -16.0, 24.0, 6.0], times5),
                "near_arm_u": _keys([-52.0, 12.0, 18.0, -112.0, -56.0], times5),
                "near_arm_l": _keys([-88.0, -128.0, -132.0, 8.0, -75.0], times5),
                "far_arm_u": _keys([-36.0, 2.0, 10.0, -100.0, -44.0], times5),
                "far_arm_l": _keys([-98.0, -126.0, -132.0, -4.0, -90.0], times5),
            },
        )
    if have("throw_back"):
        clips["throw_back"] = _replace_channels(
            clips["throw_back"],
            {
                "root_x": _keys([0.0, 3.0, -5.0, -11.0, -2.0], times5),
                "torso": _keys([3.0, 14.0, -20.0, -25.0, 3.0], times5),
                "near_arm_u": _keys([-52.0, -104.0, -22.0, 40.0, -55.0], times5),
                "near_arm_l": _keys([-88.0, 5.0, -118.0, -48.0, -80.0], times5),
                "far_arm_u": _keys([-36.0, -91.0, -11.0, 35.0, -39.0], times5),
                "far_arm_l": _keys([-98.0, 2.0, -121.0, -54.0, -92.0], times5),
            },
        )
    if have("throw_up"):
        clips["throw_up"] = _replace_channels(
            clips["throw_up"],
            {
                "root_y": _keys([0.0, 7.0, 6.0, -7.0, 0.0], times5),
                "torso": _keys([3.0, 14.0, 18.0, -19.0, -2.0], times5),
                "near_arm_u": _keys([-52.0, -14.0, -6.0, -171.0, -88.0], times5),
                "far_arm_u": _keys([-36.0, -9.0, -4.0, -154.0, -72.0], times5),
            },
        )
    if have("throw_down"):
        clips["throw_down"] = _replace_channels(
            clips["throw_down"],
            {
                "root_y": _keys([8.0, 14.0, 17.0, 22.0, 10.0], times5),
                "torso": _keys([8.0, -5.0, -8.0, 24.0, 10.0], times5),
                "near_arm_u": _keys([-52.0, 34.0, 43.0, -83.0, -55.0], times5),
                "far_arm_u": _keys([-38.0, -104.0, -113.0, -23.0, -41.0], times5),
            },
        )

    if have("final_smash"):
        clips["final_smash"] = _replace_channels(
            clips["final_smash"],
            {
                "root_x": _keys([0.0, 0.0, 0.0, 0.0, 0.0], times5),
                "root_y": _keys([0.0, -4.0, -8.0, -11.0, -4.0], times5),
                "torso": _keys([0.0, -14.0, -18.0, 8.0, 0.0], times5),
                "head": _keys([0.0, 5.0, 6.0, -4.0, 0.0], times5),
                "near_arm_u": _keys([0.0, 28.0, 45.0, -151.0, -70.0], times5),
                "near_arm_l": _keys([0.0, -64.0, -48.0, -23.0, -70.0], times5),
                "far_arm_u": _keys([0.0, -116.0, -132.0, -23.0, -54.0], times5),
                "far_arm_l": _keys([0.0, -61.0, -48.0, -110.0, -80.0], times5),
                "near_arm_hand": _keys([0.0, -18.0, -24.0, 12.0, 0.0], times5),
                "far_arm_hand": _keys([0.0, 18.0, 24.0, -12.0, 0.0], times5),
            },
        )

    author_pca_reactions(clips)
    return data


__all__ = ["REACTION_PLANTED", "author_pca_combat_clips", "author_pca_reactions"]
