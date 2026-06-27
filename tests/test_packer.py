"""Tests for the alpha-trim + MaxRects atlas packer (authoring/packer.py)."""
from PIL import Image, ImageDraw

from ambition_sprite2d_renderer.authoring.packer import FrameInput, pack_frames


def _blob(w, h, cx, cy, r, col=(60, 130, 200, 255)):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    return im


def test_trim_and_pack_is_lossless_and_reclaims_space():
    frames = [
        FrameInput(key=("a", i), image=_blob(384, 529, 192 + i, 264, 28), logical_size=(384, 529))
        for i in range(8)
    ]
    res = pack_frames(frames, max_dim=4096, padding=2, trim=True)
    # All frames placed, every placement carries trim geometry.
    assert set(res.placements) == {("a", i) for i in range(8)}
    # Packed area is a fraction of the logical area (frames are ~99% transparent).
    logical = 384 * 529 * 8
    packed = sum(p.size[0] * p.size[1] for p in res.pages)
    assert packed < logical * 0.3, (packed, logical)
    # Reconstructing each frame from its page + offset reproduces the source
    # (pack_frames asserts this internally; re-check here for documentation).
    for fr in frames:
        p = res.placements[fr.key]
        recon = Image.new("RGBA", (p.src_w, p.src_h), (0, 0, 0, 0))
        sub = res.pages[p.page].crop((p.x, p.y, p.x + p.w, p.y + p.h))
        recon.alpha_composite(sub, (p.off_x, p.off_y))
        assert recon.tobytes() == fr.image.tobytes()


def test_cross_target_frames_share_pages():
    frames = []
    for t, (w, h) in enumerate([(384, 529), (128, 95)]):
        for i in range(4):
            frames.append(FrameInput(key=(t, i), image=_blob(w, h, w // 2, h // 2, 20), logical_size=(w, h)))
    res = pack_frames(frames, max_dim=4096, padding=1, trim=True)
    pages_t0 = {res.placements[(0, i)].page for i in range(4)}
    pages_t1 = {res.placements[(1, i)].page for i in range(4)}
    assert pages_t0 & pages_t1, "different targets should be able to share a page"


def test_multipage_when_capped_small():
    frames = [
        FrameInput(key=i, image=_blob(200, 200, 100, 100, 90), logical_size=(200, 200))
        for i in range(6)
    ]
    # Cap so only ~2 trimmed (~182px) rects fit per row/page → forces multiple pages.
    res = pack_frames(frames, max_dim=256, padding=1, trim=True)
    assert len(res.pages) > 1
    for p in res.pages:
        assert p.size[0] <= 256 and p.size[1] <= 256


def test_fully_transparent_frame_is_handled():
    frames = [FrameInput(key=0, image=Image.new("RGBA", (128, 128), (0, 0, 0, 0)), logical_size=(128, 128))]
    res = pack_frames(frames, max_dim=512, trim=True)
    p = res.placements[0]
    # Empty frame collapses to a 1x1 placeholder at the origin; reconstruction
    # is still a fully transparent logical frame.
    assert (p.w, p.h) == (1, 1)
    assert (p.src_w, p.src_h) == (128, 128)


def test_untrimmed_passthrough_keeps_full_frames():
    frames = [FrameInput(key=i, image=_blob(64, 64, 32, 32, 20), logical_size=(64, 64)) for i in range(3)]
    res = pack_frames(frames, max_dim=512, padding=0, trim=False)
    for fr in frames:
        p = res.placements[fr.key]
        assert (p.w, p.h) == (64, 64)
        assert (p.off_x, p.off_y) == (0, 0)
