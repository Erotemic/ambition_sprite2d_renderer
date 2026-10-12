"""What the three targets of GNU-ton the scholar say of the actor.

One man, three sheets (`gnu_ton_scholar_villain`, `gnu_ton_scholar_fighter`,
`gnu_ton_scholar_boss`). Each rig document carries this as its
`actor_metadata`, with the bindings of the rows that sheet has.
"""
from __future__ import annotations

import json
from pathlib import Path

DESCRIPTION = (
    "GNU-ton the scholar: a small man in a coat and a wig, with a quill and a "
    "book. A parody of Isaac Newton. In his boss fight he rides the giant gnu "
    "and conducts its fists; on its back, and on a platform-fighter stage, he "
    "fights on his own feet."
)
GAMEPLAY = (
    "The quill is long and fast and does little; the book is short and slow "
    "and ends a fight. As a boss he conducts from the saddle and fights a "
    "player who climbs to him."
)

#: A binding, and the rows that can serve it: the first that the sheet has.
_BINDINGS = (
    ("default", ("idle", "rest")),
    ("locomotion.walk", ("walk",)),
    ("locomotion.run", ("run",)),
    ("traversal.jump", ("jump",)),
    ("traversal.fall", ("fall",)),
    ("action.melee.primary", ("jab", "point")),
    ("action.melee.side", ("attack_side",)),
    ("action.melee.up", ("attack_up",)),
    ("action.melee.down_tilt", ("attack_down",)),
    ("action.special.primary", ("special_neutral", "conduct")),
    ("action.defense.block", ("shield_hold", "brace")),
    ("reaction.hit", ("hit",)),
    ("reaction.death", ("death",)),
)


def actor_metadata(rows) -> dict:
    """The metadata for a sheet with the rows `rows` (their names)."""
    have = set(rows)
    bindings = {}
    for key, names in _BINDINGS:
        row = next((name for name in names if name in have), None)
        if row is not None:
            bindings[key] = {"animation": row, "events": []}
    return {
        "authoring_description": DESCRIPTION,
        "gameplay_description": GAMEPLAY,
        "animation_bindings": bindings,
    }


def stamp(rig_path: Path) -> None:
    """Write the metadata into the rig document at `rig_path`."""
    from ambition_sprite2d_renderer.rigbuild import creature_rig as CR

    doc = json.loads(rig_path.read_text(encoding="utf8"))
    stamped = {"name": doc["name"], "actor_metadata": actor_metadata(doc["clips"])}
    stamped.update((key, value) for key, value in doc.items() if key not in stamped)
    rig_path.write_text(CR.compact_keys(json.dumps(stamped, indent=1)) + "\n", encoding="utf8")
