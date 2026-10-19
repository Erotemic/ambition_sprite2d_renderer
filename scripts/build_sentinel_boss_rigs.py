#!/usr/bin/env python3
"""Build the three sentinel bosses' rig documents.

    uv run python scripts/svg_art/sentinel_boss_art.py   # the drawings, once
    uv run python scripts/build_sentinel_boss_rigs.py

The drawings say where each part turns (``JOINTS`` in the art script). This
script makes the skeleton from those joints, binds each part layer to its
bone, and authors the rows. It never draws. A channel is the turn of a bone
from the drawing, in degrees (positive clockwise on the screen: an arm
pointing forward swings down, the body leans forward).

The three share their skeleton and their rows, the seven the generic boss has
always had: ``rest``, ``floor_slam``, ``side_sweep``, ``spike_halo``,
``dash_echo``, ``hit``, ``death``. Only the halo moves differently: the
Warden's gear turns, the Gradient Sentinel's crown of spikes sways.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.devtools.svg_rig_tool import install_repo_metadata  # noqa: E402

_spec = importlib.util.spec_from_file_location("sentinel_boss_art", ROOT / "scripts" / "svg_art" / "sentinel_boss_art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

RIGGED = ROOT / "ambition_sprite2d_renderer" / "targets" / "characters" / "rigged"

#: Frame pixels for each SVG unit.
SCALE = 0.5
#: The SVG point placed at the frame's ``(center_x, ground_y)``: the middle of
#: the cloak, and the hem's line. He floats: nothing stands on that line.
CENTER_X, GROUND_Y = 300.0, 470.0
FRAME = {"width": 288, "height": 272, "center_x": 144, "ground_y": 236, "ankle_h": 0, "supersample": 3, "render_scale": 1, "trim": False}

JOLT = "(1-t)*(1-t)"
#: How far each one falls in ``death`` (frame px), to lie on the frame's floor:
#: the Gradient Sentinel's long hem reaches lowest.
DEATH_DROP = {"gradient_sentinel": 40, "clockwork_warden": 52, "hooded_sentinel": 52}


def expr(text: str) -> dict:
    return {"expr": text}


#: A key: 0 to 1 between ``a`` and ``b`` of the row, eased, held after.
def ramp(a: float, b: float) -> str:
    return f"(lambda u: u*u*(3-2*u))(max(0.0, min(1.0, (t-{a})/{b - a})))"


def eyes(dark: str = "False") -> dict:
    return {"eye_lit": expr(f"0 if ({dark}) else 1"), "eye_dark": expr(f"1 if ({dark}) else 0")}


def clips(look: str) -> dict:
    kind = art.LOOKS[look]["kind"]
    # The gear turns a spoke a loop (it has six); the spike crown only sways.
    rest_halo = "60*t" if kind == "clock" else "4*sin(tau*t)"
    cast_halo = f"120*{ramp(0.0, 1.0)}"
    SLAM_Y = f"-14*{ramp(0.0, 0.35)} + 30*{ramp(0.35, 0.5)} - 16*{ramp(0.7, 1.0)}"
    return {
        # He hovers: a slow bob, the arms drifting, the pendulum swinging.
        "rest": {
            "loop": True, "frames": 8, "duration_ms": 120,
            "channels": {
                "root_y": expr("4*sin(tau*t)"),
                "body": expr("2*sin(tau*t)"),
                "head": expr("-3*sin(tau*t+0.6)"),
                "halo": expr(rest_halo),
                "pendulum": expr("14*sin(tau*t)"),
                "near_arm_u": expr("6*sin(tau*t)"), "near_arm_l": expr("-8*sin(tau*t+1)"), "near_hand": expr("10*sin(tau*t+2)"),
                "far_arm_u": expr("-6*sin(tau*t)"), "far_arm_l": expr("8*sin(tau*t+1)"), "far_hand": expr("-10*sin(tau*t+2)"),
            },
        },
        # Up, both arms high over his head, then down on the floor with them.
        "floor_slam": {
            "loop": False, "frames": 7, "duration_ms": 82,
            "channels": {
                "root_y": expr(SLAM_Y),
                # the shock stays on the floor while he drops to it
                "bone.floor.y": expr(f"-({SLAM_Y})"),
                "body": expr(f"-6*{ramp(0.0, 0.35)} + 16*{ramp(0.35, 0.5)} - 10*{ramp(0.7, 1.0)}"),
                "head": expr(f"-6*{ramp(0.0, 0.35)} + 10*{ramp(0.35, 0.5)} - 4*{ramp(0.7, 1.0)}"),
                "pendulum": expr(f"20*{ramp(0.0, 0.35)} - 40*{ramp(0.35, 0.5)} + 20*{ramp(0.7, 1.0)}"),
                "near_arm_u": expr(f"-75*{ramp(0.0, 0.35)} + 115*{ramp(0.35, 0.5)} - 40*{ramp(0.7, 1.0)}"),
                "near_arm_l": expr(f"30*{ramp(0.0, 0.35)} + 20*{ramp(0.35, 0.5)} - 50*{ramp(0.7, 1.0)}"),
                "far_arm_u": expr(f"75*{ramp(0.0, 0.35)} - 115*{ramp(0.35, 0.5)} + 40*{ramp(0.7, 1.0)}"),
                "far_arm_l": expr(f"-30*{ramp(0.0, 0.35)} - 20*{ramp(0.35, 0.5)} + 50*{ramp(0.7, 1.0)}"),
                "fx_slam": expr("1 if 0.45 < t < 0.8 else 0"),
            },
        },
        # Arms drawn in, then flung out wide to both sides at once.
        "side_sweep": {
            "loop": False, "frames": 7, "duration_ms": 72,
            "channels": {
                "root_x": expr(f"-4*{ramp(0.0, 0.3)} + 8*{ramp(0.3, 0.5)} - 4*{ramp(0.75, 1.0)}"),
                "body": expr(f"-5*{ramp(0.0, 0.3)} + 12*{ramp(0.3, 0.5)} - 7*{ramp(0.75, 1.0)}"),
                "head": expr(f"4*{ramp(0.0, 0.3)} - 8*{ramp(0.3, 0.5)} + 4*{ramp(0.75, 1.0)}"),
                "pendulum": expr(f"-14*{ramp(0.0, 0.3)} + 28*{ramp(0.3, 0.5)} - 14*{ramp(0.75, 1.0)}"),
                "near_arm_u": expr(f"50*{ramp(0.0, 0.3)} - 78*{ramp(0.3, 0.5)} + 28*{ramp(0.75, 1.0)}"),
                "near_arm_l": expr(f"-110*{ramp(0.0, 0.3)} + 160*{ramp(0.3, 0.5)} - 50*{ramp(0.75, 1.0)}"),
                "near_hand": expr(f"30*{ramp(0.0, 0.3)} - 40*{ramp(0.3, 0.5)} + 10*{ramp(0.75, 1.0)}"),
                "far_arm_u": expr(f"-50*{ramp(0.0, 0.3)} + 73*{ramp(0.3, 0.5)} - 23*{ramp(0.75, 1.0)}"),
                "far_arm_l": expr(f"110*{ramp(0.0, 0.3)} - 159*{ramp(0.3, 0.5)} + 49*{ramp(0.75, 1.0)}"),
                "far_hand": expr(f"-30*{ramp(0.0, 0.3)} + 40*{ramp(0.3, 0.5)} - 10*{ramp(0.75, 1.0)}"),
            },
        },
        # He rises, arms spread high, the halo spinning, and throws the ring out.
        "spike_halo": {
            "loop": False, "frames": 8, "duration_ms": 92,
            "channels": {
                "root_y": expr(f"-12*{ramp(0.0, 0.4)} + 12*{ramp(0.8, 1.0)}"),
                "body": expr(f"-4*{ramp(0.0, 0.4)} + 4*{ramp(0.8, 1.0)}"),
                "head": expr(f"-8*{ramp(0.0, 0.4)} + 8*{ramp(0.8, 1.0)}"),
                "halo": expr(cast_halo),
                "pendulum": expr("10*sin(tau*t)"),
                "near_arm_u": expr(f"-60*{ramp(0.0, 0.4)} + 60*{ramp(0.8, 1.0)}"),
                "near_arm_l": expr(f"20*{ramp(0.0, 0.4)} - 20*{ramp(0.8, 1.0)}"),
                "near_hand": expr(f"-20*{ramp(0.0, 0.4)} + 20*{ramp(0.8, 1.0)}"),
                "far_arm_u": expr(f"60*{ramp(0.0, 0.4)} - 60*{ramp(0.8, 1.0)}"),
                "far_arm_l": expr(f"-20*{ramp(0.0, 0.4)} + 20*{ramp(0.8, 1.0)}"),
                "far_hand": expr(f"20*{ramp(0.0, 0.4)} - 20*{ramp(0.8, 1.0)}"),
                "fx_ring": expr("1 if 0.45 < t < 0.9 else 0"),
            },
        },
        # A lunge forward, leaning into it, the arms trailing, an echo behind.
        "dash_echo": {
            "loop": False, "frames": 7, "duration_ms": 62,
            "channels": {
                "root_x": expr(f"16*{ramp(0.0, 0.35)} - 16*{ramp(0.8, 1.0)}"),
                "body": expr(f"26*{ramp(0.0, 0.35)} - 26*{ramp(0.8, 1.0)}"),
                "head": expr(f"-14*{ramp(0.0, 0.35)} + 14*{ramp(0.8, 1.0)}"),
                "pendulum": expr(f"-40*{ramp(0.0, 0.35)} + 40*{ramp(0.8, 1.0)}"),
                "near_arm_u": expr(f"70*{ramp(0.0, 0.35)} - 70*{ramp(0.8, 1.0)}"),
                "near_arm_l": expr(f"30*{ramp(0.0, 0.35)} - 30*{ramp(0.8, 1.0)}"),
                "far_arm_u": expr(f"-30*{ramp(0.0, 0.35)} + 30*{ramp(0.8, 1.0)}"),
                "far_arm_l": expr(f"-20*{ramp(0.0, 0.35)} + 20*{ramp(0.8, 1.0)}"),
                "fx_dash": expr("1 if 0.2 < t < 0.85 else 0"),
            },
        },
        # A blow: he rocks back, arms flung up.
        "hit": {
            "loop": False, "frames": 5, "duration_ms": 90,
            "channels": {
                "root_x": expr(f"-6*{JOLT}"),
                "body": expr(f"-14*{JOLT}"),
                "head": expr(f"-12*{JOLT}"),
                "pendulum": expr(f"24*{JOLT}"),
                "near_arm_u": expr(f"-40*{JOLT}"), "near_arm_l": expr(f"-20*{JOLT}"),
                "far_arm_u": expr(f"40*{JOLT}"), "far_arm_l": expr(f"20*{JOLT}"),
            },
        },
        # A last jolt, the eyes go out, and he tips back and falls to the floor.
        "death": {
            "loop": False, "frames": 8, "duration_ms": 110,
            "channels": {
                # he rises as he tips back, so the swinging hem stays in the frame, then drops
                "root_y": expr(f"-10*{ramp(0.0, 0.3)} - 24*{ramp(0.3, 0.6)} + {DEATH_DROP[look] + 24}*{ramp(0.6, 0.95)}"),
                "root_x": expr(f"14*{ramp(0.3, 0.9)}"),
                "body": expr(f"-8*{ramp(0.0, 0.3)} - 87*{ramp(0.3, 0.75)}"),
                "head": expr(f"-20*{ramp(0.0, 0.3)} + 30*{ramp(0.3, 0.9)}"),
                "pendulum": expr(f"60*{ramp(0.3, 0.9)}"),
                "near_arm_u": expr(f"-50*{ramp(0.0, 0.3)} + 90*{ramp(0.3, 0.9)}"),
                "near_arm_l": expr(f"30*{ramp(0.0, 0.3)} + 10*{ramp(0.3, 0.9)}"),
                "far_arm_u": expr(f"50*{ramp(0.0, 0.3)} - 90*{ramp(0.3, 0.9)}"),
                "far_arm_l": expr(f"-30*{ramp(0.0, 0.3)} - 10*{ramp(0.3, 0.9)}"),
                **eyes(dark="t >= 0.5"),
            },
        },
    }


def build(look: str) -> dict:
    target = art.TARGETS[look]
    joints = art.JOINTS
    bones = []
    for name, (parent, x, y) in joints.items():
        if parent:
            _, px, py = joints[parent]
            offset = [round((x - px) * SCALE, 4), round((y - py) * SCALE, 4)]
        else:
            offset = [round((x - CENTER_X) * SCALE, 4), round((y - GROUND_Y) * SCALE, 4)]
        bones.append({"name": name, "parent": parent or None, "offset": offset, "length": 0, "rest_angle": 0})
    parts = []
    for group, _label, part, bone, z, channel in art.LAYERS:
        _, x, y = joints[bone]
        entry = {"name": part, "bone": bone, "z": z, "kind": "sprite", "include": [group], "pivot": [x, y], "rest_angle": 0}
        if channel:
            entry["opacity_channel"] = channel
            entry["opacity_default"] = 1 if channel == "eye_lit" else 0
        parts.append(entry)
    return {
        "name": target,
        "frame": FRAME,
        "svg_source": {"path": f"../../../../data/characters/{target}/{target}.svg", "view": art.view(look), "ref_dpi": 25.4, "scale": SCALE},
        "sprite_tuning": {"collision_scale": 1.6, "frame_sample_inset": 1},
        "palette": {},
        "bones": bones,
        "parts": parts,
        "ik_legs": [],
        "ik_chains": [],
        "clips": clips(look),
    }


def main() -> None:
    for look, target in art.TARGETS.items():
        out = RIGGED / target / f"{target}.rig.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(build(look), indent=2) + "\n", encoding="utf8")
        tmp.replace(out)
        print(f"wrote {out.relative_to(ROOT)}")
    for changed in install_repo_metadata(ROOT):
        print(f"catalog {Path(changed).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
