"""Shared procedural art for the two Snakes on a Plane enemy variants."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

FRAME_SIZE = (160, 128)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 145),
    ("fly", 8, 92),
    ("bank", 6, 105),
    ("hiss", 6, 108),
    ("hurt", 4, 96),
    ("death", 7, 118),
]

TRANSPARENT = (0, 0, 0, 0)
OUTLINE = (24, 21, 19, 255)
SNAKE_GREEN = (91, 148, 82, 255)
SNAKE_LIGHT = (139, 188, 115, 255)
SNAKE_DARK = (56, 102, 54, 255)
SNAKE_BELLY = (225, 213, 151, 255)
SNAKE_EYE = (28, 25, 22, 255)
TONGUE = (207, 72, 98, 255)
PAPER = (239, 240, 226, 255)
PAPER_LIGHT = (255, 255, 247, 255)
PAPER_SHADE = (183, 197, 205, 255)
PAPER_FOLD = (120, 143, 153, 255)
GRID_BG = (239, 231, 201, 255)
GRID_LINE = (137, 166, 169, 255)
GRID_MAJOR = (80, 113, 118, 255)
AXIS = (46, 52, 56, 255)
AXIS_X = (183, 72, 66, 255)
AXIS_Y = (62, 103, 170, 255)


@dataclass(frozen=True)
class PlaneSpec:
    target_name: str
    display_name: str
    character_id: str
    kind: str
    traits: Tuple[str, ...]
    barks: Tuple[str, ...]


PAPER_SPEC = PlaneSpec(
    target_name="snakes_on_a_paper_plane",
    display_name="Snakes on a Paper Plane",
    character_id="npc_snakes_on_a_paper_plane",
    kind="paper",
    traits=("enemy", "flying", "snake_swarm", "paper_airplane", "plane_pun"),
    barks=(
        "This flight is hiss-class only.",
        "Please keep your scales inside the aircraft.",
        "We folded under pressure.",
    ),
)

CARTESIAN_SPEC = PlaneSpec(
    target_name="snakes_on_a_cartesian_plane",
    display_name="Snakes on a Cartesian Plane",
    character_id="npc_snakes_on_a_cartesian_plane",
    kind="cartesian",
    traits=("enemy", "flying", "snake_swarm", "cartesian_plane", "math_pun"),
    barks=(
        "We have coordinates for your location.",
        "Stay on the positive side.",
        "Our domain is all real snakes.",
    ),
)


def actor_metadata(spec: PlaneSpec) -> dict:
    if spec.kind == "cartesian":
        authoring_description = (
            "Snakes on a Cartesian Plane parodies the title Snakes on a Plane by "
            "putting a snake swarm on a literal coordinate grid. The joke should read "
            "both as airborne action-movie nonsense and as a mathematics pun about "
            "domains, axes, quadrants, and coordinates."
        )
        gameplay_description = (
            "Use as a flying swarm enemy whose motion, attacks, or weaknesses are tied "
            "to coordinates and quadrants. It can announce the player's location, cross "
            "axes, and weaponize positive and negative space."
        )
    else:
        authoring_description = (
            "Snakes on a Paper Plane parodies the title Snakes on a Plane at the most "
            "literal possible scale: several snakes have folded themselves onto a paper "
            "airplane. The fragile craft and overconfident passengers are the visual joke."
        )
        gameplay_description = (
            "Use as a light flying swarm enemy that banks, folds, crumples, and hisses. "
            "Its paper aircraft should make it agile but vulnerable to fire, water, or "
            "violent changes in direction."
        )
    return {
        "authoring_description": authoring_description,
        "gameplay_description": gameplay_description,
        "actor": {
            "character_id": spec.character_id,
            "display_name": spec.display_name,
        },
        "body": {
            "body_plan": "FlyingSwarm",
            "body_kind": "Wide",
            "mass_class": "Light",
            "locomotion_hint": "Hover",
            "traits": list(spec.traits),
        },
        "capabilities": {
            "traversal": {
                "walk": None,
                "jump": None,
                "climb": None,
                "fly": True,
                "swim": None,
                "crawl": None,
                "use_lifts": None,
                "door_access": [],
            },
            "interactions": {
                "talk": None,
                "trade": None,
                "carry": None,
                "open_doors": [],
            },
        },
        "brain": {"default_preset": "flying_patrol"},
        "actions": {"default_preset": "flying_contact"},
        "visual": {
            "default_pose": "idle",
            "portrait": {"animation": "idle", "frame": 2},
        },
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.fly": {"animation": "fly", "events": []},
            "locomotion.bank": {"animation": "bank", "events": []},
            "action.taunt": {"animation": "hiss", "events": []},
            "damage.hit": {"animation": "hurt", "events": []},
            "lifecycle.death": {"animation": "death", "events": []},
        },
        "sockets": {
            "center": {
                "source": f"{spec.target_name}.geometry",
                "point": {"x": 80.0, "y": 65.0},
            },
            "projectile_origin": {
                "source": f"{spec.target_name}.geometry",
                "point": {"x": 130.0, "y": 57.0},
            },
        },
        "tags": list(spec.traits),
        "dialogue_hints": {"barks": list(spec.barks)},
    }


def _s(value: float) -> int:
    return int(round(value * SUPER))


def _pt(point: Point) -> Tuple[int, int]:
    return (_s(point[0]), _s(point[1]))


def _bbox(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _poly(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    pts = [_pt(point) for point in points]
    draw.polygon(pts, fill=fill)
    if outline is not None:
        draw.line(
            pts + [pts[0]],
            fill=outline,
            width=max(1, _s(width)),
            joint="curve",
        )


def _line(
    draw: ImageDraw.ImageDraw,
    points: Iterable[Point],
    fill: RGBA,
    width: float,
) -> None:
    draw.line(
        [_pt(point) for point in points],
        fill=fill,
        width=max(1, _s(width)),
        joint="curve",
    )


def _circle(
    draw: ImageDraw.ImageDraw,
    center: Point,
    radius: float,
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(
        _bbox(center[0], center[1], radius, radius),
        fill=fill,
        outline=outline,
        width=max(1, _s(width)) if outline else 0,
    )


def _transform(point: Point, center: Point, angle: float, offset: Point) -> Point:
    x = point[0] - center[0]
    y = point[1] - center[1]
    c = math.cos(angle)
    s = math.sin(angle)
    return (
        center[0] + x * c - y * s + offset[0],
        center[1] + x * s + y * c + offset[1],
    )


def _transform_points(
    points: Sequence[Point], center: Point, angle: float, offset: Point
) -> List[Point]:
    return [_transform(point, center, angle, offset) for point in points]


def _snake_curve(
    anchor: Point,
    length: float,
    height: float,
    phase: float,
    direction: float = 1.0,
) -> List[Point]:
    points: List[Point] = []
    for idx in range(13):
        t = idx / 12.0
        x = anchor[0] + direction * length * t
        y = anchor[1] - math.sin(t * math.pi) * height
        y += math.sin(t * math.tau * 1.4 + phase) * 1.8 * math.sin(t * math.pi)
        points.append((x, y))
    return points


def _draw_snake(
    draw: ImageDraw.ImageDraw,
    curve: Sequence[Point],
    *,
    transform_center: Point,
    angle: float,
    offset: Point,
    tongue: float = 0.0,
    eyes_closed: bool = False,
) -> None:
    transformed = _transform_points(curve, transform_center, angle, offset)
    for idx in range(len(transformed) - 1):
        t = idx / max(1, len(transformed) - 2)
        width = 7.0 - 2.5 * t
        segment = [transformed[idx], transformed[idx + 1]]
        _line(draw, segment, OUTLINE, width + 2.0)
        _line(draw, segment, SNAKE_GREEN, width)
    for idx in range(2, len(transformed) - 3, 3):
        _circle(draw, transformed[idx], 1.35, SNAKE_LIGHT, None)

    head = transformed[-1]
    prev = transformed[-2]
    dx = head[0] - prev[0]
    dy = head[1] - prev[1]
    length = max(0.001, math.hypot(dx, dy))
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    head_poly = [
        (head[0] - ux * 4.5 - px * 4.0, head[1] - uy * 4.5 - py * 4.0),
        (head[0] + ux * 4.0 - px * 4.6, head[1] + uy * 4.0 - py * 4.6),
        (head[0] + ux * 8.0, head[1] + uy * 8.0),
        (head[0] + ux * 4.0 + px * 4.6, head[1] + uy * 4.0 + py * 4.6),
        (head[0] - ux * 4.5 + px * 4.0, head[1] - uy * 4.5 + py * 4.0),
    ]
    _poly(draw, head_poly, SNAKE_GREEN, OUTLINE, 0.9)
    belly_poly = [
        (head[0] - ux * 1.0 + px * 0.3, head[1] - uy * 1.0 + py * 0.3),
        (head[0] + ux * 5.0 + px * 0.5, head[1] + uy * 5.0 + py * 0.5),
        (head[0] + ux * 4.1 + px * 2.7, head[1] + uy * 4.1 + py * 2.7),
        (head[0] - ux * 1.8 + px * 2.3, head[1] - uy * 1.8 + py * 2.3),
    ]
    _poly(draw, belly_poly, SNAKE_BELLY, None)
    eye = (head[0] + ux * 3.7 - px * 2.2, head[1] + uy * 3.7 - py * 2.2)
    if eyes_closed:
        _line(draw, [(eye[0] - px * 1.2, eye[1] - py * 1.2), (eye[0] + px * 1.2, eye[1] + py * 1.2)], SNAKE_EYE, 0.65)
    else:
        _circle(draw, eye, 0.9, SNAKE_EYE, None)

    if tongue > 0.0:
        mouth = (head[0] + ux * 8.0, head[1] + uy * 8.0)
        tip = (mouth[0] + ux * tongue, mouth[1] + uy * tongue)
        _line(draw, [mouth, tip], TONGUE, 0.75)
        _line(draw, [tip, (tip[0] + ux * 2.0 + px * 1.3, tip[1] + uy * 2.0 + py * 1.3)], TONGUE, 0.45)
        _line(draw, [tip, (tip[0] + ux * 2.0 - px * 1.3, tip[1] + uy * 2.0 - py * 1.3)], TONGUE, 0.45)


def _motion(anim: str, frame_idx: int, nframes: int) -> Tuple[float, Point, float, bool]:
    phase = math.tau * frame_idx / max(1, nframes)
    bob = math.sin(phase) * 2.0
    angle = math.sin(phase) * 0.035
    squash = 1.0
    eyes_closed = False
    if anim == "fly":
        bob = math.sin(phase * 2.0) * 2.8
        angle = math.sin(phase) * 0.07
    elif anim == "bank":
        angle = math.sin(phase) * 0.22
        bob = math.cos(phase) * 2.0
    elif anim == "hurt":
        angle = (-0.14, 0.12, -0.08, 0.06)[frame_idx % 4]
        bob = (-3.0, 2.0, -1.0, 0.0)[frame_idx % 4]
        eyes_closed = True
    elif anim == "death":
        t = frame_idx / max(1, nframes - 1)
        angle = t * 0.9
        bob = 2.0 + t * 24.0
        squash = max(0.65, 1.0 - t * 0.25)
        eyes_closed = True
    return angle, (0.0, bob), squash, eyes_closed


def _draw_paper_plane(
    draw: ImageDraw.ImageDraw, center: Point, angle: float, offset: Point
) -> None:
    wing = [(24.0, 67.0), (142.0, 48.0), (95.0, 78.0), (76.0, 91.0)]
    lower = [(24.0, 67.0), (95.0, 78.0), (70.0, 99.0)]
    upper_fold = [(24.0, 67.0), (142.0, 48.0), (73.0, 72.0)]
    _poly(draw, _transform_points(lower, center, angle, offset), PAPER_SHADE, OUTLINE, 1.1)
    _poly(draw, _transform_points(wing, center, angle, offset), PAPER, OUTLINE, 1.1)
    _poly(draw, _transform_points(upper_fold, center, angle, offset), PAPER_LIGHT, OUTLINE, 0.9)
    _line(
        draw,
        _transform_points([(24.0, 67.0), (95.0, 78.0)], center, angle, offset),
        PAPER_FOLD,
        1.0,
    )
    _line(
        draw,
        _transform_points([(73.0, 72.0), (142.0, 48.0)], center, angle, offset),
        PAPER_FOLD,
        0.85,
    )


def _draw_cartesian_plane(
    draw: ImageDraw.ImageDraw, center: Point, angle: float, offset: Point
) -> None:
    board = [(28.0, 48.0), (137.0, 48.0), (128.0, 91.0), (20.0, 91.0)]
    _poly(draw, _transform_points(board, center, angle, offset), GRID_BG, OUTLINE, 1.1)
    for x in range(36, 133, 12):
        top = (float(x), 48.0)
        bottom = (float(x - 8), 91.0)
        _line(draw, _transform_points([top, bottom], center, angle, offset), GRID_LINE, 0.55)
    for y in range(56, 90, 8):
        left = (28.0 - (y - 48.0) * 0.18, float(y))
        right = (137.0 - (y - 48.0) * 0.20, float(y))
        _line(draw, _transform_points([left, right], center, angle, offset), GRID_LINE, 0.55)

    x_axis = [(23.0, 72.0), (132.0, 72.0)]
    y_axis = [(78.0, 88.0), (84.5, 51.0)]
    _line(draw, _transform_points(x_axis, center, angle, offset), AXIS_X, 1.25)
    _line(draw, _transform_points(y_axis, center, angle, offset), AXIS_Y, 1.25)
    x_tip = _transform_points([(132.0, 72.0), (126.5, 69.5), (126.5, 74.5)], center, angle, offset)
    y_tip = _transform_points([(84.5, 51.0), (81.0, 56.0), (87.0, 56.7)], center, angle, offset)
    _poly(draw, x_tip, AXIS_X, None)
    _poly(draw, y_tip, AXIS_Y, None)
    origin = _transform((81.0, 72.0), center, angle, offset)
    _circle(draw, origin, 2.0, AXIS, None)


def render_frame(spec: PlaneSpec, anim: str, frame_idx: int, nframes: int) -> Image.Image:
    canvas = Image.new(
        "RGBA",
        (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER),
        TRANSPARENT,
    )
    draw = blending_draw(canvas)
    center = (80.0, 69.0)
    angle, offset, _squash, eyes_closed = _motion(anim, frame_idx, nframes)
    phase = math.tau * frame_idx / max(1, nframes)

    if spec.kind == "paper":
        _draw_paper_plane(draw, center, angle, offset)
        anchors = [
            ((44.0, 66.0), 28.0, 15.0, 0.0, 1.0),
            ((75.0, 70.0), 25.0, 18.0, 1.8, 1.0),
            ((101.0, 63.0), 21.0, 14.0, 3.4, 1.0),
        ]
    else:
        _draw_cartesian_plane(draw, center, angle, offset)
        anchors = [
            ((42.0, 67.0), 25.0, 16.0, 0.3, 1.0),
            ((72.0, 70.0), 23.0, 19.0, 2.1, 1.0),
            ((103.0, 65.0), 22.0, 15.0, 4.0, 1.0),
        ]

    tongue = 0.0
    if anim == "hiss":
        tongue = 5.0 + 2.0 * (0.5 + 0.5 * math.sin(phase))
    for idx, (anchor, length, height, local_phase, direction) in enumerate(anchors):
        curve = _snake_curve(anchor, length, height, phase + local_phase, direction)
        _draw_snake(
            draw,
            curve,
            transform_center=center,
            angle=angle,
            offset=offset,
            tongue=tongue if idx == 2 else 0.0,
            eyes_closed=eyes_closed,
        )

    if anim == "death":
        # Loose paper/grid fragments make the fall read without a drop shadow.
        for idx in range(4):
            t = frame_idx / max(1, nframes - 1)
            x = 48.0 + idx * 21.0 + math.sin(idx + t * 5.0) * 4.0
            y = 91.0 + t * (8.0 + idx * 3.0)
            fragment = [(x - 3.0, y - 1.0), (x + 3.0, y - 2.0), (x + 1.0, y + 3.0)]
            _poly(draw, fragment, PAPER_SHADE if spec.kind == "paper" else GRID_BG, OUTLINE, 0.6)

    return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def render_target(spec: PlaneSpec, out_dir: str | Path) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=spec.target_name,
        rows=ROWS,
        render_fn=lambda anim, frame_idx, nframes: render_frame(
            spec, anim, frame_idx, nframes
        ),
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=False,
        trim=False,
        actor_metadata=actor_metadata(spec),
    )
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ]
