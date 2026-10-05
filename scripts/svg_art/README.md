# Creature SVG drawing scripts (reference, not authority)

These scripts are how the first drafts of three creature SVGs were drawn:

| Script | Draws | Rig builder |
|---|---|---|
| `trex_enemy_art.py` | `data/characters/trex_enemy/trex_enemy.svg` | `scripts/build_trex_enemy_rig.py` |
| `raptor_stalker_art.py` | `data/characters/raptor_stalker/raptor_stalker.svg` | `scripts/build_raptor_stalker_rig.py` |
| `bear_mauler_art.py` | `data/characters/bear_mauler/bear_mauler.svg` | `scripts/build_bear_mauler_rig.py` |

⚠ **The SVGs own the art.** Edit an SVG directly (in Inkscape or by hand)
when the art changes; these scripts are not re-run to produce it and are not
kept in step with later edits. They are kept as worked examples for drawing a
new creature: smooth outlines from a few points, one layer per rig part, ink
silhouettes that hide the seams between parts, feathers, fringes of fur, and a
hidden `Rig Joints` layer the rig builder reads.

At the time they were committed, each script reproduced its SVG byte for byte,
except for the rig catalog block (`BEGIN/END AMBITION SVG RIG v1`) that the rig
builder appends.

## Use

```sh
cd scripts/svg_art
uv run python bear_mauler_art.py /tmp/bear.svg   # writes only where you say
```

To turn a drawing into a character: put the SVG under `data/characters/<name>/`,
write a `scripts/build_<name>_rig.py` on `rigbuild.creature_rig` (copy the
nearest one), and run it; it derives the skeleton from the joints, writes the
rig document and installs the SVG's rig catalog.

`svgkit.py` holds the shared drawing helpers; its docstring lists them.

## Sizes (at commit time)

| | script | SVG art (no catalog) | SVG with catalog |
|---|---:|---:|---:|
| T-rex | 22,376 B | 72,498 B | 97,626 B |
| raptor | 20,861 B | 107,870 B | 133,037 B |
| bear | 16,797 B | 64,889 B | 87,377 B |
| shared `svgkit.py` | 11,543 B | | |
