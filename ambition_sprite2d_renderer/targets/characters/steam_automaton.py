"""The Steam Automaton: a walking boiler of the Industrial Age.

A riveted iron boiler as big as a man stands on two piston legs. Its front
has two round portholes for eyes that glow with gaslight, a pressure gauge
over them, and a firebox door under them with the fire in its grate. A
black stack on its back puffs smoke; a brass whistle on its top screams
when it sees you. Its arms are pipes with a clamp for a hand.

It is slow and heavy. It chugs as it walks. Its windup builds pressure:
the needle goes into the red, steam leaks from its joints and the near arm
pulls back. Its strike is a piston punch: the arm shoots out and steam
bursts from its back. A hit pops a rivet and a jet of steam; at its death
its lid blows off, it sinks to its knees in a cloud of steam and goes cold.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_modern_kit as H
from . import _stage_kit as S

TARGET_NAME = "steam_automaton"
FRAME_SIZE = (192, 192)
ROWS = K.ENEMY_ROWS
GROUND = 187.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Steam Automaton", "Biped", "Large", "Heavy", "Walk", ["history", "industrial", "steam", "iron"],
    "A walking boiler of the Industrial Age in the History dimension: riveted iron on piston legs, porthole eyes, a "
    "firebox mouth, a smoking stack and a brass whistle. It is slow; it builds pressure and punches with a piston arm.",
)
ACTOR_METADATA["tags"] = ["enemy", "history"]

BOILER_W = 32.0
BOILER_H = 66.0
LEG = 44.0


def _rivets(pen, x0: float, x1: float, y: float, count: int) -> None:
    for k in range(count):
        x = x0 + (x1 - x0) * (k + 0.5) / count
        pen.dot(x, y, 1.0, H.IRON_DARK)
        pen.dot(x - 0.3, y - 0.3, 0.45, H.IRON_LIGHT)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"steam_automaton:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    flat = S.Pen(f)

    cx, sink, tilt, shake = 80.0, 0.0, 0.0, 0.0
    lift_n, lift_f, step_n, step_f = 0.0, 0.0, 0.0, 0.0
    eyes, gauge, fire, whistle, alarm, fade = 0.8, 0.3, 0.7, 0.0, False, 1.0
    smoke, punch, pull, leak, lid_off, cold = 0.4, 0.0, 0.0, 0.0, None, 0.0
    if anim == "idle":
        # It chugs: a shudder on its pistons, a puff from the stack.
        sink = 1.2 * max(0.0, math.sin(cyc * 2.0))
        shake = 0.6 * math.sin(cyc * 6.0)
        gauge = 0.35 + 0.05 * math.sin(cyc * 3.0)
        fire = 0.6 + 0.2 * math.sin(cyc * 2.0)
        smoke = t
    elif anim == "walk":
        # A heavy step on each half of the cycle: a foot rises and comes down.
        s = math.sin(cyc)
        lift_n, lift_f = max(0.0, s) * 7.0, max(0.0, -s) * 7.0
        step_n, step_f = 9.0 * math.cos(cyc), -9.0 * math.cos(cyc)
        sink = 2.5 * (1.0 - abs(s))
        tilt = 3.0 * s
        smoke = (t * 2.0) % 1.0
        fire = 0.7
    elif anim == "notice":
        whistle, eyes, alarm = math.sin(math.pi * min(1.0, t * 1.3)), 1.2, True
        sink = -2.0 * math.sin(math.pi * t)
        gauge = 0.5 + 0.2 * t
    elif anim == "windup":
        gauge = 0.85 + 0.05 * math.sin(cyc * 4.0)
        pull, leak, fire, eyes = 1.0, 1.0, 1.0, 1.2
        tilt, sink = -6.0, 3.0
        shake = 1.0 * math.sin(cyc * 8.0)
        whistle = 0.5 + 0.3 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        u = min(1.0, t * 1.8)
        punch = math.sin(math.pi * 0.5 * u) if t < 0.8 else max(0.0, 1.0 - (t - 0.8) * 3.0)
        pull = max(0.0, 1.0 - u * 3.0)
        tilt = -6.0 + 14.0 * punch
        cx += 6.0 * punch
        gauge = 0.85 - 0.5 * punch
        fire, eyes, leak = 1.0, 1.2, 0.4
        step_n = 8.0 * punch
    elif anim == "hit":
        tilt = -10.0 * math.sin(math.pi * min(1.0, t * 1.5))
        cx -= 4.0 * math.sin(math.pi * t)
        eyes, leak, fire = 0.3, 1.0, 0.5
        gauge = 0.95
    elif anim == "death":
        fall = min(1.0, t / 0.8)
        sink = 24.0 * fall * fall
        tilt = 10.0 * fall
        lid_off = fall
        eyes = max(0.0, 0.8 - fall)
        fire = max(0.0, 0.7 - fall)
        cold = fall
        gauge = 0.95 - 0.95 * fall
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    hip_y = GROUND - LEG + sink
    pen = S.Pen(f, (cx, hip_y), tilt, (shake, 0.0))
    top = hip_y - BOILER_H
    x0, x1 = cx - BOILER_W, cx + BOILER_W
    iron = K.shade(H.IRON, 1.0 - 0.25 * cold)

    # The stack behind the boiler, with its smoke.
    sx = cx - 14.0
    pen.poly([(sx - 5.0, top + 6.0), (sx + 5.0, top + 6.0), (sx + 5.0, top - 22.0), (sx - 5.0, top - 22.0)], H.SOOT)
    pen.poly([(sx - 8.0, top - 22.0), (sx + 8.0, top - 22.0), (sx + 6.0, top - 28.0), (sx - 6.0, top - 28.0)], H.SOOT)
    pen.ink([(sx + 2.6, top + 4.0), (sx + 2.6, top - 20.0)], 1.0, H.SOOT_LIGHT)
    if anim != "death":
        for k in range(3):
            u = (smoke + k / 3.0) % 1.0
            px, py = pen.at(sx - 4.0 - 10.0 * u, top - 32.0 - 24.0 * u)
            H.puff(f, px, max(12.0, py), 4.0 + 6.0 * u, K.alpha(H.SOOT_LIGHT, 0.85 * (1.0 - u * 0.7)), random.Random(f"smoke:{k}:{i}"), 5,
                   body=False)

    # The legs: an iron cylinder over a bright piston rod, a broad iron foot.
    def leg(side: float, lift: float, step: float, colour):
        hipx = cx + side * 13.0
        foot = (hipx + step, GROUND - 5.0 - lift)
        hp = pen.at(hipx, hip_y - 4.0)
        if anim == "death":
            # It sinks to its knees: the feet stay, the rods go into the cylinders.
            foot = (hipx + 4.0, GROUND - 5.0)
        knee = ((hp[0] + foot[0]) / 2.0, (hp[1] + foot[1]) / 2.0)
        flat.limb([hp, knee], 11.0, colour)
        flat.limb([knee, foot], 5.0, H.STEEL)
        flat.ink([(knee[0] - 3.0, knee[1] - 1.0), (knee[0] + 3.0, knee[1] - 1.0)], 1.0, H.IRON_DARK)
        flat.poly([(foot[0] - 10.0, foot[1] + 4.0), (foot[0] + 12.0, foot[1] + 4.0), (foot[0] + 9.0, foot[1] - 3.0), (foot[0] - 8.0, foot[1] - 3.0)], H.IRON_DARK)
        flat.dot(foot[0] + 6.0, foot[1], 1.0, H.IRON_LIGHT)
        flat.ellipse(hp[0], hp[1] + 2.0, 4.0, 3.0, H.IRON_DARK)

    leg(-1.0, lift_f, step_f, H.IRON_DARK)

    # The far arm: a pipe behind the boiler.
    fsh = pen.at(x0 + 4.0, top + 20.0)
    fhand = (fsh[0] - 6.0 + 3.0 * math.sin(cyc), fsh[1] + 24.0)
    if anim == "death":
        fhand = (fsh[0] - 4.0, fsh[1] + 30.0)
    fel, fhand = S.joint(fsh, fhand, 14.0, 14.0, 1.0)
    flat.limb([fsh, fel, fhand], 6.0, H.IRON_DARK)

    # The boiler: a riveted cylinder with a dome, darker on its far side.
    pen.poly([(x0, hip_y), (x1, hip_y), (x1, top), (x0, top)], iron)
    pen.poly([(x0, hip_y), (x0 + 12.0, hip_y), (x0 + 12.0, top), (x0, top)], K.shade(iron, 0.75), body=False)
    pen.poly([(x1 - 6.0, hip_y), (x1 - 2.0, hip_y), (x1 - 2.0, top), (x1 - 6.0, top)], K.shade(iron, 1.25), body=False)
    for y in (top + 4.0, top + 30.0, hip_y - 4.0):
        pen.ink([(x0, y), (x1, y)], 1.2, H.IRON_DARK)
        _rivets(pen, x0 + 2.0, x1 - 2.0, y - 2.6, 9)
    # The dome and its lid (the lid blows off at its death).
    pen.poly([(x0 + 2.0, top), (x1 - 2.0, top), (x1 - 8.0, top - 7.0), (x0 + 8.0, top - 7.0)], K.shade(iron, 0.9))
    lid = [(cx - 12.0, top - 7.0), (cx + 12.0, top - 7.0), (cx + 8.0, top - 11.0), (cx - 8.0, top - 11.0)]
    if lid_off is None:
        pen.poly(lid, H.BRASS)
        # The whistle on the lid.
        wx = cx + 6.0
        pen.poly([(wx - 2.0, top - 11.0), (wx + 2.0, top - 11.0), (wx + 2.4, top - 20.0), (wx - 2.4, top - 20.0)], H.BRASS)
        pen.poly([(wx - 3.4, top - 20.0), (wx + 3.4, top - 20.0), (wx + 2.0, top - 23.0), (wx - 2.0, top - 23.0)], H.BRASS_DARK)
        if whistle > 0.05:
            # A jet of steam straight up, and the shriek round it.
            jx, jy = pen.at(wx, top - 24.0)
            for k in range(3):
                H.puff(f, jx + rng.uniform(-2.0, 2.0), jy - 6.0 - 8.0 * k * whistle, 3.0 + 2.5 * k * whistle, H.STEAM, rng, 5, body=True)
            for k in range(3):
                a = math.radians(-40.0 + k * 40.0 - 90.0)
                r0 = 12.0 + 4.0 * whistle
                f.ink([(jx + math.cos(a) * r0, jy - 8.0 + math.sin(a) * r0), (jx + math.cos(a) * (r0 + 6.0), jy - 8.0 + math.sin(a) * (r0 + 6.0))],
                      1.4, H.GASLIGHT)
    else:
        # The lid flies up and spins away; the steam comes out of the top.
        lx, ly = pen.at(cx + 10.0 * lid_off, top - 11.0 - 40.0 * math.sin(math.pi * 0.5 * min(1.0, lid_off * 1.4)))
        lid2 = K.turn([(lx - 12.0, ly + 4.0), (lx + 12.0, ly + 4.0), (lx + 8.0, ly), (lx - 8.0, ly)], lx, ly, 260.0 * lid_off)
        flat.poly(lid2, H.BRASS)
        tx, ty = pen.at(cx, top - 10.0)
        for k in range(4):
            H.puff(f, tx - 8.0 + 6.0 * k + rng.uniform(-2.0, 2.0), ty - 6.0 - 6.0 * k * lid_off, 6.0 + 4.0 * lid_off, H.STEAM, rng, 5, body=True)

    # The pressure gauge.
    gx, gy = cx + 4.0, top + 14.0
    pen.ellipse(gx, gy, 7.0, 7.0, H.BRASS)
    pen.ellipse(gx, gy, 5.4, 5.4, H.PARCHMENT, body=False)
    pen.poly([(gx + math.cos(a) * 5.0, gy + math.sin(a) * 5.0) for a in [math.radians(d) for d in range(-40, 21, 10)]] + [(gx, gy)],
             (220, 60, 50, 255), body=False)
    na = math.radians(-220.0 + 240.0 * gauge)
    pen.ink([(gx, gy), (gx + math.cos(na) * 4.6, gy + math.sin(na) * 4.6)], 1.0, H.OUTLINE)
    pen.dot(gx, gy, 0.9, H.OUTLINE)
    # The porthole eyes: brass rims and gaslight behind the glass.
    for k, ex in enumerate((cx - 6.0, cx + 13.0)):
        ey = top + 28.0
        pen.ellipse(ex, ey, 6.0, 6.0, H.BRASS)
        glass = K.alpha(H.GASLIGHT, 1.0) if eyes > 0.1 else H.SOOT_LIGHT
        pen.ellipse(ex, ey, 4.2, 4.2, glass if eyes > 0.1 else H.SOOT, body=False)
        if eyes > 0.1:
            pen.ellipse(ex + 0.8, ey + 0.6, 2.0, 2.0, H.GASLIGHT_HOT, body=False)
            pen.glow(ex, ey, 6.0 * eyes, K.alpha(H.GASLIGHT, 0.5 * min(1.0, eyes)))
        if anim in ("windup", "attack_side"):
            # A hard brow: a plate bolted over the top of each porthole.
            b = [(ex - 6.6, ey - 3.6 - (2.0 if k == 0 else 0.0)), (ex + 6.6, ey - 3.6 - (0.0 if k == 0 else 2.0)), (ex + 6.6, ey - 7.0), (ex - 6.6, ey - 7.0)]
            pen.poly(b, H.IRON_DARK)
        if anim == "hit":
            pen.ink([(ex - 3.0, ey - 3.0), (ex + 3.0, ey + 3.0)], 1.2, H.OUTLINE)
    # The firebox: a door with a grate, and the fire behind it.
    fx, fy = cx + 4.0, hip_y - 14.0
    pen.poly([(fx - 11.0, fy - 7.0), (fx + 11.0, fy - 7.0), (fx + 11.0, fy + 7.0), (fx - 11.0, fy + 7.0)], H.IRON_DARK)
    if fire > 0.05:
        pen.poly([(fx - 9.0, fy - 5.0), (fx + 9.0, fy - 5.0), (fx + 9.0, fy + 5.0), (fx - 9.0, fy + 5.0)], K.alpha(H.FIRE, min(1.0, fire + 0.2)), body=False)
        pen.poly([(fx - 7.0, fy + 5.0), (fx - 3.0, fy - 2.0 - 2.0 * fire), (fx, fy + 1.0), (fx + 4.0, fy - 3.0 - 2.0 * fire), (fx + 7.0, fy + 5.0)],
                 K.alpha(H.GASLIGHT, min(1.0, fire + 0.2)), body=False)
        pen.glow(fx, fy, 10.0 * fire, K.alpha(H.FIRE, 0.45 * fire))
    else:
        pen.poly([(fx - 9.0, fy - 5.0), (fx + 9.0, fy - 5.0), (fx + 9.0, fy + 5.0), (fx - 9.0, fy + 5.0)], H.SOOT, body=False)
    for k in range(5):
        x = fx - 8.0 + k * 4.0
        pen.ink([(x, fy - 5.0), (x, fy + 5.0)], 1.0, H.IRON_DARK)

    if leak > 0.0:
        # Steam hisses from the seams.
        for k in range(3):
            px, py = pen.at(x1 + 2.0 if k % 2 else x0 - 2.0, top + 10.0 + k * 18.0)
            d = 1.0 if k % 2 else -1.0
            f.limb([(px, py), (px + d * 7.0 * leak, py - 3.0)], 2.4, K.alpha(H.STEAM, 0.9), body=False)
            f.ellipse(px + d * 9.0 * leak, py - 4.0, 3.0 * leak, 2.4 * leak, K.alpha(H.STEAM, 0.85), body=False)

    leg(1.0, lift_n, step_n, H.IRON)

    # The near arm: a pipe from a brass shoulder, and a piston that punches.
    nsh = pen.at(x1 + 1.0, top + 24.0)
    if punch > 0.0:
        a = math.radians(-6.0 + tilt)
        reach = 14.0 + 40.0 * punch
        el = (nsh[0] + 8.0, nsh[1] + 2.0)
        hand = (el[0] + math.cos(a) * reach, el[1] + math.sin(a) * reach)
        hand = (min(hand[0], 178.0), hand[1])
        flat.limb([nsh, el], 8.0, H.IRON)
        flat.limb([el, (el[0] + 12.0, el[1])], 9.0, H.IRON_DARK)
        flat.limb([(el[0] + 10.0, el[1]), hand], 4.0, H.STEEL)
        if punch > 0.6:
            # The burst of steam from its back, and lines of the blow.
            bx, by = pen.at(x0 - 4.0, top + 20.0)
            H.puff(f, max(14.0, bx - 6.0), by, 8.0 * punch, H.STEAM, rng, 6, body=True)
            for k in range(3):
                yy = hand[1] - 6.0 + k * 6.0
                f.ink([(hand[0] - 20.0, yy), (hand[0] - 30.0, yy)], 1.2, K.alpha(H.STEAM, 0.8))
    else:
        back = 10.0 * pull
        hand = (nsh[0] + 6.0 - back * 1.2, nsh[1] + 22.0 - back * 2.2 + 2.0 * math.sin(cyc) * (1.0 - pull))
        if anim == "hit":
            hand = (nsh[0] + 14.0, nsh[1] - 6.0)
        elif anim == "death":
            hand = (nsh[0] + 4.0, nsh[1] + 28.0)
        el, hand = S.joint(nsh, hand, 14.0, 14.0, 1.0)
        flat.limb([nsh, el, hand], 7.0, H.IRON)
        flat.ellipse(el[0], el[1], 4.0, 4.0, H.BRASS)
    # The clamp: two iron jaws.
    hx, hy = hand
    jaw = 3.0 + (3.0 if punch > 0.0 else 1.0)
    flat.poly([(hx - 2.0, hy - 5.0), (hx + 7.0, hy - jaw - 3.0), (hx + 9.0, hy - jaw), (hx + 2.0, hy - 1.0)], H.IRON_DARK)
    flat.poly([(hx - 2.0, hy + 5.0), (hx + 7.0, hy + jaw + 3.0), (hx + 9.0, hy + jaw), (hx + 2.0, hy + 1.0)], H.IRON_DARK)
    flat.ellipse(hx, hy, 4.4, 4.4, H.BRASS)
    pen.ellipse(x1 + 1.0, top + 24.0, 6.0, 6.0, H.BRASS)

    if anim == "hit":
        # A rivet pops out and steam jets from the hole.
        u = t
        rx, ry = pen.at(x1 - 4.0, top + 34.0)
        flat.ellipse(rx + 16.0 * u + 4.0, ry - 14.0 * math.sin(math.pi * min(1.0, u + 0.3)), 2.0, 2.0, H.IRON_LIGHT)
        f.limb([(rx, ry), (rx + 12.0, ry - 4.0)], 3.0, K.alpha(H.STEAM, 0.9), body=False)
        for k in range(5):
            a = math.tau * k / 5.0
            f.ink([(rx + math.cos(a) * 6.0, ry + math.sin(a) * 6.0), (rx + math.cos(a) * 10.0, ry + math.sin(a) * 10.0)], 1.2, H.GASLIGHT)
    if alarm:
        H.alarm_mark(f, cx + 32.0, top - 26.0)
    return H.finish(f, fade=fade, width=1.6)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
