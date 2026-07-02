"""Tests for ultrapacking (authoring/ultrapack.py): pooling published per-target
sheets into shared uniform pages at a quality tier, and the clean publish
boundary (runtime pages + catalog vs opt-in diagnostics)."""

import json

import yaml
from PIL import Image, ImageDraw

from ambition_sprite2d_renderer.authoring.ultrapack import (
    ultrapack_rendered,
    write_debug_views,
    write_pack,
)


def _write_sheet(sheet_dir, stem, *, fw, fh, n_frames, cols):
    """Write a minimal published sheet (PNG page + YAML manifest) shaped like the
    renderer's real output: a grid of `n_frames` opaque blobs, one manifest row."""
    rows = (n_frames + cols - 1) // cols
    page = Image.new("RGBA", (fw * cols, fh * rows), (0, 0, 0, 0))
    draw = ImageDraw.Draw(page)
    rects = []
    for i in range(n_frames):
        cx, cy = (i % cols) * fw, (i // cols) * fh
        draw.ellipse((cx + 4, cy + 4, cx + fw - 4, cy + fh - 4), fill=(40, 160, 90, 255))
        # Manifest rects are the packed rect within the page + trim offset. Here
        # the "packed" rect is just the full frame cell (no trim), off = (0, 0).
        rects.append({"x": cx, "y": cy, "w": fw, "h": fh, "off": [0, 0]})
    page.save(sheet_dir / f"{stem}_spritesheet.png")
    manifest = {
        "frame_width": fw,
        "frame_height": fh,
        "image": f"{stem}_spritesheet.png",
        "rows": [{"animation": "Idle", "duration_ms": 100, "page": 0, "rects": rects}],
    }
    (sheet_dir / f"{stem}_spritesheet.yaml").write_text(yaml.safe_dump(manifest))


def test_pools_published_sheets_into_shared_pages(tmp_path):
    _write_sheet(tmp_path, "alpha", fw=64, fh=64, n_frames=6, cols=3)
    _write_sheet(tmp_path, "beta", fw=48, fh=80, n_frames=4, cols=2)

    pack = ultrapack_rendered(tmp_path, page_size=512)

    # Every frame from both targets is in the pool, keyed by (target, anim, idx).
    assert {f.target for f in pack.frames} == {"alpha", "beta"}
    assert len(pack.frames) == 10
    assert pack.scale == 1.0
    # Frames from different targets can share a page (that's the whole point).
    assert len(pack.pages) >= 1
    # Logical size is preserved at base scale.
    alpha = next(f for f in pack.frames if f.target == "alpha")
    assert (alpha.src_w, alpha.src_h) == (64, 64)


def test_quality_scale_shrinks_logical_frames(tmp_path):
    _write_sheet(tmp_path, "alpha", fw=64, fh=64, n_frames=4, cols=2)

    base = ultrapack_rendered(tmp_path, scale=1.0, page_size=512)
    quarter = ultrapack_rendered(tmp_path, scale=0.25, page_size=512)

    b = next(f for f in base.frames if f.index == 0)
    q = next(f for f in quarter.frames if f.index == 0)
    assert (b.src_w, b.src_h) == (64, 64)
    assert (q.src_w, q.src_h) == (16, 16)  # 64 * 0.25
    assert quarter.scale == 0.25


def test_min_frame_px_floors_potato_frames(tmp_path):
    _write_sheet(tmp_path, "tiny", fw=64, fh=64, n_frames=2, cols=2)
    # 64 * 1/16 = 4, but the floor keeps every side at >= 8.
    potato = ultrapack_rendered(tmp_path, scale=1.0 / 16.0, min_frame_px=8, page_size=256)
    f = potato.frames[0]
    assert f.src_w >= 8 and f.src_h >= 8


def test_write_pack_is_clean_and_debug_views_are_opt_in(tmp_path):
    sheet_dir = tmp_path / "in"
    sheet_dir.mkdir()
    _write_sheet(sheet_dir, "alpha", fw=64, fh=64, n_frames=4, cols=2)

    pack = ultrapack_rendered(sheet_dir, page_size=512)
    out = tmp_path / "out"
    written = write_pack(pack, out, name="ultrapack")

    # Runtime output: page PNGs + one catalog JSON, no diagnostics dir.
    assert not (out / "diagnostics").exists()
    names = {p.name for p in out.iterdir()}
    assert "ultrapack.json" in names
    assert any(n.endswith(".png") for n in names)
    catalog = json.loads((out / "ultrapack.json").read_text())
    assert catalog["targets"]["alpha"]["Idle"]  # frames recorded under target/anim

    # Diagnostics are opt-in and land ONLY under diagnostics/.
    diag = write_debug_views(pack, out, name="ultrapack")
    assert (out / "diagnostics").is_dir()
    assert all("diagnostics" in str(p) for p in diag)
    assert (out / "diagnostics" / "ultrapack_report.txt").exists()
