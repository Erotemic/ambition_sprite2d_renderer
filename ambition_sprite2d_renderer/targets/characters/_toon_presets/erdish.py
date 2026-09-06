"""Legacy toon archetype preset for Erdish.

The runtime review config now uses the bespoke ``erdish_scholar`` generator.
Keep this fallback prop-free so ad-hoc toon jobs cannot reintroduce the old
tablet or satchel into base character poses.

One archetype per file so adding / editing a single character
doesn't require touching the shared preset module. The
``_toon_presets/__init__.py`` collects every ``PRESET`` exported
here into a single dict for the rig to consume.

See GOALS.md goal #1.
"""

from __future__ import annotations


PRESET = {
    "name": "Erdish",
    "role": "npc",
    "palette_name": "erdish",
    "body_plan": "tall",
    "outfit": "long_coat",
    "hair_style": "combed_back_balding",
    "prop": "none",
    "accessory": "none",
    "head_w": 23.0,
    "head_h": 28.0,
    "chin_h": 6.2,
    "neck_h": 4.2,
    "shoulder_w": 21.0,
    "torso_w": 17.0,
    "torso_h": 28.5,
    "hip_w": 15.5,
    "arm_upper": 14.5,
    "arm_lower": 14.2,
    "arm_radius": 2.3,
    "leg_upper": 19.0,
    "leg_lower": 17.5,
    "leg_radius": 2.6,
    "hand_r": 2.8,
    "foot_w": 10.5,
    "foot_h": 4.2,
    "coat_len": 20.0,
    "cape_len": 0.0,
    "hair_volume": 7.0,
    "nose_len": 3.4,
    "satchel_size": 0.0,
}
