# Character SVG drawing scripts (reference, not authority)

These scripts are how the first drafts of these character SVGs were drawn:

| Script | Draws | Rig builder |
|---|---|---|
| `trex_enemy_art.py` | `data/characters/trex_enemy/trex_enemy.svg` | `scripts/build_trex_enemy_rig.py` |
| `raptor_stalker_art.py` | `data/characters/raptor_stalker/raptor_stalker.svg` | `scripts/build_raptor_stalker_rig.py` |
| `bear_mauler_art.py` | `data/characters/bear_mauler/bear_mauler.svg` | `scripts/build_bear_mauler_rig.py` |
| `burning_flying_shark_art.py` | `data/characters/burning_flying_shark/burning_flying_shark.svg` | `scripts/build_burning_flying_shark_rig.py` |
| `bob_art.py` | `data/characters/bob/bob.svg` | `scripts/build_bob_rig.py` |
| `bob_front_art.py` | `data/characters/bob/bob_front.svg` | `scripts/build_bob_rig.py` |
| `stochastic_parrot_art.py` | `data/characters/stochastic_parrot_v2/stochastic_parrot_v2.svg` and `stochastic_parrot_v2_front.svg` | `scripts/build_stochastic_parrot_v2_rig.py` |

⚠ **The SVGs own the art.** Edit an SVG directly (in Inkscape or by hand)
when the art changes; these scripts are not re-run to produce it and are not
kept in step with later edits. They are kept as worked examples for drawing a
new creature: smooth outlines from a few points, one layer per rig part, ink
silhouettes that hide the seams between parts, feathers, fringes of fur, and a
hidden `Rig Joints` layer the rig builder reads. `bob_art.py` is the humanoid
example: limbs as overlapping capsules, swap sets (fist / open hands, eye and
mouth states) and props that ride a hand or stow on the back.
`stochastic_parrot_art.py` is the bird: one script drawing two views, and a
wing that swaps between folded on the body and spread in two bones.

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
| shark | 15,655 B | 51,049 B | 65,422 B |
| Bob | 23,113 B | 57,949 B | 80,431 B |
| Bob, front view | 16,227 B | 49,237 B | 69,589 B |
| Stochastic Parrot (side + front) | 21,100 B | 75,193 B + 33,294 B | 93,646 B + 40,731 B |
| shared `svgkit.py` | 11,543 B | | |
