"""Structural and native-render tests for the portrait publishing product."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from ambition_sprite2d_renderer.authoring.generator import CharacterGenerator
from ambition_sprite2d_renderer.authoring.portrait import (
    PortraitClip,
    write_portrait_sheet,
)
from ambition_sprite2d_renderer.registry import CharacterJob, Target, discover_all_targets


def _sample_frame(size=(64, 80)) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 5, size[0] - 8, size[1] - 25), fill=(210, 150, 110, 255))
    draw.rectangle(
        (12, size[1] - 30, size[0] - 12, size[1] - 1),
        fill=(20, 100, 120, 255),
    )
    return image


def test_portrait_sheet_rejects_missing_default(tmp_path):
    try:
        write_portrait_sheet(
            "sample",
            {"annoyed": PortraitClip.still(_sample_frame())},
            tmp_path,
        )
    except ValueError as error:
        assert "must define a 'default' clip" in str(error)
    else:
        raise AssertionError("portrait product accepted a missing default clip")


def test_portrait_sheet_requires_default_and_emits_runtime_shape(tmp_path):
    outputs = write_portrait_sheet(
        "sample",
        {
            "default": PortraitClip.still(_sample_frame()),
            "annoyed": PortraitClip(
                (_sample_frame(), _sample_frame()), duration_ms=90, looping=True
            ),
        },
        tmp_path,
    )
    assert outputs == [
        tmp_path / "sample_portraits.png",
        tmp_path / "sample_portraits.ron",
    ]
    sheet = Image.open(outputs[0])
    assert sheet.size == (64 * 3, 80)
    text = outputs[1].read_text(encoding="utf8")
    assert 'default_clip: "default"' in text
    assert '"annoyed": (' in text
    assert "duration_ms: 90" in text
    assert "looping: true" in text
    assert text.count("(x:") == 3


@dataclass(frozen=True)
class _Spec:
    head_w: float = 24.0
    head_h: float = 28.0


class _RecordingGenerator(CharacterGenerator):
    target = "recording"
    ANIMATIONS = {"idle": {"frames": 1, "duration_ms": 100}}

    def __init__(self):
        self.requested_sizes: list[tuple[int, int]] = []

    def build_spec(self, job):
        del job
        return _Spec()

    def render_frame(self, spec, animation, frame_index, size, job):
        del spec, animation, frame_index, job
        self.requested_sizes.append(size)
        image = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle(
            (
                size[0] * 0.36,
                size[1] * 0.08,
                size[0] * 0.64,
                size[1] * 0.72,
            ),
            fill=(255, 255, 255, 255),
        )
        return image


def test_generator_default_rerenders_at_native_portrait_source_resolution(tmp_path):
    job = CharacterJob.from_dict(
        {
            "target": "recording",
            "output_name": "recording",
            "animations": ["idle"],
            "render": {"frame_width": 128, "frame_height": 128},
            "visual": {"default_pose": "idle"},
            "sockets": {"head": {"point": {"x": 64, "y": 24}}},
        }
    )
    generator = _RecordingGenerator()
    outputs = generator.render_portraits(
        _Spec(), job, target="recording", out_dir=str(tmp_path)
    )
    assert generator.requested_sizes == [(512, 512)]
    assert Image.open(outputs[0]).size == (256, 320)
    assert Image.open(outputs[0]).getchannel("A").getbbox() is not None


def test_module_portrait_hook_is_installed_as_part_of_target_bundle(tmp_path):
    rendered = tmp_path / "rendered"
    installed = tmp_path / "installed"

    def render_sheet(out_dir, **opts):
        del opts
        image = Path(out_dir) / "bespoke_spritesheet.png"
        manifest = Path(out_dir) / "bespoke_spritesheet.ron"
        image.write_bytes(b"sheet")
        manifest.write_text("[]", encoding="utf8")
        return [image, manifest]

    def render_portraits(out_dir, **opts):
        del opts
        return write_portrait_sheet(
            "bespoke", {"default": PortraitClip.still(_sample_frame())}, out_dir
        )

    target = Target.from_module(
        name="bespoke",
        category="characters",
        module_path="tests.bespoke",
        render=render_sheet,
        render_portraits=render_portraits,
        sheet_files=("bespoke_spritesheet.png", "bespoke_spritesheet.ron"),
        portrait_files=("bespoke_portraits.png", "bespoke_portraits.ron"),
    )
    target.render_sheet(rendered)
    target.render_portraits(rendered)
    copied = target.install(rendered, installed)
    assert {path.name for path in copied} == {
        "bespoke_spritesheet.png",
        "bespoke_spritesheet.ron",
        "bespoke_portraits.png",
        "bespoke_portraits.ron",
    }


def test_vertical_slice_targets_cover_three_authoring_families():
    targets = discover_all_targets().targets
    assert targets["alice"].kind == "config"
    assert targets["alice"].supports_portraits
    assert targets["pipi_tau"].kind == "module"
    assert targets["pipi_tau"].supports_portraits
    assert targets["oiler"].kind == "module"
    assert targets["oiler"].supports_portraits


def test_oiler_portrait_hook_requests_native_svg_scale(monkeypatch, tmp_path):
    from ambition_sprite2d_renderer.targets.characters import oiler

    class _FakeRigDocument:
        frame = {"width": 128, "height": 128}

        def frame_time(self, clip_name, frame_index, frame_count):
            assert clip_name == "idle"
            assert (frame_index, frame_count) == (1, 8)
            return 0.125

        def render_at(self, clip_name, time, *, scale):
            assert clip_name == "idle"
            assert time == 0.125
            assert scale == 4
            image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse((200, 35, 312, 175), fill=(230, 190, 150, 255))
            draw.rectangle((160, 170, 352, 460), fill=(40, 80, 120, 255))
            return image

    monkeypatch.setattr(oiler, "_load_doc", lambda _filename: _FakeRigDocument())
    outputs = oiler.render_portraits(tmp_path)
    assert [path.name for path in outputs] == [
        "oiler_portraits.png",
        "oiler_portraits.ron",
    ]
    assert Image.open(outputs[0]).size == (256, 320)
    assert Image.open(outputs[0]).getchannel("A").getbbox() is not None
