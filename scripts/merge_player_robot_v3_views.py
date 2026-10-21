"""Put the player robot's views on one canvas, each in a cell of a grid.

Run once (2026-10-21); kept as the record of how the file was made. Jon:
"It's difficult to make manual edits when so many parts are stacked on top of
one another in the SVG. It would be nice if distinct viewpoints could be
distributed in a grid on the SVG canvas. ... For parts that are reused, we can
use reference clones so we don't duplicate art."

    .venv/bin/python scripts/merge_player_robot_v3_views.py

Into ``player-robot-v3.svg`` (the side view, which stays where it is):

* cell 2, ``Player Robot - Side Pure``: the robot seen from the side, with the
  torso and the pelvis from the side (``torso_side``, ``pelvis_side``, moved
  here from the side view, where they were drawn over the three-quarter body),
  both shoulders on one socket and the hips nearly on one. Every other part is
  a clone (``<use>``) of the side view's part, moved with its joint;
* cell 3, ``Player Robot - Back``, and cell 4, ``Player Robot - Front``: the
  view layers of ``player-robot-v3-back.svg`` and ``-front.svg``, moved in
  whole (a ``translate`` on the layer). Those two files are deleted.

Each layer is copied as text, so Inkscape's formatting of the art is kept. The
managed rig-metadata blocks are removed. Then ``build_player_robot_v3_svg.py
build`` writes the rigs, and ``svg_rig_tool install-catalog`` writes the SVG's
block again from them.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "ambition_sprite2d_renderer/data/characters/player_robot_v3_svg"
SIDE = DIR / "player-robot-v3.svg"
BACK = DIR / "player-robot-v3-back.svg"
FRONT = DIR / "player-robot-v3-front.svg"

INK = "{http://www.inkscape.org/namespaces/inkscape}"
BEGIN = "<!-- BEGIN AMBITION SVG RIG v1 -->"
END = "<!-- END AMBITION SVG RIG v1 -->"

#: The width of a cell (SVG units). Cell 1 is the side view at x 232..296.
CELL = 100.0
#: The canvas: four cells in a row. Its origin is the side view's old one, so
#: the side view's pixels do not move: a part's place is read in pixels of the
#: canvas, and a new origin would shift each part by a fraction of a pixel.
VIEWBOX = (232.0, 118.0, 4 * CELL, 100.0)
#: The back and front files had their origin at (228, 116); this keeps their
#: art where it was relative to the side view's art, in their cells.
OTHER_FILE_SHIFT_Y = 2.0
#: Each view's own pixel grid (`svg_parts.PIXEL_ORIGIN_ATTR`), in the layer's
#: own coordinates: the old canvas origin of the file it came from. So no view
#: is drawn on other pixels than before, and a cell moved later keeps its grid.
PIXEL_ORIGIN = {"side": "232 118", "back": "228 116", "front": "228 116"}

# The pure side view. Both shoulders sit on one socket, a little ahead of the
# neck (x 262); the hips sit near the hip centre (x 261.75), a little apart.
SOCKET = (265.3, 170.0)
HIPS = {"near": 260.0, "far": 263.5}
#: The parts each limb carries, and the joints that go with them.
ARM_PARTS = {"near": ("near_arm_u", "near_arm_l", "near_hand"), "far": ("far_arm_u", "far_arm_l", "far_hand")}
ARM_JOINTS = ("shoulder", "elbow", "wrist", "handtip")
LEG_PARTS = {"near": ("near_leg_u", "near_leg_l", "near_foot"), "far": ("far_leg_u", "far_leg_l", "far_foot")}
LEG_JOINTS = ("hip", "knee", "ankle", "toe")
#: Side-view parts the pure side view does not draw: the three-quarter torso
#: and pelvis (it draws its own), and the blades (no strike is drawn from it).
LEFT_OUT = {"torso_back", "torso_front", "torso_open", "torso_profile", "pelvis_back", "pelvis_front", "blade", "blade_far"}
#: Parts whose art moves from the side view to the pure side view.
MOVED = ("pelvis_side", "torso_side")


def _element_span(text: str, element_id: str) -> tuple[int, int]:
    """The text of the ``<g>`` with ``id`` ``element_id``, start to end."""
    match = re.search(r'<g\b[^>]*?\bid="%s"' % re.escape(element_id), text, re.S)
    if match is None:
        raise ValueError(f"no <g id={element_id!r}>")
    start = text.rfind("<", 0, match.end())
    start = text.rfind("\n", 0, start) + 1
    depth = 0
    for tag in re.finditer(r"<g\b[^>]*?(/?)>|</g>", text[start:], re.S):
        if tag.group(0) == "</g>":
            depth -= 1
        elif not tag.group(1):
            depth += 1
        if depth == 0:
            return start, start + tag.end()
    raise ValueError(f"<g id={element_id!r}> is not closed")


def _without_managed_block(text: str) -> str:
    if BEGIN not in text:
        return text
    start = text.rfind("\n", 0, text.index(BEGIN)) + 1
    stop = text.index(END) + len(END)
    return text[:start].rstrip("\n") + "\n" + text[stop:].lstrip("\n")


def _layer(path: Path, layer_id: str, dx: float, dy: float, origin: str) -> str:
    text = path.read_text(encoding="utf8")
    start, stop = _element_span(text, layer_id)
    block = text[start:stop]
    return re.sub(r'(<g\b[^>]*?\bid="%s")' % re.escape(layer_id),
                  r'\1\n     transform="translate(%g,%g)"\n     data-rig-pixel-origin="%s"' % (dx, dy, origin), block, count=1)


def _pure_side_cell(side_text: str, moved_art: str) -> str:
    root = ET.fromstring(side_text)
    view = next(e for e in root.iter() if e.get("id") == "view-player-robot-side-right")
    parts = [g for g in view if g.get("data-rig-part")]
    joints = {e.get("data-rig-joint"): e for e in view.iter() if e.get("data-rig-joint")}

    def at(name):
        e = joints[name]
        return float(e.get("cx")), float(e.get("cy"))

    shift = {}
    for side in ("near", "far"):
        sx, sy = at(f"{side}_shoulder")
        for part in ARM_PARTS[side]:
            shift[part] = (SOCKET[0] - sx, SOCKET[1] - sy)
        hx, _hy = at(f"{side}_hip")
        for part in LEG_PARTS[side]:
            shift[part] = (HIPS[side] - hx, 0.0)
    joint_shift = {}
    for side in ("near", "far"):
        for j in ARM_JOINTS:
            joint_shift[f"{side}_{j}"] = shift[ARM_PARTS[side][0]]
        for j in LEG_JOINTS:
            joint_shift[f"{side}_{j}"] = shift[LEG_PARTS[side][0]]

    lines = [
        "  <g",
        '     id="view-player-robot-side-pure"',
        '     inkscape:label="Player Robot - Side Pure"',
        '     inkscape:groupmode="layer"',
        f'     transform="translate({CELL:g},0)"',
        f'     data-rig-pixel-origin="{PIXEL_ORIGIN["side"]}"',
        '     data-note="the robot seen from the side (the wall climb): its own torso and pelvis, both shoulders on one socket; every other part is a clone of the side view\'s, moved with its joint">',
    ]
    for g in parts:
        name = g.get("data-rig-part")
        if name in LEFT_OUT:
            continue
        if name in MOVED:
            continue
        attrs = [f'data-rig-part="{name}"', f'data-rig-bone="{g.get("data-rig-bone")}"', f'data-rig-z="{g.get("data-rig-z")}"']
        for key in ("data-rig-opacity", "data-rig-opacity-default"):
            if g.get(key) is not None:
                attrs.append(f'{key}="{g.get(key)}"')
        dx, dy = shift.get(name, (0.0, 0.0))
        move = f' transform="translate({dx:.4f},{dy:.4f})"' if (dx, dy) != (0.0, 0.0) else ""
        lines += [
            "    <g",
            f'       id="pure-{g.get("id")}"',
            f'       inkscape:label="{g.get(INK + "label") or name}"',
            "       " + "\n       ".join(attrs) + ">",
            f'      <use id="pure-clone-{g.get("id")}" xlink:href="#{g.get("id")}"{move} />',
            "    </g>",
        ]
    lines.append(moved_art.rstrip("\n"))
    lines += [
        "    <g",
        '       id="pure-rig-joints"',
        '       inkscape:label="Rig Joints"',
        '       inkscape:groupmode="layer">',
    ]
    for name, e in joints.items():
        x, y = at(name)
        dx, dy = joint_shift.get(name, (0.0, 0.0))
        lines += [
            "      <circle",
            f'         id="pure-{e.get("id")}"',
            f'         inkscape:label="{e.get(INK + "label") or name}"',
            f'         cx="{x + dx:.4f}"',
            f'         cy="{y + dy:.4f}"',
            *(f'         {key}="{e.get(key)}"' for key in ("r", "style", "fill", "stroke", "stroke-width") if e.get(key) is not None),
            f'         data-rig-joint="{name}" />',
        ]
    lines += ["    </g>", "  </g>"]
    return "\n".join(lines) + "\n"


def main() -> None:
    side = _without_managed_block(SIDE.read_text(encoding="utf8"))
    # The side view's own opacity switches for the pure view's parts go: the
    # pure view has its own torso and pelvis.
    for part in ("torso_back", "pelvis_back", "pelvis_front"):
        side = side.replace(f'\n       data-rig-opacity="{part}_vis"\n       data-rig-opacity-default="1"', "")
    moved = []
    for part in MOVED:
        start, stop = _element_span(side, "part-" + part.replace("_", "-"))
        # In the pure side view these are the only torso and pelvis: always on.
        moved.append(re.sub(r'\n\s*data-rig-opacity="%s_vis"' % part, "", side[start:stop], count=1))
        side = side[:start] + side[stop:]
    moved_art = "\n".join(block.replace("\n", "\n  ") for block in moved)
    cells = (
        _pure_side_cell(side, "  " + moved_art)
        + _layer(BACK, "view-player-robot-back", 2 * CELL, OTHER_FILE_SHIFT_Y, PIXEL_ORIGIN["back"])
        + _layer(FRONT, "view-player-robot-front", 3 * CELL, OTHER_FILE_SHIFT_Y, PIXEL_ORIGIN["front"])
    )
    side = re.sub(r'(<g\b[^>]*?\bid="view-player-robot-side-right")',
                  r'\1\n     data-rig-pixel-origin="%s"' % PIXEL_ORIGIN["side"], side, count=1)
    _, side_stop = _element_span(side, "view-player-robot-side-right")
    side = side[:side_stop] + "\n" + cells.rstrip("\n") + side[side_stop:]
    x, y, w, h = VIEWBOX
    side = re.sub(r'width="64mm"\s+height="90mm"\s+viewBox="232 118 64 90"',
                  f'width="{w:g}mm"\n   height="{h:g}mm"\n   viewBox="{x:g} {y:g} {w:g} {h:g}"', side, count=1)
    if "xmlns:xlink" not in side:
        side = side.replace('xmlns:svg="http://www.w3.org/2000/svg">',
                            'xmlns:svg="http://www.w3.org/2000/svg"\n   xmlns:xlink="http://www.w3.org/1999/xlink">', 1)
    ET.fromstring(side)  # still well formed
    SIDE.write_text(side, encoding="utf8")
    BACK.unlink()
    FRONT.unlink()
    print(SIDE)


if __name__ == "__main__":
    main()
