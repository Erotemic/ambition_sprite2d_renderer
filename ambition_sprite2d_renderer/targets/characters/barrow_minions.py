"""Draw two residents of the Barrow King's burial vaults."""

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
LINEN = "#b7a789"
LINEN_DARK = "#786956"
SKIN = "#82998a"
SKIN_LIGHT = "#b2be9e"
LIGHT = "#c7f2bb"


def beats(anim, frame, frames):
    t = phase(frame, frames, anim in LOOPS)
    stride = math.sin(t * math.tau) if anim in {"walk", "run"} else 0
    strike = track(t, [(0, 0), (0.12, 1), (0.22, 1), (0.52, 0), (1, 0)]) if anim == "attack_side" else 0
    down = track(t, [(0, 0), (0.4, 0.24), (1, 1)]) if anim == "death" else float(anim == "death_idle")
    tell = 1 if anim == "windup" else math.sin(t * math.pi) if anim == "notice" else 0
    return stride, strike, down, tell


def shambler(canvas, anim, frame, frames):
    stride, strike, down, tell = beats(anim, frame, frames)
    lean = 16 * strike + 24 * down - 7 * tell
    waist = (89 + 10 * down, 91 + 25 * down + abs(stride) * 2)
    shoulder = add(waist, (6 + lean, -33 * (1 - down)))
    head = add(shoulder, (6 + 8 * down, -15 * (1 - down)))
    feet = [(82 - 19 * stride, GROUND - max(0, stride) * 7),
            (99 + 19 * stride, GROUND - max(0, -stride) * 7)]
    for i, foot in enumerate(feet):
        hip = add(waist, ((i - 0.5) * 14, 2))
        knee = ((hip[0] + foot[0]) * 0.5 + 5, (hip[1] + foot[1]) * 0.5)
        canvas.tube(hip, knee, 6, LINEN_DARK, LINEN)
        canvas.tube(knee, foot, 4, SKIN, SKIN_LIGHT)
        canvas.box(add(foot, (4, -1)), 9, 4, LINEN_DARK)
    far_hand = add(shoulder, (16 + 21 * strike, 18 + 7 * stride))
    canvas.tube(shoulder, far_hand, 4, "#667c70")
    canvas.poly([add(shoulder, (-11, 0)), add(shoulder, (10, 1)), add(waist, (17, 8)),
                 add(waist, (5, 3)), add(waist, (-3, 10)), add(waist, (-14, 6))], LINEN)
    for y in (9, 16, 24):
        canvas.line([add(shoulder, (-10, y)), add(shoulder, (8, y + 4))], LINEN_DARK, 1.4)
    elbow = add(shoulder, (13 + 12 * strike, 21 - 13 * tell))
    hand = add(elbow, (15 + 18 * strike, 5 - 21 * tell))
    canvas.tube(shoulder, elbow, 5.5, LINEN, "#d2c39d")
    canvas.tube(elbow, hand, 4, SKIN, SKIN_LIGHT)
    for y in (-2, 1, 4):
        canvas.line([add(hand, (-2, y)), add(hand, (6, y + 1))], SKIN_LIGHT, 1.4)
    canvas.oval(head, 12, 14, SKIN)
    canvas.poly([add(head, (-13, -8)), add(head, (-7, -15)), add(head, (7, -15)),
                 add(head, (12, -8)), add(head, (-5, -3)), add(head, (-11, 6))], LINEN_DARK)
    canvas.line([add(head, (4, 6)), add(head, (11, 5))], "#39362d", 2.4)
    if not down:
        canvas.line([add(head, (3, -2)), add(head, (10, -3))], LIGHT, 2.0)


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
        "body": {"body_plan": "Human" if draw is shambler else "Prop", "body_kind": "Standard",
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
    "barrow_shambler": target("barrow_shambler", "Barrow Shambler", shambler, (72, 39, 113, 140), "barrow_shambler_swipe"),
    "barrow_toaster": target("barrow_toaster", "Haunted Toaster", toaster, (61, 70, 124, 139), "barrow_toaster_rush"),
}
