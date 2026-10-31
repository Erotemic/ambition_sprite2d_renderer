"""Oiler's fighter body language: the rows a fighter needs besides his moves.

Movement (run, dash, skid, stops, jumps, landings, crouch, teeter), the
reactions (hits by height, launches by direction, tumble, knockdown, prone face
up and down, getups, techs), defence (guard, rolls, dodges), and the ledge and
grab rows; names from ``data/fighter_motion_vocabulary.yaml`` as the game asks
for them. ``scripts/build_oiler_rig.py`` seeds these clips into both side
documents (his right side and his left), so a left-facing row is his own other
side, not a flip.

Every pose is a :class:`Key` in WORLD terms on his own side skeleton, solved to
the rig's channels here: hands and carried legs on their reachable circles, so
no target is clamped by the IK into a pose nobody chose. He is propless and
old, heavy in the hips, deliberate: he braces, folds and catches himself with
his hands rather than flipping about, except where the vocabulary needs a roll.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Sequence, Tuple, Union

from ambition_sprite2d_renderer.authoring.rig_clip_keys import (
    const as _const,
    keys as _keys,
    rest as _rest,
    rest_pitch as _rest_pitch,
    shot as _shot,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument


@dataclass(frozen=True)
class Arm:
    """A hand on its arm's reachable circle from the shoulder: ``deg`` forward
    0, down 90, up -90, back 180 (world, or trunk-relative in a ``rel`` key);
    ``frac`` of the full reach."""

    deg: float
    frac: float = 0.9


@dataclass(frozen=True)
class Hand:
    """A wrist put on a point of the floor's frame: ``x`` forward of the
    body's centre line, ``y`` up from the floor; ``pitch`` the hand's world
    angle (0 points it forward, 90 down)."""

    x: float
    y: float
    pitch: float = 0.0


@dataclass(frozen=True)
class Foot:
    """A standing foot: ``dx`` from its rest x (+ forward), ``lift`` off the
    floor, ``toe`` added to its rest pitch (+ toe down)."""

    dx: float = 0.0
    lift: float = 0.0
    toe: float = 0.0


@dataclass(frozen=True)
class Leg:
    """A carried leg (airborne, lying, rolling): the ankle on the leg's circle
    from the hip, ``deg`` as for :class:`Arm` (down 90); the foot follows the
    shin, plus ``toe``."""

    deg: float
    frac: float = 0.95
    toe: float = 0.0


@dataclass(frozen=True)
class Key:
    """One pose. ``tilt`` pitches the whole body about the hips (+ forward),
    ``torso`` bends it over them, ``head`` nods (+ chin down); ``x``/``y`` move
    the root (+ forward / + down). ``pivot``: turn about the point this far
    above the hips instead of the hips (a roll spins about his middle).
    ``rel``: limb angles are relative to the trunk (a spin carries them)."""

    tilt: float = 0.0
    torso: float = 0.0
    head: float = 0.0
    x: float = 0.0
    y: float = 0.0
    near: Union[Arm, Hand] = Arm(90.0, 0.90)
    far: Union[Arm, Hand] = Arm(90.0, 0.92)
    nf: Union[Foot, Leg] = Foot()
    ff: Union[Foot, Leg] = Foot()
    pivot: Optional[float] = None
    rel: bool = False


STAND = Key()


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def tween(a: Key, b: Key, u: float) -> Key:
    """A pose ``u`` of the way from ``a`` to ``b``. Limbs of different kinds
    (a standing foot and a carried leg) switch half way."""

    def limb(p, q):
        if type(p) is not type(q):
            return q if u >= 0.5 else p
        return type(p)(*(_lerp(m, n, u) for m, n in zip(vars(p).values(), vars(q).values())))

    return Key(
        tilt=_lerp(a.tilt, b.tilt, u), torso=_lerp(a.torso, b.torso, u), head=_lerp(a.head, b.head, u),
        x=_lerp(a.x, b.x, u), y=_lerp(a.y, b.y, u),
        near=limb(a.near, b.near), far=limb(a.far, b.far), nf=limb(a.nf, b.nf), ff=limb(a.ff, b.ff),
        pivot=b.pivot if u >= 0.5 else a.pivot, rel=b.rel if u >= 0.5 else a.rel,
    )


@dataclass
class Row:
    """A row's poses, one per published frame, and what it wears."""

    poses: List[Key]
    ms: int
    loop: bool = False
    face: str = "knowing"
    blink: Optional[Sequence[float]] = None
    #: ``frame.plant``: ``each`` puts every frame's lowest paint on the floor
    #: the standing body does; ``row`` the row's lowest frame.
    plant: Optional[str] = None
    tags: Dict[str, float] = field(default_factory=dict)


class PoseSolver:
    """Solves a :class:`Key` to the side rig's channels."""

    def __init__(self, doc: dict):
        self.doc = doc
        self.sk = RigDocument(doc).build_skeleton()
        self.cx = float(doc["frame"]["center_x"])
        self.gy = float(doc["frame"]["ground_y"])
        self.ankle = float(doc["frame"].get("ankle_h", 0.0))
        bones = self.sk.bones
        self.arm_len = {s: bones[f"{s}_arm_u"].length + bones[f"{s}_arm_l"].length for s in ("near", "far")}
        self.leg_len = {s: bones[f"{s}_leg_u"].length + bones[f"{s}_leg_l"].length for s in ("near", "far")}
        self.hand_pitch = {s: _rest_pitch(doc, f"{s}_hand") for s in ("near", "far")}
        self.foot_pitch = {s: _rest_pitch(doc, f"{s}_foot") for s in ("near", "far")}
        self.foot_x = {s: _rest(doc, f"{s}_foot", "x") for s in ("near", "far")}

    def channels(self, k: Key) -> Dict[str, float]:
        x, y = k.x, k.y
        if k.pivot:
            th = math.radians(k.tilt)
            x -= k.pivot * math.sin(th)
            y += k.pivot * math.cos(th) - k.pivot
        root = (self.cx + x, self.gy + y)
        world = self.sk.world({"pelvis": k.tilt, "torso": k.torso}, root=root)
        out = {"root_x": x, "root_y": y, "pelvis": k.tilt, "torso": k.torso, "head": k.head}
        trunk = k.tilt + k.torso if k.rel else 0.0
        hips = k.tilt if k.rel else 0.0
        for side in ("near", "far"):
            arm = getattr(k, side)
            if isinstance(arm, Hand):
                out[f"{side}_hand_x"] = arm.x
                out[f"{side}_hand_y"] = -arm.y
                out[f"{side}_hand_pitch"] = arm.pitch
            else:
                deg = arm.deg + trunk
                ox, oy = world[f"{side}_arm_u"].origin
                r = self.arm_len[side] * arm.frac
                out[f"{side}_hand_x"] = ox + r * math.cos(math.radians(deg)) - self.cx
                out[f"{side}_hand_y"] = oy + r * math.sin(math.radians(deg)) - self.gy
                out[f"{side}_hand_pitch"] = self.hand_pitch[side] + (deg - 90.0)
            foot = k.nf if side == "near" else k.ff
            if isinstance(foot, Leg):
                deg = foot.deg + hips
                hx, hy = world[f"{side}_leg_u"].origin
                r = self.leg_len[side] * foot.frac
                ax = hx + r * math.cos(math.radians(deg))
                ay = hy + r * math.sin(math.radians(deg))
                out[f"{side}_foot_x"] = ax - self.cx
                out[f"{side}_foot_lift"] = self.gy - self.ankle - ay
                out[f"{side}_foot_pitch"] = self.foot_pitch[side] + (deg - 90.0) + foot.toe
            else:
                out[f"{side}_foot_x"] = self.foot_x[side] + foot.dx
                out[f"{side}_foot_lift"] = foot.lift
                out[f"{side}_foot_pitch"] = self.foot_pitch[side] + foot.toe
        return out

    def clip(self, row: Row) -> dict:
        poses = [self.channels(k) for k in row.poses]
        write = _keys if row.loop else _shot
        channels = {name: write([p[name] for p in poses], ease="linear") for name in poses[0]}
        channels["blink_vis"] = write(row.blink, ease="linear") if row.blink else _const(0.0)
        channels["talk_vis"] = _const(0.0)
        return {"loop": row.loop, "frames": len(row.poses), "duration_ms": row.ms, "channels": channels}


def _cycle(n: int) -> List[float]:
    return [math.sin(2.0 * math.pi * i / n) for i in range(n)]


# ---- the rows ----------------------------------------------------------------

def _rows() -> Dict[str, Row]:
    K = Key
    rows: Dict[str, Row] = {}

    # ---- movement ------------------------------------------------------------
    # A heavy man's run: leaning in, elbows bent and pumping, a short flight.
    n_strides = [(14, 0, -12), (7, 0, 0), (-3, 0, 6), (-13, 3, 28), (-17, 11, 40), (-6, 15, 30), (8, 9, 0), (15, 3, -14)]
    run = []
    for i in range(8):
        dx, lift, toe = n_strides[i]
        fdx, flift, ftoe = n_strides[(i + 4) % 8]
        swing = math.cos(2.0 * math.pi * i / 8)
        run.append(K(
            torso=13 + 1.5 * swing, head=-7, y=(1.5, 3.0, 1.5, -1.0)[i % 4], x=1.0,
            near=Arm(95 - 62 * swing, 0.66), far=Arm(95 + 62 * swing, 0.66),
            nf=Foot(dx, lift, toe), ff=Foot(fdx, flift, ftoe),
        ))
    rows["run"] = Row(run, 75, loop=True, plant="row", blink=[0, 0, 0, 0, 0, 0, 1, 0])

    # The dash: lower, longer, the arms flung wide, the chin leading.
    d_strides = [(18, 0, -14), (6, 0, 4), (-10, 2, 26), (-20, 12, 46), (-4, 17, 24), (14, 6, -8)]
    dash = []
    for i in range(6):
        dx, lift, toe = d_strides[i]
        fdx, flift, ftoe = d_strides[(i + 3) % 6]
        swing = math.cos(2.0 * math.pi * i / 6)
        dash.append(K(
            torso=22 + 2 * swing, head=-14, y=(2.0, 4.0, 1.0)[i % 3], x=2.0,
            near=Arm(80 - 75 * swing, 0.74), far=Arm(100 + 75 * swing, 0.74),
            nf=Foot(dx, lift, toe), ff=Foot(fdx, flift, ftoe),
        ))
    rows["dash"] = Row(dash, 62, loop=True, plant="row", face="stern")
    rows["dash_startup"] = Row([
        K(torso=4, head=-2, y=2, near=Arm(110, 0.8), far=Arm(100, 0.85), nf=Foot(1), ff=Foot(-1)),
        K(torso=14, head=-8, y=7, x=-1, near=Arm(150, 0.72), far=Arm(140, 0.74),
          nf=Foot(3, 0, -4), ff=Foot(-4, 0, 14)),
        K(torso=24, head=-14, y=3, x=3, near=Arm(10, 0.78), far=Arm(176, 0.78),
          nf=Foot(16, 8, -6), ff=Foot(-18, 2, 44)),
        dash[0],
    ], 50, plant="each", face="stern")

    # A skid: both heels driven ahead of him, sitting back into it, the arms
    # thrown back for balance.
    rows["skid"] = Row([
        K(torso=-6, head=4, y=5, x=-2, near=Arm(150, 0.82), far=Arm(165, 0.82),
          nf=Foot(16, 0, -26), ff=Foot(4, 0, -14)),
        K(torso=-14, head=8, y=9, x=-4, near=Arm(174, 0.86), far=Arm(190, 0.86),
          nf=Foot(19, 0, -32), ff=Foot(6, 0, -20)),
        K(torso=-12, head=7, y=9, x=-4, near=Arm(166, 0.84), far=Arm(184, 0.86),
          nf=Foot(19, 0, -30), ff=Foot(6, 0, -18)),
        K(torso=-6, head=4, y=6, x=-3, near=Arm(140, 0.82), far=Arm(158, 0.84),
          nf=Foot(16, 0, -20), ff=Foot(4, 0, -10)),
    ], 60, plant="each", face="stern")

    # A walk's last step: the back foot comes up beside the front one.
    rows["walk_stop"] = Row([
        K(torso=3, head=-1, near=Arm(75, 0.88), far=Arm(108, 0.9), nf=Foot(9, 0, -6), ff=Foot(-8, 2, 14)),
        K(torso=5, head=-2, y=1, near=Arm(82, 0.88), far=Arm(100, 0.9), nf=Foot(7), ff=Foot(-2, 4, 10)),
        K(torso=2, head=0, y=1.5, near=Arm(88, 0.9), far=Arm(92, 0.92), nf=Foot(5), ff=Foot(1)),
        STAND,
    ], 70, plant="each")

    # The brace out of a run: the front foot planted hard, the hips dropped
    # back, and his top half still going -- arms flung on ahead of him.
    rows["run_stop"] = Row([
        K(torso=14, head=-6, y=3, x=2, near=Arm(30, 0.7), far=Arm(150, 0.7),
          nf=Foot(16, 0, -16), ff=Foot(-14, 4, 30)),
        K(torso=34, head=-18, y=12, x=-6, near=Arm(-12, 0.96), far=Arm(14, 0.94),
          nf=Foot(22, 0, -24), ff=Foot(-16, 0, 34)),
        K(torso=30, head=-15, y=11, x=-5, near=Arm(-2, 0.94), far=Arm(22, 0.92),
          nf=Foot(22, 0, -22), ff=Foot(-16, 0, 30)),
        K(torso=16, head=-6, y=6, x=-3, near=Arm(50, 0.86), far=Arm(64, 0.88),
          nf=Foot(16, 0, -10), ff=Foot(-10, 0, 14)),
        K(torso=4, head=-1, y=1.5, near=Arm(84, 0.9), far=Arm(88, 0.92), nf=Foot(6), ff=Foot(-3)),
    ], 70, plant="each", face="stern")

    rows["jump_squat"] = Row([
        K(torso=8, head=-3, y=4, near=Arm(120, 0.82), far=Arm(115, 0.84), nf=Foot(1), ff=Foot(-1)),
        K(torso=18, head=-8, y=11, near=Arm(160, 0.78), far=Arm(152, 0.8), nf=Foot(2, 0, 4), ff=Foot(-2, 0, 6)),
        K(torso=16, head=-10, y=9, near=Arm(140, 0.8), far=Arm(132, 0.82), nf=Foot(2, 0, 20), ff=Foot(-2, 0, 24)),
    ], 40, plant="each", face="stern")

    # Up off both feet, arms swung up, then the knees come up into the rise.
    rows["jump"] = Row([
        K(torso=-4, head=-8, y=-2, near=Arm(-60, 0.92), far=Arm(-48, 0.9), nf=Leg(96, 0.99, 40), ff=Leg(100, 0.99, 44)),
        K(torso=-6, head=-8, y=-3, near=Arm(-70, 0.9), far=Arm(-56, 0.9), nf=Leg(92, 0.97, 34), ff=Leg(104, 0.97, 40)),
        K(torso=-2, head=-6, y=-3, near=Arm(-40, 0.86), far=Arm(-26, 0.86), nf=Leg(70, 0.8, 20), ff=Leg(100, 0.92, 34)),
        K(torso=2, head=-4, y=-3, near=Arm(0, 0.82), far=Arm(20, 0.84), nf=Leg(55, 0.7, 10), ff=Leg(92, 0.84, 28)),
        K(torso=3, head=-3, y=-3, near=Arm(30, 0.82), far=Arm(50, 0.84), nf=Leg(52, 0.68, 8), ff=Leg(86, 0.8, 24)),
        K(torso=3, head=-2, y=-3, near=Arm(42, 0.84), far=Arm(60, 0.86), nf=Leg(58, 0.72, 10), ff=Leg(88, 0.82, 24)),
    ], 70, face="knowing")

    # The second jump: no somersault for an old man -- he climbs the air, a
    # scissor kick off nothing with both arms flung up, then gathers his knees.
    rows["double_jump"] = Row([
        K(torso=14, head=4, y=-2, near=Arm(60, 0.7), far=Arm(76, 0.72), nf=Leg(60, 0.7, 14), ff=Leg(84, 0.76, 20)),
        K(tilt=-6, torso=-6, head=-14, y=-4, near=Arm(-96, 0.98), far=Arm(-78, 0.96), nf=Leg(52, 0.96, 34), ff=Leg(128, 0.96, 40)),
        K(tilt=-4, torso=-4, head=-12, y=-4, near=Arm(-70, 0.94), far=Arm(-52, 0.92), nf=Leg(118, 0.96, 40), ff=Leg(64, 0.94, 30)),
        K(torso=0, head=-8, y=-4, near=Arm(-20, 0.86), far=Arm(-4, 0.86), nf=Leg(60, 0.74, 16), ff=Leg(96, 0.88, 30)),
        K(torso=3, head=-4, y=-3, near=Arm(24, 0.82), far=Arm(44, 0.84), nf=Leg(52, 0.68, 8), ff=Leg(86, 0.8, 24)),
        K(torso=3, head=-2, y=-3, near=Arm(42, 0.84), far=Arm(60, 0.86), nf=Leg(58, 0.72, 10), ff=Leg(88, 0.82, 24)),
    ], 58, face="delighted")

    # Falling: arms lifted out from him, one knee up, the other leg hanging.
    rows["fall"] = Row([
        K(torso=-3 + 1.5 * s, head=-6 + 2 * s, y=-2, near=Arm(-22 + 8 * s, 0.86), far=Arm(-150 - 8 * s, 0.84),
          nf=Leg(70 + 5 * s, 0.78, 16), ff=Leg(100 - 4 * s, 0.94, 30))
        for s in _cycle(4)
    ], 110, loop=True, face="surprised")

    rows["land_light"] = Row([
        K(torso=10, head=-2, y=6, near=Arm(70, 0.86), far=Arm(80, 0.88), nf=Foot(2), ff=Foot(-1)),
        K(torso=6, head=-1, y=3, near=Arm(80, 0.88), far=Arm(86, 0.9), nf=Foot(2), ff=Foot(-1)),
        STAND,
    ], 50, plant="each")
    rows["land_hard"] = Row([
        K(torso=28, head=-14, y=17, near=Arm(40, 0.86), far=Arm(55, 0.86), nf=Foot(4, 0, -6), ff=Foot(-4, 0, 10)),
        K(torso=32, head=-12, y=19, near=Arm(58, 0.82), far=Arm(68, 0.84), nf=Foot(4, 0, -6), ff=Foot(-4, 0, 10)),
        K(torso=20, head=-6, y=11, near=Arm(72, 0.84), far=Arm(80, 0.86), nf=Foot(3, 0, -3), ff=Foot(-3, 0, 6)),
        K(torso=8, head=-2, y=4, near=Arm(84, 0.88), far=Arm(88, 0.9), nf=Foot(1), ff=Foot(-1)),
    ], 70, plant="each", face="hurt")

    # Down on his haunches, forearms on his knees.
    crouch = K(torso=24, head=-14, y=17, x=-2, near=Arm(52, 0.72), far=Arm(64, 0.72), nf=Foot(6, 0, -2), ff=Foot(-5, 0, 8))
    rows["crouch_start"] = Row([tween(STAND, crouch, 0.35), tween(STAND, crouch, 0.8), crouch], 50, plant="each")
    rows["crouch"] = Row([
        replace(crouch, torso=crouch.torso + 1.2 * s, y=crouch.y + 0.6 * s, head=crouch.head - 1.0 * s)
        for s in _cycle(4)
    ], 140, loop=True, plant="each", blink=[0, 0, 1, 0])
    rows["crouch_end"] = Row([tween(crouch, STAND, 0.4), tween(crouch, STAND, 0.8), STAND], 50, plant="each")

    # At the edge (ahead of him): toes over it, the front foot off the floor,
    # bent out over the drop and windmilling to get back.
    # The arms row backwards round full circles, the far one a beat behind.
    teeter = []
    for i in range(6):
        a = 2.0 * math.pi * i / 6
        teeter.append(K(
            tilt=6 + 3 * math.sin(a), torso=20 + 5 * math.sin(a), head=14 + 4 * math.sin(a), x=1,
            near=Arm(30 - 60 * i, 0.94), far=Arm(-30 - 60 * i, 0.92),
            nf=Foot(6, 3 + 1.5 * math.sin(a), 34), ff=Foot(-7, 0, 0),
        ))
    rows["teeter"] = Row(teeter, 100, loop=True, plant="each", face="worried")

    # ---- reactions -------------------------------------------------------------
    # Struck at the head: chin snapped up and back, shoulders after it, the
    # arms flung up loose; he settles rocked back on his heels.
    rows["hit_high"] = Row([
        K(torso=-12, head=-24, x=-2, near=Arm(20, 0.78), far=Arm(50, 0.78), nf=Foot(1, 0, -14), ff=Foot(-3)),
        K(torso=-16, head=-26, x=-3, near=Arm(-30, 0.8), far=Arm(-8, 0.82), nf=Foot(1, 0, -18), ff=Foot(-4)),
        K(torso=-13, head=-21, x=-3, near=Arm(0, 0.76), far=Arm(18, 0.78), nf=Foot(1, 0, -14), ff=Foot(-4)),
        K(torso=-11, head=-18, x=-3, near=Arm(14, 0.74), far=Arm(30, 0.76), nf=Foot(1, 0, -12), ff=Foot(-4)),
    ], 70, face="hurt", blink=[1, 1, 0, 0], plant="each")
    # In the belly: hips punched back, folded over it, arms clutched in.
    rows["hit_mid"] = Row([
        K(torso=30, head=10, x=-5, y=5, near=Arm(60, 0.55), far=Arm(72, 0.55), nf=Foot(2, 0, -6), ff=Foot(-5)),
        K(torso=38, head=14, x=-6, y=7, near=Arm(66, 0.5), far=Arm(78, 0.5), nf=Foot(3, 0, -8), ff=Foot(-5)),
        K(torso=34, head=10, x=-6, y=6, near=Arm(68, 0.52), far=Arm(80, 0.52), nf=Foot(3, 0, -8), ff=Foot(-5)),
        K(torso=30, head=7, x=-5, y=6, near=Arm(70, 0.54), far=Arm(82, 0.54), nf=Foot(3, 0, -6), ff=Foot(-5)),
    ], 70, face="hurt", blink=[1, 0, 0, 0], plant="each")
    # Across the shins: the front foot knocked from under him, pitched forward
    # over the back leg, arms thrown out to catch the balance.
    rows["hit_low"] = Row([
        K(tilt=6, torso=12, head=-12, x=1, y=3, near=Arm(-30, 0.9), far=Arm(160, 0.9),
          nf=Foot(-8, 12, 40), ff=Foot(-5)),
        K(tilt=8, torso=16, head=-14, x=1, y=4, near=Arm(-46, 0.92), far=Arm(176, 0.92),
          nf=Foot(-12, 15, 46), ff=Foot(-5)),
        K(tilt=7, torso=14, head=-12, x=1, y=4, near=Arm(-36, 0.9), far=Arm(168, 0.9),
          nf=Foot(-10, 12, 40), ff=Foot(-5)),
        K(tilt=6, torso=12, head=-10, x=1, y=4, near=Arm(-26, 0.9), far=Arm(160, 0.9),
          nf=Foot(-9, 10, 34), ff=Foot(-5)),
    ], 70, face="hurt", blink=[1, 0, 0, 0], plant="each")
    # Hit in the air: whipped back from the chest, the head, hands and feet
    # all left forward of him -- open, not the folded seat of a launch.
    rows["hit_air"] = Row([
        K(tilt=-22, torso=-8, head=18, x=-3, pivot=8.0, near=Arm(-10, 0.86), far=Arm(14, 0.86), nf=Leg(70, 0.9, 20), ff=Leg(50, 0.94, 20)),
        K(tilt=-30, torso=-10, head=22, x=-4, pivot=8.0, near=Arm(-24, 0.9), far=Arm(4, 0.9), nf=Leg(62, 0.9, 20), ff=Leg(40, 0.96, 20)),
        K(tilt=-26, torso=-8, head=18, x=-4, pivot=8.0, near=Arm(-14, 0.88), far=Arm(12, 0.88), nf=Leg(68, 0.88, 20), ff=Leg(46, 0.94, 20)),
        K(tilt=-22, torso=-6, head=14, x=-3, pivot=8.0, near=Arm(-4, 0.86), far=Arm(20, 0.86), nf=Leg(74, 0.88, 20), ff=Leg(52, 0.94, 20)),
    ], 70, face="hurt", blink=[1, 1, 0, 0])

    # Launches: one impact frame, then the flight shape he holds. Each trails
    # its limbs away from where he is going.
    def impact(near: float, far: float) -> Key:
        return K(torso=18, head=12, x=-2, near=Arm(near, 0.6), far=Arm(far, 0.6), nf=Leg(80, 0.85, 10), ff=Leg(95, 0.85, 10))

    # Up: stretched long and arched, head back, everything hanging below him.
    up = K(tilt=-14, torso=-18, head=-20, near=Arm(120, 0.95), far=Arm(140, 0.95),
           nf=Leg(98, 0.99, 34), ff=Leg(112, 0.99, 40))
    rows["launch_up"] = Row([impact(-20, 0), replace(up, tilt=-10, torso=-14), up, replace(up, near=Arm(126, 0.95), far=Arm(146, 0.95))],
                            60, face="hurt", blink=[1, 0, 0, 0])
    # Away (backwards): the hips lead, folded into a C round them, the head,
    # hands and feet all left behind, forward.
    away = K(tilt=-58, torso=42, head=16, near=Arm(6, 0.95), far=Arm(-14, 0.95),
             nf=Leg(18, 0.97, 10), ff=Leg(34, 0.97, 14), pivot=6.0)
    rows["launch_horizontal"] = Row([impact(50, 64), replace(away, tilt=-48, torso=36), away, replace(away, near=Arm(0, 0.95), far=Arm(-20, 0.95))],
                                    60, face="hurt", blink=[1, 0, 0, 0])
    # Down: diving head first, arms and legs streaming up behind him.
    down = K(tilt=128, torso=8, head=-20, near=Arm(-120, 0.95), far=Arm(-104, 0.95),
             nf=Leg(-56, 0.99, 30), ff=Leg(-78, 0.97, 30), pivot=6.0)
    rows["launch_down"] = Row([impact(-40, -24), replace(down, tilt=112), down, replace(down, near=Arm(-126, 0.95), far=Arm(-110, 0.95))],
                              60, face="hurt", blink=[1, 0, 0, 0])
    # The plain launch: spread-eagle, flung up and back, open rather than folded.
    spread = K(tilt=-36, torso=-6, head=-14, near=Arm(-30, 0.97), far=Arm(-80, 0.97),
               nf=Leg(60, 0.99, 20), ff=Leg(120, 0.99, 24), pivot=6.0)
    rows["launch"] = Row([impact(10, 30), replace(spread, tilt=-28), spread, replace(spread, near=Arm(-36, 0.97), far=Arm(-86, 0.97))],
                         60, face="hurt", blink=[1, 0, 0, 0])
    # Spiked: slammed flat, belly down, arms flung overhead and heels kicked up.
    slam = K(tilt=78, torso=-12, head=-20, near=Arm(-60, 0.95), far=Arm(-40, 0.95),
             nf=Leg(-140, 0.7, 20), ff=Leg(-170, 0.85, 20), pivot=6.0)
    rows["meteor"] = Row([impact(-50, -30), replace(slam, tilt=66), slam, replace(slam, near=Arm(-66, 0.95), far=Arm(-46, 0.95))],
                         60, face="hurt", blink=[1, 0, 0, 0])

    # Tumbling: turning head over heels about his middle, limbs loose.
    rows["tumble"] = Row([
        K(tilt=-45 * i, torso=10, head=8, pivot=6.0, rel=True,
          near=Arm(40 + 10 * math.sin(i), 0.8), far=Arm(150, 0.8), nf=Leg(60, 0.85, 20), ff=Leg(110, 0.9, 20))
        for i in range(8)
    ], 60, loop=True, face="hurt")

    # ---- on the floor --------------------------------------------------------
    # Lying is measured: the plant step puts the lowest paint on the floor.
    lie_y = 30.0
    face_up = K(tilt=-90, torso=-3, head=-12, y=lie_y, x=8, near=Arm(-150, 0.8), far=Arm(166, 0.9),
                nf=Leg(-14, 0.88, 10), ff=Leg(4, 0.98, 20))
    rows["prone_face_up"] = Row([
        replace(face_up, torso=face_up.torso + 1.2 * s, head=face_up.head + 1.2 * s) for s in _cycle(4)
    ], 160, loop=True, plant="each", face="hurt", blink=[1, 1, 0, 1])
    face_down = K(tilt=90, torso=-4, head=-24, y=lie_y, x=-8, near=Arm(150, 0.5), far=Arm(170, 0.6),
                  nf=Leg(182, 0.97, 30), ff=Leg(-168, 0.9, 50))
    rows["prone_face_down"] = Row([
        replace(face_down, torso=face_down.torso + 1.2 * s, head=face_down.head - 1.2 * s) for s in _cycle(4)
    ], 160, loop=True, plant="each", face="hurt", blink=[1, 1, 0, 1])
    # Dazed on his back, propped up on both elbows, looking down himself.
    propped = K(tilt=-56, torso=-8, head=20, y=lie_y * 0.8, x=6, near=Arm(132, 0.5), far=Arm(144, 0.52),
                nf=Leg(-8, 0.9, 10), ff=Leg(6, 0.98, 20))
    rows["prone"] = Row([
        replace(propped, head=propped.head + 3 * s, torso=propped.torso + 1.0 * s) for s in _cycle(4)
    ], 160, loop=True, plant="each", face="worried", blink=[0, 1, 0, 0])

    # Knocked down: tipped back off his feet, slammed flat, a bounce, lying.
    rows["knockdown"] = Row([
        K(tilt=-24, torso=-10, head=-16, x=-2, near=Arm(20, 0.8), far=Arm(40, 0.8), nf=Leg(70, 0.95, 20), ff=Leg(84, 0.97, 20)),
        K(tilt=-58, torso=-6, head=-10, y=lie_y * 0.5, x=2, near=Arm(-40, 0.86), far=Arm(-20, 0.86), nf=Leg(30, 0.9, 20), ff=Leg(46, 0.95, 20)),
        K(tilt=-92, torso=-2, head=-14, y=lie_y + 1, x=8, near=Arm(-170, 0.8), far=Arm(-196, 0.86), nf=Leg(-30, 0.9, 20), ff=Leg(-22, 0.97, 20)),
        K(tilt=-86, torso=-8, head=-4, y=lie_y - 5, x=8, near=Arm(-120, 0.8), far=Arm(-150, 0.86), nf=Leg(-50, 0.85, 20), ff=Leg(-34, 0.95, 20)),
        K(tilt=-90, torso=-5, head=-9, y=lie_y, x=8, near=Arm(-156, 0.72), far=Arm(-196, 0.86), nf=Leg(-36, 0.66, 10), ff=Leg(-8, 0.97, 20)),
        face_up,
    ], 70, plant="row", face="hurt", blink=[0, 1, 1, 0, 1, 1])

    sit = K(tilt=-60, torso=40, head=8, y=lie_y * 0.72, x=6, near=Arm(130, 0.94), far=Arm(146, 0.96),
            nf=Leg(-6, 0.86, 10), ff=Leg(4, 0.97, 20))
    kneel = K(torso=26, head=-6, y=17, x=-2, near=Arm(80, 0.72), far=Arm(96, 0.8), nf=Foot(8, 0, -4), ff=Foot(-8, 0, 26))
    rows["getup"] = Row([
        face_up, sit, replace(sit, tilt=-24, torso=44, y=lie_y * 0.55, nf=Leg(16, 0.62, 10), ff=Leg(54, 0.5, 30), near=Arm(100, 0.9), far=Arm(120, 0.92)),
        kneel, tween(kneel, STAND, 0.55), STAND,
    ], 80, plant="each", face="stern")
    # Rolled up backwards over his shoulders onto his feet.
    rows["getup_roll"] = Row([
        face_up,
        K(tilt=-130, torso=30, head=16, y=0.0, pivot=6.0, rel=True, near=Arm(40, 0.6), far=Arm(60, 0.6), nf=Leg(30, 0.6, 20), ff=Leg(40, 0.62, 20)),
        K(tilt=-200, torso=34, head=18, y=0.0, pivot=6.0, rel=True, near=Arm(40, 0.6), far=Arm(60, 0.6), nf=Leg(20, 0.58, 20), ff=Leg(30, 0.6, 20)),
        K(tilt=-280, torso=34, head=16, y=0.0, pivot=6.0, rel=True, near=Arm(60, 0.6), far=Arm(70, 0.6), nf=Leg(30, 0.6, 20), ff=Leg(40, 0.62, 20)),
        kneel, STAND,
    ], 70, plant="each", face="stern")
    # Up with a sweep: propped on his hands, the front leg swept out low.
    rows["getup_attack"] = Row([
        face_up,
        replace(sit, near=Arm(150, 0.9), far=Arm(160, 0.92), nf=Leg(-50, 0.5, 10)),
        K(tilt=-50, torso=28, head=-4, y=lie_y * 0.7, x=-4, near=Arm(140, 0.95), far=Arm(160, 0.95), nf=Leg(-4, 0.99, 30), ff=Leg(40, 0.55, 10)),
        K(tilt=-40, torso=26, head=-6, y=lie_y * 0.66, x=-4, near=Arm(146, 0.95), far=Arm(166, 0.95), nf=Leg(8, 0.99, 30), ff=Leg(46, 0.55, 10)),
        kneel, STAND,
    ], 60, plant="each", face="stern")

    # The tech: the landing caught on one knee, a palm slapped flat on the
    # floor ahead of him, the other arm flung back; then up.
    brace = K(tilt=48, torso=32, head=-34, y=20, near=Hand(27.0, 10.0, 6.0), far=Arm(190, 0.9),
              nf=Foot(12, 0, -4), ff=Foot(-14, 3, 30))
    rows["tech"] = Row([
        replace(brace, tilt=14, torso=16, head=-16, y=12, near=Arm(30, 0.95), far=Arm(150, 0.84), ff=Foot(-12, 3, 40)),
        brace,
        replace(brace, tilt=40, torso=28, head=-30, y=19, near=Hand(26.0, 11.5, 14.0), far=Arm(164, 0.88)),
        tween(brace, STAND, 0.6),
        STAND,
    ], 60, plant="each", face="stern")
    # Out of the brace into a forward roll, up on his feet.
    rows["tech_roll"] = Row([
        brace,
        K(tilt=60, torso=36, head=20, y=0.0, pivot=6.0, rel=True, near=Arm(40, 0.6), far=Arm(56, 0.6), nf=Leg(20, 0.6, 20), ff=Leg(30, 0.6, 20)),
        K(tilt=150, torso=36, head=20, y=0.0, pivot=6.0, rel=True, near=Arm(40, 0.6), far=Arm(56, 0.6), nf=Leg(16, 0.58, 20), ff=Leg(26, 0.58, 20)),
        K(tilt=250, torso=36, head=18, y=0.0, pivot=6.0, rel=True, near=Arm(50, 0.6), far=Arm(64, 0.6), nf=Leg(20, 0.6, 20), ff=Leg(30, 0.6, 20)),
        K(tilt=330, torso=30, head=-6, y=4, pivot=6.0, rel=True, near=Arm(60, 0.72), far=Arm(76, 0.72), nf=Leg(50, 0.7, 10), ff=Leg(70, 0.72, 10)),
        STAND,
    ], 60, plant="each", face="stern")

    # ---- defence ---------------------------------------------------------------
    # Propless, his guard is his forearms crossed before his face, knees bent.
    guard = K(torso=10, head=10, y=6, x=-1, near=Arm(-10, 0.5), far=Arm(4, 0.56), nf=Foot(5, 0, -4), ff=Foot(-6, 0, 10))
    rows["shield_raise"] = Row([tween(STAND, guard, 0.4), tween(STAND, guard, 0.85), guard], 40, plant="each", face="stern")
    rows["block"] = Row([
        replace(guard, torso=guard.torso + 0.8 * s, y=guard.y + 0.5 * s) for s in _cycle(4)
    ], 120, loop=True, plant="each", face="stern", blink=[0, 0, 0, 1])
    rows["shield_hit"] = Row([
        replace(guard, tilt=-6, torso=-4, head=-2, x=-6, near=Arm(-30, 0.46), far=Arm(-14, 0.5), nf=Foot(8, 0, -16), ff=Foot(-8, 0, 16)),
        replace(guard, tilt=-3, torso=2, head=4, x=-4, near=Arm(-20, 0.48), nf=Foot(6, 0, -10)),
        guard,
    ], 50, plant="each", face="worried", blink=[1, 0, 0])
    rows["shield_release"] = Row([tween(guard, STAND, 0.4), tween(guard, STAND, 0.8), STAND], 50, plant="each")

    def roll(sign: float) -> List[Key]:
        out = [K(torso=20, head=10, y=10, near=Arm(70, 0.7), far=Arm(84, 0.72), nf=Foot(4 * sign), ff=Foot(-4 * sign, 0, 20))]
        for turn in (70, 150, 230, 310):
            out.append(K(tilt=sign * turn, torso=38, head=22, y=8, pivot=6.0, rel=True,
                         near=Arm(50, 0.58), far=Arm(64, 0.58), nf=Leg(14, 0.56, 20), ff=Leg(24, 0.56, 20)))
        out.append(K(torso=16, head=4, y=8, near=Arm(80, 0.78), far=Arm(92, 0.8), nf=Foot(3), ff=Foot(-3, 0, 14)))
        return out

    rows["roll"] = Row(roll(1.0), 60, plant="each", face="stern")
    rows["roll_back"] = Row(roll(-1.0), 60, plant="each", face="stern")
    # The sidestep: he sways back out of it, belly in, hands raised.
    sway = K(tilt=-6, torso=-14, head=-12, x=-4, near=Arm(-110, 0.72), far=Arm(-130, 0.7), nf=Foot(2, 0, -24), ff=Foot(-7))
    rows["spot_dodge"] = Row([tween(STAND, sway, 0.6), sway, replace(sway, torso=-12, head=-10), tween(sway, STAND, 0.6), STAND],
                             60, plant="each", face="surprised")
    # In the air: balled up, arms crossed over his head.
    ball = K(tilt=18, torso=26, head=24, pivot=6.0, near=Arm(-30, 0.48), far=Arm(-10, 0.52), nf=Leg(10, 0.55, 20), ff=Leg(30, 0.55, 20))
    rows["air_dodge"] = Row([tween(K(near=Arm(40), far=Arm(60), nf=Leg(70, 0.8, 10), ff=Leg(90, 0.9, 10)), ball, 0.5),
                             ball, replace(ball, tilt=24), tween(ball, K(near=Arm(40), far=Arm(60), nf=Leg(70, 0.8, 10), ff=Leg(90, 0.9, 10)), 0.6)],
                            60, face="stern")

    # ---- ledge -----------------------------------------------------------------
    # The ledge is ahead of him at the height of his raised hands; he hangs
    # where he stood, his feet dangling.
    hang = K(torso=4, head=-14, y=-3, near=Arm(-74, 0.97), far=Arm(-80, 0.97), nf=Leg(96, 0.95, 30), ff=Leg(104, 0.9, 34))
    rows["ledge_catch"] = Row([
        K(tilt=-20, torso=-6, head=-20, y=-3, x=-4, near=Arm(-96, 0.97), far=Arm(-104, 0.97), nf=Leg(120, 0.95, 30), ff=Leg(130, 0.92, 34)),
        K(tilt=10, torso=6, head=-12, y=-2, near=Arm(-72, 0.97), far=Arm(-78, 0.97), nf=Leg(76, 0.95, 30), ff=Leg(84, 0.9, 34)),
        K(tilt=4, torso=6, head=-12, y=-3, near=Arm(-74, 0.97), far=Arm(-80, 0.97), nf=Leg(88, 0.95, 30), ff=Leg(96, 0.9, 34)),
        hang,
    ], 60, face="surprised")
    rows["ledge_grab"] = Row([
        replace(hang, torso=hang.torso + 1.5 * s, nf=Leg(96 + 4 * s, 0.95, 30), ff=Leg(104 - 3 * s, 0.9, 34)) for s in _cycle(4)
    ], 140, loop=True, face="worried", blink=[0, 0, 1, 0])
    # Hauled up on his elbows, a knee over, and stood.
    rows["ledge_climb"] = Row([
        hang,
        K(torso=10, head=-10, y=-2, near=Arm(-20, 0.6), far=Arm(-30, 0.6), nf=Leg(90, 0.95, 30), ff=Leg(96, 0.9, 30)),
        K(torso=20, head=-6, y=-10, near=Arm(60, 0.62), far=Arm(50, 0.62), nf=Leg(10, 0.6, 10), ff=Leg(96, 0.9, 30)),
        K(torso=24, head=-6, y=-6, near=Arm(80, 0.7), far=Arm(74, 0.72), nf=Foot(8, 6, 0), ff=Leg(110, 0.8, 30)),
        K(torso=14, head=-4, y=4, near=Arm(84, 0.82), far=Arm(86, 0.86), nf=Foot(6), ff=Foot(-4, 4, 20)),
        STAND,
    ], 70, face="stern")
    # A vault: palms pressed down, both knees swung up over the edge together.
    rows["ledge_getup"] = Row([
        hang,
        K(torso=14, head=-6, y=-6, near=Arm(30, 0.66), far=Arm(24, 0.66), nf=Leg(60, 0.8, 20), ff=Leg(70, 0.8, 20)),
        K(tilt=-10, torso=30, head=-4, y=-12, near=Arm(80, 0.94), far=Arm(84, 0.94), nf=Leg(10, 0.55, 10), ff=Leg(20, 0.55, 10)),
        K(torso=24, head=-6, y=10, near=Arm(70, 0.8), far=Arm(80, 0.82), nf=Foot(6, 0, 0), ff=Foot(-4, 0, 20)),
        tween(K(torso=24, head=-6, y=10, near=Arm(70, 0.8), far=Arm(80, 0.82), nf=Foot(6), ff=Foot(-4, 0, 20)), STAND, 0.6),
        STAND,
    ], 60, face="stern")
    rows["ledge_roll"] = Row([
        hang,
        K(torso=20, head=-6, y=-8, near=Arm(50, 0.66), far=Arm(44, 0.66), nf=Leg(40, 0.7, 20), ff=Leg(60, 0.75, 20)),
        K(tilt=90, torso=36, head=20, y=4, pivot=6.0, rel=True, near=Arm(50, 0.58), far=Arm(64, 0.58), nf=Leg(14, 0.56, 20), ff=Leg(24, 0.56, 20)),
        K(tilt=200, torso=38, head=22, y=6, pivot=6.0, rel=True, near=Arm(50, 0.58), far=Arm(64, 0.58), nf=Leg(14, 0.56, 20), ff=Leg(24, 0.56, 20)),
        K(tilt=300, torso=36, head=10, y=8, pivot=6.0, rel=True, near=Arm(60, 0.62), far=Arm(72, 0.62), nf=Leg(40, 0.62, 20), ff=Leg(56, 0.64, 20)),
        K(torso=14, head=2, y=6, near=Arm(80, 0.8), far=Arm(92, 0.82), nf=Foot(3), ff=Foot(-3, 0, 12)),
    ], 60, face="stern")
    rows["ledge_jump"] = Row([
        hang,
        K(torso=14, head=-4, y=-4, near=Arm(30, 0.66), far=Arm(24, 0.66), nf=Leg(50, 0.7, 20), ff=Leg(64, 0.72, 20)),
        K(torso=-6, head=-14, y=-2, near=Arm(-84, 0.98), far=Arm(-70, 0.96), nf=Leg(94, 0.99, 40), ff=Leg(104, 0.99, 44)),
        K(torso=-4, head=-10, y=-4, near=Arm(-60, 0.92), far=Arm(-44, 0.9), nf=Leg(70, 0.78, 20), ff=Leg(98, 0.92, 34)),
        K(torso=2, head=-4, y=-8, near=Arm(10, 0.84), far=Arm(28, 0.86), nf=Leg(56, 0.7, 10), ff=Leg(90, 0.84, 26)),
    ], 60, face="delighted")

    # ---- grab ------------------------------------------------------------------
    hold = K(torso=12, head=-4, y=4, x=2, near=Arm(14, 0.84), far=Arm(24, 0.8), nf=Foot(8, 0, -6), ff=Foot(-8, 0, 16))
    rows["grab"] = Row([
        K(torso=4, head=-2, y=2, x=-1, near=Arm(110, 0.8), far=Arm(120, 0.8), ff=Foot(-2, 0, 6)),
        K(torso=18, head=-8, y=5, x=4, near=Arm(4, 1.0), far=Arm(10, 1.0), nf=Foot(12, 0, -8), ff=Foot(-10, 0, 22)),
        K(torso=20, head=-8, y=5, x=5, near=Arm(10, 0.94), far=Arm(18, 0.92), nf=Foot(13, 0, -8), ff=Foot(-10, 0, 22)),
        tween(K(torso=20, head=-8, y=5, x=5, near=Arm(10, 0.94), far=Arm(18, 0.92), nf=Foot(13, 0, -8), ff=Foot(-10, 0, 22)), hold, 0.5),
        hold,
    ], 50, plant="each", face="stern")
    rows["grab_hold"] = Row([
        replace(hold, torso=hold.torso + 1.0 * s, y=hold.y + 0.5 * s) for s in _cycle(4)
    ], 140, loop=True, plant="each", face="stern", blink=[0, 1, 0, 0])
    # A short headbutt over the hold: the knowing man's argument.
    rows["pummel"] = Row([
        replace(hold, torso=4, head=-14, x=0),
        replace(hold, torso=22, head=18, x=4),
        replace(hold, torso=18, head=10, x=3),
        hold,
    ], 50, plant="each", face="stern")
    rows["throw_forward"] = Row([
        hold,
        replace(hold, torso=0, head=-6, x=-2, near=Arm(60, 0.62), far=Arm(70, 0.6), nf=Foot(4), ff=Foot(-10, 0, 20)),
        K(torso=24, head=-10, y=7, x=6, near=Arm(-6, 1.0), far=Arm(4, 1.0), nf=Foot(16, 0, -10), ff=Foot(-14, 2, 34)),
        K(torso=26, head=-10, y=7, x=6, near=Arm(0, 1.0), far=Arm(8, 1.0), nf=Foot(16, 0, -10), ff=Foot(-14, 2, 34)),
        K(torso=14, head=-4, y=3, x=3, near=Arm(50, 0.9), far=Arm(60, 0.9), nf=Foot(10), ff=Foot(-8, 0, 12)),
        STAND,
    ], 60, plant="each", face="stern")
    # Heaved up over his own head and thrown down behind him.
    rows["throw_back"] = Row([
        hold,
        K(torso=-6, head=-12, y=1, near=Arm(-40, 0.86), far=Arm(-30, 0.84), nf=Foot(6, 0, -10), ff=Foot(-6)),
        K(tilt=-6, torso=-22, head=-20, y=4, x=-3, near=Arm(-120, 0.95), far=Arm(-112, 0.95), nf=Foot(8, 0, -20), ff=Foot(-8)),
        K(tilt=-8, torso=-26, head=-18, y=6, x=-4, near=Arm(-170, 0.98), far=Arm(-160, 0.98), nf=Foot(8, 0, -22), ff=Foot(-10, 0, 0)),
        K(torso=-10, head=-6, y=3, x=-2, near=Arm(150, 0.9), far=Arm(140, 0.9), nf=Foot(6, 0, -8), ff=Foot(-8)),
        STAND,
    ], 60, plant="each", face="stern")
    rows["throw_up"] = Row([
        hold,
        K(torso=16, head=-6, y=12, near=Arm(40, 0.84), far=Arm(50, 0.82), nf=Foot(4), ff=Foot(-4, 0, 10)),
        K(torso=-6, head=-18, y=-1, near=Arm(-80, 0.98), far=Arm(-72, 0.98), nf=Foot(3, 3, 30), ff=Foot(-3, 3, 34)),
        K(torso=-8, head=-20, y=-1, near=Arm(-92, 1.0), far=Arm(-84, 1.0), nf=Foot(3, 3, 30), ff=Foot(-3, 3, 34)),
        K(torso=-2, head=-8, y=1, near=Arm(-30, 0.88), far=Arm(-20, 0.88), nf=Foot(3), ff=Foot(-3)),
        STAND,
    ], 60, plant="each", face="stern")
    rows["throw_down"] = Row([
        hold,
        K(torso=-8, head=-14, y=0, near=Arm(-70, 0.92), far=Arm(-62, 0.9), nf=Foot(6, 0, -10), ff=Foot(-6)),
        K(torso=36, head=6, y=16, x=2, near=Arm(70, 1.0), far=Arm(76, 1.0), nf=Foot(12, 0, -6), ff=Foot(-10, 0, 30)),
        K(torso=38, head=8, y=17, x=2, near=Arm(76, 1.0), far=Arm(82, 1.0), nf=Foot(12, 0, -6), ff=Foot(-10, 0, 30)),
        K(torso=18, head=-2, y=8, near=Arm(84, 0.86), far=Arm(88, 0.88), nf=Foot(8), ff=Foot(-6, 0, 12)),
        STAND,
    ], 60, plant="each", face="stern")

    # Held: hauled up onto his toes, pushing at the hand that holds him.
    held = K(tilt=-4, torso=-10, head=-10, y=-1, x=1, near=Arm(-4, 0.66), far=Arm(14, 0.62),
             nf=Foot(4, 2, 30), ff=Foot(-3, 1, 26))
    rows["grabbed"] = Row([
        replace(held, near=Arm(-4 + 8 * s, 0.66), far=Arm(14 - 8 * s, 0.62), torso=held.torso + 1.5 * s) for s in _cycle(4)
    ], 120, loop=True, plant="each", face="worried")
    rows["grabbed_pummel"] = Row([
        replace(held, torso=-18, head=-24, near=Arm(30, 0.7), far=Arm(50, 0.66)),
        replace(held, torso=-15, head=-20, near=Arm(20, 0.68), far=Arm(40, 0.64)),
        held,
    ], 60, plant="each", face="hurt", blink=[1, 1, 0])
    rows["grab_escape"] = Row([
        held,
        K(torso=8, head=-4, x=-1, near=Arm(0, 1.0), far=Arm(10, 1.0), nf=Foot(4, 0, -6), ff=Foot(-4)),
        K(torso=-4, head=-6, x=-5, y=3, near=Arm(40, 0.84), far=Arm(56, 0.84), nf=Foot(-2, 4, 20), ff=Foot(-9)),
        K(torso=2, head=-2, x=-2, y=1, near=Arm(80, 0.88), far=Arm(88, 0.9), nf=Foot(1), ff=Foot(-4)),
    ], 60, plant="each", face="stern")
    # ---- the rest the game asks for -------------------------------------------
    # The forward smash's wind-up (``smash_forward`` frame 3), held and shaking.
    rows["smash_charge"] = Row([
        K(torso=-14 + 1.2 * s, head=9, x=-4.5, y=3 + 0.5 * s, near=Arm(176 + 3 * s, 0.8), far=Arm(160 + 3 * s, 0.8),
          nf=Foot(-2), ff=Foot(-2))
        for s in (1, -1, 0.5, -0.5)
    ], 50, loop=True, plant="each", face="stern")
    # A parry: one open palm snapped out flat against the blow, weight back.
    rows["parry"] = Row([
        K(torso=-4, head=-2, x=-1, near=Arm(-20, 0.7), far=Arm(100, 0.8), nf=Foot(4, 0, -6), ff=Foot(-6)),
        K(torso=-8, head=-6, x=-3, near=Arm(-8, 1.0), far=Arm(130, 0.8), nf=Foot(6, 0, -12), ff=Foot(-8)),
        K(torso=-4, head=-2, x=-2, near=Arm(40, 0.86), far=Arm(100, 0.84), nf=Foot(4, 0, -6), ff=Foot(-6)),
    ], 50, plant="each", face="stern")
    # Dizzy (his guard broken): knees gone soft, swaying round over his feet,
    # the head lolling and the arms hanging loose.
    rows["dizzy"] = Row([
        K(tilt=6 * math.sin(a), torso=12 + 10 * math.sin(a), head=8 + 14 * math.cos(a), x=3 * math.sin(a), y=5,
          near=Arm(84 + 26 * math.sin(a), 0.92), far=Arm(96 - 26 * math.sin(a), 0.92), nf=Foot(3, 0, -4), ff=Foot(-4, 0, 6))
        for a in (2.0 * math.pi * i / 6 for i in range(6))
    ], 130, loop=True, plant="each", face="worried", blink=[0, 1, 1, 0, 1, 1])
    return rows


ROWS: Dict[str, Row] = _rows()
#: The order the sprite target publishes them in, with frames and timing.
VOCABULARY_ROWS: List[Tuple[str, int, int]] = [(name, len(row.poses), row.ms) for name, row in ROWS.items()]
#: The face each row wears.
FACE_OF: Dict[str, str] = {name: row.face for name, row in ROWS.items()}
#: ``frame.plant`` entries for the side documents.
PLANT: Dict[str, str] = {name: row.plant for name, row in ROWS.items() if row.plant}


def vocabulary_clips(doc: dict) -> Dict[str, dict]:
    """Every vocabulary row, solved on this side document's skeleton."""
    solver = PoseSolver(doc)
    return {name: solver.clip(row) for name, row in ROWS.items()}


__all__ = [
    "FACE_OF", "PLANT", "ROWS", "STAND", "VOCABULARY_ROWS", "Arm", "Foot", "Hand", "Key", "Leg", "PoseSolver", "vocabulary_clips",
]
