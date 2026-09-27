"""Player Robot v3's walk and run, solved from foot paths rather than joint waves.

The rows this replaces were one sine per joint, borrowed from the robot family:
the feet never planted, so they slid; the knees never loaded, so the body never
carried weight; and the run was the walk with larger numbers. Here a gait is a
handful of physical facts — how long a foot stays down, how far it sweeps, how
high it clears, where the body is lowest — and the joints are SOLVED from them:

* each ankle follows a path relative to its own hip: a stance sweep at constant
  speed (heel strike, flat, toe-off, each rolling about the point of the boot
  that is actually on the ground) and a swing arc back to the next contact;
* two-bone IK places the knee under that ankle, so a loaded leg bends and the
  planted boot stays on the ground line;
* the pelvis is lowest just after contact and highest where the weight is off
  (passing for a walk, flight for a run); the torso squashes and stretches with
  it, and carries the head and shoulders down by exactly the amount it squashes;
* the arms counter-swing the legs, and the forearms trail the upper arms;
* the head is FOLLOW-THROUGH: its nod lags the body's bob.

The antenna stays rigid on the head, by ruling: a spring-driven antenna was
built and rejected as too distracting on the character the player watches most.

The player crosses the world at up to 270 units/s — about five of their heights a
second — so no cadence their 20 px legs can manage keeps a stance boot locked to
the floor in game. What the solve buys instead is a boot that sweeps back at one
constant speed while it is down, which the eye reads as planted, and poses that
are unambiguous at a glance: the contact, the load, the pass, the push.

Data plus maths: the rig builder calls ``author_gaits`` after it has built the
document, and nothing here touches the filesystem.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from ...authoring.rigdoc import RigDocument
from .player_robot_v3_body import SIDES, Arm, RigBody, WorldPose, about

Point = Tuple[float, float]

# A foot's contact phase; the other foot is half a cycle behind.
CONTACT_PHASE = {"near": 0.0, "far": 0.5}
# Where each foot's stride is centred, relative to its OWN hip. The standing
# art splays the near boot 8.7 px behind its hip for the three-quarter view;
# centring the stride on that splay kept the near foot behind the body for the
# whole cycle, so it never visibly stepped forward.
TRACK_FROM_HIP = {"near": -2.5, "far": -1.0}


@dataclass(frozen=True)
class Gait:
    """One locomotion cycle, in frame pixels, degrees, and cycle fractions.

    Frame count and timing are NOT here: they are the row's, declared once in
    ``ROBOT_ROWS``, and the solve reads them off the clip.
    """

    # Fraction of the cycle each foot is on the ground. Above 0.5 both feet are
    # down at once (a walk); below it the body flies between steps (a run).
    duty: float
    # How far the pelvis sits below its standing height, so a stance leg has a
    # bent knee to load and room to sweep.
    drop: float
    # Pelvis travel from its lowest point to its highest.
    bob: float
    # Where, after a contact, the body is lowest (the "down" pose).
    low_after_contact: float
    # Ankle x relative to the stride centre (see TRACK_FROM_HIP), at contact
    # and at lift-off.
    reach_front: float
    reach_back: float
    # Swing clearance, and where in the swing the foot is highest.
    lift: float
    lift_peak: float
    # Toe-up at heel strike, heel-up at toe-off, extra toe-point mid swing.
    heel_strike: float
    toe_off: float
    swing_point: float
    # Torso: forward lean, the extra lean at the load, and the squash there.
    lean: float
    lean_load: float
    squash: float
    # Pelvis roll with the steps.
    pelvis_roll: float
    # Arms: upper-arm centre and swing (world degrees, 90 = hanging), elbow
    # bend (negative folds the forearm forward), extra bend on the forward swing,
    # and how far behind the legs the arms and forearms run.
    arm_center: float
    arm_swing: float
    elbow_bend: float
    elbow_pump: float
    arm_lag: float
    forearm_lag: float
    # Head: how much of the torso's lean it cancels, its nod, and its lag.
    head_level: float
    head_nod: float
    head_drop: float
    head_lag: float
    eye_squint: float


WALK = Gait(
    duty=0.60,
    drop=3.2,
    bob=1.6,
    low_after_contact=0.08,
    reach_front=6.5,
    reach_back=-6.5,
    lift=4.2,
    lift_peak=0.45,
    heel_strike=14.0,
    toe_off=22.0,
    swing_point=6.0,
    lean=3.0,
    lean_load=1.2,
    squash=0.025,
    pelvis_roll=2.0,
    arm_center=92.0,
    arm_swing=24.0,
    elbow_bend=-14.0,
    elbow_pump=-18.0,
    arm_lag=0.04,
    forearm_lag=0.08,
    head_level=0.5,
    head_nod=2.0,
    head_drop=0.6,
    head_lag=0.07,
    eye_squint=0.04,
)

RUN = Gait(
    duty=0.36,
    drop=4.6,
    bob=3.4,
    low_after_contact=0.10,
    reach_front=9.0,
    reach_back=-10.0,
    lift=8.5,
    lift_peak=0.38,
    heel_strike=10.0,
    toe_off=34.0,
    swing_point=18.0,
    lean=11.0,
    lean_load=2.5,
    squash=0.055,
    pelvis_roll=3.5,
    arm_center=96.0,
    arm_swing=52.0,
    elbow_bend=-78.0,
    elbow_pump=-16.0,
    arm_lag=0.03,
    forearm_lag=0.07,
    head_level=0.55,
    head_nod=3.0,
    head_drop=1.2,
    head_lag=0.06,
    eye_squint=0.16,
)

GAITS: Dict[str, Gait] = {"walk": WALK, "run": RUN}

def _smoother(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _foot(body: RigBody, gait: Gait, side: str, phase: float) -> Tuple[Point, float]:
    """Ankle position and foot world angle at `phase`."""
    p = (phase - CONTACT_PHASE[side]) % 1.0
    rest_x = body.hip_rest[side][0] + TRACK_FROM_HIP[side]
    rest_y = body.ankle_rest[side][1]
    flat_angle = body.foot_rest[side]
    # The far leg is drawn 18% shorter (it is further away); its stride is too.
    scale = sum(body.leg[side]) / max(sum(body.leg[s]) for s in SIDES)

    def stance(s: float) -> Tuple[Point, float]:
        flat = (rest_x + scale * _lerp(gait.reach_front, gait.reach_back, s), rest_y)
        strike = 0.18
        push = 0.66
        if s < strike:
            delta = -gait.heel_strike * (1.0 - _smoother(s / strike))
            pivot = body.foot_point(body.heel[side], flat, flat_angle)
        elif s > push:
            delta = gait.toe_off * _smoother((s - push) / (1.0 - push))
            pivot = body.foot_point(body.toe[side], flat, flat_angle)
        else:
            return flat, flat_angle
        return about(flat, pivot, delta), flat_angle + delta

    if p < gait.duty:
        return stance(p / gait.duty)

    u = (p - gait.duty) / (1.0 - gait.duty)
    (x0, y0), a0 = stance(1.0)
    (x1, y1), a1 = stance(0.0)
    along = _smoother(u)
    # The clearance peaks at `lift_peak` of the swing: early for a run, where
    # the heel kicks up behind before the knee drives through.
    k = math.log(0.5) / math.log(max(1e-3, gait.lift_peak))
    rise = math.sin(math.pi * (u ** k))
    x = _lerp(x0, x1, along)
    y = _lerp(y0, y1, u) - gait.lift * rise
    angle = _lerp(a0, a1, along) + gait.swing_point * rise * (1.0 - u)
    return (x, y), angle


def _pose(body: RigBody, gait: Gait, phase: float) -> Dict[str, float]:
    """The body at `phase`, as rig channels."""
    tau = 2.0 * math.pi
    low = gait.low_after_contact
    # Two steps per cycle: every bob-shaped curve runs at twice the cycle rate.
    load = math.cos(2.0 * tau * (phase - low))  # +1 at the load, -1 at the lift
    head_load = math.cos(2.0 * tau * (phase - low - gait.head_lag))
    torso = gait.lean + gait.lean_load * max(0.0, load)
    pose = WorldPose(
        root_y=gait.drop + 0.5 * gait.bob * load,
        pelvis=0.3 * gait.lean + gait.pelvis_roll * math.sin(tau * phase),
        torso=torso,
        head=torso * (1.0 - gait.head_level) + gait.head_nod * head_load,
        squash=1.0 - gait.squash * load,
        head_dy=gait.head_drop * head_load,
        ankles={side: _foot(body, gait, side, phase) for side in SIDES},
    )
    # Arms counter-swing: the near arm is back while the near foot is forward.
    for side, sign in (("near", 1.0), ("far", -1.0)):
        swing = math.cos(tau * (phase - gait.arm_lag)) * sign
        trail = math.cos(tau * (phase - gait.forearm_lag)) * sign
        upper = gait.arm_center + gait.arm_swing * swing
        lower = upper + gait.elbow_bend + gait.elbow_pump * max(0.0, -trail)
        pose.arms[side] = Arm(upper, lower)
    return body.channels(pose)


def solve_gait(
    doc: RigDocument, gait: Gait, frame_count: int
) -> Tuple[Dict[str, List[float]], dict]:
    """Per-frame channel values for one looping gait, and a report."""
    body = RigBody(doc)
    phases = [i / frame_count for i in range(frame_count)]
    frames = [_pose(body, gait, ph) for ph in phases]
    channels: Dict[str, List[float]] = {}
    for key in frames[0]:
        if key.startswith("_"):
            continue
        channels[key] = [f[key] for f in frames]
    channels["eye_squint"] = [gait.eye_squint] * frame_count
    # The worst reach over a dense sweep, not only the published frames: a
    # straightened leg between two frames is invisible here and visible in game.
    dense = [_pose(body, gait, i / 256.0) for i in range(256)]
    reach = {s: round(max(f[f"_reach_{s}"] for f in dense), 3) for s in SIDES}
    return channels, {"max_reach": reach}


def author_gaits(doc: RigDocument) -> Dict[str, dict]:
    """Replace the walk and run clips of a built v3 rig with solved gaits."""
    reports = {}
    for name, gait in GAITS.items():
        clip = doc.data["clips"][name]
        n = int(clip["frames"])
        values, report = solve_gait(doc, gait, n)
        channels = clip["channels"]
        times = [i / n for i in range(n)] + [1.0]
        for key, series in values.items():
            channels[key] = {
                "keys": [
                    [round(t, 6), round(float(v), 5)]
                    for t, v in zip(times, series + [series[0]])
                ]
            }
        reports[name] = report
    return reports


__all__ = ["GAITS", "Gait", "RUN", "WALK", "author_gaits", "solve_gait"]
