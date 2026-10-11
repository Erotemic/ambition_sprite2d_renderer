"""What the flyer targets built by ``scripts/build_flyer_rigs.py`` share (the
European swallow, the African swallow, the vulture): each is one SVG posed by
a rig on the ``bird`` anatomy, with the rows of a flying bird and the effects
of ``_bird_fx``. A target module states only what is its own: its size, its
colours and its words.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Sequence, Tuple

from ._bird_fx import RGBA, BirdFx

LOOPS = {"idle", "walk", "fly", "taunt"}


def rig_path(target: str) -> Path:
    return Path(__file__).resolve().parent / "rigged" / target / f"{target}_side.rig.json"


def flyer_fx(target: str, *, art_scale: float, frame_size: Tuple[int, int], feathers: Sequence[Tuple[RGBA, RGBA]],
             beak_tip: Tuple[float, float], flight_pitch: float) -> BirdFx:
    """The bird's effects and sheet. ``beak_tip`` is the tip of its beak in
    the head bone's frame (SVG units)."""
    return BirdFx(target=target, rig_path=rig_path(target), art_scale=art_scale, frame_size=frame_size,
                  feathers=feathers, beak_tip=beak_tip, flight_pitch=flight_pitch)


def lineage(target: str) -> Dict[str, object]:
    return {"family": target, "variant": "svg_rigged", "parents": [], "method": "svg_rig", "revision": "initial"}


def actor_metadata(target: str, *, display_name: str, art_scale: float, mass_class: str, traits: Sequence[str],
                   sockets: Dict[str, Tuple[float, float]], authoring: str, gameplay: str,
                   barks: Sequence[str]) -> dict:
    """The actor contract of a bird that flies at its target and strikes.
    ``sockets`` are points of the drawing in SVG units."""
    return {
        "actor": {"character_id": target, "display_name": display_name},
        "body": {
            "body_plan": "AvianBiped",
            "body_kind": "Floating",
            "mass_class": mass_class,
            "locomotion_hint": "Fly",
            "traits": ["enemy", "bird", "svg_rigged", *traits],
        },
        "capabilities": {
            "traversal": {
                "walk": True,
                "jump": None,
                "climb": None,
                "fly": True,
                "swim": None,
                "crawl": None,
                "use_lifts": True,
                "door_access": ["public"],
            },
            "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
        },
        "brain": {"default_preset": "parrot_lively"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "locomotion.fly": {"animation": "fly", "events": []},
            "action.melee.primary": {
                "animation": "slash",
                "events": [
                    {"t": 0.17, "event": "telegraph_peak", "source": target},
                    {"t": 0.43, "event": "hitbox_active_start", "source": target},
                    {"t": 0.64, "event": "hitbox_active_end", "source": target},
                ],
            },
            "emote.taunt": {"animation": "taunt", "events": []},
            "reaction.hurt": {"animation": "hurt", "events": []},
            "reaction.death": {"animation": "death", "events": []},
        },
        # Points on the drawn frame (before the sheet's auto-crop), perched at rest.
        "sockets": {
            name: {"source": f"{target}.geometry", "point": {"x": round(x * art_scale, 1), "y": round(y * art_scale, 1)}}
            for name, (x, y) in sockets.items()
        },
        "visual": {
            "default_pose": "idle",
            "canonical_source": f"ambition_sprite2d_renderer/data/characters/{target}/{target}.svg",
        },
        "tags": ["enemy", "bird", target, "svg_rigged"],
        "authoring_description": authoring,
        "gameplay_description": gameplay,
        "dialogue_hints": {"barks": list(barks)},
    }


__all__ = ["LOOPS", "actor_metadata", "flyer_fx", "lineage", "rig_path"]
