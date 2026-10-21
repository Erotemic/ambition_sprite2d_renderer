"""Every sprite part of the given rigs, drawn over the full canvas and in a
window (`svg_parts._render_kept`): the same size, offset and pixels? And how
long does each take? Measurement only.

    .venv/bin/python scripts/check_svg_part_window.py SCALE [RIG.json ...]

SCALE is the composite scale `S` of `RigDocument.sprite_raster` (4 is the
sheet's). With no rigs, every `*.rig.json` under targets/characters/rigged.
Pixels are compared alpha-weighted; a part whose size or offset differs is
reported with maxdiff 999.
"""
import glob, json, os, sys, time
import numpy as np
from pathlib import Path
import ambition_sprite2d_renderer.authoring.svg_parts as SP
inner = SP._rasterize_subset_cached.__wrapped__
windowed = SP._render_kept
full = lambda root, keep, dpi: SP._render_full(root, dpi)
rigs = sys.argv[2:] or sorted(glob.glob("ambition_sprite2d_renderer/targets/characters/rigged/**/*.rig.json", recursive=True))
S = float(sys.argv[1])
worst = []
n = bad = 0; t_full = t_win = 0.0
for rj in rigs:
    d = json.load(open(rj)); src = d.get("svg_source") or {}
    if not src.get("path"): continue
    svg = os.path.normpath(os.path.join(os.path.dirname(rj), src["path"]))
    if not os.path.exists(svg): continue
    st = os.stat(svg)
    dpi = float(src.get("ref_dpi", 96.0)) * float(src.get("scale", 1.0)) * S
    for part in d.get("parts", []):
        inc = tuple(part.get("include") or ())
        if part.get("kind") != "sprite" or not inc: continue
        args = (svg, st.st_mtime_ns, st.st_size, str(src.get("view", "")), inc, dpi)
        SP._render_kept = full; t = time.perf_counter(); a = inner(*args); t_full += time.perf_counter() - t
        SP._render_kept = windowed; t = time.perf_counter(); b = inner(*args); t_win += time.perf_counter() - t
        n += 1
        same = (a[0] is None) == (b[0] is None) and a[1] == b[1] and (a[0] is None or (a[0].size == b[0].size and np.array_equal(np.asarray(a[0]), np.asarray(b[0]))))
        if not same:
            bad += 1
            diff = None
            if a[0] is not None and b[0] is not None and a[0].size == b[0].size:
                def pm(im):
                    x = np.asarray(im).astype(float); return np.concatenate([x[..., :3] * x[..., 3:] / 255.0, x[..., 3:]], axis=2)
                diff = int(round(np.abs(pm(a[0]) - pm(b[0])).max()))
            px = int((np.abs(pm(a[0]) - pm(b[0])).max(axis=2) > 1.0).sum()) if diff is not None else -1
            worst.append((diff if diff is not None else 999, px, os.path.basename(rj), part.get("name"), a[1], b[1]))
worst.sort(reverse=True)
for w in worst[:8]: print("DIFF maxdiff=%s pixels=%s %s %s %s %s" % w)
print("parts with a size/offset mismatch:", sum(1 for w in worst if w[0] == 999))
print(f"{n} parts, {bad} differ; full {t_full:.1f}s, windowed {t_win:.1f}s")
