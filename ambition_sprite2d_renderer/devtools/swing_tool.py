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
TRAIL_BODY = (158, 96, 228)
TRAIL_CORE = (226, 196, 255)
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


class FastRig:
    """In-memory rig for searching, so a sample costs 0.1ms instead of 200ms.

    Profiling the old loop: one objective evaluation took 205 ms, of which
    `doc.solve` -- the actual maths -- was 0.13 ms. The other 99.9% was
    rewriting a JSON file and reloading all 136 clips to read one number back.
    No optimiser can fix an objective that expensive, so the fix is here rather
    than in the search: build the projection ONCE and patch its channel keys.

    Channel values are not the numbers stored in the pose files -- the
    projection mirrors and offsets them for a west-facing rig -- so the map is
    MEASURED per bone (two writes, once) rather than assumed.
    """

    def __init__(self, clip_name: str):
        pp = _fresh()
        self.clip_name = clip_name
        self.doc = pp._doc()
        self.clip = pp._prepared().library.clips[clip_name]
        self.channels = self.doc.clips[clip_name]["channels"]
        self._map: dict[str, tuple[float, float]] = {}

    def _keys(self, bone: str):
        entry = self.channels.get(bone)
        return entry["keys"] if entry and "keys" in entry else None

    def set(self, bone: str, idx: int, projected: float) -> None:
        keys = self._keys(bone)
        if keys is not None and idx < len(keys):
            keys[idx][1] = float(projected)

    def get(self, bone: str, idx: int) -> float:
        keys = self._keys(bone)
        return float(keys[idx][1]) if keys is not None and idx < len(keys) else 0.0

    def calibrate(self, bone: str, idx: int) -> tuple[float, float]:
        """projected = a * stored + b, measured with two real writes."""
        if bone in self._map:
            return self._map[bone]
        before = read_bone(self.clip_name, idx, bone)
        samples = []
        for probe in (0.0, 100.0):
            write_bone(self.clip_name, idx, bone, probe)
            fresh = _fresh()
            samples.append(fresh._doc().clips[self.clip_name]["channels"][bone]["keys"][idx][1])
        write_bone(self.clip_name, idx, bone, before)
        a = (samples[1] - samples[0]) / 100.0
        b = samples[0]
        self._map[bone] = (a, b)
        return a, b

    def to_projected(self, bone: str, idx: int, stored: float) -> float:
        a, b = self.calibrate(bone, idx)
        return a * stored + b

    def to_stored(self, bone: str, idx: int, projected: float) -> float:
        a, b = self.calibrate(bone, idx)
        return (projected - b) / a if a else 0.0

    def _norm(self, idx: int) -> float:
        return _frame_norm(self.clip, idx)

    def sword_angle(self, idx: int) -> float:
        world, _ = self.doc.solve(self.clip_name, self._norm(idx))
        return world["near_arm_hand"].angle % 360.0

    def grip_gap(self, idx: int) -> float:
        world, _ = self.doc.solve(self.clip_name, self._norm(idx))
        far = world["far_arm_hand"].origin
        near = world["near_arm_hand"].origin
        return math.hypot(far[0] - near[0], far[1] - near[1])


def read_bone(clip_name: str, idx: int, bone: str) -> float:
    path = _clip_path(clip_name)
    key = json.loads(path.read_text())["pose_keys"][idx]
    if "pose" in key:
        state = json.loads((LIB / "poses" / f"{key['pose'].replace('/', '__')}.pose.json").read_text())["state"]
    else:
        state = key["state"]
    return float(state.get("bones", {}).get(bone, {}).get("rotation_deg", 0.0))


def write_bone(clip_name: str, idx: int, bone: str, value: float) -> None:
    path = _clip_path(clip_name)
    doc = json.loads(path.read_text())
    key = doc["pose_keys"][idx]
    if "pose" in key:
        pose_path = LIB / "poses" / f"{key['pose'].replace('/', '__')}.pose.json"
        state = json.loads(pose_path.read_text())
        state["state"].setdefault("bones", {}).setdefault(bone, {})["rotation_deg"] = round(value, 4)
        pose_path.write_text(json.dumps(state, indent=2) + "\n")
    else:
        key["state"].setdefault("bones", {}).setdefault(bone, {})["rotation_deg"] = round(value, 4)
        path.write_text(json.dumps(doc, indent=2) + "\n")


def solve_frame_fast(rig: "FastRig", idx: int, lower: float, target: float,
                     lo: float = -260.0, hi: float = 200.0, coarse: float = 1.0):
    """Same dense scan, run entirely in memory."""
    rig.set("near_arm_l", idx, rig.to_projected("near_arm_l", idx, lower))
    best = None
    steps = int((hi - lo) / coarse) + 1
    for k in range(steps):
        stored = lo + k * coarse
        rig.set("near_arm_u", idx, rig.to_projected("near_arm_u", idx, stored))
        got = rig.sword_angle(idx)
        err = abs((got - target + 180.0) % 360.0 - 180.0)
        if best is None or err < best[0]:
            best = (err, stored, got)
    err, stored, got = best
    step = coarse / 2.0
    while step > 0.02:
        for delta in (-step, step):
            rig.set("near_arm_u", idx, rig.to_projected("near_arm_u", idx, stored + delta))
            got2 = rig.sword_angle(idx)
            err2 = abs((got2 - target + 180.0) % 360.0 - 180.0)
            if err2 < err:
                err, stored, got = err2, stored + delta, got2
        step /= 2.0
    rig.set("near_arm_u", idx, rig.to_projected("near_arm_u", idx, stored))
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


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def draw_trail(images, window: int = 3, subdiv: int = 5, inner: float = 0.58,
               alpha: int = 120, blur: float = 0.8, core_alpha: int = 150):
    """`window`/`inner`/`alpha` are what separate a tilt from a smash: a smash
    wants a longer, wider, brighter ribbon so the commitment reads."""
    axes = [blade_axis(im) for im in images]
    out = []
    for i, base in enumerate(images):
        trail = Image.new("RGBA", base.size, (0, 0, 0, 0))
        for k in range(window, 0, -1):
            j0, j1 = i - k, i - k + 1
            if j0 < 0 or j1 >= len(images) or axes[j0] is None or axes[j1] is None:
                continue
            for s in range(subdiv):
                t0, t1 = s / subdiv, (s + 1) / subdiv
                age = ((k - 1) + (1 - t1)) / window
                a = int(alpha * (1.0 - age) ** 1.7)
                if a <= 2:
                    continue
                b0 = _lerp(axes[j0][0], axes[j1][0], t0)
                p0 = _lerp(axes[j0][1], axes[j1][1], t0)
                b1 = _lerp(axes[j0][0], axes[j1][0], t1)
                p1 = _lerp(axes[j0][1], axes[j1][1], t1)
                f = inner + (1.0 - inner) * 0.55 * age
                seg = Image.new("RGBA", base.size, (0, 0, 0, 0))
                ImageDraw.Draw(seg).polygon(
                    [_lerp(b0, p0, f), p0, p1, _lerp(b1, p1, f)], fill=TRAIL_BODY + (a,)
                )
                trail.alpha_composite(seg)
        trail = trail.filter(ImageFilter.GaussianBlur(blur))
        if i > 0 and axes[i] and axes[i - 1]:
            core = Image.new("RGBA", base.size, (0, 0, 0, 0))
            ImageDraw.Draw(core).polygon(
                [_lerp(axes[i - 1][0], axes[i - 1][1], 0.80), axes[i - 1][1],
                 axes[i][1], _lerp(axes[i][0], axes[i][1], 0.80)],
                fill=TRAIL_CORE + (core_alpha,),
            )
            trail.alpha_composite(core.filter(ImageFilter.GaussianBlur(0.5)))
        comp = Image.new("RGBA", base.size, BG)
        comp.alpha_composite(trail)
        comp.alpha_composite(base)
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


def hit_polygon(axes, i, reach: float = 1.0, linger: int = 3):
    """Proposed hit volume for frame `i`: the hull of the blade over the last
    `linger` frames, so the volume GROWS as the swing travels and stays wide
    enough to connect, instead of collapsing to one thin swept step.

    NOTE: derived from the swing, not authored data. No hitboxes exist for this
    character yet (`RigDocument`'s "hitboxes" slot is empty), so this shows the
    reach a hitbox WOULD need. The shipping path is
    `core.slash_envelope.SwingDescriptor`, which drives the hit polygon and the
    effect art off one profile so they cannot drift.
    """
    pts = []
    for j in range(max(0, i - linger + 1), i + 1):
        if axes[j] is None:
            continue
        base, tip = axes[j]
        if reach != 1.0:
            base = _lerp(base, tip, 1.0 - reach)
        pts.extend([base, tip])
    if len(pts) < 3:
        return None
    return _hull(pts)


def draw_hitboxes(images, reach: float = 1.0, linger: int = 3, active=None):
    """`active` limits the overlay to the frames that actually connect.

    A swing is only dangerous for part of its travel; drawing a volume on the
    wind-up and the recovery makes an attack look far more threatening than it
    is, which is the opposite of what a review image is for.
    """
    axes = [blade_axis(im) for im in images]
    out = []
    for i, base in enumerate(images):
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        poly = None if (active is not None and i not in active) else hit_polygon(axes, i, reach, linger)
        if poly is not None and len(poly) >= 3:
            draw = ImageDraw.Draw(layer)
            draw.polygon(poly, fill=HITBOX + (46,))
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
    images, clip = render_clip(args.clip)
    if not args.no_trail:
        images = draw_trail(images)
    if args.hitbox:
        images = draw_hitboxes(images, reach=args.reach, linger=args.linger,
                               active=({int(v) for v in args.active.split(",")} if args.active else None))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    scale = args.scale
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
    draw.text((8, h // 2 - 14), args.clip, fill=(235, 235, 240, 255))
    draw.text((8, h // 2 + 2), f"{clip.frame_count}f @ {clip.frame_duration_ms}ms", fill=(150, 150, 160, 255))
    strip.save(out.with_suffix(".png"))
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
