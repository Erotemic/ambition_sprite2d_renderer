#!/usr/bin/env python3
"""Published-asset equivalence harness for the SVG migration.

Where ``parity_harness.py`` pins a *single* target's pixels over time (did this
refactor change the output?), this harness compares **two rendered authorities
of the same character** across the whole published contract — layout,
animations, geometry, metadata, portraits, and decoded pixels — and classifies
how equivalent they are. See
``ambition_sprite2d_renderer/core/equivalence.py`` for the comparator and
``docs/planning/engine/svg-component-character-migration.md`` for why.

It is authority-agnostic on purpose. The SVG migration is not a faithful-pixel
port for every character (a redesign like Oiler will never match the dead legacy
pixels and is not meant to), so a pixel mismatch is reported and quantified but
never fails on its own. What must hold is the *contract*: the same animations,
geometry, sockets, and metadata the runtime reads.

Usage (from tools/ambition_sprite2d_renderer/, deps: Pillow + stdlib +
whatever the target itself needs to render — SVG targets need the venv):

    # Bless a target's current output as its equivalence baseline.
    PYTHONPATH=. python3 equivalence_harness.py bless --target oiler

    # Compare a fresh render of a target against its blessed baseline.
    PYTHONPATH=. python3 equivalence_harness.py compare --target oiler

    # Compare two arbitrary rendered directories (e.g. a PIL render vs an SVG
    # render of a character being ported). This is the mode used while porting.
    PYTHONPATH=. python3 equivalence_harness.py compare --ref pil_out/ --cand svg_out/

    # Compare a live target render against an arbitrary reference directory.
    PYTHONPATH=. python3 equivalence_harness.py compare --target sentinel --against pil_out/

Reports land in ``<repo>/tmp/sprite-drift/<label>/`` — ``equivalence.txt`` (human
summary), ``equivalence.json`` (per-frame stats), and a canonical side-by-side.
``--strict`` exits non-zero only when a structural dimension differs.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from collections import namedtuple
from pathlib import Path
from typing import List, Optional

from ambition_sprite2d_renderer.core.equivalence import (
    compare_renders,
    format_report,
    load_render,
    write_report,
)

PKG_DIR = Path(__file__).resolve().parent
REPO_ROOT = PKG_DIR.parents[1]
BASELINE_DIR = PKG_DIR / ".equivalence-baseline"
DRIFT_DIR = REPO_ROOT / "tmp" / "sprite-drift"


def _discover():
    from ambition_sprite2d_renderer.registry import discover_all_targets

    return discover_all_targets().targets


def _render_target(name: str, out: Path) -> None:
    targets = _discover()
    if name not in targets:
        raise SystemExit(f"unknown target {name!r}; run `list` to see available targets")
    out.mkdir(parents=True, exist_ok=True)
    targets[name].render_sheet(out)


def _canonical_side_by_side(ref: Path, cand: Path, dest: Path) -> None:
    """Write a ref|cand(|diff) image of the canonical sprites for eyeballing."""
    try:
        from PIL import Image, ImageChops, ImageDraw
    except Exception:
        return

    def pick(root: Path) -> Optional[Path]:
        for pat in ("*_canonical_transparent.png", "*_canonical.png",
                    "*_preview_labeled.png", "*_spritesheet.png"):
            hits = sorted(root.rglob(pat))
            if hits:
                return hits[0]
        return None

    rp, cp = pick(ref), pick(cand)
    imgs = []
    a = Image.open(rp).convert("RGBA") if rp else None
    b = Image.open(cp).convert("RGBA") if cp else None
    imgs.append(("reference", a))
    imgs.append(("candidate", b))
    if a is not None and b is not None and a.size == b.size:
        diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB")).convert("RGBA")
        imgs.append(("diff", diff))
    pad, label_h, bg = 8, 16, (32, 34, 40, 255)
    h = max([im.height for _, im in imgs if im is not None] + [1])
    w = sum((im.width if im is not None else 48) + pad for _, im in imgs) + pad
    canvas = Image.new("RGBA", (w, h + label_h + pad), bg)
    d = ImageDraw.Draw(canvas)
    x = pad
    for label, im in imgs:
        d.text((x, 2), label, fill=(220, 224, 235, 255))
        if im is not None:
            canvas.alpha_composite(im, (x, label_h))
            x += im.width + pad
        else:
            d.text((x, label_h), "(none)", fill=(230, 120, 120, 255))
            x += 48 + pad
    dest.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dest)


def cmd_bless(args) -> int:
    dest = BASELINE_DIR / args.target
    if dest.exists():
        shutil.rmtree(dest)
    _render_target(args.target, dest)
    print(f"blessed {args.target} -> {dest}")
    return 0


def _resolve_pair(args, tmpdirs: List[Path]):
    """Return (ref_dir, ref_label, cand_dir, cand_label, out_label)."""
    if args.ref and args.cand:
        return (Path(args.ref), args.ref, Path(args.cand), args.cand,
                args.label or "ref-vs-cand")
    if not args.target:
        raise SystemExit("compare needs either --target or both --ref and --cand")
    # Candidate = a fresh render of the target.
    cand = Path(tempfile.mkdtemp(prefix="equiv_cand_"))
    tmpdirs.append(cand)
    _render_target(args.target, cand)
    if args.against:
        ref_dir, ref_label = Path(args.against), args.against
    else:
        ref_dir = BASELINE_DIR / args.target
        if not ref_dir.exists():
            raise SystemExit(
                f"no baseline for {args.target!r} — run "
                f"`bless --target {args.target}` first, or pass --against DIR")
        ref_label = f"baseline/{args.target}"
    return ref_dir, ref_label, cand, f"live/{args.target}", args.label or args.target


def cmd_compare(args) -> int:
    tmpdirs: List[Path] = []
    try:
        ref_dir, ref_label, cand_dir, cand_label, out_label = _resolve_pair(args, tmpdirs)
        ref = load_render(ref_dir)
        cand = load_render(cand_dir)
        report = compare_renders(ref, cand, edge_tol=args.edge_tol, area_tol=args.area_tol,
                                 geom_tol=args.geom_tol, size_tol=args.size_tol)
        out = DRIFT_DIR / out_label
        write_report(report, out, ref_label=ref_label, cand_label=cand_label)
        _canonical_side_by_side(ref_dir, cand_dir, out / "canonical.compare.png")
        print(format_report(report, ref_label=ref_label, cand_label=cand_label))
        print(f"\n  → report + side-by-side written to {out}")
        if args.strict and not report.structural_ok:
            return 1
        return 0
    finally:
        for d in tmpdirs:
            shutil.rmtree(d, ignore_errors=True)


def cmd_export(args) -> int:
    """Write a convertible target's editable component scene SVG to disk."""
    from ambition_sprite2d_renderer.targets.characters import _pirate_common as pirates

    if not pirates.is_pirate_family(args.target):
        raise SystemExit(
            f"{args.target!r} has no cooperative part seam yet — use "
            f"`autoconvert` for the interception-based converter")
    out = Path(args.out) if args.out else (DRIFT_DIR / args.target / f"{args.target}.svg")
    path = pirates.export_scene(args.target, out)
    scene = pirates.build_scene(args.target)
    print(f"exported component scene -> {path}  {scene.stats()}")
    return 0


def cmd_rebuild(args) -> int:
    """Rebuild a target's published sheet FROM a (human-edited) scene file."""
    from ambition_sprite2d_renderer.targets.characters import _pirate_common as pirates

    if not pirates.is_pirate_family(args.target):
        raise SystemExit(f"{args.target!r} is not scene-rebuildable yet")
    out = Path(args.out) if args.out else (DRIFT_DIR / args.target / "rebuilt")
    out.mkdir(parents=True, exist_ok=True)
    pirates.render_target_svg(args.target, out, scene_path=Path(args.scene))
    print(f"rebuilt sheet from {args.scene} -> {out}")
    print("compare against the PIL authority with:")
    print(f"  equivalence_harness.py compare --target {args.target} --against {out}")
    return 0


def _classify_status(complete: bool, unsupported, dangling, failed: int,
                     verified: int, total: int, full: bool) -> str:
    """Honest conversion status — ``captured`` means *fully* verified.

    captured — capture is complete, has no gaps, and EVERY published frame was
               re-rendered from the saved scene and matched;
    sampled  — capture is complete and clean, but only a subset of frames was
               fidelity-checked (roster-speed sampling). Not proof for the
               unchecked frames — final per-character approval must run --full;
    partial  — a real gap: unsupported ops, dangling refs, missing frames, a
               failed verification, or nothing verifiable at all.

    A pure function so the poison test can pin the boundary directly.
    """
    if not complete or unsupported or dangling or failed > 0:
        return "partial"
    if verified == 0:
        return "partial"  # could not establish fidelity for any frame
    if full and verified >= total:
        return "captured"
    return "sampled"


def _shift_onto_transparent(img, dx: int, dy: int):
    """Translate ``img`` by ``(dx, dy)`` onto a transparent canvas.

    Unlike ``ImageChops.offset`` this does NOT wrap pixels around the opposite
    edge — content shifted off the canvas is lost and the vacated band stays
    transparent, which is what a genuine alignment search wants.
    """
    from PIL import Image

    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img, (dx, dy))
    return out


# Two independent defect fractions for a candidate frame alignment, computed on
# a CONTINUOUS alpha-aware basis (no near-opaque cutoff — an earlier version
# thresholded alpha at >200, which discarded every translucent glow/beam/cloth
# pixel, so a missing or invented translucent component scored zero and passed):
#   occupancy — how much of the total alpha "mass" is present in one frame but
#               absent (or at a different alpha) in the other, over the union of
#               meaningful alpha. This is the COMPLETENESS bar (a dropped or
#               invented part — opaque OR translucent — must fail) and is tight.
#   rgb       — straight colour disagreement, weighted by how confidently BOTH
#               frames occupy each pixel (min alpha), over that mutual mass. The
#               pre-existing resvg-vs-Pillow rasterizer/AA slack, held looser.
# Two gates, not one blend: a single number cannot be both tight enough to catch
# a missing part and loose enough for colour noise. Premultiplied/alpha-weighted
# throughout, so a soft anti-aliased or blurred edge (where both frames agree on
# the gradient) contributes ~0 while a whole missing translucent limb does not.
_FrameDefect = namedtuple("_FrameDefect", "occupancy rgb")
_MEANINGFUL = 12          # alpha (0-255) below this is noise, not content
# A complete, complex frame still shows a few % defect purely from resvg-vs-Pillow
# edge AA and translucent-gradient (blur) rasterization. The occupancy bar sits
# just above that noise floor: it reliably catches the reviewer's defect class (an
# omitted/invented arm / weapon / thruster / glow == a meaningful share of the
# alpha mass) but, like any raster check, cannot resolve a single small primitive
# from fringe noise.
# Measured floor: mockingbird's complete frames run to ~0.056 occupancy, driven
# by its extended translucent thruster beam (resvg vs Pillow rasterize the soft
# gradient's alpha differently); the bar clears that with headroom.
_OCC_TOL = 0.07   # union alpha-mass mismatch past this == real dropped/added geom
_RGB_TOL = 0.12   # colour disagreement over the mutually-occupied mass (AA slack)


def _np_shift(arr, dx: int, dy: int):
    """Translate ``arr`` (H×W×C) by ``(dx, dy)`` with zero fill — no wraparound."""
    import numpy as np

    out = np.zeros_like(arr)
    h, w = arr.shape[:2]
    sx0, sx1 = max(0, -dx), w - max(0, dx)
    dx0, dx1 = max(0, dx), w - max(0, -dx)
    sy0, sy1 = max(0, -dy), h - max(0, dy)
    dy0, dy1 = max(0, dy), h - max(0, -dy)
    if sx1 > sx0 and sy1 > sy0:
        out[dy0:dy1, dx0:dx1] = arr[sy0:sy1, sx0:sx1]
    return out


def _frame_defects(pub, ras, meaningful: int = _MEANINGFUL, rgb_tol: int = 16,
                   shift: int = 1) -> "_FrameDefect":
    """Best-aligned (occupancy, rgb) defect fractions for ``pub`` vs ``ras``.

    Alpha-aware and symmetric. For each ±``shift`` alignment (``ras`` translated
    with zero fill — never wrapped) let ``ap``/``ar`` be the [0,1] alphas:

    * occupancy ``= Σ|ap-ar| / Σ max(ap,ar)`` over the union of meaningful
      alpha. Missing, invented, AND wrong-alpha geometry all land here, at any
      opacity — a translucent beam the SVG drops contributes its full alpha mass,
      while a soft edge both frames render the same (``ap≈ar``) contributes ~0.
    * rgb ``= Σ min(ap,ar)·|rgb_p-rgb_r| / Σ min(ap,ar)`` over the mutually
      occupied region — straight colour disagreement weighted toward pixels both
      frames confidently fill, so a colour drift is caught but a missing part
      (``min=0`` there) does not leak into the colour term.

    The alignment with the least occupancy defect is returned. Returns (1.0, 1.0)
    when neither frame has any meaningful content to compare. ``rgb_tol`` clamps
    sub-threshold per-channel colour noise to zero before weighting.
    """
    import numpy as np

    m = meaningful / 255.0
    P = np.asarray(pub.convert("RGBA"), dtype=np.float32)
    R0 = np.asarray(ras.convert("RGBA"), dtype=np.float32)
    ap = P[..., 3] / 255.0
    prgb = P[..., :3]
    best = _FrameDefect(1.0, 1.0)
    for dx in range(-shift, shift + 1):
        for dy in range(-shift, shift + 1):
            R = _np_shift(R0, dx, dy)
            ar = R[..., 3] / 255.0
            union = np.maximum(ap, ar)
            meaningful_mask = union > m
            n_union = float(union[meaningful_mask].sum())
            if n_union <= 0.0:
                continue
            occ = float(np.abs(ap - ar)[meaningful_mask].sum()) / n_union
            ov = np.minimum(ap, ar)
            n_ov = float(ov.sum())
            if n_ov > 0.0:
                # per-channel |Δ|, clamp sub-tol noise, average the 3 channels
                chan = np.abs(prgb - R[..., :3])
                chan = np.where(chan > rgb_tol, chan, 0.0).mean(axis=2) / 255.0
                rgb = float((ov * chan).sum()) / n_ov
            else:
                rgb = 1.0
            if occ < best.occupancy:
                best = _FrameDefect(occ, rgb)
    return best


def _frame_verified(pub, ras) -> bool:
    """True only when the frame is COMPLETE at every opacity (tight alpha-mass
    occupancy bar — a dropped/added/wrong-alpha part, opaque or translucent,
    fails) and colour-consistent where both frames occupy (looser rasterizer
    bar). A mistranslation beyond the search fails occupancy; only resvg-vs-Pillow
    AA/blur colour noise is absorbed by the rgb bar."""
    d = _frame_defects(pub, ras)
    return d.occupancy <= _OCC_TOL and d.rgb <= _RGB_TOL


def _autoconvert_one(name: str, target, out_dir: Path, verify_frames: int = 6,
                     full: bool = False):
    """Auto-capture one target into a saved scene plus fidelity statistics.

    See :func:`_classify_status` for status semantics. `needs-seam` means no
    trustworthy published-frame association exists. `full=True` verifies every
    captured frame; otherwise a clean strided sample is reported as `sampled`.
    """
    import io

    from PIL import Image, ImageChops

    from ambition_sprite2d_renderer.authoring.auto_capture import (
        capture_target_frames, discover_parts,
    )
    from ambition_sprite2d_renderer.authoring.svg_scene import ComponentScene
    from ambition_sprite2d_renderer.core.equivalence import parse_ron

    files, semantic, diagnostics = capture_target_frames(target)
    if not semantic:
        return {"status": "needs-seam", "diagnostic_recorders": len(diagnostics)}

    manifests = {k[: -len("_spritesheet.ron")]: parse_ron(v.decode())[0]
                 for k, v in files.items() if k.endswith("_spritesheet.ron")}
    expected = sum(r.get("frame_count", 0)
                   for sheet in manifests.values() for r in sheet.get("rows", []))

    stems = {k[0] for k in semantic}
    multi = len(stems) > 1

    unsupported = set()
    for rec in semantic.values():
        unsupported |= rec.unsupported

    # Build the scene from XML-split elements (never regex).
    frames_elems = {}
    canvas = None
    for (stem, anim, idx), rec in semantic.items():
        key = (f"{stem}:{anim}" if multi else anim, idx)
        frames_elems[key] = rec.body_svg()
        canvas = canvas or (rec.width, rec.height)
    parts, bodies = discover_parts(frames_elems)
    scene = ComponentScene(canvas or (128, 128))
    scene.parts = parts
    scene.frames = bodies
    scene_path = out_dir / f"{name}.svg"
    scene.save(scene_path)

    # Final fidelity: reload the SAVED scene, render its frame docs, compare
    # against the actually-published sheet pixels in frame coordinates.
    loaded = ComponentScene.load(scene_path)
    verified = failed = 0
    dangling = loaded.missing_part_refs()
    if full:
        sample = sorted(semantic)  # final approval: verify every frame
    else:
        sample = sorted(semantic)[:: max(1, len(semantic) // verify_frames)][:verify_frames]
    try:
        import resvg_py
    except ImportError:
        resvg_py = None
    if resvg_py is not None and not dangling:
        for (stem, anim, idx) in sample:
            sheet = manifests.get(stem) or next(iter(manifests.values()))
            row = next((r for r in sheet.get("rows", [])
                        if r.get("animation") == anim), None)
            page_name = f"{stem}_spritesheet.png"
            if row is None or page_name not in files or idx >= len(row["rects"]):
                failed += 1
                continue
            fw, fh = int(sheet["frame_width"]), int(sheet["frame_height"])
            doc = loaded.frame_doc(f"{stem}:{anim}" if multi else anim, idx)
            png = resvg_py.svg_to_bytes(svg_string=doc)
            ras = Image.open(io.BytesIO(bytes(png))).convert("RGBA")
            if ras.size != (fw, fh):
                # Never resize to compensate: the scene must already be in
                # published-frame coordinates (the seam fires post-crop). A
                # mismatch is a real capture defect.
                failed += 1
                continue
            page = Image.open(io.BytesIO(files[page_name])).convert("RGBA")
            r = row["rects"][idx]
            pub = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            off = r.get("off") or [0, 0]
            pub.alpha_composite(
                page.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"])),
                (int(off[0]), int(off[1])))
            # Symmetric fidelity: a frame is verified only when solid geometry
            # is COMPLETE (tight occupancy bar over the union — an omitted or
            # invented part fails) and colour-consistent (looser rasterizer/AA
            # bar). Translucent glow stays excluded (by-design alpha divergence).
            if _frame_verified(pub, ras):
                verified += 1
            else:
                failed += 1

    # Review artifact: published frame | scene render | diff for the first
    # frame of each animation.
    try:
        if resvg_py is not None:
            strips = []
            seen_anims = set()
            for (stem, anim, idx) in sorted(semantic):
                if (stem, anim) in seen_anims or idx != 0:
                    continue
                seen_anims.add((stem, anim))
                sheet = manifests.get(stem) or next(iter(manifests.values()))
                row = next((r for r in sheet.get("rows", [])
                            if r.get("animation") == anim), None)
                page_name = f"{stem}_spritesheet.png"
                if row is None or page_name not in files or not row["rects"]:
                    continue
                fw, fh = int(sheet["frame_width"]), int(sheet["frame_height"])
                doc = loaded.frame_doc(f"{stem}:{anim}" if multi else anim, 0)
                png = resvg_py.svg_to_bytes(svg_string=doc)
                ras = Image.open(io.BytesIO(bytes(png))).convert("RGBA")
                if ras.size != (fw, fh):
                    continue
                page = Image.open(io.BytesIO(files[page_name])).convert("RGBA")
                r = row["rects"][0]
                pub = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
                off = r.get("off") or [0, 0]
                pub.alpha_composite(
                    page.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"])),
                    (int(off[0]), int(off[1])))
                diff = ImageChops.difference(pub.convert("RGB"), ras.convert("RGB")).convert("RGBA")
                strip = Image.new("RGBA", (fw * 3 + 12, fh), (30, 30, 36, 255))
                strip.alpha_composite(pub, (0, 0))
                strip.alpha_composite(ras, (fw + 6, 0))
                strip.alpha_composite(diff, (fw * 2 + 12, 0))
                strips.append(strip)
            if strips:
                W = max(st.width for st in strips)
                H = sum(st.height + 4 for st in strips)
                canvas = Image.new("RGBA", (W, H), (30, 30, 36, 255))
                y = 0
                for st in strips:
                    canvas.alpha_composite(st, (0, y))
                    y += st.height + 4
                canvas.save(out_dir / f"{name}_compare.png")
    except Exception:
        pass  # the compare strip is best-effort review aid, never a failure

    complete = len(semantic) == expected and expected > 0
    status = _classify_status(complete, unsupported, dangling, failed,
                              verified, len(semantic), full)
    return {
        "status": status,
        "frames": len(semantic),
        "expected": expected,
        "parts": len(parts),
        "part_uses": scene.stats()["part_uses"],
        "verified": verified,
        "verify_failed": failed,
        "verify_full": full,
        "dangling_refs": dangling,
        "unsupported": sorted(unsupported),
        "scene": str(scene_path),
    }


def cmd_autoconvert(args) -> int:
    """Universal converter: capture any target's render into a component scene."""
    targets = _discover()
    if args.target not in targets:
        raise SystemExit(f"unknown target {args.target!r}")
    out = Path(args.out) if args.out else (DRIFT_DIR / "auto_scenes")
    out.mkdir(parents=True, exist_ok=True)
    stats = _autoconvert_one(args.target, targets[args.target], out,
                             full=args.full)
    for k, v in stats.items():
        print(f"  {k}: {v}")
    return 0


def cmd_coverage(args) -> int:
    """Run the universal converter across the roster; write a status report."""
    import json
    import traceback

    targets = _discover()
    names = sorted(targets)
    if args.targets:
        wanted = [t.strip() for t in args.targets.split(",")]
        names = [n for n in names if n in wanted]
    out = DRIFT_DIR / "auto_scenes"
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    for i, name in enumerate(names, 1):
        try:
            report[name] = _autoconvert_one(name, targets[name], out,
                                            full=args.full)
        except Exception as exc:
            report[name] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
            if args.verbose:
                traceback.print_exc()
        s = report[name]
        print(f"[{i}/{len(names)}] {name}: {s['status']}"
              f" frames={s.get('frames', 0)}/{s.get('expected', '?')}"
              f" parts={s.get('parts', 0)} verified={s.get('verified', 0)}"
              f"{' unsupported=' + ','.join(s['unsupported']) if s.get('unsupported') else ''}")
    (DRIFT_DIR / "coverage.json").write_text(json.dumps(report, indent=1, sort_keys=True))
    counts: dict = {}
    for s in report.values():
        counts[s["status"]] = counts.get(s["status"], 0) + 1
    print(f"\ncoverage: {counts} -> scenes in {out}, report in {DRIFT_DIR/'coverage.json'}")
    if counts.get("error"):
        return 1
    if args.strict and (counts.get("partial") or counts.get("needs-seam")):
        return 1
    return 0


def cmd_list(args) -> int:
    for name in sorted(_discover()):
        print(name)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("bless", help="render a target and store it as the equivalence baseline")
    pb.add_argument("--target", required=True)
    pb.set_defaults(func=cmd_bless)

    pc = sub.add_parser("compare", help="compare two renders across the published contract")
    pc.add_argument("--target", help="render this target as the candidate")
    pc.add_argument("--against", help="reference directory (default: the blessed baseline)")
    pc.add_argument("--ref", help="reference render dir (pairs with --cand)")
    pc.add_argument("--cand", help="candidate render dir (pairs with --ref)")
    pc.add_argument("--label", help="report subdirectory name under tmp/sprite-drift/")
    pc.add_argument("--edge-tol", type=int, default=6,
                    help="max per-channel delta still counted as an AA edge (default 6)")
    pc.add_argument("--area-tol", type=float, default=0.02,
                    help="fraction of a frame allowed to change for raster-equivalence (default 0.02)")
    pc.add_argument("--geom-tol", type=float, default=1.5,
                    help="pixel slack on measured geometry (body bbox/feet/sockets) (default 1.0)")
    pc.add_argument("--size-tol", type=int, default=1,
                    help="per-frame silhouette size slack in px before size-mismatch (default 1)")
    pc.add_argument("--strict", action="store_true",
                    help="exit non-zero when a structural dimension differs")
    pc.set_defaults(func=cmd_compare)

    pe = sub.add_parser("export", help="write a target's editable component scene SVG")
    pe.add_argument("--target", required=True)
    pe.add_argument("--out", help="output file (default: tmp/sprite-drift/<target>/<target>.svg)")
    pe.set_defaults(func=cmd_export)

    pr = sub.add_parser("rebuild", help="rebuild the sheet from a (human-edited) scene SVG")
    pr.add_argument("--target", required=True)
    pr.add_argument("--scene", required=True, help="path to the edited scene SVG")
    pr.add_argument("--out", help="output dir (default: tmp/sprite-drift/<target>/rebuilt)")
    pr.set_defaults(func=cmd_rebuild)

    pa = sub.add_parser("autoconvert",
                        help="capture ANY target's render into a component scene (no code changes)")
    pa.add_argument("--target", required=True)
    pa.add_argument("--out", help="scene output dir (default: tmp/sprite-drift/auto_scenes)")
    pa.add_argument("--full", action="store_true",
                    help="verify EVERY frame (required to reach 'captured', not just 'sampled')")
    pa.set_defaults(func=cmd_autoconvert)

    pv = sub.add_parser("coverage", help="run the universal converter across the roster")
    pv.add_argument("--targets", help="comma-separated subset (default: all)")
    pv.add_argument("--verbose", action="store_true")
    pv.add_argument("--full", action="store_true",
                    help="verify EVERY frame per target (slow; lets a target reach 'captured')")
    pv.add_argument("--strict", action="store_true",
                    help="also exit nonzero on partial / needs-seam results")
    pv.set_defaults(func=cmd_coverage)

    pl = sub.add_parser("list", help="list renderable targets")
    pl.set_defaults(func=cmd_list)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
