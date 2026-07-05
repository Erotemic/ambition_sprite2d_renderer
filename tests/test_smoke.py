"""Representative renderer-basis smoke tests.

These tests exercise the main renderer surfaces with a small, generic sample:
config-authored character sheets, canonicals, and module-authored prop/tile
sheets. They intentionally avoid freezing per-target art choices such as exact
animation inventories, tile names, or palette counts.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from PIL import Image

from ambition_sprite2d_renderer.authoring.canonical import render_canonical
from ambition_sprite2d_renderer.registry import CharacterJob, discover_all_targets
from ambition_sprite2d_renderer.authoring.sheet import write_spritesheet


CONFIGS = (
    Path(__file__).resolve().parent.parent / "ambition_sprite2d_renderer" / "configs"
)

CONFIG_BASIS = [
    "robot.yaml",
    "goblin.yaml",
    "ninja.yaml",
]

MODULE_RENDER_BASIS = [
    "shrine",  # prop target through module-authoring path
    "intro_lab_tileset",  # tile target through module-authoring path
]


@pytest.mark.parametrize("config_name", CONFIG_BASIS)
def test_config_target_sheet_smoke(tmp_path: Path, config_name: str):
    pytest.importorskip("rectpack")
    job = CharacterJob.load(CONFIGS / config_name)
    job.render.frame_width = 64
    job.render.frame_height = 64
    job.render.supersample = 1
    job.animations = [job.animations[0]]
    image_path, manifest_path = write_spritesheet(
        job, tmp_path / f"{Path(config_name).stem}.png", tmp_path / f"{Path(config_name).stem}.yaml"
    )
    assert image_path.exists()
    assert manifest_path.exists()

    img = Image.open(image_path).convert("RGBA")
    assert img.getchannel("A").getbbox() is not None

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest["target"] == job.target
    assert manifest["rows"]
    assert manifest["frame_width"] > 0
    assert manifest["frame_height"] > 0


@pytest.mark.parametrize("config_name", ["robot.yaml", "ninja.yaml"])
def test_config_target_canonical_smoke(config_name: str):
    job = CharacterJob.load(CONFIGS / config_name)
    image = render_canonical(job)
    assert image.size == (job.render.single_width, job.render.single_height)
    assert image.convert("RGBA").getchannel("A").getbbox() is not None


@pytest.mark.slow_render
@pytest.mark.parametrize("target_name", MODULE_RENDER_BASIS)
def test_module_target_render_basis(tmp_path: Path, target_name: str):
    target = discover_all_targets().targets[target_name]
    outputs = [Path(path) for path in target.render_sheet(tmp_path / target_name)]
    assert outputs
    assert all(path.exists() for path in outputs)

    output_names = {path.name for path in outputs}
    assert any(name.endswith(".png") for name in output_names)
    assert any(name.endswith((".yaml", ".json")) for name in output_names)

    pngs = [path for path in outputs if path.suffix == ".png"]
    assert pngs
    sample = Image.open(pngs[0]).convert("RGBA")
    assert sample.getchannel("A").getbbox() is not None

    manifests = [path for path in outputs if path.suffix in {".yaml", ".json"}]
    assert manifests
