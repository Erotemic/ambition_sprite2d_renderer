"""The paint box of the redrawn AI-era enemies (synthetic friend, spaghetti
event, helpful liar, agent swarm).

One look for all of them: a thing is a silhouette, grown into a dark outline,
filled, lit on the edge that faces the light and shaded on the edge that does
not (``Kit.solid``). A thing is painted once with its anchor at ``Kit.home``
and placed, and turned, where it sits, so a part flipbook stores each once.

Lengths are frame pixels; a turn is degrees, clockwise.
"""

from __future__ import annotations

import contextlib
import math
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Tuple, Union

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


Pose = Dict[str, object]


def polar_lerp(a: Point, b: Point, t: float) -> Point:
    """``t`` of the way from offset ``a`` to offset ``b`` round their origin:
    the turn and the reach go across, so a hand swings in an arc about its
    shoulder and does not cut through the body. The turn goes the short way."""
    ra, rb = math.hypot(*a), math.hypot(*b)
    if ra < 1e-6 or rb < 1e-6:
        return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))
    aa, ab = math.atan2(a[1], a[0]), math.atan2(b[1], b[0])
    d = (ab - aa + math.pi) % math.tau - math.pi
    ang, r = aa + d * t, lerp(ra, rb, t)
    return (r * math.cos(ang), r * math.sin(ang))


def blend(a: Pose, b: Pose, t: float, polar: Sequence[str] = ()) -> Pose:
    """The pose ``t`` of the way from ``a`` to ``b``: numbers and tuples of
    numbers go across, a word changes at the middle. A key in ``polar`` (an
    offset) goes across in an arc (``polar_lerp``)."""
    out: Pose = {}
    for k, va in a.items():
        vb = b[k]
        if k in polar:
            out[k] = polar_lerp(va, vb, t)  # type: ignore[arg-type]
        elif isinstance(va, str):
            out[k] = vb if t >= 0.5 else va
        elif isinstance(va, tuple):
            out[k] = tuple(lerp(x, y, t) for x, y in zip(va, vb))  # type: ignore[arg-type]
        else:
            out[k] = lerp(float(va), float(vb), t)  # type: ignore[arg-type]
    return out


def _back(t: float) -> float:
    """Past the key and back to it: an overshoot of about a tenth."""
    c = 1.7
    t = max(0.0, min(1.0, t)) - 1.0
    return 1.0 + (c + 1.0) * t * t * t + c * t * t


#: How the motion arrives at a key (the third item of a ``keys`` frame):
#: ``io`` starts and stops gently (the default); ``in`` gathers and leaves
#: fast (into a strike); ``out`` leaves fast and settles (out of a strike);
#: ``snap`` is most of the way in the first quarter (a blow, a jolt);
#: ``back`` goes past the key and returns (follow-through); ``hold`` keeps the
#: pose before until the key (a held frame, then a cut); ``linear`` is even.
EASES: Dict[str, Callable[[float], float]] = {
    "io": ease,
    "in": lambda t: max(0.0, min(1.0, t)) ** 2,
    "out": lambda t: 1.0 - (1.0 - max(0.0, min(1.0, t))) ** 2,
    "snap": lambda t: 1.0 - (1.0 - max(0.0, min(1.0, t))) ** 4,
    "back": _back,
    "hold": lambda t: 1.0 if t >= 1.0 else 0.0,
    "linear": lambda t: max(0.0, min(1.0, t)),
}


def keys(u: float, frames: Sequence[tuple], polar: Sequence[str] = ()) -> Pose:
    """The pose at ``u`` of a row that goes through ``frames``: ``(when,
    pose)``, or ``(when, pose, how)`` with ``how`` a name of ``EASES`` for the
    way the motion arrives at that key. Keys in ``polar`` blend in arcs."""
    if u <= frames[0][0]:
        return frames[0][1]
    for f0, f1 in zip(frames, frames[1:]):
        u0, p0, u1, p1 = f0[0], f0[1], f1[0], f1[1]
        if u <= u1:
            how = EASES[f1[2] if len(f1) > 2 else "io"]
            return blend(p0, p1, how((u - u0) / max(1e-6, u1 - u0)), polar)
    return frames[-1][1]


def solve(root: Point, target: Point, first: float, second: float, side: float) -> Tuple[Point, Point]:
    """The middle joint and the end of a two-bone limb from ``root`` toward
    ``target`` (the end stops short if the limb cannot reach). ``side``: 1
    bends it to the left of the way it points, -1 to the right."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    dist = math.hypot(dx, dy)
    if dist < 1e-3:
        dx, dy, dist = 0.0, 1.0, 1.0
    ux, uy = dx / dist, dy / dist
    span = max(abs(first - second) + 0.05, min(first + second - 0.05, dist))
    along = (first * first - second * second + span * span) / (2.0 * span)
    off = math.sqrt(max(0.0, first * first - along * along))
    joint = (root[0] + ux * along - uy * off * side, root[1] + uy * along + ux * off * side)
    return joint, (root[0] + ux * span, root[1] + uy * span)


def angle(a: Point, b: Point) -> float:
    """The turn of the way from ``a`` to ``b``."""
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def pin(p: Point) -> Point:
    """The whole frame pixel nearest ``p``: where an ``aligned`` piece goes."""
    return (float(round(p[0])), float(round(p[1])))


class Kit:
    """The paint box for one frame size."""

    def __init__(self, frame: Tuple[int, int], supersample: int = 4, ink: RGBA = OUTLINE, out: Optional[Tuple[int, int]] = None,
                 zoom: float = 1.0) -> None:
        #: The frame the character's lengths are in.
        self.frame = frame
        #: The frame it is published at: ``frame``, or larger for a sheet of a
        #: higher resolution (``authoring.texel_density``). The canvas is
        #: ``supersample`` times it, so it reduces to it by a whole factor, as
        #: a part flipbook records it.
        self.out = out or frame
        self.reduce = supersample
        #: The colour of every outline ``solid`` grows.
        self.ink = ink
        #: Canvas pixels per frame pixel. ``zoom`` paints a kit's pieces
        #: larger than its frame's lengths (a head drawn bigger than the body's
        #: lines would draw it).
        scale = supersample * self.out[0] / frame[0] * zoom
        # A whole scale stays an int: a character reads it as one (a resize
        # to `size * scale`).
        self.scale: Union[int, float] = int(scale) if float(scale).is_integer() else scale
        self.canvas = (int(round(frame[0] * self.scale)), int(round(frame[1] * self.scale)))
        #: Where a piece's anchor is painted on the scratch canvas, which is
        #: twice the frame.
        self.home: Point = (float(frame[0]), float(frame[1]))
        self._pieces: Dict[tuple, Optional[Part]] = {}

    @contextlib.contextmanager
    def drafted(self, supersample: int = 2) -> Iterator["Kit"]:
        """This kit painting at its own FRAME size, ``supersample`` times, not
        at its published size, and as it was after: for a check that needs
        where a frame's pixels are and not how they look
        (``Person.cut_frames``).

        Its pieces are painted again at that size, so a character that holds
        the kit as a module global (``K = X.K``) drafts with it.

        A sheet published at the game's texel density paints on a canvas of
        its published size times its supersample: Wolfenstein's 924 px frame
        on 3696 px, about 2.7 s a frame, so a check of his 396 frames ran past
        20 minutes (2026-10-19). Drafted at 2x his 320 px frame it paints on
        640 px."""
        saved = (self.out, self.reduce, self.scale, self.canvas, self._pieces)
        zoom = self.scale / (self.reduce * self.out[0] / self.frame[0])
        scale = supersample * zoom
        self.out, self.reduce = self.frame, supersample
        self.scale = int(scale) if float(scale).is_integer() else scale
        self.canvas = (int(round(self.frame[0] * self.scale)), int(round(self.frame[1] * self.scale)))
        self._pieces = {}
        try:
            yield self
        finally:
            self.out, self.reduce, self.scale, self.canvas, self._pieces = saved

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

    def aligned(self, key: tuple, paint: Callable) -> Optional[Part]:
        """``piece``, cut on whole frame pixels. Placed unturned at a ``pin``,
        it lands on the frame's own pixels, and a part flipbook reproduces it
        exactly. For what does not survive being reduced and then turned: thin
        lines, and a long light edge on a dark outline (measured on
        ramen_nujan's scarf, 2026-10-11)."""
        key = ("aligned",) + tuple(key)
        if key not in self._pieces:
            canvas = self.scratch()
            paint(blending_draw(canvas))
            box = canvas.getchannel("A").getbbox()
            if box is None:
                self._pieces[key] = None
            else:
                # Whole published pixels: the canvas reduces by ``reduce``.
                step = self.reduce
                box = (box[0] - box[0] % step, box[1] - box[1] % step, box[2] + (-box[2]) % step, box[3] + (-box[3]) % step)
                self._pieces[key] = (canvas.crop(box), (self.home[0] * step - box[0], self.home[1] * step - box[1]))
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
        out = Image.new("RGBA", mask.size, self.ink)
        out.putalpha(mask.filter(ImageFilter.MaxFilter(2 * self.s(outline) + 1)) if outline > 0.0 else mask)
        out.alpha_composite(body)
        part = (out, (self.home[0] * self.scale - region[0], self.home[1] * self.scale - region[1]))
        self._pieces[key] = part
        return part

    #: ``(colour, strength)``: each part placed is shaded with it, but not the
    #: parts named in ``tint_skip``. A change of form sets it for a frame (the
    #: body is one light shape, and then it is the other form).
    tint: Optional[Tuple[Tuple[int, int, int], float]] = None
    tint_skip: Tuple[str, ...] = ()

    def place(self, img: Image.Image, part: Optional[Part], at: Point, name: str, degrees: float = 0.0, scale_y: float = 1.0) -> None:
        if part is not None:
            if self.tint is not None and name not in self.tint_skip:
                from ._toon_rig import tinted

                part = tinted(part, *self.tint)
            shape_rig.place(img, part, (at[0] * self.scale, at[1] * self.scale), degrees, name, scale_y)

    def put(self, img: Image.Image, key: tuple, paint: Callable, at: Point, name: str, degrees: float = 0.0) -> None:
        self.place(img, self.piece(key, paint), at, name, degrees)

    # -- frames ----------------------------------------------------------------

    def new_frame(self) -> Image.Image:
        return Image.new("RGBA", self.canvas, TRANSPARENT)

    def downsample(self, img: Image.Image) -> Image.Image:
        return rigdoc.downsampled_canvas(img, self.out, Image.Resampling.LANCZOS)

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
            frame_size=self.out,
            auto_crop=False,
            actor_metadata=actor_metadata,
            body_metrics_fn=self.body_metrics(tuple(v * self.out[0] / self.frame[0] for v in body_box)),  # type: ignore[arg-type]
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
