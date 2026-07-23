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


def discover_parts(frames: Dict[Any, List[str]]) -> "tuple[dict, dict]":
    """Match congruent elements across frames; register them as parts.

    ``frames``: key -> list of element strings (z-order). Returns
    ``(part_defs, frame_bodies)`` in ComponentScene shape: parts hold
    centroid-local geometry; matched occurrences become ``<use>`` with the
    recovered transform; unmatched elements stay inline.
    """
    registry: List[Tuple[str, List[Point], str, str]] = []  # (style, local, pid, body)
    part_defs: Dict[str, Tuple[str, str]] = {}
    frame_bodies: Dict[Any, str] = {}
    serial = 0

    for key in sorted(frames, key=repr):
        out: List[str] = []
        for elem in frames[key]:
            pts = _parse_points(elem)
            if pts is None or len(pts) < 3:
                out.append(elem)  # ellipses/short lines: inline (cheap, exact)
                continue
            style = _style_key(elem)
            placed = False
            for rstyle, rlocal, pid, _body in registry:
                if rstyle != style:
                    continue
                m = _Congruence.match(rlocal, pts)
                if m is not None:
                    (ox, oy), deg = m
                    t = f"translate({_fmt(ox)} {_fmt(oy)})"
                    if abs(deg) > 0.01:
                        t += f" rotate({_fmt(deg)})"
                    out.append(f'<use href="#{pid}" xlink:href="#{pid}" transform="{t}"/>')
                    placed = True
                    break
            if not placed:
                centroid, local = _Congruence.canonical(pts)
                pid = f"part_auto{serial:03d}"
                serial += 1
                body = _POINTS_RE.sub(f'points="{_emit_points(local)}"', elem, count=1)
                registry.append((style, local, pid, body))
                part_defs[pid] = (f"auto{serial - 1:03d}", body)
                (ox, oy) = centroid
                out.append(f'<use href="#{pid}" xlink:href="#{pid}" '
                           f'transform="translate({_fmt(ox)} {_fmt(oy)})"/>')
        frame_bodies[key] = "".join(out)

    # Parts used only once carry no reuse value — inline them back.
    all_bodies = "".join(frame_bodies.values())
    for pid in list(part_defs):
        if all_bodies.count(f'#{pid}"') <= 2:  # href + xlink:href of ONE use
            name, body = part_defs.pop(pid)
            for key, fb in frame_bodies.items():
                pattern = re.compile(
                    rf'<use href="#{pid}" xlink:href="#{pid}" '
                    rf'transform="translate\(([-\d.]+) ([-\d.]+)\)( rotate\(([-\d.]+)\))?"/>')

                def _inline(m: "re.Match[str]") -> str:
                    t = f'translate({m.group(1)} {m.group(2)})'
                    if m.group(4):
                        t += f' rotate({m.group(4)})'
                    return f'<g transform="{t}">{body}</g>'

                frame_bodies[key] = pattern.sub(_inline, fb)
    return part_defs, frame_bodies


class _TeeDraw:
    """Forwards every call to the real ImageDraw AND a DrawRecorder."""

    def __init__(self, real: Any, rec: DrawRecorder) -> None:
        self._real = real
        self._rec = rec

    def __getattr__(self, name: str) -> Any:
        real_attr = getattr(self._real, name)
        rec_fn = getattr(self._rec, name, None)
        if not callable(real_attr) or rec_fn is None:
            return real_attr

        def tee(*args: Any, **kwargs: Any) -> Any:
            try:
                rec_fn(*args, **kwargs)
            except Exception:
                self._rec.unsupported.add(name)
            return real_attr(*args, **kwargs)

        return tee


def capture_target_frames(target) -> "tuple[dict, dict, set]":
    """Render ``target`` normally while capturing vector recorders per frame.

    Returns ``(published_files, recorders_by_image_order, unsupported_ops)``.
    ``published_files``: relpath -> bytes of the real render (untouched).
    Recorders keyed by creation order; mapping to manifest frames and fidelity
    verification are the caller's job (see the harness coverage command).
    """
    import tempfile
    from pathlib import Path
    from unittest import mock

    from PIL import Image, ImageDraw

    recorders: Dict[int, DrawRecorder] = {}
    images: Dict[int, Any] = {}
    order: List[int] = []
    consumed: set = set()  # scratch layers folded into a destination
    real_draw = ImageDraw.Draw
    real_composite = Image.Image.alpha_composite
    real_filter = Image.Image.filter

    def hooked_draw(img, mode=None):
        real = real_draw(img, mode) if mode else real_draw(img)
        key = id(img)
        if key not in recorders:
            recorders[key] = DrawRecorder(img.size)
            images[key] = img
            order.append(key)
        return _TeeDraw(real, recorders[key])

    def hooked_composite(dest, src, dest_pos=(0, 0), source=(0, 0)):
        # Fold a recorded scratch layer into its destination's recording.
        src_rec = recorders.get(id(src))
        dst_rec = recorders.get(id(dest))
        if src_rec is not None and src_rec.calls and dst_rec is None:
            recorders[id(dest)] = dst_rec = DrawRecorder(dest.size)
            images[id(dest)] = dest
            order.append(id(dest))
        if src_rec is not None and src_rec.calls and dst_rec is not None:
            dx, dy = dest_pos
            dst_rec._emit(
                f'<g transform="translate({_fmt(dx)} {_fmt(dy)})">'
                f"{src_rec.body_svg()}</g>")
            dst_rec.calls += src_rec.calls
            dst_rec.unsupported |= src_rec.unsupported
            consumed.add(id(src))
        return real_composite(dest, src, dest_pos, source)

    blur_serial = [0]

    def hooked_filter(img, flt):
        res = real_filter(img, flt)
        src_rec = recorders.get(id(img))
        if src_rec is not None and src_rec.calls:
            rec = DrawRecorder(res.size)
            radius = getattr(flt, "radius", None)
            if type(flt).__name__ == "GaussianBlur" and radius:
                # SVG-native blur: wrap the recorded geometry in a filter.
                fid = f"acblur{blur_serial[0]}"
                blur_serial[0] += 1
                rec._emit(
                    f'<defs><filter id="{fid}" x="-50%" y="-50%" width="200%" '
                    f'height="200%"><feGaussianBlur stdDeviation="{_fmt(float(radius))}"/>'
                    f'</filter></defs>'
                    f'<g filter="url(#{fid})">{src_rec.body_svg()}</g>')
            else:
                rec._emit(src_rec.body_svg())
                rec.unsupported.add(f"filter:{type(flt).__name__}")
            rec.calls = src_rec.calls
            rec.unsupported |= src_rec.unsupported
            recorders[id(res)] = rec
            images[id(res)] = res
            order.append(id(res))
            consumed.add(id(img))
        return res

    out = Path(tempfile.mkdtemp(prefix="autocap_"))
    with mock.patch.object(ImageDraw, "Draw", hooked_draw), \
         mock.patch.object(Image.Image, "alpha_composite", hooked_composite), \
         mock.patch.object(Image.Image, "filter", hooked_filter):
        target.render_sheet(out)

    files: Dict[str, bytes] = {}
    for f in sorted(out.rglob("*")):
        if f.is_file():
            files[str(f.relative_to(out))] = f.read_bytes()

    ordered = {}
    for i, key in enumerate(order):
        rec = recorders[key]
        if rec.calls and key not in consumed:
            ordered[i] = rec
    return files, ordered, set()
