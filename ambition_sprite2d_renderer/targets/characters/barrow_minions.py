"""Draw the haunted toaster from the Barrows."""

from __future__ import annotations

import math
from pathlib import Path

from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box
from ._clockwork_enemy_art import Canvas, add, phase, track

ROWS = [
    ("idle", 8, 140), ("walk", 12, 100), ("run", 12, 84),
    ("notice", 6, 100), ("windup", 6, 110), ("attack_side", 13, 66),
    ("hit", 5, 90), ("death", 10, 100), ("death_idle", 4, 200),
]
LOOPS = {"idle", "walk", "run", "windup", "death_idle"}
FRAME = (192, 152)
GROUND = 134
LIGHT = "#b2be9e"
LIGHT = "#c7f2bb"


def beats(anim, frame, frames):
    t = phase(frame, frames, anim in LOOPS)
    stride = math.sin(t * math.tau) if anim in {"walk", "run"} else 0
    strike = track(t, [(0, 0), (0.12, 1), (0.22, 1), (0.52, 0), (1, 0)]) if anim == "attack_side" else 0
    down = track(t, [(0, 0), (0.4, 0.24), (1, 1)]) if anim == "death" else float(anim == "death_idle")
    tell = 1 if anim == "windup" else math.sin(t * math.pi) if anim == "notice" else 0
    return stride, strike, down, tell


def toaster(canvas, anim, frame, frames):
    stride, strike, down, tell = beats(anim, frame, frames)
    center = (92 + 17 * strike, 96 + abs(stride) * 5 + 17 * down)
    top = add(center, (0, -22))
    for i in range(3):
        hip = add(center, (-21 + i * 20, 14))
        foot = (hip[0] + 8 * stride * (-1 if i == 1 else 1), GROUND - 3)
        knee = (hip[0] + 10, foot[1] - 12)
        canvas.line([hip, knee, foot, add(foot, (6, 0))], "#807767", 3.7)
    canvas.line([add(center, (-27, 12)), (48, 128), (37, 130), (31, 122)], "#392e2a", 3.2)
    canvas.box(center, 31, 21, "#999a8e", r=8)
    canvas.box(add(center, (6, 0)), 25, 16, "#b8b5a7", r=6)
    canvas.line([add(top, (-21, 3)), add(top, (20, 3))], "#4b413b", 3.2)
    canvas.line([add(top, (-17, -1)), add(top, (17, -1))], "#ddd4bd", 1.6)
    canvas.disk(add(center, (22, 7)), 5, "#706250")
    canvas.line([add(center, (27, -3)), add(center, (36, -6))], "#743d32", 4)
    for xy, radius in [((-16, 8), 4.4), ((-20, 9), 2.8), ((8, 13), 3.2)]:
        canvas.disk(add(center, xy), radius, "#8a5e43", None)
    if not down:
        lift = 8 * tell + 19 * strike
        ghost = add(top, (2 + 12 * strike, -11 - lift))
        canvas.poly([add(top, (-13, 1)), add(ghost, (-12, 4)), add(ghost, (-8, -9)),
                     add(ghost, (6, -12)), add(ghost, (14, -4)), add(top, (16, 0))],
                    "#82a98b", "#59745d", 1.3)
        for x in (-5, 5):
            canvas.disk(add(ghost, (x, -2)), 2.5, LIGHT, None)


def target(name, title, draw, bounds, action):
    metadata = {
        "actor": {"character_id": name, "display_name": title},
        "body": {"body_plan": "Prop", "body_kind": "Standard",
                 "mass_class": "Medium", "locomotion_hint": "Walk"},
        "actions": {"default_preset": action},
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "locomotion.run": {"animation": "run", "events": []},
            "action.melee.primary": {"animation": "attack_side", "events": []},
            "combat.hurt": {"animation": "hit", "events": []},
            "combat.death": {"animation": "death", "events": []},
        },
        "tags": ["enemy", "undead", "barrow"],
    }

    def render(out_dir: str | Path, **opts):
        def frame(anim, index, total):
            canvas = Canvas(FRAME)
            draw(canvas, anim, index, total)
            return canvas.finish()

        outputs = build_sheet(
            target=name, rows=ROWS, render_fn=frame, out_dir=Path(out_dir), frame_size=FRAME,
            auto_crop=False, actor_metadata=metadata, sits_on_ground=True,
            body_metrics_fn=lambda w, h: body_metrics_for_box(bounds, w, h),
            animation_key_map={row: row for row, _, _ in ROWS},
        )
        return list(outputs.values())

    return {"render": render, "actor_metadata": metadata}


TARGETS = {
    "barrow_toaster": target("barrow_toaster", "Haunted Toaster", toaster, (61, 70, 124, 139), "barrow_toaster_rush"),
}
