"""Sanic-support entity sprites: rings and springs.

This is deliberately an additive tack-on target instead of an edit to the
batched ``entities`` target. Discovery auto-registers any ``targets/props/*.py``
module that exposes ``render(out_dir, **opts)``; this target can therefore be
published independently while other agents are editing the main entity manifest.

The target emits loose PNGs with the same runtime-facing filenames the game can
wire later:

* ``pickup_ring.png``
* ``spring_red.png``

Its install hook places those files under ``assets/sprites/entities/`` when the
publisher is given the normal ``assets/sprites`` root.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Tuple

import yaml
from PIL import Image, ImageDraw

from ambition_sprite2d_renderer.core.draw import bbox, poly_scaled, rgba
from ambition_sprite2d_renderer.core.pipeline import CROP_GROUND, CROP_TIGHT, render_frame
from ambition_sprite2d_renderer.core.draw import blending_draw

Color = Tuple[int, int, int, int]
Point = Tuple[float, float]
DrawFn = Callable[[ImageDraw.ImageDraw, float], None]

TARGET_NAME = "sanic_support_entities"
INSTALL_SUBDIR = "entities"


@dataclass(frozen=True)
class SupportEntitySpriteSpec:
    key: str
    filename: str
    category: str
    state: str
    gameplay_hint: str
    size: Tuple[int, int] = (128, 128)
    crop: str = CROP_TIGHT


SPRITES: Tuple[SupportEntitySpriteSpec, ...] = (
    SupportEntitySpriteSpec(
        key="pickup_ring",
        filename="pickup_ring.png",
        category="pickup",
        state="idle",
        gameplay_hint="collectible momentum-platformer ring pickup",
    ),
    SupportEntitySpriteSpec(
        key="spring_red",
        filename="spring_red.png",
        category="rebound surface",
        state="idle",
        gameplay_hint="red spring / rebound pad for surface-locomotion sandbox rooms",
        crop=CROP_GROUND,
    ),
)

SHEET_FILES = (
    *(spec.filename for spec in SPRITES),
    f"{TARGET_NAME}_contact_sheet.png",
    f"{TARGET_NAME}_manifest.yaml",
)


def _line(d: ImageDraw.ImageDraw, pts: Iterable[Point], fill: Color, width: float, s: float) -> None:
    d.line(poly_scaled(list(pts), s), fill=fill, width=max(1, int(round(width * s))))


def _ellipse(
    d: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    w: float,
    h: float,
    *,
    fill: Color | None = None,
    outline: Color | None = None,
    width: float = 1.0,
    s: float,
) -> None:
    d.ellipse(
        bbox(cx * s, cy * s, w * s, h * s),
        fill=fill,
        outline=outline,
        width=max(1, int(round(width * s))),
    )


def _rounded_rect(
    d: ImageDraw.ImageDraw,
    xy: Tuple[float, float, float, float],
    *,
    radius: float,
    fill: Color,
    outline: Color | None = None,
    width: float = 1.0,
    s: float,
) -> None:
    x0, y0, x1, y1 = xy
    d.rounded_rectangle(
        (x0 * s, y0 * s, x1 * s, y1 * s),
        radius=radius * s,
        fill=fill,
        outline=outline,
        width=max(1, int(round(width * s))),
    )


def draw_pickup_ring(d: ImageDraw.ImageDraw, s: float) -> None:
    """Draw a readable gold ring at entity-sprite scale."""
    dark = rgba("#5A3307")
    shadow = (0, 0, 0, 38)
    gold = rgba("#F7B51E")
    light = rgba("#FFE985")
    hot = rgba("#FFF8C6")
    amber = rgba("#C97A10")

    # Soft contact shadow below the hovering ring.
    _ellipse(d, 64, 96, 52, 11, fill=shadow, s=s)

    # Outer + inner outlines make the crop robust against light backgrounds.
    _ellipse(d, 64, 60, 70, 86, fill=gold, outline=dark, width=3.0, s=s)
    _ellipse(d, 64, 60, 42, 56, fill=(0, 0, 0, 0), outline=dark, width=2.0, s=s)

    # Carve the center back to transparent in the supersampled buffer, then
    # redraw a subtle inner rim. Using RGBA fill with alpha 0 works here because
    # this target draws on a transparent frame, not on a precomposited sheet.
    _ellipse(d, 64, 60, 34, 48, fill=(0, 0, 0, 0), s=s)
    _ellipse(d, 64, 60, 40, 54, outline=amber, width=5.0, s=s)
    _ellipse(d, 64, 60, 31, 43, fill=(0, 0, 0, 0), outline=rgba("#FFF0A2"), width=2.0, s=s)

    # Painted highlights on the upper-left and lower-right arcs.
    _line(d, [(42, 39), (50, 31), (64, 28), (78, 33)], hot, 4.0, s)
    _line(d, [(35, 54), (37, 45), (42, 38)], light, 2.0, s)
    _line(d, [(83, 77), (75, 86), (59, 90), (47, 84)], rgba("#A85F09"), 3.0, s)

    # A tiny sparkle keeps it recognizable when scaled down.
    _line(d, [(94, 27), (94, 41)], hot, 2.0, s)
    _line(d, [(87, 34), (101, 34)], hot, 2.0, s)
    _line(d, [(31, 78), (31, 88)], rgba("#FFF3B5", 210), 1.5, s)
    _line(d, [(26, 83), (36, 83)], rgba("#FFF3B5", 210), 1.5, s)


def draw_spring_red(d: ImageDraw.ImageDraw, s: float) -> None:
    """Draw a compact red spring / rebound pad."""
    outline = rgba("#2A1712")
    red_dark = rgba("#8C1B16")
    red = rgba("#D7352E")
    red_hot = rgba("#FF746B")
    metal_dark = rgba("#4C5560")
    metal = rgba("#AEB7C2")
    metal_light = rgba("#E8EEF5")

    # Ground shadow.
    _ellipse(d, 64, 107, 74, 13, fill=(0, 0, 0, 45), s=s)

    # Base foot.
    _rounded_rect(
        d,
        (28, 90, 100, 107),
        radius=5,
        fill=red_dark,
        outline=outline,
        width=2,
        s=s,
    )
    _rounded_rect(
        d,
        (34, 86, 94, 98),
        radius=4,
        fill=red,
        outline=outline,
        width=2,
        s=s,
    )

    # Central spring coil. Alternating highlights make the zig-zag read at 1x.
    coil = [(43, 86), (84, 76), (44, 67), (84, 58), (44, 49)]
    _line(d, coil, outline, 8.0, s)
    _line(d, coil, metal_dark, 5.5, s)
    _line(d, [(45, 84), (82, 76), (46, 68), (82, 59), (47, 51)], metal_light, 2.0, s)

    # Top cap.
    d.polygon(
        poly_scaled([(33, 39), (95, 39), (105, 50), (96, 61), (32, 61), (23, 50)], s),
        fill=red,
        outline=outline,
    )
    _rounded_rect(
        d,
        (34, 32, 94, 48),
        radius=6,
        fill=red,
        outline=outline,
        width=2,
        s=s,
    )
    _line(d, [(42, 36), (86, 36)], red_hot, 3.0, s)
    _line(d, [(32, 55), (96, 55)], rgba("#71120F"), 2.0, s)

    # Small bolts on the base/cap.
    for cx, cy in ((39, 94), (89, 94), (40, 45), (88, 45)):
        _ellipse(d, cx, cy, 7, 7, fill=metal, outline=outline, width=1.0, s=s)
        _ellipse(d, cx - 1, cy - 1, 2.5, 2.5, fill=metal_light, s=s)


DRAWERS: dict[str, DrawFn] = {
    "pickup_ring": draw_pickup_ring,
    "spring_red": draw_spring_red,
}


def render_support_sprite(spec: SupportEntitySpriteSpec, *, supersample: int = 4) -> Image.Image:
    try:
        draw = DRAWERS[spec.key]
    except KeyError as ex:
        raise KeyError(f"no Sanic support drawer registered for {spec.key!r}") from ex
    return render_frame(
        draw,
        spec.size,
        supersample=supersample,
        crop=spec.crop,
        crop_padding=4,
    )


def build_contact_sheet(tiles: List[Tuple[SupportEntitySpriteSpec, Image.Image]]) -> Image.Image:
    cell_w = 148
    cell_h = 150
    label_h = 20
    sheet = Image.new("RGBA", (cell_w * len(tiles), cell_h), (0, 0, 0, 0))
    d = blending_draw(sheet)
    for idx, (spec, img) in enumerate(tiles):
        x = idx * cell_w
        sheet.alpha_composite(img, (x + (cell_w - img.width) // 2, label_h + (118 - img.height) // 2))
        d.text((x + 8, 4), spec.key, fill=(240, 244, 255, 255))
    return sheet


def render(out_dir: str | Path, **opts) -> List[Path]:
    """Render loose Sanic-support entity sprites into ``out_dir``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    supersample = int(opts.get("supersample", 4))
    outputs: List[Path] = []
    tiles: List[Tuple[SupportEntitySpriteSpec, Image.Image]] = []
    for spec in SPRITES:
        img = render_support_sprite(spec, supersample=supersample)
        path = out_dir / spec.filename
        img.save(path)
        outputs.append(path)
        tiles.append((spec, img))

    contact = build_contact_sheet(tiles)
    contact_path = out_dir / f"{TARGET_NAME}_contact_sheet.png"
    contact.save(contact_path)
    outputs.append(contact_path)

    manifest = {
        "generated_by": "ambition_sprite2d_renderer.targets.props.sanic_support_entities",
        "target": TARGET_NAME,
        "sprites": [asdict(spec) for spec in SPRITES],
        "notes": [
            "Additive target: intentionally separate from the batched entities.py manifest.",
            "Install hook copies these loose PNGs under assets/sprites/entities/.",
        ],
    }
    manifest_path = out_dir / f"{TARGET_NAME}_manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf8")
    outputs.append(manifest_path)
    return outputs


def install(render_dir: str | Path, dest_root: str | Path) -> Iterable[Path]:
    """Install under ``assets/sprites/entities`` from the normal sprite root.

    ``regen_sprites.sh --target sanic_support_entities`` passes the normal
    ``assets/sprites`` root for non-``entities`` targets. Keep this target
    additive by giving it its own install hook instead of editing the shell
    script's special cases.
    """
    render_dir = Path(render_dir)
    dest_root = Path(dest_root)
    dest_dir = dest_root / INSTALL_SUBDIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    installed: List[Path] = []
    for name in SHEET_FILES:
        src = render_dir / name
        if not src.exists():
            continue
        dst = dest_dir / name
        dst.write_bytes(src.read_bytes())
        installed.append(dst)
    return installed
