#!/usr/bin/env python3
"""Publish the Smash-style scholar *candidate* rig from the accepted D2 SVG.

Run after the D2 boss-rig build.  A separate fighter rig JSON avoids changing
its boss animation sheet/catalog: both documents share the same labeled SVG,
bones, and parts, but publish different clips and target ids.

    uv run python scripts/build_gnu_ton_scholar_fighter_rig.py
    ./scripts/regen/sprites.sh --target gnu_ton_scholar_fighter

Neither gameplay move timing/hit volumes nor fighter-roster registration are
installed here: only authored visuals and their sprite publication contract.
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

TARGET = "gnu_ton_scholar_fighter"
RIG = ROOT / "ambition_sprite2d_renderer" / "targets/characters/rigged" / f"{TARGET}.rig.json"


def make_spec():
    # Reuse the *same* skeleton and D2 art, without touching the boss pose rows.
    # A modestly larger logical frame gives room for fighter attacks and spins.
    boss = B.make_spec()
    return replace(boss, name=TARGET, rig_path=RIG, rows=F.ROWS,
                   clips=F.CLIPS, frame_size=(280, 300))


def main():
    spec = make_spec()
    if not spec.svg_path.exists():
        raise SystemExit("Run the existing D2 art and boss-rig builders first")
    if not B.RIG.exists():
        raise SystemExit("D2 boss rig is missing; build it first")
    # Build JSON only.  CR.write() rewrites the SVG's embedded catalog to match
    # this secondary target.  That would change the canonical boss art's
    # metadata while leaving the original boss rig unchanged.
    fighter = CR.build(spec)
    boss = RigDocument.load(B.RIG)
    assert [p["name"] for p in fighter["parts"]] == [p["name"] for p in boss.parts]
    assert [b["name"] for b in fighter["bones"]] == [b["name"] for b in boss.bones]
    RIG.parent.mkdir(parents=True, exist_ok=True)
    text = CR.compact_keys(json.dumps(fighter, indent=1))
    RIG.write_text(text + "\n", encoding="utf8")
    A.stamp(RIG)
    doc = RigDocument.load(RIG)
    print(f"wrote {RIG.relative_to(ROOT)} ({len(doc.clips)} fighting animations)")


if __name__ == "__main__":
    main()
