"""Drawing helpers shared by the pirate-family characters.

Pirate-specific paint code: palettes, body part draws (hat / face /
boot / sword / neck), the parametric `animation_pose` rig, and the
`draw_character(kind, anim, ...)` entry point that composes them.

Leading underscore is intentional — the target registry walks
``targets/characters/`` and treats files starting with ``_`` as
helpers, so this module won't try to register as a target.

The 5 core pirate character modules (admiral, raider, quartermaster,
lookout, navigator) re-use the same parametric rig keyed on their
palette + cohort tags (`SCARFED_KINDS`, `BEARDED_KINDS`,
`SKULL_MOTIF_KINDS`). Each `targets/characters/pirate_<role>.py`
module's `render()` calls `render_target(<role>, ...)` here, which
plumbs through to `sheet_build.build_sheet` with the right
`draw_character` partial.

A handful of non-pirate characters that happened to look pirate-ish
(colonial_statesman, viking variants, etc.) also re-use the
`draw_character` palette branches — see the per-kind switches inside
the body-draw helpers.
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

from ...authoring.sheet_build import (
    ANIMATIONS,
    BASE_FRAME,
    RGBA,
    SCALE,
    build_sheet,
    circle,
    downsample,
    ease_in_out,
    ellipse,
    lerp,
    line,
    oscillate,
    poly,
    rotated_rect_points,
    transform,
)
from ambition_sprite2d_renderer.core.draw import blending_draw
from . import _pirate_rig as pirate_rig


@dataclass
class Palette:
    outline: RGBA
    skin: RGBA
    skin_shadow: RGBA
    hat: RGBA
    coat: RGBA
    coat2: RGBA
    sash: RGBA
    shirt: RGBA
    pants: RGBA
    boots: RGBA
    metal: RGBA
    gold: RGBA
    beard: RGBA | None = None
    accent: RGBA | None = None


# Cohort tags so the parametric draw branches can ask "is this a
# scarf-wearing pirate" / "is this a bearded pirate" rather than
# spelling out every kind name in every branch. Lady pirates wear
# scarves and share the taunt-tilt + blade-tip-offset behavior with
# the male raiders, but they don't grow beards or wear the chest
# skull motif.
SCARFED_KINDS = (
    "pirate_raider",
    "pirate_quartermaster",
    "pirate_lookout",
    "pirate_navigator",
)
BEARDED_KINDS = ("pirate_raider", "pirate_quartermaster")
SKULL_MOTIF_KINDS = ("pirate_raider", "pirate_quartermaster")


PALETTES = {
    "pirate_admiral": Palette(
        outline=(26, 28, 35, 255),
        # Warm mid-brown skin. Reads as Caribbean-coast / mestizo
        # rather than European-pale; sits between the lighter raider
        # tone (#EBC4A0) and the deep brown quartermaster (#704C32) so
        # the cove lineup hits three distinct values at a glance.
        skin=(168, 124, 88, 255),
        skin_shadow=(112, 76, 48, 255),
        hat=(28, 31, 41, 255),
        coat=(88, 108, 138, 255),
        coat2=(146, 165, 191, 255),
        sash=(113, 40, 40, 255),
        shirt=(214, 205, 182, 255),
        pants=(212, 196, 160, 255),
        boots=(69, 50, 35, 255),
        metal=(210, 216, 228, 255),
        gold=(206, 171, 74, 255),
        beard=None,
        accent=(222, 72, 55, 255),
    ),
    "pirate_raider": Palette(
        outline=(28, 24, 26, 255),
        skin=(235, 196, 160, 255),
        skin_shadow=(175, 128, 95, 255),
        hat=(31, 23, 32, 255),
        coat=(196, 60, 52, 255),
        coat2=(229, 191, 105, 255),
        sash=(38, 30, 28, 255),
        shirt=(238, 228, 206, 255),
        pants=(66, 67, 73, 255),
        boots=(84, 53, 31, 255),
        metal=(201, 207, 214, 255),
        gold=(227, 184, 70, 255),
        beard=(77, 42, 23, 255),
        accent=(239, 239, 239, 255),
    ),
    # Third pirate variant — same silhouette family as `pirate_raider`
    # (broad cutlass-and-coat raider archetype) but a distinctly
    # darker skin tone so the lineup represents more of the actual
    # human phenotype range that historical Caribbean / Indian Ocean
    # / Mediterranean pirate crews drew from. The coat shifts from
    # raider's bright red to a deep teal so the silhouettes are
    # easy to tell apart at a glance even when palette-only
    # variants ship side-by-side.
    "pirate_quartermaster": Palette(
        outline=(18, 14, 16, 255),
        # Deep brown skin — noticeably darker than the existing
        # `pirate_admiral` (#A87C58) and `pirate_raider` (#EBC4A0).
        skin=(112, 76, 50, 255),
        skin_shadow=(72, 46, 28, 255),
        hat=(20, 24, 30, 255),
        coat=(28, 92, 92, 255),  # deep teal
        coat2=(206, 178, 92, 255),  # warm gold trim
        sash=(160, 38, 38, 255),  # bright crimson sash for contrast
        shirt=(238, 226, 198, 255),
        pants=(46, 42, 38, 255),
        boots=(54, 36, 22, 255),
        metal=(212, 218, 224, 255),
        gold=(228, 188, 76, 255),
        # Short cropped beard matching the warm-dark skin tone.
        beard=(38, 24, 16, 255),
        accent=(232, 220, 196, 255),
    ),
    # ─────────────────────────────────────────────────────────────────
    # Lady pirate variants. Same skeleton + hat / sash / sword
    # geometry as the male roles (the parametric character draws the
    # same silhouette), but no beard and a warmer scarf / coat
    # palette so they read as a distinct crew at a glance.
    #
    # Two skin tones — Lookout deep-brown (matches Quartermaster
    # range), Navigator pale-warm — so the lineup hits five distinct
    # phenotypes between the three men + two women.
    # ─────────────────────────────────────────────────────────────────
    "pirate_lookout": Palette(
        outline=(22, 18, 22, 255),
        # Deep brown skin in the Quartermaster range, slightly warmer.
        skin=(118, 80, 56, 255),
        skin_shadow=(76, 48, 32, 255),
        hat=(24, 28, 38, 255),  # dark navy cap
        coat=(176, 60, 88, 255),  # raspberry coat
        coat2=(232, 200, 132, 255),  # buttery trim
        sash=(48, 36, 28, 255),  # dark leather sash
        shirt=(244, 232, 208, 255),
        pants=(52, 38, 32, 255),
        boots=(60, 38, 22, 255),
        metal=(214, 220, 226, 255),
        gold=(228, 188, 76, 255),
        beard=None,  # no beard — lady pirate
        accent=(255, 230, 196, 255),
    ),
    "pirate_navigator": Palette(
        outline=(24, 20, 24, 255),
        # Pale-warm skin, between the existing Raider and a paler
        # northern-European reference. Distinct from Admiral's mid-
        # brown so the cove lineup reads as five different people.
        skin=(238, 206, 178, 255),
        skin_shadow=(196, 152, 116, 255),
        hat=(72, 24, 48, 255),  # plum hat
        coat=(46, 64, 96, 255),  # midnight navy coat
        coat2=(214, 198, 174, 255),  # bone trim
        sash=(212, 168, 64, 255),  # gold sash
        shirt=(244, 240, 232, 255),
        pants=(58, 50, 48, 255),
        boots=(64, 44, 28, 255),
        metal=(216, 222, 230, 255),
        gold=(232, 192, 80, 255),
        beard=None,  # no beard — lady pirate
        accent=(178, 116, 156, 255),
    ),
}


#: The slash, a frame for each column: the sword goes up and back over the
#: head, comes over the top, strikes to the front and goes on down. The hit of
#: the game is in frames 2 and 3 (its events are at 0.34 and 0.58 of the row).
_SLASH = {
    "sword_upper": (-150.0, -172.0, -120.0, -62.0, -36.0, -22.0),
    "sword_fore": (-215.0, -240.0, -150.0, -75.0, -40.0, -70.0),
    "weapon": (-150.0, -170.0, -80.0, 5.0, 55.0, 10.0),
    "off_upper": (30.0, 40.0, 20.0, 50.0, 56.0, 40.0),
    "off_fore": (10.0, 20.0, 0.0, 40.0, 46.0, 20.0),
    "body_tilt": (-6.0, -10.0, 2.0, 14.0, 16.0, 8.0),
    "root_x": (-2.0, -4.0, 2.0, 8.0, 9.0, 5.0),
    "left_thigh": (12.0, 16.0, 14.0, 26.0, 28.0, 20.0),
    "left_shin": (20.0, 26.0, 22.0, 30.0, 32.0, 24.0),
    "right_thigh": (-14.0, -8.0, -24.0, -40.0, -42.0, -28.0),
    "right_shin": (-4.0, 4.0, -6.0, 2.0, 4.0, -4.0),
    "head_tilt": (-4.0, -6.0, 0.0, 4.0, 4.0, 0.0),
    "hat_tilt": (-2.0, -4.0, 0.0, 4.0, 5.0, 2.0),
    "coat_sway": (10.0, 14.0, 0.0, -16.0, -18.0, -8.0),
    "mouth_open": (0.1, 0.3, 0.6, 0.8, 0.5, 0.2),
}


#: The frames of the slash that show the path of the blade, and the part of
#: the circle each shows (degrees, 0 to the front, clockwise).
_SWOOSH = {2: (205.0, 290.0), 3: (265.0, 360.0), 4: (315.0, 400.0)}


def _sampled(table, t: float) -> float:
    """The value of a row of keys at ``t`` of the way along it."""
    at = max(0.0, min(1.0, t)) * (len(table) - 1)
    i = min(int(at), len(table) - 2)
    return lerp(table[i], table[i + 1], at - i)


def animation_pose(anim, frame_idx, nframes):
    """The pose of one frame: where the body is and where each bone points.

    A limb angle is a world angle (see ``_pirate_rig``): 0 is down, negative is
    to the front, positive is to the back. The guard is the home pose: the
    feet apart with the front knee a little bent, the sword held up to the
    front, the other arm down and a little behind the body.

    Each pose but the death is planted: the root goes down or up until the
    lower foot is on the ground.
    """
    s = oscillate(frame_idx, nframes)
    t = frame_idx / max(1, nframes - 1)
    pose = {
        "root_x": 0.0,
        "bob": 0.0,
        "body_tilt": 2.0,
        "left_thigh": 12.0,
        "left_shin": 14.0,
        "right_thigh": -16.0,
        "right_shin": -6.0,
        "sword_upper": -18.0,
        "sword_fore": -100.0,
        "weapon": -50.0,
        "off_upper": 26.0,
        "off_fore": 8.0,
        "head_tilt": -2.0,
        "head_y": 0.0,
        "hat_tilt": 0.0,
        "coat_sway": 0.0,
        "shoulder_bounce": 0.0,
        "blink": False,
        "mouth_open": 0.0,
        "death_t": 0.0,
        "x_eyes": False,
    }
    if anim == "idle":
        # He breathes: the chest and the sword go up and down a little.
        pose["shoulder_bounce"] = -s * 2.0
        pose["sword_fore"] = -100.0 + s * 3.0
        pose["weapon"] = -50.0 - s * 5.0
        pose["off_upper"] = 26.0 + s * 2.0
        pose["off_fore"] = 8.0 + s * 2.0
        pose["head_tilt"] = -2.0 + s * 1.5
        pose["hat_tilt"] = s * 1.5
        pose["coat_sway"] = s * 4.0
        pose["blink"] = frame_idx == max(0, nframes - 2)
    elif anim == "walk":
        phase = (frame_idx / max(1, nframes)) * math.tau
        for side, at in (("left", phase), ("right", phase + math.pi)):
            thigh = 26.0 * math.sin(at)
            # The knee bends while the leg comes to the front.
            pose[f"{side}_thigh"] = thigh
            pose[f"{side}_shin"] = thigh + 50.0 * max(0.0, -math.cos(at))
        pose["body_tilt"] = 5.0
        pose["sword_upper"] = -14.0 + 6.0 * math.sin(phase)
        pose["sword_fore"] = -82.0 + 6.0 * math.sin(phase)
        pose["weapon"] = -30.0 + 5.0 * math.sin(2.0 * phase)
        # The free arm goes back when its leg goes to the front.
        pose["off_upper"] = 14.0 - 24.0 * math.sin(phase)
        pose["off_fore"] = pose["off_upper"] - 22.0
        pose["shoulder_bounce"] = 1.5 * math.cos(2.0 * phase)
        pose["head_tilt"] = -3.0
        pose["hat_tilt"] = 2.0 * math.sin(phase)
        pose["coat_sway"] = -12.0 * math.sin(phase)
    elif anim == "slash":
        for channel, table in _SLASH.items():
            pose[channel] = _sampled(table, t)
    elif anim == "taunt":
        # The sword is up over the head and he laughs with his head back.
        pose["body_tilt"] = -4.0 + s * 2.0
        # Not straight up: the tip of the blade stays in the frame of the sheet.
        pose["sword_upper"] = -138.0 + s * 5.0
        pose["sword_fore"] = -150.0 + s * 6.0
        pose["weapon"] = -46.0 + s * 8.0
        # The free hand is a fist that he shakes.
        pose["off_upper"] = 34.0 + s * 8.0
        pose["off_fore"] = -30.0 + s * 14.0
        pose["head_tilt"] = -8.0 + s * 4.0
        pose["hat_tilt"] = -3.0 + s * 3.0
        pose["coat_sway"] = s * 6.0
        pose["shoulder_bounce"] = -s * 2.0
        pose["mouth_open"] = 0.5 + max(0.0, s) * 0.4
    elif anim == "hurt":
        phase = math.sin(t * math.pi)
        shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
        # He is thrown back onto the back foot, and the arms go out.
        pose["root_x"] = -5.0 * phase + shake * 3.0
        pose["body_tilt"] = 2.0 - 18.0 * phase
        pose["left_thigh"] = 12.0 + 10.0 * phase
        pose["left_shin"] = 14.0 + 18.0 * phase
        pose["right_thigh"] = -16.0 + 10.0 * phase
        pose["right_shin"] = -6.0 + 14.0 * phase
        pose["sword_upper"] = -18.0 - 50.0 * phase
        pose["sword_fore"] = -100.0 - 40.0 * phase
        pose["weapon"] = -50.0 - 60.0 * phase
        pose["off_upper"] = 26.0 + 40.0 * phase
        pose["off_fore"] = 8.0 + 40.0 * phase
        pose["head_tilt"] = -2.0 - 12.0 * phase
        pose["hat_tilt"] = -10.0 * phase
        pose["coat_sway"] = -10.0 * phase
        pose["mouth_open"] = 0.6 * phase
        pose["blink"] = phase > 0.5
    elif anim == "death":
        tt = ease_in_out(t)
        up = math.sin(tt * math.pi)
        pose["death_t"] = tt
        # He goes down on his back like a plank: the body and the legs turn
        # together about the feet, which stay where they were. The sword arm
        # goes up as he falls and comes down along the body.
        pose["root_x"] = tt * 16.0
        pose["bob"] = -tt * 4.0
        pose["body_tilt"] = lerp(2.0, -86.0, tt)
        pose["left_thigh"] = lerp(12.0, -82.0, tt)
        pose["left_shin"] = lerp(14.0, -80.0, tt)
        pose["right_thigh"] = lerp(-16.0, -92.0, tt)
        pose["right_shin"] = lerp(-6.0, -86.0, tt)
        pose["sword_upper"] = lerp(-18.0, -100.0, tt) - 60.0 * up
        pose["sword_fore"] = lerp(-100.0, -84.0, tt) - 50.0 * up
        pose["weapon"] = lerp(-50.0, -8.0, tt) - 80.0 * up
        pose["off_upper"] = lerp(26.0, 100.0, tt)
        pose["off_fore"] = lerp(8.0, 96.0, tt)
        pose["head_tilt"] = lerp(-2.0, 4.0, tt)
        pose["hat_tilt"] = -14.0 * tt
        pose["coat_sway"] = 12.0 * tt
        pose["mouth_open"] = 0.5 * tt
        pose["x_eyes"] = tt > 0.55
        return pose
    # Plant the pose: the lower foot is on the ground.
    w, h = BASE_FRAME[0] * SCALE, BASE_FRAME[1] * SCALE
    joints = pirate_rig.evaluate(pose, "", w, h, pose["body_tilt"])
    low = max(joints["left_foot"].point[1], joints["right_foot"].point[1])
    pose["bob"] += (pirate_rig.ground_y(h) - low) / SCALE
    return pose


def _shade(color: RGBA, k: float) -> RGBA:
    """``color`` darker (``k`` under 1) or lighter (``k`` over 1), opaque."""
    return (
        max(0, min(255, round(color[0] * k))),
        max(0, min(255, round(color[1] * k))),
        max(0, min(255, round(color[2] * k))),
        color[3],
    )


@dataclass(frozen=True)
class Look:
    """What makes one pirate not the next one: the build of the body, the
    hair, what is on the head and the cut of the coat. The palette has the
    colours; this has the shapes."""

    #: The width of the body: 1.0 is the raider.
    build: float = 1.0
    #: ``tricorn``, ``bicorne``, ``bandana`` or ``plume``.
    headwear: str = "tricorn"
    #: The palette field of the bandana, or of the band and trim of a hat.
    band: str = "sash"
    hair: RGBA = (46, 32, 26, 255)
    #: ``short``, ``long`` (down the back) or ``tail`` (tied behind).
    hair_style: str = "short"
    #: ``full``, ``mustache`` or none.
    beard: Optional[str] = None
    eyepatch: bool = False
    earring: bool = False
    epaulettes: bool = False
    #: A skull on the hat.
    skull: bool = False
    #: ``long`` (tails to the knee, a strap across the chest) or ``short``
    #: (a jacket open on the shirt, to the belt).
    coat: str = "long"
    #: Stripes across the shirt, in the colour of the coat.
    stripes: bool = False
    #: Lashes at the eyes and colour on the lips.
    lashes: bool = False


LOOKS: Dict[str, Look] = {
    "pirate_admiral": Look(
        build=1.05, headwear="bicorne", band="gold", hair=(40, 32, 34, 255),
        beard="mustache", eyepatch=True, epaulettes=True, skull=True, coat="long",
    ),
    "pirate_raider": Look(
        build=1.0, headwear="bandana", band="coat", hair=(77, 42, 23, 255),
        beard="full", earring=True, coat="short", stripes=True,
    ),
    "pirate_quartermaster": Look(
        build=1.17, headwear="tricorn", band="sash", hair=(38, 24, 16, 255),
        beard="full", skull=True, coat="long",
    ),
    "pirate_lookout": Look(
        build=0.9, headwear="bandana", band="coat2", hair=(30, 22, 22, 255),
        hair_style="tail", earring=True, coat="short", stripes=True, lashes=True,
    ),
    "pirate_navigator": Look(
        build=0.92, headwear="plume", band="accent", hair=(156, 84, 44, 255),
        hair_style="long", coat="long", lashes=True,
    ),
}


def draw_boot(draw, center, angle, pal):
    """A sea boot: a shaft over the end of the shin, a foot with its toe to
    the front, a turned cuff and a sole. Local geometry in the boot's own
    frame; placement via the part scope."""
    with draw.part("boot", center, angle):
        poly(draw, [(-12, -24), (10, -24), (11, -3), (-12, -3)], pal.boots, pal.outline, width=3)
        poly(draw, [(-12, -8), (11, -10), (24, -4), (27, 6), (-12, 6)], pal.boots, pal.outline, width=3)
        poly(draw, [(4, -20), (9, -20), (10, -7), (5, -6)], _shade(pal.boots, 0.72))
        poly(draw, [(-14, -29), (12, -29), (13, -19), (-14, -19)],
             _shade(pal.boots, 1.32), pal.outline, width=3)
        # The sole is a polygon, not a wide line: the two rasterizers of this
        # family put the edge of a wide line a pixel apart, and the sole is the
        # lowest thing in the picture, so it is what the feet are measured by.
        poly(draw, [(-13, 3.5), (28, 3.5), (28, 7.5), (-13, 7.5)], _shade(pal.boots, 0.5))


def draw_sword(draw, hand, angle, length, pal, curve=0.0):
    def rect_at(cx, cy, w, h):
        return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
                (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]

    def spine(t: float) -> Tuple[float, float]:
        # The middle of the blade: from the guard to the tip, bent by `curve`.
        a, b, c = (8.0, 0.0), (length * 0.42, curve * 0.10), (float(length), float(curve))
        u = 1.0 - t
        return (u * u * a[0] + 2 * u * t * b[0] + t * t * c[0],
                u * u * a[1] + 2 * u * t * b[1] + t * t * c[1])

    steps = 10
    back, edge = [], []
    for i in range(steps + 1):
        t = i / steps
        x, y = spine(t)
        # A cutlass: the blade is wider toward the tip, then it is cut to a
        # point. A blade that tapers from the guard is a hair at sprite size.
        half = 5.0 + 2.6 * t if t <= 0.8 else lerp(7.08, 0.7, (t - 0.8) / 0.2)
        back.append((x, y - half * 0.7))
        edge.append((x, y + half * 1.3))
    with draw.part("sword", hand, angle):
        # The grip, the guard across it and the bow over the knuckles.
        poly(draw, rect_at(-5, 0, 14, 7), (68, 43, 27, 255), pal.outline, width=3)
        poly(draw, [(-13, 2), (-11, 12), (4, 13), (7, 4)], pal.gold, pal.outline, width=3)
        poly(draw, rect_at(5, 0, 6, 20), pal.gold, pal.outline, width=3)
        # The blade: its back, its edge, and a line of light along the back.
        poly(draw, back + edge[::-1], pal.metal, pal.outline, width=3)
        line(draw, [spine(0.06), spine(0.45), spine(0.82)], (255, 255, 255, 255), width=2)


def draw_neck(draw, chest, head_center, global_tilt, pal, look: Look):
    """The neck, from the collar of the coat to under the jaw, and the
    collar of the shirt over it."""
    base = transform((0, -28), chest, deg=global_tilt)
    top = (head_center[0] - 3, head_center[1] + 20)
    # Its two ends are square to its own line, so it keeps its width when the
    # head is thrown to one side.
    run = math.hypot(top[0] - base[0], top[1] - base[1]) or 1.0
    nx, ny = -(top[1] - base[1]) / run, (top[0] - base[0]) / run
    half = 12.5 * look.build
    pts = [
        (base[0] + nx * half, base[1] + ny * half),
        (base[0] - nx * half, base[1] - ny * half),
        (top[0] - nx * (half - 2), top[1] - ny * (half - 2)),
        (top[0] + nx * (half - 2), top[1] + ny * (half - 2)),
    ]
    poly(draw, pts, pal.skin_shadow, pal.outline, width=3)

    with draw.part("collar", chest, global_tilt):
        poly(draw, [(-21, -31), (-3, -23), (-11, -6), (-24, -14)], pal.shirt, pal.outline, width=3)
        poly(draw, [(3, -23), (21, -31), (24, -14), (11, -6)], pal.shirt, pal.outline, width=3)
        if look.coat == "long":
            # A knot of cloth at the throat, and its two ends.
            knot = pal.accent or pal.coat2
            poly(draw, rotated_rect_points((0, -13), 12, 9, 0.0), knot, pal.outline, width=2)
            poly(draw, [(-2, -9), (-11, 7), (-3, 9), (1, -2)], knot, pal.outline, width=2)
            poly(draw, [(2, -9), (11, 7), (4, 9), (-1, -2)], knot, pal.outline, width=2)


#: The head, from the middle of it: a skull with a jaw, the chin a little to
#: the front. The face looks to the right.
_HEAD = [(-25, -8), (-23, -23), (-11, -32), (7, -33), (21, -25), (27, -9),
         (26, 8), (20, 23), (8, 32), (-7, 30), (-20, 18)]


def _oval(cx: float, cy: float, rx: float, ry: float, steps: int = 16):
    """The points of an oval. A turned part can not hold an ellipse, only a
    circle: an oval in it is a polygon."""
    return [
        (cx + rx * math.cos(math.tau * i / steps), cy + ry * math.sin(math.tau * i / steps))
        for i in range(steps)
    ]


def draw_hair(draw, head_center, tilt, pal, look: Look):
    """The hair behind the head: it is painted before the face."""
    with draw.part("hair", head_center, tilt):
        if look.hair_style == "long":
            poly(draw, [(-27, -22), (-8, -34), (0, -8), (-10, 22), (-14, 40), (-24, 58), (-36, 50),
                        (-46, 56), (-44, 34), (-40, 16), (-34, -4)], look.hair, pal.outline, width=3)
            line(draw, [(-28, 2), (-32, 24), (-30, 44)], _shade(look.hair, 0.7), width=3)
            line(draw, [(-20, 20), (-24, 40)], _shade(look.hair, 1.25), width=3)
        elif look.hair_style == "tail":
            poly(draw, [(-28, -24), (-8, -34), (-4, -12), (-20, 8), (-30, 4)],
                 look.hair, pal.outline, width=3)
            poly(draw, [(-26, -8), (-46, -2), (-58, 20), (-52, 40), (-42, 30), (-40, 14), (-28, 6)],
                 look.hair, pal.outline, width=3)
            poly(draw, [(-34, -8), (-27, -8), (-27, 4), (-34, 4)], pal.gold, pal.outline, width=2)
        else:
            poly(draw, [(-29, -6), (-27, -25), (-12, -35), (2, -34), (-8, -16), (-21, 10), (-29, 8)],
                 look.hair, pal.outline, width=3)


def draw_face(draw, head_center, tilt, pal, look: Look, x_eyes=False, blink=False, mouth_open=0.0):
    """The head and the face on it, in the head's own frame."""
    white = (250, 248, 240, 255)
    with draw.part("face", head_center, tilt):
        # The ear, behind the head.
        poly(draw, _oval(-26, 0.5, 6, 8.5), pal.skin, pal.outline, width=3)
        if look.earring:
            circle(draw, (-27, 13), 4.5, pal.gold, pal.outline, width=2)
        poly(draw, list(_HEAD), pal.skin, pal.outline, width=4)
        # The side of the head away from the light.
        poly(draw, [(-22, -8), (-19, 16), (-8, 27), (-13, 10), (-16, -8)], pal.skin_shadow)
        if look.beard == "full" and pal.beard:
            poly(draw, [(-23, 4), (-12, 11), (0, 9), (8, 13), (17, 9), (26, 4), (24, 24),
                        (13, 39), (0, 42), (-12, 35), (-21, 22)], pal.beard, pal.outline, width=3)
        # The nose.
        poly(draw, [(7, -5), (15, 6), (6, 8)], pal.skin_shadow)
        line(draw, [(8, -5), (15, 6), (7, 8)], pal.outline, width=2)
        # The eyes.
        near, far, eye_y = 16.0, -3.0, -7.0
        if x_eyes:
            for ex in (far, near):
                line(draw, [(ex - 6, eye_y - 6), (ex + 6, eye_y + 6)], pal.outline, width=4)
                line(draw, [(ex - 6, eye_y + 6), (ex + 6, eye_y - 6)], pal.outline, width=4)
        else:
            for ex in (far, near):
                if look.eyepatch and ex == near:
                    continue
                if blink:
                    line(draw, [(ex - 6, eye_y), (ex + 6, eye_y + 1)], pal.outline, width=3)
                else:
                    poly(draw, _oval(ex, eye_y + 1, 5.5, 5.5), white, pal.outline, width=2)
                    circle(draw, (ex + 1.8, eye_y + 1.8), 3.0, pal.outline)
                    # The lid is down over the top of the eye, lower at the
                    # nose: these are not kind people.
                    toward = 1.0 if ex == far else -1.0
                    poly(draw, [(ex - 6.5, eye_y - 5.5), (ex + 6.5, eye_y - 5.5),
                                (ex + 6.5, eye_y - 1.2 + toward * 1.6), (ex - 6.5, eye_y - 1.2 - toward * 1.6)],
                         pal.skin)
                    line(draw, [(ex - 6.5, eye_y - 1.2 - toward * 1.6), (ex + 6.5, eye_y - 1.2 + toward * 1.6)],
                         pal.outline, width=3)
                    if look.lashes:
                        out = ex - 6.5 if ex == far else ex + 6.5
                        line(draw, [(out, eye_y - 1.5), (out - toward * 4.0, eye_y - 5.0)], pal.outline, width=2)
            line(draw, [(far - 8, eye_y - 9), (far + 7, eye_y - 5.5)], pal.outline, width=4)
            line(draw, [(near - 7, eye_y - 5.5), (near + 8, eye_y - 9)], pal.outline, width=4)
            if look.eyepatch:
                line(draw, [(-25, -17), (27, -12)], pal.outline, width=3)
                poly(draw, _oval(near, eye_y + 0.5, 8, 7.5), pal.hat, pal.outline, width=2)
        # The mouth: a grin, or open with a row of teeth.
        if mouth_open > 0.12:
            drop = 5.0 + mouth_open * 12.0
            poly(draw, [(-2, 15), (18, 13), (16, 15 + drop), (2, 16 + drop)], (48, 16, 20, 255), pal.outline, width=2)
            poly(draw, [(0, 16), (16, 14.5), (15.5, 18.5), (0.5, 20)], white)
        else:
            mouth = (232, 214, 196, 255) if look.beard == "full" and pal.beard else pal.outline
            if look.lashes:
                poly(draw, [(0, 16), (8, 15), (17, 14), (9, 21)], (176, 58, 66, 255), pal.outline, width=2)
            else:
                line(draw, [(-2, 17), (8, 20), (18, 15)], mouth, width=3)
        if look.beard == "mustache":
            dark = pal.beard or look.hair
            poly(draw, [(-6, 15), (2, 9), (9, 11), (16, 8), (25, 14), (16, 13), (9, 15), (2, 13)],
                 dark, pal.outline, width=2)


def _skull(draw, at, r, pal):
    bone = (236, 232, 224, 255)
    circle(draw, at, r, bone, pal.outline, width=2)
    line(draw, [(at[0] - r * 0.6, at[1] + r * 0.9), (at[0] + r * 0.6, at[1] + r * 0.9)], bone, width=3)
    circle(draw, (at[0] - r * 0.38, at[1] - r * 0.1), r * 0.24, pal.outline)
    circle(draw, (at[0] + r * 0.38, at[1] - r * 0.1), r * 0.24, pal.outline)


def draw_hat(draw, head_center, tilt, pal, look: Look):
    """What is on the head: a hat or a bandana, in the head's own frame."""
    band = getattr(pal, look.band) or pal.sash
    with draw.part("hat", head_center, tilt):
        if look.headwear == "bandana":
            # The ends of the knot fly behind the head.
            poly(draw, [(-27, -14), (-48, -10), (-58, 2), (-46, 0), (-34, -4)], band, pal.outline, width=3)
            poly(draw, [(-28, -12), (-44, 6), (-40, 16), (-30, 2)], _shade(band, 0.8), pal.outline, width=3)
            poly(draw, [(-27, -10), (-25, -25), (-12, -35), (8, -36), (22, -28), (28, -13),
                        (14, -17), (-6, -17)], band, pal.outline, width=4)
            poly(draw, [(4, -33), (20, -27), (25, -16), (14, -19)], _shade(band, 0.8))
            circle(draw, (-28, -12), 5.5, band, pal.outline, width=3)
            return
        if look.headwear == "plume":
            # A feather that goes back over the brim.
            feather = pal.accent or band
            poly(draw, [(12, -44), (0, -62), (-26, -72), (-54, -62), (-64, -44), (-48, -52), (-26, -52), (-6, -36)],
                 feather, pal.outline, width=3)
            line(draw, [(8, -42), (-12, -58), (-44, -58)], _shade(feather, 0.7), width=2)
            poly(draw, [(-54, -20), (-32, -32), (30, -34), (56, -22), (32, -15), (-30, -15)],
                 pal.hat, pal.outline, width=4)
            poly(draw, [(-24, -28), (-22, -43), (-8, -49), (12, -48), (23, -30)],
                 pal.hat, pal.outline, width=4)
            poly(draw, [(-24, -29), (23, -31), (22, -38), (-23, -36)], band, pal.outline, width=2)
            return
        if look.headwear == "bicorne":
            brim = [(-52, -18), (-36, -40), (-12, -56), (14, -56), (38, -42), (54, -20),
                    (30, -25), (0, -29), (-28, -24)]
            poly(draw, brim, pal.hat, pal.outline, width=4)
            line(draw, [(-48, -20), (-28, -27), (0, -32), (30, -28), (50, -22)], band, width=4)
            if look.skull:
                _skull(draw, (2, -43), 8.0, pal)
            return
        # A tricorn: three corners of a turned-up brim, and the crown in it.
        poly(draw, [(-19, -30), (-9, -57), (11, -58), (20, -31)], pal.hat, pal.outline, width=4)
        poly(draw, [(-50, -19), (-30, -37), (-10, -30), (4, -36), (20, -30), (36, -38),
                    (52, -21), (26, -22), (0, -27), (-26, -21)], pal.hat, pal.outline, width=4)
        line(draw, [(-46, -21), (-26, -24), (0, -30), (26, -25), (48, -22)], band, width=3)
        if look.skull:
            _skull(draw, (2, -44), 7.5, pal)


def _begin(draw, name: str) -> None:
    """Open a named component scope if ``draw`` records SVG; no-op for Pillow."""
    fn = getattr(draw, "begin_component", None)
    if fn is not None:
        fn(name)


def _end(draw) -> None:
    fn = getattr(draw, "end_component", None)
    if fn is not None:
        fn()


def draw_limb(draw, name: str, root, joint, end, fill, widths, ink, ink_width: int, cuff=None,
              end_cap: bool = True) -> None:
    """A two-bone limb (thigh and shin, upper arm and forearm) as two turned
    parts. Each bone is a sleeve with an ``ink`` line on its two sides, a
    round end and a side in shade. ``widths`` is the width at the root, at the
    joint and at the end. ``cuff`` is the colour of a band at the end of the
    lower bone. The lower bone starts square: the round end of the upper bone
    is the outside of the bend. ``end_cap`` is false for a leg: the boot is
    over the end of the shin, and a round end would come out under the sole.
    A part flipbook stores each bone once per length."""
    w0, w1, w2 = widths
    shade = _shade(fill, 0.78)
    for bone, a, b, wa, wb, start_cap in (
        ("upper", root, joint, w0, w1, True),
        ("lower", joint, end, w1, w2, False),
    ):
        length = round(math.hypot(b[0] - a[0], b[1] - a[1]), 2)
        deg = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        ha, hb = wa / 2.0, wb / 2.0
        with draw.part(f"{name}_{bone}", a, deg):
            if start_cap:
                circle(draw, (0.0, 0.0), ha, fill, ink, width=ink_width)
            if end_cap or bone == "upper":
                circle(draw, (length, 0.0), hb, fill, ink, width=ink_width)
            poly(draw, [(0.0, -ha), (length, -hb), (length, hb), (0.0, ha)], fill)
            poly(draw, [(0.0, -ha), (length, -hb), (length, -hb * 0.38), (0.0, -ha * 0.38)], shade)
            if cuff is not None and bone == "lower":
                poly(draw, [(length - 13.0, -hb - 1.0), (length - 1.0, -hb - 1.0),
                            (length - 1.0, hb + 1.0), (length - 13.0, hb + 1.0)],
                     cuff, ink, width=max(2, ink_width - 1))
            line(draw, [(0.0, -ha), (length, -hb)], ink, width=ink_width)
            line(draw, [(0.0, ha), (length, hb)], ink, width=ink_width)


def _draw_torso(draw, chest, global_tilt, pal, look: Look) -> None:
    """The coat or the jacket on the chest, the shirt in it and the belt. One
    rigid part in the frame of the chest."""
    b = look.build
    long_coat = look.coat == "long"
    coat_shade = _shade(pal.coat, 0.78)
    hem = 74 if long_coat else 52
    with draw.part("torso", chest, global_tilt):
        # Wide at the shoulders, in at the belt, out again under it.
        poly(draw, [(-42 * b, -14), (-30 * b, -29), (28 * b, -29), (40 * b, -14), (37 * b, 34),
                    (42 * b, hem - 6), (0, hem + 2), (-44 * b, hem - 6), (-39 * b, 34)],
             pal.coat, pal.outline, width=5)
        poly(draw, [(24 * b, -25), (37 * b, -12), (35 * b, 32), (39 * b, hem - 10), (26 * b, hem - 4)],
             coat_shade)
        # The shirt: a strip between the lapels of a coat, most of the chest
        # in an open jacket.
        sl, sr = (-13.0, 17.0) if long_coat else (-23.0 * b, 25.0 * b)
        poly(draw, [(sl, -25), (sr, -25), (sr - 3, 50), (sl - 3, 50)], pal.shirt, pal.outline, width=4)
        if look.stripes:
            for y in range(-14, 34, 13):
                poly(draw, [(sl + 2, y), (sr - 2, y), (sr - 2.4, y + 6), (sl + 1.6, y + 6)], pal.coat)
        if long_coat:
            # The lapels.
            poly(draw, [(-24, -27), (-5, -27), (-3, 10), (-13, 36), (-26, 12)],
                 pal.coat2, pal.outline, width=3)
            poly(draw, [(9, -27), (26, -27), (26, 12), (17, 36), (5, 10)],
                 pal.coat2, pal.outline, width=3)
            # A strap from the shoulder to the hip, with its buckle.
            strap = [(22 * b, -28), (34 * b, -22), (-30 * b, 36), (-38 * b, 28)]
            poly(draw, strap, pal.boots, pal.outline, width=3)
            poly(draw, rotated_rect_points((-2, 3), 12, 12, -42.0), pal.gold, pal.outline, width=2)
        else:
            # The two fronts of the jacket, open.
            poly(draw, [(-42 * b, -14), (-30 * b, -29), (-18 * b, -27), (-25 * b, 10), (-24 * b, 46), (-43 * b, 46), (-39 * b, 34)],
                 pal.coat, pal.outline, width=3)
            poly(draw, [(20 * b, -27), (28 * b, -29), (40 * b, -14), (37 * b, 34), (41 * b, 46), (26 * b, 46), (27 * b, 10)],
                 coat_shade, pal.outline, width=3)
        # The belt and its buckle.
        poly(draw, [(-41 * b, 35), (38 * b, 35), (40 * b, 48), (-43 * b, 48)],
             pal.sash, pal.outline, width=3)
        poly(draw, [(-8, 33), (8, 33), (8, 50), (-8, 50)], pal.gold, pal.outline, width=3)
        poly(draw, [(-3, 38), (3, 38), (3, 45), (-3, 45)], pal.sash)
        if look.epaulettes:
            for sx in (-1.0, 1.0):
                poly(draw, [(sx * 48 * b, -11), (sx * 45 * b, -27), (sx * 25 * b, -32), (sx * 23 * b, -19)],
                     pal.gold, pal.outline, width=3)
                for k in range(3):
                    x = sx * (30 + k * 7) * b
                    line(draw, [(x, -15 - k), (x + sx * 1.5, -6 - k)], pal.gold, width=3)


def paint_character(
    draw, kind: str, anim: str, frame_idx: int, nframes: int, frame_size=BASE_FRAME
) -> None:
    """Paint one supersampled character frame into ``draw``.

    ``draw`` is anything exposing the ImageDraw ``polygon`` / ``line`` /
    ``ellipse`` / ``arc`` subset — a real Pillow draw for raster output, or a
    :class:`~ambition_sprite2d_renderer.authoring.draw_recorder.DrawRecorder`
    to capture the same geometry as an editable SVG scene. The pirate family's
    whole vocabulary bottoms out in those calls, so one paint pass serves both.

    No drop shadow: a sprite has none in it (the rule of the project).
    """
    pal = PALETTES[kind]
    look = LOOKS[kind]
    b = look.build
    w, h = frame_size[0] * SCALE, frame_size[1] * SCALE
    pose = animation_pose(anim, frame_idx, nframes)

    global_tilt = pose["body_tilt"]

    # Joints come from the pirate's explicit skeleton (see _pirate_rig): the
    # animation lives on declared bones, and this paint pass places its parts
    # at the evaluated joints.
    joints = pirate_rig.evaluate(pose, kind, w, h, global_tilt)
    hip = joints["hip"].point
    chest = joints["chest"].point
    head_center = joints["head"].point
    back_shoulder = joints["back_shoulder"].point
    front_shoulder = joints["front_shoulder"].point

    # The back leg, then the front leg over it.
    _begin(draw, "legs")
    ground = pirate_rig.ground_y(h)
    death_t = pose["death_t"]
    for side, fill in (("left", _shade(pal.pants, 0.86)), ("right", pal.pants)):
        hip_pt = joints[f"{side}_hip"].point
        knee_pt = joints[f"{side}_knee"].point
        foot_pt = joints[f"{side}_foot"].point
        draw_limb(draw, "leg", hip_pt, knee_pt, foot_pt, fill,
                  (28 * b, 24 * b, 19 * b), pal.outline, 4, end_cap=False)
        # A foot on the ground is flat on it. A foot in the air goes with its
        # shin, and so do the feet of a body that is down.
        lifted = max(0.0, min(1.0, (ground - foot_pt[1]) / 14.0))
        draw_boot(draw, foot_pt, pose[f"{side}_shin"] * max(lifted, death_t), pal)
    # The seat of the trousers, between the two legs and under the coat.
    with draw.part("seat", hip, global_tilt):
        poly(draw, [(-29 * b, -20), (29 * b, -20), (29 * b, 8), (0, 16), (-29 * b, 8)],
             pal.pants, pal.outline, width=4)
    _end(draw)

    _begin(draw, "body")
    _draw_torso(draw, chest, global_tilt, pal, look)
    # The tails of a coat stop over the knees. A jacket has a short skirt.
    coat_sway = pose["coat_sway"]
    drop = 34.0 if look.coat == "long" else 6.0
    with draw.part("coat_tail_left", hip, global_tilt + coat_sway):
        poly(draw, [(-44 * b, -14), (-9, -14), (-11, drop - 8), (-38 * b, drop)],
             pal.coat, pal.outline, width=4)
    with draw.part("coat_tail_right", hip, global_tilt - coat_sway):
        poly(draw, [(9, -14), (42 * b, -14), (38 * b, drop), (10, drop - 8)],
             pal.coat, pal.outline, width=4)
        poly(draw, [(26 * b, -10), (39 * b, -10), (35 * b, drop - 4), (26 * b, drop - 6)],
             _shade(pal.coat, 0.78))
    _end(draw)

    # The two arms are in front of the body (Jon, 2026-10-10). The arm with no
    # sword is painted first: the sword arm is over it where they meet.
    _begin(draw, "arms")
    back_elbow = joints["back_elbow"].point
    back_hand = joints["back_hand"].point
    draw_limb(draw, "back_arm", back_shoulder, back_elbow, back_hand, pal.coat,
              (22 * b, 19 * b, 16 * b), pal.outline, 4, cuff=pal.coat2)
    with draw.part("back_hand", back_hand, 0.0):
        circle(draw, (0, 0), 9, pal.skin, pal.outline, width=3)
    _end(draw)

    # The arm with the sword, in front of the body.
    _begin(draw, "sword_arm")
    front_elbow = joints["front_elbow"].point
    front_hand = joints["front_hand"].point
    draw_limb(draw, "front_arm", front_shoulder, front_elbow, front_hand, pal.coat,
              (24 * b, 20 * b, 17 * b), pal.outline, 4, cuff=pal.coat2)
    blade = 92 if kind == "pirate_admiral" else 86
    curve = 16 if kind in SCARFED_KINDS else 5
    draw_sword(draw, front_hand, pose["weapon"], blade, pal, curve=curve)
    # The hand is over the grip of the sword.
    with draw.part("front_hand", front_hand, 0.0):
        circle(draw, (0, 0), 10, pal.skin, pal.outline, width=3)
    if anim == "slash" and frame_idx in _SWOOSH:
        # The path of the blade in the air: a part of a circle about the
        # shoulder, from where the blade was to where it is.
        start, end = _SWOOSH[frame_idx]
        reach = 150.0
        arc_box = (front_shoulder[0] - reach, front_shoulder[1] - reach,
                   front_shoulder[0] + reach, front_shoulder[1] + reach)
        draw.arc(arc_box, start=start, end=end, fill=(255, 245, 200, 180), width=8)
        draw.arc(arc_box, start=start + 8, end=end - 6, fill=(255, 255, 255, 120), width=4)
    elif anim in {"idle", "walk", "taunt"} and frame_idx % 2 == 0:
        blade_tip = transform((blade, curve), front_hand, pose["weapon"])
        with draw.part("glint", blade_tip, 0.0):
            line(draw, [(0, 0), (10, -8)], (255, 255, 255, 100), width=2)
    _end(draw)

    # The head is on the neck: it turns with the bone that carries it.
    _begin(draw, "head")
    face_tilt = joints["head"].angle
    draw_hair(draw, head_center, face_tilt, pal, look)
    draw_neck(draw, chest, head_center, global_tilt, pal, look)
    draw_face(
        draw,
        head_center,
        face_tilt,
        pal,
        look,
        x_eyes=pose["x_eyes"],
        blink=pose["blink"],
        mouth_open=pose["mouth_open"],
    )
    draw_hat(draw, head_center, face_tilt + pose["hat_tilt"], pal, look)
    _end(draw)

    # NOT dead code: an alpha-0 stroke is an ERASER through blending_draw (its
    # zero-alpha ops carve rather than no-op), so this clears a 1px seam just
    # below the feet on the death settle.
    if anim == "death":
        ground = h * 0.83
        draw.line((0, ground + 24, w, ground + 24), fill=(0, 0, 0, 0), width=1)


# ── the sheet: a rig at one scale ────────────────────────────────────────────
#
# ``draw_character`` fits each frame by its own extent (``downsample``): the
# pirate shrank and slid as his sword swung, and no part could be shared
# between frames (each was resized by its frame's own scale). The SHEET is
# drawn by ``draw_rig_frame`` instead: every frame of a pirate at ONE scale and
# ONE place, painted on a canvas ``RIG_REDUCTION`` times the frame and reduced
# by exactly that, each ``part()`` painted once and turned into place
# (``_PiecePartDraw``). A part flipbook then stores each part once.

#: The sheet's whole reduction.
RIG_REDUCTION = 3
#: The sheet frame for a ``BASE_FRAME`` request: it holds each frame of each
#: pirate at the scale of the idle pose, with a margin of 5 px or more. Measured
#: 2026-10-10, after the poses were made again, about the anchor below: 113 px
#: to the back (the death), 91 to the front (the strike), 140 up (the sword
#: over the head), 11 down (the boots).
RIG_FRAME = (220, 164)
#: Where the idle pose's box centre (x) and feet (y) land in ``RIG_FRAME``.
RIG_IDLE_ANCHOR = (118.0, 148.0)

#: (kind, frame size) -> (scale, offset): a paint point ``p`` lands at
#: ``p * scale + offset`` on the reduction canvas.
_RIG_FITS: Dict[Tuple[str, Tuple[int, int]], Tuple[float, Tuple[float, float]]] = {}


def rig_frame_size(frame_size=BASE_FRAME) -> Tuple[int, int]:
    """The sheet frame ``draw_rig_frame`` paints for a ``frame_size`` request."""
    return (
        round(RIG_FRAME[0] * frame_size[0] / BASE_FRAME[0]),
        round(RIG_FRAME[1] * frame_size[1] / BASE_FRAME[1]),
    )


def _rig_fit(kind: str, frame_size=BASE_FRAME) -> Tuple[float, Tuple[float, float]]:
    """The one scale and offset of every sheet frame of ``kind``: the idle
    pose at the size the old per-frame fit gave it (its box 78% of the frame's
    width or 88% of its height), its box centre and feet at
    ``RIG_IDLE_ANCHOR``."""
    key = (kind, tuple(frame_size))
    if key not in _RIG_FITS:
        from ...authoring.draw_recorder import PillowPartDraw

        w, h = frame_size[0] * SCALE, frame_size[1] * SCALE
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        paint_character(PillowPartDraw(blending_draw(img)), kind, "idle", 0, 6, frame_size)
        x1, y1, x2, y2 = img.getchannel("A").getbbox()
        fw, fh = frame_size
        k = RIG_REDUCTION
        scale = k * min(fw * 0.78 / (x2 - x1), fh * 0.88 / (y2 - y1))
        ax = RIG_IDLE_ANCHOR[0] * fw / BASE_FRAME[0]
        ay = RIG_IDLE_ANCHOR[1] * fh / BASE_FRAME[1]
        _RIG_FITS[key] = (scale, (ax * k - (x1 + x2) / 2.0 * scale, ay * k - y2 * scale))
    return _RIG_FITS[key]


def _rig_fit_map(kind: str, frame_size=BASE_FRAME) -> dict:
    """``_rig_fit`` in ``downsample``'s ``fit_out`` form: a paint point ``p``
    lands at ``((p.x - x0) * sx + ox, (p.y - y0) * sy + oy)`` in the frame."""
    scale, (ox, oy) = _rig_fit(kind, frame_size)
    k = RIG_REDUCTION
    w, h = rig_frame_size(frame_size)
    return {"x0": 0.0, "y0": 0.0, "x1": (w * k - ox) / scale, "y1": (h * k - oy) / scale,
            "sx": scale / k, "sy": scale / k, "nw": w, "nh": h, "ox": ox / k, "oy": oy / k}


class _PiecePartDraw:
    """``PillowPartDraw``'s twin for the sheet: each ``part()`` scope is painted
    ONCE in its own frame (cached by its calls) and placed turned through
    ``shape_rig``, so a part flipbook stores it once. Calls outside a scope are
    drawn as shapes. Every point is scaled by ``scale`` and moved by
    ``offset``; every stroke width is scaled.

    An alpha-0 stroke (the death pose's eraser line) is not drawn: a part
    flipbook cannot replay an eraser, and a rig needs none."""

    #: (name, scale, calls) -> (raster, pivot).
    _parts: Dict[tuple, Tuple[Image.Image, Tuple[float, float]]] = {}

    def __init__(self, img: Image.Image, scale: float, offset: Tuple[float, float]) -> None:
        self._img = img
        self._draw = blending_draw(img)
        self._scale = scale
        self._off = offset
        self._calls: Optional[list] = None
        self._names: Dict[str, int] = {}

    # -- scopes --------------------------------------------------------------
    @contextmanager
    def part(self, name: str, origin, deg: float = 0.0):
        assert self._calls is None, "nested part()"
        self._calls = []
        try:
            yield self
        finally:
            calls, self._calls = self._calls, None
            self._place(name, calls, origin, deg)

    def begin_component(self, name: str) -> None:
        del name

    def end_component(self) -> None:
        pass

    def _place(self, name: str, calls: list, origin, deg: float) -> None:
        from ...authoring import shape_rig

        key = (name, round(self._scale, 6), repr(calls))
        part = self._parts.get(key)
        if part is None:
            reach = 8.0
            for _op, args, kwargs in calls:
                reach = max(reach, max(abs(v) for v in _flat(args[0])) * self._scale + float(kwargs.get("width") or 1) + 4.0)
            size = int(math.ceil(2 * reach))
            local = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = blending_draw(local)
            for op, args, kwargs in calls:
                getattr(draw, op)(_moved(args[0], self._scale, reach, reach), *args[1:], **kwargs)
            box = local.getchannel("A").getbbox() or (0, 0, 1, 1)
            part = (local.crop(box), (reach - box[0], reach - box[1]))
            self._parts[key] = part
        count = self._names.get(name, 0) + 1
        self._names[name] = count
        at = (float(origin[0]) * self._scale + self._off[0], float(origin[1]) * self._scale + self._off[1])
        shape_rig.place(self._img, part, at, float(deg), name if count == 1 else f"{name}_{count}")

    # -- primitives ----------------------------------------------------------
    def _op(self, op: str, xy, *args, **kwargs) -> None:
        fill = kwargs.get("fill")
        if op == "line" and isinstance(fill, tuple) and len(fill) == 4 and fill[3] == 0:
            return
        if "width" in kwargs and kwargs["width"]:
            kwargs["width"] = max(1, int(round(kwargs["width"] * self._scale)))
        if self._calls is not None:
            self._calls.append((op, (_points(xy),) + args, kwargs))
        else:
            getattr(self._draw, op)(_moved(_points(xy), self._scale, *self._off), *args, **kwargs)

    def polygon(self, xy, fill=None, outline=None, width=1):
        if outline is None:
            self._op("polygon", xy, fill=fill)
        else:
            self._op("polygon", xy, fill=fill, outline=outline, width=width)

    # Strokes end ROUND, as the SVG capture strokes them (``DrawRecorder``
    # emits ``stroke-linecap="round"``): with one scale for every frame, a
    # square end against a round one moves the sheet's box by a pixel. An
    # opaque stroke gets a disc at each end; a translucent one is filled as
    # its outline (a disc over it would darken the end).

    def line(self, xy, fill=None, width=1, joint=None):
        pts = _points(xy)
        if _translucent(fill) and len(pts) == 2 and width >= 2:
            self._op("polygon", _capsule_outline(pts[0], pts[1], width / 2.0), fill=fill)
            return
        self._op("line", xy, fill=fill, width=width, joint=joint)
        # Outside a part only the neck's throat line is stroked, inside the
        # neck: its ends need no disc (each disc would be one more shape).
        if self._calls is not None and width >= 2 and len(pts) >= 2 and not (isinstance(fill, tuple) and len(fill) == 4 and fill[3] == 0):
            r = width / 2.0
            for x, y in (pts[0], pts[-1]):
                self._op("ellipse", (x - r, y - r, x + r, y + r), fill=fill)

    def ellipse(self, xy, fill=None, outline=None, width=1):
        self._op("ellipse", xy, fill=fill, outline=outline, width=width)

    def arc(self, xy, start, end, fill=None, width=1):
        if _translucent(fill):
            self._op("polygon", _arc_outline(_points(xy), start, end, width / 2.0), fill=fill)
            return
        self._op("arc", xy, start=start, end=end, fill=fill, width=width)


def _translucent(fill) -> bool:
    return isinstance(fill, tuple) and len(fill) == 4 and 0 < fill[3] < 255


def _capsule_outline(a, b, r: float, steps: int = 8) -> List[Tuple[float, float]]:
    """The outline of a stroke from ``a`` to ``b`` of half width ``r`` with
    round ends."""
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    pts = []
    for centre, base in ((b, ang - math.pi / 2), (a, ang + math.pi / 2)):
        for i in range(steps + 1):
            t = base + math.pi * i / steps
            pts.append((centre[0] + r * math.cos(t), centre[1] + r * math.sin(t)))
    return pts


def _arc_outline(box, start: float, end: float, r: float, steps_per_degree: float = 0.25) -> List[Tuple[float, float]]:
    """The outline of Pillow's elliptical arc stroke (``box``, degrees
    clockwise from +x) of half width ``r`` with round ends."""
    x0, y0, x1, y1 = box
    cx, cy, rx, ry = (x0 + x1) / 2.0, (y0 + y1) / 2.0, abs(x1 - x0) / 2.0, abs(y1 - y0) / 2.0
    sweep = (end - start) % 360 or 360.0
    n = max(2, int(sweep * steps_per_degree))
    angles = [math.radians(start + sweep * i / n) for i in range(n + 1)]
    outer = [(cx + (rx + r) * math.cos(a), cy + (ry + r) * math.sin(a)) for a in angles]
    inner = [(cx + (rx - r) * math.cos(a), cy + (ry - r) * math.sin(a)) for a in reversed(angles)]

    def cap(a: float, forward: bool) -> List[Tuple[float, float]]:
        px, py = cx + rx * math.cos(a), cy + ry * math.sin(a)
        base = a if forward else a + math.pi
        return [(px + r * math.cos(base + math.pi * i / 8), py + r * math.sin(base + math.pi * i / 8)) for i in range(1, 8)]

    return outer + cap(angles[-1], True) + inner + cap(angles[0], False)


def _points(xy) -> tuple:
    """``xy`` as a tuple of ``(x, y)`` pairs, or a flat bbox kept flat."""
    if xy and isinstance(xy[0], (int, float)):
        values = tuple(float(v) for v in xy)
        return values if len(values) == 4 else tuple(zip(values[0::2], values[1::2]))
    return tuple((float(p[0]), float(p[1])) for p in xy)


def _flat(points) -> List[float]:
    if points and isinstance(points[0], (int, float)):
        return list(points)
    return [v for p in points for v in p]


def _moved(points, scale: float, dx: float, dy: float):
    if points and isinstance(points[0], (int, float)):
        x0, y0, x1, y1 = points
        return (x0 * scale + dx, y0 * scale + dy, x1 * scale + dx, y1 * scale + dy)
    return [(x * scale + dx, y * scale + dy) for x, y in points]


def draw_rig_frame(
    kind: str,
    anim: str,
    frame_idx: int,
    nframes: int,
    frame_size=BASE_FRAME,
    fit_out: Optional[dict] = None,
) -> Image.Image:
    """One SHEET frame of ``kind`` (``rig_frame_size(frame_size)``): painted as
    a rig at the kind's one scale on a canvas ``RIG_REDUCTION`` times the
    frame, and reduced by exactly that. ``fit_out`` receives the
    paint-to-frame map (``_rig_fit_map``)."""
    k = RIG_REDUCTION
    out = rig_frame_size(frame_size)
    scale, offset = _rig_fit(kind, frame_size)
    img = Image.new("RGBA", (out[0] * k, out[1] * k), (0, 0, 0, 0))
    paint_character(_PiecePartDraw(img, scale, offset), kind, anim, frame_idx, nframes, frame_size)
    if fit_out is not None:
        fit_out.update(_rig_fit_map(kind, frame_size))
    return downsample_whole(img, out)


def _rig_frame_from_svg(kind: str, svg: str, frame_size=BASE_FRAME) -> Image.Image:
    """A paint-space SVG frame of ``kind`` rasterized and reduced exactly as
    ``draw_rig_frame`` paints and reduces it (``_rig_fit``): the SVG
    authority's sheet frame. Only the rasterizer differs."""
    import re

    from ...authoring.draw_recorder import rasterize_svg

    scale, (ox, oy) = _rig_fit(kind, frame_size)
    k = RIG_REDUCTION
    out = rig_frame_size(frame_size)
    w, h = out[0] * k, out[1] * k
    view = f'viewBox="{-ox / scale:.6f} {-oy / scale:.6f} {w / scale:.6f} {h / scale:.6f}"'
    svg = re.sub(r'width="[^"]*" height="[^"]*" viewBox="[^"]*"', f'width="{w}px" height="{h}px" {view}', svg, count=1)
    return downsample_whole(rasterize_svg(svg, (w, h)), out)


def downsample_whole(img: Image.Image, size: Tuple[int, int]) -> Image.Image:
    """``img`` reduced to ``size`` by the rig's whole factor: each frame pixel
    the mean of its ``RIG_REDUCTION`` square. A box has no negative lobe, so
    no faint ring lands past the art to move the sheet's measured box."""
    from ...authoring import rigdoc

    return rigdoc.downsampled_canvas(img, tuple(size), Image.Resampling.BOX)


def draw_character(
    kind: str,
    anim: str,
    frame_idx: int,
    nframes: int,
    frame_size=BASE_FRAME,
    fit_out: Optional[dict] = None,
) -> Image.Image:
    """Render one supersampled-then-downsampled pirate frame (PIL raster).

    ``fit_out`` receives the frame's paint-to-frame map (see ``downsample``).
    """
    from ...authoring.draw_recorder import PillowPartDraw

    w, h = frame_size[0] * SCALE, frame_size[1] * SCALE
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = PillowPartDraw(blending_draw(img))
    paint_character(draw, kind, anim, frame_idx, nframes, frame_size)
    return downsample(img, frame_size, fit_out=fit_out)


def capture_character_svg(
    kind: str, anim: str, frame_idx: int, nframes: int, frame_size=BASE_FRAME
) -> str:
    """Capture one pirate frame as an SVG document — the PIL->SVG conversion.

    Paints the identical parts into a :class:`DrawRecorder` at the supersampled
    resolution instead of a raster. Rasterizing the result and downsampling it
    the same way ``draw_character`` does lands within antialiasing tolerance of
    the shipped frame (``raster-equivalent`` in the equivalence harness). See
    ``docs/planning/engine/svg-component-character-migration.md``.
    """
    from ...authoring.draw_recorder import DrawRecorder

    w, h = frame_size[0] * SCALE, frame_size[1] * SCALE
    rec = DrawRecorder((w, h))
    paint_character(rec, kind, anim, frame_idx, nframes, frame_size)
    return rec.to_svg()


def render_target(
    target: str, out_dir: Path, frame_size: Tuple[int, int] = BASE_FRAME
) -> Dict[str, Path]:
    """Build a pirate-family character sheet via the parametric rig.

    Thin shim used by the 5 pirate character modules so their per-target
    ``render()`` is one line. Delegates to `sheet_build.build_sheet`
    with `draw_character(target, ...)` as the per-frame renderer.

    Returns the dict that ``build_sheet`` produced — callers flatten it
    into the ``list[Path]`` shape that the tack-on discovery API
    expects.
    """
    return render_target_with_products(target, out_dir, frame_size)[0]


def render_target_with_products(
    target: str, out_dir: Path, frame_size: Tuple[int, int] = BASE_FRAME
):
    """``render_target``, and also the products it published beside the sheet:
    ``{"body_rig": BodyRigProduct, "parts": PartFlipbook}``, empty when the
    build published none (a canonical-only build).

    Both are placed through the same frame maps as the sheet's pixels."""
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    frame_fits: Dict[Tuple[str, int], dict] = {}

    def render_fn(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        fit: dict = {}
        frame = draw_rig_frame(target, anim, frame_idx, nframes, frame_size=frame_size, fit_out=fit)
        frame_fits[(anim, frame_idx)] = fit
        return frame

    outputs = build_sheet(
        target=target,
        rows=ANIMATIONS,
        render_fn=render_fn,
        out_dir=out_dir,
        frame_size=rig_frame_size(frame_size),
        # The frame is the rig's (``RIG_FRAME``), not fitted to the art: the
        # SVG authority publishes the same frame whatever its rasterizer.
        auto_crop=False,
        frame_transform_out=frame_transform,
    )
    # The semantic body rig, from the skeleton the frames above were painted
    # on, placed through each frame's own fit into the published frame the
    # sheet measured its feet in.
    if not frame_transform:
        return outputs, {}
    import yaml

    from ._pirate_body_rig import body_rig_for_pirate

    metrics = yaml.safe_load(Path(outputs["yaml"]).read_text()).get("body_metrics") or {}
    feet = metrics.get("feet_pixel")
    if not feet:
        return outputs, {}
    feet_xy = (float(feet["x"]), float(feet["y"]))
    product = body_rig_for_pirate(target, frame_fits, frame_transform, feet_xy, frame_size)
    outputs["body_rig"] = product.write(out_dir)
    # The part flipbook, recorded as each frame is painted: every shape cut
    # and resized by the frame's own fit (``downsample``), placed as the sheet
    # placed the frame.
    from ...authoring.part_flipbook import PartFlipbook, publish_rig_flipbook

    for name, path in publish_rig_flipbook(target, ANIMATIONS, render_fn, outputs, frame_transform, out_dir).items():
        outputs["parts" if name == "ron" else name] = path
    if "parts" not in outputs:
        # A quality tier's render: its flipbook is derived, not recorded.
        return outputs, {"body_rig": product}
    return outputs, {"body_rig": product, "parts": PartFlipbook.from_published(Path(outputs["parts"]))}


def is_pirate_family(target: str) -> bool:
    """True when ``target`` is drawn by this family's parametric rig."""
    return target in PALETTES


def build_scene(target: str, frame_size: Tuple[int, int] = BASE_FRAME):
    """Capture every frame and fold them into ONE component scene.

    Parts (hat, face variants, torso, boots, sword, coat tails, chest motif)
    register once each; frames become ``<use>`` placements plus the dynamic
    limb/neck geometry. The scene is the editable Inkscape artifact.
    """
    from ...authoring.draw_recorder import DrawRecorder
    from ...authoring.svg_scene import ComponentScene

    w, h = frame_size[0] * SCALE, frame_size[1] * SCALE
    recorders = {}
    for anim, nframes, _ms in ANIMATIONS:
        for i in range(nframes):
            rec = DrawRecorder((w, h))
            paint_character(rec, target, anim, i, nframes, frame_size)
            recorders[(anim, i)] = rec
    return ComponentScene.from_recorders((w, h), recorders)


def export_scene(
    target: str, path: Path, frame_size: Tuple[int, int] = BASE_FRAME
) -> Path:
    """Write the target's editable component scene SVG to ``path``."""
    return build_scene(target, frame_size).save(Path(path))


def render_target_svg(
    target: str,
    out_dir: Path,
    frame_size: Tuple[int, int] = BASE_FRAME,
    scene_path: Path | None = None,
) -> Dict[str, Path]:
    """Build the same pirate sheet from the **SVG authority**.

    Every frame is assembled from the component scene's registered parts and
    rasterized and reduced as the raster sheet is (``_rig_frame_from_svg``),
    then routed through the same ``build_sheet`` measurement /
    packing / metadata pipeline. With ``scene_path`` the scene is loaded from
    disk instead of captured fresh — that is the human-in-the-loop path: edit
    the parts in Inkscape, rebuild the sheet from the edited file, and let the
    equivalence harness report what changed.
    """
    from ...authoring.svg_scene import ComponentScene

    out_dir.mkdir(parents=True, exist_ok=True)
    if scene_path is not None:
        scene = ComponentScene.load(Path(scene_path))
        missing = scene.missing_part_refs()
        if missing:
            raise ValueError(
                f"scene {scene_path} has dangling part references: {missing}")
    else:
        scene = build_scene(target, frame_size)

    def render_fn(anim, frame_idx, nframes):
        del nframes
        return _rig_frame_from_svg(target, scene.frame_doc(anim, frame_idx), frame_size)

    return build_sheet(
        target=target,
        rows=ANIMATIONS,
        render_fn=render_fn,
        out_dir=out_dir,
        frame_size=rig_frame_size(frame_size),
        auto_crop=False,
    )


# ── portraits ─────────────────────────────────────────────────────────────────
#
# ⛔⛔ WITHOUT THIS THE PIRATE PORTRAIT IS AN UPSCALE. A target with no native
# hook gets `Target.render_portraits`' fallback, which crops the CANONICAL
# raster -- one BASE_FRAME-sized render -- and blows it up to 256x320. Every
# pirate published a soft face for that reason and no other; the painter itself
# has always been resolution-independent.
#
# ⭐ AND THE HEAD IS ASKED FOR, NOT GUESSED. `_pirate_rig` evaluates a real
# skeleton, so `joints["head"]` is where the face is at any frame size. Seven
# pirates share one parametric rig, so one number serves all of them and none of
# them needs a hand-placed guide.

#: Render the portrait source at this multiple of the gameplay frame. The head
#: is about a quarter of the frame's width, so anything less than this crops a
#: sub-256px face and `render_framed_portrait` UPSCALES it -- which is the exact
#: defect this whole hook exists to remove. Measured: at 3x the crop was 96px
#: wide and published blockier than the fallback it replaced.
PIRATE_PORTRAIT_SCALE = 10
#: Fraction of the silhouette's height that is head-and-hat, used to isolate the
#: head band for measurement.
PIRATE_HEAD_BAND = 0.22


def pirate_face_guide(kind: str, anim: str = "idle", frame_idx: int = 0,
                      nframes: int = 1, frame_size=BASE_FRAME):
    """Where this pirate's head is, MEASURED on a render of him.

    ⛔ NOT `joints["head"]`. The rig has a head joint and it is not the drawn
    head's centre -- on the Admiral it reports y=56 of 128 while the painted head
    sits at y=13, because the joint is a socket the parts hang from rather than
    the middle of a face. Aiming a portrait at it framed his CHEST.

    So the head is taken off the silhouette: the top band of the alpha, whose
    bounding box is the hat and the face together. That is what a viewer calls
    the head, and it needs no per-pirate number.
    """
    import numpy as np

    from ...authoring.portrait import FaceGuide

    image = draw_character(kind, anim, frame_idx, nframes, frame_size=frame_size)
    alpha = np.array(image.getchannel("A")) > 8
    ys, xs = alpha.nonzero()
    if not len(ys):
        raise ValueError(f"{kind}: rendered empty, nothing to aim a portrait at")
    top, bottom = int(ys.min()), int(ys.max())
    band = ys < top + (bottom - top) * PIRATE_HEAD_BAND
    bx0, bx1 = int(xs[band].min()), int(xs[band].max())
    by0, by1 = int(ys[band].min()), int(ys[band].max())
    return FaceGuide(
        center_x=(bx0 + bx1) / 2.0,
        center_y=(by0 + by1) / 2.0,
        width=float(bx1 - bx0),
        height=float(by1 - by0),
        source_width=float(frame_size[0]),
        source_height=float(frame_size[1]),
    )


def render_pirate_portraits(target: str, out_dir, *, kind: str | None = None,
                            stills=None, quality_scale=None):
    """Portrait frames painted at portrait resolution, not cropped off a sheet."""
    from pathlib import Path

    from ...authoring.portrait import (
        DEFAULT_PORTRAIT_SIZE,
        PortraitClip,
        render_framed_portrait,
        write_portrait_sheet,
    )

    # ⛔ A QUALITY TIER SCALES THE PORTRAIT TOO -- see the rigged fighters' hook.
    q = float(quality_scale) if quality_scale else 1.0
    output_size = (max(8, round(DEFAULT_PORTRAIT_SIZE[0] * q)),
                   max(8, round(DEFAULT_PORTRAIT_SIZE[1] * q)))

    kind = kind or target
    big = (BASE_FRAME[0] * PIRATE_PORTRAIT_SCALE, BASE_FRAME[1] * PIRATE_PORTRAIT_SCALE)

    # Measured ONCE, on the pose the portrait sits in: a guide that moved per
    # frame would make the idle breathe by sliding the camera.
    guide = pirate_face_guide(kind, ANIMATIONS[0][0], 0, ANIMATIONS[0][1])
    # Head and shoulders. The measured band is the hat and face together, so the
    # view is only a little wider than it and drops far enough for a collar.
    view_width = guide.width * 1.95
    center_y = guide.center_y + guide.height * 0.88

    def frame(anim: str, index: int, count: int):
        source = draw_character(kind, anim, index, count, frame_size=big)
        return render_framed_portrait(
            source, guide, output_size=output_size,
            view_width=view_width, center_y=center_y
        )

    idle = next((name for name, *_rest in ANIMATIONS if name == "idle"), ANIMATIONS[0][0])
    count = next(n for name, n, *_r in ANIMATIONS if name == idle)
    clips = {
        "default": PortraitClip.loop(
            tuple(frame(idle, i, count) for i in range(count)), duration_ms=count * 120
        ),
        "portrait": PortraitClip.still(frame(idle, count // 3, count)),
    }
    for name, (anim, index) in (stills or {}).items():
        rows = next(n for a, n, *_r in ANIMATIONS if a == anim)
        clips[name] = PortraitClip.still(frame(anim, index, rows))
    return write_portrait_sheet(target, clips, Path(out_dir), still_clip="portrait")
