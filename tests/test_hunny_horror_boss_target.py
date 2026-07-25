from __future__ import annotations

from ambition_sprite2d_renderer.targets.characters import hunny_horror_boss as target


def test_hunny_horror_boss_has_expanded_boss_move_set():
    row_names = [name for name, _frames, _duration in target.ROWS]
    assert row_names == [
        "rest",
        "walk",
        "swipe",
        "maul",
        "slam",
        "roar",
        "stagger",
        "death",
    ]

    bindings = target.ACTOR_METADATA["animation_bindings"]
    assert bindings["action.melee.primary"]["animation"] == "swipe"
    assert bindings["action.melee.heavy"]["animation"] == "maul"
    assert bindings["action.special.primary"]["animation"] == "slam"
    assert bindings["action.special.secondary"]["animation"] == "roar"
    assert bindings["action.special.roar"]["animation"] == "roar"
    assert bindings["damage.hit"]["animation"] == "stagger"


def test_hunny_horror_boss_rows_match_rig_clip_metadata():
    doc = target.load_doc()
    expected = {name: (frames, duration) for name, frames, duration in target.ROWS}
    assert set(doc.clips) >= set(expected)
    for name, (frames, duration) in expected.items():
        clip = doc.clips[name]
        assert int(clip["frames"]) == frames
        assert int(clip["duration_ms"]) == duration
        assert clip.get("channels"), name
        mid_time = doc.frame_time(name, max(0, frames // 2), frames)
        assert 0.0 <= mid_time <= 1.0


def test_hunny_horror_boss_boss_channels_hide_the_monster_until_attacks():
    doc = target.load_doc()
    parts = {part["name"]: part for part in doc.parts}
    assert parts["teeth_upper"]["opacity_channel"] == "teeth_vis"
    assert parts["teeth_lower"]["opacity_channel"] == "teeth_vis"
    assert parts["claws_l"]["opacity_channel"] == "claw_vis"
    assert parts["claws_r"]["opacity_channel"] == "claw_vis"
    assert parts["roar_sound"]["opacity_channel"] == "sound_vis"

    assert doc.clips["rest"]["channels"]["eye_glow"]["expr"] == "0"
    assert doc.clips["walk"]["channels"]["eye_glow"]["expr"] == "0"
    assert "teeth_vis" in doc.clips["roar"]["channels"]
    assert "sound_vis" in doc.clips["roar"]["channels"]
    assert "claw_vis" in doc.clips["swipe"]["channels"]
    assert "claw_vis" in doc.clips["maul"]["channels"]
    assert "claw_vis" not in doc.clips["slam"]["channels"]
