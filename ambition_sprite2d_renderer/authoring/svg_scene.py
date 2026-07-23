"""The editable SVG component scene: parts registered once, frames assembled.

This is the file a human opens in Inkscape. Structure:

  * a visible **parts** layer — every registered part's local geometry, laid out
    on a labelled grid below the frame area. This is the *editable source*:
    each part is a named group; editing its nodes/colours updates every frame
    that uses it, because...
  * one hidden layer per **animation**, containing one sub-layer per frame,
    whose content is ``<use href="#part_...">`` placements (plus any
    frame-local "dynamic" geometry that is not yet a registered part).

``ComponentScene`` also round-trips: ``load()`` parses a (possibly
human-edited) scene back, and ``frame_doc()`` emits a standalone renderable
SVG for any frame — parts in ``<defs>``, frame body inline — which the sheet
pipeline rasterizes to publish sprites *from the edited scene*. That closes
the human-in-the-loop authoring cycle:

    PIL paint program → capture → scene SVG → human edits parts in Inkscape
        → rebuild sheet from scene → equivalence harness checks the contract

Stdlib + ElementTree only.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SVG_NS = "http://www.w3.org/2000/svg"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"
XLINK_NS = "http://www.w3.org/1999/xlink"

for _p, _u in (("", SVG_NS), ("inkscape", INK_NS), ("xlink", XLINK_NS)):
    ET.register_namespace(_p, _u)

_LABEL = f"{{{INK_NS}}}label"
_GROUPMODE = f"{{{INK_NS}}}groupmode"

# Grid layout for the parts gallery (supersampled-canvas units).
_CELL = 420
_COLS = 4


class ComponentScene:
    """Parts library + per-frame assemblies for one target."""

    def __init__(self, canvas: Tuple[int, int]) -> None:
        self.canvas = canvas
        # part id -> (semantic name, local-geometry SVG body)
        self.parts: Dict[str, Tuple[str, str]] = {}
        # (anim, frame_idx) -> frame body SVG (uses + dynamic geometry)
        self.frames: Dict[Tuple[str, int], str] = {}

    # -- building from recorders --------------------------------------------
    @classmethod
    def from_recorders(cls, canvas: Tuple[int, int], recorders) -> "ComponentScene":
        """``recorders``: dict[(anim, frame_idx)] -> DrawRecorder."""
        scene = cls(canvas)
        for key in sorted(recorders):
            rec = recorders[key]
            for pid, (name, body) in rec.part_defs.items():
                scene.parts.setdefault(pid, (name, body))
            scene.frames[key] = rec.body_svg()
        return scene

    # -- rendering -----------------------------------------------------------
    def frame_doc(self, anim: str, frame_idx: int) -> str:
        """A standalone renderable SVG for one frame (parts in <defs>)."""
        w, h = self.canvas
        defs = "".join(
            f'<g id="{pid}">{body}</g>' for pid, (_n, body) in self.parts.items()
        )
        body = self.frames[(anim, frame_idx)]
        return (
            f'<svg xmlns="{SVG_NS}" xmlns:xlink="{XLINK_NS}" '
            f'xmlns:inkscape="{INK_NS}" '
            f'width="{w}px" height="{h}px" viewBox="0 0 {w} {h}">'
            f"<defs>{defs}</defs>{body}</svg>"
        )

    def missing_part_refs(self) -> List[str]:
        """Part ids referenced by frames but absent from the library."""
        missing: List[str] = []
        for body in self.frames.values():
            for pid in re.findall(r'href="#(part_[A-Za-z0-9_]+)"', body):
                if pid not in self.parts and pid not in missing:
                    missing.append(pid)
        return missing

    # -- the editable document ----------------------------------------------
    def to_editable_svg(self) -> str:
        w, h = self.canvas
        rows = (len(self.parts) + _COLS - 1) // _COLS
        total_h = h + rows * _CELL + _CELL // 2

        gallery: List[str] = []
        for i, (pid, (name, body)) in enumerate(self.parts.items()):
            gx = _CELL // 2 + (i % _COLS) * _CELL
            gy = h + _CELL // 2 + (i // _COLS) * _CELL
            gallery.append(
                f'<g transform="translate({gx} {gy})">'
                f'<g id="{pid}" inkscape:label="{name}">{body}</g></g>'
            )

        anims: Dict[str, List[Tuple[int, str]]] = {}
        for (anim, idx), body in self.frames.items():
            anims.setdefault(anim, []).append((idx, body))

        layers: List[str] = [
            f'<g inkscape:label="parts" inkscape:groupmode="layer">'
            f'{"".join(gallery)}</g>'
        ]
        first = True
        for anim in sorted(anims):
            sub = "".join(
                f'<g inkscape:label="{anim}/{idx:02d}" inkscape:groupmode="layer"'
                f'{"" if first and idx == min(i for i, _ in anims[anim]) else " style=\"display:none\""}>'
                f"{body}</g>"
                for idx, body in sorted(anims[anim])
            )
            style = "" if first else ' style="display:none"'
            layers.append(
                f'<g inkscape:label="anim:{anim}" inkscape:groupmode="layer"{style}>{sub}</g>'
            )
            first = False

        return (
            f'<svg xmlns="{SVG_NS}" xmlns:xlink="{XLINK_NS}" '
            f'xmlns:inkscape="{INK_NS}" '
            f'data-frame-canvas="{w} {h}" '
            f'width="{w}px" height="{total_h}px" viewBox="0 0 {w} {total_h}">'
            f'{"".join(layers)}</svg>'
        )

    def save(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_editable_svg())
        return path

    # -- loading a (possibly human-edited) scene ------------------------------
    @classmethod
    def load(cls, path: Path) -> "ComponentScene":
        root = ET.fromstring(Path(path).read_text())
        # The frame canvas is stored explicitly (the gallery extends the
        # viewBox, so it cannot be recovered from the viewBox alone).
        canvas_attr = root.get("data-frame-canvas")
        if canvas_attr:
            cw, ch = (int(float(v)) for v in canvas_attr.split())
        else:  # legacy fallback: square canvas of viewBox width
            cw = ch = int(float((root.get("viewBox") or "0 0 512 512").split()[2]))
        scene = cls((cw, ch))

        def serialize_children(elem: ET.Element) -> str:
            return "".join(
                ET.tostring(child, encoding="unicode") for child in elem
            )

        for layer in root:
            label = layer.get(_LABEL) or ""
            if label == "parts":
                for wrapper in layer:
                    inner = wrapper.find(f"{{{SVG_NS}}}g")
                    if inner is None or not (inner.get("id") or "").startswith("part_"):
                        continue
                    pid = inner.get("id")
                    name = inner.get(_LABEL) or pid
                    scene.parts[pid] = (name, serialize_children(inner))
            elif label.startswith("anim:"):
                anim = label[len("anim:"):]
                for frame_layer in layer:
                    flabel = frame_layer.get(_LABEL) or ""
                    m = re.fullmatch(rf"{re.escape(anim)}/(\d+)", flabel)
                    if not m:
                        continue
                    # Strip the visibility style the editable doc added.
                    if frame_layer.get("style") == "display:none":
                        del frame_layer.attrib["style"]
                    scene.frames[(anim, int(m.group(1)))] = serialize_children(frame_layer)
        return scene

    # -- summary -------------------------------------------------------------
    def stats(self) -> Dict[str, int]:
        uses = sum(len(re.findall(r"<use ", b)) for b in self.frames.values())
        return {
            "parts": len(self.parts),
            "frames": len(self.frames),
            "part_uses": uses,
        }
