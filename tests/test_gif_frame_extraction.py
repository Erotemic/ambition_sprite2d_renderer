"""GIF frame extraction from packed AND unpacked sprite sheets.

Regression for the paged-sheet bug: ``write_animation_gifs_for_target``
used to crop every frame from the base image, so frames living on a
packed sheet's ``.1.png`` / ``.2.png`` pages (addressed by ``fpage``)
came out as garbage. The reconstruction must:

- read each frame from ITS OWN page (``fpage`` packed / ``page`` grid),
- re-inflate an alpha-trimmed rect (``off`` + sub-frame ``w``/``h``) back
  onto the logical ``frame_width × frame_height`` canvas so the character
  stays anchored,
- and behave identically for the untrimmed grid layout (``w == fw``,
  ``page`` index, no ``off``).
"""

from __future__ import annotations

from PIL import Image

from ambition_sprite2d_renderer.cli.commands import (
    _frame_from_rect,
    _manifest_page_images,
)

FW, FH = 40, 60
RED = (220, 40, 40, 255)
BLUE = (40, 80, 220, 255)


def _solid(size, color):
    return Image.new("RGBA", size, color)


def test_packed_frame_reads_its_own_page_and_reinflates(tmp_path):
    """A trimmed rect on page 2 must be cropped from page 2 and pasted at
    its trim offset onto a full logical frame."""
    # Three pages; only page 2 carries the frame's pixels.
    (tmp_path / "s.png").write_bytes(b"")  # base (page 0) — unused here
    _solid((64, 64), (0, 0, 0, 0)).save(tmp_path / "s.png")
    _solid((64, 64), (0, 0, 0, 0)).save(tmp_path / "s.1.png")
    page2 = _solid((64, 64), (0, 0, 0, 0))
    # a 10x12 red block sitting at (5, 7) on page 2
    page2.paste(RED, (5, 7, 15, 19))
    page2.save(tmp_path / "s.2.png")

    manifest = {
        "image": "s.png",
        "images": ["s.png", "s.1.png", "s.2.png"],
        "frame_width": FW,
        "frame_height": FH,
    }
    mp = tmp_path / "s_spritesheet.yaml"
    pages = _manifest_page_images(mp, manifest)
    assert set(pages) == {0, 1, 2}

    rect = {"x": 5, "y": 7, "w": 10, "h": 12, "fpage": 2, "off": (8, 9)}
    frame = _frame_from_rect(rect, pages, FW, FH)
    assert frame.size == (FW, FH)  # re-inflated to the logical frame
    # the block lands at the trim offset, not at the packed (x, y)
    assert frame.getpixel((8, 9)) == RED
    assert frame.getpixel((17, 20)) == RED  # 8+10-1, 9+12-1
    assert frame.getpixel((0, 0))[3] == 0  # rest is transparent
    # and it must NOT have been read from page 0 (which is empty)
    assert frame.getpixel((5, 7)) != RED or (8, 9) == (5, 7)


def test_grid_frame_is_returned_whole(tmp_path):
    """The untrimmed grid layout: single image, ``page`` index, full-cell
    ``w``/``h``, no ``off`` — the rect is returned as-is."""
    sheet = _solid((100 + FW * 3, FH * 2), (0, 0, 0, 0))
    # row 0, frame 1 cell at x=100+FW, y=0
    sheet.paste(BLUE, (100 + FW, 0, 100 + FW + FW, FH))
    sheet.save(tmp_path / "g.png")

    manifest = {"image": "g.png", "frame_width": FW, "frame_height": FH}
    mp = tmp_path / "g_spritesheet.yaml"
    pages = _manifest_page_images(mp, manifest)
    assert set(pages) == {0}

    rect = {"x": 100 + FW, "y": 0, "w": FW, "h": FH, "page": 0}
    frame = _frame_from_rect(rect, pages, FW, FH)
    assert frame.size == (FW, FH)
    assert frame.getpixel((0, 0)) == BLUE
    assert frame.getpixel((FW - 1, FH - 1)) == BLUE


def test_missing_page_falls_back_without_crashing(tmp_path):
    """A rect pointing at an unpublished page degrades to page 0 rather
    than throwing (partial publishes still yield the pages they have)."""
    _solid((FW, FH), RED).save(tmp_path / "s.png")
    manifest = {"image": "s.png", "frame_width": FW, "frame_height": FH}
    mp = tmp_path / "s_spritesheet.yaml"
    pages = _manifest_page_images(mp, manifest)
    rect = {"x": 0, "y": 0, "w": FW, "h": FH, "fpage": 5}
    frame = _frame_from_rect(rect, pages, FW, FH)
    assert frame is not None and frame.getpixel((0, 0)) == RED
