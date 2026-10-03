"""Standalone generator for a Smart House character sprite sheet.

Concept:
- a literal house that is also "smart"
- the face is integrated into the front of the house
- round spectacles, expressive brows, thoughtful mouth
- chimney, roof, windows, and a light-bulb / academic vibe
- stompy little foundation-feet for side-scroller readability

Generator only. No registration or GUI wiring.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "smart_house"
# Files the tack-on installer copies into the sandbox sprites dir.
# Names match what `build_sheet` writes (target_spritesheet.{png,yaml,ron}).
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]
FRAME_SIZE = (320, 320)
WORK_FRAME_SIZE = (640, 640)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("walk", 8, 95),
    ("ponder", 6, 108),
    ("lecture", 6, 94),
    ("idea", 6, 102),
    ("ram", 7, 80),
    ("hurt", 4, 90),
    ("death", 8, 112),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_smart_house",
        "display_name": "Smart House",
    },
    "body": {
        "body_plan": "PropActor",
        "body_kind": "PropLike",
        "mass_class": "Heavy",
        "locomotion_hint": "StompyWalk",
        "traits": ["story", "prop_actor", "building", "speaker", "mobile_house"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "crawl": None,
            "fly": None,
            "swim": None,
            "use_lifts": None,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.stompy_walk": {"animation": "walk", "events": []},
        "interaction.ponder": {"animation": "ponder", "events": []},
        "interaction.lecture": {
            "animation": "lecture",
            "events": [
                {"t": 0.42, "event": "speech_cue", "source": "smart_house.lecture"}
            ],
        },
        "interaction.idea": {
            "animation": "idea",
            "events": [{"t": 0.48, "event": "vfx_cue", "source": "smart_house.idea"}],
        },
        "action.special.ram": {
            "animation": "ram",
            "events": [
                {
                    "t": 0.44,
                    "event": "hitbox_active_start",
                    "source": "smart_house.ram",
                },
                {"t": 0.62, "event": "hitbox_active_end", "source": "smart_house.ram"},
            ],
        },
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "door_center": {
            "source": "smart_house.geometry",
            "point": {"x": 160.0, "y": 210.0},
        },
        "face_center": {
            "source": "smart_house.geometry",
            "point": {"x": 160.0, "y": 132.0},
        },
        "speech_bubble": {
            "source": "smart_house.geometry",
            "point": {"x": 160.0, "y": 48.0},
        },
        "chimney": {"source": "smart_house.geometry", "point": {"x": 112.0, "y": 48.0}},
        "lightbulb": {
            "source": "smart_house.geometry",
            "point": {"x": 160.0, "y": 38.0},
        },
        "book_origin": {
            "source": "smart_house.geometry",
            "point": {"x": 114.0, "y": 172.0},
        },
        "paper_origin": {
            "source": "smart_house.geometry",
            "point": {"x": 210.0, "y": 172.0},
        },
        "ram_front": {
            "source": "smart_house.geometry",
            "point": {"x": 248.0, "y": 146.0},
        },
    },
    "tags": ["story", "prop_actor", "speaker", "mobile_house"],
}

OUTLINE = (30, 24, 20, 255)
WOOD = (198, 162, 104, 255)
WOOD_SHADE = (160, 127, 79, 255)
WOOD_DARK = (118, 91, 58, 255)
ROOF = (96, 56, 48, 255)
ROOF_HI = (136, 84, 72, 255)
CHIMNEY = (154, 96, 84, 255)
WINDOW = (160, 214, 238, 255)
WINDOW_SHADE = (114, 174, 202, 255)
GLASS_HI = (232, 246, 250, 255)
STONE = (146, 150, 164, 255)
STONE_SHADE = (105, 110, 124, 255)
DOOR = (110, 76, 48, 255)
DOOR_SHADE = (86, 56, 36, 255)
BRASS = (214, 178, 86, 255)
EYE = (244, 246, 250, 255)
PUPIL = (44, 40, 48, 255)
BROW = (78, 58, 44, 255)
TONGUE = (202, 112, 118, 255)
MOUTH = (88, 54, 58, 255)
BOOK = (84, 112, 184, 255)
BOOK_PAPER = (236, 232, 212, 255)
BULB = (252, 232, 140, 255)
BULB_GLOW = (255, 238, 164, 140)
PAPER = (238, 228, 196, 255)
SMOKE = (188, 192, 204, 130)
DUST = (132, 112, 84, 130)
FX = (255, 232, 156, 150)


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(p: Point) -> Tuple[int, int]:
    return (_s(p[0]), _s(p[1]))


def _box(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _rot(x: float, y: float, deg: float) -> Point:
    rad = math.radians(deg)
    c = math.cos(rad)
    s = math.sin(rad)
    return (x * c - y * s, x * s + y * c)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _poly(
    draw: ImageDraw.ImageDraw,
    pts: Sequence[Point],
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    ipts = [_pt(p) for p in pts]
    draw.polygon(ipts, fill=fill)
    if outline and width > 0:
        draw.line(
            ipts + [ipts[0]], fill=outline, width=max(1, _s(width)), joint="curve"
        )


def _line(
    draw: ImageDraw.ImageDraw, pts: Sequence[Point], fill: RGBA, width: float = 1.0
) -> None:
    draw.line([_pt(p) for p in pts], fill=fill, width=max(1, _s(width)), joint="curve")


def _ellipse(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(
        _box(cx, cy, rx, ry), fill=fill, outline=outline, width=max(1, _s(width))
    )


def _circle(
    draw: ImageDraw.ImageDraw,
    p: Point,
    r: float,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    _ellipse(draw, p[0], p[1], r, r, fill, outline, width)


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


class Pose:
    def __init__(self, anim: str, frame_idx: int, nframes: int) -> None:
        t = frame_idx / max(1, nframes - 1)
        cyc = math.tau * frame_idx / max(1, nframes)
        s = math.sin(cyc)
        c = math.cos(cyc)

        self.root_x = 0.0
        self.root_y = 0.0
        self.bob = 0.0
        self.tilt = 0.0
        self.roof_tilt = 0.0
        self.chimney = 0.0
        self.brow = 0.0
        self.mouth_open = 0.0
        self.left_leg = 0.0
        self.right_leg = 0.0
        self.left_lift = 0.0
        self.right_lift = 0.0
        self.left_arm = 0.0
        self.right_arm = 0.0
        self.book = 0.0
        self.paper = 0.0
        self.idea = 0.0
        self.smoke = 0.0
        self.impact = 0.0
        self.dead_t = 0.0
        self.blink = False
        self.x_eye = False

        if anim == "idle":
            self.bob = s * 1.6
            self.tilt = s * 1.1
            self.roof_tilt = s * 1.6
            self.chimney = -s * 2.0
            self.brow = s * 1.0
            self.left_arm = -2.0 + s * 2.0
            self.right_arm = 2.0 - s * 1.8
            self.smoke = 0.35 + max(0.0, s) * 0.3
            self.blink = frame_idx == nframes - 2
        elif anim == "walk":
            self.root_x = s * 2.0
            self.bob = abs(s) * 2.8 - 0.5
            self.tilt = s * 2.0
            self.roof_tilt = -s * 2.6
            self.left_leg = -20.0 * s
            self.right_leg = 20.0 * s
            self.left_lift = max(0.0, -s) * 7.0
            self.right_lift = max(0.0, s) * 7.0
            self.left_arm = 14.0 * s
            self.right_arm = -12.0 * s
            self.smoke = 0.25 + abs(s) * 0.25
        elif anim == "ponder":
            self.bob = s * 1.1
            self.tilt = -1.0 + s * 0.8
            self.roof_tilt = s * 0.8
            self.brow = -4.0 + max(0.0, s) * 6.0
            self.left_arm = _lerp(0.0, 26.0, math.sin(t * math.pi))
            self.book = math.sin(t * math.pi)
            self.mouth_open = 0.04
            self.smoke = 0.25
        elif anim == "lecture":
            self.bob = s * 1.2
            self.tilt = s * 1.5
            self.roof_tilt = s * 1.2
            self.left_arm = -14.0 + s * 8.0
            self.right_arm = 28.0 - s * 6.0
            self.paper = 0.6 + max(0.0, s) * 0.35
            self.brow = -2.0
            self.mouth_open = 0.12 + max(0.0, s) * 0.06
            self.smoke = 0.22
        elif anim == "idea":
            tt = _ease(t)
            self.bob = -math.sin(tt * math.pi) * 1.8
            self.tilt = _lerp(-2.0, 2.0, tt)
            self.roof_tilt = _lerp(-2.0, 3.0, tt)
            self.left_arm = _lerp(-4.0, 16.0, tt)
            self.right_arm = _lerp(-6.0, 18.0, tt)
            self.idea = math.sin(tt * math.pi)
            self.brow = _lerp(4.0, -6.0, tt)
            self.mouth_open = 0.10 + self.idea * 0.06
            self.smoke = 0.18
        elif anim == "ram":
            tt = _ease(t)
            hit = math.sin(tt * math.pi)
            self.root_x = _lerp(-8.0, 24.0, tt)
            self.bob = -hit * 2.0
            self.tilt = _lerp(-6.0, 12.0, tt)
            self.roof_tilt = _lerp(-8.0, 16.0, tt)
            self.left_leg = _lerp(-8.0, 10.0, tt)
            self.right_leg = _lerp(10.0, -4.0, tt)
            self.left_lift = _lerp(0.0, 4.0, tt)
            self.left_arm = _lerp(-10.0, 18.0, tt)
            self.right_arm = _lerp(10.0, -18.0, tt)
            self.brow = -8.0
            self.mouth_open = 0.12
            self.impact = hit
            self.smoke = 0.12
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
            self.root_x = shake * 3.0 - hit * 3.0
            self.bob = -hit * 2.0
            self.tilt = -8.0 * hit
            self.roof_tilt = -10.0 * hit
            self.left_arm = 12.0 * hit
            self.right_arm = 14.0 * hit
            self.mouth_open = 0.16 * hit
            self.smoke = 0.10
        elif anim == "death":
            tt = _ease(t)
            self.dead_t = tt
            self.root_x = tt * 18.0
            self.root_y = tt * 12.0
            self.bob = -tt * 4.0
            self.tilt = -72.0 * tt
            self.roof_tilt = -20.0 * tt
            self.left_leg = _lerp(-2.0, 20.0, tt)
            self.right_leg = _lerp(2.0, -18.0, tt)
            self.left_arm = _lerp(0.0, 26.0, tt)
            self.right_arm = _lerp(0.0, -30.0, tt)
            self.smoke = 0.4
            self.x_eye = tt > 0.55


# ---- Pieces ------------------------------------------------------------------
#
# The house is drawn as a rig: each rigid thing (the walls, the face, the
# door, the foundation, a bone, a foot, a hand, a prop) is painted ONCE on a
# scratch canvas with its anchor at ``HOME``, cut to what it covers, and placed
# (and turned) through ``shape_rig``. Things that ride the house are painted
# in its own (level) frame and turned with it. The roof and the chimney bend
# with the pose: one piece per whole degree of their bend.

#: The anchor on the scratch canvas (work pixels); the canvas is twice it.
HOME = (300.0, 300.0)
_PIECES: Dict[tuple, object] = {}


def _piece(key: tuple, paint):
    """``(raster, anchor)``: what ``paint(draw)`` paints with its anchor at
    ``HOME``, cut to its box; ``None`` when it paints nothing. ``key`` must
    name everything ``paint`` reads."""
    if key not in _PIECES:
        canvas = Image.new("RGBA", (int(2 * HOME[0] * SUPER), int(2 * HOME[1] * SUPER)), (0, 0, 0, 0))
        paint(blending_draw(canvas))
        box = canvas.getchannel("A").getbbox()
        _PIECES[key] = None if box is None else (canvas.crop(box), (HOME[0] * SUPER - box[0], HOME[1] * SUPER - box[1]))
    return _PIECES[key]


def _put(img: Image.Image, key: tuple, paint, at: Point, name: str, degrees: float = 0.0) -> None:
    """Place the piece ``key`` with its anchor at ``at`` (work pixels)."""
    part = _piece(key, paint)
    if part is not None:
        shape_rig.place(img, part, (at[0] * SUPER, at[1] * SUPER), degrees, name)


def _home(x: float, y: float, extra: float = 0.0) -> Point:
    """The house's own frame at ``HOME``, level: a piece's ``P``."""
    rx, ry = _rot(x, y, extra)
    return (HOME[0] + rx, HOME[1] + ry)


def _draw_leg(img: Image.Image, hip: Point, ang: float, lift: float, *, front: bool) -> Point:
    """A stone leg: thigh and shin bones and the foot piece."""
    seg1 = 22
    seg2 = 26
    knee = (
        hip[0] + seg1 * math.cos(math.radians(ang)),
        hip[1] + seg1 * math.sin(math.radians(ang)),
    )
    foot = (
        knee[0] + seg2 * math.cos(math.radians(ang + 8)),
        knee[1] + seg2 * math.sin(math.radians(ang + 8)) - lift,
    )
    col = STONE if front else STONE_SHADE
    side = "near" if front else "far"
    width = 8.0 if front else 7.0
    hx, hy = HOME
    _put_ink_bone(img, hip, knee, col, width, 1.1, f"{side}_thigh")
    _put_ink_bone(img, knee, foot, col, width, 1.1, f"{side}_shin")
    _put(
        img,
        ("foot", front),
        lambda d: _ellipse(d, hx, hy, 10.0, 4.5, STONE_SHADE if front else (90, 94, 104, 255), OUTLINE, 0.7),
        (foot[0], foot[1] + 4),
        f"{side}_foot",
    )
    return foot


def _put_ink_bone(img: Image.Image, a: Point, b: Point, fill: RGBA, width: float, ink: float, name: str) -> None:
    """A bone from ``a`` to ``b``: a ``fill`` stroke with an ``ink`` line down
    its middle, one piece per (quarter-pixel) length, turned to the bone."""
    length = round(math.hypot(b[0] - a[0], b[1] - a[1]) * 4) / 4
    hx, hy = HOME

    def paint(d) -> None:
        _line(d, [(hx, hy), (hx + length, hy)], fill, width)
        _line(d, [(hx, hy), (hx + length, hy)], OUTLINE, ink)

    _put(img, ("bone", length, fill, width, ink), paint, a, name, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))


def _draw_arm(img: Image.Image, shoulder: Point, ang: float, length: float, *, front: bool) -> Point:
    """A straight wooden arm (one bone) and its brass hand."""
    hand = (
        shoulder[0] + length * math.cos(math.radians(ang)),
        shoulder[1] + length * math.sin(math.radians(ang)),
    )
    col = WOOD_SHADE if front else WOOD_DARK
    side = "near" if front else "far"
    _put_ink_bone(img, shoulder, hand, col, 6.8 if front else 5.8, 0.9, f"{side}_arm")
    hx, hy = HOME
    _put(img, ("hand", front), lambda d: _circle(d, (hx, hy), 4.4 if front else 3.8, BRASS, OUTLINE, 0.5), hand, f"{side}_hand")
    return hand


def _paint_walls(d) -> None:
    P = _home
    _poly(d, [P(-76, -168), P(84, -168), P(84, -14), P(-76, -14)], WOOD, OUTLINE, 1.4)
    for y in [-142, -114, -86, -58, -30]:
        _line(d, [P(-72, y), P(80, y)], WOOD_SHADE, 1.0)
    for x in [-46, -6, 34, 66]:
        _line(d, [P(x, -164), P(x, -18)], WOOD_SHADE, 0.7)


def _paint_roof(d, roof_tilt: float) -> None:
    P = _home
    _poly(d, [P(-96, -170), P(4, -244, roof_tilt), P(112, -170)], ROOF, OUTLINE, 1.4)
    _line(d, [P(-86, -170), P(6, -224, roof_tilt), P(100, -170)], ROOF_HI, 2.0)
    for frac in [0.12, 0.28, 0.44, 0.60, 0.76]:
        ax = _lerp(-86, 92, frac)
        _line(d, [P(ax, -170), P(ax - 22, -186 - frac * 16, roof_tilt * 0.8)], ROOF_HI, 0.8)


def _paint_face(d, x_eye: bool, blink: bool, brow: float) -> None:
    """Windows with spectacles, the eyes and the brows."""
    P = _home
    win_l = [P(-54, -136), P(-8, -136), P(-8, -94), P(-54, -94)]
    win_r = [P(8, -136), P(54, -136), P(54, -94), P(8, -94)]
    _poly(d, win_l, WINDOW, OUTLINE, 1.0)
    _poly(d, win_r, WINDOW, OUTLINE, 1.0)
    for pts in [win_l, win_r]:
        x0, y0 = pts[0]
        x1, _ = pts[1]
        _, y1 = pts[2]
        _line(d, [((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], WINDOW_SHADE, 0.8)
        _line(d, [(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], WINDOW_SHADE, 0.8)
    _line(d, [P(-48, -132), P(-18, -102)], GLASS_HI, 0.8)
    _line(d, [P(14, -132), P(44, -102)], GLASS_HI, 0.8)
    eye_l = P(-31, -114)
    eye_r = P(31, -114)
    # The lenses are rims only. The old fill of alpha 0 ERASED the window
    # and the wall under it (a hole through the house), which a rig of
    # pieces cannot replay and which was never the drawing's intent.
    _ellipse(d, eye_l[0], eye_l[1], 16.0, 12.0, None, OUTLINE, 0.9)
    _ellipse(d, eye_r[0], eye_r[1], 16.0, 12.0, None, OUTLINE, 0.9)
    _line(d, [P(-15, -114), P(15, -114)], OUTLINE, 0.8)
    if x_eye:
        _line(d, [P(-38, -122), P(-24, -106)], OUTLINE, 0.8)
        _line(d, [P(-38, -106), P(-24, -122)], OUTLINE, 0.8)
        _line(d, [P(24, -122), P(38, -106)], OUTLINE, 0.8)
        _line(d, [P(24, -106), P(38, -122)], OUTLINE, 0.8)
    elif blink:
        _line(d, [P(-38, -114), P(-24, -114)], BROW, 0.9)
        _line(d, [P(24, -114), P(38, -114)], BROW, 0.9)
    else:
        _ellipse(d, eye_l[0], eye_l[1], 7.0, 5.6, EYE, OUTLINE, 0.5)
        _ellipse(d, eye_r[0], eye_r[1], 7.0, 5.6, EYE, OUTLINE, 0.5)
        _circle(d, (eye_l[0] + 1, eye_l[1]), 1.4, PUPIL, PUPIL, 0.1)
        _circle(d, (eye_r[0] + 1, eye_r[1]), 1.4, PUPIL, PUPIL, 0.1)
    _line(d, [P(-44, -134 + brow), P(-20, -138 + brow)], BROW, 1.0)
    _line(d, [P(20, -138 + brow), P(44, -134 + brow)], BROW, 1.0)


def _paint_door(d, mouth_open: float) -> None:
    """The brass knocker nose and the door mouth."""
    P = _home
    _ellipse(d, P(0, -86)[0], P(0, -86)[1], 5.0, 5.0, BRASS, OUTLINE, 0.5)
    _poly(d, [P(-24, -72), P(24, -72), P(24, -12), P(-24, -12)], DOOR, OUTLINE, 1.0)
    _line(d, [P(0, -68), P(0, -14)], DOOR_SHADE, 0.8)
    if mouth_open > 0.03:
        _ellipse(d, P(0, -40)[0], P(0, -40)[1], 11.0, 6.0 + mouth_open * 14.0, MOUTH, OUTLINE, 0.5)
        _poly(d, [P(-4, -34), P(0, -28), P(4, -34)], TONGUE, OUTLINE, 0.3)
    else:
        _line(d, [P(-12, -40), P(0, -36), P(12, -40)], MOUTH, 0.9)
    _circle(d, P(14, -38), 2.4, BRASS, OUTLINE, 0.3)


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new(
        "RGBA", (WORK_FRAME_SIZE[0] * SUPER, WORK_FRAME_SIZE[1] * SUPER), (0, 0, 0, 0)
    )
    pose = Pose(anim, frame_idx, nframes)
    hx, hy = HOME

    root = (
        WORK_FRAME_SIZE[0] * 0.48 + pose.root_x,
        WORK_FRAME_SIZE[1] * 0.75 + pose.root_y + pose.bob,
    )
    body_ang = pose.tilt

    def P(x: float, y: float, extra: float = 0.0) -> Point:
        rx, ry = _rot(x, y, body_ang + extra)
        return (root[0] + rx, root[1] + ry)

    def house(key: tuple, paint, name: str) -> None:
        """A piece painted in the house's own frame, turned with it."""
        _put(img, key, paint, root, name, body_ang)

    # far leg first
    _draw_leg(img, P(18, -12), 94 + pose.right_leg, pose.right_lift, front=False)
    # far arm
    far_hand = _draw_arm(img, P(60, -126), 42 + pose.right_arm, 34, front=False)

    house(("walls",), _paint_walls, "walls")
    roof_tilt = float(round(pose.roof_tilt))
    house(("roof", roof_tilt), lambda d: _paint_roof(d, roof_tilt), "roof")

    # chimney and smoke
    chimney = float(round(pose.chimney))
    house(
        ("chimney", chimney),
        lambda d: _poly(d, [_home(44, -216, chimney), _home(68, -216, chimney), _home(68, -152), _home(44, -152)], CHIMNEY, OUTLINE, 0.8),
        "chimney",
    )
    if pose.smoke > 0.05:
        smoke = round(pose.smoke, 2)

        def puffs(d) -> None:
            for i, (dx, dy, rr) in enumerate([(0, 0, 8), (10, -12, 9), (2, -22, 10)]):
                _ellipse(d, hx + dx, hy + dy - smoke * 6 * i, rr, rr * 0.75, SMOKE, None, 0)

        _put(img, ("smoke", smoke), puffs, P(58, -224, pose.chimney), "smoke")

    house(("face", pose.x_eye, pose.blink, round(pose.brow, 1)), lambda d: _paint_face(d, pose.x_eye, pose.blink, round(pose.brow, 1)), "face")
    mouth = round(pose.mouth_open, 3)
    house(("door", mouth), lambda d: _paint_door(d, mouth), "door")

    # front leg and front arm
    near_foot = _draw_leg(img, P(-18, -12), 94 + pose.left_leg, pose.left_lift, front=True)
    near_hand = _draw_arm(img, P(-60, -126), 154 - pose.left_arm, 38, front=True)

    # foundation / trim over top of legs for clean stacking
    def foundation(d) -> None:
        _poly(d, [_home(-86, -18), _home(94, -18), _home(94, 8), _home(-86, 8)], STONE, OUTLINE, 1.1)
        _line(d, [_home(-82, -4), _home(90, -4)], STONE_SHADE, 0.8)

    house(("foundation",), foundation, "foundation")

    # props / fx
    if anim == "ponder" and pose.book > 0.05:
        def book(d) -> None:
            bx, by = hx, hy
            _poly(d, [(bx - 10, by - 8), (bx + 6, by - 10), (bx + 10, by + 8), (bx - 6, by + 10)], BOOK, OUTLINE, 0.5)
            _line(d, [(bx - 2, by - 6), (bx + 4, by + 6)], BOOK_PAPER, 0.8)
            _line(d, [(bx - 7, by - 4), (bx + 0, by + 8)], BOOK_PAPER, 0.6)

        _put(img, ("book",), book, (near_hand[0] - 10, near_hand[1] - 2), "book")
    if anim == "lecture" and pose.paper > 0.05:
        def paper(d) -> None:
            px, py = hx, hy
            _poly(d, [(px - 9, py - 12), (px + 7, py - 10), (px + 10, py + 10), (px - 8, py + 12)], PAPER, OUTLINE, 0.45)
            _line(d, [(px - 5, py - 6), (px + 3, py - 4)], WOOD_DARK, 0.5)
            _line(d, [(px - 4, py), (px + 4, py + 2)], WOOD_DARK, 0.5)
            _line(d, [(px - 3, py + 6), (px + 5, py + 8)], WOOD_DARK, 0.5)

        _put(img, ("paper",), paper, (far_hand[0] + 12, far_hand[1] - 4), "paper")
    if anim == "idea" and pose.idea > 0.08:
        idea = round(pose.idea, 3)

        def bulb(d) -> None:
            bx, by = hx, hy
            glow_r = 14 + idea * 8
            _ellipse(d, bx, by, glow_r + 10, glow_r + 10, BULB_GLOW, None, 0)
            _ellipse(d, bx, by, 12.0, 16.0, BULB, OUTLINE, 0.6)
            _ellipse(d, bx, by + 17, 7.0, 5.0, BRASS, OUTLINE, 0.5)
            _line(d, [(bx, by + 12), (bx, by + 20)], OUTLINE, 0.5)
            for ang in [-60, -30, 0, 30, 60]:
                r0 = 20
                r1 = 30 + idea * 6
                _line(
                    d,
                    [
                        (bx + math.cos(math.radians(ang)) * r0, by + math.sin(math.radians(ang)) * r0),
                        (bx + math.cos(math.radians(ang)) * r1, by + math.sin(math.radians(ang)) * r1),
                    ],
                    FX,
                    1.0,
                )

        _put(img, ("bulb", idea), bulb, P(0, -268, pose.roof_tilt), "bulb")
    if anim == "ram" and pose.impact > 0.15:
        def ram(d) -> None:
            box = (_s(hx - 36), _s(hy - 26), _s(hx + 42), _s(hy + 36))
            d.arc(box, 220, 350, fill=FX, width=_s(3.6))

        _put(img, ("ram_arc",), ram, P(96, -108), "ram_arc")
    if anim in {"walk", "ram"} and (pose.left_lift > 0.5 or pose.right_lift > 0.5):
        def chip(d) -> None:
            _poly(d, [(hx - 3, hy), (hx, hy - 4), (hx + 4, hy - 1), (hx + 1, hy + 3)], DUST, None, 0)

        for i, dx in enumerate([-30, -8, 14, 34]):
            _put(img, ("dust",), chip, (near_foot[0] + dx, near_foot[1] + 8), f"dust_{i}")

    return _downsample(img)


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda anim, frame_idx, nframes: _render_frame(
            anim, frame_idx, nframes
        ),
        out_dir=out_dir,
        frame_size=opts.get("frame_size", FRAME_SIZE),
        crop_margin=10,
        auto_crop=True,
        actor_metadata=ACTOR_METADATA,
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, _render_frame, outputs, frame_transform, out_dir)
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ] + list(parts.values())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the standalone Smart House sprite sheet."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME,
    )
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
