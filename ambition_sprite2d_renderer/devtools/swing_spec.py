"""Declare an attack as a SPEC, then solve and verify it.

Every request so far has reduced to the same handful of statements: the blade
points HERE on this frame, the off hand is ON THE HILT for these frames, the
swing never rises above horizontal, it sweeps one way without doubling back,
it is symmetric about straight-down. Those are constraints, and until now they
lived only in whoever was picking the numbers -- which is exactly how a
non-monotonic dip and an unwanted high wind-up both reached review.

A spec states them once, in one file per clip:

    sword_deg     the blade's world angle per frame (0=E, 90=DOWN, 180=W, 270=UP)
    elbow/torso   the profile the solver is allowed to use to reach those angles
    torso_shift   optional per-frame torso translation (leans the body out)
    grip_frames   frames where the off hand holds the hilt
    off_hand      explicit far-arm poses for frames that do NOT grip
    hitbox        which frames connect. The volume's SHAPE is not declared here
                  -- it is derived from the trail, so the hit and the art it
                  promises cannot drift apart
    invariants    checkable properties of the arc, listed below
    body          non-arm channels per frame: root_x / root_y / any bone name,
                  which is how a smash ends on one knee
    ground_contacts
                  per frame, the joints that must touch the floor. The first is
                  solved with the root and the rest with the bone above them,
                  so "she ends on one knee" is solved rather than dialled in
    effect        "trail" (a swept ribbon) or "poke" (an axial thrust flash).
                  The hit volume takes the same shape, so nothing hits in a
                  shape the player was never shown. A spec may carry ONLY an
                  effect -- no sword_deg -- when the pose is already right
    poke          thrust styling: extend/width/waist/inner
    trail         ribbon styling. A smash reads grander than a tilt by SIZE and
                  by HEAT -- body_rgb/core_rgb carry the hotter smash palette,
                  because once both are in motion size alone does not separate
                  them. The ribbon inherits the hitbox's live frames unless it
                  names its own
    todo          what is deliberately unfinished and why

`solve` writes the pose data and then checks the invariants. `check` verifies
without writing, so a clip can be re-validated after anyone edits it by hand.

Invariants:
    monotonic_increasing / monotonic_decreasing
        the blade sweeps one way, measured on the UNWRAPPED angle so a sweep
        through 0/360 still reads as continuous
    below_horizontal       every frame strictly between 0 and 180 (blade low)
    never_above:<deg>      unwrapped travel stays under this bound
    symmetric_about:<deg>[@a,b]
        two frames equidistant from an axis; defaults to the endpoints, but a
        pair can be named -- a down smash is symmetric about its two HITS, not
        about its neutral start and its settle
    starts_near:<deg>      frame 0 within tolerance of a resting angle
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import swing_tool as st

SPECS = st.LIB / "specs"
TOL = 2.5


def spec_path(clip: str) -> Path:
    return SPECS / f"{clip}.spec.json"


def load(clip: str) -> dict:
    path = spec_path(clip)
    if not path.exists():
        raise SystemExit(f"no spec for {clip!r} at {path}")
    return json.loads(path.read_text())


def unwrap(values):
    """Successive angles made continuous, so a sweep across 0/360 is monotone."""
    out = [float(values[0])]
    for value in values[1:]:
        prev = out[-1]
        candidate = float(value)
        while candidate - prev > 180.0:
            candidate -= 360.0
        while prev - candidate > 180.0:
            candidate += 360.0
        out.append(candidate)
    return out


def check_invariants(angles, invariants):
    """Return a list of failures; empty means the arc holds."""
    failures = []
    seq = unwrap(angles)

    def span(arg_text):
        """The frame range a rule governs; the whole clip unless it says otherwise.

        A swing that ends in a HOLD is not monotone over the whole clip -- the
        recovery frames sit still by design -- so the sweep rule has to be able
        to name where the sweep stops.
        """
        if "@" not in arg_text:
            return 1, len(seq)
        lo, hi = (int(v) for v in arg_text.split("@")[-1].split(","))
        return max(1, lo + 1), min(len(seq), hi + 1)

    for rule in invariants:
        name, _, arg = rule.partition(":")
        if name.startswith("monotonic_"):
            name, _, arg = rule.partition("@")
            lo, hi = span(rule)
            rising = name == "monotonic_increasing"
            bad = [i for i in range(lo, hi)
                   if (seq[i] <= seq[i - 1] if rising else seq[i] >= seq[i - 1])]
            if bad:
                verb = "increase" if rising else "decrease"
                failures.append(f"{rule}: frames {bad} do not {verb} "
                                f"({[round(v,1) for v in seq]})")
        elif name == "below_horizontal":
            bad = [i for i, a in enumerate(angles) if not (0.0 < a % 360.0 < 180.0)]
            if bad:
                failures.append(f"{rule}: frames {bad} put the blade at or above horizontal "
                                f"({[round(angles[i] % 360.0, 1) for i in bad]})")
        elif name == "never_above":
            limit = float(arg)
            span = max(seq) - min(seq)
            if span > limit + TOL:
                failures.append(f"{rule}: total travel {span:.1f} exceeds {limit}")
        elif name == "symmetric_about":
            # "90@2,6" names the pair to compare. Defaulting to the endpoints was
            # wrong for a down smash, whose symmetric pair is the two HITS while
            # frame 0 is the neutral start and the last frame is the settle.
            axis_text, _, pair = arg.partition("@")
            axis = float(axis_text)
            if pair:
                lo_i, hi_i = (int(v) for v in pair.split(","))
            else:
                lo_i, hi_i = 0, len(angles) - 1
            first = abs(((angles[lo_i] - axis + 180.0) % 360.0) - 180.0)
            last = abs(((angles[hi_i] - axis + 180.0) % 360.0) - 180.0)
            if abs(first - last) > TOL:
                failures.append(f"{rule}: frames {lo_i}/{hi_i} sit {first:.1f} and "
                                f"{last:.1f} from the axis")
        elif name == "starts_near":
            want = float(arg)
            off = abs(((angles[0] - want + 180.0) % 360.0) - 180.0)
            if off > 12.0:
                failures.append(f"{rule}: frame 0 is {off:.1f} away from {want}")
        else:
            failures.append(f"unknown invariant {rule!r}")
    return failures


def hit_shape(spec: dict) -> dict:
    """Hit-volume geometry, DERIVED from the ribbon rather than declared beside it.

    The hitbox is the trail. Its inner edge is where the ribbon's inner edge is,
    its window is how long the ribbon lingers, and it never reaches past the
    blade. Growing a hitbox therefore means making the swing sweep longer, which
    the player can see -- not quietly inflating a box beyond the art, which they
    cannot. One source, so the two cannot drift apart.
    """
    trail = spec.get("trail") or {}
    hb = spec.get("hitbox") or {}
    return {
        "reach": round(1.0 - trail.get("inner", 0.58), 4),
        "linger": trail.get("window", 3) + 1,
        "extend": hb.get("extend", 1.0),
        "inflate": hb.get("inflate", 0.0),
    }


def check_pixel_invariants(images, spec: dict, axes=None):
    """Rules about WHERE the swing lands, checked against the rendered frames.

    The angle invariants govern the shape of the arc; these govern its place in
    the world, which is the half that kept being stated in review and then lost.
    "The blade goes all the way to the ground" and "the entire hitbox is in
    front of her" are both measurable, and neither survives as a comment.

    Measured on RAW frames -- before the trail, whose core out-shines the blade.

        tip_reaches_ground:<frame>[@tol]
            the blade tip sits within `tol` px of the neutral-stance foot line
        hitbox_in_front[:tol]
            every vertex of every live hit polygon is on the facing side of the
            fighter's centre line
        feet_on_ground[:tol]
            no frame leaves the fighter hovering above the floor line
    """
    rules = spec.get("pixel_invariants") or []
    if not rules:
        return []
    ground = st.ground_y(images)
    axes = axes if axes is not None else [st.blade_axis(im) for im in images]
    front = -1.0 if spec.get("facing", "west") == "west" else 1.0
    failures = []
    for rule in rules:
        name, _, arg = rule.partition(":")
        if name == "tip_reaches_ground":
            frame_text, _, tol_text = arg.partition("@")
            i = int(frame_text)
            tol = float(tol_text) if tol_text else 8.0
            if axes[i] is None:
                failures.append(f"{rule}: no blade found on frame {i}")
                continue
            gap = ground - axes[i][1][1]
            if abs(gap) > tol:
                failures.append(f"{rule}: tip is {gap:.1f}px "
                                f"{'above' if gap > 0 else 'below'} the ground line")
        elif name == "hitbox_in_front":
            tol = float(arg) if arg else 4.0
            hb = spec.get("hitbox") or {}
            active = sorted(hb.get("active") or [])
            for i in active:
                poly = st.volume_polygon(axes, i, spec.get("effect", "trail"), active[0],
                                         hit_shape(spec), spec.get("poke") or {})
                extent = st.body_extent(images[i])
                if poly is None or extent is None:
                    continue
                behind = [p for p in poly if (p[0] - extent[0]) * front < -tol]
                if behind:
                    worst = max(abs(p[0] - extent[0]) for p in behind)
                    failures.append(f"{rule}: frame {i} puts {len(behind)} vertex/vertices "
                                    f"up to {worst:.0f}px BEHIND her centre")
        elif name == "feet_on_ground":
            tol = float(arg) if arg else 3.0
            for i, im in enumerate(images):
                extent = st.body_extent(im)
                if extent is None:
                    continue
                gap = ground - extent[1]
                if gap > tol:
                    failures.append(f"{rule}: frame {i} floats {gap:.0f}px above the floor")
        else:
            failures.append(f"unknown pixel invariant {rule!r}")
    return failures


def frame_count(clip: str, spec: dict) -> int:
    angles = spec.get("sword_deg")
    if angles:
        return len(angles)
    pp = st._fresh()
    return pp._prepared().library.clips[clip].frame_count


def measured(clip: str):
    spec = load(clip)
    return [st.sword_angle(clip, i) for i in range(frame_count(clip, spec))]


def channel_plan(clip: str, spec: dict) -> dict:
    """Every channel the spec drives, for every frame: ``{frame: {name: stored}}``.

    Building the WHOLE plan before touching disk is what makes the solve fast
    and total. Fast, because seeding is then one pass over the files instead of
    one rewrite per channel per frame. Total, because a channel absent from the
    clip is absent from the projection too, so an unseeded channel would be a
    control the in-memory solver cannot move -- and a silent no-op write reads
    exactly like "the solver could not reach that angle".

    Channels the spec does not pin keep their current stored value, so a solve
    is not also an unannounced reset of everything it did not mention.
    """
    n = len(spec["sword_deg"])
    torsos = spec.get("torso") or [None] * n
    shifts = spec.get("torso_shift") or [None] * n
    body = spec.get("body") or {}
    off_hand = spec.get("off_hand") or {}
    grips = [int(f) for f in spec.get("grip_frames") or []]

    lengths = {"elbow": len(spec["elbow"]), "torso": len(torsos), "torso_shift": len(shifts)}
    lengths.update({f"body.{k}": len(v) for k, v in body.items()})
    bad = {k: v for k, v in lengths.items() if v != n}
    if bad:
        raise SystemExit(f"{clip}: channels disagree with {n} frames: {bad}")

    plan: dict = {i: {"near_arm_l": spec["elbow"][i]} for i in range(n)}
    for i in range(n):
        if torsos[i] is not None:
            plan[i]["torso"] = torsos[i]
        if shifts[i]:
            plan[i]["torso.x"], plan[i]["torso.y"] = shifts[i]
        for channel, values in body.items():
            if values[i] is not None:
                plan[i][channel] = values[i]
    for frame, pose in off_hand.items():
        plan[int(frame)]["far_arm_u"], plan[int(frame)]["far_arm_l"] = pose
        plan[int(frame)]["far_arm_u.x"] = 0.0
        plan[int(frame)]["far_arm_u.y"] = 0.0
    if grips:
        for i in grips:
            plan[i].setdefault("far_arm_u.x", 0.0)
            plan[i].setdefault("far_arm_u.y", 0.0)

    # Seed the union across frames: a channel authored on only some frames is
    # still one channel, and the projection wants a key on every frame of it.
    names = {"near_arm_u"} | {n_ for row in plan.values() for n_ in row}
    for i in range(n):
        for name in names:
            plan[i].setdefault(name, st.read_channel(clip, i, name))
    return plan


def apply_spec(clip: str, verbose: bool = True):
    spec = load(clip)
    if "sword_deg" not in spec:
        # An effect-only spec. Some poses are already right, and re-solving one
        # from angles I transcribed off it would only be a chance to get them
        # slightly wrong.
        if verbose:
            print(f"{clip}: effect only, poses untouched")
        return spec
    angles = spec["sword_deg"]
    elbows = spec["elbow"]
    torsos = spec.get("torso") or [None] * len(angles)
    shifts = spec.get("torso_shift") or [None] * len(angles)

    was = st.ensure_frames(clip, len(angles))
    if verbose and was != len(angles):
        print(f"{clip}: {was} frames -> {len(angles)}")
    rig = st.FastRig.seed(clip, channel_plan(clip, spec))
    if verbose:
        print(f"{clip}: solving {len(angles)} frames")
        print("  f   target   elbow   torso   shoulder      got     err")
    for i, target in enumerate(angles):
        shift = tuple(shifts[i]) if shifts[i] else None
        upper, got, err = st.solve_frame_fast(rig, i, elbows[i], target,
                                              torso=torsos[i], shift=shift)
        if verbose:
            tor = "  -  " if torsos[i] is None else f"{torsos[i]:5.1f}"
            mark = "" if err < 2.0 else "   <== unreachable"
            print(f"  {i} {target:8.1f} {elbows[i]:7.1f} {tor} {upper:10.2f} {got:8.1f} {err:6.1f}{mark}")
    contacts = spec.get("ground_contacts") or {}
    if contacts:
        floor = st.ground_world(rig)
        carried: dict = {}
        for frame, joints in sorted(contacts.items(), key=lambda kv: int(kv[0])):
            # Seed each frame from the previous one's answer, so a hold stays on
            # ONE branch of the contact goal instead of flipping between the two
            # leg poses that both put the foot on the floor.
            for channel, value in carried.items():
                rig.write(channel, int(frame), value)
            for joint, channel, value, err in st.solve_ground_contacts(rig, int(frame), joints, floor):
                carried[channel] = value
                if verbose:
                    mark = "" if err < 1.5 else "   <== cannot reach the floor"
                    print(f"  contact f{frame}: {joint} via {channel}={value:.1f} "
                          f"({err:.2f}px off){mark}")
    for frame in spec.get("grip_frames") or []:
        idx = int(frame)
        _, _, gap = st.solve_grip_fast(rig, idx)
        if gap >= 1.0:
            _, gap = st.close_grip_fast(rig, idx)
        if verbose:
            mark = "" if gap < 3.0 else "   <== off hand cannot reach"
            print(f"  grip f{idx}: gap {gap:.2f}px{mark}")
    rig.flush()
    if verbose and spec.get("body"):
        print(f"  body: {', '.join(sorted(spec['body']))}")
    return spec


def report(clip: str, spec: dict) -> int:
    angles = measured(clip)
    print(f"  measured: {[round(a,1) for a in angles]}")
    failures = check_invariants(angles, spec.get("invariants") or [])
    if failures:
        print(f"  {len(failures)} INVARIANT FAILURE(S):")
        for f in failures:
            print(f"    - {f}")
        return 1
    print(f"  all {len(spec.get('invariants') or [])} invariants hold")
    if spec.get("todo"):
        print(f"  TODO: {spec['todo'][:100]}...")
    return 0


def preview(clip_name: str, spec: dict, out: Path):
    """Render the clip with its trail, hit volumes and floor rule.

    Returns the pixel-invariant failures, because the same raw frames answer
    both questions and rendering them twice is the sort of waste that turned a
    solve into a coffee break.
    """
    hb = spec.get("hitbox") or {}
    raw, clip = st.render_clip(clip_name)
    axes = [st.blade_axis(im) for im in raw]
    failures = check_pixel_invariants(raw, spec, axes)
    effect = spec.get("effect", "trail")
    style = dict(spec.get(effect) or {})
    if hb.get("active") is not None:
        # One window for both: a frame that cannot hurt anyone does not sweep light.
        style.setdefault("active", hb["active"])
    images = (st.draw_poke if effect == "poke" else st.draw_trail)(raw, axes=axes, **style)
    if hb.get("active") is not None:
        images = st.draw_hitboxes(images, active=set(hb["active"]), effect=effect,
                                  poke=spec.get("poke") or {}, axes=axes, **hit_shape(spec))
    images = st.draw_ground(images, st.ground_y(raw))
    st.save_preview(images, clip, clip_name, out, scale=2)
    return failures


def cmd_solve(args):
    spec = apply_spec(args.clip)
    code = report(args.clip, spec)
    if args.preview:
        out = Path(args.preview)
        failures = preview(args.clip, spec, out)
        if failures:
            code = 1
            print(f"  {len(failures)} PLACEMENT FAILURE(S):")
            for f in failures:
                print(f"    - {f}")
        elif spec.get("pixel_invariants"):
            print(f"  all {len(spec['pixel_invariants'])} placement rules hold")
        print(f"  wrote {out.with_suffix('.gif')}")
    raise SystemExit(code)


def cmd_check(args):
    clips = [args.clip] if args.clip else sorted(p.name.split(".")[0] for p in SPECS.glob("*.spec.json"))
    worst = 0
    for clip in clips:
        spec = load(clip)
        print(f"{clip}:")
        worst |= report(clip, spec)
    raise SystemExit(worst)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("solve", help="apply a spec, then verify its invariants")
    s.add_argument("clip")
    s.add_argument("--preview", help="also render a preview to this path")
    s.set_defaults(func=cmd_solve)
    c = sub.add_parser("check", help="verify without writing; omit CLIP for every spec")
    c.add_argument("clip", nargs="?")
    c.set_defaults(func=cmd_check)
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
