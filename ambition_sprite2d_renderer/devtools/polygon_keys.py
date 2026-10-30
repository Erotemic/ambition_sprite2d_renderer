"""The polygon fighters' attack rows, keyed in WORLD terms and written as FK clips.

The three polygons (`pointed_polygon`, `pugnacious_polygon`,
`projectile_polygon`) draw their rows from motion libraries whose clips are
per-bone deltas from the SVG rest pose. That is the wrong language to
choreograph in, so each attack is a few [`Key`] poses here, in forward-relative
world degrees (0 is the way the fighter faces, 90 straight down, -90 straight
up), and this module solves them into the clip's deltas, places the boots by
two-bone IK, and writes the clip JSON and the swing spec.

Every attack row has `ATTACK_FRAMES` frames. The game draws a move's row at
the move's own progress: frame `i` of `n` is on screen for phases
`[i/n, (i+1)/n)`, so each frame is posed at the centre of its span (`F`). The
keys of a strike are fitted to the Smash stage's clocks (`SMASH_CLOCKS`):
the smear (the weapon as one wide shape across its arc) and the contact land
inside the move's active window, the anticipation is the frame before it, and
the settle comes after. The hit windows of the specs are derived from the same
clocks, so the hit volume covers where the weapon is at contact.

Run `python -m ambition_sprite2d_renderer.devtools.polygon_keys apply` after a
change; it writes the clips and specs of all three fighters.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..authoring.skeleton import two_bone_ik

Foot = Tuple[float, float, float]  # (forward px from the standing ankle, lift px, pitch deg)
SIDES = ("near", "far")

ATTACK_FRAMES = 12
#: How far above the standing feet an airborne row rides, in px.
AIR_RISE = -6.0

#: The Smash stage's clocks: (first active, last active, total) ticks at 60 Hz.
#: The two humanoids are fast, the beast is heavy.
SMASH_CLOCKS = {
    "fast": {
        "jab": (2, 4, 15), "attack_side": (5, 8, 24), "attack_up": (4, 9, 21),
        "attack_down": (5, 7, 22), "dash_attack": (5, 12, 34), "smash_forward": (13, 16, 42),
        "smash_up": (8, 13, 36), "smash_down": (6, 11, 40), "air_neutral": (3, 22, 38),
        "air_forward": (8, 11, 40), "air_back": (6, 10, 30), "air_up": (4, 8, 28),
        "air_down": (6, 14, 40),
    },
    "heavy": {
        "jab": (5, 7, 20), "attack_side": (9, 12, 36), "attack_up": (8, 13, 32),
        "attack_down": (7, 10, 30), "dash_attack": (9, 16, 44), "smash_forward": (18, 21, 54),
        "smash_up": (12, 17, 48), "smash_down": (8, 14, 50), "air_neutral": (6, 26, 48),
        "air_forward": (14, 17, 54), "air_back": (9, 13, 40), "air_up": (7, 11, 38),
        "air_down": (10, 20, 52),
    },
}

#: Frame duration of each attack row, ms: the home game's old row length over
#: the new frame count. The game draws a move row at the move's own clock.
ROW_MS = {
    "jab": 19, "attack_side": 24, "attack_up": 24, "attack_down": 24, "dash_attack": 51,
    "smash_forward": 55, "smash_up": 40, "smash_down": 41, "air_neutral": 26,
    "air_forward": 26, "air_back": 26, "air_up": 26, "air_down": 26,
}
CHARGE_FRAMES = 8
CHARGE_MS = 82
#: The glint at the weapon's point on each frame of the charge: no two frames
#: in a row spark alike.
CHARGE_GLINT = [1.0, 0.3, 0.7, 0.15, 0.9, 0.45, 0.6, 0.2]


def F(frame: float) -> float:
    """The phase at the centre of `frame` of an `ATTACK_FRAMES` row."""
    return (frame + 0.5) / ATTACK_FRAMES


def active_frames(name: str, clocks: str) -> List[int]:
    """The frames of a row whose centre is inside the move's active window."""
    first, last, total = SMASH_CLOCKS[clocks][name]
    lo, hi = first / total, (last + 1) / total
    return [i for i in range(ATTACK_FRAMES) if lo <= F(i) <= hi]


@dataclass(frozen=True)
class Key:
    """One key pose at `at` (0..1) of the move.

    `near`/`far` are (upper arm, forearm, hand) in forward-relative world
    degrees; `None` holds the arm at rest, carried by the torso. `torso`,
    `head` lean forward when positive. `lunge` is forward px, `drop` down px.
    `feet` places boots (see `Foot`); an unlisted boot stays planted, and in
    the `air` every boot rides with the body. `aim` turns the beast's cannon
    (forward-relative degrees), `None` keeps it with the head. `ease` shapes
    the approach INTO this key: "out" arrives fast (a cut), "in" gathers (a
    wind-up), "smooth" both, "linear" neither.
    """

    at: float
    near: Optional[Tuple[float, float, float]] = None
    far: Optional[Tuple[float, float, float]] = None
    torso: float = 0.0
    head: float = 0.0
    lunge: float = 0.0
    drop: float = 0.0
    feet: Dict[str, Foot] = field(default_factory=dict)
    air: bool = False
    aim: Optional[float] = None
    ease: str = "smooth"


_EASES: Dict[str, Callable[[float], float]] = {
    "linear": lambda u: u,
    "smooth": lambda u: u * u * (3.0 - 2.0 * u),
    "out": lambda u: 1.0 - (1.0 - u) ** 3,
    "in": lambda u: u ** 3,
}


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _lerp_arm(a, b, u):
    if a is None or b is None:
        return a if u < 0.5 else b
    return tuple(_lerp(x, y, u) for x, y in zip(a, b))


def _blend(a: Key, b: Key, u: float) -> Key:
    def feet(side: str) -> Foot:
        fa = a.feet.get(side, (0.0, 0.0, 0.0))
        fb = b.feet.get(side, (0.0, 0.0, 0.0))
        return tuple(_lerp(x, y, u) for x, y in zip(fa, fb))  # type: ignore[return-value]

    aim = None if a.aim is None and b.aim is None else _lerp(
        a.aim if a.aim is not None else b.aim, b.aim if b.aim is not None else a.aim, u)
    return Key(
        at=_lerp(a.at, b.at, u),
        near=_lerp_arm(a.near, b.near, u),
        far=_lerp_arm(a.far, b.far, u),
        torso=_lerp(a.torso, b.torso, u),
        head=_lerp(a.head, b.head, u),
        lunge=_lerp(a.lunge, b.lunge, u),
        drop=_lerp(a.drop, b.drop, u),
        feet={side: feet(side) for side in SIDES},
        air=a.air,
        aim=aim,
    )


def sample(keys: Sequence[Key], phase: float) -> Key:
    """The pose at `phase`, eased into whichever key comes next."""
    if phase <= keys[0].at:
        return keys[0]
    for a, b in zip(keys, keys[1:]):
        if phase <= b.at:
            span = max(1e-6, b.at - a.at)
            return _blend(a, b, _EASES[b.ease]((phase - a.at) / span))
    return keys[-1]


class Body:
    """One polygon's rig, read from its target: rests, standing feet, facing."""

    def __init__(self, target, clocks: str) -> None:
        self.target = target
        self.clocks = clocks
        prepared = target._prepared()
        doc = target._doc()
        self.library = Path(prepared.library.path).parent
        self.unit = 1.0 / float(prepared.binding.render.frame_px_per_rig_unit)
        self.mirror = bool(prepared.reflects_motion_x)
        self.sk = doc.build_skeleton()
        self.rest = {name: b.rest_angle for name, b in self.sk.bones.items()}
        self.parent = {name: b.parent for name, b in self.sk.bones.items()}
        self.facing = -1.0 if doc.authored_faces_left else 1.0
        fr = doc.frame
        self.root = (float(fr["center_x"]), float(fr["ground_y"]))
        stand = self.sk.world({}, root=self.root)
        self.ankle_rest = {s: stand[f"{s}_leg_foot"].origin for s in SIDES}
        self.foot_rest = {s: stand[f"{s}_leg_foot"].angle for s in SIDES}
        self.leg = {s: (self.sk.bones[f"{s}_leg_u"].length, self.sk.bones[f"{s}_leg_l"].length) for s in SIDES}
        self.arm_rest = {
            s: tuple(self.fwd_of(stand[f"{s}_arm_{part}"].angle) for part in ("u", "l", "hand")) for s in SIDES
        }
        self.has_cannon = "cannon" in self.sk.bones

    # Forward-relative degrees <-> world degrees.
    def fwd(self, f: float) -> float:
        return f if self.facing > 0 else 180.0 - f

    def fwd_of(self, world: float) -> float:
        return world if self.facing > 0 else 180.0 - world

    def channels(self, key: Key) -> Dict[str, float]:
        """The clip's deltas (rendered-rig convention) and the root, px."""
        rest, s = self.rest, self.facing
        pelvis = s * 0.35 * key.torso
        torso_w = s * key.torso
        d: Dict[str, float] = {
            "pelvis": pelvis,
            "torso": torso_w - pelvis,
            "head": s * key.head - torso_w,
            "_root_x": s * key.lunge,
            "_root_y": key.drop,
        }
        for side in SIDES:
            arm = key.near if side == "near" else key.far
            if arm is None:
                r = self.arm_rest[side]
                arm = (r[0] + key.torso, r[1] + key.torso, r[2] + key.torso)
            wu, wl, wh = (self.fwd(a) for a in arm)
            d[f"{side}_arm_u"] = wu - torso_w - rest[f"{side}_arm_u"]
            d[f"{side}_arm_l"] = wl - wu - rest[f"{side}_arm_l"]
            d[f"{side}_arm_hand"] = wh - wl - rest[f"{side}_arm_hand"]
        if self.has_cannon:
            head_w = s * key.head
            d["cannon"] = 0.0 if key.aim is None else self.fwd(key.aim) - head_w - rest["cannon"]
        root = (self.root[0] + d["_root_x"], self.root[1] + d["_root_y"])
        angles = {k: v for k, v in d.items() if k in self.sk.bones}
        world = self.sk.world(angles, root=root)
        for side in SIDES:
            dx, lift, pitch = key.feet.get(side, (0.0, 0.0, 0.0))
            ax, ay = self.ankle_rest[side]
            if key.air:
                ax += d["_root_x"]
                ay += d["_root_y"]
            ankle = (ax + s * dx, ay - lift)
            hip = world[f"{side}_leg_u"].origin
            upper, lower = self.leg[side]
            a1, a2 = two_bone_ik(hip, ankle, upper, lower, bend=s)
            d[f"{side}_leg_u"] = a1 - pelvis - rest[f"{side}_leg_u"]
            d[f"{side}_leg_l"] = a2 - a1 - rest[f"{side}_leg_l"]
            d[f"{side}_leg_foot"] = self.foot_rest[side] + s * pitch - a2 - rest[f"{side}_leg_foot"]
        return d

    def state(self, key: Key) -> dict:
        """The clip JSON state of `key`, in the library's authored facing."""
        d = self.channels(key)
        m = -1.0 if self.mirror else 1.0
        bones = {
            name: {"rotation_deg": round(m * _wrap(d[name]), 4)}
            for name in sorted(self.sk.bones) if name in d
        }
        root = [round(m * d["_root_x"] * self.unit, 4), round(d["_root_y"] * self.unit, 4)]
        return {"root": {"position": root}, "bones": bones}

    def rest_key(self, at: float, *, air: bool = False, ease: str = "in", turn: int = 0) -> Key:
        """The standing pose (or the airborne tuck), its arms explicit. `turn`
        adds whole turns to the arm angles, so a swing that went over the top
        comes down the other side to rest instead of back through the front."""
        return Key(at=at, near=self.arm_at_rest("near", 0.0, turn), far=self.arm_at_rest("far", 0.0, turn),
                   air=air, drop=AIR_RISE if air else 0.0,
                   feet={"near": (-3.0, 10.0, 20.0), "far": (3.0, 12.0, 15.0)} if air else {}, ease=ease)

    def arm_at_rest(self, side: str, lean: float, turn: int = 0) -> Tuple[float, float, float]:
        """An arm hanging at rest, carried by a torso leaning `lean`."""
        return tuple(a + lean + 360.0 * turn for a in self.arm_rest[side])  # type: ignore[return-value]

    def resolved(self, key: Key) -> Key:
        """`key` with any arm left `None` made explicit (at rest, carried by
        the torso), so every blend is between numbers."""
        near = key.near if key.near is not None else self.arm_at_rest("near", key.torso)
        far = key.far if key.far is not None else self.arm_at_rest("far", key.torso)
        return replace(key, near=near, far=far)

    # -- writing -------------------------------------------------------------------

    def clip_path(self, name: str) -> Path:
        return self.library / "clips" / f"{name}.clip.json"

    def spec_path(self, name: str) -> Path:
        return self.library / "specs" / f"{name}.spec.json"

    def write_clip(self, name: str, keys: Sequence[Key], frames: int, step_ms: int, loop: bool = False,
                   named: Optional[Dict[int, str]] = None) -> None:
        """Write the clip. `named` maps a frame to a reusable pose id of the
        library: that frame's state is written to the pose file and the clip
        refers to it, so the named whole-body poses stay the clip's."""
        if [k.at for k in keys] != sorted(k.at for k in keys):
            raise ValueError(f"{name}: key phases must be in order")
        keys = [self.resolved(k) for k in keys]
        phases = [i / frames for i in range(frames)] if loop else [F(i) for i in range(frames)]
        path = self.clip_path(name)
        doc = json.loads(path.read_text())
        named = named or {}
        for frame, pose_id in named.items():
            pose_path = self.library / "poses" / f"{pose_id.replace('/', '__')}.pose.json"
            pose = json.loads(pose_path.read_text())
            pose["state"] = self.state(sample(keys, phases[frame]))
            pose["source"] = {"clip": name, "frame": frame, "kind": "authored-polygon-keys"}
            _write_json(pose_path, pose)
        doc["loop"] = loop
        doc["duration_s"] = round(frames * step_ms / 1000.0, 6)
        doc["sampling"] = {"frame_count": frames, "frame_duration_ms": step_ms}
        doc["source"] = {
            "kind": "authored-polygon-keys",
            "clip": name,
            "note": "Keyed in world terms by devtools/polygon_keys.py and solved to FK; edit the keys, not this file.",
        }
        doc["pose_keys"] = [
            {"at_s": round(i * step_ms / 1000.0, 6), "frame": i, "interpolation": "linear",
             **({"pose": named[i]} if i in named else {"state": self.state(sample(keys, ph))})}
            for i, ph in enumerate(phases)
        ]
        _write_json(path, doc)

    def write_spec(self, name: str, spec: dict) -> None:
        _write_json(self.spec_path(name), spec)


def _wrap(deg: float) -> float:
    while deg > 180.0:
        deg -= 360.0
    while deg <= -180.0:
        deg += 360.0
    return deg


def _write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


# ── the strikes ────────────────────────────────────────────────────────────────
#
# Each function returns the keys of one attack. `a0`/`a1` are the first and
# last ACTIVE frames of the Smash stage's clock for that fighter, so the smear
# is on `a0`, the contact on the frame after (or on `a0` when it is the only
# active frame), and the overshoot on the frame after `a1`.

Strike = Callable[[Body, int, int], List[Key]]


def _contact(a0: int, a1: int) -> int:
    return a0 + 1 if a1 > a0 else a0


# -- pointed_polygon: the sword -------------------------------------------------
# The sword points along the near hand: `near[2]` is the blade's direction.

def pp_jab(b: Body, a0: int, a1: int) -> List[Key]:
    c = _contact(a0, a1)
    return [
        b.rest_key(0.0),
        Key(at=F(a0 - 1), near=(140.0, 172.0, 2.0), far=(60.0, 20.0, 10.0), torso=-6.0, head=-3.0,
            lunge=-3.0, drop=2.0, ease="in"),
        Key(at=F(a0), near=(22.0, 6.0, 0.0), far=(130.0, 120.0, 110.0), torso=8.0, head=2.0, lunge=2.0,
            drop=2.5, feet={"near": (6.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(c), near=(4.0, -3.0, -2.0), far=(140.0, 125.0, 115.0), torso=14.0, head=4.0, lunge=6.0,
            drop=3.0, feet={"near": (8.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 1), near=(0.0, -6.0, -5.0), far=(140.0, 125.0, 115.0), torso=16.0, head=5.0, lunge=7.0,
            drop=3.0, feet={"near": (8.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 3), near=(55.0, 60.0, 40.0), far=(110.0, 100.0, 95.0), torso=6.0, head=2.0, lunge=3.0,
            drop=1.5, feet={"near": (4.0, 0.0, 0.0)}),
        b.rest_key(1.0),
    ]


def pp_tilt_forward(b: Body, a0: int, a1: int) -> List[Key]:
    c = _contact(a0, a1)
    return [
        b.rest_key(0.0),
        # Low coil: the blade trailing behind, point down, the body sunk.
        Key(at=F(a0 - 1), near=(135.0, 120.0, 140.0), far=(70.0, 30.0, 20.0), torso=-6.0, head=-2.0,
            lunge=-3.0, drop=3.0, feet={"far": (-2.0, 0.0, 0.0)}, ease="in"),
        # Smear: the blade sweeping up through the front, low.
        Key(at=F(a0), near=(55.0, 40.0, 42.0), far=(120.0, 110.0, 100.0), torso=8.0, head=3.0,
            lunge=3.0, drop=4.0, feet={"near": (6.0, 0.0, 0.0)}, ease="out"),
        # Contact: level, a long step in.
        Key(at=F(c), near=(8.0, -8.0, -10.0), far=(140.0, 125.0, 110.0), torso=15.0, head=5.0,
            lunge=8.0, drop=3.5, feet={"near": (12.0, 0.0, 0.0)}, ease="out"),
        # Overshoot: rising past, up on the step.
        Key(at=F(a1 + 1), near=(-30.0, -55.0, -62.0), far=(150.0, 135.0, 120.0), torso=10.0, head=1.0,
            lunge=9.0, drop=3.0, feet={"near": (12.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 3), near=(-60.0, -80.0, -90.0), far=(110.0, 100.0, 95.0), torso=4.0, head=0.0,
            lunge=6.0, drop=2.0, feet={"near": (8.0, 0.0, 0.0)}),
        b.rest_key(1.0),
    ]


def pp_tilt_up(b: Body, a0: int, a1: int) -> List[Key]:
    c = _contact(a0, a1)
    return [
        b.rest_key(0.0),
        # Crouch with the blade low in front: the arc has somewhere to come from.
        Key(at=F(a0 - 1), near=(60.0, 45.0, 35.0), far=(110.0, 100.0, 95.0), torso=10.0, head=5.0,
            drop=6.0, ease="in"),
        Key(at=F(a0), near=(-25.0, -45.0, -48.0), far=(120.0, 115.0, 105.0), torso=0.0, head=-10.0,
            drop=1.0, ease="out"),
        # The vertical, up on the toes, the head back after the blade.
        Key(at=F(c), near=(-88.0, -95.0, -92.0), far=(130.0, 130.0, 120.0), torso=-8.0, head=-22.0,
            drop=-2.0, feet={"near": (0.0, 2.0, 15.0), "far": (0.0, 2.0, 15.0)}, ease="out"),
        Key(at=F(a1 + 1), near=(-145.0, -162.0, -168.0), far=(120.0, 125.0, 115.0), torso=-12.0, head=-26.0,
            drop=0.0, ease="out"),
        Key(at=F(a1 + 3), near=(-200.0, -205.0, -210.0), far=(100.0, 95.0, 90.0), torso=-5.0, head=-10.0,
            drop=1.0),
        b.rest_key(1.0, turn=-1),
    ]


def pp_tilt_down(b: Body, a0: int, a1: int) -> List[Key]:
    c = _contact(a0, a1)
    low = {"near": (-4.0, 0.0, 0.0), "far": (6.0, 0.0, 0.0)}
    out = {"near": (-4.0, 0.0, 0.0), "far": (10.0, 0.0, 0.0)}
    poke = 24.0
    crouch = Key(at=0.0, torso=10.0, head=4.0, drop=14.0, feet=low, ease="in")
    return [
        crouch,
        Key(at=F(a0 - 1), near=(140.0, 175.0, poke), far=(60.0, 20.0, 10.0), torso=12.0, head=0.0,
            lunge=-2.0, drop=14.0, feet=low, ease="in"),
        Key(at=F(a0), near=(poke + 30.0, poke + 8.0, poke), far=(120.0, 110.0, 100.0), torso=18.0, head=3.0,
            lunge=3.0, drop=14.0, feet=out, ease="out"),
        Key(at=F(c), near=(poke + 6.0, poke, poke), far=(130.0, 115.0, 105.0), torso=24.0, head=5.0,
            lunge=7.0, drop=14.0, feet=out, ease="out"),
        Key(at=F(a1 + 1), near=(poke + 8.0, poke + 2.0, poke + 1.0), far=(130.0, 115.0, 105.0), torso=25.0,
            head=5.0, lunge=8.0, drop=14.0, feet=out, ease="out"),
        Key(at=F(a1 + 3), near=(90.0, 100.0, 60.0), far=(100.0, 90.0, 85.0), torso=14.0, head=2.0,
            lunge=3.0, drop=14.0, feet=low),
        replace(crouch, at=F(a1 + 5)),
        b.rest_key(1.0),
    ]


def pp_dash_attack(b: Body, a0: int, a1: int) -> List[Key]:
    c = _contact(a0, a1)
    run = {"near": (-8.0, 4.0, 25.0), "far": (10.0, 0.0, -5.0)}
    return [
        Key(at=0.0, near=(150.0, 160.0, -150.0), far=(50.0, 30.0, 20.0), torso=14.0, head=-4.0,
            drop=4.0, feet={"near": (-4.0, 2.0, 18.0), "far": (4.0, 0.0, 0.0)}),
        Key(at=F(a0 - 1), near=(160.0, 175.0, -140.0), far=(60.0, 40.0, 30.0), torso=16.0, head=-6.0,
            lunge=-1.0, drop=5.0, feet={"near": (-4.0, 2.0, 18.0), "far": (4.0, 0.0, 0.0)}, ease="in"),
        # Smear: launched, the blade coming over the top.
        Key(at=F(a0), near=(-50.0, -70.0, -60.0), far=(140.0, 130.0, 120.0), torso=22.0, head=-6.0,
            lunge=8.0, drop=5.0, feet=run, ease="out"),
        # Contact: level, the body nearly horizontal behind the blade.
        Key(at=F(c), near=(10.0, -4.0, -2.0), far=(150.0, 140.0, 130.0), torso=28.0, head=-8.0,
            lunge=13.0, drop=5.5, feet=run, ease="out"),
        Key(at=F(a1 + 1), near=(35.0, 20.0, 25.0), far=(150.0, 140.0, 130.0), torso=30.0, head=-6.0,
            lunge=16.0, drop=6.0, feet=run, ease="out"),
        Key(at=F(a1 + 3), near=(60.0, 50.0, 45.0), far=(130.0, 120.0, 110.0), torso=20.0, head=-3.0,
            lunge=16.0, drop=4.0, feet=run),
        Key(at=F(a1 + 5), near=(85.0, 90.0, 70.0), far=(105.0, 95.0, 90.0), torso=8.0, head=0.0,
            lunge=8.0, drop=2.0, feet={"far": (4.0, 0.0, 0.0)}),
        b.rest_key(1.0),
    ]


def pp_smash_forward(b: Body, a0: int, a1: int) -> List[Key]:
    c = _contact(a0, a1)
    step = {"near": (12.0, 0.0, 0.0), "far": (-4.0, 0.0, 0.0)}
    return [
        b.rest_key(0.0),
        Key(at=F(1), near=(-120.0, -150.0, -130.0), far=(-100.0, -150.0, -130.0), torso=-8.0, head=-5.0,
            lunge=-3.0, drop=3.0),
        # Full coil, held: the blade overhead and past vertical behind, both hands.
        Key(at=F(a0 - 1), near=(-110.0, -140.0, -150.0), far=(-95.0, -140.0, -150.0), torso=-14.0, head=-6.0,
            lunge=-4.0, drop=4.5, feet={"far": (-2.0, 1.0, 10.0)}, ease="in"),
        # Smear: over the top and coming down in front, a big step.
        Key(at=F(a0), near=(-35.0, -50.0, -40.0), far=(-30.0, -60.0, -50.0), torso=10.0, head=3.0,
            lunge=5.0, drop=5.0, feet=step, ease="out"),
        # Cleave: the blade down on the target, the body behind it.
        Key(at=F(c), near=(20.0, 12.0, 18.0), far=(30.0, 10.0, 15.0), torso=22.0, head=8.0,
            lunge=10.0, drop=6.0, feet=step, ease="out"),
        Key(at=F(a1 + 1), near=(60.0, 55.0, 60.0), far=(65.0, 55.0, 58.0), torso=30.0, head=12.0,
            lunge=12.0, drop=9.0, feet=step, ease="out"),
        # Heavy recovery: stays low, the blade dragging.
        Key(at=F(a1 + 3), near=(70.0, 65.0, 55.0), far=(90.0, 80.0, 75.0), torso=18.0, head=6.0,
            lunge=9.0, drop=6.0, feet=step),
        Key(at=F(a1 + 5), near=(85.0, 85.0, 75.0), far=(100.0, 92.0, 85.0), torso=6.0, head=2.0,
            lunge=3.0, drop=2.0, feet={"near": (4.0, 0.0, 0.0)}),
        b.rest_key(1.0),
    ]


def pp_smash_up(b: Body, a0: int, a1: int) -> List[Key]:
    c = _contact(a0, a1)
    spring = {"near": (-1.0, 7.0, 30.0), "far": (1.0, 8.0, 30.0)}
    return [
        b.rest_key(0.0),
        # Deep squat, the blade low and back, both hands.
        Key(at=F(a0 - 1), near=(120.0, 150.0, 165.0), far=(100.0, 150.0, 165.0), torso=14.0, head=6.0,
            lunge=-1.0, drop=10.0, ease="in"),
        # The spring: the blade sweeping up the front.
        Key(at=F(a0), near=(-15.0, -35.0, -30.0), far=(-5.0, -30.0, -30.0), torso=4.0, head=-12.0,
            lunge=1.0, drop=-3.0, feet={"near": (-1.0, 4.0, 25.0), "far": (1.0, 5.0, 25.0)}, ease="out"),
        Key(at=F(c), near=(-80.0, -95.0, -88.0), far=(-70.0, -90.0, -88.0), torso=-6.0, head=-26.0,
            lunge=1.0, drop=-8.0, feet=spring, ease="out"),
        Key(at=F(a1 + 1), near=(-115.0, -135.0, -140.0), far=(-105.0, -130.0, -140.0), torso=-10.0, head=-30.0,
            lunge=1.0, drop=-9.0, feet=spring, ease="out"),
        # Landing back into a crouch.
        Key(at=F(a1 + 3), near=(-150.0, -175.0, -185.0), far=(-260.0, -270.0, -275.0), torso=6.0, head=-10.0,
            drop=5.0, ease="in"),
        Key(at=F(a1 + 5), near=(-245.0, -255.0, -265.0), far=(-262.0, -268.0, -275.0), torso=2.0, drop=1.0),
        b.rest_key(1.0, turn=-1),
    ]


def pp_smash_down(b: Body, a0: int, a1: int) -> List[Key]:
    # A low spin at the feet: the blade sweeps under the body, front then
    # back, one hit each side of the window. It never points straight down
    # on a frame, and the crouch keeps the point above the floor.
    c = _contact(a0, a1)
    wide = {"near": (-7.0, 0.0, 0.0), "far": (7.0, 0.0, 0.0)}
    return [
        b.rest_key(0.0),
        # Sink wide, the blade gathered high in front.
        Key(at=F(a0 - 1), near=(-20.0, -50.0, -35.0), far=(110.0, 100.0, 90.0), torso=4.0, head=2.0,
            drop=9.0, feet=wide, ease="in"),
        Key(at=F(a0), near=(62.0, 48.0, 55.0), far=(130.0, 125.0, 115.0), torso=20.0, head=-4.0,
            lunge=2.0, drop=11.0, feet=wide, ease="out"),
        Key(at=F(c), near=(118.0, 132.0, 125.0), far=(60.0, 40.0, 30.0), torso=-6.0, head=-4.0,
            lunge=-2.0, drop=11.0, feet=wide, ease="linear"),
        Key(at=F(a1 + 1), near=(138.0, 150.0, 148.0), far=(50.0, 30.0, 25.0), torso=-10.0, head=-4.0,
            lunge=-3.0, drop=11.0, feet=wide, ease="out"),
        Key(at=F(a1 + 3), near=(130.0, 125.0, 120.0), far=(70.0, 60.0, 55.0), torso=0.0, head=-2.0,
            drop=7.0, feet={"near": (-3.0, 0.0, 0.0), "far": (3.0, 0.0, 0.0)}),
        b.rest_key(1.0),
    ]


def _air(keys: List[Key]) -> List[Key]:
    tuck = {"near": (-3.0, 10.0, 20.0), "far": (3.0, 12.0, 15.0)}
    return [replace(k, air=True, drop=k.drop + AIR_RISE, feet={**tuck, **k.feet}) for k in keys]


def pp_air_neutral(b: Body, a0: int, a1: int) -> List[Key]:
    # A full-circle spin of the blade over the active window.
    ring = [((25.0, 5.0, 0.0), 8.0), ((-70.0, -88.0, -90.0), -4.0), ((-160.0, -175.0, -180.0), -8.0),
            ((100.0, 95.0, 90.0), 4.0), ((30.0, 10.0, 0.0), 8.0)]
    keys = [b.rest_key(0.0), Key(at=F(max(0, a0 - 1)), near=(60.0, 40.0, 30.0), far=(120.0, 110.0, 100.0),
                                 torso=6.0, head=3.0, ease="in")]
    span = max(1, a1 - a0)
    for i, (near, lean) in enumerate(ring):
        at = F(a0 + span * i / (len(ring) - 1))
        keys.append(Key(at=at, near=near, far=(140.0 - 30.0 * (i % 2), 125.0, 115.0), torso=lean, head=lean * 0.4,
                        feet={"near": (-4.0, 9.0, 30.0), "far": (3.0, 11.0, 25.0)}, ease="linear" if i else "out"))
    keys.append(Key(at=F(a1 + 2), near=(70.0, 70.0, 40.0), far=(110.0, 105.0, 100.0), torso=4.0))
    keys.append(b.rest_key(1.0))
    return _air(keys)


def pp_air_forward(b: Body, a0: int, a1: int) -> List[Key]:
    c = _contact(a0, a1)
    return _air([
        b.rest_key(0.0),
        Key(at=F(a0 - 2), near=(-135.0, -155.0, -130.0), far=(60.0, 20.0, 10.0), torso=-8.0, head=-4.0,
            lunge=-2.0, feet={"near": (-6.0, 6.0, 30.0)}, ease="in"),
        Key(at=F(a0 - 1), near=(-105.0, -125.0, -100.0), far=(70.0, 30.0, 20.0), torso=-4.0, head=-2.0,
            lunge=-1.0, feet={"near": (-6.0, 6.0, 30.0)}, ease="in"),
        Key(at=F(a0), near=(5.0, -10.0, -5.0), far=(140.0, 125.0, 115.0), torso=16.0, head=6.0, lunge=4.0,
            feet={"near": (-8.0, 5.0, 35.0), "far": (5.0, 10.0, 10.0)}, ease="out"),
        Key(at=F(c), near=(25.0, 10.0, 15.0), far=(145.0, 130.0, 120.0), torso=20.0, head=7.0, lunge=4.0,
            feet={"near": (-8.0, 5.0, 35.0), "far": (5.0, 10.0, 10.0)}, ease="out"),
        Key(at=F(a1 + 1), near=(55.0, 40.0, 40.0), far=(145.0, 130.0, 120.0), torso=22.0, head=7.0, lunge=4.0,
            feet={"near": (-8.0, 5.0, 35.0), "far": (5.0, 10.0, 10.0)}, ease="out"),
        Key(at=F(a1 + 3), near=(80.0, 80.0, 60.0), far=(110.0, 105.0, 100.0), torso=8.0, head=3.0, lunge=2.0),
        b.rest_key(1.0),
    ])


def pp_air_back(b: Body, a0: int, a1: int) -> List[Key]:
    c = _contact(a0, a1)
    return _air([
        b.rest_key(0.0),
        # Gathered: the blade across the chest in front.
        Key(at=F(a0 - 1), near=(40.0, -30.0, -20.0), far=(110.0, 110.0, 100.0), torso=10.0, head=4.0,
            feet={"far": (6.0, 10.0, 0.0)}, ease="in"),
        # Smear: over the head on its way back.
        Key(at=F(a0), near=(-110.0, -130.0, -120.0), far=(80.0, 50.0, 40.0), torso=-6.0, head=-8.0,
            lunge=-1.0, feet={"near": (-6.0, 4.0, 30.0), "far": (6.0, 12.0, 0.0)}, ease="out"),
        # Contact: level behind, the body arched back into it.
        Key(at=F(c), near=(-178.0, -180.0, -180.0), far=(60.0, 30.0, 20.0), torso=-18.0, head=-14.0,
            lunge=-3.0, feet={"near": (-6.0, 4.0, 30.0), "far": (6.0, 12.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 1), near=(-200.0, -212.0, -218.0), far=(50.0, 20.0, 10.0), torso=-16.0, head=-12.0,
            lunge=-3.0, feet={"near": (-6.0, 4.0, 30.0), "far": (6.0, 12.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 3), near=(-215.0, -230.0, -240.0), far=(90.0, 80.0, 75.0), torso=-6.0, head=-4.0),
        b.rest_key(1.0, turn=-1),
    ])


def pp_air_up(b: Body, a0: int, a1: int) -> List[Key]:
    c = _contact(a0, a1)
    return _air([
        b.rest_key(0.0),
        Key(at=F(a0 - 1), near=(40.0, 20.0, 10.0), far=(110.0, 110.0, 100.0), torso=8.0, head=4.0,
            feet={"near": (-3.0, 9.0, 20.0), "far": (3.0, 11.0, 15.0)}, ease="in"),
        Key(at=F(a0), near=(-40.0, -55.0, -45.0), far=(120.0, 120.0, 110.0), torso=-2.0, head=-14.0,
            drop=-1.0, feet={"near": (-2.0, 5.0, 30.0), "far": (2.0, 6.0, 30.0)}, ease="out"),
        Key(at=F(c), near=(-85.0, -95.0, -90.0), far=(130.0, 135.0, 125.0), torso=-6.0, head=-26.0,
            drop=-2.0, feet={"near": (-2.0, 3.0, 35.0), "far": (2.0, 4.0, 35.0)}, ease="out"),
        Key(at=F(a1 + 1), near=(-150.0, -165.0, -165.0), far=(120.0, 125.0, 115.0), torso=-10.0, head=-30.0,
            drop=-2.0, feet={"near": (-2.0, 3.0, 35.0), "far": (2.0, 4.0, 35.0)}, ease="out"),
        Key(at=F(a1 + 3), near=(-195.0, -205.0, -215.0), far=(100.0, 95.0, 90.0), torso=-4.0, head=-10.0),
        b.rest_key(1.0, turn=-1),
    ])


def pp_air_down(b: Body, a0: int, a1: int) -> List[Key]:
    c = _contact(a0, a1)
    curl = {"near": (-8.0, 14.0, 40.0), "far": (-3.0, 16.0, 35.0)}
    return _air([
        b.rest_key(0.0),
        # Raised overhead first, so the stab has a direction.
        Key(at=F(a0 - 1), near=(-110.0, -120.0, -95.0), far=(70.0, 40.0, 30.0), torso=-6.0, head=-6.0,
            feet={"near": (-2.0, 3.0, 20.0), "far": (2.0, 4.0, 15.0)}, ease="in"),
        Key(at=F(a0), near=(20.0, 30.0, 25.0), far=(130.0, 125.0, 115.0), torso=10.0, head=6.0, drop=-1.0,
            feet={"near": (-5.0, 8.0, 30.0), "far": (0.0, 10.0, 25.0)}, ease="out"),
        Key(at=F(c), near=(92.0, 88.0, 90.0), far=(150.0, 145.0, 135.0), torso=16.0, head=10.0, drop=-2.0,
            feet=curl, ease="out"),
        Key(at=F(a1), near=(90.0, 88.0, 90.0), far=(150.0, 145.0, 135.0), torso=16.0, head=10.0, drop=-2.0,
            feet=curl),
        Key(at=F(a1 + 1), near=(90.0, 88.0, 90.0), far=(150.0, 145.0, 135.0), torso=14.0, head=8.0, drop=-2.0,
            feet=curl),
        Key(at=F(a1 + 3), near=(100.0, 95.0, 90.0), far=(100.0, 95.0, 90.0), torso=6.0, head=3.0),
        b.rest_key(1.0),
    ])


def pp_smash_charge(b: Body) -> List[Key]:
    """The held forward smash: the full coil, trembling, the point sparking."""
    keys = []
    for i in range(CHARGE_FRAMES):
        u = i / CHARGE_FRAMES
        w = math.sin(u * 2.0 * math.pi)
        shake = 0.5 if i % 2 == 0 else -0.5
        keys.append(Key(at=u, near=(-110.0 + 3.0 * w, -140.0, -150.0 + 4.0 * w), far=(-95.0 + 2.0 * w, -140.0, -150.0),
                        torso=-14.0 + 1.5 * w, head=-6.0, lunge=-4.0 + 0.8 * w + shake, drop=4.5 + w + 0.5 * shake,
                        feet={"far": (-2.0, 1.0, 10.0)}, ease="linear"))
    return keys


POINTED: Dict[str, Strike] = {
    "jab": pp_jab, "attack_side": pp_tilt_forward, "attack_up": pp_tilt_up, "attack_down": pp_tilt_down,
    "dash_attack": pp_dash_attack, "smash_forward": pp_smash_forward, "smash_up": pp_smash_up,
    "smash_down": pp_smash_down, "air_neutral": pp_air_neutral, "air_forward": pp_air_forward,
    "air_back": pp_air_back, "air_up": pp_air_up, "air_down": pp_air_down,
}


# -- pugnacious_polygon: the fists and boots ---------------------------------------
# The hand bone is the fist: `near[2]` is where the knuckles point.

def pg_jab(b: Body, a0: int, a1: int) -> List[Key]:
    c = _contact(a0, a1)
    guard = (80.0, 10.0, -10.0)
    return [
        b.rest_key(0.0),
        Key(at=F(a0 - 1), near=(125.0, 175.0, 185.0), far=guard, torso=-5.0, head=-2.0, lunge=-2.0,
            drop=1.5, ease="in"),
        Key(at=F(a0), near=(15.0, 4.0, 0.0), far=guard, torso=8.0, head=2.0, lunge=3.0, drop=2.0,
            feet={"near": (6.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(c), near=(2.0, -2.0, 0.0), far=guard, torso=14.0, head=4.0, lunge=6.0, drop=2.5,
            feet={"near": (8.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 1), near=(-2.0, -5.0, -3.0), far=guard, torso=16.0, head=5.0, lunge=7.0, drop=2.5,
            feet={"near": (8.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 3), near=(70.0, 150.0, 175.0), far=guard, torso=6.0, head=2.0, lunge=3.0, drop=1.0,
            feet={"near": (4.0, 0.0, 0.0)}),
        b.rest_key(1.0),
    ]


def pg_tilt_forward(b: Body, a0: int, a1: int) -> List[Key]:
    # A hook: wound back at shoulder height, swung level through the front.
    c = _contact(a0, a1)
    return [
        b.rest_key(0.0),
        Key(at=F(a0 - 1), near=(160.0, 195.0, 200.0), far=(70.0, 10.0, -10.0), torso=-10.0, head=-4.0,
            lunge=-3.0, drop=3.0, feet={"far": (-2.0, 0.0, 0.0)}, ease="in"),
        Key(at=F(a0), near=(45.0, 15.0, 5.0), far=(110.0, 80.0, 70.0), torso=8.0, head=2.0, lunge=4.0,
            drop=3.0, feet={"near": (6.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(c), near=(0.0, 0.0, 0.0), far=(130.0, 110.0, 100.0), torso=18.0, head=5.0, lunge=9.0,
            drop=3.5, feet={"near": (12.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 1), near=(-6.0, -10.0, -12.0), far=(135.0, 120.0, 110.0), torso=20.0, head=5.0, lunge=10.0,
            drop=3.5, feet={"near": (12.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 3), near=(60.0, 90.0, 100.0), far=(115.0, 105.0, 95.0), torso=6.0, head=2.0, lunge=5.0,
            drop=2.0, feet={"near": (8.0, 0.0, 0.0)}),
        b.rest_key(1.0),
    ]


def pg_tilt_up(b: Body, a0: int, a1: int) -> List[Key]:
    # An uppercut: the fist from the hip to straight up.
    c = _contact(a0, a1)
    return [
        b.rest_key(0.0),
        Key(at=F(a0 - 1), near=(120.0, 165.0, 185.0), far=(70.0, 0.0, -20.0), torso=8.0, head=4.0,
            drop=7.0, ease="in"),
        Key(at=F(a0), near=(30.0, -30.0, -45.0), far=(110.0, 90.0, 80.0), torso=2.0, head=-6.0, lunge=2.0,
            drop=2.0, ease="out"),
        Key(at=F(c), near=(-85.0, -92.0, -95.0), far=(130.0, 125.0, 115.0), torso=-6.0, head=-18.0, lunge=2.0,
            drop=-3.0, feet={"near": (0.0, 3.0, 15.0), "far": (0.0, 2.0, 15.0)}, ease="out"),
        Key(at=F(a1 + 1), near=(-110.0, -130.0, -140.0), far=(130.0, 125.0, 115.0), torso=-10.0, head=-22.0,
            lunge=2.0, drop=-2.0, feet={"near": (0.0, 2.0, 10.0)}, ease="out"),
        Key(at=F(a1 + 3), near=(-60.0, -40.0, -30.0), far=(110.0, 100.0, 95.0), torso=-2.0, head=-8.0,
            drop=1.0),
        b.rest_key(1.0),
    ]


def pg_tilt_down(b: Body, a0: int, a1: int) -> List[Key]:
    # A low sweep kick from a crouch, the near boot.
    c = _contact(a0, a1)
    crouch = Key(at=0.0, near=(60.0, 140.0, 170.0), far=(100.0, 150.0, 175.0), torso=14.0, head=4.0, drop=14.0,
                 feet={"near": (-6.0, 0.0, 0.0), "far": (6.0, 0.0, 0.0)}, ease="in")
    return [
        crouch,
        Key(at=F(a0 - 1), near=(60.0, 140.0, 170.0), far=(100.0, 150.0, 175.0), torso=18.0, head=4.0, drop=15.0,
            feet={"near": (-14.0, 2.0, -20.0), "far": (6.0, 0.0, 0.0)}, ease="in"),
        Key(at=F(a0), near=(40.0, 110.0, 140.0), far=(110.0, 160.0, 180.0), torso=10.0, head=2.0, drop=14.0,
            feet={"near": (14.0, 5.0, -10.0), "far": (6.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(c), near=(30.0, 100.0, 130.0), far=(110.0, 160.0, 180.0), torso=4.0, head=0.0, drop=14.0,
            feet={"near": (30.0, 4.0, 0.0), "far": (6.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 1), near=(30.0, 100.0, 130.0), far=(110.0, 160.0, 180.0), torso=0.0, head=-2.0, drop=14.0,
            feet={"near": (34.0, 8.0, 10.0), "far": (6.0, 0.0, 0.0)}, ease="out"),
        replace(crouch, at=F(a1 + 4)),
        b.rest_key(1.0),
    ]


def pg_dash_attack(b: Body, a0: int, a1: int) -> List[Key]:
    # A running lariat: the arm swung from behind, the body thrown forward.
    c = _contact(a0, a1)
    run = {"near": (-8.0, 4.0, 25.0), "far": (10.0, 0.0, -5.0)}
    return [
        Key(at=0.0, near=(170.0, 150.0, 140.0), far=(40.0, 20.0, 10.0), torso=14.0, head=-4.0, drop=4.0,
            feet={"near": (-4.0, 2.0, 18.0), "far": (4.0, 0.0, 0.0)}),
        Key(at=F(a0 - 1), near=(185.0, 170.0, 160.0), far=(50.0, 30.0, 20.0), torso=16.0, head=-6.0,
            lunge=-1.0, drop=5.0, feet={"near": (-4.0, 2.0, 18.0), "far": (4.0, 0.0, 0.0)}, ease="in"),
        Key(at=F(a0), near=(60.0, 30.0, 20.0), far=(140.0, 130.0, 120.0), torso=24.0, head=-6.0,
            lunge=8.0, drop=5.0, feet=run, ease="out"),
        Key(at=F(c), near=(0.0, -5.0, -5.0), far=(150.0, 140.0, 130.0), torso=28.0, head=-8.0,
            lunge=13.0, drop=5.5, feet=run, ease="out"),
        Key(at=F(a1 + 1), near=(-20.0, -25.0, -30.0), far=(150.0, 140.0, 130.0), torso=30.0, head=-6.0,
            lunge=16.0, drop=6.0, feet=run, ease="out"),
        Key(at=F(a1 + 3), near=(20.0, 20.0, 15.0), far=(130.0, 120.0, 110.0), torso=20.0, head=-3.0,
            lunge=16.0, drop=4.0, feet=run),
        Key(at=F(a1 + 5), near=(80.0, 110.0, 130.0), far=(105.0, 120.0, 140.0), torso=8.0, head=0.0,
            lunge=8.0, drop=2.0, feet={"far": (4.0, 0.0, 0.0)}),
        b.rest_key(1.0),
    ]


def pg_smash_forward(b: Body, a0: int, a1: int) -> List[Key]:
    # The full-commitment straight right.
    c = _contact(a0, a1)
    step = {"near": (14.0, 0.0, 0.0), "far": (-4.0, 0.0, 0.0)}
    return [
        b.rest_key(0.0),
        Key(at=F(1), near=(140.0, 190.0, 200.0), far=(70.0, 10.0, -10.0), torso=-8.0, head=-4.0, lunge=-3.0,
            drop=3.0),
        # Cocked: the fist drawn far back, the chest turned away, weight back.
        Key(at=F(a0 - 1), near=(165.0, 200.0, 210.0), far=(60.0, -10.0, -30.0), torso=-14.0, head=-6.0,
            lunge=-5.0, drop=4.5, feet={"far": (-3.0, 1.0, 10.0)}, ease="in"),
        Key(at=F(a0), near=(12.0, 4.0, 0.0), far=(130.0, 120.0, 110.0), torso=14.0, head=4.0, lunge=8.0,
            drop=4.0, feet=step, ease="out"),
        Key(at=F(c), near=(0.0, -2.0, 0.0), far=(140.0, 130.0, 120.0), torso=22.0, head=7.0, lunge=13.0,
            drop=4.5, feet=step, ease="out"),
        Key(at=F(a1 + 1), near=(-4.0, -6.0, -4.0), far=(145.0, 135.0, 125.0), torso=26.0, head=8.0, lunge=15.0,
            drop=5.0, feet=step, ease="out"),
        Key(at=F(a1 + 3), near=(30.0, 40.0, 40.0), far=(120.0, 115.0, 105.0), torso=16.0, head=5.0, lunge=11.0,
            drop=4.0, feet=step),
        Key(at=F(a1 + 5), near=(80.0, 120.0, 150.0), far=(105.0, 130.0, 150.0), torso=5.0, head=2.0, lunge=3.0,
            drop=1.5, feet={"near": (4.0, 0.0, 0.0)}),
        b.rest_key(1.0),
    ]


def pg_smash_up(b: Body, a0: int, a1: int) -> List[Key]:
    # A leaping uppercut.
    c = _contact(a0, a1)
    spring = {"near": (-1.0, 8.0, 30.0), "far": (1.0, 10.0, 30.0)}
    return [
        b.rest_key(0.0),
        Key(at=F(a0 - 1), near=(130.0, 175.0, 195.0), far=(80.0, 20.0, 0.0), torso=14.0, head=6.0, lunge=-1.0,
            drop=11.0, ease="in"),
        Key(at=F(a0), near=(20.0, -40.0, -55.0), far=(120.0, 110.0, 100.0), torso=4.0, head=-12.0, lunge=1.0,
            drop=-3.0, feet={"near": (-1.0, 4.0, 25.0), "far": (1.0, 5.0, 25.0)}, ease="out"),
        Key(at=F(c), near=(-85.0, -92.0, -95.0), far=(140.0, 140.0, 130.0), torso=-6.0, head=-24.0, lunge=1.0,
            drop=-9.0, feet=spring, ease="out"),
        Key(at=F(a1 + 1), near=(-105.0, -115.0, -120.0), far=(140.0, 140.0, 130.0), torso=-10.0, head=-28.0,
            lunge=1.0, drop=-10.0, feet=spring, ease="out"),
        Key(at=F(a1 + 3), near=(-80.0, -60.0, -50.0), far=(110.0, 100.0, 90.0), torso=6.0, head=-8.0, drop=5.0,
            ease="in"),
        Key(at=F(a1 + 5), near=(90.0, 130.0, 160.0), far=(100.0, 140.0, 165.0), torso=2.0, drop=1.0),
        b.rest_key(1.0),
    ]


def pg_smash_down(b: Body, a0: int, a1: int) -> List[Key]:
    # The near boot: a low kick in front, then the same boot whipped behind.
    c = _contact(a0, a1)
    arms = (90.0, 140.0, 170.0)
    return [
        b.rest_key(0.0),
        Key(at=F(a0 - 1), near=(50.0, 120.0, 150.0), far=(120.0, 160.0, 180.0), torso=12.0, head=4.0, drop=10.0,
            feet={"near": (-12.0, 3.0, -15.0), "far": (6.0, 0.0, 0.0)}, ease="in"),
        Key(at=F(a0), near=(40.0, 100.0, 130.0), far=arms, torso=-8.0, head=-2.0, drop=8.0,
            feet={"near": (40.0, 18.0, 10.0), "far": (6.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(c), near=(80.0, 150.0, 180.0), far=(110.0, 40.0, 20.0), torso=20.0, head=6.0, drop=9.0,
            feet={"near": (-38.0, 18.0, -20.0), "far": (6.0, 0.0, 0.0)}, ease="linear"),
        Key(at=F(a1 + 1), near=(80.0, 150.0, 180.0), far=(110.0, 40.0, 20.0), torso=24.0, head=8.0, drop=9.0,
            feet={"near": (-42.0, 22.0, -30.0), "far": (6.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 4), near=(70.0, 140.0, 170.0), far=(100.0, 120.0, 150.0), torso=8.0, head=2.0, drop=6.0,
            feet={"near": (-4.0, 0.0, 0.0), "far": (4.0, 0.0, 0.0)}),
        b.rest_key(1.0),
    ]


def pg_air_neutral(b: Body, a0: int, a1: int) -> List[Key]:
    # A sex kick: the near boot out in front and held, the body leaning back.
    return _air([
        b.rest_key(0.0),
        Key(at=F(max(0, a0 - 1)), near=(80.0, 140.0, 170.0), far=(110.0, 150.0, 175.0), torso=6.0, head=2.0,
            feet={"near": (6.0, 16.0, 30.0), "far": (-2.0, 14.0, 20.0)}, ease="in"),
        Key(at=F(a0), near=(100.0, 150.0, 175.0), far=(130.0, 160.0, 180.0), torso=-12.0, head=-4.0,
            feet={"near": (30.0, 18.0, 20.0), "far": (-6.0, 14.0, 25.0)}, ease="out"),
        Key(at=F(a0 + 1), near=(110.0, 155.0, 180.0), far=(140.0, 165.0, 185.0), torso=-16.0, head=-6.0,
            feet={"near": (36.0, 20.0, 20.0), "far": (-6.0, 14.0, 25.0)}, ease="out"),
        Key(at=F(a1), near=(110.0, 155.0, 180.0), far=(140.0, 165.0, 185.0), torso=-12.0, head=-4.0,
            feet={"near": (32.0, 14.0, 25.0), "far": (-6.0, 14.0, 25.0)}, ease="linear"),
        Key(at=F(a1 + 2), near=(90.0, 140.0, 170.0), far=(110.0, 150.0, 175.0), torso=0.0, head=0.0,
            feet={"near": (8.0, 12.0, 25.0), "far": (-2.0, 12.0, 20.0)}),
        b.rest_key(1.0),
    ])


def pg_air_forward(b: Body, a0: int, a1: int) -> List[Key]:
    # A flying overhead hammer fist.
    c = _contact(a0, a1)
    return _air([
        b.rest_key(0.0),
        Key(at=F(a0 - 2), near=(-130.0, -150.0, -160.0), far=(70.0, 20.0, 0.0), torso=-8.0, head=-4.0,
            lunge=-2.0, feet={"near": (-6.0, 6.0, 30.0)}, ease="in"),
        Key(at=F(a0 - 1), near=(-100.0, -120.0, -130.0), far=(80.0, 30.0, 10.0), torso=-4.0, head=-2.0,
            lunge=-1.0, feet={"near": (-6.0, 6.0, 30.0)}, ease="in"),
        Key(at=F(a0), near=(0.0, -10.0, -15.0), far=(130.0, 120.0, 110.0), torso=16.0, head=6.0, lunge=4.0,
            feet={"near": (-8.0, 5.0, 35.0), "far": (5.0, 10.0, 10.0)}, ease="out"),
        Key(at=F(c), near=(25.0, 15.0, 10.0), far=(140.0, 130.0, 120.0), torso=22.0, head=8.0, lunge=4.0,
            feet={"near": (-8.0, 5.0, 35.0), "far": (5.0, 10.0, 10.0)}, ease="out"),
        Key(at=F(a1 + 1), near=(55.0, 45.0, 40.0), far=(140.0, 130.0, 120.0), torso=24.0, head=8.0, lunge=4.0,
            feet={"near": (-8.0, 5.0, 35.0), "far": (5.0, 10.0, 10.0)}, ease="out"),
        Key(at=F(a1 + 3), near=(80.0, 110.0, 140.0), far=(110.0, 120.0, 140.0), torso=8.0, head=3.0, lunge=2.0),
        b.rest_key(1.0),
    ])


def pg_air_back(b: Body, a0: int, a1: int) -> List[Key]:
    # A back fist: the near arm straight back, the body turned into it.
    c = _contact(a0, a1)
    return _air([
        b.rest_key(0.0),
        Key(at=F(a0 - 1), near=(40.0, -30.0, -40.0), far=(110.0, 110.0, 100.0), torso=10.0, head=4.0,
            feet={"far": (6.0, 10.0, 0.0)}, ease="in"),
        Key(at=F(a0), near=(-120.0, -150.0, -160.0), far=(80.0, 50.0, 40.0), torso=-6.0, head=-8.0, lunge=-1.0,
            feet={"near": (-6.0, 4.0, 30.0), "far": (6.0, 12.0, 0.0)}, ease="out"),
        Key(at=F(c), near=(-178.0, -180.0, -180.0), far=(60.0, 30.0, 20.0), torso=-18.0, head=-14.0, lunge=-3.0,
            feet={"near": (-6.0, 4.0, 30.0), "far": (6.0, 12.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 1), near=(-195.0, -200.0, -205.0), far=(50.0, 20.0, 10.0), torso=-16.0, head=-12.0,
            lunge=-3.0, feet={"near": (-6.0, 4.0, 30.0), "far": (6.0, 12.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 3), near=(-220.0, -230.0, -240.0), far=(90.0, 100.0, 120.0), torso=-6.0, head=-4.0),
        b.rest_key(1.0, turn=-1),
    ])


def pg_air_up(b: Body, a0: int, a1: int) -> List[Key]:
    # A flip kick: the near boot swung from in front up over the head.
    c = _contact(a0, a1)
    return _air([
        b.rest_key(0.0),
        Key(at=F(a0 - 1), near=(60.0, 120.0, 150.0), far=(120.0, 150.0, 175.0), torso=10.0, head=4.0,
            feet={"near": (14.0, 10.0, 20.0), "far": (-4.0, 14.0, 20.0)}, ease="in"),
        Key(at=F(a0), near=(80.0, 130.0, 160.0), far=(130.0, 160.0, 180.0), torso=-6.0, head=-10.0, drop=-1.0,
            feet={"near": (48.0, 26.0, 60.0), "far": (-6.0, 14.0, 25.0)}, ease="out"),
        # The boot up in front of the body, clear of it, the body leaning away.
        Key(at=F(c), near=(100.0, 140.0, 165.0), far=(140.0, 165.0, 185.0), torso=-30.0, head=-22.0, drop=-2.0,
            feet={"near": (50.0, 58.0, 100.0), "far": (-8.0, 14.0, 25.0)}, ease="out"),
        Key(at=F(a1 + 1), near=(110.0, 145.0, 170.0), far=(140.0, 165.0, 185.0), torso=-32.0, head=-24.0, drop=-2.0,
            feet={"near": (34.0, 80.0, 130.0), "far": (-8.0, 14.0, 25.0)}, ease="out"),
        Key(at=F(a1 + 3), near=(90.0, 140.0, 170.0), far=(120.0, 150.0, 175.0), torso=-8.0, head=-8.0,
            feet={"near": (-16.0, 30.0, 40.0), "far": (-4.0, 14.0, 20.0)}),
        b.rest_key(1.0),
    ])


def pg_air_down(b: Body, a0: int, a1: int) -> List[Key]:
    # A stomp: the near boot driven straight down, knees up first.
    c = _contact(a0, a1)
    return _air([
        b.rest_key(0.0),
        Key(at=F(a0 - 1), near=(60.0, 120.0, 150.0), far=(120.0, 150.0, 175.0), torso=8.0, head=6.0, drop=-2.0,
            feet={"near": (6.0, 30.0, 60.0), "far": (-4.0, 24.0, 40.0)}, ease="in"),
        Key(at=F(a0), near=(70.0, 130.0, 160.0), far=(110.0, 140.0, 170.0), torso=14.0, head=10.0, drop=0.0,
            feet={"near": (4.0, 4.0, 70.0), "far": (-6.0, 22.0, 40.0)}, ease="out"),
        Key(at=F(c), near=(80.0, 140.0, 170.0), far=(110.0, 140.0, 170.0), torso=16.0, head=10.0, drop=1.0,
            feet={"near": (4.0, -4.0, 70.0), "far": (-6.0, 22.0, 40.0)}, ease="out"),
        Key(at=F(a1), near=(80.0, 140.0, 170.0), far=(110.0, 140.0, 170.0), torso=16.0, head=10.0, drop=1.0,
            feet={"near": (4.0, -4.0, 70.0), "far": (-6.0, 22.0, 40.0)}),
        Key(at=F(a1 + 1), near=(80.0, 140.0, 170.0), far=(110.0, 140.0, 170.0), torso=14.0, head=8.0, drop=0.0,
            feet={"near": (4.0, -2.0, 70.0), "far": (-6.0, 22.0, 40.0)}),
        Key(at=F(a1 + 3), near=(80.0, 130.0, 160.0), far=(100.0, 130.0, 160.0), torso=6.0, head=3.0),
        b.rest_key(1.0),
    ])


def pg_smash_charge(b: Body) -> List[Key]:
    """The held straight: cocked back, trembling, the knuckles sparking."""
    keys = []
    for i in range(CHARGE_FRAMES):
        u = i / CHARGE_FRAMES
        w = math.sin(u * 2.0 * math.pi)
        shake = 0.5 if i % 2 == 0 else -0.5
        keys.append(Key(at=u, near=(165.0 + 3.0 * w, 200.0, 210.0 + 3.0 * w), far=(60.0 - 2.0 * w, -10.0, -30.0),
                        torso=-14.0 + 1.5 * w, head=-6.0, lunge=-5.0 + 0.8 * w + shake, drop=4.5 + w + 0.5 * shake,
                        feet={"far": (-3.0, 1.0, 10.0)}, ease="linear"))
    return keys


BRAWLER: Dict[str, Strike] = {
    "jab": pg_jab, "attack_side": pg_tilt_forward, "attack_up": pg_tilt_up, "attack_down": pg_tilt_down,
    "dash_attack": pg_dash_attack, "smash_forward": pg_smash_forward, "smash_up": pg_smash_up,
    "smash_down": pg_smash_down, "air_neutral": pg_air_neutral, "air_forward": pg_air_forward,
    "air_back": pg_air_back, "air_up": pg_air_up, "air_down": pg_air_down,
}

#: The brawler's striking limb per row, for the strike axis of its spec.
BRAWLER_STRIKE = {
    "jab": ("near_arm_l", "near_arm_hand"), "attack_side": ("near_arm_l", "near_arm_hand"),
    "attack_up": ("near_arm_l", "near_arm_hand"), "attack_down": ("near_leg_l", "near_leg_foot"),
    "dash_attack": ("near_arm_l", "near_arm_hand"), "smash_forward": ("near_arm_l", "near_arm_hand"),
    "smash_up": ("near_arm_l", "near_arm_hand"), "smash_down": ("near_leg_l", "near_leg_foot"),
    "air_neutral": ("near_leg_l", "near_leg_foot"), "air_forward": ("near_arm_l", "near_arm_hand"),
    "air_back": ("near_arm_l", "near_arm_hand"), "air_up": ("near_leg_l", "near_leg_foot"),
    "air_down": ("near_leg_l", "near_leg_foot"), "smash_charge": ("near_arm_l", "near_arm_hand"),
}


# -- projectile_polygon: the head cannon ------------------------------------------
# He does not swing: a strike is a shot. `aim` points the cannon, the body coils
# before it and is pushed back along the barrel after it (the recoil), which is
# what makes a shot read as a shot. The muzzle flash is the smear.

def _shot(b: Body, a0: int, a1: int, aim: float, *, coil_drop: float = 4.0, coil_lean: float = -6.0,
          recoil: float = 5.0, feet_coil=None, feet_fire=None, air: bool = False,
          start: Optional[Key] = None, end: Optional[Key] = None) -> List[Key]:
    """One shot at `aim`: coil, fire through the window, recoil, settle."""
    c = _contact(a0, a1)
    arms_coil = ((110.0, 150.0, 170.0), (120.0, 160.0, 180.0))
    arms_fire = ((70.0, 120.0, 150.0), (90.0, 140.0, 170.0))
    fc = feet_coil or {}
    ff = feet_fire or {}
    keys = [
        start or b.rest_key(0.0, air=air),
        Key(at=F(a0 - 1), near=arms_coil[0], far=arms_coil[1], torso=coil_lean, head=0.6 * aim - 8.0,
            aim=aim - 6.0, lunge=-2.0, drop=coil_drop, feet=fc, ease="in"),
        Key(at=F(a0), near=arms_fire[0], far=arms_fire[1], torso=6.0, head=0.6 * aim, aim=aim, lunge=2.0,
            drop=coil_drop * 0.5, feet=ff, ease="out"),
        Key(at=F(c), near=arms_fire[0], far=arms_fire[1], torso=4.0, head=0.6 * aim + 2.0, aim=aim, lunge=1.0,
            drop=coil_drop * 0.5, feet=ff, ease="out"),
        # Recoil: pushed back along the barrel.
        Key(at=F(a1 + 1), near=(100.0, 140.0, 160.0), far=(110.0, 150.0, 170.0), torso=-12.0,
            head=0.6 * aim - 6.0, aim=aim + 4.0, lunge=-recoil, drop=coil_drop * 0.5 + 1.0, feet=fc, ease="out"),
        Key(at=F(a1 + 3), near=(95.0, 130.0, 155.0), far=(105.0, 140.0, 165.0), torso=-4.0, head=0.3 * aim,
            aim=0.5 * aim, lunge=-recoil * 0.5, drop=coil_drop * 0.3, feet=fc),
        end or b.rest_key(1.0, air=air),
    ]
    return _air(keys) if air else keys


def pj_jab(b, a0, a1):
    return _shot(b, a0, a1, 0.0, coil_drop=2.0, coil_lean=-4.0, recoil=4.0)


def pj_tilt_forward(b, a0, a1):
    return _shot(b, a0, a1, 0.0, coil_drop=5.0, coil_lean=-8.0, recoil=7.0,
                 feet_coil={"far": (-4.0, 0.0, 0.0)}, feet_fire={"near": (8.0, 0.0, 0.0), "far": (-4.0, 0.0, 0.0)})


def pj_tilt_up(b, a0, a1):
    return _shot(b, a0, a1, -62.0, coil_drop=6.0, coil_lean=-4.0, recoil=3.0)


def pj_tilt_down(b, a0, a1):
    crouch = Key(at=0.0, near=(90.0, 140.0, 170.0), far=(100.0, 150.0, 175.0), torso=12.0, head=10.0, drop=12.0,
                 aim=20.0, feet={"near": (-5.0, 0.0, 0.0), "far": (6.0, 0.0, 0.0)}, ease="in")
    keys = _shot(b, a0, a1, 40.0, coil_drop=14.0, coil_lean=10.0, recoil=3.0,
                 feet_coil={"near": (-5.0, 0.0, 0.0), "far": (6.0, 0.0, 0.0)},
                 feet_fire={"near": (-5.0, 0.0, 0.0), "far": (10.0, 0.0, 0.0)},
                 start=crouch, end=replace(crouch, at=F(a1 + 5)))
    return keys + [b.rest_key(1.0)]


def pj_dash_attack(b, a0, a1):
    # Two shots on the run: one as he arrives, one as he passes.
    run = {"near": (-8.0, 4.0, 25.0), "far": (10.0, 0.0, -5.0)}
    arms = ((80.0, 130.0, 160.0), (100.0, 150.0, 175.0))
    mid = (a0 + a1) // 2
    return [
        Key(at=0.0, near=arms[0], far=arms[1], torso=14.0, head=-4.0, aim=0.0, drop=4.0,
            feet={"near": (-4.0, 2.0, 18.0), "far": (4.0, 0.0, 0.0)}),
        Key(at=F(a0 - 1), near=arms[0], far=arms[1], torso=10.0, head=-6.0, aim=-6.0, lunge=2.0, drop=5.0,
            feet=run, ease="in"),
        Key(at=F(a0), near=arms[0], far=arms[1], torso=20.0, head=0.0, aim=0.0, lunge=8.0, drop=5.0, feet=run,
            ease="out"),
        Key(at=F(a0 + 1), near=arms[0], far=arms[1], torso=8.0, head=-4.0, aim=2.0, lunge=6.0, drop=5.5,
            feet=run, ease="out"),
        Key(at=F(mid + 1), near=arms[0], far=arms[1], torso=22.0, head=2.0, aim=0.0, lunge=14.0, drop=5.0,
            feet=run, ease="out"),
        Key(at=F(a1 + 1), near=arms[0], far=arms[1], torso=6.0, head=-6.0, aim=4.0, lunge=12.0, drop=6.0,
            feet=run, ease="out"),
        Key(at=F(a1 + 4), near=arms[0], far=arms[1], torso=8.0, head=0.0, aim=0.0, lunge=10.0, drop=3.0,
            feet={"far": (4.0, 0.0, 0.0)}),
        b.rest_key(1.0),
    ]


def pj_smash_forward(b, a0, a1):
    # The charged beam: a long coil, the lance, and the biggest shove back.
    brace = {"near": (10.0, 0.0, 0.0), "far": (-6.0, 0.0, 0.0)}
    arms = ((100.0, 150.0, 175.0), (110.0, 160.0, 185.0))
    return [
        b.rest_key(0.0),
        Key(at=F(1), near=arms[0], far=arms[1], torso=-6.0, head=-6.0, aim=-8.0, lunge=-2.0, drop=4.0),
        Key(at=F(a0 - 1), near=arms[0], far=arms[1], torso=-14.0, head=-12.0, aim=-14.0, lunge=-6.0, drop=10.0,
            feet={"far": (-4.0, 0.0, 0.0)}, ease="in"),
        Key(at=F(a0), near=(70.0, 120.0, 150.0), far=(90.0, 140.0, 170.0), torso=12.0, head=2.0, aim=0.0,
            lunge=5.0, drop=5.0, feet=brace, ease="out"),
        Key(at=F(a1), near=(70.0, 120.0, 150.0), far=(90.0, 140.0, 170.0), torso=10.0, head=3.0, aim=0.0,
            lunge=4.0, drop=5.0, feet=brace, ease="linear"),
        Key(at=F(a1 + 1), near=arms[0], far=arms[1], torso=-18.0, head=-8.0, aim=6.0, lunge=-12.0, drop=7.0,
            feet={"far": (-4.0, 0.0, 0.0)}, ease="out"),
        Key(at=F(a1 + 3), near=arms[0], far=arms[1], torso=-8.0, head=-4.0, aim=2.0, lunge=-5.0, drop=4.0,
            feet={"far": (-4.0, 0.0, 0.0)}),
        b.rest_key(1.0),
    ]


def pj_smash_up(b, a0, a1):
    return _shot(b, a0, a1, -78.0, coil_drop=10.0, coil_lean=6.0, recoil=2.0,
                 feet_fire={"near": (0.0, 3.0, 15.0), "far": (0.0, 3.0, 15.0)})


def pj_smash_down(b, a0, a1):
    return _shot(b, a0, a1, 62.0, coil_drop=8.0, coil_lean=-8.0, recoil=4.0,
                 feet_coil={"near": (-6.0, 0.0, 0.0), "far": (6.0, 0.0, 0.0)},
                 feet_fire={"near": (-8.0, 0.0, 0.0), "far": (8.0, 0.0, 0.0)})


def pj_air_neutral(b, a0, a1):
    # The cannon sweeps from forward-down up over the front across the window.
    arms = ((90.0, 140.0, 170.0), (100.0, 150.0, 175.0))
    keys = [b.rest_key(0.0, air=True),
            Key(at=F(max(0, a0 - 1)), near=arms[0], far=arms[1], torso=4.0, head=10.0, aim=30.0, ease="in")]
    span = max(1, a1 - a0)
    for i, aim in enumerate((20.0, -10.0, -40.0, -70.0)):
        keys.append(Key(at=F(a0 + span * i / 3), near=arms[0], far=arms[1], torso=4.0 - 4.0 * i,
                        head=0.5 * aim, aim=aim, lunge=-1.0 * i, ease="linear" if i else "out"))
    keys.append(Key(at=F(a1 + 2), near=arms[0], far=arms[1], torso=-4.0, head=-10.0, aim=-20.0))
    keys.append(b.rest_key(1.0, air=True))
    return _air(keys)


def pj_air_forward(b, a0, a1):
    return _shot(b, a0, a1, 10.0, coil_drop=0.0, coil_lean=-8.0, recoil=6.0, air=True)


def pj_air_back(b, a0, a1):
    # Fired back over the shoulder: the body turned up and back after the cannon.
    return _shot(b, a0, a1, -135.0, coil_drop=0.0, coil_lean=-14.0, recoil=-5.0, air=True)


def pj_air_up(b, a0, a1):
    return _shot(b, a0, a1, -80.0, coil_drop=0.0, coil_lean=-4.0, recoil=0.0, air=True)


def pj_air_down(b, a0, a1):
    return _shot(b, a0, a1, 85.0, coil_drop=0.0, coil_lean=14.0, recoil=-4.0, air=True,
                 feet_fire={"near": (-8.0, 14.0, 40.0), "far": (-3.0, 16.0, 35.0)})


def pj_smash_charge(b: Body) -> List[Key]:
    """The held beam: braced low, trembling, the muzzle sparking."""
    keys = []
    for i in range(CHARGE_FRAMES):
        u = i / CHARGE_FRAMES
        w = math.sin(u * 2.0 * math.pi)
        shake = 0.5 if i % 2 == 0 else -0.5
        keys.append(Key(at=u, near=(100.0, 150.0, 175.0), far=(110.0, 160.0, 185.0), torso=-10.0 + 1.5 * w,
                        head=-10.0 + 1.0 * w, aim=-12.0 + 2.0 * w, lunge=-4.0 + 0.8 * w + shake,
                        drop=7.0 + w + 0.5 * shake, feet={"far": (-4.0, 0.0, 0.0)}, ease="linear"))
    return keys


BEAST: Dict[str, Strike] = {
    "jab": pj_jab, "attack_side": pj_tilt_forward, "attack_up": pj_tilt_up, "attack_down": pj_tilt_down,
    "dash_attack": pj_dash_attack, "smash_forward": pj_smash_forward, "smash_up": pj_smash_up,
    "smash_down": pj_smash_down, "air_neutral": pj_air_neutral, "air_forward": pj_air_forward,
    "air_back": pj_air_back, "air_up": pj_air_up, "air_down": pj_air_down,
}


# ── the specs ──────────────────────────────────────────────────────────────────
#
# Each row's effect, restyled to read at game scale: a hot core, a fuller
# body, and for a sword the arc of the tip along the whole sweep.

TILT_TRAIL = {"window": 4, "subdiv": 8, "inner": 0.5, "alpha": 190, "core_alpha": 245, "blur": 1.0, "falloff": 1.3,
              "taper": 0.55, "edge_width": 3.0, "body_rgb": [150, 96, 230], "core_rgb": [236, 220, 255]}
SMASH_TRAIL = {"window": 5, "subdiv": 8, "inner": 0.4, "alpha": 215, "core_alpha": 250, "blur": 1.3, "falloff": 1.1,
               "taper": 0.5, "edge_width": 4.0, "body_rgb": [212, 104, 252], "core_rgb": [255, 244, 255]}
SWORD_POKE = {"extend": 1.34, "width": 15.0, "waist": 0.66, "inner": 0.08, "alpha": 210, "blur": 1.0,
              "core_alpha": 240, "falloff": 2.0, "window": 2, "body_rgb": [150, 208, 255], "core_rgb": [240, 252, 255]}
FIST_POKE = {"extend": 1.34, "width": 16.0, "waist": 0.62, "inner": 0.16, "alpha": 195, "core_alpha": 235,
             "blur": 1.1, "falloff": 2.0, "window": 2, "body_rgb": [236, 240, 250], "core_rgb": [255, 255, 255]}
WIND = {"window": 4, "subdiv": 8, "inner": 0.3, "alpha": 170, "core_alpha": 220, "blur": 0.8, "falloff": 1.5, "streaks": 4,
        "spread": 0.36}
REENTRY = {"window": 3, "spread": 0.8, "extend": 1.12, "trail": 0.55, "alpha": 140, "core_alpha": 235, "blur": 1.6,
           "falloff": 1.7}
MUZZLE = {"reach": 2.6, "flare": 0.36, "alpha": 215, "core_alpha": 245, "blur": 1.3, "window": 1,
          "falloff": 2.4, "bloom": 1.0}
BEAM = {"reach": 9.0, "width": 0.5, "alpha": 200, "core_alpha": 250, "blur": 2.4, "window": 2,
        "falloff": 1.5, "bloom": 2.2}
#: The charge's spark, per fighter: the colour of its weapon.
GLINT = {
    "pointed_polygon": {"strength": CHARGE_GLINT, "size": 14.0, "body_rgb": [212, 182, 250], "core_rgb": [255, 250, 255]},
    "pugnacious_polygon": {"strength": CHARGE_GLINT, "size": 14.0, "body_rgb": [255, 196, 72], "core_rgb": [255, 250, 232]},
    "projectile_polygon": {"strength": CHARGE_GLINT, "size": 14.0, "body_rgb": [186, 246, 255], "core_rgb": [244, 252, 255]},
}

POINTED_EFFECTS = {
    "jab": ("poke", SWORD_POKE), "attack_side": ("trail", TILT_TRAIL), "attack_up": ("trail", TILT_TRAIL),
    "attack_down": ("poke", SWORD_POKE), "dash_attack": ("trail", TILT_TRAIL),
    "smash_forward": ("trail", SMASH_TRAIL), "smash_up": ("trail", SMASH_TRAIL), "smash_down": ("trail", SMASH_TRAIL),
    "air_neutral": ("trail", TILT_TRAIL), "air_forward": ("trail", TILT_TRAIL), "air_back": ("trail", TILT_TRAIL),
    "air_up": ("trail", TILT_TRAIL), "air_down": ("poke", SWORD_POKE),
}
BRAWLER_EFFECTS = {
    "jab": ("poke", FIST_POKE), "attack_side": ("wind", WIND), "attack_up": ("wind", WIND),
    "attack_down": ("wind", WIND), "dash_attack": ("wind", WIND), "smash_forward": ("reentry", REENTRY),
    "smash_up": ("reentry", REENTRY), "smash_down": ("reentry", REENTRY), "air_neutral": ("poke", FIST_POKE),
    "air_forward": ("reentry", REENTRY), "air_back": ("poke", FIST_POKE), "air_up": ("wind", WIND),
    "air_down": ("reentry", REENTRY),
}
BEAST_EFFECTS = {name: ("muzzle", MUZZLE) for name in BEAST}
BEAST_EFFECTS["smash_forward"] = ("beam", BEAM)
#: Rows whose sweep is drawn on the frame before the hit as well (the weapon
#: in flight) and the frame after (the follow-through); the hit volume stays
#: the clock's. A swept effect needs two live frames to draw anything.
SWEPT = {"trail", "wind"}


def spec_for(fighter: str, name: str, effect: str, style: dict, active: List[int], strike=None,
             air: bool = False) -> dict:
    spec: dict = {
        "clip": name,
        "note": f"{name}: keys in devtools/polygon_keys.py, fitted to the Smash stage's clock; "
                f"the hit window is the clock's active frames.",
        "effect": effect,
        "facing": "west" if fighter == "pointed_polygon" else "east",
    }
    if strike:
        spec["strike"] = {"base": strike[0], "tip": strike[1]}
    spec["hitbox"] = {"active": list(active), "extend": 1.06} if fighter != "pointed_polygon" else {"active": list(active)}
    style = dict(style)
    if effect in SWEPT:
        style["active"] = list(range(max(0, active[0] - 1), min(ATTACK_FRAMES, active[-1] + 2)))
    spec[effect] = style
    if air:
        spec["airborne"] = True
    spec["pixel_invariants"] = ["hitbox_in_front"] if name not in ("air_back", "smash_down", "air_neutral", "attack_up", "smash_up", "air_up") else []
    return spec


def charge_spec(fighter: str, strike=None) -> dict:
    spec = {
        "clip": "smash_charge",
        "note": "The held smash: the body shakes one pixel each frame and the weapon's point sparks. "
                "No hit window: nothing has left the weapon yet.",
        "effect": "glint",
        "facing": "west" if fighter == "pointed_polygon" else "east",
        "glint": dict(GLINT[fighter]),
    }
    if strike:
        spec["strike"] = {"base": strike[0], "tip": strike[1]}
    return spec


FIGHTERS = {
    "pointed_polygon": ("fast", POINTED, POINTED_EFFECTS, None, pp_smash_charge),
    "pugnacious_polygon": ("fast", BRAWLER, BRAWLER_EFFECTS, BRAWLER_STRIKE, pg_smash_charge),
    "projectile_polygon": ("heavy", BEAST, BEAST_EFFECTS, {name: ("cannon", "cannon") for name in list(BEAST) + ["smash_charge"]}, pj_smash_charge),
}


#: The library's reusable named poses (`poses/`): the anticipation, the
#: contact and the recovery of a strike, which the pointed polygon's jab and
#: forward tilt refer to by name.
NAMED_POSES = {"pointed_polygon": {"jab": "humanoid/fighting_polygon/jab", "attack_side": "humanoid/fighting_polygon/ftilt"}}


def named_poses(fighter: str, name: str, active: List[int]) -> Dict[int, str]:
    stem = NAMED_POSES.get(fighter, {}).get(name)
    if not stem:
        return {}
    a0, a1 = active[0], active[-1]
    return {a0 - 1: f"{stem}/anticipation", _contact(a0, a1): f"{stem}/contact", a1 + 3: f"{stem}/recovery"}


def load_target(fighter: str):
    import importlib

    return importlib.import_module(f"ambition_sprite2d_renderer.targets.characters.{fighter}")


def apply(fighter: str, rows: Optional[Sequence[str]] = None) -> List[str]:
    """Write the clips and specs of `fighter` (all attack rows, or `rows`)."""
    clocks, strikes, effects, strike_of, charge = FIGHTERS[fighter]
    target = load_target(fighter)
    body = Body(target, clocks)
    written = []
    for name, keys_for in strikes.items():
        if rows and name not in rows:
            continue
        active = active_frames(name, clocks)
        keys = keys_for(body, active[0], active[-1])
        body.write_clip(name, keys, ATTACK_FRAMES, ROW_MS[name], named=named_poses(fighter, name, active))
        effect, style = effects[name]
        body.write_spec(name, spec_for(fighter, name, effect, style, active,
                                       strike_of[name] if strike_of else None, air=name.startswith("air_")))
        written.append(name)
    if not rows or "smash_charge" in rows:
        body.write_clip("smash_charge", charge(body), CHARGE_FRAMES, CHARGE_MS, loop=False)
        body.write_spec("smash_charge", charge_spec(fighter, strike_of["smash_charge"] if strike_of else None))
        written.append("smash_charge")
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("apply", help="write the clips and specs")
    a.add_argument("fighter", nargs="?", help="one fighter; default all three")
    a.add_argument("--rows", help="comma-separated rows; default every attack row")
    args = parser.parse_args(argv)
    fighters = [args.fighter] if args.fighter else list(FIGHTERS)
    rows = args.rows.split(",") if args.rows else None
    for fighter in fighters:
        print(fighter, ", ".join(apply(fighter, rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
