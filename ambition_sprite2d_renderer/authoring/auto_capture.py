"""Route ANY registered target to the SVG backend — no code changes needed.

The cooperative seam (``DrawRecorder.part`` + ``PillowPartDraw``) gives the
best layer grouping, but only converted paint code has it. This module is the
universal fallback: while a target's *existing* render runs, every
``ImageDraw.Draw`` gets teed into a :class:`DrawRecorder`, so the published
raster is untouched and a vector capture falls out for free. Afterwards,
**part discovery** matches congruent shapes across frames (recovering each
occurrence's translate/rotate) and registers them once, turning N flattened
frames into a parts library + placements — the same
:class:`~.svg_scene.ComponentScene` the cooperative path produces.

Fidelity is *verified, never assumed*: each captured frame is rasterized and
compared against the actually-published sheet pixels; frames that don't match
are reported as gaps (targets that paste rasters, rotate layers, or draw
through unhooked APIs). The coverage command in ``equivalence_harness.py``
runs this across the whole roster so every character, prop and tile has a
measured conversion status instead of a claim.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .draw_recorder import DrawRecorder

Point = Tuple[float, float]

_POINTS_RE = re.compile(r'points="([^"]+)"')
_STYLE_STRIP_RE = re.compile(r'points="[^"]+"\s*')


def _parse_points(elem: str) -> Optional[List[Point]]:
    m = _POINTS_RE.search(elem)
    if not m:
        return None
    pts = []
    for pair in m.group(1).split():
        x, y = pair.split(",")
        pts.append((float(x), float(y)))
    return pts


def _style_key(elem: str) -> str:
    """The element with its coordinates removed — tag + paint style."""
    return _STYLE_STRIP_RE.sub("", elem)


def _fmt(n: float) -> str:
    return f"{n:.3f}".rstrip("0").rstrip(".")


def _emit_points(pts: Sequence[Point]) -> str:
    return " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in pts)


SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"


def split_elements(body: str) -> List[str]:
    """Split a recorder body into top-level elements via a real XML parser.

    Never regex: nested groups, ``<defs>``, filters and namespaced attributes
    must survive intact. Each returned string is one whole top-level element
    (a nested group travels as a single unit).
    """
    import xml.etree.ElementTree as ET

    for prefix, uri in (("", SVG_NS), ("xlink", XLINK_NS), ("inkscape", INK_NS)):
        ET.register_namespace(prefix, uri)
    root = ET.fromstring(
        f'<root xmlns="{SVG_NS}" xmlns:xlink="{XLINK_NS}" '
        f'xmlns:inkscape="{INK_NS}">{body}</root>')
    return [ET.tostring(child, encoding="unicode") for child in root]


class _Congruence:
    """Rigid-motion (translate+rotate) matcher for ordered point lists."""

    EPS = 0.75  # px at the supersampled scale — well under a visible shift

    @staticmethod
    def canonical(pts: Sequence[Point]) -> Tuple[Point, List[Point]]:
        """Translate so the centroid is the origin; keep orientation."""
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        return (cx, cy), [(p[0] - cx, p[1] - cy) for p in pts]

    @classmethod
    def match(cls, ref_local: Sequence[Point], pts: Sequence[Point]
              ) -> Optional[Tuple[Point, float]]:
        """If ``pts`` is a rigid motion of ``ref_local``, return (origin, deg)."""
        if len(ref_local) != len(pts):
            return None
        centroid, local = cls.canonical(pts)
        # Recover rotation from the first sufficiently-long reference vector.
        deg = 0.0
        for a, b in zip(ref_local, local):
            ra = math.hypot(*a)
            if ra > 2.0:
                if abs(ra - math.hypot(*b)) > cls.EPS:
                    return None
                deg = math.degrees(math.atan2(b[1], b[0]) - math.atan2(a[1], a[0]))
                break
        rad = math.radians(deg)
        c, s = math.cos(rad), math.sin(rad)
        for a, b in zip(ref_local, local):
            rx, ry = a[0] * c - a[1] * s, a[0] * s + a[1] * c
            if math.hypot(rx - b[0], ry - b[1]) > cls.EPS:
                return None
        return centroid, deg


def descend_wrappers(body: str) -> "tuple[str, str, List[str]]":
    """Unwrap sole-child transform-only groups around a frame body.

    Post-crop semantic recorders arrive as nested wrapper groups (crop
    translate -> composite translate -> scale -> ...) around the actual
    geometry, whose coordinates live in the stable pre-downsample space that
    IS comparable across frames. Returns ``(prefix, suffix, elements)`` where
    ``prefix + "".join(elements) + suffix`` reproduces the body and
    ``elements`` are the innermost children, ready for part matching.
    """
    import xml.etree.ElementTree as ET

    prefix, suffix = "", ""
    while True:
        elems = split_elements(body)
        if len(elems) != 1:
            return prefix, suffix, elems
        try:
            node = ET.fromstring(elems[0])
        except ET.ParseError:
            return prefix, suffix, elems
        tag = node.tag.rsplit("}", 1)[-1]
        attrs = set(node.attrib)
        if tag != "g" or not attrs <= {"transform"}:
            return prefix, suffix, elems
        t = node.attrib.get("transform", "")
        open_tag = f'<g transform="{t}">' if t else "<g>"
        prefix += open_tag
        suffix = "</g>" + suffix
        body = "".join(
            ET.tostring(child, encoding="unicode") for child in node
        )


def discover_parts(frames: Dict[Any, Any]) -> "tuple[dict, dict]":
    """Match rigid units across frames; register them once as parts.

    Two passes. PASS A walks every frame's element tree collecting candidate
    subtrees (labelled groups and bare leaves) with a coordinate-stripped
    signature and an ordered point cloud. Candidates cluster by signature +
    rigid congruence. PASS B rebuilds each frame top-down: a subtree whose
    congruence class recurs (>= 2 members) becomes a registered part placed by
    ``<use>``; a group that is NOT rigid across frames (an articulated arm)
    descends into its children — so the gallery ends up holding the MAXIMAL
    rigid assemblies (a thruster, an upper arm), not geometric confetti and
    not whole frames.
    """
    import xml.etree.ElementTree as ET

    LABEL_ATTR = f"{{{INK_NS}}}label"
    SHAPE_TAGS = {"polygon", "polyline", "ellipse"}

    def _tag(node) -> str:
        return node.tag.rsplit("}", 1)[-1]

    def _cloud_and_sig(node):
        cloud: List[Point] = []
        sig_parts: List[str] = []

        def walk(el) -> bool:
            t = _tag(el)
            if t == "g":
                sig_parts.append("g")
                for child in el:
                    if not walk(child):
                        return False
                sig_parts.append("/g")
                return True
            if t in ("polygon", "polyline"):
                raw = ET.tostring(el, encoding="unicode")
                pts = _parse_points(raw)
                if pts is None:
                    return False
                cloud.extend(pts)
                sig_parts.append(_style_key(raw))
                return True
            if t == "ellipse":
                try:
                    cx, cy = float(el.get("cx")), float(el.get("cy"))
                    rx = float(el.get("rx"))
                except (TypeError, ValueError):
                    return False
                cloud.append((cx, cy))
                cloud.append((cx + rx, cy))
                attrs = {k: v for k, v in el.attrib.items() if k not in ("cx", "cy")}
                sig_parts.append("ellipse" + repr(sorted(attrs.items())))
                return True
            return False

        ok = walk(node)
        if not ok or len(cloud) < 3:
            return None, ""
        return cloud, "|".join(sig_parts)

    def _localize(node, dx: float, dy: float) -> str:
        node = ET.fromstring(ET.tostring(node, encoding="unicode"))

        def shift(el) -> None:
            t = _tag(el)
            if t in ("polygon", "polyline"):
                pts = _parse_points(ET.tostring(el, encoding="unicode")) or []
                el.set("points", _emit_points([(x + dx, y + dy) for x, y in pts]))
            elif t == "ellipse":
                el.set("cx", _fmt(float(el.get("cx")) + dx))
                el.set("cy", _fmt(float(el.get("cy")) + dy))
            for child in el:
                shift(child)

        shift(node)
        return ET.tostring(node, encoding="unicode")

    # ---- PASS A: collect candidates at every level -------------------------
    frame_trees: Dict[Any, "tuple[str, str, list]"] = {}
    classes: Dict[str, dict] = {}  # sig -> {"ref": cloud, "count": int}

    def collect(node) -> None:
        cloud, sig = _cloud_and_sig(node)
        if cloud is not None:
            cls = classes.setdefault(sig, {"ref": cloud, "count": 0})
            if _Congruence.match(
                    _Congruence.canonical(cls["ref"])[1], cloud) is not None:
                cls["count"] += 1
        if _tag(node) == "g":
            for child in node:
                collect(child)

    for key in sorted(frames, key=repr):
        raw = frames[key]
        if isinstance(raw, list):
            prefix, suffix, elems = "", "", raw
        else:
            prefix, suffix, elems = descend_wrappers(raw)
        trees = []
        for e in elems:
            try:
                trees.append(ET.fromstring(e))
            except ET.ParseError:
                trees.append(e)  # unparseable (uses with prefixes): verbatim
        frame_trees[key] = (prefix, suffix, trees)
        for t in trees:
            if not isinstance(t, str):
                collect(t)

    # ---- PASS B: rebuild, placing parts at the largest recurring level -----
    part_defs: Dict[str, Tuple[str, str]] = {}
    registered: Dict[str, str] = {}  # sig -> pid
    serial = 0

    def rebuild(node) -> str:
        nonlocal serial
        if isinstance(node, str):
            return node
        cloud, sig = _cloud_and_sig(node)
        cls = classes.get(sig) if cloud is not None else None
        if cls is not None and cls["count"] >= 2:
            local_ref = _Congruence.canonical(cls["ref"])[1]
            m = _Congruence.match(local_ref, cloud)
            if m is not None:
                (ox, oy), deg = m
                pid = registered.get(sig)
                if pid is None:
                    pid = f"part_{serial:03d}"
                    serial += 1
                    registered[sig] = pid
                    name = node.get(LABEL_ATTR) or _tag(node)
                    body = _localize(node, -ox, -oy)
                    if abs(deg) > 0.01:
                        # Def must live in the reference orientation: this
                        # occurrence is rotated by ``deg`` relative to it.
                        body = f'<g transform="rotate({_fmt(-deg)})">{body}</g>'
                    part_defs[pid] = (name, body)
                t = f"translate({_fmt(ox)} {_fmt(oy)})"
                if abs(deg) > 0.01:
                    t += f" rotate({_fmt(deg)})"
                return f'<use href="#{pid}" xlink:href="#{pid}" transform="{t}"/>'
        if _tag(node) == "g":
            inner = "".join(rebuild(child) for child in node)
            attrs = "".join(
                f' {k.replace("{" + INK_NS + "}", "inkscape:")}="{v}"'
                for k, v in node.attrib.items())
            return f"<g{attrs}>{inner}</g>"
        return ET.tostring(node, encoding="unicode")

    frame_bodies: Dict[Any, str] = {}
    for key, (prefix, suffix, trees) in frame_trees.items():
        frame_bodies[key] = prefix + "".join(rebuild(t) for t in trees) + suffix
    return part_defs, frame_bodies


class _TeeDraw:
    """Forwards every call to the real ImageDraw AND a DrawRecorder."""

    def __init__(self, real: Any, rec: DrawRecorder) -> None:
        self._real = real
        self._rec = rec

    def __getattr__(self, name: str) -> Any:
        rec_fn = getattr(self._rec, name, None)
        try:
            real_attr = getattr(self._real, name)
        except AttributeError:
            # Recorder-only surface (component()/part() scoping): forward so
            # semantic grouping reaches the recording even through the tee.
            if rec_fn is not None:
                return rec_fn
            raise
        if not callable(real_attr) or rec_fn is None:
            return real_attr

        def tee(*args: Any, **kwargs: Any) -> Any:
            try:
                rec_fn(*args, **kwargs)
            except Exception:
                self._rec.unsupported.add(name)
            return real_attr(*args, **kwargs)

        return tee


def capture_target_frames(target):
    """Render ``target`` normally while capturing vector recordings.

    Returns ``(published_files, semantic_frames, diagnostic_recorders)``:

    * ``published_files``: relpath -> bytes of the real render (untouched);
    * ``semantic_frames``: {(sheet_target, anim, frame_idx) -> DrawRecorder}
      associated at the ``sheet_build`` frame-publication seam — the recorder
      is in FINAL frame coordinates because crop/resize/composite chains are
      propagated. Empty for renderers that bypass ``build_sheet``.
    * ``diagnostic_recorders``: creation-ordered leftovers for renderers with
      no semantic seam — diagnostic only, never proof of association.

    Pillow ops with no vector meaning (paste with mask, rotate, transpose,
    unpropagated filters, source-cropped composites) mark the affected
    recorder's ``unsupported`` set; callers must downgrade accordingly.
    """
    import tempfile
    import shutil
    from pathlib import Path
    from unittest import mock

    from PIL import Image, ImageDraw

    from . import sheet_build

    import weakref

    recorders: Dict[int, DrawRecorder] = {}
    order: List[int] = []
    consumed: set = set()
    semantic: Dict[Any, DrawRecorder] = {}
    real_draw = ImageDraw.Draw
    real_composite = Image.Image.alpha_composite
    real_mod_composite = Image.alpha_composite
    real_filter = Image.Image.filter
    real_crop = Image.Image.crop
    real_resize = Image.Image.resize
    real_paste = Image.Image.paste
    real_rotate = Image.Image.rotate
    real_transpose = Image.Image.transpose

    def _adopt(img, rec):
        # No strong image refs (a roster run OOMs otherwise). A finalizer
        # retires the recorder entry when the image dies, so a recycled id
        # can never resurrect another image's recording.
        key = id(img)
        recorders[key] = rec
        order.append(key)
        weakref.finalize(img, recorders.pop, key, None)

    def _derive(src_img, res, wrap, op_name=None):
        """Propagate src_img's recording onto derived image ``res``."""
        src_rec = recorders.get(id(src_img))
        if src_rec is None or not src_rec.calls:
            return
        rec = DrawRecorder(res.size)
        rec._emit(wrap(src_rec.snapshot_svg()))
        rec.calls = src_rec.calls
        rec.unsupported |= src_rec.unsupported
        if op_name:
            rec.unsupported.add(op_name)
        for pid, v in src_rec.part_defs.items():
            rec.part_defs.setdefault(pid, v)
        _adopt(res, rec)
        consumed.add(id(src_img))

    def hooked_draw(img, mode=None):
        real = real_draw(img, mode) if mode else real_draw(img)
        if id(img) not in recorders:
            _adopt(img, DrawRecorder(img.size))
        return _TeeDraw(real, recorders[id(img)])

    def _embed(img) -> str:
        """A positioned data-URI <image> for content with no vector source.

        Per the migration plan, per-pixel/algorithmic layers (and text) remain
        embedded raster components rather than blocking conversion — the scene
        stays visually faithful; the embedded part just is not node-editable.
        """
        import base64
        import io as _io

        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return (f'<image x="0" y="0" width="{img.width}" height="{img.height}" '
                f'href="data:image/png;base64,{b64}" '
                f'xlink:href="data:image/png;base64,{b64}"/>')

    def _fold(dest, src, dest_pos, bad=None):
        src_rec = recorders.get(id(src))
        if (src_rec is None or not src_rec.calls) and src.mode == "RGBA" \
                and src.getchannel("A").getbbox() is not None:
            # Real pixels with no vector recording: embed the layer itself.
            dst_rec = recorders.get(id(dest))
            if dst_rec is None:
                dst_rec = DrawRecorder(dest.size)
                _adopt(dest, dst_rec)
            dx, dy = dest_pos
            dst_rec._emit(
                f'<g transform="translate({_fmt(dx)} {_fmt(dy)})">'
                f"{_embed(src)}</g>")
            dst_rec.calls += 1
            dst_rec.unsupported.add("raster-embed")
            return
        if src_rec is None or not src_rec.calls:
            return
        dst_rec = recorders.get(id(dest))
        if dst_rec is None:
            dst_rec = DrawRecorder(dest.size)
            _adopt(dest, dst_rec)
        dx, dy = dest_pos
        dst_rec._emit(
            f'<g transform="translate({_fmt(dx)} {_fmt(dy)})">'
            f"{src_rec.snapshot_svg()}</g>")
        dst_rec.calls += src_rec.calls
        dst_rec.unsupported |= src_rec.unsupported
        if bad:
            dst_rec.unsupported.add(bad)
        for pid, v in src_rec.part_defs.items():
            dst_rec.part_defs.setdefault(pid, v)
        consumed.add(id(src))

    in_composite = [0]

    def hooked_composite(dest, src, dest_pos=(0, 0), source=(0, 0)):
        _fold(dest, src, dest_pos,
              bad=None if tuple(source) == (0, 0) else "composite-source-crop")
        # Pillow implements alpha_composite via an internal self.paste();
        # guard so that internal call is not misflagged as a raster paste.
        in_composite[0] += 1
        try:
            return real_composite(dest, src, dest_pos, source)
        finally:
            in_composite[0] -= 1

    def hooked_mod_composite(im1, im2):
        res = real_mod_composite(im1, im2)
        r1, r2 = recorders.get(id(im1)), recorders.get(id(im2))
        if (r1 and r1.calls) or (r2 and r2.calls):
            rec = DrawRecorder(res.size)
            for r, img in ((r1, im1), (r2, im2)):
                if r and r.calls:
                    rec._emit(r.snapshot_svg())
                    rec.calls += r.calls
                    rec.unsupported |= r.unsupported
                    for pid, v in r.part_defs.items():
                        rec.part_defs.setdefault(pid, v)
                    consumed.add(id(img))
            _adopt(res, rec)
        return res

    blur_serial = [0]

    def hooked_filter(img, flt):
        res = real_filter(img, flt)
        src_rec = recorders.get(id(img))
        if src_rec is not None and src_rec.calls:
            radius = getattr(flt, "radius", None)
            if type(flt).__name__ == "GaussianBlur" and radius:
                fid = f"acblur{blur_serial[0]}"
                blur_serial[0] += 1
                _derive(img, res, lambda body: (
                    f'<defs><filter id="{fid}" x="-50%" y="-50%" width="200%" '
                    f'height="200%"><feGaussianBlur stdDeviation="{_fmt(float(radius))}"/>'
                    f'</filter></defs><g filter="url(#{fid})">{body}</g>'))
            else:
                _derive(img, res, lambda body: body,
                        op_name=f"filter:{type(flt).__name__}")
        return res

    def hooked_crop(img, box=None):
        res = real_crop(img, box)
        if box is not None:
            x0, y0 = box[0], box[1]
            _derive(img, res,
                    lambda body: f'<g transform="translate({_fmt(-x0)} {_fmt(-y0)})">{body}</g>')
        return res

    def hooked_resize(img, size, *args, **kwargs):
        res = real_resize(img, size, *args, **kwargs)
        if img.width and img.height:
            sx, sy = size[0] / img.width, size[1] / img.height
            _derive(img, res,
                    lambda body: f'<g transform="scale({sx:.6f} {sy:.6f})">{body}</g>')
        return res

    def hooked_paste(img, im, box=None, mask=None):
        if in_composite[0]:
            return real_paste(img, im, box, mask)
        rec = recorders.get(id(img))
        src_rec = recorders.get(id(im)) if not isinstance(im, (int, tuple)) else None
        if (rec and rec.calls) or (src_rec and src_rec.calls):
            if rec is None:
                rec = DrawRecorder(img.size)
                _adopt(img, rec)
            rec.unsupported.add("paste")
        return real_paste(img, im, box, mask)

    def hooked_rotate(img, angle, resample=0, expand=False, center=None,
                      translate=None, fillcolor=None):
        res = real_rotate(img, angle, resample, expand, center, translate,
                          fillcolor)
        # PIL rotates counterclockwise in a y-down raster; SVG rotate() is
        # clockwise there, hence -angle. With expand (and default center) PIL
        # re-centers the enlarged canvas on the original image centre.
        if fillcolor is not None or (expand and center is not None):
            _derive(img, res, lambda body: body, op_name="rotate")
            return res
        cx, cy = center if center is not None else (img.width / 2.0,
                                                    img.height / 2.0)
        dx, dy = translate if translate is not None else (0, 0)
        if expand:
            dx += res.width / 2.0 - cx
            dy += res.height / 2.0 - cy
        t = ""
        if dx or dy:
            t += f"translate({_fmt(dx)} {_fmt(dy)}) "
        t += f"rotate({_fmt(-angle)} {_fmt(cx)} {_fmt(cy)})"
        _derive(img, res, lambda body: f'<g transform="{t}">{body}</g>')
        return res

    def hooked_transpose(img, method):
        res = real_transpose(img, method)
        _derive(img, res, lambda body: body, op_name="transpose")
        return res

    def frame_hook(sheet_target, anim, frame_idx, frame_img):
        rec = recorders.get(id(frame_img))
        if rec is None:
            # No vector chain reached the published frame: embed its raster so
            # the scene is faithful, flagged as a non-editable component.
            rec = DrawRecorder(frame_img.size)
            rec._emit(_embed(frame_img))
            rec.calls = 1
            rec.unsupported.add("raster-embed")
        semantic[(sheet_target, anim, frame_idx)] = rec
        consumed.add(id(frame_img))

    out = Path(tempfile.mkdtemp(prefix="autocap_"))
    prev_hook = sheet_build.FRAME_CAPTURE_HOOK
    sheet_build.FRAME_CAPTURE_HOOK = frame_hook
    try:
        with mock.patch.object(ImageDraw, "Draw", hooked_draw), \
             mock.patch.object(Image.Image, "alpha_composite", hooked_composite), \
             mock.patch.object(Image, "alpha_composite", hooked_mod_composite), \
             mock.patch.object(Image.Image, "filter", hooked_filter), \
             mock.patch.object(Image.Image, "crop", hooked_crop), \
             mock.patch.object(Image.Image, "resize", hooked_resize), \
             mock.patch.object(Image.Image, "paste", hooked_paste), \
             mock.patch.object(Image.Image, "rotate", hooked_rotate), \
             mock.patch.object(Image.Image, "transpose", hooked_transpose):
            target.render_sheet(out)
        files: Dict[str, bytes] = {}
        for f in sorted(out.rglob("*")):
            if f.is_file():
                files[str(f.relative_to(out))] = f.read_bytes()
    finally:
        sheet_build.FRAME_CAPTURE_HOOK = prev_hook
        shutil.rmtree(out, ignore_errors=True)

    diagnostics = {}
    for i, key in enumerate(order):
        rec = recorders.get(key)  # finalizers retire dead images' entries
        if rec is not None and rec.calls and key not in consumed:
            diagnostics[i] = rec
    return files, semantic, diagnostics
