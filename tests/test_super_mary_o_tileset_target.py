from __future__ import annotations

from pathlib import Path

import yaml

from ambition_sprite2d_renderer.targets.tiles import super_mary_o_tileset


def test_super_mary_o_tileset_renders(tmp_path: Path) -> None:
    outputs = super_mary_o_tileset.render(tmp_path)
    assert outputs
    png_path = tmp_path / f"{super_mary_o_tileset.TARGET_NAME}.png"
    yaml_path = tmp_path / f"{super_mary_o_tileset.TARGET_NAME}.yaml"
    preview_path = tmp_path / f"{super_mary_o_tileset.TARGET_NAME}_preview.png"
    assert png_path.exists()
    assert yaml_path.exists()
    assert preview_path.exists()

    manifest = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    keys = [tile["key"] for tile in manifest["tiles"]]
    assert "brick_plain" in keys
    assert "pipe_cap_left" in keys
    assert manifest["tile_count"] == len(super_mary_o_tileset.TILES)
