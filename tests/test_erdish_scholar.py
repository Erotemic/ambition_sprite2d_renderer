from __future__ import annotations

from pathlib import Path

from PIL import Image

from ambition_sprite2d_renderer.registry import CharacterJob
from ambition_sprite2d_renderer.registry.character_generators import get_generator


CONFIG = (
    Path(__file__).resolve().parents[1]
    / "ambition_sprite2d_renderer"
    / "configs"
    / "review"
    / "erdish.yaml"
)


def _opaque_component_sizes(image: Image.Image, alpha_threshold: int = 16) -> list[int]:
    alpha = image.getchannel("A")
    pixels = alpha.load()
    width, height = alpha.size
    seen: set[tuple[int, int]] = set()
    sizes: list[int] = []
    for y in range(height):
        for x in range(width):
            if pixels[x, y] < alpha_threshold or (x, y) in seen:
                continue
            stack = [(x, y)]
            seen.add((x, y))
            size = 0
            while stack:
                px, py = stack.pop()
                size += 1
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = px + dx, py + dy
                        if not (0 <= nx < width and 0 <= ny < height):
                            continue
                        point = (nx, ny)
                        if point in seen or pixels[nx, ny] < alpha_threshold:
                            continue
                        seen.add(point)
                        stack.append(point)
            sizes.append(size)
    return sorted(sizes, reverse=True)


def test_erdish_uses_bespoke_prop_free_generator():
    job = CharacterJob.load(CONFIG)
    generator = get_generator(job.target)

    assert job.target == "erdish_scholar"
    assert job.held_item is None
    assert generator.USES_PROPS is False
    assert generator.USES_DROP_SHADOW is False


def test_erdish_has_the_runtime_playable_movement_rows():
    job = CharacterJob.load(CONFIG)
    generator = get_generator(job.target)
    required = {
        "idle",
        "walk",
        "run",
        "jump",
        "fall",
        "dash_startup",
        "dash",
        "crouch",
        "crouch_walk",
        "slide",
        "roll",
        "wall_grab",
        "wall_jump",
        "ledge_grab",
        "ledge_getup",
        "ledge_roll",
        "climb",
        "swim",
        "block",
        "hit",
        "death",
        "interact",
    }
    assert required <= set(generator.animations())


def test_every_erdish_pose_is_one_connected_character():
    job = CharacterJob.load(CONFIG)
    generator = get_generator(job.target)
    spec = generator.sample_spec(job)

    for animation, info in generator.animations().items():
        for frame_index in range(info["frames"]):
            frame = generator.render_frame(
                spec,
                animation,
                frame_index,
                (128, 128),
                job,
            )
            sizes = _opaque_component_sizes(frame)
            assert sizes, (animation, frame_index)
            assert len(sizes) == 1, (animation, frame_index, sizes)
            assert sizes[0] > 1600, (animation, frame_index, sizes)


def test_erdish_frames_remain_inside_the_authored_canvas():
    job = CharacterJob.load(CONFIG)
    generator = get_generator(job.target)
    spec = generator.sample_spec(job)

    for animation, info in generator.animations().items():
        for frame_index in range(info["frames"]):
            frame = generator.render_frame(
                spec,
                animation,
                frame_index,
                (128, 128),
                job,
            )
            bbox = frame.getbbox()
            assert bbox is not None
            left, top, right, bottom = bbox
            assert left >= 2, (animation, frame_index, bbox)
            assert top >= 2, (animation, frame_index, bbox)
            assert right <= 126, (animation, frame_index, bbox)
            assert bottom <= 126, (animation, frame_index, bbox)
