"""The cheap memory check before a sheet page is made (``core/memory_budget.py``)."""

import pytest

from ambition_sprite2d_renderer.core import memory_budget as mb


@pytest.fixture
def meminfo(tmp_path, monkeypatch):
    def set_available(gib):
        path = tmp_path / "meminfo"
        path.write_text(f"MemTotal: 18000000 kB\nMemAvailable: {int(gib * (1 << 20))} kB\n", encoding="ascii")
        monkeypatch.setattr(mb, "_MEMINFO", str(path))

    monkeypatch.setattr(mb, "RESERVE_BYTES", 1 << 30)
    return set_available


def test_a_page_that_fits_passes(meminfo):
    meminfo(8.0)
    mb.require_image((15040, 11968), "giant page")  # 0.67 GiB


def test_a_page_that_would_leave_too_little_names_itself(meminfo):
    meminfo(1.5)
    with pytest.raises(mb.OutOfImageMemory, match=r"giant page \(15040x11968 RGBA\)"):
        mb.require_image((15040, 11968), "giant page")


def test_pages_made_together_are_counted_together(meminfo):
    meminfo(3.0)
    mb.require_images([(15040, 11968)] * 2, "layers")
    with pytest.raises(mb.OutOfImageMemory, match="4 RGBA page"):
        mb.require_images([(15040, 11968)] * 4, "layers")


def test_small_images_and_unknown_memory_are_not_checked(tmp_path, monkeypatch):
    monkeypatch.setattr(mb, "_MEMINFO", str(tmp_path / "missing"))
    mb.require_image((15040, 11968), "anything")
    assert mb.available_bytes() is None
    monkeypatch.setattr(mb, "available_bytes", lambda: 0)
    mb.require_image((256, 256), "a frame")
