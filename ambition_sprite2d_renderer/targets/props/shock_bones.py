"""Paint reusable bone parts for a body that takes electric damage."""

import json
from pathlib import Path

from PIL import Image
import yaml

from ...chargen.spec import SPECIES, complete
from ..characters import _humanoid_bone_art as bones
from ..characters._clockwork_enemy_art import Canvas, bezier
from ..characters.townsfolk import SPECS, load
from . import _shock_skulls

TARGET_NAME = "shock_bones"
PUBLICATION_TIERS = ["full"]
SHEET_FILES = ["shock_bones.png", "shock_bones.shock.ron"]

CELL = 64
COLUMNS = 4
CENTER = (32, 32)


def animal_trunk(canvas, p):
    """Paint a spine, pelvis, shoulder blade, and curved ribs."""
    spine = [(12, 29), (20, 27), (29, 26), (41, 25), (52, 23)]
    canvas.line(spine, p.ink, 5.8)
    canvas.line(spine, p.bone, 3.2)
    for i, x in enumerate(range(24, 46, 4)):
        depth = (8, 11, 13, 14, 13, 10)[i]
        rib = bezier((x, 26), (x + 4, 28), (x + 4, 34 + depth), (x - 6, 29 + depth), n=9)
        canvas.line(rib, p.ink, 3.4)
        canvas.line(rib, p.shade, 2.0)
        canvas.line(rib[1:6], p.light, 1.0)
    canvas.poly([(10, 29), (12, 25), (20, 24), (23, 29),
                 (19, 35), (16, 37), (14, 33)], p.bone, p.ink, 1.2)
    canvas.poly([(42, 25), (46, 22), (49, 28), (47, 37),
                 (44, 40), (41, 34)], p.bone, p.ink, 1.2)


def paw(canvas, p):
    bones.long_bone(canvas, (30, 29), (36, 34), 2.25, p)
    for i in range(3):
        y = 33 + i * 1.65
        bones.long_bone(canvas, (35, y), (43 - i, y + 1), 0.85, p)


def tail(canvas, p):
    for i in range(7):
        x = 12 + i * 6.0
        y = 33 + 0.35 * i * (i - 4)
        canvas.oval((x, y), 3.9 - 0.28 * i, 2.8 - 0.27 * i, p.bone, p.ink, 0.8)


def _chargen_species():
    """Read each head species from its chargen spec."""
    result = {}
    for path in sorted(SPECS.glob("*.chargen.yaml")):
        spec, _ = load(path)
        result[path.name.removesuffix(".chargen.yaml")] = spec.head.species
    for path in sorted((SPECS.parent / "characters").glob("*/*.chargen.yaml")):
        spec = complete(yaml.safe_load(path.read_text(encoding="utf8")))
        result[path.name.removesuffix(".chargen.yaml")] = spec.head.species
    return result


def _table(name, data):
    lines = [f"    {name}: {{"]
    lines.extend(f"        {json.dumps(k)}: {json.dumps(v)}," for k, v in sorted(data.items()))
    return "\n".join([*lines, "    },"])


def render(out_dir, **_opts):
    """Paint the atlas and publish its skull cells and species by sheet."""
    palette = bones.FLASH
    painters = [
        lambda c: _shock_skulls.paint(c, "human", CENTER, palette),
        lambda c: bones.trunk(c, (32, 52), (32, 12), palette),
        lambda c: bones.long_bone(c, (12, 32), (52, 32), 3.0, palette),
        lambda c: bones.paired_bones(c, (12, 32), (52, 32), 2.9, palette),
        lambda c: bones.hand(c, CENTER, 0, scale=1.4, palette=palette),
        lambda c: bones.foot(c, CENTER, scale=1.4, palette=palette),
        lambda c: animal_trunk(c, palette),
        lambda c: paw(c, palette),
        lambda c: tail(c, palette),
    ]
    skulls = {"human": 0}
    for species in SPECIES:
        if species == "human":
            continue
        skulls[species] = len(painters)
        painters.append(lambda c, species=species: _shock_skulls.paint(c, species, CENTER, palette))

    rows = (len(painters) + COLUMNS - 1) // COLUMNS
    atlas = Image.new("RGBA", (COLUMNS * CELL, rows * CELL))
    for index, paint in enumerate(painters):
        cell = Canvas((CELL, CELL))
        paint(cell)
        atlas.paste(cell.finish(), (index % COLUMNS * CELL, index // COLUMNS * CELL))

    image, profiles = [Path(out_dir) / name for name in SHEET_FILES]
    image.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(image)
    profiles.write_text(
        "\n".join(["(", _table("skulls", skulls), _table("chargen", _chargen_species()), ")", ""]),
        encoding="utf8",
    )
    return [image, profiles]
