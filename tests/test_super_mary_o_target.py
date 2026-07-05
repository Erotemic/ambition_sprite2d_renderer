from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ambition_sprite2d_renderer.targets.characters import super_mary_o


@pytest.mark.slow_render
def test_super_mary_o_family_renders(tmp_path: Path) -> None:
    renderers = [
        super_mary_o.render_super_mary_o,
        super_mary_o.render_super_mary_o_tall,
        super_mary_o.render_super_mary_o_fire,
    ]
    names = [
        super_mary_o.SHORT_FORM.target_name,
        super_mary_o.TALL_FORM.target_name,
        super_mary_o.FIRE_FORM.target_name,
    ]

    for renderer, name in zip(renderers, names):
        out_dir = tmp_path / name
        outputs = renderer(out_dir)
        assert outputs
        assert (out_dir / f"{name}_spritesheet.png").exists()
        assert (out_dir / f"{name}_spritesheet.yaml").exists()
        assert (out_dir / f"{name}_actor.ron").exists()
        manifest = yaml.safe_load((out_dir / f"{name}_spritesheet.yaml").read_text(encoding="utf-8"))
        rows = manifest["rows"]
        row_names = [row["animation"] for row in rows]
        frame_counts = [row["frame_count"] for row in rows]
        assert row_names == ["idle", "dead", "walk", "jump", "skid", "climb", "swim"]
        assert frame_counts == [1, 1, 3, 1, 1, 2, 4]
