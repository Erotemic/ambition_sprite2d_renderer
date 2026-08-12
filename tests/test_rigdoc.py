"""Tests for rig documents (rigdoc): channels, rendering, IK, export,
and auto-registration of targets/characters/rigged/ documents."""

from __future__ import annotations

from pathlib import Path

import pytest

from ambition_sprite2d_renderer.authoring.rigdoc import (
    RigDocument,
    parse_color,
    part_visible,
    render_sheet_for_doc,
    sample_channel_spec,
    visible_parts,
)

TEMPLATE = (
    Path(__file__).resolve().parent.parent
    / "ambition_sprite2d_renderer"
    / "data"
    / "rig_templates"
    / "player_robot_fable.rig.json"
)


@pytest.fixture()
def doc() -> RigDocument:
    return RigDocument.load(TEMPLATE)


NOETHER = (
    Path(__file__).resolve().parent.parent
    / "ambition_sprite2d_renderer"
    / "targets"
    / "characters"
    / "rigged"
    / "noether.rig.json"
)


class TestFeatureToggles:
    """Optional-part customization: a part tagged with a `feature` only
    renders when the doc's `features` map allows it (default on)."""

    def test_part_visible_defaults_and_toggles(self):
        plain = {"name": "torso"}
        pin = {"name": "pin", "feature": "hairpin"}
        assert part_visible(plain, {}) is True              # untagged: always on
        assert part_visible(pin, {}) is True                # unlisted feature: on
        assert part_visible(pin, {"hairpin": True}) is True
        assert part_visible(pin, {"hairpin": False}) is False

    def test_visible_parts_drops_disabled_and_keeps_z_order(self):
        parts = [
            {"name": "b", "z": 2},
            {"name": "pin", "z": 5, "feature": "hairpin"},
            {"name": "a", "z": 1},
        ]
        out = [p["name"] for p in visible_parts(parts, {"hairpin": False})]
        assert out == ["a", "b"]  # pin dropped; remaining sorted by z

    def test_sprite_tuning_flows_to_ron(self, tmp_path):
        """A rig's sprite_tuning is emitted to the RON's tuning field so the
        runtime uses it for in-game size instead of the DEFAULT fallback."""
        doc = RigDocument.new_empty("tuned")
        doc.data["sprite_tuning"] = {"collision_scale": 2.0, "frame_sample_inset": 1}
        render_sheet_for_doc(doc, tmp_path)
        ron = (tmp_path / "tuned_spritesheet.ron").read_text()
        assert "tuning: Some((" in ron
        assert "collision_scale: 2.0" in ron

    def test_render_scale_increases_resolution_not_in_game_size(self, tmp_path):
        """render_scale multiplies the texture's pixels (crisper, no upscaling)
        while the aspect ratio — all the in-game size derives from — is held."""
        doc = RigDocument.new_empty("res")

        import yaml as _yaml

        def frame_dims(scale):
            doc.frame["render_scale"] = scale
            sub = tmp_path / f"s{scale}"
            sub.mkdir()
            render_sheet_for_doc(doc, sub)
            data = _yaml.safe_load((sub / "res_spritesheet.yaml").read_text())
            return data["frame_width"], data["frame_height"]

        w1, h1 = frame_dims(1)
        w2, h2 = frame_dims(2)
        assert w2 > w1 and h2 > h1, "2x render_scale yields more native pixels"
        # Aspect (what in-game size uses) is preserved within rounding.
        assert abs((w2 / h2) - (w1 / h1)) < 0.06

    def test_noether_is_tall_and_hi_res(self):
        """Emmy ships taller (collision_scale > the 1.5 fallback) and at 2x
        render resolution so she isn't pixelated in game."""
        emmy = RigDocument.load(NOETHER)
        assert emmy.sprite_tuning.get("collision_scale", 1.5) > 1.5
        assert emmy.frame.get("render_scale", 1) >= 2

    def test_noether_hairpin_is_present_and_rigid(self):
        """Emmy's hairpin reads as a hairpin (on) and is RIGID: bound to the
        `head` bone, never the bobbing `antenna` channel that made it wave."""
        emmy = RigDocument.load(NOETHER)
        assert emmy.features.get("hairpin") is True
        pin_parts = [p for p in emmy.parts if p["name"].startswith("pin_")]
        assert pin_parts, "hairpin parts should exist"
        for p in pin_parts:
            assert p["bone"] == "head", f"{p['name']} must be rigid (head-bound)"
            assert p.get("feature") == "hairpin"
        visible = {p["name"] for p in visible_parts(emmy.parts, emmy.features)}
        assert {"pin_shaft", "pin_bead"} <= visible
        # Toggling the feature off still removes it (customization seam intact).
        assert not ({"pin_shaft", "pin_bead"} & {
            p["name"] for p in visible_parts(emmy.parts, {"hairpin": False})
        })


class TestChannelSpecs:
    def test_const_expr_keys(self):
        assert sample_channel_spec({"const": 3.5}, 0.7, True) == 3.5
        assert sample_channel_spec({"expr": "2*t"}, 0.25, False) == pytest.approx(0.5)
        spec = {"keys": [[0.0, 0.0, "linear"], [1.0, 10.0, "linear"]]}
        assert sample_channel_spec(spec, 0.5, False) == pytest.approx(5.0)

    def test_expr_rejects_builtins(self):
        with pytest.raises(Exception):
            sample_channel_spec({"expr": "__import__('os')"}, 0.0, True)

    def test_parse_color(self):
        pal = {"shell": "#FDFDFB"}
        assert parse_color("shell", pal) == (253, 253, 251, 255)
        assert parse_color("#FF000080", pal) == (255, 0, 0, 128)
        assert parse_color("#00FF00", pal, opacity=0.5) == (0, 255, 0, 127)
        assert parse_color(None, pal) is None


class TestTemplateDocument:
    def test_loads_and_lists_rows(self, doc):
        assert doc.name == "player_robot_fable_rig"
        assert [r[0] for r in doc.rows()] == ["idle", "walk", "slash"]

    def test_render_frames_all_clips(self, doc):
        for anim, frames, _ in doc.rows():
            img = doc.render_frame(anim, 0, frames)
            assert img.size == (128, 128)
            assert img.getchannel("A").getbbox() is not None

    def test_ik_feet_stay_on_ground_in_walk(self, doc):
        gy = doc.frame["ground_y"]
        ankle_h = doc.frame["ankle_h"]
        for side, stance in (("near_foot", (0.1, 0.35)), ("far_foot", (0.6, 0.85))):
            for t in (stance[0], (stance[0] + stance[1]) / 2, stance[1]):
                world, _ = doc.solve("walk", t)
                ankle = world[side].origin
                assert ankle[1] == pytest.approx(gy - ankle_h, abs=0.05), (side, t)

    def test_ik_bend_channel_can_change_joint_side_per_pose(self, doc):
        doc.data["ik_chains"] = [
            {
                "upper": "near_arm_u",
                "lower": "near_arm_l",
                "channel_prefix": "near_hand",
                "rest_x": 0.0,
                "rest_y": -32.0,
                "bend": -1.0,
            }
        ]
        doc.data["clips"]["bend_negative"] = {
            "loop": False,
            "frames": 1,
            "duration_ms": 0,
            "channels": {
                "near_hand_x": {"const": 0.0},
                "near_hand_y": {"const": -32.0},
                "near_hand_bend": {"const": -1.0},
            },
        }
        doc.data["clips"]["bend_positive"] = {
            "loop": False,
            "frames": 1,
            "duration_ms": 0,
            "channels": {
                "near_hand_x": {"const": 0.0},
                "near_hand_y": {"const": -32.0},
                "near_hand_bend": {"const": 1.0},
            },
        }
        negative, _ = doc.solve("bend_negative", 0.0)
        positive, _ = doc.solve("bend_positive", 0.0)
        negative_elbow_x = negative["near_arm_l"].origin[0]
        positive_elbow_x = positive["near_arm_l"].origin[0]
        assert positive_elbow_x - negative_elbow_x > 1.0

    def test_blade_hidden_outside_slash(self, doc):
        # opacity_channel parts default to invisible when their channel is
        # absent: idle must not paint the blade.
        _, params_idle = doc.solve("idle", 0.25)
        assert "slash_vis" not in params_idle
        _, params_slash = doc.solve("slash", 0.45)
        assert params_slash["slash_vis"] > 0.5

    def test_sheet_export_bundle(self, doc, tmp_path):
        paths = render_sheet_for_doc(doc, tmp_path)
        names = {p.name for p in paths}
        assert f"{doc.name}_spritesheet.png" in names
        assert f"{doc.name}_spritesheet.ron" in names
        ron = (tmp_path / f"{doc.name}_spritesheet.ron").read_text()
        assert 'animation: "idle"' in ron

    def test_save_load_round_trip(self, doc, tmp_path):
        out = tmp_path / "x.rig.json"
        doc.save(out)
        again = RigDocument.load(out)
        assert again.data == doc.data


class TestRiggedRegistration:
    def test_rigged_module_imports(self):
        from ambition_sprite2d_renderer.targets.characters import rigged

        assert isinstance(rigged.TARGETS, dict)

    def test_doc_in_rigged_dir_registers(self, tmp_path, monkeypatch):
        from ambition_sprite2d_renderer.targets.characters import rigged

        doc = RigDocument.load(TEMPLATE)
        doc.data["name"] = "test_rigged_bot"
        doc.save(tmp_path / "test_rigged_bot.rig.json")
        monkeypatch.setattr(rigged, "RIGGED_DIR", tmp_path)
        targets = rigged._discover()
        assert "test_rigged_bot" in targets
        assert callable(targets["test_rigged_bot"]["render"])


def test_build_skeleton_reuses_cached_topology_and_invalidates_on_edit():
    doc = RigDocument.new_empty("cache_test")
    first = doc.build_skeleton()
    second = doc.build_skeleton()
    assert first is second

    doc.bones[0]["offset"][0] += 1.0
    third = doc.build_skeleton()
    assert third is not first


def test_render_at_accepts_a_precomputed_solve(monkeypatch):
    doc = RigDocument.new_empty("solved_render")
    solved = doc.solve("idle", 0.0)

    def unexpected_solve(*args, **kwargs):
        raise AssertionError("render_at recomputed a supplied solve")

    monkeypatch.setattr(doc, "solve", unexpected_solve)
    image = doc.render_at("idle", 0.0, supersample=1, solved=solved)
    assert image.size == (128, 128)


def test_render_padding_preserves_art_outside_logical_frame():
    doc = RigDocument.new_empty("overscan")
    doc.data["frame"] = {
        "width": 40,
        "height": 40,
        "supersample": 1,
        "ground_y": 20.0,
        "center_x": 4.0,
        "ankle_h": 0.0,
    }
    doc.data["bones"] = [
        {
            "name": "root",
            "parent": None,
            "offset": [0.0, 0.0],
            "length": 0.0,
            "rest_angle": 0.0,
        }
    ]
    doc.data["parts"] = [
        {
            "name": "wide",
            "bone": "root",
            "z": 0,
            "kind": "polygon",
            "points": [[-10, -5], [10, -5], [10, 5], [-10, 5]],
            "fill": "#FFFFFF",
            "outline_w": 0.0,
        }
    ]
    doc.data["clips"] = {
        "idle": {"loop": True, "frames": 1, "duration_ms": 100, "channels": {}}
    }

    clipped = doc.render_frame("idle", 0, 1)
    overscanned = doc.render_frame("idle", 0, 1, padding=12)

    assert clipped.size == (40, 40)
    assert overscanned.size == (64, 64)
    clipped_bbox = clipped.getchannel("A").getbbox()
    overscan_bbox = overscanned.getchannel("A").getbbox()
    assert clipped_bbox is not None and clipped_bbox[0] == 0
    assert overscan_bbox is not None and overscan_bbox[0] > 0
    assert overscan_bbox[2] - overscan_bbox[0] > clipped_bbox[2] - clipped_bbox[0]


def _prepared_sprite_for_test():
    from PIL import Image, ImageDraw
    from ambition_sprite2d_renderer.authoring.rigdoc import SpriteRaster

    image = Image.new("RGBA", (13, 9), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((2, 1, 11, 7), fill=(20, 180, 240, 255))
    pivot = (4.25, 3.5)
    radius = 13
    padded = Image.new("RGBA", (2 * radius, 2 * radius), (0, 0, 0, 0))
    padded.alpha_composite(
        image,
        (radius - int(round(pivot[0])), radius - int(round(pivot[1]))),
    )
    return SpriteRaster(image, pivot, padded, radius, ("test", 256))


def test_sprite_raster_cache_hit_does_not_touch_svg_path(tmp_path, monkeypatch):
    from PIL import Image
    from ambition_sprite2d_renderer.authoring import svg_parts

    svg_path = tmp_path / "part.svg"
    svg_path.write_text("<svg/>", encoding="utf8")
    rig_path = tmp_path / "test.rig.json"
    doc = RigDocument.new_empty("sprite_cache")
    doc.source_path = rig_path
    doc.data["svg_source"] = {
        "path": "part.svg",
        "view": "side",
        "ref_dpi": 96.0,
        "scale": 1.0,
    }
    part = {
        "name": "arm",
        "kind": "sprite",
        "include": ["arm"],
        "pivot": [3.0, 4.0],
    }
    calls = []

    def fake_rasterize(*args, **kwargs):
        calls.append((args, kwargs))
        return Image.new("RGBA", (8, 10), (255, 0, 0, 255)), (0, 0), 1.0

    monkeypatch.setattr(svg_parts, "rasterize_subset", fake_rasterize)
    first = doc.sprite_raster(part, 1.0)
    assert first is not None

    def unexpected_path_lookup():
        raise AssertionError("a sprite cache hit resolved the SVG path")

    monkeypatch.setattr(doc, "_svg_path", unexpected_path_lookup)
    second = doc.sprite_raster(part, 1.0)

    assert second is first
    assert len(calls) == 1


def test_prepared_rotation_matches_standalone_renderer():
    from PIL import Image
    from ambition_sprite2d_renderer.authoring.rigdoc import (
        SpriteTransformCache,
        blit_rotated,
    )

    sprite = _prepared_sprite_for_test()
    expected = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    actual = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    blit_rotated(expected, sprite.image, sprite.pivot, (40, 40), 33.0)
    blit_rotated(
        actual,
        sprite.image,
        sprite.pivot,
        (40, 40),
        33.0,
        prepared=sprite,
        transform_cache=SpriteTransformCache(),
    )
    assert actual.tobytes() == expected.tobytes()


def test_transform_cache_reuses_unchanged_part_rotation():
    from ambition_sprite2d_renderer.authoring.rigdoc import SpriteTransformCache

    sprite = _prepared_sprite_for_test()
    cache = SpriteTransformCache(max_bytes=1024 * 1024)
    first = cache.rotated(sprite, 27.5)
    second = cache.rotated(sprite, 27.5)
    equivalent_turn = cache.rotated(sprite, 387.5)

    assert second is first
    assert equivalent_turn is first


def test_transform_cache_probation_prevents_one_off_eviction():
    from PIL import Image
    import ambition_sprite2d_renderer.authoring.rigdoc as rigdoc_mod
    from ambition_sprite2d_renderer.authoring.rigdoc import SpriteRaster, SpriteTransformCache

    sprite = _prepared_sprite_for_test()
    # One 26x26 RGBA rotation fits, two do not. The resident first angle should
    # survive a one-off second angle; seeing the second angle again admits it.
    cache = SpriteTransformCache(max_bytes=26 * 26 * 4 + 8)
    first = cache.rotated(sprite, 10.0)
    one_off = cache.rotated(sprite, 20.0)
    assert len(cache._items) == 1
    assert next(iter(cache._items.values())) is first
    assert len(cache._probation) == 1

    repeated = cache.rotated(sprite, 20.0)
    assert repeated is not one_off
    assert len(cache._items) == 1
    assert next(iter(cache._items.values())) is repeated
    assert not cache._probation


def test_zero_rotation_skips_transform_cache():
    from PIL import Image
    from ambition_sprite2d_renderer.authoring.rigdoc import (
        SpriteTransformCache,
        blit_rotated,
    )

    sprite = _prepared_sprite_for_test()
    cache = SpriteTransformCache(max_bytes=1024 * 1024)
    canvas = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    blit_rotated(
        canvas,
        sprite.image,
        sprite.pivot,
        (40, 40),
        0.0,
        prepared=sprite,
        transform_cache=cache,
    )

    assert not cache._items
    assert canvas.getchannel("A").getbbox() is not None


def test_arm_max_reach_ratio_preserves_visible_elbow_bend(doc):
    doc.data["ik_chains"] = [
        {
            "upper": "near_arm_u",
            "lower": "near_arm_l",
            "channel_prefix": "near_hand",
            "rest_x": 80.0,
            "rest_y": -20.0,
            "bend": -1.0,
            "pitch_mode": "follow_lower",
            "max_reach_ratio": 0.90,
        }
    ]
    doc.data["clips"]["reach_probe"] = {
        "loop": False,
        "frames": 1,
        "duration_ms": 0,
        "channels": {
            "near_hand_x": {"const": 80.0},
            "near_hand_y": {"const": -20.0},
        },
    }
    world, _ = doc.solve("reach_probe", 0.0)
    shoulder = world["near_arm_u"].origin
    elbow = world["near_arm_l"].origin
    wrist = world["near_arm_l"].tip
    ax, ay = shoulder[0] - elbow[0], shoulder[1] - elbow[1]
    bx, by = wrist[0] - elbow[0], wrist[1] - elbow[1]
    import math
    cosine = (ax * bx + ay * by) / (math.hypot(ax, ay) * math.hypot(bx, by))
    angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
    assert angle < 170.0


def test_follow_lower_hand_pitch_does_not_pin_hand_to_svg_world_angle(doc):
    lower = next(bone for bone in doc.bones if bone["name"] == "near_arm_l")
    doc.bones.append(
        {
            "name": "near_arm_hand",
            "parent": "near_arm_l",
            "offset": [float(lower["length"]), 0.0],
            "length": 4.0,
            "rest_angle": 11.0,
        }
    )
    doc.data["ik_chains"] = [
        {
            "upper": "near_arm_u",
            "lower": "near_arm_l",
            "end": "near_arm_hand",
            "channel_prefix": "near_hand",
            "rest_x": -18.0,
            "rest_y": -20.0,
            "rest_pitch": 5.0,
            "bend": -1.0,
            "pitch_mode": "follow_lower",
        }
    ]
    doc.data["clips"]["pitch_probe"] = {
        "loop": False,
        "frames": 1,
        "duration_ms": 0,
        "channels": {
            "near_hand_x": {"const": -18.0},
            "near_hand_y": {"const": -20.0},
        },
    }
    world, _ = doc.solve("pitch_probe", 0.0)
    relative = (world["near_arm_hand"].angle - world["near_arm_l"].angle + 180.0) % 360.0 - 180.0
    rest_relative = next(
        bone["rest_angle"] for bone in doc.bones if bone["name"] == "near_arm_hand"
    )
    assert relative == pytest.approx(rest_relative)


def test_high_resolution_transform_cache_uses_bilinear_rotation(monkeypatch):
    from PIL import Image
    import ambition_sprite2d_renderer.authoring.rigdoc as rigdoc_mod
    from ambition_sprite2d_renderer.authoring.rigdoc import SpriteRaster, SpriteTransformCache

    sprite = _prepared_sprite_for_test()
    sprite = SpriteRaster(
        sprite.image,
        sprite.pivot,
        sprite.padded,
        sprite.radius,
        sprite.cache_key,
        working_scale=4.0,
    )
    seen = []

    def fake_rotate(img, angle, *, resample, center=None, expand=False):
        seen.append(resample)
        return Image.new("RGBA", img.size, (0, 0, 0, 0))

    monkeypatch.setattr(rigdoc_mod, "rotate_transparent_sprite", fake_rotate)
    SpriteTransformCache(max_bytes=1024 * 1024).rotated(sprite, 17.0)

    assert seen == [rigdoc_mod.RESAMPLING.BILINEAR]
