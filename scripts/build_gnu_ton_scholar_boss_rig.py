#!/usr/bin/env python3
"""The scholar as the BOSS wears him: his boss rows, then the rows of his duel.

In his boss fight the scholar rides the giant gnu and conducts (the ten rows
of `gnu_ton_scholar_villain`), and on the giant's back he fights with moves of
his fighter's table (rows of `gnu_ton_scholar_fighter`). A boss body draws ONE
sheet. This target is that sheet: the villain's rows first and in their order
(a boss sheet's first six rows are fixed slots), then the fighter rows the
duel plays.

The same SVG, bones and parts as the two other targets; only the list of rows
is its own.

    uv run python scripts/build_gnu_ton_scholar_boss_rig.py
    ./scripts/regen/sprites.sh --target gnu_ton_scholar_boss
"""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_gnu_ton_scholar_villain_rig as B  # noqa: E402
import gnu_ton_scholar_actor as A  # noqa: E402
import gnu_ton_scholar_fighter_poses as F  # noqa: E402
from ambition_sprite2d_renderer.rigbuild import creature_rig as CR  # noqa: E402
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument  # noqa: E402

TARGET = "gnu_ton_scholar_boss"
RIG = ROOT / "ambition_sprite2d_renderer" / "targets/characters/rigged" / f"{TARGET}.rig.json"

#: The fighter rows the duel plays: the moves he chooses on the giant's back
#: (`DUEL_MOVES` of the game's conductor module), his guard, and his stance.
DUEL_ROWS = (
    "idle", "jab", "attack_side", "attack_up", "attack_down", "smash_forward",
    "shield_raise", "shield_hold", "shield_hit", "spot_dodge", "hit_heavy", "taunt",
    # He goes to the player along the back, rolls through him, is launched
    # by a blow, lands, and comes back when he is thrown off the back.
    "walk", "run", "roll", "launch", "fall", "land", "special_up",
    # The rest of his jab's string, and the strike out of his run.
    "jab_2", "jab_3", "dash_attack",
)


def make_spec():
    boss = B.make_spec()
    fighter = {row[0]: row for row in F.ROWS}
    rows = list(B.ROWS) + [fighter[name] for name in DUEL_ROWS]
    clips = dict(B.CLIPS)
    clips.update({name: F.CLIPS[name] for name in DUEL_ROWS})
    return replace(boss, name=TARGET, rig_path=RIG, rows=rows, clips=clips, frame_size=(280, 300))


def main():
    spec = make_spec()
    if not spec.svg_path.exists() or not B.RIG.exists():
        raise SystemExit("Build the D2 art and the boss rig (`gnu_ton_scholar_villain`) first")
    # JSON only, as the fighter's builder: `CR.write` would rewrite the catalog
    # in the shared SVG.
    doc = CR.build(spec)
    RIG.parent.mkdir(parents=True, exist_ok=True)
    RIG.write_text(CR.compact_keys(json.dumps(doc, indent=1)) + "\n", encoding="utf8")
    A.stamp(RIG)
    print(f"wrote {RIG.relative_to(ROOT)} ({len(RigDocument.load(RIG).clips)} rows)")


if __name__ == "__main__":
    main()
