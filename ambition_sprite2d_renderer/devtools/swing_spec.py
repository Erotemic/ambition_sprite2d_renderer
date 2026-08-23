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
    hitbox        which frames connect, and how the volume accumulates
    invariants    checkable properties of the arc, listed below
    body          non-arm channels per frame: root_x / root_y / any bone name,
                  which is how a smash ends on one knee
    trail         ribbon styling; a smash wants window/inner/alpha turned up so
                  it reads grander than a tilt
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
    for rule in invariants:
        name, _, arg = rule.partition(":")
        if name == "monotonic_increasing":
            bad = [i for i in range(1, len(seq)) if seq[i] <= seq[i - 1]]
            if bad:
                failures.append(f"{rule}: frames {bad} do not increase "
                                f"({[round(v,1) for v in seq]})")
        elif name == "monotonic_decreasing":
            bad = [i for i in range(1, len(seq)) if seq[i] >= seq[i - 1]]
            if bad:
                failures.append(f"{rule}: frames {bad} do not decrease "
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


def measured(clip: str):
    return [st.sword_angle(clip, i) for i in range(len(load(clip)["sword_deg"]))]


def apply_spec(clip: str, verbose: bool = True):
    spec = load(clip)
    angles = spec["sword_deg"]
    elbows = spec["elbow"]
    torsos = spec.get("torso") or [None] * len(angles)
    shifts = spec.get("torso_shift") or [None] * len(angles)
    if not (len(elbows) == len(torsos) == len(shifts) == len(angles)):
        raise SystemExit(f"{clip}: spec channel lengths disagree")
    if verbose:
        print(f"{clip}: solving {len(angles)} frames")
        print("  f   target   elbow   torso   shoulder      got     err")
    for i, target in enumerate(angles):
        shift = tuple(shifts[i]) if shifts[i] else None
        upper, got, err = st.solve_frame(clip, i, elbows[i], target,
                                         torso=torsos[i], shift=shift)
        if verbose:
            tor = "  -  " if torsos[i] is None else f"{torsos[i]:5.1f}"
            mark = "" if err < 2.0 else "   <== unreachable"
            print(f"  {i} {target:8.1f} {elbows[i]:7.1f} {tor} {upper:10.2f} {got:8.1f} {err:6.1f}{mark}")
    body = spec.get("body") or {}
    if body:
        _apply_body(clip, body, len(angles))
        if verbose:
            print(f"  body: {', '.join(sorted(body))}")
    for frame, pose in (spec.get("off_hand") or {}).items():
        st.write_far(clip, int(frame), pose[0], pose[1], (0.0, 0.0))
    for frame in spec.get("grip_frames") or []:
        u, l, gap = st.solve_grip(clip, int(frame))
        if gap >= 1.0:
            _, gap = st.close_grip_by_shift(clip, int(frame), u, l)
        if verbose:
            mark = "" if gap < 3.0 else "   <== off hand cannot reach"
            print(f"  grip f{frame}: gap {gap:.2f}px{mark}")
    return spec


def _apply_body(clip: str, body: dict, frames: int) -> None:
    """Write non-arm channels: root offset and any bone rotation, per frame.

    A forward smash that ends on one knee is not an arm pose -- it drops the
    root and folds the legs. Keeping these in the same spec means the whole
    attack is one declaration rather than an arm file plus a body afterthought.
    """
    path = st._clip_path(clip)
    doc = json.loads(path.read_text())
    for i in range(frames):
        key = doc["pose_keys"][i]
        if "pose" in key:
            pose_path = st.LIB / "poses" / f"{key['pose'].replace('/', '__')}.pose.json"
            state = json.loads(pose_path.read_text())
            target = state["state"]
            sink = lambda st_=state, p=pose_path: p.write_text(json.dumps(st_, indent=2) + "\n")
        else:
            target = key["state"]
            sink = None
        for channel, values in body.items():
            if values[i] is None:
                continue
            if channel == "root_y":
                pos = target.setdefault("root", {}).setdefault("position", [0.0, 0.0])
                pos[1] = round(float(values[i]), 4)
            elif channel == "root_x":
                pos = target.setdefault("root", {}).setdefault("position", [0.0, 0.0])
                pos[0] = round(float(values[i]), 4)
            else:
                bones = target.setdefault("bones", {})
                bones.setdefault(channel, {})["rotation_deg"] = round(float(values[i]), 4)
        if sink is not None:
            sink()
    path.write_text(json.dumps(doc, indent=2) + "\n")


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


def cmd_solve(args):
    spec = apply_spec(args.clip)
    code = report(args.clip, spec)
    if args.preview:
        hb = spec.get("hitbox") or {}
        images, clip = st.render_clip(args.clip)
        images = st.draw_trail(images, **(spec.get("trail") or {}))
        if hb.get("active") is not None:
            images = st.draw_hitboxes(images, reach=hb.get("reach", 1.0),
                                      linger=hb.get("linger", 3), active=set(hb["active"]))
        out = Path(args.preview)
        st.save_preview(images, clip, args.clip, out, scale=2)
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
