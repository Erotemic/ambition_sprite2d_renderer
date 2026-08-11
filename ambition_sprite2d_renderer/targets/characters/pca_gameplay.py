"""Sprite-side gameplay geometry for the Perfect Cellular Automaton fighter.

The PCA rig is authored in logical 128x192 coordinates and published at 3x.
This module keeps all design geometry in that logical rig space, then applies
publish padding/render scale at the boundary.  The source SVG and rig artwork
remain pure presentation authority; skirt/helmet/shoulder silhouette never
silently inflates combat geometry.
"""

from __future__ import annotations

from typing import Iterable, Sequence

RIG_SIZE = (128, 192)
RENDER_SCALE = 3
PADDING = 18


def _px(value: float) -> int:
    return int(round((float(value) + PADDING) * RENDER_SCALE))


def _len(value: float) -> int:
    return int(round(float(value) * RENDER_SCALE))


def _rect(name: str, x: float, y: float, w: float, h: float) -> dict:
    return {
        "name": name,
        "x": _px(x),
        "y": _px(y),
        "w": _len(w),
        "h": _len(h),
    }


def _bbox(x: float, y: float, w: float, h: float) -> dict:
    return {"x": _px(x), "y": _px(y), "w": _len(w), "h": _len(h)}


def _poly(points: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
    return [
        (
            float(_px(x)),
            float(_px(y)),
        )
        for x, y in points
    ]


def _box_attack(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    active: Sequence[int],
    poly: Sequence[tuple[float, float]] | None = None,
) -> dict:
    out = {"bbox": _bbox(x, y, w, h), "active_frames": list(active)}
    if poly:
        out["poly"] = _poly(poly)
    return out


def _diamond_attack(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    *,
    active: Sequence[int],
) -> dict:
    return _box_attack(
        cx - rx,
        cy - ry,
        2 * rx,
        2 * ry,
        active=active,
        poly=[(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)],
    )


def _lens_attack(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    active: Sequence[int],
) -> dict:
    cy = y + h / 2.0
    return _box_attack(
        x,
        y,
        w,
        h,
        active=active,
        poly=[
            (x, cy),
            (x + w * 0.24, y),
            (x + w * 0.74, y),
            (x + w, cy),
            (x + w * 0.74, y + h),
            (x + w * 0.24, y + h),
        ],
    )


def _dual_floor_burst(*, active: Sequence[int]) -> dict:
    left = _lens_attack(6, 126, 54, 28, active=active)
    right = _lens_attack(68, 126, 54, 28, active=active)
    return {
        "bbox": _bbox(6, 126, 116, 28),
        "parts": [
            {"name": "rear_wave", **left["bbox"], "poly": left["poly"]},
            {"name": "front_wave", **right["bbox"], "poly": right["poly"]},
        ],
        "active_frames": list(active),
    }


# Body geometry intentionally omits the large shoulder shells and helmet horns.
# Those are readable silhouette, not additional damageable anatomy.
STANDING_HURTBOX = [
    _rect("head", 49, 35, 31, 34),
    _rect("upper_torso", 43, 68, 43, 38),
    _rect("pelvis", 46, 105, 36, 26),
    _rect("rear_arm", 75, 75, 18, 58),
    _rect("front_arm", 35, 75, 18, 58),
    _rect("rear_leg", 63, 128, 19, 47),
    _rect("front_leg", 44, 128, 19, 47),
]

CROUCH_HURTBOX = [
    _rect("head", 48, 50, 32, 31),
    _rect("upper_torso", 41, 80, 46, 34),
    _rect("pelvis", 43, 112, 42, 24),
    _rect("rear_arm", 74, 82, 18, 48),
    _rect("front_arm", 34, 82, 18, 48),
    _rect("rear_leg", 62, 135, 21, 34),
    _rect("front_leg", 42, 135, 21, 34),
]

AIR_HURTBOX = [
    _rect("head", 49, 32, 31, 34),
    _rect("upper_torso", 43, 65, 43, 38),
    _rect("pelvis", 46, 102, 36, 26),
    _rect("rear_arm", 75, 70, 18, 55),
    _rect("front_arm", 35, 70, 18, 55),
    _rect("rear_leg", 63, 124, 19, 43),
    _rect("front_leg", 44, 124, 19, 43),
]

PRONE_HURTBOX = [
    _rect("head", 86, 128, 27, 25),
    _rect("upper_torso", 57, 128, 34, 28),
    _rect("pelvis", 34, 133, 26, 24),
    _rect("rear_leg", 12, 139, 26, 20),
    _rect("front_leg", 4, 157, 30, 18),
]

LEDGE_HURTBOX = [
    _rect("head", 51, 49, 30, 32),
    _rect("upper_torso", 46, 79, 40, 34),
    _rect("pelvis", 48, 112, 34, 25),
    _rect("rear_leg", 61, 137, 18, 36),
    _rect("front_leg", 44, 137, 18, 36),
]

BURIED_HURTBOX = [
    _rect("head", 49, 81, 31, 31),
    _rect("upper_torso", 43, 111, 43, 29),
    _rect("pelvis", 46, 139, 36, 18),
]

SHIELDED_HURTBOX = [
    _rect("head", 50, 39, 30, 32),
    _rect("upper_torso", 42, 70, 45, 39),
    _rect("pelvis", 45, 108, 39, 26),
    _rect("rear_leg", 63, 133, 19, 42),
    _rect("front_leg", 44, 133, 19, 42),
]

_CROUCH = {"crouch_start", "crouch", "crouch_walk", "crouch_end"}
_AIR = {
    "jump", "double_jump", "fall", "fall_special", "tumble", "air_dodge",
    "air_neutral", "air_forward", "air_back", "air_up", "air_down", "air_land",
    "fly", "hover", "float_glide", "wall_jump", "ledge_jump",
}
_PRONE = {
    "knockdown", "prone", "prone_damage", "getup_attack", "getup_roll",
    "trip_fall", "trip_idle", "trip_attack", "trip_roll", "sleep", "death",
    "shield_break_fall", "shield_break_collapse",
}
_LEDGE = {
    "ledge_catch", "ledge_grab", "ledge_climb", "ledge_getup", "ledge_attack",
    "ledge_roll", "ledge_drop", "ledge_getup_attack", "wall_grab", "ladder_climb",
}
_BURIED = {"bury_start", "buried", "bury_escape"}
_SHIELDED = {
    "block", "shield_raise", "shield_release", "parry", "shield_hit", "spot_dodge",
    "roll", "roll_back", "shield_break_launch", "shield_break_recover",
}


def hurtbox_parts_for_rows(rows: Iterable[tuple[str, int, int]]) -> dict:
    out = {}
    for name, _frames, _duration in rows:
        if name in _BURIED:
            parts = BURIED_HURTBOX
        elif name in _CROUCH:
            parts = CROUCH_HURTBOX
        elif name in _AIR:
            parts = AIR_HURTBOX
        elif name in _PRONE:
            parts = PRONE_HURTBOX
        elif name in _LEDGE:
            parts = LEDGE_HURTBOX
        elif name in _SHIELDED:
            parts = SHIELDED_HURTBOX
        else:
            parts = STANDING_HURTBOX
        out[name] = {"parts": [dict(part) for part in parts]}
    return out


def body_metrics(fw: int, fh: int) -> dict:
    body = _bbox(41, 34, 46, 142)
    feet_x = float(_px(64))
    feet_y = float(_px(176))
    return {
        "body_pixel_bbox": body,
        "feet_pixel": {"x": feet_x, "y": feet_y},
        "feet_anchor_norm": {
            "x": round(feet_x / fw - 0.5, 6),
            "y": round(0.5 - feet_y / fh, 6),
        },
    }


ATTACK_HITBOXES = {
    "jab": _lens_attack(68, 78, 34, 28, active=[2]),
    "punch": _lens_attack(68, 72, 44, 36, active=[2, 3]),
    "slash": _lens_attack(64, 58, 61, 59, active=[2, 3, 4]),
    "dash_attack": _lens_attack(70, 74, 53, 44, active=[2, 3, 4]),
    "attack_side": _lens_attack(68, 70, 54, 42, active=[2, 3]),
    "attack_up": _diamond_attack(64, 61, 26, 48, active=[2, 3]),
    "attack_down": _lens_attack(61, 118, 61, 32, active=[2, 3]),
    "smash_forward": _lens_attack(68, 55, 60, 64, active=[3, 4, 5]),
    "smash_up": _diamond_attack(64, 58, 31, 60, active=[3, 4, 5]),
    "smash_down": _dual_floor_burst(active=[3, 4, 5]),
    "air_neutral": _diamond_attack(64, 91, 43, 49, active=[1, 2, 3, 4]),
    "air_forward": _lens_attack(69, 70, 55, 44, active=[2, 3]),
    "air_back": _lens_attack(5, 72, 55, 44, active=[2, 3]),
    "air_up": _diamond_attack(64, 54, 28, 50, active=[2, 3]),
    "air_down": _diamond_attack(64, 132, 27, 47, active=[2, 3, 4]),
    "shoot": _lens_attack(73, 67, 66, 23, active=[2, 3, 4]),
    "special": _box_attack(
        65,
        48,
        72,
        79,
        active=[3, 4, 5, 6],
        poly=[(65, 87), (128, 48), (137, 87), (128, 127)],
    ),
    "charge": _diamond_attack(64, 94, 41, 47, active=[2, 3, 4, 5]),
    "fly": _diamond_attack(64, 91, 27, 73, active=[1, 2, 3, 4, 5]),
    "final_smash": _diamond_attack(64, 91, 61, 80, active=[4, 5, 6, 7, 8, 9]),
    "parry": _diamond_attack(64, 88, 35, 49, active=[2, 3]),
    "grab": _lens_attack(69, 78, 31, 31, active=[2, 3]),
    "pummel": _diamond_attack(69, 90, 17, 19, active=[2]),
    "throw_forward": _lens_attack(75, 68, 53, 47, active=[4, 5]),
    "throw_back": _lens_attack(0, 72, 54, 45, active=[4, 5]),
    "throw_up": _diamond_attack(64, 58, 29, 58, active=[4, 5]),
    "throw_down": _diamond_attack(64, 132, 31, 43, active=[4, 5]),
    "getup_attack": _diamond_attack(64, 126, 55, 31, active=[3, 4]),
    "ledge_attack": _lens_attack(68, 86, 52, 37, active=[3, 4]),
    "ledge_getup_attack": _lens_attack(67, 89, 53, 38, active=[3, 4]),
    "item_swing": _lens_attack(68, 64, 60, 47, active=[2, 3, 4]),
}


PCA_MOVE_BLUEPRINT = {
    "jab": {
        "title": "Single-Tick Jab",
        "summary": "A compact one-generation strike: quick, exact, and intentionally unornamented.",
    },
    "smash_forward": {
        "title": "Deterministic Impact",
        "summary": "A committed forward smash that resolves a dense cell front at the moment of impact.",
    },
    "smash_up": {
        "title": "Branching Future",
        "summary": "An upward smash whose cells branch into the next deterministic generations above him.",
    },
    "smash_down": {
        "title": "Boundary Condition",
        "summary": "Two ground waves propagate away from the same initial condition on opposite sides.",
    },
    "shoot": {
        "title": "Generation Ray",
        "summary": "Neutral special emits a beam made from consecutive cells of one deterministic rule.",
    },
    "special": {
        "title": "Causal Cone",
        "summary": "Side special projects a spacetime cone of successive cellular-automaton generations.",
    },
    "fly": {
        "title": "Glider Ascent",
        "summary": "Up special rides a stream of stable glider motifs upward rather than generic thrust.",
    },
    "charge": {
        "title": "Fixed Point",
        "summary": "Down special contracts a local lattice into a pulsing stable attractor around his core.",
    },
    "final_smash": {
        "title": "All Future States",
        "summary": "The local frame becomes a deterministic spacetime lattice whose generations sweep outward from PCA.",
    },
}


__all__ = [
    "ATTACK_HITBOXES",
    "PADDING",
    "PCA_MOVE_BLUEPRINT",
    "RENDER_SCALE",
    "RIG_SIZE",
    "body_metrics",
    "hurtbox_parts_for_rows",
]
