"""The Hoplite: a Greek citizen soldier of the Classical Shore.

A soldier behind a big round bronze shield (an aspis) with a crimson lambda
on it, in a bronze helmet with a tall crimson crest, a bronze cuirass over a
crimson chiton, bronze greaves, and a red cloak. He holds a long spear (a
dory) with a spike at its butt.

He is the wall of the dimension: his shield comes up first. At rest the
spear stands upright beside him. When he sees you he lifts the shield to
his eyes and levels the spear over its rim (a block). His windup draws the
spear back behind the shield; his strike is a thrust over the rim with a
step. A hit rings on the shield and pushes him back; at his death he falls
on his back and his crest droops.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_cast_kit as H
from . import _stage_kit as S

TARGET_NAME = "hoplite"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 124.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Hoplite", "Biped", "Standard", "Medium", "Walk", ["soldier", "shield", "spear", "bronze"],
    "A Greek citizen soldier of the Classical Shore in the History dimension: a round bronze shield with a crimson lambda, "
    "a crested helmet and a long spear. He lifts the shield to his eyes first (a block), then thrusts over its rim.",
    "classical",
)

THIGH, SHIN = 13.0, 13.0
UPPER_ARM, FOREARM = 10.0, 10.0
TORSO = 19.0
SPEAR_FRONT, SPEAR_BACK = 46.0, 26.0
SHIELD_RX, SHIELD_RY = 13.0, 17.0


def _spear(pen: S.Pen, grip, angle: float) -> None:
    """The spear, held at `grip`, pointed at `angle` degrees (0 is forward)."""
    a = math.radians(angle)
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])

    def at(s: float, w: float = 0.0):
        return (grip[0] + d[0] * s + n[0] * w, grip[1] + d[1] * s + n[1] * w)

    pen.limb([at(-SPEAR_BACK), at(SPEAR_FRONT - 6.0)], 2.2, K.WOOD)
    pen.ink([at(-SPEAR_BACK + 2.0, -0.4), at(SPEAR_FRONT - 8.0, -0.4)], 0.5, K.shade(K.WOOD, 1.3))
    # The leaf-shaped head of bronze, and the spike at the butt.
    pen.poly([at(SPEAR_FRONT - 8.0, -1.4), at(SPEAR_FRONT - 3.0, -2.6), at(SPEAR_FRONT + 4.0, 0.0), at(SPEAR_FRONT - 3.0, 2.6),
              at(SPEAR_FRONT - 8.0, 1.4)], H.BRONZE)
    pen.ink([at(SPEAR_FRONT - 7.0), at(SPEAR_FRONT + 2.0)], 0.5, H.BRONZE_DARK)
    pen.poly([at(-SPEAR_BACK - 5.0), at(-SPEAR_BACK + 1.0, -1.5), at(-SPEAR_BACK + 1.0, 1.5)], H.BRONZE_DARK)


def _shield(pen: S.Pen, cx: float, cy: float, tilt: float, ring: float = 0.0) -> None:
    """The aspis, face on: a bronze bowl with a broad rim and a lambda."""
    pts = K.turn(K.ellipse_points(cx, cy, SHIELD_RX, SHIELD_RY, 32), cx, cy, tilt)
    pen.poly(pts, H.BRONZE)
    pen.poly(K.turn(K.ellipse_points(cx + 1.0, cy + 1.0, SHIELD_RX - 3.0, SHIELD_RY - 3.0, 28), cx, cy, tilt), H.BRONZE_LIGHT, body=False)
    pen.poly(K.turn(K.ellipse_points(cx + 1.6, cy + 1.6, SHIELD_RX - 4.2, SHIELD_RY - 4.2, 28), cx, cy, tilt), H.BRONZE, body=False)
    pen.poly(K.turn([(cx + 4.0, cy - 8.0), (cx + 10.0, cy - 2.0), (cx + 8.0, cy + 10.0), (cx + 2.0, cy + 13.0)], cx, cy, tilt),
             K.alpha(H.BRONZE_DARK, 0.6), body=False)
    # The lambda of Lacedaemon, in crimson.
    lam = [(cx - 6.0, cy + 9.0), (cx - 3.4, cy + 9.0), (cx, cy - 2.0), (cx + 3.4, cy + 9.0), (cx + 6.0, cy + 9.0), (cx + 1.4, cy - 9.0),
           (cx - 1.4, cy - 9.0)]
    pen.poly(K.turn(lam, cx, cy, tilt), H.CRIMSON, body=False)
    pen.ink(K.turn([(cx - 9.0, cy - 9.0), (cx - 6.0, cy - 12.0)], cx, cy, tilt), 1.0, K.alpha(K.WHITE, 0.8))
    if ring > 0.0:
        # It rings: a flash and lines out from where it was struck.
        pen.glow(cx + 6.0, cy - 4.0, 5.0 + 4.0 * ring, K.alpha(H.BRONZE_LIGHT, 0.8 * ring))
        for k in range(5):
            a = math.radians(-70.0 + k * 35.0)
            r0 = SHIELD_RY + 2.0
            pen.ink([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * (r0 + 6.0 * ring), cy + math.sin(a) * (r0 + 6.0 * ring))],
                    1.2, K.alpha(H.BRONZE_LIGHT, ring))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    hip_x, crouch, lean, bob = 48.0, 0.0, 0.0, 0.0
    near_foot, far_foot = (4.0, 0.0), (-4.0, 0.0)
    spear_grip, spear_angle = None, -92.0
    shield_up, shield_fwd, shield_tilt, ring = 0.0, 0.0, 0.0, 0.0
    cape, alarm, fade, rot = 0.0, False, 1.0, 0.0
    if anim == "idle":
        # At rest: the spear upright at his side, the shield on his arm.
        bob = 0.6 * math.sin(cyc)
        cape = 0.3 * math.sin(cyc + 1.0)
        spear_grip, spear_angle = "rest", -92.0 + 1.5 * math.sin(cyc)
    elif anim == "walk":
        # A march: knees up, the spear sloped, the shield on the arm.
        near_foot = (8.0 * math.sin(cyc), 5.0 * max(0.0, math.cos(cyc)))
        far_foot = (-8.0 * math.sin(cyc), 5.0 * max(0.0, -math.cos(cyc)))
        bob = -1.5 * abs(math.cos(cyc))
        lean, cape = 4.0, 0.6 + 0.3 * math.sin(cyc * 2.0)
        spear_grip, spear_angle = "rest", -80.0 + 2.0 * math.sin(cyc)
        shield_fwd = 1.0 * math.sin(cyc)
    elif anim == "notice":
        # He closes up: the shield to his eyes and the spear over its rim.
        u = min(1.0, t * 1.6)
        shield_up, crouch = 7.0 * u, 3.0 * u
        near_foot, far_foot = (10.0 * u, 0.0), (-8.0 * u, 0.0)
        spear_grip, spear_angle = ("over", 0.0 + 2.0 * u), -92.0 + 102.0 * u
        alarm = True
    elif anim == "windup":
        # Behind the shield: the spear drawn back, the body low.
        shield_up, crouch, lean = 8.0, 4.0 + 0.6 * math.sin(cyc * 2.0), -4.0
        near_foot, far_foot = (10.0, 0.0), (-10.0, 0.0)
        spear_grip, spear_angle = ("over", -10.0), 8.0 + 1.0 * math.sin(cyc * 2.0)
        cape = -0.3
    elif anim == "attack_side":
        # The thrust over the rim, with a step.
        u = min(1.0, t * 1.6)
        jab = math.sin(math.pi * min(1.0, t * 1.3))
        hip_x += 6.0 * u
        shield_up, crouch, lean = 6.0, 4.0, 6.0 * jab
        near_foot, far_foot = (12.0 + 2.0 * u, 0.0), (-10.0, 0.0)
        spear_grip, spear_angle = ("over", -10.0 + 22.0 * jab), 8.0 - 2.0 * jab
        cape = 0.8
    elif anim == "hit":
        # The blow rings on the shield and pushes him back.
        hip_x -= 4.0 * math.sin(math.pi * t)
        lean, shield_up, crouch = -10.0, 6.0, 3.0
        near_foot, far_foot = (8.0, 0.0), (-10.0, 0.0)
        spear_grip, spear_angle = ("over", -6.0), -30.0
        ring = 1.0 - t * 0.6
    elif anim == "death":
        # He reels, his knees go, and he falls on his back under his shield.
        fall = min(1.0, t / 0.8)
        crouch = 8.0 * min(1.0, fall * 2.0)
        hip_x += 36.0 * fall
        rot = -80.0 * min(1.0, max(0.0, (fall - 0.15) / 0.7)) ** 1.2
        lean = -8.0 * min(1.0, fall * 3.0)
        near_foot, far_foot = (6.0, 0.0), (-4.0, 0.0)
        spear_grip, spear_angle = ("over", -4.0), -30.0 + 110.0 * fall
        shield_up = 2.0
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    # A body on its back lies on its back, not under the floor.
    pen = S.Pen(f, (hip_x - 6.0, GROUND - 3.0), rot, (0.0, 10.0 * rot / 80.0))
    hip_y = GROUND - (THIGH + SHIN - 1.0) + crouch + bob
    lr = math.radians(lean)

    def up(p, length):
        return (p[0] + math.sin(lr) * length, p[1] - math.cos(lr) * length)

    def across(p, w):
        return (p[0] + math.cos(lr) * w, p[1] + math.sin(lr) * w)

    hip = (hip_x, hip_y)
    shoulder = up(hip, TORSO - 3.0)
    neck = up(hip, TORSO)
    head = up(neck, 8.0)
    hx, hy = head

    # The cloak behind: from the shoulders to the backs of the knees.
    flow = 8.0 + 5.0 * cape
    pen.poly([across(shoulder, -3.0), across(neck, 1.0), (hip_x - 4.0, hip_y + 12.0), (hip_x - 10.0 - flow, hip_y + 16.0), (hip_x - 8.0 - flow * 0.6, hip_y)],
             H.CRIMSON)
    pen.poly([across(shoulder, -3.0), (hip_x - 10.0 - flow, hip_y + 16.0), (hip_x - 8.0 - flow * 0.6, hip_y)], H.CRIMSON_DARK, body=False)

    def a_leg(spec, colour, greave):
        dx, lift = spec
        foot = (hip_x + dx, GROUND - 2.0 - lift)
        knee, ankle = H.leg(pen, hip, foot, THIGH, SHIN, 4.6, colour)
        # A bronze greave over the shin, and a sandal.
        pen.limb([H.lerp(knee, ankle, 0.1), H.lerp(knee, ankle, 0.85)], 5.0, greave)
        pen.ink([H.lerp(knee, ankle, 0.2), H.lerp(knee, ankle, 0.75)], 0.6, H.BRONZE_LIGHT)
        pen.poly([(ankle[0] - 2.5, ankle[1] - 1.0), (ankle[0] + 5.5, ankle[1] + 0.4), (ankle[0] + 5.5, ankle[1] + 2.2), (ankle[0] - 2.5, ankle[1] + 2.2)],
                 K.WOOD_DARK)

    a_leg(far_foot, H.SKIN_SHADE, H.BRONZE_DARK)

    # The body: a chiton skirt in strips, and a bronze cuirass.
    hb, hf = across(hip, -5.5), across(hip, 5.5)
    pen.poly([across(hip, -6.5), across(hip, 6.5), across(up(hip, -7.0), 7.5), across(up(hip, -7.0), -7.0)], H.CRIMSON)
    for w in (-4.0, -1.0, 2.0, 5.0):
        pen.ink([across(hip, w), across(up(hip, -6.5), w * 1.1)], 0.7, H.CRIMSON_DARK)
    sb, sf = across(shoulder, -6.5), across(shoulder, 6.5)
    nb, nf = across(neck, -3.0), across(neck, 3.0)
    pen.poly([hb, hf, across(up(hip, 8.0), 7.5), sf, nf, nb, sb], H.BRONZE)
    pen.poly([hb, across(hip, -2.0), across(shoulder, -3.0), sb], H.BRONZE_DARK, body=False)
    pen.ink([across(up(hip, 10.0), 1.0), across(up(hip, 10.0), 5.5)], 0.7, H.BRONZE_DARK)
    pen.ink([across(up(hip, 5.0), 0.0), across(up(hip, 5.0), 6.0)], 0.7, H.BRONZE_DARK)

    a_leg(near_foot, H.SKIN, H.BRONZE)

    # The head: a Corinthian helmet with a tall crest from front to back.
    tilt = lean * 0.4 + (10.0 if anim == "death" else 0.0)

    def Hd(x, y):
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    droop = 6.0 * min(1.0, t * 1.5) if anim == "death" else 0.0
    wave = 1.0 * math.sin(cyc + 0.5) if anim in ("idle", "walk") else (2.0 if alarm else 0.0)
    crest = [Hd(6.0, -7.0), Hd(7.0, -12.0), Hd(2.0, -17.0 - wave * 0.4 + droop), Hd(-6.0, -17.0 + droop), Hd(-12.0, -12.0 + droop * 1.2),
             Hd(-15.0, -4.0 + wave * 0.5 + droop), Hd(-11.0, -3.0 + droop * 0.5), Hd(-7.0, -8.0)]
    pen.poly(crest, H.CRIMSON)
    pen.ink([Hd(5.0, -13.0), Hd(0.0, -16.0 + droop), Hd(-8.0, -15.0 + droop), Hd(-13.0, -7.0 + droop)], 0.8, K.shade(H.CRIMSON, 1.35))
    pen.poly([Hd(-1.0, -7.0), Hd(1.0, -7.0), Hd(1.0, -10.0), Hd(-1.0, -10.0)], H.BRONZE_DARK)
    helm = [Hd(-8.0, 7.0), Hd(-8.5, -2.0), Hd(-5.0, -7.5), Hd(2.0, -8.5), Hd(7.0, -5.0), Hd(8.8, 0.0), Hd(9.0, 6.0), Hd(7.0, 9.0), Hd(2.0, 8.5),
            Hd(0.0, 3.0), Hd(-3.0, 4.0), Hd(-4.0, 8.0)]
    pen.poly(helm, H.BRONZE)
    pen.poly([Hd(-8.0, 7.0), Hd(-8.5, -2.0), Hd(-5.0, -7.5), Hd(-3.0, -6.0), Hd(-5.0, 4.0), Hd(-4.0, 8.0)], H.BRONZE_DARK, body=False)
    pen.ink([Hd(-4.0, -6.0), Hd(3.0, -6.6)], 0.7, H.BRONZE_LIGHT)
    # The T of the face opening: the eye slit and the gap down to the chin.
    pen.poly([Hd(2.5, -2.0), Hd(9.0, -2.2), Hd(9.0, 0.8), Hd(5.5, 1.0), Hd(5.5, 8.0), Hd(3.8, 8.0), Hd(3.8, 1.0), Hd(2.5, 0.8)], K.INK, body=False)
    ex, ey = Hd(6.8, -0.6)
    if anim == "death" and t > 0.4:
        pen.ink([(ex - 1.2, ey), (ex + 1.2, ey)], 0.8, K.WHITE)
    else:
        pen.dot(ex, ey, 0.9, K.WHITE)
    pen.ellipse(Hd(4.6, 7.0)[0], Hd(4.6, 7.0)[1], 1.2, 1.4, (60, 40, 30, 255), body=False)

    # The spear arm (the far arm), then the shield on the near arm, then the
    # spear and its hand over the rim.
    if spear_grip == "rest":
        # The butt of the spear stands on the ground.
        a = math.radians(spear_angle)
        grip = (hip_x + 13.0 + math.cos(a) * (SPEAR_BACK + 5.0), GROUND - 2.0 + math.sin(a) * (SPEAR_BACK + 5.0))
    else:
        dxg = spear_grip[1]
        grip = (shoulder[0] + 6.0 + dxg, shoulder[1] - 9.0)
    H.arm(pen, across(shoulder, -2.0), grip, UPPER_ARM, FOREARM, 3.8, H.SKIN_SHADE, elbow_out=1.0 if spear_grip == "rest" else -1.0)
    sx = hip_x + 7.0 + shield_fwd + (2.0 if shield_up else 0.0)
    sy = hip_y - 9.0 - shield_up
    _shield(pen, sx, sy, lean * 0.5 + (-6.0 if anim == "hit" else 0.0), ring)
    _spear(pen, grip, spear_angle)
    pen.ellipse(grip[0], grip[1], 2.4, 2.2, H.SKIN)
    if alarm:
        H.alarm_mark(f, hx + 14.0, hy - 26.0)
    return f.finish(outline=H.SEPIA_INK, width=1.4, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
