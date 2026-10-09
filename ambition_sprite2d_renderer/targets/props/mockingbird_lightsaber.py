"""The burning lightsaber the Mockingbird spits from its mouth.

A small code-generated prop: the game loads its sheet as the
`mockingbird_lightsaber` projectile visuals
(game/ambition_content/src/projectiles.rs). The Mockingbird is on fire from
phase 2 of its fight, and what it spits is on fire too: a lit saber wreathed
in flame, spinning as it flies out and comes back.

Two rows, one for each fire it burns with: ``fly`` (the red fire of phase 2)
and ``fly_cold`` (the blue, cold fire of phase 3). A row is one whole turn of
the saber in eight frames. The game does not turn the sprite: the turn is in
the frames, so the flames trail the spin and not the flight.
"""

from __future__ import annotations

import math
from pathlib import Path
from shutil import copy2
from typing import Iterable, List

from PIL import Image, ImageFilter

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "mockingbird_lightsaber"
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
WORK = (448, 448)
FINAL = (112, 112)
OUTPUT_NAME = f"{TARGET_NAME}.png"
TURN_FRAMES = 8
ROWS = [("fly", TURN_FRAMES, 45), ("fly_cold", TURN_FRAMES, 45)]

INK = (24, 22, 28, 255)
HILT = (70, 74, 86, 255)
HILT_HI = (150, 156, 170, 255)
BAND = (214, 170, 60, 255)
# (the blade's glow, its core, and the flame from its outside to its heart)
HOT = {
    "glow": (255, 70, 36),
    "core": (255, 244, 226, 255),
    "flame": ((255, 96, 30, 215), (255, 176, 64, 235), (255, 244, 200, 250)),
}
COLD = {
    "glow": (60, 150, 255),
    "core": (232, 248, 255, 255),
    "flame": ((40, 104, 255, 215), (96, 196, 255, 235), (226, 248, 255, 250)),
}


def _saber(frame: int, fire: dict) -> Image.Image:
    """The saber pointing right, its middle at the frame's middle, burning."""
    cx, cy = WORK[0] / 2, WORK[1] / 2
    hilt_len, blade_len, half = 84.0, 250.0, 11.0
    hilt_x0 = cx - (hilt_len + blade_len) / 2
    blade_x0 = hilt_x0 + hilt_len
    blade_x1 = blade_x0 + blade_len

    # The glow of the blade, soft, under everything.
    glow = Image.new("RGBA", WORK, (0, 0, 0, 0))
    g = blending_draw(glow)
    g.rounded_rectangle((blade_x0 - 6, cy - half * 2.6, blade_x1 + 14, cy + half * 2.6), radius=30,
                        fill=(*fire["glow"], 150))
    glow = glow.filter(ImageFilter.GaussianBlur(14))

    img = Image.new("RGBA", WORK, (0, 0, 0, 0))
    img.alpha_composite(glow)
    d = blending_draw(img)

    # The flames: tongues along the blade that lean back from the spin (the
    # blade turns counter-clockwise, so they trail below it here), three deep.
    for depth, color in enumerate(fire["flame"]):
        reach = (1.0, 0.68, 0.38)[depth]
        for k in range(7):
            u = (k + 0.5) / 7.0
            x = blade_x0 + blade_len * u
            # Each tongue has its own rhythm, and flickers from frame to frame.
            lick = 0.72 + 0.28 * math.sin(frame * 2.4 + k * 1.9 + depth)
            height = (52.0 + 30.0 * math.sin(k * 2.1 + 0.6)) * reach * lick
            width = 26.0 * (1.0 - 0.25 * depth)
            lean = -34.0 * reach
            d.polygon(
                [
                    (x - width, cy + half * 0.4),
                    (x - width * 0.3 + lean * 0.5, cy + height * 0.62),
                    (x + lean, cy + height),
                    (x + width * 0.5 + lean * 0.4, cy + height * 0.5),
                    (x + width, cy + half * 0.4),
                ],
                fill=color,
            )
        # And a tongue off the tip.
        tip = 44.0 * reach * (0.8 + 0.2 * math.sin(frame * 3.1 + depth))
        d.polygon([(blade_x1 - 8, cy - half), (blade_x1 + tip, cy + tip * 0.35), (blade_x1 - 8, cy + half)], fill=color)

    # The blade: the glow's colour, then its bright core.
    d.rounded_rectangle((blade_x0 - 2, cy - half, blade_x1, cy + half), radius=11,
                        fill=(*fire["glow"], 255), outline=INK, width=4)
    d.rounded_rectangle((blade_x0, cy - half * 0.5, blade_x1 - 6, cy + half * 0.5), radius=6, fill=fire["core"])

    # The hilt: dark steel, a guard at the blade, two gold bands, a pommel.
    d.rounded_rectangle((hilt_x0, cy - half * 1.15, blade_x0 + 4, cy + half * 1.15), radius=6,
                        fill=HILT, outline=INK, width=6)
    d.rectangle((hilt_x0 + 8, cy - half * 0.8, blade_x0 - 6, cy - half * 0.3), fill=HILT_HI)
    for x in (hilt_x0 + 22, hilt_x0 + 50):
        d.rectangle((x, cy - half * 1.15 + 4, x + 10, cy + half * 1.15 - 4), fill=BAND)
    d.rounded_rectangle((blade_x0 - 8, cy - half * 1.9, blade_x0 + 8, cy + half * 1.9), radius=5,
                        fill=HILT_HI, outline=INK, width=5)
    d.ellipse((hilt_x0 - 14, cy - half * 1.3, hilt_x0 + 12, cy + half * 1.3), fill=BAND, outline=INK, width=5)
    return img


def _render(animation: str, frame: int) -> Image.Image:
    fire = COLD if animation == "fly_cold" else HOT
    turn = 360.0 * (frame % TURN_FRAMES) / TURN_FRAMES
    img = _saber(frame, fire).rotate(turn, resample=Image.Resampling.BICUBIC)
    return img.resize(FINAL, Image.Resampling.LANCZOS)


def _build(out_dir: Path):
    return build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=lambda anim, frame_idx, _nframes: _render(anim, frame_idx),
        out_dir=out_dir,
        frame_size=FINAL,
        # One frame box for the whole turn: the saber turns about its middle.
        auto_crop=False,
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
