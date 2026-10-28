"""A bundle includes only declared products and their required references."""
from pathlib import Path
from types import SimpleNamespace
import pytest
from ambition_sprite2d_renderer.artifacts import collect, install


def target():
    return SimpleNamespace(name="body", sheet_files=["body_spritesheet.png", "body_spritesheet.ron"],
        portrait_files=[], install_subdir=None, portrait_install_subdir=None)


def test_parts_and_pages_are_required_but_old_numbered_pages_are_not_copied(tmp_path):
    (tmp_path / "body_spritesheet.png").write_bytes(b"page")
    (tmp_path / "body_spritesheet.ron").write_text('[(images: ["body_spritesheet.png"])]')
    (tmp_path / "body_spritesheet.9.png").write_bytes(b"old page")
    (tmp_path / "body_parts.ron").write_text('(pages: ["body_parts.png", "body_parts_1.png"])')
    (tmp_path / "body_parts.png").write_bytes(b"parts")
    with pytest.raises(ValueError, match="missing page"):
        collect(target(), tmp_path)
    (tmp_path / "body_parts_1.png").write_bytes(b"more parts")
    members = collect(target(), tmp_path)
    assert "body_parts_1.png" in members
    assert "body_spritesheet.9.png" not in members


def test_the_common_installer_does_not_write_through_a_mirror_link(tmp_path):
    source = tmp_path / "render"; source.mkdir()
    (source / "body_spritesheet.png").write_bytes(b"new")
    (source / "body_spritesheet.ron").write_text('[(image: "body_spritesheet.png")]')
    shared = tmp_path / "shared.png"; shared.write_bytes(b"shared")
    dest = tmp_path / "install"; dest.mkdir()
    (dest / "body_spritesheet.png").symlink_to(shared)
    install(target(), source, dest)
    assert shared.read_bytes() == b"shared"
    assert (dest / "body_spritesheet.png").read_bytes() == b"new"
