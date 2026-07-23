"""Bespoke procedural sprite generator for Erdish, the wandering mathematician.

Erdish used to be a ``toon_side`` preset.  That shared rig made him read as a
generic mannequin with an elderly palette: round featureless head, capsule
limbs, a floating satchel, and the same reach pose in every animation.  This
renderer gives him a character-specific construction inspired by the visual
language of an eccentric twentieth-century mathematician:

* a long, narrow, elderly face with a prominent nose and enormous round glasses;
* a connected swept-white hair mass with unruly side wisps;
* a very slim body inside an oversized blue-gray jacket and cream shirt;
* a slight forward stoop that stays energetic rather than infirm;
* expressive empty-hand gestures for talk and interact animations;
* a complete prop-free traversal set for player control: run, jump, fall,
  crouch/crawl, dash, slide, dodge roll, wall movement, ledge movement,
  climbing, swimming, blocking, hit reaction, and defeat.

The sprite is a *base character* sheet.  It deliberately renders no held item,
satchel, paper, notebook, chalk, particles, floor ellipse, or drop shadow.  All
geometry is authored in Python/Pillow.  Limbs are built as overlapping tapered
segments under a shoulder cap / cuff / hand, so every pose remains a single
logically connected character rather than a collection of floating pieces.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

from PIL import Image, ImageDraw

from ...profiling import profile
from ...authoring.generator import CharacterGenerator
from ...core.draw import rgba
from ...registry import CharacterJob
from ambition_sprite2d_renderer.core.draw import blending_draw

Color = Tuple[int, int, int, int]
Point = Tuple[float, float]


def _parse_background(value: str) -> Optional[Color]:
    return None if str(value).lower() == "transparent" else rgba(str(value))


def _mix(a: Color, b: Color, amount: float) -> Color:
    amount = max(0.0, min(1.0, amount))
    return tuple(
        int(round(a[i] * (1.0 - amount) + b[i] * amount)) for i in range(4)
    )  # type: ignore[return-value]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smoothstep(value: float) -> float:
    value = _clamp01(value)
    return value * value * (3.0 - 2.0 * value)


def _lerp(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def _lerp_point(a: Point, b: Point, amount: float) -> Point:
    return (_lerp(a[0], b[0], amount), _lerp(a[1], b[1], amount))


def _add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def _scale_point(p: Point, scale: float) -> Point:
    return (p[0] * scale, p[1] * scale)


def _poly(points: Iterable[Point], scale: float) -> list[Point]:
    return [_scale_point(point, scale) for point in points]


def _bbox(center: Point, rx: float, ry: float, scale: float) -> Tuple[float, float, float, float]:
    cx, cy = center
    return (
        (cx - rx) * scale,
        (cy - ry) * scale,
        (cx + rx) * scale,
        (cy + ry) * scale,
    )


def _unit_segment(a: Point, b: Point) -> Tuple[Point, Point, float]:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = max(1.0e-6, math.hypot(dx, dy))
    along = (dx / length, dy / length)
    normal = (-along[1], along[0])
    return along, normal, length



def _bent_tube(
    draw: ImageDraw.ImageDraw,
    start: Point,
    bend: Point,
    end: Point,
    radii: Tuple[float, float, float],
    *,
    fill: Color,
    outline: Color,
    scale: float,
    outline_width: float = 1.25,
) -> None:
    """Draw a single connected bent tube without a visible elbow disc."""
    _, n1, _ = _unit_segment(start, bend)
    _, n2, _ = _unit_segment(bend, end)
    avg = (n1[0] + n2[0], n1[1] + n2[1])
    avg_len = max(1.0e-6, math.hypot(*avg))
    nm = (avg[0] / avg_len, avg[1] / avg_len)
    r0, r1, r2 = radii
    points = [
        (start[0] + n1[0] * r0, start[1] + n1[1] * r0),
        (bend[0] + nm[0] * r1, bend[1] + nm[1] * r1),
        (end[0] + n2[0] * r2, end[1] + n2[1] * r2),
        (end[0] - n2[0] * r2, end[1] - n2[1] * r2),
        (bend[0] - nm[0] * r1, bend[1] - nm[1] * r1),
        (start[0] - n1[0] * r0, start[1] - n1[1] * r0),
    ]
    width = max(1, round(outline_width * scale))
    draw.polygon(_poly(points, scale), fill=fill, outline=outline, width=width)
    draw.ellipse(_bbox(start, r0, r0, scale), fill=fill, outline=outline, width=width)
    draw.ellipse(_bbox(end, r2, r2, scale), fill=fill, outline=outline, width=width)


def _rotate(point: Point, origin: Point, degrees: float) -> Point:
    radians = math.radians(degrees)
    c = math.cos(radians)
    s = math.sin(radians)
    x = point[0] - origin[0]
    y = point[1] - origin[1]
    return (origin[0] + x * c - y * s, origin[1] + x * s + y * c)


PALETTE: Dict[str, Color] = {
    "outline": rgba("#111619"),
    "outline_soft": rgba("#263238"),
    "skin": rgba("#D8B99E"),
    "skin_light": rgba("#EBCFB5"),
    "skin_shadow": rgba("#AE8972"),
    "hair": rgba("#E7E5DF"),
    "hair_light": rgba("#FBFAF4"),
    "hair_shadow": rgba("#A8ADB0"),
    "jacket": rgba("#657C82"),
    "jacket_light": rgba("#80979B"),
    "jacket_dark": rgba("#3D5359"),
    "shirt": rgba("#E8DCC7"),
    "shirt_shadow": rgba("#BBAE98"),
    "trouser": rgba("#26383E"),
    "trouser_light": rgba("#394D52"),
    "shoe": rgba("#4B342B"),
    "shoe_light": rgba("#6B4A3B"),
    "glass": rgba("#F5F2E8", 72),
    "eye": rgba("#222729"),
    "mouth": rgba("#5B2E2A"),
    "button": rgba("#29383C"),
}


@dataclass(frozen=True)
class ErdishSpec:
    target: str
    seed: int
    archetype: str
    name: str
    role: str
    palette_name: str
    head_width: float = 24.5
    head_height: float = 31.0
    shoulder_width: float = 28.0
    jacket_height: float = 39.0
    hip_width: float = 14.0
    upper_arm: float = 16.0
    lower_arm: float = 15.5
    upper_leg: float = 20.0
    lower_leg: float = 20.5
    hair_volume: float = 7.5


@dataclass
class ErdishPose:
    bob: float = 0.0
    lean_x: float = 0.0
    root_y: float = 0.0
    body_y: float = 0.0
    jacket_scale: float = 1.0
    rotation: float = 0.0
    rotation_pivot: Point = (64.0, 88.0)
    head_x: float = 0.0
    head_y: float = 0.0
    head_tilt: float = 0.0
    blink: bool = False
    mouth_open: float = 0.0
    mouth_smile: float = 0.0
    brow_lift: float = 0.0
    near_shoulder: Point = (0.0, 0.0)
    near_elbow: Point = (0.0, 0.0)
    near_hand: Point = (0.0, 0.0)
    near_palm: str = "relaxed"
    far_shoulder: Point = (0.0, 0.0)
    far_elbow: Point = (0.0, 0.0)
    far_hand: Point = (0.0, 0.0)
    far_palm: str = "relaxed"
    near_hip: Point = (0.0, 0.0)
    near_knee: Point = (0.0, 0.0)
    near_ankle: Point = (0.0, 0.0)
    far_hip: Point = (0.0, 0.0)
    far_knee: Point = (0.0, 0.0)
    far_ankle: Point = (0.0, 0.0)


class ErdishScholarGenerator(CharacterGenerator):
    """Character-specific base-pose renderer for Erdish."""

    target = "erdish_scholar"
    name = "erdish_scholar"
    applies_job_name = True
    USES_DROP_SHADOW = False
    USES_PROPS = False

    ANIMATIONS: Dict[str, Dict[str, int]] = {
        "idle": {"frames": 8, "duration_ms": 145},
        "walk": {"frames": 8, "duration_ms": 105},
        "run": {"frames": 8, "duration_ms": 78},
        "crouch": {"frames": 6, "duration_ms": 95},
        "crouch_walk": {"frames": 8, "duration_ms": 88},
        "jump": {"frames": 6, "duration_ms": 95},
        "fall": {"frames": 6, "duration_ms": 95},
        "dash_startup": {"frames": 4, "duration_ms": 50},
        "dash": {"frames": 6, "duration_ms": 65},
        "slide": {"frames": 6, "duration_ms": 70},
        "roll": {"frames": 8, "duration_ms": 58},
        "wall_grab": {"frames": 6, "duration_ms": 110},
        "wall_jump": {"frames": 6, "duration_ms": 85},
        "ledge_grab": {"frames": 6, "duration_ms": 100},
        "ledge_climb": {"frames": 6, "duration_ms": 100},
        "ledge_getup": {"frames": 6, "duration_ms": 40},
        "ledge_roll": {"frames": 8, "duration_ms": 37},
        "climb": {"frames": 8, "duration_ms": 100},
        "swim": {"frames": 8, "duration_ms": 105},
        "block": {"frames": 6, "duration_ms": 85},
        "hit": {"frames": 5, "duration_ms": 90},
        "death": {"frames": 8, "duration_ms": 110},
        "talk": {"frames": 8, "duration_ms": 105},
        "interact": {"frames": 8, "duration_ms": 95},
    }

    def canonical_pose(self) -> Tuple[str, int]:
        return ("idle", 1)

    def build_spec(self, job: CharacterJob) -> ErdishSpec:
        if job.archetype != "erdish":
            raise KeyError(
                "erdish_scholar ships only the existing 'erdish' archetype; "
                f"got {job.archetype!r}"
            )
        if job.held_item:
            raise ValueError("Erdish base poses do not accept held_item / prop authoring")
        return ErdishSpec(
            target=self.name,
            seed=job.seed,
            archetype=job.archetype,
            name="Erdish",
            role="npc",
            palette_name="erdish",
        )

    @profile
    def render_frame(
        self,
        spec: ErdishSpec,
        animation: str,
        frame_index: int,
        size: Tuple[int, int],
        job: CharacterJob,
    ) -> Image.Image:
        animation_info = self.animations()[animation]
        return self.render_animation_frame(
            spec,
            animation,
            frame_index % animation_info["frames"],
            animation_info["frames"],
            size,
            background=_parse_background(job.render.background),
            supersample=job.render.supersample,
            downsample=job.render.downsample,
        )

    def body_inset(self) -> Dict[str, float]:
        # Large hair and gesturing hands are visual silhouette, not collision.
        return {"left": 0.15, "right": 0.15, "top": 0.02, "bottom": 0.02}

    # ------------------------------------------------------------------ pose

    def pose_for_animation(
        self,
        animation: str,
        frame_index: int,
        frame_count: int,
    ) -> ErdishPose:
        phase = frame_index / float(frame_count)
        t = 0.0 if frame_count <= 1 else frame_index / float(frame_count - 1)
        wave = math.sin(phase * math.tau)
        cosine = math.cos(phase * math.tau)
        p = ErdishPose()

        def standing_legs() -> None:
            p.near_hip = (70.0, 87.0)
            p.near_knee = (71.0, 101.5)
            p.near_ankle = (72.5, 118.0)
            p.far_hip = (58.0, 87.0)
            p.far_knee = (57.5, 102.0)
            p.far_ankle = (55.5, 118.0)

        def relaxed_arms() -> None:
            p.near_shoulder = (78.0, 57.0)
            p.near_elbow = (84.0, 75.0)
            p.near_hand = (83.0, 94.0)
            p.far_shoulder = (51.5, 58.0)
            p.far_elbow = (48.0, 76.0)
            p.far_hand = (50.0, 95.0)

        relaxed_arms()
        standing_legs()

        if animation == "idle":
            p.bob = -0.55 * max(0.0, wave)
            p.head_y = wave * 0.35
            p.head_x = cosine * 0.22
            p.head_tilt = wave * 0.8
            p.mouth_smile = 0.25
            p.brow_lift = 0.15 * cosine
            p.blink = frame_index == 6
            adjust = max(0.0, math.sin((phase - 0.37) * math.tau)) ** 3
            p.near_elbow = (84.0 - 7.0 * adjust, 75.0 - 9.0 * adjust)
            p.near_hand = (83.0 - 10.0 * adjust, 94.0 - 47.0 * adjust)
            p.near_palm = "pinch" if adjust > 0.35 else "relaxed"

        elif animation in {"walk", "run"}:
            stride = wave
            running = animation == "run"
            gait = 1.0 if not running else 1.45
            p.bob = -(1.0 if not running else 1.7) * abs(cosine)
            p.lean_x = 1.0 if not running else 2.2
            p.head_x = 0.6 if not running else 1.1
            p.head_y = -0.25 * abs(cosine)
            p.head_tilt = (-1.0 if not running else -2.2) + wave * 0.55
            p.mouth_smile = 0.2
            p.blink = frame_index == 7
            p.near_elbow = (82.0 - 5.0 * stride * gait, 74.0)
            p.near_hand = (84.0 - 9.5 * stride * gait, 92.0)
            p.far_elbow = (47.5 + 5.0 * stride * gait, 75.0)
            p.far_hand = (47.0 + 9.0 * stride * gait, 93.0)
            near_lift = max(0.0, -cosine) * (3.0 if not running else 6.0)
            far_lift = max(0.0, cosine) * (3.0 if not running else 6.0)
            p.near_knee = (70.5 + 6.5 * stride * gait, 101.0 - near_lift * 0.35)
            p.near_ankle = (72.0 + 10.0 * stride * gait, 118.0 - near_lift)
            p.far_knee = (58.0 - 6.5 * stride * gait, 101.5 - far_lift * 0.35)
            p.far_ankle = (56.0 - 10.0 * stride * gait, 118.0 - far_lift)

        elif animation in {"crouch", "crouch_walk"}:
            moving = animation == "crouch_walk"
            stride = wave if moving else 0.0
            pulse = 0.04 * wave if not moving else 0.0
            p.body_y = 8.5 + pulse
            p.jacket_scale = 0.79
            p.head_y = 11.0 + pulse
            p.head_x = 1.0
            p.head_tilt = -2.0 + 0.5 * stride
            p.near_shoulder = (78.0, 65.0)
            p.far_shoulder = (52.0, 66.0)
            p.near_elbow = (86.0 + 3.0 * stride, 78.0)
            p.near_hand = (91.0 + 5.0 * stride, 91.0)
            p.far_elbow = (47.0 - 3.0 * stride, 79.0)
            p.far_hand = (44.0 - 5.0 * stride, 92.0)
            p.near_hip = (69.0, 94.0)
            p.far_hip = (58.0, 94.0)
            p.near_knee = (77.0 + 5.0 * stride, 104.0)
            p.near_ankle = (82.0 + 7.0 * stride, 118.0)
            p.far_knee = (53.0 - 5.0 * stride, 104.0)
            p.far_ankle = (48.0 - 7.0 * stride, 118.0)

        elif animation == "jump":
            preload = 1.0 - _smoothstep(t / 0.28)
            rise = _smoothstep((t - 0.10) / 0.50)
            p.root_y = 4.0 * preload - 6.0 * rise
            p.body_y = 4.0 * preload
            p.jacket_scale = 1.0 - 0.12 * preload
            p.head_y = 4.5 * preload
            p.head_tilt = -2.0 - 1.5 * rise
            p.near_elbow = (84.0, 70.0 - 7.0 * rise)
            p.near_hand = (91.0, 86.0 - 16.0 * rise)
            p.far_elbow = (46.0, 73.0 - 4.0 * rise)
            p.far_hand = (42.0, 90.0 - 12.0 * rise)
            p.near_knee = (76.0, 99.0 - 2.0 * rise)
            p.near_ankle = (80.0, 112.0 - 6.0 * rise)
            p.far_knee = (54.0, 101.0 - 3.0 * rise)
            p.far_ankle = (50.0, 114.0 - 8.0 * rise)

        elif animation == "fall":
            p.root_y = -6.0 + 4.0 * t
            p.head_tilt = 2.0 + 2.0 * t
            p.mouth_open = 0.18
            p.near_elbow = (88.0, 69.0)
            p.near_hand = (97.0, 78.0)
            p.near_palm = "open"
            p.far_elbow = (43.0, 70.0)
            p.far_hand = (34.0, 79.0)
            p.far_palm = "open"
            p.near_knee = (76.0, 100.0)
            p.near_ankle = (80.0, 112.0)
            p.far_knee = (53.0, 101.0)
            p.far_ankle = (49.0, 113.0)

        elif animation in {"land_hard", "land_recovery"}:
            if animation == "land_hard":
                impact = math.sin(math.pi * _clamp01(t / 0.78))
                p.root_y = -7.0 * (1.0 - _smoothstep(t / 0.36))
            else:
                impact = 1.0 - _smoothstep(t)
            p.body_y = 10.5 * impact
            p.jacket_scale = 1.0 - 0.22 * impact
            p.head_y = 12.0 * impact
            p.head_tilt = -4.0 * impact
            p.near_shoulder = (78.0, 57.0 + 8.0 * impact)
            p.far_shoulder = (51.5, 58.0 + 8.0 * impact)
            p.near_elbow = (87.0, 76.0 + 3.0 * impact)
            p.near_hand = (94.0, 94.0 + 2.0 * impact)
            p.far_elbow = (45.0, 77.0 + 3.0 * impact)
            p.far_hand = (39.0, 94.0 + 2.0 * impact)
            p.near_hip = (69.0, 88.0 + 5.0 * impact)
            p.far_hip = (58.0, 88.0 + 5.0 * impact)
            p.near_knee = (77.0, 104.0)
            p.near_ankle = (82.0, 118.0)
            p.far_knee = (52.0, 104.0)
            p.far_ankle = (47.0, 118.0)

        elif animation in {"dash_startup", "dash"}:
            charge = _smoothstep(t)
            startup = animation == "dash_startup"
            p.body_y = (7.0 * charge if startup else 3.5)
            p.jacket_scale = (1.0 - 0.16 * charge if startup else 0.92)
            p.head_y = (8.0 * charge if startup else 4.0)
            p.lean_x = (-2.5 * charge if startup else -1.5 + 4.0 * t)
            p.head_tilt = -5.0 - 3.0 * charge
            p.near_elbow = (71.0, 73.0)
            p.near_hand = (62.0, 88.0)
            p.far_elbow = (44.0, 71.0)
            p.far_hand = (34.0, 84.0)
            p.near_knee = (78.0 + 5.0 * charge, 101.0)
            p.near_ankle = (88.0 + 8.0 * charge, 118.0)
            p.far_knee = (54.0 - 5.0 * charge, 102.0)
            p.far_ankle = (45.0 - 8.0 * charge, 118.0)

        elif animation == "slide":
            p.body_y = 13.0
            p.jacket_scale = 0.68
            p.head_y = 17.0
            p.head_tilt = -8.0
            p.lean_x = -2.0 + 5.0 * t
            p.near_shoulder = (78.0, 69.0)
            p.far_shoulder = (52.0, 70.0)
            p.near_elbow = (72.0, 82.0)
            p.near_hand = (64.0, 92.0)
            p.far_elbow = (47.0, 82.0)
            p.far_hand = (41.0, 94.0)
            p.near_hip = (71.0, 96.0)
            p.far_hip = (58.0, 96.0)
            p.near_knee = (84.0, 104.0)
            p.near_ankle = (96.0, 116.0)
            p.far_knee = (50.0, 105.0)
            p.far_ankle = (39.0, 118.0)

        elif animation == "roll":
            p.body_y = 13.5
            p.jacket_scale = 0.67
            p.head_y = 17.0
            p.head_tilt = -5.0
            p.lean_x = -7.0 + 14.0 * t
            p.root_y = -2.0 * math.sin(math.pi * t)
            p.rotation = -360.0 * t
            p.rotation_pivot = (64.0, 78.0)
            p.near_shoulder = (77.0, 69.0)
            p.far_shoulder = (53.0, 70.0)
            p.near_elbow = (78.0, 83.0)
            p.near_hand = (72.0, 94.0)
            p.far_elbow = (51.0, 84.0)
            p.far_hand = (56.0, 95.0)
            p.near_hip = (70.0, 96.0)
            p.far_hip = (58.0, 96.0)
            p.near_knee = (77.0, 104.0)
            p.near_ankle = (79.0, 113.0)
            p.far_knee = (52.0, 104.0)
            p.far_ankle = (50.0, 113.0)

        elif animation == "wall_grab":
            p.root_y = -4.0 + 0.6 * wave
            p.lean_x = 3.0
            p.head_x = 1.5
            p.head_tilt = 3.0
            p.near_elbow = (91.0, 48.0)
            p.near_hand = (103.0, 38.0)
            p.near_palm = "press"
            p.far_elbow = (78.0, 48.0)
            p.far_hand = (99.0, 45.0)
            p.far_palm = "press"
            p.near_knee = (77.0, 98.0)
            p.near_ankle = (88.0, 108.0)
            p.far_knee = (59.0, 101.0)
            p.far_ankle = (83.0, 116.0)

        elif animation == "wall_jump":
            spring = _smoothstep(t)
            p.lean_x = 8.0 - 15.0 * spring
            p.root_y = -3.0 - 3.0 * math.sin(math.pi * t)
            p.head_tilt = 5.0 - 11.0 * spring
            p.near_elbow = _lerp_point((91.0, 51.0), (72.0, 66.0), spring)
            p.near_hand = _lerp_point((103.0, 43.0), (58.0, 75.0), spring)
            p.near_palm = "press" if spring < 0.4 else "open"
            p.far_elbow = _lerp_point((78.0, 53.0), (43.0, 68.0), spring)
            p.far_hand = _lerp_point((98.0, 49.0), (32.0, 79.0), spring)
            p.far_palm = "press" if spring < 0.4 else "open"
            p.near_knee = (77.0 - 7.0 * spring, 99.0)
            p.near_ankle = (88.0 - 15.0 * spring, 108.0)
            p.far_knee = (60.0 - 5.0 * spring, 101.0)
            p.far_ankle = (82.0 - 18.0 * spring, 115.0)

        elif animation == "ledge_grab":
            p.root_y = 5.0 + 0.8 * wave
            p.head_y = 2.0
            p.head_tilt = -1.0 + 0.6 * wave
            p.near_shoulder = (77.0, 58.0)
            p.far_shoulder = (52.0, 59.0)
            p.near_elbow = (78.0, 37.0)
            p.near_hand = (72.0, 16.0)
            p.near_palm = "press"
            p.far_elbow = (55.0, 38.0)
            p.far_hand = (58.0, 16.0)
            p.far_palm = "press"
            p.near_knee = (76.0, 102.0)
            p.near_ankle = (82.0, 108.0)
            p.far_knee = (54.0, 101.0)
            p.far_ankle = (48.0, 107.0)

        elif animation in {"ledge_climb", "ledge_getup"}:
            climb = _smoothstep(t)
            p.root_y = 6.0 - 9.0 * climb
            p.body_y = 6.0 * (1.0 - climb)
            p.jacket_scale = 0.84 + 0.16 * climb
            p.head_y = 7.0 * (1.0 - climb)
            p.head_tilt = -3.0 + 3.0 * climb
            p.near_shoulder = _lerp_point((77.0, 63.0), (78.0, 57.0), climb)
            p.far_shoulder = _lerp_point((52.0, 64.0), (51.5, 58.0), climb)
            p.near_elbow = _lerp_point((78.0, 39.0), (88.0, 75.0), climb)
            p.near_hand = _lerp_point((72.0, 16.0), (93.0, 91.0), climb)
            p.near_palm = "press"
            p.far_elbow = _lerp_point((55.0, 40.0), (44.0, 76.0), climb)
            p.far_hand = _lerp_point((58.0, 16.0), (39.0, 91.0), climb)
            p.far_palm = "press"
            p.near_hip = _lerp_point((70.0, 94.0), (70.0, 87.0), climb)
            p.far_hip = _lerp_point((58.0, 94.0), (58.0, 87.0), climb)
            p.near_knee = _lerp_point((76.0, 105.0), (71.0, 101.5), climb)
            p.near_ankle = _lerp_point((82.0, 109.0), (72.5, 118.0), climb)
            p.far_knee = _lerp_point((54.0, 104.0), (57.5, 102.0), climb)
            p.far_ankle = _lerp_point((48.0, 108.0), (55.5, 118.0), climb)

        elif animation == "ledge_roll":
            roll = _smoothstep((t - 0.12) / 0.88)
            p.root_y = 5.0 * (1.0 - roll) - 2.0 * math.sin(math.pi * roll) - 5.5 * roll
            p.body_y = _lerp(5.0, 13.5, roll)
            p.jacket_scale = _lerp(0.86, 0.67, roll)
            p.head_y = _lerp(6.0, 17.0, roll)
            p.head_tilt = _lerp(-2.0, -5.0, roll)
            p.lean_x = -4.0 + 9.0 * roll
            p.rotation = -360.0 * roll
            p.rotation_pivot = (64.0, 72.0)
            p.near_shoulder = _lerp_point((77.0, 62.0), (77.0, 69.0), roll)
            p.far_shoulder = _lerp_point((52.0, 63.0), (53.0, 70.0), roll)
            p.near_elbow = _lerp_point((78.0, 39.0), (78.0, 83.0), roll)
            p.near_hand = _lerp_point((72.0, 16.0), (72.0, 94.0), roll)
            p.near_palm = "press"
            p.far_elbow = _lerp_point((55.0, 40.0), (51.0, 84.0), roll)
            p.far_hand = _lerp_point((58.0, 16.0), (56.0, 95.0), roll)
            p.far_palm = "press"
            p.near_hip = _lerp_point((70.0, 94.0), (70.0, 96.0), roll)
            p.far_hip = _lerp_point((58.0, 94.0), (58.0, 96.0), roll)
            p.near_knee = _lerp_point((76.0, 105.0), (77.0, 104.0), roll)
            p.near_ankle = _lerp_point((82.0, 109.0), (79.0, 111.0), roll)
            p.far_knee = _lerp_point((54.0, 104.0), (52.0, 104.0), roll)
            p.far_ankle = _lerp_point((48.0, 108.0), (50.0, 111.0), roll)

        elif animation == "climb":
            alternate = wave
            p.root_y = -4.0 + 1.2 * cosine
            p.head_tilt = 1.5 * alternate
            p.near_elbow = (80.0, 45.0 + 9.0 * alternate)
            p.near_hand = (79.0, 29.0 + 12.0 * alternate)
            p.near_palm = "press"
            p.far_elbow = (50.0, 47.0 - 9.0 * alternate)
            p.far_hand = (51.0, 31.0 - 12.0 * alternate)
            p.far_palm = "press"
            p.near_knee = (75.0, 98.0 - 5.0 * alternate)
            p.near_ankle = (81.0, 111.0 - 9.0 * alternate)
            p.far_knee = (54.0, 100.0 + 5.0 * alternate)
            p.far_ankle = (48.0, 113.0 + 6.0 * alternate)

        elif animation == "swim":
            stroke = wave
            p.root_y = -4.0 + 1.2 * cosine
            p.rotation = -56.0 + 3.0 * wave
            p.rotation_pivot = (64.0, 76.0)
            p.head_tilt = -2.0
            p.near_elbow = (84.0 + 4.0 * stroke, 68.0)
            p.near_hand = (93.0 + 5.0 * stroke, 75.0)
            p.near_palm = "open"
            p.far_elbow = (46.0 - 4.0 * stroke, 69.0)
            p.far_hand = (37.0 - 5.0 * stroke, 76.0)
            p.far_palm = "open"
            p.near_knee = (76.0 - 4.0 * stroke, 100.0)
            p.near_ankle = (80.0 - 5.0 * stroke, 110.0)
            p.far_knee = (53.0 + 4.0 * stroke, 101.0)
            p.far_ankle = (49.0 + 5.0 * stroke, 111.0)

        elif animation == "block":
            brace = 0.25 + 0.75 * math.sin(math.pi * t)
            p.body_y = 3.0 * brace
            p.jacket_scale = 1.0 - 0.06 * brace
            p.head_y = 3.0 * brace
            p.head_tilt = -2.0 * brace
            p.near_elbow = (82.0, 67.0)
            p.near_hand = (65.0, 72.0)
            p.near_palm = "press"
            p.far_elbow = (48.0, 67.0)
            p.far_hand = (65.0, 79.0)
            p.far_palm = "press"
            p.near_knee = (74.0, 101.0)
            p.near_ankle = (77.0, 118.0)
            p.far_knee = (56.0, 102.0)
            p.far_ankle = (52.0, 118.0)

        elif animation == "hit":
            recoil = math.sin(math.pi * t)
            p.lean_x = -5.0 * recoil
            p.root_y = -2.0 * recoil
            p.head_tilt = 12.0 * recoil
            p.mouth_open = 0.8 * recoil
            p.brow_lift = 0.8 * recoil
            p.near_elbow = (73.0, 69.0)
            p.near_hand = (64.0, 79.0)
            p.far_elbow = (43.0, 70.0)
            p.far_hand = (33.0, 81.0)
            p.near_knee = (75.0, 101.0)
            p.near_ankle = (80.0, 117.0)
            p.far_knee = (55.0, 102.0)
            p.far_ankle = (50.0, 118.0)

        elif animation == "death":
            collapse = _smoothstep(t)
            p.lean_x = 8.0 * collapse
            p.root_y = -6.0 * collapse
            p.body_y = 5.0 * collapse
            p.jacket_scale = 1.0 - 0.14 * collapse
            p.head_y = 5.0 * collapse
            p.head_tilt = 6.0 * collapse
            p.rotation = 82.0 * collapse
            p.rotation_pivot = (64.0, 80.0)
            p.near_elbow = (78.0, 78.0)
            p.near_hand = (70.0, 94.0)
            p.far_elbow = (49.0, 78.0)
            p.far_hand = (55.0, 95.0)
            p.near_knee = (76.0, 103.0)
            p.near_ankle = (79.0, 116.0)
            p.far_knee = (53.0, 103.0)
            p.far_ankle = (50.0, 116.0)

        elif animation == "talk":
            gesture = 0.5 - 0.5 * math.cos(phase * math.tau)
            counter = 0.5 + 0.5 * math.sin((phase + 0.18) * math.tau)
            p.bob = -0.35 * gesture
            p.head_x = -0.45 + gesture * 0.9
            p.head_y = -gesture * 0.25
            p.head_tilt = -1.2 + gesture * 2.4
            p.mouth_open = 0.28 + 0.72 * max(0.0, math.sin((phase + 0.08) * math.tau))
            p.mouth_smile = 0.45
            p.brow_lift = 0.65 * counter
            p.blink = frame_index == 6
            p.near_elbow = (85.0 + 3.0 * gesture, 71.0 - 4.0 * gesture)
            p.near_hand = (91.0 + 12.0 * gesture, 76.0 - 13.0 * gesture)
            p.near_palm = "open" if gesture > 0.25 else "relaxed"
            p.far_elbow = (45.0 - 2.0 * counter, 72.0 - 5.0 * counter)
            p.far_hand = (40.0 - 8.0 * counter, 80.0 - 12.0 * counter)
            p.far_palm = "open" if counter > 0.25 else "relaxed"

        elif animation == "interact":
            reach = math.sin(phase * math.pi) ** 1.25
            settle = math.sin(phase * math.tau)
            p.bob = -0.5 * reach
            p.lean_x = 2.8 * reach
            p.head_x = 2.0 * reach
            p.head_y = 0.5 * reach
            p.head_tilt = -1.5 * reach
            p.mouth_open = 0.25 * reach
            p.mouth_smile = 0.2
            p.brow_lift = 0.55 * reach
            p.blink = frame_index == 7
            p.near_elbow = (87.0 + 7.0 * reach, 69.0 - 2.5 * reach)
            p.near_hand = (88.0 + 25.0 * reach, 86.0 - 18.0 * reach)
            p.near_palm = "press" if reach > 0.35 else "relaxed"
            p.far_elbow = (47.0 - 2.0 * reach, 75.0)
            p.far_hand = (48.0 - 4.0 * reach, 94.0 - 3.0 * reach)
            p.near_knee = (71.0 + 2.0 * reach, 101.0)
            p.near_ankle = (73.0 + 3.0 * reach, 118.0)
            p.far_knee = (57.5 + settle * 0.5, 102.0)

        else:  # pragma: no cover - the sheet validates animation names first.
            raise KeyError(animation)

        return p

    # --------------------------------------------------------------- rendering

    @profile
    def render_animation_frame(
        self,
        spec: ErdishSpec,
        animation: str,
        frame_index: int,
        frame_count: int,
        size: Tuple[int, int],
        *,
        background: Optional[Color] = None,
        supersample: int = 4,
        downsample: str = "lanczos",
    ) -> Image.Image:
        width, height = size
        ss = max(1, int(supersample))
        canvas = Image.new(
            "RGBA",
            (width * ss, height * ss),
            background or (0, 0, 0, 0),
        )
        # Design space is always 128 x 128; render_scale and supersampling both
        # become one scalar.  This keeps proportions invariant at every output
        # resolution while retaining clean antialiased diagonals.
        scale = (width / 128.0) * ss
        pose = self.pose_for_animation(animation, frame_index, frame_count)
        character = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        self._draw_character(character, spec, pose, scale)
        if abs(pose.rotation) > 1.0e-6:
            pivot = (
                (pose.rotation_pivot[0] + pose.lean_x) * scale,
                (pose.rotation_pivot[1] + pose.root_y) * scale,
            )
            character = character.rotate(
                pose.rotation,
                resample=Image.Resampling.BICUBIC,
                center=pivot,
                expand=False,
            )
        canvas.alpha_composite(character)

        if ss > 1:
            resample = Image.Resampling.LANCZOS
            if str(downsample).lower() in {"nearest", "none"}:
                resample = Image.Resampling.NEAREST
            canvas = canvas.resize((width, height), resample)
        return canvas

    def _draw_character(
        self,
        image: Image.Image,
        spec: ErdishSpec,
        pose: ErdishPose,
        scale: float,
    ) -> None:
        draw = blending_draw(image)
        pal = PALETTE
        cx = 64.0 + pose.lean_x
        body_top = 52.5 + pose.bob + pose.root_y + pose.body_y
        jacket_bottom = body_top + spec.jacket_height * pose.jacket_scale
        head_center = (
            64.5 + pose.head_x + pose.lean_x * 0.35,
            34.0 + pose.head_y + pose.bob + pose.root_y,
        )

        # Translate authored joint anchors by the animation's whole-body motion.
        joint_offset = (pose.lean_x, pose.bob + pose.root_y)
        near_shoulder = _add(pose.near_shoulder, joint_offset)
        near_elbow = _add(pose.near_elbow, joint_offset)
        near_hand = _add(pose.near_hand, joint_offset)
        far_shoulder = _add(pose.far_shoulder, joint_offset)
        far_elbow = _add(pose.far_elbow, joint_offset)
        far_hand = _add(pose.far_hand, joint_offset)
        near_hip = _add(pose.near_hip, joint_offset)
        near_knee = _add(pose.near_knee, joint_offset)
        near_ankle = _add(pose.near_ankle, joint_offset)
        far_hip = _add(pose.far_hip, joint_offset)
        far_knee = _add(pose.far_knee, joint_offset)
        far_ankle = _add(pose.far_ankle, joint_offset)

        # No floor ellipse / drop shadow.  Contact is expressed by the shoes
        # meeting the shared baseline at y=121.
        self._draw_leg(draw, far_hip, far_knee, far_ankle, near=False, scale=scale)
        self._draw_leg(draw, near_hip, near_knee, near_ankle, near=True, scale=scale)
        self._draw_pelvis(draw, cx, jacket_bottom, scale)
        self._draw_jacket_and_shirt(draw, cx, body_top, jacket_bottom, spec, scale)
        self._draw_neck(draw, head_center, body_top, pose.head_tilt, scale)
        self._draw_head(draw, head_center, spec, pose, scale)

        # Arms are intentionally on top of torso and head layers.  Shoulder
        # caps visibly overlap the jacket yoke, and cuffs overlap the hands, so
        # the anatomy stays legible even at the extrema of talk/interact poses.
        self._draw_arm(
            draw,
            far_shoulder,
            far_elbow,
            far_hand,
            pose.far_palm,
            near=False,
            scale=scale,
        )
        self._draw_arm(
            draw,
            near_shoulder,
            near_elbow,
            near_hand,
            pose.near_palm,
            near=True,
            scale=scale,
        )

    def _draw_leg(
        self,
        draw: ImageDraw.ImageDraw,
        hip: Point,
        knee: Point,
        ankle: Point,
        *,
        near: bool,
        scale: float,
    ) -> None:
        pal = PALETTE
        trouser = pal["trouser_light"] if near else pal["trouser"]
        dark = pal["trouser"] if near else _mix(pal["trouser"], pal["outline"], 0.22)
        _bent_tube(
            draw,
            hip,
            knee,
            ankle,
            (4.3, 3.7, 3.0),
            fill=trouser,
            outline=pal["outline"],
            scale=scale,
        )
        # A restrained inner-leg shade and knee crease add cloth volume without
        # turning the limb into a chain of mechanical joint circles.
        draw.line(
            _poly([(knee[0] - 1.7, knee[1] - 0.2), (knee[0] + 1.5, knee[1] + 0.5)], scale),
            fill=dark,
            width=max(1, round(0.8 * scale)),
        )
        # Connected ankle cuff and shoe.  The shoe overlaps the shin by 2 px.
        draw.ellipse(
            _bbox((ankle[0], ankle[1] - 0.8), 3.25, 3.2, scale),
            fill=dark,
            outline=pal["outline"],
            width=max(1, round(1.2 * scale)),
        )
        shoe_center = (ankle[0] + (1.3 if near else -0.6), ankle[1] + 2.0)
        shoe_box = _bbox(shoe_center, 5.5, 3.0, scale)
        draw.rounded_rectangle(
            shoe_box,
            radius=max(1, round(2.2 * scale)),
            fill=pal["shoe_light"] if near else pal["shoe"],
            outline=pal["outline"],
            width=max(1, round(1.25 * scale)),
        )
        # Small upper highlight, still part of the shoe rather than a shadow.
        draw.line(
            _poly(
                [
                    (shoe_center[0] - 3.4, shoe_center[1] - 1.0),
                    (shoe_center[0] + 2.5, shoe_center[1] - 1.0),
                ],
                scale,
            ),
            fill=_mix(pal["shoe_light"], pal["shirt"], 0.15),
            width=max(1, round(0.8 * scale)),
        )

    def _draw_pelvis(
        self,
        draw: ImageDraw.ImageDraw,
        cx: float,
        jacket_bottom: float,
        scale: float,
    ) -> None:
        pal = PALETTE
        draw.rounded_rectangle(
            (
                (cx - 9.0) * scale,
                (jacket_bottom - 5.0) * scale,
                (cx + 9.0) * scale,
                (jacket_bottom + 5.5) * scale,
            ),
            radius=max(1, round(2.5 * scale)),
            fill=pal["trouser"],
            outline=pal["outline"],
            width=max(1, round(1.25 * scale)),
        )

    def _draw_jacket_and_shirt(
        self,
        draw: ImageDraw.ImageDraw,
        cx: float,
        top_y: float,
        bottom_y: float,
        spec: ErdishSpec,
        scale: float,
    ) -> None:
        pal = PALETTE
        # Oversized jacket silhouette: broad, slightly dropped shoulders over a
        # narrow elderly torso.  The lower corners flare enough to read as cloth
        # but do not become disconnected coat tails.
        jacket = [
            (cx - 15.0, top_y + 3.0),
            (cx - 12.5, top_y - 1.0),
            (cx - 6.5, top_y - 3.0),
            (cx + 7.0, top_y - 2.2),
            (cx + 14.5, top_y + 2.5),
            (cx + 16.5, bottom_y - 3.0),
            (cx + 12.0, bottom_y + 2.0),
            (cx + 2.5, bottom_y + 0.5),
            (cx - 5.0, bottom_y + 1.5),
            (cx - 16.0, bottom_y - 2.5),
        ]
        draw.polygon(
            _poly(jacket, scale),
            fill=pal["jacket"],
            outline=pal["outline"],
            width=max(1, round(1.5 * scale)),
        )
        # Lit plane on the near jacket front.
        draw.polygon(
            _poly(
                [
                    (cx + 1.0, top_y + 2.0),
                    (cx + 12.8, top_y + 4.0),
                    (cx + 14.0, bottom_y - 3.5),
                    (cx + 3.0, bottom_y - 1.0),
                ],
                scale,
            ),
            fill=pal["jacket_light"],
        )
        # Cream shirt is continuous from collar to jacket hem; lapels overlap it.
        shirt = [
            (cx - 5.7, top_y - 1.2),
            (cx + 5.2, top_y - 1.2),
            (cx + 4.2, bottom_y - 5.0),
            (cx - 4.0, bottom_y - 5.0),
        ]
        draw.polygon(
            _poly(shirt, scale),
            fill=pal["shirt"],
            outline=pal["outline_soft"],
            width=max(1, round(0.85 * scale)),
        )
        # Slightly rumpled open collar, echoing the reference photograph.
        left_lapel = [
            (cx - 12.3, top_y + 1.0),
            (cx - 5.0, top_y - 1.0),
            (cx - 0.7, top_y + 9.2),
            (cx - 5.0, top_y + 16.5),
            (cx - 7.2, top_y + 7.0),
        ]
        right_lapel = [
            (cx + 12.2, top_y + 1.3),
            (cx + 5.0, top_y - 1.0),
            (cx + 0.7, top_y + 9.2),
            (cx + 5.3, top_y + 16.0),
            (cx + 7.2, top_y + 6.5),
        ]
        draw.polygon(
            _poly(left_lapel, scale),
            fill=pal["jacket_dark"],
            outline=pal["outline"],
            width=max(1, round(1.0 * scale)),
        )
        draw.polygon(
            _poly(right_lapel, scale),
            fill=pal["jacket"],
            outline=pal["outline"],
            width=max(1, round(1.0 * scale)),
        )
        draw.polygon(
            _poly(
                [
                    (cx - 5.0, top_y - 1.5),
                    (cx - 0.5, top_y + 4.7),
                    (cx - 2.1, top_y + 9.0),
                    (cx - 7.0, top_y + 2.7),
                ],
                scale,
            ),
            fill=pal["shirt"],
            outline=pal["outline_soft"],
            width=max(1, round(0.8 * scale)),
        )
        draw.polygon(
            _poly(
                [
                    (cx + 5.0, top_y - 1.5),
                    (cx + 0.5, top_y + 4.7),
                    (cx + 2.1, top_y + 9.0),
                    (cx + 7.0, top_y + 2.7),
                ],
                scale,
            ),
            fill=pal["shirt"],
            outline=pal["outline_soft"],
            width=max(1, round(0.8 * scale)),
        )
        # Jacket seam, buttons, and pocket welt are clothing details, not props.
        draw.line(
            _poly([(cx + 1.5, top_y + 15.0), (cx + 2.2, bottom_y - 3.5)], scale),
            fill=pal["jacket_dark"],
            width=max(1, round(1.0 * scale)),
        )
        for y in (top_y + 21.5, top_y + 29.0):
            draw.ellipse(
                _bbox((cx + 3.2, y), 1.0, 1.0, scale),
                fill=pal["button"],
                outline=pal["outline"],
                width=max(1, round(0.55 * scale)),
            )
        draw.line(
            _poly([(cx + 7.0, top_y + 25.0), (cx + 12.0, top_y + 24.3)], scale),
            fill=pal["jacket_dark"],
            width=max(1, round(1.0 * scale)),
        )

    def _draw_neck(
        self,
        draw: ImageDraw.ImageDraw,
        head_center: Point,
        body_top: float,
        head_tilt: float,
        scale: float,
    ) -> None:
        pal = PALETTE
        neck_center = (head_center[0] - 1.2, body_top - 1.2)
        draw.rounded_rectangle(
            (
                (neck_center[0] - 4.1) * scale,
                (head_center[1] + 12.0) * scale,
                (neck_center[0] + 4.0) * scale,
                (body_top + 3.0) * scale,
            ),
            radius=max(1, round(2.4 * scale)),
            fill=pal["skin_shadow"],
            outline=pal["outline"],
            width=max(1, round(1.2 * scale)),
        )
        draw.polygon(
            _poly(
                [
                    (neck_center[0] - 2.8, head_center[1] + 12.0),
                    (neck_center[0] + 3.0, head_center[1] + 12.0),
                    (neck_center[0] + 2.0, body_top + 0.5),
                    (neck_center[0] - 2.5, body_top + 0.5),
                ],
                scale,
            ),
            fill=pal["skin"],
        )

    def _draw_head(
        self,
        draw: ImageDraw.ImageDraw,
        center: Point,
        spec: ErdishSpec,
        pose: ErdishPose,
        scale: float,
    ) -> None:
        pal = PALETTE
        cx, cy = center
        angle = pose.head_tilt

        def rp(point: Point) -> Point:
            return _rotate(point, center, angle)

        # Hair mass first.  Every spike shares an edge with the cap so there are
        # no floating white marks.  The asymmetry and swept-back crown are the
        # strongest Paul-Erdos-inspired visual cue after the glasses.
        hair_shape = [
            rp((cx - 12.5, cy - 7.0)),
            rp((cx - 14.5, cy - 12.0)),
            rp((cx - 10.8, cy - 11.0)),
            rp((cx - 13.0, cy - 16.3)),
            rp((cx - 7.8, cy - 14.2)),
            rp((cx - 8.0, cy - 20.2)),
            rp((cx - 2.6, cy - 16.3)),
            rp((cx + 1.0, cy - 21.0)),
            rp((cx + 4.0, cy - 15.9)),
            rp((cx + 10.3, cy - 18.0)),
            rp((cx + 9.2, cy - 12.3)),
            rp((cx + 14.3, cy - 13.5)),
            rp((cx + 11.5, cy - 7.0)),
            rp((cx + 10.0, cy + 2.0)),
            rp((cx - 10.5, cy + 2.0)),
        ]
        draw.polygon(
            _poly(hair_shape, scale),
            fill=pal["hair"],
            outline=pal["outline"],
            width=max(1, round(1.35 * scale)),
        )
        # Connected side tufts, each rooted under the cap edge.  Filled wedges
        # read as unruly elderly hair; isolated line-sparks would look like VFX.
        side_tufts = [
            [rp((cx - 10.2, cy - 4.5)), rp((cx - 16.0, cy - 7.0)), rp((cx - 12.0, cy - 1.5))],
            [rp((cx - 10.7, cy + 0.0)), rp((cx - 16.3, cy - 0.8)), rp((cx - 11.0, cy + 4.0))],
            [rp((cx + 9.8, cy - 4.0)), rp((cx + 15.2, cy - 6.2)), rp((cx + 10.7, cy - 0.4))],
        ]
        for tuft in side_tufts:
            draw.polygon(
                _poly(tuft, scale),
                fill=pal["hair"],
                outline=pal["outline"],
                width=max(1, round(0.9 * scale)),
            )

        # Ears sit behind the face but overlap its contour.
        left_ear = rp((cx - 11.5, cy + 0.5))
        right_ear = rp((cx + 11.2, cy + 0.2))
        for ear in (left_ear, right_ear):
            draw.ellipse(
                _bbox(ear, 3.2, 4.6, scale),
                fill=pal["skin_shadow"],
                outline=pal["outline"],
                width=max(1, round(1.05 * scale)),
            )

        # Long narrow face, subtly fuller at forehead than jaw.
        face = [
            rp((cx - 10.5, cy - 10.5)),
            rp((cx - 7.8, cy - 14.0)),
            rp((cx + 5.5, cy - 14.0)),
            rp((cx + 10.0, cy - 9.2)),
            rp((cx + 11.0, cy + 1.0)),
            rp((cx + 7.0, cy + 11.8)),
            rp((cx + 1.2, cy + 15.0)),
            rp((cx - 5.2, cy + 12.0)),
            rp((cx - 9.8, cy + 4.0)),
        ]
        draw.polygon(
            _poly(face, scale),
            fill=pal["skin"],
            outline=pal["outline"],
            width=max(1, round(1.45 * scale)),
        )
        # Light forehead/cheek plane and temple age lines.
        draw.polygon(
            _poly(
                [
                    rp((cx - 5.5, cy - 11.5)),
                    rp((cx + 3.0, cy - 12.0)),
                    rp((cx + 6.0, cy + 7.5)),
                    rp((cx + 1.5, cy + 11.5)),
                    rp((cx - 2.0, cy + 5.0)),
                ],
                scale,
            ),
            fill=pal["skin_light"],
        )
        for yoff in (-7.5, -5.2):
            draw.line(
                _poly([rp((cx - 4.0, cy + yoff)), rp((cx + 2.0, cy + yoff - 0.4))], scale),
                fill=pal["skin_shadow"],
                width=max(1, round(0.6 * scale)),
            )

        # Large round spectacles.  Both lenses overlap the face and bridge;
        # temple arms overlap the ears/hair, keeping them visually attached.
        lens_y = cy - 1.6
        left_lens = rp((cx - 5.8, lens_y))
        right_lens = rp((cx + 5.8, lens_y - 0.3))
        lens_rx = 5.3
        lens_ry = 5.8
        for lens in (left_lens, right_lens):
            draw.ellipse(
                _bbox(lens, lens_rx, lens_ry, scale),
                fill=pal["glass"],
                outline=pal["outline"],
                width=max(1, round(1.35 * scale)),
            )
        draw.line(
            _poly([rp((cx - 0.7, lens_y - 0.2)), rp((cx + 0.8, lens_y - 0.3))], scale),
            fill=pal["outline"],
            width=max(1, round(1.3 * scale)),
        )
        draw.line(
            _poly([rp((cx - 11.0, lens_y - 0.8)), rp((cx - 13.0, lens_y - 1.8))], scale),
            fill=pal["outline"],
            width=max(1, round(1.0 * scale)),
        )
        draw.line(
            _poly([rp((cx + 11.0, lens_y - 1.0)), rp((cx + 12.6, lens_y - 2.0))], scale),
            fill=pal["outline"],
            width=max(1, round(1.0 * scale)),
        )

        # Eyes and brows are expressive enough to survive downsampling.
        eye_y = lens_y + 0.3
        for side, lens in ((-1.0, left_lens), (1.0, right_lens)):
            eye_center = rp((cx + side * 5.5, eye_y))
            if pose.blink:
                draw.line(
                    _poly(
                        [
                            (eye_center[0] - 2.1, eye_center[1]),
                            (eye_center[0] + 2.1, eye_center[1]),
                        ],
                        scale,
                    ),
                    fill=pal["eye"],
                    width=max(1, round(1.1 * scale)),
                )
            else:
                draw.ellipse(
                    _bbox(eye_center, 1.15, 1.55, scale),
                    fill=pal["eye"],
                )
                draw.ellipse(
                    _bbox((eye_center[0] + 0.25, eye_center[1] - 0.35), 0.28, 0.34, scale),
                    fill=pal["hair_light"],
                )
            brow_y = cy - 7.4 - pose.brow_lift * (1.2 if side > 0 else 0.7)
            draw.line(
                _poly(
                    [rp((cx + side * 8.4, brow_y + 0.8)), rp((cx + side * 3.0, brow_y))],
                    scale,
                ),
                fill=pal["hair_shadow"],
                width=max(1, round(1.0 * scale)),
            )

        # Characteristic long narrow nose, three-quarter projection to screen
        # right.  It is part of the face silhouette rather than a floating line.
        nose_bridge = rp((cx + 1.0, cy - 1.0))
        nose_tip = rp((cx + 4.2, cy + 5.0))
        draw.line(
            _poly([nose_bridge, nose_tip], scale),
            fill=pal["skin_shadow"],
            width=max(1, round(1.05 * scale)),
        )
        draw.line(
            _poly([nose_tip, rp((cx + 1.7, cy + 5.8))], scale),
            fill=pal["outline_soft"],
            width=max(1, round(0.8 * scale)),
        )

        mouth_y = cy + 9.2
        mouth_center = rp((cx + 1.0, mouth_y))
        if pose.mouth_open > 0.18:
            mouth_w = 3.3 + pose.mouth_open * 1.4
            mouth_h = 0.8 + pose.mouth_open * 1.7
            draw.ellipse(
                _bbox(mouth_center, mouth_w, mouth_h, scale),
                fill=pal["mouth"],
                outline=pal["outline"],
                width=max(1, round(0.65 * scale)),
            )
            draw.line(
                _poly(
                    [
                        (mouth_center[0] - mouth_w * 0.6, mouth_center[1] + mouth_h * 0.15),
                        (mouth_center[0] + mouth_w * 0.55, mouth_center[1] + mouth_h * 0.15),
                    ],
                    scale,
                ),
                fill=pal["skin_light"],
                width=max(1, round(0.5 * scale)),
            )
        else:
            smile = 1.0 + pose.mouth_smile * 1.5
            draw.arc(
                _bbox(mouth_center, 4.2, smile + 0.7, scale),
                start=15,
                end=165,
                fill=pal["mouth"],
                width=max(1, round(1.0 * scale)),
            )
        # Chin crease and cheek wrinkle.
        draw.line(
            _poly([rp((cx - 1.8, cy + 12.3)), rp((cx + 3.4, cy + 12.0))], scale),
            fill=pal["skin_shadow"],
            width=max(1, round(0.55 * scale)),
        )
        draw.line(
            _poly([rp((cx + 6.0, cy + 6.7)), rp((cx + 8.2, cy + 7.8))], scale),
            fill=pal["skin_shadow"],
            width=max(1, round(0.55 * scale)),
        )

        # Hair highlights sit inside the connected base mass.
        draw.line(
            _poly([rp((cx - 7.0, cy - 14.5)), rp((cx - 2.0, cy - 17.0))], scale),
            fill=pal["hair_light"],
            width=max(1, round(1.4 * scale)),
        )
        draw.line(
            _poly([rp((cx + 1.0, cy - 17.3)), rp((cx + 7.8, cy - 14.8))], scale),
            fill=pal["hair_light"],
            width=max(1, round(1.4 * scale)),
        )

    def _draw_arm(
        self,
        draw: ImageDraw.ImageDraw,
        shoulder: Point,
        elbow: Point,
        hand: Point,
        palm: str,
        *,
        near: bool,
        scale: float,
    ) -> None:
        pal = PALETTE
        sleeve = pal["jacket_light"] if near else pal["jacket_dark"]
        inner = pal["jacket"] if near else _mix(pal["jacket_dark"], pal["outline"], 0.12)
        # The lower sleeve stops just before the palm.  One six-sided bent tube
        # forms shoulder, upper arm, elbow, and forearm; there is no exposed
        # circular elbow joint and therefore no mannequin/robot read.
        along, normal, length = _unit_segment(elbow, hand)
        wrist = (
            hand[0] - along[0] * min(3.2, length * 0.3),
            hand[1] - along[1] * min(3.2, length * 0.3),
        )
        _bent_tube(
            draw,
            shoulder,
            elbow,
            wrist,
            (5.1, 4.25, 3.2),
            fill=sleeve,
            outline=pal["outline"],
            scale=scale,
        )
        # Inner seam follows the bend and gives the sleeve volume while staying
        # inside the same connected silhouette.
        seam_start = (shoulder[0] - normal[0] * 1.8, shoulder[1] - normal[1] * 1.8)
        seam_end = (wrist[0] - normal[0] * 1.0, wrist[1] - normal[1] * 1.0)
        draw.line(
            _poly([seam_start, elbow, seam_end], scale),
            fill=inner,
            width=max(1, round(0.9 * scale)),
            joint="curve",
        )
        # Cream cuff bridges sleeve and skin.
        draw.ellipse(
            _bbox(wrist, 3.45, 3.0, scale),
            fill=pal["shirt"],
            outline=pal["outline"],
            width=max(1, round(1.0 * scale)),
        )
        self._draw_hand(draw, wrist, hand, palm, near=near, scale=scale)

    def _draw_hand(
        self,
        draw: ImageDraw.ImageDraw,
        wrist: Point,
        center: Point,
        palm: str,
        *,
        near: bool,
        scale: float,
    ) -> None:
        pal = PALETTE
        skin = pal["skin_light"] if near else pal["skin"]
        along, normal, _ = _unit_segment(wrist, center)
        # Solid mitten-like palm first.  Fingers are short connected extensions,
        # never freestanding dots.  This is more robust and readable at 128 px.
        palm_rx = 3.8 if palm in {"open", "press"} else 3.2
        palm_ry = 3.1
        draw.ellipse(
            _bbox(center, palm_rx, palm_ry, scale),
            fill=skin,
            outline=pal["outline"],
            width=max(1, round(1.05 * scale)),
        )
        if palm == "open":
            base = (center[0] + along[0] * 1.4, center[1] + along[1] * 1.4)
            for offset in (-1.65, -0.55, 0.55, 1.65):
                finger_start = (
                    base[0] + normal[0] * offset,
                    base[1] + normal[1] * offset,
                )
                finger_end = (
                    finger_start[0] + along[0] * (3.2 - abs(offset) * 0.28),
                    finger_start[1] + along[1] * (3.2 - abs(offset) * 0.28),
                )
                draw.line(
                    _poly([finger_start, finger_end], scale),
                    fill=pal["outline"],
                    width=max(1, round(1.8 * scale)),
                )
                draw.line(
                    _poly([finger_start, finger_end], scale),
                    fill=skin,
                    width=max(1, round(1.0 * scale)),
                )
        elif palm == "press":
            finger_start = (center[0] + along[0] * 1.5, center[1] + along[1] * 1.5)
            finger_end = (center[0] + along[0] * 5.5, center[1] + along[1] * 5.5)
            draw.line(
                _poly([finger_start, finger_end], scale),
                fill=pal["outline"],
                width=max(1, round(2.0 * scale)),
            )
            draw.line(
                _poly([finger_start, finger_end], scale),
                fill=skin,
                width=max(1, round(1.15 * scale)),
            )
        elif palm == "pinch":
            # Thumb and forefinger remain rooted in the palm.
            for sign in (-1.0, 1.0):
                finger_start = (
                    center[0] + along[0] * 1.0 + normal[0] * sign * 0.8,
                    center[1] + along[1] * 1.0 + normal[1] * sign * 0.8,
                )
                finger_end = (
                    center[0] + along[0] * 3.2 + normal[0] * sign * 0.2,
                    center[1] + along[1] * 3.2 + normal[1] * sign * 0.2,
                )
                draw.line(
                    _poly([finger_start, finger_end], scale),
                    fill=pal["outline"],
                    width=max(1, round(1.75 * scale)),
                )
                draw.line(
                    _poly([finger_start, finger_end], scale),
                    fill=skin,
                    width=max(1, round(0.95 * scale)),
                )
        else:
            # A connected thumb nub makes the relaxed hand read as a hand rather
            # than a circular joint.
            thumb_start = (
                center[0] + normal[0] * 1.4,
                center[1] + normal[1] * 1.4,
            )
            thumb_end = (
                center[0] + normal[0] * 3.2 - along[0] * 0.6,
                center[1] + normal[1] * 3.2 - along[1] * 0.6,
            )
            draw.line(
                _poly([thumb_start, thumb_end], scale),
                fill=pal["outline"],
                width=max(1, round(1.9 * scale)),
            )
            draw.line(
                _poly([thumb_start, thumb_end], scale),
                fill=skin,
                width=max(1, round(1.0 * scale)),
            )
