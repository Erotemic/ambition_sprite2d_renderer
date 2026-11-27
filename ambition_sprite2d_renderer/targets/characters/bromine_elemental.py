"""Draw a pool of red liquid with a mantle of heavy vapor."""
from math import cos, pi, sin, tau
from pathlib import Path

from ._clockwork_enemy_art import Canvas, phase, track
from ...authoring.sheet_build import build_sheet
from ...core.measure import body_metrics_for_box

TARGET_NAME = "bromine_elemental"
FRAME_SIZE = (224, 144)
WINDUP, ACTIVE, RECOVERY = 0.62, 0.22, 0.74
TOTAL = WINDUP + ACTIVE + RECOVERY
ROWS = [
    ("idle", 12, 86), ("walk", 12, 80), ("run", 12, 66), ("notice", 7, 65),
    ("windup", 16, 39), ("attack_side", 40, 39), ("hit", 6, 64),
    ("death", 16, 64), ("death_idle", 1, 240),
]
LOOPS = {"idle", "walk", "run", "death_idle"}


def render_frame(anim, index, count):
    c = Canvas(FRAME_SIZE, super_scale=2)
    t = phase(index, count, anim in LOOPS)
    start, stop = WINDUP / TOTAL, (WINDUP + ACTIVE) / TOTAL
    ready = t if anim == "windup" else 0
    sweep = 0
    if anim == "attack_side":
        ready = track(t, [(0, 0), (start, 1), (start + 0.04, 0), (1, 0)])
        sweep = track(t, [(0, 0), (start, 0), (start + 0.04, 1), (stop, 0.87), (stop + 0.28, 0), (1, 0)])
    if anim == "notice":
        ready = 0.46 * t
    hurt = sin(pi * t) if anim == "hit" else 0
    death = 1 if anim == "death_idle" else (t if anim == "death" else 0)
    swell = 2 * sin(tau * t) + 23 * ready - 39 * death
    x = 87 - 16 * ready + 25 * sweep - 8 * hurt

    for j in range(7):
        drift = (t + j * 0.143) % 1
        px = x + 18 - j * (9 - 3 * ready) - 20 * drift + 26 * sweep
        py = 105 - (5 + 7 * (j % 3)) * sin(pi * drift) - 1.3 * ready * j
        c.oval((px, py), (14 + 15 * drift) * (1 - death * 0.55),
               5 + 5 * drift + 12 * ready, (102 + j * 7, 38 + j * 4, 40 + j * 3, round((1 - drift) * 168)),
               None, angle=8 + 27 * ready)
    waterline = 118
    for j in range(3):
        w = 44 + 11 * j + 31 * sweep + 12 * death
        c.oval((x + j * 4, waterline - 2 * j), w, 7 - j, ((70, 31, 43), (108, 41, 42), (146, 63, 47))[j],
               None, angle=1)
    if death < 0.94:
        top = 74 - swell
        shape = [(x - 40, 112), (x - 29, top + 15), (x - 14, top + 6), (x + 5, top),
                 (x + 25, top + 9), (x + 27 + 41 * sweep, top + 15 + 14 * sweep),
                 (x + 35 + 48 * sweep, 109), (x + 12, 119), (x - 25, 118)]
        c.poly(shape, (135, 49, 44), (62, 31, 42), 2.5)
        c.line(shape[1:6], (205, 102, 67), 2)
        c.line([(x + 2, top + 17), (x + 14, top + 20), (x + 25 + 30 * sweep, top + 18 + 13 * sweep)],
               (246, 155, 90), 2.4 if ready > 0.4 else 1.2)
        c.oval((x + 18 + 7 * sweep, top + 27), 11, 4.0 + ready, (75, 35, 44), None, angle=-8)
        c.oval((x + 21 + 7 * sweep, top + 26), 5, 1.9, (255, 210, 133), None)
        for j in range(5):
            rise = (t + 0.23 * j) % 1
            c.disk((x - 11 - 8 * j + 3 * cos(tau * rise), top + 33 - rise * (13 + 9 * ready)),
                   1.2 + j % 2 * 0.7, (225, 127, 78, round(185 * (1 - rise))), None)
    return c.finish()


TRAITS = ["enemy", "science", "elemental", "chemical_element", "bromine"]
ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Bromine Elemental"},
    "body": {"body_plan": "Slug", "body_kind": "Low", "mass_class": "Light", "locomotion_hint": "Slither", "traits": TRAITS},
    "capabilities": {"traversal": {"walk": True}},
    "actions": {"default_preset": "bromine_elemental_sweep"},
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
        "action.melee.primary": {"animation": "attack_side", "events": [
            {"t": WINDUP / TOTAL, "event": "hitbox_active_start", "source": "bromine_elemental.sweep"},
            {"t": (WINDUP + ACTIVE) / TOTAL, "event": "hitbox_active_end", "source": "bromine_elemental.sweep"},
        ]},
    },
    "tags": TRAITS,
}


def render(out_dir: str | Path, **_opts):
    outputs = build_sheet(target=TARGET_NAME, rows=ROWS, render_fn=render_frame, out_dir=Path(out_dir),
                          frame_size=FRAME_SIZE, auto_crop=False, actor_metadata=ACTOR_METADATA,
                          animation_key_map={name: name for name, _, _ in ROWS},
                          body_metrics_fn=lambda w, h: body_metrics_for_box((42, 71, 134, 119), w, h),
                          sits_on_ground=True)
    return [outputs[key] for key in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")]
