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

Rows. The plain rows are an EMPTY chest, for the usual use (an item placed
in it at runtime, or nothing); the treasure rows fill it with the drawn heap:

- ``closed``: shut (one frame);
- ``opening``: it rattles, hops, the lock swings loose, the lid cracks and
  flies back, bouncing on its hinge; nothing inside, no light (once);
- ``open``: open and empty (one frame);
- ``opening_treasure``: the same opening on the treasure: light leaks
  from under the lid, the lid flies back in a burst of light and a fountain
  of coins spouts from the heap and rains back into it (once);
- ``open_treasure``: the treasure glowing and twinkling (loops). A player
  who takes the treasure flips the chest to ``open``.

An item shown in the chest at runtime anchors on the ``item`` socket (the
middle of the box's mouth) and layers between the box's dark interior and
its front (the treasure heap's slot: above z 10, below z 30), so the box's
front hides the item's lower part.

The ``entities`` target's static ``chest_closed`` / ``chest_open`` textures
are this sheet's ``closed`` and ``open`` frames (``render_state``), so the
runtime's two chest states and this sheet show one chest.
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
from . import _chest_fx as CHEST_FX
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
                {"t": 0.4, "event": "unlock", "source": TARGET_NAME},
                {"t": 0.78, "event": "lid_open", "source": TARGET_NAME},
                {"t": 0.78, "event": "reward_spawn", "source": TARGET_NAME},
            ],
        },
        "state.open": {"animation": "open", "events": []},
        "interact.open_treasure": {
            "animation": "opening_treasure",
            "events": [
                {"t": 0.31, "event": "unlock", "source": TARGET_NAME},
                {"t": 0.54, "event": "lid_open", "source": TARGET_NAME},
                {"t": 0.62, "event": "reward_spawn", "source": TARGET_NAME},
            ],
        },
        "state.open_treasure": {"animation": "open_treasure", "events": []},
    },
    # Points on the drawn frame (before the sheet's auto-crop).
    "sockets": {
        "lock": {"source": f"{TARGET_NAME}.geometry", "point": _px(256.0, 326.0)},
        "reward": {"source": f"{TARGET_NAME}.geometry", "point": _px(256.0, 250.0)},
        "item": {"source": f"{TARGET_NAME}.geometry", "point": _px(256.0, 282.0)},
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

# --- Effect glyphs (`_creature_fx`, `_chest_fx`), in the drawing's SVG units -------

GOLD = (233, 169, 58, 255)
GOLD_LIGHT = (255, 216, 106, 255)
GOLD_DARK = (168, 104, 26, 255)
INK = (31, 20, 16, 255)


def _coin(view: int):
    """A coin spinning: face on, tilted, edge on."""
    tilt = (1.0, 0.55, 0.16)[view]

    def paint(c: FxCanvas) -> None:
        c.ellipse((0, 0), 18 * tilt + 2.0, 18, GOLD, INK, 2.0)
        if view < 2:
            c.ellipse((-4 * tilt, -4), 9 * tilt, 9, GOLD_LIGHT)
            c.ellipse((0, 0), 12 * tilt, 12, None, GOLD_DARK, 1.6)

    return paint


_GLYPHS: Dict[str, Tuple[FX.Extent, FX.Paint]] = {**FX.COMMON, **CHEST_FX.GLYPHS}
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
    """The chest in one of the runtime's two states (``closed`` / ``open``,
    both one still frame, the open chest empty), on the full 128 px frame:
    the ``entities`` target crops it."""
    return render_frame(state, 0, 1)


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
