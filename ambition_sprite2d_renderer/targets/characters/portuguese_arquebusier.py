"""The Portuguese Arquebusier of the History dimension: a soldier of Angola in the 1620s.

Portugal founded Luanda in 1576. From there its governors made war up the
Kwanza river on the kingdom of Ndongo, for land and for captives to sell
to Brazil. Their armies had a small core of soldiers with firearms, and
many more African soldiers (the guerra preta) and hired Imbangala bands.
Queen Nzinga fought these armies for some thirty years.

This creature is one soldier of the colony, an arquebusier. He wears a
steel morion (a helmet with a high comb along its top and a brim that
turns up to a point at the front and at the back), a padded jack (a coat
of linen quilted over cotton: in the heat of Angola it was better than
steel), loose breeches of red-brown wool to the knee, grey stockings and
shoes. A leather bandolier crosses his chest; from it hang small wooden
flasks, each with one charge of powder. His gun is a matchlock arquebus:
a slow-burning cord (the match) is clamped in the serpentine, a curved
lever on the lock, and its lit end glows. He is drawn as a soldier, not as
a joke.

At rest he stands with the butt of the arquebus on the ground by his foot.
He marches with it on his shoulder. When he sees you he brings it down
across his body, the muzzle up (the notice row). His windup is the slow
aim: the butt at his shoulder, his cheek on the stock, the barrel level,
the match glowing; it loops while he holds the aim. His strike is the
shot: the serpentine snaps down into the pan, the pan flashes, the muzzle
flashes, the gun kicks up, and a cloud of white smoke rolls out in front
and thins as he lowers the gun. The ball itself is the game's projectile.
A hit makes him stagger back and knocks his morion askew. At his death he
falls on his back, the arquebus falls in front of him, and he fades.

The frame is 192 by 160 px: the aimed gun, its flash and its smoke need
the width.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _history_cast_kit as H
from . import _stage_kit as S

TARGET_NAME = "portuguese_arquebusier"
FRAME_SIZE = (192, 160)
ROWS = K.ENEMY_ROWS
GROUND = 151.0
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 5.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Portuguese Arquebusier", "ndongo", "Biped", "Standard", "Medium", "Walk", ["soldier", "arquebus", "matchlock", "ranged"],
    "A soldier of the Portuguese colony of Angola in the 1620s, in the History dimension's Ndongo and Matamba: a steel morion "
    "with a high comb, a padded jack of quilted linen, red-brown breeches and a bandolier of powder flasks, with a matchlock "
    "arquebus. He brings the gun to his shoulder, aims slowly, and fires: the pan and the muzzle flash, and white smoke rolls out.",
)

Point = Tuple[float, float]

THIGH, SHIN = 22.0, 22.0
UPPER_ARM, FOREARM = 16.0, 15.0
TORSO = 34.0
#: The arquebus: the butt is at 0; the wrist of the stock, the lock, the
#: pan, the fore grip and the muzzle are at these distances along it.
WRIST, LOCK, PAN, FORE_GRIP, MUZZLE = 14.0, 19.0, 25.0, 34.0, 76.0

STEEL = (180, 186, 194, 255)
STEEL_SHADE = (120, 126, 140, 255)
STEEL_LIGHT = (228, 232, 238, 255)
IRON = (86, 88, 98, 255)
IRON_LIGHT = (140, 144, 154, 255)
JACK = (214, 196, 156, 255)
JACK_SHADE = (172, 152, 114, 255)
QUILT = (150, 128, 92, 255)
BREECHES = (122, 54, 42, 255)
BREECHES_SHADE = (86, 36, 30, 255)
STOCKING = (150, 146, 136, 255)
STOCKING_SHADE = (116, 112, 104, 255)
SHOE = (52, 40, 36, 255)
LEATHER = (112, 72, 44, 255)
FLASK = (104, 66, 38, 255)
FLASK_CAP = (52, 40, 36, 255)
STOCK = (128, 80, 46, 255)
STOCK_DARK = (86, 54, 32, 255)
SKIN = (214, 170, 132, 255)
SKIN_SHADE = (176, 132, 98, 255)
HAIR = (60, 44, 36, 255)
MATCH = (180, 154, 108, 255)
EMBER = (255, 150, 56, 255)
FLASH = (255, 238, 176, 255)
FLASH_HOT = (255, 172, 72, 255)
SMOKE = (230, 226, 218, 255)
SMOKE_SHADE = (196, 192, 186, 255)


def _arquebus(pen: S.Pen, butt: Point, angle: float, fired: float = 0.0, glow: float = 1.0) -> Dict[str, Point]:
    """The matchlock arquebus, its butt at `butt`, pointed at `angle` degrees
    (0 is forward, -90 is up). `fired` 0 holds the serpentine back with the
    lit match; 1 has it down in the pan. `glow` sets the light of the
    match. Returns the grips, the pan and the muzzle (in pen units)."""
    a = math.radians(angle)
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])

    def at(s: float, w: float = 0.0) -> Point:
        return (butt[0] + d[0] * s + n[0] * w, butt[1] + d[1] * s + n[1] * w)

    # The stock: a deep butt that drops under the line of the barrel, a
    # narrow wrist, then the fore-stock under the barrel to near the muzzle.
    # `w` > 0 is the lower side of the gun when it points forward.
    stock = [at(0.0, -1.6), at(WRIST, -0.8), at(MUZZLE - 8.0, -0.8), at(MUZZLE - 8.0, 1.6), at(WRIST + 6.0, 1.8), at(WRIST, 2.0),
             at(5.0, 5.2), at(0.0, 5.8)]
    pen.poly(stock, STOCK)
    pen.poly([at(0.6, 2.4), at(6.0, 4.4), at(0.6, 5.2)], STOCK_DARK, body=False)
    pen.ink([at(0.3, -1.4), at(0.3, 5.6)], 1.0, IRON)
    # The ramrod in its channel under the fore-stock.
    pen.ink([at(FORE_GRIP - 4.0, 1.2), at(MUZZLE - 2.0, 1.2)], 0.7, STOCK_DARK)
    # The iron barrel along the top, flared a little at the muzzle.
    pen.limb([at(WRIST - 2.0, -1.6), at(MUZZLE, -1.6)], 2.4, IRON)
    pen.ink([at(WRIST, -2.4), at(MUZZLE - 1.0, -2.4)], 0.5, IRON_LIGHT)
    pen.limb([at(MUZZLE - 2.0, -1.6), at(MUZZLE + 0.6, -1.6)], 3.2, IRON)
    pen.dot(*at(MUZZLE - 50.0, -3.2), 0.6, IRON_LIGHT)
    # The lock: a plate on the side of the stock, the pan with its cover
    # forward of it, and the long trigger lever under the stock.
    pen.poly([at(LOCK - 4.0, -0.6), at(PAN, -0.6), at(PAN, 1.4), at(LOCK - 4.0, 1.4)], IRON_LIGHT, body=False)
    pen.poly([at(PAN - 1.0, -2.2), at(PAN + 3.0, -2.2), at(PAN + 3.0, -0.6), at(PAN - 1.0, -0.6)], IRON)
    pen.limb([at(LOCK - 2.0, 2.0), at(LOCK + 3.0, 5.4), at(LOCK + 7.0, 5.8)], 1.2, IRON)
    # The serpentine: an S of iron that turns on a pin. Back, it holds the
    # match above the pan; when he fires, it swings down into the pan.
    pivot = at(LOCK, 0.4)
    back = math.radians(-120.0 + 70.0 * fired)
    bend = math.radians(-60.0 + 70.0 * fired)
    elbow = (pivot[0] + 5.0 * math.cos(a + back), pivot[1] + 5.0 * math.sin(a + back))
    jaws = (elbow[0] + 4.0 * math.cos(a + bend), elbow[1] + 4.0 * math.sin(a + bend))
    pen.limb([pivot, elbow, jaws], 1.6, IRON)
    pen.dot(*pivot, 0.8, IRON_LIGHT)
    # The match: its lit end in the jaws, its cord back over the wrist.
    pen.limb([jaws, (jaws[0] - 3.0 * d[0], jaws[1] - 3.0 * d[1]), at(WRIST - 3.0, 1.0), at(WRIST - 1.0, 6.0)], 1.0, MATCH, body=False)
    if glow > 0.0:
        pen.glow(jaws[0], jaws[1], 2.4 * glow, K.alpha(EMBER, 0.85))
        pen.dot(jaws[0], jaws[1], 0.9, EMBER)
    return {"wrist": at(WRIST + 1.0, 0.6), "fore": at(FORE_GRIP, 0.8), "pan": at(PAN + 1.0, -2.6), "muzzle": at(MUZZLE + 1.0, -1.6),
            "jaws": jaws, "dir": d}


def _morion(pen: S.Pen, hx: float, hy: float, tilt: float) -> None:
    """The comb morion, seen from the side: a round crown, a high comb along
    its top, and a brim that turns up to a point at the front and at the
    back. A row of rivets holds the lining band."""

    def P(x: float, y: float) -> Point:
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    # The crown: a dome over the top of the head.
    crown = [P(-8.4, -3.4)] + [P(8.4 * math.cos(math.radians(a)), -3.4 - 9.0 * math.sin(math.radians(a))) for a in range(180, -1, -15)]
    pen.poly(crown, STEEL)
    pen.poly([P(-8.4, -3.4), P(-8.0, -6.6), P(-6.0, -10.0), P(-3.0, -11.8), P(-2.0, -8.0), P(-4.0, -4.0)], STEEL_SHADE, body=False)
    pen.ink([P(2.0, -11.0), P(6.0, -8.0)], 0.9, STEEL_LIGHT)
    # The comb: a high thin crest, from the front of the crown to the back.
    comb = [P(-6.6, -9.0), P(-5.0, -14.4), P(-1.6, -18.0), P(2.0, -18.4), P(5.0, -15.4), P(6.8, -9.4)]
    pen.poly(comb, STEEL)
    pen.ink([P(-4.4, -13.6), P(-1.0, -17.0), P(2.4, -17.2)], 0.7, STEEL_LIGHT)
    pen.ink([P(-5.6, -9.6), P(5.8, -9.8)], 0.6, STEEL_SHADE)
    # The brim: a thin crescent, low at the sides and up to two points.
    brim = [P(-14.0, -10.0), P(-10.0, -5.0), P(-4.0, -2.4), P(4.0, -2.4), P(10.0, -5.0), P(14.6, -10.6), P(12.0, -6.4), P(6.0, -4.0),
            P(-6.0, -4.0), P(-12.0, -6.4)]
    pen.poly(brim, STEEL)
    pen.ink([P(-12.0, -7.4), P(-6.0, -3.6), P(6.0, -3.6), P(12.4, -7.6)], 0.6, STEEL_SHADE)
    for k in range(5):
        pen.dot(*P(-6.0 + k * 3.0, -5.4), 0.55, STEEL_SHADE)


def _pose(anim: str, i: int, n: int) -> dict:
    """The pose of one frame: the place of the hips, the lean, the feet, how
    he carries the gun, and the flags of the frame."""
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    p = dict(hip_x=56.0, crouch=0.0, lean=0.0, bob=0.0, near=(5.0, 0.0), far=(-5.0, 0.0), carry="order", angle=-90.0, alarm=False,
             fade=1.0, rot=0.0, tilt=0.0, t=t, fall=0.0, fired=0.0, glow=1.0, flash=0.0, pan=0.0, smoke=0.0, kick=0.0, askew=0.0)
    aim = dict(hip_x=50.0, crouch=3.0, lean=4.0, near=(-10.0, 0.0), far=(12.0, 0.0), carry="aim", angle=-2.0)
    if anim == "idle":
        # At rest: the butt by the near foot, the gun upright; the match smoulders.
        p.update(bob=0.6 * math.sin(cyc), angle=-90.0 + 0.8 * math.sin(cyc), glow=0.7 + 0.3 * math.sin(cyc * 2.0))
    elif anim == "walk":
        # A march with the gun on the shoulder.
        p.update(near=(10.0 * math.sin(cyc), 5.0 * max(0.0, math.cos(cyc))), far=(-10.0 * math.sin(cyc), 5.0 * max(0.0, -math.cos(cyc))),
                 bob=-1.6 * abs(math.cos(cyc)), lean=3.0, carry="shoulder", angle=-112.0 + 1.5 * math.sin(cyc))
    elif anim == "notice":
        # He brings the gun down across his body, the muzzle up, and takes
        # his stance.
        u = min(1.0, t * 1.5)
        e = u * u * (3.0 - 2.0 * u)
        p.update(hip_x=56.0 - 4.0 * e, crouch=2.0 * e, lean=2.0 * e, near=(5.0 - 13.0 * e, 0.0), far=(-5.0 + 16.0 * e, 0.0), carry="port",
                 angle=-90.0 + 46.0 * e, mix=e, alarm=True)
    elif anim == "windup":
        # The slow aim: the butt at the shoulder, the cheek on the stock.
        # He holds it and breathes; the match glows brighter and dimmer.
        p.update(aim, crouch=3.0 + 0.5 * math.sin(cyc), angle=-2.0 + 0.8 * math.sin(cyc), glow=0.75 + 0.25 * math.sin(cyc * 2.0))
    elif anim == "attack_side":
        # The shot, as key frames: fired (the serpentine), pan flash, muzzle
        # flash, kick (degrees up), smoke, and the lower of the gun after it.
        table = [
            (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            (1.0, 1.0, 0.0, 0.0, 0.15, 0.0),
            (1.0, 0.5, 1.0, 9.0, 0.35, 0.0),
            (1.0, 0.0, 0.3, 5.0, 0.65, 0.0),
            (1.0, 0.0, 0.0, 2.0, 0.85, 0.2),
            (1.0, 0.0, 0.0, 0.0, 1.0, 0.6),
        ]
        fired, pan, flash, kick, smoke, lower = table[i]
        p.update(aim, fired=fired, pan=pan, flash=flash, kick=kick, smoke=smoke, glow=1.0 - 0.6 * fired,
                 angle=-2.0 - kick - 40.0 * lower, lean=4.0 - 0.4 * kick - 2.0 * lower, hip_x=50.0 - 0.3 * kick)
        if lower:
            p.update(carry="port", mix=1.0)
    elif anim == "hit":
        # He staggers back; the gun swings up and the morion is knocked askew.
        k = math.sin(math.pi * (i + 1) / (n + 1))
        p.update(aim, hip_x=48.0 - 6.0 * k, lean=-12.0 * k, crouch=4.0, near=(-12.0, 0.0), far=(8.0, 0.0), angle=-14.0 - 30.0 * k,
                 tilt=-8.0 * k, askew=k, carry="port", mix=1.0)
    elif anim == "death":
        # His knees go and he falls on his back; the arquebus falls ahead.
        fall = min(1.0, t / 0.8)
        p.update(aim, crouch=10.0 * min(1.0, fall * 2.0), hip_x=48.0 + 66.0 * fall, lean=-8.0 * min(1.0, fall * 3.0), near=(4.0, 0.0),
                 far=(-2.0, 0.0), rot=-82.0 * min(1.0, max(0.0, (fall - 0.15) / 0.7)) ** 1.2, carry="dropped",
                 fade=1.0 - max(0.0, t - 0.7) / 0.3, fall=fall, tilt=12.0 * fall, glow=1.0 - fall)
    return p


def _smoke(f: K.Frame, muzzle: Point, pan: Point, amount: float, seed: int) -> None:
    """The white smoke of the shot: a cloud that rolls out from the muzzle
    and thins, and a small puff over the pan. `amount` 0..1 is its age."""
    if amount <= 0.0:
        return
    mx, my = muzzle
    fade = 1.0 - max(0.0, amount - 0.6) / 0.4 * 0.7
    puffs = [(0.0, 0.0, 5.0), (8.0, -2.0, 6.0), (16.0, 1.0, 6.5), (24.0, -3.0, 6.0), (12.0, -8.0, 5.0), (30.0, -7.0, 5.0)]
    for k, (dx, dy, r) in enumerate(puffs):
        grow = min(1.0, amount * 1.6 - k * 0.12)
        if grow <= 0.0:
            continue
        x = mx + 2.0 + dx * (0.4 + 0.6 * amount)
        y = my + dy * (0.5 + amount) - 6.0 * amount * amount
        rr = r * (0.5 + 0.7 * grow)
        x = min(FRAME_SIZE[0] - MARGIN - rr - 1.0, x)
        f.ellipse(x, y, rr, rr * 0.82, K.alpha(SMOKE, 0.82 * fade), body=False)
        f.ellipse(x + rr * 0.2, y + rr * 0.3, rr * 0.7, rr * 0.45, K.alpha(SMOKE_SHADE, 0.6 * fade), body=False)
    px, py = pan
    r = 2.5 + 3.5 * min(1.0, amount * 1.5)
    f.ellipse(px + 1.0, py - 3.0 - 6.0 * amount, r, r * 0.8, K.alpha(SMOKE, 0.75 * fade), body=False)


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

    # Where the butt of the gun is for each way to carry it.
    carry, angle = p["carry"], p["angle"]
    if carry == "order":
        butt = (hip_x + 12.0, GROUND - 3.0)
    elif carry == "shoulder":
        butt = T(4.0, 8.0)
    elif carry == "port":
        order = (hip_x + 12.0, GROUND - 3.0)
        port = T(6.0, 4.0)
        e = p.get("mix", 1.0)
        butt = (order[0] + (port[0] - order[0]) * e, order[1] + (port[1] - order[1]) * e)
    elif carry == "aim":
        # The butt in the hollow of the near shoulder; the kick pushes it back.
        butt = T(TORSO - 6.0, 3.0 - 1.2 * p["kick"] / 9.0)
    else:
        butt = None

    def a_leg(spec: Tuple[float, float], breeches, stocking) -> None:
        dx, lift = spec
        foot = (hip_x + dx, GROUND - 3.0 - lift)
        knee, ankle = H.leg(pen, (hip_x + dx * 0.15, hip_y), foot, THIGH, SHIN, 6.4, stocking)
        # Loose breeches to just below the knee, tied with a garter.
        thigh_top = (hip_x + dx * 0.15, hip_y - 2.0)
        pen.limb([thigh_top, H.lerp(thigh_top, knee, 0.6), H.lerp(knee, ankle, 0.18)], 10.0, breeches)
        g0, g1 = H.lerp(knee, ankle, 0.12), H.lerp(knee, ankle, 0.22)
        pen.limb([g0, g1], 7.0, BREECHES_SHADE, body=False)
        # The shoe: low, with a square toe.
        pen.poly([(ankle[0] - 3.0, ankle[1] - 1.0), (ankle[0] + 7.0, ankle[1] + 0.4), (ankle[0] + 7.6, ankle[1] + 3.0), (ankle[0] - 3.0, ankle[1] + 3.0)],
                 SHOE)

    gun: Optional[Dict[str, Point]] = None
    if carry == "dropped":
        # The gun falls from his hands and lies on the ground ahead.
        fall = p["fall"]
        drop = min(1.0, fall * 1.6)
        b0 = T(TORSO - 6.0, 3.0)
        b1 = (74.0, GROUND - 4.0)
        mb = (b0[0] + (b1[0] - b0[0]) * drop, b0[1] + (b1[1] - b0[1]) * drop)
        _arquebus(S.Pen(f), mb, -2.0 + 4.0 * fall, fired=1.0, glow=p["glow"])

    # The far arm (behind the body) and the far leg.
    far_grip = None
    if carry in ("port", "aim"):
        a = math.radians(angle)
        far_grip = (butt[0] + math.cos(a) * (FORE_GRIP + 0.8), butt[1] + math.sin(a) * (FORE_GRIP + 0.8))
    hand = far_grip if far_grip else T(-2.0, 3.0)
    _, end = H.arm(pen, shoulder_far, hand, UPPER_ARM, FOREARM, 5.6, JACK_SHADE, elbow_out=-1.0 if far_grip else 1.0)
    pen.ellipse(end[0], end[1], 2.8, 2.6, SKIN_SHADE)
    a_leg(p["far"], BREECHES_SHADE, STOCKING_SHADE)

    # The body: the padded jack, quilted in diamonds, with short skirts
    # over the hips.
    skirt = [T(4.0, -8.0), T(-5.0, -10.0), T(-6.0, 10.0), T(4.0, 9.0)]
    pen.poly(skirt, JACK)
    for w in (-5.0, 0.0, 5.0):
        pen.ink([T(3.0, w), T(-5.0, w + (0.5 if w > 0 else -0.5))], 0.6, QUILT)
    body = [T(3.0, -8.0), T(TORSO - 5.0, -8.6), T(TORSO - 1.0, -5.4), T(TORSO + 1.0, 2.0), T(TORSO - 4.0, 7.6), T(20.0, 10.0),
            T(8.0, 9.4), T(3.0, 8.0)]
    pen.poly(body, JACK)
    pen.poly([T(3.0, -8.0), T(TORSO - 5.0, -8.6), T(TORSO - 3.0, -4.0), T(5.0, -3.6)], JACK_SHADE, body=False)
    # The quilting: two sets of slanted lines make the diamonds.
    for k in range(-3, 4):
        u0 = 6.0 + k * 5.0
        a0, a1 = T(max(4.0, u0), -7.0), T(min(TORSO - 3.0, u0 + 14.0), 8.0)
        b0, b1 = T(max(4.0, u0 + 14.0), -7.0), T(min(TORSO - 3.0, u0), 8.0)
        if u0 + 14.0 > 4.0 and u0 < TORSO - 3.0:
            pen.ink([a0, a1], 0.5, QUILT)
            pen.ink([b0, b1], 0.5, QUILT)
    # The belt at the waist, and the buttons down the front.
    pen.limb([T(4.0, -8.4), T(4.0, 9.6)], 2.6, LEATHER, body=False)
    for u in (10.0, 16.0, 22.0, 28.0):
        pen.dot(*T(u, 8.4), 0.6, STEEL_SHADE)
    # The bandolier over the near shoulder to the far hip, with its flasks.
    pen.limb([T(TORSO - 3.0, 4.0), T(4.0, -9.0)], 2.4, LEATHER, body=False)
    for k in range(4):
        u = 8.0 + k * 5.6
        w = -9.0 + 13.0 * (u - 4.0) / (TORSO - 7.0)
        top = T(u, w)
        pen.limb([top, (top[0], top[1] + 6.0)], 3.4, FLASK, body=False)
        pen.dot(top[0], top[1] - 0.6, 1.2, FLASK_CAP)
    # The small collar of the shirt at the neck.
    pen.poly([T(TORSO - 1.0, -4.0), T(TORSO + 2.4, -3.0), T(TORSO + 2.4, 2.6), T(TORSO - 1.0, 3.4)], (232, 226, 210, 255))

    a_leg(p["near"], BREECHES, STOCKING)

    # On the march the gun leans back over the shoulder, behind the head.
    if carry == "shoulder":
        gun = _arquebus(pen, butt, angle, glow=p["glow"])

    # The head: in profile, a calm face, a moustache and a short pointed
    # beard, and the morion. In the aim he lowers his cheek to the stock.
    tilt = p["lean"] * 0.4 + p["tilt"]
    if carry == "aim":
        hx, hy = T(TORSO + 7.5, 3.0)
        tilt += 10.0
    else:
        hx, hy = T(TORSO + 10.0, 0.5)
    neck = T(TORSO + 2.0, -0.5)

    def Hd(x: float, y: float) -> Point:
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    pen.limb([neck, Hd(-1.0, 4.0)], 5.0, SKIN)
    head = [Hd(-7.0, -2.0), Hd(-6.0, -6.0), Hd(0.0, -8.0), Hd(5.0, -6.5), Hd(6.5, -3.0), Hd(8.6, 0.2), Hd(6.6, 1.4), Hd(7.0, 3.0), Hd(6.2, 4.4),
            Hd(6.4, 5.6), Hd(4.6, 7.8), Hd(0.5, 8.4), Hd(-3.0, 6.6), Hd(-6.6, 3.0)]
    pen.poly(head, SKIN)
    pen.poly([Hd(-7.0, -2.0), Hd(-6.6, -4.0), Hd(-2.0, -4.0), Hd(-3.0, 2.0), Hd(-6.6, 3.0)], HAIR, body=False)
    pen.ellipse(*Hd(-2.4, 0.6), 1.6, 2.2, SKIN_SHADE, body=False)
    # The beard: short and pointed, along the jaw to the chin.
    pen.poly([Hd(-2.0, 4.0), Hd(2.0, 5.4), Hd(5.6, 5.4), Hd(5.4, 7.6), Hd(3.0, 10.8), Hd(0.4, 8.6), Hd(-3.0, 6.6)], HAIR, body=False)
    pen.limb([Hd(3.6, 3.8), Hd(7.0, 4.4)], 1.3, HAIR, body=False)
    ex, ey = Hd(4.2, -1.6)
    if p["fade"] < 1.0 or p["fall"] > 0.4:
        pen.ink([(ex - 1.2, ey), (ex + 1.0, ey)], 0.8, H.SEPIA_INK)
    elif carry == "aim":
        # One eye shut along the barrel.
        pen.ink([(ex - 1.2, ey + 0.2), (ex + 1.2, ey - 0.2)], 0.9, H.SEPIA_INK)
    else:
        pen.dot(ex, ey, 0.9, H.SEPIA_INK)
    pen.ink([Hd(2.6, -3.6), Hd(5.6, -3.4)], 0.8, HAIR)
    _morion(pen, hx, hy, tilt - 14.0 * p["askew"])

    # The gun in the hands, then the near arm over it.
    if carry in ("order", "port", "aim"):
        gun = _arquebus(pen, butt, angle, fired=p["fired"], glow=p["glow"])
        if far_grip:
            pen.ellipse(far_grip[0], far_grip[1], 2.8, 2.5, SKIN_SHADE)
    if carry in ("port", "aim"):
        hand, elbow_out = gun["wrist"], 1.0
    elif carry == "shoulder":
        hand, elbow_out = (butt[0] + 1.0, butt[1] + 1.0), 1.0
    elif carry == "order":
        a = math.radians(angle)
        hand, elbow_out = (butt[0] + math.cos(a) * 52.0 - 1.5, butt[1] + math.sin(a) * 52.0), 1.0
    else:
        hand, elbow_out = T(-4.0, 6.0), -1.0
    elbow, end = H.arm(pen, shoulder_near, hand, UPPER_ARM, FOREARM, 6.4, JACK, elbow_out=elbow_out)
    # The quilted sleeve: rings round the arm.
    for u in (0.3, 0.55, 0.8):
        a0 = H.lerp(shoulder_near, elbow, u)
        b0 = H.lerp(elbow, end, u * 0.8)
        pen.ink([(a0[0] - 2.4, a0[1] - 1.0), (a0[0] + 2.4, a0[1] + 1.0)], 0.5, QUILT)
        pen.ink([(b0[0] - 2.2, b0[1] - 1.2), (b0[0] + 2.2, b0[1] + 1.2)], 0.5, QUILT)
    pen.ellipse(end[0], end[1], 3.0, 2.8, SKIN)
    # The shoulder wing of the jack.
    sx, sy = T(TORSO - 3.0, 0.0)
    pen.ellipse(sx, sy, 5.0, 3.0, JACK)
    pen.ink([(sx - 4.0, sy), (sx + 4.0, sy)], 0.5, QUILT)

    if gun is not None and anim == "attack_side":
        mx, my = pen.at(*gun["muzzle"])
        px, py = pen.at(*gun["pan"])
        dx, dy = gun["dir"]
        if p["pan"] > 0.0:
            # The flash in the pan, up out of the side of the lock.
            f.glow(px, py - 1.0, 4.0 * p["pan"], K.alpha(FLASH, 0.9))
            for k in range(4):
                ang = math.radians(-150.0 + k * 40.0)
                f.glow_line([(px + math.cos(ang) * 1.5, py + math.sin(ang) * 1.5), (px + math.cos(ang) * 6.0 * p["pan"], py + math.sin(ang) * 6.0 * p["pan"])],
                            1.0, K.alpha(FLASH_HOT, 0.9))
        if p["flash"] > 0.0:
            # The muzzle flash: a star of fire out along the barrel.
            k_ = p["flash"]
            f.glow(mx + dx * 5.0, my + dy * 5.0, 7.0 * k_, K.alpha(FLASH_HOT, 0.85))
            f.glow(mx + dx * 3.0, my + dy * 3.0, 4.0 * k_, K.alpha(FLASH, 0.95))
            for ang in (-40.0, -18.0, 0.0, 18.0, 40.0):
                r = math.radians(ang)
                ux, uy = dx * math.cos(r) - dy * math.sin(r), dx * math.sin(r) + dy * math.cos(r)
                ln = (16.0 if ang == 0.0 else 9.0) * k_
                f.glow_line([(mx + ux * 2.0, my + uy * 2.0), (min(FRAME_SIZE[0] - MARGIN - 2.0, mx + ux * ln), my + uy * ln)], 1.6, K.alpha(FLASH, 0.9))
        _smoke(f, (mx, my), (px, py), p["smoke"], i)
    if gun is not None and anim in ("idle", "windup"):
        # A thin thread of smoke from the lit match.
        jx, jy = pen.at(*gun["jaws"])
        sway = math.sin(math.tau * t) * 1.5
        f.ink([(jx, jy - 1.0), (jx + 1.0 + sway, jy - 5.0), (jx - 0.5 + sway, jy - 9.0), (jx + 1.0, jy - 13.0)], 0.6, K.alpha(SMOKE, 0.7))
    if anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        cx, cy = T(TORSO * 0.6, 12.0)
        for j in range(5):
            ang = math.radians(-70.0 + j * 35.0)
            f.glow_line([(cx + math.cos(ang) * 4.0, cy + math.sin(ang) * 4.0), (cx + math.cos(ang) * (4.0 + 6.0 * k), cy + math.sin(ang) * (4.0 + 6.0 * k))],
                        1.2, K.alpha(K.WHITE, 0.8))
    if anim == "death" and 0.5 < t < 0.95:
        H.dust(f, 76.0, GROUND - 2.0, 30.0, min(1.0, (t - 0.5) * 3.0) * (1.0 - t) * 2.0, f"arquebusier:death:{i}")
    if p["alarm"]:
        A.alarm_mark(f, hx + 16.0, max(16.0, hy - 32.0))
    return A.finish(f, fade=p["fade"], width=1.4)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
