"""The void versions of the three polygon fighters: the same rig, a void paint.

The void's own creatures (`void_lizard`, `void_star`) have no colour. Their
bodies are near to black, and a thin white edge on the outline shows their
form. A void polygon is a polygon fighter made of that: each facet is a dark
grey from the luminance of its source colour, the outline of each part is
white (grey on the far limbs, so near and far stay clear), the seams of the
facets are a dim grey line, and two white eye slits are on the faceless head.

⛔ **ONLY THE PAINT CHANGES.** The gameplay reads the source fighter's frame
data, so a void sheet must have the same rows, frames, frame size, crop and
hit volumes as its source. This module gets each of these from the SOURCE
module and does not measure them again:

* the padding, the frame size and the plant offsets of each frame;
* the authored hit volumes and the gameplay body (they are geometry);
* the axis of each swing effect (`blade_axis` reads the blade by brightness,
  and a void blade is black, so it must read the source frame).

The void art adds no alpha out of the source silhouette: a new stroke is
thinner than the outline stroke under it, and the eye slits are in the head.
`tests/test_void_polygon_targets.py` holds this.

The void SVG is a derived file, written to a content-addressed temp path in
the way of `mary_o_v2_svg_poc._recolored_svg`. The source SVG stays the only
editable art: an edit to it goes into the void version on the next publish.
"""

from __future__ import annotations

import copy
import hashlib
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from PIL import Image

from ambition_sprite2d_renderer.authoring import rigdoc, swing_effects
from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.authoring.svg_parts import SVG_NS  # also registers the prefixes

Point = Tuple[float, float]

#: The outline of a near part, and of a far part (a far limb is behind the
#: body, so its edge is dimmer).
EDGE_NEAR = "#f6f6f6"
EDGE_FAR = "#909090"
#: The thin line at the seam of two facets, at most this wide (it is thinner
#: on a part with a thin outline: see `_paint_part`).
SEAM = "#505050"
SEAM_WIDTH = 2.0
#: The eye slits.
EYE = "#ffffff"
#: The darkest and the lightest facet grey. The lightest is for a facet whose
#: source colour is white; the usual lit facet is near to the middle.
FACET_DARK = 9
FACET_LIGHT = 58

_HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_DRAWN = {"path", "polygon", "polyline", "rect", "circle", "ellipse", "line"}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _rgb(text: str) -> Optional[Tuple[int, int, int]]:
    match = _HEX.fullmatch(text.strip())
    if match is None:
        return None
    value = match.group(1)
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def facet_grey(colour: str) -> str:
    """The void grey of one source facet colour: its luminance, made dark.

    The source's shading stays (a lit facet is lighter than a facet in shade),
    but all of it is in the low end, so the body reads as black.
    """
    rgb = _rgb(colour)
    if rgb is None:
        return colour
    lum = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255.0
    g = round(FACET_DARK + (FACET_LIGHT - FACET_DARK) * lum ** 1.4)
    return f"#{g:02x}{g:02x}{g:02x}"


def _paint(elem: ET.Element, key: str) -> Optional[str]:
    match = re.search(rf"(?:^|;)\s*{key}\s*:\s*([^;]+)", elem.get("style") or "")
    return match.group(1).strip() if match else elem.get(key)


def _set_paint(elem: ET.Element, key: str, value: str) -> None:
    style = elem.get("style")
    if style and re.search(rf"(?:^|;)\s*{key}\s*:", style):
        elem.set("style", re.sub(rf"((?:^|;)\s*{key}\s*:\s*)[^;]+", rf"\g<1>{value}", style))
    else:
        elem.set(key, value)


def _stroked(elem: ET.Element) -> bool:
    stroke = _paint(elem, "stroke")
    return bool(stroke) and stroke != "none"


def _opaque(elem: ET.Element) -> bool:
    for key in ("opacity", "fill-opacity"):
        value = _paint(elem, key)
        if value is not None and float(value) < 0.999:
            return False
    return True


_PATH_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_ARITY = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "Z": 0}


def _vertices(elem: ET.Element) -> Optional[List[Point]]:
    """The corners of a straight or curved shape, in its parent's coordinates.

    A curve's control points are corners too: a curve is inside the hull of
    its control points, so a test on these points is a safe test. `None` for
    a shape this does not read (an arc, an unknown element).
    """
    from ambition_sprite2d_renderer.authoring.svg_parts import _affine

    tag = _local(elem.tag)
    points: List[Point] = []
    if tag in ("polygon", "polyline"):
        values = [float(v) for v in re.split(r"[\s,]+", (elem.get("points") or "").strip()) if v]
        points = list(zip(values[0::2], values[1::2]))
    elif tag == "path":
        tokens = _PATH_TOKEN.findall(elem.get("d") or "")
        x = y = sx = sy = 0.0
        cmd = None
        i = 0
        while i < len(tokens):
            if tokens[i].isalpha():
                cmd = tokens[i]
                i += 1
                if cmd in "Zz":
                    x, y = sx, sy
                    continue
            if cmd is None or cmd.upper() not in _ARITY:
                return None
            n = _ARITY[cmd.upper()]
            args = [float(v) for v in tokens[i : i + n]]
            if len(args) < n:
                return None
            i += n
            rel = cmd.islower()
            up = cmd.upper()
            if up == "H":
                x = x + args[0] if rel else args[0]
            elif up == "V":
                y = y + args[0] if rel else args[0]
            else:
                pairs = list(zip(args[0::2], args[1::2]))
                for px, py in pairs[:-1]:
                    points.append((x + px, y + py) if rel else (px, py))
                ex, ey = pairs[-1]
                x, y = (x + ex, y + ey) if rel else (ex, ey)
            points.append((x, y))
            if up == "M":
                sx, sy = x, y
                cmd = "l" if rel else "L"  # later pairs of a moveto are linetos
    else:
        return None
    a, b, c, d, e, f = _affine(elem.get("transform"))
    return [(a * px + c * py + e, b * px + d * py + f) for px, py in points]


def _inside(point: Point, polygon: Sequence[Point], tolerance: float = 0.75) -> bool:
    """Whether `point` is in `polygon` or within `tolerance` of its edge."""
    x, y = point
    hit = False
    for (x0, y0), (x1, y1) in zip(polygon, [*polygon[1:], polygon[0]]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
        dx, dy = x1 - x0, y1 - y0
        t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / max(dx * dx + dy * dy, 1e-12)))
        if (x - x0 - t * dx) ** 2 + (y - y0 - t * dy) ** 2 <= tolerance ** 2:
            return True
    return hit


@dataclass(frozen=True)
class EyeSlit:
    """One white eye slit, as a polygon in the head group's own coordinates."""

    points: Tuple[Point, ...]


def void_svg_text(source_svg: Path, eyes: Sequence[EyeSlit]) -> str:
    """The source SVG, painted as the void. The geometry does not change."""
    ET.register_namespace("", SVG_NS)
    root = ET.fromstring(Path(source_svg).read_bytes())
    parent = {child: node for node in root.iter() for child in node}
    head = None
    for group in [e for e in root.iter() if _local(e.tag) == "g"]:
        gid = group.get("id") or ""
        if not gid.startswith("polygon-"):
            continue
        if gid == "polygon-head":
            head = group
        if any((p.get("id") or "").startswith("polygon-") for p in _ancestors(group, parent)):
            continue  # a part inside a part: its parent group paints it
        _paint_part(group, edge=EDGE_FAR if "-far-" in gid else EDGE_NEAR, parent=parent)
    if head is None:
        raise ValueError(f"{source_svg}: no `polygon-head` group for the eye slits")
    for index, eye in enumerate(eyes):
        slit = ET.SubElement(head, f"{{{SVG_NS}}}polygon")
        slit.set("id", f"void-eye-{index}")
        slit.set("points", " ".join(f"{x:g},{y:g}" for x, y in eye.points))
        slit.set("fill", EYE)
    return ET.tostring(root, encoding="unicode")


def _ancestors(elem: ET.Element, parent: Dict[ET.Element, ET.Element]):
    node = parent.get(elem)
    while node is not None:
        yield node
        node = parent.get(node)


def _paint_part(group: ET.Element, edge: str, parent: Dict[ET.Element, ET.Element]) -> None:
    """Paint one rig part: dark facets, grey seams, and its outline on top.

    The source draws each part as an outlined base shape with unoutlined facets
    on it. A seam on each facet would cover the inner half of the outline, so
    the outline MOVES: the base keeps its fill, and its stroke goes to a copy
    after the facets that follow it (before the next outlined shape). The edge
    is drawn once, as in the source, so its antialiased alpha is the source's;
    a second copy on top would make each soft edge pixel more opaque.
    """
    outlines: List[ET.Element] = []
    # The outlined shape each facet sits on: the last one before it in the
    # same parent.
    base_of: Dict[ET.Element, Tuple[List[Point], float]] = {}
    for elem in list(group.iter()):
        if _local(elem.tag) not in _DRAWN:
            continue
        fill = _paint(elem, "fill")
        if fill and fill != "none":
            _set_paint(elem, "fill", facet_grey(fill))
        holder = parent.get(elem)
        if _stroked(elem):
            _set_paint(elem, "stroke", edge)
            if fill and fill != "none":
                outlines.append(elem)
                base = _vertices(elem)
                if base:
                    base_of[holder] = (base, float(_paint(elem, "stroke-width") or 1.0))
                else:
                    base_of.pop(holder, None)
            continue
        base, outline_width = base_of.get(holder, (None, 0.0))
        # The seam's outer edge stays a clear 1.5 units in from the outline's,
        # so no antialiased pixel at the silhouette gets the two summed.
        seam_width = min(SEAM_WIDTH, outline_width - 3.0)
        corners = _vertices(elem)
        if not (fill and fill != "none" and _opaque(elem) and base and corners):
            continue
        # ⛔ A seam only on a facet IN its base shape. A facet that goes out of
        # the outline (the source has a few) would put new alpha out of the
        # silhouette with its seam, and the crop and the anchors are the
        # source's. In the base, the seam is in the outline stroke's width.
        if seam_width > 0.4 and all(_inside(point, base) for point in corners):
            _set_paint(elem, "stroke", SEAM)
            _set_paint(elem, "stroke-width", f"{seam_width:g}")
            elem.set("stroke-linejoin", "round")
    for elem in outlines:
        edge_copy = copy.deepcopy(elem)
        edge_copy.attrib.pop("id", None)
        for key in list(edge_copy.attrib):
            if _local(key) in ("label", "nodetypes"):
                edge_copy.attrib.pop(key)
        _set_paint(edge_copy, "fill", "none")
        _set_paint(elem, "stroke", "none")
        siblings = list(parent[elem])
        at = siblings.index(elem) + 1
        while at < len(siblings) and not (siblings[at] in outlines or _stroked(siblings[at])):
            at += 1
        parent[elem].insert(at, edge_copy)


def void_svg_path(source_svg: Path, eyes: Sequence[EyeSlit]) -> Path:
    """Write the void SVG once per content and return its path."""
    text = void_svg_text(source_svg, eyes)
    digest = hashlib.sha1(text.encode()).hexdigest()[:16]
    out = Path(tempfile.gettempdir()) / "ambition_void_polygon" / f"{Path(source_svg).stem}_void_{digest}.svg"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(text)
        tmp.replace(out)
    return out


def greyscale_effect(layer: Image.Image) -> Image.Image:
    """An effect layer with no colour: its luminance, lifted toward white.

    A white slash on a black body is the void's look; the alpha (the shape of
    the effect) does not change.
    """
    r, g, b, a = layer.split()
    lum = Image.merge("RGB", (r, g, b)).convert("L")
    lum = lum.point([round(255 * (v / 255.0) ** 0.6) for v in range(256)])
    return Image.merge("RGBA", (lum, lum, lum, a))


class VoidPolygon:
    """One void polygon target: the source fighter, painted as the void."""

    def __init__(
        self,
        source: ModuleType,
        target: str,
        display_name: str,
        eyes: Sequence[EyeSlit],
        description: str,
    ) -> None:
        self.source = source
        self.target = target
        self.eyes = tuple(eyes)
        self.actor_metadata = self._actor_metadata(display_name, description)
        self._clip_frames = lru_cache(maxsize=None)(self._build_clip)

    # ---- the void document -------------------------------------------------

    @property
    def doc(self) -> RigDocument:
        cached = getattr(self, "_doc", None)
        if cached is None:
            base = self.source._doc()
            data = copy.deepcopy(base.data)
            data["name"] = self.target
            source_svg = Path(str(base.svg_source["path"]))
            data["svg_source"]["path"] = str(void_svg_path(source_svg, self.eyes))
            cached = self._doc = RigDocument(data, source_path=base.source_path)
        return cached

    # ---- frames -----------------------------------------------------------

    def raw_frame(self, animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        """One void frame at the source frame's padding and plant offset."""
        source = self.source
        clip = source._prepared().library.clips[animation]
        if frame_count != clip.frame_count:
            raise ValueError(
                f"{animation}: requested {frame_count} publication frames, source declares {clip.frame_count}"
            )
        times = [
            round(i * clip.frame_duration_ms / 1000.0 / max(clip.duration_s, 1e-9), 9)
            for i in range(frame_count)
        ]
        padding = source._publication_padding()
        lift = source._doc().plant_offsets(animation, times, padding=padding)[frame_idx]
        return self.doc.render_planted(animation, times[frame_idx], lift, padding=padding)

    def _axes(self, animation: str, frame_count: int):
        """The axis of the swing on each frame, read from the SOURCE fighter."""
        strike_axes = getattr(self.source, "_strike_axes", None)
        if strike_axes is not None:
            return strike_axes(animation, frame_count, self.source._publication_padding())
        return [
            swing_effects.blade_axis(self.source._raw_frame(animation, i, frame_count))
            for i in range(frame_count)
        ]

    def _build_clip(self, animation: str, frame_count: int) -> tuple:
        """Every frame of one clip, with the source's effect in grey under it.

        The effect is drawn alone (on clear frames, at the source's axes), made
        grey, and then put under the void body, which is the order every
        polygon effect uses (`composite_layer` and then `composite_canvas`).
        """
        raw = [self.raw_frame(animation, i, frame_count) for i in range(frame_count)]
        spec = self.source._spec_for(animation)
        if not spec:
            return tuple(raw)
        clear = [Image.new("RGBA", frame.size, (0, 0, 0, 0)) for frame in raw]
        effect = swing_effects.composite_authored_effect(clear, spec, axes=self._axes(animation, frame_count))
        out = []
        for layer, body in zip(effect, raw):
            comp = Image.new("RGBA", body.size, (0, 0, 0, 0))
            rigdoc.composite_layer(comp, greyscale_effect(layer), name="swing")
            rigdoc.composite_canvas(comp, body)
            out.append(comp)
        return tuple(out)

    def render_frame(self, animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        return self._clip_frames(animation, frame_count)[frame_idx]

    # ---- publication ------------------------------------------------------

    def _actor_metadata(self, display_name: str, description: str) -> dict:
        meta = copy.deepcopy(self.source.ACTOR_METADATA)
        meta["actor"] = {"character_id": self.target, "display_name": display_name}
        authoring = meta.setdefault("authoring_description", {})
        authoring["concept"] = description
        authoring["visual_language"] = [
            "the source polygon fighter's rig, poses and frames, painted as the void",
            "near-black facets with dark grey form shade from the source's own shading",
            "a crisp white edge on each near part, a grey edge on the far limbs",
            "two white eye slits on the faceless head",
            "greyscale only: no colour, and no drop shadow",
        ]
        meta.setdefault("body", {}).setdefault("traits", [])
        meta["body"]["traits"] = [*meta["body"]["traits"], "void", "enemy"]
        meta["tags"] = [*meta.get("tags", []), "void", "enemy"]
        return meta

    def render(self, out_dir, **opts):
        del opts
        source = self.source
        base = source._doc()
        rows = base.rows()
        frame_transform: dict = {}
        outputs = build_sheet(
            frame_transform_out=frame_transform,
            target=self.target,
            rows=rows,
            render_fn=self.render_frame,
            out_dir=Path(out_dir),
            frame_size=source._publication_frame_size(),
            auto_crop=True,
            crop_margin=4,
            actor_metadata=self.actor_metadata,
            body_metrics_fn=source._body_metrics,
            animation_key_map={name: name for name, _f, _d in rows},
            attack_hitboxes=source._attack_hitboxes(),
            pose_bodies="authored",
            sheet_tuning=base.sprite_tuning or {"collision_scale": 1.8},
            # The source's own facing (only `pointed_polygon` declares one; the
            # default is the same `False` the other two publish).
            authored_faces_left=base.authored_faces_left,
        )
        keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
        parts = publish_rig_flipbook(
            self.target, rows, self.render_frame, outputs, frame_transform, Path(out_dir),
            render_clip=lambda row, count: list(self._build_clip(row, count)),
        )
        return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


def module_api(void: VoidPolygon) -> Tuple[str, dict, Callable]:
    """``(TARGET_NAME, ACTOR_METADATA, render)`` for a target module."""
    return void.target, void.actor_metadata, void.render
