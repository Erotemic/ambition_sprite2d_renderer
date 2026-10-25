"""``python -m ambition_sprite2d_renderer.chargen`` (also the renderer CLI's
``chargen`` command).

    chargen cast --count 24 --seed 7 --out DIR      # specs, SVGs, contact sheet
    chargen new --base slim_male --seed 3 -o x.json # a spec to edit by hand
    chargen show SPEC --out DIR                     # SVG + turnaround of one spec
    chargen rig SPEC --out DIR                      # + rigs and posed rows
    chargen sheet SPEC --out DIR                    # + the gameplay sprite sheet
    chargen faces SPEC --out DIR                    # the expression sheet
    chargen wardrobe SPEC --out DIR                 # the wardrobe-swap sheet
    chargen species --seed 1 --out DIR              # a head of every species
    chargen bases                                   # the bases and their ranges
    chargen studio [--port 8765]                    # a local page: edit, sweep, crowd, pose

A SPEC is a ``.json`` or ``.yaml`` file; fields it leaves out are drawn from
its ``base`` and ``seed``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .family import FAMILIES
from .spec import BASES, CharacterSpec, crowd, generate


def _cmd_cast(args) -> int:
    from .rig import character_svg, slug, write_character
    from .sheets import contact_sheet, turnaround

    out = Path(args.out)
    specs = crowd(args.count, args.seed, args.bases or None, family=args.family)
    for spec in specs:
        if args.rigs:
            write_character(spec, out / slug(spec.name))
        else:
            spec.save(out / "specs" / f"{slug(spec.name)}.chargen.json")
            (out / "svg").mkdir(parents=True, exist_ok=True)
            (out / "svg" / f"{slug(spec.name)}.svg").write_text(character_svg(spec), encoding="utf8")
    print(contact_sheet(specs, out / "contact_sheet.png"))
    if args.turnaround:
        print(turnaround(specs[: args.turnaround], out / "turnaround.png"))
    return 0


def _cmd_new(args) -> int:
    spec = generate(args.base, args.seed, {"family": args.family} if args.family else None)
    if args.name:
        spec.name = args.name
    if args.output:
        print(spec.save(args.output))
    else:
        print(spec.to_json(), end="")
    return 0


def _cmd_show(args) -> int:
    from .rig import character_svg, slug
    from .sheets import turnaround

    spec = CharacterSpec.load(args.spec)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{slug(spec.name)}.svg").write_text(character_svg(spec), encoding="utf8")
    print(turnaround([spec], out / f"{slug(spec.name)}_turnaround.png"))
    return 0


def _cmd_rig(args) -> int:
    from .rig import slug, write_character
    from .sheets import posed_sheet

    spec = CharacterSpec.load(args.spec)
    files = write_character(spec, Path(args.out))
    for p in [files.spec_path, files.svg_path, *files.rigs.values()]:
        print(p)
    print(posed_sheet(files.rigs, Path(args.out) / f"{slug(spec.name)}_posed.png"))
    return 0


def _cmd_sheet(args) -> int:
    from .sheets import publish_sheet

    spec = CharacterSpec.load(args.spec)
    for p in publish_sheet(spec, Path(args.out)):
        print(p)
    return 0


def _cmd_faces(args) -> int:
    from .rig import slug
    from .sheets import expression_sheet

    spec = CharacterSpec.load(args.spec)
    print(expression_sheet(spec, Path(args.out) / f"{slug(spec.name)}_expressions.png"))
    return 0


def _cmd_wardrobe(args) -> int:
    from .rig import slug
    from .sheets import wardrobe_sheet

    spec = CharacterSpec.load(args.spec)
    print(wardrobe_sheet(spec, Path(args.out) / f"{slug(spec.name)}_wardrobe.png"))
    return 0


def _cmd_species(args) -> int:
    from .sheets import species_sheet
    from .spec import SPECIES

    specs = [crowd(1, args.seed * 100 + i, species=sp)[0] for i, sp in enumerate(SPECIES)]
    print(species_sheet(specs, Path(args.out) / "species_sheet.png"))
    return 0


def _cmd_bases(args) -> int:
    for key, base in sorted(BASES.items()):
        print(f"{key}: {base.display_name}")
        for name, (lo, hi) in sorted(base.ranges.items()):
            print(f"    {name:10s} {lo:g} .. {hi:g}")
    print("families (spec field `family`):")
    for key, fam in FAMILIES.items():
        print(f"  {key}: {fam.description}")
    return 0


def _cmd_studio(args) -> int:
    from .studio import serve

    serve(port=args.port, jobs=args.jobs, host=args.host, open_browser=args.open)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="chargen", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("cast", help="generate a cast of townsfolk and its contact sheet")
    c.add_argument("--count", type=int, default=24)
    c.add_argument("--seed", type=int, default=0)
    c.add_argument("--bases", nargs="*", choices=sorted(BASES), help="cycle through these bases (default: all)")
    c.add_argument("--family", choices=sorted(FAMILIES), help="draw all in this family (default: standard)")
    c.add_argument("--out", required=True)
    c.add_argument("--rigs", action="store_true", help="also bind every character to rigs (slower)")
    c.add_argument("--turnaround", type=int, default=0, metavar="N", help="also draw the turnaround of the first N")
    c.set_defaults(func=_cmd_cast)
    n = sub.add_parser("new", help="write one generated spec, to edit by hand")
    n.add_argument("--base", choices=sorted(BASES))
    n.add_argument("--seed", type=int, default=0)
    n.add_argument("--family", choices=sorted(FAMILIES))
    n.add_argument("--name")
    n.add_argument("-o", "--output")
    n.set_defaults(func=_cmd_new)
    for name, fn, text in (("show", _cmd_show, "the SVG and turnaround of a spec"), ("rig", _cmd_rig, "the SVG, rigs and posed rows of a spec"),
                           ("sheet", _cmd_sheet, "the gameplay sprite sheet of a spec"),
                           ("faces", _cmd_faces, "the expression sheet of a spec (every face, the visemes, the blink)"),
                           ("wardrobe", _cmd_wardrobe, "the spec as worn and with each wardrobe alternate swapped in")):
        s = sub.add_parser(name, help=text)
        s.add_argument("spec")
        s.add_argument("--out", required=True)
        s.set_defaults(func=fn)
    sp = sub.add_parser("species", help="one character of every head species, in five views and a few faces")
    sp.add_argument("--seed", type=int, default=1)
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=_cmd_species)
    st = sub.add_parser("studio", help="a local page to make characters and see every view, sweep and pose")
    st.add_argument("--port", type=int, default=8765)
    st.add_argument("--host", default="127.0.0.1", help="0.0.0.0 to reach it from another machine")
    st.add_argument("--jobs", type=int, default=6, help="processes in all (at most 6): one poses, the rest draw")
    st.add_argument("--open", action="store_true", help="open the page in a browser")
    st.set_defaults(func=_cmd_studio)
    b = sub.add_parser("bases", help="list the bases and their body ranges, and the families")
    b.set_defaults(func=_cmd_bases)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args) or 0)


__all__ = ["build_parser", "main"]
