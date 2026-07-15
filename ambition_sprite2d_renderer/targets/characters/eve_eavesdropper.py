"""Bespoke procedural sprite target for Eve, the cryptography-crew listener.

Eve is built cloak-first rather than as a generic humanoid with accessories.
Her silhouette is a broad asymmetric aubergine drape, a deep listening hood,
and a deliberately oversized brass acoustic receiver.  Its narrow end cups
the visible ear, never the mouth; the wide collector bell points away from
her face.  Idle and interact visibly listen, walk protects and carries the
receiver, and talk lowers it to free a gesturing hand.

The renderer is Python/Pillow only.  It does not paint a ground ellipse, drop
shadow, blur, glow, or other raster effect.  Layer ordering is explicit so the
two sleeves, horn, and hands stay legible above the cloak in every pose.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.generator import CharacterGenerator
from ...registry import CharacterJob
from ambition_sprite2d_renderer.core.draw import rgba

Color = Tuple[int, int, int, int]
Point = Tuple[float, float]

BASE_SIZE = 128


EVE_PALETTE: Dict[str, Color] = {
    "outline": rgba("#120B17"),
    "cloak_deep": rgba("#21142C"),
    "cloak_dark": rgba("#34203F"),
    "cloak": rgba("#4A2D59"),
    "cloak_light": rgba("#68406E"),
    "lining": rgba("#293342"),
    "lining_light": rgba("#45556A"),
    "skin": rgba("#D5B59C"),
    "skin_shadow": rgba("#A77D67"),
    "skin_light": rgba("#E8CDB5"),
    "brass_dark": rgba("#79501D"),
    "brass": rgba("#D2A13D"),
    "brass_light": rgba("#F1D274"),
    "leather_dark": rgba("#3C2725"),
    "leather": rgba("#76503D"),
    "boot": rgba("#17121B"),
    "eye": rgba("#26363C"),
    "eye_light": rgba("#DDE9E1"),
}


# Painter ordering is part of the design, not an incidental call sequence.
# Both sleeves are above every body layer.  The horn lies over the sleeves and
# the hands close over the horn, so no pose can erase an arm or detach a grip.
LAYER_Z: Dict[str, int] = {
    "cloak_back": 10,
    "legs": 20,
    "torso_cloak": 30,
    "satchel": 38,
    "hood": 42,
    "face": 48,
    "far_arm": 60,
    "near_arm": 70,
    "horn": 78,
    "hands": 84,
    "details": 90,
}

LAYER_RELATIONS: Tuple[Tuple[str, str], ...] = (
    ("torso_cloak", "cloak_back"),
    ("hood", "torso_cloak"),
    ("face", "hood"),
    ("far_arm", "torso_cloak"),
    ("near_arm", "torso_cloak"),
    ("near_arm", "far_arm"),
    ("horn", "far_arm"),
    ("horn", "near_arm"),
    ("hands", "horn"),
    ("details", "hands"),
)


def _validate_layer_z(layer_z: Mapping[str, int]) -> None:
    if set(layer_z) != set(LAYER_Z):
        raise ValueError(
            f"Eve layer set changed: expected={sorted(LAYER_Z)}, "
            f"got={sorted(layer_z)}"
        )
    values = list(layer_z.values())
    if len(values) != len(set(values)):
        raise ValueError("every Eve layer must have a unique z value")
    for upper, lower in LAYER_RELATIONS:
        if layer_z[upper] <= layer_z[lower]:
            raise ValueError(f"Eve layer contract requires {upper!r} above {lower!r}")


_validate_layer_z(LAYER_Z)


@dataclass(frozen=True)
class EveSpec:
    target: str
    seed: int
    archetype: str
    name: str
    role: str
    palette_name: str = "eve_eavesdropper"


@dataclass(frozen=True)
class EvePose:
    animation: str
    phase: float
    root_x: float = 0.0
    root_y: float = 0.0
    body_bob: float = 0.0
    lean: float = 0.0
    head_tilt: float = 0.0
    hood_sway: float = 0.0
    cloak_sway: float = 0.0
    step: float = 0.0
    blink: bool = False
    mouth_open: float = 0.0
    listen: float = 1.0
    gesture: float = 0.0
    horn_angle: float = 192.0
    horn_reach: float = 0.0
    signal: float = 0.0
    side_view: float = 0.0


class VDraw:
    """Small vector-like drawing facade in 128-pixel design coordinates."""

    def __init__(self, image: Image.Image, scale: float) -> None:
        self.image = image
        self.scale = scale
        self.draw = ImageDraw.Draw(image)

    def p(self, point: Point) -> Point:
        return (point[0] * self.scale, point[1] * self.scale)

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
                width=max(1, round(width * self.scale)),
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
            width=max(1, round(width * self.scale)),
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
        w = width * self.scale
        h = height * self.scale
        self.draw.ellipse(
            (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2),
            fill=fill,
            outline=outline,
            width=max(1, round(stroke * self.scale)),
        )

    def arc(
        self,
        box: Tuple[float, float, float, float],
        start: float,
        end: float,
        fill: Color,
        width: float,
    ) -> None:
        self.draw.arc(
            tuple(value * self.scale for value in box),
            start=start,
            end=end,
            fill=fill,
            width=max(1, round(width * self.scale)),
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
        self.ellipse(start, radius * 2.0 + stroke * 2.0, radius * 2.0 + stroke * 2.0, outline)
        self.ellipse(end, radius * 2.0 + stroke * 2.0, radius * 2.0 + stroke * 2.0, outline)
        self.line([start, end], fill, radius * 2.0)
        self.ellipse(start, radius * 2.0, radius * 2.0, fill)
        self.ellipse(end, radius * 2.0, radius * 2.0, fill)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smoothstep(value: float) -> float:
    t = _clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


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


def _pose(animation: str, frame_index: int, frame_count: int) -> EvePose:
    phase = frame_index / float(max(1, frame_count))
    wave = math.sin(phase * math.tau)
    wave2 = math.sin(phase * math.tau * 2.0)

    if animation == "idle":
        # She scans with the horn rather than standing mechanically still.
        return EvePose(
            animation=animation,
            phase=phase,
            body_bob=-0.45 * math.cos(phase * math.tau * 2.0),
            lean=1.2 + 0.8 * wave,
            head_tilt=-1.6 * wave,
            hood_sway=0.6 * wave,
            cloak_sway=0.8 * wave,
            blink=frame_index == frame_count - 2,
            listen=1.0,
            horn_angle=192.0 + 4.0 * wave,
            horn_reach=1.5 * wave,
            signal=max(0.0, wave) * 0.45,
        )

    if animation == "walk":
        # Side-on purposeful stride. The horn is tucked across the chest so it
        # remains protected and does not become a static forward-pointing rod.
        return EvePose(
            animation=animation,
            phase=phase,
            body_bob=-1.2 * abs(wave),
            lean=5.0,
            head_tilt=-2.0,
            hood_sway=-2.2 * wave,
            cloak_sway=5.0 * wave,
            step=wave,
            blink=False,
            listen=0.0,
            horn_angle=25.0 - 6.0 * wave,
            horn_reach=-2.0,
            side_view=1.0,
        )

    if animation == "talk":
        gesture = math.sin(phase * math.pi)
        mouth = 1.0 if frame_index in {1, 2, 4} else 0.25
        return EvePose(
            animation=animation,
            phase=phase,
            body_bob=-0.35 * wave2,
            lean=-1.0,
            head_tilt=1.8 * wave,
            hood_sway=0.5 * wave,
            cloak_sway=-0.6 * wave,
            blink=frame_index == frame_count - 1,
            mouth_open=mouth,
            listen=0.0,
            gesture=gesture,
            horn_angle=42.0,
            horn_reach=-4.0,
        )

    if animation == "interact":
        # A six-frame listen action: settle, extend, commit, hold, release.
        keys = (0.10, 0.42, 0.82, 1.00, 0.72, 0.28)
        focus = keys[frame_index % len(keys)]
        return EvePose(
            animation=animation,
            phase=phase,
            root_x=2.5 * focus,
            root_y=0.8 * focus,
            body_bob=0.0,
            lean=4.0 + 8.0 * focus,
            head_tilt=-4.0 * focus,
            hood_sway=1.5 * focus,
            cloak_sway=-2.0 * focus,
            blink=False,
            listen=1.0,
            horn_angle=192.0 - 5.0 * focus,
            horn_reach=8.0 * focus,
            signal=focus,
        )

    raise KeyError(f"unsupported Eve animation {animation!r}")


def _root(pose: EvePose) -> Point:
    return (pose.root_x, pose.root_y + pose.body_bob)


def _xf(pose: EvePose, point: Point, *, body: bool = True) -> Point:
    root = _root(pose)
    x, y = point
    if body:
        # A small shear communicates lean without rotating the entire sprite
        # into clipping or making the feet float.
        x += pose.lean * (1.0 - _clamp01((y - 34.0) / 82.0)) * 0.18
    return (x + root[0], y + root[1])


def _cloak_points(pose: EvePose) -> Sequence[Point]:
    sway = pose.cloak_sway
    # The walk hem lifts and separates enough to expose the stride.  Other
    # rows keep the long, planted cloak silhouette.
    walk_lift = 4.0 if pose.animation == "walk" else 0.0
    return [
        _xf(pose, (46.0, 54.0)),
        _xf(pose, (72.0, 52.0)),
        _xf(pose, (79.0 + sway * 0.18, 69.0)),
        _xf(pose, (84.0 + sway * 0.58, 111.0 - walk_lift)),
        _xf(pose, (72.0 + sway * 0.75, 116.0 - walk_lift)),
        _xf(pose, (60.0 + sway * 0.35, 111.5 - walk_lift * 0.55)),
        _xf(pose, (45.0 - sway * 0.50, 116.0 - walk_lift)),
        _xf(pose, (38.0 - sway * 0.85, 108.0 - walk_lift * 0.45)),
        _xf(pose, (42.0 - sway * 0.42, 72.0)),
    ]


def _face_center(pose: EvePose) -> Point:
    center = _xf(pose, (65.0, 36.5))
    return _add(center, (2.0, 0.0))


def _ear_point(pose: EvePose) -> Point:
    """Return the visible listening ear, shared by face and receiver geometry."""
    face_center = _face_center(pose)
    if pose.side_view > 0.5:
        return _add(face_center, (-5.8, 0.0))
    return _add(face_center, (-8.0, 0.0))


def _mouth_point(pose: EvePose) -> Point:
    face_center = _face_center(pose)
    if pose.side_view > 0.5:
        return _add(face_center, (8.0, 5.1))
    return _add(face_center, (4.1, 5.2))


def _listening_receiver_axis(pose: EvePose) -> Tuple[Point, Point, Point]:
    """Return receiver tip, bell, and unit axis for listening poses.

    The tip is mechanically pinned to Eve's visible ear.  This is the key
    semantic distinction from a played brass instrument: the tube terminates
    at the ear and the collector opens away from the face.
    """
    tip = _ear_point(pose)
    length = 31.0 + pose.horn_reach
    axis = _norm(_rotate((1.0, 0.0), pose.horn_angle))
    bell = _add(tip, _mul(axis, length))
    return tip, bell, axis


def _limb_points(pose: EvePose) -> Dict[str, Tuple[Point, Point, Point]]:
    if pose.animation == "walk":
        carry_a = _xf(pose, (70.0, 72.0))
        carry_b = _xf(pose, (83.0, 79.0))
        return {
            "far": (_xf(pose, (49.0, 56.0)), _xf(pose, (58.0, 68.0)), carry_a),
            "near": (_xf(pose, (72.0, 56.0)), _xf(pose, (76.0, 71.0)), carry_b),
        }

    if pose.animation == "talk":
        g = pose.gesture
        return {
            "far": (
                _xf(pose, (48.0, 56.0)),
                _xf(pose, (58.0, 71.0)),
                _xf(pose, (70.0, 84.0)),
            ),
            "near": (
                _xf(pose, (72.0, 56.0)),
                _xf(pose, (82.0 + 6.0 * g, 62.0 - 7.0 * g)),
                _xf(pose, (92.0 + 10.0 * g, 67.0 - 10.0 * g)),
            ),
        }

    tip, bell, axis = _listening_receiver_axis(pose)
    cross = _perp(axis)
    length = math.hypot(bell[0] - tip[0], bell[1] - tip[1])
    # One hand seats the padded earpiece.  The other supports the collector
    # underneath, producing a listening brace rather than a musician's grip.
    ear_hand = _add(tip, _add(_mul(axis, 1.0), _mul(cross, 1.2)))
    support_hand = _add(
        tip,
        _add(_mul(axis, length * 0.64), _mul(cross, 3.2)),
    )
    focus = pose.signal if pose.animation == "interact" else 0.0
    return {
        "far": (
            _xf(pose, (48.0, 56.0)),
            _xf(pose, (49.0 + 2.0 * focus, 45.0 - 1.5 * focus)),
            ear_hand,
        ),
        "near": (
            _xf(pose, (72.0, 56.0)),
            _xf(pose, (58.0 - 2.0 * focus, 58.0 - 2.0 * focus)),
            support_hand,
        ),
    }


def _horn_ends(pose: EvePose, limbs: Mapping[str, Tuple[Point, Point, Point]]) -> Tuple[Point, Point]:
    if pose.animation == "walk":
        start = _add(limbs["far"][2], (-1.0, -1.0))
        direction = _rotate((28.0, 0.0), pose.horn_angle)
        return start, _add(start, direction)
    if pose.animation == "talk":
        start = _add(limbs["far"][2], (-1.5, 0.0))
        direction = _rotate((26.0, 0.0), pose.horn_angle)
        return start, _add(start, direction)
    tip, bell, _axis = _listening_receiver_axis(pose)
    return tip, bell


def _paint_cloak_back(v: VDraw, pose: EvePose) -> None:
    pal = EVE_PALETTE
    points = list(_cloak_points(pose))
    # Rear drape is a dark offset mass, giving the cloak thickness without a
    # cast shadow or ground treatment.
    back = [(x - 2.2, y + 0.8) for x, y in points]
    v.polygon(back, pal["cloak_deep"], pal["outline"], 1.4)
    # A small trailing hood tail breaks the otherwise circular head silhouette.
    v.polygon(
        [
            _xf(pose, (45.0, 33.0)),
            _xf(pose, (37.0 - pose.hood_sway, 47.0)),
            _xf(pose, (46.0 - pose.hood_sway * 0.3, 51.0)),
        ],
        pal["cloak_deep"],
        pal["outline"],
        1.2,
    )


def _paint_legs(v: VDraw, pose: EvePose) -> None:
    pal = EVE_PALETTE
    step = pose.step
    if pose.animation == "walk":
        far_hip = _xf(pose, (58.0, 92.0))
        far_knee = _xf(pose, (56.0 - 5.0 * step, 103.0))
        far_foot = _xf(pose, (54.0 - 10.0 * step, 117.0 - 2.0 * abs(step)))
        near_hip = _xf(pose, (68.0, 92.0))
        near_knee = _xf(pose, (69.0 + 6.0 * step, 103.0))
        near_foot = _xf(pose, (72.0 + 11.0 * step, 117.0 - 2.0 * abs(step)))
    else:
        far_hip = _xf(pose, (58.0, 93.0))
        far_knee = _xf(pose, (56.0, 105.0))
        far_foot = _xf(pose, (54.0, 117.0))
        near_hip = _xf(pose, (68.0, 93.0))
        near_knee = _xf(pose, (69.0, 105.0))
        near_foot = _xf(pose, (72.0, 117.0))
    v.capsule(far_hip, far_knee, 3.0, pal["lining"], pal["outline"], 0.8)
    v.capsule(far_knee, far_foot, 2.8, pal["lining"], pal["outline"], 0.8)
    v.ellipse(_add(far_foot, (2.0, 0.5)), 10.0, 4.5, pal["boot"], pal["outline"], 0.9)
    v.capsule(near_hip, near_knee, 3.2, pal["lining_light"], pal["outline"], 0.9)
    v.capsule(near_knee, near_foot, 3.0, pal["lining_light"], pal["outline"], 0.9)
    v.ellipse(_add(near_foot, (2.5, 0.5)), 11.0, 4.8, pal["boot"], pal["outline"], 1.0)


def _paint_torso_cloak(v: VDraw, pose: EvePose) -> None:
    pal = EVE_PALETTE
    points = list(_cloak_points(pose))
    v.polygon(points, pal["cloak"], pal["outline"], 1.5)
    # Asymmetric front overlap and a slate lining reveal make the lower body
    # read as layered fabric rather than a solid purple triangle.
    overlap = [
        _xf(pose, (61.0, 58.0)),
        _xf(pose, (76.0, 58.0)),
        _xf(pose, (79.0 + pose.cloak_sway * 0.45, 108.0)),
        _xf(pose, (68.0 + pose.cloak_sway * 0.30, 114.0)),
        _xf(pose, (63.0, 91.0)),
    ]
    v.polygon(overlap, pal["cloak_dark"], pal["outline"], 1.0)
    lining = [
        _xf(pose, (62.0, 91.0)),
        _xf(pose, (68.0 + pose.cloak_sway * 0.30, 114.0)),
        _xf(pose, (58.0 + pose.cloak_sway * 0.12, 112.0)),
    ]
    v.polygon(lining, pal["lining"], pal["outline"], 0.8)
    # Shoulder mantle.
    v.polygon(
        [
            _xf(pose, (43.0, 56.0)),
            _xf(pose, (49.0, 49.0)),
            _xf(pose, (68.0, 48.0)),
            _xf(pose, (78.0, 57.0)),
            _xf(pose, (70.0, 64.0)),
            _xf(pose, (50.0, 64.0)),
        ],
        pal["cloak_dark"],
        pal["outline"],
        1.2,
    )
    clasp = _xf(pose, (63.5, 57.0))
    v.ellipse(clasp, 5.2, 5.2, pal["brass"], pal["outline"], 0.8)
    v.ellipse(_add(clasp, (-0.7, -0.8)), 1.5, 1.5, pal["brass_light"])


def _paint_satchel(v: VDraw, pose: EvePose) -> None:
    pal = EVE_PALETTE
    strap = [_xf(pose, (49.0, 55.0)), _xf(pose, (73.0, 87.0))]
    v.line(strap, pal["leather_dark"], 2.2)
    center = _xf(pose, (77.0 + pose.cloak_sway * 0.20, 88.0))
    v.polygon(
        [
            _add(center, (-7.0, -6.0)),
            _add(center, (6.0, -5.0)),
            _add(center, (7.0, 6.0)),
            _add(center, (-6.0, 7.0)),
        ],
        pal["leather"],
        pal["outline"],
        1.0,
    )
    v.line([_add(center, (-5.0, -1.0)), _add(center, (5.0, -0.5))], pal["leather_dark"], 1.0)
    v.ellipse(_add(center, (0.0, 0.5)), 2.0, 2.0, pal["brass"])


def _paint_hood(v: VDraw, pose: EvePose) -> None:
    pal = EVE_PALETTE
    center = _xf(pose, (61.5 + pose.hood_sway * 0.25, 36.0))
    # Pointed, asymmetric hood shell.
    v.polygon(
        [
            _add(center, (-15.0, 7.0)),
            _add(center, (-13.0, -8.0)),
            _add(center, (-5.0, -18.0)),
            _add(center, (9.0, -14.0)),
            _add(center, (17.0, -2.0)),
            _add(center, (13.0, 12.0)),
            _add(center, (3.0, 17.0)),
            _add(center, (-8.0, 15.0)),
        ],
        pal["cloak_deep"],
        pal["outline"],
        1.5,
    )
    # Inner hood opening uses fabric color, not transparency, so it stays
    # readable on both light and dark game backgrounds.
    v.ellipse(_add(center, (3.0, 1.0)), 24.0, 29.0, pal["cloak_dark"], pal["outline"], 1.0)
    v.line(
        [
            _add(center, (-8.0, -7.0)),
            _add(center, (-2.0, -13.0)),
            _add(center, (7.0, -11.0)),
        ],
        pal["cloak_light"],
        1.5,
    )


def _paint_face(v: VDraw, pose: EvePose) -> None:
    pal = EVE_PALETTE
    face_center = _face_center(pose)
    if pose.side_view > 0.5:
        # Cleaner side profile for the walk row.
        v.polygon(
            [
                _add(face_center, (-7.0, -10.0)),
                _add(face_center, (5.5, -10.0)),
                _add(face_center, (9.0, -2.0)),
                _add(face_center, (12.0, 0.0)),
                _add(face_center, (8.0, 2.5)),
                _add(face_center, (6.0, 9.0)),
                _add(face_center, (-4.0, 11.0)),
                _add(face_center, (-8.0, 5.0)),
            ],
            pal["skin"],
            pal["outline"],
            1.1,
        )
        eye = _add(face_center, (4.0, -2.5))
        v.ellipse(eye, 3.0, 2.2, pal["eye"], pal["outline"], 0.4)
        v.ellipse(_add(eye, (0.7, -0.4)), 0.8, 0.8, pal["eye_light"])
        v.line([_add(face_center, (6.0, 5.0)), _add(face_center, (9.0, 5.2))], pal["outline"], 0.8)
        ear = _ear_point(pose)
        v.ellipse(ear, 3.6, 4.8, pal["skin_shadow"], pal["outline"], 0.6)
        return

    v.ellipse(face_center, 19.5, 23.5, pal["skin"], pal["outline"], 1.1)
    # The nose is a small profile wedge; enough to point the gaze without
    # turning Eve into the generic round toon face.
    v.polygon(
        [
            _add(face_center, (7.4, -1.5)),
            _add(face_center, (11.2, 0.4)),
            _add(face_center, (7.2, 2.1)),
        ],
        pal["skin"],
        pal["outline"],
        0.8,
    )
    if pose.blink:
        v.line([_add(face_center, (-4.2, -2.2)), _add(face_center, (0.2, -2.5))], pal["outline"], 1.0)
        v.line([_add(face_center, (2.8, -2.4)), _add(face_center, (6.3, -2.1))], pal["outline"], 1.0)
    else:
        for eye in (_add(face_center, (-1.5, -2.5)), _add(face_center, (4.8, -2.3))):
            v.ellipse(eye, 2.6, 2.3, pal["eye"], pal["outline"], 0.35)
            v.ellipse(_add(eye, (0.55, -0.45)), 0.7, 0.7, pal["eye_light"])
    if pose.mouth_open > 0.55:
        v.ellipse(_add(face_center, (4.0, 5.5)), 4.2, 3.2, pal["outline"])
        v.line([_add(face_center, (3.0, 5.1)), _add(face_center, (5.0, 5.1))], pal["skin_light"], 0.6)
    else:
        v.line([_add(face_center, (2.2, 5.2)), _add(face_center, (6.0, 5.0))], pal["outline"], 0.8)
    # Ear must remain visible because the horn's narrow end is placed against it.
    ear = _ear_point(pose)
    v.ellipse(ear, 3.8, 5.0, pal["skin_shadow"], pal["outline"], 0.6)
    v.arc((ear[0] - 1.0, ear[1] - 1.6, ear[0] + 1.6, ear[1] + 1.5), 250, 100, pal["skin_light"], 0.6)


def _paint_arm(v: VDraw, pose: EvePose, which: str) -> None:
    pal = EVE_PALETTE
    shoulder, elbow, hand = _limb_points(pose)[which]
    if which == "far":
        upper = pal["cloak_dark"]
        lower = pal["cloak"]
        radius = 3.4
    else:
        upper = pal["cloak_light"]
        lower = pal["cloak"]
        radius = 3.7
    v.capsule(shoulder, elbow, radius, upper, pal["outline"], 0.9)
    v.capsule(elbow, hand, radius * 0.88, lower, pal["outline"], 0.9)
    # Cuff band clarifies elbow-to-hand direction at game scale.
    cuff_center = _add(elbow, _mul(_sub(hand, elbow), 0.72))
    direction = _norm(_sub(hand, elbow))
    cross = _perp(direction)
    v.line(
        [
            _add(cuff_center, _mul(cross, -3.0)),
            _add(cuff_center, _mul(cross, 3.0)),
        ],
        pal["cloak_deep"],
        1.5,
    )


def _oval_points(
    center: Point,
    axis: Point,
    axial_radius: float,
    cross_radius: float,
    samples: int = 16,
) -> Sequence[Point]:
    """Approximate an oriented oval without any raster transforms."""
    cross = _perp(axis)
    points = []
    for index in range(samples):
        angle = math.tau * index / samples
        points.append(
            _add(
                center,
                _add(
                    _mul(axis, math.cos(angle) * axial_radius),
                    _mul(cross, math.sin(angle) * cross_radius),
                ),
            )
        )
    return points


def _paint_horn(v: VDraw, pose: EvePose) -> None:
    """Paint Eve's directional acoustic receiver.

    The old design was a continuous flared cone and therefore read as a
    trumpet.  This design separates the listening cup, bent acoustic tube,
    and oval collector dish.  In listening poses the cup is visibly seated
    on the ear and the dish opens away from the face.
    """
    pal = EVE_PALETTE
    limbs = _limb_points(pose)
    start, end = _horn_ends(pose, limbs)
    axis = _norm(_sub(end, start))
    cross = _perp(axis)
    listening = pose.animation in {"idle", "interact"}

    # The acoustic path is a narrow bent tube, not a brass-instrument bore.
    # Its final segment enters the back of the collector dish.
    bend_a = _add(start, _add(_mul(axis, 6.0), _mul(cross, 2.0 if listening else 0.8)))
    bend_b = _add(end, _add(_mul(axis, -5.0), _mul(cross, 1.0)))
    tube_points = [start, bend_a, bend_b, _add(end, _mul(axis, -2.8))]
    v.line(tube_points, pal["outline"], 4.0)
    v.line(tube_points, pal["brass_dark"], 2.2)
    v.line(
        [_add(point, _mul(cross, -0.45)) for point in tube_points],
        pal["brass_light"],
        0.7,
    )

    if listening:
        # A dark padded cup visibly encloses the ear.  It is deliberately much
        # smaller than the collector and cannot be mistaken for a mouthpiece.
        v.polygon(
            _oval_points(start, axis, 2.5, 3.3),
            pal["leather_dark"],
            pal["outline"],
            0.8,
        )
        v.polygon(
            _oval_points(_add(start, _mul(axis, 0.5)), axis, 1.2, 1.8),
            pal["lining_light"],
            pal["brass_light"],
            0.45,
        )
    else:
        v.polygon(
            _oval_points(start, axis, 1.6, 2.4),
            pal["brass_dark"],
            pal["outline"],
            0.6,
        )

    # The receiver terminates in an oval parabolic collector with an exposed
    # central pickup and braces.  This reads as surveillance hardware rather
    # than a playable trumpet bell.
    outer = _oval_points(end, axis, 3.8, 9.2)
    inner_center = _add(end, _mul(axis, 0.9))
    inner = _oval_points(inner_center, axis, 2.5, 7.2)
    v.polygon(outer, pal["brass"], pal["outline"], 1.2)
    v.polygon(inner, pal["lining"], pal["brass_dark"], 0.9)

    pickup = _add(end, _mul(axis, 3.0))
    for offset in (-5.2, 0.0, 5.2):
        rim = _add(inner_center, _mul(cross, offset))
        v.line([rim, pickup], pal["brass_dark"], 0.85)
    v.ellipse(pickup, 3.2, 3.2, pal["brass_light"], pal["outline"], 0.65)
    v.ellipse(_add(pickup, _mul(axis, 0.45)), 1.2, 1.2, pal["lining_light"])

    # A collar where the bent tube enters the dish makes the mechanical
    # connection explicit.
    collar = _add(end, _mul(axis, -2.7))
    v.polygon(
        _oval_points(collar, axis, 1.5, 3.2),
        pal["brass_dark"],
        pal["outline"],
        0.55,
    )


def _paint_hands(v: VDraw, pose: EvePose) -> None:
    pal = EVE_PALETTE
    limbs = _limb_points(pose)
    horn_start, horn_end = _horn_ends(pose, limbs)
    # Hands remain tied to the sleeve endpoints, not guessed from horn geometry.
    for which, size in (("far", 4.2), ("near", 4.5)):
        hand = limbs[which][2]
        v.ellipse(hand, size, size, pal["skin"], pal["outline"], 0.8)
        # Two short finger marks establish a grip without turning the hand into
        # an unreadable mitten at 128 pixels.
        direction = _norm(_sub(horn_end, horn_start))
        v.line(
            [
                _add(hand, _mul(direction, -0.8)),
                _add(hand, _mul(direction, 1.5)),
            ],
            pal["skin_shadow"],
            0.6,
        )


def _paint_details(v: VDraw, pose: EvePose) -> None:
    pal = EVE_PALETTE
    # Cloak seams follow the drape and make body motion readable frame-to-frame.
    v.line(
        [
            _xf(pose, (51.0, 64.0)),
            _xf(pose, (49.0 - pose.cloak_sway * 0.20, 92.0)),
            _xf(pose, (46.0 - pose.cloak_sway * 0.50, 110.0)),
        ],
        pal["cloak_light"],
        1.0,
    )
    v.line(
        [
            _xf(pose, (69.0, 64.0)),
            _xf(pose, (72.0 + pose.cloak_sway * 0.25, 90.0)),
            _xf(pose, (76.0 + pose.cloak_sway * 0.55, 108.0)),
        ],
        pal["cloak_deep"],
        1.0,
    )

    if pose.signal > 0.10:
        limbs = _limb_points(pose)
        _start, bell = _horn_ends(pose, limbs)
        # Three thin receiving arcs: authored geometry, not glow or blur.
        strength = _clamp01(pose.signal)
        axis = _norm(_sub(bell, _start))
        outward = _add(bell, _mul(axis, 2.0))
        for idx in range(3):
            radius = 4.0 + idx * 2.8 + strength
            box = (
                outward[0] - radius,
                outward[1] - radius,
                outward[0] + radius,
                outward[1] + radius,
            )
            # Select the half of each ring that opens away from the receiver.
            axis_angle = math.degrees(math.atan2(axis[1], axis[0]))
            v.arc(
                box,
                axis_angle - 65.0,
                axis_angle + 65.0,
                pal["brass_light"] if idx == 0 else pal["lining_light"],
                0.8,
            )


PAINTERS: Dict[str, Callable[[VDraw, EvePose], None]] = {
    "cloak_back": _paint_cloak_back,
    "legs": _paint_legs,
    "torso_cloak": _paint_torso_cloak,
    "satchel": _paint_satchel,
    "hood": _paint_hood,
    "face": _paint_face,
    "far_arm": lambda v, p: _paint_arm(v, p, "far"),
    "near_arm": lambda v, p: _paint_arm(v, p, "near"),
    "horn": _paint_horn,
    "hands": _paint_hands,
    "details": _paint_details,
}


class EveEavesdropperGenerator(CharacterGenerator):
    name = "eve_eavesdropper"
    target = "eve_eavesdropper"
    applies_job_name = True

    ANIMATIONS: Dict[str, Dict[str, int]] = {
        "idle": {"frames": 8, "duration_ms": 120},
        "walk": {"frames": 8, "duration_ms": 100},
        "talk": {"frames": 6, "duration_ms": 100},
        "interact": {"frames": 6, "duration_ms": 95},
    }

    def build_spec(self, job: CharacterJob) -> EveSpec:
        if job.archetype != "eve":
            raise KeyError(
                "eve_eavesdropper ships only the 'eve' archetype; "
                f"got {job.archetype!r}"
            )
        return EveSpec(
            target=self.target,
            seed=job.seed,
            archetype=job.archetype,
            name="Eve",
            role="npc",
        )

    def canonical_pose(self) -> Tuple[str, int]:
        return ("idle", 2)

    def body_inset(self) -> Dict[str, float]:
        # The trumpet and trailing hood are visual extensions, not collision.
        return {"left": 0.05, "right": 0.20, "top": 0.01, "bottom": 0.0}

    def render_frame(
        self,
        spec: EveSpec,
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
