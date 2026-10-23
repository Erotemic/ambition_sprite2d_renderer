"""Carl Runga v2: the Goettingen professor, Carl Runge in a frock coat.

Bald, a full grizzled beard, a black frock coat over a wine waistcoat, a
watch chain; 183 cm, broad and heavy. He shoves with the heel of his hand.
The art and the rows: ``_runge_kutta_v2.py``. His first design is
``carl_runga``, which still renders.
"""

from __future__ import annotations

from pathlib import Path

from . import _runge_kutta_v2 as duo

TARGET_NAME = "carl_runga_v2"

ACTOR_METADATA = duo.metadata(
    TARGET_NAME,
    character_id="npc_carl_runga",
    display_name="Carl Runga",
    traits=["slow_heavy"],
    # Frame pixels of the 320x352 side-view frame, the drawing at rest.
    sockets={"head": (167.0, 180.5), "chest": (164.5, 233.0), "hand_l": (158.0, 272.0), "hand_r": (162.5, 274.0),
             "speech_bubble": (166.0, 158.0)},
)
ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Carl Runga is the loud, broad half of a Runge-Kutta duo, parodying German numerical "
            "analyst Carl Runge: a Goettingen professor with Runge's bald dome and full beard, in a "
            "black frock coat over a wine waistcoat. He thinks in sampled slopes, insists that four "
            "evaluations beat Oiler's first guess, and tries to seize Oiler's Kernel with Martin Cutta."
        ),
        "gameplay_description": (
            "Use as a forceful numerical-methods rival, co-boss, mechanic, or playable bruiser. His "
            "actions should sample, correct, average, and then commit; he supplies confidence and "
            "momentum while Cutta supplies precision."
        ),
        "dialogue_hints": {"barks": ["I sample four times and average.", "Cutta does the coefficients. I do the conviction.",
                                     "Check the middle. Check it twice."]},
    }
)


def render(out_dir: str | Path, **opts):
    del opts
    return duo.render(TARGET_NAME, ACTOR_METADATA, Path(out_dir))


def render_portraits(out_dir: str | Path, **opts):
    del opts
    return duo.render_portraits(TARGET_NAME, (160.0, 190.0), (40.0, 52.0), (72.0, 202.0), Path(out_dir))


__all__ = ["ACTOR_METADATA", "render", "render_portraits"]
