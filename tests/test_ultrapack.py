"""Tests for ultrapacking (authoring/ultrapack.py): pooling published per-target
sheets into shared uniform pages at a quality tier, and the clean publish
boundary (runtime pages + catalog vs opt-in diagnostics)."""

import json

import yaml
from PIL import Image, ImageDraw

import pytest

from ambition_sprite2d_renderer.authoring.ultrapack import (
    PackPlan,
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


def test_differential_pack_reconstruction_is_lossless(tmp_path):
    """W1: the pack pixels ARE the sheet pixels. Reconstruct every logical frame
    twice — once from the source per-target sheet, once from the packed shared
    pages via the catalog — and require byte-equality at base scale."""
    import json as _json

    from ambition_sprite2d_renderer.authoring.ultrapack import (
        _read_sheet_frames,
        _reconstruct_logical,
    )

    sheet_dir = tmp_path / "sheets"
    sheet_dir.mkdir()
    _write_sheet(sheet_dir, "alpha", fw=64, fh=64, n_frames=6, cols=3)
    _write_sheet(sheet_dir, "beta", fw=48, fh=80, n_frames=4, cols=2)

    pack = ultrapack_rendered(sheet_dir, page_size=512)
    out = tmp_path / "pack"
    write_pack(pack, out, name="ultrapack")
    catalog = _json.loads((out / "ultrapack.json").read_text())
    pages = [Image.open(out / name).convert("RGBA") for name in catalog["pages"]]

    checked = 0
    for stem in ("alpha", "beta"):
        source = {
            (meta["animation"], meta["index"]): fi.image
            for fi, meta in _read_sheet_frames(sheet_dir, stem, scale=1.0, min_px=1)
        }
        for anim, frames in catalog["targets"][stem].items():
            for fr in frames:
                packed = _reconstruct_logical(
                    pages[fr["page"]],
                    {"x": fr["x"], "y": fr["y"], "w": fr["w"], "h": fr["h"], "off": fr["off"]},
                    fr["src"][0],
                    fr["src"][1],
                )
                assert packed.tobytes() == source[(anim, fr["index"])].tobytes(), (
                    stem,
                    anim,
                    fr["index"],
                )
                checked += 1
    assert checked == 10  # every frame of both targets was compared


def test_pack_plan_groups_isolate_pages(tmp_path):
    """W7: a plan group's frames land ONLY on that group's pages; ungrouped
    targets share the general pool; the catalog records per-page groups."""
    import json as _json

    for stem in ("alpha", "beta", "gamma"):
        _write_sheet(tmp_path, stem, fw=64, fh=64, n_frames=4, cols=2)

    plan = PackPlan(groups={"zone_a": ["alpha"]})
    pack = ultrapack_rendered(tmp_path, page_size=256, plan=plan)

    assert len(pack.page_groups) == len(pack.pages)
    # Locality guarantee: every alpha frame on a zone_a page; every other
    # frame on a shared page; no page mixes groups.
    for f in pack.frames:
        group = pack.page_groups[f.page]
        assert group == ("zone_a" if f.target == "alpha" else "shared"), (f.target, group)

    out = tmp_path / "out"
    write_pack(pack, out, name="ultrapack")
    catalog = _json.loads((out / "ultrapack.json").read_text())
    assert catalog["page_groups"] == pack.page_groups
    assert set(catalog["page_groups"]) == {"zone_a", "shared"}


def test_pack_plan_rejects_reserved_and_duplicate_stems(tmp_path):
    with pytest.raises(ValueError):
        PackPlan(groups={"shared": ["alpha"]})
    with pytest.raises(ValueError):
        PackPlan(groups={"a": ["x"], "b": ["x"]})


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
