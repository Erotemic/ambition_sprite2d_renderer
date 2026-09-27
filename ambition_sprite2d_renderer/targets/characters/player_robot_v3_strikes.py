"""Player Robot v3's moveset, keyed as body mechanics on the MOVE's timeline.

The rows these replace were the robot family's idle with a line drawn out of the
near hand: the body did not move, the aerials stood on the floor, and because
the near hand hangs BEHIND the body in this three-quarter drawing, a forward
slash read as a poke backwards.

A strike is a few key poses placed at PHASES of its move — the start of the
active window, the end of it, the end of the move — written in [`WorldPose`]
terms: where the blade points, how far the body leans and lunges, which way the
torso has turned, where each boot is. Published frames are sampled BETWEEN the
keys, so a row's frame count buys smoothness and never moves a beat.

That only holds because the runtime draws a move's row at the move's progress
(`ClipRequest::for_move`): frame ``i`` of an ``n``-frame row is on screen for
phases ``[i/n, (i+1)/n)`` whatever the sheet's frame duration says. Each frame
is therefore posed at the CENTRE of that span.

The blade is an authored SVG part on the near hand (``blade``, shown by
``blade_vis``); the torso's turn is a swap between ``torso_front`` and the
``torso_open`` / ``torso_profile`` fronts. Phases below are copied from
``game/ambition_content/assets/data/movesets/player_robot.ron`` (window edge /
duration) and say so where they are used.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ...authoring.rigdoc import RigDocument
from .player_robot_v3_body import SIDES, Arm, RigBody, WorldPose

# A foot's placement: (dx, lift, pitch) — along the floor from its standing
# ankle, up from the floor, and toe-down degrees on top of its standing angle.
Foot = Tuple[float, float, float]


@dataclass(frozen=True)
class Key:
    """One key pose of a strike, at ``at`` (0..1) of its move.

    ``near`` is (upper arm, forearm, BLADE) in world degrees — 0 is straight
    ahead, 90 straight down, -90 straight up; ``far`` is the off arm's (upper,
    forearm). ``feet`` places boots (see `Foot`); on the ground an unlisted boot
    stays planted where it stands, in the ``air`` every boot is relative to the
    body, so a tuck travels with it. ``turn`` picks the torso front:
    ``"open"`` (chest to the camera, a wind-up), ``"profile"`` (chest turned to
    the target, a strike) or ``None``. ``ease`` shapes the approach INTO this
    key: ``"out"`` arrives fast and settles (a cut), ``"in"`` gathers (a
    wind-up), ``"smooth"`` both, ``"linear"`` neither (a spin).
    """

    at: float
    near: Tuple[float, float, float]
    far: Tuple[float, float]
    torso: float = 0.0
    head: float = 0.0
    lunge: float = 0.0
    drop: float = 0.0
    squash: float = 1.0
    shoulder: float = 0.0
    feet: Dict[str, Foot] = field(default_factory=dict)
    air: bool = False
    blade: float = 1.0
    turn: Optional[str] = None
    squint: float = 0.0
    ease: str = "smooth"
    # The face: "open", "fierce", "strain" or "blink" (the closed ^^ arcs);
    # `None` means fierce while the blade is out and open otherwise.
    face: Optional[str] = None
    # The head turned to look behind (the back air), mirrored about the neck.
    look_back: bool = False


# The direction the blade is DRAWN in the SVG (straight ahead, so it fits the
# canvas). A key gives the blade's world direction, which is what the eye
# tracks; the wrist is turned by the difference.
BLADE_DRAWN_DEG = 0.0
TORSO_SWAP = {"open": "torso_open_vis", "profile": "torso_profile_vis"}
# One opacity channel per authored face; exactly one shows.
FACES = {
    "open": "face_open_vis",
    "blink": "blink_vis",
    "fierce": "face_fierce_vis",
    "strain": "face_strain_vis",
}
# Airborne rows lift the body this far and tuck the boots under it: the jump and
# fall rows ride above the feet anchor by about as much.
AIR_RISE = -5.0
TUCK: Dict[str, Foot] = {"near": (-4.0, 11.0, 25.0), "far": (3.0, 13.0, 20.0)}

_EASES: Dict[str, Callable[[float], float]] = {
    "linear": lambda u: u,
    "smooth": lambda u: u * u * (3.0 - 2.0 * u),
    "out": lambda u: 1.0 - (1.0 - u) ** 3,
    "in": lambda u: u ** 3,
}


def rest(body: RigBody, at: float, *, air: bool = False) -> Key:
    """The idle pose (or the airborne tuck) with the blade stowed."""
    near, far = body.arm_rest["near"], body.arm_rest["far"]
    return Key(
        at=at,
        near=(near.upper, near.lower, BLADE_DRAWN_DEG),
        far=(far.upper, far.lower),
        blade=0.0,
        air=air,
        drop=AIR_RISE if air else 0.0,
        feet=dict(TUCK) if air else {},
        # Arriving at rest ends a move: hold the recovery pose, settle late. A
        # smooth approach read as the move being over two frames early.
        ease="in",
    )


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _blend(a: Key, b: Key, u: float) -> Key:
    """The pose `u` of the way from `a` to `b` (u already eased)."""

    def num(name: str) -> float:
        return _lerp(getattr(a, name), getattr(b, name), u)

    def feet(side: str) -> Foot:
        def one(key: Key) -> Foot:
            return key.feet.get(side, (0.0, 0.0, 0.0))

        fa, fb = one(a), one(b)
        return tuple(_lerp(x, y, u) for x, y in zip(fa, fb))  # type: ignore[return-value]

    nearest = a if u < 0.5 else b
    near = tuple(_lerp(x, y, u) for x, y in zip(a.near, b.near))
    blade = num("blade")
    # The blade IGNITES pointing where it is going and GOES OUT where it was.
    # Blended through the stowed pose instead, a blade fading in from idle
    # swept through the floor on its way to the wind-up.
    if a.blade <= 0.0 < b.blade:
        near = near[:2] + (b.near[2],)
        blade = b.blade
    elif b.blade <= 0.0 < a.blade:
        near = near[:2] + (a.near[2],)
        blade = a.blade if u < 0.5 else 0.0
    return Key(
        at=_lerp(a.at, b.at, u),
        near=near,  # type: ignore[arg-type]
        far=tuple(_lerp(x, y, u) for x, y in zip(a.far, b.far)),  # type: ignore[arg-type]
        torso=num("torso"),
        head=num("head"),
        lunge=num("lunge"),
        drop=num("drop"),
        squash=num("squash"),
        shoulder=num("shoulder"),
        feet={side: feet(side) for side in SIDES},
        # A body is airborne or it is not; the boots' frame of reference does
        # not blend. Ground and air keys never share a row.
        air=a.air,
        blade=blade,
        turn=nearest.turn,
        squint=num("squint"),
        face=nearest.face,
        look_back=nearest.look_back,
    )


def sample(keys: Sequence[Key], phase: float) -> Key:
    """The pose at `phase`, eased into whichever key comes next."""
    if phase <= keys[0].at:
        return keys[0]
    for a, b in zip(keys, keys[1:]):
        if phase <= b.at:
            span = max(1e-6, b.at - a.at)
            return _blend(a, b, _EASES[b.ease]((phase - a.at) / span))
    return keys[-1]


def _pose(body: RigBody, key: Key) -> Dict[str, float]:
    ankles = {}
    for side in SIDES:
        dx, lift, pitch = key.feet.get(side, (0.0, 0.0, 0.0))
        x, y = body.ankle_rest[side]
        if key.air:
            # The boots ride with the body.
            x += key.lunge
            y += key.drop
        ankles[side] = ((x + dx, y - lift), body.foot_rest[side] + pitch)
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
    face = key.face or ("fierce" if key.blade > 0.0 else "open")
    for name, channel in FACES.items():
        ch[channel] = 1.0 if face == name else 0.0
    # Looking back is the head seen from its OTHER side: shell, ear cup,
    # antenna and face mirrored together about the neck. Squashing the visor
    # onto the back of the shell instead kept its forward-facing slant and read
    # as a flattened face, not a turned head.
    ch["bone.head.flip_x"] = 1.0 if key.look_back else 0.0
    # ...and a head seen from its other side wears the antenna on the far ear.
    ch["antenna_near_vis"] = 0.0 if key.look_back else 1.0
    ch["antenna_far_vis"] = 1.0 if key.look_back else 0.0
    return ch


# ── The moves ─────────────────────────────────────────────────────────────────
#
# Each function returns keys on its move's timeline. `A0`/`A1` name the active
# window's edges as phases, from `player_robot.ron`.


def jab(body: RigBody) -> List[Key]:
    """Neutral attack: a quick level cut. 0.25 s, active 0.05-0.11."""
    a0, a1 = 0.05 / 0.25, 0.11 / 0.25
    return [
        rest(body, 0.0),
        # Coil: blade cocked up behind the shoulder, chest opened to the camera,
        # weight back, the off hand thrown forward for balance.
        Key(at=a0 * 0.8, near=(-150.0, -160.0, -135.0), far=(30.0, 0.0), torso=-6.0, head=-3.0,
            lunge=-2.0, drop=2.5, squash=0.97, shoulder=-3.0, turn="open", squint=0.25, ease="in"),
        # Cut: the blade level at the target at CHEST height — the head is half
        # the robot, and a blade at shoulder height draws behind it.
        Key(at=a0 + 0.35 * (a1 - a0), near=(28.0, 8.0, -2.0), far=(150.0, 120.0), torso=12.0,
            head=4.0, lunge=4.0, drop=4.0, squash=1.03, shoulder=6.0, feet={"far": (4.0, 0.0, 0.0)},
            turn="profile", squint=0.3, ease="out"),
        Key(at=a1, near=(55.0, 34.0, 16.0), far=(160.0, 140.0), torso=14.0, head=6.0, lunge=5.0,
            drop=4.5, squash=0.96, shoulder=7.0, feet={"far": (4.0, 0.0, 0.0)}, turn="profile",
            squint=0.2),
        # The blade winks out with the cut; a blade lingering into recovery
        # reads as a second, slower swing.
        Key(at=a1 + 0.12, near=(78.0, 70.0, 40.0), far=(110.0, 110.0), torso=8.0, head=3.5,
            lunge=3.0, drop=3.0, shoulder=3.0, feet={"far": (2.5, 0.0, 0.0)}, blade=0.0, squint=0.1),
        rest(body, 1.0),
    ]


def tilt_forward(body: RigBody) -> List[Key]:
    """Forward tilt: a committed rising cut with a real step. 0.31 s, A 0.07-0.14.

    Its hit launches up and forward, so the blade rises through the cut where
    the jab's stays level.
    """
    a0, a1 = 0.07 / 0.31, 0.14 / 0.31
    return [
        rest(body, 0.0),
        # Low coil: blade trailing level behind, body sunk and turned open. Its
        # angle is -170, not 190: the cut then swings OVER the top to the front,
        # where 190 would drag the blade through the floor in between.
        Key(at=a0 * 0.85, near=(160.0, 150.0, -170.0), far=(40.0, 10.0), torso=-4.0, head=-2.0,
            lunge=-3.0, drop=4.5, squash=0.95, shoulder=-4.0, feet={"far": (-1.0, 0.0, 0.0)},
            turn="open", squint=0.3, ease="in"),
        # Rising cut through the target, a long step in.
        Key(at=a0 + 0.4 * (a1 - a0), near=(10.0, -12.0, -22.0), far=(155.0, 125.0), torso=16.0,
            head=5.0, lunge=7.0, drop=3.5, squash=1.04, shoulder=7.0, feet={"far": (8.0, 0.0, 0.0)},
            turn="profile", squint=0.35, ease="out"),
        Key(at=a1, near=(-20.0, -45.0, -50.0), far=(165.0, 145.0), torso=12.0, head=2.0, lunge=8.0,
            drop=3.0, shoulder=8.0, feet={"far": (8.0, 0.0, 0.0)}, turn="profile", squint=0.25),
        Key(at=a1 + 0.2, near=(50.0, 60.0, 30.0), far=(110.0, 100.0), torso=6.0, head=2.0,
            lunge=5.0, drop=2.5, shoulder=3.0, feet={"far": (6.0, 0.0, 0.0)}, blade=0.0),
        rest(body, 1.0),
    ]


def tilt_up(body: RigBody) -> List[Key]:
    """Up tilt: an overhead arc from front to back. 0.33 s, A 0.07-0.15."""
    a0, a1 = 0.07 / 0.33, 0.15 / 0.33
    return [
        rest(body, 0.0),
        # Crouch with the blade low in front: the arc has somewhere to come from.
        Key(at=a0 * 0.85, near=(55.0, 40.0, 30.0), far=(120.0, 110.0), torso=8.0, head=4.0,
            drop=5.0, squash=0.94, squint=0.2, ease="in"),
        # Up through the vertical, body stretched onto its toes, eyes up.
        Key(at=a0 + 0.45 * (a1 - a0), near=(-95.0, -100.0, -92.0), far=(150.0, 150.0), torso=-8.0,
            head=-12.0, drop=-1.5, squash=1.06, shoulder=2.0,
            feet={"near": (0.0, 1.5, 14.0), "far": (0.0, 1.5, 14.0)}, turn="open", squint=0.3,
            ease="out"),
        # Over and behind.
        Key(at=a1, near=(-150.0, -165.0, -170.0), far=(120.0, 130.0), torso=-12.0, head=-14.0,
            drop=0.0, squash=1.02, turn="open", squint=0.2),
        Key(at=a1 + 0.2, near=(-170.0, 160.0, 150.0), far=(90.0, 95.0), torso=-5.0, head=-5.0,
            drop=1.0, blade=0.0),
        rest(body, 1.0),
    ]


def tilt_down(body: RigBody) -> List[Key]:
    """Down tilt: a crouching thrust along the floor. 0.28 s, A 0.06-0.12.

    Its volume is a long thin poke, so the blade goes out straight and comes
    straight back — no arc to read as a slash.
    """
    a0, a1 = 0.06 / 0.28, 0.12 / 0.28
    low = {"near": (-3.0, 0.0, 0.0), "far": (5.0, 0.0, 0.0)}
    return [
        rest(body, 0.0),
        # Drawn back at the hip, dropping into the crouch — the blade still
        # points AT the target: a thrust never swings.
        Key(at=a0 * 0.85, near=(150.0, 170.0, 5.0), far=(45.0, 20.0), torso=18.0, head=-8.0,
            lunge=-1.0, drop=9.0, squash=0.92, shoulder=-3.0, feet=low, turn="open", squint=0.3,
            ease="in"),
        # Thrust: arm and blade in one straight line along the floor.
        Key(at=a0 + 0.3 * (a1 - a0), near=(20.0, 8.0, 6.0), far=(140.0, 120.0), torso=26.0,
            head=-12.0, lunge=6.0, drop=10.0, squash=0.94, shoulder=7.0,
            feet={"near": (-4.0, 0.0, 0.0), "far": (9.0, 0.0, 0.0)}, turn="profile", squint=0.4,
            ease="out"),
        Key(at=a1, near=(22.0, 10.0, 8.0), far=(140.0, 120.0), torso=25.0, head=-11.0, lunge=6.0,
            drop=10.0, squash=0.94, shoulder=7.0,
            feet={"near": (-4.0, 0.0, 0.0), "far": (9.0, 0.0, 0.0)}, turn="profile", squint=0.3),
        Key(at=a1 + 0.22, near=(90.0, 100.0, 60.0), far=(90.0, 80.0), torso=12.0, head=-4.0,
            lunge=3.0, drop=6.0, squash=0.97, feet={"far": (5.0, 0.0, 0.0)}, blade=0.0),
        rest(body, 1.0),
    ]


def dash_attack(body: RigBody) -> List[Key]:
    """Dash attack: a flying lunge with the blade out in front. 0.40 s, A 0.05-0.14."""
    a0, a1 = 0.05 / 0.40, 0.14 / 0.40
    lunge_feet = {"near": (-7.0, 3.0, 25.0), "far": (9.0, 0.0, -6.0)}
    return [
        Key(at=0.0, near=(150.0, 150.0, 2.0), far=(40.0, 20.0), torso=18.0, head=-6.0,
            lunge=0.0, drop=5.0, squash=0.95, shoulder=-2.0,
            feet={"near": (-4.0, 2.0, 18.0), "far": (4.0, 0.0, 0.0)}, turn="open", squint=0.3),
        # Launched forward, body nearly horizontal behind the blade.
        Key(at=a0 + 0.3 * (a1 - a0), near=(15.0, 0.0, -4.0), far=(165.0, 150.0), torso=30.0,
            head=-10.0, lunge=10.0, drop=6.0, squash=1.04, shoulder=8.0, feet=lunge_feet,
            turn="profile", squint=0.45, ease="out"),
        # Skidding on, blade still out.
        Key(at=a1 + 0.15, near=(25.0, 10.0, 5.0), far=(160.0, 140.0), torso=24.0, head=-6.0,
            lunge=11.0, drop=5.0, squash=0.97, shoulder=7.0, feet=lunge_feet, turn="profile",
            squint=0.3),
        Key(at=0.8, near=(80.0, 80.0, 50.0), far=(100.0, 95.0), torso=10.0, head=-1.0, lunge=5.0,
            drop=2.5, feet={"far": (4.0, 0.0, 0.0)}, blade=0.0),
        rest(body, 1.0),
    ]


def smash_forward(body: RigBody) -> List[Key]:
    """Forward smash: a huge overhead cleave. 0.71 s, A 0.30-0.37.

    The long startup is where a smash is read, so it is spent on an obvious
    wind-up: blade raised high behind the head, body coiled back on one leg.
    """
    a0, a1 = 0.30 / 0.71, 0.37 / 0.71
    return [
        rest(body, 0.0),
        Key(at=a0 * 0.5, near=(-140.0, -150.0, -125.0), far=(45.0, 15.0), torso=-8.0, head=-5.0,
            lunge=-3.0, drop=3.0, squash=0.97, shoulder=-4.0, turn="open", squint=0.3),
        # Full coil, held: the blade overhead and past vertical behind.
        Key(at=a0 * 0.92, near=(-120.0, -140.0, -150.0), far=(30.0, -10.0), torso=-12.0,
            head=-6.0, lunge=-4.0, drop=4.5, squash=0.94, shoulder=-5.0,
            feet={"far": (1.0, 1.0, 10.0)}, turn="open", squint=0.45, ease="in", face="strain"),
        # CLEAVE: blade over the top and down in front, a big step and lean.
        Key(at=a0 + 0.35 * (a1 - a0), near=(25.0, 15.0, 20.0), far=(160.0, 140.0), torso=22.0,
            head=8.0, lunge=10.0, drop=6.0, squash=1.05, shoulder=9.0,
            feet={"near": (-3.0, 0.0, 0.0), "far": (10.0, 0.0, 0.0)}, turn="profile", squint=0.5,
            ease="out"),
        Key(at=a1, near=(55.0, 40.0, 30.0), far=(165.0, 150.0), torso=26.0, head=10.0, lunge=11.0,
            drop=7.0, squash=0.95, shoulder=9.0,
            feet={"near": (-3.0, 0.0, 0.0), "far": (10.0, 0.0, 0.0)}, turn="profile", squint=0.35),
        # Heavy recovery: stays low, the blade dragging out.
        Key(at=a1 + 0.25, near=(80.0, 70.0, 40.0), far=(120.0, 110.0), torso=16.0, head=5.0,
            lunge=8.0, drop=5.0, shoulder=4.0, feet={"far": (8.0, 0.0, 0.0)}, blade=0.3),
        Key(at=0.9, near=(100.0, 95.0, 80.0), far=(70.0, 80.0), torso=4.0, head=1.0, lunge=2.0,
            drop=1.5, feet={"far": (2.0, 0.0, 0.0)}, blade=0.0),
        rest(body, 1.0),
    ]


def smash_up(body: RigBody) -> List[Key]:
    """Up smash: a jumping uppercut arc. 0.66 s, A 0.26-0.34."""
    a0, a1 = 0.26 / 0.66, 0.34 / 0.66
    return [
        rest(body, 0.0),
        # Deep squat, blade low and back, ready to spring.
        Key(at=a0 * 0.9, near=(120.0, 150.0, 170.0), far=(60.0, 40.0), torso=14.0, head=6.0,
            lunge=-1.0, drop=9.0, squash=0.9, shoulder=-3.0, turn="open", squint=0.45, ease="in",
            face="strain"),
        # Spring: up off the toes, the blade sweeping up the front.
        Key(at=a0 + 0.4 * (a1 - a0), near=(-80.0, -95.0, -85.0), far=(140.0, 150.0), torso=-6.0,
            head=-14.0, lunge=1.0, drop=-7.0, squash=1.08, shoulder=3.0,
            feet={"near": (-1.0, 6.0, 30.0), "far": (1.0, 7.0, 30.0)}, turn="profile", squint=0.5,
            ease="out"),
        Key(at=a1, near=(-110.0, -130.0, -140.0), far=(130.0, 140.0), torso=-10.0, head=-16.0,
            lunge=1.0, drop=-8.0, squash=1.04, shoulder=2.0,
            feet={"near": (-1.0, 7.0, 30.0), "far": (1.0, 8.0, 30.0)}, turn="open", squint=0.35),
        # Landing back into a crouch.
        Key(at=a1 + 0.2, near=(-150.0, -190.0, -200.0), far=(90.0, 90.0), torso=6.0, head=-3.0,
            drop=5.0, squash=0.94, blade=0.2),
        Key(at=0.9, near=(115.0, 105.0, 85.0), far=(60.0, 75.0), torso=2.0, drop=1.0, blade=0.0),
        rest(body, 1.0),
    ]


def smash_down(body: RigBody) -> List[Key]:
    """Down smash: a low sweep in front, then behind. 0.60 s, A 0.22-0.30."""
    a0, a1 = 0.22 / 0.60, 0.30 / 0.60
    wide = {"near": (-6.0, 0.0, 0.0), "far": (7.0, 0.0, 0.0)}
    return [
        rest(body, 0.0),
        # Sink wide, blade gathered high.
        Key(at=a0 * 0.9, near=(-60.0, -80.0, -70.0), far=(60.0, 50.0), torso=4.0, head=2.0,
            drop=9.0, squash=0.92, feet=wide, turn="open", squint=0.45, ease="in", face="strain"),
        # Low sweep along the floor in front...
        Key(at=a0 + 0.4 * (a1 - a0), near=(60.0, 30.0, 8.0), far=(150.0, 150.0), torso=22.0,
            head=-6.0, lunge=3.0, drop=11.0, squash=0.93, shoulder=6.0, feet=wide, turn="profile",
            squint=0.5, ease="out"),
        # ...whipped over the top to cut behind (-188, not 172: the sweep
        # between would otherwise run the blade through the floor).
        Key(at=a1, near=(120.0, 160.0, -188.0), far=(30.0, 20.0), torso=10.0, head=-4.0, lunge=-1.0,
            drop=11.0, squash=0.93, shoulder=-5.0, feet=wide, turn="open", squint=0.35,
            ease="linear"),
        Key(at=a1 + 0.2, near=(110.0, 140.0, -190.0), far=(60.0, 60.0), torso=6.0, drop=6.0,
            squash=0.96, feet={"near": (-3.0, 0.0, 0.0), "far": (3.0, 0.0, 0.0)}, blade=0.2),
        rest(body, 1.0),
    ]


def smash_charge(body: RigBody) -> List[Key]:
    """Held smash: a coiled, trembling wind-up. Loops on its own clock."""
    keys = []
    for i in range(5):
        u = i / 4.0
        wobble = math.sin(u * 2.0 * math.pi)
        keys.append(Key(
            at=u, near=(-125.0 + 3.0 * wobble, -145.0, -150.0 + 4.0 * wobble), far=(30.0, -10.0),
            torso=-11.0 + 1.5 * wobble, head=-6.0, lunge=-4.0 + 0.8 * wobble, drop=5.0 + wobble,
            squash=0.94 + 0.01 * wobble, shoulder=-5.0, feet={"far": (1.0, 1.0, 10.0)},
            turn="open", squint=0.5, blade=0.85 + 0.15 * wobble, ease="linear", face="strain"))
    return keys


def _air(keys: List[Key]) -> List[Key]:
    """Mark every key airborne and default the boots to the tuck."""
    return [
        replace(k, air=True, drop=k.drop + AIR_RISE, feet={**TUCK, **k.feet}) for k in keys
    ]


def air_neutral(body: RigBody) -> List[Key]:
    """Neutral air: a full-circle spin of the blade. 0.36 s, A 0.06-0.20.

    Its volume is a ring, so the blade visits every side: front, over the top,
    behind, underneath, and back to front across the active window.
    """
    a0, a1 = 0.06 / 0.36, 0.20 / 0.36
    step = (a1 - a0) / 4.0
    ring = [
        (0.0, (25.0, 5.0, 0.0), None, 8.0),
        (-90.0, (-75.0, -90.0, -90.0), "open", -4.0),
        (-180.0, (-165.0, -175.0, -180.0), "open", -8.0),
        (-270.0, (100.0, 95.0, 90.0), None, 4.0),
        (-360.0, (30.0, 10.0, 0.0), "profile", 8.0),
    ]
    keys = [replace(rest(body, 0.0), feet={})]
    keys.append(Key(at=a0 * 0.8, near=(60.0, 40.0, 30.0), far=(130.0, 120.0), torso=6.0,
                    head=3.0, squash=0.95, squint=0.3, ease="in"))
    for i, (_deg, near, turn, lean) in enumerate(ring):
        keys.append(Key(at=a0 + i * step, near=near, far=(150.0 - 40.0 * (i % 2), 130.0),
                        torso=lean, head=lean * 0.4, squash=1.02, shoulder=3.0 if turn == "profile" else 0.0,
                        feet={"near": (-4.0, 9.0, 30.0), "far": (3.0, 11.0, 25.0)}, turn=turn,
                        squint=0.35, ease="linear" if i else "out"))
    keys.append(Key(at=a1 + 0.2, near=(70.0, 70.0, 40.0), far=(110.0, 110.0), torso=4.0,
                    blade=0.0))
    keys.append(replace(rest(body, 1.0), feet={}))
    return _air(keys)


def air_forward(body: RigBody) -> List[Key]:
    """Forward air: a leaping forward cut. 0.39 s, A 0.09-0.17."""
    a0, a1 = 0.09 / 0.39, 0.17 / 0.39
    return _air([
        replace(rest(body, 0.0), feet={}),
        Key(at=a0 * 0.85, near=(-140.0, -155.0, -130.0), far=(35.0, 5.0), torso=-8.0, head=-4.0,
            lunge=-2.0, squash=0.97, shoulder=-3.0, feet={"near": (-6.0, 6.0, 30.0)}, turn="open",
            squint=0.3, ease="in"),
        Key(at=a0 + 0.4 * (a1 - a0), near=(20.0, 5.0, 0.0), far=(160.0, 135.0), torso=18.0,
            head=6.0, lunge=4.0, squash=1.04, shoulder=7.0,
            feet={"near": (-8.0, 5.0, 35.0), "far": (5.0, 10.0, 10.0)}, turn="profile",
            squint=0.35, ease="out"),
        Key(at=a1, near=(55.0, 40.0, 35.0), far=(165.0, 150.0), torso=20.0, head=7.0, lunge=4.0,
            squash=0.97, shoulder=7.0, feet={"near": (-8.0, 5.0, 35.0), "far": (5.0, 10.0, 10.0)},
            turn="profile", squint=0.25),
        Key(at=a1 + 0.2, near=(80.0, 80.0, 60.0), far=(110.0, 105.0), torso=8.0, head=3.0,
            lunge=2.0, blade=0.0),
        replace(rest(body, 1.0), feet={}),
    ])


def air_back(body: RigBody) -> List[Key]:
    """Back air: twist and cut behind. 0.41 s, A 0.10-0.17.

    The near hand already hangs behind this body, so the blade goes out over
    the back shoulder while the chest turns to the camera and the head looks
    over its shoulder (a lean back).
    """
    a0, a1 = 0.10 / 0.41, 0.17 / 0.41
    return _air([
        replace(rest(body, 0.0), feet={}),
        # Gathered: blade tucked across the chest in front.
        Key(at=a0 * 0.85, near=(40.0, -30.0, -20.0), far=(120.0, 120.0), torso=10.0, head=4.0,
            squash=0.95, shoulder=4.0, feet={"far": (6.0, 10.0, 0.0)}, turn="profile", squint=0.3,
            ease="in"),
        # Cut behind, level, body arched back into it.
        Key(at=a0 + 0.4 * (a1 - a0), near=(175.0, 182.0, 180.0), far=(30.0, 10.0), torso=-18.0,
            head=-12.0, lunge=-3.0, squash=1.04, shoulder=-6.0,
            feet={"near": (-6.0, 4.0, 30.0), "far": (6.0, 12.0, 0.0)}, turn="open", squint=0.4,
            ease="out", look_back=True),
        Key(at=a1, near=(200.0, 215.0, 215.0), far=(20.0, 0.0), torso=-16.0, head=-10.0,
            lunge=-3.0, squash=0.98, shoulder=-6.0,
            feet={"near": (-6.0, 4.0, 30.0), "far": (6.0, 12.0, 0.0)}, turn="open", squint=0.25,
            look_back=True),
        Key(at=a1 + 0.2, near=(150.0, 140.0, 120.0), far=(70.0, 60.0), torso=-6.0, head=-3.0,
            blade=0.0, look_back=True),
        replace(rest(body, 1.0), feet={}),
    ])


def air_up(body: RigBody) -> List[Key]:
    """Up air: an arc over the head. 0.36 s, A 0.07-0.16."""
    a0, a1 = 0.07 / 0.36, 0.16 / 0.36
    return _air([
        replace(rest(body, 0.0), feet={}),
        Key(at=a0 * 0.85, near=(40.0, 20.0, 10.0), far=(120.0, 120.0), torso=8.0, head=4.0,
            squash=0.95, feet={"near": (-3.0, 9.0, 20.0), "far": (3.0, 11.0, 15.0)}, squint=0.3,
            ease="in"),
        Key(at=a0 + 0.45 * (a1 - a0), near=(-85.0, -95.0, -90.0), far=(140.0, 150.0), torso=-6.0,
            head=-14.0, drop=-2.0, squash=1.07, shoulder=2.0,
            feet={"near": (-2.0, 3.0, 35.0), "far": (2.0, 4.0, 35.0)}, turn="open", squint=0.35,
            ease="out"),
        Key(at=a1, near=(-150.0, -165.0, -165.0), far=(120.0, 130.0), torso=-10.0, head=-14.0,
            drop=-2.0, squash=1.02, feet={"near": (-2.0, 3.0, 35.0), "far": (2.0, 4.0, 35.0)},
            turn="open", squint=0.25),
        Key(at=a1 + 0.2, near=(-170.0, 160.0, 140.0), far=(90.0, 95.0), torso=-4.0, head=-4.0,
            blade=0.0),
        replace(rest(body, 1.0), feet={}),
    ])


def air_down(body: RigBody) -> List[Key]:
    """Down air: the pogo — blade straight down under the boots. 0.48 s, A 0.12-0.22.

    The hit bounces the robot, so the pose must read as a spike you can land
    ON: body curled over the blade, knees drawn up out of its way.
    """
    a0, a1 = 0.12 / 0.48, 0.22 / 0.48
    curl = {"near": (-8.0, 12.0, 40.0), "far": (-3.0, 14.0, 35.0)}
    return _air([
        replace(rest(body, 0.0), feet={}),
        # Blade raised overhead first, so the stab has a direction.
        Key(at=a0 * 0.85, near=(-110.0, -120.0, -95.0), far=(60.0, 40.0), torso=-6.0, head=-6.0,
            squash=1.03, feet={"near": (-2.0, 3.0, 20.0), "far": (2.0, 4.0, 15.0)}, squint=0.3,
            ease="in"),
        Key(at=a0 + 0.35 * (a1 - a0), near=(95.0, 88.0, 90.0), far=(160.0, 150.0), torso=16.0,
            head=10.0, drop=-2.0, squash=0.95, shoulder=3.0, feet=curl, turn="profile",
            squint=0.45, ease="out"),
        Key(at=a1, near=(92.0, 88.0, 90.0), far=(160.0, 150.0), torso=16.0, head=10.0, drop=-2.0,
            squash=0.95, shoulder=3.0, feet=curl, turn="profile", squint=0.35),
        Key(at=a1 + 0.2, near=(100.0, 95.0, 90.0), far=(100.0, 95.0), torso=6.0, head=3.0,
            blade=0.0),
        replace(rest(body, 1.0), feet={}),
    ])


def grab(body: RigBody) -> List[Key]:
    """Grab: both hands shot forward, then drawn back empty. 0.32 s, A 0.07-0.12.

    ⚠ Every reach is at CHEST height or below. The head is half this robot and
    draws over the arms, so a hand held out at shoulder height is invisible —
    the first grab and throws reached perfectly and showed nothing.
    """
    a0, a1 = 0.07 / 0.32, 0.12 / 0.32
    reach = {"far": (6.0, 0.0, 0.0)}
    return [
        rest(body, 0.0),
        Key(at=a0 * 0.8, near=(150.0, 120.0, 0.0), far=(70.0, 40.0), torso=-4.0, lunge=-1.0,
            drop=2.5, squash=0.97, blade=0.0, turn="open", squint=0.2, ease="in"),
        Key(at=a0 + 0.5 * (a1 - a0), near=(28.0, 12.0, 0.0), far=(22.0, 6.0), torso=16.0,
            head=6.0, lunge=7.0, drop=3.5, squash=1.03, shoulder=6.0, feet=reach, blade=0.0,
            turn="profile", squint=0.35, ease="out", face="fierce"),
        Key(at=a1 + 0.1, near=(30.0, 15.0, 0.0), far=(24.0, 8.0), torso=14.0, head=5.0, lunge=7.0,
            drop=3.5, shoulder=6.0, feet=reach, blade=0.0, turn="profile", squint=0.2),
        Key(at=0.8, near=(80.0, 60.0, 0.0), far=(60.0, 50.0), torso=5.0, lunge=2.0, drop=1.0,
            blade=0.0),
        rest(body, 1.0),
    ]


def grab_hold(body: RigBody) -> List[Key]:
    """Holding a grabbed body out front, arms locked. Loops on its own clock."""
    keys = []
    for i in range(5):
        u = i / 4.0
        w = math.sin(u * 2.0 * math.pi)
        keys.append(Key(at=u, near=(30.0 + 2.0 * w, 14.0, 0.0), far=(24.0 - 2.0 * w, 8.0),
                        torso=10.0 + w, head=3.0, lunge=3.0, drop=3.0 + 0.5 * w, shoulder=5.0,
                        feet={"far": (4.0, 0.0, 0.0)}, blade=0.0, turn="profile", squint=0.2,
                        ease="linear"))
    return keys


def pummel(body: RigBody) -> List[Key]:
    """Pummel: a head-butt into the held body. 0.20 s."""
    hold = dict(near=(30.0, 14.0, 0.0), far=(24.0, 8.0), lunge=3.0, drop=3.0, shoulder=5.0,
                feet={"far": (4.0, 0.0, 0.0)}, blade=0.0, turn="profile")
    return [
        Key(at=0.0, torso=10.0, head=3.0, **hold),
        Key(at=0.3, torso=-4.0, head=-10.0, squint=0.3, ease="in", face="strain", **hold),
        Key(at=0.55, torso=22.0, head=16.0, squint=0.6, ease="out", face="fierce",
            **{**hold, "lunge": 6.0}),
        Key(at=1.0, torso=10.0, head=3.0, **hold),
    ]


def _throw(body: RigBody, cast_near: tuple, cast_far: tuple, torso: float, head: float,
           lunge: float, drop: float, turn: str, wind: tuple, wind_torso: float) -> List[Key]:
    hold = dict(lunge=3.0, drop=3.0, shoulder=5.0, feet={"far": (4.0, 0.0, 0.0)}, blade=0.0)
    return [
        Key(at=0.0, near=(30.0, 14.0, 0.0), far=(24.0, 8.0), torso=10.0, head=3.0,
            turn="profile", **hold),
        Key(at=0.3, near=wind[0], far=wind[1], torso=wind_torso, head=-4.0, squash=0.95,
            turn="open", squint=0.4, ease="in", face="strain", **{**hold, "drop": 5.0}),
        Key(at=0.55, near=cast_near, far=cast_far, torso=torso, head=head, squash=1.05,
            turn=turn, squint=0.5, ease="out", face="fierce",
            **{**hold, "lunge": lunge, "drop": drop}),
        Key(at=0.8, near=(80.0, 60.0, 0.0), far=(70.0, 60.0), torso=torso * 0.4,
            head=head * 0.3, lunge=lunge * 0.5, drop=1.5, blade=0.0),
        rest(body, 1.0),
    ]


def throw_forward(body):
    return _throw(body, (25.0, 5.0, 0.0), (20.0, 0.0), 22.0, 6.0, 8.0, 4.0, "profile",
                  ((140.0, 120.0, 0.0), (150.0, 130.0)), -10.0)


def throw_back(body):
    return _throw(body, (190.0, 200.0, 0.0), (170.0, 175.0), -22.0, -10.0, -4.0, 3.0, "open",
                  ((20.0, -10.0, 0.0), (15.0, -15.0)), 16.0)


def throw_up(body):
    return _throw(body, (-100.0, -110.0, 0.0), (-80.0, -95.0), -10.0, -16.0, 2.0, -3.0, "open",
                  ((70.0, 50.0, 0.0), (60.0, 40.0)), 14.0)


def throw_down(body):
    return _throw(body, (80.0, 95.0, 0.0), (75.0, 90.0), 28.0, 14.0, 6.0, 9.0, "profile",
                  ((-110.0, -120.0, 0.0), (-100.0, -110.0)), -8.0)


def taunt(body: RigBody) -> List[Key]:
    """Taunt: ignite the blade, twirl it, and plant it with a proud lean. 0.9 s."""
    return [
        rest(body, 0.0),
        Key(at=0.15, near=(30.0, -30.0, -80.0), far=(60.0, 50.0), torso=2.0, head=-2.0,
            blade=1.0, squint=0.1, ease="out"),
        Key(at=0.3, near=(0.0, -60.0, -200.0), far=(60.0, 50.0), torso=0.0, head=-4.0,
            turn="open", squint=0.2, ease="linear"),
        Key(at=0.45, near=(0.0, -60.0, -380.0), far=(60.0, 50.0), torso=0.0, head=-4.0,
            turn="open", squint=0.2, ease="linear"),
        # Planted point-down at the side, chest out to the camera, a wink.
        Key(at=0.62, near=(60.0, 90.0, 90.0), far=(-10.0, -60.0), torso=-8.0, head=-8.0,
            drop=-1.0, squash=1.04, turn="open", squint=0.8, ease="out", face="blink"),
        Key(at=0.85, near=(60.0, 90.0, 90.0), far=(-15.0, -65.0), torso=-8.0, head=-7.0,
            drop=-1.0, squash=1.03, turn="open", squint=0.7, face="blink"),
        replace(rest(body, 1.0), blade=0.0),
    ]


STRIKES: Dict[str, Callable[[RigBody], List[Key]]] = {
    "jab": jab,
    "attack_side": tilt_forward,
    "attack_up": tilt_up,
    "attack_down": tilt_down,
    "dash_attack": dash_attack,
    "smash_charge": smash_charge,
    "smash_forward": smash_forward,
    "smash_up": smash_up,
    "smash_down": smash_down,
    "air_neutral": air_neutral,
    "air_forward": air_forward,
    "air_back": air_back,
    "air_up": air_up,
    "air_down": air_down,
    "grab": grab,
    "grab_hold": grab_hold,
    "pummel": pummel,
    "throw_forward": throw_forward,
    "throw_back": throw_back,
    "throw_up": throw_up,
    "throw_down": throw_down,
    "taunt": taunt,
}


def frame_phases(frames: int, loop: bool) -> List[float]:
    """The move phase each published frame stands for.

    A move row shows frame ``i`` across ``[i/n, (i+1)/n)``, so it is posed at
    the centre of that span. A looping row (a held charge) runs on its own
    clock and is posed at ``i/n``.
    """
    if loop:
        return [i / frames for i in range(frames)]
    return [(i + 0.5) / frames for i in range(frames)]


def _keyed(values: Sequence[float], loop: bool) -> dict:
    n = len(values)
    if loop:
        times = [i / n for i in range(n)] + [1.0]
        values = list(values) + [values[0]]
    else:
        times = [i / max(1, n - 1) for i in range(n)]
    return {"keys": [[round(t, 6), round(float(v), 5)] for t, v in zip(times, values)]}


def author_strikes(doc: RigDocument) -> Dict[str, dict]:
    """Replace the strike clips of a built v3 rig with keyed body mechanics."""
    body = RigBody(doc)
    reports = {}
    for name, keys_for in STRIKES.items():
        clip = doc.data["clips"][name]
        keys = keys_for(body)
        if [k.at for k in keys] != sorted(k.at for k in keys):
            raise ValueError(f"{name}: key phases must be in order")
        loop = bool(clip.get("loop"))
        phases = frame_phases(int(clip["frames"]), loop)
        frames = [_pose(body, sample(keys, ph)) for ph in phases]
        channels = clip["channels"]
        for key in frames[0]:
            if key.startswith("_"):
                continue
            channels[key] = _keyed([f[key] for f in frames], loop)
        # The borrowed clip's presentation channels no longer describe this row.
        for stale in ("slash", "slash_arc"):
            channels.pop(stale, None)
        reports[name] = {
            "max_reach": {s: round(max(f[f"_reach_{s}"] for f in frames), 3) for s in SIDES}
        }
    return reports


__all__ = ["Key", "STRIKES", "author_strikes", "frame_phases", "sample"]
