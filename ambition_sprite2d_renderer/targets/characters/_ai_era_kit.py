"""The paint box of the redrawn AI-era enemies (synthetic friend, spaghetti
event, helpful liar, agent swarm).

One look for all of them: a thing is a silhouette, grown into a dark outline,
filled, lit on the edge that faces the light and shaded on the edge that does
not (``Kit.solid``). A thing is painted once with its anchor at ``Kit.home``
and placed, and turned, where it sits, so a part flipbook stores each once.

Lengths are frame pixels; a turn is degrees, clockwise.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageChops, ImageFilter

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]
Part = Tuple[Image.Image, Point]

TRANSPARENT: RGBA = (0, 0, 0, 0)
OUTLINE: RGBA = (34, 22, 48, 255)
WHITE: RGBA = (255, 255, 255, 255)


def mix(a: RGBA, b: RGBA, t: float) -> RGBA:
    return tuple(int(round(a[i] * (1.0 - t) + b[i] * t)) for i in range(4))  # type: ignore[return-value]


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def turned(p: Point, degrees: float) -> Point:
    a = math.radians(degrees)
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


def bezier(a: Point, b: Point, c: Point, e: Point, steps: int = 16) -> List[Point]:
    pts: List[Point] = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        w = (u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t)
        pts.append((w[0] * a[0] + w[1] * b[0] + w[2] * c[0] + w[3] * e[0], w[0] * a[1] + w[1] * b[1] + w[2] * c[1] + w[3] * e[1]))
    return pts


class Kit:
    """The paint box for one frame size."""

    def __init__(self, frame: Tuple[int, int], supersample: int = 4) -> None:
        self.frame = frame
        self.scale = supersample
        self.canvas = (frame[0] * supersample, frame[1] * supersample)
        #: Where a piece's anchor is painted on the scratch canvas, which is
        #: twice the frame.
        self.home: Point = (float(frame[0]), float(frame[1]))
        self._pieces: Dict[tuple, Optional[Part]] = {}

    # -- units ---------------------------------------------------------------

    def s(self, v: float) -> int:
        return int(round(v * self.scale))

    def pt(self, p: Point) -> Tuple[int, int]:
        return (self.s(p[0]), self.s(p[1]))

    def at(self, x: float, y: float) -> Point:
        """The point ``(x, y)`` from ``home``."""
        return (self.home[0] + x, self.home[1] + y)

    # -- strokes ---------------------------------------------------------------

    def line(self, d, pts: Sequence[Point], fill: RGBA, width: float) -> None:
        d.line([self.pt(p) for p in pts], fill=fill, width=max(1, self.s(width)), joint="curve")

    def stroke(self, d, pts: Sequence[Point], fill: RGBA, width: float) -> None:
        """A line with round ends."""
        self.line(d, pts, fill, width)
        for p in (pts[0], pts[-1]):
            self.oval(d, p, width / 2.0, width / 2.0, fill)

    def poly(self, d, pts: Sequence[Point], fill: RGBA, outline: Optional[RGBA] = None, width: float = 1.0) -> None:
        ipts = [self.pt(p) for p in pts]
        d.polygon(ipts, fill=fill)
        if outline is not None:
            d.line(ipts + [ipts[0]], fill=outline, width=max(1, self.s(width)), joint="curve")

    def oval(self, d, c: Point, rx: float, ry: float, fill: RGBA, outline: Optional[RGBA] = None, width: float = 1.0) -> None:
        box = (self.s(c[0] - rx), self.s(c[1] - ry), self.s(c[0] + rx), self.s(c[1] + ry))
        d.ellipse(box, fill=fill, outline=outline, width=max(1, self.s(width)) if outline else 0)

    def rrect(self, d, x0: float, y0: float, x1: float, y1: float, radius: float, fill: RGBA, outline: Optional[RGBA] = None,
              width: float = 1.0) -> None:
        d.rounded_rectangle((self.s(x0), self.s(y0), self.s(x1), self.s(y1)), radius=self.s(radius), fill=fill, outline=outline,
                            width=max(1, self.s(width)) if outline else 0)

    def star4(self, d, c: Point, r: float, fill: RGBA, outline: Optional[RGBA] = OUTLINE, width: float = 0.9, waist: float = 0.34) -> None:
        """The four-pointed sparkle."""
        pts = []
        for i in range(8):
            a = math.radians(i * 45.0 - 90.0)
            rr = r if i % 2 == 0 else r * waist
            pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
        self.poly(d, pts, fill, outline, width)

    def heart(self, d, c: Point, r: float, fill: RGBA, outline: Optional[RGBA] = OUTLINE, width: float = 0.9) -> None:
        pts = []
        for i in range(40):
            t = math.tau * i / 40
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            pts.append((c[0] + x * r / 16.0, c[1] + y * r / 16.0))
        self.poly(d, pts, fill, outline, width)

    def tick(self, d, c: Point, r: float, fill: RGBA, width: float) -> None:
        """A check mark."""
        self.stroke(d, [(c[0] - r, c[1]), (c[0] - 0.3 * r, c[1] + 0.7 * r), (c[0] + r, c[1] - 0.8 * r)], fill, width)

    def cross(self, d, c: Point, r: float, fill: RGBA, width: float) -> None:
        for sign in (-1.0, 1.0):
            self.stroke(d, [(c[0] - r, c[1] - r * sign), (c[0] + r, c[1] + r * sign)], fill, width)

    # -- pieces ----------------------------------------------------------------

    def scratch(self, fill: RGBA = TRANSPARENT) -> Image.Image:
        return Image.new("RGBA", (self.canvas[0] * 2, self.canvas[1] * 2), fill)

    def _cut(self, canvas: Image.Image) -> Optional[Part]:
        box = canvas.getchannel("A").getbbox()
        if box is None:
            return None
        return (canvas.crop(box), (self.home[0] * self.scale - box[0], self.home[1] * self.scale - box[1]))

    def piece(self, key: tuple, paint: Callable) -> Optional[Part]:
        """What ``paint(draw)`` paints with its anchor at ``home``, cut to its
        box. ``key`` names everything ``paint`` reads."""
        if key not in self._pieces:
            canvas = self.scratch()
            paint(blending_draw(canvas))
            self._pieces[key] = self._cut(canvas)
        return self._pieces[key]

    def solid(
        self,
        key: tuple,
        shape: Callable,
        fill: Union[RGBA, Callable],
        detail: Optional[Callable] = None,
        *,
        outline: float = 1.3,
        rim: float = 0.36,
        shade: float = 0.34,
        shade_colour: Optional[RGBA] = None,
        light: Point = (3.0, -4.0),
        dark: Point = (-4.0, 5.5),
    ) -> Optional[Part]:
        """A lit thing with an outline. ``shape(draw)`` paints its silhouette
        (any opaque colour) about ``home``; ``fill`` is its colour, or
        ``fill(draw)`` painting all of a canvas; ``detail(draw)`` paints on it
        and is cut to the silhouette. ``rim`` and ``shade`` are how strong the
        light and the dark on its edges are."""
        if key in self._pieces:
            return self._pieces[key]
        canvas = self.scratch()
        shape(blending_draw(canvas))
        mask = canvas.getchannel("A")
        box = mask.getbbox()
        if box is None:
            self._pieces[key] = None
            return None
        pad = self.s(max(outline, abs(light[0]), abs(light[1]), abs(dark[0]), abs(dark[1]))) + 4
        region = (max(0, box[0] - pad), max(0, box[1] - pad), min(mask.size[0], box[2] + pad), min(mask.size[1], box[3] + pad))
        mask = mask.crop(region)
        if callable(fill):
            painted = self.scratch()
            fill(blending_draw(painted))
            body = painted.crop(region)
            base = body.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
        else:
            body = Image.new("RGBA", mask.size, fill)
            base = fill

        def edge(dx: float, dy: float) -> Image.Image:
            """The part of it that has nothing of it ``(dx, dy)`` away."""
            return ImageChops.multiply(mask, ImageChops.invert(ImageChops.offset(mask, -self.s(dx), -self.s(dy))))

        if rim > 0.0:
            lit = Image.new("RGBA", mask.size, WHITE)
            lit.putalpha(edge(*light).point(lambda a: int(a * rim)))
            body.alpha_composite(lit)
        if shade > 0.0:
            colour = shade_colour or mix((base[0], base[1], base[2], 255), (40, 20, 70, 255), 0.75)
            dim = Image.new("RGBA", mask.size, colour)
            dim.putalpha(edge(*dark).point(lambda a: int(a * shade)))
            body.alpha_composite(dim)
        if detail is not None:
            layer = self.scratch()
            detail(blending_draw(layer))
            body.alpha_composite(layer.crop(region))
        body.putalpha(mask)
        out = Image.new("RGBA", mask.size, OUTLINE)
        out.putalpha(mask.filter(ImageFilter.MaxFilter(2 * self.s(outline) + 1)) if outline > 0.0 else mask)
        out.alpha_composite(body)
        part = (out, (self.home[0] * self.scale - region[0], self.home[1] * self.scale - region[1]))
        self._pieces[key] = part
        return part

    def place(self, img: Image.Image, part: Optional[Part], at: Point, name: str, degrees: float = 0.0) -> None:
        if part is not None:
            shape_rig.place(img, part, (at[0] * self.scale, at[1] * self.scale), degrees, name)

    def put(self, img: Image.Image, key: tuple, paint: Callable, at: Point, name: str, degrees: float = 0.0) -> None:
        self.place(img, self.piece(key, paint), at, name, degrees)

    # -- frames ----------------------------------------------------------------

    def new_frame(self) -> Image.Image:
        return Image.new("RGBA", self.canvas, TRANSPARENT)

    def downsample(self, img: Image.Image) -> Image.Image:
        return rigdoc.downsampled_canvas(img, self.frame, Image.Resampling.LANCZOS)

    def body_metrics(self, box: Tuple[float, float, float, float]) -> Callable[[int, int], dict]:
        """The ``body_metrics_fn`` of a body whose box is ``(x0, y0, x1, y1)``
        and whose feet are at the middle of its low edge."""

        def metrics(fw: int, fh: int) -> dict:
            x, y = int(math.floor(box[0])), int(math.floor(box[1]))
            w, h = int(math.ceil(box[2])) - x, int(math.ceil(box[3])) - y
            feet = (x + w / 2.0, float(y + h))
            return {
                "body_pixel_bbox": {"x": x, "y": y, "w": w, "h": h},
                "feet_pixel": {"x": feet[0], "y": feet[1]},
                "feet_anchor_norm": {"x": round((feet[0] - fw / 2.0) / fw, 6), "y": round((fh / 2.0 - feet[1]) / fh, 6)},
            }

        return metrics

    def render(self, target: str, rows: List[Tuple[str, int, int]], frame_fn: Callable[[str, int, int], Image.Image], out_dir: Union[str, Path],
               actor_metadata: dict, body_box: Tuple[float, float, float, float]) -> List[Path]:
        """Publish the sheet and its part flipbook."""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        frame_transform: dict = {}
        outputs = build_sheet(
            frame_transform_out=frame_transform,
            target=target,
            rows=rows,
            render_fn=frame_fn,
            out_dir=out_dir,
            frame_size=self.frame,
            auto_crop=False,
            actor_metadata=actor_metadata,
            body_metrics_fn=self.body_metrics(body_box),
        )
        parts = publish_rig_flipbook(target, rows, frame_fn, outputs, frame_transform, out_dir)
        return [outputs[k] for k in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")] + list(parts.values())


def actor_metadata(character_id: str, display_name: str, *, attack_row: str, ranged: bool, traits: List[str], description: str,
                   gameplay: str) -> dict:
    """The actor contract of a ground walker with one attack row."""
    binding = "action.ranged.primary" if ranged else "action.melee.primary"
    events = (
        [{"t": 0.5, "event": "projectile_release", "source": "explicit.profile.ai_era"}]
        if ranged
        else [
            {"t": 0.35, "event": "hitbox_active_start", "source": "explicit.profile.ai_era"},
            {"t": 0.6, "event": "hitbox_active_end", "source": "explicit.profile.ai_era"},
        ]
    )
    return {
        "actor": {"character_id": character_id, "display_name": display_name},
        "body": {"body_plan": "PropActor", "body_kind": "Standard", "mass_class": "Light", "traits": traits, "locomotion_hint": "Walk"},
        "capabilities": {
            "traversal": {"walk": True, "jump": None, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": None,
                          "door_access": []},
            "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": []},
        },
        "brain": {"default_preset": "skirmisher_ranger" if ranged else "melee_brute_striker"},
        "actions": {"default_preset": "ranger_arrow" if ranged else "striker_swipe"},
        "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
        "tags": traits,
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            binding: {"animation": attack_row, "events": events},
            "combat.hurt": {"animation": "hurt", "events": []},
            "combat.death": {"animation": "death", "events": []},
        },
        "authoring_description": description,
        "gameplay_description": gameplay,
    }
