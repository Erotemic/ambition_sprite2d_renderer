"""The Napoleonic Grenadier of the History dimension: a soldier of 1802.

In 1802 Napoleon sent an army under General Leclerc to Saint-Domingue. Its
aim was to take power back from Toussaint Louverture and to bring back
slavery. The army of the people of Saint-Domingue fought it in the
mountains. War and yellow fever destroyed the expedition, and on
1 January 1804 Haiti declared its independence.

This creature is one soldier of that expedition, in the uniform of the
French line infantry of the time: a black bicorne worn crosswise, with the
tricolour cockade and the red pompom of a grenadier; a dark blue coat with
white lapels, a red collar, red cuffs and red turnbacks on its tails; a
white waistcoat and white breeches; black gaiters to the knee; white
crossbelts and a black cartridge box. He carries a musket with a fixed
bayonet. He is drawn as a soldier, not as a joke.

At rest he stands at order arms: the butt of the musket on the ground by
his foot. He marches with the musket on his shoulder. When he sees you he
brings it down to the guard, levelled at the waist with the bayonet
forward (the notice row). His windup draws the musket back; his strike is
a lunge with a long step, and the point goes about 40 px past the guard. A
hit makes him stagger back. At his death he falls on his back, the musket
falls in front of him, and he fades.

The frame is 160 by 160 px. A musket with a bayonet and a lunge of 40 px
do not fit in 128 px of width with a margin.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Optional, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _history_cast_kit as H
from . import _stage_kit as S

TARGET_NAME = "napoleonic_grenadier"
FRAME_SIZE = (160, 160)
ROWS = K.ENEMY_ROWS
GROUND = 151.0
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 5.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Napoleonic Grenadier", "haitian_revolution", "Biped", "Standard", "Medium", "Walk", ["soldier", "musket", "bayonet", "infantry"],
    "A soldier of Leclerc's expedition to Saint-Domingue (1802) in the History dimension's Haitian Revolution: a black bicorne worn "
    "crosswise with a tricolour cockade, a dark blue coat with white lapels and red cuffs, white breeches, black gaiters, and a musket "
    "with a fixed bayonet. He brings the musket to the guard, draws it back and lunges with the bayonet.",
)

Point = Tuple[float, float]

THIGH, SHIN = 22.0, 22.0
UPPER_ARM, FOREARM = 16.0, 15.0
TORSO = 34.0
#: The musket: the butt is at 0; the wrist of the stock, the fore grip, the
#: muzzle and the point of the bayonet are at these distances along it.
WRIST, FORE_GRIP, MUZZLE, POINT = 17.0, 30.0, 64.0, 80.0

COAT = (44, 56, 104, 255)
COAT_SHADE = (28, 36, 72, 255)
COAT_LIGHT = (72, 88, 140, 255)
WHITE = (240, 236, 224, 255)
WHITE_SHADE = (196, 188, 172, 255)
RED = (186, 42, 40, 255)
RED_DARK = (124, 26, 28, 255)
BLACK = (40, 34, 36, 255)
BLACK_LIGHT = (84, 76, 78, 255)
STEEL = (196, 202, 212, 255)
STEEL_SHADE = (124, 130, 146, 255)
STOCK = (150, 94, 54, 255)
STOCK_DARK = (100, 60, 34, 255)
COCKADE_BLUE = (40, 70, 150, 255)
SKIN = (232, 190, 150, 255)
SKIN_SHADE = (196, 150, 112, 255)
HAIR = (92, 64, 44, 255)
BRASS = (214, 170, 80, 255)


def _musket(pen: S.Pen, butt: Point, angle: float) -> List[Point]:
    """The musket, its butt at `butt`, pointed at `angle` degrees (0 is
    forward, -90 is up). Returns the wrist of the stock, the fore grip and
    the point of the bayonet."""
    a = math.radians(angle)
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])

    def at(s: float, w: float = 0.0) -> Point:
        return (butt[0] + d[0] * s + n[0] * w, butt[1] + d[1] * s + n[1] * w)

    # The stock: a wide butt, a narrow wrist, then the fore-stock under the
    # barrel. `w` > 0 is the lower side of the musket when it points forward.
    stock = [at(0.0, -2.2), at(WRIST - 2.0, -1.4), at(MUZZLE - 6.0, -1.4), at(MUZZLE - 6.0, 1.8), at(WRIST + 4.0, 1.8), at(WRIST, 1.4),
             at(6.0, 4.6), at(0.0, 5.0)]
    pen.poly(stock, STOCK)
    pen.poly([at(0.5, 2.2), at(6.0, 4.0), at(0.5, 4.6)], STOCK_DARK, body=False)
    pen.ink([at(0.2, -2.0), at(0.2, 4.8)], 1.0, BRASS)
    # The barrel of steel along the top, with its bands and the lock.
    pen.limb([at(WRIST - 2.0, -1.4), at(MUZZLE, -1.4)], 2.0, STEEL)
    pen.ink([at(WRIST, -2.0), at(MUZZLE, -2.0)], 0.5, K.WHITE)
    for s in (MUZZLE - 22.0, MUZZLE - 12.0, MUZZLE - 6.0):
        pen.ink([at(s, -2.4), at(s, 1.8)], 0.9, STEEL_SHADE)
    pen.poly([at(WRIST - 1.0, -0.2), at(WRIST + 5.0, -0.2), at(WRIST + 5.0, 1.6), at(WRIST - 1.0, 1.6)], STEEL_SHADE, body=False)
    pen.limb([at(WRIST + 0.5, -1.6), at(WRIST - 1.5, -3.6)], 1.0, STEEL_SHADE)
    # The white sling under the musket.
    pen.ink([at(WRIST + 2.0, 1.8), at(WRIST + 12.0, 3.4), at(MUZZLE - 12.0, 1.8)], 0.9, WHITE)
    # The bayonet: a socket round the muzzle, a short neck, and a long
    # blade of three faces beside the barrel.
    pen.limb([at(MUZZLE - 3.0, -1.4), at(MUZZLE + 1.0, -1.4)], 2.4, STEEL_SHADE)
    pen.limb([at(MUZZLE + 0.5, -1.4), at(MUZZLE + 1.5, -3.6)], 1.2, STEEL_SHADE)
    pen.poly([at(MUZZLE + 1.0, -2.6), at(MUZZLE + 1.0, -5.2), at(POINT, -3.6)], STEEL)
    pen.ink([at(MUZZLE + 2.0, -3.9), at(POINT - 2.0, -3.7)], 0.5, STEEL_SHADE)
    return [at(WRIST + 1.0), at(FORE_GRIP), at(POINT, -3.6)]


def _bicorne(pen: S.Pen, hx: float, hy: float, tilt: float) -> None:
    """The bicorne, worn crosswise and seen from the side, a little turned
    to us: a tall black fan over the head, the edge bound in black braid,
    the tricolour cockade and its loop on the near side, and the red
    pompom of a grenadier at its top."""

    def P(x: float, y: float) -> Point:
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    # The fan: low and wide, its two points out over the shoulders, so the
    # three-quarter view shows its front face as a crescent.
    fan = [P(-15.0, -5.0), P(-13.0, -9.0), P(-9.0, -13.0), P(-3.0, -15.6), P(3.0, -15.6), P(9.0, -13.0), P(13.0, -9.0), P(15.0, -5.0),
           P(10.0, -6.4), P(4.0, -7.0), P(-4.0, -7.0), P(-10.0, -6.4)]
    pen.poly(fan, BLACK)
    pen.poly([P(-15.0, -5.0), P(-13.0, -9.0), P(-9.0, -13.0), P(-6.0, -12.0), P(-9.0, -8.0), P(-10.0, -6.4)], (28, 24, 26, 255), body=False)
    pen.ink([P(-13.4, -8.4), P(-9.0, -12.4), P(-3.0, -15.0), P(3.0, -15.0), P(9.0, -12.4), P(13.4, -8.4)], 1.0, BLACK_LIGHT)
    pen.ink([P(-9.0, -7.4), P(0.0, -8.4), P(9.0, -7.4)], 0.6, BLACK_LIGHT)
    # The loop (ganse) of orange braid over the cockade, and the cockade.
    pen.ink([P(5.0, -9.5), P(6.0, -14.4)], 1.4, (226, 150, 60, 255))
    cx, cy = P(5.0, -10.0)
    pen.ellipse(cx, cy, 3.6, 3.6, RED, body=False)
    pen.ellipse(cx, cy, 2.5, 2.5, WHITE, body=False)
    pen.ellipse(cx, cy, 1.3, 1.3, COCKADE_BLUE, body=False)
    # The red pompom.
    px, py = P(1.0, -17.0)
    pen.ellipse(px, py, 2.8, 2.6, RED)
    pen.ellipse(px - 0.8, py - 0.8, 1.2, 1.0, (224, 96, 84, 255), body=False)


def _pose(anim: str, i: int, n: int) -> dict:
    """The pose of one frame: the place of the hips, the lean, the feet, the
    musket and the flags of the frame."""
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    p = dict(hip_x=52.0, crouch=0.0, lean=0.0, bob=0.0, near=(5.0, 0.0), far=(-5.0, 0.0), carry="order", butt=None, angle=-90.0,
             alarm=False, fade=1.0, rot=0.0, flash=0.0, tilt=0.0, t=t, fall=0.0)
    guard = dict(hip_x=40.0, crouch=4.0, lean=6.0, near=(-10.0, 0.0), far=(13.0, 0.0), carry="guard")
    if anim == "idle":
        # At order arms: the butt by the near foot, the musket upright.
        p.update(bob=0.6 * math.sin(cyc), angle=-90.0 + 0.8 * math.sin(cyc))
    elif anim == "walk":
        # A march with the musket on the shoulder.
        p.update(near=(10.0 * math.sin(cyc), 5.0 * max(0.0, math.cos(cyc))), far=(-10.0 * math.sin(cyc), 5.0 * max(0.0, -math.cos(cyc))),
                 bob=-1.6 * abs(math.cos(cyc)), lean=3.0, carry="shoulder", angle=-110.0 + 1.5 * math.sin(cyc))
    elif anim == "notice":
        # He brings the musket down to the guard and takes his stance.
        u = min(1.0, t * 1.5)
        e = u * u * (3.0 - 2.0 * u)
        p.update(hip_x=52.0 + (guard["hip_x"] - 52.0) * e, crouch=guard["crouch"] * e, lean=guard["lean"] * e,
                 near=(5.0 + (guard["near"][0] - 5.0) * e, 0.0), far=(-5.0 + (guard["far"][0] + 5.0) * e, 0.0), carry="guard",
                 angle=-90.0 + 82.0 * e, alarm=True, mix=e)
    elif anim == "windup":
        # The musket drawn back, the weight on the back foot.
        p.update(guard, crouch=6.0 + 0.6 * math.sin(cyc * 2.0), lean=-4.0, hip_x=36.0, angle=-12.0 + 1.0 * math.sin(cyc * 2.0), draw=-12.0)
    elif anim == "attack_side":
        # The lunge: a long step, the body forward, the arms drive the point.
        go = math.sin(math.pi * 0.5 * min(1.0, t / 0.45))
        back = max(0.0, (t - 0.65) / 0.35)
        go *= 1.0 - 0.6 * back
        p.update(guard, hip_x=36.0 + 20.0 * go, crouch=6.0 + 1.0 * go, lean=-4.0 + 16.0 * go, near=(-12.0 - 16.0 * go, 0.0),
                 far=(13.0 + 13.0 * go, 0.0), angle=-12.0 + 10.0 * go, draw=-12.0 + 33.0 * go, flash=1.0 if 1 <= i <= 2 else 0.0)
    elif anim == "hit":
        # He staggers back; the musket swings up.
        k = math.sin(math.pi * (i + 1) / (n + 1))
        p.update(guard, hip_x=42.0 - 6.0 * k, lean=-14.0 * k, crouch=5.0, near=(-12.0, 0.0), far=(8.0, 0.0), angle=-8.0 - 30.0 * k,
                 draw=-6.0 * k, flash=k, tilt=-10.0 * k)
    elif anim == "death":
        # His knees go and he falls on his back; the musket falls ahead.
        fall = min(1.0, t / 0.8)
        p.update(guard, crouch=10.0 * min(1.0, fall * 2.0), hip_x=42.0 + 72.0 * fall, lean=-8.0 * min(1.0, fall * 3.0),
                 near=(4.0, 0.0), far=(-2.0, 0.0), rot=-82.0 * min(1.0, max(0.0, (fall - 0.15) / 0.7)) ** 1.2, carry="dropped",
                 fade=1.0 - max(0.0, t - 0.7) / 0.3, fall=fall, tilt=12.0 * fall)
    return p


def _render_frame(anim: str, i: int, n: int):
    p = _pose(anim, i, n)
    t = p["t"]
    f = K.Frame(FRAME_SIZE)
    hip_x = p["hip_x"]
    rot = p["rot"]
    # A body on its back lies on its back, not under the floor.
    pen = S.Pen(f, (hip_x - 4.0, GROUND - 3.0), rot, (0.0, 12.0 * rot / 82.0))
    hip_y = GROUND - (THIGH + SHIN - 1.0) + p["crouch"] + p["bob"]
    lr = math.radians(p["lean"])

    def T(u: float, w: float) -> Point:
        """The point `u` px up the body from the hips and `w` px forward."""
        return (hip_x + math.sin(lr) * u + math.cos(lr) * w, hip_y - math.cos(lr) * u + math.sin(lr) * w)

    hip = (hip_x, hip_y)
    shoulder_near = T(TORSO - 4.0, 0.0)
    shoulder_far = T(TORSO - 4.0, -2.0)

    # The musket: where its butt is for each way to carry it.
    carry, angle = p["carry"], p["angle"]
    draw = p.get("draw", 0.0)
    if carry == "order":
        butt = (hip_x + 12.0, GROUND - 3.0)
    elif carry == "shoulder":
        butt = T(3.0, 6.0)
    elif carry == "guard" and "mix" in p:
        e = p["mix"]
        order = (hip_x + 12.0, GROUND - 3.0)
        guard = T(6.0, -10.0)
        butt = (order[0] + (guard[0] - order[0]) * e, order[1] + (guard[1] - order[1]) * e)
    else:
        a = math.radians(angle)
        butt = T(6.0, -10.0)
        butt = (butt[0] + math.cos(a) * draw, butt[1] + math.sin(a) * draw)

    # The far arm, behind the body: it holds the fore grip, or hangs.
    def far_arm(grip: Optional[Point]) -> None:
        hand = grip if grip else T(-2.0, 3.0)
        _, end = H.arm(pen, shoulder_far, hand, UPPER_ARM, FOREARM, 5.2, COAT_SHADE, elbow_out=1.0 if grip is None else -1.0)
        if grip is None:
            pen.ellipse(end[0], end[1], 2.8, 2.6, SKIN_SHADE)

    def a_leg(spec: Tuple[float, float], breeches, gaiter) -> None:
        dx, lift = spec
        foot = (hip_x + dx, GROUND - 3.0 - lift)
        knee, ankle = H.leg(pen, (hip_x + dx * 0.15, hip_y), foot, THIGH, SHIN, 7.0, breeches)
        # A black gaiter from under the knee to the shoe, buttoned on its side.
        pen.limb([H.lerp(knee, ankle, 0.08), ankle], 6.6, gaiter)
        for u in (0.3, 0.5, 0.7):
            x, y = H.lerp(knee, ankle, u)
            pen.dot(x + 1.6, y, 0.6, BLACK_LIGHT)
        pen.poly([(ankle[0] - 3.0, ankle[1] - 1.0), (ankle[0] + 7.0, ankle[1] + 0.6), (ankle[0] + 7.4, ankle[1] + 3.0), (ankle[0] - 3.0, ankle[1] + 3.0)],
                 BLACK)

    grips: List[Point] = []
    if carry == "dropped":
        # The musket falls from his hands and lies on the ground ahead.
        fall = p["fall"]
        ang = -8.0 + 8.0 * fall
        drop = min(1.0, fall * 1.6)
        b0 = T(6.0, -10.0)
        b1 = (64.0, GROUND - 3.0)
        mb = (b0[0] + (b1[0] - b0[0]) * drop, b0[1] + (b1[1] - b0[1]) * drop)
        _musket(S.Pen(f), mb, ang)

    if carry == "guard" or carry == "shoulder" or carry == "order":
        a = math.radians(angle)
        d = (math.cos(a), math.sin(a))
        wrist = (butt[0] + d[0] * (WRIST + 1.0), butt[1] + d[1] * (WRIST + 1.0))
        fore = (butt[0] + d[0] * FORE_GRIP, butt[1] + d[1] * FORE_GRIP)
        grips = [wrist, fore]

    far_arm(grips[1] if carry == "guard" else None)
    a_leg(p["far"], WHITE_SHADE, (30, 26, 28, 255))

    # The tails of the coat, behind: blue, with red turnbacks.
    tail = [T(6.0, -7.0), T(-24.0, -13.0), T(-25.0, -6.0), T(-6.0, -2.0)]
    pen.poly(tail, COAT)
    pen.poly([T(-2.0, -5.0), T(-24.5, -9.0), T(-25.0, -6.0), T(-6.0, -2.0)], RED, body=False)
    pen.ink([T(4.0, -7.4), T(-23.0, -12.6)], 0.8, COAT_SHADE)
    # The black cartridge box on its belt at the back of the hip.
    pen.poly([T(9.0, -13.0), T(9.0, -6.0), T(1.0, -6.0), T(1.0, -13.0)], BLACK)
    pen.ink([T(8.0, -12.0), T(8.0, -7.0)], 0.8, BLACK_LIGHT)

    # The body: white breeches at the hips, the coat over the trunk; at the
    # front the white lapels and the white waistcoat under them.
    pen.poly([T(-3.0, -7.0), T(-3.0, 7.0), T(4.0, 8.0), T(4.0, -7.0)], WHITE)
    body = [T(2.0, -7.5), T(TORSO - 6.0, -8.0), T(TORSO - 1.0, -5.0), T(TORSO + 1.0, 2.0), T(TORSO - 4.0, 6.5), T(22.0, 9.0),
            T(10.0, 8.6), T(3.0, 7.5), T(2.0, 4.0)]
    pen.poly(body, COAT)
    pen.poly([T(2.0, -7.5), T(TORSO - 6.0, -8.0), T(TORSO - 3.0, -4.0), T(6.0, -3.5)], COAT_SHADE, body=False)
    # The waistcoat, between the lapels and the waist.
    pen.poly([T(13.0, 4.0), T(13.0, 8.8), T(3.0, 7.8), T(3.0, 3.0)], WHITE, body=False)
    pen.ink([T(4.0, 7.0), T(12.0, 8.0)], 0.6, WHITE_SHADE)
    # The lapel: a white plastron on the chest with its buttons.
    pen.poly([T(TORSO - 3.0, 3.0), T(TORSO - 4.0, 6.6), T(22.0, 9.1), T(13.0, 8.9), T(13.0, 4.0)], WHITE, body=False)
    for u in (16.0, 20.0, 24.0, 28.0):
        pen.dot(*T(u, 6.8), 0.6, BRASS)
    pen.ink([T(13.0, 4.0), T(TORSO - 3.0, 3.0)], 0.7, WHITE_SHADE)
    # The white crossbelts.
    pen.limb([T(TORSO - 4.0, 5.0), T(3.0, -7.0)], 2.6, WHITE, body=False)
    pen.limb([T(TORSO - 4.0, -6.0), T(4.0, 7.0)], 2.6, WHITE, body=False)
    pen.ink([T(TORSO - 4.0, 4.0), T(3.0, -8.0)], 0.5, WHITE_SHADE)
    pen.ellipse(*T(TORSO * 0.5 - 1.0, -0.6), 1.6, 1.4, BRASS, body=False)
    # The red collar.
    pen.poly([T(TORSO - 1.0, -5.0), T(TORSO + 3.0, -4.0), T(TORSO + 3.0, 2.6), T(TORSO - 1.0, 3.4)], RED)

    a_leg(p["near"], WHITE, BLACK)

    # On the march the musket leans back over the shoulder, behind the head.
    if carry == "shoulder":
        _musket(pen, butt, angle)

    # The head: in profile, a calm face, short hair, the bicorne.
    tilt = p["lean"] * 0.4 + p["tilt"]
    neck = T(TORSO + 2.0, -0.5)
    hx, hy = T(TORSO + 10.0, 0.5)

    def Hd(x: float, y: float) -> Point:
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    pen.limb([neck, Hd(-1.0, 4.0)], 5.0, SKIN)
    head = [Hd(-7.0, -2.0), Hd(-6.0, -6.0), Hd(0.0, -8.0), Hd(5.0, -6.5), Hd(6.5, -3.0), Hd(8.6, 0.2), Hd(6.6, 1.4), Hd(7.0, 3.0), Hd(6.2, 4.4),
            Hd(6.4, 5.6), Hd(4.6, 7.8), Hd(0.5, 8.4), Hd(-3.0, 6.6), Hd(-6.6, 3.0)]
    pen.poly(head, SKIN)
    pen.poly([Hd(-7.0, -2.0), Hd(-6.0, -6.0), Hd(0.0, -8.0), Hd(2.0, -6.0), Hd(-2.0, -4.0), Hd(-3.0, 1.0), Hd(-6.6, 3.0)], HAIR, body=False)
    pen.poly([Hd(-1.0, -4.0), Hd(1.0, -4.0), Hd(1.6, 3.0), Hd(-0.6, 3.6)], HAIR, body=False)
    pen.ellipse(*Hd(-2.6, 0.4), 1.6, 2.2, SKIN_SHADE, body=False)
    ex, ey = Hd(4.2, -1.6)
    if p["fade"] < 1.0 or p["fall"] > 0.4:
        pen.ink([(ex - 1.2, ey), (ex + 1.0, ey)], 0.8, H.SEPIA_INK)
    else:
        pen.dot(ex, ey, 0.9, H.SEPIA_INK)
    pen.ink([Hd(2.6, -3.6), Hd(5.6, -3.4)], 0.8, HAIR)
    pen.ink([Hd(4.4, 4.6), Hd(6.2, 4.4)], 0.6, SKIN_SHADE)
    _bicorne(pen, hx, hy, tilt)

    # The musket, then the near arm over it.
    tip = None
    if carry in ("guard", "order"):
        tip = _musket(pen, butt, angle)[2]
        if carry == "guard":
            pen.ellipse(grips[1][0], grips[1][1], 2.8, 2.5, SKIN_SHADE)
    if carry == "guard":
        hand = grips[0]
        elbow_out = 1.0
    elif carry == "shoulder":
        hand = (butt[0] + 1.0, butt[1] + 1.0)
        elbow_out = 1.0
    elif carry == "order":
        a = math.radians(angle)
        hand = (butt[0] + math.cos(a) * 48.0 - 1.5, butt[1] + math.sin(a) * 48.0)
        elbow_out = 1.0
    else:
        hand = T(-4.0, 6.0)
        elbow_out = -1.0
    elbow, end = H.arm(pen, shoulder_near, hand, UPPER_ARM, FOREARM, 6.0, COAT, elbow_out=elbow_out)
    # The red cuff at the wrist, with its white flap, and the hand.
    pen.limb([H.lerp(elbow, end, 0.62), H.lerp(elbow, end, 0.88)], 6.6, RED)
    pen.ink([H.lerp(elbow, end, 0.66), H.lerp(elbow, end, 0.84)], 1.0, WHITE)
    pen.ellipse(end[0], end[1], 3.0, 2.8, SKIN)
    # The red epaulette of a grenadier, with its fringe.
    sx, sy = T(TORSO - 3.0, 0.0)
    pen.ellipse(sx, sy, 5.2, 2.6, RED)
    for k in range(4):
        x0, y0 = T(TORSO - 4.5, -3.0 + k * 2.0)
        x1, y1 = T(TORSO - 8.5, -3.6 + k * 2.2)
        pen.ink([(x0, y0), (x1, y1)], 0.9, RED_DARK)

    if p["flash"] > 0.0 and tip is not None and anim == "attack_side":
        # The point flashes at the end of the lunge.
        tx, ty = pen.at(*tip)
        f.glow(tx - 2.0, ty, 4.0, K.alpha(K.WHITE, 0.6))
        for k in range(3):
            ang = math.radians(-120.0 + k * 120.0)
            f.glow_line([(tx - 2.0 + math.cos(ang) * 2.0, ty + math.sin(ang) * 2.0), (tx - 2.0 + math.cos(ang) * 6.0, ty + math.sin(ang) * 6.0)], 1.1,
                        K.alpha(K.WHITE, 0.85))
    if p["flash"] > 0.0 and anim == "hit":
        cx, cy = T(TORSO * 0.6, 12.0)
        for k in range(5):
            ang = math.radians(-70.0 + k * 35.0)
            f.glow_line([(cx + math.cos(ang) * 4.0, cy + math.sin(ang) * 4.0), (cx + math.cos(ang) * (4.0 + 6.0 * p["flash"]),
                                                                                  cy + math.sin(ang) * (4.0 + 6.0 * p["flash"]))], 1.2, K.alpha(K.WHITE, 0.8))
    if anim == "death" and 0.5 < t < 0.95:
        H.dust(f, 70.0, GROUND - 2.0, 30.0, min(1.0, (t - 0.5) * 3.0) * (1.0 - t) * 2.0, f"grenadier:death:{i}")
    if p["alarm"]:
        A.alarm_mark(f, hx + 14.0, hy - 30.0)
    return A.finish(f, fade=p["fade"], width=1.4)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
