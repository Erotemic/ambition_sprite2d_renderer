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
BLADE_LUM = 560          # summed RGB; nothing on the body reaches this
# A tilt and a smash must be told apart at a glance, and size alone does not do
# it once both are moving -- so the two read as different HEAT as well. Both stay
# in the fighter's purple; the smash burns hotter and whiter at the core.
TRAIL_BODY = (140, 86, 220)          # tilt: deeper, cooler violet
TRAIL_CORE = (212, 182, 250)
SMASH_TRAIL_BODY = (202, 92, 248)    # smash: hotter magenta-violet
SMASH_TRAIL_CORE = (255, 238, 255)
HITBOX = (255, 96, 96)
BG = (30, 26, 32, 255)


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


def blade_axis(image: Image.Image):
    """(base, tip) of the blade in image space, base being the end nearer the body."""
    px = image.load()
    blade, body = [], []
    for y in range(image.height):
        for x in range(image.width):
            pixel = px[x, y]
            if pixel[3] < 40:
                continue
            body.append((x, y))
            if sum(pixel[:3]) > BLADE_LUM:
                blade.append((x, y))
    if len(blade) < 6 or not body:
        return None
    n = len(blade)
    cx = sum(p[0] for p in blade) / n
    cy = sum(p[1] for p in blade) / n
    sxx = syy = sxy = 0.0
    for x, y in blade:
        dx, dy = x - cx, y - cy
        sxx += dx * dx
        syy += dy * dy
        sxy += dx * dy
    theta = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ux, uy = math.cos(theta), math.sin(theta)
    projected = [(((x - cx) * ux + (y - cy) * uy), (x, y)) for x, y in blade]
    lo = min(projected)[1]
    hi = max(projected)[1]
    bx = sum(p[0] for p in body) / len(body)
    by = sum(p[1] for p in body) / len(body)
    near = lambda p: math.hypot(p[0] - bx, p[1] - by)
    return (lo, hi) if near(lo) < near(hi) else (hi, lo)


def body_extent(image: Image.Image):
    """(centre x, centre y, lowest y) of the FIGURE, blade excluded.

    Measured on a RAW frame only: the trail's core is brighter than BLADE_LUM,
    so running this after `draw_trail` would count the ribbon as anatomy.
    """
    px = image.load()
    xs, ys, lowest = [], [], 0
    for y in range(image.height):
        for x in range(image.width):
            pixel = px[x, y]
            if pixel[3] < 40 or sum(pixel[:3]) > BLADE_LUM:
                continue
            xs.append(x)
            ys.append(y)
            lowest = max(lowest, y)
    if not xs:
        return None
    return sum(xs) / len(xs), sum(ys) / len(ys), lowest


def ground_y(images) -> float:
    """Floor level: where the fighter's feet are in her NEUTRAL frame.

    A kneel or a blade driven "all the way to the ground" is a claim about a
    height, and a preview with nothing at that height cannot show whether the
    claim holds -- which is why this ships alongside the rule that checks it.
    """
    extent = body_extent(images[0])
    return float(extent[2]) if extent else float(images[0].height - 1)


def draw_ground(images, y: float, colour=(122, 112, 134)):
    """Overlay the floor rule on every frame, so the GIF carries it too."""
    out = []
    for base in images:
        comp = base.copy()
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).line([(0, y), (base.width, y)], fill=colour + (90,), width=1)
        comp.alpha_composite(layer)
        out.append(comp)
    return out


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def draw_trail(images, window: int = 3, subdiv: int = 5, inner: float = 0.58,
               alpha: int = 120, blur: float = 0.8, core_alpha: int = 150, active=None,
               body_rgb=None, core_rgb=None, falloff: float = 1.7, axes=None):
    """`window`/`inner`/`alpha` are what separate a tilt from a smash: a smash
    wants a longer, wider, brighter ribbon so the commitment reads.

    `falloff` is how fast a segment dims with age, and it has to move with
    `window`: stretching the window so the hit volume can grow also stretches
    the fade, and a smash ribbon lengthened without flattening the falloff just
    goes dim -- longer AND fainter, which is the opposite of grander.

    `active` is the SAME frame set the hit volume uses, and that is the point:
    the ribbon and the hitbox describe one swing, so a charge frame that cannot
    hurt anyone must not sweep light either. Segments keep fading for `window`
    frames afterwards, so a recovery still trails off instead of snapping dark.
    """
    live = None if active is None else set(active)
    body_rgb = tuple(body_rgb) if body_rgb else TRAIL_BODY
    core_rgb = tuple(core_rgb) if core_rgb else TRAIL_CORE
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    out = []
    for i, base in enumerate(images):
        trail = Image.new("RGBA", base.size, (0, 0, 0, 0))
        for k in range(window, 0, -1):
            j0, j1 = i - k, i - k + 1
            if j0 < 0 or j1 >= len(images) or axes[j0] is None or axes[j1] is None:
                continue
            if live is not None and (j0 not in live or j1 not in live):
                continue
            for s in range(subdiv):
                t0, t1 = s / subdiv, (s + 1) / subdiv
                age = ((k - 1) + (1 - t1)) / window
                a = int(alpha * (1.0 - age) ** falloff)
                if a <= 2:
                    continue
                b0 = _lerp(axes[j0][0], axes[j1][0], t0)
                p0 = _lerp(axes[j0][1], axes[j1][1], t0)
                b1 = _lerp(axes[j0][0], axes[j1][0], t1)
                p1 = _lerp(axes[j0][1], axes[j1][1], t1)
                f = inner + (1.0 - inner) * 0.55 * age
                seg = Image.new("RGBA", base.size, (0, 0, 0, 0))
                ImageDraw.Draw(seg).polygon(
                    [_lerp(b0, p0, f), p0, p1, _lerp(b1, p1, f)], fill=body_rgb + (a,)
                )
                trail.alpha_composite(seg)
        trail = trail.filter(ImageFilter.GaussianBlur(blur))
        core_live = live is None or (i in live and i - 1 in live)
        if i > 0 and core_live and axes[i] and axes[i - 1]:
            core = Image.new("RGBA", base.size, (0, 0, 0, 0))
            ImageDraw.Draw(core).polygon(
                [_lerp(axes[i - 1][0], axes[i - 1][1], 0.80), axes[i - 1][1],
                 axes[i][1], _lerp(axes[i][0], axes[i][1], 0.80)],
                fill=core_rgb + (core_alpha,),
            )
            trail.alpha_composite(core.filter(ImageFilter.GaussianBlur(0.5)))
        comp = Image.new("RGBA", base.size, BG)
        comp.alpha_composite(trail)
        comp.alpha_composite(base)
        out.append(comp)
    return out


# A poke is not a slow sweep -- it is a line. Its light runs ALONG the blade
# instead of trailing behind it, so a thrust reads as reach rather than as arc.
POKE_BODY = (150, 208, 255)
POKE_CORE = (240, 252, 255)


def poke_polygon(axes, i, extend: float = 1.30, width: float = 13.0,
                 waist: float = 0.66, inner: float = 0.10):
    """Lens along the blade axis: the volume a THRUST occupies.

    A swept ribbon says "this arc is dangerous"; a poke has no arc, and drawing
    one for it would promise a sweep the move does not have. So the shape is
    axial -- it starts near the hilt, bulges at `waist` and comes to a point
    past the tip, which is where a thrust's reach actually is.
    """
    if axes[i] is None:
        return None
    base, tip = axes[i]
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return None
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    start = _lerp(base, tip, inner)
    end = (base[0] + dx * extend, base[1] + dy * extend)
    mid = _lerp(start, end, waist)
    half = width / 2.0
    return [start, (mid[0] + nx * half, mid[1] + ny * half), end,
            (mid[0] - nx * half, mid[1] - ny * half)]


def draw_poke(images, active=None, extend: float = 1.30, width: float = 13.0,
              waist: float = 0.66, inner: float = 0.10, alpha: int = 190,
              blur: float = 1.0, core_alpha: int = 225, falloff: float = 2.2,
              window: int = 2, body_rgb=None, core_rgb=None, axes=None):
    """Draw the thrust flash, fading for `window` frames after each live one."""
    live = None if active is None else set(active)
    body_rgb = tuple(body_rgb) if body_rgb else POKE_BODY
    core_rgb = tuple(core_rgb) if core_rgb else POKE_CORE
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    out = []
    for i, base_im in enumerate(images):
        layer = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
        for k in range(window, -1, -1):
            j = i - k
            if j < 0 or (live is not None and j not in live):
                continue
            poly = poke_polygon(axes, j, extend, width, waist, inner)
            if poly is None:
                continue
            age = k / (window + 1)
            a = int(alpha * (1.0 - age) ** falloff)
            if a <= 2:
                continue
            spike = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
            ImageDraw.Draw(spike).polygon(poly, fill=body_rgb + (a,))
            layer.alpha_composite(spike)
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        if live is None or i in live:
            poly = poke_polygon(axes, i, extend, width * 0.34, waist, inner)
            if poly is not None:
                core = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
                ImageDraw.Draw(core).polygon(poly, fill=core_rgb + (core_alpha,))
                layer.alpha_composite(core.filter(ImageFilter.GaussianBlur(0.5)))
        comp = Image.new("RGBA", base_im.size, BG)
        comp.alpha_composite(layer)
        comp.alpha_composite(base_im)
        out.append(comp)
    return out


def _hull(points):
    """Convex hull (monotone chain). A hull cannot self-intersect, which the
    raw swept quad can: when the blade crosses over, base and tip swap sides
    and [b0, t0, t1, b1] draws an hourglass instead of a volume."""
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in points))
    if len(pts) < 3:
        return list(pts)
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2:
                (ax, ay), (bx, by) = out[-2], out[-1]
                if (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) > 0:
                    break
                out.pop()
            out.append(p)
        return out[:-1]
    return half(pts) + half(reversed(pts))


def hit_polygon(axes, i, reach: float = 1.0, linger: int | None = None, first: int = 0,
                extend: float = 1.0, inflate: float = 0.0):
    """Proposed hit volume for frame `i`: the hull of the blade over the last
    live frames, so the volume GROWS as the swing travels and by the end covers
    the whole ribbon rather than collapsing to one thin swept step. `linger`
    caps that window; without one the volume is everything the blade has swept
    since the move went live, which is what makes the hitbox match the trail.

    The window never reaches back before `first`, the frame the attack goes
    live. Without that clamp a smash's opening hitbox swallowed the overhead
    wind-up and so extended BEHIND the fighter -- a volume covering a position
    the blade held while the move was still inactive.

    `reach` trims the inner end so the volume covers blade rather than fist;
    `extend` pushes the outer end PAST the tip and `inflate` grows the hull
    sideways. A hitbox is not a tracing of the art -- a move that connects only
    where the sprite overlaps feels stingy -- so the generous part is declared
    rather than faked by drawing a longer sword.

    NOTE: derived from the swing, not authored data. No hitboxes exist for this
    character yet (`RigDocument`'s "hitboxes" slot is empty), so this shows the
    reach a hitbox WOULD need. The shipping path is
    `core.slash_envelope.SwingDescriptor`, which drives the hit polygon and the
    effect art off one profile so they cannot drift.
    """
    pts = []
    start = first if linger is None else max(first, i - linger + 1)
    for j in range(start, i + 1):
        if axes[j] is None:
            continue
        base, tip = axes[j]
        if extend != 1.0:
            tip = (base[0] + (tip[0] - base[0]) * extend,
                   base[1] + (tip[1] - base[1]) * extend)
        if reach != 1.0:
            base = _lerp(base, tip, 1.0 - reach)
        pts.extend([base, tip])
    if len(pts) < 3:
        return None
    hull = _hull(pts)
    if inflate > 0.0 and len(hull) >= 3:
        cx = sum(p[0] for p in hull) / len(hull)
        cy = sum(p[1] for p in hull) / len(hull)
        grown = []
        for x, y in hull:
            dx, dy = x - cx, y - cy
            length = math.hypot(dx, dy) or 1.0
            grown.append((x + dx / length * inflate, y + dy / length * inflate))
        hull = grown
    return hull


def hit_windows(hitbox: dict):
    """`active` as a list of WINDOWS, however the spec wrote it.

    A neutral air hits twice, and the second hit must not inherit the first's
    swept volume -- one accumulating hull across both would claim everything
    between them, which is precisely the space the move passes through without
    threatening. So each window starts its own volume.
    """
    active = hitbox.get("active")
    if not active:
        return []
    if isinstance(active[0], (list, tuple)):
        return [sorted(int(f) for f in window) for window in active]
    return [sorted(int(f) for f in active)]


def window_start(windows, i):
    """The frame the volume containing `i` began, or None if `i` is not live."""
    for window in windows:
        if i in window:
            return window[0]
    return None


def volume_polygon(axes, i, effect: str, first: int, swept: dict, poke: dict):
    """The hit volume for frame `i`, in the shape of whatever effect it draws.

    One function so the promise and the hit stay the same object: a swept effect
    hits along its ribbon, a thrust hits along its lance. Nothing gets to hit in
    a shape the player was never shown.
    """
    if effect == "poke":
        return poke_polygon(axes, i, poke.get("extend", 1.30), poke.get("width", 13.0),
                            poke.get("waist", 0.66), poke.get("inner", 0.10))
    return hit_polygon(axes, i, swept.get("reach", 1.0), swept.get("linger"),
                       first, swept.get("extend", 1.0), swept.get("inflate", 0.0))


def draw_hitboxes(images, reach: float = 1.0, linger: int | None = None, windows=None,
                  extend: float = 1.0, inflate: float = 0.0, effect: str = "trail",
                  poke=None, axes=None):
    """`active` limits the overlay to the frames that actually connect.

    A swing is only dangerous for part of its travel; drawing a volume on the
    wind-up and the recovery makes an attack look far more threatening than it
    is, which is the opposite of what a review image is for.
    """
    # Measured on the RAW frames when the caller supplies them, and it must be:
    # every effect draws light brighter than BLADE_LUM, so re-measuring here
    # reads the flash as part of the sword and drags a hitbox vertex with it.
    axes = axes if axes is not None else [blade_axis(im) for im in images]
    windows = windows or []
    out = []
    for i, base in enumerate(images):
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        first = window_start(windows, i)
        poly = (None if first is None
                else volume_polygon(axes, i, effect, first,
                                    dict(reach=reach, linger=linger, extend=extend,
                                         inflate=inflate), poke or {}))
        if poly is not None and len(poly) >= 3:
            draw = ImageDraw.Draw(layer)
            # Light enough that the ribbon's own colour still reads through it --
            # the overlay is a measurement, and it should not repaint the thing
            # being measured. The outline carries the shape.
            draw.polygon(poly, fill=HITBOX + (26,))
            draw.line(list(poly) + [poly[0]], fill=HITBOX + (210,), width=1)
        comp = base.copy()
        comp.alpha_composite(layer)
        out.append(comp)
    return out


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
