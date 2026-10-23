#!/usr/bin/env python3
"""Build the rig documents of the two mites, v2 (``dividing_mite_v2``, ``exploding_mite_v2``).

    uv run python scripts/svg_art/mites_art.py --cast   # the drawings, once
    uv run python scripts/build_mite_v2_rigs.py

The drawing (``mites_art.cast(name)``) says where each part turns and where
each of the eight legs has its hip, knee and foot. This script makes the
skeleton from those joints, binds each part layer to its bone, and authors
the rows. It never draws.

Each leg is two bones (thigh, shin) solved to a foot target (an ``ik_chains``
entry, channels ``<leg>_foot_x`` / ``<leg>_foot_y`` in frame pixels from
``(center_x, ground_y)``). A foot target is fixed in the frame, so a body that
bobs, rears or lunges keeps its feet where they stand; the walk moves the
targets on the stepping curve of ``authoring/surface_gait.Gait``.

The rows are the seven the enemies use: ``idle``, ``walk``, ``run``,
``slash`` (the mandibles snap; the hit is live 0.30-0.52 for the exploding
mite and 0.32-0.56 for the dividing mite, as before), ``hit``, ``death``,
``dash``.

- ``death`` of the dividing mite: it strains, the ring goes hot, and the two
  lobes pull apart left and right (the game puts a Puppy Slug where each goes).
- ``death`` of the exploding mite: the fuse burns down to the cap and the
  shell swells and glows white hot (the blast is the game's effect).
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.authoring.surface_gait import Gait  # noqa: E402
from ambition_sprite2d_renderer.devtools.svg_rig_tool import install_repo_metadata  # noqa: E402

_spec = importlib.util.spec_from_file_location("mites_art", ROOT / "scripts" / "svg_art" / "mites_art.py")
art = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = art
_spec.loader.exec_module(art)

PKG = ROOT / "ambition_sprite2d_renderer"
#: Frame pixels for each SVG unit.
SCALE = 0.6
FRAME = {"width": 288, "height": 200, "center_x": 144, "ground_y": 188, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}

POSITIONS = ("rear", "rmid", "fmid", "front")


def rig_path(name: str) -> Path:
    return PKG / "targets" / "characters" / "rigged" / name / f"{name}_side.rig.json"


def expr(text: str) -> dict:
    return {"expr": text}


def keys(values: List[float], kind: str = "linear") -> dict:
    """One value per frame of a one-shot row (frame ``i`` of ``n`` at ``t = i/(n-1)``)."""
    n = len(values)
    return {"keys": [[round(i / (n - 1), 6), round(v, 4), kind] for i, v in enumerate(values)]}


def smooth(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def px(pt) -> tuple:
    """A design point as frame pixels from ``(center_x, ground_y)``."""
    return ((pt[0] - art.CAST_CX) * SCALE, (pt[1] - art.GROUND) * SCALE)


class Mite:
    """One mite's rig facts, read from its cast drawing."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.cast = art.CAST[name]()
        self.legs = self.cast.legs
        #: Each leg's foot at rest, frame px from (center_x, ground_y).
        self.rest = {leg: px(foot) for leg, (_p, _h, _k, foot) in self.legs.items()}

    def leg_phase(self, leg: str) -> float:
        """Two alternating sets of four feet, with a small wave from back to front."""
        side, pos = leg.split("_", 1)
        i = POSITIONS.index(pos)
        return ((i % 2) * 0.5 + (0.5 if side == "far" else 0.0) + 0.06 * i) % 1.0

    def feet(self, dx: Dict[str, float] | None = None, dy: Dict[str, float] | None = None) -> dict:
        """Constant foot targets: the rest, moved by ``dx``/``dy`` per leg."""
        out = {}
        for leg, (x, y) in self.rest.items():
            out[f"{leg}_foot_x"] = {"const": round(x + (dx or {}).get(leg, 0.0), 4)}
            out[f"{leg}_foot_y"] = {"const": round(y + (dy or {}).get(leg, 0.0), 4)}
        return out

    def gait(self, gait: Gait) -> dict:
        out = {}
        for leg, (x, y) in self.rest.items():
            ex, lift = gait.expressions(self.leg_phase(leg))
            out[f"{leg}_foot_x"] = expr(f"{x:.4f}+({ex})")
            out[f"{leg}_foot_y"] = expr(f"{y:.4f}-({lift})")
        return out

    def per_frame_feet(self, n: int, dx_of) -> dict:
        """Feet moved per frame: ``dx_of(leg, i)`` px along x."""
        out = {}
        for leg, (x, y) in self.rest.items():
            out[f"{leg}_foot_x"] = keys([x + dx_of(leg, i) for i in range(n)])
            out[f"{leg}_foot_y"] = {"const": round(y, 4)}
        return out


WALK = Gait(stride=13.0, stance=0.6, lift=6.0)
RUN = Gait(stride=21.0, stance=0.55, lift=9.0)
DASH = Gait(stride=26.0, stance=0.5, lift=7.0)


def snap(m: Mite, start: float, end: float, n: int = 8) -> dict:
    """The swing: rear back with the mandibles open, lunge and snap them shut
    while the hit is live (``start``-``end``), settle."""
    body, rx, ry, near, far = [], [], [], [], []
    for i in range(n):
        t = i / (n - 1)
        wind = smooth(t / start) if t < start else 1.0
        strike = smooth((t - start) / (end - start)) if t >= start else 0.0
        back = smooth((t - end) / (1.0 - end)) if t > end else 0.0
        body.append(-9.0 * wind * (1 - strike) + 7.0 * strike * (1 - back))
        rx.append(-4.0 * wind * (1 - strike) + 10.0 * strike * (1 - back))
        ry.append(-2.0 * wind * (1 - strike) + 1.5 * strike * (1 - back))
        near.append(30.0 * wind * (1 - strike) - 12.0 * strike * (1 - back))
        far.append(-22.0 * wind * (1 - strike) + 10.0 * strike * (1 - back))
    return {"root_x": keys(rx, "smooth"), "root_y": keys(ry, "smooth"), "body": keys(body, "smooth"),
            "mandible_near": keys(near, "smooth"), "mandible_far": keys(far, "smooth"), **m.feet()}


JOLT = "(1-t)*(1-t)"


def common_clips(m: Mite, live: tuple) -> Dict[str, dict]:
    return {
        "idle": {"loop": True, "frames": 8, "duration_ms": 130, "channels": {
            "root_y": expr("0.9*sin(tau*t)"),
            "body": expr("0.8*sin(tau*t+0.6)"),
            "mandible_near": expr("4*sin(tau*t*2)"), "mandible_far": expr("-4*sin(tau*t*2+0.4)"),
            **m.feet()}},
        "walk": {"loop": True, "frames": 8, "duration_ms": 90, "channels": {
            "root_y": expr("-1.1*abs(sin(2*tau*t))"),
            "body": expr("1.2*sin(2*tau*t)"),
            "mandible_near": expr("5*sin(tau*t)"), "mandible_far": expr("-5*sin(tau*t+0.5)"),
            **m.gait(WALK)}},
        "run": {"loop": True, "frames": 8, "duration_ms": 60, "channels": {
            "root_y": expr("1.0-1.8*abs(sin(2*tau*t))"),
            "body": expr("4+1.5*sin(2*tau*t)"),
            "mandible_near": expr("-6+5*sin(tau*t)"), "mandible_far": expr("4-5*sin(tau*t+0.5)"),
            **m.gait(RUN)}},
        "dash": {"loop": True, "frames": 6, "duration_ms": 55, "channels": {
            "root_y": expr("3.0-1.2*abs(sin(2*tau*t))"),
            "body": expr("8+1.0*sin(2*tau*t)"),
            "mandible_near": expr("-14"), "mandible_far": expr("10"),
            **m.gait(DASH)}},
        "slash": {"loop": False, "frames": 8, "duration_ms": 70, "channels": snap(m, *live)},
        "hit": {"loop": False, "frames": 5, "duration_ms": 80, "channels": {
            "root_x": expr(f"-5*{JOLT}"), "root_y": expr(f"-2*{JOLT}"), "body": expr(f"-12*{JOLT}"),
            "mandible_near": expr(f"26*{JOLT}"), "mandible_far": expr(f"-20*{JOLT}"),
            **m.feet()}},
    }


def dividing_clips(m: Mite) -> Dict[str, dict]:
    clips = common_clips(m, (0.32, 0.56))
    for row, amp in (("idle", 5.0), ("walk", 8.0), ("run", 10.0), ("dash", 6.0), ("hit", 0.0)):
        ch = clips[row]["channels"]
        if row == "hit":
            ch["rear_feeler"] = expr(f"-18*{JOLT}")
            ch["front_feeler"] = expr(f"22*{JOLT}")
            continue
        ch["rear_feeler"] = expr(f"{amp}*sin(tau*t+1.1)")
        ch["front_feeler"] = expr(f"{amp}*sin(tau*t+0.2)")
        # the cell throbs at its waist: the lobes breathe against each other
        ch["bone.rear_lobe.x"] = expr("-0.5*sin(tau*t)")
        ch["bone.front_lobe.x"] = expr("0.5*sin(tau*t)")
    clips["slash"]["channels"]["front_feeler"] = expr("-12*sin(pi*t)")
    clips["slash"]["channels"]["rear_feeler"] = expr("8*sin(pi*t)")
    # death: it strains, the ring goes hot, and the lobes pull apart
    n = 8
    split, tilt, jitter, hot, strand = [], [], [], [], []
    for i in range(n):
        t = i / (n - 1)
        e = smooth((t - 0.35) / 0.65)
        split.append(18.0 * e)
        tilt.append(11.0 * e)
        jitter.append((1.6 if i % 2 else -1.6) * (1 - e) * (t > 0.0))
        hot.append(1.0 if 0.15 < t < 0.75 else 0.0)
        strand.append(1.0 if t >= 0.75 else 0.0)
    lobe_of = {leg: parent for leg, (parent, *_rest) in m.legs.items()}
    clips["death"] = {"loop": False, "frames": n, "duration_ms": 95, "channels": {
        "bone.rear_lobe.x": keys([-s + j for s, j in zip(split, jitter)]),
        "bone.front_lobe.x": keys([s - j for s, j in zip(split, jitter)]),
        "rear_lobe": keys([-a for a in tilt]), "front_lobe": keys(tilt),
        "rear_feeler": keys([-20.0 * min(1.0, s / 18.0) for s in split]),
        "front_feeler": keys([20.0 * min(1.0, s / 18.0) for s in split]),
        "mandible_near": keys([18.0 * min(1.0, i / 4) for i in range(n)]),
        "mandible_far": keys([-14.0 * min(1.0, i / 4) for i in range(n)]),
        "ring_cool": keys([1.0 - h - s for h, s in zip(hot, strand)]),
        "ring_hot": keys(hot), "strand": keys(strand),
        **m.per_frame_feet(n, lambda leg, i: (-split[i] if lobe_of[leg] == "rear_lobe" else split[i])),
    }}
    return clips


SPARK_FLICKER = "1 if floor(t*8+0.01) % 2 == 0 else 0"


def exploding_clips(m: Mite) -> Dict[str, dict]:
    clips = common_clips(m, (0.30, 0.52))
    for row, ch in ((r, c["channels"]) for r, c in clips.items()):
        sway = {"idle": "5*sin(tau*t)", "walk": "8*sin(2*tau*t+0.6)", "run": "-14+6*sin(2*tau*t)", "dash": "-22+4*sin(2*tau*t)",
                "slash": "10*sin(pi*t)", "hit": f"-24*{JOLT}"}[row]
        ch["fuse"] = expr(sway)
        ch["spark_0a"] = expr(SPARK_FLICKER)
        ch["spark_0b"] = expr(f"1 - ({SPARK_FLICKER})")
    # death: the fuse burns down while the shell swells and goes white hot
    n = 8
    stage = [0 if i < 3 else (1 if i < 5 else 2) for i in range(n)]
    on = lambda s: keys([1.0 if st == s else 0.0 for st in stage])  # noqa: E731
    clips["death"] = {"loop": False, "frames": n, "duration_ms": 100, "channels": {
        "root_x": keys([(1.5 if i % 2 else -1.5) * (i / (n - 1)) for i in range(n)]),
        "root_y": keys([3.0 * smooth(i / (n - 1)) for i in range(n)]),
        "body": keys([(-2.0 if i % 2 else 2.0) * (i / (n - 1)) for i in range(n)]),
        "fuse": keys([-6.0 + 3.0 * (i % 2) for i in range(n)]),
        "mandible_near": keys([24.0 * min(1.0, i / 3) for i in range(n)]),
        "mandible_far": keys([-18.0 * min(1.0, i / 3) for i in range(n)]),
        "shell_0": on(0), "shell_1": on(1), "shell_2": on(2),
        "wick_0": on(0), "wick_1": on(1), "wick_2": on(2),
        "spark_0a": keys([1.0 if st == 0 and i % 2 == 0 else 0.0 for i, st in enumerate(stage)]),
        "spark_0b": keys([1.0 if st == 0 and i % 2 == 1 else 0.0 for i, st in enumerate(stage)]),
        "spark_1a": on(1), "spark_2a": on(2),
        # the legs brace outward as it swells
        **m.per_frame_feet(n, lambda leg, i: (5.0 if leg.endswith(("front", "fmid")) else -5.0) * smooth(i / (n - 1))),
    }}
    return clips


def build(name: str) -> dict:
    m = Mite(name)
    cast = m.cast
    bones = []
    world_rest: Dict[str, float] = {}
    for bone, (parent, x, y) in cast.joints.items():
        leg = next((lg for lg in m.legs if bone in (f"{lg}_thigh", f"{lg}_shin")), None)
        if leg is not None:
            _parent, hip, knee, foot = m.legs[leg]
            a_thigh = math.degrees(math.atan2(knee[1] - hip[1], knee[0] - hip[0]))
            a_shin = math.degrees(math.atan2(foot[1] - knee[1], foot[0] - knee[0]))
            if bone.endswith("_thigh"):
                _p, ppx, ppy = cast.joints[parent]
                offset = [(x - ppx) * SCALE, (y - ppy) * SCALE]
                rest, length = a_thigh, math.dist(hip, knee) * SCALE
                world_rest[bone] = a_thigh
            else:
                offset = [math.dist(hip, knee) * SCALE, 0.0]
                rest, length = a_shin - a_thigh, math.dist(knee, foot) * SCALE
                world_rest[bone] = a_shin
        else:
            if parent:
                _p, ppx, ppy = cast.joints[parent]
                offset = [(x - ppx) * SCALE, (y - ppy) * SCALE]
            else:
                offset = list(px((x, y)))
            rest, length = 0.0, 0.0
        bones.append({"name": bone, "parent": parent or None, "offset": [round(v, 5) for v in offset],
                      "length": round(length, 5), "rest_angle": round(rest, 5)})
    parts = []
    for group, _label, part, bone, z, _items, channel, on in cast.parts:
        _p, x, y = cast.joints[bone]
        entry = {"name": part, "bone": bone, "z": z, "kind": "sprite", "include": [group], "pivot": [x, y],
                 "rest_angle": round(world_rest.get(bone, 0.0), 5)}
        if channel:
            entry["opacity_channel"] = channel
            entry["opacity_default"] = 1 if on else 0
        parts.append(entry)
    ik_chains = []
    for leg, (_parent, hip, knee, foot) in m.legs.items():
        side = (foot[0] - hip[0]) * (knee[1] - hip[1]) - (foot[1] - hip[1]) * (knee[0] - hip[0])
        rx, ry = m.rest[leg]
        ik_chains.append({"upper": f"{leg}_thigh", "lower": f"{leg}_shin", "channel_prefix": f"{leg}_foot",
                          "rest_x": round(rx, 5), "rest_y": round(ry, 5), "bend": 1 if side < 0 else -1})
    clips = dividing_clips(m) if name.startswith("dividing") else exploding_clips(m)
    return {
        "name": name,
        "frame": FRAME,
        "svg_source": {"path": f"../../../../data/characters/{name}/{name}_side.svg", "view": art.CAST_VIEW[name], "ref_dpi": 25.4, "scale": SCALE},
        "sprite_tuning": {"collision_scale": 1.0, "frame_sample_inset": 1},
        "palette": {},
        "bones": bones,
        "parts": parts,
        "ik_legs": [],
        "ik_chains": ik_chains,
        "clips": clips,
    }


def main() -> None:
    for name in art.CAST_NAMES:
        out = rig_path(name)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(build(name), indent=2) + "\n", encoding="utf8")
        tmp.replace(out)
        print(f"wrote {out.relative_to(ROOT)}")
    for changed in install_repo_metadata(ROOT):
        print(f"catalog {Path(changed).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
