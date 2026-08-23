"""Re-author player_robot_v3's crouch family so he CROUCHES instead of sinking.

The shipped crouch pushed `root_y` down by 8 px with the legs already pre-bent
at frame 0 and never folding further. That is not a crouch: the head dropped
8 px of a 42 px head-to-ankle span (19 %), and because the legs never absorbed
the drop the ankles ended 11.7 px BELOW the ground line — the feet went through
the floor, which is what showed in game.

Here the ground line is the constraint and the fold is the mechanism. For each
frame the leg is solved so its ankle lands on `ground_y - ankle_h`; `root_y` is
then free to carry the body down as far as the fold allows. Where along the
line a foot lands is a soft preference, not a constraint — with a 11.1 px thigh
and an 8.1 px shin against a 19 px standing span, a crouch forbidden to move its
feet cannot fold at all.

Idempotent: it solves from the rig's own bind pose, not from the current keys,
so running it twice produces the same document.

    python3 scripts/reauthor_robot_v3_crouch.py [--dry-run]
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument  # noqa: E402

RIG = (
    ROOT
    / "ambition_sprite2d_renderer/targets/characters/rigged/player_robot_v3"
    / "player_robot_v3.rig.json"
)

# How far the pelvis travels, in frame pixels.
#
# 12 is not a taste call, it is where the ART runs out: the pelvis joint carries
# ~13.5 px of hip art beneath it, so a pelvis below y=144.5 puts the robot's seat
# through a floor at y=158. Swept 12..18 against the rendered alpha bottom and it
# grows 1 px per 1 px of drop, exactly as that predicts. Deeper than this and the
# crouch is only lower because it is inside the ground — which is what the pose
# it replaces was doing.
#
# The character is a big head on 19 px legs against a 101 px silhouette, so the
# reachable compression is ~10%, not the ~30% a long-legged fighter gets. The
# collision box still halves; art and box are not required to agree, and cannot.
CROUCH_DROP = 12.0
# The knee's ART hangs ~11 px below the knee JOINT, so a clearance chosen for the
# joint alone puts the knee cap through the floor — the same class of mistake the
# shipped crouch made with the feet. Measured from the render, not assumed.
KNEE_CLEARANCE = 5.0
# The hold's shape on top of the leg solve. The head is a child of the torso, so
# a negative head channel keeps the face level while the chest pitches forward.
CROUCH_SHAPE = {
    "torso": 8.0,
    "head": -4.0,
    "pelvis": -2.0,
    "far_arm_u": 24.0,
    "far_arm_l": 16.0,
    "near_arm_u": -14.0,
    "near_arm_l": 10.0,
    "eye_squint": 0.18,
}
#: The head sinks onto the shoulders and SQUASHES while it does.
#:
#: The squash is the character read — a robot whose head goes wide and flat is
#: cute, and it is also the only way this one gets meaningfully lower: his head
#: is 52 px tall above its own joint, so headroom is the only room he has left.
#: Swept 1.0/0.85/0.8/0.75/0.7 against the drawing; below ~0.75 the eyes spread
#: far enough that he stops reading as himself.
#:
#: ⛔ this character's crouch is NOT half his standing height and cannot be:
#: `BodyMode::Crouching` halves his 91 px box to 45.5, and his head alone is
#: 52 px. Art and box do not agree here, by arithmetic rather than by choice.
CROUCH_HEAD_SINK = 4.0
CROUCH_HEAD_SQUASH = 0.8
#: Head channels default to 1.0 (a scale) rather than 0.0 (an offset), so they
#: cannot ride the same "everything else rests at zero" rule as the angles.
HEAD_CHANNEL_RESTS = {"bone.head.y": 0.0, "bone.head.scale_y": 1.0}

# Breathing on the hold, and the crouch-walk's stride, both in frame pixels.
BREATH = 1.6
STRIDE_X = 5.5
STRIDE_LIFT = 2.4

LEG_CHANNELS = ("far_leg_u", "far_leg_l", "far_leg_foot", "near_leg_u", "near_leg_l", "near_leg_foot")


class Poser:
    """A one-frame scratch clip on an in-memory rig — solves in ~0.07 ms."""

    def __init__(self, doc: RigDocument) -> None:
        self.doc = doc
        self.ground = doc.frame["ground_y"] - doc.frame["ankle_h"]
        names = list(doc.clips["crouch"]["channels"])
        self.ch = {n: {"keys": [[0.0, 0.0], [1.0, 0.0]]} for n in names}
        for name, rest in HEAD_CHANNEL_RESTS.items():
            self.ch.setdefault(name, {"keys": [[0.0, rest], [1.0, rest]]})
        doc.data["clips"]["__solve__"] = {
            "loop": False,
            "frames": 1,
            "duration_ms": 100,
            "channels": self.ch,
        }
        self.set(face_open_vis=1.0, head_look=1.0)

    def set(self, **vals):
        for k, v in vals.items():
            self.ch[k]["keys"] = [[0.0, float(v)], [1.0, float(v)]]

    def clear(self):
        for n in self.ch:
            rest = HEAD_CHANNEL_RESTS.get(n, 0.0)
            self.ch[n]["keys"] = [[0.0, rest], [1.0, rest]]
        self.set(face_open_vis=1.0, head_look=1.0)

    def solve(self):
        return self.doc.solve("__solve__", 0.0)[0]

    def drop(self):
        del self.doc.data["clips"]["__solve__"]


def leg_cost(p: Poser, side: str, target):
    w = p.solve()
    ankle = w[f"{side}_leg_foot"].origin
    knee = w[f"{side}_leg_l"].origin
    hip = w[f"{side}_leg_u"].origin
    cost = 40.0 * (ankle[1] - target[1]) ** 2
    cost += 0.6 * (ankle[0] - target[0]) ** 2
    # The three shape rules that pick the SQUAT branch out of the two the IK
    # admits: without them the solver is equally happy to put the knee behind
    # the hip or below the floor, and it does.
    cost += 20.0 * max(0.0, (hip[0] + 3.0) - knee[0]) ** 2
    cost += 200.0 * max(0.0, knee[1] - (target[1] - KNEE_CLEARANCE)) ** 2
    cost += 20.0 * max(0.0, (hip[1] + 2.0) - knee[1]) ** 2
    return cost


def descend(p: Poser, side: str, target, u0: float, l0: float):
    u, l = u0, l0
    p.set(**{f"{side}_leg_u": u, f"{side}_leg_l": l})
    best = leg_cost(p, side, target)
    step = 20.0
    while step > 1e-4:
        moved = False
        for name, tag in ((f"{side}_leg_u", "u"), (f"{side}_leg_l", "l")):
            for sign in (1, -1):
                val = (u if tag == "u" else l) + sign * step
                p.set(**{name: val})
                cost = leg_cost(p, side, target)
                if cost < best - 1e-9:
                    best = cost
                    if tag == "u":
                        u = val
                    else:
                        l = val
                    moved = True
                else:
                    p.set(**{name: (u if tag == "u" else l)})
        if not moved:
            step *= 0.5
    return u, l, best


def solve_leg(p: Poser, side: str, target, seed=None):
    """Solve one leg onto `target`.

    Without a seed this multi-starts, because a coarse descent from one seed
    lands in whichever branch it started nearest and the two branches here are a
    squat and a kneel. WITH a seed it descends once from the previous frame's
    answer, which is what keeps a clip on ONE branch: independently solved
    neighbours can each be correct and still differ enough to POP, and a
    six-frame breathing loop that pops is worse than one that does not breathe.
    """
    if seed is not None:
        u, l, _cost = descend(p, side, target, seed[0], seed[1])
        p.set(**{f"{side}_leg_u": u, f"{side}_leg_l": l})
        return u, l
    best = None
    for u0, l0 in itertools.product((10, 25, 40, 55, 70), (-20, -45, -70, -95)):
        u, l, cost = descend(p, side, target, u0, l0)
        if best is None or cost < best[2]:
            best = (u, l, cost)
    p.set(**{f"{side}_leg_u": best[0], f"{side}_leg_l": best[1]})
    return best[0], best[1]


def solve_foot(p: Poser, side: str, want_world_angle: float):
    lo, hi = -120.0, 120.0

    def err(v):
        p.set(**{f"{side}_leg_foot": v})
        return p.solve()[f"{side}_leg_foot"].angle - want_world_angle

    e_lo = err(lo)
    for _ in range(70):
        mid = 0.5 * (lo + hi)
        e_mid = err(mid)
        if e_lo * e_mid <= 0:
            hi = mid
        else:
            lo, e_lo = mid, e_mid
    value = 0.5 * (lo + hi)
    p.set(**{f"{side}_leg_foot": value})
    return value


def pose_at(p: Poser, rest, drop: float, foot_targets=None, seed=None):
    """Leg channels for a body dropped `drop` px, both feet on the ground line.

    `foot_targets` overrides where each ankle should land — `(x, y)` per side —
    which is how the crouch WALK swings one leg while the other stays planted.
    """
    p.clear()
    p.set(root_y=drop)
    out = {"root_y": drop}
    worst = 0.0
    for side in ("far", "near"):
        target = (foot_targets or {}).get(side) or (rest[side]["ankle"][0], p.ground)
        leg_seed = None
        if seed is not None:
            leg_seed = (seed[f"{side}_leg_u"], seed[f"{side}_leg_l"])
        u, l = solve_leg(p, side, target, leg_seed)
        out[f"{side}_leg_u"], out[f"{side}_leg_l"] = u, l
        out[f"{side}_leg_foot"] = solve_foot(p, side, rest[side]["foot_angle"])
        landed = p.solve()[f"{side}_leg_foot"].origin
        worst = max(worst, abs(landed[1] - target[1]))
    out["_ankle_error"] = worst
    return out


def head_channels(amount: float, breath: float = 0.0) -> dict:
    """The head's sink and squash at `amount` of the way into the crouch.

    The squash lerps from 1.0, not from 0.0 — it is a SCALE, and easing it the
    way the angles ease would start the transition with a head of no height.
    """
    return {
        "bone.head.y": CROUCH_HEAD_SINK * amount,
        "bone.head.scale_y": 1.0 + (CROUCH_HEAD_SQUASH - 1.0) * amount + breath,
    }


def ease(t: float) -> float:
    """Smoothstep, so the fold accelerates out of the stand and settles."""
    return t * t * (3.0 - 2.0 * t)


def keyed(values):
    n = len(values)
    return {"keys": [[i / (n - 1), float(v)] for i, v in enumerate(values)]}


def build(doc: RigDocument) -> dict:
    p = Poser(doc)
    p.clear()
    rest_world = p.solve()
    rest = {
        side: {
            "ankle": rest_world[f"{side}_leg_foot"].origin,
            "foot_angle": rest_world[f"{side}_leg_foot"].angle,
        }
        for side in ("far", "near")
    }
    stand_head = rest_world["head"].origin[1]

    hold = pose_at(p, rest, CROUCH_DROP)
    p.set(**{k: v for k, v in CROUCH_SHAPE.items()})
    hold.update(head_channels(1.0))
    hold_head = p.solve()["head"].origin[1]

    report = {
        "stand_head_y": stand_head,
        "hold_head_y": hold_head,
        "head_drop": hold_head - stand_head,
        "ankle_error": hold["_ankle_error"],
        "ground": p.ground,
    }

    poses: dict[str, list[dict]] = {}

    # crouch_start / crouch_end: stand → hold, eased, and its mirror. Frame 0 is
    # the rest pose EXACTLY — solving for "the ankle where it already is" would
    # be free to answer with the other branch, and the transition would open on
    # a pop out of idle.
    rest_frame = {"root_y": 0.0, "_ankle_error": 0.0}
    for side in ("far", "near"):
        for part in ("u", "l", "foot"):
            rest_frame[f"{side}_leg_{part}"] = 0.0
    rest_frame.update(head_channels(0.0))
    start = [rest_frame]
    for i in range(1, 5):
        f = ease(i / 4.0)
        frame = pose_at(p, rest, CROUCH_DROP * f, seed=start[-1])
        frame.update({k: v * f for k, v in CROUCH_SHAPE.items()})
        frame.update(head_channels(f))
        start.append(frame)
    poses["crouch_start"] = start
    poses["crouch_end"] = list(reversed(start))

    # crouch: the HOLD, breathing. It never returns to standing — the shipped
    # loop keyed root_y back to 0 at both ends, so the character stood up inside
    # its own crouch once per cycle.
    loop = []
    for i in range(6):
        phase = math.sin(2.0 * math.pi * i / 6.0)
        frame = pose_at(p, rest, CROUCH_DROP + BREATH * phase, seed=loop[-1] if loop else hold)
        frame.update(CROUCH_SHAPE)
        frame["torso"] = CROUCH_SHAPE["torso"] + 1.2 * phase
        frame["head"] = CROUCH_SHAPE["head"] - 0.8 * phase
        frame.update(head_channels(1.0, breath=0.025 * phase))
        loop.append(frame)
    poses["crouch"] = loop

    # crouch_walk: the hold, with the feet trading places along the ground line.
    walk = []
    for i in range(8):
        phase = 2.0 * math.pi * i / 8.0
        targets = {}
        for side, offset in (("far", 0.0), ("near", math.pi)):
            swing = math.sin(phase + offset)
            lift = max(0.0, math.sin(phase + offset + math.pi / 2.0)) * STRIDE_LIFT
            targets[side] = (rest[side]["ankle"][0] + STRIDE_X * swing, p.ground - lift)
        frame = pose_at(
            p,
            rest,
            CROUCH_DROP + 0.6 * math.sin(2.0 * phase),
            targets,
            seed=walk[-1] if walk else hold,
        )
        frame.update(CROUCH_SHAPE)
        frame["far_arm_u"] = CROUCH_SHAPE["far_arm_u"] + 6.0 * math.sin(phase)
        frame["near_arm_u"] = CROUCH_SHAPE["near_arm_u"] - 6.0 * math.sin(phase)
        frame.update(head_channels(1.0, breath=0.015 * math.sin(2.0 * phase)))
        walk.append(frame)
    poses["crouch_walk"] = walk

    p.drop()

    for clip_name, frames in poses.items():
        channels = doc.data["clips"][clip_name]["channels"]
        authored = set()
        for key in list(frames[0]):
            if key.startswith("_"):
                continue
            authored.add(key)
        for key in CROUCH_SHAPE:
            authored.add(key)
        for key in authored:
            channels[key] = keyed([f.get(key, 0.0) for f in frames])
        # Every channel this family used to key and no longer sets goes to rest
        # rather than keeping a stale value from the pose it was authored for.
        for key in channels:
            if key in authored or key in ("face_open_vis", "head_look", "blink_vis"):
                continue
            if key in LEG_CHANNELS:
                continue
            # ⛔ a SCALE rests at 1.0. Sweeping it to 0.0 with the angles is a
            # head of no height, and the sweep cannot tell them apart by name.
            channels[key] = keyed([HEAD_CHANNEL_RESTS.get(key, 0.0)] * len(frames))
        doc.data["clips"][clip_name]["frames"] = len(frames)

    report["worst_ankle_error"] = max(
        f["_ankle_error"] for frames in poses.values() for f in frames
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    doc = RigDocument.load(RIG)
    report = build(doc)
    print(f"stand head y      {report['stand_head_y']:.2f}")
    print(f"crouch head y     {report['hold_head_y']:.2f}  (drop {report['head_drop']:+.2f} px)")
    print(f"ground line       {report['ground']:.2f}")
    print(f"worst ankle error {report['worst_ankle_error']:.3f} px")
    if args.dry_run:
        print("dry run — nothing written")
        return 0
    # indent=2 to match `build_player_robot_v3_svg.py`, which is what writes
    # this document from scratch. `RigDocument.save` uses indent=1, and reaching
    # for it here reformatted all 110k lines and buried the crouch in the diff.
    RIG.write_text(json.dumps(doc.data, indent=2) + "\n")
    print(f"wrote {RIG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
