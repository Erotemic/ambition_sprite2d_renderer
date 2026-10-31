"""Mary-O's fighter body language: everything a platform fighter shows that
is not an attack (``fighter_motion_vocabulary.yaml``, scope ``fighter_core``).

Posed on the same rigid SVG rig as her walk and her attacks
(``_mary_o_v2_attacks``): limb angles 0 = hanging down, +90 = to her front,
180 = straight up, -90 = behind her. ``trunk_angle`` pitches torso, head and
arms about the hips, ``body_angle`` turns the whole figure about the torso,
``head_angle`` tilts the head; + leans toward her front in each.

Rules every row keeps:

- a grounded frame stands on her shoe line, and a body on the floor lies on
  it (``bob`` is measured per frame, not guessed);
- a recoil ENDS on its settled pose, because the game holds a clip's last
  frame for the whole hitstun;
- ``turnaround`` ends facing her front, because the game draws it in the new
  facing;
- no row aliases another: each has its own silhouette.

Hosted by the TALL sheet only, the form the Smash fighter ``mary_o_tall``
wears; the small form is a platformer body and the fire form is not a
fighter.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, List, Tuple

from ._mary_o_v2_model import Pose

P = Pose

#: Her airborne carriage, the pose a jump settles into (``jump``'s recover).
_AIR = dict(bob=-1.0, leg_front_angle=45, leg_back_angle=-32, arm_front_angle=148, arm_back_angle=-22)


def _tuck(angle: float, **kw) -> Pose:
    """A rolled-up ball turned ``angle`` degrees: knees to her chest, arms
    wrapped round them. A roll, a tumble and a flip are this at a sequence of
    angles."""
    base = dict(
        trunk_angle=24,
        head_angle=18,
        leg_front_angle=96,
        leg_back_angle=84,
        leg_front_scale=0.62,
        leg_back_scale=0.62,
        arm_front_angle=62,
        arm_back_angle=48,
        body_angle=angle,
    )
    base.update(kw)
    return P(**base)


# (frame ms, poses). Frame counts are the pose counts.
_ROWS: Dict[str, Tuple[int, List[Pose]]] = {
    # -- movement ---------------------------------------------------------
    # Looking up: chin raised, a little back on her heels.
    "idle_look_up": (200, [
        P(bob=-0.33, trunk_angle=-5, head_angle=-26, leg_front_angle=22, leg_back_angle=12, arm_front_angle=6, arm_back_angle=-8),
    ]),
    # The run leans into the speed her walk never has, the arms pump and the
    # stride opens past her skirt. Contact, pass, push, flight.
    "run": (70, [
        P(trunk_angle=12, bob=0, leg_front_angle=58, leg_back_angle=-22, arm_front_angle=-46, arm_back_angle=58),
        P(trunk_angle=14, bob=-0.25, leg_front_angle=24, leg_back_angle=6, leg_back_scale=0.78, arm_front_angle=-6, arm_back_angle=14),
        P(trunk_angle=15, bob=-0.16, leg_front_angle=-30, leg_back_angle=52, arm_front_angle=60, arm_back_angle=-50),
        P(trunk_angle=14, bob=-0.07, leg_front_angle=10, leg_front_scale=0.78, leg_back_angle=26, arm_front_angle=16, arm_back_angle=-6),
    ]),
    # The first burst: a low lunge off the back foot.
    "dash_startup": (60, [
        P(trunk_angle=22, bob=0.07, body_lean=-0.4, leg_front_angle=40, leg_front_scale=0.8, leg_back_angle=-30, arm_front_angle=-60, arm_back_angle=-40),
        P(trunk_angle=26, bob=0.45, body_lean=0.6, leg_front_angle=62, leg_back_angle=-48, arm_front_angle=40, arm_back_angle=-70),
    ]),
    # The dash itself: longer and lower than the run, arms thrown back.
    "dash": (70, [
        P(trunk_angle=20, bob=0.42, leg_front_angle=66, leg_back_angle=-40, arm_front_angle=-62, arm_back_angle=-34),
        P(trunk_angle=20, bob=0.3, leg_front_angle=30, leg_front_scale=0.8, leg_back_angle=-8, leg_back_scale=0.8, arm_front_angle=-40, arm_back_angle=-56),
        P(trunk_angle=21, bob=0.42, leg_front_angle=-34, leg_back_angle=58, arm_front_angle=-70, arm_back_angle=-26),
    ]),
    # Drawn in her NEW facing: she starts looking back the way she faced,
    # weight still on the old side, and ends square to her front.
    "turnaround": (70, [
        P(bob=-0.5, mode="lookback", trunk_angle=-10, body_lean=-0.5, leg_front_angle=-12, leg_back_angle=30, arm_front_angle=-40, arm_back_angle=30),
        P(bob=-0.5, trunk_angle=-4, head_angle=-6, leg_front_angle=10, leg_back_angle=22, arm_front_angle=30, arm_back_angle=-26),
        P(bob=-0.33, trunk_angle=3, leg_front_angle=22, leg_back_angle=12, arm_front_angle=10, arm_back_angle=-6),
    ]),
    # A walk settling: the feet come together, the arms swing through.
    "walk_stop": (80, [
        P(bob=-0.33, trunk_angle=4, leg_front_angle=34, leg_back_angle=2, arm_front_angle=26, arm_back_angle=-20),
        P(bob=-0.33, trunk_angle=-2, leg_front_angle=22, leg_back_angle=12, arm_front_angle=8, arm_back_angle=-4),
    ]),
    # The run brake: the front foot planted far ahead, hips dropped behind
    # it, the upper body thrown back against the speed and the arms still
    # going forward.
    "run_stop": (70, [
        P(trunk_angle=-22, bob=0.33, body_lean=0.7, leg_front_angle=62, leg_back_angle=-26, leg_back_scale=0.72, arm_front_angle=118, arm_back_angle=72, head_angle=-8),
        P(trunk_angle=-16, bob=-0.43, body_lean=0.07, leg_front_angle=52, leg_back_angle=-20, leg_back_scale=0.76, arm_front_angle=96, arm_back_angle=52, head_angle=-4),
        P(trunk_angle=-6, bob=-0.37, body_lean=-0.2, leg_front_angle=34, leg_back_angle=0, arm_front_angle=40, arm_back_angle=12),
    ]),
    # The beat a short hop is decided in: knees folded, arms swung back.
    "jump_squat": (50, [
        P(trunk_angle=14, bob=0.87, leg_front_angle=34, leg_front_scale=0.76, leg_back_angle=4, leg_back_scale=0.76, arm_front_angle=-38, arm_back_angle=-50),
        P(trunk_angle=18, bob=1.1, leg_front_angle=38, leg_front_scale=0.66, leg_back_angle=2, leg_back_scale=0.66, arm_front_angle=-56, arm_back_angle=-62),
    ]),
    # Her second jump is a forward somersault, landing in her jump pose.
    "double_jump": (60, [
        _tuck(70, body_lean=-5.08, bob=-1.0),
        _tuck(160, body_lean=-1.83, bob=-2),
        _tuck(250, body_lean=-0.67, bob=-1.0),
        _tuck(330, body_lean=-3.25, bob=-1.0, leg_front_scale=0.8, leg_back_scale=0.8),
        P(body_lean=1.34, bob=-1.8, leg_front_angle=34, leg_back_angle=-22, arm_front_angle=164, arm_back_angle=-150),
    ]),
    # Falling: both arms up and out, the legs reaching for the floor.
    "fall": (120, [
        P(bob=-1.0, trunk_angle=-4, leg_front_angle=26, leg_back_angle=4, arm_front_angle=126, arm_back_angle=-118, head_angle=8),
        P(bob=-1.0, trunk_angle=-3, leg_front_angle=30, leg_back_angle=0, arm_front_angle=134, arm_back_angle=-126, head_angle=8),
    ]),
    # A light landing gives a little at the knees.
    "land_light": (60, [
        P(trunk_angle=8, bob=0.2, leg_front_angle=30, leg_front_scale=0.84, leg_back_angle=6, leg_back_scale=0.84, arm_front_angle=40, arm_back_angle=-34),
        P(trunk_angle=3, bob=0.25, leg_front_angle=24, leg_front_scale=0.94, leg_back_angle=10, leg_back_scale=0.94, arm_front_angle=16, arm_back_angle=-12),
    ]),
    # A hard landing squashes her: knees deep, trunk over them, arms braced.
    "land_hard": (70, [
        P(trunk_angle=30, bob=1.7, leg_front_angle=44, leg_front_scale=0.6, leg_back_angle=-6, leg_back_scale=0.6, arm_front_angle=34, arm_back_angle=30, head_angle=-14),
        P(trunk_angle=24, bob=1.14, leg_front_angle=42, leg_front_scale=0.66, leg_back_angle=-4, leg_back_scale=0.66, arm_front_angle=24, arm_back_angle=10, head_angle=-6),
        P(trunk_angle=10, bob=0.13, leg_front_angle=30, leg_front_scale=0.84, leg_back_angle=6, leg_back_scale=0.84, arm_front_angle=14, arm_back_angle=-8),
    ]),
    # Off balance at an edge: up on the front foot, the trunk tipped out over
    # the drop and both arms windmilling to pull it back.
    "teeter_start": (70, [
        P(bob=-0.5, trunk_angle=26, body_lean=-1.23, leg_front_angle=10, leg_back_angle=-24, arm_front_angle=150, arm_back_angle=-140, head_angle=14),
        P(bob=-0.5, trunk_angle=18, body_lean=0.4, leg_front_angle=12, leg_back_angle=-30, arm_front_angle=-60, arm_back_angle=110, head_angle=10),
    ]),
    "teeter": (110, [
        P(bob=-0.33, trunk_angle=16, body_lean=0.4, leg_front_angle=14, leg_back_angle=-34, arm_front_angle=-50, arm_back_angle=120, head_angle=12),
        P(trunk_angle=10, body_lean=0.2, leg_front_angle=16, leg_back_angle=-26, arm_front_angle=60, arm_back_angle=-60, head_angle=6),
        P(bob=-0.5, trunk_angle=20, body_lean=-0.17, leg_front_angle=12, leg_back_angle=-38, arm_front_angle=150, arm_back_angle=-130, head_angle=16),
    ]),
    # Losing it entirely is a stumble forward, a hand out for the floor.
    "stumble": (70, [
        P(trunk_angle=30, bob=0.1, body_lean=-1.07, leg_front_angle=58, leg_back_angle=-34, arm_front_angle=80, arm_back_angle=-90, head_angle=10),
        P(trunk_angle=22, bob=-0.56, body_lean=0.4, leg_front_angle=36, leg_back_angle=-12, leg_back_scale=0.8, arm_front_angle=60, arm_back_angle=-60, head_angle=6),
        P(bob=-0.33, trunk_angle=6, leg_front_angle=24, leg_back_angle=8, arm_front_angle=20, arm_back_angle=-14),
    ]),
    "platform_drop": (70, [
        P(trunk_angle=8, bob=0.33, leg_front_angle=30, leg_front_scale=0.8, leg_back_angle=4, leg_back_scale=0.8, arm_front_angle=30, arm_back_angle=-20),
        P(bob=-0.6, trunk_angle=-4, leg_front_angle=12, leg_back_angle=-4, arm_front_angle=120, arm_back_angle=-110),
    ]),
    "fall_special": (130, [
        P(bob=-1.0, trunk_angle=10, head_angle=24, leg_front_angle=30, leg_back_angle=-10, arm_front_angle=40, arm_back_angle=-60),
        P(bob=-1.0, trunk_angle=12, head_angle=26, leg_front_angle=24, leg_back_angle=-4, arm_front_angle=30, arm_back_angle=-50),
    ]),
    "air_land": (60, [
        P(trunk_angle=18, bob=0.83, leg_front_angle=40, leg_front_scale=0.7, leg_back_angle=-4, leg_back_scale=0.7, arm_front_angle=70, arm_back_angle=-70),
        P(trunk_angle=8, bob=0.27, leg_front_angle=28, leg_front_scale=0.88, leg_back_angle=6, leg_back_scale=0.88, arm_front_angle=30, arm_back_angle=-24),
    ]),
    "footstool_jump": (70, [
        P(bob=-1.8, trunk_angle=-6, leg_front_angle=4, leg_back_angle=-6, arm_front_angle=170, arm_back_angle=-170),
        P(bob=-1.4, leg_front_angle=40, leg_back_angle=-26, arm_front_angle=150, arm_back_angle=-60),
    ]),
    # Stepped on from above: crushed down, head ducked, arms over it.
    "footstooled": (70, [
        P(body_lean=-0.17, trunk_angle=20, bob=1.17, head_angle=30, leg_front_angle=40, leg_front_scale=0.66, leg_back_angle=-20, leg_back_scale=0.66, arm_front_angle=150, arm_back_angle=130),
        P(body_lean=-0.5, bob=-0.33, trunk_angle=16, head_angle=24, leg_front_angle=30, leg_back_angle=-10, arm_front_angle=120, arm_back_angle=-100),
    ]),
    # -- struck -----------------------------------------------------------
    # The generic recoil, for whatever cannot say where it was struck.
    "hit": (60, [
        P(bob=-0.33, trunk_angle=-18, head_angle=-16, body_lean=5.23, leg_front_angle=34, leg_back_angle=-6, arm_front_angle=60, arm_back_angle=40),
        P(bob=-0.33, trunk_angle=-12, head_angle=-8, body_lean=-0.4, leg_front_angle=30, leg_back_angle=0, arm_front_angle=40, arm_back_angle=24),
    ]),
    # At the head: the head snaps back first and drags the trunk, the arms fly
    # up in front, the weight goes onto the back heel.
    "hit_high": (60, [
        P(bob=-0.33, trunk_angle=-14, head_angle=-34, body_lean=-0.7, leg_front_angle=40, leg_back_angle=-14, arm_front_angle=118, arm_back_angle=86),
        P(bob=-0.5, trunk_angle=-24, head_angle=-30, body_lean=7.6, leg_front_angle=44, leg_back_angle=-18, arm_front_angle=104, arm_back_angle=70),
        P(bob=-0.33, trunk_angle=-20, head_angle=-22, body_lean=5.87, leg_front_angle=40, leg_back_angle=-14, arm_front_angle=90, arm_back_angle=58),
    ]),
    # In the stomach: she folds over it, hips knocked back, arms hugging in.
    "hit_mid": (60, [
        P(trunk_angle=28, head_angle=18, bob=0.1, body_lean=-1, leg_front_angle=30, leg_front_scale=0.86, leg_back_angle=0, leg_back_scale=0.86, arm_front_angle=-14, arm_back_angle=-24),
        P(trunk_angle=36, head_angle=22, bob=0.14, body_lean=-2.77, leg_front_angle=30, leg_front_scale=0.84, leg_back_angle=-2, leg_back_scale=0.84, arm_front_angle=20, arm_back_angle=10),
        P(trunk_angle=32, head_angle=18, bob=0.03, body_lean=-1.83, leg_front_angle=28, leg_front_scale=0.86, leg_back_angle=0, leg_back_scale=0.86, arm_front_angle=16, arm_back_angle=6),
    ]),
    # Across the legs: the front foot swept out from under her, she drops onto
    # the back knee and throws her arms up and out to stay on her feet.
    "hit_low": (60, [
        P(trunk_angle=12, bob=1.4, body_lean=0.4, leg_front_angle=-50, leg_front_scale=0.9, leg_back_angle=26, leg_back_scale=0.7, arm_front_angle=140, arm_back_angle=-130, head_angle=-16),
        P(trunk_angle=20, bob=1.47, body_lean=-1.07, leg_front_angle=-58, leg_front_scale=0.86, leg_back_angle=32, leg_back_scale=0.6, arm_front_angle=124, arm_back_angle=-140, head_angle=-10),
        P(trunk_angle=17, bob=1.37, body_lean=-0.73, leg_front_angle=-52, leg_front_scale=0.88, leg_back_angle=30, leg_back_scale=0.62, arm_front_angle=112, arm_back_angle=-128, head_angle=-8),
    ]),
    # In the air: jack-knifed backward, legs kicked forward, arms flung back.
    "hit_air": (60, [
        P(body_lean=3, bob=-1.0, body_angle=-14, trunk_angle=-22, head_angle=-26, leg_front_angle=84, leg_back_angle=62, arm_front_angle=172, arm_back_angle=-162),
        P(body_lean=3.25, bob=-1.0, body_angle=-16, trunk_angle=-24, head_angle=-22, leg_front_angle=78, leg_back_angle=56, arm_front_angle=160, arm_back_angle=-150),
    ]),
    # -- launched ---------------------------------------------------------
    # Thrown upward: stretched long and arched back, every limb trailing DOWN.
    "launch_up": (70, [
        P(bob=-1.0, body_angle=-6, trunk_angle=-10, head_angle=-32, leg_front_angle=14, leg_back_angle=8, arm_front_angle=-8, arm_back_angle=-18),
        P(bob=-1.0, body_angle=-8, trunk_angle=-12, head_angle=-36, leg_front_angle=12, leg_back_angle=4, arm_front_angle=-14, arm_back_angle=-24),
    ]),
    # Thrown back: laid out flat, head leading the way she flies, limbs
    # trailing to her front.
    "launch_horizontal": (70, [
        P(body_lean=1.42, bob=-1.4, body_angle=-64, head_angle=-12, leg_front_angle=84, leg_front_scale=0.62, leg_back_angle=52, leg_back_scale=0.68, arm_front_angle=96, arm_back_angle=70),
        P(body_lean=1.67, bob=-1.4, body_angle=-70, head_angle=-14, leg_front_angle=90, leg_front_scale=0.62, leg_back_angle=58, leg_back_scale=0.68, arm_front_angle=104, arm_back_angle=78),
    ]),
    # Spiked: driven down chest-first, limbs streaming UP behind her.
    "launch_down": (70, [
        P(body_lean=-1.33, bob=-1.4, body_angle=34, head_angle=20, trunk_angle=10, leg_front_angle=-42, leg_front_scale=0.8, leg_back_angle=-64, leg_back_scale=0.76, arm_front_angle=164, arm_back_angle=-170),
        P(body_lean=-1.83, bob=-1.4, body_angle=40, head_angle=22, trunk_angle=12, leg_front_angle=-48, leg_front_scale=0.8, leg_back_angle=-70, leg_back_scale=0.76, arm_front_angle=172, arm_back_angle=-176),
    ]),
    # The generic launch: half laid back, starfished.
    "launch": (70, [
        P(bob=-1.2, body_angle=-36, head_angle=-16, leg_front_angle=50, leg_back_angle=-20, arm_front_angle=130, arm_back_angle=-120),
        P(bob=-1.2, body_angle=-40, head_angle=-18, leg_front_angle=56, leg_back_angle=-26, arm_front_angle=138, arm_back_angle=-128),
    ]),
    # A meteor is a head-first plunge, curled round her middle.
    "meteor": (70, [
        P(body_lean=-3.5, bob=-1.4, body_angle=128, trunk_angle=20, head_angle=16, leg_front_angle=60, leg_back_angle=30, leg_front_scale=0.8, arm_front_angle=170, arm_back_angle=150),
        P(body_lean=-4.08, bob=-1.4, body_angle=136, trunk_angle=22, head_angle=18, leg_front_angle=66, leg_back_angle=36, leg_front_scale=0.8, arm_front_angle=176, arm_back_angle=158),
    ]),
    # Tumbling: a loose, limp ball going over and over.
    "tumble": (80, [
        _tuck(-30, body_lean=-0.5, bob=-1.0, trunk_angle=14, leg_front_scale=0.8, arm_front_angle=120, arm_back_angle=-60),
        _tuck(-120, body_lean=0.75, bob=-1.0, trunk_angle=14, leg_front_scale=0.8, arm_front_angle=120, arm_back_angle=-60),
        _tuck(-210, body_lean=-2.66, bob=-1.33, trunk_angle=14, leg_front_scale=0.8, arm_front_angle=120, arm_back_angle=-60),
        _tuck(-300, body_lean=-3.92, bob=-1.0, trunk_angle=14, leg_front_scale=0.8, arm_front_angle=120, arm_back_angle=-60),
    ]),
    "ground_bounce": (70, [
        P(body_lean=1.92, bob=5.57, body_angle=-78, head_angle=-10, leg_front_angle=96, leg_front_scale=0.56, leg_back_angle=70, leg_back_scale=0.6, arm_front_angle=150, arm_back_angle=120),
        P(body_lean=1.41, bob=-0.6, body_angle=-56, head_angle=-14, leg_front_angle=60, leg_front_scale=0.7, leg_back_angle=24, leg_back_scale=0.74, arm_front_angle=120, arm_back_angle=-100),
    ]),
    # Against a wall or a ceiling: flattened onto it, spread-eagled.
    "impact": (60, [
        P(bob=-0.5, body_angle=-10, trunk_angle=-6, head_angle=-14, leg_front_angle=40, leg_back_angle=-30, arm_front_angle=120, arm_back_angle=-118),
        P(bob=-0.66, body_angle=-8, trunk_angle=-4, head_angle=-10, leg_front_angle=34, leg_back_angle=-24, arm_front_angle=108, arm_back_angle=-104),
    ]),
    "splat": (90, [
        P(body_angle=-4, head_angle=-24, leg_front_angle=44, leg_back_angle=-36, arm_front_angle=136, arm_back_angle=-136),
        P(body_angle=-4, head_angle=-24, leg_front_angle=46, leg_back_angle=-38, arm_front_angle=140, arm_back_angle=-140),
    ]),
    # -- floor ------------------------------------------------------------
    # Slammed onto the floor on her back: the bounce, then flat.
    "knockdown": (70, [
        P(body_lean=1.58, body_angle=-62, head_angle=-14, leg_front_angle=110, leg_back_angle=84, arm_front_angle=150, arm_back_angle=120),
        P(body_lean=2.01, bob=3.83, body_angle=-94, head_angle=10, leg_front_angle=92, leg_front_scale=0.56, leg_back_angle=72, leg_back_scale=0.6, arm_front_angle=150, arm_back_angle=30),
    ]),
    # On her back: shoulders and skirt on the floor, the face up, knees up.
    "prone_face_up": (200, [
        P(body_lean=2.09, bob=3.67, body_angle=-96, head_angle=14, leg_front_angle=92, leg_front_scale=0.56, leg_back_angle=72, leg_back_scale=0.58, arm_front_angle=104, arm_back_angle=14),
    ]),
    # On her front: chest down, head toward her facing, legs out flat behind.
    "prone_face_down": (200, [
        P(body_lean=-1.84, bob=6.5, body_angle=90, head_angle=-22, leg_front_angle=-60, leg_front_scale=0.6, leg_back_angle=-84, leg_back_scale=0.56, arm_front_angle=166, arm_back_angle=176),
    ]),
    # The generic floor pose, for whatever does not know which way up.
    "prone": (200, [
        P(body_lean=2.34, bob=4.17, body_angle=-92, head_angle=12, leg_front_angle=96, leg_front_scale=0.56, leg_back_angle=80, leg_back_scale=0.6, arm_front_angle=20, arm_back_angle=6),
    ]),
    "prone_damage": (60, [
        P(body_lean=2.92, bob=5.33, body_angle=-82, head_angle=-20, leg_front_angle=128, leg_front_scale=0.66, leg_back_angle=110, leg_back_scale=0.7, arm_front_angle=170, arm_back_angle=100),
        P(body_lean=2.09, bob=3.67, body_angle=-96, head_angle=14, leg_front_angle=92, leg_front_scale=0.56, leg_back_angle=72, leg_back_scale=0.58, arm_front_angle=104, arm_back_angle=14),
    ]),
    # Up off her back: sit up over the knees, onto a knee, stand.
    "getup": (90, [
        P(body_lean=-1.33, bob=2.83, body_angle=-40, head_angle=10, trunk_angle=24, leg_front_angle=86, leg_front_scale=0.66, leg_back_angle=72, arm_front_angle=-30, arm_back_angle=-40),
        P(body_lean=-1.5, trunk_angle=34, bob=1.5, leg_front_angle=60, leg_front_scale=0.62, leg_back_angle=-60, leg_back_scale=0.6, arm_front_angle=20, arm_back_angle=-20),
        P(trunk_angle=10, bob=0.1, leg_front_angle=30, leg_front_scale=0.86, leg_back_angle=4, leg_back_scale=0.86, arm_front_angle=12, arm_back_angle=-10),
    ]),
    "getup_roll": (60, [
        _tuck(-90, body_lean=-1.25, bob=4.17),
        _tuck(-180, body_lean=-2.33, bob=-0.33),
        _tuck(-270, body_lean=-4.42, bob=2.84),
        P(trunk_angle=16, bob=0.7, leg_front_angle=40, leg_front_scale=0.74, leg_back_angle=-6, leg_back_scale=0.74, arm_front_angle=40, arm_back_angle=-30),
    ]),
    # A sweeping kick from the floor, both ways round.
    "getup_attack": (60, [
        P(body_lean=-1.25, bob=3.17, body_angle=-50, trunk_angle=20, leg_front_angle=80, leg_front_scale=0.7, leg_back_angle=60, arm_front_angle=-40, arm_back_angle=-60),
        P(body_lean=-3, trunk_angle=40, bob=1.54, leg_front_angle=106, leg_back_angle=-24, leg_back_scale=0.6, arm_front_angle=-10, arm_back_angle=-30),
        P(body_lean=-3, trunk_angle=40, bob=1.54, leg_front_angle=40, leg_front_scale=0.6, leg_back_angle=-100, arm_front_angle=-30, arm_back_angle=10),
        P(trunk_angle=12, bob=0.14, leg_front_angle=30, leg_front_scale=0.84, leg_back_angle=4, leg_back_scale=0.84, arm_front_angle=20, arm_back_angle=-14),
    ]),
    # The floor tech: a deliberate catch. Feet planted wide, a deep squat
    # and the front palm slapped flat on the floor to take the force.
    "tech": (70, [
        P(trunk_angle=44, bob=1.57, body_lean=-2.93, head_angle=-26, leg_front_angle=60, leg_front_scale=0.6, leg_back_angle=-36, leg_back_scale=0.6, arm_front_angle=-44, arm_back_angle=-104),
        P(trunk_angle=34, bob=1.34, body_lean=-0.53, head_angle=-18, leg_front_angle=54, leg_front_scale=0.64, leg_back_angle=-30, leg_back_scale=0.64, arm_front_angle=-32, arm_back_angle=-84),
    ]),
    "tech_roll": (50, [
        _tuck(70, body_lean=-5.08, bob=1.84),
        _tuck(160, body_lean=-1.83, bob=-1.83),
        _tuck(250, body_lean=-0.67, bob=4.17),
        P(trunk_angle=22, bob=0.94, leg_front_angle=46, leg_front_scale=0.7, leg_back_angle=-10, leg_back_scale=0.7, arm_front_angle=60, arm_back_angle=-60),
    ]),
    "wall_tech": (60, [
        P(body_lean=2.67, body_angle=-30, trunk_angle=-10, leg_front_angle=-40, leg_front_scale=0.7, leg_back_angle=-60, leg_back_scale=0.7, arm_front_angle=-80, arm_back_angle=-100),
        P(bob=-0.66, body_angle=-20, leg_front_angle=-20, leg_back_angle=-40, arm_front_angle=-50, arm_back_angle=-70),
    ]),
    "wall_tech_jump": (60, [
        P(body_angle=-20, leg_front_angle=-50, leg_front_scale=0.66, leg_back_angle=-70, leg_back_scale=0.66, arm_front_angle=-70, arm_back_angle=-90),
        P(bob=-1.4, body_angle=6, leg_front_angle=20, leg_back_angle=-40, arm_front_angle=164, arm_back_angle=150),
    ]),
    "ceiling_tech": (60, [
        P(bob=-1.4, body_angle=180, trunk_angle=10, leg_front_angle=40, leg_front_scale=0.7, leg_back_angle=-20, leg_back_scale=0.7, arm_front_angle=20, arm_back_angle=-20),
        P(bob=-1.33, body_angle=150, trunk_angle=10, leg_front_angle=30, leg_back_angle=-10, arm_front_angle=60, arm_back_angle=-60),
    ]),
    # -- guard ------------------------------------------------------------
    # Her guard: crouched behind both forearms crossed in front of her face.
    "shield_raise": (50, [
        P(trunk_angle=6, bob=-0.16, leg_front_angle=30, leg_front_scale=0.9, leg_back_angle=4, leg_back_scale=0.9, arm_front_angle=100, arm_back_angle=70),
        P(trunk_angle=10, bob=0.07, head_angle=8, leg_front_angle=36, leg_front_scale=0.84, leg_back_angle=-4, leg_back_scale=0.84, arm_front_angle=142, arm_back_angle=118),
    ]),
    "block": (160, [
        P(trunk_angle=10, bob=0.07, head_angle=8, leg_front_angle=36, leg_front_scale=0.84, leg_back_angle=-4, leg_back_scale=0.84, arm_front_angle=142, arm_back_angle=118),
    ]),
    # The guard takes a hit and holds: shoved back on her heels, arms firm.
    "shield_hit": (60, [
        P(trunk_angle=-6, bob=0.24, body_lean=-0.7, head_angle=-8, leg_front_angle=46, leg_front_scale=0.84, leg_back_angle=-14, leg_back_scale=0.84, arm_front_angle=150, arm_back_angle=124),
        P(trunk_angle=4, bob=0.07, body_lean=-0.4, head_angle=2, leg_front_angle=40, leg_front_scale=0.84, leg_back_angle=-8, leg_back_scale=0.84, arm_front_angle=144, arm_back_angle=120),
    ]),
    "shield_release": (60, [
        P(trunk_angle=6, bob=-0.16, leg_front_angle=30, leg_front_scale=0.9, leg_back_angle=4, leg_back_scale=0.9, arm_front_angle=80, arm_back_angle=40),
        P(bob=-0.33, trunk_angle=2, leg_front_angle=22, leg_back_angle=12, arm_front_angle=20, arm_back_angle=0),
    ]),
    # The perfect guard: arms snapped wide open, chest out.
    "parry": (60, [
        P(body_lean=0.5, bob=-0.33, trunk_angle=-10, head_angle=-6, leg_front_angle=34, leg_back_angle=-4, arm_front_angle=110, arm_back_angle=-100),
        P(bob=-0.33, trunk_angle=-6, head_angle=-4, leg_front_angle=30, leg_back_angle=0, arm_front_angle=96, arm_back_angle=-90),
    ]),
    "roll": (55, [
        _tuck(60, body_lean=-5.09, bob=2),
        _tuck(150, body_lean=-2.58, bob=-1.67),
        _tuck(240, body_lean=-0.58, bob=3),
        _tuck(320, body_lean=-2.58, bob=2.67, leg_front_scale=0.75, leg_back_scale=0.75),
        P(trunk_angle=18, bob=0.57, leg_front_angle=40, leg_front_scale=0.74, leg_back_angle=-6, leg_back_scale=0.74, arm_front_angle=40, arm_back_angle=-30),
    ]),
    "roll_back": (55, [
        _tuck(-60, body_lean=-1.25, bob=2.67),
        _tuck(-150, body_lean=-1.25, bob=0),
        _tuck(-240, body_lean=-4.5, bob=-0.5),
        _tuck(-320, body_lean=-4.75, bob=3, leg_front_scale=0.75, leg_back_scale=0.75),
        P(trunk_angle=-6, bob=0.14, leg_front_angle=40, leg_front_scale=0.84, leg_back_angle=-14, leg_back_scale=0.84, arm_front_angle=40, arm_back_angle=30),
    ]),
    # Sidestep: she turns side on and sucks in, arms tight, up on her toes.
    "spot_dodge": (60, [
        P(bob=-0.5, trunk_angle=-6, head_angle=-10, leg_front_angle=10, leg_back_angle=22, arm_front_angle=-12, arm_back_angle=12, body_lean=-0.3),
        P(trunk_angle=-12, head_angle=-14, bob=-0.3, leg_front_angle=4, leg_back_angle=28, arm_front_angle=-20, arm_back_angle=20, body_lean=-0.6),
        P(trunk_angle=-4, leg_front_angle=18, leg_back_angle=16, arm_front_angle=0, arm_back_angle=0),
    ]),
    "air_dodge": (60, [
        _tuck(-20, bob=-1.0, arm_front_angle=40, arm_back_angle=30),
        _tuck(-40, bob=-1.0, arm_front_angle=30, arm_back_angle=20),
        P(bob=-1.0, trunk_angle=-6, leg_front_angle=40, leg_back_angle=-20, arm_front_angle=130, arm_back_angle=-60),
    ]),
    # Shield broken: thrown up, down in a heap, then reeling.
    "shield_break_launch": (70, [
        P(bob=-1.2, body_angle=-12, head_angle=-30, leg_front_angle=14, leg_back_angle=-10, arm_front_angle=170, arm_back_angle=-170),
        P(bob=-1.2, body_angle=-16, head_angle=-34, leg_front_angle=20, leg_back_angle=-16, arm_front_angle=176, arm_back_angle=-176),
    ]),
    "shield_break_fall": (90, [
        P(bob=-1.0, body_angle=-24, head_angle=-20, leg_front_angle=30, leg_back_angle=-4, arm_front_angle=150, arm_back_angle=-150),
        P(bob=-1.0, body_angle=-30, head_angle=-24, leg_front_angle=34, leg_back_angle=-8, arm_front_angle=156, arm_back_angle=-156),
    ]),
    "shield_break_collapse": (90, [
        P(body_lean=-2.5, trunk_angle=34, bob=1.77, head_angle=30, leg_front_angle=60, leg_front_scale=0.56, leg_back_angle=-50, leg_back_scale=0.56, arm_front_angle=-6, arm_back_angle=-10),
        P(body_lean=-4, trunk_angle=40, bob=1.87, head_angle=36, leg_front_angle=62, leg_front_scale=0.54, leg_back_angle=-52, leg_back_scale=0.54, arm_front_angle=-2, arm_back_angle=-6),
    ]),
    "shield_break_recover": (90, [
        P(body_lean=-1.5, trunk_angle=30, bob=1.14, head_angle=26, leg_front_angle=44, leg_front_scale=0.66, leg_back_angle=-20, leg_back_scale=0.66, arm_front_angle=4, arm_back_angle=-8),
        P(trunk_angle=10, bob=0.27, head_angle=10, leg_front_angle=28, leg_front_scale=0.88, leg_back_angle=6, leg_back_scale=0.88, arm_front_angle=10, arm_back_angle=-6),
    ]),
    # Dizzy: the head lolls and the trunk wobbles over unsteady feet.
    "dizzy": (130, [
        P(bob=-0.33, trunk_angle=-10, head_angle=-22, body_lean=-0.3, leg_front_angle=30, leg_back_angle=-2, arm_front_angle=10, arm_back_angle=-24),
        P(bob=-0.33, trunk_angle=4, head_angle=12, leg_front_angle=22, leg_back_angle=10, arm_front_angle=-10, arm_back_angle=4),
        P(bob=-0.33, trunk_angle=12, head_angle=26, body_lean=0.3, leg_front_angle=14, leg_back_angle=20, arm_front_angle=-24, arm_back_angle=10),
        P(bob=-0.33, trunk_angle=2, head_angle=-6, leg_front_angle=22, leg_back_angle=10, arm_front_angle=0, arm_back_angle=-8),
    ]),
    "sleep_start": (110, [
        P(trunk_angle=20, bob=1.27, head_angle=24, leg_front_angle=44, leg_front_scale=0.7, leg_back_angle=-20, leg_back_scale=0.7, arm_front_angle=-4, arm_back_angle=-6),
        P(body_lean=0.67, bob=4.33, body_angle=-60, head_angle=20, leg_front_angle=60, leg_front_scale=0.76, leg_back_angle=40, arm_front_angle=30, arm_back_angle=10),
    ]),
    # Asleep on her side, hands under her cheek, breathing.
    "sleep": (260, [
        P(body_lean=3, bob=3.34, body_angle=-90, head_angle=26, trunk_angle=-6, leg_front_angle=100, leg_front_scale=0.6, leg_back_angle=80, leg_back_scale=0.62, arm_front_angle=164, arm_back_angle=150),
        P(body_lean=3.33, bob=3, body_angle=-90, head_angle=28, trunk_angle=-8, leg_front_angle=100, leg_front_scale=0.6, leg_back_angle=80, leg_back_scale=0.62, arm_front_angle=166, arm_back_angle=152),
    ]),
    "wake": (90, [
        P(body_lean=-0.75, bob=3.33, body_angle=-40, head_angle=-10, trunk_angle=20, leg_front_angle=86, leg_front_scale=0.66, leg_back_angle=72, arm_front_angle=150, arm_back_angle=-140),
        P(bob=-0.33, trunk_angle=4, head_angle=-14, leg_front_angle=26, leg_back_angle=8, arm_front_angle=166, arm_back_angle=-160),
    ]),
    # Buried to the waist: arms pinned up, wriggling.
    "bury_start": (80, [
        P(bob=-0.33, trunk_angle=-6, head_angle=-14, leg_front_angle=14, leg_back_angle=-6, arm_front_angle=150, arm_back_angle=-150),
        P(bob=0, head_angle=-6, leg_front_angle=19, leg_back_angle=15, arm_front_angle=170, arm_back_angle=-170),
    ]),
    "buried": (140, [
        P(trunk_angle=-6, head_angle=-10, leg_front_angle=19, leg_back_angle=15, arm_front_angle=166, arm_back_angle=-176),
        P(trunk_angle=6, head_angle=8, leg_front_angle=19, leg_back_angle=15, arm_front_angle=176, arm_back_angle=-166),
    ]),
    "bury_escape": (70, [
        P(bob=-1.6, head_angle=-12, leg_front_angle=30, leg_back_angle=-20, arm_front_angle=170, arm_back_angle=-170),
        P(bob=-1.0, leg_front_angle=40, leg_back_angle=-26, arm_front_angle=140, arm_back_angle=-60),
    ]),
    # -- ledge ------------------------------------------------------------
    # Hanging by both hands from a ledge above her front, legs dangling.
    "ledge_catch": (60, [
        P(bob=-0.83, body_angle=-10, head_angle=-16, leg_front_angle=56, leg_back_angle=28, arm_front_angle=148, arm_back_angle=136),
        P(bob=-0.67, body_angle=-4, head_angle=-14, leg_front_angle=14, leg_back_angle=-14, arm_front_angle=150, arm_back_angle=140),
    ]),
    "ledge_grab": (180, [
        P(bob=-0.66, body_angle=-6, head_angle=-14, leg_front_angle=26, leg_back_angle=6, arm_front_angle=150, arm_back_angle=140),
        P(bob=-0.5, body_angle=-4, head_angle=-14, leg_front_angle=18, leg_back_angle=12, arm_front_angle=151, arm_back_angle=141),
    ]),
    # Climbing up over it: a knee up onto the edge, then upright.
    "ledge_climb": (80, [
        P(body_lean=-0.5, bob=-0.33, trunk_angle=34, head_angle=-18, leg_front_angle=96, leg_front_scale=0.64, leg_back_angle=-10, arm_front_angle=40, arm_back_angle=30),
        P(trunk_angle=20, bob=0.9, leg_front_angle=60, leg_front_scale=0.7, leg_back_angle=-30, leg_back_scale=0.8, arm_front_angle=10, arm_back_angle=-6),
        P(trunk_angle=4, leg_front_angle=24, leg_back_angle=10, arm_front_angle=6, arm_back_angle=-4),
    ]),
    "ledge_getup": (70, [
        P(bob=-0.33, body_lean=-2.34, trunk_angle=40, head_angle=-14, leg_front_angle=100, leg_front_scale=0.6, leg_back_angle=-20, arm_front_angle=20, arm_back_angle=10),
        P(trunk_angle=14, bob=0.14, leg_front_angle=40, leg_front_scale=0.84, leg_back_angle=-6, leg_back_scale=0.84, arm_front_angle=20, arm_back_angle=-14),
    ]),
    "ledge_roll": (55, [
        _tuck(80, body_lean=-4.83, bob=2.43),
        _tuck(170, body_lean=-1.66, bob=-1.33),
        _tuck(260, body_lean=-0.92, bob=5),
        P(trunk_angle=18, bob=0.57, leg_front_angle=40, leg_front_scale=0.74, leg_back_angle=-6, leg_back_scale=0.74, arm_front_angle=40, arm_back_angle=-30),
    ]),
    "ledge_jump": (60, [
        P(body_lean=-4.25, trunk_angle=20, head_angle=-20, leg_front_angle=80, leg_front_scale=0.7, leg_back_angle=40, leg_back_scale=0.7, arm_front_angle=120, arm_back_angle=110),
        P(bob=-1.8, leg_front_angle=30, leg_back_angle=-24, arm_front_angle=170, arm_back_angle=-160),
    ]),
    "ledge_attack": (60, [
        P(body_lean=-0.84, bob=-0.33, trunk_angle=34, head_angle=-14, leg_front_angle=96, leg_front_scale=0.64, leg_back_angle=-10, arm_front_angle=40, arm_back_angle=30),
        P(body_lean=-0.5, trunk_angle=30, bob=1.34, leg_front_angle=104, leg_back_angle=-26, leg_back_scale=0.62, arm_front_angle=-30, arm_back_angle=-50),
        P(trunk_angle=10, bob=0.1, leg_front_angle=30, leg_front_scale=0.86, leg_back_angle=4, leg_back_scale=0.86, arm_front_angle=16, arm_back_angle=-10),
    ]),
    "ledge_drop": (80, [
        P(bob=-0.5, body_angle=-4, head_angle=-6, leg_front_angle=20, leg_back_angle=8, arm_front_angle=140, arm_back_angle=128),
        P(bob=-0.6, head_angle=6, leg_front_angle=24, leg_back_angle=4, arm_front_angle=130, arm_back_angle=-120),
    ]),
    # -- held -------------------------------------------------------------
    # In somebody's grip: pinned at the arms, feet scrabbling.
    "grabbed": (110, [
        P(bob=-0.33, trunk_angle=-12, head_angle=-16, body_lean=-0.2, leg_front_angle=40, leg_back_angle=-20, arm_front_angle=34, arm_back_angle=-30),
        P(bob=-0.5, trunk_angle=-8, head_angle=-12, leg_front_angle=10, leg_back_angle=16, arm_front_angle=30, arm_back_angle=-26),
    ]),
    "grabbed_pummel": (60, [
        P(trunk_angle=18, head_angle=24, bob=0, body_lean=-0.4, leg_front_angle=30, leg_front_scale=0.86, leg_back_angle=-4, leg_back_scale=0.86, arm_front_angle=-10, arm_back_angle=-34),
        P(bob=-0.33, trunk_angle=-10, head_angle=-14, leg_front_angle=30, leg_back_angle=-10, arm_front_angle=34, arm_back_angle=-30),
    ]),
    "grab_escape": (60, [
        P(bob=-0.33, trunk_angle=-14, head_angle=-10, body_lean=6.07, leg_front_angle=40, leg_back_angle=-20, arm_front_angle=120, arm_back_angle=-110),
        P(bob=-0.33, trunk_angle=-6, body_lean=-0.4, leg_front_angle=34, leg_back_angle=-6, arm_front_angle=60, arm_back_angle=-40),
    ]),
    "grab_release": (70, [
        P(bob=-0.33, trunk_angle=-6, body_lean=-0.3, leg_front_angle=32, leg_back_angle=-4, arm_front_angle=110, arm_back_angle=-60),
        P(trunk_angle=-2, leg_front_angle=24, leg_back_angle=10, arm_front_angle=40, arm_back_angle=-20),
    ]),
    # -- trips --------------------------------------------------------------
    "trip_fall": (60, [
        P(body_lean=0.92, body_angle=40, bob=1.0, head_angle=-20, leg_front_angle=-30, leg_back_angle=-60, arm_front_angle=100, arm_back_angle=60),
        P(body_lean=-1.25, body_angle=86, head_angle=-30, leg_front_angle=-40, leg_front_scale=0.6, leg_back_angle=-60, leg_back_scale=0.56, arm_front_angle=120, arm_back_angle=100),
    ]),
    # Tripped flat: belly down, propped on her forearms.
    "trip_idle": (200, [
        P(body_lean=1.5, bob=3, body_angle=90, head_angle=-30, trunk_angle=-16, leg_front_angle=-20, leg_front_scale=0.7, leg_back_angle=-40, leg_back_scale=0.66, arm_front_angle=96, arm_back_angle=110),
    ]),
    "trip_getup": (80, [
        P(body_lean=4.09, bob=3.5, body_angle=60, head_angle=-30, trunk_angle=-20, leg_front_angle=-30, leg_front_scale=0.7, leg_back_angle=-40, arm_front_angle=60, arm_back_angle=80),
        P(body_lean=-0.5, trunk_angle=30, bob=1.5, leg_front_angle=60, leg_front_scale=0.62, leg_back_angle=-60, leg_back_scale=0.6, arm_front_angle=20, arm_back_angle=-20),
        P(trunk_angle=8, bob=0.1, leg_front_angle=30, leg_front_scale=0.86, leg_back_angle=4, leg_back_scale=0.86, arm_front_angle=12, arm_back_angle=-10),
    ]),
    "trip_attack": (60, [
        P(body_lean=2.33, bob=3.34, body_angle=70, head_angle=-24, trunk_angle=-20, leg_front_angle=-60, leg_back_angle=-90, arm_front_angle=80, arm_back_angle=90),
        P(body_lean=4.5, bob=3.17, body_angle=60, head_angle=-20, trunk_angle=-24, leg_front_angle=-110, leg_back_angle=-40, arm_front_angle=70, arm_back_angle=80),
        P(trunk_angle=20, bob=1.27, leg_front_angle=50, leg_front_scale=0.66, leg_back_angle=-30, leg_back_scale=0.7, arm_front_angle=30, arm_back_angle=-20),
    ]),
    "trip_roll": (55, [
        _tuck(90, body_lean=-4.42, bob=2.84),
        _tuck(180, body_lean=-2.33, bob=-0.33),
        _tuck(270, body_lean=-1.25, bob=4.17),
        P(trunk_angle=24, bob=0.9, leg_front_angle=50, leg_front_scale=0.72, leg_back_angle=-14, leg_back_scale=0.72, arm_front_angle=60, arm_back_angle=-50),
    ]),
    # -- stage ------------------------------------------------------------
    # She drops in, lands, and doffs her cap... as near as a rigid arm gets.
    "entrance": (110, [
        P(bob=-1.8, leg_front_angle=34, leg_back_angle=-22, arm_front_angle=164, arm_back_angle=-150),
        P(trunk_angle=18, bob=0.83, leg_front_angle=40, leg_front_scale=0.7, leg_back_angle=-4, leg_back_scale=0.7, arm_front_angle=70, arm_back_angle=-70),
        P(trunk_angle=-4, leg_front_angle=24, leg_back_angle=10, arm_front_angle=150, arm_back_angle=-20, head_angle=-6),
        P(bob=-0.33, leg_front_angle=22, leg_back_angle=12, arm_front_angle=60, arm_back_angle=-10),
    ]),
    # The win: a hop with a fist punched up, then the pose she holds.
    "victory": (110, [
        P(trunk_angle=10, bob=0.33, leg_front_angle=32, leg_front_scale=0.8, leg_back_angle=4, leg_back_scale=0.8, arm_front_angle=-30, arm_back_angle=-20),
        P(bob=-2.2, trunk_angle=-6, head_angle=-12, leg_front_angle=50, leg_back_angle=-50, leg_back_scale=0.8, arm_front_angle=176, arm_back_angle=-60),
        P(bob=-0.33, trunk_angle=-4, head_angle=-8, leg_front_angle=34, leg_back_angle=0, arm_front_angle=170, arm_back_angle=-30),
    ]),
    "victory_hold": (200, [
        P(bob=-0.33, trunk_angle=-4, head_angle=-8, leg_front_angle=34, leg_back_angle=0, arm_front_angle=170, arm_back_angle=-30),
        P(trunk_angle=-5, head_angle=-10, leg_front_angle=34, leg_back_angle=0, arm_front_angle=174, arm_back_angle=-34, bob=-0.48),
    ]),
    # The loss: slumped, head hung, arms limp.
    "loss": (220, [
        P(trunk_angle=16, head_angle=30, bob=-0.27, leg_front_angle=24, leg_back_angle=12, arm_front_angle=-4, arm_back_angle=-2),
        P(trunk_angle=18, head_angle=34, bob=-0.17, leg_front_angle=24, leg_back_angle=12, arm_front_angle=-2, arm_back_angle=0),
    ]),
    # The final smash: a crouched gather and both palms thrown forward.
    "final_smash": (90, [
        P(trunk_angle=18, bob=1.27, leg_front_angle=44, leg_front_scale=0.7, leg_back_angle=-20, leg_back_scale=0.7, arm_front_angle=-60, arm_back_angle=-70, head_angle=10),
        P(trunk_angle=-8, bob=-0.4, head_angle=-14, leg_front_angle=20, leg_back_angle=-10, arm_front_angle=176, arm_back_angle=-176),
        P(bob=0.33, trunk_angle=16, body_lean=-0.53, leg_front_angle=60, leg_back_angle=-40, arm_front_angle=96, arm_back_angle=90),
        P(bob=0.33, trunk_angle=18, body_lean=-0.6, leg_front_angle=62, leg_back_angle=-42, arm_front_angle=92, arm_back_angle=88),
        P(bob=-0.33, trunk_angle=6, leg_front_angle=30, leg_back_angle=4, arm_front_angle=30, arm_back_angle=-20),
    ]),
}


#: Every ``fighter_core`` category of ``fighter_motion_vocabulary.yaml``, and
#: the tall sheet's row that draws it. Several categories may share a row.
FIGHTER_MOTION_COVERAGE: Dict[str, str] = {
    "idle": "idle", "idle_look_up": "idle_look_up", "walk": "walk", "crouch_walk": "crouch_walk",
    "crouch_jump": "crouch_jump", "locomotion_stop": "run_stop", "turnaround": "turnaround",
    "dash_startup": "dash_startup", "run": "run", "stumble": "stumble", "crouch_start": "crouch_start",
    "crouch": "crouch", "crouch_end": "crouch_end", "land_light": "land_light", "land_hard": "land_hard",
    "jump_squat": "jump_squat", "jump": "jump", "double_jump": "double_jump", "fall": "fall",
    "fall_special": "fall_special", "land_special": "land_hard", "tumble": "tumble",
    "shield_raise": "shield_raise", "shield_hold": "block", "shield_release": "shield_release",
    "parry": "parry", "shield_hit": "shield_hit", "spot_dodge": "spot_dodge", "roll_forward": "roll",
    "roll_backward": "roll_back", "air_dodge": "air_dodge", "jab": "jab", "dash_attack": "dash_attack",
    "attack_side": "attack_side", "attack_up": "attack_up", "attack_down": "attack_down",
    "smash_charge_forward": "smash_charge", "smash_forward": "smash_forward",
    "smash_charge_up": "smash_charge", "smash_up": "smash_up", "smash_charge_down": "smash_charge",
    "smash_down": "smash_down", "air_neutral": "air_neutral", "air_forward": "air_forward",
    "air_back": "air_back", "air_up": "air_up", "air_down": "air_down", "air_land": "air_land",
    "special_neutral": "fireball", "special_side": "cape_spin", "special_up": "spring_jump",
    "special_down": "pipe_drop", "final_smash": "final_smash", "grab": "grab", "grab_hold": "grab_hold",
    "pummel": "pummel", "grab_release": "grab_release", "throw_forward": "throw_forward",
    "throw_back": "throw_back", "throw_up": "throw_up", "throw_down": "throw_down", "grabbed": "grabbed",
    "grabbed_pummel": "grabbed_pummel", "grab_escape": "grab_escape", "hit": "hit", "launch": "launch",
    "meteor": "meteor", "impact": "impact", "splat": "splat", "ground_bounce": "ground_bounce",
    "prone": "prone", "prone_damage": "prone_damage", "getup": "getup", "getup_attack": "getup_attack",
    "getup_roll": "getup_roll", "knockdown": "knockdown", "tech": "tech", "tech_roll": "tech_roll",
    "wall_tech": "wall_tech", "wall_tech_jump": "wall_tech_jump", "ceiling_tech": "ceiling_tech",
    "shield_break_launch": "shield_break_launch", "shield_break_fall": "shield_break_fall",
    "shield_break_collapse": "shield_break_collapse", "shield_break_recover": "shield_break_recover",
    "dizzy": "dizzy", "sleep_start": "sleep_start", "sleep": "sleep", "wake": "wake",
    "bury_start": "bury_start", "buried": "buried", "bury_escape": "bury_escape",
    "footstool_jump": "footstool_jump", "footstooled": "footstooled", "platform_drop": "platform_drop",
    "teeter_start": "teeter_start", "teeter": "teeter", "lose_footing": "stumble",
    "ledge_catch": "ledge_catch", "ledge_hang": "ledge_grab", "ledge_getup": "ledge_getup",
    "ledge_attack": "ledge_attack", "ledge_roll": "ledge_roll", "ledge_jump": "ledge_jump",
    "ledge_drop": "ledge_drop", "trip_fall": "trip_fall", "trip_land": "trip_fall", "trip_idle": "trip_idle",
    "trip_getup": "trip_getup", "trip_attack": "trip_attack", "trip_roll": "trip_roll", "taunt": "taunt",
    "entrance": "entrance", "victory": "victory", "victory_hold": "victory_hold", "loss": "loss",
}


def crouch_transitions(crouch: Pose) -> Dict[str, List[Pose]]:
    """``crouch_start`` and ``crouch_end``: her standing pose folding into the
    crouch she holds and out again, derived from that crouch so the depth is
    retuned in one place."""

    def toward(u: float) -> Pose:
        values = {}
        for f in dataclasses.fields(Pose):
            if f.name == "mode":
                continue
            a, b = getattr(Pose(), f.name), getattr(crouch, f.name)
            if a is None or b is None:
                values[f.name] = b if a is None else a
            else:
                values[f.name] = a + (b - a) * u
        return Pose(mode="crouch", **values)

    return {
        "crouch_start": [toward(0.45), toward(0.8)],
        "crouch_end": [toward(0.7), toward(0.3)],
    }


#: Frame ms of the crouch transitions.
_CROUCH_MS = 50


def fighter_poses() -> Dict[str, List[Pose]]:
    return {row: list(poses) for row, (_ms, poses) in _ROWS.items()}


def fighter_rows() -> List[Tuple[str, int, int]]:
    rows = [(row, len(poses), ms) for row, (ms, poses) in _ROWS.items()]
    rows += [("crouch_start", 2, _CROUCH_MS), ("crouch_end", 2, _CROUCH_MS)]
    return rows
