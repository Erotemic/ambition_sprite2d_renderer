"""The world-space pose core shared by the Polygon fighters' generators.

A pose is a [`Key`] in forward-relative world degrees (0 is the way the
fighter faces, 90 straight down, -90 straight up); [`Body`] reads one
fighter's rig from its target and solves keys into the motion library's FK
deltas, placing the boots by two-bone IK, and writes clip JSON. It knows no
attack timing and no hitboxes: `polygon_keys.py` (attack rows, fitted to
the Smash clocks, with swing specs) and `reaction_keys.py` (hit, launch,
prone and balance reactions) are its two callers.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable, Dict, Optional, Sequence, Tuple

from ..authoring.skeleton import two_bone_ik

Foot = Tuple[float, float, float]  # (forward px from the standing ankle, lift px, pitch deg)
SIDES = ("near", "far")

#: How far above the standing feet an airborne row rides, in px.
AIR_RISE = -6.0


def load_target(fighter: str):
    import importlib

    return importlib.import_module(f"ambition_sprite2d_renderer.targets.characters.{fighter}")


@dataclass(frozen=True)
class Key:
    """One key pose at `at` (0..1) of the move.

    `near`/`far` are (upper arm, forearm, hand) in forward-relative world
    degrees; `None` holds the arm at rest, carried by the torso. `torso`,
    `head` lean forward when positive. `lunge` is forward px, `drop` down px.
    `feet` places boots (see `Foot`); an unlisted boot stays planted, and in
    the `air` every boot rides with the body. `aim` turns the beast's cannon
    (forward-relative degrees), `None` keeps it with the head. `ease` shapes
    the approach INTO this key: "out" arrives fast (a cut), "gather" moves at
    once and settles (a wind-up), "in" holds and then moves, "smooth" both,
    "linear" neither.

    `tilt` turns the whole body about the hips, forward when positive: the
    pelvis, torso and head turn with it, the arms stay in world terms. A
    tilted body (or one `carried`) carries its legs: they keep their
    standing shape in the body's frame and `feet` offsets are in that frame,
    instead of reaching for the standing ankles (a launch, a tumble, a body
    lying on the floor).
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
    tilt: float = 0.0
    carried: bool = False


_EASES: Dict[str, Callable[[float], float]] = {
    "linear": lambda u: u,
    "smooth": lambda u: u * u * (3.0 - 2.0 * u),
    "out": lambda u: 1.0 - (1.0 - u) ** 3,
    "in": lambda u: u ** 3,
    # A wind-up: the body starts into the coil at once and settles into it,
    # so a slow move shows its gather over the whole startup. Cubic "in" held
    # the rest pose for most of a long startup and snapped into the coil on
    # its last frame (a Falcon-paced up tilt read as standing, then a swing).
    "gather": lambda u: 1.0 - (1.0 - u) ** 2,
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
        tilt=_lerp(a.tilt, b.tilt, u),
        carried=a.carried or b.carried,
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

    def __init__(self, target) -> None:
        self.target = target
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
        self.hip_rest = {s: stand[f"{s}_leg_u"].origin for s in SIDES}
        self.foot_rest = {s: stand[f"{s}_leg_foot"].angle for s in SIDES}
        self.leg = {s: (self.sk.bones[f"{s}_leg_u"].length, self.sk.bones[f"{s}_leg_l"].length) for s in SIDES}
        self.arm_rest = {
            s: tuple(self.fwd_of(stand[f"{s}_arm_{part}"].angle) for part in ("u", "l", "hand")) for s in SIDES
        }
        self.has_cannon = "cannon" in self.sk.bones
        # How far the resting trunk (pelvis to head) leans forward of upright,
        # in degrees: ~0 for an upright humanoid, large for a beast whose
        # body is carried forward. A pose that sets the trunk's absolute
        # direction (lying flat, diving head-first) tilts TO it: `trunk_to`.
        pelvis, head = stand["pelvis"].origin, stand["head"].origin
        self.trunk_lean = math.degrees(math.atan2(self.facing * (head[0] - pelvis[0]), pelvis[1] - head[1]))

    def trunk_to(self, direction: float) -> float:
        """The tilt that turns this rig's resting trunk to `direction`, in
        forward-relative degrees from upright (90 lies forward, -90 lies back)."""
        return direction - self.trunk_lean

    # Forward-relative degrees <-> world degrees.
    def fwd(self, f: float) -> float:
        return f if self.facing > 0 else 180.0 - f

    def fwd_of(self, world: float) -> float:
        return world if self.facing > 0 else 180.0 - world

    def channels(self, key: Key) -> Dict[str, float]:
        """The clip's deltas (rendered-rig convention) and the root, px."""
        rest, s = self.rest, self.facing
        pelvis = s * (0.35 * key.torso + key.tilt)
        torso_w = s * (key.torso + key.tilt)
        d: Dict[str, float] = {
            "pelvis": pelvis,
            "torso": torso_w - pelvis,
            "head": s * (key.head + key.tilt) - torso_w,
            "_root_x": s * key.lunge,
            "_root_y": key.drop,
        }
        for side in SIDES:
            arm = key.near if side == "near" else key.far
            if arm is None:
                r = self.arm_rest[side]
                lean = key.torso + key.tilt
                arm = (r[0] + lean, r[1] + lean, r[2] + lean)
            wu, wl, wh = (self.fwd(a) for a in arm)
            d[f"{side}_arm_u"] = wu - torso_w - rest[f"{side}_arm_u"]
            d[f"{side}_arm_l"] = wl - wu - rest[f"{side}_arm_l"]
            d[f"{side}_arm_hand"] = wh - wl - rest[f"{side}_arm_hand"]
        if self.has_cannon:
            head_w = s * (key.head + key.tilt)
            d["cannon"] = 0.0 if key.aim is None else self.fwd(key.aim) - head_w - rest["cannon"]
        root = (self.root[0] + d["_root_x"], self.root[1] + d["_root_y"])
        angles = {k: v for k, v in d.items() if k in self.sk.bones}
        world = self.sk.world(angles, root=root)
        carried = key.tilt != 0.0 or key.carried
        turn = math.radians(s * key.tilt)
        cos_t, sin_t = math.cos(turn), math.sin(turn)
        for side in SIDES:
            dx, lift, pitch = key.feet.get(side, (0.0, 0.0, 0.0))
            hip = world[f"{side}_leg_u"].origin
            if carried:
                # The standing ankle in the body's frame, turned with it.
                rx = self.ankle_rest[side][0] - self.hip_rest[side][0] + s * dx
                ry = self.ankle_rest[side][1] - self.hip_rest[side][1] - lift
                ankle = (hip[0] + rx * cos_t - ry * sin_t, hip[1] + rx * sin_t + ry * cos_t)
                pitch = pitch + key.tilt
            else:
                ax, ay = self.ankle_rest[side]
                if key.air:
                    ax += d["_root_x"]
                    ay += d["_root_y"]
                ankle = (ax + s * dx, ay - lift)
            upper, lower = self.leg[side]
            a1, a2 = two_bone_ik(hip, ankle, upper, lower, bend=s)
            d[f"{side}_leg_u"] = a1 - pelvis - rest[f"{side}_leg_u"]
            d[f"{side}_leg_l"] = a2 - a1 - rest[f"{side}_leg_l"]
            d[f"{side}_leg_foot"] = self.foot_rest[side] + s * pitch - a2 - rest[f"{side}_leg_foot"]
        return d

    def world(self, key: Key) -> dict:
        """Every bone's world placement (frame px) at `key`."""
        d = self.channels(key)
        root = (self.root[0] + d["_root_x"], self.root[1] + d["_root_y"])
        return self.sk.world({k: v for k, v in d.items() if k in self.sk.bones}, root=root)

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

    def write_clip(self, name: str, keys: Sequence[Key], frames: int, step_ms: int, loop: bool = False,
                   named: Optional[Dict[int, str]] = None, generator: str = "devtools/polygon_keys.py",
                   template: Optional[str] = None,
                   phase_of: Optional[Callable[[int], float]] = None) -> None:
        """Write the clip. `named` maps a frame to a reusable pose id of the
        library: that frame's state is written to the pose file and the clip
        refers to it, so the named whole-body poses stay the clip's."""
        if [k.at for k in keys] != sorted(k.at for k in keys):
            raise ValueError(f"{name}: key phases must be in order")
        keys = [self.resolved(k) for k in keys]
        # A frame is posed at the centre of its span unless the caller says otherwise.
        centre = phase_of or (lambda i: (i + 0.5) / frames)
        phases = [i / frames for i in range(frames)] if loop else [centre(i) for i in range(frames)]
        path = self.clip_path(name)
        # A new clip starts from `template`'s file (its schema and fields), renamed.
        source = path if path.exists() or template is None else self.clip_path(template)
        doc = json.loads(source.read_text())
        doc["id"] = name
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
            "note": f"Keyed in world terms by {generator} and solved to FK; edit the keys, not this file.",
        }
        doc["pose_keys"] = [
            {"at_s": round(i * step_ms / 1000.0, 6), "frame": i, "interpolation": "linear",
             **({"pose": named[i]} if i in named else {"state": self.state(sample(keys, ph))})}
            for i, ph in enumerate(phases)
        ]
        _write_json(path, doc)


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
