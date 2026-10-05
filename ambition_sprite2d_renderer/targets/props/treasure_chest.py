"""SVG-rigged treasure chest: a banded pirate chest that bursts open on a heap of gold.

The chest seen from the front and a little above: oak planks, iron corner
brackets and straps, a gold trim along the rim, a domed lid with a hasp over
a keyhole lock. Inside, a heap of coins with gems, a pearl string and a
goblet.

The SVG ``data/props/treasure_chest/treasure_chest.svg`` owns the art and
marks every joint; the rig document ``rigged/treasure_chest/
treasure_chest.rig.json`` owns the skeleton and the clips, which
``scripts/build_treasure_chest_rig.py`` derives and authors. The lid is a
swap set hinged at the box's back edge (closed, ajar, up, open) that the
``opening`` clip runs through, bouncing the open lid on its hinge. This
module owns only the effects and publication.

Rows:

- ``closed``: shut, a glint running over the lock now and then (loops);
- ``opening``: it rattles, hops, the lock swings loose, light leaks from
  under the lid, the lid flies back in a burst of light and a fountain of
  coins spouts from the heap and rains back into it (once);
- ``open``: the treasure glowing and twinkling (loops).

The ``entities`` target's static ``chest_closed`` / ``chest_open`` textures
are rendered from the same rig (``render_state``), so the runtime's two
chest states and this sheet show one chest.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from ..characters import _creature_fx as FX
from ..characters._svg_fighter_effects import FxCanvas, compose_rig_frame

Point = Tuple[float, float]

TARGET_NAME = "treasure_chest"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "treasure_chest.rig.json"
FRAME_SIZE = (128, 128)
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``).
ART_SCALE = 0.25


def _px(x: float, y: float) -> Dict[str, float]:
    """A point of the drawing (SVG units) as a sprite-frame point."""
    return {"x": round(x * ART_SCALE, 1), "y": round(y * ART_SCALE, 1)}


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Treasure Chest"},
    "body": {
        "body_plan": "Prop",
        "body_kind": "Device",
        "locomotion_hint": "Stationary",
        "traits": ["prop", "chest", "reward", "interactable", "svg_rigged"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "closed", "events": []},
        "state.closed": {"animation": "closed", "events": []},
        "interact.open": {
            "animation": "opening",
            "events": [
                {"t": 0.31, "event": "unlock", "source": TARGET_NAME},
                {"t": 0.54, "event": "lid_open", "source": TARGET_NAME},
                {"t": 0.62, "event": "reward_spawn", "source": TARGET_NAME},
            ],
        },
        "state.open": {"animation": "open", "events": []},
    },
    # Points on the drawn frame (before the sheet's auto-crop).
    "sockets": {
        "lock": {"source": f"{TARGET_NAME}.geometry", "point": _px(256.0, 326.0)},
        "reward": {"source": f"{TARGET_NAME}.geometry", "point": _px(256.0, 250.0)},
        "base": {"source": f"{TARGET_NAME}.geometry", "point": _px(256.0, 440.0)},
    },
    "visual": {
        "default_pose": "closed",
        "canonical_source": "ambition_sprite2d_renderer/data/props/treasure_chest/treasure_chest.svg",
    },
    "tags": ["prop", "chest", "reward", "animated", "svg_rigged"],
}


def _doc() -> RigDocument:
    return FX.rig_document(RIG_PATH)


ROWS: List[Tuple[str, int, int]] = _doc().rows()

# --- Effect glyphs (`_creature_fx`), in the drawing's SVG units ------------------

LIGHT = (255, 226, 130)
HOT = (255, 248, 214)
WHITE = (255, 255, 250, 255)
GOLD = (233, 169, 58, 255)
GOLD_LIGHT = (255, 216, 106, 255)
GOLD_DARK = (168, 104, 26, 255)
INK = (31, 20, 16, 255)


def _a(rgb, alpha: int):
    return (rgb[0], rgb[1], rgb[2], alpha)


def _paint_glow(c: FxCanvas) -> None:
    """Warm light pooled over the opening (soft: stacked translucent ovals)."""
    for k, (rx, ry, alpha) in enumerate(((170, 74, 26), (140, 58, 30), (112, 44, 36), (82, 30, 44), (52, 18, 60))):
        c.ellipse((0, 0), rx, ry, _a(LIGHT if k < 3 else HOT, alpha))


def _paint_rays(c: FxCanvas) -> None:
    """Thin beams fanning up out of the chest, each a pale core in a warm sheath."""
    for k, ang in enumerate(range(-150, -20, 18)):
        length = 210.0 if k % 2 else 160.0
        for half, scale, color in ((2.6, 1.0, _a(LIGHT, 48)), (0.9, 0.85, _a(HOT, 96))):
            a0, a1 = math.radians(ang - half), math.radians(ang + half)
            L = length * scale
            c.polygon([(0, 0), (L * math.cos(a0), L * math.sin(a0)), (L * math.cos(a1), L * math.sin(a1))], color)


def _paint_leak(c: FxCanvas) -> None:
    """Light escaping the crack under a lifted lid: a hot slit, a halo, short
    beams fanning up and out."""
    c.ellipse((0, 0), 150, 22, _a(LIGHT, 60))
    c.ellipse((0, 0), 140, 8, _a(HOT, 200))
    for ang in (-170, -150, -125, -100, -80, -55, -30, -10):
        r = math.radians(ang)
        c.line([(110 * math.cos(r) * 0.9, 6 * math.sin(r)), (150 * math.cos(r), 70 * math.sin(r))], _a(HOT, 150), 3.0)


def _paint_burst(c: FxCanvas) -> None:
    c.star((0, 0), 120.0, _a(HOT, 170), points=12, inner=0.32, rotation=-90)
    c.star((0, 0), 64.0, WHITE, points=8, inner=0.4, rotation=-67.5)


def _coin(view: int):
    """A coin spinning: face on, tilted, edge on."""
    tilt = (1.0, 0.55, 0.16)[view]

    def paint(c: FxCanvas) -> None:
        c.ellipse((0, 0), 18 * tilt + 2.0, 18, GOLD, INK, 2.0)
        if view < 2:
            c.ellipse((-4 * tilt, -4), 9 * tilt, 9, GOLD_LIGHT)
            c.ellipse((0, 0), 12 * tilt, 12, None, GOLD_DARK, 1.6)

    return paint


def _paint_sparkle(c: FxCanvas) -> None:
    c.star((0, 0), 16.0, WHITE, points=4, inner=0.22, rotation=0)
    c.star((0, 0), 8.0, _a(LIGHT, 255), points=4, inner=0.3, rotation=45)


def _paint_click(c: FxCanvas) -> None:
    c.star((0, 0), 26.0, _a(HOT, 255), points=6, inner=0.3, rotation=0)
    for ang in (-60, -20, 20, 60, 120, 160, 200, 240):
        r = math.radians(ang)
        c.line([(28 * math.cos(r), 28 * math.sin(r)), (40 * math.cos(r), 40 * math.sin(r))], WHITE, 2.4)


_GLYPHS: Dict[str, Tuple[FX.Extent, FX.Paint]] = {**FX.COMMON}
_GLYPHS["glow"] = ((172.0, 76.0, 172.0, 76.0), _paint_glow)
_GLYPHS["rays"] = ((212.0, 212.0, 212.0, 6.0), _paint_rays)
_GLYPHS["leak"] = ((152.0, 72.0, 152.0, 24.0), _paint_leak)
_GLYPHS["burst"] = ((154.0, 154.0, 154.0, 154.0), _paint_burst)
_GLYPHS["sparkle"] = ((18.0, 18.0, 18.0, 18.0), _paint_sparkle)
_GLYPHS["click"] = ((42.0, 42.0, 42.0, 42.0), _paint_click)
for _view in range(3):
    _GLYPHS[f"coin{_view}"] = ((22.0, 21.0, 22.0, 21.0), _coin(_view))
GLYPHS = FX.Glyphs(ART_SCALE, _GLYPHS)
_place = GLYPHS.place
_local = GLYPHS.local

#: The opening's centre (where the light comes from), in the box's frame:
#: SVG units from the box's bottom centre.
MOUTH = (0.0, -158.0)
#: The coin fountain: (start x, start y, drift, height, delay) in SVG units,
#: in the box's frame. Each coin leaps from the heap and drops back into it.
COINS = (
    (-60.0, -180.0, -70.0, 190.0, 0.00),
    (30.0, -186.0, 60.0, 230.0, 0.05),
    (-10.0, -190.0, -20.0, 260.0, 0.12),
    (70.0, -178.0, 90.0, 170.0, 0.18),
    (-90.0, -172.0, -50.0, 150.0, 0.26),
    (50.0, -184.0, 20.0, 210.0, 0.32),
    (-30.0, -182.0, 40.0, 180.0, 0.40),
)
#: Where sparkles twinkle on the heap (box frame, SVG units), and their phases.
SPARKLES = ((-48.0, -196.0, 0.0), (62.0, -184.0, 0.35), (14.0, -208.0, 0.7), (-100.0, -168.0, 0.5),
            (96.0, -176.0, 0.15), (-12.0, -176.0, 0.85))


def _front(canvas: FxCanvas, t: float, world, params) -> None:
    base = world["base"]
    mouth = _local(base, *MOUTH)
    _place(canvas, "glow", mouth, params.get("fx.glow", 0.0))
    _place(canvas, "rays", _local(base, 0.0, -150.0), params.get("fx.rays", 0.0))
    _place(canvas, "leak", _local(base, 0.0, -146.0), params.get("fx.leak", 0.0))
    _place(canvas, "burst", mouth, params.get("fx.burst", 0.0) * 0.85)
    lock = world["lock"]
    _place(canvas, "click", _local(lock, 0.0, 18.0), params.get("fx.click", 0.0))
    _place(canvas, "sparkle", _local(lock, -14.0, 8.0), params.get("fx.glint", 0.0))
    dust = params.get("fx.dust", 0.0)
    _place(canvas, "dust", _local(base, -150.0, 2.0), dust)
    _place(canvas, "dust", _local(base, 150.0, 2.0), dust)
    clock = params.get("fx.coins", 0.0)
    if 0.0 < clock < 1.0:
        for k, (x0, y0, drift, height, delay) in enumerate(COINS):
            s = (clock - delay) / 0.6
            if not 0.0 < s < 1.0:
                continue
            x = x0 + drift * s
            y = y0 - height * 4.0 * s * (1.0 - s)
            spin = int(s * 9.0 + k) % 4
            _place(canvas, f"coin{(0, 1, 2, 1)[spin]}", _local(base, x, y), 1.0)
    sparkle = params.get("fx.sparkle", 0.0)
    if sparkle > 0.02:
        phase = params.get("fx.twinkle", t)
        for x, y, offset in SPARKLES:
            w = 0.5 + 0.5 * math.sin(math.tau * (phase * 2.0 + offset))
            _place(canvas, "sparkle", _local(base, x, y), sparkle * w * w)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return compose_rig_frame(_doc(), animation, frame_idx, frame_count, front=_front, fx_pieces=True)


def render_state(state: str) -> Image.Image:
    """The chest at rest in one of the runtime's two states (``closed`` /
    ``open``), on the full 128 px frame, without the light beams: the
    ``entities`` target crops it."""
    frames = dict((name, frames) for name, frames, _ms in ROWS)

    def front(canvas: FxCanvas, t: float, world, params) -> None:
        # No beams: they would widen the texture's crop and shrink the chest
        # in its entity box. The glow and the sparkles stay.
        _front(canvas, t, world, {**params, "fx.rays": 0.0})

    return compose_rig_frame(_doc(), state, 0, frames[state], front=front)


# ---- Target registration hooks ------------------------------------------------


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        actor_metadata=ACTOR_METADATA,
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, out_dir)
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[k]) for k in keys if outputs.get(k)] + list(parts.values())


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir))


__all__ = ["ACTOR_METADATA", "ROWS", "SHEET_FILES", "TARGET_NAME", "render", "render_canonical", "render_frame",
           "render_state"]
