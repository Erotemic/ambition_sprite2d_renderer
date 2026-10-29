"""Hand-drawn 2D art over the parts of a generated character.

The 3D figure places; the 2D art draws. A spec names an overlay
(``spec.overlay``): one SVG file, ``data/overlays/<name>.overlay.svg``,
with one cell per view key. A cell holds groups, and each group draws on
one rig part of that view::

    <svg data-overlay-ref="height:188 head:29.1 trunk:56.6 leg:91.7">
      <g data-view="front">
        <g data-overlay-part="head" data-overlay-mode="replace"
           data-overlay-anchor="neck" data-overlay-scale="head head"
           transform="translate(160,180.9)">
          <path d="..." fill="..."/>
        </g>
      </g>
    </svg>

* ``data-overlay-part``: the rig part (``drawkit.Part.name``) in that view.
* ``data-overlay-mode``: ``replace`` (the art is the part's whole drawing;
  a group with no paths removes the part) or ``over`` (a new part on the
  same bone, painted just above the part).
* ``data-overlay-anchor``: a joint of the view (``draw.view_joints``: the
  ``neck`` is the head's pivot, the ``waist`` the torso's, a ``*_grip`` a
  hand's, a ``*_hip`` a coat skirt's). The group's paths are drawn in SVG
  units with that joint at (0, 0).
* ``data-overlay-scale``: the measures of the figure (``MEASURES``) that
  the art follows across and down. The file's ``data-overlay-ref`` holds
  each measure of the figure the art was drawn on, so the art grows and
  shrinks with the body (a taller character, a longer trunk).

A group's own ``transform`` only places it for an author in an editor; the
drawing ignores it. A path's ``transform`` (``translate``, ``scale``,
``rotate``, ``matrix``) applies. Paths may use any command but arcs.
A left view is the mirror of its right twin, like the rest of the drawing.
"""

from __future__ import annotations

import functools
import math
import re
from dataclasses import replace
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Sequence, Tuple
from xml.etree import ElementTree as ET

from .body import Figure
from .drawkit import Part
from .geometry import Point, View
from .svgout import Canvas, El

OVERLAYS = Path(__file__).resolve().parents[1] / "data" / "overlays"
SUFFIX = ".overlay.svg"
MODES = ("replace", "over")
SVG_NS = "{http://www.w3.org/2000/svg}"

#: The measures an overlay can follow, in cm, from the figure.
MEASURES: Dict[str, Callable[[Figure], float]] = {
    "height": lambda f: f.H,
    "head": lambda f: f.hh,
    "trunk": lambda f: f.T,
    "leg": lambda f: f.sole_y - f.y_hip,
}

Matrix = Tuple[float, float, float, float, float, float]
IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def available() -> List[str]:
    """The names of the overlay files."""
    return sorted(p.name[: -len(SUFFIX)] for p in OVERLAYS.glob(f"*{SUFFIX}"))


def path_of(name: str) -> Path:
    return OVERLAYS / f"{name}{SUFFIX}"


# ---- the file ------------------------------------------------------------------------------------


class Group:
    """One group of a cell: the art of one part in one view."""

    def __init__(self, part: str, mode: str, anchor: str, scale: Tuple[str, str], els: List[Tuple[List, dict]]) -> None:
        self.part, self.mode, self.anchor, self.scale, self.els = part, mode, anchor, scale, els


class Overlay:
    def __init__(self, name: str, ref: Dict[str, float], cells: Dict[str, List[Group]]) -> None:
        self.name, self.ref, self.cells = name, ref, cells


@functools.lru_cache(maxsize=None)
def _load_cached(path: str, mtime: float) -> Overlay:
    return parse(Path(path).read_text(encoding="utf8"), Path(path).name[: -len(SUFFIX)])


def load(name: str) -> Overlay:
    p = path_of(name)
    if not p.exists():
        raise ValueError(f"no overlay {name!r}: {p} does not exist (overlays: {available()})")
    return _load_cached(str(p), p.stat().st_mtime)


def parse(text: str, name: str = "overlay") -> Overlay:
    root = ET.fromstring(text)
    ref: Dict[str, float] = {}
    for item in root.attrib.get("data-overlay-ref", "").split():
        key, _, value = item.partition(":")
        if key not in MEASURES:
            raise ValueError(f"overlay {name}: data-overlay-ref names {key!r}, not one of {sorted(MEASURES)}")
        ref[key] = float(value)
    cells: Dict[str, List[Group]] = {}
    for cell in root.iter(f"{SVG_NS}g"):
        view = cell.attrib.get("data-view")
        if view is None:
            continue
        if view in cells:
            raise ValueError(f"overlay {name}: two cells for the view {view!r}")
        groups = []
        for g in cell:
            part = g.attrib.get("data-overlay-part")
            if part is None:
                continue
            where = f"overlay {name}, view {view}, part {part}"
            mode = g.attrib.get("data-overlay-mode", "replace")
            if mode not in MODES:
                raise ValueError(f"{where}: mode {mode!r} is not one of {MODES}")
            anchor = g.attrib.get("data-overlay-anchor")
            if not anchor:
                raise ValueError(f"{where}: no data-overlay-anchor")
            scale = tuple(g.attrib.get("data-overlay-scale", "height height").split())
            if len(scale) != 2 or any(s not in MEASURES or s not in ref for s in scale):
                raise ValueError(f"{where}: data-overlay-scale {scale!r} must name two measures of data-overlay-ref {sorted(ref)}")
            els = []
            for el in g.iter():
                if el is g:
                    continue
                if el.tag != f"{SVG_NS}path":
                    if el.tag == f"{SVG_NS}g":
                        raise ValueError(f"{where}: a group in a part group; keep the paths flat")
                    raise ValueError(f"{where}: <{el.tag.replace(SVG_NS, '')}> is not a path")
                segs = parse_d(el.attrib["d"], where)
                m = parse_transform(el.attrib.get("transform", ""), where)
                els.append((transform_segments(segs, m), _paint(el), math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))))
            groups.append(Group(part, mode, anchor, scale, els))  # type: ignore[arg-type]
        cells[view] = groups
    return Overlay(name, ref, cells)


def _paint(el: ET.Element) -> dict:
    attrs = dict(el.attrib)
    for item in attrs.pop("style", "").split(";"):
        key, _, value = item.partition(":")
        if key.strip():
            attrs[key.strip()] = value.strip()
    opacity = float(attrs.get("opacity", 1.0)) * float(attrs.get("fill-opacity", 1.0))
    return {
        "fill": attrs.get("fill", "#000000"),
        "stroke": attrs.get("stroke", "none"),
        "width": float(attrs.get("stroke-width", 1.0)) if attrs.get("stroke", "none") != "none" else 0.0,
        "cap": attrs.get("stroke-linecap", "round"),
        "opacity": opacity,
    }


# ---- path data -----------------------------------------------------------------------------------

_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtZzAa]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "Z": 0}


def parse_d(d: str, where: str = "") -> List[Tuple[str, List[Point]]]:
    """Path data as absolute segments: ``M``/``L`` (one point), ``C`` (three),
    ``Q`` (two) and ``Z``."""
    toks = _TOKEN.findall(d)
    out: List[Tuple[str, List[Point]]] = []
    i, cmd = 0, ""
    cur: Point = (0.0, 0.0)
    start: Point = (0.0, 0.0)
    last_c: Point | None = None
    last_q: Point | None = None
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "Aa":
                raise ValueError(f"{where}: arcs (A) are not supported; convert them to curves")
            if cmd in "Zz":
                out.append(("Z", []))
                cur, last_c, last_q = start, None, None
                continue
        elif not cmd:
            raise ValueError(f"{where}: path data does not start with a command")
        up, rel = cmd.upper(), cmd.islower()
        n = _ARGS[up]
        args = [float(x) for x in toks[i:i + n]]
        if len(args) < n:
            raise ValueError(f"{where}: {cmd} needs {n} numbers")
        i += n
        ox, oy = cur if rel else (0.0, 0.0)
        if up == "H":
            pts = [(args[0] + ox, cur[1])]
        elif up == "V":
            pts = [(cur[0], args[0] + oy)]
        else:
            pts = [(args[k] + ox, args[k + 1] + oy) for k in range(0, n, 2)]
        if up == "M":
            out.append(("M", pts))
            start = pts[0]
            cmd = "l" if rel else "L"
            last_c = last_q = None
        elif up in "LHV":
            out.append(("L", pts))
            last_c = last_q = None
        elif up == "C":
            out.append(("C", pts))
            last_c, last_q = pts[1], None
        elif up == "S":
            c1 = (2 * cur[0] - last_c[0], 2 * cur[1] - last_c[1]) if last_c else cur
            out.append(("C", [c1] + pts))
            last_c, last_q = pts[0], None
        elif up == "Q":
            out.append(("Q", pts))
            last_q, last_c = pts[0], None
        elif up == "T":
            q1 = (2 * cur[0] - last_q[0], 2 * cur[1] - last_q[1]) if last_q else cur
            out.append(("Q", [q1] + pts))
            last_q, last_c = q1, None
        cur = out[-1][1][-1]
    return out


def parse_transform(text: str, where: str = "") -> Matrix:
    m = IDENTITY
    for fn, args in re.findall(r"(\w+)\s*\(([^)]*)\)", text):
        v = [float(x) for x in re.split(r"[\s,]+", args.strip()) if x]
        if fn == "translate":
            t = (1.0, 0.0, 0.0, 1.0, v[0], v[1] if len(v) > 1 else 0.0)
        elif fn == "scale":
            t = (v[0], 0.0, 0.0, v[1] if len(v) > 1 else v[0], 0.0, 0.0)
        elif fn == "rotate":
            a = math.radians(v[0])
            c, s = math.cos(a), math.sin(a)
            t = (c, s, -s, c, 0.0, 0.0)
            if len(v) == 3:
                t = _mul(_mul((1.0, 0.0, 0.0, 1.0, v[1], v[2]), t), (1.0, 0.0, 0.0, 1.0, -v[1], -v[2]))
        elif fn == "matrix":
            t = tuple(v)  # type: ignore[assignment]
        else:
            raise ValueError(f"{where}: transform {fn}() is not supported")
        m = _mul(m, t)  # type: ignore[arg-type]
    return m


def _mul(a: Matrix, b: Matrix) -> Matrix:
    return (a[0] * b[0] + a[2] * b[1], a[1] * b[0] + a[3] * b[1], a[0] * b[2] + a[2] * b[3], a[1] * b[2] + a[3] * b[3],
            a[0] * b[4] + a[2] * b[5] + a[4], a[1] * b[4] + a[3] * b[5] + a[5])


def transform_segments(segs, m: Matrix):
    if m == IDENTITY:
        return segs
    return [(c, [(m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]) for x, y in pts]) for c, pts in segs]


def _f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def to_d(segs, fn: Callable[[Point], Point]) -> str:
    out = []
    for c, pts in segs:
        out.append(c + " ".join(f"{_f(x)},{_f(y)}" for x, y in map(fn, pts)))
    return " ".join(out)


# ---- drawing -------------------------------------------------------------------------------------


def apply(fig: Figure, view: View, canvas: Canvas, parts: Sequence[Part], joints: Mapping[str, Point]) -> List[Part]:
    """``parts`` with the spec's overlay drawn on them (unchanged without one)."""
    name = getattr(fig.spec, "overlay", "")
    if not name:
        return list(parts)
    ov = load(name)
    groups = ov.cells.get(view.key, [])
    by_name = {p.name: i for i, p in enumerate(parts)}
    out = list(parts)
    for g in groups:
        where = f"overlay {name}, view {view.key}, part {g.part}"
        if g.part not in by_name:
            raise ValueError(f"{where}: the view draws no part {g.part!r}")
        if g.anchor not in joints:
            raise ValueError(f"{where}: no joint {g.anchor!r} (joints: {sorted(joints)})")
        ax, ay = canvas.xy(joints[g.anchor])
        sx = MEASURES[g.scale[0]](fig) / ov.ref[g.scale[0]]
        sy = MEASURES[g.scale[1]](fig) / ov.ref[g.scale[1]]
        sw = math.sqrt(sx * sy)

        def place(p: Point, _ax=ax, _ay=ay, _sx=sx, _sy=sy) -> Point:
            return (_ax + p[0] * _sx, _ay + p[1] * _sy)

        els = [El(to_d(segs, place), fill=paint["fill"], stroke=paint["stroke"], width=paint["width"] * sw * k,
                  cap=paint["cap"], opacity=paint["opacity"]) for segs, paint, k in g.els]
        i = by_name[g.part]
        target = out[i]
        if g.mode == "replace":
            out[i] = replace(target, els=els)
        else:
            out.append(replace(target, name=f"{target.name}__overlay", z=target.z + 0.01, els=els, label=f"{target.label} (overlay)"))
    return out


__all__ = ["MEASURES", "MODES", "OVERLAYS", "Overlay", "apply", "available", "load", "parse", "parse_d", "path_of"]
