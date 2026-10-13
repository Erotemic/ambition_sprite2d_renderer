# Character and prop SVG drawing scripts (reference, not authority)

These scripts are how the first drafts of these character and prop SVGs were drawn:

| Script | Draws | Rig builder |
|---|---|---|
| `trex_enemy_art.py` | `data/characters/trex_enemy/trex_enemy.svg` | `scripts/build_trex_enemy_rig.py` |
| `raptor_stalker_art.py` | `data/characters/raptor_stalker/raptor_stalker.svg` | `scripts/build_raptor_stalker_rig.py` |
| `bear_mauler_art.py` | `data/characters/bear_mauler/bear_mauler.svg` | `scripts/build_bear_mauler_rig.py` |
| `burning_flying_shark_art.py` | `data/characters/burning_flying_shark/burning_flying_shark.svg` | `scripts/build_burning_flying_shark_rig.py` |
| `bob_art.py` | `data/characters/bob/bob.svg` | `scripts/build_bob_rig.py` |
| `bob_front_art.py` | `data/characters/bob/bob_front.svg` | `scripts/build_bob_rig.py` |
| `stochastic_parrot_art.py` | `data/characters/stochastic_parrot_v2/stochastic_parrot_v2.svg`, `stochastic_parrot_v2_front.svg` and `stochastic_parrot_v2_three_quarter.svg` | `scripts/build_stochastic_parrot_v2_rig.py` |
| `chicken_art.py` | `data/characters/chicken/chicken.svg` and `data/characters/chicken_hen/chicken_hen.svg` | `scripts/build_chicken_rig.py` |
| `owl_art.py` | `data/characters/owl/owl.svg` | `scripts/build_owl_rig.py` |
| `ratites_art.py` | `data/characters/<bird>/<bird>.svg` for `ostrich`, `ostrich_hen`, `emu`, `cassowary`, `kiwi` and `shoebill` | `scripts/build_ratite_rigs.py` |
| `swallows_art.py` | `data/characters/european_swallow/european_swallow.svg` and `data/characters/african_swallow/african_swallow.svg` | `scripts/build_flyer_rigs.py` |
| `vulture_art.py` | `data/characters/vulture/vulture.svg` | `scripts/build_flyer_rigs.py` |
| `penguin_art.py` | `data/characters/penguin/penguin.svg` | `scripts/build_penguin_rig.py` |
| `dinosaurs_art.py` | `data/characters/<name>/<name>.svg` for `compsognathus`, `dilophosaurus` and `pachycephalosaurus` | `scripts/build_ratite_rigs.py` |
| `triceratops_art.py` | `data/characters/triceratops/triceratops.svg` | `scripts/build_triceratops_rig.py` |
| `treasure_chest_art.py` | `data/props/treasure_chest/treasure_chest.svg` | `scripts/build_treasure_chest_rig.py` |
| `boss_chest_art.py` | `data/props/boss_chest/boss_chest.svg` | `scripts/build_boss_chest_rig.py` |
| `mockingbird_boss_v2_art.py` | `data/characters/mockingbird_boss_v2/mockingbird_boss_v2.svg` | `scripts/build_mockingbird_boss_v2_rig.py` |
| `imperfect_cellular_automaton_art.py` | `data/characters/imperfect_cellular_automaton/imperfect_cellular_automaton.svg` and `imperfect_cellular_automaton_fault_side.svg` (her two sides) | `scripts/build_imperfect_cellular_automaton_rig.py` |
| `giant_gnu_art.py` | nothing: it draws one pose of GNU-ton's giant to look at. The giant's drawing is the target's own module (`targets/characters/gnu_ton_boss/giant_art.py`), not an SVG | none: the target makes its frames from poses |

⚠ **The SVGs own the art.** Edit an SVG directly (in Inkscape or by hand)
when the art changes; these scripts are not re-run to produce it and are not
kept in step with later edits. They are kept as worked examples for drawing a
new creature: smooth outlines from a few points, one layer per rig part, ink
silhouettes that hide the seams between parts, feathers, fringes of fur, and a
hidden `Rig Joints` layer the rig builder reads. `bob_art.py` is the humanoid
example: limbs as overlapping capsules, swap sets (fist / open hands, eye and
mouth states) and props that ride a hand or stow on the back.
`stochastic_parrot_art.py` is the bird: one script drawing three views, and a
wing that swaps between folded on the body and spread in two bones.
`chicken_art.py` and `owl_art.py` are side-view birds on the same joints, drawn
with the helpers in `birdkit.py` (the spread wing, the legs, the eye swap set);
the owl's body is seen from the side and its face is turned to the viewer.
`ratites_art.py` is one script for several birds of one build (long legs that
fold at the hock, a neck in its own bone): each bird is a function, and a hen
whose colours differ from the cock's is the same function with another palette.
`treasure_chest_art.py` and `boss_chest_art.py` are props: a lid drawn four
times (closed, ajar, up, open) as a swap set hinged at the box's back edge.
`mockingbird_boss_v2_art.py` is the machine: armour panels shaded inside their
silhouettes, steel cylinders with rings and a sheen, rotor blades drawn as a
swap set of spin states, claws open or shut, a glowing core seen through a
cage of ribs, and rigid swept jet wings in perspective (the near one reaching
toward the camera, the far one hidden but for its tip); its
rig builder writes its own (gunship) skeleton instead of a
`rigbuild` family.
`imperfect_cellular_automaton_art.py` is a character whose two sides differ:
one script draws her from each side, in flat polygons, and a swap set of
layers (`grid_<n>`) that the rig shows one at a time.

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
`birdkit.py` adds the helpers the side-view birds share.

## Sizes (at commit time)

| | script | SVG art (no catalog) | SVG with catalog |
|---|---:|---:|---:|
| T-rex | 22,376 B | 72,498 B | 97,626 B |
| raptor | 20,861 B | 107,870 B | 133,037 B |
| bear | 16,797 B | 64,889 B | 87,377 B |
| shark | 15,655 B | 51,049 B | 65,422 B |
| Bob | 23,113 B | 57,949 B | 80,431 B |
| Bob, front view | 16,227 B | 49,237 B | 69,589 B |
| Stochastic Parrot (side + front + three-quarter) | 27,996 B | 75,193 + 33,294 + 38,090 B | 93,646 + 40,731 + 45,511 B |
| treasure chest | 13,344 B | 33,926 B | 41,223 B |
| boss chest | 12,576 B | 38,518 B | 45,010 B |
| Mockingbird v2 | 33,889 B | 102,171 B | 132,614 B |
| shared `svgkit.py` | 11,543 B | | |
