#!/usr/bin/env python3
"""How far the game's ground on the giant's shoulders is from the drawn shoulders, per row.

    uv run python scripts/measure_giant_shoulder_ground.py

For each row of the giant's sheet, at each tick (60 a second) of the row,
the height of each end of each shoulder in the frame that is drawn, against:

* before: the shoulder at rest (a ledge that does not follow the art);
* after: the game's ground, which follows the art
  (`ambition_characters::actor::SurfaceTable::segment`): each frame's surface
  in the middle of the frame's time, going smoothly to the next.

World units (1.3 a frame pixel). The worst of each row, and the worst
movement of the ground in one tick.
"""
from __future__ import annotations

from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import giant_art as g
from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import sprite_generator as sg

WORLD = g.WORLD_PER_PIXEL
TICK = 1.0 / 60.0
#: The rows that hold their last frame (the others loop).
ONE_SHOT_SUFFIXES = ("_windup", "_strike", "_hold", "_recover")
ONE_SHOT = {"death", "buck", "armed_buck", "hit", "armed_hit", "stomp", "clamp"}

_cache: dict = {}


def _drawn(row: str, count: int, frame: int) -> dict:
    key = (row, frame)
    if key not in _cache:
        _cache[key] = g.surfaces(g.pose_for(row, frame / count))
    return _cache[key]


def _frame_at(count: int, ms: int, t: float, looping: bool) -> int:
    step = int(max(0.0, t) / (ms / 1000.0))
    return step % count if looping else min(step, count - 1)


def _ground(row: str, count: int, ms: int, t: float, looping: bool) -> dict:
    """`SurfaceTable::segment`: frames from the middle of the first."""
    at = t / (ms / 1000.0) - 0.5
    at = at % count if looping else max(0.0, at)
    step, part = int(at), at - int(at)
    if looping:
        this, nxt = step % count, (step + 1) % count
    elif step + 1 >= count:
        this, nxt, part = count - 1, count - 1, 0.0
    else:
        this, nxt = step, step + 1
    a, b = _drawn(row, count, this), _drawn(row, count, nxt)
    return {k: tuple(tuple(p[j] + (q[j] - p[j]) * part for j in range(2)) for p, q in zip(a[k], b[k])) for k in a}


def main() -> None:
    rest = g.surfaces(g.pose_for("rest", 0.0))
    rows = []
    worst_step = 0.0
    for row, count, ms in sg.ANIMATIONS:
        looping = not (row.endswith(ONE_SHOT_SUFFIXES) or row in ONE_SHOT)
        before = after = 0.0
        last = None
        t = 0.0
        while t < count * ms / 1000.0:
            drawn = _drawn(row, count, _frame_at(count, ms, t, looping))
            ground = _ground(row, count, ms, t, looping)
            for name in drawn:
                for end in range(2):
                    before = max(before, abs(drawn[name][end][1] - rest[name][end][1]) * WORLD)
                    after = max(after, abs(drawn[name][end][1] - ground[name][end][1]) * WORLD)
                    if last is not None:
                        worst_step = max(worst_step, abs(ground[name][end][1] - last[name][end][1]) * WORLD)
            last = ground
            t += TICK
        rows.append((row, before, after))
    rows.sort(key=lambda r: -r[1])
    print(f"{'row':24s} {'before':>8s} {'after':>8s}")
    for row, before, after in rows:
        print(f"{row:24s} {before:8.1f} {after:8.1f}")
    print(f"{len(rows)} rows; worst before {max(r[1] for r in rows):.1f}, after {max(r[2] for r in rows):.1f}; "
          f"the ground moves at most {worst_step:.1f} in one tick")


if __name__ == "__main__":
    main()
