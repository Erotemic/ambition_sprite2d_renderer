from pathlib import Path

import pytest
from PIL import Image

from ambition_sprite2d_renderer.registry.character_generators import get_generator
from ambition_sprite2d_renderer.registry import CharacterJob
from ambition_sprite2d_renderer.targets.props.entities import (
    write_entity_sprites,
)
from ambition_sprite2d_renderer.authoring.sheet import build_spritesheet


# Resolve configs relative to the package, not the cwd.
CONFIGS = (
    Path(__file__).resolve().parent.parent / "ambition_sprite2d_renderer" / "configs"
)


def _alpha_bbox_metrics(img):
    bbox = img.getchannel("A").getbbox()
    assert bbox is not None
    x1, y1, x2, y2 = bbox
    return {
        "w": x2 - x1,
        "h": y2 - y1,
        "area": sum(img.getchannel("A").histogram()[11:]),
        "bottom": y2,
        "bbox": bbox,
    }


def test_animation_sets_include_blink_parts_and_dash():
    for target in ["robot", "goblin"]:
        adapter = get_generator(target)
        assert "blink_out" in adapter.animations()
        assert "blink_in" in adapter.animations()
        assert "dash" in adapter.animations()


@pytest.mark.slow_render
def test_death_frames_keep_visible_mass_and_anchor():
    for cfg in ["robot.yaml", "goblin.yaml", "boss.yaml"]:
        job = CharacterJob.load(Path(str(CONFIGS)) / cfg)
        adapter = get_generator(job.target)
        spec = adapter.sample_spec(job)
        info = adapter.animations()["death"]
        frames = [
            adapter.render_frame(spec, "death", idx, (128, 128), job)
            for idx in range(info["frames"])
        ]
        metrics = [_alpha_bbox_metrics(img) for img in frames]
        first = metrics[0]
        min_area = min(m["area"] for m in metrics)
        # Regression guard: death poses may change, but should not collapse into
        # a tiny off-ground blob.
        assert min_area >= first["area"] * 0.78, (job.target, metrics)
        for m in metrics:
            assert m["bottom"] >= first["bottom"] - 8, (job.target, metrics)
            assert m["w"] >= first["w"] * 0.70, (job.target, metrics)


def test_blink_parts_are_teleport_not_eyelid_blink():
    for target in ["robot", "goblin"]:
        adapter = get_generator(target)
        adapter.sample_spec(CharacterJob.load(Path(str(CONFIGS)) / f"{target}.yaml"))
        generator = adapter
        for name in ["blink_out", "blink_in"]:
            info = adapter.animations()[name]
            for idx in range(info["frames"]):
                pose = generator.pose_for_animation(name, idx, info["frames"])
                assert not pose.blink


@pytest.mark.slow_render
def test_entity_sprites_render_manifest_and_nonempty_images(tmp_path):
    out_dir = tmp_path / "entities"
    outputs = write_entity_sprites(out_dir)
    output_paths = {Path(path) for path in outputs}
    manifest = out_dir / "entity_manifest.yaml"
    contact_sheet = out_dir / "entity_contact_sheet.png"
    assert manifest in output_paths
    assert contact_sheet in output_paths
    assert manifest.exists()
    assert contact_sheet.exists()

    pngs = sorted(path for path in output_paths if path.suffix == ".png")
    assert pngs
    for path in pngs[:8]:
        img = Image.open(path).convert("RGBA")
        assert img.getchannel("A").getbbox() is not None, path


@pytest.mark.slow_render
def test_tight_crop_eliminates_transparent_edges_on_entity_sprites(tmp_path):
    """Auto-cropped entity sprites should not keep excessive transparent margin.

    The invariant is about the crop pipeline and in-game collision-box scaling,
    not about a specific authored item list.
    """
    out_dir = tmp_path / "entities"
    write_entity_sprites(out_dir)
    samples = [
        "chest_closed.png",
        "pickup_health.png",
        "breakable_intact.png",
        "pogo_orb.png",
        "hazard_spikes.png",
        "solid_block.png",
    ]
    for name in samples:
        img = Image.open(out_dir / name).convert("RGBA")
        bbox = img.getchannel("A").getbbox()
        assert bbox is not None, name
        l, t, r, b = bbox
        cw, ch = r - l, b - t
        w, h = img.size
        fill = (cw * ch) / (w * h)
        assert fill >= 0.70, (
            f"{name} content fill {fill:.0%} below 70% — sprite has "
            "too much transparent margin and will look smaller than "
            "its collision box when stretched"
        )


@pytest.mark.slow_render
def test_tile_sprites_match_authored_dimensions_and_skip_crop(tmp_path):
    """Tile sprites must keep their full authored canvas.

    Bevy's tiled image mode repeats textures at native pixel scale, so cropping
    or wrong-axis sizing would change the repeat period.
    """
    out_dir = tmp_path / "entities"
    write_entity_sprites(out_dir)
    tiles = {
        "solid_tile.png": (32, 32),
        "one_way_tile.png": (32, 16),
        "hazard_tile.png": (32, 16),
        "soft_blink_tile.png": (32, 32),
        "hard_blink_tile.png": (32, 32),
    }
    for name, expected_size in tiles.items():
        img = Image.open(out_dir / name).convert("RGBA")
        assert img.size == expected_size, (name, img.size)


@pytest.mark.slow_render
def test_spritesheet_emits_body_metrics():
    pytest.importorskip("rectpack")
    """Sprite manifests must carry measured body extent so runtime code can
    align sprites with collision boxes without hand-tuned anchor constants."""
    for cfg_name in ("robot", "goblin", "boss"):
        job = CharacterJob.load(Path(CONFIGS / f"{cfg_name}.yaml"))
        # Truncate to one anim and skip supersampling so this test is fast.
        job.animations = job.animations[:1]
        job.render.supersample = 1
        _, manifest = build_spritesheet(job)
        assert "body_metrics" in manifest, cfg_name
        bm = manifest["body_metrics"]

        bbox = bm["body_pixel_bbox"]
        assert bbox["w"] > 0 and bbox["h"] > 0, (cfg_name, bbox)

        feet = bm["feet_pixel"]
        assert 0 <= feet["x"] <= bm["frame_width"], (cfg_name, feet)
        assert 0 <= feet["y"] <= bm["frame_height"], (cfg_name, feet)

        # Bevy anchor convention: y in [-0.5, +0.5], 0=center, +0.5=top.
        # Our characters all stand near the bottom of their frames, so the
        # feet anchor should always be below center (negative).
        anchor_y = bm["feet_anchor_norm"]["y"]
        assert -0.5 <= anchor_y < 0.0, (cfg_name, anchor_y)


@pytest.mark.slow_render
def test_sandbag_adapter_participates_in_character_pipeline(tmp_path):
    pytest.importorskip("rectpack")
    job = CharacterJob.load(CONFIGS / "sandbag.yaml")
    # This test pins logical frame geometry, crop behavior, and packer limits;
    # it does not assert the authored pose inventory.
    job.render.render_scale = 1
    pages, manifest = build_spritesheet(job)
    assert manifest["target"] == "sandbag"
    assert manifest["crop"]["enabled"] is False
    # Logical frame size is unchanged by packing (gameplay coordinate space).
    assert manifest["frame_width"] == 128
    assert manifest["frame_height"] == 128
    # Packed pages stay within the GPU texture limit, and packing the trimmed
    # frames reclaims space vs a naive grid.
    assert pages, "sandbag must produce at least one page"
    assert all(p.size[0] <= 4096 and p.size[1] <= 4096 for p in pages)
    grid_area = (manifest["label_width"] + 128 * 11) * (128 * 11)
    packed_area = sum(p.size[0] * p.size[1] for p in pages)
    assert packed_area < grid_area, (packed_area, grid_area)
