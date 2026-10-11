"""What the ratite targets share (the ostrich, the emu, the cassowary, the
kiwi): each is one SVG posed by a rig on the ``ratite`` anatomy
(``scripts/build_ratite_rigs.py``), with the rows of a ground bird and the
effects of ``_bird_fx``. A target module states only what is its own: its
size, its colours and its words.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Sequence, Tuple

from ._bird_fx import RGBA, BirdFx

LOOPS = {"idle", "walk", "run", "jump", "fall", "taunt"}


def rig_path(target: str) -> Path:
    return Path(__file__).resolve().parent / "rigged" / target / f"{target}_side.rig.json"


def ratite_fx(target: str, *, art_scale: float, frame_size: Tuple[int, int], feathers: Sequence[Tuple[RGBA, RGBA]],
              beak_length: float) -> BirdFx:
    """The bird's effects and sheet. ``beak_length`` is the length of its
    head bone (the back of the head to the beak tip), in SVG units."""
    return BirdFx(target=target, rig_path=rig_path(target), art_scale=art_scale, frame_size=frame_size,
                  feathers=feathers, beak_tip=(beak_length, 0.0))


def lineage(target: str) -> Dict[str, object]:
    return {"family": target, "variant": "svg_rigged", "parents": [], "method": "svg_rig", "revision": "initial"}


def actor_metadata(target: str, *, display_name: str, art_scale: float, mass_class: str, traits: Sequence[str],
                   sockets: Dict[str, Tuple[float, float]], authoring: str, gameplay: str,
                   barks: Sequence[str]) -> dict:
    """The actor contract of a ground bird that runs at its target and
    strikes. ``sockets`` are points of the drawing in SVG units."""
    return {
        "actor": {"character_id": target, "display_name": display_name},
        "body": {
            "body_plan": "AvianBiped",
            "body_kind": "Standard",
            "mass_class": mass_class,
            "locomotion_hint": "Run",
            "traits": ["enemy", "bird", "ground_bird", "ratite", "svg_rigged", *traits],
        },
        "capabilities": {
            "traversal": {
                "walk": True,
                "jump": True,
                "climb": None,
                "fly": None,
                "swim": None,
                "crawl": None,
                "use_lifts": True,
                "door_access": ["public"],
            },
            "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
        },
        "brain": {"default_preset": "melee_brute_striker"},
        "actions": {"default_preset": "striker_swipe"},
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "locomotion.run": {"animation": "run", "events": []},
            "locomotion.jump": {"animation": "jump", "events": []},
            "locomotion.fall": {"animation": "fall", "events": []},
            "action.melee.primary": {
                "animation": "slash",
                "events": [
                    {"t": 0.17, "event": "telegraph_peak", "source": target},
                    {"t": 0.42, "event": "hitbox_active_start", "source": target},
                    {"t": 0.67, "event": "hitbox_active_end", "source": target},
                ],
            },
            "emote.taunt": {"animation": "taunt", "events": []},
            "reaction.hurt": {"animation": "hurt", "events": []},
            "reaction.death": {"animation": "death", "events": []},
        },
        # Points on the drawn frame (before the sheet's auto-crop), standing at rest.
        "sockets": {
            name: {"source": f"{target}.geometry", "point": {"x": round(x * art_scale, 1), "y": round(y * art_scale, 1)}}
            for name, (x, y) in sockets.items()
        },
        "visual": {
            "default_pose": "idle",
            "canonical_source": f"ambition_sprite2d_renderer/data/characters/{target}/{target}.svg",
        },
        "tags": ["enemy", "bird", "ratite", target, "svg_rigged"],
        "authoring_description": authoring,
        "gameplay_description": gameplay,
        "dialogue_hints": {"barks": list(barks)},
    }


__all__ = ["LOOPS", "actor_metadata", "lineage", "ratite_fx", "rig_path"]
