#!/usr/bin/env python3
"""Reusable SVG geometry utilities for transform- and <use>-aware validation.

The module intentionally stays dependency-light (lxml only) and focuses on the
subset needed by authored sprite SVGs: affine transform composition, inverse
matrices, resolving local <use> references, and collecting path geometry in a
common coordinate frame.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable

from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"
XLINK_HREF = f"{{{XLINK_NS}}}href"
INK_LABEL = f"{{{INK_NS}}}label"

_TRANSFORM_RE = re.compile(r"([A-Za-z]+)\s*\(([^)]*)\)")
_NUMBER_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")

Matrix = tuple[float, float, float, float, float, float]  # SVG a,b,c,d,e,f


def identity() -> Matrix:
    return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def multiply(left: Matrix, right: Matrix) -> Matrix:
    a1,b1,c1,d1,e1,f1 = left
    a2,b2,c2,d2,e2,f2 = right
    return (
        a1*a2 + c1*b2,
        b1*a2 + d1*b2,
        a1*c2 + c1*d2,
        b1*c2 + d1*d2,
        a1*e2 + c1*f2 + e1,
        b1*e2 + d1*f2 + f1,
    )


def inverse(m: Matrix) -> Matrix:
    a,b,c,d,e,f = m
    det = a*d - b*c
    if abs(det) < 1e-12:
        raise ValueError(f"singular SVG matrix: {m}")
    return (
        d/det,
        -b/det,
        -c/det,
        a/det,
        (c*f - d*e)/det,
        (b*e - a*f)/det,
    )


def parse_transform(text: str | None) -> Matrix:
    result = identity()
    if not text:
        return result
    for name, raw_args in _TRANSFORM_RE.findall(text):
        args = [float(x) for x in _NUMBER_RE.findall(raw_args)]
        if name == "matrix":
            if len(args) != 6:
                raise ValueError(text)
            m = tuple(args)  # type: ignore[assignment]
        elif name == "translate":
            tx = args[0]
            ty = args[1] if len(args) > 1 else 0.0
            m = (1.0, 0.0, 0.0, 1.0, tx, ty)
        elif name == "scale":
            sx = args[0]
            sy = args[1] if len(args) > 1 else sx
            m = (sx, 0.0, 0.0, sy, 0.0, 0.0)
        elif name == "rotate":
            radians = math.radians(args[0])
            co = math.cos(radians)
            si = math.sin(radians)
            r = (co, si, -si, co, 0.0, 0.0)
            if len(args) == 3:
                cx, cy = args[1], args[2]
                m = multiply(multiply((1,0,0,1,cx,cy), r), (1,0,0,1,-cx,-cy))
            else:
                m = r
        elif name == "skewX":
            m = (1.0, 0.0, math.tan(math.radians(args[0])), 1.0, 0.0, 0.0)
        elif name == "skewY":
            m = (1.0, math.tan(math.radians(args[0])), 0.0, 1.0, 0.0, 0.0)
        else:
            raise ValueError(f"unsupported SVG transform {name!r}: {text}")
        result = multiply(result, m)
    return result


def matrix_text(m: Matrix, digits: int = 10) -> str:
    vals=[]
    for v in m:
        if abs(v) < 10**(-digits):
            v=0.0
        vals.append(f"{v:.{digits}f}".rstrip("0").rstrip(".") or "0")
    return "matrix(" + ",".join(vals) + ")"


def max_matrix_delta(a: Matrix, b: Matrix) -> float:
    return max(abs(x-y) for x,y in zip(a,b))


def element_by_id(root, id_: str):
    found = root.xpath(f'//*[@id="{id_}"]')
    if not found:
        raise KeyError(id_)
    return found[0]


def local_href(elem) -> str | None:
    return elem.get("href") or elem.get(XLINK_HREF)


@dataclass(frozen=True)
class PathGeometry:
    label: str
    d: str
    transform: Matrix


def collect_paths(root, element_id: str) -> list[PathGeometry]:
    """Collect all path geometry below element_id, resolving local <use> clones.

    Transforms are expressed in the selected element's parent coordinate system,
    including the selected element's own transform. This makes two independently
    structured subtrees directly comparable when they should render the same
    local geometry.
    """
    start = element_by_id(root, element_id)
    id_map = {e.get("id"): e for e in root.iter() if e.get("id")}
    out: list[PathGeometry] = []

    def walk(elem, parent_matrix: Matrix, stack: tuple[str, ...]) -> None:
        here = multiply(parent_matrix, parse_transform(elem.get("transform")))
        tag = etree.QName(elem).localname
        if tag == "use":
            href = local_href(elem)
            if href and href.startswith("#"):
                target_id = href[1:]
                if target_id in stack:
                    raise ValueError(f"cyclic <use> reference: {stack + (target_id,)}")
                target = id_map.get(target_id)
                if target is None:
                    raise KeyError(f"unresolved <use>: {href}")
                walk(target, here, stack + (target_id,))
            return
        if tag == "path":
            out.append(PathGeometry(
                label=elem.get(INK_LABEL) or elem.get("id") or "path",
                d=elem.get("d") or "",
                transform=here,
            ))
            return
        for child in elem:
            if isinstance(child.tag, str):
                walk(child, here, stack)

    walk(start, identity(), (element_id,))
    return out


def compare_path_geometry(left: Iterable[PathGeometry], right: Iterable[PathGeometry]) -> tuple[bool, list[str]]:
    l=list(left); r=list(right)
    messages=[]
    if len(l) != len(r):
        messages.append(f"path count differs: {len(l)} != {len(r)}")
        return False, messages
    ok=True
    for idx,(a,b) in enumerate(zip(l,r)):
        if a.label != b.label:
            ok=False; messages.append(f"[{idx}] label differs: {a.label!r} != {b.label!r}")
        if a.d != b.d:
            ok=False; messages.append(f"[{idx}] path data differs for {a.label!r}")
        delta=max_matrix_delta(a.transform,b.transform)
        if delta > 1e-8:
            ok=False; messages.append(f"[{idx}] transform delta for {a.label!r}: {delta:.3g}")
    return ok,messages
