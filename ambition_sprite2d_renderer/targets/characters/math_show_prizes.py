"""The goat and the car behind the doors of Hylbert's Hotel's game show (the
Math dimension's ballroom, `math_hotel_door_1..3`): the closets' prop
pictures (`targets/props/math_ballroom_props.py` `goat`, `car`), alive.

- `math_show_goat`: the goat, standing, unimpressed. `idle` chews, its beard
  wagging, and flicks its tail; `walk` steps in diagonal pairs; `hit` starts
  with its head flung up; `death` folds its legs, lies down and fades.
- `math_show_car`: the red convertible with a gold bow on it. `idle` is the
  showroom: the bow's ribbons stir, a gleam runs along the paint and the
  headlamp winks; `hit` rocks it on its springs; `death` lets its tyres down
  and it fades.

Each faces right, drawn at two frame pixels to each of the prop's room
pixels, on the prop's own numbers, with room at the top for the horns and the
bow.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image

from . import _art_cast_kit as K
from ..props._town_kit import Canvas
from ..props.math_hotel_props import GOLD

PPU = 2.0


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


# --------------------------------------------------------------------- goat

GOAT = "math_show_goat"
GOAT_W, GOAT_H = 100.0, 86.0
GOAT_G = GOAT_H - 2.0
GOAT_ROWS: List[Tuple[str, int, int]] = [("idle", 10, 140), ("walk", 8, 110), ("hit", 3, 90), ("death", 6, 140)]
GOAT_METADATA = _metadata(
    GOAT, "Goat", "quadruped", ["animal", "goat", "game_show"],
    "The goat behind a door of Hylbert's game show, the closet prop drawn to move: it chews, unimpressed, flicks its "
    "tail, ambles about the closet, starts when struck and lies down.",
)
COAT = (220, 214, 200)
COAT_HEAD = (226, 220, 206)
HORN = (150, 130, 100)
HOOF = (60, 50, 40)
BEARD = (200, 194, 180)


def draw_goat(c, *, legs, sink: float, bob: float, dip: float, chew: float, tail: float, start: float) -> None:
    """The prop's goat (facing east), posed. `legs`: each leg's (swing,
    lift), hind far, hind near, fore far, fore near; `sink` folds the legs
    and lowers the body; `dip` lowers the head; `chew` wags the beard; `tail`
    turns the tail up (degrees); `start` throws the head up and back."""
    g = GOAT_G
    by = sink * 22.0 - bob
    reach = 30.0 * (1.0 - sink * 0.8)
    hips = (22, 30, 56, 64)
    far = (True, False, True, False)
    for x, (swing, lift), is_far in sorted(zip(hips, legs, far), key=lambda leg: not leg[2]):
        top = g - 30 + by
        foot = (x + 2 + swing, min(g, top + reach) - lift)
        colour = tuple(int(v * 0.82) for v in COAT) if is_far else COAT
        c.put(c.mask(lambda p: p.line([(x + 2, top), foot], 4.0)), colour)
        c.put(c.mask(lambda p: p.rect(foot[0] - 2.5, foot[1] - 3, foot[0] + 2.5, foot[1])), HOOF)
    body = c.mask(lambda p: p.ellipse(44, g - 38 + by, 28, 16))
    c.put(body, COAT)
    c.tone(body * np.clip((c.y - (g - 54 + by)) / 40, 0, 1), -0.2)
    # The tail, turned about its root.
    root = (16, g - 42 + by)
    a = math.radians(-50 - tail)
    tip = (root[0] + 9.0 * math.cos(a) * -1, root[1] + 9.0 * math.sin(a))
    c.put(c.mask(lambda p: p.line([root, tip], 3)), BEARD)
    # The head, on its neck: everything of the prop's head moved by (hx, hy).
    hx, hy = -2.0 * start + 1.0 * dip, by + 7.0 * dip - 6.0 * start
    c.put(c.mask(lambda p: p.poly([(58, g - 46 + by), (70, g - 52 + by), (76 + hx, g - 50 + hy), (74 + hx, g - 40 + hy), (62, g - 32 + by)])), COAT)
    head = c.mask(lambda p: (p.poly([(66 + hx, g - 46 + hy), (76 + hx, g - 64 + hy), (90 + hx, g - 52 + hy), (86 + hx, g - 44 + hy), (74 + hx, g - 40 + hy)]),
                             p.ellipse(88 + hx, g - 47 + hy + chew * 0.6, 4, 4)))
    c.put(head, COAT_HEAD)
    c.put(c.mask(lambda p: (p.line([(74 + hx, g - 62 + hy), (68 + hx, g - 74 + hy), (62 + hx, g - 70 + hy)], 2.4),
                            p.line([(78 + hx, g - 63 + hy), (76 + hx, g - 76 + hy), (70 + hx, g - 74 + hy)], 2.4))), HORN)
    c.put(c.mask(lambda p: p.line([(84 + hx, g - 42 + hy), (84 + hx + chew, g - 34 + hy)], 2.2)), BEARD)
    eye = 0.6 if start > 0.5 else 0.0
    c.put(c.mask(lambda p: p.rect(78 + hx, g - 57 + hy - eye, 83 + hx, g - 55 + hy + eye)), (40, 30, 20))


def _goat_pose(anim: str, i: int, n: int) -> dict:
    loop = anim in {"idle", "walk"}
    t = K.phase(i, n, loop)
    still = [(0.0, 0.0)] * 4
    if anim == "idle":
        flick = _smooth((t - 0.7) / 0.1) * (1.0 - _smooth((t - 0.85) / 0.1))
        return dict(legs=still, sink=0.0, bob=0.0, dip=0.15 + 0.1 * math.sin(t * math.tau),
                    chew=1.4 * math.sin(t * math.tau * 4.0), tail=45.0 * flick, start=0.0)
    if anim == "walk":
        a = math.sin(t * math.tau)
        la, lb = max(0.0, math.cos(t * math.tau)) * 3.0, max(0.0, -math.cos(t * math.tau)) * 3.0
        legs = [(4.0 * a, la), (-4.0 * a, lb), (-4.0 * a, lb), (4.0 * a, la)]
        return dict(legs=legs, sink=0.0, bob=0.8 * abs(a), dip=0.0, chew=0.0, tail=10.0, start=0.0)
    if anim == "hit":
        k = [0.6, 1.0, 0.4][min(i, 2)]
        return dict(legs=[(-2.0 * k, 0.0)] * 4, sink=0.05 * k, bob=0.0, dip=0.0, chew=0.0, tail=40.0 * k, start=k)
    s = _smooth(t * 1.3)
    return dict(legs=[(3.0 * s, 0.0), (3.0 * s, 0.0), (-3.0 * s, 0.0), (-3.0 * s, 0.0)], sink=s, bob=0.0, dip=0.8 * s, chew=0.0, tail=0.0, start=0.0)


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
    "The car behind a door of Hylbert's game show, the closet prop drawn to move: a red convertible with a gold bow, "
    "its ribbons stirring and its paint gleaming; it rocks on its springs when struck.",
)
RED = (196, 40, 44)
GLASS = (170, 210, 230)
TRIM = (240, 230, 220)
TYRE = (30, 30, 34)
HUB = (200, 200, 210)
LAMP = (255, 240, 190)


def draw_car(c, *, lift: float, tilt: float, flat: float, ribbon: float, gleam: float | None, lamp: float, roll: float) -> None:
    """The prop's car, posed: `lift` raises the body on its springs, `tilt`
    noses it down (+) or up; `flat` lets the tyres down; `ribbon` stirs the
    bow's tails; `gleam` is where a light runs along the paint (0 to 1, or
    none); `lamp` lights the headlamp; `roll` turns the hubs (degrees)."""
    g = CAR_G
    wheel_r = 16.0 * (1.0 - 0.35 * flat)

    def y(x: float, v: float) -> float:
        return v - lift + tilt * (x - 105.0) / 105.0 * 3.0 + flat * 6.0

    pts = [(10, g - 18), (14, g - 40), (60, g - 44), (90, g - 66), (130, g - 66), (150, g - 44), (192, g - 40), (196, g - 18)]
    body_pts = [(x, y(x, v)) for x, v in pts]
    body = c.mask(lambda p: p.poly(body_pts))
    c.put(body, RED)
    c.tone(body * np.clip((c.y - (g - 66)) / 48, 0, 1), -0.25)
    if gleam is not None:
        gx = 10 + 186 * gleam
        band = np.clip(1.0 - np.abs(c.x - gx - (c.y - (g - 40)) * 0.4) / 6.0, 0, 1)
        c.light(body * band, (255, 255, 255), 0.55)
    c.put(c.mask(lambda p: p.poly([(96, y(96, g - 64)), (126, y(126, g - 64)), (138, y(138, g - 46)), (92, y(92, g - 46))])), GLASS, 0.8)
    c.put(c.mask(lambda p: p.poly([(14, y(14, g - 42)), (196, y(196, g - 42)), (196, y(196, g - 39)), (14, y(14, g - 39))])), TRIM)
    c.put(c.mask(lambda p: p.ellipse(192, y(192, g - 33), 3.2, 2.4)), LAMP if lamp > 0.5 else (230, 210, 170))
    if lamp > 0.5:
        # The wink: a soft light thrown ahead of the lamp.
        c.put(c.mask(lambda p: p.ellipse(199, y(192, g - 33), 7.0, 4.0), blur=1.5), LAMP, 0.45)
    for x in (46, 160):
        cy = g - wheel_r + 2.0 * flat
        c.put(c.mask(lambda p: p.ellipse(x, cy, 16, wheel_r)), TYRE)
        c.put(c.mask(lambda p: p.ellipse(x, cy, 7, 7 * wheel_r / 16)), HUB)
        a = math.radians(roll)
        c.put(c.mask(lambda p: p.line([(x - 5 * math.cos(a), cy - 5 * math.sin(a)), (x + 5 * math.cos(a), cy + 5 * math.sin(a))], 1.4)), (150, 150, 160))
    # The bow on top, its two tails stirring.
    bx, by = 112, y(112, g - 72)
    s = ribbon
    c.put(c.mask(lambda p: (p.poly([(bx, by), (bx - 22, by - 12 - 2 * s), (bx - 20, by + 10)]),
                            p.poly([(bx, by), (bx + 22, by - 12 + 2 * s), (bx + 20, by + 10)]), p.ellipse(bx, by, 5))), GOLD)
    c.put(c.mask(lambda p: (p.line([(bx, by), (bx - 5, by + 11), (bx - 8 - 3 * s, by + 22)], 2),
                            p.line([(bx, by), (bx + 6, by + 11), (bx + 10 + 3 * s, by + 22)], 2))), GOLD)


def _car_pose(anim: str, i: int, n: int) -> dict:
    t = K.phase(i, n, anim in {"idle", "walk"})
    if anim == "idle":
        gleam = t / 0.6 if t < 0.6 else None
        return dict(lift=0.0, tilt=0.0, flat=0.0, ribbon=math.sin(t * math.tau * 2.0), gleam=gleam, lamp=1.0 if 0.75 <= t < 0.85 else 0.0, roll=0.0)
    if anim == "walk":
        return dict(lift=0.5 * abs(math.sin(t * math.tau)), tilt=0.0, flat=0.0, ribbon=math.sin(t * math.tau), gleam=None, lamp=0.0, roll=-90.0 * t)
    if anim == "hit":
        k = [1.0, -0.7, 0.3][min(i, 2)]
        return dict(lift=2.0 * k, tilt=2.0 * k, flat=0.0, ribbon=2.0 * k, gleam=None, lamp=0.0, roll=0.0)
    s = _smooth(t * 1.3)
    return dict(lift=0.0, tilt=0.0, flat=s, ribbon=-s, gleam=None, lamp=0.0, roll=0.0)


def _car_frame(anim: str, i: int, n: int) -> Image.Image:
    c = Canvas(CAR, CAR_W, CAR_H, (0.0, 0.0), PPU)
    draw_car(c, **_car_pose(anim, i, n))
    image = c.image()
    if anim == "death":
        image = _fade(image, 1.0 - _smooth((K.phase(i, n, False) - 0.6) / 0.4))
    return image


def _render(name, rows, frame, metadata, w, h):
    def render(out_dir: str | Path, **opts) -> List[Path]:
        return K.render_target(name, rows, frame, (int(w * PPU), int(h * PPU)), metadata, out_dir, **opts)

    return render


TARGETS = {
    GOAT: {"render": _render(GOAT, GOAT_ROWS, _goat_frame, GOAT_METADATA, GOAT_W, GOAT_H), "actor_metadata": GOAT_METADATA},
    CAR: {"render": _render(CAR, CAR_ROWS, _car_frame, CAR_METADATA, CAR_W, CAR_H), "actor_metadata": CAR_METADATA},
}
