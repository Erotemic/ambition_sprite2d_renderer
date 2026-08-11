#!/usr/bin/env python3
"""Build the canonical SVG rigs for Patent Clerk and Carl Stargan.

The manually traced SVGs in ``assets/`` are the art/geometry authority.  Their
source pose may be intentionally exploded or splayed to expose rigid pieces;
natural gameplay pose and IK anatomy are authored separately here.  This
builder extracts explicit part/joint geometry and authors animation clips; it
never recreates character artwork.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib
import importlib.machinery
import importlib.metadata
import importlib.util
import inspect
import json
import math
import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from PIL import ImageChops

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


BUILDER_VERSION = 17


def _is_extension_path(path: Path) -> bool:
    """Return whether *path* names a CPython native extension module."""

    value = str(path)
    return any(value.endswith(suffix) for suffix in importlib.machinery.EXTENSION_SUFFIXES)


def _native_resvg_origin(resvg_py: object) -> Path | None:
    """Locate the compiled implementation behind the public package wrapper.

    ``resvg_py`` is distributed as a normal Python package whose public
    ``__init__.py`` re-exports functions from a PyO3 extension module.  The
    package's own ``__file__`` is therefore expected to end in ``.py`` even
    though ``svg_to_bytes`` is native code.
    """

    svg_to_bytes = getattr(resvg_py, "svg_to_bytes", None)
    if not callable(svg_to_bytes) or not inspect.isbuiltin(svg_to_bytes):
        return None

    candidates: list[Path] = []

    implementation_name = getattr(svg_to_bytes, "__module__", "")
    if implementation_name:
        try:
            implementation = importlib.import_module(implementation_name)
        except (ImportError, ValueError):
            implementation = None
        implementation_path = Path(getattr(implementation, "__file__", ""))
        if implementation_path.name:
            candidates.append(implementation_path)

    package_name = getattr(resvg_py, "__name__", "resvg_py")
    for child_name in ("resvg_py", "_resvg_py"):
        try:
            child_spec = importlib.util.find_spec(f"{package_name}.{child_name}")
        except (ImportError, ModuleNotFoundError, ValueError):
            child_spec = None
        if child_spec is not None and child_spec.origin:
            candidates.append(Path(child_spec.origin))

    package_path = Path(getattr(resvg_py, "__file__", ""))
    if package_path.name:
        package_dir = package_path.parent
        for suffix in importlib.machinery.EXTENSION_SUFFIXES:
            candidates.extend(sorted(package_dir.glob(f"*{suffix}")))

    for candidate in candidates:
        if candidate.name and _is_extension_path(candidate):
            return candidate.resolve()

    return None


def _require_native_resvg() -> tuple[str, str]:
    """Return the native implementation path and installed package version.

    The canonical rig geometry depends on resvg's exact SVG rasterization.
    Substituting another renderer changes part bounds and joint centers, so we
    deliberately reject Python shims and fallback renderers here while
    accepting the official package's Python ``__init__.py`` wrapper.
    """

    try:
        import resvg_py
    except ModuleNotFoundError as ex:
        raise RuntimeError(
            "canonical scientist SVG rigs require the native resvg_py package; "
            "run `uv sync` from tools/ambition_sprite2d_renderer, then rerun "
            "this command"
        ) from ex

    if not callable(getattr(resvg_py, "svg_to_bytes", None)):
        raise RuntimeError("native resvg_py is missing svg_to_bytes")

    native_path = _native_resvg_origin(resvg_py)
    if native_path is None:
        package_path = Path(getattr(resvg_py, "__file__", ""))
        implementation_name = getattr(resvg_py.svg_to_bytes, "__module__", "<unknown>")
        raise RuntimeError(
            "resvg_py imported, but its compiled PyO3 implementation could not "
            f"be located (package={package_path or '<unknown>'}, "
            f"svg_to_bytes.__module__={implementation_name!r}); refusing a "
            "pure-Python SVG fallback"
        )

    try:
        version = importlib.metadata.version("resvg-py")
    except importlib.metadata.PackageNotFoundError:
        try:
            version = importlib.metadata.version("resvg_py")
        except importlib.metadata.PackageNotFoundError as ex:
            raise RuntimeError(
                "resvg_py imported, but no installed package metadata was found; "
                "refusing to build unverifiable canonical rig geometry"
            ) from ex
    return str(native_path), version


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (  # noqa: E402
    HumanoidViewSpec,
    LimbPoseHint,
    build_humanoid_view_document,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument, sample_channel_spec  # noqa: E402
from ambition_sprite2d_renderer.authoring.fighter_motion_catalog import (  # noqa: E402
    invert_rotation_channel,
    materialize_motion_rows,
    validate_motion_coverage,
)
from ambition_sprite2d_renderer.targets.characters.patent_clerk_motion import (  # noqa: E402
    APPLICABLE_MOTION_SCOPES as PATENT_MOTION_SCOPES,
    FIGHTER_MOTION_COVERAGE as PATENT_MOTION_COVERAGE,
    PATENT_ROWS,
)
from ambition_sprite2d_renderer.targets.characters.carl_stargan_motion import (  # noqa: E402
    APPLICABLE_MOTION_SCOPES as CARL_MOTION_SCOPES,
    CARL_ROWS,
    FIGHTER_MOTION_COVERAGE as CARL_MOTION_COVERAGE,
    LOOPING_ROWS as CARL_LOOPING_ROWS,
    POSE_ALIASES as CARL_POSE_ALIASES,
)

INK_NS = "http://www.inkscape.org/namespaces/inkscape"
INK_LABEL = f"{{{INK_NS}}}label"


@dataclass(frozen=True)
class CharacterSpec:
    name: str
    svg_name: str
    view: str
    frame_size: tuple[int, int]
    target_height: float
    ground_margin: float
    collision_scale: float
    rows: tuple[tuple[str, int, int], ...]
    hands_follow_forearms: bool = False
    natural_arm_pose: Mapping[str, LimbPoseHint] | None = None
    arm_max_reach_ratio: float | None = None

    @property
    def svg_path(self) -> Path:
        return ROOT / "assets" / self.svg_name

    @property
    def rig_dir(self) -> Path:
        return (
            ROOT
            / "ambition_sprite2d_renderer"
            / "targets"
            / "characters"
            / "rigged"
            / self.name
        )

    @property
    def rig_path(self) -> Path:
        return self.rig_dir / f"{self.name}_side.rig.json"


SPECS = {
    "patent_clerk": CharacterSpec(
        name="patent_clerk",
        svg_name="patent-clerk.svg",
        view="Patent Clerk - Side Left",
        frame_size=(176, 176),
        target_height=118.0,
        ground_margin=26.0,
        collision_scale=1.66,
        rows=PATENT_ROWS,
        hands_follow_forearms=True,
        # The SVG is deliberately splayed so all rigid pieces are visible.
        # Natural gameplay anatomy is authored separately.  Each hint is in
        # frame coordinates relative to (center_x, ground_y): hand target plus
        # the elbow position that identifies the intended two-bone IK branch.
        # Both lower arms point generally west with a small relaxed bend.
        natural_arm_pose={
            "near": LimbPoseHint(target=(-12.0, -57.0), joint=(2.5, -64.0)),
            "far": LimbPoseHint(target=(-20.0, -49.0), joint=(-9.0, -59.0)),
        },
        # Keep a small visible elbow bend even when a gesture reaches beyond
        # the physical chain length instead of letting IK snap ruler-straight.
        arm_max_reach_ratio=0.98,
    ),
    "carl_stargan": CharacterSpec(
        name="carl_stargan",
        svg_name="carl-stargan.svg",
        view="Carl Stargan - Side Left",
        frame_size=(160, 160),
        target_height=112.0,
        ground_margin=24.0,
        collision_scale=1.58,
        rows=CARL_ROWS,
        hands_follow_forearms=True,
        # Carl's SVG is also authored as a fully splayed paper-doll layout so
        # every rigid piece stays visible while tracing. Gameplay motion should
        # instead start from a relaxed west-facing stance with both forearms
        # folding back toward the body.
        natural_arm_pose={
            # Targets are deliberately comfortably inside each chain's reach:
            # Carl should retain a visible elbow bend instead of snapping into
            # the straight-armed SVG paper-doll stance.
            "near": LimbPoseHint(target=(-12.0, -58.0), joint=(-4.3, -72.7)),
            "far": LimbPoseHint(target=(-22.0, -52.0), joint=(-12.8, -61.5)),
        },
        arm_max_reach_ratio=0.98,
    ),
}


def const(value: float) -> dict:
    return {"const": round(float(value), 4)}


def expr(value: str) -> dict:
    return {"expr": value}


def keys(values: Sequence[float], *, loop: bool, ease: str = "smooth") -> dict:
    n = len(values)
    if n == 0:
        return {"keys": []}
    denom = n if loop else max(1, n - 1)
    rows = [[round(i / denom, 6), round(float(value), 4), ease] for i, value in enumerate(values)]
    if loop:
        rows.append([1.0, round(float(values[0]), 4), ease])
    return {"keys": rows}


def _rest(
    doc: Mapping[str, object],
    *,
    hands_follow_forearms: bool = False,
    natural_arm_pose: Mapping[str, LimbPoseHint] | None = None,
) -> dict[str, float]:
    out: dict[str, float] = {}
    for entry in doc.get("ik_legs", []):  # type: ignore[union-attr]
        prefix = str(entry["channel_prefix"])
        out[f"{prefix}_x"] = float(entry["rest_x"])
        out[f"{prefix}_lift"] = float(entry["rest_lift"])
        out[f"{prefix}_pitch"] = float(entry["rest_pitch"])
        out[f"{prefix}_bend"] = float(entry["bend"])
    for entry in doc.get("ik_chains", []):  # type: ignore[union-attr]
        prefix = str(entry["channel_prefix"])
        out[f"{prefix}_x"] = float(entry["rest_x"])
        out[f"{prefix}_y"] = float(entry["rest_y"])
        out[f"{prefix}_pitch"] = float(entry["rest_pitch"])
        out[f"{prefix}_bend"] = float(entry["bend"])
    if hands_follow_forearms:
        out["_hands_follow_forearms"] = 1.0
    if natural_arm_pose is not None:
        for side in ("near", "far"):
            hint = natural_arm_pose.get(side)
            if hint is None:
                continue
            out[f"_natural_{side}_hand_x"] = float(hint.target[0])
            out[f"_natural_{side}_hand_y"] = float(hint.target[1])
    return out


def _clip(frames: int, duration_ms: int, *, loop: bool, channels: Mapping[str, dict]) -> dict:
    return {
        "loop": bool(loop),
        "frames": int(frames),
        "duration_ms": int(duration_ms),
        "channels": dict(channels),
    }


def _hand_anchor(
    rest: Mapping[str, float], prefix: str, *, compact: bool
) -> tuple[float, float]:
    if prefix == "near_hand":
        legacy_x = 17.0
        legacy_y = -50.0 if compact else -48.0
    elif prefix == "far_hand":
        legacy_x = -13.0
        legacy_y = -49.0 if compact else -47.0
    else:
        raise ValueError(f"unknown hand prefix {prefix!r}")
    return (
        float(rest.get(f"_natural_{prefix}_x", legacy_x)),
        float(rest.get(f"_natural_{prefix}_y", legacy_y)),
    )


def _rebase_hand_trajectory(
    rest: Mapping[str, float],
    prefix: str,
    xs: Sequence[float],
    ys: Sequence[float],
    *,
    compact: bool,
) -> tuple[list[float], list[float]]:
    """Move legacy pose deltas onto the character's natural side-view arms.

    Scientist clips were originally authored around generic neutral anchors
    (near=(17,-50), far=(-13,-49) for compact sheets).  Patent Clerk's SVG is
    an exploded/splayed authoring layout, not a neutral pose.  Rebase the
    existing gesture deltas onto his natural wrist targets so all ordinary
    clips keep the intended motion while both forearms rest toward west.
    """
    anchor_x, anchor_y = _hand_anchor(rest, prefix, compact=compact)
    if prefix == "near_hand":
        legacy_x = 17.0
        legacy_y = -50.0 if compact else -48.0
    else:
        legacy_x = -13.0
        legacy_y = -49.0 if compact else -47.0
    return (
        [anchor_x + (float(value) - legacy_x) for value in xs],
        [anchor_y + (float(value) - legacy_y) for value in ys],
    )


def _neutral(rest: Mapping[str, float], *, compact: bool) -> dict[str, dict]:
    near_x, near_y = _hand_anchor(rest, "near_hand", compact=compact)
    far_x, far_y = _hand_anchor(rest, "far_hand", compact=compact)
    return {
        "near_hand_x": const(near_x),
        "near_hand_y": const(near_y),
        "far_hand_x": const(far_x),
        "far_hand_y": const(far_y),
        "near_foot_x": const(10.0),
        "near_foot_lift": const(0.0),
        "near_foot_pitch": const(rest["near_foot_pitch"]),
        "far_foot_x": const(-10.0),
        "far_foot_lift": const(0.0),
        "far_foot_pitch": const(rest["far_foot_pitch"]),
    }


def _locomotion(rest: Mapping[str, float], frames: int, duration: int, *, run: bool, compact: bool) -> dict:
    stride = 15.0 if run else 10.0
    lift = 9.0 if run else 6.0
    arm = 8.0 if run else 5.0
    near_hand_x, near_hand_y = _hand_anchor(rest, "near_hand", compact=compact)
    far_hand_x, far_hand_y = _hand_anchor(rest, "far_hand", compact=compact)
    base = _neutral(rest, compact=compact)
    base.update(
        {
            "root_y": expr(f"{1.8 if run else 1.0}*abs(sin(tau*t))-{0.8 if run else 0.4}"),
            "pelvis": expr(f"{2.8 if run else 1.5}*sin(tau*t)"),
            "torso": expr(f"{-3.4 if run else -1.8}*sin(tau*t)"),
            "head": expr(f"{1.8 if run else 1.0}*sin(tau*t)"),
            "near_foot_x": expr(f"10+{stride}*sin(tau*t)"),
            "near_foot_lift": expr(f"{lift}*max(0,-sin(tau*t))"),
            "far_foot_x": expr(f"-10-{stride}*sin(tau*t)"),
            "far_foot_lift": expr(f"{lift}*max(0,sin(tau*t))"),
            "near_hand_x": expr(f"{near_hand_x}-{arm}*sin(tau*t)"),
            "near_hand_y": expr(f"{near_hand_y}+2*sin(tau*t)"),
            "far_hand_x": expr(f"{far_hand_x}+{arm}*sin(tau*t)"),
            "far_hand_y": expr(f"{far_hand_y}-2*sin(tau*t)"),
        }
    )
    return _clip(frames, duration, loop=True, channels=base)


def _pose(rest: Mapping[str, float], frames: int, duration: int, *, loop: bool = False,
          compact: bool = False, root_y: Sequence[float] | None = None,
          pelvis: Sequence[float] | None = None, torso: Sequence[float] | None = None,
          head: Sequence[float] | None = None,
          near_hand: tuple[Sequence[float], Sequence[float], Sequence[float]] | None = None,
          far_hand: tuple[Sequence[float], Sequence[float], Sequence[float]] | None = None,
          near_foot: tuple[Sequence[float], Sequence[float], Sequence[float]] | None = None,
          far_foot: tuple[Sequence[float], Sequence[float], Sequence[float]] | None = None) -> dict:
    channels = _neutral(rest, compact=compact)
    for name, values in (("root_y", root_y), ("pelvis", pelvis), ("torso", torso), ("head", head)):
        if values is not None:
            channels[name] = keys(values, loop=loop)
    for prefix, triplet in (("near_hand", near_hand), ("far_hand", far_hand)):
        if triplet is not None:
            x_values, y_values = _rebase_hand_trajectory(
                rest, prefix, triplet[0], triplet[1], compact=compact
            )
            channels[f"{prefix}_x"] = keys(x_values, loop=loop)
            channels[f"{prefix}_y"] = keys(y_values, loop=loop)
            if not rest.get("_hands_follow_forearms", 0.0):
                channels[f"{prefix}_pitch"] = keys(triplet[2], loop=loop)
    for prefix, triplet in (("near_foot", near_foot), ("far_foot", far_foot)):
        if triplet is not None:
            channels[f"{prefix}_x"] = keys(triplet[0], loop=loop)
            channels[f"{prefix}_lift"] = keys(triplet[1], loop=loop)
            channels[f"{prefix}_pitch"] = keys(triplet[2], loop=loop)
    return _clip(frames, duration, loop=loop, channels=channels)


def _common_clips(spec: CharacterSpec, doc: Mapping[str, object], *, compact: bool) -> dict[str, dict]:
    r = _rest(
        doc,
        hands_follow_forearms=spec.hands_follow_forearms,
        natural_arm_pose=spec.natural_arm_pose,
    )
    rows = {name: (frames, duration) for name, frames, duration in spec.rows}
    clips: dict[str, dict] = {}
    f, d = rows["idle"]
    idle = _neutral(r, compact=compact)
    _near_idle_x, near_idle_y = _hand_anchor(r, "near_hand", compact=compact)
    _far_idle_x, far_idle_y = _hand_anchor(r, "far_hand", compact=compact)
    idle.update({
        "root_y": expr("0.65*sin(tau*t)"),
        "torso": expr("1.1*sin(tau*t)"),
        "head": expr("-0.8*sin(tau*t)"),
        "near_hand_y": expr(f"{near_idle_y}+0.8*sin(tau*t)"),
        "far_hand_y": expr(f"{far_idle_y}-0.6*sin(tau*t)"),
    })
    clips["idle"] = _clip(f, d, loop=True, channels=idle)
    clips["walk"] = _locomotion(r, *rows["walk"], run=False, compact=compact)
    clips["run"] = _locomotion(r, *rows["run"], run=True, compact=compact)

    for name in ("crouch", "crouch_walk"):
        f, d = rows[name]
        loop = name == "crouch_walk"
        clips[name] = _pose(
            r, f, d, loop=loop, compact=compact,
            root_y=[10, 12, 13, 12, 10, 11] if not loop else [11, 12, 13, 12, 11, 10, 11, 12],
            torso=[8, 10, 11, 10, 8, 9] if not loop else [8, 10, 9, 7, 8, 10, 9, 7],
            head=[-5, -6, -7, -6, -5, -5] if not loop else [-5, -6, -5, -4, -5, -6, -5, -4],
            near_hand=([9, 7, 5, 7, 9, 8], [-42, -40, -39, -40, -42, -41], [65]*6),
            far_hand=([-8, -7, -6, -7, -8, -8], [-43, -41, -40, -41, -43, -42], [115]*6),
        )

    f, d = rows["jump"]
    clips["jump"] = _pose(
        r, f, d, compact=compact,
        root_y=[4, -3, -12, -16, -10, -2], torso=[8, 5, 0, -3, -1, 3], head=[-4, -2, 1, 3, 1, -1],
        near_hand=([14, 8, 1, -2, 4, 12], [-54, -62, -72, -78, -68, -56], [70, 50, 30, 20, 40, 65]),
        far_hand=([-11, -5, 2, 4, -2, -9], [-53, -61, -70, -75, -66, -55], [110, 130, 150, 160, 140, 115]),
        near_foot=([10, 8, 4, 2, 5, 9], [0, 5, 14, 18, 10, 2], [r["near_foot_pitch"], r["near_foot_pitch"]-8, r["near_foot_pitch"]-16, r["near_foot_pitch"]-18, r["near_foot_pitch"]-8, r["near_foot_pitch"]]),
        far_foot=([-10, -8, -4, -2, -5, -9], [0, 4, 12, 16, 9, 2], [r["far_foot_pitch"], r["far_foot_pitch"]+8, r["far_foot_pitch"]+16, r["far_foot_pitch"]+18, r["far_foot_pitch"]+8, r["far_foot_pitch"]]),
    )
    f, d = rows["fall"]
    clips["fall"] = _pose(r, f, d, loop=True, compact=compact,
        root_y=[-8,-9,-10,-9,-8,-7], torso=[-3,-5,-4,-2,-1,-2], head=[3,4,3,2,1,2],
        near_hand=([6,4,3,4,6,7],[-66,-69,-71,-69,-66,-64],[35,30,25,30,35,40]),
        far_hand=([-3,-1,0,-1,-3,-4],[-64,-67,-69,-67,-64,-62],[145,150,155,150,145,140]))

    if "land_hard" in rows:
        f, d = rows["land_hard"]
        clips["land_hard"] = _pose(r, f, d, compact=compact,
            root_y=[-5,4,13,16,11,7,3,0][:f], torso=[-4,8,16,19,12,6,2,0][:f], head=[3,-5,-10,-12,-7,-3,-1,0][:f],
            near_hand=([10,7,3,1,4,8,12,17][:f],[-55,-45,-37,-34,-39,-44,-48,-50][:f],[70,65,60,55,60,70,75,80][:f]),
            far_hand=([-8,-5,-2,0,-3,-7,-10,-13][:f],[-54,-44,-36,-33,-38,-43,-47,-49][:f],[110,115,120,125,120,110,105,100][:f]))
    if "land_recovery" in rows:
        f, d = rows["land_recovery"]
        clips["land_recovery"] = _pose(r, f, d, compact=compact,
            root_y=[11,9,6,3,1,0], torso=[12,9,6,3,1,0], head=[-7,-5,-3,-2,-1,0])

    for name in ("dash_startup", "dash"):
        if name not in rows:
            continue
        f, d = rows[name]
        clips[name] = _pose(r, f, d, loop=name == "dash", compact=compact,
            root_y=[0,-1,-2,-1,0,1][:f], torso=[8,13,17,13,8,10][:f], head=[-5,-8,-10,-8,-5,-6][:f],
            near_hand=([12,7,1,-4,-1,5][:f],[-49,-47,-45,-43,-45,-48][:f],[80,72,65,58,65,74][:f]),
            far_hand=([-9,-4,2,7,4,-2][:f],[-48,-46,-44,-42,-44,-47][:f],[100,108,115,122,115,106][:f]),
            near_foot=([12,18,23,18,12,8][:f],[0,1,4,1,0,2][:f],[r["near_foot_pitch"]]*f),
            far_foot=([-11,-16,-21,-17,-12,-8][:f],[0,3,7,3,0,1][:f],[r["far_foot_pitch"]]*f))

    for name in ("slide", "roll"):
        if name not in rows:
            continue
        f, d = rows[name]
        if name == "slide":
            clips[name] = _pose(r, f, d, compact=compact,
                root_y=[9,12,13,12,10,8], torso=[15,19,21,18,14,10], head=[-9,-11,-12,-10,-7,-5],
                near_hand=([4,0,-4,-2,3,8],[-42,-39,-37,-38,-41,-45],[55,50,45,50,60,70]),
                far_hand=([-3,0,4,2,-2,-7],[-41,-38,-36,-37,-40,-44],[125,130,135,130,120,110]))
        else:
            # Both scientist sheets face west.  A forward roll therefore turns
            # counter-clockwise in screen space (negative bone rotation).  The
            # old positive sweep made the body read as a backward somersault,
            # and its planted default feet fought the rotating pelvis.  Keep
            # the centre of mass low, tuck all four IK targets around the body,
            # then open back into the authored stance.
            clips[name] = _pose(r, f, d, compact=compact,
                root_y=[5,9,13,16,15,11,7,3],
                pelvis=[0,-35,-82,-132,-184,-236,-286,-328],
                torso=[-4,-14,-27,-39,-43,-34,-19,-5],
                head=[3,9,16,22,24,18,10,3],
                near_hand=([11,5,-1,-5,-3,2,9,15],[-47,-39,-33,-30,-31,-36,-43,-49],[75,55,35,20,5,25,55,78]),
                far_hand=([-9,-4,1,4,3,-1,-7,-12],[-46,-38,-32,-29,-30,-35,-42,-48],[105,125,145,160,175,150,120,102]),
                near_foot=([9,5,1,-3,-2,2,7,10],[2,10,20,27,25,18,9,2],[r["near_foot_pitch"],r["near_foot_pitch"]-8,r["near_foot_pitch"]-18,r["near_foot_pitch"]-28,r["near_foot_pitch"]-22,r["near_foot_pitch"]-12,r["near_foot_pitch"]-4,r["near_foot_pitch"]]),
                far_foot=([-9,-5,-1,3,2,-2,-7,-10],[1,9,18,25,24,17,8,1],[r["far_foot_pitch"],r["far_foot_pitch"]+8,r["far_foot_pitch"]+18,r["far_foot_pitch"]+28,r["far_foot_pitch"]+22,r["far_foot_pitch"]+12,r["far_foot_pitch"]+4,r["far_foot_pitch"]]))

    for name in ("wall_grab", "ledge_grab"):
        if name in rows:
            f, d = rows[name]
            clips[name] = _pose(r, f, d, loop=True, compact=compact,
                root_y=[-3,-4,-5,-4,-3,-2], torso=[-8,-9,-10,-9,-8,-7], head=[5,6,7,6,5,4],
                near_hand=([-30,-31,-32,-31,-30,-29],[-78,-79,-80,-79,-78,-77],[180]*6),
                far_hand=([-24,-25,-26,-25,-24,-23],[-65,-66,-67,-66,-65,-64],[180]*6),
                near_foot=([4,3,2,3,4,5],[8,10,12,10,8,7],[r["near_foot_pitch"]]*6),
                far_foot=([-4,-3,-2,-3,-4,-5],[4,6,8,6,4,3],[r["far_foot_pitch"]]*6))
    for name in ("wall_jump", "ledge_climb", "ledge_getup", "ledge_roll"):
        if name in rows:
            f, d = rows[name]
            clips[name] = _pose(r, f, d, compact=compact,
                root_y=[4,-2,-11,-8,-3,0,1,0][:f], torso=[-8,-3,6,10,6,2,0,0][:f], head=[5,2,-4,-6,-3,-1,0,0][:f],
                near_hand=([-28,-22,-12,0,8,14,16,17][:f],[-76,-72,-65,-58,-53,-50,-49,-48][:f],[180,160,130,100,85,80,80,80][:f]),
                far_hand=([-22,-17,-8,2,8,12,13,13][:f],[-64,-62,-58,-54,-51,-49,-48,-47][:f],[180,155,130,110,100,100,100,100][:f]))
    for name in ("climb", "swim"):
        if name in rows:
            f, d = rows[name]
            clips[name] = _pose(r, f, d, loop=True, compact=compact,
                root_y=[0,-2,-3,-1,1,2,1,0], torso=[2,5,3,-1,-3,-5,-2,1], head=[-1,-2,-1,1,2,2,1,0],
                near_hand=([-4,-14,-22,-10,5,14,8,0],[-64,-74,-80,-70,-58,-50,-56,-62],[45,25,10,30,70,95,80,55]),
                far_hand=([5,14,20,10,-4,-14,-8,1],[-55,-49,-54,-66,-76,-80,-70,-60],[135,155,170,150,110,85,100,125]),
                near_foot=([8,4,0,5,10,14,12,9],[0,4,9,5,0,2,4,1],[r["near_foot_pitch"]]*8),
                far_foot=([-8,-4,0,-5,-10,-14,-12,-9],[4,1,0,3,8,5,1,3],[r["far_foot_pitch"]]*8))

    f, d = rows["block"]
    clips["block"] = _pose(r, f, d, loop=True, compact=compact,
        root_y=[1,0,-1,0,1,1], torso=[5,7,8,7,5,4], head=[-3,-4,-5,-4,-3,-2],
        near_hand=([-15,-17,-18,-17,-15,-14],[-70,-72,-73,-72,-70,-69],[165]*6),
        far_hand=([-7,-9,-10,-9,-7,-6],[-60,-62,-63,-62,-60,-59],[160]*6))
    f, d = rows["hit"]
    clips["hit"] = _pose(r, f, d, compact=compact,
        root_y=[0,3,-2,1,0], torso=[0,-12,8,-4,0], head=[0,10,-7,3,0],
        near_hand=([17,24,12,19,17],[-50,-43,-56,-48,-50],[80,105,60,85,80]),
        far_hand=([-13,-5,-20,-11,-13],[-49,-42,-55,-47,-49],[100,75,120,95,100]))
    f, d = rows["death"]
    clips["death"] = _pose(r, f, d, compact=compact,
        root_y=[0,-1,-3,-6,-10,-14,-18,-20,-20][:f], pelvis=[0,-8,-20,-38,-58,-76,-88,-94,-96][:f],
        torso=[0,-6,-15,-28,-45,-61,-72,-78,-80][:f], head=[0,4,9,15,22,27,30,32,33][:f],
        near_hand=([17,19,23,28,31,32,32,32,32][:f],[-50,-48,-42,-32,-20,-12,-8,-7,-7][:f],[80,75,60,35,10,-10,-20,-25,-25][:f]),
        far_hand=([-13,-11,-7,-2,2,4,4,4,4][:f],[-49,-47,-41,-31,-20,-13,-9,-8,-8][:f],[100,105,120,145,170,190,200,205,205][:f]))

    f, d = rows["talk"]
    clips["talk"] = _pose(r, f, d, loop=True, compact=compact,
        root_y=[0,-1,-1,0,1,1,0,0], torso=[0,2,4,2,0,-2,-1,0], head=[0,-2,-4,-2,1,3,2,0],
        near_hand=([17,10,2,-4,0,8,14,17],[-50,-55,-62,-67,-63,-57,-52,-50],[80,70,55,45,55,65,75,80]))
    f, d = rows["interact"]
    clips["interact"] = _pose(r, f, d, loop=True, compact=compact,
        torso=[0,2,4,3,1,-1,-1,0], head=[0,-1,-3,-2,0,1,1,0],
        near_hand=([17,8,-4,-14,-10,-2,8,17],[-50,-53,-57,-61,-60,-57,-53,-50],[80,70,60,50,55,65,75,80]))
    f, d = rows["celebrate"]
    clips["celebrate"] = _pose(r, f, d, loop=True, compact=compact,
        root_y=[0,-2,-4,-2,0,1,0,-1], torso=[0,-4,-7,-4,0,3,1,-1], head=[0,3,6,3,0,-2,-1,0],
        near_hand=([17,8,-5,-14,-8,2,11,17],[-50,-61,-75,-84,-78,-66,-56,-50],[80,55,30,15,30,50,70,80]),
        far_hand=([-13,-5,6,14,8,-1,-9,-13],[-49,-60,-74,-82,-76,-64,-55,-49],[100,125,150,165,150,130,110,100]))
    f, d = rows["taunt"]
    clips["taunt"] = _pose(r, f, d, loop=True, compact=compact,
        torso=[0,3,6,4,0,-2,-1,0], head=[0,-4,-7,-5,0,4,2,0],
        near_hand=([17,4,-8,-15,-10,0,11,17],[-50,-57,-65,-69,-66,-59,-53,-50],[80,65,50,40,50,65,75,80]),
        far_hand=([-13,-8,-2,3,1,-5,-10,-13],[-49,-47,-45,-44,-45,-47,-48,-49],[100,105,110,115,112,108,103,100]))
    return clips


def _patent_clips(spec: CharacterSpec, doc: Mapping[str, object]) -> dict[str, dict]:
    """Author Patent Clerk's current full-fighter motion surface.

    The canonical vocabulary is intentionally larger than the current art.
    Variants collapse onto representative rows in ``patent_clerk_motion.py``;
    every row declared here, however, is an intentional silhouette rather than
    an accidental neutral fallback.
    """

    clips = _common_clips(spec, doc, compact=True)
    r = _rest(
        doc,
        hands_follow_forearms=spec.hands_follow_forearms,
        natural_arm_pose=spec.natural_arm_pose,
    )
    rows = {name: (frames, duration) for name, frames, duration in spec.rows}

    def add_pose(name: str, *, loop: bool = False, **kwargs) -> None:
        f, d = rows[name]
        clips[name] = _pose(r, f, d, loop=loop, compact=True, **kwargs)

    def clone(name: str, source: str, *, loop: bool | None = None) -> None:
        f, d = rows[name]
        base = deepcopy(clips[source])
        base["frames"] = f
        base["duration_ms"] = d
        if loop is not None:
            base["loop"] = loop
        clips[name] = base

    # ---- Character-concept actions -------------------------------------
    # These remain the visual language used by the fighter-facing coverage map:
    # margin correction = f-tilt, light argument = neutral special, reference
    # frame = side special, accelerating elevator = up special, synchronized
    # clocks = down special, mass/energy conversion = forward smash, and the
    # annus mirabilis sequence = final smash.
    action_specs = {
        "known_result": dict(loop=False, torso=[0,3,6,8,5,2,0], head=[0,-2,-5,-7,-4,-1,0],
            near_hand=([17,5,-8,-23,-28,-16,17],[-50,-55,-62,-66,-65,-58,-50],[80,65,50,25,15,40,80])),
        "application_review": dict(loop=False, torso=[0,2,5,7,4,0], head=[0,1,3,4,2,0],
            near_hand=([17,8,-2,-12,-20,-8],[-50,-54,-59,-62,-61,-52],[80,70,60,45,30,70]),
            far_hand=([-13,-7,0,7,12,-8],[-49,-53,-58,-61,-59,-50],[100,110,120,135,145,105])),
        "margin_correction": dict(loop=False, torso=[0,5,9,12,7,2,0], head=[0,-3,-6,-8,-5,-2,0],
            near_hand=([17,4,-12,-32,-39,-20,17],[-50,-52,-54,-56,-55,-52,-50],[80,65,45,15,5,35,80])),
        "light_argument": dict(loop=False, root_y=[0,-1,-2,-3,-2,-1,0,0], torso=[0,4,8,12,10,5,1,0], head=[0,-3,-6,-9,-8,-4,-1,0],
            near_hand=([17,6,-10,-28,-42,-44,-30,17],[-50,-55,-61,-66,-68,-67,-60,-50],[80,65,45,20,0,-5,25,80]),
            far_hand=([-13,-8,-2,4,7,4,-2,-13],[-49,-47,-45,-44,-44,-45,-47,-49],[100,105,110,118,125,118,108,100])),
        "reference_frame": dict(loop=False, torso=[0,-2,-5,-7,-5,-2,0,0,0], head=[0,2,5,7,5,2,0,0,0],
            near_hand=([17,24,31,38,42,38,30,23,17],[-50,-57,-65,-72,-76,-72,-64,-56,-50],[80,72,60,45,30,45,60,72,80]),
            far_hand=([-13,-20,-27,-34,-39,-35,-27,-20,-13],[-49,-56,-64,-71,-75,-71,-63,-55,-49],[100,108,120,135,150,135,120,108,100])),
        "elevator_thought": dict(loop=False, root_y=[2,0,-4,-9,-14,-10,-5,-1,0], torso=[0,-3,-6,-8,-9,-6,-3,-1,0], head=[0,2,4,6,7,5,3,1,0],
            near_hand=([17,12,5,-2,-7,-4,2,10,17],[-50,-61,-72,-82,-91,-84,-72,-60,-50],[80,60,40,20,5,20,40,60,80]),
            far_hand=([-13,-8,-2,5,10,7,1,-7,-13],[-49,-60,-71,-81,-90,-83,-71,-59,-49],[100,120,140,160,175,160,140,120,100])),
        "synchronize_clocks": dict(loop=False, torso=[0,2,5,7,8,7,5,2,0,0], head=[0,-1,-3,-5,-6,-5,-3,-1,0,0],
            near_hand=([17,9,0,-10,-20,-29,-23,-10,4,17],[-50,-55,-60,-65,-68,-66,-61,-56,-52,-50],[80,70,60,50,35,20,35,50,65,80]),
            far_hand=([-13,-5,4,14,24,31,25,12,0,-13],[-49,-54,-59,-64,-67,-65,-60,-55,-51,-49],[100,110,120,130,145,160,145,130,115,100])),
        "mass_energy_conversion": dict(loop=False, root_y=[0,-1,-2,-3,-4,-3,-2,-1,0,0], torso=[0,3,6,9,12,10,7,3,1,0], head=[0,-2,-4,-6,-8,-7,-5,-2,-1,0],
            near_hand=([17,10,3,-5,-12,-8,0,9,15,17],[-50,-55,-60,-64,-67,-64,-59,-54,-51,-50],[80,70,60,50,40,50,60,70,78,80]),
            far_hand=([-13,-6,1,9,16,12,4,-5,-11,-13],[-49,-54,-59,-63,-66,-63,-58,-53,-50,-49],[100,110,120,130,140,130,120,110,102,100])),
        "annus_mirabilis": dict(loop=False, root_y=[0,-2,-5,-9,-13,-17,-15,-11,-7,-3,-1,0], torso=[0,4,9,14,19,23,20,15,10,5,2,0], head=[0,-3,-6,-9,-12,-15,-13,-9,-6,-3,-1,0],
            near_hand=([17,10,1,-10,-22,-34,-42,-38,-28,-15,2,17],[-50,-59,-69,-79,-88,-94,-96,-90,-79,-67,-56,-50],[80,65,50,35,20,8,0,10,25,45,65,80]),
            far_hand=([-13,-6,3,14,26,38,46,42,32,19,4,-13],[-49,-58,-68,-78,-87,-93,-95,-89,-78,-66,-55,-49],[100,115,130,145,160,172,180,170,155,135,115,100])),
    }
    for name, kwargs in action_specs.items():
        add_pose(name, **kwargs)

    # ---- Stance, locomotion, jumps, falls -------------------------------
    add_pose("idle_look_up", loop=True,
        root_y=[0,-1,-1,0,1,1,0,0], torso=[0,-1,-2,-2,-1,0,0,0],
        head=[0,4,8,11,10,7,3,0])
    add_pose("walk_stop",
        root_y=[1,2,3,2,1,0], torso=[-6,-3,2,4,2,0], head=[4,2,-1,-3,-1,0],
        near_foot=([18,15,12,10,10,10],[2,1,0,0,0,0],[r["near_foot_pitch"]]*6),
        far_foot=([-17,-14,-12,-10,-10,-10],[1,0,0,0,0,0],[r["far_foot_pitch"]]*6))
    add_pose("turnaround",
        root_y=[0,1,2,1,0,0], pelvis=[0,8,18,14,6,0], torso=[0,-9,-18,-14,-6,0],
        head=[0,8,16,13,6,0],
        near_hand=([17,10,2,-2,6,17],[-50,-48,-47,-48,-49,-50],[80]*6),
        far_hand=([-13,-5,2,5,-3,-13],[-49,-48,-47,-47,-48,-49],[100]*6))
    add_pose("stumble",
        root_y=[0,3,7,4,1,0], pelvis=[0,-5,-12,-7,-2,0], torso=[0,-10,-24,-15,-5,0],
        head=[0,8,18,12,4,0],
        near_hand=([17,24,31,26,21,17],[-50,-45,-39,-43,-47,-50],[80]*6),
        far_hand=([-13,-20,-27,-22,-17,-13],[-49,-44,-38,-42,-46,-49],[100]*6))
    add_pose("crouch_start",
        root_y=[0,3,7,10,11], torso=[0,3,7,9,9], head=[0,-2,-4,-5,-5],
        near_hand=([17,14,11,9,9],[-50,-47,-44,-42,-42],[80]*5),
        far_hand=([-13,-11,-9,-8,-8],[-49,-46,-44,-43,-43],[100]*5))
    add_pose("crouch_end",
        root_y=[11,9,6,3,0], torso=[9,8,5,2,0], head=[-5,-4,-3,-1,0],
        near_hand=([9,10,12,15,17],[-42,-44,-46,-48,-50],[80]*5),
        far_hand=([-8,-9,-10,-12,-13],[-43,-44,-46,-48,-49],[100]*5))
    add_pose("land_light",
        root_y=[-2,2,5,3,0], torso=[-2,4,7,4,0], head=[2,-3,-5,-3,0],
        near_hand=([14,11,8,12,17],[-52,-47,-44,-47,-50],[80]*5),
        far_hand=([-11,-8,-5,-8,-13],[-51,-46,-43,-46,-49],[100]*5))
    add_pose("jump_squat",
        root_y=[0,4,9,12,7], torso=[0,4,9,12,5], head=[0,-2,-5,-7,-3],
        near_hand=([17,13,9,6,10],[-50,-47,-44,-42,-46],[80]*5),
        far_hand=([-13,-10,-7,-5,-8],[-49,-46,-43,-41,-45],[100]*5))
    add_pose("double_jump",
        root_y=[-5,-11,-20,-28,-24,-15,-7], pelvis=[0,-12,-25,-38,-24,-10,0],
        torso=[0,5,10,14,9,4,0], head=[0,-3,-6,-8,-5,-2,0],
        near_hand=([17,8,-4,-15,-8,4,17],[-50,-61,-74,-84,-76,-62,-50],[80]*7),
        far_hand=([-13,-4,7,16,9,-2,-13],[-49,-60,-73,-83,-75,-61,-49],[100]*7),
        near_foot=([10,6,1,-4,0,6,10],[1,7,15,21,15,7,1],[r["near_foot_pitch"]]*7),
        far_foot=([-10,-6,-1,4,0,-6,-10],[1,7,15,21,15,7,1],[r["far_foot_pitch"]]*7))
    add_pose("fall_special", loop=True,
        root_y=[-7,-8,-9,-8,-7,-6,-7], pelvis=[0,2,4,2,0,-2,0],
        torso=[5,7,8,7,5,4,5], head=[-3,-4,-5,-4,-3,-2,-3],
        near_hand=([6,5,4,5,6,7,6],[-38,-37,-36,-37,-38,-39,-38],[80]*7),
        far_hand=([-4,-3,-2,-3,-4,-5,-4],[-37,-36,-35,-36,-37,-38,-37],[100]*7))
    add_pose("tumble", loop=True,
        root_y=[-10,-12,-14,-13,-11,-9,-8,-9],
        pelvis=[0,45,90,135,180,225,270,315], torso=[0,-8,-13,-8,0,8,13,8], head=[0,6,10,6,0,-6,-10,-6],
        near_hand=([7,2,-3,-7,-5,0,5,8],[-49,-44,-40,-42,-48,-54,-56,-52],[80]*8),
        far_hand=([-5,0,5,8,6,1,-4,-6],[-48,-43,-39,-41,-47,-53,-55,-51],[100]*8))
    add_pose("roll_back",
        root_y=[5,9,13,16,15,11,7,3],
        pelvis=[0,35,82,132,184,236,286,328], torso=[4,14,27,39,43,34,19,5], head=[-3,-9,-16,-22,-24,-18,-10,-3],
        near_hand=([11,5,-1,-5,-3,2,9,15],[-47,-39,-33,-30,-31,-36,-43,-49],[80]*8),
        far_hand=([-9,-4,1,4,3,-1,-7,-12],[-46,-38,-32,-29,-30,-35,-42,-48],[100]*8),
        near_foot=([9,5,1,-3,-2,2,7,10],[2,10,20,27,25,18,9,2],[r["near_foot_pitch"]]*8),
        far_foot=([-9,-5,-1,3,2,-2,-7,-10],[1,9,18,25,24,17,8,1],[r["far_foot_pitch"]]*8))
    add_pose("spot_dodge",
        root_y=[0,-1,-3,-5,-3,-1,0], torso=[0,7,15,22,15,7,0], head=[0,-5,-10,-14,-10,-5,0],
        near_hand=([17,14,9,4,9,14,17],[-50,-47,-43,-40,-43,-47,-50],[80]*7),
        far_hand=([-13,-10,-5,0,-5,-10,-13],[-49,-46,-42,-39,-42,-46,-49],[100]*7))
    add_pose("air_dodge",
        root_y=[-9,-11,-13,-12,-10,-8,-9], pelvis=[0,-9,-20,-28,-20,-9,0],
        torso=[0,5,11,15,11,5,0], head=[0,-4,-8,-10,-8,-4,0],
        near_hand=([8,3,-2,-5,-2,3,8],[-48,-42,-38,-36,-38,-42,-48],[80]*7),
        far_hand=([-6,-1,4,7,4,-1,-6],[-47,-41,-37,-35,-37,-41,-47],[100]*7),
        near_foot=([5,2,-2,-4,-2,2,5],[5,12,17,19,17,12,5],[r["near_foot_pitch"]]*7),
        far_foot=([-5,-2,2,4,2,-2,-5],[5,12,17,19,17,12,5],[r["far_foot_pitch"]]*7))
    add_pose("platform_drop",
        root_y=[6,10,15,21,27], torso=[8,10,8,4,1], head=[-5,-6,-4,-2,0],
        near_hand=([10,8,7,8,10],[-43,-41,-40,-42,-45],[80]*5),
        far_hand=([-8,-6,-5,-6,-8],[-42,-40,-39,-41,-44],[100]*5))
    clone("footstool_jump", "double_jump", loop=False)
    add_pose("teeter_start",
        root_y=[0,0,1,2,1], torso=[0,-7,-15,-20,-18], head=[0,5,10,14,12],
        near_hand=([17,23,28,31,29],[-50,-45,-41,-39,-40],[80]*5),
        far_hand=([-13,-19,-24,-27,-25],[-49,-44,-40,-38,-39],[100]*5))
    add_pose("teeter", loop=True,
        root_y=[1,2,1,0,1,2,1,0], torso=[-18,-20,-22,-20,-18,-16,-17,-18], head=[12,14,16,14,12,10,11,12],
        near_hand=([29,31,33,31,29,27,28,29],[-40,-39,-38,-39,-40,-41,-41,-40],[80]*8),
        far_hand=([-25,-27,-29,-27,-25,-23,-24,-25],[-39,-38,-37,-38,-39,-40,-40,-39],[100]*8))

    # ---- Shield / parry -------------------------------------------------
    add_pose("shield_raise",
        torso=[0,2,4,6,6], head=[0,-1,-2,-3,-3],
        near_hand=([17,9,1,-9,-15],[-50,-56,-63,-68,-70],[80]*5),
        far_hand=([-13,-10,-8,-7,-7],[-49,-53,-57,-59,-60],[100]*5))
    add_pose("shield_release",
        torso=[6,5,3,1,0], head=[-3,-3,-2,-1,0],
        near_hand=([-15,-9,-1,9,17],[-70,-68,-63,-56,-50],[80]*5),
        far_hand=([-7,-7,-8,-10,-13],[-60,-59,-57,-53,-49],[100]*5))
    add_pose("shield_hit",
        root_y=[0,2,-1,1,0], torso=[6,12,2,8,6], head=[-3,-8,1,-5,-3],
        near_hand=([-15,-20,-11,-17,-15],[-70,-66,-73,-69,-70],[80]*5),
        far_hand=([-7,-11,-4,-9,-7],[-60,-57,-63,-59,-60],[100]*5))

    # ---- Normals / smashes / aerials -----------------------------------
    add_pose("jab",
        torso=[0,3,7,11,5,0], head=[0,-2,-4,-6,-3,0],
        near_hand=([17,5,-14,-32,-7,17],[-50,-51,-52,-52,-51,-50],[80]*6),
        far_hand=([-13,-10,-7,-5,-9,-13],[-49,-47,-46,-46,-47,-49],[100]*6))
    add_pose("dash_attack",
        root_y=[0,-1,-3,-4,-2,0,0], torso=[10,16,22,27,20,12,6], head=[-6,-9,-13,-16,-12,-7,-3],
        near_hand=([8,-4,-19,-36,-40,-15,10],[-48,-49,-50,-51,-50,-49,-48],[80]*7),
        far_hand=([-4,1,8,13,10,2,-5],[-47,-44,-42,-41,-42,-45,-47],[100]*7))
    add_pose("attack_up",
        torso=[0,-2,-6,-10,-12,-8,-3,0], head=[0,2,5,8,10,7,3,0],
        near_hand=([17,10,2,-7,-15,-9,4,17],[-50,-62,-75,-87,-97,-90,-69,-50],[80]*8))
    add_pose("attack_down",
        root_y=[0,2,5,7,6,3,1,0], torso=[0,4,9,14,16,11,5,0], head=[0,-2,-5,-8,-10,-7,-3,0],
        near_hand=([17,7,-5,-18,-30,-24,-7,17],[-50,-47,-43,-39,-35,-38,-44,-50],[80]*8))
    add_pose("smash_charge", loop=True,
        root_y=[4,5,6,5,4,3,4,5], torso=[10,12,14,13,11,9,10,12], head=[-6,-7,-8,-8,-7,-5,-6,-7],
        near_hand=([10,13,16,15,11,8,9,11],[-45,-42,-40,-41,-44,-47,-46,-44],[80]*8),
        far_hand=([-8,-11,-14,-13,-9,-6,-7,-9],[-44,-41,-39,-40,-43,-46,-45,-43],[100]*8))
    add_pose("smash_up",
        root_y=[2,1,-2,-5,-7,-4,-1,0,0], torso=[4,0,-5,-11,-16,-12,-5,0,0], head=[-2,1,5,9,13,10,4,1,0],
        near_hand=([12,7,1,-6,-13,-8,1,10,17],[-49,-61,-75,-90,-101,-93,-76,-60,-50],[80]*9),
        far_hand=([-9,-4,2,8,14,9,1,-7,-13],[-48,-60,-74,-89,-100,-92,-75,-59,-49],[100]*9))
    add_pose("smash_down",
        root_y=[0,3,7,10,12,10,6,2,0], torso=[0,5,10,16,20,16,9,3,0], head=[0,-3,-6,-10,-13,-10,-6,-2,0],
        near_hand=([17,8,-3,-16,-30,-36,-24,-5,17],[-50,-47,-43,-39,-35,-33,-37,-44,-50],[80]*9),
        far_hand=([-13,-5,4,14,24,31,22,5,-13],[-49,-46,-42,-38,-34,-32,-36,-43,-49],[100]*9))
    air_specs = {
        "air_neutral": dict(pelvis=[0,-18,-38,-56,-38,-18,0,0],
            near_hand=([8,-1,-9,-14,-9,-1,8,12],[-61,-69,-75,-77,-74,-67,-60,-58],[80]*8),
            far_hand=([-6,3,11,16,11,3,-6,-10],[-60,-68,-74,-76,-73,-66,-59,-57],[100]*8)),
        "air_forward": dict(torso=[0,4,9,14,10,4,0], head=[0,-2,-5,-8,-6,-2,0],
            near_hand=([17,5,-12,-31,-42,-17,17],[-50,-55,-60,-63,-62,-56,-50],[80]*7)),
        "air_back": dict(torso=[0,-3,-7,-11,-8,-3,0], head=[0,2,5,7,5,2,0],
            far_hand=([-13,-2,12,27,35,9,-13],[-49,-54,-59,-61,-60,-55,-49],[100]*7)),
        "air_up": dict(torso=[0,-2,-6,-10,-8,-3,0], head=[0,2,5,8,6,2,0],
            near_hand=([17,8,-3,-14,-19,-7,17],[-50,-64,-80,-95,-102,-83,-50],[80]*7)),
        "air_down": dict(torso=[0,3,7,11,8,3,0], head=[0,-2,-5,-8,-6,-2,0],
            near_hand=([17,8,-3,-14,-20,-7,17],[-50,-45,-39,-32,-27,-37,-50],[80]*7)),
    }
    for name, kwargs in air_specs.items():
        add_pose(name, root_y=[-9,-11,-13,-12,-10,-8,-9,-9], **kwargs)
    add_pose("air_land",
        root_y=[-2,3,6,4,1,0], torso=[-3,5,9,6,2,0], head=[2,-3,-6,-4,-1,0])

    # ---- Grabs / throws / grabbed reactions ----------------------------
    add_pose("grab",
        torso=[0,4,9,13,9,3,0], head=[0,-2,-4,-6,-4,-1,0],
        near_hand=([17,8,-6,-22,-31,-12,17],[-50,-54,-57,-58,-57,-53,-50],[80]*7),
        far_hand=([-13,-5,5,16,22,6,-13],[-49,-53,-56,-57,-56,-52,-49],[100]*7))
    add_pose("grab_hold", loop=True,
        torso=[7,8,9,8,7,6,7,8], head=[-3,-4,-5,-4,-3,-2,-3,-4],
        near_hand=([-18,-19,-20,-19,-18,-17,-18,-19],[-57,-58,-59,-58,-57,-56,-57,-58],[80]*8),
        far_hand=([12,13,14,13,12,11,12,13],[-56,-57,-58,-57,-56,-55,-56,-57],[100]*8))
    add_pose("pummel",
        torso=[7,10,14,9,7], head=[-3,-5,-7,-4,-3],
        near_hand=([-18,-10,-27,-12,-18],[-57,-55,-58,-56,-57],[80]*5))
    add_pose("grab_release",
        torso=[7,5,3,1,0], head=[-3,-2,-1,0,0],
        near_hand=([-18,-9,0,9,17],[-57,-55,-53,-51,-50],[80]*5),
        far_hand=([12,5,-2,-8,-13],[-56,-54,-52,-50,-49],[100]*5))
    throw_specs = {
        "throw_forward": dict(torso=[0,4,10,17,20,12,5,0], head=[0,-2,-5,-9,-11,-7,-3,0],
            near_hand=([-18,-25,-33,-42,-48,-31,-7,17],[-57,-58,-59,-58,-56,-54,-52,-50],[80]*8)),
        "throw_back": dict(pelvis=[0,8,18,28,22,12,4,0], torso=[0,-5,-11,-17,-14,-8,-3,0], head=[0,3,7,10,8,4,2,0],
            far_hand=([12,20,29,38,44,28,5,-13],[-56,-57,-58,-57,-55,-53,-51,-49],[100]*8)),
        "throw_up": dict(root_y=[0,-1,-3,-5,-4,-2,0,0], torso=[0,-3,-8,-13,-15,-9,-3,0], head=[0,2,5,8,10,6,2,0],
            near_hand=([-18,-12,-5,2,7,1,-7,17],[-57,-68,-80,-92,-99,-88,-70,-50],[80]*8)),
        "throw_down": dict(root_y=[0,2,5,8,9,6,2,0], torso=[0,4,9,15,18,12,5,0], head=[0,-2,-5,-9,-11,-7,-3,0],
            near_hand=([-18,-21,-24,-27,-30,-20,-4,17],[-57,-50,-43,-36,-31,-36,-43,-50],[80]*8)),
    }
    for name, kwargs in throw_specs.items():
        add_pose(name, **kwargs)
    add_pose("grabbed", loop=True,
        root_y=[0,1,0,-1,0,1,0,0], torso=[-5,-6,-7,-6,-5,-4,-5,-6], head=[5,6,7,6,5,4,5,6],
        near_hand=([5,4,3,4,5,6,5,4],[-45,-44,-43,-44,-45,-46,-45,-44],[80]*8),
        far_hand=([-3,-2,-1,-2,-3,-4,-3,-2],[-44,-43,-42,-43,-44,-45,-44,-43],[100]*8))
    add_pose("grabbed_pummel",
        root_y=[0,2,-1,1,0], torso=[-5,-13,4,-8,-5], head=[5,12,-3,9,5])
    add_pose("grab_escape",
        root_y=[0,-1,-2,-1,0,0,0], torso=[-5,-9,-13,-8,-3,0,0], head=[5,8,11,7,3,0,0],
        near_hand=([5,-3,-11,-4,5,12,17],[-45,-52,-60,-54,-49,-47,-50],[80]*7),
        far_hand=([-3,5,13,6,-3,-10,-13],[-44,-51,-59,-53,-48,-46,-49],[100]*7))

    # ---- Damage, knockdown, get-up, tech -------------------------------
    add_pose("launch",
        root_y=[0,-6,-14,-24,-33,-41,-47], pelvis=[0,-12,-28,-48,-68,-86,-102],
        torso=[0,-5,-10,-15,-20,-24,-27], head=[0,4,8,12,16,19,21],
        near_hand=([17,21,26,31,35,38,40],[-50,-45,-39,-32,-24,-17,-12],[80]*7),
        far_hand=([-13,-17,-22,-27,-31,-34,-36],[-49,-44,-38,-31,-23,-16,-11],[100]*7))
    add_pose("meteor",
        root_y=[-8,-3,5,15,27,38,48], pelvis=[0,10,25,43,62,80,95],
        torso=[0,5,10,15,20,24,27], head=[0,-4,-8,-12,-16,-19,-21])
    add_pose("impact",
        root_y=[0,3,-2,1,0], torso=[0,-20,12,-7,0], head=[0,15,-9,5,0],
        near_hand=([17,25,10,20,17],[-50,-42,-57,-47,-50],[80]*5),
        far_hand=([-13,-5,-22,-10,-13],[-49,-41,-56,-46,-49],[100]*5))
    add_pose("splat", loop=True,
        root_y=[1,2,3,2,1,0,1,2], torso=[-24,-26,-28,-26,-24,-22,-23,-25], head=[16,18,20,18,16,14,15,17],
        near_hand=([24,25,26,25,24,23,24,25],[-44,-43,-42,-43,-44,-45,-44,-43],[80]*8),
        far_hand=([-20,-21,-22,-21,-20,-19,-20,-21],[-43,-42,-41,-42,-43,-44,-43,-42],[100]*8))
    add_pose("ground_bounce",
        root_y=[-10,-4,7,15,9,3,0], pelvis=[70,82,94,92,88,86,86], torso=[0,6,12,10,6,3,0], head=[0,-5,-10,-8,-5,-2,0])
    add_pose("knockdown",
        root_y=[0,4,9,14,18,20], pelvis=[0,18,40,62,78,86], torso=[0,-5,-10,-12,-9,-4], head=[0,4,8,10,7,3])
    add_pose("prone", loop=True,
        root_y=[20,21,20,19,20,21,20,19], pelvis=[86,86,87,86,86,85,86,86], torso=[-4,-5,-4,-3,-4,-5,-4,-3], head=[3,4,3,2,3,4,3,2])
    add_pose("prone_damage",
        root_y=[20,23,18,22,20], pelvis=[86,92,80,90,86], torso=[-4,-12,6,-10,-4], head=[3,10,-5,8,3])
    add_pose("getup",
        root_y=[20,18,14,10,6,3,1,0], pelvis=[86,75,60,45,30,18,8,0], torso=[-4,-2,2,5,6,4,2,0], head=[3,2,0,-2,-3,-2,-1,0])
    add_pose("getup_attack",
        root_y=[20,18,14,10,7,4,2,0], pelvis=[86,74,58,42,28,16,7,0], torso=[-4,0,6,12,15,10,4,0], head=[3,1,-2,-5,-7,-5,-2,0],
        near_hand=([8,-2,-14,-28,-39,-24,-3,17],[-42,-45,-48,-50,-49,-47,-48,-50],[80]*8))
    clone("getup_roll", "roll", loop=False)
    add_pose("tech",
        root_y=[8,5,2,0,0,0], pelvis=[18,12,6,2,0,0], torso=[7,5,3,1,0,0], head=[-4,-3,-2,-1,0,0])
    clone("tech_roll", "roll", loop=False)
    add_pose("wall_tech",
        root_y=[-4,-2,0,1,0,0], torso=[-20,-14,-8,-3,0,0], head=[14,10,6,2,0,0],
        near_hand=([-30,-24,-16,-7,3,17],[-76,-70,-63,-57,-53,-50],[80]*6))
    add_pose("wall_tech_jump",
        root_y=[0,-5,-13,-22,-27,-18,-8], torso=[-16,-10,-2,7,12,7,1], head=[11,7,2,-5,-8,-5,-1],
        near_hand=([-28,-20,-10,0,8,13,17],[-74,-70,-64,-59,-55,-52,-50],[80]*7))
    add_pose("ceiling_tech",
        root_y=[-22,-18,-12,-7,-3,0], pelvis=[180,155,115,70,30,0], torso=[0,-4,-6,-4,-2,0], head=[0,3,5,3,1,0])
    clone("shield_break_launch", "launch", loop=False)
    add_pose("shield_break_fall", loop=True,
        root_y=[-12,-11,-10,-9,-10,-11,-12], pelvis=[20,35,50,65,80,95,110], torso=[3,5,7,5,3,1,3], head=[-2,-4,-6,-4,-2,0,-2])
    add_pose("shield_break_collapse",
        root_y=[0,5,11,17,20,20,20,20], pelvis=[0,14,32,55,75,86,88,88], torso=[0,-4,-8,-12,-10,-6,-4,-4], head=[0,3,6,9,7,4,3,3])
    clone("shield_break_recover", "getup", loop=False)
    add_pose("dizzy", loop=True,
        root_y=[0,1,2,1,0,-1,0,1,2,1], torso=[0,3,5,3,0,-3,-5,-3,0,3], head=[-8,-14,-17,-13,-6,3,10,13,7,-2],
        near_hand=([10,11,12,11,10,9,8,9,10,11],[-45,-44,-43,-44,-45,-46,-47,-46,-45,-44],[80]*10),
        far_hand=([-8,-9,-10,-9,-8,-7,-6,-7,-8,-9],[-44,-43,-42,-43,-44,-45,-46,-45,-44,-43],[100]*10))
    add_pose("sleep_start",
        root_y=[0,4,9,14,18,20,20], pelvis=[0,14,30,48,65,78,86], torso=[0,-3,-6,-9,-8,-5,-4], head=[0,3,6,8,7,4,3])
    clone("sleep", "prone", loop=True)
    clone("wake", "getup", loop=False)
    add_pose("bury_start",
        root_y=[0,5,11,18,25,31,35], torso=[0,2,5,7,8,6,4], head=[0,-1,-3,-5,-6,-4,-2],
        near_hand=([17,12,6,1,-3,0,5],[-50,-55,-60,-65,-69,-65,-60],[80]*7),
        far_hand=([-13,-8,-2,3,7,4,-1],[-49,-54,-59,-64,-68,-64,-59],[100]*7))
    add_pose("buried", loop=True,
        root_y=[35,36,35,34,35,36,35,34], torso=[4,5,6,5,4,3,4,5], head=[-2,-3,-4,-3,-2,-1,-2,-3])
    add_pose("bury_escape",
        root_y=[35,31,26,20,13,7,2,0], torso=[4,6,9,12,9,5,2,0], head=[-2,-4,-6,-8,-6,-3,-1,0],
        near_hand=([5,-1,-8,-14,-9,0,10,17],[-60,-66,-72,-77,-72,-64,-56,-50],[80]*8),
        far_hand=([-1,5,12,18,13,4,-6,-13],[-59,-65,-71,-76,-71,-63,-55,-49],[100]*8))

    # ---- Ledge ----------------------------------------------------------
    add_pose("ledge_catch",
        root_y=[2,-1,-4,-5,-4], torso=[0,-5,-9,-10,-9], head=[0,3,6,7,6],
        near_hand=([-10,-20,-28,-31,-30],[-63,-70,-77,-80,-78],[80]*5),
        far_hand=([-5,-13,-20,-24,-23],[-57,-61,-65,-67,-65],[100]*5))
    add_pose("ledge_getup",
        root_y=[-5,-3,0,3,5,3,1], torso=[-9,-5,0,6,9,5,1], head=[6,3,0,-4,-6,-3,-1],
        near_hand=([-30,-24,-16,-7,2,10,17],[-78,-73,-67,-61,-56,-53,-50],[80]*7),
        far_hand=([-23,-18,-12,-5,2,-6,-13],[-65,-62,-59,-55,-52,-50,-49],[100]*7))
    add_pose("ledge_attack",
        root_y=[-4,-2,1,4,5,3,1,0], torso=[-8,-3,4,11,15,10,4,0], head=[5,2,-2,-6,-8,-5,-2,0],
        near_hand=([-29,-20,-8,-22,-40,-25,-4,17],[-76,-69,-61,-55,-53,-54,-48,-50],[80]*8))
    clone("ledge_roll", "roll", loop=False)
    add_pose("ledge_jump",
        root_y=[-4,-9,-17,-26,-31,-23,-12], torso=[-8,-3,4,10,13,8,2], head=[5,2,-3,-7,-9,-5,-1],
        near_hand=([-29,-22,-14,-6,1,8,14],[-76,-71,-66,-61,-57,-54,-51],[80]*7),
        far_hand=([-23,-17,-10,-3,4,-3,-10],[-64,-61,-58,-55,-52,-50,-49],[100]*7))
    add_pose("ledge_drop",
        root_y=[-4,0,5,11,18], torso=[-9,-7,-4,-2,0], head=[6,5,3,1,0],
        near_hand=([-30,-24,-16,-3,10],[-78,-72,-65,-57,-50],[80]*5),
        far_hand=([-23,-19,-13,-8,-13],[-65,-62,-58,-54,-49],[100]*5))

    # ---- Generic dynamic-item body poses --------------------------------
    # No prop is baked into these frames: held items are separate runtime art.
    add_pose("item_hold", loop=True,
        torso=[0,1,2,1,0,-1,0,1], head=[0,-1,-2,-1,0,1,0,-1],
        near_hand=([-6,-7,-8,-7,-6,-5,-6,-7],[-55,-56,-57,-56,-55,-54,-55,-56],[80]*8),
        far_hand=([-2,-3,-4,-3,-2,-1,-2,-3],[-54,-55,-56,-55,-54,-53,-54,-55],[100]*8))
    add_pose("item_hold_crouch", loop=True,
        root_y=[11,12,13,12,11,10,11,12], torso=[8,9,10,9,8,7,8,9], head=[-5,-6,-7,-6,-5,-4,-5,-6],
        near_hand=([-5,-6,-7,-6,-5,-4,-5,-6],[-47,-48,-49,-48,-47,-46,-47,-48],[80]*8),
        far_hand=([-1,-2,-3,-2,-1,0,-1,-2],[-46,-47,-48,-47,-46,-45,-46,-47],[100]*8))
    add_pose("item_pickup",
        root_y=[0,4,9,12,8,3,0], torso=[0,6,13,17,11,4,0], head=[0,-3,-7,-9,-6,-2,0],
        near_hand=([17,10,2,-5,-1,8,17],[-50,-43,-36,-31,-36,-44,-50],[80]*7))
    add_pose("item_heavy_pickup",
        root_y=[0,5,11,15,12,7,2,0], torso=[0,8,16,21,17,10,4,0], head=[0,-4,-8,-11,-9,-5,-2,0],
        near_hand=([17,10,2,-5,-9,-3,7,17],[-50,-44,-38,-34,-32,-36,-43,-50],[80]*8),
        far_hand=([-13,-6,2,9,13,7,-3,-13],[-49,-43,-37,-33,-31,-35,-42,-49],[100]*8))
    add_pose("item_heavy_carry", loop=True,
        root_y=[2,3,4,3,2,1,2,3], torso=[8,10,11,10,8,7,8,9], head=[-5,-6,-7,-6,-5,-4,-5,-6],
        near_hand=([-8,-9,-10,-9,-8,-7,-8,-9],[-57,-58,-59,-58,-57,-56,-57,-58],[80]*8),
        far_hand=([3,4,5,4,3,2,3,4],[-56,-57,-58,-57,-56,-55,-56,-57],[100]*8))
    add_pose("item_throw",
        torso=[0,4,10,16,19,12,5], head=[0,-2,-5,-8,-10,-6,-2],
        near_hand=([-6,-15,-27,-40,-49,-26,7],[-55,-56,-57,-56,-53,-51,-50],[80]*7),
        far_hand=([-2,2,7,11,12,5,-5],[-54,-52,-50,-49,-49,-51,-53],[100]*7))
    add_pose("item_drop",
        torso=[0,3,6,3,0], head=[0,-2,-4,-2,0],
        near_hand=([-6,-4,-1,4,17],[-55,-50,-44,-39,-50],[80]*5))
    add_pose("item_swing",
        torso=[0,4,9,14,10,4,0], head=[0,-2,-5,-8,-6,-2,0],
        near_hand=([-6,-14,-26,-39,-43,-23,-6],[-55,-58,-59,-57,-52,-50,-55],[80]*7))

    # ---- Entrance / results --------------------------------------------
    add_pose("entrance",
        root_y=[24,18,12,7,3,1,0,0,0,0], torso=[8,6,4,2,1,0,0,0,0,0], head=[-5,-4,-3,-2,-1,0,0,0,0,0],
        near_hand=([7,8,10,12,14,16,17,17,17,17],[-42,-44,-46,-48,-49,-50,-50,-50,-50,-50],[80]*10),
        far_hand=([-5,-6,-8,-10,-11,-12,-13,-13,-13,-13],[-41,-43,-45,-47,-48,-49,-49,-49,-49,-49],[100]*10))
    add_pose("victory_hold", loop=True,
        root_y=[0,-1,-1,0,1,1,0,0], torso=[-4,-5,-6,-5,-4,-3,-4,-5], head=[6,7,8,7,6,5,6,7],
        near_hand=([-12,-13,-14,-13,-12,-11,-12,-13],[-78,-79,-80,-79,-78,-77,-78,-79],[80]*8),
        far_hand=([8,9,10,9,8,7,8,9],[-70,-71,-72,-71,-70,-69,-70,-71],[100]*8))
    add_pose("loss", loop=True,
        root_y=[2,3,4,3,2,1,2,3], torso=[12,14,16,14,12,10,11,13], head=[-9,-10,-11,-10,-9,-8,-9,-10],
        near_hand=([9,8,7,8,9,10,9,8],[-40,-39,-38,-39,-40,-41,-40,-39],[80]*8),
        far_hand=([-7,-6,-5,-6,-7,-8,-7,-6],[-39,-38,-37,-38,-39,-40,-39,-38],[100]*8))

    # Rows that are intentional present-day aliases rather than separate art.
    # This keeps the sheet compact while the coverage map can still distinguish
    # categories such as trip vs knockdown or heavy vs light item grip.
    intentional_aliases = {
        # No unique row needed: coverage maps these categories directly to the
        # named source row in patent_clerk_motion.py.
    }
    del intentional_aliases

    missing = set(rows) - set(clips)
    extra = set(clips) - set(rows)
    if missing or extra:
        raise ValueError(
            f"Patent Clerk motion authoring mismatch: missing={sorted(missing)}, "
            f"extra={sorted(extra)}"
        )
    return clips

def _retarget_clip_arms_to_torso(
    doc: Mapping[str, object],
    clips: Mapping[str, dict],
    name: str,
    *,
    reach_scale: float = 0.78,
) -> dict:
    """Keep both wrists in a stable torso-local relationship through a clip.

    Whole-body rotations such as rolls move the shoulders through large arcs.
    World-space wrist keys can cross a shoulder between adjacent samples even
    when the authored numbers look smooth, which forces analytic IK through a
    near-180-degree lower-arm swing.  Reconstruct the wrist trajectory from the
    solved shoulder and the natural idle shoulder-to-wrist vector instead.
    """

    if name not in clips or "idle" not in clips:
        return deepcopy(clips[name])
    # Some unit-level builder tests exercise clip authoring with only IK rest
    # metadata and intentionally omit the physical skeleton/frame.  The
    # torso-lock is a geometry refinement, so leave the authored clip intact
    # when there is no geometry to solve.
    if "frame" not in doc or "bones" not in doc:
        return deepcopy(clips[name])
    data = deepcopy(dict(doc))
    data["clips"] = {
        "idle": deepcopy(clips["idle"]),
        name: deepcopy(clips[name]),
    }
    rig = RigDocument(data)
    reference_world, _ = rig.solve("idle", 0.0)
    reference_torso = reference_world.get("torso")
    reference_angle = float(reference_torso.angle if reference_torso is not None else 0.0)
    reference_vectors: dict[str, tuple[float, float]] = {}
    for side in ("near", "far"):
        shoulder = reference_world[f"{side}_arm_u"].origin
        wrist = reference_world[f"{side}_arm_hand"].origin
        reference_vectors[side] = (
            (wrist[0] - shoulder[0]) * reach_scale,
            (wrist[1] - shoulder[1]) * reach_scale,
        )

    clip = deepcopy(clips[name])
    frames = max(1, int(clip.get("frames", 1)))
    loop = bool(clip.get("loop", False))
    cx = float(rig.frame.get("center_x", rig.frame["width"] / 2.0))
    gy = float(rig.frame.get("ground_y", rig.frame["height"] - 2.0))
    targets: dict[str, tuple[list[float], list[float]]] = {
        "near": ([], []),
        "far": ([], []),
    }
    for frame_idx in range(frames):
        t = rig.frame_time(name, frame_idx, frames)
        world, _ = rig.solve(name, t)
        torso = world.get("torso")
        angle = math.radians(
            float(torso.angle if torso is not None else reference_angle) - reference_angle
        )
        c = math.cos(angle)
        s = math.sin(angle)
        for side in ("near", "far"):
            vx, vy = reference_vectors[side]
            rotated = (c * vx - s * vy, s * vx + c * vy)
            shoulder = world[f"{side}_arm_u"].origin
            xs, ys = targets[side]
            xs.append(shoulder[0] + rotated[0] - cx)
            ys.append(shoulder[1] + rotated[1] - gy)

    channels = clip.setdefault("channels", {})
    for side in ("near", "far"):
        xs, ys = targets[side]
        channels[f"{side}_hand_x"] = keys(xs, loop=loop)
        channels[f"{side}_hand_y"] = keys(ys, loop=loop)
        channels.pop(f"{side}_hand_pitch", None)
    return clip


def _freeze_clip_pose(
    doc: Mapping[str, object],
    clips: Mapping[str, dict],
    *,
    name: str,
    source: str,
    frames: int,
    duration_ms: int,
) -> dict:
    """Publish a stable looping hold from the final sampled source pose."""

    source_clip = clips[source]
    source_channels = source_clip.get("channels", {})
    if "frame" not in doc or "bones" not in doc:
        channels = {
            channel: const(
                sample_channel_spec(
                    channel_spec,
                    1.0,
                    bool(source_clip.get("loop", False)),
                )
            )
            for channel, channel_spec in source_channels.items()
        }
        return _clip(frames, duration_ms, loop=True, channels=channels)

    data = deepcopy(dict(doc))
    data["clips"] = {source: deepcopy(source_clip)}
    rig = RigDocument(data)
    source_frames = max(1, int(source_clip.get("frames", 1)))
    t = rig.frame_time(source, source_frames - 1, source_frames)
    _world, params = rig.solve(source, t)
    channels = {
        channel: const(params[channel])
        for channel in source_channels
        if channel in params
    }
    return _clip(frames, duration_ms, loop=True, channels=channels)


def _stargan_clips(spec: CharacterSpec, doc: Mapping[str, object]) -> dict[str, dict]:
    clips = _common_clips(spec, doc, compact=False)
    r = _rest(
        doc,
        hands_follow_forearms=spec.hands_follow_forearms,
        natural_arm_pose=spec.natural_arm_pose,
    )
    rows = {name: (frames, duration) for name, frames, duration in spec.rows}
    if "cosmic_drift" in rows:
        f, d = rows["cosmic_drift"]
        clips["cosmic_drift"] = _pose(r, f, d, loop=True,
            root_y=[-5,-7,-9,-8,-5,-3,-2,-3], torso=[-4,-6,-7,-5,-2,1,0,-2], head=[2,4,5,3,1,-1,0,1],
            near_hand=([22,28,31,28,22,16,14,17],[-57,-63,-68,-65,-58,-52,-50,-53],[65,55,45,55,65,75,80,72]),
            far_hand=([-18,-24,-27,-24,-18,-12,-10,-13],[-56,-62,-67,-64,-57,-51,-49,-52],[115,125,135,125,115,105,100,108]))
    if "float_glide" in rows:
        f, d = rows["float_glide"]
        clips["float_glide"] = _pose(r, f, d, loop=True,
            root_y=[-8,-10,-12,-11,-8,-6,-5,-6], torso=[-5,-7,-8,-6,-3,0,-1,-3], head=[3,5,6,4,2,0,1,2],
            near_hand=([26,31,34,31,26,21,19,22],[-61,-66,-70,-68,-62,-57,-55,-58],[55,45,35,45,55,65,70,62]),
            far_hand=([-22,-27,-30,-27,-22,-17,-15,-18],[-60,-65,-69,-67,-61,-56,-54,-57],[125,135,145,135,125,115,110,118]))
    action_specs = {
        "think": dict(loop=True, torso=[0,2,4,3,1,-1,-1,0], head=[-2,-5,-8,-6,-2,1,0,-1],
            near_hand=([17,9,0,-7,-10,-6,3,12],[-48,-58,-69,-80,-87,-81,-68,-56],[80,65,50,35,25,35,55,70])),
        "use_telescope": dict(loop=False, torso=[0,3,7,10,11,10,7,4,1,0], head=[0,-3,-7,-10,-11,-10,-7,-4,-1,0],
            near_hand=([17,7,-5,-18,-28,-31,-28,-18,-2,17],[-48,-57,-67,-77,-84,-86,-83,-75,-61,-48],[80,65,50,35,20,15,20,35,55,80]),
            far_hand=([-13,-5,4,13,20,23,20,12,0,-13],[-47,-55,-63,-71,-77,-79,-76,-69,-57,-47],[100,115,130,145,160,165,160,145,125,100])),
        "stargaze": dict(loop=False, root_y=[0,-2,-5,-8,-11,-13,-11,-7,-3,0], torso=[0,-3,-7,-11,-14,-16,-13,-9,-4,0], head=[0,3,7,11,14,16,13,9,4,0],
            near_hand=([17,10,2,-7,-16,-24,-18,-8,5,17],[-48,-59,-71,-82,-92,-98,-91,-79,-63,-48],[80,65,50,35,20,10,20,40,60,80]),
            # Keep the far hand on Carl's west-facing side while it rises.  The
            # older arc crossed through the shoulder late in the gesture and
            # made the lower arm snap roughly ninety degrees in one frame.
            far_hand=([-13,-14,-16,-18,-20,-21,-20,-18,-15,-13],[-47,-56,-65,-73,-80,-84,-78,-68,-56,-47],[100,112,124,136,148,155,148,132,116,100])),
        "jab": dict(loop=False, torso=[0,5,12,9,3], head=[0,-3,-7,-5,-1],
            near_hand=([17,2,-28,-40,17],[-48,-50,-53,-54,-48],[80,55,15,0,80])),
        "punch": dict(loop=False, torso=[0,4,9,15,12,6,0], head=[0,-2,-5,-8,-6,-3,0],
            near_hand=([17,7,-8,-29,-44,-18,17],[-48,-51,-54,-57,-57,-53,-48],[80,65,45,18,0,35,80]),
            far_hand=([-13,-8,-2,5,8,1,-13],[-47,-45,-43,-42,-43,-45,-47],[100,105,112,120,125,115,100])),
        "planetary_orbit": dict(loop=False, root_y=[0,-1,-3,-5,-6,-4,-2,-1,0], torso=[0,3,7,11,14,11,7,3,0], head=[0,-2,-5,-7,-9,-7,-5,-2,0],
            near_hand=([17,8,-3,-15,-28,-35,-24,-5,17],[-48,-58,-68,-75,-77,-70,-59,-51,-48],[80,60,40,20,5,15,35,60,80]),
            far_hand=([-13,-6,2,10,18,23,16,2,-13],[-47,-54,-61,-66,-68,-63,-55,-49,-47],[100,115,130,145,160,150,130,110,100])),
        "attack_up": dict(loop=False, torso=[0,-2,-6,-10,-12,-8,-3,0], head=[0,2,5,8,10,7,3,0],
            near_hand=([17,10,2,-7,-15,-9,4,17],[-48,-60,-73,-85,-95,-88,-67,-48],[80,60,40,20,5,20,55,80])),
        "attack_down": dict(loop=False, torso=[0,3,7,12,14,10,4,0], head=[0,-2,-5,-8,-10,-7,-3,0],
            near_hand=([17,7,-5,-18,-30,-24,-7,17],[-48,-45,-41,-37,-34,-37,-42,-48],[80,65,45,20,5,20,50,80])),
        "pale_blue_dot": dict(loop=False, root_y=[0,-1,-3,-5,-7,-5,-3,-1,0], torso=[0,3,7,11,14,11,7,3,0], head=[0,-2,-5,-8,-10,-8,-5,-2,0],
            near_hand=([17,7,-6,-21,-36,-43,-37,-17,17],[-48,-54,-61,-67,-71,-72,-67,-57,-48],[80,65,45,25,8,0,12,45,80]),
            far_hand=([-13,-7,-1,5,10,12,9,1,-13],[-47,-50,-54,-58,-60,-59,-55,-50,-47],[100,108,116,125,135,138,130,115,100])),
        "cosmic_calendar": dict(loop=False, root_y=[0,-1,-2,-4,-6,-5,-3,-2,-1,0], torso=[0,2,5,8,11,13,10,7,3,0], head=[0,-1,-3,-5,-7,-8,-6,-4,-2,0],
            near_hand=([17,11,4,-4,-13,-23,-30,-24,-8,17],[-48,-55,-62,-69,-75,-80,-82,-75,-61,-48],[80,70,60,50,40,25,15,30,55,80]),
            far_hand=([-13,-7,0,8,17,27,34,28,12,-13],[-47,-54,-61,-68,-74,-79,-81,-74,-60,-47],[100,110,120,130,140,155,165,150,125,100])),
        "billions_and_billions": dict(loop=False, root_y=[0,-1,-3,-5,-7,-6,-4,-2,-1,0], torso=[0,3,7,11,15,17,14,9,4,0], head=[0,-2,-5,-8,-11,-12,-9,-6,-3,0],
            near_hand=([17,10,3,-4,-10,-4,8,22,30,17],[-48,-54,-60,-65,-68,-65,-59,-53,-50,-48],[80,70,60,50,40,50,65,75,80,80]),
            far_hand=([-13,-6,1,8,14,8,-4,-18,-26,-13],[-47,-53,-59,-64,-67,-64,-58,-52,-49,-47],[100,110,120,130,140,130,115,105,100,100])),
        "starstuff": dict(loop=False, root_y=[0,-2,-5,-9,-13,-16,-14,-10,-5,0], pelvis=[0,8,18,30,45,60,48,32,15,0], torso=[0,-4,-9,-14,-19,-23,-19,-13,-6,0], head=[0,3,7,11,15,18,15,10,5,0],
            near_hand=([17,10,2,-7,-14,-18,-14,-7,5,17],[-48,-59,-70,-80,-88,-92,-87,-77,-62,-48],[80,65,50,35,20,12,22,42,62,80]),
            # A broad two-arm cosmic lift, but both wrists remain on stable IK
            # arcs instead of crossing a shoulder as the torso pitches back.
            far_hand=([-13,-14,-16,-18,-20,-21,-20,-18,-15,-13],[-47,-56,-65,-74,-82,-86,-80,-70,-58,-47],[100,112,124,136,148,158,150,134,118,100])),
    }
    for name, kwargs in action_specs.items():
        f, d = rows[name]
        clips[name] = _pose(r, f, d, compact=False, **kwargs)
    # Air attacks share an expressive floating basis with directional hands.
    air_targets = {
        "air_neutral": ([-14,-22,-26,-22,-14,-6,2,8], [-78,-84,-86,-84,-78,-70,-64,-62]),
        "air_forward": ([-8,-20,-35,-43,-30,-12,17], [-64,-68,-70,-69,-65,-57,-48]),
        "air_back": ([17,24,34,40,31,22,17], [-48,-55,-62,-65,-61,-54,-48]),
        "air_down": ([17,10,2,-8,-17,-8,4], [-48,-43,-38,-33,-29,-35,-43]),
        "air_up": ([17,10,2,-8,-17,-8,4], [-48,-60,-73,-87,-96,-84,-64]),
    }
    for name, (xs, ys) in air_targets.items():
        f, d = rows[name]
        clips[name] = _pose(r, f, d, compact=False,
            root_y=[-8,-10,-12,-10,-8,-6,-7,-8][:f], torso=[-3,-5,-6,-4,-1,1,0,-2][:f], head=[2,4,5,3,1,-1,0,1][:f],
            near_hand=(xs[:f], ys[:f], [70,55,35,20,35,55,75,80][:f]))

    # ---- Pose-quality overrides -----------------------------------------
    # The complete fighter-motion surface deliberately reuses choreography,
    # but a semantic alias must not turn a transition into a looping pose or
    # inherit an IK singularity.  These representative rows get explicit,
    # conservative silhouettes that remain useful until the art merits finer
    # variation.
    if "fall_special" in rows:
        f, d = rows["fall_special"]
        clips["fall_special"] = deepcopy(clips["fall"])
        clips["fall_special"]["frames"] = f
        clips["fall_special"]["duration_ms"] = d
        clips["fall_special"]["loop"] = True

    for name in ("prone", "sleep", "trip_idle"):
        if name in rows:
            f, d = rows[name]
            clips[name] = _freeze_clip_pose(
                doc, clips, name=name, source="death", frames=f, duration_ms=d
            )

    def static_hold(
        name: str,
        *,
        near: tuple[float, float],
        far: tuple[float, float],
        torso_angle: float = 2.0,
        head_angle: float = -1.0,
    ) -> None:
        if name not in rows:
            return
        f, d = rows[name]
        channels = _neutral(r, compact=False)
        channels.update(
            {
                "torso": const(torso_angle),
                "head": const(head_angle),
                "near_hand_x": const(near[0]),
                "near_hand_y": const(near[1]),
                "far_hand_x": const(far[0]),
                "far_hand_y": const(far[1]),
            }
        )
        clips[name] = _clip(f, d, loop=True, channels=channels)

    static_hold("grab_hold", near=(-28.0, -57.0), far=(-25.0, -50.0), torso_angle=4.0)
    static_hold("item_hold", near=(-24.0, -55.0), far=(-19.0, -47.0))

    # Climb/swim used broad mirrored arcs copied from an older scientist. The
    # far wrist crossed the shoulder twice per cycle.  Keep the alternating
    # action but constrain both ellipses to Carl's west-facing side.
    if "climb" in clips:
        climb = deepcopy(clips["climb"])
        climb_channels = climb["channels"]
        climb_channels["near_hand_x"] = expr(f"{r['_natural_near_hand_x'] - 5.0}+4*sin(tau*t)")
        climb_channels["near_hand_y"] = expr(f"{r['_natural_near_hand_y'] - 14.0}-8*sin(tau*t)")
        climb_channels["far_hand_x"] = expr(f"{r['_natural_far_hand_x'] - 5.0}-4*sin(tau*t)")
        climb_channels["far_hand_y"] = expr(f"{r['_natural_far_hand_y'] - 12.0}+8*sin(tau*t)")
        clips["climb"] = climb
    if "swim" in clips:
        swim = deepcopy(clips["swim"])
        swim_channels = swim["channels"]
        swim_channels["near_hand_x"] = expr(f"{r['_natural_near_hand_x'] - 10.0}-10*sin(tau*t)")
        swim_channels["near_hand_y"] = expr(f"{r['_natural_near_hand_y']}+4*cos(tau*t)")
        swim_channels["far_hand_x"] = expr(f"{r['_natural_far_hand_x'] - 8.0}+10*sin(tau*t)")
        swim_channels["far_hand_y"] = expr(f"{r['_natural_far_hand_y']}-4*cos(tau*t)")
        clips["swim"] = swim

    if "ledge_getup" in clips:
        ledge = deepcopy(clips["ledge_getup"])
        ledge["channels"]["near_hand_x"] = keys([-46,-42,-34,-26,-18,-12], loop=False)
        ledge["channels"]["near_hand_y"] = keys([-78,-74,-66,-60,-56,-54], loop=False)
        ledge["channels"]["far_hand_x"] = keys([-38,-34,-28,-24,-20,-19], loop=False)
        ledge["channels"]["far_hand_y"] = keys([-68,-66,-62,-56,-50,-47], loop=False)
        clips["ledge_getup"] = ledge

    if "celebrate" in rows:
        f, d = rows["celebrate"]
        channels = _neutral(r, compact=False)
        channels.update(
            {
                "root_y": keys([0,-2,-4,-2,0,1,0,-1], loop=True),
                "torso": keys([0,-4,-7,-4,0,3,1,-1], loop=True),
                "head": keys([0,3,6,3,0,-2,-1,0], loop=True),
                "near_hand_x": keys([-11,-14,-18,-20,-18,-15,-12,-11], loop=True),
                "near_hand_y": keys([-54,-62,-72,-78,-72,-64,-58,-54], loop=True),
                "far_hand_x": keys([-19,-18,-16,-14,-15,-17,-18,-19], loop=True),
                "far_hand_y": keys([-47,-56,-66,-74,-70,-60,-52,-47], loop=True),
            }
        )
        clips["celebrate"] = _clip(f, d, loop=True, channels=channels)

    had_back_roll = "roll_back" in clips
    clips = materialize_motion_rows(
        rows=spec.rows,
        clips=clips,
        aliases=CARL_POSE_ALIASES,
        looping_rows=CARL_LOOPING_ROWS,
        character="carl_stargan",
    )
    if not had_back_roll:
        clips["roll_back"] = invert_rotation_channel(clips["roll_back"], "pelvis")

    # World-space roll targets were the source of the 170+ degree elbow pops
    # reported by the pose auditor.  Lock the hands to the rotating torso for
    # every row currently borrowing the roll silhouette, including the reverse
    # roll after its pelvis direction has been inverted.
    for name in (
        "roll",
        "roll_back",
        "tumble",
        "spot_dodge",
        "getup_roll",
        "tech_roll",
        "grab_escape",
        "trip_roll",
    ):
        if name in clips:
            clips[name] = _retarget_clip_arms_to_torso(doc, clips, name, reach_scale=0.78)

    # The prone/sleep/trip holds use the final collapse body pose but keep Carl's
    # normal arm anatomy in that rotated torso frame.  This avoids both the old
    # death-transition loop seam and wrists pointing back through his shoulders.
    for name in ("prone", "sleep", "trip_idle"):
        if name in clips:
            clips[name] = _retarget_clip_arms_to_torso(doc, clips, name, reach_scale=0.76)
    return clips


def _canonical_svg_part_order(svg_path: Path, view: str) -> list[str]:
    """Return rig-part names in the canonical SVG document order.

    Paint order is authored by moving the part groups in Inkscape, so document
    order is the only z-order authority for these canonical scientist rigs.
    ``data-rig-z`` remains readable by the generic SVG-rig importer for older
    attribute-ordered documents, but its numeric value is deliberately ignored
    here.  That keeps a legitimate group reorder from requiring a second, easy
    to forget renumbering pass over redundant metadata.
    """

    root = ET.fromstring(svg_path.read_bytes())
    layer = next(
        (elem for elem in root.iter() if elem.get(INK_LABEL) == view),
        None,
    )
    if layer is None:
        raise ValueError(f"{svg_path} has no SVG view {view!r}")

    names: list[str] = []
    for elem in layer.iter():
        name = elem.get("data-rig-part")
        if name is None:
            continue
        if name in names:
            raise ValueError(f"duplicate SVG rig part {name!r} in {view!r}")
        names.append(name)
    if not names:
        raise ValueError(f"{svg_path} view {view!r} contains no rig parts")
    return names


def _enforce_canonical_part_order(doc: dict, spec: CharacterSpec) -> None:
    """Rewrite extracted rig order from the canonical SVG, defensively."""

    source_order = _canonical_svg_part_order(spec.svg_path, spec.view)
    by_name = {str(part["name"]): part for part in doc.get("parts", [])}
    if set(by_name) != set(source_order):
        raise ValueError(
            f"{spec.name} extracted part set differs from canonical SVG: "
            f"missing={sorted(set(source_order) - set(by_name))}, "
            f"extra={sorted(set(by_name) - set(source_order))}"
        )
    ordered = []
    for index, name in enumerate(source_order):
        part = by_name[name]
        part["z"] = float(index)
        part["svg_source_order"] = index
        ordered.append(part)
    doc["parts"] = ordered


def _part_by_name(doc: RigDocument, name: str) -> dict:
    return next(part for part in doc.parts if str(part.get("name")) == name)


def _sprite_overlap_pixels(
    doc: RigDocument,
    first_name: str,
    second_name: str,
    *,
    composite_scale: float = 4.0,
) -> int:
    """Count overlapping nontransparent pixels with both parts pivot-aligned.

    Parts bound to the same bone must share the same authored pivot. Measuring
    overlap in pivot-local raster space catches an omitted, empty, or displaced
    overlay even when its numeric z value looks correct.
    """

    first = doc.sprite_raster(_part_by_name(doc, first_name), composite_scale)
    second = doc.sprite_raster(_part_by_name(doc, second_name), composite_scale)
    if first is None or second is None:
        return 0

    first_x = -int(round(first.pivot[0]))
    first_y = -int(round(first.pivot[1]))
    second_x = -int(round(second.pivot[0]))
    second_y = -int(round(second.pivot[1]))
    left = max(first_x, second_x)
    top = max(first_y, second_y)
    right = min(first_x + first.image.width, second_x + second.image.width)
    bottom = min(first_y + first.image.height, second_y + second.image.height)
    if right <= left or bottom <= top:
        return 0

    first_alpha = first.image.getchannel("A").crop(
        (left - first_x, top - first_y, right - first_x, bottom - first_y)
    )
    second_alpha = second.image.getchannel("A").crop(
        (left - second_x, top - second_y, right - second_x, bottom - second_y)
    )
    overlap = ImageChops.multiply(first_alpha, second_alpha)
    return sum(overlap.histogram()[1:])


def _validate_carl_layer_model(doc: RigDocument) -> None:
    """Validate Carl's multiple same-bone paint slices and head overlays."""

    part_names = [str(part["name"]) for part in doc.parts]
    ordered_slices = (
        "torso_backing",
        "torso",
        "head",
        "torso_front_overlay",
        "hair_back",
        "hair_front",
    )
    indices = [part_names.index(name) for name in ordered_slices]
    if indices != sorted(indices):
        raise ValueError(
            "Carl Stargan canonical paint slices are out of order: "
            f"{list(zip(ordered_slices, indices))!r}"
        )

    expected_bones = {
        "torso_backing": "torso",
        "torso": "torso",
        "torso_front_overlay": "torso",
        "head": "head",
        "hair_back": "head",
        "hair_front": "head",
    }
    actual_bones = {
        name: str(_part_by_name(doc, name).get("bone"))
        for name in expected_bones
    }
    wrong_bones = {
        name: (actual_bones[name], expected)
        for name, expected in expected_bones.items()
        if actual_bones[name] != expected
    }
    if wrong_bones:
        raise ValueError(f"Carl Stargan canonical paint slices bind wrong bones: {wrong_bones}")

    back_overlap = _sprite_overlap_pixels(doc, "head", "hair_back")
    front_overlap = _sprite_overlap_pixels(doc, "head", "hair_front")
    if back_overlap < 500 or front_overlap < 150:
        raise ValueError(
            "Carl Stargan hair rasters do not cover the skull as authored: "
            f"head/hair_back={back_overlap}px, head/hair_front={front_overlap}px"
        )


def _visible_joint_copy(svg_path: Path) -> Path:
    root = ET.fromstring(svg_path.read_bytes())
    found = False
    for elem in root.iter():
        if elem.get(INK_LABEL) == "Rig Joints":
            elem.set("style", "display:inline")
            found = True
    if not found:
        raise ValueError(f"{svg_path} has no 'Rig Joints' layer")
    handle = tempfile.NamedTemporaryFile(prefix=f"{svg_path.stem}-joints-", suffix=".svg", delete=False)
    handle.close()
    path = Path(handle.name)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return path


def build_one(spec: CharacterSpec) -> Path:
    if spec.name == "patent_clerk":
        validate_motion_coverage(
            row_names=[name for name, _frames, _duration in spec.rows],
            coverage=PATENT_MOTION_COVERAGE,
            scopes=PATENT_MOTION_SCOPES,
            character="patent_clerk",
        )
    elif spec.name == "carl_stargan":
        validate_motion_coverage(
            row_names=[name for name, _frames, _duration in spec.rows],
            coverage=CARL_MOTION_COVERAGE,
            scopes=CARL_MOTION_SCOPES,
            character="carl_stargan",
        )

    renderer_path, renderer_version = _require_native_resvg()
    if not spec.svg_path.exists():
        raise FileNotFoundError(spec.svg_path)
    temporary = _visible_joint_copy(spec.svg_path)
    try:
        width, height = spec.frame_size
        doc = build_humanoid_view_document(
            temporary,
            spec.rig_dir,
            HumanoidViewSpec(
                view=spec.view,
                name=spec.name,
                frame_width=width,
                frame_height=height,
                center_x=width / 2.0,
                ground_y=height - spec.ground_margin,
                target_height=spec.target_height,
                ref_dpi=96.0,
                supersample=4,
                render_scale=1,
                collision_scale=spec.collision_scale,
                part_order="document",
                arm_pose_hints=spec.natural_arm_pose,
                arm_max_reach_ratio=spec.arm_max_reach_ratio,
            ),
        )
    finally:
        temporary.unlink(missing_ok=True)

    _enforce_canonical_part_order(doc, spec)
    doc["svg_source"]["path"] = os.path.relpath(spec.svg_path, spec.rig_dir)
    doc["clips"] = (
        _patent_clips(spec, doc)
        if spec.name == "patent_clerk"
        else _stargan_clips(spec, doc)
    )
    doc["features"] = {
        "paper_doll": True,
        "canonical_svg": True,
        "facing": "left",
        "source_authority": str(spec.svg_path.relative_to(ROOT)),
        "source_pose_role": "geometry-layout-only",
        "natural_pose_authority": "character-spec",
        "part_order_policy": "svg-document-order",
    }
    if spec.natural_arm_pose:
        doc["natural_pose"] = {
            "arms": {
                side: {
                    "hand": [float(hint.target[0]), float(hint.target[1])],
                    "elbow": [float(hint.joint[0]), float(hint.joint[1])],
                }
                for side, hint in spec.natural_arm_pose.items()
            }
        }
    doc["asset_metadata"] = {
        "source_kind": "manual-svg-paperdoll",
        "builder": "scripts/build_scientist_fighter_rigs.py",
        "character": spec.name,
    }
    doc["build_provenance"] = {
        "schema": "canonical-svg-rig-v3",
        "builder_version": BUILDER_VERSION,
        "renderer": "resvg_py",
        "renderer_version": renderer_version,
        "renderer_backend": "native-extension",
        "svg_sha256": _sha256(spec.svg_path),
        "part_order_policy": "svg-document-order",
        "part_order": "svg-document",
    }
    spec.rig_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, indent=2, sort_keys=False) + "\n"
    spec.rig_path.write_text(text, encoding="utf-8")
    return spec.rig_path


def validate_one(spec: CharacterSpec) -> None:
    path = build_one(spec)
    doc = RigDocument.load(path)
    expected = {name for name, _frames, _duration in spec.rows}
    actual = set(doc.clips)
    if actual != expected:
        raise ValueError(
            f"{spec.name} clip mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}"
        )
    required_parts = {
        "pelvis", "torso", "head",
        "near_arm_u", "near_arm_l", "near_hand",
        "far_arm_u", "far_arm_l", "far_hand",
        "near_leg_u", "near_leg_l", "near_foot",
        "far_leg_u", "far_leg_l", "far_foot",
    }
    parts = {str(part["name"]) for part in doc.parts}
    missing = required_parts - parts
    if missing:
        raise ValueError(f"{spec.name} rig missing parts: {sorted(missing)}")

    provenance = doc.data.get("build_provenance") or {}
    if provenance.get("renderer") != "resvg_py":
        raise ValueError(f"{spec.name} rig was not built by native resvg_py")
    if provenance.get("svg_sha256") != _sha256(spec.svg_path):
        raise ValueError(f"{spec.name} rig source hash does not match its SVG")
    if provenance.get("part_order") != "svg-document":
        raise ValueError(f"{spec.name} rig does not preserve SVG document order")

    z_values = [float(part.get("z", 0.0)) for part in doc.parts]
    expected_z = [float(index) for index in range(len(doc.parts))]
    if z_values != expected_z:
        raise ValueError(
            f"{spec.name} rig part z-order is not canonical SVG document order: "
            f"{z_values!r}"
        )
    if spec.name == "carl_stargan":
        _validate_carl_layer_model(doc)

    rendered_frames = 0
    for animation, frames, _duration in spec.rows:
        for frame_idx in range(frames):
            image = doc.render_frame(animation, frame_idx, frames)
            if image.mode != "RGBA":
                raise ValueError(f"{spec.name}:{animation}:{frame_idx} is not RGBA")
            if image.getbbox() is None:
                raise ValueError(f"{spec.name}:{animation}:{frame_idx} rendered empty")
            rendered_frames += 1

    print(
        f"{spec.name}: {len(doc.parts)} parts, {len(doc.bones)} bones, "
        f"{len(doc.clips)} clips, {rendered_frames} native-resvg frames -> {path}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "validate"), nargs="?", default="build")
    parser.add_argument("characters", nargs="*", choices=tuple(SPECS), default=None)
    args = parser.parse_args(argv)
    names = args.characters or list(SPECS)
    renderer_path, renderer_version = _require_native_resvg()
    print(f"SVG renderer: resvg_py {renderer_version} ({renderer_path})")
    for name in names:
        if args.command == "validate":
            validate_one(SPECS[name])
        else:
            print(build_one(SPECS[name]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
