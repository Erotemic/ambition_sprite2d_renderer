"""Draw the terrain skins.

    python -m ambition_sprite2d_renderer.terrain draw --out-dir DIR [SKIN ...]
    python -m ambition_sprite2d_renderer.terrain preview OUT.png [SKIN ...]

`draw` publishes `<skin>_<part>.png` for each part of each skin (and the
ornaments of a skin that has them, `ornaments.py`), and the mote
picture, the decor picture and the door of each biome (`<biome>_motes.png`,
`<biome>_decor.png`, `<biome>_decor_glow.png`, `<biome>_door.png`, and its
opening `<biome>_door_opening.png`), and the
shimmer of a biome that has one (`<biome>_shimmer.png`), and the opaque
scene behind the water of a biome that has one
(`<biome>_water_backdrop.png`, `water_backdrops.py`). `preview`
writes one picture with a small made-up room in each skin. It does not run
the game. `draw` records which callable drew each file (`provenance.py`).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

from PIL import Image

from .. import provenance
if __name__ == "__main__":
    from .. import read_record
    read_record.start(provenance.repo_root(), [provenance.asset_root(), Path(__file__).resolve().parents[2] / ".cache"])
from . import decor, doors, fixtures, motes, ornaments, shimmer, skins, two_state, water_backdrops

#: One published file: its skin or biome, its name, the callable that draws
#: it (for the provenance record) and the call that draws it.
Job = tuple[str, str, Callable, Callable[[], Image.Image]]

_WATER = ("water_clear", "water_murky", "water_surface", "blink_soft", "blink_hard", "blink_edge", "hazard_fill", "hazard_edge")


def _skin_part(skin: skins.Skin, part: str) -> Job:
    make = skins.PARTS[part]
    painter = two_state.PAINTERS.get((skin.key, part))
    return (skin.key, part, painter or make, lambda: two_state.paint(skin.key, part) or make(skin))


def jobs(names: list[str]) -> list[Job]:
    """Every file `draw` publishes for the skins `names` (every skin when
    empty), in the order it draws them."""
    chosen = [skin for skin in skins.SKINS if not names or skin.key in names]
    out: list[Job] = []
    for skin in chosen:
        out += [_skin_part(skin, part) for part in skins.PARTS]
        out += [(skin.key, part, paint, paint) for (owner, part), paint in ornaments.PAINTERS.items() if owner == skin.key]
    wanted = [key for key in names] if names else None

    def keyed(table) -> list[str]:
        return [key for key in table if wanted is None or key in wanted]

    out += [(key, "motes", motes.strip, lambda key=key: motes.strip(key)) for key in keyed(motes.MOTES)]
    out += [(key, "shadow", motes.shadow, lambda key=key: motes.shadow(key)) for key in keyed(motes.SHADOWS)]
    for key in keyed(decor.DECOR):
        out.append((key, "decor", decor.strip, lambda key=key: decor.strip(key)))
        out.append((key, "decor_glow", decor.glow_strip, lambda key=key: decor.glow_strip(key)))
    out += [(key, "shimmer", shimmer.picture, lambda key=key: shimmer.picture(key)) for key in keyed(shimmer.SHIMMERS)]
    for skin in chosen:
        out.append((skin.key, "ladder", fixtures.ladder, lambda key=skin.key: fixtures.ladder(key)))
        # The water, the blink walls and the spikes are the same in each
        # biome: each one has its copy, so the game finds it by the theme of
        # the room as each other part.
        for part in _WATER:
            fn = getattr(fixtures, part)
            out.append((skin.key, part, fn, fn))
    out += [(key, "water_backdrop", render, render) for key, render in water_backdrops.BACKDROPS.items() if wanted is None or key in wanted]
    for key in keyed(doors.DOORS):
        out.append((key, "door", doors.door, lambda key=key: doors.door(key)))
        out.append((key, "door_opening", doors.opening, lambda key=key: doors.opening(key)))
    return out


def plan(dest: Path, names: list[str]) -> provenance.Book:
    """What `draw` publishes into `dest`, by skin or biome, and what draws each file."""
    book = provenance.Book("terrain_skin", dest, "./scripts/regen/backgrounds.sh  # terrain skin {unit}", "terrain")
    for unit, part, fn, _draw in jobs(names):
        book.add(unit, dest / f"{unit}_{part}.png", fn)
    return book


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ambition_sprite2d_renderer.terrain", description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    draw = sub.add_parser("draw", help="publish the parts of each skin")
    draw.add_argument("--out-dir", type=Path, required=True)
    draw.add_argument("skins", nargs="*")
    preview = sub.add_parser("preview", help="a made-up room in each skin")
    preview.add_argument("out", type=Path)
    preview.add_argument("skins", nargs="*")
    args = parser.parse_args(argv)

    known = {skin.key: skin for skin in skins.SKINS}
    unknown = [name for name in args.skins if name not in known]
    if unknown:
        raise SystemExit(f"no skin named {unknown}; the skins are {sorted(known)}")
    if args.command == "draw":
        args.out_dir.mkdir(parents=True, exist_ok=True)
        for unit, part, _fn, draw_one in jobs(args.skins):
            path = args.out_dir / f"{unit}_{part}.png"
            draw_one().save(path)
            print(path)
        plan(args.out_dir, args.skins).write()
        return 0
    chosen = [known[name] for name in args.skins] or list(skins.SKINS)
    # The two-state hub draws its own parts (`two_state.py`); each other skin
    # is drawn by the parts of `skins.py`.
    drawn = {
        skin.key: {part: two_state.paint(skin.key, part) or make(skin) for part, make in skins.PARTS.items()}
        for skin in chosen
    }
    rooms = [skins.mockup(skin, drawn[skin.key]) for skin in chosen]
    columns = 2 if len(rooms) > 1 else 1
    rows = (len(rooms) + columns - 1) // columns
    w, h = rooms[0].size
    sheet = Image.new("RGB", (w * columns, h * rows))
    for index, room in enumerate(rooms):
        sheet.paste(room.convert("RGB"), ((index % columns) * w, (index // columns) * h))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
