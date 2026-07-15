"""Structural rendering checks for the Iron Lotus heavy ninja."""

from __future__ import annotations

from collections import deque

from ambition_sprite2d_renderer.targets.characters import ninja_heavy


def _opaque_component_sizes(image, *, alpha_threshold: int = 128) -> list[int]:
    """Return 8-connected opaque-component sizes without optional scipy."""
    alpha = image.getchannel("A")
    pixels = alpha.load()
    width, height = image.size
    seen: set[tuple[int, int]] = set()
    sizes: list[int] = []

    for y in range(height):
        for x in range(width):
            if pixels[x, y] < alpha_threshold or (x, y) in seen:
                continue
            queue = deque([(x, y)])
            seen.add((x, y))
            size = 0
            while queue:
                px, py = queue.popleft()
                size += 1
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = px + dx, py + dy
                        point = (nx, ny)
                        if not (0 <= nx < width and 0 <= ny < height):
                            continue
                        if point in seen or pixels[nx, ny] < alpha_threshold:
                            continue
                        seen.add(point)
                        queue.append(point)
            sizes.append(size)

    return sorted(sizes, reverse=True)


def test_ninja_heavy_body_is_connected_in_every_pose() -> None:
    """No limb, head, foot, or held weapon may become a floating sticker."""
    failures = []
    for animation, frame_count, _frame_ms in ninja_heavy.ROWS:
        for frame_idx in range(frame_count):
            image = ninja_heavy._render_frame(
                animation,
                frame_idx,
                frame_count,
                include_effects=False,
            )
            significant = [
                size
                for size in _opaque_component_sizes(image)
                if size >= 20
            ]
            if len(significant) != 1:
                failures.append((animation, frame_idx, significant))

    assert failures == []
