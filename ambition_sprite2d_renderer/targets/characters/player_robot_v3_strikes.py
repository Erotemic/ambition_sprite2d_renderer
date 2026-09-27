"""Player Robot v3's melee strikes, keyed as body mechanics.

The rows these replace were the robot family's idle with a line drawn out of the
near hand: the body did not move, and because the near hand hangs BEHIND the
body in this three-quarter drawing, the forward slash read as a poke backwards.

A strike here is a short list of key poses, each one frame of the published
row, written in [`WorldPose`] terms — where the blade points, how far the body
leans and lunges, which way the torso has turned — and solved into channels by
[`RigBody`], which keeps the boots planted by IK. The blade is an authored SVG
part on the near hand (``blade``, shown by ``blade_vis``), so it turns with the
wrist rather than being drawn after the fact.

Poses are keyed to the MOVE's windows, not to taste: a row's frames play at the
sheet's fixed rate, so frame ``i`` of ``jab`` is on screen from ``i`` x 42 ms, and
the moveset's startup/active/recovery windows decide what each frame must show.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from ...authoring.rigdoc import RigDocument
from .player_robot_v3_body import SIDES, Arm, RigBody, WorldPose


@dataclass(frozen=True)
class Key:
    """One published frame of a strike.

    ``near``/``far`` are world angles (upper arm, forearm, BLADE direction for
    the near hand; upper arm, forearm for the off hand). ``step`` moves the
    front (far) boot forward along the floor; the back boot stays planted.
    ``blade`` is the blade's opacity; ``turn`` is which torso front shows:
    ``"open"`` (chest toward the camera, the coil), ``"profile"`` (chest turned
    toward the target, the strike), or ``None`` (the drawn three-quarter torso).
    """

    near: tuple
    far: tuple
    torso: float = 0.0
    head: float = 0.0
    lunge: float = 0.0
    drop: float = 0.0
    squash: float = 1.0
    shoulder: float = 0.0
    step: float = 0.0
    blade: float = 1.0
    turn: str | None = None
    squint: float = 0.0
    params: Dict[str, float] = field(default_factory=dict)


# The direction the blade is DRAWN in the SVG (straight ahead, so it fits the
# canvas). A key gives the blade's world direction, which is what the eye
# tracks; the wrist is turned by the difference.
BLADE_DRAWN_DEG = 0.0
TORSO_SWAP = {"open": "torso_open_vis", "profile": "torso_profile_vis"}


def _rest_key(body: RigBody) -> Key:
    near, far = body.arm_rest["near"], body.arm_rest["far"]
    return Key(near=(near.upper, near.lower, BLADE_DRAWN_DEG), far=(far.upper, far.lower), blade=0.0)


def _pose(body: RigBody, key: Key) -> Dict[str, float]:
    ankles = {}
    far_x, far_y = body.ankle_rest["far"]
    ankles["far"] = ((far_x + key.step, far_y), body.foot_rest["far"])
    pose = WorldPose(
        root_x=key.lunge,
        root_y=key.drop,
        pelvis=0.35 * key.torso,
        torso=key.torso,
        head=key.head,
        squash=key.squash,
        # The torso TURNS by sliding its shoulders: the near one comes forward
        # as the chest swings toward the target, the far one goes back.
        shoulder_dx={"near": key.shoulder, "far": -0.6 * key.shoulder},
        arms={
            "near": Arm(
                key.near[0],
                key.near[1],
                key.near[2] - BLADE_DRAWN_DEG + body.arm_rest["near"].hand,
            ),
            "far": Arm(*key.far),
        },
        ankles=ankles,
    )
    ch = body.channels(pose)
    ch["blade_vis"] = key.blade
    ch["torso_front_vis"] = 0.0 if key.turn else 1.0
    for turn, channel in TORSO_SWAP.items():
        ch[channel] = 1.0 if key.turn == turn else 0.0
    ch["eye_squint"] = key.squint
    ch.update(key.params)
    return ch


def jab_keys(body: RigBody) -> List[Key]:
    """The neutral slash: coil, cut, follow through, recover.

    Window map (``player_robot.ron`` ``jab``: 0.25 s, active 0.05-0.11) at
    42 ms a frame: 0 is the startup, 1-2 the active cut, 3-5 the recovery,
    ending on the idle pose exactly so the next row does not pop.
    """
    rest = _rest_key(body)
    return [
        # Coil: blade cocked up behind the shoulder, chest opened to the camera,
        # weight back, the off hand thrown forward for balance.
        Key(near=(-150.0, -160.0, -135.0), far=(30.0, 0.0), torso=-6.0, head=-3.0,
            lunge=-2.0, drop=2.5, squash=0.97, shoulder=-3.0, turn="open", squint=0.25),
        # Cut: the blade level at the target at CHEST height — the head is half
        # the robot, and a blade at shoulder height draws behind it. Chest swung
        # round to the target, front boot stepped in, the off arm flung back.
        Key(near=(28.0, 8.0, -2.0), far=(150.0, 120.0), torso=12.0, head=4.0,
            lunge=4.0, drop=4.0, squash=1.03, shoulder=6.0, step=4.0, turn="profile", squint=0.3),
        # Follow-through: the blade carries on forward and down, not into the floor.
        Key(near=(55.0, 34.0, 16.0), far=(160.0, 140.0), torso=14.0, head=6.0,
            lunge=5.0, drop=4.5, squash=0.96, shoulder=7.0, step=4.0, turn="profile", squint=0.2),
        # Recover: the blade is gone the moment the cut is — a blade that lingers
        # into the recovery reads as a second, slower swing.
        Key(near=(78.0, 70.0, 40.0), far=(110.0, 110.0), torso=8.0, head=3.5,
            lunge=3.0, drop=3.0, squash=0.99, shoulder=3.0, step=2.5, blade=0.0, squint=0.1),
        Key(near=(105.0, 100.0, 85.0), far=(70.0, 85.0), torso=3.0, head=1.5,
            lunge=1.0, drop=1.2, shoulder=1.0, step=1.0, blade=0.0),
        rest,
    ]


STRIKES = {"jab": jab_keys}


def _keyed(values: Sequence[float]) -> dict:
    n = len(values)
    return {"keys": [[round(i / max(1, n - 1), 6), round(float(v), 5)] for i, v in enumerate(values)]}


def author_strikes(doc: RigDocument) -> Dict[str, dict]:
    """Replace the strike clips of a built v3 rig with keyed body mechanics."""
    body = RigBody(doc)
    reports = {}
    for name, keys_for in STRIKES.items():
        clip = doc.data["clips"][name]
        keys = keys_for(body)
        if len(keys) != int(clip["frames"]):
            raise ValueError(
                f"{name}: {len(keys)} key poses for a {clip['frames']}-frame row; "
                "a key is one published frame"
            )
        frames = [_pose(body, key) for key in keys]
        channels = clip["channels"]
        for key in frames[0]:
            if key.startswith("_"):
                continue
            channels[key] = _keyed([f[key] for f in frames])
        # The borrowed clip's presentation channels no longer describe this row.
        for stale in ("slash", "slash_arc"):
            channels.pop(stale, None)
        reports[name] = {
            "max_reach": {s: round(max(f[f"_reach_{s}"] for f in frames), 3) for s in SIDES}
        }
    return reports


__all__ = ["Key", "STRIKES", "author_strikes"]
