"""Alice, a cipher courier in an ivory split coat and indigo tailoring.

Editable SVG paper-doll parts share one articulated pose path across views.
Authored action poses and procedural cartography effects feed the normal sheet
and portrait publisher.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from ...profiling import profile
from .alice_paper_doll import draw_doll
from ...authoring.animation_vocab import (
    DEFAULT_ADVANCED_TIMINGS,
    DEFAULT_DIRECTIONAL_ATTACK_TIMINGS,
    DEFAULT_EXTENDED_TIMINGS,
    DEFAULT_TRAVERSAL_POLISH_TIMINGS,
)
from ambition_sprite2d_renderer.core.draw import blending_draw
from ...authoring.generator import CharacterGenerator
from ...registry import CharacterJob
from ambition_sprite2d_renderer.core.draw import rgba

Color = Tuple[int, int, int, int]
Point = Tuple[float, float]


def parse_background(value: str) -> Optional[Color]:
    return None if str(value).lower() == "transparent" else rgba(str(value))


def _scaled(color: Color, factor: float) -> Color:
    return (
        max(0, min(255, round(color[0] * factor))),
        max(0, min(255, round(color[1] * factor))),
        max(0, min(255, round(color[2] * factor))),
        color[3],
    )


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smoothstep(value: float) -> float:
    t = _clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


ALICE_PALETTE: Dict[str, Color] = {
    "outline": rgba("#0B1118"),
    "skin": rgba("#E5BFA1"),
    "skin_shadow": rgba("#B98569"),
    "skin_light": rgba("#F3D8BD"),
    "hair": rgba("#101722"),
    "hair_mid": rgba("#25364B"),
    "hair_light": rgba("#48627B"),
    "jacket": rgba("#176878"),
    "jacket_dark": rgba("#0B3C49"),
    "jacket_light": rgba("#2A93A2"),
    "shirt": rgba("#E8E0C7"),
    "shirt_shadow": rgba("#B7AA88"),
    "trouser": rgba("#293542"),
    "trouser_dark": rgba("#18212C"),
    "boot": rgba("#241C1A"),
    "boot_light": rgba("#4A342B"),
    "leather": rgba("#8C4F32"),
    "leather_dark": rgba("#4F2D22"),
    "amber": rgba("#D99A3D"),
    "amber_light": rgba("#F0C36A"),
    "map": rgba("#F2E5B9"),
    "map_shadow": rgba("#C9B77C"),
    "map_ink": rgba("#315C63"),
    "route": rgba("#C6514B"),
    "seal": rgba("#B9443D"),
    "metal": rgba("#D7D8D1"),
    "metal_dark": rgba("#68727A"),
    "eye": rgba("#263E4C"),
    "white": rgba("#FBF4E5"),
}


class AliceView(str, Enum):
    THREE_QUARTER = "three_quarter"
    FRONT = "front"
    SIDE = "side"


ANIMATION_VIEWS: Dict[str, AliceView] = {
    "idle": AliceView.THREE_QUARTER,
    "talk": AliceView.FRONT,
    "interact": AliceView.THREE_QUARTER,
    "idle_front": AliceView.FRONT,
    "idle_side": AliceView.SIDE,
}


@dataclass(frozen=True)
class AliceSpec:
    target: str
    seed: int
    archetype: str
    name: str
    role: str
    palette_name: str



@dataclass
class AlicePose:
    view: AliceView
    body_bob: float = 0.0
    head_tilt: float = 0.0
    blink: bool = False
    talk_open: float = 0.0
    step: float = 0.0
    gesture: float = 0.0
    map_open: float = 0.0
    scan: float = 0.0
    walk_index: int = -1
    walk_body_y: float = 0.0

    # Player-grade side-view action controls, authored in 128px source space.
    root_x: float = 0.0
    root_y: float = 0.0
    lean: float = 0.0
    crouch: float = 0.0
    gait_scale: float = 1.0
    arm_swing: float = 1.0
    far_hand: Optional[Point] = None
    near_hand: Optional[Point] = None
    far_foot: Optional[Point] = None
    near_foot: Optional[Point] = None
    far_bend: float = -1.0
    near_bend: float = -1.0
    prop: str = "folio"
    tool_angle: float = 0.0
    effect: str = ""
    effect_strength: float = 0.0
    rotation: float = 0.0
    opacity: float = 1.0
    hit_flash: float = 0.0


def _bbox(
    cx: float, cy: float, w: float, h: float
) -> Tuple[float, float, float, float]:
    return (cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0)


def _poly(
    d: ImageDraw.ImageDraw,
    points: Sequence[Point],
    *,
    fill: Color,
    outline: Color,
    width: int,
) -> None:
    pts = [(round(x), round(y)) for x, y in points]
    d.polygon(pts, fill=fill)
    d.line([*pts, pts[0]], fill=outline, width=max(1, width), joint="curve")


def _line(
    d: ImageDraw.ImageDraw,
    points: Iterable[Point],
    *,
    fill: Color,
    width: int,
) -> None:
    d.line(
        [(round(x), round(y)) for x, y in points],
        fill=fill,
        width=max(1, width),
        joint="curve",
    )


def _ellipse(
    d: ImageDraw.ImageDraw,
    box: Tuple[float, float, float, float],
    *,
    fill: Color,
    outline: Optional[Color] = None,
    width: int = 1,
) -> None:
    d.ellipse(
        tuple(round(v) for v in box), fill=fill, outline=outline, width=max(1, width)
    )


def _rounded(
    d: ImageDraw.ImageDraw,
    box: Tuple[float, float, float, float],
    *,
    radius: float,
    fill: Color,
    outline: Optional[Color] = None,
    width: int = 1,
) -> None:
    d.rounded_rectangle(
        tuple(round(v) for v in box),
        radius=max(1, round(radius)),
        fill=fill,
        outline=outline,
        width=max(1, width),
    )


class AliceCryptographerGenerator(CharacterGenerator):
    name = "alice_cryptographer"
    target = "alice_cryptographer"
    applies_job_name = True

    # Match the main robot's broad player vocabulary while keeping Alice's
    # actual poses, props, and effects character-specific.
    ANIMATIONS: Dict[str, Dict[str, int]] = {
        "idle": {"frames": 8, "duration_ms": 120},
        "walk": {"frames": 8, "duration_ms": 95},
        "run": {"frames": 8, "duration_ms": 72},
        "jump": {"frames": 6, "duration_ms": 90},
        "fall": {"frames": 6, "duration_ms": 92},
        "slash": {"frames": 8, "duration_ms": 66},
        "hit": {"frames": 5, "duration_ms": 86},
        "death": {"frames": 8, "duration_ms": 105},
        "blink_out": {"frames": 6, "duration_ms": 58},
        "blink_in": {"frames": 6, "duration_ms": 58},
        "dash": {"frames": 6, "duration_ms": 60},
        **DEFAULT_EXTENDED_TIMINGS,
        **DEFAULT_ADVANCED_TIMINGS,
        **DEFAULT_TRAVERSAL_POLISH_TIMINGS,
        **DEFAULT_DIRECTIONAL_ATTACK_TIMINGS,
        "idle_front": {"frames": 8, "duration_ms": 120},
        "idle_side": {"frames": 8, "duration_ms": 120},
    }

    def build_spec(self, job: CharacterJob) -> AliceSpec:
        if job.archetype != "alice":
            raise KeyError(
                "alice_cryptographer ships only the 'alice' archetype; "
                f"got {job.archetype!r}"
            )
        return AliceSpec(
            target=self.name,
            seed=job.seed,
            archetype=job.archetype,
            name="Alice",
            role="npc",
            palette_name="alice_ivory_cipher_courier",
        )

    def canonical_pose(self) -> Tuple[str, int]:
        return ("idle", 1)

    @profile
    def render_frame(
        self,
        spec: AliceSpec,
        animation: str,
        frame_index: int,
        size: Tuple[int, int],
        job: CharacterJob,
    ) -> Image.Image:
        anim = self.animations()[animation]
        return self.render_animation_frame(
            spec,
            animation,
            frame_index % anim["frames"],
            anim["frames"],
            size,
            background=parse_background(job.render.background),
            supersample=job.render.supersample,
            downsample=job.render.downsample,
        )

    def body_inset(self) -> Dict[str, float]:
        # Hair, coat tails, and carried maps extend beyond the collision volume.
        return {"left": 0.08, "right": 0.08, "top": 0.02, "bottom": 0.0}

    def attack_hitboxes(self, size: Tuple[int, int]) -> Dict[str, Dict[str, Any]]:
        """Right-facing volumes for Alice's staff, route-pin, and compass attacks."""
        w, h = size
        cx = w * 0.5

        def hitbox(x: float, y: float, width: float, height: float) -> Dict[str, Any]:
            return {
                "bbox": (round(x), round(y), round(width), round(height)),
                "active_frames": [2, 3, 4, 5],
            }

        thrust = hitbox(cx + w * 0.02, h * 0.31, w * 0.62, h * 0.28)
        upward = hitbox(cx - w * 0.16, -h * 0.04, w * 0.48, h * 0.60)
        downward = hitbox(cx - w * 0.03, h * 0.48, w * 0.40, h * 0.52)
        backward = hitbox(cx - w * 0.55, h * 0.22, w * 0.56, h * 0.52)
        ring = hitbox(cx - w * 0.42, h * 0.16, w * 0.84, h * 0.70)
        return {
            "slash": dict(thrust),
            "attack_side": dict(thrust),
            "ledge_getup_attack": dict(thrust),
            "air_forward": dict(thrust),
            "attack_up": dict(upward),
            "air_up": dict(upward),
            "attack_down": dict(downward),
            "air_down": dict(downward),
            "air_back": dict(backward),
            "air_neutral": dict(ring),
        }

    def pose_for_animation(self, animation: str, frame: int, count: int) -> AlicePose:
        t = 0.0 if count <= 1 else frame / float(count - 1)
        wave = math.sin(t * math.tau)
        half = math.sin(t * math.pi)
        pose = AlicePose(view=ANIMATION_VIEWS.get(animation, AliceView.SIDE))

        if animation == "idle":
            pose.body_bob = 0.42 * wave
            pose.head_tilt = 0.75 * wave
            pose.blink = frame == count - 1
            pose.scan = 0.12 * wave
        elif animation in {"walk", "run", "crouch_walk"}:
            index = frame % 8
            pose.walk_index = index
            pose.step = (-1.0, -0.62, -0.18, 0.52, 1.0, 0.58, 0.08, -0.55)[index]
            pose.walk_body_y = (0.0, 1.15, 0.35, -0.65, 0.0, 1.15, 0.35, -0.65)[index]
            pose.head_tilt = (0.35, 0.10, -0.15, -0.35, -0.35, -0.10, 0.15, 0.35)[index]
            pose.prop = "none"
            if animation == "run":
                pose.gait_scale = 1.48
                pose.arm_swing = 1.52
                pose.lean = -6.5
                pose.walk_body_y *= 1.30
            elif animation == "crouch_walk":
                pose.gait_scale = 0.58
                pose.arm_swing = 0.46
                pose.crouch = 0.68
                pose.lean = -2.5
        elif animation == "jump":
            launch = _smoothstep((t - 0.08) / 0.42)
            preload = 1.0 - _smoothstep(t / 0.22)
            pose.root_y = 4.0 * preload - 12.0 * launch
            pose.lean = -5.0 - 4.0 * launch
            pose.crouch = 0.52 * preload
            pose.near_hand = (2.0, 5.0)
            pose.far_hand = (-8.0, 10.0)
            pose.near_foot = (5.0, -5.0 - 5.0 * launch)
            pose.far_foot = (-5.0, -2.0 - 7.0 * launch)
            pose.prop = "none"
        elif animation == "fall":
            pose.root_y = -10.0 + 10.0 * t
            pose.lean = 2.0 + 4.0 * t
            pose.near_hand = (11.0, 10.0)
            pose.far_hand = (-9.0, 8.0)
            pose.near_foot = (6.0, -6.0)
            pose.far_foot = (-6.0, -3.0)
            pose.prop = "none"
        elif animation in {"hover", "float_glide"}:
            pose.root_y = -9.0 + 1.1 * wave
            pose.lean = -11.0 if animation == "float_glide" else -3.0
            pose.near_hand = (12.0, 8.0 if animation == "float_glide" else 16.0)
            pose.far_hand = (-9.0, 7.0)
            pose.near_foot = (7.0, -6.0 + wave)
            pose.far_foot = (-7.0, -4.0 - wave)
            pose.prop = "map_glider"
            pose.effect = "route_glide"
            pose.effect_strength = 0.72 + 0.28 * abs(wave)
        elif animation in {"dash", "dash_startup"}:
            charge = _smoothstep(t)
            pose.crouch = 0.32 + (0.34 * charge if animation == "dash_startup" else 0.0)
            pose.lean = -10.0 - 9.0 * charge
            pose.root_x = 5.0 * charge if animation == "dash" else -2.0 * charge
            pose.near_hand = (-7.0, 16.0)
            pose.far_hand = (-13.0, 13.0)
            pose.near_foot = (8.0, -1.0)
            pose.far_foot = (-9.0, -2.0)
            pose.prop = "none"
            pose.effect = "route_speed"
            pose.effect_strength = charge
        elif animation in {"crouch", "slide"}:
            pose.crouch = 0.70 if animation == "crouch" else 0.92
            pose.lean = -2.5 if animation == "crouch" else -13.0
            pose.root_x = 4.5 * t if animation == "slide" else 0.0
            pose.near_hand = (6.0, 20.0)
            pose.far_hand = (-8.0, 17.0)
            pose.near_foot = (10.0, -1.0)
            pose.far_foot = (-8.0, -1.0)
            pose.prop = "none"
            if animation == "slide":
                pose.effect = "route_speed"
                pose.effect_strength = half
        elif animation in {"land", "land_hard", "land_recovery"}:
            impact = 1.0 - _smoothstep(t) if animation == "land_recovery" else math.sin(math.pi * _clamp01(t / 0.72))
            pose.root_y = -9.0 * (1.0 - _smoothstep(t / 0.42))
            pose.crouch = (0.42 if animation == "land" else 0.88) * impact
            pose.lean = -5.5 * impact
            pose.near_hand = (8.0, 20.0)
            pose.far_hand = (-8.0, 17.0)
            pose.near_foot = (7.0, -1.0)
            pose.far_foot = (-7.0, -1.0)
            pose.prop = "none"
            pose.effect = "route_impact"
            pose.effect_strength = impact
        elif animation in {"roll", "ledge_roll"}:
            pose.crouch = 0.84
            pose.root_x = _lerp(-5.0, 8.0, t)
            pose.root_y = -1.8 * math.sin(math.pi * t)
            pose.rotation = -360.0 * t
            pose.near_hand = (2.0, 19.0)
            pose.far_hand = (-5.0, 18.0)
            pose.near_foot = (5.0, -3.0)
            pose.far_foot = (-5.0, -3.0)
            pose.prop = "none"
        elif animation in {"wall_slide", "wall_grab", "ledge_grab"}:
            pose.root_x = 7.0
            pose.root_y = -12.0 + (4.0 * t if animation == "wall_slide" else 0.0)
            pose.lean = 5.5
            pose.near_hand = (14.0, 1.0 if animation == "ledge_grab" else 10.0)
            pose.far_hand = (12.0, 7.0 if animation == "ledge_grab" else 14.0)
            pose.near_foot = (8.0, -8.0)
            pose.far_foot = (7.0, 0.0)
            pose.near_bend = 1.0
            pose.prop = "none"
        elif animation == "wall_jump":
            spring = _smoothstep(t)
            pose.root_x = 8.0 - 16.0 * spring
            pose.root_y = -5.0 - 7.0 * math.sin(math.pi * t)
            pose.lean = 8.0 - 20.0 * spring
            pose.near_hand = (12.0 - 19.0 * spring, 9.0)
            pose.far_hand = (10.0 - 15.0 * spring, 15.0)
            pose.near_foot = (8.0 - 13.0 * spring, -6.0)
            pose.far_foot = (6.0 - 11.0 * spring, -2.0)
            pose.prop = "none"
        elif animation in {"climb", "ledge_climb", "ledge_getup"}:
            climb = _smoothstep(t)
            alternate = math.sin(t * math.tau)
            pose.root_y = -9.0 * climb if animation != "climb" else -6.5 + 1.3 * wave
            pose.root_x = 5.0 * (1.0 - climb) if animation != "climb" else 6.0
            pose.crouch = 0.32 * (1.0 - climb) if animation != "climb" else 0.14
            pose.near_hand = (12.0, 4.0 + 5.0 * alternate)
            pose.far_hand = (10.0, 11.0 - 5.0 * alternate)
            pose.near_foot = (7.0, -6.0 - 4.0 * alternate)
            pose.far_foot = (5.0, -2.0 + 4.0 * alternate)
            pose.near_bend = 1.0
            pose.prop = "none"
        elif animation == "swim":
            pose.root_y = -13.0 + 1.1 * wave
            pose.lean = -14.0
            pose.rotation = -8.0 + 3.0 * wave
            pose.near_hand = (16.0 + 5.0 * wave, 12.0)
            pose.far_hand = (-9.0 - 5.0 * wave, 12.0)
            pose.near_foot = (9.0 - 3.5 * wave, -4.0)
            pose.far_foot = (-9.0 + 3.5 * wave, -2.0)
            pose.prop = "none"
            pose.effect = "water"
            pose.effect_strength = 0.72
        elif animation == "hit":
            recoil = math.sin(math.pi * t)
            pose.root_x = -5.5 * recoil
            pose.lean = 12.0 * recoil
            pose.near_hand = (-5.0, 8.0)
            pose.far_hand = (-11.0, 13.0)
            pose.near_foot = (5.0, -1.0)
            pose.far_foot = (-5.0, -1.0)
            pose.prop = "none"
            pose.hit_flash = recoil
            pose.effect = "hit"
            pose.effect_strength = recoil
        elif animation == "death":
            collapse = _smoothstep(t)
            pose.root_x = -4.5 * collapse
            pose.root_y = 5.0 * collapse
            pose.crouch = 0.46 * collapse
            pose.rotation = 88.0 * collapse
            pose.opacity = 1.0 - 0.18 * _smoothstep((t - 0.82) / 0.18)
            pose.near_hand = (-2.0, 19.0)
            pose.far_hand = (-9.0, 17.0)
            pose.prop = "none"
        elif animation in {"blink_out", "blink_in"}:
            amount = _smoothstep(t)
            if animation == "blink_out":
                pose.opacity = max(0.08, 1.0 - amount)
                pose.root_x = 7.0 * amount
                pose.lean = -12.0 * amount
            else:
                pose.opacity = max(0.08, amount)
                pose.root_x = 7.0 * (1.0 - amount)
                pose.lean = -12.0 * (1.0 - amount)
            pose.crouch = 0.24 * math.sin(math.pi * t)
            pose.prop = "none"
            pose.effect = "route_blink"
            pose.effect_strength = math.sin(math.pi * t)
        elif animation in {"slash", "attack_side", "ledge_getup_attack"}:
            thrust = _smoothstep((t - 0.10) / 0.68)
            pose.root_x = 5.0 * thrust
            pose.lean = -11.0 + 12.0 * thrust
            pose.crouch = 0.20 * math.sin(math.pi * t)
            pose.near_hand = (7.0 + 8.0 * thrust, 10.0 + 2.0 * thrust)
            pose.far_hand = (0.0 + 7.0 * thrust, 13.0 + 1.5 * thrust)
            pose.tool_angle = -12.0 + 6.0 * thrust
            pose.prop = "survey_staff"
            pose.effect = "staff_thrust"
            pose.effect_strength = math.sin(math.pi * t)
            if animation == "ledge_getup_attack":
                pose.root_y = -10.0 * _smoothstep(t / 0.45)
                pose.crouch += 0.42 * (1.0 - _smoothstep(t / 0.35))
        elif animation in {"attack_up", "air_up"}:
            swing = _smoothstep((t - 0.10) / 0.68)
            pose.root_y = -12.0 if animation == "air_up" else 0.0
            pose.near_hand = (5.0, 5.0)
            pose.far_hand = (-2.0, 10.0)
            pose.tool_angle = 38.0 - 150.0 * swing
            pose.prop = "survey_staff"
            pose.effect = "staff_up"
            pose.effect_strength = math.sin(math.pi * t)
        elif animation in {"attack_down", "air_down"}:
            strike = _smoothstep((t - 0.08) / 0.72)
            pose.root_y = -13.0 if animation == "air_down" else 0.0
            pose.crouch = 0.48 if animation == "attack_down" else 0.0
            pose.near_hand = (10.0, 14.0)
            pose.far_hand = (2.0, 13.0)
            pose.tool_angle = -58.0 + 105.0 * strike
            pose.prop = "route_pin"
            pose.effect = "pin_drop"
            pose.effect_strength = math.sin(math.pi * t)
        elif animation == "air_forward":
            thrust = _smoothstep((t - 0.08) / 0.72)
            pose.root_y = -13.0
            pose.lean = -10.0
            pose.near_hand = (13.0 + 6.0 * thrust, 10.0)
            pose.far_hand = (4.0 + 4.0 * thrust, 12.0)
            pose.near_foot = (7.0, -5.0)
            pose.far_foot = (-7.0, -3.0)
            pose.tool_angle = -8.0
            pose.prop = "survey_staff"
            pose.effect = "staff_thrust"
            pose.effect_strength = math.sin(math.pi * t)
        elif animation == "air_back":
            sweep = _smoothstep((t - 0.08) / 0.72)
            pose.root_y = -13.0
            pose.lean = 5.0
            pose.near_hand = (-7.0 - 5.0 * sweep, 9.0)
            pose.far_hand = (-11.0, 13.0)
            pose.near_foot = (5.0, -5.0)
            pose.far_foot = (-5.0, -3.0)
            pose.tool_angle = -35.0 - 145.0 * sweep
            pose.prop = "map_ribbon"
            pose.effect = "ribbon_back"
            pose.effect_strength = math.sin(math.pi * t)
        elif animation == "air_neutral":
            pose.root_y = -13.0
            pose.rotation = -14.0 * math.sin(math.pi * t)
            pose.near_hand = (10.0, 9.0)
            pose.far_hand = (-9.0, 10.0)
            pose.near_foot = (6.0, -5.0)
            pose.far_foot = (-6.0, -3.0)
            pose.tool_angle = -90.0 + 360.0 * t
            pose.prop = "compass_disc"
            pose.effect = "compass_spin"
            pose.effect_strength = math.sin(math.pi * t)
        elif animation == "block":
            brace = math.sin(math.pi * t)
            pose.crouch = 0.24 * brace
            pose.lean = -3.0
            pose.near_hand = (13.0, 9.0)
            pose.far_hand = (7.0, 14.0)
            pose.near_bend = 1.0
            pose.prop = "map_ward"
            pose.effect = "map_block"
            pose.effect_strength = brace
        elif animation in {"aim", "shoot"}:
            recoil = math.sin(math.pi * t) if animation == "shoot" else 0.0
            pose.lean = -5.0 + 6.0 * recoil
            pose.near_hand = (15.0 - 3.0 * recoil, 10.0)
            pose.far_hand = (8.0 - 2.0 * recoil, 13.0)
            pose.near_bend = 1.0
            pose.prop = "route_projector"
            pose.tool_angle = 0.0
            if animation == "shoot":
                pose.effect = "route_dart"
                pose.effect_strength = max(0.0, 1.0 - abs(t - 0.48) / 0.24)
        elif animation in {"charge", "cast"}:
            charge = _smoothstep(t) if animation == "charge" else math.sin(math.pi * t)
            pose.near_hand = (13.0, 7.0)
            pose.far_hand = (6.0, 12.0)
            pose.near_bend = 1.0
            pose.prop = "route_projector"
            pose.tool_angle = -10.0
            pose.effect = "triangulate" if animation == "charge" else "cipher_cast"
            pose.effect_strength = charge
        elif animation == "stomp":
            impact = math.sin(math.pi * t)
            pose.root_y = -11.0 * math.sin(math.pi * min(1.0, t * 1.3))
            pose.crouch = 0.62 * _smoothstep((t - 0.55) / 0.30)
            pose.near_hand = (8.0, 6.0)
            pose.far_hand = (-8.0, 7.0)
            pose.near_foot = (6.0, -1.0)
            pose.far_foot = (-4.0, -6.0)
            pose.prop = "none"
            pose.effect = "route_stamp"
            pose.effect_strength = impact
        elif animation == "talk":
            pose.view = AliceView.FRONT
            pose.body_bob = 0.22 * wave
            pose.talk_open = 0.12 + 0.88 * (0.5 + 0.5 * wave)
            pose.gesture = max(0.0, half)
            pose.head_tilt = 0.78 * wave
            pose.blink = frame == count - 1
        elif animation == "interact":
            pose.view = AliceView.THREE_QUARTER
            pose.body_bob = -0.32 * half
            pose.map_open = max(0.0, half)
            pose.gesture = max(0.0, half)
            pose.scan = wave
            pose.head_tilt = -1.2 * half
        elif animation in {"pickup", "throw"}:
            action = _smoothstep(t)
            pose.crouch = math.sin(math.pi * t) * 0.52 if animation == "pickup" else 0.18
            pose.near_hand = (10.0 + 5.0 * action, 23.0 - 18.0 * action)
            pose.far_hand = (2.0 + 4.0 * action, 20.0 - 13.0 * action)
            pose.prop = "map_bundle"
            pose.effect = "throw_route" if animation == "throw" else ""
            pose.effect_strength = action
        elif animation == "celebrate":
            pose.root_y = -5.5 * abs(math.sin(math.pi * t))
            pose.near_hand = (8.0, -5.0)
            pose.far_hand = (-8.0, -4.0)
            pose.prop = "open_map"
            pose.effect = "triangulate"
            pose.effect_strength = 0.45 + 0.30 * abs(wave)
        elif animation in {"sit", "sleep"}:
            pose.crouch = 1.0
            pose.root_y = 0.0 if animation == "sit" else -2.0
            pose.lean = -3.0 if animation == "sit" else 8.0
            pose.rotation = 0.0 if animation == "sit" else 7.0
            pose.near_hand = (5.0, 20.0)
            pose.far_hand = (-5.0, 19.0)
            pose.near_foot = (10.0, -1.0)
            pose.far_foot = (-2.0, -1.0)
            pose.prop = "none"
            if animation == "sleep":
                pose.effect = "sleep"
                pose.effect_strength = 0.65 + 0.35 * wave
        elif animation == "idle_front":
            pose.view = AliceView.FRONT
            pose.body_bob = 0.34 * wave
            pose.head_tilt = 0.52 * wave
            pose.scan = 0.20 * wave
            pose.blink = frame == count - 1
        elif animation == "idle_side":
            pose.view = AliceView.SIDE
            pose.body_bob = 0.34 * wave
            pose.head_tilt = 0.52 * wave
            pose.scan = 0.25 * wave
            pose.blink = frame == count - 1
            pose.prop = "folio"
        return pose

    @profile
    def render_animation_frame(
        self,
        spec: AliceSpec,
        animation: str,
        frame_index: int,
        frame_count: int,
        size: Tuple[int, int],
        *,
        background: Optional[Color],
        supersample: int,
        downsample: str,
    ) -> Image.Image:
        del downsample
        width, height = size
        ss = max(1, int(supersample))
        canvas = Image.new(
            "RGBA",
            (width * ss, height * ss),
            background or (0, 0, 0, 0),
        )
        actor = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        scale = (width / 128.0) * ss
        pose = self.pose_for_animation(animation, frame_index, frame_count)
        cx = (64.0 + pose.root_x) * scale
        feet_y = (117.0 + pose.body_bob + pose.root_y) * scale
        d = blending_draw(actor)
        if pose.prop == "map_glider":
            self._draw_map_glider(d, cx, feet_y - 70 * scale, scale)
        hand = draw_doll(actor, cx, feet_y, pose, scale, self._solve_two_bone_joint)
        d = blending_draw(actor)
        if pose.prop in {"folio", "map_ribbon", "map_bundle", "open_map"}:
            self._draw_map_folio(d, hand[0] + 3 * scale, hand[1], scale * .8,
                                 open_amount=max(pose.map_open, float(pose.prop == "open_map")))
        elif pose.prop in {"survey_staff", "route_pin"}:
            self._draw_survey_staff(d, hand, pose.tool_angle, scale, pin_tip=pose.prop == "route_pin")
        elif pose.prop == "route_projector":
            self._draw_route_projector(d, hand, pose.tool_angle, scale)
        elif pose.prop == "map_ward":
            self._draw_map_ward(d, hand, scale)
        elif pose.prop == "compass_disc":
            self._draw_compass_disc(d, hand, pose.tool_angle, scale)
        self._draw_action_effects(actor, cx, feet_y, pose, scale)

        if abs(pose.rotation) > 0.01:
            pivot = (round(cx), round(feet_y - 41.0 * scale))
            actor = actor.rotate(
                -pose.rotation,
                resample=Image.Resampling.BICUBIC,
                center=pivot,
                expand=False,
            )

        if pose.hit_flash > 0.0:
            alpha = actor.getchannel("A")
            strength = _clamp01(pose.hit_flash)
            tint = Image.new("RGBA", actor.size, (255, 228, 200, round(155 * strength)))
            tint.putalpha(alpha.point(lambda value: round(value * 0.60 * strength)))
            actor = Image.alpha_composite(actor, tint)

        if pose.opacity < 0.999:
            alpha = actor.getchannel("A")
            actor.putalpha(alpha.point(lambda value: round(value * _clamp01(pose.opacity))))

        canvas.alpha_composite(actor)
        if ss > 1:
            canvas = canvas.resize((width, height), Image.Resampling.LANCZOS)
        return canvas

    # ------------------------------------------------------------------
    # Shared accessories and face details

    def _solve_two_bone_joint(
        self,
        root: Point,
        target: Point,
        upper_len: float,
        lower_len: float,
        *,
        bend_sign: float,
    ) -> Tuple[Point, Point]:
        """Solve a two-segment limb while keeping its bend semantically stable.

        Side-view limbs should not flip their elbows or knees merely because a
        target crosses the body.  ``bend_sign=-1`` places the middle joint on
        the screen-left/back side of the root-to-target line, which is the
        natural elbow direction for Alice's right-facing profile.
        """
        dx = target[0] - root[0]
        dy = target[1] - root[1]
        distance = math.hypot(dx, dy)
        min_reach = abs(upper_len - lower_len) + 1e-4
        max_reach = max(min_reach + 1e-4, upper_len + lower_len - 1e-4)
        clamped_distance = max(min_reach, min(max_reach, distance))
        if distance > 1e-6 and clamped_distance != distance:
            ratio = clamped_distance / distance
            target = (root[0] + dx * ratio, root[1] + dy * ratio)
            dx = target[0] - root[0]
            dy = target[1] - root[1]
        base = math.atan2(dy, dx)
        cosine = (
            upper_len * upper_len
            + clamped_distance * clamped_distance
            - lower_len * lower_len
        ) / (2.0 * upper_len * clamped_distance)
        offset = math.acos(max(-1.0, min(1.0, cosine)))
        angle = base - bend_sign * offset
        joint = (
            root[0] + math.cos(angle) * upper_len,
            root[1] + math.sin(angle) * upper_len,
        )
        return joint, target

    def _draw_map_folio(
        self,
        d: ImageDraw.ImageDraw,
        cx: float,
        cy: float,
        s: float,
        *,
        angle_hint: float = 0.0,
        open_amount: float = 0.0,
    ) -> None:
        """Draw Alice's sealed route folio, optionally opening into a map."""
        pal = ALICE_PALETTE
        outline = pal["outline"]
        if open_amount <= 0.05:
            w, h = 11.0 * s, 15.0 * s
            skew = angle_hint * 2.0 * s
            pts = [
                (cx - w / 2 + skew, cy - h / 2),
                (cx + w / 2 + skew, cy - h / 2 + 1.2 * s),
                (cx + w / 2 - skew, cy + h / 2),
                (cx - w / 2 - skew, cy + h / 2 - 1.2 * s),
            ]
            _poly(d, pts, fill=pal["map"], outline=outline, width=round(1.0 * s))
            _line(
                d,
                [(cx - 4.0 * s, cy - 3.0 * s), (cx + 3.0 * s, cy + 2.0 * s)],
                fill=pal["map_shadow"],
                width=round(0.8 * s),
            )
            _ellipse(
                d,
                _bbox(cx + 1.5 * s, cy + 1.2 * s, 4.0 * s, 4.0 * s),
                fill=pal["seal"],
                outline=outline,
                width=round(0.7 * s),
            )
            return

        amount = min(1.0, open_amount)
        w = (14.0 + 23.0 * amount) * s
        h = (16.0 + 4.0 * amount) * s
        left = cx - w / 2
        right = cx + w / 2
        top = cy - h / 2
        bottom = cy + h / 2
        fold = cx + 1.0 * s
        _poly(
            d,
            [
                (left, top + 2.0 * s),
                (fold, top),
                (right, top + 2.0 * s),
                (right - 1.0 * s, bottom),
                (fold, bottom - 1.0 * s),
                (left + 1.0 * s, bottom),
            ],
            fill=pal["map"],
            outline=outline,
            width=round(1.0 * s),
        )
        _line(
            d,
            [(fold, top), (fold, bottom - 1.0 * s)],
            fill=pal["map_shadow"],
            width=round(0.8 * s),
        )
        # Topographic marks and a deliberately red private route.
        for offset in (-5.0, 1.0, 6.0):
            _line(
                d,
                [
                    (left + 4.0 * s, cy + offset * 0.55 * s),
                    (cx - 3.0 * s, cy + (offset - 2.0) * 0.55 * s),
                    (right - 4.0 * s, cy + (offset + 1.0) * 0.55 * s),
                ],
                fill=pal["map_ink"],
                width=round(0.7 * s),
            )
        _line(
            d,
            [
                (left + 5.0 * s, bottom - 4.0 * s),
                (cx - 4.0 * s, cy + 1.0 * s),
                (cx + 5.0 * s, cy - 4.0 * s),
                (right - 5.0 * s, top + 4.0 * s),
            ],
            fill=pal["route"],
            width=round(1.3 * s),
        )
        for x, y in (
            (left + 5.0 * s, bottom - 4.0 * s),
            (right - 5.0 * s, top + 4.0 * s),
        ):
            _ellipse(
                d,
                _bbox(x, y, 2.4 * s, 2.4 * s),
                fill=pal["route"],
                outline=outline,
                width=round(0.5 * s),
            )

    def _draw_survey_staff(
        self,
        d: ImageDraw.ImageDraw,
        hand: Point,
        angle_deg: float,
        s: float,
        *,
        pin_tip: bool = False,
    ) -> None:
        """Alice's collapsible survey staff: a precise thrusting tool, not a wrench."""
        pal = ALICE_PALETTE
        angle = math.radians(angle_deg)
        ux, uy = math.cos(angle), math.sin(angle)
        px, py = -uy, ux
        tail = (hand[0] - ux * 6.0 * s, hand[1] - uy * 6.0 * s)
        tip = (hand[0] + ux * 25.0 * s, hand[1] + uy * 25.0 * s)
        _line(d, [tail, tip], fill=pal["outline"], width=round(4.2 * s))
        _line(d, [tail, tip], fill=pal["metal"], width=round(2.3 * s))
        for distance in (-2.0, 8.0, 18.0):
            center = (hand[0] + ux * distance * s, hand[1] + uy * distance * s)
            _line(
                d,
                [
                    (center[0] - px * 2.7 * s, center[1] - py * 2.7 * s),
                    (center[0] + px * 2.7 * s, center[1] + py * 2.7 * s),
                ],
                fill=pal["amber"],
                width=round(1.3 * s),
            )
        if pin_tip:
            point = (tip[0] + ux * 4.5 * s, tip[1] + uy * 4.5 * s)
            _poly(
                d,
                [
                    point,
                    (tip[0] + px * 3.8 * s, tip[1] + py * 3.8 * s),
                    (tip[0] - px * 3.8 * s, tip[1] - py * 3.8 * s),
                ],
                fill=pal["route"],
                outline=pal["outline"],
                width=round(0.8 * s),
            )
        else:
            _ellipse(
                d,
                _bbox(tip[0], tip[1], 6.4 * s, 6.4 * s),
                fill=pal["amber"],
                outline=pal["outline"],
                width=round(0.8 * s),
            )
            _ellipse(d, _bbox(tip[0], tip[1], 2.2 * s, 2.2 * s), fill=pal["map_ink"])

    def _draw_route_projector(
        self,
        d: ImageDraw.ImageDraw,
        hand: Point,
        angle_deg: float,
        s: float,
    ) -> Point:
        pal = ALICE_PALETTE
        angle = math.radians(angle_deg)
        ux, uy = math.cos(angle), math.sin(angle)
        px, py = -uy, ux
        center = (hand[0] + ux * 5.0 * s, hand[1] + uy * 5.0 * s)
        ring = (center[0] + ux * 4.0 * s, center[1] + uy * 4.0 * s)
        _ellipse(
            d,
            _bbox(center[0], center[1], 10.0 * s, 10.0 * s),
            fill=pal["metal_dark"],
            outline=pal["outline"],
            width=round(0.9 * s),
        )
        _ellipse(
            d,
            _bbox(ring[0], ring[1], 6.0 * s, 6.0 * s),
            fill=pal["amber_light"],
            outline=pal["outline"],
            width=round(0.7 * s),
        )
        muzzle = (center[0] + ux * 12.0 * s, center[1] + uy * 12.0 * s)
        _line(d, [ring, muzzle], fill=pal["map_ink"], width=round(1.5 * s))
        _line(
            d,
            [
                (center[0] - px * 3.5 * s, center[1] - py * 3.5 * s),
                (center[0] + px * 3.5 * s, center[1] + py * 3.5 * s),
            ],
            fill=pal["amber"],
            width=round(1.0 * s),
        )
        return muzzle

    def _draw_map_ward(self, d: ImageDraw.ImageDraw, hand: Point, s: float) -> None:
        pal = ALICE_PALETTE
        outline = pal["outline"]
        fold = [
            (hand[0] - 1.0 * s, hand[1] - 13.0 * s),
            (hand[0] + 13.0 * s, hand[1] - 10.0 * s),
            (hand[0] + 14.0 * s, hand[1] + 10.0 * s),
            (hand[0] + 1.0 * s, hand[1] + 13.0 * s),
        ]
        _poly(d, fold, fill=pal["map"], outline=outline, width=round(1.0 * s))
        _line(
            d,
            [(hand[0] + 6.0 * s, hand[1] - 11.5 * s), (hand[0] + 7.0 * s, hand[1] + 11.5 * s)],
            fill=pal["map_shadow"],
            width=round(1.0 * s),
        )
        _line(
            d,
            [
                (hand[0] + 1.0 * s, hand[1] + 5.0 * s),
                (hand[0] + 5.0 * s, hand[1] - 1.0 * s),
                (hand[0] + 11.5 * s, hand[1] + 3.5 * s),
            ],
            fill=pal["route"],
            width=round(1.3 * s),
        )

    def _draw_compass_disc(
        self, d: ImageDraw.ImageDraw, hand: Point, angle_deg: float, s: float
    ) -> None:
        pal = ALICE_PALETTE
        angle = math.radians(angle_deg)
        center = (
            hand[0] + math.cos(angle) * 8.0 * s,
            hand[1] + math.sin(angle) * 8.0 * s,
        )
        _ellipse(
            d,
            _bbox(center[0], center[1], 13.0 * s, 13.0 * s),
            fill=pal["metal_dark"],
            outline=pal["outline"],
            width=round(1.0 * s),
        )
        _ellipse(
            d,
            _bbox(center[0], center[1], 8.0 * s, 8.0 * s),
            fill=pal["amber_light"],
            outline=pal["outline"],
            width=round(0.6 * s),
        )
        r = 4.0 * s
        _line(
            d,
            [
                (center[0] - math.cos(angle) * r, center[1] - math.sin(angle) * r),
                (center[0] + math.cos(angle) * r, center[1] + math.sin(angle) * r),
            ],
            fill=pal["route"],
            width=round(1.2 * s),
        )

    def _draw_map_glider(
        self, d: ImageDraw.ImageDraw, cx: float, shoulder_y: float, s: float
    ) -> None:
        """An unfolded route map used as a compact aerial cape/glider."""
        pal = ALICE_PALETTE
        outline = pal["outline"]
        points = [
            (cx - 11.0 * s, shoulder_y + 2.0 * s),
            (cx - 35.0 * s, shoulder_y + 8.0 * s),
            (cx - 30.0 * s, shoulder_y + 24.0 * s),
            (cx - 10.0 * s, shoulder_y + 18.0 * s),
            (cx + 5.0 * s, shoulder_y + 7.0 * s),
        ]
        _poly(d, points, fill=pal["map"], outline=outline, width=round(1.0 * s))
        _line(d, [points[0], points[2], points[4]], fill=pal["map_shadow"], width=round(1.0 * s))
        _line(
            d,
            [
                (cx - 30.0 * s, shoulder_y + 15.0 * s),
                (cx - 20.0 * s, shoulder_y + 11.0 * s),
                (cx - 11.0 * s, shoulder_y + 17.0 * s),
                (cx - 1.0 * s, shoulder_y + 10.0 * s),
            ],
            fill=pal["route"],
            width=round(1.2 * s),
        )

    def _draw_action_effects(
        self,
        image: Image.Image,
        cx: float,
        feet_y: float,
        pose: AlicePose,
        s: float,
    ) -> None:
        """Cartographic/cipher action effects. Never paints a drop shadow."""
        if not pose.effect or pose.effect_strength <= 0.001:
            return
        d = blending_draw(image)
        pal = ALICE_PALETTE
        strength = _clamp01(pose.effect_strength)
        body_y = feet_y - 45.0 * s
        teal = (*pal["jacket_light"][:3], round(220 * strength))
        amber = (*pal["amber_light"][:3], round(220 * strength))
        route = (*pal["route"][:3], round(225 * strength))

        if pose.effect == "staff_thrust":
            origin = (cx + 13.0 * s, body_y + 4.0 * s)
            _line(d, [origin, (cx + (36.0 + 14.0 * strength) * s, body_y + 1.0 * s)], fill=amber, width=round(2.0 * s))
            for offset in (-5.0, 5.0):
                _line(d, [(cx + 20.0 * s, body_y + offset * s), (cx + 35.0 * s, body_y + offset * 0.4 * s)], fill=teal, width=round(1.0 * s))
        elif pose.effect == "staff_up":
            box = (cx - 20 * s, body_y - 45 * s, cx + 31 * s, body_y + 9 * s)
            d.arc(tuple(round(v) for v in box), 188, 336, fill=amber, width=max(1, round(2.2 * s)))
            inner = (box[0] + 5*s, box[1] + 5*s, box[2] - 5*s, box[3] - 5*s)
            d.arc(tuple(round(v) for v in inner), 188, 336, fill=teal, width=max(1, round(1.1 * s)))
        elif pose.effect == "pin_drop":
            x = cx + 22.0 * s
            _line(d, [(x, body_y - 8.0 * s), (x, feet_y + 2.0 * s)], fill=route, width=round(1.8 * s))
            _poly(d, [(x, feet_y - 3*s), (x - 5*s, feet_y - 10*s), (x + 5*s, feet_y - 10*s)], fill=route, outline=amber, width=round(0.8*s))
        elif pose.effect == "ribbon_back":
            points = [
                (cx - 5.0*s, body_y - 8.0*s),
                (cx - 22.0*s, body_y - 20.0*s),
                (cx - 40.0*s, body_y - 4.0*s),
                (cx - 29.0*s, body_y + 18.0*s),
            ]
            _line(d, points, fill=route, width=round(2.0*s))
            for point in points[1:]:
                _ellipse(d, _bbox(point[0], point[1], 3.0*s, 3.0*s), fill=amber)
        elif pose.effect == "compass_spin":
            for radius, color in ((31.0, amber), (23.0, teal)):
                box = _bbox(cx, body_y, radius * 2*s, radius * 2*s)
                d.arc(tuple(round(v) for v in box), 0, round(330*strength + 20), fill=color, width=max(1, round(1.5*s)))
            for angle in (0, 120, 240):
                rad = math.radians(angle + 160.0 * strength)
                p = (cx + math.cos(rad)*28*s, body_y + math.sin(rad)*28*s)
                _ellipse(d, _bbox(p[0], p[1], 4*s, 4*s), fill=route)
        elif pose.effect == "route_speed":
            for i, yoff in enumerate((-13.0, -2.0, 10.0, 20.0)):
                length = (13.0 + 5.0 * i) * strength
                x0 = cx - (15.0 + length) * s
                x1 = cx - 15.0 * s
                _line(d, [(x0, body_y + yoff*s), (x1, body_y + yoff*s)], fill=teal if i % 2 else amber, width=round((1.0 + 0.2*i)*s))
                _ellipse(d, _bbox(x0, body_y + yoff*s, 2.4*s, 2.4*s), fill=route)
        elif pose.effect == "route_blink":
            direction = -1.0 if pose.opacity < 0.55 else 1.0
            for i in range(6):
                y = body_y + (-25.0 + i * 10.0) * s
                x0 = cx + direction * (8.0 + i * 1.5) * s
                x1 = cx + direction * (25.0 + i * 3.0) * s
                _line(d, [(x0, y), (x1, y)], fill=teal if i % 2 else amber, width=round(1.3*s))
                _ellipse(d, _bbox(x1, y, 2.2*s, 2.2*s), fill=route)
        elif pose.effect == "route_dart":
            origin = (cx + 30.0 * s, body_y + 1.0 * s)
            tip = (origin[0] + 18.0 * strength * s, origin[1])
            _line(d, [origin, tip], fill=teal, width=round(1.8*s))
            _poly(d, [tip, (tip[0]-6*s, tip[1]-4*s), (tip[0]-6*s, tip[1]+4*s)], fill=route, outline=amber, width=round(0.7*s))
        elif pose.effect in {"triangulate", "cipher_cast"}:
            center = (cx + 29.0 * s, body_y - (5.0 if pose.effect == "cipher_cast" else 0.0) * s)
            radius = (5.0 + 10.0 * strength) * s
            pts = []
            for i in range(3):
                ang = math.radians(-90 + i*120 + 70*strength)
                pts.append((center[0] + math.cos(ang)*radius, center[1] + math.sin(ang)*radius))
            _line(d, [*pts, pts[0]], fill=amber, width=round(1.5*s))
            _ellipse(d, _bbox(center[0], center[1], radius*0.55, radius*0.55), fill=(*pal["jacket_light"][:3], round(70*strength)), outline=teal, width=round(1.0*s))
            if pose.effect == "cipher_cast":
                for i, p in enumerate(pts):
                    _line(d, [center, p], fill=route if i == 1 else teal, width=round(0.8*s))
        elif pose.effect == "map_block":
            box = (cx + 4*s, body_y - 29*s, cx + 41*s, body_y + 29*s)
            d.arc(tuple(round(v) for v in box), 250, 110, fill=teal, width=max(1, round(2.0*s)))
            for yoff in (-12.0, 0.0, 12.0):
                _line(d, [(cx + 18*s, body_y + yoff*s), (cx + 32*s, body_y + yoff*0.7*s)], fill=amber, width=round(0.9*s))
        elif pose.effect in {"route_impact", "route_stamp"}:
            y = feet_y - 1.0 * s
            for dx in (-15.0, -8.0, 0.0, 8.0, 15.0):
                top = y - (5.0 + abs(dx)*0.18) * s * strength
                _line(d, [(cx + dx*s, y), (cx + dx*1.25*s, top)], fill=amber if dx else route, width=round(1.2*s))
            if pose.effect == "route_stamp":
                d.arc(tuple(round(v) for v in _bbox(cx, y, 30*s*strength, 9*s)), 180, 360, fill=teal, width=max(1, round(1.0*s)))
        elif pose.effect == "route_glide":
            for i in range(3):
                y = body_y + (-13.0 + i*11.0)*s
                _line(d, [(cx - (33.0 + i*5.0)*s, y), (cx - 14.0*s, y + 2.0*s)], fill=teal if i != 1 else amber, width=round(1.0*s))
        elif pose.effect == "water":
            for i in range(3):
                y = feet_y - (5.0 + i * 5.0) * s
                d.arc((round(cx - 31*s), round(y-3*s), round(cx-7*s), round(y+3*s)), 180, 350, fill=teal, width=max(1, round(1.0*s)))
        elif pose.effect == "hit":
            center = (cx + 9.0*s, body_y - 2.0*s)
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                _line(d, [center, (center[0] + math.cos(rad)*9*s*strength, center[1] + math.sin(rad)*9*s*strength)], fill=route if angle % 120 else amber, width=round(1.1*s))
        elif pose.effect == "throw_route":
            for i in range(4):
                x = cx + (18.0 + i*6.0)*s*strength
                y = body_y + (-5.0 + i*2.0)*s
                _ellipse(d, _bbox(x, y, 2.5*s, 2.5*s), fill=route if i % 2 else amber)
        elif pose.effect == "sleep":
            for i in range(3):
                x = cx + (18.0 + i*6.0)*s
                y = body_y - (18.0 + i*7.0)*s
                _line(d, [(x, y), (x+4*s, y), (x, y-5*s), (x+4*s, y-5*s)], fill=teal, width=round(1.0*s))
