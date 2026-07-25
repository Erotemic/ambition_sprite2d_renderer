"""Sprite generator for a literal snake with a cardboard-box shell.

This is the intended Koopa-replacement joke: a sneaky green snake that crawls
around carrying a taped-up box on its back, retreats fully into it when
stomped, idles while boxed, peeks to telegraph emergence, and then emerges.
The target name stays ``solid_snake`` for the pun, but the art is an actual
snake, not the stealth-game protagonist.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "solid_snake"
FRAME_SIZE = (128, 128)
SUPER = 4
CANVAS_W = FRAME_SIZE[0] * SUPER
CANVAS_H = FRAME_SIZE[1] * SUPER
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 140),
    ("walk", 8, 96),
    ("retreat", 6, 120),
    ("boxed_idle", 6, 140),
    ("peek", 6, 135),
    ("emerge", 6, 120),
    ("hiss", 6, 110),
    ("death", 6, 120),
]

TRANSPARENT = (0, 0, 0, 0)
OUTLINE = (22, 18, 14, 255)
SNAKE = (98, 143, 88, 255)
SNAKE_LIGHT = (129, 171, 113, 255)
SNAKE_DARK = (72, 108, 67, 255)
BELLY = (203, 197, 144, 255)
EYE = (30, 25, 22, 255)
TONGUE = (202, 73, 95, 255)
BOX = (188, 145, 89, 255)
BOX_LIGHT = (213, 173, 118, 255)
BOX_DARK = (143, 105, 63, 255)
BOX_TAPE = (226, 202, 156, 255)
BOX_MARK = (105, 79, 50, 255)

ACTOR_METADATA = {
    "actor": {"character_id": "npc_solid_snake", "display_name": "Solid Snake"},
    "body": {
        "body_plan": "Serpentine",
        "body_kind": "Snake",
        "mass_class": "Light",
        "traits": [
            "story",
            "serpent",
            "box_shell",
            "memey",
            "stealth_parody",
        ],
        "locomotion_hint": "Slither",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": True,
            "use_lifts": False,
            "door_access": None,
        },
        "interactions": {
            "talk": False,
            "trade": None,
            "carry": None,
            "open_doors": None,
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "portrait": {"animation": "idle", "frame": 2},
    },
    "tags": ["story", "serpent", "box_shell", "stealth_parody"],
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "ability.hide": {"animation": "retreat", "events": []},
        "ability.hidden_idle": {"animation": "boxed_idle", "events": []},
        "ability.peek": {"animation": "peek", "events": []},
        "ability.emerge": {"animation": "emerge", "events": []},
        "combat.hurt": {"animation": "retreat", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
    "dialogue_hints": {
        "barks": [
            "Hiss.",
            "The box is the shell.",
            "Sneaking is easier when nobody respects the disguise.",
        ]
    },
}


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(x: float, y: float) -> Tuple[int, int]:
    return (_s(x), _s(y))


def _bbox(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _draw_line(draw: ImageDraw.ImageDraw, pts: Iterable[Point], fill: RGBA, width: float) -> None:
    draw.line([_pt(x, y) for x, y in pts], fill=fill, width=max(1, _s(width)), joint="curve")


def _poly(
    draw: ImageDraw.ImageDraw,
    pts: Sequence[Point],
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    ipts = [_pt(x, y) for x, y in pts]
    draw.polygon(ipts, fill=fill)
    if outline is not None:
        draw.line(ipts + [ipts[0]], fill=outline, width=max(1, _s(width)), joint="curve")


def _circle(
    draw: ImageDraw.ImageDraw,
    p: Point,
    r: float,
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(_bbox(p[0], p[1], r, r), fill=fill, outline=outline, width=max(1, _s(width)) if outline else 0)


def _downsample(img: Image.Image) -> Image.Image:
    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _mix(a: RGBA, b: RGBA, t: float) -> RGBA:
    return tuple(int(round(a[i] * (1.0 - t) + b[i] * t)) for i in range(4))  # type: ignore[return-value]


def _phase(frame_idx: int, nframes: int) -> float:
    return math.tau * (frame_idx / max(1, nframes))


def _snake_curve(anim: str, frame_idx: int, nframes: int) -> tuple[list[Point], Point, Point, float]:
    ph = _phase(frame_idx, nframes)
    pts: list[Point] = []
    if anim == "death":
        for i in range(16):
            x = 28.0 + i * 5.3
            y = 84.0 + 1.4 * math.sin(i * 0.8) + i * 0.55
            pts.append((x, y))
        neck = (104.0, 88.0)
        head = (113.0, 91.0)
        angle = 0.42
        return pts, neck, head, angle

    if anim == "walk":
        amp = 8.0
        lift = 0.0
        slither = ph
    elif anim == "hiss":
        amp = 5.5
        lift = -1.5
        slither = ph * 0.35
    elif anim == "emerge":
        amp = 4.0
        lift = -1.0
        slither = ph * 0.30
    else:
        amp = 4.0
        lift = 0.0
        slither = ph * 0.45

    for i in range(16):
        t = i / 15.0
        x = 22.0 + t * 78.0
        sway = math.sin(t * 2.5 * math.pi + slither) * amp
        taper = 1.0 - 0.25 * t
        y = 81.0 + sway * taper + lift - t * 2.0
        pts.append((x, y))

    neck_base = pts[-1]
    if anim == "hiss":
        neck = (neck_base[0] + 7.0, neck_base[1] - 17.0)
        head = (neck[0] + 8.5, neck[1] - 4.0)
        angle = -0.35
    else:
        neck = (neck_base[0] + 7.0, neck_base[1] - 10.0)
        head = (neck[0] + 8.0, neck[1] - 1.5)
        angle = -0.10 if anim in {"walk", "emerge"} else -0.05
    return pts, neck, head, angle


def _body_width(t: float) -> float:
    return 12.5 - 5.5 * t


def _draw_box(draw: ImageDraw.ImageDraw, cx: float, cy: float, peek: float = 0.0, wobble: float = 0.0) -> None:
    left = cx - 20.0 + wobble
    top = cy - 12.0
    right = cx + 18.0 + wobble
    bottom = cy + 15.0
    front = [
        (left, top),
        (right - 5.0, top),
        (right, top + 4.0),
        (right, bottom - 3.0),
        (left + 5.0, bottom),
        (left, bottom - 5.0),
    ]
    _poly(draw, front, BOX, OUTLINE, 1.0)
    _poly(draw, [(left, top), (left + 8.0, top - 5.0), (right + 1.0, top - 5.0), (right - 5.0, top)], BOX_LIGHT, OUTLINE, 0.8)
    _poly(draw, [(right - 5.0, top), (right + 1.0, top - 5.0), (right + 6.5, top + 0.0), (right, top + 4.0)], _mix(BOX_DARK, OUTLINE, 0.1), OUTLINE, 0.8)
    _draw_line(draw, [(left + 11.5, top + 2.0), (left + 11.5, bottom - 4.0)], BOX_TAPE, 0.9)
    _draw_line(draw, [(left + 8.0, top + 1.5), (right - 8.0, top + 1.5)], BOX_TAPE, 0.8)
    _draw_line(draw, [(left + 26.0, top + 2.0), (left + 26.0, bottom - 4.0)], BOX_TAPE, 0.9)
    _draw_line(draw, [(left + 7.0, cy + 0.2), (left + 13.0, cy - 1.8), (left + 15.0, cy + 4.0)], BOX_MARK, 0.8)
    _draw_line(draw, [(left + 23.0, cy - 2.0), (left + 31.0, cy - 2.5), (left + 31.5, cy + 3.2), (left + 23.5, cy + 3.0)], BOX_MARK, 0.8)
    if peek > 0.0:
        head = (left + 5.5, top + 13.0 - 7.0 * peek)
        _circle(draw, head, 4.4, SNAKE, OUTLINE, 0.8)
        _circle(draw, (head[0] + 3.0, head[1] - 1.0), 0.9, EYE, None)
        if peek > 0.55:
            _draw_line(draw, [(head[0] + 4.8, head[1] + 0.5), (head[0] + 9.0, head[1] - 0.2)], TONGUE, 0.8)
            _draw_line(draw, [(head[0] + 9.0, head[1] - 0.2), (head[0] + 10.8, head[1] - 1.5)], TONGUE, 0.5)
            _draw_line(draw, [(head[0] + 9.0, head[1] - 0.2), (head[0] + 10.8, head[1] + 1.3)], TONGUE, 0.5)


def _draw_body(draw: ImageDraw.ImageDraw, pts: list[Point], neck: Point, head: Point, head_angle: float) -> None:
    chain = pts + [neck, head]
    n = len(chain)
    for idx in range(n - 1):
        t = idx / max(1, n - 2)
        seg = [chain[idx], chain[idx + 1]]
        w = _body_width(t)
        _draw_line(draw, seg, OUTLINE, w + 3.0)
        _draw_line(draw, seg, SNAKE, w)
        if idx > 1 and idx < n - 3:
            c = chain[idx]
            _circle(draw, c, w * 0.19, SNAKE, None)

    for idx in range(1, len(pts) - 1, 2):
        t = idx / max(1, len(pts) - 1)
        p = pts[idx]
        _circle(draw, (p[0], p[1] + 1.5 + 0.5 * t), max(1.4, _body_width(t) * 0.22), BELLY, None)

    tail = pts[0]
    _poly(
        draw,
        [(tail[0] - 8.0, tail[1] + 1.0), (tail[0] - 1.0, tail[1] - 3.0), (tail[0] + 1.8, tail[1] + 3.0)],
        SNAKE_DARK,
        OUTLINE,
        0.7,
    )

    hx, hy = head
    head_pts = [
        (hx - 7.0, hy - 5.0),
        (hx + 2.0, hy - 8.0),
        (hx + 10.5, hy - 4.0),
        (hx + 12.0, hy + 0.5),
        (hx + 5.5, hy + 6.0),
        (hx - 3.0, hy + 5.5),
        (hx - 8.0, hy + 1.0),
    ]
    _poly(draw, head_pts, SNAKE, OUTLINE, 1.0)
    _poly(draw, [(hx - 2.0, hy + 1.5), (hx + 7.5, hy + 1.0), (hx + 4.0, hy + 5.0), (hx - 3.0, hy + 4.0)], BELLY, None)
    _draw_line(draw, [(hx - 5.5, hy - 2.0), (hx + 6.5, hy - 4.3)], SNAKE_LIGHT, 0.8)
    _circle(draw, (hx + 5.0, hy - 2.3), 1.1, EYE, None)
    _draw_line(draw, [(hx + 8.0, hy + 1.3), (hx + 12.0, hy + 1.0)], OUTLINE, 0.6)
    _poly(draw, [(hx + 2.0, hy - 6.0), (hx + 4.0, hy - 9.0), (hx + 6.0, hy - 6.8)], SNAKE_DARK, OUTLINE, 0.5)


def _draw_tongue(draw: ImageDraw.ImageDraw, head: Point, length: float = 7.5) -> None:
    hx, hy = head
    mid = (hx + 11.5, hy + 1.0)
    tip = (hx + 11.5 + length, hy + 0.3)
    _draw_line(draw, [mid, tip], TONGUE, 0.8)
    _draw_line(draw, [tip, (tip[0] + 2.2, tip[1] - 1.8)], TONGUE, 0.45)
    _draw_line(draw, [tip, (tip[0] + 2.2, tip[1] + 1.8)], TONGUE, 0.45)


def _draw_back_box_snake(draw: ImageDraw.ImageDraw, anim: str, frame_idx: int, nframes: int) -> tuple[list[Point], Point, Point, Point]:
    pts, neck, head, head_angle = _snake_curve(anim, frame_idx, nframes)
    _draw_body(draw, pts, neck, head, head_angle)
    box_anchor = pts[7]
    wobble = math.sin(_phase(frame_idx, nframes)) * (1.2 if anim == "walk" else 0.4)
    _draw_box(draw, box_anchor[0] + 5.0, box_anchor[1] - 13.5, peek=0.0, wobble=wobble)
    _draw_line(draw, [(box_anchor[0] - 5.0, box_anchor[1] - 10.5), (box_anchor[0] + 19.0, box_anchor[1] - 7.5)], OUTLINE, 1.0)
    _draw_line(draw, [(box_anchor[0] - 8.0, box_anchor[1] - 0.5), (box_anchor[0] + 15.0, box_anchor[1] + 3.5)], OUTLINE, 1.0)
    _draw_line(draw, [(box_anchor[0] - 5.0, box_anchor[1] - 10.5), (box_anchor[0] + 19.0, box_anchor[1] - 7.5)], BOX_TAPE, 0.55)
    _draw_line(draw, [(box_anchor[0] - 8.0, box_anchor[1] - 0.5), (box_anchor[0] + 15.0, box_anchor[1] + 3.5)], BOX_TAPE, 0.55)
    return pts, neck, head, box_anchor


def _draw_retreat_frame(draw: ImageDraw.ImageDraw, frame_idx: int, nframes: int) -> None:
    ph = _phase(frame_idx, nframes)
    wobble = math.sin(ph) * 0.45
    progress = frame_idx / max(1, nframes - 1)
    box_cx = 67.0
    box_cy = 74.0
    _draw_box(draw, box_cx, box_cy, peek=0.0, wobble=wobble)

    retreat_end = 0.82
    if progress >= retreat_end:
        return
    visible = 1.0 - (progress / retreat_end)
    entry = (84.0 + wobble, 83.5)
    tail = (entry[0] + 1.5, 85.0)
    mid = (entry[0] + 8.0 + 10.0 * visible, 84.0 + math.sin(ph) * 1.2)
    head = (entry[0] + 13.0 + 19.0 * visible, 81.5 - 4.5 * visible)
    chain = [tail, mid, head]
    widths = [7.4, 6.0]
    for idx in range(2):
        seg = [chain[idx], chain[idx + 1]]
        width = widths[idx] * (0.85 + 0.15 * visible)
        _draw_line(draw, seg, OUTLINE, width + 2.2)
        _draw_line(draw, seg, SNAKE, width)
    _circle(draw, ((tail[0] + mid[0]) * 0.5, (tail[1] + mid[1]) * 0.5 + 0.8), 1.7, BELLY, None)
    _circle(draw, ((mid[0] + head[0]) * 0.5, (mid[1] + head[1]) * 0.5 + 0.8), 1.5, BELLY, None)
    hx, hy = head
    _poly(
        draw,
        [
            (hx - 5.8, hy - 3.8),
            (hx + 0.8, hy - 5.6),
            (hx + 7.2, hy - 2.8),
            (hx + 8.2, hy + 0.8),
            (hx + 4.5, hy + 4.2),
            (hx - 2.8, hy + 4.5),
            (hx - 6.2, hy + 1.0),
        ],
        SNAKE,
        OUTLINE,
        0.9,
    )
    _poly(draw, [(hx - 1.0, hy + 1.2), (hx + 4.8, hy + 0.8), (hx + 2.8, hy + 3.6), (hx - 2.0, hy + 3.4)], BELLY, None)
    _circle(draw, (hx + 3.0, hy - 1.5), 0.9, EYE, None)


def _draw_boxed_idle(draw: ImageDraw.ImageDraw, frame_idx: int, nframes: int) -> None:
    ph = _phase(frame_idx, nframes)
    wobble = math.sin(ph) * 0.45
    _draw_box(draw, 67.0, 74.0, peek=0.0, wobble=wobble)


def _draw_peek(draw: ImageDraw.ImageDraw, frame_idx: int, nframes: int) -> None:
    ph = _phase(frame_idx, nframes)
    t = frame_idx / max(1, nframes - 1)
    peek = 0.22 + 0.72 * (0.5 - 0.5 * math.cos(math.pi * t))
    wobble = math.sin(ph) * 0.35
    _draw_box(draw, 67.0, 74.0, peek=peek, wobble=wobble)


def _draw_emerge(draw: ImageDraw.ImageDraw, frame_idx: int, nframes: int) -> None:
    ph = _phase(frame_idx, nframes)
    progress = frame_idx / max(1, nframes - 1)
    box_cx = 67.0
    box_cy = 74.0
    wobble = math.sin(ph) * 0.30
    _draw_box(draw, box_cx, box_cy, peek=0.0, wobble=wobble)

    visible = progress
    entry = (84.0 + wobble, 83.5)
    tail = (entry[0] + 1.5, 85.0)
    mid = (entry[0] + 8.0 + 10.0 * visible, 84.0 + math.sin(ph) * 1.2)
    head = (entry[0] + 13.0 + 19.0 * visible, 81.5 - 4.5 * visible)
    chain = [tail, mid, head]
    widths = [7.4, 6.0]
    for idx in range(2):
        seg = [chain[idx], chain[idx + 1]]
        width = widths[idx] * (0.85 + 0.15 * visible)
        _draw_line(draw, seg, OUTLINE, width + 2.2)
        _draw_line(draw, seg, SNAKE, width)
    _circle(draw, ((tail[0] + mid[0]) * 0.5, (tail[1] + mid[1]) * 0.5 + 0.8), 1.7, BELLY, None)
    _circle(draw, ((mid[0] + head[0]) * 0.5, (mid[1] + head[1]) * 0.5 + 0.8), 1.5, BELLY, None)
    hx, hy = head
    _poly(
        draw,
        [
            (hx - 5.8, hy - 3.8),
            (hx + 0.8, hy - 5.6),
            (hx + 7.2, hy - 2.8),
            (hx + 8.2, hy + 0.8),
            (hx + 4.5, hy + 4.2),
            (hx - 2.8, hy + 4.5),
            (hx - 6.2, hy + 1.0),
        ],
        SNAKE,
        OUTLINE,
        0.9,
    )
    _poly(draw, [(hx - 1.0, hy + 1.2), (hx + 4.8, hy + 0.8), (hx + 2.8, hy + 3.6), (hx - 2.0, hy + 3.4)], BELLY, None)
    _circle(draw, (hx + 3.0, hy - 1.5), 0.9, EYE, None)


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), TRANSPARENT)
    draw = blending_draw(img)

    if anim == "retreat":
        _draw_retreat_frame(draw, frame_idx, nframes)
        return _downsample(img)
    if anim == "boxed_idle":
        _draw_boxed_idle(draw, frame_idx, nframes)
        return _downsample(img)
    if anim == "peek":
        _draw_peek(draw, frame_idx, nframes)
        return _downsample(img)
    if anim == "emerge":
        _draw_emerge(draw, frame_idx, nframes)
        return _downsample(img)

    pts, neck, head, box_anchor = _draw_back_box_snake(draw, anim, frame_idx, nframes)

    if anim == "hiss":
        _draw_tongue(draw, head, 9.0 + 1.0 * math.sin(_phase(frame_idx, nframes)))
        for i in range(2):
            r = 8.0 + i * 5.5 + math.sin(_phase(frame_idx, nframes)) * 1.2
            draw.arc(_bbox(head[0] + 12.0, head[1] - 2.0, r, r * 0.65), start=290, end=20, fill=BOX_TAPE, width=max(1, _s(0.7)))
    elif anim == "idle" and frame_idx % max(1, nframes // 3) == 1:
        _draw_tongue(draw, head, 5.0)
    elif anim == "death":
        draw.arc(_bbox(head[0] + 6.0, head[1] - 1.0, 4.0, 3.0), start=20, end=160, fill=OUTLINE, width=max(1, _s(0.6)))

    return _downsample(img)


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda anim, frame_idx, nframes: _render_frame(anim, frame_idx, nframes),
        out_dir=out_dir,
        frame_size=opts.get("frame_size", FRAME_SIZE),
        auto_crop=False,
        trim=False,
        actor_metadata=ACTOR_METADATA,
        # The snake's silhouette CHANGES SHAPE between poses more than almost
        # any other body in the tree: sprawled it is a long low serpent, boxed
        # it is a small cardboard cube. Publishing per-row hurtboxes is what
        # lets the runtime take its collision + hurt box FROM THE ART for the
        # pose it is actually showing, instead of one idle-frame box that is
        # wrong for half the withdraw cycle. Row names are the gameplay keys
        # here (the runtime maps them through `CharacterAnim::from_name`), so
        # the identity map is the honest mapping.
        animation_key_map={name: name for name, _frames, _duration in ROWS},
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Solid Snake sprite target.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME,
    )
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
