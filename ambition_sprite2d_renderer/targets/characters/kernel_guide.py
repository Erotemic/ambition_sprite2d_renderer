"""The Kernel Guide: the one who shows a new arrival about the Kernel.

A calm guide in a hooded robe of deep teal with a trim of amber, round glasses
that glow, and a slate with a screen of light that the tutorial is read from.
The guide was a preset of the toon rig with four short rows. It is a character
on the rig of the pirate crew now (`_pirate_common`, `_pirate_rig`): the same
skeleton, its own look, its own poses, and eight rows (idle, walk, talk,
interact, slash, shoot, hurt, death).

The guide has no weapon. The hand that a pirate has a sword in has the slate,
and a guide that was hit too many times fights with it (Jon, 2026-10-10): it
hits with the slate (`slash`) and it sends a bolt of light from the screen
(`shoot`). The names of the rows are the names the game looks for.
"""

from __future__ import annotations

import math
from pathlib import Path

from ...authoring.sheet_build import ease_in_out, lerp, oscillate
from . import _pirate_common as crew

TARGET_NAME = "kernel_guide"
SHEET_FILES = [f"{TARGET_NAME}_spritesheet.png", f"{TARGET_NAME}_spritesheet.yaml"]

#: (row, frames, ms a frame).
ROWS = [
    ("idle", 8, 120),
    ("walk", 8, 100),
    ("talk", 8, 110),
    ("interact", 6, 100),
    ("slash", 6, 85),
    ("shoot", 6, 85),
    ("hurt", 4, 90),
    ("death", 8, 110),
]

PALETTE = crew.Palette(
    outline=(22, 24, 34, 255),
    skin=(198, 150, 110, 255),
    skin_shadow=(150, 104, 72, 255),
    # The hood is the robe.
    hat=(34, 96, 110, 255),
    coat=(34, 96, 110, 255),
    coat2=(236, 180, 84, 255),
    sash=(58, 40, 70, 255),
    shirt=(232, 226, 206, 255),
    pants=(44, 48, 66, 255),
    boots=(70, 52, 40, 255),
    # The light of the glasses, of the slate and of the stone on the belt.
    metal=(120, 230, 240, 255),
    gold=(236, 180, 84, 255),
    beard=None,
    accent=(120, 230, 240, 255),
)

LOOK = crew.Look(
    build=0.98, headwear="hood", band="coat2", hair=(60, 44, 40, 255),
    coat="robe", sword=False, prop="tablet", glasses=True, gentle=True,
)


def _home() -> dict:
    """The guide at rest: upright, the feet near, the slate held up to read,
    the head down to it a little, the other arm down."""
    pose = crew.home_pose()
    pose.update({
        "body_tilt": 0.0,
        "left_thigh": 7.0,
        "left_shin": 8.0,
        "right_thigh": -7.0,
        "right_shin": -4.0,
        "sword_upper": -22.0,
        "sword_fore": -82.0,
        "weapon": -64.0,
        "off_upper": 12.0,
        "off_fore": -4.0,
        "head_tilt": 7.0,
    })
    return pose


def pose(anim: str, frame_idx: int, nframes: int) -> dict:
    """The pose of one frame of the guide. See `_pirate_common.animation_pose`
    for the channels: a limb angle is a world angle, 0 is down, negative is to
    the front."""
    s = oscillate(frame_idx, nframes)
    c = math.cos((frame_idx / max(1, nframes)) * math.tau)
    phase = (frame_idx / max(1, nframes)) * math.tau
    t = frame_idx / max(1, nframes - 1)
    p = _home()
    if anim == "idle":
        # Reads the slate, breathes, and looks up from it once in the loop.
        up = max(0.0, math.sin(phase - 2.4)) ** 2
        p["shoulder_bounce"] = -s * 1.6
        p["sword_fore"] = -82.0 + s * 2.0
        p["weapon"] = -64.0 + c * 2.0
        p["off_fore"] = -4.0 + c * 3.0
        p["head_tilt"] = 7.0 - 9.0 * up + c * 1.0
        p["coat_sway"] = c * 2.0
        p["glow"] = 0.15 + 0.15 * max(0.0, s)
        p["blink"] = frame_idx == max(0, nframes - 2)
    elif anim == "walk":
        for side, at in (("left", phase), ("right", phase + math.pi)):
            thigh = 19.0 * math.sin(at)
            p[f"{side}_thigh"] = thigh
            p[f"{side}_shin"] = thigh + 38.0 * max(0.0, -math.cos(at))
        p["body_tilt"] = 3.0
        p["sword_upper"] = -20.0 + 4.0 * math.sin(phase)
        p["sword_fore"] = -78.0 + 4.0 * math.sin(phase)
        p["weapon"] = -60.0 + 3.0 * math.sin(2.0 * phase)
        p["off_upper"] = 8.0 - 18.0 * math.sin(phase)
        p["off_fore"] = p["off_upper"] - 16.0
        p["shoulder_bounce"] = 1.2 * math.cos(2.0 * phase)
        p["head_tilt"] = 1.0
        p["coat_sway"] = -9.0 * math.sin(phase)
    elif anim == "talk":
        # Looks at the one it talks to, and the free hand says the words too.
        p["sword_upper"] = -16.0
        p["sword_fore"] = -66.0 + c * 3.0
        p["weapon"] = -52.0 + c * 3.0
        # The hand is up beside the shoulder, not across the chest.
        p["off_upper"] = 26.0 + s * 6.0
        p["off_fore"] = -150.0 + c * 18.0
        p["head_tilt"] = -4.0 + c * 3.0
        p["body_tilt"] = 1.0 + s * 1.0
        p["shoulder_bounce"] = -s * 1.2
        p["mouth_open"] = 0.15 + 0.6 * max(0.0, math.sin(2.0 * phase + 0.6))
        p["coat_sway"] = s * 3.0
        p["glow"] = 0.2
    elif anim == "interact":
        # Holds the slate up and puts a finger on it: the screen goes bright.
        tap = max(0.0, math.sin(2.0 * phase)) ** 2
        p["sword_upper"] = -40.0 + c * 2.0
        p["sword_fore"] = -112.0 + s * 2.0
        p["weapon"] = -80.0
        p["off_upper"] = -52.0 - 6.0 * tap
        p["off_fore"] = -92.0 - 14.0 * tap + c * 2.0
        p["head_tilt"] = 9.0 - c * 1.5
        p["body_tilt"] = 2.0
        p["glow"] = 0.2 + 0.8 * tap
    elif anim == "slash":
        # Lifts the slate over the head and brings it down flat on the one in
        # front. The arcs are those of the crew's cut: they are in the frame.
        for channel, table in crew._SLASH.items():
            p[channel] = crew._sampled(table, t)
        p["mouth_open"] = crew._sampled((0.0, 0.2, 0.5, 0.6, 0.3, 0.1), t)
        p["glow"] = crew._sampled((0.2, 0.5, 1.0, 1.0, 0.5, 0.2), t)
    elif anim == "shoot":
        # Holds the slate out with the two hands, the screen to the front. The
        # screen goes bright, the bolt goes, and the guide goes back a little.
        p["sword_upper"] = crew._sampled((-40.0, -66.0, -76.0, -70.0, -60.0, -40.0), t)
        p["sword_fore"] = crew._sampled((-88.0, -92.0, -90.0, -106.0, -98.0, -88.0), t)
        p["weapon"] = crew._sampled((-70.0, -84.0, -88.0, -106.0, -96.0, -76.0), t)
        p["off_upper"] = crew._sampled((-10.0, -40.0, -52.0, -46.0, -30.0, -6.0), t)
        p["off_fore"] = crew._sampled((-40.0, -84.0, -92.0, -100.0, -70.0, -30.0), t)
        p["body_tilt"] = crew._sampled((2.0, 5.0, 4.0, -6.0, -3.0, 0.0), t)
        p["root_x"] = crew._sampled((0.0, 1.0, 1.0, -4.0, -2.0, 0.0), t)
        p["head_tilt"] = crew._sampled((4.0, 0.0, -2.0, -8.0, -3.0, 3.0), t)
        p["coat_sway"] = crew._sampled((0.0, -3.0, -4.0, 8.0, 5.0, 1.0), t)
        p["glow"] = crew._sampled((0.3, 0.7, 1.0, 0.8, 0.4, 0.2), t)
        p["mouth_open"] = crew._sampled((0.0, 0.1, 0.4, 0.5, 0.2, 0.0), t)
    elif anim == "hurt":
        # Thrown back, the slate held to the chest.
        hit = crew._sampled((0.6, 1.0, 0.65, 0.2), t)
        shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
        p["root_x"] = -5.0 * hit + shake * 3.0
        p["body_tilt"] = -16.0 * hit
        p["left_thigh"] = 7.0 + 12.0 * hit
        p["left_shin"] = 8.0 + 18.0 * hit
        p["right_thigh"] = -7.0 + 8.0 * hit
        p["right_shin"] = -4.0 + 12.0 * hit
        p["sword_upper"] = -22.0 + 6.0 * hit
        p["sword_fore"] = -82.0 - 50.0 * hit
        p["weapon"] = -64.0 - 40.0 * hit
        p["off_upper"] = 12.0 + 44.0 * hit
        p["off_fore"] = -4.0 + 40.0 * hit
        p["head_tilt"] = 7.0 - 18.0 * hit
        p["hat_tilt"] = -6.0 * hit
        p["coat_sway"] = -8.0 * hit
        p["mouth_open"] = 0.7 * hit
        p["blink"] = hit > 0.5
    elif anim == "death":
        # Goes down on the back, and the slate goes out of the hand.
        tt = ease_in_out(t)
        up = math.sin(tt * math.pi)
        p["death_t"] = tt
        p["root_x"] = tt * 16.0
        p["bob"] = -tt * 4.0
        p["body_tilt"] = lerp(0.0, -86.0, tt)
        p["left_thigh"] = lerp(7.0, -82.0, tt)
        p["left_shin"] = lerp(8.0, -80.0, tt)
        p["right_thigh"] = lerp(-7.0, -92.0, tt)
        p["right_shin"] = lerp(-4.0, -86.0, tt)
        p["sword_upper"] = lerp(-22.0, -110.0, tt) - 50.0 * up
        p["sword_fore"] = lerp(-82.0, -96.0, tt) - 40.0 * up
        p["weapon"] = lerp(-64.0, 4.0, tt) - 70.0 * up
        p["off_upper"] = lerp(12.0, 100.0, tt)
        p["off_fore"] = lerp(-4.0, 96.0, tt)
        p["head_tilt"] = lerp(7.0, 4.0, tt)
        p["hat_tilt"] = -8.0 * tt
        p["coat_sway"] = 6.0 * tt
        p["mouth_open"] = 0.5 * tt
        p["glow"] = 0.2 * (1.0 - tt)
        p["x_eyes"] = tt > 0.55
        return p
    return crew.planted(p)


# The guide is a kind of the crew rig.
crew.PALETTES[TARGET_NAME] = PALETTE
crew.LOOKS[TARGET_NAME] = LOOK
crew.ROWS[TARGET_NAME] = ROWS
crew.POSES[TARGET_NAME] = pose

_SOCKET = "explicit.profile.humanoid"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_kernel_guide", "display_name": "Kernel Guide"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "guide"],
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
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "kernel_guide_slate"},
    "visual": {"default_pose": "idle"},
    "tags": ["story", "humanoid", "guide"],
    "sockets": {
        "head": {"source": _SOCKET, "point": {"x": 64.0, "y": 24.0}},
        "chest": {"source": _SOCKET, "point": {"x": 64.0, "y": 54.0}},
        "hand_l": {"source": _SOCKET, "point": {"x": 48.0, "y": 64.0}},
        "hand_r": {"source": _SOCKET, "point": {"x": 80.0, "y": 64.0}},
        "speech_bubble": {"source": _SOCKET, "point": {"x": 64.0, "y": 8.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
    },
}


def render(out_dir: str | Path, **opts):
    out_dir = Path(out_dir)
    frame_size = opts.get("frame_size")
    outputs = crew.render_target(TARGET_NAME, out_dir, frame_size=frame_size or (128, 128))
    return [outputs["spritesheet"], outputs["yaml"]]


def render_portraits(out_dir: str | Path, **opts):
    """Painted at portrait resolution: see `_pirate_common`."""
    return crew.render_pirate_portraits(
        TARGET_NAME, out_dir, quality_scale=opts.get("quality_scale"), kind=TARGET_NAME
    )
