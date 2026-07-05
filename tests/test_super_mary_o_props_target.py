from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ambition_sprite2d_renderer.targets.props import super_mary_o_props


@pytest.mark.slow_render
def test_super_mary_o_props_render(tmp_path: Path) -> None:
    for name, spec in super_mary_o_props.SPECS.items():
        out_dir = tmp_path / name
        outputs = super_mary_o_props.TARGETS[name]["render"](out_dir)
        assert outputs
        assert (out_dir / f"{name}_spritesheet.png").exists()
        assert (out_dir / f"{name}_spritesheet.yaml").exists()
        manifest = yaml.safe_load((out_dir / f"{name}_spritesheet.yaml").read_text(encoding="utf-8"))
        row_names = [row["animation"] for row in manifest["rows"]]
        assert row_names[0] == spec.rows[0][0]
        assert manifest["frame_width"] == super_mary_o_props.FRAME[0]
        assert manifest["frame_height"] == super_mary_o_props.FRAME[1]
