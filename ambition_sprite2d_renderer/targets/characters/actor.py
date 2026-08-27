"""SVG-rigged Actor: a performer who commits to the role completely.

Hand-drawn, rigged by program, and bound to the Pointed Polygon's BODY without
his sword: long lines, weight on the back foot, every gesture held a beat too
long because a gesture that is not held did not read from the back row. She is
that archetype's shape and none of its equipment.

⭐ **what she fights with is THE DUEL SCENE.** Her forward smash is a fencer's
lunge with a blade of stage light that exists for exactly the frames the role
calls for it. There is no sword part on this rig and there is not going to be
one: the reach is authored as the swing's own axis, extended past her hand, and
the hit volume is built from that same number -- so the blade a player sees IS
the blade that hits them, and nothing hits in a shape nobody was shown.

Her light is STAGE light: warm amber and gel-pink, thrown from above and in
front. Her sweeps leave a ribbon because the light lags the gesture, which is
the whole reason a stage gesture is held.

⭐ **and the other two specials are stage machinery, not technique.** Down is a
TRAP: she hits her mark, the boards give, and she comes up out of a second door
somewhere else -- `blink_out` going and `blink_in` arriving, which is what that
pair of rows is for. Up is a FLYLINE that catches her at the waist and takes her
straight up with her feet trailing. Neither is something she does; both are
things done to her, and she goes with them because that is the job.

⛔ **her far shoulder lives behind her cardigan panel: 12px of it at rest,
against the Medic's 54.** That is the costume, not a defect, and it decides how
she is posed -- the NEAR arm carries every line and the far one counterweights.
`scripts/check_character_reads.py` measures each character against her OWN
drawing for exactly this reason; one threshold would either pass every broken
frame of the Medic's or condemn the Actor as she was drawn.
"""
from __future__ import annotations

from pathlib import Path

from ._authored_swing_fighter import AuthoredSwingFighter

TARGET_NAME = "actor"
_FIGHTER = AuthoredSwingFighter(TARGET_NAME)

POSE_HIGHLIGHTS = (
    "idle", "walk", "run", "crouch", "jump", "fall", "land_light", "turnaround",
    "roll", "spot_dodge", "air_dodge", "shield_raise",
    "jab", "attack_side", "attack_up", "attack_down", "dash_attack",
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
        "display_name": "The Actor",
    },
    "authoring_description": {
        "concept": (
            "A working performer between calls: an oversized grey cardigan over "
            "a dark tank, flared grey trousers, worn boots, and an auburn updo "
            "coming down at the edges. She is dressed for a rehearsal room and "
            "carries herself for a house of nine hundred."
        ),
        "visual_language": [
            "three greys and one auburn; the only saturated thing on her is her hair",
            "long unbroken lines -- the cardigan reads as one silhouette from shoulder to knee",
            "flat cel shading with a single dark outline, no rendered volume",
            "the far side of her is drawn one step back in tone, baked into the fills",
            "no held props: whatever she is holding, she is only holding for this scene",
        ],
        "rigging_notes": [
            "The SVG owns artwork and static rig geometry; editor-neutral motion JSON owns poses and clips.",
            "Near/far are decided by PAINT ORDER: she faces east, so what paints behind the cardigan is her left and reads far. The ids the art arrived with had every one of them backwards.",
            "The far-side depth tint is baked into opaque fills, never group opacity -- each part rasterizes to its own transparent layer, so alpha would publish a see-through arm.",
            "Her cardigan sleeves ride the upper arms; the two front panels ride the torso and carry their own bind pivots for later flare.",
            "Her far shoulder sits behind a cardigan panel by design; she is posed so the NEAR arm carries every line.",
            "She has no torso_side/torso_back art, so her library carries no shoulder-socket offsets; restoring the torso turn is an art step.",
        ],
    },
    "gameplay_description": {
        "role": "committed mid-range duellist with a conjured reach",
        "combat_identity": [
            "medium weight, deliberate startup, long disjointed reach on the frames she commits to",
            "the reach is real but temporary -- outside the duel scene her hands are empty and short",
            "high reward, high recovery: everything she throws is held, and a held gesture can be punished",
            "complete grounded, aerial, special, defensive, capture, pummel and throw vocabulary",
        ],
        "authoring_notes": [
            "Special mapping: neutral MONOLOGUE (`special`), side THE LINE (`shoot`), down THE TRAP (`blink_out` going, `blink_in` arriving), up CURTAIN CALL (`fly`), Final Smash STANDING OVATION (`final_smash`).",
            "The trap and the flyline are things the STAGE does to her. Both publish NO hit volume -- a hole in the boards and a wire hurt nobody -- so their specs carry no `hitbox.active` and name their live frames on the effect's own block.",
            "The conjured blade is an authored EFFECT with an authored volume, not a rig part. Do not add a sword to this rig.",
            "The gameplay repertoire lives in ambition_content; this target publishes art, rig and authored hit volumes only.",
        ],
    },
    "dialogue_hints": {
        "suggested_barks": [
            "From the top.",
            "That was your cue.",
            "Louder. The back row paid too.",
            "I can do this all night. I have.",
        ],
        "fallback_dialogue": [
            "I'm not playing anyone right now. It's disconcerting, isn't it.",
            "Everyone's in costume. Most of them just don't know it.",
            "Give me a moment. I have to decide who I am.",
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["humanoid", "duellist", "performer", "playable_candidate", "svg_rigged"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": True, "swim": True,
                      "crawl": True, "use_lifts": True},
        "interactions": {"talk": True, "carry": True},
    },
    "visual": {
        "default_pose": "idle",
        "canonical_source": "data/characters/actor/actor.svg",
        "pose_reference": list(POSE_HIGHLIGHTS),
    },
    "actions": {"default_preset": TARGET_NAME, "archetype": "sword_humanoid"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "jab", "events": []},
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
        "action.special.down": {"animation": "blink_out", "events": []},
        "action.special.down_arrive": {"animation": "blink_in", "events": []},
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
    "tags": ["humanoid", "duellist", "performer", "smash", "svg_rigged"],
}


def render(out_dir: str | Path, **opts):
    del opts
    return _FIGHTER.render(out_dir, ACTOR_METADATA)
