"""The Brush Knight: a guardian of the Art dimension, armour with a brush.

A knight in white armour with a magenta plume and a magenta cape, who holds
a paint brush as long as a lance: a handle of pale wood, a gold ferrule,
and hairs heavy with magenta paint. The armour is empty, or nobody has
looked; the visor is shut and dark.

It is the noble enemy of the dimension: its blows are big and they show
first. Its windup lifts the brush back over its head; its strike sweeps
the brush down in front of it and leaves a stroke of paint in the air.
A hit knocks it back; at its death the armour falls in pieces and the
paint runs out of it.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K

TARGET_NAME = "brush_knight"
FRAME_SIZE = (168, 128)
ROWS = K.ENEMY_ROWS
GROUND = 125.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Brush Knight", "Biped", "Standard", "Medium", "Walk", ["armour", "brush", "paint"],
    "A guardian of the Art dimension: white armour with a magenta plume that wields a brush as long as a lance. Its "
    "blows are slow and clear: it lifts the brush back, then sweeps a stroke of paint across the ground in front.",
)


def _brush(f: K.Frame, grip, angle: float, paint_alpha: float = 1.0) -> tuple:
    """The brush, held at `grip`, pointed at `angle` degrees (0 is forward,
    negative is up). Returns the tip of its hairs."""
    a = math.radians(angle)
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])

    def at(s: float, w: float = 0.0):
        return (grip[0] + d[0] * s + n[0] * w, grip[1] + d[1] * s + n[1] * w)

    f.limb([at(-24.0), at(28.0)], 3.4, K.WOOD)
    f.ink([at(-22.0, -0.6), at(26.0, -0.6)], 0.6, K.shade(K.WOOD, 1.3))
    f.poly([at(27.0, -2.8), at(35.0, -3.4), at(35.0, 3.4), at(27.0, 2.8)], K.GOLD)
    f.ink([at(30.0, -3.0), at(30.0, 3.0)], 0.7, K.GOLD_DARK)
    hairs = [at(35.0, -4.0), at(42.0, -5.6), at(50.0, -3.6), at(56.0, 0.0), at(50.0, 3.6), at(42.0, 5.6), at(35.0, 4.0)]
    f.poly(hairs, (250, 240, 230, 255))
    f.poly([at(42.0, -5.2), at(50.0, -3.4), at(56.0, 0.0), at(50.0, 3.4), at(42.0, 5.2)], K.alpha(K.MAGENTA, paint_alpha))
    f.ink([at(44.0, -2.0), at(53.0, -0.6)], 0.6, K.alpha(K.MAGENTA_LIGHT, paint_alpha))
    return at(56.0)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    crouch, lean, stride, brush, cape, fade, apart, alarm = 0.0, 0.0, 0.0, -58.0, 0.0, 1.0, 0.0, False
    hip_x = 54.0
    if anim == "idle":
        crouch = 1.0 + 1.0 * math.sin(cyc)
        brush = -58.0 + 2.0 * math.sin(cyc)
        cape = 0.3 * math.sin(cyc)
    elif anim == "walk":
        stride, crouch, lean, cape = math.sin(cyc), 1.5 * abs(math.cos(cyc)), 4.0, 0.6 + 0.3 * math.sin(cyc * 2.0)
        brush = -52.0 + 4.0 * math.sin(cyc)
    elif anim == "notice":
        brush, lean, alarm = -70.0, -4.0, True
        crouch = -2.0 * math.sin(math.pi * t)
    elif anim == "windup":
        brush, lean, crouch = -150.0 + 2.0 * math.sin(cyc * 2.0), -10.0, 6.0
        stride, cape = 0.5, -0.4
    elif anim == "attack_side":
        swing = min(1.0, t * 1.4)
        brush = -150.0 + 175.0 * (1.0 - (1.0 - swing) ** 2)
        lean, crouch, stride, cape = 14.0 * math.sin(math.pi * swing), 6.0, 0.8, 0.9
        hip_x += 8.0 * swing
    elif anim == "hit":
        lean, brush, crouch = -16.0, -80.0, 2.0
        hip_x -= 4.0 * math.sin(math.pi * t)
    elif anim == "death":
        apart, brush, crouch = t, -10.0 - 20.0 * t, 10.0 * t
        fade = 1.0 - max(0.0, t - 0.65) / 0.35

    hip_y = GROUND - 36.0 + crouch
    lean_r = math.radians(lean)

    def up(x, y, length):
        return (x + math.sin(lean_r) * length, y - math.cos(lean_r) * length)

    neck = up(hip_x, hip_y, 30.0)
    head = up(neck[0], neck[1] + apart * 18.0, 12.0)
    head = (head[0] + apart * 10.0, head[1] + apart * 30.0)

    # The cape behind: from the shoulders to behind the knees, in the wind.
    flow = 10.0 + 6.0 * cape
    f.poly([(neck[0] - 4.0, neck[1] + 2.0), (neck[0] + 2.0, neck[1] + 4.0), (hip_x - 6.0, hip_y + 14.0 + apart * 10.0), (hip_x - 14.0 - flow, hip_y + 18.0 + apart * 12.0), (hip_x - 10.0 - flow * 0.6, hip_y + 4.0)], K.MAGENTA)
    f.poly([(neck[0] - 4.0, neck[1] + 2.0), (hip_x - 14.0 - flow, hip_y + 18.0 + apart * 12.0), (hip_x - 10.0 - flow * 0.6, hip_y + 4.0)], K.shade(K.MAGENTA, 0.7), body=False)
    # The far leg, in shade, then the near leg.
    for side, colour in ((-1.0, K.STEEL_SHADE), (1.0, K.STEEL)):
        swing = stride * side
        foot = (hip_x + 10.0 * swing + side * 2.0, GROUND - 2.0)
        knee = (hip_x + 6.0 * swing + 4.0 + side, hip_y + 17.0 - crouch * 0.3)
        if apart:
            knee = (knee[0], knee[1] + apart * 4.0)
        f.limb([(hip_x, hip_y), knee], 7.0, colour)
        f.limb([knee, foot], 6.0, colour)
        f.poly([(foot[0] - 4.0, GROUND), (foot[0] + 8.0, GROUND), (foot[0] + 6.0, GROUND - 5.0), (foot[0] - 3.0, GROUND - 6.0)], K.shade(colour, 0.85))
        f.ellipse(knee[0], knee[1], 4.0, 3.6, K.shade(colour, 1.15))
    # The body: a breastplate and a skirt of plates.
    sx, sy = hip_x, hip_y + apart * 14.0
    torso = K.turn([(sx - 9.0, sy + 2.0), (sx + 10.0, sy + 2.0), (sx + 12.0, sy - 18.0), (sx + 8.0, sy - 30.0), (sx - 8.0, sy - 30.0), (sx - 11.0, sy - 16.0)], sx, sy, lean)
    f.poly(torso, K.STEEL)
    f.poly(K.turn([(sx - 11.0, sy - 16.0), (sx - 8.0, sy - 30.0), (sx - 2.0, sy - 30.0), (sx - 4.0, sy + 2.0), (sx - 9.0, sy + 2.0)], sx, sy, lean), K.STEEL_SHADE, body=False)
    f.poly(K.turn([(sx - 10.0, sy), (sx + 11.0, sy), (sx + 13.0, sy + 8.0), (sx - 12.0, sy + 8.0)], sx, sy, lean), K.shade(K.STEEL, 0.9))
    f.ink(K.turn([(sx - 11.0, sy + 4.0), (sx + 12.0, sy + 4.0)], sx, sy, lean), 0.7, K.STEEL_SHADE)
    # A swirl of paint on the breastplate: the emblem of the dimension.
    ex, ey = K.turn([(sx + 1.0, sy - 16.0)], sx, sy, lean)[0]
    f.ellipse(ex, ey, 4.6, 4.6, K.MAGENTA, body=False)
    f.ellipse(ex + 0.8, ey - 0.6, 2.6, 2.6, K.CYAN, body=False)
    f.ellipse(ex + 1.2, ey - 1.0, 1.0, 1.0, K.YELLOW, body=False)
    # The head: a bucket helm with a dark visor and a plume.
    hx, hy = head
    helm = [(hx - 8.0, hy + 7.0), (hx + 9.0, hy + 7.0), (hx + 10.0, hy - 4.0), (hx + 6.0, hy - 10.0), (hx - 6.0, hy - 10.0), (hx - 9.0, hy - 4.0)]
    helm = K.turn(helm, hx, hy, lean + apart * 60.0)
    plume_wave = 3.0 * math.sin(cyc + 1.0) if anim in ("idle", "walk") else (6.0 if alarm else 0.0)
    plume = K.turn([(hx - 2.0, hy - 9.0), (hx + 3.0, hy - 13.0), (hx - 2.0, hy - 20.0 - plume_wave * 0.5), (hx - 14.0, hy - 16.0 - plume_wave), (hx - 22.0, hy - 8.0 + plume_wave * 0.3), (hx - 10.0, hy - 9.0)], hx, hy, lean + apart * 60.0)
    f.poly(plume, K.MAGENTA)
    f.ink(plume[1:4], 0.8, K.MAGENTA_LIGHT)
    f.poly(helm, K.STEEL)
    visor = K.turn([(hx + 1.0, hy - 3.0), (hx + 10.0, hy - 3.0), (hx + 10.0, hy + 1.0), (hx + 1.0, hy + 1.0)], hx, hy, lean + apart * 60.0)
    f.poly(visor, K.INK, body=False)
    for k in range(3):
        f.ink(K.turn([(hx + 3.0 + k * 2.6, hy - 2.0), (hx + 3.0 + k * 2.6, hy)], hx, hy, lean + apart * 60.0), 0.6, K.alpha(K.MAGENTA_LIGHT, 0.8))

    # The arms and the brush: the hands on the handle, the near hand in front.
    shoulder = K.turn([(sx + 2.0, sy - 26.0)], sx, sy, lean)[0]
    grip = (shoulder[0] + 10.0 + math.cos(math.radians(brush)) * 4.0, shoulder[1] + 10.0 + math.sin(math.radians(brush)) * 6.0)
    if apart:
        grip = (grip[0] + 18.0 * apart, GROUND - 9.0 - 30.0 * (1.0 - apart))
    if anim == "attack_side" and 0.25 < t < 0.85:
        # The stroke of paint the sweep leaves in the air.
        arc = []
        for k in range(12):
            a = math.radians(-120.0 + 140.0 * k / 11.0)
            arc.append((grip[0] + math.cos(a) * 54.0, grip[1] + math.sin(a) * 50.0))
        f.glow_line(arc, 5.0, K.alpha(K.MAGENTA, 0.75 * (1.0 - abs(t - 0.55) / 0.3)))
    tip = _brush(f, grip, brush, paint_alpha=1.0 - apart)
    f.limb([shoulder, ((shoulder[0] + grip[0]) / 2.0, (shoulder[1] + grip[1]) / 2.0 + 3.0), grip], 5.0, K.STEEL)
    f.ellipse(grip[0], grip[1], 3.4, 3.4, K.STEEL_SHADE)
    if alarm:
        f.limb([(hx + 16.0, hy - 22.0), (hx + 16.0, hy - 14.0)], 2.6, K.MAGENTA)
        f.ellipse(hx + 16.0, hy - 9.5, 1.7, 1.7, K.MAGENTA)
    if anim == "death" and apart > 0.3:
        f.ellipse(hip_x + 6.0, GROUND - 3.0, 18.0 * apart, 2.0, K.alpha(K.MAGENTA, 1.0))
    del tip
    return f.finish(width=1.6, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
