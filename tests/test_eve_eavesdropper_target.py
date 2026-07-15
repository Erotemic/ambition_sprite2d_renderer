from __future__ import annotations

from pathlib import Path
import math

from ambition_sprite2d_renderer.registry import CharacterJob
from ambition_sprite2d_renderer.registry.character_generators import get_generator
from ambition_sprite2d_renderer.targets.characters import eve_eavesdropper as eve


ROOT = Path(__file__).resolve().parents[1]
CONFIG = (
    ROOT
    / "ambition_sprite2d_renderer"
    / "configs"
    / "review"
    / "eve.yaml"
)


def test_eve_config_uses_bespoke_target() -> None:
    job = CharacterJob.load(CONFIG)
    assert job.target == "eve_eavesdropper"
    assert job.archetype == "eve"
    assert get_generator(job.target).__class__ is eve.EveEavesdropperGenerator


def test_eve_layer_contract_keeps_arms_and_grips_visible() -> None:
    eve._validate_layer_z(eve.LAYER_Z)
    body_layers = {"cloak_back", "legs", "torso_cloak", "satchel", "hood", "face"}
    for arm in ("far_arm", "near_arm"):
        assert all(eve.LAYER_Z[arm] > eve.LAYER_Z[layer] for layer in body_layers)
    assert eve.LAYER_Z["horn"] > eve.LAYER_Z["near_arm"]
    assert eve.LAYER_Z["hands"] > eve.LAYER_Z["horn"]


def test_eve_renders_every_authored_frame_without_clipping() -> None:
    job = CharacterJob.load(CONFIG)
    generator = get_generator(job.target)
    spec = generator.sample_spec(job)
    assert list(generator.animations()) == ["idle", "walk", "talk", "interact"]

    for animation, metadata in generator.animations().items():
        for frame_index in range(metadata["frames"]):
            image = generator.render_frame(spec, animation, frame_index, (128, 128), job)
            assert image.mode == "RGBA"
            alpha = image.getchannel("A")
            # Ignore sub-16-alpha Lanczos ringing outside the authored silhouette.
            bbox = alpha.point(lambda value: 255 if value >= 16 else 0).getbbox()
            assert bbox is not None
            left, top, right, bottom = bbox
            assert left >= 1, (animation, frame_index, bbox)
            assert top >= 1, (animation, frame_index, bbox)
            assert right <= 127, (animation, frame_index, bbox)
            assert bottom <= 127, (animation, frame_index, bbox)


def test_listening_receiver_cups_ear_and_points_away_from_mouth() -> None:
    for animation in ("idle", "interact"):
        frame_count = eve.EveEavesdropperGenerator.ANIMATIONS[animation]["frames"]
        for frame_index in range(frame_count):
            pose = eve._pose(animation, frame_index, frame_count)
            limbs = eve._limb_points(pose)
            tip, collector = eve._horn_ends(pose, limbs)
            ear = eve._ear_point(pose)
            mouth = eve._mouth_point(pose)

            assert eve._sub(tip, ear) == (0.0, 0.0)
            assert math.dist(tip, mouth) >= 8.0
            axis = eve._norm(eve._sub(collector, tip))
            mouth_direction = eve._sub(mouth, tip)
            assert axis[0] * mouth_direction[0] + axis[1] * mouth_direction[1] < 0.0
            assert collector[0] <= ear[0] - 20.0


def test_eve_has_no_forbidden_raster_effects() -> None:
    assert not eve.source_uses_forbidden_raster_effects()
