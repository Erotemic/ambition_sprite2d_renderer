"""Authored fighting-game pose library for GNU-ton's *D2* scholar.

The existing SVG is the only anatomy/art authority.  This file defines pose
VALUES in the shared humanoid semantic language: planted/airborne feet,
upper-arm and elbow directions, world-facing hand/quill direction, expressions,
and independent book/coat/wig controls.  It does not define combat rules,
hitboxes, invulnerability, or runtime state transitions.

Canvas +x is forward; angles are degrees in screen coordinates (y down).
Keep the boss clips in build_gnu_ton_scholar_villain_rig.py unchanged.
"""
from __future__ import annotations

import math

import build_gnu_ton_scholar_villain_rig as B

J = B.BODY.J
HX = B.BODY.rest_x


def ground(side: str, dx: float = 0, lift: float = 0, pitch: float = 0):
    return B.g(HX(side) + dx, lift, pitch)


def air(side: str, dx: float = 0, dy: float = 0, pitch: float = 0):
    return B.b(dx, dy, pitch)


# Duelist silhouette: planted asymmetric legs, quill raised off the shoulder,
# book at the back hip.  Distinct from the boss's formal upright rest.
STANCE = {
    **B.REST,
    "y": 9, "lean": 11, "head": -4,
    "nu": -57, "ne": 24, "nw": -80,
    "fu": 111, "fe": -20, "fw": 105,
    "nf": ground("near", 16), "ff": ground("far", -18),
    "eye": "open", "mouth": "closed", "book": 1, "book_open": 0,
    "quill": 1, "stars": 0, "apple": 0,
}

# Flying pose: feet are carried by the body rather than being world-pinned.
FLIGHT = {
    **STANCE, "y": -24, "lean": 9, "head": -6,
    "nf": air("near", 8, -25, 12), "ff": air("far", -8, -28, -9),
    "nu": -28, "ne": 18, "fu": 143, "fe": -8,
    "near_tail": 14, "far_tail": -12, "queue": 12,
}


def hold(pose: dict, *, sway=0, flutter=0, queue=0):
    return B.clip([(0.0, pose), (1.0, pose)], sway=sway, flutter=flutter, queue=queue)


def action(wind: dict, contact: dict, recover: dict | None = None, *,
           start: dict | None = None, end: dict | None = None,
           sway=2, flutter=3, queue=2):
    """Readable anticipation -> impact -> followthrough -> recovery arc."""
    home = dict(STANCE if start is None else start)
    keys = [(0.0, home),
            (0.24, {**wind, "ease": "out"}),
            (0.48, {**contact, "ease": "in"}),
            (0.72, {**(recover or {}), "ease": "out"}),
            (1.0, home)]
    return B.clip(keys, sway=sway, flutter=flutter, queue=queue)


def transition(destination: dict, *, source: dict | None = None, sway=1):
    return B.clip([(0.0, STANCE if source is None else source),
                   (1.0, destination)], sway=sway)


def cycle_legs(kind: str):
    """Foot-contact-aware in-place run/walk, never translating an entire rig."""
    stride = {"walk": 20, "run": 30, "crouch_walk": 12}[kind]
    lift = {"walk": 12, "run": 20, "crouch_walk": 6}[kind]
    crouched = kind == "crouch_walk"
    fast = kind == "run"
    idle_encoding = hold(STANCE, sway=2, flutter=3, queue=2)

    def draw(i: int, n: int, t: float):
        theta = math.tau * t
        pose = {
            **STANCE,
            "y": (22 if crouched else 0) + (3.0 if fast else 1.3) * math.sin(2 * theta),
            "lean": (18 if fast else 16 if crouched else 9) + 3 * math.sin(theta),
            "head": -3 + 2 * math.sin(theta + 0.4),
            "nu": -57 + (31 if fast else 22) * math.sin(theta + 0.4),
            "fu": 111 - (30 if fast else 20) * math.sin(theta + 0.4),
            "near_tail": 5 * math.sin(theta + 0.3),
            "far_tail": -6 * math.sin(theta + 0.3),
        }
        # Back half of stride is grounded. Forward swing lifts the foot.
        for side, phase in (("near", 0), ("far", math.pi)):
            s = theta + phase
            dx = stride * math.cos(s)
            h = lift * max(0, math.sin(s))
            pose["nf" if side == "near" else "ff"] = ground(side, dx, h)
        channels = idle_encoding(i, n, t)
        channels.update(B.BODY.channels(pose))
        # Above, angle/IK channels use the changing pose, while baseline
        # expression and accessory opacity channels come from the shared rig.
        return channels

    return draw


CROUCH = {**STANCE, "y": 25, "lean": 19, "head": -8,
          "nu": 19, "ne": 58, "fu": 157, "fe": 26,
          "nf": ground("near", 15), "ff": ground("far", -19)}
SHIELD = {**STANCE, "lean": -9, "nu": -14, "ne": 92, "nw": -75,
          # Bring the book in front of the chest and in front of the coat,
          # below the near arm. The far-hand bone also owns the book pages.
          "fu": 15, "fe": 95, "fw": -42, "fz": 42, "eye": "angry",
          "book": 1, "quill": 1, "nf": ground("near", 12), "ff": ground("far", -14)}
GRAB = {**STANCE, "lean": 14, "nu": -9, "ne": -3, "nw": -20,
        "fu": 1, "fe": 0, "fw": -3, "quill": 0, "book": 0,
        "nf": ground("near", 18), "ff": ground("far", -15)}
PRONE = {**STANCE, "spin": -81, "y": 55, "x": 58, "head": -81,
         "nu": 126, "ne": -8, "fu": -165, "fe": 14,
         "nf": air("near", -4, -5), "ff": air("far", -10, -6),
         "quill": 0, "book": 0, "eye": "shut", "mouth": "grit",
         **B.arm_depth(-43)}

CLIPS = {}
ROW_SPECS = {}


def register(name: str, clip, frames=7, ms=75, loop=False):
    if name in CLIPS:
        raise ValueError(f"duplicate fighter clip: {name}")
    CLIPS[name] = clip
    ROW_SPECS[name] = (name, frames, ms, loop)


# Neutral, mobility and platform traversal -------------------------------------
register("idle", hold(STANCE, sway=1.5, flutter=2, queue=1), 10, 105, True)
register("idle_look_up", hold({**STANCE, "head": -19, "nu": -70, "nw": -85}), 6, 105, True)
register("walk", cycle_legs("walk"), 8, 93, True)
register("run", cycle_legs("run"), 8, 67, True)
register("dash_startup", action({"y": 13, "lean": -9, "head": 8},
                                 {"x": 12, "lean": 35, "head": -3,
                                  "nu": 23, "fu": 177, "nf": ground("near", 18)},
                                 {"lean": 30}), 5, 55)
register("dash", action({"y": 8, "lean": 12},
                         {"x": 18, "lean": 36, "head": -15, "nu": 23,
                          "nf": ground("near", 31, 5), "ff": ground("far", -28, 5)},
                         {"lean": 23, "near_tail": 22}), 6, 65)
register("walk_stop", action({"lean": 17, "x": 6},
                              {"y": 8, "lean": -8, "nf": ground("near", 12),
                               "ff": ground("far", -16)},
                              {"y": 2, "lean": 2}), 6, 67)
register("turnaround", action({"x": 7, "lean": 24},
                               {"y": 15, "lean": -19, "head": 13,
                                "nu": 51, "ne": 42, "fu": -38, "fe": -10,
                                "nf": ground("near", -10, 4)},
                               {"lean": -7}), 6, 70)
register("crouch_start", transition(CROUCH), 5, 65)
register("crouch", hold(CROUCH, sway=1), 6, 100, True)
register("crouch_walk", cycle_legs("crouch_walk"), 8, 100, True)
register("crouch_end", transition(STANCE, source=CROUCH), 5, 65)
register("jump_squat", transition({**CROUCH, "y": 31, "head": -10,
                                  "near_tail": 8}), 5, 54)
register("jump", action({"y": 20, "lean": 0, "nf": ground("near", 10),
                         "ff": ground("far", -7)},
                        {**FLIGHT, "y": -35, "nu": -80, "fu": -125,
                         "nf": air("near", 15, -39), "ff": air("far", -9, -12)},
                        {**FLIGHT, "y": -28, "nu": -42},
                        start=STANCE, end=FLIGHT), 8, 77)
register("double_jump", action({**FLIGHT, "y": -27, "head": 10},
                               {**FLIGHT, "y": -51, "spin": 25, "head": 25,
                                "nf": air("near", 14, -38),
                                "ff": air("far", -9, -47), "nu": -113,
                                "fu": -92},
                               {**FLIGHT, "spin": 0, "y": -35},
                               start=FLIGHT, end=FLIGHT), 8, 72)
register("fall", hold({**FLIGHT, "y": -18, "lean": -8, "head": 5,
                        "nu": 12, "fu": 176, "queue": -6},
                       sway=3, flutter=5, queue=3), 8, 95, True)
register("fall_special", hold({**FLIGHT, "y": -22, "lean": 24,
                                "nu": 85, "fu": 120, "eye": "shut",
                                "mouth": "grit"}, flutter=4), 7, 87, True)
register("land", transition({**CROUCH, "y": 19}, source=FLIGHT), 6, 55)
register("land_hard", action({**FLIGHT, "y": -6, "lean": 30},
                              {**CROUCH, "y": 34, "lean": 36,
                               "nu": 70, "fu": 135, "mouth": "grit"},
                              CROUCH, start=FLIGHT), 8, 70)
register("land_recovery", transition(STANCE, source=CROUCH), 6, 75)
register("platform_drop", transition({**FLIGHT, "y": 12,
                                      "nu": 46, "fu": 157}, source=CROUCH), 6, 85)
register("wall_grab", hold({**FLIGHT, "y": -20, "lean": 20,
                             "nu": -76, "ne": 20, "fu": -110,
                             "nf": air("near", -4, -47),
                             "ff": air("far", -16, -30), "quill": 0}), 6, 100, True)
register("wall_jump", action({**FLIGHT, "y": -20, "lean": 30,
                              "nu": -65, "nf": air("near", -9, -38)},
                             {**FLIGHT, "y": -47, "x": -30, "lean": -20,
                              "nu": 112, "fu": 13, "head": -10},
                             {**FLIGHT, "y": -26, "x": -15},
                             start=FLIGHT, end=FLIGHT), 7, 67)
ledge = {**FLIGHT, "y": -22, "lean": 28, "head": -13,
         "nu": -83, "ne": -20, "fu": -97, "fe": -5,
         "nf": air("near", -7, -38), "ff": air("far", -2, -15),
         "quill": 0, "book": 0}
register("ledge_catch", transition(ledge, source=FLIGHT), 5, 58)
register("ledge_grab", hold(ledge, flutter=1, queue=2), 6, 115, True)
register("ledge_getup", action({**ledge, "y": -10, "nu": -79},
                                {**CROUCH, "y": 24, "nu": 34, "fu": 150},
                                {**CROUCH, "y": 12}, start=ledge), 7, 58)
register("ledge_roll", action({**ledge, "head": -15},
                               {**PRONE, "spin": -145, "head": -145, "y": 10,
                                "x": 16, "nf": air("near", -12, -18),
                                "ff": air("far", 8, -16)},
                               {**CROUCH, "x": 25}, start=ledge), 8, 45)
register("ledge_attack", action({**ledge, "y": 0, "head": -7},
                                 {**CROUCH, "nu": -15, "ne": -8,
                                  "nw": -8, "head": -9, "mouth": "grit"},
                                 CROUCH, start=ledge), 8, 44)
# The runtime also uses this explicit name for the timed ledge getup strike.
register("ledge_getup_attack", action({**ledge, "y": 0, "head": -7},
                                       {**CROUCH, "nu": -13, "ne": -8,
                                        "nw": -7, "head": -8, "mouth": "grit"},
                                       CROUCH, start=ledge), 8, 37)
register("ledge_jump", action({**ledge, "y": -12},
                               {**FLIGHT, "y": -45, "nu": -113, "fu": -99},
                               FLIGHT, start=ledge, end=FLIGHT), 7, 65)
register("ledge_drop", transition({**FLIGHT, "y": 15, "lean": -6},
                                  source=ledge), 6, 65)

# Defense -----------------------------------------------------------------------
register("shield_raise", transition(SHIELD), 5, 65)
register("shield_hold", hold(SHIELD, sway=1.5, flutter=1), 7, 105, True)
register("shield_hit", action({**SHIELD, "lean": -4},
                              {**SHIELD, "x": -10, "lean": -21,
                               "head": 18, "eye": "shut", "mouth": "grit"},
                              SHIELD, start=SHIELD, end=SHIELD), 6, 75)
register("shield_release", transition(STANCE, source=SHIELD), 5, 55)
register("parry", action({**SHIELD, "lean": 11},
                         {**SHIELD, "nu": -43, "ne": 65,
                          "fu": -22, "fe": 94, "head": -13, "mouth": "smile"},
                         SHIELD), 6, 56)
register("spot_dodge", action({"y": 7, "lean": -9},
                              {**CROUCH, "y": 33, "lean": -17,
                               "nu": 77, "fu": 98, "eye": "shut",
                               "quill": 0}, CROUCH), 7, 57)
roll_start = {**CROUCH, "quill": 0, "book": 0}
register("roll", action(roll_start,
                        {**PRONE, "spin": 125, "head": 125, "x": 20,
                         "y": 32, "nf": air("near", 14, -16),
                         "ff": air("far", -7, -12)},
                        {**CROUCH, "x": 35, "y": 24}, start=roll_start), 8, 50)
register("roll_back", action(roll_start,
                             {**PRONE, "spin": -125, "head": -125, "x": 17,
                              "y": 33, "nf": air("near", 5, -18),
                              "ff": air("far", -9, -14)},
                             {**CROUCH, "x": -31, "y": 23}, start=roll_start), 8, 50)
register("air_dodge", action({**FLIGHT, "head": -15},
                             {**FLIGHT, "spin": -29, "head": -29,
                              "nu": 134, "fu": -17,
                              "nf": air("near", 20, -29),
                              "ff": air("far", -14, -23), "eye": "shut"},
                             FLIGHT, start=FLIGHT, end=FLIGHT), 7, 60)
register("tech", action({**PRONE, "y": 27},
                        {**CROUCH, "y": 18, "x": 4, "head": -14},
                        CROUCH, start=PRONE), 7, 60)

# Ground attacks: quill fencing, sweeping jacket and slammed Principia ------
register("jab", action({"lean": -5, "nu": -58, "ne": 62, "nw": -90,
                        "eye": "angry"},
                       {"lean": 17, "x": 9, "nu": 2, "ne": 0,
                        "nw": -15, "mouth": "grit", "nf": ground("near", 17)},
                       {"lean": 9, "nu": 12, "ne": 2}), 6, 49)
register("jab_2", action({"lean": 9, "nu": 31, "ne": 78},
                         {"lean": 20, "x": 12, "nu": -7, "ne": -11,
                          "nw": -7, "head": 4, "eye": "angry"},
                         {"nu": 21, "ne": 12}), 6, 49)
register("jab_3", action({"x": -6, "lean": -7, "nu": -70,
                         "ne": 54, "queue": -5},
                         {"x": 18, "lean": 34, "nu": -16,
                          "ne": -20, "nw": -4, "mouth": "open",
                          "nf": ground("near", 22), "near_tail": 23},
                         {"nu": 29, "ne": -4, "near_tail": 10}), 8, 54)
register("dash_attack", action({"x": -5, "y": 12, "lean": 29,
                               "nf": ground("near", 8)},
                              {"x": 31, "lean": 39, "nu": 5, "ne": -12,
                               "nw": -2, "fu": -28, "eye": "angry",
                               "nf": ground("near", 35),
                               "ff": ground("far", -28, 4)},
                              {"x": 25, "lean": 23, "near_tail": 24}), 8, 62)
register("attack_side", action({"x": -6, "nu": -87, "ne": 87,
                                "nw": -86, "lean": -7},
                               {"x": 12, "lean": 22, "nu": -16,
                                "ne": -15, "nw": 0, "head": -10,
                                "nf": ground("near", 20)},
                               {"lean": 18, "nu": 17,
                                "near_tail": 14}), 7, 62)
register("attack_up", action({"lean": 20, "y": 10,
                              "nu": 37, "ne": 86, "head": -23},
                             {"lean": -8, "y": -6, "nu": -102,
                              "ne": 0, "nw": -90, "head": -26,
                              "far_tail": -12, "mouth": "open"},
                             {"nu": -72, "ne": 10}), 7, 66)
register("attack_down", action({"y": 19, "lean": 17,
                                "nu": -60, "ne": 78},
                               {"y": 22, "lean": 32,
                                "nu": 48, "ne": -4, "nw": 37,
                                "head": 10, "nf": ground("near", 22),
                                "eye": "angry"}, CROUCH), 8, 61)
register("smash_charge", hold({**CROUCH, "y": 18, "lean": -10,
                               "nu": -111, "ne": 101, "nw": -88,
                               "head": -10, "mouth": "grit", "eye": "angry",
                               "near_tail": -7},
                              sway=3, flutter=5, queue=4), 8, 91, True)
register("smash_forward", action({"x": -14, "lean": -15,
                                  "nu": -133, "ne": 84, "nw": -79,
                                  "head": -12, "eye": "angry"},
                                 {"x": 23, "lean": 41,
                                  "nu": 2, "ne": -17, "nw": 0,
                                  "head": -5, "mouth": "open",
                                  "nf": ground("near", 30),
                                  "ff": ground("far", -24),
                                  "near_tail": 27},
                                 {"x": 16, "lean": 27, "nu": 25,
                                  "ne": -8}, flutter=6), 9, 63)
register("smash_up", action({**CROUCH, "nu": -35,
                             "ne": 106, "head": -15},
                            {"y": -17, "lean": -17,
                             "nu": -106, "ne": -2, "nw": -93,
                             "fu": -85, "fe": 13, "head": -30,
                             "mouth": "open", "near_tail": 28,
                             "ff": ground("far", -17)},
                            {"nu": -48, "lean": -10}, flutter=6), 9, 68)
register("smash_down", action({"lean": -12, "nu": -100,
                               "ne": 66, "y": 12},
                              {**CROUCH, "y": 28, "lean": 37,
                               "nu": 50, "ne": -8, "nw": 57,
                               "fu": 150, "fe": -7,
                               "nf": ground("near", 30),
                               "ff": ground("far", -29),
                               "mouth": "grit", "near_tail": 25},
                              {"y": 12, "lean": 15}, flutter=5), 9, 65)

# Aerials: all leg targets are body-relative; no planted feet in the air -----
register("air_neutral", action({**FLIGHT, "nu": -50, "fu": 166},
                               {**FLIGHT, "spin": 45, "head": 45,
                                "nu": 2, "ne": -24, "fu": -29, "fe": 14,
                                "nf": air("near", 24, -38),
                                "ff": air("far", -21, -16)},
                               {**FLIGHT, "spin": 0},
                               start=FLIGHT, end=FLIGHT), 8, 64)
register("air_forward", action({**FLIGHT, "nu": -81, "ne": 58},
                               {**FLIGHT, "nu": -2, "ne": -15,
                                "nw": 0, "lean": 29,
                                "nf": air("near", 27, -16),
                                "ff": air("far", -17, -32),
                                "eye": "angry"}, FLIGHT,
                               start=FLIGHT, end=FLIGHT), 8, 62)
register("air_back", action({**FLIGHT, "nu": 23, "fu": -105},
                            {**FLIGHT, "lean": -23, "fu": -177, "fe": -9,
                             "fw": 176, "nf": air("near", 17, -28),
                             "ff": air("far", -33, -30)}, FLIGHT,
                            start=FLIGHT, end=FLIGHT), 8, 64)
register("air_up", action({**FLIGHT, "head": -29,
                           "nu": -42, "ne": 86},
                          {**FLIGHT, "nu": -109, "ne": 0,
                           "nw": -91, "head": -32, "fu": -54,
                           "near_tail": 22}, FLIGHT,
                          start=FLIGHT, end=FLIGHT), 8, 65)
register("air_down", action({**FLIGHT, "lean": 30,
                             "nu": 16, "ne": 72},
                            {**FLIGHT, "lean": 35,
                             "nu": 89, "ne": -9, "nw": 89,
                             "nf": air("near", 10, 27, 0),
                             "ff": air("far", -13, -48, 8),
                             "eye": "angry"}, FLIGHT,
                            start=FLIGHT, end=FLIGHT), 8, 67)
register("air_land", transition(CROUCH, source=FLIGHT), 5, 65)

# Four concept special attacks. No hit/reflect/projectile rules are installed.
register("special_neutral", action({"book": 0, "book_open": 1,
                                    "fu": -123, "fe": 14, "fw": -40},
                                   {"book": 0, "book_open": 1,
                                    "fu": -137, "fe": -10, "fw": -45,
                                    "nu": -80, "ne": 5, "nw": -86,
                                    "head": -21, "mouth": "open",
                                    "near_tail": 19, "queue": 10},
                                   {"book": 0, "book_open": 1,
                                    "nu": -54, "head": -14}, flutter=4), 9, 74)
register("special_side", action({"x": -10, "lean": -12,
                                 "nu": -125, "ne": 90},
                                {"x": 25, "lean": 36,
                                 "nu": -11, "ne": -12, "nw": -6,
                                 "head": -4, "mouth": "open",
                                 "nf": ground("near", 29),
                                 "near_tail": 26},
                                {"x": 20, "lean": 20}), 9, 68)
register("special_up", action({**CROUCH, "book": 0, "book_open": 1,
                               "nu": -92, "head": -28},
                              {**FLIGHT, "y": -54, "nu": -95,
                               "ne": -8, "nw": -89, "fu": -114,
                               "book": 0, "book_open": 1,
                               "head": -28, "mouth": "open",
                               "near_tail": 26},
                              {**FLIGHT, "y": -33, "book": 0,
                               "book_open": 0},
                              end=FLIGHT, flutter=5), 9, 70)
register("special_down", action({"book": 0, "book_open": 1,
                                 "lean": 0, "nu": -60, "fu": -72,
                                 "head": -15},
                                {**SHIELD, "book": 0, "book_open": 1,
                                 "nu": -14, "ne": 94, "fw": -90,
                                 "eye": "angry", "mouth": "grit",
                                 "near_tail": -18},
                                {"book": 0, "book_open": 1, "lean": 5}), 9, 79)

# Grabs / throws ---------------------------------------------------------------
register("grab", action({"lean": -8, "quill": 0, "book": 0,
                         "nu": -39, "ne": 74},
                        GRAB, {"lean": 5, "nu": 27, "ne": 11},
                        sway=1), 7, 68)
register("grab_hold", hold({**GRAB, "nu": 17, "ne": 40,
                            "fu": 24, "fe": 30}, sway=1), 7, 110, True)
register("pummel", action({**GRAB, "x": -5, "nu": -55, "ne": 95},
                          {**GRAB, "x": 9, "lean": 27,
                           "nu": -6, "ne": -18, "mouth": "grit"},
                          GRAB, start=GRAB, end=GRAB), 6, 55)
register("grab_release", transition(STANCE, source=GRAB), 5, 67)
register("throw_forward", action({**GRAB, "lean": -15,
                                  "nu": 28, "ne": 60},
                                 {**GRAB, "x": 19, "lean": 43,
                                  "nu": -18, "ne": -16, "fu": 4,
                                  "fe": -9, "mouth": "open",
                                  "nf": ground("near", 23)},
                                 {"lean": 20}, start=GRAB), 8, 65)
register("throw_back", action({**GRAB, "lean": 24},
                              {**GRAB, "x": -18, "lean": -34,
                               "nu": 150, "ne": -14, "fu": -152,
                               "fe": -6, "head": -12,
                               "ff": ground("far", -25)},
                              {"lean": -11}, start=GRAB), 8, 67)
register("throw_up", action({**GRAB, "y": 15,
                            "nu": 30, "ne": 80},
                           {**GRAB, "y": -15, "lean": -8,
                            "nu": -114, "ne": -5, "fu": -100,
                            "fe": 0, "head": -30,
                            "mouth": "open"},
                           {"y": -4, "nu": -60}, start=GRAB), 8, 65)
register("throw_down", action({**GRAB, "lean": -13,
                               "nu": -85, "ne": 70},
                              {**CROUCH, "quill": 0, "book": 0,
                               "y": 30, "lean": 35, "nu": 65,
                               "ne": -8, "fu": 112,
                               "mouth": "grit", "eye": "angry"},
                              CROUCH, start=GRAB), 8, 65)
register("grabbed", hold({**STANCE, "quill": 0, "book": 0,
                          "lean": -13, "nu": 60, "ne": 36,
                          "fu": 119, "fe": 33, "eye": "surprised",
                          "mouth": "open"}, flutter=2), 6, 120, True)
register("grab_escape", action({"lean": -17, "nu": 41, "ne": 51,
                                "quill": 0, "book": 0},
                               {"lean": 27, "nu": -20, "ne": -30,
                                "fu": 154, "fe": -20, "head": 17,
                                "mouth": "grit"},
                               {"lean": 8}), 7, 59)

# Damage, death, presentation ---------------------------------------------------
register("hit", B.HIT, 6, 80)
register("hit_heavy", action({"x": 5, "lean": 10},
                             {"x": -16, "lean": -30, "head": -24,
                              "nu": 83, "ne": -8, "fu": 140,
                              "eye": "shut", "mouth": "open",
                              "quill": 0, "book": 0},
                             {"x": -9, "lean": -16}), 8, 80)
register("launch", action({"x": -7, "y": 5, "lean": -11},
                          {**FLIGHT, "y": -60, "x": -28,
                           "spin": -43, "head": -43,
                           "nf": air("near", 8, -22),
                           "ff": air("far", -12, -19),
                           "quill": 0, "book": 0,
                           "eye": "shut", "mouth": "open"},
                          {**FLIGHT, "y": -34, "spin": -18,
                           "head": -18, "quill": 0, "book": 0},
                          end=FLIGHT), 8, 62)
register("tumble", B.TUMBLE, 8, 70)
register("knockdown", action({"x": -13, "lean": -25,
                              "quill": 0, "book": 0},
                             {**PRONE, "y": 44, "spin": -69,
                              "head": -69},
                             PRONE, end=PRONE), 8, 75)
register("prone", hold(PRONE), 6, 140, True)
register("prone_damage", action(PRONE,
                                 {**PRONE, "head": -63, "spin": -71,
                                  "eye": "shut", "mouth": "open"},
                                 PRONE, start=PRONE, end=PRONE), 5, 95)
register("getup_attack", action({**PRONE, "y": 32},
                                {**CROUCH, "y": 21, "nu": -8,
                                 "ne": -9, "nw": -4,
                                 "quill": 1, "book": 0},
                                CROUCH, start=PRONE), 8, 62)
register("getup_roll", action({**PRONE, "x": 34},
                              {**PRONE, "spin": -175, "head": -175,
                               "x": 45, "y": 22},
                              {**CROUCH, "x": 55}, start=PRONE), 8, 55)
register("getup", action({**PRONE, "y": 37},
                         {**CROUCH, "y": 26, "nu": 68,
                          "fu": 118, "head": -4,
                          "quill": 0, "book": 0},
                         CROUCH, start=PRONE), 8, 67)
register("dizzy", B.DAZED, 8, 120, True)
register("death", B.DEATH, 10, 105)
# Item-adjacent poses carry no item logic: sockets and inventory semantics
# remain owned by the future game-side fighter integration.
register("item_hold", hold({**STANCE, "nu": 3, "ne": 63,
                             "nw": -88, "quill": 0, "book": 0}), 6, 110, True)
register("item_pickup", action({**CROUCH, "y": 20, "quill": 0,
                                "book": 0, "nu": 63, "ne": -10},
                               {**CROUCH, "y": 33, "lean": 40,
                                "nu": 76, "ne": 0, "quill": 0,
                                "book": 0},
                               {"nu": 17, "ne": 55}), 7, 70)
register("item_throw", action({"nu": 27, "ne": 88,
                               "quill": 0, "book": 0},
                              {"nu": -12, "ne": -18,
                               "nw": -5, "x": 13, "lean": 22,
                               "quill": 0, "book": 0},
                              {"nu": 31, "ne": -5}), 8, 70)
register("item_drop", action({"nu": 35, "ne": 50,
                              "quill": 0, "book": 0},
                             {"nu": 99, "ne": 0,
                              "quill": 0, "book": 0},
                             {"nu": 60}), 6, 70)
register("item_swing", action({"nu": -104, "ne": 94,
                               "quill": 0, "book": 0},
                              {"nu": 0, "ne": -12, "nw": -5,
                               "x": 12, "quill": 0, "book": 0},
                              {"nu": 33, "ne": 0}), 8, 65)
register("teeter", hold({**STANCE, "lean": 25,
                         "nf": ground("near", 21),
                         "ff": ground("far", 2),
                         "nu": 45, "fu": 139,
                         "eye": "surprised", "mouth": "open"},
                        sway=2.5, flutter=3), 8, 90, True)
register("taunt", action({"lean": -12, "nu": -34, "ne": 47,
                          "mouth": "smile"},
                         {"lean": 4, "nu": -80, "ne": 6,
                          "nw": -90, "fu": -108, "fe": -5,
                          "head": -9, "mouth": "smile",
                          "near_tail": 10},
                         {"nu": -65, "mouth": "smile"}), 10, 95)
register("entrance", action({**STANCE, "spin": -39, "head": -39,
                            "x": -14, "quill": 0, "book": 0},
                           {**STANCE, "spin": 0, "head": -8,
                            "nu": -89, "ne": 28, "nw": -90,
                            "quill": 1, "book": 1, "mouth": "smile"},
                           {"nu": -62, "head": -3}), 9, 90)
register("victory_hold", hold({**STANCE, "nu": -98, "ne": -5,
                               "nw": -90, "fu": -91, "fe": 0,
                               "head": -11, "mouth": "smile",
                               "near_tail": 10}, sway=3, flutter=4), 10, 110, True)
register("loss", hold({**CROUCH, "y": 35, "lean": -28,
                       "head": 26, "nu": 97, "fu": 82,
                       "quill": 0, "book": 0,
                       "eye": "shut", "mouth": "wavy"}), 8, 110, True)

ROWS = list(ROW_SPECS.values())
