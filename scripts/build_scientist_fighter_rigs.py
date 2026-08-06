#!/usr/bin/env python3
"""Build the canonical SVG rigs for Patent Clerk and Carl Stargan.

The manually traced SVGs in ``assets/`` are the art authority. This builder only
extracts their explicit part/joint annotations and authors animation clips; it
never recreates character geometry.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
import types
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _install_resvg_fallback() -> str:
    try:
        import resvg_py  # noqa: F401
        return "resvg_py"
    except ModuleNotFoundError:
        try:
            import cairosvg
        except ModuleNotFoundError as ex:
            raise RuntimeError(
                "building SVG rigs requires resvg_py or CairoSVG"
            ) from ex
        module = types.ModuleType("resvg_py")

        def svg_to_bytes(*, svg_string: str, dpi: float = 96.0):
            return cairosvg.svg2png(
                bytestring=svg_string.encode("utf-8"),
                dpi=float(dpi),
            )

        module.svg_to_bytes = svg_to_bytes  # type: ignore[attr-defined]
        sys.modules["resvg_py"] = module
        return "cairosvg fallback"


_RENDERER = _install_resvg_fallback()

from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (  # noqa: E402
    HumanoidViewSpec,
    build_humanoid_view_document,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument  # noqa: E402

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


PATENT_ROWS = (
    ("idle", 8, 148), ("walk", 8, 106), ("run", 8, 76),
    ("crouch", 6, 94), ("crouch_walk", 8, 90), ("jump", 6, 88),
    ("fall", 6, 92), ("land_hard", 7, 80), ("dash_startup", 4, 50),
    ("dash", 6, 58), ("slide", 6, 68), ("roll", 8, 58),
    ("wall_grab", 6, 102), ("wall_jump", 6, 80),
    ("ledge_grab", 6, 96), ("ledge_climb", 6, 92),
    ("climb", 8, 96), ("swim", 8, 102), ("block", 6, 80),
    ("known_result", 7, 62), ("hit", 5, 82), ("death", 9, 102),
    ("talk", 8, 104), ("interact", 8, 92),
    ("application_review", 6, 58), ("margin_correction", 7, 64),
    ("light_argument", 8, 66), ("reference_frame", 9, 72),
    ("elevator_thought", 9, 72), ("synchronize_clocks", 10, 78),
    ("mass_energy_conversion", 10, 80), ("annus_mirabilis", 12, 82),
    ("celebrate", 8, 88), ("taunt", 8, 92),
)

STARGAN_ROWS = (
    ("idle", 8, 150), ("walk", 8, 108), ("run", 8, 82),
    ("crouch", 6, 96), ("crouch_walk", 8, 90), ("jump", 6, 92),
    ("fall", 6, 92), ("land_hard", 8, 92),
    ("land_recovery", 6, 74), ("dash_startup", 4, 52),
    ("dash", 6, 62), ("cosmic_drift", 8, 58), ("slide", 6, 70),
    ("roll", 8, 58), ("wall_grab", 6, 105),
    ("wall_jump", 6, 82), ("ledge_grab", 6, 98),
    ("ledge_climb", 6, 98), ("ledge_getup", 6, 44),
    ("ledge_roll", 8, 40), ("climb", 8, 98), ("swim", 8, 104),
    ("float_glide", 8, 108), ("block", 6, 84), ("hit", 5, 88),
    ("death", 8, 108), ("talk", 8, 108), ("interact", 8, 92),
    ("think", 8, 112), ("use_telescope", 10, 96),
    ("stargaze", 10, 108), ("jab", 5, 58), ("punch", 7, 70),
    ("planetary_orbit", 9, 72), ("attack_up", 8, 66),
    ("attack_down", 8, 66), ("air_neutral", 8, 62),
    ("air_forward", 7, 62), ("air_back", 7, 62),
    ("air_down", 7, 70), ("air_up", 7, 62),
    ("pale_blue_dot", 9, 78), ("cosmic_calendar", 10, 78),
    ("billions_and_billions", 10, 76), ("starstuff", 10, 76),
    ("celebrate", 8, 90), ("taunt", 8, 94),
)

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
    ),
    "carl_stargan": CharacterSpec(
        name="carl_stargan",
        svg_name="carl-stargan.svg",
        view="Carl Stargan - Side Left",
        frame_size=(160, 160),
        target_height=112.0,
        ground_margin=24.0,
        collision_scale=1.58,
        rows=STARGAN_ROWS,
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


def _rest(doc: Mapping[str, object]) -> dict[str, float]:
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
    return out


def _clip(frames: int, duration_ms: int, *, loop: bool, channels: Mapping[str, dict]) -> dict:
    return {
        "loop": bool(loop),
        "frames": int(frames),
        "duration_ms": int(duration_ms),
        "channels": dict(channels),
    }


def _neutral(rest: Mapping[str, float], *, compact: bool) -> dict[str, dict]:
    hand_y = -50.0 if compact else -48.0
    return {
        "near_hand_x": const(17.0),
        "near_hand_y": const(hand_y),
        "near_hand_pitch": const(80.0),
        "far_hand_x": const(-13.0),
        "far_hand_y": const(hand_y + 1.0),
        "far_hand_pitch": const(100.0),
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
            "near_hand_x": expr(f"17-{arm}*sin(tau*t)"),
            "near_hand_y": expr(f"{-50 if compact else -48}+2*sin(tau*t)"),
            "far_hand_x": expr(f"-13+{arm}*sin(tau*t)"),
            "far_hand_y": expr(f"{-49 if compact else -47}-2*sin(tau*t)"),
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
            channels[f"{prefix}_x"] = keys(triplet[0], loop=loop)
            channels[f"{prefix}_y"] = keys(triplet[1], loop=loop)
            channels[f"{prefix}_pitch"] = keys(triplet[2], loop=loop)
    for prefix, triplet in (("near_foot", near_foot), ("far_foot", far_foot)):
        if triplet is not None:
            channels[f"{prefix}_x"] = keys(triplet[0], loop=loop)
            channels[f"{prefix}_lift"] = keys(triplet[1], loop=loop)
            channels[f"{prefix}_pitch"] = keys(triplet[2], loop=loop)
    return _clip(frames, duration, loop=loop, channels=channels)


def _common_clips(spec: CharacterSpec, doc: Mapping[str, object], *, compact: bool) -> dict[str, dict]:
    r = _rest(doc)
    rows = {name: (frames, duration) for name, frames, duration in spec.rows}
    clips: dict[str, dict] = {}
    f, d = rows["idle"]
    idle = _neutral(r, compact=compact)
    idle.update({
        "root_y": expr("0.65*sin(tau*t)"),
        "torso": expr("1.1*sin(tau*t)"),
        "head": expr("-0.8*sin(tau*t)"),
        "near_hand_y": expr(f"{-50 if compact else -48}+0.8*sin(tau*t)"),
        "far_hand_y": expr(f"{-49 if compact else -47}-0.6*sin(tau*t)"),
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
            clips[name] = _pose(r, f, d, compact=compact,
                root_y=[-3,-4,-6,-10,-10,-6,-4,-3], pelvis=[0,45,90,135,180,225,270,315],
                torso=[0,20,35,45,35,20,8,0], head=[0,-15,-25,-30,-25,-15,-6,0],
                near_hand=([8,1,-6,-10,-6,1,8,14],[-48,-42,-38,-36,-38,-42,-48,-52],[70,45,20,0,160,135,105,80]),
                far_hand=([-6,1,7,10,7,1,-6,-11],[-47,-41,-37,-35,-37,-41,-47,-51],[110,135,160,180,20,45,75,100]))

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
    clips = _common_clips(spec, doc, compact=True)
    r = _rest(doc)
    rows = {name: (frames, duration) for name, frames, duration in spec.rows}
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
        f, d = rows[name]
        clips[name] = _pose(r, f, d, compact=True, **kwargs)
    return clips


def _stargan_clips(spec: CharacterSpec, doc: Mapping[str, object]) -> dict[str, dict]:
    clips = _common_clips(spec, doc, compact=False)
    r = _rest(doc)
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
            far_hand=([-13,-6,2,11,20,28,22,12,0,-13],[-47,-58,-70,-81,-91,-97,-90,-78,-62,-47],[100,115,130,145,160,170,160,140,120,100])),
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
            near_hand=([17,12,6,-1,-8,-14,-10,-3,7,17],[-48,-59,-70,-80,-89,-94,-88,-77,-61,-48],[80,65,50,35,20,10,20,40,60,80]),
            far_hand=([-13,-8,-2,5,12,18,14,7,-3,-13],[-47,-58,-69,-79,-88,-93,-87,-76,-60,-47],[100,115,130,145,160,170,160,140,120,100])),
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
    return clips


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
            ),
        )
    finally:
        temporary.unlink(missing_ok=True)

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
    }
    doc["asset_metadata"] = {
        "source_kind": "manual-svg-paperdoll",
        "builder": "scripts/build_scientist_fighter_rigs.py",
        "character": spec.name,
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
    print(f"{spec.name}: {len(doc.parts)} parts, {len(doc.bones)} bones, {len(doc.clips)} clips -> {path}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "validate"), nargs="?", default="build")
    parser.add_argument("characters", nargs="*", choices=tuple(SPECS), default=None)
    args = parser.parse_args(argv)
    names = args.characters or list(SPECS)
    print(f"SVG renderer: {_RENDERER}")
    for name in names:
        if args.command == "validate":
            validate_one(SPECS[name])
        else:
            print(build_one(SPECS[name]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
