#!/usr/bin/env python3
"""Draw the giant gnu (GNU-ton's mount) as one SVG, to look at a pose.

The giant's drawing is not here. It is the published target's own module,
``ambition_sprite2d_renderer/targets/characters/gnu_ton_boss/giant_art.py``:
its stances, its expressions, its rows and its frames. This script asks that
module for one pose and writes it, with the whole giant in view.

    uv run python scripts/svg_art/giant_gnu_art.py OUT.svg [STANCE] [EXPRESSION] [--arms] [--curl]

``STANCE`` is ``sloped`` (on all fours) or ``reared``. ``EXPRESSION`` is a
name of ``giant_art.EXPRESSIONS`` (``ordered`` and ``free`` are its two faces
at rest). ``--arms`` draws an arm from each shoulder to its fist: the fight
has the fists as bodies of their own, so the sheets have no arms. ``--curl``
draws the curled horns of the first design.
"""
from __future__ import annotations

import sys
from pathlib import Path

from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import giant_art

#: The view: the whole giant in each stance, its arms up also.
VIEW = (0.0, -320.0, 1800.0, 1452.0)

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    stance = giant_art.STANCES[args[1] if len(args) > 1 else "sloped"]
    pose = dict(stance=stance, expr=giant_art.EXPRESSIONS[args[2] if len(args) > 2 else stance["expr"]], head=(0.0, 0.0), dust=0.0)
    Path(args[0]).write_text(
        giant_art.giant_svg(pose, arms="--arms" in sys.argv, horns="curl" if "--curl" in sys.argv else "gnu", view=VIEW)
    )
