"""Portable prose and bark hints published with character sprite sheets."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument, render_sheet_for_doc
from ambition_sprite2d_renderer.authoring.sheet_build import (
    build_sheet,
    publish_character_notes,
)
from ambition_sprite2d_renderer.registry import CharacterJob
from ambition_sprite2d_renderer.yaml_io import safe_load


def test_character_job_roundtrips_freeform_character_notes():
    job = CharacterJob.from_dict(
        {
            "target": "toon",
            "authoring_description": "A prose authoring prompt.",
            "gameplay_description": "An optional gameplay pitch.",
            "dialogue_hints": {"barks": ["First bark.", "Second bark."]},
        }
    )

    assert job.authoring_description == "A prose authoring prompt."
    assert job.gameplay_description == "An optional gameplay pitch."
    assert job.dialogue_hints["barks"] == ["First bark.", "Second bark."]
    assert job.to_dict()["authoring_description"] == "A prose authoring prompt."
    assert job.to_dict()["gameplay_description"] == "An optional gameplay pitch."
    assert job.to_dict()["dialogue_hints"]["barks"] == [
        "First bark.",
        "Second bark.",
    ]


def test_publish_character_notes_copies_and_normalizes_barks():
    metadata = {
        "authoring_description": "  Explain the parody in prose.  ",
        "gameplay_description": "  Games may opt into this behavior.  ",
        "dialogue_hints": {"barks": ["  Hello.  ", "", "Again."]},
        "actor": {"character_id": "not_part_of_sheet_yaml_notes"},
    }
    manifest = {"target": "example"}

    publish_character_notes(manifest, metadata)

    assert manifest == {
        "target": "example",
        "authoring_description": "Explain the parody in prose.",
        "gameplay_description": "Games may opt into this behavior.",
        "dialogue_hints": {"barks": ["Hello.", "Again."]},
    }
    assert metadata["dialogue_hints"]["barks"][0] == "  Hello.  "


def test_tackon_sheet_yaml_publishes_character_notes(tmp_path: Path):
    metadata = {
        "authoring_description": "A tiny test parody.",
        "gameplay_description": "Use as a test actor.",
        "dialogue_hints": {"barks": ["Test bark."]},
    }

    outputs = build_sheet(
        target="character_notes_test",
        rows=[("idle", 1, 100)],
        render_fn=lambda _anim, _idx, _count: Image.new(
            "RGBA", (8, 8), (255, 255, 255, 255)
        ),
        out_dir=tmp_path,
        frame_size=(8, 8),
        label_width=1,
        auto_crop=False,
        trim=False,
        actor_metadata=metadata,
    )
    manifest = safe_load(outputs["yaml"].read_text(encoding="utf8"))

    assert manifest["authoring_description"] == "A tiny test parody."
    assert manifest["gameplay_description"] == "Use as a test actor."
    assert manifest["dialogue_hints"]["barks"] == ["Test bark."]


def test_rig_document_forwards_actor_metadata_to_sheet_builder(monkeypatch, tmp_path):
    captured = {}

    def fake_build_sheet(**kwargs):
        captured.update(kwargs)
        return {
            key: tmp_path / f"rig_notes_{key}.tmp"
            for key in (
                "spritesheet",
                "yaml",
                "ron",
                "actor",
                "canonical",
                "canonical_transparent",
                "preview",
            )
        }

    monkeypatch.setattr(
        "ambition_sprite2d_renderer.authoring.sheet_build.build_sheet",
        fake_build_sheet,
    )
    metadata = {
        "authoring_description": "A rig-authored parody.",
        "gameplay_description": "Use the rig in a game.",
        "dialogue_hints": {"barks": ["Rig bark."]},
    }
    doc = RigDocument(
        {
            "name": "rig_notes",
            "frame": {"width": 8, "height": 8},
            "clips": {"idle": {"frames": 1, "duration_ms": 100}},
            "actor_metadata": metadata,
        }
    )

    render_sheet_for_doc(doc, tmp_path)

    assert captured["actor_metadata"] == metadata


def test_adapter_manifest_publishes_character_notes(monkeypatch):
    from ambition_sprite2d_renderer.authoring import sheet as sheet_module
    from ambition_sprite2d_renderer.authoring import sheet_build as sheet_build_module

    class FakeGenerator:
        def sample_spec(self, _job):
            return object()

        def animations(self):
            return {"idle": {"frames": 1, "duration_ms": 100}}

        def render_frame(self, _spec, _animation, _index, size, _job):
            return Image.new("RGBA", size, (255, 255, 255, 255))

        def spec_dict(self, _spec):
            return {}

        def body_inset(self):
            return None

        def hurtbox_parts(self, _size):
            return {}

        def attack_hitboxes(self, _size):
            return {}

    def fake_layout(_target, rendered_rows, fw, fh, **_kwargs):
        rows = [
            {
                "animation": rendered_rows[0][0],
                "row_index": 0,
                "frame_count": 1,
                "duration_ms": 100,
                "rects": [],
            }
        ]
        return [Image.new("RGBA", (fw, fh), (0, 0, 0, 0))], rows, 1

    monkeypatch.setattr(sheet_module, "get_generator", lambda _target: FakeGenerator())
    monkeypatch.setattr(sheet_build_module, "layout_sheet_rows", fake_layout)
    job = CharacterJob.from_dict(
        {
            "target": "fake",
            "animations": ["idle"],
            "authoring_description": "Adapter authoring prose.",
            "gameplay_description": "Adapter gameplay prose.",
            "dialogue_hints": {"barks": ["Adapter bark."]},
            "render": {"frame_width": 8, "frame_height": 8, "render_scale": 1},
        }
    )

    _pages, manifest = sheet_module.build_spritesheet(job)

    assert manifest["authoring_description"] == "Adapter authoring prose."
    assert manifest["gameplay_description"] == "Adapter gameplay prose."
    assert manifest["dialogue_hints"]["barks"] == ["Adapter bark."]


def test_review_character_configs_load_portable_notes():
    configs = (
        "alice.yaml",
        "bob.yaml",
        "craig.yaml",
        "erdish.yaml",
        "eve.yaml",
        "judy.yaml",
        "mallory.yaml",
        "oiler.yaml",
        "olivia.yaml",
        "peggy.yaml",
        "sybil.yaml",
        "trent.yaml",
        "trudy.yaml",
        "victor.yaml",
        "walter.yaml",
    )
    config_dir = (
        Path(__file__).resolve().parents[1]
        / "ambition_sprite2d_renderer"
        / "configs"
        / "review"
    )

    for filename in configs:
        job = CharacterJob.load(config_dir / filename)
        assert job.authoring_description
        assert job.gameplay_description
        assert job.dialogue_hints.get("barks")
