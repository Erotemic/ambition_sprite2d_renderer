"""Inspect and author one clip's sword arc without rebuilding the whole sheet.

Publishing a sheet renders all 136 clips; checking one attack does not need
that. ``preview`` renders a single clip straight from ``RigDocument.render_at``
and draws the swept blade trail over it, so a swing can be judged in seconds.

``describe`` reports the SWORD'S WORLD ANGLE per frame, which is the quantity an
animator actually reasons about ("the blade sweeps up from 128 to 233"). The
stored channels are per-bone deltas from the SVG rest pose, so that angle is not
readable from the clip JSON directly.

``set-arc`` is the inverse: given the angle you want the blade to hold on each
frame, it searches the shoulder channel (with the elbow profile you supply) for
the pose that produces it. The search is a dense scan rather than a root find
because the angle wraps -- a sign-based bisection converges on the solution
pointing 180 degrees the wrong way.

Angles are screen-space degrees: 0 = east, 90 = down, 180 = west, 270 = up.
This character faces west, so a rising forward slash runs ~130 -> ~230.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

LIB = Path("ambition_sprite2d_renderer/data/motion/humanoid/fighting_polygon_v1")
# The effect itself lives in `authoring`, not here, because the PUBLISHER needs
# it too — see `swing_effects`. Re-exported so this tool's own vocabulary is
# unchanged.
from ..authoring.swing_effects import (  # noqa: F401
    BLADE_LUM,
    HITBOX,
    POKE_BODY,
    POKE_CORE,
    SMASH_TRAIL_BODY,
    SMASH_TRAIL_CORE,
    TRAIL_BODY,
    TRAIL_CORE,
    blade_axis,
    body_extent,
    composite_authored_effect,
    draw_ground,
    draw_hitboxes,
    draw_poke,
    draw_trail,
    ground_y,
    hit_polygon,
    hit_windows,
    poke_polygon,
    volume_polygon,
    window_start,
)
from ..authoring.swing_effects import BG  # noqa: F401


def _target():
    from ambition_sprite2d_renderer.targets.characters import pointed_polygon as pp
    return pp


def _fresh():
    """Drop the memoised rig so an edited clip is re-read."""
    pp = _target()
    pp._prepared.cache_clear()
    pp._doc.cache_clear()
    return pp


def _frame_norm(clip, idx: int) -> float:
    return round((idx * clip.frame_duration_ms / 1000.0) / max(clip.duration_s, 1e-9), 9)


def sword_angle(clip_name: str, idx: int) -> float:
    pp = _fresh()
    doc = pp._doc()
    clip = pp._prepared().library.clips[clip_name]
    world, _ = doc.solve(clip_name, _frame_norm(clip, idx))
    return world["near_arm_hand"].angle % 360.0


def _clip_path(name: str) -> Path:
    return LIB / "clips" / f"{name}.clip.json"


def write_arm(clip_name: str, idx: int, upper: float, lower: float,
              torso: float | None = None, shift=None) -> None:
    """Set the near shoulder/elbow (and optionally the torso) on one frame.

    The torso is the arms' PARENT, so leaning it rotates the whole chain. Some
    reach simply is not available from the shoulder alone -- a rear-side strike
    needs the body to come with it -- and this is the only pivot the side-view
    rig has. A real turn-under would need a torso-twist sprite that does not
    exist yet; see the TODO on attack_up.
    """
    path = _clip_path(clip_name)
    doc = json.loads(path.read_text())
    key = doc["pose_keys"][idx]
    if "pose" in key:
        pose_path = LIB / "poses" / f"{key['pose'].replace('/', '__')}.pose.json"
        state = json.loads(pose_path.read_text())
        bones = state["state"].setdefault("bones", {})
        bones.setdefault("near_arm_u", {})["rotation_deg"] = round(upper, 4)
        bones.setdefault("near_arm_l", {})["rotation_deg"] = round(lower, 4)
        if torso is not None:
            bones.setdefault("torso", {})["rotation_deg"] = round(torso, 4)
        if shift is not None:
            bones.setdefault("torso", {})["position"] = [round(shift[0], 4), round(shift[1], 4)]
        pose_path.write_text(json.dumps(state, indent=2) + "\n")
    else:
        bones = key["state"].setdefault("bones", {})
        bones.setdefault("near_arm_u", {})["rotation_deg"] = round(upper, 4)
        bones.setdefault("near_arm_l", {})["rotation_deg"] = round(lower, 4)
        if torso is not None:
            bones.setdefault("torso", {})["rotation_deg"] = round(torso, 4)
        if shift is not None:
            bones.setdefault("torso", {})["position"] = [round(shift[0], 4), round(shift[1], 4)]
        path.write_text(json.dumps(doc, indent=2) + "\n")


def _state_for(clip_name: str, idx: int):
    """(mutable pose state, save callback) for one frame.

    A frame is either an inline state in the clip or a reference to a shared
    pose file, and every writer needs the same two-case unwrap.
    """
    path = _clip_path(clip_name)
    doc = json.loads(path.read_text())
    key = doc["pose_keys"][idx]
    if "pose" in key:
        pose_path = LIB / "poses" / f"{key['pose'].replace('/', '__')}.pose.json"
        state = json.loads(pose_path.read_text())
        return state["state"], lambda: pose_path.write_text(json.dumps(state, indent=2) + "\n")
    return key["state"], lambda: path.write_text(json.dumps(doc, indent=2) + "\n")


def _slot(state: dict, name: str):
    """(container, key) inside a pose state for one logical channel.

    Logical names are flat so a spec can name any of them the same way:
    ``torso`` is a rotation, ``torso.x`` a translation component, ``root_y``
    the whole-rig offset. Everything downstream -- seeding, calibration,
    flushing -- then treats all three identically.
    """
    if name in ("root_x", "root_y"):
        pos = state.setdefault("root", {}).setdefault("position", [0.0, 0.0])
        return pos, 0 if name == "root_x" else 1
    bone, _, comp = name.partition(".")
    entry = state.setdefault("bones", {}).setdefault(bone, {})
    if comp:
        return entry.setdefault("position", [0.0, 0.0]), 0 if comp == "x" else 1
    return entry, "rotation_deg"


def _proj_key(name: str) -> str:
    """The projected-channel key a logical channel shows up under."""
    if name in ("root_x", "root_y"):
        return name
    bone, _, comp = name.partition(".")
    return f"bone.{bone}.{comp}" if comp else bone


def read_channel(clip_name: str, idx: int, name: str) -> float:
    state, _ = _state_for(clip_name, idx)
    container, key = _slot(state, name)
    if isinstance(key, int):
        return float(container[key])
    return float(container.get(key, 0.0))


def batch_write(clip_name: str, updates: dict) -> None:
    """Write ``{frame: {channel: value}}`` in ONE pass over the files.

    The old writers re-read and re-wrote the clip document for every single
    channel, which is most of why a solve took minutes. Grouping by file also
    keeps shared pose files consistent: several frames pointing at one pose get
    applied to the same in-memory document instead of racing through it.
    """
    path = _clip_path(clip_name)
    doc = json.loads(path.read_text())
    pose_docs: dict = {}
    clip_dirty = False
    for idx in sorted(updates):
        key = doc["pose_keys"][idx]
        if "pose" in key:
            pose_path = LIB / "poses" / f"{key['pose'].replace('/', '__')}.pose.json"
            if pose_path not in pose_docs:
                pose_docs[pose_path] = json.loads(pose_path.read_text())
            state = pose_docs[pose_path]["state"]
        else:
            state = key["state"]
            clip_dirty = True
        for name, value in updates[idx].items():
            if value is None:
                continue
            container, slot = _slot(state, name)
            container[slot] = round(float(value), 4)
    if clip_dirty:
        path.write_text(json.dumps(doc, indent=2) + "\n")
    for pose_path, pose_doc in pose_docs.items():
        pose_path.write_text(json.dumps(pose_doc, indent=2) + "\n")


def ensure_frames(clip_name: str, count: int) -> int:
    """Grow or trim a clip to `count` frames, returning how many it had.

    The spec declares one value per frame, so it -- not the baked clip -- is the
    authority on how long an attack is. New frames copy the last pose, which is
    the right default for a hold: they read as a freeze until the spec gives
    them their own numbers.
    """
    path = _clip_path(clip_name)
    doc = json.loads(path.read_text())
    keys = doc["pose_keys"]
    before = len(keys)
    if before == count:
        return before
    step_ms = doc["sampling"]["frame_duration_ms"]
    while len(keys) < count:
        grown = json.loads(json.dumps(keys[-1]))
        if "pose" in grown:
            # A hold must be editable per frame, so it cannot keep sharing the
            # pose file the frame before it points at.
            source = LIB / "poses" / f"{grown['pose'].replace('/', '__')}.pose.json"
            grown = {"state": json.loads(source.read_text())["state"]}
        keys.append(grown)
    del keys[count:]
    for i, key in enumerate(keys):
        key["frame"] = i
        key["at_s"] = round(i * step_ms / 1000.0, 6)
    doc["sampling"]["frame_count"] = count
    doc["duration_s"] = round(count * step_ms / 1000.0, 6)
    path.write_text(json.dumps(doc, indent=2) + "\n")
    return before


class FastRig:
    """In-memory rig for searching, so a sample costs 0.1ms instead of 200ms.

    Profiling the old loop: one objective evaluation took 205 ms, of which
    `doc.solve` -- the actual maths -- was 0.13 ms. The other 99.9% was
    rewriting a JSON file and reloading all 136 clips to read one number back.
    No optimiser can fix an objective that expensive, so the fix is here rather
    than in the search: build the projection ONCE and patch its channel keys.

    Channel values are not the numbers stored in the pose files -- the
    projection mirrors and offsets them for a west-facing rig -- so the map is
    MEASURED per channel (two writes, once) rather than assumed.

    A channel only exists in the projection if the clip authors it, so a rig is
    built AFTER `seed`, and `set` raises rather than silently doing nothing --
    a no-op write reads as "the solver could not reach that angle".
    """

    def __init__(self, clip_name: str):
        pp = _fresh()
        self.clip_name = clip_name
        self.doc = pp._doc()
        self.clip = pp._prepared().library.clips[clip_name]
        self.channels = self.doc.clips[clip_name]["channels"]
        self._map: dict[str, tuple[float, float]] = {}
        self.dirty: dict[int, dict[str, float]] = {}

    @staticmethod
    def seed(clip_name: str, updates: dict) -> "FastRig":
        """Write starting values for every channel a solve will touch, then build.

        Seeding is what makes the in-memory path total: an unauthored channel is
        absent from the projection, so without this a spec naming a new bone
        would search a control that does not exist.

        A channel that is identically zero on EVERY frame is elided from the
        projection as well, which bites translations specifically: seeding a
        shoulder offset with its resting 0.0 leaves the solver with no control
        to move, and `set` then raises rather than pretending. So force those
        non-zero to materialise the keys, then queue the intended value for the
        flush -- if it really is zero everywhere the channel simply drops out
        again on the next load, which is what a zero offset means anyway.
        """
        batch_write(clip_name, updates)
        rig = FastRig(clip_name)
        missing = sorted({name for row in updates.values() for name in row
                          if rig._keys(name) is None})
        if missing:
            batch_write(clip_name, {idx: {name: 1.0 for name in missing} for idx in updates})
            rig = FastRig(clip_name)
            for idx, row in updates.items():
                for name in missing:
                    rig.write(name, idx, row.get(name, 0.0))
        return rig

    def _keys(self, name: str):
        entry = self.channels.get(_proj_key(name))
        return entry["keys"] if entry and "keys" in entry else None

    def set(self, name: str, idx: int, projected: float) -> None:
        keys = self._keys(name)
        if keys is None or idx >= len(keys):
            raise KeyError(f"{self.clip_name}: channel {name!r} frame {idx} is not authored; seed it first")
        keys[idx][1] = float(projected)

    def get(self, name: str, idx: int) -> float:
        keys = self._keys(name)
        return float(keys[idx][1]) if keys is not None and idx < len(keys) else 0.0

    def calibrate(self, name: str, idx: int) -> tuple[float, float]:
        """projected = a * stored + b, measured with two real writes."""
        if name in self._map:
            return self._map[name]
        before = read_channel(self.clip_name, idx, name)
        samples = []
        for probe in (0.0, 100.0):
            batch_write(self.clip_name, {idx: {name: probe}})
            fresh = _fresh()
            samples.append(fresh._doc().clips[self.clip_name]["channels"][_proj_key(name)]["keys"][idx][1])
        batch_write(self.clip_name, {idx: {name: before}})
        a = (samples[1] - samples[0]) / 100.0
        self._map[name] = (a, samples[0])
        return self._map[name]

    def to_projected(self, name: str, idx: int, stored: float) -> float:
        a, b = self.calibrate(name, idx)
        return a * stored + b

    def to_stored(self, name: str, idx: int, projected: float) -> float:
        a, b = self.calibrate(name, idx)
        return (projected - b) / a if a else 0.0

    def write(self, name: str, idx: int, stored: float) -> None:
        """Set a channel by its STORED value and remember it for the flush."""
        self.set(name, idx, self.to_projected(name, idx, stored))
        self.dirty.setdefault(idx, {})[name] = stored

    def flush(self) -> None:
        """Persist everything `write` recorded, in one pass."""
        if self.dirty:
            batch_write(self.clip_name, self.dirty)
            self.dirty = {}

    def _norm(self, idx: int) -> float:
        return _frame_norm(self.clip, idx)

    def _world(self, idx: int):
        world, _ = self.doc.solve(self.clip_name, self._norm(idx))
        return world

    def sword_angle(self, idx: int) -> float:
        return self._world(idx)["near_arm_hand"].angle % 360.0

    def grip_vector(self, idx: int):
        world = self._world(idx)
        far = world["far_arm_hand"].origin
        near = world["near_arm_hand"].origin
        return (near[0] - far[0], near[1] - far[1])

    def grip_gap(self, idx: int) -> float:
        return math.hypot(*self.grip_vector(idx))


def read_bone(clip_name: str, idx: int, bone: str) -> float:
    return read_channel(clip_name, idx, bone)


def write_bone(clip_name: str, idx: int, bone: str, value: float) -> None:
    batch_write(clip_name, {idx: {bone: value}})


def solve_grip_fast(rig: "FastRig", idx: int, coarse: float = 12.0):
    """Scan both far-arm rotations for the pose putting its hand on the hilt."""
    best = None
    for u in [i * coarse - 200.0 for i in range(int(280 / coarse) + 1)]:
        rig.write("far_arm_u", idx, u)
        for l in [i * coarse - 150.0 for i in range(int(220 / coarse) + 1)]:
            rig.write("far_arm_l", idx, l)
            gap = rig.grip_gap(idx)
            if best is None or gap < best[0]:
                best = (gap, u, l)
    gap, u, l = best
    step = coarse / 2.0
    while step > 0.25:
        for du in (-step, 0.0, step):
            for dl in (-step, 0.0, step):
                rig.write("far_arm_u", idx, u + du)
                rig.write("far_arm_l", idx, l + dl)
                got = rig.grip_gap(idx)
                if got < gap:
                    gap, u, l = got, u + du, l + dl
        step /= 2.0
    rig.write("far_arm_u", idx, u)
    rig.write("far_arm_l", idx, l)
    return u, l, gap


def close_grip_fast(rig: "FastRig", idx: int, rounds: int = 8, limit: float = 30.0):
    """Translate the far shoulder until its hand sits on the hilt.

    Rotation alone cannot always reach: once the sword goes overhead the hilt
    leaves the far arm's circle entirely, and only moving the shoulder closes it.

    `position` is a LOCAL offset, applied in the bone's parent frame, so the
    world-space gap is NOT the shift to apply -- feeding it back directly made
    the gap grow. Instead measure the map: nudge x, nudge y, read how the hand
    actually moves, and solve the resulting 2x2 system. That needs no assumption
    about the frame's orientation or scale, so it keeps working if either changes.
    """
    shift = [0.0, 0.0]
    probe = 4.0

    def place(x, y):
        rig.write("far_arm_u.x", idx, x)
        rig.write("far_arm_u.y", idx, y)
        return rig.grip_vector(idx)

    for _ in range(rounds):
        base = place(*shift)
        if math.hypot(*base) < 0.4:
            break
        gx = place(shift[0] + probe, shift[1])
        gy = place(shift[0], shift[1] + probe)
        # columns: how the gap responds to a unit of local x / local y
        a = ((gx[0] - base[0]) / probe, (gx[1] - base[1]) / probe)
        b = ((gy[0] - base[0]) / probe, (gy[1] - base[1]) / probe)
        det = a[0] * b[1] - a[1] * b[0]
        if abs(det) < 1e-9:
            break
        shift[0] += (-base[0] * b[1] + base[1] * b[0]) / det
        shift[1] += (-base[1] * a[0] + base[0] * a[1]) / det
        length = math.hypot(*shift)
        if length > limit:
            shift[0] *= limit / length
            shift[1] *= limit / length
            place(*shift)
            break
    place(*shift)
    return tuple(shift), rig.grip_gap(idx)

def solve_frame_fast(rig: "FastRig", idx: int, lower: float, target: float,
                     lo: float = -260.0, hi: float = 200.0, coarse: float = 1.0,
                     torso: float | None = None, shift=None):
    """Scan the shoulder for the angle closest to `target`, entirely in memory.

    The range is deliberately wider than a shoulder plausibly bends. A narrow
    window silently reports "out of reach" when the scan simply saturated at its
    own bound -- which it did, at +70, and read as an anatomy limit.

    Note `shift` cannot help a target: translating the torso moves where the
    blade IS, never which way it POINTS. Only rotations change the angle.
    """
    rig.write("near_arm_l", idx, lower)
    if torso is not None:
        rig.write("torso", idx, torso)
    if shift is not None:
        rig.write("torso.x", idx, shift[0])
        rig.write("torso.y", idx, shift[1])
    best = None
    steps = int((hi - lo) / coarse) + 1
    for k in range(steps):
        stored = lo + k * coarse
        rig.write("near_arm_u", idx, stored)
        got = rig.sword_angle(idx)
        err = abs((got - target + 180.0) % 360.0 - 180.0)
        if best is None or err < best[0]:
            best = (err, stored, got)
    err, stored, got = best
    step = coarse / 2.0
    while step > 0.02:
        for delta in (-step, step):
            rig.write("near_arm_u", idx, stored + delta)
            got2 = rig.sword_angle(idx)
            err2 = abs((got2 - target + 180.0) % 360.0 - 180.0)
            if err2 < err:
                err, stored, got = err2, stored + delta, got2
        step /= 2.0
    rig.write("near_arm_u", idx, stored)
    return stored, got, err


def solve_frame(clip_name: str, idx: int, lower: float, target: float,
                lo: float = -260.0, hi: float = 200.0, coarse: float = 2.0,
                torso: float | None = None, shift=None):
    """Scan the shoulder channel for the angle closest to `target`.

    The range is deliberately wider than a shoulder plausibly bends. A narrow
    window silently reports "out of reach" when the scan simply saturated at its
    own bound -- which it did, at +70, and read as an anatomy limit.

    Note `shift` cannot help a target: translating the torso moves where the
    blade IS, never which way it POINTS. Only rotations change the angle.
    """
    best = None
    steps = int((hi - lo) / coarse) + 1
    for k in range(steps):
        upper = lo + k * coarse
        write_arm(clip_name, idx, upper, lower, torso, shift)
        got = sword_angle(clip_name, idx)
        err = abs((got - target + 180.0) % 360.0 - 180.0)
        if best is None or err < best[0]:
            best = (err, upper, got)
    err, upper, got = best
    for delta in (-1.5, -1.0, -0.5, 0.5, 1.0, 1.5):
        write_arm(clip_name, idx, upper + delta, lower, torso, shift)
        got2 = sword_angle(clip_name, idx)
        err2 = abs((got2 - target + 180.0) % 360.0 - 180.0)
        if err2 < err:
            err, upper, got = err2, upper + delta, got2
    write_arm(clip_name, idx, upper, lower, torso, shift)
    return upper, got, err


def write_far(clip_name: str, idx: int, upper: float, lower: float, shift=None) -> None:
    """Pose the FAR arm on one frame, optionally translating its shoulder."""
    path = _clip_path(clip_name)
    doc = json.loads(path.read_text())
    key = doc["pose_keys"][idx]
    if "pose" in key:
        pose_path = LIB / "poses" / f"{key['pose'].replace('/', '__')}.pose.json"
        state = json.loads(pose_path.read_text())
        bones = state["state"].setdefault("bones", {})
        target, writer = bones, lambda: pose_path.write_text(json.dumps(state, indent=2) + "\n")
    else:
        bones = key["state"].setdefault("bones", {})
        target, writer = bones, lambda: path.write_text(json.dumps(doc, indent=2) + "\n")
    target.setdefault("far_arm_u", {})["rotation_deg"] = round(upper, 4)
    target.setdefault("far_arm_l", {})["rotation_deg"] = round(lower, 4)
    if shift is not None:
        target.setdefault("far_arm_u", {})["position"] = [round(shift[0], 4), round(shift[1], 4)]
    writer()


def grip_gap(clip_name: str, idx: int) -> float:
    """Distance from the far hand to the near hand, i.e. to the hilt.

    A two-handed grip is the far hand ARRIVING at the sword, which is a position
    goal, not an angle one -- so it is solved against this distance rather than
    with `set-arc`.
    """
    pp = _fresh()
    doc = pp._doc()
    clip = pp._prepared().library.clips[clip_name]
    world, _ = doc.solve(clip_name, _frame_norm(clip, idx))
    far = world["far_arm_hand"].origin
    near = world["near_arm_hand"].origin
    return math.hypot(far[0] - near[0], far[1] - near[1])


def grip_vector(clip_name: str, idx: int):
    """Vector from the far hand to the hilt, in world units."""
    pp = _fresh()
    doc = pp._doc()
    clip = pp._prepared().library.clips[clip_name]
    world, _ = doc.solve(clip_name, _frame_norm(clip, idx))
    far = world["far_arm_hand"].origin
    near = world["near_arm_hand"].origin
    return (near[0] - far[0], near[1] - far[1])


def close_grip_by_shift(clip_name: str, idx: int, upper: float, lower: float,
                        rounds: int = 8, limit: float = 30.0):
    """Translate the far shoulder until its hand sits on the hilt.

    Rotation alone cannot always reach: once the sword goes overhead the hilt
    leaves the far arm's circle entirely, and only moving the shoulder closes it.

    `position` is a LOCAL offset, applied in the bone's parent frame, so the
    world-space gap is NOT the shift to apply -- feeding it back directly made
    the gap grow. Instead measure the map: nudge x, nudge y, read how the hand
    actually moves, and solve the resulting 2x2 system. That needs no assumption
    about the frame's orientation or scale, so it keeps working if either
    changes.
    """
    shift = [0.0, 0.0]
    probe = 4.0
    for _ in range(rounds):
        write_far(clip_name, idx, upper, lower, tuple(shift))
        gap = grip_vector(clip_name, idx)
        if math.hypot(*gap) < 0.4:
            break
        base = grip_vector(clip_name, idx)
        write_far(clip_name, idx, upper, lower, (shift[0] + probe, shift[1]))
        gx = grip_vector(clip_name, idx)
        write_far(clip_name, idx, upper, lower, (shift[0], shift[1] + probe))
        gy = grip_vector(clip_name, idx)
        # columns: how the gap responds to a unit of local x / local y
        a = ((gx[0] - base[0]) / probe, (gx[1] - base[1]) / probe)
        b = ((gy[0] - base[0]) / probe, (gy[1] - base[1]) / probe)
        det = a[0] * b[1] - a[1] * b[0]
        if abs(det) < 1e-9:
            break
        # solve [a b] * step = -base   (drive the gap to zero)
        step_x = (-base[0] * b[1] + base[1] * b[0]) / det
        step_y = (-base[1] * a[0] + base[0] * a[1]) / det
        shift[0] += step_x
        shift[1] += step_y
        length = math.hypot(*shift)
        if length > limit:
            shift[0] *= limit / length
            shift[1] *= limit / length
            break
    write_far(clip_name, idx, upper, lower, tuple(shift))
    return tuple(shift), grip_gap(clip_name, idx)


def solve_grip(clip_name: str, idx: int, coarse: float = 12.0, shift=None):
    """Scan both far-arm channels for the pose that puts its hand on the hilt."""
    best = None
    for u in [i * coarse - 200.0 for i in range(int(280 / coarse) + 1)]:
        for l in [i * coarse - 150.0 for i in range(int(220 / coarse) + 1)]:
            write_far(clip_name, idx, u, l, shift)
            gap = grip_gap(clip_name, idx)
            if best is None or gap < best[0]:
                best = (gap, u, l)
    gap, u, l = best
    step = coarse / 2.0
    while step > 0.4:
        for du in (-step, 0.0, step):
            for dl in (-step, 0.0, step):
                write_far(clip_name, idx, u + du, l + dl, shift)
                got = grip_gap(clip_name, idx)
                if got < gap:
                    gap, u, l = got, u + du, l + dl
        step /= 2.0
    write_far(clip_name, idx, u, l, shift)
    return u, l, gap


# Which bone rotation moves a joint up or down, once the root has been placed.
GROUND_DRIVER = {
    "near_leg_foot": "near_leg_l",
    "far_leg_foot": "far_leg_l",
    "near_leg_l": "near_leg_u",
    "far_leg_l": "far_leg_u",
}


def ground_world(rig: "FastRig") -> float:
    """Floor height in RIG space: where the feet rest in the neutral frame.

    The rig's contact points are joints, not soles, so this is the height a
    joint sits at when it is standing on the floor -- which is exactly the
    quantity a contact goal wants to match, and keeps the measure independent
    of how much foot art hangs below the ankle.
    """
    world = rig._world(0)
    return max(world["near_leg_foot"].origin[1], world["far_leg_foot"].origin[1])


def solve_ground_contacts(rig: "FastRig", idx: int, joints, ground: float,
                          lo: float = -220.0, hi: float = 320.0, coarse: float = 4.0):
    """Put the named joints ON the floor: root first, then one bone per joint.

    A kneel is not a deeper crouch. Rotating the thigh cannot lower the knee --
    the knee is furthest down when the thigh hangs straight, so folding harder
    RAISES it, which is what a hand-tuned attempt produced. Only dropping the
    pelvis brings a knee to the floor, so the first joint is solved with the
    root and every later one with the bone above it.

    A contact goal has more than one answer -- a foot reaches the floor with the
    leg folded under OR straight out -- so ties break toward the value the frame
    already had. Without that, one frame of a three-frame hold picked the other
    branch and the leg snapped straight for a sixtieth of a second.
    """
    results = []
    for n, joint in enumerate(joints):
        channel = "root_y" if n == 0 else GROUND_DRIVER.get(joint)
        if channel is None:
            raise SystemExit(f"no ground driver known for joint {joint!r}")
        start = rig.to_stored(channel, idx, rig.get(channel, idx))

        def error(value):
            rig.write(channel, idx, value)
            return abs(rig._world(idx)[joint].origin[1] - ground)

        # Refine EVERY local minimum, not just the best coarse sample. The scan
        # grid straddles a branch's zero crossing as often as it lands on it, so
        # comparing raw coarse errors picks the branch by luck: one frame of a
        # hold flipped to the other leg pose because its grid point happened to
        # sit 0.7px nearer the floor.
        steps = int((hi - lo) / coarse) + 1
        samples = [(lo + k * coarse, error(lo + k * coarse)) for k in range(steps)]
        minima = [i for i in range(len(samples))
                  if (i == 0 or samples[i][1] <= samples[i - 1][1])
                  and (i == len(samples) - 1 or samples[i][1] <= samples[i + 1][1])]
        candidates = []
        for i in minima:
            value, err = samples[i]
            step = coarse / 2.0
            while step > 0.05:
                for delta in (-step, step):
                    err2 = error(value + delta)
                    if err2 < err:
                        err, value = err2, value + delta
                step /= 2.0
            candidates.append((err, value))
        err, value = min(candidates, key=lambda c: (round(c[0] / 1.0), abs(c[1] - start)))
        rig.write(channel, idx, value)
        results.append((joint, channel, value, err))
    return results



def render_clip(clip_name: str):
    pp = _fresh()
    clip = pp._prepared().library.clips[clip_name]
    return [pp._render_frame(clip_name, i, clip.frame_count) for i in range(clip.frame_count)], clip


def cmd_describe(args):
    pp = _fresh()
    clip = pp._prepared().library.clips[args.clip]
    raw = json.loads(_clip_path(args.clip).read_text())
    print(f"{args.clip}: {clip.frame_count}f @ {clip.frame_duration_ms}ms  loop={raw['loop']}")
    print("  f   sword_deg   shoulder    elbow   source")
    for i in range(clip.frame_count):
        key = raw["pose_keys"][i]
        if "pose" in key:
            state = json.loads((LIB / "poses" / f"{key['pose'].replace('/', '__')}.pose.json").read_text())["state"]
            src = key["pose"].split("/")[-1]
        else:
            state = key["state"]
            src = "inline"
        bones = state.get("bones", {})
        up = bones.get("near_arm_u", {}).get("rotation_deg", 0.0)
        lo = bones.get("near_arm_l", {}).get("rotation_deg", 0.0)
        print(f"  {i}  {sword_angle(args.clip, i):9.1f} {up:10.1f} {lo:8.1f}   {src}")


def cmd_set_arc(args):
    angles = [float(v) for v in args.angles.split(",")]
    elbows = [float(v) for v in args.elbows.split(",")]
    if len(angles) != len(elbows):
        raise SystemExit("--angles and --elbows must have the same length")
    torsos = [float(v) for v in args.torso.split(",")] if args.torso else [None] * len(angles)
    shifts = ([tuple(float(c) for c in pair.split(":")) for pair in args.torso_shift.split(",")]
              if args.torso_shift else [None] * len(angles))
    if len(shifts) != len(angles):
        raise SystemExit("--torso-shift must have the same length as --angles")
    if len(torsos) != len(angles):
        raise SystemExit("--torso must have the same length as --angles")
    print("  f   elbow   torso   shoulder     got   target    err")
    for i, (target, elbow) in enumerate(zip(angles, elbows)):
        upper, got, err = solve_frame(args.clip, i, elbow, target, torso=torsos[i], shift=shifts[i])
        flag = "" if err < 2.0 else "   <== out of reach; lean the torso"
        tor = "  -  " if torsos[i] is None else f"{torsos[i]:5.1f}"
        print(f"  {i} {elbow:7.1f} {tor} {upper:10.2f} {got:7.1f} {target:8.1f} {err:6.1f}{flag}")


def cmd_grip(args):
    shift = tuple(float(c) for c in args.shift.split(":")) if args.shift else None
    print("  f   far_shoulder   far_elbow    gap(px)")
    for i in [int(v) for v in args.frames.split(",")]:
        u, l, gap = solve_grip(args.clip, i, shift=shift)
        note = ""
        if args.auto_shift and gap >= 1.0:
            moved, gap = close_grip_by_shift(args.clip, i, u, l)
            note = f"   shoulder moved ({moved[0]:+.1f},{moved[1]:+.1f})"
        flag = "" if gap < 3.0 else "   <== still short"
        print(f"  {i} {u:12.1f} {l:11.1f} {gap:10.2f}{note}{flag}")


def save_preview(images, clip, clip_name: str, out: Path, scale: int = 2) -> None:
    """One writer for the GIF + frame strip, shared by `preview` and the spec tool."""
    out.parent.mkdir(parents=True, exist_ok=True)
    big = [im.resize((im.width * scale, im.height * scale), Image.NEAREST) for im in images]
    big[0].convert("P", palette=Image.ADAPTIVE, colors=255).save(
        out.with_suffix(".gif"), save_all=True,
        append_images=[b.convert("P", palette=Image.ADAPTIVE, colors=255) for b in big[1:]],
        duration=clip.frame_duration_ms, loop=0, disposal=2,
    )
    w, h = big[0].size
    strip = Image.new("RGBA", (w * len(big) + 150, h), BG)
    for i, im in enumerate(big):
        strip.paste(im, (150 + i * w, 0), im)
    draw = ImageDraw.Draw(strip)
    draw.text((8, h // 2 - 14), clip_name, fill=(235, 235, 240, 255))
    draw.text((8, h // 2 + 2), f"{clip.frame_count}f @ {clip.frame_duration_ms}ms",
              fill=(150, 150, 160, 255))
    strip.save(out.with_suffix(".png"))


def cmd_preview(args):
    raw, clip = render_clip(args.clip)
    images = raw if args.no_trail else draw_trail(raw)
    if args.hitbox:
        active = {int(v) for v in args.active.split(",")} if args.active else None
        images = draw_hitboxes(images, reach=args.reach, linger=args.linger, active=active)
    if not args.no_ground:
        images = draw_ground(images, ground_y(raw))
    out = Path(args.out)
    save_preview(images, clip, args.clip, out, scale=args.scale)
    print(f"wrote {out.with_suffix('.gif')} and {out.with_suffix('.png')}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("describe", help="per-frame sword angle and arm channels")
    d.add_argument("clip")
    d.set_defaults(func=cmd_describe)
    s = sub.add_parser("set-arc", help="solve arm poses for target sword angles")
    s.add_argument("clip")
    s.add_argument("--angles", required=True, help="comma-separated sword angles, one per frame")
    s.add_argument("--elbows", required=True, help="comma-separated elbow deltas, one per frame")
    s.add_argument("--torso", help="comma-separated torso leans, one per frame; the arms' parent, "
                                   "so this buys reach the shoulder alone cannot")
    s.add_argument("--torso-shift", dest="torso_shift",
                   help="comma-separated dx:dy torso translations, one per frame; leans the whole "
                        "upper body OUT over a strike for reach a rotation cannot give")
    s.set_defaults(func=cmd_set_arc)
    g = sub.add_parser("grip", help="place the FAR hand on the hilt (two-handed grip)")
    g.add_argument("clip")
    g.add_argument("--frames", required=True, help="comma-separated frames to grip")
    g.add_argument("--shift", help="dx:dy translation of the far shoulder, applied to every gripped frame")
    g.add_argument("--auto-shift", dest="auto_shift", action="store_true",
                   help="translate the far shoulder until its hand reaches the hilt")
    g.set_defaults(func=cmd_grip)
    p = sub.add_parser("preview", help="render ONE clip with the blade trail")
    p.add_argument("clip")
    p.add_argument("--out", required=True)
    p.add_argument("--scale", type=int, default=2)
    p.add_argument("--no-trail", action="store_true")
    p.add_argument("--no-ground", action="store_true",
                   help="omit the floor rule taken from the clip's neutral frame")
    p.add_argument("--hitbox", action="store_true",
                   help="overlay the blade's swept quad as a proposed hit volume")
    p.add_argument("--reach", type=float, default=1.0,
                   help="fraction of the blade the hit volume covers (1.0 = to the tip)")
    p.add_argument("--linger", type=int, default=3,
                   help="how many frames of blade travel the hit volume accumulates")
    p.add_argument("--active", help="comma-separated frames that actually connect; "
                                    "omit to draw a volume on every frame")
    p.set_defaults(func=cmd_preview)
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
