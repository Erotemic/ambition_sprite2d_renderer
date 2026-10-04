"""Standalone generator for a side-profile dinosaur enemy.

This target renders a stylized raptor-like dinosaur enemy built for
side-scrolling gameplay readability. It emphasizes a clear profile silhouette
and multiple attack rows that imply distinct combat patterns:
- bite / lunge
- tail sweep
- pounce
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from ...authoring import rigdoc, shape_rig
from . import _solo_shape_rig as _rig
from . import _fx_piece
from ...authoring.part_flipbook import publish_rig_flipbook
from PIL import Image, ImageDraw
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_BASENAME = "raptor_stalker"
FRAME_SIZE = (240, 224)
WORK_FRAME_SIZE = (480, 448)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("walk", 8, 95),
    ("bite", 7, 80),
    ("tail_sweep", 7, 85),
    ("pounce", 8, 85),
    ("hurt", 4, 90),
    ("death", 8, 110),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_raptor_stalker",
        "display_name": "Raptor Stalker",
    },
    "body": {
        "body_plan": "BeastBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "locomotion_hint": "Run",
        "traits": ["enemy", "beast", "dinosaur", "stalker", "no_hands"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": {"height_px": None, "distance_px": None, "source": "raptor_pounce_animation"},
            "climb": None,
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
    "actions": {"default_preset": "striker_swipe"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.run": {"animation": "walk", "events": []},
        "action.melee.primary": {
            "animation": "bite",
            "events": [
                {"t": 0.34, "event": "hitbox_active_start", "source": "raptor_stalker.bite"},
                {"t": 0.56, "event": "hitbox_active_end", "source": "raptor_stalker.bite"},
            ],
        },
        "action.melee.tail_sweep": {
            "animation": "tail_sweep",
            "events": [
                {"t": 0.32, "event": "hitbox_active_start", "source": "raptor_stalker.tail_sweep"},
                {"t": 0.64, "event": "hitbox_active_end", "source": "raptor_stalker.tail_sweep"},
            ],
        },
        "action.special.pounce": {"animation": "pounce", "events": [{"t": 0.42, "event": "leap_commit", "source": "raptor_stalker.pounce"}]},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "raptor_stalker.geometry", "point": {"x": 166.0, "y": 60.0}},
        "mouth": {"source": "raptor_stalker.geometry", "point": {"x": 194.0, "y": 76.0}},
        "tail_base": {"source": "raptor_stalker.geometry", "point": {"x": 72.0, "y": 118.0}},
        "tail_tip": {"source": "raptor_stalker.geometry", "point": {"x": 32.0, "y": 106.0}},
        "foreclaw": {"source": "raptor_stalker.geometry", "point": {"x": 164.0, "y": 118.0}},
        "pounce_origin": {"source": "raptor_stalker.geometry", "point": {"x": 116.0, "y": 172.0}},
    },
    "tags": ["enemy", "beast", "dinosaur"],
}

OUTLINE = (18, 22, 18, 255)
SCALE_DARK = (44, 74, 50, 255)
SCALE = (84, 138, 90, 255)
SCALE_LIGHT = (132, 190, 126, 255)
BELLY = (224, 214, 166, 255)
BELLY_SHADOW = (170, 156, 120, 255)
ACCENT = (204, 92, 54, 255)
ACCENT_LIGHT = (248, 172, 112, 255)
CLAW = (242, 236, 218, 255)
EYE = (252, 232, 116, 255)
EYE_HOT = (255, 254, 232, 255)
SHADOW = (0, 0, 0, 42)
DUST = (214, 166, 118, 120)


@dataclass
class Pose:
    root_x: float = 0.0
    root_y: float = 0.0
    bob: float = 0.0
    lean: float = 0.0
    body_tilt: float = 0.0
    head_tilt: float = 0.0
    tail_sway: float = 0.0
    tail_lift: float = 0.0
    neck_extend: float = 0.0
    jaw_open: float = 0.0
    crest_sway: float = 0.0
    front_leg: float = 0.0
    back_leg: float = 0.0
    front_foot_lift: float = 0.0
    back_foot_lift: float = 0.0
    front_arm: float = 0.0
    back_arm: float = 0.0
    crouch: float = 0.0
    pounce: float = 0.0
    bite_lunge: float = 0.0
    sweep_arc: float = 0.0
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
        self.body_tilt = 0.0
        self.head_tilt = 0.0
        self.tail_sway = 0.0
        self.tail_lift = 0.0
        self.neck_extend = 0.0
        self.jaw_open = 0.0
        self.crest_sway = 0.0
        self.front_leg = 0.0
        self.back_leg = 0.0
        self.front_foot_lift = 0.0
        self.back_foot_lift = 0.0
        self.front_arm = 0.0
        self.back_arm = 0.0
        self.crouch = 0.0
        self.pounce = 0.0
        self.bite_lunge = 0.0
        self.sweep_arc = 0.0
        self.blink = False
        self.x_eyes = False
        self.dead = False

        if anim == "idle":
            self.bob = s * 1.4
            self.lean = s * 1.2
            self.body_tilt = s * 1.2
            self.head_tilt = -s * 1.8
            self.tail_sway = -s * 10.0
            self.tail_lift = abs(s) * 3.0
            self.front_arm = 8.0 + s * 4.0
            self.back_arm = -10.0 - s * 4.0
            self.front_leg = c * 1.0
            self.back_leg = -c * 1.0
            self.crest_sway = s * 5.0
            self.blink = frame_idx == nframes - 2
        elif anim == "walk":
            self.root_x = s * 2.4
            self.bob = abs(s) * 2.8 - 0.8
            self.lean = s * 2.6
            self.body_tilt = s * 1.8
            self.head_tilt = -s * 1.6
            self.tail_sway = -s * 14.0
            self.tail_lift = abs(s) * 4.0
            self.front_leg = 20.0 * s
            self.back_leg = -20.0 * s
            self.front_foot_lift = max(0.0, s) * 10.0
            self.back_foot_lift = max(0.0, -s) * 10.0
            self.front_arm = -10.0 * s + 6.0
            self.back_arm = 10.0 * s - 10.0
            self.crest_sway = -s * 8.0
        elif anim == "bite":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-8.0, 12.0, tt)
            self.bob = -hit * 4.0
            self.lean = _lerp(-10.0, 18.0, tt)
            self.body_tilt = _lerp(-6.0, 14.0, tt)
            self.head_tilt = _lerp(-8.0, 10.0, tt)
            self.neck_extend = _lerp(0.0, 34.0, tt)
            self.bite_lunge = _lerp(0.0, 32.0, tt)
            self.jaw_open = hit * 0.32
            self.tail_sway = _lerp(12.0, -14.0, tt)
            self.tail_lift = _lerp(6.0, -2.0, tt)
            self.front_leg = -10.0 - hit * 4.0
            self.back_leg = 14.0 + hit * 4.0
            self.front_arm = _lerp(-28.0, 18.0, tt)
            self.back_arm = _lerp(-12.0, 12.0, tt)
            self.crouch = _lerp(8.0, 0.0, tt)
            self.crest_sway = _lerp(10.0, -8.0, tt)
        elif anim == "tail_sweep":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-4.0, 6.0, tt)
            self.bob = -hit * 2.8
            self.lean = _lerp(16.0, -20.0, tt)
            self.body_tilt = _lerp(14.0, -16.0, tt)
            self.head_tilt = _lerp(10.0, -12.0, tt)
            self.tail_sway = _lerp(-42.0, 54.0, tt)
            self.tail_lift = 4.0 + hit * 4.0
            self.front_leg = 8.0 - hit * 4.0
            self.back_leg = -8.0 + hit * 4.0
            self.front_arm = _lerp(18.0, -10.0, tt)
            self.back_arm = _lerp(10.0, -18.0, tt)
            self.sweep_arc = hit
            self.crest_sway = _lerp(-8.0, 12.0, tt)
            self.jaw_open = hit * 0.14
        elif anim == "pounce":
            tt = _ease(t)
            launch = math.sin(tt * math.pi)
            self.root_x = _lerp(-12.0, 22.0, tt)
            self.root_y = -launch * 20.0
            self.pounce = launch
            self.bob = -launch * 5.0
            self.lean = _lerp(-18.0, 22.0, tt)
            self.body_tilt = _lerp(-10.0, 16.0, tt)
            self.head_tilt = _lerp(-8.0, 12.0, tt)
            self.neck_extend = launch * 14.0
            self.jaw_open = launch * 0.16
            self.tail_sway = _lerp(18.0, -24.0, tt)
            self.tail_lift = _lerp(10.0, -4.0, tt)
            self.front_leg = _lerp(-24.0, 28.0, tt)
            self.back_leg = _lerp(-18.0, 24.0, tt)
            self.front_foot_lift = launch * 20.0
            self.back_foot_lift = launch * 18.0
            self.front_arm = _lerp(-16.0, 22.0, tt)
            self.back_arm = _lerp(-20.0, 18.0, tt)
            self.crouch = _lerp(12.0, 0.0, tt)
            self.crest_sway = _lerp(14.0, -14.0, tt)
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 4.0) * (1.0 - t)
            self.root_x = shake * 4.0
            self.bob = -hit * 2.2
            self.lean = -16.0 * hit
            self.body_tilt = -10.0 * hit
            self.head_tilt = 18.0 * hit
            self.jaw_open = 0.24 * hit
            self.tail_sway = 12.0 * hit
            self.tail_lift = 6.0 * hit
            self.front_leg = 8.0 * hit
            self.back_leg = -6.0 * hit
            self.front_arm = 12.0 * hit
            self.back_arm = 10.0 * hit
        elif anim == "death":
            tt = _ease(t)
            self.root_x = tt * 16.0
            self.root_y = tt * 6.0
            self.bob = -tt * 4.0
            self.lean = -86.0 * tt
            self.body_tilt = -32.0 * tt
            self.head_tilt = 26.0 * tt
            self.neck_extend = tt * 6.0
            self.jaw_open = 0.28 * tt
            self.tail_sway = -40.0 * tt
            self.tail_lift = 10.0 * tt
            self.front_leg = _lerp(0.0, 28.0, tt)
            self.back_leg = _lerp(0.0, -24.0, tt)
            self.front_foot_lift = tt * 10.0
            self.back_foot_lift = tt * 8.0
            self.front_arm = _lerp(8.0, 44.0, tt)
            self.back_arm = _lerp(-10.0, -40.0, tt)
            self.crest_sway = tt * 10.0
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


# --- Drawn as a rig (``shape_rig``): each rigid piece is painted once at its
# rest place and turned into the frame; limbs are bones of a fixed length. ---

#: Where a bone piece's root sits on its rest canvas (work pixels).
_BONE_O: Point = (30.0, 30.0)


def _sp(p: Point) -> Point:
    return (p[0] * SUPER, p[1] * SUPER)


def _rest(key, paint, pivot: Point):
    """A piece painted at its rest place on a frame-sized canvas, cut to what
    it covers (``_solo_shape_rig.rest_piece``); ``pivot`` in work pixels."""
    return _rig.rest_piece((TARGET_NAME,) + tuple(key), _CANVAS, _sp(pivot), paint)


def _put(img: Image.Image, part, at: Point, deg: float, name: str) -> None:
    shape_rig.place(img, part, _sp(at), deg, name)


_HALVES: dict = {}


def _mirrored_half(key, paint, O: Point):
    """What ``paint(draw)`` paints symmetric about the vertical through ``O``
    (work pixels) as its left half and that half mirrored (the same raster
    transposed), each with its pivot at ``O``. The half is cut on whole
    frame pixels so the mirror survives the reduction."""
    cached = _HALVES.get(key)
    if cached is None:
        grid = SUPER * WORK_FRAME_SIZE[0] // FRAME_SIZE[0]
        canvas = Image.new("RGBA", (int(2 * O[0] * SUPER), int(2 * O[1] * SUPER)), (0, 0, 0, 0))
        paint(blending_draw(canvas))
        cx = int(O[0] * SUPER)
        assert cx % grid == 0, "the axis must fall on a frame pixel"
        box = canvas.getchannel("A").getbbox()
        x0 = box[0] - box[0] % grid
        half = (canvas.crop((x0, box[1], cx, box[3])), (float(cx - x0), O[1] * SUPER - box[1]))
        cached = _HALVES[key] = (half, _fx_piece.mirrored(half))
    return cached


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
_REST_ROOT: Point = (WORK_FRAME_SIZE[0] * 0.39, WORK_FRAME_SIZE[1] * 0.79)


def _frame_of(pose: Pose):
    """The body frame: its root, lean and ``P`` (body-local to canvas work px)."""
    root = (WORK_FRAME_SIZE[0] * 0.39 + pose.root_x, WORK_FRAME_SIZE[1] * 0.79 + pose.root_y + pose.bob)
    tilt = pose.lean

    def P(x: float, y: float) -> Point:
        rx, ry = _rot_local(x, y, tilt)
        return (root[0] + rx, root[1] + ry)

    return root, tilt, P


def _limb_points(pose: Pose, P) -> dict:
    """The painter's limb joints, (root, joint, end) per limb."""
    return {
        "back_leg": (P(-24, -34), P(-42 + pose.back_leg * 0.18, 2 - pose.crouch * 0.10), P(-52 + pose.back_leg * 0.16, 14 - pose.back_foot_lift)),
        "front_leg": (P(20, -30), P(34 + pose.front_leg * 0.18, 0 - pose.crouch * 0.10), P(44 + pose.front_leg * 0.16, 16 - pose.front_foot_lift)),
        "back_arm": (P(6, -92), P(12 + pose.back_arm * 0.16, -74 + pose.back_arm * 0.12), P(18 + pose.back_arm * 0.20, -56 + pose.back_arm * 0.14)),
        "front_arm": (P(20, -96), P(26 + pose.front_arm * 0.18, -76 + pose.front_arm * 0.14), P(36 + pose.front_arm * 0.20, -58 + pose.front_arm * 0.12)),
    }


def _joints(anim: str, frame_idx: int, nframes: int) -> dict:
    pose = Pose(anim, frame_idx, nframes)
    return _limb_points(pose, _frame_of(pose)[2])


def _P0(x: float, y: float) -> Point:
    return (_REST_ROOT[0] + x, _REST_ROOT[1] + y)


#: The tail at rest: its joints (body-local) and each segment's stroke width.
#: Pose values that reshape a piece, in steps: the body's crouch and the
#: neck's reach (each step is one raster).
_CROUCH_STEP = 12.0
_NECK_STEP = 12.0
_TAIL_REST = [(-34.0, -74.0), (-84.0, -82.0), (-126.0, -72.0), (-154.0, -54.0)]
_TAIL_W = [12.0, 9.5, 7.5]


class RaptorStalkerRenderer:
    def render_frame(self, anim: str, frame_idx: int, nframes: int) -> Image.Image:
        img = Image.new("RGBA", _CANVAS, (0, 0, 0, 0))
        pose = Pose(anim, frame_idx, nframes)
        root, tilt, P = _frame_of(pose)
        limbs = _limb_points(pose, P)

        # No baked ground drop shadow; the scene renderer owns contact shadows.
        self._draw_tail(img, P, pose, root, tilt)
        self._draw_leg(img, limbs["back_leg"], tilt, front=False, name="back_leg")
        self._draw_body(img, pose, root, tilt)
        self._draw_arm(img, limbs["back_arm"], front=False, name="back_arm")
        self._draw_head(img, P, pose, root, tilt)
        self._draw_leg(img, limbs["front_leg"], tilt, front=True, name="front_leg")
        self._draw_arm(img, limbs["front_arm"], front=True, name="front_arm")
        # Effects are pieces painted once at full size, placed and faded.
        if anim == "tail_sweep" and pose.sweep_arc > 0.2:
            self._draw_tail_fx(img, P, pose)
        if anim == "pounce" and pose.pounce > 0.16:
            self._draw_pounce_fx(img, P, pose, tilt)
        if anim == "bite" and pose.bite_lunge > 10:
            self._draw_bite_fx(img, P, pose)
        return _downsample(img)

    def _draw_tail(self, img: Image.Image, P, pose: Pose, root: Point, tilt: float) -> None:
        """Three tail bones of their rest lengths, each aimed at where the
        painter's swaying tail put its next joint; the blade rides the tip and
        the fins ride the body, lifted with the tail."""
        lift, sway = pose.tail_lift, pose.tail_sway
        targets = [
            P(-34, -74 + lift * 0.4),
            P(-84, -82 + lift * 0.9 + sway * 0.25),
            P(-126, -72 + lift * 1.1 + sway * 0.38),
            P(-154, -54 + lift * 0.8 + sway * 0.46),
        ]
        at = targets[0]
        for i in range(3):
            length = round(math.dist(_TAIL_REST[i], _TAIL_REST[i + 1]), 1)
            deg = _deg(at, targets[i + 1])
            _put(img, _bone_piece(("tail", i), length, _TAIL_W[i], SCALE_DARK, OUTLINE, 2.2), at, deg, f"tail{i}")
            at = (at[0] + length * math.cos(math.radians(deg)), at[1] + length * math.sin(math.radians(deg)))

        def blade(draw) -> None:
            d = _BONE_O
            _poly(draw, [(d[0] - 6, d[1] - 6), (d[0] + 24, d[1] - 2), (d[0] + 8, d[1] + 8)], ACCENT_LIGHT, OUTLINE, 0.8)

        _put(img, _rest(("blade",), blade, _BONE_O), at, 0.0, "tail_blade")
        P0 = _P0
        fins = {
            "fin1": ([P0(-92, -84), P0(-104, -102), P0(-82, -92)], 0.73),
            "fin2": ([P0(-70, -78), P0(-82, -96), P0(-60, -84)], 0.43),
        }
        for name, (pts, k) in fins.items():
            part = _rest((name,), lambda d, pts=pts: _poly(d, pts, ACCENT, OUTLINE, 0.7), _REST_ROOT)
            _put(img, part, P(0, lift * k), tilt, name)

    def _draw_body(self, img: Image.Image, pose: Pose, root: Point, tilt: float) -> None:
        crouch = _rig.q(pose.crouch, _CROUCH_STEP)

        def paint(draw) -> None:
            P = _P0
            torso = [P(-42, -94 - crouch), P(2, -122 - crouch), P(48, -110 - crouch), P(68, -80), P(50, -44), P(8, -30), P(-34, -42), P(-54, -68)]
            _poly(draw, torso, SCALE, OUTLINE, 1.6)
            back_plate = [P(-28, -92 - crouch), P(8, -110 - crouch), P(36, -98 - crouch), P(28, -70), P(-4, -60), P(-24, -72)]
            _poly(draw, back_plate, SCALE_LIGHT, OUTLINE, 1.0)
            _poly(draw, [P(-18, -74), P(20, -80), P(46, -68), P(34, -42), P(4, -34), P(-22, -46)], BELLY, OUTLINE, 0.9)
            _poly(draw, [P(10, -86), P(36, -88), P(52, -70), P(36, -54), P(12, -58)], BELLY_SHADOW, OUTLINE, 0.8)
            _poly(draw, [P(-8, -96 - crouch * 0.4), P(2, -108 - crouch * 0.4), P(14, -90), P(4, -84)], ACCENT, OUTLINE, 0.6)
            _poly(draw, [P(18, -100 - crouch * 0.4), P(30, -110 - crouch * 0.4), P(40, -92), P(28, -86)], ACCENT, OUTLINE, 0.6)
            _line(draw, [P(-16, -88), P(4, -38)], SCALE_DARK, 1.0)

        _put(img, _rest(("body", crouch), paint, _REST_ROOT), root, tilt, "body")

    def _draw_head(self, img: Image.Image, P, pose: Pose, root: Point, tilt: float) -> None:
        """The upright skull with its crest (turned by its sway), the neck
        (riding the body, in a few reaches), and the face as the snout, the
        lower jaw turned at its hinge, the upper teeth and the eyes (open,
        shut or crossed out)."""
        hx, hy = P(64 + pose.neck_extend + pose.bite_lunge * 0.35, -98 - pose.crouch * 0.4 + pose.head_tilt * 0.15)
        O = (60.0, 60.0)

        def skull(draw) -> None:
            x, y = O
            pts = [(x - 28, y - 14), (x - 8, y - 24), (x + 30, y - 20), (x + 60, y - 8), (x + 70, y + 2), (x + 54, y + 10), (x + 18, y + 14), (x - 18, y + 10), (x - 32, y - 2)]
            _poly(draw, pts, SCALE_LIGHT, OUTLINE, 1.2)

        def crest(draw) -> None:
            x, y = O
            _poly(draw, [(x - 4, y - 22), (x + 14, y - 36), (x + 30, y - 20), (x + 10, y - 10)], ACCENT, OUTLINE, 0.8)

        _put(img, _rest(("skull",), skull, O), (hx, hy), 0.0, "skull")
        # The crest's tip (20 px above its root) sways ``0.15 * crest_sway`` down.
        crest_root = (13.0, -16.0)
        crest_deg = -math.degrees(math.atan2(pose.crest_sway * 0.15, 20.0))
        _put(img, _rest(("crest",), crest, (O[0] + crest_root[0], O[1] + crest_root[1])), (hx + crest_root[0], hy + crest_root[1]), crest_deg, "crest")
        neck_extend = _rig.q(pose.neck_extend, _NECK_STEP)

        def neck(draw) -> None:
            P0 = _P0
            pts = [P0(32, -100), P0(54 + neck_extend * 0.35, -112), P0(66 + neck_extend * 0.2, -90), P0(40, -76)]
            _poly(draw, pts, SCALE, OUTLINE, 1.0)

        _put(img, _rest(("neck", neck_extend), neck, _REST_ROOT), root, tilt, "neck")
        look = "x" if pose.x_eyes else "shut" if pose.blink else "open"

        def snout(draw) -> None:
            x, y = O
            _poly(draw, [(x + 12, y - 2), (x + 64, y + 0), (x + 76, y + 4), (x + 56, y + 10), (x + 18, y + 8)], BELLY, OUTLINE, 0.8)

        def jaw(draw) -> None:
            x, y = O
            _poly(draw, [(x + 12, y + 8), (x + 46, y + 14), (x + 68, y + 12), (x + 50, y + 20), (x + 18, y + 16)], BELLY_SHADOW, OUTLINE, 0.8)
            for xoff in (24, 34, 46, 58, 68):
                _line(draw, [(x + xoff - 2, y + 12), (x + xoff + 2, y + 8)], CLAW, 0.7)

        def upper_teeth(draw) -> None:
            x, y = O
            _poly(draw, [(x + 42, y - 2), (x + 48, y - 2), (x + 46, y + 2)], OUTLINE, OUTLINE, 0.3)
            for xoff in (24, 34, 46, 58, 68):
                _line(draw, [(x + xoff, y + 6), (x + xoff - 4, y + 12)], CLAW, 0.7)

        def eyes(draw) -> None:
            x, y = O
            if look == "x":
                _line(draw, [(x + 2, y - 2), (x + 12, y + 8)], OUTLINE, 1.0)
                _line(draw, [(x + 2, y + 8), (x + 12, y - 2)], OUTLINE, 1.0)
            elif look == "shut":
                _line(draw, [(x + 2, y + 2), (x + 14, y + 2)], EYE_HOT, 1.0)
            else:
                _ellipse(draw, x + 8, y + 1, 6, 4, EYE, EYE_HOT, 0.8)
                _circle(draw, (x + 10, y + 1), 1.6, OUTLINE, OUTLINE, 0.5)

        _put(img, _rest(("snout",), snout, O), (hx, hy), 0.0, "snout")
        # The jaw's front (about 45 px out from its hinge) drops ``22 * jaw_open``.
        hinge = (15.0, 12.0)
        jaw_deg = math.degrees(math.atan2(22.0 * pose.jaw_open, 45.0))
        _put(img, _rest(("jaw",), jaw, (O[0] + hinge[0], O[1] + hinge[1])), (hx + hinge[0], hy + hinge[1]), jaw_deg, "jaw")
        _put(img, _rest(("upper_teeth",), upper_teeth, O), (hx, hy), 0.0, "upper_teeth")
        _put(img, _rest(("eyes", look), eyes, O), (hx, hy), 0.0, "eyes")

    def _draw_leg(self, img: Image.Image, chain, tilt: float, front: bool, name: str) -> None:
        """Thigh and shin bones of fixed length (bent at the painter's knee),
        the knee, the shin guard riding the shin and the toes riding the ankle."""
        hip, knee_ref, ankle = chain
        knee, l1, l2 = _limb(lambda J: J, name, hip, knee_ref, ankle)
        base = SCALE if front else SCALE_DARK
        light = SCALE_LIGHT if front else SCALE
        _put(img, _bone_piece((name, 1), l1, 8.4 if front else 7.6, base, OUTLINE, 2.0), hip, _deg(hip, knee), f"{name}_thigh")
        shin_deg = _deg(knee, ankle)
        _put(img, _bone_piece((name, 2), l2, 7.2 if front else 6.6, base, OUTLINE, 2.0), knee, shin_deg, f"{name}_shin")
        knee_part = _rest(("knee", front), lambda d: _ellipse(d, _BONE_O[0], _BONE_O[1], 7.0, 8.5, light, OUTLINE, 1.0), _BONE_O)
        _put(img, knee_part, knee, 0.0, f"{name}_knee")

        def guard(draw) -> None:
            x, y = _BONE_O
            # The painter's screen offsets, for the shin pointing straight
            # down; the piece turns with the shin.
            _poly(draw, [(x - 4, y), (x - 2, y + l2 - 8), (x + 7, y + l2 + 2), (x + 5, y + 4)], light, OUTLINE, 0.8)

        _put(img, _rest(("guard", front, l2), guard, _BONE_O), knee, shin_deg - 90.0, f"{name}_guard")
        def toes(draw) -> None:
            P0 = _P0
            a = P0(0, 0)
            toe = P0(20, 2) if front else P0(14, 4)
            back_toe = P0(-8, 4) if front else P0(-6, 6)
            _line(draw, [a, toe], CLAW, 2.5)
            _line(draw, [a, toe], OUTLINE, 0.9)
            _line(draw, [a, back_toe], CLAW, 1.8)
            _line(draw, [a, back_toe], OUTLINE, 0.8)
            claw2 = (toe[0] + 8, toe[1] + 3)
            _line(draw, [a, claw2], CLAW, 2.0)
            _line(draw, [a, claw2], OUTLINE, 0.8)
            sickle = (toe[0] + 4, toe[1] - 10)
            _line(draw, [toe, sickle], CLAW, 2.0)
            _line(draw, [toe, sickle], OUTLINE, 0.8)

        _put(img, _rest(("toes", front), toes, _REST_ROOT), ankle, tilt, f"{name}_toes")

    def _draw_arm(self, img: Image.Image, chain, front: bool, name: str) -> None:
        shoulder, elbow_ref, wrist = chain
        elbow, l1, l2 = _limb(lambda J: J, name, shoulder, elbow_ref, wrist)
        base = SCALE_LIGHT if front else SCALE
        _put(img, _bone_piece((name, 1), l1, 5.2 if front else 4.6, base, OUTLINE, 1.7), shoulder, _deg(shoulder, elbow), f"{name}_upper")
        _put(img, _bone_piece((name, 2), l2, 4.6 if front else 4.0, base, OUTLINE, 1.7), elbow, _deg(elbow, wrist), f"{name}_fore")
        _put(img, _rest(("elbow",), lambda d: _ellipse(d, _BONE_O[0], _BONE_O[1], 4.8, 6.0, SCALE_LIGHT, OUTLINE, 0.8), _BONE_O), elbow, 0.0, f"{name}_elbow")

        def claws(draw) -> None:
            w = _BONE_O
            for claw in ((w[0] + 8, w[1] + 4), (w[0] + 6, w[1] - 4)):
                _line(draw, [w, claw], CLAW, 1.6)
                _line(draw, [w, claw], OUTLINE, 0.6)

        _put(img, _rest(("claws",), claws, _BONE_O), wrist, 0.0, f"{name}_claws")

    def _draw_tail_fx(self, img: Image.Image, P, pose: Pose) -> None:
        """The tail sweep's arc: one piece around its centre, faded in and out."""
        O = (110.0, 80.0)

        def paint(draw) -> None:
            box = (_s(O[0] - 102), _s(O[1] - 70), _s(O[0] + 102), _s(O[1] + 70))
            draw.arc(box, 16, 164, fill=(*ACCENT[:3], 132), width=_s(6.5))
            draw.arc(box, 27, 153, fill=(255, 244, 208, 104), width=_s(2.0))

        opacity = min(1.0, 0.35 + pose.sweep_arc * 0.65)
        for half, side in zip(_mirrored_half(("fx_tail",), paint, O), ("l", "r")):
            _rig.place(img, half, _sp(P(-74, -70)), 0.0, f"fx_tail_{side}", opacity)

    def _draw_pounce_fx(self, img: Image.Image, P, pose: Pose, tilt: float) -> None:
        """The pounce's dust pool (one piece, faded in) and three shards (one
        piece, riding the body's turn)."""
        O = (40.0, 20.0)

        def pool(draw) -> None:
            _ellipse(draw, O[0], O[1], 26, 8, DUST, outline=(0, 0, 0, 0), width=0)

        def shard(draw) -> None:
            _poly(draw, [(O[0] - 8, O[1]), (O[0], O[1] - 10), (O[0] + 8, O[1])], (*ACCENT_LIGHT[:3], 148), (*ACCENT[:3], 120), 0.5)

        _rig.place(img, _rest(("fx_pounce_pool",), pool, O), _sp(P(-12, 12)), 0.0, "fx_pounce", pose.pounce)
        for k, dx in enumerate((-16, -4, 10)):
            _put(img, _rest(("fx_pounce_shard",), shard, O), P(-4 + dx, 10), tilt, f"fx_pounce_shard{k}")

    def _draw_bite_fx(self, img: Image.Image, P, pose: Pose) -> None:
        O = (40.0, 30.0)

        def paint(draw) -> None:
            box = (_s(O[0] - 34), _s(O[1] - 20), _s(O[0] + 34), _s(O[1] + 20))
            draw.arc(box, 180, 24, fill=(*ACCENT_LIGHT[:3], 180), width=_s(3.0))

        _put(img, _rest(("fx_bite",), paint, O), P(126, -84), 0.0, "fx_bite")


def _render_sheet(renderer: RaptorStalkerRenderer, out_dir: Path):
    frame_w, frame_h = FRAME_SIZE
    sheet_w = max(frames for _, frames, _ in ROWS) * frame_w
    sheet_h = len(ROWS) * frame_h
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    preview = Image.new("RGBA", (sheet_w + 128, sheet_h), (248, 246, 242, 255))
    pdraw = blending_draw(preview)
    canonical = None
    for row_idx, (name, nframes, _ms) in enumerate(ROWS):
        pdraw.text((8, row_idx * frame_h + 8), name, fill=(36, 36, 36, 255))
        for frame_idx in range(nframes):
            frame = renderer.render_frame(name, frame_idx, nframes)
            x = frame_idx * frame_w
            y = row_idx * frame_h
            sheet.alpha_composite(frame, (x, y))
            preview.alpha_composite(frame, (x + 128, y))
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
    """Render the raptor_stalker spritesheet bundle via the shared
    `sheet_build.build_sheet` pipeline (auto-cropped, with the
    runtime-compatible YAML+RON shape). See `bear_mauler.render` for
    the full rationale — same conversion."""
    from ...authoring.sheet_build import build_sheet
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    renderer = RaptorStalkerRenderer()
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
    parser = argparse.ArgumentParser(description="Render a side-profile raptor stalker enemy spritesheet.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_BASENAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
