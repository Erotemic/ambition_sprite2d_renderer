"""Bad Apple: a bruised apple that rolls into fights and bites.

The enemy shares the body, leaf, and stem geometry of GNU-ton's apple prop.
The face, rolling effects, and animation poses are programmatic SVG parts.
No AI or combat logic is registered by this art target.
"""

from __future__ import annotations

from pathlib import Path

from ._apple_enemy_family import BAD_ROWS, frame_png, frame_svg, render_family

TARGET_NAME = "bad_apple"
ROWS = BAD_ROWS
FRAME_SIZE = (256, 256)
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]

ACTOR_METADATA = {
    "actor": {"character_id": "bad_apple", "display_name": "Bad Apple"},
    "body": {
        "body_plan": "BeastBiped",
        "body_kind": "LowProfile",
        "mass_class": "Light",
        "locomotion_hint": "Roll",
        "traits": ["enemy", "fruit", "small", "biter"],
    },
    "capabilities": {"traversal": {"walk": True, "fly": None}},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "action.melee.primary": {"animation": "chomp", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "tags": ["enemy", "fruit", "gnu_ton_handle"],
    "authoring_description": {
        "visual_inspirations": [
            "GNU-ton's apple projectile body, leaf, and stem.",
            "A rotting red predator with slitted jaundiced eyes, a large black maw, and uneven fangs.",
        ],
        "rigging_notes": [
            "The generator animates expressions and deformation, not the full-body rolling rotation.",
            "The apple contour is traced from the projectile mask. Keep its silhouette shared.",
            "The wilted leaf and facial scars are attached geometry, not detached effects.",
            "No ground or drop shadow is baked into any animation frame.",
            "An engine pose must rotate the whole character smoothly during rolling locomotion.",
        ],
    },
    "gameplay_description": (
        "A proposed rolling enemy for the GNU-ton gravity region. Its sprite walk clip "
        "animates expressions only; physics-driven rolling, biting behavior, and collision "
        "are not implemented here."
    ),
}


def render_svg(animation: str = "idle", frame: int = 0, count: int | None = None) -> str:
    if count is None:
        count = dict((name, n) for name, n, _ in ROWS)[animation]
    return frame_svg(TARGET_NAME, animation, frame, count)


def render_frame(animation: str, frame_idx: int, frame_count: int):
    return frame_png(TARGET_NAME, animation, frame_idx, frame_count)


def render(out_dir: str | Path, **opts):
    del opts
    return render_family(out_dir, kind=TARGET_NAME, rows=ROWS, actor_metadata=ACTOR_METADATA)


__all__ = ["ACTOR_METADATA", "FRAME_SIZE", "ROWS", "SHEET_FILES", "TARGET_NAME", "render", "render_frame", "render_svg"]
