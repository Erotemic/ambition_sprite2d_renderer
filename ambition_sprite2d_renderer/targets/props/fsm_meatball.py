"""The Flying Spaghetti Monster's thrown meatball.

A small code-generated prop: one transparent PNG the game loads as the
`meatball` projectile visual (game/ambition_content/src/projectiles.rs). It is
the same meatball the boss wears on its bell — ground-meat crumb, a gloss of
marinara on top — drawn alone and a touch larger than life so it reads in
flight.
"""

from __future__ import annotations

import math
from pathlib import Path
from shutil import copy2
from typing import Iterable, List

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "fsm_meatball"
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

OUTLINE = (58, 40, 30, 255)
MEAT = (140, 78, 50, 255)
MEAT_SHADE = (96, 50, 32, 255)
MEAT_HI = (184, 116, 78, 255)
CRUMB = (78, 40, 26, 255)
SAUCE = (196, 52, 34, 255)
SAUCE_HI = (240, 118, 88, 235)


def _hash(i: int, salt: int) -> float:
    v = math.sin(i * 12.9898 + salt * 78.233) * 43758.5453
    return v - math.floor(v)


def _render_meatball() -> Image.Image:
    img = Image.new("RGBA", (WORK_SIZE, WORK_SIZE), (0, 0, 0, 0))
    d = blending_draw(img)
    c, r = WORK_SIZE / 2, WORK_SIZE * 0.42

    def ell(cx, cy, rx, ry, fill, outline=None, width=0):
        d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=fill, outline=outline, width=width)

    ell(c, c, r, r, MEAT, OUTLINE, 14)
    ell(c + r * 0.16, c + r * 0.2, r * 0.8, r * 0.74, MEAT_SHADE)
    ell(c - r * 0.08, c - r * 0.06, r * 0.8, r * 0.76, MEAT)
    ell(c - r * 0.3, c - r * 0.32, r * 0.34, r * 0.26, MEAT_HI)
    for k in range(22):
        a = _hash(k, 3) * math.tau
        dist = math.sqrt(_hash(k, 7)) * 0.8
        rr = r * (0.05 + 0.05 * _hash(k, 5))
        col = CRUMB if _hash(k, 11) < 0.6 else MEAT_HI
        ell(c + math.cos(a) * r * dist, c + math.sin(a) * r * dist, rr, rr, col)
    # A marinara cap, glossy, running down one side.
    cap = []
    for k in range(19):
        a = math.pi + math.pi * k / 18
        cap.append((c + math.cos(a) * r * 0.97, c + math.sin(a) * r * 0.97))
    for k in range(18, -1, -1):
        a = math.pi + math.pi * k / 18
        lip = 0.5 + 0.12 * math.sin(k * 1.9)
        cap.append((c + math.cos(a) * r * 0.9, c - r * lip + math.sin(a) * r * 0.12))
    d.polygon(cap, fill=SAUCE)
    d.line([(c + r * 0.05, c - r * 0.45), (c + r * 0.05, c + r * 0.1)], fill=SAUCE, width=int(r * 0.16))
    ell(c + r * 0.05, c + r * 0.1, r * 0.1, r * 0.1, SAUCE)
    ell(c - r * 0.34, c - r * 0.7, r * 0.2, r * 0.08, SAUCE_HI)
    return img.resize((FINAL_SIZE, FINAL_SIZE), Image.Resampling.LANCZOS)


def render_sheet(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda _anim, _frame_idx, _nframes: _render_meatball(),
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
        render_fn=lambda _anim, _frame_idx, _nframes: _render_meatball(),
        out_dir=out_dir,
        frame_size=(FINAL_SIZE, FINAL_SIZE),
        auto_crop=True,
        crop_margin=4,
    )
    return outputs["canonical_transparent"]


def install(render_dir: str | Path, dest_root: str | Path) -> Iterable[Path]:
    render_dir = Path(render_dir)
    dest_root = Path(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)
    installed: List[Path] = []
    for name in SHEET_FILES:
        src = render_dir / name
        if src.exists():
            dst = dest_root / name
            dst.write_bytes(src.read_bytes())
            installed.append(dst)
    return installed


def render(out_dir: str | Path, **opts) -> List[Path]:
    return render_sheet(out_dir, **opts)
