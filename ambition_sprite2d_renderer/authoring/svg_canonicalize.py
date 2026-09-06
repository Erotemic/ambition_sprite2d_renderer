"""Canonicalize a hand-authored Inkscape SVG into a small, diff-stable form.

Inkscape files are large and noisy in version control: flat fills are stored as
one-stop ``<linearGradient>`` swatches reached through ``url(#…)`` chains, ``<defs>``
accumulates orphaned gradients/effects, editor window state rides along in
``sodipodi:namedview``, and coordinates carry pointless precision. None of that is
the art. This module rewrites the file so it:

- **shrinks** — solid-swatch gradients are inlined as plain ``fill``/``stroke``
  colours and every unreachable ``<defs>`` entry is vacuumed (reachability from the
  document, transitive through kept defs);
- **stays editable** — every ``inkscape:label`` / ``groupmode`` / id / transform /
  path / used path-effect is preserved, so Inkscape opens it unchanged;
- **diffs cleanly** — output is deterministic and idempotent: whitespace is
  re-indented uniformly, attributes are emitted in a fixed order, volatile editor
  state is dropped, and over-precise numbers are rounded. Running it on its own
  output is a no-op, so the only diffs are real edits.

Intended workflow: edit in Inkscape → ``canonicalize`` → commit. The art is the
single source of truth; this just normalizes its serialization. Genuine multi-stop
gradients are kept verbatim (this is a no-op on art that uses them).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional, Set

from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd"
XLINK_NS = "http://www.w3.org/1999/xlink"

# Editor session attrs on <sodipodi:namedview> that change every save (window
# size, zoom, cursor, active layer) — pure diff noise. Keep only the stable
# document-level handful, matched by LOCAL name (namespace prefix-agnostic).
_NAMEDVIEW_KEEP = {"id", "pagecolor", "bordercolor", "document-units"}

# Attribute emission order: identity first, then geometry, then long values last.
# Anything unlisted sorts alphabetically in the middle band.
_ATTR_FIRST = [
    "id", "{%s}label" % INK_NS, "{%s}groupmode" % INK_NS, "{%s}role" % SODIPODI_NS,
    "x", "y", "width", "height", "cx", "cy", "r", "rx", "ry", "points", "d",
    "transform", "{%s}href" % XLINK_NS, "href",
]
_ATTR_LAST = ["style", "{%s}original-d" % INK_NS, "{%s}path-effect" % INK_NS]

# A number with >= `keep` fractional digits; rounded to `keep`. Leaves ids and
# 6-digit hex colours (no decimal point) untouched.
_NUM = re.compile(r"-?\d+\.\d+")
_REF = re.compile(r"#([A-Za-z_][\w:.\-]*)")

_GRADIENTS = (f"{{{SVG_NS}}}linearGradient", f"{{{SVG_NS}}}radialGradient")


def _local(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


# ---- solid-swatch gradient inlining ------------------------------------------


def _stop_color(style: str, attrib) -> Optional[str]:
    raw = style or ""
    col = re.search(r"stop-color:\s*(#[0-9a-fA-F]{6}|[a-zA-Z]+)", raw)
    color = col.group(1) if col else attrib.get("stop-color")
    if not color:
        return None
    op = re.search(r"stop-opacity:\s*([0-9.]+)", raw)
    if op and float(op.group(1)) < 0.999:
        return color + format(round(float(op.group(1)) * 255), "02x")
    return color


def _solid_colors(root) -> Dict[str, str]:
    """linearGradient id -> single solid colour it resolves to (else absent)."""
    grads = {g.get("id"): g for tag in _GRADIENTS for g in root.iter(tag) if g.get("id")}

    def resolve(gid: str, seen=()) -> Optional[str]:
        g = grads.get(gid)
        if g is None or gid in seen:
            return None
        cols = [c for st in g.iter(f"{{{SVG_NS}}}stop")
                if (c := _stop_color(st.get("style", ""), st.attrib)) is not None]
        if cols:
            return cols[0] if len(set(cols)) == 1 else None
        href = g.get(f"{{{XLINK_NS}}}href") or g.get("href")
        return resolve(href.lstrip("#"), seen + (gid,)) if href else None

    return {gid: c for gid in grads if (c := resolve(gid)) is not None}


def _inline_solid_gradients(root, colors: Dict[str, str]) -> None:
    sub = lambda v: re.sub(r"url\(#([^)]+)\)",
                           lambda m: colors.get(m.group(1), m.group(0)), v)
    for el in root.iter():
        for attr in ("style", "fill", "stroke"):
            v = el.get(attr)
            if v and "url(#" in v:
                el.set(attr, sub(v))


# ---- defs vacuum (remove anything the document no longer references) ----------


def _refs_in(el) -> Set[str]:
    out: Set[str] = set()
    for v in el.attrib.values():
        out.update(_REF.findall(v))
    return out


def _vacuum_defs(root) -> int:
    defs_ids = {}
    for defs in root.iter(f"{{{SVG_NS}}}defs"):
        for el in defs.iter():
            if el is not defs and el.get("id"):
                defs_ids[el.get("id")] = el
    # Seeds: ids referenced from anywhere outside <defs>.
    defs_nodes = {id(el) for el in defs_ids.values()}
    seeds: Set[str] = set()
    for el in root.iter():
        if id(el) in defs_nodes:
            continue
        seeds |= _refs_in(el)
    # Transitive closure within defs.
    keep: Set[str] = set()
    stack = [s for s in seeds if s in defs_ids]
    while stack:
        i = stack.pop()
        if i in keep:
            continue
        keep.add(i)
        stack += [r for r in _refs_in(defs_ids[i]) if r in defs_ids]
    removed = 0
    for gid, el in defs_ids.items():
        if gid not in keep:
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)
                removed += 1
    return removed


# ---- normalization (deterministic formatting) --------------------------------


def _strip_namedview(root) -> None:
    for nv in (el for el in root.iter() if _local(el.tag) == "namedview"):
        for attr in list(nv.attrib):
            if _local(attr) not in _NAMEDVIEW_KEEP:
                del nv.attrib[attr]
        for child in list(nv):  # grid / guide editor furniture
            nv.remove(child)


def _round_numbers(root, precision: int) -> None:
    def fix(v: str) -> str:
        return _NUM.sub(lambda m: f"{float(m.group(0)):.{precision}f}".rstrip("0").rstrip("."), v)
    for el in root.iter():
        for attr, v in list(el.attrib.items()):
            if any(ch.isdigit() for ch in v) and ("#" not in v or "." in v):
                el.set(attr, fix(v))


def _order_attrs(root) -> None:
    first = {k: i for i, k in enumerate(_ATTR_FIRST)}
    last = {k: i for i, k in enumerate(_ATTR_LAST)}

    def key(name: str):
        if name in first:
            return (0, first[name], "")
        if name in last:
            return (2, last[name], "")
        return (1, 0, name)

    for el in root.iter():
        items = sorted(el.attrib.items(), key=lambda kv: key(kv[0]))
        if [k for k, _ in items] == list(el.attrib):
            continue
        for k in list(el.attrib):
            del el.attrib[k]
        for k, v in items:
            el.set(k, v)


def _normalize_whitespace(root) -> None:
    for el in root.iter():
        if el.text is not None and not el.text.strip():
            el.text = None
        if el.tail is not None and not el.tail.strip():
            el.tail = None


def canonicalize(src: Path, dst: Path, precision: int = 3) -> dict:
    src, dst = Path(src), Path(dst)
    parser = etree.XMLParser(remove_comments=True, remove_blank_text=True)
    tree = etree.parse(str(src), parser)
    root = tree.getroot()

    colors = _solid_colors(root)
    _inline_solid_gradients(root, colors)
    removed = _vacuum_defs(root)
    _strip_namedview(root)
    if precision is not None and precision >= 0:
        _round_numbers(root, precision)
    _normalize_whitespace(root)
    _order_attrs(root)
    etree.indent(tree, space="  ")

    body = etree.tostring(root, encoding="unicode")
    out = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + body + "\n"
    before = src.stat().st_size
    dst.write_text(out, encoding="utf8")
    return {"colors_inlined": len(colors), "defs_removed": removed,
            "bytes_in": before, "bytes_out": len(out.encode("utf8"))}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src")
    ap.add_argument("dst", nargs="?", help="output path (default: overwrite src in place)")
    ap.add_argument("--precision", type=int, default=3)
    a = ap.parse_args(argv)
    dst = a.dst or a.src
    s = canonicalize(Path(a.src), Path(dst), a.precision)
    print(f"{a.src} -> {dst}: inlined {s['colors_inlined']} solid gradients, "
          f"vacuumed {s['defs_removed']} defs; "
          f"{s['bytes_in']//1024}K -> {s['bytes_out']//1024}K")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
