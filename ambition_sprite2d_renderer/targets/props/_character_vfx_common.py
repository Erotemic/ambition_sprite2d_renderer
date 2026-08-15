"""Shared authoring helpers for detached character-specific VFX catalogs.

This module is intentionally private to target discovery.  It contains drawing
primitives and publication/metadata plumbing only; each public character VFX
module remains the authored source of its own visual vocabulary.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from PIL import Image, ImageDraw

from ...authoring.sheet_build import build_sheet, write_canonical
from ...yaml_io import safe_dump

RGBA = tuple[int, int, int, int]
Point = tuple[float, float]
FrameDrawer = Callable[["Canvas", float], None]


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def smooth(value: float) -> float:
    t = clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def pulse(value: float) -> float:
    return 0.5 + 0.5 * math.sin(math.tau * value)


def window(value: float, attack: float = 0.42) -> float:
    t = clamp01(value)
    if t <= attack:
        return smooth(t / max(attack, 1e-6))
    return smooth((1.0 - t) / max(1.0 - attack, 1e-6))


def fade(color: RGBA, alpha: float) -> RGBA:
    return (color[0], color[1], color[2], max(0, min(255, round(color[3] * clamp01(alpha)))))


def mix(a: RGBA, b: RGBA, amount: float) -> RGBA:
    t = clamp01(amount)
    return tuple(round(a[i] * (1.0 - t) + b[i] * t) for i in range(4))  # type: ignore[return-value]


_PIXEL_FONT_3X5: dict[str, tuple[str, ...]] = {
    "A": ("010", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("011", "100", "100", "100", "011"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "J": ("001", "001", "001", "101", "010"),
    "K": ("101", "101", "110", "101", "101"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("010", "101", "101", "101", "010"),
    "P": ("110", "101", "110", "100", "100"),
    "Q": ("010", "101", "101", "011", "001"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"),
    "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"),
    "Z": ("111", "001", "010", "100", "111"),
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("110", "001", "010", "100", "111"),
    "3": ("110", "001", "010", "001", "110"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "110", "001", "110"),
    "6": ("011", "100", "110", "101", "010"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("010", "101", "010", "101", "010"),
    "9": ("010", "101", "011", "001", "110"),
    "?": ("110", "001", "010", "000", "010"),
    "+": ("000", "010", "111", "010", "000"),
    "-": ("000", "000", "111", "000", "000"),
    "=": ("000", "111", "000", "111", "000"),
}


class Canvas:
    """Logical-coordinate drawing wrapper over a supersampled RGBA image."""

    def __init__(self, frame_size: tuple[int, int], supersample: int = 4):
        self.frame_size = frame_size
        self.super = supersample
        self.image = Image.new(
            "RGBA",
            (frame_size[0] * supersample, frame_size[1] * supersample),
            (0, 0, 0, 0),
        )
        self.draw = ImageDraw.Draw(self.image)

    def _s(self, value: float) -> int:
        return round(value * self.super)

    def _point(self, point: Point) -> tuple[int, int]:
        return (self._s(point[0]), self._s(point[1]))

    def line(self, points: Sequence[Point], color: RGBA, width: float = 1.0) -> None:
        self.draw.line([self._point(p) for p in points], fill=color, width=max(1, self._s(width)), joint="curve")

    def polygon(
        self,
        points: Sequence[Point],
        fill: RGBA | None = None,
        outline: RGBA | None = None,
        width: float = 1.0,
    ) -> None:
        scaled = [self._point(p) for p in points]
        self.draw.polygon(scaled, fill=fill)
        if outline is not None:
            self.draw.line(scaled + [scaled[0]], fill=outline, width=max(1, self._s(width)), joint="curve")

    def rect(
        self,
        box: tuple[float, float, float, float],
        fill: RGBA | None = None,
        outline: RGBA | None = None,
        width: float = 1.0,
    ) -> None:
        x0, y0, x1, y1 = box
        self.draw.rectangle(
            (self._s(x0), self._s(y0), self._s(x1), self._s(y1)),
            fill=fill,
            outline=outline,
            width=max(1, self._s(width)),
        )

    def ellipse(
        self,
        center: Point,
        rx: float,
        ry: float | None = None,
        fill: RGBA | None = None,
        outline: RGBA | None = None,
        width: float = 1.0,
    ) -> None:
        if ry is None:
            ry = rx
        x, y = center
        self.draw.ellipse(
            (self._s(x - rx), self._s(y - ry), self._s(x + rx), self._s(y + ry)),
            fill=fill,
            outline=outline,
            width=max(1, self._s(width)),
        )

    def arc(
        self,
        center: Point,
        rx: float,
        ry: float,
        start_deg: float,
        end_deg: float,
        color: RGBA,
        width: float = 1.0,
    ) -> None:
        x, y = center
        self.draw.arc(
            (self._s(x - rx), self._s(y - ry), self._s(x + rx), self._s(y + ry)),
            start=start_deg,
            end=end_deg,
            fill=color,
            width=max(1, self._s(width)),
        )

    def star(
        self,
        center: Point,
        outer: float,
        color: RGBA,
        *,
        points: int = 4,
        inner: float = 0.35,
        rotation: float = -math.pi / 2,
        outline: RGBA | None = None,
        width: float = 0.8,
    ) -> None:
        pts: list[Point] = []
        for i in range(points * 2):
            angle = rotation + i * math.pi / points
            radius = outer if i % 2 == 0 else outer * inner
            pts.append((center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius))
        self.polygon(pts, color, outline, width)

    def diamond(
        self,
        center: Point,
        rx: float,
        ry: float,
        fill: RGBA | None,
        outline: RGBA | None,
        width: float = 1.0,
    ) -> None:
        x, y = center
        self.polygon([(x, y - ry), (x + rx, y), (x, y + ry), (x - rx, y)], fill, outline, width)

    def arrow(self, start: Point, end: Point, color: RGBA, width: float = 1.4, head: float = 5.0) -> None:
        self.line([start, end], color, width)
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = max(1e-6, math.hypot(dx, dy))
        ux, uy = dx / length, dy / length
        nx, ny = -uy, ux
        base = (end[0] - ux * head, end[1] - uy * head)
        self.polygon(
            [end, (base[0] + nx * head * 0.55, base[1] + ny * head * 0.55), (base[0] - nx * head * 0.55, base[1] - ny * head * 0.55)],
            color,
        )

    def pixel_text(
        self,
        center: Point,
        text: str,
        color: RGBA,
        *,
        scale: float = 2.0,
        shadow: RGBA | None = None,
    ) -> None:
        text = text.upper()
        advance = 4.0 * scale
        line_width = max(0.0, len(text) * advance - scale)
        left = center[0] - line_width * 0.5
        top = center[1] - 2.5 * scale

        def draw_at(dx: float, dy: float, fill: RGBA) -> None:
            cursor = left
            for char in text:
                if char == " ":
                    cursor += advance
                    continue
                rows = _PIXEL_FONT_3X5.get(char, _PIXEL_FONT_3X5["?"])
                for iy, row in enumerate(rows):
                    for ix, bit in enumerate(row):
                        if bit != "1":
                            continue
                        x0 = cursor + ix * scale + dx
                        y0 = top + iy * scale + dy
                        self.rect((x0, y0, x0 + scale * 0.86, y0 + scale * 0.86), fill=fill)
                cursor += advance

        if shadow is not None:
            draw_at(scale * 0.55, scale * 0.55, shadow)
        draw_at(0.0, 0.0, color)

    def finish(self) -> Image.Image:
        return self.image.resize(self.frame_size, Image.Resampling.NEAREST)


def make_spec(
    family: str,
    intent: str,
    *,
    loop: bool = False,
    placement: str = "world",
    orientation: str = "radial",
    mirror_x: bool = False,
    rotate_safe: bool = True,
    blend: str = "alpha",
    layer: str = "over_world",
    attachment: str = "world_locked_after_spawn",
    tint: str = "preserve_character_palette",
    size: int = 104,
    relationship: str = "active",
    extra_anchor: str | None = None,
) -> dict:
    return {
        "family": family,
        "intent": intent,
        "loop": loop,
        "placement": placement,
        "orientation": orientation,
        "mirror_x": mirror_x,
        "rotate_safe": rotate_safe,
        "blend_mode_hint": blend,
        "draw_layer_hint": layer,
        "attachment_hint": attachment,
        "tintability": tint,
        "nominal_visual_span_px": size,
        "effect_relationship": relationship,
        "extra_anchor": extra_anchor,
    }


def actor_metadata(target_name: str, display_name: str, character_context_id: str) -> dict:
    return {
        "actor": {
            "character_id": f"fx_{target_name}",
            "display_name": display_name,
        },
        "body": {
            "body_plan": "Effect",
            "body_kind": "Overlay",
            "mass_class": "Light",
            "locomotion_hint": "Stationary",
            "traits": ["fx", "overlay", "presentation", "character_specific"],
        },
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "sockets": {
            "origin": {
                "source": f"{target_name}.geometry",
                "point": {"x": 72.0, "y": 72.0},
            },
        },
        "tags": ["fx", "overlay", "presentation", "character_specific", character_context_id],
    }


def _progress(loop: bool, frame_idx: int, nframes: int) -> float:
    if loop:
        return frame_idx / max(1, nframes)
    return frame_idx / max(1, nframes - 1)


def _phase(loop: bool, frame_idx: int, nframes: int, p: float) -> str:
    if loop:
        return "loop"
    if frame_idx == nframes - 1:
        return "clear"
    if p < 0.24:
        return "onset"
    if p < 0.68:
        return "active"
    return "resolve"


def _intensity(loop: bool, p: float) -> float:
    if loop:
        return round(0.72 + 0.18 * pulse(p), 4)
    return round(window(p, 0.34), 4)


def publish_catalog(
    *,
    target_name: str,
    display_name: str,
    character_context_id: str,
    character_context_display: str,
    rows: Sequence[tuple[str, int, int]],
    drawers: Mapping[str, FrameDrawer],
    specs: Mapping[str, dict],
    origins: Mapping[str, Point],
    out_dir: str | Path,
    frame_size: tuple[int, int] = (144, 144),
    supersample: int = 4,
    crop_margin: int = 5,
) -> list[Path]:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    row_map = {name: (frames, duration_ms) for name, frames, duration_ms in rows}
    missing = sorted(set(row_map) - set(drawers))
    if missing:
        raise ValueError(f"missing drawer(s) for {target_name}: {', '.join(missing)}")
    missing_specs = sorted(set(row_map) - set(specs))
    if missing_specs:
        raise ValueError(f"missing authoring spec(s) for {target_name}: {', '.join(missing_specs)}")

    def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        spec = specs[anim]
        loop = bool(spec["loop"])
        if not loop and frame_idx == nframes - 1:
            return Image.new("RGBA", frame_size, (0, 0, 0, 0))
        p = _progress(loop, frame_idx, nframes)
        canvas = Canvas(frame_size, supersample)
        drawers[anim](canvas, p)
        return canvas.finish()

    def frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
        spec = specs[anim]
        loop = bool(spec["loop"])
        p = _progress(loop, frame_idx, nframes)
        ox, oy = origins.get(anim, (frame_size[0] * 0.5, frame_size[1] * 0.5))
        anchors = {"origin": {"x": ox, "y": oy}}
        extra_anchor = spec.get("extra_anchor")
        if extra_anchor:
            anchors[str(extra_anchor)] = {"x": ox, "y": oy}
        return {
            "anchors": anchors,
            "effect": {
                "family": spec["family"],
                "character_context_id": character_context_id,
                "phase": _phase(loop, frame_idx, nframes, p),
                "progress": round(p, 4),
                "intensity_hint": _intensity(loop, p),
                "clear_frame": bool(not loop and frame_idx == nframes - 1),
            },
        }

    outputs = build_sheet(
        target=target_name,
        rows=rows,
        render_fn=render_frame,
        out_dir=out_path,
        frame_size=frame_size,
        frame_meta_fn=frame_meta,
        auto_crop=True,
        crop_margin=crop_margin,
        actor_metadata=actor_metadata(target_name, display_name, character_context_id),
    )

    animations: dict[str, dict] = {}
    for name, (nframes, duration_ms) in row_map.items():
        spec = dict(specs[name])
        spec.pop("extra_anchor", None)
        loop = bool(spec["loop"])
        ox, oy = origins.get(name, (frame_size[0] * 0.5, frame_size[1] * 0.5))
        animations[name] = {
            **spec,
            "frame_count": nframes,
            "frame_duration_ms": duration_ms,
            "total_duration_ms": nframes * duration_ms,
            "origin_anchor": "origin",
            "additional_anchor": specs[name].get("extra_anchor"),
            "completion_hint": "loop_until_cancelled" if loop else "despawn_after_clear_frame",
            "authored_origin": {"x": ox, "y": oy},
            "frames": [
                {
                    "frame": i,
                    "phase": _phase(loop, i, nframes, _progress(loop, i, nframes)),
                    "progress": round(_progress(loop, i, nframes), 4),
                    "intensity_hint": _intensity(loop, _progress(loop, i, nframes)),
                    "clear_frame": bool(not loop and i == nframes - 1),
                }
                for i in range(nframes)
            ],
        }

    authoring_doc = {
        "schema": "ambition.sprite_character_vfx_authoring",
        "schema_version": 1,
        "target": target_name,
        "status": "authoring_hints_not_yet_runtime_contract",
        "scope": "detached_character_vfx",
        "character_context": {
            "character_id": character_context_id,
            "display_name": character_context_display,
        },
        "coordinate_space": "logical frame pixels; runtime manifest anchors are translated through auto-crop/trim",
        "author_owned_fields": [
            "animation timing",
            "origin/contact/emitter/target anchors",
            "loop and completion intent",
            "effect relationship to startup/active/impact/sustain/release/aftermath",
            "world/source/target/surface attachment intent",
            "orientation, rotation safety, and mirror allowance",
            "draw-layer and compositing intent",
            "tintability and nominal visual span",
            "frame-level phase and relative intensity",
        ],
        "runtime_promotion_notes": [
            "These sprites are detached presentation marks. Body-wrapping or limb-dependent effects remain authored with the character renderer.",
            "Treat row timing and frame anchors as authoritative immediately; never infer authored pivots from alpha bounds.",
            "The current sheet RON preserves frame anchors but not arbitrary effect notes. Keep this sidecar as authorial intent until repeated use justifies generic runtime fields.",
            "Promote placement, orientation, attachment, layer, blend, loop, and completion as generic presentation vocabulary; do not switch on these animation names in engine code.",
            "Directional effects author +X as forward unless their orientation field says otherwise. Rotate/mirror around the authored origin.",
            "Surface/contact effects publish a semantic anchor. Surface normals and gravity-relative orientation belong to presentation transforms, not duplicated sprite rows.",
            "Character palette is semantic content, not a requirement that the effect be attached to that character body entity.",
        ],
        "animations": animations,
    }
    authoring_path = out_path / f"{target_name}_authoring.yaml"
    authoring_path.write_text(safe_dump(authoring_doc, sort_keys=False, width=120), encoding="utf8")

    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        authoring_path,
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ]


def publish_canonical(
    *,
    target_name: str,
    rows: Sequence[tuple[str, int, int]],
    drawers: Mapping[str, FrameDrawer],
    specs: Mapping[str, dict],
    out_dir: str | Path,
    frame_size: tuple[int, int] = (144, 144),
    supersample: int = 4,
    crop_margin: int = 5,
) -> Path:
    def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        loop = bool(specs[anim]["loop"])
        if not loop and frame_idx == nframes - 1:
            return Image.new("RGBA", frame_size, (0, 0, 0, 0))
        p = _progress(loop, frame_idx, nframes)
        canvas = Canvas(frame_size, supersample)
        drawers[anim](canvas, p)
        return canvas.finish()

    return write_canonical(
        target_name,
        rows,
        render_frame,
        Path(out_dir),
        frame_size=frame_size,
        crop_margin=crop_margin,
    )


def sheet_files(target_name: str) -> tuple[str, ...]:
    return (
        f"{target_name}_spritesheet.png",
        f"{target_name}_spritesheet.yaml",
        f"{target_name}_spritesheet.ron",
        f"{target_name}_actor.ron",
        f"{target_name}_authoring.yaml",
    )
