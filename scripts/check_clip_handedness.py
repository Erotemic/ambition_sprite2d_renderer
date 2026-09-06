#!/usr/bin/env python3
"""Every clip must reach FORWARD, or say that it does not.

⛔⛔ THE BUG CLASS THIS EXISTS FOR. Jon, 2026-08-27, on the Officer's side
special: *"the officer side b fires the right direction but art is horizontally
flipped. idk why these flip bugs happen so often, but we need to think of how to
make them structurally difficult."*

What had happened is worth stating exactly, because it is not what it looked
like. Nothing flipped a frame. The `shoot` clip's bone rotations were authored
with every sign inverted, so the Officer extended his gun arm BACKWARDS, over
his own shoulder; the engine then mirrored the whole sprite to face his target,
so the round left in the right direction while he aimed behind himself. A
"horizontal flip" and "a sign error in a pose" look identical on screen and have
nothing in common in the data.

⭐⭐ SO THE CHECK IS ON PUBLISHED PIXELS, not on the pose. A rule about rotation
signs would have to know each rig's convention and would be wrong for the next
one; "the dangerous end of a reach goes toward the character's face" is true of
every humanoid ever drawn, and the sheet already states which way that is
(`authored_faces_left`).

⛔ WHY THE EXISTING GUARD DID NOT CATCH IT. `devtools/swing_spec.py` has had a
`hitbox_in_front` pixel invariant for a while, and it computes forward from a
`facing` field each spec types by hand. Two problems, both structural: the rule
only runs `if spec.get("pixel_invariants")`, so it is opt-in and the Officer's
shoot spec did not opt in; and the hand-typed `facing` had drifted — 14 of his
15 specs said `east` while his rig is drawn WEST, so the number the rule would
have used was wrong anyway. A fact stated in three places, one of them by hand
in a hundred files, is a hiding place. This reads the sheet.

Usage:

    uv run python scripts/check_clip_handedness.py officer
    uv run python scripts/check_clip_handedness.py            # every rigged sheet
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import yaml
from PIL import Image

# Clips whose dangerous end is BEHIND the fighter on purpose. Naming them is the
# opt-out, and it is deliberately a short hand-kept list rather than a pattern:
# "back" in a clip name means several different things and a regex would quietly
# excuse the next real defect.
REACHES_BACKWARD = {
    "air_back",
    "throw_back",
}

# How far behind the body's own centre a hit polygon may sit before it is a
# finding. Generous: a swing's hull can trail past the hip on its way through,
# and a hull that overshoots by a few pixels is animation. The Officer's inverted
# clip put its ENTIRE polygon behind him.
BEHIND_SLACK_PX = 10.0


def check_sheet(
    sheet_dir: pathlib.Path, target: str, verbose: bool, required: bool = False
) -> list[str]:
    """Every published hit polygon must sit ahead of the body that throws it.

    ⛔⛔ ABSENCE IS NOT SUCCESS FOR A TARGET SOMEBODY NAMED. A missing manifest
    returned no findings, so `check_clip_handedness.py officer` on a tree with no
    generated sheets — which is every clean checkout, since they are gitignored —
    counted the request and skipped the check, then printed
    `OK: 1 sheet(s), every clip reaches forward`.

    ⚠ `required` is the distinction, and it is not pedantry: the DEFAULT
    population is a glob over every published sheet, and most of them are not
    rigged fighters — they publish no per-animation hit polygons and never
    will. Failing those would make the checker permanently red and therefore
    ignored. So a sheet nobody asked about may be silently unrigged; a sheet
    somebody NAMED may not.
    """
    manifest = sheet_dir / f"{target}_spritesheet.yaml"
    if not manifest.exists():
        if not required:
            return []
        return [
            f"{target}: no `{manifest.name}` under {sheet_dir} — the sheet is "
            f"not generated, so nothing was checked. Run "
            f"`./scripts/regen/sprites.sh --target {target}` first."
        ]
    doc = yaml.safe_load(manifest.read_text())
    metrics = doc.get("body_metrics") or {}
    animations = metrics.get("animations") or {}
    bbox = metrics.get("body_pixel_bbox")
    if not animations or not bbox:
        if not required:
            return []
        missing = "animations" if bbox else "body_pixel_bbox"
        return [
            f"{target}: its manifest publishes no `body_metrics.{missing}`, so "
            f"no clip could be judged against the body. A rigged sheet publishes "
            f"both — if this target is not rigged, it does not belong on a "
            f"handedness run."
        ]

    ron_path = sheet_dir / f"{target}_spritesheet.ron"
    ron = ron_path.read_text() if ron_path.exists() else ""
    # ⛔ THE ONE AUTHORITY FOR WHICH WAY THIS ART IS DRAWN, read out of the
    # published sheet rather than typed into a spec beside every clip. The
    # hand-typed copy is what drifted: 14 of the Officer's 15 specs claimed
    # `east` for a rig drawn WEST, so any rule trusting them was already wrong.
    faces_left = "authored_faces_left: true" in ron
    forward = -1.0 if faces_left else 1.0

    # The body's own centre, in the same pixel frame the polygons use.
    centre_x = bbox["x"] + bbox["w"] / 2.0
    centre_y = bbox["y"] + bbox["h"] / 2.0

    findings = []
    findings.extend(_declared_facing_agrees(target, faces_left))
    for anim, entry in sorted(animations.items()):
        hitbox = (entry or {}).get("hitbox") or {}
        poly = hitbox.get("poly")
        if not poly:
            continue
        # How far the polygon's furthest vertex sits in each direction. A swing
        # is judged by where its REACH is, not by its centroid: a hull straddling
        # the body is an ordinary wide swing.
        ahead = max((x - centre_x) * forward for x, _ in poly)
        behind = max((centre_x - x) * forward for x, _ in poly)
        # ⛔⛔ A VERTICAL ATTACK IS NOT A FORWARD REACH, and asking whether it is
        # "in front" is the wrong question about it. An up-tilt's hull lives
        # above the head and a down-air's below the feet; either may sit a little
        # behind the midline without anything being wrong, and two real clips
        # (`medic/air_up`, `pugnacious_polygon/attack_up`) do exactly that. The
        # test is which axis the hull actually travels along, measured — not a
        # list of clip names ending in `_up`, which would excuse a genuinely
        # inverted up-attack and would need extending for every new naming
        # convention.
        centroid_x = sum(x for x, _ in poly) / len(poly)
        centroid_y = sum(y for _, y in poly) / len(poly)
        travels_vertically = abs(centroid_y - centre_y) > abs(centroid_x - centre_x)
        if verbose:
            axis = "vertical" if travels_vertically else "horizontal"
            print(
                f"  {anim:22s} ahead {ahead:7.1f}px  behind {behind:7.1f}px  {axis}"
            )
        if anim in REACHES_BACKWARD or travels_vertically:
            continue
        if ahead <= 0.0 and behind > BEHIND_SLACK_PX:
            findings.append(
                f"{target}/{anim}: its whole hit polygon sits up to "
                f"{behind:.0f}px BEHIND the body on a sheet drawn facing "
                f"{'left' if faces_left else 'right'}. Either the pose's rotation "
                f"signs are inverted — the shape this exists to catch — or the "
                f"clip belongs in REACHES_BACKWARD."
            )
    return findings


# Which motion library each rigged sheet draws from. Hand-kept and short: only
# characters with a FORKED library can disagree with their sheet, and the fork is
# a deliberate act somebody performs.
LIBRARY_FOR_TARGET = {
    "officer": "officer_brawler_v1",
    "medic": "medic_triage_v1",
    "performer": "performer_stage_v1",
    "author": "author_pen_v1",
    "pointed_polygon": "fighting_polygon_v1",
    "pugnacious_polygon": "fighting_brawler_v1",
}


def _declared_facing_agrees(target: str, faces_left: bool) -> list[str]:
    """A library's specs must not claim a handedness its sheet contradicts.

    ⛔⛔ THIS IS HOW THE OFFICER'S BUG WAS BORN. `officer_brawler_v1` was FORKED
    from `fighting_brawler_v1`, whose rig is drawn EAST — and the fork copied the
    metadata without the handedness. All fifteen of his specs said `east` while
    his own art faces WEST. So an author checking the neighbouring clips before
    writing a new one, which is the correct instinct and what the house rules
    ask for, was told the wrong thing by every neighbour.

    The field has no runtime authority — `swing_spec.py` is the only reader and
    its library path is hardcoded — which is exactly why it rotted unnoticed. It
    is still what a human reads, so it has to be true.
    """
    library = LIBRARY_FOR_TARGET.get(target)
    if library is None:
        return []
    specs = (
        pathlib.Path(__file__).resolve().parent.parent
        / "ambition_sprite2d_renderer/data/motion/humanoid"
        / library
        / "specs"
    )
    if not specs.is_dir():
        return []
    import json

    expected = "west" if faces_left else "east"
    wrong = sorted(
        path.stem.removesuffix(".spec")
        for path in specs.glob("*.spec.json")
        if json.loads(path.read_text()).get("facing") not in (None, expected)
    )
    if not wrong:
        return []
    return [
        f"{target}: {len(wrong)} spec(s) in {library} declare the opposite "
        f"handedness to the published sheet (which is drawn "
        f"{'west' if faces_left else 'east'}): {', '.join(wrong[:6])}"
        f"{' …' if len(wrong) > 6 else ''}. A forked library that copied its "
        f"metadata without its handedness tells every future author the wrong "
        f"thing."
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", help="sheet targets; default all rigged")
    parser.add_argument(
        "--assets",
        default="../../../crates/ambition_platformer2d_actor_monolith/assets/sprites",
        help="published sprite directory",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    root = (pathlib.Path(__file__).resolve().parent / args.assets).resolve()
    targets = args.targets or sorted(
        p.name[: -len("_spritesheet.yaml")]
        for p in root.glob("*_spritesheet.yaml")
    )

    # ⛔⛔ AND AN EMPTY DEFAULT RUN IS NOT A PASS EITHER. The default population is
    # a glob over generated files; on a clean tree it finds none, and reporting
    # that as success is the same defect one level up.
    if not targets:
        print(
            f"FAIL no `*_spritesheet.yaml` under {root} — the sheets are "
            "generated and gitignored, so this checker had nothing to read. "
            "Run `./scripts/regen/sprites.sh` first, or name targets explicitly."
        )
        return 1

    findings = []
    for target in targets:
        if args.verbose:
            print(f"{target}:")
        findings.extend(
            check_sheet(root, target, args.verbose, required=bool(args.targets))
        )

    if not findings:
        print(f"OK: {len(targets)} sheet(s), every clip reaches forward.")
        return 0
    for finding in findings:
        print(f"FAIL {finding}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
