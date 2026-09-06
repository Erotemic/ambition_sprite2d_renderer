"""Animation-key analysis helpers used by the rig editor.

The rig format stores channel keys, but that alone is not a useful description
of an animation's important poses: generated clips often contain a value on
every frame.  The editor therefore also supports clip-level ``pose_keys`` —
authoring bookmarks for the poses an artist considers structurally important.
They do not affect rendering or sheet publication.
"""

from __future__ import annotations

import math
from typing import Iterable, Optional, Sequence


def time_to_frame(t: float, frames: int, loop: bool) -> int:
    """Map normalized channel-key time to the nearest authored frame."""
    frames = max(1, int(frames))
    if loop:
        return int(round((float(t) % 1.0) * frames)) % frames
    if frames <= 1:
        return 0
    return max(0, min(frames - 1, int(round(float(t) * (frames - 1)))))


def channel_key_frames(clip: dict, channel: Optional[str] = None) -> dict[str, set[int]]:
    """Return explicit frame indices keyed by each channel."""
    frames = max(1, int(clip.get("frames", 1)))
    loop = bool(clip.get("loop", True))
    channels = clip.get("channels") or {}
    names: Iterable[str] = (channel,) if channel else channels
    result: dict[str, set[int]] = {}
    for name in names:
        spec = channels.get(name)
        if not spec or "keys" not in spec:
            result[name] = set()
            continue
        result[name] = {
            time_to_frame(float(key[0]), frames, loop)
            for key in spec.get("keys") or []
            if key
        }
    return result


def keyed_channels_at_frame(clip: dict, frame_idx: int) -> list[str]:
    """Names of channels with an explicit key at ``frame_idx``."""
    keyed = channel_key_frames(clip)
    return [name for name, frames in keyed.items() if int(frame_idx) in frames]


def _is_angle_channel(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ("angle", "pitch", "rotation")) or not any(
        token in lowered for token in ("_x", "_y", "lift", "opacity", "_vis", "scale")
    )


def _delta(a: float, b: float, angular: bool) -> float:
    d = float(b) - float(a)
    if angular:
        d = (d + 180.0) % 360.0 - 180.0
    return d


def suggest_pose_key_frames(doc, clip_name: str, max_keys: int = 6) -> list[int]:
    """Suggest a small set of representative key poses for a clip.

    The suggestion is intentionally editor-only.  It looks for direction
    changes / curvature across all driven channels, then fills temporal gaps so
    even clips authored with one channel key on every frame become readable as
    a handful of important poses plus in-betweens.
    """
    clip = doc.clips.get(clip_name) or {}
    frames = max(1, int(clip.get("frames", 1)))
    if frames <= 3:
        return list(range(frames))

    channels = list((clip.get("channels") or {}).keys())
    target = min(max(3, int(round(math.sqrt(frames))) + 1), max_keys, frames)
    loop = bool(clip.get("loop", True))
    chosen: set[int] = {0}
    if not loop:
        chosen.add(frames - 1)

    if channels:
        samples = [doc.sample(clip_name, doc.frame_time(clip_name, i)) for i in range(frames)]
        ranges: dict[str, float] = {}
        for name in channels:
            values = [float(sample.get(name, 0.0)) for sample in samples]
            ranges[name] = max(1.0, max(values) - min(values))

        scores: list[tuple[float, int]] = []
        for i in range(frames):
            if not loop and i in {0, frames - 1}:
                continue
            prev_i = (i - 1) % frames
            next_i = (i + 1) % frames
            score = 0.0
            for name in channels:
                angular = _is_angle_channel(name)
                prev_v = float(samples[prev_i].get(name, 0.0))
                value = float(samples[i].get(name, 0.0))
                next_v = float(samples[next_i].get(name, 0.0))
                d0 = _delta(prev_v, value, angular)
                d1 = _delta(value, next_v, angular)
                # Curvature finds reversals / anticipation poses.  A small
                # movement term still rewards visually distinct passing poses.
                score += (abs(d1 - d0) + 0.2 * (abs(d0) + abs(d1))) / ranges[name]
            scores.append((score, i))

        for _score, frame in sorted(scores, reverse=True):
            if len(chosen) >= target:
                break
            # Avoid filling adjacent frames before broader motion is covered.
            if all(min((frame - other) % frames, (other - frame) % frames) > 1 for other in chosen):
                chosen.add(frame)

    # Fill any remaining slots by repeatedly splitting the largest temporal gap.
    while len(chosen) < target:
        ordered = sorted(chosen)
        gaps: list[tuple[int, int, int]] = []
        for left, right in zip(ordered, ordered[1:]):
            gaps.append((right - left, left, right))
        if loop:
            gaps.append(((ordered[0] + frames) - ordered[-1], ordered[-1], ordered[0] + frames))
        elif ordered[-1] < frames - 1:
            gaps.append((frames - 1 - ordered[-1], ordered[-1], frames - 1))
        if not gaps:
            break
        _gap, left, right = max(gaps)
        candidate = ((left + right) // 2) % frames
        if candidate in chosen:
            for candidate in range(frames):
                if candidate not in chosen:
                    break
        chosen.add(candidate)

    return sorted(chosen)


def pose_key_frames(doc, clip_name: str) -> tuple[list[int], bool]:
    """Return ``(frames, explicit)`` for the clip's pose-key track."""
    clip = doc.clips.get(clip_name) or {}
    frames = max(1, int(clip.get("frames", 1)))
    raw = clip.get("pose_keys")
    if raw is not None:
        cleaned = sorted({max(0, min(frames - 1, int(frame))) for frame in raw})
        return cleaned, True
    return suggest_pose_key_frames(doc, clip_name), False


def neighbor_pose_keys(
    pose_keys: Sequence[int], current: int, frames: int, loop: bool
) -> tuple[Optional[int], Optional[int]]:
    """Nearest previous and next pose keys around ``current``."""
    ordered = sorted({int(frame) for frame in pose_keys if 0 <= int(frame) < frames})
    if not ordered:
        return None, None
    previous = next((frame for frame in reversed(ordered) if frame < current), None)
    following = next((frame for frame in ordered if frame > current), None)
    if loop and len(ordered) > 1:
        if previous is None:
            previous = ordered[-1]
        if following is None:
            following = ordered[0]
    return previous, following


def segment_frames(previous: Optional[int], following: Optional[int], frames: int, loop: bool) -> list[int]:
    """Frame indices in temporal order from previous key to next key."""
    if previous is None or following is None or frames <= 0:
        return []
    if previous <= following:
        return list(range(previous, following + 1))
    if loop:
        return list(range(previous, frames)) + list(range(0, following + 1))
    return []
