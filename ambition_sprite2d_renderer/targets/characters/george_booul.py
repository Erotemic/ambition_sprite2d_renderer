"""Classic sheet-ghost sprite target for George Boo'l.

George Boo'l is a playful George Boole parody.  He is deliberately rendered as
an unmistakable old-fashioned bedsheet ghost: one draped cloth silhouette, two
eye holes, a mouth hole, little raised sheet-corners for hands, and a scalloped
hem.  Boolean ideas appear in the animation language rather than through a
busy costume:

* TRUE is the ordinary pale sheet state;
* FALSE is the inverted charcoal sheet state;
* NOT flips between those states;
* AND focuses two inputs into one green logic discharge;
* a failed proposition makes the sheet collapse like abandoned laundry.

The mixed cast of humans, animals, machines, ghosts, and other beings is normal
in Ambition.  Nobody needs to explain why Boo'l is a ghost.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "george_booul"
FRAME_SIZE = (160, 160)
SUPER = 4
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER
CENTER_X = 80.0
GROUND_Y = 137.0

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 132),
    ("idle_false", 8, 132),
    ("drift", 8, 96),
    ("toggle_state", 8, 88),
    ("and_zap", 8, 78),
    ("not_fade", 8, 92),
    ("hit", 5, 88),
    ("death", 8, 112),
    ("taunt", 8, 104),
]

SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]

AUTHORING_DESCRIPTION = (
    "George Boo'l parodies George Boole, whose algebra of true/false values "
    "became foundational to logic and computing. The design intentionally uses "
    "the simplest possible Halloween bedsheet ghost silhouette. Boolean ideas "
    "are expressed through state inversion and attack staging rather than a "
    "literal scholar costume: white sheet means TRUE, charcoal sheet means "
    "FALSE, NOT flips the palette, AND merges two inputs, and defeat leaves an "
    "empty sheet on the floor. The name is pronounced like 'George Boole' with "
    "a ghostly 'boo' emphasized."
)

GAMEPLAY_DESCRIPTION = (
    "Suggested gameplay role: lightweight hovering trap-zoner. Boo'l drifts "
    "smoothly, changes between TRUE and FALSE states, and converts placed logic "
    "marks into short ranged bursts. TRUE should favor readable setup and "
    "control; FALSE can favor feints, brief fades, and counterplay. His attacks "
    "should feel clean and binary rather than visually noisy."
)

SUGGESTED_BARKS = {
    "idle": [
        "True. False. Boo.",
        "A tidy proposition, at last.",
        "Mind the operator.",
    ],
    "provoked": [
        "Then let us test your premise.",
        "That does not follow.",
    ],
    "on_hit": [
        "An invalid operation!",
        "You wrinkled the proof!",
    ],
    "victory": [
        "The proposition stands.",
        "Decided conclusively.",
    ],
}

FALLBACK_DIALOGUE = [
    "A proposition does not become true merely because it is loud.",
    "Elegant systems survive contact with inconvenient examples.",
    "Most confusion is only a missing operator wearing a dramatic hat.",
    "I haunt the space between yes and no. It is busier than one expects.",
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_george_booul",
        "actor_id": "george_booul",
        "display_name": "George Boo'l",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "locomotion_hint": "Hover",
        "traits": [
            "story",
            "ghost",
            "logic",
            "boolean",
            "playable_candidate",
        ],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "fly": True,
            "swim": None,
            "crawl": None,
            "use_lifts": True,
            "door_access": ["public", "service"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public", "service"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle", "music_cue": "scholar_haunt"},
    "dialogue_hints": {
        "barks": [line for lines in SUGGESTED_BARKS.values() for line in lines],
        "fallback_dialogue": FALLBACK_DIALOGUE,
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "drift", "events": []},
        "interaction.talk": {"animation": "taunt", "events": []},
        "action.cast.primary": {"animation": "and_zap", "events": []},
        "action.cast.secondary": {"animation": "toggle_state", "events": []},
        "action.special": {"animation": "not_fade", "events": []},
        "damage.hit": {"animation": "hit", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "george_booul.geometry", "point": {"x": 80.0, "y": 48.0}},
        "chest": {"source": "george_booul.geometry", "point": {"x": 80.0, "y": 82.0}},
        "hand_l": {"source": "george_booul.geometry", "point": {"x": 48.0, "y": 86.0}},
        "hand_r": {"source": "george_booul.geometry", "point": {"x": 112.0, "y": 86.0}},
        "speech_bubble": {"source": "george_booul.geometry", "point": {"x": 80.0, "y": 13.0}},
        "focus": {"source": "george_booul.geometry", "point": {"x": 80.0, "y": 63.0}},
    },
    "tags": ["story", "ghost", "logic", "boolean", "playable_candidate"],
}

INK = (20, 25, 30, 255)
INK_SOFT = (65, 73, 81, 255)
TRUE_CLOTH = (238, 243, 232, 255)
TRUE_LIGHT = (255, 255, 247, 255)
TRUE_SHADOW = (183, 199, 190, 255)
FALSE_CLOTH = (43, 42, 50, 255)
FALSE_LIGHT = (79, 73, 88, 255)
FALSE_SHADOW = (24, 25, 31, 255)
TRUE_EYE = (19, 28, 27, 255)
FALSE_EYE = (244, 106, 53, 255)
LOGIC_GREEN = (113, 231, 135, 255)
LOGIC_GREEN_LIGHT = (205, 255, 192, 255)
LOGIC_RED = (244, 95, 60, 255)
LOGIC_GOLD = (244, 211, 104, 255)


@dataclass
class Pose:
    state: float = 1.0
    x: float = 0.0
    y: float = 0.0
    tilt: float = 0.0
    bob: float = 0.0
    arm_l: float = 0.0
    arm_r: float = 0.0
    hand_l_y: float = 0.0
    hand_r_y: float = 0.0
    hem_wave: float = 0.0
    eye_scale: float = 1.0
    mouth_open: float = 0.0
    blink: bool = False
    opacity: float = 1.0
    squash_x: float = 1.0
    squash_y: float = 1.0
    fx: str = ""
    fx_strength: float = 0.0
    collapse: float = 0.0
    phase: float = 0.0


def _s(value: float) -> int:
    return max(1, round(value * SUPER))


def _pt(x: float, y: float) -> Point:
    return (x * SUPER, y * SUPER)


def _box(x0: float, y0: float, x1: float, y1: float) -> Tuple[int, int, int, int]:
    return (
        round(x0 * SUPER),
        round(y0 * SUPER),
        round(x1 * SUPER),
        round(y1 * SUPER),
    )


def _rgba(color: RGBA, alpha: float = 1.0) -> RGBA:
    return (
        color[0],
        color[1],
        color[2],
        max(0, min(255, round(color[3] * alpha))),
    )


def _lerp_color(a: RGBA, b: RGBA, t: float) -> RGBA:
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(4))  # type: ignore[return-value]


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _downsample(img: Image.Image) -> Image.Image:
    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _pose(animation: str, frame_idx: int, nframes: int) -> Pose:
    p = Pose()
    phase = frame_idx / max(1, nframes)
    t = frame_idx / max(1, nframes - 1)
    wave = math.sin(phase * math.tau)
    wave2 = math.sin(phase * math.tau * 2.0)
    p.phase = phase

    if animation == "idle":
        p.state = 1.0
        p.y = -2.5 * (0.5 - 0.5 * math.cos(phase * math.tau))
        p.x = 1.2 * wave
        p.tilt = 1.7 * wave
        p.hem_wave = wave
        p.arm_l = 2.0 * wave
        p.arm_r = -2.0 * wave
        p.blink = frame_idx == 6
    elif animation == "idle_false":
        p.state = 0.0
        p.y = -2.0 * (0.5 - 0.5 * math.cos(phase * math.tau))
        p.x = -1.0 * wave
        p.tilt = -1.5 * wave
        p.hem_wave = -wave
        p.arm_l = -1.5 * wave
        p.arm_r = 1.5 * wave
        p.eye_scale = 1.0 + 0.08 * wave2
        p.blink = frame_idx == 2
    elif animation == "drift":
        p.state = 1.0
        p.x = 7.0 * wave
        p.y = -4.0 * abs(wave)
        p.tilt = 4.0 * wave
        p.hem_wave = 1.5 * wave
        p.arm_l = -7.0 * wave
        p.arm_r = 7.0 * wave
        p.hand_l_y = 2.0 * wave
        p.hand_r_y = -2.0 * wave
    elif animation == "toggle_state":
        flip = _smoothstep(t)
        p.state = 1.0 - flip
        p.y = -4.0 * math.sin(t * math.pi)
        p.tilt = 360.0 * t
        p.squash_x = 1.0 - 0.45 * math.sin(t * math.pi)
        p.squash_y = 1.0 + 0.25 * math.sin(t * math.pi)
        p.arm_l = -12.0 * math.sin(t * math.pi)
        p.arm_r = 12.0 * math.sin(t * math.pi)
        p.fx = "toggle"
        p.fx_strength = math.sin(t * math.pi)
    elif animation == "and_zap":
        p.state = 1.0
        charge = math.sin(t * math.pi)
        p.y = -3.0 * charge
        p.tilt = 2.0 * wave
        p.arm_l = -22.0 * charge
        p.arm_r = 22.0 * charge
        p.hand_l_y = -8.0 * charge
        p.hand_r_y = -8.0 * charge
        p.hem_wave = wave
        p.mouth_open = 0.35 + 0.5 * charge
        p.fx = "and"
        p.fx_strength = charge
    elif animation == "not_fade":
        pulse = math.sin(t * math.pi)
        p.state = 1.0 - _smoothstep(min(1.0, t * 1.2))
        p.y = -6.0 * pulse
        p.x = 5.0 * math.sin(t * math.tau)
        p.tilt = -10.0 * pulse
        p.arm_l = -10.0 * pulse
        p.arm_r = 10.0 * pulse
        p.opacity = 1.0 - 0.55 * pulse
        p.fx = "not"
        p.fx_strength = pulse
    elif animation == "hit":
        impact = math.sin(t * math.pi)
        p.state = 1.0
        p.x = -9.0 * impact
        p.y = 2.0 * impact
        p.tilt = -13.0 * impact
        p.squash_x = 1.0 + 0.12 * impact
        p.squash_y = 1.0 - 0.10 * impact
        p.arm_l = 11.0 * impact
        p.arm_r = -11.0 * impact
        p.eye_scale = 0.8
        p.mouth_open = 0.8 * impact
        p.fx = "hit"
        p.fx_strength = impact
    elif animation == "death":
        p.state = 1.0
        if t < 0.35:
            u = t / 0.35
            p.y = 3.0 * u
            p.x = -3.0 * u
            p.tilt = -16.0 * u
            p.arm_l = 8.0 * u
            p.arm_r = -8.0 * u
            p.mouth_open = 0.5 * u
        else:
            u = _smoothstep((t - 0.35) / 0.65)
            p.y = 3.0 + 24.0 * u
            p.x = -3.0 + 5.0 * u
            p.tilt = -16.0 + 19.0 * u
            p.squash_x = 1.0 + 0.45 * u
            p.squash_y = 1.0 - 0.66 * u
            p.arm_l = 8.0 * (1.0 - u)
            p.arm_r = -8.0 * (1.0 - u)
            p.eye_scale = 1.0 - 0.65 * u
            p.opacity = 1.0 - 0.18 * u
            p.collapse = u
            p.blink = u > 0.35
    elif animation == "taunt":
        p.state = 1.0
        p.y = -3.0 * (0.5 - 0.5 * math.cos(phase * math.tau))
        p.x = 2.0 * wave
        p.tilt = 4.0 * wave
        p.arm_l = -18.0 * math.sin(phase * math.tau * 0.5)
        p.arm_r = 18.0 * math.sin(phase * math.tau * 0.5)
        p.hand_l_y = -8.0 * abs(wave)
        p.hand_r_y = -8.0 * abs(wave)
        p.hem_wave = wave2
        p.mouth_open = 0.35 + 0.35 * (0.5 + 0.5 * wave2)
    return p


def _sheet_palette(state: float):
    cloth = _lerp_color(FALSE_CLOTH, TRUE_CLOTH, state)
    light = _lerp_color(FALSE_LIGHT, TRUE_LIGHT, state)
    shadow = _lerp_color(FALSE_SHADOW, TRUE_SHADOW, state)
    eyes = _lerp_color(FALSE_EYE, TRUE_EYE, state)
    outline = _lerp_color((11, 12, 16, 255), INK, state)
    return cloth, light, shadow, eyes, outline


def _draw_fx(draw: ImageDraw.ImageDraw, p: Pose, cx: float, cy: float) -> None:
    alpha = p.opacity
    if p.fx == "toggle":
        radius = 22.0 + 20.0 * p.fx_strength
        draw.arc(
            _box(cx - radius, cy - radius, cx + radius, cy + radius),
            start=20,
            end=330,
            fill=_rgba(LOGIC_GOLD, alpha),
            width=_s(2.0),
        )
        draw.line(
            [_pt(cx - radius * 0.75, cy - radius * 0.5), _pt(cx + radius * 0.75, cy + radius * 0.5)],
            fill=_rgba(LOGIC_RED, alpha),
            width=_s(2.2),
        )
    elif p.fx == "and":
        strength = p.fx_strength
        left = (cx - 33.0, cy - 2.0)
        right = (cx + 33.0, cy - 2.0)
        focus = (cx, cy + 4.0)
        for px, py in (left, right):
            draw.ellipse(
                _box(px - 4.0, py - 4.0, px + 4.0, py + 4.0),
                fill=_rgba(LOGIC_GREEN_LIGHT, alpha),
                outline=_rgba(INK, alpha),
                width=_s(0.8),
            )
            draw.line(
                [_pt(px, py), _pt(focus[0], focus[1])],
                fill=_rgba(LOGIC_GREEN, strength * alpha),
                width=_s(2.0 + strength),
            )
        beam_end = cx + 32.0 + 28.0 * strength
        draw.line(
            [_pt(focus[0], focus[1]), _pt(beam_end, focus[1])],
            fill=_rgba(LOGIC_GREEN_LIGHT, strength * alpha),
            width=_s(3.0 + 2.0 * strength),
        )
        draw.line(
            [_pt(focus[0], focus[1]), _pt(beam_end, focus[1])],
            fill=_rgba(LOGIC_GREEN, strength * alpha),
            width=_s(1.2 + strength),
        )
    elif p.fx == "not":
        radius = 18.0 + 15.0 * p.fx_strength
        draw.ellipse(
            _box(cx - radius, cy - radius, cx + radius, cy + radius),
            outline=_rgba(LOGIC_RED, p.fx_strength * alpha),
            width=_s(1.8),
        )
        draw.line(
            [_pt(cx - radius * 0.70, cy - radius * 0.70), _pt(cx + radius * 0.70, cy + radius * 0.70)],
            fill=_rgba(LOGIC_RED, p.fx_strength * alpha),
            width=_s(2.0),
        )
    elif p.fx == "hit":
        strength = p.fx_strength
        for angle in (0.0, math.pi * 0.7, math.pi * 1.35):
            x0 = cx + math.cos(angle) * 28.0
            y0 = cy + math.sin(angle) * 24.0
            x1 = cx + math.cos(angle) * (35.0 + 10.0 * strength)
            y1 = cy + math.sin(angle) * (31.0 + 10.0 * strength)
            draw.line(
                [_pt(x0, y0), _pt(x1, y1)],
                fill=_rgba(LOGIC_RED, strength * alpha),
                width=_s(1.5),
            )


def _draw_sheet(img: Image.Image, p: Pose) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = blending_draw(layer)
    cx = CENTER_X + p.x
    top = 29.0 + p.y
    bottom = GROUND_Y + p.y
    cloth, light, shadow, eye_color, outline = _sheet_palette(p.state)
    alpha = p.opacity

    # Back glow only during logic actions; never a ground shadow.
    if p.fx_strength > 0.01:
        glow = LOGIC_GREEN if p.fx == "and" else LOGIC_RED
        radius = 34.0 + 8.0 * p.fx_strength
        draw.ellipse(
            _box(cx - radius, top + 8.0 - radius * 0.25, cx + radius, bottom + radius * 0.25),
            fill=_rgba(glow, 0.12 * p.fx_strength * alpha),
        )

    # Little raised sheet-corners functioning as ghost hands.
    shoulder_y = top + 47.0
    left_hand = (cx - 34.0 + p.arm_l * 0.45, shoulder_y + p.hand_l_y)
    right_hand = (cx + 34.0 + p.arm_r * 0.45, shoulder_y + p.hand_r_y)
    left_arm = [
        (cx - 20.0, shoulder_y - 4.0),
        (left_hand[0] + 4.0, left_hand[1] - 8.0),
        (left_hand[0] - 4.0, left_hand[1] + 2.0),
        (cx - 24.0, shoulder_y + 12.0),
    ]
    right_arm = [
        (cx + 20.0, shoulder_y - 4.0),
        (right_hand[0] - 4.0, right_hand[1] - 8.0),
        (right_hand[0] + 4.0, right_hand[1] + 2.0),
        (cx + 24.0, shoulder_y + 12.0),
    ]
    draw.polygon([_pt(*q) for q in left_arm], fill=_rgba(shadow, alpha), outline=_rgba(outline, alpha))
    draw.polygon([_pt(*q) for q in right_arm], fill=_rgba(shadow, alpha), outline=_rgba(outline, alpha))

    # Main draped sheet silhouette.
    hem = [
        (cx + 31.0, bottom - 22.0),
        (cx + 29.0, bottom - 10.0 + 1.5 * p.hem_wave),
        (cx + 22.0, bottom - 2.0 - 2.0 * p.hem_wave),
        (cx + 13.0, bottom - 10.0 + 2.0 * p.hem_wave),
        (cx + 4.0, bottom - 1.0 - 1.5 * p.hem_wave),
        (cx - 5.0, bottom - 10.0 + 2.2 * p.hem_wave),
        (cx - 14.0, bottom - 2.0 - 1.4 * p.hem_wave),
        (cx - 23.0, bottom - 10.0 + 1.7 * p.hem_wave),
        (cx - 31.0, bottom - 3.0 - 1.4 * p.hem_wave),
        (cx - 34.0, bottom - 22.0),
    ]
    sheet = [
        (cx, top),
        (cx + 13.0, top + 5.0),
        (cx + 23.0, top + 18.0),
        (cx + 29.0, top + 36.0),
        (cx + 32.0, bottom - 23.0),
        *hem,
        (cx - 32.0, bottom - 23.0),
        (cx - 29.0, top + 36.0),
        (cx - 23.0, top + 18.0),
        (cx - 13.0, top + 5.0),
    ]
    draw.polygon([_pt(*q) for q in sheet], fill=_rgba(cloth, alpha), outline=_rgba(outline, alpha))

    # Cloth highlight and broad folds.
    highlight = [
        (cx - 6.0, top + 5.0),
        (cx + 3.0, top + 6.0),
        (cx + 9.0, top + 21.0),
        (cx + 7.0, bottom - 18.0),
        (cx - 2.0, bottom - 9.0),
        (cx - 9.0, top + 25.0),
    ]
    draw.polygon([_pt(*q) for q in highlight], fill=_rgba(light, 0.54 * alpha))
    fold_specs = [
        (-18.0, top + 22.0, -23.0, bottom - 17.0),
        (-6.0, top + 18.0, -9.0, bottom - 12.0),
        (8.0, top + 19.0, 14.0, bottom - 15.0),
        (20.0, top + 27.0, 24.0, bottom - 19.0),
    ]
    for x0, y0, x1, y1 in fold_specs:
        draw.line(
            [_pt(cx + x0, y0), _pt(cx + x1, y1)],
            fill=_rgba(shadow, 0.65 * alpha),
            width=_s(1.1),
        )

    # Face holes: classic, simple, and readable.
    eye_y = top + 27.0
    for ex in (cx - 8.0, cx + 8.0):
        if p.blink:
            draw.line(
                [_pt(ex - 4.0, eye_y), _pt(ex + 4.0, eye_y)],
                fill=_rgba(eye_color, alpha),
                width=_s(1.8),
            )
        else:
            ew = 5.1 * p.eye_scale
            eh = 7.0 * p.eye_scale
            draw.ellipse(
                _box(ex - ew, eye_y - eh, ex + ew, eye_y + eh),
                fill=_rgba(eye_color, alpha),
            )
            # A pinprick highlight keeps FALSE-state eyes alive at small scale.
            if p.state < 0.5:
                draw.ellipse(
                    _box(ex - 1.3, eye_y - 2.3, ex + 0.6, eye_y - 0.4),
                    fill=_rgba(LOGIC_GOLD, alpha),
                )

    mouth_y = top + 47.0
    mouth_w = 5.5 + 1.5 * p.mouth_open
    mouth_h = 3.5 + 6.0 * p.mouth_open
    draw.ellipse(
        _box(cx - mouth_w, mouth_y - mouth_h, cx + mouth_w, mouth_y + mouth_h),
        fill=_rgba(eye_color, alpha),
    )

    # Small logic badge at the throat: restrained, not costume-like.
    badge_y = top + 64.0
    badge_color = LOGIC_GREEN if p.state >= 0.5 else LOGIC_RED
    draw.ellipse(
        _box(cx - 4.2, badge_y - 4.2, cx + 4.2, badge_y + 4.2),
        fill=_rgba(badge_color, alpha),
        outline=_rgba(outline, alpha),
        width=_s(0.7),
    )
    mark_x = cx - 1.0 if p.state >= 0.5 else cx
    draw.line(
        [_pt(mark_x, badge_y - 2.2), _pt(mark_x, badge_y + 2.2)],
        fill=_rgba(TRUE_LIGHT if p.state >= 0.5 else LOGIC_GOLD, alpha),
        width=_s(1.0),
    )

    _draw_fx(draw, p, cx, top + 50.0)

    if p.squash_x != 1.0 or p.squash_y != 1.0:
        crop = layer.crop(_box(34.0, 15.0, 126.0, 144.0))
        target = (_s(92.0 * p.squash_x), _s(129.0 * p.squash_y))
        crop = crop.resize(target, Image.Resampling.BICUBIC)
        scaled = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        x = _s(CENTER_X) - target[0] // 2
        y = _s(144.0) - target[1]
        scaled.alpha_composite(crop, (x, y))
        layer = scaled

    if abs(p.tilt) > 0.01:
        layer = layer.rotate(
            p.tilt,
            resample=Image.Resampling.BICUBIC,
            center=_pt(CENTER_X + p.x, 85.0 + p.y),
            fillcolor=(0, 0, 0, 0),
        )

    img.alpha_composite(layer)


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _draw_sheet(img, _pose(animation, frame_idx, nframes))
    return _downsample(img)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=112,
        actor_metadata=ACTOR_METADATA,
        auto_crop=False,
        trim=False,
    )
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
    ]


__all__ = [
    "ACTOR_METADATA",
    "AUTHORING_DESCRIPTION",
    "FALLBACK_DIALOGUE",
    "FRAME_SIZE",
    "GAMEPLAY_DESCRIPTION",
    "ROWS",
    "SHEET_FILES",
    "SUGGESTED_BARKS",
    "TARGET_NAME",
    "render",
    "render_frame",
]
