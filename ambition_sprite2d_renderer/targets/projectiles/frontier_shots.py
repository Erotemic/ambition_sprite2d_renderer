"""Marshal Gallus's thrown things (`docs/planning/game/leadensaddle.md`): the
stick of dynamite he lobs and the tumbleweeds his whistle drives down the
corral. Each is a projectile look (`projectile_visuals.ron`).

- `gallus_dynamite`: a red stick with a black band, its fuse fizzing. It
  spins as it flies (`travel`, looping); the look's rotation is
  `GravityUpright`, so the spin is drawn here, not by the game.
- `gallus_tumbleweed`: a ball of dry stems that rolls (`travel`, looping):
  the stems turn, the outline stays round.

Both are drawn travelling +x.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFilter

from ...authoring.sheet_build import build_sheet

SS = 4


def _canvas(w, h):
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)  # raw-draw-ok: opaque strokes on a clear canvas


def _poly(d, pts, fill):
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill)


def _line(d, pts, w, fill):
    d.line([(x * SS, y * SS) for x, y in pts], fill=fill, width=max(1, int(w * SS)), joint="curve")


def _dot(d, x, y, r, fill):
    d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=fill)


DYN_W, DYN_H = 40, 40


def _dynamite(frame_idx: int, nframes: int) -> Image.Image:
    img, d = _canvas(DYN_W, DYN_H)
    a = frame_idx / nframes * math.tau
    cx, cy, half_l, half_w = 20, 20, 11, 4.2
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux

    def at(s, t):
        return (cx + ux * s + vx * t, cy + uy * s + vy * t)

    _poly(d, [at(-half_l, -half_w), at(half_l, -half_w), at(half_l, half_w), at(-half_l, half_w)], (178, 40, 34, 255))
    _poly(d, [at(-half_l, -half_w), at(half_l, -half_w), at(half_l, -half_w * 0.3), at(-half_l, -half_w * 0.3)], (220, 82, 64, 255))
    for s in (-half_l * 0.45, half_l * 0.45):
        _poly(d, [at(s - 1.2, -half_w), at(s + 1.2, -half_w), at(s + 1.2, half_w), at(s - 1.2, half_w)], (30, 26, 26, 255))
    # The fuse from one end, and its spark.
    tip = at(half_l + 6, 2.5 * math.sin(a * 3))
    _line(d, [at(half_l, 0), at(half_l + 3, 1.5), tip], 1.0, (60, 52, 44, 255))
    flick = 1.0 + 0.4 * math.sin(frame_idx * 2.1)
    _dot(d, tip[0], tip[1], 2.6 * flick, (255, 200, 90, 200))
    _dot(d, tip[0], tip[1], 1.2 * flick, (255, 250, 220, 255))
    for i in range(3):
        sa = a + i * 2.1 + frame_idx
        _dot(d, tip[0] + math.cos(sa) * 3.5, tip[1] + math.sin(sa) * 3.5, 0.6, (255, 220, 120, 255))
    return img.resize((DYN_W, DYN_H), Image.LANCZOS)


WEED_W, WEED_H = 48, 48


def _tumbleweed(frame_idx: int, nframes: int) -> Image.Image:
    img, d = _canvas(WEED_W, WEED_H)
    a = frame_idx / nframes * math.tau
    cx, cy, r = 24, 24, 19
    _dot(d, cx, cy, r * 0.8, (96, 70, 40, 60))
    for i in range(46):
        # Stems as arcs of chords of the ball, turned by the roll.
        p = i * 2.399 + a
        q = p + 1.4 + (i % 5) * 0.35
        rr = r * (0.55 + 0.45 * ((i * 37) % 11) / 10)
        mid = ((math.cos(p) + math.cos(q)) * rr * 0.3, (math.sin(p) + math.sin(q)) * rr * 0.3)
        pts = [(cx + math.cos(p) * rr, cy + math.sin(p) * rr), (cx + mid[0], cy + mid[1]), (cx + math.cos(q) * rr, cy + math.sin(q) * rr)]
        shade = 96 + (i * 23) % 110
        _line(d, pts, 1.3, (shade, int(shade * 0.76), int(shade * 0.46), 255))
    out = img.resize((WEED_W, WEED_H), Image.LANCZOS)
    return out.filter(ImageFilter.GaussianBlur(0.2))


def _target(name, draw, size, frames, ms, intent):
    rows = [("travel", frames, ms)]
    meta = {
        "actor": {"character_id": f"prop_{name}", "display_name": name.replace("_", " ").title()},
        "visual_description": {"intent": intent},
        "tags": ["projectile", "frontier", "marshal_gallus"],
    }

    def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
        del animation
        return draw(frame_idx, nframes)

    def render(out_dir: str | Path, **opts) -> List[Path]:
        del opts
        outputs = build_sheet(target=name, rows=rows, render_fn=render_frame, out_dir=Path(out_dir), frame_size=size,
                              auto_crop=False, actor_metadata=meta)
        keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
        return [Path(outputs[key]) for key in keys if outputs.get(key)]

    return {"render": render, "actor_metadata": meta}


TARGETS = {
    "gallus_dynamite": _target("gallus_dynamite", _dynamite, (DYN_W, DYN_H), 8, 60,
                               "A stick of dynamite, its fuse lit, spinning end over end."),
    "gallus_tumbleweed": _target("gallus_tumbleweed", _tumbleweed, (WEED_W, WEED_H), 8, 70,
                                 "A tumbleweed rolling: dry stems in a ball."),
}

__all__ = ["TARGETS"]
