"""The per-frame / per-resolution rendering contract.

Every generator must render each frame of each animation independently, at any
requested resolution, so custom packers and debug views can drive them without
the built-in sheet pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ambition_sprite2d_renderer.authoring.frame_source import (
    FrameSource,
    render_all_frames,
    render_animation,
)
from ambition_sprite2d_renderer.authoring.generators import GENERATORS, get_generator
from ambition_sprite2d_renderer.registry import CharacterJob

import yaml

CONFIGS = Path(__file__).resolve().parents[1] / "ambition_sprite2d_renderer" / "configs"


def _config_by_target() -> dict:
    """Map each generator target to one config that drives it (configs live in
    the root and in review/ + factions/ subdirs)."""
    found: dict = {}
    for path in sorted(CONFIGS.rglob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text())
        except Exception:
            continue
        if isinstance(data, dict):
            found.setdefault(data.get("target"), path)
    return found


_CONFIG_FOR = _config_by_target()


def _source(target: str) -> FrameSource:
    job = CharacterJob.load(_CONFIG_FOR[target])
    return get_generator(target).frames_for(job)


def test_every_generator_has_a_test_config():
    # The resolution + independence guarantees are per-generator; every
    # registered generator must be reachable through a config.
    missing = set(GENERATORS) - set(_CONFIG_FOR)
    assert not missing, f"no config found for generators: {sorted(missing)}"


@pytest.mark.parametrize("target", sorted(g for g in GENERATORS if g in _CONFIG_FOR))
@pytest.mark.parametrize("size", [(24, 24), (96, 96), (200, 200), (64, 128)])
def test_generator_renders_at_arbitrary_resolution(target, size):
    src = _source(target)
    animation = next(iter(src.animations()))
    count = src.animations()[animation]["frames"]
    img = src.frame(animation, 0, count, size)
    assert img.size == size, f"{target} ignored the requested size"
    assert img.getchannel("A").getbbox() is not None, f"{target} rendered empty at {size}"


@pytest.mark.parametrize("target", ["goblin", "robot", "boss"])
def test_frames_are_independent_of_render_order(target):
    src = _source(target)
    anims = src.animations()
    first = next(iter(anims))
    n = anims[first]["frames"]

    baseline = src.frame(first, 0, n, (96, 96)).tobytes()
    # Render other frames / sizes in between; the target frame must be unchanged.
    for other in list(anims)[1:3]:
        on = anims[other]["frames"]
        src.frame(other, on - 1, on, (48, 48))
        src.frame(other, 0, on, (128, 128))
    again = src.frame(first, 0, n, (96, 96)).tobytes()
    assert again == baseline, f"{target} frame depends on render order (hidden state)"


def test_render_all_frames_enumerates_every_frame():
    src = _source("ninja")
    anims = src.animations()
    expected = sum(info["frames"] for info in anims.values())
    frames = render_all_frames(src, (64, 64))
    assert len(frames) == expected
    # Keys are unique and every frame carries its own image at the requested size.
    assert len({f.key for f in frames}) == expected
    assert all(f.image.size == (64, 64) for f in frames)


def test_render_animation_covers_one_animation():
    src = _source("goblin")
    animation = next(iter(src.animations()))
    n = src.animations()[animation]["frames"]
    frames = render_animation(src, animation, (80, 80))
    assert [f.index for f in frames] == list(range(n))
    assert all(f.animation == animation for f in frames)


def test_export_frames_writes_png_per_frame_plus_index(tmp_path):
    from ambition_sprite2d_renderer.authoring.frame_debug import export_frames

    src = _source("sandbag")
    paths = export_frames(src, (64, 64), tmp_path)
    pngs = [p for p in paths if p.suffix == ".png"]
    expected = sum(info["frames"] for info in src.animations().values())
    assert len(pngs) == expected
    index = json.loads((tmp_path / "frames.json").read_text())
    assert index["target"] == "sandbag"
    assert index["width"] == 64 and index["height"] == 64
    assert len(index["frames"]) == expected
