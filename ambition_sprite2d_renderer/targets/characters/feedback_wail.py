"""The Feedback Wail: the ghost of a loudspeaker of the Resonant Reach.

A speaker cabinet, pale and glowing as a ghost is, with brass corners. Its
foot is not a foot: the cabinet thins into the wavy hem of a ghost, and a
cable hangs from the hem as a tail, with a jack plug at its end. On its
front, two tweeters are its eyes and the big woofer cone is its mouth.

It floats and keeps its distance. Its windup is a breath: the cone draws
in and the cabinet swells. Its strike is the wail: the cone throws out, the
cabinet kicks back, and rings of cyan sound fly from its mouth. A hit gives
it static; at its death it squeals, stretches up and fades, and its plug
falls.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K

TARGET_NAME = "feedback_wail"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Feedback Wail", "Amorphous", "Small", "Light", "Float", ["music", "ghost", "floating", "glowing"],
    "The ghost of a loudspeaker in the Resonant Reach of the Art dimension: a pale cabinet with a cable for a tail. "
    "It floats, keeps its distance, draws in a breath, and shrieks rings of sound across the room.",
)

#: The ghost's colours: pale night blue, and the brass of the Reach.
GHOST = (196, 210, 248, 255)
GHOST_SHADE = (132, 146, 212, 255)
GHOST_DARK = (64, 70, 140, 255)
CONE = (40, 38, 78, 255)
CONE_RING = (92, 96, 160, 255)
BRASS = K.GOLD
BRASS_DARK = K.GOLD_DARK
CABLE = (44, 40, 62, 255)
SOUND = K.CYAN
SOUND_LIGHT = K.CYAN_LIGHT


def _arc(cx: float, cy: float, r: float, spread: float, count: int = 12) -> list:
    """An arc of a ring of sound that opens to the right."""
    return [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in (spread * (2.0 * k / (count - 1) - 1.0) for k in range(count))]


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"wail:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cx, cy = 58.0, 58.0
    lean, sx, sy, cone_out, eyes, fade = 0.0, 1.0, 1.0, 0.0, "open", 1.0
    tail_swing, tail_drop, glow, alarm, static = math.sin(cyc), 0.0, 0.35, False, 0.0
    rings: List[float] = []
    if anim == "idle":
        cy += 3.0 * math.sin(cyc)
        cone_out = 0.15 * math.sin(cyc * 2.0)
        rings = [((t * 2.0) % 1.0) * 0.45]
    elif anim == "walk":
        cy += 2.0 * math.sin(cyc * 2.0)
        lean, tail_swing = 10.0, 1.6 + 0.6 * math.sin(cyc)
    elif anim == "notice":
        cy -= 6.0 * math.sin(math.pi * t)
        sy = 1.0 + 0.08 * math.sin(math.pi * t)
        eyes, alarm, glow = "wide", True, 0.6
        static = 0.6 * (1.0 - t)
    elif anim == "windup":
        sx, sy = 1.10 + 0.02 * math.sin(cyc * 2.0), 1.06
        lean, cone_out, eyes, glow = -10.0, -0.6, "narrow", 0.6 + 0.3 * math.sin(cyc * 2.0)
        cx -= 3.0
    elif anim == "attack_side":
        shriek = math.sin(math.pi * min(1.0, t * 1.4))
        lean, cone_out, eyes, glow = -14.0 * shriek, 1.0 * shriek, "narrow", 1.0
        cx -= 6.0 * shriek
        sx = 1.0 + 0.08 * shriek
        rings = [t * 1.3 - 0.0, t * 1.3 - 0.25, t * 1.3 - 0.5]
    elif anim == "hit":
        sx, sy = 1.18, 0.84
        lean, eyes, static, glow = -10.0, "x", 1.0, 0.2
        cx -= 4.0 * math.sin(math.pi * t)
    elif anim == "death":
        sx, sy = 1.0 - 0.3 * t, 1.0 + 0.5 * t
        cy -= 10.0 * t
        eyes, glow, tail_drop = "x", 0.6 * (1.0 - t), t
        fade = 1.0 - max(0.0, t - 0.35) / 0.65
        rings = [0.3 + 0.5 * t] if t < 0.6 else []

    def at(points):
        """Points of the cabinet: scaled about its middle, then leaned."""
        return K.turn([(cx + (x - cx) * sx, cy + (y - cy) * sy) for x, y in points], cx, cy, lean)

    def pt(x, y):
        return at([(x, y)])[0]

    # The cabinet in 3/4: the front faces right; the side goes back to the left.
    fl, fr, top, foot = cx - 6.0, cx + 20.0, cy - 24.0, cy + 18.0
    bl, back_up = cx - 18.0, 5.0

    # The cable: from under the hem, down and back, with a plug at its end.
    root = pt(cx + 2.0, foot + 8.0)
    cable = [root]
    for k in range(1, 9):
        u = k / 8.0
        x = root[0] - 18.0 * u - 6.0 * tail_swing * u * u + 10.0 * u * u * (1.0 - tail_drop)
        y = root[1] + 28.0 * u + 8.0 * tail_drop * u
        cable.append((x + 3.0 * math.sin(cyc + u * 4.0) * (1.0 - tail_drop), min(y, 112.0)))
    f.limb(cable, 2.6, CABLE)
    px, py = cable[-1]
    dx, dy = cable[-1][0] - cable[-2][0], cable[-1][1] - cable[-2][1]
    d = math.hypot(dx, dy) or 1.0
    ux, uy = dx / d, dy / d
    # The jack plug: a brass barrel and a silver tip.
    f.limb([(px, py), (px + ux * 7.0, py + uy * 7.0)], 4.6, BRASS)
    f.limb([(px + ux * 7.0, py + uy * 7.0), (px + ux * 12.0, py + uy * 12.0)], 2.0, K.STEEL)
    f.ink([(px + ux * 2.0 - uy * 2.2, py + uy * 2.0 + ux * 2.2), (px + ux * 2.0 + uy * 2.2, py + uy * 2.0 - ux * 2.2)], 0.8, BRASS_DARK)

    # The hem: the foot of the cabinet thins into the wavy edge of a ghost.
    hem = []
    for k in range(9):
        u = k / 8.0
        x = fr - (fr - bl) * u
        wave = 5.0 * math.sin(cyc + u * 7.0) + (8.0 if k % 2 else 2.0)
        hem.append((x, foot + wave - back_up * max(0.0, (fl - x) / (fl - bl)) if x < fl else foot + wave))
    side = [(fl, top), (bl, top - back_up), (bl, foot - back_up)]
    front = [(fl, top), (fr, top), (fr, foot)]
    body = front + hem + side[1:2]
    f.poly(at(body), GHOST)
    # The side of the cabinet, in shade, and its top, lit.
    f.poly(at([(fl, top), (bl, top - back_up), (bl, foot - back_up + 4.0), (fl, foot + 4.0)]), GHOST_SHADE, body=False)
    f.poly(at([(bl, top - back_up), (fl - 4.0, top - back_up - 3.0), (fr - 4.0, top - 3.0), (fr, top), (fl, top)]), K.shade(GHOST, 1.35))
    f.ink(at([(fl, top), (fl, foot + 4.0)]), 0.9, GHOST_DARK)
    # Brass corners on the cabinet.
    for x, y in ((fr, top), (fl, top), (bl, top - back_up)):
        f.poly(at([(x - 2.6, y - 2.6), (x + 2.6, y - 2.6), (x + 2.6, y + 2.6), (x - 2.6, y + 2.6)]), BRASS)

    # The face on the front.
    mx = (fl + fr) / 2.0 + 0.6
    # Two tweeters: its eyes.
    for k, ox in enumerate((-6.2, 6.2)):
        ex, ey = mx + ox, top + 9.0
        ecx, ecy = pt(ex, ey)
        f.ellipse(ecx, ecy, 4.4, 4.4, BRASS, body=False)
        f.ellipse(ecx, ecy, 3.4, 3.4, CONE, body=False)
        if eyes == "x":
            for s in (-1.0, 1.0):
                f.ink([(ecx - 2.2, ecy - 2.2 * s), (ecx + 2.2, ecy + 2.2 * s)], 1.1, SOUND_LIGHT)
            continue
        big = 1.3 if eyes == "wide" else 1.0
        f.ellipse(ecx + 0.6, ecy, 1.6 * big, 1.9 * big, SOUND_LIGHT, body=False)
        f.glow(ecx + 0.6, ecy, 3.6 * big, K.alpha(SOUND, 0.55 * (0.5 + glow)))
        if eyes == "narrow":
            # A hard brow across the top of each eye: it means it.
            inner = 1.0 if ox < 0 else -1.0
            f.poly(at([(ex - 4.6, ey - 5.0 + (1.0 - inner) * 1.4), (ex + 4.6, ey - 5.0 + (1.0 + inner) * 1.4), (ex + 4.6, ey - 1.6 + inner * 0.8), (ex - 4.6, ey - 1.6 - inner * 0.8)]), GHOST, body=False)
            f.ink(at([(ex - 4.6, ey - 1.8 - inner * 0.8), (ex + 4.6, ey - 1.8 + inner * 0.8)]), 1.0, GHOST_DARK)
    # The woofer: its mouth. The cone goes in to breathe and out to wail.
    wx, wy = pt(mx, top + 27.0)
    r = 10.5 + 1.8 * cone_out
    f.ellipse(wx, wy, r + 1.8, r + 1.8, BRASS, body=False)
    f.ellipse(wx, wy, r, r, CONE_RING, body=False)
    f.ellipse(wx, wy, r * 0.78, r * 0.78, CONE, body=False)
    cap = 3.2 + 2.0 * cone_out
    f.ellipse(wx + 1.4 * cone_out, wy, max(1.6, cap), max(1.6, cap), K.shade(CONE_RING, 1.2), body=False)
    if cone_out > 0.3:
        f.glow(wx + 2.0, wy, r * 0.9, K.alpha(SOUND, 0.45 * cone_out))
    # The glow of a ghost round the cabinet.
    f.glow(cx + 2.0, cy - 2.0, 24.0 * sx, K.alpha(SOUND, 0.05 + 0.08 * glow))

    # Rings of sound from the mouth, out to the right.
    for u in rings:
        if 0.0 < u < 1.0:
            rr = 8.0 + 50.0 * u
            ring_x = min(wx + 4.0, 112.0 - rr)
            f.glow_line(_arc(ring_x, wy, rr, 0.75 - 0.25 * u), 3.0 - 1.0 * u, K.alpha(SOUND, 0.95 * (1.0 - u * 0.7)))
            f.glow_line(_arc(ring_x, wy, rr - 3.0, 0.65 - 0.25 * u), 1.0, K.alpha(SOUND_LIGHT, 0.7 * (1.0 - u)))
    # Static: little jags of sound round the cabinet.
    if static > 0.0:
        for k in range(6):
            a = rng.uniform(0.0, math.tau)
            x0, y0 = cx + 2.0 + math.cos(a) * 30.0, cy - 2.0 + math.sin(a) * 30.0
            f.glow_line([(x0, y0), (x0 + 3.0, y0 - 3.0), (x0 + 1.0, y0 + 1.0), (x0 + 5.0, y0 - 1.0)], 1.2, K.alpha(SOUND_LIGHT, static))
    if alarm:
        ax, ay = cx + 30.0, cy - 36.0
        f.limb([(ax, ay - 9.0), (ax, ay)], 2.6, SOUND)
        f.ellipse(ax, ay + 5.0, 1.7, 1.7, SOUND)
    return f.finish(outline=K.shade(GHOST_DARK, 0.55), width=1.4, glow_blur=2.6, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
