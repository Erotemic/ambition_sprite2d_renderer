"""The pirate heavies: three big women of one crew, drawn from one template.

This target does NOT go through the pirate-family draw_character rig (see
_pirate_common.draw_character). It uses build_sheet for the sheet layout
and its own rig: the skeleton is _pirate_heavy_rig (two-bone IK to the
hands and the feet), the poses are pose_for, and each rigid part is one
piece (see "Pieces").

The three (VARIANTS) share the skeleton, the poses and the painters. A
VariantSpec gives each her build, her palette, and one of each kind of
thing she wears: what is on her head, how her hair is, her mark, the blade of
her cleaver.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ...authoring.portrait import (
    PortraitClip,
    render_canonical_portrait,
    write_portrait_sheet,
)
from ambition_sprite2d_renderer.core.draw import blending_draw
from . import _pirate_heavy_rig as rig
from ._pirate_heavy_rig import (
    FOREARM,
    HAFT_BACK,
    HIP_Y,
    SHIN,
    SHOULDER,
    THIGH,
    UPPER_ARM,
    evaluate as _rig_evaluate,
)

ACTOR_METADATA = {
    "actor": {"character_id": "npc_pirate_heavy", "display_name": "Pirate Heavy"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "traits": ["enemy", "combatant", "pirate", "heavy"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": None,
            "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "melee_brute_brute"},
    "actions": {"default_preset": "brute_lunge"},
    "visual": {"default_pose": "idle"},
    "tags": ["story", "humanoid", "enemy", "combatant", "pirate", "heavy"],
    "sockets": {
        "head": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 24.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 54.0},
        },
        "hand_l": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 48.0, "y": 64.0},
        },
        "hand_r": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 80.0, "y": 64.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 8.0},
        },
        "weapon_grip": {
            "source": "explicit.profile.combat_humanoid",
            "point": {"x": 80.0, "y": 64.0},
        },
        "weapon_tip": {
            "source": "explicit.profile.combat_humanoid",
            "point": {"x": 104.0, "y": 60.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {
                    "t": 0.34,
                    "event": "hitbox_active_start",
                    "source": "explicit.profile.combat_humanoid",
                },
                {
                    "t": 0.58,
                    "event": "hitbox_active_end",
                    "source": "explicit.profile.combat_humanoid",
                },
            ],
        },
    },
}


RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

BASE_TARGET_NAME = "pirate_heavy"
# Output (post-downsample) frame resolution. Heavy pirate bruisers render larger
# on screen than a normal character, so the texture needs more native pixels to
# stay crisp (a normal character ships at a 256 native frame). Geometry is
# authored in WORK_FRAME_SIZE units and supersampled by SUPER (=6).
FRAME_SIZE = (640, 576)
WORK_FRAME_SIZE = (640, 576)
SUPER = 6
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("walk", 8, 95),
    ("slash", 7, 80),
    ("taunt", 6, 110),
    ("hurt", 4, 90),
    ("death", 8, 110),
]

OUTLINE = (20, 16, 18, 255)
METAL = (194, 202, 206, 255)
METAL_DARK = (104, 111, 118, 255)
RIVET = (60, 64, 70, 255)
GOLD = (232, 183, 68, 255)
TEETH = (250, 244, 220, 255)
#: The game's contract for a hand that holds an item
#: (`rendering::posed_hand::ITEM_REST_ANGLE`): a hand part that is not turned
#: holds an item that points the way she faces and this many degrees up.
ITEM_REST_ANGLE = 24.0
WOOD = (96, 60, 38, 255)
WHITE = (255, 255, 255, 255)
SLASH = (255, 246, 214, 255)


@dataclass(frozen=True)
class Palette:
    skin: RGBA
    skin_shadow: RGBA
    hair: RGBA
    hair_hi: RGBA
    bandana: RGBA
    bandana_dark: RGBA
    shirt: RGBA
    bodice: RGBA
    bodice_hi: RGBA
    skirt: RGBA
    skirt_hi: RGBA
    sash: RGBA
    boot: RGBA
    boot_hi: RGBA
    iris: RGBA = (226, 160, 44, 255)
    lip: RGBA = (158, 44, 62, 255)
    hat: RGBA = (36, 32, 46, 255)
    slash: RGBA = SLASH


@dataclass(frozen=True)
class VariantSpec:
    """One heavy. The three are one template: the same skeleton, the same
    poses, the same painters. A variant changes the build (the scales), and it
    picks one of each kind of thing she wears."""

    slug: str
    display_name: str
    palette: Palette
    # the build: each is a scale of the template
    shoulder: float = 1.0
    bust: float = 1.0
    waist: float = 1.0
    hip: float = 1.0
    arm: float = 1.0
    head: float = 1.0
    tall: float = 1.0
    # what she wears
    headwear: str = "bandana"  # "bandana", "tricorn" or "band"
    hair: str = "dreads"  # "dreads", "braid" or "waves"
    mark: str = "pauldron"  # "pauldron", "bandolier" or "neckerchief"
    # "slab", "ports", "hook", or "none": no cleaver in the art, because she
    # holds an item that the GAME draws (Iron Mary's gun-sword). The game draws
    # a held item in the hand of the pose that is drawn: it reads the track
    # `right_hand` of the part flipbook each frame, where the hand is and how
    # it is turned (see "The hands" in `_draw_variant`).
    blade: str = "slab"
    bracer: str = "iron"  # "iron", "leather" or "rope"
    striped_sleeves: bool = False
    # the small things of her face
    cheek_scar: bool = False
    nose_ring: bool = False
    hair_beads: bool = False
    necklace: bool = False
    beauty_mark: bool = False
    brow_notch: bool = False
    freckles: bool = False
    gold_tooth: bool = False


VARIANTS: Dict[str, VariantSpec] = {
    # A tricorn with a red plume, one thick braid, a bandolier of charges, and
    # a cleaver with three gun ports. The widest of the three.
    "broadside_bess": VariantSpec(
        slug="broadside_bess",
        display_name="Broadside Bess",
        palette=Palette(
            skin=(165, 105, 72, 255),
            skin_shadow=(106, 61, 43, 255),
            hair=(46, 28, 24, 255),
            hair_hi=(92, 58, 42, 255),
            bandana=(190, 36, 58, 255),
            bandana_dark=(120, 20, 38, 255),
            shirt=(235, 220, 190, 255),
            bodice=(88, 34, 46, 255),
            bodice_hi=(150, 70, 78, 255),
            skirt=(42, 68, 100, 255),
            skirt_hi=(72, 112, 154, 255),
            sash=(225, 170, 60, 255),
            boot=(57, 38, 29, 255),
            boot_hi=(98, 61, 38, 255),
            iris=(132, 176, 92, 255),
            lip=(172, 52, 50, 255),
        ),
        shoulder=1.05,
        bust=1.1,
        waist=1.2,
        hip=1.14,
        arm=1.1,
        tall=0.97,
        headwear="tricorn",
        hair="braid",
        mark="bandolier",
        blade="ports",
        bracer="leather",
        necklace=True,
        gold_tooth=True,
    ),
    # A red bandana over a mane of dreads, an iron shoulder. She rides a shark
    # and she holds a gun-sword, which the game draws in her lead hand.
    "iron_mary": VariantSpec(
        slug="iron_mary",
        display_name="Iron Mary",
        palette=Palette(
            skin=(114, 78, 54, 255),
            skin_shadow=(73, 47, 31, 255),
            hair=(38, 24, 18, 255),
            hair_hi=(78, 51, 34, 255),
            bandana=(160, 26, 46, 255),
            bandana_dark=(98, 16, 30, 255),
            shirt=(236, 226, 196, 255),
            bodice=(46, 34, 53, 255),
            bodice_hi=(107, 82, 118, 255),
            skirt=(52, 88, 73, 255),
            skirt_hi=(84, 129, 109, 255),
            sash=(214, 164, 58, 255),
            boot=(54, 34, 26, 255),
            boot_hi=(88, 58, 40, 255),
        ),
        blade="none",
        cheek_scar=True,
        nose_ring=True,
        necklace=True,
        brow_notch=True,
        hair_beads=True,
        gold_tooth=True,
    ),
    # A rose band in long red hair, striped sleeves, a sailor's neckerchief, a
    # cleaver with a hooked point. The tallest and the leanest of the three.
    "salt_annet": VariantSpec(
        slug="salt_annet",
        display_name="Salt Annet",
        palette=Palette(
            skin=(214, 158, 122, 255),
            skin_shadow=(150, 100, 72, 255),
            hair=(146, 58, 30, 255),
            hair_hi=(204, 108, 56, 255),
            bandana=(176, 58, 92, 255),
            bandana_dark=(116, 34, 60, 255),
            shirt=(244, 234, 208, 255),
            bodice=(34, 80, 90, 255),
            bodice_hi=(84, 146, 150, 255),
            skirt=(186, 166, 130, 255),
            skirt_hi=(224, 208, 174, 255),
            sash=(48, 86, 118, 255),
            boot=(69, 43, 29, 255),
            boot_hi=(111, 72, 44, 255),
            iris=(108, 170, 214, 255),
            lip=(196, 84, 96, 255),
        ),
        shoulder=0.94,
        bust=0.95,
        waist=0.9,
        hip=0.95,
        arm=0.9,
        tall=1.06,
        headwear="band",
        hair="waves",
        mark="neckerchief",
        blade="hook",
        bracer="rope",
        striped_sleeves=True,
        hair_beads=True,
        beauty_mark=True,
        freckles=True,
    ),
}


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(p: Point) -> Tuple[int, int]:
    return (_s(p[0]), _s(p[1]))


def _box(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_p(a: Point, b: Point, t: float) -> Point:
    return (_lerp(a[0], b[0], t), _lerp(a[1], b[1], t))


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _mix(a: RGBA, b: RGBA, t: float) -> RGBA:
    return (int(round(_lerp(a[0], b[0], t))), int(round(_lerp(a[1], b[1], t))), int(round(_lerp(a[2], b[2], t))), 255)


def _poly(
    draw: ImageDraw.ImageDraw,
    pts: Sequence[Point],
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    ipts = [_pt(p) for p in pts]
    draw.polygon(ipts, fill=fill)
    if outline and width > 0:
        draw.line(
            ipts + [ipts[0]], fill=outline, width=max(1, _s(width)), joint="curve"
        )


def _line(
    draw: ImageDraw.ImageDraw, pts: Sequence[Point], fill: RGBA, width: float = 1.0
) -> None:
    draw.line([_pt(p) for p in pts], fill=fill, width=max(1, _s(width)), joint="curve")


def _ellipse(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(
        _box(cx, cy, rx, ry), fill=fill, outline=outline, width=max(1, _s(width))
    )


def _circle(
    draw: ImageDraw.ImageDraw,
    c: Point,
    r: float,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.0,
) -> None:
    _ellipse(draw, c[0], c[1], r, r, fill, outline, width)


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


# ---- Poses -------------------------------------------------------------------


@dataclass
class Pose:
    """What the body does in one frame, for a variant whose ``tall`` is 1. The
    skeleton (``_pirate_heavy_rig.evaluate``) makes the joints from it."""

    pelvis: Point = (0.0, HIP_Y)
    lean: float = 0.0
    twist: float = 0.0  # 0 square to the camera, 1 side on
    head_tilt: float = 0.0
    head_dx: float = 0.0
    r_hand: Point = (69.0, -57.0)  # the lead hand, with the cleaver
    weapon: float = -66.0  # the degrees of the haft
    two_hand: bool = False  # the far hand is on the haft too
    l_hand: Point = (-40.0, -56.0)
    r_bend: float = 1.0  # +1: the elbow is clockwise of the line from shoulder to hand
    l_bend: float = 1.0
    l_foot: Point = (-21.0, 0.0)  # x, and how far it is off the ground
    r_foot: Point = (21.0, 0.0)
    skirt_sway: float = 0.0
    hair_swing: float = 0.0
    mouth: float = 0.05
    blink: bool = False
    x_eyes: bool = False
    swoosh: Optional[Tuple[float, float, float]] = None  # from, to (degrees of the haft), strength
    chips: bool = False
    body_rot: float = 0.0  # the whole body about the ground between her feet
    root: Point = (0.0, 0.0)
    # the cleaver out of her hand: where its grip is from the root, and its degrees
    loose_weapon: Optional[Tuple[Point, float]] = None


#: The chop, one row for each frame.
SLASH_KEYS = [
    # the weight goes back and the cleaver comes up; the free fist guards
    dict(pelvis=(-6, -55), lean=-8, twist=0.2, head_tilt=-4, r_hand=(40, -158), weapon=-104, l_hand=(-4, -90), l_foot=(-24, 0), r_foot=(16, 0), mouth=0.12),
    # the top of the windup: the blade is over and behind her head
    dict(pelvis=(-11, -53), lean=-16, twist=0.3, head_tilt=-7, r_hand=(26, -174), weapon=-150, l_hand=(8, -94), l_foot=(-26, 0), r_foot=(18, 7), mouth=0.25),
    # the cleaver starts down
    dict(pelvis=(-2, -54), lean=-2, twist=0.3, head_tilt=0, r_hand=(60, -156), weapon=-70, l_hand=(18, -84), l_foot=(-26, 0), r_foot=(30, 4), mouth=0.5, swoosh=(-150, -70, 0.6)),
    # the hit: the front foot is down, the weight is over it, both hands are on the haft
    dict(pelvis=(13, -50), lean=21, twist=0.8, head_tilt=6, r_hand=(88, -68), weapon=20, two_hand=True, l_foot=(-28, 0), r_foot=(42, 0), mouth=0.7, swoosh=(-92, 20, 1.0)),
    # the blade is in the deck
    dict(pelvis=(15, -46), lean=27, twist=0.85, head_tilt=8, r_hand=(84, -46), weapon=36, two_hand=True, l_foot=(-28, 0), r_foot=(43, 0), mouth=0.55, swoosh=(-30, 36, 0.5), chips=True),
    dict(pelvis=(14, -47), lean=24, twist=0.8, head_tilt=6, r_hand=(83, -49), weapon=33, two_hand=True, l_foot=(-28, 0), r_foot=(43, 0), mouth=0.3, chips=True),
    # she pulls it out
    dict(pelvis=(7, -53), lean=11, twist=0.4, head_tilt=1, r_hand=(72, -74), weapon=-12, two_hand=True, l_foot=(-25, 0), r_foot=(32, 0), mouth=0.12),
]


def pose_for(anim: str, i: int, n: int) -> Pose:
    t = i / max(1, n - 1)
    cyc = math.tau * i / max(1, n)
    # Rounded: a quarter turn must give an exact 0. A foot that is 1e-16 off the
    # deck is turned 1e-16 degrees, and a part turned at all is resampled.
    s, c = round(math.sin(cyc), 9), round(math.cos(cyc), 9)
    p = Pose()
    if anim == "idle":
        # the cleaver stands at her side like a staff; the free fist is on her hip
        p.pelvis = (0.0, HIP_Y + 1.0 + s * 1.2)
        p.lean = 1.5 + s * 0.8
        p.head_tilt = -2.0 + s * 1.6
        p.r_hand = (69.0, -57.0 + s * 1.5)
        p.weapon = -66.0 + s * 2.0
        p.l_hand = (-40.0, -56.0 + s * 1.0)
        p.skirt_sway = s * 3.0
        p.hair_swing = s * 2.0
        p.blink = i == n - 2
    elif anim == "walk":
        p.pelvis = (s * 2.0, HIP_Y + 2.0 - abs(c) * 3.0)
        p.lean = 5.0 + s * 2.5
        p.head_tilt = -2.0 - s * 2.0
        # A wide waddle: the feet come together and go apart, and one boot is
        # never over the other. Where two boots overlap, the rows that are part
        # ink are drawn twice, and the part flipbook does not replay that.
        p.l_foot = (-27.0 - 8.0 * s, max(0.0, c) * 8.0)
        p.r_foot = (29.0 + 8.0 * s, max(0.0, -c) * 8.0)
        p.r_hand = (68.0 - s * 3.0, -58.0 + abs(c) * 3.0)
        p.weapon = -62.0 + s * 4.0
        p.l_hand = (-50.0 + 16.0 * s, -50.0 - abs(s) * 4.0)
        p.skirt_sway = -s * 8.0
        p.hair_swing = -s * 5.0
    elif anim == "slash":
        for name, value in SLASH_KEYS[i].items():
            setattr(p, name, value)
        p.skirt_sway = -p.lean * 0.5
        p.hair_swing = -p.lean * 0.6
    elif anim == "taunt":
        # the cleaver over her head, the free arm flexed, a shout
        p.pelvis = (-2.0, HIP_Y + 1.0 - abs(s) * 1.5)
        p.lean = -7.0 + s * 2.0
        p.head_tilt = -8.0 + s * 3.0
        p.r_hand = (46.0, -168.0 - s * 6.0)
        p.weapon = -84.0 + s * 9.0
        p.l_hand = (-72.0, -132.0 + s * 4.0)
        p.l_bend = -1.0
        p.mouth = 0.6 + max(0.0, s) * 0.2
        p.skirt_sway = s * 4.0
        p.hair_swing = s * 4.0
    elif anim == "hurt":
        hit = math.sin(t * math.pi)
        p.pelvis = (-6.0 * hit, HIP_Y + 2.0 * hit)
        p.lean = -15.0 * hit
        p.head_tilt = 12.0 * hit
        p.r_hand = (69.0 + 12.0 * hit, -57.0 - 34.0 * hit)
        p.weapon = -66.0 + 34.0 * hit
        p.l_hand = (-40.0 - 26.0 * hit, -56.0 - 44.0 * hit)
        p.l_bend = -1.0 if hit > 0.3 else 1.0
        p.l_foot = (-21.0 - 6.0 * hit, 0.0)
        p.mouth = 0.45 * hit
        p.skirt_sway = 9.0 * hit
        p.hair_swing = 10.0 * hit
    elif anim == "death":
        # She goes over on her back. The cleaver leaves her hand and comes to
        # rest on the deck in front of her.
        tt = _ease(t)
        fall = _ease((t - 0.12) / 0.6)
        p.body_rot = -90.0 * fall
        # on her side, her width is her height off the deck
        p.root = (-14.0 * fall, -54.0 * fall + 5.0 * math.sin(max(0.0, t - 0.72) / 0.28 * math.pi))
        p.pelvis = (0.0, HIP_Y + 5.0 * math.sin(min(1.0, t / 0.3) * math.pi))
        p.lean = -10.0 * math.sin(tt * math.pi) - 4.0 * fall
        p.head_tilt = 14.0 * fall
        # one arm comes to rest on her, the other on the deck past her head
        p.r_hand = _lerp_p(_lerp_p((69.0, -57.0), (92.0, -120.0), math.sin(fall * math.pi)), (34.0, -62.0), fall)
        p.l_hand = _lerp_p((-40.0, -56.0), (-34.0, -158.0), fall)
        p.l_foot = (-21.0, 12.0 * fall)
        p.r_foot = (21.0, 3.0 * fall)
        p.mouth = 0.5 * math.sin(tt * math.pi) + 0.1
        p.x_eyes = fall > 0.6
        p.skirt_sway = 8.0 * fall
        p.hair_swing = 14.0 * math.sin(fall * math.pi)
        drop = _ease((t - 0.1) / 0.5)
        if drop > 0.0:
            # from where her hand was, down to the deck
            p.loose_weapon = (_lerp_p((69.0, -57.0), (58.0, -9.0), drop), _lerp(-66.0, -2.0, drop) - 14.0 * math.sin(drop * math.pi))
    return p


#: How far her gun hand is to the front of its rest in each frame of the
#: attack row: back, then a thrust, then back.
_GUN_THRUST = (-4.0, -9.0, 6.0, 22.0, 25.0, 18.0, 6.0)


def _hold_a_gun(pose: Pose, anim: str, frame_idx: int) -> None:
    """Change a pose of the cleaver to one of a gun-sword: it is level in her
    lead hand at her hip, and her attack is a thrust with it, not a chop. The
    game draws the gun-sword and points it at her target."""
    pose.two_hand = False
    pose.swoosh = None
    pose.chips = False
    pose.r_bend = 1.0
    if anim == "taunt":
        return
    lift = pose.r_hand[1] + 57.0 if anim in ("idle", "walk") else 0.0
    pose.r_hand = (62.0, -84.0 + lift)
    pose.weapon = -ITEM_REST_ANGLE
    if anim == "slash":
        thrust = _GUN_THRUST[frame_idx]
        pose.r_hand = (58.0 + thrust, -86.0)
        pose.lean *= 0.5
        pose.pelvis = (pose.pelvis[0] * 0.5, pose.pelvis[1])
        pose.l_hand = (-44.0 - pose.lean * 0.6, -70.0)
    elif anim == "hurt":
        pose.r_hand = (62.0 + pose.lean * -0.6, -84.0 + pose.lean * 1.2)


# ---- Pieces ------------------------------------------------------------------
#
# A heavy is drawn as a rig: each rigid thing (the head, the torso, a limb, a
# boot, the cleaver) is painted ONCE by its painter on a scratch canvas with its
# anchor at ``HOME``, cut to what it covers, and placed (and turned) through
# ``shape_rig``. A part flipbook stores each once. The skirt is not rigid: it is
# one piece for each shape it takes.

#: The scratch canvas's half size and the anchor (work pixels).
HOME = (200.0, 200.0)
HX, HY = HOME
_PIECES: Dict[tuple, object] = {}


def _piece(key: tuple, paint):
    """``(raster, anchor)``: what ``paint(draw)`` paints with its anchor at
    ``HOME``, cut to its box; ``None`` when it paints nothing. ``key`` must
    name everything ``paint`` reads."""
    if key not in _PIECES:
        size = int(2 * HOME[0] * SUPER), int(2 * HOME[1] * SUPER)
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        paint(blending_draw(canvas))
        box = canvas.getchannel("A").getbbox()
        _PIECES[key] = None if box is None else (canvas.crop(box), (HOME[0] * SUPER - box[0], HOME[1] * SUPER - box[1]))
    return _PIECES[key]


def _put(img: Image.Image, key: tuple, paint, at: Point, name: str, degrees: float = 0.0) -> None:
    """Place the piece ``key`` with its anchor at ``at`` (work pixels)."""
    part = _piece(key, paint)
    if part is not None:
        shape_rig.place(img, part, (at[0] * SUPER, at[1] * SUPER), degrees, name)


def _limb(d, length: float, w0: float, w1: float, fill: RGBA, ink: float = 1.7) -> None:
    """A tapered limb along +x from ``HOME``, round at both ends."""
    for grow, color in ((ink, OUTLINE), (0.0, fill)):
        a, b = w0 / 2 + grow, w1 / 2 + grow
        d.polygon([_pt(q) for q in [(HX, HY - a), (HX + length, HY - b), (HX + length, HY + b), (HX, HY + a)]], fill=color)
        d.ellipse(_box(HX, HY, a, a), fill=color)
        d.ellipse(_box(HX + length, HY, b, b), fill=color)


# ---- Painters: the arms --------------------------------------------------------


def _paint_upper_arm(d, spec: VariantSpec) -> None:
    pal, k = spec.palette, spec.arm
    _limb(d, UPPER_ARM, 18.5 * k, 16.0 * k, _mix(pal.skin, pal.skin_shadow, 0.3))
    _line(d, [(HX + 18, HY - 4.0 * k), (HX + UPPER_ARM - 4, HY - 3.2 * k)], _mix(pal.skin, WHITE, 0.1), 1.6)
    # the sleeve of her blouse, off the shoulder: full, and drawn in at a band
    puff = [(-6, -11.5), (3, -14.5), (12, -13.5), (17, -8.5), (17, 8.5), (12, 13.5), (3, 14.5), (-6, 11.5)]
    _poly(d, [(HX + x, HY + y * k) for x, y in puff], pal.shirt, OUTLINE, 1.7)
    if spec.striped_sleeves:
        for x in (0.0, 5.5, 11.0):
            _line(d, [(HX + x, HY - 12.6 * k), (HX + x + 1.0, HY + 12.6 * k)], pal.sash, 2.3)
    else:
        shade = _mix(pal.shirt, OUTLINE, 0.22)
        for y0, y1 in ((-9.5, -7.0), (-3.0, -2.2), (3.5, 2.6), (9.5, 7.0)):
            _line(d, [(HX - 1, HY + y0 * k), (HX + 13, HY + y1 * k)], shade, 1.0)
    _poly(d, [(HX + 14.5, HY - 9.2 * k), (HX + 19, HY - 8.6 * k), (HX + 19, HY + 8.6 * k), (HX + 14.5, HY + 9.2 * k)], _mix(pal.shirt, pal.sash, 0.55), OUTLINE, 1.2)


def _paint_forearm(d, spec: VariantSpec) -> None:
    pal, k = spec.palette, spec.arm
    _limb(d, FOREARM, 16.0 * k, 12.5 * k, pal.skin)
    _line(d, [(HX + 4, HY - 4 * k), (HX + FOREARM - 20, HY - 3.6 * k)], _mix(pal.skin, WHITE, 0.14), 1.5)
    # what she wears at the wrist
    x0, x1 = HX + FOREARM - 19, HX + FOREARM - 4
    cuff = [(x0, HY - 8.8 * k), (x1, HY - 7.6 * k), (x1, HY + 7.6 * k), (x0, HY + 8.8 * k)]
    if spec.bracer == "iron":
        _poly(d, cuff, METAL_DARK, OUTLINE, 1.4)
        _line(d, [(x0 + 2, HY - 5.5 * k), (x1 - 2, HY - 5.0 * k)], METAL, 1.7)
        for y in (-1.5, 4.0):
            _circle(d, ((x0 + x1) / 2, HY + y * k), 1.2, RIVET, OUTLINE, 0.3)
    elif spec.bracer == "leather":
        _poly(d, cuff, pal.boot_hi, OUTLINE, 1.4)
        _line(d, [(x0 + 2, HY - 5.5 * k), (x1 - 2, HY - 5.0 * k)], _mix(pal.boot_hi, WHITE, 0.25), 1.3)
        for x in (x0 + 4, x1 - 4):
            _circle(d, (x, HY + 1.5 * k), 1.5, GOLD, OUTLINE, 0.4)
    else:
        # turns of rope
        _poly(d, cuff, pal.shirt, OUTLINE, 1.4)
        for x in (x0 + 3.7, x0 + 7.5, x0 + 11.2):
            _line(d, [(x, HY - 8.2 * k), (x + 1.2, HY + 8.2 * k)], _mix(pal.shirt, OUTLINE, 0.4), 1.0)


def _paint_fist(d, spec: VariantSpec) -> None:
    pal, k = spec.palette, 0.5 + 0.5 * spec.arm
    _circle(d, (HX, HY), 10.0 * k, pal.skin, OUTLINE, 1.7)
    for x in (-5.0, 0.0, 5.0):
        _line(d, [(HX + x + 0.5, HY - 5.0), (HX + x - 0.5, HY + 5.0)], pal.skin_shadow, 1.1)


def _paint_pauldron(d, spec: VariantSpec) -> None:
    """Three iron plates down one shoulder. The shoulder is at ``HOME`` and the
    arm goes along +x."""
    for k, (x0, h) in enumerate(((9.0, 11.0), (1.5, 12.2), (-9.0, 13.2))):
        long = 11.0 if k < 2 else 14.0
        plate = [(HX + x0, HY - h), (HX + x0 + long - 3, HY - h - 0.6), (HX + x0 + long, HY - h * 0.3), (HX + x0 + long, HY + h * 0.3), (HX + x0 + long - 3, HY + h + 0.6), (HX + x0, HY + h)]
        _poly(d, plate, METAL if k else METAL_DARK, OUTLINE, 1.5)
        _line(d, [(HX + x0 + 2, HY - h + 3.5), (HX + x0 + long - 3, HY - h + 3.2)], (238, 243, 243, 210) if k else METAL, 1.4)
    for y in (-8.0, 0.0, 8.0):
        _circle(d, (HX - 5.0, HY + y), 1.5, RIVET, OUTLINE, 0.4)


# ---- Painters: the body --------------------------------------------------------


def _paint_torso(d, spec: VariantSpec, sw: float, cx: float) -> None:
    """The torso, pelvis at ``HOME``, up to the shoulders: a laced bodice over
    a blouse that is off her shoulders. ``sw`` is half the width of the
    shoulders as turned; ``cx`` is where the middle of the chest is."""
    pal, tall = spec.palette, spec.tall
    P = lambda x, y: (HX + x, HY + y * tall)
    turn = sw / (SHOULDER * spec.shoulder)
    k = sw / SHOULDER
    cw = 38.0 * spec.bust * turn
    waist = 24.0 * spec.waist
    hip = spec.hip
    skin = _mix(pal.skin, pal.skin_shadow, 0.18)
    neck = _mix(pal.skin, pal.skin_shadow, 0.55)
    fx = cw * 0.55 + cx * 0.4
    # her shoulders and her chest
    _poly(d, [P(-sw, -53), P(-15 * k, -62), P(17 * k, -62), P(sw, -53), P(cw, -40), P(-cw, -40)], skin, OUTLINE, 1.9)
    _poly(d, [P(cx - 10, -75), P(cx + 6, -75), P(cx + 7, -59), P(cx - 10, -59)], neck, OUTLINE, 1.5)
    _line(d, [P(cx - 9, -59), P(cx + 6, -59)], neck, 2.0)
    _line(d, [P(cx - 22, -56), P(cx - 7, -54)], pal.skin_shadow, 1.1)
    _line(d, [P(cx + 5, -54), P(cx + 17, -56)], pal.skin_shadow, 1.1)
    # the bodice: full at the chest, drawn in hard at the waist, out again at the hip
    body = [P(-cw, -45), P(-cw * 0.5, -50), P(cx - 1, -41), P(fx, -50), P(cw, -45), P(cw + 1.5, -31), P(waist, -15), P(32 * hip, -4), P(-32 * hip, -4), P(-waist, -15), P(-cw - 1.5, -31)]
    _poly(d, body, pal.bodice, OUTLINE, 1.9)
    near = [P(-cw + 2, -43.5), P(-cw * 0.5, -48), P(cx - 3, -39.5), P(cx - 3, -29), P(-cw * 0.5, -22.5), P(-cw + 2, -29)]
    far = [P(cw - 2, -43.5), P(fx, -48), P(cx + 1, -39.5), P(cx + 1, -29), P(cw * 0.55, -22.5), P(cw - 2, -29)]
    _poly(d, near, pal.bodice_hi, OUTLINE, 1.2)
    _poly(d, far, pal.bodice_hi, OUTLINE, 1.2)
    hi = _mix(pal.bodice_hi, WHITE, 0.28)
    _line(d, [P(-cw + 6, -40), P(-cw * 0.5, -44.5)], hi, 1.5)
    _line(d, [P(fx + 1, -44.5), P(cw - 6, -40)], hi, 1.5)
    # the bones of the bodice, and its lacing
    dark = _mix(pal.bodice, OUTLINE, 0.35)
    for side in (-1.0, 1.0):
        _line(d, [P(side * waist * 0.78, -22), P(side * waist * 0.62, -6)], dark, 1.2)
    _poly(d, [P(cx - 5, -29), P(cx + 3, -29), P(cx + 3, -5), P(cx - 5, -5)], dark, None, 0)
    for y in (-28, -21, -14):
        _line(d, [P(cx - 5, y), P(cx + 3, y + 5)], pal.shirt, 1.3)
        _line(d, [P(cx + 3, y), P(cx - 5, y + 5)], pal.shirt, 1.3)
    # the frill of the blouse along the top of the bodice
    frill = [P(-cw - 1, -45), P(-cw * 0.5, -50.5), P(cx - 1, -41.5), P(fx, -50.5), P(cw + 1, -45)]
    _line(d, frill, OUTLINE, 6.6)
    _line(d, frill, pal.shirt, 3.8)
    if spec.mark == "bandolier":
        # a belt of charges from the near shoulder to the far hip
        a, b = P(-sw + 7, -52), P(29 * hip, -9)
        _line(d, [a, b], OUTLINE, 10.0)
        _line(d, [a, b], pal.boot_hi, 6.6)
        for f in (0.2, 0.4, 0.6, 0.8):
            c = _lerp_p(a, b, f)
            _poly(d, [(c[0] - 2.6, c[1] - 6.5), (c[0] + 2.6, c[1] - 5.5), (c[0] + 2.6, c[1] + 4.5), (c[0] - 2.6, c[1] + 3.5)], GOLD, OUTLINE, 0.9)
    # the sash on her hips, and its iron buckle
    _poly(d, [P(-33 * hip, -9), P(33 * hip, -9), P(38 * hip, 6), P(-38 * hip, 6)], pal.sash, OUTLINE, 1.7)
    _line(d, [P(-31 * hip, -5.5), P(31 * hip, -5.5)], _mix(pal.sash, WHITE, 0.4), 1.3)
    _line(d, [P(-35 * hip, 2), P(35 * hip, 2)], _mix(pal.sash, OUTLINE, 0.3), 1.1)
    _poly(d, [P(cx - 9, -12), P(cx + 9, -12), P(cx + 10, 9), P(cx - 10, 9)], METAL, OUTLINE, 1.6)
    _poly(d, [P(cx - 4.5, -7.5), P(cx + 4.5, -7.5), P(cx + 4.5, 4), P(cx - 4.5, 4)], METAL_DARK, OUTLINE, 1.0)
    _line(d, [P(cx - 7, -9.5), P(cx + 5, -9.5)], (240, 244, 244, 220), 1.2)
    if spec.necklace:
        for x, y in ((-11, -56), (-6, -52), (-1, -50), (4, -52), (9, -56)):
            _circle(d, P(cx + x, y), 2.1, GOLD, OUTLINE, 0.5)
    if spec.mark == "neckerchief":
        # a sailor's cloth, knotted at her throat
        cloth = pal.sash
        _poly(d, [P(cx - 14, -62), P(cx + 10, -62), P(cx + 4, -52), P(cx - 2, -44), P(cx - 8, -52)], cloth, OUTLINE, 1.4)
        _poly(d, [P(cx - 4, -52), P(cx - 9, -40), P(cx - 3, -42)], _mix(cloth, OUTLINE, 0.25), OUTLINE, 1.0)
        _poly(d, [P(cx, -52), P(cx + 5, -41), P(cx - 1, -43)], cloth, OUTLINE, 1.0)
        _circle(d, P(cx - 2, -52), 3.0, _mix(cloth, WHITE, 0.2), OUTLINE, 1.0)


def _paint_sash_tail(d, spec: VariantSpec) -> None:
    """The end of the sash, the knot at ``HOME``, hanging along +x."""
    pal = spec.palette
    _poly(d, [(HX - 2, HY - 6), (HX + 30, HY - 8), (HX + 26, HY - 1), (HX + 34, HY + 5), (HX - 2, HY + 5)], pal.sash, OUTLINE, 1.5)
    _line(d, [(HX + 4, HY - 2), (HX + 26, HY - 3)], _mix(pal.sash, OUTLINE, 0.3), 1.0)
    _circle(d, (HX, HY), 5.0, _mix(pal.sash, OUTLINE, 0.2), OUTLINE, 1.3)


def _paint_skirt(d, spec: VariantSpec, wl: Point, wr: Point, hl: float, hr: float, hem_y: float, sway: float) -> None:
    """The skirt, pelvis at ``HOME``: from the waist ``wl``..``wr`` to a hem
    from ``hl`` to ``hr`` at ``hem_y``."""
    pal = spec.palette
    P = lambda x, y: (HX + x, HY + y)
    mid = (hl + hr) / 2 + sway * 0.3
    q1, q3 = _lerp(hl, mid, 0.5), _lerp(mid, hr, 0.5)
    hem = [P(hr + sway * 0.2, hem_y - 7), P(q3 + 6, hem_y + 5), P(q3 - 4, hem_y - 1), P(mid, hem_y + 6), P(q1 + 4, hem_y - 1), P(q1 - 6, hem_y + 5), P(hl + sway * 0.2, hem_y - 7)]
    _poly(d, [P(*wl), P(*wr)] + hem, pal.skirt, OUTLINE, 2.0)
    for f in (0.12, 0.32, 0.5, 0.68, 0.88):
        top = _lerp_p(wl, wr, _lerp(0.2, 0.8, f))
        bottom = (_lerp(hl, hr, f) + sway * 0.25, hem_y - 3 + 6 * abs(math.sin(f * math.pi * 2.5)))
        _line(d, [P(*top), P(*bottom)], pal.skirt_hi, 1.3)
    # the dark band of the hem
    _line(d, [(x, y - 5) for x, y in hem], _mix(pal.skirt, OUTLINE, 0.45), 1.6)


def _paint_boot_shaft(d, spec: VariantSpec) -> None:
    pal = spec.palette
    _limb(d, SHIN * spec.tall, 17.0, 14.0, pal.boot)
    _poly(d, [(HX - 2, HY - 10), (HX + 7, HY - 9.5), (HX + 7, HY + 9.5), (HX - 2, HY + 10)], pal.boot_hi, OUTLINE, 1.3)


def _paint_foot(d, spec: VariantSpec) -> None:
    """A boot, the ankle at ``HOME``, the toe toward +x.

    The sole ends ``ANKLE`` under the ankle exactly, and the root of the body
    is on a whole pixel: the low edge of a boot on the deck is the edge of a
    pixel row. A row that is part ink is drawn twice where two boots overlap,
    and the part flipbook does not replay that."""
    pal = spec.palette
    f = lambda x, y: (HX + x, HY + y)
    low = rig.ANKLE - 0.85
    _poly(d, [f(-10, -8), f(7, -9), f(20, -3), f(25, 5), f(24, low), f(-10, low)], pal.boot, OUTLINE, 1.7)
    # the iron cap of the toe
    _poly(d, [f(12, -6), f(20, -3), f(25, 5), f(24, low), f(11, low)], METAL_DARK, OUTLINE, 1.2)
    _line(d, [f(14, -3), f(20, 1)], METAL, 1.3)
    _poly(d, [f(-10.85, 5.8), f(24.85, 5.8), f(24.85, rig.ANKLE), f(-10.85, rig.ANKLE)], OUTLINE, None, 0)
    _line(d, [f(-7, -4), f(5, -5)], GOLD, 1.2)


# ---- Painters: the cleaver -----------------------------------------------------

#: A blade: its outline, the ground edge (a band along the belly), the belly
#: itself (inked again over the band), the forge dark down the spine, and the
#: holes through it.
_BLADES = {
    # a slab of iron with a long belly
    "slab": dict(
        outline=[(40, -8), (98, -10), (106, -3), (107, 24), (98, 36), (62, 39), (49, 31), (45, 9)],
        edge=[(49, 31), (62, 39), (98, 36), (107, 24), (101, 23), (95, 30), (63, 32.5), (52, 26)],
        belly=[(49, 31), (62, 39), (98, 36), (107, 24)],
        spine=[(42, -6.5), (97, -8.5), (103, -3), (98, 3), (46, 4)],
        holes=[(94, 14, 4.0)],
    ),
    # deeper, with a clipped corner and three gun ports
    "ports": dict(
        outline=[(40, -8), (94, -10), (106, 0), (107, 30), (99, 42), (60, 45), (48, 36), (45, 9)],
        edge=[(48, 36), (60, 45), (99, 42), (107, 30), (101, 29), (96, 36), (61, 38.5), (51, 31)],
        belly=[(48, 36), (60, 45), (99, 42), (107, 30)],
        spine=[(42, -6.5), (93, -8.5), (102, -1), (97, 4), (46, 4)],
        holes=[(62, 17, 3.6), (77, 17, 3.6), (92, 17, 3.6)],
    ),
    # a long belly that comes up to a hooked point
    "hook": dict(
        outline=[(40, -8), (90, -9), (116, -22), (112, 4), (103, 24), (85, 35), (60, 33), (49, 26), (45, 9)],
        edge=[(49, 26), (60, 33), (85, 35), (103, 24), (112, 4), (116, -22), (109, -8), (106, 4), (98, 20), (83, 29), (61, 27.5), (52, 21.5)],
        belly=[(49, 26), (60, 33), (85, 35), (103, 24), (112, 4), (116, -22)],
        spine=[(42, -6.5), (89, -7.5), (100, -13), (96, 0), (46, 4)],
        holes=[],
    ),
}


def _paint_cleaver(d, spec: VariantSpec) -> None:
    """The great cleaver, the lead hand at ``HOME``, the haft along +x, the
    edge toward +y."""
    P = lambda x, y: (HX + x, HY + y)
    _line(d, [P(-HAFT_BACK, 0), P(60, 0)], OUTLINE, 9.4)
    _line(d, [P(-HAFT_BACK, 0), P(60, 0)], WOOD, 6.0)
    _line(d, [P(-HAFT_BACK + 3, -1.5), P(60, -1.5)], _mix(WOOD, WHITE, 0.22), 1.2)
    for x in range(-30, 14, 7):
        _line(d, [P(x, -3.6), P(x + 3, 3.6)], (54, 34, 24, 255), 1.5)
    _circle(d, P(-HAFT_BACK - 3, 0), 5.6, GOLD, OUTLINE, 1.5)
    blade = _BLADES[spec.blade]
    _poly(d, [P(*q) for q in blade["outline"]], METAL, OUTLINE, 2.3)
    _poly(d, [P(*q) for q in blade["edge"]], (236, 241, 242, 255), None, 0)
    _line(d, [P(*q) for q in blade["belly"]], OUTLINE, 2.3)
    _poly(d, [P(*q) for q in blade["spine"]], METAL_DARK, None, 0)
    _line(d, [P(48, 9), P(92, 7)], (238, 244, 244, 190), 1.5)
    for x, y, r in blade["holes"]:
        _circle(d, P(x, y), r, (40, 42, 50, 255), OUTLINE, 1.3)
    # the iron that holds the blade to the haft
    _poly(d, [P(38, -8), P(50, -8), P(50, 8), P(38, 8)], GOLD, OUTLINE, 1.4)
    for x, y in ((56, -3), (68, -3.5), (80, -4)):
        _circle(d, P(x, y), 1.9, RIVET, OUTLINE, 0.5)


# ---- Painters: the hair --------------------------------------------------------


def _paint_dread(d, spec: VariantSpec, length: float) -> None:
    pal = spec.palette
    _limb(d, length, 9.5, 6.5, pal.hair, ink=1.5)
    if spec.hair_beads:
        _poly(d, [(HX + length - 9, HY - 4.2), (HX + length - 4, HY - 4.0), (HX + length - 4, HY + 4.0), (HX + length - 9, HY + 4.2)], GOLD, OUTLINE, 0.9)
    for x in range(8, int(length) - 12, 8):
        _line(d, [(HX + x, HY - 4.0), (HX + x + 2.5, HY + 4.0)], pal.hair_hi, 1.1)


def _paint_lock(d, spec: VariantSpec, length: float) -> None:
    """A loose lock of long hair."""
    pal = spec.palette
    _limb(d, length, 11.0, 5.0, pal.hair, ink=1.5)
    _line(d, [(HX + 4, HY - 2.0), (HX + length * 0.5, HY + 1.5), (HX + length - 6, HY - 0.5)], pal.hair_hi, 1.5)
    if spec.hair_beads:
        _circle(d, (HX + length - 3, HY), 3.2, GOLD, OUTLINE, 0.9)


def _paint_braid(d, spec: VariantSpec, length: float) -> None:
    """One thick plait, tied with a ribbon."""
    pal = spec.palette
    step = 9.0
    count = int(length // step)
    for k in range(count):
        x = HX + k * step
        w = _lerp(13.5, 9.0, k / max(1, count - 1))
        _poly(d, [(x - 1.5, HY), (x + step * 0.55, HY - w / 2), (x + step + 1.5, HY), (x + step * 0.55, HY + w / 2)], pal.hair, OUTLINE, 1.4)
        _line(d, [(x + 2.5, HY - 1.0), (x + step * 0.55, HY - w / 2 + 2.2)], pal.hair_hi, 1.2)
    end = HX + count * step
    _poly(d, [(end, HY - 3.5), (end + 11, HY - 6.0), (end + 9, HY), (end + 12, HY + 5.5), (end, HY + 3.5)], pal.hair, OUTLINE, 1.2)
    _poly(d, [(end - 3, HY - 5.2), (end + 2.5, HY - 5.0), (end + 2.5, HY + 5.0), (end - 3, HY + 5.2)], pal.bandana, OUTLINE, 1.0)


def _paint_mane(d, spec: VariantSpec) -> None:
    """The mass of her hair behind her, the middle of the head at ``HOME``."""
    pal = spec.palette
    scale = HEAD * spec.head
    P = lambda x, y: (HX + x * scale, HY + y * scale)
    if spec.hair == "dreads":
        _poly(d, [P(-12, -17), P(-24, -10), P(-32, 10), P(-34, 34), P(-27, 52), P(-17, 47), P(-9, 56), P(1, 44), P(8, 30), P(9, 6)], pal.hair, OUTLINE, 1.7)
        strands = (((-20, -2), (-28, 34)), ((-13, 2), (-18, 44)), ((-5, 6), (-6, 46)), ((3, 8), (4, 34)))
    elif spec.hair == "braid":
        # pinned up under her hat: a round mass at the back of her neck
        _poly(d, [P(-12, -17), P(-24, -10), P(-30, 2), P(-31, 16), P(-25, 27), P(-14, 30), P(-3, 25), P(5, 14), P(8, 2)], pal.hair, OUTLINE, 1.7)
        strands = (((-22, -2), (-26, 16)), ((-14, 4), (-17, 24)), ((-5, 6), (-5, 22)))
    else:
        # long, loose and in waves, to the middle of her back
        _poly(d, [P(-12, -17), P(-25, -9), P(-33, 8), P(-30, 22), P(-37, 38), P(-31, 58), P(-22, 50), P(-14, 62), P(-4, 48), P(4, 36), P(10, 16), P(8, 0)], pal.hair, OUTLINE, 1.7)
        strands = (((-22, -2), (-25, 20), (-30, 44)), ((-14, 2), (-15, 26), (-19, 50)), ((-5, 6), (-4, 28), (-9, 48)), ((3, 8), (5, 26)))
    for strand in strands:
        _line(d, [P(*q) for q in strand], pal.hair_hi, 1.3)


# ---- Painters: the head --------------------------------------------------------

#: The head is drawn this much larger than its numbers.
HEAD = 1.16


def _paint_head(d, spec: VariantSpec, mouth: float, blink: bool, x_eyes: bool) -> None:
    """The head, turned three quarters to the way she faces, its middle at
    ``HOME``."""
    pal = spec.palette
    scale = HEAD * spec.head
    P = lambda x, y: (HX + x * scale, HY + y * scale)
    ink = 1.12

    def poly(pts, fill, outline=OUTLINE, width=1.0):
        _poly(d, pts, fill, outline, width * ink)

    def line(pts, fill, width=1.0):
        _line(d, pts, fill, width * ink)

    def circle(c, r, fill, outline=OUTLINE, width=1.0):
        _circle(d, c, r * scale, fill, outline, width * ink)

    skin, dark = pal.skin, pal.skin_shadow
    if spec.headwear in ("bandana", "band"):
        # the tails of the cloth, behind her head
        far = 1.0 if spec.headwear == "bandana" else 1.35
        poly([P(-20, -13), P(-20 - 20 * far, -13 - 8 * far), P(-20 - 15 * far, -13 + 5 * far)], pal.bandana, OUTLINE, 1.3)
        poly([P(-20, -10), P(-20 - 16 * far, -10 + 9 * far), P(-20 - 7 * far, -10 + 12 * far)], pal.bandana_dark, OUTLINE, 1.3)
    # the hair at the back of her head
    poly([P(-21, -10), P(-13, -19), P(-3, -12), P(-7, 13), P(-19, 16), P(-24, 4)], pal.hair, OUTLINE, 1.5)
    # the face: round, with full cheeks; the jaw drops when she shouts
    jaw = 3.0 * mouth if mouth > 0.2 else 0.0

    def arc(a0, a1, shrink=0.0, steps=12):
        """Points of the round of the lower face, from ``a0`` to ``a1`` degrees."""
        pts = []
        for k in range(steps + 1):
            a = math.radians(_lerp(a0, a1, k / steps))
            pts.append(P(0.8 + (18.4 - shrink) * math.cos(a) + 1.6 * math.sin(a), 2.5 + (19.0 - shrink + jaw) * math.sin(a)))
        return pts

    poly([P(-15, -9), P(-8, -17), P(6, -18), P(14, -13), P(18.2, -5)] + arc(-8, 188), skin, OUTLINE, 1.9)
    # the near side of the face, in shadow: a thin moon, so the cheek stays round
    poly(arc(112, 186) + arc(186, 112, shrink=4.6), _mix(skin, dark, 0.4), None, 0)
    poly([P(-6, -3), P(18, -3), P(18, 5.5), P(9, 6.5), P(-4, 5.5)], _mix(skin, dark, 0.2), None, 0)
    # the light on the far cheek
    line(arc(8, 40, shrink=3.2, steps=5), _mix(skin, WHITE, 0.16), 1.7)
    if spec.freckles:
        for x, y in ((-1, 8.5), (2, 10), (5, 8.2), (14, 8.6), (16, 10.2), (11.5, 7.6)):
            circle(P(x, y), 0.6, _mix(skin, dark, 0.85), None, 0)
    # the ear and its ring
    poly([P(-13.5, -3), P(-9, -4), P(-8, 4.5), P(-11, 8), P(-14.5, 4)], _mix(skin, dark, 0.25), OUTLINE, 1.1)
    circle(P(-11.5, 11.5), 2.9, GOLD, OUTLINE, 0.8)
    circle(P(-11.5, 11.5), 1.0, _mix(skin, dark, 0.6), None, 0)
    # the nose, and the small ring in it
    poly([P(9, 1), P(13.6, 9.2), P(7.6, 10.8)], _mix(skin, dark, 0.35), None, 0)
    line([P(11.5, 5.5), P(13.6, 9.2), P(8.6, 10.8)], OUTLINE, 1.2)
    if spec.nose_ring:
        circle(P(8.2, 10.9), 1.7, GOLD, OUTLINE, 0.6)
    # The eyes: fierce. The lids slant down to the nose, the irises look at her
    # target, and the brows sit on them.
    if x_eyes:
        for ex in (2.0, 13.5):
            line([P(ex - 3.4, -0.5), P(ex + 3.4, 5.5)], OUTLINE, 1.5)
            line([P(ex - 3.4, 5.5), P(ex + 3.4, -0.5)], OUTLINE, 1.5)
    elif blink:
        line([P(-3.5, 2.6), P(7.2, 3.8)], OUTLINE, 1.7)
        line([P(10.2, 3.8), P(17.2, 2.6)], OUTLINE, 1.7)
        for a, b in (((-3.5, 2.6), (-6.6, 4.4)), ((-1.6, 2.9), (-3.4, 5.6)), ((17.2, 2.6), (19.6, 4.2)), ((15.6, 3.0), (16.8, 5.4))):
            line([P(*a), P(*b)], OUTLINE, 1.0)
    else:
        white = (252, 248, 236, 255)
        poly([P(-3.6, 0.4), P(7.4, 2.8), P(6.2, 4.9), P(1.6, 5.8), P(-2.6, 4.2)], white, OUTLINE, 0.9)
        poly([P(10.0, 2.8), P(17.4, 0.4), P(16.8, 4.2), P(13.6, 5.6), P(11.0, 4.7)], white, OUTLINE, 0.9)
        for (ix, iy), r in (((3.6, 3.4), 2.5), ((14.4, 3.3), 2.2)):
            circle(P(ix, iy), r, pal.iris, OUTLINE, 0.8)
            circle(P(ix + 0.2, iy + 0.1), r * 0.5, OUTLINE, None, 0)
            circle(P(ix - 0.8, iy - 0.6), 0.55, WHITE, None, 0)
        # the lids come down over the top of the irises
        lid = _mix(skin, dark, 0.25)
        poly([P(-3.6, 0.4), P(7.4, 2.8), P(7.4, 0.2), P(-3.6, -2.2)], lid, None, 0)
        poly([P(10.0, 2.8), P(17.4, 0.4), P(17.4, -2.2), P(10.0, 0.2)], lid, None, 0)
        line([P(-3.9, 0.3), P(7.6, 2.9)], OUTLINE, 2.0)
        line([P(9.8, 2.9), P(17.6, 0.3)], OUTLINE, 2.0)
        # the lashes at the outer corners
        lashes = (
            ((-3.8, 0.4), (-7.6, -1.2)), ((-2.6, 0.6), (-5.8, -3.2)), ((-1.0, 0.9), (-3.0, -3.6)), ((-2.4, 4.2), (-5.2, 5.0)),
            ((17.5, 0.4), (20.4, -1.2)), ((16.6, 0.7), (18.8, -3.0)), ((15.4, 1.1), (16.6, -3.0)),
        )
        for a, b in lashes:
            line([P(*a), P(*b)], OUTLINE, 1.05)
    if not x_eyes:
        # the brows: an arch at the outer end, thick and low at the nose
        brow = _mix(pal.hair, OUTLINE, 0.6)
        poly([P(-6.4, -3.6), P(-1.5, -6.6), P(8.2, -1.6), P(8.0, 1.4), P(-0.5, -3.2), P(-6.0, -2.2)], brow, None, 0)
        poly([P(9.4, 1.4), P(9.4, -1.6), P(14.6, -6.2), P(18.2, -4.6), P(18.0, -3.2), P(14.6, -3.4)], brow, None, 0)
        line([P(8.4, -4.6), P(8.9, -1.8)], _mix(dark, OUTLINE, 0.4), 1.0)
        if spec.brow_notch:
            line([P(1.2, -6.4), P(2.6, -1.6)], skin, 1.3)
    if spec.cheek_scar:
        scar = _mix(dark, OUTLINE, 0.35)
        line([P(-6.0, 8.0), P(-2.5, 12.5), P(0.0, 18)], scar, 1.3)
        for y in (10.5, 14.5):
            line([P(-5.6, y + 0.8), P(-0.8, y - 0.8)], scar, 0.9)
    if spec.beauty_mark:
        circle(P(-1.5, 14.5), 1.0, OUTLINE, None, 0)
    # the mouth: full lips, painted
    lip = pal.lip
    my = -0.9 + jaw * 0.5
    if mouth > 0.2:
        drop = 3.0 + 5.0 * mouth
        poly([P(1.2, 12.7 + my), P(15.3, 11.8 + my), P(14, 14 + my + drop), P(3.7, 15 + my + drop)], lip, OUTLINE, 1.0)
        poly([P(2.6, 13.8 + my), P(14, 13 + my), P(12.8, 12.6 + my + drop), P(4.8, 13.4 + my + drop)], (74, 22, 30, 255), OUTLINE, 0.8)
        poly([P(3.4, 14 + my), P(13.4, 13.4 + my), P(13, 15.8 + my), P(4, 16.4 + my)], TEETH, None, 0)
        if spec.gold_tooth:
            poly([P(9.4, 13.7 + my), P(11.6, 13.5 + my), P(11.5, 15.9 + my), P(9.5, 16.1 + my)], GOLD, None, 0)
    else:
        poly([P(2.8, 16.4 + my), P(6.2, 14.6 + my), P(8.6, 15.5 + my), P(11, 14.5 + my), P(14.6, 16.4 + my), P(8.6, 17.3 + my)], _mix(lip, OUTLINE, 0.3), OUTLINE, 0.8)
        poly([P(4, 16.9 + my), P(8.6, 17.3 + my), P(13.6, 16.8 + my), P(11.4, 20.2 + my), P(6.4, 20.5 + my)], lip, OUTLINE, 0.8)
        line([P(7, 18.6 + my), P(10.4, 18.4 + my)], _mix(lip, WHITE, 0.4), 0.9)
    # her hair at the brow, and what she wears over the mass of it
    roots = [P(-19, -9.5), P(-6, -12.5), P(8, -13), P(19.4, -10.5), P(19, -7.4), P(14, -9.2), P(9, -7.4), P(3, -9.4), P(-3, -7.6), P(-9, -9.4), P(-14, -6.4), P(-18.4, -4.4)]
    poly(roots, pal.hair, OUTLINE, 1.3)
    dome = [P(-20.5, -8.5), P(-24, -16), P(-20, -25), P(-10, -30), P(4, -29.5), P(13.5, -24), P(19, -15), P(19.6, -10.5), P(8, -13), P(-6, -12.5)]
    band = [P(-20.5, -8.5), P(-6, -12.5), P(8, -13), P(19.6, -10.5), P(19.6, -14.4), P(8, -16.8), P(-6, -16.2), P(-21.6, -12.4)]
    if spec.headwear == "bandana":
        poly(dome, pal.bandana, OUTLINE, 1.7)
        poly(band, pal.bandana_dark, OUTLINE, 0.9)
        line([P(-11, -25.5), P(3, -26), P(11, -22)], _mix(pal.bandana, WHITE, 0.3), 1.4)
        line([P(-19, -19), P(-13, -24)], _mix(pal.bandana, OUTLINE, 0.3), 1.1)
        line([P(-2, -17.5), P(1, -28)], _mix(pal.bandana, OUTLINE, 0.25), 1.0)
        circle(P(-21.5, -12), 4.4, pal.bandana_dark, OUTLINE, 1.2)
    elif spec.headwear == "band":
        # her hair is over the band, in waves
        poly(dome, pal.hair, OUTLINE, 1.7)
        for wave in (((-17, -17), (-12, -25), (-4, -27)), ((-6, -17.5), (0, -25), (9, -24)), ((6, -18), (12, -21), (16, -16))):
            line([P(*q) for q in wave], pal.hair_hi, 1.4)
        poly(band, pal.bandana, OUTLINE, 1.1)
        line([P(-18, -11.5), P(-6, -14.6), P(8, -15.2), P(18, -12.8)], _mix(pal.bandana, WHITE, 0.3), 1.1)
        circle(P(-21.5, -12), 4.4, pal.bandana_dark, OUTLINE, 1.2)
    else:
        # A tricorn: the crown, the brim turned up to a point at the front and
        # at the back, a gold cord round it, and a plume.
        hat = pal.hat
        poly([P(-13, -22), P(-24, -40), P(-35, -37), P(-33, -26), P(-22, -17)], pal.bandana, OUTLINE, 1.4)
        line([P(-15, -21), P(-29, -35)], pal.bandana_dark, 1.3)
        poly([P(-16, -12), P(-14, -27), P(-5, -32), P(9, -30), P(15, -13)], _mix(hat, WHITE, 0.08), OUTLINE, 1.7)
        brim = [P(-33, -9), P(-24, -21), P(-10, -17.5), P(4, -19.5), P(15, -22), P(31, -10), P(16, -8.5), P(1, -12.5), P(-14, -9)]
        poly(brim, hat, OUTLINE, 1.8)
        line([P(-30.5, -10.4), P(-23.4, -18.6), P(-10, -15.3), P(4, -17.2), P(15, -19.6), P(27.5, -10.6)], GOLD, 1.6)
        line([P(-14, -9), P(1, -12.5), P(16, -8.5)], _mix(hat, WHITE, 0.18), 1.0)


# ---- The frame -----------------------------------------------------------------


def _hair_rows(spec: VariantSpec):
    """``(back, front)``: the strands that hang behind her and the ones that
    come over her near shoulder. A row is ``(x, y, length, degrees)``: where on
    the head it starts, and how it hangs."""
    if spec.hair == "dreads":
        return ((-22, 4, 62, 106), (-15, 8, 68, 99), (-7, 10, 64, 93), (3, 10, 54, 86)), ((-16, 6, 46, 101), (-10, 11, 40, 95))
    if spec.hair == "braid":
        return (), ((-13, 9, 54, 97),)
    return ((-23, 6, 60, 104), (-4, 12, 52, 90)), ((-16, 6, 50, 100), (-10, 12, 40, 94))


def _draw_variant(
    anim: str, frame_idx: int, nframes: int, spec: VariantSpec
) -> Image.Image:
    img = Image.new(
        "RGBA", (WORK_FRAME_SIZE[0] * SUPER, WORK_FRAME_SIZE[1] * SUPER), (0, 0, 0, 0)
    )
    pose = pose_for(anim, frame_idx, nframes)
    if spec.blade == "none" and anim != "death":
        _hold_a_gun(pose, anim, frame_idx)
    pal = spec.palette
    slug = spec.slug
    J = _rig_evaluate(pose, spec, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    turn = J.body_rot
    lean = J.lean

    def put(key, paint, at: Point, name: str, degrees: float = 0.0) -> None:
        """A piece at ``at`` in the frame of the body, turned with the body."""
        _put(img, key, paint, J.world(at), name, degrees + turn)

    along = rig.rot((1.0, 0.0), J.weapon)

    # the arc of the swing, behind her
    if pose.swoosh:
        a0, a1, strength = pose.swoosh

        def swoosh(d) -> None:
            steps = 26
            outer, inner = [], []
            for k in range(steps + 1):
                f = k / steps
                a = math.radians(_lerp(a0, a1, f))
                wide = (10.0 + 30.0 * f) * strength
                outer.append((HX + 126.0 * math.cos(a), HY + 126.0 * math.sin(a)))
                inner.append((HX + (126.0 - wide) * math.cos(a), HY + (126.0 - wide) * math.sin(a)))
            d.polygon([_pt(q) for q in outer + inner[::-1]], fill=pal.slash[:3] + (int(105 * strength),))
            d.line([_pt(q) for q in outer], fill=(255, 255, 255, int(170 * strength)), width=_s(2.2))

        put(("swoosh", pal.slash, a0, a1, strength), swoosh, rig.add(J.right_hand, (-10.0 * along[0], -10.0 * along[1])), "swoosh")

    # her hair behind her
    head_scale = HEAD * spec.head
    back, front = _hair_rows(spec)
    strand = {"dreads": _paint_dread, "braid": _paint_braid, "waves": _paint_lock}[spec.hair]

    def strands(rows, tag: str) -> None:
        for k, (dx, dy, length, hang) in enumerate(rows):
            start = rig.add(J.head, rig.rot((dx * head_scale, dy * head_scale), J.head_rot))
            # a strand hangs down; when she is down it lies on the deck, away from her
            down = _lerp(hang + lean * 0.2, 176.0 - 5.0 * k, min(1.0, -turn / 90.0))
            put(("strand", slug, length), lambda d, length=length: strand(d, spec, length), start, f"{tag}_{k}", down - turn + pose.hair_swing * (1.0 + 0.25 * k))

    put(("mane", slug), lambda d: _paint_mane(d, spec), J.head, "mane", J.head_rot + pose.hair_swing * 0.8)
    strands(back, "hair_back")

    # the legs and the boots
    for side, hip, knee, ankle, foot in (
        ("left", J.left_hip, J.left_knee, J.left_ankle, pose.l_foot),
        ("right", J.right_hip, J.right_knee, J.right_ankle, pose.r_foot),
    ):
        put(("thigh", slug), lambda d: _limb(d, THIGH * spec.tall, 13.0, 11.0, pal.skin_shadow, ink=1.5), hip, f"{side}_thigh", rig.angle(hip, knee))
        put(("shaft", slug), lambda d: _paint_boot_shaft(d, spec), knee, f"{side}_shaft", rig.angle(knee, ankle))
        put(("foot", slug), lambda d: _paint_foot(d, spec), ankle, f"{side}_foot", -foot[1] * 2.2)

    # the skirt
    pelvis = J.pelvis
    wl, wr = rig.rot((-37.0 * spec.hip, 2.0), lean), rig.rot((37.0 * spec.hip, 2.0), lean)
    reach = 56.0 * spec.hip
    hl = min(-reach, min(J.left_ankle[0], J.left_knee[0]) - pelvis[0] - 17.0)
    hr = max(reach, max(J.right_ankle[0], J.right_knee[0]) - pelvis[0] + 17.0)
    hem_y = -9.0 - pelvis[1]
    shape = tuple(round(v, 1) for v in (*wl, *wr, hl, hr, hem_y, pose.skirt_sway))
    put(("skirt", slug) + shape, lambda d: _paint_skirt(d, spec, wl, wr, hl, hr, hem_y, pose.skirt_sway), pelvis, "skirt")

    # the torso, the end of her sash, and the hair that comes over her shoulder
    sw, cx = J.shoulder_half, J.chest_x
    put(("torso", slug, round(sw, 1), round(cx, 1)), lambda d: _paint_torso(d, spec, sw, cx), pelvis, "torso", lean)
    put(("sash_tail", slug), lambda d: _paint_sash_tail(d, spec), rig.add(pelvis, rig.rot((-31.0 * spec.hip, -1.0), lean)), "sash_tail", 100.0 - turn + pose.skirt_sway * 1.5)
    strands(front, "hair_front")

    # the head: one piece for each face
    mouth = round(pose.mouth, 3)
    put(("head", slug, pose.blink, pose.x_eyes, mouth), lambda d: _paint_head(d, spec, mouth, pose.blink, pose.x_eyes), J.head, "head", J.head_rot)

    # the arms: the far one, then the one with the cleaver
    for side, shoulder, elbow, hand in (
        ("left", J.left_shoulder, J.left_elbow, J.left_hand),
        ("right", J.right_shoulder, J.right_elbow, J.right_hand),
    ):
        put(("upper", slug), lambda d: _paint_upper_arm(d, spec), shoulder, f"{side}_upper_arm", rig.angle(shoulder, elbow))
        put(("fore", slug), lambda d: _paint_forearm(d, spec), elbow, f"{side}_forearm", rig.angle(elbow, hand))
    if spec.mark == "pauldron":
        put(("pauldron", slug), lambda d: _paint_pauldron(d, spec), J.right_shoulder, "pauldron", rig.angle(J.right_shoulder, J.right_elbow))

    # the cleaver: in her lead hand, or out of it on its way to the deck
    cleaver = ("cleaver", slug)
    if spec.blade == "none":
        pass
    elif pose.loose_weapon is None:
        put(cleaver, lambda d: _paint_cleaver(d, spec), J.right_hand, "cleaver", J.weapon)
    else:
        at, degrees = pose.loose_weapon
        work = (J.stance[0] + at[0], J.stance[1] + at[1])
        _put(img, cleaver, lambda d: _paint_cleaver(d, spec), work, "cleaver", degrees)
    # The hands. The track `right_hand` is what the game reads to draw an item
    # she holds: the item is where this part is, and it turns as this part is
    # turned. So the lead hand is turned as the haft is (`J.weapon`), from the
    # rest the game states, and not as her forearm is.
    put(("fist", slug), lambda d: _paint_fist(d, spec), J.left_hand, "left_hand", rig.angle(J.left_elbow, J.left_hand))
    put(("fist", slug), lambda d: _paint_fist(d, spec), J.right_hand, "right_hand", J.weapon + ITEM_REST_ANGLE)

    if pose.chips:
        # bits of the deck, where the belly of the blade went in
        tip = rig.add(J.right_hand, rig.rot((90.0, 36.0), J.weapon))

        def chip(d) -> None:
            _poly(d, [(HX - 3.0, HY - 2.0), (HX + 3.5, HY), (HX, HY + 3.5)], (150, 112, 70, 255), OUTLINE, 0.7)

        for k, (dx, dy) in enumerate(((-16, -14), (-4, -24), (10, -17), (20, -6))):
            put(("chip",), chip, rig.add(tip, (dx + math.sin(frame_idx + k) * 2.0, dy)), f"chip_{k}", k * 40.0)

    return _downsample(img)


def _body_box(spec: VariantSpec) -> Tuple[float, float, float, float]:
    """``(x0, y0, x1, y1)`` of her body in the drawn frame: from the top of
    her head to her soles, as wide as her skirt. The cleaver, a plume and the
    tails of a bandana are not her body."""
    cx, ground = float(round(WORK_FRAME_SIZE[0] * 0.46)), float(round(WORK_FRAME_SIZE[1] * 0.67))
    half = 56.0 * spec.hip + 2.0
    head = (HIP_Y - rig.CHEST) * spec.tall - 31.0 * (0.4 + 0.6 * spec.head)
    top = head - 30.0 * HEAD * spec.head - 2.0
    return (cx - half, ground + top, cx + half, ground)


def _body_metrics(spec: VariantSpec):
    """The ``body_metrics_fn`` of a variant. Without it the box is the alpha
    box of the first frame, and that has the cleaver in it: the body the world
    collides with was twice as wide as she is."""

    def metrics(fw: int, fh: int) -> dict:
        x0, y0, x1, y1 = _body_box(spec)
        x, y = int(math.floor(x0)), int(math.floor(y0))
        w, h = int(math.ceil(x1)) - x, int(math.ceil(y1)) - y
        feet = (x + w / 2.0, float(y + h))
        return {
            "body_pixel_bbox": {"x": x, "y": y, "w": w, "h": h},
            "feet_pixel": {"x": feet[0], "y": feet[1]},
            "feet_anchor_norm": {"x": round((feet[0] - fw / 2.0) / fw, 6), "y": round((fh / 2.0 - feet[1]) / fh, 6)},
        }

    return metrics


def render_variant(spec: VariantSpec, out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_size = opts.get("frame_size", FRAME_SIZE)
    target_name = f"{BASE_TARGET_NAME}_{spec.slug}"

    def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        return _draw_variant(anim, frame_idx, nframes, spec)

    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=target_name,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=frame_size,
        crop_margin=10,
        auto_crop=True,
        body_metrics_fn=_body_metrics(spec),
    )
    parts = publish_rig_flipbook(target_name, ROWS, render_frame, outputs, frame_transform, out_dir)
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ] + list(parts.values())


PORTRAIT_FILES = tuple(
    name
    for slug in VARIANTS
    for name in (
        f"{BASE_TARGET_NAME}_{slug}_portraits.png",
        f"{BASE_TARGET_NAME}_{slug}_portraits.ron",
    )
)

# This target installs one sheet PER VARIANT, not one sheet named after itself,
# so the default `<target>_spritesheet.*` list described files it never writes
# and omitted every file it does. `install` below is the authority on what gets
# copied; this declaration exists so a reader — and the install audit — can tell
# what this target is responsible for without running it.
SHEET_FILES = tuple(
    name
    for slug in VARIANTS
    for name in (
        f"{BASE_TARGET_NAME}_{slug}_spritesheet.png",
        f"{BASE_TARGET_NAME}_{slug}_spritesheet.yaml",
        f"{BASE_TARGET_NAME}_{slug}_spritesheet.ron",
    )
)


def render_portraits(out_dir: str | Path, variant: str = "all", **opts) -> List[Path]:
    """Publish freshly rendered default portraits for every heavy variant."""

    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = VARIANTS.items() if variant == "all" else [(variant, VARIANTS[variant])]
    outputs: List[Path] = []
    for slug, spec in selected:
        source = _draw_variant("idle", 1, 6, spec)
        portrait = render_canonical_portrait(
            source, actor_metadata=ACTOR_METADATA
        )
        target = f"{BASE_TARGET_NAME}_{slug}"
        outputs.extend(
            write_portrait_sheet(
                target, {"default": PortraitClip.still(portrait)}, out_dir
            )
        )
    return outputs


def render(out_dir: str | Path, variant: str = "all", **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []
    if variant == "all":
        for slug, spec in VARIANTS.items():
            outputs.extend(render_variant(spec, out_dir / slug, **opts))
    else:
        spec = VARIANTS[variant]
        outputs.extend(render_variant(spec, out_dir, **opts))
    return outputs


# CLI hook for `render-publish pirate_heavy`. Each variant's sheet
# files live under `out_dir/{slug}/` from `render` above; this
# function walks every variant subdir and copies its PNG + YAML +
# RON to the destination sprites folder (flat, per-variant
# filenames). Mirrors the pattern in `sandbag.install`.


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render one or more pirate-heavy sprite variants."
    )
    parser.add_argument("--variant", choices=["all", *VARIANTS.keys()], default="all")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "generated"
        / "pirate_heavy_variants",
    )
    args = parser.parse_args(argv)
    for path in render(args.out_dir, variant=args.variant):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
