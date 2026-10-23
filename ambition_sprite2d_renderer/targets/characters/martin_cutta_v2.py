"""Martin Cutta v2: the coefficient clerk, Martin Kutta in a grey lounge suit.

Upright, dark hair and a moustache, a dove-grey lounge suit with a high
collar, pince-nez on a cord and the green ledger of coefficients; 173 cm. He
swats with the ledger. The art and the rows: ``_runge_kutta_v2.py``. His first
design is ``martin_cutta``, which still renders.
"""

from __future__ import annotations

from pathlib import Path

from . import _runge_kutta_v2 as duo

TARGET_NAME = "martin_cutta_v2"

ACTOR_METADATA = duo.metadata(
    TARGET_NAME,
    character_id="npc_martin_cutta",
    display_name="Martin Cutta",
    traits=[],
    # Frame pixels of the 320x352 side-view frame, the drawing at rest.
    sockets={"head": (165.5, 190.5), "chest": (163.0, 240.5), "hand_l": (159.5, 276.0), "hand_r": (163.0, 278.0),
             "speech_bubble": (165.0, 168.0)},
)
ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Martin Cutta is the lean, exacting half of the Runge-Kutta duo, parodying mathematician "
            "Martin Kutta: upright in a dove-grey lounge suit, pince-nez, Kutta's moustache, the ledger "
            "of coefficients under his arm. He resents Runga receiving first billing and quietly knows "
            "that the famous method does not work without his coefficients."
        ),
        "gameplay_description": (
            "Use as the calculating partner to Carl Runga: a technical rival, co-boss, or "
            "precision-oriented playable character. He should correct Runga's rounding, expose error "
            "terms, and turn bravado into a stable method."
        ),
        "dialogue_hints": {"barks": ["The method does not work without me.", "He contributes the first and the volume.",
                                     "He may show his error term."]},
    }
)


def render(out_dir: str | Path, **opts):
    del opts
    return duo.render(TARGET_NAME, ACTOR_METADATA, Path(out_dir))


def render_portraits(out_dir: str | Path, **opts):
    del opts
    return duo.render_portraits(TARGET_NAME, (160.0, 196.0), (32.0, 44.0), (62.0, 210.0), Path(out_dir))


__all__ = ["ACTOR_METADATA", "render", "render_portraits"]
