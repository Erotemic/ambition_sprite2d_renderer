"""Mary-O's fighting rows: one row per move of her platform-fighter kit.

Her sheet drew no attack at all, so every move of her Smash kit played her
idle while its hit volume and dust played beside her. These rows are posed on
the same rigid SVG rig as her walk (``Pose`` angles: an arm or a leg at 0 hangs
down, +90 points to the front, 180 straight up; the back limbs reach behind her
at -90), so they are the same drawing in new positions.

⭐ A ROW IS SLAVED TO ITS MOVE: the game shows frame ``floor(progress *
frames)``. So each row is keyed in MOVE PROGRESS, from the move's own windows
(``mary_o.ron``): the limb is out by the time the move's first Active window
opens and stays out through it, then follows through. ``ACTIVE`` below copies
those windows; a retimed move must be retimed here too.

Mary-O is the plumber in a dress: the kicks are his (the hop kick, the drop
kick, the mule kick, the stomp), the up smash is the punch that
breaks a block over his head, the down smash is the breakdance sweep.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, List, Sequence, Tuple

from ._mary_o_v2_model import Pose

#: The bind angle of each limb: what ``None`` (the rest pose) means, so a
#: keyed pose can ease back to her idle.
REST = {
    "arm_front_angle": 1.8,
    "arm_back_angle": 0.5,
    "leg_front_angle": 19.2,
    "leg_back_angle": 14.9,
}

_NUMERIC = [f.name for f in dataclasses.fields(Pose) if f.name != "mode"]


def _value(pose: Pose, name: str) -> float:
    v = getattr(pose, name)
    if v is None:
        return REST.get(name, 0.0)
    return float(v)


def _lerp(a: Pose, b: Pose, u: float) -> Pose:
    u = max(0.0, min(1.0, u))
    # Smoothstep: a limb gets going and settles, it does not tick.
    u = u * u * (3.0 - 2.0 * u)
    out = {n: _value(a, n) + (_value(b, n) - _value(a, n)) * u for n in _NUMERIC}
    return Pose(mode=a.mode if u < 0.5 else b.mode, **out)


def keyed(keys: Sequence[Tuple[float, Pose]], frames: int) -> List[Pose]:
    """``frames`` poses for a row, sampling ``keys`` (move progress -> pose) at
    the middle of each frame's share of the move."""
    out = []
    for i in range(frames):
        t = (i + 0.5) / frames
        if t <= keys[0][0]:
            out.append(_lerp(keys[0][1], keys[0][1], 0.0))
            continue
        for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
            if t0 <= t <= t1:
                out.append(_lerp(p0, p1, (t - t0) / max(1e-6, t1 - t0)))
                break
        else:
            out.append(_lerp(keys[-1][1], keys[-1][1], 0.0))
    return out


IDLE = Pose(**{k: v for k, v in REST.items()})

#: (move duration s, first Active start s, last Active end s), from `mary_o.ron`.
ACTIVE = {
    "jab": (0.23, 0.05, 0.10),
    "attack_side": (0.30, 0.07, 0.14),
    "attack_up": (0.30, 0.07, 0.14),
    "attack_down": (0.29, 0.06, 0.13),
    "smash_forward": (0.53, 0.16, 0.25),
    "smash_up": (0.52, 0.15, 0.25),
    "smash_down": (0.56, 0.17, 0.26),
    "air_neutral": (0.32, 0.06, 0.17),
    "air_forward": (0.33, 0.08, 0.16),
    "air_back": (0.34, 0.09, 0.15),
    "air_up": (0.31, 0.07, 0.15),
    "air_down": (0.38, 0.09, 0.18),
    "dash_attack": (0.40, 0.05, 0.14),
    "fireball": (0.56, 0.14, 0.24),
    "cape_spin": (0.54, 0.12, 0.22),
    "spring_jump": (0.46, 0.06, 0.18),
    "pipe_drop": (0.62, 0.16, 0.25),
    "pipe_dive": (0.41, 0.09, 0.19),
    "grab": (0.31, 0.07, 0.12),
}


def _window(row: str) -> Tuple[float, float]:
    dur, a0, a1 = ACTIVE[row]
    return a0 / dur, a1 / dur


def _strike(row: str, windup: Pose, out: Pose, follow: Pose, *, recover: Pose = IDLE,
            lead: float = 0.06, settle: float = 0.9) -> List[Tuple[float, Pose]]:
    """The common shape of a hit: wind up, be OUT a little before the window
    opens and hold through it, follow through, settle."""
    a0, a1 = _window(row)
    return [
        (0.0, IDLE),
        (max(0.02, a0 * 0.55), windup),
        (max(a0 * 0.75, a0 - lead), out),
        (a1, out),
        (min(0.97, a1 + (settle - a1) * 0.45), follow),
        (settle, recover),
        (1.0, recover),
    ]


def _frames(row: str) -> int:
    """About 25 frames a second of the move, and never fewer than 5."""
    dur = ACTIVE[row][0]
    return max(5, round(dur / 0.04))


P = Pose
_KEYS: Dict[str, List[Tuple[float, Pose]]] = {
    # Jab, the hop kick: the front foot snaps out at hip height.
    "jab": _strike(
        "jab",
        windup=P(body_lean=-0.4, leg_front_angle=48, leg_back_angle=-8, arm_front_angle=30, arm_back_angle=-30),
        out=P(body_lean=-0.9, leg_front_angle=116, leg_back_angle=-4, arm_front_angle=-25, arm_back_angle=-60),
        follow=P(body_lean=-0.5, leg_front_angle=60, leg_back_angle=-6, arm_front_angle=0, arm_back_angle=-30),
    ),
    # Forward tilt, the sweep kick: a lower, longer kick, the body behind it.
    "attack_side": _strike(
        "attack_side",
        windup=P(body_lean=-0.6, leg_front_angle=-20, leg_back_angle=10, arm_front_angle=40, arm_back_angle=-20),
        out=P(body_lean=-1.2, leg_front_angle=104, leg_back_angle=-30, arm_front_angle=-35, arm_back_angle=-80),
        follow=P(body_lean=-0.6, leg_front_angle=70, leg_back_angle=-10, arm_front_angle=-10, arm_back_angle=-40),
    ),
    # Up tilt, the header: she springs up and drives the crown of her cap.
    "attack_up": _strike(
        "attack_up",
        windup=P(bob=1.2, body_lean=0.4, leg_front_angle=30, leg_back_angle=-12, arm_front_angle=-30, arm_back_angle=-40),
        out=P(body_lean=0.6, head_dx=0.8, head_dy=-2.6, leg_front_angle=24, leg_back_angle=4, arm_front_angle=-50, arm_back_angle=-70),
        follow=P(head_dy=-1.2, leg_front_angle=20, leg_back_angle=8, arm_front_angle=-20, arm_back_angle=-40),
    ),
    # Down tilt, the slide: down low, the front foot skimming the floor.
    "attack_down": _strike(
        "attack_down",
        windup=P(bob=1.4, body_lean=0.6, leg_front_angle=40, leg_back_angle=-30, arm_front_angle=40, arm_back_angle=-40),
        out=P(body_lean=-1.0, leg_front_angle=108, leg_back_angle=-62, arm_front_angle=60, arm_back_angle=-80),
        follow=P(body_lean=-0.6, leg_front_angle=88, leg_back_angle=-46, arm_front_angle=40, arm_back_angle=-60),
    ),
    # Forward smash: the front leg cocked back, then a full drive kick.
    "smash_forward": _strike(
        "smash_forward",
        windup=P(body_lean=0.6, bob=0.6, leg_front_angle=-40, leg_back_angle=20, arm_front_angle=60, arm_back_angle=30),
        out=P(body_lean=-1.4, leg_front_angle=122, leg_back_angle=-26, arm_front_angle=-40, arm_back_angle=-95),
        follow=P(body_lean=-0.8, leg_front_angle=92, leg_back_angle=-14, arm_front_angle=-20, arm_back_angle=-60),
        lead=0.08,
    ),
    # Up smash, the block punch: crouch, then the fist straight up.
    "smash_up": _strike(
        "smash_up",
        windup=P(bob=2.0, body_lean=0.3, leg_front_angle=34, leg_back_angle=-20, arm_front_angle=20, arm_back_angle=-30),
        out=P(bob=-3.0, head_dy=-0.4, leg_front_angle=10, leg_back_angle=-4, arm_front_angle=178, arm_back_angle=-30),
        follow=P(bob=-1.6, leg_front_angle=14, leg_back_angle=2, arm_front_angle=160, arm_back_angle=-20),
        lead=0.08,
    ),
    # Down smash, the breakdance sweep: low, both legs out, front and back.
    "smash_down": _strike(
        "smash_down",
        windup=P(bob=1.8, leg_front_angle=40, leg_back_angle=-34, arm_front_angle=60, arm_back_angle=-60),
        out=P(leg_front_angle=112, leg_back_angle=-96, arm_front_angle=40, arm_back_angle=-40),
        follow=P(leg_front_angle=86, leg_back_angle=-80, arm_front_angle=50, arm_back_angle=-50),
        lead=0.08,
    ),
    # Neutral air: a star, every limb out, which is what hits all around her.
    "air_neutral": _strike(
        "air_neutral",
        windup=P(bob=-0.6, leg_front_angle=40, leg_back_angle=-30, arm_front_angle=60, arm_back_angle=-60),
        out=P(leg_front_angle=90, leg_back_angle=-80, arm_front_angle=120, arm_back_angle=-120),
        follow=P(bob=-0.8, leg_front_angle=50, leg_back_angle=-50, arm_front_angle=100, arm_back_angle=-100),
        recover=P(bob=-1.0, leg_front_angle=45, leg_back_angle=-32, arm_front_angle=148, arm_back_angle=-22),
    ),
    # Forward air, the drop kick: both feet to the front, the body laid back.
    "air_forward": _strike(
        "air_forward",
        windup=P(bob=-1.0, body_lean=0.6, leg_front_angle=20, leg_back_angle=-30, arm_front_angle=120, arm_back_angle=-20),
        out=P(body_lean=-1.6, leg_front_angle=116, leg_back_angle=104, arm_front_angle=150, arm_back_angle=-120),
        follow=P(bob=-1.4, body_lean=-1.0, leg_front_angle=70, leg_back_angle=50, arm_front_angle=140, arm_back_angle=-80),
        recover=P(bob=-1.0, leg_front_angle=45, leg_back_angle=-32, arm_front_angle=148, arm_back_angle=-22),
    ),
    # Back air, the mule kick: the back leg straight out behind her.
    "air_back": _strike(
        "air_back",
        windup=P(bob=-1.0, body_lean=-0.4, leg_front_angle=40, leg_back_angle=10, arm_front_angle=80, arm_back_angle=20),
        out=P(body_lean=1.2, leg_front_angle=40, leg_back_angle=-108, arm_front_angle=100, arm_back_angle=60),
        follow=P(bob=-1.0, body_lean=0.6, leg_front_angle=34, leg_back_angle=-70, arm_front_angle=110, arm_back_angle=20),
        recover=P(bob=-1.0, leg_front_angle=45, leg_back_angle=-32, arm_front_angle=148, arm_back_angle=-22),
    ),
    # Up air: the flip kick's feet would go up behind her dress (a leg past
    # ~115 degrees is hidden by it), so the strike over her head is both hands,
    # thrown up out of a tuck.
    "air_up": _strike(
        "air_up",
        windup=P(leg_front_angle=70, leg_back_angle=-50, arm_front_angle=20, arm_back_angle=-30),
        out=P(leg_front_angle=40, leg_back_angle=-30, arm_front_angle=176, arm_back_angle=-168, head_dy=-0.6),
        follow=P(leg_front_angle=44, leg_back_angle=-32, arm_front_angle=160, arm_back_angle=-140),
        recover=P(leg_front_angle=45, leg_back_angle=-32, arm_front_angle=148, arm_back_angle=-22),
    ),
    # Down air, the stomp: both feet driven straight down, arms thrown up.
    "air_down": _strike(
        "air_down",
        windup=P(bob=-2.0, leg_front_angle=60, leg_back_angle=40, arm_front_angle=60, arm_back_angle=-60),
        out=P(bob=-0.4, leg_front_angle=4, leg_back_angle=-4, arm_front_angle=165, arm_back_angle=-165),
        follow=P(bob=-0.6, leg_front_angle=10, leg_back_angle=-8, arm_front_angle=150, arm_back_angle=-150),
        recover=P(bob=-1.0, leg_front_angle=45, leg_back_angle=-32, arm_front_angle=148, arm_back_angle=-22),
    ),
    # Dash attack, a flying kick out of the run.
    "dash_attack": _strike(
        "dash_attack",
        windup=P(body_lean=1.0, leg_front_angle=30, leg_back_angle=-30, arm_front_angle=-20, arm_back_angle=20),
        out=P(body_lean=-0.8, leg_front_angle=114, leg_back_angle=-50, arm_front_angle=120, arm_back_angle=-90),
        follow=P(body_lean=-0.4, bob=-0.8, leg_front_angle=70, leg_back_angle=-30, arm_front_angle=80, arm_back_angle=-60),
        lead=0.03,
    ),
    # Neutral special, the fireball: the throwing hand to the front.
    "fireball": _strike(
        "fireball",
        windup=P(mode="fireball", body_lean=-0.6, arm_front_angle=-30, arm_back_angle=30, leg_front_dx=0.2),
        out=P(mode="fireball", body_lean=0.9, arm_front_angle=94, arm_back_angle=-40, leg_front_dx=1.0, leg_back_dx=-0.5),
        follow=P(mode="fireball", body_lean=0.6, arm_front_angle=76, arm_back_angle=-24, leg_front_dx=0.8, leg_back_dx=-0.3),
    ),
    # Side special, the cape: the arm sweeps the cape across her front.
    "cape_spin": _strike(
        "cape_spin",
        windup=P(body_lean=-0.8, arm_front_angle=-60, arm_back_angle=-80, leg_front_angle=30, leg_back_angle=-14),
        out=P(body_lean=1.0, arm_front_angle=100, arm_back_angle=80, leg_front_angle=36, leg_back_angle=-22),
        follow=P(body_lean=0.8, arm_front_angle=140, arm_back_angle=100, leg_front_angle=30, leg_back_angle=-18),
    ),
    # Up special, the spring jump: the uppercut that carries her up.
    "spring_jump": _strike(
        "spring_jump",
        windup=P(bob=1.6, leg_front_angle=34, leg_back_angle=-20, arm_front_angle=10, arm_back_angle=-30),
        out=P(bob=-2.6, leg_front_angle=40, leg_back_angle=-10, arm_front_angle=172, arm_back_angle=-40),
        follow=P(bob=-2.0, leg_front_angle=50, leg_back_angle=-20, arm_front_angle=160, arm_back_angle=-30),
        recover=P(bob=-1.0, leg_front_angle=45, leg_back_angle=-32, arm_front_angle=148, arm_back_angle=-22),
        lead=0.03,
    ),
    # Down special on the ground, the pipe drop: a squat and a slam, both feet.
    "pipe_drop": _strike(
        "pipe_drop",
        windup=P(bob=-2.0, leg_front_angle=50, leg_back_angle=-40, arm_front_angle=160, arm_back_angle=-160),
        out=P(leg_front_angle=76, leg_back_angle=-66, arm_front_angle=70, arm_back_angle=-70),
        follow=P(bob=2.4, leg_front_angle=44, leg_back_angle=-44, arm_front_angle=50, arm_back_angle=-50),
    ),
    # Down special in the air, the pipe dive: straight down like a pipe.
    "pipe_dive": _strike(
        "pipe_dive",
        windup=P(bob=-2.0, leg_front_angle=50, leg_back_angle=-30, arm_front_angle=120, arm_back_angle=-120),
        out=P(bob=-0.6, leg_front_angle=2, leg_back_angle=-2, arm_front_angle=178, arm_back_angle=-178),
        follow=P(bob=-0.6, leg_front_angle=4, leg_back_angle=-4, arm_front_angle=175, arm_back_angle=-175),
        recover=P(bob=-1.0, leg_front_angle=45, leg_back_angle=-32, arm_front_angle=148, arm_back_angle=-22),
    ),
    # The grab: both hands out at chest height.
    "grab": _strike(
        "grab",
        windup=P(body_lean=-0.4, arm_front_angle=40, arm_back_angle=30),
        out=P(body_lean=1.0, arm_front_angle=92, arm_back_angle=86, leg_front_angle=30, leg_back_angle=-16),
        follow=P(body_lean=0.6, arm_front_angle=70, arm_back_angle=64, leg_front_angle=24, leg_back_angle=-6),
    ),
}

#: The rows whose frames hold a pose rather than strike: the held victim, the
#: charge, the throws. (name, frames, poses)
_HELD: Dict[str, List[Pose]] = {
    "grab_hold": [P(body_lean=0.6, arm_front_angle=80, arm_back_angle=74, leg_front_angle=26, leg_back_angle=-10)],
    "pummel": [
        P(body_lean=0.6, arm_front_angle=80, arm_back_angle=74, leg_front_angle=26, leg_back_angle=-10),
        P(body_lean=0.9, bob=-0.6, arm_front_angle=80, arm_back_angle=74, leg_front_angle=80, leg_back_angle=-10),
        P(body_lean=0.6, arm_front_angle=80, arm_back_angle=74, leg_front_angle=30, leg_back_angle=-10),
    ],
    "throw_forward": [
        P(body_lean=0.3, arm_front_angle=80, arm_back_angle=70),
        P(body_lean=1.4, arm_front_angle=96, arm_back_angle=96, leg_front_angle=40, leg_back_angle=-26),
        P(body_lean=0.8, arm_front_angle=60, arm_back_angle=50, leg_front_angle=30, leg_back_angle=-16),
    ],
    "throw_back": [
        P(body_lean=0.3, arm_front_angle=80, arm_back_angle=70),
        P(body_lean=-1.2, arm_front_angle=140, arm_back_angle=-100, leg_front_angle=30, leg_back_angle=-30),
        P(body_lean=-0.8, arm_front_angle=40, arm_back_angle=-80, leg_front_angle=24, leg_back_angle=-20),
    ],
    "throw_up": [
        P(bob=1.0, arm_front_angle=80, arm_back_angle=70, leg_front_angle=34, leg_back_angle=-20),
        P(bob=-1.6, arm_front_angle=176, arm_back_angle=-176, leg_front_angle=10, leg_back_angle=-6),
        P(bob=-0.8, arm_front_angle=150, arm_back_angle=-150),
    ],
    "throw_down": [
        P(bob=-0.6, arm_front_angle=150, arm_back_angle=-150),
        P(bob=2.4, arm_front_angle=40, arm_back_angle=-40, leg_front_angle=50, leg_back_angle=-40),
        P(bob=1.4, arm_front_angle=20, arm_back_angle=-20, leg_front_angle=34, leg_back_angle=-24),
    ],
    # The smash charge: the wound-up crouch, quivering.
    "smash_charge": [
        P(bob=1.4, body_lean=0.4, leg_front_angle=30, leg_back_angle=-20, arm_front_angle=40, arm_back_angle=-50),
        P(bob=1.7, body_lean=0.5, leg_front_angle=32, leg_back_angle=-22, arm_front_angle=44, arm_back_angle=-54),
    ],
    # The taunt: a thumbs-up and a wink... as near as a rigid arm gets.
    "taunt": [
        P(arm_front_angle=60, arm_back_angle=-10),
        P(bob=-0.4, arm_front_angle=150, arm_back_angle=-20, head_dy=-0.2),
        P(bob=-0.4, arm_front_angle=160, arm_back_angle=-20, head_dy=-0.2),
        P(arm_front_angle=60, arm_back_angle=-10),
    ],
}

_HELD_MS = {
    "grab_hold": 160, "pummel": 66, "throw_forward": 85, "throw_back": 90,
    "throw_up": 87, "throw_down": 93, "smash_charge": 120, "taunt": 225,
}


def attack_poses() -> Dict[str, List[Pose]]:
    poses = {row: keyed(keys, _frames(row)) for row, keys in _KEYS.items()}
    poses.update(_HELD)
    return poses


def attack_rows() -> List[Tuple[str, int, int]]:
    rows = [(row, _frames(row), round(ACTIVE[row][0] * 1000 / _frames(row))) for row in _KEYS]
    rows += [(row, len(p), _HELD_MS[row]) for row, p in _HELD.items()]
    return rows
