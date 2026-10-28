"""The bolt the Smirking Behemoth fires from its eye.

A small code-generated prop: the game loads its sheet as the `eye_beam`
projectile visual (game/ambition_content/src/projectiles.rs), drawn nose
along its flight. The boss fires a short line of these (`eye_beam` in
`ambition_content_modules`), and each one is longer than the space between
two of them, so the line reads as one beam.

It has the colours of the eye that fires it (`smirking_behemoth_boss.py`):
the pale glow of the eye for the core, the gold of the pupil about it, and
the violet of the hat band for the edge. No ink line: it is light. Drawn
pointing RIGHT; the ``fly`` row makes the core beat and the edge crackle.
"""

from __future__ import annotations

import math
from pathlib import Path
from shutil import copy2
from typing import Iterable, List

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "behemoth_eye_bolt"
SHEET_FILES = (
    f"{TARGET_NAME}.png",
    # The packed sheet and its sidecars ship too: a published manifest naming
    # an unpublished page is a broken package contract.
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

# Drawn at 4x and reduced.
WORK = (448, 144)
FINAL = (112, 36)
OUTPUT_NAME = f"{TARGET_NAME}.png"
ROWS = [("fly", 4, 45)]

EDGE = (188, 132, 208, 150)
EDGE_HOT = (236, 120, 190, 200)
GOLD = (240, 206, 60, 240)
CORE = (255, 247, 205, 255)
WHITE = (255, 255, 255, 255)


def _lance(tail: float, nose: float, cy: float, half: float, pinch: float) -> list:
    """A lance from ``tail`` to ``nose``: a long point at the nose and a short
    one at the tail. ``pinch`` narrows the waist (the core beats)."""
    body = nose - tail
    return [
        (tail, cy),
        (tail + body * 0.10, cy - half * 0.8),
        (tail + body * 0.45, cy - half * pinch),
        (tail + body * 0.72, cy - half),
        (nose, cy),
        (tail + body * 0.72, cy + half),
        (tail + body * 0.45, cy + half * pinch),
        (tail + body * 0.10, cy + half * 0.8),
    ]


def _render(frame: int) -> Image.Image:
    img = Image.new("RGBA", WORK, (0, 0, 0, 0))
    d = blending_draw(img)
    cy = WORK[1] / 2
    beat = (1.0, 0.86, 1.08, 0.92)[frame % 4]
    # The edge: a wide violet lance, and sparks that leave it toward the tail.
    d.polygon(_lance(18.0, 436.0, cy, 46.0 * beat, 0.78), fill=EDGE)
    for k in range(5):
        # each spark is at a place of its own in each frame
        x = 70.0 + 62.0 * k + 23.0 * ((frame + k) % 4)
        side = -1.0 if (k + frame) % 2 else 1.0
        y = cy + side * (40.0 + 9.0 * math.sin(1.7 * k + frame))
        d.polygon([(x + 22, y), (x, y - side * 9), (x - 30, y + side * 7), (x, y + side * 5)], fill=EDGE_HOT)
    # The body of the bolt, and the core in it.
    d.polygon(_lance(44.0, 430.0, cy, 28.0 * beat, 0.70), fill=GOLD)
    d.polygon(_lance(80.0, 420.0, cy, 15.0 * beat, 0.62), fill=CORE)
    d.polygon(_lance(250.0, 412.0, cy, 6.5, 0.9), fill=WHITE)
    return img.resize(FINAL, Image.Resampling.LANCZOS)


def _build(out_dir: Path):
    return build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda _anim, frame_idx, _nframes: _render(frame_idx),
        out_dir=out_dir,
        frame_size=FINAL,
        auto_crop=True,
        crop_margin=4,
    )


def render_sheet(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = _build(out_dir)
    copy2(outputs["canonical_transparent"], out_dir / OUTPUT_NAME)
    return [
        out_dir / OUTPUT_NAME,
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["preview"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
    ]


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return _build(out_dir)["canonical_transparent"]




def render(out_dir: str | Path, **opts) -> List[Path]:
    return render_sheet(out_dir, **opts)
