"""Composable construction sprites for the Super Mary-O demo.

These are deliberately separate from ``super_mary_o_pipe``.  The older target
is a complete decorative prop; this module publishes fixed-canvas pieces that
level/render code can compose without stretching artwork:

* ``super_mary_o_pipe_body`` repeats vertically;
* ``super_mary_o_pipe_top`` caps the repeated body;
* ``super_mary_o_flag_pole_body`` repeats vertically;
* ``super_mary_o_flag_pole_top`` caps the pole with its finial;
* ``super_mary_o_flag`` is a separate four-frame waving banner.
* ``super_mary_o_lava_top`` is the top of a pit of lava: four frames of a wave
  that go round, with the light of the lava in the air over it. It repeats
  along a pit;
* ``super_mary_o_lava_body`` is the lava under the top. It repeats along a pit,
  and the game makes it as deep as the pit is.

The seams and attachment anchors are part of the generated frame metadata.
Frames are never cropped or trim-packed because their transparent margins and
edge coordinates are construction geometry, not disposable whitespace.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ..super_mary_o_common import (
    OUTLINE,
    PIPE_COPPER,
    PIPE_COPPER_SHADOW,
    PIPE_COPPER_SHEEN,
    PIPE_COPPER_DARK,
    PIPE_COPPER_LIGHT,
    SKY_BLUE,
    TRANSPARENT,
    PixelCanvas,
    rasterize_logical,
)

RGBA = Tuple[int, int, int, int]
FrameMetaFn = Callable[[str, int, int], dict]
FrameFn = Callable[[str, int, int], Image.Image]

SCALE = 4
PIPE_LOGICAL = (16, 8)
POLE_LOGICAL = (8, 8)
FLAG_LOGICAL = (16, 12)

PIPE_FRAME = (PIPE_LOGICAL[0] * SCALE, PIPE_LOGICAL[1] * SCALE)
POLE_FRAME = (POLE_LOGICAL[0] * SCALE, POLE_LOGICAL[1] * SCALE)
FLAG_FRAME = (FLAG_LOGICAL[0] * SCALE, FLAG_LOGICAL[1] * SCALE)

POLE_LIGHT: RGBA = (244, 241, 222, 255)
POLE_MID: RGBA = (196, 201, 190, 255)
POLE_DARK: RGBA = (105, 113, 109, 255)
POLE_GLEAM: RGBA = (255, 255, 246, 255)
FLAG_RED: RGBA = (194, 48, 40, 255)
FLAG_RED_DARK: RGBA = (128, 30, 29, 255)
FLAG_RED_LIGHT: RGBA = (232, 76, 57, 255)
FLAG_GOLD: RGBA = (248, 201, 70, 255)
FLAG_CREAM: RGBA = (255, 244, 205, 255)


@dataclass(frozen=True)
class ConstructionSpec:
    target_name: str
    display_name: str
    frame_size: tuple[int, int]
    rows: List[Tuple[str, int, int]]
    renderer: FrameFn
    frame_meta: FrameMetaFn
    traits: Tuple[str, ...]


def _pipe_body_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    del animation, frame_idx, nframes

    def painter(px: PixelCanvas) -> None:
        # No horizontal outline: the first and last rows are intentionally the
        # same, so any number of body segments can meet without a dark seam.
        #
        # The shaft fills most of the frame (13 of 16 logical units). It used to
        # be 8 — half the frame — against a 14-unit lip, so the pipe read as a
        # thin tube wearing a hat three times too wide for it, and a body sliding
        # down it was wider than the tube it was supposedly inside.
        px.rect(1.5, 0.0, 14.5, 8.0, fill=PIPE_COPPER)
        px.rect(1.5, 0.0, 2.0, 8.0, fill=OUTLINE)
        px.rect(14.0, 0.0, 14.5, 8.0, fill=OUTLINE)
        px.rect(2.0, 0.0, 4.0, 8.0, fill=PIPE_COPPER_LIGHT)
        px.rect(4.0, 0.0, 5.5, 8.0, fill=PIPE_COPPER_SHEEN)
        px.rect(12.0, 0.0, 14.0, 8.0, fill=PIPE_COPPER_DARK)

    return rasterize_logical(PIPE_LOGICAL, SCALE, painter)


def _pipe_top_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    del animation, frame_idx, nframes

    def painter(px: PixelCanvas) -> None:
        # The lower neck is byte-for-byte the same vertical cross-section as
        # the body target.  The lip overhangs without changing the seam.
        px.rect(1.5, 3.5, 14.5, 8.0, fill=PIPE_COPPER)
        px.rect(1.5, 3.5, 2.0, 8.0, fill=OUTLINE)
        px.rect(14.0, 3.5, 14.5, 8.0, fill=OUTLINE)
        px.rect(2.0, 3.5, 4.0, 8.0, fill=PIPE_COPPER_LIGHT)
        px.rect(4.0, 3.5, 5.5, 8.0, fill=PIPE_COPPER_SHEEN)
        px.rect(12.0, 3.5, 14.0, 8.0, fill=PIPE_COPPER_DARK)

        # The lip overhangs the neck by ONE logical unit each side. It used to
        # overhang by three, which is what made the rim read as far too wide for
        # its own pipe.
        px.rect(0.5, 0.5, 15.5, 4.5, fill=OUTLINE)
        px.rect(1.0, 1.0, 15.0, 4.0, fill=PIPE_COPPER)
        px.rect(1.0, 1.0, 3.5, 4.0, fill=PIPE_COPPER_LIGHT)
        px.rect(3.5, 1.0, 5.0, 4.0, fill=PIPE_COPPER_SHEEN)
        px.rect(12.5, 1.0, 15.0, 4.0, fill=PIPE_COPPER_DARK)
        px.rect(1.5, 3.5, 14.5, 4.0, fill=PIPE_COPPER_SHADOW)

    return rasterize_logical(PIPE_LOGICAL, SCALE, painter)


def _pole_body_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    del animation, frame_idx, nframes

    def painter(px: PixelCanvas) -> None:
        # Like the pipe body, this runs through both vertical edges unchanged.
        px.rect(3.0, 0.0, 5.0, 8.0, fill=POLE_DARK)
        px.rect(3.25, 0.0, 4.75, 8.0, fill=POLE_MID)
        px.rect(3.25, 0.0, 3.75, 8.0, fill=POLE_LIGHT)
        px.rect(3.5, 0.0, 3.75, 8.0, fill=POLE_GLEAM)

    return rasterize_logical(POLE_LOGICAL, SCALE, painter)


def _pole_top_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    del animation, frame_idx, nframes

    def painter(px: PixelCanvas) -> None:
        # Stem first, then finial. The bottom row matches the body target.
        px.rect(3.0, 3.0, 5.0, 8.0, fill=POLE_DARK)
        px.rect(3.25, 3.0, 4.75, 8.0, fill=POLE_MID)
        px.rect(3.25, 3.0, 3.75, 8.0, fill=POLE_LIGHT)
        px.rect(3.5, 3.0, 3.75, 8.0, fill=POLE_GLEAM)
        px.ellipse(1.5, 0.0, 6.5, 4.5, fill=POLE_DARK, outline=OUTLINE, width=0.5)
        px.ellipse(2.0, 0.5, 6.0, 4.0, fill=POLE_LIGHT)
        px.ellipse(2.5, 0.8, 4.2, 2.3, fill=POLE_GLEAM)

    return rasterize_logical(POLE_LOGICAL, SCALE, painter)


def _flag_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    del animation
    wave = (-0.5, 0.0, 0.75, 0.0)[frame_idx % 4]
    curl = (0.5, 1.0, 0.0, -0.5)[frame_idx % 4]

    def painter(px: PixelCanvas) -> None:
        # Fixed tie loops: animation moves only the free edge, so a renderer can
        # pin every frame to the same pole attachment points.
        px.rect(0.5, 2.0, 2.5, 3.5, fill=FLAG_GOLD, outline=OUTLINE, width=0.5)
        px.rect(0.5, 8.5, 2.5, 10.0, fill=FLAG_GOLD, outline=OUTLINE, width=0.5)

        outer = [
            (2.0, 1.5),
            (12.5, 1.5 + wave),
            (15.0, 3.0 + curl),
            (14.0, 6.0 + wave),
            (15.0, 9.0 - curl),
            (12.5, 10.5 - wave),
            (2.0, 10.5),
        ]
        px.polygon(outer, fill=OUTLINE)
        inner = [
            (2.5, 2.0),
            (12.2, 2.0 + wave),
            (14.2, 3.3 + curl),
            (13.2, 6.0 + wave),
            (14.2, 8.7 - curl),
            (12.2, 10.0 - wave),
            (2.5, 10.0),
        ]
        px.polygon(inner, fill=FLAG_RED)
        px.polygon(
            [
                (2.5, 2.0),
                (12.2, 2.0 + wave),
                (13.0, 3.0 + curl),
                (3.0, 3.0),
            ],
            fill=FLAG_RED_LIGHT,
        )
        px.polygon(
            [
                (3.0, 8.7),
                (13.0, 7.9 - curl * 0.5),
                (14.2, 8.7 - curl),
                (12.2, 10.0 - wave),
                (2.5, 10.0),
            ],
            fill=FLAG_RED_DARK,
        )
        # A simple coin-diamond emblem avoids baking text into the reusable art.
        px.polygon(
            [(6.0, 4.0), (8.0, 3.0), (10.0, 4.25), (8.0, 7.75), (6.0, 6.5)],
            fill=FLAG_CREAM,
            outline=FLAG_GOLD,
            width=0.5,
        )
        px.rect(7.5, 4.25, 8.5, 6.75, fill=FLAG_GOLD)

    return rasterize_logical(FLAG_LOGICAL, SCALE, painter)


def _pipe_body_meta(animation: str, frame_idx: int, nframes: int) -> dict:
    del animation, frame_idx, nframes
    return {
        "anchors": {
            "stack_top": {"x": PIPE_FRAME[0] / 2, "y": 0.0},
            "stack_bottom": {"x": PIPE_FRAME[0] / 2, "y": float(PIPE_FRAME[1])},
        },
        "construction": {"kind": "pipe_body", "repeat_axis": "y"},
    }


def _pipe_top_meta(animation: str, frame_idx: int, nframes: int) -> dict:
    del animation, frame_idx, nframes
    return {
        "anchors": {
            "body_seam": {"x": PIPE_FRAME[0] / 2, "y": float(PIPE_FRAME[1])},
            "mouth_center": {"x": PIPE_FRAME[0] / 2, "y": 4.0},
        },
        "construction": {"kind": "pipe_top"},
    }


def _pole_body_meta(animation: str, frame_idx: int, nframes: int) -> dict:
    del animation, frame_idx, nframes
    return {
        "anchors": {
            "stack_top": {"x": POLE_FRAME[0] / 2, "y": 0.0},
            "stack_bottom": {"x": POLE_FRAME[0] / 2, "y": float(POLE_FRAME[1])},
        },
        "construction": {"kind": "flag_pole_body", "repeat_axis": "y"},
    }


def _pole_top_meta(animation: str, frame_idx: int, nframes: int) -> dict:
    del animation, frame_idx, nframes
    return {
        "anchors": {
            "body_seam": {"x": POLE_FRAME[0] / 2, "y": float(POLE_FRAME[1])},
            "flag_mount": {"x": POLE_FRAME[0] / 2 + 2.0, "y": 12.0},
        },
        "construction": {"kind": "flag_pole_top"},
    }


def _flag_meta(animation: str, frame_idx: int, nframes: int) -> dict:
    del animation, frame_idx, nframes
    return {
        "anchors": {
            "tie_upper": {"x": 4.0, "y": 10.0},
            "tie_lower": {"x": 4.0, "y": 36.0},
            "pole_mount": {"x": 4.0, "y": 23.0},
        },
        "construction": {"kind": "flag", "attach_to": "flag_pole_top.flag_mount"},
    }


# ── lava ──────────────────────────────────────────────────────────────────
LAVA_LOGICAL = (16, 16)
LAVA_FRAME = (LAVA_LOGICAL[0] * SCALE, LAVA_LOGICAL[1] * SCALE)
LAVA_FRAMES = 4
#: The logical row of the top of the lava in its top frame, in the mean. The
#: rows over it are air with the light of the lava in it.
LAVA_SURFACE = 8
LAVA_SURFACE_PX = float(LAVA_SURFACE * SCALE)

LAVA_WHITE: RGBA = (255, 244, 190, 255)
LAVA_YELLOW: RGBA = (255, 206, 84, 255)
LAVA_ORANGE: RGBA = (255, 132, 36, 255)
LAVA_RED: RGBA = (232, 54, 30, 255)
LAVA_DEEP: RGBA = (160, 22, 30, 255)
LAVA_DARK: RGBA = (92, 10, 28, 255)
#: The light of the lava in the air over it, at the lava and at its top.
LAVA_GLOW: RGBA = (255, 110, 40, 96)


def _lava_grid() -> list:
    return [[TRANSPARENT for _ in range(LAVA_LOGICAL[0])] for _ in range(LAVA_LOGICAL[1])]


def _lava_image(grid: list) -> Image.Image:
    image = Image.new("RGBA", LAVA_LOGICAL, TRANSPARENT)
    image.putdata([colour for row in grid for colour in row])
    return image.resize(LAVA_FRAME, Image.NEAREST)


def _lava_wave(x: int, frame_idx: int, nframes: int) -> int:
    """The row of the top of the lava at column `x`: one wave to the frame
    width, which goes one part of the width along in each frame."""
    phase = (x / LAVA_LOGICAL[0] - frame_idx / float(max(nframes, 1))) * 2.0 * math.pi
    return LAVA_SURFACE + int(round(1.2 * math.sin(phase)))


def _lava_top_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    del animation
    width, height = LAVA_LOGICAL
    grid = _lava_grid()
    for x in range(width):
        top = _lava_wave(x, frame_idx, nframes)
        # A skin of light on the wave, then the hot lava, then the red of the body.
        bands = ((LAVA_WHITE, 1), (LAVA_YELLOW, 1), (LAVA_ORANGE, 2 + (x + frame_idx) % 2))
        y = top
        for colour, rows in bands:
            for _ in range(rows):
                if y < height:
                    grid[y][x] = colour
                y += 1
        while y < height:
            grid[y][x] = LAVA_RED
            y += 1
    # A bubble that comes up, grows and breaks, one time in the four frames.
    bx = 11
    by = _lava_wave(bx, frame_idx, nframes)
    if frame_idx % 4 == 1:
        grid[by - 1][bx] = LAVA_YELLOW
    elif frame_idx % 4 == 2:
        for dx, dy in ((0, -2), (-1, -1), (1, -1)):
            grid[by + dy][bx + dx] = LAVA_YELLOW
        grid[by - 1][bx] = LAVA_WHITE
    elif frame_idx % 4 == 3:
        for dx, dy in ((-2, -2), (2, -2), (0, -3)):
            grid[by + dy][(bx + dx) % width] = LAVA_ORANGE
    image = _lava_image(grid)
    # The light in the air: none at the top of the frame, most at the lava.
    # It is a smooth ramp, not pixels: it is light, and it is not a thing.
    glow = Image.new("RGBA", LAVA_FRAME, TRANSPARENT)
    pixels = glow.load()
    for y in range(LAVA_FRAME[1]):
        alpha = int(LAVA_GLOW[3] * min(1.0, y / (LAVA_SURFACE_PX + SCALE)) ** 1.6)
        for x in range(LAVA_FRAME[0]):
            pixels[x, y] = (*LAVA_GLOW[:3], alpha)
    glow.alpha_composite(image)
    return glow


def _lava_body_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    del animation
    width, height = LAVA_LOGICAL
    grid = _lava_grid()
    for y in range(height):
        for x in range(width):
            # Three bands, each with a toothed edge, from the red of the top
            # to the dark of the deep.
            tooth = (x + y) % 2
            if y < 5 + tooth:
                colour = LAVA_RED
            elif y < 11 + tooth:
                colour = LAVA_DEEP
            else:
                colour = LAVA_DARK
            grid[y][x] = colour
    # Lumps of hot lava that go slowly along under the top.
    shift = frame_idx * width // max(nframes, 1)
    for x0, y0, long in ((1, 2, 4), (9, 4, 3), (5, 8, 3), (13, 10, 2)):
        for dx in range(long):
            grid[y0][(x0 + dx + shift) % width] = LAVA_ORANGE if y0 < 6 else LAVA_RED
    return _lava_image(grid)


def _lava_top_meta(animation: str, frame_idx: int, nframes: int) -> dict:
    del animation, frame_idx, nframes
    return {
        "anchors": {
            "surface": {"x": LAVA_FRAME[0] / 2, "y": LAVA_SURFACE_PX},
            "body_seam": {"x": LAVA_FRAME[0] / 2, "y": float(LAVA_FRAME[1])},
        },
        "construction": {"kind": "lava_top", "repeat_axis": "x"},
    }


def _lava_body_meta(animation: str, frame_idx: int, nframes: int) -> dict:
    del animation, frame_idx, nframes
    return {
        "anchors": {"stack_top": {"x": LAVA_FRAME[0] / 2, "y": 0.0}},
        "construction": {"kind": "lava_body", "repeat_axis": "x"},
    }


SPECS: Dict[str, ConstructionSpec] = {
    "super_mary_o_pipe_body": ConstructionSpec(
        target_name="super_mary_o_pipe_body",
        display_name="Mary-O Pipe Body",
        frame_size=PIPE_FRAME,
        rows=[("idle", 1, 150)],
        renderer=_pipe_body_frame,
        frame_meta=_pipe_body_meta,
        traits=("scenery", "pipe", "construction", "stackable"),
    ),
    "super_mary_o_pipe_top": ConstructionSpec(
        target_name="super_mary_o_pipe_top",
        display_name="Mary-O Pipe Top",
        frame_size=PIPE_FRAME,
        rows=[("idle", 1, 150)],
        renderer=_pipe_top_frame,
        frame_meta=_pipe_top_meta,
        traits=("scenery", "pipe", "construction", "cap"),
    ),
    "super_mary_o_flag_pole_body": ConstructionSpec(
        target_name="super_mary_o_flag_pole_body",
        display_name="Mary-O Flag Pole Body",
        frame_size=POLE_FRAME,
        rows=[("idle", 1, 150)],
        renderer=_pole_body_frame,
        frame_meta=_pole_body_meta,
        traits=("scenery", "flagpole", "construction", "stackable"),
    ),
    "super_mary_o_flag_pole_top": ConstructionSpec(
        target_name="super_mary_o_flag_pole_top",
        display_name="Mary-O Flag Pole Top",
        frame_size=POLE_FRAME,
        rows=[("idle", 1, 150)],
        renderer=_pole_top_frame,
        frame_meta=_pole_top_meta,
        traits=("scenery", "flagpole", "construction", "cap"),
    ),
    "super_mary_o_flag": ConstructionSpec(
        target_name="super_mary_o_flag",
        display_name="Mary-O Goal Flag",
        frame_size=FLAG_FRAME,
        rows=[("idle", 4, 120)],
        renderer=_flag_frame,
        frame_meta=_flag_meta,
        traits=("scenery", "flag", "goal", "animated"),
    ),
    "super_mary_o_lava_top": ConstructionSpec(
        target_name="super_mary_o_lava_top",
        display_name="Mary-O Lava Top",
        frame_size=LAVA_FRAME,
        rows=[("idle", LAVA_FRAMES, 170)],
        renderer=_lava_top_frame,
        frame_meta=_lava_top_meta,
        traits=("scenery", "lava", "construction", "animated"),
    ),
    "super_mary_o_lava_body": ConstructionSpec(
        target_name="super_mary_o_lava_body",
        display_name="Mary-O Lava Body",
        frame_size=LAVA_FRAME,
        rows=[("idle", LAVA_FRAMES, 260)],
        renderer=_lava_body_frame,
        frame_meta=_lava_body_meta,
        traits=("scenery", "lava", "construction", "animated"),
    ),
}


def _actor_metadata(spec: ConstructionSpec) -> dict:
    return {
        "actor": {
            "character_id": f"prop_{spec.target_name}",
            "display_name": spec.display_name,
        },
        "body": {
            "body_plan": "StaticProp",
            "body_kind": "Scenery",
            "mass_class": "Static",
            "locomotion_hint": "None",
            "traits": list(spec.traits),
        },
        "tags": list(spec.traits),
    }


def _render_spec(spec: ConstructionSpec, out_dir: str | Path) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=spec.target_name,
        rows=spec.rows,
        render_fn=spec.renderer,
        out_dir=out_dir,
        frame_size=spec.frame_size,
        frame_meta_fn=spec.frame_meta,
        label_width=160,
        auto_crop=False,
        actor_metadata=_actor_metadata(spec),
    )
    return [
        outputs[key]
        for key in (
            "canonical",
            "canonical_transparent",
            "spritesheet",
            "yaml",
            "ron",
            "actor",
            "preview",
        )
    ]


def render_construction_preview(out_path: str | Path) -> Path:
    """Render one code-generated composition showing how the pieces stack."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGBA", (384, 288), SKY_BLUE)

    # Ground strip.
    for y in range(240, 288):
        for x in range(384):
            canvas.putpixel((x, y), (176, 118, 64, 255))

    pipe_x = 48
    pipe_bottom = 240
    body = _pipe_body_frame("idle", 0, 1)
    top = _pipe_top_frame("idle", 0, 1)
    for i in range(4):
        canvas.alpha_composite(body, (pipe_x, pipe_bottom - (i + 1) * body.height))
    canvas.alpha_composite(top, (pipe_x, pipe_bottom - 5 * body.height))

    pole_x = 248
    pole_bottom = 240
    pole_body = _pole_body_frame("idle", 0, 1)
    pole_top = _pole_top_frame("idle", 0, 1)
    for i in range(6):
        canvas.alpha_composite(
            pole_body,
            (pole_x, pole_bottom - (i + 1) * pole_body.height),
        )
    pole_top_y = pole_bottom - 7 * pole_body.height
    canvas.alpha_composite(pole_top, (pole_x, pole_top_y))
    flag = _flag_frame("idle", 2, 4)
    canvas.alpha_composite(flag, (pole_x + 14, pole_top_y + 4))

    canvas.save(out_path)
    return out_path


TARGETS = {
    name: {
        "render": (lambda out_dir, _spec=spec, **opts: _render_spec(_spec, out_dir)),
        "actor_metadata": _actor_metadata(spec),
    }
    for name, spec in SPECS.items()
}

__all__ = ["SPECS", "TARGETS", "render_construction_preview"]
