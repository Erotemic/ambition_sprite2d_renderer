"""The drawing kit of the cast of the Art dimension.

The concept sheets draw the cast as cel-shaded shapes in flat colour, each
with one thick dark outline round its whole silhouette. This kit draws a
frame that way:

- each shape is drawn in work pixels (``SUPER`` times the published size)
  in the order it is called, as a painter paints;
- a shape that is part of the body adds to the silhouette, and the outline
  is the silhouette made wider, under the shapes;
- lines inside the silhouette (a mouth, a fold, a crack) are drawn in ink
  and do not change the outline;
- a glow (living ink, a lit eye) is drawn on its own layer, over the
  outline, and adds no outline.

Coordinates are published pixels of the frame, with ``y`` down. Each target
faces right and stands with its feet on its ground row.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter

from ambition_sprite2d_renderer.core.draw import blending_draw

from ...authoring.sheet_build import build_sheet

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

SUPER = 4
TRANSPARENT: RGBA = (0, 0, 0, 0)

#: The palette of the dimension (the concept sheets).
PAPER: RGBA = (248, 244, 234, 255)
PAPER_SHADE: RGBA = (214, 206, 190, 255)
INK: RGBA = (34, 22, 52, 255)
MAGENTA: RGBA = (232, 54, 172, 255)
MAGENTA_LIGHT: RGBA = (255, 140, 214, 255)
CYAN: RGBA = (40, 200, 236, 255)
CYAN_LIGHT: RGBA = (160, 240, 255, 255)
YELLOW: RGBA = (255, 210, 50, 255)
VIOLET: RGBA = (118, 64, 196, 255)
VIOLET_DARK: RGBA = (62, 30, 112, 255)
MARBLE: RGBA = (226, 224, 236, 255)
MARBLE_SHADE: RGBA = (168, 164, 188, 255)
STEEL: RGBA = (210, 214, 228, 255)
STEEL_SHADE: RGBA = (130, 136, 160, 255)
WOOD: RGBA = (176, 120, 70, 255)
WOOD_DARK: RGBA = (118, 74, 40, 255)
GOLD: RGBA = (240, 186, 60, 255)
GOLD_DARK: RGBA = (176, 118, 30, 255)
WHITE: RGBA = (255, 255, 255, 255)
MOSS: RGBA = (110, 170, 70, 255)


def shade(colour: RGBA, k: float) -> RGBA:
    """`colour` made darker (`k` under 1) or lighter (over 1, toward white)."""
    if k <= 1.0:
        return (int(colour[0] * k), int(colour[1] * k), int(colour[2] * k), colour[3])
    t = min(1.0, k - 1.0)
    return tuple(int(c + (255 - c) * t) for c in colour[:3]) + (colour[3],)  # type: ignore[return-value]


def alpha(colour: RGBA, a: float) -> RGBA:
    return (colour[0], colour[1], colour[2], int(max(0.0, min(1.0, a)) * colour[3]))


def turn(points: Iterable[Point], cx: float, cy: float, degrees: float) -> List[Point]:
    """`points` turned by `degrees` (clockwise on the screen) about `(cx, cy)`."""
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in points]


def ellipse_points(cx: float, cy: float, rx: float, ry: float, count: int = 28, jitter: float = 0.0, rng: Optional[random.Random] = None) -> List[Point]:
    """An ellipse as a polygon. `jitter` moves each point by up to that many
    pixels, as a line drawn by hand wavers."""
    pts = []
    for k in range(count):
        a = math.tau * k / count
        j = rng.uniform(-jitter, jitter) if (jitter and rng) else 0.0
        pts.append((cx + (rx + j) * math.cos(a), cy + (ry + j) * math.sin(a)))
    return pts


def grow(points: Sequence[Point], d: float) -> List[Point]:
    """`points` moved `d` pixels away from their middle: a shape a little
    larger, to draw an ink ring under the shape itself."""
    cx = sum(x for x, _ in points) / len(points)
    cy = sum(y for _, y in points) / len(points)
    out = []
    for x, y in points:
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy) or 1.0
        out.append((x + dx / r * d, y + dy / r * d))
    return out


def phase(anim_frame: int, frames: int, loop: bool) -> float:
    """0..1 through a row: a loop does not reach 1 (its last frame leads to
    the first); a row that plays once ends on 1."""
    return anim_frame / float(frames) if loop else anim_frame / float(max(1, frames - 1))


class Frame:
    """One frame in work."""

    def __init__(self, size: Tuple[int, int]) -> None:
        self.size = size
        work = (size[0] * SUPER, size[1] * SUPER)
        self.image = Image.new("RGBA", work, TRANSPARENT)
        self.silhouette = Image.new("L", work, 0)
        self.glow_layer = Image.new("RGBA", work, TRANSPARENT)
        self._draw = blending_draw(self.image)
        self._sil = ImageDraw.Draw(self.silhouette)  # raw-draw-ok: an L mask has no alpha to composite
        self._glow = blending_draw(self.glow_layer)

    @staticmethod
    def _w(points: Iterable[Point]) -> List[Tuple[float, float]]:
        return [(x * SUPER, y * SUPER) for x, y in points]

    # -- shapes of the body --------------------------------------------------

    def poly(self, points: Sequence[Point], fill: RGBA, body: bool = True) -> None:
        pts = self._w(points)
        self._draw.polygon(pts, fill=fill)
        if body:
            self._sil.polygon(pts, fill=255)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, fill: RGBA, body: bool = True) -> None:
        box = [(cx - rx) * SUPER, (cy - ry) * SUPER, (cx + rx) * SUPER, (cy + ry) * SUPER]
        self._draw.ellipse(box, fill=fill)
        if body:
            self._sil.ellipse(box, fill=255)

    def limb(self, points: Sequence[Point], width: float, fill: RGBA, body: bool = True) -> None:
        """A thick line with round joints and ends: an arm, a leg, a handle."""
        pts = self._w(points)
        w = max(1, int(round(width * SUPER)))
        self._draw.line(pts, fill=fill, width=w, joint="curve")
        r = width * SUPER / 2.0
        for x, y in (pts[0], pts[-1]):
            self._draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)
        if body:
            self._sil.line(pts, fill=255, width=w, joint="curve")
            for x, y in (pts[0], pts[-1]):
                self._sil.ellipse([x - r, y - r, x + r, y + r], fill=255)

    # -- lines and light -----------------------------------------------------

    def ink(self, points: Sequence[Point], width: float = 1.2, fill: RGBA = INK) -> None:
        """A line inside the body: it is drawn, and the outline does not grow."""
        self._draw.line(self._w(points), fill=fill, width=max(1, int(round(width * SUPER))), joint="curve")

    def dot(self, cx: float, cy: float, r: float, fill: RGBA = INK) -> None:
        self._draw.ellipse([(cx - r) * SUPER, (cy - r) * SUPER, (cx + r) * SUPER, (cy + r) * SUPER], fill=fill)

    def glow(self, cx: float, cy: float, r: float, fill: RGBA) -> None:
        """A soft round light, drawn over everything."""
        self._glow.ellipse([(cx - r) * SUPER, (cy - r) * SUPER, (cx + r) * SUPER, (cy + r) * SUPER], fill=fill)

    def glow_poly(self, points: Sequence[Point], fill: RGBA) -> None:
        self._glow.polygon(self._w(points), fill=fill)

    def glow_line(self, points: Sequence[Point], width: float, fill: RGBA) -> None:
        self._glow.line(self._w(points), fill=fill, width=max(1, int(round(width * SUPER))), joint="curve")

    # -- the picture ---------------------------------------------------------

    def finish(self, outline: RGBA = INK, width: float = 1.6, glow_blur: float = 2.5, fade: float = 1.0) -> Image.Image:
        """The frame at its published size: the outline under the shapes, the
        glow over them. `fade` multiplies the alpha of the whole frame."""
        reach = max(1, int(round(width * SUPER)))
        wide = self.silhouette.filter(ImageFilter.MaxFilter(2 * reach + 1))
        out = Image.new("RGBA", self.image.size, TRANSPARENT)
        out.paste(outline, mask=wide)
        out.alpha_composite(self.image)
        if self.glow_layer.getbbox():
            soft = self.glow_layer.filter(ImageFilter.GaussianBlur(glow_blur * SUPER))
            out.alpha_composite(soft)
            out.alpha_composite(self.glow_layer)
        if fade < 1.0:
            a = out.getchannel("A").point(lambda v: int(v * max(0.0, fade)))
            out.putalpha(a)
        return out.resize(self.size, Image.Resampling.LANCZOS)


def render_target(target: str, rows, render_frame, frame_size, actor_metadata, out_dir, **opts) -> List[Path]:
    """Publish one target's sheet with the shared builder."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=target,
        rows=rows,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=opts.get("frame_size", frame_size),
        auto_crop=False,
        actor_metadata=actor_metadata,
        animation_key_map={name: name for name, _frames, _duration in rows},
    )
    return [outputs[key] for key in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")]


def enemy_metadata(character_id: str, display_name: str, body_plan: str, body_kind: str, mass: str, locomotion: str, traits: Sequence[str], description: str) -> dict:
    """The actor sidecar of an enemy of the dimension: its rows are the enemy
    contract (`docs/planning/game/enemy-patterns.md`)."""
    return {
        "actor": {"character_id": character_id, "display_name": display_name},
        "body": {"body_plan": body_plan, "body_kind": body_kind, "mass_class": mass, "traits": list(traits), "locomotion_hint": locomotion},
        "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
        "tags": ["enemy", "art"],
        "authoring_description": description,
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "combat.hurt": {"animation": "hit", "events": []},
            "combat.death": {"animation": "death", "events": []},
        },
    }


#: The rows of each enemy of the dimension: the cycle of
#: `docs/planning/game/enemy-patterns.md` (notice, windup, the strike), and
#: a hit and a death.
ENEMY_ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 140),
    ("walk", 8, 90),
    ("notice", 4, 110),
    ("windup", 4, 90),
    ("attack_side", 6, 70),
    ("hit", 3, 90),
    ("death", 6, 110),
]
LOOPS = {"idle", "walk", "windup"}
