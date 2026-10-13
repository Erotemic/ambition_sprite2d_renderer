"""Structural rendering checks for the Ninja Heavy."""

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


def test_ninja_heavy_body_is_connected_in_every_pose(monkeypatch) -> None:
    """No limb, head, foot or held weapon is a piece that floats by itself.

    The dust of the club's hit is not a part of him. When he is down the club
    lies by him (the pose key ``held`` is 0): it can then be a second piece."""
    monkeypatch.setattr(ninja_heavy.X, "effects", lambda ctx: [])
    failures = []
    for animation, frame_count, _frame_ms in ninja_heavy.ROWS:
        for frame_idx in range(frame_count):
            image = ninja_heavy._render_frame(animation, frame_idx, frame_count)
            # A row that faces the viewer has no pose key ``held``: the club is in his hand.
            side = ninja_heavy.X.poses.get(animation) if animation not in ninja_heavy.X.front_poses else None
            held = side is None or float(ninja_heavy.X.full(side(frame_idx, frame_count))["held"]) >= 0.5
            significant = [size for size in _opaque_component_sizes(image) if size >= 20]
            if len(significant) not in ((1,) if held else (1, 2)):
                failures.append((animation, frame_idx, held, significant))

    assert failures == []


def test_ninja_heavy_shows_no_skin_but_at_his_eyes() -> None:
    """He is in black from his head to his feet (Jon, 2026-10-13: "Less skin,
    I like the dark clad in black look")."""
    def is_skin(pixel) -> bool:
        r, g, b, a = pixel
        # Skin; not the brass of his club (its green is far over its blue) and not his white papers.
        return a > 200 and r > 150 and r > g > b > 90 and g - b < 60 and r - b > 40

    image = ninja_heavy._render_frame("idle", 0, 6).convert("RGBA")
    box = image.getbbox()
    width, height = image.size
    pixels = image.load()
    rows_with_skin = {y for y in range(height) for x in range(width) if is_skin(pixels[x, y])}
    assert rows_with_skin, "his eyes are in a band of skin"
    # All of it is in his head: the top fifth of him.
    assert max(rows_with_skin) < box[1] + (box[3] - box[1]) * 0.2
