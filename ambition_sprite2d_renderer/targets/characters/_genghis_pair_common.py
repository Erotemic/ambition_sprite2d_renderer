from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from PIL import Image, ImageColor, ImageDraw

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ...authoring.sheet_build import build_sheet

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

FRAME_W = 128
FRAME_H = 128
SUPER = 4
CANVAS_W = FRAME_W * SUPER
CANVAS_H = FRAME_H * SUPER
FRAME_SIZE = (FRAME_W, FRAME_H)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 142),
    ("walk", 8, 96),
    ("talk", 6, 108),
    ("interact", 6, 92),
    ("taunt", 8, 94),
]
OUTLINE = (25, 18, 17, 255)
WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)


@dataclass(frozen=True)
class VariantSpec:
    target_name: str
    display_name: str
    character_id: str
    confidence: float
    slouch: float
    bark_lines: Tuple[str, ...]
    palette: Dict[str, RGBA]


VARIANTS: Dict[str, VariantSpec] = {
    "genghis_can": VariantSpec(
        target_name="genghis_can",
        display_name="Genghis Can",
        character_id="npc_genghis_can",
        confidence=1.0,
        slouch=0.0,
        bark_lines=(
            "Can I conquer this realm? Genghis Can.",
            "Every border is a suggestion.",
            "Advance. History hates hesitation.",
        ),
        palette={
            "skin": (202, 154, 118, 255),
            "skin_shadow": (159, 111, 82, 255),
            "hat_fur": (53, 36, 30, 255),
            "hat_top": (142, 35, 28, 255),
            "hair": (32, 24, 20, 255),
            "beard": (36, 27, 23, 255),
            "robe": (135, 28, 24, 255),
            "robe_shadow": (95, 19, 19, 255),
            "robe_light": (175, 60, 51, 255),
            "trim": (215, 170, 75, 255),
            "lamellar": (115, 54, 35, 255),
            "lamellar_light": (154, 84, 47, 255),
            "belt": (68, 44, 32, 255),
            "buckle": (225, 192, 101, 255),
            "cape": (94, 28, 21, 255),
            "boot": (63, 44, 37, 255),
            "boot_sole": (31, 24, 21, 255),
            "eye": (28, 18, 15, 255),
            "mouth": (124, 57, 53, 255),
        },
    ),
    "genghis_cant": VariantSpec(
        target_name="genghis_cant",
        display_name="Genghis Can't",
        character_id="npc_genghis_cant",
        confidence=0.1,
        slouch=4.0,
        bark_lines=(
            "Perhaps we could postpone the invasion.",
            "This map has too many directions.",
            "Retreat is a kind of strategy... probably.",
        ),
        palette={
            "skin": (197, 148, 116, 255),
            "skin_shadow": (153, 106, 82, 255),
            "hat_fur": (70, 56, 48, 255),
            "hat_top": (74, 92, 118, 255),
            "hair": (38, 29, 24, 255),
            "beard": (58, 45, 38, 255),
            "robe": (84, 97, 116, 255),
            "robe_shadow": (60, 69, 84, 255),
            "robe_light": (110, 124, 145, 255),
            "trim": (162, 145, 90, 255),
            "lamellar": (97, 73, 54, 255),
            "lamellar_light": (132, 102, 76, 255),
            "belt": (70, 55, 43, 255),
            "buckle": (171, 156, 109, 255),
            "cape": (91, 86, 98, 255),
            "boot": (66, 54, 46, 255),
            "boot_sole": (31, 26, 24, 255),
            "eye": (33, 26, 22, 255),
            "mouth": (112, 63, 60, 255),
        },
    ),
}


ACTOR_METADATA: Dict[str, Dict] = {
    name: {
        "actor": {"character_id": spec.character_id, "display_name": spec.display_name},
        "body": {
            "body_plan": "HumanoidBiped",
            "body_kind": "Standard",
            "mass_class": "Medium",
            "traits": [
                "story",
                "humanoid",
                "warlord",
                "nomad_parody",
                "paired_character",
            ],
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
        "visual": {
            "default_pose": "idle",
            "portrait": {"animation": "idle", "frame": 2},
        },
        "tags": [
            "story",
            "humanoid",
            "warlord",
            "nomad_parody",
            "paired_character",
        ],
        "sockets": {
            "head": {"source": "explicit.profile.humanoid", "point": {"x": 64.0, "y": 28.0}},
            "chest": {"source": "explicit.profile.humanoid", "point": {"x": 64.0, "y": 61.0}},
            "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 45.0, "y": 78.0}},
            "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 84.0, "y": 78.0}},
            "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 64.0, "y": 8.0}},
        },
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "interaction.talk": {"animation": "talk", "events": []},
            "interaction.use": {"animation": "interact", "events": []},
            "emote.taunt": {"animation": "taunt", "events": []},
        },
        "dialogue_hints": {"barks": list(spec.bark_lines)},
    }
    for name, spec in VARIANTS.items()
}

ACTOR_METADATA["genghis_can"].update(
    {
        "authoring_description": (
            "Genghis Can is the unstoppable half of a paired Genghis Khan parody. "
            "He turns the conqueror's name into pure affirmative momentum: move first, "
            "claim the horizon, and correct mistakes while already advancing."
        ),
        "gameplay_description": (
            "Use as an aggressive commander, rushdown rival, quest instigator, or paired "
            "boss. He should favor immediate expansion and confident improvisation, in "
            "contrast to his reflective brother Genghis Can't."
        ),
    }
)
ACTOR_METADATA["genghis_cant"].update(
    {
        "authoring_description": (
            "Genghis Can't is the hesitant, ethically reflective half of a paired Genghis "
            "Khan parody. The name turns conquest into doubt: he has the same potential "
            "horde as his brother but cannot stop calculating whether taking something is "
            "worth its human cost."
        ),
        "gameplay_description": (
            "Use as a cautious commander, defensive rival, advisor, or paired boss. He "
            "should delay, inspect consequences, and sometimes discover that refusing an "
            "action is the stronger move."
        ),
    }
)


def _rgba(color: str, alpha: int = 255) -> RGBA:
    r, g, b = ImageColor.getrgb(color)
    return (r, g, b, alpha)


def _mix(a: RGBA, b: RGBA, t: float) -> RGBA:
    return tuple(int(round(a[i] * (1.0 - t) + b[i] * t)) for i in range(4))  # type: ignore[return-value]


def _s(value: float) -> int:
    return int(round(value * SUPER))


def _pt(x: float, y: float) -> Tuple[int, int]:
    return (_s(x), _s(y))


def _bbox(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease01(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _draw_line(draw: ImageDraw.ImageDraw, points: Iterable[Point], fill: RGBA, width: float) -> None:
    draw.line([_pt(x, y) for x, y in points], fill=fill, width=_s(width), joint="curve")


def _arm_chain(shoulder: Point, upper: float, lower: float, a1: float, a2: float) -> Tuple[Point, Point]:
    elbow = (
        shoulder[0] + math.cos(a1) * upper,
        shoulder[1] + math.sin(a1) * upper,
    )
    hand = (
        elbow[0] + math.cos(a1 + a2) * lower,
        elbow[1] + math.sin(a1 + a2) * lower,
    )
    return elbow, hand


def _frame_state(anim: str, frame_idx: int, nframes: int, spec: VariantSpec) -> Dict[str, float]:
    t = frame_idx / max(1, nframes)
    cyc = math.tau * t
    bounce = math.sin(cyc)
    step = math.sin(cyc)
    sway = math.sin(cyc + math.pi / 2)
    talk = 0.0
    interact = 0.0
    taunt = 0.0
    if anim == "talk":
        talk = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(cyc * 1.4))
    if anim == "interact":
        interact = _ease01(0.5 + 0.5 * math.sin(cyc - math.pi / 3))
    if anim == "taunt":
        taunt = 0.5 + 0.5 * math.sin(cyc)

    body_bob = bounce * (1.0 if anim == "idle" else 0.8)
    if anim == "walk":
        body_bob = abs(step) * 1.6
    if anim in {"interact", "taunt"}:
        body_bob = math.sin(cyc) * 0.8

    can = spec.confidence
    if anim == "walk":
        stride = step * _lerp(3.2, 6.6, can)
    else:
        stride = 0.0
    torso_tilt = _lerp(0.10, -0.02, can)
    if anim == "walk":
        torso_tilt += math.sin(cyc) * 0.06
    if spec.target_name.endswith("cant"):
        torso_tilt += 0.06
    if anim == "interact":
        torso_tilt += _lerp(0.02, -0.10, can) * interact
    if anim == "taunt":
        torso_tilt += _lerp(0.12, -0.06, can) * taunt

    mouth_open = 0.8 * talk + (0.18 if anim == "taunt" and can > 0.5 else 0.06)
    if spec.target_name.endswith("cant") and anim == "talk":
        mouth_open *= 0.75

    return {
        "cyc": cyc,
        "bounce": bounce,
        "sway": sway,
        "step": step,
        "talk": talk,
        "interact": interact,
        "taunt": taunt,
        "body_bob": body_bob,
        "stride": stride,
        "torso_tilt": torso_tilt,
        "mouth_open": mouth_open,
    }


# --- Rig construction -------------------------------------------------------
#
# The pair are drawn as a rig (``shape_rig``): every rigid piece is painted once
# in its own frame, at the supersampled scale, and placed. The robe (with its
# mantle, lamellar and belt), neck, head and front trim ride the torso as it
# bobs and tilts; the cape is keyed by its (rounded) wave; each leg is one
# piece keyed by its (rounded) knee and foot; each arm is its bones turned by
# the arm chain's angles, outlines first and fills over them as the polyline
# drew them.


def _piece(key, half: Tuple[float, float], paint) -> Tuple[Image.Image, Point]:
    """A piece ``2 * half`` frame pixels, its pivot at the centre:
    ``paint(draw, ox, oy)`` paints it with the local origin at ``(ox, oy)``."""
    size = (2 * _s(half[0]), 2 * _s(half[1]))
    return shape_rig.piece(("genghis",) + tuple(key), size, (size[0] / 2, size[1] / 2), lambda d: paint(d, half[0], half[1]))


def _put(canvas: Image.Image, part, at: Point, degrees: float, name: str) -> None:
    shape_rig.place(canvas, part, (at[0] * SUPER, at[1] * SUPER), degrees, name)


def _paint_cape(draw, pal: Dict[str, RGBA], tx: float, bob: float, can: float, cape_wave: float) -> None:
    cape_bottom = 118.0 + bob - _lerp(2.0, 0.0, can)
    draw.polygon(
        [_pt(tx - 18.0, 66.0 + bob), _pt(tx + 16.0, 68.0 + bob), _pt(tx + 24.0 + cape_wave * 2.5, 104.0 + bob), _pt(tx + 8.0, cape_bottom), _pt(tx - 12.0, cape_bottom - 1.0), _pt(tx - 23.0 - cape_wave * 2.0, 102.0 + bob)],
        fill=pal["cape"],
        outline=OUTLINE,
    )


def _paint_leg(draw, pal: Dict[str, RGBA], hip: Point, knee: Point, foot: Point) -> None:
    _draw_line(draw, [hip, knee, foot], OUTLINE, 7.5)
    _draw_line(draw, [hip, knee, foot], pal["boot"], 5.6)
    draw.ellipse(_bbox(knee[0], knee[1], 1.8, 1.8), fill=pal["robe_shadow"], outline=OUTLINE)
    draw.rounded_rectangle((_s(foot[0] - 6.5), _s(foot[1] - 3.2), _s(foot[0] + 6.6), _s(foot[1] + 3.5)), radius=_s(2.0), fill=pal["boot"], outline=OUTLINE)
    draw.rectangle((_s(foot[0] - 6.2), _s(foot[1] + 0.7), _s(foot[0] + 6.0), _s(foot[1] + 3.5)), fill=pal["boot_sole"], outline=None)


def _paint_robe(draw, pal: Dict[str, RGBA], tx: float, bob: float, can: float) -> None:
    """The robe, mantle, lamellar and belt about ``(tx, 80 + bob)``: rigid
    with the torso (its hem, panels and belt bob with it)."""
    foot_y = 118.0 + bob
    hem_notch = _lerp(3.5, 1.6, can)
    draw.polygon(
        [
            _pt(tx - 20.0, 60.0 + bob),
            _pt(tx - 14.0, 52.0 + bob),
            _pt(tx + 12.0, 52.0 + bob),
            _pt(tx + 20.0, 60.0 + bob),
            _pt(tx + 22.0, 82.0 + bob),
            _pt(tx + 17.0, 106.0 + bob),
            _pt(tx + 6.5, foot_y - 3.0),
            _pt(tx, foot_y - hem_notch),
            _pt(tx - 6.0, foot_y - 3.0),
            _pt(tx - 18.0, 106.0 + bob),
            _pt(tx - 23.0, 82.0 + bob),
        ],
        fill=pal["robe"],
        outline=OUTLINE,
    )
    draw.polygon(
        [_pt(tx - 3.5, 56.0 + bob), _pt(tx + 8.0, 56.0 + bob), _pt(tx + 12.0, 90.0 + bob), _pt(tx + 4.0, 108.0 + bob), _pt(tx - 2.0, 98.0 + bob)],
        fill=pal["robe_light"],
        outline=None,
    )
    draw.polygon(
        [_pt(tx - 18.0, 58.0 + bob), _pt(tx - 11.0, 56.0 + bob), _pt(tx - 9.0, 91.0 + bob), _pt(tx - 16.0, 105.0 + bob), _pt(tx - 20.0, 82.0 + bob)],
        fill=pal["robe_shadow"],
        outline=None,
    )
    draw.rectangle((_s(tx - 2.0), _s(59.0 + bob), _s(tx + 1.8), _s(foot_y - 5.0)), fill=pal["trim"], outline=None)

    # Shoulder mantle.
    draw.rounded_rectangle((_s(tx - 19.5), _s(57.0 + bob), _s(tx + 19.5), _s(69.0 + bob)), radius=_s(4.0), fill=pal["hat_fur"], outline=OUTLINE)
    draw.rounded_rectangle((_s(tx - 13.0), _s(58.5 + bob), _s(tx + 13.0), _s(65.5 + bob)), radius=_s(3.0), fill=_mix(pal["hat_fur"], WHITE, 0.18), outline=None)

    # Lamellar chest.
    chest_top = 70.0 + bob
    for row in range(4):
        cols = 4 if row < 3 else 3
        y = chest_top + row * 5.0
        xoff = tx - (cols * 4.3 - 1.8)
        for col in range(cols):
            x = xoff + col * 8.6 + (2.2 if row == 3 else 0.0)
            w = 6.9
            draw.rounded_rectangle((_s(x), _s(y), _s(x + w), _s(y + 4.5)), radius=_s(1.4), fill=pal["lamellar"], outline=OUTLINE)
            draw.rectangle((_s(x + 1.2), _s(y + 1.1), _s(x + w - 1.0), _s(y + 2.1)), fill=pal["lamellar_light"], outline=None)

    # Belt.
    draw.rounded_rectangle((_s(tx - 18.0), _s(88.0 + bob), _s(tx + 18.0), _s(94.5 + bob)), radius=_s(2.0), fill=pal["belt"], outline=OUTLINE)
    draw.rounded_rectangle((_s(tx - 4.0), _s(87.8 + bob), _s(tx + 4.0), _s(94.8 + bob)), radius=_s(1.6), fill=pal["buckle"], outline=OUTLINE)


def _paint_head(draw, spec: VariantSpec, head_cx: float, head_y: float, talking: bool, mouth_open: float) -> None:
    pal = spec.palette
    can = spec.confidence
    draw.ellipse(_bbox(head_cx, head_y + 0.2, 15.5, 17.8), fill=pal["skin"], outline=OUTLINE)
    draw.pieslice(_bbox(head_cx, head_y + 4.0, 15.2, 14.2), start=0, end=180, fill=pal["skin_shadow"], outline=None)
    draw.ellipse(_bbox(head_cx, head_y - 6.0, 13.6, 8.5), fill=pal["hair"], outline=OUTLINE)

    # Hat.
    draw.rounded_rectangle((_s(head_cx - 18.0), _s(head_y - 11.0), _s(head_cx + 18.0), _s(head_y - 1.0)), radius=_s(4.0), fill=pal["hat_fur"], outline=OUTLINE)
    hat_pts = [
        (head_cx - 11.0, head_y - 5.0),
        (head_cx - 8.5, head_y - 21.0),
        (head_cx + 0.5, head_y - 24.0),
        (head_cx + 10.0, head_y - 20.0),
        (head_cx + 12.0, head_y - 4.0),
    ]
    if spec.target_name.endswith("cant"):
        hat_pts = [(x + (2.0 if i > 1 else 0.0), y + (2.0 if i > 1 else 0.0)) for i, (x, y) in enumerate(hat_pts)]
    draw.polygon([_pt(x, y) for x, y in hat_pts], fill=pal["hat_top"], outline=OUTLINE)
    draw.polygon([_pt(head_cx - 2.0, head_y - 20.0), _pt(head_cx + 3.0, head_y - 31.0), _pt(head_cx + 7.0, head_y - 19.0)], fill=pal["hat_top"], outline=OUTLINE)

    # Ears.
    draw.ellipse(_bbox(head_cx - 14.5, head_y + 1.8, 2.5, 3.8), fill=pal["skin"], outline=OUTLINE)
    draw.ellipse(_bbox(head_cx + 14.5, head_y + 1.8, 2.5, 3.8), fill=pal["skin"], outline=OUTLINE)

    # Brows and eyes.
    brow_raise = _lerp(1.8, -0.8, can)
    if talking:
        brow_raise += 0.6 * (1.0 - can)
    left_brow_y = head_y - 1.5 - brow_raise
    right_brow_y = head_y - 0.8 - brow_raise * 0.85
    _draw_line(draw, [(head_cx - 8.7, left_brow_y + (1.0 if can < 0.5 else 0.0)), (head_cx - 2.2, left_brow_y - (1.0 if can > 0.5 else 0.2))], pal["eye"], 1.6)
    _draw_line(draw, [(head_cx + 2.3, right_brow_y - (1.0 if can > 0.5 else -0.2)), (head_cx + 8.7, right_brow_y + (1.0 if can < 0.5 else 0.0))], pal["eye"], 1.6)
    eye_drop = 0.0 if can > 0.5 else 1.6
    draw.ellipse(_bbox(head_cx - 5.7, head_y + 1.6 + eye_drop, 1.8, 1.6 if can > 0.5 else 1.2), fill=pal["eye"], outline=None)
    draw.ellipse(_bbox(head_cx + 5.5, head_y + 2.0 + eye_drop, 1.7, 1.5 if can > 0.5 else 1.1), fill=pal["eye"], outline=None)

    # Nose.
    _draw_line(draw, [(head_cx + 0.3, head_y + 1.0), (head_cx - 0.4, head_y + 7.0), (head_cx + 2.0, head_y + 8.2)], pal["skin_shadow"], 1.3)

    # Mustache + beard.
    mustache_y = head_y + 8.2
    if can > 0.5:
        moust_left = [(head_cx - 9.2, mustache_y), (head_cx - 4.8, mustache_y - 1.3), (head_cx - 0.7, mustache_y + 0.7)]
        moust_right = [(head_cx + 0.6, mustache_y + 0.6), (head_cx + 4.8, mustache_y - 1.2), (head_cx + 9.4, mustache_y)]
    else:
        moust_left = [(head_cx - 7.8, mustache_y + 1.1), (head_cx - 4.3, mustache_y), (head_cx - 0.7, mustache_y + 1.6)]
        moust_right = [(head_cx + 0.6, mustache_y + 1.5), (head_cx + 3.8, mustache_y + 0.3), (head_cx + 7.4, mustache_y + 1.4)]
    _draw_line(draw, moust_left, pal["beard"], 2.6)
    _draw_line(draw, moust_right, pal["beard"], 2.6)
    beard_w = _lerp(8.8, 6.3, can)
    beard_h = _lerp(8.4, 6.6, can)
    draw.pieslice(_bbox(head_cx, head_y + 13.2, beard_w, beard_h), start=14, end=166, fill=pal["beard"], outline=OUTLINE)

    # Mouth.
    mouth_y = head_y + 11.6
    if spec.target_name.endswith("cant"):
        draw.arc((_s(head_cx - 4.4), _s(mouth_y - 1.2), _s(head_cx + 4.2), _s(mouth_y + 2.6 + mouth_open)), start=12, end=164, fill=pal["mouth"], width=_s(1.1))
    else:
        draw.arc((_s(head_cx - 4.3), _s(mouth_y - 0.6), _s(head_cx + 4.3), _s(mouth_y + 2.4 + mouth_open)), start=200, end=340, fill=pal["mouth"], width=_s(1.2))
    if talking:
        draw.ellipse(_bbox(head_cx, mouth_y + 1.9, 2.8, 1.6 + mouth_open * 1.9), fill=pal["mouth"], outline=None)


def _place_arm(img: Image.Image, spec: VariantSpec, side: str, shoulder: Point, a1: float, a2: float) -> None:
    """The arm's bones turned by the chain's angles: both outlines, then both
    fills (each with its round joint at the elbow, as the polyline's curve
    joint), then the elbow and hand discs on the forearm."""
    pal = spec.palette
    width, upper_len, lower_len = 6.7, 16.0, 13.2
    elbow, _hand = _arm_chain(shoulder, upper_len, lower_len, a1, a2)
    upper_deg, lower_deg = math.degrees(a1), math.degrees(a1 + a2)
    half = (22.0, 22.0)

    def stroke(color: RGBA, w: float, length: float, joint: bool):
        def paint(d, ox: float, oy: float) -> None:
            _draw_line(d, [(ox, oy), (ox + length, oy)], color, w)
            if joint:
                d.ellipse(_bbox(ox + length, oy, w / 2, w / 2), fill=color, outline=None)

        return paint

    for layer, color, w in (("outline", OUTLINE, width + 2.8), ("fill", pal["robe"], width)):
        _put(img, _piece((spec.target_name, "upper_arm", layer), half, stroke(color, w, upper_len, True)), shoulder, upper_deg, f"{side}_upper_arm_{layer}")
        if layer == "outline":
            _put(img, _piece((spec.target_name, "forearm", layer), half, stroke(color, w, lower_len, False)), elbow, lower_deg, f"{side}_forearm_{layer}")

    def paint_forearm(d, ox: float, oy: float) -> None:
        _draw_line(d, [(ox, oy), (ox + lower_len, oy)], pal["robe"], width)
        d.ellipse(_bbox(ox, oy, width * 0.26, width * 0.26), fill=pal["robe"], outline=OUTLINE)
        d.ellipse(_bbox(ox + lower_len, oy, width * 0.33, width * 0.33), fill=pal["skin"], outline=OUTLINE)

    _put(img, _piece((spec.target_name, "forearm", "fill"), half, paint_forearm), elbow, lower_deg, f"{side}_forearm_fill")


def render_frame(variant_name: str, anim: str, frame_idx: int, nframes: int) -> Image.Image:
    spec = VARIANTS[variant_name]
    pal = spec.palette
    st = _frame_state(anim, frame_idx, nframes, spec)

    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), TRANSPARENT)

    can = spec.confidence
    slouch = spec.slouch
    center_x = 64.0
    bob = st["body_bob"]
    foot_y = 118.0 + bob
    hip_y = 91.0 + bob + slouch * 0.25
    shoulder_y = 66.0 + bob + slouch * 0.55
    head_y = 36.0 + bob + slouch * 0.7
    torso_shift_x = st["torso_tilt"] * 16.0
    torso_x = center_x + torso_shift_x
    shoulder_l = (torso_x - 16.0, shoulder_y)
    shoulder_r = (torso_x + 16.0, shoulder_y + 0.6)
    # The torso's pieces are painted about this point and ride it.
    torso_at = (torso_x, 80.0 + bob)

    # Back cape and silhouette extenders.
    cape_wave = round(math.sin(st["cyc"] + (0.0 if anim == "walk" else 1.1)), 1)
    cape = _piece(
        (variant_name, "cape", cape_wave), (30.0, 42.0),
        lambda d, ox, oy: _paint_cape(d, pal, ox, oy - 80.0, can, cape_wave),
    )
    _put(img, cape, torso_at, 0.0, "cape")

    # Legs: each one piece about its hip, keyed by its knee and foot.
    left_stride = -5.0 - st["stride"] * 0.60
    right_stride = 5.0 + st["stride"] * 0.60
    knee_drop_l = 12.0 - abs(st["stride"]) * 0.15
    knee_drop_r = 12.0 + abs(st["stride"]) * 0.08
    left_knee = (center_x - 7.0 + left_stride * 0.18, hip_y + knee_drop_l)
    right_knee = (center_x + 7.0 + right_stride * 0.18, hip_y + knee_drop_r)
    left_foot = (center_x - 7.0 + left_stride, foot_y)
    right_foot = (center_x + 8.0 + right_stride, foot_y)
    for side, hip, knee, foot in [("left", (center_x - 6.0, hip_y), left_knee, left_foot), ("right", (center_x + 6.0, hip_y), right_knee, right_foot)]:
        dk = (round((knee[0] - hip[0]) * 2) / 2, round((knee[1] - hip[1]) * 2) / 2)
        df = (round((foot[0] - hip[0]) * 2) / 2, round((foot[1] - hip[1]) * 2) / 2)
        leg = _piece(
            (variant_name, "leg", dk, df), (20.0, 34.0),
            lambda d, ox, oy, dk=dk, df=df: _paint_leg(d, pal, (ox, oy), (ox + dk[0], oy + dk[1]), (ox + df[0], oy + df[1])),
        )
        _put(img, leg, hip, 0.0, f"{side}_leg")

    # Robe body, mantle, lamellar and belt.
    robe = _piece((variant_name, "robe"), (28.0, 42.0), lambda d, ox, oy: _paint_robe(d, pal, ox, oy - 80.0, can))
    _put(img, robe, torso_at, 0.0, "robe")

    # Arms.
    if anim == "walk":
        a = st["step"]
        left_upper = math.radians(_lerp(122, 112, can)) + a * 0.46
        left_lower = math.radians(_lerp(-36, -22, can))
        right_upper = math.radians(_lerp(44, 32, can)) - a * 0.46
        right_lower = math.radians(_lerp(26, 18, can))
    elif anim == "talk":
        left_upper = math.radians(_lerp(118, 90, can))
        left_lower = math.radians(_lerp(-44, -16, can))
        right_upper = math.radians(_lerp(25, -10, can)) - st["talk"] * 0.34
        right_lower = math.radians(_lerp(40, 58, can))
    elif anim == "interact":
        left_upper = math.radians(_lerp(130, 106, can))
        left_lower = math.radians(_lerp(-34, -18, can))
        right_upper = math.radians(_lerp(10, -58, can)) - st["interact"] * 0.30
        right_lower = math.radians(_lerp(54, 74, can))
    elif anim == "taunt":
        left_upper = math.radians(_lerp(118, 86, can))
        left_lower = math.radians(_lerp(-32, -12, can))
        right_upper = math.radians(_lerp(52, -22, can))
        right_lower = math.radians(_lerp(36, 66, can))
    else:
        left_upper = math.radians(_lerp(126, 112, can))
        left_lower = math.radians(_lerp(-26, -12, can))
        right_upper = math.radians(_lerp(38, 16, can))
        right_lower = math.radians(_lerp(20, 44, can))

    _place_arm(img, spec, "left", shoulder_l, left_upper, left_lower)
    _place_arm(img, spec, "right", shoulder_r, right_upper, right_lower)

    # Neck.
    def paint_neck(d, ox: float, oy: float) -> None:
        d.rounded_rectangle((_s(ox - 4.0), _s(oy - 29.0), _s(ox + 4.0), _s(oy - 22.0)), radius=_s(1.8), fill=pal["skin_shadow"], outline=OUTLINE)

    _put(img, _piece((variant_name, "neck"), (8.0, 32.0), paint_neck), torso_at, 0.0, "neck")

    # Head and face: one piece per (rounded) mouth.
    head_cx = torso_x + _lerp(-1.4, 0.2, can)
    talking = anim == "talk"
    mouth_open = round(st["mouth_open"] * 20.0) / 20.0
    head = _piece(
        (variant_name, "head", talking, mouth_open), (22.0, 34.0),
        lambda d, ox, oy: _paint_head(d, spec, ox, oy, talking, mouth_open),
    )
    _put(img, head, (head_cx, head_y), 0.0, "head")

    # Final tunic trim and fur cuffs in front.
    def paint_trim(d, ox: float, oy: float) -> None:
        d.rectangle((_s(ox - 22.0), _s(oy - 3.0), _s(ox - 17.0), _s(oy + 5.0)), fill=pal["trim"], outline=OUTLINE)
        d.rectangle((_s(ox + 17.0), _s(oy - 3.0), _s(ox + 22.0), _s(oy + 5.0)), fill=pal["trim"], outline=OUTLINE)

    _put(img, _piece((variant_name, "trim"), (24.0, 8.0), paint_trim), torso_at, 0.0, "trim")

    return _downsample(img)


def render_portraits(variant_name: str, out_dir: str | Path, **opts) -> List[Path]:
    del opts
    spec = VARIANTS[variant_name]

    def portrait_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        source = render_frame(variant_name, animation, frame_idx, frame_count)
        face = FaceGuide(
            center_x=64.0,
            center_y=28.0 + spec.slouch * 0.45,
            width=30.0,
            height=32.0,
            source_width=128.0,
            source_height=128.0,
        )
        return render_framed_portrait(source, face)

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 2, 8)),
        "talking": PortraitClip(tuple(portrait_frame("talk", i, 6) for i in range(6)), duration_ms=100, looping=True),
        "emote": PortraitClip.still(portrait_frame("taunt", 3, 8)),
    }
    return write_portrait_sheet(spec.target_name, clips, Path(out_dir))


def render_target(variant_name: str, out_dir: str | Path, **opts) -> List[Path]:
    del opts
    spec = VARIANTS[variant_name]

    def render_fn(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        return render_frame(variant_name, animation, frame_idx, frame_count)

    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=spec.target_name,
        rows=ROWS,
        render_fn=render_fn,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA[variant_name],
        sheet_tuning={"collision_scale": 1.68},
    )
    keys = (
        "spritesheet",
        "yaml",
        "ron",
        "actor",
        "canonical",
        "canonical_transparent",
        "preview",
    )
    parts = publish_rig_flipbook(spec.target_name, ROWS, render_fn, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())
