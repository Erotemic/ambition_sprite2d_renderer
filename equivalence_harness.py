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


def _autoconvert_one(name: str, target, out_dir: Path, verify_frames: int = 6):
    """Auto-capture one target -> saved scene + fidelity stats.

    Status semantics (per the 2026-07-23 conversion review):
      captured   — every published frame captured at the semantic seam, no
                   unsupported ops, and the SAVED scene re-renders to match
                   the published pixels on every sampled frame;
      partial    — captured with gaps (unsupported ops, missing frames, or
                   sampled-frame mismatches) — a diagnostic candidate scene;
      needs-seam — the renderer never crossed the build_sheet publication
                   seam; no trustworthy frame association exists.
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
            # Judge solid content (translucent divergence = alpha semantics).
            best = 1.0
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    b = ImageChops.offset(ras, dx, dy)
                    mask = ImageChops.multiply(
                        pub.split()[3].point(lambda v: 255 if v > 200 else 0),
                        b.split()[3].point(lambda v: 255 if v > 200 else 0))
                    n_mask = sum(mask.histogram()[1:])
                    if not n_mask:
                        continue
                    diff = ImageChops.difference(pub.convert("RGB"), b.convert("RGB"))
                    merged = diff.split()[0]
                    for band in diff.split()[1:]:
                        merged = ImageChops.lighter(merged, band)
                    over = merged.point(lambda v: 255 if v > 16 else 0)
                    bad = sum(ImageChops.multiply(over, mask).histogram()[1:])
                    best = min(best, bad / n_mask)
            if best <= 0.10:
                verified += 1
            else:
                failed += 1

    complete = len(semantic) == expected and expected > 0
    ok = complete and not unsupported and not dangling and failed == 0 and verified > 0
    status = "captured" if ok else "partial"
    return {
        "status": status,
        "frames": len(semantic),
        "expected": expected,
        "parts": len(parts),
        "part_uses": scene.stats()["part_uses"],
        "verified": verified,
        "verify_failed": failed,
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
    stats = _autoconvert_one(args.target, targets[args.target], out)
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
            report[name] = _autoconvert_one(name, targets[name], out)
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
    pa.set_defaults(func=cmd_autoconvert)

    pv = sub.add_parser("coverage", help="run the universal converter across the roster")
    pv.add_argument("--targets", help="comma-separated subset (default: all)")
    pv.add_argument("--verbose", action="store_true")
    pv.add_argument("--strict", action="store_true",
                    help="also exit nonzero on partial / needs-seam results")
    pv.set_defaults(func=cmd_coverage)

    pl = sub.add_parser("list", help="list renderable targets")
    pl.set_defaults(func=cmd_list)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
