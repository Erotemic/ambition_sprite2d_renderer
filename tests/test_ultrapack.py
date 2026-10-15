"""Tests for ultrapacking (authoring/ultrapack.py): pooling published per-target
sheets into shared uniform pages at a quality tier, and the clean publish
boundary (runtime pages + catalog vs opt-in diagnostics)."""

import json

import yaml
from PIL import Image, ImageDraw

import pytest

from ambition_sprite2d_renderer.authoring.ultrapack import (
    PackPlan,
    pack_tier,
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


def _recolour(sheet_dir, stem):
    page_path = sheet_dir / f"{stem}_spritesheet.png"
    page = Image.open(page_path).convert("RGBA")
    pixels = page.load()
    for y in range(page.height):
        for x in range(page.width):
            r, g, b, a = pixels[x, y]
            if a:
                pixels[x, y] = (255 - r, g, b, a)
    page.save(page_path)


def test_a_page_whose_pixels_did_not_change_is_not_written_again(tmp_path):
    """An edit to one sheet rewrites only the pages that hold its frames:
    encoding a page costs about 5 times its decode."""
    sheets = tmp_path / "in"
    sheets.mkdir()
    for stem in ("alpha", "beta"):
        _write_sheet(sheets, stem, fw=64, fh=64, n_frames=4, cols=2)
    plan = PackPlan(groups={"zone_a": ["alpha"]})
    out = tmp_path / "out"
    write_pack(ultrapack_rendered(sheets, page_size=256, plan=plan), out, name="ultrapack")
    pack = ultrapack_rendered(sheets, page_size=256, plan=plan)
    alpha_page = out / f"ultrapack_{pack.page_groups.index('zone_a')}.png"
    beta_page = out / f"ultrapack_{pack.page_groups.index('shared')}.png"
    before = {page: page.stat().st_mtime_ns for page in (alpha_page, beta_page)}
    alpha_page.touch()  # a write would move the mtime past this
    os_mtime = alpha_page.stat().st_mtime_ns

    _recolour(sheets, "beta")
    pack = ultrapack_rendered(sheets, page_size=256, plan=plan)
    write_pack(pack, out, name="ultrapack")

    assert alpha_page.stat().st_mtime_ns == os_mtime, "the unchanged page was written again"
    assert beta_page.stat().st_mtime_ns != before[beta_page], "the changed page was kept"
    # Control: every page on disk is what a fresh write of this pack gives.
    fresh = tmp_path / "fresh"
    write_pack(pack, fresh, name="ultrapack")
    for page in fresh.glob("*.png"):
        assert Image.open(page).tobytes() == Image.open(out / page.name).tobytes(), page.name


def test_a_pack_with_fewer_pages_leaves_no_stale_page(tmp_path):
    sheets = tmp_path / "in"
    sheets.mkdir()
    for stem in ("alpha", "beta"):
        _write_sheet(sheets, stem, fw=64, fh=64, n_frames=4, cols=2)
    out = tmp_path / "out"
    two = ultrapack_rendered(sheets, page_size=256, plan=PackPlan(groups={"zone_a": ["alpha"]}))
    write_pack(two, out, name="ultrapack")
    assert len(list(out.glob("ultrapack_*.png"))) == len(two.pages) >= 2

    one = ultrapack_rendered(sheets, page_size=256)
    write_pack(one, out, name="ultrapack")
    assert sorted(p.name for p in out.glob("ultrapack_*.png")) == [f"ultrapack_{i}.png" for i in range(len(one.pages))]


def _redraw(sheet_dir, stem, *, shift, hole):
    """Draw each frame of a test sheet again, ``shift`` px to the right in its
    cell, with a transparent ``hole`` in its middle: the frames keep their
    trimmed sizes and change their offsets and some pixels' alpha."""
    page_path = sheet_dir / f"{stem}_spritesheet.png"
    manifest = yaml.safe_load((sheet_dir / f"{stem}_spritesheet.yaml").read_text())
    fw, fh = manifest["frame_width"], manifest["frame_height"]
    page = Image.new("RGBA", Image.open(page_path).size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(page)
    for rect in manifest["rows"][0]["rects"]:
        cx, cy = rect["x"] + shift, rect["y"]
        draw.ellipse((cx + 4, cy + 4, cx + fw - 4 - 2, cy + fh - 4), fill=(200, 40, 90, 255))
        if hole:
            mx, my = cx + fw // 2, cy + fh // 2
            draw.rectangle((mx - 3, my - 3, mx + 3, my + 3), fill=(0, 0, 0, 0))
    page.save(page_path)


def _same_files(left, right):
    names = sorted(p.name for p in left.iterdir())
    assert names == sorted(p.name for p in right.iterdir())
    for name in names:
        assert (left / name).read_bytes() == (right / name).read_bytes(), name


def test_a_tier_whose_changed_sheets_kept_their_sizes_is_patched_to_the_bytes_of_a_full_pack(tmp_path):
    """A recolour or a shading pass draws only the pages that hold the
    changed frames, and writes what a full pack writes. A change in a
    frame's trimmed size packs the tier in full."""
    sheets = tmp_path / "in"
    sheets.mkdir()
    for stem in ("alpha", "beta", "gamma"):
        _write_sheet(sheets, stem, fw=64, fh=64, n_frames=4, cols=2)
    _redraw(sheets, "beta", shift=0, hole=False)
    plan = PackPlan(groups={"zone_a": ["alpha"], "zone_g": ["gamma"]})
    out, state = tmp_path / "out", tmp_path / "state.json"
    how, _ = pack_tier(sheets, out, state, page_size=256, plan=plan)
    assert how.startswith("packed"), how

    def fresh_pack(label):
        fresh = tmp_path / label
        write_pack(ultrapack_rendered(sheets, page_size=256, plan=plan), fresh, name="ultrapack")
        return fresh

    # The same pixels moved 2 px, with a hole: the same trimmed sizes.
    _redraw(sheets, "beta", shift=2, hole=True)
    alpha_page = out / "ultrapack_0.png"
    alpha_mtime = alpha_page.stat().st_mtime_ns
    how, written = pack_tier(sheets, out, state, page_size=256, plan=plan)
    assert how.startswith("patched 1 sheet(s)") and "beta" in how, how
    assert alpha_page not in written and alpha_page.stat().st_mtime_ns == alpha_mtime
    _same_files(out, fresh_pack("fresh_patch"))

    # Nothing changed: nothing is drawn.
    how, written = pack_tier(sheets, out, state, page_size=256, plan=plan)
    assert how.startswith("patched 0 sheet(s)"), how

    # A frame that grew: a new layout, so a full pack.
    _write_sheet(sheets, "beta", fw=72, fh=72, n_frames=4, cols=2)
    how, _ = pack_tier(sheets, out, state, page_size=256, plan=plan)
    assert how.startswith("packed"), how
    _same_files(out, fresh_pack("fresh_grow"))

    # A new sheet: a full pack.
    _write_sheet(sheets, "delta", fw=32, fh=32, n_frames=2, cols=2)
    how, _ = pack_tier(sheets, out, state, page_size=256, plan=plan)
    assert how.startswith("packed"), how


def test_a_tier_with_no_state_or_another_layout_on_disk_is_packed_in_full(tmp_path):
    """The state is the only proof of what the pages on disk are. A run cut
    short leaves none, and a catalog written by another run does not match
    it: each is packed in full."""
    sheets = tmp_path / "in"
    sheets.mkdir()
    for stem in ("alpha", "beta"):
        _write_sheet(sheets, stem, fw=64, fh=64, n_frames=4, cols=2)
    _redraw(sheets, "beta", shift=0, hole=False)
    out, state = tmp_path / "out", tmp_path / "state.json"
    pack_tier(sheets, out, state, page_size=256)
    # Same sizes: only the state can refuse the patch.
    _redraw(sheets, "beta", shift=2, hole=False)
    # Another run wrote the tier with other numbers.
    write_pack(ultrapack_rendered(sheets, page_size=512), out, name="ultrapack")
    how, _ = pack_tier(sheets, out, state, page_size=256)
    assert how.startswith("packed"), how
    state.unlink()
    _redraw(sheets, "beta", shift=0, hole=True)
    how, _ = pack_tier(sheets, out, state, page_size=256)
    assert how.startswith("packed"), how


def test_a_tier_pack_cut_short_leaves_no_state(tmp_path, monkeypatch):
    """A full pack that stops after it wrote some pages leaves pages of a new
    layout under the old catalog's state. No state is left, so the next run
    does not patch those pages."""
    from ambition_sprite2d_renderer.authoring import ultrapack as module

    sheets = tmp_path / "in"
    sheets.mkdir()
    for stem in ("alpha", "beta"):
        _write_sheet(sheets, stem, fw=64, fh=64, n_frames=4, cols=2)
    out, state = tmp_path / "out", tmp_path / "state.json"
    pack_tier(sheets, out, state, page_size=256)
    assert state.is_file()

    def stops(*_args, **_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(module, "write_pack", stops)
    _write_sheet(sheets, "beta", fw=72, fh=72, n_frames=4, cols=2)
    with pytest.raises(KeyboardInterrupt):
        pack_tier(sheets, out, state, page_size=256)
    assert not state.exists(), "a pack cut short left its state"


def test_a_tier_knows_its_unchanged_pages_by_digest_and_does_not_decode_them(tmp_path, monkeypatch):
    """A full pack keeps a page whose file still holds the pixels it wrote,
    known by the digest in its state. A page file changed since then is
    decoded and compared, and written again when its pixels differ."""
    from ambition_sprite2d_renderer.authoring import ultrapack as module

    sheets = tmp_path / "in"
    sheets.mkdir()
    for stem in ("alpha", "beta"):
        _write_sheet(sheets, stem, fw=64, fh=64, n_frames=4, cols=2)
    plan = PackPlan(groups={"zone_a": ["alpha"]})
    out, state = tmp_path / "out", tmp_path / "state.json"
    pack_tier(sheets, out, state, page_size=256, plan=plan)
    alpha_page = out / "ultrapack_0.png"
    alpha_mtime = alpha_page.stat().st_mtime_ns

    decoded = []
    real = module._holds_pixels
    monkeypatch.setattr(module, "_holds_pixels", lambda path, img: decoded.append(path.name) or real(path, img))
    # beta grows: a full pack, and alpha's page has the same pixels.
    _write_sheet(sheets, "beta", fw=72, fh=72, n_frames=4, cols=2)
    how, _ = pack_tier(sheets, out, state, page_size=256, plan=plan)
    assert how.startswith("packed"), how
    assert "ultrapack_0.png" not in decoded, decoded
    assert alpha_page.stat().st_mtime_ns == alpha_mtime, "the unchanged page was written again"

    # Something else wrote alpha's page: its digest is not trusted.
    Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(alpha_page)
    _write_sheet(sheets, "beta", fw=64, fh=64, n_frames=4, cols=2)
    pack_tier(sheets, out, state, page_size=256, plan=plan)
    assert "ultrapack_0.png" in decoded, decoded
    fresh = tmp_path / "fresh"
    write_pack(ultrapack_rendered(sheets, page_size=256, plan=plan), fresh, name="ultrapack")
    _same_files(out, fresh)
