"""Sprite-side gameplay geometry for the Noether fighter.

Frame dimensions and pose hurtboxes are derived from the rig document rather
than restated here. Authored strike volumes remain in normalized body space
because reach is gameplay intent, not a property the skeleton can infer. This
module publishes sheet geometry only; move timing/damage belong to the game, and
the SVG/rig remain presentation authority."""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Iterable, Sequence

TARGET_NAME = "noether"

#: Transparent margin, in rig units, that :mod:`noether` composes around the rig
#: frame (``RIG_RENDER_PADDING``). It lives here because every coordinate in this
#: module has to cross it, and it is imported there rather than restated — the
#: mistake this whole file is a correction for.
PADDING = 28

#: The rig this module's authored rectangles were written against, stated as the
#: one measurement both rigs can be compared by: the head bone's height above the
#: floor. The original was ``pelvis(20.5) + torso(4) + head(26)``.
#:
#:  it is a RATIO's denominator, not a coordinate. Nothing below is in this
#: space by the time it reaches the sheet.
AUTHORED_STATURE = 50.5


@lru_cache(maxsize=1)
def _rig():
    # Imported lazily: loading the document can rebuild a stale rig, and importing
    # a module should not do that.
    from ...authoring.canonical_scientist_rig import load_scientist_rig

    return load_scientist_rig(TARGET_NAME)


def _frame() -> dict:
    return _rig().frame


@lru_cache(maxsize=1)
def _stature() -> float:
    """Her head bone's height above the floor, in live rig units.

    The one number that makes an authored proportion portable across a rebuild.
    """
    world, _params = _rig().solve("idle", 0.0)
    return float(_frame()["ground_y"]) - float(world["head"].origin[1])


def _scale() -> float:
    """Authored body units → live rig units."""
    return _stature() / AUTHORED_STATURE


def _px(value: float) -> int:
    """A LIVE rig coordinate, in published pixels."""
    return int(round((float(value) + PADDING) * int(_frame().get("render_scale", 1))))


def _len(value: float) -> int:
    """A LIVE rig LENGTH, in published pixels — padding is an offset, not a size."""
    return int(round(float(value) * int(_frame().get("render_scale", 1))))


def _rect_px(x0: float, y0: float, x1: float, y1: float, name: str | None = None) -> dict:
    """A live-rig rectangle, published. Corners rather than origin+size, because
    every derivation below produces corners and converting twice loses a pixel."""
    out = {
        "x": _px(x0),
        "y": _px(y0),
        "w": max(1, _px(x1) - _px(x0)),
        "h": max(1, _px(y1) - _px(y0)),
    }
    if name is not None:
        return {"name": name, **out}
    return out


def _authored(dx: float, above_floor: float, w: float, h: float) -> dict:
    """One rectangle authored in NORMALIZED body space, published.

    ``dx`` runs from her centre line and ``above_floor`` names the rectangle's TOP
    as a height above the ground line — both in units where her head bone stands
    :data:`AUTHORED_STATURE` up. Widths and heights are lengths in that same space.
    """
    frame = _frame()
    scale = _scale()
    x0 = float(frame["center_x"]) + dx * scale
    y0 = float(frame["ground_y"]) - above_floor * scale
    return _rect_px(x0, y0, x0 + w * scale, y0 + h * scale)


def _attack(
    dx: float,
    above_floor: float,
    w: float,
    h: float,
    *,
    active: Sequence[int],
) -> dict:
    """One strike volume and the frames of its row that carry it.

    ⚠ **`active` is a list of FRAME INDICES, not a duration.** A row's startup and
    recovery frames are simply absent from it, which is what lets a sheet author
    a slow tell and a fast hit without a second timing vocabulary.
    """
    return {"bbox": _authored(dx, above_floor, w, h), "active_frames": list(active)}


# ── hurtboxes, SOLVED from the rig ───────────────────────────────────────────
#
#  seven parts, and they are the rig's own limbs. A single body rectangle
# cannot say that a fighter's outstretched arm is hittable while her head is not,
# which is the whole reason the sheet publishes parts rather than one box.
#
#  and they are no longer SEVEN HAND-LISTED POSE FAMILIES. This file used to
# carry standing/crouch/air/prone/ledge/shielded/buried rectangle sets plus six
# name tables deciding which row got which — 120 lines whose only job was to
# approximate what the rig already knows exactly, and which silently kept
# approximating it after the rig was rebuilt. A row's boxes now come from
# SOLVING that row's own clip: a crouch is low because the crouch pose is low,
# and a knocked-down body is long because she is lying down in it.

#: Half-thicknesses, as fractions of :func:`_stature`, so a rebuilt rig keeps its
#: proportions. A limb is a segment and a segment has no width; this is the only
#: thing about a hurtbox a skeleton cannot state.
_LIMB_HALF = 0.045
_TORSO_HALF = 0.11
_PELVIS_HALF = 0.12
_HEAD_HALF = 0.13

#: bone chains behind each published part name.
_ARM_CHAINS = {
    "rear_arm": ("far_arm_u", "far_arm_l", "far_arm_hand"),
    "front_arm": ("near_arm_u", "near_arm_l", "near_arm_hand"),
    "rear_leg": ("far_leg_u", "far_leg_l", "far_leg_foot"),
    "front_leg": ("near_leg_u", "near_leg_l", "near_leg_foot"),
}


def _segment(world, bone: str) -> tuple[float, float, float, float]:
    """A bone's two endpoints in rig space. A zero-length bone is a point."""
    entry = world[bone]
    x0, y0 = entry.origin
    angle = math.radians(entry.angle)
    return (
        float(x0),
        float(y0),
        float(x0) + math.cos(angle) * float(entry.length),
        float(y0) + math.sin(angle) * float(entry.length),
    )


def _chain_box(world, bones: Iterable[str], pad: float) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for bone in bones:
        x0, y0, x1, y1 = _segment(world, bone)
        xs += [x0, x1]
        ys += [y0, y1]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def _parts_for_pose(world) -> list[dict]:
    """The seven published parts, read off one solved pose."""
    stature = _stature()
    head_x, head_y = (float(v) for v in world["head"].origin)
    torso_x, torso_y = (float(v) for v in world["torso"].origin)
    pelvis_x, pelvis_y = (float(v) for v in world["pelvis"].origin)
    head_half = _HEAD_HALF * stature
    torso_half = _TORSO_HALF * stature
    pelvis_half = _PELVIS_HALF * stature
    limb_half = _LIMB_HALF * stature

    parts = [
        _rect_px(
            head_x - head_half,
            head_y - head_half,
            head_x + head_half,
            head_y + head_half,
            name="head",
        ),
        # The torso runs from just inside the head down to the pelvis joint, so a
        # hit to the chest is not a hit to the face.
        _rect_px(
            torso_x - torso_half,
            min(head_y + head_half * 0.2, torso_y),
            torso_x + torso_half,
            max(head_y + head_half * 0.2, torso_y),
            name="upper_torso",
        ),
        _rect_px(
            pelvis_x - pelvis_half,
            min(torso_y, pelvis_y),
            pelvis_x + pelvis_half,
            max(torso_y, pelvis_y) + pelvis_half * 0.6,
            name="pelvis",
        ),
    ]
    for name, bones in _ARM_CHAINS.items():
        x0, y0, x1, y1 = _chain_box(world, bones, limb_half)
        parts.append(_rect_px(x0, y0, x1, y1, name=name))
    return parts


@lru_cache(maxsize=256)
def _parts_for_row(row: str) -> tuple[tuple[tuple[str, int], ...], ...]:
    """Cached, hashable part set for one authored row.

    ⚠ **every row gets an answer**, and the fallback is the IDLE pose rather than
    nothing: a row the rig cannot solve is still a body that can be hit, and
    publishing no parts for it would make her invulnerable in that pose.
    """
    doc = _rig()
    for animation in (row, "idle"):
        try:
            world, _params = doc.solve(animation, 0.5)
        except Exception:  # noqa: BLE001 — a rig that cannot solve a row is data, not a crash
            continue
        return tuple(tuple(sorted(part.items())) for part in _parts_for_pose(world))
    return ()


def hurtbox_parts_for_rows(rows: Iterable[tuple[str, int, int]]) -> dict:
    """One part set per authored row, solved from that row's own pose."""
    out = {}
    for name, _frames, _duration in rows:
        parts = [dict(part) for part in _parts_for_row(name)]
        if parts:
            out[name] = {"parts": parts}
    return out


#: A column of the drawn frame counts as BODY when it carries at least this
#: fraction of the silhouette's height. Her outstretched hand occupies about
#: 11% of her rows and her skirt about 30%, so the two separate cleanly — and
#: the rule is a measurement rather than a taste call, which is what lets it
#: survive a new pose.
BODY_COLUMN_COVERAGE = 0.15


def body_from_silhouette(profile: dict) -> tuple[float, float, float, float]:
    """Return the drawn body bounds after excluding thin reaching columns.

    `profile` contains per-column alpha coverage and the published-frame bounds.
    Keeping columns above `BODY_COLUMN_COVERAGE` covers the body while excluding
    narrow outstretched limbs.
    """
    x0, y0, x1, y1 = profile["bounds"]
    columns = profile["columns"]
    span = max(1.0, float(y1 - y0))
    keep = [x for x, rows in enumerate(columns) if rows / span >= BODY_COLUMN_COVERAGE]
    if keep:
        x0, x1 = float(min(keep)), float(max(keep) + 1)
    return (x0, float(y0), x1, float(y1))


def body_metrics(fw: int, fh: int, profile: dict | None = None) -> dict:
    """Where Noether's body and feet are in the published frame.

    ⭐ **the feet point is the rig's OWN ground line**, which is the hover fix: a
    body placed by its feet stands ON the floor rather than forty pixels above
    it. The rig is asked because the rig is what drew the picture.

    ⭐ **the box is the DRAWING**, trimmed by [`body_from_silhouette`] — not a
    fraction of her stature. Without a measured `profile` it falls back to the
    skeleton envelope, which is honest but narrower than she looks; every real
    publish passes one.
    """
    frame = _frame()
    world, _params = _rig().solve("idle", 0.0)
    ground = float(frame["ground_y"])
    centre = float(frame["center_x"])

    if profile is not None:
        #  already in PUBLISHED pixels — the profile is measured on the composed
        # frame — so this does not go through `_px`, which converts from rig
        # space. Mixing the two spaces is the exact mistake this file exists to
        # correct.
        x0, y0, x1, y1 = body_from_silhouette(profile)
        body = {
            "x": int(round(x0)),
            "y": int(round(y0)),
            "w": max(1, int(round(x1 - x0))),
            "h": max(1, int(round(y1 - y0))),
        }
    else:
        stature = _stature()
        half_width = 0.19 * stature
        top = float(world["head"].origin[1]) - _HEAD_HALF * stature
        body = _rect_px(centre - half_width, top, centre + half_width, ground)

    feet_x = float(_px(centre))
    feet_y = float(_px(ground))
    return {
        "body_pixel_bbox": body,
        "feet_pixel": {"x": feet_x, "y": feet_y},
        "feet_anchor_norm": {
            "x": round(feet_x / fw - 0.5, 6),
            "y": round(0.5 - feet_y / fh, 6),
        },
    }


# ── strike volumes ───────────────────────────────────────────────────────────
#
#  these are the SHEET's geometry, not the game's balance. Damage, launch
# angle, knockback growth and frame timings live on Noether's `MovesetContract`
# in Ambition content; what a sheet can honestly say is WHERE a drawn strike
# reaches and WHICH of its frames are the strike. A second combat database here
# would be the `character_archetypes.ron` mistake in Python.
#
#  her blade reaches roughly 30 authored units ahead of centre on a committed
# swing — that is the number the reaches below are scaled against rather than a
# taste call. `dx` runs from her centre line, and the second argument is the
# rectangle's TOP as a height above the floor.


def _attack_table() -> dict:
    return {
        # ── ordinary fighter surface ────────────────────────────────────────
        "jab": _attack(6, 48, 20, 14, active=[2]),
        "punch": _attack(6, 47, 24, 16, active=[2, 3]),
        "slash": _attack(4, 54, 30, 28, active=[2, 3, 4]),
        "dash_attack": _attack(5, 44, 27, 22, active=[2, 3, 4]),
        "attack_side": _attack(6, 48, 27, 20, active=[2, 3]),
        "attack_up": _attack(-9, 76, 20, 24, active=[2, 3]),
        "attack_down": _attack(-2, 16, 28, 16, active=[2, 3]),
        "smash_forward": _attack(5, 56, 32, 32, active=[3, 4, 5]),
        "smash_up": _attack(-11, 84, 24, 32, active=[3, 4, 5]),
        "smash_down": _attack(-20, 14, 42, 14, active=[3, 4, 5]),
        "air_neutral": _attack(-14, 56, 30, 26, active=[2, 3]),
        "air_forward": _attack(5, 56, 28, 24, active=[2, 3]),
        "air_back": _attack(-32, 54, 28, 22, active=[2, 3]),
        "air_up": _attack(-10, 80, 22, 24, active=[2, 3]),
        "air_down": _attack(-9, 22, 20, 26, active=[2, 3]),
        "ledge_attack": _attack(3, 34, 26, 18, active=[2, 3]),
        "getup_attack": _attack(-22, 16, 46, 16, active=[2, 3]),
        # ── the signature clips `noether_motion` renames ────────────────────
        #
        #  each is the pose the renamed row DRAWS, which is why they are not all
        # the same shape: a conservation law is a held field, a generator strike
        # is a committed swing, and a symmetry break is the biggest thing she
        # does.
        "generator_strike": _attack(4, 58, 34, 34, active=[2, 3, 4]),
        "conservation_law": _attack(-18, 60, 40, 44, active=[3, 4, 5, 6]),
        "symmetry_shift": _attack(-14, 52, 32, 30, active=[2, 3, 4]),
        "symmetry_proof": _attack(2, 52, 30, 26, active=[2, 3, 4]),
        "invariant_field": _attack(-26, 34, 56, 34, active=[3, 4, 5, 6]),
        "symmetry_break": _attack(-24, 72, 52, 60, active=[4, 5, 6]),
        "noether_theorem": _attack(-34, 86, 72, 86, active=[5, 6, 7, 8]),
    }


@lru_cache(maxsize=1)
def attack_hitboxes() -> dict:
    """The strike table, resolved against the live rig.

    ⚠ **a function, not a module constant.** Resolving it needs the rig document,
    and a module that loads (and can rebuild) a rig at import time is a module
    nobody can import cheaply.
    """
    return _attack_table()


NOETHER_MOVE_BLUEPRINT = {
    #  DESIGN INPUT AND NAMING VOCABULARY — NOT A RUNTIME COMBAT DATABASE.
    # The engine reads Noether's timings, damage and launch from her
    # `CharacterDefinition` in Ambition content. This block travels with the
    # SHEET so an artist and a designer can see the same intent beside the art
    # that draws it, and so a future authoring step has something to import from
    # rather than a blank page.
    #
    #  the `clip` of each entry is the authored ROW NAME, which is the one thing
    # here the game genuinely consumes — through `MoveSpec.clip` and the sheet's
    # own row table.
    "melee": {
        "clip": "generator_strike",
        "intent": "A committed swing along the blade: her fastest way to say no.",
    },
    "special_neutral": {
        "clip": "conservation_law",
        "intent": "A held field that returns what it absorbs — punish for a "
                  "committed attack rather than a poke.",
    },
    "special_side": {
        "clip": "symmetry_shift",
        "intent": "A lateral displacement that keeps her facing: reposition "
                  "without conceding the neutral.",
    },
    "special_up": {
        "clip": "ethereal_lift",
        "intent": "Her recovery. Rises, does not attack — the traversal motif, "
                  "not a second offensive option.",
    },
    "special_down": {
        "clip": "invariant_field",
        "intent": "A low, wide field that denies the ground in front of her.",
    },
    "super": {
        "clip": "noether_theorem",
        "intent": "Every symmetry has its conserved quantity; the whole screen "
                  "pays. The slowest tell she has.",
    },
    "defense_parry": {
        "clip": "invariant_parry",
        "intent": "A guard that keeps what it blocks — the defensive half of the "
                  "conservation idea.",
    },
    "break": {
        "clip": "symmetry_break",
        "intent": "The launcher: the moment the invariant stops holding.",
    },
}


__all__ = [
    "NOETHER_MOVE_BLUEPRINT",
    "PADDING",
    "TARGET_NAME",
    "attack_hitboxes",
    "body_metrics",
    "hurtbox_parts_for_rows",
]
