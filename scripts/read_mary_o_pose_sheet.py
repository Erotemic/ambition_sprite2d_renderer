#!/usr/bin/env python3
"""Read an edited Mary-O pose sheet back out as pose values.

Pairs with `export_mary_o_pose_sheet.py`. For every part in every cell it
recomputes the placement the exporter wrote, reads the placement that is in the
file now, and reports the difference -- a translation in frame units and a
rotation in degrees, which is exactly what a pose entry holds.

    uv run python scripts/read_mary_o_pose_sheet.py [--form tall] [--anim crouch]
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.targets.characters import _mary_o_v2_svg_poc as poc  # noqa: E402
from ambition_sprite2d_renderer.targets.characters import _mary_o_v2_model as M  # noqa: E402

SOURCE = ROOT / "assets" / "mary_o_v2.svg"
FORMS = {"short": M.SHORT_FORM, "tall": M.TALL_FORM, "fire": M.FIRE_FORM}


def mul(a, b):
    return (a[0]*b[0]+a[2]*b[1], a[1]*b[0]+a[3]*b[1],
            a[0]*b[2]+a[2]*b[3], a[1]*b[2]+a[3]*b[3],
            a[0]*b[4]+a[2]*b[5]+a[4], a[1]*b[4]+a[3]*b[5]+a[5])


def parse_tx(t):
    m = (1, 0, 0, 1, 0, 0)
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", t or ""):
        v = [float(x) for x in re.split(r"[,\s]+", args.strip()) if x]
        if name == "translate":
            n = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0.0)
        elif name == "matrix":
            n = tuple(v)
        elif name == "scale":
            n = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "rotate":
            a = math.radians(v[0]); c, s = math.cos(a), math.sin(a)
            n = (c, s, -s, c, 0, 0)
        else:
            raise SystemExit(f"unhandled transform {name!r}")
        m = mul(m, n)
    return m


def inv(m):
    a, b, c, d, e, f = m
    det = a*d - b*c
    return (d/det, -b/det, -c/det, a/det, (c*f - d*e)/det, (b*e - a*f)/det)


def apply(m, p):
    return (m[0]*p[0] + m[2]*p[1] + m[4], m[1]*p[0] + m[3]*p[1] + m[5])


def chain_to(el, root):
    """Transforms from `root` down to and including `el`."""
    stack, n = [], el
    while n is not None and n is not root:
        stack.append(n.get("transform"))
        n = n.getparent()
    m = (1, 0, 0, 1, 0, 0)
    for t in reversed(stack):
        m = mul(m, parse_tx(t))
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", default=None)
    ap.add_argument("--anim", default=None)
    ap.add_argument("--min-move", type=float, default=0.25)
    a = ap.parse_args()

    for key, form in FORMS.items():
        if a.form and key != a.form:
            continue
        path = ROOT / "assets" / f"mary_o_v2_poses_{key}.svg"
        if not path.exists():
            continue
        edited = etree.fromstring(path.read_bytes())
        eids = {e.get("id"): e for e in edited.iter() if isinstance(e.tag, str) and e.get("id")}

        side = poc.build_rig_document(SOURCE, form, "side")
        front = poc.build_rig_document(SOURCE, form, "front")
        src = etree.fromstring(SOURCE.read_bytes())
        anc = {}
        def walk(el, accm):
            for kid in el:
                if not isinstance(kid.tag, str):
                    continue
                if kid.get("id"):
                    anc[kid.get("id")] = accm
                walk(kid, mul(accm, parse_tx(kid.get("transform"))))
        walk(src, (1, 0, 0, 1, 0, 0))

        print(f"\n================ {key} ================")
        for anim, nframes, _dur in form.rows:
            if a.anim and anim != a.anim:
                continue
            doc = front if anim == "death" else side
            clip = anim if anim in doc.data["clips"] else None
            if clip is None:
                continue
            for fi in range(nframes):
                t = doc.frame_time(clip, fi, nframes)
                sample = doc.sample(clip, t)
                fr = doc.frame
                rootpt = (float(fr.get("center_x", fr["width"]/2)) + sample.get("root_x", 0.0),
                          float(fr.get("ground_y", fr["height"]-2)) + sample.get("root_y", 0.0))
                sk = doc.build_skeleton()
                offs = {n: (sample.get(f"bone.{n}.x", 0.0), sample.get(f"bone.{n}.y", 0.0)) for n in sk.bones}
                world = sk.world({n: v for n, v in sample.items() if n in sk.bones}, root=rootpt, offsets=offs)
                for part in doc.data["parts"]:
                    bone = part.get("bone")
                    if bone not in world:
                        continue
                    bw = world[bone]
                    px, py = part["pivot"]
                    for art_id in part["include"]:
                        uid = f"pose_{key}_{anim}_{fi:02d}_{part['name']}"
                        el = eids.get(uid)
                        if el is None:
                            continue
                        A = anc.get(art_id, (1, 0, 0, 1, 0, 0))
                        local_pivot = apply(inv(A), (px, py))
                        cell = chain_to(el.getparent(), edited)
                        T = mul(cell, parse_tx(el.get("transform")))
                        now = apply(T, local_pivot)
                        want = apply(cell, bw.origin)
                        dx, dy = now[0]-want[0], now[1]-want[1]
                        ang = math.degrees(math.atan2(T[1], T[0]))
                        dang = ((ang - bw.angle + 180) % 360) - 180
                        if abs(dx) < a.min_move and abs(dy) < a.min_move and abs(dang) < 0.5:
                            continue
                        print(f"  {anim:<9} f{fi} {part['name']:<20} "
                              f"move=({dx:+7.2f},{dy:+7.2f})  rot={dang:+7.2f}deg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
