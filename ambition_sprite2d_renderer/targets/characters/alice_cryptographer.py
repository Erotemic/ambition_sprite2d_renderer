"""Bespoke procedural sprite target for Alice, field cartographer.

Alice is part of the cryptography crew, but in Ambition she is the person who
maps routes that powerful institutions would rather keep legible only to
themselves.  The sprite therefore reads *field operative first* and
*cryptography reference second*:

* a compact expedition jacket with an asymmetric closure;
* a cross-body survey harness, compass, map folio, and map tube;
* reinforced trousers and planted field boots rather than a skirt/robe;
* a high braided ponytail that gives her a fast, unmistakable silhouette;
* a tiny one-time-pad tape on the harness rather than a literal lab costume.
* a clean transparent cutout with no painted ground or drop shadow.

The animation vocabulary stays runtime-compatible with the historical Alice
sheet (``idle``, ``walk``, ``talk``, ``interact``, ``idle_side``), but every
view is redrawn.  Idle is a confident three-quarter stance, talk is front-facing,
walk/idle_side use a real profile, and interact opens a route map while she
checks a compass.  The profile walk follows the shared PCA-style authored
contact/down/passing/up baseline with ankle targets and two-bone IK.
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
    "walk": AliceView.SIDE,
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
    head_w: float = 24.0
    head_h: float = 27.0
    shoulder_w: float = 27.0
    torso_h: float = 29.0
    waist_w: float = 20.0
    hip_w: float = 23.0
    thigh_h: float = 18.0
    shin_h: float = 18.0
    boot_h: float = 9.0
    arm_len: float = 27.0
    pony_segments: int = 6


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

    ANIMATIONS: Dict[str, Dict[str, int]] = {
        "idle": {"frames": 6, "duration_ms": 140},
        "walk": {"frames": 8, "duration_ms": 95},
        "talk": {"frames": 6, "duration_ms": 110},
        "interact": {"frames": 6, "duration_ms": 130},
        "idle_side": {"frames": 6, "duration_ms": 140},
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
            palette_name="alice_field_cartographer",
        )

    def canonical_pose(self) -> Tuple[str, int]:
        return ("idle", 1)

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
        # The braid and carried map are visual extensions, not collision volume.
        return {"left": 0.08, "right": 0.08, "top": 0.02, "bottom": 0.0}

    def pose_for_animation(self, animation: str, frame: int, count: int) -> AlicePose:
        t = 0.0 if count <= 1 else frame / float(count - 1)
        wave = math.sin(t * math.tau)
        half = math.sin(t * math.pi)
        pose = AlicePose(view=ANIMATION_VIEWS.get(animation, AliceView.THREE_QUARTER))
        if animation == "idle":
            pose.body_bob = 0.45 * wave
            pose.head_tilt = 0.8 * wave
            pose.blink = frame == count - 1
            pose.scan = 0.12 * wave
        elif animation == "walk":
            # Authored eight-pose contact/down/passing/up loop.  This mirrors
            # the good PCA/side-biped baseline instead of driving limbs from a
            # single opposed sine wave.  ``step`` is the near-arm swing value;
            # feet use their own ankle-target tables in ``_draw_side``.
            index = frame % 8
            pose.walk_index = index
            pose.step = (-1.0, -0.62, -0.18, 0.52, 1.0, 0.58, 0.08, -0.55)[index]
            pose.walk_body_y = (0.0, 1.15, 0.35, -0.65, 0.0, 1.15, 0.35, -0.65)[index]
            pose.head_tilt = (0.35, 0.10, -0.15, -0.35, -0.35, -0.10, 0.15, 0.35)[index]
        elif animation == "talk":
            pose.body_bob = 0.25 * wave
            pose.talk_open = 0.15 + 0.85 * (0.5 + 0.5 * wave)
            pose.gesture = max(0.0, half)
            pose.head_tilt = 0.9 * wave
            pose.blink = frame == count - 1
        elif animation == "interact":
            pose.body_bob = -0.35 * half
            pose.map_open = max(0.0, half)
            pose.gesture = max(0.0, half)
            pose.scan = wave
            pose.head_tilt = -1.3 * half
        elif animation == "idle_side":
            pose.body_bob = 0.35 * wave
            pose.scan = 0.5 + 0.25 * wave
            pose.blink = frame == count - 1
        return pose

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
        image = Image.new(
            "RGBA",
            (width * ss, height * ss),
            background or (0, 0, 0, 0),
        )
        scale = (width / 128.0) * ss
        pose = self.pose_for_animation(animation, frame_index, frame_count)
        cx = 64.0 * scale
        feet_y = (117.0 + pose.body_bob) * scale
        if pose.view is AliceView.FRONT:
            self._draw_front(image, cx, feet_y, spec, pose, scale)
        elif pose.view is AliceView.SIDE:
            self._draw_side(image, cx, feet_y, spec, pose, scale)
        else:
            self._draw_three_quarter(image, cx, feet_y, spec, pose, scale)
        if ss > 1:
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        return image

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
        """Draw a jointed limb with one continuous, naturally rounded stroke."""
        outline = ALICE_PALETTE["outline"]
        _line(d, [root, joint, end], fill=outline, width=round((width + 2.0) * s))
        _line(d, [root, joint, end], fill=fill, width=round(width * s))

    def _draw_side_boot(
        self,
        d: ImageDraw.ImageDraw,
        ankle: Point,
        ground_y: float,
        s: float,
        *,
        near: bool,
        foot_roll: float,
    ) -> None:
        """Draw a profile boot anchored to the solved ankle target."""
        pal = ALICE_PALETTE
        outline = pal["outline"]
        bottom = max(ankle[1] + 6.5 * s, ground_y)
        heel = ankle[0] - (4.2 if near else 3.8) * s
        toe = ankle[0] + (8.0 if near else 7.2) * s
        roll = foot_roll * s
        points = [
            (heel, ankle[1] - 1.2 * s),
            (ankle[0] + 3.2 * s, ankle[1] - 0.8 * s),
            (toe, bottom - 3.0 * s - roll),
            (toe - 0.4 * s, bottom),
            (heel - 0.3 * s, bottom),
        ]
        _poly(d, points, fill=pal["boot"], outline=outline, width=round(1.0 * s))
        _line(
            d,
            [
                (heel + 0.8 * s, ankle[1] + 1.7 * s),
                (ankle[0] + 3.8 * s, ankle[1] + 1.7 * s),
            ],
            fill=pal["boot_light"],
            width=round(1.2 * s),
        )

    def _draw_braid(
        self,
        d: ImageDraw.ImageDraw,
        points: Sequence[Point],
        s: float,
        *,
        behind: bool = True,
    ) -> None:
        pal = ALICE_PALETTE
        outline = pal["outline"]
        for index, (x, y) in enumerate(points):
            diameter = (6.0 - index * 0.45) * s
            fill = pal["hair"] if index % 2 == 0 else pal["hair_mid"]
            _ellipse(
                d,
                _bbox(x, y, diameter, diameter * 0.82),
                fill=fill,
                outline=outline,
                width=round(0.9 * s),
            )
        if points:
            x, y = points[-1]
            _rounded(
                d,
                (x - 2.1 * s, y + 1.2 * s, x + 2.1 * s, y + 4.2 * s),
                radius=1.0 * s,
                fill=pal["amber"],
                outline=outline,
                width=round(0.8 * s),
            )

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

    def _draw_compass(
        self, d: ImageDraw.ImageDraw, cx: float, cy: float, s: float
    ) -> None:
        pal = ALICE_PALETTE
        outline = pal["outline"]
        _ellipse(
            d,
            _bbox(cx, cy, 7.2 * s, 7.2 * s),
            fill=pal["amber"],
            outline=outline,
            width=round(1.0 * s),
        )
        _ellipse(
            d,
            _bbox(cx, cy, 4.5 * s, 4.5 * s),
            fill=pal["shirt"],
            outline=pal["leather_dark"],
            width=round(0.6 * s),
        )
        _poly(
            d,
            [
                (cx, cy - 2.0 * s),
                (cx + 1.0 * s, cy + 1.5 * s),
                (cx, cy + 0.7 * s),
                (cx - 1.0 * s, cy + 1.5 * s),
            ],
            fill=pal["route"],
            outline=outline,
            width=round(0.4 * s),
        )

    def _draw_front_bust_seam(
        self,
        d: ImageDraw.ImageDraw,
        cx: float,
        shoulder_y: float,
        s: float,
        *,
        three_quarter: bool = False,
    ) -> None:
        """Draw the same shallow jacket contour in every forward-facing frame.

        This is a tailoring seam, not a floating anatomy glyph.  Keeping it in
        one helper prevents the subtle chest cue from disappearing when Alice
        changes between idle, talk, and interact animations.  The arch is made
        from two almost-straight segments so it does not read as a pronounced
        upside-down U.
        """
        pal = ALICE_PALETTE
        seam = _scaled(pal["jacket_dark"], 1.18)
        if three_quarter:
            points = [
                (cx - 4.6 * s, shoulder_y + 14.0 * s),
                (cx + 0.8 * s, shoulder_y + 12.8 * s),
                (cx + 6.2 * s, shoulder_y + 13.8 * s),
            ]
        else:
            points = [
                (cx - 5.4 * s, shoulder_y + 14.0 * s),
                (cx, shoulder_y + 12.8 * s),
                (cx + 5.4 * s, shoulder_y + 14.0 * s),
            ]
        _line(d, points, fill=seam, width=round(0.55 * s))

    def _draw_cipher_tape(
        self, d: ImageDraw.ImageDraw, x: float, y: float, s: float
    ) -> None:
        pal = ALICE_PALETTE
        outline = pal["outline"]
        _rounded(
            d,
            (x - 3.0 * s, y - 1.0 * s, x + 3.0 * s, y + 12.0 * s),
            radius=1.0 * s,
            fill=pal["shirt"],
            outline=outline,
            width=round(0.8 * s),
        )
        for index in range(5):
            if index in (0, 3, 4):
                _rounded(
                    d,
                    (
                        x - 1.8 * s,
                        y + (1.0 + index * 2.0) * s,
                        x + 1.8 * s,
                        y + (2.3 + index * 2.0) * s,
                    ),
                    radius=0.4 * s,
                    fill=pal["outline"],
                )

    # ------------------------------------------------------------------
    # Three-quarter view

    def _draw_three_quarter(
        self,
        image: Image.Image,
        cx: float,
        feet_y: float,
        spec: AliceSpec,
        pose: AlicePose,
        s: float,
    ) -> None:
        d = ImageDraw.Draw(image)
        pal = ALICE_PALETTE
        outline = pal["outline"]

        boot_top = feet_y - spec.boot_h * s
        shin_top = boot_top - spec.shin_h * s
        hip_y = shin_top - spec.thigh_h * s
        shoulder_y = hip_y - spec.torso_h * s
        head_c = (cx + 1.8 * s, shoulder_y - 11.5 * s)

        # Rear braid and map tube establish the silhouette before the body.
        braid_base = (head_c[0] - 8.0 * s, head_c[1] - 10.0 * s)
        braid_points = [
            (
                braid_base[0] - 4.0 * math.sin(i * 0.7 + pose.scan) * s,
                braid_base[1] + (5.0 + i * 5.2) * s,
            )
            for i in range(spec.pony_segments)
        ]
        self._draw_braid(d, braid_points, s)
        _rounded(
            d,
            (cx - 15.0 * s, shoulder_y + 9.0 * s, cx - 8.0 * s, hip_y + 15.0 * s),
            radius=3.0 * s,
            fill=pal["leather_dark"],
            outline=outline,
            width=round(1.0 * s),
        )
        _line(
            d,
            [(cx - 13.2 * s, shoulder_y + 13.0 * s), (cx - 10.2 * s, hip_y + 11.0 * s)],
            fill=pal["amber"],
            width=round(1.0 * s),
        )

        # Legs: one planted forward for a confident, non-neutral stance.
        for near, sign in ((False, -1), (True, 1)):
            x = cx + sign * (5.2 if near else 4.0) * s
            forward = (1.5 if near else -1.0) * s
            thigh = [
                (x - 3.8 * s, hip_y),
                (x + 3.8 * s, hip_y),
                (x + 3.2 * s + forward, shin_top),
                (x - 3.2 * s + forward, shin_top),
            ]
            _poly(
                d,
                thigh,
                fill=pal["trouser"] if near else pal["trouser_dark"],
                outline=outline,
                width=round(1.0 * s),
            )
            shin = [
                (x - 3.2 * s + forward, shin_top),
                (x + 3.2 * s + forward, shin_top),
                (x + 3.0 * s + 1.4 * forward, boot_top),
                (x - 3.0 * s + 1.4 * forward, boot_top),
            ]
            _poly(
                d,
                shin,
                fill=pal["trouser"] if near else pal["trouser_dark"],
                outline=outline,
                width=round(1.0 * s),
            )
            boot_x = x + 1.8 * forward
            _rounded(
                d,
                (boot_x - 5.0 * s, boot_top - 1.0 * s, boot_x + 6.8 * s, feet_y),
                radius=2.5 * s,
                fill=pal["boot"],
                outline=outline,
                width=round(1.0 * s),
            )
            _line(
                d,
                [
                    (boot_x - 4.0 * s, boot_top + 2.0 * s),
                    (boot_x + 4.0 * s, boot_top + 2.0 * s),
                ],
                fill=pal["boot_light"],
                width=round(1.5 * s),
            )
            _line(
                d,
                [
                    (boot_x - 4.8 * s, feet_y - 1.1 * s),
                    (boot_x + 6.8 * s, feet_y - 1.1 * s),
                ],
                fill=outline,
                width=round(1.2 * s),
            )

        # Far arm: holds the folio low unless interact opens it.
        far_shoulder = (cx - 10.5 * s, shoulder_y + 4.0 * s)
        far_elbow = (cx - 15.5 * s - pose.gesture * 1.5 * s, shoulder_y + 18.0 * s)
        far_hand = (
            cx - 14.0 * s - pose.gesture * 3.0 * s,
            hip_y + 6.0 * s - pose.gesture * 6.0 * s,
        )
        _line(
            d,
            [far_shoulder, far_elbow, far_hand],
            fill=pal["jacket_dark"],
            width=round(7.0 * s),
        )
        _line(
            d, [far_shoulder, far_elbow, far_hand], fill=outline, width=round(1.0 * s)
        )
        _ellipse(
            d,
            _bbox(far_hand[0], far_hand[1], 5.3 * s, 5.3 * s),
            fill=pal["skin"],
            outline=outline,
            width=round(0.9 * s),
        )

        # Torso: angular expedition jacket, no robe/skirt silhouette.
        # Keep the jacket contour simple and clockwise.  The previous five
        # point contour pinched directly from the back hip to the back waist;
        # this was legal, but made the torso read unnaturally slab-like next
        # to the better articulated limbs.  The two shallow camera-right
        # chest points give Alice a very small, fully clothed human bust while
        # preserving the compact Lucina-like field-operator silhouette.
        torso = [
            (cx - 13.0 * s, shoulder_y),
            (cx + 14.0 * s, shoulder_y + 1.0 * s),
            (cx + 14.6 * s, shoulder_y + 8.0 * s),
            (cx + 14.1 * s, shoulder_y + 12.5 * s),
            (cx + 10.2 * s, shoulder_y + 20.0 * s),
            (cx + 12.0 * s, hip_y + 1.0 * s),
            (cx - 11.0 * s, hip_y),
            (cx - 10.2 * s, shoulder_y + 18.0 * s),
        ]
        _poly(d, torso, fill=pal["jacket"], outline=outline, width=round(1.2 * s))
        # Short high collar and cream throat panel.
        _poly(
            d,
            [
                (cx - 7.0 * s, shoulder_y),
                (cx + 6.5 * s, shoulder_y),
                (cx + 3.0 * s, shoulder_y + 7.0 * s),
                (cx - 2.0 * s, shoulder_y + 8.0 * s),
            ],
            fill=pal["shirt"],
            outline=outline,
            width=round(1.0 * s),
        )
        _poly(
            d,
            [
                (cx - 8.0 * s, shoulder_y),
                (cx - 0.5 * s, shoulder_y + 8.0 * s),
                (cx - 4.0 * s, shoulder_y + 12.0 * s),
                (cx - 11.0 * s, shoulder_y + 4.0 * s),
            ],
            fill=pal["jacket_dark"],
            outline=outline,
            width=round(0.9 * s),
        )
        _line(
            d,
            [(cx + 7.0 * s, shoulder_y + 3.0 * s), (cx - 1.0 * s, hip_y - 2.0 * s)],
            fill=pal["amber"],
            width=round(2.0 * s),
        )
        _line(
            d,
            [(cx + 8.3 * s, shoulder_y + 3.0 * s), (cx + 0.3 * s, hip_y - 2.0 * s)],
            fill=outline,
            width=round(0.7 * s),
        )
        _line(
            d,
            [
                (cx + 3.2 * s, shoulder_y + 8.0 * s),
                (cx + 7.0 * s, shoulder_y + 12.0 * s),
                (cx + 8.3 * s, shoulder_y + 15.0 * s),
            ],
            fill=pal["jacket_dark"],
            width=round(0.65 * s),
        )
        self._draw_front_bust_seam(
            d, cx, shoulder_y, s, three_quarter=True
        )
        # Jacket hem split and highlight.
        _line(
            d,
            [(cx - 10.0 * s, hip_y - 1.0 * s), (cx + 11.0 * s, hip_y)],
            fill=pal["jacket_light"],
            width=round(1.0 * s),
        )
        _line(
            d,
            [(cx + 7.5 * s, shoulder_y + 9.0 * s), (cx + 8.5 * s, hip_y - 5.0 * s)],
            fill=pal["jacket_light"],
            width=round(1.0 * s),
        )

        # Harness, belt, compass, and OTP tape.
        _line(
            d,
            [(cx - 8.5 * s, shoulder_y + 2.0 * s), (cx + 7.0 * s, hip_y - 1.0 * s)],
            fill=pal["leather_dark"],
            width=round(4.0 * s),
        )
        _line(
            d,
            [(cx - 8.5 * s, shoulder_y + 2.0 * s), (cx + 7.0 * s, hip_y - 1.0 * s)],
            fill=pal["leather"],
            width=round(2.2 * s),
        )
        _rounded(
            d,
            (cx - 12.0 * s, hip_y - 3.0 * s, cx + 12.0 * s, hip_y + 2.0 * s),
            radius=1.5 * s,
            fill=pal["leather_dark"],
            outline=outline,
            width=round(0.8 * s),
        )
        self._draw_compass(d, cx + 8.7 * s, hip_y + 3.5 * s, s)
        self._draw_cipher_tape(d, cx + 3.5 * s, shoulder_y + 9.0 * s, s)

        # Near arm: hand on hip in idle, raised compass hand in interact.
        near_shoulder = (cx + 11.5 * s, shoulder_y + 4.0 * s)
        if pose.map_open > 0.05:
            near_elbow = (cx + 15.0 * s, shoulder_y + 15.0 * s)
            near_hand = (cx + 13.0 * s, shoulder_y + 24.0 * s - 4.0 * pose.gesture * s)
        else:
            near_elbow = (cx + 16.0 * s, shoulder_y + 17.0 * s)
            near_hand = (cx + 10.5 * s, hip_y - 1.0 * s)
        _line(
            d,
            [near_shoulder, near_elbow, near_hand],
            fill=outline,
            width=round(8.0 * s),
        )
        _line(
            d,
            [near_shoulder, near_elbow, near_hand],
            fill=pal["jacket"],
            width=round(6.2 * s),
        )
        _rounded(
            d,
            (
                near_hand[0] - 3.2 * s,
                near_hand[1] - 3.2 * s,
                near_hand[0] + 3.2 * s,
                near_hand[1] + 3.2 * s,
            ),
            radius=2.0 * s,
            fill=pal["skin"],
            outline=outline,
            width=round(0.9 * s),
        )

        if pose.map_open > 0.05:
            map_cx = cx - 4.0 * s
            map_cy = shoulder_y + 29.0 * s
            self._draw_map_folio(d, map_cx, map_cy, s, open_amount=pose.map_open)
            self._draw_compass(
                d, near_hand[0] + 0.5 * s, near_hand[1] - 1.0 * s, s * 0.82
            )
        else:
            self._draw_map_folio(
                d, far_hand[0] - 1.0 * s, far_hand[1] + 2.0 * s, s, angle_hint=-0.35
            )

        self._draw_head_three_quarter(d, head_c, pose, s)

    def _draw_head_three_quarter(
        self, d: ImageDraw.ImageDraw, c: Point, pose: AlicePose, s: float
    ) -> None:
        pal = ALICE_PALETTE
        outline = pal["outline"]
        cx, cy = c
        tilt = pose.head_tilt * 0.15 * s
        # Neck and rear hair cap.
        _rounded(
            d,
            (cx - 3.8 * s, cy + 9.0 * s, cx + 3.8 * s, cy + 16.0 * s),
            radius=2.0 * s,
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.8 * s),
        )
        _ellipse(
            d,
            _bbox(cx - 1.5 * s, cy - 1.0 * s, 27.0 * s, 30.0 * s),
            fill=pal["hair"],
            outline=outline,
            width=round(1.1 * s),
        )
        # Face oval shifted camera-right.
        _ellipse(
            d,
            _bbox(cx + 2.0 * s, cy + 1.0 * s, 21.0 * s, 25.0 * s),
            fill=pal["skin"],
            outline=outline,
            width=round(1.0 * s),
        )
        # Ear and side lock.
        _ellipse(
            d,
            _bbox(cx - 8.2 * s, cy + 1.5 * s, 4.3 * s, 6.0 * s),
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.8 * s),
        )
        fringe = [
            (cx - 11.0 * s, cy - 10.0 * s),
            (cx + 10.0 * s, cy - 11.0 * s),
            (cx + 4.0 * s, cy - 2.5 * s),
            (cx - 2.0 * s, cy - 5.2 * s),
            (cx - 7.5 * s, cy + 1.5 * s),
        ]
        # Fill the fringe into the rear hair mass without outlining the shared
        # edge.  A full polygon outline used to leave a cap/bangs seam that
        # could read as a transparent gap after downsampling.
        d.polygon([(round(x), round(y)) for x, y in fringe], fill=pal["hair"])
        _line(
            d,
            [fringe[1], fringe[2], fringe[3], fringe[4]],
            fill=outline,
            width=round(1.0 * s),
        )
        _poly(
            d,
            [
                (cx - 8.0 * s, cy - 6.0 * s),
                (cx - 4.5 * s, cy - 8.5 * s),
                (cx - 5.0 * s, cy + 9.0 * s),
                (cx - 9.0 * s, cy + 7.0 * s),
            ],
            fill=pal["hair_mid"],
            outline=outline,
            width=round(0.8 * s),
        )
        _line(
            d,
            [(cx - 4.0 * s, cy - 10.0 * s), (cx + 5.0 * s, cy - 9.0 * s)],
            fill=pal["hair_light"],
            width=round(1.2 * s),
        )
        # Hair tie / survey pin at braid root.
        _ellipse(
            d,
            _bbox(cx - 9.5 * s, cy - 8.0 * s, 4.0 * s, 4.0 * s),
            fill=pal["amber"],
            outline=outline,
            width=round(0.7 * s),
        )

        eye_y = cy - 0.5 * s + tilt
        if pose.blink:
            _line(
                d,
                [(cx - 2.8 * s, eye_y), (cx + 0.2 * s, eye_y + 0.2 * s)],
                fill=outline,
                width=round(1.0 * s),
            )
            _line(
                d,
                [(cx + 5.2 * s, eye_y - 0.2 * s), (cx + 8.1 * s, eye_y - 0.4 * s)],
                fill=outline,
                width=round(1.0 * s),
            )
        else:
            for ex, scale in ((cx - 1.2 * s, 1.0), (cx + 6.5 * s, 0.92)):
                _ellipse(
                    d,
                    _bbox(ex, eye_y, 3.4 * scale * s, 2.4 * s),
                    fill=pal["white"],
                    outline=outline,
                    width=round(0.6 * s),
                )
                _ellipse(
                    d,
                    _bbox(ex + 0.45 * s, eye_y, 1.35 * s, 1.7 * s),
                    fill=pal["eye"],
                    outline=outline,
                    width=round(0.35 * s),
                )
        # Assertive eyebrows, with the camera-near one slightly raised.
        _line(
            d,
            [(cx - 3.0 * s, cy - 4.2 * s + tilt), (cx + 0.2 * s, cy - 4.7 * s + tilt)],
            fill=outline,
            width=round(1.2 * s),
        )
        _line(
            d,
            [(cx + 4.6 * s, cy - 4.8 * s + tilt), (cx + 8.5 * s, cy - 5.4 * s + tilt)],
            fill=outline,
            width=round(1.2 * s),
        )
        # Nose, cheek plane, and a small confident half-smile.
        _line(
            d,
            [
                (cx + 3.4 * s, cy + 0.3 * s),
                (cx + 4.4 * s, cy + 3.0 * s),
                (cx + 3.0 * s, cy + 3.2 * s),
            ],
            fill=pal["skin_shadow"],
            width=round(0.8 * s),
        )
        _line(
            d,
            [
                (cx + 2.0 * s, cy + 7.0 * s),
                (cx + 5.0 * s, cy + 7.4 * s),
                (cx + 7.0 * s, cy + 6.5 * s),
            ],
            fill=outline,
            width=round(0.9 * s),
        )
        _line(
            d,
            [(cx + 5.8 * s, cy + 7.5 * s), (cx + 7.2 * s, cy + 6.7 * s)],
            fill=pal["route"],
            width=round(0.6 * s),
        )

    # ------------------------------------------------------------------
    # Front view for dialogue

    def _draw_front(
        self,
        image: Image.Image,
        cx: float,
        feet_y: float,
        spec: AliceSpec,
        pose: AlicePose,
        s: float,
    ) -> None:
        d = ImageDraw.Draw(image)
        pal = ALICE_PALETTE
        outline = pal["outline"]
        boot_top = feet_y - spec.boot_h * s
        shin_top = boot_top - spec.shin_h * s
        hip_y = shin_top - spec.thigh_h * s
        shoulder_y = hip_y - spec.torso_h * s
        head_c = (cx, shoulder_y - 11.5 * s)

        # Ponytail peeks behind one shoulder in the front view.
        points = [
            (cx - 10.0 * s - i * 0.8 * s, head_c[1] - 3.0 * s + i * 5.2 * s)
            for i in range(spec.pony_segments)
        ]
        self._draw_braid(d, points, s)

        # Legs and boots.
        for sign in (-1, 1):
            x = cx + sign * 5.5 * s
            _poly(
                d,
                [
                    (x - 3.7 * s, hip_y),
                    (x + 3.7 * s, hip_y),
                    (x + 3.0 * s, boot_top),
                    (x - 3.0 * s, boot_top),
                ],
                fill=pal["trouser"] if sign > 0 else pal["trouser_dark"],
                outline=outline,
                width=round(1.0 * s),
            )
            _rounded(
                d,
                (x - 5.0 * s, boot_top - 1.0 * s, x + 5.0 * s, feet_y),
                radius=2.3 * s,
                fill=pal["boot"],
                outline=outline,
                width=round(1.0 * s),
            )
            _line(
                d,
                [(x - 4.0 * s, boot_top + 2.0 * s), (x + 4.0 * s, boot_top + 2.0 * s)],
                fill=pal["boot_light"],
                width=round(1.3 * s),
            )

        # Back arm cradles the route folio.
        left_sh = (cx - 12.0 * s, shoulder_y + 4.0 * s)
        left_elbow = (cx - 15.0 * s, shoulder_y + 18.0 * s)
        left_hand = (cx - 9.5 * s, hip_y + 1.5 * s)
        _line(d, [left_sh, left_elbow, left_hand], fill=outline, width=round(8.0 * s))
        _line(
            d,
            [left_sh, left_elbow, left_hand],
            fill=pal["jacket_dark"],
            width=round(6.0 * s),
        )
        _ellipse(
            d,
            _bbox(left_hand[0], left_hand[1], 5.0 * s, 5.0 * s),
            fill=pal["skin"],
            outline=outline,
            width=round(0.8 * s),
        )
        self._draw_map_folio(
            d, left_hand[0] - 2.0 * s, left_hand[1] + 2.0 * s, s, angle_hint=-0.2
        )

        # Clockwise, non-self-intersecting jacket silhouette.  The former
        # point order doubled back across the upper torso, cutting a literal
        # transparent triangle into every raised-hand talk pose.  Mild chest
        # fullness and waist taper keep the body human without exaggeration.
        torso = [
            (cx - 13.5 * s, shoulder_y),
            (cx + 13.5 * s, shoulder_y),
            (cx + 12.9 * s, shoulder_y + 8.5 * s),
            (cx + 10.4 * s, shoulder_y + 19.0 * s),
            (cx + 11.5 * s, hip_y),
            (cx - 11.5 * s, hip_y),
            (cx - 10.4 * s, shoulder_y + 19.0 * s),
            (cx - 12.9 * s, shoulder_y + 8.5 * s),
        ]
        _poly(d, torso, fill=pal["jacket"], outline=outline, width=round(1.2 * s))
        _poly(
            d,
            [
                (cx - 6.8 * s, shoulder_y),
                (cx + 6.8 * s, shoulder_y),
                (cx + 3.0 * s, shoulder_y + 8.0 * s),
                (cx - 3.0 * s, shoulder_y + 8.0 * s),
            ],
            fill=pal["shirt"],
            outline=outline,
            width=round(0.9 * s),
        )
        _line(
            d,
            [(cx - 8.0 * s, shoulder_y + 2.0 * s), (cx + 8.0 * s, hip_y - 2.0 * s)],
            fill=pal["leather_dark"],
            width=round(4.0 * s),
        )
        _line(
            d,
            [(cx - 8.0 * s, shoulder_y + 2.0 * s), (cx + 8.0 * s, hip_y - 2.0 * s)],
            fill=pal["leather"],
            width=round(2.0 * s),
        )
        _line(
            d,
            [(cx + 7.5 * s, shoulder_y + 3.0 * s), (cx - 1.0 * s, hip_y - 1.5 * s)],
            fill=pal["amber"],
            width=round(1.7 * s),
        )
        # Author one shallow, continuous tailoring contour through a shared
        # helper.  The same cue is used by every front and three-quarter frame,
        # so it cannot blink in and out as the animation changes pose.
        self._draw_front_bust_seam(d, cx, shoulder_y, s)
        _rounded(
            d,
            (cx - 12.0 * s, hip_y - 3.0 * s, cx + 12.0 * s, hip_y + 2.0 * s),
            radius=1.5 * s,
            fill=pal["leather_dark"],
            outline=outline,
            width=round(0.8 * s),
        )
        self._draw_cipher_tape(d, cx + 3.2 * s, shoulder_y + 10.0 * s, s)
        self._draw_compass(d, cx + 9.0 * s, hip_y + 3.0 * s, s)

        # Talking hand: open palm and changing height make the animation legible.
        right_sh = (cx + 12.0 * s, shoulder_y + 4.0 * s)
        right_elbow = (cx + 17.0 * s, shoulder_y + 16.0 * s - 3.0 * pose.gesture * s)
        right_hand = (
            cx + 16.0 * s + 3.0 * pose.gesture * s,
            shoulder_y + 27.0 * s - 11.0 * pose.gesture * s,
        )
        _line(
            d, [right_sh, right_elbow, right_hand], fill=outline, width=round(8.0 * s)
        )
        _line(
            d,
            [right_sh, right_elbow, right_hand],
            fill=pal["jacket"],
            width=round(6.0 * s),
        )
        _ellipse(
            d,
            _bbox(right_hand[0], right_hand[1], 6.0 * s, 5.0 * s),
            fill=pal["skin"],
            outline=outline,
            width=round(0.9 * s),
        )
        if pose.gesture > 0.35:
            for dy in (-1.8, 0.0, 1.8):
                _line(
                    d,
                    [
                        (right_hand[0] + 1.5 * s, right_hand[1] + dy * s),
                        (right_hand[0] + 4.0 * s, right_hand[1] + dy * 0.8 * s),
                    ],
                    fill=outline,
                    width=round(0.55 * s),
                )

        self._draw_head_front(d, head_c, pose, s)

    def _draw_head_front(
        self, d: ImageDraw.ImageDraw, c: Point, pose: AlicePose, s: float
    ) -> None:
        pal = ALICE_PALETTE
        outline = pal["outline"]
        cx, cy = c
        _rounded(
            d,
            (cx - 3.8 * s, cy + 9.0 * s, cx + 3.8 * s, cy + 16.0 * s),
            radius=2.0 * s,
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.8 * s),
        )
        _ellipse(
            d,
            _bbox(cx, cy - 1.0 * s, 28.0 * s, 30.0 * s),
            fill=pal["hair"],
            outline=outline,
            width=round(1.1 * s),
        )
        _ellipse(
            d,
            _bbox(cx, cy + 1.0 * s, 22.0 * s, 25.0 * s),
            fill=pal["skin"],
            outline=outline,
            width=round(1.0 * s),
        )
        for sign in (-1, 1):
            _ellipse(
                d,
                _bbox(cx + sign * 10.8 * s, cy + 1.5 * s, 4.0 * s, 5.5 * s),
                fill=pal["skin_shadow"],
                outline=outline,
                width=round(0.7 * s),
            )
        # Asymmetric swept fringe, still recognizable from the front.
        fringe = [
            (cx - 13.0 * s, cy - 10.5 * s),
            (cx + 11.0 * s, cy - 11.0 * s),
            (cx + 4.0 * s, cy - 2.0 * s),
            (cx - 1.0 * s, cy - 5.5 * s),
            (cx - 8.5 * s, cy - 1.0 * s),
        ]
        d.polygon([(round(x), round(y)) for x, y in fringe], fill=pal["hair"])
        _line(
            d,
            [fringe[1], fringe[2], fringe[3], fringe[4]],
            fill=outline,
            width=round(1.0 * s),
        )
        _line(
            d,
            [(cx - 5.0 * s, cy - 10.2 * s), (cx + 5.0 * s, cy - 9.2 * s)],
            fill=pal["hair_light"],
            width=round(1.1 * s),
        )
        _ellipse(
            d,
            _bbox(cx - 11.0 * s, cy - 7.5 * s, 4.0 * s, 4.0 * s),
            fill=pal["amber"],
            outline=outline,
            width=round(0.7 * s),
        )

        eye_y = cy + 0.1 * s
        if pose.blink:
            for sign in (-1, 1):
                _line(
                    d,
                    [(cx + sign * 3.0 * s, eye_y), (cx + sign * 7.0 * s, eye_y)],
                    fill=outline,
                    width=round(1.0 * s),
                )
        else:
            for sign in (-1, 1):
                ex = cx + sign * 5.0 * s
                _ellipse(
                    d,
                    _bbox(ex, eye_y, 3.6 * s, 2.5 * s),
                    fill=pal["white"],
                    outline=outline,
                    width=round(0.6 * s),
                )
                _ellipse(
                    d,
                    _bbox(ex + sign * 0.25 * s, eye_y, 1.4 * s, 1.8 * s),
                    fill=pal["eye"],
                    outline=outline,
                    width=round(0.35 * s),
                )
        _line(
            d,
            [(cx - 7.0 * s, cy - 4.0 * s), (cx - 3.0 * s, cy - 4.7 * s)],
            fill=outline,
            width=round(1.2 * s),
        )
        _line(
            d,
            [(cx + 3.0 * s, cy - 4.7 * s), (cx + 7.0 * s, cy - 4.0 * s)],
            fill=outline,
            width=round(1.2 * s),
        )
        _line(
            d,
            [
                (cx, cy + 1.0 * s),
                (cx + 0.8 * s, cy + 4.0 * s),
                (cx - 0.7 * s, cy + 4.3 * s),
            ],
            fill=pal["skin_shadow"],
            width=round(0.8 * s),
        )
        mouth_y = cy + 8.0 * s
        if pose.talk_open > 0.35:
            _ellipse(
                d,
                _bbox(cx + 0.5 * s, mouth_y, 5.0 * s, (1.8 + 3.0 * pose.talk_open) * s),
                fill=outline,
                outline=outline,
                width=round(0.7 * s),
            )
            _line(
                d,
                [(cx - 1.0 * s, mouth_y + 0.2 * s), (cx + 2.0 * s, mouth_y + 0.2 * s)],
                fill=pal["route"],
                width=round(0.7 * s),
            )
        else:
            _line(
                d,
                [
                    (cx - 2.0 * s, mouth_y),
                    (cx + 1.0 * s, mouth_y + 0.5 * s),
                    (cx + 3.0 * s, mouth_y - 0.3 * s),
                ],
                fill=outline,
                width=round(0.9 * s),
            )

    # ------------------------------------------------------------------
    # Profile views

    def _draw_side(
        self,
        image: Image.Image,
        cx: float,
        feet_y: float,
        spec: AliceSpec,
        pose: AlicePose,
        s: float,
    ) -> None:
        d = ImageDraw.Draw(image)
        pal = ALICE_PALETTE
        outline = pal["outline"]

        base_boot_top = feet_y - spec.boot_h * s
        base_shin_top = base_boot_top - spec.shin_h * s
        base_hip_y = base_shin_top - spec.thigh_h * s
        body_shift_y = pose.walk_body_y * s if pose.walk_index >= 0 else 0.0
        hip_y = base_hip_y + body_shift_y
        shoulder_y = hip_y - spec.torso_h * s
        lean = 1.0 * pose.step * s if pose.walk_index >= 0 else 0.8 * pose.scan * s

        # The profile head was drifting too far in front of the ribcage.  Keep
        # the authored face geometry intact and translate the whole head/neck
        # unit backward together so the ear, neck, and shoulder stack remain
        # coherent instead of correcting those pieces independently.
        head_back = -2.8 * s
        head_c = (cx + 2.5 * s + lean + head_back, shoulder_y - 11.5 * s)

        # Ponytail trails opposite motion; idle-side hangs with a subtle sweep.
        trail = -3.2 * pose.step if pose.walk_index >= 0 else -1.5 - 1.2 * pose.scan
        points = [
            (
                head_c[0] - 9.0 * s + trail * (i + 1) * 0.32 * s,
                head_c[1] - 6.0 * s + i * 5.0 * s,
            )
            for i in range(spec.pony_segments)
        ]
        self._draw_braid(d, points, s)

        # Alice faces screen-right, so her LEFT arm is the far/back arm.  Draw
        # it before both the map tube and torso; it must never pop in front of
        # the body as the walk cycles.  Both arms use the same stable
        # screen-left elbow bend, avoiding the old inside-out joint poses.
        # The shoulder joints sit under and slightly behind the neck.  Keeping
        # them back prevents the profile from looking hunched or as though the
        # arms have been pasted onto the front of the ribcage.
        # The shoulder correction is a rigid translation of the complete
        # arm chain.  In particular, idle-side targets must move with the
        # shoulder; otherwise IK pulls the elbow and hand back toward the old
        # forward location and makes the arm look detached.
        # The far/back arm was pushed too far toward screen-left.  Bring its
        # complete chain forward (screen-right) while leaving it behind the
        # torso in z-order.  Shoulder, elbow solution, and hand target all use
        # the same offset, so the arm remains connected.
        far_arm_back = -1.4 * s
        far_shoulder = (cx - 3.8 * s + lean + far_arm_back, shoulder_y + 4.0 * s)
        if pose.walk_index >= 0:
            far_swing = -pose.step
            far_target = (
                far_shoulder[0] + far_swing * 7.6 * s,
                shoulder_y + 26.0 * s,
            )
        else:
            far_target = (cx - 4.0 * s + lean + far_arm_back, hip_y + 1.0 * s)
        far_elbow, far_hand = self._solve_two_bone_joint(
            far_shoulder,
            far_target,
            13.2 * s,
            13.0 * s,
            bend_sign=-1.0,
        )
        self._draw_two_bone_limb(
            d,
            far_shoulder,
            far_elbow,
            far_hand,
            s,
            fill=pal["jacket_dark"],
            width=5.5,
        )
        _ellipse(
            d,
            _bbox(far_hand[0], far_hand[1], 4.6 * s, 4.6 * s),
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.8 * s),
        )

        # Map tube sits on top of the far arm but behind the torso.
        _rounded(
            d,
            (
                cx - 12.0 * s + lean,
                shoulder_y + 5.0 * s,
                cx - 5.0 * s + lean,
                hip_y + 14.0 * s,
            ),
            radius=3.0 * s,
            fill=pal["leather_dark"],
            outline=outline,
            width=round(1.0 * s),
        )
        _line(
            d,
            [
                (cx - 10.2 * s + lean, shoulder_y + 8.0 * s),
                (cx - 7.0 * s + lean, hip_y + 10.0 * s),
            ],
            fill=pal["amber"],
            width=round(1.0 * s),
        )

        # PCA-inspired eight-pose ankle targets.  The targets encode contact,
        # down, passing, and up poses; two-bone IK keeps the leg lengths fixed
        # and ensures both knees continue to bend toward screen-right.
        if pose.walk_index >= 0:
            index = pose.walk_index % 8
            leg_len = (spec.thigh_h + spec.shin_h) * s
            stride = leg_len * 0.285
            lift_scale = leg_len * 0.145
            far_x = (-0.82, -0.46, 0.04, 0.48, 0.62, 0.37, -0.10, -0.60)
            near_x = (0.95, 0.50, 0.02, -0.43, -0.56, -0.30, 0.14, 0.64)
            far_lift = (0.00, 0.00, 0.28, 0.08, 0.00, 1.00, 0.42, 0.10)
            near_lift = (0.00, 0.35, 1.00, 0.12, 0.00, 0.00, 0.25, 0.06)
            far_roll = (-0.5, -0.1, 0.3, 0.7, 0.2, -0.8, -0.3, 0.0)
            near_roll = (0.2, -0.8, -0.3, 0.0, -0.5, -0.1, 0.3, 0.7)
            far_ground = feet_y - far_lift[index] * lift_scale
            near_ground = feet_y - near_lift[index] * lift_scale
            far_ankle_target = (
                cx + far_x[index] * stride + lean,
                far_ground - 10.5 * s,
            )
            near_ankle_target = (
                cx + near_x[index] * stride + lean,
                near_ground - 10.5 * s,
            )
            far_foot_roll = far_roll[index]
            near_foot_roll = near_roll[index]
        else:
            far_ground = feet_y
            near_ground = feet_y
            far_ankle_target = (cx - 1.6 * s + lean, feet_y - 10.5 * s)
            near_ankle_target = (cx + 2.2 * s + lean, feet_y - 10.5 * s)
            far_foot_roll = 0.0
            near_foot_roll = 0.0

        far_hip = (cx - 1.4 * s + lean, hip_y)
        near_hip = (cx + 2.0 * s + lean, hip_y)
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

        # Explicit far-then-near leg ordering keeps ownership stable through
        # crossover frames.  Both remain behind the jacket/belt at the hips.
        self._draw_two_bone_limb(
            d,
            far_hip,
            far_knee,
            far_ankle,
            s,
            fill=pal["trouser_dark"],
            width=6.0,
        )
        self._draw_side_boot(
            d,
            far_ankle,
            far_ground,
            s,
            near=False,
            foot_roll=far_foot_roll,
        )
        self._draw_two_bone_limb(
            d,
            near_hip,
            near_knee,
            near_ankle,
            s,
            fill=pal["trouser"],
            width=6.2,
        )
        self._draw_side_boot(
            d,
            near_ankle,
            near_ground,
            s,
            near=True,
            foot_roll=near_foot_roll,
        )

        # Draw the complete profile head before the jacket.  The jacket then
        # owns the shoulder seam and covers the bottom of the neck/hair mass,
        # which is the physically correct profile layering.  The face remains
        # unobscured because it terminates above the shoulder line.
        self._draw_head_side(d, head_c, pose, s)

        # Jacket profile.
        # Profile jacket: shoulder back beneath the neck, then a tiny forward
        # chest curve, under-bust return, waist, and hip.  The change is only a
        # few source pixels so Alice remains compact and athletic rather than
        # becoming stylized around her bust.
        torso = [
            (cx - 6.2 * s + lean, shoulder_y),
            (cx + 4.6 * s + lean, shoulder_y + 1.0 * s),
            (cx + 6.8 * s + lean, shoulder_y + 5.5 * s),
            (cx + 8.2 * s + lean, shoulder_y + 10.8 * s),
            (cx + 7.1 * s + lean, shoulder_y + 15.3 * s),
            (cx + 5.7 * s + lean, shoulder_y + 20.5 * s),
            (cx + 7.6 * s + lean, hip_y),
            (cx - 5.2 * s + lean, hip_y),
        ]
        _poly(d, torso, fill=pal["jacket"], outline=outline, width=round(1.2 * s))
        _poly(
            d,
            [
                (cx + 2.0 * s + lean, shoulder_y),
                (cx + 5.8 * s + lean, shoulder_y + 1.0 * s),
                (cx + 4.0 * s + lean, shoulder_y + 8.0 * s),
            ],
            fill=pal["shirt"],
            outline=outline,
            width=round(0.9 * s),
        )
        _line(
            d,
            [
                (cx - 4.0 * s + lean, shoulder_y + 2.0 * s),
                (cx + 7.0 * s + lean, hip_y - 1.0 * s),
            ],
            fill=pal["leather_dark"],
            width=round(4.0 * s),
        )
        _line(
            d,
            [
                (cx - 4.0 * s + lean, shoulder_y + 2.0 * s),
                (cx + 7.0 * s + lean, hip_y - 1.0 * s),
            ],
            fill=pal["leather"],
            width=round(2.0 * s),
        )
        _line(
            d,
            [
                (cx + 7.0 * s + lean, shoulder_y + 7.0 * s),
                (cx + 6.2 * s + lean, hip_y - 4.0 * s),
            ],
            fill=pal["jacket_light"],
            width=round(1.0 * s),
        )
        _rounded(
            d,
            (
                cx - 6.0 * s + lean,
                hip_y - 3.0 * s,
                cx + 9.0 * s + lean,
                hip_y + 2.0 * s,
            ),
            radius=1.4 * s,
            fill=pal["leather_dark"],
            outline=outline,
            width=round(0.8 * s),
        )
        self._draw_compass(d, cx + 8.0 * s + lean, hip_y + 3.0 * s, s * 0.85)

        # Near/right arm stays in front of the torso.  It shares the same
        # backward elbow solution as the far arm, while the hand target swings
        # opposite the near leg.  idle_side raises the folio without inverting
        # the elbow.
        # The near/front arm still sat too far toward Alice's chest.  Move its
        # complete chain farther toward screen-left (her back).  This offset is
        # intentionally independent of the far arm: profile overlap needs the
        # far arm slightly forward and the near arm slightly back.
        near_arm_back = -7.2 * s
        near_shoulder = (cx + 7.0 * s + lean + near_arm_back, shoulder_y + 4.0 * s)
        if pose.walk_index >= 0:
            near_target = (
                near_shoulder[0] + pose.step * 8.0 * s,
                shoulder_y + 26.0 * s,
            )
        else:
            near_target = (
                cx + 14.0 * s + lean + near_arm_back,
                shoulder_y + 21.0 * s - pose.scan * 2.0 * s,
            )
        near_elbow, near_hand = self._solve_two_bone_joint(
            near_shoulder,
            near_target,
            13.5 * s,
            13.0 * s,
            bend_sign=-1.0,
        )
        self._draw_two_bone_limb(
            d,
            near_shoulder,
            near_elbow,
            near_hand,
            s,
            fill=pal["jacket"],
            width=6.0,
        )
        _ellipse(
            d,
            _bbox(near_hand[0], near_hand[1], 5.2 * s, 5.2 * s),
            fill=pal["skin"],
            outline=outline,
            width=round(0.9 * s),
        )
        if pose.walk_index < 0:
            self._draw_map_folio(
                d,
                near_hand[0] + 3.2 * s,
                near_hand[1] - 1.5 * s,
                s * 0.9,
                angle_hint=0.25,
            )

    def _draw_head_side(
        self, d: ImageDraw.ImageDraw, c: Point, pose: AlicePose, s: float
    ) -> None:
        pal = ALICE_PALETTE
        outline = pal["outline"]
        cx, cy = c
        _rounded(
            d,
            (cx - 3.5 * s, cy + 9.0 * s, cx + 3.5 * s, cy + 16.0 * s),
            radius=2.0 * s,
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.8 * s),
        )
        # Restore the full rear skull mass from the earlier profile.  The
        # previous polish accidentally narrowed the crown/back of the head
        # while trying to repair only the lower hair edge.  Keep the generous
        # rear silhouette and fix the actual problem at the nape instead.
        _ellipse(
            d,
            _bbox(cx - 3.0 * s, cy - 1.0 * s, 25.0 * s, 29.0 * s),
            fill=pal["hair"],
            outline=outline,
            width=round(1.1 * s),
        )

        # Fix only the lower side lock.  It falls nearly vertically behind the
        # ear and neck, then disappears beneath the jacket.  It is painted
        # before the face so the cheek/jaw cleanly own the foreground edge;
        # there is no forward hook that can curl back into or eat the head.
        nape_drape = [
            (cx - 8.2 * s, cy - 5.0 * s),
            (cx - 5.0 * s, cy - 6.4 * s),
            (cx - 4.8 * s, cy + 4.8 * s),
            (cx - 5.8 * s, cy + 10.5 * s),
            (cx - 7.8 * s, cy + 12.5 * s),
            (cx - 9.0 * s, cy + 6.0 * s),
        ]
        d.polygon([(round(x), round(y)) for x, y in nape_drape], fill=pal["hair_mid"])
        _line(
            d,
            [nape_drape[1], nape_drape[2], nape_drape[3], nape_drape[4]],
            fill=outline,
            width=round(0.8 * s),
        )

        # The face cuts cleanly across the front of the rear hair mass.  Its
        # rear cheek/jaw points remain far enough back that the cranium reads
        # as full rather than flattened.
        face = [
            (cx - 7.0 * s, cy - 9.5 * s),
            (cx + 6.0 * s, cy - 8.0 * s),
            (cx + 8.5 * s, cy - 2.0 * s),
            (cx + 12.0 * s, cy + 0.5 * s),
            (cx + 8.5 * s, cy + 3.0 * s),
            (cx + 9.5 * s, cy + 6.0 * s),
            (cx + 5.0 * s, cy + 10.5 * s),
            (cx - 5.5 * s, cy + 8.0 * s),
            (cx - 8.0 * s, cy),
        ]
        _poly(d, face, fill=pal["skin"], outline=outline, width=round(1.0 * s))

        # Ear remains visible between the swept fringe and the rear drape.
        _ellipse(
            d,
            _bbox(cx - 5.6 * s, cy + 0.5 * s, 3.5 * s, 5.2 * s),
            fill=pal["skin_shadow"],
            outline=outline,
            width=round(0.65 * s),
        )

        # Bangs overlap the crown by several pixels.  Only the exposed lower
        # hairline gets an outline, so there is no cap seam or alpha slit where
        # the fringe joins the main hair mass.
        fringe = [
            (cx - 9.5 * s, cy - 10.8 * s),
            (cx + 7.0 * s, cy - 10.3 * s),
            (cx + 3.8 * s, cy - 2.5 * s),
            (cx - 1.8 * s, cy - 5.2 * s),
            (cx - 6.7 * s, cy + 0.4 * s),
        ]
        d.polygon([(round(x), round(y)) for x, y in fringe], fill=pal["hair"])
        _line(
            d,
            [fringe[1], fringe[2], fringe[3], fringe[4]],
            fill=outline,
            width=round(1.0 * s),
        )

        _line(
            d,
            [(cx - 4.0 * s, cy - 10.0 * s), (cx + 3.0 * s, cy - 8.8 * s)],
            fill=pal["hair_light"],
            width=round(1.1 * s),
        )
        _ellipse(
            d,
            _bbox(cx - 9.0 * s, cy - 7.0 * s, 4.0 * s, 4.0 * s),
            fill=pal["amber"],
            outline=outline,
            width=round(0.7 * s),
        )

        eye = (cx + 4.8 * s, cy - 0.5 * s)
        if pose.blink:
            _line(
                d,
                [(eye[0] - 1.5 * s, eye[1]), (eye[0] + 1.8 * s, eye[1])],
                fill=outline,
                width=round(1.0 * s),
            )
        else:
            _ellipse(
                d,
                _bbox(eye[0], eye[1], 3.5 * s, 2.4 * s),
                fill=pal["white"],
                outline=outline,
                width=round(0.6 * s),
            )
            _ellipse(
                d,
                _bbox(eye[0] + 0.5 * s, eye[1], 1.4 * s, 1.8 * s),
                fill=pal["eye"],
                outline=outline,
                width=round(0.35 * s),
            )
        _line(
            d,
            [(cx + 2.5 * s, cy - 4.3 * s), (cx + 7.0 * s, cy - 5.0 * s)],
            fill=outline,
            width=round(1.2 * s),
        )
        _line(
            d,
            [(cx + 6.0 * s, cy + 7.0 * s), (cx + 9.0 * s, cy + 6.6 * s)],
            fill=outline,
            width=round(0.9 * s),
        )


__all__ = ["AliceCryptographerGenerator", "AliceSpec", "AlicePose", "AliceView"]
