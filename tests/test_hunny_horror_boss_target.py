from __future__ import annotations

from ambition_sprite2d_renderer.targets.characters import hunny_horror_boss as target


def test_hunny_horror_boss_bindings_name_rows_the_sheet_publishes():
    rows = {name for name, _frames, _duration in target.ROWS}
    for binding, spec in target.ACTOR_METADATA["animation_bindings"].items():
        assert spec["animation"] in rows, binding
