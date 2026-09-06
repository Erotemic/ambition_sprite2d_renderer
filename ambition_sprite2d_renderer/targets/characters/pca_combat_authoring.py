"""Bespoke fighter choreography refinements for the Perfect Cellular Automaton.

The first full-fighter pass intentionally seeded many semantic rows from PCA's
existing authored poses.  This pass graduates the important Smash-facing rows
from aliases into deliberate choreography while preserving the SVG geometry and
all unrelated GUI-authored clips.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping, MutableMapping, Sequence

from ...profiling import profile


def _keys(values: Sequence[float], times: Sequence[float] | None = None, *, ease: str = "smooth") -> dict:
    vals = [float(v) for v in values]
    if times is None:
        denom = max(1, len(vals) - 1)
        ts = [i / denom for i in range(len(vals))]
    else:
        ts = [float(v) for v in times]
    if len(vals) != len(ts):
        raise ValueError("keyframe values/times length mismatch")
    return {"keys": [[round(t, 4), round(v, 4), ease] for t, v in zip(ts, vals)]}


def _replace_channels(clip: Mapping[str, object], replacements: Mapping[str, object]) -> dict:
    out = deepcopy(dict(clip))
    channels = deepcopy(dict(out.get("channels") or {}))
    channels.update(deepcopy(dict(replacements)))
    out["channels"] = channels
    out["loop"] = False
    return out


@profile
def author_pca_combat_clips(data: MutableMapping[str, object]) -> MutableMapping[str, object]:
    """Make the alias-heavy Smash rows genuinely PCA-specific.

    The values intentionally stay in the established rig's channel vocabulary;
    no new bones or art are introduced.  Existing locomotion and already-bespoke
    aerial/special clips are preserved.
    """

    clips = data.get("clips")
    if not isinstance(clips, dict):
        return data

    def have(name: str) -> bool:
        return isinstance(clips.get(name), dict)

    times4 = (0.0, 0.28, 0.58, 1.0)
    times5 = (0.0, 0.22, 0.48, 0.70, 1.0)

    if have("parry"):
        clips["parry"] = _replace_channels(
            clips["parry"],
            {
                "near_arm_u": _keys([-69.34, -28.0, -78.0, -69.34], times4),
                "near_arm_l": _keys([-100.7, -42.0, -112.0, -100.7], times4),
                "far_arm_u": _keys([-55.43, -92.0, -48.0, -55.43], times4),
                "far_arm_l": _keys([-115.03, -46.0, -123.0, -115.03], times4),
                "near_arm_hand": _keys([8.0, -15.0, 12.0, 8.0], times4),
                "far_arm_hand": _keys([8.0, 15.0, -12.0, 8.0], times4),
                "torso": _keys([5.0, -6.0, 7.0, 5.0], times4),
                "root_y": _keys([4.0, 1.0, 5.0, 4.0], times4),
            },
        )

    if have("dash_attack"):
        clips["dash_attack"] = _replace_channels(
            clips["dash_attack"],
            {
                "root_x": _keys([0.0, 2.0, 13.0, 16.0, 4.0], times5),
                "torso": _keys([3.0, -15.0, 20.0, 23.0, 4.0], times5),
                "head": _keys([0.0, -5.0, 3.0, 2.0, 0.0], times5),
                "near_arm_u": _keys([-52.34, -8.0, -118.0, -122.0, -58.0], times5),
                "near_arm_l": _keys([-88.7, -124.0, 13.0, 8.0, -62.0], times5),
                "far_arm_u": _keys([-36.43, -6.0, -56.0, -62.0, -39.0], times5),
                "far_arm_l": _keys([-98.03, -126.0, -84.0, -88.0, -99.0], times5),
            },
        )

    if have("smash_forward"):
        clips["smash_forward"] = _replace_channels(
            clips["smash_forward"],
            {
                "root_x": _keys([0.0, -3.0, 0.0, 11.0, 3.0], times5),
                "root_y": _keys([0.0, 3.0, 2.0, -1.0, 0.0], times5),
                "torso": _keys([3.0, -18.0, -21.0, 26.0, 7.0], times5),
                "head": _keys([0.0, 6.0, 7.0, -6.0, 0.0], times5),
                "near_arm_u": _keys([-52.34, 8.0, 18.0, -111.0, -55.0], times5),
                "near_arm_l": _keys([-88.7, -121.0, -132.0, 2.0, -81.0], times5),
                "far_arm_u": _keys([-36.43, -1.0, 7.0, -96.0, -42.0], times5),
                "far_arm_l": _keys([-98.03, -129.0, -137.0, -8.0, -93.0], times5),
                "near_arm_hand": _keys([0.0, -8.0, -12.0, 5.0, 0.0], times5),
                "far_arm_hand": _keys([0.0, 8.0, 12.0, -5.0, 0.0], times5),
            },
        )

    if have("smash_up"):
        clips["smash_up"] = _replace_channels(
            clips["smash_up"],
            {
                "root_y": _keys([0.0, 9.0, 5.0, -8.0, 0.0], times5),
                "torso": _keys([3.0, 15.0, 18.0, -18.0, -2.0], times5),
                "head": _keys([0.0, 4.0, 4.0, -10.0, 0.0], times5),
                "near_arm_u": _keys([-52.34, -12.0, -6.0, -169.0, -91.0], times5),
                "near_arm_l": _keys([-88.7, -121.0, -125.0, -10.0, -48.0], times5),
                "far_arm_u": _keys([-36.43, -11.0, -5.0, -151.0, -74.0], times5),
                "far_arm_l": _keys([-98.03, -120.0, -124.0, -17.0, -57.0], times5),
                "near_arm_hand": _keys([0.0, 4.0, 6.0, -28.0, -12.0], times5),
                "far_arm_hand": _keys([0.0, -4.0, -6.0, 28.0, 12.0], times5),
            },
        )

    if have("smash_down"):
        clips["smash_down"] = _replace_channels(
            clips["smash_down"],
            {
                "root_y": _keys([7.0, 15.0, 17.0, 21.0, 10.0], times5),
                "torso": _keys([8.0, -5.0, -8.0, 23.0, 10.0], times5),
                "head": _keys([-2.0, 3.0, 3.0, -7.0, -2.0], times5),
                "near_arm_u": _keys([-52.34, 36.0, 46.0, -84.0, -55.0], times5),
                "near_arm_l": _keys([-68.7, -42.0, -39.0, 11.0, -61.0], times5),
                "far_arm_u": _keys([-38.43, -106.0, -116.0, -22.0, -41.0], times5),
                "far_arm_l": _keys([-83.03, -42.0, -39.0, -114.0, -86.0], times5),
            },
        )

    if have("grab"):
        clips["grab"] = _replace_channels(
            clips["grab"],
            {
                "root_x": _keys([0.0, 1.0, 5.0, 4.0, 0.0], times5),
                "torso": _keys([0.0, -3.0, 9.0, 7.0, 0.0], times5),
                "near_arm_u": _keys([0.0, -18.0, -105.0, -101.0, 0.0], times5),
                "near_arm_l": _keys([0.0, -94.0, 8.0, 5.0, 0.0], times5),
                "far_arm_u": _keys([0.0, -9.0, -93.0, -89.0, 0.0], times5),
                "far_arm_l": _keys([0.0, -101.0, 5.0, 3.0, 0.0], times5),
            },
        )

    # Throws each get a body trajectory rather than merely borrowing an attack.
    if have("throw_forward"):
        clips["throw_forward"] = _replace_channels(
            clips["throw_forward"],
            {
                "root_x": _keys([0.0, -2.0, 1.0, 10.0, 3.0], times5),
                "torso": _keys([4.0, -14.0, -16.0, 24.0, 6.0], times5),
                "near_arm_u": _keys([-52.0, 12.0, 18.0, -112.0, -56.0], times5),
                "near_arm_l": _keys([-88.0, -128.0, -132.0, 8.0, -75.0], times5),
                "far_arm_u": _keys([-36.0, 2.0, 10.0, -100.0, -44.0], times5),
                "far_arm_l": _keys([-98.0, -126.0, -132.0, -4.0, -90.0], times5),
            },
        )
    if have("throw_back"):
        clips["throw_back"] = _replace_channels(
            clips["throw_back"],
            {
                "root_x": _keys([0.0, 3.0, -5.0, -11.0, -2.0], times5),
                "torso": _keys([3.0, 14.0, -20.0, -25.0, 3.0], times5),
                "near_arm_u": _keys([-52.0, -104.0, -22.0, 40.0, -55.0], times5),
                "near_arm_l": _keys([-88.0, 5.0, -118.0, -48.0, -80.0], times5),
                "far_arm_u": _keys([-36.0, -91.0, -11.0, 35.0, -39.0], times5),
                "far_arm_l": _keys([-98.0, 2.0, -121.0, -54.0, -92.0], times5),
            },
        )
    if have("throw_up"):
        clips["throw_up"] = _replace_channels(
            clips["throw_up"],
            {
                "root_y": _keys([0.0, 7.0, 6.0, -7.0, 0.0], times5),
                "torso": _keys([3.0, 14.0, 18.0, -19.0, -2.0], times5),
                "near_arm_u": _keys([-52.0, -14.0, -6.0, -171.0, -88.0], times5),
                "far_arm_u": _keys([-36.0, -9.0, -4.0, -154.0, -72.0], times5),
            },
        )
    if have("throw_down"):
        clips["throw_down"] = _replace_channels(
            clips["throw_down"],
            {
                "root_y": _keys([8.0, 14.0, 17.0, 22.0, 10.0], times5),
                "torso": _keys([8.0, -5.0, -8.0, 24.0, 10.0], times5),
                "near_arm_u": _keys([-52.0, 34.0, 43.0, -83.0, -55.0], times5),
                "far_arm_u": _keys([-38.0, -104.0, -113.0, -23.0, -41.0], times5),
            },
        )

    if have("final_smash"):
        clips["final_smash"] = _replace_channels(
            clips["final_smash"],
            {
                "root_x": _keys([0.0, 0.0, 0.0, 0.0, 0.0], times5),
                "root_y": _keys([0.0, -4.0, -8.0, -11.0, -4.0], times5),
                "torso": _keys([0.0, -14.0, -18.0, 8.0, 0.0], times5),
                "head": _keys([0.0, 5.0, 6.0, -4.0, 0.0], times5),
                "near_arm_u": _keys([0.0, 28.0, 45.0, -151.0, -70.0], times5),
                "near_arm_l": _keys([0.0, -64.0, -48.0, -23.0, -70.0], times5),
                "far_arm_u": _keys([0.0, -116.0, -132.0, -23.0, -54.0], times5),
                "far_arm_l": _keys([0.0, -61.0, -48.0, -110.0, -80.0], times5),
                "near_arm_hand": _keys([0.0, -18.0, -24.0, 12.0, 0.0], times5),
                "far_arm_hand": _keys([0.0, 18.0, 24.0, -12.0, 0.0], times5),
            },
        )

    return data


__all__ = ["author_pca_combat_clips"]
