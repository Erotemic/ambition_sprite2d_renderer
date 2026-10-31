"""Which clips of a motion library are the same keyed pose sequence?

Groups each library's `clips/*.clip.json` by the ordered sequence of their
`pose_keys[*].state` (or named `pose`) values. Duration is not part of the
grouping; a group whose members play at different lengths says so. It is a
source audit, not a visual comparison: two clips with the same keys can
still be drawn differently, and two with different keys can look alike.

    python -m ambition_sprite2d_renderer.devtools.clip_alias_audit
    python -m ambition_sprite2d_renderer.devtools.clip_alias_audit fighting_polygon_v1 --clips launch,hit,tech
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

HUMANOID = Path(__file__).resolve().parents[1] / "data" / "motion" / "humanoid"
POLYGON_LIBRARIES = ("fighting_polygon_v1", "fighting_brawler_v1", "projectile_beast_v1")


def alias_groups(library: str) -> list[tuple[list[str], set[float]]]:
    """Every group of two or more clips with identical ordered keys, and the
    distinct durations among them."""
    groups: dict[tuple, list[tuple[str, float]]] = defaultdict(list)
    for path in sorted((HUMANOID / library / "clips").glob("*.clip.json")):
        doc = json.loads(path.read_text())
        keys = tuple(
            json.dumps(key.get("state", key.get("pose")), sort_keys=True) for key in doc.get("pose_keys", [])
        )
        groups[keys].append((doc.get("id", path.name), float(doc.get("duration_s", 0.0))))
    return sorted(
        ([name for name, _ in members], {duration for _, duration in members})
        for members in groups.values()
        if len(members) > 1
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("libraries", nargs="*", default=list(POLYGON_LIBRARIES))
    parser.add_argument("--clips", help="only groups containing one of these clips (comma-separated)")
    args = parser.parse_args(argv)
    only = set(args.clips.split(",")) if args.clips else None
    for library in args.libraries:
        print(library)
        for names, durations in alias_groups(library):
            if only and not only & set(names):
                continue
            timing = "" if len(durations) == 1 else f"  (durations differ: {sorted(durations)})"
            print(f"  {', '.join(names)}{timing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
