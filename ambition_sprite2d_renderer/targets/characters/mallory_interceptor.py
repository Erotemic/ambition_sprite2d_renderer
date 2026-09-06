"""Bespoke procedural sprite target for Mallory, the active interceptor.

This is the polished successor to the stronger pre-SVG design.  Mallory's
identity is carried by her silhouette, oxblood ponytail, asymmetric field
jacket, crossed routing seams, and precise body language.  She does not depend
on a handheld board, stylus, weapon, or other prop.

The renderer is Python/Pillow only.  It never paints a ground ellipse, drop
shadow, blur, glow, generated-image asset, or SVG-derived sprite.  Layer order
is explicit, both arms stay above the torso, the walking ponytail always trails
screen-left, and a fixed design transform keeps every pose comfortably inside
the 128x128 gameplay frame.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from ...profiling import profile
from ...authoring.generator import CharacterGenerator
from ...registry import CharacterJob
from ambition_sprite2d_renderer.core.draw import rgba
from ambition_sprite2d_renderer.core.draw import blending_draw

Color = Tuple[int, int, int, int]
Point = Tuple[float, float]
BASE_SIZE = 128
DESIGN_SCALE = 0.92
DESIGN_CENTER: Point = (64.0, 66.0)

MALLORY_PALETTE: Dict[str, Color] = {
    "outline": rgba("#100B0D"),
    "black": rgba("#17171B"),
    "black_mid": rgba("#26262C"),
    "black_light": rgba("#3A3B43"),
    "oxblood_dark": rgba("#4E111B"),
    "oxblood": rgba("#8E2635"),
    "oxblood_light": rgba("#C44755"),
    "skin": rgba("#D6A38B"),
    "skin_shadow": rgba("#A97462"),
    "skin_light": rgba("#E8BDA7"),
    "chrome_dark": rgba("#555D66"),
    "chrome": rgba("#AAB4BC"),
    "chrome_light": rgba("#E5ECEE"),
    "route_a": rgba("#53BFD1"),
    "route_b": rgba("#E3B351"),
    "rewrite": rgba("#E14B58"),
    "boot": rgba("#111115"),
    "eye": rgba("#27353A"),
    "white": rgba("#F6EDE5"),
}

# Painter order is a hard contract.  Hair stays behind the body, while both
# complete arms and both hands stay above the torso in every animation.
LAYER_Z: Dict[str, int] = {
    "ponytail_back": 10,
    "jacket_tails": 20,
    "legs": 30,
    "torso": 40,
    "head": 50,
    "far_arm": 60,
    "near_arm": 70,
    "hands": 80,
    "details": 90,
}

LAYER_RELATIONS: Tuple[Tuple[str, str], ...] = (
    ("jacket_tails", "ponytail_back"),
    ("torso", "legs"),
    ("head", "torso"),
    ("far_arm", "torso"),
    ("near_arm", "torso"),
    ("near_arm", "far_arm"),
    ("hands", "near_arm"),
    ("hands", "far_arm"),
    ("details", "hands"),
)


def _validate_layer_z(layer_z: Mapping[str, int]) -> None:
    if set(layer_z) != set(LAYER_Z):
        raise ValueError(
            f"Mallory layer set changed: expected={sorted(LAYER_Z)}, "
            f"got={sorted(layer_z)}"
        )
    values = list(layer_z.values())
    if len(values) != len(set(values)):
        raise ValueError("every Mallory layer must have a unique z value")
    for upper, lower in LAYER_RELATIONS:
        if layer_z[upper] <= layer_z[lower]:
            raise ValueError(
                f"Mallory layer contract requires {upper!r} above {lower!r}"
            )


_validate_layer_z(LAYER_Z)


@dataclass(frozen=True)
class MallorySpec:
    target: str
    seed: int
    archetype: str
    name: str
    role: str
    palette_name: str = "mallory_interceptor"


@dataclass(frozen=True)
class MalloryPose:
    animation: str
    phase: float
    root_x: float = 0.0
    root_y: float = 0.0
    bob: float = 0.0
    lean: float = 0.0
    head_tilt: float = 0.0
    side_view: float = 0.0
    step: float = 0.0
    ponytail_sway: float = 0.0
    coat_sway: float = 0.0
    blink: bool = False
    mouth_open: float = 0.0
    gesture: float = 0.0
    intercept: float = 0.0
    guard: float = 0.0


@dataclass(frozen=True)
class FaceGeometry:
    """Inspectable facial landmarks for anatomy and visual-regression tests."""

    profile: bool
    center: Point
    eyes: Tuple[Point, ...]
    brows: Tuple[Tuple[Point, Point], ...]
    nose: Tuple[Point, Point]
    mouth: Point


class VDraw:
    """Vector-like drawing facade in 128-pixel design coordinates."""

    def __init__(self, image: Image.Image, scale: float) -> None:
        self.image = image
        self.scale = scale
        self.draw = blending_draw(image)

    def p(self, point: Point) -> Point:
        cx, cy = DESIGN_CENTER
        x = cx + (point[0] - cx) * DESIGN_SCALE
        y = cy + (point[1] - cy) * DESIGN_SCALE
        return (x * self.scale, y * self.scale)

    def d(self, value: float) -> float:
        return value * self.scale * DESIGN_SCALE

    def polygon(
        self,
        points: Sequence[Point],
        fill: Color,
        outline: Optional[Color] = None,
        width: float = 1.0,
    ) -> None:
        pts = [self.p(point) for point in points]
        self.draw.polygon(pts, fill=fill)
        if outline is not None:
            self.draw.line(
                [*pts, pts[0]],
                fill=outline,
                width=max(1, round(self.d(width))),
                joint="curve",
            )

    def line(
        self,
        points: Iterable[Point],
        fill: Color,
        width: float,
        joint: str = "curve",
    ) -> None:
        self.draw.line(
            [self.p(point) for point in points],
            fill=fill,
            width=max(1, round(self.d(width))),
            joint=joint,
        )

    def ellipse(
        self,
        center: Point,
        width: float,
        height: float,
        fill: Color,
        outline: Optional[Color] = None,
        stroke: float = 1.0,
    ) -> None:
        cx, cy = self.p(center)
        w = self.d(width)
        h = self.d(height)
        self.draw.ellipse(
            (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2),
            fill=fill,
            outline=outline,
            width=max(1, round(self.d(stroke))),
        )

    def rounded(
        self,
        center: Point,
        width: float,
        height: float,
        radius: float,
        fill: Color,
        outline: Optional[Color] = None,
        stroke: float = 1.0,
    ) -> None:
        cx, cy = self.p(center)
        w = self.d(width)
        h = self.d(height)
        self.draw.rounded_rectangle(
            (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2),
            radius=max(1, round(self.d(radius))),
            fill=fill,
            outline=outline,
            width=max(1, round(self.d(stroke))),
        )

    def capsule(
        self,
        start: Point,
        end: Point,
        radius: float,
        fill: Color,
        outline: Color,
        stroke: float = 1.0,
    ) -> None:
        self.line([start, end], outline, radius * 2.0 + stroke * 2.0)
        self.ellipse(
            start,
            radius * 2.0 + stroke * 2.0,
            radius * 2.0 + stroke * 2.0,
            outline,
        )
        self.ellipse(
            end,
            radius * 2.0 + stroke * 2.0,
            radius * 2.0 + stroke * 2.0,
            outline,
        )
        self.line([start, end], fill, radius * 2.0)
        self.ellipse(start, radius * 2.0, radius * 2.0, fill)
        self.ellipse(end, radius * 2.0, radius * 2.0, fill)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smoothstep(value: float) -> float:
    t = _clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def _add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def _sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def _mul(a: Point, factor: float) -> Point:
    return (a[0] * factor, a[1] * factor)


def _norm(a: Point) -> Point:
    length = math.hypot(a[0], a[1])
    if length < 1e-6:
        return (1.0, 0.0)
    return (a[0] / length, a[1] / length)


def _perp(a: Point) -> Point:
    return (-a[1], a[0])


def _rotate(point: Point, degrees: float) -> Point:
    radians = math.radians(degrees)
    c = math.cos(radians)
    s = math.sin(radians)
    return (point[0] * c - point[1] * s, point[0] * s + point[1] * c)


def _pose(animation: str, frame_index: int, frame_count: int) -> MalloryPose:
    phase = frame_index / float(max(1, frame_count))
    wave = math.sin(phase * math.tau)
    wave2 = math.sin(phase * math.tau * 2.0)

    if animation == "idle":
        return MalloryPose(
            animation=animation,
            phase=phase,
            bob=-0.35 * math.cos(phase * math.tau * 2.0),
            lean=-0.4 + 0.25 * wave,
            head_tilt=0.8 * wave,
            ponytail_sway=0.8 * wave,
            coat_sway=-0.45 * wave,
            blink=frame_index == frame_count - 2,
            guard=0.18 + 0.08 * wave2,
        )

    if animation == "walk":
        return MalloryPose(
            animation=animation,
            phase=phase,
            bob=-1.05 * abs(wave),
            lean=4.0,
            head_tilt=-1.2,
            side_view=1.0,
            step=wave,
            # Negative values reinforce screen-left trailing on acceleration.
            ponytail_sway=-2.8 - 2.2 * max(0.0, wave),
            coat_sway=4.0 * wave,
            guard=0.0,
        )

    if animation == "talk":
        gesture = math.sin(phase * math.pi)
        return MalloryPose(
            animation=animation,
            phase=phase,
            bob=-0.25 * wave2,
            lean=-0.7,
            head_tilt=1.3 * wave,
            ponytail_sway=0.65 * wave,
            coat_sway=-0.5 * wave,
            blink=frame_index == frame_count - 1,
            mouth_open=1.0 if frame_index in {1, 2, 4} else 0.2,
            gesture=gesture,
            guard=0.08,
        )

    if animation == "interact":
        keys = (0.05, 0.22, 0.55, 0.88, 1.0, 0.78, 0.42, 0.14)
        focus = keys[frame_index % len(keys)]
        return MalloryPose(
            animation=animation,
            phase=phase,
            root_x=1.2 * focus,
            root_y=0.3 * focus,
            lean=0.5 + 5.0 * focus,
            head_tilt=-2.0 * focus,
            ponytail_sway=-0.6 + 1.4 * focus,
            coat_sway=-1.2 * focus,
            intercept=focus,
            guard=0.45 + 0.55 * focus,
        )

    raise KeyError(f"unsupported Mallory animation {animation!r}")


def _root(pose: MalloryPose) -> Point:
    return (pose.root_x, pose.root_y + pose.bob)


def _xf(pose: MalloryPose, point: Point, *, lean: bool = True) -> Point:
    x, y = point
    if lean:
        x += pose.lean * (1.0 - _clamp01((y - 28.0) / 90.0)) * 0.20
    root = _root(pose)
    return (x + root[0], y + root[1])




def _limb_points(pose: MalloryPose) -> Dict[str, Point]:
    if pose.animation == "walk":
        far_shoulder = _xf(pose, (56.0, 58.0))
        near_shoulder = _xf(pose, (72.0, 57.0))
        # Arms counter-swing with the legs and remain fully readable.
        far_hand = _xf(pose, (50.0 + 8.5 * pose.step, 81.0 - 2.0 * pose.step))
        near_hand = _xf(pose, (82.0 - 9.5 * pose.step, 79.0 + 2.0 * pose.step))
    elif pose.animation == "talk":
        far_shoulder = _xf(pose, (55.0, 58.0))
        near_shoulder = _xf(pose, (73.0, 58.0))
        far_hand = _xf(pose, (54.0, 83.0))
        near_hand = _xf(pose, (88.0 + 4.0 * pose.gesture, 63.0 - 10.0 * pose.gesture))
    elif pose.animation == "interact":
        focus = pose.intercept
        far_shoulder = _xf(pose, (54.0, 57.0))
        near_shoulder = _xf(pose, (75.0, 57.0))
        # One hand seals the crossed routing seams at the sternum while the
        # other redirects outward.  This is readable without a handheld prop.
        far_hand = _xf(pose, (52.0 + 12.0 * focus, 80.0 - 15.0 * focus))
        near_hand = _xf(pose, (76.0 + 15.0 * focus, 78.0 - 12.0 * focus))
    else:
        far_shoulder = _xf(pose, (54.0, 57.0))
        near_shoulder = _xf(pose, (75.0, 57.0))
        far_hand = _xf(pose, (56.0 - 2.0 * pose.guard, 80.0 - 4.0 * pose.guard))
        near_hand = _xf(pose, (73.0 + 3.0 * pose.guard, 78.0 - 5.0 * pose.guard))

    far_elbow = (
        (far_shoulder[0] + far_hand[0]) * 0.5 - 4.0,
        (far_shoulder[1] + far_hand[1]) * 0.5 + 2.5,
    )
    near_elbow = (
        (near_shoulder[0] + near_hand[0]) * 0.5 + 4.0,
        (near_shoulder[1] + near_hand[1]) * 0.5 + 1.5,
    )
    return {
        "far_shoulder": far_shoulder,
        "far_elbow": far_elbow,
        "far_hand": far_hand,
        "near_shoulder": near_shoulder,
        "near_elbow": near_elbow,
        "near_hand": near_hand,
    }


def _ponytail_points(pose: MalloryPose) -> Tuple[Point, ...]:
    """Return the visible ponytail centerline.

    In the right-facing walk view every point after the root must be farther
    screen-left.  This makes the silhouette invariant testable instead of
    relying on an ambiguous hair-sway sign convention.
    """

    if pose.side_view > 0.5:
        root = _xf(pose, (56.0, 31.0))
        points = [root]
        for idx in range(1, 7):
            t = idx / 6.0
            x = root[0] - 3.0 - idx * 2.35 + pose.ponytail_sway * t
            y = root[1] + 3.5 + idx * 5.4 + 1.2 * math.sin(t * math.pi)
            points.append((x, y))
        return tuple(points)

    root = _xf(pose, (55.0, 31.0))
    points = [root]
    for idx in range(1, 7):
        t = idx / 6.0
        x = root[0] - 2.0 - idx * 1.05 + pose.ponytail_sway * t
        y = root[1] + idx * 6.2
        points.append((x, y))
    return tuple(points)


def _paint_ponytail_back(v: VDraw, pose: MalloryPose) -> None:
    pal = MALLORY_PALETTE
    points = _ponytail_points(pose)
    v.line(points, pal["outline"], 7.0)
    v.line(points, pal["oxblood_dark"], 5.1)

    # A chrome tie clearly separates the hair mass from the neck and preserves
    # the old version's sharper, segmented visual rhythm.
    tie = points[1]
    v.rounded(tie, 5.5, 3.3, 0.9, pal["chrome_dark"], pal["outline"], 0.7)
    for idx, point in enumerate(points[2:], start=2):
        taper = max(3.0, 6.1 - idx * 0.45)
        v.ellipse(point, taper, taper * 0.82, pal["oxblood"], pal["outline"], 0.7)
        if idx % 2 == 0:
            v.line(
                [(point[0] - taper * 0.25, point[1] - 0.8),
                 (point[0] + taper * 0.25, point[1] + 0.5)],
                pal["oxblood_light"],
                0.65,
            )


def _paint_jacket_tails(v: VDraw, pose: MalloryPose) -> None:
    pal = MALLORY_PALETTE
    sway = pose.coat_sway
    left = [
        _xf(pose, (52.0, 79.0)),
        _xf(pose, (63.0, 80.0)),
        _xf(pose, (60.0 + sway * 0.2, 105.0)),
        _xf(pose, (48.0 + sway * 0.75, 111.0)),
        _xf(pose, (45.0 + sway, 96.0)),
    ]
    right = [
        _xf(pose, (64.0, 80.0)),
        _xf(pose, (75.0, 78.0)),
        _xf(pose, (82.0 + sway * 0.85, 105.0)),
        _xf(pose, (69.0 + sway * 0.25, 109.0)),
        _xf(pose, (64.0, 95.0)),
    ]
    v.polygon(left, pal["black_mid"], pal["outline"], 1.2)
    v.polygon(right, pal["oxblood_dark"], pal["outline"], 1.2)
    v.line([left[0], left[-1]], pal["black_light"], 0.9)
    v.line([right[0], right[-1]], pal["oxblood_light"], 0.8)


def _paint_legs(v: VDraw, pose: MalloryPose) -> None:
    pal = MALLORY_PALETTE
    step = pose.step if pose.animation == "walk" else 0.0
    far_hip = _xf(pose, (58.0, 84.0))
    near_hip = _xf(pose, (69.0, 84.0))
    far_foot = _xf(pose, (55.0 - 11.0 * step, 113.0 - 2.2 * max(0.0, step)), lean=False)
    near_foot = _xf(pose, (73.0 + 11.0 * step, 113.0 + 2.2 * min(0.0, step)), lean=False)
    far_knee = ((far_hip[0] + far_foot[0]) * 0.5 - 2.2, 97.0 + _root(pose)[1])
    near_knee = ((near_hip[0] + near_foot[0]) * 0.5 + 2.4, 97.0 + _root(pose)[1])

    for hip, knee, foot, fill in (
        (far_hip, far_knee, far_foot, pal["black"]),
        (near_hip, near_knee, near_foot, pal["black_mid"]),
    ):
        v.capsule(hip, knee, 3.4, fill, pal["outline"], 0.8)
        v.capsule(knee, foot, 3.1, fill, pal["outline"], 0.8)
        toe = (foot[0] + (5.8 if pose.side_view > 0.5 else 3.8), foot[1] + 0.2)
        v.capsule(foot, toe, 3.0, pal["boot"], pal["outline"], 0.8)
        v.line([(foot[0] - 2.0, foot[1] - 1.2), (foot[0] + 2.5, foot[1] - 1.2)], pal["chrome_dark"], 0.7)


def _paint_torso(v: VDraw, pose: MalloryPose) -> None:
    pal = MALLORY_PALETTE
    torso = [
        _xf(pose, (53.0, 53.0)),
        _xf(pose, (68.0, 51.0)),
        _xf(pose, (78.0, 57.0)),
        _xf(pose, (76.0, 81.0)),
        _xf(pose, (68.0, 87.0)),
        _xf(pose, (53.0, 84.0)),
        _xf(pose, (48.0, 62.0)),
    ]
    v.polygon(torso, pal["black"], pal["outline"], 1.4)

    # Rigid asymmetric shoulder armor and diagonal route harness.
    shoulder = [
        _xf(pose, (49.0, 57.0)),
        _xf(pose, (56.0, 50.0)),
        _xf(pose, (66.0, 52.0)),
        _xf(pose, (62.0, 60.0)),
        _xf(pose, (52.0, 63.0)),
    ]
    v.polygon(shoulder, pal["oxblood_dark"], pal["outline"], 1.0)
    v.line([_xf(pose, (55.0, 53.0)), _xf(pose, (72.0, 82.0))], pal["outline"], 5.4)
    v.line([_xf(pose, (55.0, 53.0)), _xf(pose, (72.0, 82.0))], pal["chrome_dark"], 3.5)
    v.line([_xf(pose, (55.5, 53.5)), _xf(pose, (71.5, 81.3))], pal["chrome"], 0.9)

    # Crossed routing seams are sewn into the jacket.  The cyan and gold paths
    # carry the interception motif without turning a handheld object into the
    # character's identity.
    v.line([_xf(pose, (58.0, 57.0)), _xf(pose, (68.0, 73.0))], pal["outline"], 2.5)
    v.line([_xf(pose, (58.0, 57.0)), _xf(pose, (68.0, 73.0))], pal["route_a"], 1.05)
    v.line([_xf(pose, (71.0, 57.0)), _xf(pose, (62.0, 73.0))], pal["outline"], 2.5)
    v.line([_xf(pose, (71.0, 57.0)), _xf(pose, (62.0, 73.0))], pal["route_b"], 1.05)
    splice = _xf(pose, (65.0, 68.0))
    v.rounded(splice, 4.3, 3.3, 0.7, pal["rewrite"], pal["outline"], 0.6)

    # Oxblood off-center closure and waist cinch.
    v.line([_xf(pose, (68.0, 55.0)), _xf(pose, (65.0, 82.0))], pal["oxblood"], 2.2)
    v.line([_xf(pose, (51.5, 79.0)), _xf(pose, (75.0, 79.0))], pal["outline"], 3.6)
    v.line([_xf(pose, (52.0, 79.0)), _xf(pose, (74.5, 79.0))], pal["black_light"], 2.1)
    buckle = _xf(pose, (66.0, 79.0))
    v.rounded(buckle, 5.4, 4.2, 1.0, pal["chrome"], pal["outline"], 0.8)
    v.rounded(buckle, 2.5, 1.8, 0.6, pal["black"], None)

    # High collar reinforces the precise, armored silhouette.
    v.polygon(
        [_xf(pose, (56.0, 54.0)), _xf(pose, (59.0, 43.0)), _xf(pose, (65.0, 54.0))],
        pal["black_light"],
        pal["outline"],
        1.0,
    )
    v.polygon(
        [_xf(pose, (65.0, 54.0)), _xf(pose, (70.0, 44.0)), _xf(pose, (73.0, 57.0))],
        pal["oxblood_dark"],
        pal["outline"],
        1.0,
    )


def _face_geometry(pose: MalloryPose) -> FaceGeometry:
    """Return facial landmarks without conflating hairstyle and anatomy.

    Mallory's idle, talk, and interact poses are frontal/three-quarter views and
    therefore always receive two eyes.  Only the deliberate walk-cycle profile
    is permitted to collapse to one visible eye.
    """

    center = _xf(pose, (64.0, 36.0))
    profile = pose.side_view > 0.5
    if profile:
        eye = (center[0] + 4.2, center[1] - 1.5)
        return FaceGeometry(
            profile=True,
            center=center,
            eyes=(eye,),
            brows=(((eye[0] - 2.0, eye[1] - 3.2), (eye[0] + 2.8, eye[1] - 3.8)),),
            nose=((center[0] + 7.0, center[1] + 0.2), (center[0] + 9.0, center[1] + 2.2)),
            mouth=(center[0] + 8.0, center[1] + 5.8),
        )

    # The face is slightly three-quarter-right, but still clearly binocular.
    # A wider inner gap keeps the two eyes distinct after 128px downsampling.
    left_eye = (center[0] - 3.8, center[1] - 1.35)
    right_eye = (center[0] + 4.0, center[1] - 1.15)
    return FaceGeometry(
        profile=False,
        center=center,
        eyes=(left_eye, right_eye),
        brows=(
            ((left_eye[0] - 2.0, left_eye[1] - 3.3), (left_eye[0] + 2.1, left_eye[1] - 3.7)),
            ((right_eye[0] - 2.1, right_eye[1] - 3.5), (right_eye[0] + 2.4, right_eye[1] - 4.0)),
        ),
        nose=((center[0] + 0.4, center[1] + 0.1), (center[0] + 1.2, center[1] + 3.2)),
        mouth=(center[0] + 1.0, center[1] + 6.0),
    )


def _paint_head(v: VDraw, pose: MalloryPose) -> None:
    pal = MALLORY_PALETTE
    face = _face_geometry(pose)
    center = face.center
    side = face.profile
    v.ellipse(center, 23.0 if not side else 20.0, 27.0, pal["skin"], pal["outline"], 1.4)

    # Asymmetric shaved side plus swept oxblood crest, not a helmet cap.  The
    # fringe stays above the brow line; asymmetry must never erase an eye.
    if side:
        hair = [
            (center[0] - 10.0, center[1] - 7.0),
            (center[0] - 8.0, center[1] - 13.0),
            (center[0] + 1.0, center[1] - 15.0),
            (center[0] + 8.0, center[1] - 10.0),
            (center[0] + 4.0, center[1] - 5.0),
            (center[0] - 2.0, center[1] - 7.0),
        ]
    else:
        hair = [
            (center[0] - 11.0, center[1] - 6.4),
            (center[0] - 9.0, center[1] - 13.0),
            (center[0] + 0.5, center[1] - 15.5),
            (center[0] + 8.5, center[1] - 10.0),
            (center[0] + 6.0, center[1] - 5.2),
            (center[0] + 1.0, center[1] - 6.4),
            (center[0] - 3.5, center[1] - 6.0),
        ]
    v.polygon(hair, pal["oxblood"], pal["outline"], 1.1)
    v.line([hair[1], hair[2], hair[3]], pal["oxblood_light"], 1.0)

    shaved_x = center[0] + (5.4 if not side else -4.8)
    for yoff in (-7.0, -3.0, 1.0):
        v.line(
            [(shaved_x - 1.5, center[1] + yoff), (shaved_x + 1.0, center[1] + yoff - 1.2)],
            pal["skin_shadow"],
            0.65,
        )

    # Visible ear and small chrome comm clip, away from the mouth.
    ear = (center[0] - 8.5 if side else center[0] - 9.5, center[1] + 0.8)
    v.ellipse(ear, 4.0, 5.5, pal["skin_shadow"], pal["outline"], 0.7)
    v.rounded((ear[0] - 0.2, ear[1] + 0.2), 2.2, 3.2, 0.7, pal["chrome_dark"], pal["outline"], 0.5)

    for eye, brow in zip(face.eyes, face.brows):
        if pose.blink:
            v.line([(eye[0] - 1.65, eye[1]), (eye[0] + 1.65, eye[1])], pal["outline"], 1.0)
        else:
            v.ellipse(eye, 3.5, 2.55, pal["white"], pal["outline"], 0.55)
            pupil_shift = 0.45 if side else 0.25
            v.ellipse((eye[0] + pupil_shift, eye[1]), 1.25, 1.65, pal["eye"], pal["outline"], 0.3)
        v.line(list(brow), pal["outline"], 1.05)

    # A small offset nose establishes the three-quarter head direction and
    # prevents two eyes from reading as a flat mask.
    v.line(list(face.nose), pal["skin_shadow"], 0.75)
    if not side:
        v.line(
            [(face.nose[1][0] - 0.2, face.nose[1][1]), (face.nose[1][0] + 1.1, face.nose[1][1] + 0.2)],
            pal["outline"],
            0.55,
        )

    mouth = face.mouth
    if pose.mouth_open > 0.4:
        v.ellipse(mouth, 3.7, 2.0 + 1.8 * pose.mouth_open, pal["oxblood_dark"], pal["outline"], 0.5)
    else:
        v.line([(mouth[0] - 1.8, mouth[1]), (mouth[0] + 2.0, mouth[1] - 0.4)], pal["outline"], 0.8)




def _paint_arm(v: VDraw, pose: MalloryPose, which: str) -> None:
    pal = MALLORY_PALETTE
    limbs = _limb_points(pose)
    shoulder = limbs[f"{which}_shoulder"]
    elbow = limbs[f"{which}_elbow"]
    hand = limbs[f"{which}_hand"]
    fill = pal["black_mid"] if which == "near" else pal["black"]
    cuff = pal["oxblood"] if which == "near" else pal["chrome_dark"]
    v.capsule(shoulder, elbow, 4.0, fill, pal["outline"], 0.8)
    v.capsule(elbow, hand, 3.4, fill, pal["outline"], 0.8)
    axis = _norm(_sub(hand, elbow))
    cuff_center = _add(hand, _mul(axis, -3.0))
    normal = _perp(axis)
    v.line([_add(cuff_center, _mul(normal, -3.1)), _add(cuff_center, _mul(normal, 3.1))], pal["outline"], 3.4)
    v.line([_add(cuff_center, _mul(normal, -2.6)), _add(cuff_center, _mul(normal, 2.6))], cuff, 1.9)


def _paint_hands(v: VDraw, pose: MalloryPose) -> None:
    pal = MALLORY_PALETTE
    limbs = _limb_points(pose)
    far_hand = limbs["far_hand"]
    near_hand = limbs["near_hand"]
    v.ellipse(far_hand, 6.3, 6.0, pal["skin"], pal["outline"], 0.9)
    v.ellipse(near_hand, 6.6, 6.1, pal["skin_light"], pal["outline"], 0.9)

    if pose.animation == "talk":
        # Exact two-finger explanatory gesture, not a fist or generic wave.
        v.line([near_hand, (near_hand[0] + 6.5, near_hand[1] - 5.0)], pal["outline"], 2.0)
        v.line([near_hand, (near_hand[0] + 7.0, near_hand[1] - 1.0)], pal["outline"], 2.0)
        v.line([(near_hand[0] + 0.3, near_hand[1]), (near_hand[0] + 6.2, near_hand[1] - 4.6)], pal["skin_light"], 1.0)
        v.line([(near_hand[0] + 0.3, near_hand[1] + 0.5), (near_hand[0] + 6.5, near_hand[1] - 0.7)], pal["skin_light"], 1.0)

    if pose.animation == "interact":
        # Open redirecting palm.  Fingers are short and anatomical, so the
        # silhouette cannot be mistaken for a stylus or weapon.
        spread = 2.5 + 2.5 * pose.intercept
        for idx, dy in enumerate((-2.2, 0.0, 2.2)):
            length = spread - idx * 0.25
            v.line(
                [near_hand, (near_hand[0] + length, near_hand[1] + dy)],
                pal["outline"],
                1.7,
            )
            v.line(
                [(near_hand[0] + 0.3, near_hand[1]),
                 (near_hand[0] + length - 0.3, near_hand[1] + dy)],
                pal["skin_light"],
                0.75,
            )


def _paint_details(v: VDraw, pose: MalloryPose) -> None:
    pal = MALLORY_PALETTE
    # Small integrated jacket hardware; nothing is detached or hand-held.
    for x, y in ((55.0, 68.0), (59.0, 72.0), (72.0, 66.0)):
        p = _xf(pose, (x, y))
        v.rounded(p, 2.2, 2.2, 0.5, pal["chrome"], pal["outline"], 0.45)
    v.line([_xf(pose, (51.0, 74.0)), _xf(pose, (58.0, 74.0))], pal["oxblood_light"], 0.8)

    # The rewrite clasp is intrinsic to the jacket and receives a crisp inner
    # mark at the peak of the intercept animation.  No glow or floating effect.
    if pose.intercept > 0.55:
        splice = _xf(pose, (65.0, 68.0))
        v.line(
            [(splice[0] - 1.1, splice[1]), (splice[0] + 1.1, splice[1])],
            pal["chrome_light"],
            0.7,
        )


PAINTERS: Dict[str, Callable[[VDraw, MalloryPose], None]] = {
    "ponytail_back": _paint_ponytail_back,
    "jacket_tails": _paint_jacket_tails,
    "legs": _paint_legs,
    "torso": _paint_torso,
    "head": _paint_head,
    "far_arm": lambda v, p: _paint_arm(v, p, "far"),
    "near_arm": lambda v, p: _paint_arm(v, p, "near"),
    "hands": _paint_hands,
    "details": _paint_details,
}



class MalloryInterceptorGenerator(CharacterGenerator):
    name = "mallory_interceptor"
    target = "mallory_interceptor"
    applies_job_name = True

    ANIMATIONS: Dict[str, Dict[str, int]] = {
        "idle": {"frames": 8, "duration_ms": 120},
        "walk": {"frames": 8, "duration_ms": 95},
        "talk": {"frames": 6, "duration_ms": 100},
        "interact": {"frames": 8, "duration_ms": 86},
    }

    def build_spec(self, job: CharacterJob) -> MallorySpec:
        if job.archetype != "mallory":
            raise KeyError(
                "mallory_interceptor ships only the 'mallory' archetype; "
                f"got {job.archetype!r}"
            )
        return MallorySpec(
            target=self.target,
            seed=job.seed,
            archetype=job.archetype,
            name="Mallory",
            role="npc",
        )

    def canonical_pose(self) -> Tuple[str, int]:
        return ("idle", 2)

    def body_inset(self) -> Dict[str, float]:
        # Ponytail and jacket tails are cosmetic extensions.  The fixed design
        # scale keeps them inside the gameplay frame with comfortable margins.
        return {"left": 0.10, "right": 0.10, "top": 0.04, "bottom": 0.04}

    @profile
    def render_frame(
        self,
        spec: MallorySpec,
        animation: str,
        frame_index: int,
        size: Tuple[int, int],
        job: CharacterJob,
    ) -> Image.Image:
        del spec
        meta = self.animations()[animation]
        pose = _pose(animation, frame_index % meta["frames"], meta["frames"])
        supersample = max(2, int(job.render.supersample))
        source = Image.new(
            "RGBA",
            (BASE_SIZE * supersample, BASE_SIZE * supersample),
            (0, 0, 0, 0),
        )
        vector = VDraw(source, float(supersample))
        for layer_name in sorted(PAINTERS, key=LAYER_Z.__getitem__):
            PAINTERS[layer_name](vector, pose)
        resample = (
            Image.Resampling.LANCZOS
            if str(job.render.downsample).lower() == "lanczos"
            else Image.Resampling.BICUBIC
        )
        return source.resize(size, resample)


def source_uses_forbidden_raster_effects() -> bool:
    forbidden_globals = ("ImageFilter", "GaussianBlur", "BoxBlur")
    return any(name in globals() for name in forbidden_globals)


__all__ = [
    "MalloryInterceptorGenerator",
    "MallorySpec",
    "MalloryPose",
    "FaceGeometry",
    "DESIGN_SCALE",
    "_ponytail_points",
    "LAYER_Z",
    "LAYER_RELATIONS",
    "PAINTERS",
    "source_uses_forbidden_raster_effects",
]
