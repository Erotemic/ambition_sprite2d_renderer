"""The bossofthegame's keystrokes: keycaps that fall on the player.

In his fight's second phase (the game's ``docs/planning/game/final-boss.md``)
he types, and what he types falls: each keystroke is a keycap of a mechanical
keyboard, its letter on its top. One row per letter, ``a`` to ``z``, and
``back`` (the backspace key, an arrow to the left), so a
projectile look names its letter by the row (``keycap_k`` draws the row
``k``). Each row is two frames: the key turns a little as it falls.

The letters are drawn as geometry from a 5 x 7 dot font here, not from a
system font, so the sheet is the same on every machine.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ambition_sprite2d_renderer.core.draw import blending_draw

from ...authoring.sheet_build import build_sheet, write_canonical

TARGET_NAME = "boss_keycaps"

FRAME_W, FRAME_H = 40, 40
SUPERSAMPLE = 4

#: A 5 x 7 dot font: each letter is seven rows of five dots, "#" inked.
FONT = {
    "a": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "b": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "c": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "d": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "e": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "f": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "g": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    "h": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "i": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "j": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "k": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "l": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "m": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "n": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "o": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "p": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "r": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "s": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "t": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "u": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "v": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "w": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "x": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    # The backspace key: an arrow to the left.
    "back": ["..#..", ".#...", "#####", ".#...", "..#..", ".....", "#####"],
}

#: (name, frames, ms): one row per letter.
ROWS: List[Tuple[str, int, int]] = [(letter, 2, 120) for letter in sorted(FONT)]

CAP_SIDE = (156, 150, 140)
CAP_TOP = (242, 238, 228)
CAP_SHINE = (255, 255, 250)
INK = (30, 28, 34)
LEGEND = (40, 36, 46)


def _box(draw, x0, y0, x1, y1, colour, r=0.0):
    s = SUPERSAMPLE
    draw.rounded_rectangle([x0 * s, y0 * s, x1 * s, y1 * s], radius=r * s, fill=tuple(colour) + (255,))


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    del nframes
    img = Image.new("RGBA", (FRAME_W * SUPERSAMPLE, FRAME_H * SUPERSAMPLE), (0, 0, 0, 0))
    draw = blending_draw(img)
    # the key: an ink rim, the skirt, the dished top a little up and back
    _box(draw, 3, 4, 37, 37, INK, 6)
    _box(draw, 5, 6, 35, 35, CAP_SIDE, 5)
    _box(draw, 8, 7, 32, 29, CAP_TOP, 4)
    _box(draw, 9, 8, 31, 11, CAP_SHINE, 2)
    # the letter, 5 x 7 dots of 3 px, on the top
    rows = FONT.get(animation, FONT["x"])
    ox, oy = 20 - 7.5, 18 - 10.5
    for j, line in enumerate(rows):
        for i, dot in enumerate(line):
            if dot == "#":
                _box(draw, ox + i * 3, oy + j * 3, ox + i * 3 + 3, oy + j * 3 + 3, LEGEND)
    small = img.resize((FRAME_W, FRAME_H), Image.LANCZOS)
    # it turns a little as it falls
    return small.rotate(-6 if frame_idx % 2 else 6, resample=Image.BICUBIC)


ACTOR_METADATA = {
    "actor": {"character_id": "prop_boss_keycaps", "display_name": "Keystrokes"},
    "visual_description": {
        "intent": "A keycap of a mechanical keyboard with one letter on its top: what the bossofthegame types falls on the player.",
    },
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        auto_crop=True,
        crop_margin=2,
        actor_metadata=ACTOR_METADATA,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=(FRAME_W, FRAME_H))


__all__ = ["ACTOR_METADATA", "ROWS", "TARGET_NAME", "render", "render_canonical", "render_frame"]
