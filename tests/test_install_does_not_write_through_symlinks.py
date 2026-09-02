"""Publishing a rendered sheet must not write into a symlinked destination.

The game repo's `scripts/mirror_assets_for_worktree.py` points every generated
asset in a git worktree at the MAIN checkout's copy, file by file, so that a
regenerated sheet lands as a real file in the worktree and main never sees it.

⛔⛔ `shutil.copy2` OPENS THE DESTINATION FOR WRITING, AND AN OPEN-FOR-WRITE
FOLLOWS A SYMLINK. Measured 2026-09-02: copying onto a symlink changed the
TARGET's bytes and left the link in place. So `install()` from a worktree
silently rewrote the assets every other session builds and gates from — while
the mirror's own docstring promised that could not happen.
"""

from __future__ import annotations

import os
import shutil

from ambition_sprite2d_renderer.registry import discovery


def test_a_plain_copy2_really_does_follow_a_symlink(tmp_path):
    """⭐ THE PREMISE. Without it the test below could pass on a system where
    copies never followed links, pinning nothing."""
    shared = tmp_path / "main.png"
    shared.write_text("SHARED")
    link = tmp_path / "work.png"
    os.symlink(shared, link)
    fresh = tmp_path / "fresh.png"
    fresh.write_text("FRESH")

    shutil.copy2(fresh, link)
    assert shared.read_text() == "FRESH", "premise: copy2 writes through the link"


def test_copy_sheet_files_replaces_the_link_not_the_shared_file(tmp_path):
    render_dir = tmp_path / "render"
    dest = tmp_path / "dest"
    shared = tmp_path / "shared"
    for d in (render_dir, dest, shared):
        d.mkdir()

    (render_dir / "x_spritesheet.png").write_text("FRESH")
    (shared / "x_spritesheet.png").write_text("SHARED")
    os.symlink(shared / "x_spritesheet.png", dest / "x_spritesheet.png")

    discovery._copy_sheet_files(["x_spritesheet.png"], render_dir, dest)

    assert (shared / "x_spritesheet.png").read_text() == "SHARED", (
        "the MAIN checkout's asset must be untouched by a worktree publish"
    )
    assert (dest / "x_spritesheet.png").read_text() == "FRESH"
    assert not (dest / "x_spritesheet.png").is_symlink(), (
        "the worktree now owns a real file, which is what the mirror promises"
    )


def test_an_ordinary_destination_is_still_overwritten(tmp_path):
    """The guard must not turn a normal republish into a no-op."""
    render_dir = tmp_path / "render"
    dest = tmp_path / "dest"
    render_dir.mkdir()
    dest.mkdir()
    (render_dir / "y_spritesheet.png").write_text("FRESH")
    (dest / "y_spritesheet.png").write_text("STALE")

    discovery._copy_sheet_files(["y_spritesheet.png"], render_dir, dest)
    assert (dest / "y_spritesheet.png").read_text() == "FRESH"
