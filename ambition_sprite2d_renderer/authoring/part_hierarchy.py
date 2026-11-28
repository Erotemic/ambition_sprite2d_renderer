"""Parent-relative interpolation of the published rigid part transforms.

Keep the keyframes and their draw order. A parent transforms the child's
pivot and angle, not its texture scale. A texture change is discrete. This
module mirrors the runtime's ``rigged::hierarchy`` interpolation rule.
"""
from __future__ import annotations

from dataclasses import replace
import math


def hierarchy_order(parents, tracks):
    """Return (track, parent) pairs in parent-first order."""
    pending = {name: None for name in parents.values()}
    pending.update(parents)
    unknown = set(pending) - set(tracks)
    if unknown:
        raise ValueError(f'unknown hierarchy tracks: {sorted(unknown)}')
    result = []
    while pending:
        ready = sorted(name for name, parent in pending.items() if parent not in pending)
        if not ready:
            raise ValueError('cycle in track_parents')
        for name in ready:
            result.append((name, pending.pop(name)))
    return result


def validate_hierarchy(parents, clips):
    if not parents:
        return
    tracks = {d.track for _, frames in clips.values() for frame in frames for d in frame}
    order = dict(hierarchy_order(parents, tracks))
    for row, (_, frames) in clips.items():
        for index, frame in enumerate(frames):
            present = set()
            for d in frame:
                if d.track not in order:
                    continue
                if d.track in present:
                    raise ValueError(f'{row}:{index} draws hierarchy track {d.track} twice')
                present.add(d.track)
                if (not all(math.isfinite(x) for x in (*d.at, d.rotation, *d.scale))
                        or any(x == 0 for x in d.scale)):
                    raise ValueError(f'{row}:{index} has an invalid hierarchy transform')
            for name in present:
                parent = order[name]
                if parent is not None and parent not in present:
                    raise ValueError(f'{row}:{index} draws {name} without parent {parent}')


def _rotate(xy, angle):
    c, s = math.cos(angle), math.sin(angle)
    return c * xy[0] - s * xy[1], s * xy[0] + c * xy[1]


def _local(draw, parent):
    if parent is None:
        return draw.at, draw.rotation
    return (_rotate((draw.at[0] - parent.at[0], draw.at[1] - parent.at[1]), -parent.rotation),
            draw.rotation - parent.rotation)


def _turn(a, b):
    return (b - a + math.pi) % math.tau - math.pi


def articulate(parents, before, after, t, draws, *, destination=False):
    """Apply the parent graph to a flat tween or blend, in place.

    A track that exists at just one endpoint keeps its local transform from
    that endpoint. If a composed pose removes a parent, use world space.
    ``draws`` has the source order for a tween and the destination order for
    a blend. The selection of rasters, opacity, and tint stays independent.
    """
    if not parents:
        return draws
    a = {d.track: d for d in before if d.track is not None}
    b = {d.track: d for d in after if d.track is not None}
    by_track = {d.track: i for i, d in enumerate(draws) if d.track is not None}
    # A composition may omit some tracks. The graph itself is still valid.
    order = hierarchy_order(parents, set(parents) | set(parents.values()))
    for name, parent in order:
        if name not in by_track:
            continue
        x, y = a.get(name), b.get(name)
        attach = (parent in by_track and (x is None or parent in a)
                  and (y is None or parent in b))
        p, q = (a.get(parent), b.get(parent)) if attach else (None, None)
        start = _local(x, p) if x is not None else _local(y, q)
        end = _local(y, q) if y is not None else start
        at = tuple(i + (j - i) * t for i, j in zip(start[0], end[0]))
        rotation = start[1] + _turn(start[1], end[1]) * t
        if attach:
            pivot = draws[by_track[parent]]
            delta = _rotate(at, pivot.rotation)
            at = pivot.at[0] + delta[0], pivot.at[1] + delta[1]
            rotation += pivot.rotation
        index = by_track[name]
        scale = draws[index].scale
        if destination and x is not None and y is not None and any(i * j <= 0 for i, j in zip(x.scale, y.scale)):
            scale = y.scale
        draws[index] = replace(draws[index], at=at, rotation=rotation, scale=scale)
    return draws


def blend_draws(before, after, t, parents=None):
    """The runtime clip-blend rule, for offline preview and tests."""
    t = max(0.0, min(1.0, t))
    if t >= 1.0:
        return list(after)
    a = {d.track: d for d in before if d.track is not None}
    draws = []
    for d in after:
        old = a.get(d.track)
        if old is None:
            draws.append(d)
        else:
            draws.append(replace(d,
                at=tuple(i + (j - i) * t for i, j in zip(old.at, d.at)),
                rotation=old.rotation + _turn(old.rotation, d.rotation) * t,
                scale=tuple(i + (j - i) * t for i, j in zip(old.scale, d.scale))))
    return articulate(parents or {}, before, after, t, draws, destination=True)
