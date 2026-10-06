"""A rock the Tyrant King shakes loose from his arena's ceiling.

A small code-generated prop: one transparent PNG the game loads as the
`trex_rock` projectile visual (game/ambition_content/src/projectiles.rs). His
stomps and his crashes into the wall bring these down: a chipped chunk of the
cave's own stone, lit from above so it reads falling against the dark.
"""

from __future__ import annotations

import math
from pathlib import Path
from shutil import copy2
from typing import Iterable, List

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "trex_rock"
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

OUTLINE = (34, 28, 30, 255)
STONE = (112, 98, 92, 255)
STONE_SHADE = (78, 66, 64, 255)
STONE_DEEP = (56, 46, 46, 255)
STONE_HI = (158, 142, 128, 255)
STONE_LIGHT = (196, 182, 160, 255)
MOSS = (92, 108, 62, 255)


def _hash(i: int, salt: int) -> float:
    v = math.sin(i * 12.9898 + salt * 78.233) * 43758.5453
    return v - math.floor(v)


def _outline_points(c: float, r: float) -> list[tuple[float, float]]:
    """An irregular, faceted boulder: nine corners at uneven radii."""
    pts = []
    n = 9
    for k in range(n):
        a = -math.pi / 2 + math.tau * (k + 0.35 * (_hash(k, 1) - 0.5)) / n
        rr = r * (0.78 + 0.22 * _hash(k, 2))
        pts.append((c + math.cos(a) * rr, c + math.sin(a) * rr * 0.86))
    return pts


def _render_rock() -> Image.Image:
    img = Image.new("RGBA", (WORK_SIZE, WORK_SIZE), (0, 0, 0, 0))
    d = blending_draw(img)
    c, r = WORK_SIZE / 2, WORK_SIZE * 0.44
    pts = _outline_points(c, r)
    d.polygon(pts, fill=STONE, outline=OUTLINE, width=14)
    # Facets: a fan from an off-centre peak, shaded by which way each faces
    # (light from the upper left).
    peak = (c - r * 0.18, c - r * 0.2)
    for k in range(len(pts)):
        a, b = pts[k], pts[(k + 1) % len(pts)]
        mid_a = math.atan2((a[1] + b[1]) / 2 - peak[1], (a[0] + b[0]) / 2 - peak[0])
        lit = math.cos(mid_a - math.radians(-135))
        col = STONE_LIGHT if lit > 0.75 else STONE_HI if lit > 0.25 else STONE if lit > -0.3 else STONE_SHADE if lit > -0.8 else STONE_DEEP
        inset = [peak, (a[0] + (peak[0] - a[0]) * 0.08, a[1] + (peak[1] - a[1]) * 0.08),
                 (b[0] + (peak[0] - b[0]) * 0.08, b[1] + (peak[1] - b[1]) * 0.08)]
        d.polygon(inset, fill=col)
    # Facet ridges, then the silhouette again over them.
    for p in pts[::2]:
        d.line([peak, (p[0] + (peak[0] - p[0]) * 0.08, p[1] + (peak[1] - p[1]) * 0.08)], fill=STONE_DEEP, width=6)
    d.polygon(pts, outline=OUTLINE, width=14)
    # Cracks and pits.
    for k in range(5):
        a = _hash(k, 5) * math.tau
        dist = 0.25 + 0.45 * _hash(k, 6)
        x, y = c + math.cos(a) * r * dist, c + math.sin(a) * r * dist * 0.8
        ln = r * (0.12 + 0.1 * _hash(k, 7))
        b = a + 1.2 + _hash(k, 8)
        d.line([(x, y), (x + math.cos(b) * ln, y + math.sin(b) * ln), (x + math.cos(b + 0.7) * ln * 1.6, y + math.sin(b + 0.7) * ln * 1.6)],
               fill=OUTLINE, width=7)
    for k in range(7):
        a = _hash(k, 9) * math.tau
        dist = math.sqrt(_hash(k, 10)) * 0.62
        rr = r * (0.03 + 0.025 * _hash(k, 11))
        x, y = c + math.cos(a) * r * dist, c + math.sin(a) * r * dist * 0.8
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=STONE_DEEP)
    # A little moss on the underside: it hung from a ceiling.
    for k in range(6):
        x = c - r * 0.45 + r * 0.9 * _hash(k, 12)
        y = c + r * (0.52 + 0.1 * _hash(k, 13))
        rr = r * (0.05 + 0.04 * _hash(k, 14))
        d.ellipse((x - rr, y - rr * 0.6, x + rr, y + rr * 0.6), fill=MOSS)
    return img.resize((FINAL_SIZE, FINAL_SIZE), Image.Resampling.LANCZOS)


def render_sheet(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda _anim, _frame_idx, _nframes: _render_rock(),
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
        render_fn=lambda _anim, _frame_idx, _nframes: _render_rock(),
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
