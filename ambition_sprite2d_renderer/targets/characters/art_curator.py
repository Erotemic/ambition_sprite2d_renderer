"""The Curator: the keeper of the Art dimension.

A small figure in a cloak and a hat with a wide brim, whose face is in the
shade of the hat: dark, with two lit eyes and nothing else that shows. The
hat is yellow with a long magenta feather; the cloak is white with bands of
magenta and the swirl of the dimension on it. The Curator holds a staff of
gold with a swirl of the three primaries at its top, which glows.

The Curator keeps the plaza's gate open. Kind, and hard to read.

Rows: ``idle`` (the staff's light turns), ``walk``, ``talk`` (the hand
that is free moves; the brim nods), ``hit`` and ``death`` (the cloak falls
empty and the hat on top of it).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K

TARGET_NAME = "art_curator"
FRAME_SIZE = (128, 128)
GROUND = 125.0
ROWS: List[Tuple[str, int, int]] = [("idle", 6, 160), ("walk", 8, 110), ("talk", 6, 120), ("hit", 3, 90), ("death", 6, 120)]
LOOPS = {"idle", "walk", "talk"}

ACTOR_METADATA = {
    "actor": {"character_id": "npc_art_curator", "display_name": "The Curator"},
    "body": {"body_plan": "Biped", "body_kind": "Standard", "mass_class": "Light", "traits": ["cloak", "hat", "staff"], "locomotion_hint": "Walk"},
    "visual": {"default_pose": "idle", "portrait": {"animation": "talk", "frame": 1}},
    "tags": ["townsfolk", "art", "peaceful"],
    "authoring_description": (
        "The keeper of the Art dimension: a small figure in a white cloak and a wide yellow hat with a magenta feather, "
        "whose face is dark under the brim but for two lit eyes. Holds a gold staff with a swirl of paint at its top. "
        "An original character; it parodies no one."
    ),
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "dialogue.talk": {"animation": "talk", "events": []},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
}

CLOAK = (250, 244, 248, 255)
CLOAK_SHADE = (212, 196, 222, 255)
HAT = (255, 206, 60, 255)
HAT_SHADE = (214, 150, 30, 255)
FACE = (26, 16, 44, 255)
EYES = (255, 246, 200, 255)


def _swirl(f: K.Frame, cx: float, cy: float, r: float, turn: float, light: float) -> None:
    """The swirl of the three primaries: three arms that wind into the middle."""
    f.ellipse(cx, cy, r, r, K.WHITE)
    for k, colour in enumerate((K.MAGENTA, K.CYAN, K.YELLOW)):
        pts = []
        for s in range(12):
            u = s / 11.0
            a = turn + k * math.tau / 3.0 + u * 2.4
            rr = r * (0.95 - 0.8 * u)
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        f.ink(pts, r * 0.32, colour)
    f.glow(cx, cy, r * 1.8, K.alpha(K.WHITE, 0.35 * light))
    f.glow(cx, cy, r * 1.1, K.alpha(K.MAGENTA_LIGHT, 0.35 * light))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    bob, step, nod, hand, lean, fall, fade, light = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.8
    cx = 58.0
    if anim == "idle":
        bob, light = 1.0 * math.sin(cyc), 0.7 + 0.3 * math.sin(cyc)
    elif anim == "walk":
        bob, step, lean = -1.5 * abs(math.sin(cyc)), math.sin(cyc), 3.0
    elif anim == "talk":
        nod, hand = 2.0 * math.sin(cyc * 2.0), 0.5 + 0.5 * math.sin(cyc)
    elif anim == "hit":
        lean, nod = -12.0, -3.0
    elif anim == "death":
        fall, light = t, 1.0 - t
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    top = GROUND - 66.0 + bob + fall * 40.0
    hem = GROUND - 3.0
    # The staff, held in the far hand, in front of the cloak's far side.
    staff_x = cx + 20.0 + lean * 0.3
    staff_top = GROUND - 92.0 + bob + fall * 70.0
    staff_lean = fall * 70.0
    staff = K.turn([(staff_x, GROUND - 1.0), (staff_x, staff_top)], staff_x, GROUND - 1.0, staff_lean)
    f.limb(staff, 2.8, K.GOLD)
    f.ink(staff, 0.7, K.GOLD_DARK)
    sx, sy = staff[1]
    f.limb([(sx - 4.0, sy + 3.0), (sx, sy - 1.0), (sx + 4.0, sy + 3.0)], 1.8, K.GOLD)
    _swirl(f, sx, sy - 6.0, 7.0, cyc * 0.5, light)
    # The cloak: a bell from the shoulders to the ground, its hem moving.
    sway = 2.5 * step
    left_hem = (cx - 22.0 - sway, hem)
    right_hem = (cx + 22.0 - sway, hem)
    cloak = [(cx - 9.0, top + 4.0), (cx + 10.0, top + 4.0), right_hem]
    for k in range(5):
        u = k / 4.0
        cloak.append((right_hem[0] + (left_hem[0] - right_hem[0]) * u, hem + 2.0 * math.sin(u * math.pi * 2.0 + cyc)))
    cloak.append(left_hem)
    if fall:
        cloak = [(x, max(y, top + 4.0 + (y - top) * (1.0 - 0.6 * fall))) for x, y in cloak]
    f.poly(K.turn(cloak, cx, hem, lean), CLOAK)
    f.poly(K.turn([(cx - 9.0, top + 4.0), (cx - 1.0, top + 4.0), (cx - 6.0, hem), left_hem], cx, hem, lean), CLOAK_SHADE, body=False)
    # Bands of magenta at the hem and down the front.
    f.poly(K.turn([(left_hem[0] + 1.0, hem - 6.0), (right_hem[0] - 1.0, hem - 6.0), (right_hem[0], hem - 1.0), (left_hem[0], hem - 1.0)], cx, hem, lean), K.MAGENTA, body=False)
    f.poly(K.turn([(cx + 3.0, top + 8.0), (cx + 7.0, top + 8.0), (cx + 10.0 - sway, hem - 6.0), (cx + 5.0 - sway, hem - 6.0)], cx, hem, lean), K.MAGENTA, body=False)
    # The swirl of the dimension on the cloak's breast.
    if not fall:
        bx, by = K.turn([(cx - 4.0, top + 26.0)], cx, hem, lean)[0]
        _swirl(f, bx, by, 5.0, 0.6, 0.0)
    # Boots under the hem.
    for side in (-1.0, 1.0):
        bx = cx + side * 7.0 + 4.0 * step * side
        f.poly([(bx - 4.0, GROUND), (bx + 6.0, GROUND), (bx + 5.0, GROUND - 4.0), (bx - 3.0, GROUND - 5.0)], K.VIOLET_DARK)
    # The free hand: out of the cloak when the Curator talks.
    if hand > 0.05 and not fall:
        hx, hy = K.turn([(cx + 12.0 + 6.0 * hand, top + 22.0 - 6.0 * hand)], cx, hem, lean)[0]
        f.limb([K.turn([(cx + 6.0, top + 14.0)], cx, hem, lean)[0], (hx, hy)], 4.6, CLOAK)
        f.ellipse(hx + 1.5, hy, 2.6, 2.6, FACE)
    # The hand on the staff.
    f.ellipse(staff_x - 1.0 + staff_lean * 0.1, GROUND - 52.0 + bob + fall * 30.0, 3.2, 3.0, CLOAK_SHADE)
    # The head under the hat: dark, two eyes.
    hx, hy = K.turn([(cx + 1.0, top - 4.0 + nod * 0.4)], cx, hem, lean)[0]
    f.ellipse(hx, hy, 9.0, 8.0, FACE)
    if not fall:
        blink = anim == "idle" and i == 3
        for ox in (-3.0, 4.4):
            if blink:
                f.ink([(hx + ox - 1.6, hy + 1.0), (hx + ox + 1.6, hy + 1.0)], 0.9, EYES)
            else:
                f.ellipse(hx + ox, hy + 1.0, 1.6, 2.4, EYES, body=False)
                f.glow(hx + ox, hy + 1.0, 3.0, K.alpha(EYES, 0.35))
    # The hat: a wide brim and a crown that bends back, with its feather.
    brim_tilt = lean + nod * 1.5 + fall * 30.0
    hat_x, hat_y = hx, hy - 7.0 + fall * 6.0
    brim = K.turn(K.ellipse_points(hat_x, hat_y, 21.0, 4.6, 24), hat_x, hat_y, brim_tilt)
    crown = K.turn([(hat_x - 9.0, hat_y - 1.0), (hat_x + 9.0, hat_y - 1.0), (hat_x + 6.0, hat_y - 12.0), (hat_x - 2.0, hat_y - 20.0), (hat_x - 10.0, hat_y - 17.0), (hat_x - 6.0, hat_y - 10.0)], hat_x, hat_y, brim_tilt)
    feather = K.turn([(hat_x - 4.0, hat_y - 8.0), (hat_x - 12.0, hat_y - 26.0), (hat_x - 22.0, hat_y - 30.0 + 2.0 * math.sin(cyc)), (hat_x - 14.0, hat_y - 16.0)], hat_x, hat_y, brim_tilt)
    f.poly(feather, K.MAGENTA)
    f.ink(feather[0:3], 0.8, K.MAGENTA_LIGHT)
    f.poly(crown, HAT)
    f.poly(K.turn([(hat_x - 9.0, hat_y - 1.0), (hat_x - 2.0, hat_y - 1.0), (hat_x - 6.0, hat_y - 10.0), (hat_x - 10.0, hat_y - 17.0)], hat_x, hat_y, brim_tilt), HAT_SHADE, body=False)
    f.poly(K.turn([(hat_x - 9.0, hat_y - 4.0), (hat_x + 9.0, hat_y - 4.0), (hat_x + 8.6, hat_y - 1.0), (hat_x - 8.6, hat_y - 1.0)], hat_x, hat_y, brim_tilt), K.MAGENTA, body=False)
    f.poly(brim, HAT)
    f.poly(K.turn(K.ellipse_points(hat_x, hat_y + 1.6, 20.0, 2.6, 24), hat_x, hat_y, brim_tilt), HAT_SHADE, body=False)
    return f.finish(width=1.6, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
