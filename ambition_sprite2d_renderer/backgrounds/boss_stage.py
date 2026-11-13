"""The scene of the Boss dimension: the bossofthegame's last show
(`docs/planning/game/final-boss.md`).

``boss_stage`` is a stadium at night with a rock show in it. The beams of
the light rig cross over the smoke in the dark. Far off, the stands go up in
tiers, full of people with their lights held up, and a wall of LEDs over the
stage shows the show's meter. Near are the stage's scaffold towers with the speaker
arrays hung on them and a truss of lamps across the top. The crowd's raised
hands are in front (`foreground`).

The colours are the show's: the black of the stage, the magenta and cyan of
the lamps, and the red and gold of Full Stack, so the fight in front of it
reads as part of the show. Bright detail is far off or at the edges: the
middle of the view, where the giant stands, stays dark.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .parts import HORIZON, fog, haze, lamps, solid, vignette

SHOW = {
    "top": (6, 4, 16),
    "deep": (20, 10, 40),
    "violet": (64, 28, 104),
    "magenta": (236, 48, 150),
    "cyan": (70, 220, 255),
    "amber": (255, 176, 70),
    "red": (214, 34, 54),
    "gold": (242, 192, 84),
    "spot": (255, 246, 230),
    "crowd": (16, 10, 28),
    "far": (48, 26, 76),
    "near": (12, 8, 20),
    "near_light": (96, 52, 124),
}

#: Where the beams of the rig come from (the truss over the stage) and the
#: colour of each, in turn.
BEAM_COLOURS = ("magenta", "cyan", "amber", "magenta", "spot", "cyan", "amber")


def _array(pen: Pen, u: float, top: float, boxes: int, w: float, h: float, curl: float) -> list[tuple[float, float, float, float]]:
    """A line array of speakers hung from `top`: `boxes` cabinets, each a
    little more turned down than the one over it (the J of a hung array).
    Returns the faces (u0, v0, u1, v1) of the cabinets."""
    faces = []
    v = top
    shift = 0.0
    for k in range(boxes):
        bend = curl * (k / max(1, boxes - 1)) ** 2
        pen.poly([(u - w + shift, v), (u + w + shift, v), (u + w + shift + bend * 0.4, v + h), (u - w + shift - bend * 0.4, v + h)])
        faces.append((u - w * 0.8 + shift, v + h * 0.2, u + w * 0.8 + shift, v + h * 0.8))
        v += h * 1.04
        shift += bend * 0.2
    # The bumper it hangs from, and its chain to the truss.
    pen.rect(u - w * 1.1, top - h * 0.4, u + w * 1.1, top - h * 0.1)
    pen.line([(u, 0.0), (u, top - h * 0.4)], 0.0016)
    return faces


def boss_stage(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = SHOW
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.30, p["deep"]), (HORIZON - 0.04, p["violet"]), (HORIZON + 0.06, mix(p["violet"], p["magenta"], 0.25)), (0.82, p["deep"]), (1.0, p["top"])]))
        # The smoke of the show, lit from below.
        smoke = a.noise("show smoke", cells=3.0, octaves=5, stretch=2.5)
        a.light(layer, smoothstep(0.45, 0.85, smoke) * smoothstep(0.15, HORIZON, a.v), mix(p["violet"], p["magenta"], 0.4), 0.45)
        # The beams of the rig: from points along the top of the stage out
        # and up into the smoke, each its own colour.
        rng = a.rand("show beams")
        for k, name in enumerate(BEAM_COLOURS):
            beams, pen = a.drawing()
            src = (0.08 + k * 0.14 + rng.uniform(-0.02, 0.02), HORIZON + 0.02)
            angle = -90.0 + (k - 3) * 13.0 + rng.uniform(-5.0, 5.0)
            spread = rng.uniform(1.4, 2.4)
            far = 0.95
            dx0, dy0 = math.cos(math.radians(angle - spread)), math.sin(math.radians(angle - spread))
            dx1, dy1 = math.cos(math.radians(angle + spread)), math.sin(math.radians(angle + spread))
            pen.poly([src, (src[0] + dx0 * far, src[1] + dy0 * far), (src[0] + dx1 * far, src[1] + dy1 * far)])
            beam = a.mask_of(beams, blur=5.0) * smoothstep(0.0, 0.5, a.v) * (0.55 + 0.45 * smoke)
            a.light(layer, beam, p[name], 0.42)
        # A warm glow where the stage is, under the horizon.
        a.light(layer, a.spot(0.5, HORIZON + 0.03, 0.42, 1.8, squash=2.4), p["magenta"], 0.28)
        a.light(layer, a.spot(0.5, HORIZON + 0.05, 0.22, 2.0, squash=2.0), p["amber"], 0.25)
        a.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("stands")
        # The stands: tiers that go up from the floor to each side, a bowl
        # whose far rim is under the horizon in the middle and higher out at
        # the sides.
        def rim(u: np.ndarray) -> np.ndarray:
            return HORIZON + 0.04 - 0.17 * ((u - 0.5) / 0.5) ** 2
        stands = (a.v > rim(a.u)).astype(np.float32)
        layer = solid(a, stands, mix(p["far"], p["violet"], 0.3), p["crowd"], HORIZON - 0.2, HORIZON + 0.1, "stands", 0.06)
        # The tiers' lines.
        for k in range(1, 9):
            line = np.abs(a.v - (rim(a.u) + k * 0.024)) < 0.0012
            a.shade(layer, line.astype(np.float32) * stands, 0.35)
        # The crowd's lights: phones and lighters, white and warm, thicker
        # low down.
        crowd, pen = a.drawing()
        warm, warm_pen = a.drawing()
        for _ in range(900):
            u = rng.random()
            v = float(rim(np.array(u))) + rng.uniform(0.06, 0.55) ** 1.6
            r = rng.uniform(0.0007, 0.0016)
            (warm_pen if rng.random() < 0.35 else pen).ellipse(u, v, r)
        a.light(layer, a.mask_of(crowd, blur=0.4) * stands, p["spot"], 0.50)
        a.light(layer, a.mask_of(warm, blur=0.4) * stands, p["amber"], 0.55)
        # The LED wall over the stage, in the middle of the bowl: dark glass
        # with FINAL TOUR on it in lamps, and the frame of the stage roof.
        wall_u0, wall_u1, wall_v0, wall_v1 = 0.35, 0.65, HORIZON - 0.25, HORIZON - 0.13
        frame, frame_pen = a.drawing()
        frame_pen.rect(wall_u0 - 0.012, wall_v0 - 0.016, wall_u1 + 0.012, wall_v1 + 0.010)
        for u in (wall_u0 - 0.010, wall_u1 + 0.004):
            frame_pen.rect(u, wall_v1, u + 0.006, HORIZON + 0.06)
        frame_mask = a.mask_of(frame, blur=0.3)
        a.put(layer, frame_mask, scale(p["crowd"], 1.2))
        glass = ((a.u > wall_u0) & (a.u < wall_u1) & (a.v > wall_v0) & (a.v < wall_v1)).astype(np.float32)
        a.put(layer, glass, mix(p["deep"], p["violet"], 0.25))
        # The LED grid: faint lines in the glass.
        grid = ((np.sin(a.u * math.tau * 220.0) > 0.85) | (np.sin(a.v * math.tau * 220.0) > 0.85)).astype(np.float32)
        a.shade(layer, grid * glass, 0.25)
        # On it, the show's meter: bars of lamps that rise from the middle
        # out, magenta low and amber at the top, the same each side. The
        # game draws some rooms' backdrops mirrored (`parallax.rs`
        # `room_mirrors_its_backdrop`), so nothing on it is writing: the
        # tour's name is a sign in the room.
        bars, bar_pen = a.drawing()
        hot, hot_pen = a.drawing()
        rng_bars = a.rand("led meter")
        count = 13
        pitch = (wall_u1 - wall_u0 - 0.04) / (2 * count)
        heights = [0.35 + 0.65 * abs(math.sin(1.7 * k + 0.4)) * (1.0 - 0.5 * k / count) for k in range(count)]
        foot = wall_v1 - 0.016
        tall = wall_v1 - wall_v0 - 0.03
        for k, h in enumerate(heights):
            lamps_up = int(h * 9)
            for side in (-1.0, 1.0):
                u = 0.5 + side * (k + 0.5) * pitch
                for r in range(lamps_up):
                    v = foot - (r + 0.5) * tall / 9.0
                    (hot_pen if r >= 6 else bar_pen).rect(u - pitch * 0.36, v - tall / 22.0, u + pitch * 0.36, v + tall / 22.0)
        del rng_bars
        lit = a.mask_of(bars, blur=0.3)
        top = a.mask_of(hot, blur=0.3)
        a.glow(layer, a.mask_of(bars, blur=4.0) * glass, p["magenta"], 0.35)
        a.put(layer, lit, mix(p["magenta"], p["spot"], 0.2))
        a.put(layer, top, p["amber"])
        a.put(layer, ((np.abs(a.v - (foot + 0.006)) < 0.0012) & (a.u > wall_u0 + 0.02) & (a.u < wall_u1 - 0.02)).astype(np.float32), p["gold"], 0.8)
        a.light(layer, a.rim(frame_mask, 0.0, 0.003, 0.5) * frame_mask, p["magenta"], 0.4)
        haze(a, layer, p["violet"], 0.16, HORIZON + 0.08)
        return layer
    if layer_key == "near_background":
        image, pen = a.drawing()
        # The deck of the stage at the bottom.
        pen.rect(0.0, 0.705, 1.0, 1.0)
        # The scaffold towers at each side, with their cross braces.
        towers, tower_pen = a.drawing()
        for u0, u1 in ((0.02, 0.10), (0.90, 0.98)):
            for u in (u0, u1):
                tower_pen.rect(u - 0.003, 0.0, u + 0.003, 0.71)
            v = 0.05
            while v < 0.70:
                tower_pen.line([(u0, v), (u1, v + 0.06)], 0.0018)
                tower_pen.line([(u1, v), (u0, v + 0.06)], 0.0018)
                tower_pen.rect(u0, v - 0.0015, u1, v + 0.0015)
                v += 0.06
        # The truss across the top: two chords and their zig-zag.
        truss, truss_pen = a.drawing()
        top0, top1 = 0.235, 0.265
        truss_pen.rect(0.0, top0 - 0.0025, 1.0, top0 + 0.0025)
        truss_pen.rect(0.0, top1 - 0.0025, 1.0, top1 + 0.0025)
        u = 0.0
        while u < 1.0:
            truss_pen.line([(u, top0), (u + 0.015, top1), (u + 0.03, top0)], 0.0016)
            u += 0.03
        # Speaker arrays hung inside the towers, turned in to the stage.
        arrays, array_pen = a.drawing()
        faces = []
        faces += _array(array_pen, 0.16, 0.30, 7, 0.032, 0.034, 0.02)
        faces += _array(array_pen, 0.84, 0.30, 7, 0.032, 0.034, -0.02)
        # Lamps on the truss: cans that hang under it.
        cans, can_pen = a.drawing()
        lenses = []
        for k in range(14):
            u = 0.035 + k * 0.071
            can_pen.rect(u - 0.006, top1 + 0.004, u + 0.006, top1 + 0.022)
            lenses.append((u, top1 + 0.024, 0.0045))
        mask = np.maximum.reduce([a.mask_of(image), a.mask_of(towers), a.mask_of(truss), a.mask_of(arrays), a.mask_of(cans)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.35), p["near"], 0.25, 0.75, "near", 0.08)
        # The speaker faces: a grille, a shade darker, with a line of light.
        grille, grille_pen = a.drawing()
        for u0, v0, u1, v1 in faces:
            grille_pen.rect(u0, v0, u1, v1)
        g = a.mask_of(grille, blur=0.3)
        a.shade(layer, g, 0.45)
        a.light(layer, g * (np.sin(a.v * math.tau * 400.0) > 0.6), p["near_light"], 0.25)
        # The towers are steel: a light on the edge toward the stage.
        tw = a.mask_of(towers)
        a.light(layer, (a.rim(tw, 0.002, 0.0, 0.3) * (a.u < 0.5) + a.rim(tw, -0.002, 0.0, 0.3) * (a.u > 0.5)) * tw, p["near_light"], 0.6)
        # The deck: boards, its lip, and the light of the stage on it.
        deck = (a.v > 0.705).astype(np.float32)
        a.shade(layer, (np.sin(a.u * math.tau * 70.0) > 0.94) * deck, 0.3)
        a.put(layer, a.band(0.707, 0.0025, 1.0), mix(p["magenta"], p["near"], 0.35))
        a.light(layer, deck * a.spot(0.5, 0.705, 0.45, 2.0, squash=2.5), p["magenta"], 0.25)
        lamps(a, layer, lenses[::2], p["magenta"], halo=3.0, strength=0.65)
        lamps(a, layer, lenses[1::2], p["cyan"], halo=3.0, strength=0.65)
        # A strobe at the top of each tower.
        lamps(a, layer, [(0.06, 0.04, 0.005), (0.94, 0.04, 0.005)], p["spot"], halo=4.0, strength=0.8)
        a.light(layer, a.rim(mask, -0.003, 0.003, 0.4) * mask, p["near_light"], 0.25)
        return layer
    layer = a.blank()
    # The beams, faint, over the play: two that cross over the middle.
    beams, pen = a.drawing()
    pen.poly([(0.10, 0.18), (0.14, 0.17), (0.60, 0.78), (0.46, 0.80)])
    pen.poly([(0.90, 0.18), (0.86, 0.17), (0.40, 0.78), (0.54, 0.80)])
    a.put(layer, a.mask_of(beams, blur=12.0), p["magenta"], 0.07)
    a.put(layer, fog(a, "stage smoke", 0.72, 0.12), p["violet"], 0.20)
    vignette(a, layer, p["near"], 0.38)
    return layer


def crowd_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The crowd in front of the stage: heads, and hands held up, some with
    a phone lit in them, standing from below. Nothing hangs from above: the
    Boss is up there."""
    rng = art_.rand("crowd foreground")
    bottom = 0.628
    u = -0.01
    while u < 1.01:
        w = rng.uniform(0.022, 0.034)
        top = bottom + rng.uniform(0.020, 0.034)
        pen.ellipse(u, top, w * 0.42, w * 0.5)
        pen.rect(u - w * 0.6, top + w * 0.3, u + w * 0.6, 1.0)
        if rng.random() < 0.28:
            # A hand held up: an arm from the shoulder, and a phone in some.
            side = rng.choice((-1.0, 1.0))
            hand = (u + side * w * 0.5 + rng.uniform(-0.004, 0.004), bottom - rng.uniform(0.004, 0.016))
            pen.line([(u + side * w * 0.45, top + w * 0.35), hand], 0.0042)
            pen.ellipse(*hand, 0.0042)
            if rng.random() < 0.6:
                pen.rect(hand[0] - 0.0028, hand[1] - 0.012, hand[0] + 0.0028, hand[1] - 0.002)
                layer_lights.append((hand[0], hand[1] - 0.007, 0.0026, SHOW["spot"]))
        u += w * rng.uniform(0.9, 1.3)
