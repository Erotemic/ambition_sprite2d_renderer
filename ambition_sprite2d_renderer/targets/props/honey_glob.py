"""A glob of honey the Hunny Horror spits.

A small code-generated prop: one transparent PNG the game loads as the
`honey_glob` projectile visual (game/ambition_content/src/projectiles.rs). He
lobs these in arcs and they burst where they land: a heavy drop of amber honey,
lit from above, with a highlight and a string trailing up behind it.
"""

from __future__ import annotations

import math
from pathlib import Path
from shutil import copy2
from typing import Iterable, List

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "honey_glob"
SHEET_FILES = (
    f"{TARGET_NAME}.png",
    # The packed sheet and its sidecars ship too: a published manifest naming
    # an unpublished page is a broken package contract.
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

WORK_SIZE = 512
FINAL_SIZE = 128
OUTPUT_NAME = f"{TARGET_NAME}.png"
ROWS = [("idle", 1, 100)]

OUTLINE = (92, 46, 8, 255)
HONEY = (244, 164, 24, 255)
HONEY_DEEP = (204, 116, 12, 255)
HONEY_LIGHT = (255, 214, 104, 255)
SHINE = (255, 250, 228, 255)


def _render_glob() -> Image.Image:
    img = Image.new("RGBA", (WORK_SIZE, WORK_SIZE), (0, 0, 0, 0))
    d = blending_draw(img)
    c = WORK_SIZE / 2
    r = WORK_SIZE * 0.4

    def drop(scale: float, dy: float = 0.0) -> list:
        """A teardrop, its tip up: it trails a string behind it as it falls."""
        pts = []
        for i in range(72):
            t = math.tau * i / 72
            x = r * scale * math.sin(t) * math.sin(t / 2.0) ** 0.8
            y = -r * scale * math.cos(t)
            pts.append((c + x, c + y * 1.05 + dy))
        return pts

    d.polygon(drop(1.0), fill=HONEY, outline=OUTLINE, width=16)
    d.polygon(drop(0.7, r * 0.3), fill=HONEY_DEEP)
    d.polygon(drop(0.62, r * 0.12), fill=HONEY)
    d.ellipse((c - r * 0.42, c - r * 0.05, c + r * 0.1, c + r * 0.42), fill=HONEY_LIGHT)
    d.ellipse((c - r * 0.34, c + r * 0.02, c - r * 0.1, c + r * 0.22), fill=SHINE)
    d.polygon(drop(1.0), outline=OUTLINE, width=16)
    return img.resize((FINAL_SIZE, FINAL_SIZE), Image.Resampling.LANCZOS)


def render_sheet(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda _anim, _frame_idx, _nframes: _render_glob(),
        out_dir=out_dir,
        frame_size=(FINAL_SIZE, FINAL_SIZE),
        auto_crop=True,
        crop_margin=4,
    )
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
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda _anim, _frame_idx, _nframes: _render_glob(),
        out_dir=out_dir,
        frame_size=(FINAL_SIZE, FINAL_SIZE),
        auto_crop=True,
        crop_margin=4,
    )
    return outputs["canonical_transparent"]




def render(out_dir: str | Path, **opts) -> List[Path]:
    return render_sheet(out_dir, **opts)
