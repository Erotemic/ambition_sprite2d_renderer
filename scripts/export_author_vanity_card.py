"""Bake the author vanity-card animation into placements the engine can play.

The card is authored here, in Python, because this is where the rigs, the IK
solver and the choreography live. None of that belongs in the game: solving two
bone chains per frame to draw a title card would put an animation system in the
engine to serve one screen.

So the split is: **Python owns the motion, Rust owns the drawing.** This script
runs the real timeline through the real solver — the same
:func:`compose_actors` the GIF uses, never a second copy of the arithmetic — and
writes down where every part ENDED UP on every frame. What the engine gets is a
flipbook of transforms: a list of images, and per frame a list of
``(part, centre, rotation)``. Drawing that is a loop over quads, which is the
kind of thing a game engine is already good at.

Two properties this buys, both of which the frame-sequence card lacked:

* the payload is 40 small part rasters instead of 80 full-canvas frames, and it
  scales to any resolution because the parts are placed, not pre-composited;
* the animation is *data*, so retiming or re-posing means re-running this
  script — no engine change, no shader, no new system.

⚠ **the baked table is verified against the renderer, not trusted.** ``--verify``
re-composites the baked placements with PIL and diffs them against a direct
``render_frame`` of the same frame. A sign error in the rotation or a mishandled
pivot shows up there, in seconds, instead of in a Bevy window twenty minutes
later.

Usage::

    uv run python scripts/export_author_vanity_card.py
    uv run python scripts/export_author_vanity_card.py --verify
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from PIL import Image

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument, visible_parts
from ambition_sprite2d_renderer.targets.characters import player_robot_v3 as player_robot_v3_target

import render_author_vanity_dialog as dialog

REPO_ROOT = ROOT.parents[1]
PAYLOAD_DIR = REPO_ROOT / "game" / "ambition_content" / "assets" / "vanity_card" / "rig"
MANIFEST = REPO_ROOT / "game" / "ambition_content" / "assets" / "data" / "vanity_card_rig.ron"
ASSET_PREFIX = "vanity_card/rig"

# Raster scale for the exported part images, relative to canvas pixels. The card
# is authored on a 640x360 canvas and played on screens several times that, so
# the parts are baked at 4x and scaled down by the engine rather than up.
PART_OVERSAMPLE = 4.0

# The author's near-side arm draws OVER the prop; everything else on the author
# draws under it. Same split the GIF makes with two part-subset documents, kept
# here as a z-band because the exporter has no layers, only depths.
NEAR_ARM_PARTS = ("near_arm_u", "near_arm_l", "near_sleeve", "near_hand")

Z_ROBOT = 0
Z_AUTHOR_BODY = 1000
Z_PROP = 2000
Z_AUTHOR_NEAR_ARM = 3000


def rotate_clockwise(point: Tuple[float, float], degrees: float) -> Tuple[float, float]:
    """Rotate in SCREEN space, where +y is down and a positive angle is visually
    clockwise — the same convention ``blit_rotated`` and Bevy's `UiTransform`
    both use, so the baked number needs no adjustment at either end."""
    radians = math.radians(degrees)
    cos, sin = math.cos(radians), math.sin(radians)
    return (
        point[0] * cos - point[1] * sin,
        point[0] * sin + point[1] * cos,
    )


class PartAtlas:
    """Every part rasterized ONCE, pivot-centred, keyed by (actor, part name)."""

    def __init__(self) -> None:
        self.order: List[str] = []
        self.index: Dict[Tuple[str, str], int] = {}
        self.images: List[Image.Image] = []
        self.pivots: List[Tuple[float, float]] = []
        self.scales: List[float] = []

    def intern(
        self, actor: str, doc: RigDocument, part: dict, raster_scale: float
    ) -> Optional[int]:
        key = (actor, str(part.get("name")))
        if key in self.index:
            return self.index[key]
        sprite = doc.sprite_image(part, raster_scale)
        if sprite is None:
            return None
        image, pivot = sprite
        slot = len(self.order)
        self.index[key] = slot
        self.order.append(f"{actor}_{part.get('name')}")
        self.images.append(image)
        self.pivots.append((float(pivot[0]), float(pivot[1])))
        self.scales.append(raster_scale)
        return slot


def part_draws(
    atlas: PartAtlas,
    actor: str,
    placement,
    doc: RigDocument,
    z_base: int,
    *,
    only: Optional[Sequence[str]] = None,
    without: Optional[Sequence[str]] = None,
) -> List[dict]:
    """Where every visible sprite part of one actor lands, in canvas units.

    Mirrors :func:`rigdoc.paint_part`: the part's raster is pivot-centred on its
    bone's ORIGIN and rotated by ``bone.angle - rest_angle``. The only thing
    added here is the map from rig-document pixels to canvas pixels, which is
    exactly what ``ActorPlacement.point_for_bone`` already does.
    """
    style = placement.style
    raster_scale = style.render_scale * PART_OVERSAMPLE
    draws: List[dict] = []
    for part in visible_parts(doc.parts, doc.features):
        name = str(part.get("name"))
        if only is not None and name not in only:
            continue
        if without is not None and name in without:
            continue
        if part.get("kind") != "sprite":
            raise SystemExit(
                f"{actor}:{name} is a {part.get('kind')!r} part. Only rigid sprite parts "
                "can be baked as transforms — a vector part deforms with its bone and "
                "would need the engine to draw geometry, which is the thing this "
                "export exists to avoid."
            )
        bone_name = part.get("bone")
        if bone_name not in placement.world:
            continue
        # A part bound to an opacity channel is hidden when its channel is off;
        # for these two rigs that is the robot's blink, driven 0/1 with no tween
        # (see the dialog manifest), so a hidden part is simply not drawn.
        channel = part.get("opacity_channel")
        if channel and placement.params.get(channel, 0.0) <= 0.01:
            continue

        slot = atlas.intern(actor, doc, part, raster_scale)
        if slot is None:
            continue

        bone = placement.world[bone_name]
        angle = bone.angle - float(part.get("rest_angle", 0.0))
        pivot_screen = placement.point_for_bone(bone_name)

        image = atlas.images[slot]
        pivot_px = atlas.pivots[slot]
        # Canvas units per raster pixel: the doc is drawn at `raster_scale`, and
        # the actor is displayed at `effective_scale` of its document size.
        unit = style.effective_scale / raster_scale
        offset = (
            (image.width / 2.0 - pivot_px[0]) * unit,
            (image.height / 2.0 - pivot_px[1]) * unit,
        )
        spun = rotate_clockwise(offset, angle)
        draws.append(
            {
                "part": slot,
                "x": pivot_screen[0] + spun[0],
                "y": pivot_screen[1] + spun[1],
                "w": image.width * unit,
                "h": image.height * unit,
                "deg": angle,
                "z": z_base + int(round(float(part.get("z", 0.0)) * 10.0)),
            }
        )
    return draws


def prop_draw(atlas: PartAtlas, prop: Image.Image, state) -> dict:
    key = ("prop", "gamepad")
    if key not in atlas.index:
        atlas.index[key] = len(atlas.order)
        atlas.order.append("prop_gamepad")
        atlas.images.append(prop)
        atlas.pivots.append((prop.width / 2.0, prop.height / 2.0))
        atlas.scales.append(1.0)
    slot = atlas.index[key]
    return {
        "part": slot,
        "x": state.gamepad_center[0],
        "y": state.gamepad_center[1],
        "w": float(prop.width),
        "h": float(prop.height),
        # `draw_rotated_prop` rotates the PIL image by `angle` counter-clockwise,
        # so the screen-clockwise angle the engine wants is its negation.
        "deg": -float(state.gamepad_angle),
        "z": Z_PROP,
    }


def bake(verify: bool) -> Tuple[dict, PartAtlas]:
    dialog.ensure_rigs_exist()
    author_doc = RigDocument.load(dialog.AUTHOR_RIG_PATH)
    robot_doc = player_robot_v3_target.load_doc()
    author_hands_doc = dialog.hand_only_doc(author_doc)
    robot_hands_doc = dialog.hand_only_doc(robot_doc)
    author_style = dialog.calculate_style(author_doc, "vanity_idle", dialog.AUTHOR_TARGET_HEIGHT)
    robot_style = dialog.calculate_style(robot_doc, "idle", dialog.ROBOT_TARGET_HEIGHT)
    prop = dialog.render_gamepad()

    atlas = PartAtlas()
    frames: List[dict] = []

    for frame_index in range(dialog.ANIMATION_FRAMES):
        state = dialog.timeline_state(frame_index)
        robot, author = dialog.compose_actors(
            state,
            author_doc,
            author_hands_doc,
            author_style,
            robot_doc,
            robot_hands_doc,
            robot_style,
            prop.width,
        )

        draws: List[dict] = []
        draws += part_draws(atlas, "robot", robot, robot_doc, Z_ROBOT)
        draws += part_draws(
            atlas, "author", author, author_doc, Z_AUTHOR_BODY, without=NEAR_ARM_PARTS
        )
        draws.append(prop_draw(atlas, prop, state))
        draws += part_draws(
            atlas, "author", author, author_doc, Z_AUTHOR_NEAR_ARM, only=NEAR_ARM_PARTS
        )
        draws.sort(key=lambda row: row["z"])

        bubble = None
        if state.bubble_text and state.bubble_speaker:
            anchor = (
                robot.head_anchor() if state.bubble_speaker == "robot" else author.head_anchor()
            )
            box = (155, 52) if state.bubble_speaker == "robot" else (388, 24)
            bubble = {
                "text": state.bubble_text,
                "tail_x": anchor[0],
                "tail_y": anchor[1],
                "box_x": float(box[0]),
                "box_y": float(box[1]),
            }

        frames.append({"draws": draws, "bubble": bubble})

        if verify:
            verify_frame(
                frame_index,
                frames[-1],
                atlas,
                state,
                author_doc,
                author_hands_doc,
                author_style,
                robot_doc,
                robot_hands_doc,
                robot_style,
                prop,
            )

    manifest = {
        "canvas": (float(dialog.CANVAS_SIZE[0]), float(dialog.CANVAS_SIZE[1])),
        "frame_ms": int(dialog.FRAME_DURATION_MS),
        "frames": frames,
    }
    return manifest, atlas


def composite_from_bake(frame: dict, atlas: PartAtlas) -> Image.Image:
    """Re-draw one baked frame with PIL — the engine's job, done here to check it."""
    canvas = Image.new("RGBA", dialog.CANVAS_SIZE, (0, 0, 0, 0))
    for row in frame["draws"]:
        image = atlas.images[row["part"]]
        scaled = image.resize(
            (max(1, int(round(row["w"]))), max(1, int(round(row["h"])))),
            Image.Resampling.LANCZOS,
        )
        spun = scaled.rotate(-row["deg"], resample=Image.Resampling.BICUBIC, expand=True)
        canvas.alpha_composite(
            spun,
            (
                int(round(row["x"] - spun.width / 2.0)),
                int(round(row["y"] - spun.height / 2.0)),
            ),
        )
    return canvas


def verify_frame(
    frame_index: int,
    frame: dict,
    atlas: PartAtlas,
    state,
    author_doc,
    author_hands_doc,
    author_style,
    robot_doc,
    robot_hands_doc,
    robot_style,
    prop,
) -> None:
    """Diff the baked composition against the renderer's own output.

    Bubbles and the backdrop are excluded — the engine draws those as UI, so they
    are not part of what the bake claims. What IS claimed is that every rig part
    lands in the same place, and that is compared as a silhouette: resampling a
    part on its own cannot reproduce the renderer's supersampled edges pixel for
    pixel, but a part in the wrong POSITION, at the wrong SIZE, or spun the wrong
    WAY moves the silhouette a long way.
    """
    from PIL import ImageChops

    # ⚠ the backdrop has to come OFF the reference, not be "excluded" in prose.
    # `render_frame` fills the card first, so the reference silhouette was the
    # whole canvas and every frame read as ~85% wrong while the bake was in fact
    # correct — a verifier that fails on everything teaches nothing.
    painted_background = dialog.draw_background
    dialog.draw_background = lambda canvas: None
    try:
        reference = dialog.render_frame(
            replace(state, bubble_speaker=None, bubble_text=None),
            author_doc,
            author_hands_doc,
            dialog.parts_exclude_doc(author_doc, NEAR_ARM_PARTS),
            dialog.parts_include_doc(author_doc, NEAR_ARM_PARTS),
            author_style,
            robot_doc,
            robot_hands_doc,
            robot_style,
            prop,
        )
    finally:
        dialog.draw_background = painted_background
    baked = composite_from_bake(frame, atlas)

    def silhouette(image: Image.Image) -> Image.Image:
        return image.getchannel("A").point(lambda value: 255 if value > 96 else 0)

    ref_mask, bake_mask = silhouette(reference), silhouette(baked)
    difference = ImageChops.difference(ref_mask, bake_mask)
    wrong = sum(1 for pixel in difference.getdata() if pixel)
    covered = sum(1 for pixel in ref_mask.getdata() if pixel)
    share = wrong / max(1, covered)
    print(f"  frame {frame_index:03d}: silhouette mismatch {share * 100:5.1f}%")
    if share > 0.12:
        debug = Path(__file__).resolve().parents[1] / "agent-scratch" / "vanity_verify"
        debug.mkdir(parents=True, exist_ok=True)
        reference.save(debug / f"reference_{frame_index:03d}.png")
        baked.save(debug / f"baked_{frame_index:03d}.png")
        raise SystemExit(
            f"frame {frame_index}: baked placements disagree with the renderer by "
            f"{share * 100:.1f}% of the drawn silhouette. Wrote both to {debug} for comparison."
        )


def ron_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_manifest(
    manifest: dict, atlas: PartAtlas, rects: List[Tuple[int, int, int, int]]
) -> None:
    lines: List[str] = []
    lines.append("// GENERATED by tools/ambition_sprite2d_renderer/scripts/export_author_vanity_card.py")
    lines.append("// The motion is authored in Python (rigs + IK + choreography); this is where it")
    lines.append("// LANDED, frame by frame, so the engine only has to place quads. Do not hand-edit:")
    lines.append("// re-run the exporter, which verifies itself against the renderer.")
    lines.append("(")
    lines.append(f"    canvas: ({manifest['canvas'][0]:.1f}, {manifest['canvas'][1]:.1f}),")
    lines.append(f"    frame_ms: {manifest['frame_ms']},")
    lines.append(f'    sheet: "{ASSET_PREFIX}/vanity_card_parts.png",')
    lines.append("    parts: [")
    for name, rect in zip(atlas.order, rects):
        lines.append(
            f"        (name: {ron_string(name)}, x: {rect[0]}, y: {rect[1]}, "
            f"w: {rect[2]}, h: {rect[3]}),"
        )
    lines.append("    ],")
    lines.append("    frames: [")
    for frame in manifest["frames"]:
        lines.append("        (")
        lines.append("            draws: [")
        for row in frame["draws"]:
            lines.append(
                "                (part: {part}, x: {x:.2f}, y: {y:.2f}, "
                "w: {w:.2f}, h: {h:.2f}, deg: {deg:.2f}),".format(**row)
            )
        lines.append("            ],")
        bubble = frame["bubble"]
        if bubble is None:
            lines.append("            bubble: None,")
        else:
            lines.append(
                "            bubble: Some((text: {text}, tail_x: {tail_x:.2f}, "
                "tail_y: {tail_y:.2f}, box_x: {box_x:.2f}, box_y: {box_y:.2f})),".format(
                    text=ron_string(bubble["text"]),
                    **{k: v for k, v in bubble.items() if k != "text"},
                )
            )
        lines.append("        ),")
    lines.append("    ],")
    lines.append(")")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text("\n".join(lines) + "\n")


def pack_atlas(atlas: PartAtlas) -> Tuple[Image.Image, List[Tuple[int, int, int, int]]]:
    """Pack every part into ONE image, in a shelf layout.

    **One texture load, not forty-one.** The card is the first thing the game
    shows, and on a phone the cost of an asset is dominated by the number of
    them rather than by their total bytes — 41 parts weigh 336 KB together,
    which is less than the frame sequence this replaces, but they would have
    been 41 separate loads on the critical path of the boot.

    Shelf packing (sort by height, fill rows) rather than anything cleverer: the
    parts are a fixed set of 41 rectangles, it wastes a few percent, and a
    rectangle packer would be a page of code serving one image.
    """
    padding = 2
    max_width = 2048
    order = sorted(range(len(atlas.images)), key=lambda i: -atlas.images[i].height)

    rects: List[Optional[Tuple[int, int, int, int]]] = [None] * len(atlas.images)
    pen_x, pen_y, shelf_height, used_width = padding, padding, 0, 0
    for slot in order:
        image = atlas.images[slot]
        if pen_x + image.width + padding > max_width:
            pen_x = padding
            pen_y += shelf_height + padding
            shelf_height = 0
        rects[slot] = (pen_x, pen_y, image.width, image.height)
        pen_x += image.width + padding
        used_width = max(used_width, pen_x)
        shelf_height = max(shelf_height, image.height)

    sheet = Image.new("RGBA", (used_width, pen_y + shelf_height + padding), (0, 0, 0, 0))
    for slot, rect in enumerate(rects):
        assert rect is not None
        sheet.paste(atlas.images[slot], (rect[0], rect[1]))
    return sheet, [rect for rect in rects if rect is not None]


def write_parts(sheet: Image.Image) -> None:
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)
    sheet.save(PAYLOAD_DIR / "vanity_card_parts.png")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="re-composite every baked frame and diff it against the renderer",
    )
    args = parser.parse_args(argv)

    manifest, atlas = bake(args.verify)
    sheet, rects = pack_atlas(atlas)
    write_parts(sheet)
    write_manifest(manifest, atlas, rects)

    total = sum(len(frame["draws"]) for frame in manifest["frames"])
    print(f"parts:  {len(atlas.order)} in one {sheet.width}x{sheet.height} sheet -> {PAYLOAD_DIR}")
    print(f"frames: {len(manifest['frames'])} ({total} placements) -> {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
