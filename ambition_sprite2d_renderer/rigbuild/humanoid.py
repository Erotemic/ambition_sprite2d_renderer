"""The humanoid fighter family's anatomy and pose language, for ``creature_rig``.

Bob's body: a ``pelvis`` root (turning it spins the whole fighter about his
hips: flips, rolls, tumbles), a ``torso`` from the pelvis to the neck, a
``head``, two FK arms (``<side>_arm_u`` / ``<side>_arm_l`` / ``<side>_hand``)
and two IK legs (``<side>_leg_u`` / ``<side>_leg_l`` / ``<side>_foot``) whose
feet plant. The SVG marks the joints ``pelvis``, ``neck``, ``head_top`` and per
side ``<side>_shoulder``, ``_elbow``, ``_wrist``, ``_hip``, ``_knee``,
``_ankle``. Hand parts are drawn pointing +x from the wrist (a hand bone's
rest world angle is 0); a prop held in the fist runs up the hand's local -y.

⭐ THE POSE LANGUAGE. A fighter's moves are written as key poses, not as rig
channels. A pose is a dict of a few readable fields, all in SVG units and
degrees (y down, a positive angle turns clockwise on screen, the fighter
faces +x):

``x``, ``y``
    The hips' offset from where they were drawn (``y`` < 0 is up).
``spin``
    The whole body turned about the hips (a forward flip runs positive), or
    about a point ``spin_about`` units up the torso.
``lean``
    The torso bent over the hips (positive: forward).
``head``
    The head's WORLD tilt from upright (positive: chin down), so a leaning
    fighter keeps his eyes on the opponent unless told otherwise.
``nu`` / ``fu``
    The near / far upper arm's WORLD direction (0 forward, 90 hanging, -90
    straight up, 180 straight back).
``ne`` / ``fe``
    Elbow flexion: the forearm turned back from the upper arm's line
    (0 straight; 90 a right angle, the hand curling forward and up).
``nw`` / ``fw``
    The WORLD direction a prop gripped in that hand points (``-90`` up, 0
    forward). For a hand holding nothing it is just the fist's angle.
``nf`` / ``ff``
    A foot: ``("g", x, lift, pitch)`` planted in the world (``x`` from the
    centre line, ``lift`` above the ground), or ``("b", dx, dy, pitch)``
    carried with the body (an offset from where the drawing put that ankle,
    in the hips' frame: a tucked or kicking leg in the air).
``fz``
    Draw-order lift for the far arm (0: behind the body; about 55: across
    the chest, under the near arm).
``eye``, ``mouth``, ``nhand``, ``fhand``
    Swap-set states (``eye``: open / angry / shut / dead / dizzy;
    ``mouth``: closed / smile / open / grit; a hand: fist / open).
``wrench``, ``analyzer``
    Prop visibility (0 or 1; a wrench out of the hand shows stowed on the
    back). Anything named ``fx.*`` or ``bone.*``, and
    ``body_opacity``, passes straight through as a channel.

``keyed(base, keys)`` builds a clip function from timed key poses; each key
says only what changes and carries everything else forward, and how it is
reached (``"ease"``: ``io`` smooth, ``out`` a fast start that settles, ``in`` a
slow start that snaps, ``lin``, ``hold`` stays at the previous key until this
one's time). ``Body.channels`` turns a pose into the rig's channels.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple, Union

from .creature_rig import (  # noqa: F401  (re-exported for builder scripts)
    BoneSpec,
    CreatureSpec,
    Leg,
    Point,
    Pose,
    heading,
    limb,
    pulse,
    read_svg,
    rotate,
    segment,
    smooth01,
    track,
    write,
)

SIDES = ("far", "near")
EYES = ("open", "angry", "shut", "dead", "dizzy")
MOUTHS = ("closed", "smile", "open", "grit")
HANDS = ("fist", "open")
#: A hand bone's length (SVG units): only the editor draws it.
HAND_LENGTH = 22.0

Foot = Tuple[str, float, float, float]
Value = Union[float, str, Foot]
Semantic = Dict[str, Value]


def skeleton(J: Dict[str, Point], hand_len: float) -> List[BoneSpec]:
    bones: List[BoneSpec] = [("pelvis", None, J["pelvis"], -90.0, 0.0)]
    bones.append(segment("torso", "pelvis", J["pelvis"], J["neck"]))
    bones.append(segment("head", "torso", J["neck"], J["head_top"]))
    for side in SIDES:
        bones.append(segment(f"{side}_arm_u", "torso", J[f"{side}_shoulder"], J[f"{side}_elbow"]))
        bones.append(segment(f"{side}_arm_l", f"{side}_arm_u", J[f"{side}_elbow"], J[f"{side}_wrist"]))
        bones.append((f"{side}_hand", f"{side}_arm_l", J[f"{side}_wrist"], 0.0, round(hand_len, 4)))
    for side in SIDES:
        bones += limb(f"{side}_leg_u", f"{side}_leg_l", f"{side}_foot", "pelvis",
                      J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"])
    return bones


def humanoid_spec(*, knee_bend: float = 1.0, far_knee_bend: float | None = None, **fields) -> CreatureSpec:
    """A ``CreatureSpec`` with the humanoid skeleton and two IK legs. A side
    view's knees both fold forward (``knee_bend``); a front view's fold
    outward, mirrored, so the far leg takes ``far_knee_bend``."""
    bends = {"near": knee_bend, "far": knee_bend if far_knee_bend is None else far_knee_bend}
    legs = [Leg(f"{side}_leg_u", f"{side}_leg_l", f"{side}_foot", f"{side}_foot", f"{side}_ankle", bend=bends[side])
            for side in SIDES]
    hand_len = HAND_LENGTH * fields["scale"]
    angles = {"pelvis", "torso", "head"}
    for side in SIDES:
        angles |= {f"{side}_arm_u", f"{side}_arm_l", f"{side}_hand", f"{side}_foot_pitch"}
    fields.setdefault("angle_channels", frozenset(angles))
    fields.setdefault("compact_keys", True)
    return CreatureSpec(skeleton=lambda J: skeleton(J, hand_len), legs=legs, **fields)


# --- the pose language -----------------------------------------------------------


@dataclass
class Body:
    """The drawn rest geometry a pose is measured against (SVG units)."""

    J: Dict[str, Point]
    center_x: float
    ground_y: float

    @classmethod
    def from_svg(cls, svg_path: Path, center_x: float, ground_y: float) -> "Body":
        J, _parts = read_svg(svg_path)
        return cls(J, center_x, ground_y)

    @property
    def ankle_h(self) -> float:
        return self.ground_y - self.J["near_ankle"][1]

    def rest_x(self, side: str) -> float:
        return self.J[f"{side}_ankle"][0] - self.center_x

    def hip_offset(self) -> Point:
        return (self.J["pelvis"][0] - self.center_x, self.J["pelvis"][1] - self.ground_y)

    def _rest(self, a: str, b: str) -> float:
        return heading(self.J[a], self.J[b])

    def foot_world(self, pose: Semantic, side: str) -> Tuple[float, float, float]:
        """A foot as ``(x, lift, pitch)`` in the world, whatever its mode."""
        pose = self.pivoted(pose)
        mode, a, b, pitch = pose[f"{side[0]}f"]  # type: ignore[misc]
        if mode == "g":
            return float(a), float(b), float(pitch)
        spin = float(pose.get("spin", 0.0))
        px, py = self.hip_offset()
        ax, ay = self.J[f"{side}_ankle"]
        hx, hy = self.J["pelvis"]
        lx, ly = rotate((ax - hx + float(a), ay - hy + float(b)), spin)
        wx = px + float(pose.get("x", 0.0)) + lx
        wy = py + float(pose.get("y", 0.0)) + ly
        return wx, -wy - self.ankle_h, float(pitch) + spin

    @staticmethod
    def pivoted(pose: Semantic) -> Semantic:
        """``spin_about`` (units above the hips) moves the spin's pivot up the
        body: a flip turns about the middle of the torso instead of the hips,
        which keeps a whirling fighter inside his frame."""
        h = float(pose.get("spin_about", 0.0))
        if not h:
            return pose
        rx, ry = rotate((0.0, -h), float(pose.get("spin", 0.0)))
        out = {k: v for k, v in pose.items() if k != "spin_about"}
        out["x"] = float(pose.get("x", 0.0)) - rx
        out["y"] = float(pose.get("y", 0.0)) - h - ry
        return out

    def channels(self, pose: Semantic) -> Pose:
        """The rig channels for one semantic pose."""
        pose = self.pivoted(pose)
        g = lambda k, d=0.0: float(pose.get(k, d))  # noqa: E731
        spin, lean = g("spin"), g("lean")
        out: Pose = {
            "root_x": g("x"),
            "root_y": g("y"),
            "pelvis": spin,
            "torso": lean,
            "head": g("head") - spin - lean,
        }
        for side in SIDES:
            s = side[0]
            ru = self._rest(f"{side}_shoulder", f"{side}_elbow")
            rl = self._rest(f"{side}_elbow", f"{side}_wrist")
            upper = g(f"{s}u", ru)
            flex = g(f"{s}e", ru - rl)
            fore = upper - flex
            out[f"{side}_arm_u"] = wrap(upper - ru - spin - lean)
            out[f"{side}_arm_l"] = wrap(-flex - rl + ru)
            out[f"{side}_hand"] = wrap(g(f"{s}w", -90.0) + 90.0 - fore + rl)
            x, lift, pitch = self.foot_world(pose, side)
            out[f"{side}_foot_x"] = x
            out[f"{side}_foot_lift"] = lift
            out[f"{side}_foot_pitch"] = pitch
            hand = str(pose.get(f"{s}hand", "fist"))
            for h in HANDS:
                out[f"hand.{side}.{h}"] = 1.0 if h == hand else 0.0
        # The far arm is drawn behind the body; ``fz`` lifts it over the torso
        # (under the near arm) for a reach across the chest: a grab, a throw.
        fz = g("fz")
        for bone in ("far_arm_u", "far_arm_l", "far_hand"):
            out[f"bone.{bone}.z"] = fz
        eye = str(pose.get("eye", "open"))
        for e in EYES:
            out[f"eye.{e}"] = 1.0 if e == eye else 0.0
        mouth = str(pose.get("mouth", "closed"))
        for m in MOUTHS:
            out[f"mouth.{m}"] = 1.0 if m == mouth else 0.0
        # A wrench not in the hand is stowed in its strap across the back.
        out["prop.wrench"] = g("wrench", 1.0)
        out["prop.wrench_back"] = 1.0 - out["prop.wrench"]
        out["prop.analyzer"] = g("analyzer", 0.0)
        for k, v in pose.items():
            if k.startswith("fx.") and float(v) == 0.0:  # type: ignore[arg-type]
                continue  # an effect at rest is no channel (the default is 0)
            if k.startswith(("fx.", "bone.")) or k == "body_opacity":
                out[k] = float(v)  # type: ignore[arg-type]
        return out


def wrap(deg: float) -> float:
    return (deg + 180.0) % 360.0 - 180.0


EASES: Dict[str, Callable[[float], float]] = {
    "io": smooth01,
    "out": lambda u: 1.0 - (1.0 - u) ** 2.2,
    "in": lambda u: u ** 2.2,
    "lin": lambda u: u,
    "hold": lambda u: 1.0 if u >= 1.0 else 0.0,
}

Key = Tuple[float, Semantic]


def resolve(base: Semantic, keys: Sequence[Key]) -> List[Tuple[float, Semantic]]:
    """Each key with everything it does not say carried forward."""
    out = []
    cur = dict(base)
    for t, k in keys:
        cur = {**cur, **{n: v for n, v in k.items() if n != "ease"}}
        cur["ease"] = k.get("ease", "io")
        out.append((t, dict(cur)))
    return out


def lerp_pose(body: Body, a: Semantic, b: Semantic, u: float) -> Semantic:
    out: Semantic = {}
    for name in set(a) | set(b):
        if name == "ease":
            continue
        va, vb = a.get(name, b.get(name)), b.get(name, a.get(name))
        if isinstance(va, str) or isinstance(vb, str):
            out[name] = vb if u >= 1.0 else va
        elif isinstance(va, tuple):
            out[name] = va  # feet are blended below, once the body is known
        else:
            out[name] = float(va) + (float(vb) - float(va)) * u  # type: ignore[arg-type]
    for side in SIDES:
        n = f"{side[0]}f"
        fa, fb = a.get(n), b.get(n)
        if fa is None or fb is None:
            out[n] = fa or fb
            continue
        if fa[0] == fb[0]:  # type: ignore[index]
            out[n] = (fa[0],) + tuple(float(p) + (float(q) - float(p)) * u  # type: ignore[index]
                                      for p, q in zip(fa[1:], fb[1:]))  # type: ignore[index]
        else:
            # Mixed modes blend in the world, each measured on this frame's body.
            wa = body.foot_world({**out, n: fa}, side)
            wb = body.foot_world({**out, n: fb}, side)
            out[n] = ("g",) + tuple(p + (q - p) * u for p, q in zip(wa, wb))
    return out


def at(body: Body, base: Semantic, keys: Sequence[Key], t: float) -> Semantic:
    """The pose at clip time ``t`` (keys sorted by time, in [0, 1])."""
    res = resolve(base, keys)
    if t <= res[0][0]:
        return {k: v for k, v in res[0][1].items() if k != "ease"}
    for (t0, a), (t1, b) in zip(res, res[1:]):
        if t <= t1:
            u = 0.0 if t1 <= t0 else (t - t0) / (t1 - t0)
            return lerp_pose(body, a, b, EASES[str(b["ease"])](u))
    return {k: v for k, v in res[-1][1].items() if k != "ease"}


def keyed(body: Body, base: Semantic, keys: Sequence[Key],
          extra: Callable[[float, Semantic], None] | None = None) -> Callable[[int, int, float], Pose]:
    """A clip function from key poses (``extra`` may adjust each frame's pose)."""

    def fn(i: int, n: int, t: float) -> Pose:
        pose = at(body, base, keys, t)
        if extra is not None:
            extra(t, pose)
        return body.channels(pose)

    return fn
