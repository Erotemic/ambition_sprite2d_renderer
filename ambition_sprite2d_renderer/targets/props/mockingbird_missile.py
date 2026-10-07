"""The missile the Mockingbird fires off its wingtip.

A small code-generated prop: the game loads its sheet as the
`mockingbird_missile` projectile visual (game/ambition_content/src/projectiles.rs),
drawn nose along its flight. It is the missile the boss's near wing carries
(`scripts/svg_art/mockingbird_boss_v2_art.py`, ``missile``): a steel body with
rings and a hazard band, tail fins and a teal warhead with a pale tip, here
with its motor lit. Drawn pointing RIGHT; the ``fly`` row flickers the flame.
"""

from __future__ import annotations

from pathlib import Path
from shutil import copy2
from typing import Iterable, List

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "mockingbird_missile"
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
WORK = (640, 200)
FINAL = (160, 50)
OUTPUT_NAME = f"{TARGET_NAME}.png"
ROWS = [("fly", 3, 60)]

INK = (24, 22, 28, 255)
STEEL = (150, 156, 166, 255)
STEEL_HI = (214, 220, 228, 255)
STEEL_LO = (92, 98, 110, 255)
HAZARD = (236, 196, 52, 255)
WARHEAD = (52, 170, 160, 255)
WARHEAD_HI = (150, 232, 220, 255)
TIP = (236, 244, 240, 255)
FLAME = ((255, 120, 36, 230), (255, 196, 80, 245), (255, 250, 220, 255))


def _render(frame: int) -> Image.Image:
    img = Image.new("RGBA", WORK, (0, 0, 0, 0))
    d = blending_draw(img)
    cy = WORK[1] / 2
    r = 26.0
    tail, nose = 190.0, 600.0
    # The flame first, behind the body: a plume off the tail, flickering.
    lick = (1.0, 0.82, 1.12)[frame % 3]
    for color, k in zip(FLAME, (1.0, 0.7, 0.4)):
        length = 170.0 * k * lick
        w = r * 1.2 * k
        d.polygon([(tail + 6, cy - w), (tail - length * 0.5, cy - w * 0.7), (tail - length, cy),
                   (tail - length * 0.5, cy + w * 0.7), (tail + 6, cy + w)], fill=color)
    # Tail fins, above and below.
    for s in (-1, 1):
        d.polygon([(tail + 70, cy + s * r * 0.8), (tail - 8, cy + s * r * 2.3), (tail + 10, cy + s * r * 0.8)],
                  fill=STEEL_LO, outline=INK, width=6)
    # The body: a cylinder, shaded top to bottom.
    body_end = nose - 110
    d.rounded_rectangle((tail, cy - r, body_end, cy + r), radius=8, fill=STEEL, outline=INK, width=7)
    d.rectangle((tail + 8, cy - r + 6, body_end - 4, cy - r * 0.35), fill=STEEL_HI)
    d.rectangle((tail + 8, cy + r * 0.4, body_end - 4, cy + r - 6), fill=STEEL_LO)
    # Rings, and the hazard band.
    for x in (tail + 40, body_end - 30):
        d.line([(x, cy - r + 4), (x, cy + r - 4)], fill=INK, width=6)
    band = (body_end - 120, body_end - 70)
    d.rectangle((band[0], cy - r + 4, band[1], cy + r - 4), fill=HAZARD)
    for k in range(4):
        x = band[0] + 6 + k * 12
        d.polygon([(x, cy - r + 4), (x + 8, cy - r + 4), (x - 4, cy + r - 4), (x - 12, cy + r - 4)], fill=INK)
    # The warhead: a teal ogive with a pale tip.
    d.polygon([(body_end - 4, cy - r), (body_end + 60, cy - r * 0.75), (nose - 20, cy - r * 0.25), (nose, cy),
               (nose - 20, cy + r * 0.25), (body_end + 60, cy + r * 0.75), (body_end - 4, cy + r)],
              fill=WARHEAD, outline=INK, width=7)
    d.polygon([(body_end + 10, cy - r * 0.7), (body_end + 60, cy - r * 0.55), (nose - 30, cy - r * 0.15),
               (body_end + 40, cy - r * 0.2)], fill=WARHEAD_HI)
    d.polygon([(nose - 34, cy - r * 0.34), (nose, cy), (nose - 34, cy + r * 0.34)], fill=TIP, outline=INK, width=5)
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

