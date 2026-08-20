#!/usr/bin/env python3
"""Write Mary-O's POSES as an editable SVG, laid out like her spritesheet.

One cell per frame, rows in sheet order, each cell holding the real art placed
exactly where the rig would place it -- as `<use>` of the source SVG's parts, so
the file stays small and always shows current artwork.

The point is the round trip: open this in Inkscape, drag a part until the pose
looks right, save, and `read_mary_o_pose_sheet.py` reads the positions back out
as pose values. A pose stops being a column of numbers nobody can picture.

    uv run python scripts/export_mary_o_pose_sheet.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.targets.characters import _mary_o_v2_svg_poc as poc  # noqa: E402
from ambition_sprite2d_renderer.targets.characters import _mary_o_v2_model as M  # noqa: E402

SVG_NS = "http://www.w3.org/2000/svg"
INK = "http://www.inkscape.org/namespaces/inkscape"
XLINK = "http://www.w3.org/1999/xlink"
SOURCE = ROOT / "assets" / "mary_o_v2.svg"
LABEL_W = 90


def _ancestor_matrix(src_root):
    """id -> the transform its ANCESTORS apply, composed.

    ⛔ `<use>` honours the referenced element's own transform but NOT the ones
    its ancestors carry, and every art id here lives inside a view layer with a
    `translate(...)` on it. Without folding that chain back in, every part draws
    at the wrong place -- which looks exactly like the art failing to resolve.
    """
    import re as _re

    def mul(a, b):
        return (a[0]*b[0]+a[2]*b[1], a[1]*b[0]+a[3]*b[1],
                a[0]*b[2]+a[2]*b[3], a[1]*b[2]+a[3]*b[3],
                a[0]*b[4]+a[2]*b[5]+a[4], a[1]*b[4]+a[3]*b[5]+a[5])

    def parse(t):
        m = (1, 0, 0, 1, 0, 0)
        for name, args in _re.findall(r"(\w+)\s*\(([^)]*)\)", t or ""):
            v = [float(x) for x in _re.split(r"[,\s]+", args.strip()) if x]
            if name == "translate":
                n = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0.0)
            elif name == "matrix":
                n = tuple(v)
            elif name == "scale":
                n = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
            elif name == "rotate":
                a = math.radians(v[0]); c, sn = math.cos(a), math.sin(a)
                n = (c, sn, -sn, c, 0, 0)
            else:
                raise SystemExit(f"unhandled transform {name!r}")
            m = mul(m, n)
        return m

    out = {}
    def walk(el, acc):
        for kid in el:
            if not isinstance(kid.tag, str):
                continue
            if kid.get("id"):
                out[kid.get("id")] = acc
            walk(kid, mul(acc, parse(kid.get("transform"))))
    walk(src_root, (1, 0, 0, 1, 0, 0))
    return out


def _cell_group(doc, form, anim, frame_idx, nframes, x0, y0, anc):
    """One frame's worth of `<use>` placements, in sheet coordinates."""
    projection = "front" if anim == "death" else "side"
    clip = "death" if anim == "death" else anim
    if clip not in doc.data["clips"]:
        return None
    t = doc.frame_time(clip, frame_idx, nframes)
    sample = doc.sample(clip, t)
    fr = doc.frame
    root = (
        float(fr.get("center_x", fr["width"] / 2)) + sample.get("root_x", 0.0),
        float(fr.get("ground_y", fr["height"] - 2)) + sample.get("root_y", 0.0),
    )
    sk = doc.build_skeleton()
    offsets = {
        n: (sample.get(f"bone.{n}.x", 0.0), sample.get(f"bone.{n}.y", 0.0))
        for n in sk.bones
    }
    world = sk.world({n: v for n, v in sample.items() if n in sk.bones},
                     root=root, offsets=offsets)

    g = etree.Element(f"{{{SVG_NS}}}g")
    g.set(f"{{{INK}}}label", f"{anim}/{frame_idx:02d}")
    g.set("id", f"pose_{form}_{anim}_{frame_idx:02d}")
    g.set("transform", f"translate({x0},{y0})")
    for part in doc.data["parts"]:
        bone = part.get("bone")
        if bone not in world:
            continue
        bw = world[bone]
        delta = bw.angle - float(part.get("rest_angle", 0.0))
        sy = float(sample.get(f"bone.{bone}.scale_y", 1.0))
        sx = -1.0 if sample.get(f"bone.{bone}.flip_x", 0.0) >= 0.5 else 1.0
        px, py = part["pivot"]
        for art_id in part["include"]:
            u = etree.SubElement(g, f"{{{SVG_NS}}}use")
            u.set(f"{{{XLINK}}}href", f"#{art_id}")
            u.set(f"{{{INK}}}label", f"{part['name']}")
            u.set("id", f"pose_{form}_{anim}_{frame_idx:02d}_{part['name']}")
            u.set("data-pose-part", part["name"])
            u.set("data-pose-bone", bone)
            A = anc.get(art_id, (1, 0, 0, 1, 0, 0))
            u.set(
                "transform",
                f"translate({bw.origin[0]:.4g},{bw.origin[1]:.4g}) "
                f"rotate({delta:.4g}) scale({sx:.4g},{sy:.4g}) "
                f"translate({-px:.4g},{-py:.4g}) "
                f"matrix({','.join(f'{v:.6g}' for v in A)})",
            )
        # the handle an author actually drags
        d = etree.SubElement(g, f"{{{SVG_NS}}}circle")
        d.set("id", f"pivot_{form}_{anim}_{frame_idx:02d}_{part['name']}")
        d.set(f"{{{INK}}}label", f"{part['name']} pivot")
        d.set("data-pose-pivot", part["name"])
        d.set("cx", f"{bw.origin[0]:.4g}")
        d.set("cy", f"{bw.origin[1]:.4g}")
        d.set("r", "1.1")
        d.set("fill", "#ff3bd4")
        d.set("fill-opacity", "0.35")
        d.set("stroke", "#43133d")
        d.set("stroke-width", "0.5")
    return g


def build(form_spec, key: str) -> etree._Element:
    side = poc.build_rig_document(SOURCE, form_spec, "side")
    front = poc.build_rig_document(SOURCE, form_spec, "front")
    fw = side.frame["width"]
    fh = side.frame["height"]
    rows = list(form_spec.rows)
    cols = max(n for _r, n, _d in rows)

    root_el = etree.Element(
        f"{{{SVG_NS}}}svg",
        nsmap={None: SVG_NS, "inkscape": INK, "xlink": XLINK},
    )
    width = LABEL_W + cols * fw
    height = len(rows) * fh
    root_el.set("width", str(width))
    root_el.set("height", str(height))
    root_el.set("viewBox", f"0 0 {width} {height}")

    # the source art, referenced not copied: <use> resolves into <defs>
    defs = etree.SubElement(root_el, f"{{{SVG_NS}}}defs")
    src = etree.fromstring(SOURCE.read_bytes())
    anc = _ancestor_matrix(src)
    for child in src:
        if isinstance(child.tag, str) and child.tag.split("}")[-1] in ("defs", "g"):
            defs.append(child)

    for r, (anim, nframes, _dur) in enumerate(rows):
        y0 = r * fh
        lab = etree.SubElement(root_el, f"{{{SVG_NS}}}text")
        lab.set("x", "4")
        lab.set("y", str(y0 + fh / 2))
        lab.set("font-size", "9")
        lab.set("fill", "#43133d")
        lab.set(f"{{{INK}}}label", f"label {anim}")
        lab.text = anim
        doc = front if anim == "death" else side
        for f in range(nframes):
            g = _cell_group(doc, key, anim, f, nframes, LABEL_W + f * fw, y0, anc)
            if g is not None:
                root_el.append(g)
        # a frame outline, so cells are obvious while dragging
        for f in range(nframes):
            box = etree.SubElement(root_el, f"{{{SVG_NS}}}rect")
            box.set("x", str(LABEL_W + f * fw)); box.set("y", str(y0))
            box.set("width", str(fw)); box.set("height", str(fh))
            box.set("fill", "none"); box.set("stroke", "#c8b8d8")
            box.set("stroke-width", "0.3")
            box.set(f"{{{INK}}}label", f"cell {anim}/{f:02d}")
    return root_el


def main() -> int:
    for form, key in ((M.SHORT_FORM, "short"), (M.TALL_FORM, "tall"), (M.FIRE_FORM, "fire")):
        el = build(form, key)
        etree.indent(el, space="  ")
        out = ROOT / "assets" / f"mary_o_v2_poses_{key}.svg"
        out.write_bytes(etree.tostring(el, xml_declaration=True, encoding="UTF-8", pretty_print=True))
        print(f"wrote {out.relative_to(ROOT)}  ({out.stat().st_size:,} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
