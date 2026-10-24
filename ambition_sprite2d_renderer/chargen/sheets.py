"""Review images and the sprite sheet of generated characters.

* :func:`contact_sheet`: many characters, each in its five views.
* :func:`turnaround`: characters turning full circle: front, front 3/4, side,
  back 3/4, back, then the three left views (mirrors of their right twins).
* :func:`posed_sheet`: a rigged character's posed rows, per view.
* :func:`publish_sheet`: the gameplay sprite sheet, actor sidecar and
  previews, through ``build_sheet`` like any hand-made SVG rig.

Review images are drawn at a review scale on a flat grey; they carry no drop
shadow.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image

from ..authoring.svg_parts import _svg_to_png_bytes
from ..core.draw import blending_draw, font
from .geometry import VIEW_BY_KEY, VIEWS, View
from .rig import UNIT, slug, view_svg, write_character
from .spec import CharacterSpec

BG = (214, 219, 226, 255)
TEXT = (40, 36, 44, 255)


def render_view(spec: CharacterSpec, view: View, px_per_cm: float = 1.6, *, mirror: bool = False) -> Image.Image:
    """One view of ``spec``, its whole cell, ``px_per_cm`` pixels a centimetre."""
    dpi = 25.4 * px_per_cm / UNIT
    img = Image.open(io.BytesIO(_svg_to_png_bytes(view_svg(spec, view), dpi))).convert("RGBA")
    return img.transpose(Image.FLIP_LEFT_RIGHT) if mirror else img


def _union_bbox(images: Iterable[Image.Image]) -> Optional[Tuple[int, int, int, int]]:
    box = None
    for im in images:
        b = im.getchannel("A").getbbox()
        if b is None:
            continue
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    return box


def _on_bg(im: Image.Image) -> Image.Image:
    out = Image.new("RGBA", im.size, BG)
    out.alpha_composite(im)
    return out


def _label(img: Image.Image, xy: Tuple[int, int], text: str, size: int = 14) -> None:
    blending_draw(img).text(xy, text, fill=TEXT, font=font(size))


def contact_sheet(specs: Sequence[CharacterSpec], out: Path, *, px_per_cm: float = 1.3, per_row: int = 4,
                  views: Sequence[View] = VIEWS) -> Path:
    """Every character in every view, in blocks of five, ``per_row`` blocks a row."""
    blocks: List[Image.Image] = []
    for spec in specs:
        ims = [render_view(spec, v, px_per_cm) for v in views]
        box = _union_bbox(ims)
        # One crop height for the five views keeps their ground line shared.
        cell_w = max(im.getchannel("A").getbbox()[2] - im.getchannel("A").getbbox()[0] for im in ims) + 10
        top = max(0, box[1] - 6)
        bottom = box[3] + 4
        pad = 22
        block = Image.new("RGBA", (cell_w * len(ims) + 8, bottom - top + pad), BG)
        for i, im in enumerate(ims):
            b = im.getchannel("A").getbbox()
            cx = (b[0] + b[2]) // 2
            crop = im.crop((cx - cell_w // 2, top, cx - cell_w // 2 + cell_w, bottom))
            block.alpha_composite(crop, (4 + i * cell_w, pad))
        _label(block, (6, 3), f"{spec.name}: {spec.base.replace('_', ' ')}, {spec.body.height_cm:.0f} cm", 13)
        blocks.append(block)
    bw = max(b.width for b in blocks)
    rows = [blocks[i:i + per_row] for i in range(0, len(blocks), per_row)]
    heights = [max(b.height for b in r) for r in rows]
    header = 30
    sheet = Image.new("RGBA", (bw * per_row + 12, sum(heights) + header + 6 * len(rows)), BG)
    _label(sheet, (8, 6), "Generated cast: front, front 3/4, side, back 3/4, back (one spec each; left views mirror the right)", 16)
    y = header
    for r, h in zip(rows, heights):
        for i, b in enumerate(r):
            sheet.alpha_composite(b, (6 + i * bw, y + h - b.height))
        y += h + 6
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out)
    return out


#: The turnaround: the five drawn views, then the left views as mirrors.
TURN = (("front", False, "front"), ("front_3q", False, "front 3/4"), ("side", False, "side"), ("back_3q", False, "back 3/4"),
        ("back", False, "back"), ("back_3q", True, "back 3/4 (left)"), ("side", True, "side (left)"), ("front_3q", True, "front 3/4 (left)"))


def turnaround(specs: Sequence[CharacterSpec], out: Path, *, px_per_cm: float = 2.6) -> Path:
    strips: List[Image.Image] = []
    for spec in specs:
        ims = [render_view(spec, VIEW_BY_KEY[k], px_per_cm, mirror=m) for k, m, _ in TURN]
        box = _union_bbox(ims)
        cell_w = max(im.getchannel("A").getbbox()[2] - im.getchannel("A").getbbox()[0] for im in ims) + 24
        top, bottom = max(0, box[1] - 10), box[3] + 8
        strip = Image.new("RGBA", (cell_w * len(ims), bottom - top + 50), BG)
        for i, (im, (_k, _m, name)) in enumerate(zip(ims, TURN)):
            b = im.getchannel("A").getbbox()
            cx = (b[0] + b[2]) // 2
            strip.alpha_composite(im.crop((cx - cell_w // 2, top, cx - cell_w // 2 + cell_w, bottom)), (i * cell_w, 28))
            _label(strip, (i * cell_w + 8, bottom - top + 30), name, 14)
        _label(strip, (8, 4), f"{spec.name} ({spec.base.replace('_', ' ')}, seed {spec.seed})", 16)
        strips.append(strip)
    w = max(s.width for s in strips)
    sheet = Image.new("RGBA", (w, sum(s.height for s in strips)), BG)
    y = 0
    for s in strips:
        sheet.alpha_composite(s, (0, y))
        y += s.height
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out)
    return out


# ---- the rigged character --------------------------------------------------------------------

#: Published row -> (view, clip in that view's rig). ``turn`` is composed:
#: the idle pose of each view in turn.
ROWS: Dict[str, Tuple[str, str]] = {
    "idle": ("front_3q", "idle"),
    "walk": ("side", "walk"),
    "talk": ("front", "talk"),
    "idle_back": ("back_3q", "idle"),
    "walk_away": ("back_3q", "walk"),
    "walk_toward": ("front_3q", "walk"),
}
TURN_ROW = ("front", "front_3q", "side", "back_3q", "back")


class RiggedCharacter:
    """The rigs of one generated character, rendered as the sheet's rows."""

    def __init__(self, rigs: Dict[str, Path]) -> None:
        from ..authoring.rigdoc import RigDocument

        self.docs = {k: RigDocument.load(p) for k, p in rigs.items()}

    def frame_size(self) -> Tuple[int, int]:
        """The size of a rendered frame (the rig frame at its render scale)."""
        fr = next(iter(self.docs.values())).frame
        k = int(fr.get("render_scale", 1))
        return int(fr["width"]) * k, int(fr["height"]) * k

    def rows(self) -> List[Tuple[str, int, int]]:
        out = []
        for name, (view, clip) in ROWS.items():
            c = self.docs[view].clips[clip]
            out.append((name, int(c["frames"]), int(c["duration_ms"])))
        out.append(("turn", len(TURN_ROW), 140))
        return out

    def render_frame(self, animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        if animation == "turn":
            doc = self.docs[TURN_ROW[frame_idx % len(TURN_ROW)]]
            return doc.render_frame("idle", 0, 8)
        view, clip = ROWS[animation]
        return self.docs[view].render_frame(clip, frame_idx, frame_count)


def posed_sheet(rigs: Dict[str, Path], out: Path, *, rows: Optional[Sequence[str]] = None, scale: float = 1.0) -> Path:
    """The posed rows of a rigged character, one strip each, labelled."""
    rc = RiggedCharacter(rigs)
    names = list(rows or [r[0] for r in rc.rows()])
    counts = {n: f for n, f, _ in rc.rows()}
    strips = []
    for name in names:
        ims = [rc.render_frame(name, i, counts[name]) for i in range(counts[name])]
        strips.append((name, ims))
    box = _union_bbox(im for _n, ims in strips for im in ims)
    fw, fh = box[2] - box[0] + 8, box[3] - box[1] + 8
    if scale != 1.0:
        fw, fh = int(fw * scale), int(fh * scale)
    label_w = 110
    width = label_w + fw * max(len(ims) for _n, ims in strips)
    sheet = Image.new("RGBA", (width, (fh + 6) * len(strips) + 6), BG)
    for r, (name, ims) in enumerate(strips):
        y = 6 + r * (fh + 6)
        _label(sheet, (8, y + fh // 2 - 8), name, 15)
        for i, im in enumerate(ims):
            crop = im.crop((box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4))
            if scale != 1.0:
                crop = crop.resize((fw, fh), Image.LANCZOS)
            sheet.alpha_composite(crop, (label_w + i * fw, y))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out)
    return out


def actor_metadata(spec: CharacterSpec) -> dict:
    name = slug(spec.name)
    traits = ["humanoid", "townsfolk", "generated"]
    return {
        "actor": {"character_id": f"npc_chargen_{name}", "display_name": spec.name},
        "authoring_description": (
            f"A generated background townsperson ({spec.base.replace('_', ' ')}, seed {spec.seed}) from the character "
            "generator (ambition_sprite2d_renderer.chargen). It parodies no one; its look is drawn from the spec."
        ),
        "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Medium", "traits": traits, "locomotion_hint": "Walk"},
        "capabilities": {
            "traversal": {"walk": True, "jump": None, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": True,
                          "door_access": ["public"]},
            "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
        },
        "brain": {"default_preset": "patrol_peaceful"},
        "actions": {"default_preset": "peaceful"},
        "visual": {"default_pose": "idle"},
        "tags": traits + ["svg_rigged"],
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "interaction.talk": {"animation": "talk", "events": []},
        },
    }


def publish_sheet(spec: CharacterSpec, out_dir: Path, rigs: Optional[Dict[str, Path]] = None) -> List[Path]:
    """The gameplay sprite sheet of ``spec`` (its rows: :data:`ROWS` and
    ``turn``) with its YAML/RON manifests, actor sidecar and previews."""
    from ..authoring.part_flipbook import publish_rig_flipbook
    from ..authoring.sheet_build import build_sheet

    out_dir = Path(out_dir)
    if rigs is None:
        rigs = write_character(spec, out_dir).rigs
    rc = RiggedCharacter(rigs)
    target = f"chargen_{slug(spec.name)}"
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=target,
        rows=rc.rows(),
        render_fn=rc.render_frame,
        out_dir=out_dir,
        frame_size=rc.frame_size(),
        auto_crop=True,
        crop_margin=4,
        actor_metadata=actor_metadata(spec),
        sheet_tuning={"collision_scale": 1.7},
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(target, rc.rows(), rc.render_frame, outputs, frame_transform, out_dir)
    return [Path(outputs[k]) for k in keys if outputs.get(k)] + list(parts.values())


__all__ = ["ROWS", "RiggedCharacter", "actor_metadata", "contact_sheet", "posed_sheet", "publish_sheet", "render_view", "turnaround"]
