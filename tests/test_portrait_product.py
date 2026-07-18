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


def test_module_character_without_hook_uses_fresh_canonical_fallback(tmp_path):
    calls: list[str] = []

    def render_sheet(out_dir, **opts):
        del out_dir, opts
        raise AssertionError("portrait fallback must not sample a gameplay sheet")

    def render_canonical(out_dir, **opts):
        del opts
        calls.append("canonical")
        out = Path(out_dir) / "fallback_canonical_transparent.png"
        _sample_frame((160, 200)).save(out)
        return out

    target = Target.from_module(
        name="fallback",
        category="characters",
        module_path="tests.fallback",
        render=render_sheet,
        render_canonical=render_canonical,
        sheet_files=("fallback_spritesheet.png",),
        portrait_files=("fallback_portraits.png", "fallback_portraits.ron"),
        actor_metadata={"body": {"body_plan": "HumanoidBiped"}},
    )
    assert target.supports_portraits
    outputs = target.render_portraits(tmp_path)
    assert calls == ["canonical"]
    assert [path.name for path in outputs] == [
        "fallback_portraits.png",
        "fallback_portraits.ron",
    ]
    assert Image.open(outputs[0]).size == (256, 320)


def test_portrait_install_subdirectory_is_independent_of_gameplay_install(tmp_path):
    rendered = tmp_path / "rendered"
    installed = tmp_path / "installed"
    rendered.mkdir()
    (rendered / "boss_spritesheet.png").write_bytes(b"sheet")
    write_portrait_sheet(
        "boss", {"default": PortraitClip.still(_sample_frame())}, rendered
    )
    target = Target.from_module(
        name="boss",
        category="characters",
        module_path="tests.boss",
        render=lambda *_args, **_kwargs: [],
        sheet_files=("boss_spritesheet.png",),
        portrait_files=("boss_portraits.png", "boss_portraits.ron"),
        portrait_install_subdir="boss",
    )
    target.install(rendered, installed)
    assert (installed / "boss_spritesheet.png").exists()
    assert (installed / "boss" / "boss_portraits.png").exists()
    assert (installed / "boss" / "boss_portraits.ron").exists()


def test_every_discovered_character_declares_portrait_support():
    report = discover_all_targets()
    unsupported = sorted(
        target.name
        for target in report.targets.values()
        if target.category == "characters" and not target.supports_portraits
    )
    assert unsupported == []


def test_portrait_gallery_discovers_nested_products(tmp_path):
    from ambition_sprite2d_renderer.authoring.portrait import write_portrait_gallery

    write_portrait_sheet(
        "flat", {"default": PortraitClip.still(_sample_frame())}, tmp_path
    )
    nested = tmp_path / "boss"
    write_portrait_sheet(
        "nested", {"default": PortraitClip.still(_sample_frame())}, nested
    )
    out, warnings = write_portrait_gallery(tmp_path, tmp_path / "gallery.png", columns=2)
    assert warnings == []
    assert out.exists()
    assert Image.open(out).getchannel("A").getbbox() is not None


def test_sheet_build_canonical_mode_draws_only_one_fresh_frame(tmp_path):
    from ambition_sprite2d_renderer.authoring.frame_source import CallableFrameSource
    from ambition_sprite2d_renderer.authoring.sheet_build import (
        canonical_render_only,
        render_sheet,
    )

    calls: list[tuple[str, int, int]] = []

    def render_frame(animation, index, count):
        calls.append((animation, index, count))
        return _sample_frame((64, 80))

    source = CallableFrameSource(
        target="family_member",
        rows=[("idle", 4, 100), ("walk", 8, 80)],
        render_fn=render_frame,
        frame_size=(64, 80),
        auto_crop=False,
    )
    with canonical_render_only():
        outputs = render_sheet(source, tmp_path)

    assert calls == [("idle", 1, 4)]
    assert outputs["canonical"].exists()
    assert outputs["canonical_transparent"].exists()
    assert not outputs["spritesheet"].exists()


def test_sandbag_portrait_uses_its_procedural_authoring_path(tmp_path, monkeypatch):
    from ambition_sprite2d_renderer.targets.characters import sandbag

    calls: list[tuple[str, int, int]] = []

    def render_frame(animation, frame_index, frame_count):
        calls.append((animation, frame_index, frame_count))
        return _sample_frame((512, 512))

    monkeypatch.setattr(sandbag, "render_sandbag_frame", render_frame)
    outputs = sandbag.render_portraits(tmp_path)

    assert calls == [("idle", 1, 6)]
    assert [path.name for path in outputs] == [
        "sandbag_portraits.png",
        "sandbag_portraits.ron",
    ]


def test_robot_heavy_portraits_cover_concrete_variants(tmp_path, monkeypatch):
    from ambition_sprite2d_renderer.targets.characters import robot_heavy

    calls: list[tuple[str, str, int, int]] = []

    def render_frame(self, animation, frame_index, frame_count):
        calls.append((self.spec.target_name, animation, frame_index, frame_count))
        return _sample_frame((512, 512))

    monkeypatch.setattr(robot_heavy.RobotHeavyRenderer, "render_frame", render_frame)
    outputs = robot_heavy.render_portraits(tmp_path)

    expected_targets = [spec.target_name for spec in robot_heavy.VARIANTS.values()]
    assert [call[0] for call in calls] == expected_targets
    assert all(call[1:] == ("idle", 1, 6) for call in calls)
    assert {path.name for path in outputs} == {
        name
        for target in expected_targets
        for name in (f"{target}_portraits.png", f"{target}_portraits.ron")
    }


def test_gnu_ton_portraits_cover_multipart_hall_actors(tmp_path, monkeypatch):
    from ambition_sprite2d_renderer.targets.characters import gnu_ton_boss

    calls: list[tuple[str, int, int, str]] = []

    def draw_frame(animation, frame_index, frame_count, *, layer):
        calls.append((animation, frame_index, frame_count, layer))
        return _sample_frame((768, 576))

    monkeypatch.setattr(gnu_ton_boss.sprite_generator, "draw_frame", draw_frame)
    outputs = gnu_ton_boss.render_portraits(tmp_path)

    assert calls == [
        ("rest", 1, 10, "full"),
        ("rest", 1, 10, "giant_body"),
        ("rest", 1, 10, "hands"),
    ]
    assert {path.name for path in outputs} == set(gnu_ton_boss.PORTRAIT_FILES)


def test_mockingbird_fallback_uses_quick_canonical_path(tmp_path, monkeypatch):
    from ambition_sprite2d_renderer.targets.characters import mockingbird_boss

    calls: list[bool] = []

    def render_outputs(*, outdir, quick):
        calls.append(quick)
        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        canonical = outdir / "mockingbird_boss_canonical_transparent.png"
        _sample_frame((512, 512)).save(canonical)
        return [canonical]

    monkeypatch.setattr(
        mockingbird_boss.sprite_generator, "render_outputs", render_outputs
    )
    target = discover_all_targets().targets["mockingbird_boss"]
    outputs = target.render_portraits(tmp_path)

    assert calls == [True]
    assert [path.name for path in outputs] == [
        "mockingbird_boss_portraits.png",
        "mockingbird_boss_portraits.ron",
    ]
