"""Standalone generator for a side-profile mantis lancer enemy.

Designed specifically for side-scrolling readability. The silhouette is a
forward-facing insectoid lancer with exaggerated blade arms and hind legs, and
it includes multiple attack animations that suggest distinct gameplay patterns:
long stab, sweeping slash, and pouncing leap.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from ...authoring import rigdoc, shape_rig
from . import _solo_shape_rig as _rig
from ...authoring.part_flipbook import publish_rig_flipbook
from PIL import Image, ImageDraw
from ambition_sprite2d_renderer.core.draw import blending_draw


RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_BASENAME = "mantis_lancer"
FRAME_SIZE = (240, 224)
WORK_FRAME_SIZE = (480, 448)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("walk", 8, 95),
    ("stab", 7, 80),
    ("slash", 7, 80),
    ("pounce", 8, 85),
    ("hurt", 4, 90),
    ("death", 8, 110),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_mantis_lancer",
        "display_name": "Mantis Lancer",
    },
    "body": {
        "body_plan": "InsectoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "locomotion_hint": "Walk",
        "traits": ["enemy", "insectoid", "blade_arms", "lancer"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": {"height_px": None, "distance_px": None, "source": "mantis_pounce_animation"},
            "climb": True,
            "crawl": None,
            "fly": None,
            "swim": None,
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {
            "talk": None,
            "trade": None,
            "carry": None,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "brute_lunge"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "action.melee.primary": {
            "animation": "stab",
            "events": [
                {"t": 0.36, "event": "hitbox_active_start", "source": "mantis_lancer.stab"},
                {"t": 0.60, "event": "hitbox_active_end", "source": "mantis_lancer.stab"},
            ],
        },
        "action.melee.sweep": {
            "animation": "slash",
            "events": [
                {"t": 0.30, "event": "hitbox_active_start", "source": "mantis_lancer.slash"},
                {"t": 0.62, "event": "hitbox_active_end", "source": "mantis_lancer.slash"},
            ],
        },
        "action.special.pounce": {"animation": "pounce", "events": [{"t": 0.40, "event": "leap_commit", "source": "mantis_lancer.pounce"}]},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "mantis_lancer.geometry", "point": {"x": 144.0, "y": 58.0}},
        "thorax": {"source": "mantis_lancer.geometry", "point": {"x": 112.0, "y": 96.0}},
        "blade_l": {"source": "mantis_lancer.geometry", "point": {"x": 95.0, "y": 102.0}},
        "blade_r": {"source": "mantis_lancer.geometry", "point": {"x": 172.0, "y": 100.0}},
        "blade_tip": {"source": "mantis_lancer.geometry", "point": {"x": 210.0, "y": 88.0}},
        "pounce_origin": {"source": "mantis_lancer.geometry", "point": {"x": 124.0, "y": 170.0}},
    },
    "tags": ["enemy", "insectoid", "lancer"],
}

OUTLINE = (16, 18, 18, 255)
CHITIN_DARK = (38, 56, 34, 255)
CHITIN = (72, 108, 62, 255)
CHITIN_LIGHT = (122, 164, 94, 255)
ACCENT = (196, 80, 44, 255)
ACCENT_LIGHT = (242, 156, 88, 255)
BONE = (218, 224, 194, 255)
SHADOW = (0, 0, 0, 42)
EYE = (255, 224, 118, 255)
EYE_HOT = (255, 250, 210, 255)


@dataclass
class Pose:
    root_x: float = 0.0
    root_y: float = 0.0
    bob: float = 0.0
    lean: float = 0.0
    thorax_tilt: float = 0.0
    head_tilt: float = 0.0
    abdomen_lift: float = 0.0
    crest_sway: float = 0.0
    front_blade: float = 0.0
    back_blade: float = 0.0
    front_leg: float = 0.0
    back_leg: float = 0.0
    front_foot_lift: float = 0.0
    back_foot_lift: float = 0.0
    stab_extension: float = 0.0
    crouch: float = 0.0
    airborne: float = 0.0
    slash_arc: float = 0.0
    mouth_open: float = 0.0
    blink: bool = False
    x_eyes: bool = False
    dead: bool = False

    def __init__(self, anim: str, frame_idx: int, nframes: int):
        t = frame_idx / max(1, nframes - 1)
        cyc = math.tau * frame_idx / max(1, nframes)
        s = math.sin(cyc)
        c = math.cos(cyc)

        self.root_x = 0.0
        self.root_y = 0.0
        self.bob = 0.0
        self.lean = 0.0
        self.thorax_tilt = 0.0
        self.head_tilt = 0.0
        self.abdomen_lift = 0.0
        self.crest_sway = 0.0
        self.front_blade = 0.0
        self.back_blade = 0.0
        self.front_leg = 0.0
        self.back_leg = 0.0
        self.front_foot_lift = 0.0
        self.back_foot_lift = 0.0
        self.stab_extension = 0.0
        self.crouch = 0.0
        self.airborne = 0.0
        self.slash_arc = 0.0
        self.mouth_open = 0.0
        self.blink = False
        self.x_eyes = False
        self.dead = False

        if anim == "idle":
            self.bob = s * 1.5
            self.lean = s * 1.4
            self.thorax_tilt = s * 1.2
            self.head_tilt = -s * 1.6
            self.abdomen_lift = abs(s) * 1.8
            self.front_blade = 12.0 + s * 4.0
            self.back_blade = -18.0 - s * 4.0
            self.front_leg = c * 1.2
            self.back_leg = -c * 1.2
            self.crest_sway = s * 6.0
            self.blink = frame_idx == nframes - 2
        elif anim == "walk":
            self.root_x = s * 2.4
            self.bob = abs(s) * 3.0 - 0.8
            self.lean = s * 3.2
            self.thorax_tilt = s * 2.2
            self.head_tilt = -s * 2.0
            self.abdomen_lift = abs(s) * 3.0
            self.front_leg = 22.0 * s
            self.back_leg = -20.0 * s
            self.front_blade = -8.0 * s + 10.0
            self.back_blade = 10.0 * s - 18.0
            self.front_foot_lift = max(0.0, s) * 9.0
            self.back_foot_lift = max(0.0, -s) * 9.0
            self.crest_sway = -s * 10.0
        elif anim == "stab":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-8.0, 12.0, tt)
            self.bob = -hit * 4.0
            self.lean = _lerp(-12.0, 16.0, tt)
            self.thorax_tilt = _lerp(-8.0, 14.0, tt)
            self.head_tilt = _lerp(-10.0, 6.0, tt)
            self.abdomen_lift = _lerp(4.0, -2.0, tt)
            self.front_blade = _lerp(-126.0, 16.0, tt)
            self.back_blade = _lerp(-26.0, 18.0, tt)
            self.front_leg = -8.0 - hit * 4.0
            self.back_leg = 14.0 + hit * 3.0
            self.stab_extension = _lerp(0.0, 44.0, tt)
            self.crouch = _lerp(6.0, 0.0, tt)
            self.mouth_open = 0.22 * hit
            self.crest_sway = _lerp(14.0, -10.0, tt)
        elif anim == "slash":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-4.0, 6.0, tt)
            self.bob = -hit * 3.0
            self.lean = _lerp(10.0, -18.0, tt)
            self.thorax_tilt = _lerp(8.0, -22.0, tt)
            self.head_tilt = _lerp(8.0, -14.0, tt)
            self.abdomen_lift = 2.0 + hit * 2.0
            self.front_blade = _lerp(54.0, -108.0, tt)
            self.back_blade = _lerp(18.0, -32.0, tt)
            self.front_leg = 10.0 - hit * 6.0
            self.back_leg = -10.0 + hit * 4.0
            self.slash_arc = hit
            self.crouch = 2.0
            self.mouth_open = 0.16 * hit
            self.crest_sway = _lerp(-12.0, 16.0, tt)
        elif anim == "pounce":
            tt = _ease(t)
            launch = math.sin(tt * math.pi)
            self.root_x = _lerp(-12.0, 20.0, tt)
            self.root_y = -launch * 20.0
            self.airborne = launch
            self.bob = -launch * 6.0
            self.lean = _lerp(-18.0, 22.0, tt)
            self.thorax_tilt = _lerp(-12.0, 18.0, tt)
            self.head_tilt = _lerp(-10.0, 10.0, tt)
            self.abdomen_lift = _lerp(8.0, -4.0, tt)
            self.front_blade = _lerp(-72.0, 30.0, tt)
            self.back_blade = _lerp(-48.0, 26.0, tt)
            self.front_leg = _lerp(-26.0, 22.0, tt)
            self.back_leg = _lerp(-18.0, 28.0, tt)
            self.front_foot_lift = launch * 20.0
            self.back_foot_lift = launch * 18.0
            self.stab_extension = launch * 16.0
            self.crouch = _lerp(10.0, 0.0, tt)
            self.crest_sway = _lerp(18.0, -18.0, tt)
            self.mouth_open = 0.2 * launch
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 4.0) * (1.0 - t)
            self.root_x = shake * 4.0
            self.bob = -hit * 2.5
            self.lean = -18.0 * hit
            self.thorax_tilt = -12.0 * hit
            self.head_tilt = 18.0 * hit
            self.front_blade = 22.0 * hit
            self.back_blade = 18.0 * hit
            self.front_leg = 10.0 * hit
            self.back_leg = -8.0 * hit
            self.abdomen_lift = 8.0 * hit
            self.mouth_open = 0.24 * hit
        elif anim == "death":
            tt = _ease(t)
            self.root_x = tt * 16.0
            self.root_y = tt * 6.0
            self.bob = -tt * 4.0
            self.lean = -88.0 * tt
            self.thorax_tilt = -36.0 * tt
            self.head_tilt = 28.0 * tt
            self.front_blade = _lerp(10.0, 72.0, tt)
            self.back_blade = _lerp(-16.0, -88.0, tt)
            self.front_leg = _lerp(0.0, 30.0, tt)
            self.back_leg = _lerp(0.0, -28.0, tt)
            self.front_foot_lift = tt * 8.0
            self.back_foot_lift = tt * 10.0
            self.abdomen_lift = _lerp(0.0, 12.0, tt)
            self.crouch = tt * 6.0
            self.crest_sway = tt * 12.0
            self.mouth_open = 0.22 * tt
            self.x_eyes = tt > 0.55
            self.dead = tt > 0.7


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(p: Point) -> Tuple[int, int]:
    return (_s(p[0]), _s(p[1]))


def _box(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _rot_local(x: float, y: float, deg: float) -> Point:
    rad = math.radians(deg)
    c = math.cos(rad)
    s = math.sin(rad)
    return (x * c - y * s, x * s + y * c)


def _poly(draw: ImageDraw.ImageDraw, pts: Sequence[Point], fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.0) -> None:
    ipts = [_pt(p) for p in pts]
    draw.polygon(ipts, fill=fill)
    if outline and width > 0:
        draw.line(ipts + [ipts[0]], fill=outline, width=max(1, _s(width)), joint="curve")


def _line(draw: ImageDraw.ImageDraw, pts: Sequence[Point], fill: RGBA, width: float = 1.0) -> None:
    draw.line([_pt(p) for p in pts], fill=fill, width=max(1, _s(width)), joint="curve")


def _ellipse(draw: ImageDraw.ImageDraw, cx: float, cy: float, rx: float, ry: float, fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.0) -> None:
    draw.ellipse(_box(cx, cy, rx, ry), fill=fill, outline=outline, width=max(1, _s(width)))


def _circle(draw: ImageDraw.ImageDraw, c: Point, r: float, fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.0) -> None:
    _ellipse(draw, c[0], c[1], r, r, fill, outline, width)


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


# --- Drawn as a rig (``shape_rig``): each rigid piece is painted once at its
# rest place and turned into the frame; limbs are bones of a fixed length. ---

#: Where a bone piece's root sits on its rest canvas (work pixels); a
#: piece reaching every way is painted about the canvas middle.
_BONE_O: Point = (30.0, 30.0)
_MID_O: Point = (WORK_FRAME_SIZE[0] / 2.0, WORK_FRAME_SIZE[1] / 2.0)


def _sp(p: Point) -> Point:
    return (p[0] * SUPER, p[1] * SUPER)


def _rest(key, paint, pivot: Point):
    """A piece painted at its rest place on a frame-sized canvas, cut to what
    it covers (``_solo_shape_rig.rest_piece``); ``pivot`` in work pixels."""
    return _rig.rest_piece((TARGET_NAME,) + tuple(key), _CANVAS, _sp(pivot), paint)


def _put(img: Image.Image, part, at: Point, deg: float, name: str) -> None:
    shape_rig.place(img, part, _sp(at), deg, name)


def _fx_layer(img: Image.Image, paint, name: str) -> None:
    """A per-frame effect (it changes every frame) as ONE raster: painted on
    its own canvas, cut to what it covers and placed at its corner."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    paint(blending_draw(layer))
    box = layer.getchannel("A").getbbox()
    if box is not None:
        shape_rig.place(img, (layer.crop(box), (0.0, 0.0)), (float(box[0]), float(box[1])), 0.0, name)


def _deg(a: Point, b: Point) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _ik(root: Point, target: Point, l1: float, l2: float, ref: Point) -> Point:
    """The middle joint of a two-bone limb (lengths ``l1``, ``l2``) from
    ``root`` to ``target``, on the side of ``ref`` (the painter's own joint)."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = max(1e-6, min(math.hypot(dx, dy), l1 + l2 - 1e-6))
    ux, uy = dx / d, dy / d
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    bx, by = root[0] + ux * a, root[1] + uy * a
    c1 = (bx - uy * h, by + ux * h)
    c2 = (bx + uy * h, by - ux * h)
    d1 = (c1[0] - ref[0]) ** 2 + (c1[1] - ref[1]) ** 2
    d2 = (c2[0] - ref[0]) ** 2 + (c2[1] - ref[1]) ** 2
    return c1 if d1 <= d2 else c2


def _bone_piece(key, length: float, width: float, fill: RGBA, centre: RGBA, centre_w: float, cap: bool = False):
    """A straight limb segment along +x from its root: the painter's thick
    stroke with its dark centre line (``cap`` rounds the root end)."""
    O = _BONE_O

    def paint(d) -> None:
        end = (O[0] + length, O[1])
        if cap:
            _circle(d, O, width / 2.0, fill, fill, 0.1)
        _line(d, [O, end], fill, width)
        if centre is not None:
            _line(d, [O, end], centre, centre_w)

    return _rest(("bone",) + tuple(key) + (length, width, fill, centre, centre_w, cap), paint, O)


_LIMB_LENGTHS: dict = {}


def _limb_lengths(chains) -> dict:
    """Each limb's bone lengths: the painter's own in the rest pose (the
    first frame). ``chains(J)`` names each limb's ``(root, joint, end)``."""
    if not _LIMB_LENGTHS:
        for limb, (a, b, c) in chains(_joints(ROWS[0][0], 0, ROWS[0][1])).items():
            _LIMB_LENGTHS[limb] = (round(math.dist(a, b), 1), round(math.dist(b, c), 1))
    return _LIMB_LENGTHS


def _limb(chains, limb: str, root: Point, ref: Point, end: Point) -> Tuple[Point, float, float]:
    """A two-bone limb from ``root`` to ``end`` of its rest bone lengths,
    bent toward the painter's joint ``ref``. Out of reach (the painter's
    position-shift limb grows), both bones lengthen to the next 3-pixel
    step: a stretched limb takes a few lengths. Returns (joint, l1, l2)."""
    l1, l2 = _limb_lengths(chains)[limb]
    d = math.dist(root, end)
    if d > l1 + l2 - 0.5:
        k = math.ceil((d + 0.5) / 3.0) * 3.0 / (l1 + l2)
        l1, l2 = round(l1 * k, 1), round(l2 * k, 1)
    return _ik(root, end, l1, l2, ref), l1, l2


_CANVAS = (WORK_FRAME_SIZE[0] * SUPER, WORK_FRAME_SIZE[1] * SUPER)
TARGET_NAME = TARGET_BASENAME
_REST_ROOT: Point = (WORK_FRAME_SIZE[0] * 0.40, WORK_FRAME_SIZE[1] * 0.78)


def _frame_of(pose: Pose):
    """The body frame: its root, lean and ``P`` (body-local to canvas work px)."""
    root = (WORK_FRAME_SIZE[0] * 0.40 + pose.root_x, WORK_FRAME_SIZE[1] * 0.78 + pose.root_y + pose.bob)
    tilt = pose.lean

    def P(x: float, y: float) -> Point:
        rx, ry = _rot_local(x, y, tilt)
        return (root[0] + rx, root[1] + ry)

    return root, tilt, P


def _limb_points(pose: Pose, P) -> dict:
    """The painter's limb joints: (root, joint, end) per limb, and each blade's tip."""
    return {
        "back_leg": (P(-40, -34), P(-66 + pose.back_leg * 0.18, -2 - pose.crouch * 0.15), P(-82 + pose.back_leg * 0.14, 11 - pose.back_foot_lift)),
        "front_leg": (P(6, -28), P(18 + pose.front_leg * 0.16, -4 - pose.crouch * 0.10), P(26 + pose.front_leg * 0.14, 12 - pose.front_foot_lift)),
        "back_blade": (
            P(2, -102 - pose.crouch * 0.3),
            P(12 + pose.back_blade * 0.10, -70 + pose.back_blade * 0.16),
            P(30 + pose.back_blade * 0.18, -48 + pose.back_blade * 0.18),
        ),
        "front_blade": (
            P(24, -112 - pose.crouch * 0.3),
            P(36 + pose.front_blade * 0.10 + pose.stab_extension * 0.12, -80 + pose.front_blade * 0.18),
            P(56 + pose.front_blade * 0.22 + pose.stab_extension * 0.30, -64 + pose.front_blade * 0.16),
        ),
    }


def _blade_tips(pose: Pose, P) -> dict:
    return {
        "back_blade": P(70 + pose.back_blade * 0.40 + pose.stab_extension * 0.18, -64 + pose.back_blade * 0.08),
        "front_blade": P(112 + pose.front_blade * 0.44 + pose.stab_extension * 0.70, -72 + pose.front_blade * 0.10),
    }


def _joints(anim: str, frame_idx: int, nframes: int) -> dict:
    pose = Pose(anim, frame_idx, nframes)
    return _limb_points(pose, _frame_of(pose)[2])


def _P0(x: float, y: float) -> Point:
    return (_REST_ROOT[0] + x, _REST_ROOT[1] + y)


_BLADE_REST: dict = {}


def _blade_rest(name: str) -> float:
    """The blade's angle (wrist to tip) in the rest pose: it is painted there."""
    if not _BLADE_REST:
        pose = Pose(ROWS[0][0], 0, ROWS[0][1])
        P = _frame_of(pose)[2]
        limbs, tips = _limb_points(pose, P), _blade_tips(pose, P)
        for key in tips:
            _BLADE_REST[key] = _deg(limbs[key][2], tips[key])
    return _BLADE_REST[name]


class MantisLancerRenderer:
    def render_frame(self, anim: str, frame_idx: int, nframes: int) -> Image.Image:
        img = Image.new("RGBA", _CANVAS, (0, 0, 0, 0))
        pose = Pose(anim, frame_idx, nframes)
        root, tilt, P = _frame_of(pose)
        limbs, tips = _limb_points(pose, P), _blade_tips(pose, P)

        # No baked ground drop shadow; the scene renderer owns contact shadows.
        self._draw_leg(img, limbs["back_leg"], pose.back_leg, tilt, front=False, name="back_leg")
        self._draw_abdomen(img, pose, root, tilt)
        self._draw_body(img, pose, root, tilt)
        self._draw_blade_arm(img, limbs["back_blade"], tips["back_blade"], front=False, name="back_blade")
        self._draw_head(img, P, pose)
        self._draw_leg(img, limbs["front_leg"], pose.front_leg, tilt, front=True, name="front_leg")
        self._draw_blade_arm(img, limbs["front_blade"], tips["front_blade"], front=True, name="front_blade")
        # Effects change every frame: one raster each.
        if anim == "slash" and pose.slash_arc > 0.2:
            _fx_layer(img, lambda d: self._draw_slash_fx(d, P, pose), "fx_slash")
        if anim == "pounce" and pose.airborne > 0.15:
            _fx_layer(img, lambda d: self._draw_pounce_fx(d, P, pose), "fx_pounce")
        return _downsample(img)

    def _draw_abdomen(self, img: Image.Image, pose: Pose, root: Point, tilt: float) -> None:
        lift = _rig.q(pose.abdomen_lift, 1.0)

        def paint(draw) -> None:
            P = _P0
            belly = [P(-78, -86 + lift), P(-104, -74 + lift), P(-114, -46 + lift), P(-100, -20), P(-72, -8), P(-42, -20), P(-34, -50), P(-48, -76 + lift)]
            _poly(draw, belly, CHITIN_DARK, OUTLINE, 1.5)
            _poly(draw, [P(-90, -66 + lift), P(-106, -58 + lift), P(-102, -40 + lift), P(-82, -34)], CHITIN, OUTLINE, 0.8)
            for off in (-94, -82, -70, -58):
                _line(draw, [P(off, -68 + lift * 0.6), P(off + 4, -22)], CHITIN_LIGHT, 0.7)
            _poly(draw, [P(-112, -52 + lift), P(-136, -60 + lift), P(-126, -40 + lift)], BONE, OUTLINE, 0.8)

        _put(img, _rest(("abdomen", lift), paint, _REST_ROOT), root, tilt, "abdomen")

    def _draw_body(self, img: Image.Image, pose: Pose, root: Point, tilt: float) -> None:
        crouch = _rig.q(pose.crouch, 1.0)

        def paint(draw) -> None:
            P = _P0
            _poly(draw, [P(-36, -104 - crouch), P(18, -128 - crouch), P(52, -106 - crouch), P(58, -72), P(30, -42), P(-12, -38), P(-44, -62)], CHITIN, OUTLINE, 1.7)
            _poly(draw, [P(-22, -102 - crouch), P(14, -118 - crouch), P(40, -102 - crouch), P(36, -72), P(8, -54), P(-20, -68)], CHITIN_LIGHT, OUTLINE, 1.1)
            _line(draw, [P(-8, -106 - crouch), P(6, -54)], CHITIN_DARK, 1.0)
            _poly(draw, [P(-18, -72), P(8, -78), P(22, -58), P(4, -40), P(-18, -44)], ACCENT, OUTLINE, 0.9)

        _put(img, _rest(("body", crouch), paint, _REST_ROOT), root, tilt, "body")

    def _draw_head(self, img: Image.Image, P, pose: Pose) -> None:
        """The upright head: one piece per face (crest sway, jaw, eyes)."""
        hx, hy = P(62 + pose.stab_extension * 0.35, -108 - pose.crouch + pose.head_tilt * 0.18)
        crest = _rig.q(pose.crest_sway, 2.0)
        mouth = _rig.q(pose.mouth_open, 0.05)
        blink, x_eyes = pose.blink, pose.x_eyes
        O = (60.0, 60.0)

        def paint(draw) -> None:
            x, y = O
            _poly(draw, [(x - 18, y - 12), (x + 8, y - 20), (x + 34, y - 10), (x + 42, y + 4), (x + 26, y + 16), (x - 2, y + 18), (x - 18, y + 8)], CHITIN_LIGHT, OUTLINE, 1.2)
            _poly(draw, [(x - 6, y - 18), (x + 16, y - 36 + crest * 0.2), (x + 34, y - 22), (x + 14, y - 8)], ACCENT, OUTLINE, 0.9)
            if x_eyes:
                _line(draw, [(x + 5, y - 3), (x + 15, y + 5)], OUTLINE, 1.0)
                _line(draw, [(x + 5, y + 5), (x + 15, y - 3)], OUTLINE, 1.0)
            elif blink:
                _line(draw, [(x + 4, y + 1), (x + 16, y + 1)], EYE_HOT, 1.0)
            else:
                _ellipse(draw, x + 10, y + 0, 6, 4, EYE, EYE_HOT, 0.8)
                _line(draw, [(x + 2, y - 6), (x + 16, y - 2)], OUTLINE, 0.8)
            _poly(draw, [(x + 16, y + 6), (x + 38, y + 8), (x + 48, y + 2), (x + 34, y + 14)], BONE, OUTLINE, 0.8)
            _poly(draw, [(x + 16, y + 10), (x + 34, y + 18 + mouth * 10), (x + 44, y + 14), (x + 28, y + 20 + mouth * 8)], BONE, OUTLINE, 0.8)
            for dy in (-6, 4):
                _line(draw, [(x + 10, y + dy), (x + 2, y + dy - 12)], BONE, 0.7)

        _put(img, _rest(("head", crest, mouth, blink, x_eyes), paint, O), (hx, hy), 0.0, "head")

    def _draw_leg(self, img: Image.Image, chain, swing: float, tilt: float, front: bool, name: str) -> None:
        """Thigh and shin bones of fixed length (bent at the painter's knee),
        the knee, the shin plate riding the shin and the toes riding the ankle."""
        hip, knee_ref, ankle = chain
        knee, l1, l2 = _limb(lambda J: J, name, hip, knee_ref, ankle)
        base = CHITIN if front else CHITIN_DARK
        _put(img, _bone_piece((name, 1), l1, 7.2 if front else 6.8, base, OUTLINE, 2.0), hip, _deg(hip, knee), f"{name}_thigh")
        shin_deg = _deg(knee, ankle)
        _put(img, _bone_piece((name, 2), l2, 6.4 if front else 6.0, base, OUTLINE, 2.0), knee, shin_deg, f"{name}_shin")
        knee_part = _rest(("knee",), lambda d: _ellipse(d, _BONE_O[0], _BONE_O[1], 6.5, 8.0, CHITIN_LIGHT, OUTLINE, 1.0), _BONE_O)
        _put(img, knee_part, knee, 0.0, f"{name}_knee")

        def plate(draw) -> None:
            x, y = _BONE_O
            # The painter's screen offsets, for the shin pointing straight
            # down; the piece turns with the shin.
            _poly(draw, [(x - 5, y), (x - 3, y + l2 - 6), (x + 6, y + l2 + 2), (x + 4, y + 4)], CHITIN_LIGHT if front else CHITIN, OUTLINE, 0.8)

        _put(img, _rest(("plate", front, l2), plate, _BONE_O), knee, shin_deg - 90.0, f"{name}_plate")
        sw = _rig.q(swing, 4.0)

        def toes(draw) -> None:
            P0 = _P0
            a = P0(0, 0)
            toe = P0(14 - sw * 0.02, 4) if front else P0(-12 - sw * 0.02, 5)
            _line(draw, [a, toe], BONE, 2.4)
            _line(draw, [a, toe], OUTLINE, 1.0)
            claw2 = (toe[0] + (7 if front else 5), toe[1] + 3)
            _line(draw, [a, claw2], BONE, 2.0)
            _line(draw, [a, claw2], OUTLINE, 0.9)

        _put(img, _rest(("toes", front, sw), toes, _REST_ROOT), ankle, tilt, f"{name}_toes")

    def _draw_blade_arm(self, img: Image.Image, chain, blade_tip: Point, front: bool, name: str) -> None:
        """Two bones bent at the painter's elbow, the elbow, and the blade:
        painted once at its rest angle (a few lengths), turned about the wrist
        to point at the painter's tip."""
        shoulder, elbow_ref, wrist = chain
        elbow, l1, l2 = _limb(lambda J: J, name, shoulder, elbow_ref, wrist)
        limb = CHITIN_LIGHT if front else CHITIN
        _put(img, _bone_piece((name, 1), l1, 7.2 if front else 6.4, limb, OUTLINE, 2.0), shoulder, _deg(shoulder, elbow), f"{name}_upper")
        _put(img, _bone_piece((name, 2), l2, 6.6 if front else 5.8, limb, OUTLINE, 2.0), elbow, _deg(elbow, wrist), f"{name}_fore")
        _put(img, _rest(("elbow",), lambda d: _ellipse(d, _BONE_O[0], _BONE_O[1], 6.5, 8.5, CHITIN_LIGHT, OUTLINE, 1.0), _BONE_O), elbow, 0.0, f"{name}_elbow")
        rest = _blade_rest(name)
        length = _rig.q(math.dist(wrist, blade_tip), 4.0)

        def blade(draw) -> None:
            w = _MID_O
            t = (w[0] + length * math.cos(math.radians(rest)), w[1] + length * math.sin(math.radians(rest)))
            _poly(draw, [w, (t[0] - 22, t[1] - 10), t, (t[0] - 14, t[1] + 14), (w[0] - 6, w[1] + 6)], BONE, OUTLINE, 1.0)
            _poly(draw, [(w[0] + 2, w[1] - 2), (t[0] - 18, t[1] - 2), (t[0] - 10, t[1] + 7), (w[0], w[1] + 2)], ACCENT_LIGHT if front else ACCENT, OUTLINE, 0.7)

        _put(img, _rest(("blade", front, length), blade, _MID_O), wrist, _deg(wrist, blade_tip) - rest, f"{name}_blade")

    def _draw_slash_fx(self, draw: ImageDraw.ImageDraw, P, pose: Pose) -> None:
        cx, cy = P(84, -76)
        box = (_s(cx - 92), _s(cy - 72), _s(cx + 92), _s(cy + 72))
        draw.arc(box, 182, 332, fill=(*ACCENT[:3], 136), width=_s(5.0 + pose.slash_arc * 2.0))
        draw.arc(box, 196, 320, fill=(255, 240, 210, 110), width=_s(2.0))

    def _draw_pounce_fx(self, draw: ImageDraw.ImageDraw, P, pose: Pose) -> None:
        c = P(-24, 9)
        _ellipse(draw, c[0], c[1], 18 + pose.airborne * 8, 6 + pose.airborne * 2, (*ACCENT[:3], 80), outline=(0, 0, 0, 0), width=0)
        for dx in (-18, -6, 10):
            shard = [P(-18 + dx, 8), P(-10 + dx, 0), P(-2 + dx, 8)]
            _poly(draw, shard, (*ACCENT_LIGHT[:3], 160), (*ACCENT[:3], 140), 0.5)


def _write_yaml(path: Path) -> None:
    lines = [
        f"target: {TARGET_BASENAME}",
        f"frame_width: {FRAME_SIZE[0]}",
        f"frame_height: {FRAME_SIZE[1]}",
        "rows:",
    ]
    for name, frames, ms in ROWS:
        lines.extend([
            f"  - name: {name}",
            f"    frames: {frames}",
            f"    frame_ms: {ms}",
        ])
    path.write_text("\n".join(lines) + "\n")


def _write_ron(path: Path) -> None:
    row_lines = []
    for name, frames, ms in ROWS:
        row_lines.append(f'        (name: "{name}", frames: {frames}, frame_ms: {ms}),')
    ron = [
        "(",
        f'    target: "{TARGET_BASENAME}",',
        f'    frame_width: {FRAME_SIZE[0]},',
        f'    frame_height: {FRAME_SIZE[1]},',
        "    rows: [",
        *row_lines,
        "    ],",
        ")",
    ]
    path.write_text("\n".join(ron) + "\n")


def _render_sheet(renderer: MantisLancerRenderer, out_dir: Path):
    frame_w, frame_h = FRAME_SIZE
    sheet_w = max(frames for _, frames, _ in ROWS) * frame_w
    sheet_h = len(ROWS) * frame_h
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    preview = Image.new("RGBA", (sheet_w + 112, sheet_h), (250, 248, 244, 255))
    pdraw = blending_draw(preview)
    canonical = None
    for row_idx, (name, nframes, _ms) in enumerate(ROWS):
        pdraw.text((8, row_idx * frame_h + 8), name, fill=(32, 32, 32, 255))
        for frame_idx in range(nframes):
            frame = renderer.render_frame(name, frame_idx, nframes)
            x = frame_idx * frame_w
            y = row_idx * frame_h
            sheet.alpha_composite(frame, (x, y))
            preview.alpha_composite(frame, (x + 112, y))
            if canonical is None and name == "idle" and frame_idx == 0:
                canonical = frame
    if canonical is None:
        canonical = renderer.render_frame(ROWS[0][0], 0, ROWS[0][1])
    spritesheet_path = out_dir / f"{TARGET_BASENAME}.png"
    yaml_path = out_dir / f"{TARGET_BASENAME}.yaml"
    ron_path = out_dir / f"{TARGET_BASENAME}.ron"
    preview_path = out_dir / f"{TARGET_BASENAME}_preview_labeled.png"
    canonical_path = out_dir / f"{TARGET_BASENAME}_canonical.png"
    sheet.save(spritesheet_path)
    preview.save(preview_path)
    canonical.save(canonical_path)
    _write_yaml(yaml_path)
    _write_ron(ron_path)
    return [spritesheet_path, yaml_path, ron_path, preview_path, canonical_path]


def render(out_dir: str | Path, **opts):
    """Render the mantis_lancer spritesheet bundle via the shared
    `sheet_build.build_sheet` pipeline (auto-cropped, with the
    runtime-compatible YAML+RON shape). See `bear_mauler.render` for
    the full rationale — same conversion."""
    from ...authoring.sheet_build import build_sheet
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    renderer = MantisLancerRenderer()
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_BASENAME,
        rows=ROWS,
        render_fn=renderer.render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=True,
        actor_metadata=ACTOR_METADATA,
    )
    parts = publish_rig_flipbook(TARGET_BASENAME, ROWS, renderer.render_frame, outputs, frame_transform, Path(out_dir))
    return [
        outputs["spritesheet"], outputs["yaml"], outputs["ron"],
        outputs["actor"], outputs["preview"], outputs["canonical"], outputs["canonical_transparent"],
    ] + list(parts.values())


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a side-profile mantis lancer enemy spritesheet.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_BASENAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
