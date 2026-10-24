"""Scenery props of the gate network's districts, drawn in room coordinates.

Each prop of a district room (`pirate_port_props`, `ninja_village_props`) is
drawn on a canvas whose window is its FRAME in the room's own coordinates
(world units, y down, the room's top left at 0, 0). So the art is drawn
where the room's walk lines are: a gallery, a roof or a yard is drawn at the
y of the one-way platform that the room places there
(`tools/ambition_ldtk_tools/specs/<district>/make_specs.py`). The room places
the prop over its frame's top left, at the body box of the published sheet
(`specs/<district>/props.py`). The numbers of both are the rooms'.

Each prop is its own target (its own sheet, one `idle` frame). No drop
shadows: form shade on a thing's own faces only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ._town_kit import Canvas, Kit


@dataclass(frozen=True)
class Piece:
    """One prop: its frame in its room (x0, y0, x1, y1) and how it is drawn."""

    frame: Tuple[float, float, float, float]
    draw: Callable[[Canvas, Kit], None]
    px: float = 2.0
    traits: Tuple[str, ...] = ("scenery",)


def draw(name: str, piece: Piece, pal: dict, sun: float = -1.0) -> Image.Image:
    x0, y0, x1, y1 = piece.frame
    c = Canvas(name, x1 - x0, y1 - y0, origin=(x0, y0), ppu=piece.px)
    k = Kit(c, pal, sun=sun)
    piece.draw(c, k)
    return c.image()


def frame_size(piece: Piece) -> Tuple[int, int]:
    x0, y0, x1, y1 = piece.frame
    return int(round((x1 - x0) * piece.px)), int(round((y1 - y0) * piece.px))


def _actor(name: str, piece: Piece) -> dict:
    traits = ["prop", "scenery", *piece.traits]
    return {
        "actor": {"character_id": f"prop_{name}", "display_name": name.replace("_", " ").title()},
        "body": {"body_plan": "Prop", "body_kind": "Scenery", "mass_class": "Heavy", "locomotion_hint": "Static", "traits": traits},
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {"default": {"animation": "idle", "events": []}},
        "tags": traits,
    }


def targets(pieces: Dict[str, Piece], pal: dict, sun: float = -1.0) -> Dict[str, dict]:
    """The registry entries of `pieces`."""

    def renderer(name: str, piece: Piece):
        def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
            del frame_idx, nframes
            if anim != "idle":
                raise ValueError(f"unknown animation: {anim}")
            return draw(name, piece, pal, sun)

        def frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
            del anim, frame_idx, nframes
            fw, fh = frame_size(piece)
            return {"anchors": {"foot": {"x": fw / 2, "y": float(fh)}}, "forward": {"x": 0.0, "y": -1.0}, "angle_deg": 0.0}

        def render(out_dir: str | Path, **opts) -> List[Path]:
            del opts
            out_dir = Path(out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            outputs = build_sheet(
                target=name,
                rows=[("idle", 1, 400)],
                render_fn=render_frame,
                out_dir=out_dir,
                frame_size=frame_size(piece),
                frame_meta_fn=frame_meta,
                auto_crop=False,
                actor_metadata=_actor(name, piece),
            )
            return [outputs[key] for key in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")]

        return render

    return {name: {"render": renderer(name, piece), "actor_metadata": _actor(name, piece)} for name, piece in pieces.items()}


def preview(pieces: Dict[str, Piece], pal: dict, out: Path, names=None, bg=(150, 170, 190), scale: float = 0.5) -> Path:
    """Every piece drawn where it stands, on one picture per room-sized sheet
    (a look-dev aid; not published)."""
    names = list(names or pieces)
    x0 = min(pieces[n].frame[0] for n in names)
    y0 = min(pieces[n].frame[1] for n in names)
    x1 = max(pieces[n].frame[2] for n in names)
    y1 = max(pieces[n].frame[3] for n in names)
    sheet = Image.new("RGBA", (int((x1 - x0) * scale), int((y1 - y0) * scale)), bg + (255,))
    for n in names:
        p = pieces[n]
        im = draw(n, p, pal)
        w, h = int((p.frame[2] - p.frame[0]) * scale), int((p.frame[3] - p.frame[1]) * scale)
        sheet.alpha_composite(im.resize((max(1, w), max(1, h)), Image.LANCZOS), (int((p.frame[0] - x0) * scale), int((p.frame[1] - y0) * scale)))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


__all__ = ["Piece", "draw", "frame_size", "preview", "targets"]
