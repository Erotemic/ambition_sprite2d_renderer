"""Bespoke procedural sprite for the Creator character.

The Creator is intentionally more distinctive than the simple toon-rig cast: a
robed / tailored figure with an asymmetric mantle, high collar, luminous chest
sigil, and a small geometric halo frame. The result is meant to read as an
important authored NPC for the intro rather than a generic townsperson.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageColor, ImageDraw, ImageFilter

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_creator",
        "display_name": "Creator",
        "actor_id": "creator",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "intro", "story", "creator"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": None,
            "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle"},
    "tags": ["story", "humanoid", "intro", "story", "creator"],
    "sockets": {
        "head": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 24.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 54.0},
        },
        "hand_l": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 48.0, "y": 64.0},
        },
        "hand_r": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 80.0, "y": 64.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 8.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
    },
    "missing_information": [
        "Creator story-presence state is intentionally authored outside the "
        "renderer sidecar."
    ],
}


RGBA = Tuple[int, int, int, int]

TARGET_NAME = "creator"
SHEET_FILES = [f"{TARGET_NAME}_spritesheet.png", f"{TARGET_NAME}_spritesheet.yaml"]

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 145),
    ("speak", 6, 110),
    ("gesture", 6, 100),
    ("walk", 8, 95),
]

FRAME_SIZE = (160, 192)
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


def _glow_ellipse(base: Image.Image, bbox, fill: RGBA, blur: float = 4.0) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = blending_draw(layer)
    draw.ellipse(bbox, fill=fill)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=blur * SUPER / 2.0))
    rigdoc.composite_canvas(base, layer)


def _glow_polygon(base: Image.Image, pts, fill: RGBA, blur: float = 4.0) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = blending_draw(layer)
    draw.polygon([_pt(x, y) for x, y in pts], fill=fill)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=blur * SUPER / 2.0))
    rigdoc.composite_canvas(base, layer)


def _piece(key: tuple, size: Tuple[float, float], origin: Tuple[float, float], paint) -> tuple:
    """A piece of the Creator painted once (``shape_rig``): ``paint(draw)``
    draws in frame units with its anchor at ``origin`` (frame units) on a
    ``size`` canvas (frame units). ``key`` names everything ``paint`` reads."""
    return shape_rig.piece(("creator",) + key, (size[0] * SUPER, size[1] * SUPER), (origin[0] * SUPER, origin[1] * SUPER), paint)


def _put(img: Image.Image, part: tuple, at: Tuple[float, float], name: str, degrees: float = 0.0) -> None:
    shape_rig.place(img, part, (at[0] * SUPER, at[1] * SUPER), degrees, name)


def _bone(img: Image.Image, a, b, length: float, width: float, fill: RGBA, name: str) -> None:
    """A flat-ended sleeve of ``length`` from ``a`` toward ``b``, painted once along +x."""
    pad = width + 2.0
    part = _piece(
        ("bone", length, width, fill), (length + 2 * pad, 2 * pad), (pad, pad),
        lambda d: d.line((_s(pad), _s(pad), _s(pad + length), _s(pad)), fill=fill, width=_s(width)),
    )
    _put(img, part, a, name, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))


def _palette() -> dict:
    """The Creator's palette."""
    return {
        "coat_dark": _rgba("#22253d"),
        "coat_mid": _rgba("#343b63"),
        "coat_light": _rgba("#55639c"),
        "lining": _rgba("#8a5d9d"),
        "mantle": _rgba("#643f7d"),
        "brass": _rgba("#d6b370"),
        "cloth_light": _rgba("#9ea9d1"),
        "skin": _rgba("#d7b3a0"),
        "hair": _rgba("#f1eee6"),
        "shadow": _rgba("#10131f"),
        "glow_cyan": _rgba("#8befff"),
        "glow_violet": _rgba("#b88cff"),
    }


#: The coat pieces are painted with the body at rest (bob 0) on the frame's
#: own coordinates, anchored at its top left, and ride the bob.
COAT_SIZE = (160.0, 176.0)


def _paint_leg(d, drop: float) -> None:
    """A trouser leg and boot centred on x 10, the leg's top at y 8 (the frame's
    y 120 at rest); the boot drops ``drop`` in the walk."""
    pal = _palette()
    x, foot_y = 10.0, 8.0 + 44.0 + drop
    d.rectangle(_box(x - 4.2, 8.0, x + 4.0, foot_y - 8.0), fill=_rgba("#2d314f"), outline=pal["shadow"])
    d.rectangle(_box(x - 4.7, foot_y - 11.0, x + 5.2, foot_y), fill=_rgba("#4f5565"), outline=pal["shadow"])


def _paint_coat(d) -> None:
    """Coat, lining, collar, mantle and epaulet at rest (bob 0)."""
    pal = _palette()
    shadow = pal["shadow"]
    coat = [
        (60.0, 85.0), (72.0, 77.0), (89.0, 75.0), (99.0, 80.0), (103.0, 96.0),
        (108.0, 126.0), (112.0, 156.0), (96.0, 164.0), (88.0, 118.0), (79.0, 165.0),
        (70.0, 118.0), (59.0, 160.0), (45.0, 153.0), (50.0, 126.0), (54.0, 98.0),
    ]
    d.polygon([_pt(*p) for p in coat], fill=pal["coat_dark"], outline=shadow)
    inner_coat = [
        (64.0, 88.0), (77.0, 80.0), (89.0, 79.0), (97.0, 84.0), (101.0, 98.0),
        (104.0, 126.0), (107.0, 151.0), (95.0, 157.0), (87.0, 116.0), (79.0, 160.0),
        (71.0, 115.0), (62.0, 154.0), (50.0, 148.0), (56.0, 100.0),
    ]
    d.polygon([_pt(*p) for p in inner_coat], fill=pal["coat_mid"])
    d.polygon([_pt(72.0, 112.0), _pt(79.0, 160.0), _pt(86.0, 112.0)], fill=pal["lining"])

    # High collar and lapels.
    collar_left = [(67.0, 77.0), (77.0, 63.0), (84.0, 80.0), (77.0, 93.0)]
    collar_right = [(92.0, 77.0), (82.0, 63.0), (76.0, 80.0), (82.0, 94.0)]
    d.polygon([_pt(*p) for p in collar_left], fill=pal["coat_light"], outline=shadow)
    d.polygon([_pt(*p) for p in collar_right], fill=pal["coat_light"], outline=shadow)

    # Asymmetric mantle / shoulder piece (its sway of under a third of a pixel dropped).
    mantle_poly = [(58.0, 77.0), (71.0, 68.0), (93.0, 68.0), (104.0, 77.0), (100.0, 88.0), (75.0, 90.0), (62.0, 86.0)]
    d.polygon([_pt(*p) for p in mantle_poly], fill=pal["mantle"], outline=shadow)
    epaulet = [(56.0, 78.0), (45.0, 88.0), (52.0, 100.0), (70.0, 90.0)]
    d.polygon([_pt(*p) for p in epaulet], fill=_rgba("#7b4d96"), outline=shadow)
    d.line(_box(61.0, 83.0, 98.0, 83.0), fill=pal["brass"], width=_s(0.8))


def _paint_front(d) -> None:
    """Chest sigil, gold trim and sash at rest (bob 0)."""
    pal = _palette()
    img = d._img
    sigil_cx, sigil_cy = 80.0, 95.0
    _glow_ellipse(img, _box(sigil_cx - 7.0, sigil_cy - 7.0, sigil_cx + 7.0, sigil_cy + 7.0), _rgba("#7ceeff", 105), blur=4.6)
    _glow_polygon(
        img,
        [(sigil_cx, sigil_cy - 6.0), (sigil_cx + 6.0, sigil_cy), (sigil_cx, sigil_cy + 6.0), (sigil_cx - 6.0, sigil_cy)],
        _rgba("#b88cff", 80),
        blur=3.5,
    )
    d.polygon(
        [_pt(sigil_cx, sigil_cy - 4.0), _pt(sigil_cx + 4.0, sigil_cy), _pt(sigil_cx, sigil_cy + 4.0), _pt(sigil_cx - 4.0, sigil_cy)],
        fill=pal["glow_cyan"],
        outline=_rgba("#effdff"),
    )
    d.ellipse(_box(sigil_cx - 2.1, sigil_cy - 2.1, sigil_cx + 2.1, sigil_cy + 2.1), fill=pal["glow_violet"])
    d.line(_box(73.0, 81.0, 79.0, 156.0), fill=pal["brass"], width=_s(0.55))
    d.line(_box(87.0, 81.0, 81.0, 156.0), fill=pal["brass"], width=_s(0.55))
    sash = [(90.0, 100.0), (101.0, 103.0), (94.0, 149.0), (84.0, 145.0)]
    d.polygon([_pt(*p) for p in sash], fill=_rgba("#7e4a92"), outline=pal["shadow"])
    d.line(_box(92.0, 105.0, 88.0, 145.0), fill=pal["cloth_light"], width=_s(0.42))


def _paint_head(d, hx: float, head_y: float, speak_open: float) -> None:
    """Head, white hair and face; ``hx`` stands for the frame's x 81."""
    pal = _palette()
    shadow = pal["shadow"]
    dx = hx - 81.0
    d.ellipse(_box(66.0 + dx, head_y - 1.0, 96.0 + dx, head_y + 30.0), fill=pal["skin"], outline=shadow)
    hair_back = [(66.0, head_y + 5.0), (72.0, head_y - 5.0), (88.0, head_y - 7.0), (96.0, head_y + 2.0), (94.0, head_y + 22.0), (84.0, head_y + 28.0), (72.0, head_y + 26.0)]
    d.polygon([_pt(x + dx, y) for x, y in hair_back], fill=pal["hair"], outline=shadow)
    hair_front = [(69.0, head_y + 1.0), (79.0, head_y - 6.0), (92.0, head_y + 1.5), (88.0, head_y + 7.0), (76.0, head_y + 8.0)]
    d.polygon([_pt(x + dx, y) for x, y in hair_front], fill=_rgba("#faf8f2"), outline=shadow)

    # Face.
    eye_y = head_y + 11.0
    d.line(_box(75.0 + dx, eye_y, 79.5 + dx, eye_y), fill=shadow, width=_s(0.55))
    d.line(_box(84.0 + dx, eye_y, 88.5 + dx, eye_y), fill=shadow, width=_s(0.55))
    d.arc(_box(77.5 + dx, head_y + 15.0, 85.5 + dx, head_y + 23.0 + speak_open * 2.8), 20, 160, fill=_rgba("#7e3f56"), width=_s(0.55))
    d.line(_box(81.0 + dx, head_y + 11.0, 80.0 + dx, head_y + 16.0), fill=_rgba("#b98f86"), width=_s(0.35))


def _paint_halo(d, c: float) -> None:
    """The halo frame at phase 0 around ``(c, c)``. Its six spokes repeat every
    60 degrees and its rings are round, so the phase turns the piece."""
    halo = Image.new("RGBA", d._img.size, (0, 0, 0, 0))
    hd = blending_draw(halo)
    outer_r = 23.0
    inner_r = 18.0
    hd.ellipse(_box(c - outer_r, c - outer_r, c + outer_r, c + outer_r), outline=_rgba("#6fdfff", 180), width=_s(1.0))
    hd.ellipse(_box(c - inner_r, c - inner_r, c + inner_r, c + inner_r), outline=_rgba("#cc9cff", 160), width=_s(0.7))
    for i in range(6):
        ang = i * (math.tau / 6.0)
        x1 = c + math.cos(ang) * 15.0
        y1 = c + math.sin(ang) * 15.0
        x2 = c + math.cos(ang) * 24.5
        y2 = c + math.sin(ang) * 24.5
        hd.line((_s(x1), _s(y1), _s(x2), _s(y2)), fill=_rgba("#a7f3ff", 160), width=_s(0.55))
        shard = [
            (x2, y2),
            (x2 + math.cos(ang + 0.45) * 3.5, y2 + math.sin(ang + 0.45) * 3.5),
            (x2 + math.cos(ang - 0.45) * 3.5, y2 + math.sin(ang - 0.45) * 3.5),
        ]
        hd.polygon([_pt(*p) for p in shard], fill=_rgba("#d5c0ff", 135))
    d._img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(radius=2.0)))


def _draw_creator(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    """The Creator as a rig: legs, coat, hands, codex, head, halo (turned by its
    phase) and the chest details are pieces painted once riding the bob; arms
    are fixed-length sleeves; the hand's particles change every frame and are
    one draw."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    t = frame_idx / max(1, nframes)
    cyc = math.tau * t
    bob = math.sin(cyc) * (1.0 if anim != "walk" else 1.5)
    sway = math.sin(cyc * 0.6) * (0.9 if anim == "idle" else 1.35)
    halo_phase = cyc * (0.65 if anim == "idle" else 1.0)
    speak_open = 0.0
    if anim == "speak":
        speak_open = 0.15 + 0.85 * (0.5 + 0.5 * math.sin(cyc * 1.8))
    gesture = 0.0
    if anim == "gesture":
        gesture = 0.25 + 0.75 * (0.5 + 0.5 * math.sin(cyc * 1.4 - 0.5))
    walk_phase = cyc
    step = math.sin(walk_phase)
    pal = _palette()

    # Ground shadow removed; the in-game renderer composites the
    # Creator over scene geometry that provides ground contact.

    head_y = 52.0 + bob - sway * 0.5
    at_rest = (0.0, bob)

    # Legs and boots. (The coat slits once drawn here lay wholly under the coat.)
    left_leg_dx = -5.5 + (step * 3.0 if anim == "walk" else -0.6)
    right_leg_dx = 5.0 - (step * 3.0 if anim == "walk" else -0.2)
    for side, leg_dx, drop in (
        ("left", left_leg_dx, 2.5 if anim == "walk" and step > 0 else 0.0),
        ("right", right_leg_dx, 2.5 if anim == "walk" and step < 0 else 0.0),
    ):
        leg = _piece(("leg", drop), (20.0, 58.0), (10.0, 8.0), lambda d, drop=drop: _paint_leg(d, drop))
        _put(img, leg, (79.0 + leg_dx, 120.0 + bob), f"{side}_leg")

    # Main coat silhouette, collar, mantle and epaulet.
    _put(img, _piece(("coat",), COAT_SIZE, (0.0, 0.0), _paint_coat), at_rest, "coat")

    # Arms.
    left_arm_angle = -0.35 - gesture * 0.85
    right_arm_angle = 0.2 + (0.15 if anim == "speak" else 0.0)
    left_shoulder = (61.0, 90.0 + bob)
    right_shoulder = (97.0, 90.0 + bob)

    def limb_pts(origin, ang, upper_len, fore_len):
        ox, oy = origin
        ex = ox + math.cos(ang) * upper_len
        ey = oy + math.sin(ang) * upper_len
        hx = ex + math.cos(ang + 0.2) * fore_len
        hy = ey + math.sin(ang + 0.2) * fore_len
        return (ox, oy), (ex, ey), (hx, hy)

    l0, l1, l2 = limb_pts(left_shoulder, left_arm_angle, 16.0, 13.0)
    r0, r1, r2 = limb_pts(right_shoulder, right_arm_angle, 18.0, 12.0)
    _bone(img, l0, l1, 16.0, 3.3, pal["coat_mid"], "left_upper_arm")
    _bone(img, l1, l2, 13.0, 2.9, pal["coat_light"], "left_forearm")
    _bone(img, r0, r1, 18.0, 3.1, pal["coat_mid"], "right_upper_arm")
    _bone(img, r1, r2, 12.0, 2.7, pal["coat_light"], "right_forearm")
    # Hands.
    for side, hand, r in (("left", l2, 3.5), ("right", r2, 3.3)):
        part = _piece(
            ("hand", r), (10.0, 10.0), (5.0, 5.0),
            lambda d, r=r: d.ellipse(_box(5.0 - r, 5.0 - r, 5.0 + r, 5.0 + r), fill=pal["skin"], outline=pal["shadow"]),
        )
        _put(img, part, hand, f"{side}_hand")

    # Right hand held codex / tablet.
    def paint_codex(d) -> None:
        cx, cy = 9.0, 12.0
        codex = [(cx - 7.0, cy - 8.0), (cx + 3.0, cy - 10.0), (cx + 7.0, cy + 4.0), (cx - 4.0, cy + 6.0)]
        d.polygon([_pt(*p) for p in codex], fill=_rgba("#d8dce8"), outline=pal["shadow"])
        d.line(_box(cx - 2.0, cy - 7.0, cx + 2.0, cy + 4.0), fill=_rgba("#a59bcf"), width=_s(0.55))

    _put(img, _piece(("codex",), (18.0, 20.0), (9.0, 12.0), paint_codex), r2, "codex")

    # Head.
    speak = round(speak_open * 10) / 10
    head = _piece(("head", speak), (36.0, 42.0), (18.0, 9.0), lambda d: _paint_head(d, 18.0, 9.0, speak))
    _put(img, head, (81.0, head_y), "head")

    # Halo frame behind the head.
    halo = _piece(("halo",), (64.0, 64.0), (32.0, 32.0), lambda d: _paint_halo(d, 32.0))
    _put(img, halo, (81.0, head_y + 10.0), "halo", math.degrees(halo_phase) % 60.0)

    # Chest sigil / clasp, gold trim and sash.
    _put(img, _piece(("front",), COAT_SIZE, (0.0, 0.0), _paint_front), at_rest, "front")

    # Small floating particles around the raised hand during gesture / speech.
    particle_amp = 0.0
    if anim in {"gesture", "speak"}:
        particle_amp = 0.55 if anim == "gesture" else 0.35
        p_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        pd = blending_draw(p_layer)
        for i in range(5):
            ang = cyc * 0.8 + i * 1.18
            px = l2[0] + math.cos(ang) * (9.0 + i * 1.4)
            py = l2[1] + math.sin(ang * 1.3) * (6.0 + i * 0.8)
            r = 1.1 + (i % 2) * 0.5
            pd.ellipse(_box(px - r, py - r, px + r, py + r), fill=_rgba("#9ff8ff", int(135 + 40 * particle_amp)))
        p_layer = p_layer.filter(ImageFilter.GaussianBlur(radius=1.4))
        box = p_layer.getbbox()
        if box is not None:
            shape_rig.place(img, (p_layer.crop(box), (0.0, 0.0)), (float(box[0]), float(box[1])), 0.0, "particles")

    return _downsample(img)


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    return _draw_creator(animation, frame_idx, nframes)


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
        label_width=108,
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir))
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["preview"],
    ] + list(parts.values())
