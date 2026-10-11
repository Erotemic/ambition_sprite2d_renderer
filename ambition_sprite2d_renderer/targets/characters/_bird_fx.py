"""Effects and publication shared by the side-view SVG-rigged birds built with
``rigbuild.bird`` (the chicken, the owl).

A bird's clips key the strength of each effect on ``fx.*`` channels:
``fx.peck`` (a star at the beak), ``fx.hit`` (a blow landing on the chest),
``fx.strike`` and ``fx.rake`` (the talons), ``fx.feathers`` (loose feathers
flung from the body), ``fx.drift`` (one last feather coming down),
``fx.dust`` (at the feet), ``fx.speed`` (streaks behind the body) and
``fx.notes`` (sound off an open beak). ``BirdFx`` draws them in the bird's
own feather colours.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

from PIL import Image

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from . import _creature_fx as FX
from ._svg_fighter_effects import FxCanvas, compose_rig_frame

Point = Tuple[float, float]
RGBA = Tuple[int, int, int, int]

INK = (29, 20, 24, 255)
WHITE = (255, 252, 244, 255)
STREAK = (255, 248, 226, 150)
SCRATCH = (255, 244, 214, 235)
GOLD = (246, 198, 50, 255)
#: The effects read at the sprite's small size only drawn bigger than the
#: art's own units: glyph units are this much larger than the drawing's.
FX_UNIT = 1.6


def _feather(fill: RGBA, tip: RGBA) -> FX.Paint:
    def paint(c: FxCanvas) -> None:
        pts = [(-14, 0), (-8, -5), (4, -5.5), (14, -2), (18, 0), (14, 2), (4, 5.5), (-8, 5)]
        c.polygon(pts, fill, INK, 1.2)
        c.polygon([(6, -4.5), (14, -2), (18, 0), (14, 2), (6, 4.5)], tip)
        c.line([(-16, 0), (14, 0)], INK, 0.9)

    return paint


def _paint_speed(c: FxCanvas) -> None:
    for y, x0, length in ((-24, 30, 60), (-6, 24, 84), (12, 34, 66), (28, 44, 46)):
        c.line([(x0, y), (x0 + length, y)], STREAK, 2.4)


def _paint_noise(c: FxCanvas) -> None:
    """Sound coming off the beak: three arcs and two glints."""
    for r in (14, 26, 38):
        c.arc((0, 0), r, r, -40, 40, (255, 246, 214, 220), 2.6)
    c.star((44, -24), 6.0, GOLD, points=4, inner=0.3, rotation=0)
    c.star((40, 26), 5.0, WHITE, points=4, inner=0.3, rotation=0)


def _paint_peck(c: FxCanvas) -> None:
    c.star((0, 0), 12.0, (255, 236, 120, 255), points=6, inner=0.35, rotation=0)
    c.star((0, 0), 6.0, WHITE, points=6, inner=0.45, rotation=30)
    for ang in (-50.0, 0.0, 50.0):
        r = math.radians(ang)
        c.line([(14 * math.cos(r), 14 * math.sin(r)), (24 * math.cos(r), 24 * math.sin(r))], WHITE, 2.0)


def _paint_rake(c: FxCanvas) -> None:
    """Three claw slashes."""
    for k in (-1, 0, 1):
        c.polygon([(-26, -14 + 10 * k), (24, 8 + 10 * k), (28, 12 + 10 * k), (-20, -8 + 10 * k)], SCRATCH)


class BirdFx:
    """One bird's effects and its sheet.

    ``feathers`` are the (fill, tip) colours of the feathers it sheds,
    ``beak_tip`` the tip of its beak in the head bone's frame (SVG units),
    ``flight_pitch`` the body angle of its level flight (its speed streaks
    trail back along that line). ``body_bone`` and ``foot_bone`` name the
    bones the effects sit on (an anatomy that is not a bird's names them
    differently).
    """

    def __init__(self, *, target: str, rig_path: Path, art_scale: float, frame_size: Tuple[int, int],
                 feathers: Sequence[Tuple[RGBA, RGBA]], beak_tip: Point, flight_pitch: float = 36.0,
                 body_bone: str = "body", foot_bone: str = "near_foot") -> None:
        self.target = target
        self.body_bone = body_bone
        self.foot_bone = foot_bone
        self.rig_path = rig_path
        self.art_scale = art_scale
        self.frame_size = frame_size
        self.beak_tip = beak_tip
        self.flight_pitch = flight_pitch
        glyphs: Dict[str, Tuple[FX.Extent, FX.Paint]] = {**FX.COMMON}
        self.feather_names: List[str] = []
        for k, (fill, tip) in enumerate(feathers):
            glyphs[f"feather_{k}"] = ((18.0, 8.0, 20.0, 8.0), _feather(fill, tip))
            self.feather_names.append(f"feather_{k}")
        glyphs["speed"] = ((4.0, 28.0, 112.0, 32.0), _paint_speed)
        glyphs["noise"] = ((6.0, 44.0, 52.0, 44.0), _paint_noise)
        glyphs["peck"] = ((26.0, 26.0, 26.0, 26.0), _paint_peck)
        glyphs["rake"] = ((30.0, 26.0, 32.0, 26.0), _paint_rake)
        self.glyphs = FX.Glyphs(art_scale * FX_UNIT, glyphs)

    def doc(self) -> RigDocument:
        return FX.rig_document(self.rig_path)

    def rows(self) -> List[Tuple[str, int, int]]:
        """The sheet's rows: the rig's clips, in its order."""
        return self.doc().rows()

    def _local(self, bone, x: float, y: float) -> Point:
        return bone.to_world((x * self.art_scale, y * self.art_scale))

    def _behind(self, canvas: FxCanvas, t: float, world, params) -> None:
        place, k = self.glyphs.place, self.art_scale
        speed = params.get("fx.speed", 0.0)
        if speed > 0.02:
            body = world[self.body_bone]
            place(canvas, "speed", body.origin, speed, degrees=body.angle - self.flight_pitch + 180.0)
        dust = params.get("fx.dust", 0.0)
        if dust > 0.02:
            ground = float(self.doc().frame["ground_y"])
            x = world[self.body_bone].origin[0]
            place(canvas, "dust", (x - 26.0 * k, ground), dust)
            place(canvas, "dust", (x + 36.0 * k, ground), dust * 0.8)

    def _front(self, canvas: FxCanvas, t: float, world, params) -> None:
        place, k = self.glyphs.place, self.art_scale
        head = world["head"]
        bx, by = self.beak_tip
        beak = self._local(head, bx, by)
        place(canvas, "peck", self._local(head, bx + 10.0, by), params.get("fx.peck", 0.0))
        # A blow landing on the bird's chest; its own talons striking.
        place(canvas, "hit", self._local(world[self.body_bone], 40.0, -20.0), params.get("fx.hit", 0.0))
        foot = world[self.foot_bone].origin
        place(canvas, "hit", (foot[0] + 10.0 * k, foot[1]), params.get("fx.strike", 0.0))
        place(canvas, "rake", (foot[0] + 8.0 * k, foot[1] + 10.0 * k), params.get("fx.rake", 0.0))
        feathers = params.get("fx.feathers", 0.0)
        if feathers > 0.02:
            # Loose feathers flung out from the body, drifting as they go.
            centre = self._local(world[self.body_bone], 10.0, 0.0)
            count = 6
            for j in range(count):
                a = math.tau * j / count + 0.6
                reach = (50.0 + 90.0 * ((t * 1.6 + 0.13 * j) % 1.0)) * k
                at = (centre[0] + math.cos(a) * reach, centre[1] + math.sin(a) * reach * 0.8)
                place(canvas, self.feather_names[j % len(self.feather_names)], at, feathers,
                      degrees=math.degrees(a) + 40.0 * math.sin(t * 9.0 + j))
        drift = params.get("fx.drift", 0.0)
        if drift > 0.02:
            # One last feather seesawing down onto the body.
            body = world[self.body_bone].origin
            y = body[1] - (110.0 - 70.0 * t) * k
            x = body[0] + 18.0 * math.sin(t * 9.0) * k
            place(canvas, self.feather_names[0], (x, y), drift, degrees=25.0 * math.sin(t * 9.0))
        noise = params.get("fx.notes", 0.0)
        if noise > 0.02 and params.get("jaw", 0.0) > 14.0:
            place(canvas, "noise", beak, noise, degrees=head.angle)

    def render_frame(self, animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        return compose_rig_frame(self.doc(), animation, frame_idx, frame_count, behind=self._behind, front=self._front,
                                 fx_pieces=True)

    def render(self, out_dir: Path, actor_metadata: dict) -> List[Path]:
        rows = self.rows()
        frame_transform: dict = {}
        outputs = build_sheet(
            frame_transform_out=frame_transform,
            target=self.target,
            rows=rows,
            render_fn=self.render_frame,
            out_dir=Path(out_dir),
            frame_size=self.frame_size,
            actor_metadata=actor_metadata,
        )
        keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
        parts = publish_rig_flipbook(self.target, rows, self.render_frame, outputs, frame_transform, Path(out_dir))
        return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())

    def render_canonical(self, out_dir: Path) -> Path:
        return write_canonical(self.target, self.rows(), self.render_frame, Path(out_dir))


__all__ = ["BirdFx"]
