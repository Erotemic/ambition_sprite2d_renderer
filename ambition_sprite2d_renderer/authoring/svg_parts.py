"""Rasterize labelled subsets of a hand-authored SVG into per-part sprites.

The bone toolkit's other part kinds (``polygon``/``capsule``/``circle``) draw
procedural shapes from a palette. ``svg_parts`` instead lets a rig bind the
*actual* vector art a human drew in Inkscape: each rig ``sprite`` part names a
set of SVG element ids, and this module renders just those elements — with the
document's gradients, transforms and stacking intact — to a transparent raster
that the rig then pins to a bone and rotates.

The only source of truth is the SVG plus the ``.rig.json``; nothing binary is
written to disk. Re-author the SVG, re-render the sheet, and the rig follows.

Isolation works by *hiding everything else*: we keep ``<defs>`` (so gradient
fills resolve) and every ancestor ``transform`` (so the kept elements land in
their true document position), and set ``display:none`` on every other drawable
leaf and on sibling view layers. Rendering over the full document viewBox means
all parts share one coordinate frame, so a part's pivot is simply its joint
position in SVG user units.
"""

from __future__ import annotations

import io
import inspect
import warnings
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image

from ..profiling import profile

SVG_NS = "http://www.w3.org/2000/svg"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd"
XLINK_NS = "http://www.w3.org/1999/xlink"

# resvg renders mm-sized documents; 1 user unit == 1mm for these Inkscape files,
# so user-units -> pixels is dpi / MM_PER_INCH.
MM_PER_INCH = 25.4

_DRAWABLE = {"path", "polygon", "rect", "ellipse", "circle", "line", "image"}

for _prefix, _uri in (("", SVG_NS), ("inkscape", INK_NS),
                      ("sodipodi", SODIPODI_NS), ("xlink", XLINK_NS)):
    ET.register_namespace(_prefix, _uri)


_FALLBACK_WARNING_EMITTED = False


def _native_resvg_callable(module: object):
    """Return the compiled resvg entry point, never a Python compatibility shim."""
    svg_to_bytes = getattr(module, "svg_to_bytes", None)
    if callable(svg_to_bytes) and inspect.isbuiltin(svg_to_bytes):
        return svg_to_bytes
    return None


@profile
def _svg_to_png_bytes(svg_string: str, dpi: float) -> bytes:
    """Rasterize SVG, preferring native resvg and falling back to CairoSVG.

    CairoSVG is intentionally a compatibility path for authoring/review
    environments that do not have the ``resvg-py`` wheel installed.  Its
    antialiasing and SVG edge-case behavior can differ from resvg, so callers
    must not mistake fallback pixels for canonical publication output.
    """
    try:
        import resvg_py
    except (ImportError, ModuleNotFoundError):
        resvg_py = None

    svg_to_bytes = (
        _native_resvg_callable(resvg_py) if resvg_py is not None else None
    )
    if svg_to_bytes is not None:
        return bytes(svg_to_bytes(svg_string=svg_string, dpi=float(dpi)))

    try:
        import cairosvg
    except ModuleNotFoundError as ex:
        raise RuntimeError(
            "SVG sprite rendering requires native resvg-py; CairoSVG can be used "
            "as a review-only fallback when it is installed"
        ) from ex

    global _FALLBACK_WARNING_EMITTED
    if not _FALLBACK_WARNING_EMITTED:
        warnings.warn(
            "SVG RASTERIZER FALLBACK: native resvg_py is unavailable or is only "
            "a Python shim; using CairoSVG for authoring/review. Pixel bounds, "
            "antialiasing, and some SVG semantics may differ. Install resvg-py "
            "before treating generated pixels or rebuilt rig geometry as "
            "canonical.",
            RuntimeWarning,
            stacklevel=3,
        )
        _FALLBACK_WARNING_EMITTED = True
    return bytes(
        cairosvg.svg2png(
            bytestring=svg_string.encode("utf8"),
            dpi=float(dpi),
        )
    )

def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _label(elem: ET.Element) -> Optional[str]:
    return elem.get(f"{{{INK_NS}}}label")


def _hide(elem: ET.Element) -> None:
    style = elem.get("style", "") or ""
    elem.set("style", (style + ";" if style else "") + "display:none")


@lru_cache(maxsize=16)
def _parse(svg_path: str, mtime_ns: int, size: int) -> bytes:
    """Cached raw SVG bytes, invalidated by source-file identity changes."""
    del mtime_ns, size
    return Path(svg_path).read_bytes()


def view_layers(root: ET.Element) -> List[str]:
    """Inkscape ``label``s of the top-level layers (the per-viewpoint groups)."""
    return [lbl for g in root if (lbl := _label(g)) is not None]


def _descendant_drawables(elem: ET.Element) -> List[ET.Element]:
    out: List[ET.Element] = []
    for child in elem.iter():
        if _local(child.tag) in _DRAWABLE:
            out.append(child)
    return out


@profile
def rasterize_subset(
    svg_path: Path,
    view: str,
    include_ids: Sequence[str],
    dpi: float,
) -> Tuple[Optional[Image.Image], Tuple[int, int], float]:
    """Render only ``include_ids`` (within layer ``view``) to a cropped RGBA.

    ``include_ids`` may name leaf elements or groups (a group keeps all its
    drawable descendants). Returns ``(image_or_None, (off_x, off_y), px_per_unit)``
    where the offset is the cropped image's top-left in full-canvas pixels and
    ``px_per_unit`` converts SVG user units to those pixels. ``None`` when the
    subset renders empty (e.g. a fully off-screen or transparent selection).

    The expensive resvg result is cached process-wide by source-file identity,
    view, subset, and DPI. ``RigDocument`` also has a per-document prepared-part
    cache; this outer cache bridges sheet/canonical/portrait documents that use
    the same immutable SVG subset during one regeneration process. A copy is
    returned so callers cannot mutate the shared cache entry.
    """
    svg_path = Path(svg_path)
    stat = svg_path.stat()
    image, offset, px_per_unit = _rasterize_subset_cached(
        str(svg_path),
        int(stat.st_mtime_ns),
        int(stat.st_size),
        str(view),
        tuple(str(i) for i in include_ids),
        float(dpi),
    )
    return (image.copy() if image is not None else None), offset, px_per_unit


@lru_cache(maxsize=256)
@profile
def _rasterize_subset_cached(
    svg_path: str,
    mtime_ns: int,
    size: int,
    view: str,
    include_ids: Tuple[str, ...],
    dpi: float,
) -> Tuple[Optional[Image.Image], Tuple[int, int], float]:
    raw = _parse(svg_path, mtime_ns, size)
    root = ET.fromstring(raw)

    by_id: Dict[str, ET.Element] = {}
    for elem in root.iter():
        eid = elem.get("id")
        if eid is not None:
            by_id[eid] = elem

    keep: set = set()
    for iid in include_ids:
        elem = by_id.get(iid)
        if elem is None:
            continue
        keep.add(id(elem))
        for drawable in _descendant_drawables(elem):
            keep.add(id(drawable))

    # Hide sibling view layers wholesale, then every drawable leaf we don't keep.
    for layer in root:
        if _label(layer) is not None and _label(layer) != view:
            _hide(layer)
    for elem in root.iter():
        if _local(elem.tag) in _DRAWABLE and id(elem) not in keep:
            _hide(elem)

    svg_str = ET.tostring(root, encoding="unicode")
    png = _svg_to_png_bytes(svg_str, float(dpi))
    img = Image.open(io.BytesIO(png)).convert("RGBA")
    bbox = img.getbbox()
    px_per_unit = dpi / MM_PER_INCH
    if bbox is None:
        return None, (0, 0), px_per_unit
    return img.crop(bbox), (bbox[0], bbox[1]), px_per_unit
