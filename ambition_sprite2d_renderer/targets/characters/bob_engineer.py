"""Procedural sprite target for Bob, the cryptography crew's hardware engineer.

Bob is not a generic workshop NPC with a few tiny tools pasted onto him.  He is
Alice's peer: a capable field engineer who can cut a key, rebuild a lock, probe a
cipher machine, and keep moving when the job leaves the lab.  The redesign uses
one coherent silhouette in every view:

* broad but human shoulders, rolled work sleeves, and a fitted utility vest;
* a compact cross-body hardware satchel and readable key/tool hardware;
* safety glasses pushed onto his forehead rather than a costume hard-hat;
* a short tousled haircut, sideburns, and a close beard that stay coherent in
  front, three-quarter, and profile views;
* planted work boots and an authored eight-pose PCA-style walk cycle;
* a portable lock/cipher analyzer for the interaction animation.

Bob now carries the same broad player-grade animation vocabulary as the main
robot: walk/run, aerial and wall traversal, dodge/landing states, blink travel,
directional wrench attacks, blocking, aiming, shooting, and charge/cast poses,
while retaining his richer conversation and analyzer interactions.  The
renderer never paints a ground ellipse or drop shadow; scene lighting and
contact belong to the game renderer, not the sprite texture.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.animation_vocab import (
    DEFAULT_ADVANCED_TIMINGS,
    DEFAULT_DIRECTIONAL_ATTACK_TIMINGS,
    DEFAULT_EXTENDED_TIMINGS,
    DEFAULT_TRAVERSAL_POLISH_TIMINGS,
)
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


BOB_PALETTE: Dict[str, Color] = {
    "outline": rgba("#11100F"),
    "skin": rgba("#B98A68"),
    "skin_light": rgba("#D3A583"),
    "skin_shadow": rgba("#855C43"),
    "hair": rgba("#2B201B"),
    "hair_mid": rgba("#49352B"),
    "hair_light": rgba("#765445"),
    "beard": rgba("#4A3329"),
    "beard_dark": rgba("#2A1D19"),
    "shirt": rgba("#355A79"),
    "shirt_dark": rgba("#213A51"),
    "shirt_light": rgba("#5A819E"),
    "vest": rgba("#9E7245"),
    "vest_dark": rgba("#654529"),
    "vest_light": rgba("#C49662"),
    "reinforce": rgba("#4C3929"),
    "hi_vis": rgba("#E6BC47"),
    "hi_vis_dark": rgba("#92701F"),
    "pants": rgba("#30343A"),
    "pants_dark": rgba("#1D2228"),
    "pants_light": rgba("#4D535B"),
    "boot": rgba("#241C18"),
    "boot_light": rgba("#5B4032"),
    "boot_sole": rgba("#0D0B0A"),
    "leather": rgba("#704427"),
    "leather_light": rgba("#A86A3A"),
    "leather_dark": rgba("#3B2518"),
    "steel": rgba("#BFC4C8"),
    "steel_dark": rgba("#596169"),
    "brass": rgba("#D89A3C"),
    "brass_light": rgba("#F0C66B"),
    "brass_dark": rgba("#825315"),
    "glass": rgba("#A8D7D9"),
    "glass_dark": rgba("#39747B"),
    "device": rgba("#D9D3BD"),
    "device_dark": rgba("#77715F"),
    "device_screen": rgba("#4AB0A0"),
    "indicator": rgba("#D45A45"),
    "white": rgba("#F8F1E4"),
    "eye": rgba("#2A211D"),
}


class BobView(str, Enum):
    THREE_QUARTER = "three_quarter"
    FRONT = "front"
    SIDE = "side"


# Gameplay actions default to the right-facing profile used by the player
# robot.  Bob keeps front/three-quarter rows for conversation and portrait
# acting, but every traversal/combat row shares one side-view body instead of
# becoming a disconnected alternate costume.
ANIMATION_VIEWS: Dict[str, BobView] = {
    "idle": BobView.THREE_QUARTER,
    "talk": BobView.FRONT,
    "interact": BobView.FRONT,
    "idle_front": BobView.FRONT,
    "idle_side": BobView.SIDE,
}


@dataclass(frozen=True)
class BobSpec:
    target: str
    seed: int
    archetype: str
    name: str
    role: str
    palette_name: str
    head_w: float = 25.0
    head_h: float = 27.5
    shoulder_w: float = 32.0
    torso_h: float = 29.0
    waist_w: float = 23.0
    hip_w: float = 25.0
    thigh_h: float = 18.0
    shin_h: float = 18.0
    boot_h: float = 9.0
    arm_upper: float = 13.5
    arm_lower: float = 13.0


@dataclass
class BobPose:
    view: BobView
    body_bob: float = 0.0
    head_tilt: float = 0.0
    blink: bool = False
    talk_open: float = 0.0
    gesture: float = 0.0
    interact: float = 0.0
    scan: float = 0.0
    walk_index: int = -1
    walk_body_y: float = 0.0
    step: float = 0.0

    # Shared player-grade action controls. Coordinates are authored in the
    # 128px source space and interpreted relative to Bob's side-view body.
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
    far_bend: float = 1.0
    near_bend: float = -1.0
    prop: str = "keys"
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
        tuple(round(v) for v in box),
        fill=fill,
        outline=outline,
        width=max(1, width),
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


class BobEngineerGenerator(CharacterGenerator):
    name = "bob_engineer"
    target = "bob_engineer"
    applies_job_name = True

    # Bob now authors the same broad movement/combat vocabulary as the player
    # robot.  The review config chooses the runtime-relevant subset; keeping the
    # complete table here makes Bob a genuine player-candidate rather than an
    # NPC sheet with a walk row bolted on.
    ANIMATIONS: Dict[str, Dict[str, int]] = {
        "idle": {"frames": 8, "duration_ms": 120},
        "walk": {"frames": 8, "duration_ms": 95},
        "run": {"frames": 8, "duration_ms": 75},
        "jump": {"frames": 6, "duration_ms": 95},
        "fall": {"frames": 6, "duration_ms": 95},
        "slash": {"frames": 8, "duration_ms": 75},
        "hit": {"frames": 5, "duration_ms": 90},
        "death": {"frames": 8, "duration_ms": 110},
        "blink_out": {"frames": 6, "duration_ms": 62},
        "blink_in": {"frames": 6, "duration_ms": 62},
        "dash": {"frames": 6, "duration_ms": 65},
        **DEFAULT_EXTENDED_TIMINGS,
        **DEFAULT_ADVANCED_TIMINGS,
        **DEFAULT_TRAVERSAL_POLISH_TIMINGS,
        **DEFAULT_DIRECTIONAL_ATTACK_TIMINGS,
        "idle_front": {"frames": 8, "duration_ms": 120},
        "idle_side": {"frames": 8, "duration_ms": 120},
    }

    def build_spec(self, job: CharacterJob) -> BobSpec:
        if job.archetype != "bob":
            raise KeyError(
                f"bob_engineer ships only the 'bob' archetype; got {job.archetype!r}"
            )
        return BobSpec(
            target=self.name,
            seed=job.seed,
            archetype=job.archetype,
            name="Bob",
            role="npc",
            palette_name="bob_field_hardware_engineer",
        )

    def canonical_pose(self) -> Tuple[str, int]:
        return ("idle", 1)

    def body_inset(self) -> Dict[str, float]:
        # The satchel, carried keys, and analyzer are silhouette extensions.
        return {"left": 0.07, "right": 0.07, "top": 0.02, "bottom": 0.0}

    def attack_hitboxes(self, size: Tuple[int, int]) -> Dict[str, Dict[str, Any]]:
        """Right-facing gameplay volumes for Bob's wrench attacks.

        The runtime mirrors these when Bob faces left.  Cosmetic wrench arcs
        extend beyond the body, so the hitboxes are authored explicitly rather
        than inferred from alpha.
        """
        w, h = size
        cx = w * 0.5

        def hitbox(x: float, y: float, width: float, height: float) -> Dict[str, Any]:
            return {
                "bbox": (round(x), round(y), round(width), round(height)),
                "active_frames": [2, 3, 4, 5],
            }

        forward = hitbox(cx + w * 0.04, h * 0.25, w * 0.53, h * 0.55)
        upward = hitbox(cx - w * 0.18, -h * 0.02, w * 0.48, h * 0.58)
        downward = hitbox(cx - w * 0.02, h * 0.48, w * 0.43, h * 0.52)
        backward = hitbox(cx - w * 0.48, h * 0.24, w * 0.48, h * 0.56)
        neutral = hitbox(cx - w * 0.38, h * 0.18, w * 0.78, h * 0.66)
        return {
            "slash": dict(forward),
            "attack_side": dict(forward),
            "ledge_getup_attack": dict(forward),
            "air_forward": dict(forward),
            "attack_up": dict(upward),
            "air_up": dict(upward),
            "attack_down": dict(downward),
            "air_down": dict(downward),
            "air_back": dict(backward),
            "air_neutral": dict(neutral),
        }

    def render_frame(
        self,
        spec: BobSpec,
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

    def pose_for_animation(self, animation: str, frame: int, count: int) -> BobPose:
        t = 0.0 if count <= 1 else frame / float(count - 1)
        wave = math.sin(t * math.tau)
        half = math.sin(t * math.pi)
        pose = BobPose(view=ANIMATION_VIEWS.get(animation, BobView.SIDE))

        if animation == "idle":
            pose.body_bob = 0.4 * wave
            pose.head_tilt = 0.7 * wave
            pose.scan = 0.18 * wave
            pose.blink = frame == count - 1
        elif animation in {"walk", "run", "crouch_walk"}:
            index = frame % 8
            pose.walk_index = index
            pose.step = (-1.0, -0.62, -0.18, 0.52, 1.0, 0.58, 0.08, -0.55)[index]
            pose.walk_body_y = (0.0, 1.15, 0.35, -0.65, 0.0, 1.15, 0.35, -0.65)[index]
            pose.head_tilt = (0.3, 0.08, -0.12, -0.28, -0.3, -0.08, 0.12, 0.28)[index]
            pose.prop = "none"
            if animation == "run":
                pose.gait_scale = 1.38
                pose.arm_swing = 1.38
                pose.lean = -5.0
                pose.walk_body_y *= 1.35
            elif animation == "crouch_walk":
                pose.gait_scale = 0.56
                pose.arm_swing = 0.42
                pose.crouch = 0.72
                pose.lean = -2.0
        elif animation == "jump":
            launch = _smoothstep((t - 0.10) / 0.42)
            preload = 1.0 - _smoothstep(t / 0.24)
            pose.root_y = 4.5 * preload - 11.0 * launch
            pose.lean = -4.0 - 3.0 * launch
            pose.crouch = 0.55 * preload
            pose.near_hand = (-2.0, 8.0)
            pose.far_hand = (-9.0, 13.0)
            pose.near_foot = (4.0, -5.0 - 4.0 * launch)
            pose.far_foot = (-4.0, -2.0 - 6.0 * launch)
            pose.prop = "none"
        elif animation == "fall":
            pose.root_y = -9.0 + 9.0 * t
            pose.lean = 3.0 + 3.0 * t
            pose.near_hand = (10.0, 13.0)
            pose.far_hand = (-8.0, 11.0)
            pose.near_foot = (5.0, -5.0)
            pose.far_foot = (-5.0, -3.0)
            pose.prop = "none"
        elif animation in {"hover", "float_glide"}:
            pose.root_y = -8.0 + 1.2 * wave
            pose.lean = -9.0 if animation == "float_glide" else -2.0
            pose.near_hand = (12.0, 12.0 if animation == "float_glide" else 18.0)
            pose.far_hand = (-8.0, 8.0)
            pose.near_foot = (7.0, -5.0 + wave)
            pose.far_foot = (-6.0, -3.0 - wave)
            pose.prop = "none"
            pose.effect = "hover"
            pose.effect_strength = 0.7 + 0.3 * abs(wave)
        elif animation in {"dash", "dash_startup"}:
            charge = _smoothstep(t)
            pose.crouch = 0.35 + (0.35 * charge if animation == "dash_startup" else 0.0)
            pose.lean = -8.0 - 8.0 * charge
            pose.root_x = 4.0 * charge if animation == "dash" else -2.5 * charge
            pose.near_hand = (-8.0, 18.0)
            pose.far_hand = (-12.0, 15.0)
            pose.near_foot = (7.0, 0.0)
            pose.far_foot = (-8.0, -1.0)
            pose.prop = "none"
            pose.effect = "speed"
            pose.effect_strength = charge
        elif animation in {"crouch", "slide"}:
            pose.crouch = 0.72 if animation == "crouch" else 0.9
            pose.lean = -2.0 if animation == "crouch" else -12.0
            pose.root_x = 4.0 * t if animation == "slide" else 0.0
            pose.near_hand = (7.0, 20.0)
            pose.far_hand = (-7.0, 18.0)
            pose.near_foot = (9.0, 0.0)
            pose.far_foot = (-7.0, 0.0)
            pose.prop = "none"
            if animation == "slide":
                pose.effect = "speed"
                pose.effect_strength = half
        elif animation in {"land", "land_hard", "land_recovery"}:
            if animation == "land_recovery":
                impact = 1.0 - _smoothstep(t)
            else:
                impact = math.sin(math.pi * _clamp01(t / 0.72))
            pose.root_y = -8.0 * (1.0 - _smoothstep(t / 0.42))
            pose.crouch = (0.45 if animation == "land" else 0.92) * impact
            pose.lean = -5.0 * impact
            pose.near_hand = (8.0, 21.0)
            pose.far_hand = (-8.0, 18.0)
            pose.near_foot = (7.0, 0.0)
            pose.far_foot = (-6.0, 0.0)
            pose.prop = "none"
            pose.effect = "impact"
            pose.effect_strength = impact
        elif animation in {"roll", "ledge_roll"}:
            pose.crouch = 0.82
            pose.root_x = _lerp(-5.0, 7.0, t)
            pose.root_y = -1.5 * math.sin(math.pi * t)
            pose.rotation = -360.0 * t
            pose.near_hand = (2.0, 20.0)
            pose.far_hand = (-4.0, 19.0)
            pose.near_foot = (5.0, -2.0)
            pose.far_foot = (-5.0, -2.0)
            pose.prop = "none"
        elif animation in {"wall_slide", "wall_grab", "ledge_grab"}:
            pose.root_x = 7.0
            pose.root_y = -11.0 + (4.0 * t if animation == "wall_slide" else 0.0)
            pose.lean = 5.0
            pose.near_hand = (14.0, 2.0 if animation == "ledge_grab" else 11.0)
            pose.far_hand = (12.0, 8.0 if animation == "ledge_grab" else 15.0)
            pose.near_foot = (8.0, -7.0)
            pose.far_foot = (7.0, 1.0)
            pose.near_bend = 1.0
            pose.prop = "none"
        elif animation == "wall_jump":
            spring = _smoothstep(t)
            pose.root_x = 8.0 - 15.0 * spring
            pose.root_y = -5.0 - 6.0 * math.sin(math.pi * t)
            pose.lean = 8.0 - 18.0 * spring
            pose.near_hand = (12.0 - 18.0 * spring, 10.0)
            pose.far_hand = (10.0 - 14.0 * spring, 16.0)
            pose.near_foot = (8.0 - 12.0 * spring, -5.0)
            pose.far_foot = (6.0 - 10.0 * spring, -1.0)
            pose.prop = "none"
        elif animation in {"climb", "ledge_climb", "ledge_getup"}:
            climb = _smoothstep(t)
            alternate = math.sin(t * math.tau)
            pose.root_y = -8.0 * climb if animation != "climb" else -6.0 + 1.5 * wave
            pose.root_x = 5.0 * (1.0 - climb) if animation != "climb" else 6.0
            pose.crouch = 0.35 * (1.0 - climb) if animation != "climb" else 0.15
            pose.near_hand = (12.0, 5.0 + 5.0 * alternate)
            pose.far_hand = (10.0, 12.0 - 5.0 * alternate)
            pose.near_foot = (7.0, -5.0 - 4.0 * alternate)
            pose.far_foot = (5.0, -1.0 + 4.0 * alternate)
            pose.near_bend = 1.0
            pose.prop = "none"
        elif animation == "swim":
            pose.root_y = -12.0 + 1.2 * wave
            pose.lean = -13.0
            pose.rotation = -8.0 + 3.0 * wave
            pose.near_hand = (15.0 + 4.0 * wave, 13.0)
            pose.far_hand = (-8.0 - 4.0 * wave, 13.0)
            pose.near_foot = (8.0 - 3.0 * wave, -3.0)
            pose.far_foot = (-8.0 + 3.0 * wave, -1.0)
            pose.prop = "none"
            pose.effect = "water"
            pose.effect_strength = 0.7
        elif animation == "hit":
            recoil = math.sin(math.pi * t)
            pose.root_x = -5.0 * recoil
            pose.lean = 11.0 * recoil
            pose.near_hand = (-5.0, 9.0)
            pose.far_hand = (-10.0, 14.0)
            pose.near_foot = (5.0, 0.0)
            pose.far_foot = (-5.0, 0.0)
            pose.prop = "none"
            pose.hit_flash = recoil
            pose.effect = "hit"
            pose.effect_strength = recoil
        elif animation == "death":
            collapse = _smoothstep(t)
            pose.root_x = -4.0 * collapse
            pose.root_y = 5.0 * collapse
            pose.crouch = 0.45 * collapse
            pose.rotation = 88.0 * collapse
            pose.opacity = 1.0 - 0.18 * _smoothstep((t - 0.82) / 0.18)
            pose.near_hand = (-2.0, 20.0)
            pose.far_hand = (-8.0, 18.0)
            pose.prop = "none"
        elif animation in {"blink_out", "blink_in"}:
            amount = _smoothstep(t)
            if animation == "blink_out":
                pose.opacity = max(0.08, 1.0 - amount)
                pose.root_x = 6.0 * amount
                pose.lean = -10.0 * amount
            else:
                pose.opacity = max(0.08, amount)
                pose.root_x = 6.0 * (1.0 - amount)
                pose.lean = -10.0 * (1.0 - amount)
            pose.crouch = 0.25 * math.sin(math.pi * t)
            pose.prop = "none"
            pose.effect = animation
            pose.effect_strength = math.sin(math.pi * t)
        elif animation in {"slash", "attack_side", "ledge_getup_attack"}:
            swing = _smoothstep((t - 0.12) / 0.68)
            pose.root_x = 4.0 * swing
            pose.lean = -8.0 + 14.0 * swing
            pose.crouch = 0.22 * math.sin(math.pi * t)
            pose.near_hand = (8.0 + 7.0 * swing, 8.0 + 9.0 * swing)
            pose.far_hand = (1.0 + 6.0 * swing, 12.0 + 6.0 * swing)
            pose.tool_angle = -118.0 + 190.0 * swing
            pose.prop = "wrench"
            pose.effect = "slash_side"
            pose.effect_strength = math.sin(math.pi * t)
            if animation == "ledge_getup_attack":
                pose.root_y = -10.0 * _smoothstep(t / 0.45)
                pose.crouch += 0.45 * (1.0 - _smoothstep(t / 0.35))
        elif animation in {"attack_up", "air_up"}:
            swing = _smoothstep((t - 0.12) / 0.66)
            pose.root_y = -11.0 if animation == "air_up" else 0.0
            pose.near_hand = (5.0, 5.0)
            pose.far_hand = (-2.0, 10.0)
            pose.tool_angle = 30.0 - 145.0 * swing
            pose.prop = "wrench"
            pose.effect = "slash_up"
            pose.effect_strength = math.sin(math.pi * t)
        elif animation in {"attack_down", "air_down"}:
            swing = _smoothstep((t - 0.10) / 0.70)
            pose.root_y = -12.0 if animation == "air_down" else 0.0
            pose.crouch = 0.5 if animation == "attack_down" else 0.0
            pose.near_hand = (9.0, 15.0)
            pose.far_hand = (1.0, 14.0)
            pose.tool_angle = -35.0 + 118.0 * swing
            pose.prop = "wrench"
            pose.effect = "slash_down"
            pose.effect_strength = math.sin(math.pi * t)
        elif animation == "air_forward":
            swing = _smoothstep((t - 0.10) / 0.72)
            pose.root_y = -12.0
            pose.lean = -7.0
            pose.near_hand = (12.0 + 5.0 * swing, 11.0)
            pose.far_hand = (3.0, 13.0)
            pose.near_foot = (6.0, -4.0)
            pose.far_foot = (-6.0, -2.0)
            pose.tool_angle = -85.0 + 155.0 * swing
            pose.prop = "wrench"
            pose.effect = "slash_side"
            pose.effect_strength = math.sin(math.pi * t)
        elif animation == "air_back":
            swing = _smoothstep((t - 0.10) / 0.72)
            pose.root_y = -12.0
            pose.lean = 5.0
            pose.near_hand = (-7.0 - 5.0 * swing, 10.0)
            pose.far_hand = (-10.0, 14.0)
            pose.near_foot = (5.0, -4.0)
            pose.far_foot = (-5.0, -2.0)
            pose.tool_angle = -30.0 - 150.0 * swing
            pose.prop = "wrench"
            pose.effect = "slash_back"
            pose.effect_strength = math.sin(math.pi * t)
        elif animation == "air_neutral":
            pose.root_y = -12.0
            pose.rotation = -18.0 * math.sin(math.pi * t)
            pose.near_hand = (10.0, 10.0)
            pose.far_hand = (-9.0, 11.0)
            pose.near_foot = (6.0, -4.0)
            pose.far_foot = (-6.0, -2.0)
            pose.tool_angle = -90.0 + 360.0 * t
            pose.prop = "wrench"
            pose.effect = "slash_spin"
            pose.effect_strength = math.sin(math.pi * t)
        elif animation == "block":
            brace = math.sin(math.pi * t)
            pose.crouch = 0.28 * brace
            pose.lean = -3.0
            pose.near_hand = (14.0, 11.0)
            pose.far_hand = (8.0, 16.0)
            pose.near_bend = 1.0
            pose.prop = "guard"
            pose.effect = "block"
            pose.effect_strength = brace
        elif animation in {"aim", "shoot"}:
            recoil = math.sin(math.pi * t) if animation == "shoot" else 0.0
            pose.lean = -4.0 + 6.0 * recoil
            pose.near_hand = (15.0 - 3.0 * recoil, 11.0)
            pose.far_hand = (8.0 - 2.0 * recoil, 14.0)
            pose.near_bend = 1.0
            pose.prop = "projector"
            pose.tool_angle = 0.0
            if animation == "shoot":
                pose.effect = "muzzle"
                pose.effect_strength = max(0.0, 1.0 - abs(t - 0.48) / 0.24)
        elif animation in {"charge", "cast"}:
            charge = _smoothstep(t) if animation == "charge" else math.sin(math.pi * t)
            pose.near_hand = (13.0, 8.0)
            pose.far_hand = (7.0, 13.0)
            pose.near_bend = 1.0
            pose.prop = "projector"
            pose.tool_angle = -12.0
            pose.effect = "charge" if animation == "charge" else "cast"
            pose.effect_strength = charge
        elif animation == "stomp":
            impact = math.sin(math.pi * t)
            pose.root_y = -10.0 * math.sin(math.pi * min(1.0, t * 1.3))
            pose.crouch = 0.65 * _smoothstep((t - 0.55) / 0.30)
            pose.near_hand = (9.0, 7.0)
            pose.far_hand = (-7.0, 8.0)
            pose.near_foot = (6.0, 0.0)
            pose.far_foot = (-4.0, -5.0)
            pose.prop = "none"
            pose.effect = "impact"
            pose.effect_strength = impact
        elif animation == "talk":
            pose.view = BobView.FRONT
            pose.body_bob = 0.22 * wave
            pose.talk_open = 0.12 + 0.88 * (0.5 + 0.5 * wave)
            pose.gesture = max(0.0, half)
            pose.head_tilt = 0.75 * wave
            pose.blink = frame == count - 1
        elif animation == "interact":
            pose.view = BobView.FRONT
            pose.body_bob = -0.25 * half
            pose.interact = max(0.0, half)
            pose.scan = wave
            pose.head_tilt = -0.8 * half
        elif animation in {"pickup", "throw"}:
            action = _smoothstep(t)
            pose.crouch = (
                (math.sin(math.pi * t) * 0.55) if animation == "pickup" else 0.2
            )
            pose.near_hand = (10.0 + 5.0 * action, 24.0 - 18.0 * action)
            pose.far_hand = (2.0 + 4.0 * action, 21.0 - 13.0 * action)
            pose.prop = "parcel"
            pose.effect = "throw" if animation == "throw" else ""
            pose.effect_strength = action
        elif animation == "celebrate":
            pose.root_y = -5.0 * abs(math.sin(math.pi * t))
            pose.near_hand = (8.0, -5.0)
            pose.far_hand = (-8.0, -4.0)
            pose.prop = "wrench"
            pose.tool_angle = -55.0 + 12.0 * wave
        elif animation in {"sit", "sleep"}:
            pose.crouch = 1.0
            pose.root_y = 0.0 if animation == "sit" else -2.0
            pose.lean = -3.0 if animation == "sit" else 8.0
            pose.rotation = 0.0 if animation == "sit" else 7.0
            pose.near_hand = (5.0, 21.0)
            pose.far_hand = (-5.0, 20.0)
            pose.near_foot = (10.0, 0.0)
            pose.far_foot = (-2.0, 0.0)
            pose.prop = "none"
            if animation == "sleep":
                pose.effect = "sleep"
                pose.effect_strength = 0.65 + 0.35 * wave
        elif animation in {"idle_front", "idle_side"}:
            pose.body_bob = 0.35 * wave
            pose.head_tilt = 0.55 * wave
            pose.scan = 0.25 * wave
            pose.blink = frame == count - 1
        return pose

    def render_animation_frame(
        self,
        spec: BobSpec,
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
        if pose.view is BobView.FRONT:
            self._draw_front(actor, cx, feet_y, spec, pose, scale)
        elif pose.view is BobView.SIDE:
            self._draw_side(actor, cx, feet_y, spec, pose, scale)
            self._draw_action_effects(actor, cx, feet_y, pose, scale)
        else:
            self._draw_three_quarter(actor, cx, feet_y, spec, pose, scale)

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
            tint = Image.new(
                "RGBA",
                actor.size,
                (255, 226, 196, round(160 * strength)),
            )
            tint.putalpha(alpha.point(lambda value: round(value * 0.62 * strength)))
            actor = Image.alpha_composite(actor, tint)

        if pose.opacity < 0.999:
            alpha = actor.getchannel("A")
            actor.putalpha(
                alpha.point(lambda value: round(value * _clamp01(pose.opacity)))
            )

        canvas.alpha_composite(actor)
        if ss > 1:
            canvas = canvas.resize((width, height), Image.Resampling.LANCZOS)
        return canvas

    # ------------------------------------------------------------------
    # Shared mechanics and props

    def _solve_two_bone_joint(
        self,
        root: Point,
        target: Point,
        upper_len: float,
        lower_len: float,
        *,
        bend_sign: float,
    ) -> Tuple[Point, Point]:
        dx = target[0] - root[0]
        dy = target[1] - root[1]
        distance = math.hypot(dx, dy)
        min_reach = abs(upper_len - lower_len) + 1e-4
        max_reach = max(min_reach + 1e-4, upper_len + lower_len - 1e-4)
        clamped = max(min_reach, min(max_reach, distance))
        if distance > 1e-6 and clamped != distance:
            ratio = clamped / distance
            target = (root[0] + dx * ratio, root[1] + dy * ratio)
            dx = target[0] - root[0]
            dy = target[1] - root[1]
        base = math.atan2(dy, dx)
        cosine = (upper_len * upper_len + clamped * clamped - lower_len * lower_len) / (
            2.0 * upper_len * clamped
        )
        offset = math.acos(max(-1.0, min(1.0, cosine)))
        angle = base - bend_sign * offset
        joint = (
            root[0] + math.cos(angle) * upper_len,
            root[1] + math.sin(angle) * upper_len,
        )
        return joint, target

    def _draw_two_bone_limb(
        self,
        d: ImageDraw.ImageDraw,
        root: Point,
        joint: Point,
        end: Point,
        s: float,
        *,
        fill: Color,
        width: float,
    ) -> None:
        outline = BOB_PALETTE["outline"]
        _line(d, [root, joint, end], fill=outline, width=round((width + 2.1) * s))
        _line(d, [root, joint, end], fill=fill, width=round(width * s))

    def _draw_hand(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        s: float,
        *,
        width: float = 5.4,
        height: float = 5.2,
    ) -> None:
        pal = BOB_PALETTE
        _ellipse(
            d,
            _bbox(center[0], center[1], width * s, height * s),
            fill=pal["skin"],
            outline=pal["outline"],
            width=round(0.9 * s),
        )

    def _draw_profile_boot(
        self,
        d: ImageDraw.ImageDraw,
        ankle: Point,
        ground_y: float,
        s: float,
        *,
        near: bool,
        foot_roll: float,
    ) -> None:
        pal = BOB_PALETTE
        bottom = max(ankle[1] + 6.6 * s, ground_y)
        heel = ankle[0] - (4.4 if near else 4.0) * s
        toe = ankle[0] + (8.4 if near else 7.7) * s
        roll = foot_roll * s
        points = [
            (heel, ankle[1] - 1.5 * s),
            (ankle[0] + 3.4 * s, ankle[1] - 0.8 * s),
            (toe, bottom - 3.0 * s - roll),
            (toe - 0.4 * s, bottom),
            (heel - 0.5 * s, bottom),
        ]
        _poly(
            d,
            points,
            fill=pal["boot"],
            outline=pal["outline"],
            width=round(1.0 * s),
        )
        _line(
            d,
            [(heel, bottom - 1.0 * s), (toe - 0.5 * s, bottom - 1.0 * s)],
            fill=pal["boot_sole"],
            width=round(1.4 * s),
        )
        _line(
            d,
            [
                (heel + 1.0 * s, ankle[1] + 1.5 * s),
                (ankle[0] + 4.4 * s, ankle[1] + 1.5 * s),
            ],
            fill=pal["boot_light"],
            width=round(1.1 * s),
        )

    def _draw_keyring(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        s: float,
        *,
        scale: float = 1.0,
        direction: float = 1.0,
    ) -> None:
        pal = BOB_PALETTE
        x, y = center
        ring = 2.8 * scale * s
        # Outline-only ring: a transparent fill would punch an alpha hole into
        # Bob whenever the keys overlap his vest or hand.
        d.ellipse(
            tuple(round(v) for v in _bbox(x, y, ring * 2.0, ring * 2.0)),
            outline=pal["brass_dark"],
            width=max(1, round(1.0 * scale * s)),
        )
        # Two readable keys beat the old glittery three-key tassel at sprite
        # scale.  Their unequal lengths preserve the silhouette without
        # obscuring Bob's hand and trousers.
        for index, dx in enumerate((-1.55, 1.25)):
            key_x = x + dx * scale * s
            key_top = y + ring * 0.70
            length = (5.3 + index * 0.9) * scale * s
            key_tip_x = key_x + direction * 0.35 * scale * s
            _line(
                d,
                [(key_x, key_top), (key_tip_x, key_top + length)],
                fill=pal["brass"],
                width=round(1.05 * scale * s),
            )
            tooth_y = key_top + length - 1.0 * scale * s
            _line(
                d,
                [
                    (key_tip_x, tooth_y),
                    (key_tip_x + direction * 1.5 * scale * s, tooth_y),
                ],
                fill=pal["brass_dark"],
                width=round(0.75 * scale * s),
            )

    def _draw_satchel(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        s: float,
        *,
        side: bool = False,
    ) -> None:
        pal = BOB_PALETTE
        x, y = center
        w = (11.0 if side else 13.0) * s
        h = 18.0 * s
        _rounded(
            d,
            (x - w / 2.0, y - h / 2.0, x + w / 2.0, y + h / 2.0),
            radius=2.0 * s,
            fill=pal["leather"],
            outline=pal["outline"],
            width=round(1.0 * s),
        )
        _poly(
            d,
            [
                (x - w / 2.0, y - h * 0.18),
                (x + w / 2.0, y - h * 0.18),
                (x + w * 0.34, y + h * 0.05),
                (x - w * 0.34, y + h * 0.05),
            ],
            fill=pal["leather_light"],
            outline=pal["outline"],
            width=round(0.8 * s),
        )
        _rounded(
            d,
            (x - 1.6 * s, y - 0.8 * s, x + 1.6 * s, y + 2.4 * s),
            radius=0.8 * s,
            fill=pal["brass"],
            outline=pal["outline"],
            width=round(0.6 * s),
        )
        # One readable driver handle rather than a noisy miniature tool rack.
        _line(
            d,
            [(x + 3.5 * s, y + 3.0 * s), (x + 3.2 * s, y + 10.0 * s)],
            fill=pal["steel_dark"],
            width=round(1.4 * s),
        )
        _rounded(
            d,
            (x + 1.7 * s, y + 7.0 * s, x + 4.8 * s, y + 11.5 * s),
            radius=0.8 * s,
            fill=pal["hi_vis"],
            outline=pal["outline"],
            width=round(0.6 * s),
        )

    def _draw_analyzer(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        s: float,
        *,
        open_amount: float,
        scan: float,
    ) -> None:
        pal = BOB_PALETTE
        x, y = center
        w = (15.0 + 5.0 * open_amount) * s
        h = 11.0 * s
        _rounded(
            d,
            (x - w / 2.0, y - h / 2.0, x + w / 2.0, y + h / 2.0),
            radius=2.0 * s,
            fill=pal["device"],
            outline=pal["outline"],
            width=round(1.0 * s),
        )
        _rounded(
            d,
            (
                x - w * 0.28,
                y - h * 0.28,
                x + w * 0.18,
                y + h * 0.08,
            ),
            radius=0.9 * s,
            fill=pal["device_screen"],
            outline=pal["outline"],
            width=round(0.65 * s),
        )
        scan_x = x - w * 0.22 + (0.5 + 0.5 * scan) * w * 0.30
        _line(
            d,
            [(scan_x, y - h * 0.23), (scan_x, y + h * 0.02)],
            fill=pal["white"],
            width=round(0.7 * s),
        )
        for dx in (-0.05, 0.12, 0.29):
            _ellipse(
                d,
                _bbox(x + w * dx, y + h * 0.27, 2.1 * s, 2.1 * s),
                fill=pal["indicator"] if dx == 0.29 else pal["steel_dark"],
                outline=pal["outline"],
                width=round(0.5 * s),
            )
        # A key blank clamped into the right edge sells the hardware role.
        _line(
            d,
            [
                (x + w / 2.0 - 1.2 * s, y - 0.4 * s),
                (x + w / 2.0 + 5.3 * s, y - 0.4 * s),
            ],
            fill=pal["brass"],
            width=round(1.4 * s),
        )
        _ellipse(
            d,
            _bbox(x + w / 2.0 + 5.5 * s, y - 0.4 * s, 3.4 * s, 3.4 * s),
            fill=pal["brass_dark"],
            outline=pal["outline"],
            width=round(0.7 * s),
        )

    def _draw_goggles_three_quarter(
        self, d: ImageDraw.ImageDraw, cx: float, cy: float, s: float
    ) -> None:
        pal = BOB_PALETTE
        _line(
            d,
            [(cx - 8.5 * s, cy), (cx + 8.0 * s, cy - 1.0 * s)],
            fill=pal["leather_dark"],
            width=round(1.3 * s),
        )
        for lx in (-4.3, 4.0):
            _rounded(
                d,
                (
                    cx + (lx - 2.6) * s,
                    cy - 2.6 * s,
                    cx + (lx + 2.6) * s,
                    cy + 2.2 * s,
                ),
                radius=1.4 * s,
                fill=pal["glass"],
                outline=pal["outline"],
                width=round(0.75 * s),
            )
            _line(
                d,
                [
                    (cx + (lx - 1.2) * s, cy - 1.7 * s),
                    (cx + (lx + 1.2) * s, cy + 0.8 * s),
                ],
                fill=pal["white"],
                width=round(0.55 * s),
            )

    # ------------------------------------------------------------------
    # Three-quarter view

    def _draw_three_quarter(
        self,
        image: Image.Image,
        cx: float,
        feet_y: float,
        spec: BobSpec,
        pose: BobPose,
        s: float,
    ) -> None:
        d = ImageDraw.Draw(image)
        pal = BOB_PALETTE
        outline = pal["outline"]
        boot_top = feet_y - spec.boot_h * s
        shin_top = boot_top - spec.shin_h * s
        hip_y = shin_top - spec.thigh_h * s
        shoulder_y = hip_y - spec.torso_h * s
        head_c = (
            cx + 1.5 * s,
            shoulder_y - 11.0 * s + pose.head_tilt * 0.12 * s,
        )

        # Rear leg first, then the near leg.  A slight stance gives him weight
        # without the old pinched, nearly merged trouser silhouette.
        legs = (
            (-1, cx - 5.4 * s, pal["pants_dark"]),
            (1, cx + 5.0 * s, pal["pants"]),
        )
        for sign, leg_x, fill in legs:
            knee_x = leg_x + sign * 0.7 * s
            ankle_x = leg_x + sign * 0.35 * s
            _poly(
                d,
                [
                    (leg_x - 4.3 * s, hip_y - 0.5 * s),
                    (leg_x + 4.3 * s, hip_y - 0.5 * s),
                    (knee_x + 3.8 * s, shin_top),
                    (ankle_x + 3.5 * s, boot_top),
                    (ankle_x - 3.5 * s, boot_top),
                    (knee_x - 3.8 * s, shin_top),
                ],
                fill=fill,
                outline=outline,
                width=round(1.0 * s),
            )
            _rounded(
                d,
                (
                    ankle_x - 5.7 * s,
                    boot_top - 0.2 * s,
                    ankle_x + 5.7 * s,
                    feet_y,
                ),
                radius=2.0 * s,
                fill=pal["boot"],
                outline=outline,
                width=round(1.0 * s),
            )
            _line(
                d,
                [
                    (ankle_x - 5.2 * s, feet_y - 1.2 * s),
                    (ankle_x + 5.2 * s, feet_y - 1.2 * s),
                ],
                fill=pal["boot_sole"],
                width=round(1.3 * s),
            )
            _line(
                d,
                [
                    (ankle_x - 3.5 * s, boot_top + 2.0 * s),
                    (ankle_x + 3.5 * s, boot_top + 2.0 * s),
                ],
                fill=pal["boot_light"],
                width=round(1.0 * s),
            )

        # Satchel and far arm are behind the body.
        self._draw_satchel(d, (cx - 13.0 * s, hip_y - 10.0 * s), s * 0.92)
        far_shoulder = (cx - 11.5 * s, shoulder_y + 5.0 * s)
        # Author the relaxed elbow explicitly.  The previous IK solution put
        # the elbow on the inside of the arm, making the limb fold across the
        # ribcage like a backwards hinge.  In a relaxed standing pose the
        # upper arm falls slightly outward and the forearm returns gently
        # toward the hip.
        far_elbow = (cx - 14.2 * s, shoulder_y + 17.0 * s)
        far_hand = (cx - 13.2 * s, hip_y - 3.0 * s)
        self._draw_two_bone_limb(
            d,
            far_shoulder,
            far_elbow,
            far_hand,
            s,
            fill=pal["shirt_dark"],
            width=5.8,
        )
        self._draw_hand(d, far_hand, s)

        # Under-shirt owns the complete ribcage; vest panels layer over it.
        _poly(
            d,
            [
                (cx - 14.5 * s, shoulder_y + 1.0 * s),
                (cx + 14.0 * s, shoulder_y + 1.0 * s),
                (cx + 11.2 * s, hip_y),
                (cx - 10.8 * s, hip_y),
            ],
            fill=pal["shirt"],
            outline=outline,
            width=round(1.1 * s),
        )
        # Rolled sleeve cuffs make the arms read as clothing rather than tubes.
        _rounded(
            d,
            (
                cx - 15.5 * s,
                shoulder_y + 5.0 * s,
                cx - 9.0 * s,
                shoulder_y + 12.0 * s,
            ),
            radius=1.5 * s,
            fill=pal["shirt_dark"],
            outline=outline,
            width=round(0.8 * s),
        )

        left_panel = [
            (cx - 11.8 * s, shoulder_y + 2.0 * s),
            (cx - 2.3 * s, shoulder_y + 3.2 * s),
            (cx - 1.0 * s, hip_y),
            (cx - 10.5 * s, hip_y),
        ]
        right_panel = [
            (cx + 1.5 * s, shoulder_y + 3.0 * s),
            (cx + 12.2 * s, shoulder_y + 2.2 * s),
            (cx + 10.8 * s, hip_y),
            (cx + 0.8 * s, hip_y),
        ]
        _poly(
            d,
            left_panel,
            fill=pal["vest_dark"],
            outline=outline,
            width=round(1.0 * s),
        )
        _poly(
            d,
            right_panel,
            fill=pal["vest"],
            outline=outline,
            width=round(1.0 * s),
        )
        # Broad, integrated lapels and one diagonal reflective tape create a
        # readable asymmetry without scattering tiny rectangles over the vest.
        _poly(
            d,
            [
                (cx - 2.5 * s, shoulder_y + 3.2 * s),
                (cx + 0.6 * s, shoulder_y + 5.2 * s),
                (cx - 4.0 * s, shoulder_y + 14.0 * s),
                (cx - 7.0 * s, shoulder_y + 8.0 * s),
            ],
            fill=pal["vest_light"],
            outline=outline,
            width=round(0.75 * s),
        )
        _poly(
            d,
            [
                (cx + 1.3 * s, shoulder_y + 3.2 * s),
                (cx + 5.5 * s, shoulder_y + 7.0 * s),
                (cx + 3.4 * s, shoulder_y + 13.8 * s),
                (cx + 0.2 * s, shoulder_y + 5.5 * s),
            ],
            fill=pal["vest_light"],
            outline=outline,
            width=round(0.75 * s),
        )
        _line(
            d,
            [
                (cx - 9.5 * s, shoulder_y + 15.2 * s),
                (cx + 8.8 * s, shoulder_y + 21.0 * s),
            ],
            fill=pal["hi_vis_dark"],
            width=round(3.8 * s),
        )
        _line(
            d,
            [
                (cx - 9.5 * s, shoulder_y + 15.2 * s),
                (cx + 8.8 * s, shoulder_y + 21.0 * s),
            ],
            fill=pal["hi_vis"],
            width=round(2.0 * s),
        )
        _rounded(
            d,
            (
                cx + 4.7 * s,
                shoulder_y + 8.0 * s,
                cx + 10.0 * s,
                shoulder_y + 13.5 * s,
            ),
            radius=1.1 * s,
            fill=pal["reinforce"],
            outline=outline,
            width=round(0.7 * s),
        )

        # Harness and belt unify the props with his body instead of floating.
        _line(
            d,
            [
                (cx + 7.0 * s, shoulder_y + 1.0 * s),
                (cx - 6.5 * s, hip_y + 1.0 * s),
            ],
            fill=pal["leather_dark"],
            width=round(4.2 * s),
        )
        _line(
            d,
            [
                (cx + 7.0 * s, shoulder_y + 1.0 * s),
                (cx - 6.5 * s, hip_y + 1.0 * s),
            ],
            fill=pal["leather"],
            width=round(2.3 * s),
        )
        _rounded(
            d,
            (cx - 12.5 * s, hip_y - 2.5 * s, cx + 12.5 * s, hip_y + 2.6 * s),
            radius=1.3 * s,
            fill=pal["leather_dark"],
            outline=outline,
            width=round(0.8 * s),
        )
        _rounded(
            d,
            (cx - 2.8 * s, hip_y - 2.0 * s, cx + 2.8 * s, hip_y + 2.2 * s),
            radius=0.8 * s,
            fill=pal["steel"],
            outline=outline,
            width=round(0.65 * s),
        )
        self._draw_keyring(d, (cx + 8.3 * s, hip_y + 4.5 * s), s, scale=0.60)

        # Near arm and iconic key ring.
        near_shoulder = (cx + 11.8 * s, shoulder_y + 5.0 * s)
        near_elbow = (
            cx + 14.5 * s + pose.scan * 0.25 * s,
            shoulder_y + 17.0 * s,
        )
        near_hand = (
            cx + 13.2 * s + pose.scan * 0.65 * s,
            hip_y - 4.0 * s,
        )
        self._draw_two_bone_limb(
            d,
            near_shoulder,
            near_elbow,
            near_hand,
            s,
            fill=pal["shirt"],
            width=6.0,
        )
        _rounded(
            d,
            _bbox(
                near_shoulder[0] + 0.4 * s,
                near_shoulder[1] + 5.5 * s,
                6.5 * s,
                7.0 * s,
            ),
            radius=1.4 * s,
            fill=pal["shirt_dark"],
            outline=outline,
            width=round(0.75 * s),
        )
        self._draw_hand(d, near_hand, s)
        self._draw_keyring(
            d,
            (near_hand[0] + 4.8 * s, near_hand[1] + 1.0 * s),
            s,
            scale=0.62,
        )

        self._draw_head_three_quarter(d, head_c, pose, s)

    def _draw_head_three_quarter(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        pose: BobPose,
        s: float,
    ) -> None:
        pal = BOB_PALETTE
        outline = pal["outline"]
        cx, cy = center

        # Short neck behind the head, then a full cranium and a softer jaw.
        _rounded(
            d,
            (cx - 4.1 * s, cy + 9.5 * s, cx + 4.1 * s, cy + 17.0 * s),
            radius=2.0 * s,
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.8 * s),
        )
        _ellipse(
            d,
            _bbox(cx, cy - 0.8 * s, 25.5 * s, 27.5 * s),
            fill=pal["skin"],
            outline=outline,
            width=round(1.1 * s),
        )
        # Ear on the far side.
        _ellipse(
            d,
            _bbox(cx - 10.8 * s, cy + 1.0 * s, 4.0 * s, 6.0 * s),
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.7 * s),
        )

        # Hair is one full cap plus a few deliberate tufts.  It follows the
        # skull instead of reading as a flat brown lid.
        hair_mass = [
            (cx - 11.8 * s, cy - 2.0 * s),
            (cx - 10.5 * s, cy - 9.0 * s),
            (cx - 5.5 * s, cy - 13.5 * s),
            (cx + 2.0 * s, cy - 14.2 * s),
            (cx + 9.0 * s, cy - 10.5 * s),
            (cx + 11.0 * s, cy - 4.0 * s),
            (cx + 6.0 * s, cy - 6.0 * s),
            (cx + 2.0 * s, cy - 3.8 * s),
            (cx - 2.0 * s, cy - 6.8 * s),
            (cx - 6.8 * s, cy - 3.8 * s),
        ]
        _poly(
            d,
            hair_mass,
            fill=pal["hair"],
            outline=outline,
            width=round(1.0 * s),
        )
        _poly(
            d,
            [
                (cx - 6.5 * s, cy - 11.5 * s),
                (cx - 1.5 * s, cy - 15.2 * s),
                (cx + 0.5 * s, cy - 8.0 * s),
            ],
            fill=pal["hair_mid"],
            outline=outline,
            width=round(0.65 * s),
        )
        _poly(
            d,
            [
                (cx + 0.5 * s, cy - 13.8 * s),
                (cx + 6.5 * s, cy - 12.2 * s),
                (cx + 3.3 * s, cy - 7.0 * s),
            ],
            fill=pal["hair_mid"],
            outline=outline,
            width=round(0.65 * s),
        )
        _line(
            d,
            [(cx - 3.5 * s, cy - 12.0 * s), (cx + 4.5 * s, cy - 10.8 * s)],
            fill=pal["hair_light"],
            width=round(1.1 * s),
        )
        self._draw_goggles_three_quarter(d, cx, cy - 8.5 * s, s)

        # Brows and eyes carry more confidence than the old sleepy dots.
        _line(
            d,
            [(cx - 7.0 * s, cy - 2.5 * s), (cx - 2.2 * s, cy - 3.2 * s)],
            fill=pal["hair"],
            width=round(1.0 * s),
        )
        _line(
            d,
            [(cx + 2.2 * s, cy - 3.4 * s), (cx + 7.4 * s, cy - 2.0 * s)],
            fill=pal["hair"],
            width=round(1.0 * s),
        )
        if pose.blink:
            _line(
                d,
                [(cx - 6.4 * s, cy), (cx - 2.5 * s, cy)],
                fill=outline,
                width=round(1.0 * s),
            )
            _line(
                d,
                [(cx + 2.5 * s, cy), (cx + 6.2 * s, cy + 0.3 * s)],
                fill=outline,
                width=round(1.0 * s),
            )
        else:
            for eye_x, eye_y in ((cx - 4.5 * s, cy), (cx + 4.3 * s, cy + 0.2 * s)):
                _ellipse(
                    d,
                    _bbox(eye_x, eye_y, 3.0 * s, 3.5 * s),
                    fill=pal["white"],
                    outline=outline,
                    width=round(0.65 * s),
                )
                _ellipse(
                    d,
                    _bbox(eye_x + 0.5 * s, eye_y + 0.2 * s, 1.4 * s, 1.8 * s),
                    fill=pal["eye"],
                )

        # Nose, beard mask, and mouth are integrated rather than a floating
        # moustache strip.  The beard follows cheek and jaw planes.
        _line(
            d,
            [(cx + 1.0 * s, cy + 0.6 * s), (cx + 2.8 * s, cy + 3.0 * s)],
            fill=pal["skin_shadow"],
            width=round(0.8 * s),
        )
        beard = [
            (cx - 8.4 * s, cy + 3.6 * s),
            (cx - 4.0 * s, cy + 5.2 * s),
            (cx + 1.5 * s, cy + 4.6 * s),
            (cx + 7.5 * s, cy + 3.8 * s),
            (cx + 7.0 * s, cy + 8.5 * s),
            (cx + 2.2 * s, cy + 12.3 * s),
            (cx - 3.7 * s, cy + 11.8 * s),
            (cx - 7.8 * s, cy + 8.5 * s),
        ]
        _poly(
            d,
            beard,
            fill=pal["beard"],
            outline=outline,
            width=round(0.75 * s),
        )
        _line(
            d,
            [beard[0], beard[1], beard[2], beard[3]],
            fill=pal["beard_dark"],
            width=round(0.7 * s),
        )
        _line(
            d,
            [(cx - 3.8 * s, cy + 6.2 * s), (cx + 4.8 * s, cy + 6.5 * s)],
            fill=outline,
            width=round(1.0 * s),
        )
        _line(
            d,
            [(cx - 1.8 * s, cy + 9.4 * s), (cx + 2.5 * s, cy + 9.5 * s)],
            fill=pal["hair_light"],
            width=round(0.65 * s),
        )

    # ------------------------------------------------------------------
    # Front view

    def _draw_front(
        self,
        image: Image.Image,
        cx: float,
        feet_y: float,
        spec: BobSpec,
        pose: BobPose,
        s: float,
    ) -> None:
        d = ImageDraw.Draw(image)
        pal = BOB_PALETTE
        outline = pal["outline"]
        boot_top = feet_y - spec.boot_h * s
        shin_top = boot_top - spec.shin_h * s
        hip_y = shin_top - spec.thigh_h * s
        shoulder_y = hip_y - spec.torso_h * s
        head_c = (cx, shoulder_y - 11.0 * s + pose.head_tilt * 0.1 * s)

        # Legs and boots.
        for sign, fill in ((-1, pal["pants_dark"]), (1, pal["pants"])):
            leg_x = cx + sign * 5.1 * s
            _poly(
                d,
                [
                    (leg_x - 4.2 * s, hip_y),
                    (leg_x + 4.2 * s, hip_y),
                    (leg_x + 3.6 * s, boot_top),
                    (leg_x - 3.6 * s, boot_top),
                ],
                fill=fill,
                outline=outline,
                width=round(1.0 * s),
            )
            _rounded(
                d,
                (
                    leg_x - 5.5 * s,
                    boot_top,
                    leg_x + 5.5 * s,
                    feet_y,
                ),
                radius=2.0 * s,
                fill=pal["boot"],
                outline=outline,
                width=round(1.0 * s),
            )
            _line(
                d,
                [
                    (leg_x - 5.1 * s, feet_y - 1.1 * s),
                    (leg_x + 5.1 * s, feet_y - 1.1 * s),
                ],
                fill=pal["boot_sole"],
                width=round(1.25 * s),
            )
            _line(
                d,
                [
                    (leg_x - 3.4 * s, boot_top + 2.0 * s),
                    (leg_x + 3.4 * s, boot_top + 2.0 * s),
                ],
                fill=pal["boot_light"],
                width=round(1.0 * s),
            )

        # Far-side satchel is partially visible behind the body.
        self._draw_satchel(d, (cx - 15.0 * s, hip_y - 10.0 * s), s * 0.88)

        # Back arm.  Front-view elbows must remain lateral to their shoulders:
        # upper arms drop slightly outward, then forearms return inward.  The
        # previous generic IK solution sometimes selected the opposite branch
        # and produced an anatomically backwards zig-zag across Bob's torso.
        left_shoulder = (cx - 12.5 * s, shoulder_y + 5.0 * s)
        relaxed_left_elbow = (cx - 15.2 * s, shoulder_y + 17.2 * s)
        relaxed_left_hand = (cx - 14.0 * s, hip_y - 3.0 * s)
        device_left_elbow = (cx - 13.8 * s, shoulder_y + 18.0 * s)
        device_left_hand = (cx - 6.2 * s, shoulder_y + 19.0 * s)
        mix = max(0.0, min(1.0, pose.interact))
        left_elbow = (
            relaxed_left_elbow[0]
            + (device_left_elbow[0] - relaxed_left_elbow[0]) * mix,
            relaxed_left_elbow[1]
            + (device_left_elbow[1] - relaxed_left_elbow[1]) * mix,
        )
        left_hand = (
            relaxed_left_hand[0] + (device_left_hand[0] - relaxed_left_hand[0]) * mix,
            relaxed_left_hand[1] + (device_left_hand[1] - relaxed_left_hand[1]) * mix,
        )
        self._draw_two_bone_limb(
            d,
            left_shoulder,
            left_elbow,
            left_hand,
            s,
            fill=pal["shirt_dark"],
            width=5.9,
        )
        self._draw_hand(d, left_hand, s)

        # Torso underlayer.
        _poly(
            d,
            [
                (cx - 15.0 * s, shoulder_y + 1.0 * s),
                (cx + 15.0 * s, shoulder_y + 1.0 * s),
                (cx + 11.5 * s, hip_y),
                (cx - 11.5 * s, hip_y),
            ],
            fill=pal["shirt"],
            outline=outline,
            width=round(1.1 * s),
        )
        # Collar and henley placket.
        _poly(
            d,
            [
                (cx - 6.0 * s, shoulder_y + 1.2 * s),
                (cx, shoulder_y + 6.2 * s),
                (cx + 6.0 * s, shoulder_y + 1.2 * s),
            ],
            fill=pal["shirt_dark"],
            outline=outline,
            width=round(0.75 * s),
        )
        _rounded(
            d,
            (cx - 1.4 * s, shoulder_y + 5.0 * s, cx + 1.4 * s, shoulder_y + 15.0 * s),
            radius=0.8 * s,
            fill=pal["shirt_light"],
            outline=outline,
            width=round(0.55 * s),
        )
        for y_off in (8.0, 11.5):
            _ellipse(
                d,
                _bbox(cx, shoulder_y + y_off * s, 1.4 * s, 1.4 * s),
                fill=pal["steel_dark"],
            )

        # Clean vest panels with no self-intersections or alpha wedges.
        _poly(
            d,
            [
                (cx - 13.0 * s, shoulder_y + 2.5 * s),
                (cx - 3.2 * s, shoulder_y + 3.5 * s),
                (cx - 1.2 * s, hip_y),
                (cx - 11.0 * s, hip_y),
            ],
            fill=pal["vest_dark"],
            outline=outline,
            width=round(1.0 * s),
        )
        _poly(
            d,
            [
                (cx + 3.2 * s, shoulder_y + 3.5 * s),
                (cx + 13.0 * s, shoulder_y + 2.5 * s),
                (cx + 11.0 * s, hip_y),
                (cx + 1.2 * s, hip_y),
            ],
            fill=pal["vest"],
            outline=outline,
            width=round(1.0 * s),
        )
        _poly(
            d,
            [
                (cx - 3.4 * s, shoulder_y + 3.4 * s),
                (cx - 0.2 * s, shoulder_y + 6.0 * s),
                (cx - 4.5 * s, shoulder_y + 14.0 * s),
                (cx - 7.2 * s, shoulder_y + 8.2 * s),
            ],
            fill=pal["vest_light"],
            outline=outline,
            width=round(0.7 * s),
        )
        _poly(
            d,
            [
                (cx + 3.4 * s, shoulder_y + 3.4 * s),
                (cx + 0.2 * s, shoulder_y + 6.0 * s),
                (cx + 4.5 * s, shoulder_y + 14.0 * s),
                (cx + 7.2 * s, shoulder_y + 8.2 * s),
            ],
            fill=pal["vest_light"],
            outline=outline,
            width=round(0.7 * s),
        )
        # Horizontal reflective band appears in every front frame.
        _line(
            d,
            [
                (cx - 10.5 * s, shoulder_y + 18.0 * s),
                (cx + 10.5 * s, shoulder_y + 18.0 * s),
            ],
            fill=pal["hi_vis_dark"],
            width=round(3.8 * s),
        )
        _line(
            d,
            [
                (cx - 10.5 * s, shoulder_y + 18.0 * s),
                (cx + 10.5 * s, shoulder_y + 18.0 * s),
            ],
            fill=pal["hi_vis"],
            width=round(2.0 * s),
        )
        _rounded(
            d,
            (
                cx + 5.0 * s,
                shoulder_y + 8.0 * s,
                cx + 10.2 * s,
                shoulder_y + 13.3 * s,
            ),
            radius=1.0 * s,
            fill=pal["reinforce"],
            outline=outline,
            width=round(0.65 * s),
        )
        _rounded(
            d,
            (cx - 12.8 * s, hip_y - 2.5 * s, cx + 12.8 * s, hip_y + 2.6 * s),
            radius=1.3 * s,
            fill=pal["leather_dark"],
            outline=outline,
            width=round(0.8 * s),
        )
        _rounded(
            d,
            (cx - 2.8 * s, hip_y - 2.0 * s, cx + 2.8 * s, hip_y + 2.2 * s),
            radius=0.8 * s,
            fill=pal["steel"],
            outline=outline,
            width=round(0.65 * s),
        )
        self._draw_keyring(d, (cx + 8.5 * s, hip_y + 4.5 * s), s, scale=0.58)

        # Near/right arm.  As above, keep the elbow outside the shoulder in
        # every front-view pose.  Interaction rotates the forearm inward around
        # a low, stable elbow; talking rotates it outward and upward rather than
        # reversing the elbow hinge.
        right_shoulder = (cx + 12.5 * s, shoulder_y + 5.0 * s)
        relaxed_right_elbow = (cx + 15.2 * s, shoulder_y + 17.2 * s)
        relaxed_right_hand = (cx + 14.0 * s, hip_y - 3.0 * s)
        device_right_elbow = (cx + 13.8 * s, shoulder_y + 18.0 * s)
        device_right_hand = (cx + 6.2 * s, shoulder_y + 19.0 * s)
        gesture_right_elbow = (cx + 15.5 * s, shoulder_y + 16.0 * s)
        gesture_right_hand = (cx + 20.0 * s, shoulder_y + 11.5 * s)
        interact_mix = max(0.0, min(1.0, pose.interact))
        gesture_mix = 0.0 if interact_mix > 0.0 else max(0.0, min(1.0, pose.gesture))
        right_elbow = (
            relaxed_right_elbow[0]
            + (device_right_elbow[0] - relaxed_right_elbow[0]) * interact_mix
            + (gesture_right_elbow[0] - relaxed_right_elbow[0]) * gesture_mix,
            relaxed_right_elbow[1]
            + (device_right_elbow[1] - relaxed_right_elbow[1]) * interact_mix
            + (gesture_right_elbow[1] - relaxed_right_elbow[1]) * gesture_mix,
        )
        right_hand = (
            relaxed_right_hand[0]
            + (device_right_hand[0] - relaxed_right_hand[0]) * interact_mix
            + (gesture_right_hand[0] - relaxed_right_hand[0]) * gesture_mix,
            relaxed_right_hand[1]
            + (device_right_hand[1] - relaxed_right_hand[1]) * interact_mix
            + (gesture_right_hand[1] - relaxed_right_hand[1]) * gesture_mix,
        )
        self._draw_two_bone_limb(
            d,
            right_shoulder,
            right_elbow,
            right_hand,
            s,
            fill=pal["shirt"],
            width=6.0,
        )
        self._draw_hand(d, right_hand, s)
        if pose.interact <= 0.0 and pose.gesture <= 0.05:
            self._draw_keyring(
                d,
                (right_hand[0] + 4.5 * s, right_hand[1] + 0.8 * s),
                s,
                scale=0.68,
            )

        if pose.interact > 0.02:
            self._draw_analyzer(
                d,
                (cx, shoulder_y + 19.0 * s),
                s,
                open_amount=pose.interact,
                scan=pose.scan,
            )

        self._draw_head_front(d, head_c, pose, s)

    def _draw_head_front(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        pose: BobPose,
        s: float,
    ) -> None:
        pal = BOB_PALETTE
        outline = pal["outline"]
        cx, cy = center
        _rounded(
            d,
            (cx - 4.2 * s, cy + 9.5 * s, cx + 4.2 * s, cy + 17.0 * s),
            radius=2.0 * s,
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.8 * s),
        )
        _ellipse(
            d,
            _bbox(cx, cy - 0.8 * s, 25.5 * s, 27.5 * s),
            fill=pal["skin"],
            outline=outline,
            width=round(1.1 * s),
        )
        for sign in (-1, 1):
            _ellipse(
                d,
                _bbox(cx + sign * 11.5 * s, cy + 1.0 * s, 4.0 * s, 6.0 * s),
                fill=pal["skin_shadow"],
                outline=outline,
                width=round(0.65 * s),
            )

        hair = [
            (cx - 12.0 * s, cy - 2.0 * s),
            (cx - 10.5 * s, cy - 9.0 * s),
            (cx - 5.5 * s, cy - 13.5 * s),
            (cx, cy - 14.5 * s),
            (cx + 6.5 * s, cy - 13.0 * s),
            (cx + 11.5 * s, cy - 8.0 * s),
            (cx + 12.0 * s, cy - 2.0 * s),
            (cx + 6.5 * s, cy - 5.5 * s),
            (cx + 2.0 * s, cy - 3.5 * s),
            (cx - 2.0 * s, cy - 6.5 * s),
            (cx - 7.0 * s, cy - 3.5 * s),
        ]
        _poly(d, hair, fill=pal["hair"], outline=outline, width=round(1.0 * s))
        _poly(
            d,
            [
                (cx - 6.0 * s, cy - 11.8 * s),
                (cx - 1.0 * s, cy - 15.0 * s),
                (cx + 0.8 * s, cy - 7.8 * s),
            ],
            fill=pal["hair_mid"],
            outline=outline,
            width=round(0.6 * s),
        )
        _poly(
            d,
            [
                (cx + 0.8 * s, cy - 14.0 * s),
                (cx + 6.8 * s, cy - 12.2 * s),
                (cx + 3.4 * s, cy - 7.0 * s),
            ],
            fill=pal["hair_mid"],
            outline=outline,
            width=round(0.6 * s),
        )
        self._draw_goggles_three_quarter(d, cx, cy - 8.5 * s, s)

        _line(
            d,
            [(cx - 7.2 * s, cy - 2.5 * s), (cx - 2.2 * s, cy - 3.0 * s)],
            fill=pal["hair"],
            width=round(1.0 * s),
        )
        _line(
            d,
            [(cx + 2.2 * s, cy - 3.0 * s), (cx + 7.2 * s, cy - 2.5 * s)],
            fill=pal["hair"],
            width=round(1.0 * s),
        )
        if pose.blink:
            for sign in (-1, 1):
                _line(
                    d,
                    [
                        (cx + sign * 6.2 * s, cy),
                        (cx + sign * 2.6 * s, cy),
                    ],
                    fill=outline,
                    width=round(1.0 * s),
                )
        else:
            for sign in (-1, 1):
                ex = cx + sign * 4.4 * s
                _ellipse(
                    d,
                    _bbox(ex, cy, 3.0 * s, 3.5 * s),
                    fill=pal["white"],
                    outline=outline,
                    width=round(0.65 * s),
                )
                _ellipse(
                    d,
                    _bbox(ex, cy + 0.2 * s, 1.4 * s, 1.8 * s),
                    fill=pal["eye"],
                )

        _line(
            d,
            [(cx, cy + 0.7 * s), (cx + 1.3 * s, cy + 3.0 * s)],
            fill=pal["skin_shadow"],
            width=round(0.8 * s),
        )
        beard = [
            (cx - 8.6 * s, cy + 3.7 * s),
            (cx - 4.0 * s, cy + 5.0 * s),
            (cx, cy + 4.6 * s),
            (cx + 4.0 * s, cy + 5.0 * s),
            (cx + 8.6 * s, cy + 3.7 * s),
            (cx + 7.3 * s, cy + 8.7 * s),
            (cx + 2.7 * s, cy + 12.4 * s),
            (cx - 2.7 * s, cy + 12.4 * s),
            (cx - 7.3 * s, cy + 8.7 * s),
        ]
        _poly(
            d,
            beard,
            fill=pal["beard"],
            outline=outline,
            width=round(0.75 * s),
        )
        _line(
            d,
            [beard[0], beard[1], beard[2], beard[3], beard[4]],
            fill=pal["beard_dark"],
            width=round(0.7 * s),
        )
        if pose.talk_open > 0.18:
            mouth_h = (1.2 + 2.0 * pose.talk_open) * s
            _ellipse(
                d,
                _bbox(cx, cy + 6.6 * s, 6.8 * s, mouth_h),
                fill=pal["beard_dark"],
                outline=outline,
                width=round(0.7 * s),
            )
            _line(
                d,
                [
                    (cx - 2.2 * s, cy + 6.4 * s),
                    (cx + 2.2 * s, cy + 6.4 * s),
                ],
                fill=pal["white"],
                width=round(0.6 * s),
            )
        else:
            _line(
                d,
                [(cx - 3.7 * s, cy + 6.5 * s), (cx + 3.7 * s, cy + 6.5 * s)],
                fill=outline,
                width=round(1.0 * s),
            )

    # ------------------------------------------------------------------
    # Side view

    def _draw_wrench(
        self,
        d: ImageDraw.ImageDraw,
        hand: Point,
        angle_deg: float,
        s: float,
    ) -> None:
        """Draw Bob's oversized adjustable wrench in hand-local orientation."""
        pal = BOB_PALETTE
        angle = math.radians(angle_deg)
        ux, uy = math.cos(angle), math.sin(angle)
        px, py = -uy, ux
        tail = (hand[0] - ux * 4.0 * s, hand[1] - uy * 4.0 * s)
        head = (hand[0] + ux * 21.0 * s, hand[1] + uy * 21.0 * s)
        _line(d, [tail, head], fill=pal["outline"], width=round(4.6 * s))
        _line(d, [tail, head], fill=pal["steel"], width=round(2.8 * s))
        jaw_base = (head[0] - ux * 2.0 * s, head[1] - uy * 2.0 * s)
        jaw_a = (head[0] + px * 5.0 * s, head[1] + py * 5.0 * s)
        jaw_b = (head[0] - px * 5.0 * s, head[1] - py * 5.0 * s)
        notch_a = (
            head[0] + ux * 3.5 * s + px * 2.0 * s,
            head[1] + uy * 3.5 * s + py * 2.0 * s,
        )
        notch_b = (
            head[0] + ux * 3.5 * s - px * 2.0 * s,
            head[1] + uy * 3.5 * s - py * 2.0 * s,
        )
        _poly(
            d,
            [jaw_base, jaw_a, notch_a, notch_b, jaw_b],
            fill=pal["steel"],
            outline=pal["outline"],
            width=round(1.0 * s),
        )
        _ellipse(
            d,
            _bbox(tail[0], tail[1], 3.2 * s, 3.2 * s),
            fill=pal["leather_dark"],
            outline=pal["outline"],
            width=round(0.6 * s),
        )

    def _draw_projector(
        self,
        d: ImageDraw.ImageDraw,
        hand: Point,
        angle_deg: float,
        s: float,
    ) -> Point:
        """Compact diagnostic pulse projector; returns its muzzle point."""
        pal = BOB_PALETTE
        angle = math.radians(angle_deg)
        ux, uy = math.cos(angle), math.sin(angle)
        px, py = -uy, ux
        center = (hand[0] + ux * 5.5 * s, hand[1] + uy * 5.5 * s)
        half_l, half_w = 6.2 * s, 3.5 * s
        body = [
            (
                center[0] - ux * half_l - px * half_w,
                center[1] - uy * half_l - py * half_w,
            ),
            (
                center[0] + ux * half_l - px * half_w,
                center[1] + uy * half_l - py * half_w,
            ),
            (
                center[0] + ux * half_l + px * half_w,
                center[1] + uy * half_l + py * half_w,
            ),
            (
                center[0] - ux * half_l + px * half_w,
                center[1] - uy * half_l + py * half_w,
            ),
        ]
        _poly(d, body, fill=pal["device"], outline=pal["outline"], width=round(0.9 * s))
        muzzle = (center[0] + ux * 8.5 * s, center[1] + uy * 8.5 * s)
        _line(d, [center, muzzle], fill=pal["steel_dark"], width=round(3.4 * s))
        _line(d, [center, muzzle], fill=pal["steel"], width=round(1.8 * s))
        _ellipse(
            d,
            _bbox(center[0], center[1], 4.2 * s, 4.2 * s),
            fill=pal["device_screen"],
            outline=pal["outline"],
            width=round(0.6 * s),
        )
        return muzzle

    def _draw_guard_plate(
        self,
        d: ImageDraw.ImageDraw,
        hand: Point,
        s: float,
    ) -> None:
        pal = BOB_PALETTE
        _rounded(
            d,
            (
                hand[0] - 1.0 * s,
                hand[1] - 12.0 * s,
                hand[0] + 11.0 * s,
                hand[1] + 12.0 * s,
            ),
            radius=3.0 * s,
            fill=pal["device"],
            outline=pal["outline"],
            width=round(1.2 * s),
        )
        _line(
            d,
            [
                (hand[0] + 2.0 * s, hand[1] - 8.0 * s),
                (hand[0] + 7.5 * s, hand[1] + 7.0 * s),
            ],
            fill=pal["hi_vis"],
            width=round(2.0 * s),
        )
        _ellipse(
            d,
            _bbox(hand[0] + 5.0 * s, hand[1], 4.0 * s, 4.0 * s),
            fill=pal["device_screen"],
            outline=pal["outline"],
            width=round(0.6 * s),
        )

    def _draw_action_effects(
        self,
        image: Image.Image,
        cx: float,
        feet_y: float,
        pose: BobPose,
        s: float,
    ) -> None:
        """Line-based gameplay effects. Never paints a ground/drop shadow."""
        if not pose.effect or pose.effect_strength <= 0.001:
            return
        d = ImageDraw.Draw(image)
        pal = BOB_PALETTE
        strength = _clamp01(pose.effect_strength)
        body_y = feet_y - 45.0 * s
        glow = (*pal["device_screen"][:3], round(215 * strength))
        brass = (*pal["brass_light"][:3], round(220 * strength))

        if pose.effect.startswith("slash"):
            if pose.effect == "slash_up":
                box = (cx - 23 * s, body_y - 43 * s, cx + 31 * s, body_y + 10 * s)
                start, end = 190, 330
            elif pose.effect == "slash_down":
                box = (cx - 8 * s, body_y - 2 * s, cx + 44 * s, body_y + 50 * s)
                start, end = 15, 145
            elif pose.effect == "slash_back":
                box = (cx - 48 * s, body_y - 24 * s, cx + 5 * s, body_y + 31 * s)
                start, end = 215, 345
            elif pose.effect == "slash_spin":
                box = (cx - 38 * s, body_y - 34 * s, cx + 38 * s, body_y + 38 * s)
                start, end = 0, 350
            else:
                box = (cx - 5 * s, body_y - 30 * s, cx + 50 * s, body_y + 31 * s)
                start, end = 205, 350
            d.arc(
                tuple(round(v) for v in box),
                start=start,
                end=end,
                fill=brass,
                width=max(1, round(2.4 * s)),
            )
            inner = tuple(
                round(v)
                for v in (
                    box[0] + 5 * s,
                    box[1] + 5 * s,
                    box[2] - 5 * s,
                    box[3] - 5 * s,
                )
            )
            d.arc(inner, start=start, end=end, fill=glow, width=max(1, round(1.2 * s)))
        elif pose.effect == "speed":
            for i, yoff in enumerate((-11.0, 1.0, 13.0)):
                length = (14.0 + 5.0 * i) * strength
                _line(
                    d,
                    [
                        (cx - (15.0 + length) * s, body_y + yoff * s),
                        (cx - 15.0 * s, body_y + yoff * s),
                    ],
                    fill=glow,
                    width=round((1.2 + 0.25 * i) * s),
                )
        elif pose.effect in {"blink_out", "blink_in"}:
            direction = -1.0 if pose.effect == "blink_out" else 1.0
            for i in range(5):
                y = body_y + (-24.0 + i * 12.0) * s
                x0 = cx + direction * (8.0 + i * 2.0) * s
                x1 = cx + direction * (25.0 + i * 3.0) * s
                _line(d, [(x0, y), (x1, y)], fill=glow, width=round(1.4 * s))
        elif pose.effect == "muzzle":
            origin = (cx + 30.0 * s, body_y + 3.0 * s)
            rays = [(-6.0, -6.0), (10.0, 0.0), (-5.0, 7.0)]
            for dx, dy in rays:
                _line(
                    d,
                    [
                        origin,
                        (origin[0] + dx * s * strength, origin[1] + dy * s * strength),
                    ],
                    fill=brass,
                    width=round(1.7 * s),
                )
            _ellipse(
                d,
                _bbox(origin[0], origin[1], 7.0 * s * strength, 7.0 * s * strength),
                fill=glow,
            )
        elif pose.effect in {"charge", "cast"}:
            center = (
                cx + 28.0 * s,
                body_y - (4.0 if pose.effect == "cast" else 0.0) * s,
            )
            radius = (4.0 + 9.0 * strength) * s
            _ellipse(
                d,
                _bbox(center[0], center[1], radius * 2, radius * 2),
                fill=(*pal["device_screen"][:3], round(75 * strength)),
                outline=glow,
                width=round(1.5 * s),
            )
            d.arc(
                tuple(
                    round(v)
                    for v in _bbox(center[0], center[1], radius * 2.8, radius * 1.5)
                ),
                15,
                320,
                fill=brass,
                width=max(1, round(1.0 * s)),
            )
        elif pose.effect == "block":
            box = (cx + 6 * s, body_y - 28 * s, cx + 39 * s, body_y + 28 * s)
            d.arc(
                tuple(round(v) for v in box),
                255,
                105,
                fill=glow,
                width=max(1, round(2.0 * s)),
            )
        elif pose.effect == "impact":
            y = feet_y - 1.0 * s
            for dx in (-13.0, -6.0, 7.0, 14.0):
                _line(
                    d,
                    [(cx + dx * s, y), (cx + dx * 1.35 * s, y - 6.0 * s * strength)],
                    fill=brass,
                    width=round(1.2 * s),
                )
        elif pose.effect == "hover":
            for dx in (-6.0, 5.0):
                _line(
                    d,
                    [
                        (cx + dx * s, feet_y - 3 * s),
                        (cx + dx * s, feet_y + (4.0 + 6.0 * strength) * s),
                    ],
                    fill=glow,
                    width=round(1.3 * s),
                )
        elif pose.effect == "water":
            for i in range(3):
                y = feet_y - (5.0 + i * 5.0) * s
                d.arc(
                    (
                        round(cx - 30 * s),
                        round(y - 3 * s),
                        round(cx - 7 * s),
                        round(y + 3 * s),
                    ),
                    180,
                    350,
                    fill=glow,
                    width=max(1, round(1.0 * s)),
                )
        elif pose.effect == "hit":
            center = (cx + 9.0 * s, body_y - 2.0 * s)
            for angle in range(0, 360, 60):
                r = math.radians(angle)
                _line(
                    d,
                    [
                        center,
                        (
                            center[0] + math.cos(r) * 9.0 * s * strength,
                            center[1] + math.sin(r) * 9.0 * s * strength,
                        ),
                    ],
                    fill=brass,
                    width=round(1.2 * s),
                )
        elif pose.effect == "sleep":
            for i in range(3):
                x = cx + (18.0 + i * 6.0) * s
                y = body_y - (18.0 + i * 7.0) * s
                _line(
                    d,
                    [(x, y), (x + 4 * s, y), (x, y - 5 * s), (x + 4 * s, y - 5 * s)],
                    fill=glow,
                    width=round(1.0 * s),
                )

    def _draw_side(
        self,
        image: Image.Image,
        cx: float,
        feet_y: float,
        spec: BobSpec,
        pose: BobPose,
        s: float,
    ) -> None:
        d = ImageDraw.Draw(image)
        pal = BOB_PALETTE
        outline = pal["outline"]
        base_boot_top = feet_y - spec.boot_h * s
        base_shin_top = base_boot_top - spec.shin_h * s
        base_hip_y = base_shin_top - spec.thigh_h * s
        body_shift = pose.walk_body_y * s if pose.walk_index >= 0 else 0.0
        crouch = _clamp01(pose.crouch)
        hip_y = base_hip_y + body_shift + 4.5 * crouch * s
        shoulder_y = hip_y - (spec.torso_h - 6.0 * crouch) * s
        lean = (
            (
                0.8 * pose.step * pose.arm_swing
                if pose.walk_index >= 0
                else 0.5 * pose.scan
            )
            + pose.lean
        ) * s
        head_c = (cx + 1.8 * s + lean, shoulder_y - 11.0 * s)

        # Satchel and far arm are behind the torso.
        self._draw_satchel(
            d, (cx - 8.5 * s + lean, hip_y - 10.0 * s), s * 0.92, side=True
        )
        far_shoulder = (cx - 3.6 * s + lean, shoulder_y + 5.0 * s)
        if pose.far_hand is not None:
            far_target = (
                cx + pose.far_hand[0] * s + lean,
                shoulder_y + pose.far_hand[1] * s,
            )
        elif pose.walk_index >= 0:
            far_target = (
                far_shoulder[0] - pose.step * 8.0 * pose.arm_swing * s,
                shoulder_y + 26.0 * s,
            )
        else:
            far_target = (cx - 5.8 * s + lean, hip_y - 3.0 * s)
        far_elbow, far_hand = self._solve_two_bone_joint(
            far_shoulder,
            far_target,
            spec.arm_upper * s,
            spec.arm_lower * s,
            bend_sign=pose.far_bend,
        )
        self._draw_two_bone_limb(
            d,
            far_shoulder,
            far_elbow,
            far_hand,
            s,
            fill=pal["shirt_dark"],
            width=5.8,
        )
        self._draw_hand(d, far_hand, s, width=4.9, height=5.0)

        # Authored foot targets: near leg begins at rear contact while far leg
        # begins at front contact.  The phases include down, passing, and up,
        # avoiding the old scissor-leg interpolation.
        if pose.walk_index >= 0:
            near_targets = (
                (-8.5, 0.0, 0.0),
                (-5.0, 0.0, 0.0),
                (0.0, -2.0, 0.6),
                (5.0, -4.2, 1.5),
                (8.5, 0.0, 0.0),
                (5.0, 0.0, 0.0),
                (0.0, -2.0, 0.6),
                (-5.0, -4.2, 1.5),
            )
            far_targets = (
                (8.5, 0.0, 0.0),
                (5.0, 0.0, 0.0),
                (0.0, -2.0, 0.6),
                (-5.0, -4.2, 1.5),
                (-8.5, 0.0, 0.0),
                (-5.0, 0.0, 0.0),
                (0.0, -2.0, 0.6),
                (5.0, -4.2, 1.5),
            )
            near_dx, near_lift, near_roll = near_targets[pose.walk_index]
            far_dx, far_lift, far_roll = far_targets[pose.walk_index]
            near_dx *= pose.gait_scale
            far_dx *= pose.gait_scale
            near_lift *= pose.gait_scale
            far_lift *= pose.gait_scale
        else:
            near_dx, near_lift, near_roll = (3.2, 0.0, 0.0)
            far_dx, far_lift, far_roll = (-3.2, 0.0, 0.0)

        far_hip = (cx - 1.4 * s + lean, hip_y)
        near_hip = (cx + 2.8 * s + lean, hip_y)
        far_ground = feet_y
        near_ground = feet_y
        if pose.far_foot is not None:
            far_ankle_target = (
                cx + pose.far_foot[0] * s + lean,
                base_boot_top + pose.far_foot[1] * s,
            )
        else:
            far_ankle_target = (
                cx + far_dx * s + lean,
                base_boot_top + far_lift * s,
            )
        if pose.near_foot is not None:
            near_ankle_target = (
                cx + pose.near_foot[0] * s + lean,
                base_boot_top + pose.near_foot[1] * s,
            )
        else:
            near_ankle_target = (
                cx + near_dx * s + lean,
                base_boot_top + near_lift * s,
            )
        far_knee, far_ankle = self._solve_two_bone_joint(
            far_hip,
            far_ankle_target,
            spec.thigh_h * s,
            spec.shin_h * s,
            bend_sign=1.0,
        )
        near_knee, near_ankle = self._solve_two_bone_joint(
            near_hip,
            near_ankle_target,
            spec.thigh_h * s,
            spec.shin_h * s,
            bend_sign=1.0,
        )
        self._draw_two_bone_limb(
            d,
            far_hip,
            far_knee,
            far_ankle,
            s,
            fill=pal["pants_dark"],
            width=6.2,
        )
        self._draw_profile_boot(
            d,
            far_ankle,
            far_ground,
            s,
            near=False,
            foot_roll=far_roll,
        )
        self._draw_two_bone_limb(
            d,
            near_hip,
            near_knee,
            near_ankle,
            s,
            fill=pal["pants"],
            width=6.4,
        )
        self._draw_profile_boot(
            d,
            near_ankle,
            near_ground,
            s,
            near=True,
            foot_roll=near_roll,
        )

        # Head and neck are behind the torso shoulder seam, so the jacket owns
        # the lower-neck overlap and Bob never looks decapitated or pasted on.
        self._draw_head_side(d, head_c, pose, s)

        torso = [
            (cx - 7.0 * s + lean, shoulder_y),
            (cx + 5.0 * s + lean, shoulder_y + 1.0 * s),
            (cx + 8.0 * s + lean, shoulder_y + 9.0 * s),
            (cx + 7.0 * s + lean, shoulder_y + 20.0 * s),
            (cx + 7.8 * s + lean, hip_y),
            (cx - 6.3 * s + lean, hip_y),
        ]
        _poly(d, torso, fill=pal["shirt"], outline=outline, width=round(1.1 * s))
        vest = [
            (cx - 5.5 * s + lean, shoulder_y + 1.5 * s),
            (cx + 2.0 * s + lean, shoulder_y + 2.8 * s),
            (cx + 6.5 * s + lean, shoulder_y + 10.0 * s),
            (cx + 5.8 * s + lean, hip_y),
            (cx - 5.5 * s + lean, hip_y),
        ]
        _poly(d, vest, fill=pal["vest"], outline=outline, width=round(1.0 * s))
        _poly(
            d,
            [
                (cx - 4.8 * s + lean, shoulder_y + 2.0 * s),
                (cx + 1.5 * s + lean, shoulder_y + 3.2 * s),
                (cx - 1.0 * s + lean, shoulder_y + 11.5 * s),
            ],
            fill=pal["vest_light"],
            outline=outline,
            width=round(0.7 * s),
        )
        _line(
            d,
            [
                (cx - 3.8 * s + lean, shoulder_y + 16.0 * s),
                (cx + 5.8 * s + lean, shoulder_y + 18.5 * s),
            ],
            fill=pal["hi_vis_dark"],
            width=round(3.6 * s),
        )
        _line(
            d,
            [
                (cx - 3.8 * s + lean, shoulder_y + 16.0 * s),
                (cx + 5.8 * s + lean, shoulder_y + 18.5 * s),
            ],
            fill=pal["hi_vis"],
            width=round(1.9 * s),
        )
        _line(
            d,
            [
                (cx + 1.0 * s + lean, shoulder_y + 1.5 * s),
                (cx - 4.8 * s + lean, hip_y),
            ],
            fill=pal["leather_dark"],
            width=round(4.0 * s),
        )
        _line(
            d,
            [
                (cx + 1.0 * s + lean, shoulder_y + 1.5 * s),
                (cx - 4.8 * s + lean, hip_y),
            ],
            fill=pal["leather"],
            width=round(2.2 * s),
        )
        _rounded(
            d,
            (
                cx - 6.5 * s + lean,
                hip_y - 2.5 * s,
                cx + 8.2 * s + lean,
                hip_y + 2.6 * s,
            ),
            radius=1.2 * s,
            fill=pal["leather_dark"],
            outline=outline,
            width=round(0.8 * s),
        )
        self._draw_keyring(
            d,
            (cx + 6.5 * s + lean, hip_y + 4.5 * s),
            s,
            scale=0.55,
        )

        # Near arm in front, with shoulder positioned beneath the neck rather
        # than pasted onto the front edge of the chest.
        near_shoulder = (cx + 3.8 * s + lean, shoulder_y + 5.0 * s)
        if pose.near_hand is not None:
            near_target = (
                cx + pose.near_hand[0] * s + lean,
                shoulder_y + pose.near_hand[1] * s,
            )
        elif pose.walk_index >= 0:
            near_target = (
                near_shoulder[0] + pose.step * 8.0 * pose.arm_swing * s,
                shoulder_y + 26.0 * s,
            )
        else:
            near_target = (cx + 6.5 * s + lean, hip_y - 3.0 * s)
        near_elbow, near_hand = self._solve_two_bone_joint(
            near_shoulder,
            near_target,
            spec.arm_upper * s,
            spec.arm_lower * s,
            bend_sign=pose.near_bend,
        )
        self._draw_two_bone_limb(
            d,
            near_shoulder,
            near_elbow,
            near_hand,
            s,
            fill=pal["shirt"],
            width=6.0,
        )
        self._draw_hand(d, near_hand, s, width=5.0, height=5.1)
        if pose.prop == "keys":
            self._draw_keyring(
                d,
                (near_hand[0] + 4.2 * s, near_hand[1] + 0.8 * s),
                s,
                scale=0.62,
            )
        elif pose.prop == "wrench":
            self._draw_wrench(d, near_hand, pose.tool_angle, s)
        elif pose.prop == "projector":
            self._draw_projector(d, near_hand, pose.tool_angle, s)
        elif pose.prop == "guard":
            self._draw_guard_plate(d, near_hand, s)
        elif pose.prop == "parcel":
            _rounded(
                d,
                (
                    near_hand[0] - 4.5 * s,
                    near_hand[1] - 4.0 * s,
                    near_hand[0] + 7.5 * s,
                    near_hand[1] + 5.5 * s,
                ),
                radius=1.2 * s,
                fill=pal["device"],
                outline=outline,
                width=round(0.8 * s),
            )
            _line(
                d,
                [
                    (near_hand[0] + 1.5 * s, near_hand[1] - 4.0 * s),
                    (near_hand[0] + 1.5 * s, near_hand[1] + 5.5 * s),
                ],
                fill=pal["indicator"],
                width=round(1.0 * s),
            )

    def _draw_head_side(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        pose: BobPose,
        s: float,
    ) -> None:
        pal = BOB_PALETTE
        outline = pal["outline"]
        cx, cy = center

        # The old profile was materially smaller than Bob's front and
        # three-quarter heads.  Scale the cranium and face together around the
        # same neck anchor so his identity and apparent body scale do not jump
        # when the animation changes view.
        hs = 1.10 * s
        cy -= 0.35 * s
        _rounded(
            d,
            (cx - 3.8 * s, cy + 10.2 * hs, cx + 3.8 * s, cy + 17.0 * s),
            radius=2.0 * s,
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.75 * s),
        )

        # Full rear skull, then the face plane.  Bob faces screen-right.  The
        # haircut owns the rear volume while the face carries a clear brow,
        # nose, cheek, and jaw; neither shape is a shrunken profile cutout.
        rear_hair = [
            (cx - 10.7 * hs, cy + 5.8 * hs),
            (cx - 11.4 * hs, cy - 2.5 * hs),
            (cx - 8.8 * hs, cy - 9.8 * hs),
            (cx - 3.2 * hs, cy - 14.0 * hs),
            (cx + 3.8 * hs, cy - 13.5 * hs),
            (cx + 7.6 * hs, cy - 9.3 * hs),
            (cx + 6.0 * hs, cy - 5.8 * hs),
            (cx + 1.6 * hs, cy - 7.0 * hs),
            (cx - 2.1 * hs, cy - 5.0 * hs),
            (cx - 5.9 * hs, cy - 2.2 * hs),
            (cx - 6.4 * hs, cy + 6.1 * hs),
            (cx - 8.7 * hs, cy + 9.3 * hs),
        ]
        _poly(
            d,
            rear_hair,
            fill=pal["hair"],
            outline=outline,
            width=round(1.0 * s),
        )
        face = [
            (cx - 6.9 * hs, cy - 9.0 * hs),
            (cx + 5.7 * hs, cy - 8.1 * hs),
            (cx + 8.2 * hs, cy - 2.6 * hs),
            (cx + 11.7 * hs, cy + 0.1 * hs),
            (cx + 8.4 * hs, cy + 2.7 * hs),
            (cx + 8.9 * hs, cy + 6.2 * hs),
            (cx + 4.1 * hs, cy + 10.5 * hs),
            (cx - 4.9 * hs, cy + 8.3 * hs),
            (cx - 7.3 * hs, cy + 0.5 * hs),
        ]
        _poly(d, face, fill=pal["skin"], outline=outline, width=round(1.0 * s))
        _ellipse(
            d,
            _bbox(cx - 5.4 * hs, cy + 0.7 * hs, 3.9 * hs, 5.8 * hs),
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.65 * s),
        )

        # Hairline and crown tufts drape over the face plane while preserving
        # enough forehead to keep the larger head readable.
        fringe = [
            (cx - 9.1 * hs, cy - 9.8 * hs),
            (cx + 5.7 * hs, cy - 10.3 * hs),
            (cx + 2.7 * hs, cy - 4.4 * hs),
            (cx - 1.5 * hs, cy - 6.4 * hs),
            (cx - 5.9 * hs, cy - 3.7 * hs),
        ]
        d.polygon([(round(x), round(y)) for x, y in fringe], fill=pal["hair"])
        _line(
            d,
            [fringe[1], fringe[2], fringe[3], fringe[4]],
            fill=outline,
            width=round(0.9 * s),
        )
        _poly(
            d,
            [
                (cx - 4.6 * hs, cy - 11.9 * hs),
                (cx + 0.5 * hs, cy - 14.6 * hs),
                (cx + 1.6 * hs, cy - 8.2 * hs),
            ],
            fill=pal["hair_mid"],
            outline=outline,
            width=round(0.6 * s),
        )
        _line(
            d,
            [(cx - 3.9 * hs, cy - 11.1 * hs), (cx + 3.1 * hs, cy - 10.1 * hs)],
            fill=pal["hair_light"],
            width=round(1.0 * s),
        )

        # Profile safety glasses rest on the forehead.
        _line(
            d,
            [(cx - 7.1 * hs, cy - 7.2 * hs), (cx + 5.2 * hs, cy - 7.8 * hs)],
            fill=pal["leather_dark"],
            width=round(1.2 * s),
        )
        _rounded(
            d,
            (cx - 0.5 * hs, cy - 10.0 * hs, cx + 5.4 * hs, cy - 5.6 * hs),
            radius=1.3 * s,
            fill=pal["glass"],
            outline=outline,
            width=round(0.7 * s),
        )
        _line(
            d,
            [(cx + 0.6 * hs, cy - 9.1 * hs), (cx + 4.0 * hs, cy - 6.5 * hs)],
            fill=pal["white"],
            width=round(0.5 * s),
        )

        # The beard is part of the jaw silhouette, not a floating patch.  Its
        # lower contour shares the face's chin point exactly and is outlined as
        # one continuous form.
        beard = [
            (cx - 5.0 * hs, cy + 2.4 * hs),
            (cx + 0.4 * hs, cy + 4.5 * hs),
            (cx + 7.0 * hs, cy + 3.8 * hs),
            (cx + 7.3 * hs, cy + 7.2 * hs),
            (cx + 4.1 * hs, cy + 10.5 * hs),
            (cx - 2.7 * hs, cy + 9.2 * hs),
            (cx - 5.4 * hs, cy + 6.1 * hs),
        ]
        _poly(
            d,
            beard,
            fill=pal["beard"],
            outline=outline,
            width=round(0.75 * s),
        )
        _line(
            d,
            [beard[0], beard[1], beard[2]],
            fill=pal["beard_dark"],
            width=round(0.7 * s),
        )

        eye = (cx + 4.3 * hs, cy - 0.8 * hs)
        if pose.blink:
            _line(
                d,
                [(eye[0] - 1.5 * hs, eye[1]), (eye[0] + 1.7 * hs, eye[1])],
                fill=outline,
                width=round(1.0 * s),
            )
        else:
            _ellipse(
                d,
                _bbox(eye[0], eye[1], 3.0 * hs, 3.4 * hs),
                fill=pal["white"],
                outline=outline,
                width=round(0.65 * s),
            )
            _ellipse(
                d,
                _bbox(eye[0] + 0.5 * hs, eye[1], 1.4 * hs, 1.7 * hs),
                fill=pal["eye"],
            )
        _line(
            d,
            [(cx + 1.9 * hs, cy - 3.2 * hs), (cx + 6.2 * hs, cy - 2.8 * hs)],
            fill=pal["hair"],
            width=round(1.0 * s),
        )
        _line(
            d,
            [(cx + 6.7 * hs, cy + 5.6 * hs), (cx + 9.2 * hs, cy + 5.3 * hs)],
            fill=outline,
            width=round(0.9 * s),
        )
