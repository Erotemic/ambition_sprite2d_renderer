"""Sprite-side gameplay geometry for the Noether fighter.

Noether's rig is authored in the logical 128x128 space her ``noether.rig.json``
declares (``ground_y = 101``, ``center_x = 64``, ``render_scale = 2``), and the
target composes it with :data:`noether.RIG_RENDER_PADDING`.  Every number in this
module is written in that RIG space and mapped to published pixels once, at the
boundary, by :func:`_px` / :func:`_len` — the same discipline
``pca_gameplay.py`` follows.

⭐ **the geometry is DERIVED from the rig's own bone chain, not eyeballed.** The
pelvis sits ``20.5`` above the ground line, the torso ``4`` above that and the
head ``26`` above the torso; arms hang from the torso at ``-9.5`` with a ``9.5``
upper and an ``8`` lower; legs run from the pelvis to the floor through a ``10``
upper, an ``8.5`` lower and a ``6`` foot.  Reading those numbers rather than
inventing a silhouette is what keeps combat geometry honest when the ART moves:
a wider coat or a longer skirt changes the drawing and must not silently inflate
the boxes a fighter is hit by.

⚠ **the source SVG and the rig remain presentation authority.** Nothing here
feeds back into them, and the timings/damage of Noether's moves are the GAME's
(``CharacterDefinition`` + ``MovesetContract``), never this file's.  What lives
here is what the SHEET knows: where her body is in each pose, and which frames of
an authored clip carry a strike.
"""

from __future__ import annotations

from typing import Iterable, Sequence

# The rig document's own frame, restated so a reader of this file does not have
# to open the JSON to follow the numbers below.
RIG_SIZE = (128, 128)
GROUND_Y = 101.0
CENTER_X = 64.0
RENDER_SCALE = 2
PADDING = 28


def _px(value: float) -> int:
    """A rig coordinate, in published pixels."""
    return int(round((float(value) + PADDING) * RENDER_SCALE))


def _len(value: float) -> int:
    """A rig LENGTH, in published pixels — padding is an offset, not a size."""
    return int(round(float(value) * RENDER_SCALE))


def _rect(name: str, x: float, y: float, w: float, h: float) -> dict:
    return {"name": name, "x": _px(x), "y": _px(y), "w": _len(w), "h": _len(h)}


def _bbox(x: float, y: float, w: float, h: float) -> dict:
    return {"x": _px(x), "y": _px(y), "w": _len(w), "h": _len(h)}


def _attack(
    x: float,
    y: float,
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
    return {"bbox": _bbox(x, y, w, h), "active_frames": list(active)}


# ── hurtboxes, by pose family ────────────────────────────────────────────────
#
# ⭐ **seven parts, and they are the rig's own limbs.** A single body rectangle
# cannot say that a fighter's outstretched arm is hittable while her head is not,
# which is the whole reason the sheet publishes parts rather than one box.

STANDING_HURTBOX = [
    # head bone: pelvis(-20.5) + torso(-4) + head(-26) = 50.5 above the floor.
    _rect("head", CENTER_X - 8, GROUND_Y - 62, 16, 15),
    _rect("upper_torso", CENTER_X - 10, GROUND_Y - 47, 20, 18),
    _rect("pelvis", CENTER_X - 9, GROUND_Y - 29, 18, 10),
    # arms hang from the torso at -9.5, upper 9.5 + lower 8.
    _rect("rear_arm", CENTER_X + 1, GROUND_Y - 44, 8, 20),
    _rect("front_arm", CENTER_X - 9, GROUND_Y - 44, 8, 20),
    # legs: pelvis to floor through 10 + 8.5 + 6.
    _rect("rear_leg", CENTER_X, GROUND_Y - 20, 8, 20),
    _rect("front_leg", CENTER_X - 8, GROUND_Y - 20, 8, 20),
]

CROUCH_HURTBOX = [
    _rect("head", CENTER_X - 8, GROUND_Y - 47, 16, 14),
    _rect("upper_torso", CENTER_X - 11, GROUND_Y - 34, 22, 15),
    _rect("pelvis", CENTER_X - 10, GROUND_Y - 20, 20, 9),
    _rect("rear_arm", CENTER_X + 1, GROUND_Y - 33, 8, 16),
    _rect("front_arm", CENTER_X - 9, GROUND_Y - 33, 8, 16),
    _rect("rear_leg", CENTER_X, GROUND_Y - 12, 8, 12),
    _rect("front_leg", CENTER_X - 8, GROUND_Y - 12, 8, 12),
]

# ⚠ airborne is the standing set lifted, NOT a smaller one. A fighter does not
# become harder to hit by leaving the ground; only her feet stop touching it.
AIR_HURTBOX = [
    _rect("head", CENTER_X - 8, GROUND_Y - 65, 16, 15),
    _rect("upper_torso", CENTER_X - 10, GROUND_Y - 50, 20, 18),
    _rect("pelvis", CENTER_X - 9, GROUND_Y - 32, 18, 10),
    _rect("rear_arm", CENTER_X + 1, GROUND_Y - 47, 8, 19),
    _rect("front_arm", CENTER_X - 9, GROUND_Y - 47, 8, 19),
    _rect("rear_leg", CENTER_X, GROUND_Y - 23, 8, 18),
    _rect("front_leg", CENTER_X - 8, GROUND_Y - 23, 8, 18),
]

# Prone is the body ROTATED onto the floor: long in x, short in y, and the head
# leads. Reusing the standing boxes here would leave a knocked-down fighter
# hittable through empty air above her.
PRONE_HURTBOX = [
    _rect("head", CENTER_X + 12, GROUND_Y - 13, 13, 12),
    _rect("upper_torso", CENTER_X - 4, GROUND_Y - 14, 16, 13),
    _rect("pelvis", CENTER_X - 15, GROUND_Y - 12, 11, 11),
    _rect("rear_leg", CENTER_X - 26, GROUND_Y - 10, 11, 9),
    _rect("front_leg", CENTER_X - 34, GROUND_Y - 8, 12, 8),
]

LEDGE_HURTBOX = [
    _rect("head", CENTER_X - 7, GROUND_Y - 49, 15, 14),
    _rect("upper_torso", CENTER_X - 9, GROUND_Y - 35, 19, 16),
    _rect("pelvis", CENTER_X - 8, GROUND_Y - 19, 17, 11),
    _rect("rear_leg", CENTER_X, GROUND_Y - 9, 8, 16),
    _rect("front_leg", CENTER_X - 8, GROUND_Y - 9, 8, 16),
]

# A guarded body pulls its limbs IN — the shield covers what the arms leave.
SHIELDED_HURTBOX = [
    _rect("head", CENTER_X - 7, GROUND_Y - 59, 15, 14),
    _rect("upper_torso", CENTER_X - 10, GROUND_Y - 45, 21, 18),
    _rect("pelvis", CENTER_X - 9, GROUND_Y - 27, 19, 10),
    _rect("rear_leg", CENTER_X, GROUND_Y - 18, 8, 18),
    _rect("front_leg", CENTER_X - 8, GROUND_Y - 18, 8, 18),
]

BURIED_HURTBOX = [
    _rect("head", CENTER_X - 8, GROUND_Y - 26, 16, 14),
    _rect("upper_torso", CENTER_X - 10, GROUND_Y - 13, 20, 12),
]

_CROUCH = {"crouch_start", "crouch", "crouch_walk", "crouch_end"}
_AIR = {
    "jump", "double_jump", "fall", "fall_special", "tumble", "air_dodge",
    "air_neutral", "air_forward", "air_back", "air_up", "air_down", "air_land",
    "fly", "hover", "float_glide", "wall_jump", "ledge_jump",
    # ⭐ her signature traversal is an AERIAL pose, whatever it is named.
    "ethereal_lift",
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
    # ⭐ the parry she is named for is a GUARD pose, not a strike.
    "invariant_parry",
}


def hurtbox_parts_for_rows(rows: Iterable[tuple[str, int, int]]) -> dict:
    """One part set per authored row, chosen by pose family.

    ⚠ **every row gets an answer**, and the fallback is STANDING rather than
    nothing: a row this file has not classified is still a body that can be hit,
    and publishing no parts for it would make her invulnerable in that pose.
    """
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
    """Where Noether's body and feet are in the published frame.

    The bbox spans her natural pose — antenna tip to floor, arm to arm — and the
    feet point is the rig's own ground line under its centre, so a body placed by
    its feet stands ON the floor rather than through it.
    """
    body = _bbox(CENTER_X - 13, GROUND_Y - 70, 26, 70)
    feet_x = float(_px(CENTER_X))
    feet_y = float(_px(GROUND_Y))
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
# ⛔ **these are the SHEET's geometry, not the game's balance.** Damage, launch
# angle, knockback growth and frame timings live on Noether's `MovesetContract`
# in Ambition content; what a sheet can honestly say is WHERE a drawn strike
# reaches and WHICH of its frames are the strike. A second combat database here
# would be the `character_archetypes.ron` mistake in Python.
#
# ⚠ her blade bone is 26 long off a hand at +8, so a committed swing reaches
# roughly 30 rig units ahead of centre — that is the number the reaches below are
# scaled against rather than a taste call.

ATTACK_HITBOXES = {
    # ── ordinary fighter surface ────────────────────────────────────────────
    "jab": _attack(CENTER_X + 6, GROUND_Y - 48, 20, 14, active=[2]),
    "punch": _attack(CENTER_X + 6, GROUND_Y - 47, 24, 16, active=[2, 3]),
    "slash": _attack(CENTER_X + 4, GROUND_Y - 54, 30, 28, active=[2, 3, 4]),
    "dash_attack": _attack(CENTER_X + 5, GROUND_Y - 44, 27, 22, active=[2, 3, 4]),
    "attack_side": _attack(CENTER_X + 6, GROUND_Y - 48, 27, 20, active=[2, 3]),
    "attack_up": _attack(CENTER_X - 9, GROUND_Y - 76, 20, 24, active=[2, 3]),
    "attack_down": _attack(CENTER_X - 2, GROUND_Y - 16, 28, 16, active=[2, 3]),
    "smash_forward": _attack(CENTER_X + 5, GROUND_Y - 56, 32, 32, active=[3, 4, 5]),
    "smash_up": _attack(CENTER_X - 11, GROUND_Y - 84, 24, 32, active=[3, 4, 5]),
    "smash_down": _attack(CENTER_X - 20, GROUND_Y - 14, 42, 14, active=[3, 4, 5]),
    "air_neutral": _attack(CENTER_X - 14, GROUND_Y - 56, 30, 26, active=[2, 3]),
    "air_forward": _attack(CENTER_X + 5, GROUND_Y - 56, 28, 24, active=[2, 3]),
    "air_back": _attack(CENTER_X - 32, GROUND_Y - 54, 28, 22, active=[2, 3]),
    "air_up": _attack(CENTER_X - 10, GROUND_Y - 80, 22, 24, active=[2, 3]),
    "air_down": _attack(CENTER_X - 9, GROUND_Y - 22, 20, 26, active=[2, 3]),
    "ledge_attack": _attack(CENTER_X + 3, GROUND_Y - 34, 26, 18, active=[2, 3]),
    "getup_attack": _attack(CENTER_X - 22, GROUND_Y - 16, 46, 16, active=[2, 3]),
    # ── the signature clips `noether_motion` renames ────────────────────────
    #
    # ⚠ each is the pose the renamed row DRAWS, which is why they are not all the
    # same shape: a conservation law is a held field, a generator strike is a
    # committed swing, and a symmetry break is the biggest thing she does.
    "generator_strike": _attack(CENTER_X + 4, GROUND_Y - 58, 34, 34, active=[2, 3, 4]),
    "conservation_law": _attack(CENTER_X - 18, GROUND_Y - 60, 40, 44, active=[3, 4, 5, 6]),
    "symmetry_shift": _attack(CENTER_X - 14, GROUND_Y - 52, 32, 30, active=[2, 3, 4]),
    "symmetry_proof": _attack(CENTER_X + 2, GROUND_Y - 52, 30, 26, active=[2, 3, 4]),
    "invariant_field": _attack(CENTER_X - 26, GROUND_Y - 34, 56, 34, active=[3, 4, 5, 6]),
    "symmetry_break": _attack(CENTER_X - 24, GROUND_Y - 72, 52, 60, active=[4, 5, 6]),
    "noether_theorem": _attack(CENTER_X - 34, GROUND_Y - 86, 72, 86, active=[5, 6, 7, 8]),
}


NOETHER_MOVE_BLUEPRINT = {
    # ⛔⛔ **DESIGN INPUT AND NAMING VOCABULARY — NOT A RUNTIME COMBAT DATABASE.**
    # The engine reads Noether's timings, damage and launch from her
    # `CharacterDefinition` in Ambition content. This block travels with the
    # SHEET so an artist and a designer can see the same intent beside the art
    # that draws it, and so a future authoring step has something to import from
    # rather than a blank page.
    #
    # ⚠ the `clip` of each entry is the authored ROW NAME, which is the one thing
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
    "ATTACK_HITBOXES",
    "NOETHER_MOVE_BLUEPRINT",
    "body_metrics",
    "hurtbox_parts_for_rows",
]
