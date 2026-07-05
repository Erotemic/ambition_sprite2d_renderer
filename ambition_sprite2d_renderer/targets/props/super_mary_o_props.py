"""World-object sheets for the Super Mary-O push.

These targets intentionally stay lightweight and data-driven so the repo can
swap in SMB1-like pickups / scenery without touching runtime code first.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ..super_mary_o_common import (
    BRICK,
    GAS_RED,
    GAS_RED_DARK,
    MILK_BLUE,
    MILK_WHITE,
    OUTLINE,
    PIPE_GREEN,
    PIPE_GREEN_DARK,
    PIPE_GREEN_LIGHT,
    STEEL,
    STEEL_DARK,
    WHITE,
    COIN_GOLD,
    COIN_GOLD_LIGHT,
    bottom_center_canvas,
    rasterize_logical,
    sprite_shadow,
)

FRAME = (96, 96)
LOGICAL = (28, 28)
SCALE = 3
LABEL_WIDTH = 120


@dataclass(frozen=True)
class PropSpec:
    target_name: str
    display_name: str
    rows: List[Tuple[str, int, int]]
    renderer: Callable[[str, int, int], Image.Image]
    traits: Tuple[str, ...]



def _outlined_rect(px, x1, y1, x2, y2, *, fill, inset: float = 0.4) -> None:
    px.rect(x1, y1, x2, y2, fill=OUTLINE)
    ix1, iy1 = x1 + inset, y1 + inset
    ix2, iy2 = x2 - inset, y2 - inset
    if ix2 <= ix1 or iy2 <= iy1:
        px.rect(x1, y1, x2, y2, fill=fill)
        return
    px.rect(ix1, iy1, ix2, iy2, fill=fill)



def _pipe_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    bob = [0.0, -0.2, 0.0, 0.2][frame_idx % 4] if nframes > 1 else 0.0

    def painter(px) -> None:
        _outlined_rect(px, 7, 20 + bob, 21, 27 + bob, fill=PIPE_GREEN)
        _outlined_rect(px, 5, 11 + bob, 23, 17 + bob, fill=PIPE_GREEN)
        px.rect(5.8, 12.0 + bob, 9.0, 16.2 + bob, fill=PIPE_GREEN_LIGHT)
        px.rect(10.0, 12.0 + bob, 13.8, 16.2 + bob, fill=PIPE_GREEN)
        px.rect(14.5, 12.0 + bob, 22.0, 16.2 + bob, fill=PIPE_GREEN_DARK)
        px.rect(19.2, 11.6 + bob, 22.0, 27.0 + bob, fill=PIPE_GREEN_DARK)
        px.rect(6.0, 18.0 + bob, 20.0, 19.0 + bob, fill=PIPE_GREEN_LIGHT)
        px.rect(8.2, 13.8 + bob, 20.0, 15.0 + bob, fill=(0, 0, 0, 110))

    sprite = rasterize_logical(LOGICAL, SCALE, painter)
    frame = bottom_center_canvas(sprite, FRAME)
    shadow = sprite_shadow(FRAME, width=42, height=8, y=88)
    shadow.alpha_composite(frame)
    return shadow



def _milk_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    bob = [0.0, -0.5, -1.0, -0.4][frame_idx % 4]
    tilt = [-0.3, 0.0, 0.3, 0.0][frame_idx % 4]

    def painter(px) -> None:
        left = 9.0 + tilt
        right = 19.0 + tilt
        _outlined_rect(px, left, 9.0 + bob, right, 23.0 + bob, fill=MILK_WHITE)
        px.polygon(
            [(left, 9.0 + bob), (left + 2.4, 6.0 + bob), (right - 2.4, 6.0 + bob), (right, 9.0 + bob)],
            fill=MILK_WHITE,
            outline=OUTLINE,
        )
        px.rect(left + 1.0, 12.0 + bob, right - 1.0, 17.0 + bob, fill=MILK_BLUE)
        px.line([(left + 2.6, 10.6 + bob), (left + 2.6, 21.0 + bob)], fill=(216, 230, 255, 255), width=0.6)
        _outlined_rect(px, left + 2.1, 13.0 + bob, left + 3.4, 16.5 + bob, fill=WHITE, inset=0.15)
        _outlined_rect(px, left + 5.0, 13.2 + bob, left + 8.2, 14.4 + bob, fill=WHITE, inset=0.15)
        _outlined_rect(px, left + 5.0, 15.1 + bob, left + 8.6, 16.3 + bob, fill=WHITE, inset=0.15)
        px.rect(left + 2.0, 18.1 + bob, right - 2.0, 20.0 + bob, fill=(209, 230, 255, 255))

    sprite = rasterize_logical(LOGICAL, SCALE, painter)
    frame = bottom_center_canvas(sprite, FRAME)
    shadow = sprite_shadow(FRAME, width=28, height=7, y=88)
    shadow.alpha_composite(frame)
    return shadow



def _gas_tank_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    bob = [0.0, -0.5, -0.8, -0.2][frame_idx % 4]
    glow = [0.0, 0.6, 1.0, 0.4][frame_idx % 4]

    def painter(px) -> None:
        _outlined_rect(px, 8.0, 10.5 + bob, 19.8, 23.0 + bob, fill=GAS_RED)
        _outlined_rect(px, 10.4, 8.8 + bob, 17.2, 12.0 + bob, fill=GAS_RED)
        _outlined_rect(px, 16.6, 8.0 + bob, 18.6, 10.8 + bob, fill=STEEL)
        _outlined_rect(px, 18.4, 8.5 + bob, 21.5, 10.0 + bob, fill=STEEL)
        px.rect(18.2, 10.2 + bob, 19.8, 12.6 + bob, fill=STEEL_DARK)
        px.rect(9.4, 13.0 + bob, 12.4, 21.0 + bob, fill=(255, 189, 171, 255))
        px.rect(13.2, 13.0 + bob, 18.4, 14.4 + bob, fill=GAS_RED_DARK)
        px.rect(13.2, 16.2 + bob, 18.4, 17.6 + bob, fill=GAS_RED_DARK)
        px.rect(13.2, 19.4 + bob, 18.4, 20.8 + bob, fill=GAS_RED_DARK)
        if glow > 0.0:
            px.ellipse(11.2, 12.2 + bob, 19.0, 20.0 + bob, fill=(255, 236, 192, int(70 * glow)), outline=None)

    sprite = rasterize_logical(LOGICAL, SCALE, painter)
    frame = bottom_center_canvas(sprite, FRAME)
    shadow = sprite_shadow(FRAME, width=30, height=7, y=88)
    shadow.alpha_composite(frame)
    return shadow



def _coin_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    phase = frame_idx % max(1, nframes)
    widths = [7.6, 4.2, 2.4, 4.2, 7.6, 4.8]
    inner = [5.2, 2.2, 0.8, 2.2, 5.2, 2.8]
    w = widths[phase % len(widths)]
    iw = inner[phase % len(inner)]
    left = 14.0 - w / 2.0
    right = 14.0 + w / 2.0

    def painter(px) -> None:
        px.ellipse(left, 8.5, right, 20.5, fill=COIN_GOLD, outline=OUTLINE, width=0.8)
        if iw > 1.0:
            ileft = 14.0 - iw / 2.0
            iright = 14.0 + iw / 2.0
            px.ellipse(ileft, 10.2, iright, 18.8, fill=COIN_GOLD_LIGHT, outline=None)
        px.rect(13.4, 10.8, 14.8, 18.4, fill=OUTLINE)
        px.rect(12.2, 12.0, 15.6, 13.2, fill=OUTLINE)

    sprite = rasterize_logical(LOGICAL, SCALE, painter)
    frame = bottom_center_canvas(sprite, FRAME, offset_y=-4)
    shadow = sprite_shadow(FRAME, width=24, height=6, y=88)
    shadow.alpha_composite(frame)
    return shadow


SPECS: Dict[str, PropSpec] = {
    "super_mary_o_pipe": PropSpec(
        target_name="super_mary_o_pipe",
        display_name="Mary Pipe",
        rows=[("idle", 1, 150)],
        renderer=_pipe_frame,
        traits=("scenery", "pipe", "retro"),
    ),
    "super_mary_o_milk_carton": PropSpec(
        target_name="super_mary_o_milk_carton",
        display_name="Milk Carton Power-Up",
        rows=[("idle", 4, 125)],
        renderer=_milk_frame,
        traits=("pickup", "milk", "powerup", "retro"),
    ),
    "super_mary_o_gasoline_tank": PropSpec(
        target_name="super_mary_o_gasoline_tank",
        display_name="Gasoline Tank Power-Up",
        rows=[("idle", 4, 125)],
        renderer=_gas_tank_frame,
        traits=("pickup", "gasoline", "powerup", "retro"),
    ),
    "super_mary_o_coin": PropSpec(
        target_name="super_mary_o_coin",
        display_name="Mary Coin",
        rows=[("idle", 1, 120), ("spin", 6, 85)],
        renderer=_coin_frame,
        traits=("pickup", "coin", "currency", "retro"),
    ),
}



def _actor_metadata(spec: PropSpec) -> dict:
    return {
        "actor": {"character_id": f"prop_{spec.target_name}", "display_name": spec.display_name},
        "body": {
            "body_plan": "StaticProp",
            "body_kind": "Pickup",
            "mass_class": "Light",
            "locomotion_hint": "None",
            "traits": list(spec.traits),
        },
        "tags": list(spec.traits),
    }



def _render_spec(spec: PropSpec, out_dir: str | Path) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    outputs = build_sheet(
        target=spec.target_name,
        rows=spec.rows,
        render_fn=spec.renderer,
        out_dir=out_dir,
        frame_size=FRAME,
        label_width=LABEL_WIDTH,
        auto_crop=False,
        actor_metadata=_actor_metadata(spec),
        trim=False,
    )
    return [
        outputs[k]
        for k in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")
    ]



def render(out_dir: str | Path, **opts) -> List[Path]:
    rendered: List[Path] = []
    for spec in SPECS.values():
        rendered.extend(_render_spec(spec, out_dir))
    return rendered


TARGETS = {
    name: {"render": (lambda out_dir, _spec=spec, **opts: _render_spec(_spec, out_dir)), "actor_metadata": _actor_metadata(spec)}
    for name, spec in SPECS.items()
}
