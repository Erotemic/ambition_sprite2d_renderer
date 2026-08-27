"""SVG-rigged Medic: a field paramedic who fights the way she works.

Hand-drawn, rigged by program, and bound to the Pugnacious Polygon's brawler
skeleton sped up and re-aimed. Her whole vocabulary is the PALM -- heel strikes,
lifts, compressions -- because a medic's trained motion is push, lift, carry,
and never close the fist. Anything heavy she does with both hands, the way a
person actually moves another person's weight.

⭐ **she is the only fighter here who can put something back.** Her neutral
special SPENDS a slice of her own margin to buy tempo; her down special kneels
and repays it. A fighter who can only spend is a gimmick; one who can spend and
repay has a decision to make every time she does either.

Her swings read CLINICAL: a cold white-cyan that belongs to monitors and sterile
light. Tilts throw a thin lance, like a trace crossing a screen; smashes
discharge, a hard white compression edge with the cyan boiling off behind it.
Nothing of hers is warm, which is what separates her from the brawler she shares
timings with.

⛔ **her far shoulder disappears behind her own shirt past `far_arm_u = 95`.**
Measured on the render: 54px of shoulder at the drawn rest angle, 28 at 90, 13
from 100 up. Her torso is black and her arms are not, so past that bound the
forearm emerges past the shirt's edge with nothing above it and publishes as a
fist growing out of her hip. Her far arm therefore never chambers BACKWARD; it
chambers forward and low. `scripts/check_character_reads.py` is what keeps that
honest, and it fails on the pose that taught it.

Her sleeves ride the UPPER ARMS, not the torso. That is the opposite of the
Officer's choice and it is his reasoning applied to a different garment: his
sleeve is loose enough that the arm rotates out from under it, hers is a fitted
cap drawn onto the shoulder, and leaving it behind opens a notch where the joint
should be.
"""
from __future__ import annotations

from pathlib import Path

from ._authored_swing_fighter import AuthoredSwingFighter

TARGET_NAME = "medic"
_FIGHTER = AuthoredSwingFighter(TARGET_NAME)

#: A compact vocabulary to show first when reviewing this fighter. The rig
#: publishes the full fighter vocabulary (136 clips).
POSE_HIGHLIGHTS = (
    "idle", "walk", "run", "crouch", "jump", "fall", "land_light", "turnaround",
    "roll", "spot_dodge", "air_dodge", "shield_raise",
    "jab", "punch", "attack_side", "attack_up", "attack_down", "dash_attack",
    "smash_forward", "smash_up", "smash_down",
    "air_neutral", "air_forward", "air_back", "air_up", "air_down",
    "grab", "grab_hold", "pummel",
    "throw_forward", "throw_back", "throw_up", "throw_down",
    "special", "shoot", "charge", "fly", "final_smash",
    "grabbed", "launch", "knockdown", "getup", "tech",
    "ledge_grab", "ledge_getup", "ledge_attack",
    "item_hold", "item_throw", "taunt", "victory_hold", "loss",
)

ACTOR_METADATA = {
    "actor": {
        "character_id": TARGET_NAME,
        "display_name": "The Medic",
    },
    "authoring_description": {
        "concept": (
            "A field paramedic off duty: black fitted top, black leggings, "
            "trainers, a high ponytail and small gold hoops. She is dressed for "
            "a shift that has not ended and she moves like someone who has "
            "carried people."
        ),
        "visual_language": [
            "near-black clothing against warm skin and copper hair -- two values, no third",
            "flat cel shading with a single dark outline, no rendered volume",
            "the ponytail is the only thing on her that swings",
            "open hands in every pose; she is never drawn with a fist",
            "no drop shadow and no held props",
        ],
        "rigging_notes": [
            "The SVG owns artwork and static rig geometry; editor-neutral motion JSON owns poses and clips.",
            "Near/far are decided by PAINT ORDER, not by the layer names the art arrived with: she faces east, so what paints behind the shirt is her left and reads far.",
            "Her cap sleeves ride the upper arms so a raised arm keeps its shoulder.",
            "far_arm_u stays at or below 95 degrees -- past that the shirt swallows her shoulder and the forearm reads as detached.",
            "She has no torso_side/torso_back art, so her library carries no shoulder-socket offsets; restoring the torso turn is an art step.",
        ],
    },
    "gameplay_description": {
        "role": "fast two-handed brawler; tempo over power",
        "combat_identity": [
            "light-medium weight, high mobility, low raw KO power, long combo strings",
            "every heavy commitment is a TWO-HANDED one, which is what makes her smashes slow and her tilts fast",
            "her specials trade her own margin for tempo rather than adding reach, and one of them buys it back",
            "the heal is a commitment, not a freebie: she goes to a knee and for its whole length she is not looking at you",
            "complete grounded, aerial, special, defensive, capture, pummel and throw vocabulary",
        ],
        "authoring_notes": [
            "Special mapping: neutral ADRENALINE (`special`), side TOURNIQUET (`shoot`), down FIELD DRESSING (`charge`), up RESCUE LIFT (`fly`), Final Smash CODE (`final_smash`).",
            "ADRENALINE and FIELD DRESSING are a PAIR: one spends her margin for tempo, the other puts it back on one knee with both hands busy. Neither publishes a hit volume — the specs carry no `hitbox.active` and name their live frames on the effect's own block.",
            "The gameplay repertoire lives in ambition_content; this target publishes art, rig and authored hit volumes only.",
        ],
    },
    "dialogue_hints": {
        "suggested_barks": [
            "Stay down. I'm not asking.",
            "Look at me. Can you hear me?",
            "You're going to be fine. Probably.",
            "I've got you.",
        ],
        "fallback_dialogue": [
            "I don't fight people. I move them.",
            "Whatever you did to your shoulder, that wasn't me.",
            "Sit. Breathe. We'll get to it.",
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": ["humanoid", "brawler", "support", "playable_candidate", "svg_rigged"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": True, "swim": True,
                      "crawl": True, "use_lifts": True},
        "interactions": {"talk": True, "carry": True},
    },
    "visual": {
        "default_pose": "idle",
        "canonical_source": "data/characters/medic/medic.svg",
        "pose_reference": list(POSE_HIGHLIGHTS),
    },
    "actions": {"default_preset": TARGET_NAME, "archetype": "brawler_humanoid"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "jab", "events": []},
        "action.melee.secondary": {"animation": "punch", "events": []},
        "action.melee.forward": {"animation": "attack_side", "events": []},
        "action.melee.up": {"animation": "attack_up", "events": []},
        "action.melee.down": {"animation": "attack_down", "events": []},
        "action.melee.dash": {"animation": "dash_attack", "events": []},
        "action.smash.forward": {"animation": "smash_forward", "events": []},
        "action.smash.up": {"animation": "smash_up", "events": []},
        "action.smash.down": {"animation": "smash_down", "events": []},
        "action.aerial.neutral": {"animation": "air_neutral", "events": []},
        "action.aerial.forward": {"animation": "air_forward", "events": []},
        "action.aerial.back": {"animation": "air_back", "events": []},
        "action.aerial.up": {"animation": "air_up", "events": []},
        "action.aerial.down": {"animation": "air_down", "events": []},
        "action.special.neutral": {"animation": "special", "events": []},
        "action.special.side": {"animation": "shoot", "events": []},
        "action.special.down": {"animation": "charge", "events": []},
        "action.special.up": {"animation": "fly", "events": []},
        "action.special.final": {"animation": "final_smash", "events": []},
        "action.capture.grab": {"animation": "grab", "events": []},
        "action.capture.hold": {"animation": "grab_hold", "events": []},
        "action.capture.pummel": {"animation": "pummel", "events": []},
        "action.capture.throw_forward": {"animation": "throw_forward", "events": []},
        "action.capture.throw_back": {"animation": "throw_back", "events": []},
        "action.capture.throw_up": {"animation": "throw_up", "events": []},
        "action.capture.throw_down": {"animation": "throw_down", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
        "emote.victory": {"animation": "victory_hold", "events": []},
    },
    "tags": ["humanoid", "brawler", "support", "smash", "svg_rigged"],
}


def render(out_dir: str | Path, **opts):
    del opts
    return _FIGHTER.render(out_dir, ACTOR_METADATA)

#: Extra stills a UI can address by name: `(clip, frame)`.
PORTRAIT_STILLS = {
    # The look she gives a casualty, and the one she gives an opponent.
    "working": ("charge", 4),
    "spent": ("special", 8),
}


def render_portraits(out_dir: str | Path, **opts):
    """Her portrait, rendered from the rig -- see `AuthoredSwingFighter`.

    Without this hook the registry derives a default by cropping the CANONICAL
    raster, which is about 190px tall, and blows it up to 256x320: soft
    everywhere and unreadable around the eyes.
    """
    return _FIGHTER.render_portraits(
        out_dir, clips=PORTRAIT_STILLS, quality_scale=opts.get("quality_scale")
    )
