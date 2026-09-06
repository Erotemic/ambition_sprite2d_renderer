"""Bespoke procedural sprite renderer for Oiler, the drain-market mechanic.

Oiler is the first warm practical anchor after the intro escape. He is not a
professor costume with a wrench pasted on top. He is a compact, capable gate
mechanic who happens to think in curves, tolerances, and invariants:

* a rust-colored workshop banyan cut short enough to work in;
* a dark leather apron with brass fittings and a chalked spiral mark;
* rolled sleeves, olive work trousers, and heavy drain boots;
* a wrapped cream shop cap with gray temple hair and a short gray beard;
* a compact wrench, oil flask, tool satchel, and a readable gate stabilizer;
* a grounded eight-pose contact/down/passing/up walk cycle;
* expressive talk acting and a real repair interaction rather than arm waving.

All art is rendered procedurally with Pillow. The target never paints a ground
ellipse or drop shadow; contact lighting belongs to the game renderer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.generator import CharacterGenerator
from ...registry import CharacterJob
from ambition_sprite2d_renderer.core.draw import rgba
from ambition_sprite2d_renderer.core.draw import blending_draw

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


OILER_PALETTE: Dict[str, Color] = {
    "outline": rgba("#17120E"),
    "skin": rgba("#D7AA82"),
    "skin_light": rgba("#E9C6A4"),
    "skin_shadow": rgba("#A77959"),
    "cap": rgba("#D8C99E"),
    "cap_light": rgba("#F0E4BD"),
    "cap_shadow": rgba("#99865D"),
    "hair": rgba("#A79E8A"),
    "hair_light": rgba("#D7CFBD"),
    "beard": rgba("#8E8475"),
    "beard_dark": rgba("#5F584F"),
    "brow": rgba("#655C50"),
    "coat": rgba("#8D4529"),
    "coat_light": rgba("#B96338"),
    "coat_dark": rgba("#4B251A"),
    "shirt": rgba("#E9DFC4"),
    "shirt_shadow": rgba("#BDB08D"),
    "apron": rgba("#4E3425"),
    "apron_light": rgba("#79513A"),
    "apron_dark": rgba("#2B1C16"),
    "trouser": rgba("#4B5140"),
    "trouser_light": rgba("#68705A"),
    "trouser_dark": rgba("#303529"),
    "boot": rgba("#251D18"),
    "boot_light": rgba("#594134"),
    "boot_sole": rgba("#0D0B09"),
    "steel": rgba("#B9C0C0"),
    "steel_light": rgba("#E3E7E2"),
    "steel_dark": rgba("#596365"),
    "brass": rgba("#D39A3B"),
    "brass_light": rgba("#F0C96A"),
    "brass_dark": rgba("#7B5119"),
    "oil": rgba("#283D43"),
    "oil_light": rgba("#4E7478"),
    "gauge": rgba("#D9E0D8"),
    "gauge_ink": rgba("#3E5557"),
    "warning": rgba("#C44C35"),
    "chalk": rgba("#E5D9B5"),
    "eye": rgba("#2B241F"),
    "white": rgba("#FFF6E5"),
}


class OilerView(str, Enum):
    THREE_QUARTER = "three_quarter"
    FRONT = "front"
    SIDE = "side"


@dataclass(frozen=True)
class OilerSpec:
    target: str
    seed: int
    archetype: str
    name: str
    role: str
    palette_name: str
    head_w: float = 25.5
    head_h: float = 27.5
    shoulder_w: float = 31.5
    torso_h: float = 30.0
    waist_w: float = 24.0
    hip_w: float = 25.5
    thigh_h: float = 17.5
    shin_h: float = 16.5
    boot_h: float = 8.5
    arm_upper: float = 13.3
    arm_lower: float = 12.8


@dataclass
class OilerPose:
    view: OilerView
    body_bob: float = 0.0
    head_tilt: float = 0.0
    blink: bool = False
    talk_open: float = 0.0
    gesture: float = 0.0
    interact: float = 0.0
    torque: float = 0.0
    walk_index: int = -1
    walk_body_y: float = 0.0
    step: float = 0.0


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


class OilerMechanicGenerator(CharacterGenerator):
    """High-detail Oiler renderer used by the generic toon adapter."""

    name = "oiler_mechanic"
    target = "toon"
    applies_job_name = True

    # Keep these counts identical to ToonSideGenerator's existing four rows.
    # The checked-in YAML can remain untouched while the Python renderer is
    # upgraded underneath it.
    ANIMATIONS: Dict[str, Dict[str, int]] = {
        "idle": {"frames": 8, "duration_ms": 120},
        "walk": {"frames": 8, "duration_ms": 100},
        "talk": {"frames": 6, "duration_ms": 100},
        "interact": {"frames": 6, "duration_ms": 95},
    }

    def build_spec(self, job: CharacterJob) -> OilerSpec:
        if job.archetype != "oiler":
            raise KeyError(
                "oiler_mechanic ships only the 'oiler' archetype; "
                f"got {job.archetype!r}"
            )
        return OilerSpec(
            target="toon",
            seed=job.seed,
            archetype=job.archetype,
            name="Oiler",
            role="npc",
            palette_name="oiler_gate_mechanic",
        )

    def canonical_pose(self) -> Tuple[str, int]:
        return ("idle", 1)

    def body_inset(self) -> Dict[str, float]:
        return {"left": 0.08, "right": 0.08, "top": 0.02, "bottom": 0.0}

    def render_frame(
        self,
        spec: OilerSpec,
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

    def pose_for_animation(
        self, animation: str, frame: int, count: int
    ) -> OilerPose:
        t = 0.0 if count <= 1 else frame / float(count - 1)
        wave = math.sin(t * math.tau)
        half = math.sin(t * math.pi)
        if animation == "walk":
            index = frame % 8
            return OilerPose(
                view=OilerView.SIDE,
                walk_index=index,
                step=(-1.0, -0.62, -0.16, 0.50, 1.0, 0.62, 0.16, -0.50)[
                    index
                ],
                walk_body_y=(0.0, 1.2, 0.35, -0.55, 0.0, 1.2, 0.35, -0.55)[
                    index
                ],
                head_tilt=(0.25, 0.05, -0.15, -0.25, -0.25, -0.05, 0.15, 0.25)[
                    index
                ],
            )
        if animation == "talk":
            return OilerPose(
                view=OilerView.FRONT,
                body_bob=0.18 * wave,
                head_tilt=0.65 * wave,
                blink=frame == count - 1,
                talk_open=0.16 + 0.84 * (0.5 + 0.5 * wave),
                gesture=max(0.0, half),
            )
        if animation == "interact":
            return OilerPose(
                view=OilerView.THREE_QUARTER,
                body_bob=0.45 * half,
                head_tilt=-1.1 * half,
                interact=max(0.0, half),
                torque=wave,
                blink=frame == count - 1,
            )
        return OilerPose(
            view=OilerView.THREE_QUARTER,
            body_bob=0.35 * wave,
            head_tilt=0.55 * wave,
            blink=frame == count - 1,
            gesture=0.10 * max(0.0, half),
        )

    def render_animation_frame(
        self,
        spec: OilerSpec,
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
        image = Image.new(
            "RGBA",
            (width * ss, height * ss),
            background or (0, 0, 0, 0),
        )
        scale = (width / 128.0) * ss
        pose = self.pose_for_animation(animation, frame_index, frame_count)
        cx = 64.0 * scale
        feet_y = (117.0 + pose.body_bob) * scale
        if pose.view is OilerView.SIDE:
            self._draw_side(image, cx, feet_y, spec, pose, scale)
        elif pose.view is OilerView.FRONT:
            self._draw_front(image, cx, feet_y, spec, pose, scale)
        else:
            self._draw_three_quarter(image, cx, feet_y, spec, pose, scale)
        if ss > 1:
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        return image

    # ------------------------------------------------------------------
    # Geometry helpers

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

    def _draw_limb(
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
        outline = OILER_PALETTE["outline"]
        _line(d, [root, joint, end], fill=outline, width=round((width + 2.0) * s))
        _line(d, [root, joint, end], fill=fill, width=round(width * s))

    def _draw_hand(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        s: float,
        *,
        palm_w: float = 5.2,
        palm_h: float = 5.0,
    ) -> None:
        pal = OILER_PALETTE
        _ellipse(
            d,
            _bbox(center[0], center[1], palm_w * s, palm_h * s),
            fill=pal["skin"],
            outline=pal["outline"],
            width=round(0.9 * s),
        )

    def _draw_boot_front(
        self, d: ImageDraw.ImageDraw, center_x: float, boot_top: float, feet_y: float, s: float
    ) -> None:
        pal = OILER_PALETTE
        _rounded(
            d,
            (center_x - 5.7 * s, boot_top, center_x + 5.7 * s, feet_y),
            radius=2.0 * s,
            fill=pal["boot"],
            outline=pal["outline"],
            width=round(1.0 * s),
        )
        _line(
            d,
            [(center_x - 4.6 * s, boot_top + 2.2 * s), (center_x + 4.6 * s, boot_top + 2.2 * s)],
            fill=pal["boot_light"],
            width=round(1.1 * s),
        )
        _line(
            d,
            [(center_x - 5.1 * s, feet_y - 1.1 * s), (center_x + 5.1 * s, feet_y - 1.1 * s)],
            fill=pal["boot_sole"],
            width=round(1.3 * s),
        )

    def _draw_boot_side(
        self,
        d: ImageDraw.ImageDraw,
        ankle: Point,
        ground_y: float,
        s: float,
        *,
        near: bool,
        foot_roll: float = 0.0,
    ) -> None:
        pal = OILER_PALETTE
        direction = 1.0
        heel_x = ankle[0] - 3.2 * s
        toe_x = ankle[0] + (7.8 if near else 7.0) * s
        top_y = ankle[1] - 1.0 * s
        sole_y = ground_y - max(0.0, foot_roll) * 0.65 * s
        _poly(
            d,
            [
                (heel_x, top_y),
                (ankle[0] + 3.2 * s, top_y),
                (toe_x, sole_y - 3.0 * s),
                (toe_x + direction * 0.6 * s, sole_y),
                (heel_x - 0.4 * s, sole_y),
            ],
            fill=pal["boot"] if near else pal["boot_sole"],
            outline=pal["outline"],
            width=round(1.0 * s),
        )
        _line(
            d,
            [(heel_x, top_y + 2.0 * s), (ankle[0] + 3.2 * s, top_y + 2.0 * s)],
            fill=pal["boot_light"],
            width=round(1.0 * s),
        )
        _line(
            d,
            [(heel_x - 0.1 * s, sole_y - 0.9 * s), (toe_x + 0.2 * s, sole_y - 0.9 * s)],
            fill=pal["boot_sole"],
            width=round(1.3 * s),
        )

    # ------------------------------------------------------------------
    # Props and costume details

    def _draw_wrench(
        self,
        d: ImageDraw.ImageDraw,
        hand: Point,
        s: float,
        *,
        angle_deg: float,
        length: float = 18.0,
    ) -> None:
        pal = OILER_PALETTE
        angle = math.radians(angle_deg)
        ux, uy = math.cos(angle), math.sin(angle)
        vx, vy = -uy, ux
        start = (hand[0] - ux * 1.5 * s, hand[1] - uy * 1.5 * s)
        end = (hand[0] + ux * length * s, hand[1] + uy * length * s)
        _line(d, [start, end], fill=pal["outline"], width=round(4.3 * s))
        _line(d, [start, end], fill=pal["steel"], width=round(2.7 * s))
        _ellipse(
            d,
            _bbox(start[0], start[1], 4.8 * s, 4.8 * s),
            fill=pal["steel_dark"],
            outline=pal["outline"],
            width=round(0.8 * s),
        )
        jaw_center = (end[0], end[1])
        p1 = (jaw_center[0] + vx * 4.0 * s, jaw_center[1] + vy * 4.0 * s)
        p2 = (jaw_center[0] - vx * 4.0 * s, jaw_center[1] - vy * 4.0 * s)
        bite = (jaw_center[0] - ux * 3.0 * s, jaw_center[1] - uy * 3.0 * s)
        _poly(
            d,
            [
                (p1[0] - ux * 2.0 * s, p1[1] - uy * 2.0 * s),
                p1,
                (jaw_center[0] + ux * 2.1 * s, jaw_center[1] + uy * 2.1 * s),
                p2,
                (p2[0] - ux * 2.0 * s, p2[1] - uy * 2.0 * s),
                bite,
            ],
            fill=pal["steel_light"],
            outline=pal["outline"],
            width=round(0.8 * s),
        )

    def _draw_satchel(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        s: float,
        *,
        side: bool = False,
    ) -> None:
        pal = OILER_PALETTE
        w = (11.0 if side else 13.0) * s
        h = 15.0 * s
        _rounded(
            d,
            _bbox(center[0], center[1], w, h),
            radius=2.0 * s,
            fill=pal["apron_dark"],
            outline=pal["outline"],
            width=round(1.0 * s),
        )
        _poly(
            d,
            [
                (center[0] - w * 0.46, center[1] - h * 0.18),
                (center[0] + w * 0.46, center[1] - h * 0.18),
                (center[0] + w * 0.36, center[1] + h * 0.12),
                (center[0] - w * 0.36, center[1] + h * 0.12),
            ],
            fill=pal["apron_light"],
            outline=pal["outline"],
            width=round(0.7 * s),
        )
        _ellipse(
            d,
            _bbox(center[0], center[1] + 0.2 * h, 2.8 * s, 2.8 * s),
            fill=pal["brass"],
            outline=pal["outline"],
            width=round(0.7 * s),
        )
        # Oil flask reads as a dark blue-green cylinder at the bag edge.
        flask_x = center[0] - w * 0.48
        _rounded(
            d,
            (flask_x - 2.1 * s, center[1] - 2.0 * s, flask_x + 2.1 * s, center[1] + 7.0 * s),
            radius=1.1 * s,
            fill=pal["oil"],
            outline=pal["outline"],
            width=round(0.7 * s),
        )
        _line(
            d,
            [(flask_x - 1.3 * s, center[1] + 0.5 * s), (flask_x + 1.3 * s, center[1] + 0.5 * s)],
            fill=pal["oil_light"],
            width=round(0.8 * s),
        )

    def _draw_stabilizer(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        s: float,
        *,
        phase: float,
    ) -> None:
        pal = OILER_PALETTE
        cx, cy = center
        # Compact gate-ring stabilizer with a gauge and three clamp blocks.
        _ellipse(
            d,
            _bbox(cx, cy, 27.0 * s, 24.0 * s),
            fill=pal["apron_dark"],
            outline=pal["outline"],
            width=round(1.1 * s),
        )
        _ellipse(
            d,
            _bbox(cx, cy, 19.0 * s, 16.0 * s),
            fill=pal["oil"],
            outline=pal["brass_dark"],
            width=round(2.0 * s),
        )
        _ellipse(
            d,
            _bbox(cx, cy, 8.0 * s, 8.0 * s),
            fill=pal["steel_dark"],
            outline=pal["outline"],
            width=round(0.8 * s),
        )
        for angle in (-90.0, 30.0, 150.0):
            a = math.radians(angle)
            bx = cx + math.cos(a) * 10.7 * s
            by = cy + math.sin(a) * 9.3 * s
            _rounded(
                d,
                _bbox(bx, by, 6.0 * s, 5.0 * s),
                radius=1.0 * s,
                fill=pal["brass"],
                outline=pal["outline"],
                width=round(0.8 * s),
            )
        gauge_y = cy - 15.2 * s
        _rounded(
            d,
            _bbox(cx, gauge_y, 13.0 * s, 8.5 * s),
            radius=1.8 * s,
            fill=pal["gauge"],
            outline=pal["outline"],
            width=round(0.9 * s),
        )
        needle_angle = math.radians(-55.0 + phase * 18.0)
        _line(
            d,
            [
                (cx, gauge_y + 2.1 * s),
                (
                    cx + math.cos(needle_angle) * 4.0 * s,
                    gauge_y + 2.1 * s + math.sin(needle_angle) * 4.0 * s,
                ),
            ],
            fill=pal["warning"],
            width=round(1.0 * s),
        )
        _ellipse(
            d,
            _bbox(cx, gauge_y + 2.1 * s, 2.0 * s, 2.0 * s),
            fill=pal["brass_dark"],
            outline=pal["outline"],
            width=round(0.5 * s),
        )

    def _draw_apron_spiral(
        self, d: ImageDraw.ImageDraw, center: Point, s: float
    ) -> None:
        pal = OILER_PALETTE
        cx, cy = center
        pts = []
        for idx in range(14):
            theta = idx * 0.72
            radius = (0.35 + idx * 0.23) * s
            pts.append((cx + math.cos(theta) * radius, cy + math.sin(theta) * radius))
        _line(d, pts, fill=pal["chalk"], width=round(0.75 * s))

    # ------------------------------------------------------------------
    # Three-quarter view

    def _draw_three_quarter(
        self,
        image: Image.Image,
        cx: float,
        feet_y: float,
        spec: OilerSpec,
        pose: OilerPose,
        s: float,
    ) -> None:
        d = blending_draw(image)
        pal = OILER_PALETTE
        outline = pal["outline"]
        boot_top = feet_y - spec.boot_h * s
        shin_top = boot_top - spec.shin_h * s
        hip_y = shin_top - spec.thigh_h * s
        shoulder_y = hip_y - spec.torso_h * s
        crouch = pose.interact * 2.0 * s
        hip_y += crouch
        shoulder_y += crouch
        head_c = (cx + 1.5 * s, shoulder_y - 11.2 * s + pose.head_tilt * 0.12 * s)

        # Legs and boots. Oiler is broad and stable, not bow-legged or a block.
        for leg_x, fill, sign in (
            (cx - 5.0 * s, pal["trouser_dark"], -1.0),
            (cx + 5.0 * s, pal["trouser"], 1.0),
        ):
            knee_x = leg_x + sign * 0.7 * s
            _poly(
                d,
                [
                    (leg_x - 4.0 * s, hip_y),
                    (leg_x + 4.0 * s, hip_y),
                    (knee_x + 3.5 * s, shin_top + crouch),
                    (leg_x + 3.2 * s, boot_top),
                    (leg_x - 3.2 * s, boot_top),
                    (knee_x - 3.5 * s, shin_top + crouch),
                ],
                fill=fill,
                outline=outline,
                width=round(1.0 * s),
            )
            self._draw_boot_front(d, leg_x, boot_top, feet_y, s)

        # Rear tool bag and far arm.
        self._draw_satchel(d, (cx - 14.0 * s, hip_y - 10.0 * s), s * 0.92)
        far_shoulder = (cx - 12.0 * s, shoulder_y + 6.0 * s)
        if pose.interact > 0.0:
            far_hand = (cx - 5.0 * s, hip_y - 10.0 * s)
            far_elbow = (cx - 14.0 * s, shoulder_y + 17.0 * s)
        else:
            far_hand = (cx - 13.0 * s, hip_y - 4.0 * s)
            far_elbow = (cx - 15.0 * s, shoulder_y + 18.0 * s)
        self._draw_limb(
            d,
            far_shoulder,
            far_elbow,
            far_hand,
            s,
            fill=pal["coat_dark"],
            width=6.0,
        )
        self._draw_hand(d, far_hand, s)

        # The head and neck are behind the coat. The torso is drawn next and
        # cleanly owns the collar/shoulder overlap instead of leaving a pasted
        # neck seam.
        self._draw_head_three_quarter(d, head_c, pose, s * 1.035)

        # Short, shaped workshop coat rather than a flat rectangular tunic.
        _poly(
            d,
            [
                (cx - 13.3 * s, shoulder_y + 0.5 * s),
                (cx - 7.0 * s, shoulder_y - 1.2 * s),
                (cx + 7.8 * s, shoulder_y - 0.5 * s),
                (cx + 14.0 * s, shoulder_y + 3.5 * s),
                (cx + 12.0 * s, shoulder_y + 17.0 * s),
                (cx + 10.4 * s, hip_y),
                (cx - 10.8 * s, hip_y),
                (cx - 13.0 * s, shoulder_y + 17.0 * s),
            ],
            fill=pal["coat"],
            outline=outline,
            width=round(1.1 * s),
        )
        # Banyan front panels and collar create cloth depth without random symbols.
        _poly(
            d,
            [
                (cx - 13.4 * s, shoulder_y + 1.5 * s),
                (cx - 2.0 * s, shoulder_y + 3.0 * s),
                (cx - 1.0 * s, hip_y - 3.0 * s),
                (cx - 10.5 * s, hip_y),
            ],
            fill=pal["coat_dark"],
            outline=outline,
            width=round(0.8 * s),
        )
        _poly(
            d,
            [
                (cx - 4.8 * s, shoulder_y + 0.8 * s),
                (cx + 5.5 * s, shoulder_y + 1.0 * s),
                (cx + 1.8 * s, shoulder_y + 8.0 * s),
                (cx - 1.4 * s, shoulder_y + 8.0 * s),
            ],
            fill=pal["shirt"],
            outline=outline,
            width=round(0.8 * s),
        )
        _line(
            d,
            [(cx + 10.2 * s, shoulder_y + 4.0 * s), (cx + 8.7 * s, hip_y - 3.0 * s)],
            fill=pal["coat_light"],
            width=round(1.1 * s),
        )

        # Apron shoulder straps make the leather layer read as worn gear, not
        # a floating rectangle pasted over the coat.
        for a, b in (
            ((cx - 8.8 * s, shoulder_y + 4.0 * s), (cx - 7.5 * s, shoulder_y + 13.0 * s)),
            ((cx + 7.8 * s, shoulder_y + 4.0 * s), (cx + 7.0 * s, shoulder_y + 13.0 * s)),
        ):
            _line(d, [a, b], fill=outline, width=round(3.2 * s))
            _line(d, [a, b], fill=pal["apron_light"], width=round(1.6 * s))

        # Apron is a coherent front layer with a waist strap and tool pockets.
        _poly(
            d,
            [
                (cx - 10.2 * s, shoulder_y + 12.0 * s),
                (cx + 10.5 * s, shoulder_y + 12.0 * s),
                (cx + 9.2 * s, hip_y + 4.2 * s),
                (cx - 8.8 * s, hip_y + 4.2 * s),
            ],
            fill=pal["apron"],
            outline=outline,
            width=round(1.0 * s),
        )
        _line(
            d,
            [(cx - 11.0 * s, shoulder_y + 13.0 * s), (cx + 11.0 * s, shoulder_y + 13.0 * s)],
            fill=pal["apron_light"],
            width=round(2.0 * s),
        )
        _rounded(
            d,
            (
                cx + 2.0 * s,
                shoulder_y + 22.0 * s,
                cx + 9.0 * s,
                shoulder_y + 29.0 * s,
            ),
            radius=1.0 * s,
            fill=pal["apron_light"],
            outline=outline,
            width=round(0.7 * s),
        )
        self._draw_apron_spiral(d, (cx - 3.0 * s, shoulder_y + 23.0 * s), s)

        near_shoulder = (cx + 11.4 * s, shoulder_y + 6.0 * s)
        if pose.interact > 0.0:
            stabilizer_center = (cx + 2.0 * s, hip_y - 5.5 * s)
            near_hand = (cx + 7.8 * s, hip_y - 13.0 * s)
            near_elbow = (cx + 15.0 * s, shoulder_y + 17.0 * s)
            self._draw_limb(
                d,
                near_shoulder,
                near_elbow,
                near_hand,
                s,
                fill=pal["coat"],
                width=6.2,
            )
            self._draw_stabilizer(d, stabilizer_center, s, phase=pose.torque)
            self._draw_wrench(
                d,
                near_hand,
                s,
                angle_deg=118.0 + pose.torque * 20.0,
                length=14.0,
            )
            self._draw_hand(d, near_hand, s)
            # Far hand braces the ring after the prop is painted.
            self._draw_hand(d, far_hand, s, palm_w=4.8, palm_h=4.8)
        else:
            near_hand = (cx + 12.8 * s, hip_y - 3.0 * s)
            near_elbow = (cx + 15.2 * s, shoulder_y + 18.0 * s)
            self._draw_limb(
                d,
                near_shoulder,
                near_elbow,
                near_hand,
                s,
                fill=pal["coat"],
                width=6.2,
            )
            self._draw_wrench(d, near_hand, s, angle_deg=95.0, length=16.0)
            self._draw_hand(d, near_hand, s)

    # ------------------------------------------------------------------
    # Front talk view

    def _draw_front(
        self,
        image: Image.Image,
        cx: float,
        feet_y: float,
        spec: OilerSpec,
        pose: OilerPose,
        s: float,
    ) -> None:
        d = blending_draw(image)
        pal = OILER_PALETTE
        outline = pal["outline"]
        boot_top = feet_y - spec.boot_h * s
        shin_top = boot_top - spec.shin_h * s
        hip_y = shin_top - spec.thigh_h * s
        shoulder_y = hip_y - spec.torso_h * s
        head_c = (cx, shoulder_y - 11.5 * s + pose.head_tilt * 0.1 * s)

        for leg_x, fill in ((cx - 5.0 * s, pal["trouser_dark"]), (cx + 5.0 * s, pal["trouser"])):
            _poly(
                d,
                [
                    (leg_x - 4.0 * s, hip_y),
                    (leg_x + 4.0 * s, hip_y),
                    (leg_x + 3.4 * s, boot_top),
                    (leg_x - 3.4 * s, boot_top),
                ],
                fill=fill,
                outline=outline,
                width=round(1.0 * s),
            )
            self._draw_boot_front(d, leg_x, boot_top, feet_y, s)

        self._draw_satchel(d, (cx - 14.0 * s, hip_y - 10.0 * s), s * 0.9)

        # Far arm: open practical gesture, elbow stays outside the ribcage.
        far_shoulder = (cx - 12.5 * s, shoulder_y + 6.0 * s)
        far_elbow = (
            cx - (15.5 + 2.5 * pose.gesture) * s,
            shoulder_y + (16.0 - 2.0 * pose.gesture) * s,
        )
        far_hand = (
            cx - (13.0 + 8.0 * pose.gesture) * s,
            hip_y - (4.0 + 8.0 * pose.gesture) * s,
        )
        self._draw_limb(
            d,
            far_shoulder,
            far_elbow,
            far_hand,
            s,
            fill=pal["coat_dark"],
            width=6.0,
        )
        self._draw_hand(d, far_hand, s)
        if pose.gesture > 0.25:
            _line(
                d,
                [
                    (far_hand[0] - 1.5 * s, far_hand[1] - 1.0 * s),
                    (far_hand[0] - 4.0 * s, far_hand[1] - 3.0 * s),
                ],
                fill=outline,
                width=round(0.8 * s),
            )

        self._draw_head_front(d, head_c, pose, s * 1.035)

        _poly(
            d,
            [
                (cx - 13.8 * s, shoulder_y + 0.5 * s),
                (cx - 7.0 * s, shoulder_y - 1.2 * s),
                (cx + 7.0 * s, shoulder_y - 1.2 * s),
                (cx + 13.8 * s, shoulder_y + 0.5 * s),
                (cx + 12.0 * s, shoulder_y + 17.0 * s),
                (cx + 10.5 * s, hip_y),
                (cx - 10.5 * s, hip_y),
                (cx - 12.0 * s, shoulder_y + 17.0 * s),
            ],
            fill=pal["coat"],
            outline=outline,
            width=round(1.1 * s),
        )
        _poly(
            d,
            [
                (cx - 4.8 * s, shoulder_y + 0.8 * s),
                (cx + 4.8 * s, shoulder_y + 0.8 * s),
                (cx + 1.9 * s, shoulder_y + 8.0 * s),
                (cx - 1.9 * s, shoulder_y + 8.0 * s),
            ],
            fill=pal["shirt"],
            outline=outline,
            width=round(0.8 * s),
        )
        _line(
            d,
            [(cx - 12.0 * s, shoulder_y + 4.0 * s), (cx - 8.8 * s, hip_y - 2.0 * s)],
            fill=pal["coat_dark"],
            width=round(1.2 * s),
        )
        _line(
            d,
            [(cx + 12.0 * s, shoulder_y + 4.0 * s), (cx + 8.8 * s, hip_y - 2.0 * s)],
            fill=pal["coat_light"],
            width=round(1.2 * s),
        )
        for a, b in (
            ((cx - 8.8 * s, shoulder_y + 4.0 * s), (cx - 7.5 * s, shoulder_y + 13.0 * s)),
            ((cx + 8.8 * s, shoulder_y + 4.0 * s), (cx + 7.5 * s, shoulder_y + 13.0 * s)),
        ):
            _line(d, [a, b], fill=outline, width=round(3.2 * s))
            _line(d, [a, b], fill=pal["apron_light"], width=round(1.6 * s))

        _poly(
            d,
            [
                (cx - 10.5 * s, shoulder_y + 12.0 * s),
                (cx + 10.5 * s, shoulder_y + 12.0 * s),
                (cx + 9.2 * s, hip_y + 4.0 * s),
                (cx - 9.2 * s, hip_y + 4.0 * s),
            ],
            fill=pal["apron"],
            outline=outline,
            width=round(1.0 * s),
        )
        _line(
            d,
            [(cx - 11.0 * s, shoulder_y + 13.0 * s), (cx + 11.0 * s, shoulder_y + 13.0 * s)],
            fill=pal["apron_light"],
            width=round(2.0 * s),
        )
        self._draw_apron_spiral(d, (cx - 3.5 * s, shoulder_y + 23.0 * s), s)

        # Near arm holds the wrench against the apron. Its elbow also stays
        # lateral, so neither front arm bends backward across the body.
        near_shoulder = (cx + 12.5 * s, shoulder_y + 6.0 * s)
        near_elbow = (cx + 15.5 * s, shoulder_y + 17.0 * s)
        near_hand = (cx + 11.5 * s, hip_y - 4.0 * s)
        self._draw_limb(
            d,
            near_shoulder,
            near_elbow,
            near_hand,
            s,
            fill=pal["coat"],
            width=6.2,
        )
        self._draw_wrench(d, near_hand, s, angle_deg=100.0, length=15.0)
        self._draw_hand(d, near_hand, s)

    # ------------------------------------------------------------------
    # Side walk view

    def _draw_side(
        self,
        image: Image.Image,
        cx: float,
        feet_y: float,
        spec: OilerSpec,
        pose: OilerPose,
        s: float,
    ) -> None:
        d = blending_draw(image)
        pal = OILER_PALETTE
        outline = pal["outline"]
        base_boot_top = feet_y - spec.boot_h * s
        base_shin_top = base_boot_top - spec.shin_h * s
        base_hip_y = base_shin_top - spec.thigh_h * s
        body_shift = pose.walk_body_y * s
        hip_y = base_hip_y + body_shift
        shoulder_y = hip_y - spec.torso_h * s
        lean = 0.65 * pose.step * s
        head_c = (cx + 1.0 * s + lean, shoulder_y - 11.3 * s + pose.head_tilt * 0.1 * s)

        self._draw_satchel(d, (cx - 9.7 * s + lean, hip_y - 10.0 * s), s * 0.88, side=True)

        # Far arm is behind the body and swings opposite the near leg.
        far_shoulder = (cx - 3.8 * s + lean, shoulder_y + 6.0 * s)
        far_target = (
            far_shoulder[0] - pose.step * 7.2 * s,
            shoulder_y + 26.0 * s,
        )
        far_elbow, far_hand = self._solve_two_bone_joint(
            far_shoulder,
            far_target,
            spec.arm_upper * s,
            spec.arm_lower * s,
            bend_sign=1.0,
        )
        self._draw_limb(
            d,
            far_shoulder,
            far_elbow,
            far_hand,
            s,
            fill=pal["coat_dark"],
            width=5.8,
        )
        self._draw_hand(d, far_hand, s, palm_w=4.7, palm_h=4.8)

        near_targets = (
            (-8.5, 0.0, 0.0),
            (-5.2, 0.0, 0.0),
            (0.0, -2.0, 0.6),
            (5.2, -4.0, 1.4),
            (8.5, 0.0, 0.0),
            (5.2, 0.0, 0.0),
            (0.0, -2.0, 0.6),
            (-5.2, -4.0, 1.4),
        )
        far_targets = (
            (8.5, 0.0, 0.0),
            (5.2, 0.0, 0.0),
            (0.0, -2.0, 0.6),
            (-5.2, -4.0, 1.4),
            (-8.5, 0.0, 0.0),
            (-5.2, 0.0, 0.0),
            (0.0, -2.0, 0.6),
            (5.2, -4.0, 1.4),
        )
        near_dx, near_lift, near_roll = near_targets[pose.walk_index]
        far_dx, far_lift, far_roll = far_targets[pose.walk_index]
        far_hip = (cx - 1.5 * s + lean, hip_y)
        near_hip = (cx + 2.7 * s + lean, hip_y)
        far_ankle_target = (cx + far_dx * s + lean, base_boot_top + far_lift * s)
        near_ankle_target = (cx + near_dx * s + lean, base_boot_top + near_lift * s)
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
        self._draw_limb(
            d,
            far_hip,
            far_knee,
            far_ankle,
            s,
            fill=pal["trouser_dark"],
            width=6.2,
        )
        self._draw_boot_side(d, far_ankle, feet_y, s, near=False, foot_roll=far_roll)
        self._draw_limb(
            d,
            near_hip,
            near_knee,
            near_ankle,
            s,
            fill=pal["trouser"],
            width=6.4,
        )
        self._draw_boot_side(d, near_ankle, feet_y, s, near=True, foot_roll=near_roll)

        # Head and neck behind the torso. Oiler faces screen-right.
        self._draw_head_side(d, (head_c[0], head_c[1] + 0.4 * s), pose, s * 1.08)

        torso = [
            (cx - 7.5 * s + lean, shoulder_y),
            (cx + 5.5 * s + lean, shoulder_y + 1.0 * s),
            (cx + 8.2 * s + lean, shoulder_y + 9.0 * s),
            (cx + 7.0 * s + lean, hip_y),
            (cx - 6.5 * s + lean, hip_y),
        ]
        _poly(d, torso, fill=pal["coat"], outline=outline, width=round(1.1 * s))
        _poly(
            d,
            [
                (cx - 5.8 * s + lean, shoulder_y + 2.0 * s),
                (cx + 1.7 * s + lean, shoulder_y + 3.0 * s),
                (cx + 5.7 * s + lean, hip_y),
                (cx - 5.0 * s + lean, hip_y),
            ],
            fill=pal["apron"],
            outline=outline,
            width=round(0.9 * s),
        )
        _line(
            d,
            [(cx - 5.5 * s + lean, shoulder_y + 14.0 * s), (cx + 6.2 * s + lean, shoulder_y + 16.0 * s)],
            fill=pal["apron_light"],
            width=round(2.0 * s),
        )
        _line(
            d,
            [(cx - 1.5 * s + lean, shoulder_y + 1.5 * s), (cx - 5.5 * s + lean, hip_y)],
            fill=pal["apron_dark"],
            width=round(3.2 * s),
        )
        self._draw_apron_spiral(d, (cx + 1.0 * s + lean, shoulder_y + 22.0 * s), s * 0.8)

        near_shoulder = (cx + 3.8 * s + lean, shoulder_y + 6.0 * s)
        near_target = (
            near_shoulder[0] + pose.step * 7.2 * s,
            shoulder_y + 26.0 * s,
        )
        near_elbow, near_hand = self._solve_two_bone_joint(
            near_shoulder,
            near_target,
            spec.arm_upper * s,
            spec.arm_lower * s,
            bend_sign=-1.0,
        )
        self._draw_limb(
            d,
            near_shoulder,
            near_elbow,
            near_hand,
            s,
            fill=pal["coat"],
            width=6.0,
        )
        self._draw_wrench(
            d,
            near_hand,
            s,
            angle_deg=90.0 + pose.step * 10.0,
            length=14.0,
        )
        self._draw_hand(d, near_hand, s, palm_w=4.8, palm_h=4.9)

    # ------------------------------------------------------------------
    # Heads

    def _draw_cap_front(
        self, d: ImageDraw.ImageDraw, cx: float, cy: float, s: float, *, three_quarter: bool
    ) -> None:
        pal = OILER_PALETTE
        outline = pal["outline"]
        shift = 1.0 * s if three_quarter else 0.0
        # Wrapped cap: a low crown with three cloth bands and a small rear knot.
        _ellipse(
            d,
            (cx - 13.6 * s, cy - 15.5 * s, cx + 13.6 * s, cy + 1.0 * s),
            fill=pal["cap"],
            outline=outline,
            width=round(1.0 * s),
        )
        _poly(
            d,
            [
                (cx - 7.5 * s + shift, cy - 14.0 * s),
                (cx + 1.0 * s + shift, cy - 17.2 * s),
                (cx + 8.0 * s + shift, cy - 13.0 * s),
                (cx + 4.0 * s + shift, cy - 9.0 * s),
                (cx - 3.0 * s + shift, cy - 10.5 * s),
            ],
            fill=pal["cap_light"],
            outline=outline,
            width=round(0.8 * s),
        )
        _line(
            d,
            [(cx - 12.0 * s, cy - 7.0 * s), (cx + 12.0 * s, cy - 5.0 * s)],
            fill=pal["cap_shadow"],
            width=round(1.2 * s),
        )
        _line(
            d,
            [(cx - 10.0 * s, cy - 11.0 * s), (cx + 8.0 * s, cy - 8.7 * s)],
            fill=pal["cap_shadow"],
            width=round(0.9 * s),
        )
        knot_x = cx - 11.5 * s if three_quarter else cx - 12.5 * s
        _ellipse(
            d,
            _bbox(knot_x, cy - 2.0 * s, 6.0 * s, 5.5 * s),
            fill=pal["cap_shadow"],
            outline=outline,
            width=round(0.8 * s),
        )

    def _draw_head_three_quarter(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        pose: OilerPose,
        s: float,
    ) -> None:
        pal = OILER_PALETTE
        outline = pal["outline"]
        cx, cy = center
        # Neck first; the coat collar overlaps it later in the visual stack.
        _rounded(
            d,
            (cx - 3.8 * s, cy + 8.5 * s, cx + 4.0 * s, cy + 17.0 * s),
            radius=2.0 * s,
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.8 * s),
        )
        # Gray temple hair peeks under the cap and behind the jaw.
        _ellipse(
            d,
            (cx - 12.8 * s, cy - 5.0 * s, cx - 5.0 * s, cy + 9.0 * s),
            fill=pal["hair"],
            outline=outline,
            width=round(0.8 * s),
        )
        _ellipse(
            d,
            (cx + 6.5 * s, cy - 3.0 * s, cx + 11.5 * s, cy + 6.5 * s),
            fill=pal["hair_light"],
            outline=outline,
            width=round(0.7 * s),
        )
        _ellipse(
            d,
            (cx - 11.0 * s, cy - 10.0 * s, cx + 12.0 * s, cy + 12.0 * s),
            fill=pal["skin"],
            outline=outline,
            width=round(1.0 * s),
        )
        _ellipse(
            d,
            (cx + 5.0 * s, cy - 5.0 * s, cx + 12.5 * s, cy + 7.0 * s),
            fill=pal["skin_light"],
        )
        self._draw_cap_front(d, cx, cy - 1.0 * s, s, three_quarter=True)

        # Brows and eyes.
        _line(
            d,
            [(cx - 6.8 * s, cy - 1.4 * s), (cx - 2.2 * s, cy - 2.2 * s)],
            fill=pal["brow"],
            width=round(1.4 * s),
        )
        _line(
            d,
            [(cx + 2.4 * s, cy - 2.2 * s), (cx + 7.0 * s, cy - 1.4 * s)],
            fill=pal["brow"],
            width=round(1.4 * s),
        )
        if pose.blink:
            _line(d, [(cx - 6.0 * s, cy + 0.4 * s), (cx - 2.2 * s, cy + 0.4 * s)], fill=outline, width=round(1.0 * s))
            _line(d, [(cx + 2.3 * s, cy + 0.4 * s), (cx + 6.2 * s, cy + 0.4 * s)], fill=outline, width=round(1.0 * s))
        else:
            _ellipse(d, _bbox(cx - 4.0 * s, cy + 0.2 * s, 2.2 * s, 3.0 * s), fill=pal["eye"])
            _ellipse(d, _bbox(cx + 4.6 * s, cy + 0.2 * s, 2.2 * s, 3.0 * s), fill=pal["eye"])
        # Strong practical nose and aligned beard/moustache.
        _poly(
            d,
            [
                (cx + 1.8 * s, cy + 0.8 * s),
                (cx + 5.3 * s, cy + 4.0 * s),
                (cx + 1.2 * s, cy + 4.5 * s),
            ],
            fill=pal["skin_light"],
            outline=outline,
            width=round(0.7 * s),
        )
        _line(
            d,
            [(cx - 4.5 * s, cy + 6.1 * s), (cx, cy + 5.1 * s), (cx + 4.7 * s, cy + 6.1 * s)],
            fill=pal["beard_dark"],
            width=round(2.1 * s),
        )
        beard = [
            (cx - 7.8 * s, cy + 5.5 * s),
            (cx - 5.8 * s, cy + 10.0 * s),
            (cx, cy + 13.0 * s),
            (cx + 6.5 * s, cy + 10.0 * s),
            (cx + 7.5 * s, cy + 5.5 * s),
            (cx + 3.4 * s, cy + 7.8 * s),
            (cx, cy + 9.0 * s),
            (cx - 3.8 * s, cy + 7.8 * s),
        ]
        _poly(d, beard, fill=pal["beard"], outline=outline, width=round(0.8 * s))
        if pose.talk_open > 0.15:
            _ellipse(
                d,
                _bbox(cx + 0.3 * s, cy + 7.2 * s, 4.8 * s, (2.0 + 2.5 * pose.talk_open) * s),
                fill=pal["outline"],
                outline=outline,
                width=round(0.5 * s),
            )
        else:
            _line(
                d,
                [(cx - 2.0 * s, cy + 7.1 * s), (cx + 2.8 * s, cy + 7.1 * s)],
                fill=pal["outline"],
                width=round(0.8 * s),
            )
        # Grease smudge under the far cheek.
        _line(
            d,
            [(cx - 8.0 * s, cy + 3.0 * s), (cx - 5.3 * s, cy + 4.0 * s)],
            fill=_scaled(pal["oil"], 0.8),
            width=round(0.8 * s),
        )

    def _draw_head_front(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        pose: OilerPose,
        s: float,
    ) -> None:
        pal = OILER_PALETTE
        outline = pal["outline"]
        cx, cy = center
        _rounded(
            d,
            (cx - 4.0 * s, cy + 8.5 * s, cx + 4.0 * s, cy + 17.0 * s),
            radius=2.0 * s,
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.8 * s),
        )
        _ellipse(
            d,
            (cx - 12.5 * s, cy - 5.0 * s, cx - 5.5 * s, cy + 9.0 * s),
            fill=pal["hair"],
            outline=outline,
            width=round(0.8 * s),
        )
        _ellipse(
            d,
            (cx + 5.5 * s, cy - 5.0 * s, cx + 12.5 * s, cy + 9.0 * s),
            fill=pal["hair"],
            outline=outline,
            width=round(0.8 * s),
        )
        _ellipse(
            d,
            (cx - 11.5 * s, cy - 10.0 * s, cx + 11.5 * s, cy + 12.5 * s),
            fill=pal["skin"],
            outline=outline,
            width=round(1.0 * s),
        )
        self._draw_cap_front(d, cx, cy - 1.0 * s, s, three_quarter=False)
        _line(d, [(cx - 7.2 * s, cy - 1.5 * s), (cx - 2.3 * s, cy - 2.3 * s)], fill=pal["brow"], width=round(1.4 * s))
        _line(d, [(cx + 2.3 * s, cy - 2.3 * s), (cx + 7.2 * s, cy - 1.5 * s)], fill=pal["brow"], width=round(1.4 * s))
        if pose.blink:
            _line(d, [(cx - 6.2 * s, cy + 0.5 * s), (cx - 2.2 * s, cy + 0.5 * s)], fill=outline, width=round(1.0 * s))
            _line(d, [(cx + 2.2 * s, cy + 0.5 * s), (cx + 6.2 * s, cy + 0.5 * s)], fill=outline, width=round(1.0 * s))
        else:
            _ellipse(d, _bbox(cx - 4.2 * s, cy + 0.3 * s, 2.2 * s, 3.0 * s), fill=pal["eye"])
            _ellipse(d, _bbox(cx + 4.2 * s, cy + 0.3 * s, 2.2 * s, 3.0 * s), fill=pal["eye"])
        _poly(
            d,
            [(cx, cy + 0.8 * s), (cx + 2.7 * s, cy + 4.4 * s), (cx - 1.0 * s, cy + 4.4 * s)],
            fill=pal["skin_light"],
            outline=outline,
            width=round(0.7 * s),
        )
        _line(
            d,
            [(cx - 5.0 * s, cy + 6.1 * s), (cx, cy + 5.0 * s), (cx + 5.0 * s, cy + 6.1 * s)],
            fill=pal["beard_dark"],
            width=round(2.2 * s),
        )
        _poly(
            d,
            [
                (cx - 8.0 * s, cy + 5.6 * s),
                (cx - 5.8 * s, cy + 10.2 * s),
                (cx, cy + 13.2 * s),
                (cx + 5.8 * s, cy + 10.2 * s),
                (cx + 8.0 * s, cy + 5.6 * s),
                (cx + 3.5 * s, cy + 7.8 * s),
                (cx, cy + 9.2 * s),
                (cx - 3.5 * s, cy + 7.8 * s),
            ],
            fill=pal["beard"],
            outline=outline,
            width=round(0.8 * s),
        )
        if pose.talk_open > 0.15:
            _ellipse(
                d,
                _bbox(cx, cy + 7.2 * s, 4.8 * s, (2.0 + 2.7 * pose.talk_open) * s),
                fill=outline,
                outline=outline,
                width=round(0.5 * s),
            )
        else:
            _line(d, [(cx - 2.4 * s, cy + 7.1 * s), (cx + 2.4 * s, cy + 7.1 * s)], fill=outline, width=round(0.8 * s))
        _line(
            d,
            [(cx + 6.0 * s, cy + 2.8 * s), (cx + 8.2 * s, cy + 4.0 * s)],
            fill=_scaled(pal["oil"], 0.8),
            width=round(0.8 * s),
        )

    def _draw_head_side(
        self,
        d: ImageDraw.ImageDraw,
        center: Point,
        pose: OilerPose,
        s: float,
    ) -> None:
        pal = OILER_PALETTE
        outline = pal["outline"]
        cx, cy = center
        # Full profile head, facing right. The cap sits on the skull instead of
        # replacing it, and the beard terminates exactly on the jaw/chin line.
        _rounded(
            d,
            (cx - 4.3 * s, cy + 9.0 * s, cx + 3.5 * s, cy + 17.0 * s),
            radius=2.0 * s,
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.8 * s),
        )
        _ellipse(
            d,
            (cx - 12.0 * s, cy - 8.0 * s, cx + 7.0 * s, cy + 11.0 * s),
            fill=pal["skin"],
            outline=outline,
            width=round(1.0 * s),
        )
        # Nose and face plane.
        _poly(
            d,
            [
                (cx + 4.5 * s, cy - 2.0 * s),
                (cx + 11.5 * s, cy + 2.2 * s),
                (cx + 5.0 * s, cy + 4.2 * s),
            ],
            fill=pal["skin_light"],
            outline=outline,
            width=round(0.8 * s),
        )
        # Temple hair remains below the cap and outside the face contour.
        _poly(
            d,
            [
                (cx - 11.5 * s, cy - 5.0 * s),
                (cx - 8.0 * s, cy - 8.0 * s),
                (cx - 5.5 * s, cy + 3.0 * s),
                (cx - 7.0 * s, cy + 9.0 * s),
                (cx - 11.5 * s, cy + 7.0 * s),
            ],
            fill=pal["hair"],
            outline=outline,
            width=round(0.8 * s),
        )
        # Side cap with a full crown and cloth tail at the back.
        _ellipse(
            d,
            (cx - 13.0 * s, cy - 16.0 * s, cx + 8.5 * s, cy - 0.5 * s),
            fill=pal["cap"],
            outline=outline,
            width=round(1.0 * s),
        )
        _poly(
            d,
            [
                (cx - 7.5 * s, cy - 14.5 * s),
                (cx + 0.5 * s, cy - 17.0 * s),
                (cx + 6.5 * s, cy - 12.0 * s),
                (cx + 1.0 * s, cy - 8.5 * s),
                (cx - 5.0 * s, cy - 10.0 * s),
            ],
            fill=pal["cap_light"],
            outline=outline,
            width=round(0.8 * s),
        )
        _line(
            d,
            [(cx - 11.5 * s, cy - 7.0 * s), (cx + 7.0 * s, cy - 5.0 * s)],
            fill=pal["cap_shadow"],
            width=round(1.1 * s),
        )
        _ellipse(
            d,
            _bbox(cx - 12.0 * s, cy - 1.5 * s, 6.0 * s, 5.5 * s),
            fill=pal["cap_shadow"],
            outline=outline,
            width=round(0.8 * s),
        )
        _line(
            d,
            [(cx + 0.8 * s, cy - 1.3 * s), (cx + 5.2 * s, cy - 1.7 * s)],
            fill=pal["brow"],
            width=round(1.4 * s),
        )
        if pose.blink:
            _line(d, [(cx + 2.0 * s, cy + 0.6 * s), (cx + 5.5 * s, cy + 0.6 * s)], fill=outline, width=round(1.0 * s))
        else:
            _ellipse(d, _bbox(cx + 4.0 * s, cy + 0.5 * s, 2.2 * s, 3.0 * s), fill=pal["eye"])
        # Moustache and beard hug the profile jaw; neither floats above it.
        _line(
            d,
            [(cx + 2.5 * s, cy + 5.2 * s), (cx + 7.5 * s, cy + 5.9 * s)],
            fill=pal["beard_dark"],
            width=round(2.0 * s),
        )
        _poly(
            d,
            [
                (cx - 1.5 * s, cy + 5.5 * s),
                (cx + 6.5 * s, cy + 5.5 * s),
                (cx + 5.0 * s, cy + 10.0 * s),
                (cx + 0.5 * s, cy + 13.0 * s),
                (cx - 4.0 * s, cy + 9.0 * s),
            ],
            fill=pal["beard"],
            outline=outline,
            width=round(0.8 * s),
        )
        _line(
            d,
            [(cx + 3.5 * s, cy + 7.2 * s), (cx + 7.0 * s, cy + 7.2 * s)],
            fill=outline,
            width=round(0.8 * s),
        )
        _line(
            d,
            [(cx - 7.0 * s, cy + 1.5 * s), (cx - 4.5 * s, cy + 2.5 * s)],
            fill=_scaled(pal["oil"], 0.8),
            width=round(0.8 * s),
        )
