"""Draw the terrain skins.

    python -m ambition_sprite2d_renderer.terrain draw --out-dir DIR [SKIN ...]
    python -m ambition_sprite2d_renderer.terrain preview OUT.png [SKIN ...]

`draw` publishes `<skin>_<part>.png` for each part of each skin, and the mote
picture, the decor picture and the door of each biome (`<biome>_motes.png`,
`<biome>_decor.png`, `<biome>_decor_glow.png`, `<biome>_door.png`). `preview`
writes one picture with a small made-up room in each skin. It does not run
the game.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from . import decor, doors, fixtures, motes, skins


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
    chosen = [known[name] for name in args.skins] or list(skins.SKINS)
    drawn = {skin.key: {part: make(skin) for part, make in skins.PARTS.items()} for skin in chosen}
    if args.command == "draw":
        args.out_dir.mkdir(parents=True, exist_ok=True)
        for key, parts in drawn.items():
            for part, image in parts.items():
                path = args.out_dir / f"{key}_{part}.png"
                image.save(path)
                print(path)
        for key in motes.MOTES:
            if args.skins and key not in args.skins:
                continue
            path = args.out_dir / f"{key}_motes.png"
            motes.strip(key).save(path)
            print(path)
        for key in motes.SHADOWS:
            if args.skins and key not in args.skins:
                continue
            path = args.out_dir / f"{key}_shadow.png"
            motes.shadow(key).save(path)
            print(path)
        for key in decor.DECOR:
            if args.skins and key not in args.skins:
                continue
            path = args.out_dir / f"{key}_decor.png"
            decor.strip(key).save(path)
            print(path)
            path = args.out_dir / f"{key}_decor_glow.png"
            decor.glow_strip(key).save(path)
            print(path)
        water = {
            "water_clear": fixtures.water_clear(),
            "water_murky": fixtures.water_murky(),
            "water_surface": fixtures.water_surface(),
            "blink_soft": fixtures.blink_soft(),
            "blink_hard": fixtures.blink_hard(),
            "blink_edge": fixtures.blink_edge(),
            "hazard_fill": fixtures.hazard_fill(),
            "hazard_edge": fixtures.hazard_edge(),
        }
        for skin in skins.SKINS:
            if args.skins and skin.key not in args.skins:
                continue
            path = args.out_dir / f"{skin.key}_ladder.png"
            fixtures.ladder(skin.key).save(path)
            print(path)
            # The water, the blink walls and the spikes are the same in each
            # biome: each one has its copy, so the game finds it by the theme of the room
            # as each other part.
            for part, image in water.items():
                path = args.out_dir / f"{skin.key}_{part}.png"
                image.save(path)
                print(path)
        for key in doors.DOORS:
            if args.skins and key not in args.skins:
                continue
            path = args.out_dir / f"{key}_door.png"
            doors.door(key).save(path)
            print(path)
        return 0
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
