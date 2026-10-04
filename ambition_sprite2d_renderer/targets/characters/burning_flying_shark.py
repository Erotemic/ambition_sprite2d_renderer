"""Procedural burning flying shark mount sprite sheet.

A tack-on target for the pirate sky-mount: a broad, side-view shark with a
combat harness, ember fins, and persistent fire streaming from its dorsal ridge
and tail. The goal is a readable gameplay silhouette rather than a fully
realistic shark.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageColor, ImageFilter

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "burning_flying_shark"
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_burning_flying_shark",
        "display_name": "Burning Flying Shark",
    },
    "body": {
        "body_plan": "Flyer",
        "body_kind": "Floating",
        "mass_class": "Heavy",
        "locomotion_hint": "Fly",
        "traits": ["enemy", "pirate", "aerial", "mount", "beast", "no_hands", "fire"],
    },
    "capabilities": {
        "traversal": {
            "walk": False,
            "jump": None,
            "climb": None,
            "fly": True,
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
    "brain": {"default_preset": "wanderer_puppy_slug"},
    "actions": {"default_preset": "peaceful_float"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.fly": {"animation": "fly", "events": []},
        "action.melee.primary": {
            "animation": "chomp",
            "events": [
                {
                    "t": 0.24,
                    "event": "telegraph_peak",
                    "source": "burning_flying_shark",
                },
                {
                    "t": 0.36,
                    "event": "hitbox_active_start",
                    "source": "burning_flying_shark",
                },
                {
                    "t": 0.64,
                    "event": "hitbox_active_end",
                    "source": "burning_flying_shark",
                },
            ],
        },
        "action.special.dive": {
            "animation": "dive",
            "events": [
                {"t": 0.40, "event": "dive_commit", "source": "burning_flying_shark"},
            ],
        },
    },
    "sockets": {
        "mouth": {
            "source": "burning_flying_shark.geometry",
            "point": {"x": 148.0, "y": 66.0},
        },
        "head": {
            "source": "burning_flying_shark.geometry",
            "point": {"x": 132.0, "y": 56.0},
        },
        "tail": {
            "source": "burning_flying_shark.geometry",
            "point": {"x": 34.0, "y": 64.0},
        },
        "saddle": {
            "source": "burning_flying_shark.geometry",
            "point": {"x": 88.0, "y": 44.0},
        },
        "ember_origin": {
            "source": "burning_flying_shark.geometry",
            "point": {"x": 58.0, "y": 42.0},
        },
    },
    "tags": ["pirate", "aerial", "enemy", "beast", "fire"],
}

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 135),
    ("fly", 8, 90),
    ("chomp", 6, 82),
    ("dive", 8, 82),
]

FRAME_SIZE = (192, 128)
SUPER = 4
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER


def _rgba(color: str, alpha: int = 255) -> RGBA:
    r, g, b = ImageColor.getrgb(color)
    return (r, g, b, alpha)


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(x: float, y: float) -> Tuple[int, int]:
    return (_s(x), _s(y))


def _box(x1: float, y1: float, x2: float, y2: float) -> Tuple[int, int, int, int]:
    return (_s(x1), _s(y1), _s(x2), _s(y2))


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


def _draw_glow(
    base: Image.Image, points: list[Point], color: RGBA, blur: float = 4.0
) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = blending_draw(layer)
    draw.polygon([_pt(x, y) for x, y in points], fill=color)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=blur * SUPER / 2.0))
    base.alpha_composite(layer)


def _paint_flame_plume(base: Image.Image, anchor: Point, length: float, width: float, blur_scale: float) -> None:
    """A flame plume from ``anchor`` along +x, ``length`` long and ``width``
    wide (frame units): a soft glow under three tongues of flame."""
    ax, ay = anchor
    outer = [
        (ax, ay - width * 0.50),
        (ax, ay + width * 0.58),
        (ax + length * 0.38, ay),
        (ax + length * 0.75, ay + width * 0.42),
        (ax + length, ay),
        (ax + length * 0.72, ay - width * 0.35),
        (ax - length * 0.05, ay),
    ]
    mid = [
        (ax, ay - width * 0.22),
        (ax, ay + width * 0.25),
        (ax + length * 0.35, ay),
        (ax + length * 0.65, ay + width * 0.18),
        (ax + length * 0.84, ay),
        (ax + length * 0.60, ay - width * 0.16),
    ]
    inner = [
        (ax, ay - width * 0.10),
        (ax, ay + width * 0.10),
        (ax + length * 0.32, ay),
        (ax + length * 0.58, ay),
        (ax + length * 0.72, ay),
        (ax + length * 0.30, ay - width * 0.08),
    ]
    _draw_glow(base, outer, _rgba("#ff621d", 120), blur=5.0 * blur_scale)
    _draw_glow(base, mid, _rgba("#ff9d2f", 150), blur=3.2 * blur_scale)
    draw = blending_draw(base)
    draw.polygon([_pt(x, y) for x, y in outer], fill=_rgba("#ff7a22", 170))
    draw.polygon([_pt(x, y) for x, y in mid], fill=_rgba("#ffb142", 195))
    draw.polygon([_pt(x, y) for x, y in inner], fill=_rgba("#fff3b0", 215))


#: The pieces' canvas (frame units): full width, ``PIECE_CY`` above the body
#: centre line and the rest below it.
PIECE_H = 84.0
PIECE_CY = 42.0
#: Half the side of a flame plume's canvas (frame units), its anchor at the centre.
FLAME_HALF = 24.0
#: The two plume sizes (a flame's scale) and its three flicker steps
#: (length factor, width factor): a longer tongue is thinner.
FLAME_SCALES = (0.95, 1.15)
FLAME_FLICKER = ((0.78, 1.06), (0.92, 0.98), (1.06, 0.88))
#: The body turns about this point (frame units, on the centre line) when it
#: dives nose down.
PITCH_X = 90.0

#: Pieces painted on a frame-sized canvas, kept cropped to what they cover
#: (the frame-sized raster would sit in ``shape_rig``'s cache for the process).
_CROPPED: dict = {}


def _cropped_piece(key: tuple, size, pivot, paint) -> tuple:
    """``shape_rig.piece`` for a piece painted on a large canvas: painted once,
    cropped to its alpha box with its pivot moved to match, and cached here."""
    hit = _CROPPED.get(key)
    if hit is None:
        image = Image.new("RGBA", (int(math.ceil(size[0])), int(math.ceil(size[1]))), (0, 0, 0, 0))
        paint(blending_draw(image))
        box = image.getbbox() or (0, 0, 1, 1)
        hit = (image.crop(box), (pivot[0] - box[0], pivot[1] - box[1]))
        _CROPPED[key] = hit
    return hit


def _turn(pivot: Point, rest: Point, posed: Point) -> float:
    """Degrees (clockwise) that turn the point ``rest`` about ``pivot`` onto
    the direction of ``posed``: a rigid piece hinged at ``pivot``."""
    a = math.atan2(rest[1] - pivot[1], rest[0] - pivot[0])
    b = math.atan2(posed[1] - pivot[1], posed[0] - pivot[0])
    return math.degrees(b - a)


class _Body:
    """The shark's body frame: its centre line at ``cy`` (frame units),
    turned ``pitch`` degrees (clockwise: nose down) about ``PITCH_X``."""

    def __init__(self, cy: float, pitch: float) -> None:
        self.cy = cy
        self.pitch = pitch
        r = math.radians(pitch)
        self._c, self._s = math.cos(r), math.sin(r)

    def point(self, x: float, dy: float) -> Point:
        """Canvas pixels of the body point ``x`` along, ``dy`` below the centre line."""
        px, py = x - PITCH_X, dy
        return ((PITCH_X + px * self._c - py * self._s) * SUPER, (self.cy + px * self._s + py * self._c) * SUPER)

    def put(self, img: Image.Image, key: tuple, paint, pivot: Point, name: str, degrees: float = 0.0) -> None:
        """The piece ``key`` (``paint(draw, cy)`` draws it at rest in frame
        units) hinged at ``pivot`` = (x, dy) and turned ``degrees`` more
        than the body."""
        part = _cropped_piece(
            ("burning_flying_shark",) + key,
            (W, PIECE_H * SUPER),
            (pivot[0] * SUPER, (PIECE_CY + pivot[1]) * SUPER),
            lambda d: paint(d, PIECE_CY),
        )
        shape_rig.place(img, part, self.point(*pivot), self.pitch + degrees, name)


TAIL_PIVOT = (56.0, 1.0)
TAIL_TIP = (28.0, 0.0)


def _paint_tail(draw, cy: float) -> None:
    tail_base = (TAIL_PIVOT[0], cy + TAIL_PIVOT[1])
    tail_tip = (TAIL_TIP[0], cy + TAIL_TIP[1])
    tail_upper = [tail_base, (41.0, cy - 5.0), (tail_tip[0], tail_tip[1] - 16.0), (34.0, cy - 2.5)]
    tail_lower = [tail_base, (40.0, cy + 7.0), (tail_tip[0], tail_tip[1] + 18.0), (33.0, cy + 5.0)]
    draw.polygon([_pt(*p) for p in tail_upper], fill=_rgba("#4a5968"), outline=_rgba("#182028"))
    draw.polygon([_pt(*p) for p in tail_lower], fill=_rgba("#404d5c"), outline=_rgba("#182028"))


#: Fins as triangles (root, tip, root) at rest (x, dy) with the tip's travel
#: per unit of wing flap; each is hinged at the middle of its root.
REAR_FIN = ((76.0, 3.0), (58.0, 14.0), (85.0, 15.0))
WING_BACK = ((82.0, -1.5), (60.0, -21.0), (95.0, -9.0))
WING_FRONT = ((94.0, 0.5), (62.0, 12.0), (103.0, 10.0))
DORSAL = ((87.0, -8.0), (94.0, -31.0), (105.0, -8.0))


def _root(fin) -> Point:
    return ((fin[0][0] + fin[2][0]) / 2.0, (fin[0][1] + fin[2][1]) / 2.0)


def _fin_painter(fin, fill: RGBA, outline: RGBA):
    def paint(draw, cy: float) -> None:
        draw.polygon([_pt(x, cy + dy) for x, dy in fin], fill=fill, outline=outline)

    return paint


def _place_fin(img, body: _Body, name: str, fin, tip_dy: float, fill: RGBA, outline: RGBA) -> None:
    """The fin ``fin`` turned at its root so its tip moves ``tip_dy`` down."""
    root, tip = _root(fin), fin[1]
    body.put(img, (name,), _fin_painter(fin, fill, outline), root, name, _turn(root, tip, (tip[0], tip[1] + tip_dy)))


def _paint_body(draw, cy: float) -> None:
    body_left = 50.0
    body_right = 126.0
    top = cy - 18.0
    bottom = cy + 18.0
    draw.ellipse(_box(body_left, top, body_right, bottom), fill=_rgba("#596978"), outline=_rgba("#15202c"), width=_s(1.6))
    draw.ellipse(_box(body_left + 4.0, top + 3.0, body_right - 6.0, bottom - 2.0), fill=_rgba("#667888"))
    draw.pieslice(_box(78.0, top + 2.0, 132.0, bottom - 2.0), 80, 280, fill=_rgba("#495867", 120))
    draw.pieslice(_box(58.0, cy - 11.0, 116.0, cy + 14.0), 108, 248, fill=_rgba("#8191a1", 115))


def _paint_head(draw, cy: float) -> None:
    """Snout, belly, the mouth line, glowing eye and gills (the jaw and the
    teeth are pieces of their own)."""
    img = draw._img
    head_pts = [(108.0, cy - 18.0), (141.5, cy - 10.0), (153.0, cy - 3.0), (157.0, cy + 1.0), (153.0, cy + 6.0), (140.5, cy + 12.0), (105.0, cy + 18.0)]
    draw.polygon([_pt(*p) for p in head_pts], fill=_rgba("#627385"), outline=_rgba("#15202c"))
    belly = [(75.0, cy + 7.0), (104.0, cy + 11.0), (136.0, cy + 11.0), (153.0, cy + 6.0), (138.0, cy + 14.0), (113.0, cy + 16.0), (88.0, cy + 17.0)]
    draw.polygon([_pt(*p) for p in belly], fill=_rgba("#c0c9cf", 210))
    draw.line([_pt(124.0, cy + 0.5), _pt(154.0, cy + 1.0)], fill=_rgba("#172028"), width=_s(1.2))
    draw.ellipse(_box(119.0, cy - 8.0, 126.5, cy - 1.5), fill=_rgba("#1c0b08"))
    eye_glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    eg = blending_draw(eye_glow)
    eg.ellipse(_box(120.4, cy - 6.6, 124.8, cy - 2.6), fill=_rgba("#ff8b29", 220))
    img.alpha_composite(eye_glow.filter(ImageFilter.GaussianBlur(radius=2.6)))
    draw.ellipse(_box(121.0, cy - 6.0, 124.1, cy - 3.2), fill=_rgba("#ffd76d"))
    for gx in (112.0, 116.0, 120.0):
        draw.arc(_box(gx, cy - 4.0, gx + 7.0, cy + 8.0), 260, 78, fill=_rgba("#314150"), width=_s(0.8))


#: The jaw: the open mouth (hinge, tip, chin) at full gape, hinged at the
#: back of the mouth and turned up as the mouth closes.
JAW = ((123.0, 1.0), (150.5, 16.0), (135.0, 15.0))


def _jaw_tip_dy(mouth_open: float) -> float:
    return 7.5 + 8.5 * mouth_open


def _paint_jaw(draw, cy: float) -> None:
    draw.polygon([_pt(x, cy + dy) for x, dy in JAW], fill=_rgba("#8a4140"), outline=_rgba("#1d1214"))


def _paint_teeth(draw, cy: float) -> None:
    for tooth_x in (131.0, 137.5, 144.0, 149.0):
        tooth = [(tooth_x, cy + 1.6), (tooth_x + 1.8, cy + 4.6), (tooth_x + 3.6, cy + 1.5)]
        draw.polygon([_pt(*p) for p in tooth], fill=_rgba("#f5efe2"))


def _paint_harness(draw, cy: float) -> None:
    """Pirate harness / saddle."""
    strap = _rgba("#5a3f28")
    brass = _rgba("#d0a85e")
    steel = _rgba("#b7c2cd")
    draw.rectangle(_box(78.0, cy - 10.5, 101.0, cy + 0.5), fill=_rgba("#4c3424"), outline=_rgba("#1b1210"))
    draw.rectangle(_box(82.0, cy - 17.0, 95.0, cy - 10.0), fill=_rgba("#77533a"), outline=_rgba("#1b1210"))
    draw.line(_box(77.0, cy - 3.0, 106.0, cy - 1.0), fill=strap, width=_s(1.5))
    draw.line(_box(88.0, cy - 13.0, 88.0, cy + 6.0), fill=strap, width=_s(1.2))
    draw.line(_box(99.0, cy - 11.0, 99.0, cy + 7.0), fill=strap, width=_s(1.2))
    draw.ellipse(_box(86.0, cy - 2.2, 89.8, cy + 1.6), fill=brass)
    draw.ellipse(_box(97.0, cy - 2.2, 100.8, cy + 1.6), fill=brass)
    draw.line(_box(101.0, cy - 13.0, 111.0, cy - 15.5), fill=steel, width=_s(0.9))
    draw.line(_box(111.0, cy - 15.5, 117.0, cy - 12.0), fill=steel, width=_s(0.9))


def _flame(size: int, flicker: int) -> tuple:
    """The plume of size step ``size`` and flicker step ``flicker``, painted
    once along +x with its anchor at the centre."""
    scale = FLAME_SCALES[size]
    long_k, wide_k = FLAME_FLICKER[flicker]
    half = FLAME_HALF * SUPER
    return shape_rig.piece(
        ("burning_flying_shark", "flame", size, flicker),
        (2 * half, 2 * half),
        (half, half),
        lambda d: _paint_flame_plume(d._img, (FLAME_HALF, FLAME_HALF), 14.0 * scale * long_k, 6.4 * scale * wide_k, scale),
    )


#: Ember specks: three sizes of one soft dot.
EMBER_RADII = (0.85, 1.19, 1.53)


def _ember(size: int) -> tuple:
    r = EMBER_RADII[size]
    half = 4.0 * SUPER

    def paint(d) -> None:
        dot = Image.new("RGBA", d._img.size, (0, 0, 0, 0))
        blending_draw(dot).ellipse((half - r * SUPER, half - r * SUPER, half + r * SUPER, half + r * SUPER), fill=_rgba("#ffb451", 160))
        d._img.alpha_composite(dot.filter(ImageFilter.GaussianBlur(radius=1.0)))

    return shape_rig.piece(("burning_flying_shark", "ember", size), (2 * half, 2 * half), (half, half), paint)


def _draw_shark(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    """The shark as a rig: every piece is painted once and turned into place.
    The body bobs (and dives nose down); the tail, the fins and the jaw turn
    at their roots; the flames are two plume sizes in three flicker steps,
    turned along their streams and faded; the embers are soft dots."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    t = frame_idx / max(1, nframes)
    cyc = math.tau * t
    bob = math.sin(cyc) * (1.6 if anim == "idle" else 2.4)
    tail_swing = math.sin(cyc * (1.0 if anim == "idle" else 1.35)) * (4.0 if anim == "fly" else 5.4)
    wing_flap = math.sin(cyc * (1.25 if anim == "idle" else 1.8)) * (5.5 if anim != "dive" else 2.8)
    mouth_open = 1.0 if anim == "chomp" and frame_idx in {1, 2, 3, 4} else 0.0
    if anim == "chomp":
        mouth_open = max(mouth_open, 0.18 + 0.82 * math.sin(t * math.pi))
    # A dive pitches the whole body nose down (the nose drops 3 to 7 px).
    pitch = 0.0
    if anim == "dive":
        nose_drop = 5.0 + 2.0 * math.sin(cyc * 1.2)
        pitch = math.degrees(math.atan2(nose_drop, 157.0 - PITCH_X))

    # Drop shadow intentionally omitted — the shark is airborne;
    # an under-body ground shadow reads as a grounded prop.
    body = _Body(62.0 + bob, pitch)

    # Tail and rear fin behind the body.
    tail_deg = _turn(TAIL_PIVOT, TAIL_TIP, (TAIL_TIP[0], TAIL_TIP[1] + tail_swing))
    body.put(img, ("tail",), _paint_tail, TAIL_PIVOT, "tail", tail_deg)
    _place_fin(img, body, "rear_fin", REAR_FIN, wing_flap * 0.45, _rgba("#d5682f"), _rgba("#3d1d16"))
    # Main body, then the snout, the jaw and the teeth.
    body.put(img, ("body",), _paint_body, (90.0, 0.0), "body")
    body.put(img, ("head",), _paint_head, (130.0, 0.0), "head")
    if mouth_open > 0.05:
        hinge, tip = JAW[0], JAW[1]
        jaw_deg = _turn(hinge, tip, (tip[0], _jaw_tip_dy(mouth_open)))
        body.put(img, ("jaw",), _paint_jaw, hinge, "jaw", jaw_deg)
    body.put(img, ("teeth",), _paint_teeth, (140.0, 2.0), "teeth")
    # Wings / pectoral fins and dorsal fin, then the harness.
    _place_fin(img, body, "wing_back", WING_BACK, -wing_flap, _rgba("#c85d2e"), _rgba("#3d1d16"))
    _place_fin(img, body, "wing_front", WING_FRONT, wing_flap, _rgba("#da6e33"), _rgba("#3d1d16"))
    _place_fin(img, body, "dorsal", DORSAL, -abs(wing_flap) * 0.35, _rgba("#de6b2b"), _rgba("#4a1f13"))
    body.put(img, ("harness",), _paint_harness, (90.0, -6.0), "harness")

    # Flame plumes stream from the dorsal ridge, the flanks and the tail tip.
    tail_r = math.radians(tail_deg)
    tdx, tdy = 36.0 - TAIL_PIVOT[0], 1.0 - TAIL_PIVOT[1]
    tail_flame = (TAIL_PIVOT[0] + tdx * math.cos(tail_r) - tdy * math.sin(tail_r), TAIL_PIVOT[1] + tdx * math.sin(tail_r) + tdy * math.cos(tail_r))
    flame_anchors = [
        ((95.0, -26.0), (-0.25, -1.0), 0, 0.2),
        ((80.0, -16.5), (-0.95, -0.28), 1, 1.1),
        ((74.0, 13.0), (-0.92, 0.24), 0, 2.0),
        (tail_flame, (-1.0, 0.10), 1, 1.6),
    ]
    for k, (anchor, direction, size, offset) in enumerate(flame_anchors):
        phase = cyc + offset
        flicker = int(round(math.sin(phase))) + 1
        wobble = 7.0 * math.sin(phase * 1.7)
        deg = math.degrees(math.atan2(direction[1], direction[0])) + wobble + body.pitch
        opacity = round(0.86 + 0.14 * math.cos(phase * 1.7), 2)
        rigdoc.blit_rotated(img, *_flame(size, flicker), body.point(*anchor), deg, opacity, part_name=f"flame{k}")

    # Ember specks drift behind the shark.
    for i in range(12):
        ex = 58.0 - i * 5.8 + math.sin(cyc + i) * 1.7
        ey = body.cy - 22.0 + (i % 5) * 7.0 + math.cos(cyc * 1.8 + i * 0.7) * 1.6
        shape_rig.place(img, _ember(i % 3), (ex * SUPER, ey * SUPER), 0.0, f"ember{i}")

    return _downsample(img)


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    return _draw_shark(animation, frame_idx, nframes)


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=118,
        actor_metadata=ACTOR_METADATA,
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir))
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
    ] + list(parts.values())
