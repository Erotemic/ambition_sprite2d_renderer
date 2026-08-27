#!/usr/bin/env python3
"""Three things a posed cutout character must not do, measured on the pixels.

⛔⛔ A POSE FILE CANNOT TELL YOU ANY OF THEM. Whether a limb reads as attached,
whether a foot is standing on the floor, and whether the figure is one object are
facts about where the ART lands after the bones move -- not about the numbers
that moved them. Each of these was authored past, in one afternoon, by someone
reading the angles and believing them.

  ROOTS   A limb may not show only its TIP, far from its own joint. The Medic's shirt
          is black and her arms are not, so with the far shoulder tucked behind
          the trunk her forearm simply appears past the shirt's edge, joined to
          nothing the eye can follow. Topology passes on every one of those
          frames; so does adjacency; so does "is the root visible", which also
          condemns the Actor's far thigh for the crime of standing behind her
          near one. What separates the two is DISTANCE: a thigh hidden behind a
          shin still has art within a pixel or two of the hip, and a forearm
          orphaned at the hip does not -- and what tells those apart is whether
          the MIDDLE segment is on screen. The Actor's rear leg starts 15px from
          the hip and reads perfectly, because a whole shin and boot come out
          from under the coat hem. The Medic's far arm chambered behind her shirt
          shows a hand and nothing else: a fist growing out of her own hip. The
          measured bound on her rig is `far_arm_u <= 95`.

  FLOOR   A grounded row's lowest foot belongs ON the floor. Rising above it is
          an authored lift and is reported, not failed; sinking BELOW it is
          always wrong, and it is what a root solver that grounds the wrong
          ankle produces -- ground the foot that folded FURTHEST and a leg swept
          out at hip height becomes the contact point, burying the standing one.

  PIECES  The silhouette is one connected component. The weakest of the three,
          and kept because it is the only one that catches a part whose bind
          pivot is simply wrong.

Usage:
    uv run python scripts/check_character_reads.py medic actor
    uv run python scripts/check_character_reads.py medic --clips idle,jab --strict
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ambition_sprite2d_renderer.authoring.motion_ir import CharacterMotionBinding
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument

#: Overscan for the probe renders. Generous: a limb thrown outside the logical
#: frame would otherwise be measured as absent rather than as reaching.
PAD = (90, 110, 110, 60)

CHAINS = {
    "near_arm": ("near_arm_u", "near_arm_l", "near_arm_hand"),
    "far_arm": ("far_arm_u", "far_arm_l", "far_arm_hand"),
    "near_leg": ("near_leg_u", "near_leg_l", "near_leg_foot"),
    "far_leg": ("far_leg_u", "far_leg_l", "far_leg_foot"),
}

#: ⛔ THE SMALLEST VISIBLE CHAIN IS THE ONE THE DEFECT LOOKS LIKE. Set this at a
#: comfortable 40px and the check skips exactly the frames it exists to catch --
#: the Medic's orphaned fist is 18 pixels of hand. Below this a limb really is
#: behind the body and makes no claim about where it attaches; at or above it,
#: something is on screen and has to come from somewhere.
MIN_CHAIN_PX = 8
#: ⭐ THE BAR IS THE DRAWING'S OWN, NOT A CONSTANT. How far a limb's visible art
#: sits from its joint at rest is a fact about the costume -- the Actor's
#: cardigan panel already covers her far shoulder in the pose she was drawn in.
#: So the rest pose sets the bar and a pose may not read worse than the art does
#: by more than this many published pixels.
REST_GAP_SLACK_PX = 7.0
#: ...and even then it is only a defect if the segment BETWEEN root and tip is
#: off screen too. That is what separates a shin coming out from under a coat hem
#: from a fist growing out of a hip.
MIN_MIDDLE_PX = 18
#: Rows that leave the ground on purpose. Everything else owes the floor a foot.
AIRBORNE = {
    "air_back", "air_dodge", "air_down", "air_forward", "air_land", "air_neutral",
    "air_up", "double_jump", "fall", "fall_special", "float_glide", "fly",
    "footstool_jump", "hover", "jump", "launch", "ledge_attack", "ledge_catch",
    "ledge_climb", "ledge_drop", "ledge_getup", "ledge_getup_attack", "ledge_grab",
    "ledge_jump", "ledge_roll", "meteor", "shield_break_fall", "shield_break_launch",
    "swim", "tumble", "wall_grab", "wall_jump", "wall_tech", "wall_tech_jump",
    "ceiling_tech", "ground_bounce", "splat", "blink_in", "blink_out", "entrance",
}


def _rest_clip(prepared) -> str:
    """Name of a one-frame clip holding the SVG's own rest pose.

    Installed into the loaded library in memory only -- the bar has to be the
    drawing, and the drawing is not one of the authored rows.
    """
    import dataclasses

    from ambition_sprite2d_renderer.authoring.motion_ir import ClipPoseKey

    name = "__rest_baseline__"
    if name in prepared.library.clips:
        return name
    template = next(iter(prepared.library.clips.values()))
    prepared.library.clips[name] = dataclasses.replace(
        template,
        id=name,
        loop=False,
        duration_s=template.frame_duration_ms / 1000.0,
        frame_count=1,
        pose_keys=(ClipPoseKey.from_dict(
            {"at_s": 0.0, "frame": 0, "state": {"bones": {}}}),),
        tracks=(),
        markers=(),
    )
    return name


def _visible_px(doc, occluders, clip, t) -> int:
    mask = _mask(doc, clip, t)
    if occluders is not None:
        mask = mask & ~_mask(occluders, clip, t)
    return int(mask.sum())


def _joint_gap(doc, chain, occluders, root_bone, clip, t):
    """Published pixels from a limb's own joint to the nearest VISIBLE art of it.

    `None` when the chain has too little on screen to read either way -- a limb
    genuinely behind the body is not making a claim about where it attaches.
    """
    from ambition_sprite2d_renderer.authoring.rigdoc import translate_bone_worlds

    mask = _mask(chain, clip, t)
    if occluders is not None:
        mask = mask & ~_mask(occluders, clip, t)
    if int(mask.sum()) < MIN_CHAIN_PX:
        return None
    world, _params = doc.solve(clip, float(t))
    world = translate_bone_worlds(world, float(PAD[0]), float(PAD[1]))
    if root_bone not in world:
        return None
    jx, jy = world[root_bone].origin
    ys, xs = mask.nonzero()
    return float(np.sqrt(((xs - jx) ** 2 + (ys - jy) ** 2).min()))


def _subset(doc: RigDocument, names) -> RigDocument:
    data = copy.deepcopy(doc.data)
    data["parts"] = [p for p in data["parts"] if p["name"] in names]
    return RigDocument(data, source_path=doc.source_path)


def _mask(doc: RigDocument, clip: str, t: float, alpha: int = 24) -> np.ndarray:
    return np.array(doc.render_at(clip, t, supersample=1, padding=PAD)
                    .getchannel("A")) > alpha


def _components(mask: np.ndarray):
    """8-connected component sizes, largest first."""
    height, width = mask.shape
    labels = np.zeros((height, width), np.int32)
    sizes = []
    current = 0
    for sy, sx in zip(*mask.nonzero()):
        if labels[sy, sx]:
            continue
        current += 1
        labels[sy, sx] = current
        stack = [(sy, sx)]
        count = 0
        while stack:
            y, x = stack.pop()
            count += 1
            y0, y1 = max(0, y - 1), min(height, y + 2)
            x0, x1 = max(0, x - 1), min(width, x + 2)
            block = mask[y0:y1, x0:x1] & (labels[y0:y1, x0:x1] == 0)
            for dy, dx in zip(*block.nonzero()):
                labels[y0 + dy, x0 + dx] = current
                stack.append((y0 + dy, x0 + dx))
        sizes.append(count)
    sizes.sort(reverse=True)
    return sizes


def check(character: str, clips=None):
    binding = CharacterMotionBinding.load(
        REPO / "ambition_sprite2d_renderer" / "data" / "characters"
        / character / f"{character}.motion.json"
    )
    prepared = binding.load_prepared()
    doc = prepared.to_rig_document()
    parts = {p["name"]: p for p in doc.data["parts"]}

    chain_doc, mid_doc, occ_doc = {}, {}, {}
    for chain, bones in CHAINS.items():
        mine = {n for n, p in parts.items() if p.get("bone") in bones}
        if not mine:
            continue
        chain_doc[chain] = _subset(doc, mine)
        mid_doc[chain] = _subset(doc, {n for n, p in parts.items()
                                       if p.get("bone") in bones[:2]})
        # Occlusion is decided by z: everything painted in FRONT of the whole
        # chain can hide it.
        top = max(float(parts[n].get("z", 0)) for n in mine)
        above = {n for n in parts if n not in mine and float(parts[n].get("z", 0)) > top}
        occ_doc[chain] = _subset(doc, above) if above else None

    # The bar, measured on the rig at rest -- the pose the artist drew.
    rest = _rest_clip(prepared)
    rest_gap = {c: _joint_gap(doc, chain_doc[c], occ_doc[c], CHAINS[c][0], rest, 0.0)
                for c in chain_doc}

    feet = {n for n, p in parts.items() if str(p.get("bone", "")).endswith("_foot")}
    foot_doc = _subset(doc, feet) if feet else None
    floor_y = PAD[1] + binding.render.root_anchor_px[1]

    errors, notes = [], []
    for name in sorted(clips or prepared.library.clips):
        clip = prepared.library.clips[name]
        for i in range(clip.frame_count):
            t = round(i * clip.frame_duration_ms / 1000.0 / max(clip.duration_s, 1e-9), 9)
            where = f"{character} {name} f{i}"

            for chain in chain_doc:
                gap = _joint_gap(doc, chain_doc[chain], occ_doc[chain],
                                 CHAINS[chain][0], name, t)
                if gap is None:
                    continue
                allowed = (rest_gap[chain] or 0.0) + REST_GAP_SLACK_PX
                if gap <= allowed:
                    continue
                middle = _visible_px(mid_doc[chain], occ_doc[chain], name, t)
                if middle >= MIN_MIDDLE_PX:
                    continue
                errors.append(
                    f"{where}: {chain} shows only its tip, {gap:.0f}px from its own "
                    f"joint ({rest_gap[chain]:.0f}px at rest) and {middle}px of the "
                    f"segment between -- it reads as a limb joined to nothing")

            if foot_doc is not None and name not in AIRBORNE:
                mask = _mask(foot_doc, name, t)
                if mask.any():
                    low = int(mask.nonzero()[0].max())
                    if low - floor_y > 3:
                        errors.append(f"{where}: lowest foot {low - floor_y:.0f}px "
                                      f"THROUGH the floor")
                    elif floor_y - low > 3:
                        notes.append(f"{where}: lowest foot {floor_y - low:.0f}px "
                                     f"above the floor (authored lift?)")

            sizes = _components(_mask(doc, name, t))
            if len(sizes) > 1 and sizes[1] >= max(8, sum(sizes) * 0.004):
                errors.append(f"{where}: silhouette is {len(sizes)} pieces "
                              f"{sizes[:3]} -- a part has come off")
    return errors, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("characters", nargs="+")
    parser.add_argument("--clips", help="comma-separated clip ids (default: all)")
    parser.add_argument("--quiet-lifts", action="store_true",
                        help="do not print the authored-lift notes")
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero if anything at all is reported")
    args = parser.parse_args()
    clips = args.clips.split(",") if args.clips else None

    failed = False
    for character in args.characters:
        errors, notes = check(character, clips)
        for line in errors:
            print(f"ERROR {line}")
        if not args.quiet_lifts:
            for line in notes:
                print(f"note  {line}")
        print(f"{character}: {len(errors)} errors, {len(notes)} lifts")
        failed |= bool(errors) or (args.strict and bool(notes))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
