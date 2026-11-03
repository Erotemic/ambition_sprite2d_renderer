"""NDR-115: the household android of the Picture Palace.

A gentle android of smooth white plates on grey joints, slim, upright, a
butler's black bow tie at its throat. Its head is round and white, with a
dark face plate where a kind face is drawn in simple lights: two round eyes
and a smile of dots. It is slowly becoming more human: one hand is already
a real hand of skin, and it holds that hand up a little, as a thing it is
still getting used to.

A parody of the film android who wanted for two hundred years to be a man
(an original drawing, no likeness). It talks; it does not fight.

Rows: ``idle`` (it looks at its hand; it blinks), ``walk``, ``talk`` (the
smile of lights moves; the hand of skin makes a small gesture), ``hit`` and
``death`` (it kneels, its head bows, and its lights go out).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _picture_palace_kit as M

TARGET_NAME = "art_ndr115"
FRAME_SIZE = (160, 224)
GROUND = 219.0
ROWS: List[Tuple[str, int, int]] = M.ROWS
LOOPS = M.LOOPS

ACTOR_METADATA = M.machine_metadata(
    "npc_art_ndr115", "NDR-115", "Biped", "Standard", ["robot", "android", "butler", "becoming_human"],
    "A gentle household android of the Picture Palace in the Art dimension: smooth white plates on grey joints, a round head "
    "with a kind face of simple lights, a butler's bow tie, and one hand that is already a real hand of skin. It wants to be "
    "human and has two hundred years to work on it. A parody of the android of the films about one; an original drawing.",
)

PLATE = (242, 244, 248, 255)
PLATE_SHADE = (190, 196, 210, 255)
JOINT = (128, 134, 150, 255)
JOINT_DARK = (88, 92, 106, 255)
VISOR = (48, 54, 70, 255)
LIGHT = (130, 226, 255, 255)
LIGHT_HOT = (230, 252, 255, 255)
SKIN = (234, 180, 148, 255)
SKIN_SHADE = (196, 136, 108, 255)
TIE = (24, 22, 30, 255)

THIGH, SHIN = 33.5, 34.0


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    cx = 74.0
    bob, lean, nod, look, smile, light, stride, sink, swing, gesture, blink = 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, False
    if anim == "idle":
        look = 0.5 + 0.5 * math.sin(cyc)
        nod = 2.0 * look
        blink = i == 4
        bob = 0.6 * math.sin(cyc)
    elif anim == "walk":
        stride = math.sin(cyc)
        bob = -1.5 * abs(math.cos(cyc))
        swing = -10.0 * stride
        lean = 1.5
    elif anim == "talk":
        smile = 0.5 + 0.5 * math.sin(cyc * 2.0)
        gesture = math.sin(cyc)
        nod = 1.0 * math.sin(cyc * 2.0)
    elif anim == "hit":
        lean, nod, light = -8.0 + 3.0 * t, -2.0, (0.3 if i == 1 else 1.0)
    elif anim == "death":
        sink = 30.0 * min(1.0, t * 1.3)
        lean = 10.0 * t
        nod = 10.0 * t
        light = max(0.0, 1.0 - t * 1.2)
        swing = 8.0 * t

    hip = (cx, 134.0 + bob + sink)

    def U(dx: float, dy: float):
        return K.turn([(hip[0] + dx, hip[1] + dy)], hip[0], hip[1], lean)[0]

    def Us(points):
        return [U(x, y) for x, y in points]

    # -- legs ---------------------------------------------------------------------
    for side, colour, dx, phase in ((1.0, PLATE_SHADE, 6.0, -1.0), (-1.0, PLATE, -5.0, 1.0)):
        h = (hip[0] + dx, hip[1] + 5.0)
        step = stride * phase
        ax = cx + dx * 1.1 + 12.0 * step + (12.0 * t if anim == "death" else 0.0) * (1 if side < 0 else 0.4)
        lift = 5.0 * max(0.0, math.cos(cyc)) * (1 if step > 0 else 0) if anim == "walk" else 0.0
        ankle = (ax, GROUND - 11.0 - lift)
        kn = M.knee(h, ankle, THIGH, SHIN, 1.0)
        M.rod(f, [h, kn], 4.0, JOINT_DARK)
        M.rod(f, [h, (h[0] + (kn[0] - h[0]) * 0.82, h[1] + (kn[1] - h[1]) * 0.82)], 10.0, colour)
        M.rod(f, [kn, ankle], 4.0, JOINT_DARK)
        M.rod(f, [(kn[0] + (ankle[0] - kn[0]) * 0.15, kn[1] + (ankle[1] - kn[1]) * 0.15), (ankle[0], ankle[1] - 3.0)], 9.0, colour)
        M.disc(f, kn[0], kn[1], 4.6, 4.6, JOINT)
        fy = ankle[1]
        M.plate(f, [(ax - 6.0, fy - 1.0), (ax + 6.0, fy - 1.0), (ax + 14.0, fy + 6.0), (ax + 14.0, fy + 11.0), (ax - 7.0, fy + 11.0), (ax - 8.0, fy + 5.0)], colour)
        f.ink([(ax - 6.0, fy + 8.0), (ax + 12.0, fy + 8.0)], 0.8, JOINT)

    # -- the far arm: held behind the back, as a butler stands -------------------
    sh_f = U(14.0, -60.0)
    el_f = K.turn([U(10.0, -34.0)], sh_f[0], sh_f[1], swing)[0]
    wr_f = K.turn([U(-6.0, -20.0)], sh_f[0], sh_f[1], swing * 0.5)[0]
    M.rod(f, [sh_f, el_f], 8.0, PLATE_SHADE)
    M.rod(f, [el_f, wr_f], 7.0, PLATE_SHADE)
    M.disc(f, el_f[0], el_f[1], 3.6, 3.6, JOINT_DARK)

    # -- pelvis, waist, chest -----------------------------------------------------
    M.plate(f, Us([(-15.0, -8.0), (15.0, -8.0), (13.0, 4.0), (6.0, 9.0), (-6.0, 9.0), (-13.0, 4.0)]), PLATE)
    f.poly(Us([(-15.0, -8.0), (-6.0, -8.0), (-6.0, 9.0), (-13.0, 4.0)]), PLATE_SHADE, body=False)
    for k in range(3):
        y = -12.0 - k * 5.0
        M.plate(f, Us([(-10.0 + k, y - 2.6), (10.0 - k, y - 2.6), (10.0 - k, y + 2.6), (-10.0 + k, y + 2.6)]), JOINT, edge=0.7)
    chest = [(-19.0, -62.0), (-6.0, -66.0), (10.0, -65.0), (19.0, -58.0), (18.0, -40.0), (12.0, -28.0), (-12.0, -28.0), (-18.0, -40.0)]
    M.plate(f, Us(chest), PLATE)
    f.poly(Us([(-19.0, -62.0), (-6.0, -66.0), (-6.0, -28.0), (-12.0, -28.0), (-18.0, -40.0)]), PLATE_SHADE, body=False)
    f.ink(Us([(-2.0, -62.0), (0.0, -32.0)]), 0.9, PLATE_SHADE)
    f.ink(Us([(-14.0, -44.0), (14.0, -44.0)]), 0.8, PLATE_SHADE)
    f.ink(Us([(8.0, -60.0), (16.0, -54.0)]), 1.2, K.WHITE)

    # -- neck, bow tie, head ------------------------------------------------------
    M.rod(f, Us([(3.0, -64.0), (3.0, -72.0)]), 7.0, JOINT)
    # The butler's bow tie at the throat.
    bx, by = U(10.0, -65.0)
    M.plate(f, [(bx - 6.0, by - 4.0), (bx, by - 0.5), (bx - 6.0, by + 3.5)], TIE, edge=0.6)
    M.plate(f, [(bx + 6.0, by - 4.0), (bx, by - 0.5), (bx + 6.0, by + 3.5)], TIE, edge=0.6)
    f.dot(bx, by - 0.3, 1.6, (60, 58, 70, 255))
    hc = U(4.0, -86.0 + nod * 0.3)
    hrot = lean * 0.3 + nod * 1.5

    def H(dx: float, dy: float):
        return K.turn([(hc[0] + dx, hc[1] + dy)], hc[0], hc[1], hrot)[0]

    def Hs(points):
        return [H(x, y) for x, y in points]

    M.plate(f, Hs(K.ellipse_points(0.0, 0.0, 14.0, 15.0, 30)), PLATE)
    # The back of the head in shade: half of the round, to a line behind the ear.
    back = [(-14.0 * math.cos(a), 15.0 * math.sin(a)) for a in [-math.pi / 2 + k * math.pi / 12 for k in range(13)]]
    f.poly(Hs(back + [(-6.0, 14.0), (-6.0, -14.0)]), PLATE_SHADE, body=False)
    # The ear: a grey disc at the side of the head.
    M.disc(f, *H(-5.0, 1.0), 4.0, 4.6, JOINT, body=False)
    f.dot(*H(-5.0, 1.0), 1.4, JOINT_DARK)
    # The face plate, and the kind face of lights on it.
    face = [(1.0, -8.0), (8.0, -10.0), (13.0, -6.0), (14.4, 1.0), (12.0, 8.0), (6.0, 10.0), (2.0, 7.0), (0.0, 0.0)]
    M.plate(f, Hs(face), VISOR, edge=0.7, body=False)
    for ex in (5.0, 11.0):
        exx, eyy = H(ex, -2.0)
        if blink:
            f.ink([(exx - 1.6, eyy), (exx + 1.6, eyy)], 0.9, K.alpha(LIGHT, light))
        else:
            f.dot(exx, eyy, 1.7, K.alpha(LIGHT, light))
            f.dot(exx + 0.4, eyy - 0.4, 0.6, K.alpha(LIGHT_HOT, light))
            f.glow(exx, eyy, 3.2, K.alpha(LIGHT, 0.4 * light))
    for k in range(5):
        u = (k - 2) / 2.0
        mx, my = H(8.0 + 2.2 * (k - 2), 4.5 + 1.2 * (1.0 - u * u) * (1.0 + 0.6 * smile) - (0.8 * smile if k in (1, 3) else 0.0))
        f.dot(mx, my, 0.75, K.alpha(LIGHT, light))
        f.glow(mx, my, 1.6, K.alpha(LIGHT, 0.3 * light))
    f.ink(Hs([(-6.0, -11.0), (2.0, -13.5)]), 1.2, K.WHITE)

    # -- the near arm, with its hand of skin ---------------------------------------
    sh_n = U(-14.0, -58.0)
    M.disc(f, sh_n[0], sh_n[1], 6.0, 6.0, PLATE)
    raise_ = 0.6 * look + 2.0 * gesture
    el_n = U(-16.0, -32.0)
    wr_n = U(6.0, -40.0 - 3.0 * raise_)
    M.rod(f, [sh_n, el_n], 8.0, PLATE)
    M.disc(f, el_n[0], el_n[1], 3.8, 3.8, JOINT)
    M.rod(f, [el_n, wr_n], 7.0, PLATE)
    # A white cuff where the plates stop and the skin begins.
    M.rod(f, [(wr_n[0] - 2.0, wr_n[1] + 0.6), (wr_n[0] + 0.5, wr_n[1])], 8.4, K.WHITE, edge=0.8)
    # The hand: an open palm, fingers up, a thumb toward the face.
    px, py = wr_n[0] + 5.0, wr_n[1] - 3.0
    tilt = -10.0 * gesture
    palm = K.turn(K.ellipse_points(px, py, 4.0, 4.6, 16), px, py + 4.0, tilt)
    for k in range(4):
        fx = px - 3.0 + k * 2.1
        fl = (6.0, 7.0, 6.6, 5.4)[k]
        tip = K.turn([(fx + 0.6, py - 3.0 - fl)], px, py + 4.0, tilt)[0]
        base = K.turn([(fx, py - 2.0)], px, py + 4.0, tilt)[0]
        M.rod(f, [base, tip], 1.9, SKIN, edge=0.7)
    thumb = K.turn([(px + 3.0, py + 1.0), (px + 7.0, py - 2.5)], px, py + 4.0, tilt)
    M.rod(f, thumb, 2.2, SKIN, edge=0.7)
    M.plate(f, palm, SKIN, edge=0.7)
    f.ink(K.turn([(px - 2.0, py + 1.0), (px + 1.0, py + 2.0)], px, py + 4.0, tilt), 0.6, SKIN_SHADE)
    return f.finish(width=1.6)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
