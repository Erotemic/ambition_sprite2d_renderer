"""The goat and the car behind the doors of Hylbert's Hotel's game show (the
Math dimension's ballroom, `math_hotel_door_1..3`). The closets' prop
pictures (`targets/props/math_ballroom_props.py` `goat`, `car`) are these
two at rest, so the props and the actors cannot drift apart.

- `math_show_goat`: a white nanny goat, standing, unimpressed: horns swept
  back, ears out sideways, a beard, amber eyes with a goat's bar pupils, a
  short tail that stands up. `idle` chews (the jaw and the beard), flicks an
  ear, blinks and flicks its tail; `walk` steps in diagonal pairs, the head
  nodding; `hit` throws the head up, ears back and eyes wide; `death`
  buckles the knees, lies down, closes its eyes and fades.
- `math_show_car`: a red fifties convertible, the top folded down, a gold
  ribbon round its bonnet tied in a bow: tail fins, whitewall tyres,
  chrome bumpers, a side spear, cream seats. `idle` is the showroom: the
  bow's tails stir, a gleam runs along the paint, the headlamp winks;
  `walk` rolls the wheels; `hit` rocks it on its springs; `death` lets its
  tyres down, a hubcap drops off, steam leaks from the bonnet and it fades.

Each faces right, drawn at two frame pixels to each room pixel, inked, its
ground line where the prop's was.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image, ImageFilter

from . import _art_cast_kit as K
from ..props._town_kit import Canvas
from ..props.math_hotel_props import GOLD

PPU = 2.0
Point = Tuple[float, float]
INK = (44, 32, 30)


def _smooth(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def _metadata(character_id: str, display_name: str, body_plan: str, traits, description: str) -> dict:
    return {
        "actor": {"character_id": character_id, "display_name": display_name},
        "body": {"body_plan": body_plan, "body_kind": "Standard", "mass_class": "Medium", "traits": list(traits), "locomotion_hint": "Walk"},
        "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
        "tags": ["art"],
        "authoring_description": description,
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "combat.hurt": {"animation": "hit", "events": []},
            "combat.death": {"animation": "death", "events": []},
        },
    }


def _fade(image: Image.Image, fade: float) -> Image.Image:
    if fade < 1.0:
        image.putalpha(image.getchannel("A").point(lambda v: int(v * max(0.0, fade))))
    return image


def _shade(colour, k: float):
    return tuple(max(0, min(255, int(round(v * k)))) for v in colour)


# ------------------------------------------------------------------ drawing


def _grow(c: Canvas, m: np.ndarray, width: float) -> np.ndarray:
    """`m` grown by `width` room pixels: the ink round a part."""
    n = max(1, int(round(width * c.k)))
    img = Image.fromarray(np.clip(m * 255, 0, 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(2 * n + 1))
    return np.asarray(img, np.float32) / 255.0


def _inked(c: Canvas, m: np.ndarray, colour, ink: float = 0.7) -> np.ndarray:
    c.put(_grow(c, m, ink), INK)
    c.put(m, colour)
    return m


def _rot(p: Point, deg: float, about: Point = (0.0, 0.0)) -> Point:
    a = math.radians(deg)
    x, y = p[0] - about[0], p[1] - about[1]
    return (about[0] + x * math.cos(a) - y * math.sin(a), about[1] + x * math.sin(a) + y * math.cos(a))


def _limb(p, pts: Sequence[Point], widths: Sequence[float]) -> None:
    """A tapered limb through `pts`, `widths` across at each point."""
    for (a, wa), (b, wb) in zip(zip(pts, widths), zip(pts[1:], widths[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n
        p.poly([(a[0] + nx * wa / 2, a[1] + ny * wa / 2), (b[0] + nx * wb / 2, b[1] + ny * wb / 2),
                (b[0] - nx * wb / 2, b[1] - ny * wb / 2), (a[0] - nx * wa / 2, a[1] - ny * wa / 2)])
    for q, w in zip(pts, widths):
        p.ellipse(q[0], q[1], w / 2)


def _leaf(root: Point, deg: float, length: float, width: float, bend: float = 0.0) -> List[Point]:
    """A leaf from `root` pointing at `deg` (0 east, 90 down): an ear, a
    tail, a bow's loop. `bend` curls its tip (degrees)."""
    out = []
    n = 8
    for side in (1.0, -1.0):
        row = []
        for i in range(n + 1):
            t = i / n
            half = width / 2 * math.sin(math.pi * min(1.0, t * 1.15)) * side
            a = math.radians(deg + bend * t * t)
            along = (math.cos(a), math.sin(a))
            x = root[0] + along[0] * length * t - along[1] * half
            y = root[1] + along[1] * length * t + along[0] * half
            row.append((x, y))
        out.extend(row if side > 0 else row[::-1])
    return out


def _ik(hip: Point, foot: Point, a: float, b: float, bend: float) -> Point:
    """The joint between bones `a` and `b` from `hip` to `foot`; `bend` +1
    puts it behind the line (east is ahead), -1 ahead of it."""
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = max(1e-3, min(math.hypot(dx, dy), a + b - 1e-3))
    cos_h = max(-1.0, min(1.0, (a * a + d * d - b * b) / (2 * a * d)))
    ang = math.atan2(dy, dx) + bend * math.acos(cos_h)
    return (hip[0] + a * math.cos(ang), hip[1] + a * math.sin(ang))


# --------------------------------------------------------------------- goat

GOAT = "math_show_goat"
GOAT_W, GOAT_H = 100.0, 86.0
GOAT_G = GOAT_H - 2.0
GOAT_ROWS: List[Tuple[str, int, int]] = [("idle", 10, 140), ("walk", 8, 110), ("hit", 3, 90), ("death", 6, 140)]
GOAT_METADATA = _metadata(
    GOAT, "Goat", "quadruped", ["animal", "goat", "game_show"],
    "The goat behind a door of Hylbert's game show, the closet prop drawn to move: a white nanny goat that chews, "
    "unimpressed, flicks an ear and her tail, ambles about the closet, starts when struck and lies down.",
)
COAT = (238, 232, 218)
MUZZLE = (226, 206, 196)
EAR_IN = (226, 176, 166)
HORN = (204, 180, 132)
HORN_RIDGE = (150, 124, 86)
HOOF = (74, 60, 50)
IRIS = (222, 166, 56)
UDDER = (232, 186, 176)

#: The head at rest, relative to the poll, in room pixels: the profile from
#: the back of the skull over the brow down the long nose to the chin.
HEAD = [(-2.5, 3.0), (0.0, -0.5), (4.0, -1.2), (7.5, 1.0), (10.5, 5.0), (13.2, 9.5), (15.0, 12.6), (14.6, 14.6), (13.2, 15.4),
        (10.8, 15.2), (8.0, 15.6), (3.4, 12.6), (-0.4, 9.0)]
JAW = [(10.6, 15.0), (13.8, 15.3), (12.6, 17.4), (8.8, 16.6)]
EYE = (6.2, 4.4)
NOSTRIL = (13.4, 11.6)
EAR_ROOT = (0.6, 4.6)
HORN_PATH = [(2.4, -0.2), (1.2, -5.0), (-1.2, -9.4), (-4.8, -12.6), (-9.0, -13.8), (-11.6, -13.2)]
HORN_W = [3.4, 3.0, 2.6, 2.0, 1.4, 0.7]
#: Where the head sits on the neck at rest.
POLL = (74.0, -62.0)


def draw_goat(c, *, legs, sink: float, bob: float, dip: float, chew: float, tail: float, start: float, blink: float = 0.0,
              ear: float = 0.0, g: float = GOAT_G) -> None:
    """The goat (facing east), posed. `legs`: each leg's (swing, lift),
    hind far, hind near, fore far, fore near; `sink` folds the legs and
    lowers the body; `dip` lowers the head; `chew` works the jaw and the
    beard (-1 to 1); `tail` turns the tail up (degrees); `start` throws the
    head up, the ears back and the eyes wide; `blink` closes the eyes;
    `ear` flicks the near ear up (0 to 1); `g` is the ground line."""
    by = sink * 20.0 - bob
    far_tone = 0.8

    def at(x: float, h: float) -> Point:
        return (x, g - h + by)

    # The legs first: the body covers their tops.
    hips = [(27.0, True), (24.0, False), (61.0, True), (64.0, False)]
    for (x, is_far), (swing, lift), hind in sorted(zip(hips, legs, (True, True, False, False)), key=lambda e: not e[0][1]):
        colour = _shade(COAT, far_tone) if is_far else COAT
        tuck = sink * (7.0 if hind else -7.0)
        foot = (x + 1.0 + swing + tuck, g - lift)
        if hind:
            hip = at(x, 38.0)
            hock = (foot[0] - 2.6 - 1.5 * sink, foot[1] - 14.0 + 3.0 * lift / 3.0 + 4.0 * sink)
            stifle = _ik(hip, hock, 15.0, 12.0, -1.0)
            pts, widths = [hip, stifle, hock, (foot[0], foot[1] - 3.0)], [9.0, 6.0, 3.6, 2.8]
        else:
            hip = at(x, 30.0)
            knee = _ik(hip, (foot[0], foot[1] - 3.0), 14.0, 14.0, -1.0 if lift > 0 or sink > 0 else 1.0)
            pts, widths = [hip, knee, (foot[0], foot[1] - 3.0)], [6.4, 4.0, 2.9]
        _inked(c, c.mask(lambda p: _limb(p, pts, widths)), colour)
        hoof = c.mask(lambda p: p.poly([(foot[0] - 2.0, foot[1] - 3.4), (foot[0] + 1.8, foot[1] - 3.4), (foot[0] + 2.6, foot[1]),
                                        (foot[0] - 2.2, foot[1])]))
        _inked(c, hoof, _shade(HOOF, 0.85) if is_far else HOOF, 0.5)
        c.put(c.mask(lambda p: p.line([(foot[0] + 0.4, foot[1] - 2.0), (foot[0] + 0.6, foot[1])], 0.4)), INK)

    # The head's pose: the whole head turns about the poll.
    turn = 22.0 * dip - 28.0 * start
    poll = (POLL[0] - 1.5 * start + 1.0 * dip, g + POLL[1] + by + 6.0 * dip - 3.0 * start)

    def hp(q: Point) -> Point:
        r = _rot(q, turn)
        return (poll[0] + r[0], poll[1] + r[1])

    # The far horn and the far ear, behind the head and neck.
    horn_far = [hp((x + 1.6, y + 0.4)) for x, y in HORN_PATH]
    _inked(c, c.mask(lambda p: _limb(p, horn_far, HORN_W)), _shade(HORN, far_tone), 0.55)
    ear_deg_far = 200.0 + turn - 40.0 * start
    far_ear = [hp(EAR_ROOT)]
    far_ear = _leaf((far_ear[0][0] + 1.2, far_ear[0][1] - 0.6), ear_deg_far - 14.0, 7.0, 3.2, bend=-14.0)
    _inked(c, c.mask(lambda p: p.poly(far_ear)), _shade(COAT, far_tone), 0.55)

    # The tail: a short flag that stands up, flicked higher.
    root = at(20.0, 48.0)
    tail_pts = _leaf(root, -120.0 - tail, 8.0, 4.0, bend=-20.0)
    _inked(c, c.mask(lambda p: p.poly(tail_pts)), COAT, 0.6)

    # The body: the barrel, the haunch and the shoulder, the shaggy belly,
    # and the neck up to the head.
    torso = [at(19, 46), at(16, 41), at(16.5, 34), at(22, 29), at(30, 27.5), at(44, 26.5), at(56, 27.5), at(64, 29.5), at(70, 34),
             at(72, 40), at(70, 46), at(64, 51), at(56, 52.5), at(44, 50), at(32, 50.5), at(24, 49.5)]
    fringe = []
    for i in range(9):
        x = 26 + i * 5.0
        fringe += [at(x, 28.0), at(x + 2.5, 25.4 - 0.5 * (i % 2))]
    fringe.append(at(70, 30.0))
    throat = hp((-0.4, 9.0))
    jaw_angle = hp((3.4, 12.6))
    skull = hp((-2.5, 3.0))
    neck = [at(57, 52), skull, hp((1.0, 6.0)), jaw_angle, throat, at(73.5, 41), at(70, 34)]

    def body(p):
        p.poly(torso)
        p.ellipse(*at(25.0, 39.0), 10.0, 11.0)
        p.ellipse(*at(62.0, 40.0), 8.0, 10.0)
        p.poly([at(22, 30)] + fringe + [at(70, 34), at(44, 30)])
        p.poly(neck)

    bm = c.mask(body)
    _inked(c, bm, COAT)
    # Shade: the underside in shadow, the light along the back, the fur.
    c.tone(bm * np.clip((c.y - (g - 52 + by)) / 30.0, 0, 1), -0.2)
    c.light(bm * np.clip(1.0 - np.abs(c.y - (g - 49 + by)) / 4.0, 0, 1), (255, 252, 240), 0.35)
    c.tone(bm * (c.noise("goat_fur", 18, 14) - 0.5), 0.08)
    # The haunch's line and the shoulder's.
    c.put(c.mask(lambda p: p.line([at(30, 47), at(33.5, 42), at(34, 36), at(31.5, 31)], 0.45)), _shade(COAT, 0.72))
    c.put(c.mask(lambda p: p.line([at(57.5, 48), at(55.5, 43), at(55.5, 37), at(58, 32)], 0.45)), _shade(COAT, 0.72))
    if sink < 0.5:
        um = c.mask(lambda p: (p.ellipse(*at(33.5, 27.0), 3.4, 2.4), p.ellipse(*at(32.5, 25.2), 0.8, 1.2), p.ellipse(*at(35.0, 25.2), 0.8, 1.2)))
        _inked(c, um, UDDER, 0.5)

    # The head.
    hm = c.mask(lambda p: p.poly([hp(q) for q in HEAD]))
    _inked(c, hm, COAT)
    c.paint(hm * c.soften(c.mask(lambda p: p.ellipse(*hp((13.2, 12.0)), 4.0, 4.6)), 1.2), np.broadcast_to(np.asarray(MUZZLE, np.float32), c.rgb.shape))
    c.tone(hm * np.clip((c.y - (poll[1] + 4)) / 18.0, 0, 1), -0.12)
    # The jaw, chewing: it drops and slides, the beard with it.
    jaw_open = max(0.0, chew) * 1.2
    jaw = [hp((x + 0.6 * chew, y + jaw_open * (x - 8.8) / 5.0)) for x, y in JAW]
    _inked(c, c.mask(lambda p: p.poly(jaw)), COAT, 0.55)
    c.put(c.mask(lambda p: p.line([hp((10.8, 15.0)), hp((14.0, 14.7))], 0.5)), INK)
    beard_root = hp((11.0 + 0.6 * chew, 16.8 + jaw_open))
    beard = [beard_root, (beard_root[0] - 0.4 + 0.8 * chew, beard_root[1] + 3.6), (beard_root[0] - 0.6 + 1.6 * chew, beard_root[1] + 7.6)]
    _inked(c, c.mask(lambda p: _limb(p, beard, [3.4, 2.4, 0.6])), _shade(COAT, 0.93), 0.5)
    for dx in (-0.7, 0.6):
        c.put(c.mask(lambda p: p.line([(beard_root[0] + dx, beard_root[1] + 0.8), (beard_root[0] + dx * 0.4 + 1.1 * chew, beard_root[1] + 5.8)], 0.3)),
              _shade(COAT, 0.72))
    # The nostril.
    c.put(c.mask(lambda p: p.line([hp(NOSTRIL), hp((NOSTRIL[0] + 0.9, NOSTRIL[1] + 1.2))], 0.8)), INK)
    # The eye: amber with a bar pupil; wide when startled, a lid when it
    # blinks.
    ex, ey = hp(EYE)
    wide = 1.0 + 0.35 * start
    if blink >= 0.7:
        c.put(c.mask(lambda p: p.line([(ex - 2.2, ey), (ex, ey + 0.7), (ex + 2.2, ey)], 0.6)), INK)
    else:
        open_ = (1.0 - blink) * wide
        em = c.mask(lambda p: p.ellipse(ex, ey, 2.3 * wide, 1.7 * open_))
        _inked(c, em, IRIS, 0.45)
        c.put(c.mask(lambda p: p.rect(ex - 1.5 * wide, ey - 0.35 * open_, ex + 1.5 * wide, ey + 0.35 * open_)), INK)
        c.put(c.mask(lambda p: p.ellipse(ex + 0.9, ey - 0.6 * open_, 0.45)), (255, 250, 236))
        # The brow over it.
        c.put(c.mask(lambda p: p.line([(ex - 2.6, ey - 2.0 * open_ - 0.2), (ex + 2.0, ey - 2.4 * open_ - 0.2)], 0.5)), _shade(COAT, 0.6))
    # The near horn, ridged.
    horn = [hp(q) for q in HORN_PATH]
    _inked(c, c.mask(lambda p: _limb(p, horn, HORN_W)), HORN, 0.55)
    for i in range(1, len(horn) - 1):
        (x0, y0), (x1, y1) = horn[i - 1], horn[i + 1]
        n = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = -(y1 - y0) / n, (x1 - x0) / n
        w = HORN_W[i] / 2
        q = horn[i]
        c.put(c.mask(lambda p: p.line([(q[0] - nx * w, q[1] - ny * w), (q[0] + nx * w, q[1] + ny * w)], 0.35)), HORN_RIDGE)
    # The near ear: out sideways and a little down; it flicks up, and lies
    # back when the goat is startled.
    ear_deg = 178.0 + turn - 38.0 * ear + 24.0 * start
    ear_pts = _leaf(hp(EAR_ROOT), ear_deg, 8.4, 3.8, bend=-16.0 + 10.0 * ear)
    _inked(c, c.mask(lambda p: p.poly(ear_pts)), COAT, 0.55)
    inner = _leaf(hp(EAR_ROOT), ear_deg, 6.2, 1.6, bend=-16.0 + 10.0 * ear)
    c.put(c.mask(lambda p: p.poly(inner)), EAR_IN)


def _goat_pose(anim: str, i: int, n: int) -> dict:
    loop = anim in {"idle", "walk"}
    t = K.phase(i, n, loop)
    still = [(0.0, 0.0)] * 4
    if anim == "idle":
        flick = _smooth((t - 0.7) / 0.1) * (1.0 - _smooth((t - 0.85) / 0.1))
        ear = _smooth((t - 0.2) / 0.1) * (1.0 - _smooth((t - 0.35) / 0.1))
        return dict(legs=still, sink=0.0, bob=0.3 * math.sin(t * math.tau), dip=0.12 + 0.08 * math.sin(t * math.tau),
                    chew=math.sin(t * math.tau * 3.0), tail=40.0 * flick, start=0.0, blink=1.0 if i == 6 else 0.0, ear=ear)
    if anim == "walk":
        a = math.sin(t * math.tau)
        la, lb = max(0.0, math.cos(t * math.tau)) * 3.4, max(0.0, -math.cos(t * math.tau)) * 3.4
        # Diagonal pairs: the far hind with the near fore.
        legs = [(5.0 * a, la), (-5.0 * a, lb), (-5.0 * a, lb), (5.0 * a, la)]
        return dict(legs=legs, sink=0.0, bob=0.9 * abs(math.cos(t * math.tau)), dip=0.1 + 0.12 * math.sin(t * math.tau * 2.0), chew=0.0,
                    tail=12.0, start=0.0, ear=0.3)
    if anim == "hit":
        k = [0.7, 1.0, 0.45][min(i, 2)]
        return dict(legs=[(-2.0 * k, 0.0)] * 4, sink=0.04 * k, bob=0.0, dip=0.0, chew=-0.6 * k, tail=45.0 * k, start=k)
    # Death: the knees buckle, she lies down, the head sinks, eyes close.
    s = _smooth(t * 1.3)
    return dict(legs=still, sink=s, bob=0.0, dip=0.2 + 0.9 * _smooth(t * 1.6 - 0.3), chew=0.0, tail=-10.0 * s, start=0.0,
                blink=_smooth((t - 0.4) / 0.3), ear=-0.4 * s)


def _goat_frame(anim: str, i: int, n: int) -> Image.Image:
    c = Canvas(GOAT, GOAT_W, GOAT_H, (0.0, 0.0), PPU)
    draw_goat(c, **_goat_pose(anim, i, n))
    image = c.image()
    if anim == "death":
        image = _fade(image, 1.0 - _smooth((K.phase(i, n, False) - 0.6) / 0.4))
    return image


# ---------------------------------------------------------------------- car

CAR = "math_show_car"
CAR_W, CAR_H = 210.0, 104.0
CAR_G = CAR_H - 2.0
CAR_ROWS: List[Tuple[str, int, int]] = [("idle", 12, 110), ("walk", 4, 110), ("hit", 3, 90), ("death", 6, 140)]
CAR_METADATA = _metadata(
    CAR, "The Car", "vehicle", ["vehicle", "car", "prize", "game_show"],
    "The car behind a door of Hylbert's game show, the closet prop drawn to move: a red fifties convertible with tail "
    "fins and whitewalls, a gold ribbon and bow on its bonnet; its paint gleams; it rocks on its springs when struck.",
)
RED = (204, 34, 40)
RED_DARK = (120, 18, 26)
CHROME = (226, 230, 236)
CHROME_DARK = (136, 142, 156)
GLASS = (176, 214, 232)
SEAT = (238, 226, 200)
TOP = (214, 196, 160)
TYRE = (34, 32, 36)
WHITEWALL = (240, 238, 230)
LAMP = (255, 244, 200)
TAIL_LAMP = (255, 96, 64)
WELL = (24, 18, 20)
GOLD_DARK = _shade(GOLD, 0.7)
WHEELS = (48.0, 162.0)
WHEEL_R = 14.5


def _arc(cx: float, cy: float, r: float, a0: float, a1: float, n: int = 12) -> List[Point]:
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _loop(knot: Point, deg: float, length: float = 25.0, depth: float = 17.0) -> Tuple[List[Point], List[Point]]:
    """One loop of a bow from its knot at `deg`: a rounded oval that pinches
    to the knot, and the shadowed fold inside it."""

    def oval(scale: float, along: float) -> List[Point]:
        a = math.radians(deg)
        out = []
        for i in range(24):
            u = 2 * math.pi * i / 24
            x = along + length / 2 * scale * (1 - math.cos(u)) * 0.5 + length / 2 * (1 - scale) * 0.5
            y = depth / 2 * scale * math.sin(u) * min(1.0, 0.35 + (1 - math.cos(u)) * 0.6)
            out.append((knot[0] + x * math.cos(a) - y * math.sin(a), knot[1] + x * math.sin(a) + y * math.cos(a)))
        return out

    return oval(1.0, 0.0), oval(0.42, length * 0.32)


def draw_car(c, *, lift: float, tilt: float, flat: float, ribbon: float, gleam: Optional[float], lamp: float, roll: float,
             steam: float = 0.0, cap_off: float = 0.0, g: float = CAR_G) -> None:
    """The car, posed: `lift` raises the body on its springs, `tilt` noses
    it down (+) or up; `flat` lets the tyres down; `ribbon` stirs the bow's
    tails; `gleam` is where a light runs along the paint (0 to 1, or none);
    `lamp` lights the headlamp; `roll` turns the wheels (degrees); `steam`
    leaks from the bonnet (0 to 1); `cap_off` drops the rear hubcap (0 to 1);
    `g` is the ground line."""
    r = WHEEL_R * (1.0 - 0.22 * flat)
    axle = g - r - 1.2 * flat
    sink = 4.0 * flat

    def at(x: float, h: float) -> Point:
        return (x, g - h - lift + sink + tilt * (x - 105.0) / 105.0 * 3.0)

    # The wheel wells, dark, behind the body.
    for x in WHEELS:
        c.put(c.mask(lambda p: p.ellipse(*at(x, 16.5), 17.0, 16.0)), WELL)
    # The folded top behind the rear seat, the seats and the wheel, then the
    # windscreen: what stands above the body's belt line.
    top = c.mask(lambda p: (p.ellipse(*at(30.0, 40.5), 9.0, 4.0), p.poly([at(22, 39), at(40, 39), at(38, 43), at(24, 43)])))
    _inked(c, top, TOP, 0.55)
    c.put(c.mask(lambda p: [p.line([at(x, 37.5), at(x + 2, 44)], 0.4) for x in (26, 31, 36)]), _shade(TOP, 0.7))
    for x0, x1, h in ((52, 80, 47.0), (90, 112, 48.5)):
        seat = c.mask(lambda p: (p.poly([at(x0, 37), at(x0 + 1, h - 2.5), at(x1 - 1, h - 2.5), at(x1, 37)]),
                                 p.ellipse(*at((x0 + x1) / 2, h - 2.5), (x1 - x0) / 2, 2.6)))
        _inked(c, seat, SEAT, 0.55)
        c.put(c.mask(lambda p: [p.line([at(x, 38), at(x, h - 1.5)], 0.35) for x in np.linspace(x0 + 4, x1 - 4, 4)]), _shade(SEAT, 0.78))
    wheel_c = at(116.0, 44.0)
    c.put(c.mask(lambda p: p.line([at(122.0, 38.5), wheel_c], 1.2)), INK)
    c.put(c.mask(lambda p: p.ring(wheel_c[0], wheel_c[1], 3.4, 1.1)), INK)
    screen = [at(119, 37), at(126, 37), at(116, 55), at(110, 55)]
    c.put(c.mask(lambda p: p.poly(screen)), GLASS, 0.55)
    c.light(c.mask(lambda p: p.line([at(122, 39), at(114, 53)], 0.8)), (255, 255, 255), 0.5)
    c.put(c.mask(lambda p: (p.line([at(119, 37), at(110, 55), at(116, 55), at(126, 37)], 1.0))), CHROME_DARK)
    c.put(c.mask(lambda p: p.ellipse(*at(124.0, 40.0), 1.8, 1.2)), CHROME)  # the mirror

    # The body: a long low side, fins at the tail, a hooded headlamp, cut
    # round the wheels.
    front_arch = _arc(WHEELS[1], 0.0, 17.5, 0.0, -180.0)
    rear_arch = _arc(WHEELS[0], 0.0, 17.5, 0.0, -180.0)
    outline = [(7, 15), (6, 27), (8, 35), (13, 42.5), (17, 42.8), (24, 39), (60, 37.2), (119, 37.4), (160, 37.0), (186, 35.4),
               (195, 33.5), (200, 29.5), (201, 22), (199, 15)]
    outline += [(x, 16.5 - y) for x, y in front_arch]
    outline += [(x, 16.5 - y) for x, y in rear_arch]
    pts = [at(x, h) for x, h in outline]
    bm = c.mask(lambda p: p.poly(pts))
    _inked(c, bm, RED, 0.8)
    # Paint: lit along the shoulder, darker down the side and under it.
    c.tone(bm * np.clip((c.y - (at(0, 34)[1])) / 22.0, 0, 1), -0.32)
    c.light(bm * np.clip(1.0 - np.abs(c.y - at(0, 33.0)[1]) / 2.2, 0, 1), (255, 220, 214), 0.5)
    c.tint(bm * np.clip(1.0 - np.abs(c.y - at(0, 15.5)[1]) / 3.0, 0, 1), RED_DARK, 0.45)
    if gleam is not None:
        gx = 10 + 190 * gleam
        band = np.clip(1.0 - np.abs(c.x - gx - (c.y - at(0, 30)[1]) * 0.45) / 5.0, 0, 1)
        c.light(bm * band, (255, 255, 255), 0.6)
    # The belt line's chrome, the side spear, the door, its handle.
    c.put(c.mask(lambda p: p.line([at(24, 38.4), at(60, 36.6), at(119, 36.8), at(186, 34.8)], 1.1)), CHROME)
    spear = c.mask(lambda p: p.poly([at(60, 25.5), at(188, 27.8), at(188, 26.2), at(70, 24.0)]))
    c.put(_grow(c, spear, 0.35), CHROME_DARK)
    c.put(spear, CHROME)
    c.put(c.mask(lambda p: (p.line([at(84, 36.2), at(83, 13.4)], 0.5), p.line([at(128, 36.2), at(130, 13.2)], 0.5))), _shade(RED_DARK, 0.7))
    c.put(c.mask(lambda p: p.rect(*at(88, 32.4), *at(93, 31.0))), CHROME)
    # The fin's tail lamp, the bumpers, the headlamp in its hood, the
    # bonnet's ornament.
    c.put(c.mask(lambda p: p.ellipse(*at(9.5, 33.5), 1.6, 3.6)), TAIL_LAMP)
    for x0, x1 in ((3.0, 15.0), (192.0, 205.0)):
        bumper = c.mask(lambda p: p.poly([at(x0, 21.5), at(x1, 21.5), at(x1 + (1 if x1 > 100 else 0), 15.0), at(x0 - (0 if x1 > 100 else 1), 15.0)]))
        _inked(c, bumper, CHROME, 0.55)
        c.light(bumper * np.clip(1.0 - np.abs(c.y - at(0, 19.5)[1]) / 1.0, 0, 1), (255, 255, 255), 0.7)
    hx, hy = at(197.2, 28.2)
    _inked(c, c.mask(lambda p: p.ellipse(hx, hy, 3.4, 3.8)), CHROME, 0.5)
    c.put(c.mask(lambda p: p.ellipse(hx + 0.3, hy, 2.4, 2.8)), LAMP if lamp > 0.5 else (232, 220, 190))
    if lamp > 0.5:
        # The wink: a light thrown ahead and a glint.
        c.put(c.mask(lambda p: p.ellipse(hx + 7.0, hy, 8.0, 4.4), blur=1.6), LAMP, 0.5)
        c.put(c.mask(lambda p: (p.line([(hx + 2.0, hy - 5.0), (hx + 2.0, hy + 5.0)], 0.5), p.line([(hx - 3.0, hy), (hx + 7.0, hy)], 0.5))), (255, 255, 255))
    c.put(c.mask(lambda p: p.poly([at(184, 35.2), at(191, 37.6), at(189, 35.0)])), CHROME)

    # The ribbon round the bonnet and the bow on it.
    rx = 140.0
    band = c.mask(lambda p: p.poly([at(rx - 2.6, 37.4), at(rx + 2.6, 37.4), at(rx + 2.9, 13.4), at(rx - 2.3, 13.4)]))
    _inked(c, band, GOLD, 0.45)
    c.tone(band * np.clip((c.y - at(0, 37)[1]) / 24.0, 0, 1), -0.25)
    knot = at(rx + 0.4, 40.5)
    s = ribbon
    loops = [_loop(knot, -150.0 - 3.0 * s), _loop(knot, -30.0 + 3.0 * s)]
    tails = [_leaf(knot, 128.0 + 6.0 * s, 15.0, 4.6, bend=-18.0), _leaf(knot, 52.0 - 6.0 * s, 14.0, 4.6, bend=22.0)]
    for leaf in tails:
        _inked(c, c.mask(lambda p: p.poly(leaf)), GOLD_DARK, 0.5)
    for leaf, fold in loops:
        lm = c.mask(lambda p: p.poly(leaf))
        _inked(c, lm, GOLD, 0.5)
        c.tone(lm * np.clip((c.y - (knot[1] - 12)) / 14.0, 0, 1), -0.22)
        # The inside of the loop, in its own shadow.
        c.put(c.mask(lambda p: p.poly(fold)), GOLD_DARK)
    _inked(c, c.mask(lambda p: p.ellipse(knot[0], knot[1], 3.4, 3.0)), _shade(GOLD, 0.88), 0.5)

    # The wheels: whitewalls and chrome caps, turning.
    for j, x in enumerate(WHEELS):
        cx, cy = x, axle
        tyre = c.mask(lambda p: p.ellipse(cx, cy, WHEEL_R * (1.0 + 0.12 * flat), r))
        _inked(c, tyre, TYRE, 0.5)
        c.put(c.mask(lambda p: p.ring(cx, cy, r * 0.68, 2.6)), WHITEWALL)
        off = cap_off if j == 0 else 0.0
        if off < 1.0:
            ccx, ccy = cx - 6.0 * off, cy + (r - 5.0) * off
            cap = c.mask(lambda p: p.ellipse(ccx, ccy, 5.6, 5.6 * (1.0 - 0.6 * off)))
            _inked(c, cap, CHROME, 0.4)
            for k in range(3):
                a = math.radians(roll + 120.0 * k)
                c.put(c.mask(lambda p: p.line([(ccx, ccy), (ccx + 4.4 * math.cos(a), ccy + 4.4 * math.sin(a) * (1.0 - 0.6 * off))], 0.7)),
                      CHROME_DARK)
            c.light(c.mask(lambda p: p.ellipse(ccx - 1.6, ccy - 1.8, 1.4)), (255, 255, 255), 0.8)
        else:
            c.put(c.mask(lambda p: p.ellipse(cx, cy, 3.6)), (70, 70, 76))
            c.put(c.mask(lambda p: [p.ellipse(cx + 2.4 * math.cos(math.radians(72 * k)), cy + 2.4 * math.sin(math.radians(72 * k)), 0.6)
                                    for k in range(5)]), CHROME_DARK)
        if off >= 1.0:
            # The hubcap, fallen flat on the ground beside its wheel.
            _inked(c, c.mask(lambda p: p.ellipse(cx - 20.0, g - 1.2, 5.6, 1.3)), CHROME, 0.4)

    if steam > 0.0:
        rng = np.random.default_rng(7)
        for k in range(5):
            u = (steam * 1.6 + k * 0.21) % 1.0
            px, py = at(168.0 + 10.0 * rng.random(), 38.0 + 22.0 * u)
            c.put(c.mask(lambda p: p.ellipse(px + 4.0 * u, py, 3.0 + 4.0 * u), blur=1.6), (236, 238, 240), 0.6 * (1.0 - u) * min(1.0, steam * 3.0))


def _car_pose(anim: str, i: int, n: int) -> dict:
    t = K.phase(i, n, anim in {"idle", "walk"})
    if anim == "idle":
        gleam = t / 0.6 if t < 0.6 else None
        return dict(lift=0.0, tilt=0.0, flat=0.0, ribbon=math.sin(t * math.tau * 2.0), gleam=gleam, lamp=1.0 if 0.75 <= t < 0.85 else 0.0, roll=0.0)
    if anim == "walk":
        return dict(lift=0.5 * abs(math.sin(t * math.tau)), tilt=0.0, flat=0.0, ribbon=math.sin(t * math.tau), gleam=None, lamp=0.0, roll=120.0 * t * 4 / n)
    if anim == "hit":
        k = [1.0, -0.7, 0.3][min(i, 2)]
        return dict(lift=2.0 * k, tilt=2.0 * k, flat=0.0, ribbon=2.0 * k, gleam=None, lamp=0.0, roll=0.0)
    s = _smooth(t * 1.3)
    return dict(lift=0.0, tilt=-0.8 * s, flat=s, ribbon=-s, gleam=None, lamp=0.0, roll=0.0, steam=t, cap_off=_smooth((t - 0.2) / 0.3))


def _car_frame(anim: str, i: int, n: int) -> Image.Image:
    c = Canvas(CAR, CAR_W, CAR_H, (0.0, 0.0), PPU)
    draw_car(c, **_car_pose(anim, i, n))
    image = c.image()
    if anim == "death":
        image = _fade(image, 1.0 - _smooth((K.phase(i, n, False) - 0.6) / 0.4))
    return image


def goat_at_rest(c, g: float) -> None:
    """The goat as the closet's prop picture shows it: standing still."""
    draw_goat(c, legs=[(0.0, 0.0)] * 4, sink=0.0, bob=0.0, dip=0.12, chew=0.0, tail=0.0, start=0.0, g=g)


def car_at_rest(c, g: float) -> None:
    """The car as the closet's prop picture shows it: parked, the bow still."""
    draw_car(c, lift=0.0, tilt=0.0, flat=0.0, ribbon=0.0, gleam=None, lamp=0.0, roll=0.0, g=g)


def _render(name, rows, frame, metadata, w, h):
    def render(out_dir: str | Path, **opts) -> List[Path]:
        return K.render_target(name, rows, frame, (int(w * PPU), int(h * PPU)), metadata, out_dir, **opts)

    return render


TARGETS = {
    GOAT: {"render": _render(GOAT, GOAT_ROWS, _goat_frame, GOAT_METADATA, GOAT_W, GOAT_H), "actor_metadata": GOAT_METADATA},
    CAR: {"render": _render(CAR, CAR_ROWS, _car_frame, CAR_METADATA, CAR_W, CAR_H), "actor_metadata": CAR_METADATA},
}
