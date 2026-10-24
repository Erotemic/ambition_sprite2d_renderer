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
import math
from dataclasses import dataclass
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


def render_view(spec: CharacterSpec, view: View, px_per_cm: float = 1.6, *, mirror: bool = False, state=None, features=None) -> Image.Image:
    """One view of ``spec``, its whole cell, ``px_per_cm`` pixels a centimetre
    (``state``: face channels, ``features``: components shown or hidden)."""
    dpi = 25.4 * px_per_cm / UNIT
    img = Image.open(io.BytesIO(_svg_to_png_bytes(view_svg(spec, view, state=state, features=features), dpi))).convert("RGBA")
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


# ---- faces, species and wardrobe ---------------------------------------------------------------


def _head_crop(spec: CharacterSpec, view: View, px_per_cm: float, *, state=None, features=None, mirror: bool = False) -> Image.Image:
    """The head and shoulders of one view (``state``: face channels)."""
    from .body import build
    from .rig import CELL_W, GROUND

    fig = build(spec)
    im = render_view(spec, view, px_per_cm, state=state, features=features)
    k = px_per_cm / UNIT  # image px per SVG unit
    neck = view.project(fig.joints["neck"])
    cx = (CELL_W / 2.0 + neck[0] * UNIT) * k
    top = (GROUND + (fig.crown - 0.55 * fig.hh) * UNIT) * k
    size = 2.1 * fig.hh * UNIT * k
    crop = _on_bg(im.crop((int(cx - size / 2), int(top), int(cx + size / 2), int(top + size))))
    return crop.transpose(Image.FLIP_LEFT_RIGHT) if mirror else crop


def _grid(title: str, rows: Sequence[Tuple[str, Sequence[Tuple[str, Image.Image]]]], out: Path, *, label_w: int = 150) -> Path:
    """Labelled rows of labelled tiles on the review grey."""
    tw = max(im.width for _r, tiles in rows for _n, im in tiles)
    th = max(im.height for _r, tiles in rows for _n, im in tiles)
    cols = max(len(tiles) for _r, tiles in rows)
    head, cap = 34, 20
    sheet = Image.new("RGBA", (max(label_w + cols * (tw + 6) + 6, 16 + 10 * len(title)), head + len(rows) * (th + cap + 8)), BG)
    _label(sheet, (8, 8), title, 17)
    for r, (name, tiles) in enumerate(rows):
        y = head + r * (th + cap + 8)
        _label(sheet, (8, y + th // 2 - 8), name, 14)
        for c, (cap_text, im) in enumerate(tiles):
            x = label_w + c * (tw + 6)
            sheet.alpha_composite(im, (x + (tw - im.width) // 2, y + th - im.height))
            _label(sheet, (x + 4, y + th + 2), cap_text, 12)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out)
    return out


def _figure_tiles(spec: CharacterSpec, px_per_cm: float, views: Sequence[View] = VIEWS, *, features=None, state=None) -> List[Image.Image]:
    """The views of ``spec`` cropped to one shared box (a shared ground line)."""
    ims = [render_view(spec, v, px_per_cm, state=state, features=features) for v in views]
    box = _union_bbox(ims)
    w = max(im.getchannel("A").getbbox()[2] - im.getchannel("A").getbbox()[0] for im in ims) + 12
    out = []
    for im in ims:
        b = im.getchannel("A").getbbox()
        cx = (b[0] + b[2]) // 2
        out.append(_on_bg(im.crop((cx - w // 2, box[1] - 6, cx - w // 2 + w, box[3] + 4))))
    return out


#: The expressions a species sheet shows for each head.
SPECIES_FACES = ("neutral", "happy", "angry", "surprised", "sad")


def species_sheet(specs: Sequence[CharacterSpec], out: Path, *, px_per_cm: float = 1.5) -> Path:
    """Each character in its five views, then its head in a few expressions
    (front 3/4), one row each: heads of every species on one humanoid body."""
    from .face import face_channels

    rows = []
    for spec in specs:
        figs = _figure_tiles(spec, px_per_cm)
        rows.append((f"{spec.head.species}: {spec.name}", list(zip(("front", "front 3/4", "side", "back 3/4", "back"), figs))))
        heads = [(f, _head_crop(spec, VIEW_BY_KEY["front_3q"], px_per_cm * 2.2, state=face_channels(f))) for f in SPECIES_FACES]
        rows.append((f"{spec.head.species} faces", heads))
    return _grid("Species heads: one humanoid body, a fresh anthropomorphic head per species", rows, out)


def expression_sheet(spec: CharacterSpec, out: Path, *, px_per_cm: float = 3.2) -> Path:
    """Every face (emotions and looks) in front, front 3/4 and side, then the
    talking mouths (visemes) of a few emotions, and the blink."""
    from .face import FACES, VISEMES, face_channels

    views = [VIEW_BY_KEY[k] for k in ("front", "front_3q", "side")]
    rows = []
    for v in views:
        rows.append((v.label, [(f, _head_crop(spec, v, px_per_cm, state=face_channels(f))) for f in FACES]))
    for emo in ("neutral", "happy", "angry", "afraid"):
        rows.append((f"talk {emo}", [(vis, _head_crop(spec, VIEW_BY_KEY["front_3q"], px_per_cm, state=face_channels(emo, vis)))
                                     for vis in VISEMES]))
    rows.append(("blink", [(f"{v.key}", _head_crop(spec, v, px_per_cm, state=face_channels("neutral", blink=1.0))) for v in views]))
    return _grid(f"Expressions: {spec.name} (eyes, brows and mouth are rig parts; blink is an overlay)", rows, out, label_w=120)


def wardrobe_sheet(spec: CharacterSpec, out: Path, *, px_per_cm: float = 1.4,
                   views: Sequence[str] = ("front_3q", "side", "back_3q")) -> Path:
    """The spec as worn, then each wardrobe alternate swapped in (its slot's
    worn feature off, the alternate's on), in a few views. One rig: the
    swaps are feature toggles, not redraws."""
    from .rig import draw_views

    _fig, drawn = draw_views(spec, [VIEW_BY_KEY[views[0]]])
    worn = sorted({p.feature for p in drawn[0].parts if p.feature and "@" not in p.name})
    vs = [VIEW_BY_KEY[k] for k in views]
    rows = [("as worn", [(v.key, im) for v, im in zip(vs, _figure_tiles(spec, px_per_cm, vs))])]
    for item in spec.outfit.wardrobe:
        slot, _, kind = item.partition(":")
        feats = {f: (not f.startswith(slot + ":")) for f in worn}
        feats[f"{slot}:{kind}"] = True
        rows.append((f"{slot} -> {kind}", [(v.key, im) for v, im in zip(vs, _figure_tiles(spec, px_per_cm, vs, features=feats))]))
    return _grid(f"Wardrobe swaps: {spec.name} (one rig, components toggled)", rows, out)


# ---- the rigged character --------------------------------------------------------------------

#: The rows a published sheet carries by default: what the game asks a
#: townsperson or a fighter-capable NPC for (``CharacterAnim`` names). Any
#: library clip can be published by naming it (``publish_sheet(rows=...)``).
PUBLISH_ROWS: Tuple[str, ...] = (
    "idle", "idle_back", "walk", "walk_away", "walk_toward", "run", "skid", "jump", "fall", "land", "crouch", "crawl",
    "climb", "ledge_hang", "wall_slide", "dash", "attack", "jab", "attack_up", "attack_down", "air_neutral", "special",
    "hurt", "tumble", "death", "death_idle", "talk", "interact", "wave", "happy", "sit_down", "sit_idle", "stand_up",
    "sleep", "shield_hold", "item_hold", "item_pickup", "item_throw", "item_swing", "item_swing_up", "item_swing_down",
    "item_swing_back", "turnaround", "turn_away",
)

#: Rows composed across views: (view, mirrored) per frame, each the view's
#: idle. ``turnaround`` turns from facing right to facing left through the
#: front; ``turn_away`` through the back (a left view is its right twin
#: mirrored).
COMPOSED: Dict[str, Tuple[Tuple[str, bool], ...]] = {
    "turnaround": (("side", False), ("front_3q", False), ("front", False), ("front_3q", True), ("side", True)),
    "turn_away": (("side", False), ("back_3q", False), ("back", False), ("back_3q", True), ("side", True)),
}


class RiggedCharacter:
    """The rigs of one generated character, rendered as sheet rows. A row is
    a motion-library clip drawn from the view the library names for it
    (``motion.publish_views``), or a :data:`COMPOSED` turn."""

    def __init__(self, rigs: Dict[str, Path], rows: Optional[Sequence[str]] = None) -> None:
        from ..authoring.rigdoc import RigDocument

        self.docs = {k: RigDocument.load(p) for k, p in rigs.items()}
        some = next(iter(self.docs.values()))
        views = some.data.get("chargen", {}).get("publish_views") or {}
        self.views: Dict[str, str] = {name: views.get(name, "side") for name in some.clips}
        self.names = list(rows) if rows is not None else [r for r in PUBLISH_ROWS if r in self.views or r in COMPOSED]

    def frame_size(self) -> Tuple[int, int]:
        """The size of a rendered frame (the rig frame at its render scale)."""
        fr = next(iter(self.docs.values())).frame
        k = int(fr.get("render_scale", 1))
        return int(fr["width"]) * k, int(fr["height"]) * k

    def rows(self) -> List[Tuple[str, int, int]]:
        out = []
        for name in self.names:
            if name in COMPOSED:
                out.append((name, len(COMPOSED[name]), 90))
                continue
            c = self.docs[self.views[name]].clips[name]
            out.append((name, int(c["frames"]), int(c["duration_ms"])))
        return out

    def render_frame(self, animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        if animation in COMPOSED:
            view, mirrored = COMPOSED[animation][frame_idx % len(COMPOSED[animation])]
            im = self.docs[view].render_frame("idle", 0, int(self.docs[view].clips["idle"]["frames"]))
            return im.transpose(Image.FLIP_LEFT_RIGHT) if mirrored else im
        return self.docs[self.views[animation]].render_frame(animation, frame_idx, frame_count)


def posed_sheet(rigs: Dict[str, Path], out: Path, *, rows: Optional[Sequence[str]] = None, scale: float = 1.0) -> Path:
    """The posed rows of a rigged character, one strip each, labelled."""
    rc = RiggedCharacter(rigs, rows)
    names = [r[0] for r in rc.rows()]
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


def clip_union_sheet(rigs: Dict[str, Path], out: Path, *, clips: Optional[Sequence[str]] = None, samples: int = 6,
                     scale: float = 0.42, columns: int = 3, title: str = "") -> Path:
    """Every clip of the motion library (or ``clips``), each a strip of up to
    ``samples`` evenly spaced frames drawn from the view the sheet publishes
    it from, in ``columns`` columns: the whole clip union at a glance."""
    some = RiggedCharacter(rigs, [])
    names = list(clips) if clips is not None else list(some.views)
    rc = RiggedCharacter(rigs, names)
    strips = []
    for name, n, _ms in rc.rows():
        idx = sorted({round(i * (n - 1) / max(1, samples - 1)) for i in range(min(n, samples))})
        strips.append((f"{name} ({rc.views.get(name, '')}, {n}f)", [rc.render_frame(name, i, n) for i in idx]))
    box = _union_bbox(im for _n, ims in strips for im in ims)
    fw, fh = int((box[2] - box[0] + 6) * scale), int((box[3] - box[1] + 6) * scale)
    cap = 16
    sw = fw * samples + 8
    rows = (len(strips) + columns - 1) // columns
    head = 30
    sheet = Image.new("RGBA", (sw * columns + 8, head + rows * (fh + cap + 4)), BG)
    _label(sheet, (8, 6), title or f"Clip union ({len(strips)} clips), each from its sheet view", 16)
    for k, (name, ims) in enumerate(strips):
        col, row = divmod(k, rows)
        x, y = 4 + col * sw, head + row * (fh + cap + 4)
        _label(sheet, (x + 2, y), name, 11)
        for i, im in enumerate(ims):
            crop = im.crop((box[0] - 3, box[1] - 3, box[2] + 3, box[3] + 3)).resize((fw, fh), Image.LANCZOS)
            sheet.alpha_composite(crop, (x + i * fw, y + cap))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out)
    return out


# ---- held items ---------------------------------------------------------------------------------

#: World units per centimetre (a 185 cm townsperson stands 71.6 units tall
#: in the character catalog), to draw an item at its game size.
WORLD_PER_CM = 71.6 / 185.0


@dataclass
class HeldItemArt:
    """One row of the game's ``held_item_art.ron``: the picture, its size in
    world units, and where along its length the hand holds it (0 the near
    end; ``None`` its middle)."""

    item: str
    image: Path
    size: Tuple[float, float]
    grip: Optional[float] = None


def load_held_item_art(ron_path: Path, asset_root: Path) -> Dict[str, HeldItemArt]:
    """The rows of ``held_item_art.ron`` whose picture exists under ``asset_root``."""
    import re

    out = {}
    pat = re.compile(r'"(\w+)":\s*\(path:\s*"([^"]+)",\s*size:\s*\(([\d.]+),\s*([\d.]+)\)(?:,\s*grip:\s*Some\(([\d.]+)\))?')
    for m in pat.finditer(Path(ron_path).read_text(encoding="utf8")):
        img = Path(asset_root) / m.group(2)
        if img.exists():
            out[m.group(1)] = HeldItemArt(m.group(1), img, (float(m.group(3)), float(m.group(4))),
                                          float(m.group(5)) if m.group(5) else None)
    return out


def _hand_only(doc, depth: str = "near"):
    from ..authoring.rigdoc import RigDocument

    data = dict(doc.data)
    data["parts"] = [p for p in doc.data["parts"] if p["name"] == f"{depth}_hand"]
    hand = RigDocument(data)
    hand.path = getattr(doc, "path", None)
    return hand


def render_holding(doc, clip: str, frame: int, art: HeldItemArt, *, rest_angle: float = 24.0) -> Image.Image:
    """One frame of ``clip`` with ``art`` in the near hand, placed as the game
    places it: its grip on the hand part's pivot (the ``near_grip`` bone),
    pointing forward and ``rest_angle`` up when the hand is at rest, turning
    with the hand. The fist is drawn again over the item, so the fingers
    close round it."""
    n = int(doc.clips[clip]["frames"])
    t = doc.frame_time(clip, frame, n)
    world, params = doc.solve(clip, t)
    k = int(doc.frame.get("render_scale", 1))
    body = doc.render_at(clip, t, solved=(world, params))
    hand = _hand_only(doc).render_at(clip, t, solved=(world, params))
    grip_part = next(p for p in doc.data["parts"] if p["name"] == "near_hand")
    turn = world["near_grip"].angle - float(grip_part.get("rest_angle", 0.0))
    px_per_unit = float(doc.data.get("chargen", {}).get("px_per_cm", 0.62)) / WORLD_PER_CM * k
    w, h = art.size[0] * px_per_unit, art.size[1] * px_per_unit
    pic = Image.open(art.image).convert("RGBA").resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)
    g = 0.5 if art.grip is None else art.grip
    pivot = (g * pic.width, pic.height / 2.0)
    # Rotate about the grip: pad so the pivot is the centre, then rotate.
    r = int(math.ceil(math.hypot(max(pivot[0], pic.width - pivot[0]), pic.height))) + 2
    pad = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    pad.alpha_composite(pic, (int(round(r - pivot[0])), int(round(r - pivot[1]))))
    pad = pad.rotate(rest_angle - turn, resample=Image.BICUBIC)
    gx, gy = world["near_grip"].origin
    out = Image.new("RGBA", body.size, (0, 0, 0, 0))
    out.alpha_composite(body)
    out.alpha_composite(pad, (int(round(gx * k - r)), int(round(gy * k - r))))
    out.alpha_composite(hand)
    return out


#: The clips a held-items sheet shows: (view, clip, frame), frame -1 = the middle.
HELD_SHOTS: Tuple[Tuple[str, str, int], ...] = (
    ("front_3q", "item_hold", 0), ("side", "item_hold", 0), ("side", "walk", 2), ("side", "item_swing", 2),
    ("side", "item_swing", 3), ("side", "item_swing", 5), ("side", "item_swing_up", 3), ("side", "item_swing_down", 3),
    ("side", "jump", 3), ("side", "item_throw", 3), ("back_3q", "item_hold", 0), ("front", "item_hold", 0),
)


def held_items_sheet(rigs: Dict[str, Path], arts: Sequence[HeldItemArt], out: Path, *, shots=HELD_SHOTS, scale: float = 0.6,
                     title: str = "") -> Path:
    """Each item (a row) in the near hand through ``shots`` (view, clip,
    frame): the item's grip on the fist in every view and clip."""
    from ..authoring.rigdoc import RigDocument

    docs = {k: RigDocument.load(p) for k, p in rigs.items()}
    rows = []
    for art in arts:
        tiles = []
        for view, clip, frame in shots:
            doc = docs[view]
            n = int(doc.clips[clip]["frames"])
            fi = n // 2 if frame < 0 else min(frame, n - 1)
            tiles.append((f"{clip} {view}", render_holding(doc, clip, fi, art)))
        rows.append((art.item, tiles))
    box = _union_bbox(im for _r, tiles in rows for _n, im in tiles)
    fit = []
    for name, tiles in rows:
        fit.append((name, [(c, _on_bg(im.crop((box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4)).resize(
            (int((box[2] - box[0] + 8) * scale), int((box[3] - box[1] + 8) * scale)), Image.LANCZOS))) for c, im in tiles]))
    return _grid(title or "Held items: the game's item art on the fist (grip on the hand pivot, forward and 24 deg up at rest)", fit, out,
                 label_w=130)


def actor_metadata(spec: CharacterSpec, *, character_id: Optional[str] = None, description: Optional[str] = None) -> dict:
    """The actor sidecar of ``spec``. ``character_id`` is the game's catalog
    id (default ``npc_chargen_<slug>``); ``description`` is the
    ``authoring_description`` (default: a note that names the base and seed)."""
    name = slug(spec.name)
    traits = ["humanoid", "townsfolk", "generated"]
    return {
        "actor": {"character_id": character_id or f"npc_chargen_{name}", "display_name": spec.name},
        "authoring_description": description or (
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


def publish_sheet(spec: CharacterSpec, out_dir: Path, rigs: Optional[Dict[str, Path]] = None, *, target: Optional[str] = None,
                  metadata: Optional[dict] = None, rows: Optional[Sequence[str]] = None) -> List[Path]:
    """The gameplay sprite sheet of ``spec`` (``rows``, default
    :data:`PUBLISH_ROWS`) with its YAML/RON manifests, actor sidecar,
    part flipbook and previews.
    ``target`` names the files (default ``chargen_<slug>``); ``metadata`` is
    the actor sidecar (default :func:`actor_metadata`)."""
    from ..authoring.part_flipbook import publish_rig_flipbook
    from ..authoring.sheet_build import build_sheet

    out_dir = Path(out_dir)
    if rigs is None:
        rigs = write_character(spec, out_dir).rigs
    rc = RiggedCharacter(rigs, rows)
    target = target or f"chargen_{slug(spec.name)}"
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
        actor_metadata=metadata or actor_metadata(spec),
        sheet_tuning={"collision_scale": 1.7},
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(target, rc.rows(), rc.render_frame, outputs, frame_transform, out_dir)
    return [Path(outputs[k]) for k in keys if outputs.get(k)] + list(parts.values())


__all__ = ["COMPOSED", "HELD_SHOTS", "HeldItemArt", "held_items_sheet", "load_held_item_art", "render_holding", "clip_union_sheet", "PUBLISH_ROWS", "SPECIES_FACES", "expression_sheet", "species_sheet", "wardrobe_sheet", "RiggedCharacter", "actor_metadata", "contact_sheet", "posed_sheet", "publish_sheet", "render_view", "turnaround"]
